#!/usr/bin/env bash
# Foreground user start; --check is read-only. No automatic sync or installation.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
PYTHON="$ROOT/../code/.venv/bin/python"
test -x "$PYTHON" || { echo 'Project virtualenv is missing' >&2; exit 2; }
cd "$ROOT"
export PYTHONPATH="$ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" -B "$ROOT/scripts/start_baselines.py" "$@"
