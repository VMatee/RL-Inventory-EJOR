"""One bounded artifact per learner task; evaluator data has a separate file."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .contracts import (
    Feature,
    History,
    Normalization,
    Observation,
    Window,
    exact_keys,
    features_at,
    fit_normalization,
    integer,
)
from .provenance import read_json


@dataclass(frozen=True)
class LearnerView:
    history: History
    normalization: Normalization
    features: tuple[Feature, ...]


def separate_artifacts(payloads):
    outputs = {
        name: value for name, value in payloads.items() if name != "training.json"
    }
    dispatch = {}
    for token, value in payloads["training.json"].items():
        filename = "learner-" + hashlib.sha256(token.encode()).hexdigest() + ".json"
        if filename in outputs:
            raise ValueError("duplicate learner artifact identity")
        outputs[filename] = value
        dispatch[token] = filename
    return outputs, dispatch


def load_learner(
    path: Path,
    *,
    sha256: str,
    dataset: str,
    series: str,
    origin: int,
    budget: int,
    allowed_features: tuple[str, ...] = ("month", "weekday"),
) -> LearnerView:
    """Dispatcher supplies one pinned file and expected contract, never a raw reader.

    This is an accidental-leakage boundary, not an OS sandbox against malicious
    code. Source fingerprints and task IDs must not be used as predictive features.
    """
    integer(origin, "origin")
    integer(budget, "budget")
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("learner artifact exceeds 8 MiB bound")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError("learner artifact fingerprint mismatch")
    value = read_json(raw)
    exact_keys(value, ("history", "normalization", "features"), "learner view")
    h = value["history"]
    exact_keys(h, ("dataset", "series", "origin", "observations"), "history")
    history = History(
        h["dataset"],
        h["series"],
        h["origin"],
        tuple(Observation(**o) for o in h["observations"]),
    )
    if (history.dataset, history.series, history.origin, len(history.observations)) != (
        dataset,
        series,
        origin,
        budget,
    ):
        raise ValueError("learner artifact does not match assigned history budget")
    n = value["normalization"]
    exact_keys(n, ("mean", "scale", "fitted_days"), "normalization")
    if not isinstance(n["fitted_days"], list) or not n["fitted_days"]:
        raise ValueError("normalization training lineage is required")
    expected = fit_normalization(
        history, Window(n["fitted_days"][0], n["fitted_days"][-1] + 1)
    )
    if (n["mean"], n["scale"], tuple(n["fitted_days"])) != (
        expected.mean,
        expected.scale,
        expected.fitted_days,
    ):
        raise ValueError("normalization does not match training-only fit")
    features = tuple(Feature(**f) for f in value["features"])
    if any(f.name not in allowed_features for f in features):
        raise ValueError("undeclared feature in learner artifact")
    features_at(features, origin)
    first = history.observations[0]
    for feature in features:
        if feature.name in ("month", "weekday"):
            civil_date = date.fromisoformat(first.date) + timedelta(
                days=feature.day - first.day
            )
            expected_value = (
                civil_date.month if feature.name == "month" else civil_date.weekday()
            )
            if (
                feature.value != expected_value
                or feature.available_day != 0
                or feature.evidence != "deterministic civil calendar"
            ):
                raise ValueError(
                    "calendar feature differs from deterministic civil date"
                )
    return LearnerView(history, expected, features)
