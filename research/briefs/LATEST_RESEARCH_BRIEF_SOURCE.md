# Latest research brief: source and status

Source: user-provided Thai research strategy in the conversation, 397 lines (2026-10-17). The original source remains in the conversation and should be consulted as the authoritative detailed brief; this file is a faithful **summary**, not a verbatim copy.

Working title: When Is Limited Demand Data Enough? Decision-Sensitive Policy Learning for Inventory Control.

Core: limited demand history -> GP posterior -> inventory simulator with known dynamics -> neural policy improvement guarded by decision-sensitive uncertainty in the cost difference against a baseline.

Three proposed contributions: inventory-structured uncertainty of policy differences; safeguard against model exploitation; decision-relevant data sufficiency.

Evaluation: controlled synthetic/DP; M5 with n=28,56,112,224; Favorita external validation. Strong baselines include tuned base-stock, Bayesian simple-model optimization, GP+MPC, GP+DCL, robust policy improvement, TED/HDPO where compatible, neural ensemble. Main metric is cost-data frontier; report tail losses, deterioration rates, non-inferiority and uncertainty calibration.

Important caveats: sales are not necessarily uncensored demand; simulator costs/lead times are scenario assumptions; proposed guarantees are unproved; pretraining and hyperparameter data must be disclosed.
