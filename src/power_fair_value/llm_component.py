"""Programmatic OpenAI component for trading-note drafting."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        env_path = candidate / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return


SYSTEM_PROMPT = """You are an energy trading analyst.
Write concise, auditable trading commentary from structured model outputs.
Do not invent new data. Mention model limitations and invalidation triggers.
Use ASCII only. Write EUR/MWh, not currency symbols.
"""


def ascii_clean(text: str) -> str:
    replacements = {
        "€": "EUR",
        "â‚¬": "EUR",
        "’": "'",
        "â€™": "'",
        "âEUR™": "'",
        "–": "-",
        "—": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\bEUR\s*(\d+(?:\.\d+)?)\s*/MWh", r"\1 EUR/MWh", text)
    text = re.sub(r"\bEUR\s*(\d+(?:\.\d+)?)", r"\1 EUR", text)
    return text


def draft_trading_note(summary: dict[str, object], logs_dir: Path) -> str:
    logs_dir.mkdir(parents=True, exist_ok=True)
    _load_env()

    user_prompt = (
        "Draft a short DA-to-prompt-curve view from this JSON. "
        "Use 5 bullets maximum and include invalidation triggers.\n\n"
        + json.dumps(summary, indent=2)
    )
    (logs_dir / "llm_prompt.md").write_text(
        "# System Prompt\n\n" + SYSTEM_PROMPT + "\n\n# User Prompt\n\n" + user_prompt,
        encoding="utf-8",
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        output = "LLM step skipped: OPENAI_API_KEY was not available."
        (logs_dir / "llm_output.md").write_text(output, encoding="utf-8")
        return output

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        store=True,
    )
    output = ascii_clean(response.output_text)
    (logs_dir / "llm_output.md").write_text(output, encoding="utf-8")
    return output
