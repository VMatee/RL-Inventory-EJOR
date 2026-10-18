# M2 known-model engineering reference

The owner explicitly authorized M2 on 2026-10-17 and accepted the current M1
conventions as its engineering reference, not as final publication assumptions.
See `INVENTORY_MODEL.md` for the unchanged event timing and terminal accounting.
This reference uses synthetic **known iid** finite-support demand only. It does
not learn demand, use retail data, or implement a GP/RL method.

## Information, objective, and numerical convention

The policy sees `(remaining, InventoryState(on_hand, pipeline))` after current
receipts and before current demand. The known demand law is shared by the DP
and baseline tuner. In the iid model this is sufficient decision information;
dependent/nonstationary demand would require a different information contract.
There is no realized current/future demand argument in the policy interface.
The independent test oracle allows full *past* demand history, never future
demand. Restricting the DP to the stated Markov state loses no decision-relevant
information for this known iid model.

For the M1 cost `g(s,q,d)` and transition `f(s,q,d)`, compute

```text
V(0,s) = 0
V(n,s) = min over q in {0,...,Q_max} sum_d p(d) [g(s,q,d) + V(n-1,f(s,q,d))].
```

This is the exact finite-horizon mathematical DP, computed to floating-point
precision, not a symbolic exact-arithmetic solver. `FiniteDemand` requires
unique nonnegative integer support and finite nonnegative numeric probabilities.
It rejects empty laws, zero mass and sums differing from one by more than
`1e-12`. Accepted roundoff within that tolerance is normalized explicitly;
`input_mass` records the original sum. Zero-mass entries are not expanded.
Counts inherit M1's representability limit of `2**53`; overflow fails explicitly.

Action ties choose the smallest action with exactly equal computed cost.
Near ties are not rounded or grouped. The demo checks returned-policy agreement
and DP dominance using absolute tolerance `1e-10`; that check is not a general
floating-point error theorem. Absolute gaps are always reported; the relative
gap is `null` at zero reference cost. Deterministic and binary-rational fixtures
are checked for exact equality.

## Reachability, resource limits, and policy evaluation

The solver first discovers every positive-probability decision state reachable
under every allowed action, then performs backward induction. Keys contain both
time remaining and physical state. Terminal states have implicit zero value;
they are not stored as decision states. Returned action/value maps are read-only;
requests outside the reachable keys fail instead of clipping or inventing an action.

No artificial inventory cap is used. Finite horizon and bounded orders imply
finite reachability: on-hand at period t cannot exceed initial on-hand plus all
initial pipeline units plus `t * Q_max`. This conservative bound is explanatory,
not a truncation. M1 still computes its hypothetical next receipt at the final
step, without sales or cost after the horizon.

`ResourceLimits` bounds total decision-state insertions, transition calls, and
elapsed computation time. A violated limit raises `ResourceLimitError` and
returns no partial optimum. Counts include repeated state-time visits across
different baseline grid evaluations. DP transition counts include both reachability
and backward induction; they are implementation work counts, not simulated data.
Policy evaluation uses forward probability propagation with one policy call per
decision state before demand branching. It never minimizes over actions.
The tuner shares one cumulative budget across its grid. The two baseline
variants receive identical, separate budgets and the same grid, demand law,
initial state, costs, horizon and decision-time information. DP and policy replay
also receive separate budgets. Work counts are reported for each operation;
this remains an engineering reference, not a matched-compute empirical study.

Limits bound computational containers, not OS resident bytes. Clock checks are
cooperative; user-supplied policy callbacks must terminate. Use the documented
external process timeout as well. Very large instances, nonfinite accumulated
costs, probability underflow in forward evaluation, or M1 count overflow fail;
they are not approximated. Defaults are small-reference conveniences, not a
scalability claim.

## Baseline and independent evidence

Both variants use a **constant integer level S** and after-receipt position:

