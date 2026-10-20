"""M3 bounded preparation: learner histories and evaluator outcomes stay separate."""

from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from .budgets import (
    SourcePolicy,
    access,
    assert_same_evaluation,
    ledger,
    study_information,
    validate_ledger,
)
from .contracts import (
    BUDGETS,
    EvaluationTargets,
    History,
    Phase,
    SplitPlan,
    Window,
    exact_keys,
    features_at,
    fit_normalization,
    integer,
)
from .m5 import (
    ReadLimits,
    calendar_features,
    check_overlap,
    eligible,
    load_calendar,
    load_catalog,
    load_observations,
    rank_candidates,
)
from .protocol import guard_legacy_development, recognized_m5_source
from .provenance import fingerprint, read_json, verify_inputs


def parse_config(raw: bytes):
    cfg = read_json(raw)
    exact_keys(
        cfg,
        (
            "schema_version",
            "dataset_version",
            "mode",
            "seed",
            "candidate_count",
            "min_nonzero",
            "origins",
            "horizon",
            "development_window",
            "budgets",
            "calendar_features",
            "limits",
        ),
        "M3 config",
    )
    if type(cfg["schema_version"]) is not int or cfg["schema_version"] != 1:
        raise ValueError("unsupported configuration version")
    if not isinstance(cfg["dataset_version"], str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_.:/-]{0,127}", cfg["dataset_version"]
    ):
        raise ValueError("dataset_version must be a predeclared logical version label")
    if cfg["mode"] != "development_demo":
        raise ValueError(
            "only development_demo is authorized; final holdout is not frozen"
        )
    for name in ("seed", "min_nonzero"):
        integer(cfg[name], name, 0)
    integer(cfg["candidate_count"], "candidate_count")
    if cfg["budgets"] != list(BUDGETS) or any(
        type(n) is not int for n in cfg["budgets"]
    ):
        raise ValueError("M3 demonstration requires exact 28/56/112/224 budget grid")
    if type(cfg["calendar_features"]) is not bool:
        raise ValueError("calendar_features must be Boolean")
    exact_keys(cfg["development_window"], ("start", "stop"), "development window")
    plan = SplitPlan(
        (Phase("development", Window(**cfg["development_window"])),), cfg["horizon"]
    )
    if not isinstance(cfg["origins"], list):
        raise ValueError("origins must be a list")
    plan.validate_origins("development", tuple(cfg["origins"]))
    if len(cfg["origins"]) > 4:
        raise ValueError("M3 demo limited to four origins")
    if cfg["min_nonzero"] > min(BUDGETS):
        raise ValueError("eligibility can use only the shortest history")
    exact_keys(
        cfg["limits"],
        ("max_seconds", "max_rows", "max_series", "max_days", "max_selected"),
        "limits",
    )
    limits = ReadLimits(**cfg["limits"])
    if (
        limits.max_series > 40_000
        or limits.max_days > 3000
        or limits.max_selected > 32
        or limits.max_rows > 7_000_000
        or cfg["candidate_count"] > limits.max_selected
    ):
        raise ValueError("M3 demonstration memory/work bounds exceeded")
    guard_legacy_development(cfg)
    return cfg, plan, limits


