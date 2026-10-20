"""M4d-0 synthetic-only, least-privilege reference execution prototype.

NOT a real-data executor, not GP/RL training, not an authorization to release
M5 outcomes. A separately approved, reviewed M4d-1 implementation is required
before any real observations may pass through an executor.

The learner stage consumes ONLY a pinned learner artifact and plan. The scorer
receives EvaluationTargets through a separate, already-released scorer path.
All saved values are LOCAL PRIVATE experimental artifacts (never commit).
"""

from __future__ import annotations

import hashlib
import math
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

from inventory_ejor.data.budgets import access, ledger
from inventory_ejor.data.contracts import EvaluationTargets, Window, exact_keys
from inventory_ejor.data.evidence import RECEIPT_KEYS, EvidenceStore
from inventory_ejor.data.m4d0_store import PrivateExecutionStore
from inventory_ejor.data.protocol import M5_VERSION, require, sha256_id
from inventory_ejor.data.provenance import canonical, fingerprint, read_json
from inventory_ejor.data.releases import authorize_task
from inventory_ejor.data.staged import (
    learner_payload,
    select_cohort,
    validate_task_ledger,
)
from inventory_ejor.data.views import LearnerView, load_learner
from inventory_ejor.envs import (
    CostParameters,
    InventoryConfig,
    InventoryState,
    transition,
    validate_state,
)

METHOD = "synthetic_empirical_base_stock_reference"


def source_hashes():
    """Pin the complete local inventory_ejor Python source snapshot, not binaries."""
    checkout = Path(__file__).resolve().parents[3]
    hashes = {}
    for path in sorted((checkout / "src/inventory_ejor").rglob("*.py")):
        relative = str(path.relative_to(checkout))
        require(
            path.is_file() and path == path.resolve(),
            "Missing or symlinked execution dependency",
        )
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def scenario_contract(scenario):
    require(type(scenario) is dict, "Explicit scenario required")
    exact_keys(
        scenario,
        (
            "lead_time",
            "horizon",
            "max_order",
            "initial_on_hand",
            "initial_pipeline",
            "costs",
            "additional_terminal_value",
        ),
        "M4d0 scenario",
    )
    require(
        type(scenario["initial_pipeline"]) is list,
        "Initial pipeline must be a JSON list",
    )
    require(
        scenario["additional_terminal_value"] == 0
        and type(scenario["additional_terminal_value"]) is int,
        "Prototype supports zero salvage only",
    )
    require(type(scenario["costs"]) is dict, "Exact cost specification required")
    exact_keys(
        scenario["costs"],
        ("holding", "lost_sales", "variable_order", "fixed_order"),
        "cost coefficients",
    )
    config = InventoryConfig(
        lead_time=scenario["lead_time"],
        horizon=scenario["horizon"],
        max_order=scenario["max_order"],
        costs=CostParameters(**scenario["costs"]),
    )
    require(
        config.horizon <= 128 and config.lead_time <= 10 and config.max_order <= 100,
        "M4d0 CPU reference scenario exceeds bounded scope",
    )
    state = InventoryState(
        scenario["initial_on_hand"], tuple(scenario["initial_pipeline"])
    )
    validate_state(config, state)
    return config, state


def exact_reference_target(total_sales, budget, lead_time, max_order):
    """Exact integer ceiling; Python integers avoid roundoff before the cap."""
    for name, value, low, high in (
        ("total", total_sales, 0, 3660 * 2**53),
        ("budget", budget, 1, 3660),
        ("lead", lead_time, 1, 10),
        ("max_order", max_order, 0, 100),
    ):
        require(
            type(value) is int and low <= value <= high,
            f"Invalid bounded integer reference {name}",
        )
    require(total_sales <= budget * 2**53, "Historical count bound exceeded")
    return min(
        max_order * (lead_time + 1),
        (total_sales * (lead_time + 1) + budget - 1) // budget,
    )


def runtime_versions():
    return {
        "python": sys.version,
        "numpy": version("numpy"),
        "gymnasium": version("gymnasium"),
    }


def _reference_target(view, inventory, budget):
    require(
        type(view) is LearnerView and len(view.history.observations) == budget,
        "Reference fitting requires exactly n learner observations",
    )
    require(
        all(
            type(o.sales) is int and 0 <= o.sales <= 2**53
            for o in view.history.observations
        ),
        "Historical count bound exceeded",
    )
    return exact_reference_target(
        sum(o.sales for o in view.history.observations),
        budget,
        inventory.lead_time,
        inventory.max_order,
    )


