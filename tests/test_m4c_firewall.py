"""Synthetic-only protocol/release attacks, with reader spies before any IO."""

from __future__ import annotations

import copy
import json
import random
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from m3_fixtures import config as legacy_config

from inventory_ejor.data.budgets import PURPOSES
from inventory_ejor.data.contracts import (
    EvaluationTargets,
    Feature,
    Normalization,
    Observation,
    Window,
)
from inventory_ejor.data.preparation import parse_config, prepare
from inventory_ejor.data.protocol import (
    M5_EVALUATION_SHA256,
    M5_SOURCE_FINGERPRINT,
    M5_VERSION,
    guard_legacy_bundle,
    guard_legacy_job,
    plan_protocol,
)
from inventory_ejor.data.provenance import canonical, fingerprint
from inventory_ejor.data.releases import (
    check_calibration,
    check_freeze,
    check_selection,
    freeze_template,
    release_template,
)
from inventory_ejor.data.staged import (
    learner_payload,
    prepare_evaluation,
    prepare_learner,
    select_cohort,
    validate_task_ledger,
)
from inventory_ejor.data.views import LearnerView

H = "a" * 64


def configuration():
    return {
        "schema_version": 1,
        "status": "proposal_pending_owner_approval",
        "dataset_version": "synthetic-only-v1",
        "first_date": "2020-01-01",
        "source_window": {"start": 1, "stop": 41},
        "horizon": 2,
        "budgets": [2, 4],
        "phases": [
            {"role": "development", "start": 1, "stop": 7, "origins": [5]},
            {"role": "calibration", "start": 7, "stop": 13, "origins": [11]},
            {"role": "validation", "start": 13, "stop": 19, "origins": [17]},
            {"role": "final_test", "start": 19, "stop": 41, "origins": [23, 29]},
        ],
        "cohort": {
            "rule": "metadata_hash_without_sales",
            "count": 2,
            "seed": 0,
            "catalog_sha256": fingerprint(["A", "B", "C"]),
        },
        "features": ["month", "weekday"],
        "information_track": "per_series_with_shared_development",
    }


class MemorySource:
    """No files, GPU or model. Everything is a deterministic artificial count."""

    manifest_sha256 = H

    def __init__(self):
        self.calls = []
        self.values = {}

    def _observations(self, kind, series, window):
        self.calls.append((kind, series, window.start, window.stop))
        return tuple(
            Observation(
                day,
                (date(2020, 1, 1) + timedelta(days=day - 1)).isoformat(),
                self.values.get(day, 3 if day % 4 == 0 else 0),
            )
            for day in window.days
        )

    def read_history(self, series, window):
        return self._observations("history", series, window)

    def verify_freeze(self, config, freeze):
        # Synthetic adapter only; production adapter checks actual code/spec files.
        if self.manifest_sha256 != freeze["source_manifest_sha256"]:
            raise ValueError("synthetic manifest mismatch")

    def read_evaluation(self, series, window):
        return self._observations("evaluation", series, window)


def synthetic_records(cfg):
    """Approved records exist ONLY in this ephemeral synthetic fixture."""
    freeze = freeze_template(cfg)
    freeze.update(
        approved=True,
        approved_by_owner="SYNTHETIC TEST ONLY",
        decision_record="synthetic:test",
        analysis_spec_sha256=H,
        source_manifest_sha256=H,
        code_commit="b" * 40,
    )
    selection = {
        "schema_version": 1,
        "kind": "selection_lock",
        "protocol_sha256": fingerprint(cfg),
        "freeze_sha256": fingerprint(freeze),
        "selection_frozen": True,
        "candidate_sha256": H,
        "baseline_sha256": H,
        "search_spec_sha256": H,
        "calibration_rule_sha256": H,
        "development_access_log_sha256": H,
    }
    calibration = {
        "schema_version": 1,
        "kind": "calibration_lock",
        "protocol_sha256": fingerprint(cfg),
        "freeze_sha256": fingerprint(freeze),
        "selection_sha256": fingerprint(selection),
        "calibration_frozen": True,
        "calibration_result_sha256": H,
        "access_log_sha256": H,
    }
    return freeze, selection, calibration


