"""M4d-0 synthetic-only, least-privilege reference execution prototype.

NOT a real-data executor, not GP/RL training, not an authorization to release
M5 outcomes. A separately approved, reviewed M4d-1 implementation is required
before any real observations may pass through an executor.

The learner stage consumes ONLY a pinned learner artifact and plan. The scorer
receives EvaluationTargets through a separate, already-released scorer path.
All saved values are LOCAL PRIVATE experimental artifacts (never commit).
"""

from __future__ import annotations

import hashlib
import math
import os
import sys
from dataclasses import asdict
from pathlib import Path

from inventory_ejor.data.contracts import EvaluationTargets, Window, exact_keys
from inventory_ejor.data.evidence import EvidenceStore
from inventory_ejor.data.protocol import M5_VERSION, require
from inventory_ejor.data.provenance import canonical, fingerprint, read_json
from inventory_ejor.data.releases import authorize_task
from inventory_ejor.data.staged import (
    learner_payload,
    select_cohort,
    validate_task_ledger,
)
from inventory_ejor.data.views import LearnerView, load_learner
from inventory_ejor.envs import (
    CostParameters,
    InventoryConfig,
    InventoryState,
    transition,
    validate_state,
)

METHOD = "synthetic_empirical_base_stock_reference"
EXPECTED_FILES = (
    "src/inventory_ejor/data/m4d0_execution.py",
    "src/inventory_ejor/data/views.py",
    "src/inventory_ejor/data/staged.py",
    "src/inventory_ejor/data/releases.py",
    "src/inventory_ejor/data/evidence.py",
    "src/inventory_ejor/data/contracts.py",
    "src/inventory_ejor/data/provenance.py",
    "src/inventory_ejor/envs/lost_sales.py",
)
PRIVATE_MAX_BYTES = 8 * 1024 * 1024


