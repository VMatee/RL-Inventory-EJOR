# Local workspace migration and GP/RL environment setup — 2026-10-17

## Intent and boundaries

User-authorized workspace reorganization and Python virtual-environment installation. This is **infrastructure validation only**, not an inventory-control scientific result. The canonical project remains the private repository `VMatee/RL-Inventory-EJOR`; the research topic and methods were not changed.

## Paths and preservation

- Workspace parent: `/home/jvserver/Desktop/work/research journal/RL-Inventory-EJOR`
- Canonical Git checkout: `<workspace>/github/` (moved as a unit with `.git/`; original history/remote preserved)
- Serena configuration: `<workspace>/.serena/` (retained at original active workspace root)
- New Python 3.10.12 environment: `<workspace>/code/.venv/`
- Preserved pre-migration minimal venv: `<workspace>/code/legacy-venv-pre-migration/` (do **not** use after moving; old shebangs may be invalid)
- Local convenience symlinks: `code/src`, `code/tests`, `code/experiments` point into `github/`. Never independently edit/copy a second implementation.
- Working code is versioned only under `github/src/`; `pyproject.toml` permits an editable install.

## Dependencies actually installed into new virtualenv

- Python: 3.10.12
- PyTorch: 2.9.1+cu130 (official CUDA 13.0 wheel; no system CUDA toolkit installed)
- NumPy: 2.2.6; SciPy: 1.15.3; Pandas: 2.3.3; scikit-learn: 1.7.2
- GPyTorch: 1.14; BoTorch: 0.15.1 (compatible with Python 3.10)
- Gymnasium: 1.4.0; Stable-Baselines3: 2.9.0
- TensorBoard: 2.21.0; PyArrow: 24.0.0; JupyterLab: 4.6.4
- pytest: 9.1.1; Ruff: 0.17.1
- See `environment/requirements-lock.txt` for the exact resolved package snapshot (not a universal lock).

The first bounded CUDA PyTorch wheel installation reached its time cap during installation; a second invocation reused cached wheels and completed successfully. The science/development dependency installation completed successfully and `pip check` reported no broken requirements.

## Actual smoke validations

- `scripts/check_environment.py`: package imports, active virtualenv, CUDA 13.0, four GPUs — passed.
- Four NVIDIA RTX 3090 (24 GB each): a small on-device tensor matrix operation passed on GPU 0, 1, 2 and 3.
- A small BoTorch SingleTaskGP posterior computation with CUDA tensors succeeded on GPU 0, yielding a finite `(3, 1)` posterior mean. **This is an import/API smoke test, not GP calibration or numerical research.**
- Python source installed in editable mode with `pip install -e .`.
- `make -C github check`: passed; 16 bibliography keys resolve (infrastructure-only).
- `make -C github test`: all six unit tests passed.
- `code/.venv/bin/python -m pytest github/tests -q`: six tests passed.
- `git -C github diff --check`: passed before committing.
- Post-merge Git synchronization and the final commit SHA are checked separately at handoff.

## Not done

No M5/Favorita data, no DynaPlex/TED setup, no full inventory environment, no neural policy training or numerical claims, no system-level NVIDIA/CUDA/OS changes and no local TeX distribution installation. Historical notes may describe the old path and initial empty venv; do not rewrite historical provenance.

## Safe user commands

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
bash scripts/sync_main.sh   # clean, idle main only
../code/.venv/bin/python scripts/check_environment.py
../code/.venv/bin/python scripts/check_project.py
../code/.venv/bin/python -m unittest discover -s tests -v
```

To run Python interactively: `source "../code/.venv/bin/activate"` after entering `github/`. Use `deactivate` to exit. The `code/.venv` directory, wheel caches, raw datasets and checkpoints are not committed.
