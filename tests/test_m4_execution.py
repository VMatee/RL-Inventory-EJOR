"""Real subprocess scheduler/timeout tests on synthetic stub outputs only."""

from __future__ import annotations

import io
import json
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from inventory_ejor.baselines.execution import session_lease, verify_artifacts
from inventory_ejor.baselines.launcher import dispatch
from inventory_ejor.baselines.planning import encode, sha_file
from inventory_ejor.baselines.reporting import summarize_session

ROOT = Path(__file__).resolve().parents[1]
STUB = """import argparse,json,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser()
for n in ('plan','approval','job-index','output'): p.add_argument('--'+n,required=True)
a=p.parse_args(); root=Path.cwd(); plan=json.loads(Path(a.plan).read_text())
j=plan['jobs'][int(a.job_index)]; out=root/a.output; out.mkdir()
if j.get('behavior')=='fail': raise SystemExit(7)
if j.get('behavior')=='sleep': time.sleep(10)
if j.get('behavior')=='mutate': (root/'tracked.txt').write_text('changed')
r={'job':j['id'],'method':j['method'],'budget':j['budget'],'series':j['series'],
'status':'completed_development_baseline_requires_review','source_commit':plan['git']['commit'],
 'total_cost':0.0,'total_seconds':0.01,'selected_base_stock':0,
 'base_stock_grid_upper_boundary_selected':False,'order_cap_binding_periods':0}
(out/'result.json').write_text(json.dumps(r))
(out/'private_sales_replay.json').write_text(json.dumps([{'cost':0,'observed_sales_as_requests':0,'fulfilled':0}]))
"""


class ExecutionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="baseline-scheduler-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "results/runs").mkdir(parents=True)
        (self.root / "data/processed/fixture").mkdir(parents=True)
        shutil.copyfile(
            ROOT / "scripts/run_experiment.py", self.root / "scripts/run_experiment.py"
        )
        (self.root / "scripts/baseline_worker.py").write_text(STUB)
        (self.root / ".gitignore").write_text("results/runs/\ndata/processed/\n")
        (self.root / "config.json").write_text("{}")
        (self.root / "tracked.txt").write_text("original")
        for args in (
            ["init", "-q"],
            ["add", "."],
            [
                "-c",
                "user.name=Synthetic test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-qm",
                "synthetic fixture",
            ],
        ):
            subprocess.run(
                ["git", *args],
                cwd=self.root,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        self.plan = {
            "git": {"commit": commit},
            "config_path": "config.json",
            "bundle_manifest": "data/processed/fixture/manifest.json",
            "config": {
                "resources": {
                    "cpu_workers": 2,
                    "gpu_ids": [],
                    "cpu_threads_per_worker": 1,
                    "job_timeout_seconds": 3,
                    "session_timeout_seconds": 20,
                }
            },
            "jobs": [],
        }
        self.bundle = self.root / "data/processed/fixture"
        (self.bundle / "manifest.json").write_text("{}")
        self.approval = self.bundle / "approval.json"
        self.approval.write_text("{}")

    def run_jobs(self, behaviors):
        self.plan["jobs"] = [
            {
                "id": f"synthetic-{i}",
                "method": "stub",
                "device_kind": "cpu",
                "series": "fixture",
                "budget": 28,
                "seed": i,
                "origin": 1,
                "horizon": 1,
                "behavior": value,
            }
            for i, value in enumerate(behaviors)
        ]
        path = self.bundle / "plan.json"
        path.write_bytes(encode(self.plan))
        with redirect_stdout(io.StringIO()):
            result = dispatch(self.root, path, self.approval, self.plan)
        sessions = list((self.root / "results/runs").glob("m4-approved-*"))
        self.assertEqual(len(sessions), 1)
        self.assertFalse((self.root.parent / "code/.baseline_execution.lock").exists())
        return result, sessions[0]

    def test_real_subprocess_success_has_complete_audited_reports(self):
        code, directory = self.run_jobs(["ok"] * 4)
        self.assertEqual(code, 0)
        summary = json.loads((directory / "session_summary.json").read_text())
        self.assertEqual(summary["jobs_finished"], 4)
        self.assertEqual({e["slot"] for e in summary["entries"]}, {0, 1})
        self.assertTrue((directory / "baseline_results.csv").is_file())
        self.assertEqual(summarize_session(self.root, directory)["job_count"], 4)

    def test_existing_lock_creates_no_output_and_is_never_removed(self):
        with session_lease(self.root):
            lock = self.root.parent / "code/.baseline_execution.lock"
            original = lock.read_bytes()
            with self.assertRaises(RuntimeError):
                dispatch(self.root, self.bundle / "unused", self.approval, self.plan)
            self.assertEqual(original, lock.read_bytes())
            self.assertEqual(list((self.root / "results/runs").iterdir()), [])

    def test_failed_job_stops_new_jobs_and_forbids_averaging(self):
        self.plan["config"]["resources"]["cpu_workers"] = 1
        code, directory = self.run_jobs(["fail", "ok", "ok"])
        self.assertNotEqual(code, 0)
        summary = json.loads((directory / "session_summary.json").read_text())
        self.assertEqual(summary["jobs_finished"], 1)
        self.assertEqual(summary["entries"][0]["exit_code"], 7)
        with self.assertRaises(ValueError):
            summarize_session(self.root, directory)

    def test_timeout_does_not_report_success_or_start_more_jobs(self):
        self.plan["config"]["resources"].update(cpu_workers=1, job_timeout_seconds=1)
        code, directory = self.run_jobs(["sleep", "ok"])
        self.assertNotEqual(code, 0)
        summary = json.loads((directory / "session_summary.json").read_text())
        self.assertEqual(summary["jobs_finished"], 1)
        self.assertEqual(summary["entries"][0]["exit_code"], 124)

    def test_session_deadline_reaps_active_wrapper(self):
        self.plan["config"]["resources"].update(
            cpu_workers=1, job_timeout_seconds=15, session_timeout_seconds=1
        )
        start = time.monotonic()
        code, directory = self.run_jobs(["sleep", "ok"])
        self.assertNotEqual(code, 0)
        self.assertLess(time.monotonic() - start, 8)
        summary = json.loads((directory / "session_summary.json").read_text())
        self.assertEqual(summary["jobs_finished"], 1)
        self.assertIn("TimeoutError", summary["error"])

    def test_source_change_invalidates_an_exit_zero_worker(self):
        code, directory = self.run_jobs(["mutate"])
        self.assertNotEqual(code, 0)
        summary = json.loads((directory / "session_summary.json").read_text())
        self.assertIn("source changed", summary["entries"][0]["error"])

    def test_changed_result_hash_is_rejected_by_summary(self):
        _, directory = self.run_jobs(["ok"])
        result = next(directory.glob("synthetic-*/result.json"))
        result.write_bytes(result.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "changed"):
            summarize_session(self.root, directory)

    def test_preflight_rejects_modified_learner_before_start(self):
        source = self.bundle / "learner.json"
        source.write_bytes(b"original")
        plan = {
            "jobs": [
                {
                    "learner_file": "data/processed/fixture/learner.json",
                    "learner_sha256": sha_file(source),
                    "evaluator_file": "data/processed/fixture/learner.json",
                    "evaluator_sha256": sha_file(source),
                }
            ]
        }
        self.assertEqual(verify_artifacts(self.root, plan), 1)
        source.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            verify_artifacts(self.root, plan)

    def test_sigterm_wrapper_reaps_child_process(self):
        command = [
            sys.executable,
            str(self.root / "scripts/run_experiment.py"),
            "--config",
            "config.json",
            "--seed",
            "0",
            "--kind",
            "pilot",
            "--timeout",
            "15",
            "--",
            sys.executable,
            "-c",
            "import time;time.sleep(60)",
        ]
        p = subprocess.Popen(
            command,
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        self.addCleanup(lambda: p.kill() if p.poll() is None else None)
        deadline = time.monotonic() + 8
        child = None
        while time.monotonic() < deadline:
            manifests = list((self.root / "results/runs").glob("*/manifest.json"))
            if manifests:
                data = json.loads(manifests[0].read_text())
                if "pid" in data:
                    child = data["pid"]
                    break
            time.sleep(0.03)
        self.assertIsNotNone(child)
        p.send_signal(signal.SIGTERM)
        p.communicate(timeout=12)
        self.assertEqual(p.returncode, 130)
        self.assertFalse(Path(f"/proc/{child}").exists())
        data = json.loads(manifests[0].read_text())
        self.assertEqual(data["status"], "interrupted")
