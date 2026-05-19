from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Resolve the project root from the script location.
PROJECT_DIR = Path(__file__).resolve().parents[1]

# Add src/ to the Python import path for local execution.
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

# Import the end-to-end case-study pipeline.
from power_fair_value.pipeline import run_case_study


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the European power fair-value pipeline.")

    # Historical sample window, interpreted as Europe/Berlin local power days.
    parser.add_argument("--start", default="2025-01-01", help="Inclusive start date, YYYY-MM-DD.")
    parser.add_argument("--end", default="2026-05-06", help="Inclusive end date, YYYY-MM-DD.")

    # Optional switch for running the deterministic data/model path without the OpenAI commentary step.
    parser.add_argument("--skip-llm", action="store_true", help="Run all steps except the OpenAI commentary draft.")

    # Optional Front-Week baseload curve mark used to turn DA fair value into a tradable prompt view.
    # If omitted, the pipeline uses and labels a recent DA average as a proxy reference.
    parser.add_argument(
        "--front-week-price",
        type=float,
        default=None,
        help="Optional live/manual Front-Week baseload curve mark in EUR/MWh for tradable signal translation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Pipeline stages:
    # 1. Download SMARD hourly DE-LU price and fundamental data.
    # 2. Run QA checks for missing values, timestamp continuity, and DST local-day counts.
    # 3. Build lag, renewable, load, and calendar features.
    # 4. Validate baseline and XGBoost models on a chronological holdout.
    # 5. Translate DA fair value into a prompt-curve view.
    # 6. Generate and log the OpenAI trading-note draft, unless skipped.
    # 7. Write processed data, QA, metrics, predictions, report, and LLM logs.
    paths = run_case_study(
        start=args.start,
        end=args.end,
        project_dir=PROJECT_DIR,
        skip_llm=args.skip_llm,
        front_week_price=args.front_week_price,
    )

    # Echo generated artifacts for review/submission.
    print("Wrote case-study outputs:")
    for name, path in paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
