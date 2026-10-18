# M3 implementation and independent engineering evidence — 2026-10-18

M3 is implemented as an **uncommitted review diff**, not scientifically accepted.
Source base: `14d0741ea2328aa28cef7612976357c4b3cb6d53`.
Branch: `feat/m3-data-information-protocol`. Nothing staged, committed, pushed or
merged. M4/GP/RL training, new downloads, installations and manuscript results were
not started. This report supersedes stale status statements that M2 awaits review;
it does not rewrite the historical M2 evidence.

## Entry checks and authorization

The owner explicitly authorized M3 and subsequently confirmed resolution of the
launcher blocker. Independently checked correct `code/` working directory and
existing Python 3.10.12; clean `main`; local HEAD and live `git ls-remote origin
refs/heads/main` both `14d0741...`; no Git index lock or competing process with a
working directory in the repository. Created the requested branch from that main.
The separate launcher branch remains `cd43843c1d20eb5b5b8073ce73f26a07d61db3fa`.
No automatic stash, reset, pull, checkout of another branch, or data deletion.
Process-cwd inspection is a practical concurrency check, not a proof against all
possible external writers.

Read the workspace/canonical AGENTS, status/charter/tasks/decisions/implementation
plan, M1 specification, M2 reference, evaluation protocol and dataset source plans.
Ran the existing 66 tests before edits: **66 passed in 0.619 s**. Initial project
check and M1/M2 reference commands also succeeded. Saved SHA256/size snapshots of
59 existing files under raw/processed data and results before creating artifacts.

## Delivered components and complete changed-file inventory

| Path | Role |
|---|---|
| `src/inventory_ejor/data/__init__.py` | Data package; sales interpretation boundary |
| `src/inventory_ejor/data/contracts.py` | Immutable observations/history/targets, half-open windows, phases/origins, normalization and feature availability |
| `src/inventory_ejor/data/m5.py` | Streaming M5 catalog, calendar and requested sales; deterministic selection, historical overlap check, weekly price alignment |
| `src/inventory_ejor/data/budgets.py` | Strict information ledgers, real-observation unions, track labels and conservative comparison checks |
| `src/inventory_ejor/data/provenance.py` | Strict JSON, input/artifact hashes, source identity, exclusive output writes |
| `src/inventory_ejor/data/preparation.py` | Bounded development preparation, cohort decisions, nested views, split/information manifests |
| `src/inventory_ejor/data/views.py` | Separate learner artifacts and pinned single-task consumer interface |
| `src/inventory_ejor/data/synthetic.py` | Bounded seeded finite-law iid synthetic observations; zero real-data credit |
| `scripts/prepare_m3.py` | CPU-only CLI; memory/CPU caps; fresh ignored output directories |
| `scripts/audit_m3.py` | Independent read-only original-CSV/artifact/repeat/preservation audit |
| `tests/m3_fixtures.py` | Independent miniature CSV fixtures with no actual retailer records |
| `tests/test_m3_data.py` | 45 adversarial and independent regression tests |
| `experiments/configs/m3_development_demo.json` | Deterministic seed-0 bounded development demo |
| `experiments/configs/m3_protocol_proposal.json` | Non-executable scientific proposal; final dates explicitly null |
| `experiments/protocol/EVALUATION.md` | Expanded proposed chronological, information, covariate and external-validation protocol |
| `data/M3_PIPELINE.md` | Reproduction commands and common learner interface |
| `data/DATASET_PLAN.md` | Appended current M3 engineering status; acquisition history retained |
| `docs/STATUS.md` | Current M2 merge/M3 review status and remaining gates |
| `docs/TASKS.md` | M2 merge confirmation, M3 deliverables and review gate |
| `docs/DECISION_LOG.md` | Actual M3 authorization and engineering choices; scientific proposals labeled |
| `docs/SESSION_LOG.md` | Appended session work, checks and unresolved decisions |
| `results/summaries/M3_IMPLEMENTATION_REVIEW_20261018.md` | This review report |
| `results/summaries/m3_verification_20261018.json` | Aggregate machine-readable evidence, source/config identities and artifact fingerprints; no restricted records |

