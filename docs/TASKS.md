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

## M4a - Initial baseline preparation [source prepared for review; runs NOT authorized]

Owner authorization on 2026-10-18 covers preparing data and code ONLY, with GPU-focused future execution and a stop before fitting/scoring. M3 has merged at `9151cec` (PR #8). The available M5 data were prepared into a new 12-series/48-learner-view development bundle from 32 fixed candidates; no final holdout dates are frozen. Favorita remains authorization-gated.

Source implementations: empirical iid base-stock, Gamma-Poisson base-stock, exact log1p-Gaussian-surrogate GP base-stock, and one-step GP rollout over a fixed base-stock continuation policy. Rollout is NOT DCL or a globally optimized MPC. The GP is NOT a Poisson-likelihood model or a calibrated guarantee. Details, proposed 192-job configuration and four-GPU scheduling are in `docs/M4_BASELINE_PREPARATION.md`.

The plan builder and default launcher do not fit/score anything. Explicit owner approval, numerical-validation confirmation, exact plan hash and unchanged clean source are required for execution. Numerical tests are separately opt-in in `tests/validation_m4_numerics.py` and have not run. Preparation/interface tests are not scientific or numerical evidence. Stop for owner inspection.

## M4b - Strong learning baselines and validation [planned; separate approval required]

After M4a review and numerical checks, separately authorize limited baseline pilots, then stronger GP+MPC/DCL and appropriate TED/HDPO reproductions or clearly labeled adaptations. Implement explicit likelihood/joint sampling, epistemic/aleatoric separation, comparable information access and declared compute. Final comparator roster and evaluation assumptions remain pending; do not assume GP superiority or start the proposed method without a separate specification.

## M5 - Decision-sensitive mechanism and analysis [planned]

Depends M4 and prior-art audit. Compare robust baseline regret, Bayesian risk, DCL/TED and data-efficient GP control. Same GP/optimizer/data as plain baseline; change only proposed mechanism. Account for model misspecification and adaptive policy selection. No invented guarantees.

## M6 - Frozen publication study [planned]

Freeze holdouts, budgets, seeds, non-inferiority margin, scenarios and baselines. Synthetic, M5 and external Favorita tracks. Cost-data frontier, baseline harm, service, calibration and runtime with dependence-aware uncertainty. Long runs require resource approval.

## M7 - Submission preparation [planned]

Claims-to-evidence audit, complete proofs/results, bibliography verification, independent reproduction, current EJOR and institutional ABDC checks, actual author information, declarations and PDF review. No acceptance guarantee.
