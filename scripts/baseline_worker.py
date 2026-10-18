"""Approved single-job entrypoint; runtime authorization is enforced in worker.main."""

from inventory_ejor.baselines.worker import main

if __name__ == "__main__":
    raise SystemExit(main())
