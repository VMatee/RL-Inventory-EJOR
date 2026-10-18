"""Independent contingent-policy enumeration and M2 API/CLI rejection tests."""

import copy
import importlib.util
import io
import itertools
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from inventory_ejor.demand import FiniteDemand
from inventory_ejor.envs import CostParameters, InventoryConfig, InventoryState
from inventory_ejor.policies.base_stock import (
    BaseStockPolicy,
    HorizonAwareBaseStockPolicy,
    tune_base_stock,
)
from inventory_ejor.solvers.finite_horizon import (
    ResourceLimitError,
    ResourceLimits,
    cost_gap,
    evaluate_policy,
    solve_dp,
)

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "m2_cli", ROOT / "scripts/run_m2_reference.py"
)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def config(lead=1, horizon=3, maximum=1, costs=(1, 4, 0.5, 0)):
    return InventoryConfig(lead, horizon, maximum, CostParameters(*costs))


def calendar_cost(cfg, initial, path, choose):
    """Independent calendar, rational costs; does NOT call the M1 kernel.

    The chooser sees only the prefix of already realized demand. The caller
    enumerates a complete policy once, then evaluates it on every leaf.
    """
    receipts = dict(enumerate(initial.pipeline, start=1))
    stock, total = initial.on_hand, Fraction(0)
    h, b, c, k = (
        Fraction(str(v))
        for v in (
            cfg.costs.holding,
            cfg.costs.lost_sales,
            cfg.costs.variable_order,
            cfg.costs.fixed_order,
        )
    )
    for t, demand in enumerate(path):
        if t:
            stock += receipts.get(t, 0)
        pending = tuple(receipts.get(t + j, 0) for j in range(1, cfg.lead_time))
        order = choose(path[:t], stock, pending)
        receipts[t + cfg.lead_time] = order
        shortage = max(0, demand - stock)
        stock = max(0, stock - demand)
        total += h * stock + b * shortage + c * order + (k if order else 0)
    return total  # no receipt at T, liquidation, or terminal cost


def expected_calendar_cost(cfg, initial, law, choose):
    total = Fraction(0)
    for outcomes in itertools.product(
        tuple(zip(law.support, law.probabilities, strict=True)), repeat=cfg.horizon
    ):
        path = tuple(d for d, _ in outcomes)
        weight = Fraction(1)
        for _, probability in outcomes:
            weight *= Fraction(str(probability))
        total += weight * calendar_cost(cfg, initial, path, choose)
    return total


def exhaustive_contingent_optimum(cfg, initial, law):
    # Every demand-prefix node gets its own action, fixed across leaves with
    # that prefix. This is exhaustive adaptive policy enumeration, no Bellman
    # recursion, state merging, value memoization, or future-demand access.
    nodes = [
        prefix
        for t in range(cfg.horizon)
        for prefix in itertools.product(law.support, repeat=t)
    ]
    count = (cfg.max_order + 1) ** len(nodes)
    if count > 10000:
        raise ValueError("independent oracle restricted to tiny fixtures")
    best = None
    for action_vector in itertools.product(range(cfg.max_order + 1), repeat=len(nodes)):
        policy = dict(zip(nodes, action_vector, strict=True))
        value = expected_calendar_cost(
            cfg, initial, law, lambda history, x, p, policy=policy: policy[history]
        )
        best = value if best is None else min(best, value)
    return best, count


def calendar_base_stock(cfg, level, horizon_aware):
    """Independent comparator uses absolute arrival date, not production code."""

    def choose(history, stock, pending):
        arrival_date = len(history) + cfg.lead_time
        if horizon_aware and arrival_date >= cfg.horizon:
            return 0
        return min(cfg.max_order, max(0, level - stock - sum(pending)))

    return choose


