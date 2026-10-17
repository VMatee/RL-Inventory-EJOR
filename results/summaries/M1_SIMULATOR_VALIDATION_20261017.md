# M1 deterministic inventory simulator: validation record — 2026-10-17

## Research scope and status

This is **engineering/behavioral validation**, not evidence of a GP/RL contribution, a theorem, inventory optimality, or any measured performance on real retail data. The owner requested to prepare M1 and remove the obsolete Python environment.

M1's previously unspecified modeling conventions were selected and explicitly recorded in `theory/INVENTORY_MODEL.md` and `docs/DECISION_LOG.md`, including the after-arrival decision epoch, order arrival at the start of `t+L`, lost sales with no backlog, costs assessed after demand/before next receipt, and zero extra terminal charge/salvage. These are **provisional engineering conventions pending owner review before M2/theory**.

## Files and behavior

- `src/inventory_ejor/envs/lost_sales.py`: pure `transition(config,state,order,demand)`, immutable state and cost dataclasses, strict integer/action/cost validation, no clipping, full receipt pipeline and finite-horizon Gymnasium wrapper.
- `src/inventory_ejor/envs/__init__.py`: reusable API export.
- `tests/fixtures/m1_hand_calculated.json`: independently hand-worked five-period L=3 scenario, with every intermediate state and cost component; **total cost = 47**.
- `tests/test_inventory_env.py`: exact hand trajectory, separate event-calendar comparator, L=1/2/3/4/5 timing checks, stock conservation, cost decomposition, terminal-state accounting, invalid inputs, no future-demand in policy observation and Gymnasium API.
- `scripts/run_m1_reference.py` and `make m1-reference`: deterministic fixture replay with declared scope and machine-readable output.
- Manual GitHub Actions infrastructure job extended to install minimal numpy/gymnasium/ruff dependencies and run M1 tests. This workflow is manual; **no remote CI execution is claimed**.

## Specific invariants tested

```text
state at decision t: x_t already includes arrivals due at t
pending pipeline length: L-1 (empty when L=1)
sales_t = min(x_t, d_t)
lost_t = d_t - sales_t
ending_t = x_t - sales_t
arriving_(t+1) = (pipeline_t + (q_t,))[0]
x_(t+1) = ending_t + arriving_(t+1)
pipeline_(t+1) = (pipeline_t + (q_t,))[1:]
cost_t = h*ending_t + b*lost_t + c*q_t + K*1[q_t>0]
terminal cost beyond sum_{t=0}^{T-1} cost_t: 0
```

The post-period-T hypothetical state is not a terminal salvage account. The terminal snapshot retains stock immediately *after* demand in T-1 and all L still-pending batches.

## Executed commands and results

From `<workspace>/github`, using `../code/.venv/bin/python`:

```bash
../code/.venv/bin/python -m unittest discover -s tests -v
../code/.venv/bin/python -m pytest tests -q
../code/.venv/bin/python -m ruff check src/inventory_ejor/envs tests/test_inventory_env.py scripts/run_m1_reference.py
../code/.venv/bin/python scripts/check_project.py
../code/.venv/bin/python scripts/run_m1_reference.py
git diff --check
```

Expected audited outputs: **34 unittest cases pass (six infrastructure plus 28 M1), 34 pytest cases pass**, with separately reported unittest subtests; Ruff and static reference checks pass; fixture replay reports `matched_hand_fixture=true` and `total_cost=47`. Inspect the final post-commit output in the handoff before relying on these numbers.

The owner-requested removal of `code/legacy-venv-pre-migration` was guarded by checks that the path was exactly the expected obsolete venv, no process was using it, and the replacement `code/.venv` could import and run PyTorch/GPyTorch. The old folder is absent; the active venv and Git history are intact.

## Scientific and implementation limitations

- M1 consumes **controlled/fully observed exogenous demand**. Using sales data as if uncensored demand is not validated here. Hidden demand features or a nonstationary/autocorrelated process can require additional decision-time state, to be specified later.
- The deterministic Gym trace is for reproduction/testing; a real or malicious agent can inspect private Python attributes if handed the raw env object. Policy information discipline must be enforced by later training/evaluation drivers.
- Fixed initial stock and pipeline are after the period-zero receipt; no warmup, terminal salvage, backlog, disposal, stock capacity or perishability is modeled.
- The finite-horizon boundary may favor peculiar end-of-horizon ordering policies. M2 must decide whether to include terminal value/rollout extensions before comparing optimal policies; changes must be applied to equations and tests together.
- No demand generator, DP algorithm, GP model, neural policy, published benchmark reproduction, M5/Favorita dataset or new computational theorem has been implemented.
- GitHub Actions job was edited but is **not claimed to have run**. The local suite is the validation source for this handoff.

## Next acceptance gate

Obtain the owner's approval or requested edits to decision timing, L convention, initial pipeline definition, unit counts, cost parameters and terminal horizon boundary. After that, M2 may implement an independent small-state finite-support dynamic-programming solution and tuned base-stock benchmark; do not conflate those with the tested M1 simulator.
