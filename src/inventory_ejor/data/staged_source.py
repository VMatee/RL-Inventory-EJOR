"""Trusted bounded M5 reader adapters for staged preparation.

Constructors read no files. Every supported read, including a direct adapter
call, validates a complete per-request authorization before raw IO. The returned
LearnerView has no reader. No OS isolation or hostile-Python sandbox is claimed.
"""

from __future__ import annotations

import copy
import hashlib
import subprocess
from pathlib import Path

from .contracts import Window, exact_keys
from .evidence import EvidenceStore, access_receipt
from .m5 import ReadLimits, load_calendar, load_observations
from .protocol import M5_VERSION, plan_protocol, recognized_m5_source, require
from .provenance import fingerprint, verify_inputs
from .releases import check_freeze


class _WindowSource:
    def __init__(self, raw_dir, manifest, *, analysis_spec_path):
        raw = Path(raw_dir).absolute()
        require(raw == raw.resolve(), "Raw source must be canonical, without symlinks")
        self._root = raw
        self._manifest = copy.deepcopy(manifest)
        self._analysis_spec = Path(analysis_spec_path).absolute()

    @property
    def manifest_sha256(self):
        return fingerprint(self._manifest)

    def verify_freeze(self, config, freeze):
        """Bind live clean code and actual analysis-spec bytes before data IO."""
        check_freeze(config, freeze)
        require(
            self.manifest_sha256 == freeze["source_manifest_sha256"],
            "Reader source manifest differs from scientific freeze",
        )
        if recognized_m5_source(self._root, self._manifest):
            require(
                config["dataset_version"] == M5_VERSION,
                "Real M5 source cannot masquerade as a fixture "
                "or another logical version",
            )
            plan_protocol(config)
        commit, dirty = _live_code()
        require(
            commit == freeze["code_commit"] and not dirty,
            "Live code differs from the clean reviewed scientific freeze",
        )
        path = self._analysis_spec
        require(
            path == path.resolve() and path.is_file(),
            "Noncanonical analysis specification",
        )
        require(
            hashlib.sha256(path.read_bytes()).hexdigest()
            == freeze["analysis_spec_sha256"],
            "Analysis specification changed after approval",
        )

    def _read(self, series, window, *, capability=None, authorization=None):
        # No reusable 'armed' flag or stale grant: validate this exact read.
        from .staged import _authorize

        require(type(authorization) is dict, "Complete per-read authorization required")
        exact_keys(
            authorization,
            (
                "config",
                "freeze",
                "release",
                "catalog",
                "phase",
                "origin",
                "budget",
                "selection",
                "calibration",
                "evidence",
            ),
            "source authorization",
        )
        require(capability == self._capability, "Cross-capability source access")
        a = authorization
        task, _ = _authorize(
            a["config"],
            a["freeze"],
            a["release"],
            a["catalog"],
            series,
            a["phase"],
            a["origin"],
            a["budget"],
            capability,
            a["selection"],
            a["calibration"],
            a["evidence"],
        )
        require(
            type(a["evidence"]) is EvidenceStore,
            "Production reads require persisted access receipts",
        )
        require(
            type(window) is Window
            and window
            == Window(
                **task["history" if capability == "learner_history" else "evaluation"]
            ),
            "Window differs from authorized source task",
        )
        self.verify_freeze(a["config"], a["freeze"])
        limits = ReadLimits(max_seconds=100, max_selected=1024)
        # Validate every path BEFORE provenance hashing or CSV interpretation.
        for name in (
            "calendar.csv",
            "sales_train_validation.csv",
            "sales_train_evaluation.csv",
            "sell_prices.csv",
            "sample_submission.csv",
        ):
            path = self._root / name
            require(
                path == path.resolve() and path.is_file(), "Noncanonical source file"
            )
        before = verify_inputs(self._root, self._manifest, limits)
        calendar = load_calendar(self._root / "calendar.csv", limits)
        result = load_observations(
            self._root / "sales_train_evaluation.csv",
            (series,),
            window,
            calendar,
            limits,
        )[series]
        require(
            before == verify_inputs(self._root, self._manifest, limits),
            "Source changed during staged preparation",
        )
        # Persist before returning values. An interrupted/failed read may have
        # exposed data without a success receipt; it must not be retried as blind.
        access_receipt(
            a["config"], a["freeze"], a["release"], series, window, a["evidence"]
        )
        return result


class M5HistorySource(_WindowSource):
    """Trusted history adapter; no public evaluator method."""

    _capability = "learner_history"

    def read_history(self, series, window, *, authorization=None):
        return self._read(
            series, window, capability=self._capability, authorization=authorization
        )


class M5EvaluatorSource(_WindowSource):
    """Trusted scorer adapter, supplied only to the separate scorer API."""

    _capability = "evaluation_outcomes"

    def read_evaluation(self, series, window, *, authorization=None):
        return self._read(
            series, window, capability=self._capability, authorization=authorization
        )


def _live_code():
    root = Path(__file__).resolve().parents[3]
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=5
    ).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        text=True,
        timeout=5,
    ).strip()
    return commit, bool(dirty)
