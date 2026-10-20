"""Local content-addressed metadata evidence, not signatures or an OS sandbox.

All reads are bounded canonical JSON; this store never follows a file reference
from a record. Procedure specifications are attestations, not executable models.
The M4d executor must separately verify every byte actually loaded for fitting.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path

from .contracts import Window, exact_keys
from .protocol import MAX_EVIDENCE_RECEIPTS, plan_protocol, require, sha256_id
from .provenance import canonical, fingerprint, read_json
from .releases import check_calibration, check_selection, check_task_attestation

COMMON = ("schema_version", "kind", "protocol_sha256", "freeze_sha256")
PROCEDURES = (
    "candidate_sha256",
    "baseline_sha256",
    "search_spec_sha256",
    "calibration_rule_sha256",
)
RECEIPT_KEYS = (
    *COMMON,
    "source_manifest_sha256",
    "release_sha256",
    "cohort_sha256",
    "phase",
    "origin",
    "budget",
    "capability",
    "series",
    "window",
    "selection_sha256",
    "calibration_sha256",
)


class EvidenceStore:
    """Dedicated canonical directory, exclusive writes, revalidated on each read.

    Existing identical records can be reused; different bytes cannot overwrite a
    digest. A local owner can still replace files: subsequent reads detect stale
    hashes, but this is not an authenticated append-only log.
    """

    def __init__(self, root):
        self.root = Path(root).absolute()
        self._check_root()

    def _check_root(self):
        root = self.root
        require(
            root == root.resolve() and root.is_dir(),
            "Canonical existing evidence directory required",
        )
        repo = Path(__file__).resolve().parents[3]
        for directory in ("data/raw", "data/processed", "results/runs"):
            require(
                not root.is_relative_to(repo / directory),
                "Evidence cannot use protected artifact directories",
            )

    def _path(self, digest):
        self._check_root()
        sha256_id(digest, "evidence digest")
        path = self.root / (digest + ".json")
        require(path == path.resolve(), "Noncanonical evidence file")
        return path

    def read(self, digest):
        path = self._path(digest)
        require(
            path.is_file() and path.stat().st_size <= 1024 * 1024,
            "Missing or oversized persisted evidence",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == digest,
            "Persisted evidence checksum mismatch",
        )
        obj = read_json(raw)
        require(canonical(obj) == raw, "Evidence must use canonical JSON")
        return obj

    def put(self, obj):
        raw = canonical(obj)
        require(len(raw) <= 1024 * 1024, "Oversized evidence")
        digest = hashlib.sha256(raw).hexdigest()
        path = self._path(digest)
        if path.exists():
            require(self.read(digest) == obj, "Conflicting persisted evidence")
        else:
            with path.open("xb") as stream:
                stream.write(raw)
        return digest


def access_receipt(config, freeze, release, series, window, store):
    """Persist the exact released access metadata, without observation values."""
    require(type(store) is EvidenceStore, "Persisted access receipt store required")
    release_sha = store.put(release)
    receipt = {
        "schema_version": 1,
        "kind": "staged_access_receipt",
        "protocol_sha256": fingerprint(config),
        "freeze_sha256": fingerprint(freeze),
        "source_manifest_sha256": freeze["source_manifest_sha256"],
        "release_sha256": release_sha,
        "cohort_sha256": release["cohort_sha256"],
        **{
            key: release[key]
            for key in (
                "phase",
                "origin",
                "budget",
                "capability",
                "selection_sha256",
                "calibration_sha256",
            )
        },
        "series": series,
        "window": asdict(window),
    }
    return store.put(receipt)


def _typed(store, digest, kind, config, freeze, extra):
    obj = store.read(digest)
    exact_keys(obj, (*COMMON, *extra), kind)
    require(
        type(obj["schema_version"]) is int
        and obj["schema_version"] == 1
        and obj["kind"] == kind,
        "Wrong evidence type/version",
    )
    require(
        obj["protocol_sha256"] == fingerprint(config)
        and obj["freeze_sha256"] == fingerprint(freeze),
        "Evidence belongs to another freeze",
    )
    return obj


def _digests(values):
    require(
        type(values) is list and 0 < len(values) <= MAX_EVIDENCE_RECEIPTS,
        "Nonempty bounded receipt list required",
    )
    for value in values:
        sha256_id(value, "receipt digest")
    require(values == sorted(set(values)), "Receipt IDs must be unique and sorted")
    return values


def _receipts(config, freeze, cohort, store, digests, phases, selection=None):
    actual = set()
    required = set()
    for task in plan_protocol(config)["tasks"]:
        if task["phase"] == phases[-1]:
            for series in cohort:
                required.add(
                    (
                        task["phase"],
                        task["origin"],
                        task["budget"],
                        "learner_history",
                        series,
                    )
                )
                required.add(
                    (task["phase"], task["origin"], None, "evaluation_outcomes", series)
                )
    selected = []
    for digest in _digests(digests):
        r = _typed(
            store,
            digest,
            "staged_access_receipt",
            config,
            freeze,
            RECEIPT_KEYS[len(COMMON) :],
        )
        require(
            r["phase"] in phases and r["series"] in cohort,
            "Wrong evidence phase/cohort",
        )
        require(
            r["source_manifest_sha256"] == freeze["source_manifest_sha256"],
            "Receipt source differs from freeze",
        )
        task = check_task_attestation(
            config,
            freeze,
            store.read(r["release_sha256"]),
            phase=r["phase"],
            origin=r["origin"],
            budget=r["budget"],
            capability=r["capability"],
            cohort_sha256=fingerprint(list(cohort)),
            selection=selection,
        )
        release = store.read(r["release_sha256"])
        for key in ("cohort_sha256", "selection_sha256", "calibration_sha256"):
            require(r[key] == release[key], "Receipt and release identities differ")
        expected = task[
            "history" if r["capability"] == "learner_history" else "evaluation"
        ]
        exact_keys(r["window"], ("start", "stop"), "receipt window")
        Window(**r["window"])  # Reject bool/int aliases in persisted metadata.
        require(r["window"] == expected, "Receipt window differs from released task")
        identity = (r["phase"], r["origin"], r["budget"], r["capability"], r["series"])
        require(identity not in actual, "Duplicate receipt task")
        actual.add(identity)
        if r["phase"] == phases[-1]:
            selected.append(digest)
    require(required <= actual, "Incomplete prerequisite phase access coverage")
    return sorted(selected)


def verify_selection(config, freeze, selection, cohort, store):
    """Verify persisted specifications, validation coverage and result bindings.

    Presence of access/result records does not prove correct or honest scientific
    selection. No trained model is deserialized, and no outcomes are opened here.
    """
    check_selection(config, freeze, selection)
    for field in PROCEDURES:
        obj = _typed(
            store,
            selection[field],
            "procedure_specification",
            config,
            freeze,
            ("role", "specification"),
        )
        require(
            obj["role"] == field.removesuffix("_sha256"),
            "Wrong procedure artifact role",
        )
        require(
            type(obj["specification"]) is dict and bool(obj["specification"]),
            "Empty procedure specification",
        )
    log = _typed(
        store,
        selection["development_access_log_sha256"],
        "selection_evidence",
        config,
        freeze,
        (*PROCEDURES, "receipt_sha256s", "selection_result_sha256"),
    )
    for field in PROCEDURES:
        require(log[field] == selection[field], "Selection evidence procedure mismatch")
    validation = _receipts(
        config,
        freeze,
        cohort,
        store,
        log["receipt_sha256s"],
        ("development", "validation"),
    )
    result = _typed(
        store,
        log["selection_result_sha256"],
        "selection_result",
        config,
        freeze,
        (*PROCEDURES, "validation_receipt_sha256s", "result"),
    )
    require(
        all(result[f] == selection[f] for f in PROCEDURES),
        "Selection result procedure mismatch",
    )
    require(
        result["validation_receipt_sha256s"] == validation,
        "Selection result does not reference validation evidence",
    )
    require(
        type(result["result"]) is dict and bool(result["result"]),
        "Empty selection result",
    )


def verify_calibration(config, freeze, selection, calibration, cohort, store):
    check_calibration(config, freeze, selection, calibration)
    log = _typed(
        store,
        calibration["access_log_sha256"],
        "calibration_evidence",
        config,
        freeze,
        ("selection_sha256", "receipt_sha256s"),
    )
    require(
        log["selection_sha256"] == fingerprint(selection),
        "Calibration evidence selection mismatch",
    )
    receipts = _receipts(
        config,
        freeze,
        cohort,
        store,
        log["receipt_sha256s"],
        ("calibration",),
        selection,
    )
    result = _typed(
        store,
        calibration["calibration_result_sha256"],
        "calibration_result",
        config,
        freeze,
        ("selection_sha256", "calibration_receipt_sha256s", "result"),
    )
    require(
        result["selection_sha256"] == fingerprint(selection)
        and result["calibration_receipt_sha256s"] == receipts,
        "Calibration result does not reference its access evidence",
    )
    require(
        type(result["result"]) is dict and bool(result["result"]),
        "Empty calibration result",
    )
