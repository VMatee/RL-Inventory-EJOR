"""End-to-end synthetic M4b session, including admitted corruption.

All artifacts are generated inside an isolated TemporaryDirectory; no M5 raw,
prepared, test, or original run data are read. No actual GPU or model is run.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from inventory_ejor.baselines.analysis import analyze_session
from inventory_ejor.baselines.audit_checks import policy_counts
from inventory_ejor.baselines.planning import digest, sha_file
from inventory_ejor.baselines.reporting import summarize_session
from inventory_ejor.data.budgets import SourcePolicy, access, ledger, validate_ledger
from inventory_ejor.data.contracts import (
    History,
    Observation,
    Window,
    fit_normalization,
)
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


def save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def make_complete_synthetic_session(root, *, zero_evaluation=False):
    """Fabricate a fully provenance-bound 16-job saved session, no training."""
    session = root / "results/runs/synthetic-test"
    session.mkdir(parents=True)
    dataset = root / "data/processed/synthetic"
    dataset.mkdir(parents=True)
    config_dir = root / "experiments/configs"
    config_dir.mkdir(parents=True)
    t0 = date(2011, 1, 29)
    origin, horizon = 225, 4
    days = [0, 0, 0, 0] if zero_evaluation else [0, 2, 1, 3]
    evaluator = dataset / "evaluation.json"
    save(
        evaluator,
        {
            "S@225": {
                "dataset": "D",
                "series": "S",
                "window": {"start": origin, "stop": origin + horizon},
                "observations": [
                    {"day": origin + t, "sales": value} for t, value in enumerate(days)
                ],
            }
        },
    )
    config = {
        "purpose": "development_preview_not_publication",
        "methods": list(METHODS),
        "budgets": list(BUDGETS),
        "seeds": [0],
        "scenario": {
            "lead_time": 2,
            "max_order": 3,
            "initial_on_hand": 0,
            "initial_pipeline": [0],
            "costs": {
                "holding": 1,
                "lost_sales": 10,
                "fixed_order": 0,
                "variable_order": 0,
            },
            "additional_terminal_value": 0,
        },
        "base_stock_levels": [0, 1, 2],
        "sampling": {"tuning_paths": 3, "decision_paths": 2},
        "gp": {"steps": 2},
        "resources": {
            "gpu_ids": [0, 1, 2, 3],
            "job_timeout_seconds": 300,
        },
    }
    config_file = config_dir / "synthetic.json"
    save(config_file, config)
    manifest_file = dataset / "manifest.json"
    save(manifest_file, {"synthetic": True, "never_a_real_M5_result": True})
    policies = [
        {
            "dataset": "D",
            "first_date": "2011-01-29",
            "allowed": [{"start": 1, "stop": origin}],
            "forbidden_outcomes": [],
        }
    ]
    policy = SourcePolicy("D", "2011-01-29", (Window(1, origin),), ())
    inventory_config = InventoryConfig(
        2,
        horizon,
        3,
        CostParameters(holding=1, lost_sales=10, fixed_order=0, variable_order=0),
    )
    jobs = []
    artifacts = {}
    for n in BUDGETS:
        sequence = tuple(
            Observation(
                day=t,
                date=(t0 + timedelta(days=t - 1)).isoformat(),
                sales=t % 3,
            )
            for t in range(origin - n, origin)
        )
        hist = History("D", "S", origin, sequence)
        normalization = fit_normalization(hist, hist.window)
        learner = dataset / f"learner-{n}.json"
        save(
            learner,
            {
                "history": {
                    "dataset": "D",
                    "series": "S",
                    "origin": origin,
                    "observations": [
                        {"day": o.day, "date": o.date, "sales": o.sales}
                        for o in sequence
                    ],
                },
                "normalization": {
                    "mean": normalization.mean,
                    "scale": normalization.scale,
                    "fitted_days": list(normalization.fitted_days),
                },
                "features": [],
            },
        )
        artifacts[n] = (learner, hist)
        for method in METHODS:
            job_id = f"synthetic-{n}-{method}"
            jobs.append(
                {
                    "id": job_id,
                    "series": "S",
                    "origin": origin,
                    "budget": n,
                    "method": method,
                    "seed": 0,
                    "horizon": horizon,
                    "device_kind": "gpu" if method.startswith("gp_") else "cpu",
                    "learner_file": str(learner.relative_to(root)),
                    "learner_sha256": sha_file(learner),
                    "evaluator_file": str(evaluator.relative_to(root)),
                    "evaluator_sha256": sha_file(evaluator),
                    "evaluation_token": "S@225",
                    "dataset_version": "D",
                    "history_ledger": ledger(hist, "m3_preparation_only", ()),
                    "source_policies": policies,
                }
            )
    plan = {
        "jobs": jobs,
        "config": config,
        "config_path": str(config_file.relative_to(root)),
        "config_sha256": sha_file(config_file),
        "bundle_manifest": str(manifest_file.relative_to(root)),
        "bundle_manifest_sha256": sha_file(manifest_file),
        "data_source_fingerprint": "m5-sha256:synthetic-unit-test-only",
        "git": {"commit": "synthetic-test-source"},
        "execution_sources": {"synthetic_fixture": "not_a_real_git_file"},
    }
    save(session / "plan.json", plan)
    save(
        session / "approval.json",
        {
            "approved": True,
            "allow_model_fitting": True,
            "allow_baseline_scoring": True,
            "allow_gpu": True,
            "numerical_validation_completed": True,
            "approved_by_owner": "synthetic-fixture-does-NOT-authorize-real-execution",
            "plan_sha256": digest(plan),
            "purpose": "development_preview_only",
        },
    )
    entries = []
    for idx, job in enumerate(jobs):
        model = job["method"]
        hist = artifacts[job["budget"]][1]
        compute = policy_counts(config, job)
        info = copy.deepcopy(job["history_ledger"])
        info["method"] = model
        info["access"]["demand_model_fitting"] = [access(hist)]
        if model.startswith("gp_"):
            info["access"]["hyperparameter_optimization"] = [access(hist)]
        info["compute_allowance"] = {
            "cpu_seconds": 300,
            "memory_mb": 8192,
            "gpu": 1 if job["device_kind"] == "gpu" else 0,
        }
        info["synthetic_transitions"] = compute["synthetic_transitions"]
        info["optimization_trials"] = compute["optimization_trials"]
        validated = validate_ledger(info, (policy,), hist)
        effective_seed = int.from_bytes(
            hashlib.sha256(f"S:{origin}:{job['budget']}:0".encode()).digest()[:4], "big"
        ) % (2**31 - 10000)
        state = InventoryState(0, (0,))
        trace = []
        costs = {
            "holding": 0.0,
            "lost_sales": 0.0,
            "variable_order": 0.0,
            "fixed_order": 0.0,
        }
        fulfilled = 0
        for t, demand in enumerate(days):
            order = (
                (2 if model == "gp_rollout" else 1)
                if t == 0 and not zero_evaluation
                else 0
            )
            step = transition(inventory_config, state, order, demand)
            trace.append(
                {
                    "period": t,
                    "day": origin + t,
                    "on_hand": state.on_hand,
                    "pipeline": list(state.pipeline),
                    "order": order,
                    "observed_sales_as_requests": demand,
                    "fulfilled": step.sales,
                    "lost_units": step.lost_units,
                    "cost": step.costs.total,
                }
            )
            for key in costs:
                costs[key] += getattr(step.costs, key)
            fulfilled += step.sales
            state = step.next_state
        output = session / job["id"]
        result = {
            "status": "completed_development_baseline_requires_review",
            "job": job["id"],
            "method": model,
            "series": "S",
            "origin": origin,
            "budget": job["budget"],
            "seed": 0,
            "effective_seed": effective_seed,
            "source_commit": "synthetic-test-source",
            "execution_source_hashes": plan["execution_sources"],
            "rl_training": False,
            "our_proposed_method": False,
            "total_cost": sum(costs.values()),
            "cost_components": costs,
            "fill_rate": (fulfilled / sum(days)) if sum(days) else None,
            "total_seconds": 0.01,
            "selected_base_stock": 1,
            "base_stock_grid_upper_boundary_selected": False,
            "order_cap_binding_periods": 0,
            "simulated_paths": compute["simulated_paths"],
            "information_ledger": info,
            "validated_information_counts": json.loads(json.dumps(validated)),
            "model": {"marginal_likelihood_losses": [1.4, 1.2]}
            if model.startswith("gp_")
            else {"kind": model},
            "tuning_model_costs_not_test_results": [1, 2, 3],
            "terminal": {
                "ending_stock_before_receipt": step.ending_on_hand,
                "outstanding_receipts": list(step.outstanding_after_order),
                "additional_value": 0,
            },
        }
        save(output / "result.json", result)
        save(output / "private_sales_replay.json", trace)
        wrap = {
            "command": [
                sys.executable,
                str(root / "scripts/baseline_worker.py"),
                "--plan",
                str(session / "plan.json"),
                "--approval",
                str(session / "approval.json"),
                "--job-index",
                str(idx),
                "--output",
                str(output.relative_to(root)),
            ],
            "status": "succeeded",
            "exit_code": 0,
            "kind": "pilot",
            "clean_source": True,
            "git_status_before": "",
            "git_status_after": "",
            "source_unchanged": True,
            "source_commit": "synthetic-test-source",
            "source_commit_after": "synthetic-test-source",
            "seed": 0,
            "cwd": str(root),
            "config_sha256": plan["config_sha256"],
            "config_path": str(config_file),
            "data_manifest": {
                "path": str(manifest_file),
                "sha256": plan["bundle_manifest_sha256"],
            },
            "timeout_seconds": 300,
        }
        wrapped_file = session / (job["id"] + ".manifest.json")
        save(wrapped_file, wrap)
        entries.append(
            {
                "job": job["id"],
                "output": str(output.relative_to(root)),
                "exit_code": 0,
                "device": job["device_kind"],
                "slot": idx % 4,
                "physical_gpu_uuid": f"GPU-synthetic{idx // 4}"
                if job["device_kind"] == "gpu"
                else None,
                "result_sha256": sha_file(output / "result.json"),
                "trace_sha256": sha_file(output / "private_sales_replay.json"),
                "wrapper_manifest": str(wrapped_file.relative_to(root)),
                "wrapper_manifest_sha256": sha_file(wrapped_file),
            }
        )
    save(
        session / "session_summary.json",
        {
            "status": "completed",
            "error": None,
            "source_commit": "synthetic-test-source",
            "scientific_acceptance": "development_only_not_publication",
            "jobs_requested": len(jobs),
            "jobs_finished": len(jobs),
            "runtime_seconds": 0.1,
            "entries": entries,
        },
    )
    summarize_session(root, session, write=True)
    return session


class SyntheticFullAuditTests(unittest.TestCase):
    def test_all_zero_future_costs_report_undefined_relative_ratios(self):
        # Historical learner sales remain positive while the FUTURE evaluation
        # has zero requests, stock, orders and cost for all compared policies.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = make_complete_synthetic_session(root, zero_evaluation=True)
            audit = analyze_session(root, session)
            self.assertEqual(audit["integrity"]["verified_jobs"], 16)
            self.assertEqual(audit["integrity"]["independent_m1_transitions"], 64)
            self.assertTrue(
                all(value["total_cost"] == 0 for value in audit["methods"].values())
            )
            for other in METHODS:
                if other == "gp_rollout":
                    continue
                self.assertIsNone(
                    audit["paired_vs_gp_rollout"][other][
                        "relative_pooled_cost_reduction"
                    ]
                )
                self.assertIsNone(
                    audit["paired_vs_gp_rollout_excluding_two_highest_request_series"][
                        other
                    ]
                )
                loo = audit["leave_one_series_relative_reduction_ranges"][other]
                self.assertIsNone(loo["min_relative_reduction"])
                self.assertIsNone(loo["max_relative_reduction"])
                self.assertEqual(loo["valid_omissions"], 0)
                self.assertEqual(loo["excluded_zero_denominator_omissions"], 0)
                equal = audit["equal_series_average_relative_improvement"][other]
                self.assertIsNone(equal["mean_relative_reduction"])
                self.assertIsNone(equal["median_relative_reduction"])
                self.assertEqual(equal["valid_series"], 0)
                self.assertEqual(equal["excluded_zero_denominator_series"], 1)

    def test_symlink_rejection_for_all_twelve_input_leaf_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = make_complete_synthetic_session(root)
            saved_plan = json.loads((session / "plan.json").read_text())
            first_job = saved_plan["jobs"][0]
            saved_summary = json.loads((session / "session_summary.json").read_text())
            first_entry = saved_summary["entries"][0]
            candidates = {
                "plan": session / "plan.json",
                "approval": session / "approval.json",
                "summary": session / "session_summary.json",
                "aggregate": session / "aggregate_summary.json",
                "csv": session / "baseline_results.csv",
                "result": root / first_entry["output"] / "result.json",
                "trace": (root / first_entry["output"] / "private_sales_replay.json"),
                "wrapper": root / first_entry["wrapper_manifest"],
                "evaluator": root / first_job["evaluator_file"],
                "learner": root / first_job["learner_file"],
                "configuration": root / saved_plan["config_path"],
                "bundle_manifest": root / saved_plan["bundle_manifest"],
            }
            self.assertEqual(len(candidates), 12)
            for label, leaf in candidates.items():
                with self.subTest(input_leaf=label):
                    # A symlink to the original valid bytes must still be
                    # rejected BEFORE it is read, not merely by SHA256 failure.
                    hidden_original = leaf.with_name(leaf.name + ".saved")
                    leaf.rename(hidden_original)
                    try:
                        leaf.symlink_to(hidden_original)
                        with self.assertRaisesRegex(ValueError, "Symlink/noncanonical"):
                            analyze_session(root, session)
                    finally:
                        leaf.unlink()
                        hidden_original.rename(leaf)
            self.assertEqual(
                analyze_session(root, session)["integrity"]["verified_jobs"], 16
            )

    def test_complete_synthetic_session_and_inmemory_defect_regressions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = make_complete_synthetic_session(root)
            analyzed = analyze_session(root, session)
            self.assertEqual(analyzed["integrity"]["verified_jobs"], 16)
            self.assertEqual(analyzed["integrity"]["independent_m1_transitions"], 64)
            summary_file = session / "session_summary.json"
            summary = json.loads(summary_file.read_text())
            corrupted = copy.deepcopy(summary)
            first, second = corrupted["entries"][:2]
            first["wrapper_manifest"] = second["wrapper_manifest"]
            first["wrapper_manifest_sha256"] = second["wrapper_manifest_sha256"]
            save(summary_file, corrupted)
            with self.assertRaisesRegex(ValueError, "does not belong|Duplicate"):
                analyze_session(root, session)
            save(summary_file, summary)

            # Full session, but one fraudulent ledger and refreshed digest.
            first = summary["entries"][0]
            result_file = root / first["output"] / "result.json"
            result = json.loads(result_file.read_text())
            corrupt = copy.deepcopy(result)
            corrupt["information_ledger"]["synthetic_transitions"] = 1
            save(result_file, corrupt)
            bad_summary = copy.deepcopy(summary)
            bad_summary["entries"][0]["result_sha256"] = sha_file(result_file)
            save(summary_file, bad_summary)
            with self.assertRaisesRegex(ValueError, "ledger disagrees"):
                analyze_session(root, session)
            save(result_file, result)
            save(summary_file, summary)

            # Forged terminal metadata, with an updated result checksum.
            corrupt = copy.deepcopy(result)
            corrupt["terminal"]["ending_stock_before_receipt"] = 999
            save(result_file, corrupt)
            bad_summary = copy.deepcopy(summary)
            bad_summary["entries"][0]["result_sha256"] = sha_file(result_file)
            save(summary_file, bad_summary)
            with self.assertRaisesRegex(ValueError, "Terminal"):
                analyze_session(root, session)
            save(result_file, result)
            save(summary_file, summary)

            # Evaluator changed but its pinned SHA256 was not updated.
            evaluator = root / "data/processed/synthetic/evaluation.json"
            original_eval = json.loads(evaluator.read_text())
            corrupt_eval = copy.deepcopy(original_eval)
            corrupt_eval["S@225"]["observations"][0]["sales"] = 999
            save(evaluator, corrupt_eval)
            with self.assertRaisesRegex(ValueError, "Evaluator input checksum"):
                analyze_session(root, session)
            save(evaluator, original_eval)
            self.assertEqual(
                analyze_session(root, session)["integrity"]["verified_jobs"], 16
            )
            # All modifications were confined to an isolated TemporaryDirectory.


if __name__ == "__main__":
    unittest.main()
