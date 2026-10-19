# RL-Inventory-EJOR

**Working title:** *When Is a Short Demand History Enough? Decision-Sensitive Policy Learning for Inventory Control*

**Stage:** M4 M5 development-baseline pilot completed and M4b results audit prepared. The proposed research method, theoretical contributions, final-test generalization and retailer benefits remain **unproved**; development cost comparisons are not journal findings.

## Start here

- [Current status and next action](docs/STATUS.md)
- [Agent instructions](AGENTS.md)
- [ChatGPT / GitHub / local workflow](docs/WORKFLOW.md)
- [Task queue and acceptance criteria](docs/TASKS.md)
- [Research charter](docs/PROJECT_CHARTER.md)
- [Manuscript source and build](manuscript/README.md)

## Local workspace layout

The local workspace is `~/Desktop/work/research journal/RL-Inventory-EJOR/`. The **Git repository is the `github/` child**, not the workspace parent. All versioned source, manuscript, experiment protocols and tests stay inside `github/`. The sibling `code/` holds the isolated `code/.venv` Python environment and convenient links to the versioned source. The Serena configuration remains in the parent `.serena/` directory so the connected plugin can inspect both children. Always run Git commands from `github/` (or specify its path), and use `../code/.venv/bin/python` for research Python. See [environment setup](environment/README.md). Do not create a second Git checkout in `code/`.

## Completed development pilot and M4b analysis (2026-10-19)

**Do not rerun the 192-job one-shot M4 campaign.** M3 was merged at `9151cec`, then PR #9 merged at `5d01105` and the original M5 development pilot completed **192/192 jobs** across all four GPUs and two CPU workers. The verified local (Git-ignored) session is `results/runs/m4-approved-yc4xtrp1/`, with `baseline_results.csv`, `aggregate_summary.json`, complete output hashes and 5,376 audited M1 transitions. This was a 12-series single-origin **development** sales-as-requests simulation, **not** a final EJOR evaluation or actual retailer cost estimate.

M4b provides [Audited development results](results/summaries/M4_BASELINE_RESULTS_AUDIT.md), a [development/holdout design proposal](experiments/protocol/M4B_DEVELOPMENT_PROTOCOL.md), reusable `scripts/analyze_m4_results.py`, new regression tests and an [independent GPT-6 Pro review handoff](docs/M4B_INDEPENDENT_REVIEW_HANDOFF.md). The scripts analyze saved outputs **read-only by default**; no new GP, RL or GPU jobs are started.

```bash
# From this github/ checkout: verify existing results, with NO writes or new runs
../code/.venv/bin/python -B scripts/analyze_m4_results.py --session results/runs/m4-approved-yc4xtrp1
```

The original item-level 2017 Favorita data remain pending authorized Kaggle access. No final M5 test, external validation or novelty claim is authorized by M4b. See [current status](docs/STATUS.md) and the [claim register](docs/CLAIMS.md).

## Research direction

Can a short initial demand history justify changing a replenishment policy when the demand model is uncertain? We investigate whether inventory-specific sensitivity of **policy-cost differences** helps a learned policy avoid exploiting an inaccurate model without becoming uniformly conservative.

Core scope: single-item, periodic-review lost sales; known positive fixed lead time; exogenous demand observed after each period; limited initial real-data histories; GP demand posterior; known stock-flow equations; neural policy improvement. GP models unknown demand, not known inventory accounting.

GP + RL, Bayesian uncertainty and baseline-relative policy improvement are established ideas. Novelty must be demonstrated against prior work. See [claims](docs/CLAIMS.md) and [proof obligations](theory/PROOF_OBLIGATIONS.md). Do not reopen EV charging, rolling service constraints, multi-echelon control or censored-demand inference without a documented research decision.

## One project record, complementary tools

| Component | Responsibility |
|---|---|
| GitHub main | Reviewed manuscript, code, protocols, decisions and small evidence summaries |
| ChatGPT web | Literature verification, scientific criticism, planning, drafting and interpretation |
| SeneraAiServer / Serena | Inspect this PC checkout, synchronize safely, edit scoped files, execute short checks and inspect logs |
| Local Codex, optional | Implement one accepted task, tests and code review under AGENTS.md |
| Local PC / user terminal | Data processing and approved long experiments |

GitHub holds the authoritative **reviewed version**, but uncommitted local work must be preserved. Synchronization is explicit, not automatic. Only one agent writes a checkout at a time. ChatGPT does not continue working after the conversation ends.

## Codex from the code/ workspace

