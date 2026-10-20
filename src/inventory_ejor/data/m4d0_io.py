"""M4d-0 pure metadata performance budget: no data-file opening or hashing.

This does NOT optimize M5 preparation; it prevents an unreviewed high-I/O
design from silently being treated as ready. Reviewed batching / immutable
snapshot reuse is a separate M4d-1 gate with its own correctness tests.
"""

from __future__ import annotations

from inventory_ejor.data.protocol import plan_protocol, require
from inventory_ejor.data.provenance import canonical

EXPECTED_FILES = frozenset(
    {
        "calendar.csv",
        "sales_train_validation.csv",
        "sales_train_evaluation.csv",
        "sell_prices.csv",
        "sample_submission.csv",
    }
)


def project_naive_preparation_io(config, input_file_bytes):
    """Worst-case logical reads under current per-series M4c source adapter.

    Every source call hashes all five immutable files twice, scans the long
    training/evaluation sales CSV once and reads calendar once. Assume one
    evaluation call per series/origin (not per history budget). Results are
    *logical processed bytes*, not disk traffic, elapsed time, or a proof of
    execution. Real future runs require an explicit bound and authorization.
    """
    plan = plan_protocol(config)
    require(
        type(input_file_bytes) is dict and set(input_file_bytes) == EXPECTED_FILES,
        "Expected the five metadata file sizes, no observation data",
    )
    for name, size in input_file_bytes.items():
        require(
            type(size) is int and 0 < size <= 2**46,
            f"Invalid metadata file size: {name}",
        )
    cohort = config["cohort"]["count"]
    tasks = plan["tasks"]
    origins = {(x["phase"], x["origin"]) for x in tasks}
    learner_reads = cohort * len(tasks)
    scorer_reads = cohort * len(origins)
    total_reads = learner_reads + scorer_reads
    source_bytes = sum(input_file_bytes.values())
    each = (
        source_bytes * 2
        + input_file_bytes["sales_train_evaluation.csv"]
        + input_file_bytes["calendar.csv"]
    )
    return {
        "schema_version": 1,
        "kind": "m4d0_metadata_io_projection",
        "cohort": cohort,
        "histories": learner_reads,
        "scorer_windows": scorer_reads,
        "reader_calls": total_reads,
        "bytes_per_reader_call": each,
        "logical_processed_bytes": total_reads * each,
        "source_hash_bytes": total_reads * source_bytes * 2,
        "sales_csv_scan_bytes": (
            total_reads * input_file_bytes["sales_train_evaluation.csv"]
        ),
        "calendar_scan_bytes": total_reads * input_file_bytes["calendar.csv"],
        "assumptions": [
            "One scorer read per item and unique phase/origin",
            "All five source files verified twice per read",
            "No physical disk bandwidth or caching assertion",
            "No separate method/seed repeated preparation included",
            "Metadata-only: no dataset values or reserved outcomes read",
        ],
    }


def require_preparation_budget(
    projection, *, maximum_logical_bytes, config, input_file_bytes
):
    """Fail closed instead of launching an unapproved terabyte-scale sweep."""
    require(
        type(projection) is dict
        and canonical(projection)
        == canonical(project_naive_preparation_io(config, input_file_bytes)),
        "Valid metadata-only projection required",
    )
    require(
        type(maximum_logical_bytes) is int and 0 < maximum_logical_bytes <= 2**55,
        "Explicit positive preparation I/O allowance required",
    )
    require(
        type(projection.get("logical_processed_bytes")) is int
        and 0 <= projection["logical_processed_bytes"] <= maximum_logical_bytes,
        "Estimated preparation exceeds authorized I/O allowance; "
        "batch/snapshot optimization requires independent review",
    )
    return projection
