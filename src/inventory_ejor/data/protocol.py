"""Pure metadata planning. Constructing a plan grants NO observation access.

The old SplitPlan's calendar role order is retained; logical access order is
development, validation/selection, calibration, final. No reader imports here.
"""

from __future__ import annotations

import copy
import re
from datetime import date, timedelta
from pathlib import Path

from .contracts import ROLES, Phase, SplitPlan, Window, exact_keys, integer
from .embargo import validate_nonadaptive_origin_embargo
from .provenance import fingerprint

ACCESS_ORDER = ("development", "validation", "calibration", "final_test")
MAX_EVIDENCE_RECEIPTS = 10_000
M5_VERSION = "m5-accuracy-zenodo-10203108-v1"
M5_EVALUATION_SHA256 = (
    "4b4a47c44c38380d2a9168216fea8c9ff2f31b1ddb772f8a0995952a038b8aa0"
)
M5_SOURCE_FINGERPRINT = (
    "m5-sha256:975e2a16a90d3ec7ba7cee145dbebd62a119bcf2dcbcf4b3885d04263de8dbc5"
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256_id(value, label):
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
        f"{label} requires a lowercase SHA256 identity",
    )
    return value


def metadata_config_path(path, root):
    """Validate a bounded metadata leaf without opening protected values."""
    path, root = Path(path).absolute(), Path(root).resolve()
    require(
        path == path.resolve() and path.is_file(),
        "Symlink/noncanonical or missing metadata configuration",
    )
    require(
        not any(
            (root / prefix) in path.parents
            for prefix in ("data/raw", "data/processed", "results/runs")
        ),
        "Protected data/results cannot be a metadata configuration",
    )
    require(
        path.suffix == ".json" and path.stat().st_size <= 65536,
        "Metadata configuration must be JSON (<=64 KiB)",
    )
    return path


def plan_protocol(config):
    """Validate complete phase geometry, returning a JSON metadata-only plan."""
    exact_keys(
        config,
        (
            "schema_version",
            "status",
            "dataset_version",
            "first_date",
            "source_window",
            "horizon",
            "budgets",
            "phases",
            "cohort",
            "features",
            "information_track",
        ),
        "M4c protocol",
    )
    require(
        type(config["schema_version"]) is int and config["schema_version"] == 1,
        "Unsupported protocol version",
    )
    require(
        config["status"] == "proposal_pending_owner_approval",
        "Protocol configuration is a proposal; approval is a separate record",
    )
    require(
        isinstance(config["dataset_version"], str)
        and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:/-]{0,127}", config["dataset_version"]),
        "Predeclared logical dataset version required",
    )
    require(
        date.fromisoformat(config["first_date"]).isoformat() == config["first_date"],
        "Canonical first_date required",
    )
    exact_keys(config["source_window"], ("start", "stop"), "source window")
    source = Window(**config["source_window"])
    require(source.start == 1 and source.stop <= 100_001, "Unsupported source extent")
    # Reject impossible civil-date extents before any future reader can run.
    try:
        date.fromisoformat(config["first_date"]) + timedelta(days=source.stop - 2)
    except OverflowError as exc:
        raise ValueError("Source metadata exceeds the civil-date extent") from exc
    integer(config["horizon"], "horizon")
    require(config["horizon"] <= 366, "Horizon exceeds bounded planning scope")
    budgets = config["budgets"]
    require(type(budgets) is list and 0 < len(budgets) <= 16, "Invalid budget grid")
    for n in budgets:
        integer(n, "budget")
        require(n <= 3660, "History exceeds bounded planning scope")
    require(budgets == sorted(set(budgets)), "Budgets must be increasing and unique")
    require(
        type(config["phases"]) is list and len(config["phases"]) == 4,
        "Declare exactly four chronological phases",
    )
    phases, origins_by_role = [], {}
    for entry in config["phases"]:
        exact_keys(entry, ("role", "start", "stop", "origins"), "phase")
        require(
            type(entry["origins"]) is list and 0 < len(entry["origins"]) <= 32,
            "Each phase requires a bounded nonempty origin list",
        )
        for origin in entry["origins"]:
            integer(origin, "origin")
        window = Window(entry["start"], entry["stop"])
        require(source.contains(window), "Phase extends beyond source metadata")
        phases.append(Phase(entry["role"], window))
        require(entry["role"] not in origins_by_role, "Duplicate phase")
        origins_by_role[entry["role"]] = tuple(entry["origins"])
    require(
        tuple(p.role for p in phases) == ROLES, "Declare all phases in calendar order"
    )
    split = SplitPlan(tuple(phases), config["horizon"], tuple(budgets))
    if config["dataset_version"] == M5_VERSION:
        require(
            config["first_date"] == "2011-01-29"
            and config["source_window"] == {"start": 1, "stop": 1942},
            "M5 logical version must retain its verified date/extent metadata",
        )
        require(
            phases[0].window.contains(Window(1, 253)),
            "Known exposed M5 history/outcomes [1,253) must remain development",
        )
    tasks = []
    for phase in phases:
        origins = origins_by_role[phase.role]
        split.validate_origins(phase.role, origins)
        # Conservative nonadaptive contexts in every phase, not just final.
        validate_nonadaptive_origin_embargo(
            origins, largest_history=max(budgets), horizon=config["horizon"]
        )
        for origin in origins:
            for budget in budgets:
                history, target = split.windows(phase.role, origin, budget)
                tasks.append(
                    {
                        "phase": phase.role,
                        "origin": origin,
                        "budget": budget,
                        "history": {"start": history.start, "stop": history.stop},
                        "evaluation": {"start": target.start, "stop": target.stop},
                    }
                )
    cohort = config["cohort"]
    exact_keys(cohort, ("rule", "count", "seed", "catalog_sha256"), "cohort")
    sha256_id(cohort["catalog_sha256"], "metadata catalog")
    require(
        cohort["rule"] == "metadata_hash_without_sales",
        "Sales-based screening is unsupported in the staged strict-n path",
    )
    integer(cohort["count"], "cohort count")
    integer(cohort["seed"], "cohort seed", 0)
    require(cohort["count"] <= 1024, "Cohort exceeds planning bound")
    # A canonical list of <=10,000 SHA256 IDs fits the 1 MiB evidence bound.
    # Do not compile a plan whose prerequisite access inventory cannot be saved.
    for roles in (("development", "validation"), ("calibration",)):
        receipts = (
            cohort["count"]
            * (len(budgets) + 1)
            * sum(len(origins_by_role[role]) for role in roles)
        )
        require(
            receipts <= MAX_EVIDENCE_RECEIPTS,
            "Plan exceeds persisted evidence capacity",
        )
    require(
        type(config["features"]) is list
        and len(set(config["features"])) == len(config["features"])
        and all(x in ("month", "weekday") for x in config["features"]),
        "Only deterministic civil-calendar features are supported",
    )
    require(
        config["information_track"] == "per_series_with_shared_development",
        "Pooling/pretraining/online adaptation require a separate implementation",
    )
    return {
        "schema_version": 1,
        "protocol": copy.deepcopy(config),
        "protocol_sha256": fingerprint(config),
        "tasks": tasks,
        "access_order": list(ACCESS_ORDER),
        "value_access_authorized": False,
    }


