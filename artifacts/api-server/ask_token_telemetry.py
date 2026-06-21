"""OpenAI token + cost bundle for Ask (Cosmic Intelligence) calls."""

from __future__ import annotations

import os
from typing import Any


def usd_inr_rate() -> float:
    try:
        return float(os.environ.get("COMPAT_USD_INR_RATE", "83") or "83")
    except (TypeError, ValueError):
        return 83.0


def usage_from_response(response: Any, model_requested: str) -> dict[str, Any]:
    """Extract tokens + USD/INR cost from an OpenAI chat completion response."""
    from vedic.compat.openai_pdf_telemetry import (
        estimate_call_cost_usd,
        get_effective_usd_per_1m_table,
        usage_triplet,
    )

    rm = getattr(response, "model", None) or model_requested or "gpt-4.1-mini"
    pt, ct, tt = usage_triplet(response)
    cached = 0
    try:
        usage = getattr(response, "usage", None)
        ptd = getattr(usage, "prompt_tokens_details", None) if usage else None
        if ptd is not None:
            cached = int(
                getattr(ptd, "cached_tokens", 0)
                or (ptd.get("cached_tokens", 0) if isinstance(ptd, dict) else 0)
                or 0
            )
    except Exception:
        cached = 0

    table, _src = get_effective_usd_per_1m_table()
    cost_usd = estimate_call_cost_usd(rm, pt, ct, table) if (pt or ct) else 0.0
    rate = usd_inr_rate()
    cost_inr = round(cost_usd * rate, 4)

    return {
        "llm_model": str(rm),
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "total_tokens": tt,
        "cached_tokens": cached,
        "cost_usd": round(cost_usd, 6),
        "cost_inr": cost_inr,
    }


def extract_usage_from_result(result: dict | None) -> dict[str, Any]:
    """Read flat or nested token fields from an Ask JSON result."""
    if not isinstance(result, dict):
        return {}
    nested = result.get("token_usage")
    if isinstance(nested, dict):
        return {
            "llm_model": nested.get("llm_model") or nested.get("model"),
            "prompt_tokens": nested.get("prompt_tokens"),
            "completion_tokens": nested.get("completion_tokens"),
            "total_tokens": nested.get("total_tokens"),
            "cached_tokens": nested.get("cached_tokens"),
            "cost_usd": nested.get("cost_usd"),
            "cost_inr": nested.get("cost_inr"),
        }
    return {
        "llm_model": result.get("llm_model"),
        "prompt_tokens": result.get("prompt_tokens"),
        "completion_tokens": result.get("completion_tokens"),
        "total_tokens": result.get("total_tokens"),
        "cached_tokens": result.get("cached_tokens"),
        "cost_usd": result.get("cost_usd"),
        "cost_inr": result.get("cost_inr"),
    }


__all__ = ["usage_from_response", "extract_usage_from_result", "usd_inr_rate"]
