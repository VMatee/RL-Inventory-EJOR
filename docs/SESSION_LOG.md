# Session handoff log

## 2026-10-17 - Independent M2 PR preparation (separate worktree)

M2 correction was reviewed via an isolated `review/m2-exact-reference-pr` worktree created from clean `main` at `2cbce59` while two Codex interactive sessions remained open. An explicit 16-file source allowlist was copied and each file's SHA256 checked; **the original dirty `feat/m2-exact-reference` checkout and raw M5/results directories were not edited**. The manual repository GitHub Actions job was extended to run deterministic M2 checks alongside M1. A suspected pre-existing line-continuation typo was independently checked at byte level and proved not to be a defect; the original valid shell continuation was preserved.

Independent checks: 66 unit tests, Ruff lint/format, numeric DP/policy/base-stock replay (2.875/2.875/3.000), 36 additional bounded synthetic cross-checks and the repository static check passed. Scientific interpretation remains unchanged: corrected horizon-aware baseline closes the naive 0.125 toy-example gap. Evidence and outstanding boundaries: `results/summaries/M2_INDEPENDENT_PR_REVIEW_20261017.md`. The PR is for human review, **not authorization to merge or begin M3**. Preserve the original Codex worktree until its owner safely reconciles the outstanding uncommitted changes.

## 2026-10-17 - M2 benchmark-fairness correction and Ruff review

The user supplied an independent review identifying that the tiny example's
0.125 gap vanished when base-stock stopped ordering outside the horizon, and
authorized M2 corrections only. Continued on dirty `feat/m2-exact-reference`
at base `2cbce59fd0cf0f738e177a0ef7e8bc6347882431`; preserved all existing work,
old run artifacts, M1 equations/code/tests, and the original demo configuration.

Added `HorizonAwareBaseStockPolicy` with `remaining <= lead_time` cutoff;
retained the original as a clearly labeled naive constant comparator. Tuned
both on the same grid, known demand law, initial state and resource allowance.
The cutoff uses only decision-time information. Revised CLI output names both
variants explicitly. Corrected interpretation: DP and horizon-aware S=1 both
cost **2.875**; naive S=1 costs **3.000**. The entire earlier 0.125 gap was due
to unnecessary final-period placement costs, not a demonstrated DP advantage
over a horizon-aware baseline. No replacement example was selected.

Before correction: 61 tests passed in 0.640 s. After: **66 passed in 0.718 s**.
Independent rational/calendar enumeration agrees for both variants at each
grid level, and hand path costs explain the gap. New tests cover L=3,T=2,
the exact cutoff and last useful order, same-prefix no-lookahead, per-variant
budget enforcement and repeatable default calls. Fixed imports, strict zip,
loop variable binding, and construction of default limits inside functions;
formatted only new M2 Python files. Installed Ruff 0.17.1 reports no diagnostics
under `--select E,F,I,B,UP`; format check passes. Initial narrower selection
reproduced 14 diagnostics, rather than the review's reported 15. No packages
were installed. Static project check and M1 cost-47 fixture still pass.

New smoke evidence: `results/runs/20261017T154421Z-smoke-2ce059a3/`, exit 0;
external elapsed 0.34 s, peak RSS 39,296 KiB. Exact commands, changed files,
independent calculations and final patch artifacts are recorded in
`results/summaries/M2_REFERENCE_VALIDATION_20261017.md`. Historical evidence
below remains a record of the original implementation, with interpretation
superseded by this correction. No commit/push/merge, download, GPU/training,
or M3 work. Stop after corrected M2 review.

## 2026-10-17 - M2 exact reference and known-model base-stock (Codex)

The actual user instruction invoked `CODEX_PROMPT.md`, explicitly approved current
M1 conventions as the **M2 engineering reference only**, and authorized M2 only.
Final publication assumptions remain open. Read local/canonical rules, current
status/charter/tasks/decision log, implementation plan, M1 specification,
evaluation/data protocol and affected source/tests. Confirmed existing venv and
canonical symlinks. Clean main began at `2cbce59fd0cf0f738e177a0ef7e8bc6347882431`;
no experiment or active repository writer was found. Created
`feat/m2-exact-reference`; no pre-existing work was discarded.

Implemented validated known iid finite-support demand, reachable-state exact
finite-horizon DP, forward policy evaluation, and constant capped base-stock
with exact known-model grid tuning. No inventory truncation; explicit state,
work and time failure. Preserved M1 code/tests/fixtures; changed only its
specification's approval-status paragraph. Added strict config/CLI, dirty-source
hashes, bounded synthetic demo, and independent rational/calendar enumeration
of 128 contingent policies for each L=1/L=2 fixture.

Before edits: 46 tests passed. After: 61 passed in 0.550 s, including 15 M2 tests.
Static checks and `git diff --check` passed. M1 fixture remains 47.0. M2 demo:
DP/returned-policy cost 2.875; tuned constant S=1 cost 3.000, gap 0.125. L=1
open-loop sanity minimum is 3.000, strictly worse than the adaptive optimum.
Saved smoke artifact `results/runs/20261017T153021Z-smoke-bdef32de/`: exit 0,
child runtime 0.214406 s, external elapsed 0.37 s, peak RSS 38,888 KiB.

Existing environment, serial tiny CPU computations, process timeouts <=120 s.
No installation/download, real-data access, GPU/training, sweep, commit, push or
merge. Work remains unstaged/uncommitted; evidence identifies the base SHA plus
dirty source hashes. Files, exact commands, outputs, conventions and limitations:
`results/summaries/M2_REFERENCE_VALIDATION_20261017.md`.

Stopped at M2 review. Next: owner review; M3 leakage-safe information/data
contracts require separate authorization. No later milestone started.

## 2026-10-17 - Codex entry point in code/ and staged implementation plan

At the user's request, inspected the latest clean repository at base 758d439d31ddadadd9e4ebeb6b22bca0bf0df4c7 and the existing code/ workspace/symlinks. Added Git-tracked templates for code/README.md, AGENTS.md (startup adapter only), CODEX_PROMPT.md and start_codex.sh, plus a hash-guarded local installer and seven offline safety tests. The canonical scientific rulebook remains github/AGENTS.md. No second source tree, Git repository, lowercase agent.md alias, dependency environment or dataset copy was created.

Added docs/CODEX_IMPLEMENTATION_PLAN.md with M2-M7 outputs, independent validation requirements and scientific/resource gates. The first-task prompt explicitly accepts current M1 conventions for M2 engineering only when the owner sends it; this setup does not record an approval that has not occurred. No M2 implementation or GP/RL experiment was performed.

Observed Codex CLI 0.163.0 supports --cd, --add-dir, --sandbox and --ask-for-approval. Local entry files were installed, installer idempotence checked, and start_codex.sh --check passed. No interactive Codex session, model invocation, authentication check or full sandbox runtime was launched. Scientific data and code/.venv were left unchanged. Validation record: results/summaries/CODEX_WORKSPACE_SETUP_20261017.md.

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
