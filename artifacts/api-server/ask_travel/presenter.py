"""Travel → LLM payload: full Engine Execution + QUESTION_PRIORITY_FACTS."""

from __future__ import annotations

import json

from ask_mr.types import EngineResult

TRAVEL_ENGINE_EXECUTION_JSON_LABEL = "TRAVEL_ENGINE_EXECUTION_JSON:"
QUESTION_PRIORITY_FACTS_LABEL = "QUESTION_PRIORITY_FACTS:"


def to_travel_llm_payload(result: EngineResult, *, question: str = "") -> str:
    checks = dict(result.checks or {})
    execution = checks.get("travel_engine_execution") or {}
    label = (
        str(checks.get("routing_label") or result.archetype or "").strip().lower()
        or str(execution.get("routing_label") or "").strip().lower()
    )
    payload = {
        "question": (question or "").strip(),
        "routing_label": label,
        "schema_version": execution.get("schema_version") or "travel_engine_execution_v1",
        "d1": execution.get("d1") or checks.get("d1_travel_facts") or {},
        "d9": execution.get("d9") or checks.get("d9_travel_facts") or {},
        "lagnesh": execution.get("lagnesh") or {},
        "vargottama_planets": execution.get("vargottama_planets") or [],
        "dimensions": execution.get("dimensions") or {},
        "travel_yogas": execution.get("travel_yogas") or [],
        "sub_flags": execution.get("sub_flags") or {},
        "afflictions": execution.get("afflictions") or [],
        "composite_score": execution.get("composite_score"),
        "strength_label": execution.get("strength_label"),
    }
    dasha = execution.get("dasha_timing_compact") if isinstance(execution, dict) else None
    if isinstance(dasha, dict) and (dasha.get("current") or dasha.get("top_windows")):
        payload["dasha_timing_compact"] = dasha
    parts = [
        TRAVEL_ENGINE_EXECUTION_JSON_LABEL + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        from ask_travel.selected_blocks import build_travel_selected_blocks

        selected = build_travel_selected_blocks(
            question or "",
            "",
            meta={"checks": checks, "routing_label": label, "archetype": label},
            execution=execution if isinstance(execution, dict) else None,
        )
        priority = str(selected.get("priority_facts_for_llm") or "").strip()
        if priority or selected.get("expected_blocks"):
            if priority:
                parts.append(priority)
            checks["travel_selected_blocks_preview"] = {
                "focus": selected.get("focus"),
                "focus_label": selected.get("focus_label"),
                "expected_blocks": (selected.get("expected_blocks") or [])[:8],
                "priority_facts_for_llm": priority,
                "source": "travel_engine_execution",
                "selection_fallback": selected.get("selection_fallback"),
            }
            result.checks = checks
    except Exception:
        pass

    parts.append(
        "NARRATOR_LOCK: Use ONLY TRAVEL_ENGINE_EXECUTION_JSON for chart facts. "
        f"routing_label={label} = answer focus — not a separate engine. "
        "Cite #1 from QUESTION_PRIORITY_FACTS as natural chart proof when answering. "
        "Do not invent placements, signs, houses, guaranteed visa, fixed country, or dates."
    )
    if result.verdict:
        parts.append(f"VERDICT_HINT: {result.verdict}")
    if result.answer_plan:
        parts.append(f"ANSWER_PLAN: {result.answer_plan}")
    return "\n\n".join(parts)
