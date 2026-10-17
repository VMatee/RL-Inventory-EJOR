# Tests

From the Git checkout, run `../code/.venv/bin/python -m unittest discover -s tests -v` or `../code/.venv/bin/python -m pytest tests -q`.

M0 tests validate infrastructure, citation resolution and provenance-runner argument handling. M1 tests in `test_inventory_env.py` validate deterministic integer lost-sales stock flow, lead time L=1/2/3/4/5, fixed and variable costs, horizon/terminal behavior, rejection of invalid inputs, Gymnasium interface and independence from future demand. The hand-computed fixture `fixtures/m1_hand_calculated.json` and a separately written event-calendar comparator provide references beyond the production transition logic. Run `make m1-reference` for a readable JSON replay. This does NOT prove general inventory policy optimality, GP uncertainty validity or RL results. M2 must add an independently validated small-state DP benchmark.
