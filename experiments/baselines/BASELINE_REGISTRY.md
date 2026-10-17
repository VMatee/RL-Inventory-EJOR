# Baseline registry (planned, not implemented)

1. Tuned adaptive / capped base-stock.
2. Simple Bayesian demand model plus optimization.
3. GP + MPC.
4. GP + DCL with ordinary posterior sampling.
5. Generic Bayesian or robust safe policy improvement.
6. TED / HDPO where formulations and access permit fair reimplementation.
7. Neural-ensemble uncertainty replacement for GP.

Critical ablation: identical GP, DCL, data and compute; change **only** the proposed decision-sensitive safeguard. Compare known-model and data-limited DCL separately.
