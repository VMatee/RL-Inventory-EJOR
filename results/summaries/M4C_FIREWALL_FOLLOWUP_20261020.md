# PR #11 critical follow-up — 2026-10-20

Review branch: `feat/m4c-protocol-access-firewall`,
[PR #11](https://github.com/VMatee/RL-Inventory-EJOR/pull/11), against main
`bea7dcb5ad82c457e81f75b6965179d725acae45`. Entry local and remote head both
`4d9a777cd8f8e07b39e33df2bd120676b5c593ec`; checkout was clean. This report and
its implementation are in the follow-up commit shown by PR history. No merge.

## Assessment

Both reported counterexamples were real at the entry commit. Passing 201 tests
did not cover direct source calls or establish persisted selection evidence.

1. Temporary miniature CSVs allowed both `read_history` and `read_evaluation` to
   return two synthetic observations with no freeze, release or locks and a
   nonexistent analysis specification. This was an actual supported-adapter
   authorization defect, despite the earlier trusted-preparer assumption.
2. Structurally valid placeholder selection hashes allowed calibration history
   preparation without actual referenced files or validation receipts. Existing
   checks established a trusted attestation chain, not persisted selection work.

The supported adapters now reject the first counterexample. Protected stage
authorization rejects the second and requires verifiable persisted metadata
evidence. This does **not** prove that model selection was scientifically valid
or even executed: that stronger guarantee needs actual execution/audit artifacts
in the future M4d runner. No final scientific freeze or real release exists.

## Implemented corrections and code references

- `src/inventory_ejor/data/staged_source.py:65`: every direct adapter read now
  requires a complete authorization context, exact cohort/task/window/capability,
  actual evidence where applicable, clean frozen code, actual specification and
  source identity. No persistent armed-reader state. Canonical raw leaves are
  checked before hashing. `:143` persists metadata before returning observations;
  `:154` and `:165` are distinct history/scorer methods.
- `src/inventory_ejor/data/releases.py:170`: `check_task_attestation` explicitly
  validates metadata only. `:258` `authorize_task` adds mandatory persisted
  selection/calibration evidence for calibration/final access. Unapproved
  releases fail before evidence reads. Structural `check_selection`/calibration
  APIs remain available and are documented as non-authorizing checks.
- `src/inventory_ejor/data/evidence.py:42`: dedicated canonical content-addressed
  JSON store with exclusive writes, identical-record reuse, 1 MiB size bound,
  same-byte SHA256/parse checks, strict types and no embedded-path traversal.
  Protected artifact trees and symlink paths are refused. `:102` persists a
  receipt and its actual approved release without observation values.
- `evidence.py:159`: prerequisites cover every selected series, declared origin,
  history budget and one separate outcome path. Duplicate tasks, wrong phase,
  wrong window, source/cohort/lock swaps and missing coverage are rejected.
  `:224` verifies actual procedure specifications and a linked selection result;
  `:288` additionally verifies calibration result/access evidence for final use.
- `src/inventory_ejor/data/staged.py:144` and `:225`: learner/scorer preparers
  supply per-read context and return the persisted access-receipt digest.
  Optional development/validation in-memory fixtures retain compatibility;
  production adapters always require a store. Custom callbacks now accept an
  `authorization` keyword. Historical M3 APIs and schemas are unchanged.
- `src/inventory_ejor/data/protocol.py:177`: reject metadata plans whose required
  evidence inventory exceeds 10,000 receipts, before source access. `:290`:
  legacy workers refuse explicit protected phases before model imports. Existing
  real-M5 origin guards remain active even when the phase field is omitted.
- `src/inventory_ejor/baselines/planning.py:267` remains unchanged: staged
  manifests are refused before the legacy planner hashes evaluator artifacts.

Evidence format and trust levels are documented in `docs/M4C_ACCESS_FIREWALL.md`.
All positive authorizations and numerical source reads in new tests are synthetic.
No production bypass switch or approved real record was introduced.

## Test and verification evidence

Commands, executed from the Git root with the existing isolated environment:

```bash
PYTHONDONTWRITEBYTECODE=1 ../code/.venv/bin/python -B \
  -m unittest discover -s tests -v
../code/.venv/bin/ruff check --select E,F,I,B,UP \
  src/inventory_ejor/data/{protocol,evidence,releases,staged,staged_source,preparation}.py \
  src/inventory_ejor/baselines/{planning,worker}.py \
  scripts/{plan_m4c,prepare_m3}.py tests/test_m4c*.py
../code/.venv/bin/ruff format --check \
  src/inventory_ejor/data/{protocol,evidence,releases,staged,staged_source,preparation}.py \
  src/inventory_ejor/baselines/{planning,worker}.py \
  scripts/{plan_m4c,prepare_m3}.py tests/test_m4c*.py
../code/.venv/bin/python -B scripts/check_project.py
../code/.venv/bin/python -B scripts/plan_m4c.py \
  --config experiments/configs/m4c_protocol_candidate.json
../code/.venv/bin/python -B scripts/analyze_m4_results.py \
  --session results/runs/m4-approved-yc4xtrp1
git diff --check
```

- **218/218 repository tests passed in 15.466 s**; 17 new follow-up tests in
  `tests/test_m4c_access_evidence.py`. The existing 201 tests remain compatible.
- Strict scoped lint and formatting pass across all **14 PR Python files**.
  Project check passes: 16 bibliography entries and 16 cited keys. No new
  literature, manuscript claims or TeX verification is asserted.
- The metadata command still emits 28 tasks, `value_access_authorized=false`
  and an unapproved freeze template. No new production observation access.
- Existing randomized half-open boundary tests, numerical/audit corruption tests,
  zero/intermittent demand and complete-byte future-cell noninterference remain
  in the full suite. No model fitting, GPU test or real baseline execution.
- Expected missing-Kaggle refusal/synthetic ZIP output belongs to existing unit
  tests; it does not represent dataset acquisition.

New negative cases and their regression locations:

| Attack or control | Test line in `tests/test_m4c_access_evidence.py` |
|---|---|
| Direct history/scorer calls without records, missing spec | 50 |
| Valid direct reads persist separate exact receipts; no later armed read | 68 |
| Unauthorized windows, richer windows, swapped capabilities/private method | 100 |
| Unapproved grant opens neither evidence nor raw source; actual spec required | 137 |
| Configuration changed after approval | 160 |
| Persistence failure propagates instead of returning values | 169 |
| Development adapter requires receipt persistence too | 182 |
| Legacy planner rejects staged manifest before any artifact hash | 212 |
| Legacy worker refuses all three protected phases before imports/IO | 242 |
| Placeholder selection hashes, with no store or an empty reference | 273 |
| Missing validation outcomes, history budget or series | 293 |
| Duplicate receipts, wrong phase, rehashed wrong window | 315 |
| Missing/mutated/symlinked artifact, wrong evidence kind | 340 |
| Selection result lacking actual validation receipt links | 364 |
| Missing calibration result, incomplete coverage, wrong selection | 381 |
| Symlinked store and attempts to overwrite a mutated digest | 400 |
| Metadata plan cannot fit its required evidence inventory | 414 |

First integration attempt exposed two fixture adjustments: one old synthetic
scorer call omitted the newly required evidence store; a source-alias regression
was stopped earlier by the new manifest guard. Added the store to the positive
fixture and bound that synthetic alias fixture's freeze to its altered manifest
so the intended masquerading check is still exercised. Assertions were not
weakened. Initial strict lint/format issues were corrected. Full suite then passed.

Parallel read-only engineering checks independently attacked missing/tampered/
symlinked files, placeholder locks and rehashed incomplete coverage using `/tmp`
fixtures; all failed before source callbacks. This is an internal adversarial
pass, not external scientific peer review. A second pass found an evidence-size
mismatch for huge metadata plans; the explicit 10,000-receipt compiler bound and
boundary regression resolve it. No additional concrete gate bypass was found.

## Preservation and original development evidence

Reused the original read-only SHA256/size inventory before editing and checked
it again after testing: **1,611/1,611 unchanged**, zero new or removed protected
files. Covers raw/processed data, all existing run artifacts, approvals/STARTED/
plans/private traces and selected original launch records. Full-source byte
hashing is provenance work; no new M5 observation values were interpreted.
Snapshot SHA256:
`cee767a3db64d64bdaee5f0f3133188efebecee2064c286337cec461c146ad88`.

The entire newly generated original-audit JSON is **equal** to the preceding
M4c audit JSON. It verifies 192 jobs and 5,376 independent replay periods, with
costs 10,156 / 10,186 / 9,904 / 9,497. The 407/9,904 descriptive reduction,
5.91803278689x transition ratio, 336/407 first-arrival savings and terminal
stocks 119/147 remain development diagnostics with their earlier limitations.
No rerun or overwrite of the original campaign occurred.

Private logs, entry counterexamples, metadata output, audit JSON, integrity
inventory and machine report are retained outside Git at workspace-relative
`code/backups/m4c-hardening-20261020-9_rg4dyo/` (owner-only permissions), with
working copies in `/tmp/m4c-hardening-9_rg4dyo/`. No private item-level records,
credentials or datasets were pushed.

## Remaining findings and scientific assessment

**BLOCKING — supported M4c API:** no remaining demonstrated bypass in the tested
trusted-caller contract. This is scoped engineering evidence, not automatic PR
approval. New real experiments remain blocked pending scientific release and the
M4d executor gates below; they are not enabled by this PR.

**MAJOR — future execution gate, not a newly discovered numerical code defect:**
persisted records establish actual specification/result bytes and declared access
coverage. Nonempty result dictionaries do not demonstrate executed validation or
correct selection/calibration. Local owners can fabricate records; unsigned owner
strings do not authenticate people or wall clock order. M4d must verify complete
actual validation/calibration outputs, numerical audits, model dependencies and
method/seed task coverage before stage transitions. The strict learner/scorer
contract and mandatory attacks are at `experiments/protocol/M4D_READINESS.md:132`.
An unimplemented future executor cannot be certified safe in advance. Current
legacy rejection tests establish the existing integration boundary only.

**MAJOR — open scientific design:** retain the paired equal-item-store mean cost
benefit at fixed primary n as a candidate finite-benchmark score. Population claims
need an explicit target and sampling/dependence assumptions. A fixed-seed hash
subset of the ex-post catalog is reproducible, not automatically a probability
sample or historically available assortment. A/B have two final calendar contexts,
C three; none establishes adequate temporal replication or power. More SKUs,
budgets or optimizer seeds cannot supply missing calendar replication. No valid
confirmatory interval, p-value or non-inferiority claim is established. Primary
history/baseline/weights, inference, independent pilot inputs and an externally
justified margin remain PENDING OWNER APPROVAL. See scientific protocol sections
3, 5, 7–9. No outcome-free evidence ranks A/B/C by statistical power.

**MINOR — operational limits:** raw hashes and evidence are rechecked per read;
this favors correctness but scales poorly. Identical receipts deduplicate, so the
store is not a chronological attempt/retry journal. Partial reads can expose
values before failure and must enter the trusted exposure inventory. No OS-level
security or hostile local-writer protection is claimed. These limitations must
not be described as proven anti-tamper chronology or fresh holdout reuse.

Prioritize the future work: (1) actual execution/artifact closure and scorer
isolation with synthetic integration attacks; (2) owner-approved estimand,
chronology/cohort/exposure inventory and dependence/power strategy; (3) separately
authorized six-method development matrix and common warm/longer-horizon controls;
(4) only then investigate the proposed method and publication evidence. Reuse a
fitted demand model across a controller pair, but retune continuation for the
declared warm state/objective. Nothing here establishes steady-state GP rollout
superiority, calibrated policy safety or EJOR novelty.

## Changed files in this follow-up

Implementation: `src/inventory_ejor/data/evidence.py`, `protocol.py`, `releases.py`,
`staged.py`, `staged_source.py`.

Tests: `tests/test_m4c_access_evidence.py`, `test_m4c_firewall.py`,
`test_m4c_source_integration.py`.

Documentation: `docs/M4C_ACCESS_FIREWALL.md`, `STATUS.md`, `TASKS.md`, `CLAIMS.md`,
`DECISION_LOG.md`, `SESSION_LOG.md`; `experiments/protocol/M4C_SCIENTIFIC_PROTOCOL.md`,
`M4D_READINESS.md`; historical verification addendum and this follow-up report.
