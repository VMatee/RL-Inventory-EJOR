#!/usr/bin/env python3
"""Synchronous provenance wrapper; no scientific algorithm is supplied."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, stderr=subprocess.PIPE).strip()

def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_json(path: Path, value: object) -> None:
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
    temp.replace(path)

def terminate(process: subprocess.Popen) -> None:
    if os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait()

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--kind', choices=('smoke','pilot','research'), default='smoke')
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--data-manifest', type=Path)
    parser.add_argument('--allow-dirty', action='store_true', help='Smoke only')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.seed < 0:
        parser.error('timeout must be positive and seed nonnegative')
    if args.allow_dirty and args.kind != 'smoke':
        parser.error('--allow-dirty is restricted to smoke')
    config_path = args.config.resolve()
    try:
        config_bytes = config_path.read_bytes()
        config = json.loads(config_bytes)
    except (OSError, ValueError) as exc:
        parser.error(f'Cannot read JSON config: {exc}')
    if not isinstance(config, dict):
        parser.error('Config must be a JSON object')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        if args.kind != 'smoke':
            parser.error('pilot/research require an explicit implemented command after --')
        command = [sys.executable, str(ROOT/'scripts/check_project.py')]
    if args.kind == 'research' and not args.data_manifest:
        parser.error('research requires --data-manifest, also for synthetic generators')
    data = None
    if args.data_manifest:
        path = args.data_manifest.resolve()
        if not path.is_file():
            parser.error('Data-manifest path is not a file')
        data = {'path': str(path), 'sha256': sha256(path)}
    try:
        commit = git('rev-parse','HEAD')
        before = git('status','--porcelain','--untracked-files=all')
    except (OSError, subprocess.CalledProcessError) as exc:
        parser.error(f'Git provenance unavailable: {exc}')
    if before and not args.allow_dirty:
        parser.error('Working tree is dirty. Commit/reconcile first; nothing discarded.')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+f'-{args.kind}-'+uuid.uuid4().hex[:8]
    directory = ROOT/'results/runs'/run_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'config.json').write_bytes(config_bytes)
    packages = sorted(({'name': d.metadata.get('Name','unknown'), 'version': d.version}
        for d in importlib.metadata.distributions()), key=lambda d:(d['name'],d['version']))
    write_json(directory/'environment.json', {'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'packages': packages})
    manifest = {'schema_version':1, 'run_id':run_id, 'kind':args.kind, 'status':'running',
        'started_utc':stamp(), 'source_commit':commit, 'git_status_before':before,
        'clean_source':not bool(before), 'config_path':str(config_path),
        'config_sha256':sha256(directory/'config.json'), 'seed':args.seed,
        'seed_note':'Recorded only; child command must consume its config/seed explicitly.',
        'data_manifest':data, 'command':command, 'timeout_seconds':args.timeout, 'cwd':str(ROOT),
        'is_scientific_evidence':False if args.kind=='smoke' else 'requires_review'}
    write_json(directory/'manifest.json', manifest)
    started = time.monotonic()
    code = 1
    try:
        with (directory/'console.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=(os.name=='posix'))
            manifest['pid'] = process.pid
            write_json(directory/'manifest.json', manifest)
            try:
                code = process.wait(timeout=args.timeout)
                manifest['status'] = 'succeeded' if code==0 else 'failed'
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                timed_out = isinstance(exc, subprocess.TimeoutExpired)
                manifest['status'] = 'timed_out' if timed_out else 'interrupted'
                code = 124 if timed_out else 130
                terminate(process)
    except OSError as exc:
        manifest['status'] = 'failed_to_start'
        manifest['error'] = str(exc)
    finally:
        manifest['exit_code'] = code
        manifest['finished_utc'] = stamp()
        manifest['runtime_seconds'] = round(time.monotonic()-started,6)
        try:
            after = git('status','--porcelain','--untracked-files=all')
            end_commit = git('rev-parse','HEAD')
            manifest['git_status_after'] = after
            manifest['source_commit_after'] = end_commit
            manifest['source_unchanged'] = not before and not after and commit==end_commit
        except (OSError, subprocess.CalledProcessError):
            manifest['source_unchanged'] = False
        write_json(directory/'manifest.json', manifest)
    print(json.dumps({'run_id':run_id, 'status':manifest['status'], 'exit_code':code,
        'manifest':str(directory/'manifest.json')}, indent=2))
    return code if code>=0 else 128+abs(code)

if __name__ == '__main__':
    raise SystemExit(main())
