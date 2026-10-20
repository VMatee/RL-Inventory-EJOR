# PR #12 response to independent REQUEST CHANGES

**Date:** 2026-10-20, Asia/Bangkok. **Original reviewed head:**
`ff05c5b9b6272bb87eba6db7f2cc08cda2950977`; merged M4c base:
`4d21c19371f0abaf089f194be685a21026c00999`.
**Status:** independent re-review APPROVED the scoped implementation at
`e9698b0896fcb0c55c20bd3c43c6b5648ed1cc62`. The two final changes below are
newly author-tested, not covered by that earlier approval. PR #12 remains
open and unmerged; the author recommends the completed scoped PR for merge.
No new real M5
observations, training, GPU execution or M4d-1 campaign were authorized or run.

## Final two-issue hardening after e9698b0

Entry checkout/remote/PR head matched `e9698b0` on
`feat/m4d0-safe-executor`, base `4d21c193`, with a clean tree. Root was the
only writer. Changes are confined to three M4d-0 source files, one new
synthetic test module and relevant protocol/verification/handoff documents.
Status/session updates record the actual review stage; original source,
datasets, approvals and run artifacts remain untouched.

### A. Scale-relative cost tolerance

**Reproduced before editing:** a complete synthetic lifecycle with correct
cost 5,000,000,000,000,000 audited successfully after changing only the saved
total to 5,000,000,000,000,100 and recomputing its SHA256. Relative tolerance
allowed a representably different +100 result and no internal component-total
identity was enforced.

**Correction:** `m4d0_execution.py:649` validates finite nonnegative numeric
costs and rejects overflow, then requires exact
`total_cost == math.fsum(cost_components.values())`. The independent audit
at `m4d0_audit.py:141` checks the explicit left-associated M1 period sum and
at `:164` checks the independently reconstructed chronological component
totals exactly. Adjusting a component and total together, balancing components,
or relinking a changed period trace cannot exploit scale-relative tolerance.

Exact comparison is justified here by the **specified producer arithmetic**:
same pinned runtime, float coefficients, integer stock/request/order values,
same component products and chronological `+=`, same period addition order,
and final `math.fsum`. Independent stock-flow representation remains separate
from M1. This is not a blanket rule for independently regrouped computations.
In particular, 64 periods at stock 3 and holding coefficient 0.1 legitimately
produce component-based total 19.200000000000024 while `fsum(period_costs)`
is 19.200000000000003. The valid original record is accepted; the test does
not impose the false identity between those two reductions. A second case
checks the rounding distinction between left-associated period sums and fsum.

Six cost regression methods in `tests/test_m4d0_final_hardening.py:127`
through `:212` cover the original +100 attack, one-ULP and balanced-component
attacks, changed periods, zero/subnormal/tiny/noninteger/large finite costs,
valid accumulation differences, invalid types, NaN/Inf and overflow. Canonical
JSON rejects nonfinite values before persistence; the score validator also
rejects them directly. These are binary floating-point evidence identities,
not exact real-valued money. An edit rounded back to the same float is not
a distinct stored numeric value; underflow retains ordinary float semantics.

### B. Persistence failure plus failed temporary cleanup

**Reproduced before editing:** injecting primary file-fsync failure and
secondary unlink failure raised the secondary error, not the original
persistence error; one pending file and no final file remained.

**Correction:** `m4d0_store.py:24` defines `PendingArtifactCleanupError` with
the exact `pending_path`. Cleanup (`:132`) is attempted once for this call's
own exclusively created file. If persistence/cancellation and cleanup both
fail, the exact primary exception remains primary, chained from the cleanup
diagnostic and its original OS cause (`:177`). Cleanup-only failure also
raises. File and directory fsync and no-overwrite publication remain required
before any successful return. A creation failure does not trigger deletion
of a file this call did not create.

Seven cleanup regression methods at
`tests/test_m4d0_final_hardening.py:262` through `:401` cover combined fsync
and cleanup failure, partial pending bytes, pending evidence ineligibility,
post-publication cleanup failure, synchronized retry of existing final bytes,
three bounded repeated failures, quiescent owner recovery, preservation of
another writer's pending file, repeated directory-sync failure and four actual
concurrent identical publishers. Existing create/write/fsync/publication,
symlink, short-write and retry regressions also remain passing.

