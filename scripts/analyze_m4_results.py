"""Reproduce read-only M4 development results; never run baseline jobs.

Usage:
  ../code/.venv/bin/python -B scripts/analyze_m4_results.py \
      --session results/runs/m4-approved-yc4xtrp1
  ../code/.venv/bin/python -B scripts/analyze_m4_results.py \
      --session results/runs/m4-approved-yc4xtrp1 \
      --output-dir results/analysis/m4b-original-192

The optional output directory must not exist. It is Git-ignored and contains
private per-series data, so only the aggregate public JSON may be shared.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from inventory_ejor.baselines.analysis import analyze_session, public_report
from inventory_ejor.baselines.planning import encode, inside

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument(
        "--output-dir", type=Path, help="Optional NEW ignored directory"
    )
    args = parser.parse_args(argv)
    try:
        session = inside(ROOT, args.session, "results/runs")
        audit = analyze_session(ROOT, session)
        public = public_report(audit)
        if args.output_dir is not None:
            output = inside(ROOT, args.output_dir, "results/analysis")
            expected_parent = (ROOT / "results/analysis").resolve()
            if output.parent != expected_parent:
                raise ValueError("Output must be a direct child of results/analysis")
            expected_parent.mkdir(parents=True, exist_ok=True)
            output.mkdir(mode=0o700, exist_ok=False)
            (output / "audit_private.json").write_bytes(encode(audit))
            (output / "audit_public.json").write_bytes(encode(public))
            print(
                json.dumps(
                    {
                        "status": "verified_read_only_development_analysis",
                        "verified_jobs": audit["integrity"]["verified_jobs"],
                        "output": str(output.relative_to(ROOT)),
                        "private_artifacts": "remain_git_ignored",
                        "baseline_jobs_executed": 0,
                    },
                    indent=2,
                )
            )
        else:
            print(encode(public).decode(), end="")
    except (KeyError, ValueError, OSError, TypeError, AssertionError) as exc:
        print(
            f"M4 DEVELOPMENT AUDIT REFUSED: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
