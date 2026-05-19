# Prompt Curve Translation

Latest forecast date: 2026-05-06
Forecast DA fair value: 104.56 EUR/MWh
Baseline same-hour weekly average: 65.36 EUR/MWh
Recent 14-day realised DA average: 70.09 EUR/MWh
Reference type: manual_front_week_curve_mark
Reference price: 110.22 EUR/MWh
Fair-value spread to reference: -5.66 EUR/MWh
Validation MAE: 19.49 EUR/MWh
Decision threshold: 19.49 EUR/MWh

Guidance: Neutral / no strong prompt bias

Use: if DA fair value is materially above the Front-Week baseload mark, this supports buying/long prompt exposure; if materially below, it supports selling/short prompt exposure. If no live curve mark is supplied, the recent 14-day DA average is only a proxy and should be replaced before trading.

Invalidation: large intraday wind/solar forecast revisions, failed QA checks, realised DA clear within one validation MAE of recent averages, or market-specific outages/fuel/news not captured by the model.
