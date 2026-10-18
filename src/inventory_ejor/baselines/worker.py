"""Single approved baseline task. Never called during preparation-only work."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from .planning import (
    check_approval,
    check_live_plan,
    encode,
    inside,
    read_json,
    sha_file,
)

ROOT = Path(__file__).resolve().parents[3]


def execute_job(root, plan, job, output, device_kind):
    # Numerical imports occur only after main() has checked owner approval.
    from inventory_ejor.data.budgets import SourcePolicy, access, validate_ledger
    from inventory_ejor.data.contracts import Window
    from inventory_ejor.data.views import load_learner
    from inventory_ejor.envs import (
        CostParameters,
        InventoryConfig,
        InventoryState,
        transition,
    )

    from .controllers import PredictiveInventoryPolicy
    from .models import GPSampler, SimpleSampler

    cfg = plan["config"]
    # Applied only inside an explicitly approved worker, never by preparation.
    import resource

    cpu_cap = cfg["resources"]["job_timeout_seconds"]
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_cap, cpu_cap))
    if device_kind == "cpu":
        resource.setrlimit(resource.RLIMIT_AS, (8192 * 1024**2, 8192 * 1024**2))
    learner_path = inside(root, job["learner_file"], "data/processed")
    view = load_learner(
        learner_path,
        sha256=job["learner_sha256"],
        dataset=job["dataset_version"],
        series=job["series"],
        origin=job["origin"],
        budget=job["budget"],
    )
    info = copy.deepcopy(job["history_ledger"])
    info["method"] = job["method"]
    info["access"]["demand_model_fitting"] = [access(view.history)]
    if job["method"].startswith("gp_"):
        info["access"]["hyperparameter_optimization"] = [access(view.history)]
    info["compute_allowance"] = {
        "cpu_seconds": cfg["resources"]["job_timeout_seconds"],
        "memory_mb": 8192,
        "gpu": 1 if device_kind == "gpu" else 0,
    }
    policies = tuple(
        SourcePolicy(
            p["dataset"],
            p["first_date"],
            tuple(Window(**w) for w in p["allowed"]),
            tuple(Window(**w) for w in p["forbidden_outcomes"]),
        )
        for p in job["source_policies"]
    )
    validate_ledger(info, policies, view.history)
    # Shared seed mapping for the two GP controllers; no full-dataset fingerprint.
    seed_key = f"{job['series']}:{job['origin']}:{job['budget']}:{job['seed']}"
    seed = int.from_bytes(hashlib.sha256(seed_key.encode()).digest()[:4], "big") % (
        2**31 - 10000
    )
    start = time.monotonic()
    if device_kind == "gpu":
        sampler = GPSampler(
            view,
            job["horizon"],
            cfg["gp"],
            cfg["sampling"]["max_generated_count"],
            seed,
            cfg["resources"]["gpu_memory_fraction"],
        )
    else:
        kind = (
            "empirical" if job["method"] == "empirical_base_stock" else "gamma_poisson"
        )
        sampler = SimpleSampler(
            view, kind, cfg["gamma_poisson"], cfg["sampling"]["max_generated_count"]
        )
    fit_seconds = time.monotonic() - start
    scenario = cfg["scenario"]
    initial = InventoryState(
        scenario["initial_on_hand"], tuple(scenario["initial_pipeline"])
    )
    policy = PredictiveInventoryPolicy(
        sampler,
        scenario,
        cfg["base_stock_levels"],
        initial,
        job["horizon"],
        cfg["sampling"],
        seed,
        device_kind,
        job["method"] == "gp_rollout",
    )
    fit_and_tune_seconds = time.monotonic() - start

    # Only the trusted scorer reads outcomes, AFTER model fitting/base-policy tuning.
    target_path = inside(root, job["evaluator_file"], "data/processed")
    if sha_file(target_path) != job["evaluator_sha256"]:
        raise ValueError("Evaluation artifact changed")
    target = read_json(target_path)[job["evaluation_token"]]
    observations = target["observations"]
    if target["dataset"] != job["dataset_version"] or target["series"] != job["series"]:
        raise ValueError("Evaluator identity mismatch")
    if [o["day"] for o in observations] != list(
        range(job["origin"], job["origin"] + job["horizon"])
    ):
        raise ValueError("Evaluation days mismatch")
    if target["window"] != {
        "start": job["origin"],
        "stop": job["origin"] + job["horizon"],
    }:
        raise ValueError("Evaluation boundary mismatch")
    config = InventoryConfig(
        scenario["lead_time"],
        job["horizon"],
        scenario["max_order"],
        CostParameters(**scenario["costs"]),
    )
    state = initial
    trace = []
    totals = {
        k: 0.0 for k in ("holding", "lost_sales", "variable_order", "fixed_order")
    }
    total_demand = total_sales = 0
    for t, observation in enumerate(observations):
        # No outcome is an argument to action(); only current M1 state and time.
        q = policy.action(job["horizon"] - t, state)
        outcome = transition(config, state, q, observation["sales"])
        for name in totals:
            totals[name] += getattr(outcome.costs, name)
        total_demand += outcome.demand
        total_sales += outcome.sales
        trace.append(
            {
                "period": t,
                "day": observation["day"],
                "order": q,
                "on_hand": state.on_hand,
                "pipeline": list(state.pipeline),
                "observed_sales_as_requests": outcome.demand,
                "fulfilled": outcome.sales,
                "lost_units": outcome.lost_units,
                "cost": outcome.costs.total,
            }
        )
        state = outcome.next_state
    info["synthetic_transitions"] = policy.simulated_transitions
    info["optimization_trials"] = policy.level_grid_size + policy.action_comparisons
    counts = validate_ledger(info, policies, view.history)
    peak_rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    if peak_rss_mib > info["compute_allowance"]["memory_mb"]:
        raise MemoryError("Worker exceeded its declared host-memory budget")
    result = {
        "status": "completed_development_baseline_requires_review",
        "job": job["id"],
        "method": job["method"],
        "series": job["series"],
        "budget": job["budget"],
        "seed": job["seed"],
        "effective_seed": seed,
        "model": sampler.metadata,
        "total_cost": sum(totals.values()),
        "cost_components": totals,
        "fill_rate": total_sales / total_demand if total_demand else None,
        "zero_total_demand": total_demand == 0,
        "selected_base_stock": policy.level,
        "base_stock_grid_upper_boundary_selected": policy.level_at_upper_boundary,
        "tuning_model_costs_not_test_results": policy.tuning_costs,
        "fit_seconds": fit_seconds,
        "fit_and_tune_seconds": fit_and_tune_seconds,
        "total_seconds": time.monotonic() - start,
        "host_peak_rss_mib": peak_rss_mib,
        "order_cap_binding_periods": sum(
            row["order"] == scenario["max_order"] and scenario["max_order"] > 0
            for row in trace
        ),
        "simulated_paths": policy.simulated_paths,
        "information_ledger": info,
        "validated_information_counts": counts,
        "source_commit": plan["git"]["commit"],
        "execution_source_hashes": plan["execution_sources"],
        "physical_gpu_env": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "rl_training": False,
        "our_proposed_method": False,
        "scientific_status": "development only; not deployment evidence, si"
        "gnificance, novelty or publication result",
        "terminal": {
            "ending_stock_before_receipt": outcome.ending_on_hand,
            "outstanding_receipts": list(outcome.outstanding_after_order),
            "additional_value": 0.0,
        },
    }
    for name, payload in (
        ("result.json", result),
        ("private_sales_replay.json", trace),
    ):
        with (output / name).open("xb") as stream:
            stream.write(encode(payload))
    print(
        json.dumps(
            {
                "job": job["id"],
                "status": "succeeded",
                "output": str(output.relative_to(root)),
            }
        )
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--job-index", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        plan, approval = read_json(args.plan), read_json(args.approval)
        check_approval(plan, approval)
        check_live_plan(ROOT, plan)
        if not 0 <= args.job_index < len(plan["jobs"]):
            raise ValueError("Invalid job index")
        job = plan["jobs"][args.job_index]
        visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        if job["device_kind"] == "gpu" and (not visible or "," in visible):
            raise PermissionError(
                "GPU job must be isolated to exactly one assigned device"
            )
        if job["device_kind"] == "cpu" and visible:
            raise PermissionError("CPU worker must not see GPUs")
        output = inside(ROOT, args.output, "results/runs")
        output.mkdir(parents=False, exist_ok=False)
        execute_job(ROOT, plan, job, output, job["device_kind"])
    except Exception as exc:
        print(f"BASELINE WORKER FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
