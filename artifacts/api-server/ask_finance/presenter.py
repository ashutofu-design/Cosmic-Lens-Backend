"""Finance → LLM payload: full Engine Execution + QUESTION_PRIORITY_FACTS."""

from __future__ import annotations

import json
from datetime import datetime

from ask_mr.types import EngineResult

FINANCE_ENGINE_EXECUTION_JSON_LABEL = "FINANCE_ENGINE_EXECUTION_JSON:"
QUESTION_PRIORITY_FACTS_LABEL = "QUESTION_PRIORITY_FACTS:"


def to_finance_llm_payload(result: EngineResult, *, question: str = "") -> str:
    checks = dict(result.checks or {})
    execution = checks.get("finance_engine_execution") or {}
    label = (
        str(checks.get("routing_label") or result.archetype or "").strip().lower()
        or str(execution.get("routing_label") or "").strip().lower()
    )
    payload = {
        "question": (question or "").strip(),
        "routing_label": label,
        "schema_version": execution.get("schema_version") or "finance_engine_execution_v1",
        "d1": execution.get("d1") or checks.get("d1_finance_facts") or {},
        "d9": execution.get("d9") or checks.get("d9_finance_facts") or {},
        "divisional_chart_tag": execution.get("divisional_chart_tag") or "D2",
        "divisional_chart": (
            execution.get("divisional_chart")
            or checks.get("finance_divisional_facts")
            or {}
        ),
        "charts_used": execution.get("charts_used") or checks.get("charts_used") or ["D1", "D9"],
        "lagnesh": execution.get("lagnesh") or {},
        "vargottama_planets": execution.get("vargottama_planets") or [],
        "dimensions": execution.get("dimensions") or {},
        "wealth_yogas": execution.get("wealth_yogas") or [],
        "sub_flags": execution.get("sub_flags") or {},
        "afflictions": execution.get("afflictions") or [],
    }
    dasha = execution.get("dasha_timing_compact") if isinstance(execution, dict) else None
    has_dasha = isinstance(dasha, dict) and (dasha.get("current") or dasha.get("top_windows"))
    if has_dasha:
        payload["dasha_timing_compact"] = dasha
    # Anchor "today" so the narrator never treats a past month as a future event.
    _today = datetime.utcnow()
    payload["today"] = _today.strftime("%d %b %Y")
    parts = [
        f"CURRENT_DATE: today is {_today.strftime('%d %b %Y')} "
        f"({_today.strftime('%B %Y')}). Any dasha/period date BEFORE today is "
        f"already PAST — never describe it as upcoming/future.",
        FINANCE_ENGINE_EXECUTION_JSON_LABEL + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        from ask_finance.selected_blocks import build_finance_selected_blocks

        selected = build_finance_selected_blocks(
            question or "",
            "",
            meta={"checks": checks, "routing_label": label, "archetype": label},
            execution=execution if isinstance(execution, dict) else None,
        )
        priority = str(selected.get("priority_facts_for_llm") or "").strip()
        if priority or selected.get("expected_blocks"):
            if priority:
                parts.append(priority)
            checks["finance_selected_blocks_preview"] = {
                "focus": selected.get("focus"),
                "focus_label": selected.get("focus_label"),
                "expected_blocks": (selected.get("expected_blocks") or [])[:8],
                "priority_facts_for_llm": priority,
                "source": "finance_engine_execution",
                "selection_fallback": selected.get("selection_fallback"),
            }
            result.checks = checks
    except Exception:
        pass

    _dasha_rule = ""
    if has_dasha:
        _dasha_rule = (
            " DASHA: cite dasha ONLY from dasha_timing_compact — 'current' is the "
            "MD/AD/PD running RIGHT NOW (today), 'top_windows' are upcoming. Never "
            "name a different current dasha and never call a past-dated window future."
        )
    else:
        _dasha_rule = (
            " DASHA: no dasha data provided — do NOT mention any mahadasha / "
            "antardasha / period dates at all; answer from placements only."
        )
    parts.append(
        "NARRATOR_LOCK: Use ONLY FINANCE_ENGINE_EXECUTION_JSON for chart facts. "
        f"routing_label={label} = answer focus — not a separate engine. "
        "Cite #1 from QUESTION_PRIORITY_FACTS as natural chart proof when answering. "
        "Do not invent placements, signs, houses, stock tips, or dates." + _dasha_rule
    )
    if result.verdict:
        parts.append(f"VERDICT_HINT: {result.verdict}")
    if result.answer_plan:
        parts.append(f"ANSWER_PLAN: {result.answer_plan}")
    return "\n\n".join(parts)
