"""Independent leakage traps for M3. All CSV inputs are generated miniature data."""

import copy
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from m3_fixtures import config, fixture_manifest, make_fixture, write_csv

from inventory_ejor.data.budgets import (
    SourcePolicy,
    access,
    assert_comparable,
    assert_same_evaluation,
    ledger,
    validate_ledger,
)
from inventory_ejor.data.contracts import (
    BUDGETS,
    EvaluationTargets,
    Feature,
    History,
    Observation,
    Phase,
    SplitPlan,
    Window,
    features_at,
    fit_normalization,
)
from inventory_ejor.data.m5 import (
    ReadLimits,
    calendar_features,
    check_overlap,
    eligible,
    load_calendar,
    load_catalog,
    load_observations,
    load_prices,
    price_features,
    rank_candidates,
)
from inventory_ejor.data.preparation import parse_config, prepare
from inventory_ejor.data.provenance import (
    canonical,
    read_json,
    verify_inputs,
    write_exclusive,
)
from inventory_ejor.data.synthetic import sample_iid
from inventory_ejor.data.views import load_learner, separate_artifacts

ROOT = Path(__file__).resolve().parents[1]


def history(n=28, origin=225):
    return History(
        "fixture-v1",
        "A",
        origin,
        tuple(
            Observation(
                d, (date(2020, 1, 1) + timedelta(days=d - 1)).isoformat(), d % 5
            )
            for d in range(origin - n, origin)
        ),
    )


