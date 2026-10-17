# Codex implementation plan: from M1 to a reproducible EJOR study

Status: **implementation specification, not a completed experimental pipeline**. Derived from this repository's PROJECT_CHARTER, TASKS, INVENTORY_MODEL, EVALUATION and BASELINE_REGISTRY. Additional engineering recommendations below do not establish new scientific results, new scope, or publication novelty.

## Authority and current starting point

Canonical science/permissions: AGENTS.md, docs/PROJECT_CHARTER.md, docs/DECISION_LOG.md and the current user task. TASKS.md tracks completion; STATUS.md records the latest evidence. This document expands execution requirements; it does not automatically authorize every milestone.

Observed at setup (2026-10-17, source base 758d439): M1 deterministic kernel and Gymnasium wrapper present; 39 tests passed. M5's five raw CSVs acquired with checksum provenance. Original 2017 item-level Favorita not acquired; Kaggle authorization absent. No M2 DP, GP demand pipeline, learned inventory policy, proposed mechanism or full empirical study exists. Refresh these observations before work.

Codex can implement the engineering components over several reviewed tasks. It must not fill scientific gaps by inventing a theorem, a penalty called 'novel', or a completed benchmark reproduction. M1 engineering-convention acceptance, final dataset splits, the mechanism's actual definition and resource approvals remain explicit gates.

## Proposed module map (create only when its task is authorized)

```text
src/inventory_ejor/
  envs/                     # existing M1 stock-flow kernel; preserve API/tests
  demand/                   # finite-support laws first; fitted predictive models later
  solvers/                  # exact finite-horizon DP and scenario optimization
  policies/                 # base-stock; policy interfaces; learned policies later
  models/                   # GP and alternative uncertainty representations
  learning/                 # ordinary policy improvement before proposed safeguard
  data/                     # data contracts, chronological splits and transformations
  evaluation/               # paired outcomes, uncertainty, cost-data frontiers
experiments/configs/        # executable declarative configurations, not undocumented notebooks
scripts/                   # thin CLI entry points using package implementations
results/runs/              # ignored unique run directories and full provenance
results/summaries/         # reviewed small evidence records
```

Reuse existing modules when possible. Avoid building an expansive framework before a tested end-to-end example. Source code belongs in github/, even when Codex starts in code/.

## M2 - Exact reference and classical baseline (first implementation task)

**Entry gate:** the user accepts the documented M1 conventions as the engineering reference for this task. This is not approval of all eventual publication boundary assumptions. If approval is absent, report the specific convention decision; baseline checks and a design note can proceed without silently claiming acceptance.

**Deliverables**

1. A finite-support demand object with explicit integer support and valid probability mass; reject negative support, nonfinite/negative probabilities, zero total mass, and sums outside a declared numerical tolerance. Do not silently renormalize materially invalid inputs. Start with independent identically distributed demand; arbitrary dependence/nonstationarity is not solved by this interface.
2. A finite-horizon dynamic program minimizing expected M1 operating cost over integer actions 0..Q_max. Time-to-go must enter the value/policy key. Reuse the validated pure transition for normal evaluation and document zero additional terminal value. Return values, selected actions, tie-breaking semantics and diagnostic counts.
3. Independent tiny decision-tree or exhaustive-contingent-policy checks. Exhaustive OPEN-LOOP sequences are not an exact comparator for adaptive policies. Do not use future realized demand when selecting an action. Avoid calling the same DP recursion an independent oracle.
4. A baseline policy using the explicitly stated after-arrival inventory position: `position = on_hand + sum(pipeline)`; `order = min(Q_max, max(0, S - position))`. This is a baseline definition, not an optimality claim for lost sales. State whether S is constant or time-dependent; begin with a constant integer S and separately labeled fixed-case zero/constant policies for sanity checks.
5. Tune S on a declared finite grid using exact policy evaluation for controlled known-demand M2 tests. Label such tuning **known-model**, not small-real-data learning. If later simulation tuning is used, separate tuning and evaluation draws.
6. A runnable, validated config and CLI demo under experiments/configs and scripts. Print actual cost, gap to the exact reference, horizon, initial state, costs, support, action range, seed where applicable, and state counts. Require explicit overwrite consent for saved outputs or use a unique run directory.

**Correctness and resource constraints**

