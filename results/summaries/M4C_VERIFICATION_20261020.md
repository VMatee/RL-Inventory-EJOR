# M4c engineering verification — 2026-10-20 Asia/Bangkok

Scope: candidate scientific protocol, metadata compiler and staged preparation
firewall. Base main is `bea7dcb5ad82c457e81f75b6965179d725acae45` (merged PR #10).
Branch: `feat/m4c-protocol-access-firewall`. See the PR head for the final commit.
No scientific freeze, positive real release, new demand observation, model fit,
GPU experiment, baseline campaign or final evaluation was performed.

## Initial inspection and technical plan

Verified clean main, matching origin/main and expected GitHub repository before
creating the feature branch. No baseline worker/start/scheduler processes were
active. Read AGENTS, charter/status/tasks/claims/decisions, both historical
protocols, M4b report/review response, and actual contracts/readers/tests.

The old M3 preparer eagerly reads target outcomes; the old M4 planner hashes all
bundle artifacts. Merely adding new phase labels would expose protected values
during preparation/preflight. Also, `development_demo` accepted arbitrary
self-declared real-M5 origins, and SplitPlan alone did not enforce the history
embargo. The implementation therefore preserves old schemas, limits real legacy
access to exposed d_225, and supplies separate metadata/staged preparation paths.

Plan executed: compare chronology alternatives and define research gates; add
central full-plan/release validation; isolate learner/scorer access; close old
entry-point bypasses before reads; exercise synthetic attacks and compatibility;
perform parallel read-only adversarial reviews; verify evidence integrity; prepare
a scoped commit and PR. These were internal engineering reviews, not external
scientific peer review or a publication approval.

## Commands and measured outcomes

All Python commands used `../code/.venv/bin/python -B` from the Git root.

```bash
../code/.venv/bin/python -B -m unittest discover -s tests -q
../code/.venv/bin/ruff check --select E,F,I,B,UP \
  src/inventory_ejor/data/{protocol,releases,staged,staged_source,preparation}.py \
  src/inventory_ejor/baselines/{planning,worker}.py \
  scripts/{plan_m4c,prepare_m3}.py tests/test_m4c*.py
../code/.venv/bin/ruff format --check \
  src/inventory_ejor/data/{protocol,releases,staged,staged_source,preparation}.py \
  src/inventory_ejor/baselines/{planning,worker}.py \
  scripts/{plan_m4c,prepare_m3}.py tests/test_m4c*.py
../code/.venv/bin/python -B scripts/check_project.py
../code/.venv/bin/python -B scripts/plan_m4c.py \
  --config experiments/configs/m4c_protocol_candidate.json
../code/.venv/bin/python -B scripts/analyze_m4_results.py \
  --session results/runs/m4-approved-yc4xtrp1
git diff --check
```

- **201/201 repository tests passed**, final measured runtime **10.170 s**.
  The prior 168 tests remain compatible; 33 new M4c tests passed.
- **250 fixed-seed randomized paired boundary cases** (seed 451) each check
  valid touching contexts and an invalid one-day overlap. All three documented
  A/B/C layouts pass; adding an eighth 252-day block fails.
- Scoped strict Ruff lint passed; all **12 changed Python files** are formatted.
  This is not a claim that every untouched repository file passes Ruff.
- Project structure/citation check passed: 16 entries and 16 resolved keys.
  No manuscript changed, and no TeX build or new bibliography audit is claimed.
- Metadata command generated 28 task contracts, `value_access_authorized=false`,
  and `approved=false` for the freeze template. It wrote no project artifact.
- Test stdout includes the expected missing-Kaggle-credentials refusal and an
  isolated synthetic ZIP receipt. These are negative/acquisition unit tests;
  no Favorita dataset was acquired or authenticated network download attempted.

## Failure cases and corrections

The first new firewall suite passed 18/19: an indirect `EvaluationTargets`
returned as history raised TypeError before the expected ValueError. Added
explicit immutable Observation-tuple checks, preserving fail-closed behavior.
Initial scoped lint found formatting/import/line-length issues; corrected them.

Read-only adversarial passes identified and corrected substantive omissions:

| Challenge | Final enforcement/evidence |
|---|---|
| Relabel d_1914 as legacy `development_demo` | Parser/preparer reject recognized real-M5 access before source verification |
| Allowed config but actual protected split/ledger | Planner validates actual task metadata and identities before artifact hashing |
| Renamed logical dataset plus official historical source | Worker rejects before numerical imports; real staged adapter rejects source aliasing |
| Shrink budgets and promote exposed pilot to final | Known M5 `[1,253)` must remain development |
| Disjoint outcomes but later history overlaps | Complete protocol integrates SplitPlan and maximum-history embargo |
| Insufficient runway or one-day phase crossing | Metadata plan refuses before callbacks |
| Unapproved/stale protocol, release, cohort, n or lock | Exact hash/task/owner record checks before callbacks |
| Calibration before selection or final before calibration | Both history and outcome capabilities require the prerequisite locks |
| Retune candidate/baseline/rule after calibration | Hash chain invalidates the final release |
| Forbidden cells through any fitting access category | Exact-history SourcePolicy plus reserved-outcome restrictions; all PURPOSES tested |
| Unverified pretraining/pooling | Unsupported tracks and lineage booleans fail closed |
| Forged normalization, missing features, late price | Actual view recomputed/compared to full deterministic allowance |
| Evaluator object passed indirectly as learner | Typed separation; cannot normalize/serialize as learner |
| Changed/dirty code or analysis specification | Production adapter refuses before raw hashing/observation callback |
| Symlinked config, manifest, specification or raw leaf | Canonical checks before content opens; read/hash spies verify failure order |
| Protected JSON supplied as metadata config | Metadata/legacy entry points reject before parsing data values |
| Reserved future value mutation | Complete serialized learner remains identical; changed source/release hashes stay in trusted receipts |
| Zero/intermittent demand | Valid zero histories/requests accepted; existing zero-cost M4b tests retained |

Production integration tests use actual M3 miniature CSV fixtures, actual source
checksums and analysis-specification files, and the staged preparation APIs.
Only clean live Git identity is mocked for reproducibility in a dirty test tree.
They separately prepare permitted learner days `[21,22]` and scorer `[23,24]`.
An actual synthetic future CSV-cell intervention first fails its old checksum;
after freshly bound synthetic source/approval records, every learner byte is
unchanged, while the trusted release receipt correctly changes identity.
No model is fitted. New tests have finite loops and bounded source reads; the
production adapter retains cooperative <=100-second raw-read checks.

## Protected evidence

Before modifying source, saved a SHA256/size inventory of **1,611 existing files**
under data/raw, data/processed, results/runs and existing selected local launch
records. Full raw bytes were hashed for provenance, not interpreted as future
sales. The external local snapshot is
`/tmp/rl-inventory-m4c-_zbfxthe/protected_before.json`, SHA256
`cee767a3db64d64bdaee5f0f3133188efebecee2064c286337cec461c146ad88`.
Its private inventory is not committed or uploaded.
The same inventory and aggregate logs are also retained in the private local
directory `code/backups/m4c-entry-20261020-48e7zt57/` at the workspace parent,
with owner-only permissions, so the evidence does not depend on temporary-file
retention.

After tests, all **1,611/1,611** sizes and hashes match: **zero changes, zero new
protected files**. Original approvals, STARTED markers, sealed plans, raw data,
learner/evaluator artifacts and private traces were not overwritten or rerun.
Logs and synthetic fixtures stayed outside protected directories.

The original read-only M4 audit still verifies **192 jobs / 5,376 periods**:
costs **10,156 / 10,186 / 9,904 / 9,497**, GP reduction **4.10945072698%**,
simulation ratio **5.91803278689x**, first-arrival saving **336/407**, and
terminal stock **119/147**. These are unchanged development diagnostics.

The candidate metadata frame hash was reconstructed from existing M3 cohort
IDs (30,490 unique metadata IDs); no new observation values were consulted.
No reserved development, calibration, validation or final outcomes were opened.

## Changed files

Implementation/config:
`src/inventory_ejor/data/protocol.py`, `releases.py`, `staged.py`,
`staged_source.py`, `preparation.py`; `src/inventory_ejor/baselines/planning.py`,
`worker.py`; `scripts/plan_m4c.py`, `scripts/prepare_m3.py`;
`experiments/configs/m4c_protocol_candidate.json`.

Tests: `tests/test_m4c_cli.py`, `tests/test_m4c_firewall.py`,
`tests/test_m4c_source_integration.py`.

Scientific/handoff documentation: `experiments/protocol/M4C_SCIENTIFIC_PROTOCOL.md`,
`experiments/protocol/M4D_READINESS.md`, `docs/M4C_ACCESS_FIREWALL.md`, this report,
`AGENTS.md`, `README.md`, `docs/STATUS.md`, `docs/TASKS.md`, `docs/CLAIMS.md`,
`docs/DECISION_LOG.md`, `docs/SESSION_LOG.md`.

## Open gates

No remaining blocking implementation defect is known in tested preparation paths.
Independent PR review is still required. Owner scientific freeze and all new real
releases remain closed: chronology/cohort, primary n/baseline/weights, operational
cost/state scenarios, compute/seeds, dependence/power assumptions and an external
non-inferiority margin require decisions/evidence. No confirmatory p-values were
computed from the original pilot.

Future M4d execution must integrate these APIs, verify actual frozen procedure/
model artifacts, persist access receipts and obtain separate run authorization.
Unsigned records are not authenticated signatures; the API is not an OS sandbox
or append-only journal. Rehashing all source files per read is conservative and
may need a reviewed immutable-snapshot optimization before a large campaign.
These limits are explicit, not hidden defaults or publication guarantees.
