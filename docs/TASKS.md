# Task queue and acceptance criteria

Statuses are planned/in progress/blocked/validated. Mark validated only with code SHA and evidence. Begin one task at a time.

Codex may start in sibling `code/` using its AGENTS adapter and `CODEX_PROMPT.md`. Detailed engineering requirements for M2-M7 are in `docs/CODEX_IMPLEMENTATION_PLAN.md`; this queue remains the completion record. The saved prompt approves current M1 conventions for M2 only **when explicitly sent by the owner**. Instruction/launcher setup does not mark M2-M7 complete or authorize a full training sweep.

## M0 - Workflow setup [validated: infrastructure only]

Canonical LaTeX/BibTeX, source archive, README/AGENTS, workflow, sync/check scripts, provenance and infrastructure tests. See SESSION_LOG. No scientific results.

## M1 - Model specification and minimal simulator [implemented and locally tested; engineering conventions accepted for M2]

Agree on units, lead-time convention, receipt/order/demand timing, initial stock and pipeline, action bounds, holding/shortage/order costs, horizon and terminal treatment. Document before implementation; do not silently resolve scientific ambiguity.

Implement src/inventory_ejor/envs with tests for zero demand/order, exact depletion, lost sales versus backlog, L=1 and L>1 pipeline progression, arrival date, nonnegative inventory, cost decomposition, invalid inputs and terminal accounting. Cross-check hand-computed trajectories. No GP/RL, downloads or new dependencies without approval.

Implementation evidence: `theory/INVENTORY_MODEL.md` gives explicit state/event equations, lead-time and terminal semantics; `src/inventory_ejor/envs/lost_sales.py` contains a pure transition and a Gymnasium wrapper; `tests/fixtures/m1_hand_calculated.json` is an independently hand-calculated reference (cost 47), cross-checked by deterministic tests including a separately written event-calendar comparator. `scripts/run_m1_reference.py` replays the fixture. See `results/summaries/M1_SIMULATOR_VALIDATION_20261017.md` for exact checks/code SHA.

Acceptance for use in M2: local automated tests and fixture pass **AND** the owner reviews/accepts selected event timing, initial-state interpretation and terminal handling. Do not present a provisional convention as confirmed by the user. Update formulation, tests and decision log together if modified.

The owner explicitly accepted the current conventions for M2 in the 2026-10-17 session instruction. Final publication assumptions remain open; no M1 source or test fixtures changed.

## M2 - Exact reference and baseline [reviewed and merged at 14d0741]

Current owner confirmation (2026-10-18): reviewed and merged into main at `14d0741`. The implementation narrative below preserves historical pre-merge evidence.

Depends M1. Small finite-support DP plus tuned base-stock. Compare tiny instances with exhaustive enumeration. Specify bounds/truncations, initial and terminal states. Deliver config, fixtures and paired evaluation.

Implemented finite iid demand validation, exact reachable-state finite-horizon DP, forward policy evaluation, and naive constant and horizon-aware capped base-stock with exact known-model finite-grid tuning on the same grid and allowance. No inventory truncation; explicit state/work/time failure. Tiny independent rational/calendar enumeration covers 128 contingent policies per fixture. Before the review correction: 61 tests passed; after: 66 tests passed, including unchanged M1 tests. The unchanged demo now reports DP=horizon-aware S=1 cost 2.875 and naive S=1 cost 3.000. The earlier 0.125 gap disappears with the horizon-aware baseline; no new example was selected. Independent hand/calendar tests cover the cutoff, L exceeding the horizon, and no lookahead. Ruff E,F,I,B,UP and formatting checks pass. Source: base `2cbce59fd0cf0f738e177a0ef7e8bc6347882431` plus the uncommitted M2 diff on `feat/m2-exact-reference`; no standalone M2 commit yet. Evidence and exact commands: `results/summaries/M2_REFERENCE_VALIDATION_20261017.md`. Implementation evidence only; stop for review before M3/M4.

## M3 - Data/information audit [engineering merged in PR #8 at 9151cec; scientific protocol not frozen]

