# Response to independent Codex review of PR #10 — 2026-10-19

**External review received.** Owner supplied an adversarial
Codex GPT-6.1 Ultra (reasoning ultra) review of PR #10 head
`3fe9eec` vs baseline `5d01105`. This is a **different review process
from the other account's scarce ChatGPT Web Pro quota**; no such Web Pro
review is claimed. The reviewer independently re-simulated 5,376
periods without importing production M1, found original 4.10945%
arithmetic consistent, and **requested changes** for genuine integrity
defects. The authoring agent accepts the findings, not merely the
numerical praise. **Do not merge before an independent re-review of the
follow-up PR revision.**

## Blocking and software findings: remediated in source; re-review pending

| Reviewer objection | Remediation | Counterexample/test |
|---|---|---|
| Pinned evaluator unseen; future request path could silently drift | `audit_checks.evaluate_job` checks canonical evaluator leaf, SHA256 of the **same bytes parsed**, dataset/token/series/window/day identity, and every trace request. | Synthetic wrong request and modified evaluator with old fingerprint both rejected |
| Ledger/training/compute numbers trusted rather than validated | `reconstructed_ledger` calls real `load_learner` + `validate_ledger` against declared source/forbidden windows; reconstructs worker's exact declared accesses, GPU/CPU limits, effective seed, simulation paths/transition and controller-trial formulas; reconciles saved validated counts. | Synthetic altered access, one-transition claim or counts rejected |
| Valid wrapper receipt could be swapped across jobs | `bound_wrapper` validates unique receipt, executable/worker command, exact planned job index, output, plan, approval, git cleanliness/commit before/after, source/config/data identity and exit status. | Duplicate and reassigned wrapper rejected |
| Terminal summary not audited | Independent hand-coded calendar-list stock/pipeline oracle checks each transition/cost component and saved terminal stock/receipts. | Impossible terminal stock and cost parts rejected |
| Symlinked saved input could be opened first | All session/plan/approval/summary/aggregate/CSV and job result/trace/wrapper leaves are checked as canonical paths **before read**, including before the old aggregate code is invoked. Evaluator+learner checked separately. | Synthetic symlinked plan rejected before file access |
| M3 SplitPlan guards outcome overlap but not reuse in later history | New pure `validate_nonadaptive_origin_embargo`; draft future-phase geometry revised to allow two 224+28 nonadaptive blocks with explicit no-reuse histories. | `(1737,1765)` refused, candidate `(1485,1914)` accepted |
| "Independent M1 replay" is shared production code | M1 replay now paired with a separate calendar-list oracle with no `transition()` import; terminal verification included. | Hand-computed synthetic cost/receipt fixture, plus verified real 192-job paths |
| Missing per-item, per-window, terminal sensitivity | Aggregate-only leave-one-series ranges and equal-series average relative improvements added; transients 3–5 vs later recorded; terminal inventory values audited. | Read-only independent recomputation from 192 saved paths |

**Automated follow-up validation:** a fully synthetic 16-job saved session is
built, accepted by `analyze_session()`, and then intentionally corrupted at the
wrapper, ledger and terminal levels (with refreshed checksums), or at the
immutable evaluator level. It fails closed in each case and accepts restored
files. The complete ordinary test suite now passes **166/166**, with the
original 192/192 result audit independently repeated without any new
model fitting. Synthetic tests do not contain or load M5 observations.

**Source review boundaries:** these tests demonstrate fail-closed behavior
on specified counterexamples, not full formal security against a local
attacker who can alter arbitrary trusted Git commits and hashes. The
scientific and empirical pipeline is explicitly not yet publication-ready.

## New substantive scientific diagnostics

- **336 / 407 = 82.56%** of the original GP-rollout versus same-GP
  base-stock cost advantage occurs **at the first replenishment-arrival
  periods t=3..5**. All 336 initial saving units are *holding costs*.
  Later t=6..27 contributes 71 net saving units. This is a startup/
  transient result, **not** a durable steady-state superiority claim.