def _task(config, catalog, phase, origin, budget, series, release, freeze, evidence):
    require(
        config["dataset_version"].startswith("synthetic-")
        and config["dataset_version"] != M5_VERSION,
        "M4d0 intentionally refuses real M5 and non-synthetic data",
    )
    require(phase == "development", "M4d0 supports synthetic development only")
    require(type(evidence) is EvidenceStore, "Persisted evidence required")
    cohort = select_cohort(config, catalog)
    require(series in cohort, "Out-of-cohort series forbidden")
    task = authorize_task(
        config,
        freeze,
        release,
        phase=phase,
        origin=origin,
        budget=budget,
        capability="learner_history",
        cohort_sha256=fingerprint(list(cohort)),
        cohort=cohort,
        evidence=evidence,
    )
    return task, cohort


def _receipt(
    evidence,
    digest,
    release,
    *,
    config,
    freeze,
    cohort,
    series,
    phase,
    origin,
    budget,
    capability,
    window,
):
    require(isinstance(digest, str), "Persisted receipt identity required")
    value = evidence.read(digest)
    exact_keys(value, RECEIPT_KEYS, "staged access receipt")
    require(
        type(value["schema_version"]) is int and value["schema_version"] == 1,
        "Unsupported receipt version",
    )
    require(
        type(value["origin"]) is int
        and (value["budget"] is None or type(value["budget"]) is int),
        "Receipt task requires integer types",
    )
    exact_keys(value["window"], ("start", "stop"), "receipt window")
    Window(**value["window"])
    require(
        value["kind"] == "staged_access_receipt"
        and value["protocol_sha256"] == fingerprint(config)
        and value["freeze_sha256"] == fingerprint(freeze)
        and value["release_sha256"] == fingerprint(release)
        and value["source_manifest_sha256"] == freeze["source_manifest_sha256"]
        and value["cohort_sha256"] == fingerprint(list(cohort))
        and (
            value["series"],
            value["phase"],
            value["origin"],
            value["budget"],
            value["capability"],
        )
        == (series, phase, origin, budget, capability)
        and value["window"] == asdict(window)
        and value["selection_sha256"] == release["selection_sha256"]
        and value["calibration_sha256"] == release["calibration_sha256"],
        "Receipt is not bound to the exact released data access",
    )
    require(
        evidence.read(value["release_sha256"]) == release,
        "Persisted release identity differs from input",
    )


def publish_learner_only_plan(
    private_store,
    evidence,
    *,
    config,
    freeze,
    release,
    catalog,
    view,
    receipt,
    phase,
    series,
    origin,
    budget,
    scenario,
    seed,
):
    """Trusted preparer -> bounded private input; no evaluator object accepted."""
    require(
        type(private_store) is PrivateExecutionStore,
        "Private M4d0 artifact store required",
    )
    require(
        type(view) is LearnerView and type(receipt) is dict,
        "Only verified learner view and receipt accepted",
    )
    require(
        type(seed) is int and 0 <= seed <= 2**31 - 1,
        "Execution seed must be a bounded nonnegative integer",
    )
    require(seed <= 2**31 - 1, "Seed exceeds bounded reference scope")
    task, cohort = _task(
        config, catalog, phase, origin, budget, series, release, freeze, evidence
    )
    require(
        view.history.dataset == config["dataset_version"]
        and view.history.series == series
        and view.history.origin == origin
        and view.history.window == Window(**task["history"]),
        "Learner view does not match approved task",
    )
    require(
        receipt["protocol_sha256"] == fingerprint(config)
        and receipt["release_sha256"] == fingerprint(release)
        and receipt["cohort_sha256"] == fingerprint(list(cohort))
        and receipt["information_track"] == config["information_track"],
        "Learner receipt identity mismatch",
    )
    _receipt(
        evidence,
        receipt["access_receipt_sha256"],
        release,
        config=config,
        freeze=freeze,
        cohort=cohort,
        series=series,
        phase=phase,
        origin=origin,
        budget=budget,
        capability="learner_history",
        window=Window(**task["history"]),
    )
    require(
        read_json(canonical(receipt["validated_counts"]))
        == read_json(
            canonical(
                validate_task_ledger(
                    config, phase, origin, budget, view, receipt["ledger"]
                )
            )
        ),
        "Learner information ledger validation differs from saved receipt",
    )
    inv, state = scenario_contract(scenario)
    require(
        inv.horizon == config["horizon"],
        "Execution horizon differs from approved protocol",
    )
    # Exactly the existing M3 learner-only schema, with no evaluator keys.
    learner_digest = private_store.put(learner_payload(view))
    plan = {
        "schema_version": 1,
        "kind": "synthetic_reference_execution_plan",
        "dataset": config["dataset_version"],
        "series": series,
        "phase": phase,
        "origin": origin,
        "budget": budget,
        "seed": seed,
        "method": METHOD,
        "protocol_sha256": fingerprint(config),
        "freeze_sha256": fingerprint(freeze),
        "history_release_sha256": fingerprint(release),
        "history_receipt_sha256": receipt["access_receipt_sha256"],
        "learner_sha256": learner_digest,
        "information_track": config["information_track"],
        "scenario": scenario,
        "scenario_sha256": fingerprint(scenario),
        "dependency_sha256s": source_hashes(),
        "python": sys.version.split()[0],
        "runtime": runtime_versions(),
        "initial_stock": state.on_hand,
    }
    require(
        not any("evaluation" in key or "target" in key or "raw" in key for key in plan),
        "Learner plan must not embed evaluation handles",
    )
    return private_store.put(plan)


