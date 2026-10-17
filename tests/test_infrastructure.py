"""Workflow tests only; scientific tests are added in later milestones."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

check = load('check_project', ROOT/'scripts/check_project.py')
runner = load('run_experiment', ROOT/'scripts/run_experiment.py')

class InfrastructureTests(unittest.TestCase):
    def test_repository_and_citations(self):
        errors, entries, cited = check.validate(ROOT)
        self.assertEqual(errors, [])
        self.assertGreater(entries,0)
        self.assertGreater(cited,0)

    def test_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            errors,_,_ = check.validate(Path(directory))
            self.assertTrue(any('Missing:' in e for e in errors))

    def test_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sample'
            path.write_bytes(b'inventory')
            self.assertEqual(runner.sha256(path),hashlib.sha256(b'inventory').hexdigest())

    def test_manifest_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'manifest.json'
            runner.write_json(path,{'seed':3})
            self.assertEqual(json.loads(path.read_text()),{'seed':3})
            self.assertFalse(path.with_suffix('.json.tmp').exists())

    def test_invalid_timeout(self):
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/run_experiment.py'),
            '--config',str(ROOT/'experiments/configs/smoke.json'),'--seed','0','--timeout','0'],
            capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(proc.returncode,2)
        self.assertIn('timeout must be positive',proc.stderr)

    def test_dirty_research_override(self):
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/run_experiment.py'),
            '--config',str(ROOT/'experiments/configs/smoke.json'),'--seed','0',
            '--kind','research','--allow-dirty'],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(proc.returncode,2)
        self.assertIn('restricted to smoke',proc.stderr)

if __name__=='__main__':
    unittest.main()
