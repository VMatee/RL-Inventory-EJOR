# Research decision log

2026-10-20 PR #12 response to independent REQUEST CHANGES at `ff05c5b`:

- Treat audit false success as a blocking defect. Require the actual M4c
  persisted authorization context and strict shared schemas/identities at
  scoring and audit boundaries; do not retain a numerical-only success path.
- Compute the integer reference target by exact division; report terminal
  batches before next-period receipts. Keep M1 unchanged and check results
  with a separate absolute-arrival oracle and test-only rational oracle.
- Use bounded POSIX temporary writes, file synchronization, atomic
  no-overwrite publication and directory synchronization. Existing objects
  must also be verified and synchronized; a failed synchronization never
  returns success. These guarantees apply to the private execution store,
  not retrospectively to M4c EvidenceStore.
- Pin the complete local Python package snapshot plus declared actual runtime
  versions; state that this is not a hermetic binary/runtime image. Recompute
  I/O projections from required declared context rather than trust totals.
- Retain trusted-owner limitations, M4d-1 integration gates and every scientific
  choice PENDING OWNER APPROVAL. No new real observations or experiments.

2026-10-20 M4d-0 engineering decisions (provisional until independent PR review):

- Isolate the new engineering branch in a separate Git worktree, because an
  unrelated Codex session is active in the project workspace. Do not modify
  the merged `main` checkout or original M5/results directories.
- Implement **synthetic development ONLY**, with explicit independent owner
  execution approval and source history/outcome releases. A trivial, pinned
  empirical reference checks the architecture; no GP/RL/final evaluation.
- Persist real executed synthetic fit and scorer trace as locally private,
  content-addressed evidence; independently reconstruct from pinned learner
  and separately released synthetic outcomes. Do not confuse recorded hashes
  or local owner attestations with proof of honest M4d selection execution.
- Add metadata-only I/O estimates and admission checks; DO NOT silently
  remove M4c source hashes or install an unsafe unrestricted shared cache.
  Actual performant batching and M4d-1 executor remain future review gates.

2026-10-20 M4c engineering decisions (the older rows remain historical):

- PR #11 critical follow-up: treat unguarded direct adapter access as an actual
  supported-API defect; reauthorize each exact read and persist metadata receipts
  before returning values. Do not use a reusable armed-source flag.
- Separate metadata attestation validation from value authorization. Require
  actual canonical specification/result/access artifacts for calibration/final;
  refuse placeholder hashes, substituted files and incomplete phase coverage.
  Unsigned records remain trusted attestations, not proof of execution, owner
  identity or scientific validity. M4d must verify model dependencies and complete
  actual validation/calibration execution before enabling protected experiments.
- Preserve candidate A/B/C and all owner scientific gates. Clarify conditional
  finite-catalog interpretation, limited temporal replication and warm-state
  continuation tuning; no new real data or empirical conclusions are introduced.

- Preserve legacy M3/M4 schemas; confine real-M5 legacy preparation/execution
  to exposed d_225. A separate staged API checks metadata and owner records
  before observation callbacks. Old planners cannot silently accept new stages.
- Validate full-context phase geometry and nonadaptive embargo together, for
  every declared origin; keep known M5 `[1,253)` development permanently.
- Separate learner and scorer capabilities. Calibration requires frozen
  procedure selection; final access also requires frozen calibration. Owner
  approval and source/code/spec identity are separate from metadata validation.
- Candidate cohort uses a pinned metadata frame without sales screening; retain
  A/B/C chronology alternatives. Cohort count/seed, chronology, estimand,
  dependence assumptions, power, costs, margin and execution are all **PENDING
  OWNER APPROVAL**. No proposed date or passing test is a scientific freeze.
- Refuse unsupported pooling/pretraining rather than accepting a lineage boolean.
  Document shared development/validation/calibration information separately.
- No additional observation values or real model execution are authorized in
  M4c. The six-method M4d matrix and boundary panels are readiness proposals.

| Date | Decision | Rationale |
|---|---|---|
| 2026-10-17 | Adopt limited-demand-data decision-sensitive inventory policy learning | Latest supplied research brief; earlier rolling-service-control idea is not the active main contribution |

