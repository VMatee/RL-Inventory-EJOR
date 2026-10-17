# M2 implementation validation — 2026-10-17

## Review correction: the 0.125 gap disappears

The user requested M2-only corrections after independent review identified the
missing horizon-aware comparator. **On the unchanged original tiny example,
DP and horizon-aware base-stock S=1 both cost 2.875. The earlier 0.125 gap
disappears.** Original constant base-stock S=1 still costs 3.000 and is explicitly
labeled the **naive comparator**. The example/configuration was not replaced,
and no search for a positive-gap example was performed.

The added policy orders zero if `remaining <= lead_time`, equivalent to an
arrival date `t+L >= T`. Under M1's nonnegative ordering costs and zero terminal
valuation, these orders cannot improve evaluated cost. The cutoff uses only
known time remaining and lead time; it never reads current/future demand.
M1 stock-flow equations, code, fixtures and tests are unchanged.

Both variants are tuned separately over S={0,1,2,3} by exact known-model
evaluation with the same initial state, costs, law, horizon and resource
allowance (1000 states, 10000 transition calls, 10 seconds per variant).
The API retains `BaseStockPolicy` and `tune_base_stock(..., horizon_aware=False)`
as the naive behavior; use `HorizonAwareBaseStockPolicy` or `horizon_aware=True`
for the finite-horizon baseline. CLI results now explicitly separate
`base_stock.naive_constant` and `base_stock.horizon_aware`.

| Same original configuration | Naive constant | Horizon-aware |
|---|---:|---:|
| Selected S | 1 | 1 |
| Expected cost | 3.000 | 2.875 |
| Absolute gap to DP=2.875 | 0.125 | **0** |
| Relative gap to DP | 0.043478260869565216 | **0** |
| Costs for S=0,1,2,3 | 3.375, 3.000, 3.500, 4.375 | 3.375, 2.875, 3.250, 4.000 |
| Cumulative tuning state-time visits / transition calls | 21 / 42 | 21 / 42 |

DP still uses 8 decision state-time keys and 48 transition calls. Returned-policy
evaluation remains 2.875, using 5 states and 10 calls. These are implementation
counts, not new observations or a training budget.

### Independent calculations and regression coverage

The independent oracle enumerates 128 complete contingent policies over eight
binary demand paths with rational arithmetic and a separate receipt calendar.
Both base-stock variants at every grid level are checked against that calendar
for the original L=1 case and the existing L=2 case with initial pipeline.
The original adaptive optimum remains **23/8**. Hand-calculated path costs
for S=1 provide a separate check:

| Demand path | Naive cost | Horizon-aware cost |
|---|---:|---:|
| 000 | 3 | 3 |
| 001 | 2 | 2 |
| 010 | 1.5 | 1 |
| 011 | 5.5 | 5 |
| 100 | 1.5 | 1.5 |
| 101 | 0.5 | 0.5 |
| 110 | 5.5 | 5.5 |
| 111 | 4.5 | 4.5 |

Each path has probability 1/8. Only paths 010 and 011 incur the naive policy's
unnecessary final order charge of 0.5: `2/8 * 0.5 = 0.125`. Thus this example
does **not** show an advantage of DP over horizon-aware base-stock. The open-loop
minimum remains 3.000; it is not an adaptive-policy benchmark.

Additional fixed regression: L=3,T=2, initial stock 0, pipeline (1,0), deterministic
demand 1, costs (1,4,0.5,0.25). With S=2, naive cost is **19/4=4.75** and
horizon-aware cost is **4**: the initial receipt meets the second period's demand,
and only the first-period lost-sales cost is necessary. Exhaustive contingent
enumeration gives 4. All horizon-aware levels in {0,1,2,3} tie at 4, selecting
S=0 by the declared tie rule. This is a cutoff regression, not a new headline
positive-gap example. Tests also verify remaining=L+1 allows an order,
remaining=L and remaining<L suppress it, invalid input is still rejected at
cutoff, and changing current/future demands while preserving the past prefix
cannot change the decision.

### Exact commands and results for this correction

Commands ran from `<workspace>/github` with the existing venv, serial bounded CPU
computations and no dependency installation:

