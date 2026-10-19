# Optional extra GPT-6 Pro review handoff — M4b, 2026-10-19

> An independent Codex GPT-6.1 Ultra code/science review **has already been
> completed** and supplied by the owner; it requested changes to PR #10.
> The authoring account addressed those findings in a follow-up patch.
> See `docs/M4B_CODEX_REVIEW_RESPONSE_20261019.md` for the exact accepted
> findings and regression-test response. A **read-only re-review of that
> patch is still required before merge**. The scarce Web GPT-6 Pro quota
> has not been used; it is optional additional review, not a prerequisite
> if a satisfactory independent Codex re-review is completed.


**Purpose:** rigorous outside-the-author scientific and code audit of the
M4b work, to be performed by the owner's **other ChatGPT account** using
the shared SeneraAiServer connection. **No external Pro review has been
performed or claimed by this authoring session.**

## Ready-to-paste reviewer instruction

You are acting as an adversarial independent reviewer for a potential
European Journal of Operational Research (EJOR) methodology manuscript
on data-limited inventory policy learning. Your role is **review only**:
read code, run read-only integrity checks or fast isolated tests if useful,
and report issues. **Do not edit, commit, push, merge, synchronize Git,
rerun 192 baselines, access final M5 outcomes, change data, download
anything or train any model.** Do not modify the original checkout or
write into another project. The authoring agent is not simultaneously
editing this checkout during your review.

Activate SeneraAiServer for project
`/home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR`.
Run Git commands from its `github/` child. Read `github/AGENTS.md`,
`docs/PROJECT_CHARTER.md`, `docs/CLAIMS.md`,
`experiments/protocol/EVALUATION.md` and the **M4b PR diff** before
judging results. Do not rely solely on the PR's narrative.

Read all three M4b deliverables and their actual implementation:
- `src/inventory_ejor/baselines/analysis.py`
- `scripts/analyze_m4_results.py`
- `tests/test_m4b_analysis.py`
- `results/summaries/M4_BASELINE_RESULTS_AUDIT.md`
- `experiments/protocol/M4B_DEVELOPMENT_PROTOCOL.md`

Verify the source session is
`results/runs/m4-approved-yc4xtrp1/` and the original run's source
commit is `5d01105671b8033d7bc8aefa0daedeb1ab99b0be`.
Treat all run outputs, per-series private analysis and prepared M5
learner/evaluator JSONs as **private read-only local evidence**. The
corrected study has 12 selected M5 item-store series, four nested
historical budgets, one forward 28-day window and seed 0.

### Independent questions (answer each explicitly)

1. **Evidence integrity:** Are the SHA256 checks complete and the
   method/budget/series/outcome comparisons reconstructible? Do the
   saved M1 transitions, costs/components, provenance wrapper and
   learner ledger really match? Look for omitted validations, symlink/
   path escape, silent filesystem writes or untrustworthy row identity.
2. **Statistical estimands:** Do the report's mean differences, cost
   reductions, 34/11/3 paired outcomes, 10/2/0 per-series outcomes,
   fill rates and 5.92× simulation-effort ratio agree with raw verified
   output? Are 48 paired tasks incorrectly considered independent?
   Does the report avoid invalid p-values/non-inferiority assertions?
3. **Data bias and leakage:** Is the historically screened cohort
   prospective with respect to d_225; how does M5 ex-post item
   catalog, zero-sales censoring, 28-day positive-sale selection and
   79% top-two demand concentration limit external validity?
4. **Model/scenario fairness:** Does the same fitted GP really underpin
   both GP controllers? Can the observed 4.11% difference be
   attributed to decision-time rollout rather than GP superiority?
   What is confounded by different synthetic-transition budgets,
   zero initial stock, lead-time 3 and horizon-end cutoff?
5. **Proposed future firewall:** Are the candidate half-open date
   ranges, n=224 history runways, non-overlap rules, per-origin
   information budgets, model/compute-matched comparisons, training
   seeds and limited holdout rules defensible? Do not mistakenly
   treat the proposed final M5 window as a blind unpublished test.
6. **Novelty:** What specifically is not yet established about
   inventory-structured uncertainty in a *paired policy cost
   difference* versus GP rollout, DCL, TED/HDPO and generic robust
   baseline-improvement methods? List falsifiable tests and the
   strongest prior-art overlaps. Do not invent a theorem or sources.

### Deliverable expected from the Pro reviewer

Return a structured, independent verdict: **BLOCKING errors,
MAJOR scientific limitations, MINOR clarity/tests, VERIFIED facts,
and an ordered remediation plan**. Cite exact file paths and code
lines wherever possible. Clearly distinguish numerical audit defects
from the wider manuscript's not-yet-demonstrated novelty. Do not
describe hypotheses as results. When unsure, state the uncertainty.

The authoring account will implement any accepted changes in a new
commit, rerun targeted regression checks and verify the unchanged
original run files. Keep both accounts in **single-writer mode**.

## Read-only reproduction command

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
../code/.venv/bin/python -B scripts/analyze_m4_results.py \
  --session results/runs/m4-approved-yc4xtrp1
```

This default CLI prints aggregate-only JSON and writes nothing.
Do **not** use `--output-dir` during an independent read-only
review unless the user has separately authorized a new local output
directory. Do not run `code/run_baselines.sh` again: the one-shot
M4 session is complete and preserved.
