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
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from .planning import (
    check_approval,
    check_live_plan,
    encode,
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
    # Called only after approval and unchanged clean-source checks in main().
    resources = plan["config"]["resources"]
    pending = {"cpu": queue.Queue(), "gpu": queue.Queue()}
    for index, job in enumerate(plan["jobs"]):
        pending[job["device_kind"]].put((index, job))
    stop = threading.Event()
    guard = threading.Lock()
    processes = {}
    entries = []
    run_root = root / "results/runs"
    run_root.mkdir(parents=True, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix="m4-approved-", dir=run_root))
    (session / "plan.json").write_bytes(encode(plan))
    (session / "approval.json").write_bytes(Path(approval_path).read_bytes())
    lock = root.parent / "code/.baseline_execution.lock"
    try:
        with lock.open("x") as stream:
            stream.write(str(os.getpid()) + "\n")
    except FileExistsError as exc:
        raise RuntimeError(
            "Another baseline session or stale lock exists; inspect before removing it"
        ) from exc

    def lane(kind, slot):
        while not stop.is_set():
            try:
                index, job = pending[kind].get_nowait()
            except queue.Empty:
                return
            assigned = gpu_devices[slot] if kind == "gpu" and gpu_devices else slot
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
                str(plan_path),
                "--approval",
                str(approval_path),
                "--job-index",
                str(index),
                "--output",
                output,
            ]
            rc = 1
            try:
                with (session / f"{job['id']}.wrapper.log").open("x") as log:
                    process = subprocess.Popen(
                        command,
                        cwd=root,
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                    with guard:
                        processes[job["id"]] = process
                    try:
                        rc = process.wait(timeout=resources["job_timeout_seconds"] + 60)
                    except subprocess.TimeoutExpired:
                        # Ask the wrapper to terminate its own child group.
                        # Never signal another project's process.
                        process.send_signal(signal.SIGINT)
                        try:
                            process.wait(timeout=15)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=10)
                        rc = 124
            except OSError as exc:
                with (session / f"{job['id']}.launch_error.txt").open("x") as f:
                    f.write(str(exc))
            finally:
                with guard:
                    processes.pop(job["id"], None)
                    entries.append(
                        {
                            "job": job["id"],
                            "device": kind,
                            "slot": slot,
                            "exit_code": rc,
                            "output": output,
                        }
                    )
                if rc != 0:
                    # Finish in-flight jobs; stop issuing new jobs after failure.
                    stop.set()
                pending[kind].task_done()

    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=resources["cpu_workers"] + len(resources["gpu_ids"])
    )
    try:
        futures = [
            executor.submit(lane, "cpu", i) for i in range(resources["cpu_workers"])
        ]
        futures += [executor.submit(lane, "gpu", i) for i in resources["gpu_ids"]]
        for future in futures:
            future.result()
    except KeyboardInterrupt:
        stop.set()
        with guard:
            for process in processes.values():
                if process.poll() is None:
                    process.send_signal(signal.SIGINT)
        raise
    finally:
        executor.shutdown(wait=True)
        summary = {
            "status": "failed_or_incomplete"
            if stop.is_set() or len(entries) != len(plan["jobs"])
            else "completed",
            "jobs_requested": len(plan["jobs"]),
            "jobs_finished": len(entries),
            "entries": entries,
            "scientific_acceptance": "requires_independent_review",
        }
        with (session / "session_summary.json").open("xb") as out:
            out.write(encode(summary))
        if lock.exists() and lock.read_text().strip() == str(os.getpid()):
            lock.unlink()
    print(
        json.dumps(
            {"session": str(session.relative_to(root)), "status": summary["status"]}
        )
    )
    return 0 if summary["status"] == "completed" else 1


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
