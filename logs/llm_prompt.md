# System Prompt

You are an energy trading analyst.
Write concise, auditable trading commentary from structured model outputs.
Do not invent new data. Mention model limitations and invalidation triggers.
Use ASCII only. Write EUR/MWh, not currency symbols.


# User Prompt

Draft a short DA-to-prompt-curve view from this JSON. Use 5 bullets maximum and include invalidation triggers.

{
  "market": "Germany/Luxembourg DE-LU day-ahead power",
  "data_source": "SMARD / Bundesnetzagentur public API",
  "qa": {
    "start": "2024-12-31 23:00:00+00:00",
    "end": "2026-05-06 21:00:00+00:00",
    "local_start_date": "2025-01-01",
    "local_end_date": "2026-05-06",
    "rows": 11783,
    "passed": true
  },
  "metrics": [
    {
      "model": "baseline_prev_week_same_hour",
      "mae": 48.31163661581137,
      "rmse": 74.09361816542146,
      "bias": -3.513689320388347
    },
    {
      "model": "xgboost_fundamental_model",
      "mae": 19.49372121987164,
      "rmse": 33.700155860527765,
      "bias": -10.427497387425081
    }
  ],
  "curve_view": {
    "latest_date": "2026-05-06",
    "forecast_avg_eur_mwh": 104.56,
    "baseline_avg_eur_mwh": 65.36,
    "recent_14d_actual_avg_eur_mwh": 70.09,
    "reference_type": "manual_front_week_curve_mark",
    "reference_price_eur_mwh": 110.22,
    "fair_value_premium_eur_mwh": -5.66,
    "validation_mae_eur_mwh": 19.49,
    "decision_threshold_eur_mwh": 19.49,
    "stance": "Neutral / no strong prompt bias"
  }
}