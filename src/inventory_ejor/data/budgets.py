"""Auditable real-observation access ledger, separate from synthetic computation.

This validates declared access and supplied learner views, not arbitrary Python
file reads. External artifacts need their own complete, pinned data lineage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta

from .contracts import History, Window, exact_keys, integer

PURPOSES = (
    "per_series_history",
    "cross_series_pooling",
    "pretraining",
    "hyperparameter_optimization",
    "calibration",
    "validation",
    "normalization",
    "demand_model_fitting",
    "eligibility",
    "initialization",
)
TRACKS = ("per_series", "pooled", "pretrained", "rich_data", "known_model_oracle")


@dataclass(frozen=True)
class SourcePolicy:
    dataset: str  # Logical version; trusted manifest binds it to exact source hashes.
    first_date: str
    allowed: tuple[Window, ...]
    forbidden_outcomes: tuple[Window, ...] = ()

    def __post_init__(self):
        if (
            not self.dataset
            or date.fromisoformat(self.first_date).isoformat() != self.first_date
        ):
            raise ValueError("invalid dataset policy")
        for spans in (self.allowed, self.forbidden_outcomes):
            if type(spans) is not tuple or any(
                not isinstance(w, Window) for w in spans
            ):
                raise ValueError("source windows must be immutable Window tuples")


def overlaps(a, b):
    return a.start < b.stop and b.start < a.stop


def access(history: History, window: Window | None = None):
    if type(history) is not History:
        raise ValueError("access requires a learner history")
    chosen = window or history.window
    if not history.window.contains(chosen):
        raise ValueError("access exceeds supplied history")
    return {
        "dataset": history.dataset,
        "series": history.series,
        "start": chosen.start,
        "stop": chosen.stop,
    }


def ledger(history: History, method: str, features: tuple[str, ...]):
    record = {
        "schema_version": 1,
        "method": method,
        "track": "per_series",
        "dataset": history.dataset,
        "series": history.series,
        "origin": history.origin,
        "history_days": len(history.observations),
        "access": {p: [] for p in PURPOSES},
        "pretrained_artifacts": [],
        "synthetic_transitions": 0,
        "optimization_trials": 0,
        "compute_allowance": {"cpu_seconds": 100, "memory_mb": 512, "gpu": 0},
        "features": list(features),
    }
    record["access"]["per_series_history"] = [access(history)]
    return record


def validate_ledger(record, policies: tuple[SourcePolicy, ...], history: History):
    """Count distinct observation identities; repeated uses are not new data."""
    exact_keys(
        record,
        (
            "schema_version",
            "method",
            "track",
            "dataset",
            "series",
            "origin",
            "history_days",
            "access",
            "pretrained_artifacts",
            "synthetic_transitions",
            "optimization_trials",
            "compute_allowance",
            "features",
        ),
        "information ledger",
    )
    if type(history) is not History:
        raise ValueError("ledger must be validated against the actual learner view")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise ValueError("unsupported ledger version")
    if not isinstance(record["method"], str) or not record["method"]:
        raise ValueError("method id required")
    if record["track"] not in TRACKS:
        raise ValueError("unknown information track")
    integer(record["origin"], "origin")
    integer(record["history_days"], "history_days")
    if (
        record["dataset"],
        record["series"],
        record["origin"],
        record["history_days"],
    ) != (history.dataset, history.series, history.origin, len(history.observations)):
        raise ValueError("ledger does not describe actual history")
    source = {p.dataset: p for p in policies}
    if len(source) != len(policies) or history.dataset not in source:
        raise ValueError("missing/duplicate source policy")
    decision_date = date.fromisoformat(source[history.dataset].first_date) + timedelta(
        days=history.origin - 1
    )
    for o in history.observations:
        expected = date.fromisoformat(source[history.dataset].first_date) + timedelta(
            days=o.day - 1
        )
        if o.date != expected.isoformat():
            raise ValueError("history dates inconsistent with source provenance")
    exact_keys(record["access"], PURPOSES, "access categories")
    unique, by_purpose = set(), {}
    declared_cells = 0
    for purpose, entries in record["access"].items():
        if not isinstance(entries, list):
            raise ValueError("access entries must be lists")
        identities = set()
        for entry in entries:
            exact_keys(entry, ("dataset", "series", "start", "stop"), "access entry")
            if (
                entry["dataset"] not in source
                or not isinstance(entry["series"], str)
                or not entry["series"]
            ):
                raise ValueError("unknown source/series")
            window = Window(entry["start"], entry["stop"])
            declared_cells += window.stop - window.start
            if declared_cells > 1_000_000:
                raise ValueError(
                    "M3 ledger exceeds bounded one-million access-cell audit"
                )
            policy = source[entry["dataset"]]
            if not any(w.contains(window) for w in policy.allowed):
                raise ValueError("access outside authorized source windows")
            if any(overlaps(window, w) for w in policy.forbidden_outcomes):
                raise ValueError("frozen outcome access")
            last_date = date.fromisoformat(policy.first_date) + timedelta(
                days=window.stop - 2
            )
            if last_date >= decision_date:
                raise ValueError("future observations in information ledger")
            own = (
                entry["dataset"] == history.dataset
                and entry["series"] == history.series
            )
            if not own and record["track"] not in (
                "pooled",
                "pretrained",
                "known_model_oracle",
            ):
                raise ValueError(
                    "cross-series/external access requires "
                    "a pooling/pretraining/oracle label"
                )
            if purpose == "per_series_history" and (
                not own or window != history.window
            ):
                raise ValueError("initial history does not match exact budget")
            if record["track"] == "per_series" and (
                not own or not history.window.contains(window)
            ):
                raise ValueError(
                    "extra real information requires a separately labeled track"
                )
            if purpose == "cross_series_pooling" and record["track"] not in (
                "pooled",
                "pretrained",
            ):
                raise ValueError("pooling must be explicitly labeled")
            if purpose == "pretraining" and record["track"] != "pretrained":
                raise ValueError("pretraining must be explicitly labeled")
            for day in window.days:
                identity = (entry["dataset"], entry["series"], day)
                if identity in identities:
                    raise ValueError(
                        "duplicate/overlapping access entry within category"
                    )
                identities.add(identity)
        by_purpose[purpose] = len(identities)
        unique.update(identities)
    if record["access"]["per_series_history"] != [access(history)]:
        raise ValueError("exact initial-history access entry required")
    for name in ("synthetic_transitions", "optimization_trials"):
        integer(record[name], name, 0)
    exact_keys(
        record["compute_allowance"], ("cpu_seconds", "memory_mb", "gpu"), "compute"
    )
    for name, value in record["compute_allowance"].items():
        integer(value, name, 0 if name == "gpu" else 1)
    features = record["features"]
    if not isinstance(features, list) or any(
        not isinstance(f, str) or not f for f in features
    ):
        raise ValueError("feature names must be explicit")
    if len(set(features)) != len(features):
        raise ValueError("duplicate feature")
    artifacts = record["pretrained_artifacts"]
    if not isinstance(artifacts, list):
        raise ValueError("pretrained artifacts must be a list")
    for artifact in artifacts:
        exact_keys(artifact, ("sha256", "lineage_complete"), "pretrained artifact")
        digest = artifact["sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            raise ValueError("artifact must have SHA256 identity")
        if artifact["lineage_complete"] is not True:
            raise ValueError(
                "unknown pretraining information cannot claim a measured budget"
            )
    if bool(artifacts) != bool(record["access"]["pretraining"]):
        raise ValueError("pretraining artifacts and data lineage must both be declared")
    if artifacts and record["track"] != "pretrained":
        raise ValueError("pretrained model cannot be a per-series-only method")
    return {
        "unique_real_observations": len(unique),
        "by_purpose": by_purpose,
        "synthetic_transitions": record["synthetic_transitions"],
        "source_policies": [asdict(p) for p in policies],
    }


def assert_comparable(records, policies, histories):
    """Require equal declared access, features and compute allowances."""
    if len(records) < 2 or len(records) != len(histories):
        raise ValueError("comparison requires matching records and histories")
    for record, history in zip(records, histories, strict=True):
        validate_ledger(record, policies, history)
    baseline = {k: v for k, v in records[0].items() if k != "method"}
    for record in records[1:]:
        if {k: v for k, v in record.items() if k != "method"} != baseline:
            raise ValueError(
                "unequal information/compute contracts; label separate comparator"
            )


def assert_same_evaluation(windows):
    if not windows or any(window != windows[0] for window in windows):
        raise ValueError("methods/budgets must share evaluation dates")


def study_information(
    dataset_version,
    source_fingerprint,
    selected_windows,
    candidates,
    screening,
    roster_series,
):
    """Trusted study-wide sales-cell union, separate from each learner's budget.

    Repeated budgets/origins and the selected candidates' screening cells are
    counted once. Full-source identity belongs only in this trusted ledger.
    """
    windows = sorted({(series, w.start, w.stop) for series, w in selected_windows})
    selected = {
        (series, day) for series, start, stop in windows for day in range(start, stop)
    }
    screened = {(series, day) for series in candidates for day in screening.days}
    combined = selected | screened
    return {
        "schema_version": 1,
        "dataset_version": dataset_version,
        "source_fingerprint": source_fingerprint,
        "cell_identity": "dataset_version, canonical item/store series, day",
        "selected_history_windows": [
            {"series": series, "start": start, "stop": stop}
            for series, start, stop in windows
        ],
        "screening_window": asdict(screening),
        "counts": {
            "selected_history_cells": len(selected),
            "candidate_screening_cells": len(screened),
            "screening_already_in_selected_history": len(selected & screened),
            "additional_screening_cells": len(screened - selected),
            "unique_historical_sales_cells": len(combined),
        },
        "by_series": [
            {
                "series": series,
                "unique_historical_sales_cells": sum(k == series for k, _ in combined),
            }
            for series in sorted({k for k, _ in combined})
        ],
        "catalog_metadata_series": roster_series,
        "roster_warning": (
            "Ex-post M5 item/store roster; selection/survivorship bias remains. "
            "Metadata access is distinct from historical sales-cell counts."
        ),
        "scope": (
            "Study-design historical sales access, including excluded candidates; "
            "not an individual learner budget. Evaluator outcomes are separate."
        ),
    }
