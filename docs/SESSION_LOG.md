# Session handoff log

## 2026-10-17 - M3 source acquisition audit (incomplete: Favorita auth required)

At the user's request, confirmed the frozen study plan calls for TWO public retail-sales sources (M5 Walmart and original 2017 item-level Corporación Favorita) plus a synthetic experiment track that is generated rather than downloaded. M3 acquisition started ahead of M2; no scientific split or training was changed.

Downloaded all five M5 CSVs to Git-ignored `data/raw/m5/`, totaling 450,472,284 bytes. Two small CSVs came from organizer Zenodo record 10203108; larger CSVs used a pinned Hugging Face mirror with concurrent byte-range downloads. **All five were verified byte-for-byte with exact Zenodo file lengths and MD5**, with SHA256, schema and row-count metadata recorded in tracked `data/manifests/m5_verified_20261017.json`. A time-limited incomplete Zenodo part was deleted only after its complete counterpart passed verification. Confirmed raw sales, not uncensored demand; no leakage-prone preprocessing or data-driven item selection was performed.

Installed Kaggle CLI 1.7.4 (Python3.10-compatible) and py7zr 1.1.2 in isolated `code/.venv`; added a guarded Favorita official-competition download/ZIP verification tool. Original Kaggle competition data are gated by accepted rules and credentials. No Kaggle credential was present on the PC, so **Favorita was not downloaded**, and no unauthorized third-party substitute was used. Details and next user action: `data/sources/FAVORITA.md`, `results/summaries/M3_DATA_ACQUISITION_20261017.md`.

M1 timing approval and M2 DP remain the next method milestones. M3 preprocessing/split protocol and the Favorita external holdout remain pending. No RL/GP experiment or publication result is claimed.

## 2026-10-17 - M1 model specification and deterministic inventory simulator

At the owner's request, verified that no running process used the obsolete local `code/legacy-venv-pre-migration` environment, validated the active `code/.venv` and then deleted only the obsolete environment directory. Git checkout and current venv remain intact. Historic setup logs are retained as point-in-time records.

Selected/documented M1 **engineering conventions** in `theory/INVENTORY_MODEL.md`: after-arrival decision epoch, known lead time `L>=1`, current order first available in period `t+L`, sales=min(stock,demand), no backlogs, end-stock holding/shortage/order costs, and zero *additional* terminal value/cost. Added pure stock-flow transition, Gymnasium wrapper, independent hand fixture, tests, and explicit no-lookahead/terminal semantics. Conventions are **pending owner review before M2**; no GP/RL model, data ingestion, proof or real-world outcome is claimed.

Validation and remaining limitations: `results/summaries/M1_SIMULATOR_VALIDATION_20261017.md`. Next scientific task only after owner review: M2 exact finite-state DP and tuned base-stock reference.

## 2026-10-17 - Parent workspace, Git child and isolated ML environment

At the user's request, migrated the entire clean Git checkout (including `.git`, version history, manuscript and code) into `<workspace>/github/`; kept the connected Serena `.serena/` at the parent. Created `<workspace>/code/.venv` and local source symlinks to the tracked `github/src`, `github/tests`, and `github/experiments`. The original lightweight environment was preserved, not removed, as `code/legacy-venv-pre-migration`. No second Git repository or fork of the Python code was created.

Installed official PyTorch CUDA 13.0 wheels and compatible GP/RL scientific/development dependencies in the new Python 3.10.12 venv. All four RTX 3090 GPUs passed small tensor computations; a GPyTorch/BoTorch posterior worked on GPU 0. Pip dependency integrity and all environment imports passed. Captured actual package versions in `environment/requirements-lock.txt`. The initial bounded PyTorch installation timed out after downloading wheels; a second installation resumed from cached wheels and completed successfully. See `results/summaries/LOCAL_WORKSPACE_SETUP_20261017.md` for exact checks and limitations.

No DynaPlex baseline replication, dataset download, TeX installation, long GPU training, or scientific inference occurred. Next research task remains M1 (formal model and simulator), unchanged.

## 2026-10-17 - Agent instruction cleanup

Removed redundant `agent.md` pointer at the user's request. Kept canonical `AGENTS.md`; updated README references and the repository static checker to no longer require the removed file. Research scope and manuscript were not changed. Validation and Git synchronization are recorded with the corresponding commit and checks.

## 2026-10-17 - GitHub-first setup

Starting SHA: 9019a91c305876b0c156a547f4b3ee0c72c96c98. Clean checkout matched origin/main. Created setup/github-first-workflow for scoped maintenance.

Read the existing charter, protocols and scaffold; preserved the limited-data research direction. Added workflow/agent instructions, task/claim records, safe synchronization, static checks and a provenance runner. Importing the supplied Introduction retains its framing; bibliography verification remains a separate task. Malformed LaTeX placeholder escapes are corrected.

Python 3.10.12 and Codex 0.163.0 detected. No Codex task, scientific experiment, dataset download or dependency/system installation performed. Record actual validation in results/summaries/SETUP_VALIDATION.md after it runs.

Next: M1 model conventions and deterministic simulator tests. Scientific dependencies and local TeX remain setup/approval tasks.

Local commit identity was initially unset; configured repository-local name/email from the existing commits. No global identity or authentication was changed. The first commit attempt was blocked before writing a commit; no source was discarded.

Validation completed on ebdfca7162eb28f7b0167c08bd59f3994816ea4d: six unit tests, 16 citation keys, runner success/failure/timeout and non-main sync guard passed. Matching manuscript sources compiled to seven reviewed pages in the ChatGPT temporary environment only. Evidence: results/summaries/SETUP_VALIDATION.md. Next: publish reviewed maintenance to main and confirm local/remote synchronization.

## 2026-10-17 - Introduction revision for EJOR positioning

Starting main SHA: 89933c8eff05417e9396bc0ce71fb253966d34e4. The user requested a stronger Introduction in GitHub and synchronization to the PC using SeneraAiServer. Read live AGENTS, charter, status, tasks, workflow, manuscript and provenance; retained the established limited-real-demand-data inventory scope.

Created GitHub branch docs/introduction-ejor-revision-20261017 with manuscript source commit 17e9304c67d6993a0631fed2d8b5be872730708a. Changes cover the Introduction, small bibliography corrections, scoped primary-source audit, and manuscript provenance/documentation. No other manuscript section or scientific implementation was added.

The revised Introduction is approximately 1,550 words, with 16 citation keys and an explicit definition of the policy-cost difference. It distinguishes real observations from simulated experience; epistemic uncertainty from demand variability and Monte Carlo error; and an inventory-specific research objective from existing Bayesian and baseline-relative principles. It retains prospective contributions and evaluation language, including the limitations of M5/Favorita sales replay.

Matching source compiled to a seven-page PDF in the ChatGPT temporary environment. A broken BibTeX executable link there was handled using an isolated PATH shim to the existing bibtex.original executable; no PC environment was modified. The final LaTeX log contained no warnings or undefined citations, and all seven pages were visually inspected. No generated PDF or font files were committed.

Fetched the GitHub task branch to the PC. Validated source commit 17e9304c67d6993a0631fed2d8b5be872730708a in a temporary detached worktree: static structure/citation check passed, six infrastructure unit tests passed, git diff --check passed, and three source SHA256 values matched the compiled sources. The temporary worktree was removed normally. Local main stayed clean at the starting SHA during this pre-merge validation.

See results/summaries/INTRODUCTION_REVISION_20261017.md for exact checks and limitations. Final merge and local synchronization are to be evidenced by the GitHub PR/commit and final tool report, not inferred from this pre-merge record. M1 remains the next research task.