class PrivateExecutionStore:
    """Exclusive content-addressed outputs outside versioned Git checkouts.

    Neither the original source nor a released evaluation artifact is a valid
    destination. Refuses symlinked roots and files. NOT tamper-proof against an
    untrusted local OS user with arbitrary filesystem access.
    """

    def __init__(self, directory):
        self.root = Path(directory).absolute()
        require(
            self.root.is_dir() and self.root == self.root.resolve(),
            "Pre-existing canonical private execution directory required",
        )
        require(
            self.root.stat().st_uid == os.getuid()
            and (self.root.stat().st_mode & 0o077) == 0,
            "Private execution directory must be owned by caller with mode 0700",
        )
        # Refuse ALL Git checkouts, including sibling worktrees, not just
        # the checkout containing this module.
        require(
            not any(
                (parent / ".git").exists() for parent in (self.root, *self.root.parents)
            ),
            "Private M4d0 artifacts cannot be written into a Git worktree",
        )

    def _path(self, digest):
        require(
            isinstance(digest, str)
            and len(digest) == 64
            and all(c in "0123456789abcdef" for c in digest),
            "Invalid content hash",
        )
        require(self.root == self.root.resolve(), "Private store root changed")
        path = self.root / (digest + ".json")
        require(
            path.parent == self.root and not path.is_symlink(),
            "Private store symlink/path substitution refused",
        )
        return path

    def put(self, value):
        data = canonical(value)
        require(len(data) <= PRIVATE_MAX_BYTES, "Oversized private artifact")
        digest = hashlib.sha256(data).hexdigest()
        path = self._path(digest)
        if path.exists():
            require(path.read_bytes() == data, "Existing artifact content changed")
        else:
            # Exclusive creation; a partial failure cannot be reported as success.
            descriptor = os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o600,
            )
            with os.fdopen(descriptor, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
        return digest

    def read(self, digest, *, kind=None):
        path = self._path(digest)
        require(
            path.is_file() and path.stat().st_size <= PRIVATE_MAX_BYTES,
            "Missing or oversized private execution artifact",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == digest
            and raw == canonical(read_json(raw)),
            "Private execution artifact modified or noncanonical",
        )
        item = read_json(raw)
        require(
            type(item) is dict and (kind is None or item.get("kind") == kind),
            "Wrong execution artifact kind",
        )
        return item

    def file(self, digest):
        """For the existing bounded, checksum-verifying load_learner() only."""
        self.read(digest)
        return self._path(digest)


def source_hashes():
    """Pin every implementation byte used by this bounded reference run."""
    checkout = Path(__file__).resolve().parents[3]
    hashes = {}
    for relative in EXPECTED_FILES:
        path = checkout / relative
        require(
            path.is_file() and not path.is_symlink(),
            "Missing or symlinked execution dependency",
        )
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def scenario_contract(scenario):
    require(type(scenario) is dict, "Explicit scenario required")
    exact_keys(
        scenario,
        (
            "lead_time",
            "horizon",
            "max_order",
            "initial_on_hand",
            "initial_pipeline",
            "costs",
            "additional_terminal_value",
        ),
        "M4d0 scenario",
    )
    require(
        type(scenario["initial_pipeline"]) is list,
        "Initial pipeline must be a JSON list",
    )
    require(
        scenario["additional_terminal_value"] == 0
        and type(scenario["additional_terminal_value"]) is int,
        "Prototype supports zero salvage only",
    )
    require(type(scenario["costs"]) is dict, "Exact cost specification required")
    exact_keys(
        scenario["costs"],
        ("holding", "lost_sales", "variable_order", "fixed_order"),
        "cost coefficients",
    )
    config = InventoryConfig(
        lead_time=scenario["lead_time"],
        horizon=scenario["horizon"],
        max_order=scenario["max_order"],
        costs=CostParameters(**scenario["costs"]),
    )
    require(
        config.horizon <= 128 and config.lead_time <= 10 and config.max_order <= 100,
        "M4d0 CPU reference scenario exceeds bounded scope",
    )
    state = InventoryState(
        scenario["initial_on_hand"], tuple(scenario["initial_pipeline"])
    )
    validate_state(config, state)
    return config, state


def _reference_target(view, inventory, budget):
    require(
        type(view) is LearnerView and len(view.history.observations) == budget,
        "Reference fitting requires exactly n learner observations",
    )
    mean = math.fsum(o.sales for o in view.history.observations) / budget
    return min(
        inventory.max_order * (inventory.lead_time + 1),
        math.ceil(mean * (inventory.lead_time + 1)),
    )


def _task(config, catalog, phase, origin, budget, series, release, freeze, evidence):
    require(
        config["dataset_version"].startswith("synthetic-")
        and config["dataset_version"] != M5_VERSION,
        "M4d0 intentionally refuses real M5 and non-synthetic data",
    )
    require(phase == "development", "M4d0 supports synthetic development only")
    require(type(evidence) is EvidenceStore, "Persisted evidence required")
    cohort = select_cohort(config, catalog)
    require(series in cohort, "Out-of-cohort series forbidden")
    task = authorize_task(
        config,
        freeze,
        release,
        phase=phase,
        origin=origin,
        budget=budget,
        capability="learner_history",
        cohort_sha256=fingerprint(list(cohort)),
        cohort=cohort,
        evidence=evidence,
    )
    return task, cohort


def _receipt(
    evidence,
    digest,
    release,
    *,
    config,
    freeze,
    cohort,
    series,
    phase,
    origin,
    budget,
    capability,
    window,
):
    require(isinstance(digest, str), "Persisted receipt identity required")
    value = evidence.read(digest)
    require(
        value["kind"] == "staged_access_receipt"
        and value["protocol_sha256"] == fingerprint(config)
        and value["freeze_sha256"] == fingerprint(freeze)
        and value["release_sha256"] == fingerprint(release)
        and value["source_manifest_sha256"] == freeze["source_manifest_sha256"]
        and value["cohort_sha256"] == fingerprint(list(cohort))
        and (
            value["series"],
            value["phase"],
            value["origin"],
            value["budget"],
            value["capability"],
        )
        == (series, phase, origin, budget, capability)
        and value["window"] == asdict(window)
        and value["selection_sha256"] == release["selection_sha256"]
        and value["calibration_sha256"] == release["calibration_sha256"],
        "Receipt is not bound to the exact released data access",
    )
    require(
        evidence.read(value["release_sha256"]) == release,
        "Persisted release identity differs from input",
    )


def publish_learner_only_plan(
    private_store,
    evidence,
    *,
    config,
    freeze,
    release,
    catalog,
    view,
    receipt,
    phase,
    series,
    origin,
    budget,
    scenario,
    seed,
):
    """Trusted preparer -> bounded private input; no evaluator object accepted."""
    require(
        type(private_store) is PrivateExecutionStore,
        "Private M4d0 artifact store required",
    )
    require(
        type(view) is LearnerView and type(receipt) is dict,
        "Only verified learner view and receipt accepted",
    )
    require(
        type(seed) is int and 0 <= seed <= 2**31 - 1,
        "Execution seed must be a bounded nonnegative integer",
    )
    require(seed <= 2**31 - 1, "Seed exceeds bounded reference scope")
    task, cohort = _task(
        config, catalog, phase, origin, budget, series, release, freeze, evidence
    )
    require(
        view.history.dataset == config["dataset_version"]
        and view.history.series == series
        and view.history.origin == origin
        and view.history.window == Window(**task["history"]),
        "Learner view does not match approved task",
    )
    require(
        receipt["protocol_sha256"] == fingerprint(config)
        and receipt["release_sha256"] == fingerprint(release)
        and receipt["cohort_sha256"] == fingerprint(list(cohort))
        and receipt["information_track"] == config["information_track"],
        "Learner receipt identity mismatch",
    )
    _receipt(
        evidence,
        receipt["access_receipt_sha256"],
        release,
        config=config,
        freeze=freeze,
        cohort=cohort,
        series=series,
        phase=phase,
        origin=origin,
        budget=budget,
        capability="learner_history",
        window=Window(**task["history"]),
    )
    require(
        read_json(canonical(receipt["validated_counts"]))
        == read_json(
            canonical(
                validate_task_ledger(
                    config, phase, origin, budget, view, receipt["ledger"]
                )
            )
        ),
        "Learner information ledger validation differs from saved receipt",
    )
    inv, state = scenario_contract(scenario)
    require(
        inv.horizon == config["horizon"],
        "Execution horizon differs from approved protocol",
    )
    # Exactly the existing M3 learner-only schema, with no evaluator keys.
    learner_digest = private_store.put(learner_payload(view))
    plan = {
        "schema_version": 1,
        "kind": "synthetic_reference_execution_plan",
        "dataset": config["dataset_version"],
        "series": series,
        "phase": phase,
        "origin": origin,
        "budget": budget,
        "seed": seed,
        "method": METHOD,
        "protocol_sha256": fingerprint(config),
        "freeze_sha256": fingerprint(freeze),
        "history_release_sha256": fingerprint(release),
        "history_receipt_sha256": receipt["access_receipt_sha256"],
        "learner_sha256": learner_digest,
        "information_track": config["information_track"],
        "scenario": scenario,
        "scenario_sha256": fingerprint(scenario),
        "dependency_sha256s": source_hashes(),
        "python": sys.version.split()[0],
        "initial_stock": state.on_hand,
    }
    require(
        not any("evaluation" in key or "target" in key or "raw" in key for key in plan),
        "Learner plan must not embed evaluation handles",
    )
    return private_store.put(plan)


def execution_approval_template(plan_digest):
    return {
        "schema_version": 1,
        "kind": "synthetic_reference_run_approval",
        "approved": False,
        "plan_sha256": plan_digest,
        "approved_by_owner": "",
        "decision_record": "",
    }


def _verify_execution_approval(approval, plan_digest):
    exact_keys(
        approval,
        (
            "schema_version",
            "kind",
            "approved",
            "plan_sha256",
            "approved_by_owner",
            "decision_record",
        ),
        "reference execution approval",
    )
    require(
        type(approval["schema_version"]) is int
        and approval["schema_version"] == 1
        and approval["kind"] == "synthetic_reference_run_approval"
        and approval["approved"] is True
        and approval["plan_sha256"] == plan_digest
        and isinstance(approval["approved_by_owner"], str)
        and approval["approved_by_owner"].strip()
        and isinstance(approval["decision_record"], str)
        and approval["decision_record"].strip(),
        "Separate explicit execution approval required",
    )


def execute_synthetic_reference(private_store, plan_digest, approval):
    """Learner-only CPU execution. No scorer/targets/raw-reader parameters."""
    _verify_execution_approval(approval, plan_digest)
    plan = private_store.read(plan_digest, kind="synthetic_reference_execution_plan")
    approval_sha = private_store.put(approval)
    require(
        approval_sha == fingerprint(approval),
        "Persisted execution approval identity mismatch",
    )
    require(
        plan["dependency_sha256s"] == source_hashes()
        and plan["python"] == sys.version.split()[0],
        "Execution code/runtime differs from pinned plan",
    )
    scenario, _ = scenario_contract(plan["scenario"])
    require(
        plan["method"] == METHOD
        and plan["scenario_sha256"] == fingerprint(plan["scenario"])
        and plan["dataset"].startswith("synthetic-")
        and plan["phase"] == "development"
        and scenario.horizon <= 128,
        "Unsupported or altered prototype plan",
    )
    # Existing load_learner verifies exact M3 history/normalizer/calendar
    # schema and SHA256 without giving the algorithm any evaluator handle.
    view = load_learner(
        private_store.file(plan["learner_sha256"]),
        sha256=plan["learner_sha256"],
        dataset=plan["dataset"],
        series=plan["series"],
        origin=plan["origin"],
        budget=plan["budget"],
    )
    threshold = _reference_target(view, scenario, plan["budget"])
    result = {
        "schema_version": 1,
        "kind": "synthetic_reference_fit_result",
        "plan_sha256": plan_digest,
        "execution_approval_sha256": fingerprint(approval),
        "learner_sha256": plan["learner_sha256"],
        "dependency_sha256s": plan["dependency_sha256s"],
        "scenario_sha256": plan["scenario_sha256"],
        "seed": plan["seed"],
        "method": METHOD,
        "status": "completed_synthetic_cpu_reference",
        "base_stock_target": threshold,
        "sum_training_sales": sum(o.sales for o in view.history.observations),
        "real_history_observations": plan["budget"],
        "optimizer_steps": 0,
        "simulated_transitions": 0,
        "trained_gp": False,
        "trained_rl": False,
    }
    return private_store.put(result)


def _score_receipt(
    evidence, digest, *, config, freeze, release, cohort, series, phase, origin, task
):
    _receipt(
        evidence,
        digest,
        release,
        config=config,
        freeze=freeze,
        cohort=cohort,
        series=series,
        phase=phase,
        origin=origin,
        budget=None,
        capability="evaluation_outcomes",
        window=Window(**task["evaluation"]),
    )


def score_synthetic_reference(
    private_store,
    evidence,
    *,
    plan_digest,
    fit_digest,
    approval,
    config,
    freeze,
    evaluation_release,
    catalog,
    targets,
    scorer_receipt,
):
    """Separate trusted scorer. Requires an independently released target."""
    require(
        type(targets) is EvaluationTargets and type(scorer_receipt) is dict,
        "Scorer-only EvaluationTargets and receipt required",
    )
    _verify_execution_approval(approval, plan_digest)
    plan = private_store.read(plan_digest, kind="synthetic_reference_execution_plan")
    fit = private_store.read(fit_digest, kind="synthetic_reference_fit_result")
    require(
        private_store.read(
            fit["execution_approval_sha256"],
            kind="synthetic_reference_run_approval",
        )
        == approval,
        "Pinned execution approval evidence is missing or changed",
    )
    require(
        fit["plan_sha256"] == plan_digest
        and fit["execution_approval_sha256"] == fingerprint(approval)
        and fit["learner_sha256"] == plan["learner_sha256"]
        and fit["scenario_sha256"] == plan["scenario_sha256"]
        and fit["dependency_sha256s"] == source_hashes()
        and fit["method"] == METHOD
        and fit["seed"] == plan["seed"]
        and fit["status"] == "completed_synthetic_cpu_reference",
        "Scorer cannot accept an unbound or modified fit",
    )
    require(
        plan["dataset"] == config["dataset_version"]
        and plan["protocol_sha256"] == fingerprint(config)
        and plan["freeze_sha256"] == fingerprint(freeze)
        and plan["scenario_sha256"] == fingerprint(plan["scenario"])
        and plan["phase"] == "development"
        and plan["dataset"].startswith("synthetic-"),
        "Scorer plan/context mismatch or real dataset forbidden",
    )
    cohort = select_cohort(config, catalog)
    require(plan["series"] in cohort, "Scorer cohort mismatch")
    task = authorize_task(
        config,
        freeze,
        evaluation_release,
        phase=plan["phase"],
        origin=plan["origin"],
        budget=None,
        capability="evaluation_outcomes",
        cohort_sha256=fingerprint(list(cohort)),
        cohort=cohort,
        evidence=evidence,
    )
    require(
        scorer_receipt["protocol_sha256"] == fingerprint(config)
        and scorer_receipt["release_sha256"] == fingerprint(evaluation_release)
        and scorer_receipt["cohort_sha256"] == fingerprint(list(cohort)),
        "Scorer receipt metadata differs from evaluation release",
    )
    _score_receipt(
        evidence,
        scorer_receipt["access_receipt_sha256"],
        config=config,
        freeze=freeze,
        release=evaluation_release,
        cohort=cohort,
        series=plan["series"],
        phase=plan["phase"],
        origin=plan["origin"],
        task=task,
    )
    require(
        (targets.dataset, targets.series) == (plan["dataset"], plan["series"])
        and targets.window == Window(**task["evaluation"]),
        "Scorer targets do not match separately released task",
    )
    inv, state = scenario_contract(plan["scenario"])
    require(inv.horizon == len(targets.observations), "Evaluation horizon mismatch")
    # The independent scorer may verify the pinned learner artifact, but
    # never returns its newly obtained outcome values to the learner.
    pinned_view = load_learner(
        private_store.file(plan["learner_sha256"]),
        sha256=plan["learner_sha256"],
        dataset=plan["dataset"],
        series=plan["series"],
        origin=plan["origin"],
        budget=plan["budget"],
    )
    require(
        fit["base_stock_target"] == _reference_target(pinned_view, inv, plan["budget"])
        and fit["sum_training_sales"]
        == sum(o.sales for o in pinned_view.history.observations)
        and fit["real_history_observations"] == plan["budget"]
        and fit["simulated_transitions"] == fit["optimizer_steps"] == 0
        and fit["trained_gp"] is False
        and fit["trained_rl"] is False,
        "Scorer rejects fabricated reference policy/fit evidence",
    )
    limit = fit["base_stock_target"]
    require(
        type(limit) is int and 0 <= limit <= inv.max_order * (inv.lead_time + 1),
        "Invalid learned controller parameter",
    )
    components = {
        "holding": 0.0,
        "lost_sales": 0.0,
        "variable_order": 0.0,
        "fixed_order": 0.0,
    }
    trace = []
    served = requests = 0
    for period, obs in enumerate(targets.observations):
        # Decide from stock and pipeline BEFORE revealing current demand.
        position = state.on_hand + sum(state.pipeline)
        q = max(0, min(inv.max_order, limit - position))
        if period + inv.lead_time >= inv.horizon:
            q = 0
        outcome = transition(inv, state, q, obs.sales)
        trace.append(
            {
                "period": period,
                "day": obs.day,
                "on_hand": state.on_hand,
                "pipeline": list(state.pipeline),
                "order": q,
                "observed_sales_as_requests": obs.sales,
                "fulfilled": outcome.sales,
                "lost_units": outcome.lost_units,
                "cost": outcome.costs.total,
            }
        )
        for name in components:
            components[name] += getattr(outcome.costs, name)
        served += outcome.sales
        requests += obs.sales
        state = outcome.next_state
    private_trace = private_store.put(
        {
            "schema_version": 1,
            "kind": "synthetic_private_scoring_trace",
            "plan_sha256": plan_digest,
            "fit_sha256": fit_digest,
            "periods": trace,
        }
    )
    record = {
        "schema_version": 1,
        "kind": "synthetic_reference_score_evidence",
        "plan_sha256": plan_digest,
        "fit_sha256": fit_digest,
        "execution_approval_sha256": fingerprint(approval),
        "evaluation_release_sha256": fingerprint(evaluation_release),
        "evaluation_receipt_sha256": scorer_receipt["access_receipt_sha256"],
        "trace_sha256": private_trace,
        "scenario_sha256": plan["scenario_sha256"],
        "source_code_sha256s": source_hashes(),
        "cost_components": components,
        "total_cost": math.fsum(components.values()),
        "fulfilled": served,
        "requests": requests,
        "fill_rate": (served / requests if requests else None),
        "ending_stock": trace[-1]["on_hand"] - trace[-1]["fulfilled"],
        "ending_pipeline": list(state.pipeline),
        "simulation_periods": len(trace),
        "trained_gp": False,
        "trained_rl": False,
        "status": "synthetic_only_not_retail_evidence",
    }
    # No score is returned until both local trace and score evidence are durable.
    return private_store.put(record)