All other existing code, M1/M2 fixtures, configurations, source manifests and
historical results remain unchanged. Preparation/audit use the Python standard
library. The synthetic helper reuses M2 finite-law validation, which transitively
imports the already-installed NumPy/Gymnasium through M1. Ruff version: 0.17.1.
The wrapper records the complete existing environment; no dependency changes.

## Executed validation and measured outcomes

| Check | Result |
|---|---|
| Existing baseline suite before changes | 66/66 passed, 0.619 s |
| Final complete suite | **111/111 passed**, 1.372 s |
| Final M3-only suite | **45/45 passed**, 0.758 s |
| Ruff E,F,I,B,UP on M3 Python files | Passed |
| Ruff formatting on M3 Python files and pipeline documentation | Passed |
| Project structural/citation check | Passed: 16 bibliography entries and 16 citation keys |
| M1 regression | Cost 47; complete JSON output identical before/after |
| M2 regression | DP 2.875; horizon-aware S=1 cost 2.875; naive S=1 cost 3.000 |
| M2 complete output comparison | Identical before/after except code provenance, as expected |
| M1/M2 source, tests, fixtures, reference CLI diff | Empty |
| First preparation | Exit 0; 8.018 s; peak RSS 55,028 KiB |
| Repeat preparation | Exit 0; 7.562 s; peak RSS 55,256 KiB |
| Original M5 input SHA256/size checks | All five files matched before/after and in independent audit |
| Independent raw-CSV/normalization audit | All 20 learner views verified; five evaluator trajectories matched source cells |
| Deterministic artifacts | **22/22 identical** across runs: 20 learner files, cohort, evaluator outcomes |
| Preservation snapshot | **59/59 pre-existing raw/processed/results files unchanged** by SHA256 and size |
| Git tracking of restricted directories | Only `.gitkeep` tracked in raw, processed and run directories |
| Whitespace diff check | Passed |

The full suite includes mocked Favorita acquisition tests that print a synthetic
ZIP result and an expected missing-credentials diagnostic. These do **not** mean
Favorita was downloaded or authenticated during this session.

Repository-wide lint is **not clean**: `ruff check --select E,F,I,B,UP .` reports
54 findings in 12 unchanged HEAD files. Repository-wide formatting flags 13
unchanged HEAD files. Byte comparisons with `git show HEAD:path` verified their
pre-existing status. M3 code passes; no unrelated M1/infrastructure formatting was
changed to conceal the broader failure. Logs remain in the local audit directory.

An initial M3 fixture test incorrectly expected removing the first observation
to invalidate a generic History, although that creates a valid shorter history.
It was corrected to remove an interior day; ledger tests separately reject a
mismatched declared n. The initial M3 lint pass also found formatting/style issues,
which were corrected. Final tests above passed; these initial failures are not
reported as successful checks. A review-patch helper also initially treated
`git diff --no-index --check` exit 1 (files differ, no whitespace diagnostic) as
a failure; the helper was corrected to distinguish differences from errors.

## Exact reproduction and verification commands

All commands below run from `github/` using the existing sibling environment.
Every test/demo process is bounded at 120 seconds or less.

```bash
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/main
git switch -c feat/m3-data-information-protocol

timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -v
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -p 'test_m3_data.py' -v
timeout 120s ../code/.venv/bin/python scripts/check_project.py
timeout 120s ../code/.venv/bin/python scripts/run_m1_reference.py
timeout 120s ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json

timeout 120s ../code/.venv/bin/python -m ruff check --select E,F,I,B,UP src/inventory_ejor/data scripts/prepare_m3.py scripts/audit_m3.py tests/test_m3_data.py tests/m3_fixtures.py
timeout 120s ../code/.venv/bin/python -m ruff format --check src/inventory_ejor/data scripts/prepare_m3.py scripts/audit_m3.py tests/test_m3_data.py tests/m3_fixtures.py data/M3_PIPELINE.md
# These broader checks were executed and failed on pre-existing files:
timeout 120s ../code/.venv/bin/python -m ruff check --select E,F,I,B,UP . --output-format concise
timeout 120s ../code/.venv/bin/python -m ruff format --check .

# Executed twice, each producing a fresh local run and processed directory:
timeout 120s ../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/m3_development_demo.json --seed 0 --timeout 110 --allow-dirty -- ../code/.venv/bin/python scripts/prepare_m3.py --config experiments/configs/m3_development_demo.json --seed 0

timeout 120s ../code/.venv/bin/python scripts/audit_m3.py --directory data/processed/m3-demo-9xfx5j08 --repeat data/processed/m3-demo-myd3wrbj --preservation-snapshot results/runs/m3-audit-r1y6p0fm/before.json

git diff --check
git ls-files data/raw data/processed results/runs
git status --short --branch
git status --porcelain=v1 --untracked-files=all
git diff --cached --stat
```

