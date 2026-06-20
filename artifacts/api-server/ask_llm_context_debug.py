"""Admin-only debug payload — what chart/context was sent to the Ask LLM."""

from __future__ import annotations

import json
import os
from typing import Any

_MAX_DB_CHARS = 80_000

_ANSWER_PATH_LABELS = {
    "engine_only": "Engine only (no LLM)",
    "engine_then_llm": "Engine → LLM",
    "direct_llm": "Direct LLM (no engine facts)",
    "unknown": "Unknown path",
}


def derive_answer_path(
    *,
    llm_called: bool,
    skip_reason: str = "",
    checks: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (code, human label) for admin: how the user answer was produced."""
    checks = checks or {}
    slice_meta = slice_meta or {}
    skip = (skip_reason or "").strip().lower()

    slice_type = str(checks.get("slice_type") or "")
    has_verdict = bool(slice_meta.get("verdict"))
    has_evidence = bool(slice_meta.get("evidence"))
    mr_v1 = (
        slice_meta.get("slice") == "mr_engine_v1"
        or checks.get("mr_engine") == "v1"
        or slice_type == "mr_engine_v1"
    )
    mr_static = bool(checks.get("is_mr_static"))
    marriage_engine = bool(checks.get("is_marriage_engine"))
    timing_engine = slice_type == "timing_marriage_engine"
    legacy_slice = slice_type in ("marriage_relationship",) or bool(
        slice_meta.get("slice") and slice_meta.get("slice") != "mr_engine_v1"
    )
    has_engine_facts = (
        has_verdict
        or has_evidence
        or mr_v1
        or mr_static
        or marriage_engine
        or timing_engine
        or legacy_slice
    )

    if not llm_called:
        if skip in ("mr_engine_template", "marriage_timing_deterministic") or checks.get("skip_llm"):
            return "engine_only", _ANSWER_PATH_LABELS["engine_only"]
        if has_engine_facts:
            return "engine_only", _ANSWER_PATH_LABELS["engine_only"]
        return "unknown", _ANSWER_PATH_LABELS["unknown"]

    if has_engine_facts and (mr_v1 or mr_static or marriage_engine or timing_engine or legacy_slice):
        return "engine_then_llm", _ANSWER_PATH_LABELS["engine_then_llm"]
    if has_verdict or has_evidence:
        return "engine_then_llm", _ANSWER_PATH_LABELS["engine_then_llm"]
    return "direct_llm", _ANSWER_PATH_LABELS["direct_llm"]


def build_engine_facts_snapshot(
    *,
    checks: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured engine facts the LLM was told to use (admin-only)."""
    checks = checks or {}
    slice_meta = slice_meta or {}
    nested = slice_meta.get("checks") if isinstance(slice_meta.get("checks"), dict) else {}
    return {
        "archetype": slice_meta.get("archetype") or checks.get("archetype"),
        "verdict": slice_meta.get("verdict"),
        "summary": list(slice_meta.get("summary") or []),
        "evidence": list(slice_meta.get("evidence") or []),
        "ignore": list(slice_meta.get("ignore") or []),
        "love_score": nested.get("love_score"),
        "arrange_score": nested.get("arrange_score"),
        "verdict_public": nested.get("verdict_public"),
        "confidence_ratio": nested.get("confidence_ratio"),
    }


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
    _checks = checks or {}
    _slice_meta = slice_meta or {}
    answer_path, answer_path_label = derive_answer_path(
        llm_called=llm_called,
        skip_reason=skip_reason,
        checks=_checks,
        slice_meta=_slice_meta,
    )
    engine_facts = build_engine_facts_snapshot(checks=_checks, slice_meta=_slice_meta)
    return {
        "version": 1,
        "route": route,
        "question": (question or "")[:500],
        "question_type": question_type,
        "is_timing": bool(is_timing),
        "llm_called": bool(llm_called),
        "answer_path": answer_path,
        "answer_path_label": answer_path_label,
        "engine_facts": engine_facts,
        "skip_reason": (skip_reason or "")[:200] or None,
        "checks": _checks,
        "slice_meta": _slice_meta,
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
