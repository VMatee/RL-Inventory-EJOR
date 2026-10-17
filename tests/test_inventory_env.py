"""Independent, deterministic M1 tests for lost-sales inventory event timing.

No stochastic data fitting, real datasets, RL training or GP models are used.
Reference quantities come from a hand-calculated JSON fixture.
"""

import json
import random
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
from gymnasium.utils.env_checker import check_env

from inventory_ejor.envs import (
    CostParameters,
    InventoryConfig,
    InventoryState,
    LostSalesInventoryEnv,
    simulate_fixed_actions,
    transition,
    validate_state,
)

FIXTURE = Path(__file__).parent / "fixtures" / "m1_hand_calculated.json"


def config(
    lead_time: int = 2,
    horizon: int = 3,
    max_order: int = 10,
    *,
    holding: float = 2.0,
    shortage: float = 7.0,
    unit: float = 1.0,
    fixed: float = 3.0,
) -> InventoryConfig:
    return InventoryConfig(
        lead_time=lead_time,
        horizon=horizon,
        max_order=max_order,
        costs=CostParameters(holding, shortage, unit, fixed),
    )


class M1HandFixtureTests(unittest.TestCase):
    def test_hand_computed_fixture_against_pure_kernel(self):
        fixture = json.loads(FIXTURE.read_text())
        assert fixture["provenance"].startswith("Manually computed")
        c = fixture["config"]
        cfg = InventoryConfig(
            c["lead_time"], c["horizon"], c["max_order"],
            CostParameters(**c["costs"]),
        )
        start = fixture["initial_state"]
        init = InventoryState(start["on_hand"], tuple(start["pipeline"]))
        outcomes = simulate_fixed_actions(
            cfg, fixture["demands"], fixture["orders"], init
        )
        self.assertEqual(len(outcomes), 5)
        total = 0.0
        for outcome, expected in zip(outcomes, fixture["expected"]):
            self.assertEqual(outcome.prior_state.on_hand, expected["initial_on_hand"])
            self.assertEqual(outcome.prior_state.pipeline, tuple(expected["initial_pipeline"]))
            self.assertEqual(outcome.sales, expected["sales"])
            self.assertEqual(outcome.lost_units, expected["lost_units"])
            self.assertEqual(outcome.ending_on_hand, expected["ending_on_hand"])
            self.assertEqual(outcome.next_period_receipt, expected["next_period_receipt"])
            self.assertEqual(outcome.next_state.on_hand, expected["next_on_hand"])
            self.assertEqual(outcome.next_state.pipeline, tuple(expected["next_pipeline"]))
            self.assertEqual(outcome.costs.holding, expected["holding_cost"])
            self.assertEqual(outcome.costs.lost_sales, expected["lost_sales_cost"])
            self.assertEqual(
                outcome.costs.variable_order + outcome.costs.fixed_order,
                expected["ordering_cost"],
            )
            self.assertEqual(outcome.costs.total, expected["total_cost"])
            self.assertEqual(outcome.reward, -outcome.costs.total)
            total += outcome.costs.total

        self.assertEqual(total, fixture["expected_total_cost"])
        self.assertEqual(
            outcomes[-1].outstanding_after_order,
            tuple(fixture["terminal_snapshot"]["outstanding_receipts"]),
        )

    def test_gym_wrapper_matches_hand_fixture_and_terminal_snapshot(self):
        f = json.loads(FIXTURE.read_text())
        c = f["config"]
        cfg = InventoryConfig(
            c["lead_time"], c["horizon"], c["max_order"],
            CostParameters(**c["costs"]),
        )
        init = InventoryState(
            f["initial_state"]["on_hand"],
            tuple(f["initial_state"]["pipeline"]),
        )
        env = LostSalesInventoryEnv(cfg, f["demands"], init)
        obs, info = env.reset(seed=41)
        np.testing.assert_array_equal(obs, [4, 2, 1, 5])
        self.assertEqual(info, {})
        total = 0
        for t, (order, e) in enumerate(zip(f["orders"], f["expected"])):
            obs, reward, terminated, truncated, info = env.step(order)
            self.assertFalse(truncated)
            self.assertEqual(terminated, t == cfg.horizon - 1)
            self.assertEqual(info["period"], t)
            self.assertEqual(info["demand"], f["demands"][t])
            self.assertEqual(info["sales"], e["sales"])
            self.assertEqual(info["lost_units"], e["lost_units"])
            self.assertEqual(info["cost_total"], e["total_cost"])
            self.assertEqual(reward, -e["total_cost"])
            np.testing.assert_array_equal(
                obs, [e["next_on_hand"], *e["next_pipeline"], cfg.horizon - t - 1]
            )
            total += e["total_cost"]
        self.assertEqual(total, 47)
        self.assertEqual(env.episode_cost, 47)
        self.assertEqual(
            info["terminal_snapshot"]["ending_on_hand_before_next_receipt"],
            f["terminal_snapshot"]["ending_on_hand_before_next_receipt"],
        )
        self.assertEqual(
            info["terminal_snapshot"]["outstanding_receipts"],
            tuple(f["terminal_snapshot"]["outstanding_receipts"]),
        )
        self.assertEqual(
            info["terminal_snapshot"]["additional_terminal_cost"],
            f["terminal_snapshot"]["additional_terminal_cost"],
        )
        with self.assertRaises(RuntimeError):
            env.step(0)