The reference CLIs were captured in a synchronous Python harness using
`subprocess.check_output(..., cwd=repository, timeout=110)` inside an external
`timeout 120s` process. Their saved JSON was compared after dropping only the M2
`provenance` field. Unit-test stdout/stderr and broad lint outputs were redirected
to fresh audit log files; no previous logs were overwritten.

The branch-creation command is historical evidence, **not** a command to rerun
on the current dirty task branch. The demonstration and audit commands are runnable
now. Use the new output paths printed by any later demo.

Local artifacts:

- Audit/baseline/reference/test logs: `results/runs/m3-audit-r1y6p0fm/`.
- First wrapper: `results/runs/20261018T071712Z-smoke-680f9607/`.
- First processed bundle: `data/processed/m3-demo-9xfx5j08/`.
- Repeat wrapper: `results/runs/20261018T071856Z-smoke-db292bd3/`.
- Repeat processed bundle: `data/processed/m3-demo-myd3wrbj/`.

Each processed manifest records original input hashes, config, origin/date/split
bounds, information ledgers, source-file hashes at dirty base `14d0741`, environment,
resource limits and output hashes. The data artifacts are byte-reproducible;
manifest runtime/command metadata is run-specific. The preparation source did not
change between the two runs. The independent auditor and its two tests were added
after those runs and audited the already saved artifacts; their identities are
included in the aggregate verification record.

## Actual data findings and information use

The inspected real schemas have 30,490 item/store series, 1,941 canonical sales
days, and 1,969 calendar days. Validation CSV ends d_1913; evaluation extends the
same history to d_1941. The canonical 1941-day matrix is streamed, not materialized.
Only requested cells are parsed as sales. Overlap comparison covered the five
retained series' d_1..d_224 histories, not the whole real matrix.

The deterministic demo uses d_225 as the first origin with a complete 224-day
history. Maximum history: 2011-01-29..2011-09-09; development outcomes:
2011-09-10..2011-10-07. These engineering dates are not proposed final cutoffs.
Eight hash-ranked candidates were fixed using seed 0. Five met the proposed rule
of at least one positive sale in the latest 28 days; three were excluded without
replacement. No seed/cutoff search was performed.

There are 1,120 distinct retained maximum-history sales observations, of which
**988 are zero**, and 140 separate development outcome observations. All selected
cells parsed as nonnegative integers with complete dates; no clipping, rounding,
filling, or stockout inference. The zero prevalence and earliest-history origin
make this a poor basis for generalizing demand behavior; it is a preparation smoke
case, not a selected publication sample.

Each of the 20 learner views has exactly 28, 56, 112 or 224 real observations.
Normalization and own-series screening reuse those observations, rather than
adding real-data credit. No pooling, pretraining, hyperparameter fitting,
calibration/validation fitting, demand-model fitting, or synthetic inventory
training occurred. Civil-calendar features are deterministic; no price/event/SNAP
features entered learners. The code exposes all these information categories for
later methods and rejects undeclared additional information in the per-series
track.

The **study-wide** view is different: screening inspected 8×28=224 candidate
observations, including 84 from excluded series. Maximum retained histories plus
excluded screening contain 1,204 distinct historical sales cells, not merely 28.
All metadata IDs in the 30,490-series roster were read. The manifest discloses this
shared design access separately; per-method n must never be presented as the
entire study's real-data consumption. Fixed rolling cohorts can retain earlier
screening information, and are automatically labeled richer-data access where it
falls outside a later history.

