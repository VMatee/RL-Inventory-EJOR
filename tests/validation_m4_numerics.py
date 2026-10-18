"""OPT-IN numerical validation. Not collected by normal test*.py discovery.

These tests execute synthetic controllers, and optionally a tiny GP fit. They
have NOT been run in the preparation-only task. Owner approval is required.
"""

from __future__ import annotations

import os
import unittest
from datetime import date, timedelta

APPROVED = os.environ.get("EJOR_APPROVED_NUMERICAL_VALIDATION") == "1"
CUDA_APPROVED = os.environ.get("EJOR_APPROVED_CUDA_VALIDATION") == "1"


@unittest.skipUnless(APPROVED, "Owner has not authorized numerical validation")
class DeferredNumericalValidation(unittest.TestCase):
    def test_numpy_batched_cost_matches_independent_m1_loop(self):
        import numpy as np

        from inventory_ejor.baselines.controllers import numpy_costs, order_up_to
        from inventory_ejor.envs import (
            CostParameters,
            InventoryConfig,
            InventoryState,
            transition,
        )

        paths = np.array([[0, 3, 1, 4], [2, 0, 5, 1], [1, 1, 1, 1]], dtype=np.int64)
        for lead in (1, 2, 3):
            scenario = {
                "lead_time": lead,
                "max_order": 4,
                "costs": {
                    "holding": 1.0,
                    "lost_sales": 7.0,
                    "variable_order": 0.5,
                    "fixed_order": 2.0,
                },
            }
            state = InventoryState(2, (1,) * (lead - 1))
            levels = [0, 1, 3, 6]
            config = InventoryConfig(lead, 4, 4, CostParameters(**scenario["costs"]))
            expected = []
            for level in levels:
                costs = []
                for path in paths:
                    s, cost = state, 0.0
                    for t, d in enumerate(path):
                        q = order_up_to(4 - t, s, level, scenario)
                        result = transition(config, s, q, int(d))
                        cost += result.costs.total
                        s = result.next_state
                    costs.append(cost)
                expected.append(sum(costs) / len(costs))
            np.testing.assert_allclose(
                numpy_costs(paths, scenario, state, levels),
                expected,
                rtol=0,
                atol=1e-12,
            )

    def test_seeded_inventory_cost_parity_over_multiple_states(self):
        """Compare deterministic M1 trajectories with varied pipeline and first order.

        This is a bounded numerical fixture, not a real-data baseline run.
        GPU comparison runs only when tiny CUDA validation is separately enabled.
        """
        import numpy as np

        from inventory_ejor.baselines.controllers import (
            numpy_costs,
            order_up_to,
        )
        from inventory_ejor.envs import (
            CostParameters,
            InventoryConfig,
            InventoryState,
            transition,
        )

        if CUDA_APPROVED:
            import torch

        rng = np.random.default_rng(8292026)
        checked = 0
        overrides = 0
        for lead in (1, 2, 3, 4):
            for horizon in (1, 2, 3, 4, 6, 8):
                for attempt in range(3):
                    costs = {
                        "holding": 1.25,
                        "lost_sales": 9.5,
                        "variable_order": 0.75,
                        "fixed_order": 2.5,
                    }
                    scenario = {
                        "lead_time": lead,
                        "max_order": 4,
                        "costs": costs,
                    }
                    state = InventoryState(
                        int(rng.integers(0, 7)),
                        tuple(int(v) for v in rng.integers(0, 5, size=lead - 1)),
                    )
                    paths = rng.integers(0, 9, size=(5, horizon), dtype=np.int64)
                    levels = [0, 1, 3, 6, 10]
                    initial_orders = [0, 1, 2, 3, 4] if attempt == 2 else None
                    cfg = InventoryConfig(lead, horizon, 4, CostParameters(**costs))
                    reference = []
                    for candidate, level in enumerate(levels):
                        trajectory_costs = []
                        for demands in paths:
                            current = state
                            total = 0.0
                            for t, demand in enumerate(demands):
                                remaining = horizon - t
                                if remaining <= lead:
                                    order = 0
                                elif t == 0 and initial_orders is not None:
                                    order = initial_orders[candidate]
                                else:
                                    order = order_up_to(
                                        remaining, current, level, scenario
                                    )
                                step = transition(cfg, current, order, int(demand))
                                total += step.costs.total
                                current = step.next_state
                            trajectory_costs.append(total)
                        reference.append(np.mean(trajectory_costs))

                    with self.subTest(lead=lead, horizon=horizon, attempt=attempt):
                        np.testing.assert_allclose(
                            numpy_costs(paths, scenario, state, levels, initial_orders),
                            reference,
                            rtol=0,
                            atol=1e-12,
                        )
                        if CUDA_APPROVED:
                            from inventory_ejor.baselines.controllers import (
                                torch_costs,
                            )

                            result = torch_costs(
                                torch.as_tensor(paths, device="cuda:0"),
                                scenario,
                                state,
                                levels,
                                initial_orders,
                            )
                            np.testing.assert_allclose(
                                result.detach().cpu().numpy(),
                                reference,
                                rtol=0,
                                atol=1e-12,
                            )
                    checked += 1
                    overrides += int(initial_orders is not None)
        self.assertEqual((checked, overrides), (72, 24))

    def test_tail_arrivals_do_not_generate_orders(self):
        from inventory_ejor.baselines.controllers import order_up_to
        from inventory_ejor.envs import InventoryState

        scenario = {"lead_time": 3, "max_order": 10}
        self.assertEqual(order_up_to(3, InventoryState(0, (0, 0)), 10, scenario), 0)
        self.assertEqual(order_up_to(4, InventoryState(0, (0, 0)), 10, scenario), 10)

    def test_gamma_poisson_draws_are_reproducible_and_nonnegative(self):
        from types import SimpleNamespace

        import numpy as np

        from inventory_ejor.baselines.models import SimpleSampler
        from inventory_ejor.data.contracts import History, Observation

        h = History(
            "synthetic-only",
            "test",
            29,
            tuple(
                Observation(
                    d, (date(2020, 1, 1) + timedelta(days=d - 1)).isoformat(), d % 3
                )
                for d in range(1, 29)
            ),
        )
        m = SimpleSampler(
            SimpleNamespace(history=h),
            "gamma_poisson",
            {"prior_shape": 1.0, "prior_rate": 1.0},
            10000,
        )
        a, b = m.draw(0, 7, 64, 1), m.draw(0, 7, 64, 1)
        np.testing.assert_array_equal(a, b)
        self.assertTrue((a >= 0).all())
        self.assertEqual(m.metadata["posterior_shape"], 29.0)
        self.assertEqual(m.metadata["posterior_rate"], 29.0)

    @unittest.skipUnless(
        CUDA_APPROVED, "Separate approval for tiny CUDA validation required"
    )
    def test_gpu_tensor_costs_match_cpu_reference(self):
        import numpy as np
        import torch

        from inventory_ejor.baselines.controllers import numpy_costs, torch_costs
        from inventory_ejor.envs import InventoryState

        if not torch.cuda.is_available():
            self.fail("Approved GPU validation requested but CUDA unavailable")
        paths = np.array([[0, 1, 4, 0], [1, 3, 2, 1]], dtype=np.int64)
        for lead in (1, 2, 3):
            scenario = {
                "lead_time": lead,
                "max_order": 4,
                "costs": {
                    "holding": 1.0,
                    "lost_sales": 7.0,
                    "variable_order": 0.5,
                    "fixed_order": 2.0,
                },
            }
            state = InventoryState(1, (2,) * (lead - 1))
            actual = (
                torch_costs(
                    torch.tensor(paths, device="cuda:0"), scenario, state, [0, 2, 5]
                )
                .cpu()
                .numpy()
            )
            np.testing.assert_allclose(
                actual,
                numpy_costs(paths, scenario, state, [0, 2, 5]),
                rtol=0,
                atol=1e-12,
            )

    @unittest.skipUnless(CUDA_APPROVED, "Separate approval for tiny GP fit required")
    def test_tiny_gp_fit_and_joint_predictive_sampling(self):
        from types import SimpleNamespace

        import torch

        from inventory_ejor.baselines.models import GPSampler
        from inventory_ejor.data.contracts import History, Observation

        h = History(
            "synthetic-only",
            "test",
            29,
            tuple(
                Observation(
                    d, (date(2020, 1, 1) + timedelta(days=d - 1)).isoformat(), d % 3
                )
                for d in range(1, 29)
            ),
        )
        m = GPSampler(
            SimpleNamespace(history=h),
            4,
            {
                "steps": 2,
                "learning_rate": 0.05,
                "noise_floor": 0.0001,
                "cholesky_jitter": 1e-6,
            },
            1000000,
            0,
            0.5,
        )
        paths = m.draw(0, 4, 8, 123)
        self.assertEqual(tuple(paths.shape), (8, 4))
        self.assertEqual(paths.device.type, "cuda")
        self.assertTrue(torch.isfinite(paths).all().item())
        self.assertTrue((paths >= 0).all().item())
        # Joint latent + observation-noise draws must be repeatable for a pinned seed.
        torch.testing.assert_close(m.draw(0, 4, 8, 123), paths, rtol=0, atol=0)
        with self.assertRaisesRegex(ValueError, "outside declared evaluation horizon"):
            m.draw(1, 4, 8, 123)


if __name__ == "__main__":
    unittest.main()
