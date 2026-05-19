"""Dataset quality checks."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

MARKET_TZ = ZoneInfo("Europe/Berlin")


def _markdown_table(df: pd.DataFrame) -> str:
    columns = list(df.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def expected_local_power_day_hours(local_date) -> int:
    start = datetime(local_date.year, local_date.month, local_date.day, tzinfo=MARKET_TZ)
    next_date = local_date + timedelta(days=1)
    end = datetime(next_date.year, next_date.month, next_date.day, tzinfo=MARKET_TZ)
    seconds = (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds()
    return int(seconds / 3600)


def qa_checks(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    checks: list[dict[str, object]] = []
    required = [
        "price_da_eur_mwh",
        "load_forecast_mw",
        "wind_onshore_forecast_mw",
        "wind_offshore_forecast_mw",
        "solar_forecast_mw",
    ]

    checks.append({"check": "row_count", "value": len(df), "passed": len(df) > 24 * 90})
    checks.append({"check": "timestamp_unique", "value": bool(df["timestamp_utc"].is_unique), "passed": bool(df["timestamp_utc"].is_unique)})
    checks.append({"check": "timestamp_monotonic", "value": bool(df["timestamp_utc"].is_monotonic_increasing), "passed": bool(df["timestamp_utc"].is_monotonic_increasing)})
    expected_utc = pd.date_range(df["timestamp_utc"].min(), df["timestamp_utc"].max(), freq="h", tz="UTC")
    missing_utc_hours = int(len(expected_utc.difference(pd.DatetimeIndex(df["timestamp_utc"]))))
    checks.append({"check": "missing_utc_hours", "value": missing_utc_hours, "passed": missing_utc_hours == 0})

    for column in required:
        missing = int(df[column].isna().sum())
        checks.append({"check": f"missing_{column}", "value": missing, "passed": missing == 0})

    local = df["timestamp_utc"].dt.tz_convert(MARKET_TZ)
    local_counts = local.dt.date.value_counts().sort_index()
    bad_power_days = 0
    for local_date, count in local_counts.items():
        expected_hours = expected_local_power_day_hours(local_date)
        if int(count) != expected_hours:
            bad_power_days += 1
    checks.append({"check": "bad_local_power_day_hour_counts", "value": bad_power_days, "passed": bad_power_days == 0})

    checks.append({"check": "price_reasonable_min", "value": float(df["price_da_eur_mwh"].min()), "passed": df["price_da_eur_mwh"].min() > -1000})
    checks.append({"check": "price_reasonable_max", "value": float(df["price_da_eur_mwh"].max()), "passed": df["price_da_eur_mwh"].max() < 5000})

    summary = {
        "start": str(df["timestamp_utc"].min()),
        "end": str(df["timestamp_utc"].max()),
        "local_start_date": str(local.dt.date.min()),
        "local_end_date": str(local.dt.date.max()),
        "rows": len(df),
        "passed": all(bool(row["passed"]) for row in checks),
    }
    return pd.DataFrame(checks), summary


def write_qa_report(checks: pd.DataFrame, summary: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# QA Report",
        "",
        f"Start: {summary['start']}",
        f"End: {summary['end']}",
        f"Local power-day start: {summary['local_start_date']}",
        f"Local power-day end: {summary['local_end_date']}",
        f"Rows: {summary['rows']}",
        f"Overall pass: {summary['passed']}",
        "",
        _markdown_table(checks),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