A separate post-selection retrospective price join audit over the retained
224-day histories matched 102 of 160 possible series/week keys; 406 of 1,120
series-days had no matching price. This was not used for cohort selection or any
learner input, and no values were filled. Missing prices and zero sales do not
identify stockouts or uncensored demand. Weekly price publication timing remains
unknown. The audit took 6.178 seconds; its aggregate record is
`results/runs/m3-audit-r1y6p0fm/price-audit.json`.

Exact price inspection body (executed under `timeout 120s ../code/.venv/bin/python -`):

```text
from inventory_ejor.data.m5 import ReadLimits, load_calendar, load_catalog, load_prices
from pathlib import Path
import json, time
root=Path.cwd(); start=time.monotonic(); limits=ReadLimits(max_seconds=100)
cohort=json.loads((root/'data/processed/m3-demo-9xfx5j08/cohort.json').read_text())
cal=load_calendar(root/'data/raw/m5/calendar.csv',limits)
catalog,_=load_catalog(root/'data/raw/m5/sales_train_evaluation.csv',limits)
keys=tuple(cohort['included']); days=tuple(range(1,225))
weeks=tuple(sorted({cal[d]['wm_yr_wk'] for d in days}))
prices=load_prices(root/'data/raw/m5/sell_prices.csv',catalog,keys,weeks,limits)
missing=sum((key,cal[d]['wm_yr_wk']) not in prices for key in keys for d in days)
summary={'scope':'post-selection retrospective price join audit only; not learner feature access','history_window':[1,225],'selected_series':len(keys),'requested_weeks':len(weeks),'matched_series_week_prices':len(prices),'requested_series_days':len(keys)*len(days),'missing_price_series_days':missing,'imputation':False,'used_in_cohort_selection':False,'known_at_decision_time_claimed':False,'runtime_seconds':time.monotonic()-start}
p=root/'results/runs/m3-audit-r1y6p0fm/price-audit.json'
with p.open('x') as f: json.dump(summary,f,indent=2)
print(json.dumps(summary,indent=2))
```

## Proposed protocol, unresolved decisions and critical assessment

The full proposal is `experiments/protocol/EVALUATION.md`. It keeps development,
calibration, validation and final-test phases disjoint, including each phase's
history runway. All methods and n values share origins and future windows.
Nonoverlapping rolling outcome windows are supported, with retained selection
information counted. Final dates remain null, and the CLI rejects non-development
execution. A 28-day horizon is a proposed whole-week starting point, not a final
operational choice. Four minimal 224+28-day phases fit in 1941 days; that does not
justify a particular seasonal allocation or prove sufficient statistical power.

Owner decisions before M4/final freeze:

1. Approve phase boundaries, origins, horizon and seasonality/regime coverage;
   no outcome-driven cutoff selection. Decide whether strictly separate contexts
   or an explicitly accounted alternative best answers the research question.
2. Approve cohort eligibility, candidate sampling, and shared study-development
   information. The retrospective M5 roster and positive-history screen cannot
   prove ex-ante assortment availability or eliminate survivor/selection bias.
3. Define within-n fitting/calibration/tuning allocation and how shared earlier
   development influences model/hyperparameter selection. Equal per-series n does
   not erase cross-series pretraining or shared tuning history.
4. Approve the observed-sales-replay estimand, censoring/misspecification
   sensitivity, and stationary versus evolving demand assumptions. No true
   inventory performance can be inferred from M5 sales alone.
5. Declare feature release timing; retain deterministic calendar-only defaults
   until prices/promotions/events have defensible availability assumptions.
6. Specify common scenario initial stock/pipeline, costs, horizon/terminal
   sensitivities, matched compute allowances, baseline roster and non-inferiority
   margins, with dependence-aware uncertainty analysis. Preserve accepted M1/M2
   mechanics unless a separate change is explicitly justified and approved.
7. Complete source usage/redistribution review. Favorita remains unavailable and
   unexamined; freeze method and adaptation rules before authorized acquisition.
   Returns/fractional units/omitted rows need decisions before M1 compatibility.

