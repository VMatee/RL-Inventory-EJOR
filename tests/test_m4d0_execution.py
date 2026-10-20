"""Synthetic-only M4d-0 reference execution, evidence, and boundary attacks.

No M5/Favorita files, GP fitting, RL training, CUDA or actual evaluation runs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_m4c_firewall import MemorySource, configuration, synthetic_records

from inventory_ejor.data.evidence import EvidenceStore
from inventory_ejor.data.m4d0_audit import verify_synthetic_reference_trace
from inventory_ejor.data.m4d0_execution import (
    METHOD,
    PrivateExecutionStore,
    execute_synthetic_reference,
    execution_approval_template,
    publish_learner_only_plan,
    scenario_contract,
    score_synthetic_reference,
)
from inventory_ejor.data.m4d0_io import (
    project_naive_preparation_io,
    require_preparation_budget,
)
from inventory_ejor.data.provenance import fingerprint
from inventory_ejor.data.releases import release_template
from inventory_ejor.data.staged import (
    prepare_evaluation,
    prepare_learner,
    select_cohort,
)

M5_BYTE_SIZES_METADATA_ONLY = {
    "calendar.csv": 103_469,
    "sales_train_validation.csv": 120_007_726,
    "sales_train_evaluation.csv": 121_736_518,
    "sell_prices.csv": 203_395_785,
    "sample_submission.csv": 5_228_786,
}


def tiny_scenario(*, stock=0, lead=2, horizon=2, holding=1.0):
    return {
        "lead_time": lead,
        "horizon": horizon,
        "max_order": 5,
        "initial_on_hand": stock,
        "initial_pipeline": [0] * (lead - 1),
        "costs": {
            "holding": holding,
            "lost_sales": 10.0,
            "variable_order": 0.1,
            "fixed_order": 1.0,
        },
        "additional_terminal_value": 0,
    }


class M4d0ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="m4d0-private-synthetic-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / "evidence").mkdir()
        (root / "private").mkdir(mode=0o700)
        self.evidence = EvidenceStore(root / "evidence")
        self.private = PrivateExecutionStore(root / "private")
        self.config = configuration()
        self.freeze, _, _ = synthetic_records(self.config)
        self.catalog = ("A", "B", "C")
        self.series = select_cohort(self.config, self.catalog)[0]
        self.source = MemorySource()
        self.scenario = tiny_scenario()
        self.history_release = self.release("learner_history")
        self.eval_release = self.release("evaluation_outcomes")

    def release(self, capability):
        release = release_template(
            self.config,
            "development",
            5,
            2 if capability == "learner_history" else None,
            capability,
            fingerprint(list(select_cohort(self.config, self.catalog))),
        )
        release.update(
            approved=True,
            approved_by_owner="SYNTHETIC-TEST-ONLY",
            decision_record="CPU synthetic fixture only; never M5",
            freeze_sha256=fingerprint(self.freeze),
        )
        return release

    def prepare_history(self):
        return prepare_learner(
            self.config,
            self.freeze,
            self.history_release,
            catalog=self.catalog,
            series=self.series,
            phase="development",
            origin=5,
            budget=2,
            source=self.source,
            evidence=self.evidence,
        )

    def publish(self, view=None, receipt=None, **overrides):
        if view is None or receipt is None:
            view, receipt = self.prepare_history()
        values = dict(
            private_store=self.private,
            evidence=self.evidence,
            config=self.config,
            freeze=self.freeze,
            release=self.history_release,
            catalog=self.catalog,
            view=view,
            receipt=receipt,
            phase="development",
            series=self.series,
            origin=5,
            budget=2,
            scenario=self.scenario,
            seed=0,
        )
        values.update(overrides)
        return publish_learner_only_plan(**values)

    def approval(self, plan_sha):
        approval = execution_approval_template(plan_sha)
        approval.update(
            approved=True,
            approved_by_owner="SYNTHETIC-TEST-ONLY",
            decision_record="synthetic CPU ref execution, no external data",
        )
        return approval

    def evaluate(self):
        return prepare_evaluation(
            self.config,
            self.freeze,
            self.eval_release,
            catalog=self.catalog,
            series=self.series,
            phase="development",
            origin=5,
            source=self.source,
            evidence=self.evidence,
        )

    def score(self, plan_sha, fit_sha, approval, targets=None, receipt=None, **changes):
        if targets is None or receipt is None:
            targets, receipt = self.evaluate()
        arguments = dict(
            private_store=self.private,
            evidence=self.evidence,
            plan_digest=plan_sha,
            fit_digest=fit_sha,
            approval=approval,
            config=self.config,
            freeze=self.freeze,
            evaluation_release=self.eval_release,
            catalog=self.catalog,
            targets=targets,
            scorer_receipt=receipt,
        )
        arguments.update(changes)
        return score_synthetic_reference(**arguments)

    def test_full_synthetic_lifecycle_with_separate_scorer_release(self):
        view, receipt = self.prepare_history()
        self.assertEqual(self.source.calls, [("history", self.series, 3, 5)])
        plan_sha = self.publish(view, receipt)
        plan = self.private.read(plan_sha, kind="synthetic_reference_execution_plan")
        self.assertEqual(plan["method"], METHOD)
        self.assertNotIn("evaluator", json.dumps(plan))
        self.assertNotIn("sales_train", json.dumps(plan))
        self.assertEqual(self.source.calls, [("history", self.series, 3, 5)])
        approval = self.approval(plan_sha)
        with patch.object(self.source, "read_evaluation", side_effect=AssertionError):
            fit_sha = execute_synthetic_reference(self.private, plan_sha, approval)
        fit = self.private.read(fit_sha, kind="synthetic_reference_fit_result")
        self.assertEqual(fit["real_history_observations"], 2)
        self.assertEqual(fit["optimizer_steps"], 0)
        self.assertFalse(fit["trained_gp"] or fit["trained_rl"])
        self.assertEqual(self.source.calls, [("history", self.series, 3, 5)])
        targets, outcome_receipt = self.evaluate()
        self.assertEqual(self.source.calls[-1], ("evaluation", self.series, 5, 7))
        score_sha = self.score(plan_sha, fit_sha, approval, targets, outcome_receipt)
        evidence = self.private.read(
            score_sha, kind="synthetic_reference_score_evidence"
        )
        self.assertEqual(evidence["simulation_periods"], 2)
        self.assertEqual(evidence["status"], "synthetic_only_not_retail_evidence")
        self.assertEqual(
            evidence["total_cost"], sum(evidence["cost_components"].values())
        )
        self.assertIsNotNone(
            self.private.read(
                evidence["trace_sha256"], kind="synthetic_private_scoring_trace"
            )
        )
        self.assertEqual(
            score_sha, self.score(plan_sha, fit_sha, approval, targets, outcome_receipt)
        )
        verified = verify_synthetic_reference_trace(
            self.private,
            plan_sha,
            fit_sha,
            score_sha,
            targets,
            evidence=self.evidence,
            config=self.config,
            freeze=self.freeze,
            catalog=self.catalog,
        )
        self.assertEqual(verified["status"], "independent_synthetic_replay_verified")
        self.assertEqual(verified["periods"], 2)
        self.assertEqual(
            fit_sha, execute_synthetic_reference(self.private, plan_sha, approval)
        )

    def test_positive_order_pipeline_and_horizon_cutoff_replayed(self):
        # Longer synthetic-only phase geometry to exercise actual lead-time
        # receipts and nonzero orders, not just horizon <= L no-action cases.
        self.config["horizon"] = 4
        self.config["phases"] = [
            {"role": "development", "start": 1, "stop": 9, "origins": [5]},
            {"role": "calibration", "start": 9, "stop": 17, "origins": [13]},
            {"role": "validation", "start": 17, "stop": 25, "origins": [21]},
            {"role": "final_test", "start": 25, "stop": 41, "origins": [29, 37]},
        ]
        self.freeze, _, _ = synthetic_records(self.config)
        self.history_release = self.release("learner_history")
        self.eval_release = self.release("evaluation_outcomes")
        self.scenario = tiny_scenario(horizon=4, lead=2)
        plan_sha = self.publish()
        approval = self.approval(plan_sha)
        fit_sha = execute_synthetic_reference(self.private, plan_sha, approval)
        targets, receipt = self.evaluate()
        score_sha = self.score(plan_sha, fit_sha, approval, targets, receipt)
        evidence = self.private.read(
            score_sha, kind="synthetic_reference_score_evidence"
        )
        trace = self.private.read(
            evidence["trace_sha256"], kind="synthetic_private_scoring_trace"
        )["periods"]
        self.assertGreater(trace[0]["order"], 0)
        self.assertEqual(trace[2]["on_hand"], trace[0]["order"])
        self.assertEqual([t["order"] for t in trace[-2:]], [0, 0])
        self.assertGreater(evidence["total_cost"], 0)
        self.assertEqual(
            verify_synthetic_reference_trace(
                self.private,
                plan_sha,
                fit_sha,
                score_sha,
                targets,
                evidence=self.evidence,
                config=self.config,
                freeze=self.freeze,
                catalog=self.catalog,
            )["periods"],
            4,
        )

    def test_missing_or_cross_task_history_release_refused(self):
        view, receipt = self.prepare_history()
        changed = dict(receipt, release_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "receipt identity"):
            self.publish(view, changed)
        with self.assertRaises(ValueError):
            self.publish(view, receipt, origin=11)
        changed = dict(receipt, access_receipt_sha256="0" * 64)
        with self.assertRaises(ValueError):
            self.publish(view, changed)
        bad = copy.deepcopy(self.history_release)
        bad["capability"] = "evaluation_outcomes"
        with self.assertRaises(ValueError):
            self.publish(view, receipt, release=bad)

    def test_strict_execution_approval_and_code_pinning(self):
        plan_sha = self.publish()
        approval = execution_approval_template(plan_sha)
        with self.assertRaisesRegex(ValueError, "approval"):
            execute_synthetic_reference(self.private, plan_sha, approval)
        approved = self.approval(plan_sha)
        wrong = dict(approved, plan_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "approval"):
            execute_synthetic_reference(self.private, plan_sha, wrong)
        with patch(
            "inventory_ejor.data.m4d0_execution.source_hashes",
            return_value={"modified_module": "0" * 64},
        ):
            with self.assertRaisesRegex(ValueError, "code/runtime"):
                execute_synthetic_reference(self.private, plan_sha, approved)

    def test_execution_approval_must_be_persisted_before_scoring(self):
        plan_sha = self.publish()
        approval = self.approval(plan_sha)
        fit_sha = execute_synthetic_reference(self.private, plan_sha, approval)
        fit = self.private.read(fit_sha, kind="synthetic_reference_fit_result")
        digest = fit["execution_approval_sha256"]
        self.assertEqual(
            self.private.read(digest, kind="synthetic_reference_run_approval"),
            approval,
        )
        target, scorer_receipt = self.evaluate()
        receipt_file = self.private._path(digest)
        backed_up = receipt_file.with_suffix(".temporary")
        receipt_file.rename(backed_up)
        try:
            with self.assertRaisesRegex(ValueError, "Missing"):
                self.score(plan_sha, fit_sha, approval, target, scorer_receipt)
        finally:
            backed_up.rename(receipt_file)

    def test_private_artifact_tamper_and_learner_schema_refused(self):
        plan_sha = self.publish()
        plan = self.private.read(plan_sha, kind="synthetic_reference_execution_plan")
        p = self.private._path(plan["learner_sha256"])
        original = p.read_bytes()
        try:
            p.write_bytes(original + b"\n")
            with self.assertRaisesRegex(ValueError, "modified|noncanonical"):
                execute_synthetic_reference(
                    self.private, plan_sha, self.approval(plan_sha)
                )
        finally:
            p.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "symlink"):
            with tempfile.TemporaryDirectory() as d:
                file = self.private.root / ("0" * 64 + ".json")
                file.symlink_to(Path(d) / "arbitrary.json")
                self.private.read("0" * 64, kind="synthetic_reference_execution_plan")
        p = self.private._path(plan["learner_sha256"])
        self.assertEqual(
            hashlib.sha256(p.read_bytes()).hexdigest(), plan["learner_sha256"]
        )

    def test_no_real_data_or_preapproved_future_phase(self):
        view, receipt = self.prepare_history()
        real = copy.deepcopy(self.config)
        real["dataset_version"] = "m5-accuracy-zenodo-10203108-v1"
        with self.assertRaisesRegex(ValueError, "refuses real M5"):
            self.publish(view, receipt, config=real)
        with self.assertRaisesRegex(ValueError, "synthetic development only"):
            self.publish(view, receipt, phase="final_test")
        with self.assertRaisesRegex(ValueError, "Execution horizon"):
            self.publish(view, receipt, scenario=tiny_scenario(horizon=3))

    def test_scorer_requires_independent_release_and_pinned_fit(self):
        plan_sha = self.publish()
        approval = self.approval(plan_sha)
        fit_sha = execute_synthetic_reference(self.private, plan_sha, approval)
        targets, receipt = self.evaluate()
        bad = dict(self.eval_release, approved=False)
        with self.assertRaisesRegex(ValueError, "authorization"):
            self.score(
                plan_sha, fit_sha, approval, targets, receipt, evaluation_release=bad
            )
        wrong = dict(receipt, access_receipt_sha256="0" * 64)
        with self.assertRaises(ValueError):
            self.score(plan_sha, fit_sha, approval, targets, wrong)
        with self.assertRaises(ValueError):
            self.score("0" * 64, fit_sha, approval, targets, receipt)
        with self.assertRaisesRegex(ValueError, "match"):
            from inventory_ejor.data.contracts import EvaluationTargets, Window

            bad_targets = EvaluationTargets(
                self.config["dataset_version"],
                self.series,
                Window(5, 6),
                (targets.observations[0],),
            )
            self.score(plan_sha, fit_sha, approval, bad_targets, receipt)

    def test_scorer_receipt_persistence_failure_never_returns_score(self):
        plan_sha = self.publish()
        approval = self.approval(plan_sha)
        fit_sha = execute_synthetic_reference(self.private, plan_sha, approval)
        target, receipt = self.evaluate()
        before = set(self.private.root.iterdir())
        original_put = self.private.put

        def fail_score_evidence(obj):
            if obj.get("kind") == "synthetic_reference_score_evidence":
                raise OSError("Synthetic simulated disk fault at score persistence")
            return original_put(obj)

        with patch.object(self.private, "put", side_effect=fail_score_evidence):
            with self.assertRaisesRegex(OSError, "score persistence"):
                self.score(plan_sha, fit_sha, approval, target, receipt)
        # Trace may exist, but no score evidence is returned to a caller.
        self.assertTrue(set(self.private.root.iterdir()) >= before)

    def test_adversarial_rehashed_model_and_trace_detected(self):
        plan_sha = self.publish()
        approval = self.approval(plan_sha)
        fit_sha = execute_synthetic_reference(self.private, plan_sha, approval)
        targets, receipt = self.evaluate()
        score_sha = self.score(plan_sha, fit_sha, approval, targets, receipt)

        tampered_fit = copy.deepcopy(
            self.private.read(fit_sha, kind="synthetic_reference_fit_result")
        )
        tampered_fit["base_stock_target"] += 1
        forged_fit_sha = self.private.put(tampered_fit)
        with self.assertRaisesRegex(ValueError, "fabricated reference"):
            self.score(plan_sha, forged_fit_sha, approval, targets, receipt)

        score = copy.deepcopy(
            self.private.read(score_sha, kind="synthetic_reference_score_evidence")
        )
        trace = copy.deepcopy(
            self.private.read(
                score["trace_sha256"], kind="synthetic_private_scoring_trace"
            )
        )
        trace["periods"][0]["order"] += 1
        forged_trace_sha = self.private.put(trace)
        score["trace_sha256"] = forged_trace_sha
        forged_score_sha = self.private.put(score)
        with self.assertRaisesRegex(ValueError, "Saved action"):
            verify_synthetic_reference_trace(
                self.private,
                plan_sha,
                fit_sha,
                forged_score_sha,
                targets,
                evidence=self.evidence,
                config=self.config,
                freeze=self.freeze,
                catalog=self.catalog,
            )

    def test_zero_requests_and_nonzero_initial_stock(self):
        self.source.values.update({5: 0, 6: 0})
        self.scenario = tiny_scenario(stock=3)
        plan_sha = self.publish()
        approval = self.approval(plan_sha)
        fit_sha = execute_synthetic_reference(self.private, plan_sha, approval)
        score_sha = self.score(plan_sha, fit_sha, approval)
        record = self.private.read(score_sha, kind="synthetic_reference_score_evidence")
        self.assertIsNone(record["fill_rate"])
        self.assertEqual(record["requests"], 0)
        self.assertEqual(record["simulation_periods"], 2)

    def test_bad_scenario_and_root_location_rejected(self):
        for scenario in [
            tiny_scenario(lead=0),
            tiny_scenario(horizon=999),
            dict(tiny_scenario(), additional_terminal_value=100),
            dict(tiny_scenario(), initial_pipeline=[0, 0]),
        ]:
            with self.subTest(scenario=scenario):
                with self.assertRaises((ValueError, TypeError)):
                    scenario_contract(scenario)
        repo = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, "Git worktree"):
            PrivateExecutionStore(repo)


class M4d0IoTests(unittest.TestCase):
    def test_prespecified_m5_metadata_projection_and_hard_limit(self):
        from inventory_ejor.data.provenance import read_json

        config = read_json(
            (
                Path(__file__).resolve().parents[1]
                / "experiments/configs/m4c_protocol_candidate.json"
            ).read_bytes()
        )
        data = project_naive_preparation_io(config, M5_BYTE_SIZES_METADATA_ONLY)
        self.assertEqual(data["reader_calls"], 1120)
        self.assertEqual(data["histories"], 896)
        self.assertEqual(data["scorer_windows"], 224)
        self.assertEqual(data["logical_processed_bytes"], 1_145_518_701_600)
        with self.assertRaisesRegex(ValueError, "exceeds authorized"):
            require_preparation_budget(
                data,
                maximum_logical_bytes=8 * (2**30),
                config=config,
                input_file_bytes=M5_BYTE_SIZES_METADATA_ONLY,
            )
        self.assertIs(
            require_preparation_budget(
                data,
                maximum_logical_bytes=2 * (2**40),
                config=config,
                input_file_bytes=M5_BYTE_SIZES_METADATA_ONLY,
            ),
            data,
        )

    def test_projection_never_opens_raw_data(self):
        config = configuration()
        with patch("builtins.open", side_effect=AssertionError("data read")):
            estimate = project_naive_preparation_io(
                config, {k: 32 for k in M5_BYTE_SIZES_METADATA_ONLY}
            )
        self.assertEqual(estimate["reader_calls"], 2 * (2 + 1) * 5)
        with self.assertRaisesRegex(ValueError, "Expected the five"):
            project_naive_preparation_io(config, {"not_an_input": 1})
        with self.assertRaisesRegex(ValueError, "positive"):
            require_preparation_budget(
                estimate,
                maximum_logical_bytes=0,
                config=config,
                input_file_bytes={k: 32 for k in M5_BYTE_SIZES_METADATA_ONLY},
            )

    def test_cli_metadata_gate_fails_closed_without_reading_source(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="m4d0-sizes-metadata-") as temp:
            sizes = Path(temp) / "sizes.json"
            sizes.write_text(json.dumps(M5_BYTE_SIZES_METADATA_ONLY), encoding="utf-8")
            command = [
                sys.executable,
                "-B",
                "scripts/check_m4d0_io.py",
                "--config",
                "experiments/configs/m4c_protocol_candidate.json",
                "--sizes",
                str(sizes),
                "--max-logical-gib",
                "8",
            ]
            env = dict(
                os.environ, PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1"
            )
            refused = subprocess.run(
                command,
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(refused.returncode, 2, refused.stderr)
            report = json.loads(refused.stdout)
            self.assertFalse(report["within_explicit_budget"])
            self.assertFalse(report["source_observations_opened"])
            self.assertFalse(report["execution_authorized"])
            approved = subprocess.run(
                command[:-1] + ["2048"],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(approved.returncode, 0, approved.stderr)
            self.assertTrue(json.loads(approved.stdout)["within_explicit_budget"])


if __name__ == "__main__":
    unittest.main()