The user authorized acquisition of both planned external datasets. All five M5 source CSVs were downloaded locally (450,472,284 bytes), verified against organizer Zenodo file sizes/MD5, SHA256 recorded with source provenance and raw schema counts; see `data/manifests/m5_verified_20261017.json` and `results/summaries/M3_DATA_ACQUISITION_20261017.md`. The original item-level 2017 Favorita competition requires Kaggle credentials and accepted rules; absent on the connected PC, **not downloaded**. `scripts/fetch_favorita.py` provides authenticated CLI acquisition and archive verification after user action. No raw file enters Git.

**2026-10-18 M3 implementation:** reusable streaming M5 ingestion; immutable learner/evaluator views; disjoint chronological phase contracts; exact 28/56/112/224-day accounting; pooling/pretraining/normalization/tuning ledgers; separate learner artifacts; deterministic fixtures and bounded CPU preparation. Source base `14d0741` plus uncommitted diff on `feat/m3-data-information-protocol`. Evidence: `results/summaries/M3_IMPLEMENTATION_REVIEW_20261018.md`. The owner explicitly authorized M3 only. No final dates/holdout frozen, no new downloads, model fitting, commits or publication claims.

**2026-10-18 review correction:** separated full-source fingerprints from learner-visible logical dataset versions; retained pinned artifact and identity validation; added complete-byte d_226 noninterference and independent study-union checks. Trusted manifest schema 2 records 1,204 historical cells without double-counting shared screening. Current checks: 119 total tests, 53 M3 tests, six dedicated correction tests passed; M1/M2 reference outputs unchanged. Review remains open; this is implementation evidence, not scientific acceptance.

**M3 scientific acceptance still pending:** verify access/redistribution terms; review/approve proposed SKU eligibility, treatment of zero sale records/censoring, chronological phases and real-data budgets; approve shared cross-series development, calibration/validation and pretraining rules. Favorita returns/fractional units need decisions after authorized access. Raw acquisition is not evaluation readiness. Favorita remains a prospective frozen external validation track.

## M4a - Initial baseline preparation and run [completed 2026-10-18]

Original GitHub PR #9 merged at `5d01105`; four-GPU M5 development session `results/runs/m4-approved-yc4xtrp1/` completed 192/192 jobs, status `complete_and_hash_verified`, 93.659 s. The same 12 series/28,56,112,224-day historical budgets share a 28-day future window at d_225. This is **not** a publication experiment, and does not establish GP superiority, 28-day non-inferiority or retailer cost savings. Do not launch the one-shot campaign again. Preparation-only descriptions and the 2026-10-18 execution setup remain historical documentation.

## M4b - Results audit and protocol draft [independent Codex APPROVE; minor fixes implemented]

Use `scripts/analyze_m4_results.py` to read-only audit saved 192 jobs, provenance and learner hashes, rebuild aggregate values, independently replay 5,376 M1 transitions, report matched effects at the 12-series unit, relative/absolute cost components, startup unavoidable shortage and unequal compute budgets. Per-series artifacts under ignored `results/analysis/` must not be pushed. Source-anchored descriptive facts in `results/summaries/M4_BASELINE_RESULTS_AUDIT.md`. No model fitting/GPU execution or new evaluation data in M4b. M4b development protocol draft: `experiments/protocol/M4B_DEVELOPMENT_PROTOCOL.md`. An independent **Codex GPT-6.1 Ultra** review was received and verified the 4.11% arithmetic but found two blocking integrity gaps. Fixes include evaluator/ledger reconstruction, per-job wrapper binding, terminal/calendar replay, safe path checks, a feasible two-block final holdout **candidate**, synthetic full-session positive/negative tests, and 166/166 ordinary tests. See `docs/M4B_CODEX_REVIEW_RESPONSE_20261019.md`. Independent **Codex GPT-6.1 Ultra re-review APPROVED** the scoped M4b software audit at `eef0fd4`, with no BLOCKING or MAJOR issues. The author subsequently fixed three MINOR issues: valid zero-cost relative summaries, sealed calibration access after later validation selection, and 12-type synthetic symlink regression tests. These last minor changes are author-tested, not separately peer reviewed. The other-account Web Pro review was not performed; optional instructions remain in `docs/M4B_INDEPENDENT_REVIEW_HANDOFF.md`. Authoring-account tests are not independent peer review.

