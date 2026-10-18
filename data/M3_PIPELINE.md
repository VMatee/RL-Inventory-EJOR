# M3 local data preparation

Engineering scope: reproducible local preparation and access contracts. Scientific
acceptance and final dates remain pending in `experiments/protocol/EVALUATION.md`.
The existing five M5 sources are read-only. No model fitting occurs.

From `github/`, run the bounded demonstration through the existing wrapper:

```bash
timeout 120s ../code/.venv/bin/python scripts/run_experiment.py --config experiments/configs/m3_development_demo.json --seed 0 --timeout 110 --allow-dirty -- ../code/.venv/bin/python scripts/prepare_m3.py --config experiments/configs/m3_development_demo.json --seed 0
```

This consumes seed 0 for stable candidate ranking. The child rejects a different
CLI seed. It creates a fresh ignored `data/processed/m3-demo-*` directory and the
wrapper prints a fresh `results/runs/*/manifest.json` path. Look in that run's
`console.log` for the processed directory and aggregate checks. No existing path
is overwritten. Direct equivalent, with JSON summary on stdout:

```bash
timeout 120s ../code/.venv/bin/python scripts/prepare_m3.py --config experiments/configs/m3_development_demo.json --seed 0
```

The demo chooses origin d_225 because it is the first day with a complete 224-day
history, and a 28-day development outcome window. It consumes only d_1..d_252
sales values for selected candidates. These are **engineering fixture dates**,
not a proposed final holdout: 2011-01-29..2011-09-09 initial maximum history;
2011-09-10..2011-10-07 outcomes. There is no seed or cutoff search.

## Components and consumer contract

- `inventory_ejor.data.m5`: strict schemas, streaming catalog/selected sales,
  chronological calendar, deterministic ranking, common-history eligibility,
  authorized overlap check, retrospective weekly prices and availability gates.
- `contracts`: immutable history/evaluator types, half-open split phases, shared
  origin windows, training-only normalization, decision-time features.
- `budgets`: machine-readable access ledgers, real-observation unions, distinct
  pooling/pretraining/rich-data labels, exact-contract comparison checks.
- `provenance`: strict JSON, original-input SHA256/size verification, canonical
  artifact hashes, dirty source fingerprints, exclusive output writes.
- `preparation`: bounded development pipeline with one cohort and nested budgets.
- `views`: one saved learner file per task and a checked consumer interface.
- `synthetic`: bounded seeded sampling from an explicit finite iid law; real
  observation count remains zero. This does not fit a demand model or run M2.

The trusted dispatcher reads the run manifest and assigns **one** learner file.
All methods use the same entry for a given series/origin/n. For example:

```python
from pathlib import Path
from inventory_ejor.data.views import load_learner

# Values are supplied by the trusted dispatcher from the preparation manifest.
view = load_learner(
    Path(assigned_file),
    sha256=assigned_hash,
    dataset=assigned_dataset,
    series=assigned_series,
    origin=assigned_origin,
    budget=assigned_n,
)
# view.history.observations, view.normalization, view.features only.
# Evaluator outcomes and other budgets are not attributes of this view.
```

The dispatcher must also validate the method's declared ledger using
`validate_ledger`, the source-window policy, and the actual `view.history`.
It must give final-test outcome access only to its scorer. The local Python API
cannot prevent deliberately opening another file; this is an auditable contract,
not a security claim. Actual model data access remains an M4 integration obligation.

Use `SplitPlan` with explicitly reviewed `Phase`/`Window` objects for later
chronological layouts. The current CLI intentionally accepts only development
demonstrations. The proposal JSON has null dates and is not executable.

## Verification

```bash
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -v
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -p 'test_m3_data.py' -v
timeout 120s ../code/.venv/bin/python -m ruff check --select E,F,I,B,UP src/inventory_ejor/data scripts/prepare_m3.py tests/test_m3_data.py tests/m3_fixtures.py
timeout 120s ../code/.venv/bin/python -m ruff format --check src/inventory_ejor/data scripts/prepare_m3.py tests/test_m3_data.py tests/m3_fixtures.py
```

Fixtures are independent miniature CSVs. Tests never require actual retail data,
Kaggle access, GP/RL training, downloads or GPU execution. The synthetic helper
reuses existing M2 validation and its installed NumPy/Gymnasium dependencies. Local source hashes and
aggregate evidence may be tracked; all restricted derivative artifacts stay ignored.

An independent audit reads original CSVs using `csv` and recomputes statistics
using `statistics`, without calling the preparation/normalization code:

```bash
timeout 120s ../code/.venv/bin/python scripts/audit_m3.py --directory data/processed/m3-demo-9xfx5j08 --repeat data/processed/m3-demo-myd3wrbj --preservation-snapshot results/runs/m3-audit-r1y6p0fm/before.json
```

Those paths identify this session's saved local runs; substitute the output paths
from a future demonstration. `--repeat` and `--preservation-snapshot` are optional.
The audit creates no files. Snapshots must be captured before work to establish
preservation; generating one afterward cannot establish a prior state.

## Corrected identity contract

Use `manifest["learner_dataset_version"]` as the dispatcher's expected dataset
argument to `load_learner`. Never pass the trusted full-content
`manifest["dataset"]` or source hashes to a learner. The required config
`dataset_version` is a fixed logical release label, chosen before withheld data
inspection. Manifest schema 2 retains complete input integrity checks and binds
that label to exact source content. Old saved schema-1 bundles are preserved;
re-run preparation into a fresh directory to obtain corrected learner files.

`manifest["study_information"]` separately counts study-design access. The demo
records 1,204 historical sales cells (1,120 selected plus 84 additional screening),
not the sum of all learners' nested budgets. The ex-post M5 roster can still cause
selection/survivorship bias. This remains a research-design review issue.

Run the independent miniature intervention and all M3 tests:

```bash
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -p 'test_m3_noninterference.py' -v
timeout 120s ../code/.venv/bin/python -m unittest discover -s tests -p 'test_m3*.py' -v
```
