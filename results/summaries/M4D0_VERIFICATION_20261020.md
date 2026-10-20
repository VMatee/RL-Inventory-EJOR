# M4d-0 synthetic-only reference execution: verification report

**Date:** 2026-10-20 Asia/Bangkok.
**Scope:** CPU-only synthetic engineering. No real M5/M4d-1 baseline execution,
new outcome release, EJOR result, new research method or scientific freeze.

## Final cost/cleanup hardening after independently approved e9698b0

The independent re-review approved M4d-0 at `e9698b0`. The subsequent two
minor corrections are **newly author-tested**, not attributed to that earlier
approval. Entry feature checkout and remote PR matched that clean head.

- Reproduced rehashed total `5e15+100` being accepted. Shared validation now
  requires the exact saved `total == math.fsum(components)` identity. Independent
  replay checks exact chronological component totals and the defined
  left-associated period arithmetic. Zero/subnormal/noninteger/large finite
  cases pass; representably changed totals/components/periods fail. Legitimate
  differences from regrouping period costs are preserved, not treated as errors.
- Reproduced file-fsync plus unlink failure masking the primary error. Cleanup
  now preserves that primary exception, chains an explicit pending-path/OS
  diagnostic, and attempts owned cleanup once. Rejection is not cleanup:
  failed deletion can leave orphans. Owner recovery requires quiescent writers,
  reviewed pending-file removal and directory synchronization. No auto-pruning.
- Added `tests/test_m4d0_final_hardening.py`: **13 new methods**. Existing B1
  and C1–C4 regression cases remain passing without redesigning those fixes.

| Final check | Result |
|---|---|
| Complete feature-source repository tests | **268/268 passed**, 28.682 s |
| Synthetic-only M4d-0 tests | **50/50 passed**, 12.974 s |
| Strict scoped Ruff E,F,I,B,UP / format | Passed / eight Python files formatted |
| Project structure / Git diff | Passed |
| Original protected SHA256/size and full path set | **1,611 unchanged**, zero new/missing paths |
| New reserved values parsed, real fitting/baselines or GPUs | None |

Separate authoring self-audits accepted 60 fresh synthetic lifecycles/rejected
360 rehashed numerical changes, passed 55 combined storage checks and rejected
36 fresh original-provenance/interaction corruptions. No new
scoped blocking/major defect was found. These are not independent peer review.
Exact commands, code/test references, remaining limitations and the original
snapshot identity are in
[`M4D0_CODEX_REVIEW_RESPONSE_20261020.md`](../../docs/M4D0_CODEX_REVIEW_RESPONSE_20261020.md).

**Author assessment: technically merge-ready, APPROVE TO MERGE within
synthetic-only M4d-0.** PR #12 must remain open/unmerged until the owner acts.
M4d-1 real-data execution and EJOR publication readiness remain **NOT READY**.
No new scientific freeze, selection-valid coverage or novelty is established.

## Historical first-pass and B1/C1–C4 verification

**Superseded first-pass verification below:** the independent adversarial
review of `ff05c5b` found B1/C1–C4 despite 233 passing tests. Those tests did
not establish the claimed complete provenance or numerical correctness.
The correction report is
[`docs/M4D0_CODEX_REVIEW_RESPONSE_20261020.md`](../../docs/M4D0_CODEX_REVIEW_RESPONSE_20261020.md).
It records strict audit context/validation, exact fitting, terminal correction,
independent stock-flow replay, durable publication, **255/255 repository
tests / 37 M4d-0 tests passed**, and **1,611/1,611 original files unchanged**.
At that report stage external re-review remained required; the historical first-pass
description/counts are retained below rather than silently rewritten.

## Implemented

- src/inventory_ejor/data/m4d0_execution.py: separate learner-only plan and
  M4c access receipt, private SHA256-addressed learner file, explicit owner
  synthetic-execution approval with persisted bytes, bounded non-GP/non-RL
  deterministic CPU fit, and a separately released scorer with private trace,
  score evidence, fixed initial state and pinned scenario/source dependencies.
- src/inventory_ejor/data/m4d0_audit.py: read-only reconstruction of the
  reference fitted parameter and every M1 transition from pinned learner and
  scorer-only evaluation targets.
- src/inventory_ejor/data/m4d0_io.py and scripts/check_m4d0_io.py: pure
  metadata I/O projection and explicit admission gate. The current unbatched
  32-series/7-origin/four-budget candidate entails 1,120 per-series reads,
  **1,145,518,701,600 logical processed bytes (~1.04 TiB)**. This is not an
  actual disk throughput benchmark and the heavy I/O has NOT been optimized.
- tests/test_m4d0_execution.py: 15 new synthetic-only adversarial tests.
- experiments/protocol/M4D0_SAFE_EXECUTION.md and
  docs/M4D0_INDEPENDENT_REVIEW_HANDOFF.md: scope, independent review and
  critical unimplemented gates.

## Verification

All implementation and tests were executed in a NEW separate Git worktree,
branch feat/m4d0-safe-executor, because a Codex process was open in the same
project workspace. The main Git checkout was not edited.

| Check | Verified result |
|---|---|
| Complete repository Python suite, feature src on PYTHONPATH | **233/233 passed** |
| New synthetic-only tests | **15/15 passed** |
| Scoped strict Ruff lint E,F,I,B,UP | Passed |
| Project structure and bibliography-key checks | Passed; not a source fact-check |
| Original pre-M4c protected snapshot SHA256+size | **1,611/1,611 unchanged** |
| Original main checkout at inspection | Clean, merged M4c commit 4d21c193 |
| Additional M5, calibration or final values opened | None |
| Original four-GPU baseline session altered/rerun | No |
| GP/RL training or new GPU experiments | None |

## Adversarial test findings

The implementation refuses wrong history/scorer releases, mismatched cohort,
window and history budget, altered code identity, missing or unapproved
execution grants, forged reference controller values, modified/rehashed
scoring traces, symlinked/private artifacts, nonzero-order-after-horizon
violations in M1 replays, and score persistence failures. Zero-demand windows,
undefined fill rates, nonzero initial stock and correctly separated release
calls have synthetic coverage.

Private outputs are created in canonical caller-owned, mode-0700 directories
outside Git worktrees, with content hashes and exclusive file creation.
The scorer validates the same fixed empirical reference against pinned
learner bytes; an independent read-only replayer verifies traces against M1.
These tests do not prove causality, model superiority or code sandboxing.

## Remaining scientific and M4d-1 execution gates

1. Actual validation, model selection and calibration computations are not
   verified by M4c user-issued evidence records; the new CPU-only synthetic
   reference result does NOT replace full method/checkpoint/seed coverage.
2. The real M4d-1 executor, production learner/scorer process isolation,
   exact external dependency hashes, resource monitoring and strict real
   execution approval are NOT implemented.
3. M4c evaluation receipts certify access metadata and are not yet bound
   cryptographically to the exact returned observation bytes. A verified
   scorer-only evaluator artifact and full exposure/attempt log remain needed.
4. Repeated source hashing (~1.04 TiB logical workload) has not been
   optimized: the M4d0 metadata-only gate DETECTS/REJECTS excess, it does not
   provide reviewed safe batching.
5. No cohort/power/estimand/scenario freeze, real M5 outcome access or
   EJOR inventory-specific mathematical novelty is authorized or established.

**Merge gate:** request independent code/research-integrity review of this
synthetic-only PR before merging. Any subsequent real-data execution requires
separate owner approval and new controlled engineering.
