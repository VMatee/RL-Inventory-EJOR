"""Released, stage-specific preparation; no combined learner/evaluator bundle.

Only the trusted preparer receives a bounded source. Learners receive immutable
LearnerView values with no source, evaluator handle, raw fingerprint or release
metadata. Scorer access is a different API and a separately approved capability.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta

from .budgets import SourcePolicy, access, ledger, validate_ledger
from .contracts import (
    EvaluationTargets,
    Feature,
    History,
    Observation,
    Window,
    fit_normalization,
)
from .evidence import access_receipt
from .m5 import rank_candidates
from .protocol import plan_protocol, require, task_for
from .provenance import fingerprint
from .releases import authorize_task
from .views import LearnerView


def select_cohort(config, catalog):
    """Only canonical metadata IDs; never accepts observations or sales screens."""
    plan_protocol(config)
    require(
        type(catalog) is tuple and 0 < len(catalog) <= 40_000,
        "Bounded immutable metadata catalog required",
    )
    require(
        all(isinstance(x, str) and x and x.strip() == x for x in catalog)
        and len(catalog) == len(set(catalog)),
        "Unique canonical metadata IDs required",
    )
    require(
        fingerprint(sorted(catalog)) == config["cohort"]["catalog_sha256"],
        "Metadata sampling frame changed after protocol definition",
    )
    return rank_candidates(catalog, config["cohort"]["count"], config["cohort"]["seed"])


def _authorize(
    config,
    freeze,
    release,
    catalog,
    series,
    phase,
    origin,
    budget,
    capability,
    selection,
    calibration,
    evidence=None,
):
    cohort = select_cohort(config, catalog)
    require(series in cohort, "Series outside fixed metadata cohort; no replacement")
    task = authorize_task(
        config,
        freeze,
        release,
        phase=phase,
        origin=origin,
        budget=budget,
        capability=capability,
        cohort_sha256=fingerprint(list(cohort)),
        selection=selection,
        calibration=calibration,
        evidence=evidence,
        cohort=cohort,
    )
    return task, cohort


def validate_task_ledger(config, phase, origin, budget, view, record):
    """Strict per-item access; all reserved outcomes forbidden in every category.

    Shared study development is disclosed separately by the protocol and locks.
    Cross-series weights/data are deliberately unsupported, not implicitly free.
    """
    task = task_for(config, phase, origin, budget)
    require(type(view) is LearnerView, "Only learner views may validate fitting access")
    require(
        (view.history.dataset, view.history.origin, len(view.history.observations))
        == (config["dataset_version"], origin, budget),
        "Learner task identity mismatch",
    )
    require(
        record["track"] == "per_series" and not record["pretrained_artifacts"],
        "Pooling/pretraining require a separately supported and approved lineage track",
    )
    history = Window(**task["history"])
    require(
        view.normalization == fit_normalization(view.history, history),
        "View normalization must equal its training-only fit",
    )
    require(
        view.features == _calendar_features(config, history, origin),
        "View features must equal the complete deterministic calendar allowance",
    )
    forbidden = tuple(
        Window(**t["evaluation"])
        for t in plan_protocol(config)["tasks"]
        if t["phase"] != "development"
    )
    policy = SourcePolicy(
        config["dataset_version"], config["first_date"], (history,), forbidden
    )
    counts = validate_ledger(record, (policy,), view.history)
    require(
        set(record["features"]) == set(config["features"]), "Feature allowance mismatch"
    )
    require(
        not record["access"]["calibration"] and not record["access"]["validation"],
        "Outcome access is scorer-only, never part of learner fitting",
    )
    return counts


def _calendar_features(config, window, origin):
    first = date.fromisoformat(config["first_date"])
    return tuple(
        Feature(
            name,
            day,
            0,
            (first + timedelta(days=day - 1)).month
            if name == "month"
            else (first + timedelta(days=day - 1)).weekday(),
            "deterministic civil calendar",
        )
        for day in range(window.start, origin + config["horizon"])
        for name in config["features"]
    )


def prepare_learner(
    config,
    freeze,
    release,
    *,
    catalog,
    series,
    phase,
    origin,
    budget,
    source,
    selection=None,
    calibration=None,
    evidence=None,
):
    """Return (learner view, trusted access receipt), reading only one n-history.

    source.read_history is called only after all release checks. Source hashes
    are checked on its trusted manifest, never copied into the learner view.
    """
    task, cohort = _authorize(
        config,
        freeze,
        release,
        catalog,
        series,
        phase,
        origin,
        budget,
        "learner_history",
        selection,
        calibration,
        evidence,
    )
    require(
        source.manifest_sha256 == freeze["source_manifest_sha256"],
        "Reader source manifest differs from scientific freeze",
    )
    source.verify_freeze(config, freeze)
    window = Window(**task["history"])
    authorization = dict(
        config=config,
        freeze=freeze,
        release=release,
        catalog=catalog,
        phase=phase,
        origin=origin,
        budget=budget,
        selection=selection,
        calibration=calibration,
        evidence=evidence,
    )
    observations = source.read_history(series, window, authorization=authorization)
    require(
        type(observations) is tuple
        and all(type(o) is Observation for o in observations),
        "History reader must return an immutable observation tuple, never targets",
    )
    history = History(config["dataset_version"], series, origin, observations)
    require(history.window == window, "Reader returned an unauthorized history window")
    features = _calendar_features(config, window, origin)
    view = LearnerView(history, fit_normalization(history, window), features)
    info = ledger(history, "staged_preparation_only", tuple(config["features"]))
    for purpose in ("normalization", "demand_model_fitting"):
        info["access"][purpose] = [access(history)]
    counts = validate_task_ledger(config, phase, origin, budget, view, info)
    return view, {
        "protocol_sha256": fingerprint(config),
        "release_sha256": fingerprint(release),
        "cohort_sha256": fingerprint(list(cohort)),
        "ledger": info,
        "validated_counts": counts,
        "information_track": config["information_track"],
        "access_receipt_sha256": access_receipt(
            config, freeze, release, series, window, evidence
        )
        if evidence is not None
        else None,
    }


def prepare_evaluation(
    config,
    freeze,
    release,
    *,
    catalog,
    series,
    phase,
    origin,
    source,
    selection=None,
    calibration=None,
    evidence=None,
):
    """Trusted scorer only. Independent outcome release, no learner reference."""
    task, cohort = _authorize(
        config,
        freeze,
        release,
        catalog,
        series,
        phase,
        origin,
        None,
        "evaluation_outcomes",
        selection,
        calibration,
        evidence,
    )
    require(
        source.manifest_sha256 == freeze["source_manifest_sha256"],
        "Reader source manifest differs from scientific freeze",
    )
    source.verify_freeze(config, freeze)
    window = Window(**task["evaluation"])
    authorization = dict(
        config=config,
        freeze=freeze,
        release=release,
        catalog=catalog,
        phase=phase,
        origin=origin,
        budget=None,
        selection=selection,
        calibration=calibration,
        evidence=evidence,
    )
    observations = source.read_evaluation(series, window, authorization=authorization)
    require(
        type(observations) is tuple
        and all(type(o) is Observation for o in observations),
        "Scorer reader must return an immutable observation tuple",
    )
    target = EvaluationTargets(config["dataset_version"], series, window, observations)
    first = date.fromisoformat(config["first_date"])
    require(
        all(
            o.date == (first + timedelta(days=o.day - 1)).isoformat()
            for o in observations
        ),
        "Evaluator dates inconsistent with source metadata",
    )
    return target, {
        "protocol_sha256": fingerprint(config),
        "release_sha256": fingerprint(release),
        "cohort_sha256": fingerprint(list(cohort)),
        "source_manifest_sha256": source.manifest_sha256,
        "phase": phase,
        "series": series,
        "window": asdict(window),
        "selection_sha256": release["selection_sha256"],
        "calibration_sha256": release["calibration_sha256"],
        "access_receipt_sha256": access_receipt(
            config, freeze, release, series, window, evidence
        )
        if evidence is not None
        else None,
    }


def learner_payload(view):
    """Existing M3 learner-file schema; release/protocol metadata stays trusted."""
    require(type(view) is LearnerView, "Cannot serialize evaluator as learner")
    return {
        "history": asdict(view.history),
        "normalization": asdict(view.normalization),
        "features": [asdict(f) for f in view.features],
    }