class M1EventTimingTests(unittest.TestCase):
    def test_order_first_sellable_exactly_t_plus_L(self):
        for L in (1, 2, 3, 4):
            with self.subTest(lead_time=L):
                cfg = config(lead_time=L, horizon=L + 2)
                demands = [0] * cfg.horizon
                demands[L] = 6
                env = LostSalesInventoryEnv(cfg, demands)
                obs, _ = env.reset()
                self.assertEqual(tuple(obs[1:-1]), (0,) * (L - 1))
                for t in range(cfg.horizon):
                    if t < L:
                        self.assertEqual(obs[0], 0.0)
                    obs, _, _, _, info = env.step(5 if t == 0 else 0)
                    if t < L:
                        self.assertEqual(info["sales"], 0)
                    if t == L:
                        self.assertEqual(info["sales"], 5)
                        self.assertEqual(info["lost_units"], 1)

    def test_l1_next_period_arrival_not_same_period_sales(self):
        cfg = config(lead_time=1, horizon=2)
        a = transition(cfg, InventoryState(0, ()), 0, 5)
        b = transition(cfg, InventoryState(0, ()), 8, 5)
        self.assertEqual((a.sales, a.lost_units), (0, 5))
        self.assertEqual((b.sales, b.lost_units), (0, 5))
        self.assertEqual(a.next_state.on_hand, 0)
        self.assertEqual(b.next_state.on_hand, 8)
        self.assertEqual(b.outstanding_after_order, (8,))
        self.assertEqual(b.next_state.pipeline, ())

    def test_l4_pipeline_exact_shift_and_arrival(self):
        cfg = config(lead_time=4)
        s = InventoryState(2, (5, 4, 3))
        outcome = transition(cfg, s, 7, 1)
        self.assertEqual(outcome.ending_on_hand, 1)
        self.assertEqual(outcome.next_period_receipt, 5)
        self.assertEqual(outcome.next_state, InventoryState(6, (4, 3, 7)))
        self.assertEqual(outcome.outstanding_after_order, (5, 4, 3, 7))

    def test_initial_pipeline_not_available_for_current_sales(self):
        cfg = config(lead_time=2)
        outcome = transition(cfg, InventoryState(1, (3,)), 0, 6)
        self.assertEqual(outcome.sales, 1)
        self.assertEqual(outcome.lost_units, 5)
        self.assertEqual(outcome.ending_on_hand, 0)
        self.assertEqual(outcome.next_state.on_hand, 3)

    def test_no_order_no_demand_keeps_stock_and_charges_holding(self):
        cfg = config(lead_time=2, horizon=3)
        outcomes = simulate_fixed_actions(
            cfg, (0, 0, 0), (0, 0, 0), InventoryState(4, (0,))
        )
        self.assertEqual([o.ending_on_hand for o in outcomes], [4, 4, 4])
        self.assertEqual([o.costs.holding for o in outcomes], [8, 8, 8])
        self.assertEqual(sum(o.costs.total for o in outcomes), 24)

    def test_exact_depletion_has_no_lost_units(self):
        cfg = config()
        o = transition(cfg, InventoryState(5, (0,)), 0, 5)
        self.assertEqual((o.sales, o.lost_units, o.ending_on_hand), (5, 0, 0))

    def test_lost_sales_are_never_backlogged(self):
        cfg = config(lead_time=1, horizon=2)
        s = InventoryState(2, ())
        first = transition(cfg, s, 0, 7)
        second = transition(cfg, first.next_state, 0, 0)
        self.assertEqual((first.sales, first.lost_units), (2, 5))
        self.assertEqual(second.next_state.on_hand, 0)
        self.assertEqual(second.lost_units, 0)

    def test_per_period_cost_decomposition(self):
        cfg = config(lead_time=2, holding=2, shortage=4, unit=3, fixed=6)
        outcome = transition(cfg, InventoryState(3, (1,)), 2, 5)
        self.assertEqual(outcome.costs.holding, 0)
        self.assertEqual(outcome.costs.lost_sales, 8)
        self.assertEqual(outcome.costs.variable_order, 6)
        self.assertEqual(outcome.costs.fixed_order, 6)
        self.assertEqual(outcome.costs.total, 20)
        zero_order = transition(cfg, InventoryState(3, (1,)), 0, 0)
        self.assertEqual(zero_order.costs.fixed_order, 0)
        self.assertEqual(zero_order.costs.variable_order, 0)
        self.assertEqual(zero_order.costs.holding, 6)

    def test_terminal_records_outstanding_and_no_extra_salvage(self):
        cfg = config(lead_time=1, horizon=1, holding=2, shortage=3, unit=1, fixed=5)
        env = LostSalesInventoryEnv(cfg, (1,), InventoryState(3, ()))
        env.reset()
        obs, reward, terminated, truncated, info = env.step(4)
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(info["ending_on_hand"], 2)
        self.assertEqual(info["cost_total"], 13)
        self.assertEqual(reward, -13)
        self.assertEqual(obs[0], 6)  # hypothetical start-of-t=1 receipt OUTSIDE horizon
        self.assertEqual(obs[-1], 0)
        self.assertEqual(
            info["terminal_snapshot"],
            {
                "ending_on_hand_before_next_receipt": 2,
                "outstanding_receipts": (4,),
                "additional_terminal_cost": 0.0,
            },
        )

    def test_zero_horizon_extension_not_charged(self):
        cfg = config(lead_time=3, horizon=1, unit=1, fixed=1)
        env = LostSalesInventoryEnv(cfg, (0,))
        env.reset()
        _, reward, terminated, _, info = env.step(5)
        self.assertEqual(reward, -6.0)
        self.assertTrue(terminated)
        self.assertEqual(info["terminal_snapshot"]["outstanding_receipts"], (0, 0, 5))
        self.assertEqual(info["terminal_snapshot"]["additional_terminal_cost"], 0)

    def test_pure_step_does_not_mutate_state(self):
        cfg = config()
        state = InventoryState(3, (2,))
        outcome = transition(cfg, state, 4, 1)
        self.assertEqual(state, InventoryState(3, (2,)))
        self.assertNotEqual(outcome.next_state, state)
        with self.assertRaises(FrozenInstanceError):
            state.on_hand = 10

    def test_many_hand_invariants(self):
        rnd = random.Random(83417)
        for lead in (1, 2, 4):
            cfg = config(lead_time=lead, horizon=80)
            state = InventoryState(2, (1,) * (lead - 1))
            for _ in range(cfg.horizon):
                q, d = rnd.randrange(0, 11), rnd.randrange(0, 15)
                outcome = transition(cfg, state, q, d)
                self.assertEqual(outcome.sales + outcome.lost_units, d)
                self.assertEqual(outcome.sales + outcome.ending_on_hand, state.on_hand)
                self.assertLessEqual(outcome.sales, state.on_hand)
                self.assertEqual(outcome.next_state.on_hand, outcome.ending_on_hand + outcome.next_period_receipt)
                self.assertEqual(len(outcome.next_state.pipeline), lead - 1)
                self.assertEqual(outcome.outstanding_after_order[-1], q)
                self.assertTrue(all(x >= 0 for x in (outcome.next_state.on_hand, *outcome.next_state.pipeline)))
                self.assertGreaterEqual(outcome.costs.total, 0)
                state = outcome.next_state


    def test_calendar_based_independent_reference_catches_off_by_one(self):
        # A separately written event-calendar simulation, not pipeline shifting,
        # is a second reference beside the manually calculated JSON trajectory.
        rnd = random.Random(177)
        for lead in (1, 2, 3, 5):
            cfg = config(lead_time=lead, horizon=15)
            init = InventoryState(3, tuple(rnd.randrange(4) for _ in range(lead - 1)))
            demands = tuple(rnd.randrange(12) for _ in range(cfg.horizon))
            orders = tuple(rnd.randrange(8) for _ in range(cfg.horizon))
            outcomes = simulate_fixed_actions(cfg, demands, orders, init)
            calendar = {j + 1: qty for j, qty in enumerate(init.pipeline)}
            stock = init.on_hand
            for t, (q, d, result) in enumerate(zip(orders, demands, outcomes)):
                if t:
                    stock += calendar.get(t, 0)
                self.assertEqual(result.prior_state.on_hand, stock)
                calendar[t + lead] = calendar.get(t + lead, 0) + q
                sales = min(stock, d)
                missing = d - sales
                stock -= sales
                next_receipt = calendar.get(t + 1, 0)
                self.assertEqual(result.sales, sales)
                self.assertEqual(result.lost_units, missing)
                self.assertEqual(result.ending_on_hand, stock)
                self.assertEqual(result.next_period_receipt, next_receipt)
                self.assertEqual(result.next_state.on_hand, stock + next_receipt)
                self.assertEqual(
                    result.costs.total,
                    cfg.costs.holding * stock
                    + cfg.costs.lost_sales * missing
                    + cfg.costs.variable_order * q
                    + (cfg.costs.fixed_order if q else 0),
                )
                self.assertEqual(
                    result.outstanding_after_order,
                    tuple(calendar.get(k, 0) for k in range(t + 1, t + lead + 1)),
                )


