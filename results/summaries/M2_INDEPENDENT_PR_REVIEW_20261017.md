# Independent M2 pull-request review — 2026-10-17

**Status:** ready for a **reviewable PR**, not a journal-result acceptance or permission to merge. Codex's original `feat/m2-exact-reference` checkout remains open, dirty, and **untouched**. To obey one-writer safety, the review copied an explicit 16-file allowlist into an independent `review/m2-exact-reference-pr` Git worktree from `main` at `2cbce59fd0cf0f738e177a0ef7e8bc6347882431`, verifying SHA256 of every copied file. Raw datasets, checkpoints and experiment runs were **not** copied, modified or uploaded.

## Scientific/engineering review conclusions

- The M2 implementation uses **known iid finite-support demand**, exact finite-horizon Bellman expectations to floating-point precision, reachable inventory state/pipeline and the existing unmodified M1 transition. It is an engineering oracle, not a learned or deployable solution under limited unknown demand.
- The `HorizonAwareBaseStockPolicy` applies `q=0` when `remaining <= lead_time`, because under M1 the order arrives at or after T and M1 assigns no further terminal value. This uses only decision-time observables. The ordinary constant-S implementation is retained as a **naive comparator**.
- The original tiny example (L=1, T=3) gives exact DP expected cost **2.875**, replay **2.875**, horizon-aware tuned S=1 **2.875** (gap **0.000**), and naive constant-S tuned S=1 **3.000** (gap **0.125**). The naive gap is fully explained by unnecessary last-period orders; do **not** describe it as an RL/GP improvement or an EJOR contribution.
- Both baselines are tuned on the same declared constant-level grid and share the known demand law and cost model. Neither represents an empirically fair *data-limited* comparator until the M3/M4 information-budget protocol is frozen.
- Independently authored exhaustive contingent-policy enumeration uses past-demand histories and rational arithmetic on tiny fixtures. The production tests cover lead-time timing, cutoff boundary, no-lookahead, fixed and variable costs, terminal treatment, initial pipeline and resource-limit failure.
- The no-salvage, zero-additional-terminal-cost M1 boundary is the **approved engineering** reference; publication-relevant alternate boundary/warm-start conventions are still open. Horizon-aware base-stock is not a generally optimal inventory rule.

## Independent commands executed in a SEPARATE worktree

From `<workspace>/m2-pr-review`, with `<workspace>/code/.venv`:

```bash
PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 timeout 120 ../code/.venv/bin/python -B -m unittest discover -s tests -q
../code/.venv/bin/python -m ruff check --select E,F,I,B,UP src/inventory_ejor/demand src/inventory_ejor/solvers src/inventory_ejor/policies scripts/run_m2_reference.py tests/test_m2_reference.py
../code/.venv/bin/python -m ruff format --check src/inventory_ejor/demand src/inventory_ejor/solvers src/inventory_ejor/policies scripts/run_m2_reference.py tests/test_m2_reference.py
PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 timeout 25 ../code/.venv/bin/python -B scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
git diff --check
```

**Results verified before PR creation:** 66/66 unittests passed; Ruff lint passed; seven files passed Ruff formatting; static repository check passed; DP and both baseline results match Codex's corrected report. Extra read-only synthetic property cross-check covered **36** configurations across lead time L=1,2,3, mixed horizon, order bounds, costs, initial pipeline and binary demand, comparing DP with independently evaluated DP-policy and both baseline policies. All 36 passed. These properties complement, but do not replace, the independent rational tiny-case oracle.

The existing manual `.github/workflows/checks.yml` was checked at byte level: its shell line continuation has **one** backslash and was already valid. The review **only extends its manual job** to run M2's existing tests, deterministic demo and Ruff lint; no new pull-request trigger, cloud action, dataset download or GPU job was launched. CI is not claimed to have passed remotely.

## Boundaries and handoff

- Only reviewed source, small reference fixtures/config, tests, documentation and manual CI source enter this PR. No raw M5/Favorita datasets, numerical training outputs, GPU checkpoints, passwords or unreviewed artifacts.
- GitHub main must remain unchanged until human PR review/merge. The original Codex branch still has uncommitted duplicate M2 changes; **do not run sync, reset, clean or branch switch there**. After closing both Codex sessions, reconcile it against the merged PR safely and explicitly before syncing main. The separate review worktree can be removed once pushed and clean.
- Next scientific step after accepting M2: finalize M3 temporal data governance and constrained information budgets before training. Favorita remains authorization-gated. Zero observed cost gap on a toy model does not indicate that a proposed method succeeds or fails in general.
