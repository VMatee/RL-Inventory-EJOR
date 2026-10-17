# Task queue and acceptance criteria

Statuses are planned/in progress/blocked/validated. Mark validated only with code SHA and evidence. Begin one task at a time.

## M0 - Workflow setup [validated: infrastructure only]

Canonical LaTeX/BibTeX, source archive, README/AGENTS, workflow, sync/check scripts, provenance and infrastructure tests. See SESSION_LOG. No scientific results.

## M1 - Model specification and minimal simulator [planned]

Agree on units, lead-time convention, receipt/order/demand timing, initial stock and pipeline, action bounds, holding/shortage/order costs, horizon and terminal treatment. Document before implementation; do not silently resolve scientific ambiguity.

Implement src/inventory_ejor/envs with tests for zero demand/order, exact depletion, lost sales versus backlog, L=1 and L>1 pipeline progression, arrival date, nonnegative inventory, cost decomposition, invalid inputs and terminal accounting. Cross-check hand-computed trajectories. No GP/RL, downloads or new dependencies without approval.

Acceptance: equations and code agree; deterministic tests catch off-by-one errors; reference fixtures are reproducible. Update formulation only after conventions are accepted.

## M2 - Exact reference and baseline [planned]

Depends M1. Small finite-support DP plus tuned base-stock. Compare tiny instances with exhaustive enumeration. Specify bounds/truncations, initial and terminal states. Deliver config, fixtures and paired evaluation.

## M3 - Data/information audit [planned]

Audit M5 provenance, licensing/access and chronological budgets. Download only with authorization; hash raw files and record splits/series selection. Count calibration/validation/pretraining. Keep raw data local. Favorita reserved for frozen external validation.

## M4 - Plain GP baselines [planned]

Depends M2 and data specification. Simple Bayesian demand model, GP posterior, GP+MPC and ordinary GP+DCL; explicit likelihood/joint sampling, epistemic/aleatoric separation and matched budgets. Select and pin approved dependencies. Do not assume GP superiority.

## M5 - Decision-sensitive mechanism and analysis [planned]

Depends M4 and prior-art audit. Compare robust baseline regret, Bayesian risk, DCL/TED and data-efficient GP control. Same GP/optimizer/data as plain baseline; change only proposed mechanism. Account for model misspecification and adaptive policy selection. No invented guarantees.

## M6 - Frozen publication study [planned]

Freeze holdouts, budgets, seeds, non-inferiority margin, scenarios and baselines. Synthetic, M5 and external Favorita tracks. Cost-data frontier, baseline harm, service, calibration and runtime with dependence-aware uncertainty. Long runs require resource approval.

## M7 - Submission preparation [planned]

Claims-to-evidence audit, complete proofs/results, bibliography verification, independent reproduction, current EJOR and institutional ABDC checks, actual author information, declarations and PDF review. No acceptance guarantee.
