# M4d baseline readiness and bounded development design

Status: design candidate only. No experiment, model fitting, data release, GPU
job, new outcome access, or campaign rerun is authorized by this document.
The completed d_225 pilot and original 192 jobs remain immutable evidence.
Scientific acceptance and an execution allowance are separate from engineering
readiness. A future run needs its own reviewed source, inputs, scope, and grant.

## 1. Questions and priority

First separate demand-model effects from controller effects. Then determine
whether the observed GP rollout gain survives a common warm initial state.
Investigate data length, recency, time scaling, seasonality, uncertainty, and
compute in targeted panels rather than an indiscriminate full cross-product.

The d_225 pilot's 336/407 saving units occur at the first arrival periods
t=3..5, all through holding costs. This boundary sensitivity prevents a
steady-state interpretation; the arithmetic does not demonstrate a durable
GP or rollout advantage. Later-period cost and terminal stock remain outcomes.

## 2. First complete the six-method matrix

| Demand model | Horizon-aware base-stock | One-step rollout |
|---|---|---|
| Empirical iid | Required | Required; missing from original pilot |
| Gamma-Poisson | Required | Required; missing from original pilot |
| GP log1p-Gaussian surrogate | Required | Required |

Within each model/series/origin/budget/algorithm-seed combination, fit once and
reuse the fitted model, tuned continuation, and tuning paths for both
controllers. Expose identical learner information, prior access, initialization,
action bounds, cost objective, horizon, and terminal convention. Save paired
model identities and effort counters. Adapt the old GP-only rollout dispatch;
do not silently send a simple-model rollout through the GP or wrong sampler.

The first informative development panel may reuse the already exposed d_225
window and the fixed 12 pilot series. It tests implementation and mechanisms;
it supplies no fresh confirmatory evidence. Missing controllers require a new
authorized campaign, not a modification or rerun of the sealed original jobs.
Candidate budgets are n={28,224}, with algorithm seeds {0,1,2}. Six methods
would produce 432 policy evaluations for one initial state; this is a planning
count, not an approved job allowance or a claim that three seeds suffice.

Origin d_477 is a separate prospective development candidate. Preparing its
histories, screening cells, or outcomes requires the applicable stage release;
its existence in a metadata plan does not grant data access. Freeze the panel
before that access. Keep already exposed and newly released origins distinct.

## 3. Minimal boundary panel

Retain the original cold state: on-hand=0 and all L-1 pipeline entries=0.
Add a targeted same-GP/controller pair under one common warm-state rule before
expanding every model/scenario combination. For the candidate L=3, Qmax=20
scenario, let mu28 be the mean requests in the common pre-origin 28-day history
and r=min(Qmax, ceil(mu28)); set on-hand=r and pipeline=(r,r). For general L,
use L-1 copies of r. This is a feasible prescribed initial state, not a sample
from a demonstrated stationary distribution. Freeze or replace the rule before
viewing comparison outcomes. Use the same state across methods and budgets;
never initialize n=28 using 224-day information. Log initialization access.

At the candidate two budgets and three seeds, this targeted warm GP pair adds
144 policy evaluations. Report cold and warm effects separately, including
cost components for t<L, L<=t<2L, and t>=2L; preventable versus inherited
shortage; action-cap use; and ending stock and outstanding receipts. Do not
discard harmful switches or sparse cases with tied cost. Declare zero-cost
denominator handling. A different common warm-state rule is sensitivity work.

A longer horizon needs a new metadata plan and release. Prove that every
[origin-224, origin+T) fits its phase, outcomes do not overlap, and no later
history contains earlier protected outcomes, using the actual T. The current
28-day design does not authorize a 56-day path. With T=56, origins 225 and 477
would have earlier outcomes [225,281) intersecting later history [253,477),
so their original 252-day spacing fails the nonadaptive embargo. Recompute
all runways and spacing before choosing longer-horizon origins. Revaluing old
actions under salvage is a trace sensitivity, not performance of policies
optimized for the new terminal objective.

## 4. Targeted model and information controls

Add a weekday-stratified empirical/count control using the same deterministic
calendar as the GP; freeze sparse-weekday fallback without future information.
Add a prespecified recency-weighted empirical/count model, with any decay
selection confined to allowed development. Pair their controllers where a
controller comparison is claimed. Treat these as separate declared panels.

Compare the original GP time/(n-1) feature with a fixed calendar-day scale.
Use matched forecast dates and all other GP settings; report how the time
feature, older regimes, and MC variation confound a naive sample-size effect.
Add an uncertainty-component control that removes latent-function uncertainty
while preserving declared aleatoric noise, plus forecast diagnostics for zero
mass, bias, tails, and distribution/quantile scores. Describe the surrogate
count transform and the component removed; a point forecast alone changes
several distributional properties. Keep posterior conditioning versus frozen
forecasts explicit; hyperparameter refitting is a different operation.

## 5. Compute, random streams, and interpretation

Label the first comparison matched-information/native-compute. Retain actual
fit, draw, simulation-transition, search-trial, runtime, and memory accounting.
Then specify matched-compute frontiers at a few fixed allowances chosen on
development. Count GP fitting and prediction effort as well as inventory
transitions; equal transitions alone do not equal total computation. Report
trade-offs rather than claiming that the native-compute result is matched.

Use separate fit, tuning, and decision random-stream identities. Couple tuning
and action comparisons through common random numbers where valid, including
across history budgets; keep tuning independent of decision sampling. The old
budget-dependent seed mapping does not create coupled budget comparisons.
For different predictive laws, document the coupling (for example shared base
uniforms/normals), rather than equating identical integer seeds with CRN.
Repeat algorithm seeds and check MC convergence separately from demand-path
variation. Neither new seeds nor four history budgets create new real series.

## 6. Ready-to-run checklist; all required before execution

- Freeze scientific choices, failure handling, primary comparisons, cohort
  eligibility, information tracks, budget/seed lists, and bounded run counts.
- Validate calendar geometry, origin embargo, exact permitted windows, stage
  release dependencies, and any new horizon before reading observations.
- Bind learner and evaluator artifacts separately to the protocol and grant;
  prevent planning/preflight from opening unreleased evaluator files.
- Test sampler/controller dispatch, independent stock-flow and terminal replay,
  CRN identities, zero-demand cases, count guards, and exact effort formulas.
- Demonstrate immutable output/provenance behavior and bounded resource use on
  isolated synthetic fixtures; no retail training is needed for this gate.
- Obtain a separate development execution allowance. Keep calibration,
  validation, final outcomes, RL, and external-dataset access outside that scope.
