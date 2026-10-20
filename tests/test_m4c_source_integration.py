"""Actual staged CSV adapters, with miniature synthetic files only."""

from __future__ import annotations

import copy
import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from m3_fixtures import fixture_manifest, make_fixture, write_csv
from test_m4c_firewall import configuration, synthetic_records

from inventory_ejor.data.protocol import M5_EVALUATION_SHA256
from inventory_ejor.data.provenance import canonical, fingerprint
from inventory_ejor.data.releases import release_template
from inventory_ejor.data.staged import (
    learner_payload,
    prepare_evaluation,
    prepare_learner,
    select_cohort,
)
from inventory_ejor.data.staged_source import M5EvaluatorSource, M5HistorySource


class StagedSourceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="m4c-synthetic-adapter-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.raw = root / "csv"
        self.manifest = make_fixture(self.raw)
        self.spec = root / "analysis.txt"
        self.spec.write_text("synthetic prespecified analysis only\n")
        self.catalog = tuple(f"FOODS_1_00{i}_CA_1" for i in range(1, 4))
        self.cfg = configuration()
        self.cfg["cohort"]["catalog_sha256"] = fingerprint(sorted(self.catalog))
        self.freeze, self.selection, self.calibration = synthetic_records(self.cfg)
        self.freeze.update(
            source_manifest_sha256=fingerprint(self.manifest),
            analysis_spec_sha256=hashlib.sha256(self.spec.read_bytes()).hexdigest(),
        )
        self.selection["freeze_sha256"] = fingerprint(self.freeze)
        self.calibration.update(
            freeze_sha256=fingerprint(self.freeze),
            selection_sha256=fingerprint(self.selection),
        )
        self.series = select_cohort(self.cfg, self.catalog)[0]

    def source(self, cls=M5HistorySource):
        return cls(self.raw, self.manifest, analysis_spec_path=self.spec)

    def release(self, capability="learner_history"):
        result = release_template(
            self.cfg,
            "final_test",
            23,
            2 if capability == "learner_history" else None,
            capability,
            fingerprint(list(select_cohort(self.cfg, self.catalog))),
        )
        result.update(
            approved=True,
            approved_by_owner="SYNTHETIC TEST ONLY",
            decision_record="synthetic:release",
            freeze_sha256=fingerprint(self.freeze),
            selection_sha256=fingerprint(self.selection),
            calibration_sha256=fingerprint(self.calibration),
        )
        return result

    def prepare_history(self, source):
        return prepare_learner(
            self.cfg,
            self.freeze,
            self.release(),
            catalog=self.catalog,
            series=self.series,
            phase="final_test",
            origin=23,
            budget=2,
            source=source,
            selection=self.selection,
            calibration=self.calibration,
        )

    def test_actual_csv_learner_and_scorer_paths_are_separate(self):
        with patch(
            "inventory_ejor.data.staged_source._live_code",
            return_value=("b" * 40, False),
        ):
            view, receipt = self.prepare_history(self.source())
            self.assertEqual([o.day for o in view.history.observations], [21, 22])
            self.assertEqual(receipt["validated_counts"]["unique_real_observations"], 2)
            target, scorer_receipt = prepare_evaluation(
                self.cfg,
                self.freeze,
                self.release("evaluation_outcomes"),
                catalog=self.catalog,
                series=self.series,
                phase="final_test",
                origin=23,
                source=self.source(M5EvaluatorSource),
                selection=self.selection,
                calibration=self.calibration,
            )
            self.assertEqual([o.day for o in target.observations], [23, 24])
            self.assertEqual(
                scorer_receipt["source_manifest_sha256"], fingerprint(self.manifest)
            )
        self.assertFalse(hasattr(self.source(), "read_evaluation"))
        self.assertFalse(hasattr(self.source(M5EvaluatorSource), "read_history"))

    def test_dirty_or_changed_code_refused_before_raw_hashing(self):
        for live in (("c" * 40, False), ("b" * 40, True)):
            with (
                self.subTest(live=live),
                patch(
                    "inventory_ejor.data.staged_source._live_code", return_value=live
                ),
                patch(
                    "inventory_ejor.data.staged_source.verify_inputs",
                    side_effect=AssertionError("unsafe raw read"),
                ) as spy,
            ):
                with self.assertRaisesRegex(ValueError, "Live code"):
                    self.prepare_history(self.source())
                spy.assert_not_called()

    def test_analysis_spec_mutation_and_symlink_refused_before_raw(self):
        source = self.source()
        self.spec.write_text("changed after approval")
        with (
            patch(
                "inventory_ejor.data.staged_source._live_code",
                return_value=("b" * 40, False),
            ),
            patch(
                "inventory_ejor.data.staged_source.verify_inputs",
                side_effect=AssertionError("unsafe raw read"),
            ) as spy,
        ):
            with self.assertRaisesRegex(ValueError, "specification changed"):
                self.prepare_history(source)
            replacement = self.spec.with_name("other.txt")
            replacement.write_text("synthetic prespecified analysis only\n")
            self.spec.unlink()
            self.spec.symlink_to(replacement)
            with self.assertRaisesRegex(ValueError, "Noncanonical analysis"):
                self.prepare_history(source)
            spy.assert_not_called()

    def test_real_source_identity_cannot_be_relabelled_as_fixture(self):
        # Only metadata changes; no actual M5 file is created or opened.
        manifest = copy.deepcopy(self.manifest)
        for entry in manifest["files"]:
            if entry["filename"] == "sales_train_evaluation.csv":
                entry["sha256"] = M5_EVALUATION_SHA256
        source = M5HistorySource(self.raw, manifest, analysis_spec_path=self.spec)
        with patch(
            "inventory_ejor.data.staged_source.verify_inputs",
            side_effect=AssertionError("unsafe raw read"),
        ) as spy:
            with self.assertRaisesRegex(ValueError, "masquerade"):
                source.verify_freeze(self.cfg, self.freeze)
            spy.assert_not_called()

    def test_raw_leaf_symlink_and_mutation_refused(self):
        source = self.source()
        with patch(
            "inventory_ejor.data.staged_source._live_code",
            return_value=("b" * 40, False),
        ):
            path = self.raw / "calendar.csv"
            actual = path.with_name("actual-calendar.csv")
            path.rename(actual)
            path.symlink_to(actual)
            with self.assertRaisesRegex(ValueError, "Noncanonical source"):
                self.prepare_history(source)
            path.unlink()
            actual.rename(path)
            path.write_text("changed")
            with self.assertRaisesRegex(ValueError, "checksum/size mismatch"):
                self.prepare_history(source)

    def test_future_csv_cell_cannot_change_complete_learner_payload(self):
        with patch(
            "inventory_ejor.data.staged_source._live_code",
            return_value=("b" * 40, False),
        ):
            before, old_receipt = self.prepare_history(self.source())
            path = self.raw / "sales_train_evaluation.csv"
            with path.open(newline="") as stream:
                rows = list(csv.reader(stream))
            rows[1][rows[0].index("d_24")] = "777777"
            write_csv(path, rows[0], rows[1:])
            with self.assertRaisesRegex(ValueError, "checksum/size mismatch"):
                self.prepare_history(self.source())
            # Fresh SYNTHETIC approvals bind changed bytes; learner identity
            # and data still must not depend on this withheld sales cell.
            self.manifest = fixture_manifest(self.raw)
            self.freeze["source_manifest_sha256"] = fingerprint(self.manifest)
            self.selection["freeze_sha256"] = fingerprint(self.freeze)
            self.calibration.update(
                freeze_sha256=fingerprint(self.freeze),
                selection_sha256=fingerprint(self.selection),
            )
            after, new_receipt = self.prepare_history(self.source())
            self.assertEqual(
                canonical(learner_payload(before)), canonical(learner_payload(after))
            )
            self.assertNotEqual(
                old_receipt["release_sha256"], new_receipt["release_sha256"]
            )


if __name__ == "__main__":
    unittest.main()
