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


_SYSTEM_ARCHETYPES = frozenset({
    "digestive_health",
    "cardio_health",
    "nervous_health",
    "musculoskeletal_health",
    "skin_health",
    "endocrine_health",
    "respiratory_health",
    "immune_health",
})


def _attach_health_engine_execution(result: EngineResult, kundli: dict) -> EngineResult:
    """Persist fixed D1 + D9 health chart pack for LLM + admin debugger."""
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


_attach_d1_health_facts = _attach_health_engine_execution


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
        result = run_hard_guard(kundli, question, archetype=archetype, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "overall_vitality":
        from .engines.overall_vitality import run_overall_vitality
        result = run_overall_vitality(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "chronic_tendency":
        from .engines.chronic_tendency import run_chronic_tendency
        result = run_chronic_tendency(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "mental_stress":
        from .engines.mental_stress import run_mental_stress
        result = run_mental_stress(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "surgery_risk_tone":
        from .engines.surgery_risk_tone import run_surgery_risk_tone
        result = run_surgery_risk_tone(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "preventive_risk":
        from .engines.preventive_risk import run_preventive_risk
        result = run_preventive_risk(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "recovery_capacity":
        from .engines.recovery_capacity import run_recovery_capacity
        result = run_recovery_capacity(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "accident_risk":
        from .engines.accident_risk import run_accident_risk
        result = run_accident_risk(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "parent_health":
        from .engines.parent_health import run_parent_health
        result = run_parent_health(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "addiction_support":
        from .engines.addiction_support import run_addiction_support
        result = run_addiction_support(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "reproductive_support":
        from .engines.reproductive_support import run_reproductive_support
        result = run_reproductive_support(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype == "heart_blood_pressure":
        from .engines.heart_blood_pressure import run_heart_blood_pressure
        result = run_heart_blood_pressure(kundli, question, wants_explain=wants_explain)
        return _attach_d1_health_facts(result, kundli)
    if archetype in _SYSTEM_ARCHETYPES:
        from .engines.system_health import run_system_health
        result = run_system_health(
            kundli, question, archetype=archetype, wants_explain=wants_explain
        )
        return _attach_d1_health_facts(result, kundli)

    from .engines.general_health import run_general_health
    result = run_general_health(kundli, question, wants_explain=wants_explain)
    return _attach_d1_health_facts(result, kundli)
