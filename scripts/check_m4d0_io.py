"""Metadata-only M4d-0 preparation I/O guard. Does NOT open observations.

Example:
  python -B scripts/check_m4d0_io.py \
      --config experiments/configs/m4c_protocol_candidate.json \
      --sizes /path/to/size-metadata.json --max-logical-gib 8

Sizes JSON must contain exactly five M5 source basenames mapped to byte sizes.
The example candidate currently exceeds an 8 GiB allowance by a wide margin.
No real-data preparation is enabled by passing this metadata check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from inventory_ejor.data.m4d0_io import (
    project_naive_preparation_io,
    require_preparation_budget,
)
from inventory_ejor.data.protocol import metadata_config_path
from inventory_ejor.data.provenance import read_json

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--sizes", required=True, type=Path)
    parser.add_argument("--max-logical-gib", required=True, type=int)
    args = parser.parse_args(argv)
    try:
        config = read_json(metadata_config_path(args.config, ROOT).read_bytes())
        sizes_path = metadata_config_path(args.sizes, ROOT)
        if sizes_path.stat().st_size > 4096:
            raise ValueError("Source-size metadata exceeds 4 KiB")
        sizes = read_json(sizes_path.read_bytes())
        projection = project_naive_preparation_io(config, sizes)
        result = {
            "metadata_only": True,
            "source_observations_opened": False,
            "execution_authorized": False,
            "projection": projection,
        }
        try:
            require_preparation_budget(
                projection, maximum_logical_bytes=args.max_logical_gib * (2**30)
            )
        except ValueError as exc:
            result["within_explicit_budget"] = False
            result["warning"] = str(exc)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 2
        result["within_explicit_budget"] = True
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(
            f"M4D0 METADATA GATE REFUSED: {type(exc).__name__}: {exc}", file=sys.stderr
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