| 2026-10-17 | Adopt GitHub-first canonical LaTeX, one-writer local execution and reviewed evidence handoffs | User requests ChatGPT web + GitHub + SeneraAiServer + optional local Codex; research scope unchanged |
| 2026-10-17 | M1 *engineering* convention selected for validation: after-arrival decision state, order at t received start t+L, demand after order, lost sales, holding before next receipt; no additional terminal valuation | Previous model brief left event timing and terminal treatment unspecified. Explicitly documented with independent hand fixture and tests; **not claimed to be author-approved final scientific convention**. Confirm before M2/theory comparisons. |
| 2026-10-17 | Retain two external real-sales datasets only (M5 primary, original 2017 item-level Favorita frozen external validation) plus one synthetic data track | User requested acquiring all *planned* data ahead of M2. M5 files were verified; Favorita remains blocked by required Kaggle rules/account. Data acquisition does not authorize leakage-unsafe preprocessing, new empirical claims or substitutions. |
| 2026-10-17 | Owner explicitly approves current M1 conventions as the M2 engineering reference and authorizes M2 only | Actual session instruction says “Use CODEX_PROMPT.md as my task specification” and explicitly approves after-receipt decisions, positive fixed L, receipt at t+L, lost sales, holding before next receipt, placement ordering costs and zero additional terminal salvage/penalty. Preserve current initial pipeline and integer actions. This does not approve every final publication assumption or later milestones. CPU-only bounded tests/demos, existing environment, <=120 seconds per process; no installation, data download, GPU/training, sweep, commit/push/merge. |
| 2026-10-17 | M2 implementation uses known iid finite-support demand, full reachable-state DP and constant capped base-stock grid tuning | Authorized engineering choices within M2; ties use smallest exactly minimizing action/level, zero reference gives undefined relative gap, budget exhaustion fails explicitly without truncation. See `theory/M2_REFERENCE.md` and M2 evidence report. No novelty, theorem, learned-policy or retail outcome claim. |
| 2026-10-17 | Correct M2 fairness by tuning a horizon-aware base-stock variant alongside the naive constant comparator | User explicitly requested correction after independent review. Order zero for remaining <= L using only known horizon/lead time; same grid, law, state, costs and per-variant allowance. The unchanged tiny example has DP=horizon-aware cost 2.875, naive cost 3.000: the earlier 0.125 gap disappears with the fairer horizon-aware baseline. Preserve historical evidence and M1 conventions; no search for a positive-gap replacement, no M3 or training. |

| 2026-10-18 | Owner confirms reviewed M1/M2 merge at `14d0741` and explicitly authorizes M3 only | Rechecked clean local main and live GitHub main at that SHA; created `feat/m3-data-information-protocol`. Unrelated launcher work remains on `chore/remove-codex-launcher` at `cd43843`. No M4, GP/RL training, downloads, package changes, commit/push/merge authorized. |
| 2026-10-18 | M3 engineering: canonical evaluation sales source, pre-origin overlap checks, immutable budget-specific learner files and separate evaluator outcomes | The overlapping sales files are not independent data; chronological/date and access ledgers enforce declared information, without interpreting sales as uncensored demand. Original files remain read-only. |
| 2026-10-18 | Propose disjoint phase contexts/outcomes, shared origins and shortest-history cohort screening without replacement | Proposed scientific choices, NOT owner-accepted final assumptions. The early d_225 development demonstration is the first complete 224-day-history case, not a chosen final test. Final dates, cohort rule, shared development allowance, initial state and covariate availability remain pending review. |
| 2026-10-18 | Count retained cohort-screening information across rolling origins and keep pretraining/pooling separate | A fixed cohort can encode older observations outside a later 28-day window. The ledger records them and labels richer information rather than silently claiming an isolated 28-day experiment. Synthetic counts remain separate; no demand model was fitted in M3. |

