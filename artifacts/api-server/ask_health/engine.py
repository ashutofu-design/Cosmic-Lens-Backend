from __future__ import annotations

import os

from .classifier import classify_health_archetype
from .types import EngineResult

_HARD_GUARD_ARCHETYPES = frozenset({
    "refuse_diagnosis",
    "refuse_death",
    "refuse_cure_guarantee",
    "refuse_timing_decline",
    "refuse_timing_recovery",
    "refuse_surgery_muhurat",
    "crisis_redirect",
})


def _attach_health_engine_execution(result: EngineResult, kundli: dict) -> EngineResult:
    """Persist fixed D1 + D9 health chart pack for LLM + admin Engine Execution."""
    try:
        from health_static.health_facts import compute_health_engine_execution

        pack = compute_health_engine_execution(kundli if isinstance(kundli, dict) else {})
        checks = dict(result.checks or {})
        checks["health_engine_execution"] = pack
        checks["d1_health_facts"] = pack.get("d1") or {}
        checks["d9_health_facts"] = pack.get("d9") or {}
        checks["engine_version"] = "health_engine_execution_v1"
        result.checks = checks
    except Exception as exc:
        checks = dict(result.checks or {})
        checks["health_engine_execution_error"] = str(exc)[:180]
        result.checks = checks
    return result


def run_health_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_HEALTH_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_HEALTH_ENGINE=0 — caller should use legacy health path")

    archetype = (archetype or "").strip().lower() or classify_health_archetype(question)

    if archetype in _HARD_GUARD_ARCHETYPES:
        from .engines.hard_guard import run_hard_guard

        return run_hard_guard(kundli, question, archetype=archetype, wants_explain=wants_explain)

    result = EngineResult(
        archetype=archetype,
        verdict="",
        confidence="medium",
        word_budget=75 if not wants_explain else 120,
        answer_plan=(
            "Read D1 and D9 health chart JSON. Answer the user's exact health question in natural "
            "Hinglish/English — chart tendency from JSON, not medical diagnosis. "
            "If user named a condition, address that angle with chart evidence + doctor disclaimer."
        ),
        summary=[],
        evidence=[],
        ignore=["exact death date", "suicide/self-harm encouragement"],
        checks={
            "slice_type": "health_engine_v1",
            "archetype": archetype,
        },
    )
    return _attach_health_engine_execution(result, kundli)
