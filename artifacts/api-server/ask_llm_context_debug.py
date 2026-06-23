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
    sl = str(slice_meta.get("slice") or "")
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
    domain_engine_slice = sl in (
        "mr_engine_v1",
        "career_engine_v1",
        "education_engine_v1",
        "children_engine_v1",
        "property_engine_v1",
        "travel_engine_v1",
        "litigation_engine_v1",
        "finance_engine_v1",
        "health_engine_v1",
    )
    has_engine_facts = (
        has_verdict
        or has_evidence
        or mr_v1
        or mr_static
        or marriage_engine
        or timing_engine
        or legacy_slice
        or domain_engine_slice
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


_MARRIAGE_TRACE_STEP_ORDER = (
    "step0",
    "step0a",
    "step1",
    "step2",
    "step3",
    "step4",
    "step5",
    "step6",
    "step7",
    "step8",
)


def _finalize_step7_transit(s7: dict[str, Any], trace: dict[str, Any]) -> None:
    try:
        from event_timing.marriage.marriage_engine_v2 import finalize_transit_display
    except Exception:
        return

    samples = s7.get("samples") if isinstance(s7.get("samples"), list) else []
    window = None
    wins = trace.get("top_3_windows") or []
    if wins and isinstance(wins[0], dict):
        window = wins[0]
        if not samples:
            samples = window.get("transit_samples") or []

    detail, months, by_month = finalize_transit_display(
        samples=samples,
        detail=str(s7.get("detail") or ""),
        months=s7.get("months") if isinstance(s7.get("months"), list) else None,
        window=window,
    )
    s7["detail"] = detail
    s7["months"] = months
    s7["by_month"] = by_month
    s7.pop("samples", None)


def normalize_engine_trace_transit_months(trace: dict[str, Any] | None) -> dict[str, Any] | None:
    """Rewrite step7 / timing_audit transit — month + Guru/Shani rashi."""
    if not isinstance(trace, dict):
        return trace
    try:
        from event_timing.marriage.marriage_engine_v2 import (
            finalize_transit_display,
            _monthify_verbose_transit_detail,
        )
    except Exception:
        return trace

    step_audit = trace.get("step_audit")
    if isinstance(step_audit, dict):
        s7 = step_audit.get("step7")
        if isinstance(s7, dict):
            _finalize_step7_transit(s7, trace)

    timing_audit = trace.get("timing_audit")
    if isinstance(timing_audit, dict):
        transit = timing_audit.get("transit")
        if isinstance(transit, dict):
            samples = transit.get("samples") if isinstance(transit.get("samples"), list) else []
            window = None
            wins = trace.get("top_3_windows") or []
            if wins and isinstance(wins[0], dict):
                window = wins[0]
            detail, months, by_month = finalize_transit_display(
                samples=samples,
                detail=str(transit.get("detail") or ""),
                months=transit.get("months") if isinstance(transit.get("months"), list) else None,
                window=window,
            )
            transit["detail"] = detail
            transit["months"] = months
            transit["by_month"] = by_month
            transit.pop("samples", None)

        for check in timing_audit.get("checks") or []:
            if not isinstance(check, dict):
                continue
            if check.get("name") == "transit_support" and isinstance(check.get("detail"), str):
                check["detail"] = _monthify_verbose_transit_detail(check["detail"])

    for win in trace.get("top_3_windows") or []:
        if isinstance(win, dict):
            d, m, b = finalize_transit_display(
                samples=win.get("transit_samples") or [],
                detail=str(win.get("dt_detail") or ""),
                months=win.get("transit_months") if isinstance(win.get("transit_months"), list) else None,
                window=win,
            )
            win["dt_detail"] = d
            win["transit_months"] = m
            win["transit_by_month"] = b
            win.pop("transit_samples", None)

    return trace


def build_marriage_engine_trace(engine_result: dict[str, Any] | None) -> dict[str, Any] | None:
    """Trimmed marriage M17 audit for admin panel (step-by-step pipeline)."""
    if not isinstance(engine_result, dict) or not engine_result:
        return None
    step_audit = engine_result.get("step_audit")
    if not isinstance(step_audit, dict):
        step_audit = {}
    timing_audit = engine_result.get("timing_audit")
    if not isinstance(timing_audit, dict):
        timing_audit = {}
    top_windows = engine_result.get("top_3_windows") or []
    if not isinstance(top_windows, list):
        top_windows = []
    factors = engine_result.get("factors") or []
    if not isinstance(factors, list):
        factors = []
    return normalize_engine_trace_transit_months({
        "engine": "marriage_timing_m17",
        "primary_window": engine_result.get("primary_window"),
        "backup_window": engine_result.get("backup_window"),
        "key_trigger": engine_result.get("key_trigger"),
        "verdict": engine_result.get("verdict"),
        "band": engine_result.get("band"),
        "user_age": engine_result.get("user_age"),
        "too_young_for_marriage": engine_result.get("too_young_for_marriage"),
        "step_audit": step_audit,
        "step_order": list(_MARRIAGE_TRACE_STEP_ORDER),
        "timing_audit": timing_audit,
        "top_3_windows": top_windows[:3],
        "factors": factors[:50],
        "risk_flags": list(engine_result.get("risk_flags") or [])[:20],
    })


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
    intent_source: str = "regex",
    llm_intent: dict[str, Any] | None = None,
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
        "intent_source": intent_source or "regex",
        "llm_intent": llm_intent or None,
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
        if not isinstance(data, dict):
            return None
        blocks = data.get("blocks")
        if isinstance(blocks, dict):
            for key in ("engine_trace", "marriage_engine_trace"):
                tr = blocks.get(key)
                if isinstance(tr, dict):
                    blocks[key] = normalize_engine_trace_transit_months(tr)
        return data
    except Exception:
        return {"raw": str(raw)[:4000]}
