"""Deterministic, auditable stock-flow kernel for M1 lost-sales inventory.

Decision epochs are AFTER current-period receipts and BEFORE order/demand.
An order at t arrives at the beginning of t + L, for any L >= 1.
See theory/INVENTORY_MODEL.md. No forecast or GP/RL code lives here.
"""

from __future__ import annotations

import math
import operator
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# All inventory counts are exactly representable in float64 observations.
MAX_EXACT_UNITS = 2**53


def _count(value: object, label: str) -> int:
    """Require a nonnegative integer, not a float, boolean or silent rounding."""
    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{label} must be a nonnegative integer, not boolean")
    try:
        result = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"{label} must be a nonnegative integer") from exc
    if result < 0 or result > MAX_EXACT_UNITS:
        raise ValueError(f"{label} must be between 0 and {MAX_EXACT_UNITS}")
    return int(result)


def _nonnegative_money(value: object, label: str) -> float:
    """Validate finite, nonnegative scenario parameters."""
    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{label} must be a finite nonnegative real number")
    try:
        result = float(value)  # supports numeric scalars including np.float64
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"{label} must be a finite nonnegative real number") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label} must be a finite nonnegative real number")
    return result


@dataclass(frozen=True)
class CostParameters:
    """Scenario costs, NOT measured retailer accounting data."""

    holding: float
    lost_sales: float
    variable_order: float
    fixed_order: float

    def __post_init__(self) -> None:
        for label in ("holding", "lost_sales", "variable_order", "fixed_order"):
            object.__setattr__(
                self, label, _nonnegative_money(getattr(self, label), label)
            )


@dataclass(frozen=True)
class InventoryConfig:
    """Positive known lead time and finite-horizon inventory experiment."""

    lead_time: int
    horizon: int
    max_order: int
    costs: CostParameters

    def __post_init__(self) -> None:
        lead = _count(self.lead_time, "lead_time")
        horizon = _count(self.horizon, "horizon")
        if lead < 1 or horizon < 1:
            raise ValueError("lead_time and horizon must be positive")
        object.__setattr__(self, "lead_time", lead)
        object.__setattr__(self, "horizon", horizon)
        object.__setattr__(self, "max_order", _count(self.max_order, "max_order"))
        if not isinstance(self.costs, CostParameters):
            raise TypeError("costs must be CostParameters")


@dataclass(frozen=True)
class InventoryState:
    """Stock AFTER current receipt; pipeline is due in t+1,...,t+L-1."""

    on_hand: int
    pipeline: tuple[int, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "on_hand", _count(self.on_hand, "on_hand"))
        if not isinstance(self.pipeline, tuple):
            raise TypeError("pipeline must be a tuple of nonnegative integers")
        object.__setattr__(
            self,
            "pipeline",
            tuple(_count(v, f"pipeline[{i}]") for i, v in enumerate(self.pipeline)),
        )


def validate_state(config: InventoryConfig, state: InventoryState) -> None:
    if not isinstance(config, InventoryConfig):
        raise TypeError("config must be InventoryConfig")
    if not isinstance(state, InventoryState):
        raise TypeError("state must be InventoryState")
    expected = config.lead_time - 1
    if len(state.pipeline) != expected:
        raise ValueError(
            f"pipeline length {len(state.pipeline)} != L-1 ({expected})"
        )


@dataclass(frozen=True)
class StepCosts:
    holding: float
    lost_sales: float
    variable_order: float
    fixed_order: float

    @property
    def total(self) -> float:
        return self.holding + self.lost_sales + self.variable_order + self.fixed_order


@dataclass(frozen=True)
class StepOutcome:
    prior_state: InventoryState
    next_state: InventoryState
    order: int
    demand: int
    sales: int
    lost_units: int
    ending_on_hand: int
    next_period_receipt: int
    outstanding_after_order: tuple[int, ...]
    costs: StepCosts

    @property
    def reward(self) -> float:
        return -self.costs.total


def transition(
    config: InventoryConfig,
    state: InventoryState,
    order: int,
    demand: int,
) -> StepOutcome:
    """Pure one-period deterministic transition, suitable for small-state DP.

    The demand argument is observed by the simulator after order selection;
    it is NOT information available to the policy when it chooses order.
    """
    validate_state(config, state)
    q = _count(order, "order")
    d = _count(demand, "demand")
    if q > config.max_order:
        raise ValueError(f"order {q} exceeds max_order {config.max_order}")

    sales = min(state.on_hand, d)
    lost_units = d - sales
    end = state.on_hand - sales

    # The pipeline at the end of period t has L batches, including q_t.
    outstanding = state.pipeline + (q,)
    next_receipt = outstanding[0]
    new_on_hand = end + next_receipt
    if new_on_hand > MAX_EXACT_UNITS:
        raise OverflowError("next on-hand exceeds exactly representable units")
    next_state = InventoryState(
        on_hand=new_on_hand, pipeline=outstanding[1:]
    )
    cost = config.costs
    breakdown = StepCosts(
        holding=cost.holding * end,
        lost_sales=cost.lost_sales * lost_units,
        variable_order=cost.variable_order * q,
        fixed_order=cost.fixed_order if q > 0 else 0.0,
    )
    if not all(
        math.isfinite(v)
        for v in (
            breakdown.holding,
            breakdown.lost_sales,
            breakdown.variable_order,
            breakdown.fixed_order,
            breakdown.total,
        )
    ):
        raise OverflowError("cost is not finite")
    return StepOutcome(
        prior_state=state,
        next_state=next_state,
        order=q,
        demand=d,
        sales=sales,
        lost_units=lost_units,
        ending_on_hand=end,
        next_period_receipt=next_receipt,
        outstanding_after_order=outstanding,
        costs=breakdown,
    )