- Saved terminal **stock-before-receipt totals** across 48 paired
  experiments: **GP base-stock 119**, GP rollout **147**. Any blanket
  claim that the rollout simply reduces terminal inventory is false.
- GP versus iid-only models confounds forecasting uncertainty with the
  GP's time/weekday features; proposed non-GP seasonal control added.
- Original effective seed hashes `series:origin:budget:seed`, and
  therefore changes MC optimization streams across history budgets.
- Demand models are **frozen in evaluation**: inventory updates do not
  imply posterior predictive adaptation. No post-selection coverage
  guarantee follows from a GP posterior.
- M3 records **3,248 distinct historical selected + screening sales
  cells**, including **560 additional excluded-candidate screening**
  cells. New protocol and report disclose these shared-design accesses.

## Still OPEN: scientific/research gates (not code bugs)

1. Prospectively freeze appropriate final chronological cutoffs, seed
   ensemble, cohort selection, primary estimand, dependence unit,
   sample/power calculation and non-inferiority margin **before opening
   reserved outcomes**. The new illustrated geometry is not an
   authorization or scientific power analysis.
2. Strengthen the 3×2 crossed model/controller matrix with seasonal
   non-GP controls, decouple recency/data-length/GP time scaling/MC
   randomness and compare effort at matched native and compute budgets.
3. Run *new authorized* development-only warm-start/long-horizon/
   terminal-value sensitivity: the observed advantage is transient.
4. Specify a demonstrably novel inventory-specific estimator/safeguard
   versus robust baseline regret, DCL, TED and HDPO. Test harmful
   accepted switches, unnecessary rejections and post-selection
   coverage under known-law synthetic data with model misspecification.
5. Favorita original 2017 item-store dataset remains access-blocked.
   Neither raw retailer financial savings nor paper acceptance can
   be inferred.

## Independent re-review result and minor follow-ups

The owner returned an independent **Codex GPT-6.1 Ultra follow-up** on
commit `eef0fd40bc64a3db6f09bdb8a523b1d5bc80baac`: **APPROVE for
scoped M4b audit**, zero remaining blocking or major M4b defects.
The reviewer reproduced all earlier corruption counterexamples and
confirmed the original 192 jobs, 5,376 periods, 4.10945% reduction,
5.91803× simulated effort, and 336/407 first-arrival concentration.
The review separately verified 633 selected protected input/run files
against saved hashes (a narrower subset than the author's 640-file
whole-study snapshot) and exercised a broader 12-input symlink matrix.

Three reviewer-identified **minor** items were subsequently addressed:
relative summaries now represent zero-denominator cases as JSON `null`
with valid/excluded counts, rather than throwing `StatisticsError`;
valid all-zero-request/cost synthetic full-session regression was added;
12 synthetic input symlink types are checked through the actual auditor;
and the proposed chronological data protocol now explicitly seals the
earlier-dated calibration outcomes until after later validation-based
model/policy selection is frozen. This unusual date/access order is **not**
a scientifically validated solution to calibration drift or
post-selection coverage; M4c must still prospectively freeze a defensible
scheme before any withheld M5 outcomes are opened.

The final three minor fixes are verified by authoring-account tests;
they have **not** received an additional independent audit and are not
represented as such. The Codex independent APPROVE covered the previous
verified implementation plus a limited follow-up list; it did not
approve EJOR publication readiness.

## Re-review acceptance checklist (historical instructions, now completed for `eef0fd4`)

The independent Codex reviewer (or an equally independent agent with
read-only access) should rerun the **same previous in-memory corruption
cases** against the newest PR #10 head. Return whether they now fail
closed, with exact code lines, plus any remaining new BLOCKING or
MAJOR issues. Confirm the original 192 campaign is unchanged and
numbers 4.10945%, 5.91803×, 336/407, and terminal 119/147 reproduce.
Do not merge automatically or treat a positive code review as approval
for the future scientific experiments.