```bash
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -v
timeout 120s ../code/.venv/bin/python -m ruff check --select E,F,I,B,UP --output-format concise src/inventory_ejor/demand src/inventory_ejor/policies src/inventory_ejor/solvers scripts/run_m2_reference.py tests/test_m2_reference.py
timeout 120s ../code/.venv/bin/python -m ruff format --check src/inventory_ejor/demand src/inventory_ejor/policies src/inventory_ejor/solvers scripts/run_m2_reference.py tests/test_m2_reference.py
timeout 120s ../code/.venv/bin/python scripts/check_project.py
timeout 120s ../code/.venv/bin/python scripts/run_m1_reference.py
timeout 120s ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
git diff --check
```

- Before correction: **61 tests passed in 0.640 s**. After: **66 tests passed
  in 0.718 s**, including 20 M2 tests and unchanged M1 regressions. No test failed.
- Ruff **0.17.1**: **all checks passed** under E,F,I,B,UP; formatting check:
  **7 files already formatted**. No suppression or lint-rule configuration added.
- Initial Ruff check failed as expected. The narrower E4,E7,E9,F,I,B,UP selection
  reproduced **14 diagnostics** in the actual checkout, versus the review's
  reported 15; the broader E selection also exposed long lines. All findings
  under the broader selection are now resolved: imports sorted, zip lengths
  explicit (`strict=True`), loop variables bound at definition, default resource
  objects constructed per call rather than in function defaults, and formatting.
- Static project check passed: 16 bibliography entries and cited keys resolve.
  M1 hand fixture remains **47.0**, with zero terminal extra cost. Whitespace and
  M1-preservation checks pass. CLI reproducibility test compares two executions.

Saved corrected smoke run (the command was also measured with `/usr/bin/time`):

```bash
/usr/bin/time -f 'elapsed_seconds=%e peak_rss_kib=%M' timeout 120s ../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/m2_tiny.json --seed 0 --timeout 110 --allow-dirty -- ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
```

New artifact: `results/runs/20261017T154421Z-smoke-2ce059a3/` containing manifest,
console output with implementation hashes, config and environment snapshot.
Status **succeeded**, exit **0**; measured elapsed **0.34 s**, peak RSS
**39,296 KiB**. Python 3.10.12, NumPy 2.2.6, Gymnasium 1.4.0 unchanged. Config
SHA256 remains `b83ffb34d20267ca1794c34781cfa5b4c7b500989a7e1d5ed66b542ca29f6027`.
No RNG is used; wrapper seed 0 is metadata and the child reports seed null.
Old run `20261017T153021Z-smoke-bdef32de` is preserved as pre-correction evidence.

### Diff, limits and review recommendation

Continued on existing dirty `feat/m2-exact-reference`, base
`2cbce59fd0cf0f738e177a0ef7e8bc6347882431`. The correction modifies 12 existing
work-in-progress files: demand validation, base-stock, DP defaults/formatting,
demo script, M2 tests, M2 reference, baseline registry, this report, and
STATUS/TASKS/DECISION_LOG/SESSION_LOG. Original tiny config, M1 specification
and implementation, package initializer stubs, user files and prior artifacts
are preserved. The original M2 diff remains unstaged/uncommitted.

Review artifacts under `results/runs/20261017T154153Z-m2-correction-6pf5fkjr/`:
`before.json` records the starting work-in-progress files, `correction.patch`
shows this turn's changes, and `full-m2.patch` includes the complete final M2
diff against HEAD, including untracked new source/tests/docs. No commit created.

The cutoff is justified for the accepted finite horizon, positive fixed lead
time, nonnegative costs and zero terminal valuation only. The corrected baseline
still uses a constant level before cutoff, tuned on a finite known-iid-law grid;
equality on this example is not universal optimality or publication evidence.
Float expectations, explicit resource limits, no stock truncation and cooperative
clock checks remain as documented. The CLI's nested variant output is a deliberate
schema change. Recommend reviewing the cutoff boundaries, equal per-variant
tuning contract and corrected zero-gap interpretation before M2 acceptance.
Stop at M2; no M3, data download, dependency installation, model/GPU training,
commit, push or merge. Suggested eventual commit message:
`feat: add M2 exact reference with horizon-aware and naive base-stock baselines`.

