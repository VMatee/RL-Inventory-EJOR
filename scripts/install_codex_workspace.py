"""Deploy Git-tracked Codex entry files into the sibling code/ workspace.

No overwriting of unknown or locally edited targets; no --force mode. Only
four explicitly named files and an installer-state JSON file are touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("README.md", "AGENTS.md", "CODEX_PROMPT.md", "start_codex.sh")
STATE = ".codex_workspace_state.json"


class InstallConflict(ValueError):
    """A local file cannot safely be updated from the tracked template."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(target: Path, content: bytes, mode: int) -> None:
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        temp.chmod(mode)
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()


def deploy(repo: Path, code: Path, *, check: bool = False) -> list[str]:
    """Preflight all files, then install; return names requiring an update.

    check=True is read-only. A changed tracked template may replace only the
    last installed bytes (or an already identical target), never local edits.
    """
    repo = Path(repo).resolve(strict=True)
    code = Path(code)
    if code.is_symlink() or code.parent.resolve() != repo.parent or code.name != "code":
        raise InstallConflict("Target must be the real sibling code/ directory")
    if not code.is_dir():
        raise InstallConflict("Existing code/ workspace is missing; nothing created")
    templates = repo / "infrastructure" / "codex_workspace"
    state_path = code / STATE
    if state_path.is_symlink():
        raise InstallConflict("Installer state must not be a symlink")
    previous = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("schema_version") != 1 or not isinstance(state.get("files"), dict):
            raise InstallConflict("Unknown installer-state schema")
        previous = state["files"]
    for alias in ("agent.md", "readme.md", "AGENTS.override.md"):
        if (code / alias).exists() or (code / alias).is_symlink():
            raise InstallConflict(f"Review pre-existing {alias}; no alias deletion is automatic")
    payloads: dict[str, bytes] = {}
    pending: list[str] = []
    for name in FILES:
        source = templates / (name + ".template")
        if source.is_symlink() or not source.is_file():
            raise InstallConflict(f"Missing/nonregular tracked template: {name}")
        content = source.read_bytes()
        target = code / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise InstallConflict(f"Target is not a regular file: {name}")
        if target.exists():
            current = digest(target.read_bytes())
            if current == digest(content):
                payloads[name] = content
                continue
            if current != previous.get(name):
                raise InstallConflict(f"Preserving unknown/locally edited {name}; reconcile it first")
        payloads[name] = content
        pending.append(name)
    if check:
        return pending
    # Re-read target hashes immediately before writing to catch intervening edits.
    for name in pending:
        target = code / name
        if target.exists():
            current = digest(target.read_bytes())
            if target.is_symlink() or current not in (previous.get(name), digest(payloads[name])):
                raise InstallConflict(f"Concurrent edit detected: {name}; aborting")
        _atomic_write(target, payloads[name], 0o700 if name.endswith(".sh") else 0o644)
    record = {
        "schema_version": 1,
        "templates_relative_to_repo": "infrastructure/codex_workspace",
        "files": {name: digest(content) for name, content in payloads.items()},
    }
    _atomic_write(state_path, (json.dumps(record, indent=2, sort_keys=True) + "\n").encode(), 0o600)
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only drift/conflict check")
    args = parser.parse_args()
    try:
        changed = deploy(ROOT, ROOT.parent / "code", check=args.check)
    except (InstallConflict, OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(json.dumps({
        "mode": "check" if args.check else "install",
        "workspace": str(ROOT.parent / "code"),
        "pending_files" if args.check else "updated_files": changed,
        "scope": "Codex documentation/launcher only; no model, Git sync or experiment started",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
