"""Forecast models and validation metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from power_fair_value.features import FEATURE_COLUMNS


TARGET = "price_da_eur_mwh"


def clean_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    needed = ["timestamp_utc", "timestamp_cet", TARGET, *FEATURE_COLUMNS]
    return df[needed].dropna().copy()


def train_validation_split(df: pd.DataFrame, val_days: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = df["timestamp_utc"].max() - pd.Timedelta(days=val_days)
    train = df[df["timestamp_utc"] < cutoff].copy()
    valid = df[df["timestamp_utc"] >= cutoff].copy()
    return train, valid


def fit_xgboost(train: pd.DataFrame) -> XGBRegressor:
    x = train[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = train[TARGET].to_numpy(dtype=float)
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=1,
    )
    model.fit(x, y)
    return model


def predict_xgboost(model: XGBRegressor, frame: pd.DataFrame) -> np.ndarray:
    return model.predict(frame[FEATURE_COLUMNS].to_numpy(dtype=float))


def metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    error = y_pred.to_numpy(dtype=float) - y_true.to_numpy(dtype=float)
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "bias": float(np.mean(error)),
    }


def validate_models(frame: pd.DataFrame, val_days: int = 30) -> tuple[pd.DataFrame, pd.DataFrame, XGBRegressor]:
    clean = clean_model_frame(frame)
    train, valid = train_validation_split(clean, val_days=val_days)
    model = fit_xgboost(train)

    preds = valid[["timestamp_utc", "timestamp_cet", TARGET]].copy()
    preds["baseline_pred"] = valid["price_lag_168"]
    preds["improved_pred"] = predict_xgboost(model, valid)
    preds["id"] = preds["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    rows = []
    for name, column in [("baseline_prev_week_same_hour", "baseline_pred"), ("xgboost_fundamental_model", "improved_pred")]:
        row = {"model": name}
        row.update(metrics(preds[TARGET], preds[column]))
        rows.append(row)
    return preds, pd.DataFrame(rows), model


def feature_importance(model: XGBRegressor) -> pd.DataFrame:
    rows = [
        {"feature": feature, "importance": float(importance)}
        for feature, importance in zip(FEATURE_COLUMNS, model.feature_importances_)
    ]
    return pd.DataFrame(rows).sort_values("importance", ascending=False).reset_index(drop=True)
