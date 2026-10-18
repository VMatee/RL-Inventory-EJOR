# M4a: data and GPU-ready baseline preparation - REVIEW BEFORE RUNNING

**Scope authorized on 2026-10-18:** prepare data and baseline code, use the existing four GPUs in the *future execution design*, and stop for owner inspection. **No demand-model fit, baseline scoring, RL training, numerical GPU test, or experiment sweep is authorized by this preparation.**

M3 is merged at `9151cec`. Its data interfaces are reused; M1/M2 dynamics and reference implementations are unchanged. This document is a proposed DEVELOPMENT preview, not a frozen publication experiment or a claim that these initial baselines constitute the paper's final competitor set.

## 1. Data ready for inspection

| Data | Current status | Role |
|---|---|---|
| Original M5 | All five files present locally; source SHA256 identities verified by M3 preparation/audit | Primary retail-sales source |
| M5 development bundle | `data/processed/m3-demo-9vex_g9j/`, manifest schema 2 | 12 eligible series from a fixed set of 32 candidates; 48 learner views, 12 evaluator trajectories |
| Original item-level Favorita 2017 | NOT downloaded; local Kaggle credentials/competition authorization still unavailable | Future external-retailer validation; not silently replaced |
| Synthetic demand | Existing finite-law generator and M1/M2 test fixtures available | Numerical correctness and controlled research, not extra real observations |

The development configuration is `experiments/configs/m4_data_development.json`: seed 0, fixed hash-ranked 32-candidate roster, no replacement after screening, first origin d_225, 28-day outcome horizon, and nested initial histories of 28/56/112/224 days. The original early development window is retained; no final-test dates are selected or inspected. Eligibility uses at least one positive sale in the common 28-day pre-origin window. Twelve passed and twenty were excluded; this is not a representative publication cohort and no seed search was used to improve the sample.

The study inspected **2,688 selected history cells plus 560 additional excluded-candidate screening cells = 3,248 distinct historical sales cells**. The 896 candidate-screening cells include 336 already counted selected-history cells. Evaluator outcomes are separate (336 cells). There are 1,813 zero-sales cells among the 2,688 selected historical cells. These are sales, not inferred latent demand or stock availability. Ex-post assortment/survivorship and censoring caveats remain.

All original files, prior M3 bundles, results and backups are retained. New preparation creates a fresh ignored directory; it never rewrites the original data. Do not move raw or derived retail records into Git. The previous five-series M3 bundle remains preserved but is not the default M4a preview input.

## 2. Exactly which initial baselines are implemented in source?

| Method ID | Demand representation | Inventory decision rule | Proposed execution |
|---|---|---|---|
| `empirical_base_stock` | IID resampling of the allowed history; plug-in model, no epistemic posterior | Horizon-aware capped order-up-to rule, tuned by model-only simulations | CPU |
| `gamma_poisson_base_stock` | Conjugate Gamma-Poisson law with declared prior, one sampled rate per complete trajectory | Same horizon-aware rule and the same candidate-level grid | CPU |
| `gp_base_stock` | Exact Gaussian GP on standardized `log1p` sales, conditional on fitted hyperparameters | Same horizon-aware rule and grid | One GPU per independent job |
| `gp_rollout` | The same GP specification, fitting seed and training data | One-step action rollout over a fixed tuned base-stock continuation policy | One GPU per independent job; batched path/action costs |

**Not included:** DCL, TED, HDPO, a globally optimized MPC, neural RL, a neural-ensemble comparator, or our inventory-sensitive methodological contribution. Do not rename this rollout as DCL/MPC or claim published-method reproduction. Those remain later separately scoped work. This initial suite tests a simple probabilistic model, the value of the GP representation, and the incremental value of one-step lookahead.

### Demand and policy definitions

All fitting receives only an immutable, checksum-pinned M3 learner view. No full dataset hash, evaluator handle, or raw reader is passed to a sampler/policy. The trusted scorer loads outcomes after fitting and tuning and sends `action(remaining, state)` only the current M1 state and time, never current/future sales. Fitted demand-model parameters stay frozen throughout replay; no hidden online conditioning/refitting is performed.

