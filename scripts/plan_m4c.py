"""Validate a candidate M4c protocol and print metadata only; never read sales.

Usage: python -B scripts/plan_m4c.py --config <candidate-protocol.json>
The output includes a nonapproving freeze template. This CLI has no data reader,
release, execution, model-fitting or artifact-preparation option.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from inventory_ejor.data.protocol import metadata_config_path, plan_protocol
from inventory_ejor.data.provenance import canonical, read_json
from inventory_ejor.data.releases import freeze_template

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        path = metadata_config_path(args.config, ROOT)
        config = read_json(path.read_bytes())
        print(
            canonical(
                {
                    "plan": plan_protocol(config),
                    "freeze_template": freeze_template(config),
                }
            ).decode(),
            end="",
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
