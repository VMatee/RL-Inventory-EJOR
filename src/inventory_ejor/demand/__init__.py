"""Known iid finite-support demand for the M2 engineering reference."""

import math
from dataclasses import dataclass, field
from numbers import Real

from inventory_ejor.envs.lost_sales import _count

PROBABILITY_TOLERANCE = 1e-12


@dataclass(frozen=True)
class FiniteDemand:
    """Unique integer support; roundoff-only normalization within 1e-12.

    Zero-probability entries are retained but never expanded. This law is
    known and iid across periods, not a fitted model or a real-data budget.
    """

    support: tuple[int, ...]
    probabilities: tuple[float, ...]
    input_mass: float = field(init=False)

    def __post_init__(self) -> None:
        support = tuple(_count(d, "demand support") for d in self.support)
        raw = tuple(self.probabilities)
        if not support or len(support) != len(raw):
            raise ValueError("nonempty support and matching probabilities required")
        if len(set(support)) != len(support):
            raise ValueError("demand support must be unique")
        if any(isinstance(p, bool) or not isinstance(p, Real) for p in raw):
            raise TypeError("probabilities must be real numbers, not bool/strings")
        probabilities = tuple(float(p) for p in raw)
        if any(not math.isfinite(p) or p < 0 for p in probabilities):
            raise ValueError("probabilities must be finite and nonnegative")
        mass = math.fsum(probabilities)
        if mass <= 0 or abs(mass - 1) > PROBABILITY_TOLERANCE:
            raise ValueError("probability mass must sum to one within 1e-12")
        object.__setattr__(self, "support", support)
        object.__setattr__(self, "input_mass", mass)
        object.__setattr__(
            self, "probabilities", tuple(p / mass for p in probabilities)
        )

    @property
    def outcomes(self) -> tuple[tuple[int, float], ...]:
        return tuple(
            (d, p)
            for d, p in zip(self.support, self.probabilities, strict=True)
            if p > 0
        )
