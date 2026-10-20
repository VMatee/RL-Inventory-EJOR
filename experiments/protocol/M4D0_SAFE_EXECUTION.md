# M4d-0: synthetic-only execution/evidence prototype

**Status (2026-10-20):** implementation in a scoped feature branch; **not an
approval to fit models or read any new M5 outcomes**. The owner requested the
M4d-0 engineering milestone after merging PR #11. The experiment-facing
scientific decisions, candidate 28-day schedule, source access approvals,
primary estimand, statistical power and future M4d-1 GPU campaigns remain
**PENDING OWNER APPROVAL**.

Independent re-review approved the scoped implementation at `e9698b0`.
The final cost-verification/cleanup hardening described below is newly
author-tested; that earlier approval is not attributed to these later edits.

## Motivation

M4c established separate `prepare_learner()` and `prepare_evaluation()`
capabilities and source/evidence integrity, but did **not** implement an
experiment executor, validate that selection code actually ran, pin loaded
model/config dependencies, or solve repeated source hashing (~1.04 TiB of
logical processing in the candidate 32-series × 7-origin design).

The original 192-job `d_225` run remains immutable. This milestone explicitly
does NOT rerun it, train a GP/NN/RL policy, open an unexposed M5 window, obtain
Kaggle/Favorita data, or create a publication-effect estimate.

## Implemented, deliberately bounded reference contract

```text
Existing M4c trusted preparer (synthetic, approved history release)
  -> LearnerView + validated access ledger/receipt
  -> publish_learner_only_plan(...)
     - task/phase/cohort/window/ledger verification
     - actual bounded learner-only JSON bytes (private, SHA256-addressed)
     - frozen scenario, task, seed, versioned dependency digests
     - no evaluation or raw reader handle in learner artifact/plan
  -> separate execution_approval_template(plan_hash), owner attestation
  -> execute_synthetic_reference(...)
     - rehash loaded learner, dependencies and exact trained view
     - deterministic EMPIRICAL base-stock reference from training history
     - 0 optimizer steps, 0 GP/RL training, no evaluator input
     - exclusive/hashed fit evidence written before returned
  -> trusted independent scorer with a separately approved outcome release
     - existing M4c prepare_evaluation(...) produces EvaluationTargets
     - scorer checks outcome receipt, task identity and policy evidence
     - revalidates the deterministic fitted reference decision
     - sequentially chooses an order BEFORE consuming each request
     - M1 stock-flow/cost replay and private, hashed score+trace persistence
  -> independent read-only verify_synthetic_reference_trace(...)
     - mandatory persisted M4c history/outcome release and receipt context
     - same strict plan, approval, fitted-result and score schema validators
     - derive base-stock from the pinned history again
     - separate absolute-arrival stock-flow oracle (does not call M1 transition)
     - recheck every saved transition, terminal batch and score metadata
```

The implemented controller is **only** `synthetic_empirical_base_stock_reference`:
fixed lead-time-aware target from the n permitted historical sales, with
order-cap and final-horizon order cutoff. It does **not** equal a tuned
six-method M4d baseline or the proposed research contribution. It is used to
prove that learner-only dispatch and independent scorer release can be made
reproducible with exact artifact/code/seed/scenario links.

For integer historical total `s`, history length `n`, lead `L` and order cap
`Q`, the target is exactly `min(Q*(L+1), (s*(L+1)+n-1)//n)`; no floating-point
mean or ceiling is used. Each count is a nonnegative integer bounded by
`2**53`; `n <= 3660`, `L <= 10`, `Q <= 100` and horizon `T <= 128` bound this
prototype. An order at period `t` is suppressed when `t+L >= T`. Terminal
stock is after the last request, **before** any next-period receipt. Terminal
outstanding is the final transition's `outstanding_after_order`, of length
`L` (arrival dates `T` through `T+L-1`); these batches are reported even with
zero salvage. No terminal disposal charge, shortage backlog or salvage value
is introduced.

### Defined floating-point cost representation

The reference uses finite nonnegative binary floating-point scenario costs,
not exact decimal accounting. Its reproducible evidence format specifies:

