# Local runbook

## Available now

A standard-library provenance wrapper and an infrastructure smoke config. No scientific simulator, GP or RL implementation is supplied by setup. The wrapper records execution, not mathematical correctness.

```bash
../code/.venv/bin/python scripts/check_project.py
../code/.venv/bin/python -m unittest discover -s tests -v
../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/smoke.json --seed 0
```

The smoke run uses no dataset and creates no inventory performance metrics. Local output is results/runs/<UTC>-smoke-<id>/ with manifest.json, config.json, environment.json and console.log. These are ignored by Git.

## Scientific runs, after implementing the entry point

Use this pattern with an ACTUAL implemented command:

```text
../code/.venv/bin/python scripts/run_experiment.py --kind pilot --config <tracked-config.json> --seed <seed> --timeout <approved-seconds> -- <command> <arguments>
```

Run kinds: smoke (plumbing), pilot (exploratory) and research (frozen evaluation). Pilot/research require an explicit command. Research additionally requires --data-manifest <file>, whose SHA-256 is stored. That manifest should describe dataset/generator/version, hashes, split dates, series selection, access terms and information budgets. The wrapper hashes it but does not validate its scientific contents.

The child command must consume config and seed explicitly; the wrapper records but does NOT inject these arguments. Do not put secrets in arguments/config. All run types reject dirty code by default; --allow-dirty is smoke-only and marks the provenance accordingly.

The runner executes synchronously without a shell, enforces an approved timeout and records failures/interruption. It is not a scheduler, checkpoint manager or guarantee of reproducibility. A clean commit is necessary but not sufficient. On Linux it terminates only its own child process group on timeout.

## Before research execution

Approve task/config/resources. Verify fixed clean source revision, locked dependencies, data fingerprint, split, initial/terminal conventions, cost scenarios, RNG handling, log paths, disk capacity and stopping rule. Use a separate worktree/clone, and do not change its code while running.

The user owns long jobs in a terminal/tmux. Do not launch them through Serena or assume an unattended ChatGPT process. Later calls can inspect logs and manifests.

## Publishing evidence back to GitHub

Inspect actual metrics and exit status. Copy small reviewed summaries to results/summaries, referencing source SHA, immutable run ID, config/data hashes, seeds, command, runtime and protocol version. Keep raw data/checkpoints/logs local; never leak private rows or credentials. Record failures/exclusions/reruns and uncertainty.

Use paired demand trajectories, independent training replications and dependence-aware evaluation. Calibration/validation/pretraining count toward information budgets. Simulated samples are not additional real observations. Rich-data references see no post-cutoff data. Specify non-inferiority margins before final tests; lack of significance is not equivalence.
