# M3 chronological evaluation and information protocol

Status: implemented engineering contracts; **proposed scientific protocol, pending
owner review**. M3 authorizes bounded preparation only. No final holdout is frozen,
no GP/RL fitting or inventory-cost experiment has run, and no retailer benefit is
claimed. M1/M2 semantics remain unchanged at base commit `14d0741`.

## Estimands and evidence

Tracks remain (A) known-law synthetic demand with M2 references on small cases,
(B) M5 observed-sales-driven simulation, (C) original item-level 2017 Favorita as
frozen external validation. Prediction error and simulated inventory decision
cost are distinct endpoints. Neither is evidence of observed retailer cost
improvement. M5 does not provide on-hand inventory, lost sales, procurement costs,
or uncensored demand. Zero observed sales do not identify zero latent demand or a
stockout. Positive sales establish historical transactions, not continuous stock
availability. No demand reconstruction, clipping, rounding, or zero imputation
is performed. Missing/invalid selected cells cause a failure, not a replacement
item chosen after examining outcomes.

Epistemic demand-model uncertainty, intrinsic demand randomness, Monte Carlo
error, and optimization error must remain separately labeled in M4+. Synthetic
observations do not increase the number of real observations. Later GP intervals
will require calibration evidence; no distribution-free coverage is implied.

## Source chronology and overlap

