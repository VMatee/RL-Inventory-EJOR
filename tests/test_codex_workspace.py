"""Offline tests for installing Codex entry files without overwriting local work."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("codex_workspace_installer", ROOT / "scripts/install_codex_workspace.py")
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class CodexWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / "github"
        self.templates = self.repo / "infrastructure" / "codex_workspace"
        self.templates.mkdir(parents=True)
        self.code = base / "code"
        self.code.mkdir()
        for name in installer.FILES:
            (self.templates / (name + ".template")).write_text(f"original {name}\n")

    def test_initial_install_and_idempotent_refresh(self):
        changed = installer.deploy(self.repo, self.code)
        self.assertEqual(set(changed), set(installer.FILES))
        self.assertEqual(installer.deploy(self.repo, self.code), [])
        self.assertTrue((self.code / "start_codex.sh").stat().st_mode & 0o100)

    def test_read_only_check_creates_nothing(self):
        self.assertEqual(set(installer.deploy(self.repo, self.code, check=True)), set(installer.FILES))
        self.assertEqual(list(self.code.iterdir()), [])

    def test_changed_template_updates_previously_managed_bytes(self):
        installer.deploy(self.repo, self.code)
        (self.templates / "README.md.template").write_text("new tracked text\n")
        self.assertEqual(installer.deploy(self.repo, self.code), ["README.md"])
        self.assertEqual((self.code / "README.md").read_text(), "new tracked text\n")

    def test_unknown_local_file_blocks_all_writes(self):
        (self.code / "AGENTS.md").write_text("user instructions\n")
        with self.assertRaises(installer.InstallConflict):
            installer.deploy(self.repo, self.code)
        self.assertFalse((self.code / "README.md").exists())
        self.assertEqual((self.code / "AGENTS.md").read_text(), "user instructions\n")

    def test_local_edit_blocks_refresh_and_preserves_other_targets(self):
        installer.deploy(self.repo, self.code)
        (self.code / "CODEX_PROMPT.md").write_text("intentional local edit\n")
        (self.templates / "README.md.template").write_text("new tracked text\n")
        with self.assertRaises(installer.InstallConflict):
            installer.deploy(self.repo, self.code)
        self.assertEqual((self.code / "README.md").read_text(), "original README.md\n")
        self.assertEqual((self.code / "CODEX_PROMPT.md").read_text(), "intentional local edit\n")

    def test_symlink_target_and_duplicate_alias_are_not_overwritten(self):
        external = Path(self.temp.name) / "private.txt"
        external.write_text("keep\n")
        (self.code / "README.md").symlink_to(external)
        with self.assertRaises(installer.InstallConflict):
            installer.deploy(self.repo, self.code)
        self.assertEqual(external.read_text(), "keep\n")
        (self.code / "README.md").unlink()
        (self.code / "agent.md").write_text("old instructions\n")
        with self.assertRaises(installer.InstallConflict):
            installer.deploy(self.repo, self.code)
        self.assertTrue((self.code / "agent.md").exists())

    def test_unrelated_files_and_environment_remain_untouched(self):
        venv = self.code / ".venv"
        venv.mkdir()
        (venv / "marker").write_bytes(b"preserve python environment")
        (self.code / "training.log").write_bytes(b"preserve results")
        installer.deploy(self.repo, self.code)
        self.assertEqual((venv / "marker").read_bytes(), b"preserve python environment")
        self.assertEqual((self.code / "training.log").read_bytes(), b"preserve results")
        wrong = Path(self.temp.name) / "wrong"
        wrong.mkdir()
        with self.assertRaises(installer.InstallConflict):
            installer.deploy(self.repo, wrong)


if __name__ == "__main__":
    unittest.main()
