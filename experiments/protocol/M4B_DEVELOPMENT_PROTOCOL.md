# M4b development-evaluation protocol — planned, not executed

**Status 2026-10-19:** Design recommendation from an audited **single-origin M5
development pilot**. This document does not open, precompute, download, or
authorize scores on calibration, validation, final M5 windows, or Favorita.
The paper-level evaluation protocol and final non-inferiority margin are **not
yet scientifically frozen**. The original M4 run and its results remain
immutable; its historic settings are not retroactively retuned.

## 1. Research purpose and fixed inventory setting

Question: when do short, real observed-sales histories permit decision-relevant
inventory policy improvement, and can an inventory-specific assessment of
paired policy-cost uncertainty prevent model-exploitation failures?

Core setting remains the Project Charter: one item; periodic review;
nonnegative demand/request counts; lost sales; *known, strictly positive fixed
lead time*; fixed order cap; exact M1 stock flow. The intended new method may
use GP-informed, neural policy improvement but the published contribution must
be defined and shown distinct from existing GP + rollout, DCL, TED/HDPO and
ordinary robust-safe policy-improvement methods.

Separate these unresolved objects:

1. **Demand model accuracy and calibration:** distributional adequacy of the
   fitted predictive law, particularly zero days, peaks and shifted regimes.
2. **Inventory decision quality:** simulated holding/shortage/order cost,
   fill rate and preventable versus inherited unmet requests.
3. **Policy improvement uncertainty:** uncertainty of paired
   `J(π) - J(π_baseline)` under genuinely unknown demand, with model
   misspecification and adaptive policy-selection effects.
4. **Optimization/compute error:** sampling error and policy optimizer/training
   error; a high GPU budget must not masquerade as better data efficiency.

The 2026-10-18 pilot uses M5 *observed sales as simulation requests*.
Stockouts, uncensored latent demand and true retailer costs are unobserved.
All later empirical cost claims remain strictly **counterfactual under stated
stock/lead-time/cost/replay assumptions**, not real retailer savings.

## 2. Existing M4 development evidence and its limitations

The *already observed* development cohort was 32 metadata-ranked candidates,
12 historically eligible item-store series, origin `d_225` and evaluation
`[225,253)`, with budgets `n ∈ {28,56,112,224}` and seed 0. All four methods
share each series' single future path. The saved outputs live at
`results/runs/m4-approved-yc4xtrp1/`. The reusable audit is
`scripts/analyze_m4_results.py`; its source-of-truth facts are in
`results/summaries/M4_BASELINE_RESULTS_AUDIT.md`.

**Do not** call 48 (12 series × four nested budgets) independent experimental
units. The 12 item-store series are themselves correlated through locations,
product categories and the common calendar. Multiple optimization/MC seeds
assess algorithmic randomness; they do *not* provide new observed demand paths.

The pilot does not establish demand-model superiority, a GP guarantee,
non-inferiority of `n=28`, EJOR novelty or general-population performance.
Selection uses a common 28-day positive-sale eligibility screen, which excludes
some fully dormant histories, and metadata of a retrospectively known item
roster. Screening access (including excluded candidates) is study information.
M3 records **3,248 distinct historical sales cells** in this initial study:
2,688 selected-history cells plus **560 additional excluded-candidate
screening** cells; the historical access accounting cannot be advertised as
merely `n=28/56/112/224` for every design decision. Methods receive only
their declared learner observations, but cohort screening is shared design
information and must be reported separately.

## 3. Chronological access firewall (proposed geometry)

The original M5 source contains actual sales through `d_1941`.
Use **half-open** day intervals; require each phase's
`[origin - 224, origin + 28)` to lie wholly within that phase.
The earlier proposal allocated only 429 days to the final phase and could NOT
accommodate two disjoint 224-day-history-plus-28-day-evaluation blocks
(2×252=504 days). An independently reviewed **feasible illustrative**
layout, still **not frozen or authorized to inspect**, is:

| Phase | Proposed protected range | Illustrative origin(s) | Use |
|---|---|---|---|
| Development | `[1,757)` | Already inspected `225`; prospective `477,729` | Methods/debug/architecture, all accesses logged |
| Calibration | `[757,1009)` | `981` | Prespecified post-selection calibration only |
| Validation | `[1009,1261)` | `1233` | Declared model/hyperparameter selection |
| Final M5 test | `[1261,1942)` | `1485,1914` | Two disjoint 224+28 context/outcome blocks; only frozen evaluation |

