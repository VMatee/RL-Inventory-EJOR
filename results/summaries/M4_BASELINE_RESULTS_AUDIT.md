# M4b audited development-baseline results — 2026-10-19

**Evidence status:** verified *single-origin exploratory development results*.
**NOT** a final/independent EJOR experiment, statistical-significance test,
policy safety guarantee, true-demand reconstruction or proof of novelty.

## 1. Immutable evidence and reproducibility

- Existing session: `results/runs/m4-approved-yc4xtrp1/` (ignored/private).
- Original source commit: `5d01105671b8033d7bc8aefa0daedeb1ab99b0be`.
- Original input: M5 12 pre-origin-screened item-store series from 32
  predetermined candidates, four nested budgets `28/56/112/224`, one
  origin `d_225`, a common 28-day forward sales-as-requests path per series,
  seed 0, four baseline methods (192 jobs).
- Session status `completed`, 192/192 exit-zero, 93.659 seconds scheduler
  wall time; original aggregate status `complete_and_hash_verified`.
- Reusable strict read-only verifier:
  `scripts/analyze_m4_results.py --session results/runs/m4-approved-yc4xtrp1`.
  It recomputes saved aggregate results, checks 192 wrapper/source/config/
  data-manifest hashes, 192 individual result hashes and 192 trace hashes,
  verifies each result against the saved CSV, the **pinned evaluator's
  actual forward requests**, validated M3 learner histories, full access
  ledgers/compute accounting, bound per-job wrapper commands and terminal
  metadata. All **5,376 periods** are rechecked both against original M1
  and an **independent calendar-list implementation**. No trained method,
  GPU job or test outcome is regenerated.
- The local ignored folder
  `results/analysis/m4b-original-20261019/` contains
  `audit_private.json` with per-series diagnostics and
  `audit_public.json` with aggregate-only data. **Do not upload the
  private file**, retail traces or protected prepared/raw inputs.

The 192 successful jobs are 192 **model × budget × series** tasks, **not**
192 statistically independent sales sequences. For each of 12 series, all
16 method/budget combinations score the exact same future 28-day path.
The study-wide M3 ledger disclosed **3,248 historical sales cells**:
2,688 selected-history cells plus 560 additional excluded-candidate
screening cells. The screen is design information, not an unreported
extra set of independent demand observations for learners.

## 2. Baseline cost and service-level results

The cost is a **simulated diagnostic unit**, not retailer dollars:
holding = 1/unit-period, lost request = 10/unit, no order charges, lead
time = 3 periods, initial on-hand/pipeline = 0, no extra terminal
value. Lower mean cost is preferred. Every mean in the table below
averages 12 item-store paths, each evaluated over 28 days.

| Real observed-sales history | Empirical + base-stock | Gamma–Poisson + base-stock | GP + base-stock | GP + one-step rollout |
|---:|---:|---:|---:|---:|
| 28 days | 208.17 | 207.33 | 208.67 | **199.58** |
| 56 days | 207.83 | 209.08 | 207.25 | **196.75** |
| 112 days | 210.67 | 211.75 | 203.75 | **198.00** |
| 224 days | 219.67 | 220.67 | 205.67 | **197.08** |

Cost decomposition sums **all 48 tasks per method**; repeated outcome
windows mean these are descriptive scores, not 48 independent replicates.

| Method | Total cost | Holding | Lost requests | Mean cost/job | Pooled fill rate |
|---|---:|---:|---:|---:|---:|
| Empirical + base-stock | 10,156 | 2,946 | 7,210 | 211.58 | 67.35% |
| Gamma–Poisson + base-stock | 10,186 | 2,556 | 7,630 | 212.21 | 65.44% |
| GP + base-stock | 9,904 | 3,344 | 6,560 | 206.33 | 70.29% |
| GP + rollout | **9,497** | **3,037** | **6,460** | **197.85** | **70.74%** |

All methods evaluated 552 unique forward units across the 12 series;
counting the same windows over the four histories yields 2,208 request
units **per method** in this table. The pooled fill rate is
`sum(fulfilled)/sum(requests)`, *not* a mean of item fill-rate percentages.

## 3. Matched policy comparisons (exploratory)

For `Δ = cost(comparator) - cost(GP rollout)`, a positive value favors
GP rollout. The following compares the same `series × history` pair:

| Comparator | Mean Δ over 48 pairs | Aggregate cost reduction | Win/tie/loss over 48 pairs | Win/tie/loss after averaging by 12 series |
|---|---:|---:|---|---|
| Empirical + base-stock | +13.73 | 6.49% | 33 / 11 / 4 | 10 / 2 / 0 |
| Gamma–Poisson + base-stock | +14.35 | 6.76% | 30 / 11 / 7 | 9 / 2 / 1 |
| GP + base-stock | **+8.48** | **4.11%** | **34 / 11 / 3** | **10 / 2 / 0** |

