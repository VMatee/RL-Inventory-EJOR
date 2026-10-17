"""Naive constant and horizon-aware base-stock; known-model grid tuning."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from inventory_ejor.demand import FiniteDemand
from inventory_ejor.envs import InventoryConfig, InventoryState, validate_state
from inventory_ejor.envs.lost_sales import _count
from inventory_ejor.solvers.finite_horizon import (
    Diagnostics,
    PolicyEvaluation,
    ResourceLimitError,
    ResourceLimits,
    _Budget,
    _evaluate,
    _validate,
)


@dataclass(frozen=True)
class BaseStockPolicy:
    """Naive comparator: q=min(Q_max, max(0, S-x-sum(p))) at every period."""

    config: InventoryConfig
    level: int

    def __post_init__(self):
        if not isinstance(self.config, InventoryConfig):
            raise TypeError("config must be InventoryConfig")
        object.__setattr__(self, "level", _count(self.level, "base-stock level"))

    def __call__(self, remaining: int, state: InventoryState) -> int:
        validate_state(self.config, state)
        if not 1 <= _count(remaining, "remaining") <= self.config.horizon:
            raise ValueError("remaining must be within the decision horizon")
        position = state.on_hand + sum(state.pipeline)
        return min(self.config.max_order, max(0, self.level - position))


class HorizonAwareBaseStockPolicy(BaseStockPolicy):
    """Constant S while receipts can still serve demand; otherwise order zero.

    An order with remaining <= L arrives at or after T, outside the evaluated
    demand periods. The cutoff uses only known time remaining and lead time.
    Nonnegative placement costs and zero terminal value make such orders
    unnecessary. This does not claim optimality of constant S before cutoff.
    """

    def __call__(self, remaining: int, state: InventoryState) -> int:
        order = super().__call__(remaining, state)  # validate even at cutoff
        return 0 if remaining <= self.config.lead_time else order


@dataclass(frozen=True)
class TuningResult:
    policy: BaseStockPolicy
    evaluations: Mapping[int, PolicyEvaluation]
    diagnostics: Diagnostics

    @property
    def expected_cost(self):
        return self.evaluations[self.policy.level].expected_cost


def tune_base_stock(
    config: InventoryConfig,
    initial: InventoryState,
    demand: FiniteDemand,
    levels: Iterable[int],
    limits: ResourceLimits | None = None,
    *,
    horizon_aware: bool = False,
) -> TuningResult:
    """Known-model tuning on a finite supplied grid; ties pick smallest S.

    horizon_aware=False preserves the original naive constant comparator.
    True adds the known-time cutoff; each call tunes that variant separately.
    Limits apply cumulatively across the grid. No claim of optimality outside
    this grid, among time-varying levels, or among all lost-sales policies.
    """
    limits = ResourceLimits() if limits is None else limits
    _validate(config, initial, demand, limits)
    if not isinstance(horizon_aware, bool):
        raise TypeError("horizon_aware must be boolean")
    policy_type = HorizonAwareBaseStockPolicy if horizon_aware else BaseStockPolicy
    budget = _Budget(limits)
    grid = set()
    for level in levels:
        budget.check()
        grid.add(_count(level, "base-stock level"))
        if len(grid) > limits.max_states:
            raise ResourceLimitError("tuning grid exceeds state budget")
    if not grid:
        raise ValueError("base-stock grid must be nonempty")
    evaluations = {}
    for level in sorted(grid):
        evaluations[level] = _evaluate(
            config, initial, demand, policy_type(config, level), budget
        )
    chosen = min(evaluations, key=lambda s: (evaluations[s].expected_cost, s))
    return TuningResult(
        policy_type(config, chosen),
        MappingProxyType(evaluations),
        Diagnostics(budget.states, budget.transitions),
    )
