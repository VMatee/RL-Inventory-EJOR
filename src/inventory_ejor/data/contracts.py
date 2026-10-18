"""Immutable learner/evaluator views and chronological information boundaries."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

BUDGETS = (28, 56, 112, 224)
ROLES = ("development", "calibration", "validation", "final_test")


def integer(value, name, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def exact_keys(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{name} requires exactly {sorted(keys)}")


@dataclass(frozen=True)
class Window:
    """Half-open M5 day indices [start, stop); day 1 is the first CSV day."""

    start: int
    stop: int

    def __post_init__(self):
        integer(self.start, "start")
        integer(self.stop, "stop")
        if self.stop <= self.start:
            raise ValueError("empty/reversed window")

    def contains(self, other: Window) -> bool:
        return self.start <= other.start and other.stop <= self.stop

    @property
    def days(self):
        return tuple(range(self.start, self.stop))


@dataclass(frozen=True)
class Phase:
    role: str
    window: Window

    def __post_init__(self):
        if self.role not in ROLES or not isinstance(self.window, Window):
            raise ValueError("invalid phase")


@dataclass(frozen=True)
class SplitPlan:
    """Separate phase contexts as well as outcomes; no reuse across phases."""

    phases: tuple[Phase, ...]
    horizon: int
    budgets: tuple[int, ...] = BUDGETS

    def __post_init__(self):
        integer(self.horizon, "horizon")
        if type(self.phases) is not tuple or not self.phases:
            raise ValueError("phases must be a nonempty immutable tuple")
        if type(self.budgets) is not tuple or not self.budgets:
            raise ValueError("budgets must be a nonempty tuple")
        for n in self.budgets:
            integer(n, "budget")
        if tuple(sorted(set(self.budgets))) != self.budgets:
            raise ValueError("budgets must be increasing and unique")
        if any(not isinstance(p, Phase) for p in self.phases):
            raise ValueError("invalid phase object")
        ranks = [ROLES.index(p.role) for p in self.phases]
        if ranks != sorted(set(ranks)):
            raise ValueError("phases must be unique and chronologically ordered")
        for left, right in zip(self.phases, self.phases[1:], strict=False):
            if left.window.stop > right.window.start:
                raise ValueError("phase overlap")

    def windows(self, role: str, origin: int, budget: int):
        integer(origin, "origin")
        integer(budget, "budget")
        if budget not in self.budgets:
            raise ValueError("undeclared history budget")
        phase = next((p for p in self.phases if p.role == role), None)
        if phase is None:
            raise ValueError("undeclared phase")
        # Require all budgets to be feasible at every origin for a common cohort.
        runway = Window(origin - max(self.budgets), origin + self.horizon)
        if not phase.window.contains(runway):
            raise ValueError("history/outcomes cross phase boundary")
        return Window(origin - budget, origin), Window(origin, origin + self.horizon)

    def validate_origins(self, role: str, origins: tuple[int, ...]):
        if not origins or tuple(sorted(set(origins))) != origins:
            raise ValueError("origins must be nonempty, increasing and unique")
        for origin in origins:
            self.windows(role, origin, self.budgets[0])
        if any(
            b < a + self.horizon for a, b in zip(origins, origins[1:], strict=False)
        ):
            raise ValueError("overlapping outcome windows require a separate protocol")


@dataclass(frozen=True)
class Observation:
    day: int
    date: str
    sales: int

    def __post_init__(self):
        integer(self.day, "day")
        integer(self.sales, "sales", 0)
        parsed = date.fromisoformat(self.date)
        if parsed.isoformat() != self.date:
            raise ValueError("date must be canonical ISO date")


def check_observations(observations, window):
    if type(observations) is not tuple or not all(
        isinstance(o, Observation) for o in observations
    ):
        raise ValueError("observations must be an immutable tuple")
    if tuple(o.day for o in observations) != window.days:
        raise ValueError("missing, duplicate or unordered observation days")
    for a, b in zip(observations, observations[1:], strict=False):
        if date.fromisoformat(b.date) - date.fromisoformat(a.date) != timedelta(days=1):
            raise ValueError("dates are not consecutive")


@dataclass(frozen=True)
class History:
    dataset: str
    series: str
    origin: int
    observations: tuple[Observation, ...]

    def __post_init__(self):
        integer(self.origin, "origin")
        if not self.dataset or not self.series or not self.observations:
            raise ValueError("history requires dataset, series and observations")
        check_observations(self.observations, self.window)

    @property
    def window(self):
        return Window(self.origin - len(self.observations), self.origin)


@dataclass(frozen=True)
class EvaluationTargets:
    """Evaluator-only object; never passed to a learner or normalization fitter."""

    dataset: str
    series: str
    window: Window
    observations: tuple[Observation, ...]

    def __post_init__(self):
        if not self.dataset or not self.series:
            raise ValueError("targets require dataset and series")
        check_observations(self.observations, self.window)


@dataclass(frozen=True)
class Normalization:
    mean: float
    scale: float
    fitted_days: tuple[int, ...]


def fit_normalization(history: History, allowed: Window) -> Normalization:
    """Population mean/std of explicitly allowed training days; never impute."""
    if type(history) is not History or not history.window.contains(allowed):
        raise ValueError("normalization requires a training-only history window")
    values = [o.sales for o in history.observations if o.day in allowed.days]
    mean = math.fsum(values) / len(values)
    scale = math.sqrt(math.fsum((v - mean) ** 2 for v in values) / len(values))
    return Normalization(mean, scale or 1.0, allowed.days)


@dataclass(frozen=True)
class Feature:
    name: str
    day: int
    available_day: int
    value: float
    evidence: str

    def __post_init__(self):
        integer(self.day, "feature day")
        integer(self.available_day, "availability day", 0)
        if not self.name or not self.evidence or isinstance(self.value, bool):
            raise ValueError("feature name and availability evidence required")
        if not isinstance(self.value, (float, int)) or not math.isfinite(self.value):
            raise ValueError("feature must be finite numeric")


def features_at(features: tuple[Feature, ...], decision_day: int):
    """Strict join: unavailable requested features are errors, not silent fills."""
    integer(decision_day, "decision day")
    keys = [(f.name, f.day) for f in features]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate feature join key")
    if any(f.available_day > decision_day for f in features):
        raise ValueError("feature unavailable at decision time")
    return features
