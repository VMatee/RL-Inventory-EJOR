"""Opt-in future numerical checks; default only prints the unexecuted checklist."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-numerical-validation", action="store_true")
    parser.add_argument("--gpu", type=int)
    args = parser.parse_args(argv)
    if not args.approve_numerical_validation:
        print(
            "NOT RUN: synthetic M1/vector parity, sampler "
            "checks, optional single-GPU tiny GP validatio"
            "n."
        )
        print(
            "Request owner review first; this command does"
            " not grant baseline-run approval."
        )
        return 0
    if args.gpu is not None and not 0 <= args.gpu <= 31:
        parser.error("GPU index outside 0..31")
    env = dict(os.environ)
    env["EJOR_APPROVED_NUMERICAL_VALIDATION"] = "1"
    env["EJOR_APPROVED_CUDA_VALIDATION"] = "1" if args.gpu is not None else "0"
    env["CUDA_VISIBLE_DEVICES"] = "" if args.gpu is None else str(args.gpu)
    env["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    env["OMP_NUM_THREADS"] = "2"
    env["MKL_NUM_THREADS"] = "2"
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "validation_m4_numerics.py",
        "-v",
    ]
    completed = subprocess.run(command, cwd=ROOT, env=env, timeout=120, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