Recovery is **not automatic**. OS refusal can leave partial or complete
pending files, and repeated failed attempts can accumulate them. Diagnostics
instruct the caller to stop retries. The protocol requires all writers to be
quiescent before explicit reviewed pending-file removal and directory fsync.
No age/PID heuristic can safely infer inactivity; final artifacts are never
deleted by cleanup. Rejection, successful cleanup and successful recovery are
distinct outcomes. No cleanup-success or bounded-total-disk guarantee is made.

### Final verification and authoring self-audit

| Check | Result |
|---|---|
| M4d-0 suite | **50/50 passed**, 12.974 s; 13 added regression methods |
| Complete repository suite | **268/268 passed**, 28.682 s |
| Strict scoped Ruff E,F,I,B,UP / format | Passed / eight Python files formatted |
| Structure / Git diff checks | Passed; not literature, TeX or scientific validation |
| Original protected SHA256 + size | **1,611/1,611 unchanged**; zero added/removed paths |
| New real observations, GP/RL training, GPU/baseline execution | None |

Exact commands from the feature worktree:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests CUDA_VISIBLE_DEVICES= \
  timeout 300s ../../.venv/bin/python -B -m unittest discover \
  -s tests -p 'test_m4d0*.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests CUDA_VISIBLE_DEVICES= \
  timeout 300s ../../.venv/bin/python -B -m unittest discover -s tests -v
```

Use the scoped Ruff/format commands recorded below, including the new
`tests/test_m4d0_final_hardening.py`, then `scripts/check_project.py` and
`git diff --check`. Entry and final integrity checks stream SHA256/size
against the original snapshot described below; the final check also compares
the complete protected path set in the original `github/` checkout.

Final logs and the bounded integrity script are retained outside Git under
`code/backups/m4d0-final-hardening-20261020-gq9a342j/` (directory 0700,
files 0600). Exact integrity command from this feature worktree:

```bash
../../.venv/bin/python -B \
  ../../backups/m4d0-final-hardening-20261020-gq9a342j/verify_protected.py
