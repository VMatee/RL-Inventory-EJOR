# Observed local integration

Inspected 2026-10-17 through the requested SeneraAiServer:

- Project: RL-Inventory-EJOR.
- Checkout: /home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR.
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

Keep the existing .venv. Infrastructure needs only the standard library. Before scientific work, agree on PyTorch/GP libraries, CPU/CUDA compatibility and a lockfile; install only approved project dependencies. Environment manifests list installed names/versions, not secrets, and are not substitutes for a tested lockfile.

For local manuscript compilation, obtain approval before installing a TeX distribution with elsarticle, BibTeX and latexmk. Missing local TeX does not block simulator work.

Repository-local Git author identity was initialized from existing commit metadata so local commits work. Global identity and credentials were not modified.
