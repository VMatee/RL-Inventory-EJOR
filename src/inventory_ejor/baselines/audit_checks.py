"""Strict read-only M4b verification helpers.

No model inference, worker execution, new output, or reserved-phase reads.
Uses a separate hand-written receipt/calendar oracle to check the unchanged
production M1 transition semantics rather than importing transition().
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

from inventory_ejor.data.budgets import SourcePolicy, access, validate_ledger
from inventory_ejor.data.contracts import Window
from inventory_ejor.data.provenance import read_json as parse_json_bytes
from inventory_ejor.data.views import load_learner

from .planning import inside, read_json, sha_file


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checked_leaf(root: Path, path: Path, prefix: str) -> Path:
    """Reject symlinks and paths outside a trusted subtree BEFORE any open."""
    root = Path(root).resolve()
    path = Path(path).absolute()
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Input file escapes Git root") from exc
    actual = inside(root, str(relative), prefix)
    require(
        actual.is_file() and not actual.is_symlink(), "Missing/non-regular audit input"
    )
    return actual


def evaluate_job(root, job, trace, cache):
    """Bind saved requests to the exact immutable scorer-visible M3 evaluator."""
    path = checked_leaf(root, root / job["evaluator_file"], "data/processed")
    cached = cache.get(str(path))
    if cached is None:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        require(digest == job["evaluator_sha256"], "Evaluator input checksum mismatch")
        parsed = parse_json_bytes(raw)
        cache[str(path)] = (digest, parsed)
        cached = cache[str(path)]
    digest, document = cached
    require(digest == job["evaluator_sha256"], "Evaluator plan hashes disagree")
    token = f"{job['series']}@{job['origin']}"
    require(
        job["evaluation_token"] == token and token in document,
        "Evaluator series/origin token mismatch",
    )
    target = document[token]
    require(
        target["dataset"] == job["dataset_version"]
        and target["series"] == job["series"]
        and target["window"]
        == {"start": job["origin"], "stop": job["origin"] + job["horizon"]},
        "Evaluator identity/window mismatch",
    )
    observations = target["observations"]
    require(len(observations) == job["horizon"], "Evaluator observation count mismatch")
    for day, (observation, recorded) in enumerate(
        zip(observations, trace, strict=True)
    ):
        require(
            observation["day"] == job["origin"] + day
            and type(observation["sales"]) is int
            and observation["sales"] >= 0
            and recorded["day"] == observation["day"]
            and recorded["observed_sales_as_requests"] == observation["sales"],
            "Saved replay requests do not match pinned M3 evaluator",
        )
    return str(path)


def policy_counts(config, job):
    """Reconstruct policy simulation effort from fixed algorithm loop geometry."""
    horizon = job["horizon"]
    lead = config["scenario"]["lead_time"]
    base_levels = len(config["base_stock_levels"])
    paths_tuning = config["sampling"]["tuning_paths"]
    base_steps = base_levels * paths_tuning * horizon
    periods = max(0, horizon - lead)
    rollout = job["method"] == "gp_rollout"
    actions = config["scenario"]["max_order"] + 1
    decision_paths = config["sampling"]["decision_paths"]
    decisions_simulated = (
        actions * decision_paths * sum(range(lead + 1, horizon + 1)) if rollout else 0
    )
    return {
        "synthetic_transitions": base_steps + decisions_simulated,
        "optimization_trials": base_levels + actions * periods
        if rollout
        else base_levels,
        "simulated_paths": paths_tuning + periods * decision_paths
        if rollout
        else paths_tuning,
    }


def reconstructed_ledger(root, plan, job, result):
    """Load the actual pre-origin learner and fully reconstruct validated lineage."""
    path = checked_leaf(root, root / job["learner_file"], "data/processed")
    view = load_learner(
        path,
        sha256=job["learner_sha256"],
        dataset=job["dataset_version"],
        series=job["series"],
        origin=job["origin"],
        budget=job["budget"],
    )
    historical = copy.deepcopy(job["history_ledger"])
    historical["method"] = job["method"]
    historical["access"]["demand_model_fitting"] = [access(view.history)]
    if job["method"].startswith("gp_"):
        historical["access"]["hyperparameter_optimization"] = [access(view.history)]
    historical["compute_allowance"] = {
        "cpu_seconds": plan["config"]["resources"]["job_timeout_seconds"],
        "memory_mb": 8192,
        "gpu": 1 if job["device_kind"] == "gpu" else 0,
    }
    effort = policy_counts(plan["config"], job)
    historical["synthetic_transitions"] = effort["synthetic_transitions"]
    historical["optimization_trials"] = effort["optimization_trials"]
    policies = tuple(
        SourcePolicy(
            p["dataset"],
            p["first_date"],
            tuple(Window(**w) for w in p["allowed"]),
            tuple(Window(**w) for w in p["forbidden_outcomes"]),
        )
        for p in job["source_policies"]
    )
    validated = validate_ledger(historical, policies, view.history)
    require(
        result["information_ledger"] == historical,
        "Observed ledger disagrees with independent expected access/compute",
    )
    require(
        result["validated_information_counts"] == json.loads(json.dumps(validated)),
        "Saved information counts fail independent validation",
    )
    require(
        result["simulated_paths"] == effort["simulated_paths"],
        "Saved synthetic path count disagrees with decision algorithm",
    )
    require(
        result["effective_seed"]
        == (
            int.from_bytes(
                hashlib.sha256(
                    f"{job['series']}:{job['origin']}:{job['budget']}:{job['seed']}".encode()
                ).digest()[:4],
                "big",
            )
            % (2**31 - 10000)
        ),
        "Effective seed does not match planned series/origin/budget/seed",
    )
    return view.history.observations, effort


def independent_calendar_replay(scenario, job, trace, result):
    """Independent small calendar-list oracle, no call to the production M1 transition.

    Inventory state starts after this period's receipt. Outstanding after order
    has L batches; the first is due next review, the rest form next pipeline.
    """
    lead, cap = scenario["lead_time"], scenario["max_order"]
    holding, short = scenario["costs"]["holding"], scenario["costs"]["lost_sales"]
    variable, fixed = (
        scenario["costs"]["variable_order"],
        scenario["costs"]["fixed_order"],
    )
    hand = scenario["initial_on_hand"]
    pipeline = list(scenario["initial_pipeline"])
    require(len(pipeline) == lead - 1, "Invalid initial pipeline")
    totals = dict(holding=0.0, lost_sales=0.0, variable_order=0.0, fixed_order=0.0)
    terminal = None
    requests = fulfilled = 0
    for time_index, row in enumerate(trace):
        q, d = row["order"], row["observed_sales_as_requests"]
        require(
            row["period"] == time_index
            and row["day"] == job["origin"] + time_index
            and row["on_hand"] == hand
            and row["pipeline"] == pipeline,
            "Independent calendar state/period differs",
        )
        require(
            type(q) is int and 0 <= q <= cap and type(d) is int and d >= 0,
            "Invalid independent-calendar action/request",
        )
        if job["horizon"] - time_index <= lead:
            require(q == 0, "Too-late order in independent-calendar replay")
        served, missed = min(hand, d), max(d - hand, 0)
        ending = hand - served
        outstanding = pipeline + [q]
        require(
            row["fulfilled"] == served and row["lost_units"] == missed,
            "Independent calendar fulfilled/lost mismatch",
        )
        period_cost = {
            "holding": holding * ending,
            "lost_sales": short * missed,
            "variable_order": variable * q,
            "fixed_order": fixed if q > 0 else 0.0,
        }
        require(
            math.isclose(
                sum(period_cost.values()), row["cost"], rel_tol=0, abs_tol=1e-9
            ),
            "Independent calendar cost differs",
        )
        for key in totals:
            totals[key] += period_cost[key]
        terminal = {
            "ending_stock_before_receipt": ending,
            "outstanding_receipts": outstanding,
            "additional_value": scenario["additional_terminal_value"],
        }
        hand = ending + outstanding[0]
        pipeline = outstanding[1:]
        requests += d
        fulfilled += served
    require(terminal == result["terminal"], "Terminal state/receipts metadata mismatch")
    require(
        all(
            math.isclose(v, result["cost_components"][k], rel_tol=0, abs_tol=1e-9)
            for k, v in totals.items()
        ),
        "Independent calendar cost components mismatch",
    )
    require(
        math.isclose(
            sum(totals.values()), result["total_cost"], rel_tol=0, abs_tol=1e-9
        ),
        "Independent calendar total cost mismatch",
    )
    return requests, fulfilled, totals


def bound_wrapper(root, session, plan, job_index, job, entry, used_manifests):
    """Bind the actual worker receipt to exactly one source, job, and output."""
    path = checked_leaf(root, root / entry["wrapper_manifest"], "results/runs")
    require(
        sha_file(path) == entry["wrapper_manifest_sha256"],
        "Saved job wrapper receipt checksum mismatch",
    )
    require(str(path) not in used_manifests, "Duplicate job wrapper receipt")
    used_manifests.add(str(path))
    receipt = read_json(path)
    command = receipt["command"]
    require(
        type(command) is list and len(command) == 10,
        "Worker wrapper command shape mismatch",
    )
    require(
        Path(command[1]) == root / "scripts/baseline_worker.py"
        and command[2:]
        == [
            "--plan",
            str(session / "plan.json"),
            "--approval",
            str(session / "approval.json"),
            "--job-index",
            str(job_index),
            "--output",
            entry["output"],
        ],
        "Wrapper receipt does not belong to this planned job",
    )
    require(
        Path(command[0]).is_file() and "python" in Path(command[0]).name,
        "Wrapper worker executable is not Python",
    )
    require(
        receipt["status"] == "succeeded"
        and receipt["exit_code"] == entry["exit_code"] == 0
        and receipt["kind"] == "pilot"
        and receipt["clean_source"] is True
        and receipt["git_status_before"] == receipt["git_status_after"] == ""
        and receipt["source_unchanged"] is True
        and receipt["source_commit"]
        == receipt["source_commit_after"]
        == plan["git"]["commit"]
        and receipt["seed"] == job["seed"]
        and receipt["cwd"] == str(root)
        and receipt["config_sha256"] == plan["config_sha256"]
        and Path(receipt["config_path"]) == root / plan["config_path"]
        and receipt["data_manifest"]
        == {
            "path": str(root / plan["bundle_manifest"]),
            "sha256": plan["bundle_manifest_sha256"],
        }
        and receipt["timeout_seconds"]
        == plan["config"]["resources"]["job_timeout_seconds"],
        "Invalid per-job wrapper provenance",
    )
    return receipt
