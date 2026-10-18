"""Preparation-only tests. NEVER fit models, score policies, or touch CUDA.

M3 miniature data preparation is used solely to test file/interface contracts.
Numerical baseline tests are separately opt-in and are NOT run in this task.
"""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from m3_fixtures import config as m3_config
from m3_fixtures import make_fixture

from inventory_ejor.baselines import launcher
from inventory_ejor.baselines.planning import (
    approval_template,
    build_plan,
    check_approval,
    check_live_plan,
    digest,
    encode,
    inside,
    validate_config,
    worker_env,
)
from inventory_ejor.data.preparation import prepare
from inventory_ejor.data.provenance import fingerprint
from inventory_ejor.data.views import separate_artifacts

ROOT = Path(__file__).resolve().parents[1]


def baseline_config():
    return json.loads(
        (ROOT / "experiments/configs/m4_baseline_preview.json").read_text()
    )


class M4PreparationContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="m4-contract-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        raw = self.root / "raw-fixture"
        original = make_fixture(raw)
        payload, manifest = prepare(raw, original, encode(m3_config()))
        payload, dispatch = separate_artifacts(payload)
        manifest["learner_dispatch"] = dispatch
        manifest["artifacts"] = {
            name: {"sha256": fingerprint(value), "bytes": len(encode(value))}
            for name, value in payload.items()
        }
        self.bundle = self.root / "data/processed/fixture"
        self.bundle.mkdir(parents=True)
        for name, value in payload.items():
            (self.bundle / name).write_bytes(encode(value))
        (self.bundle / "manifest.json").write_bytes(encode(manifest))
        self.config = baseline_config()
        self.config["prepared_bundle"] = "data/processed/fixture"
        self.config_path = self.root / "config.json"
        self.config_path.write_bytes(encode(self.config))

    def build(self):
        with (
            patch(
                "inventory_ejor.baselines.planning.git_state",
                return_value={
                    "commit": "fixture-commit",
                    "branch": "fixture",
                    "dirty": True,
                },
            ),
            patch(
                "inventory_ejor.baselines.planning.execution_sources",
                return_value={"fixture.py": "abc"},
            ),
        ):
            return build_plan(self.root, self.config_path)

    def test_plan_only_has_expected_jobs_and_no_fit(self):
        plan = self.build()
        self.assertEqual(
            len(plan["jobs"]), 48
        )  # 3 fixture series x 4 budgets x 4 methods
        self.assertEqual(plan["summary"]["devices"], {"cpu": 24, "gpu": 24})
        self.assertEqual(plan["summary"]["gpu_ids"], [0, 1, 2, 3])
        self.assertFalse(plan["summary"]["training_executed"])
        self.assertFalse(plan["summary"]["baseline_scoring_executed"])
        self.assertEqual(len({j["id"] for j in plan["jobs"]}), 48)

    def test_preparation_does_not_modify_any_fixture_data(self):
        paths = list(self.bundle.iterdir())
        before = {p.name: p.read_bytes() for p in paths}
        self.build()
        self.assertEqual(before, {p.name: p.read_bytes() for p in paths})

    def test_old_schema_rejected(self):
        p = self.bundle / "manifest.json"
        value = json.loads(p.read_text())
        value["schema_version"] = 1
        p.write_bytes(encode(value))
        with self.assertRaisesRegex(ValueError, "schema-2"):
            self.build()

    def test_changed_learner_rejected(self):
        p = next(self.bundle.glob("learner-*.json"))
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.build()

    def test_duplicate_gpu_and_unimplemented_method_rejected(self):
        for key, value in (("methods", ["DCL"]), ("budgets", [7]), ("seeds", [0, 0])):
            c = copy.deepcopy(self.config)
            c[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_config(c)
        c = copy.deepcopy(self.config)
        c["resources"]["gpu_ids"] = [0, 0]
        with self.assertRaises(ValueError):
            validate_config(c)

    def test_config_cannot_authorize_execution(self):
        c = copy.deepcopy(self.config)
        c["run_authorized"] = True
        with self.assertRaisesRegex(ValueError, "nonauthorizing"):
            validate_config(c)

    def test_changed_terminal_and_wrong_pipeline_rejected(self):
        for field, value in (
            ("additional_terminal_value", 1),
            ("initial_pipeline", []),
        ):
            c = copy.deepcopy(self.config)
            c["scenario"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_config(c)

    def test_job_cap_prevents_hidden_large_sweep(self):
        self.config["resources"]["max_jobs"] = 2
        self.config_path.write_bytes(encode(self.config))
        with self.assertRaisesRegex(ValueError, "job count"):
            self.build()

    def test_default_approval_denied(self):
        plan = self.build()
        a = approval_template(plan)
        self.assertEqual(a["plan_sha256"], digest(plan))
        with self.assertRaises(PermissionError):
            check_approval(plan, a)

    def test_every_execution_gate_required(self):
        plan = self.build()
        a = approval_template(plan)
        for key in (
            "approved",
            "allow_model_fitting",
            "allow_baseline_scoring",
            "allow_gpu",
            "numerical_validation_completed",
        ):
            a[key] = True
        a["approved_by_owner"] = "test-only fictitious permission, never used to run"
        check_approval(plan, a)
        for key in (
            "approved",
            "allow_model_fitting",
            "allow_baseline_scoring",
            "allow_gpu",
            "numerical_validation_completed",
        ):
            b = copy.deepcopy(a)
            b[key] = False
            with self.subTest(key=key), self.assertRaises(PermissionError):
                check_approval(plan, b)
        changed = copy.deepcopy(plan)
        changed["jobs"][0]["seed"] = 123
        with self.assertRaisesRegex(PermissionError, "exact plan"):
            check_approval(changed, a)

    def test_dirty_sources_cannot_execute(self):
        plan = self.build()
        with patch(
            "inventory_ejor.baselines.planning.git_state", return_value=plan["git"]
        ):
            with self.assertRaisesRegex(PermissionError, "clean-source"):
                check_live_plan(self.root, plan)

    def test_dry_run_does_not_dispatch_workers(self):
        plan_path = self.root / "plan.json"
        plan_path.write_bytes(encode(self.build()))
        with (
            patch.object(launcher, "dispatch") as dispatch,
            redirect_stdout(io.StringIO()) as stream,
        ):
            self.assertEqual(launcher.main(["--plan", str(plan_path)]), 0)
            dispatch.assert_not_called()
            output = json.loads(stream.getvalue())
            self.assertEqual(output["mode"], "DRY_RUN_ONLY")
            self.assertEqual(output["models_fitted"], 0)
            self.assertEqual(output["baselines_scored"], 0)
            self.assertIn("no baseline execution is approved", output["note"])

    def test_execute_without_approval_never_starts_worker(self):
        path = self.root / "plan.json"
        path.write_bytes(encode(self.build()))
        with (
            patch.object(launcher, "dispatch") as dispatch,
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(launcher.main(["--plan", str(path), "--execute"]), 2)
            dispatch.assert_not_called()

    def test_cpu_and_gpu_isolation_leaves_parent_environment_unchanged(self):
        parent = {"CUDA_VISIBLE_DEVICES": "7", "SENTINEL": "keep"}
        cpu = worker_env(parent, "cpu", 0, 2)
        gpu = worker_env(parent, "gpu", 3, 2)
        self.assertEqual(cpu["CUDA_VISIBLE_DEVICES"], "")
        self.assertEqual(gpu["CUDA_VISIBLE_DEVICES"], "3")
        self.assertEqual(parent["CUDA_VISIBLE_DEVICES"], "7")
        self.assertEqual(gpu["OMP_NUM_THREADS"], "2")

    def test_path_traversal_and_symlink_refused(self):
        with self.assertRaises(ValueError):
            inside(self.root, "../outside")
        outside = self.root / "outside"
        outside.mkdir()
        link = self.root / "data/processed/link"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            inside(self.root, "data/processed/link/file", "data/processed")

    def test_manifest_records_equal_evaluation_origin_for_all_budgets(self):
        plan = self.build()
        for j in plan["jobs"]:
            self.assertEqual(j["origin"], 225)
            self.assertEqual(j["horizon"], 28)
            self.assertIn(j["budget"], (28, 56, 112, 224))
            self.assertNotIn("outcomes", j)
            self.assertNotIn("observations", j)

    def test_duplicate_split_identity_is_rejected(self):
        path = self.bundle / "manifest.json"
        obj = json.loads(path.read_text())
        obj["splits"].append(copy.deepcopy(obj["splits"][0]))
        path.write_bytes(encode(obj))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.build()

    def test_shifted_evaluator_origin_is_rejected_before_fitting(self):
        path = self.bundle / "manifest.json"
        obj = json.loads(path.read_text())
        obj["splits"][0]["evaluation"]["start"] += 1
        path.write_bytes(encode(obj))
        with self.assertRaisesRegex(ValueError, "boundary"):
            self.build()

    def test_each_series_requires_every_requested_budget(self):
        path = self.bundle / "manifest.json"
        obj = json.loads(path.read_text())
        token = next(t for t in obj["learner_dispatch"] if t.endswith("/n28"))
        del obj["learner_dispatch"][token]
        obj["splits"] = [row for row in obj["splits"] if row["token"] != token]
        obj["information_budgets"] = [
            row for row in obj["information_budgets"] if row["token"] != token
        ]
        path.write_bytes(encode(obj))
        with self.assertRaisesRegex(ValueError, "matched budgets"):
            self.build()

    def test_boolean_schema_version_is_not_an_integer_version(self):
        c = copy.deepcopy(self.config)
        c["schema_version"] = True
        with self.assertRaises(ValueError):
            validate_config(c)

    def test_plan_builder_does_not_import_numerical_models(self):
        import builtins

        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name in ("torch", "gpytorch") or name.endswith(
                ("models", "controllers")
            ):
                raise AssertionError("Preparation attempted to import numerical code")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guarded_import):
            plan = self.build()
        self.assertFalse(plan["summary"]["training_executed"])

    def test_idle_gpu_mapping_uses_uuid_without_gpu_access(self):
        text = "0, GPU-first, 24576, 15, 0\n3, GPU-fourth, 24576, 15, 0\n"
        found = launcher.parse_idle_gpu_inventory(text, [0, 3], 0.7)
        self.assertEqual(found, {0: "GPU-first", 3: "GPU-fourth"})
        env = worker_env({}, "gpu", found[3], 2)
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "GPU-fourth")

    def test_busy_or_missing_gpu_is_refused_without_killing_anything(self):
        for text in (
            "0, GPU-first, 24576, 16000, 0\n",
            "0, GPU-first, 24576, 15, 95\n",
            "0, GPU-first, 24576, nan, 0\n",
            "1, GPU-other, 24576, 15, 0\n",
        ):
            with self.subTest(text=text), self.assertRaises(RuntimeError):
                launcher.parse_idle_gpu_inventory(text, [0], 0.7)


if __name__ == "__main__":
    unittest.main()
