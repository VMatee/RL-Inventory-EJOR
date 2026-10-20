# M4c staged preparation and scientific access records

Status: implemented for metadata planning and gated preparation; scientific
freeze and all new M5 releases are **PENDING OWNER APPROVAL**. There is no
approved real release in this PR. No M4d runner or final scorer is enabled.

## Entry points and separation

`scripts/plan_m4c.py --config experiments/configs/m4c_protocol_candidate.json`
prints a metadata-only plan and an unapproved freeze template. It imports no
reader or model, writes nothing, and rejects protected data/result paths and
symlinked configurations. The complete protocol is validated before the plan
is emitted; a valid plan is not permission to prepare observations.

`data.protocol.plan_protocol` combines `SplitPlan` with the nonadaptive embargo
for every phase. It derives the largest history from the entire budget grid,
checks all origins, source extents, calendar dates, unique phase/budget lists,
and full history-plus-outcome runways. Known M5 `[1,253)` remains development
even if a new proposal shrinks history budgets. It cannot become a final test.

`data.staged.prepare_learner` is the trusted preparation API. It checks the
complete records and task identity before a source callback, reads one exact
own-series n-history, constructs training-only normalization and deterministic
civil-calendar features, and returns `(LearnerView, trusted_receipt)`.
`learner_payload(view)` produces the existing M3 learner schema. There is no
evaluator path, source object, release hash or full-source fingerprint in it.
The normal learner receives only this value or its pinned artifact.

`data.staged.prepare_evaluation` is the separate trusted scorer API. It needs
an `evaluation_outcomes` release, not the learner release, and returns
`(EvaluationTargets, trusted_receipt)`. Both APIs validate the entire protocol,
including other origins, rather than trusting the requested origin alone.
An evaluator cannot be serialized as a learner or validated as fitting data.
The actual returned view's normalization and complete feature values are checked
by `validate_task_ledger`; declarations cannot hide a late feature or bad fit.

`M5HistorySource` and `M5EvaluatorSource` are separate bounded production
adapters. Constructors read no files. Before observation access, they check the
canonical source-manifest fingerprint, actual clean live Git commit, and SHA256
of the actual analysis-specification file against the scientific freeze.
Recognized M5 sources cannot be renamed as fixtures to escape exposure rules.
All five raw source paths must be canonical; source checksums are verified before
and after each read. Full-source byte hashing is trusted provenance work, not
parsing withheld sales into predictors. Only the requested window is interpreted
as observations. These adapters were exercised only on temporary synthetic CSVs.

## Record chain

Records use strict keys and canonical JSON fingerprints. A template is always
false/nonapproving; there is no CLI that approves a record or accesses outcomes.
All positive authorizations in tests are explicit **synthetic-only fixtures**.

| Record | Bound identities and prerequisite |
|---|---|
| `scientific_freeze` | Exact protocol hash, analysis-spec raw-file SHA256, canonical source-manifest fingerprint, full clean reviewed Git commit, named owner, decision record, `approved=true` |
| `selection_lock` | Protocol/freeze hashes, frozen candidate and baseline procedures, search specification, calibration rule, complete selection-stage access-log hash, `selection_frozen=true` |
| `calibration_lock` | Exact selection lock, protocol/freeze hashes, calibration result and access-log hashes, `calibration_frozen=true` |
| `data_release` | Named owner/decision, protocol/freeze, one phase/origin, exact n for learner capability, fixed-cohort hash, and required selection/calibration locks |

Development/validation access requires its own approved task release. Calibration
history **and** outcomes require selection to be frozen first. Final history
**and** outcomes require the same frozen selection and calibration. The cohort
release covers its fixed selected IDs, with no replacements, and one release
may be reused for paired methods/budgets only within its explicitly bound scope;
a learner n-release cannot be transplanted to another budget.

The selection lock binds a **learning/decision procedure**: code, hyperparameters,
normalization recipe, features, seed mapping, optimizer rules and calibration
procedure. It does not bind unseen final fitted GP weights. Fitting that frozen
recipe on a newly released n-history is permitted; choosing a different recipe
using calibration/final outcomes is not. The field named
`development_access_log_sha256` must inventory **all selection-stage access,
including validation**, and its study-wide distinct-cell union. It is not proof
that the whole research effort used only n observations.

Opaque lock hashes are trusted evidence references, not proof that model files
exist or that a scientific calculation was performed correctly. The M4d runner
must pin and verify actual procedure/checkpoint and calibration artifacts, persist
these returned receipts, and bind model/source/config/runtime before scoring.
The M4c API does not automatically persist a chronological event journal or mark
a release as consumed. Repeated scoring cannot be treated as a fresh holdout.

## Cohort and strict information scope

The candidate pins the sorted metadata sampling frame by SHA256. Its 30,490 IDs
were reconstructed from the **existing** M3 `cohort.json` metadata; no new sales
or reserved outcomes were opened. Only that aggregate hash is committed. Count
32 and seed 0 are reviewable candidate choices, not scientifically approved
defaults. Hash ranking performs no activity screen. This changes the prospective
cohort from the historically screened 12-series pilot and needs owner approval.

Every fitting-ledger access category is constrained to the exact n-history;
all reserved outcome windows are forbidden across all series/categories.
Future observations, earlier final outcomes, calibration/validation outcomes,
undeclared features, cross-series pooling and pretrained artifacts are refused.
Merely claiming `lineage_complete=true` cannot enable pretraining. The implemented
track is strict own-history input **plus separately disclosed shared development**.
Richer data or online adaptation needs a distinct implementation and approval.

## Legacy compatibility and bypass closure

The old M3 demo, M4 planner and worker retain historical behavior for synthetic
fixtures and already exposed real-M5 d_225. A legacy config cannot authorize a
new real M5 origin by calling it `development_demo`. Recognition uses logical
version, canonical raw location and/or pinned historical source identity.
The planner checks actual split and ledger metadata **before** hashing artifacts,
and checks configuration/manifest leaves before opening symlinks. Worker guards
run before numerical imports. Existing M3 schemas and M4b auditing are unchanged.

The legacy planner intentionally cannot consume staged protected bundles. Future
M4d integration must use separate learner/scorer artifacts and explicit releases;
do not make it accept a new status string and then hash every evaluator artifact.

## Operational and security limits

This is an accidental-leakage and reproducibility boundary in trusted code.
Python and the shared filesystem are not an OS sandbox. A privileged caller can
bypass APIs and open a raw CSV; unsigned owner records are not cryptographic
identity authentication. A production service needing hostile-code isolation
requires separate principals/filesystem permissions and an append-only audit log.
This PR does not claim those properties.

The safe supported route is metadata planning, independently reviewed owner
records, trusted staged preparation, persisted receipts, and a separately
reviewed executor. Owner freeze, release and execution scope remain separate
decisions. Date separation and record checks do not establish calibration
coverage, inference validity, real retailer savings or novelty.
