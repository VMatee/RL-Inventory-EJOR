"""Local-only provenance and exclusive artifact writes; no network operations."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

FILES = (
    "calendar.csv",
    "sales_train_validation.csv",
    "sales_train_evaluation.csv",
    "sell_prices.csv",
    "sample_submission.csv",
)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def read_json(raw):
    return json.loads(
        raw,
        object_pairs_hook=unique_object,
        parse_constant=lambda s: (_ for _ in ()).throw(ValueError(f"invalid JSON {s}")),
    )


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path: Path, limits=None):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            if limits:
                limits.check()
            digest.update(block)
    return digest.hexdigest()


def verify_inputs(root: Path, manifest, limits):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("invalid input manifest")
    entries = manifest["files"]
    if len(entries) != len(FILES) or {e.get("filename") for e in entries} != set(FILES):
        raise ValueError("input manifest must describe exactly five original M5 files")
    actual = {}
    for entry in entries:
        name = entry["filename"]
        path = root / name
        size = path.stat().st_size
        digest = file_hash(path, limits)
        if (
            type(entry.get("bytes")) is not int
            or size != entry["bytes"]
            or digest != entry.get("sha256")
        ):
            raise ValueError(f"input checksum/size mismatch: {name}")
        actual[name] = {"bytes": size, "sha256": digest}
    return actual


def code_provenance(root: Path):
    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.PIPE, timeout=5
        ).strip()

    paths = sorted((root / "src/inventory_ejor").rglob("*.py")) + [
        root / "scripts/prepare_m3.py"
    ]
    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=all")),
        "source_sha256": {str(p.relative_to(root)): file_hash(p) for p in paths},
        "protocol_sha256": file_hash(root / "experiments/protocol/EVALUATION.md"),
        "python": platform.python_version(),
        "dependencies": "Python standard library only",
    }


def write_exclusive(path, payload):
    with path.open("xb") as stream:
        stream.write(canonical(payload))
