# M4d-0: synthetic-only execution/evidence prototype

**Status (2026-10-20):** implementation in a scoped feature branch; **not an
approval to fit models or read any new M5 outcomes**. The owner requested the
M4d-0 engineering milestone after merging PR #11. The experiment-facing
scientific decisions, candidate 28-day schedule, source access approvals,
primary estimand, statistical power and future M4d-1 GPU campaigns remain
**PENDING OWNER APPROVAL**.

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
     - derive base-stock from the pinned history again
     - independently recheck each saved transition and score metadata
```

The implemented controller is **only** `synthetic_empirical_base_stock_reference`:
fixed lead-time-aware target from the n permitted historical sales, with
order-cap and final-horizon order cutoff. It does **not** equal a tuned
six-method M4d baseline or the proposed research contribution. It is used to
prove that learner-only dispatch and independent scorer release can be made
reproducible with exact artifact/code/seed/scenario links.

`PrivateExecutionStore` uses a pre-existing, user-owned mode-0700 directory
**outside every Git worktree**, content-addressed bounded JSON and exclusive
writes. The synthetic test harness uses `TemporaryDirectory`; observational
records and private traces are never committed. Source/runtime dependencies
are pinned by SHA256 of the reference executor, existing M4c staging/security
modules, view validator and M1 kernel, and the Python version.

The prototype is **not** a sandbox against a malicious user with access to the
filesystem or Python interpreter. A trusted caller could still create
fabricated stage/evidence files. Results from arbitrary GP/NN methods cannot
use this deterministic reference path.

## Implemented I/O performance admission gate (not an optimization)

`src/inventory_ejor/data/m4d0_io.py` computes **metadata-only** preparation
work and refuses a campaign that exceeds an explicit logical-byte allowance.
The CLI `scripts/check_m4d0_io.py` requires only a bounded JSON of five
source file sizes and the M4c protocol configuration, never an observations CSV.

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
   M4c signed-like hash records attest to user-supplied metadata; they do not
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
  ../../.venv/bin/python -B -m unittest discover -s tests -p 'test_m4d0_execution.py' -v

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests \
  ../../.venv/bin/python -B -m unittest discover -s tests -q

../../.venv/bin/python -m ruff check --select E,F,I,B,UP \
  src/inventory_ejor/data/m4d0_execution.py \
  src/inventory_ejor/data/m4d0_audit.py \
  src/inventory_ejor/data/m4d0_io.py \
  scripts/check_m4d0_io.py tests/test_m4d0_execution.py
```

A four-period synthetic case also demonstrates positive replenishment,
lead-time receipts and the final-horizon order cutoff (rather than only a
no-order short horizon). The synthetic tests verify exact
learner/decision/scorer provenance, bad
stage releases, wrong window and scenarios, absent or forged approvals,
tampered learner bytes/symlinks, altered fit/score traces even when their
untrusted hashes are recomputed, zero-request fill rates, persistence
failure and per-task method/seed/code dependency bindings.

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
