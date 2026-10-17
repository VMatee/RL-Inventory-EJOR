# M1 inventory model: deterministic reference semantics

**Status (2026-10-17):** Selected and implemented as the **M1 engineering convention**, not yet an empirical research result or a user-approved final theoretical formulation. Review/change these assumptions explicitly in `docs/DECISION_LOG.md` before beginning M2. This document is the reference for code, test fixtures and eventual problem-formulation equations.

## 1. Scope and units

- Single item, one stocking location, periodic review, **lost sales (never backorders)**.
- All stocks, order quantities, pipeline entries, and exogenous realized demands are **nonnegative integer units**. Cash costs are finite nonnegative real-valued scenario parameters. No returns, disposal, perishability, capacity limit on stock or rationing.
- **Deterministic, known, positive integer lead time** `L >= 1`. Demand may be arbitrarily varying between periods, but the M1 kernel does not fit or assume its distribution. The Gymnasium wrapper accepts an exactly specified exogenous demand trace for deterministic tests.
- Finite **horizon** `T >= 1` periods, indexed `t = 0, ..., T-1`. The observed state includes time remaining, so this is a finite-horizon task.
- The replenishment decision `q_t` is an integer satisfying `0 <= q_t <= Q_max`, with `Q_max >= 0`. No implicit clipping, adjustment or rounding of invalid actions.

## 2. Decision-epoch state and timing (important)

**Define the state immediately AFTER the receipt due at the beginning of period `t`, but BEFORE its order and demand.** Therefore the on-hand stock `x_t` is immediately available for sales during period `t`. The pending order vector is

```text
s_t = (x_t, p_{t,1}, ..., p_{t,L-1})
p_{t,k} = quantity scheduled to arrive at the START of period t+k.
```

No pipeline entry is due *at* `t`: it has already been incorporated into `x_t`. For `L=1`, the pipeline is the empty tuple. The initial state is an explicitly supplied after-arrival `x_0` and a vector of exactly `L-1` future arrivals; the default is zero stock and a zero-filled pipeline.

Events for each `t`:

