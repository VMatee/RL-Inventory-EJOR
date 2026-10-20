"""The metadata command cannot consume protected inputs or grant access."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_m4c_firewall import configuration


class MetadataCommandTests(unittest.TestCase):
    def setUp(self):
        script = Path(__file__).resolve().parents[1] / "scripts/plan_m4c.py"
        spec = importlib.util.spec_from_file_location("m4c_metadata_cli_test", script)
        self.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.cli)

    def test_valid_metadata_command_only_prints_nonapproving_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "candidate.json"
            config.write_text(json.dumps(configuration()))
            stdout = io.StringIO()
            with patch.object(self.cli, "ROOT", root), redirect_stdout(stdout):
                self.assertEqual(self.cli.main(["--config", str(config)]), 0)
            result = json.loads(stdout.getvalue())
            self.assertFalse(result["plan"]["value_access_authorized"])
            self.assertFalse(result["freeze_template"]["approved"])
            self.assertEqual(list(root.iterdir()), [config])

    def test_protected_config_rejected_without_reading_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for subtree in ("data/raw", "data/processed", "results/runs"):
                path = root / subtree / "synthetic-private.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{"synthetic": 999999}')
                with (
                    self.subTest(subtree=subtree),
                    patch.object(self.cli, "ROOT", root),
                    patch.object(
                        Path, "read_bytes", side_effect=AssertionError("unsafe read")
                    ) as spy,
                    redirect_stderr(io.StringIO()),
                    self.assertRaises(SystemExit),
                ):
                    self.cli.main(["--config", str(path)])
                spy.assert_not_called()

    def test_symlink_config_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            actual = root / "actual.json"
            actual.write_text(json.dumps(configuration()))
            link = root / "link.json"
            link.symlink_to(actual)
            with (
                patch.object(self.cli, "ROOT", root),
                patch.object(
                    Path, "read_bytes", side_effect=AssertionError("unsafe read")
                ) as spy,
                redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                self.cli.main(["--config", str(link)])
            spy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
