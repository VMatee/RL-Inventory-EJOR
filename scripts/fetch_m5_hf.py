"""Parallel, resumable M5 fetch from a pinned Hugging Face mirror.

Each output is cryptographically checked against the University of Nicosia
Zenodo archive's MD5 and exact file size before it is named a valid CSV.
This preserves comparability with the primary Zenodo/Kaggle dataset.

Run from github/:
  ../code/.venv/bin/python scripts/fetch_m5_hf.py --file sales_train_validation.csv
  ../code/.venv/bin/python scripts/fetch_m5.py --verify-only

Do NOT add raw CSVs to Git. Mirror is a delivery mechanism, not a new dataset.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
from fetch_m5 import DEST, FILES, validate, verify_all  # type: ignore[import-not-found]

# Immutable Hugging Face mirror commit. Original files are cross-checked
# against Zenodo record 10203108 before being accepted.
MIRROR_COMMIT = "849da4b68665cb20e6a904f7a5e2581093589483"
BASE = f"https://huggingface.co/datasets/kashif/M5/resolve/{MIRROR_COMMIT}/"


def _download_chunk(
    name: str,
    index: int,
    chunk_size: int,
    expected_size: int,
    chunk_dir: Path,
) -> tuple[int, int]:
    start = index * chunk_size
    end = min(start + chunk_size, expected_size) - 1
    expected = end - start + 1
    target = chunk_dir / f"{index:06d}.chunk"
    if target.exists():
        if target.is_file() and target.stat().st_size == expected:
            return index, expected
        raise ValueError(f"Invalid existing chunk size: {target}; inspect before retry")
    url = BASE + name
    temp = chunk_dir / f"{index:06d}.tmp"
    last_error = None
    for attempt in range(2):
        try:
            with requests.get(
                url, headers={"Range": f"bytes={start}-{end}"},
                timeout=(12, 30), stream=True,
            ) as response:
                response.raise_for_status()
                content_range = response.headers.get("Content-Range")
                if response.status_code != 206 or content_range != f"bytes {start}-{end}/{expected_size}":
                    raise ValueError(
                        f"Unsafe response for {name} chunk {index}: "
                        f"status={response.status_code}, range={content_range!r}"
                    )
                received = 0
                with temp.open("wb") as dst:
                    for piece in response.iter_content(chunk_size=1024 * 1024):
                        if piece:
                            received += len(piece)
                            if received > expected:
                                raise ValueError(f"Chunk {index} exceeds declared range")
                            dst.write(piece)
            if received != expected:
                raise ValueError(f"Truncated chunk {index}: got {received}, expected {expected}")
            temp.replace(target)
            return index, received
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if temp.exists():
                temp.unlink()
            if attempt == 1:
                raise RuntimeError(f"Failed {name} chunk {index}: {last_error}") from exc
    raise AssertionError("unreachable")


def fetch_hf(name: str, workers: int, chunk_mib: int) -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    final = DEST / name
    if final.exists():
        return validate(final, name)

    expected_size = FILES[name][0]
    chunk_size = chunk_mib * 1024 * 1024
    chunk_dir = DEST / f".{name}.hf_chunks"
    chunk_dir.mkdir(exist_ok=True)
    parts = (expected_size + chunk_size - 1) // chunk_size
    print(
        f"Downloading M5 {name} via pinned Hugging Face mirror: "
        f"{parts} ranges with {workers} workers; cross-checking Zenodo MD5.",
        flush=True,
    )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_download_chunk, name, i, chunk_size, expected_size, chunk_dir)
            for i in range(parts)
        ]
        total = 0
        for fut in as_completed(futures):
            _, n = fut.result()
            total += n
        if total != expected_size:
            raise ValueError(f"Chunks total {total}, expected {expected_size}")

    assembly = DEST / f".{name}.hf_assembling"
    if assembly.exists():
        raise FileExistsError(f"An old assembly file exists; inspect it: {assembly}")
    with assembly.open("wb") as out:
        for i in range(parts):
            with (chunk_dir / f"{i:06d}.chunk").open("rb") as chunk:
                shutil.copyfileobj(chunk, out, 1024 * 1024)
    try:
        info = validate(assembly, name)
    except Exception:
        print("Final assembled bytes fail pinned Zenodo integrity check; chunks retained.", file=sys.stderr)
        raise
    assembly.replace(final)
    # Delete only known own chunks after the verified file is installed.
    shutil.rmtree(chunk_dir)
    origins = DEST / "acquisition_sources.json"
    records = {}
    if origins.is_file():
        records = json.loads(origins.read_text(encoding="utf-8"))
    records[name] = {
        "downloaded_from": BASE + name,
        "mirror_commit": MIRROR_COMMIT,
        "verified_against": "https://zenodo.org/records/10203108",
        "sha256": info["sha256"],
        "checked_utc": datetime.now(timezone.utc).isoformat(),
    }
    temporary = DEST / "acquisition_sources.json.tmp"
    temporary.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(origins)
    print(f"Verified M5 {name}: {expected_size:,} bytes, Zenodo MD5 matches.")
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, choices=tuple(FILES))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--chunk-mib", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16 or not 1 <= args.chunk_mib <= 16:
        parser.error("workers must be 1-16 and chunk-mib 1-16")
    fetch_hf(args.file, args.workers, args.chunk_mib)
    verify_all()  # may report incomplete if remaining source files are absent
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
