"""Opt-in, bounded whole-stack acceptance on synthetic data in a separate clone.

Never loads the real M5 bundle. Calls the real scheduler, provenance wrapper,
worker, model, inventory replay and result auditor with a tiny synthetic fixture.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-synthetic", action="store_true")
    parser.add_argument("--gpus", default="0,1,2,3")
    args = parser.parse_args(argv)
    if not args.execute_synthetic:
        print(
            "NOT RUN: use explicit --execute-synthetic for isolated fixture validation"
        )
        return 0
    devices = [int(v) for v in args.gpus.split(",")]
    if len(devices) != 4 or len(set(devices)) != 4:
        parser.error(
            "Four different GPU device indices required for this acceptance test"
        )
    state = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT
    )
    if state.strip():
        parser.error("Commit reviewed source before full-stack validation")
    parent = ROOT.parent / "code/validations"
    parent.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="m4-stack-", dir=parent))
    clone = destination / "github"
    subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--no-hardlinks",
            "--single-branch",
            str(ROOT),
            str(clone),
        ],
        check=True,
        timeout=15,
        capture_output=True,
    )
    # Only this interpreter imports the fixture clone's source/test utilities.
    sys.path.insert(0, str(clone / "src"))
    sys.path.insert(0, str(clone / "tests"))
    from m3_fixtures import config as fixture_config
    from m3_fixtures import make_fixture

    from inventory_ejor.baselines.planning import approval_template, build_plan, encode
    from inventory_ejor.data.preparation import prepare
    from inventory_ejor.data.provenance import fingerprint
    from inventory_ejor.data.views import separate_artifacts

    raw = clone / "data/raw/synthetic_acceptance"
    source = make_fixture(raw)
    cfg = fixture_config()
    cfg["horizon"] = 4
    cfg["development_window"]["stop"] = 229
    payloads, manifest = prepare(raw, source, encode(cfg))
    payloads, dispatch = separate_artifacts(payloads)
    manifest["learner_dispatch"] = dispatch
    manifest["artifacts"] = {
        name: {"sha256": fingerprint(value), "bytes": len(encode(value))}
        for name, value in payloads.items()
    }
    bundle = clone / "data/processed/synthetic_acceptance"
    bundle.mkdir(parents=True)
    for name, value in {**payloads, "manifest.json": manifest}.items():
        (bundle / name).write_bytes(encode(value))
    pilot = json.loads(
        (clone / "experiments/configs/m4_baseline_preview.json").read_text()
    )
    pilot["prepared_bundle"] = "data/processed/synthetic_acceptance"
    pilot["budgets"] = [28]
    pilot["seeds"] = [0]
    pilot["scenario"].update(lead_time=1, max_order=3, initial_pipeline=[])
    pilot["base_stock_levels"] = [0, 1, 2, 3, 4, 6]
    pilot["sampling"].update(tuning_paths=8, decision_paths=8)
    pilot["gp"]["steps"] = 2
    pilot["resources"].update(
        gpu_ids=devices,
        cpu_workers=2,
        job_timeout_seconds=30,
        session_timeout_seconds=90,
        max_jobs=12,
        gpu_memory_fraction=0.4,
    )
    config_path = clone / "experiments/configs/synthetic_stack_acceptance.json"
    config_path.write_bytes(encode(pilot))
    subprocess.run(
        ["git", "add", "--", str(config_path.relative_to(clone))],
        cwd=clone,
        check=True,
        timeout=10,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Synthetic acceptance",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "Synthetic acceptance configuration only",
        ],
        cwd=clone,
        check=True,
        timeout=10,
    )
    plan = build_plan(clone, config_path)
    if len(plan["jobs"]) != 12:
        raise ValueError(
            "Expected exactly 12 miniature jobs, not a retail-data campaign"
        )
    approval = approval_template(plan)
    for key in (
        "approved",
        "allow_model_fitting",
        "allow_baseline_scoring",
        "allow_gpu",
        "numerical_validation_completed",
    ):
        approval[key] = True
    approval["approved_by_owner"] = "Delegated synthetic-only preflight acceptance"
    (bundle / "plan.json").write_bytes(encode(plan))
    (bundle / "approval.json").write_bytes(encode(approval))
    env = dict(os.environ)
    env["PYTHONPATH"] = str(clone / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with (destination / "scheduler.log").open("x") as log:
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                str(clone / "scripts/run_baselines.py"),
                "--plan",
                str(bundle / "plan.json"),
                "--approval",
                str(bundle / "approval.json"),
                "--execute",
            ],
            cwd=clone,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=110,
        )
    sessions = list((clone / "results/runs").glob("m4-approved-*"))
    report = {
        "synthetic_only": True,
        "root": str(destination),
        "exit_code": process.returncode,
        "seconds": time.monotonic() - started,
    }
    if len(sessions) == 1:
        session = sessions[0]
        summary = json.loads((session / "session_summary.json").read_text())
        report.update(
            status=summary["status"],
            jobs_finished=summary["jobs_finished"],
            gpu_slots=sorted(
                {e["slot"] for e in summary["entries"] if e["device"] == "gpu"}
            ),
            aggregate_report_exists=(session / "aggregate_summary.json").is_file(),
            csv_exists=(session / "baseline_results.csv").is_file(),
            lock_released=not (clone.parent / "code/.baseline_execution.lock").exists(),
        )
    (destination / "validation_report.json").write_bytes(encode(report))
    print(json.dumps(report, indent=2))
    return (
        0
        if (
            process.returncode == 0
            and report.get("status") == "completed"
            and report.get("jobs_finished") == 12
            and report.get("gpu_slots") == sorted(devices)
            and report.get("aggregate_report_exists")
            and report.get("csv_exists")
            and report.get("lock_released")
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
