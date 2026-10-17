"""Offline guards for the M5/Favorita dataset acquisition tools.

No public data downloads, network calls or Kaggle credentials needed in CI.
These checks do not replace validation of the actual acquired raw CSVs.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m5 = load_module("fetch_m5_test", "fetch_m5.py")
favorita = load_module("fetch_favorita_test", "fetch_favorita.py")


class DatasetSourceTests(unittest.TestCase):
    def test_m5_fixed_expected_metadata(self):
        self.assertEqual(len(m5.FILES), 5)
        self.assertEqual(sum(size for size, _ in m5.FILES.values()), 450472284)
        self.assertEqual(m5.RECORD, "10203108")
        self.assertEqual(m5.FILES["sales_train_validation.csv"][0], 120007726)

    def test_m5_checksum_rejects_invalid_content(self):
        with tempfile.TemporaryDirectory() as directory:
            f = Path(directory) / "calendar.csv"
            f.write_bytes(b"not the official M5 calendar data\n")
            with self.assertRaisesRegex(ValueError, "integrity mismatch"):
                m5.validate(f, "calendar.csv")

    def test_favorita_is_correct_original_competition(self):
        self.assertEqual(favorita.COMPETITION, "favorita-grocery-sales-forecasting")
        self.assertEqual(len(favorita.EXPECTED), 8)
        self.assertIn("train.csv.7z", favorita.EXPECTED)
        self.assertIn("items.csv.7z", favorita.EXPECTED)

    def test_favorita_archive_completeness_and_crc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / favorita.ZIP.name
            # Offline stand-in archive: tests structural manifest and ZIP CRC only.
            with ZipFile(archive_path, mode="w") as zf:
                for name in favorita.EXPECTED:
                    zf.writestr(name, b"synthetic test bytes")
            with patch.object(favorita, "DEST", root), patch.object(
                favorita, "ZIP", archive_path
            ):
                status = favorita.inspect()
                self.assertEqual(status["zip_status"], "complete_directory")
                self.assertEqual(favorita.verify(), 0)
                record = json.loads((root / "manifest.json").read_text())
                self.assertEqual(len(record["members"]), 8)
                self.assertTrue(record["verified"])

    def test_missing_credentials_never_triggers_network(self):
        with patch.object(favorita, "credentials_present", return_value=False):
            self.assertEqual(favorita.download(60), 2)


if __name__ == "__main__":
    unittest.main()
