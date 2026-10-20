"""Adversarial follow-up: production adapter guards and persisted evidence.

All source values, owners, decisions and artifacts are temporary synthetic data.
"""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_m4c_firewall as firewall_fixture
import test_m4c_source_integration as source_fixture

from inventory_ejor.data.contracts import Window
from inventory_ejor.data.evidence import EvidenceStore, verify_selection
from inventory_ejor.data.provenance import fingerprint
from inventory_ejor.data.staged_source import M5EvaluatorSource, M5HistorySource


class DirectAdapterAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.f = source_fixture.StagedSourceIntegrationTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.live = patch(
            "inventory_ejor.data.staged_source._live_code",
            return_value=("b" * 40, False),
        )
        self.live.start()
        self.addCleanup(self.live.stop)

    def authorization(self, capability="learner_history"):
        f = self.f
        return dict(
            config=f.cfg,
            freeze=f.freeze,
            release=f.release(capability),
            catalog=f.catalog,
            phase="final_test",
            origin=23,
            budget=2 if capability == "learner_history" else None,
            selection=f.selection,
            calibration=f.calibration,
            evidence=f.evidence,
        )

    def test_both_direct_methods_without_records_reject_before_raw_io(self):
        f = self.f
        f.spec.unlink()
        with patch(
            "inventory_ejor.data.staged_source.verify_inputs",
            side_effect=AssertionError("raw access"),
        ) as spy:
            for cls, method in (
                (M5HistorySource, "read_history"),
                (M5EvaluatorSource, "read_evaluation"),
            ):
                with (
                    self.subTest(cls=cls),
                    self.assertRaisesRegex(ValueError, "per-read authorization"),
                ):
                    getattr(f.source(cls), method)(f.series, Window(23, 25))
            spy.assert_not_called()

    def test_authorized_direct_reads_persist_exact_distinct_receipts(self):
        f = self.f
        for cls, method, capability, window in (
            (M5HistorySource, "read_history", "learner_history", Window(21, 23)),
            (
                M5EvaluatorSource,
                "read_evaluation",
                "evaluation_outcomes",
                Window(23, 25),
            ),
        ):
            source = f.source(cls)
            rows = getattr(source, method)(
                f.series, window, authorization=self.authorization(capability)
            )
            self.assertEqual([o.day for o in rows], list(window.days))
            receipts = [f.evidence.read(p.stem) for p in f.evidence.root.glob("*.json")]
            matching = [
                r
                for r in receipts
                if r.get("kind") == "staged_access_receipt"
                and r["phase"] == "final_test"
                and r["capability"] == capability
            ]
            self.assertEqual(len(matching), 1)
            self.assertEqual(
                matching[0]["release_sha256"], fingerprint(f.release(capability))
            )
            # A successful read never arms an unscoped second read.
            with self.assertRaises(ValueError):
                getattr(source, method)(f.series, window)

    def test_wrong_window_and_cross_capability_reject_before_raw_io(self):
        f = self.f
        with patch(
            "inventory_ejor.data.staged_source.verify_inputs",
            side_effect=AssertionError("raw access"),
        ) as spy:
            attacks = (
                (f.source(), "read_history", Window(23, 25), self.authorization()),
                (f.source(), "read_history", Window(20, 23), self.authorization()),
                (
                    f.source(),
                    "read_history",
                    Window(21, 23),
                    self.authorization("evaluation_outcomes"),
                ),
                (
                    f.source(M5EvaluatorSource),
                    "read_evaluation",
                    Window(23, 25),
                    self.authorization(),
                ),
            )
            for source, method, window, auth in attacks:
                with (
                    self.subTest(method=method, window=window),
                    self.assertRaises(ValueError),
                ):
                    getattr(source, method)(f.series, window, authorization=auth)
            with self.assertRaisesRegex(ValueError, "Cross-capability"):
                f.source()._read(
                    f.series,
                    Window(23, 25),
                    capability="evaluation_outcomes",
                    authorization=self.authorization("evaluation_outcomes"),
                )
            spy.assert_not_called()

    def test_full_context_still_requires_live_spec_and_owner_approval(self):
        f = self.f
        with patch(
            "inventory_ejor.data.staged_source.verify_inputs",
            side_effect=AssertionError("raw access"),
        ) as spy:
            auth = self.authorization()
            auth["release"]["approved"] = False
            with patch.object(
                f.evidence, "read", side_effect=AssertionError("evidence access")
            ) as evidence_spy:
                with self.assertRaisesRegex(ValueError, "owner authorization"):
                    f.source().read_history(
                        f.series, Window(21, 23), authorization=auth
                    )
                evidence_spy.assert_not_called()
            f.spec.unlink()
            with self.assertRaisesRegex(ValueError, "analysis specification"):
                f.source().read_history(
                    f.series, Window(21, 23), authorization=self.authorization()
                )
            spy.assert_not_called()

    def test_authorization_cannot_be_reused_after_config_change(self):
        f = self.f
        auth = self.authorization()
        f.cfg["cohort"]["seed"] += 1
        with patch("inventory_ejor.data.staged_source.verify_inputs") as spy:
            with self.assertRaises(ValueError):
                f.source().read_history(f.series, Window(21, 23), authorization=auth)
            spy.assert_not_called()

    def test_receipt_persistence_failure_prevents_returning_values(self):
        f = self.f
        source = f.source()
        # The read may already have exposed values to the trusted preparer;
        # failure must propagate and must not deliver them as a successful call.
        with patch.object(
            f.evidence, "put", side_effect=OSError("synthetic persistence failure")
        ):
            with self.assertRaisesRegex(OSError, "persistence failure"):
                source.read_history(
                    f.series, Window(21, 23), authorization=self.authorization()
                )

    def test_development_adapter_also_requires_a_persisted_receipt_store(self):
        f = self.f
        auth = self.authorization()
        release = firewall_fixture.release_template(
            f.cfg,
            "development",
            5,
            2,
            "learner_history",
            fingerprint(list(firewall_fixture.select_cohort(f.cfg, f.catalog))),
        )
        release.update(
            approved=True,
            approved_by_owner="SYNTHETIC ONLY",
            decision_record="synthetic:development",
            freeze_sha256=fingerprint(f.freeze),
        )
        auth.update(
            release=release,
            phase="development",
            origin=5,
            selection=None,
            calibration=None,
            evidence=None,
        )
        with patch("inventory_ejor.data.staged_source.verify_inputs") as spy:
            with self.assertRaisesRegex(ValueError, "persisted access receipts"):
                f.source().read_history(f.series, Window(3, 5), authorization=auth)
            spy.assert_not_called()

    def test_legacy_planner_refuses_staged_metadata_before_hashing_artifacts(self):
        from inventory_ejor.baselines.planning import build_plan

        with tempfile.TemporaryDirectory(prefix="m4c-legacy-contract-") as tmp:
            root = Path(tmp)
            (root / "config.json").write_text("{}")
            cfg = {"prepared_bundle": "data/processed/synthetic"}
            manifest = {
                "schema_version": 1,
                "kind": "staged_learner_manifest",
                "status": "prepared_staged_learner_only",
            }
            with (
                patch(
                    "inventory_ejor.baselines.planning.read_json",
                    side_effect=[cfg, manifest],
                ),
                patch(
                    "inventory_ejor.baselines.planning.validate_config",
                    return_value=cfg,
                ),
                patch(
                    "inventory_ejor.baselines.planning.sha_file",
                    side_effect=AssertionError("unreleased evaluator hash"),
                ) as spy,
            ):
                with self.assertRaisesRegex(ValueError, "Only corrected M3"):
                    build_plan(root, root / "config.json")
                spy.assert_not_called()

    def test_legacy_worker_refuses_every_explicit_protected_phase(self):
        from inventory_ejor.baselines.worker import execute_job

        for phase in ("validation", "calibration", "final_test"):
            # No usable plan, data paths or output directory. The guard must
            # reject before loading a model or looking at any of those fields.
            with (
                self.subTest(phase=phase),
                self.assertRaisesRegex(ValueError, "Legacy workers"),
            ):
                execute_job(Path("/nonexistent"), {}, {"phase": phase}, None, "cpu")


class PersistedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.f = firewall_fixture.FirewallTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)

    def log(self):
        f = self.f
        return f.evidence.read(f.selection["development_access_log_sha256"])

    def changed_selection(self, log):
        f = self.f
        selection = copy.deepcopy(f.selection)
        selection["development_access_log_sha256"] = f.evidence.put(log)
        release = f.grant("calibration", 11)
        release["selection_sha256"] = fingerprint(selection)
        return release, selection

    def test_hash_shaped_placeholders_no_longer_authorize_calibration(self):
        f = self.f
        _, selection, _ = firewall_fixture.synthetic_records(f.cfg)
        release = f.grant("calibration", 11)
        release["selection_sha256"] = fingerprint(selection)
        for store in (None, f.evidence):
            with (
                self.subTest(store=store),
                self.assertRaisesRegex(ValueError, "evidence"),
            ):
                f.learner(
                    release,
                    phase="calibration",
                    origin=11,
                    selection=selection,
                    calibration=None,
                    evidence=store,
                )
        self.assertEqual(f.source.calls, [])

    def test_absent_validation_outcome_or_history_or_series_rejected(self):
        f = self.f
        for predicate in (
            lambda r: r["capability"] == "evaluation_outcomes",
            lambda r: r["capability"] == "learner_history" and r["budget"] == 4,
            lambda r: r["series"] == f.series,
        ):
            log = self.log()
            log["receipt_sha256s"] = [
                d for d in log["receipt_sha256s"] if not predicate(f.evidence.read(d))
            ]
            release, selection = self.changed_selection(log)
            with self.assertRaisesRegex(ValueError, "coverage"):
                f.learner(
                    release,
                    phase="calibration",
                    origin=11,
                    selection=selection,
                    calibration=None,
                )
        self.assertEqual(f.source.calls, [])

    def test_duplicate_wrong_phase_and_rehashed_wrong_window_rejected(self):
        f = self.f
        for change in ("duplicate", "wrong_phase", "wrong_window"):
            log = self.log()
            if change == "duplicate":
                log["receipt_sha256s"].append(log["receipt_sha256s"][0])
            else:
                receipt = f.evidence.read(log["receipt_sha256s"][0])
                if change == "wrong_phase":
                    receipt["phase"] = "final_test"
                else:
                    receipt["window"]["stop"] += 1
                log["receipt_sha256s"][0] = f.evidence.put(receipt)
                log["receipt_sha256s"].sort()
            release, selection = self.changed_selection(log)
            with self.subTest(change=change), self.assertRaises(ValueError):
                f.learner(
                    release,
                    phase="calibration",
                    origin=11,
                    selection=selection,
                    calibration=None,
                )
        self.assertEqual(f.source.calls, [])

    def test_wrong_kind_missing_file_mutation_and_symlink_rejected(self):
        f = self.f
        digest = f.selection["candidate_sha256"]
        path = f.evidence.root / (digest + ".json")
        original = path.read_bytes()
        for attack in ("missing", "mutation", "symlink"):
            path.unlink()
            if attack == "mutation":
                path.write_bytes(b"{}")
            elif attack == "symlink":
                target = path.with_name("unread.txt")
                target.write_bytes(original)
                path.symlink_to(target)
            with self.subTest(attack=attack), self.assertRaises(ValueError):
                f.learner()
            if path.is_symlink() or path.exists():
                path.unlink()
            path.write_bytes(original)
        wrong = f.evidence.put({"synthetic": "wrong kind"})
        selection = dict(f.selection, candidate_sha256=wrong)
        with self.assertRaises(ValueError):
            verify_selection(f.cfg, f.freeze, selection, (f.series,), f.evidence)
        self.assertEqual(f.source.calls, [])

    def test_selection_result_must_bind_actual_validation_receipts(self):
        f = self.f
        log = self.log()
        result = f.evidence.read(log["selection_result_sha256"])
        result["validation_receipt_sha256s"] = []
        log["selection_result_sha256"] = f.evidence.put(result)
        release, selection = self.changed_selection(log)
        with self.assertRaisesRegex(ValueError, "validation evidence"):
            f.learner(
                release,
                phase="calibration",
                origin=11,
                selection=selection,
                calibration=None,
            )
        self.assertEqual(f.source.calls, [])

    def test_final_requires_persisted_calibration_result_and_coverage(self):
        f = self.f
        for attack in ("missing_result", "incomplete_receipts", "wrong_selection"):
            calibration = dict(f.calibration)
            if attack == "missing_result":
                calibration["calibration_result_sha256"] = "0" * 64
            else:
                log = f.evidence.read(calibration["access_log_sha256"])
                if attack == "incomplete_receipts":
                    log["receipt_sha256s"].pop()
                else:
                    log["selection_sha256"] = "0" * 64
                calibration["access_log_sha256"] = f.evidence.put(log)
            release = f.grant()
            release["calibration_sha256"] = fingerprint(calibration)
            with self.subTest(attack=attack), self.assertRaises(ValueError):
                f.learner(release, calibration=calibration)
        self.assertEqual(f.source.calls, [])

    def test_store_rejects_symlink_root_and_existing_mutated_digest(self):
        f = self.f
        with tempfile.TemporaryDirectory(prefix="m4c-store-") as temp:
            alias = Path(temp) / "alias"
            alias.symlink_to(f.evidence.root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "Canonical"):
                EvidenceStore(alias)
        obj = {"synthetic": "exclusive record"}
        digest = f.evidence.put(obj)
        self.assertEqual(f.evidence.put(obj), digest)
        (f.evidence.root / (digest + ".json")).write_text("{}")
        with self.assertRaisesRegex(ValueError, "checksum"):
            f.evidence.put(obj)

    def test_metadata_plan_rejects_unrepresentable_evidence_inventory(self):
        cfg = firewall_fixture.configuration()
        cfg["source_window"]["stop"] = 401
        for i, phase in enumerate(cfg["phases"]):
            phase.update(start=1 + 100 * i, stop=101 + 100 * i, origins=[5 + 100 * i])
        cfg["phases"][2]["origins"] = [205 + 6 * j for j in range(10)]
        cfg["cohort"]["count"] = 256
        firewall_fixture.plan_protocol(cfg)  # 8,448 selection-stage receipts fit.
        cfg["cohort"]["count"] = 1024
        with self.assertRaisesRegex(ValueError, "evidence capacity"):
            firewall_fixture.plan_protocol(cfg)


if __name__ == "__main__":
    unittest.main()
