"""Feature engineering for hourly power prices."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("timestamp_utc")
    local = out["timestamp_cet"]

    out["hour"] = local.dt.hour
    out["day_of_week"] = local.dt.dayofweek
    out["month"] = local.dt.month
    out["is_weekend"] = out["day_of_week"].isin([5, 6]).astype(int)

    out["wind_total_forecast_mw"] = out["wind_onshore_forecast_mw"] + out["wind_offshore_forecast_mw"]
    out["renewable_forecast_mw"] = out["wind_total_forecast_mw"] + out["solar_forecast_mw"]
    out["residual_load_forecast_mw"] = out["load_forecast_mw"] - out["renewable_forecast_mw"]
    out["price_lag_24"] = out["price_da_eur_mwh"].shift(24)
    out["price_lag_168"] = out["price_da_eur_mwh"].shift(168)
    out["price_roll_7d"] = out["price_da_eur_mwh"].shift(24).rolling(168, min_periods=24).mean()

    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24)
    out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 7)
    out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 7)
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)
    return out


FEATURE_COLUMNS = [
    "wind_onshore_forecast_mw",
    "wind_offshore_forecast_mw",
    "solar_forecast_mw",
    "load_forecast_mw",
    "wind_total_forecast_mw",
    "renewable_forecast_mw",
    "residual_load_forecast_mw",
    "price_lag_24",
    "price_lag_168",
    "price_roll_7d",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",
]