def execution_approval_template(plan_digest):
    return {
        "schema_version": 1,
        "kind": "synthetic_reference_run_approval",
        "approved": False,
        "plan_sha256": plan_digest,
        "approved_by_owner": "",
        "decision_record": "",
    }


def _verify_execution_approval(approval, plan_digest):
    exact_keys(
        approval,
        (
            "schema_version",
            "kind",
            "approved",
            "plan_sha256",
            "approved_by_owner",
            "decision_record",
        ),
        "reference execution approval",
    )

    require(
        type(approval["schema_version"]) is int
        and approval["schema_version"] == 1
        and approval["kind"] == "synthetic_reference_run_approval"
        and approval["approved"] is True
        and approval["plan_sha256"] == plan_digest
        and isinstance(approval["approved_by_owner"], str)
        and approval["approved_by_owner"].strip()
        and isinstance(approval["decision_record"], str)
        and approval["decision_record"].strip(),
        "Separate explicit execution approval required",
    )


PLAN_FIELDS = (
    "dataset series phase origin budget seed method protocol_sha256 freeze_sha256 "
    "history_release_sha256 history_receipt_sha256 learner_sha256 information_track "
    "scenario scenario_sha256 dependency_sha256s python runtime initial_stock"
).split()
FIT_FIELDS = (
    "plan_sha256 execution_approval_sha256 learner_sha256 dependency_sha256s "
    "scenario_sha256 seed method status base_stock_target sum_training_sales "
    "real_history_observations optimizer_steps simulated_transitions "
    "trained_gp trained_rl"
).split()
SCORE_FIELDS = (
    "plan_sha256 fit_sha256 execution_approval_sha256 evaluation_release_sha256 "
    "evaluation_receipt_sha256 trace_sha256 scenario_sha256 source_code_sha256s "
    "cost_components total_cost fulfilled requests fill_rate ending_stock "
    "ending_pipeline "
    "simulation_periods trained_gp trained_rl status"
).split()
TRACE_ROW_FIELDS = (
    "period day on_hand pipeline order observed_sales_as_requests "
    "fulfilled lost_units cost"
).split()


def _schema(value, kind, fields):
    exact_keys(value, ("schema_version", "kind", *fields), kind)
    require(
        type(value["schema_version"]) is int
        and value["schema_version"] == 1
        and value["kind"] == kind,
        "Unsupported execution artifact schema",
    )


def _bounded_int(value, label, maximum, minimum=0):
    require(
        type(value) is int and minimum <= value <= maximum,
        f"Invalid bounded integer {label}",
    )


