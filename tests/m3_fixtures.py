"""Independent miniature M5-shaped CSVs; no real data and no production readers."""

import csv
import hashlib
from datetime import date, timedelta


def write_csv(path, header, values):
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(values)


def make_fixture(root):
    root.mkdir(exist_ok=True)
    calendar = []
    for i in range(1, 281):
        dt = date(2020, 1, 1) + timedelta(days=i - 1)
        calendar.append(
            [
                dt.isoformat(),
                str(1000 + (i - 1) // 7),
                dt.strftime("%A"),
                (dt.weekday() + 2) % 7 + 1,
                dt.month,
                dt.year,
                f"d_{i}",
                "",
                "",
                "",
                "",
                0,
                1,
                0,
            ]
        )
    write_csv(
        root / "calendar.csv",
        [
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
        ],
        calendar,
    )
    meta = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
    for suffix, count in [("validation", 252), ("evaluation", 280)]:
        rows = []
        for item in ("FOODS_1_001", "FOODS_1_002", "FOODS_1_003"):
            sales = [i % 5 if i <= 224 else 999999 for i in range(1, count + 1)]
            rows.append(
                [f"{item}_CA_1_{suffix}", item, "FOODS_1", "FOODS", "CA_1", "CA"]
                + sales
            )
        write_csv(
            root / f"sales_train_{suffix}.csv",
            meta + [f"d_{i}" for i in range(1, count + 1)],
            rows,
        )
    write_csv(
        root / "sell_prices.csv",
        ["store_id", "item_id", "wm_yr_wk", "sell_price"],
        [
            ["CA_1", item, str(week), "2.50"]
            for item in ("FOODS_1_001", "FOODS_1_002", "FOODS_1_003")
            for week in range(1000, 1040)
        ],
    )
    write_csv(
        root / "sample_submission.csv",
        ["id"] + [f"F{i}" for i in range(1, 29)],
        [["FOODS_1_001_CA_1_validation"] + [0] * 28],
    )
    return fixture_manifest(root)


def fixture_manifest(root):
    return {
        "dataset": "independent miniature fixture",
        "files": [
            {
                "filename": p.name,
                "bytes": len(p.read_bytes()),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in sorted(root.glob("*.csv"))
        ],
    }


def config():
    return {
        "schema_version": 1,
        "dataset_version": "miniature-m5-fixture-v1",
        "mode": "development_demo",
        "seed": 0,
        "candidate_count": 3,
        "min_nonzero": 1,
        "origins": [225],
        "horizon": 28,
        "development_window": {"start": 1, "stop": 253},
        "budgets": [28, 56, 112, 224],
        "calendar_features": True,
        "limits": {
            "max_seconds": 10,
            "max_rows": 1000,
            "max_series": 10,
            "max_days": 300,
            "max_selected": 3,
        },
    }
