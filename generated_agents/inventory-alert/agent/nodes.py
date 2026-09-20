from __future__ import annotations

import json
import os

from harness_core import get_logger

from .prompts import ANALYSIS_PROMPT, SYSTEM_PROMPT

logger = get_logger(__name__)

_DEFAULT_MODEL = "openai/gpt-oss-120b"


def _get_model() -> str:
    return os.environ.get("AIR_MODEL", _DEFAULT_MODEL)


def _get_api_key() -> str:
    key = os.environ.get("AIREFINERY_API_KEY", "").strip()
    if not key:
        raise OSError("AIREFINERY_API_KEY must be set (see .env.example)")
    return key


def _strip_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            inner = parts[1].strip()
            if inner.startswith("json"):
                inner = inner[4:].strip()
            return inner
    return text


async def analyze(state: dict) -> dict:
    from air import AsyncAIRefinery

    logger.info("inventory_alert_analyze", sku=state.get("sku"))
    client = AsyncAIRefinery(api_key=_get_api_key())
    user_content = ANALYSIS_PROMPT.format(**state)
    response = await client.chat.completions.create(
        model=_get_model(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )
    raw = response.choices[0].message.content
    avg = state.get("avg_daily_sales", 1.0) or 1.0
    days = int(state.get("current_stock", 0) / avg)
    try:
        parsed = json.loads(_strip_markdown(raw))
    except (json.JSONDecodeError, ValueError):
        parsed = {
            "alert_level": "low" if days > state.get("lead_days", 7) else "critical",
            "recommended_order_qty": int(avg * state.get("lead_days", 7) * 2),
            "days_until_stockout": days,
            "message": raw,
        }
    return {**state, **parsed}
