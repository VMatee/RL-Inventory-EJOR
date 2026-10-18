"""Whole-artifact noninterference under a single withheld-outcome intervention.

Fixture generation, CSV mutation and byte comparisons are independent of the
production reader, hashing, normalization and information-count implementations.
"""

import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from m3_fixtures import config, fixture_manifest, make_fixture, write_csv

from inventory_ejor.data.budgets import study_information
from inventory_ejor.data.contracts import Window
from inventory_ejor.data.preparation import parse_config, prepare
from inventory_ejor.data.views import load_learner, separate_artifacts


def encoded(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


class NoninterferenceTests(unittest.TestCase):
    def test_single_future_day_226_preserves_complete_learner_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left, right = root / "original", root / "future_changed"
            before_manifest = make_fixture(left)
            make_fixture(right)
            path = right / "sales_train_evaluation.csv"
            with path.open(newline="") as stream:
                rows = list(csv.reader(stream))
            column = rows[0].index("d_226")
            self.assertEqual(rows[1][column], "999999")
            rows[1][column] = "777777"
            write_csv(path, rows[0], rows[1:])
            after_manifest = fixture_manifest(right)
            # Independent intervention check: exactly one CSV cell changed.
            with (left / path.name).open(newline="") as stream:
                original = list(csv.reader(stream))
            self.assertEqual(
                [
                    (r, c)
                    for r in range(len(rows))
                    for c in range(len(rows[r]))
                    if rows[r][c] != original[r][c]
                ],
                [(1, column)],
            )
            for name in (
                "calendar.csv",
                "sales_train_validation.csv",
                "sell_prices.csv",
                "sample_submission.csv",
            ):
                self.assertEqual(
                    (left / name).read_bytes(), (right / name).read_bytes()
                )
            payload_a, trusted_a = prepare(left, before_manifest, encoded(config()))
            with self.assertRaisesRegex(ValueError, "checksum/size mismatch"):
                prepare(right, before_manifest, encoded(config()))
            payload_b, trusted_b = prepare(right, after_manifest, encoded(config()))
            artifacts_a, dispatch_a = separate_artifacts(payload_a)
            artifacts_b, dispatch_b = separate_artifacts(payload_b)
            self.assertEqual(dispatch_a, dispatch_b)
            self.assertEqual(len(dispatch_a), 12)
            for name in dispatch_a.values():
                with self.subTest(artifact=name):
                    a, b = encoded(artifacts_a[name]), encoded(artifacts_b[name])
                    self.assertEqual(a, b)  # Every field, identifier and metadata byte.
                    # Inspect the exact bytes written, not a projection of fields.
                    (left / name).write_bytes(a)
                    (right / name).write_bytes(b)
                    self.assertEqual(
                        (left / name).read_bytes(), (right / name).read_bytes()
                    )
                    self.assertNotIn(trusted_a["dataset"].encode(), a)
                    self.assertNotIn(trusted_b["dataset"].encode(), a)
                    self.assertEqual(
                        artifacts_a[name]["history"]["dataset"],
                        config()["dataset_version"],
                    )
                    self.assertEqual(
                        hashlib.sha256(a).digest(), hashlib.sha256(b).digest()
                    )
            self.assertEqual(
                encoded(payload_a["cohort.json"]), encoded(payload_b["cohort.json"])
            )
            self.assertNotEqual(trusted_a["inputs"], trusted_b["inputs"])
            self.assertNotEqual(trusted_a["dataset"], trusted_b["dataset"])
            changed = payload_b["evaluation.json"]["FOODS_1_001_CA_1@225"][
                "observations"
            ][1]
            self.assertEqual((changed["day"], changed["sales"]), (226, 777777))
            # Only the evaluator's intended sales cell differs.
            repaired = json.loads(encoded(payload_b["evaluation.json"]))
            repaired["FOODS_1_001_CA_1@225"]["observations"][1]["sales"] = 999999
            self.assertEqual(encoded(payload_a["evaluation.json"]), encoded(repaired))

    def test_study_union_is_1204_not_sum_of_budgets_or_screening(self):
        selected = tuple(f"selected_{i}" for i in range(5))
        candidates = selected + ("excluded_0", "excluded_1", "excluded_2")
        windows = [(key, Window(1, 225)) for key in selected]
        # Repeated four budgets and duplicated declarations add no real cells.
        windows += [
            (key, Window(225 - n, 225)) for key in selected for n in (28, 56, 112, 224)
        ]
        study = study_information(
            "fixture-v1",
            "trusted-source",
            windows * 2,
            candidates,
            Window(197, 225),
            100,
        )
        self.assertEqual(
            study["counts"],
            {
                "selected_history_cells": 1120,
                "candidate_screening_cells": 224,
                "screening_already_in_selected_history": 140,
                "additional_screening_cells": 84,
                "unique_historical_sales_cells": 1204,
            },
        )
        self.assertEqual(
            sum(row["unique_historical_sales_cells"] for row in study["by_series"]),
            1204,
        )
        self.assertIn("Ex-post", study["roster_warning"])
        self.assertIn("survivorship", study["roster_warning"])

    def test_preparation_study_ledger_includes_excluded_candidate_only_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_fixture(root)
            for name in ("sales_train_validation.csv", "sales_train_evaluation.csv"):
                with (root / name).open(newline="") as stream:
                    rows = list(csv.reader(stream))
                for day in range(197, 225):
                    rows[1][rows[0].index(f"d_{day}")] = "0"
                write_csv(root / name, rows[0], rows[1:])
            payloads, manifest = prepare(
                root, fixture_manifest(root), encoded(config())
            )
            self.assertEqual(
                manifest["study_information"]["counts"],
                {
                    "selected_history_cells": 448,
                    "candidate_screening_cells": 84,
                    "screening_already_in_selected_history": 56,
                    "additional_screening_cells": 28,
                    "unique_historical_sales_cells": 476,
                },
            )
            self.assertEqual(len(payloads["training.json"]), 8)
            self.assertEqual(
                manifest["study_information"]["source_fingerprint"], manifest["dataset"]
            )

    def test_study_union_deduplicates_overlapping_rolling_histories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = make_fixture(root)
            cfg = config()
            cfg["origins"] = [225, 253]
            cfg["development_window"]["stop"] = 281
            _, output = prepare(root, manifest, encoded(cfg))
            self.assertEqual(
                output["study_information"]["counts"]["unique_historical_sales_cells"],
                756,
            )
            self.assertEqual(
                output["study_information"]["counts"]["additional_screening_cells"], 0
            )

    def test_consumer_keeps_strict_identity_checksum_budget_and_feature_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = make_fixture(root)
            payloads, trusted = prepare(root, source, encoded(config()))
            value = next(iter(payloads["training.json"].values()))
            path = root / "learner.json"
            good = dict(
                dataset=config()["dataset_version"],
                series=value["history"]["series"],
                origin=225,
                budget=28,
            )
            path.write_bytes(encoded(value))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            load_learner(path, sha256=digest, **good)
            for field, wrong in (
                ("dataset", "different-release-v2"),
                ("dataset", trusted["dataset"]),
                ("series", "other"),
                ("origin", 226),
                ("budget", 56),
            ):
                with (
                    self.subTest(field=field, wrong=wrong),
                    self.assertRaises(ValueError),
                ):
                    load_learner(path, sha256=digest, **{**good, field: wrong})
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                load_learner(path, sha256="0" * 64, **good)
            for mutation in (
                "metadata",
                "feature_name",
                "feature_value",
                "feature_evidence",
                "normalization",
            ):
                bad = copy.deepcopy(value)
                if mutation == "metadata":
                    bad["history"]["source_sha256"] = trusted["dataset"]
                elif mutation == "feature_name":
                    bad["features"][0]["name"] = "raw_source_hash"
                elif mutation == "feature_value":
                    bad["features"][0]["value"] = 777777
                elif mutation == "feature_evidence":
                    bad["features"][0]["evidence"] = trusted["dataset"]
                else:
                    bad["normalization"]["mean"] = 777777
                path.write_bytes(encoded(bad))
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    load_learner(
                        path,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        **good,
                    )

    def test_logical_dataset_version_is_required_and_validated(self):
        for version in (None, True, "", 123, "has spaces"):
            cfg = config()
            cfg["dataset_version"] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                parse_config(encoded(cfg))
        cfg = config()
        del cfg["dataset_version"]
        with self.assertRaises(ValueError):
            parse_config(encoded(cfg))


if __name__ == "__main__":
    unittest.main()
