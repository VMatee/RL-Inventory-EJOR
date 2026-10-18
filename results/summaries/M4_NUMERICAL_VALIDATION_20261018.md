# M4 numerical-validation review — 2026-10-18

**Verdict: PASS for bounded synthetic numerical checks only.** This validates selected cost-kernel mechanics and tiny-GP execution on four isolated RTX 3090 devices. It **does not approve or run the 192-job M5 development pilot**, any full GP fit, publication study, final holdout, RL training or the proposed inventory-sensitive method.

## Context and authorization

The owner first authorized M4a *data/source preparation without execution* and subsequently explicitly asked to perform the previously proposed **CPU/GPU numerical validation with synthetic fixtures**, while retaining the stop-before-baselines boundary. SeneraAiServer performed this validation directly without running Codex or merging draft GitHub PR #9.

Starting source: `feat/m4-baselines-prepare-only`, `dd68f386ad16155c0f7a080b1258fba3c0b3c3db`, based on M3 `main` `9151cece320f0d0563720e7c48790f72862d5211`. Other active Codex processes had their working directories in an unrelated research project. No baseline worker or run-experiment process was detected. No new dependencies, driver changes, Favorita downloads or changes to M1/M2 equations were made.

## Opt-in tests executed, not merely reviewed

All calls used sibling `../code/.venv/bin/python -B` (Python 3.10.12), `PYTHONDONTWRITEBYTECODE=1`, bounded `timeout`, and explicit `EJOR_APPROVED_NUMERICAL_VALIDATION=1`. CUDA tests additionally required `EJOR_APPROVED_CUDA_VALIDATION=1`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, and exactly one visible GPU via its real NVIDIA UUID.

| Check | Actual result |
|---|---|
| Original CPU numerical fixtures | 3/3 pass; two CUDA fixtures skipped |
| Expanded CPU numerical fixture | All 72 deterministic scenarios match independently replayed M1 transitions; 24 scenarios override the first order |
| GPU 0, expanded opt-in suite | 6/6 pass |
| GPU 1, expanded opt-in suite | 6/6 pass |
| GPU 2, expanded opt-in suite | 6/6 pass |
| GPU 3, expanded opt-in suite | 6/6 pass |
| Normal repository test discovery (no opt-in GP fitting) | 142/142 tests pass |
| Scoped new M4 Ruff lint/format | Pass |
| Hardware metadata preflight via `parse_idle_gpu_inventory` | All four UUIDs accepted, under configured memory/utilization limits |

The strong deterministic parity fixture spans lead times `L in {1,2,3,4}`, horizons `T in {1,2,3,4,6,8}`, three variants each, five synthetic demand trajectories and five base-stock candidates. It includes nonzero initial stock and pipeline, lost-sales/holding/variable/fixed ordering costs, and 24 first-action override cases. For every setting, the independent `inventory_ejor.envs.transition` trajectory agrees with both vectorized NumPy and GPU Torch costs to **absolute tolerance 1e-12** (zero relative tolerance). A separate original 3-path fixture checks M1 parity, and a horizon-aware arrival test checks the ordering cutoff.

Predictive checks verify Gamma-Poisson seeded draws are repeatable and nonnegative. The tiny synthetic GP fixture fits **two optimizer steps** on 28 synthetic historical observations, samples eight four-period paths, checks device/dtype/finite/nonnegative outputs, reproducibility for the same posterior-draw seed, and rejection of an out-of-horizon request. This is a technical GPU acceptance smoke test, **not trained GP baseline evaluation** and provides no evidence of model calibration or numerical convergence.

Original opt-in command (CPU validation, no CUDA):
```bash
EJOR_APPROVED_NUMERICAL_VALIDATION=1 EJOR_APPROVED_CUDA_VALIDATION=0 \
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
timeout 120 ../code/.venv/bin/python -B -m unittest discover -s tests \
-p validation_m4_numerics.py -v
```

Per-GPU tiny fixture (repeat individually for GPUs 0..3, substituting the *actual* GPU UUID as `UUID`, after checking the device is idle):
```bash
EJOR_APPROVED_NUMERICAL_VALIDATION=1 EJOR_APPROVED_CUDA_VALIDATION=1 \
CUDA_VISIBLE_DEVICES=UUID CUBLAS_WORKSPACE_CONFIG=:4096:8 \
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 timeout 35 ../code/.venv/bin/python -B \
-m unittest discover -s tests -p validation_m4_numerics.py -q
```

Only the opt-in numerical-validation fixture files were executed. The baseline scheduler's default dry-run and plan remain unchanged: **no `run_baselines.py --execute`, no baseline `worker`, no M5 cost scoring and no `results/runs/m4-approved-*` created**. The reviewed plan's `approval.example.json` continues to have false flags. These validation environment variables do **not** authorize a baseline execution plan.

## Boundaries and outstanding review gates

- These tests establish cost-kernel agreement **for the tested synthetic states**. They do not guarantee an exhaustive proof of all integer/state/horizon combinations or independently certify the complete worker/scheduler pipeline. Four-GPU parallel scheduling, timeout/failure cleanup, output-manifest integrity and M5 model-fit/evaluation separation have not been exercised end-to-end.
- The GP remains a log1p-Gaussian surrogate with fitted point hyperparameters and heuristic discretization, not a count-likelihood GP or calibration guarantee. Two-step synthetic GPU fitting shows API viability only.
- The first M5 preview uses 12 historically selected item–store series, a single development origin, a 28-day evaluation horizon, historical budgets 28/56/112/224 and one planned seed. It is **not** a representative EJOR publication cohort. All simulation costs require the declared sales-as-requests scenario interpretation; M5 provides no directly observed retailer inventory costs or stockout flags.
- Approve the proposed lead time, maximum order, zero starting stock/pipeline, holding/shortage ratio, predictive sampling and tuning grid **before** authorizing even the small M5 pilot. Explicitly agree how to handle unavoidable lead-time exposure and terminal effects.
- A future pilot must use a new, reviewed plan hash after these test/document changes, and an explicit owner approval recording the allowed job count, specific devices, time limits, and access. Do not convert the earlier default `approval.example.json` into an execution approval, and do not merge this draft PR without owner review.

**Engineering conclusion:** bounded numerical validation is suitable to support a subsequent separately approved *small development* pilot, subject to review of the scientific scenario and execution harness. No baseline improvements, statistical results, GPU speedups, EJOR novelty, or external validity are claimed.
