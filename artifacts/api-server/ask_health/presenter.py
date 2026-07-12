"""Health engine → LLM payload with full health_engine_execution JSON."""

from __future__ import annotations

import json

from ask_mr.types import EngineResult

HEALTH_ENGINE_EXECUTION_JSON_LABEL = "HEALTH_ENGINE_EXECUTION_JSON:"


def to_health_llm_payload(result: EngineResult, *, question: str = "") -> str:
    """Full engine execution pack for every health question — same data as admin debugger."""
    checks = dict(result.checks or {})
    execution = checks.get("health_engine_execution") or {}
    if not execution:
        execution = {
            "schema_version": "health_engine_execution_v1",
            "d1": checks.get("d1_health_facts") or {},
            "d9": checks.get("d9_health_facts") or {},
        }
    payload = {
        "question": (question or "").strip(),
        "engine": {
            "archetype": result.archetype,
            "verdict": result.verdict,
            "confidence": result.confidence,
            "summary": list(result.summary or []),
            "evidence": list(result.evidence or []),
            "evidence_positive": list(result.evidence_positive or []),
            "evidence_negative": list(result.evidence_negative or []),
            "answer_plan": result.answer_plan,
            "do_not_claim": list(result.ignore or []),
        },
        "health_engine_execution": execution,
    }
    return (
        HEALTH_ENGINE_EXECUTION_JSON_LABEL + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
