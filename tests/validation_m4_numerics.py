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


if __name__ == "__main__":
    unittest.main()
