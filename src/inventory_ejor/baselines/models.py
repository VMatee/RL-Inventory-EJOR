"""Initial demand-model baselines; NOT executed during preparation.

Models receive ONLY M3 LearnerView and prespecified settings. No repository,
raw-data, evaluator path, source hash or full plan is supplied to a model.
GP is an empirical-Bayes log1p-Gaussian surrogate, not a count-likelihood GP.
"""

from __future__ import annotations

import math
from datetime import date, timedelta


def make_features(history, days):
    """Known time + civil-weekday features; no future-observed covariates."""
    first = history.observations[0]
    start = date.fromisoformat(first.date)
    scale = max(len(history.observations) - 1, 1)
    return [
        [
            (d - first.day) / scale,
            math.sin(
                2 * math.pi * (start + timedelta(days=d - first.day)).weekday() / 7
            ),
            math.cos(
                2 * math.pi * (start + timedelta(days=d - first.day)).weekday() / 7
            ),
        ]
        for d in days
    ]


class SimpleSampler:
    """Empirical iid plug-in or conjugate Gamma-Poisson predictive paths."""

    def __init__(self, view, kind, prior, max_generated_count):
        import numpy as np

        self.values = np.asarray(
            [o.sales for o in view.history.observations], dtype=np.int64
        )
        if len(self.values) != len(view.history.observations) or not len(self.values):
            raise ValueError("Empty or malformed training history")
        self.kind = kind
        self.max_count = max_generated_count
        self.shape = float(prior["prior_shape"]) + int(self.values.sum())
        self.rate = float(prior["prior_rate"]) + len(self.values)
        self.metadata = {
            "kind": kind,
            "fitting_real_observations": len(self.values),
            "online_parameter_updates": False,
            "uncertainty": (
                "iid empirical plug-in: no epistemic posterior"
                if kind == "empirical"
                else "Gamma rate uncertainty; Poisson noise conditi"
                "onal on each sampled rate"
            ),
            "prior": prior if kind == "gamma_poisson" else None,
            "posterior_shape": self.shape if kind == "gamma_poisson" else None,
            "posterior_rate": self.rate if kind == "gamma_poisson" else None,
        }

    def draw(self, offset, horizon, count, seed):
        import numpy as np

        if offset < 0 or horizon < 1 or count < 1:
            raise ValueError("Invalid predictive path shape")
        rng = np.random.default_rng(seed)
        if self.kind == "empirical":
            draws = rng.choice(self.values, size=(count, horizon), replace=True)
        elif self.kind == "gamma_poisson":
            # One rate per complete trajectory, not a fresh epistemic model each day.
            rates = rng.gamma(shape=self.shape, scale=1.0 / self.rate, size=(count, 1))
            draws = rng.poisson(rates, size=(count, horizon))
        else:
            raise ValueError("Unsupported simple sampler")
        if (draws < 0).any() or (draws > self.max_count).any():
            raise ValueError(
                "Predictive count guard exceeded; do not silently clip tails"
            )
        return draws