**Calendar order is NOT access/release order in this provisional layout.**
Because the calibration outcomes `[757,1009)` are dated *before* the
validation outcomes `[1009,1261)`, they must remain **sealed** while
model/hyperparameter/policy selection uses development and the permitted
validation outcomes. **Only after** the entire candidate-selection
procedure and chosen policy are frozen may the separate calibration
outcomes be opened for a predeclared calibration-only procedure; they
must not be recycled for model ranking, architecture revision or
hyperparameter tuning. Final M5 outcomes remain sealed until both
selection and calibration are frozen. Calendar-time reversal may make
calibration less representative under drift; at the M4c design lock,
assess this risk with allowed metadata and consider a revised phase
geometry (and corresponding M3 role-order constraints) instead of
silently treating early calibration data as independent post-selection
coverage evidence. This access ordering **does not itself guarantee
selection-valid coverage**.

For the illustrative final origins, history+outcome blocks are
`[1261,1513)` and `[1690,1942)`. Neither later *history* may contain
an earlier final *outcome*, even if the two outcome windows do not overlap.
Because the 2016 M5 competition's final 28-day window is publicly known,
`d_1914..d_1941` cannot be described as a truly unseen/private benchmark.
This allocation is a **candidate geometry only**: calendar/seasonality,
cohort counts and sample-size adequacy need metadata-only review, then an
explicit prospective freeze before any new access.

The preliminary `d_225` observation window has **already been inspected**.
It must remain development forever. Do not silently promote it or another
data-exposed period into validation/final. In particular `d_1914..d_1941`
is public M5 competition data, not a cryptographically blind hidden test, so
a future disclosure must state its public-benchmark limitations.

The phase boundaries/origins in this table are **candidates requiring a
documented freeze before access**, not preapproved final scientific choices.
Confirm calendar/seasonality, eligible sample counts and power using *allowed
metadata only*. M3 `SplitPlan.validate_origins()` currently prevents only
**overlapping outcome windows**; it does not prevent a later history from
including a prior evaluation outcome. Use `SplitPlan.windows` **and** the
separate pure `validate_nonadaptive_origin_embargo()` helper, or an equivalent
explicit `forbidden_outcomes` check, before any final-plan preparation.
No final phase may reuse another final window's outcomes as learner history;
online adaptation is a separate research protocol and cannot be assumed.
The two candidate final origins are not proof of statistical independence.
**Never use all 1,941 days for both model development and final evaluation.**

For an eligible cohort, fix prospective metadata-only candidate selection and
positive-history screening rule before opening its outcome period. Log the
hash-ranked candidates, exclusions, screening data and any cross-series/pooled
access. Do not replace failed cases or select seeds based on observed results.
Reevaluate whether the current positive-sale criterion biases conclusions
about zero-heavy or dormant items, using development only.

## 4. Crossed baseline matrix: separate model and controller effects

Build this minimally complete **3 × 2** experiment first, before novel RL
training. Existing jobs are recorded, not overwritten or relabeled:

| Demand sampler | Horizon-aware base-stock | One-step rollout using same tuned continuation |
|---|---|---|
| Empirical iid | Existing | **Implement** |
| Gamma–Poisson | Existing | **Implement** |
| GP log1p-Gaussian surrogate | Existing | Existing |

Within each model, use identical per-series learner artifacts, fitted
parameters, sampled tuning paths, baseline grid and initial state; change only
the decision-time controller. Across models, keep the same real-data budget and
allowed prior/pretraining access. Preserve original results; new jobs get new
plan/config/versioned code identifiers.

Add a **recency-aware** simple model (e.g. window-weighted empirical rates,
prespecified decay), a **seasonal non-GP control** (e.g. weekday-stratified
empirical or count model with the same deterministic calendar), and a
**GP time-feature normalization ablation** using fixed calendar-day units
rather than division by `n-1`. Without a calendar-matched non-GP control,
GP versus iid samplers confounds uncertainty representation with known
weekday/time features. The GP scaling ablation is also critical:
changing `n` presently changes both data volume and the GP feature scale/
extrapolation geometry. Ensure each ablation is selected/tuned on development
data, never on its comparison outcome.

