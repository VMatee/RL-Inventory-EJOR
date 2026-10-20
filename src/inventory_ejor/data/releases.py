"""Hash-bound scientific freeze, selection, calibration and per-task releases.

These are auditable owner records, not signatures or an OS security sandbox.
No record is approved by a template, a passing test or metadata planning.
"""

from __future__ import annotations

from .contracts import exact_keys
from .protocol import plan_protocol, require, sha256_id, task_for
from .provenance import fingerprint


def freeze_template(config):
    return {
        "schema_version": 1,
        "kind": "scientific_freeze",
        "approved": False,
        "protocol_sha256": plan_protocol(config)["protocol_sha256"],
        "analysis_spec_sha256": None,
        "source_manifest_sha256": None,
        "code_commit": None,
        "approved_by_owner": "",
        "decision_record": "",
    }


def _record(record, kind, keys):
    exact_keys(record, ("schema_version", "kind", *keys), kind)
    require(
        type(record["schema_version"]) is int and record["schema_version"] == 1,
        "Unsupported release record version",
    )
    require(record["kind"] == kind, "Wrong release record kind")


def _owner(record):
    require(record["approved"] is True, "Separate owner authorization required")
    for key in ("approved_by_owner", "decision_record"):
        require(
            isinstance(record[key], str) and bool(record[key].strip()),
            "Named owner and scientific decision record required",
        )


def check_freeze(config, freeze):
    _record(
        freeze,
        "scientific_freeze",
        (
            "approved",
            "protocol_sha256",
            "analysis_spec_sha256",
            "source_manifest_sha256",
            "code_commit",
            "approved_by_owner",
            "decision_record",
        ),
    )
    require(
        freeze["protocol_sha256"] == plan_protocol(config)["protocol_sha256"],
        "Protocol changed after scientific approval",
    )
    _owner(freeze)
    for field in ("analysis_spec_sha256", "source_manifest_sha256"):
        sha256_id(freeze[field], field)
    require(
        isinstance(freeze["code_commit"], str)
        and len(freeze["code_commit"]) == 40
        and all(c in "0123456789abcdef" for c in freeze["code_commit"]),
        "Full reviewed code commit required",
    )
    return fingerprint(freeze)


def check_selection(config, freeze, selection):
    """Check an attestation's structure/bindings, NOT persisted evidence."""
    _record(
        selection,
        "selection_lock",
        (
            "protocol_sha256",
            "freeze_sha256",
            "selection_frozen",
            "candidate_sha256",
            "baseline_sha256",
            "search_spec_sha256",
            "calibration_rule_sha256",
            "development_access_log_sha256",
        ),
    )
    require(
        selection["protocol_sha256"] == plan_protocol(config)["protocol_sha256"]
        and selection["freeze_sha256"] == check_freeze(config, freeze),
        "Selection lock belongs to another scientific freeze",
    )
    require(
        selection["selection_frozen"] is True, "Model/policy selection is not frozen"
    )
    for field in (
        "candidate_sha256",
        "baseline_sha256",
        "search_spec_sha256",
        "calibration_rule_sha256",
        "development_access_log_sha256",
    ):
        sha256_id(selection[field], field)
    return fingerprint(selection)


def check_calibration(config, freeze, selection, calibration):
    """Check the attested lock chain; authorize_task also verifies its files."""
    _record(
        calibration,
        "calibration_lock",
        (
            "protocol_sha256",
            "freeze_sha256",
            "selection_sha256",
            "calibration_frozen",
            "calibration_result_sha256",
            "access_log_sha256",
        ),
    )
    require(
        calibration["protocol_sha256"] == plan_protocol(config)["protocol_sha256"]
        and calibration["freeze_sha256"] == check_freeze(config, freeze)
        and calibration["selection_sha256"]
        == check_selection(config, freeze, selection),
        "Calibration lock is not bound to frozen policy selection",
    )
    require(calibration["calibration_frozen"] is True, "Calibration is not frozen")
    for field in ("calibration_result_sha256", "access_log_sha256"):
        sha256_id(calibration[field], field)
    return fingerprint(calibration)


