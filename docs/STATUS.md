# Current status

Updated: 2026-10-17. See Git history and SESSION_LOG for actual validation.

## Research

- Active scope: limited-demand-data, GP-informed, decision-sensitive inventory policy learning. The research direction has not changed.
- Introduction: the initial Word import has been substantively revised in canonical LaTeX at the user's request. It now sharpens the operational question, defines the policy-cost difference, and distinguishes the intended inventory-specific contribution from existing GP, Bayesian-risk and baseline-regret principles.
- Contributions and evaluations remain proposed: no new theory or numerical findings are asserted.
- Other manuscript sections remain excluded placeholders.
- M1 deterministic inventory simulator is now implemented and locally tested (pure transition plus Gymnasium wrapper, hand-computed reference trajectory and independent calendar cross-check). The event ordering and terminal conventions are explicit **engineering selections still awaiting scientific/owner review**, not a finished theory result.
- M3 acquisition: **all five M5 CSVs are present locally**, matching the Zenodo MD5/size metadata (450,472,284 bytes total); schema and row counts were checked. Public provenance and SHA256 are recorded in `data/manifests/m5_verified_20261017.json`. **Favorita is not acquired:** user Kaggle account, accepted rules and credentials are required. See `data/DATASET_PLAN.md` and the M3 acquisition report.
- Small-state optimal DP, tuned inventory baselines, GP/RL training, leakage-safe data transformations/frozen train-test splits and empirical findings have **not** been implemented.
- References: all 16 citation keys resolve. Scoped primary-source claim checks are documented in research/literature/REFERENCE_AUDIT.md; a complete bibliography/theorem/novelty audit remains outstanding.

## Infrastructure

- Canonical scientific/Git rules remain in this repository's `AGENTS.md`; no lowercase `agent.md` alias is used. The sibling `code/AGENTS.md` is a startup adapter directing Codex to those rules. `code/README.md`, `CODEX_PROMPT.md` and `start_codex.sh` provide the requested local entry workflow; tracked templates and a hash-guarded installer are included.
- `docs/CODEX_IMPLEMENTATION_PLAN.md` defines M2-M7 deliverables and validation gates. This setup does not implement M2 or start Codex/training. Sending the saved first-task prompt would accept existing M1 conventions for M2 engineering; merely storing it is **not** recorded owner acceptance. Launcher path/flag checks passed against CLI 0.163.0; login/model access and end-to-end sandbox execution remain untested.
The Git checkout now resides under the workspace's `github/` child, while the existing Serena project configuration stays in the parent `.serena/`. All scientific source and manuscript remain Git-tracked under `github/`. The active Python 3.10.12 virtual environment is isolated in sibling `code/.venv`; the old `code/legacy-venv-pre-migration` folder was deleted at the owner's explicit request after checking no processes used it. Project-specific Python dependencies are installed with a pinned snapshot in `environment/requirements-lock.txt`, including CUDA-enabled PyTorch 2.9.1, GPyTorch, BoTorch and Stable-Baselines3. All four RTX 3090 GPUs passed allocation/compute checks, and a small BoTorch/GPyTorch posterior evaluated on GPU 0. Codex authentication/model access remains untested. No system drivers, OS packages, TeX, raw datasets or long scientific training were installed/launched.

GitHub remains the canonical reviewed record; synchronization is explicit and refuses dirty/divergent local trees. Only one writer may use a checkout. The manuscript revision was published to a task branch through the GitHub connector and validated on the PC in an isolated temporary worktree without changing local main.

## Completed validation

Initial infrastructure validation is recorded in results/summaries/SETUP_VALIDATION.md.

For manuscript source commit 17e9304c67d6993a0631fed2d8b5be872730708a: static checks and six infrastructure unit tests passed on the PC. SHA256 hashes of the Introduction, bibliography and main.tex matched the source compiled in the ChatGPT temporary environment. That build produced seven pages with no final citation/LaTeX warnings; all pages were visually reviewed. This is not a local-PC TeX build or scientific validation. Details: results/summaries/INTRODUCTION_REVISION_20261017.md.

## Next task

M1 code, stock-flow timing specification, deterministic hand-calculated fixture and Gymnasium checks are implemented and locally tested; **obtain owner acceptance of the recorded M1 event/terminal conventions** before treating the mathematical formulation as frozen. Thereafter M2: build an independent small finite-support DP and tuned base-stock benchmark. No GP/RL training yet.

## Research blockers

Owner review of selected M1 model conventions, independent M2 exact DP reference, baseline-specific implementations, **Favorita authorized Kaggle acquisition and raw-data usage terms**, M3 time-series preprocessing/eligibility and frozen splits, complete reference/novelty audit, and frozen information/compute protocol. The full current EJOR author guide was not accessible during the revision; final submission requirements must be checked before submission.
