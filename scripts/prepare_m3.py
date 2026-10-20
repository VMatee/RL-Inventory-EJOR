"""Bounded local M3 development demo. No model fitting or inventory experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import sys
import tempfile
import time
from pathlib import Path

from inventory_ejor.data.preparation import parse_config, prepare
from inventory_ejor.data.protocol import metadata_config_path
from inventory_ejor.data.provenance import (
    canonical,
    code_provenance,
    file_hash,
    read_json,
    write_exclusive,
)
from inventory_ejor.data.views import separate_artifacts

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args(argv)
    started = time.monotonic()
    try:
        raw = metadata_config_path(args.config, ROOT).read_bytes()
        cfg, _, _ = parse_config(raw)
        if args.seed != cfg["seed"]:
            raise ValueError("CLI seed must equal the consumed config selection seed")
        # Linux CPU-only process: stdlib pipeline, bounded address space + CPU time.
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (110, 110))
        input_path = ROOT / "data/manifests/m5_verified_20261017.json"
        payloads, manifest = prepare(
            ROOT / "data/raw/m5", read_json(input_path.read_bytes()), raw
        )
        payloads, dispatch = separate_artifacts(payloads)
        manifest["learner_dispatch"] = dispatch
        manifest.update(
            {
                "code": code_provenance(ROOT),
                "input_manifest_sha256": file_hash(input_path),
                "config_file_sha256": hashlib.sha256(raw).hexdigest(),
                "command": [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    *sys.argv[1:],
                ],
                "seed": args.seed,
                "cpu_only": True,
                "limits": {
                    "address_space_mb": 512,
                    "cpu_seconds": 110,
                    "external_wall_timeout_required": 120,
                },
            }
        )
        manifest["artifacts"] = {
            name: {
                "sha256": hashlib.sha256(canonical(value)).hexdigest(),
                "bytes": len(canonical(value)),
            }
            for name, value in payloads.items()
        }
        destination = ROOT / "data/processed"
        if destination.is_symlink() or destination.resolve() != destination:
            raise ValueError(
                "processed destination must be the canonical local directory"
            )
        destination.mkdir(exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="m3-demo-", dir=destination))
        for name, value in payloads.items():
            write_exclusive(output / name, value)
        manifest["runtime_seconds"] = time.monotonic() - started
        manifest["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        write_exclusive(output / "manifest.json", manifest)
    except (OSError, ValueError, TypeError, RuntimeError, MemoryError, KeyError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                "status": manifest["status"],
                "quality": manifest["quality"],
                "runtime_seconds": manifest["runtime_seconds"],
                "peak_rss_kib": manifest["peak_rss_kib"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