The local entry files are `../code/README.md`, `../code/AGENTS.md`, `../code/CODEX_PROMPT.md` and `../code/start_codex.sh`. `code/AGENTS.md` is a startup adapter to this repository's canonical rules, not a second research policy. Canonical source still lives here under `src/`.

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/code"
bash start_codex.sh --check  # no Codex model session
bash start_codex.sh          # user-terminal interactive session
```

Review `CODEX_PROMPT.md` before sending it: the first task approves the existing M1 engineering conventions for **M2 only**, not an unattended full study. The [complete implementation plan](docs/CODEX_IMPLEMENTATION_PLAN.md) defines M2-M7 outputs, scientific gates and tests. This setup does not implement those milestones or verify Codex login/model access.

After a reviewed Git sync, run `../code/.venv/bin/python scripts/install_codex_workspace.py` from this checkout to refresh the four local entry files. The installer protects unknown/local edits instead of overwriting them. The source templates are in `infrastructure/codex_workspace/`.

## Local quick start

```bash
cd "/home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR/github"
git status --short --branch
# Only for a clean, idle main checkout:
bash scripts/sync_main.sh
../code/.venv/bin/python scripts/check_project.py
../code/.venv/bin/python -m unittest discover -s tests -v
../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/smoke.json --seed 0
```

To verify the M1 deterministic inventory simulator without RL training, run `make m1-reference` and `../code/.venv/bin/python -m unittest discover -s tests -v`. The M1 model equations, period timing and terminal boundary are in [the model specification](theory/INVENTORY_MODEL.md); conventions are selected for implementation and require owner review before M2.

The smoke run checks repository plumbing only. It does not train GP/RL, download data or generate inventory performance. See [runbook](docs/EXPERIMENT_RUNBOOK.md). The Python environment belongs to the *sibling* workspace directory `../code/.venv` (Python 3.10.12), not to the Git repository. Installation and version snapshots are documented in [environment setup](environment/README.md).

## Manuscript

Edit `manuscript/sections/*.tex` and `manuscript/references.bib`. LaTeX is canonical; PDF/Word exports are review copies. The Introduction is imported from the supplied Word draft, with its source archive and checksum retained. Other sections remain placeholders.

```bash
make manuscript  # Requires latexmk, BibTeX and elsarticle
```

This is not a complete submission. Check current EJOR requirements before submitting. No new bibliography verification or research results are implied by importing the draft.

## Evidence plan

1. Synthetic instances and small-state DP references (generated by code; not an external download).
2. M5 Walmart primary sales-driven replay with proposed initial histories of 28, 56, 112 and 224 days. **All five source CSVs were acquired and hash-verified locally; M3 chronological preprocessing/splits are not frozen yet.**
3. Original 2017 Corporación Favorita *item-level* competition for external validation after the method/protocol are frozen. Its original raw files are **not yet downloaded** because Kaggle authentication and competition-rule acceptance are required on the user's PC. See [dataset plan](data/DATASET_PLAN.md) and [Favorita acquisition instructions](data/sources/FAVORITA.md).

M5/Favorita contain sales, not complete uncensored demand or actual inventory cost ledgers. Costs and lead times are scenario assumptions unless documented otherwise. Match information and compute; count calibration, validation and pretraining. Posterior credibility is not frequentist coverage. Only M5 raw acquisition is currently complete; raw Favorita remains access-gated, and no dataset preprocessing or experimental training has been performed.

## Repository map

- `AGENTS.md`: the single canonical instruction file for local Codex and other project agents.
- `docs/`: status, tasks, workflow, claims, decisions and handoffs.
- `manuscript/`: editable LaTeX, bibliography and provenance.
- `research/`, `theory/`: references, source archives, novelty and analysis.
- `src/inventory_ejor/`, `tests/`: research implementation and tests; `pyproject.toml` supports `pip install -e .` from `github/` into `code/.venv`.
- `experiments/`: configurations, protocol and baseline registry.
- `data/`: locked dataset plan, source metadata and SHA256 provenance; **two external datasets** planned, M5 source files verified locally, Favorita Kaggle access pending. Raw and processed bytes stay local.
- `results/runs/`: local logs/manifests, ignored by Git.
- `results/summaries/`: small reviewed evidence returned to GitHub.
- `scripts/`: synchronization, static checks and provenance runner.
- `.github/`: PR template and manually triggered checks only.

## Next milestone

**M1: finalize inventory event timing and implement a tested minimal simulator.** Do not begin large RL training before the simulator and exact reference are validated. EJOR is the target, not a guaranteed outcome. No automatic cloud training, paid APIs or self-hosted GitHub runner are configured.

## Start the finalized initial development baseline campaign

The owner has delegated the initial run settings; no further option selection is needed for this scope. From `<workspace>/code`, use `bash run_baselines.sh --check` for read-only preflight, or `bash run_baselines.sh` to start the sealed 192-job M5 development run in the foreground (four GPU lanes and two CPU lanes). Do not change branches, sync or run Codex in this checkout during execution. The real campaign is not launched during preparation. Full protocol, safety behavior and remaining research boundaries: [BASELINE_RUN_PROTOCOL](docs/BASELINE_RUN_PROTOCOL.md). Numerical and whole-stack synthetic acceptance: [readiness report](results/summaries/M4_RUN_READINESS_20261018.md). Raw and processed data/results remain local.
