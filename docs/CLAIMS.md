# Claim register

| ID | Claim | Status | Required evidence |
|---|---|---|---|
| H1 | Inventory-sensitive comparisons improve limited-data policies | Hypothesis | Matched ablations; none yet |
| H2 | GP improves over simple/neural uncertainty models | Hypothesis | Crossed model/controller experiments |
| H3 | Short histories approach rich-data performance in identified regimes | Hypothesis | Prespecified non-inferiority study |
| T1 | A policy-improvement bound has stated coverage | Unproved target | Assumptions, proof, adaptive-selection analysis |
| D1 | Sales replay establishes actual retailer cost improvement | Unsupported | Must not claim |
| I1 | Repository checks and runner work locally | Infrastructure only | SESSION_LOG and setup validation summary |
| E1 | First 192 M5 development tasks completed and saved outputs match M1 and an independent calendar oracle | Verified engineering result, development only; corrected after independent review | `results/summaries/M4_BASELINE_RESULTS_AUDIT.md`, source-integrity/error regressions and `docs/M4B_CODEX_REVIEW_RESPONSE_20261019.md`; not a significance proof |
| E2 | GP one-step rollout gives 4.11% lower pooled diagnostic simulated cost than the identical-GP base-stock comparator at the examined origin | Verified descriptive exploratory result only; no general-population inference | 12 dependent item-store histories, 48 matched budget tasks, 5.92× simulated-transition cost, and cost decomposition in the M4b audit |
| I2 | Proposed later development/calibration/validation/final geometry prevents all future information leakage | Global guarantee unproved; supported preparation boundaries implemented and synthetically tested in M4c | M4c protocol/firewall; owner freeze and future runner integration remain required |
| I3 | M4c supported preparation APIs reject specified future-history, stage-release, ledger, cohort and symlink violations before observation callbacks | Synthetic engineering evidence; no OS isolation or scientific coverage guarantee | `tests/test_m4c_firewall.py`, `tests/test_m4c_source_integration.py`, `tests/test_m4c_cli.py`; `results/summaries/M4C_VERIFICATION_20261020.md` |
| P1 | M4c chronology/estimands/power proposals constitute a frozen publication design | False; pending owner approval and missing scientific inputs | `experiments/protocol/M4C_SCIENTIFIC_PROTOCOL.md`; no approved real release |
| I4 | Direct production adapter reads require exact per-call authorization and persisted selection/calibration prerequisites where applicable | Synthetic engineering evidence after PR #11 follow-up; fixes the earlier direct-adapter bypass | `tests/test_m4c_access_evidence.py`, `results/summaries/M4C_FIREWALL_FOLLOWUP_20261020.md` |
| I5 | Hash-verified selection/access records prove executed validation, honest chronology or scientifically valid selection | False; verified persisted bytes and declared coverage are separate from owner attestation and scientific/execution validity | `docs/M4C_ACCESS_FIREWALL.md`; actual execution/model dependency checks remain mandatory M4d gates |

A running program is not proof of a hypothesis. Imported references are not a new novelty audit. Record null results, failures and protocol deviations.
