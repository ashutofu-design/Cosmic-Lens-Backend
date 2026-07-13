"""Health → LLM payload: full Engine Execution + ranked question-priority facts."""

from __future__ import annotations

import json

from ask_mr.types import EngineResult

HEALTH_ENGINE_EXECUTION_JSON_LABEL = "HEALTH_ENGINE_EXECUTION_JSON:"
QUESTION_PRIORITY_FACTS_LABEL = "QUESTION_PRIORITY_FACTS:"


def to_health_llm_payload(result: EngineResult, *, question: str = "") -> str:
    """Full D1/D9 Engine Execution + compact ranked facts (+ timing dasha if any)."""
    checks = dict(result.checks or {})
    execution = checks.get("health_engine_execution") or {}
    payload = {
        "question": (question or "").strip(),
        "d1": execution.get("d1") or checks.get("d1_health_facts") or {},
        "d9": execution.get("d9") or checks.get("d9_health_facts") or {},
    }
    dasha = execution.get("dasha_timing_compact") if isinstance(execution, dict) else None
    if isinstance(dasha, dict) and (dasha.get("current") or dasha.get("top_windows")):
        payload["dasha_timing_compact"] = dasha
    parts = [
        HEALTH_ENGINE_EXECUTION_JSON_LABEL + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    ]
    try:
        from ask_health.selected_blocks import build_health_selected_blocks

        selected = build_health_selected_blocks(
            question or "",
            "",
            meta={"checks": checks},
            execution=execution if isinstance(execution, dict) else None,
        )
        priority = str(selected.get("priority_facts_for_llm") or "").strip()
        if priority:
            parts.append(priority)
            # Keep for admin audit when narrator runs
            checks["health_selected_blocks_preview"] = {
                "focus": selected.get("focus"),
                "focus_label": selected.get("focus_label"),
                "expected_blocks": (selected.get("expected_blocks") or [])[:8],
                "priority_facts_for_llm": priority,
                "source": "health_engine_execution",
            }
            result.checks = checks
    except Exception:
        pass
    return "\n\n".join(parts)
