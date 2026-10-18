# M4 initial baseline run readiness - 2026-10-18

## Decision

The user explicitly delegated final pre-run choices and requested a ready-to-start four-GPU baseline run without another judgment cycle. The fixed development scope is `docs/BASELINE_RUN_PROTOCOL.md`: the existing 12-series M5 bundle, four history budgets, four initial methods and seed 0, totaling **192 jobs** (96 GPU, 96 CPU). These settings are accepted for an **initial development run only**. No final holdout, external Favorita, RL/novel-method execution, publication superiority or causal retailer saving is authorized or inferred.

The assistant finalizes/reviews source and provides a sealed local launch plan. **The user will start the real M5 campaign; it is not run in this preparation task.** No Codex work is required.

## Execution problems addressed

The earlier numerical check certified kernels, not the whole workflow. Finalization strengthened the real execution path:

- An exclusive project lease is acquired **before** any session output creation. Collisions preserve the existing lock; stale locks are not auto-deleted.
- Children consume immutable session copies of the exact plan and approval.
- Input artifact SHA256 values and Python/package versions are checked before dispatch; clean code/source fingerprints are checked in each worker.
- SIGTERM/SIGHUP/Control-C and per-job/session timeout handling reap the wrapper's child process group. Only the launched session's processes are signaled; other projects are untouched.
- A failed job stops new work. Exit zero is insufficient: correct output identity, trace/result hashes, successful wrapper provenance, and unchanged source are required.
- Atomic progress and final session receipts are saved. Automatic summaries refuse incomplete campaigns, changed files or mismatched costs. Completed runs produce private `baseline_results.csv` and `aggregate_summary.json`.
- `sync_main.sh` refuses while the project execution lock exists. The user launch adapter has a one-shot marker to prevent duplicate campaigns from the same approval.

No M1 stock-flow equations, M2 oracle, GP likelihood, number of data observations or proposed final-test split was changed in this task. The chosen numerical baselines remain empirical/Gamma-Poisson/GP base-stock and GP one-step rollout, not DCL/TED/HDPO/RL or the paper's proposed method.

## Tests actually executed

### Offline regressions and real subprocess fault tests

**152 ordinary tests passed** after adding nine execution-safety tests and a minimal-CI preparation test for missing optional numerical packages. The new suite runs genuine short-lived subprocesses using artificial stub outputs, not retail data:

1. Two CPU lanes complete jobs with verified wrapper receipts and automatic tables.
2. Existing lock blocks execution without creating a session directory.
3. A failed job prevents later jobs and aggregate reporting.
4. Per-job timeout terminates the worker and records exit 124.
5. Session deadline reaps active wrappers and stops the queue.
6. A worker that changes source cannot be treated as successful.
7. Modified results are rejected by the report hash check.
8. Changed learner inputs are rejected before launching.
9. SIGTERM to the provenance wrapper reaps its child and records interruption.

Tests initially exposed a missing `origin` field in the independent scheduler stub fixture; that fixture was corrected. Production job contracts always contain the origin. Existing preparation tests continued to pass. Scoped new-code Ruff lint/format and the project structure/citation-key check passed. Legacy repository-wide lint debt is not represented as resolved.

### Full real worker/scheduler acceptance on four GPUs

Executed `scripts/validate_baseline_stack.py --execute-synthetic --gpus 0,1,2,3` under a 120-second outer cap. This clones the reviewed code locally, synthesizes tiny M3-compatible files in that isolated clone, commits its synthetic config locally, and runs the **actual scheduler -> provenance wrapper -> worker -> model/controller -> inventory replay -> output auditor/report generator**.

The acceptance configuration has 3 synthetic series, one 28-observation budget, four methods, seed 0: **12 jobs**. GP fits are two optimizer steps, simulations use eight paths and four future periods. No actual M5 or Favorita CSV is copied into the clone or consumed. The fixture-only approval cannot authorize the real campaign because it is bound to a different plan, data fingerprint and local synthetic commit.

Measured first successful end-to-end acceptance:
- All **12/12** jobs completed; CPU and GP methods were actually invoked on **synthetic data**.
- All four physical GPU lanes **0,1,2,3** participated.
- All output identities, wrapper receipts, unchanged-source checks and hashes passed.
- Aggregate JSON and per-job CSV were produced, and the project lock was released.
- Approximately **8.13 seconds** scheduler wall time. This is NOT a measured speedup or forecast of full M5 runtime.
- Evidence retained in local `code/validations/m4-stack-d6oxjesw/validation_report.json` and its `scheduler.log`; raw synthetic runtime artifacts are not uploaded.

The direct opt-in six-test CPU/GPU kernel and two-step-GP fixtures were previously passed independently on all four RTX 3090 devices; they include 72 seeded state/lead-time/horizon scenarios with 24 first-order overrides and tolerance 1e-12 against M1.

## Data and run boundaries

M5 inputs and the corrected M3 development bundle are pinned. The prepared cohort contains 12 historically screened item-store series, 48 learner views and a study-wide initial historical union of 3,248 sales cells. Each learner sees only its assigned n observations plus deterministic calendar information. Forecast models stay frozen during replay; predictive rollouts are model simulation, not new real observations. Initial stock/pipeline, costs, terminal rule and action/grid caps are identical across methods.

The final implementation is ready for the user's first **bounded development** launch. Numerical calibration, model convergence on real data, generalization, empirical ranking and EJOR novelty are unknown until studied. The final publication experiment requires a representative cohort, additional seeds and scenarios, stronger specialized baselines, and a defensible methodological contribution. Missing Favorita access does not prevent this M5-only pilot; it remains a later authorized external-validation task.

## Handoff

After Git review/merge, the local plan and real authorization are regenerated against final clean `main`. Local `code/BASELINE_READY.json` pins plan/approval hashes, while `code/run_baselines.sh` provides the user start command. The examples still default to false; the actual approval records the owner's **delegated initial development scope**, not an invented signature.

`bash run_baselines.sh --check` verifies readiness only. `bash run_baselines.sh` starts in the foreground, once. No training task is detached or scheduled by this preparation. GPU reuse by other projects, modified files/versions, stale locks or an already-started campaign cause a visible refusal, never silent overrides or deletion of previous work.
