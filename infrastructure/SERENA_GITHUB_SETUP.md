# Observed local integration

Inspected 2026-10-17 through the requested SeneraAiServer:

- Project: RL-Inventory-EJOR.
- Serena workspace root: /home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR (local .serena stays here).
- Git checkout: /home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR/github.
- Python environment: /home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR/code/.venv.
- Canonical Python code remains versioned under github/src; code/src is a local convenience symlink, never an independent copy.
- Remote: git@github-rl-inventory-ejor:VMatee/RL-Inventory-EJOR.git.
- Initial main: clean and matching origin/main at 9019a91c305876b0c156a547f4b3ee0c72c96c98.
- Existing virtualenv: Python 3.10.12.
- Codex CLI: 0.163.0; executable present, auth/model access untested.
- make/timeout available; latexmk/pdflatex not detected on this PC.

No SSH keys, daemon settings, global Codex config, plugin permissions or repository visibility were changed. Never copy credentials into the repository.

## Session startup

Read server initial instructions and verify active project. Inspect local Git tree before fetch/pull. Use sync_main.sh only on clean idle main. Dirty/diverged trees need reconciliation, not deletion. See docs/WORKFLOW.md for prompts and PR flow.

The shell tool permits short synchronous checks, not interactive Codex, services or long-running jobs. User-terminal execution and bounded later log inspection are the intended long-job workflow. A GitHub self-hosted runner is unnecessary and not installed.

## Environment

The active isolated Python 3.10.12 environment is now at `../code/.venv` relative to the Git checkout. The initial minimal virtualenv previously preserved at `../code/legacy-venv-pre-migration` was removed at the owner's explicit request after verifying no running process uses it; the active `../code/.venv` is unchanged. The user authorized installation of the project Python science/development dependencies. Official PyTorch 2.9.1+cu130 wheels, GPyTorch, BoTorch, Gymnasium, Stable-Baselines3, scientific tools and local development packages were installed into the new virtualenv only. See `environment/README.md` and the resolved `environment/requirements-lock.txt` for exact versions and installation steps. `scripts/check_environment.py` tests imports and basic GPU allocations. No system drivers, OS packages or TeX were installed. The lock is a Linux/Python/CUDA environment snapshot, not a universal reproducibility guarantee.

For local manuscript compilation, obtain approval before installing a TeX distribution with elsarticle, BibTeX and latexmk. Missing local TeX does not block simulator work.

Repository-local Git author identity was initialized from existing commit metadata so local commits work. Global identity and credentials were not modified.
