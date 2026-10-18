"""Batched predictive scenario costs and horizon-aware inventory policies.

Numerical routines are prepared but have NOT been executed/validated in this
preparation task. Future numerical validation must compare both backends with
M1 before any scientific baseline run. No clairvoyant future action optimization:
rollouts use a fixed base-stock rule responding only to simulated past sales.
"""

from __future__ import annotations


def numpy_costs(paths, scenario, state, levels, first_orders=None):
    import numpy as np

    paths = np.asarray(paths)
    if paths.dtype.kind not in "iu" or (paths > 2**53).any():
        raise ValueError(
            "Predictive counts must be exact integers; no rounding or truncation"
        )
    paths = paths.astype(np.int64, copy=False)
    if paths.ndim != 2 or not paths.shape[0] or not paths.shape[1] or (paths < 0).any():
        raise ValueError(
            "Predictive paths must be nonempty nonnegative [paths,horizon]"
        )
    levels = np.asarray(levels)
    if (
        levels.ndim != 1
        or not levels.size
        or levels.dtype.kind not in "iu"
        or (levels < 0).any()
        or (levels > 2**53).any()
    ):
        raise ValueError("Nonempty nonnegative integer level grid required")
    levels = levels.astype(np.int64, copy=False)
    if len(state.pipeline) != scenario["lead_time"] - 1:
        raise ValueError("State pipeline must match positive lead time")
    if first_orders is not None:
        first_orders = np.asarray(first_orders)
        if (
            first_orders.shape != levels.shape
            or first_orders.dtype.kind not in "iu"
            or (first_orders < 0).any()
            or (first_orders > scenario["max_order"]).any()
        ):
            raise ValueError(
                "Each first-order candidate must be an integer within the action bound"
            )
    candidates, samples = len(levels), len(paths)
    horizon = paths.shape[1]
    lead = scenario["lead_time"]
    stock = np.full((candidates, samples), state.on_hand, dtype=np.int64)
    pipeline = np.broadcast_to(
        np.asarray(state.pipeline, dtype=np.int64), (candidates, samples, lead - 1)
    ).copy()
    totals = np.zeros((candidates, samples), dtype=np.float64)
    costs = scenario["costs"]
    for t in range(horizon):
        if horizon - t <= lead:
            q = np.zeros_like(stock)
        elif t == 0 and first_orders is not None:
            q = np.broadcast_to(
                np.asarray(first_orders, dtype=np.int64)[:, None], stock.shape
            )
        else:
            q = np.clip(
                levels[:, None] - stock - pipeline.sum(axis=-1),
                0,
                scenario["max_order"],
            )
        d = paths[:, t][None, :]
        sales = np.minimum(stock, d)
        ending, lost = stock - sales, d - sales
        totals += (
            costs["holding"] * ending
            + costs["lost_sales"] * lost
            + costs["variable_order"] * q
            + costs["fixed_order"] * (q > 0)
        )
        if lead == 1:
            stock = ending + q
        else:
            stock = ending + pipeline[:, :, 0]
            pipeline = np.concatenate((pipeline[:, :, 1:], q[:, :, None]), axis=-1)
    if not np.isfinite(totals).all():
        raise FloatingPointError("Nonfinite simulated cost")
    return totals.mean(axis=1)