class DemandTests(unittest.TestCase):
    def test_invalid_support_and_probabilities(self):
        cases = [
            ([], []),
            ([0], []),
            ([-1], [1]),
            ([0.5], [1]),
            ([True], [1]),
            ([2**53 + 1], [1]),
            ([0, 0], [0.5, 0.5]),
            ([0], [0]),
            ([0], [-1]),
            ([0], [float("nan")]),
            ([0], [float("inf")]),
            ([0, 1], [0.3, 0.6]),
            ([0], [True]),
            ([0], ["1"]),
        ]
        for support, probabilities in cases:
            with self.subTest(support=support, probabilities=probabilities):
                with self.assertRaises((TypeError, ValueError)):
                    FiniteDemand(support, probabilities)

    def test_roundoff_normalization_is_recorded_and_zero_mass_skipped(self):
        law = FiniteDemand([0, 1, 9], [0.5, 0.5 + 2e-13, 0])
        self.assertNotEqual(law.input_mass, 1)
        self.assertAlmostEqual(sum(law.probabilities), 1, places=15)
        self.assertEqual(len(law.outcomes), 2)
        self.assertEqual(law.support, (0, 1, 9))


class ExactReferenceTests(unittest.TestCase):
    def test_original_gap_disappears_with_horizon_aware_tuning(self):
        cfg, initial = config(), InventoryState(1, ())
        law = FiniteDemand((0, 1), (0.5, 0.5))
        limits = ResourceLimits(max_states=1000, max_transitions=10000, max_seconds=10)
        naive = tune_base_stock(
            cfg, initial, law, range(4), limits, horizon_aware=False
        )
        aware = tune_base_stock(cfg, initial, law, range(4), limits, horizon_aware=True)
        optimum, count = exhaustive_contingent_optimum(cfg, initial, law)
        self.assertEqual(count, 128)
        self.assertEqual(optimum, Fraction(23, 8))
        self.assertEqual(naive.policy.level, 1)
        self.assertEqual(aware.policy.level, 1)
        self.assertEqual(naive.expected_cost, 3)
        self.assertEqual(aware.expected_cost, float(optimum))
        self.assertEqual(
            solve_dp(cfg, initial, law, limits).expected_cost, float(optimum)
        )
        self.assertEqual(
            cost_gap(aware.expected_cost, float(optimum)),
            {"absolute": 0, "relative": 0},
        )
        # Hand costs in lexicographic path order 000,001,...,111. Only paths
        # 010 and 011 incur an unnecessary final 0.5 placement under naive S=1.
        naive_costs = (
            3,
            2,
            Fraction(3, 2),
            Fraction(11, 2),
            Fraction(3, 2),
            Fraction(1, 2),
            Fraction(11, 2),
            Fraction(9, 2),
        )
        aware_costs = (
            3,
            2,
            1,
            5,
            Fraction(3, 2),
            Fraction(1, 2),
            Fraction(11, 2),
            Fraction(9, 2),
        )
        self.assertEqual(sum(naive_costs) / 8 - sum(aware_costs) / 8, Fraction(1, 8))
        for path, naive_cost, aware_cost in zip(
            itertools.product((0, 1), repeat=3), naive_costs, aware_costs, strict=True
        ):
            self.assertEqual(
                calendar_cost(cfg, initial, path, calendar_base_stock(cfg, 1, False)),
                naive_cost,
            )
            self.assertEqual(
                calendar_cost(cfg, initial, path, calendar_base_stock(cfg, 1, True)),
                aware_cost,
            )

    def test_horizon_aware_lead_longer_than_horizon(self):
        cfg = config(lead=3, horizon=2, costs=(1, 4, 0.5, 0.25))
        initial, law = InventoryState(0, (1, 0)), FiniteDemand((1,), (1,))
        # New orders cannot arrive during periods 0,1. Initial receipt at 1
        # meets the second demand; only the first shortage (cost 4) is needed.
        naive = BaseStockPolicy(cfg, 2)
        aware = HorizonAwareBaseStockPolicy(cfg, 2)
        self.assertEqual(naive(2, initial), 1)
        self.assertEqual(aware(2, initial), 0)
        self.assertEqual(evaluate_policy(cfg, initial, law, naive).expected_cost, 4.75)
        self.assertEqual(evaluate_policy(cfg, initial, law, aware).expected_cost, 4)
        self.assertEqual(
            expected_calendar_cost(
                cfg, initial, law, calendar_base_stock(cfg, 2, False)
            ),
            Fraction(19, 4),
        )
        self.assertEqual(
            expected_calendar_cost(
                cfg, initial, law, calendar_base_stock(cfg, 2, True)
            ),
            4,
        )
        optimum, _ = exhaustive_contingent_optimum(cfg, initial, law)
        self.assertEqual(optimum, 4)
        tuned = tune_base_stock(cfg, initial, law, [3, 2, 1, 0], horizon_aware=True)
        self.assertEqual(tuned.expected_cost, 4)
        self.assertEqual(tuned.policy.level, 0)  # exact level tie
        self.assertTrue(all(e.expected_cost == 4 for e in tuned.evaluations.values()))

    def test_cutoff_boundary_and_validation_before_returning_zero(self):
        cfg, state = config(lead=2), InventoryState(0, (0,))
        aware = HorizonAwareBaseStockPolicy(cfg, 1)
        self.assertEqual(aware(3, state), 1)  # arrival in final sales period
        self.assertEqual(aware(2, state), 0)  # arrival at T: no sales
        self.assertEqual(aware(1, state), 0)  # arrival after T
        for remaining in (0, -1, True, 0.5, 4):
            with self.assertRaises((TypeError, ValueError)):
                aware(remaining, state)
        with self.assertRaises(ValueError):
            aware(1, InventoryState(0, ()))

    def test_horizon_aware_policy_uses_only_decision_time_information(self):
        cfg, initial = config(), InventoryState(1, ())
        policy = HorizonAwareBaseStockPolicy(cfg, 1)
        seen = {}

        def choose(history, stock, pending):
            remaining = cfg.horizon - len(history)
            action = policy(remaining, InventoryState(stock, pending))
            self.assertEqual(seen.setdefault(history, action), action)
            if remaining <= cfg.lead_time:
                self.assertEqual(action, 0)
            return action

        # Different current and future demands share each decision-time prefix.
        for path in itertools.product((0, 1), repeat=3):
            calendar_cost(cfg, initial, path, choose)
        self.assertEqual(len(seen), 7)
        self.assertEqual(seen[()], 0)
        self.assertEqual(seen[(0,)], 0)
        self.assertEqual(seen[(1,)], 1)

    def test_both_tuners_keep_separate_equal_limits_and_default_calls_repeat(self):
        cfg, initial, law = (
            config(),
            InventoryState(1, ()),
            FiniteDemand((0, 1), (0.5, 0.5)),
        )
        for horizon_aware in (False, True):
            with self.assertRaises(ResourceLimitError):
                tune_base_stock(
                    cfg,
                    initial,
                    law,
                    range(4),
                    ResourceLimits(max_transitions=1),
                    horizon_aware=horizon_aware,
                )
            first = tune_base_stock(
                cfg, initial, law, range(4), horizon_aware=horizon_aware
            )
            second = tune_base_stock(
                cfg, initial, law, range(4), horizon_aware=horizon_aware
            )
            self.assertEqual(first.expected_cost, second.expected_cost)
            self.assertEqual(first.diagnostics, second.diagnostics)
        with self.assertRaises(TypeError):
            tune_base_stock(cfg, initial, law, [1], horizon_aware="yes")

    def test_exhaustive_adaptive_reference_l1_l2_and_initial_pipeline(self):
        law = FiniteDemand((0, 1), (0.5, 0.5))
        for cfg, initial in [
            (config(), InventoryState(1, ())),
            (config(lead=2, costs=(1, 4, 0.5, 0.25)), InventoryState(0, (1,))),
        ]:
            with self.subTest(lead=cfg.lead_time):
                expected, count = exhaustive_contingent_optimum(cfg, initial, law)
                self.assertEqual(count, 128)
                result = solve_dp(cfg, initial, law)
                self.assertEqual(result.expected_cost, float(expected))
                replay = expected_calendar_cost(
                    cfg,
                    initial,
                    law,
                    lambda history, x, p, result=result, horizon=cfg.horizon: (
                        result.action(horizon - len(history), InventoryState(x, p))
                    ),
                )
                self.assertEqual(replay, expected)
                self.assertEqual(
                    evaluate_policy(cfg, initial, law, result.action).expected_cost,
                    float(expected),
                )
                for horizon_aware in (False, True):
                    baseline = tune_base_stock(
                        cfg, initial, law, range(4), horizon_aware=horizon_aware
                    )
                    for level, value in baseline.evaluations.items():
                        self.assertLessEqual(result.expected_cost, value.expected_cost)
                        calendar = expected_calendar_cost(
                            cfg,
                            initial,
                            law,
                            calendar_base_stock(cfg, level, horizon_aware),
                        )
                        self.assertEqual(value.expected_cost, float(calendar))

    def test_adaptive_policy_strictly_beats_open_loop_sanity_comparator(self):
        cfg, initial = config(), InventoryState(1, ())
        law = FiniteDemand((0, 1), (0.5, 0.5))
        open_loop = min(
            expected_calendar_cost(
                cfg,
                initial,
                law,
                lambda history, x, p, orders=orders: orders[len(history)],
            )
            for orders in itertools.product(range(2), repeat=3)
        )
        result = solve_dp(cfg, initial, law)
        self.assertLess(result.expected_cost, float(open_loop))
        self.assertEqual(result.expected_cost, 23 / 8)
        self.assertEqual(open_loop, 3)
        # Same physical state requires different actions with different time left.
        self.assertEqual(result.action(1, InventoryState(0, ())), 0)
        self.assertEqual(result.action(2, InventoryState(0, ())), 1)

    def test_deterministic_hand_case_and_positive_lead_time(self):
        cfg = config(horizon=3, costs=(1, 5, 1, 0))
        law, initial = FiniteDemand((1,), (1,)), InventoryState(0, ())
        # q=(1,1,0): first shortage 5 plus two placement costs of 1.
        result = solve_dp(cfg, initial, law)
        self.assertEqual(result.expected_cost, 7)
        self.assertEqual(
            evaluate_policy(cfg, initial, law, result.action).expected_cost, 7
        )
        self.assertEqual(
            evaluate_policy(cfg, initial, law, lambda n, s: 0).expected_cost, 15
        )
        self.assertEqual(
            evaluate_policy(cfg, initial, law, lambda n, s: 1).expected_cost, 8
        )

    def test_one_period_and_horizon_shorter_than_lead(self):
        law = FiniteDemand((2,), (1,))
        cfg, initial = config(horizon=1, costs=(2, 7, 1, 3)), InventoryState(1, ())
        result = solve_dp(cfg, initial, law)
        self.assertEqual(result.expected_cost, 7)
        self.assertEqual(result.action(1, initial), 0)
        cfg, initial = (
            config(lead=4, horizon=2, costs=(2, 7, 1, 3)),
            InventoryState(0, (1, 5, 0)),
        )
        result = solve_dp(cfg, initial, law)
        self.assertEqual(
            result.expected_cost, 21
        )  # losses 2 then 1, no value for later 5
        self.assertTrue(all(q == 0 for q in result.actions.values()))

    def test_zero_demand_zero_max_order_zero_cost_ties_and_zero_gap(self):
        initial, law = InventoryState(2, ()), FiniteDemand((0,), (1,))
        cfg = config(maximum=0)
        self.assertEqual(solve_dp(cfg, initial, law).expected_cost, 6)
        cfg = config(costs=(0, 0, 0, 0))
        result = solve_dp(cfg, initial, law)
        self.assertEqual(result.expected_cost, 0)
        self.assertTrue(all(q == 0 for q in result.actions.values()))
        tuned = tune_base_stock(cfg, initial, law, [3, 1, 0, 1])
        self.assertEqual(tuned.policy.level, 0)
        self.assertEqual(cost_gap(0, 0), {"absolute": 0, "relative": None})
        self.assertEqual(cost_gap(1, 0), {"absolute": 1, "relative": None})

    def test_base_stock_position_capping_and_terminal_orders(self):
        cfg = config(lead=3, costs=(0, 0, 2, 3))
        policy = BaseStockPolicy(cfg, 5)
        self.assertEqual(policy(3, InventoryState(1, (2, 2))), 0)
        self.assertEqual(policy(3, InventoryState(0, (0, 0))), 1)
        cfg = config(horizon=1, costs=(0, 0, 2, 3))
        law, initial = FiniteDemand((0,), (1,)), InventoryState(0, ())
        self.assertEqual(
            evaluate_policy(cfg, initial, law, BaseStockPolicy(cfg, 1)).expected_cost, 5
        )
        self.assertEqual(solve_dp(cfg, initial, law).expected_cost, 0)

    def test_no_lookahead_same_prefix_same_action(self):
        cfg, initial = config(), InventoryState(1, ())
        law = FiniteDemand((0, 1), (0.5, 0.5))
        result = solve_dp(cfg, initial, law)
        seen = {}

        def choose(history, stock, pending):
            action = result.action(
                cfg.horizon - len(history), InventoryState(stock, pending)
            )
            self.assertEqual(seen.setdefault(history, action), action)
            return action

        for path in itertools.product((0, 1), repeat=3):
            calendar_cost(cfg, initial, path, choose)
        self.assertEqual(len(seen), 7)

    def test_limits_fail_explicitly_without_returning_truncated_solution(self):
        cfg, initial, law = (
            config(),
            InventoryState(0, ()),
            FiniteDemand((0, 1), (0.5, 0.5)),
        )
        for limits, message in [
            (ResourceLimits(max_states=1), "state limit"),
            (ResourceLimits(max_transitions=1), "transition limit"),
        ]:
            with self.assertRaisesRegex(ResourceLimitError, message):
                solve_dp(cfg, initial, law, limits)
            with self.assertRaises(ResourceLimitError):
                evaluate_policy(cfg, initial, law, lambda n, s: 1, limits)
        with patch(
            "inventory_ejor.solvers.finite_horizon.time.monotonic", side_effect=[0, 31]
        ):
            with self.assertRaisesRegex(ResourceLimitError, "time limit"):
                solve_dp(cfg, initial, law)
        with self.assertRaisesRegex(ResourceLimitError, "state limit"):
            tune_base_stock(cfg, initial, law, [0, 1], ResourceLimits(max_states=5))

    def test_invalid_policy_state_grid_and_limits(self):
        cfg, initial, law = config(), InventoryState(0, ()), FiniteDemand((0,), (1,))
        for policy in (
            lambda n, s: 2,
            lambda n, s: -1,
            lambda n, s: True,
            lambda n, s: 0.5,
        ):
            with self.assertRaises((ValueError, TypeError)):
                evaluate_policy(cfg, initial, law, policy)
        for grid in ([], [-1], [True], [0.5]):
            with self.assertRaises((ValueError, TypeError)):
                tune_base_stock(cfg, initial, law, grid)
        with self.assertRaises(ValueError):
            solve_dp(cfg, InventoryState(0, (1,)), law)
        for kwargs in (
            {"max_states": 0},
            {"max_transitions": True},
            {"max_seconds": 0},
            {"max_seconds": float("nan")},
            {"max_seconds": 121},
        ):
            with self.assertRaises((ValueError, TypeError)):
                ResourceLimits(**kwargs)
        result = solve_dp(cfg, initial, law)
        with self.assertRaises(ValueError):
            result.action(0, initial)
        with self.assertRaises(KeyError):
            result.action(3, InventoryState(99, ()))

    def test_no_hidden_stock_cap_and_accumulated_cost_overflow(self):
        cfg, law = config(horizon=2, costs=(0, 1, 0, 0)), FiniteDemand((0,), (1,))
        result = solve_dp(cfg, InventoryState(100, ()), law)
        self.assertIn((1, InventoryState(101, ())), result.values)
        cfg = config(horizon=2, maximum=0, costs=(1e308, 0, 0, 0))
        for run in (
            lambda: solve_dp(cfg, InventoryState(1, ()), law),
            lambda: evaluate_policy(cfg, InventoryState(1, ()), law, lambda n, s: 0),
        ):
            with self.assertRaises(OverflowError):
                run()