The 12 series are **not assumed independent**: they share the calendar
and may share locations/categories. No p-value, confirmatory confidence
interval, sample-size/generalization claim or superiority statement is
justified by this exploratory selection. Removing the two highest-*future-
request* series, solely as an explicitly **post hoc diagnostic**, leaves
an observed GP-base-stock versus rollout pooled-cost reduction of **9.61%**
among the other ten; this is *not* an externally valid trimmed estimator
or an approved cohort-selection rule.

For GP base-stock versus GP rollout, **leave-one-series-out pooled
relative cost reductions** range from **3.26% to 8.01%** (12
exploratory omissions). The **equal-series average of within-series
relative reductions** is **7.74%** for the same comparator, unlike the
4.11% pooled-cost ratio. These are different descriptive weightings,
not interchangeable population estimands or confidence intervals.

Three GP-rollout versus GP-base-stock budget/series pairs experienced
a worse simulated cost. They must not be dropped. Identical outcomes
in several sparse-demand pairs can reflect low policy discrimination,
not evidence of statistical equality.

## 4. Why GP rollout appears to improve costs

Saved per-job metadata confirm that the two GP controllers have an
**identical fitted GP model, identical tuned base-stock level, and
identical base-stock tuning-cost vectors in all 48 paired cases**.
They differ in decision-time action optimization, not fitted GP parameters.
The rollout changes **407/1,344 = 30.28%** of recorded daily actions.

Compared with the GP base-stock method, GP rollout saves **407** aggregate
cost units: **307 holding units (75.4% of saving)** and **100 lost-request
penalty units (24.6%)**. Pooled fill rate improves only from 70.29% to
70.74% (about **0.45 percentage points**). This supports the narrower
interpretation that action-specific stock/timing optimization helps
in this setup; it does **not** establish predictive calibration or
GP demand-model superiority.

Cost improvement must be interpreted jointly with additional computation:
mean simulated M1 transitions per job are **437,248** for GP base-stock
versus **2,587,648** for GP rollout (**5.92×**). The average reported
in-worker time is approximately **2.76 s** versus **2.93 s**; this small
wall difference on this tiny four-GPU setup is **not** compute-matched
evidence or a transferable GPU-speedup claim. The rollout's declared
optimization trials are 586 versus 61 for base-stock. The 48 base-stock
GP fits recorded 75 finite Adam loss values each with final loss no
greater than initial, but that alone does not establish convergence.

## 5. Five concrete threats to scientific interpretation

**A. Heavy concentration and intermittent requests.** The two
highest-future-request series account for **437/552 = 79.17%** of
requests, and **74.04%** of aggregate GP rollout cost. Eight of 12
series have at most 11 requested units over 28 days; six have at least
20 zero-sales days in their 28-day historical learner window.
Both raw-cost weighting and zero-demand sparsity strongly influence
rankings. Stratify prospective cohorts by *historical*, not future,
activity before the next trial.

**B. Inherited startup lost requests and first-arrival transient.** With
zero initial inventory/pipeline and positive lead time 3, the first
three request periods are unfillable. Their shared lost-request penalty
sums to **2,000** across four histories, about **19.6–21.1%** of method
totals. An independent reviewer further found, and the revised auditor
recomputed, that **336/407 = 82.56% of the GP-rollout cost advantage
occurs in periods 3–5** (the first three days replenishment can arrive)
and **all 336 saved units are holding costs**. Periods 6–27 contribute
a net 71 saved units. Despite a total holding-cost advantage, GP
rollout finishes with **147 versus 119 total units of recorded
end-of-horizon stock-before-receipt** over 48 matched series/budget
paths. Thus a claim about a uniform reduction of leftover terminal
inventory would be false. These initial-state/transient findings are
exploratory and strongly motivate prespecified warm-start, terminal
value and longer-horizon tests; preserve historic scores unchanged.

**C. Nonmonotone information budgets.** For GP rollout, average
28-day costs at histories 28/56/112/224 are
199.58/196.75/198.00/197.08. A monotone improvement cannot be
inferred; neither can a 28-day non-inferiority statement. The older
observations may come from different regimes, and the implemented
GP scales relative time by `history_length-1`, **changing model
features when data volume changes**. Carry out a fixed-calendar
time-feature ablation; never infer isolated sample-size effects from
these four rows.

