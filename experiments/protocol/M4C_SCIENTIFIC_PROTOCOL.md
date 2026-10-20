# M4c scientific protocol proposal — metadata and synthetic validation only

Status: **CANDIDATE PENDING OWNER APPROVAL; NOT A FROZEN PUBLICATION DESIGN.**
Prepared against reviewed M4b main `bea7dcb5ad82c457e81f75b6965179d725acae45`.
This document authorizes no M5 observation reads, model fitting, baseline jobs,
final scoring, downloads, or changes to original M4 evidence. Geometry checks and
synthetic tests establish software properties only. Unresolved decisions remain
explicit; omitted statistical parameters must not become implementation defaults.

## 1. Scientific object and limits

Study one-item periodic-review lost-sales control with known positive fixed lead
time, known stock-flow dynamics, an order cap, and limited initial observations.
Observed M5 sales are hypothetical exogenous requests in a controlled simulator.
They do not identify latent demand, actual stockouts, true supplier lead times, or
retailer financial savings. Zero recorded sales are not certified zero demand.
A GP posterior is neither automatic predictive calibration nor a policy-safety
certificate. Epistemic, demand-noise, simulation, and optimization uncertainty
must remain distinct. Policy selection must be included in any coverage claim.
The observed d_225 pilot remains development permanently. Its 192 tasks must not
be rerun or promoted into an independent validation experiment. Its cohort and
shared screening accesses remain part of the study's historical information.
All M5 results are public-benchmark evidence, including d_1914..d_1941; none of
these proposed windows is a cryptographically blind or unpublished benchmark.

## 2. Chronological geometry: constraints and capacity

Use half-open M5 indices; day 1 is 2011-01-29. Dates below use deterministic
`date(2011,1,29) + timedelta(days=day-1)` arithmetic, without reading sales.
The observed sales extent is [1,1942), ending at d_1941 on 2016-05-22.
Proposed history budgets remain 28/56/112/224 and outcome horizon T=28.
For each origin o, H_n=[o-n,o), E_o=[o,o+T), and its full runway is
B_o=[o-224,o+28). Require B_o wholly within its assigned phase.
For nonadaptive origins o_i<o_j, require H_224(o_j) intersect E(o_i) to be empty.
For fixed history/horizon this implies adjacent origin spacing of at least 252
periods. Outcome nonoverlap alone, spacing of 28 days, is insufficient.
A phase of length L can therefore accommodate at most floor(L/252) full blocks.
The 1,941 observed days fit seven such blocks with 177 days left over.
Three development + one calibration + one validation blocks leave capacity for
only two final blocks. A third final block requires a different allocation.
No calculation here establishes statistical independence, power, or suitability
of 28-day scoring. Additional real warm-up observations would change this geometry.

## 3. Alternatives: all feasible, none scientifically frozen

**A — retain the reviewed M4b candidate as the engineering proposal.**

| Phase | Half-open range | Origins | Calendar span, stop exclusive |
|---|---|---|---|
| Development | [1,757) | 225,477,729 | 2011-01-29 to 2013-02-23 |
| Calibration | [757,1009) | 981 | 2013-02-23 to 2013-11-02 |
| Validation | [1009,1261) | 1233 | 2013-11-02 to 2014-07-12 |
| Final | [1261,1942) | 1485,1914 | 2014-07-12 to 2016-05-23 |

Its final runways are [1261,1513) and [1690,1942), separated by 177 days.
Final outcome windows are 2015-02-21 to 2015-03-21 and 2016-04-25 to
2016-05-23, both stop exclusive. This retains two prospective development
origins beyond the already inspected 225 and two separated final contexts.
It offers only two final calendar contexts; a larger SKU count does not repair
that temporal limitation. The final gap remains reserved, not free tuning data.

