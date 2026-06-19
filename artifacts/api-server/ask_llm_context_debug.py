"""Admin-only debug payload — what chart/context was sent to the Ask LLM."""

from __future__ import annotations

import json
import os
from typing import Any

_MAX_DB_CHARS = 80_000


def build_admin_llm_context(
    *,
    question: str,
    route: str = "raw_passthrough",
    question_type: str = "STATIC",
    is_timing: bool = False,
    checks: dict[str, Any] | None = None,
    chart_text: str = "",
    system_prompt: str = "",
    extra_rules: str = "",
    user_payload: str = "",
    model: str = "",
    max_tokens: int | None = None,
    slice_meta: dict[str, Any] | None = None,
    blocks: dict[str, Any] | None = None,
    llm_called: bool = True,
    skip_reason: str = "",
) -> dict[str, Any]:
    """Structured snapshot for admin panel (never shown to end users)."""
    return {
        "version": 1,
        "route": route,
        "question": (question or "")[:500],
        "question_type": question_type,
        "is_timing": bool(is_timing),
        "llm_called": bool(llm_called),
        "skip_reason": (skip_reason or "")[:200] or None,
        "checks": checks or {},
        "slice_meta": slice_meta or {},
        "blocks": blocks or {},
        "chart_text": chart_text or "",
        "extra_rules": extra_rules or "",
        "system_prompt": system_prompt or "",
        "user_payload": user_payload or "",
        "model": model or None,
        "max_tokens": max_tokens,
        "sizes": {
            "chart_chars": len(chart_text or ""),
            "system_prompt_chars": len(system_prompt or ""),
            "extra_rules_chars": len(extra_rules or ""),
            "user_payload_chars": len(user_payload or ""),
        },
    }


def serialize_llm_context_for_db(ctx: Any) -> str | None:
    if not ctx:
        return None
    try:
        raw = json.dumps(ctx, ensure_ascii=False, default=str)
    except Exception:
        return None
    if len(raw) > _MAX_DB_CHARS:
        return raw[: _MAX_DB_CHARS - 1] + "…"
    return raw


def parse_llm_context_from_db(raw: str | None) -> dict[str, Any] | None:
    if not raw or not str(raw).strip():
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return {"raw": str(raw)[:4000]}
