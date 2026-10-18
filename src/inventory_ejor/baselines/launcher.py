"""Review-first scheduler: dry-run by default; four independent GPU lanes.

This module imports no torch and never forks a live CUDA runtime. Each future
job runs in a fresh interpreter via the existing provenance/timeout wrapper.
No scheduler or numerical worker is started without a hash-bound approval.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from .planning import (
    check_approval,
    check_live_plan,
    read_json,
    worker_env,
)

ROOT = Path(__file__).resolve().parents[3]


def parse_idle_gpu_inventory(text, required, memory_fraction):
    """Parse nvidia-smi metadata without initializing CUDA or stopping other work."""
    devices = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = [value.strip() for value in line.split(",")]
        if len(fields) != 5:
            raise RuntimeError("Unexpected nvidia-smi inventory schema")
        index, identity, total, used, utilization = fields
        index = int(index)
        if index in devices or not identity.startswith("GPU-"):
            raise RuntimeError("Duplicate GPU index or missing stable GPU UUID")
        devices[index] = (identity, float(total), float(used), float(utilization))
    if not set(required) <= set(devices):
        raise RuntimeError("Not all approved GPU indices are present")
    selected = {}
    for index in required:
        identity, total, used, utilization = devices[index]
        if (
            not all(math.isfinite(v) for v in (total, used, utilization))
            or total <= 0
            or used < 0
            or utilization < 0
            or used > 256
            or utilization > 10
            or total - used < total * memory_fraction
        ):
            raise RuntimeError(
                f"GPU {index} is busy or lacks approved memory headroom; "
                "leave other projects untouched and retry when idle"
            )
        selected[index] = identity
    return selected


def dispatch(root, plan_path, approval_path, plan, gpu_devices=None):
    """Bounded foreground scheduling with immutable receipts and failure cleanup."""
    from .execution import (
        atomic_json,
        audit_job_output,
        interruption_handlers,
        session_lease,
        stop_wrapper,
    )

    resources = plan["config"]["resources"]
    with session_lease(root), interruption_handlers():
        # A lock collision creates NO session directory or partial output.
        run_root = root / "results/runs"
        run_root.mkdir(parents=True, exist_ok=True)
        session = Path(tempfile.mkdtemp(prefix="m4-approved-", dir=run_root))
        atomic_json(session / "plan.json", plan)
        atomic_json(session / "approval.json", read_json(approval_path))
        # All children consume these snapshots, not caller-editable original files.
        snapshot_plan = session / "plan.json"
        snapshot_approval = session / "approval.json"
        pending = {"cpu": queue.Queue(), "gpu": queue.Queue()}
        for index, job in enumerate(plan["jobs"]):
            pending[job["device_kind"]].put((index, job))
        stop = threading.Event()
        guard = threading.Lock()
        processes, entries = {}, []
        interrupted = False
        error = None
        started = time.monotonic()
        print(f"Baseline session: {session}", flush=True)

        def progress(status="running"):
            atomic_json(
                session / "progress.json",
                {
                    "status": status,
                    "jobs_requested": len(plan["jobs"]),
                    "jobs_finished": len(entries),
                    "running": sorted(processes),
                    "entries": list(entries),
                },
            )

        def lane(kind, slot):
            while True:
                with guard:
                    if stop.is_set():
                        return
                    try:
                        index, job = pending[kind].get_nowait()
                    except queue.Empty:
                        return
                assigned = gpu_devices[slot] if kind == "gpu" else slot
                env = worker_env(
                    os.environ, kind, assigned, resources["cpu_threads_per_worker"]
                )
                output = str((session / job["id"]).relative_to(root))
                command = [
                    sys.executable,
                    str(root / "scripts/run_experiment.py"),
                    "--config",
                    str(root / plan["config_path"]),
                    "--seed",
                    str(job["seed"]),
                    "--kind",
                    "pilot",
                    "--timeout",
                    str(resources["job_timeout_seconds"]),
                    "--data-manifest",
                    str(root / plan["bundle_manifest"]),
                    "--",
                    sys.executable,
                    str(root / "scripts/baseline_worker.py"),
                    "--plan",
                    str(snapshot_plan),
                    "--approval",
                    str(snapshot_approval),
                    "--job-index",
                    str(index),
                    "--output",
                    output,
                ]
                entry = {
                    "job": job["id"],
                    "device": kind,
                    "slot": slot,
                    "physical_gpu_uuid": assigned if kind == "gpu" else None,
                    "exit_code": 1,
                    "output": output,
                }
                process = None
                log_path = session / f"{job['id']}.wrapper.log"
                try:
                    with log_path.open("x") as log:
                        with guard:
                            if stop.is_set():
                                entry["error"] = (
                                    "Cancelled before launch after peer failure"
                                )
                                return
                            process = subprocess.Popen(
                                command,
                                cwd=root,
                                env=env,
                                stdout=log,
                                stderr=subprocess.STDOUT,
                                start_new_session=True,
                            )
                            processes[job["id"]] = process
                            progress()
                        try:
                            entry["exit_code"] = process.wait(
                                timeout=resources["job_timeout_seconds"] + 45
                            )
                        except subprocess.TimeoutExpired:
                            stop_wrapper(process)
                            entry["exit_code"] = 124
                    if entry["exit_code"] == 0:
                        entry.update(audit_job_output(root, job, output, log_path))
                except Exception as exc:
                    if process is not None:
                        stop_wrapper(process)
                    entry["exit_code"] = 1
                    entry["error"] = f"{type(exc).__name__}: {exc}"
                    atomic_json(session / f"{job['id']}.error.json", entry)
                finally:
                    with guard:
                        processes.pop(job["id"], None)
                        if entry["exit_code"] != 0:
                            stop.set()
                        entries.append(entry)
                        progress()
                        print(
                            f"[{len(entries)}/{len(plan['jobs'])}] "
                            f"{job['method']} {kind}:{slot} exit={entry['exit_code']}",
                            flush=True,
                        )
                    pending[kind].task_done()

        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=resources["cpu_workers"] + len(resources["gpu_ids"])
        )
        try:
            progress()
            futures = [
                executor.submit(lane, "cpu", i) for i in range(resources["cpu_workers"])
            ]
            if any(j["device_kind"] == "gpu" for j in plan["jobs"]):
                futures += [
                    executor.submit(lane, "gpu", i) for i in resources["gpu_ids"]
                ]
            for future in concurrent.futures.as_completed(
                futures, timeout=resources.get("session_timeout_seconds", 7200)
            ):
                future.result()
        except (KeyboardInterrupt, Exception) as exc:
            interrupted = isinstance(exc, KeyboardInterrupt)
            error = f"{type(exc).__name__}: {exc}"
            stop.set()
            with guard:
                active = list(processes.values())
            for process in active:
                stop_wrapper(process)
        finally:
            executor.shutdown(wait=True)
            status = (
                "interrupted"
                if interrupted
                else "failed_or_incomplete"
                if stop.is_set() or len(entries) != len(plan["jobs"])
                else "completed"
            )
            summary = {
                "status": status,
                "jobs_requested": len(plan["jobs"]),
                "jobs_finished": len(entries),
                "entries": entries,
                "runtime_seconds": time.monotonic() - started,
                "error": error,
                "source_commit": plan["git"]["commit"],
                "scientific_acceptance": "development_only_not_publication",
            }
            atomic_json(session / "session_summary.json", summary)
            with guard:
                progress(status)
        # Summary generation never hides incomplete jobs behind averages.
        if summary["status"] == "completed":
            from .reporting import summarize_session

            summarize_session(root, session, write=True)
        print(
            json.dumps(
                {"session": str(session.relative_to(root)), "status": summary["status"]}
            ),
            flush=True,
        )
        return 0 if summary["status"] == "completed" else 130 if interrupted else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = read_json(args.plan)
        if not args.execute:
            print(
                json.dumps(
                    {
                        "mode": "DRY_RUN_ONLY",
                        "summary": plan["summary"],
                        "approved": False,
                        "models_fitted": 0,
                        "baselines_scored": 0,
                        "note": "Dry-run only: no baseline execution is approved; "
                        "synthetic validation alone never grants approval.",
                    },
                    indent=2,
                )
            )
            return 0
        if args.approval is None:
            raise PermissionError("Execution requires separate explicit owner approval")
        check_approval(plan, read_json(args.approval))
        check_live_plan(ROOT, plan)
        from .execution import verify_artifacts

        verify_artifacts(ROOT, plan)
        # Check metadata only AFTER approval. UUIDs avoid device-index reordering.
        devices = {}
        if any(j["device_kind"] == "gpu" for j in plan["jobs"]):
            inventory = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=index,uuid,memory.total,memory.used,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
                timeout=10,
            )
            resources = plan["config"]["resources"]
            devices = parse_idle_gpu_inventory(
                inventory, resources["gpu_ids"], resources["gpu_memory_fraction"]
            )
        return dispatch(
            ROOT, args.plan.resolve(), args.approval.resolve(), plan, devices
        )
    except (
        ValueError,
        RuntimeError,
        OSError,
        KeyError,
        PermissionError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"BASELINE EXECUTION REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