def prepare(raw_dir: Path, input_manifest, raw_config: bytes):
    cfg, plan, limits = parse_config(raw_config)
    # Legacy demos cannot relabel reserved real-M5 outcomes as development.
    # Check metadata before hashing or opening any raw source.
    guard_legacy_development(
        cfg, real_source=recognized_m5_source(raw_dir, input_manifest)
    )
    before = verify_inputs(raw_dir, input_manifest, limits)
    # A full-source hash includes withheld outcomes. It must never enter a
    # learner artifact, task filename or predictor, even as an opaque identifier.
    source_fingerprint = "m5-sha256:" + fingerprint(before)
    dataset = cfg["dataset_version"]
    calendar = load_calendar(raw_dir / "calendar.csv", limits)
    catalog, max_day = load_catalog(raw_dir / "sales_train_evaluation.csv", limits)
    if max_day not in calendar:
        raise ValueError("sales/calendar extent mismatch")
    candidates = rank_candidates(catalog, cfg["candidate_count"], cfg["seed"])
    first = cfg["origins"][0]
    screening = Window(first - min(BUDGETS), first)
    screening_data = load_observations(
        raw_dir / "sales_train_evaluation.csv", candidates, screening, calendar, limits
    )
    included, exclusions = [], []
    for key in candidates:
        if eligible(screening_data[key], screening, cfg["min_nonzero"]):
            included.append(key)
        else:
            exclusions.append(
                {"series": key, "reason": "too_few_positive_sales_in_common_history"}
            )
    # No outcome-driven replacement search after candidate IDs are fixed.
    if not included:
        raise ValueError(
            "no eligible candidates; do not search seeds based on outcomes"
        )
    selected = tuple(included)
    unselected = sorted(set(catalog) - set(candidates))
    policies = (SourcePolicy(dataset, calendar[1]["date"], (plan.phases[0].window,)),)
    training, evaluator, ledgers, splits, overlap = {}, {}, [], [], []
    selected_history_windows = []
    for origin in cfg["origins"]:
        full, target_window = plan.windows("development", origin, max(BUDGETS))
        histories = load_observations(
            raw_dir / "sales_train_evaluation.csv", selected, full, calendar, limits
        )
        selected_history_windows.extend((key, full) for key in selected)
        overlap.append(
            check_overlap(
                raw_dir / "sales_train_validation.csv",
                raw_dir / "sales_train_evaluation.csv",
                selected,
                full,
                calendar,
                limits,
            )
        )
        # A separate read and object type is reserved for the evaluator.
        targets = load_observations(
            raw_dir / "sales_train_evaluation.csv",
            selected,
            target_window,
            calendar,
            limits,
        )
        windows = []
        for key in selected:
            evaluation = EvaluationTargets(dataset, key, target_window, targets[key])
            evaluator[f"{key}@{origin}"] = asdict(evaluation)
            for n in BUDGETS:
                history_window, evaluation_window = plan.windows(
                    "development", origin, n
                )
                windows.append(evaluation_window)
                history = History(
                    dataset,
                    key,
                    origin,
                    tuple(o for o in histories[key] if o.day >= history_window.start),
                )
                normalized = fit_normalization(history, history_window)
                # Only deterministic calendar values, which are known before deployment.
                features = (
                    calendar_features(
                        history_window.days + target_window.days, calendar
                    )
                    if cfg["calendar_features"]
                    else ()
                )
                features_at(features, origin)
                token = f"{key}@{origin}/n{n}"
                training[token] = {
                    "history": asdict(history),
                    "normalization": asdict(normalized),
                    "features": [asdict(f) for f in features],
                }
                info = ledger(
                    history,
                    "m3_preparation_only",
                    tuple(sorted({f.name for f in features})),
                )
                info["access"]["normalization"] = [access(history)]
                # Screening is fixed at the FIRST origin, so later histories must not
                # hide its extra observations. Rolling cohorts are richer information.
                if not history_window.contains(screening):
                    info["track"] = "rich_data"
                info["access"]["eligibility"] = [
                    {
                        "dataset": dataset,
                        "series": key,
                        "start": screening.start,
                        "stop": screening.stop,
                    }
                ]
                counts = validate_ledger(info, policies, history)
                ledgers.append(
                    {"token": token, "ledger": info, "validated_counts": counts}
                )
                splits.append(
                    {
                        "token": token,
                        "history": asdict(history_window),
                        "evaluation": asdict(evaluation_window),
                        "history_dates": [
                            calendar[history_window.start]["date"],
                            calendar[origin - 1]["date"],
                        ],
                        "evaluation_dates": [
                            calendar[origin]["date"],
                            calendar[target_window.stop - 1]["date"],
                        ],
                    }
                )
        assert_same_evaluation(windows)
    after = verify_inputs(raw_dir, input_manifest, limits)
    if before != after:
        raise ValueError("raw inputs changed during preparation")
    cohort = {
        "candidates": list(candidates),
        "included": list(selected),
        "excluded": exclusions,
        "not_sampled": unselected,
        "not_sampled_reason": "outside fixed metadata-hash candidate set",
        "screening_window": asdict(screening),
        "screening_dates": [
            calendar[screening.start]["date"],
            calendar[screening.stop - 1]["date"],
        ],
        "screening_observations": len(candidates) * len(screening.days),
        "selection_seed": cfg["seed"],
        "min_nonzero": cfg["min_nonzero"],
        "replacement": False,
        "shared_design_information": (
            "cohort membership; candidate screening is disclosed separately, "
            "never pooled into fitting"
        ),
    }
    quality = {
        "catalog_series": len(catalog),
        "sales_days": max_day,
        "calendar_days": len(calendar),
        "candidates": len(candidates),
        "included": len(selected),
        "excluded": len(exclusions),
        "history_views": len(training),
        "outcome_views": len(evaluator),
        "raw_sha256_verified_before_after": True,
        "selected_cells": "nonnegative integers, complete dates; no clipping/filling",
        "scope": (
            "metadata catalog and selected authorized windows; "
            "no full-sales outcome audit"
        ),
        "interpretation": (
            "observed sales, potentially stockout-censored; no inferred demand/costs"
        ),
    }
    manifest = {
        "schema_version": 2,
        "status": "prepared_development_demo",
        "scientific_acceptance": "pending_owner_review; no final holdout frozen",
        "dataset": source_fingerprint,
        "learner_dataset_version": dataset,
        "study_information": study_information(
            dataset,
            source_fingerprint,
            selected_history_windows,
            candidates,
            screening,
            len(catalog),
        ),
        "inputs": before,
        "config": cfg,
        "config_fingerprint": fingerprint(cfg),
        "split_plan": asdict(plan),
        "splits": splits,
        "information_budgets": ledgers,
        "overlap_checks": overlap,
        "quality": quality,
        "transformations": [
            "metadata hash ranking",
            "shortest-history eligibility without replacement",
            "nested contiguous sales histories",
            "training-only population normalization",
            "separate evaluator outcomes",
        ],
        "prices_events_snap": "disabled: availability evidence required",
        "initial_inventory": (
            "not inferred; shared scenario state must be specified "
            "before inventory evaluation"
        ),
        "raw_data_unchanged": before == after,
    }
    return {
        "training.json": training,
        "evaluation.json": evaluator,
        "cohort.json": cohort,
    }, manifest