Engineering limitations: Python interfaces protect against accidental leakage,
not deliberately opening arbitrary files. Information manifests validate declared
access and supplied views; they cannot prove undocumented pretraining lineage or
police all future fitting code. `assert_comparable` is deliberately conservative
and checks exact declarations, not realized computational fairness. Scientific
freeze approvals are procedural. The full sales matrix and all price values were
not semantically audited. No final holdout, empirical cost advantage, GP
calibration, RL convergence, new theorem, novel mechanism, or EJOR readiness was
validated. Independent review of this implementation is still required.

Recommended next task: **review M3 and approve a concrete information/evaluation
contract**, then separately authorize a small M4 baseline implementation using the
same dispatcher/ledger. Do not begin training on the strength of this report.

Proposed commit message (not executed):
`Implement M3 leakage-safe M5 preparation and information-budget contracts`.


## Independent-review correction — 2026-10-18

This appended section supersedes the earlier test counts and learner-identity
contract. Earlier evidence above is retained as history. Source remains base
`14d0741ea2328aa28cef7612976357c4b3cb6d53` plus an uncommitted diff on
`feat/m3-data-information-protocol`; scientific acceptance remains pending.

### Reproduced defect and correction

Independent review correctly identified a noninterference defect: `history.dataset`
was a SHA256 identity of all raw inputs, including withheld outcomes. Changing only
miniature-fixture day 226 while training ends at day 224 left observations and
normalization unchanged but altered every serialized learner artifact. This
violated the complete learner-information boundary even though the hash was not
an ordinary demand predictor. Comparing only history values was insufficient.
The new single-cell intervention reproduced changes in all 12 learner files before
the fix. The initial adversarial test also had a tuple/list comparison mismatch
in its evaluator assertion; that assertion was corrected to compare serialized
bytes, without relaxing the learner-byte equality requirement.

Preparation now requires a **predeclared logical dataset version**, fixed
independently of withheld outcomes. The demonstration uses
`m5-accuracy-zenodo-10203108-v1`; independent fixtures use
`miniature-m5-fixture-v1`. The full raw-source fingerprint remains the trusted
manifest's `dataset`; `learner_dataset_version` separately identifies the learner
namespace. Manifest schema 2 preserves all raw SHA256/size input checks and artifact
checksums, and adds an explicit study-information union. Trusted dispatch must
verify this mapping and artifact pins before supplying a learner file. Full-source
hashes, aggregate outcomes and preparation/audit metadata are not learner inputs.
The audit recomputes the trusted identity and checks the version/config binding.

`load_learner` retains strict artifact checksum, dataset version, series, origin,
budget, schema, date and training-only normalization validation. Deterministic
weekday/month values and their availability/evidence are now recomputed and
validated, rejecting a future marker disguised as a calendar feature even if the
caller supplies a matching checksum for the modified file. No full raw checksum
is accepted as the declared logical version when a dispatcher pins the correct
version. The configuration validator rejects missing/malformed version labels.
Old schema-1 bundles remain unchanged; the audit can inspect them but does not
certify the new study ledger for them. Use fresh schema-2 preparations for corrected
learner access.

The independent miniature test changes exactly one sales cell, d_226 from 999999
to 777777, and checks unchanged bytes for the other four source files. With matching
updated trusted provenance, all 12 learner files, names/checksums, cohort bytes
and training-only statistics are identical. The evaluator changes exactly that
sales cell and trusted fingerprints change; using the old input manifest rejects
the modified source. Additional tampering tests reject wrong logical version,
series/origin/budget/checksum, added raw-source metadata, undeclared predictor names,
future-derived calendar values/evidence and modified normalization.

### Study-wide information accounting

The demonstration exposes five selected 224-day histories = **1,120 distinct
historical sales cells**. Screening reads eight candidates over 28 days = 224
cells; five selected candidates contribute 140 already counted cells. The three
excluded candidates contribute **84 additional cells**. The study-wide union is
therefore **1,120 + 224 - 140 = 1,204**, not 1,120 and not 1,344. It is not the sum
of all nested learner budgets or repeated access. The new trusted study ledger
records the windows, count decomposition and per-series union; independent CSV
and artifact audit verifies the decomposition and union. Tests also check repeated
budget declarations, exclusions and overlapping rolling histories.