**D. Sales are not latent demand.** M5 does not record the on-hand
stocks, supplier lead times, actual shortage costs or genuine
stockouts of a retailer. Replaying **observed sales as requests**
is a controlled hypothetical simulation. A zero-sale observation
does not mean demand was necessarily zero. Do not describe the
computed savings as observed Walmart financial outcomes or valid
real-world stockout rates.

**E. Incomplete baseline/compute matrix.** Empirical and
Gamma–Poisson were tested with base-stock only, so we do not yet
know how much of rollout's benefit would occur under simpler
demand models. Both compute-matched and native-budget comparisons
are needed; GP+rollout is not DCL/MPC/RL and is not the paper's
proposed new method. Its effective MC seed includes the history budget,
so contrasts between n values also differ in optimizer random draws;
and GP uses deterministic calendar features that iid comparators lack.

## 6. Independent Codex review and closed/open obligations

An independent **Codex GPT-6.1 Ultra** review supplied by the owner on
2026-10-19 confirmed the original 4.10945% computation using an external
calendar oracle without importing production M1. The review found two
**blocking verifier defects** in the *first* PR #10 revision: it did not
bind evaluator input to replay requests and trusted self-declared ledger
and compute counts. It also found job-wrapper swapping, unchecked
terminal metadata, premature symlink following and an impossible promise
about independent final-origin histories.

The follow-up revision now verifies evaluator and learner fingerprints
and values, reconstructs full M3 access ledgers with `validate_ledger`,
reconstructs known simulation-work formulas, binds unique job-indexed
worker manifests, validates terminal metadata against an independent
calendar oracle, and checks symlink/noncanonical files before opening.
New synthetic adversarial tests exercise forged inputs, ledgers, wrapped
jobs, terminal results and forbidden final-history overlap. The original
192-run data were not altered or rerun.

**Still open:** a scientifically frozen choice of chronological cutoffs,
true inferential estimand, power/sample size, dependence structure,
selection-valid uncertainty construction, strong competitive baselines,
and established EJOR novelty. Software checks do not close these gates.

## 7. Claim-register implications and next research gate

- **H1 inventory-sensitive limited-data policy improvement:** **not
  established**; a decision-time GP rollout ablation is a useful existing
  baseline, not the proposed novel inventory-sensitive safeguard.
- **H2 GP improvement over simpler/neural uncertainty:** **not
  established**; cross model × controller matrix and forecast calibration
  are missing.
- **H3 short-demand-history sufficiency:** **not established**; one
  origin and confounded recency/time-scale prevent non-inferiority claims.
- **T1 policy-improvement uncertainty bound:** **unproved**; no bound
  was implemented or evaluated.
- **D1 actual retailer costs:** **unsupported**, and expressly excluded.

**Next step (no jobs authorized by this report):**
use `experiments/protocol/M4B_DEVELOPMENT_PROTOCOL.md` to define a
protected development/calibration/validation/final firewall, implement
Empirical+rollout and Gamma–Poisson+rollout plus recency/time-scaling
controls, and conduct development-only matched compute/data ablations.
Develop a precise inventory-specific, lead-time/pipeline-aware
**paired policy-cost uncertainty mechanism** in parallel with
prior-art examination; only then run controlled synthetic and expanded
retail-sale diagnostics. Favorita remains pending authorized original
2017 Kaggle competition access.

## 8. Exact reproduction (read-only default)

From the versioned Git root `github/`:

```bash
../code/.venv/bin/python -B scripts/analyze_m4_results.py \
  --session results/runs/m4-approved-yc4xtrp1

# Optional local, Git-ignored machine outputs (only if directory is NEW):
../code/.venv/bin/python -B scripts/analyze_m4_results.py \
  --session results/runs/m4-approved-yc4xtrp1 \
  --output-dir results/analysis/m4b-independent-recheck
```

The first form prints aggregate-only JSON and writes **nothing**.
The second writes `audit_private.json` and `audit_public.json` into a
new ignored directory only; it does not modify run artifacts or start
baselines. The auditor fails closed for altered outputs, missing jobs,
misaligned timestamps/requests, provenance/ledger inconsistencies,
incorrect cost decompositions or unsupported scope. Automated synthetic tests are in `tests/test_m4b_analysis.py` and
`tests/test_m4b_review_fixes.py`. The second suite includes explicit corruption/embargo regressions.
`tests/test_m4b_full_audit_synthetic.py` builds and accepts a complete
synthetic 16-job end-to-end session and then verifies that forged receipt,
ledger, terminal and evaluator data are refused after read-only checking.

**Scientific boundary:** successful code checks validate only the
reported computations and stock-flow replay for this one experiment.
They do not prove causal policy benefit, theoretical novelty,
distributional coverage, population significance or journal acceptance.
