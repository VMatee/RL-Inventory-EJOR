# Codex code/ workspace setup - 2026-10-17

## Task and starting state

The owner requested README/agent instructions in the local code/ directory and a prompt to build all research code/experiments over the project. Starting repository revision: 758d439d31ddadadd9e4ebeb6b22bca0bf0df4c7; clean main; existing 39 tests passed. M1 was implemented, M2 not implemented, M5 raw files present, Favorita still reported no archive/credentials. These observations are dated; future sessions must inspect actual state.

## Changes

- Git-tracked templates under infrastructure/codex_workspace/ for README.md, AGENTS.md, CODEX_PROMPT.md and start_codex.sh.
- Managed copies installed under the sibling local code/ directory. No lowercase agent.md alias. Local AGENTS is an adapter to the canonical github/AGENTS.md, not another scientific rulebook.
- scripts/install_codex_workspace.py preflights targets, checks hashes, preserves unknown/local edits, refuses symlinks/ambiguous aliases, and writes only four entry files plus its local state record. Its --check mode is read-only.
- docs/CODEX_IMPLEMENTATION_PLAN.md translates the existing M2-M7 roadmap into coding deliverables, independent tests, data/compute contracts, methodology gates and handoffs. Proposed module layout is an engineering plan, not evidence of implementation.
- Canonical README/AGENTS and workflow/status/task records link the new entry point.

## Validation actually performed

- Existing baseline suite before edits: 39 tests passed.
- Seven additional installer tests passed: first/idempotent install; check-only creates nothing; updating known managed bytes; unknown/local edits preserved; preflight blocks all changes; symlinks/aliases rejected; unrelated environment/results untouched.
- Full local pytest suite after adding installer tests: **46 passed, 34 subtests passed**.
- Ruff checks for the new installer and tests: passed after fixing import order.
- Launcher Bash syntax check: passed.
- Actual local installer --check, install, --check: four files created then no drift.
- Actual local start_codex.sh --check: matched intended code/ cwd and github/ extra writable directory; installed Codex CLI 0.163.0 supports the four required flags.

The launcher uses workspace-write with on-request approvals, not full access. Flags are also documented in official Codex guidance checked during this task:
- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/cli/reference

The additional writable root is the sibling github/ repository, not the user's whole home directory. Permission scoping does not by itself protect ignored data inside that writable tree; instructions prohibit deletion/overwrite and separate backups remain necessary.

## Explicit limits

No interactive Codex/model session, login/quota verification, model selection, full sandbox test, global Codex configuration change, package installation, M2 solver implementation, dataset download, GP/RL training, or experiment sweep occurred. Source and data symlinks, raw datasets, existing result files and code/.venv were not moved or replaced. Test output is installation evidence, not a scientific result.

The saved first-task prompt contains scoped acceptance of the current M1 convention for M2 engineering. It is a proposed user message, not an approval already received; it only authorizes work when actually sent. The complete implementation plan is context, not permission to run every stage without review.

## Re-run and handoff

From workspace/code:

```bash
.venv/bin/python ../github/scripts/install_codex_workspace.py --check
bash start_codex.sh --check
# Interactive command for the owner's terminal only:
bash start_codex.sh
```

Read CODEX_PROMPT.md before sending its body to Codex. It authorizes M2 only, keeps scientific claims provisional, preserves the existing M1 fixture and data, and ends with a tested reviewable diff. Later milestones need their own bounded user tasks. Review branch/commit and final local/remote synchronization at the handoff; this report does not imply a model session has run.
