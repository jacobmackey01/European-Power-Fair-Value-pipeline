# Technical Notes

This note maps the main portfolio claims to the exact code and outputs in the repository.

## 1. SMARD API Ingestion And QA

Relevant files:

- `src/power_fair_value/smard.py`
- `src/power_fair_value/qa.py`
- `tests/test_models.py`
- `outputs/qa_report.md`

The pipeline downloads public hourly data from SMARD/Bundesnetzagentur. Timestamps are regularised in UTC, then converted to `Europe/Berlin` for local power-day checks.

The DST check is implemented in `expected_local_power_day_hours()`:

- March clock-change day is expected to have 23 local hours.
- October clock-change day is expected to have 25 local hours.
- Normal days are expected to have 24 local hours.

This avoids forcing European power data into a naive fixed 24-hour daily structure.

## 2. Baseline Versus XGBoost

Relevant files:

- `src/power_fair_value/features.py`
- `src/power_fair_value/models.py`
- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/feature_importance.csv`

The baseline model is the previous-week same-hour price:

```text
baseline_pred = price_lag_168
```

The improved model is an `XGBRegressor` trained on engineered features, including:

- forecasted load
- forecasted wind and solar
- residual load
- `price_lag_24`
- `price_lag_168`
- 7-day rolling price average
- cyclical calendar encodings

The validation split is chronological, not random, to avoid leaking future information into training.

Final validation metrics:

| Model | MAE | RMSE | Bias |
| --- | ---: | ---: | ---: |
| Previous-week same-hour baseline | 48.31 | 74.09 | -3.51 |
| XGBoost fundamental model | 19.49 | 33.70 | -10.43 |

The negative bias is intentionally reported. A production version would add missing marginal-cost drivers such as gas, carbon, coal, outages, temperature, and interconnector flows.

## 3. Prompt-Curve Translation

Relevant files:

- `src/power_fair_value/curve.py`
- `outputs/prompt_curve_view.md`

The model's latest day-ahead fair-value average is compared with a manual Front-Week baseload reference supplied through:

```powershell
python scripts/run_case_study.py --front-week-price 110.22
```

The signal threshold is the validation MAE. If the fair-value spread is smaller than the model's typical absolute error, the pipeline reports a neutral stance rather than a false-precision trade call.

## 4. Auditable LLM Reporting Layer

Relevant files:

- `src/power_fair_value/llm_component.py`
- `logs/llm_prompt.md`
- `logs/llm_output.md`

The LLM component is a reporting layer, not a forecaster. It receives structured JSON containing:

- market name
- data source
- QA summary
- baseline and XGBoost metrics
- curve-view fields
- decision threshold and stance

The prompt is constrained to produce concise, auditable commentary and explicitly tells the model not to invent data. The request uses `temperature=0`, and both the prompt and output are written to disk for review.

This design keeps the numeric model deterministic and uses the LLM only to reduce manual report-writing overhead.