| 2026-10-18 | Correct learner-artifact noninterference by separating logical dataset version from trusted full-source identity | Independent review demonstrated that changing only withheld d_226 changed learner bytes through `history.dataset`. Owner explicitly authorized M3 corrections only. Keep all raw SHA256/integrity checks in trusted manifest schema 2; use a predeclared version label in learner artifacts and pin their complete checksum, series, origin, budget and normalization. The label must be fixed independently of outcomes; trusted dispatch must bind it to source provenance. No final split or M4 authorization implied. |
| 2026-10-18 | Record study-wide historical access as a distinct-cell union, separately from individual budgets | Demonstration uses 1,120 selected history cells and 224 candidate-screening cells, of which 140 are shared: 1,204 distinct cells, including 84 extra excluded-candidate cells. Deduplicate overlapping origins and nested budgets. Retain explicit ex-post M5 roster selection/survivorship warning; this accounting does not certify ex-ante assortment availability. |

| 2026-10-18 | Owner authorizes M4a data and baseline SOURCE preparation only, with inspection before any execution | Preserve M3 engineering acceptance at PR #8 / 9151cec. No GP fits, numerical baseline/GPU validation, baseline scoring, RL training or final-holdout access is authorized. Existing uncommitted M4 preparation sources were backed up before review. |
| 2026-10-18 | Prepare one development bundle from 32 fixed M5 candidates without replacement, same d_225 origin and four historical budgets | 12 eligible series and 48 learner views; historical union 3,248 cells. This is a reviewable development cohort, not a final publication sample or a seed search. Original Favorita remains blocked by account authorization. |
| 2026-10-18 | Prepare four initial baselines and independent GPU jobs, not distributed training of one tiny GP | Empirical/Gamma-Poisson base-stock on CPU, GP base-stock and one-step GP rollout on one isolated GPU per job; four GPU lanes planned. No DCL/TED/HDPO, full MPC or proposed method is claimed. CPU work is retained where GPU overhead may dominate. Speedups and numerical correctness are unmeasured. |
| 2026-10-18 | Separately authorize tiny CPU/GPU synthetic numerical validation of M4, not baseline execution | Direct M1-NumPy-Torch comparison over 72 seeded state/horizon scenarios and six opt-in fixtures per isolated RTX 3090 passed; 142 ordinary tests passed. The two-step synthetic GP smoke fit is not an M5 baseline training result. PR #9 remains draft; approval template stays false, final protocol and all 192 baseline jobs remain blocked. See results/summaries/M4_NUMERICAL_VALIDATION_20261018.md. |

| 2026-10-18 | Owner delegates all remaining initial baseline pre-run choices and readiness | Fix existing 12-series M5 development cohort, four budgets, four methods and one seed (192 jobs), four GPUs plus two CPU lanes, 300s/job and 7200s/session. Prepare sealed one-shot foreground start and finalize PR #9; do not start real M5 jobs in preparation. |
| 2026-10-18 | Validate full scheduler/worker/report pipeline on an isolated synthetic clone | Real 12-job synthetic acceptance used all four GPUs; add fault/timeout/interruption/source-change/lock tests. Record descriptive-only outputs and refuse incomplete aggregation. No claims about GP calibration, retailer cost savings or EJOR novelty. |

| 2026-10-19 | Interpret finished 192-job M5 development run without retroactive model selection | M4b analyzes saved session `m4-approved-yc4xtrp1` read-only. Keep its original outcomes/data unchanged. Treat GP-rollout cost reductions as exploratory, distinguish 12 series from 48 correlated budget pairs, account for 5.92x extra synthetic compute, startup unavoidable shortages and high-volume concentration. No p-values, GP safety claims, 28-day non-inferiority, retailer costs, external validation or novel method are established. |
| 2026-10-19 | Provide a concrete prospective M4b development design but do not open final outcomes or execute next experiments | Propose guarded chronological phase geometry, crossed 3x2 model/controller matrix, matched compute/data/synthetic robustness, causal-neutral sales interpretation, and an independently reviewable hypothesis for inventory-structured policy-cost uncertainty. The other GPT-6 Pro account has not completed independent review; provide read-only reviewer handoff, not simulated approval. |