```

A separate authoring-account adversarial pass accepted 60 fresh complete
synthetic lifecycles (seed 20261022, coefficients from zero/subnormal through
1e300) and rejected 360 representably distinct, rehashed total/component/period
changes. Another pass checked 55 storage assertions, including cancellation
and concurrent-duplicate publication combined with fsync and cleanup failure.
An additional regression pass rejected 36 fresh original-provenance and
cost/provenance-interaction corruptions, including physically missing approval
and unapproved seed/scenario changes at all applicable stage boundaries.
All fixtures were temporary and cleaned. These are authoring-account
self-tests, **not independent peer review**; they do not extend the earlier
independent approval to unreviewed source bytes.

Representative original B1/C1–C4 cases remain passing regression checks:
nonexistent release/receipt, missing persisted approval, failed fit and false
training/retail claims; dependency/runtime/method/seed/scenario inconsistency;
target 29 and cost 209.4; terminal outstanding [5,0,0]; repeated failed syncs.
Their implementation was not redesigned. No new BLOCKING or MAJOR defect
was found in the bounded final authoring pass.

**Final author recommendation: APPROVE TO MERGE the scoped M4d-0 PR.**
M4d-1 real-data execution and EJOR publication remain NOT READY, and all
owner scientific decisions remain pending. No merge or new data release is
performed by this correction.

## Historical B1/C1–C4 response and evidence at e9698b0

The remaining sections preserve the earlier response, commands, counts and
source line references **at e9698b0**. Their pending-review statements are
historical; the completed independent re-review and final author-tested
hardening status are recorded above.

The independent review was correct: 233 passing tests missed real audit,
numerical and persistence defects. The earlier verification report is retained
as historical first-pass evidence, explicitly superseded by this response.

## B1 — auditor verifies invalid provenance (BLOCKING)

**Corrected.** `m4d0_execution.py:423` (`validated_plan`), `:477`
(`validated_fit`), `:516`/`:561` (history/outcome authorization context) and
`:612` (score schema) are shared by scoring and auditing. They reject unknown
fields, unsupported schema/types (including Boolean integer aliases), wrong
method/status/flags, incomplete identities and inconsistent current source or
runtime snapshots. The actual saved approval is loaded and strictly checked
at `m4d0_execution.py:354`; fitted policy and training counts are recomputed.

`m4d0_audit.py:27` now **requires** `evidence`, `config`, `freeze`, `catalog`;
`:44` checks the full scoped chain before numerical replay. History and
evaluation releases/receipts must actually exist in the supplied M4c
EvidenceStore and match exact protocol, freeze, source, phase, origin,
budget, cohort, series, capability and window. Plan history dates/features
are rechecked against the protocol ledger contract. There is no permissive
numerical-only audit fallback returning the old success language.

Regression evidence: `tests/test_m4d0_review_regressions.py:83`, `:93`, `:111`,
`:127`, `:149`, `:203`, `:222`, `:244`. These deliberately rehash and relink
invalid objects, delete actual persisted prerequisites, substitute
capabilities and alter terminal/trace metadata. Valid complete audit remains
accepted. A score claiming GP/RL training or retail evidence is rejected.

**Retained limit:** persisted hash-linked owner attestations do not prove
scientific validation/model-selection execution or authentic observation
bytes. Audit output explicitly says
`scientific_selection_execution_verified=false` and
`raw_observation_bytes_verified=false` (`m4d0_audit.py:175`). Owner identity is
not authenticated by these local records. A coherent fabricated authorized
synthetic lifecycle is outside the trusted-caller honesty guarantee.

## C1 — executor/scorer validation mismatch (MAJOR)

**Corrected.** Executor, scorer and auditor consume the same strict
`validated_plan` and scorer/auditor also use `validated_fit`. Current package
source hashes, full Python build/version and installed NumPy/Gymnasium versions
must match the plan; fitted dependencies must match both plan and current
source. Plan, fit, persisted approval, learner, method, seed, scenario and
initial state identities are checked together.

Regression: `tests/test_m4d0_review_regressions.py:165` constructs a valid
artifact graph, alters/relinks the plan, approval and fit, then requires all
three boundaries to reject invalid Python/runtime/dependencies, method,
Boolean seed, contradictory stock or extra fields. Malformed saved approvals
are covered separately at `:149`. Rehashing is not treated as authorization.

## C2 — floating-point target ceiling (MAJOR)

**Corrected.** `m4d0_execution.py:106` implements exact integer arithmetic:

```text
target = min(Q*(L+1), (historical_total*(L+1) + n - 1)//n)
```

Historical counts, total, budget, lead and cap have explicit integer/type/bound
checks. Neither fit nor audit computes a floating mean followed by `ceil`.
The shared helper is verified independently by `Fraction`-based test logic,
not certified solely by calling itself from both fit and audit.

Original counterexample reproduced as a regression at
`tests/test_m4d0_review_regressions.py:456`: n=28,sum=116,L=6 gives **29**, not
30. n=56/112/224 with proportional totals also gives 29. With Q=5,T=8,
stock=25, zero pipeline and requests, first order is **4**, holding cost 208,
variable ordering 0.4, fixed ordering 1: **total 209.4**, not 211.5.
Boundary grid tests at `:423` cover budgets through 3660, L=1..10, cap and
ceiling neighbors, maximum exact counts, invalid types and bounds.

## C3 — terminal outstanding convention (MAJOR)

**Corrected.** Scoring saves the last transition's `ending_on_hand` and
`outstanding_after_order` (`m4d0_execution.py:816`), not the next-period
state. The independent auditor reconstructs terminal arrivals at dates
`T..T+L-1` (`m4d0_audit.py:156`). Terminal outstanding always has L batches;
arrivals immediately after the horizon are retained. Additional terminal
value remains explicitly zero; costs do not silently include salvage.

Original regression at `tests/test_m4d0_review_regressions.py:467`:
L=3,T=2,stock=0,pipeline=[4,5],zero requests/history gives terminal stock
**4**, outstanding **[5,0,0]**, and holding cost **4**.
At `:475`, 120 bounded full synthetic lifecycles (seed 20261020) cover L=1..10,
zero/intermittent requests, initial stock/pipelines, caps, horizon/cutoff
boundaries and cost decomposition against a separate rational/calendar oracle.

## C4 — atomic durable private evidence (MAJOR)

**Corrected.** `PrivateExecutionStore` is now in `m4d0_store.py`, re-exported
from `m4d0_execution` for existing imports. `put` (`m4d0_store.py:120`) creates
an exclusive mode-0600 same-directory temporary artifact, loops on short
writes, synchronizes the complete file, atomically publishes by a hard link
that cannot replace another final name, removes its temporary link, and
synchronizes the directory before returning. Existing matching artifacts are
read/verified and synchronized again (`:115`); corrupt/conflicting objects
are rejected without overwrite. Directory/regular-file checks use held file
descriptors and no-follow opens. Reads verify canonical bytes and SHA256.

Fault injection at `tests/test_m4d0_review_regressions.py:520`, `:555`, `:582`,
`:602`, `:649` covers creation, partial/zero writes, file fsync, publication,
directory fsync, identical concurrent publication, corrupted existing objects
and retries. The original full-score fsync-failure counterexample now raises
on both failed attempt and failed retry; normal synchronized retry succeeds.
No score is returned until trace and score `put()` have both succeeded.
An explicit `fchmod` also preserves exact mode 0600 when the caller's umask
removes owner permissions; the restrictive-umask regression is at `:582`.

The guarantee assumes a POSIX local filesystem honoring `fsync` and hard-link
semantics. A post-publication directory-sync failure can leave complete final
bytes but **never returns success**. Process death may leave `.pending-*`
orphans; they are not artifacts. Owner cleanup requires confirming no active
writer. This is not hostile same-user protection or a transaction/durability
upgrade to the separate legacy M4c EvidenceStore.

## Five MINOR findings

1. **Independent numerical verification:** corrected. `m4d0_audit.py` uses an
   absolute-arrival calendar, not M1 `transition()`. The positive audit test
   at `tests/test_m4d0_review_regressions.py:83` patches production transition
   to raise during audit. Tests additionally use rational arithmetic and a
   separately expressed oracle. Shared validation/target helpers are disclosed.
2. **Dependency overclaim:** corrected and bounded. `source_hashes`
   (`m4d0_execution.py:45`) covers every local package Python source, including
   auditor/store/protocol; `runtime_versions` (`:125`) records actual runtime
   versions. Test `:258` checks formerly omitted important files. Native
   library bytes, OS/import-loader integrity and external dependency closures
   are not hermetically pinned; immutable production environment remains M4d-1.
3. **Directory invariants only checked at construction:** corrected.
   `m4d0_store.py:38` rechecks root ownership, canonical path, exact mode 0700
   and all ancestor Git markers at access. Descriptor/path identity is checked
   around operations. Regression at `tests/test_m4d0_review_regressions.py:620`
   changes mode/adds a Git marker after construction; access rejects both.
4. **Caller-supplied I/O projection:** corrected within metadata scope.
   `m4d0_io.py:79` requires config and five source sizes, recomputes the whole
   projection and compares canonical bytes. The CLI passes the context.
   Regression at `tests/test_m4d0_review_regressions.py:687` rejects forged low,
   omitted, Boolean-alias and stale projection fields without source reads.
   Declared file sizes remain trusted; this is not a dispatch meter and does
   not account for future extra method/seed preparation calls automatically.
5. **"Signed-like" terminology:** replaced in the current protocol with
   **hash-linked owner attestations**. No cryptographic signing, authenticated
   ownership, append-only chronology or actual selection execution is claimed.

## Verification and commands

From `code/worktrees/m4d0-safe-executor`, feature source explicitly selected:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests CUDA_VISIBLE_DEVICES= \
  timeout 300s ../../.venv/bin/python -B -m unittest discover \
  -s tests -p 'test_m4d0*.py' -v

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests CUDA_VISIBLE_DEVICES= \
  timeout 300s ../../.venv/bin/python -B -m unittest discover -s tests -v

../../.venv/bin/python -B -m ruff check --no-cache --select E,F,I,B,UP \
  src/inventory_ejor/data/m4d0_execution.py \
  src/inventory_ejor/data/m4d0_audit.py \
  src/inventory_ejor/data/m4d0_store.py \
  src/inventory_ejor/data/m4d0_io.py scripts/check_m4d0_io.py \
  tests/test_m4d0_execution.py tests/test_m4d0_review_regressions.py \
  tests/test_m4d0_final_hardening.py

../../.venv/bin/python -B -m ruff format --check --no-cache \
  src/inventory_ejor/data/m4d0_execution.py \
  src/inventory_ejor/data/m4d0_audit.py \
  src/inventory_ejor/data/m4d0_store.py \
  src/inventory_ejor/data/m4d0_io.py scripts/check_m4d0_io.py \
  tests/test_m4d0_execution.py tests/test_m4d0_review_regressions.py \
  tests/test_m4d0_final_hardening.py

../../.venv/bin/python -B scripts/check_project.py
git diff --check
```

| Check | Result |
|---|---|
| All M4d-0 tests | 37/37 passed in 11.493 s (15 existing + 22 added methods; many subcases) |
| Complete repository suite | 255/255 passed in 27.357 s |
| Strict scoped Ruff / format | Passed / all seven files formatted |
| Structure/bibliography-key check | Passed; not source fact-check or TeX build |
| Protected SHA256 + size | 1,611/1,611 unchanged; zero added/removed protected files |
| Reserved observation values parsed; real training/baselines; GPUs | None |

An initial full-suite invocation omitted `PYTHONPATH`: the environment's
editable main checkout lacks this feature module, causing two import errors
(220 discovered tests). Corrected feature-source invocation passed all 255.
An early existing test failed because an unapproved release was checked after
outer receipt metadata; validation ordering was corrected, without weakening
the test. Scoped lint initially caught formatting/line lengths and those were
fixed. No failing assertion was relaxed to obtain the reported pass.

Three read-only internal reviewers also challenged the revised implementation:
reported 41/41 additional provenance corruptions rejected, 19 storage checks
passed, 10,000 rational target comparisons and 110 additional full synthetic
lifecycles passed. One concurrent numerical attempt detected source drift
during an edit; the stable-source rerun passed 4/4 numerical regression methods.
Those supplementary one-off checks are not external scientific review; the
committed regression suite is the reproducible acceptance evidence.

### Original evidence integrity

Reused the saved original manifest:
`code/backups/m4c-entry-20261020-48e7zt57/protected_before.json`, SHA256
`cee767a3db64d64bdaee5f0f3133188efebecee2064c286337cec461c146ad88`.
Compared every saved byte size and streaming SHA256 (1-MiB binary chunks)
against the original `github/` artifacts and the absolute readiness marker;
compared the full file set under `data/raw`, `data/processed`, `results/runs`.
Result: 1,611 unchanged, no mismatches, no added or removed paths. Binary
hashing did not parse or inspect reserved sales values. The original 192-job
campaign was neither rerun nor regenerated. Temporary synthetic fixture
directories were cleaned by their test contexts; verification logs contain
no research observations.

Private verification logs and the bounded hashing script are retained locally
in `code/backups/pr12-review-fixes-20261020-4qntfv87/` (0700, files 0600),
outside all Git worktrees. The exact final integrity command from the feature
worktree is:

```bash
../../.venv/bin/python -B \
  ../../backups/pr12-review-fixes-20261020-4qntfv87/verify_protected.py
```

## Remaining scope gates and recommendation

- **Current B1/C1–C4:** corrected with adversarial regressions; no remaining
  demonstrated BLOCKING or MAJOR defect in the bounded synthetic reference
  contract from this authoring pass. Request external independent re-review,
  repeating the original counterexamples at the actual current PR head.
- **M4d-1: NOT READY.** Require separately approved scientific design,
  execution-verified full selection coverage, sealed scorer observation bytes,
  production separation/runtime packaging, pre-access attempt logging and
  reviewed bounded immutable batching. A metadata allowance is not a release.
- **EJOR: NOT READY.** Synthetic execution establishes no novelty, real policy
  superiority, population inference, calibration coverage or sample-size
  sufficiency. Six-method crossed baselines, matched computation/seasonal
  controls, warm-start/terminal/lead sensitivities, dependence-aware inference
  and justified external evaluation remain research work. Chronology,
  estimand, cohort, power and scientific freeze remain PENDING OWNER APPROVAL.

See `docs/M4D0_INDEPENDENT_REVIEW_HANDOFF.md` for exact repeat attacks. Do not
merge PR #12 or start M4d-1 from these engineering checks.
