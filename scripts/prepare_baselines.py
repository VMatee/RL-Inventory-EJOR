"""Prepare an M4a review bundle, never fit or evaluate any baseline."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from inventory_ejor.baselines.planning import approval_template, build_plan, encode

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        plan = build_plan(ROOT, args.config)
        parent = ROOT / "data/processed"
        if parent.is_symlink():
            raise ValueError("Processed directory must not be a symlink")
        parent.mkdir(exist_ok=True)
        dest = Path(tempfile.mkdtemp(prefix="m4-plan-", dir=parent))
        for name, payload in (
            ("plan.json", plan),
            ("approval.example.json", approval_template(plan)),
        ):
            with (dest / name).open("xb") as f:
                f.write(encode(payload))
        text = (
            "# Baseline review bundle - NOT AUTHORIZED TO RUN\n\n"
            + json.dumps(plan["summary"], indent=2)
            + "\n\n"
            "No model was fitted and no baseline was evalu"
            "ated. Do not change the approval flags "
            "until numerical validation and the proposed scenario have been reviewed.\n"
            "After committing reviewed code, regenerate th"
            "is plan and approve its new hash; "
            "a dirty-source plan cannot be executed. See d"
            "ocs/M4_BASELINE_PREPARATION.md.\n"
        )
        with (dest / "REVIEW.md").open("x") as f:
            f.write(text)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {
                "output": str(dest.relative_to(ROOT)),
                "summary": plan["summary"],
                "execution_authorized": False,
                "numerical_validation": "not_executed_by_preparation_command",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