def torch_costs(paths, scenario, state, levels, first_orders=None):
    import torch

    if (
        paths.dtype != torch.int64
        or paths.ndim != 2
        or min(paths.shape) < 1
        or (paths < 0).any().item()
        or (paths > 2**53).any().item()
    ):
        raise ValueError("Predictive paths must be nonnegative int64 [paths,horizon]")
    device = paths.device
    levels = torch.as_tensor(levels, device=device)
    if (
        levels.dtype != torch.int64
        or levels.ndim != 1
        or not levels.numel()
        or (levels < 0).any().item()
        or (levels > 2**53).any().item()
    ):
        raise ValueError("Nonempty nonnegative int64 level grid required")
    if len(state.pipeline) != scenario["lead_time"] - 1:
        raise ValueError("State pipeline must match positive lead time")
    if first_orders is not None:
        first_orders = torch.as_tensor(first_orders, device=device)
        if (
            first_orders.dtype != torch.int64
            or first_orders.shape != levels.shape
            or (first_orders < 0).any().item()
            or (first_orders > scenario["max_order"]).any().item()
        ):
            raise ValueError("First-order candidates must be valid int64 actions")
    candidates, samples = len(levels), len(paths)
    horizon = paths.shape[1]
    lead = scenario["lead_time"]
    stock = torch.full(
        (candidates, samples), state.on_hand, dtype=torch.int64, device=device
    )
    pipeline = (
        torch.tensor(state.pipeline, dtype=torch.int64, device=device)
        .expand(candidates, samples, lead - 1)
        .clone()
    )
    totals = torch.zeros((candidates, samples), dtype=torch.float64, device=device)
    costs = scenario["costs"]
    for t in range(horizon):
        if horizon - t <= lead:
            q = torch.zeros_like(stock)
        elif t == 0 and first_orders is not None:
            q = torch.as_tensor(first_orders, dtype=torch.int64, device=device)[
                :, None
            ].expand_as(stock)
        else:
            q = (levels[:, None] - stock - pipeline.sum(dim=-1)).clamp(
                0, scenario["max_order"]
            )
        d = paths[:, t].unsqueeze(0)
        sales = torch.minimum(stock, d)
        ending, lost = stock - sales, d - sales
        totals += (
            costs["holding"] * ending
            + costs["lost_sales"] * lost
            + costs["variable_order"] * q
            + costs["fixed_order"] * (q > 0)
        )
        if lead == 1:
            stock = ending + q
        else:
            stock = ending + pipeline[:, :, 0]
            pipeline = torch.cat((pipeline[:, :, 1:], q.unsqueeze(-1)), dim=-1)
    if not torch.isfinite(totals).all().item():
        raise FloatingPointError("Nonfinite simulated cost")
    return totals.mean(dim=1)


def order_up_to(remaining, state, level, scenario):
    if remaining <= scenario["lead_time"]:
        return 0
    return max(
        0, min(scenario["max_order"], level - state.on_hand - sum(state.pipeline))
    )


class PredictiveInventoryPolicy:
    """Tuned constant base stock or one-step action rollout with that base policy.

    Not DCL, not a globally solved MPC, and not the proposed research method.
    The decision-time action includes q=0..Qmax, compared on common simulated
    demand paths. All later rollout actions obey the fixed base-stock rule.
    """

    def __init__(
        self,
        sampler,
        scenario,
        levels,
        initial_state,
        horizon,
        sampling,
        seed,
        device_kind,
        use_rollout,
    ):
        self.sampler = sampler
        self.scenario = scenario
        self.horizon = horizon
        self.sampling = sampling
        self.seed = seed
        self.use_rollout = use_rollout
        self.cost_fn = torch_costs if device_kind == "gpu" else numpy_costs
        draws = sampler.draw(0, horizon, sampling["tuning_paths"], seed + 101)
        costs = self.cost_fn(draws, scenario, initial_state, levels)
        # Ascending grid + first argmin implies the smallest level on exact ties.
        index = int(costs.argmin().item())
        self.level = levels[index]
        self.tuning_costs = (
            costs.detach().cpu().tolist() if device_kind == "gpu" else costs.tolist()
        )
        self.level_at_upper_boundary = self.level == max(levels)
        self.simulated_transitions = len(levels) * sampling["tuning_paths"] * horizon
        self.simulated_paths = sampling["tuning_paths"]
        self.action_comparisons = 0
        self.level_grid_size = len(levels)

    def action(self, remaining, state):
        if remaining <= self.scenario["lead_time"]:
            return 0
        if not self.use_rollout:
            return order_up_to(remaining, state, self.level, self.scenario)
        offset = self.horizon - remaining
        # New random stream independent of tuning, same stream across compared actions.
        draws = self.sampler.draw(
            offset,
            remaining,
            self.sampling["decision_paths"],
            self.seed + 1001 + offset,
        )
        orders = list(range(self.scenario["max_order"] + 1))
        costs = self.cost_fn(
            draws, self.scenario, state, [self.level] * len(orders), orders
        )
        self.simulated_transitions += (
            len(orders) * self.sampling["decision_paths"] * remaining
        )
        self.simulated_paths += self.sampling["decision_paths"]
        self.action_comparisons += len(orders)
        return orders[int(costs.argmin().item())]
