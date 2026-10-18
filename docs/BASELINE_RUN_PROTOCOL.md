# Frozen initial M5 baseline development run

## Authority and scope

On 2026-10-18 the owner delegated final pre-run decisions and asked for a ready-to-start baseline campaign on all four GPUs, without another methodological-option approval cycle. This document fixes the **initial development run only**, not the publication study. Preparation may run synthetic numerical and end-to-end acceptance fixtures. The real M5 run starts **only when the user invokes the delivered launch command**.

The run is deliberately the already prepared 12-series cohort, with no further selection/search based on held-out results. Final-test dates, broader representative cohorts, published learning-baseline reproductions, our proposed method, causal retailer claims and a final paper's statistical conclusions are NOT included.

## Fixed data and information access

- Exact corrected M3 bundle: `data/processed/m3-demo-9vex_g9j/`.
- M5 organizer source hashes stay pinned; original 2017 Favorita remains unavailable and is not substituted or needed for this initial run.
- 32 seed-0 metadata-ranked candidates; 12 historically eligible series; no replacements after inspecting outcomes.
- Each model receives exactly one 28/56/112/224-day learner artifact and deterministic calendar features. The trusted scorer alone reads the corresponding 28-day outcome sequence starting at d_225.
- 48 learner views, 12 evaluator trajectories. Study-wide initial historical access is 3,248 distinct cells, including 560 extra excluded-series screening cells.
- No pooled fitting, pretrained model, online demand refitting, outcome-guided tuning or final-test access. The policy observes current inventory/time, but model parameters stay fixed during replay.
- M5 observed sales are treated as exogenous simulation requests. No reconstruction of censored latent demand, inferred stockouts or real retailer accounting is claimed.

## Fixed decision/model settings

Use `experiments/configs/m4_baseline_preview.json`: positive fixed lead time 3, maximum order 20, zero initial stock and two zero pipeline entries; holding 1, lost-request penalty 10, variable/fixed order costs 0, zero extra terminal valuation. Base-stock levels are the complete declared integer grid 0..60. Use horizon-aware order cutoff so replenishments arriving outside the horizon are not placed. All methods share the same initial state and realized request path.

Zero starting stock makes initial positive-lead-time shortages unavoidable in this particular diagnostic scenario; do not attribute them to model quality. Grid-edge selections and order-cap binding are recorded as warnings. Do not silently retune caps or remove unfavorable series after this run. This is an initial functioning/comparison study, not a performance-optimal business configuration.

Four methods: empirical iid + base-stock; explicit Gamma(1,1)-Poisson + base-stock; log1p exact-Gaussian GP + base-stock; same GP + one-step rollout with base-stock continuation. GP is a transformed Gaussian surrogate, not a count-likelihood GP. This rollout is NOT DCL, TED/HDPO, global MPC, RL or the novel proposed method. GP hyperparameters use 75 fixed Adam steps at 0.05, float64, declared noise floor/jitter; 256 predictive tuning/decision paths; model-generated counts above the declared guard cause failure rather than tail clipping. Seed 0 is for debugging/development, not independent statistical replication.

## Compute and start contract

192 jobs = 12 series x 4 budgets x 4 methods x 1 seed: 96 GPU and 96 CPU jobs. Run four single-GPU lanes by physical UUID (GPU 0..3), with two CPU lanes and two BLAS threads per worker. GPU memory allocation is capped at 70% per process; per-job wall cap 300 seconds, session wall cap 7,200 seconds. Failures stop new jobs; active jobs finish or are reaped within their bounded timeout. SIGTERM/SIGHUP/Control-C trigger controlled child cleanup. An unresolvable stale lock is not automatically deleted. External jobs not honoring this project's lock cannot be controlled; the launcher refuses currently busy devices rather than killing another project's process.

Source, interpreter/package versions, config, prepared manifest, learner/evaluator hashes, plan and approval are pinned. A project execution lock prevents a second campaign and blocks `scripts/sync_main.sh`. The local one-shot launcher has an exclusive `STARTED.json` marker to prevent duplicate campaigns. Never edit the checkout, pull, switch branches or start Codex here during execution. Unexpected failures remain saved and are not automatically retried or omitted from averages.

After successful completion, all output receipts are checked. `baseline_results.csv` and `aggregate_summary.json` are created under the session's ignored `results/runs/m4-approved-*/` directory. The summary refuses incomplete campaigns or altered result/trace fingerprints. Raw item-level traces remain private and Git-ignored. Means and fill-rate summaries are descriptive, not significance or superiority claims.

## User operation

The finalized local adapter is `code/run_baselines.sh`.

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/code"
bash run_baselines.sh --check   # read-only readiness check, optional
bash run_baselines.sh           # starts the approved campaign in the foreground
```

No token, approval editing, extra dataset download, manual branch decision, or new Codex task is required. Keep the terminal open; do not start a second copy. A preflight refusal due to changed code/data/runtime, already-used plan, stale lock or a GPU now used by another project is intentional and never silently bypassed.

This scope does not authorize publication final-test evaluation, extra datasets or the proposed research method. Favorita is a later external-validation task; its absence does not block this initial M5 development run.
