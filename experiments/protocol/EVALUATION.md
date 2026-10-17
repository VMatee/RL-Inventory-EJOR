# Proposed evaluation protocol

Tracks: (A) synthetic demand with known distribution and small-state DP; (B) M5 historical sales-driven simulation; (C) Favorita frozen external validation.

For M5: n=28,56,112,224 days of initial history; same cutoff and future test dates for every method. Rich-data comparator may use older pre-cutoff observations but never future observations. Primary track freezes learned demand model/policy at deployment; online updating is a separate track with matched post-deployment access.

Primary endpoint: held-out inventory cost versus initial data budget. Also report holding/shortage/ordering, fill rate, tail costs, fraction/magnitude of harmful policy switches, runtime, calibration and forecast scores as diagnostics. Predefine economically motivated non-inferiority margin and use dependence-aware uncertainty intervals. Record all tuning and pretraining information.
