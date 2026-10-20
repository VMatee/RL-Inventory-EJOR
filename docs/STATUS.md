# Current status

Updated: 2026-10-20 (Asia/Bangkok). See Git history and SESSION_LOG for validation.

## PR #12 corrections awaiting independent re-review

The independent review of `ff05c5b` requested changes despite 233 passing
tests. The follow-up corrects B1 and C1–C4: strict shared artifact/evidence
validation, exact integer reference fitting, correct terminal outstanding
batches, an independent numerical replay and atomic, synchronized private
publication. The expanded suite passes **255/255**, including **37 M4d-0
tests**; original protected SHA256/size checks remain **1,611/1,611 unchanged**.
See `docs/M4D0_CODEX_REVIEW_RESPONSE_20261020.md` for counterexamples,
commands and remaining limits. PR #12 remains open for independent review;
no merge, real M5 access, M4d-1 execution or scientific freeze is authorized.

## Research

- Active scope: limited-demand-data, GP-informed, decision-sensitive inventory policy learning. The research direction has not changed.
- Introduction: the initial Word import has been substantively revised in canonical LaTeX at the user's request. It now sharpens the operational question, defines the policy-cost difference, and distinguishes the intended inventory-specific contribution from existing GP, Bayesian-risk and baseline-regret principles.
- Contributions and evaluations remain proposed: no new theory or numerical findings are asserted.
- Other manuscript sections remain excluded placeholders.
- M1 deterministic inventory simulator is implemented and locally tested (pure transition plus Gymnasium wrapper, hand-computed reference trajectory and independent calendar cross-check). The owner explicitly accepted its current conventions **for M2 engineering** on 2026-10-17. Final publication assumptions remain open. M1 source/tests/fixtures are unchanged by M2.
- M3 acquisition: **all five M5 CSVs are present locally**, matching the Zenodo MD5/size metadata (450,472,284 bytes total); schema and row counts were checked. Public provenance and SHA256 are recorded in `data/manifests/m5_verified_20261017.json`. **Favorita is not acquired:** user Kaggle account, accepted rules and credentials are required. See `data/DATASET_PLAN.md` and the M3 acquisition report.
- M2 was reviewed and merged into local/GitHub `main` at `14d0741ea2328aa28cef7612976357c4b3cb6d53`, as stated by the owner and independently checked on 2026-10-18. Earlier M2 reports remain historical evidence. M1/M2 mechanics are unchanged; the baseline before M3 passed all 66 existing tests.
- M3 ingestion, chronological contracts, information accounting, independent leakage traps and bounded local preparation were independently reviewed and merged through PR #8 at `9151cec`. M3 scientific protocol/holdout acceptance remains pending. See `data/M3_PIPELINE.md`, `experiments/protocol/EVALUATION.md` and `results/summaries/M3_IMPLEMENTATION_REVIEW_20261018.md`. No final holdout is frozen and no GP/RL training or empirical inventory-cost experiment has run.
- M3 independent-review correction: full-source SHA256 is now confined to trusted provenance; learner artifacts use a predeclared logical dataset version. A single withheld d_226 mutation leaves every learner byte unchanged. Study-wide historical access is explicitly 1,204 distinct cells (1,120 selected histories plus 84 additional screening cells). All 119 tests pass (53 M3; six dedicated noninterference/accounting tests); scoped Ruff/format checks pass. Repository-wide checks retain 54 lint findings and 13 formatting failures in unchanged files. The appended correction section of the M3 report and `results/summaries/m3_correction_verification_20261018.json` record current evidence. Independent engineering re-review and merge are complete; scientific protocol approval remains separate.
- References: all 16 citation keys resolve. Scoped primary-source claim checks are documented in research/literature/REFERENCE_AUDIT.md; a complete bibliography/theorem/novelty audit remains outstanding.

## Infrastructure

- Canonical scientific/Git rules remain in this repository's `AGENTS.md`; no lowercase `agent.md` alias is used. The sibling `code/AGENTS.md` is a startup adapter directing Codex to those rules. `code/README.md`, `CODEX_PROMPT.md` and `start_codex.sh` provide the requested local entry workflow; tracked templates and a hash-guarded installer are included.
- `docs/CODEX_IMPLEMENTATION_PLAN.md` defines M2-M7 deliverables and validation gates. The subsequent M2 session explicitly invoked the saved prompt and approved M1 engineering conventions; the saved file alone was not authorization. M2 implementation does not authorize later milestones/training. Launcher path/flag checks passed against CLI 0.163.0; login/model access through that launcher and end-to-end sandbox execution remain untested.
The Git checkout now resides under the workspace's `github/` child, while the existing Serena project configuration stays in the parent `.serena/`. All scientific source and manuscript remain Git-tracked under `github/`. The active Python 3.10.12 virtual environment is isolated in sibling `code/.venv`; the old `code/legacy-venv-pre-migration` folder was deleted at the owner's explicit request after checking no processes used it. Project-specific Python dependencies are installed with a pinned snapshot in `environment/requirements-lock.txt`, including CUDA-enabled PyTorch 2.9.1, GPyTorch, BoTorch and Stable-Baselines3. All four RTX 3090 GPUs passed allocation/compute checks, and a small BoTorch/GPyTorch posterior evaluated on GPU 0. Codex authentication/model access remains untested. No system drivers, OS packages, TeX, raw datasets or long scientific training were installed/launched.

GitHub remains the canonical reviewed record; synchronization is explicit and refuses dirty/divergent local trees. Only one writer may use a checkout. The manuscript revision was published to a task branch through the GitHub connector and validated on the PC in an isolated temporary worktree without changing local main.

## Completed validation