def default_state(config: InventoryConfig, initial_on_hand: int = 0) -> InventoryState:
    return InventoryState(
        on_hand=initial_on_hand,
        pipeline=(0,) * (config.lead_time - 1),
    )


def simulate_fixed_actions(
    config: InventoryConfig,
    demand_trace: Sequence[int],
    orders: Sequence[int],
    initial_state: InventoryState | None = None,
) -> tuple[StepOutcome, ...]:
    """Deterministic *fixture* evaluator, not a policy that sees future demand."""
    demands = tuple(_count(d, "demand") for d in demand_trace)
    actions = tuple(_count(q, "order") for q in orders)
    if len(demands) != config.horizon or len(actions) != config.horizon:
        raise ValueError("demand_trace and orders must both match horizon")
    state = default_state(config) if initial_state is None else initial_state
    validate_state(config, state)
    outcomes: list[StepOutcome] = []
    for q, d in zip(actions, demands):
        outcome = transition(config, state, q, d)
        outcomes.append(outcome)
        state = outcome.next_state
    return tuple(outcomes)


class LostSalesInventoryEnv(gym.Env[np.ndarray, int]):
    """Gymnasium environment for deterministic exogenous demand traces (M1).

    Observation [on_hand, pending_due_t+1, ..., pending_due_t+L-1,
                 periods_remaining] has length L+1 and dtype float64.

    Reward is negative per-period operating cost. A known finite horizon is
    an MDP terminal event (terminated=True, truncated=False). There is zero
    additional terminal cost, salvage or disposal.
    """

    metadata: ClassVar[dict[str, list[str]]] = {"render_modes": []}

    def __init__(
        self,
        config: InventoryConfig,
        demand_trace: Sequence[int],
        initial_state: InventoryState | None = None,
    ) -> None:
        super().__init__()
        if not isinstance(config, InventoryConfig):
            raise TypeError("config must be InventoryConfig")
        demands = tuple(_count(d, "demand") for d in demand_trace)
        if len(demands) != config.horizon:
            raise ValueError("demand_trace length must equal horizon")
        state = default_state(config) if initial_state is None else initial_state
        validate_state(config, state)

        self.config = config
        self._demand_trace = demands   # simulator-only exogenous trace
        self._initial_state = state
        self._state = state
        self._t = 0
        self._episode_cost = 0.0

        self.action_space = spaces.Discrete(config.max_order + 1)
        self.observation_space = spaces.Box(
            low=0.0,
            high=float(MAX_EXACT_UNITS),
            shape=(config.lead_time + 1,),
            dtype=np.float64,
        )

    @property
    def state(self) -> InventoryState:
        return self._state

    @property
    def period(self) -> int:
        return self._t

    @property
    def episode_cost(self) -> float:
        return self._episode_cost

    def _observation(self) -> np.ndarray:
        return np.asarray(
            (self._state.on_hand, *self._state.pipeline, self.config.horizon - self._t),
            dtype=np.float64,
        )

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        if options not in (None, {}):
            raise ValueError("M1 reset options are not supported")
        self._state = self._initial_state
        self._t = 0
        self._episode_cost = 0.0
        return self._observation(), {}

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        if self._t >= self.config.horizon:
            raise RuntimeError("episode ended; call reset() before step()")
        # action is validated before state mutation.
        outcome = transition(
            self.config, self._state, action, self._demand_trace[self._t]
        )
        prev_period = self._t
        self._state = outcome.next_state
        self._t += 1
        self._episode_cost += outcome.costs.total
        terminated = self._t == self.config.horizon
        info = {
            "period": prev_period,
            "order": outcome.order,
            "demand": outcome.demand,  # just realized; NEVER future trace
            "sales": outcome.sales,
            "lost_units": outcome.lost_units,
            "ending_on_hand": outcome.ending_on_hand,  # before next receipt
            "next_period_receipt": outcome.next_period_receipt,
            "outstanding_after_order": outcome.outstanding_after_order,
            "cost_holding": outcome.costs.holding,
            "cost_lost_sales": outcome.costs.lost_sales,
            "cost_variable_order": outcome.costs.variable_order,
            "cost_fixed_order": outcome.costs.fixed_order,
            "cost_total": outcome.costs.total,
            "cumulative_cost": self._episode_cost,
        }
        if terminated:
            info["terminal_snapshot"] = {
                "ending_on_hand_before_next_receipt": outcome.ending_on_hand,
                "outstanding_receipts": outcome.outstanding_after_order,
                "additional_terminal_cost": 0.0,
            }
        return self._observation(), outcome.reward, terminated, False, info