class CommandTests(unittest.TestCase):
    def test_cli_failure_exit_has_diagnostic_and_no_partial_result(self):
        base = json.loads((ROOT / "experiments/configs/m2_tiny.json").read_text())
        limited = copy.deepcopy(base)
        limited["limits"]["max_states"] = 1
        for raw, message in [
            (b"{}", "requires exactly"),
            (json.dumps(limited).encode(), "state limit"),
        ]:
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(Path, "read_bytes", return_value=raw):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as caught:
                        cli.main(["--config", "synthetic-test.json"])
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn(message, stderr.getvalue())

    def test_malformed_config_rejected(self):
        base = json.loads((ROOT / "experiments/configs/m2_tiny.json").read_text())
        cases = [[], {**base, "unknown": 1}]
        for path, value in [
            (("inventory", "horizon"), 0),
            (("inventory", "costs", "holding"), "1"),
            (("inventory", "costs", "holding"), float("nan")),
            (("initial_state", "pipeline"), [1]),
            (("demand", "probabilities"), [0.2, 0.2]),
            (("base_stock_levels",), []),
            (("limits", "max_seconds"), 121),
        ]:
            bad = copy.deepcopy(base)
            node = bad
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value
            cases.append(bad)
        for value in cases:
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                cli.parse_config(json.dumps(value).encode())
        with self.assertRaisesRegex(ValueError, "duplicate"):
            cli.parse_config(b'{"inventory": {}, "inventory": {}}')

    def test_demo_reproducible_with_provenance(self):
        command = [
            sys.executable,
            str(ROOT / "scripts/run_m2_reference.py"),
            "--config",
            str(ROOT / "experiments/configs/m2_tiny.json"),
        ]
        first = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=15, check=True
        )
        second = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=15, check=True
        )
        self.assertEqual(first.stdout, second.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(
            result["optimal_expected_cost"], result["returned_policy_expected_cost"]
        )
        self.assertEqual(result["additional_terminal_value"], 0)
        self.assertEqual(len(result["provenance"]["source_commit"]), 40)
        self.assertEqual(len(result["provenance"]["config_sha256"]), 64)
        self.assertIn(
            "src/inventory_ejor/solvers/finite_horizon.py",
            result["provenance"]["source_sha256"],
        )
        self.assertIsNone(result["seed"])
        naive = result["base_stock"]["naive_constant"]
        aware = result["base_stock"]["horizon_aware"]
        self.assertEqual(naive["expected_cost"], 3)
        self.assertEqual(aware["expected_cost"], 2.875)
        self.assertEqual(aware["gap_to_dp"], {"absolute": 0, "relative": 0})
        self.assertEqual(naive["limits_per_variant"], aware["limits_per_variant"])
        self.assertEqual(naive["grid_costs"].keys(), aware["grid_costs"].keys())


if __name__ == "__main__":
    unittest.main()
