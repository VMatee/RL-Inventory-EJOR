"""Reproduce the hand-calculated M1 trace. No training or dataset access."""

from __future__ import annotations

import json
from pathlib import Path

from inventory_ejor.envs import (
    CostParameters,
    InventoryConfig,
    InventoryState,
    LostSalesInventoryEnv,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    fixture_path = root / "tests" / "fixtures" / "m1_hand_calculated.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fields = fixture["config"]
    cfg = InventoryConfig(
        lead_time=fields["lead_time"],
        horizon=fields["horizon"],
        max_order=fields["max_order"],
        costs=CostParameters(**fields["costs"]),
    )
    initial = fixture["initial_state"]
    env = LostSalesInventoryEnv(
        cfg,
        fixture["demands"],
        InventoryState(initial["on_hand"], tuple(initial["pipeline"])),
    )
    env.reset(seed=0)
    periods: list[dict] = []
    for order in fixture["orders"]:
        _, _, done, truncated, info = env.step(order)
        assert not truncated
        periods.append(
            {
                "t": info["period"],
                "order": info["order"],
                "demand": info["demand"],
                "sales": info["sales"],
                "lost_units": info["lost_units"],
                "end_stock": info["ending_on_hand"],
                "cost": info["cost_total"],
            }
        )
    actual = env.episode_cost
    expected = fixture["expected_total_cost"]
    ok = done and actual == expected
    print(json.dumps({
        "fixture": fixture["id"],
        "periods": periods,
        "total_cost": actual,
        "expected_cost": expected,
        "terminal_snapshot": info["terminal_snapshot"],
        "matched_hand_fixture": ok,
        "scope": "M1 deterministic reference only; not learned policy or research outcome",
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