For Gamma-Poisson, `shape = prior_shape + sum(history)` and `rate = prior_rate + n`. One latent rate is drawn for a whole simulated path, then Poisson noise is drawn conditional on that rate. This separates within-model demand noise from posterior parameter uncertainty; it is an IID rate model, not a seasonal forecasting model.

The GP uses a constant mean and an ARD RBF covariance on relative time and sine/cosine weekday features. It fits Gaussian marginal likelihood on **training-only** standardized log1p sales. At prediction time it jointly samples the latent Gaussian vector over future dates, adds separate Gaussian likelihood noise, and applies `round(max(expm1(z), 0))` on the original log scale. This is an explicitly defined transformed-Gaussian count surrogate, **not a Poisson-likelihood GP**, not a posterior over hyperparameters, and not automatically calibrated. Negative transformed values have a declared atom at zero; large/nonfinite generated counts cause failure instead of silently clipping the upper tail. A proper count-likelihood model may be needed later; that is not resolved by source preparation.

The policy tunes S in the stated grid using only simulated demand from the fitted model. It orders `max(0, min(Q_max, S - on_hand - sum(pipeline)))`, except that orders are zero when `remaining <= L`. Under the current zero-extra-terminal-value convention those orders cannot serve an in-horizon demand. The rollout compares each current order in `0..Q_max` on common simulated paths, then uses the fixed base-stock rule for subsequent simulated decisions. It is not clairvoyant future-action optimization. GP-base-stock and GP-rollout use the same fitting seed, base-stock tuning draw count and estimator settings; rollout additionally spends decision-time simulation. The additional computation is counted rather than represented as an equal-compute comparison.

These numerical implementations have **not been executed in this task**. Source review, syntax and orchestration tests do not establish numerical validity.

## 3. Proposed development run - currently locked

`experiments/configs/m4_baseline_preview.json` proposes:

- 12 series x 4 budgets x 4 methods x 1 seed = **192 jobs** (96 CPU jobs and 96 GPU jobs).
- One shared scenario: L=3, Q_max=20, zero initial after-arrival stock/pipeline, holding=1, shortage=10, variable/fixed ordering=0, and zero extra terminal value.
- Base-stock grid 0..60, 256 tuning paths, 256 decision paths for rollout, GP float64 and 75 Adam steps.
- A 300-second per-job wall-time limit through the existing provenance runner; CPU time is separately bounded in the worker. No automatic retry or hidden extra sweep after failure.
- Fixed seed 0 is only an integration preview. Multiple seeds, stronger baselines, more scenarios and adequate statistical power must be approved for the actual study.

All scenario numbers are **proposals to inspect**, not tuned optima, business accounting observations or final journal settings. Initial shortages with positive lead time, end-of-horizon behavior and binding order/grid bounds must be investigated before scientific claims. Proposed outputs flag a selected upper grid bound and count order-cap binding periods.

The information ledger records fitting/normalization and GP hyperparameter access, simulation counts, trial counts and runtime. The four methods share real-data access, but their computations/hardware differ: **this preview does not establish matched-compute superiority**. The scenario initial state is not inferred from future sales. Every run remains sales-driven simulation rather than observed retailer savings.

## 4. Four-GPU execution design

Use four independent subprocess lanes, one per physical GPU (IDs 0,1,2,3), rather than spreading a small 28-224-point GP across all cards. Each worker sees one GPU via `CUDA_VISIBLE_DEVICES` and computes its GP and batched rollout costs there. The scheduler resolves physical indices to GPU UUIDs before launching, checks that the requested devices are idle (at most 256 MiB used and 10% utilization) and have the requested memory headroom, and refuses to interrupt other projects. Availability may change later; the preparation-time idle snapshot is not a reservation.