**B — earlier final pair, with the same phase allocation as A.**
Use final origins 1485 and 1737; their runways [1261,1513) and [1513,1765)
are contiguous and satisfy the embargo. The second outcome window is
2015-10-31 to 2015-11-28, stop exclusive. This leaves the latest 177 days
unscored and avoids relying on the competition's last-28-day boundary, while
remaining a public M5 benchmark. It adds no independent calendar context over A.
There is no outcome-free evidence here establishing A or B as more informative.

**C — replication-priority alternative with one fewer development block.**

| Phase | Half-open range | Origins | Calendar span, stop exclusive |
|---|---|---|---|
| Development | [1,505) | 225,477 | 2011-01-29 to 2012-06-16 |
| Calibration | [505,757) | 729 | 2012-06-16 to 2013-02-23 |
| Validation | [757,1009) | 981 | 2013-02-23 to 2013-11-02 |
| Final | [1009,1942) | 1233,1485,1914 | 2013-11-02 to 2016-05-23 |

Final runways are [1009,1261), [1261,1513), and [1690,1942).
The added final outcome window is 2014-06-14 to 2014-07-12, stop exclusive.
This trades one prospective development origin for a third final context;
three contexts still do not justify generic temporal-cluster asymptotics.
Changing previously proposed roles is permissible only if those data remain
unopened; a documented exposure inventory must precede any freeze.
Recommendation: retain **A as CANDIDATE PENDING OWNER APPROVAL**, record B/C
as explicit alternatives, and decide using scientific priorities and a power
strategy rather than observed performance. Candidate geometry is not permission
to prepare its learner or evaluator artifacts.

## 4. Access order differs from calendar order

Physical phase dates follow the existing ordered SplitPlan roles. Logical access
must instead follow: DEVELOPMENT -> VALIDATION -> SELECTION LOCK -> CALIBRATION
-> CALIBRATION LOCK -> FINAL. Earlier calibration dates can remain sealed until
after later validation is examined; the calendar position does not imply access.
A proposed state machine is:

1. DRAFT: inspect metadata and synthetic fixtures; all new sales remain closed.
2. DESIGN AUTHORIZED: owner records exact geometry, cohort, budgets and scope;
   geometry validation alone cannot produce this state or grant data access.
3. DEVELOPMENT: use only separately authorized development observations and
   experiments. Record every architecture, tuning, normalization and feature use.
4. VALIDATION: evaluate only the declared candidate family and selection rule;
   calibration observations/outcomes and all final data remain inaccessible.
5. SELECTION LOCK: bind selected candidate, baseline, feature rules, history and
   compute budgets, seed ensemble, code/config hashes, and calibration procedure.
6. CALIBRATION: open the separately authorized calibration data only after that
   lock. Apply the prespecified calibration rule without changing the candidate.
7. CALIBRATION LOCK: bind thresholds and the prespecified fallback/stop decision.
8. FINAL AUTHORIZED: score the frozen procedure on separately authorized final
   windows; no feedback-driven method, seed, cohort or scenario changes.

A failed calibration triggers the declared baseline fallback or a stop. Retuning
would consume that calibration set and requires a newly justified design, not
silent reuse of its previous status. A valid simultaneous or selection-aware
calibration construction is an alternative only when precisely specified before
access. Sealing and access order alone do not imply exchangeability, coverage,
or transfer across seasonal/regime shifts. No such guarantee is established.

The lock binds a learning/decision **procedure**, not fitted weights requiring
unseen final histories. Prescribed within-n fitting after a history release is
permitted; selecting new features, hyperparameters or decision rules from
calibration/final feedback is not. Calibration therefore concerns the specified
procedure across histories under stated assumptions, not automatic coverage for
an identical already-fitted final-item policy. Record prerequisites alone are
not an append-only access journal or proof of an opaque artifact's contents.

## 5. Cohort and information accounting

