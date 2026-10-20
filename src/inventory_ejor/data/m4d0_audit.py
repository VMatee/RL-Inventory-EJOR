"""Strict authorization audit and independent absolute-arrival numerical replay.

No production M1 transition is reused. Authorized metadata does not establish
honest scientific execution or the actual raw observation bytes returned by M4c.
"""

from __future__ import annotations

import math

from .contracts import EvaluationTargets, exact_keys
from .m4d0_execution import (
    TRACE_ROW_FIELDS,
    _bounded_int,
    _schema,
    exact_reference_target,
    validate_history_context,
    validate_outcome_context,
    validate_score_record,
    validated_fit,
    validated_plan,
)
from .m4d0_store import PrivateExecutionStore
from .protocol import require


def verify_synthetic_reference_trace(
    private_store: PrivateExecutionStore,
    plan_digest,
    fit_digest,
    score_digest,
    targets: EvaluationTargets,
    *,
    evidence,
    config,
    freeze,
    catalog,
):
    """Verify complete scoped reference evidence, not scientific selection.

    Authorization context is mandatory; no numerical-only fallback can return
    this success status. This function reads persisted records and writes none.
    """
    plan, scenario, initial, view = validated_plan(private_store, plan_digest)
    fit, approval = validated_fit(
        private_store, plan_digest, fit_digest, plan, scenario, view
    )
    validate_history_context(plan, view, evidence, config, freeze, catalog)
    score = private_store.read(score_digest, kind="synthetic_reference_score_evidence")
    validate_score_record(score, plan_digest, fit_digest, plan, scenario, approval)
    release = evidence.read(score["evaluation_release_sha256"])
    validate_outcome_context(
        plan,
        evidence,
        config,
        freeze,
        catalog,
        release,
        score["evaluation_receipt_sha256"],
        targets,
    )
    require(
        len(targets.observations) == scenario.horizon, "Evaluation horizon mismatch"
    )
    trace = private_store.read(
        score["trace_sha256"], kind="synthetic_private_scoring_trace"
    )
    _schema(
        trace,
        "synthetic_private_scoring_trace",
        ("plan_sha256", "fit_sha256", "periods"),
    )
    require(
        trace["plan_sha256"] == plan_digest and trace["fit_sha256"] == fit_digest,
        "Broken result-to-plan-to-trace provenance chain",
    )
    rows = trace["periods"]
    require(
        type(rows) is list and len(rows) == scenario.horizon,
        "Missing or extra saved scorer transitions",
    )
    proposed = exact_reference_target(
        sum(o.sales for o in view.history.observations),
        plan["budget"],
        scenario.lead_time,
        scenario.max_order,
    )
    arrivals = dict(enumerate(initial.pipeline, 1))
    stock = initial.on_hand
    costs = dict.fromkeys(
        ("holding", "lost_sales", "variable_order", "fixed_order"), 0.0
    )
    served = requests = 0
    for t, (recorded, observed) in enumerate(
        zip(rows, targets.observations, strict=True)
    ):
        exact_keys(recorded, TRACE_ROW_FIELDS, "trace row")
        stock += arrivals.pop(t, 0)
        _bounded_int(stock, "oracle stock", 2**53)
        pending = [arrivals.get(t + j, 0) for j in range(1, scenario.lead_time)]
        q = max(0, min(scenario.max_order, proposed - stock - sum(pending)))
        if t + scenario.lead_time >= scenario.horizon:
            q = 0
        for field in (
            "period",
            "day",
            "on_hand",
            "order",
            "observed_sales_as_requests",
            "fulfilled",
            "lost_units",
        ):
            _bounded_int(recorded[field], field, 2**53)
        require(
            type(recorded["pipeline"]) is list
            and len(recorded["pipeline"]) == scenario.lead_time - 1,
            "Invalid trace pipeline shape",
        )
        for count in recorded["pipeline"]:
            _bounded_int(count, "trace batch", 2**53)
        require(
            recorded["period"] == t
            and recorded["day"] == observed.day
            and recorded["observed_sales_as_requests"] == observed.sales
            and recorded["on_hand"] == stock
            and recorded["pipeline"] == pending
            and recorded["order"] == q,
            "Saved action, history or current-request path differs",
        )
        arrivals[t + scenario.lead_time] = q
        fulfilled = min(stock, observed.sales)
        lost = observed.sales - fulfilled
        stock -= fulfilled
        c = scenario.costs
        current = {
            "holding": c.holding * stock,
            "lost_sales": c.lost_sales * lost,
            "variable_order": c.variable_order * q,
            "fixed_order": c.fixed_order if q else 0.0,
        }
        require(
            type(recorded["cost"]) in (int, float)
            and math.isfinite(recorded["cost"])
            and recorded["fulfilled"] == fulfilled
            and recorded["lost_units"] == lost
            and math.isclose(
                recorded["cost"], sum(current.values()), rel_tol=1e-12, abs_tol=1e-9
            ),
            "Saved reference transition/cost differs",
        )
        _bounded_int(stock + arrivals.get(t + 1, 0), "next stock", 2**53)
        for name, value in current.items():
            costs[name] += value
        served += fulfilled
        requests += observed.sales
    outstanding = [
        arrivals.get(scenario.horizon + j, 0) for j in range(scenario.lead_time)
    ]
    total = math.fsum(costs.values())
    require(
        all(
            math.isclose(
                costs[k], score["cost_components"][k], rel_tol=1e-12, abs_tol=1e-9
            )
            for k in costs
        )
        and math.isclose(total, score["total_cost"], rel_tol=1e-12, abs_tol=1e-9)
        and score["fulfilled"] == served
        and score["requests"] == requests
        and score["ending_stock"] == stock
        and score["ending_pipeline"] == outstanding
        and score["fill_rate"] == (served / requests if requests else None),
        "Saved score totals, fill rate or terminal state differ",
    )
    return {
        "status": "independent_synthetic_replay_verified",
        "periods": len(rows),
        "total_cost": total,
        "training_observations": len(view.history.observations),
        "evaluation_requests": requests,
        "trained_gp": False,
        "trained_rl": False,
        "authorization_attestations_verified": True,
        "scientific_selection_execution_verified": False,
        "raw_observation_bytes_verified": False,
    }
