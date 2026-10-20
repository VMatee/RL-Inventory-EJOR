"""Synthetic cost-representation and persistence/cleanup failure regressions."""

from __future__ import annotations

import copy
import math
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_m4d0_execution as fixtures
from test_m4c_firewall import synthetic_records

from inventory_ejor.data.m4d0_audit import verify_synthetic_reference_trace
from inventory_ejor.data.m4d0_execution import (
    execute_synthetic_reference,
    validate_score_record,
    validated_plan,
)
from inventory_ejor.data.m4d0_store import (
    PendingArtifactCleanupError,
    PrivateExecutionStore,
)
from inventory_ejor.data.provenance import fingerprint
from inventory_ejor.data.releases import release_template
from inventory_ejor.data.staged import (
    prepare_evaluation,
    prepare_learner,
    select_cohort,
)


class CostRepresentationTests(unittest.TestCase):
    def lifecycle(self, history, requests, scenario):
        f = fixtures.M4d0ReferenceTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        n, horizon = len(history), len(requests)
        width = n + horizon
        f.config.update(
            budgets=[n],
            horizon=horizon,
            source_window={"start": 1, "stop": 1 + 5 * width},
        )
        for i, phase in enumerate(f.config["phases"]):
            phase.update(
                start=1 + i * width,
                stop=1 + (i + 1) * width,
                origins=[1 + i * width + n],
            )
        f.config["phases"][-1]["stop"] += width
        f.config["phases"][-1]["origins"].append(1 + 4 * width + n)
        f.freeze, _, _ = synthetic_records(f.config)
        f.scenario = scenario
        f.source.values = dict(enumerate([*history, *requests], 1))
        cohort = select_cohort(f.config, f.catalog)
        for capability, budget, attribute in (
            ("learner_history", n, "history_release"),
            ("evaluation_outcomes", None, "eval_release"),
        ):
            release = release_template(
                f.config,
                "development",
                n + 1,
                budget,
                capability,
                fingerprint(list(cohort)),
            )
            release.update(
                approved=True,
                approved_by_owner="SYNTHETIC ONLY",
                decision_record="synthetic:cost-boundary",
                freeze_sha256=fingerprint(f.freeze),
            )
            setattr(f, attribute, release)
        common = dict(
            catalog=f.catalog,
            series=f.series,
            phase="development",
            origin=n + 1,
            source=f.source,
            evidence=f.evidence,
        )
        view, receipt = prepare_learner(
            f.config, f.freeze, f.history_release, budget=n, **common
        )
        plan = f.publish(view, receipt, origin=n + 1, budget=n)
        approval = f.approval(plan)
        fit = execute_synthetic_reference(f.private, plan, approval)
        targets, receipt = prepare_evaluation(
            f.config, f.freeze, f.eval_release, **common
        )
        score = f.score(plan, fit, approval, targets, receipt)
        run = SimpleNamespace(
            f=f, plan=plan, approval=approval, fit=fit, targets=targets, score=score
        )
        self.audit(run)
        return run

    @staticmethod
    def audit(run, score=None):
        f = run.f
        return verify_synthetic_reference_trace(
            f.private,
            run.plan,
            run.fit,
            score or run.score,
            run.targets,
            evidence=f.evidence,
            config=f.config,
            freeze=f.freeze,
            catalog=f.catalog,
        )

    def high_cost(self):
        scenario = fixtures.tiny_scenario()
        scenario["costs"].update(
            holding=0.0, lost_sales=1e15, variable_order=0.0, fixed_order=0.0
        )
        return self.lifecycle([0, 0], [5, 0], scenario)

    def test_rehashed_total_plus_100_at_5e15_is_rejected(self):
        run = self.high_cost()
        score = run.f.private.read(run.score)
        self.assertEqual(score["total_cost"], 5_000_000_000_000_000)
        score["total_cost"] += 100
        forged = run.f.private.put(score)
        self.assertNotEqual(forged, run.score)
        with self.assertRaisesRegex(ValueError, "fsum of saved components"):
            self.audit(run, forged)

    def test_zero_subnormal_small_noninteger_and_large_finite_costs(self):
        for coefficient in (0.0, 5e-324, 1e-201, 0.1, 0.35, 1e100, 1e307):
            horizon = 2 if coefficient == 1e307 else 64
            scenario = fixtures.tiny_scenario(stock=3, lead=1, horizon=horizon)
            scenario["costs"]["holding"] = coefficient
            with self.subTest(coefficient=coefficient):
                run = self.lifecycle([0, 0], [0] * horizon, scenario)
                saved = run.f.private.read(run.score)
                trace = run.f.private.read(saved["trace_sha256"])["periods"]
                self.assertEqual(
                    saved["total_cost"], math.fsum(saved["cost_components"].values())
                )
                if coefficient in (0.1, 1e-201):
                    # Regrouping the same mathematical sum rounds differently.
                    self.assertNotEqual(
                        saved["total_cost"], math.fsum(r["cost"] for r in trace)
                    )
                    self.assertEqual(self.audit(run)["total_cost"], saved["total_cost"])

    def test_period_left_association_is_preserved_not_replaced_by_fsum(self):
        scenario = fixtures.tiny_scenario(stock=1, lead=1, horizon=2)
        scenario["costs"].update(
            holding=float(2**53), variable_order=0.2, fixed_order=1.0
        )
        run = self.lifecycle([3, 3], [0, 0], scenario)
        saved = run.f.private.read(run.score)
        trace = run.f.private.read(saved["trace_sha256"])
        self.assertEqual(trace["periods"][0]["order"], 5)
        self.assertEqual(trace["periods"][0]["cost"], float(2**53))
        trace["periods"][0]["cost"] = math.fsum((2**53, 0.0, 1.0, 1.0))
        self.assertNotEqual(trace["periods"][0]["cost"], float(2**53))
        saved["trace_sha256"] = run.f.private.put(trace)
        with self.assertRaisesRegex(ValueError, "transition/cost"):
            self.audit(run, run.f.private.put(saved))

    def test_coherently_rehashed_component_and_total_changes_rejected(self):
        run = self.high_cost()
        for mode in ("plus_100", "one_ulp", "balanced"):
            saved = run.f.private.read(run.score)
            components = saved["cost_components"]
            if mode == "balanced":
                components["holding"] += 100
                components["lost_sales"] -= 100
            else:
                components["lost_sales"] = (
                    components["lost_sales"] + 100
                    if mode == "plus_100"
                    else math.nextafter(components["lost_sales"], math.inf)
                )
            saved["total_cost"] = math.fsum(components.values())
            with (
                self.subTest(mode=mode),
                self.assertRaisesRegex(ValueError, "score totals"),
            ):
                self.audit(run, run.f.private.put(saved))

    def test_rehashed_period_and_tiny_component_corruption_rejected(self):
        for coefficient in (0.0, 1e-201, 0.3, 1e15):
            scenario = fixtures.tiny_scenario(stock=3, lead=1, horizon=2)
            scenario["costs"]["holding"] = coefficient
            run = self.lifecycle([0, 0], [0, 0], scenario)
            saved = run.f.private.read(run.score)
            trace = run.f.private.read(saved["trace_sha256"])
            original = trace["periods"][0]["cost"]
            trace["periods"][0]["cost"] = math.nextafter(original, math.inf)
            saved["trace_sha256"] = run.f.private.put(trace)
            with self.subTest(coefficient=coefficient), self.assertRaises(ValueError):
                self.audit(run, run.f.private.put(saved))
            saved = run.f.private.read(run.score)
            components = saved["cost_components"]
            components["holding"] = math.nextafter(components["holding"], math.inf)
            saved["total_cost"] = math.fsum(components.values())
            with self.assertRaises(ValueError):
                self.audit(run, run.f.private.put(saved))

    def test_invalid_nonfinite_and_overflowing_costs_fail_closed(self):
        run = self.high_cost()
        f = run.f
        plan, inv, _, _ = validated_plan(f.private, run.plan)
        original = f.private.read(run.score)
        for invalid in (
            True,
            -1,
            None,
            "5",
            [],
            math.inf,
            -math.inf,
            math.nan,
            10**1000,
        ):
            for field in ("total", "component"):
                saved = copy.deepcopy(original)
                if field == "total":
                    saved["total_cost"] = invalid
                else:
                    saved["cost_components"]["holding"] = invalid
                with self.subTest(field=field, invalid=str(invalid)[:20]):
                    with self.assertRaises(ValueError):
                        validate_score_record(
                            saved, run.plan, run.fit, plan, inv, run.approval
                        )
        overflow = copy.deepcopy(original)
        overflow["cost_components"].update(holding=1e308, lost_sales=1e308)
        overflow["total_cost"] = 1e308
        with self.assertRaises(ValueError):
            self.audit(run, f.private.put(overflow))
        for invalid in (True, -1, None, "5", math.inf, math.nan):
            saved = copy.deepcopy(original)
            trace = f.private.read(saved["trace_sha256"])
            trace["periods"][0]["cost"] = invalid
            with self.subTest(period_cost=str(invalid)), self.assertRaises(ValueError):
                # Canonical persistence itself rejects NaN/Inf before audit.
                saved["trace_sha256"] = f.private.put(trace)
                self.audit(run, f.private.put(saved))


class CleanupFailureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="m4d0-cleanup-regression-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = PrivateExecutionStore(self.root)
        self.value = {"kind": "synthetic-cleanup-test", "values": [1, 2, 3]}

    def test_primary_sync_failure_preserved_with_explicit_cleanup_cause(self):
        primary, secondary = OSError("PRIMARY fsync"), OSError("SECONDARY unlink")
        with (
            patch("inventory_ejor.data.m4d0_store.os.fsync", side_effect=primary),
            patch(
                "inventory_ejor.data.m4d0_store.os.unlink", side_effect=secondary
            ) as unlink,
        ):
            with self.assertRaises(OSError) as caught:
                self.store.put(self.value)
            self.assertIs(caught.exception, primary)
            self.assertEqual(unlink.call_count, 1)
        diagnostic = caught.exception.__cause__
        self.assertIsInstance(diagnostic, PendingArtifactCleanupError)
        self.assertIs(diagnostic.__cause__, secondary)
        self.assertEqual(list(self.root.glob("*.json")), [])
        self.assertEqual(list(self.root.glob(".pending-*")), [diagnostic.pending_path])
        self.assertIn(str(diagnostic.pending_path), str(diagnostic))
        self.assertIn("stop retries", str(diagnostic))

    def test_partial_pending_file_never_accepted_and_retry_succeeds(self):
        write, calls = os.write, 0
        primary = OSError("partial write")

        def partial(fd, data):
            nonlocal calls
            calls += 1
            if calls == 1:
                return write(fd, data[:3])
            raise primary

        with (
            patch("inventory_ejor.data.m4d0_store.os.write", side_effect=partial),
            patch(
                "inventory_ejor.data.m4d0_store.os.unlink",
                side_effect=OSError("cleanup"),
            ),
        ):
            with self.assertRaises(OSError) as caught:
                self.store.put(self.value)
        self.assertIs(caught.exception, primary)
        pending = next(self.root.glob(".pending-*"))
        self.assertEqual(pending.stat().st_size, 3)
        for identity in (pending.name, fingerprint(self.value)):
            with self.assertRaises(ValueError):
                self.store.read(identity)
            with self.assertRaises(ValueError):
                self.store.file(identity)
        digest = self.store.put(self.value)
        self.assertEqual(self.store.read(digest), self.value)
        self.assertTrue(pending.exists())

    def test_publication_cleanup_failure_and_preexisting_retry(self):
        with patch(
            "inventory_ejor.data.m4d0_store.os.unlink", side_effect=OSError("cleanup")
        ) as unlink:
            with self.assertRaises(PendingArtifactCleanupError) as caught:
                self.store.put(self.value)
            self.assertEqual(unlink.call_count, 1)
        self.assertEqual(len(list(self.root.glob("*.json"))), 1)
        self.assertTrue(caught.exception.pending_path.exists())
        with (
            patch("inventory_ejor.data.m4d0_store.os.fsync", wraps=os.fsync) as sync,
            patch(
                "inventory_ejor.data.m4d0_store.os.unlink",
                side_effect=AssertionError("unrelated cleanup"),
            ),
        ):
            digest = self.store.put(self.value)
            self.assertEqual(sync.call_count, 2)
        self.assertEqual(self.store.read(digest), self.value)
        self.assertTrue(caught.exception.pending_path.exists())

    def test_bounded_repeated_failures_require_quiescent_owner_recovery(self):
        for attempt in range(3):
            primary = OSError(f"fsync attempt {attempt}")
            with (
                patch("inventory_ejor.data.m4d0_store.os.fsync", side_effect=primary),
                patch(
                    "inventory_ejor.data.m4d0_store.os.unlink",
                    side_effect=OSError("cleanup"),
                ),
            ):
                with self.assertRaises(OSError) as caught:
                    self.store.put(self.value)
                self.assertIs(caught.exception, primary)
            self.assertEqual(len(list(self.root.glob(".pending-*"))), attempt + 1)
            self.assertEqual(list(self.root.glob("*.json")), [])
        # Explicit test-owner recovery after all calls have stopped; no auto-pruning.
        for path in self.root.glob(".pending-*"):
            path.unlink()
        directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertEqual(self.store.read(self.store.put(self.value)), self.value)

    def test_failed_creation_does_not_cleanup_another_writers_file(self):
        other = self.root / (".pending-" + "a" * 32)
        other.write_bytes(b"another active writer")
        open_file = os.open

        def fail_create(path, *args, **kwargs):
            if str(path).startswith(".pending-"):
                raise OSError("creation failed")
            return open_file(path, *args, **kwargs)

        with (
            patch("inventory_ejor.data.m4d0_store.os.open", side_effect=fail_create),
            patch(
                "inventory_ejor.data.m4d0_store.os.unlink",
                side_effect=AssertionError("must not unlink"),
            ),
        ):
            with self.assertRaisesRegex(OSError, "creation"):
                self.store.put(self.value)
        self.assertEqual(other.read_bytes(), b"another active writer")

    def test_repeated_directory_sync_failure_never_claims_success(self):
        sync = os.fsync
        import stat

        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("directory synchronization")
            return sync(fd)

        for _ in range(3):
            with patch(
                "inventory_ejor.data.m4d0_store.os.fsync", side_effect=fail_directory
            ):
                with self.assertRaisesRegex(OSError, "directory"):
                    self.store.put(self.value)
        self.assertEqual(list(self.root.glob(".pending-*")), [])
        self.assertEqual(len(list(self.root.glob("*.json"))), 1)
        self.assertEqual(self.store.read(self.store.put(self.value)), self.value)

    def test_real_concurrent_identical_publication_remains_valid(self):
        barrier = threading.Barrier(4)

        def publish(_):
            barrier.wait(timeout=5)
            return self.store.put(self.value)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(publish, i) for i in range(4)]
            digests = [future.result(timeout=10) for future in futures]
        self.assertEqual(len(set(digests)), 1)
        self.assertEqual(self.store.read(digests[0]), self.value)
        self.assertEqual(list(self.root.glob(".pending-*")), [])
        self.assertEqual(len(list(self.root.glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