Preferred new-cohort proposal: **metadata-only candidate selection, no sales
activity screen**, pending owner approval. Fix candidate count, seed, ranking
rule, identity normalization and any store/category strata before sales access.
Hash-ranked item-store IDs may come from the known ex-post M5 catalog. This
catalog is not a reconstructed historical assortment; survivor/assortment bias
remains. Publish selection/exclusion rules and counts as aggregate metadata.
Include all valid candidate histories, including all-zero histories. Do not
replace dormant, difficult, failed, or poor-performing cases after outcomes.
The required candidate count, seed and allocation are not set by this document.
Previously screened M4 membership is exposed shared design information, not a
new metadata-only sample. Reusing it requires that disclosure.
An alternative historical positive-sales screen needs explicit owner acceptance,
origin-local dates inside the shortest n=28 history, all candidate screening
counts, and a target population conditional on that activity rule. Do not choose
an earlier cohort by intersecting memberships selected using later histories.
For varying origin cohorts, define the estimand's origin weights and denominators
before access; maintain identical cases across methods/budgets at each origin.

Each learner receives exactly n consecutive own-series observations ending at o,
training-only transformations, and explicitly allowed deterministic calendar
features. No longer-budget normalization may enter the short-budget learner.
Disclose shared development/validation/calibration access separately from this
per-learner n. The procedure is development-assisted, not an isolated n-observation
algorithm. Shared development is not untracked cross-item parameter pooling.
Pooling and pretraining remain refused until their complete lineage, budget
semantics, artifact bindings and authorization are separately implemented.
Count unique historical cells by dataset/series/day union, with per-purpose
counts and metadata access separately disclosed. Reusing an observation does
not create data; synthetic transitions, repeated seeds and cost scenarios do not
create new real observations. Warm-up and initialization uses also need ledgers.

## 6. Enforce the proposal before a future preparation path can read data

Validate all phase windows, origins, budgets, horizon and embargo centrally.
Call both SplitPlan validation and the nonadaptive history embargo; derive the
largest history from declared budgets, rather than an independently supplied
smaller number. Bind forbidden final outcomes to every learner-access purpose,
including fitting, normalization, screening, tuning, calibration and pretraining.
Reject malformed types, duplicate/unsorted origins, phase crossing and any
outcome-to-later-history intersection, including exact boundary counterexamples.
The existing M3 preparer is development-demo-only and performs first-origin
sales screening. Passing a generic geometry validator must not enable it to
open proposed calibration/validation/final data or silently change cohort rules.
An M4c metadata/synthetic plan compiler must not call sales loaders or fit models.
Require explicit future preparation scope plus pinned source/config/approval
identities; proposal flags and passing tests are not scientific approval.
Exercise all access stages with synthetic ledgers and spies that fail if a
forbidden source is opened. Preserve original raw, processed and run artifacts.

Implemented paths and limitations are specified in `docs/M4C_ACCESS_FIREWALL.md`.
`experiments/configs/m4c_protocol_candidate.json` encodes A with candidate cohort
count 32/seed 0 and the pinned existing metadata frame; these values remain
PENDING OWNER APPROVAL. Supported preparation checks are implemented, while
scientific approval, staged experiment execution, actual model-artifact binding
at scoring and an operational access journal remain distinct future gates.

## 7. Estimands and reporting: choose the target before selecting a test

Let G(s,o,n,r,theta)=C_baseline-C_candidate for matched series, origin, history,
seed and operational scenario; positive G favors the candidate. C is the sum of
specified holding, lost-request and ordering costs over the fixed horizon.
For a fixed primary history n, a candidate benchmark estimand/estimator is:

`mu_hat_n = sum_theta w_theta * sum_o w_o * (1/|S_o|) * sum_s_in_S_o mean_r G`.

Here S_o is the prospectively defined common cohort at origin o; nonnegative
scenario/origin weights sum to one within each dimension. Freeze these weights,
the primary n, baseline and policy-selection rule before reserved outcomes.
Average algorithm seeds within each real series/origin before treating that
series/origin as a repeated measure. Best-seed selection on final costs is banned.
Choose the strongest eligible baseline using the declared development/validation
rule, never the final sample minimum. Publish every prespecified comparator.
A fixed public benchmark supports a conditional descriptive score. Extending it
to an expectation over new item-stores or future periods requires a declared
sampling population and justified dependence assumptions; bootstrap output alone
does not create that target. Equal-series gain, pooled cost ratios, equal-series
relative gains, and pooled fulfilled/requested service are distinct estimands.
Predeclare zero-denominator rules; publish absolute harm as well as relative gain.
Report each n separately as a cost-data curve. Averaging all four n values is an
artificial budget mixture unless its weights have a stated scientific meaning.

