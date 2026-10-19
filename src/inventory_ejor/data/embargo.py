"""Additional outcome-to-future-history embargo for nonadaptive research phases.

The M3 SplitPlan rejects overlapping evaluation windows but, by design,
does not prohibit reuse of a previous window's observed outcomes as the
history at a later origin. That is NOT acceptable for a deliberately
nonadaptive held-out comparison, even if the two evaluation windows are
disjoint. This pure helper reads no data and authorizes no experiment.
"""

from __future__ import annotations

from .contracts import Window, integer


def validate_nonadaptive_origin_embargo(
    origins: tuple[int, ...],
    *,
    largest_history: int,
    horizon: int,
) -> None:
    """Reject any later history overlapping any earlier evaluation window."""
    integer(largest_history, "largest_history")
    integer(horizon, "horizon")
    if not isinstance(origins, tuple) or not origins:
        raise ValueError("Origin sequence must be a nonempty tuple")
    if tuple(sorted(set(origins))) != origins:
        raise ValueError("Origins must be increasing and unique")
    outcomes = []
    for origin in origins:
        integer(origin, "origin")
        history = Window(origin - largest_history, origin)
        for old in outcomes:
            if old.start < history.stop and history.start < old.stop:
                raise ValueError(
                    "Nonadaptive holdout embargo: later history includes "
                    "an earlier reserved evaluation outcome"
                )
        outcomes.append(Window(origin, origin + horizon))
