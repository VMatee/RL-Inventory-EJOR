"""Pure, offline M4b audit tests; no retail data, GP training, or GPU access."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from inventory_ejor.baselines.analysis import (
    analyze_session,
    paired_summary,
    public_report,
    recheck_trace,
    safe_fraction,
)
from inventory_ejor.envs import (
    CostParameters,
    InventoryConfig,
    InventoryState,
    transition,
)


class M4BAnalysisTests(unittest.TestCase):
    def test_paired_descriptive_grouping_uses_series_not_48_independents(self):
        values = {
            ("S1", 28, "gp_base_stock"): {"total_cost": 10.0},
            ("S1", 28, "gp_rollout"): {"total_cost": 7.0},
            ("S1", 224, "gp_base_stock"): {"total_cost": 8.0},
            ("S1", 224, "gp_rollout"): {"total_cost": 8.0},
            ("S2", 28, "gp_base_stock"): {"total_cost": 20.0},
            ("S2", 28, "gp_rollout"): {"total_cost": 21.0},
            ("S2", 224, "gp_base_stock"): {"total_cost": 18.0},
            ("S2", 224, "gp_rollout"): {"total_cost": 17.0},
        }
        stats = paired_summary(
            values, ["S1", "S2"], [28, 224], "gp_base_stock", "gp_rollout"
        )
        self.assertEqual(stats["paired_cases"], 4)
        self.assertEqual(stats["independent_series_not_asserted"], 2)
        self.assertEqual(stats["paired_wins_ties_losses"], [2, 1, 1])
        self.assertEqual(stats["series_wins_ties_losses"], [1, 1, 0])
        self.assertAlmostEqual(stats["mean_paired_delta"], 0.75)
        self.assertAlmostEqual(stats["relative_pooled_cost_reduction"], 3 / 56)
        self.assertEqual(stats["series_average_deltas"]["S1"], 1.5)
        self.assertEqual(stats["series_average_deltas"]["S2"], 0.0)

    def test_paired_result_can_be_negative_or_zero(self):
        records = {
            ("S", 28, "simple"): {"total_cost": 3},
            ("S", 28, "rollout"): {"total_cost": 4},
        }
        x = paired_summary(records, ["S"], [28], "simple", "rollout")
        self.assertEqual(x["mean_paired_delta"], -1)
        self.assertEqual(x["paired_wins_ties_losses"], [0, 0, 1])
        self.assertAlmostEqual(x["relative_pooled_cost_reduction"], -1 / 3)

    def test_zero_baseline_does_not_fabricate_percentage(self):
        self.assertIsNone(safe_fraction(0, 0))
        self.assertIsNone(safe_fraction(5, 0))
        self.assertEqual(safe_fraction(0, 5), 0)

    def test_public_report_strips_private_per_series_outputs(self):
        private = {
            "source_commit": "test-commit",
            "series_private": {"SECRET-SKU-ID": {"cost": 12}},
            "data_diagnostics": {
                "top_two_series_request_share": 0.5,
                "request_counts_by_series_private": {"SECRET-SKU-ID": 15},
                "historical_profiles_by_series_private": {"SECRET-SKU-ID": {}},
            },
            "paired_vs_gp_rollout": {
                "gp_base_stock": {
                    "mean_paired_delta": 2,
                    "series_average_deltas": {"SECRET-SKU-ID": 2},
                }
            },
        }
        public = public_report(private)
        dump = json.dumps(public)
        self.assertNotIn("SECRET", dump)
        self.assertNotIn("series_private", public)
        self.assertEqual(
            public["data_diagnostics"], {"top_two_series_request_share": 0.5}
        )
        self.assertEqual(
            public["paired_vs_gp_rollout"]["gp_base_stock"], {"mean_paired_delta": 2}
        )

    def test_independent_m1_replay_validates_all_cost_components(self):
        costs = CostParameters(
            holding=1.25, lost_sales=7.0, variable_order=0.5, fixed_order=2.0
        )
        cfg = InventoryConfig(lead_time=2, horizon=4, max_order=5, costs=costs)
        state = InventoryState(0, (0,))
        saved = []
        for t, (order, demand) in enumerate(
            zip((2, 1, 0, 0), (1, 2, 0, 3), strict=True)
        ):
            step = transition(cfg, state, order, demand)
            saved.append(
                {
                    "period": t,
                    "day": 40 + t,
                    "on_hand": state.on_hand,
                    "pipeline": list(state.pipeline),
                    "order": order,
                    "observed_sales_as_requests": demand,
                    "fulfilled": step.sales,
                    "lost_units": step.lost_units,
                    "cost": step.costs.total,
                }
            )
            state = step.next_state
        req, filled, total, parts = recheck_trace(
            cfg, InventoryState(0, (0,)), saved, 40
        )
        self.assertEqual(req, 6)
        self.assertTrue(0 <= filled <= req)
        self.assertAlmostEqual(sum(parts.values()), total)

        altered = [dict(row) for row in saved]
        altered[1]["lost_units"] += 1
        with self.assertRaisesRegex(ValueError, "Replay units differ"):
            recheck_trace(cfg, InventoryState(0, (0,)), altered, 40)

        altered = [dict(row) for row in saved]
        altered[2]["cost"] += 1
        with self.assertRaisesRegex(ValueError, "Replay cost differs"):
            recheck_trace(cfg, InventoryState(0, (0,)), altered, 40)

    def test_replay_rejects_order_that_would_arrive_after_horizon(self):
        cfg = InventoryConfig(
            lead_time=3,
            horizon=3,
            max_order=4,
            costs=CostParameters(
                holding=1, lost_sales=10, variable_order=0, fixed_order=0
            ),
        )
        state = InventoryState(0, (0, 0))
        expected = transition(cfg, state, 2, 1)
        trace = [
            {
                "day": 225,
                "period": 0,
                "on_hand": 0,
                "pipeline": [0, 0],
                "order": 2,
                "observed_sales_as_requests": 1,
                "fulfilled": expected.sales,
                "lost_units": expected.lost_units,
                "cost": expected.costs.total,
            }
        ]
        with self.assertRaisesRegex(ValueError, "arrive after"):
            recheck_trace(cfg, state, trace, 225)

    def test_unexpected_directory_refused_before_opening_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results/runs").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "direct child"):
                analyze_session(root, root / "other" / "candidate")


if __name__ == "__main__":
    unittest.main()