def validated_plan(store, digest):
    """Same consumed-plan contract at execution, scoring and audit boundaries."""
    require(
        type(store) is PrivateExecutionStore, "Private M4d0 artifact store required"
    )
    plan = store.read(digest, kind="synthetic_reference_execution_plan")
    _schema(plan, "synthetic_reference_execution_plan", PLAN_FIELDS)
    require(
        plan["dependency_sha256s"] == source_hashes()
        and plan["python"] == sys.version.split()[0]
        and plan["runtime"] == runtime_versions(),
        "Execution code/runtime differs from pinned plan",
    )
    require(
        type(plan["dataset"]) is str
        and plan["dataset"].startswith("synthetic-")
        and type(plan["series"]) is str
        and bool(plan["series"])
        and plan["method"] == METHOD
        and plan["phase"] == "development"
        and plan["information_track"] == "per_series_with_shared_development",
        "Unsupported or altered prototype plan",
    )
    _bounded_int(plan["seed"], "seed", 2**31 - 1)
    _bounded_int(plan["origin"], "origin", 100000, 1)
    _bounded_int(plan["budget"], "history budget", 3660, 1)
    for field in (
        "protocol_sha256",
        "freeze_sha256",
        "history_release_sha256",
        "history_receipt_sha256",
        "learner_sha256",
        "scenario_sha256",
    ):
        sha256_id(plan[field], field)
    inv, state = scenario_contract(plan["scenario"])
    require(
        plan["scenario_sha256"] == fingerprint(plan["scenario"])
        and type(plan["initial_stock"]) is int
        and plan["initial_stock"] == state.on_hand,
        "Plan scenario identity mismatch",
    )
    view = load_learner(
        store.file(plan["learner_sha256"]),
        sha256=plan["learner_sha256"],
        dataset=plan["dataset"],
        series=plan["series"],
        origin=plan["origin"],
        budget=plan["budget"],
    )
    _reference_target(view, inv, plan["budget"])
    return plan, inv, state, view


def validated_fit(store, plan_digest, fit_digest, plan, inv, view, approval=None):
    fit = store.read(fit_digest, kind="synthetic_reference_fit_result")
    _schema(fit, "synthetic_reference_fit_result", FIT_FIELDS)
    saved = store.read(
        fit["execution_approval_sha256"], kind="synthetic_reference_run_approval"
    )
    _verify_execution_approval(saved, plan_digest)
    require(approval is None or saved == approval, "Pinned execution approval differs")
    for field in (
        "seed",
        "base_stock_target",
        "sum_training_sales",
        "real_history_observations",
        "optimizer_steps",
        "simulated_transitions",
    ):
        _bounded_int(fit[field], field, 3660 * 2**53)
    require(
        fit["plan_sha256"] == plan_digest
        and fit["learner_sha256"] == plan["learner_sha256"]
        and fit["scenario_sha256"] == plan["scenario_sha256"]
        and fit["dependency_sha256s"] == plan["dependency_sha256s"] == source_hashes()
        and fit["method"] == plan["method"] == METHOD
        and fit["seed"] == plan["seed"]
        and fit["status"] == "completed_synthetic_cpu_reference",
        "Scorer/auditor cannot accept an unbound or modified fit",
    )
    require(
        fit["base_stock_target"] == _reference_target(view, inv, plan["budget"])
        and fit["sum_training_sales"] == sum(o.sales for o in view.history.observations)
        and fit["real_history_observations"] == plan["budget"]
        and fit["optimizer_steps"] == fit["simulated_transitions"] == 0
        and fit["trained_gp"] is False
        and fit["trained_rl"] is False,
        "Scorer/auditor rejects fabricated reference policy/fit evidence",
    )
    return fit, saved


def validate_history_context(plan, view, evidence, config, freeze, catalog):
    require(
        type(evidence) is EvidenceStore, "Persisted authorization evidence required"
    )
    require(
        plan["dataset"] == config["dataset_version"]
        and plan["protocol_sha256"] == fingerprint(config)
        and plan["freeze_sha256"] == fingerprint(freeze),
        "Plan/context identity mismatch",
    )
    release = evidence.read(plan["history_release_sha256"])
    task, cohort = _task(
        config,
        catalog,
        plan["phase"],
        plan["origin"],
        plan["budget"],
        plan["series"],
        release,
        freeze,
        evidence,
    )
    _receipt(
        evidence,
        plan["history_receipt_sha256"],
        release,
        config=config,
        freeze=freeze,
        cohort=cohort,
        series=plan["series"],
        phase=plan["phase"],
        origin=plan["origin"],
        budget=plan["budget"],
        capability="learner_history",
        window=Window(**task["history"]),
    )
    info = ledger(view.history, METHOD, tuple(config["features"]))
    for purpose in ("normalization", "demand_model_fitting"):
        info["access"][purpose] = [access(view.history)]
    validate_task_ledger(
        config, plan["phase"], plan["origin"], plan["budget"], view, info
    )
    return task, cohort


