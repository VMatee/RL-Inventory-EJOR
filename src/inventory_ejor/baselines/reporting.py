"""Audit completed private run outputs and create descriptive tables, not claims."""

from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from pathlib import Path

from .planning import encode, inside, read_json, sha_file


def summarize_session(root, session, write=False):
    root, session = Path(root).resolve(), Path(session).resolve()
    if root / "results/runs" not in session.parents:
        raise ValueError("Summary input must be a local results session")
    summary = read_json(session / "session_summary.json")
    plan = read_json(session / "plan.json")
    requested = {j["id"]: j for j in plan["jobs"]}
    if len(requested) != len(plan["jobs"]):
        raise ValueError("Duplicate plan identity")
    entries = summary["entries"]
    if (
        summary["status"] != "completed"
        or len(entries) != len(requested)
        or {e["job"] for e in entries} != set(requested)
        or any(e["exit_code"] != 0 for e in entries)
    ):
        raise ValueError("Incomplete/failed campaign: refuse misleading averages")
    rows = []
    for entry in entries:
        job = requested[entry["job"]]
        directory = inside(root, entry["output"], "results/runs")
        for name, key in (
            ("result.json", "result_sha256"),
            ("private_sales_replay.json", "trace_sha256"),
        ):
            if sha_file(directory / name) != entry[key]:
                raise ValueError("Saved result or trace changed since completion")
        result = read_json(directory / "result.json")
        trace = read_json(directory / "private_sales_replay.json")
        if result["source_commit"] != plan["git"]["commit"]:
            raise ValueError("Result source commit does not match plan")
        if len(trace) != job["horizon"]:
            raise ValueError("Trace length does not match evaluation horizon")
        trace_cost = math.fsum(t["cost"] for t in trace)
        if not math.isfinite(trace_cost) or not math.isclose(
            trace_cost, result["total_cost"], rel_tol=1e-12, abs_tol=1e-9
        ):
            raise ValueError("Total cost does not match retained trace")
        requests = sum(t["observed_sales_as_requests"] for t in trace)
        fulfilled = sum(t["fulfilled"] for t in trace)
        rows.append(
            {
                "job": job["id"],
                "method": job["method"],
                "series": job["series"],
                "origin": job["origin"],
                "budget": job["budget"],
                "seed": job["seed"],
                "total_cost": result["total_cost"],
                "fill_rate": fulfilled / requests if requests else None,
                "total_requests": requests,
                "fulfilled_requests": fulfilled,
                "runtime_seconds": result["total_seconds"],
                "selected_base_stock": result["selected_base_stock"],
                "upper_grid_boundary": result[
                    "base_stock_grid_upper_boundary_selected"
                ],
                "order_cap_periods": result["order_cap_binding_periods"],
                "output": entry["output"],
            }
        )
    rows.sort(key=lambda r: (r["method"], r["budget"], r["series"], r["seed"]))
    groups = defaultdict(list)
    for row in rows:
        groups[row["method"], row["budget"]].append(row)
    aggregates = []
    for (method, budget), group in sorted(groups.items()):
        requests = sum(r["total_requests"] for r in group)
        aggregates.append(
            {
                "method": method,
                "budget": budget,
                "jobs": len(group),
                "mean_total_cost": math.fsum(r["total_cost"] for r in group)
                / len(group),
                "weighted_fill_rate": (
                    sum(r["fulfilled_requests"] for r in group) / requests
                    if requests
                    else None
                ),
                "mean_runtime_seconds": sum(r["runtime_seconds"] for r in group)
                / len(group),
                "grid_boundary_jobs": sum(r["upper_grid_boundary"] for r in group),
            }
        )
    report = {
        "status": "complete_and_hash_verified",
        "job_count": len(rows),
        "source_commit": plan["git"]["commit"],
        "groups": aggregates,
        "scope": "descriptive development sales-replay simulation only",
        "warning": "No causal savings, novelty, significance or GP superiority claim",
    }
    if write:
        text = io.StringIO()
        writer = csv.DictWriter(text, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        for name, data in (
            ("baseline_results.csv", text.getvalue().encode()),
            ("aggregate_summary.json", encode(report)),
        ):
            with (session / name).open("xb") as stream:
                stream.write(data)
    return report
