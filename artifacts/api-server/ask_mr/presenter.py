"""Relationship → LLM payload: full Engine Execution (D1 + D9) + routing label."""

from __future__ import annotations

import json

from ask_mr.types import EngineResult

RELATIONSHIP_ENGINE_EXECUTION_JSON_LABEL = "RELATIONSHIP_ENGINE_EXECUTION_JSON:"


def to_relationship_llm_payload(result: EngineResult, *, question: str = "") -> str:
    """Full D1/D9 Relationship Engine Execution for narrator + admin."""
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
    parts = [
        RELATIONSHIP_ENGINE_EXECUTION_JSON_LABEL + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        (
            "NARRATOR_LOCK: Use ONLY RELATIONSHIP_ENGINE_EXECUTION_JSON for chart facts. "
            f"routing_label={label} = answer focus (loyalty vs commitment etc.) — not a separate engine. "
            "Do not invent placements, signs, houses, or dates."
        ),
    ]
    if result.verdict:
        parts.append(f"VERDICT_HINT: {result.verdict}")
    if result.answer_plan:
        parts.append(f"ANSWER_PLAN: {result.answer_plan}")
    return "\n\n".join(parts)
