"""Trusted bounded M5 reader adapters for staged preparation.

Constructors read no files. Only the trusted staged preparer receives these
adapters; the returned LearnerView has no reader. Direct raw-reader use remains
outside this accidental-leakage API, as in M3 (no OS isolation is claimed).
"""

from __future__ import annotations

import copy
import hashlib
import subprocess
from pathlib import Path

from .m5 import ReadLimits, load_calendar, load_observations
from .protocol import M5_VERSION, plan_protocol, recognized_m5_source, require
from .provenance import fingerprint, verify_inputs


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

    def _read(self, series, window):
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
        return result


class M5HistorySource(_WindowSource):
    """Trusted history adapter; no public evaluator method."""

    def read_history(self, series, window):
        return self._read(series, window)


class M5EvaluatorSource(_WindowSource):
    """Trusted scorer adapter, supplied only to the separate scorer API."""

    def read_evaluation(self, series, window):
        return self._read(series, window)


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
