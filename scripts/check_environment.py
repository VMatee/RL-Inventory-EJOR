#!/usr/bin/env python3
"""Read-only validation for the current project's Python ML environment.

A successful import/GPU operation verifies basic installation, not scientific correctness.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    expected = repo.parent / "code" / ".venv"
    data = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "expected_virtualenv": str(expected),
        "packages": {},
        "torch_cuda": {},
    }
    packages = [
        "numpy", "scipy", "pandas", "sklearn", "matplotlib", "pyarrow",
        "gpytorch", "botorch", "gymnasium", "stable_baselines3",
        "tensorboard", "pytest", "inventory_ejor",
    ]
    errors: list[str] = []
    if expected.resolve() != Path(sys.prefix).resolve():
        errors.append(f"Wrong Python environment: {sys.prefix}; expected {expected}")
    for name in packages:
        try:
            mod = importlib.import_module(name)
            data["packages"][name] = getattr(mod, "__version__", "imported")
        except Exception as exc:  # report exact failing import
            data["packages"][name] = f"FAILED ({type(exc).__name__}: {exc})"
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    try:
        import torch
        data["packages"]["torch"] = torch.__version__
        cuda = data["torch_cuda"]
        cuda["built_with"] = torch.version.cuda
        cuda["available"] = bool(torch.cuda.is_available())
        cuda["device_count"] = torch.cuda.device_count() if cuda["available"] else 0
        if not cuda["available"]:
            errors.append("PyTorch CUDA is not available")
        else:
            cuda["device_names"] = [torch.cuda.get_device_name(i) for i in range(cuda["device_count"])]
            # Very small allocations on each available GPU; no training.
            for i in range(cuda["device_count"]):
                x = torch.ones((2, 2), device=f"cuda:{i}")
                assert torch.isfinite((x @ x).sum()).item()
            if cuda["device_count"] != 4:
                errors.append(f"Expected four GPUs, detected {cuda['device_count']}")
    except Exception as exc:
        data["torch_cuda"]["failure"] = f"{type(exc).__name__}: {exc}"
        errors.append(f"torch: {type(exc).__name__}: {exc}")
    data["errors"] = errors
    print(json.dumps(data, indent=2, ensure_ascii=True, default=str))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