- Preserve M1 timing: stock observed after current receipt, pipeline length L-1, an order at t first usable at t+L, loss not backlog, holding before next receipt.
- No silent stock caps. Reachable states are finite for finite horizon and bounded actions; use reachability or justify an exact bound. A computational state limit must fail explicitly instead of returning a truncated solution as 'optimal'.
- Finite-support enumeration may use floating-point expectations: call it an exact mathematical DP solved to numerical precision, state tolerances, and test deterministic cases exactly. Test probability mass, all-zero demand, Q_max=0, L=1 and L>1, horizon < lead time, one-period cases, initial pipeline, cost ties and zero reference cost (avoid division by zero).
- An optimal DP value cannot exceed the cost of an admissible baseline under the SAME initial state, information, costs, horizon and demand law, up to declared numerical tolerance. Verify that applying the returned policy reproduces its value.
- First task budget: CPU-only, one process, per-process timeout <=120 seconds, tiny support and horizon, no dependency changes. Fail with a diagnostic if the state space grows too large. No M5 scanning, data download or neural training is required.

**Acceptance:** independent reference agrees, regressions pass, terminal treatment is visible, invalid configs fail, a new user can run the documented example. Record measured values rather than target numbers. Then stop for review; do not proceed directly to GP training.

## M3 - Leakage-safe data and information contracts

Raw M5 acquisition is complete, but preprocessing and evaluation readiness are not. Download state is separate from scientific readiness.

Implement schema validation and immutable file fingerprints; a chronological split contract with cutoff/horizon, product eligibility, external pretraining information, validation/calibration access and all real-data budgets. Primary initial histories are the proposed 28/56/112/224-day grid, not permission to select whichever looks best after testing.

The M5 validation and evaluation CSVs contain overlapping histories. Never concatenate them as independent observations. Do not read post-cutoff outcomes for normalization, model selection, series eligibility or demand priors. Use synthetic miniature CSV fixtures to test the reader/splitter before inspecting a development subset. No item selection based on final-test behavior.

Specify permitted exogenous features as of the decision time (including publication time of prices/promotions if available). M1's physical observation alone does not supply sufficient information for every dependent demand process. All competitors must receive the same allowed history/forecasts in their comparison track.

Favorita must be the original 2017 item-level competition, not the later family-level data. Account explicitly for returns, noninteger units, missing store-item dates and unobserved stock availability. Do not round/clip/fill scientifically ambiguous records just to satisfy M1. Require an approved transformation/scope decision first. Keep its final holdout out of method development.

**Acceptance:** leakage tests catch deliberately injected future information; budgets account for calibration, tuning and external data; raw sources remain unchanged; transformations have a manifest; legal/access questions are documented. No final holdout tuning.

## M4 - Demand and controller baselines before the proposed method

Start with a simple Bayesian/parametric demand baseline, ordinary GP demand modeling and predictive sampling, GP+predictive optimization, and ordinary GP+DCL-style policy learning. Follow BASELINE_REGISTRY; not all implementations exist yet.

**Demand requirements:** likelihood must match the retained unit/demand convention. A Gaussian regression output clipped to positive values is not silently interchangeable with a count-demand posterior. A non-Gaussian GP needs explicitly approximate inference and corresponding tests. Separate latent-model uncertainty from demand sampling noise; draw joint paths consistently rather than resampling an unrelated latent function at every period. Test repeatability, support, numerical conditioning and model misspecification. Calibration claims need held-out evidence.

**Controller requirements:** publish a common policy interface and information contract. Plain GP-RL, GP-MPC and simple inventory policies must share predictive scenarios/observations and comparable budgets. MPC must respect nonanticipativity: a clairvoyant scenario solution can be a bound, not an implementable competitor. Approximate policy iteration and neural fitting need explicit cost/reward conventions, discount/horizon alignment, convergence diagnostics and checkpoint metadata.

**Published methods:** inspect actual DCL/TED/HDPO sources and versions before reproducing. Name a simplification 'DCL-style' or 'adaptation' until fidelity is verified. A source citation or imported checkpoint does not prove replication. Document offline training information and cost of pretrained policies. No downloading external repos/packages without the scoped task authorization.

**Acceptance:** one small synthetic end-to-end baseline works, agrees with M2 references within measured tolerances where applicable, has independent seeds and no information advantage. Unit/integration smoke checks are not evidence of real-data superiority.

## M5 - Proposed inventory-sensitive policy improvement

