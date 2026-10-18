"""Streaming local M5 readers. Never concatenate the two overlapping sales CSVs.

CSV parsing necessarily transports whole wide rows; only requested day cells
are interpreted. Hash verification is byte-level provenance, not training access.
"""

from __future__ import annotations

import csv
import hashlib
import math
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .contracts import Feature, Observation, Window, integer

META = ("id", "item_id", "dept_id", "cat_id", "store_id", "state_id")
CALENDAR = (
    "date",
    "wm_yr_wk",
    "weekday",
    "wday",
    "month",
    "year",
    "d",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
    "snap_CA",
    "snap_TX",
    "snap_WI",
)
PRICE = ("store_id", "item_id", "wm_yr_wk", "sell_price")


@dataclass
class ReadLimits:
    max_seconds: int = 100
    max_rows: int = 7_000_000
    max_series: int = 40_000
    max_days: int = 3000
    max_selected: int = 32

    def __post_init__(self):
        for name in (
            "max_seconds",
            "max_rows",
            "max_series",
            "max_days",
            "max_selected",
        ):
            integer(getattr(self, name), name)
        if self.max_seconds > 110:
            raise ValueError("M3 max_seconds must be <=110; use external 120s timeout")
        self.started = time.monotonic()

    def check(self, row=0):
        if row > self.max_rows or time.monotonic() - self.started > self.max_seconds:
            raise RuntimeError("M3 read resource limit exceeded; no partial result")


def rows(path: Path, limits: ReadLimits):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, None)
        if not header or len(header) != len(set(header)):
            raise ValueError(f"missing/duplicate columns: {path.name}")
        yield header
        for number, row in enumerate(reader, 1):
            limits.check(number)
            if len(row) != len(header):
                raise ValueError(f"ragged CSV row {number}: {path.name}")
            yield row


def count_cell(value: str):
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError(
            "sales must be observed nonnegative integer cells; no imputation"
        )
    result = int(value)
    if result > 2**53:
        raise ValueError("sales exceeds M1 exact count range")
    return result


def sales_header(header, limits):
    n = len(header) - len(META)
    if tuple(header[:6]) != META or n <= 0 or n > limits.max_days:
        raise ValueError("invalid M5 sales schema or day limit")
    if header[6:] != [f"d_{i}" for i in range(1, n + 1)]:
        raise ValueError("sales columns must be consecutive d_1..d_N")
    return n


def metadata(row):
    fields = dict(zip(META, row[:6], strict=True))
    if any(not value for value in fields.values()):
        raise ValueError("empty series metadata")
    series = fields["item_id"] + "_" + fields["store_id"]
    if fields["id"] not in (series + "_validation", series + "_evaluation"):
        raise ValueError("id does not match item/store")
    if not fields["store_id"].startswith(fields["state_id"] + "_"):
        raise ValueError("store/state mismatch")
    return series, fields


def load_catalog(path: Path, limits: ReadLimits):
    iterator = rows(path, limits)
    days = sales_header(next(iterator), limits)
    catalog = {}
    for row in iterator:
        key, fields = metadata(row)
        if key in catalog:
            raise ValueError("duplicate item/store")
        catalog[key] = fields
        if len(catalog) > limits.max_series:
            raise RuntimeError("catalog memory bound exceeded")
    if not catalog:
        raise ValueError("empty catalog")
    return catalog, days


def rank_candidates(catalog, count: int, seed: int):
    integer(count, "candidate count")
    integer(seed, "selection seed", 0)
    if count > len(catalog):
        raise ValueError("candidate count exceeds catalog")
    return tuple(
        sorted(
            catalog,
            key=lambda k: (hashlib.sha256(f"{seed}:{k}".encode()).hexdigest(), k),
        )[:count]
    )


def eligible(observations: tuple[Observation, ...], window: Window, min_nonzero: int):
    """Only the common shortest history is admissible for outcome-based screening."""
    integer(min_nonzero, "min_nonzero", 0)
    if min_nonzero > len(window.days):
        raise ValueError("eligibility threshold exceeds screening history")
    if tuple(o.day for o in observations) != window.days:
        raise ValueError("eligibility received data outside declared screening window")
    return sum(o.sales > 0 for o in observations) >= min_nonzero


