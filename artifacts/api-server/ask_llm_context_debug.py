"""Admin-only debug payload — what chart/context was sent to the Ask LLM."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

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
    career_engine = bool(checks.get("is_career_engine"))
    timing_engine = slice_type in (
        "timing_marriage_engine",
        "timing_marriage_engine_alt",
        "timing_career_engine",
    )
    domain_engine_slice = sl in (
        "mr_engine_v1",
        "career_engine_v1",
        "career_timing_v1",
        "education_engine_v1",
        "children_engine_v1",
        "property_engine_v1",
        "travel_engine_v1",
        "litigation_engine_v1",
        "luck_engine_v1",
        "controlled_fallback_v1",
        "finance_engine_v1",
        "health_engine_v1",
        "travel_timing_v1",
        "finance_timing_v1",
        "health_timing_v1",
        "children_timing_v1",
        "love_timing_v1",
        "education_timing_v1",
        "property_timing_v1",
        "litigation_timing_v1",
        "vehicle_timing_v1",
        "vehicle_engine_v1",
    )
    dcr_love_buckets = sl == "marriage_relationship" and bool(slice_meta.get("buckets"))
    has_engine_facts = (
        has_verdict
        or has_evidence
        or domain_engine_slice
        or dcr_love_buckets
        or mr_v1
        or (mr_static and (has_verdict or has_evidence or domain_engine_slice))
        or (marriage_engine and (has_verdict or has_evidence or domain_engine_slice))
        or (career_engine and (has_verdict or has_evidence or domain_engine_slice))
        or timing_engine
    )

    if not llm_called:
        if skip in ("mr_engine_template", "marriage_timing_deterministic") or checks.get("skip_llm"):
            return "engine_only", _ANSWER_PATH_LABELS["engine_only"]
        if has_engine_facts:
            return "engine_only", _ANSWER_PATH_LABELS["engine_only"]
        return "unknown", _ANSWER_PATH_LABELS["unknown"]

    if has_engine_facts and (
        mr_v1
        or (mr_static and (has_verdict or has_evidence or domain_engine_slice))
        or (marriage_engine and (has_verdict or has_evidence or domain_engine_slice))
        or (career_engine and (has_verdict or has_evidence or domain_engine_slice))
        or timing_engine
        or dcr_love_buckets
    ):
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


def _transit_ctx_from_trace(trace: dict[str, Any], s7: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    ctx = trace.get("transit_chart_context")
    if isinstance(ctx, dict) and ctx.get("h7_si") is not None:
        return ctx
    try:
        from event_timing.marriage.marriage_engine_v2 import transit_ctx_from_public_chart
    except Exception:
        return None
    if s7 is None:
        step_audit = trace.get("step_audit")
        if isinstance(step_audit, dict):
            s7 = step_audit.get("step7")
    if isinstance(s7, dict):
        rebuilt = transit_ctx_from_public_chart(s7.get("chart_context"))
        if rebuilt:
            return rebuilt
    return None


def _finalize_step7_transit(s7: dict[str, Any], trace: dict[str, Any]) -> None:
    try:
        from event_timing.marriage.marriage_engine_v2 import _build_step7_transit_package
    except Exception:
        return

    window: dict[str, Any] = {}
    wins = trace.get("top_3_windows") or []
    if wins and isinstance(wins[0], dict):
        window = dict(wins[0])
    window.setdefault("transit_confirmed", s7.get("transit_confirmed"))
    window.setdefault("jup", s7.get("jupiter_hit", s7.get("jup")))
    window.setdefault("sat", s7.get("saturn_hit", s7.get("sat")))
    window.setdefault("dt", s7.get("double_transit", s7.get("dt")))
    if s7.get("detail") and not window.get("dt_detail"):
        window["dt_detail"] = s7.get("detail")

    pkg = _build_step7_transit_package(
        window, _transit_ctx_from_trace(trace, s7),
    )
    s7["detail"] = pkg.get("detail")
    s7["months"] = pkg.get("months")
    s7["by_month"] = pkg.get("by_month")
    s7["transit_type"] = pkg.get("transit_type")
    s7["transit_type_label"] = pkg.get("transit_type_label")
    s7["chart_context"] = pkg.get("chart_context")
    s7["jupiter_hit"] = pkg.get("jupiter_hit")
    s7["saturn_hit"] = pkg.get("saturn_hit")
    s7["double_transit"] = pkg.get("double_transit")
    s7.pop("samples", None)


def normalize_engine_trace_transit_months(trace: dict[str, Any] | None) -> dict[str, Any] | None:
    """Rewrite step7 / timing_audit transit — month + Guru/Shani rashi."""
    if not isinstance(trace, dict):
        return trace
    try:
        from event_timing.marriage.marriage_engine_v2 import (
            _build_step7_transit_package,
            _monthify_verbose_transit_detail,
        )
    except Exception:
        return trace

    transit_ctx = _transit_ctx_from_trace(trace)

    step_audit = trace.get("step_audit")
    if isinstance(step_audit, dict):
        s7 = step_audit.get("step7")
        if isinstance(s7, dict):
            _finalize_step7_transit(s7, trace)

    timing_audit = trace.get("timing_audit")
    if isinstance(timing_audit, dict):
        transit = timing_audit.get("transit")
        if isinstance(transit, dict):
            window = wins[0] if (wins := trace.get("top_3_windows") or []) and isinstance(wins[0], dict) else {}
            pkg = _build_step7_transit_package(window, transit_ctx)
            transit["detail"] = pkg.get("detail")
            transit["months"] = pkg.get("months")
            transit["by_month"] = pkg.get("by_month")
            transit["transit_type"] = pkg.get("transit_type")
            transit["transit_type_label"] = pkg.get("transit_type_label")
            transit["chart_context"] = pkg.get("chart_context")
            transit.pop("samples", None)

        for check in timing_audit.get("checks") or []:
            if not isinstance(check, dict):
                continue
            if check.get("name") == "transit_support" and isinstance(check.get("detail"), str):
                check["detail"] = _monthify_verbose_transit_detail(
                    check["detail"], transit_ctx,
                )

    for win in trace.get("top_3_windows") or []:
        if isinstance(win, dict):
            pkg = _build_step7_transit_package(win, transit_ctx)
            win["dt_detail"] = pkg.get("detail")
            win["transit_months"] = pkg.get("months")
            win["transit_by_month"] = pkg.get("by_month")
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
        "transit_chart_context": engine_result.get("transit_chart_context"),
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
    out = {
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
    if slice_meta.get("dasha_trace"):
        out["dasha_trace"] = slice_meta.get("dasha_trace")
    if slice_meta.get("timing_evidence"):
        out["timing_evidence"] = list(slice_meta.get("timing_evidence") or [])
    return out


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
    has_engine_facts = bool(
        engine_facts.get("verdict")
        or (engine_facts.get("evidence") or [])
        or (_slice_meta.get("verdict"))
        or (_slice_meta.get("evidence"))
    )
    try:
        from ask_intent_fidelity import (
            build_question_understanding_detail,
            build_question_understanding_line,
            resolve_question_understood,
        )

        question_understood = resolve_question_understood(
            question,
            llm_intent,
            skip_reason=skip_reason,
            intent_source=intent_source,
            has_engine_facts=has_engine_facts,
        )
        understanding_line = build_question_understanding_line(
            question,
            llm_intent,
            skip_reason=skip_reason,
            intent_source=intent_source,
            has_engine_facts=has_engine_facts,
            engine_archetype=str(_slice_meta.get("archetype") or engine_facts.get("archetype") or ""),
        )
        understanding_detail = build_question_understanding_detail(
            question,
            llm_intent,
            skip_reason=skip_reason,
            intent_source=intent_source,
            engine_archetype=str(_slice_meta.get("archetype") or engine_facts.get("archetype") or ""),
        )
    except Exception:
        question_understood = ""
        understanding_line = ""
        understanding_detail = ""
    return {
        "version": 1,
        "route": route,
        "question": (question or "")[:500],
        "question_type": question_type,
        "is_timing": bool(is_timing),
        "intent_source": intent_source or "regex",
        "question_understood": question_understood or None,
        "understanding_line": understanding_line,
        "understanding_detail": understanding_detail or None,
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
