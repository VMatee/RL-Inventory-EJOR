"""Session safety and output audit; no numerical model imports."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import time
import uuid
from pathlib import Path

from .planning import encode, inside, read_json, sha_file


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(encode(value))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


@contextlib.contextmanager
def session_lease(root):
    """Acquire BEFORE writing outputs; never remove someone else's/stale lock."""
    path = Path(root).parent / "code/.baseline_execution.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    content = {"pid": os.getpid(), "token": token, "root": str(root)}
    try:
        with path.open("x") as stream:
            stream.write(json.dumps(content) + "\n")
    except FileExistsError as exc:
        raise RuntimeError(
            "Baseline session/stale lock exists; inspect it, never auto-remove it"
        ) from exc
    try:
        yield
    finally:
        try:
            if read_json(path).get("token") == token:
                path.unlink()
        except (OSError, ValueError, AttributeError):
            pass  # Leave an unrecognized lock intact for recovery.


@contextlib.contextmanager
def interruption_handlers():
    """Graceful terminal close/SIGTERM cleanup in the scheduler's main thread."""
    previous = {}

    def interrupt(signum, frame):
        raise KeyboardInterrupt(f"Received signal {signum}")

    try:
        for name in ("SIGTERM", "SIGHUP"):
            number = getattr(signal, name, None)
            if number is not None:
                previous[number] = signal.signal(number, interrupt)
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def stop_wrapper(process):
    """Ask only this wrapper to reap its child group; bounded escalation."""
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def audit_job_output(root, job, output, wrapper_log):
    """Return auditable output hashes; exit zero without evidence is not success."""
    root = Path(root)
    data = read_json(root / output / "result.json")
    if (
        data.get("job") != job["id"]
        or data.get("method") != job["method"]
        or data.get("budget") != job["budget"]
        or data.get("series") != job["series"]
        or data.get("status") != "completed_development_baseline_requires_review"
    ):
        raise ValueError("Worker result does not match assigned job")
    receipt = read_json(wrapper_log)
    path = Path(receipt["manifest"]).resolve()
    if root / "results/runs" not in path.parents:
        raise ValueError("Wrapper manifest is outside project results")
    manifest = read_json(path)
    if (
        manifest.get("status") != "succeeded"
        or manifest.get("exit_code") != 0
        or manifest.get("source_unchanged") is not True
        or manifest.get("source_commit") != data.get("source_commit")
    ):
        raise ValueError("Wrapper failed or source changed during job")
    return {
        "result_sha256": sha_file(root / output / "result.json"),
        "trace_sha256": sha_file(root / output / "private_sales_replay.json"),
        "wrapper_manifest": str(path.relative_to(root)),
        "wrapper_manifest_sha256": sha_file(path),
    }


def verify_artifacts(root, plan):
    """Verify every immutable learner/evaluator input before any worker starts."""
    seen = {}
    for job in plan["jobs"]:
        for name, hashkey in (
            ("learner_file", "learner_sha256"),
            ("evaluator_file", "evaluator_sha256"),
        ):
            relative, expected = job[name], job[hashkey]
            if relative in seen and seen[relative] != expected:
                raise ValueError("Same artifact assigned inconsistent fingerprints")
            if relative not in seen:
                actual = sha_file(inside(root, relative, "data/processed"))
                if actual != expected:
                    raise ValueError(f"Prepared data changed: {relative}")
                seen[relative] = actual
    return len(seen)


def monotonic_seconds():
    return time.monotonic()
