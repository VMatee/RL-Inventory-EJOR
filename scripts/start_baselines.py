"""One-shot launch of the locally sealed, user-delegated M5 development plan.

--check performs preflight only. Invoking without --check is the USER's start
command; it launches the approved development jobs in the foreground.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from inventory_ejor.baselines.execution import verify_artifacts
from inventory_ejor.baselines.launcher import main as launch
from inventory_ejor.baselines.launcher import parse_idle_gpu_inventory
from inventory_ejor.baselines.planning import (
    check_approval,
    check_live_plan,
    inside,
    read_json,
    sha_file,
)

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        pointer = read_json(ROOT.parent / "code/BASELINE_READY.json")
        plan_path = inside(ROOT, pointer["plan"], "data/processed")
        approval_path = inside(ROOT, pointer["approval"], "data/processed")
        if sha_file(plan_path) != pointer["plan_file_sha256"]:
            raise ValueError("Sealed plan bytes changed")
        if sha_file(approval_path) != pointer["approval_file_sha256"]:
            raise ValueError("Sealed approval bytes changed")
        plan, approval = read_json(plan_path), read_json(approval_path)
        check_live_plan(ROOT, plan)
        check_approval(plan, approval)
        artifact_count = verify_artifacts(ROOT, plan)
        if (ROOT.parent / "code/.baseline_execution.lock").exists():
            raise RuntimeError("An active session or unresolved stale lock exists")
        marker = plan_path.parent / "STARTED.json"
        if marker.exists():
            raise RuntimeError(
                "This campaign has already started; outputs are preserved. "
                "No automatic duplicate campaign or rerun."
            )
        inventory = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,uuid,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
        )
        devices = parse_idle_gpu_inventory(
            inventory,
            plan["config"]["resources"]["gpu_ids"],
            plan["config"]["resources"]["gpu_memory_fraction"],
        )
        print(
            json.dumps(
                {
                    "ready": True,
                    "mode": "PREFLIGHT_ONLY" if args.check else "USER_START",
                    "commit": plan["git"]["commit"],
                    "jobs": len(plan["jobs"]),
                    "gpus": list(devices),
                    "verified_artifacts": artifact_count,
                    "scope": "M5 development only; not final publication evaluation",
                },
                indent=2,
            ),
            flush=True,
        )
        if args.check:
            return 0
        with marker.open("x") as stream:
            json.dump({"plan": str(plan_path), "source": plan["git"]["commit"]}, stream)
        return launch(
            [
                "--plan",
                str(plan_path),
                "--approval",
                str(approval_path),
                "--execute",
            ]
        )
    except (ValueError, RuntimeError, PermissionError, OSError, KeyError) as exc:
        print(f"START REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
