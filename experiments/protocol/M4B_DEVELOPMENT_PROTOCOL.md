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

## 3. Chronological access firewall (proposed geometry)

The original M5 source contains actual sales through `d_1941`.
Use **half-open** day intervals and require each phase's
`[origin - 224, origin + 28)` to lie wholly within that phase.
This possible geometry illustrates a conservative separation without reading
proposed later outcomes; it is **not permission to evaluate** them:

| Phase | Proposed reserved day range | Illustrative origin(s) | Permitted use |
|---|---|---|---|
| Development | `[1,1009)` | Existing `225`; future `477,729,981` | Method/debug/architecture search, all accesses recorded |
| Calibration | `[1009,1261)` | `1233` | Only prespecified calibration operations |
| Validation | `[1261,1513)` | `1485` | Declared method/hyperparameter selection |
| Final M5 test | `[1513,1942)` | `1914` | Frozen model/process scoring once, no feedback tuning |

The preliminary `d_225` observation window has **already been inspected**.
It must remain development forever. Do not silently promote it or another
data-exposed period into validation/final. In particular `d_1914..d_1941`
is public M5 competition data, not a cryptographically blind hidden test, so
a future disclosure must state its public-benchmark limitations.

The phase boundaries/origins in this table are **candidates requiring a
documented freeze before access**, not preapproved final scientific choices.
Confirm calendar/seasonality, eligible sample counts and power *using allowed
metadata only*. More than one final nonoverlapping window is desirable, but
adding one must not train on another final window's observed outcomes unless
a separate, explicitly declared online-adaptation protocol is designed.
Use M3 `SplitPlan` to enforce windows/forbidden outcomes in code. **Never
use all 1,941 days for both model development and final evaluation.**

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
prespecified decay) and a **GP time-feature normalization ablation** using
fixed calendar-day units rather than division by `n-1`. The latter is critical:
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
streams. Do not count a second draw on the same M5 path as a second real
evaluation window.

## 6. Outcome definitions and descriptive statistics

For each eligible item-store `s`, origin `o`, history budget `n`, method
`m`, seed `r` and scenario `θ`, define

```text
C(s,o,n,m,r,θ) = sum of M1 holding + lost-sales + order costs
Δ(s,o,n,r,θ ; m,b) = C(s,o,n,m,r,θ) - C(s,o,n,b,r,θ)
```

Lower cost is preferred. Record total cost and components, order-cap frequency,
fill rate as **fulfilled / total requests** (when requests >0), ending inventory
and pipeline, startup-inevitable exposure (when initial inventory/pipeline are
zero and `lead_time > 0`), and model/decision computation.

For this 12-series single-origin pilot, publish means and medians of matched
costs, pair wins/ties/losses, item-store **clustered** average differences
across four budgets, demand/scale-normalized descriptive costs, pooled fill
rates, and leave-one-series/two-highest-demand exclusions. Explicitly label
the selection of the top two as exploratory sensitivity, not hypothesis
testing. Distinguish aggregate-weighted improvement from equal-series
average improvement. Do not attach p-values or confidence coverage claims to
the 48 mechanically correlated pairs.

For an eventual independent test, define primary estimand and statistical
sampling unit in advance. Use hierarchical/cluster-aware uncertainty methods
where justified by item/store and temporal dependence, with sufficiently many
clusters/origins; sensitivity to cluster choice is mandatory. Seeds are
repeatability factors, not independent demand units. Report distributional
tails and baseline *harm* frequency rather than focusing only on average gain.

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
