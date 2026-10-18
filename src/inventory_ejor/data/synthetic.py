"""Bounded iid synthetic observations with an explicit known law; no real data."""

from __future__ import annotations

import random

from inventory_ejor.demand import FiniteDemand

from .contracts import integer


def sample_iid(support, probabilities, length: int, seed: int):
    integer(length, "length")
    integer(seed, "seed", 0)
    if length > 10_000:
        raise ValueError("M3 generator limited to 10000 observations")
    law = FiniteDemand(support, probabilities)
    rng = random.Random(seed)
    values = tuple(rng.choices(law.support, weights=law.probabilities, k=length))
    return values, {
        "kind": "synthetic_known_iid",
        "support": list(law.support),
        "probabilities": list(law.probabilities),
        "seed": seed,
        "generator": "python.random.Random.choices",
        "length": length,
        "real_observations": 0,
        "synthetic_observations": length,
    }
