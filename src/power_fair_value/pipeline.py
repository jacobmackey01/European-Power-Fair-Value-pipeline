"""End-to-end case-study pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from power_fair_value.curve import latest_day_view, write_curve_view
from power_fair_value.features import add_features
from power_fair_value.llm_component import draft_trading_note
from power_fair_value.models import feature_importance, validate_models
from power_fair_value.qa import qa_checks, write_qa_report
from power_fair_value.report import write_case_study
from power_fair_value.smard import build_dataset


def run_case_study(
    *,
    start: str,
    end: str,
    project_dir: Path,
    skip_llm: bool = False,
    front_week_price: float | None = None,
) -> dict[str, Path]:
    data_raw = project_dir / "data" / "raw"
    data_processed = project_dir / "data" / "processed"
    outputs = project_dir / "outputs"
    logs = project_dir / "logs"
    docs = project_dir / "docs"

    dataset = build_dataset(start, end, data_raw)
    checks, qa_summary = qa_checks(dataset)
    write_qa_report(checks, qa_summary, outputs / "qa_report.md")

    features = add_features(dataset)
    data_processed.mkdir(parents=True, exist_ok=True)
    dataset_path = data_processed / "de_lu_power_dataset.csv"
    features.to_csv(dataset_path, index=False)

    predictions, metrics, model = validate_models(features, val_days=30)
    outputs.mkdir(parents=True, exist_ok=True)
    metrics_path = outputs / "metrics.csv"
    predictions_path = outputs / "predictions.csv"
    submission_path = outputs / "submission.csv"
    feature_importance_path = outputs / "feature_importance.csv"
    metrics.to_csv(metrics_path, index=False)
    predictions.to_csv(predictions_path, index=False)
    predictions[["id", "improved_pred"]].rename(columns={"improved_pred": "y_pred"}).to_csv(submission_path, index=False)
    feature_importance(model).to_csv(feature_importance_path, index=False)

    curve_view = latest_day_view(predictions, metrics, front_week_price=front_week_price)
    write_curve_view(curve_view, outputs / "prompt_curve_view.md")

    llm_summary = {
        "market": "Germany/Luxembourg DE-LU day-ahead power",
        "data_source": "SMARD / Bundesnetzagentur public API",
        "qa": qa_summary,
        "metrics": metrics.to_dict(orient="records"),
        "curve_view": curve_view,
    }
    if skip_llm:
        llm_note = "LLM step skipped by command-line flag."
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "llm_prompt.md").write_text("LLM step skipped.", encoding="utf-8")
        (logs / "llm_output.md").write_text(llm_note, encoding="utf-8")
    else:
        llm_note = draft_trading_note(llm_summary, logs)

    write_case_study(docs / "case_study.md", metrics, qa_summary, curve_view, llm_note)

    return {
        "dataset": dataset_path,
        "qa_report": outputs / "qa_report.md",
        "metrics": metrics_path,
        "predictions": predictions_path,
        "submission": submission_path,
        "feature_importance": feature_importance_path,
        "curve_view": outputs / "prompt_curve_view.md",
        "case_study": docs / "case_study.md",
        "llm_prompt": logs / "llm_prompt.md",
        "llm_output": logs / "llm_output.md",
    }