1. **Observe** current decision state `s_t` (stock after this period's receipts, and future committed arrivals); time remaining is observable.
2. **Choose/order** `q_t` units, to be received at the beginning of period `t+L` — **not** during the current sales period, even if `L=1`.
3. **Realize** nonnegative demand `d_t` over period `t`, and record sales `y_t`, lost units `u_t` and end-of-period stock `e_t`. Unmet demand disappears; no backlog is carried.
4. **Charge** holding, shortage and procurement costs for period `t` on the outcomes defined below; holding is charged on `e_t` **before the next period's receipt**.
5. **Advance** to the next decision epoch, including the receipt due at the *start* of `t+1`, without extra cost for receiving it.

Equivalent equations (all indices zero-based):

```text
y_t = min(x_t, d_t)
u_t = d_t - y_t
e_t = x_t - y_t = max(x_t - d_t, 0)

if L == 1:
    r_(t+1) = q_t
    p_(t+1) = ()
else:
    r_(t+1) = p_(t,1)
    p_(t+1) = (p_(t,2), ..., p_(t,L-1), q_t)

x_(t+1) = e_t + r_(t+1)

holding_t = h * e_t
shortage_t = b * u_t
variable_order_t = c * q_t
fixed_order_t = K * 1[q_t > 0]
cost_t = holding_t + shortage_t + variable_order_t + fixed_order_t
reward_t = -cost_t
```

The order currently placed is **first sellable in period `t+L`**, not `t+L-1`. Even when the order is no longer in the pipeline, remaining stock may continue to influence later periods; truncating its influence at `L+1` is **not** assumed.

**Mass-balance invariant:** `x_(t+1) = x_t - y_t + r_(t+1)` with `u_t = d_t - y_t`. The pipeline shifts by one period and appends `q_t` (for `L=1`, it stays empty). In particular, `q_t` cannot influence `y_t` for any positive lead time.

## 3. Objective and finite-horizon boundary

Let `h,b,c,K >= 0` denote per-unit holding, per-unit lost-sales penalty, per-unit order, and fixed order-placement costs respectively (configured scenario parameters, **not** verified retailer costs). The finite-horizon realized total is

```text
C_T = sum(cost_t for t in 0, ..., T-1)
```

The terminal balance is observed **after demand in period T-1 but before any receipt at the start of period T**, as `e_(T-1)`. The post-order pipeline at that moment consists of `L` outstanding batches scheduled for periods `T, ..., T+L-1`, represented as `(p_(T-1,1), ..., p_(T-1,L-1), q_(T-1))`; when `L=1`, this is just `(q_(T-1),)`.

**For M1 set terminal salvage, disposal and extra holding costs to zero.** Every order is charged when placed, even if delivery is outside the evaluation horizon. Outstanding terminal batches are **reported** but are not sold, liquidated, or charged additional holding within `C_T`. Such truncation can create end-of-horizon artifacts; M2+ should explicitly handle comparisons with shared horizons/warm starts or alternative boundary conventions, and never treat this as an infinite-horizon optimality claim.

The transition kernel may compute the *post-arrival* hypothetical `s_T` (after the receipt at the beginning of period T), purely for a consistent state update; there is **no demand, sale or extra cost in period T**. Consequently `s_T.x` may include an arrival not yet present in terminal pre-arrival stock. The terminal summary must use `e_(T-1)` and the outstanding vector, not equate `s_T.x` with physical stock immediately at the end of `T-1`.

## 4. Information boundary for later GP/RL work

M1's deterministic demand trace is supplied **to the simulator**, not to a policy. This observation is Markov for the known stock-flow dynamics; it is **not automatically sufficient for an unknown demand process with autocorrelation or latent regime**. Future GP/RL baselines must add decision-time information (e.g., legally observed past demand and exogenous covariates) when their demand assumptions require it, without leaking future data. A Gymnasium agent sees only `[x_t, p_{t,1}, ..., p_{t,L-1}, T-t]`; no demand for the current or future period is in the observation. After the `step`, `info` may report the *realized* demand and outcomes of that just-completed period. Any future exogenous features/forecasts, training-time simulator access, initial data budgets, demand-model uncertainty and their timing require separate declarations before M3/M4. This API does not protect against a malicious Python policy directly introspecting the environment's private attributes.

The M1 use of fully observed realized demand reflects a **controlled simulator assumption**. Sales traces such as M5/Favorita are not automatically uncensored demand; that limitation remains for later data protocols. Simulated trajectories are not additional real observations.

## 5. Deterministic, independently hand-computed fixture

For `L=3, T=5, Q_max=10`, initial after-arrival stock `4`, initial pipeline `(2,1)`, and costs `h=2, b=7, c=1, K=3`:

| t | (x,p) before order | q | demand | sales | lost | end e | receipt t+1 | (x,p) at t+1 | holding | shortage | order | total |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 0 | (4,(2,1)) | 3 | 3 | 3 | 0 | 1 | 2 | (3,(1,3)) | 2 | 0 | 6 | 8 |
| 1 | (3,(1,3)) | 0 | 5 | 3 | 2 | 0 | 1 | (1,(3,0)) | 0 | 14 | 0 | 14 |
| 2 | (1,(3,0)) | 4 | 2 | 1 | 1 | 0 | 3 | (3,(0,4)) | 0 | 7 | 7 | 14 |
| 3 | (3,(0,4)) | 1 | 4 | 3 | 1 | 0 | 0 | (0,(4,1)) | 0 | 7 | 4 | 11 |
| 4 | (0,(4,1)) | 0 | 0 | 0 | 0 | 0 | 4 | (4,(1,0)) | 0 | 0 | 0 | 0 |

**Total cost: 47.** At the end of the last demand period terminal stock is `0` with outstanding receipts `(4,1,0)`. The hypothetical `x_5=4` reflects the start-of-period-5 receipt and is *not* used to calculate terminal-period sales or holding.

This hand calculation is a **code fixture**, not an empirical study.

## 6. Test and review gates

Required deterministic checks: zero demand/order, exact depletion, no backorders, action/demand validity, lead times `L=1,2,3`, nonnegative mass balance, independent hand fixture, holding/shortage/fixed/variable cost components, horizon termination and no additional terminal cost, reproducible reset, no pre-demand observation of realized demand, Gymnasium API compliance.

M1 requires no GP model, numerical optimal policy, RL training, datasets or new dependencies. The **event timing and boundary treatment are explicit engineering conventions**; if later theory/evaluation selects different conventions, modify this document, code, fixtures and decision log as one reviewable change.