This milestone is a **research gate**, not permission for Codex to invent a completed method.

Before implementation, write a method specification addressing: the precise candidate/baseline cost-difference estimand; demand-model posterior; rollouts; inventory sensitivity calculation; uncertainty estimator; change-acceptance rule; treatment of adaptive policy selection; prior-art distinction; approximation errors and computational complexity. Separate posterior credibility from frequentist coverage and independent evaluation.

Keep the same GP, policy backbone and data budgets as the ordinary method when testing the safeguard. Paired demand streams support comparisons but are not a novelty claim. Do not choose a threshold by looking at the final test set or uniformly overstock to make safety look better. If the mechanism is undefined, implement interfaces/tests and report the blocker rather than producing a misleading 'full method'.

**Acceptance:** approved rule is executable, reference/edge cases pass, pivotal matched-backbone ablation is possible, failure cases and computational overhead are reported. Analytical statements enter CLAIMS.md only with a proof or explicitly limited numerical evidence; do not call numerical tests a theorem.

## M6 - Experiment engine, pilots and frozen publication study

Implement a declarative experiment matrix: demand family or dataset/split ID, L, costs, initial state/terminal policy, real-data budget, forecaster, controller, mechanism flag, seeds, simulation allowance and runtime limit. Validate schema and resolve inputs before dispatch. A `--dry-run` should list jobs/resources/output paths without consuming the dataset or starting training.

Each run records immutable config/hash, source commit, data/split hashes, dependency versions, seed streams, CPU/GPU selection, start/end, exit status and observed metrics. Use the existing run wrapper; the child must consume its config/seed. Separate training, validation and test RNGs. Preserve failed runs. Never overwrite another run or mark a failed job completed because a partial result file exists.

Pilot before a full sweep. Numerical results need comparable achieved cost/service and uncertainty, not a favorable reward curve alone. Final metrics: operating-cost decomposition and cost-data frontier; harmful-switch frequency/severity; service outcomes; tail behavior; calibration diagnostics; simulation calls; runtime and memory. For rich-data comparisons, prespecify non-inferiority margin and interval construction; lack of significance is not equivalence. Avoid undefined ratios for zero/near-zero reference cost.

Analysis must account for shared test trajectories, training seeds, and temporal/item dependence. Match uncertainty model and controller separately to isolate gains. Include failure/misspecification regimes, not only successful cases. Rich-data old regimes and short recent histories must not be confused with pure data efficiency.

**Resource gate:** pilot/full training needs explicit job count, CPU/GPU IDs, memory, timeout, disk allowance and stop conditions. Default is not all four GPUs. Independent-seed parallelism can be considered only after profiling and approval. No running code while the same checkout is being edited/synced; use reviewed fixed-commit execution copies for long runs.

**Acceptance:** one small job runs reproducibly, failure/resume rules are tested, outputs trace to source/config/data, final study frozen before test inspection, complete negative and positive results retained. Favorita cannot be marked complete before authorized acquisition and preprocessing validation.

## M7 - Evidence-to-manuscript tooling and submission preparation

Generate tables/figures from saved run artifacts, not hand-entered favorable numbers. Build a claim-to-proof/experiment map and preserve analysis scripts and source revision. Distinguish model-relative results, synthetic control and sales-driven replay; do not claim measured Walmart/Favorita operational savings.

Complete source/version checks, third-party attribution and license compliance. Check current EJOR author guidance and relevant AI-use disclosure at submission time, not from a stale setup note. A functioning implementation is not submission readiness. Draft Methods/Results only when requested and supported by actual outputs.

## Per-task handoff protocol

Every milestone or bounded subtask ends with: changed files; commands and actual outcomes; independent checks; assumptions; evidence paths/run IDs; resource use; failed/untested items; branch/revision and uncommitted changes; one recommended next task. Record the status in STATUS/TASKS/SESSION_LOG without rewriting earlier provenance.

No step is silently marked passed. No new domain is added. No blanket prompt authorizes perpetual training, credentials use, or publishing unreviewed output.

## Tool guidance used for this workspace

Current local `codex --help` verified `--cd`, `--add-dir`, `--sandbox workspace-write`, and `--ask-for-approval on-request` on 0.163.0. Official documentation checked 2026-10-17:
- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/cli/reference

These support startup/permission instructions, not scientific claims. No Codex model session, login, paid API call, or full training job was launched by the documentation setup.
