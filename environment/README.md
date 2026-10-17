# Isolated Python environment for RL-Inventory-EJOR

The **outer workspace** is `~/Desktop/work/research journal/RL-Inventory-EJOR`.
Inside it:
- `github/` is the one authoritative Git repository (including .git, manuscript, src, tests, experiments, data and research).
- `code/.venv/` is the only **active** project Python virtual environment. It is **not** Git-tracked.
- `code/src`, `code/tests` and `code/experiments` are local symbolic links into the Git repository, not independent source copies.
- `.serena/` stays in the outer workspace so the existing connected SeneraAiServer project remains usable.
- `code/legacy-venv-pre-migration/` may contain the preserved initial minimal venv; it is **not usable after moving**, and can be removed later by the owner once satisfied with the replacement.

All relative commands in this repository assume `cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"`. Quote paths because the parent contains spaces.

## Baseline setup (Ubuntu 22.04; Python 3.10; NVIDIA driver 580 / four RTX 3090)

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
python3.10 -m venv ../code/.venv
../code/.venv/bin/python -m pip install --upgrade pip setuptools wheel
# Verified official PyTorch CUDA 13.0 wheel line. No system CUDA toolkit needed for standard wheels.
../code/.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cu130 'torch==2.9.1'
../code/.venv/bin/python -m pip install -r environment/requirements-science.in -r environment/requirements-dev.in
../code/.venv/bin/python -m pip check
../code/.venv/bin/python scripts/check_environment.py
../code/.venv/bin/python -m pip freeze --all > environment/requirements-lock.txt
```

The dependency snapshot is a version record from the installed Linux/Python/CUDA environment, **not a cross-platform lock**. Reproduction on other hardware needs its own compatible PyTorch wheel before installing the remaining packages. Installations may download several gigabytes. Use only the virtual environment's pip; do not install global or OS packages, change drivers or reconfigure system CUDA.

The snapshot should be committed only after successful installation and verification; the environment folder, raw data, checkpoints, logs and cache should remain local. Before reproducibility claims, record the package versions, GPU smoke test, code commit and corresponding run configuration.

## What this DOES NOT install

It does not fetch M5/Favorita datasets, install DynaPlex/TED from separate repositories, compile custom CUDA extensions, or install every possible GP/RL package. TensorFlow, Ray, CUDA toolkit and other frameworks remain optional until a baseline demonstrably requires them.

## Checks

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
../code/.venv/bin/python scripts/check_environment.py
../code/.venv/bin/python scripts/check_project.py
../code/.venv/bin/python -m unittest discover -s tests -v
```

A missing GPU or failed package import must be reported, not silently interpreted as success.
