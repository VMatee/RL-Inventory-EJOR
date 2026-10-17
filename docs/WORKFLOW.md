# GitHub-first research workflow

The checkout is in `<workspace>/github`, while the isolated Python virtual environment is `<workspace>/code/.venv`; Serena stays activated on the outer workspace with `.serena/`. All commands below assume the Git child directory. Do not move scientific source out of the tracked repository.

GitHub main is the reviewed project record. The PC executes experiments. ChatGPT web supports research/planning/review; SeneraAiServer bridges the chat to this checkout; local Codex is an optional implementation assistant. None automatically synchronizes or validates the others.

## Normal cycle

1. Read README, AGENTS, STATUS and the next task through the GitHub connector at the actual latest revision. For local work call SeneraAiServer initial_instructions and verify the active project/path.
2. Agree on one task and acceptance criteria. Document research decisions in DECISION_LOG.
3. Inspect Git state. Synchronize clean, idle main and create a task branch. Preserve dirty work; never reset/clean/stash it automatically.
4. Assign ONE writer: Serena or Codex. Web/GitHub edits also require fetching the updated branch before local edits.
5. Test, inspect diff and commit named files. Push the task branch; review a PR before merging. Direct main maintenance needs explicit authorization.
6. Pull merged main on the PC only when clean and idle. Run short validation. Execute research from a dedicated clean fixed-commit worktree/clone.
7. Return small reviewed summaries with provenance to GitHub, not raw data/checkpoints. Update STATUS and SESSION_LOG.

```bash
cd "/home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR/github"
bash scripts/sync_main.sh
git switch -c feat/m1-inventory-env
../code/.venv/bin/python scripts/check_project.py
../code/.venv/bin/python -m unittest discover -s tests -v
git diff --check
git diff
# Stage named reviewed files, commit, and push the task branch for review.
```

A divergent branch is a reconciliation task, never permission to reset. Do not switch/pull/edit a checkout while a job uses its code. Parallel agents require different worktrees/clones and output directories, not merely different branch names.

## Manuscript cycle

Canonical source: manuscript/sections/*.tex and references.bib. Draft/critique one section with verified references; commit on a docs branch. Compile and inspect a PDF. Word/PDF exports are review copies; incorporate accepted edits back into LaTeX. The supplied Introduction is archived with a source checksum. Importing it does not independently verify its bibliography or establish its proposed results. Other sections remain placeholders.

## Local Codex

Observed at setup: codex-cli 0.163.0. Login, quota, model selection and execution of a Codex task were NOT verified. Existing authentication must never be printed or copied. Check installed help before using flags.

Preferred entry is the sibling `code/` directory requested by the owner. Its `AGENTS.md` adapter explicitly reads `../github/AGENTS.md`; the launcher grants sibling repository write access with `--add-dir`, while retaining `workspace-write` and `on-request` approvals. This is not automatic permission to run a full study.

Run interactively in the USER'S terminal, not the Serena shell tool:

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/code"
# Stop other writers and jobs using the checkout first.
bash start_codex.sh --check
bash start_codex.sh
```

Then review/send the body of `CODEX_PROMPT.md` for M2. That prompt explicitly accepts the existing M1 conventions as the engineering reference for M2; its presence on disk does not record user acceptance. The full task chain and acceptance checks are in `../github/docs/CODEX_IMPLEMENTATION_PLAN.md`. The first session ends after M2 review; further milestones and expensive experiments need scoped authorization.

The local entry files are managed copies of Git-tracked templates. After a clean, idle main sync, refresh them from github/ with `../code/.venv/bin/python scripts/install_codex_workspace.py`. The installer stops on unknown/local edits; reconcile those rather than overwriting. Direct `codex` use from github/ remains possible, but do not start a second writer.

Retain approval prompts using the options supported by the installed version. Never use approval/sandbox bypass flags. Do not hard-code legacy approval flags without checking installed help. ChatGPT plugin installation does not automatically configure Codex's own MCP servers; sharing this Git checkout is sufficient for the proposed workflow.

Task prompt:

> Read AGENTS.md, docs/STATUS.md, docs/TASKS.md, theory/INVENTORY_MODEL.md and the evaluation protocol. M1 deterministic inventory transitions have been implemented and tested; **first review the selected event-timing and terminal conventions with the owner before M2 work**. Once that scope is approved, implement only the accepted next task in a new branch, never silently change timing or terminal treatment. No GP/RL training, data downloads, dependency upgrades or pushes without separate approval. Run checks and report the exact diff, test results and remaining blockers.

## Long jobs

The user starts approved long experiments in a terminal, optionally tmux, from a fixed-commit execution worktree. Confirm resource budget, command, dataset rights and stopping criteria first. Serena can inspect bounded log tails/status later, but its shell tool must not launch interactive or long-running processes. ChatGPT does not keep working after the current interaction or promise unattended monitoring.

A tool timeout is not proof a process stopped; verify its recorded PID/status before rerunning. Avoid duplicate expensive runs. See docs/EXPERIMENT_RUNBOOK.md.

## Reusable ChatGPT prompts

**Resume:** Use GitHub VMatee/RL-Inventory-EJOR as the project record. Read AGENTS.md, STATUS and TASKS at latest main. State the verified stage, blockers and next task. Do not reopen the research direction without evidence.

**Sync/check:** Use SeneraAiServer, read initial instructions, verify the active project and local Git state. If clean and idle, fetch/fast-forward main without discarding work, run documented short checks and smoke test, report local/remote SHAs and manifest. No training.

**Evidence review:** Read the specified results/summaries file and cited manifest/config/code revision. Separate measured results from hypotheses, check information/compute parity and uncertainty, and recommend one next experiment. Do not infer unreported results.

## Official tool documentation

Checked during setup; consult current pages and installed help before changing commands:

- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/cli/reference
- https://docs.github.com/en/get-started/using-github/github-flow

No cloud research jobs, automatic paid service use or self-hosted GitHub runner are configured. Manual CI may consume the account's GitHub Actions allowance; check billing before using it.
