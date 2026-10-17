# Proposed inventory model specification (not finalized)

Single-item, periodic-review, lost-sales inventory with known fixed lead time L. Explicitly define state as on-hand stock plus outstanding order pipeline, action as nonnegative replenishment, sales as min(available inventory, demand), unmet demand as lost, and holding/shortage/order costs as scenario parameters. Record exact within-period event ordering (arrival, order, demand, accounting), initial pipeline, terminal costs, and horizon in a formal specification before writing the simulator.

Let J_P(pi) be expected policy cost under demand process P. For learned policy pi and baseline pi_b, Delta_P(pi,pi_b) = J_P(pi) - J_P(pi_b). Negative Delta favors the learned policy. Any upper confidence/posterior bound U_n must specify coverage semantics, adaptive selection handling, and assumptions; it is not yet a proven guarantee.
