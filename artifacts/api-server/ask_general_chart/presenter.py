"""General chart → LLM payload."""

from __future__ import annotations

import json
from datetime import datetime

from ask_mr.types import EngineResult

GENERAL_CHART_JSON_LABEL = "GENERAL_CHART_ENGINE_EXECUTION_JSON:"


def to_general_chart_llm_payload(result: EngineResult, *, question: str = "") -> str:
    checks = dict(result.checks or {})
    execution = checks.get("general_chart_engine_execution") or {}
    _today = datetime.utcnow()
    payload = {
        "question": (question or "").strip(),
        "domain": "general",
        "mode": "llm_general_chart",
        "schema_version": execution.get("schema_version") or "general_chart_engine_execution_v1",
        "today": _today.strftime("%d %b %Y"),
        "d1": execution.get("d1") or {},
        "d9": execution.get("d9") or {},
        "dasha_timing_compact": execution.get("dasha_timing_compact") or {},
        "charts_used": execution.get("charts_used") or ["D1", "D9", "DASHA"],
    }
    parts = [
        f"CURRENT_DATE: today is {_today.strftime('%d %b %Y')} "
        f"({_today.strftime('%B %Y')}). Past dasha/period dates are PAST — never call them future.",
        "QUESTION_DNA_LOCK: Domain=general — no specialist engine. "
        "Answer from D1 + D9 + dasha only. Match user_wants / intent from Question DNA.",
        GENERAL_CHART_JSON_LABEL + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        from ask_general_chart.selected_blocks import build_general_selected_blocks

        selected = build_general_selected_blocks(
            question or "",
            "",
            meta={"checks": checks},
            execution=execution if isinstance(execution, dict) else None,
        )
        priority = str(selected.get("priority_facts_for_llm") or "").strip()
        if priority or selected.get("expected_blocks"):
            if priority:
                parts.append(priority)
            checks["general_selected_blocks_preview"] = {
                "focus": selected.get("focus"),
                "focus_label": selected.get("focus_label"),
                "expected_blocks": (selected.get("expected_blocks") or [])[:8],
                "priority_facts_for_llm": priority,
                "source": "general_chart_engine_execution",
                "selection_fallback": selected.get("selection_fallback"),
            }
            result.checks = checks
    except Exception:
        pass

    parts.append(
        "NARRATOR_LOCK: Use ONLY GENERAL_CHART_ENGINE_EXECUTION_JSON for chart facts. "
        "Cite #1 from QUESTION_PRIORITY_FACTS as natural chart proof. "
        "Do not invent placements, signs, houses, or dates. "
        "DASHA: cite only from dasha_timing_compact — current = running NOW."
    )
    if result.verdict:
        parts.append(f"VERDICT_HINT: {result.verdict}")
    if result.answer_plan:
        parts.append(f"ANSWER_PLAN: {result.answer_plan}")
    return "\n\n".join(parts)