class M1ValidationTests(unittest.TestCase):
    def test_config_rejects_invalid_lead_horizon_max_order(self):
        for lead, horizon, maximum in ((0, 3, 2), (1, 0, 2), (1, 3, -1)):
            with self.subTest(values=(lead, horizon, maximum)), self.assertRaises(ValueError):
                config(lead, horizon, maximum)
        for invalid in (1.0, True, np.bool_(True), "2"):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                config(lead_time=invalid)
        with self.assertRaises(TypeError):
            InventoryConfig(1, 2, 3, costs=None)

    def test_invalid_money_rejected(self):
        for bad in (-1, float("nan"), float("inf"), -float("inf")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                CostParameters(bad, 0, 0, 0)
        for bad in (True, None, "not-money"):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                CostParameters(1, bad, 0, 0)

    def test_invalid_state_and_pipeline_shape_rejected(self):
        cfg = config(lead_time=3)
        with self.assertRaises(ValueError):
            validate_state(cfg, InventoryState(2, (4,)))
        with self.assertRaises(TypeError):
            InventoryState(2, [4, 3])
        for bad in (-1, True, 1.5):
            with self.subTest(bad=bad), self.assertRaises((ValueError, TypeError)):
                InventoryState(bad, (1, 2))
        with self.assertRaises(ValueError):
            InventoryState(2**53 + 1, ())

    def test_orders_invalid_no_silent_clipping(self):
        cfg = config(lead_time=2, max_order=4)
        state = InventoryState(0, (0,))
        for bad in (-1, 5, 2**53 + 1):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                transition(cfg, state, bad, 0)
        for bad in (True, 1.0, np.float64(1), None):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                transition(cfg, state, bad, 0)
        valid = transition(cfg, state, np.int64(4), 0)
        self.assertEqual(valid.order, 4)

    def test_demands_invalid_rejected(self):
        cfg = config(lead_time=1)
        for bad in (-1, 2**53 + 1):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                transition(cfg, InventoryState(0, ()), 0, bad)
        for bad in (1.2, float("nan"), True, np.bool_(False)):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                transition(cfg, InventoryState(0, ()), 0, bad)

    def test_trace_length_and_action_length_must_match(self):
        cfg = config(horizon=3)
        with self.assertRaises(ValueError):
            LostSalesInventoryEnv(cfg, (0, 0))
        with self.assertRaises(ValueError):
            simulate_fixed_actions(cfg, (0, 0, 0), (0, 0))
        with self.assertRaises(ValueError):
            simulate_fixed_actions(cfg, (0, 0), (0, 0, 0))

    def test_invalid_action_does_not_advance_time_or_state(self):
        cfg = config(lead_time=1, horizon=1, max_order=0)
        env = LostSalesInventoryEnv(cfg, (1,), InventoryState(2, ()))
        obs, _ = env.reset()
        with self.assertRaises(ValueError):
            env.step(1)
        self.assertEqual(env.period, 0)
        self.assertEqual(env.state, InventoryState(2, ()))
        self.assertEqual(env.episode_cost, 0)
        np.testing.assert_array_equal(obs, [2, 1])

    def test_cost_overflow_rejected(self):
        cfg = config(holding=1e308, shortage=0, unit=0, fixed=0)
        with self.assertRaises(OverflowError):
            transition(cfg, InventoryState(5, (0,)), 0, 0)


class M1GymnasiumTests(unittest.TestCase):
    def test_env_observation_has_no_future_demand(self):
        cfg = config(lead_time=2, horizon=3)
        first = LostSalesInventoryEnv(cfg, (1, 2, 4), InventoryState(6, (1,)))
        second = LostSalesInventoryEnv(cfg, (1, 9, 5), InventoryState(6, (1,)))
        o1, i1 = first.reset(seed=29)
        o2, i2 = second.reset(seed=29)
        np.testing.assert_array_equal(o1, o2)
        self.assertEqual(i1, i2)
        self.assertEqual(tuple(o1), (6.0, 1.0, 3.0))
        n1, _, _, _, info1 = first.step(0)
        n2, _, _, _, info2 = second.step(0)
        np.testing.assert_array_equal(n1, n2)
        self.assertEqual(info1, info2)
        self.assertNotIn("future_demand", info1)

    def test_gymnasium_checker(self):
        env = LostSalesInventoryEnv(config(lead_time=3, horizon=4), (0, 1, 2, 3))
        check_env(env, skip_render_check=True)

    def test_reset_replays_trace_and_clears_cost(self):
        cfg = config(lead_time=1, horizon=2)
        env = LostSalesInventoryEnv(cfg, (4, 2), InventoryState(3, ()))
        _, info = env.reset(seed=17)
        self.assertEqual(info, {})
        trajectory = []
        for q in (5, 1):
            obs, reward, terminated, _, detail = env.step(q)
            trajectory.append((tuple(obs), reward, terminated, dict(detail)))
        self.assertGreater(env.episode_cost, 0)
        obs, _ = env.reset(seed=17)
        self.assertEqual(tuple(obs), (3.0, 2.0))
        self.assertEqual(env.episode_cost, 0)
        for q, expected in zip((5, 1), trajectory):
            obs, reward, terminated, _, detail = env.step(q)
            self.assertEqual((tuple(obs), reward, terminated, detail), expected)

    def test_empty_pipeline_for_l1_and_nonempty_for_l2(self):
        env1 = LostSalesInventoryEnv(config(lead_time=1), (0, 0, 0))
        obs1, _ = env1.reset()
        self.assertEqual(obs1.shape, (2,))
        self.assertEqual(env1.state.pipeline, ())
        env2 = LostSalesInventoryEnv(config(lead_time=2), (0, 0, 0))
        obs2, _ = env2.reset()
        self.assertEqual(obs2.shape, (3,))
        self.assertEqual(env2.state.pipeline, (0,))

    def test_reset_options_and_double_step_raises(self):
        env = LostSalesInventoryEnv(config(lead_time=1, horizon=1), (0,))
        with self.assertRaises(ValueError):
            env.reset(options={"new_demands": [99]})
        env.reset()
        env.step(0)
        with self.assertRaises(RuntimeError):
            env.step(0)


if __name__ == "__main__":
    unittest.main()
