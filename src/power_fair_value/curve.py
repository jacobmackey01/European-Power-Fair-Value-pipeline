"""Translate DA fair-value forecasts into prompt-curve guidance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def latest_day_view(
    predictions: pd.DataFrame,
    metrics: pd.DataFrame,
    *,
    front_week_price: float | None = None,
) -> dict[str, object]:
    preds = predictions.copy()
    preds["local_date"] = preds["timestamp_cet"].dt.date
    latest_date = preds["local_date"].max()
    latest = preds[preds["local_date"] == latest_date]

    recent = preds[preds["timestamp_utc"] >= preds["timestamp_utc"].max() - pd.Timedelta(days=14)]
    improved_mae = float(metrics.loc[metrics["model"] != "baseline_prev_week_same_hour", "mae"].iloc[0])

    forecast_avg = float(latest["improved_pred"].mean())
    baseline_avg = float(latest["baseline_pred"].mean())
    recent_actual_avg = float(recent["price_da_eur_mwh"].mean())
    reference_price = float(front_week_price) if front_week_price is not None else recent_actual_avg
    reference_type = "manual_front_week_curve_mark" if front_week_price is not None else "recent_14d_DA_proxy"
    fair_value_premium = forecast_avg - reference_price
    threshold = max(5.0, improved_mae)

    if fair_value_premium > threshold:
        stance = "BUY / long Front-Week baseload bias"
    elif fair_value_premium < -threshold:
        stance = "SELL / short Front-Week baseload bias"
    else:
        stance = "Neutral / no strong prompt bias"

    return {
        "latest_date": str(latest_date),
        "forecast_avg_eur_mwh": round(forecast_avg, 2),
        "baseline_avg_eur_mwh": round(baseline_avg, 2),
        "recent_14d_actual_avg_eur_mwh": round(recent_actual_avg, 2),
        "reference_type": reference_type,
        "reference_price_eur_mwh": round(reference_price, 2),
        "fair_value_premium_eur_mwh": round(fair_value_premium, 2),
        "validation_mae_eur_mwh": round(improved_mae, 2),
        "decision_threshold_eur_mwh": round(threshold, 2),
        "stance": stance,
    }


def write_curve_view(view: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Prompt Curve Translation",
        "",
        f"Latest forecast date: {view['latest_date']}",
        f"Forecast DA fair value: {view['forecast_avg_eur_mwh']} EUR/MWh",
        f"Baseline same-hour weekly average: {view['baseline_avg_eur_mwh']} EUR/MWh",
        f"Recent 14-day realised DA average: {view['recent_14d_actual_avg_eur_mwh']} EUR/MWh",
        f"Reference type: {view['reference_type']}",
        f"Reference price: {view['reference_price_eur_mwh']} EUR/MWh",
        f"Fair-value spread to reference: {view['fair_value_premium_eur_mwh']} EUR/MWh",
        f"Validation MAE: {view['validation_mae_eur_mwh']} EUR/MWh",
        f"Decision threshold: {view['decision_threshold_eur_mwh']} EUR/MWh",
        "",
        f"Guidance: {view['stance']}",
        "",
        "Use: if DA fair value is materially above the Front-Week baseload mark, this supports buying/long prompt exposure; if materially below, it supports selling/short prompt exposure. If no live curve mark is supplied, the recent 14-day DA average is only a proxy and should be replaced before trading.",
        "",
        "Invalidation: large intraday wind/solar forecast revisions, failed QA checks, realised DA clear within one validation MAE of recent averages, or market-specific outages/fuel/news not captured by the model.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