def load_calendar(path: Path, limits: ReadLimits):
    iterator = rows(path, limits)
    if tuple(next(iterator)) != CALENDAR:
        raise ValueError("invalid calendar schema")
    calendar = {}
    previous = None
    for i, values in enumerate(iterator, 1):
        if i > limits.max_days:
            raise RuntimeError("calendar day bound exceeded")
        row = dict(zip(CALENDAR, values, strict=True))
        day = date.fromisoformat(row["date"])
        if row["d"] != f"d_{i}" or day.isoformat() != row["date"]:
            raise ValueError("invalid calendar day/date key")
        if previous is not None and day != previous + timedelta(days=1):
            raise ValueError("calendar missing/duplicate/nonchronological date")
        if (int(row["year"]), int(row["month"])) != (day.year, day.month):
            raise ValueError("inconsistent calendar year/month")
        if (
            row["weekday"] != day.strftime("%A")
            or int(row["wday"]) != (day.weekday() + 2) % 7 + 1
        ):
            raise ValueError("inconsistent weekday")
        if not re.fullmatch(r"[0-9]+", row["wm_yr_wk"]):
            raise ValueError("invalid week key")
        if any(row[f"snap_{s}"] not in ("0", "1") for s in ("CA", "TX", "WI")):
            raise ValueError("invalid SNAP flag")
        calendar[i] = row
        previous = day
    if not calendar:
        raise ValueError("empty calendar")
    return calendar


def load_observations(path, keys, window, calendar, limits):
    """Return only the requested days/series, with no data-source handle attached."""
    keys = tuple(keys)
    if not keys or len(set(keys)) != len(keys) or len(keys) > limits.max_selected:
        raise ValueError("invalid selected series or selection memory bound")
    if len(window.days) > limits.max_days:
        raise RuntimeError("observation day bound exceeded")
    if any(day not in calendar for day in window.days):
        raise ValueError("calendar join missing requested day")
    iterator = rows(path, limits)
    maximum = sales_header(next(iterator), limits)
    if window.stop - 1 > maximum:
        raise ValueError("requested sales days unavailable")
    wanted, result = set(keys), {}
    for row in iterator:
        # Do not convert or validate any unrequested sales cell.
        key = row[1] + "_" + row[4]
        if key not in wanted:
            continue
        metadata(row)
        if key in result:
            raise ValueError("duplicate selected series")
        result[key] = tuple(
            Observation(day, calendar[day]["date"], count_cell(row[5 + day]))
            for day in window.days
        )
    if set(result) != wanted:
        raise ValueError("selected series missing")
    return result


def check_overlap(validation, evaluation, keys, window, calendar, limits):
    """Check only explicitly authorized history; never inspect later outcomes."""
    maxima = []
    for path in (validation, evaluation):
        iterator = rows(path, limits)
        try:
            maxima.append(sales_header(next(iterator), limits))
        finally:
            iterator.close()
    stop = min(window.stop, min(maxima) + 1)
    if stop <= window.start:
        return {
            "checked_series": 0,
            "checked_window": None,
            "equal": None,
            "scope": "no shared columns in requested pre-origin window",
        }
    window = Window(window.start, stop)
    a = load_observations(validation, keys, window, calendar, limits)
    b = load_observations(evaluation, keys, window, calendar, limits)
    if a != b:
        raise ValueError("overlapping M5 histories disagree")
    return {
        "checked_series": len(keys),
        "checked_window": [window.start, window.stop],
        "equal": True,
        "scope": "requested pre-origin cells only",
    }


def load_prices(path, catalog, keys, weeks, limits):
    """Retrospective join data only. No claim these prices were known in advance."""
    if len(keys) > limits.max_selected or len(weeks) > limits.max_days:
        raise ValueError("price join exceeds memory bound")
    pairs = {(catalog[k]["store_id"], catalog[k]["item_id"]): k for k in keys}
    weeks = set(weeks)
    iterator = rows(path, limits)
    if tuple(next(iterator)) != PRICE:
        raise ValueError("invalid price schema")
    result = {}
    for row in iterator:
        pair = (row[0], row[1])
        if pair not in pairs or row[2] not in weeks:
            continue
        key = (pairs[pair], row[2])
        if key in result:
            raise ValueError("duplicate price join key")
        value = float(row[3])
        if not math.isfinite(value) or value <= 0:
            raise ValueError("price must be positive finite; no fill")
        result[key] = value
    return result


def price_features(series, days, calendar, prices, release_days, evidence):
    """Require external availability evidence; M5 has no price publication times."""
    if not evidence:
        raise ValueError("price availability evidence required")
    result = []
    for day in days:
        week = calendar[day]["wm_yr_wk"]
        key = (series, week)
        if key not in prices or key not in release_days:
            raise ValueError("missing price/release-time join; no imputation")
        result.append(
            Feature("sell_price", day, release_days[key], prices[key], evidence)
        )
    return tuple(result)


def calendar_features(days, calendar):
    # Compute deterministic civil-calendar features, never assume event/SNAP release.
    return tuple(
        Feature(name, day, 0, value, "deterministic civil calendar")
        for day in days
        for name, value in (
            ("weekday", date.fromisoformat(calendar[day]["date"]).weekday()),
            ("month", date.fromisoformat(calendar[day]["date"]).month),
        )
    )