Then evaluate stronger comparators only after checking appropriate problem
and information equivalence: state-aware GP + finite-horizon planning/MPC,
DCL with GP or non-GP demand sampling, suitable generic safe policy
improvement, and faithful TED/HDPO reproductions if feasible. Label
incomparable or adapted methods as such; do not call current one-step
rollout an RL, global-MPC or DCL baseline.

## 5. Compute, fitting and uncertainty fairness

Each method receives exactly `n` consecutive permitted per-item
observations, unless a separately labeled **shared-development/pooled**
information track is used. Count and disclose screening, hyperparameter
selection, normalization, calibration, validation and all pretraining access.
Simulated transitions are *compute*, not real demand observations.

For controller comparisons, run at least two **distinct** experiment tracks:

- **Matched-information, native-compute:** expose each method's natural
  declared compute budget, logging GP fits, prediction draws, synthetic
  transitions, optimization trials, runtime, peak host/GPU memory and
  decisions per second. Interpret superior accuracy conditional on compute.
- **Matched-information, matched-compute:** use a prespecified transition,
  model-fit and search allowance (or a cost-performance frontier at multiple
  budgets). Set early-stopping/draw-reuse/trials equitably. Retuning a method
  must occur strictly on development windows.

Keep epistemic uncertainty, aleatoric demand variation, Monte Carlo path
error and optimizer error separate. GP log1p-Gaussian predictions are an
uncalibrated empirical-Bayes surrogate, not a count-likelihood or robust
coverage guarantee. Evaluate held-out development forecast diagnostics:
predictive mean bias, distribution/quantile scores, predicted zero-day mass,
positive-tail behavior and performance under demand shifts. Record failing
GP fits and loss trajectories; 75 optimizer steps without divergence are not
a convergence certificate.

Use common random numbers for *fair paired simulator comparisons* wherever
the source of randomness is under experimental control. If methods are
trained repeatedly, pin independent training seeds and matched evaluation
streams. **The original M4 effective optimizer seed hashes `series:origin:
budget:seed`**, so its nominal `seed=0` uses different MC streams between
history budgets; this further confounds a naive data-sufficiency comparison.
Future experiments should explicitly couple streams where valid, record
independent training/MC seeds and convergence diagnostics, and distinguish
fixed versus online-update GP controllers. The pilot GP **does not refit or
condition on newly observed evaluation sales**: it updates inventory state
only. Do not label this Bayesian posterior-adaptive inventory control.
Do not count a second draw on the same M5 path as a second real evaluation.

## 6. Outcome definitions and descriptive statistics

For each eligible item-store `s`, origin `o`, history budget `n`, method
`m`, seed `r` and scenario `θ`, define

```text
C(s,o,n,m,r,θ) = sum of M1 holding + lost-sales + order costs
G(s,o,n,r,θ ; candidate,baseline) = C(baseline) - C(candidate)
Positive G is a paired cost benefit of candidate versus baseline.
```

Lower cost is preferred. Record total cost and components, order-cap frequency,
fill rate as **fulfilled / total requests** (when requests >0), ending inventory
and pipeline, startup-inevitable exposure (when initial inventory/pipeline are
zero and `lead_time > 0`), and model/decision computation.

For this 12-series single-origin pilot, publish means and medians of matched
costs, pair wins/ties/losses, within-item-store averages of differences
across four budgets, exploratory demand/scale-normalized descriptive costs, pooled fill
rates, and leave-one-series/two-highest-demand exclusions. Explicitly label
the selection of the top two as exploratory sensitivity, not hypothesis
testing. Distinguish aggregate-weighted improvement from equal-series
average improvement. Do not attach p-values or confidence coverage claims to
the 48 mechanically correlated pairs.

**Candidate primary estimand to predeclare at M4c:** the equal-item-store
average **paired 28-day simulated cost gain** `G` from the selected policy
versus the strongest prespecified baseline at a fixed history budget, then
aggregate across prospectively eligible origins and operational scenarios
using explicit weights. Lower cost remains the objective; `G>0` favors the
candidate. A scale-normalized secondary estimand and pooled demand-weighted
service metric must be labeled separately. Item-store/origin is a repeated
measure, **not** an independent sample. Treat store/geographic clustering and
shared calendar shocks as potential dependencies and plan hierarchical or
cluster-aware uncertainty estimation with adequate numbers of true clusters;
with 12 series across eight stores and one common window, the pilot has no
reliable confirmatory inference. Prespecify a future sampling/power plan,
multiple truly distinct origins, method training/MC seeds, uncertainty
intervals, harm frequency and error under severe misspecification *before*
opening reserved outcomes. Counts/seeds/margins remain unapproved, not hidden
implicit defaults. Seeds are repeatability factors, not new real demand paths.