def release_template(config, phase, origin, budget, capability, cohort_sha256):
    require(
        capability in ("learner_history", "evaluation_outcomes"),
        "Unsupported access capability",
    )
    # Evaluator access is the same path for all budgets and uses no budget field.
    task_for(
        config, phase, origin, budget if budget is not None else max(config["budgets"])
    )
    require(
        (capability == "learner_history") == (budget is not None),
        "Only learner-history releases specify a budget",
    )
    sha256_id(cohort_sha256, "cohort_sha256")
    return {
        "schema_version": 1,
        "kind": "data_release",
        "approved": False,
        "protocol_sha256": plan_protocol(config)["protocol_sha256"],
        "freeze_sha256": None,
        "phase": phase,
        "origin": origin,
        "budget": budget,
        "capability": capability,
        "cohort_sha256": cohort_sha256,
        "selection_sha256": None,
        "calibration_sha256": None,
        "approved_by_owner": "",
        "decision_record": "",
    }


def check_task_attestation(
    config,
    freeze,
    release,
    *,
    phase,
    origin,
    budget,
    capability,
    cohort_sha256,
    selection=None,
    calibration=None,
):
    """Metadata-only attestation validation. This does NOT authorize value IO."""
    task = task_for(
        config, phase, origin, budget if budget is not None else max(config["budgets"])
    )
    _record(
        release,
        "data_release",
        (
            "approved",
            "protocol_sha256",
            "freeze_sha256",
            "phase",
            "origin",
            "budget",
            "capability",
            "cohort_sha256",
            "selection_sha256",
            "calibration_sha256",
            "approved_by_owner",
            "decision_record",
        ),
    )
    expected = release_template(
        config, phase, origin, budget, capability, cohort_sha256
    )
    for field in (
        "protocol_sha256",
        "phase",
        "origin",
        "budget",
        "capability",
        "cohort_sha256",
    ):
        require(
            release[field] == expected[field], f"Release does not bind task: {field}"
        )
    # Reject bool/int aliases as well as value mismatches.
    require(
        type(release["origin"]) is int
        and (release["budget"] is None or type(release["budget"]) is int),
        "Release origins/budgets require exact integer types",
    )
    require(
        release["freeze_sha256"] == check_freeze(config, freeze),
        "Release belongs to another scientific freeze",
    )
    _owner(release)
    if phase in ("calibration", "final_test"):
        require(
            selection is not None, "Calibration/final access requires frozen selection"
        )
        require(
            release["selection_sha256"] == check_selection(config, freeze, selection),
            "Release does not bind frozen selection",
        )
    else:
        require(
            release["selection_sha256"] is None and selection is None,
            "Development/validation must not consume a later selection lock",
        )
    if phase == "final_test":
        require(calibration is not None, "Final access requires frozen calibration")
        require(
            release["calibration_sha256"]
            == check_calibration(config, freeze, selection, calibration),
            "Final release does not bind frozen calibration",
        )
    else:
        require(
            release["calibration_sha256"] is None and calibration is None,
            "Only final tasks may consume a calibration lock",
        )
    return task


def authorize_task(
    config,
    freeze,
    release,
    *,
    phase,
    origin,
    budget,
    capability,
    cohort_sha256,
    selection=None,
    calibration=None,
    evidence=None,
    cohort=None,
):
    """Authorize value IO: attested releases AND persisted prerequisite evidence.

    Evidence demonstrates byte identity and declared access coverage, not honest
    ownership, correct model selection or an authenticated event chronology.
    """
    task = check_task_attestation(
        config,
        freeze,
        release,
        phase=phase,
        origin=origin,
        budget=budget,
        capability=capability,
        cohort_sha256=cohort_sha256,
        selection=selection,
        calibration=calibration,
    )
    if phase in ("calibration", "final_test"):
        from .evidence import EvidenceStore, verify_calibration, verify_selection

        require(
            type(evidence) is EvidenceStore, "Persisted selection evidence required"
        )
        require(
            type(cohort) is tuple and fingerprint(list(cohort)) == cohort_sha256,
            "Evidence requires the exact fixed cohort",
        )
        verify_selection(config, freeze, selection, cohort, evidence)
        if phase == "final_test":
            verify_calibration(config, freeze, selection, calibration, cohort, evidence)
    return task
