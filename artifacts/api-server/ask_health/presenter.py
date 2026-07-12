"""Health engine → LLM payload with verified D1 + D9 chart context."""

from __future__ import annotations

import json

from ask_mr.types import EngineResult


def _slim_chart_for_llm(facts: dict) -> dict:
    if not isinstance(facts, dict):
        return {}
    if facts.get("error"):
        return {"chart": facts.get("chart"), "error": facts.get("error")}
    return {
        "chart": facts.get("chart"),
        "ascendant": facts.get("ascendant"),
        "lagnesh": facts.get("lagnesh"),
        "planets": facts.get("planets") or [],
        "houses": facts.get("houses") or [],
        "health_houses": facts.get("health_houses") or [],
        "house_lords": facts.get("house_lords") or {},
        "karakas": facts.get("karakas") or {},
        "aspects": facts.get("aspects") or [],
        "afflictions": facts.get("afflictions") or [],
        "vitality_score": facts.get("vitality_score"),
        "vitality_risk": facts.get("vitality_risk"),
        "dimensions": facts.get("dimensions") or {},
    }


def _slim_health_execution_for_llm(pack: dict) -> dict:
    if not isinstance(pack, dict):
        return {}
    return {
        "schema_version": pack.get("schema_version") or "health_engine_execution_v1",
        "d1": _slim_chart_for_llm(pack.get("d1") if isinstance(pack.get("d1"), dict) else {}),
        "d9": _slim_chart_for_llm(pack.get("d9") if isinstance(pack.get("d9"), dict) else {}),
        "lagnesh": pack.get("lagnesh") or {},
        "vargottama_planets": pack.get("vargottama_planets") or [],
        "vargottama_details": pack.get("vargottama_details") or [],
    }


def to_health_llm_payload(result: EngineResult, *, question: str = "") -> str:
    """Stable health payload for LLM — one D1+D9 block (admin keeps full checks separately)."""
    checks = dict(result.checks or {})
    raw_pack = checks.get("health_engine_execution") or {}
    if not raw_pack:
        raw_pack = {
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
        "health_chart_context": _slim_health_execution_for_llm(raw_pack),
    }
    return (
        "VERIFIED_HEALTH_CONTEXT_JSON:\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
