"""SMARD public API ingestion."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import pandas as pd


BASE_URL = "https://www.smard.de/app/chart_data"
MARKET_TZ = ZoneInfo("Europe/Berlin")


@dataclass(frozen=True)
class SmardSeries:
    name: str
    filter_id: int
    region: str
    unit: str


SERIES = [
    SmardSeries("price_da_eur_mwh", 4169, "DE-LU", "EUR/MWh"),
    SmardSeries("load_forecast_mw", 122, "DE", "MW"),
    SmardSeries("wind_onshore_forecast_mw", 123, "DE", "MW"),
    SmardSeries("wind_offshore_forecast_mw", 3791, "DE", "MW"),
    SmardSeries("solar_forecast_mw", 125, "DE", "MW"),
]


def _read_json(url: str) -> dict:
    with urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _to_date(value: str | date | datetime) -> date:
    if isinstance(value, str):
        return datetime.fromisoformat(value).date()
    elif isinstance(value, date) and not isinstance(value, datetime):
        return value
    return value.astimezone(MARKET_TZ).date() if value.tzinfo else value.date()


def _local_midnight_ms(value: str | date | datetime) -> int:
    local_date = _to_date(value)
    dt = datetime(local_date.year, local_date.month, local_date.day, tzinfo=MARKET_TZ)
    return int(dt.timestamp() * 1000)


def _local_end_of_day_ms(value: str | date | datetime) -> int:
    local_date = _to_date(value)
    next_midnight = datetime(local_date.year, local_date.month, local_date.day, tzinfo=MARKET_TZ) + timedelta(days=1)
    return int(next_midnight.timestamp() * 1000) - 1


def _timestamp_index(series: SmardSeries, resolution: str = "hour") -> list[int]:
    url = f"{BASE_URL}/{series.filter_id}/{series.region}/index_{resolution}.json"
    return _read_json(url)["timestamps"]


def _chunk(series: SmardSeries, timestamp: int, resolution: str = "hour") -> list[list[float]]:
    url = (
        f"{BASE_URL}/{series.filter_id}/{series.region}/"
        f"{series.filter_id}_{series.region}_{resolution}_{timestamp}.json"
    )
    return _read_json(url).get("series", [])


def _candidate_timestamps(timestamps: Iterable[int], start_ms: int, end_ms: int) -> list[int]:
    # SMARD chunks are weekly-ish. Pull the chunk immediately before the start
    # so lag features and edge hours are not accidentally dropped.
    ordered = sorted(timestamps)
    candidates = [ts for ts in ordered if start_ms - 8 * 24 * 3600 * 1000 <= ts <= end_ms]
    return candidates


def fetch_smard_series(
    series: SmardSeries,
    start: str,
    end: str,
    *,
    sleep_seconds: float = 0.05,
) -> pd.DataFrame:
    start_ms = _local_midnight_ms(start)
    end_ms = _local_end_of_day_ms(end)
    timestamps = _candidate_timestamps(_timestamp_index(series), start_ms, end_ms)

    rows: list[list[float]] = []
    for timestamp in timestamps:
        rows.extend(_chunk(series, timestamp))
        time.sleep(sleep_seconds)

    df = pd.DataFrame(rows, columns=["timestamp_ms", series.name])
    df = df.drop_duplicates("timestamp_ms").sort_values("timestamp_ms")
    df = df[(df["timestamp_ms"] >= start_ms) & (df["timestamp_ms"] <= end_ms)]
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    return df[["timestamp_utc", series.name]]


def _regularize_hourly_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("timestamp_utc").set_index("timestamp_utc")
    full_index = pd.date_range(df.index.min(), df.index.max(), freq="h", tz=timezone.utc)
    df = df.reindex(full_index)
    df.index.name = "timestamp_utc"

    # Do not fill the target price. Small gaps in fundamentals are interpolated
    # so a missing wind/load datapoint does not unnecessarily destroy a whole day.
    fundamental_columns = [column for column in df.columns if column != "price_da_eur_mwh"]
    df[fundamental_columns] = df[fundamental_columns].interpolate(method="time", limit=2, limit_direction="both")
    df = df.reset_index()
    df["timestamp_cet"] = df["timestamp_utc"].dt.tz_convert(MARKET_TZ)
    return df


def build_dataset(start: str, end: str, raw_dir: Path) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    merged: pd.DataFrame | None = None

    for series in SERIES:
        df = fetch_smard_series(series, start, end)
        df.to_csv(raw_dir / f"{series.name}.csv", index=False)
        merged = df if merged is None else merged.merge(df, on="timestamp_utc", how="outer")

    assert merged is not None
    return _regularize_hourly_index(merged)
