# European Power Fair Value: Forecasting Day-Ahead and Translating to Prompt Curve Views

Name: Jacob Mackey
Email: jacobmackey01@gmail.com

## 1. Data Ingestion And QA

Market: Germany/Luxembourg day-ahead power price (DE-LU). Source: SMARD, the Bundesnetzagentur electricity market data platform. The dataset combines hourly day-ahead prices with forecasted load, forecasted onshore wind, forecasted offshore wind, and forecasted photovoltaic generation.

Sample window: local power days 2025-01-01 to 2026-05-06 (11783 hourly rows before feature lag drops). QA overall pass: True.

DST handling: timestamps are stored in UTC and converted to Europe/Berlin for local power-day grouping. QA explicitly checks local day hour counts, so spring-forward days must have 23 hours and fall-back days must have 25 hours.

## 2. Forecasting And Validation

Target: next-day/hourly day-ahead price in EUR/MWh. Baseline is previous-week same-hour price. Improved model is an XGBoost regressor using price lags, forecasted load, forecasted wind/solar, residual-load-style features, and calendar features. Validation is chronological over the final 30 days.

| model | mae | rmse | bias |
| --- | --- | --- | --- |
| baseline_prev_week_same_hour | 48.312 | 74.094 | -3.514 |
| xgboost_fundamental_model | 19.494 | 33.7 | -10.427 |

## 3. Prompt Curve Translation

Latest forecast date: 2026-05-06. Model DA fair value: 104.56 EUR/MWh versus reference price of 110.22 EUR/MWh (manual_front_week_curve_mark). Fair-value spread: -5.66 EUR/MWh. Stance: Neutral / no strong prompt bias.

For an actual trade recommendation, the reference should be replaced with a live/manual Front-Week baseload curve mark via `--front-week-price`. Without that input, the pipeline clearly labels the comparison as a recent-DA proxy rather than a traded curve.

The view is invalidated by material wind/solar forecast revisions, failed QA checks, outages/fuel/news outside the model, or realised DA clearing within roughly one validation MAE of recent averages.

## 4. AI/LLM Integration

The LLM is used programmatically after model validation to draft a concise trading commentary from structured metrics, QA results, and the curve-view signal. It reduces manual report-writing work and logs both prompt and output for auditability.

LLM output:

- DE-LU DA model output is above the baseline and recent realized levels: forecast avg 104.56 EUR/MWh vs baseline 65.36 EUR/MWh and 14d actual avg 70.09 EUR/MWh.
- Versus the manual front-week curve mark, the model implies a small discount: reference 110.22 EUR/MWh, fair value premium -5.66 EUR/MWh.
- Net view remains Neutral / no strong prompt bias because the premium is well inside the validation MAE of 19.49 EUR/MWh, so the signal is not strong enough to justify a directional prompt-curve call.
- Model quality is materially better than the naive baseline (MAE 19.49 vs 48.31 EUR/MWh; RMSE 33.70 vs 74.09 EUR/MWh), but the xgboost model still shows negative bias (-10.43 EUR/MWh), so it may understate prices.
- Invalidation triggers: if the DA forecast vs curve mark gap widens beyond +/-19.49 EUR/MWh, if the model bias flips materially, or if new market data pushes the 14d actual average or curve mark materially away from the current 70.09 / 110.22 EUR/MWh anchors.