## Original implementation evidence (before review correction)

The sections below preserve the first implementation's commands, results and
provenance. References there to the constant baseline mean the **naive** variant;
their positive-gap interpretation is superseded by the correction above.

## Authorization and source

The actual user instruction invoked `code/CODEX_PROMPT.md` and explicitly
accepted the current M1 conventions **for M2 engineering only**. It authorized
finite-support demand, exact finite-horizon DP, known-model base-stock tuning,
independent tiny validation and a runnable configuration/demo. It did not freeze
all publication assumptions or authorize later milestones, training or publishing.

Starting checkout: clean `main`, HEAD
`2cbce59fd0cf0f738e177a0ef7e8bc6347882431`, `VMatee/RL-Inventory-EJOR`.
Confirmed `code/` cwd, existing Python 3.10.12 venv and canonical source/test/config
symlinks. No experiment or active repository writer was found; the resident
Python process was a language server. Created `feat/m2-exact-reference`.
The implementation is **this uncommitted diff on that base**, not code already
contained in the base commit. Nothing was staged, committed, pushed or merged.
M1 transition/test/fixture bytes are unchanged; its specification changes only
the approval-status paragraph.

## Changed files

New files:

- `src/inventory_ejor/demand/__init__.py`: validated known iid finite law.
- `src/inventory_ejor/solvers/__init__.py` and `finite_horizon.py`: full reachable-state DP, forward policy evaluation, diagnostics, resource limits, cost gaps.
- `src/inventory_ejor/policies/__init__.py` and `base_stock.py`: constant capped base-stock and cumulative-budget known-model grid tuning.
- `scripts/run_m2_reference.py`: strict JSON CLI and source/config provenance.
- `experiments/configs/m2_tiny.json`: bounded synthetic fixture.
- `tests/test_m2_reference.py`: independent rational/calendar contingent-policy enumeration, rejection, information and resource tests.
- `theory/M2_REFERENCE.md`: mathematical/API/baseline definitions and runnable usage.
- This evidence report.

Updated: `docs/STATUS.md`, `docs/TASKS.md`, `docs/DECISION_LOG.md`,
`docs/SESSION_LOG.md`, `experiments/baselines/BASELINE_REGISTRY.md`, and
`theory/INVENTORY_MODEL.md` (status paragraph only). No manuscript, raw/processed
data, dependency/environment, existing result or later-milestone implementation edits.

## Commands and checks

All commands ran from `<workspace>/github` using the existing environment.
Tests/demos ran serially on CPU with process timeouts <=120 seconds.

```bash
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -v
```

Before edits: **46 tests passed**, 0.121 seconds reported by unittest.
After implementation: **61 tests passed**, 0.550 seconds, including **15 M2 tests**
and all unchanged M1 tests. The existing credential-rejection test prints an
expected `BLOCKED` message and passes; no acquisition is attempted. ZIP checks
use synthetic temporary fixtures, not retailer data.

```bash
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -p test_m2_reference.py -v
```

Initial focused pass: 14 tests in 0.429 seconds. One additional CLI failure test
was then added and included in the 61-test pass. The reproducibility test runs
the CLI twice with a 15-second timeout per child and verifies identical stdout.

```bash
timeout 120s ../code/.venv/bin/python scripts/check_project.py
timeout 120s ../code/.venv/bin/python scripts/run_m1_reference.py
git diff --check
```

Static check passed: 16 bibliography entries and all 16 cited keys resolve.
M1 fixture still gives **47.0**, terminal pre-receipt stock **0**, outstanding
receipts **[4,1,0]**, extra terminal cost **0**. Whitespace check passed.
No failing test invocation occurred. Invalid-input and budget-exhaustion checks
are expected rejections; the CLI emits an error without a partial solution.

## Demonstration and independent validation

```bash
timeout 120s ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
```

L=1, T=3, Q_max=1; initial on-hand=1 and empty pipeline;
costs (holding, lost sales, variable order, fixed order)=(1,4,0.5,0).
Known iid demand is 0 or 1 with probability 0.5 each; additional terminal value=0.
The child parses and uses the configuration. There is no RNG/seed requirement.

