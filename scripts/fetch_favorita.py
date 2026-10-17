"""Stage authentic item-by-store Corporacion Favorita 2017 competition archives.

Competition source (NOT the newer product-family Store Sales dataset):
https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data

Kaggle access is subject to competition rules; the user must sign in and
accept the rules in their own browser. This script never enters credentials,
accepts terms on someone's behalf, or uses unverified mirrors. Raw files
remain local and Git-ignored.

From github/:
  ../code/.venv/bin/python scripts/fetch_favorita.py --status
  ../code/.venv/bin/python scripts/fetch_favorita.py --download
  ../code/.venv/bin/python scripts/fetch_favorita.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw" / "favorita"
ZIP = DEST / "favorita-grocery-sales-forecasting.zip"
COMPETITION = "favorita-grocery-sales-forecasting"
SOURCE = f"https://www.kaggle.com/competitions/{COMPETITION}/data"
EXPECTED = frozenset({
    "train.csv.7z", "test.csv.7z", "stores.csv.7z", "items.csv.7z",
    "oil.csv.7z", "transactions.csv.7z", "holidays_events.csv.7z",
    "sample_submission.csv.7z",
})


def credentials_present() -> bool:
    # This deliberately checks presence only, never reads or prints secrets.
    # Pinned legacy Kaggle CLI 1.7.4 authenticates with username+key,
    # not a standalone KAGGLE_API_TOKEN; avoid false-positive readiness.
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    return (Path.home() / ".kaggle" / "kaggle.json").is_file()


def sha256_file(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def inspect() -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    archives = {}
    for name in sorted(EXPECTED):
        path = DEST / name
        if path.is_file():
            archives[name] = {"size_bytes": path.stat().st_size}
    zip_entries = []
    zip_status = None
    if ZIP.is_file():
        try:
            with ZipFile(ZIP) as archive:
                zip_entries = sorted(
                    Path(member.filename).name
                    for member in archive.infolist() if not member.is_dir()
                )
            missing = sorted(EXPECTED - set(zip_entries))
            zip_status = "complete_directory" if not missing else f"missing_names:{missing}"
        except BadZipFile:
            zip_status = "invalid_zip"
    return {
        "dataset": "Corporacion Favorita Grocery Sales Forecasting (2017, item/store)",
        "source": SOURCE,
        "license_note": "Subject to Competition Rules: account acceptance required",
        "credentials_configured": credentials_present(),
        "archive_present": ZIP.is_file(),
        "archive_bytes": ZIP.stat().st_size if ZIP.is_file() else 0,
        "zip_status": zip_status,
        "zip_entries": zip_entries,
        "individual_archives_present": sorted(archives),
        "expected_archive_names": sorted(EXPECTED),
        "status": (
            "downloaded_unverified"
            if ZIP.is_file() and zip_status == "complete_directory"
            else "not_acquired_or_incomplete"
        ),
    }


def download(timeout_seconds: int) -> int:
    if not credentials_present():
        print(
            "BLOCKED: no Kaggle credentials on this PC. In your own browser, "
            f"sign in and accept the rules at {SOURCE}. Then configure Kaggle "
            "authentication on this machine. Do not paste tokens into chat. "
            "The old CLI in Python 3.10 uses legacy kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY.",
            file=sys.stderr,
        )
        return 2
    if ZIP.exists():
        print("Existing zip will not be overwritten. Inspect with --verify.")
        return 3
    cli = Path(sys.executable).parent / "kaggle"
    if not cli.is_file():
        print(f"Kaggle CLI not installed at {cli}", file=sys.stderr)
        return 2
    DEST.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(cli), "competitions", "download", "-c", COMPETITION,
        "-p", str(DEST),
    ]
    print("Requesting competition archive through authorized Kaggle CLI.", flush=True)
    try:
        subprocess.run(cmd, check=True, timeout=timeout_seconds)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(
            f"Kaggle download failed or timed out: {type(exc).__name__}. "
            "Check accepted competition rules, credentials, and network. "
            "Do not assume that a partial archive is usable.",
            file=sys.stderr,
        )
        return 3
    return verify()


def verify() -> int:
    status = inspect()
    if not ZIP.is_file():
        print(json.dumps(status, indent=2))
        print("No complete Kaggle ZIP found; raw Favorita is not ready.")
        return 1
    if status["zip_status"] != "complete_directory":
        print(json.dumps(status, indent=2))
        return 1
    # Explicit CRC pass; tests compressed archive integrity without extracting >5GB.
    with ZipFile(ZIP) as archive:
        bad_name = archive.testzip()
        if bad_name:
            print(f"CRC failure in {bad_name!r}", file=sys.stderr)
            return 1
        member_info = [
            {"name": Path(m.filename).name, "uncompressed_bytes": m.file_size}
            for m in archive.infolist() if not m.is_dir()
        ]
    evidence = {
        "dataset": status["dataset"],
        "source": SOURCE,
        "license_note": status["license_note"],
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "archive_file": ZIP.name,
        "archive_size_bytes": ZIP.stat().st_size,
        "sha256": sha256_file(ZIP),
        "members": member_info,
        "verified": True,
        "caveat": "ZIP+CRC valid; nested 7z and individual CSV schemas not yet tested",
    }
    (DEST / "manifest.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": "verified_kaggle_zip",
        "archive_bytes": evidence["archive_size_bytes"],
        "member_count": len(member_info),
        "sha256": evidence["sha256"],
    }, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--status", action="store_true")
    actions.add_argument("--download", action="store_true")
    actions.add_argument("--verify", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    if not 30 <= args.timeout_seconds <= 7200:
        parser.error("--timeout-seconds must be 30-7200")
    if args.status:
        print(json.dumps(inspect(), indent=2))
        return 0
    if args.download:
        return download(args.timeout_seconds)
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