Initial infrastructure validation is recorded in results/summaries/SETUP_VALIDATION.md.

For manuscript source commit 17e9304c67d6993a0631fed2d8b5be872730708a: static checks and six infrastructure unit tests passed on the PC. SHA256 hashes of the Introduction, bibliography and main.tex matched the source compiled in the ChatGPT temporary environment. That build produced seven pages with no final citation/LaTeX warnings; all pages were visually reviewed. This is not a local-PC TeX build or scientific validation. Details: results/summaries/INTRODUCTION_REVISION_20261017.md.

## Current M4b results-audit milestone (2026-10-19)

M4a infrastructure and its first real **M5 development** run are completed. GitHub/local main at original execution source `5d01105671b8033d7bc8aefa0daedeb1ab99b0be` launched 192/192 jobs using four isolated GPUs and two CPU lanes. Session `results/runs/m4-approved-yc4xtrp1/` reports `completed`, `aggregate_summary.json` reports `complete_and_hash_verified`, and the old one-shot `STARTED.json` remains. **Do not rerun the original campaign** or overwrite its ignored artifacts. It consists of 12 series, histories 28/56/112/224, origin d_225, seed 0 and the four initial non-RL baselines.

M4b now contributes read-only `scripts/analyze_m4_results.py`, strict source/output/learner/checksum verification, independent replay of 5,376 M1 transitions, per-series/cluster-aware exploratory paired comparisons and GP model/compute ablation accounting. Aggregated evidence: `results/summaries/M4_BASELINE_RESULTS_AUDIT.md`; local private machine outputs: `results/analysis/m4b-original-20261019/` (Git-ignored). GP one-step rollout has 4.11% lower *descriptive pooled development cost* than matched GP base-stock but uses 5.92× simulation transitions; these numbers are not publication, significance, GP superiority or true retailer saving claims. The first two high-volume series account for 79.17% of observed evaluation requests; 48 budget comparisons are not 48 independent series.

## Next task

Independent **Codex GPT-6.1 Ultra** review of PR #10 was supplied on 2026-10-19 and requested changes: evaluator-input binding, full ledger/compute validation, job-specific wrapper binding, independent-calendar/terminal checks, symlink preflight, and a feasible nonadaptive final-history embargo. The follow-up implementation and tests address these findings. See `docs/M4B_CODEX_REVIEW_RESPONSE_20261019.md`. **Independent Codex re-review at `eef0fd4` APPROVED the scoped M4b software audit**, reporting no remaining BLOCKING or MAJOR defects, after repeating original corruption tests and confirming immutable development results. Three MINOR follow-ups were implemented and author-tested: zero-cost-safe relative summaries, explicit validation-before-calibration *access* order with calibration outcomes sealed, and end-to-end synthetic symlink regressions for all 12 input types. This scoped software acceptance does not approve future final-test preparation or EJOR novelty. The other account's limited ChatGPT Web Pro quota remains unused. The future M4c calendar windows and primary estimand are still proposed, not frozen; no later M5 outcomes or GPUs have been accessed by this analysis task. M4d stronger crossed baselines, M5/Favorita final evaluation and novelty claims remain open.

## Later publication work (not a blocker for this initial pilot)

Interpret development results and failures, design the inventory-sensitive contribution, add stronger published learning baselines, address sales censoring and cohort/terminal/cost sensitivity, freeze the final test/information/compute protocol and statistical design, verify data-use terms, acquire original Favorita through authorized access, and complete the literature/claim/proof audit. Passing software tests does not establish EJOR novelty or empirical superiority.

## M4c merged as PR #11 / M4d-0 implementation (2026-10-20)

PR [#11](https://github.com/VMatee/RL-Inventory-EJOR/pull/11) merged on
2026-10-20 at `4d21c19371f0abaf089f194be685a21026c00999`.
The local `main` has that merge. M4c remains limited trusted-owner
infrastructure and does not authorize reserved outcomes or M4d experiments.

M4b was merged as PR #10 at `bea7dcb5ad82c457e81f75b6965179d725acae45`.
The M4c feature branch implements metadata-only planning, complete phase/history
embargo checks, staged learner/scorer preparation, hash-bound owner releases,
selection-before-calibration and calibration-before-final prerequisites, and
live code/specification/source checks. It also closes legacy development-label,
task-metadata and manifest-symlink bypasses before protected reads. Historical
M3 synthetic behavior and the original d_225 audit remain supported.

See `experiments/protocol/M4C_SCIENTIFIC_PROTOCOL.md`,
`docs/M4C_ACCESS_FIREWALL.md` and `experiments/protocol/M4D_READINESS.md`.
Chronology A is a candidate, with B/C alternatives; no scientific freeze or
positive real release exists. All new M5 values and M4d execution remain closed.
PR #11 received independent approval within trusted-owner scope and was
merged. The next scoped task is M4d-0 synthetic-only execution infrastructure,
not M4d-1 real data or owner scientific freeze. Verification and
preserved-artifact evidence are in `results/summaries/M4C_VERIFICATION_20261020.md`.

### PR #11 critical follow-up

The independent review found a real direct-adapter authorization bypass and
hash-only selection evidence. Reproduced both on synthetic fixtures at `4d9a777`.
Adapters now authorize each exact read and persist receipts; calibration/final
also require actual typed specification/result files and complete prerequisite
access coverage. Legacy workers reject explicit protected phases. This verifies
declared persisted evidence, not executed or scientifically valid selection.
M4d executor/model dependency checks remain mandatory future gates. Chronology,
estimand, cohort and inference choices remain PENDING OWNER APPROVAL. Follow-up
commands, limitations and preservation evidence:
`results/summaries/M4C_FIREWALL_FOLLOWUP_20261020.md`.