Calibration for a selected/adaptively tuned policy does **not** automatically
retain pre-selection uncertainty coverage. A claimed T1 guarantee requires
valid simultaneous/selection-aware calibration or independently separated
post-selection calibration evidence, plus controlled known-law coverage tests;
ordinary GP credible intervals alone do not imply coverage.

A non-inferiority claim about a short history `n=28` versus `224` needs
an **externally justified, prespecified cost margin** and a valid one-sided
design on reserved outcomes. No margin/power has been justified by the
current 12-series pilot; selecting it after viewing final costs is prohibited.
Differences between budgets also reflect recency and time-feature scaling.

## 7. Controlled synthetic track and operational sensitivity

Synthetic data provide known latent demand and ground truth. Develop
stationary count laws, intermittent/zero-inflated demand, level/trend shifts,
varying lead time and misspecified GP families. Use independent synthetic
histories and evaluation paths; count real samples separately from simulations.
Compare M1 replay to small M2 exact DP only where the IID known-law DP
assumptions genuinely hold (no fictitious oracle result for nonstationary
regimes). Record true GP calibration/error separately from cost improvement.

Development sensitivity candidates (not a combinatorial run permission):
lead time `{1,3,5}`, holding/lost-sales ratio
`{(1,2),(1,10),(1,20)}`, zero-stock and prespecified common warm-start
initial states, finite-horizon terminal treatment/salvage, capped-order binding,
and path-draw/compute budgets. Construct informative minimal scenario slices
before considering a large cross-product; predeclare what failure each slice
tests. Varying lead time also requires consistent pipeline state lengths and
horizon-aware order cutoffs.

## 8. Our proposed contribution — testable structure, not a result

Promising but **unproved** mechanism: a decision-sensitive, inventory-structured
comparison of candidate policy against a protected baseline, recognizing that
today's order cannot undo inherited positive-lead-time shortage but can affect
later costs through pipeline and available stock.

Possible hypothesis: inventory-structured propagation of demand uncertainty to
a **paired cost difference** makes candidate acceptance/rejection more reliable
than generic policy-return intervals, simple penalties or plain GP rollout
under limited histories and model misspecification.

Distinguish this from common random numbers, standard GP model uncertainty,
naive adaptive penalties, DCL/ordinary RL and generic safe policy improvement.
Before implementation, write the precise estimator, assumptions, action/
policy-selection adaptation issue, testable failure cases, and either a
defensible mathematical statement or a separately meaningful computational
method. Use identical GP, continuation policy, learner access and compute when
ablating the **new** inventory-sensitive component.

This mechanism is a *research candidate*, not an established guarantee or
theorem. Research may legitimately find it fails or adds no advantage.

## 9. Work packages and gates

1. **M4b audit (completed upon reviewed PR):** checksum/provenance verification,
   independent M1 replay, 12-series dependence-aware descriptive analysis,
   preserved artifacts, tests and no evaluation execution.
2. **M4c design lock:** prospective later development origins/cohort groups,
   explicitly forbidden later outcome ranges, metric/compute matching and
   initial/salvage-cost sensitivity priorities. Expose no reserved results.
3. **M4d baseline implementation:** fill 3×2 matrix, recency/GP-scaling
   diagnostics, GPU/CPU tests and one bounded development-only pilot.
4. **M5 theory and mechanism:** verify prior art; define and test inventory-
   sensitive paired comparison versus strongest matched conventional method.
5. **M6 publication protocol lock:** justified estimator, margins, powers,
   baselines, seeds, final scenarios and holdouts; no adaptive changes after
   freezing. External 2017 item-store Favorita requires authorized Kaggle
   terms/data and declared treatment of missing, fractional and negative sales.

The original immutable run is **not** a manuscript Results section. Every
future campaign requires its own versioned config, scientific gate and
execution approval. Do not rerun the 192-job campaign to get a nicer result.
