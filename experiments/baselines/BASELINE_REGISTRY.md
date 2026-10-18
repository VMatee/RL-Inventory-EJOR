# Baseline registry

M2 implements horizon-aware capped base-stock and preserves the original
constant capped policy as a **naive comparator**. The horizon-aware variant
orders zero whenever `remaining <= lead_time`. Both are tuned separately by
exact known-iid-model evaluation on the same finite grid with equal resource
allowances; see `theory/M2_REFERENCE.md`. They use the same M1 initial state,
costs, horizon and demand law as the DP numerical reference. On the unchanged
tiny example the earlier 0.125 gap disappears: horizon-aware S=1 and DP both
cost 2.875; naive S=1 costs 3.000.
This is not a data-limited learned baseline or a reproduced published method.
The broader baselines below remain planned.

1. Tuned adaptive / capped base-stock.
2. Simple Bayesian demand model plus optimization.
3. GP + MPC.
4. GP + DCL with ordinary posterior sampling.
5. Generic Bayesian or robust safe policy improvement.
6. TED / HDPO where formulations and access permit fair reimplementation.
7. Neural-ensemble uncertainty replacement for GP.

Critical ablation: identical GP, DCL, data and compute; change **only** the proposed decision-sensitive safeguard. Compare known-model and data-limited DCL separately.
