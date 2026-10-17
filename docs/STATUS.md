# Current status

Updated: 2026-10-17. See Git history and SESSION_LOG for actual validation.

## Research

- Active scope: limited-demand-data, GP-informed, decision-sensitive inventory policy learning. The research direction has not changed.
- Introduction: the initial Word import has been substantively revised in canonical LaTeX at the user's request. It now sharpens the operational question, defines the policy-cost difference, and distinguishes the intended inventory-specific contribution from existing GP, Bayesian-risk and baseline-regret principles.
- Contributions and evaluations remain proposed: no new theory or numerical findings are asserted.
- Other manuscript sections remain excluded placeholders.
- Inventory simulator, DP, GP/RL and datasets have not been implemented/validated by this manuscript task.
- References: all 16 citation keys resolve. Scoped primary-source claim checks are documented in research/literature/REFERENCE_AUDIT.md; a complete bibliography/theorem/novelty audit remains outstanding.

## Infrastructure

- Agent instructions are now maintained solely in `AGENTS.md`; the redundant lowercase `agent.md` pointer was removed. Research scope is unchanged.
The Git checkout now resides under the workspace's `github/` child, while the existing Serena project configuration stays in the parent `.serena/`. All scientific source and manuscript remain Git-tracked under `github/`. The active Python 3.10.12 virtual environment is isolated in sibling `code/.venv`; the initial minimal venv is preserved as an inactive backup in `code/legacy-venv-pre-migration`. Project-specific Python dependencies are installed with a pinned snapshot in `environment/requirements-lock.txt`, including CUDA-enabled PyTorch 2.9.1, GPyTorch, BoTorch and Stable-Baselines3. All four RTX 3090 GPUs passed allocation/compute checks, and a small BoTorch/GPyTorch posterior evaluated on GPU 0. Codex authentication/model access remains untested. No system drivers, OS packages, TeX, raw datasets or long scientific training were installed/launched.

GitHub remains the canonical reviewed record; synchronization is explicit and refuses dirty/divergent local trees. Only one writer may use a checkout. The manuscript revision was published to a task branch through the GitHub connector and validated on the PC in an isolated temporary worktree without changing local main.

## Completed validation

Initial infrastructure validation is recorded in results/summaries/SETUP_VALIDATION.md.

For manuscript source commit 17e9304c67d6993a0631fed2d8b5be872730708a: static checks and six infrastructure unit tests passed on the PC. SHA256 hashes of the Introduction, bibliography and main.tex matched the source compiled in the ChatGPT temporary environment. That build produced seven pages with no final citation/LaTeX warnings; all pages were visually reviewed. This is not a local-PC TeX build or scientific validation. Details: results/summaries/INTRODUCTION_REVISION_20261017.md.

## Next task

M1: finalize arrival/order/demand timing, initial stock/pipeline, terminal treatment and action bounds in theory/INVENTORY_MODEL.md; implement the minimal inventory environment and deterministic tests. Do not begin GP/RL training or reopen the research direction as part of this manuscript revision.

## Research blockers

Model conventions, exact reference implementation, baseline-specific implementations/dependencies, approved dataset provenance, complete reference/novelty audit, and a frozen information/compute protocol. The full current EJOR author guide was not accessible during the revision; final submission requirements must be checked before submission.