class GPSampler:
    """Exact GP on standardized log1p sales; independent per-SKU GPU worker.

    Kernel hyperparameters are type-II point estimates. Latent posterior draws
    preserve within-path temporal covariance; independent Gaussian likelihood
    noise is added separately, then the declared rounded nonnegative inverse
    transform defines a surrogate count law. No hyperparameter posterior or
    calibration guarantee is implied. The demand model stays frozen in replay.
    """

    def __init__(
        self, view, horizon, config, max_generated_count, seed, memory_fraction
    ):
        import gpytorch
        import torch

        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError(
                "Expected exactly one isolated visible CUDA GPU; no silent CPU fallback"
            )
        torch.cuda.set_device(0)
        torch.cuda.set_per_process_memory_fraction(memory_fraction, 0)
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
        self.torch, self.gpytorch = torch, gpytorch
        self.device = torch.device("cuda:0")
        self.config = config
        self.max_count = max_generated_count
        self.history = view.history
        self.horizon = horizon
        self.origin = view.history.origin
        x = torch.tensor(
            make_features(view.history, [o.day for o in view.history.observations]),
            dtype=torch.float64,
            device=self.device,
        )
        y0 = torch.log1p(
            torch.tensor(
                [o.sales for o in view.history.observations],
                dtype=torch.float64,
                device=self.device,
            )
        )
        self.mean = y0.mean()
        sd = y0.std(unbiased=False)
        self.scale = sd if float(sd.item()) > 0 else torch.ones_like(sd)
        y = (y0 - self.mean) / self.scale

        class ExactCountSurrogate(gpytorch.models.ExactGP):
            def __init__(self, train_x, train_y, likelihood):
                super().__init__(train_x, train_y, likelihood)
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(
                    gpytorch.kernels.RBFKernel(ard_num_dims=3)
                )

            def forward(self, inputs):
                return gpytorch.distributions.MultivariateNormal(
                    self.mean_module(inputs), self.covar_module(inputs)
                )

        likelihood = gpytorch.likelihoods.GaussianLikelihood(
            noise_constraint=gpytorch.constraints.GreaterThan(config["noise_floor"])
        )
        self.model = ExactCountSurrogate(x, y, likelihood).to(
            device=self.device, dtype=torch.float64
        )
        self.likelihood = self.model.likelihood
        self.model.train()
        self.likelihood.train()
        optimizer = torch.optim.Adam(
            self.model.parameters(), lr=config["learning_rate"]
        )
        mll = gpytorch.mlls.ExactMarginalLogLikelihood(self.likelihood, self.model)
        losses = []
        with (
            gpytorch.settings.max_cholesky_size(2048),
            gpytorch.settings.cholesky_jitter(double_value=config["cholesky_jitter"]),
        ):
            for _ in range(config["steps"]):
                optimizer.zero_grad(set_to_none=True)
                loss = -mll(self.model(x), y)
                if not torch.isfinite(loss).item():
                    raise FloatingPointError("Nonfinite GP marginal likelihood")
                loss.backward()
                if any(
                    p.grad is not None and not torch.isfinite(p.grad).all().item()
                    for p in self.model.parameters()
                ):
                    raise FloatingPointError("Nonfinite GP gradient")
                optimizer.step()
                losses.append(float(loss.item()))
        self.model.eval()
        self.likelihood.eval()
        self.metadata = {
            "kind": "exact_log1p_gaussian_surrogate",
            "device": torch.cuda.get_device_name(0),
            "fitting_real_observations": len(view.history.observations),
            "dtype": "float64",
            "gp_optimizer_steps": config["steps"],
            "marginal_likelihood_losses": losses,
            "hyperparameters": {
                k: v.detach().cpu().tolist() for k, v in self.model.named_parameters()
            },
            "noise_variance_standardized_log_scale": float(
                self.likelihood.noise.item()
            ),
            "log_transform_mean": float(self.mean.item()),
            "log_transform_scale": float(self.scale.item()),
            "uncertainty": "latent-function posterior conditional on fitt"
            "ed hyperparameters plus likelihood noise",
            "count_transform": "round(max(expm1(z*training_sd + training_mean), 0))",
            "limitations": [
                "not Poisson/count-likelihood GP",
                "no hyperparameter uncertainty",
                "not automatically calibrated",
                "no latent-demand reconstruction",
            ],
            "online_parameter_updates": False,
        }

    def draw(self, offset, horizon, count, seed):
        torch, gpytorch = self.torch, self.gpytorch
        if offset < 0 or horizon < 1 or offset + horizon > self.horizon:
            raise ValueError("Predictive window outside declared evaluation horizon")
        torch.manual_seed(seed)
        days = list(range(self.origin + offset, self.origin + offset + horizon))
        x = torch.tensor(
            make_features(self.history, days), dtype=torch.float64, device=self.device
        )
        with (
            torch.no_grad(),
            gpytorch.settings.max_cholesky_size(2048),
            gpytorch.settings.cholesky_jitter(
                double_value=self.config["cholesky_jitter"]
            ),
        ):
            latent = self.model(x).rsample(torch.Size([count]))
            noise = torch.randn(latent.shape, dtype=latent.dtype, device=latent.device)
            observations = latent + self.likelihood.noise.sqrt() * noise
            transformed = torch.expm1(observations * self.scale + self.mean)
            if not torch.isfinite(transformed).all().item():
                raise FloatingPointError(
                    "GP inverse transform overflow; refusing a fab"
                    "ricated clipped forecast"
                )
            draws = transformed.clamp_min(0).round()
            if (draws > self.max_count).any().item():
                raise ValueError(
                    "GP tail exceeds declared count guard; record "
                    "failure, never clip high counts"
                )
            return draws.to(torch.int64)