- Period cost is left-associated `((holding + lost_sales) + variable_order)
  + fixed_order`, matching M1 `StepCosts.total`.
- Each component total uses chronological `+=` starting at `0.0`.
- The saved total equals `math.fsum(saved_component_totals.values())` exactly.

The independent arrival-calendar audit reconstructs the same coefficient/count
products and specified addition order under the pinned runtime. Therefore
saved period costs and components can be compared exactly; a scale-relative
or fixed absolute tolerance is unnecessary for these evidence identities.
The shared score validator also checks the exact internal total/components
identity and rejects invalid, nonfinite or overflowing totals. Rehashing
`5e15` to `5e15+100`, changing one representable unit, or adjusting components
and total coherently must not pass merely because costs are large or tiny.

This does **not** require the total to equal `math.fsum(period_costs)`: that
regroups rounding operations. For 64 periods with stock 3, no requests/orders
and holding coefficient 0.1, the valid component-based total is
19.200000000000024, while `fsum(period_costs)` is 19.200000000000003. The audit
accepts that legitimate difference. Alternative arithmetic algorithms or
runtime environments need a new reviewed contract; this is neither numerical
perfection nor general tolerance-free comparison of independent algorithms.
Underflow follows float semantics; a proposed edit that rounds back to the
identical numeric value is not a distinct stored cost discrepancy.

`PrivateExecutionStore` uses a pre-existing, user-owned mode-0700 directory
**outside every Git worktree**, content-addressed bounded JSON, and rechecks
directory ownership/mode/canonical location at every access. Artifact reads
use a bounded regular-file descriptor with `O_NOFOLLOW`, require mode 0600
and verify canonical bytes and SHA256. The synthetic test harness uses
`TemporaryDirectory`; observational records and private traces are never
committed.

Successful `put()` means exclusive same-directory temporary creation, a
complete write, file `fsync`, atomic no-overwrite hard-link publication,
temporary unlink and directory `fsync` have succeeded. An existing matching
artifact is read/verified and **file- and directory-synchronized again**.
Pre-publication failures leave no final name and attempt owned temporary
cleanup once. If deletion also fails, the original persistence exception
remains primary, chained from `PendingArtifactCleanupError` (with
`pending_path`) and the original OS cleanup error. A cleanup-only failure
raises that diagnostic; neither case returns success.
A directory-sync failure after publication may leave complete final bytes,
but raises; retry cannot bypass synchronization. Process death **or failed
cleanup** can leave partial or complete `.pending-*` files. These names are
never recognized as artifacts; reading their content hash does not promote
them. Normal retries do not prune or reuse pending files. Persistent cleanup
failures can accumulate one orphan per attempted new publication: no global
disk-usage bound is claimed. Stop retries and recover explicitly. This
assumes POSIX local storage honoring `fsync`/atomic hard links, not network
filesystem semantics or a hostile same-user writer. It does not add these
durability properties to the existing M4c EvidenceStore.

Owner-controlled orphan recovery is deliberately not automatic:

1. Stop and quiesce **all** processes allowed to write that private store.
   File age, PID labels or an `lsof` snapshot alone do not prove inactivity.
2. Reconfirm the canonical caller-owned mode-0700 root outside Git worktrees.
   Inspect only explicitly reviewed `.pending-[0-9a-f]{32}` names as regular
   caller-owned files, without following symlinks.
3. Remove those reviewed pending files, never `<SHA256>.json` final artifacts
   or files belonging to active writers. Synchronize the directory with
   `fsync` after deletion. If deletion or synchronization fails, report failure
   and stop; do not announce successful recovery or continue an automatic loop.

Each `put` cleans only its own newly created temporary file. There is no age
heuristic, background collector or cleanup API that can race an active writer.

The consumed dependency manifest hashes **all local
`src/inventory_ejor/**/*.py` files**, including this auditor and store;
executor, scorer and auditor require the same current snapshot. Runtime
identity includes full Python build/version and installed NumPy/Gymnasium
versions. This is not a hermetic pin of native binaries, operating system,
import loader, external distribution contents or every transitive dependency.
Source mutation while a lifecycle is running is unsupported and fails
subsequent snapshot comparison; real M4d-1 needs an immutable runtime image.