## M4c - Scientific proposal and access firewall [merged as PR #11; owner scientific freeze pending]

Choose/record chronological development/calibration/validation/final partitions, eligibility and common information allowances prospectively and without opening later outcomes. Preserve the examined d_225 pilot as development. Predefine initial stock/pipeline, cost/terminal scenarios and matched per-policy compute protocol; disclose sales censoring. Document treatment of dependent item-store/temporal observations and noninferiority-margin justification before final evaluation.

Implemented metadata compiler and staged preparation APIs, explicit scientific
freeze/selection/calibration/task-release records, source/code/spec binding,
full-origin embargo integration, and negative synthetic tests. Legacy real-M5
access is restricted to d_225; malformed task metadata and symlinks are checked
before artifact reads. Candidate protocol, estimands/power strategy and M4d
readiness are documented, not scientifically frozen. Review
`docs/M4C_ACCESS_FIREWALL.md` and `results/summaries/M4C_VERIFICATION_20261020.md`.
Actual M4d runner integration, owner choices, new observation releases and
execution remain separate gates. No new real observations or models were used.

PR #11 follow-up hardens direct production adapter calls and requires persisted
selection/calibration evidence before protected reads. Evidence covers declared
series/origin/history/outcome access, not actual model/seed execution or scientific
validity. See `results/summaries/M4C_FIREWALL_FOLLOWUP_20261020.md`; the strict M4d
integration contract is mandatory before enabling a new executor.

## M4d-0 - Synthetic-only execution/evidence prototype [implemented; independent review pending]

The owner requested M4d-0 on 2026-10-20. On a separate writer worktree,
implemented `src/inventory_ejor/data/m4d0_execution.py` as a narrow synthetic
reference learner-only plan + approved CPU fit and separate released scorer,
with private, content-addressed trace and run evidence; independent
`m4d0_audit.py` replay; metadata-only `m4d0_io.py` and
`scripts/check_m4d0_io.py` to reject an over-budget preparation estimate.
Tests cover release separation, code/data/seed/scenario fingerprints,
tampering, symlinks, zero requests, rehashed adversarial scores, and
persistence failures. Details: `experiments/protocol/M4D0_SAFE_EXECUTION.md`.
Independent review of `ff05c5b` requested changes. B1/C1–C4 follow-up now adds
shared strict validators with mandatory persisted authorization context,
exact integer fitting, canonical terminal reporting, independent arrival
replay and atomic durable publication/retry checks. Expanded validation:
255 repository tests, including 37 M4d-0 tests, pass; re-review remains pending.
See `docs/M4D0_CODEX_REVIEW_RESPONSE_20261020.md`.
**This is NOT a GP/RL trainer, an M5 execution grant, real selection evidence,
or an optimized real-data batch reader.** Await independent PR re-review;
all M4d-1 real-data, GPU and final-outcome gates remain unapproved.

## M4d - Stronger crossed baselines [planned; separate execution approval]

Add Empirical + one-step rollout and Gamma–Poisson + one-step rollout to complete 3-demand-model × 2-controller matrix; recency-aware baseline and GP fixed-calendar-time-scale ablation. Then GP planning/DCL and appropriate TED/HDPO or explicit adaptations as feasible. Test forecast calibration, epistemic/aleatoric differences and matched data/compute. New versioned development-only runs need separate scope and authorization; original 192-job artifacts remain immutable.

## M5 - Decision-sensitive mechanism and analysis [planned]

Depends M4 and prior-art audit. Compare robust baseline regret, Bayesian risk, DCL/TED and data-efficient GP control. Same GP/optimizer/data as plain baseline; change only proposed mechanism. Account for model misspecification and adaptive policy selection. No invented guarantees.

## M6 - Frozen publication study [planned]

Freeze holdouts, budgets, seeds, non-inferiority margin, scenarios and baselines. Synthetic, M5 and external Favorita tracks. Cost-data frontier, baseline harm, service, calibration and runtime with dependence-aware uncertainty. Long runs require resource approval.

## M7 - Submission preparation [planned]

Claims-to-evidence audit, complete proofs/results, bibliography verification, independent reproduction, current EJOR and institutional ABDC checks, actual author information, declarations and PDF review. No acceptance guarantee.