```text
position = on_hand + sum(pipeline)
naive_order = min(Q_max, max(0, S - position))
horizon_aware_order = 0 if remaining <= lead_time else naive_order
```

`BaseStockPolicy` preserves the original **naive constant comparator**, which
orders even when receipt would be outside the evaluation horizon.
`HorizonAwareBaseStockPolicy` is the finite-horizon baseline: at period t,
`remaining=T-t`, so `remaining <= L` is equivalent to `t+L >= T`. Such orders
cannot serve any evaluated demand and incur nonnegative placement costs with
zero additional terminal value. Choosing zero is therefore sufficient (even
when ordering costs are zero and extra orders would tie). At `remaining=L+1`,
orders can still arrive in the last sales period and are permitted.

The cutoff depends only on known lead time and observed time remaining, never
current or future realized demand. It changes policy decisions, not M1 timing,
costs, receipt dates or terminal treatment. It does not optimize the level S
over time before the cutoff and is not generally an optimal lost-sales policy.

Tune **each variant separately** over the same declared finite grid using exact
known-model evaluation and the same per-variant resource allowance. Exact ties
select smaller S. The API uses `tune_base_stock(..., horizon_aware=True)` for the
finite-horizon variant; explicit `False` retains the original naive behavior
(also the compatibility default). There are no tuning/evaluation random draws,
seeds, or real-data learning budgets.

**Corrected interpretation of the unchanged tiny example:** the original
0.125 gap disappears with horizon-aware base-stock. Both variants select S=1;
DP and horizon-aware cost are **2.875**, while naive cost remains **3.000**.
For the naive policy, paths 010 and 011 each pay an unnecessary final order
cost 0.5, accounting for the entire expected gap: `2/8 * 0.5 = 0.125`.
This example does not demonstrate a DP advantage over the horizon-aware
baseline. It was retained unchanged, not replaced to manufacture a positive gap.

`tests/test_m2_reference.py` independently enumerates all 128 assignments of
binary actions to the seven past-demand-prefix nodes in each three-period
binary-demand fixture. It evaluates each complete contingent policy over all
eight demand paths with rational arithmetic and a separate receipt calendar.
It calls neither the production transition nor the Bellman recursion. Tests
cover L=1 and L=2 with a nonzero initial pipeline, returned-policy execution,
and every grid level of both baselines. Additional hand-calculated path costs
check the gap's exact source; L=3,T=2 checks orders arriving beyond the entire
horizon; cutoff equality and last-useful-order tests catch off-by-one errors.
Different current/future demand paths with the same past prefix produce the
same action. The open-loop minimum remains 3.000 in the original example,
but both DP and horizon-aware base-stock achieve 2.875. Open-loop enumeration
is labeled only as a sanity comparison, never an adaptive optimum.

## Runnable example

From the Git checkout (`github/`), using the existing sibling environment:

```bash
timeout 120s ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -v
```

The strict JSON configuration supplies all costs, state, demand, tuning grid,
and resource limits. The CLI rejects missing/unknown/duplicate fields and invalid
values. It prints configuration, actual costs/gaps, counts, terminal convention,
and provenance (base commit, dirty flag, source-file and config hashes, versions).
JSON now reports `base_stock.naive_constant` and `base_stock.horizon_aware`, each
with its own grid costs, selected level, limits, counts and gap. Consumers of
the original flat `base_stock` result must select a named variant explicitly.
It writes no result files itself. For a fresh saved local smoke artifact:

```bash
timeout 120s ../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/m2_tiny.json --seed 0 --timeout 110 --allow-dirty -- ../code/.venv/bin/python scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
```

The wrapper creates a unique ignored run directory, captures stdout/environment,
and records status. Its required seed 0 is provenance metadata only; the child
explicitly reports `seed: null` because enumeration uses no random draws. This
is a deterministic engineering smoke demonstration, not a research run.
Measured results and limitations are in
`results/summaries/M2_REFERENCE_VALIDATION_20261017.md`. Stop for M2 review.