CPU lanes are separate (two workers, two BLAS/OpenMP threads each) and cannot see GPUs. CPU I/O, hashing, JSON/CSV preparation and small classical calculations are not pushed to GPU solely for appearance. No GPU speedup, perfect fourfold scaling, or superior GPU accuracy is claimed before profiling.

A fresh Python interpreter per job avoids forking an initialized CUDA context. Float64, explicit seeds and `CUBLAS_WORKSPACE_CONFIG` support reproducibility within a fixed stack, but do not guarantee bitwise equality across releases/devices. The launcher limits GPU allocations to 70% per process, uses one project-session lock and preserves every job's logs/results. CPU workers have an 8 GiB address-space cap. GPU host memory is checked through peak RSS at completion rather than setting a CUDA-incompatible address-space cap. A failed job stops new jobs; in-flight jobs finish under their time limits.

## 5. Safe commands NOW: prepare/inspect only

From `~/Desktop/work/research journal/RL-Inventory-EJOR/github`:

```bash
# Creates a new local review bundle. Does NOT fit or evaluate a baseline.
../code/.venv/bin/python scripts/prepare_baselines.py \
  --config experiments/configs/m4_baseline_preview.json

# Replace PLAN_DIR with the printed m4-plan-* directory.
# Default is DRY_RUN_ONLY: no workers, GPUs, fitting or scoring.
../code/.venv/bin/python scripts/run_baselines.py \
  --plan PLAN_DIR/plan.json

# Prints an unexecuted numerical checklist; does NOT perform numerical tests.
../code/.venv/bin/python scripts/validate_baseline_numerics.py
```

The plan records input/config/source hashes, source commit, all task identities and allowed resource settings. `approval.example.json` contains **false for every permission**. A dirty-source plan is inspectable but never executable. After source changes or merging a PR, regenerate the plan; approval for a previous hash does not carry forward.

No baseline run can begin through the provided CLI unless `--execute`, an exact-plan-hash-bound owner approval, completed numerical-validation confirmation, permitted GPU use, and clean unchanged source are all supplied. The Boolean confirmation is an owner attestation, not a fabricated test receipt. This is a guard against accidental use, not an OS sandbox against intentionally modified code.

## 6. Required next review and separate authorizations

1. Review this document, dataset cohort, source implementation and the plan. Decide whether the provisional scenario and four-baseline scope are the right first pilot.
2. **Synthetic numerical validation separately authorized and executed on 2026-10-18.** The opt-in `tests/validation_m4_numerics.py` suite now checks 72 seeded NumPy/GPU/M1 trajectory scenarios (including nonzero pipelines and first-order overrides), Gamma-Poisson reproducibility and tiny GP posterior sampling. All six opt-in tests passed separately on each of the four RTX 3090 devices, using one real device UUID per process. The ordinary test suite passed 142/142. See `results/summaries/M4_NUMERICAL_VALIDATION_20261018.md`. These tiny synthetic GPU checks do **not** fit or score a real M5 baseline.
3. **Still pending:** owner review of numerical evidence, proposed scenario, worker/scheduler execution handling, runtime limits and source/plan identity. A limited M5 development pilot requires a **new explicit approval** and a regenerated exact-hash-bound clean-source plan. The `numerical_validation_completed` approval flag remains false in every saved example; never flip it automatically after tests.
4. Full research comparisons, final holdout access, DCL/TED/HDPO reproduction and our proposed method each need their own scientific/execution scope. No entire-paper training command is supplied or silently started here.

## 7. Primary implementation references (API guidance, not research evidence)

- GPyTorch 1.14 GPU exact-regression tutorial: https://docs.gpytorch.ai/en/v1.14/examples/02_Scalable_Exact_GPs/Simple_GP_Regression_CUDA.html
- PyTorch 2.9 CUDA semantics and device visibility: https://docs.pytorch.org/docs/2.9/notes/cuda.html
- PyTorch 2.9 reproducibility and deterministic settings: https://docs.pytorch.org/docs/2.9/notes/randomness.html

These sources support API/design choices only. They do not establish our method's novelty, numerical correctness, predictive calibration, speedup, or suitability for EJOR acceptance.
