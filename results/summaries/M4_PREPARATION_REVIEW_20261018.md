# M4a preparation-only handoff - 2026-10-18

**Status: SOURCE AND DATA PREPARED FOR OWNER REVIEW; NO BASELINE RUN.** The owner requested data preparation, then baseline code matched to those data, with a four-GPU execution design and an explicit stop before running. This report is infrastructure/data-preparation evidence, not numerical baseline validation or research results.

## Starting state and preservation

GitHub `main` and the local base were `9151cece320f0d0563720e7c48790f72862d5211` (merged M3). The PC already had 13 uncommitted M4 preparation files on `feat/m4-baselines-prepare-only`, with no observed process writing to this project. Before continuing, those files were archived with SHA256 at local `code/backups/m4-prepare-entry-20261018T085915Z/`. A separate snapshot captured 205 existing raw/processed/results files for preservation checking. No destructive reset, Git clean, system package change, driver update or dependency installation was used.

## Data actually prepared and checked

`experiments/configs/m4_data_development.json` uses the unchanged M3 preparation logic: fixed seed 0, 32 hash-ranked candidates without replacement, origin d_225, 28-day development horizon and budgets 28/56/112/224. It creates `data/processed/m3-demo-9vex_g9j/` (schema 2).

| Check | Observed preparation output |
|---|---:|
| Original M5 CSVs verified before/after | 5 |
| Candidate series | 32 |
| Eligible / excluded series | 12 / 20 |
| Learner views / evaluator trajectories | 48 / 12 |
| Distinct selected historical sales cells | 2,688 |
| Additional excluded-candidate screening cells | 560 |
| Study-wide historical union | 3,248 |
| Distinct development outcome cells | 336 |
| Data preparation runtime | 8.60 seconds (CPU) |
| Data preparation peak RSS | 55,936 KiB |

A read-only independent audit against the original CSVs confirmed the new bundle's source identities, 48 learner views and study counts. No raw source or older prepared bundle was modified. These measurements characterize data handling only. Final holdout dates, representative cohort, sales-censoring interpretation and publication scenarios remain unfrozen. Original item-level Favorita 2017 is still not present; credential/authorization flags were absent. No alternative Favorita dataset or unverified mirror was substituted.

## Prepared source deliverables

- `src/inventory_ejor/baselines/models.py`: empirical iid, conjugate Gamma-Poisson and GPU exact GP transformed-Gaussian surrogate sampling code. Models receive only an authorized learner view; no source hash or evaluator path.
- `controllers.py`: NumPy/PyTorch batched cost kernels preserving M1 timing; horizon-aware base-stock tuning and one-step action rollout. Integer/shape/pipeline/action guards were added. **Numerical kernels NOT run.**
- `planning.py`: verified M3 schema-2 task construction, all-budget/cohort consistency, input/source/config hashes, false-by-default approval template and clean-source execution checks. No Torch import or model fitting in planning.
- `launcher.py`: dry-run default, four independent GPU lanes and two CPU lanes, stable physical-GPU UUID resolution, idle/headroom checks, refusal rather than interference with other projects, project execution lock, failure/timeout handling and output preservation. **Scheduler execution NOT run.**
- `worker.py`: future approved fit/tune/score flow, clean-source and permission rechecks, per-learner information ledger, scenario cost components and private trace outputs, runtime/peak-RSS reporting. **Worker NOT invoked.**
- Four entry scripts: `prepare_baselines.py`, `run_baselines.py`, `baseline_worker.py`, `validate_baseline_numerics.py`.
- `tests/test_m4_preparation.py`: 23 preparation-only contract/negative tests; no numerical models or CUDA.
- `tests/validation_m4_numerics.py`: separate opt-in tests for numerical M1 parity, predictive samplers and small GPU/GP operations; **NOT run and outside default discovery**.
- Two versioned development configs and `docs/M4_BASELINE_PREPARATION.md` with equations, assumptions, reference API sources and reviewer gates.

