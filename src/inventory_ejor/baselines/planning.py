"""Prepare and validate baseline jobs without importing any numerical model.

No torch import, GPU access, fitting, policy evaluation or process launch here.
Full-source identities remain in trusted plans, never model inputs.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
from collections import Counter
from pathlib import Path

from inventory_ejor.data.budgets import SourcePolicy, validate_ledger
from inventory_ejor.data.contracts import Window
from inventory_ejor.data.views import load_learner

METHODS = {
    "empirical_base_stock": "cpu",
    "gamma_poisson_base_stock": "cpu",
    "gp_base_stock": "gpu",
    "gp_rollout": "gpu",
}
BUDGETS = (28, 56, 112, 224)
SCRIPT_NAMES = (
    "scripts/prepare_baselines.py",
    "scripts/run_baselines.py",
    "scripts/baseline_worker.py",
    "scripts/start_baselines.py",
    "scripts/run_experiment.py",
    "scripts/validate_baseline_numerics.py",
    "tests/validation_m4_numerics.py",
    "environment/requirements-lock.txt",
)


def encode(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    from inventory_ejor.data.provenance import read_json as strict_json

    return strict_json(Path(path).read_bytes())


def inside(root, relative, prefix=None):
    """Only canonical relative paths; reject traversal and symlink escapes."""
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Only repository-relative paths are allowed")
    raw = root / rel
    real = raw.resolve()
    if real != raw or root not in real.parents:
        raise ValueError("Symlink/noncanonical artifact path")
    if prefix is not None and (root / prefix) not in real.parents:
        raise ValueError(f"Path must be strictly below {prefix}")
    return real


def _int(value, label, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer in [{low}, {high}]")


def _real(value, label, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{label} out of range")


def validate_config(c):
    expected = {
        "schema_version",
        "purpose",
        "prepared_bundle",
        "budgets",
        "seeds",
        "methods",
        "scenario",
        "base_stock_levels",
        "sampling",
        "gamma_poisson",
        "gp",
        "resources",
        "run_authorized",
    }
    if (
        not isinstance(c, dict)
        or set(c) != expected
        or type(c["schema_version"]) is not int
        or c["schema_version"] != 1
    ):
        raise ValueError("Unsupported or incomplete baseline configuration")
    if c["purpose"] != "development_preview_not_publication":
        raise ValueError("Only declared development data are authorized")
    if c["run_authorized"] is not False:
        raise ValueError(
            "Configuration must remain nonauthorizing; use separate approval"
        )
    for name in ("budgets", "seeds", "methods", "base_stock_levels"):
        values = c[name]
        if (
            not isinstance(values, list)
            or not values
            or len(set(values)) != len(values)
        ):
            raise ValueError(f"{name} must be a nonempty unique list")
    if any(type(n) is not int or n not in BUDGETS for n in c["budgets"]):
        raise ValueError("Unsupported history budget")
    for seed in c["seeds"]:
        _int(seed, "seed", 0, 2**31 - 1)
    if any(name not in METHODS for name in c["methods"]):
        raise ValueError("Unimplemented baseline requested (DCL/TED are not included)")
    levels = c["base_stock_levels"]
    for level in levels:
        _int(level, "base-stock level", 0, 10000)
    if sorted(levels) != levels or len(levels) > 256:
        raise ValueError("Level grid must be ordered and contain at most 256 levels")
    s = c["scenario"]
    if set(s) != {
        "lead_time",
        "max_order",
        "initial_on_hand",
        "initial_pipeline",
        "costs",
        "additional_terminal_value",
    }:
        raise ValueError("Unsupported inventory scenario")
    _int(s["lead_time"], "lead time", 1, 28)
    _int(s["max_order"], "order cap", 0, 100)
    _int(s["initial_on_hand"], "initial stock", 0, 10000)
    if (
        not isinstance(s["initial_pipeline"], list)
        or len(s["initial_pipeline"]) != s["lead_time"] - 1
    ):
        raise ValueError("Initial pipeline must contain L-1 future receipts")
    for p in s["initial_pipeline"]:
        _int(p, "pipeline count", 0, 10000)
    if s["additional_terminal_value"] != 0:
        raise ValueError("M1 terminal convention cannot be changed in M4a")
    if set(s["costs"]) != {"holding", "lost_sales", "variable_order", "fixed_order"}:
        raise ValueError("All four scenario cost components are required")
    for k, v in s["costs"].items():
        _real(v, k, 0, 1e6)
    if set(c["sampling"]) != {"tuning_paths", "decision_paths", "max_generated_count"}:
        raise ValueError("Unexpected sampler configuration")
    for k in ("tuning_paths", "decision_paths"):
        _int(c["sampling"][k], k, 2, 4096)
    _int(c["sampling"]["max_generated_count"], "generated count guard", 1, 10**8)
    g = c["gp"]
    if set(g) != {"steps", "learning_rate", "dtype", "noise_floor", "cholesky_jitter"}:
        raise ValueError("Unexpected GP configuration")
    if g["dtype"] != "float64":
        raise ValueError(
            "Numerical reference implementation currently requires float64"
        )
    _int(g["steps"], "GP steps", 1, 500)
    _real(g["learning_rate"], "learning rate", 1e-5, 1)
    _real(g["noise_floor"], "noise floor", 1e-8, 1)
    _real(g["cholesky_jitter"], "GP jitter", 1e-10, 0.1)
    if set(c["gamma_poisson"]) != {"prior_shape", "prior_rate"}:
        raise ValueError("Explicit Gamma prior parameters required")
    for k, v in c["gamma_poisson"].items():
        _real(v, k, 1e-8, 1e8)
    r = c["resources"]
    if set(r) != {
        "gpu_ids",
        "workers_per_gpu",
        "cpu_workers",
        "cpu_threads_per_worker",
        "job_timeout_seconds",
        "max_jobs",
        "gpu_memory_fraction",
        "session_timeout_seconds",
    }:
        raise ValueError("Unexpected resource limits")
    if (
        not isinstance(r["gpu_ids"], list)
        or not r["gpu_ids"]
        or len(set(r["gpu_ids"])) != len(r["gpu_ids"])
    ):
        raise ValueError("GPU IDs must be nonempty and unique")
    for gpu in r["gpu_ids"]:
        _int(gpu, "GPU index", 0, 31)
    if r["workers_per_gpu"] != 1:
        raise ValueError("Exactly one subprocess per selected GPU")
    _int(r["cpu_workers"], "CPU workers", 1, 4)
    _int(r["cpu_threads_per_worker"], "CPU threads per worker", 1, 4)
    _int(r["job_timeout_seconds"], "per-job time cap", 30, 1800)
    _int(r["max_jobs"], "job cap", 1, 1000)
    _int(r["session_timeout_seconds"], "session time cap", 30, 21600)
    _real(r["gpu_memory_fraction"], "GPU memory fraction", 0.1, 0.9)
    return c


def runtime_state():
    """Installed versions, not imports or CUDA initialization."""
    names = ("numpy", "scipy", "torch", "gpytorch", "gymnasium")
    return {
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in names},
    }


def execution_sources(root):
    root = Path(root)
    paths = sorted((root / "src/inventory_ejor").rglob("*.py"))
    paths += [root / n for n in SCRIPT_NAMES]
    return {str(p.relative_to(root)): sha_file(p) for p in paths}


def git_state(root):
    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, timeout=10
        ).strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=all")),
    }


def build_plan(root, config_path):
    """Validate already prepared M3 data; construct jobs, never run them."""
    root = Path(root).resolve()
    config_path = Path(config_path).resolve()
    if root not in config_path.parents:
        raise ValueError("Config must be inside the Git repository")
    cfg = validate_config(read_json(config_path))
    bundle = inside(root, cfg["prepared_bundle"], "data/processed")
    manifest_path = bundle / "manifest.json"
    m = read_json(manifest_path)
    if m.get("schema_version") != 2 or m.get("status") != "prepared_development_demo":
        raise ValueError("Only corrected M3 schema-2 development bundles are allowed")
    if m["config"]["mode"] != "development_demo":
        raise ValueError("No access to final or external holdout is allowed")
    for name, entry in m["artifacts"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe artifact name")
        p = inside(root, str((bundle / name).relative_to(root)), "data/processed")
        if p.stat().st_size != entry["bytes"] or sha_file(p) != entry["sha256"]:
            raise ValueError(f"Prepared artifact integrity mismatch: {name}")
    splits = {x["token"]: x for x in m["splits"]}
    information = {x["token"]: x for x in m["information_budgets"]}
    if (
        len(splits) != len(m["splits"])
        or len(information) != len(m["information_budgets"])
        or set(splits) != set(information)
        or set(splits) != set(m["learner_dispatch"])
    ):
        raise ValueError(
            "Duplicate or inconsistent split/ledger/learner task identities"
        )
    jobs = []
    for token, filename in sorted(m["learner_dispatch"].items()):
        entry = information[token]
        declared = entry["ledger"]
        n = declared["history_days"]
        if n not in cfg["budgets"]:
            continue
        split = splits[token]
        if (
            split["history"]
            != {
                "start": declared["origin"] - n,
                "stop": declared["origin"],
            }
            or split["evaluation"]["start"] != declared["origin"]
            or token != f"{declared['series']}@{declared['origin']}/n{n}"
            or Path(filename).name != filename
            or filename not in m["artifacts"]
        ):
            raise ValueError(
                "Learner/split identity or chronological boundary mismatch"
            )
        horizon = split["evaluation"]["stop"] - split["evaluation"]["start"]
        if not 1 <= horizon <= 56:
            raise ValueError("Only bounded development horizons <=56 are supported")
        view = load_learner(
            bundle / filename,
            sha256=m["artifacts"][filename]["sha256"],
            dataset=m["learner_dataset_version"],
            series=declared["series"],
            origin=declared["origin"],
            budget=n,
        )
        policies = tuple(
            SourcePolicy(
                p["dataset"],
                p["first_date"],
                tuple(Window(**w) for w in p["allowed"]),
                tuple(Window(**w) for w in p["forbidden_outcomes"]),
            )
            for p in entry["validated_counts"]["source_policies"]
        )
        validate_ledger(declared, policies, view.history)
        for method in cfg["methods"]:
            for seed in cfg["seeds"]:
                job = {
                    "method": method,
                    "device_kind": METHODS[method],
                    "seed": seed,
                    "learner_file": str((bundle / filename).relative_to(root)),
                    "learner_sha256": m["artifacts"][filename]["sha256"],
                    "dataset_version": m["learner_dataset_version"],
                    "series": declared["series"],
                    "origin": declared["origin"],
                    "budget": n,
                    "horizon": horizon,
                    "evaluator_file": str(
                        (bundle / "evaluation.json").relative_to(root)
                    ),
                    "evaluator_sha256": m["artifacts"]["evaluation.json"]["sha256"],
                    "evaluation_token": f"{declared['series']}@{declared['origin']}",
                    "history_ledger": copy.deepcopy(declared),
                    "source_policies": entry["validated_counts"]["source_policies"],
                }
                job["id"] = digest(job)[:20]
                jobs.append(job)
    if not jobs or len(jobs) > cfg["resources"]["max_jobs"]:
        raise ValueError("No jobs or proposed job count exceeds explicit cap")
    actual_budgets = {j["budget"] for j in jobs}
    if actual_budgets != set(cfg["budgets"]):
        raise ValueError("Requested budgets not all available in prepared data")
    if len({j["id"] for j in jobs}) != len(jobs):
        raise ValueError("Duplicate job identity")
    cohorts = {(j["series"], j["origin"]) for j in jobs}
    for series, origin in cohorts:
        group = [j for j in jobs if (j["series"], j["origin"]) == (series, origin)]
        observed = {(j["budget"], j["method"], j["seed"]) for j in group}
        expected = {
            (n, method, seed)
            for n in cfg["budgets"]
            for method in cfg["methods"]
            for seed in cfg["seeds"]
        }
        if observed != expected or len({j["horizon"] for j in group}) != 1:
            raise ValueError(
                "Each cohort must have all matched budgets/methods/seeds/horizons"
            )
    plan = {
        "schema_version": 1,
        "status": "prepared_not_authorized_not_executed",
        "config": cfg,
        "config_path": str(config_path.relative_to(root)),
        "config_sha256": sha_file(config_path),
        "bundle_manifest": str(manifest_path.relative_to(root)),
        "bundle_manifest_sha256": sha_file(manifest_path),
        "data_source_fingerprint": m["dataset"],
        "study_information": m["study_information"],
        "git": git_state(root),
        "runtime": runtime_state(),
        "execution_sources": execution_sources(root),
        "jobs": jobs,
        "summary": {
            "jobs": len(jobs),
            "methods": dict(Counter(j["method"] for j in jobs)),
            "devices": dict(Counter(j["device_kind"] for j in jobs)),
            "series": len({j["series"] for j in jobs}),
            "budgets": sorted(actual_budgets),
            "seeds": cfg["seeds"],
            "gpu_ids": cfg["resources"]["gpu_ids"],
            "training_executed": False,
            "baseline_scoring_executed": False,
        },
    }
    return plan


def approval_template(plan):
    return {
        "schema_version": 1,
        "approved": False,
        "allow_model_fitting": False,
        "allow_baseline_scoring": False,
        "allow_gpu": False,
        "numerical_validation_completed": False,
        "approved_by_owner": "",
        "plan_sha256": digest(plan),
        "purpose": "development_preview_only",
    }


def check_approval(plan, approval):
    for key in (
        "approved",
        "allow_model_fitting",
        "allow_baseline_scoring",
        "numerical_validation_completed",
    ):
        if approval.get(key) is not True:
            raise PermissionError(f"Execution is locked: {key} is not approved")
    if (
        any(j["device_kind"] == "gpu" for j in plan["jobs"])
        and approval.get("allow_gpu") is not True
    ):
        raise PermissionError("GPU execution not approved")
    if approval.get("plan_sha256") != digest(plan):
        raise PermissionError("Approval does not bind this exact plan")
    if (
        not isinstance(approval.get("approved_by_owner"), str)
        or not approval["approved_by_owner"].strip()
    ):
        raise PermissionError("Owner approval record is required")
    if approval.get("purpose") != "development_preview_only":
        raise PermissionError("This is not authorization for a publication study")


def check_live_plan(root, plan):
    validate_config(plan["config"])
    now = git_state(root)
    if now["dirty"] or plan["git"]["dirty"] or now["commit"] != plan["git"]["commit"]:
        raise PermissionError(
            "Commit reviewed code, then regenerate and approve a clean-source plan"
        )
    if plan.get("runtime") != runtime_state():
        raise PermissionError("Python/package versions differ from the approved plan")
    if execution_sources(root) != plan["execution_sources"]:
        raise PermissionError("Executable source differs from approved plan")
    for key, hkey in (
        ("config_path", "config_sha256"),
        ("bundle_manifest", "bundle_manifest_sha256"),
    ):
        if sha_file(inside(root, plan[key])) != plan[hkey]:
            raise PermissionError("Approved configuration or data manifest changed")


def worker_env(base_env, device_kind, gpu_id, threads):
    env = dict(base_env)
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id) if device_kind == "gpu" else ""
    env["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    env["OMP_NUM_THREADS"] = str(threads)
    env["MKL_NUM_THREADS"] = str(threads)
    env["OPENBLAS_NUM_THREADS"] = str(threads)
    env["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    env["PYTHONHASHSEED"] = "0"
    return env