| Quantity | Measured value |
|---|---:|
| DP expected cost | 2.875 = 23/8 |
| Initial optimal action | 0 |
| Returned policy forward-evaluated cost | 2.875 |
| DP decision state-time keys / transition calls | 8 / 48 |
| Returned policy evaluation states / calls | 5 / 10 |
| Tuned constant base-stock level | 1 |
| Base-stock expected cost | 3.000 |
| Absolute / relative gap to DP | 0.125 / 0.043478260869565216 |
| Aggregate grid evaluation states / calls | 21 / 42 |
| Grid S=0,1,2,3 costs | 3.375, 3.000, 3.500, 4.375 |

Independent validation enumerates **128 complete contingent policies** over
**8 demand paths** in each fixture using rational arithmetic and a separately
written receipt calendar. It uses neither the production transition nor Bellman
recursion. L=1 optimum **23/8** agrees; the open-loop minimum is **3**, strictly
worse and explicitly not an adaptive optimum. L=2 with initial stock=0,
pipeline=(1,), fixed order cost=0.25 and otherwise the same settings gives
adaptive optimum **15/4=3.75**, also agreeing. Every grid baseline and returned
DP policy are independently evaluated on calendar paths. A deterministic hand
case gives **7**, versus zero-order cost **15** and constant-one-order cost **8**.

Tests also cover probability validity/roundoff normalization, L=1/L>1,
initial pipeline, horizon shorter than lead time, one-period and zero demand/order
cases, action/level ties, zero reference, time-dependent decisions, same-prefix
no-lookahead, invalid policy/configs, inventory above a small artificial cap,
cost overflow, and state/work/time exhaustion.

## Saved artifact and resource measurements

```bash
/usr/bin/time -f 'elapsed_seconds=%e peak_rss_kib=%M' timeout 120s ../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/m2_tiny.json --seed 0 --timeout 110 --allow-dirty -- ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
```

Created a fresh ignored directory:
`results/runs/20261017T153021Z-smoke-bdef32de/` with `manifest.json`, `config.json`,
`environment.json` and `console.log`. Status **succeeded**, exit **0**;
wrapper-recorded child runtime **0.214406 s**, external elapsed **0.37 s**,
peak RSS **38,888 KiB**. One computation process; the wrapper records provenance
and supervises it. No GPU operation, sweep or training.

Config SHA256:
`b83ffb34d20267ca1794c34781cfa5b4c7b500989a7e1d5ed66b542ca29f6027`.
Python **3.10.12**, NumPy **2.2.6**, Gymnasium **1.4.0**; full installed dependency
snapshot is in `environment.json`. Child output contains individual SHA256 hashes
of all production Python files and the demo script, identifying the dirty source.
The wrapper's required seed 0 is metadata only: the deterministic child explicitly
reports `seed: null`, since exhaustive expectations consume no random draws.

The wrapper records `clean_source=false` and `source_unchanged=false` because its
conservative predicate requires a clean checkout both before and after. Recorded
Git statuses and HEAD are equal across the run; no source was edited during it.
This is dirty-source engineering evidence, not a fixed-commit research run.
Subsequent documentation edits do not alter the saved implementation hashes.

## Limitations and acceptance gate

Known iid finite integer demand only: no fitted forecaster, dependent demand,
latent regime, uncertainty guarantee, GP/RL or retail-data inference. The baseline
is optimal only on its declared constant-level grid; end-of-horizon placement
cost artifacts remain visible. Probability tolerance is 1e-12; demo comparison
tolerance is 1e-10. Float expectations are not a new theorem or general numerical
error bound. Final publication assumptions remain open.

No inventory truncation. Demo budgets are 1000 decision states, 10000 transition
calls and 10 seconds for each DP/replay/tuning operation (cumulative across tuning
levels), plus an external process timeout. State/work limits bound containers,
not OS memory. Clock checks are cooperative and custom policy callbacks must
terminate. Large-instance scalability and empirical comparisons are untested.

M2 is implemented and locally tested, **awaiting owner review**. Proposed commit:
`feat: add M2 exact inventory reference and tuned base-stock baseline`.
Next task: review M2; only after acceptance and separate authorization, begin M3
leakage-safe data/information contracts with synthetic fixtures. Stop here.
