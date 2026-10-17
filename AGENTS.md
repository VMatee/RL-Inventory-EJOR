# Agent instructions: RL-Inventory-EJOR

These rules apply to this repository. AGENTS.md is the single canonical agent instruction file. Platform safety rules and explicit user instructions take precedence.

## Before acting

Read docs/STATUS.md, docs/PROJECT_CHARTER.md, docs/TASKS.md and the applicable protocol. Read docs/DECISION_LOG.md for scope decisions. Inspect actual branch, commit and working-tree state; prior chat is not a substitute for repository evidence.

When using SeneraAiServer, call initial_instructions once per coding session and confirm the active project is RL-Inventory-EJOR. Follow the server's execution restrictions. Never operate in another connected workspace. Quote the local path because it contains spaces.

## Scientific scope and integrity

Study limited initial REAL demand data, known inventory dynamics, fixed positive lead time, GP demand uncertainty and neural policy improvement. Do not add another application, rolling service constraints, unknown lead times, multi-echelon control or censored-demand inference without owner approval and a decision-log entry.

Never invent citations, data access, outcomes, proofs, guarantees or completed reproductions. Distinguish hypotheses, derived statements, verified sources and measured results. An imported bibliography is not a fresh source audit. Keep manuscript contributions conditional until demonstrated.

Separate epistemic uncertainty, demand noise, Monte Carlo error and optimizer error. A GP posterior is not automatically calibrated; posterior credibility is not frequentist coverage. Adaptive policy selection must be included in any claimed coverage argument. GP+RL or baseline-relative uncertainty alone is not novelty.

Count calibration, normalization, validation, cross-item pretraining and hyperparameter data. Do not use future test information or choose series from test performance. Synthetic transitions are not new real observations. Sales replay is not observed retailer cost improvement. Match data and compute budgets and preregister final-test margins/scenarios.

## Git safety and concurrency

Inspect pwd, git status --short --branch, remote identity and HEAD before edits. Do not expose credentials embedded in URLs. Never discard, reset, clean, automatically stash or force-push another person's work. Dirty/diverged trees are synchronization blockers.

Use scripts/sync_main.sh only on clean, idle main. Normal work uses task branches and reviewed PRs. Direct main maintenance requires explicit user authorization; the initial workflow setup is such a maintenance task. Inspect diffs and stage named files, not a blind git add. Push only to VMatee/RL-Inventory-EJOR when authorized.

Only one writer per checkout: Serena OR Codex. Parallel work requires separate worktrees/clones, branches and output directories. Different branch names in the same directory do not prevent conflicts. Never pull, switch branches or edit source in a running experiment's checkout.

## Local execution

Use the existing .venv/bin/python (observed Python 3.10.12). No package/CUDA/system upgrades, data downloads, paid APIs or long GPU jobs without explicit approval and resource scope. Do not print secret environment variables or authentication files.

Serena shell calls must be short, synchronous and noninteractive. Do not start interactive Codex, a server, detached training or an unattended job there. The user may run approved long jobs from a terminal/tmux. Later calls may inspect logs, but do not promise background monitoring.

Use scripts/run_experiment.py for approved runs. Record config, seed, code SHA, dirty state, data fingerprint, versions, command, runtime and exit status. The child algorithm must consume its config/seed explicitly; the wrapper does not inject them. Infrastructure success is not a scientific result.

Raw data, logs, exports and checkpoints stay ignored. Commit small reviewed summaries with provenance under results/summaries. Inspect outputs for private records or credentials before sharing.

## Manuscript

Canonical: manuscript/main.tex, sections/*.tex and references.bib. Preserve the supplied Introduction's framing; substantive changes need review. Draft only requested sections. Never manufacture Methods or Results to fill placeholders.

Use natbib citation keys. Verify new references against primary sources and record support in research/literature/REFERENCE_AUDIT.md. Preserve unverified items as pending. A failed search does not prove absence of prior work. Check current EJOR format and AI-use disclosure requirements before submission.

Run static checks after edits; compile and visually inspect the PDF when TeX is available. Missing TeX is a blocker, not a successful build. Word/PDF are derived review copies, not competing sources.

## Checks and handoff

```bash
.venv/bin/python scripts/check_project.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_experiment.py --config experiments/configs/smoke.json --seed 0
```

Current tests validate plumbing, not a research model. Report exact commands/results, failures, untested items, changed files, branch/commit and next task. Update docs/STATUS.md and docs/SESSION_LOG.md. Add scientific claims only with evidence in docs/CLAIMS.md. Stop after the accepted task rather than implementing the entire roadmap.