def task_for(config, phase, origin, budget):
    plan = plan_protocol(config)
    integer(origin, "origin")
    integer(budget, "budget")
    found = [
        t
        for t in plan["tasks"]
        if (t["phase"], t["origin"], t["budget"]) == (phase, origin, budget)
    ]
    require(len(found) == 1, "Task is not in the complete declared protocol")
    return found[0]


def guard_legacy_development(config, *, real_source=False):
    """Prevent relabeling reserved M5 windows as a legacy development demo.

    Synthetic legacy fixtures retain their historical flexible geometry. Real
    M5 has only the already exposed d_225 window grandfathered into this path.
    A new real origin must use an explicitly released staged preparation.
    """
    if real_source or config.get("dataset_version") == M5_VERSION:
        require(
            config.get("origins") == [225]
            and config.get("horizon") == 28
            and config.get("development_window") == {"start": 1, "stop": 253},
            "Legacy M5 access is limited to historical d_225; "
            "use the staged release firewall",
        )


def recognized_m5_source(raw_dir, manifest):
    """Metadata/path recognition; never opens sales to identify a source."""
    require(
        isinstance(manifest, dict)
        and isinstance(manifest.get("files"), list)
        and all(isinstance(e, dict) for e in manifest["files"]),
        "Invalid source manifest metadata",
    )
    official = Path(__file__).resolve().parents[3] / "data/raw/m5"
    return Path(raw_dir).resolve() == official or any(
        e.get("filename") == "sales_train_evaluation.csv"
        and e.get("sha256") == M5_EVALUATION_SHA256
        for e in manifest.get("files", [])
    )


def guard_legacy_bundle(manifest):
    """Check actual task metadata BEFORE an old planner hashes any artifacts."""
    real = (
        manifest.get("learner_dataset_version") == M5_VERSION
        or manifest.get("inputs", {})
        .get("sales_train_evaluation.csv", {})
        .get("sha256")
        == M5_EVALUATION_SHA256
    )
    config = manifest["config"]
    guard_legacy_development(config, real_source=real)
    if real or config.get("dataset_version") == M5_VERSION:
        for split in manifest.get("splits", []):
            require(
                split["evaluation"] == {"start": 225, "stop": 253},
                "Legacy M5 split attempts protected outcome access",
            )
            require(
                Window(1, 225).contains(Window(**split["history"])),
                "Legacy M5 split attempts protected history access",
            )
        for entry in manifest.get("information_budgets", []):
            record = entry["ledger"]
            require(
                type(record["origin"]) is int and record["origin"] == 225,
                "Legacy M5 ledger attempts protected origin access",
            )
            for accesses in record["access"].values():
                for a in accesses:
                    require(
                        Window(1, 225).contains(Window(a["start"], a["stop"])),
                        "Legacy M5 ledger attempts protected observation access",
                    )


def guard_legacy_job(job, plan):
    require(
        job.get("phase", "development") == "development",
        "Legacy workers cannot execute staged protected phases",
    )
    guard_legacy_development(
        {
            "dataset_version": job.get("dataset_version"),
            "origins": [job.get("origin")],
            "horizon": job.get("horizon"),
            "development_window": {"start": 1, "stop": 253},
        },
        real_source=plan.get("data_source_fingerprint") == M5_SOURCE_FINGERPRINT,
    )