class ChronologicalTests(unittest.TestCase):
    def setUp(self):
        self.plan = SplitPlan(
            tuple(
                Phase(role, Window(1 + 300 * i, 301 + 300 * i))
                for i, role in enumerate(
                    ("development", "calibration", "validation", "final_test")
                )
            ),
            28,
        )

    def test_exact_budgets_shared_future_dates_and_no_overlap(self):
        windows = []
        for n in (28, 56, 112, 224):
            train, target = self.plan.windows("development", 225, n)
            self.assertEqual(len(train.days), n)
            self.assertEqual(train.days, tuple(range(225 - n, 225)))
            self.assertEqual(target.days, tuple(range(225, 253)))
            self.assertFalse(set(train.days) & set(target.days))
            windows.append(target)
        assert_same_evaluation(windows)

    def test_four_phase_separation_includes_context(self):
        all_days = set()
        for role, origin in zip(
            ("development", "calibration", "validation", "final_test"),
            (225, 525, 825, 1125),
            strict=True,
        ):
            train, target = self.plan.windows(role, origin, 224)
            days = set(train.days + target.days)
            self.assertFalse(all_days & days)
            all_days.update(days)

    def test_history_cannot_cross_phase_boundary(self):
        with self.assertRaisesRegex(ValueError, "boundary"):
            self.plan.windows("validation", 700, 28)

    def test_reject_phase_overlap_order_duplicate_and_missing(self):
        for phases in (
            (
                Phase("development", Window(1, 500)),
                Phase("validation", Window(400, 800)),
            ),
            (
                Phase("validation", Window(1, 300)),
                Phase("development", Window(300, 600)),
            ),
            (
                Phase("development", Window(1, 300)),
                Phase("development", Window(300, 600)),
            ),
        ):
            with self.subTest(phases=phases), self.assertRaises(ValueError):
                SplitPlan(phases, 28)
        with self.assertRaises(ValueError):
            self.plan.windows("unknown", 225, 28)

    def test_origin_overlap_duplicates_and_resource_types(self):
        self.plan.validate_origins("development", (225, 253))
        for origins in ((225, 226), (225, 225), (253, 225), ()):
            with self.subTest(origins=origins), self.assertRaises(ValueError):
                self.plan.validate_origins("development", origins)
        for value in (True, 1.5, -1, 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Window(value, 10)
        with self.assertRaises(ValueError):
            assert_same_evaluation([Window(225, 253), Window(226, 254)])

    def test_history_immutable_and_rejects_future_missing_duplicate_dates(self):
        h = history()
        with self.assertRaises(FrozenInstanceError):
            h.origin = 226
        for obs in (
            h.observations[:10] + h.observations[11:],
            h.observations + (h.observations[-1],),
            tuple(reversed(h.observations)),
        ):
            with self.subTest(obs=len(obs)), self.assertRaises(ValueError):
                History(h.dataset, h.series, h.origin, obs)
        with self.assertRaises(ValueError):
            History(
                "x",
                "A",
                225,
                (
                    Observation(224, "2020-01-01", 1),
                    Observation(225, "2020-01-02", 999999),
                ),
            )

    def test_normalization_independent_hand_values_and_test_rejection(self):
        h = History(
            "x",
            "A",
            5,
            tuple(Observation(i, f"2020-01-0{i}", 2 * i) for i in range(1, 5)),
        )
        norm = fit_normalization(h, Window(1, 4))
        self.assertEqual(norm.mean, 4)
        self.assertAlmostEqual(norm.scale, (8 / 3) ** 0.5)
        self.assertEqual(norm.fitted_days, (1, 2, 3))
        with self.assertRaises(ValueError):
            fit_normalization(h, Window(1, 6))
        target = EvaluationTargets(
            "x", "A", Window(5, 6), (Observation(5, "2020-01-05", 999999),)
        )
        with self.assertRaises(ValueError):
            fit_normalization(target, Window(5, 6))

    def test_constant_normalization_uses_unit_scale(self):
        h = History(
            "x",
            "A",
            3,
            (Observation(1, "2020-01-01", 0), Observation(2, "2020-01-02", 0)),
        )
        self.assertEqual(fit_normalization(h, h.window).scale, 1)

    def test_availability_and_duplicate_feature_traps(self):
        good = Feature("price", 225, 224, 3.5, "externally documented release")
        self.assertEqual(features_at((good,), 225), (good,))
        with self.assertRaises(ValueError):
            features_at((Feature("price", 225, 226, 3.5, "late"),), 225)
        with self.assertRaises(ValueError):
            features_at((good, good), 225)
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Feature("x", 1, 0, value, "evidence")


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.h = history()
        self.policies = (
            SourcePolicy(
                "fixture-v1", "2020-01-01", (Window(1, 281),), (Window(225, 253),)
            ),
        )
        self.info = ledger(self.h, "A", ("month", "weekday"))

    def test_all_history_budgets_count_distinct_observations(self):
        for n in BUDGETS:
            h = history(n)
            info = ledger(h, "A", ())
            for purpose in (
                "normalization",
                "demand_model_fitting",
                "hyperparameter_optimization",
                "calibration",
                "validation",
                "initialization",
                "eligibility",
            ):
                info["access"][purpose] = [access(h)]
            info["synthetic_transitions"] = 10000
            info["optimization_trials"] = 12
            result = validate_ledger(info, self.policies, h)
            self.assertEqual(result["unique_real_observations"], n)
            self.assertEqual(result["synthetic_transitions"], 10000)
            self.assertEqual(result["by_purpose"]["normalization"], n)

    def test_future_normalization_and_frozen_outcomes_rejected(self):
        for start, stop in ((224, 226), (225, 253)):
            info = copy.deepcopy(self.info)
            info["access"]["normalization"] = [
                {"dataset": "fixture-v1", "series": "A", "start": start, "stop": stop}
            ]
            with self.subTest(start=start), self.assertRaises(ValueError):
                validate_ledger(info, self.policies, self.h)

    def test_extra_older_data_cannot_claim_28_day_only(self):
        self.info["access"]["hyperparameter_optimization"] = [
            {"dataset": "fixture-v1", "series": "A", "start": 1, "stop": 29}
        ]
        with self.assertRaisesRegex(ValueError, "extra real information"):
            validate_ledger(self.info, self.policies, self.h)
        self.info["track"] = "rich_data"
        self.assertEqual(
            validate_ledger(self.info, self.policies, self.h)[
                "unique_real_observations"
            ],
            56,
        )

    def test_pooling_requires_label_and_counts_cross_series(self):
        self.info["access"]["cross_series_pooling"] = [
            {"dataset": "fixture-v1", "series": "B", "start": 197, "stop": 225}
        ]
        with self.assertRaises(ValueError):
            validate_ledger(self.info, self.policies, self.h)
        self.info["track"] = "pooled"
        self.assertEqual(
            validate_ledger(self.info, self.policies, self.h)[
                "unique_real_observations"
            ],
            56,
        )

    def test_pretraining_requires_pinned_artifact_and_complete_lineage(self):
        self.info["track"] = "pretrained"
        self.info["access"]["pretraining"] = [
            {"dataset": "fixture-v1", "series": "B", "start": 1, "stop": 197}
        ]
        with self.assertRaises(ValueError):
            validate_ledger(self.info, self.policies, self.h)
        self.info["pretrained_artifacts"] = [
            {"sha256": "a" * 64, "lineage_complete": False}
        ]
        with self.assertRaises(ValueError):
            validate_ledger(self.info, self.policies, self.h)
        self.info["pretrained_artifacts"][0]["lineage_complete"] = True
        self.assertEqual(
            validate_ledger(self.info, self.policies, self.h)[
                "unique_real_observations"
            ],
            224,
        )

    def test_external_source_uses_calendar_dates_not_incomparable_day_indices(self):
        self.info["track"] = "pooled"
        self.info["access"]["cross_series_pooling"] = [
            {"dataset": "later", "series": "B", "start": 1, "stop": 2}
        ]
        policies = self.policies + (
            SourcePolicy("later", "2022-01-01", (Window(1, 100),)),
        )
        with self.assertRaisesRegex(ValueError, "future observations"):
            validate_ledger(self.info, policies, self.h)

    def test_duplicate_unknown_missing_access_and_forged_count_rejected(self):
        cases = []
        bad = copy.deepcopy(self.info)
        bad["history_days"] = 56
        cases.append(bad)
        bad = copy.deepcopy(self.info)
        bad["access"].pop("pretraining")
        cases.append(bad)
        bad = copy.deepcopy(self.info)
        bad["access"]["per_series_history"] *= 2
        cases.append(bad)
        bad = copy.deepcopy(self.info)
        bad["access"]["normalization"] = [
            {"dataset": "unknown", "series": "A", "start": 197, "stop": 225}
        ]
        cases.append(bad)
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate_ledger(case, self.policies, self.h)

    def test_matching_methods_and_mismatched_compute_or_features(self):
        other = copy.deepcopy(self.info)
        other["method"] = "B"
        assert_comparable([self.info, other], self.policies, [self.h, self.h])
        for key, value in [
            ("features", ["sell_price"]),
            ("synthetic_transitions", 1),
            ("track", "known_model_oracle"),
        ]:
            bad = copy.deepcopy(other)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                assert_comparable([self.info, bad], self.policies, [self.h, self.h])

    def test_json_roundtrip_preserves_audited_budget(self):
        result = validate_ledger(read_json(canonical(self.info)), self.policies, self.h)
        self.assertEqual(result["unique_real_observations"], 28)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = make_fixture(self.root)
        self.limits = ReadLimits()
        self.calendar = load_calendar(self.root / "calendar.csv", self.limits)
        self.catalog, _ = load_catalog(
            self.root / "sales_train_evaluation.csv", self.limits
        )
        self.keys = ("FOODS_1_001_CA_1",)

    def change_csv(self, name, change):
        path = self.root / name
        with path.open(newline="") as f:
            rows = list(csv.reader(f))
        change(rows)
        write_csv(path, rows[0], rows[1:])

    def test_selected_history_exact_values_and_no_future_values(self):
        result = load_observations(
            self.root / "sales_train_evaluation.csv",
            self.keys,
            Window(197, 225),
            self.calendar,
            self.limits,
        )
        self.assertEqual(
            tuple(o.sales for o in result[self.keys[0]]),
            tuple(i % 5 for i in range(197, 225)),
        )
        self.assertNotIn(999999, [o.sales for o in result[self.keys[0]]])

    def test_future_cells_cannot_be_accessed_by_history_reader(self):
        with (self.root / "sales_train_evaluation.csv").open(newline="") as f:
            raw = list(csv.reader(f))

        class GuardedRow(list):
            def __getitem__(self, index):
                if isinstance(index, int) and index >= 230:  # index 5+d_225
                    raise AssertionError("future cell accessed")
                return super().__getitem__(index)

        guarded = [raw[0]] + [GuardedRow(row) for row in raw[1:]]
        with patch("inventory_ejor.data.m5.rows", return_value=iter(guarded)):
            load_observations(
                self.root / "sales_train_evaluation.csv",
                self.keys,
                Window(197, 225),
                self.calendar,
                self.limits,
            )

    def test_unrequested_future_malformed_values_do_not_affect_history(self):
        self.change_csv(
            "sales_train_evaluation.csv",
            lambda rows: rows[1].__setitem__(230, "FUTURE_POISON"),
        )
        load_observations(
            self.root / "sales_train_evaluation.csv",
            self.keys,
            Window(197, 225),
            self.calendar,
            self.limits,
        )
        with self.assertRaises(ValueError):
            load_observations(
                self.root / "sales_train_evaluation.csv",
                self.keys,
                Window(225, 253),
                self.calendar,
                self.limits,
            )

    def test_bad_sales_no_clipping_rounding_or_fill(self):
        for cell in ("", "-1", "1.5", "NaN", "inf", "01"):
            self.change_csv(
                "sales_train_evaluation.csv",
                lambda rows, cell=cell: rows[1].__setitem__(202, cell),
            )
            with self.subTest(cell=cell), self.assertRaises(ValueError):
                load_observations(
                    self.root / "sales_train_evaluation.csv",
                    self.keys,
                    Window(197, 225),
                    self.calendar,
                    self.limits,
                )

    def test_missing_duplicate_and_reordered_sales_columns(self):
        for mutate in (
            lambda r: r[0].__setitem__(6, "d_2"),
            lambda r: r[0].__setitem__(1, "id"),
            lambda r: r[1].pop(),
        ):
            make_fixture(self.root)
            self.change_csv("sales_train_evaluation.csv", mutate)
            with self.assertRaises(ValueError):
                load_catalog(self.root / "sales_train_evaluation.csv", self.limits)

    def test_duplicate_and_missing_series_rejected(self):
        self.change_csv("sales_train_evaluation.csv", lambda rows: rows.append(rows[1]))
        with self.assertRaises(ValueError):
            load_catalog(self.root / "sales_train_evaluation.csv", self.limits)
        with self.assertRaises(ValueError):
            load_observations(
                self.root / "sales_train_evaluation.csv",
                self.keys,
                Window(197, 225),
                self.calendar,
                self.limits,
            )
        make_fixture(self.root)
        with self.assertRaises(ValueError):
            load_observations(
                self.root / "sales_train_evaluation.csv",
                ("missing",),
                Window(197, 225),
                self.calendar,
                self.limits,
            )

    def test_chronological_calendar_join_and_missing_dates(self):
        self.assertEqual(self.calendar[225]["date"], "2020-08-12")
        for mutate in (
            lambda r: r[2].__setitem__(0, r[1][0]),
            lambda r: r[2].__setitem__(6, "d_3"),
            lambda r: r.pop(2),
            lambda r: r[2].__setitem__(4, "12"),
        ):
            make_fixture(self.root)
            self.change_csv("calendar.csv", mutate)
            with self.assertRaises(ValueError):
                load_calendar(self.root / "calendar.csv", self.limits)

    def test_overlap_checks_only_history_and_rejects_disagreement(self):
        result = check_overlap(
            self.root / "sales_train_validation.csv",
            self.root / "sales_train_evaluation.csv",
            self.keys,
            Window(197, 225),
            self.calendar,
            self.limits,
        )
        self.assertTrue(result["equal"])
        self.change_csv(
            "sales_train_validation.csv", lambda rows: rows[1].__setitem__(202, "99")
        )
        with self.assertRaisesRegex(ValueError, "disagree"):
            check_overlap(
                self.root / "sales_train_validation.csv",
                self.root / "sales_train_evaluation.csv",
                self.keys,
                Window(197, 225),
                self.calendar,
                self.limits,
            )

    def test_deterministic_selection_independent_of_row_order(self):
        expected = tuple(
            sorted(
                self.catalog,
                key=lambda k: (hashlib.sha256(("17:" + k).encode()).hexdigest(), k),
            )[:2]
        )
        self.assertEqual(rank_candidates(self.catalog, 2, 17), expected)
        reversed_catalog = dict(reversed(list(self.catalog.items())))
        self.assertEqual(rank_candidates(reversed_catalog, 2, 17), expected)

    def test_selection_refuses_future_outcome_window(self):
        observations = load_observations(
            self.root / "sales_train_evaluation.csv",
            self.keys,
            Window(197, 226),
            self.calendar,
            self.limits,
        )[self.keys[0]]
        with self.assertRaises(ValueError):
            eligible(observations, Window(197, 225), 1)
        self.assertTrue(eligible(observations[:-1], Window(197, 225), 1))

    def test_price_alignment_availability_and_missing_joins(self):
        prices = load_prices(
            self.root / "sell_prices.csv",
            self.catalog,
            self.keys,
            ("1028",),
            self.limits,
        )
        key = (self.keys[0], "1028")
        self.assertEqual(prices[key], 2.5)
        features = price_features(
            self.keys[0],
            (197, 198),
            self.calendar,
            prices,
            {key: 204},
            "test-only publication assumption",
        )
        with self.assertRaises(ValueError):
            features_at(features, 198)
        features_at(features, 204)
        with self.assertRaises(ValueError):
            price_features(
                self.keys[0], (197,), self.calendar, prices, {}, "missing publication"
            )
        self.change_csv("sell_prices.csv", lambda rows: rows.append(rows[29]))
        with self.assertRaises(ValueError):
            load_prices(
                self.root / "sell_prices.csv",
                self.catalog,
                self.keys,
                ("1028",),
                self.limits,
            )

    def test_deterministic_calendar_features_exclude_events_and_snap(self):
        features = calendar_features((225,), self.calendar)
        self.assertEqual({f.name for f in features}, {"weekday", "month"})
        self.assertEqual([f.value for f in features], [2, 8])
        features_at(features, 1)

    def test_row_time_series_day_and_selection_limits(self):
        for limits in (
            ReadLimits(max_rows=1),
            ReadLimits(max_series=1),
            ReadLimits(max_days=1),
        ):
            with (
                self.subTest(limits=limits),
                self.assertRaises((RuntimeError, ValueError)),
            ):
                load_catalog(self.root / "sales_train_evaluation.csv", limits)
        limits = ReadLimits()
        limits.started -= 200
        with self.assertRaises(RuntimeError):
            load_calendar(self.root / "calendar.csv", limits)
        with self.assertRaises(ValueError):
            load_observations(
                self.root / "sales_train_evaluation.csv",
                tuple(self.catalog),
                Window(197, 225),
                self.calendar,
                ReadLimits(max_selected=1),
            )

    def test_manifest_integrity_and_input_nonmutation(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        verified = verify_inputs(self.root, self.manifest, self.limits)
        for name, payload in before.items():
            self.assertEqual(
                verified[name]["sha256"], hashlib.sha256(payload).hexdigest()
            )
        load_observations(
            self.root / "sales_train_evaluation.csv",
            self.keys,
            Window(197, 225),
            self.calendar,
            self.limits,
        )
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        bad = copy.deepcopy(self.manifest)
        bad["files"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            verify_inputs(self.root, bad, self.limits)
        bad = copy.deepcopy(self.manifest)
        bad["files"][0]["filename"] = "../outside.csv"
        with self.assertRaises(ValueError):
            verify_inputs(self.root, bad, self.limits)

    def test_end_to_end_deterministic_fingerprints_budgets_and_raw_preservation(self):
        raw = canonical(config())
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        payload, manifest = prepare(self.root, self.manifest, raw)
        again, second = prepare(self.root, self.manifest, raw)
        self.assertEqual(canonical(payload), canonical(again))
        self.assertEqual(manifest, second)
        self.assertEqual(len(payload["training.json"]), 12)
        self.assertEqual(len(payload["evaluation.json"]), 3)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        for entry in manifest["information_budgets"]:
            self.assertEqual(
                entry["validated_counts"]["unique_real_observations"],
                entry["ledger"]["history_days"],
            )
            self.assertEqual(
                entry["validated_counts"]["by_purpose"]["demand_model_fitting"], 0
            )
        for values in payload["training.json"].values():
            self.assertLess(
                max(o["sales"] for o in values["history"]["observations"]), 5
            )
            self.assertLess(values["normalization"]["mean"], 5)
        for values in payload["evaluation.json"].values():
            self.assertEqual({o["sales"] for o in values["observations"]}, {999999})

    def test_future_outcome_changes_cannot_change_cohort_history_or_normalization(self):
        before, _ = prepare(self.root, self.manifest, canonical(config()))
        self.change_csv(
            "sales_train_evaluation.csv",
            lambda rows: [
                row.__setitem__(slice(230, None), ["888888"] * (len(row) - 230))
                for row in rows[1:]
            ],
        )
        after, _ = prepare(self.root, fixture_manifest(self.root), canonical(config()))
        self.assertEqual(before["cohort.json"], after["cohort.json"])
        self.assertEqual(
            canonical(before["training.json"]), canonical(after["training.json"])
        )
        for key in before["training.json"]:
            for field in ("observations", "origin", "series"):
                self.assertEqual(
                    before["training.json"][key]["history"][field],
                    after["training.json"][key]["history"][field],
                )
            self.assertEqual(
                before["training.json"][key]["normalization"],
                after["training.json"][key]["normalization"],
            )

    def test_excluded_series_have_reasons_and_are_not_replaced(self):
        self.change_csv(
            "sales_train_evaluation.csv",
            lambda rows: rows[1].__setitem__(slice(202, 230), ["0"] * 28),
        )
        self.change_csv(
            "sales_train_validation.csv",
            lambda rows: rows[1].__setitem__(slice(202, 230), ["0"] * 28),
        )
        payload, manifest = prepare(
            self.root, fixture_manifest(self.root), canonical(config())
        )
        self.assertEqual(manifest["quality"]["included"], 2)
        self.assertEqual(
            payload["cohort.json"]["excluded"],
            [
                {
                    "series": self.keys[0],
                    "reason": "too_few_positive_sales_in_common_history",
                }
            ],
        )
        self.assertFalse(payload["cohort.json"]["replacement"])

    def test_rolling_cohort_information_is_not_hidden(self):
        cfg = config()
        cfg["origins"] = [225, 253]
        cfg["development_window"]["stop"] = 281
        _, manifest = prepare(self.root, self.manifest, canonical(cfg))
        for entry in manifest["information_budgets"]:
            if (
                entry["ledger"]["origin"] == 253
                and entry["ledger"]["history_days"] == 28
            ):
                self.assertEqual(entry["ledger"]["track"], "rich_data")
                self.assertEqual(
                    entry["validated_counts"]["unique_real_observations"], 56
                )

    def test_one_file_per_learner_budget_and_strict_consumer(self):
        payloads, manifest = prepare(self.root, self.manifest, canonical(config()))
        outputs, dispatch = separate_artifacts(payloads)
        self.assertNotIn("training.json", outputs)
        self.assertEqual(len(dispatch), 12)
        for entry in manifest["information_budgets"]:
            info = entry["ledger"]
            filename = dispatch[entry["token"]]
            path = self.root / filename
            write_exclusive(path, outputs[filename])
            view = load_learner(
                path,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                dataset=info["dataset"],
                series=info["series"],
                origin=info["origin"],
                budget=info["history_days"],
            )
            self.assertEqual(len(view.history.observations), info["history_days"])
            self.assertFalse(hasattr(view, "targets"))
            self.assertFalse(hasattr(view, "reader"))

    def test_consumer_rejects_tampered_normalization_and_wrong_budget(self):
        payloads, _ = prepare(self.root, self.manifest, canonical(config()))
        value = next(iter(payloads["training.json"].values()))
        path = self.root / "learner.json"
        for mutation in (
            "normalization",
            "budget",
            "fingerprint",
            "outcomes",
            "feature",
        ):
            changed = copy.deepcopy(value)
            if mutation == "normalization":
                changed["normalization"]["mean"] = 999999
            if mutation == "outcomes":
                changed["evaluation"] = [999999]
            if mutation == "feature":
                changed["features"][0]["available_day"] = 226
            path.write_bytes(canonical(changed))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                load_learner(
                    path,
                    sha256="0" * 64 if mutation == "fingerprint" else digest,
                    dataset=value["history"]["dataset"],
                    series=value["history"]["series"],
                    origin=225,
                    budget=56 if mutation == "budget" else 28,
                )

    def test_overlap_extension_is_never_counted_twice(self):
        result = check_overlap(
            self.root / "sales_train_validation.csv",
            self.root / "sales_train_evaluation.csv",
            self.keys,
            Window(245, 260),
            self.calendar,
            self.limits,
        )
        self.assertEqual(result["checked_window"], [245, 253])
        result = check_overlap(
            self.root / "sales_train_validation.csv",
            self.root / "sales_train_evaluation.csv",
            self.keys,
            Window(253, 260),
            self.calendar,
            self.limits,
        )
        self.assertIsNone(result["equal"])


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        raw = self.root / "data/raw/m5"
        raw.mkdir(parents=True)
        original = make_fixture(raw)
        meta = self.root / "data/manifests"
        meta.mkdir()
        (meta / "m5_verified_20261017.json").write_bytes(canonical(original))
        self.output = self.root / "data/processed/run"
        self.output.mkdir(parents=True)
        payloads, self.manifest = prepare(raw, original, canonical(config()))
        payloads, dispatch = separate_artifacts(payloads)
        self.manifest["learner_dispatch"] = dispatch
        self.manifest["artifacts"] = {}
        for name, value in payloads.items():
            payload = canonical(value)
            (self.output / name).write_bytes(payload)
            self.manifest["artifacts"][name] = {
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        (self.output / "manifest.json").write_bytes(canonical(self.manifest))
        spec = importlib.util.spec_from_file_location(
            "independent_m3_audit", ROOT / "scripts/audit_m3.py"
        )
        self.auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.auditor)
        self.auditor.ROOT = self.root

    def test_independent_csv_audit_and_repeat(self):
        result = self.auditor.audit(self.output, self.output)
        self.assertEqual(result["learner_views_verified"], 12)
        self.assertEqual(result["unique_selected_history_cells"], 672)
        self.assertEqual(result["unique_development_outcome_cells"], 84)
        self.assertEqual(result["repeat_artifacts_identical"], 14)

    def test_independent_audit_detects_false_normalization_even_with_new_hash(self):
        name = next(iter(self.manifest["learner_dispatch"].values()))
        path = self.output / name
        value = json.loads(path.read_bytes())
        value["normalization"]["mean"] = 999999
        path.write_bytes(canonical(value))
        self.manifest["artifacts"][name] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        (self.output / "manifest.json").write_bytes(canonical(self.manifest))
        with self.assertRaisesRegex(ValueError, "normalization mean mismatch"):
            self.auditor.audit(self.output)

    def test_independent_audit_rejects_double_counted_study_screening(self):
        self.manifest["study_information"]["counts"][
            "unique_historical_sales_cells"
        ] += 84
        (self.output / "manifest.json").write_bytes(canonical(self.manifest))
        with self.assertRaisesRegex(
            ValueError, "study-wide information counts mismatch"
        ):
            self.auditor.audit(self.output)

    def test_independent_audit_rejects_incorrect_logical_version_binding(self):
        self.manifest["learner_dataset_version"] = "different-release"
        (self.output / "manifest.json").write_bytes(canonical(self.manifest))
        with self.assertRaisesRegex(
            ValueError, "logical dataset version/config mismatch"
        ):
            self.auditor.audit(self.output)


class ConfigurationTests(unittest.TestCase):
    def test_malformed_configs_rejected(self):
        cases = []
        for key, value in [
            ("mode", "final_test"),
            ("candidate_count", True),
            ("seed", -1),
            ("budgets", [28, 56]),
            ("origins", [225, 226]),
            ("calendar_features", 1),
            ("min_nonzero", 29),
        ]:
            bad = config()
            bad[key] = value
            cases.append(bad)
        bad = config()
        bad["extra"] = 1
        cases.append(bad)
        bad = config()
        bad["limits"]["max_selected"] = 100
        cases.append(bad)
        bad = config()
        bad["limits"]["max_seconds"] = 121
        cases.append(bad)
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                parse_config(canonical(case))
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b"[]", b"{"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_config(raw)

    def test_cli_bad_config_fails_before_data_access(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text("{}")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/prepare_m3.py"),
                    "--config",
                    str(path),
                    "--seed",
                    "0",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("M3 config requires exactly", result.stderr)
            self.assertEqual(result.stdout, "")

    def test_exclusive_artifact_writes_preserve_previous_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "manifest.json"
            write_exclusive(p, {"a": 1})
            with self.assertRaises(FileExistsError):
                write_exclusive(p, {"a": 2})
            self.assertEqual(json.loads(p.read_bytes()), {"a": 1})

    def test_synthetic_generation_known_support_and_separate_information(self):
        a, record = sample_iid((0, 2), (0.5, 0.5), 28, 17)
        self.assertEqual((a, record), sample_iid((0, 2), (0.5, 0.5), 28, 17))
        self.assertLessEqual(set(a), {0, 2})
        self.assertEqual(record["real_observations"], 0)
        self.assertEqual(record["synthetic_observations"], 28)
        self.assertEqual(sample_iid((3,), (1,), 2, 0)[0], (3, 3))
        for args in (
            ((-1,), (1,), 1, 0),
            ((0,), (0.5,), 1, 0),
            ((0,), (1,), 10001, 0),
            ((0,), (1,), 1, True),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                sample_iid(*args)


if __name__ == "__main__":
    unittest.main()
