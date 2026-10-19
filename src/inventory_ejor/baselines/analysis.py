"""Read-only, integrity-first analysis of a completed M4 development campaign.

This module NEVER fits models, dispatches workers, changes source/results, or
opens an unreleased/final-evaluation dataset. Results are descriptions of a
single development sales-as-requests scenario, not statistical inference.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from inventory_ejor.baselines.audit_checks import (
    bound_wrapper,
    checked_leaf,
    evaluate_job,
    independent_calendar_replay,
    reconstructed_ledger,
)
from inventory_ejor.baselines.planning import (
    check_approval,
    inside,
    read_json,
    sha_file,
)
from inventory_ejor.baselines.reporting import summarize_session
from inventory_ejor.envs import (
    CostParameters,
    InventoryConfig,
    InventoryState,
    transition,
)

METHODS = (
    "empirical_base_stock",
    "gamma_poisson_base_stock",
    "gp_base_stock",
    "gp_rollout",
)
BUDGETS = (28, 56, 112, 224)


def require(test: bool, description: str) -> None:
    if not test:
        raise ValueError(description)


def close(a: float, b: float) -> bool:
    return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-9)


def safe_fraction(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def cost_profile(result: dict) -> dict:
    return {
        "holding": float(result["cost_components"]["holding"]),
        "lost_sales": float(result["cost_components"]["lost_sales"]),
        "variable_order": float(result["cost_components"]["variable_order"]),
        "fixed_order": float(result["cost_components"]["fixed_order"]),
    }


def paired_summary(
    by_case: dict,
    series: list[str],
    budgets: list[int],
    comparator: str,
    challenger: str,
) -> dict:
    """Descriptive matched differences only; a series is the cluster."""
    deltas = [
        float(by_case[s, b, comparator]["total_cost"])
        - float(by_case[s, b, challenger]["total_cost"])
        for s in series
        for b in budgets
    ]
    clustered = {
        s: statistics.mean(
            float(by_case[s, b, comparator]["total_cost"])
            - float(by_case[s, b, challenger]["total_cost"])
            for b in budgets
        )
        for s in series
    }
    lhs = math.fsum(
        float(by_case[s, b, comparator]["total_cost"]) for s in series for b in budgets
    )
    rhs = math.fsum(
        float(by_case[s, b, challenger]["total_cost"]) for s in series for b in budgets
    )
    return {
        "comparator": comparator,
        "challenger": challenger,
        "paired_cases": len(deltas),
        "independent_series_not_asserted": len(series),
        "mean_paired_delta": statistics.mean(deltas),
        "median_paired_delta": statistics.median(deltas),
        "relative_pooled_cost_reduction": safe_fraction(lhs - rhs, lhs),
        "paired_wins_ties_losses": [
            sum(x > 0 for x in deltas),
            sum(x == 0 for x in deltas),
            sum(x < 0 for x in deltas),
        ],
        "series_average_deltas": clustered,
        "series_wins_ties_losses": [
            sum(x > 0 for x in clustered.values()),
            sum(x == 0 for x in clustered.values()),
            sum(x < 0 for x in clustered.values()),
        ],
    }


def recheck_trace(
    cfg: InventoryConfig, state: InventoryState, observations: list, origin: int
) -> tuple[int, int, float, dict]:
    """Independent M1 replay of every saved action and observed sales request."""
    total = 0.0
    parts = {
        key: 0.0 for key in ("holding", "lost_sales", "variable_order", "fixed_order")
    }
    requests = fulfilled = 0
    for t, observation in enumerate(observations):
        require(
            observation["day"] == origin + t and observation["period"] == t,
            "Trace chronology mismatch",
        )
        require(
            observation["on_hand"] == state.on_hand
            and observation["pipeline"] == list(state.pipeline),
            "Trace inventory state mismatch",
        )
        order, demand = observation["order"], observation["observed_sales_as_requests"]
        require(
            type(order) is int and 0 <= order <= cfg.max_order, "Order out of bounds"
        )
        require(type(demand) is int and demand >= 0, "Invalid sales-as-requests")
        if cfg.horizon - t <= cfg.lead_time:
            require(order == 0, "Order would arrive after evaluation horizon")
        outcome = transition(cfg, state, order, demand)
        require(
            outcome.sales == observation["fulfilled"]
            and outcome.lost_units == observation["lost_units"],
            "Replay units differ from M1 reference",
        )
        require(
            close(outcome.costs.total, observation["cost"]),
            "Replay cost differs from M1 reference",
        )
        total += outcome.costs.total
        for key in parts:
            parts[key] += getattr(outcome.costs, key)
        requests += demand
        fulfilled += outcome.sales
        state = outcome.next_state
    return requests, fulfilled, total, parts


def analyze_session(root: Path, session: Path) -> dict:
    """Fully verify one completed development session, then analyze read-only.

    Refuses partial, changed or non-development outputs, any missing/mismatched
    provenance or incomplete crossed comparisons.
    """
    root = Path(root).resolve()
    raw_session = Path(session).absolute()
    require(
        raw_session.parent == root / "results/runs",
        "Expected direct child of results/runs, not arbitrary file path",
    )
    session = inside(root, str(raw_session.relative_to(root)), "results/runs")
    require(session.is_dir(), "Missing or noncanonical saved session")
    plan = read_json(checked_leaf(root, session / "plan.json", "results/runs"))
    summary = read_json(
        checked_leaf(root, session / "session_summary.json", "results/runs")
    )
    approval = read_json(checked_leaf(root, session / "approval.json", "results/runs"))
    check_approval(plan, approval)
    require(
        sha_file(inside(root, plan["config_path"])) == plan["config_sha256"],
        "Development config changed",
    )
    require(
        sha_file(inside(root, plan["bundle_manifest"], "data/processed"))
        == plan["bundle_manifest_sha256"],
        "Development manifest changed",
    )
    require(
        plan["config"]["purpose"] == "development_preview_not_publication",
        "Only the prespecified M4 development plan is analyzable",
    )
    require(
        str(plan["data_source_fingerprint"]).startswith("m5-sha256:"),
        "Not an M5 development source",
    )
    require(
        summary["scientific_acceptance"] == "development_only_not_publication",
        "Refuse incorrectly labeled study",
    )
    require(plan["git"]["commit"] == summary["source_commit"], "Source commit mismatch")
    require(
        summary["status"] == "completed" and summary.get("error") is None,
        "Session not successfully completed",
    )
    require(
        summary["jobs_requested"] == summary["jobs_finished"] == len(plan["jobs"]),
        "Session job counts inconsistent",
    )

    # No aggregate generator may touch arbitrary or symlinked result leaves.
    # Preflight ALL the stored file paths before invoking historical reporting.
    for entry in summary["entries"]:
        location = root / entry["output"]
        require(location.parent == session, "Results belong to another session")
        checked_leaf(root, location / "result.json", "results/runs")
        checked_leaf(root, location / "private_sales_replay.json", "results/runs")
        checked_leaf(root, root / entry["wrapper_manifest"], "results/runs")
    checked_leaf(root, session / "baseline_results.csv", "results/runs")
    generated = summarize_session(root, session, write=False)
    require(
        generated
        == read_json(
            checked_leaf(root, session / "aggregate_summary.json", "results/runs")
        ),
        "Saved aggregate does not match independent checksum-verifying regeneration",
    )

    with checked_leaf(root, session / "baseline_results.csv", "results/runs").open(
        newline="", encoding="utf-8"
    ) as file:
        listed = list(csv.DictReader(file))
    csv_rows = {row["job"]: row for row in listed}
    require(
        len(csv_rows) == len(listed) == len(plan["jobs"]),
        "CSV row count or job identity mismatch",
    )

    config = plan["config"]["scenario"]
    require(
        config["initial_on_hand"] == 0
        and all(v == 0 for v in config["initial_pipeline"])
        and config["lead_time"] > 0,
        "The first-run unavoidable-shortage interpretation assumes zero "
        "initial stock/pipeline and positive lead time",
    )
    job_index = {job["id"]: job for job in plan["jobs"]}
    require(len(job_index) == len(plan["jobs"]), "Duplicate job")
    entries = summary["entries"]
    require(
        {entry["job"] for entry in entries} == set(job_index)
        and len(entries) == len(job_index),
        "Entry identity mismatch",
    )
    require(
        set(plan["config"]["methods"]) == set(METHODS)
        and set(plan["config"]["budgets"]) == set(BUDGETS),
        "Unexpected preliminary baseline comparison matrix",
    )

    by_case: dict = {}
    traces: dict = {}
    history: dict = {}
    gpu_lanes: Counter = Counter()
    transitions_verified = 0
    costs_by_method = defaultdict(lambda: Counter())
    runtime_by_method: dict[str, list[float]] = defaultdict(list)
    gp_losses: dict = {}
    evaluations: dict = {}
    used_manifests: set[str] = set()
    job_positions = {job["id"]: idx for idx, job in enumerate(plan["jobs"])}
    for entry in entries:
        job = job_index[entry["job"]]
        require(entry["exit_code"] == 0, "Nonzero job status")
        for name, key in (
            ("result.json", "result_sha256"),
            ("private_sales_replay.json", "trace_sha256"),
        ):
            path = inside(root, str(Path(entry["output"]) / name), "results/runs")
            require(sha_file(path) == entry[key], "Modified result/trace checksum")
        bound_wrapper(
            root, session, plan, job_positions[entry["job"]], job, entry, used_manifests
        )

        output = inside(root, entry["output"], "results/runs")
        require(output.parent == session, "Result escapes this session")
        result, trace = (
            read_json(output / "result.json"),
            read_json(output / "private_sales_replay.json"),
        )
        for key in ("method", "series", "budget", "seed"):
            require(result[key] == job[key], f"Result field mismatch: {key}")
        require(
            result["job"] == entry["job"]
            and result["source_commit"] == plan["git"]["commit"]
            and result["rl_training"] is False
            and result["our_proposed_method"] is False
            and result["execution_source_hashes"] == plan["execution_sources"]
            and result["status"] == "completed_development_baseline_requires_review",
            "Misidentified development result",
        )
        require(len(trace) == job["horizon"], "Missing replay periods")
        m1_config = InventoryConfig(
            config["lead_time"],
            job["horizon"],
            config["max_order"],
            CostParameters(**config["costs"]),
        )
        initial = InventoryState(
            config["initial_on_hand"], tuple(config["initial_pipeline"])
        )
        evaluate_job(root, job, trace, evaluations)
        requests, fulfilled, total_cost, cost_components = recheck_trace(
            m1_config, initial, trace, job["origin"]
        )
        calendar_requests, calendar_filled, _ = independent_calendar_replay(
            config, job, trace, result
        )
        require(
            (requests, fulfilled) == (calendar_requests, calendar_filled),
            "Independent calendar and M1 replay disagree",
        )
        require(
            close(total_cost, result["total_cost"])
            and close(sum(cost_profile(result).values()), total_cost)
            and all(
                close(cost_components[k], v) for k, v in cost_profile(result).items()
            ),
            "Result cost decomposition mismatch",
        )
        listed_row = csv_rows[entry["job"]]
        require(
            listed_row["method"] == job["method"]
            and listed_row["series"] == job["series"]
            and int(listed_row["budget"]) == job["budget"]
            and int(listed_row["seed"]) == job["seed"]
            and listed_row["output"] == entry["output"]
            and close(float(listed_row["total_cost"]), total_cost)
            and int(listed_row["total_requests"]) == requests
            and int(listed_row["fulfilled_requests"]) == fulfilled
            and int(listed_row["origin"]) == job["origin"]
            and close(float(listed_row["runtime_seconds"]), result["total_seconds"])
            and close(
                float(listed_row["selected_base_stock"]), result["selected_base_stock"]
            )
            and listed_row["upper_grid_boundary"]
            == str(result["base_stock_grid_upper_boundary_selected"])
            and int(listed_row["order_cap_periods"])
            == result["order_cap_binding_periods"]
            and (
                (listed_row["fill_rate"] == "" and requests == 0)
                or (
                    requests > 0
                    and close(float(listed_row["fill_rate"]), fulfilled / requests)
                )
            ),
            "Saved CSV does not match verified job",
        )
        require(
            close(result["fill_rate"], fulfilled / requests)
            if requests
            else result["fill_rate"] is None,
            "Wrong saved fill rate",
        )
        learner_observations, effort = reconstructed_ledger(root, plan, job, result)
        require(
            result["information_ledger"]["synthetic_transitions"]
            == effort["synthetic_transitions"],
            "Reconstructed compute budget mismatch",
        )
        series_key = (job["series"], job["origin"], job["budget"])
        method_key = (job["series"], job["budget"], job["method"])
        require(method_key not in by_case, "Duplicate series/budget/method")
        by_case[method_key] = result
        traces[method_key] = trace
        transitions_verified += len(trace)
        for cost_name, amount in cost_profile(result).items():
            costs_by_method[job["method"]][cost_name] += amount
        costs_by_method[job["method"]]["total"] += total_cost
        costs_by_method[job["method"]]["requests"] += requests
        costs_by_method[job["method"]]["fulfilled"] += fulfilled
        costs_by_method[job["method"]]["simulated_transitions"] += result[
            "information_ledger"
        ]["synthetic_transitions"]
        runtime_by_method[job["method"]].append(result["total_seconds"])
        if job["device_kind"] == "gpu":
            require(
                entry["physical_gpu_uuid"].startswith("GPU-"),
                "Missing physical GPU UUID",
            )
            gpu_lanes[entry["physical_gpu_uuid"]] += 1
        else:
            require(
                entry["physical_gpu_uuid"] is None, "CPU job incorrectly claims GPU"
            )

        if series_key not in history:
            history[series_key] = {
                "sum_sales": sum(o.sales for o in learner_observations),
                "positive_days": sum(o.sales > 0 for o in learner_observations),
                "zero_days": sum(o.sales == 0 for o in learner_observations),
            }
        if job["method"] == "gp_base_stock":
            losses = result["model"]["marginal_likelihood_losses"]
            require(
                len(losses) == plan["config"]["gp"]["steps"]
                and all(math.isfinite(v) for v in losses),
                "Invalid GP training diagnostic",
            )
            gp_losses[job["series"], job["budget"]] = (losses[0], losses[-1])

    series = sorted({job["series"] for job in plan["jobs"]})
    budgets = sorted({job["budget"] for job in plan["jobs"]})
    require(
        len(by_case) == len(series) * len(budgets) * len(METHODS),
        "Incomplete comparison grid",
    )
    for s in series:
        expected = None
        for b in budgets:
            for m in METHODS:
                seq = tuple(
                    row["observed_sales_as_requests"] for row in traces[s, b, m]
                )
                if expected is None:
                    expected = seq
                require(
                    expected == seq,
                    "Future requests differ across compared models/budgets",
                )
    require(
        len(gpu_lanes) == len(plan["config"]["resources"]["gpu_ids"]),
        "The approved 4-GPU run did not use all four devices",
    )

    aggregate = {}
    for m in METHODS:
        totals = costs_by_method[m]
        aggregate[m] = {
            "jobs": len(runtime_by_method[m]),
            "mean_total_cost_per_28day_series": totals["total"]
            / len(runtime_by_method[m]),
            "total_cost": totals["total"],
            "cost_components": {
                k: totals[k]
                for k in ("holding", "lost_sales", "variable_order", "fixed_order")
            },
            "pooled_fill_rate": safe_fraction(totals["fulfilled"], totals["requests"]),
            "mean_job_runtime_seconds": statistics.mean(runtime_by_method[m]),
            "mean_simulated_transitions": (
                totals["simulated_transitions"] / len(runtime_by_method[m])
            ),
        }

    paired = {
        other: paired_summary(by_case, series, budgets, other, "gp_rollout")
        for other in METHODS
        if other != "gp_rollout"
    }
    budget_deltas = {}
    for method in METHODS:
        budget_deltas[method] = {}
        for budget in budgets[:-1]:
            values = [
                by_case[s, budget, method]["total_cost"]
                - by_case[s, 224, method]["total_cost"]
                for s in series
            ]
            budget_deltas[method][str(budget)] = {
                "mean_short_minus_224": statistics.mean(values),
                "median_short_minus_224": statistics.median(values),
                "short_better_ties_long_better": [
                    sum(v < 0 for v in values),
                    sum(v == 0 for v in values),
                    sum(v > 0 for v in values),
                ],
            }

    # Time-ordered paired replays expose how the decision method differs.
    gp_same_model = gp_same_tuned_level = gp_same_tuning_costs = 0
    changed_actions = periods = 0
    startup_cost = 0.0
    arrival_window_saving = later_window_saving = 0.0
    arrival_window_holding_saving = 0.0
    terminal_gp_stock = terminal_rollout_stock = 0
    for s in series:
        for b in budgets:
            left = by_case[s, b, "gp_base_stock"]
            right = by_case[s, b, "gp_rollout"]
            terminal_gp_stock += left["terminal"]["ending_stock_before_receipt"]
            terminal_rollout_stock += right["terminal"]["ending_stock_before_receipt"]
            gp_same_model += left["model"] == right["model"]
            gp_same_tuned_level += (
                left["selected_base_stock"] == right["selected_base_stock"]
            )
            gp_same_tuning_costs += (
                left["tuning_model_costs_not_test_results"]
                == right["tuning_model_costs_not_test_results"]
            )
            for t, (a, c) in enumerate(
                zip(
                    traces[s, b, "gp_base_stock"],
                    traces[s, b, "gp_rollout"],
                    strict=True,
                )
            ):
                periods += 1
                changed_actions += a["order"] != c["order"]
                if t < config["lead_time"]:
                    startup_cost += a["lost_units"] * config["costs"]["lost_sales"]
                elif t < min(2 * config["lead_time"], len(traces[s, b, "gp_rollout"])):
                    arrival_window_saving += a["cost"] - c["cost"]
                    arrival_window_holding_saving += (
                        (a["on_hand"] - a["fulfilled"])
                        - (c["on_hand"] - c["fulfilled"])
                    ) * config["costs"]["holding"]
                else:
                    later_window_saving += a["cost"] - c["cost"]

    sales_by_series = {
        s: sum(
            t["observed_sales_as_requests"] for t in traces[s, budgets[0], METHODS[0]]
        )
        for s in series
    }
    sorted_series = sorted(series, key=lambda s: (-sales_by_series[s], s))
    exclude_top2 = set(sorted_series[:2])
    total_requests = sum(sales_by_series.values())
    top2_rollout_cost = math.fsum(
        by_case[s, b, "gp_rollout"]["total_cost"]
        for s in sorted_series[:2]
        for b in budgets
    )
    gp_rollout_total = aggregate["gp_rollout"]["total_cost"]
    paired_top2_removed = {}
    leave_one_series_ranges = {}
    equal_series_relative_improvement = {}
    for other in METHODS:
        if other == "gp_rollout":
            continue
        subset = [s for s in series if s not in exclude_top2]
        paired_top2_removed[other] = (
            paired_summary(by_case, subset, budgets, other, "gp_rollout")[
                "relative_pooled_cost_reduction"
            ]
            if subset
            else None
        )
        leave_values = [
            paired_summary(
                by_case,
                [x for x in series if x != held],
                budgets,
                other,
                "gp_rollout",
            )["relative_pooled_cost_reduction"]
            for held in series
            if len(series) > 1
        ]
        leave_one_series_ranges[other] = {
            "min_relative_reduction": min(leave_values) if leave_values else None,
            "max_relative_reduction": max(leave_values) if leave_values else None,
        }
        relative_items = []
        for s in series:
            a = math.fsum(by_case[s, b, other]["total_cost"] for b in budgets)
            c = math.fsum(by_case[s, b, "gp_rollout"]["total_cost"] for b in budgets)
            if a > 0:
                relative_items.append((a - c) / a)
        equal_series_relative_improvement[other] = {
            "mean_relative_reduction": statistics.mean(relative_items),
            "median_relative_reduction": statistics.median(relative_items),
            "valid_series": len(relative_items),
        }

    origins = sorted({j["origin"] for j in plan["jobs"]})
    require(len(origins) == 1, "M4b initial-run audit expects one origin")
    origin = origins[0]
    histories28 = [history[s, origin, 28] for s in series]
    return {
        "schema_version": 1,
        "scope": "single M5 development scenario: descriptive, not final test",
        "source_commit": plan["git"]["commit"],
        "session": str(session.relative_to(root)),
        "session_wall_seconds": summary["runtime_seconds"],
        "integrity": {
            "verified_jobs": len(entries),
            "verified_wrapper_hashes": len(entries),
            "verified_result_hashes": len(entries),
            "verified_trace_hashes": len(entries),
            "independent_m1_transitions": transitions_verified,
            "identical_evaluation_requests_all_methods_and_budgets": True,
            "physical_gpu_jobs": dict(gpu_lanes),
        },
        "design": {
            "series": len(series),
            "budgets": budgets,
            "methods": list(METHODS),
            "seeds": plan["config"]["seeds"],
            "origin": sorted({j["origin"] for j in plan["jobs"]}),
            "horizon": sorted({j["horizon"] for j in plan["jobs"]}),
            "scenario": config,
        },
        "methods": aggregate,
        "published_aggregate_groups": generated["groups"],
        "paired_vs_gp_rollout": paired,
        "paired_vs_gp_rollout_excluding_two_highest_request_series": (
            paired_top2_removed
        ),
        "leave_one_series_relative_reduction_ranges": leave_one_series_ranges,
        "equal_series_average_relative_improvement": (
            equal_series_relative_improvement
        ),
        "budgets_compared_to_224": budget_deltas,
        "gp_controlled_ablation": {
            "same_fitted_model_pairs": gp_same_model,
            "same_tuned_base_stock_pairs": gp_same_tuned_level,
            "same_base_stock_tuning_cost_pairs": gp_same_tuning_costs,
            "total_pairs": len(series) * len(budgets),
            "changed_orders": changed_actions,
            "decision_periods": periods,
            "changed_order_share": safe_fraction(changed_actions, periods),
            "simulated_transition_ratio_rollout_to_gp_base": safe_fraction(
                aggregate["gp_rollout"]["mean_simulated_transitions"],
                aggregate["gp_base_stock"]["mean_simulated_transitions"],
            ),
            "gp_marginal_loss_final_above_initial": sum(
                end > start for start, end in gp_losses.values()
            ),
            "gp_loss_paths_checked": len(gp_losses),
            "gp_optimizer_convergence_not_established": True,
            "first_receivable_window_saving_periods": [
                config["lead_time"],
                min(2 * config["lead_time"], plan["jobs"][0]["horizon"]) - 1,
            ],
            "first_receivable_window_cost_saving": arrival_window_saving,
            "first_receivable_window_holding_cost_saving": (
                arrival_window_holding_saving
            ),
            "later_window_cost_saving": later_window_saving,
            "ending_stock_before_receipt_gp_base_sum": terminal_gp_stock,
            "ending_stock_before_receipt_gp_rollout_sum": terminal_rollout_stock,
        },
        "data_diagnostics": {
            "distinct_development_series": len(series),
            "unique_28day_requests": total_requests,
            "top_two_series_request_share": safe_fraction(
                sum(sales_by_series[s] for s in sorted_series[:2]),
                total_requests,
            ),
            "top_two_series_gp_rollout_cost_share": safe_fraction(
                top2_rollout_cost, gp_rollout_total
            ),
            "series_with_at_most_11_requests": sum(
                v <= 11 for v in sales_by_series.values()
            ),
            "series_with_at_least_20_zero_history_days_of_28": sum(
                h["zero_days"] >= 20 for h in histories28
            ),
            "unavoidable_initial_shortage_cost_across_all_budgets": (startup_cost),
            "unavoidable_cost_share_by_method": {
                m: safe_fraction(startup_cost, aggregate[m]["total_cost"])
                for m in METHODS
            },
            "request_counts_by_series_private": sales_by_series,
            "historical_profiles_by_series_private": {
                s: {str(b): history[s, origin, b] for b in budgets} for s in series
            },
        },
        "series_private": {
            s: {
                "future_requests": sales_by_series[s],
                "cost_by_method_and_budget": {
                    m: {str(b): by_case[s, b, m]["total_cost"] for b in budgets}
                    for m in METHODS
                },
                "gp_rollout_minus_gp_base_stock": {
                    str(b): by_case[s, b, "gp_rollout"]["total_cost"]
                    - by_case[s, b, "gp_base_stock"]["total_cost"]
                    for b in budgets
                },
            }
            for s in series
        },
        "warnings": [
            "A single prechosen development origin and seed cannot demonstrate "
            "population superiority, coverage, statistical significance "
            "or EJOR novelty.",
            "Four nested historical budgets share the same 28-day future window: "
            "48 method pairs are NOT 48 independent statistical units.",
            "Cross-series dependency and store/item clustering are not modeled.",
            "Retail sales are only exogenous request proxies, NOT uncensored demand.",
            "Zero stock plus positive lead time yields unavoidable initial "
            "lost demand.",
            "High-volume series dominate pooled costs and fill-rate ratios.",
            "More old history changes recency and time-feature scaling together "
            "with sample size; no noninferiority inference is justified.",
            "GP + rollout receives substantially more synthetic decision computation "
            "than the GP base-stock policy.",
            "No final holdout is read; no method is fitted or scored anew.",
        ],
    }


def public_report(audit: dict) -> dict:
    """Keep item-level analysis local; return aggregate-only reproducible facts."""
    result = {k: v for k, v in audit.items() if k not in ("series_private",)}
    result["data_diagnostics"] = {
        k: v for k, v in audit["data_diagnostics"].items() if not k.endswith("_private")
    }
    result["paired_vs_gp_rollout"] = {
        name: {k: v for k, v in item.items() if k != "series_average_deltas"}
        for name, item in audit["paired_vs_gp_rollout"].items()
    }
    return result