The authoritative local source is the five files identified by
`data/manifests/m5_verified_20261017.json`. M3 verifies their sizes/SHA256 before
and after preparation, and retains the original manifest identity. The organizer's
[Zenodo record](https://zenodo.org/records/10203108) supplies public file identities;
its publication/version listing is not a license to redistribute restricted data.
The [organizer repository](https://github.com/Mcompetitions/M5-methods) describes
separate validation/evaluation phases. Calendar/header observations below were
measured from the verified local inputs, not guessed from file names.

| Source | Observed sales columns | Local calendar dates |
|---|---|---|
| sales_train_validation.csv | d_1 through d_1913 | 2011-01-29 through 2016-04-24 |
| sales_train_evaluation.csv | d_1 through d_1941 | 2011-01-29 through 2016-05-22 |
| calendar.csv | d_1 through d_1969 | 2011-01-29 through 2016-06-19 |

The added d_1914..d_1941 window is 2016-04-25..2016-05-22. Calendar days
1942..1969 have no outcomes in either supplied training CSV. The submission
file contains forecast slots, not observations. Never concatenate the two sales
files. Use evaluation CSV as the single canonical source, stripping the suffix
only through validated item/store identity. Compare shared **requested historical
cells** against validation CSV; do not inspect later sales to certify an earlier
training task. The manifest states the exact overlap checked; this is not a full
cell-by-cell overlap audit.

CSV streaming necessarily reads raw row bytes, including unrequested columns.
Only requested cells are interpreted as sales; future cells are not supplied to
normalization, cohort screening, or learners. Byte hashing all files is provenance
work, not model access. Hashes and identifiers must never become predictors.

## Proposed chronological design — no final dates selected

Use ordered, disjoint development, calibration, validation, and final-test phases.
The conservative default gives **each phase its own history runway** as well as
its own outcome windows. In half-open day notation, phase P=[a,b), origin o,
history H_n=[o-n,o), and outcomes E=[o,o+T). Require
[o-224,o+T) contained in P. This avoids borrowing earlier phase outcomes as
context for a supposedly untouched later phase. Four phases each containing one
224-day runway and 28-day evaluation require 1008 days, within M5's 1941-day
coverage; this arithmetic establishes feasibility, not optimal phase allocation.

A 28-day evaluation horizon is a proposed starting point: whole weeks align with
the planned 28/56/112/224 history grid and permit controlled horizon comparisons.
It is not established as an appropriate operational horizon for every lead time.
Before freezing, the owner should select phase dates and origin spacing based on
seasonality, regime changes, available periods, lead times, costs and statistical
power, **without examining candidate final outcomes**. The original competition
last-28-day boundary is a reference, not an automatic final test for this study.
`experiments/configs/m3_protocol_proposal.json` records unresolved dates as null.

Within an origin, every method and budget receives the same item/store cohort,
origin, future dates, costs, inventory initial state, and terminal treatment.
Histories are nested and end at the same exclusive cutoff. `SplitPlan` rejects
phase crossing, duplicate/out-of-order origins and overlapping outcome windows.
Multiple nonoverlapping origins are supported; they remain temporally and
cross-series dependent and are not independent replications. No random row split.

Development may inform architecture. Calibration outcomes may inform only declared
calibration choices. Validation outcomes may select declared hyperparameters and
policies. Final outcomes may only score the frozen procedure. All such earlier
real-data access must be declared even if it only affects a hyperparameter,
threshold or normalization constant. An entirely isolated n-observation method
must split fitting/calibration/tuning *inside* those n observations. Methods whose
architecture/hyperparameters were selected using other real observations need a
separate shared-development/pooled/rich-data declaration. Merely using identical
hyperparameters across methods does not erase their development information.

The M3 CLI executes only `development_demo`, not final evaluation. Generic split
utilities can express proposed later phases but do not authorize their inspection.
Freeze approvals are procedural decisions recorded by the owner; software cannot
infer them from a Boolean or from a passing test.

## Cohort and observation budgets

Candidate IDs are ranked by SHA256 of `seed:canonical_item_store` with lexical tie
breaking. Fix the candidate count and seed **before outcomes are read**. Within
those candidates, require at least one positive observed sale during the common
28-day history at the first origin (configurable; proposed, not scientifically
accepted). No failed candidate is replaced. The rule confirms pre-origin
transaction evidence and excludes some dormant/intermittent items; its effect on
generalizability must be reviewed. Do not try new seeds until the cohort looks
favorable. Metadata uses an ex-post M5 roster: active-history screening reduces
future-assortment issues but cannot establish a historically complete assortment
or eliminate dataset survivor bias.

A common 28-day screening window avoids making the 28-day method's cohort depend
on 224-day outcomes. Any earlier metadata/price-based eligibility would itself
require additional information accounting. Schema coverage is checked for every
requested history. An invalid longer history aborts preparation rather than
silently selecting a different cohort for that budget.

The local cohort manifest records candidates, inclusions, exclusions/reasons,
non-sampled IDs/reason, selection seed, screening dates, and total screening
observations across candidates. Shared cohort membership is design information,
not evidence that the complete study consumed only n real values. Each learner's
ledger counts its own eligibility window; other candidate screening is separately
disclosed and never pooled into its fit. Future studies need approval of this
shared-design allowance and should publish both per-learner and study-wide access.

For rolling origins with a fixed cohort, the first origin's screening window may
lie outside a later n-day history. The implementation retains/counts it and labels
that learner `rich_data`; it never silently claims fresh isolated n-day access.
Alternatives needing review are a new prospective cohort at each origin, or an
explicit shared cohort-information allowance. Inference must account for this
selection and the dependence between origins.

## Machine-readable information ledger

The ledger identifies logical dataset versions, series, half-open observation ranges,
origin, n, information track, and the following categories:

| Category | Required accounting |
|---|---|
| Per-series history | Exactly n consecutive real observations ending before origin |
| Cross-series pooling | Every additional series/source/window; label pooled |
| Pretraining | Pinned artifact SHA256 plus complete real-data lineage; label pretrained |
| Hyperparameter optimization | Accessed real windows and optimization trial count |
| Calibration/validation | Each accessed window, even if reused for tuning |
| Normalization | Actual fitting days; training-only mean/population SD |
| Demand-model fitting | Actual fitting window; zero in M3 because no model is fitted |
| Eligibility/initialization | Observations used to select series or infer initial quantities |
| Synthetic trajectories | Separate synthetic transition count, never real-data credit |
| Compute/features | Explicit CPU/memory/GPU allowance and permitted feature names |

Unique real observations are the union of (logical dataset version, series, day).
The trusted manifest binds each version to exact full-source fingerprints;
combining runs requires checking those bindings before unioning access identities.
Repeated use for several purposes does not create new data; per-purpose counts
still expose reuse. Within a category, overlapping duplicate declarations fail.
External datasets use their own date origin to prevent incomparable day indices
from hiding future data. Unquantified pretraining is rejected rather than
misrepresented as a measured 28-day budget. This M3 validator bounds an audit at
one million declared access cells and fails explicitly above that limit.

`validate_ledger` checks the actual supplied History and authorized source windows,
including forbidden final outcome intervals. `assert_comparable` is a conservative
exact-contract check for the same n; it rejects unequal declared real access,
features, synthetic/trial counts, pretrained artifacts or compute allowances.
`assert_same_evaluation` separately checks future windows. Different n values
form a cost–data curve, not an equal-information comparison. Known-model oracle
and rich-data methods must remain separately labeled. Matching declarations is
necessary, not sufficient: future model code must use the dispatcher and report
actual work/runtime, rather than bypassing the access ledger.

## Covariates, normalization, and initialization

Civil-calendar month and weekday are deterministic and available in advance.
The default excludes event names, SNAP and price features. M5's weekly prices and
calendar event columns do not provide publication timestamps for our decision
problem. The price loader offers retrospective item/store/week alignment with
unique-key validation and no forward/backward fill. A price feature additionally
requires an explicit release-day mapping and evidence/assumption string;
`features_at` rejects requested features released after the decision. Future
promotions/events require the same declaration and matched availability for every
method. No future price is used as a demand predictor by default.

Normalization fits only the declared training slice of a History. A held-out
calibration slice can be excluded using an explicit fitting Window and matching
ledger entry. Constant training data uses scale=1, recorded explicitly. The
consumer recomputes the training-only statistics to reject contaminated artifacts.
The 224-day view's statistics are never shared with the 28-day view.

M3 does not initialize inventory from sales. M4+ must specify an explicit common
scenario initial stock and pipeline, or a rule using only its declared history.
Warm-up observations and simulated warm-up transitions need separate accounting.
M1 receipt timing, L-1 initial pipeline, finite horizon, placement costs and zero
additional terminal value remain unchanged. A proposed alternate boundary
convention requires its own decision, not a data-preprocessing shortcut.

## Artifact boundary and reproducibility

A trusted preparation process reads local raw data, creates one immutable learner
artifact per series/origin/n, and writes evaluator outcomes separately. The
`load_learner` API receives one pinned file plus expected dataset/series/origin/n;
it returns history, training-only normalization, and allowed features. It has no
reader or evaluator reference. This prevents accidental broad access; Python and
the filesystem are not a security sandbox against deliberately bypassing code.
Never hand a learner the full cohort/evaluator manifest as predictive input.

Each fresh ignored `data/processed/m3-demo-*` directory contains learner files,
`evaluation.json`, `cohort.json`, and `manifest.json`. The manifest records source
hashes, config, seed, splits/dates, information ledgers, transformation rules,
code revision plus dirty source hashes, environment, resource limits, artifact
fingerprints, and exclusions. Files use exclusive creation; outputs are never
reused. A stable artifact hash excludes runtime/path metadata. The wrapper writes
its own fresh ignored `results/runs/*` provenance. Only aggregate reports/public
source metadata are reviewable tracked artifacts. No raw or processed data uploads.

The CLI uses standard-library streaming, at most 32 candidates, 40,000 catalog
series, 3,000 days and four origins; address space is capped at 512 MiB and CPU time
at 110 s on Linux. Readers have cooperative <=110 s elapsed checks. Run with an
external 120 s wall timeout as shown in `data/M3_PIPELINE.md`. CPU-only preparation
is not an inventory research run. No downloads, package changes or GPU activity.

## External validation and scientific acceptance gate

Favorita remains the **original item-level 2017** competition and is not acquired
or substituted. Freeze M5 method/protocol, budget rules, adaptation policy and
external analysis before authorized acquisition/inspection. Then validate the
source schema and prespecify handling of returns, fractional units, omitted
zero-sales rows, promotions and unobserved stock availability. Do not clip/round
or convert omitted rows to known-zero latent demand. If unit/observation semantics
cannot match M1, request a scientifically explicit scope/transformation decision.
Any Favorita-specific adaptation consumes declared adaptation data and requires a
separate untouched external holdout. Report failures rather than retuning on it.

Before M4/final freeze the owner must resolve: phase boundaries/origins/horizon;
cohort rule and study-wide development allowance; covariate release assumptions;
within-n fit/calibration allocation; stationary versus evolving demand; the
sales-replay estimand and censoring sensitivity; common initial state/costs and
horizon sensitivity; source usage terms; non-inferiority margins and dependent
uncertainty analysis; matched compute allowances and baseline roster. Primary
candidate endpoint remains simulated operating cost versus n, with holding,
shortage/ordering, fill rate, tails, harmful switches, runtime, forecast error and
calibration as separate diagnostics. No superiority, novelty, coverage or EJOR
readiness follows from M3 tests. Stop for independent review.

## M3 review correction: whole-artifact noninterference

The initial implementation put the entire raw-data SHA256 identity in
`History.dataset`. A future-only sales mutation therefore changed learner bytes
although its observations and normalization were unchanged. The previous tests
checked selected fields and missed this channel. The corrected configuration
requires a predeclared `dataset_version` (official demo:
`m5-accuracy-zenodo-10203108-v1`; miniature tests use a separate fixture version).
This version is a logical release label, not a digest calculated from outcomes.
It must be assigned before inspecting withheld outcomes and must not be renamed
in response to them. Syntax validation cannot enforce that procedural obligation.

Manifest schema 2 keeps the full content identity in trusted `dataset` and all
original hashes in `inputs`; `learner_dataset_version` explicitly binds the logical
version to those verified sources. Learner and evaluator objects use the logical
version. Each learner's checksum covers its complete allowed-content artifact and
remains strictly checked alongside dataset version, series, origin, budget and
normalization. Full-source hashes, input-manifest hashes and run metadata must
stay with the trusted dispatcher/auditor, outside learner files and features.
Default calendar features are recomputed by the consumer from civil dates; an
outcome encoded as a calendar value or evidence string is rejected. Arbitrary
externally authorized features still require their own availability evidence.

Changing only fixture day 226 with origin 225 now leaves every learner byte,
filename, artifact checksum, cohort and training statistic unchanged. The evaluator
cell and trusted raw-data fingerprints change. This is a controlled engineering
noninterference check, not a general proof against arbitrary file access.

The trusted `study_information` ledger records selected history windows, candidate
screening, their set intersection/union and per-series totals. For the demo:
1,120 selected historical cells + 224 candidate-screening cells - 140 shared
cells = **1,204 distinct historical sales cells**, including 84 additional cells
from excluded candidates. Repeated budgets and overlapping rolling histories do
not create additional observations. Evaluator outcomes and metadata access are
separate. The ex-post item/store roster warning remains explicit: selection and
survivorship bias are unresolved even when sales-cell counts are correct.

Prior schema-1 artifacts remain preserved historical evidence of the defect;
the auditor can inspect them but does not certify the new study ledger for them.
New preparations use schema 2 and fresh paths. No final dates or M4 authorization
follow from this correction.
