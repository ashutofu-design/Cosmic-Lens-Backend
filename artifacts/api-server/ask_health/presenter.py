"""Health engine → LLM payload with complete verified D1 facts."""

from __future__ import annotations

import json

from ask_mr.types import EngineResult


def to_health_llm_payload(result: EngineResult, *, question: str = "") -> str:
    """One stable payload for every health question; the LLM chooses answer depth."""
    checks = dict(result.checks or {})
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
        "health_engine_execution": checks.get("health_engine_execution") or {},
        "d1_health_facts": checks.get("d1_health_facts") or {},
        "d9_health_facts": checks.get("d9_health_facts") or {},
    }
    return (
        "VERIFIED_HEALTH_CONTEXT_JSON:\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
