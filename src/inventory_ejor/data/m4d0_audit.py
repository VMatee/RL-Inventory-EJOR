"""Independent read-only verifier for a saved M4d-0 synthetic reference run.

Reconstruct training decision and every M1 transition from *pinned learner*
and *separately authorized evaluator* inputs. Validated metadata / successful
checks are NOT evidence of real scientific selection or non-synthetic validity.
"""

from __future__ import annotations

import math

from inventory_ejor.data.contracts import EvaluationTargets
from inventory_ejor.data.m4d0_execution import (
    METHOD,
    PrivateExecutionStore,
    scenario_contract,
    source_hashes,
)
from inventory_ejor.data.protocol import require
from inventory_ejor.data.provenance import fingerprint
from inventory_ejor.data.views import load_learner
from inventory_ejor.envs import transition


def verify_synthetic_reference_trace(
    private_store: PrivateExecutionStore,
    plan_digest,
    fit_digest,
    score_digest,
    targets: EvaluationTargets,
):
    """Read-only counterfactual replay of all original saved synthetic results."""
    require(
        type(private_store) is PrivateExecutionStore,
        "Use isolated private artifact store",
    )
    plan = private_store.read(plan_digest, kind="synthetic_reference_execution_plan")
    fit = private_store.read(fit_digest, kind="synthetic_reference_fit_result")
    saved_approval = private_store.read(
        fit["execution_approval_sha256"],
        kind="synthetic_reference_run_approval",
    )
    require(
        saved_approval["approved"] is True
        and saved_approval["plan_sha256"] == plan_digest
        and saved_approval["approved_by_owner"]
        and saved_approval["decision_record"],
        "Execution approval is not a pinned owner attestation",
    )
    score = private_store.read(score_digest, kind="synthetic_reference_score_evidence")
    require(
        score["execution_approval_sha256"] == fingerprint(saved_approval),
        "Score and persisted execution approval mismatch",
    )
    trace_record = private_store.read(
        score["trace_sha256"], kind="synthetic_private_scoring_trace"
    )
    require(
        plan["dependency_sha256s"] == source_hashes()
        and score["source_code_sha256s"] == source_hashes(),
        "Execution/audit code drifted from pinned source dependencies",
    )
    require(
        (
            fit["plan_sha256"],
            score["plan_sha256"],
            score["fit_sha256"],
            trace_record["plan_sha256"],
            trace_record["fit_sha256"],
        )
        == (plan_digest, plan_digest, fit_digest, plan_digest, fit_digest),
        "Broken result-to-plan-to-trace provenance chain",
    )
    require(
        plan["method"] == fit["method"] == METHOD
        and plan["dataset"].startswith("synthetic-")
        and fit["learner_sha256"] == plan["learner_sha256"]
        and fit["seed"] == plan["seed"]
        and score["scenario_sha256"]
        == fit["scenario_sha256"]
        == plan["scenario_sha256"]
        == fingerprint(plan["scenario"]),
        "Mismatched method/dataset/seed/scenario metadata",
    )
    view = load_learner(
        private_store.file(plan["learner_sha256"]),
        sha256=plan["learner_sha256"],
        dataset=plan["dataset"],
        series=plan["series"],
        origin=plan["origin"],
        budget=plan["budget"],
    )
    scenario, state = scenario_contract(plan["scenario"])
    proposed = min(
        scenario.max_order * (scenario.lead_time + 1),
        math.ceil(
            (math.fsum(o.sales for o in view.history.observations) / plan["budget"])
            * (scenario.lead_time + 1)
        ),
    )
    require(
        fit["base_stock_target"] == proposed
        and fit["sum_training_sales"] == sum(o.sales for o in view.history.observations)
        and fit["real_history_observations"] == plan["budget"]
        and fit["optimizer_steps"] == fit["simulated_transitions"] == 0
        and fit["trained_gp"] is False
        and fit["trained_rl"] is False,
        "Fitted reference parameters/effort do not match pinned learner history",
    )
    require(
        isinstance(targets, EvaluationTargets)
        and (targets.dataset, targets.series) == (plan["dataset"], plan["series"])
        and targets.window.start == plan["origin"]
        and len(targets.observations) == scenario.horizon,
        "Evaluation targets outside pinned synthetic task",
    )
    rows = trace_record["periods"]
    require(
        type(rows) is list and len(rows) == scenario.horizon,
        "Missing or extra saved scorer transitions",
    )
    costs = {
        "holding": 0.0,
        "lost_sales": 0.0,
        "variable_order": 0.0,
        "fixed_order": 0.0,
    }
    served = requests = 0
    for t, (recorded, observed) in enumerate(
        zip(rows, targets.observations, strict=True)
    ):
        q = max(
            0, min(scenario.max_order, proposed - (state.on_hand + sum(state.pipeline)))
        )
        if t + scenario.lead_time >= scenario.horizon:
            q = 0
        require(
            recorded["day"] == observed.day
            and recorded["period"] == t
            and recorded["observed_sales_as_requests"] == observed.sales
            and recorded["on_hand"] == state.on_hand
            and recorded["pipeline"] == list(state.pipeline)
            and recorded["order"] == q,
            "Saved action, history or current-request path differs",
        )
        outcome = transition(scenario, state, q, observed.sales)
        require(
            recorded["fulfilled"] == outcome.sales
            and recorded["lost_units"] == outcome.lost_units
            and math.isclose(
                recorded["cost"], outcome.costs.total, rel_tol=1e-12, abs_tol=1e-9
            ),
            "Saved reference transition/cost differs",
        )
        for name in costs:
            costs[name] += getattr(outcome.costs, name)
        served += outcome.sales
        requests += observed.sales
        state = outcome.next_state
    expected_cost = math.fsum(costs.values())
    require(
        all(
            math.isclose(
                costs[k], score["cost_components"][k], rel_tol=1e-12, abs_tol=1e-9
            )
            for k in costs
        )
        and math.isclose(
            expected_cost, score["total_cost"], rel_tol=1e-12, abs_tol=1e-9
        )
        and score["fulfilled"] == served
        and score["requests"] == requests
        and score["simulation_periods"] == len(rows)
        and score["ending_stock"] == rows[-1]["on_hand"] - rows[-1]["fulfilled"]
        and score["ending_pipeline"] == list(state.pipeline)
        and (
            score["fill_rate"] == served / requests
            if requests
            else score["fill_rate"] is None
        ),
        "Saved score totals, fill rate or terminal state differ",
    )
    return {
        "status": "independent_synthetic_replay_verified",
        "periods": len(rows),
        "total_cost": expected_cost,
        "training_observations": len(view.history.observations),
        "evaluation_requests": requests,
        "trained_gp": False,
        "trained_rl": False,
    }
