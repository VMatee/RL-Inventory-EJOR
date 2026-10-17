"""Exact finite-horizon iid DP, solved using floating-point expectations.

Reachability covers every admissible action and positive-probability demand.
No stock truncation. The M1 transition is unchanged; V(0, s) = 0 for all s.
Policies receive only (periods_remaining, after_receipt_state).
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from inventory_ejor.demand import FiniteDemand
from inventory_ejor.envs import (
    InventoryConfig,
    InventoryState,
    transition,
    validate_state,
)
from inventory_ejor.envs.lost_sales import _count

Policy = Callable[[int, InventoryState], int]
Key = tuple[int, InventoryState]
VALUE_TOLERANCE = 1e-10  # validation only; never used to select a worse action


class ResourceLimitError(RuntimeError):
    """An incomplete computation is rejected, never returned as optimal."""


@dataclass(frozen=True)
class ResourceLimits:
    max_states: int = 10000
    max_transitions: int = 200000
    max_seconds: float = 30.0

    def __post_init__(self) -> None:
        for name in ("max_states", "max_transitions"):
            value = _count(getattr(self, name), name)
            if value < 1:
                raise ValueError(f"{name} must be positive")
            object.__setattr__(self, name, value)
        if (
            isinstance(self.max_seconds, bool)
            or not isinstance(self.max_seconds, (int, float))
            or not math.isfinite(self.max_seconds)
            or not 0 < self.max_seconds <= 120
        ):
            raise ValueError("max_seconds must be finite and in (0, 120]")


class _Budget:
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.started = time.monotonic()
        self.states = 0
        self.transitions = 0

    def check(self) -> None:
        if time.monotonic() - self.started >= self.limits.max_seconds:
            raise ResourceLimitError("time limit exceeded; no solution returned")

    def state(self) -> None:
        self.check()
        self.states += 1
        if self.states > self.limits.max_states:
            raise ResourceLimitError(
                "state limit exceeded; no stock truncation performed"
            )

    def step(self, config, state, order, demand):
        self.check()
        self.transitions += 1
        if self.transitions > self.limits.max_transitions:
            raise ResourceLimitError("transition limit exceeded; no solution returned")
        return transition(config, state, order, demand)


@dataclass(frozen=True)
class Diagnostics:
    decision_states: int
    transition_calls: int


@dataclass(frozen=True)
class DPResult:
    expected_cost: float
    values: Mapping[Key, float]
    actions: Mapping[Key, int]
    diagnostics: Diagnostics

    def action(self, remaining: int, state: InventoryState) -> int:
        remaining = _count(remaining, "remaining")
        if remaining < 1:
            raise ValueError("no decision at terminal time")
        return self.actions[remaining, state]  # unknown state fails, never clips


@dataclass(frozen=True)
class PolicyEvaluation:
    expected_cost: float
    diagnostics: Diagnostics


def _validate(config, initial, demand, limits):
    validate_state(config, initial)
    if not isinstance(demand, FiniteDemand):
        raise TypeError("demand must be FiniteDemand")
    if not isinstance(limits, ResourceLimits):
        raise TypeError("limits must be ResourceLimits")


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise OverflowError("expected cost is not finite")
    return value


def solve_dp(
    config: InventoryConfig,
    initial: InventoryState,
    demand: FiniteDemand,
    limits: ResourceLimits | None = None,
) -> DPResult:
    """Return the adaptive optimum from initial, including all reachable keys.

    Keys include time remaining. Ascending action order and strict improvement
    select the smallest action on exactly equal computed costs; near ties are
    not rounded. Terminal states are implicit and not counted/materialized.
    """
    limits = ResourceLimits() if limits is None else limits
    _validate(config, initial, demand, limits)
    budget = _Budget(limits)
    budget.state()
    layers = [{initial: None}]
    outcomes = demand.outcomes
    for _ in range(config.horizon - 1):
        following = {}
        for state in layers[-1]:
            for q in range(config.max_order + 1):
                for d, _prob in outcomes:
                    nxt = budget.step(config, state, q, d).next_state
                    if nxt not in following:
                        budget.state()
                        following[nxt] = None
        layers.append(following)

    values, actions = {}, {}
    for t in reversed(range(config.horizon)):
        remaining = config.horizon - t
        for state in layers[t]:
            best, chosen = math.inf, 0
            for q in range(config.max_order + 1):
                terms = []
                for d, prob in outcomes:
                    step = budget.step(config, state, q, d)
                    continuation = (
                        values[remaining - 1, step.next_state] if remaining > 1 else 0.0
                    )
                    terms.append(prob * _finite(step.costs.total + continuation))
                cost = _finite(math.fsum(terms))
                if cost < best:
                    best, chosen = cost, q
            values[remaining, state] = best
            actions[remaining, state] = chosen
    budget.check()
    return DPResult(
        values[config.horizon, initial],
        MappingProxyType(values),
        MappingProxyType(actions),
        Diagnostics(budget.states, budget.transitions),
    )


def _evaluate(config, initial, demand, policy, budget):
    # Forward probability propagation, not Bellman minimization. Invoke a
    # deterministic policy once per decision state, BEFORE branching on demand.
    before_states, before_steps = budget.states, budget.transitions
    budget.state()
    distribution = {initial: 1.0}
    total = 0.0
    outcomes = demand.outcomes
    for remaining in range(config.horizon, 0, -1):
        following = {}
        period_terms = []
        for state, mass in distribution.items():
            budget.check()
            q = _count(policy(remaining, state), "policy order")
            if q > config.max_order:
                raise ValueError("policy order exceeds max_order")
            for d, prob in outcomes:
                step = budget.step(config, state, q, d)
                weight = mass * prob
                if weight == 0:
                    raise ArithmeticError(
                        "path probability underflow; no solution returned"
                    )
                period_terms.append(weight * step.costs.total)
                if remaining > 1:
                    nxt = step.next_state
                    if nxt not in following:
                        budget.state()
                        following[nxt] = 0.0
                    following[nxt] += weight
        total = _finite(total + math.fsum(period_terms))
        distribution = following
    budget.check()
    return PolicyEvaluation(
        total,
        Diagnostics(budget.states - before_states, budget.transitions - before_steps),
    )


def evaluate_policy(
    config: InventoryConfig,
    initial: InventoryState,
    demand: FiniteDemand,
    policy: Policy,
    limits: ResourceLimits | None = None,
) -> PolicyEvaluation:
    """Exactly enumerate a deterministic Markov policy under the known iid law."""
    limits = ResourceLimits() if limits is None else limits
    _validate(config, initial, demand, limits)
    return _evaluate(config, initial, demand, policy, _Budget(limits))


def cost_gap(cost: float, reference: float) -> dict[str, float | None]:
    """Absolute gap always; relative gap undefined when reference is zero."""
    if not all(math.isfinite(v) and v >= 0 for v in (cost, reference)):
        raise ValueError("costs must be finite and nonnegative")
    difference = cost - reference
    return {
        "absolute": difference,
        "relative": difference / reference if reference > 0 else None,
    }