def validate_outcome_context(
    plan, evidence, config, freeze, catalog, release, receipt_digest, targets
):
    require(
        type(targets) is EvaluationTargets, "Scorer-only EvaluationTargets required"
    )
    cohort = select_cohort(config, catalog)
    require(plan["series"] in cohort, "Scorer cohort mismatch")
    task = authorize_task(
        config,
        freeze,
        release,
        phase=plan["phase"],
        origin=plan["origin"],
        budget=None,
        capability="evaluation_outcomes",
        cohort_sha256=fingerprint(list(cohort)),
        cohort=cohort,
        evidence=evidence,
    )
    _score_receipt(
        evidence,
        receipt_digest,
        config=config,
        freeze=freeze,
        release=release,
        cohort=cohort,
        series=plan["series"],
        phase=plan["phase"],
        origin=plan["origin"],
        task=task,
    )
    require(
        (targets.dataset, targets.series) == (plan["dataset"], plan["series"])
        and targets.window == Window(**task["evaluation"]),
        "Scorer targets do not match separately released task",
    )
    from datetime import date, timedelta

    first = date.fromisoformat(config["first_date"])
    require(
        all(
            o.date == (first + timedelta(days=o.day - 1)).isoformat()
            and 0 <= o.sales <= 2**53
            for o in targets.observations
        ),
        "Evaluator dates/counts differ from bounded source contract",
    )
    return task


def validate_score_record(score, plan_digest, fit_digest, plan, inv, approval):
    _schema(score, "synthetic_reference_score_evidence", SCORE_FIELDS)
    for field in (
        "evaluation_release_sha256",
        "evaluation_receipt_sha256",
        "trace_sha256",
    ):
        sha256_id(score[field], field)
    require(
        score["plan_sha256"] == plan_digest
        and score["fit_sha256"] == fit_digest
        and score["execution_approval_sha256"] == fingerprint(approval)
        and score["scenario_sha256"] == plan["scenario_sha256"]
        and score["source_code_sha256s"]
        == plan["dependency_sha256s"]
        == source_hashes()
        and score["trained_gp"] is False
        and score["trained_rl"] is False
        and score["status"] == "synthetic_only_not_retail_evidence",
        "Score execution identities/status differ",
    )
    for field in ("fulfilled", "requests", "ending_stock", "simulation_periods"):
        _bounded_int(score[field], field, inv.horizon * 2**53)
    require(
        score["simulation_periods"] == inv.horizon
        and score["fulfilled"] <= score["requests"]
        and type(score["ending_pipeline"]) is list
        and len(score["ending_pipeline"]) == inv.lead_time,
        "Invalid score counts/terminal shape",
    )
    for count in score["ending_pipeline"]:
        _bounded_int(count, "terminal batch", 2**53)
    exact_keys(
        score["cost_components"],
        ("holding", "lost_sales", "variable_order", "fixed_order"),
        "score costs",
    )
    for value in (*score["cost_components"].values(), score["total_cost"]):
        require(
            type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "Invalid finite nonnegative score cost",
        )
    require(
        score["fill_rate"] is None
        if score["requests"] == 0
        else type(score["fill_rate"]) in (int, float) and 0 <= score["fill_rate"] <= 1,
        "Invalid score fill rate",
    )


def execute_synthetic_reference(private_store, plan_digest, approval):
    """Learner-only CPU execution. No scorer/targets/raw-reader parameters."""
    _verify_execution_approval(approval, plan_digest)
    plan, scenario, _, view = validated_plan(private_store, plan_digest)
    private_store.put(approval)
    threshold = _reference_target(view, scenario, plan["budget"])
    result = {
        "schema_version": 1,
        "kind": "synthetic_reference_fit_result",
        "plan_sha256": plan_digest,
        "execution_approval_sha256": fingerprint(approval),
        "learner_sha256": plan["learner_sha256"],
        "dependency_sha256s": plan["dependency_sha256s"],
        "scenario_sha256": plan["scenario_sha256"],
        "seed": plan["seed"],
        "method": METHOD,
        "status": "completed_synthetic_cpu_reference",
        "base_stock_target": threshold,
        "sum_training_sales": sum(o.sales for o in view.history.observations),
        "real_history_observations": plan["budget"],
        "optimizer_steps": 0,
        "simulated_transitions": 0,
        "trained_gp": False,
        "trained_rl": False,
    }
    return private_store.put(result)


