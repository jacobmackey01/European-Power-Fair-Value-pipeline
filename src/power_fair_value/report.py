"""Case-study report generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from power_fair_value.llm_component import ascii_clean


def _markdown_table(df: pd.DataFrame) -> str:
    columns = list(df.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def write_case_study(
    path: Path,
    metrics: pd.DataFrame,
    qa_summary: dict[str, object],
    curve_view: dict[str, object],
    llm_note: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# European Power Fair Value: Forecasting Day-Ahead and Translating to Prompt Curve Views",
        "",
        "Name: Jacob Mackey",
        "Email: jacobmackey01@gmail.com",
        "",
        "## 1. Data Ingestion And QA",
        "",
        "Market: Germany/Luxembourg day-ahead power price (DE-LU). Source: SMARD, the Bundesnetzagentur electricity market data platform. The dataset combines hourly day-ahead prices with forecasted load, forecasted onshore wind, forecasted offshore wind, and forecasted photovoltaic generation.",
        "",
        f"Sample window: local power days {qa_summary.get('local_start_date', qa_summary['start'])} to {qa_summary.get('local_end_date', qa_summary['end'])} ({qa_summary['rows']} hourly rows before feature lag drops). QA overall pass: {qa_summary['passed']}.",
        "",
        "DST handling: timestamps are stored in UTC and converted to Europe/Berlin for local power-day grouping. QA explicitly checks local day hour counts, so spring-forward days must have 23 hours and fall-back days must have 25 hours.",
        "",
        "## 2. Forecasting And Validation",
        "",
        "Target: next-day/hourly day-ahead price in EUR/MWh. Baseline is previous-week same-hour price. Improved model is an XGBoost regressor using price lags, forecasted load, forecasted wind/solar, residual-load-style features, and calendar features. Validation is chronological over the final 30 days.",
        "",
        _markdown_table(metrics.round(3)),
        "",
        "## 3. Prompt Curve Translation",
        "",
        f"Latest forecast date: {curve_view['latest_date']}. Model DA fair value: {curve_view['forecast_avg_eur_mwh']} EUR/MWh versus reference price of {curve_view['reference_price_eur_mwh']} EUR/MWh ({curve_view['reference_type']}). Fair-value spread: {curve_view['fair_value_premium_eur_mwh']} EUR/MWh. Stance: {curve_view['stance']}.",
        "",
        "For an actual trade recommendation, the reference should be replaced with a live/manual Front-Week baseload curve mark via `--front-week-price`. Without that input, the pipeline clearly labels the comparison as a recent-DA proxy rather than a traded curve.",
        "",
        "The view is invalidated by material wind/solar forecast revisions, failed QA checks, outages/fuel/news outside the model, or realised DA clearing within roughly one validation MAE of recent averages.",
        "",
        "## 4. AI/LLM Integration",
        "",
        "The LLM is used programmatically after model validation to draft a concise trading commentary from structured metrics, QA results, and the curve-view signal. It reduces manual report-writing work and logs both prompt and output for auditability.",
        "",
        "LLM output:",
        "",
        ascii_clean(llm_note),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
