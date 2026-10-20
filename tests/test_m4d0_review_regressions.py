"""PR #12 adversarial corrections. All artifacts are disposable synthetic data."""

from __future__ import annotations

import math
import os
import random
import stat
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import test_m4d0_execution as fixture
from test_m4c_firewall import MemorySource, configuration, synthetic_records

from inventory_ejor.data.m4d0_audit import verify_synthetic_reference_trace
from inventory_ejor.data.m4d0_execution import (
    exact_reference_target,
    execute_synthetic_reference,
    publish_learner_only_plan,
    score_synthetic_reference,
    source_hashes,
)
from inventory_ejor.data.m4d0_io import (
    project_naive_preparation_io,
    require_preparation_budget,
)
from inventory_ejor.data.m4d0_store import PrivateExecutionStore
from inventory_ejor.data.provenance import fingerprint
from inventory_ejor.data.releases import release_template
from inventory_ejor.data.staged import (
    prepare_evaluation,
    prepare_learner,
    select_cohort,
)


class ProvenanceRegressions(unittest.TestCase):
    def setUp(self):
        self.f = fixture.M4d0ReferenceTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        f = self.f
        self.plan = f.publish()
        self.approval = f.approval(self.plan)
        self.fit = execute_synthetic_reference(f.private, self.plan, self.approval)
        self.targets, self.receipt = f.evaluate()
        self.score = f.score(
            self.plan, self.fit, self.approval, self.targets, self.receipt
        )

    def audit(self, *, plan=None, fit=None, score=None):
        f = self.f
        return verify_synthetic_reference_trace(
            f.private,
            plan or self.plan,
            fit or self.fit,
            score or self.score,
            self.targets,
            evidence=f.evidence,
            config=f.config,
            freeze=f.freeze,
            catalog=f.catalog,
        )

    def relink(self, fit, approval=None):
        f = self.f
        if approval is not None:
            fit["execution_approval_sha256"] = f.private.put(approval)
        digest = f.private.put(fit)
        score = f.private.read(self.score)
        trace = f.private.read(score["trace_sha256"])
        trace["fit_sha256"] = digest
        score.update(
            fit_sha256=digest,
            trace_sha256=f.private.put(trace),
            execution_approval_sha256=fit["execution_approval_sha256"],
        )
        return digest, f.private.put(score)

    def test_valid_complete_audit_and_no_production_transition(self):
        with patch(
            "inventory_ejor.data.m4d0_execution.transition",
            side_effect=AssertionError("shared kernel"),
        ):
            result = self.audit()
        self.assertTrue(result["authorization_attestations_verified"])
        self.assertFalse(result["scientific_selection_execution_verified"])
        self.assertFalse(result["raw_observation_bytes_verified"])

    def test_audit_requires_authorization_context(self):
        with self.assertRaises(TypeError):
            verify_synthetic_reference_trace(
                self.f.private, self.plan, self.fit, self.score, self.targets
            )
        with self.assertRaises(ValueError):
            verify_synthetic_reference_trace(
                self.f.private,
                self.plan,
                self.fit,
                self.score,
                self.targets,
                evidence=None,
                config=self.f.config,
                freeze=self.f.freeze,
                catalog=self.f.catalog,
            )

    def test_rehashed_missing_evaluator_refs_and_false_score_claims_rejected(self):
        for field, value in (
            ("evaluation_release_sha256", "0" * 64),
            ("evaluation_receipt_sha256", "0" * 64),
            ("trained_gp", True),
            ("trained_rl", True),
            ("status", "actual_retail_evidence"),
            ("schema_version", True),
            ("simulation_periods", True),
            ("extra_claim", "retail savings"),
        ):
            score = self.f.private.read(self.score)
            score[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.audit(score=self.f.private.put(score))

    def test_rehashed_fit_dependencies_failed_status_and_flags_rejected(self):
        for field, value in (
            ("dependency_sha256s", {"unrelated": "0" * 64}),
            ("status", "failed_fit"),
            ("seed", 1),
            ("seed", False),
            ("trained_gp", True),
            ("trained_rl", True),
            ("optimizer_steps", 1),
            ("base_stock_target", 999),
            ("extra_claim", True),
        ):
            fit = self.f.private.read(self.fit)
            fit[field] = value
            badfit, badscore = self.relink(fit)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.audit(fit=badfit, score=badscore)
            with self.assertRaises(ValueError):
                self.f.score(
                    self.plan, badfit, self.approval, self.targets, self.receipt
                )

    def test_rehashed_malformed_approvals_rejected_by_scorer_and_audit(self):
        for field, value in (
            ("schema_version", 999),
            ("approved_by_owner", 42),
            ("decision_record", True),
            ("approved", 1),
            ("extra_claim", True),
        ):
            approval = dict(self.approval)
            approval[field] = value
            fit, score = self.relink(self.f.private.read(self.fit), approval)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.audit(fit=fit, score=score)
            with self.assertRaises(ValueError):
                self.f.score(self.plan, fit, approval, self.targets, self.receipt)

    def test_executor_scorer_audit_reject_same_invalid_relinked_plan(self):
        for field, value in (
            ("python", "0.0"),
            ("dependency_sha256s", {"unknown": "0" * 64}),
            ("runtime", {}),
            ("method", "wrong"),
            ("seed", True),
            ("initial_stock", 999),
            ("extra_claim", True),
        ):
            f = self.f
            plan = f.private.read(self.plan)
            plan[field] = value
            badplan = f.private.put(plan)
            approval = f.approval(badplan)
            f.private.put(approval)
            fit = f.private.read(self.fit)
            fit.update(
                plan_sha256=badplan, execution_approval_sha256=fingerprint(approval)
            )
            badfit = f.private.put(fit)
            score = f.private.read(self.score)
            trace = f.private.read(score["trace_sha256"])
            trace.update(plan_sha256=badplan, fit_sha256=badfit)
            score.update(
                plan_sha256=badplan,
                fit_sha256=badfit,
                trace_sha256=f.private.put(trace),
                execution_approval_sha256=fingerprint(approval),
            )
            badscore = f.private.put(score)
            with self.subTest(field=field), self.assertRaises(ValueError):
                execute_synthetic_reference(f.private, badplan, approval)
            with self.assertRaises(ValueError):
                f.score(badplan, badfit, approval, self.targets, self.receipt)
            with self.assertRaises(ValueError):
                self.audit(plan=badplan, fit=badfit, score=badscore)

    def test_actual_persisted_history_and_evaluator_evidence_required(self):
        f = self.f
        plan = f.private.read(self.plan)
        score = f.private.read(self.score)
        for digest in (
            plan["history_release_sha256"],
            plan["history_receipt_sha256"],
            score["evaluation_release_sha256"],
            score["evaluation_receipt_sha256"],
        ):
            path = f.evidence.root / (digest + ".json")
            backup = path.with_suffix(".backup")
            path.rename(backup)
            try:
                with self.subTest(digest=digest), self.assertRaises(ValueError):
                    self.audit()
            finally:
                backup.rename(path)

    def test_capability_swaps_and_receipt_type_aliases_rejected(self):
        f = self.f
        score = f.private.read(self.score)
        plan = f.private.read(self.plan)
        score["evaluation_receipt_sha256"] = plan["history_receipt_sha256"]
        with self.assertRaises(ValueError):
            self.audit(score=f.private.put(score))
        for key, value in (
            ("origin", True),
            ("budget", True),
            ("schema_version", True),
            ("extra_claim", 1),
        ):
            receipt = f.evidence.read(
                f.private.read(self.score)["evaluation_receipt_sha256"]
            )
            receipt[key] = value
            changed = f.private.read(self.score)
            changed["evaluation_receipt_sha256"] = f.evidence.put(receipt)
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.audit(score=f.private.put(changed))

    def test_rehashed_trace_extras_and_terminal_tampering_rejected(self):
        for attack in ("extra", "boolean", "terminal"):
            score = self.f.private.read(self.score)
            trace = self.f.private.read(score["trace_sha256"])
            if attack == "extra":
                trace["periods"][0]["unverified_claim"] = True
            elif attack == "boolean":
                trace["periods"][0]["order"] = False
            else:
                score["ending_pipeline"] = [7] * self.f.scenario["lead_time"]
            score["trace_sha256"] = self.f.private.put(trace)
            with self.subTest(attack=attack), self.assertRaises(ValueError):
                self.audit(score=self.f.private.put(score))

    def test_dependency_snapshot_includes_auditor_store_and_protocol(self):
        hashes = source_hashes()
        for name in (
            "data/m4d0_audit.py",
            "data/m4d0_store.py",
            "data/protocol.py",
            "data/budgets.py",
            "envs/__init__.py",
        ):
            self.assertIn("src/inventory_ejor/" + name, hashes)


class NumericalRegressions(unittest.TestCase):
    def setUp(self):
        self.f = fixture.M4d0ReferenceTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)

    def run_case(self, history, demands, scenario):
        f = self.f
        n, h = len(history), len(demands)
        cfg = configuration()
        width = n + h
        cfg.update(
            budgets=[n], horizon=h, source_window={"start": 1, "stop": 1 + 5 * width}
        )
        for i, phase in enumerate(cfg["phases"]):
            phase.update(
                start=1 + i * width,
                stop=1 + (i + 1) * width,
                origins=[1 + i * width + n],
            )
        cfg["phases"][-1]["stop"] += width
        cfg["phases"][-1]["origins"].append(1 + 4 * width + n)
        freeze, _, _ = synthetic_records(cfg)
        cohort = select_cohort(cfg, f.catalog)
        source = MemorySource()
        source.values = dict(enumerate([*history, *demands], 1))

        def release(cap, budget):
            r = release_template(
                cfg, "development", n + 1, budget, cap, fingerprint(list(cohort))
            )
            r.update(
                approved=True,
                approved_by_owner="SYNTHETIC ONLY",
                decision_record="synthetic:case",
                freeze_sha256=fingerprint(freeze),
            )
            return r

        hr, er = release("learner_history", n), release("evaluation_outcomes", None)
        view, receipt = prepare_learner(
            cfg,
            freeze,
            hr,
            catalog=f.catalog,
            series=f.series,
            phase="development",
            origin=n + 1,
            budget=n,
            source=source,
            evidence=f.evidence,
        )
        plan = publish_learner_only_plan(
            f.private,
            f.evidence,
            config=cfg,
            freeze=freeze,
            release=hr,
            catalog=f.catalog,
            view=view,
            receipt=receipt,
            phase="development",
            series=f.series,
            origin=n + 1,
            budget=n,
            scenario=scenario,
            seed=0,
        )
        approval = f.approval(plan)
        fit = execute_synthetic_reference(f.private, plan, approval)
        targets, receipt = prepare_evaluation(
            cfg,
            freeze,
            er,
            catalog=f.catalog,
            series=f.series,
            phase="development",
            origin=n + 1,
            source=source,
            evidence=f.evidence,
        )
        score = score_synthetic_reference(
            f.private,
            f.evidence,
            plan_digest=plan,
            fit_digest=fit,
            approval=approval,
            config=cfg,
            freeze=freeze,
            evaluation_release=er,
            catalog=f.catalog,
            targets=targets,
            scorer_receipt=receipt,
        )
        saved = f.private.read(score)
        checked = verify_synthetic_reference_trace(
            f.private,
            plan,
            fit,
            score,
            targets,
            evidence=f.evidence,
            config=cfg,
            freeze=freeze,
            catalog=f.catalog,
        )
        self.assertEqual(checked["total_cost"], saved["total_cost"])
        return (
            f.private.read(fit),
            saved,
            f.private.read(saved["trace_sha256"])["periods"],
        )

    @staticmethod
    def oracle(history, demands, scenario):
        # Test-only exact rational cost oracle; never calls production helpers.
        lead = scenario["lead_time"]
        h = len(demands)
        cap = scenario["max_order"]
        target = min(
            cap * (lead + 1),
            math.ceil(Fraction(sum(history) * (lead + 1), len(history))),
        )
        schedule = {j: q for j, q in enumerate(scenario["initial_pipeline"], 1)}
        stock = scenario["initial_on_hand"]
        orders = []
        total = Fraction(0)
        served = 0
        for t, demand in enumerate(demands):
            stock += schedule.pop(t, 0)
            position = stock + sum(q for day, q in schedule.items() if day > t)
            order = min(cap, max(0, target - position)) if t + lead < h else 0
            schedule[t + lead] = order
            orders.append(order)
            sales = min(stock, demand)
            served += sales
            stock -= sales
            c = scenario["costs"]
            total += (
                Fraction(str(c["holding"])) * stock
                + Fraction(str(c["lost_sales"])) * (demand - sales)
                + Fraction(str(c["variable_order"])) * order
                + (Fraction(str(c["fixed_order"])) if order else 0)
            )
        return (
            target,
            orders,
            float(total),
            stock,
            [schedule.get(h + j, 0) for j in range(lead)],
            served,
        )

    def test_exact_ceiling_all_budgets_leads_and_boundary_neighbors(self):
        for n in (1, 2, 28, 56, 112, 224, 3660):
            for lead in range(1, 11):
                for total in (
                    0,
                    1,
                    n - 1,
                    n,
                    n + 1,
                    116 * n // 28 - 1,
                    116 * n // 28,
                    116 * n // 28 + 1,
                ):
                    if total < 0:
                        continue
                    expected = min(
                        100 * (lead + 1), math.ceil(Fraction(total * (lead + 1), n))
                    )
                    self.assertEqual(
                        exact_reference_target(total, n, lead, 100), expected
                    )
        for args in (
            (True, 28, 6, 5),
            (116, False, 6, 5),
            (116, 28, True, 5),
            (116, 28, 6, True),
            (-1, 28, 6, 5),
            (1, 0, 6, 5),
            (2**53 + 1, 1, 6, 5),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                exact_reference_target(*args)

    def test_original_ceil_counterexample_cost_209_point_4(self):
        for n in (28, 56, 112, 224):
            scenario = fixture.tiny_scenario(stock=25, lead=6, horizon=8)
            history = [116 * (n // 28)] + [0] * (n - 1)
            demands = [0] * 8
            fit, score, trace = self.run_case(history, demands, scenario)
            self.assertEqual(fit["base_stock_target"], 29)
            self.assertEqual([r["order"] for r in trace], [4, 0, 0, 0, 0, 0, 0, 0])
            self.assertAlmostEqual(score["total_cost"], 209.4)
            self.assertEqual(self.oracle(history, demands, scenario)[0], 29)

    def test_original_terminal_pipeline_counterexample(self):
        scenario = fixture.tiny_scenario(lead=3, horizon=2)
        scenario["initial_pipeline"] = [4, 5]
        _, score, _ = self.run_case([0, 0], [0, 0], scenario)
        self.assertEqual(score["ending_stock"], 4)
        self.assertEqual(score["ending_pipeline"], [5, 0, 0])
        self.assertEqual(score["total_cost"], 4)

    def test_fixed_seed_full_lifecycles_against_fraction_arrival_oracle(self):
        rng = random.Random(20261020)
        for lead in range(1, 11):
            for horizon in range(1, 13):
                scenario = fixture.tiny_scenario(
                    stock=rng.randrange(11), lead=lead, horizon=horizon
                )
                scenario["initial_pipeline"] = [
                    rng.randrange(6) for _ in range(lead - 1)
                ]
                scenario["max_order"] = rng.randrange(9)
                history = [
                    rng.randrange(8) if rng.random() < 0.6 else 0
                    for _ in range(rng.randrange(1, 9))
                ]
                demands = [
                    rng.randrange(8) if rng.random() < 0.6 else 0
                    for _ in range(horizon)
                ]
                fit, score, trace = self.run_case(history, demands, scenario)
                target, orders, cost, stock, pipeline, served = self.oracle(
                    history, demands, scenario
                )
                with self.subTest(lead=lead, horizon=horizon):
                    self.assertEqual(fit["base_stock_target"], target)
                    self.assertEqual([r["order"] for r in trace], orders)
                    self.assertAlmostEqual(score["total_cost"], cost)
                    self.assertEqual(
                        (
                            score["ending_stock"],
                            score["ending_pipeline"],
                            score["fulfilled"],
                        ),
                        (stock, pipeline, served),
                    )


class DurableStoreRegressions(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="m4d0-atomic-regression-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.store = PrivateExecutionStore(self.root)
        self.value = {"kind": "synthetic-test", "numbers": [1, 2, 3]}

    def test_create_write_file_sync_and_publication_faults_leave_no_final(self):
        original_open, original_write = os.open, os.write
        calls = 0

        def bad_open(path, *args, **kwargs):
            if str(path).startswith(".pending-"):
                raise OSError("creation fault")
            return original_open(path, *args, **kwargs)

        def partial(fd, data):
            nonlocal calls
            calls += 1
            if calls == 1:
                return original_write(fd, data[:3])
            raise OSError("partial write fault")

        for function, effect in (
            ("open", bad_open),
            ("write", partial),
            ("write", lambda fd, data: 0),
            ("fsync", OSError("file sync fault")),
            ("link", OSError("publication fault")),
        ):
            with (
                self.subTest(function=function),
                patch(
                    "inventory_ejor.data.m4d0_store.os." + function, side_effect=effect
                ),
            ):
                with self.assertRaises(OSError):
                    self.store.put(self.value)
            self.assertEqual(list(self.root.iterdir()), [])
        digest = self.store.put(self.value)
        self.assertEqual(self.store.read(digest), self.value)

    def test_directory_sync_failure_and_retry_never_skip_synchronization(self):
        sync = os.fsync

        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("directory sync fault")
            return sync(fd)

        with patch(
            "inventory_ejor.data.m4d0_store.os.fsync", side_effect=fail_directory
        ):
            with self.assertRaisesRegex(OSError, "directory"):
                self.store.put(self.value)
        self.assertEqual(len(list(self.root.glob("*.json"))), 1)
        self.assertEqual(list(self.root.glob(".pending-*")), [])
        with patch(
            "inventory_ejor.data.m4d0_store.os.fsync",
            side_effect=OSError("retry sync fault"),
        ) as sync_spy:
            with self.assertRaisesRegex(OSError, "retry"):
                self.store.put(self.value)
            self.assertGreater(sync_spy.call_count, 0)
        with patch("inventory_ejor.data.m4d0_store.os.fsync", wraps=sync) as sync_spy:
            digest = self.store.put(self.value)
            self.assertEqual(sync_spy.call_count, 2)
        self.assertEqual(self.store.read(digest), self.value)

    def test_short_writes_complete_and_identical_artifact_is_resynchronized(self):
        write = os.write
        with patch(
            "inventory_ejor.data.m4d0_store.os.write",
            side_effect=lambda fd, data: write(fd, data[:3]),
        ):
            digest = self.store.put(self.value)
        self.assertEqual(self.store.read(digest), self.value)
        with patch("inventory_ejor.data.m4d0_store.os.fsync", wraps=os.fsync) as sync:
            self.assertEqual(self.store.put(self.value), digest)
            self.assertEqual(sync.call_count, 2)
        previous_mask = os.umask(0o777)
        try:
            restricted = self.store.put({"kind": "restrictive-umask"})
        finally:
            os.umask(previous_mask)
        self.assertEqual(
            stat.S_IMODE(self.store.file(restricted).stat().st_mode), 0o600
        )

    def test_identical_publication_race_is_validated_and_conflict_never_overwritten(
        self,
    ):
        link = os.link

        def concurrent(*args, **kwargs):
            link(*args, **kwargs)
            raise FileExistsError("concurrent identical publisher")

        with patch("inventory_ejor.data.m4d0_store.os.link", side_effect=concurrent):
            digest = self.store.put(self.value)
        self.assertEqual(self.store.read(digest), self.value)
        path = self.store.file(digest)
        path.write_bytes(b"{}")
        with self.assertRaises(ValueError):
            self.store.put(self.value)
        self.assertEqual(path.read_bytes(), b"{}")

    def test_root_permissions_and_worktree_invariants_rechecked(self):
        digest = self.store.put(self.value)
        self.root.chmod(0o755)
        try:
            for action in (
                lambda: self.store.put(self.value),
                lambda: self.store.read(digest),
                lambda: self.store.file(digest),
            ):
                with self.assertRaisesRegex(ValueError, "0700"):
                    action()
        finally:
            self.root.chmod(0o700)
        (self.root / ".git").write_text("synthetic worktree marker")
        with self.assertRaisesRegex(ValueError, "Git worktree"):
            self.store.put(self.value)

    def test_symlink_and_nonregular_file_rejected(self):
        path = self.root / (fingerprint(self.value) + ".json")
        target = self.root / "target"
        target.write_text("{}")
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.store.put(self.value)
        path.unlink()
        os.mkfifo(path, 0o600)
        with self.assertRaisesRegex(ValueError, "nonregular"):
            self.store.read(fingerprint(self.value))

    def test_failed_score_sync_and_retry_counterexample(self):
        f = fixture.M4d0ReferenceTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        plan = f.publish()
        approval = f.approval(plan)
        fit = execute_synthetic_reference(f.private, plan, approval)
        targets, receipt = f.evaluate()
        sync = os.fsync

        def fail_score_file(fd):
            if stat.S_ISREG(os.fstat(fd).st_mode):
                item = __import__("json").loads(
                    Path("/proc/self/fd/" + str(fd)).read_bytes()
                )
                if item.get("kind") == "synthetic_reference_score_evidence":
                    raise OSError("score fsync fault")
            return sync(fd)

        with patch(
            "inventory_ejor.data.m4d0_store.os.fsync", side_effect=fail_score_file
        ):
            with self.assertRaises(OSError):
                f.score(plan, fit, approval, targets, receipt)
        with patch(
            "inventory_ejor.data.m4d0_store.os.fsync",
            side_effect=OSError("retry fsync fault"),
        ) as spy:
            with self.assertRaises(OSError):
                f.score(plan, fit, approval, targets, receipt)
            self.assertGreater(spy.call_count, 0)
        self.assertEqual(
            f.private.read(f.score(plan, fit, approval, targets, receipt))["status"],
            "synthetic_only_not_retail_evidence",
        )


class IoProjectionRegressions(unittest.TestCase):
    def test_forged_or_stale_projection_rejected_against_recomputed_context(self):
        cfg = configuration()
        sizes = {name: 32 for name in fixture.M5_BYTE_SIZES_METADATA_ONLY}
        good = project_naive_preparation_io(cfg, sizes)
        for bad in (
            {"kind": "m4d0_metadata_io_projection", "logical_processed_bytes": 0},
            dict(good, logical_processed_bytes=0),
            dict(good, schema_version=True),
        ):
            with self.assertRaises(ValueError):
                require_preparation_budget(
                    bad, maximum_logical_bytes=2**30, config=cfg, input_file_bytes=sizes
                )
        with (
            patch("builtins.open", side_effect=AssertionError("data IO")),
            patch.object(Path, "open", side_effect=AssertionError("data IO")),
        ):
            self.assertEqual(
                require_preparation_budget(
                    good,
                    maximum_logical_bytes=2**30,
                    config=cfg,
                    input_file_bytes=sizes,
                ),
                good,
            )
        changed = dict(sizes)
        changed["calendar.csv"] += 1
        with self.assertRaises(ValueError):
            require_preparation_budget(
                good, maximum_logical_bytes=2**30, config=cfg, input_file_bytes=changed
            )


if __name__ == "__main__":
    unittest.main()