def _score_receipt(
    evidence, digest, *, config, freeze, release, cohort, series, phase, origin, task
):
    _receipt(
        evidence,
        digest,
        release,
        config=config,
        freeze=freeze,
        cohort=cohort,
        series=series,
        phase=phase,
        origin=origin,
        budget=None,
        capability="evaluation_outcomes",
        window=Window(**task["evaluation"]),
    )


def score_synthetic_reference(
    private_store,
    evidence,
    *,
    plan_digest,
    fit_digest,
    approval,
    config,
    freeze,
    evaluation_release,
    catalog,
    targets,
    scorer_receipt,
):
    """Separate trusted scorer. Requires an independently released target."""
    require(
        type(targets) is EvaluationTargets and type(scorer_receipt) is dict,
        "Scorer-only EvaluationTargets and receipt required",
    )
    _verify_execution_approval(approval, plan_digest)
    plan, inv, state, pinned_view = validated_plan(private_store, plan_digest)
    fit, _ = validated_fit(
        private_store, plan_digest, fit_digest, plan, inv, pinned_view, approval
    )
    _, cohort = validate_history_context(
        plan, pinned_view, evidence, config, freeze, catalog
    )
    validate_outcome_context(
        plan,
        evidence,
        config,
        freeze,
        catalog,
        evaluation_release,
        scorer_receipt["access_receipt_sha256"],
        targets,
    )
    require(
        scorer_receipt["protocol_sha256"] == fingerprint(config)
        and scorer_receipt["release_sha256"] == fingerprint(evaluation_release)
        and scorer_receipt["cohort_sha256"] == fingerprint(list(cohort)),
        "Scorer receipt metadata differs from evaluation release",
    )
    require(inv.horizon == len(targets.observations), "Evaluation horizon mismatch")
    limit = fit["base_stock_target"]
    require(
        type(limit) is int and 0 <= limit <= inv.max_order * (inv.lead_time + 1),
        "Invalid learned controller parameter",
    )
    components = {
        "holding": 0.0,
        "lost_sales": 0.0,
        "variable_order": 0.0,
        "fixed_order": 0.0,
    }
    trace = []
    served = requests = 0
    for period, obs in enumerate(targets.observations):
        # Decide from stock and pipeline BEFORE revealing current demand.
        position = state.on_hand + sum(state.pipeline)
        q = max(0, min(inv.max_order, limit - position))
        if period + inv.lead_time >= inv.horizon:
            q = 0
        outcome = transition(inv, state, q, obs.sales)
        trace.append(
            {
                "period": period,
                "day": obs.day,
                "on_hand": state.on_hand,
                "pipeline": list(state.pipeline),
                "order": q,
                "observed_sales_as_requests": obs.sales,
                "fulfilled": outcome.sales,
                "lost_units": outcome.lost_units,
                "cost": outcome.costs.total,
            }
        )
        for name in components:
            components[name] += getattr(outcome.costs, name)
        served += outcome.sales
        requests += obs.sales
        state = outcome.next_state
    private_trace = private_store.put(
        {
            "schema_version": 1,
            "kind": "synthetic_private_scoring_trace",
            "plan_sha256": plan_digest,
            "fit_sha256": fit_digest,
            "periods": trace,
        }
    )
    record = {
        "schema_version": 1,
        "kind": "synthetic_reference_score_evidence",
        "plan_sha256": plan_digest,
        "fit_sha256": fit_digest,
        "execution_approval_sha256": fingerprint(approval),
        "evaluation_release_sha256": fingerprint(evaluation_release),
        "evaluation_receipt_sha256": scorer_receipt["access_receipt_sha256"],
        "trace_sha256": private_trace,
        "scenario_sha256": plan["scenario_sha256"],
        "source_code_sha256s": source_hashes(),
        "cost_components": components,
        "total_cost": math.fsum(components.values()),
        "fulfilled": served,
        "requests": requests,
        "fill_rate": (served / requests if requests else None),
        "ending_stock": outcome.ending_on_hand,
        "ending_pipeline": list(outcome.outstanding_after_order),
        "simulation_periods": len(trace),
        "trained_gp": False,
        "trained_rl": False,
        "status": "synthetic_only_not_retail_evidence",
    }
    validate_score_record(record, plan_digest, fit_digest, plan, inv, approval)
    # No score is returned until both local trace and score evidence are durable.
    return private_store.put(record)