Individual learner budgets remain exactly 28/56/112/224 observations. Shared
study-design information must be disclosed in comparisons; it cannot be credited
as an isolated 28-observation study. The 140 development evaluator cells are
separate from the historical union; any future outcome-guided development would
need explicit accounting and cannot consume final-test data. Existing ledgers
continue to distinguish pooling, pretraining, tuning/calibration, normalization,
initialization, demand-model fitting and synthetic transitions. No training was run.

**The item/store roster comes from ex-post M5 metadata and can introduce
selection/survivorship bias.** Metadata access is disclosed separately from sales
cell counts; historical-only screening does not establish ex-ante assortment
availability or eliminate that bias. Zero sales remain observed sales, not inferred
stockouts, demand or measured inventory costs.

### Correction file inventory

Modified relative to the pre-review M3 worktree:

- `src/inventory_ejor/data/preparation.py`: logical version contract, trusted source
  separation, schema-2 preparation/study manifest.
- `src/inventory_ejor/data/budgets.py`: deduplicated study-wide historical union.
- `src/inventory_ejor/data/views.py`: deterministic feature-value/evidence guards.
- `scripts/audit_m3.py`: independent schema-2 source/version/study-count audit.
- `experiments/configs/m3_development_demo.json`, `tests/m3_fixtures.py`: explicit
  logical versions for real release and miniature fixture, respectively.
- `tests/test_m3_data.py`: complete-artifact comparison and two audit-tampering tests.
- `data/M3_PIPELINE.md`, `experiments/protocol/EVALUATION.md`: corrected consumer
  contract, study totals and trust-boundary limitations.
- `docs/STATUS.md`, `docs/TASKS.md`, `docs/DECISION_LOG.md`, `docs/SESSION_LOG.md`:
  current implementation evidence and unchanged scientific acceptance gate.
- This report: append-only correction, preserving its prior complete contents.

New files: `tests/test_m3_noninterference.py` (six independent/adversarial tests)
and `results/summaries/m3_correction_verification_20261018.json` (aggregate evidence).
The full M3 inventory is the earlier 23-file list plus these two files. No M1/M2
implementation, regression fixture, source acquisition manifest or previous
verification summary was changed.

### Executed correction validation

Existing baseline before correction: **111 tests passed in 1.492 s**. Final checks:

| Check | Executed result |
|---|---|
| Full suite | **119 passed**, 1.954 s |
| M3 suite | **53 passed**, 1.250 s |
| Independent noninterference/accounting module | **6 passed**, 0.296 s; included in both counts above |
| M3 Ruff E,F,I,B,UP | Pass |
| M3 formatting | Pass; 14 Python files already formatted |
| Project check | Pass; 16 bibliography entries / 16 citation keys |
| M1 regression | Complete output unchanged; total cost 47 |
| M2 regression | Complete output unchanged excluding source provenance; DP/horizon-aware 2.875, naive 3.000 |
| Repository-wide Ruff | **Not passing:** 54 pre-existing findings in 12 byte-unchanged files |
| Repository-wide formatting | **Not passing:** 13 byte-unchanged files would be reformatted |
| Corrected M5 demonstration | Pass; 8.223844169 s, peak RSS 55,044 KiB, CPU only |
| Independent original-CSV audit | Pass; five raw identities, 20 learner views, 1,204 historical union verified |

All commands ran with the existing Python 3.10.12 environment under a 120-second
outer timeout. Each test command also had a 110-second subprocess timeout. No
package was installed or upgraded. Exact commands from repository `github/`:

```bash
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -v
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -p 'test_m3*.py' -v
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -p test_m3_noninterference.py -v
timeout 120s ../code/.venv/bin/python -m ruff check --select E,F,I,B,UP src/inventory_ejor/data scripts/prepare_m3.py scripts/audit_m3.py tests/test_m3_data.py tests/test_m3_noninterference.py tests/m3_fixtures.py
timeout 120s ../code/.venv/bin/python -m ruff format --check src/inventory_ejor/data scripts/prepare_m3.py scripts/audit_m3.py tests/test_m3_data.py tests/test_m3_noninterference.py tests/m3_fixtures.py data/M3_PIPELINE.md
timeout 120s ../code/.venv/bin/python scripts/check_project.py
timeout 120s ../code/.venv/bin/python scripts/run_m1_reference.py
timeout 120s ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
timeout 120s ../code/.venv/bin/python -m ruff check --select E,F,I,B,UP . --output-format concise
timeout 120s ../code/.venv/bin/python -m ruff format --check .
```