Initial methods: `empirical_base_stock`, `gamma_poisson_base_stock`, `gp_base_stock`, `gp_rollout`. The latter is a one-step rollout with a fixed base-stock continuation rule, not DCL, TED, HDPO, a globally solved MPC or our proposed contribution. The GP uses `log1p` Gaussian regression with a declared nonnegative rounded inverse transform; it is not a Poisson-likelihood GP or a calibrated Bayesian guarantee.

## Proposed plan, not executed results

The configuration proposes **192 jobs**: 12 series x 4 history budgets x 4 methods x 1 seed. There are 96 GPU jobs (48 GP-base-stock, 48 GP-rollout) and 96 CPU jobs. Future GPU execution uses one isolated device per process and all four devices for independent tasks; it does not concatenate VRAM or distribute one tiny GP over four cards. No speedup was measured.

The shared scenario is L=3, Q_max=20, zero initial stock/pipeline, holding=1, shortage=10, zero ordering costs, and zero additional terminal value. Grid 0..60, 256 predictive paths, 75 GP optimization steps, float64 and 300-second per-job limit are **proposals for inspection**, not accepted research parameters. The methods share real history access; differing computation must be disclosed. Final scientific fairness/terminal/censoring/statistical decisions remain open.

A preview was generated at `data/processed/m4-plan-81i4sj3x/` while source was uncommitted. It is intentionally **not executable**. After the reviewed source commit, generate a fresh clean-source plan; the exact local path is provided in the final handoff and local `code/BASELINE_REVIEW_20261018.md`. Plan and approval files stay Git-ignored.

All approval-template flags are false. `run_baselines.py` without `--execute` displays only `DRY_RUN_ONLY`. Actual execution additionally requires an explicit owner approval bound to the exact plan hash and confirmation of completed numerical validation. This is protection against accidental use, not a security boundary against deliberately rewritten code.

## Checks performed versus deliberately NOT performed

**Performed:** data preparation; independent original-CSV audit; 23 preparation-only tests; Python source parsing/compilation without importing numerical models; scoped Ruff lint/format; plan construction; default dry-run/negative permission checks; GPU inventory query using nvidia-smi metadata only; preservation hashes. The GitHub workflow remains manual-only, and no remote CI run was triggered.

**NOT performed:** any new baseline sampler invocation, parameter fitting, GP training, policy tuning/scoring, numerical vector-kernel experiment, GPU allocation/compute test, actual multiprocess scheduling, RL training, published-method reproduction, final-test or Favorita evaluation. M1/M2 source remains unchanged. Existing numerical reference tests need not be rerun simply to format or inspect new source; their historical evidence is not labeled as a new execution.

The default numerical-validation command was invoked without approval and printed **NOT RUN**. Numeric validation is a separate future authorization, followed by another review before even the small development baseline pilot. No baseline numerical result can be inferred from the preparation test count.

Final preparation-only checks: **23/23 contract tests passed** (2.680 seconds); all 12 new Python source/test files compiled for syntax without execution; scoped Ruff lint and formatting passed; repository/citation static checks passed. The no-execute launcher reported `DRY_RUN_ONLY`, `models_fitted=0`, `baselines_scored=0` and `approved=false`. All **205/205 pre-existing protected files** matched their entry SHA256 and size snapshots exactly. Manual CI syntax/scope was checked but no remote workflow was triggered. No complete numerical-test-suite or baseline run is claimed.

## Safe review commands

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
../code/.venv/bin/python -m unittest discover -s tests -p 'test_m4_preparation.py' -v
../code/.venv/bin/python scripts/prepare_baselines.py --config experiments/configs/m4_baseline_preview.json
# Use the newly printed path; this command only displays the proposed jobs:
../code/.venv/bin/python scripts/run_baselines.py --plan "data/processed/m4-plan-REPLACE_ME/plan.json"
../code/.venv/bin/python scripts/validate_baseline_numerics.py
```

Review `docs/M4_BASELINE_PREPARATION.md` before authorizing numerical validation. Do not approve a run merely because the scripts parse or preparation tests pass.
