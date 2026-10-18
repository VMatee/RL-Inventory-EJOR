# Current status

Updated: 2026-10-18. See Git history and SESSION_LOG for actual validation.

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

## Current preparation-only milestone

M3 was merged through PR #8 at `9151cece320f0d0563720e7c48790f72862d5211`. Its earlier pre-merge notes above are historical; M3 engineering acceptance is complete, while final scientific protocol/holdout decisions remain open.

The owner now authorizes **M4a DATA/CODE PREPARATION ONLY**, explicitly requiring review before any baseline runs. A 32-candidate development preparation retained 12 series and created 48 schema-2 learner views; `data/processed/m3-demo-9vex_g9j` is the new local bundle. M5 source hashes remain verified; Favorita is still blocked by missing Kaggle authorization and is not substituted. The study-wide historical union for this new bundle is 3,248 cells (not the earlier five-series bundle's 1,204).

Initial baseline source, a nonexecuting plan builder, GPU/CPU scheduler and approval gates are staged on `feat/m4-baselines-prepare-only`. Scope: empirical base-stock, Gamma-Poisson base-stock, transformed-Gaussian GP base-stock and GP one-step rollout. These are not DCL/TED/HDPO implementations or the proposed contribution. Proposed execution is four independent single-GPU lanes plus two CPU lanes. **No new baseline has been fitted, numerically validated or scored; no GPU baseline computation or training has been launched.** See `docs/M4_BASELINE_PREPARATION.md`.

## Next task

Owner inspects the M4a code, data bundle and plan; separately authorize synthetic numerical checks before any baseline run. The default run command is dry-run only and all approval-template flags remain false. Do not treat successful preparation tests as numerical validation. Final experiment dates, scenarios, cohort, information/compute comparison rules and public-data limitations still need scientific review.

## Research blockers

Owner review of M3 and eventual publication boundary assumptions, remaining baseline-specific implementations, **Favorita authorized Kaggle acquisition and raw-data usage terms**, M3 time-series preprocessing/eligibility and frozen splits, complete reference/novelty audit, and frozen information/compute protocol. The full current EJOR author guide was not accessible during the revision; final submission requirements must be checked before submission.