## 8. Dependence, power and non-inferiority remain explicit gates

Repeated budgets, scenarios and seeds share observations. Series may share stores,
categories/geography and calendar shocks; paired differences may reduce, but do
not automatically eliminate, those dependencies. More SKUs in the same stores do
not create more independent stores. Two or three final origins are few time units.
Plan store/item and temporal dependence sensitivity; do not call item-store-only
clustering sufficient without an argument. Report per-origin and store-level
results even when a justified confirmatory interval is unavailable.
For weighted repeated units i, `Var(sum_i w_i G_i)=sum_i sum_j w_i w_j Cov(G_i,G_j)`.
Dropping off-diagonal covariance or using the 48 pilot budget pairs as independent
units is unjustified. Training seeds measure algorithm repeatability separately.
Under a specifically justified independent-cluster normal planning approximation,
`K >= ((z_(1-alpha)+z_(1-beta))*sigma_G/delta)^2` is only a symbolic starting point.
Alpha, target power, meaningful effect delta, cluster variance sigma_G, cluster
counts and dependence parameters are unresolved; this formula supplies none.
Use an authorized development variance assessment and/or explicitly assumed
synthetic dependence/effect grids, with sensitivity to strong common shocks.
Label simulated power as conditional on those assumptions; no adequate sample
size, actual power or confidence coverage has been established by M4c.
A synthetic coverage study needs independent histories and evaluation paths;
repeat optimization seeds within a path are not independent coverage trials.

Short-history sufficiency is a separate non-inferiority question. Define
`D=C_short-C_rich` for the same frozen procedure/comparable compute, and margin
M>0 in justified operational/scenario units. H0: E[D]>=M; claim non-inferiority
only if a valid prespecified one-sided upper bound lies below M. No margin is
inferred from the observed 4.11% pilot result or selected after final costs.
Primary gain versus a strong same-n baseline does not itself establish this
claim. Control multiple budgets/comparators/scenarios through a declared primary
contrast and a justified secondary/multiplicity plan. Recency, GP feature scale
and Monte Carlo randomness must be separated from an isolated sample-size claim.

## 9. Owner decision record and next gate

| Decision | Current proposal | Status before any reserved access |
|---|---|---|
| Chronology | A; B/C documented alternatives | Pending owner approval |
| Calibration access | Validation/selection lock before unsealing calibration | Pending binding workflow |
| Cohort | Metadata-only, no sales screen preferred | Pending count/seed/strata approval |
| Information track | Own n plus disclosed shared development | Pending precise shared-access inventory |
| Primary n/baseline/weights | Formula above; values not chosen here | Pending scientific choice |
| Initial stock/pipeline | Common rule; zero/warm-start sensitivity needed | Pending scenario/ledger choice |
| Costs, lead time, terminal value | Pilot values are historical, not final defaults | Pending operational justification |
| Compute/seed ensemble | Native and matched-compute tracks; coupled streams where valid | Pending actual allowances |
| Inference/power | Dependence-aware plan; symbolic quantities only | Pending population/assumptions/design |
| Non-inferiority | Separate margin and one-sided design | Pending external margin justification |
| Coverage/novelty | Selection-valid mechanism and prior-art comparison unproved | Open research gate |
| Final/Favorita execution | No access or jobs authorized by this proposal | Separate explicit future scope |

Freeze only a concrete reviewed design, with a dated exposure inventory, exact
configuration and code hashes, documented owner decisions and separate execution
scope. Until those exist, software should continue to report PROPOSAL/NOT FROZEN.
