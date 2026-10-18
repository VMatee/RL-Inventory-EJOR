"""Independent read-only audit of prepared M3 demo artifacts against original CSVs.

Uses csv/hashlib/statistics directly, not production preparation or normalization.
Run under `timeout 120s`. No model fitting, output files or dataset modification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import resource
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(directory, repeat=None, snapshot=None):
    base = (ROOT / "data/processed").resolve()
    require(
        base in directory.resolve().parents, "audit input must be under data/processed"
    )
    manifest = json.loads((directory / "manifest.json").read_text())
    original = json.loads(
        (ROOT / "data/manifests/m5_verified_20261017.json").read_text()
    )
    version = manifest.get("schema_version")
    require(version in (1, 2), "unsupported preparation manifest version")
    if version == 2:
        identity = hashlib.sha256(
            (json.dumps(manifest["inputs"], sort_keys=True, indent=2) + "\n").encode()
        ).hexdigest()
        require(
            manifest["dataset"] == "m5-sha256:" + identity,
            "trusted full-source fingerprint mismatch",
        )
        require(
            manifest["learner_dataset_version"]
            == manifest["config"]["dataset_version"],
            "logical dataset version/config mismatch",
        )
    for source in original["files"]:
        path = ROOT / "data/raw/m5" / source["filename"]
        require(sha(path) == source["sha256"], "original input hash mismatch")
        require(
            manifest["inputs"][source["filename"]]
            == {"sha256": source["sha256"], "bytes": source["bytes"]},
            "prepared provenance does not match original manifest",
        )
    for name, expected in manifest["artifacts"].items():
        require(Path(name).name == name, "invalid artifact path")
        path = directory / name
        require(
            sha(path) == expected["sha256"]
            and path.stat().st_size == expected["bytes"],
            "artifact hash/length mismatch",
        )
    with (ROOT / "data/raw/m5/calendar.csv").open(newline="") as stream:
        dates = {int(row["d"][2:]): row["date"] for row in csv.DictReader(stream)}
    cohort = json.loads((directory / "cohort.json").read_text())
    selected = set(cohort["included"])
    screen = cohort["screening_window"]
    needed = {
        key: set(range(screen["start"], screen["stop"])) for key in cohort["candidates"]
    }
    for split in manifest["splits"]:
        series = split["token"].split("@")[0]
        needed[series].update(
            range(split["history"]["start"], split["evaluation"]["stop"])
        )
    values = {}
    with (ROOT / "data/raw/m5/sales_train_evaluation.csv").open(newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        item, store = header.index("item_id"), header.index("store_id")
        positions = {
            day: header.index(f"d_{day}") for day in set.union(*needed.values())
        }
        for row in reader:
            series = row[item] + "_" + row[store]
            if series in needed:
                values[series] = {d: int(row[positions[d]]) for d in needed[series]}
    for key in cohort["candidates"]:
        active = sum(values[key][d] > 0 for d in range(screen["start"], screen["stop"]))
        require(
            (key in selected) == (active >= cohort["min_nonzero"]),
            "cohort screen mismatch",
        )
    unique_history = set()
    unique_targets = set()
    for split in manifest["splits"]:
        learner = json.loads(
            (directory / manifest["learner_dispatch"][split["token"]]).read_text()
        )
        h = learner["history"]
        if version == 2:
            require(
                h["dataset"] == manifest["learner_dataset_version"],
                "learner dataset version mismatch",
            )
        window = split["history"]
        require(
            [o["day"] for o in h["observations"]]
            == list(range(window["start"], h["origin"])),
            "history day/budget mismatch",
        )
        require(
            window["stop"] == h["origin"] == split["evaluation"]["start"],
            "cutoff mismatch",
        )
        for obs in h["observations"]:
            d, key = obs["day"], h["series"]
            require(
                obs["sales"] == values[key][d] and obs["date"] == dates[d],
                "history differs from original CSV",
            )
            unique_history.add((key, d))
        n = learner["normalization"]
        training = [values[h["series"]][d] for d in n["fitted_days"]]
        require(
            set(n["fitted_days"]) <= {o["day"] for o in h["observations"]},
            "normalization leakage",
        )
        require(
            math.isclose(n["mean"], statistics.mean(training), abs_tol=1e-12),
            "normalization mean mismatch",
        )
        require(
            math.isclose(n["scale"], statistics.pstdev(training) or 1.0, abs_tol=1e-12),
            "normalization scale mismatch",
        )
    outcomes = json.loads((directory / "evaluation.json").read_text())
    for target in outcomes.values():
        for obs in target["observations"]:
            d, key = obs["day"], target["series"]
            require(
                obs["sales"] == values[key][d] and obs["date"] == dates[d],
                "outcome differs from CSV",
            )
            unique_targets.add((key, d))
    # Primary demo is one origin; multi-origin histories may contain earlier outcomes.
    if len(manifest["config"]["origins"]) == 1:
        require(not unique_history & unique_targets, "history/outcome overlap")
    screened = {
        (key, day)
        for key in cohort["candidates"]
        for day in range(screen["start"], screen["stop"])
    }
    study_counts = {
        "selected_history_cells": len(unique_history),
        "candidate_screening_cells": len(screened),
        "screening_already_in_selected_history": len(unique_history & screened),
        "additional_screening_cells": len(screened - unique_history),
        "unique_historical_sales_cells": len(unique_history | screened),
    }
    if version == 2:
        study = manifest["study_information"]
        require(
            study["counts"] == study_counts, "study-wide information counts mismatch"
        )
        require(
            study["source_fingerprint"] == manifest["dataset"]
            and study["dataset_version"] == manifest["learner_dataset_version"],
            "study source/version binding mismatch",
        )
        by_series = [
            {
                "series": key,
                "unique_historical_sales_cells": sum(
                    series == key for series, _ in unique_history | screened
                ),
            }
            for key in sorted(cohort["candidates"])
        ]
        require(study["by_series"] == by_series, "study per-series counts mismatch")
    matched = None
    if repeat:
        require(base in repeat.resolve().parents, "repeat must be under data/processed")
        second = json.loads((repeat / "manifest.json").read_text())
        require(
            manifest["artifacts"] == second["artifacts"],
            "repeat artifact fingerprints differ",
        )
        for name, entry in second["artifacts"].items():
            require(
                Path(name).name == name and sha(repeat / name) == entry["sha256"],
                "repeat artifact modified",
            )
        matched = len(second["artifacts"])
    protected = None
    if snapshot:
        before = json.loads(snapshot.read_text())
        for name, entry in before.items():
            path = ROOT / name
            require(
                path.is_file()
                and path.stat().st_size == entry["bytes"]
                and sha(path) == entry["sha256"],
                "historical artifact changed: " + name,
            )
        protected = len(before)
    return {
        "manifest_schema_version": version,
        "study_information_verified": version == 2,
        "study_information_counts": study_counts,
        "original_input_hashes_verified": len(original["files"]),
        "learner_views_verified": len(manifest["learner_dispatch"]),
        "unique_selected_history_cells": len(unique_history),
        "zero_selected_history_cells": sum(
            values[key][d] == 0 for key, d in unique_history
        ),
        "unique_development_outcome_cells": len(unique_targets),
        "candidate_screening_cells": cohort["screening_observations"],
        "excluded_candidate_screening_cells": (
            len(cohort["candidates"]) - len(selected)
        )
        * (screen["stop"] - screen["start"]),
        "repeat_artifacts_identical": matched,
        "preexisting_files_unchanged": protected,
        "scientific_claim": "engineering audit only",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--repeat", type=Path)
    parser.add_argument("--preservation-snapshot", type=Path)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (110, 110))
    try:
        result = audit(args.directory, args.repeat, args.preservation_snapshot)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
