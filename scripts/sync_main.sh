#!/usr/bin/env bash
# Never discards local work; the caller must also ensure this checkout is idle.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [[ -e ../code/.baseline_execution.lock ]]; then
  printf 'Refusing sync: baseline execution lock exists. Do not change running code.\n' >&2
  exit 2
fi
branch="$(git symbolic-ref --short -q HEAD || true)"
if [[ "$branch" != main ]]; then
  printf 'Refusing sync: branch is %s, not main.\n' "$branch" >&2; exit 2
fi
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  printf 'Refusing sync: working tree is dirty. Preserve/review changes first.\n' >&2
  git status --short; exit 2
fi
remote="$(git remote get-url origin)"
case "$remote" in
  git@github-rl-inventory-ejor:VMatee/RL-Inventory-EJOR.git|git@github.com:VMatee/RL-Inventory-EJOR.git|https://github.com/VMatee/RL-Inventory-EJOR.git) ;;
  *) printf 'Unexpected origin; inspect it locally. No changes made.\n' >&2; exit 2 ;;
esac
git fetch origin
if ! git merge-base --is-ancestor HEAD origin/main; then
  printf 'Local main has unpublished/divergent commits. No reset performed.\n' >&2; exit 2
fi
git merge --ff-only origin/main
printf 'Synchronized SHA: '; git rev-parse HEAD
git status --short --branch
