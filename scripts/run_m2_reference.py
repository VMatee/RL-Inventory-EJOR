"""Bounded synthetic M2 demonstration. Exact enumeration; no random draws.

Print JSON to stdout. For saved artifacts use run_experiment.py's unique
smoke directory; this command itself never creates/overwrites result files.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from dataclasses import asdict
from numbers import Real
from pathlib import Path

from inventory_ejor.demand import PROBABILITY_TOLERANCE, FiniteDemand
from inventory_ejor.envs import (
    CostParameters,
    InventoryConfig,
    InventoryState,
    validate_state,
)
from inventory_ejor.envs.lost_sales import _count
from inventory_ejor.policies.base_stock import tune_base_stock
from inventory_ejor.solvers.finite_horizon import (
    VALUE_TOLERANCE,
    ResourceLimitError,
    ResourceLimits,
    cost_gap,
    evaluate_policy,
    solve_dp,
)

ROOT = Path(__file__).resolve().parents[1]


def _keys(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"{name} requires exactly these keys: {sorted(expected)}")


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def parse_config(raw: bytes):
    fields = json.loads(raw, object_pairs_hook=_unique_object)
    _keys(
        fields,
        ("inventory", "initial_state", "demand", "base_stock_levels", "limits"),
        "config",
    )
    inventory = fields["inventory"]
    _keys(inventory, ("lead_time", "horizon", "max_order", "costs"), "inventory")
    _keys(
        inventory["costs"],
        ("holding", "lost_sales", "variable_order", "fixed_order"),
        "costs",
    )
    if any(
        isinstance(v, bool) or not isinstance(v, Real)
        for v in inventory["costs"].values()
    ):
        raise ValueError("costs must be JSON numbers")
    cfg = InventoryConfig(
        **{**inventory, "costs": CostParameters(**inventory["costs"])}
    )
    initial = fields["initial_state"]
    _keys(initial, ("on_hand", "pipeline"), "initial_state")
    if not isinstance(initial["pipeline"], list):
        raise ValueError("pipeline must be an array")
    state = InventoryState(initial["on_hand"], tuple(initial["pipeline"]))
    validate_state(cfg, state)
    _keys(fields["demand"], ("support", "probabilities"), "demand")
    if any(not isinstance(v, list) for v in fields["demand"].values()):
        raise ValueError("demand support/probabilities must be arrays")
    demand = FiniteDemand(**fields["demand"])
    _keys(fields["limits"], ("max_states", "max_transitions", "max_seconds"), "limits")
    limits = ResourceLimits(**fields["limits"])
    grid = fields["base_stock_levels"]
    if not isinstance(grid, list) or not grid:
        raise ValueError("base_stock_levels must be a nonempty array")
    grid = tuple(_count(v, "base-stock level") for v in grid)
    return cfg, state, demand, grid, limits


def provenance(raw: bytes):
    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.PIPE, timeout=5
        ).strip()

    # Include uncommitted/untracked implementation bytes: a base SHA alone
    # does not identify the implementation being demonstrated before review.
    files = sorted((ROOT / "src/inventory_ejor").rglob("*.py")) + [
        Path(__file__).resolve()
    ]
    return {
        "source_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=all")),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
        },
        "config_sha256": hashlib.sha256(raw).hexdigest(),
        "python": platform.python_version(),
        "dependencies": {
            name: importlib.metadata.version(name) for name in ("numpy", "gymnasium")
        },
        "data": "inline synthetic iid finite law; no real-data files or split",
    }


def demonstrate(raw: bytes):
    cfg, initial, demand, grid, limits = parse_config(raw)
    optimum = solve_dp(cfg, initial, demand, limits)
    replay = evaluate_policy(cfg, initial, demand, optimum.action, limits)
    baselines = {
        "naive_constant": tune_base_stock(
            cfg, initial, demand, grid, limits, horizon_aware=False
        ),
        "horizon_aware": tune_base_stock(
            cfg, initial, demand, grid, limits, horizon_aware=True
        ),
    }
    if abs(replay.expected_cost - optimum.expected_cost) > VALUE_TOLERANCE:
        raise ArithmeticError("returned policy does not reproduce DP value")
    if any(
        result.expected_cost + VALUE_TOLERANCE < optimum.expected_cost
        for tuned in baselines.values()
        for result in tuned.evaluations.values()
    ):
        raise ArithmeticError("admissible baseline below DP reference")
    definitions = {
        "naive_constant": "naive comparator: constant S, no horizon cutoff",
        "horizon_aware": "constant S; order zero when remaining <= lead_time",
    }
    return {
        "scope": (
            "M2 known-model iid engineering reference; "
            "exact mathematical DP to numerical precision"
        ),
        "inventory": asdict(cfg),
        "initial_state": asdict(initial),
        "demand": asdict(demand),
        "action_range": [0, cfg.max_order],
        "additional_terminal_value": 0,
        "limits": asdict(limits),
        "seed": None,
        "seed_note": "not applicable: exhaustive expectations, no RNG",
        "probability_tolerance": PROBABILITY_TOLERANCE,
        "value_check_absolute_tolerance": VALUE_TOLERANCE,
        "tie_break": "smallest action/level on exactly equal floating-point cost",
        "optimal_expected_cost": optimum.expected_cost,
        "optimal_initial_action": optimum.action(cfg.horizon, initial),
        "returned_policy_expected_cost": replay.expected_cost,
        "dp_counts": asdict(optimum.diagnostics),
        "returned_policy_counts": asdict(replay.diagnostics),
        "base_stock_rule": "q=min(Q_max,max(0,S-on_hand-sum(pipeline)))",
        "base_stock": {
            name: {
                "definition": definitions[name],
                "tuning": "known-model exact evaluation on declared grid",
                "limits_per_variant": asdict(limits),
                "selected_level": tuned.policy.level,
                "expected_cost": tuned.expected_cost,
                "grid_costs": {
                    str(s): e.expected_cost for s, e in tuned.evaluations.items()
                },
                "gap_to_dp": cost_gap(tuned.expected_cost, optimum.expected_cost),
                "counts": asdict(tuned.diagnostics),
            }
            for name, tuned in baselines.items()
        },
        "provenance": provenance(raw),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = demonstrate(args.config.read_bytes())
    except (
        OSError,
        ValueError,
        TypeError,
        ArithmeticError,
        ResourceLimitError,
        subprocess.SubprocessError,
    ) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
