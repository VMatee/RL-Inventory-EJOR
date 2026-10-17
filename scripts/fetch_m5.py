"""Acquire and verify the fixed public M5 Zenodo record, without Git-tracking raw data.

Usage from the Git checkout:
  ../code/.venv/bin/python scripts/fetch_m5.py --file calendar.csv
  ../code/.venv/bin/python scripts/fetch_m5.py --download-all
  ../code/.venv/bin/python scripts/fetch_m5.py --verify-only

This script does not select SKUs or create train/test splits. It pins the
University of Nicosia's Zenodo record files (DOI: 10.5281/zenodo.10203108).
The original Kaggle competition says "Subject to Competition Rules"; users
must review applicable terms before publishing or redistributing extracts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEST = REPO_ROOT / "data" / "raw" / "m5"
RECORD = "10203108"
BASE_URL = f"https://zenodo.org/api/records/{RECORD}/files/"
SOURCE = "https://zenodo.org/records/10203108"
ORIGINAL = "https://www.kaggle.com/competitions/m5-forecasting-accuracy/data"

# Immutable record metadata, checked against Zenodo's public records API.
FILES = {
    "calendar.csv": (103469, "3ffeab2991b0c8e861d008b39ea4c95c"),
    "sales_train_validation.csv": (120007726, "26a366a25beb57b0a8f4c7b148758f94"),
    "sales_train_evaluation.csv": (121736518, "b806dfc9f30a745102b708c09951f6aa"),
    "sell_prices.csv": (203395785, "08c591caa99e55daf3e0ccac913f7c85"),
    "sample_submission.csv": (5228786, "c281a69d7c011274899d92020a66e25b"),
}


def file_hashes(path: Path) -> tuple[int, str, str]:
    size = 0
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
            size += len(chunk)
    return size, md5.hexdigest(), sha256.hexdigest()


def validate(path: Path, name: str) -> dict:
    expected_size, expected_md5 = FILES[name]
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_size, actual_md5, actual_sha256 = file_hashes(path)
    if (actual_size, actual_md5) != (expected_size, expected_md5):
        raise ValueError(
            f"{name} integrity mismatch: bytes={actual_size}, md5={actual_md5}, "
            f"expected bytes={expected_size}, md5={expected_md5}. "
            "Never use or silently overwrite an invalid file."
        )
    return {
        "filename": name,
        "size_bytes": actual_size,
        "zenodo_md5": expected_md5,
        "sha256": actual_sha256,
        "verification_reference_url": f"{BASE_URL}{name}/content",
    }


def fetch_one(name: str, timeout: int) -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    final = DEST / name
    if final.exists():
        info = validate(final, name)
        print(f"Verified existing: {name} ({info['size_bytes']:,} bytes)")
        return info
    part = DEST / (name + ".part")
    if part.exists() and not part.is_file():
        raise ValueError(f"Refusing unsafe partial-file path: {part}")
    url = f"{BASE_URL}{name}/content"
    cmd = [
        "curl", "--fail", "--location", "--silent", "--show-error",
        "--connect-timeout", "10",
        "--max-time", str(timeout),
        "--retry", "1",
        "--continue-at", "-",
        "--output", str(part),
        url,
    ]
    print(f"Fetching M5 {name} from Zenodo record {RECORD} (<= {timeout}s).", flush=True)
    try:
        subprocess.run(cmd, check=True, timeout=timeout + 8)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"Download not complete: {name} ({exc}). Partial remains resumable.", file=sys.stderr)
        raise SystemExit(2) from exc
    try:
        info = validate(part, name)
    except (ValueError, FileNotFoundError) as exc:
        print(f"File did not pass checksum verification: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc
    part.replace(final)  # atomic on same filesystem after checksum verification
    print(f"Verified and installed: {name} ({info['size_bytes']:,} bytes).")
    return info


def verify_all() -> int:
    completed = []
    missing = []
    invalid = []
    acquired = {}
    origin_path = DEST / "acquisition_sources.json"
    if origin_path.is_file():
        acquired = json.loads(origin_path.read_text(encoding="utf-8"))
    for name in FILES:
        try:
            info = validate(DEST / name, name)
            info["acquired_from"] = acquired.get(name, {}).get(
                "downloaded_from", f"{BASE_URL}{name}/content"
            )
            completed.append(info)
        except FileNotFoundError:
            missing.append(name)
        except ValueError as exc:
            invalid.append(str(exc))
    result = {
        "dataset": "M5 Forecasting - Accuracy",
        "record_id": RECORD,
        "record_doi": "10.5281/zenodo.10203108",
        "secondary_source": SOURCE,
        "original_source": ORIGINAL,
        "origin_license_note": "Kaggle original: Subject to Competition Rules; redistribution not assessed",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "completed": completed,
        "missing": missing,
        "invalid": invalid,
        "status": "complete" if not missing and not invalid else "incomplete",
    }
    DEST.mkdir(parents=True, exist_ok=True)
    temp = DEST / "manifest.json.tmp"
    temp.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(DEST / "manifest.json")
    print(json.dumps({
        "status": result["status"],
        "verified_count": len(completed),
        "expected_count": len(FILES),
        "total_verified_bytes": sum(it["size_bytes"] for it in completed),
        "missing": missing,
        "invalid": invalid,
        "local_manifest": str(DEST / "manifest.json"),
    }, indent=2))
    return 0 if result["status"] == "complete" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--file", choices=tuple(FILES))
    mode.add_argument("--download-all", action="store_true")
    mode.add_argument("--verify-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=75)
    opts = parser.parse_args()
    if not 15 <= opts.timeout_seconds <= 600:
        parser.error("--timeout-seconds must be between 15 and 600")
    if opts.file:
        fetch_one(opts.file, opts.timeout_seconds)
        verify_all()  # reports that other required files may not be present yet
        return 0  # downloading a single requested file succeeded
    if opts.download_all:
        for name in FILES:
            fetch_one(name, opts.timeout_seconds)
    return verify_all()


if __name__ == "__main__":
    raise SystemExit(main())
