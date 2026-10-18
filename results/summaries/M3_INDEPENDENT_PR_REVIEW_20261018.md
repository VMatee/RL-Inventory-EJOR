# Independent M3 engineering PR review — 2026-10-18

**Status:** reviewed M3 engineering source is suitable for a **human-review Pull Request**. **Not merged**, **not an authorization for M4**, and **not approval of the proposed EJOR experimental design or a claim about real inventory costs**.

## Scope and source preservation

The review used an isolated Git worktree on `review/m3-data-information-pr` created from `main` commit `14d0741ea2328aa28cef7612976357c4b3cb6d53`. The original Codex checkout remained on `feat/m3-data-information-protocol` with uncommitted changes. An exact allowlist of **25** source/config/test/report files was copied; SHA256 of every copied file was checked against the original. The review did not alter the original source checkout, its raw M5 CSVs, processed outputs, experiment runs, backups or Python environment.

The Codex process still active during PR preparation was checked via its real working directory and belonged to the unrelated `RBVR_IJTST_research_code` project, not RL-Inventory-EJOR. No process was writing to this project.

This PR additionally extends the existing **manual-only GitHub Actions** checks with M3 fixture-only tests and scoped Ruff lint/format. The workflow remains `workflow_dispatch`; it does **not** run on PR creation by default, require M5 datasets, train a model, or touch GPUs.

## Scientific and software review

- M5 is **observed sales**, potentially affected by unknown availability/censoring, not independently measured latent demand or retailer inventory costs. The current procedure is a development demonstration, not a final scientific test.
- Chronological history intervals are half-open, with fixed origins, separate evaluator outcomes, and nested real history budgets **28/56/112/224**. Underlying M1/M2 equations and reference fixtures remain unchanged.
- The former future-outcome fingerprint leak is corrected: learner-visible `dataset_version` is a predeclared logical source label; full-content fingerprints remain in the **trusted** provenance/manifest only. Explicitly audited learner artifacts contain no full-source hash, and the evaluator data are a separate file.
- Independent miniature fixture interventions changed only withheld sales at days **225, 226, 251, 270** (training ends day 224). At each intervention all **12 learner artifacts** remained byte-identical; trusted input identity changed. A separate six-test adversarial suite covers logical identity, tampering and information accounting.
- The study-wide information ledger counts **1,120 selected historical cells + 84 additional excluded-candidate screening cells = 1,204 distinct real historical sales cells**. Shared sample/cohort design is more informative than an isolated n=28-day learner; it must never be hidden. The selected M5 roster is ex-post and **selection/survivorship bias remains unresolved**.
- M5 canonical sales columns are `d_1..d_1941` in evaluation and `d_1..d_1913` in validation; the overlap is checked only where authorized. Future features such as price/promotions require documented availability; M3's learner demo uses only predictable civil-calendar features.
- `load_learner` and the information ledger are auditable interfaces, **not an OS isolation barrier**. Any M4 method can bypass them if code accesses the local filesystem directly. M4 integration must enforce a trusted dispatcher and document actual data/compute usage.

## Independently executed checks

Commands were run against the **isolated review worktree**, forcing imports through `PYTHONPATH="$PWD/src"`, using the existing Python 3.10 environment and time-bounded CPU processes:

```bash
PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 timeout 120 ../code/.venv/bin/python -B -m unittest discover -s tests -q
PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 timeout 120 ../code/.venv/bin/python -B -m pytest -p no:cacheprovider -q tests
../code/.venv/bin/python -m ruff check --select E,F,I,B,UP src/inventory_ejor/data scripts/prepare_m3.py scripts/audit_m3.py tests/test_m3_data.py tests/test_m3_noninterference.py tests/m3_fixtures.py
../code/.venv/bin/python -m ruff format --check src/inventory_ejor/data scripts/prepare_m3.py scripts/audit_m3.py tests/test_m3_data.py tests/test_m3_noninterference.py tests/m3_fixtures.py
PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 ../code/.venv/bin/python -B scripts/check_project.py
PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 timeout 30 ../code/.venv/bin/python -B scripts/run_m1_reference.py
PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 timeout 30 ../code/.venv/bin/python -B scripts/run_m2_reference.py --config experiments/configs/m2_tiny.json
```

**Results:** unittest **119/119**, pytest **119 passed + 144 subtests**, all scoped M3 Ruff checks/formatting **passed**, project static check **passed**, M1 fixture cost **47.0**, and M2 DP/horizon-aware/naive costs **2.875 / 2.875 / 3.000**.

The existing prepared M5 schema-2 outputs were independently audited **read-only** from the original checkout using `scripts/audit_m3.py --directory data/processed/m3-demo-_zw6b5hj`: all **5** original CSV source SHA256 identities, **20** learner views, and **1,204** study-wide historical sales cells matched the manifest. The demonstration retained **5 of 8** candidates, including **988 zero-sales cells among 1,120** retained history cells; no stockout or latent-demand inference is justified. Earlier retrospective price alignment found 406/1,120 missing series-day price joins, and prices are not learner features in this M3 demo.

**Additional stronger reproducibility check:** executed a *fresh read-only re-preparation in memory* using review-worktree M3 code and the original raw M5 inputs. All **22/22** schema-2 saved artifact SHA256 hashes and sizes, the task dispatch, study information, and quality statistics exactly matched the earlier processed demonstration. No new dataset or result artifact was written during this re-preparation (about **8.16 CPU/wall seconds**, peak RSS about **54.5 MiB**).

Manual CI YAML was parsed successfully and the new M3 step was verified to use only locally synthesized fixtures. Independently reran repository-wide Ruff/format checks: **54 lint findings across 12 unchanged legacy Python files**, and **13 legacy files would be reformatted**. The review confirmed no lint findings in newly changed M3 files. These existing broad-scope failures are **not** remedied by this targeted M3 PR; all new M3-scoped checks pass.

**Preservation nuance:** in an earlier independent review, `scripts/fetch_m5.py --verify-only` refreshed ignored `data/raw/m5/manifest.json` with a new `checked_utc`, altering its local hash even though the 5 source CSV checksums still match. The Codex M3 report was also intentionally appended. A prior 134-file snapshot therefore currently has 132 exact matches plus those two explained metadata/report differences. This review did **not** claim 134 unchanged files or overwrite the raw CSVs.

## Open scientific approval gates (before M4 or final holdout)

1. Freeze phase boundaries, admissible training/development information, and evaluation origins/horizon without looking at final outcomes.
2. Choose and document cohort eligibility, shared study-level information, survivor-bias caveats, and whether pooled/pretrained methods belong to separate comparator tracks.
3. Define operational assumptions for inventory initial stock/pipeline, costs, lead-time/horizon sensitivity, and observed-sales replay under demand censoring. Report results only as **simulated** cost scenarios unless a proper real-world estimand is established.
4. Specify covariate availability/release evidence, calibration allocations within each n, statistical dependence/power and comparison margins, matched compute budget, and robust baseline roster.
5. Review M5 usage/redistribution terms; original item-level Favorita 2017 remains gated on Kaggle authorization and cannot be substituted.

**PR handoff:** code is reviewable at an engineering level; scientific protocol explicitly remains unapproved. The original dirty Codex branch is deliberately **not switched, reset, cleaned, committed, pushed or merged** in this step. GitHub main must remain unchanged until human PR review. Reconcile local branches only after deciding whether to merge.
