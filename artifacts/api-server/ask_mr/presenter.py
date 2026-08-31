"""Relationship → LLM payload: full Engine Execution + QUESTION_PRIORITY_FACTS (health-style)."""

from __future__ import annotations

import json

from ask_mr.types import EngineResult

RELATIONSHIP_ENGINE_EXECUTION_JSON_LABEL = "RELATIONSHIP_ENGINE_EXECUTION_JSON:"
QUESTION_PRIORITY_FACTS_LABEL = "QUESTION_PRIORITY_FACTS:"


def to_relationship_llm_payload(result: EngineResult, *, question: str = "") -> str:
    """Full D1/D9 Relationship Engine Execution + ranked priority facts for narrator."""
    checks = dict(result.checks or {})
    execution = checks.get("relationship_engine_execution") or {}
    label = (
        str(checks.get("routing_label") or result.archetype or "").strip().lower()
        or str(execution.get("routing_label") or "").strip().lower()
    )
    payload = {
        "question": (question or "").strip(),
        "routing_label": label,
        "schema_version": execution.get("schema_version") or "relationship_engine_execution_v1",
        "d1": execution.get("d1") or checks.get("d1_relationship_facts") or {},
        "d9": execution.get("d9") or checks.get("d9_relationship_facts") or {},
        "lagnesh": execution.get("lagnesh") or {},
        "vargottama_planets": execution.get("vargottama_planets") or [],
        "manglik": execution.get("manglik") or {},
        "relationship_signals": execution.get("relationship_signals") or {},
    }
    dasha = execution.get("dasha_timing_compact") if isinstance(execution, dict) else None
    if isinstance(dasha, dict) and (dasha.get("current") or dasha.get("top_windows")):
        payload["dasha_timing_compact"] = dasha
    parts = [
        RELATIONSHIP_ENGINE_EXECUTION_JSON_LABEL + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        from ask_mr.selected_blocks import build_relationship_selected_blocks

        selected = build_relationship_selected_blocks(
            question or "",
            "",
            meta={"checks": checks, "routing_label": label, "archetype": label},
            execution=execution if isinstance(execution, dict) else None,
        )
        priority = str(selected.get("priority_facts_for_llm") or "").strip()
        if priority or selected.get("expected_blocks"):
            if priority:
                parts.append(priority)
            checks["relationship_selected_blocks_preview"] = {
                "focus": selected.get("focus"),
                "focus_label": selected.get("focus_label"),
                "expected_blocks": (selected.get("expected_blocks") or [])[:8],
                "priority_facts_for_llm": priority,
                "source": "relationship_engine_execution",
                "selection_fallback": selected.get("selection_fallback"),
            }
            result.checks = checks
    except Exception:
        pass

    parts.append(
        "NARRATOR_LOCK: Use ONLY RELATIONSHIP_ENGINE_EXECUTION_JSON for chart facts. "
        f"routing_label={label} = answer focus — not a separate engine. "
        "Cite #1 from QUESTION_PRIORITY_FACTS as natural chart proof when answering. "
        "Do not invent placements, signs, houses, or dates."
    )
    if result.verdict:
        parts.append(f"VERDICT_HINT: {result.verdict}")
    if result.answer_plan:
        parts.append(f"ANSWER_PLAN: {result.answer_plan}")
    return "\n\n".join(parts)
