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

## M2 - Exact reference and baseline [implemented and locally tested; awaiting owner review]

Depends M1. Small finite-support DP plus tuned base-stock. Compare tiny instances with exhaustive enumeration. Specify bounds/truncations, initial and terminal states. Deliver config, fixtures and paired evaluation.

Implemented finite iid demand validation, exact reachable-state finite-horizon DP, forward policy evaluation, and naive constant and horizon-aware capped base-stock with exact known-model finite-grid tuning on the same grid and allowance. No inventory truncation; explicit state/work/time failure. Tiny independent rational/calendar enumeration covers 128 contingent policies per fixture. Before the review correction: 61 tests passed; after: 66 tests passed, including unchanged M1 tests. The unchanged demo now reports DP=horizon-aware S=1 cost 2.875 and naive S=1 cost 3.000. The earlier 0.125 gap disappears with the horizon-aware baseline; no new example was selected. Independent hand/calendar tests cover the cutoff, L exceeding the horizon, and no lookahead. Ruff E,F,I,B,UP and formatting checks pass. Source: base `2cbce59fd0cf0f738e177a0ef7e8bc6347882431` plus the uncommitted M2 diff on `feat/m2-exact-reference`; no standalone M2 commit yet. Evidence and exact commands: `results/summaries/M2_REFERENCE_VALIDATION_20261017.md`. Implementation evidence only; stop for review before M3/M4.

## M3 - Data/information audit [raw-data acquisition partially completed: M5 verified, Favorita Kaggle authorization outstanding]

The user authorized acquisition of both planned external datasets. All five M5 source CSVs were downloaded locally (450,472,284 bytes), verified against organizer Zenodo file sizes/MD5, SHA256 recorded with source provenance and raw schema counts; see `data/manifests/m5_verified_20261017.json` and `results/summaries/M3_DATA_ACQUISITION_20261017.md`. The original item-level 2017 Favorita competition requires Kaggle credentials and accepted rules; absent on the connected PC, **not downloaded**. `scripts/fetch_favorita.py` provides authenticated CLI acquisition and archive verification after user action. No raw file enters Git.

**M3 scientific work still pending:** verify access/redistribution terms; define SKU eligibility, treatment of returns/zero sale records/censoring, frozen chronological splits and leakage-safe real-data budgets; account for cross-series, calibration/validation and pretraining. Raw acquisition is not evaluation readiness. Favorita remains a prospective frozen external validation track.

## M4 - Plain GP baselines [planned]

Depends M2 and data specification. Simple Bayesian demand model, GP posterior, GP+MPC and ordinary GP+DCL; explicit likelihood/joint sampling, epistemic/aleatoric separation and matched budgets. Select and pin approved dependencies. Do not assume GP superiority.

## M5 - Decision-sensitive mechanism and analysis [planned]

Depends M4 and prior-art audit. Compare robust baseline regret, Bayesian risk, DCL/TED and data-efficient GP control. Same GP/optimizer/data as plain baseline; change only proposed mechanism. Account for model misspecification and adaptive policy selection. No invented guarantees.

## M6 - Frozen publication study [planned]

Freeze holdouts, budgets, seeds, non-inferiority margin, scenarios and baselines. Synthetic, M5 and external Favorita tracks. Cost-data frontier, baseline harm, service, calibration and runtime with dependence-aware uncertainty. Long runs require resource approval.

## M7 - Submission preparation [planned]

Claims-to-evidence audit, complete proofs/results, bibliography verification, independent reproduction, current EJOR and institutional ABDC checks, actual author information, declarations and PDF review. No acceptance guarantee.