The prototype is **not** a sandbox against a malicious user with access to the
filesystem or Python interpreter. A trusted caller could still create
fabricated stage/evidence files. Results from arbitrary GP/NN methods cannot
use this deterministic reference path.

Audit success now requires actual persisted, correctly linked release,
receipt, approval, plan, learner, fit, trace and score records. Rehashing and
relinking invalid records does not bypass schema, identity, current runtime,
status, method, exact policy or numerical checks. The audit API requires
`evidence`, `config`, `freeze` and `catalog` keyword context; there is no
numerical-only fallback with the same success status. Its explicit
`authorization_attestations_verified=true` means structural/persisted
authorization consistency, **not authenticated owner identity or executed
scientific model selection**. `scientific_selection_execution_verified` and
`raw_observation_bytes_verified` are both false. A trusted owner can still
fabricate a coherent authorized synthetic evidence graph; M4c receipts do
not bind the actual returned evaluation bytes. Replaying supplied targets
and saved traces cannot establish otherwise.

## Implemented I/O performance admission gate (not an optimization)

`src/inventory_ejor/data/m4d0_io.py` computes **metadata-only** preparation
work and refuses a campaign that exceeds an explicit logical-byte allowance.
The CLI `scripts/check_m4d0_io.py` requires only a bounded JSON of five
source file sizes and the M4c protocol configuration, never an observations CSV.
The public allowance helper also requires this configuration and size context
and recomputes the complete projection before comparison. A caller-supplied
reduced total, omitted field or stale projection is rejected. Source sizes
remain declared metadata; this is not a live call meter or authenticated
proof of file sizes. Any future executor with repeated method/seed reads
must account for those calls separately and enforce the bound at dispatch.

Under the existing source-adapter behavior (all five source files hashed
twice per read, one sales CSV scan and one calendar read), the current
32-series × 7-origin × 4-budget M4c candidate implies:

| Quantity | Estimated value |
|---|---:|
| Histories | 896 |
| Separate scorer windows | 224 |
| Total per-item reader calls | 1,120 |
| Logical bytes per call | 1,022,784,555 |
| **Total logical processed data** | **1,145,518,701,600 bytes (~1.04 TiB)** |

The calculation assumes one outcome read per series/origin (not four per
budget); repeated scoring per policy/seed could multiply it. This is **not
physical disk traffic, measured runtime or a verified optimized throughput**.
An 8-GiB admission budget appropriately rejects the candidate. A caller
entering a larger allowance is not automatically approved to execute a
campaign; scientific and data-access releases are independently required.

**Still required for real M4d-1:** a reviewed immutable snapshot/validated
batch-preparer design that preserves per-item exact access, source integrity,
per-task receipts and an auditable failure/attempt log without exposing
prohibited dates via shared caches. Benchmark it with synthetic data and
hard upper bounds before any real-source run. Simply removing hashes or
caching unrestricted M5 arrays in learner processes is prohibited.

## Explicitly not yet implemented

1. **Real-data stage execution**: `m4d0_execution.py` intentionally refuses
   the M5 dataset and every non-synthetic dataset. Only synthetic development
   tasks are supported. No runner enabling final/validation or calibration
   evidence has been deployed.
2. **Six competitive baselines**: empirical/Gamma-Poisson/GP and each
   base-stock/rollout controller plus seasonal, recency, compute-matched and
   warm-start comparators are future M4d-1 work.
3. **Execution-verified validation -> selection -> calibration**: existing
   M4c hash-linked owner attestations record user-supplied metadata; they do not
   verify that validation policies were actually fitted/scored. M4d-1 must
   bind complete method/seed/outcome coverage, actual model checkpoints,
   scorer audits, causal chronology and selection/computation evidence before
   calibration. Synthetic reference fit verification is not this guarantee.