class FirewallTests(unittest.TestCase):
    def setUp(self):
        self.cfg = configuration()
        self.catalog = ("A", "B", "C")
        self.series = select_cohort(self.cfg, self.catalog)[0]
        self.freeze, self.selection, self.calibration = synthetic_records(self.cfg)
        self.source = MemorySource()

    def grant(
        self, phase="final_test", origin=23, budget=2, capability="learner_history"
    ):
        release = release_template(
            self.cfg,
            phase,
            origin,
            budget,
            capability,
            fingerprint(list(select_cohort(self.cfg, self.catalog))),
        )
        release.update(
            approved=True,
            approved_by_owner="SYNTHETIC TEST ONLY",
            decision_record="synthetic:release",
            freeze_sha256=fingerprint(self.freeze),
        )
        if phase in ("calibration", "final_test"):
            release["selection_sha256"] = fingerprint(self.selection)
        if phase == "final_test":
            release["calibration_sha256"] = fingerprint(self.calibration)
        return release

    def learner(self, release=None, **overrides):
        args = dict(
            catalog=self.catalog,
            series=self.series,
            phase="final_test",
            origin=23,
            budget=2,
            source=self.source,
            selection=self.selection,
            calibration=self.calibration,
        )
        args.update(overrides)
        return prepare_learner(self.cfg, self.freeze, release or self.grant(), **args)

    def test_metadata_plan_and_nonapproving_templates_need_no_reader(self):
        result = plan_protocol(self.cfg)
        self.assertFalse(result["value_access_authorized"])
        self.assertEqual(len(result["tasks"]), 10)
        self.assertEqual(
            result["access_order"],
            ["development", "validation", "calibration", "final_test"],
        )
        self.assertFalse(freeze_template(self.cfg)["approved"])
        with self.assertRaises(ValueError):
            check_freeze(self.cfg, freeze_template(self.cfg))
        self.assertEqual(self.source.calls, [])

    def test_whole_candidate_m5_geometry_is_metadata_only(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "experiments/configs/m4c_protocol_candidate.json"
        )
        cfg = json.loads(path.read_text())
        self.assertEqual(len(plan_protocol(cfg)["tasks"]), 28)
        for origin in (1484, 1915):
            bad = copy.deepcopy(cfg)
            bad["phases"][-1]["origins"] = [origin]
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                plan_protocol(bad)
        cfg["phases"][-1]["origins"] = [1485, 1737]
        plan_protocol(cfg)  # Exact touching endpoints are permitted.
        cfg["phases"][-1]["origins"] = [1485, 1736]
        with self.assertRaisesRegex(ValueError, "embargo"):
            plan_protocol(cfg)

    def test_reject_duplicate_unsorted_missing_and_one_day_crossing(self):
        for origins in ([23, 23], [29, 23], [], [22], [40], [23, 28]):
            cfg = copy.deepcopy(self.cfg)
            cfg["phases"][-1]["origins"] = origins
            with self.subTest(origins=origins), self.assertRaises(ValueError):
                plan_protocol(cfg)

    def test_alternative_layouts_and_nonadaptive_capacity(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "experiments/configs/m4c_protocol_candidate.json"
        )
        base = json.loads(path.read_text())
        earlier_pair = copy.deepcopy(base)
        earlier_pair["phases"][-1]["origins"] = [1485, 1737]
        replication = copy.deepcopy(base)
        for phase, start, stop, origins in zip(
            replication["phases"],
            (1, 505, 757, 1009),
            (505, 757, 1009, 1942),
            ([225, 477], [729], [981], [1233, 1485, 1914]),
            strict=True,
        ):
            phase.update(start=start, stop=stop, origins=origins)
        for cfg in (base, earlier_pair, replication):
            with self.subTest(phases=cfg["phases"]):
                self.assertEqual(len(plan_protocol(cfg)["tasks"]), 7 * 4)
        # 3 development + 1 calibration + 1 validation leaves two final blocks.
        self.assertEqual(1941 // (224 + 28), 7)
        base["phases"][-1]["origins"] = [1485, 1737, 1989]
        with self.assertRaises(ValueError):
            plan_protocol(base)

    def test_fixed_seed_randomized_half_open_boundaries(self):
        rng = random.Random(451)
        for _ in range(250):
            n, h = rng.randint(1, 30), rng.randint(1, 14)
            width = n + h
            cfg = configuration()
            cfg.update(
                budgets=[n],
                horizon=h,
                source_window={"start": 1, "stop": 1 + 5 * width},
            )
            for i, phase in enumerate(cfg["phases"]):
                phase.update(
                    start=1 + i * width,
                    stop=1 + (i + 1) * width,
                    origins=[1 + i * width + n],
                )
            cfg["phases"][-1]["stop"] += width
            a = cfg["phases"][-1]["origins"][0]
            cfg["phases"][-1]["origins"].append(a + width)
            plan_protocol(cfg)
            cfg["phases"][-1]["origins"][-1] -= 1
            with self.assertRaises(ValueError):
                plan_protocol(cfg)

    def test_released_learner_reads_only_own_history(self):
        view, receipt = self.learner()
        self.assertEqual(self.source.calls, [("history", self.series, 21, 23)])
        self.assertEqual(receipt["validated_counts"]["unique_real_observations"], 2)
        self.assertFalse(hasattr(view, "read_evaluation"))
        self.assertFalse(hasattr(view, "source"))
        payload = canonical(learner_payload(view))
        self.assertNotIn(fingerprint(self.cfg).encode(), payload)
        self.assertNotIn(H.encode(), payload)

    def test_unapproved_or_tampered_release_rejected_before_reader(self):
        for key, value in (
            ("approved", False),
            ("budget", 4),
            ("origin", 29),
            ("phase", "calibration"),
            ("freeze_sha256", "0" * 64),
            ("capability", "evaluation_outcomes"),
            ("cohort_sha256", "0" * 64),
            ("selection_sha256", "0" * 64),
        ):
            release = self.grant()
            release[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.learner(release)
        self.assertEqual(self.source.calls, [])

    def test_config_change_after_freeze_and_manifest_change(self):
        release = self.grant()
        self.cfg["cohort"]["seed"] = 1
        with self.assertRaises(ValueError):
            self.learner(release)
        self.cfg["cohort"]["seed"] = 0
        self.source.manifest_sha256 = "0" * 64
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.learner()
        self.assertEqual(self.source.calls, [])

    def test_calibration_before_selection_and_final_before_calibration(self):
        calibration_grant = self.grant("calibration", 11)
        with self.assertRaisesRegex(ValueError, "frozen selection"):
            self.learner(
                calibration_grant,
                phase="calibration",
                origin=11,
                selection=None,
                calibration=None,
            )
        with self.assertRaisesRegex(ValueError, "frozen calibration"):
            self.learner(calibration=None)
        self.assertEqual(self.source.calls, [])
        self.learner(
            calibration_grant, phase="calibration", origin=11, calibration=None
        )
        self.assertEqual(self.source.calls, [("history", self.series, 9, 11)])

    def test_retuning_after_calibration_invalidates_final_release(self):
        for field in ("candidate_sha256", "baseline_sha256", "calibration_rule_sha256"):
            changed = copy.deepcopy(self.selection)
            changed[field] = "0" * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.learner(selection=changed)
        self.assertEqual(self.source.calls, [])

    def test_selection_and_calibration_locks_validate_complete_chain(self):
        check_selection(self.cfg, self.freeze, self.selection)
        check_calibration(self.cfg, self.freeze, self.selection, self.calibration)
        for field in ("selection_sha256", "freeze_sha256"):
            changed = copy.deepcopy(self.calibration)
            changed[field] = "0" * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_calibration(self.cfg, self.freeze, self.selection, changed)

    def test_evaluator_is_separate_capability_and_cannot_be_learner(self):
        args = dict(
            catalog=self.catalog,
            series=self.series,
            phase="final_test",
            origin=23,
            source=self.source,
            selection=self.selection,
            calibration=self.calibration,
        )
        with self.assertRaises(ValueError):
            prepare_evaluation(self.cfg, self.freeze, self.grant(), **args)
        self.assertEqual(self.source.calls, [])
        release = self.grant(budget=None, capability="evaluation_outcomes")
        target, receipt = prepare_evaluation(self.cfg, self.freeze, release, **args)
        self.assertEqual(receipt["release_sha256"], fingerprint(release))
        self.assertIsInstance(target, EvaluationTargets)
        with self.assertRaises(ValueError):
            learner_payload(target)
        with self.assertRaises(ValueError):
            self.learner(release)

    def test_future_observation_and_indirect_targets_in_history_rejected(self):
        original = self.source.read_history
        self.source.read_history = lambda series, window: original(
            series, Window(window.start + 1, window.stop + 1)
        )
        with self.assertRaises(ValueError):
            self.learner()
        self.source.read_history = lambda series, window: EvaluationTargets(
            "x", series, window, original(series, window)
        )
        with self.assertRaises(ValueError):
            self.learner()

    def test_outcomes_denied_through_every_fitting_access_category(self):
        view, receipt = self.learner()
        for purpose in PURPOSES:
            info = copy.deepcopy(receipt["ledger"])
            info["access"][purpose].append(
                {
                    "dataset": self.cfg["dataset_version"],
                    "series": self.series,
                    "start": 23,
                    "stop": 24,
                }
            )
            with self.subTest(purpose=purpose), self.assertRaises(ValueError):
                validate_task_ledger(self.cfg, "final_test", 23, 2, view, info)
        for track in ("pooled", "pretrained", "rich_data"):
            info = copy.deepcopy(receipt["ledger"])
            info["track"] = track
            with self.subTest(track=track), self.assertRaises(ValueError):
                validate_task_ledger(self.cfg, "final_test", 23, 2, view, info)

    def test_unverified_pretraining_and_future_features_fail_closed(self):
        view, receipt = self.learner()
        info = copy.deepcopy(receipt["ledger"])
        info["pretrained_artifacts"] = [{"sha256": H, "lineage_complete": True}]
        with self.assertRaisesRegex(ValueError, "pretraining"):
            validate_task_ledger(self.cfg, "final_test", 23, 2, view, info)
        for features in (["price"], ["month", "month"]):
            cfg = copy.deepcopy(self.cfg)
            cfg["features"] = features
            with self.subTest(features=features), self.assertRaises(ValueError):
                plan_protocol(cfg)

    def test_cohort_cannot_use_future_sales_or_replacements(self):
        cohort = select_cohort(self.cfg, self.catalog)
        excluded = next(x for x in self.catalog if x not in cohort)
        with self.assertRaisesRegex(ValueError, "cohort"):
            self.learner(series=excluded)
        cfg = copy.deepcopy(self.cfg)
        cfg["cohort"]["rule"] = "positive_future_sales"
        with self.assertRaises(ValueError):
            plan_protocol(cfg)
        with self.assertRaises(ValueError):
            select_cohort(self.cfg, (("A", 9999), "B"))
        self.assertEqual(self.source.calls, [])

    def test_reserved_mutation_preserves_complete_learner_bytes(self):
        first, receipt = self.learner()
        self.source.values[23] = 999999  # Reserved outcome mutation.
        second, second_receipt = self.learner()
        self.assertEqual(
            canonical(learner_payload(first)), canonical(learner_payload(second))
        )
        self.assertEqual(receipt, second_receipt)
        self.assertTrue(
            all(call[0] == "history" and call[3] == 23 for call in self.source.calls)
        )

    def test_valid_zero_request_and_intermittent_histories(self):
        self.source.values = {day: 0 for day in range(1, 41)}
        view, _ = self.learner()
        self.assertEqual(view.normalization.scale, 1)
        target, _ = prepare_evaluation(
            self.cfg,
            self.freeze,
            self.grant(budget=None, capability="evaluation_outcomes"),
            catalog=self.catalog,
            series=self.series,
            phase="final_test",
            origin=23,
            source=self.source,
            selection=self.selection,
            calibration=self.calibration,
        )
        self.assertEqual(sum(o.sales for o in target.observations), 0)

    def test_consumer_rejects_forged_normalization_missing_and_future_features(self):
        view, receipt = self.learner()
        bad_views = (
            LearnerView(
                view.history,
                Normalization(999, 1, view.normalization.fitted_days),
                view.features,
            ),
            LearnerView(view.history, view.normalization, ()),
            LearnerView(
                view.history,
                view.normalization,
                (Feature("price", 23, 24, 999, "future price"),),
            ),
        )
        for bad in bad_views:
            with self.subTest(view=bad), self.assertRaises(ValueError):
                validate_task_ledger(
                    self.cfg, "final_test", 23, 2, bad, receipt["ledger"]
                )

    def test_exposed_m5_history_cannot_be_promoted_to_final(self):
        cfg = configuration()
        cfg.update(
            dataset_version=M5_VERSION,
            first_date="2011-01-29",
            source_window={"start": 1, "stop": 1942},
            horizon=28,
            budgets=[28],
        )
        for phase, start, stop, origin in zip(
            cfg["phases"],
            (1, 57, 113, 169),
            (57, 113, 169, 253),
            (29, 85, 141, 225),
            strict=True,
        ):
            phase.update(start=start, stop=stop, origins=[origin])
        with self.assertRaisesRegex(ValueError, "exposed"):
            plan_protocol(cfg)

    def test_legacy_allowed_config_does_not_hide_protected_split_or_ledger(self):
        manifest = {
            "config": {
                "dataset_version": M5_VERSION,
                "origins": [225],
                "horizon": 28,
                "development_window": {"start": 1, "stop": 253},
            },
            "splits": [
                {
                    "history": {"start": 1690, "stop": 1914},
                    "evaluation": {"start": 1914, "stop": 1942},
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "protected"):
            guard_legacy_bundle(manifest)
        manifest.pop("splits")
        manifest["information_budgets"] = [{"ledger": {"origin": 1914}}]
        with self.assertRaisesRegex(ValueError, "protected"):
            guard_legacy_bundle(manifest)
        with self.assertRaisesRegex(ValueError, "Legacy M5"):
            guard_legacy_job(
                {"dataset_version": "renamed", "origin": 1914, "horizon": 28},
                {"data_source_fingerprint": M5_SOURCE_FINGERPRINT},
            )

    def test_legacy_manifest_symlink_rejected_before_read(self):
        from inventory_ejor.baselines.planning import build_plan

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.json").write_text("{}")
            bundle = root / "data/processed/synthetic"
            bundle.mkdir(parents=True)
            outside = root / "outside.json"
            outside.write_text("{}")
            (bundle / "manifest.json").symlink_to(outside)
            cfg = {"prepared_bundle": "data/processed/synthetic"}
            with (
                patch(
                    "inventory_ejor.baselines.planning.read_json", return_value=cfg
                ) as spy,
                patch(
                    "inventory_ejor.baselines.planning.validate_config",
                    return_value=cfg,
                ),
            ):
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    build_plan(root, root / "config.json")
                self.assertEqual(
                    spy.call_count, 1
                )  # Only config; manifest never opened.

    def test_legacy_final_relabel_rejected_before_any_raw_read(self):
        cfg = legacy_config()
        cfg.update(
            dataset_version=M5_VERSION,
            origins=[1914],
            development_window={"start": 1, "stop": 1942},
        )
        with self.assertRaisesRegex(ValueError, "Legacy M5"):
            parse_config(canonical(cfg))
        cfg["dataset_version"] = "renamed-fixture"
        manifest = {
            "files": [
                {
                    "filename": "sales_train_evaluation.csv",
                    "sha256": M5_EVALUATION_SHA256,
                }
            ]
        }
        with patch(
            "inventory_ejor.data.preparation.verify_inputs",
            side_effect=AssertionError("unsafe raw read"),
        ) as spy:
            with self.assertRaisesRegex(ValueError, "Legacy M5"):
                prepare(Path("/nonexistent-synthetic-source"), manifest, canonical(cfg))
            spy.assert_not_called()

    def test_legacy_baseline_plan_checks_scope_before_artifact_hashing(self):
        from inventory_ejor.baselines.planning import build_plan

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.json").write_text("{}")
            cfg = {"prepared_bundle": "data/processed/synthetic"}
            manifest = {
                "schema_version": 2,
                "status": "prepared_development_demo",
                "config": {
                    "mode": "development_demo",
                    "dataset_version": M5_VERSION,
                    "origins": [1914],
                    "horizon": 28,
                    "development_window": {"start": 1, "stop": 1942},
                },
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
                    side_effect=AssertionError("unsafe artifact hash"),
                ) as spy,
            ):
                with self.assertRaisesRegex(ValueError, "Legacy M5"):
                    build_plan(root, root / "config.json")
                spy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