Fresh end-to-end preparation command (authorized bounded development demonstration):

```bash
timeout 120s ../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/m3_development_demo.json --seed 0 --timeout 110 --allow-dirty -- ../code/.venv/bin/python scripts/prepare_m3.py --config experiments/configs/m3_development_demo.json --seed 0
```

It created fresh `data/processed/m3-demo-_zw6b5hj`, with wrapper evidence at
`results/runs/20261018T075246Z-smoke-9b4d055b`. The child consumed config and seed;
all five raw inputs retained their hashes. Eight candidates yielded five retained
and three excluded series; 20 learner files and five outcome trajectories.
The selected histories still contain 988 zero cells out of 1,120. No additional
price audit was run for this correction; the earlier 406 missing-price findings
remain historical evidence, with no imputation or learner price access.

```bash
timeout 120s ../code/.venv/bin/python scripts/audit_m3.py --directory data/processed/m3-demo-_zw6b5hj --preservation-snapshot results/runs/m3-correction-m7x4j4x1/preservation-before.json
```

That audit verified all **134 pre-existing snapshot files before this report was
appended**. Final preservation checks verify **133 byte-identical files**, including
all snapshotted raw inputs, prior processed bundles, previous experiment runs and
discovered backups; the sole intentional update is this report. Its original bytes
remain an exact prefix and a before-image copy exists in the local audit archive.
The snapshot includes the three files of `code/backups/m2-codex-before-pr7-20261018`.
This is a statement about inspected paths, not a machine-wide backup certification.
No checkpoints were deleted or rewritten. All Git refs, including local main and
the preserved launcher branch, remain unchanged; nothing is staged. Raw/processed
files and runs remain ignored and absent from tracked files, except tracked
`.gitkeep` placeholders. Exact status, source hashes and preservation evidence are
in the fresh aggregate verification JSON.

Local logs and exact command arrays are in `results/runs/m3-correction-m7x4j4x1`.
The new complete M3 patch includes tracked and untracked review files; the separate
correction patch compares against the captured pre-review worktree. Neither patch
contains restricted data. Prior patches and audit logs remain intact.

### Limits and review gate

Logical version labels provide stable names, **not content authentication**; source
and artifact checksums still provide integrity in the trusted dispatcher. Label
assignment must be governed independently of withheld outcomes. A regex cannot
prove that an arbitrary user-chosen label or claimed release date was chosen
without looking ahead. Likewise, the common Python interface is not a sandbox
against arbitrary raw-file access. Trusted provenance must not be forwarded to a
learner or used as a feature, seed or tuning signal. Custom externally authorized
features still require defensible availability declarations; deterministic feature
checks do not establish historical release timing for prices/promotions/events.

The byte-intervention test verifies this implementation for unchanged metadata and
history with altered future sales. It does not prove censoring assumptions,
statistical validity, ex-ante cohort availability, or absence of undocumented
pretraining. A corrected real-data bundle was prepared and audited once; no second
corrected real-data repeat run was performed. Deterministic fixture checks and the
prior two-run evidence are separately reported, not relabeled as new replication.

All seven scientific decision groups listed earlier remain open: phase/origin/
horizon and seasonal coverage; cohort/shared development allowance; within-budget
fitting/tuning/calibration and pooling; sales-replay estimand/censoring; covariate
release timing; scenario initialization/costs/compute/inference; and Favorita
access/transformations after freezing the method. Final dates remain null. This
correction does not change accepted M1/M2 mechanics or invent inventory costs,
latent demand, model-selection evidence or manuscript results.

Next task: independent review of the complete corrected M3 diff and approval of
its scientific information/evaluation contract. **Stop before M4 or GP/RL training.**
Proposed commit message, not executed:
`Implement M3 leakage-safe data preparation with noninterfering learner artifacts`.