4. **Production isolation**: policy code in this prototype is fixed,
   deterministic, trusted Python; it is not a general untrusted plugin sandbox,
   independent OS process, GPU worker, container or runtime resource monitor.
   Production learner code must never receive a scorer object, evaluator data
   or path, or raw source reader; separate processes/permissions should be
   reviewed for stronger fault isolation.
5. **Durability and adversaries**: content hashes and mode-0700 local stores
   provide accidental-tampering evidence, not authenticated signing,
   append-only event ordering or immunity to a privileged local writer.
   M4c can record a successful release *after* reading data; a failing receipt
   write may expose values without a success record. M4d-1 needs a
   pre-access intent/attempt journal and appropriate atomic response handling.
6. **Actual evaluator-byte binding**: an M4c outcome receipt binds allowed
   source/window/phase but not cryptographically the observation bytes it
   returned. This prototype trusts the separate scorer's
   `prepare_evaluation()` output and its recorded private trace. The eventual
   scorer should seal the **actual evaluator artifact bytes** and verify this
   binding before scoring, without ever making that artifact learner-visible.
7. **Formal statistics and theoretical novelty**: synthetic reference tests
   establish no EJOR empirical superiority, policy-improvement bound,
   selection-valid calibration or generalization. Final phase geometry,
   primary estimand and scientific release remain undecided.

## Reproducible checks (synthetic-only)

From the feature worktree, with its own source on `PYTHONPATH`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests \
  CUDA_VISIBLE_DEVICES= timeout 300s ../../.venv/bin/python -B \
  -m unittest discover -s tests -p 'test_m4d0*.py' -v

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests \
  CUDA_VISIBLE_DEVICES= timeout 300s ../../.venv/bin/python -B \
  -m unittest discover -s tests -v

../../.venv/bin/python -B -m ruff check --no-cache --select E,F,I,B,UP \
  src/inventory_ejor/data/m4d0_execution.py \
  src/inventory_ejor/data/m4d0_audit.py \
  src/inventory_ejor/data/m4d0_store.py \
  src/inventory_ejor/data/m4d0_io.py \
  scripts/check_m4d0_io.py tests/test_m4d0_execution.py \
  tests/test_m4d0_review_regressions.py tests/test_m4d0_final_hardening.py
```

A four-period synthetic case also demonstrates positive replenishment,
lead-time receipts and the final-horizon order cutoff (rather than only a
no-order short horizon). The synthetic tests verify exact
learner/decision/scorer provenance, bad
stage releases, wrong window and scenarios, absent or forged approvals,
tampered learner bytes/symlinks, altered fit/score traces even when their
untrusted hashes are recomputed, zero-request fill rates, persistence
failure and per-task method/seed/code dependency bindings.

The correction suite adds the historical `116/28, L=6` rounding
counterexample (target 29, independent total cost 209.4), terminal initial
pipeline `[4,5]` at `L=3,T=2`, 120 fixed-seed full lifecycles checked by a
test-only rational arithmetic/arrival-calendar oracle, rehashed/relinked
invalid evidence graphs and file/write/fsync/publication/retry fault injection.
These tests validate the bounded reference implementation, not general
numerical optimality or learned policy quality.

`test_m4d0_final_hardening.py` adds full-lifecycle cost forgeries, valid
zero/subnormal/noninteger/large-cost representations, combined persistence and
cleanup failures, pending-file ineligibility, explicit quiescent-owner recovery,
unchanged unrelated pending files and four actual concurrent publishers.

Do not run `scripts/run_baselines.py` or `scripts/start_baselines.py` as
part of M4d-0. Existing `results/runs/m4-approved-yc4xtrp1/` is immutable.

## Next review/owner gates

- Independent adversarial review of this PR, particularly the boundaries
  between trusted M4c authorized reads and synthetic-only reference stages.
- Separate owner approval of an **M4d-1 scientific design and execution
  allowance**, including data access, planned compute and real phases.
- Implement production scorer source-byte binding, genuine execution-verified
  selection evidence, integration with exact official learner-only manifests,
  and bounded data preparation before touching new real M5 outcomes.
- Perform controlled development-only baseline model × controller and
  cold/warm initialization ablations; no final inference until its protocol
  is explicitly frozen.
