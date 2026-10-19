"""Adversarial, synthetic-only regressions for the M4b independent review.

Never opens M5, runs a baseline job, or touches original run outputs.
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
from types import SimpleNamespace
from unittest.mock import patch

from inventory_ejor.baselines.audit_checks import (
    bound_wrapper,
    checked_leaf,
    evaluate_job,
    independent_calendar_replay,
    policy_counts,
    reconstructed_ledger,
)
from inventory_ejor.baselines.planning import sha_file
from inventory_ejor.data.budgets import SourcePolicy, access, ledger, validate_ledger
from inventory_ejor.data.contracts import History, Observation, Window
from inventory_ejor.data.embargo import validate_nonadaptive_origin_embargo


class IndependentReviewRegressionTests(unittest.TestCase):
    def test_final_history_embargo_not_merely_disjoint_outcomes(self):
        # These origins have distinct outcomes, but second history includes
        # all first outcomes. This was mistakenly allowed by SplitPlan alone.
        with self.assertRaisesRegex(ValueError, "embargo"):
            validate_nonadaptive_origin_embargo(
                (1737, 1765), largest_history=224, horizon=28
            )
        # Two disjoint 224+28 context/outcome blocks in candidate final span.
        validate_nonadaptive_origin_embargo(
            (1485, 1914), largest_history=224, horizon=28
        )

    def test_symlink_session_plan_refused_before_file_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = root / "results/runs/fake"
            session.mkdir(parents=True)
            outside = root.parent / ("m4b-outside-" + root.name + ".json")
            # Use an external pathname but NEVER touch the target of a symlink.
            (session / "plan.json").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "Symlink"):
                checked_leaf(root, session / "plan.json", "results/runs")
            with self.assertRaisesRegex(ValueError, "Symlink"):
                from inventory_ejor.baselines.analysis import analyze_session

                analyze_session(root, session)

    def test_real_evaluator_fingerprint_and_trace_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "data/processed/fake"
            folder.mkdir(parents=True)
            evaluator = folder / "evaluation.json"
            data = {
                "S@5": {
                    "dataset": "D",
                    "series": "S",
                    "window": {"start": 5, "stop": 7},
                    "observations": [
                        {"day": 5, "sales": 2},
                        {"day": 6, "sales": 0},
                    ],
                }
            }
            evaluator.write_text(json.dumps(data), encoding="utf-8")
            job = {
                "dataset_version": "D",
                "series": "S",
                "origin": 5,
                "horizon": 2,
                "evaluation_token": "S@5",
                "evaluator_file": "data/processed/fake/evaluation.json",
                "evaluator_sha256": sha_file(evaluator),
            }
            trace = [
                {"day": 5, "observed_sales_as_requests": 2},
                {"day": 6, "observed_sales_as_requests": 0},
            ]
            cache = {}
            evaluate_job(root, job, trace, cache)
            changed_trace = [dict(row) for row in trace]
            changed_trace[1]["observed_sales_as_requests"] = 1
            with self.assertRaisesRegex(ValueError, "replay requests"):
                evaluate_job(root, job, changed_trace, cache)

            # Same expected checksum but different evaluator contents is rejected.
            data["S@5"]["observations"][0]["sales"] = 3
            evaluator.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                evaluate_job(root, job, trace, {})

    def test_ledger_reconstruction_rejects_fake_gpu_compute_and_access(self):
        origin = 6
        first = date(2011, 1, 29)
        observations = tuple(
            Observation(
                day=t, date=(first + timedelta(days=t - 1)).isoformat(), sales=t
            )
            for t in range(2, 6)
        )
        history = History("D", "S", origin, observations)
        initial_ledger = ledger(history, "m3_preparation_only", ("weekday",))
        scenario = {"lead_time": 2, "max_order": 3}
        config = {
            "scenario": scenario,
            "base_stock_levels": [0, 1],
            "sampling": {"tuning_paths": 8, "decision_paths": 4},
            "resources": {"job_timeout_seconds": 300},
        }
        job = {
            "id": "sample",
            "method": "gp_rollout",
            "device_kind": "gpu",
            "series": "S",
            "origin": origin,
            "budget": 4,
            "seed": 0,
            "horizon": 4,
            "dataset_version": "D",
            "learner_file": "data/processed/fake/learner.json",
            "learner_sha256": "f" * 64,
            "history_ledger": initial_ledger,
            "source_policies": [
                {
                    "dataset": "D",
                    "first_date": "2011-01-29",
                    "allowed": [{"start": 1, "stop": 6}],
                    "forbidden_outcomes": [],
                }
            ],
        }
        effort = policy_counts(config, job)
        self.assertEqual(
            effort,
            {
                "synthetic_transitions": 176,
                "optimization_trials": 10,
                "simulated_paths": 16,
            },
        )
        expected = copy.deepcopy(initial_ledger)
        expected["method"] = "gp_rollout"
        expected["access"]["demand_model_fitting"] = [access(history)]
        expected["access"]["hyperparameter_optimization"] = [access(history)]
        expected["compute_allowance"] = {
            "cpu_seconds": 300,
            "memory_mb": 8192,
            "gpu": 1,
        }
        expected["synthetic_transitions"] = 176
        expected["optimization_trials"] = 10
        policy = SourcePolicy("D", "2011-01-29", (Window(1, 6),), ())
        validated = validate_ledger(expected, (policy,), history)
        seed = int.from_bytes(hashlib.sha256(b"S:6:4:0").digest()[:4], "big") % (
            2**31 - 10000
        )
        result = {
            "information_ledger": expected,
            "validated_information_counts": json.loads(json.dumps(validated)),
            "simulated_paths": 16,
            "effective_seed": seed,
        }
        with (
            patch(
                "inventory_ejor.baselines.audit_checks.checked_leaf",
                return_value=Path("/fake"),
            ),
            patch(
                "inventory_ejor.baselines.audit_checks.load_learner",
                return_value=SimpleNamespace(history=history),
            ),
        ):
            actual, counted = reconstructed_ledger(
                Path("/fake"), {"config": config}, job, result
            )
            self.assertEqual(actual, observations)
            self.assertEqual(counted, effort)
            changed = copy.deepcopy(result)
            changed["information_ledger"]["synthetic_transitions"] = 1
            with self.assertRaisesRegex(ValueError, "ledger disagrees"):
                reconstructed_ledger(Path("/fake"), {"config": config}, job, changed)
            changed = copy.deepcopy(result)
            changed["information_ledger"]["access"]["per_series_history"] = []
            with self.assertRaisesRegex(ValueError, "ledger disagrees"):
                reconstructed_ledger(Path("/fake"), {"config": config}, job, changed)
            changed = copy.deepcopy(result)
            changed["validated_information_counts"]["unique_real_observations"] = 1
            with self.assertRaisesRegex(ValueError, "information counts"):
                reconstructed_ledger(Path("/fake"), {"config": config}, job, changed)

    def test_wrapper_is_uniquely_bound_to_original_job(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = root / "results/runs/test"
            session.mkdir(parents=True)
            path = session / "manifest.json"
            command = [
                sys.executable,
                str(root / "scripts/baseline_worker.py"),
                "--plan",
                str(session / "plan.json"),
                "--approval",
                str(session / "approval.json"),
                "--job-index",
                "3",
                "--output",
                "results/runs/test/abc",
            ]
            manifest = {
                "command": command,
                "status": "succeeded",
                "exit_code": 0,
                "kind": "pilot",
                "clean_source": True,
                "git_status_before": "",
                "git_status_after": "",
                "source_unchanged": True,
                "source_commit": "sha",
                "source_commit_after": "sha",
                "seed": 0,
                "cwd": str(root),
                "config_sha256": "conf",
                "config_path": str(root / "config.json"),
                "data_manifest": {
                    "path": str(root / "data/processed/manifest.json"),
                    "sha256": "data",
                },
                "timeout_seconds": 300,
            }
            path.write_text(json.dumps(manifest), encoding="utf-8")
            entry = {
                "wrapper_manifest": "results/runs/test/manifest.json",
                "wrapper_manifest_sha256": sha_file(path),
                "exit_code": 0,
                "output": "results/runs/test/abc",
            }
            plan = {
                "git": {"commit": "sha"},
                "config_path": "config.json",
                "config_sha256": "conf",
                "bundle_manifest": "data/processed/manifest.json",
                "bundle_manifest_sha256": "data",
                "config": {"resources": {"job_timeout_seconds": 300}},
            }
            used = set()
            bound_wrapper(root, session, plan, 3, {"seed": 0}, entry, used)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                bound_wrapper(root, session, plan, 3, {"seed": 0}, entry, used)
            with self.assertRaisesRegex(ValueError, "does not belong"):
                bound_wrapper(root, session, plan, 4, {"seed": 0}, entry, set())

    def test_calendar_oracle_verifies_terminal_and_transient_costs(self):
        scenario = {
            "lead_time": 2,
            "max_order": 2,
            "initial_on_hand": 0,
            "initial_pipeline": [0],
            "costs": {
                "holding": 1,
                "lost_sales": 10,
                "variable_order": 0,
                "fixed_order": 0,
            },
            "additional_terminal_value": 0,
        }
        trace = [
            dict(
                period=0,
                day=40,
                on_hand=0,
                pipeline=[0],
                order=2,
                observed_sales_as_requests=1,
                fulfilled=0,
                lost_units=1,
                cost=10,
            ),
            dict(
                period=1,
                day=41,
                on_hand=0,
                pipeline=[2],
                order=1,
                observed_sales_as_requests=0,
                fulfilled=0,
                lost_units=0,
                cost=0,
            ),
            dict(
                period=2,
                day=42,
                on_hand=2,
                pipeline=[1],
                order=0,
                observed_sales_as_requests=1,
                fulfilled=1,
                lost_units=0,
                cost=1,
            ),
            dict(
                period=3,
                day=43,
                on_hand=2,
                pipeline=[0],
                order=0,
                observed_sales_as_requests=2,
                fulfilled=2,
                lost_units=0,
                cost=0,
            ),
        ]
        result = {
            "total_cost": 11,
            "cost_components": {
                "holding": 1,
                "lost_sales": 10,
                "variable_order": 0,
                "fixed_order": 0,
            },
            "terminal": {
                "ending_stock_before_receipt": 0,
                "outstanding_receipts": [0, 0],
                "additional_value": 0,
            },
        }
        job = {"origin": 40, "horizon": 4}
        demands, supplied, pieces = independent_calendar_replay(
            scenario, job, trace, result
        )
        self.assertEqual((demands, supplied), (4, 3))
        self.assertEqual(pieces["lost_sales"], 10)
        altered = copy.deepcopy(result)
        altered["terminal"]["ending_stock_before_receipt"] = 99
        with self.assertRaisesRegex(ValueError, "Terminal"):
            independent_calendar_replay(scenario, job, trace, altered)
        altered = copy.deepcopy(result)
        altered["cost_components"]["holding"] = 0
        with self.assertRaisesRegex(ValueError, "components"):
            independent_calendar_replay(scenario, job, trace, altered)


if __name__ == "__main__":
    unittest.main()
