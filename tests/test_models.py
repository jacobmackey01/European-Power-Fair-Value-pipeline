import numpy as np
import pandas as pd

from power_fair_value.features import add_features
from power_fair_value.models import clean_model_frame
from power_fair_value.qa import expected_local_power_day_hours


def test_feature_frame_contains_lagged_price_columns():
    timestamps = pd.date_range("2025-01-01", periods=200, freq="h", tz="UTC")
    df = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "timestamp_cet": timestamps.tz_convert("Europe/Berlin"),
            "price_da_eur_mwh": np.arange(200.0),
            "wind_onshore_forecast_mw": 1000.0,
            "wind_offshore_forecast_mw": 500.0,
            "solar_forecast_mw": 200.0,
            "load_forecast_mw": 50000.0,
        }
    )

    featured = add_features(df)
    clean = clean_model_frame(featured)

    assert "price_lag_24" in clean.columns
    assert "price_lag_168" in clean.columns
    assert clean["price_lag_168"].iloc[0] == 0.0


def test_expected_local_power_day_hours_handles_dst():
    assert expected_local_power_day_hours(pd.Timestamp("2025-03-30").date()) == 23
    assert expected_local_power_day_hours(pd.Timestamp("2025-10-26").date()) == 25
    assert expected_local_power_day_hours(pd.Timestamp("2025-04-01").date()) == 24
