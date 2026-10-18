"""Baseline scheduler: dry-run by default; no execution without owner approval."""

from inventory_ejor.baselines.launcher import main

if __name__ == "__main__":
    raise SystemExit(main())
