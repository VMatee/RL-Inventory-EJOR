# M4d-0 independent adversarial review handoff

**Status:** Independent re-review APPROVED the scoped implementation at
`e9698b0896fcb0c55c20bd3c43c6b5648ed1cc62`. Final cost and cleanup changes
are newly author-tested, not covered by that earlier independent approval.
The author recommends the completed scoped PR for merge after the checks in
the updated verification report. No merge is performed automatically.
This is synthetic-only CPU reference infrastructure, not permission for M5,
Kaggle/Favorita, protected phases, real baselines or GP/RL execution.

## Final two-issue repeat checklist

Review the current head against `e9698b0`; see the final-hardening section of
`docs/M4D0_CODEX_REVIEW_RESPONSE_20261020.md` and
`tests/test_m4d0_final_hardening.py`.

1. Complete a valid synthetic lifecycle with total 5,000,000,000,000,000,
   verify it, change only saved total by +100 and rehash. Audit must reject.
   Also alter a component and recompute total coherently, make balanced
   component changes, or relink a modified period cost. Check one representable
   increment at zero, subnormal, small and very large scales.
2. Preserve valid rounding: the scorer uses chronological component sums,
   `fsum` for total, and left-associated period addition. The valid total need
   not equal `fsum(period_costs)`; do not certify a regrouped period sum instead.
3. Combine file-fsync/write/publication failure with failed temporary unlink.
   The exact primary exception must remain primary; its explicit cleanup
   cause must identify the pending path and original OS cleanup error. Cleanup
   is attempted once. A cleanup-only failure must raise, not return a digest.
4. Verify partial/complete pending files are never accepted as completed
   evidence; repeated failures can leave orphans. Normal retry synchronizes
   valid final bytes and does not silently delete those or another writer's
   pending files. Recovery requires quiescent writers and explicit owner action.
5. Repeat B1/C1–C4 below. Do not infer M4d-1 readiness, actual scientific
   selection execution, raw-byte authenticity, calibration coverage or novelty.

## Ready-to-paste reviewer request

Act as an independent and adversarial research software reviewer for RL-Inventory-EJOR. Read AGENTS.md, experiments/protocol/M4D0_SAFE_EXECUTION.md, experiments/protocol/M4D_READINESS.md, and the entire PR diff. Inspect the actual code:

- src/inventory_ejor/data/m4d0_execution.py
- src/inventory_ejor/data/m4d0_audit.py
- src/inventory_ejor/data/m4d0_store.py
- src/inventory_ejor/data/m4d0_io.py
- scripts/check_m4d0_io.py
- tests/test_m4d0_execution.py
- tests/test_m4d0_review_regressions.py
- tests/test_m4d0_final_hardening.py
- Existing M4c data/views.py, staged.py, staged_source.py, releases.py and evidence.py.

Verify with synthetic fixtures, without modifying repository code:

1. Can learner code, its input manifest or preflight read raw input, evaluator paths, results or targets? Are calendar features predeclared?
2. Can history authorization be swapped for evaluation permission? Check cohort, phase, series, origin, history budget/window, release, receipt, and separate execution approval.
3. Are actual learner bytes, implementation bytes, initial stock/pipeline, lead, costs, cutoff, seed, horizon and terminal convention pinned when consumed? Can a freshly rehashed forged fitted controller or scoring trace bypass the scorer/auditor?
4. Are all artifacts exclusive, mode-0700 private, and rejected if modified/symlinked? What happens if approval or score persistence fails?
5. Does the metadata-only I/O estimator reproduce 1,145,518,701,600 logical bytes (~1.04 TiB) for the prospective 32-series/7-origin/four-budget candidate? Does its explicit byte gate refuse over-budget preparation without reading source data? It is NOT an optimization.
6. Does any text overclaim genuine executed validation/model selection, secure OS isolation, a ready real-M5 executor, real observations, selection-valid inference or EJOR novelty?

## Mandatory repeat of original REQUEST CHANGES counterexamples

The original reviewed commit was `ff05c5b9b6272bb87eba6db7f2cc08cda2950977`.
Review the complete PR and the follow-up diff from that commit, at the actual
current PR head. Read `docs/M4D0_CODEX_REVIEW_RESPONSE_20261020.md`; do not
accept its assertions without checking code and running synthetic attacks.

- **B1:** rehash/relink score records to nonexistent evaluator release/receipt
  hashes, fit records with wrong dependency hashes or failed status, malformed
  approvals (including Boolean/integer aliases), and GP/RL/retail claims.
  The audit must require actual persisted history and outcome releases and
  receipts plus `evidence`, `config`, `freeze`, `catalog` keyword context.
- **C1:** coherently relink a fitted result and approval to a plan with invalid
  Python, runtime versions or dependencies. Executor, scorer and auditor must
  reject it. Also try substituted valid but inconsistent artifacts.
- **C2:** history `n=28,sum=116,L=6` must give target 29, not 30. Repeat at
  n=56/112/224 with proportionate totals. With Q=5,T=8,stock=25,zero pipeline
  and zero requests, first order is 4 and total cost 209.4. Use an independent
  integer/rational calculation, not the production helper to certify itself.
- **C3:** L=3,T=2,initial pipeline `[4,5]`,zero history/requests must end with
  stock 4 and outstanding `[5,0,0]`, not `[0,0]`. Check multiple leads and
  arrivals beyond the horizon; auditor must not call M1 `transition()`.
- **C4:** inject create, partial/zero write, file fsync, hard-link publication
  and directory fsync failures. Patch `inventory_ejor.data.m4d0_store.os`
  (the store moved out of execution.py). No call can succeed after failed
  sync; retrying identical final bytes must sync the file and directory.
  Check cleanup, a post-publication failure, conflict/no-overwrite and modes.
- **Minor:** recheck root mode/Git boundaries at access time; verify the local
  source manifest includes auditor/store/protocol and actual runtime versions;
  forge a low I/O projection while keeping the true declared config/sizes.

Authorization checks establish persisted hash-linked owner attestations, not
actual validation/model-selection execution or authentic raw target bytes.
A fully coherent fabricated synthetic lifecycle is within that documented
trusted-owner limitation. There is no OS sandbox or real-M5 execution gate
release in this milestone. Report remaining limitations separately from
defects within this scoped reference contract.

Produce BLOCKING / MAJOR / MINOR issues, exact source/line references, verified tests, and separate verdicts for (a) scoped PR merge, (b) real M4d-1 execution and (c) EJOR research.

**Strictly read-only:** No edits, commits, pushes, merges, new M5 outcomes, model fitting, GPU jobs, downloaded data, or rerun of the sealed 192-job baseline.

## Worktree reproduction

The author used a separate worktree because another Codex process was running in the project parent:

/home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR/code/worktrees/m4d0-safe-executor

From that directory, set PYTHONPATH=src:tests and run the unittest discovery suite with the sibling code/.venv Python 3.10 environment, and scoped Ruff lint. Do not run start_baselines.py.

The project owner must separately approve future real-data M4d-1 execution and all additional observation releases, even if this PR passes independent code review.
