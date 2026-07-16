"""Travel static engine — unified travel_engine_execution_v1 by default."""

from __future__ import annotations

import os
from typing import Any

from .classifier import classify_travel_archetype
from .types import EngineResult


def _legacy_slice_enabled() -> bool:
    return (os.environ.get("ASK_TRAVEL_ENGINE") or "1").strip() == "0"


def _legacy_archetype_engines_enabled() -> bool:
    return (os.environ.get("ASK_TRAVEL_LEGACY_ARCHETYPE_ENGINES") or "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _resolve_travel_archetype_label(question: str, archetype: str | None) -> str:
    archetype = (archetype or "").strip().lower()
    if not archetype:
        archetype = classify_travel_archetype(question)
    return archetype or "general_travel"


def _attach_travel_engine_execution(
    result: EngineResult,
    kundli: dict,
    *,
    question: str = "",
    llm_intent: dict | None = None,
) -> EngineResult:
    try:
        from travel_static.travel_facts import compute_travel_engine_execution

        pack = compute_travel_engine_execution(
            kundli if isinstance(kundli, dict) else {},
            question=question or "",
            routing_label=result.archetype or "",
            llm_intent=llm_intent,
        )
        checks = dict(result.checks or {})
        checks["travel_engine_execution"] = pack
        checks["d1_travel_facts"] = pack.get("d1") or {}
        checks["d9_travel_facts"] = pack.get("d9") or {}
        checks["engine_version"] = "travel_engine_execution_v1"
        checks["unified_execution"] = True
        checks["routing_label"] = result.archetype
        if pack.get("composite_score") is not None:
            checks["travel_score"] = pack.get("composite_score")
        result.checks = checks
    except Exception as exc:
        checks = dict(result.checks or {})
        checks["travel_engine_execution_error"] = str(exc)[:180]
        result.checks = checks
    return result


def _run_legacy_archetype_engines(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str,
) -> EngineResult:
    from .engines.travel_engines import (
        run_business_travel,
        run_foreign_settlement,
        run_general_travel,
        run_immigration,
        run_passport_travel,
        run_pilgrimage_travel,
        run_relocation_abroad,
        run_return_india,
        run_short_travel,
        run_travel_obstacles,
        run_travel_risk,
        run_travel_country_fit,
        run_travel_yog,
        run_visa_theme,
    )

    dispatch = {
        "travel_yog": run_travel_yog,
        "foreign_settlement": run_foreign_settlement,
        "visa_theme": run_visa_theme,
        "relocation_abroad": run_relocation_abroad,
        "return_india": run_return_india,
        "travel_obstacles": run_travel_obstacles,
        "short_travel": run_short_travel,
        "pilgrimage_travel": run_pilgrimage_travel,
        "passport_travel": run_passport_travel,
        "immigration": run_immigration,
        "business_travel": run_business_travel,
        "travel_risk": run_travel_risk,
        "travel_country_fit": run_travel_country_fit,
        "general_travel": run_general_travel,
    }
    runner = dispatch.get(archetype, run_general_travel)
    return runner(kundli, question, wants_explain=wants_explain)


def run_travel_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
    llm_intent: dict | None = None,
) -> EngineResult:
    """Travel static — unified travel_engine_execution_v1 by default.

    Archetype is a routing label. Set ASK_TRAVEL_LEGACY_ARCHETYPE_ENGINES=1
    to restore per-archetype string-evidence engines (EE pack still attached).
    """
    if _legacy_slice_enabled():
        raise RuntimeError("ASK_TRAVEL_ENGINE=0 — caller should use legacy travel path")

    label = _resolve_travel_archetype_label(question, archetype)

    if _legacy_archetype_engines_enabled():
        result = _run_legacy_archetype_engines(
            kundli, question, wants_explain=wants_explain, archetype=label,
        )
        return _attach_travel_engine_execution(
            result, kundli, question=question or "", llm_intent=llm_intent,
        )

    dims_hint = ""
    try:
        from travel_static.travel_facts import compute_travel_facts

        facts = compute_travel_facts(kundli if isinstance(kundli, dict) else {})
        dims = facts.get("dimensions") or {}
        bits = []
        for k in ("foreign_travel", "settlement", "visa_luck", "short_travel", "travel_risk"):
            row = dims.get(k) if isinstance(dims, dict) else None
            if isinstance(row, dict) and row.get("verdict"):
                bits.append(f"{k}={row.get('verdict')}")
        if bits:
            dims_hint = "; ".join(bits)
        if facts.get("strength_label"):
            dims_hint = (dims_hint + " | " if dims_hint else "") + str(facts["strength_label"])
    except Exception:
        pass

    result = EngineResult(
        archetype=label,
        verdict=dims_hint or "",
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan=(
            "Read TRAVEL_ENGINE_EXECUTION_JSON (D1 + D9). "
            f"routing_label={label} is the answer focus only — answer the user's exact "
            "travel/abroad/visa question in warm Hinglish using pack facts, not invented placements. "
            "No guaranteed visa, no fixed country name, no exact travel date unless dasha_timing_compact."
        ),
        summary=[
            "Unified travel pack: D1 + D9 foreign axes (3H/9H/12H / Rahu / Jupiter).",
            f"Routing label (focus): {label}",
        ],
        evidence=[],
        ignore=["timing", "exact date", "guaranteed visa", "exact country name"],
        checks={
            "slice_type": "travel_engine_v1",
            "archetype": label,
            "routing_label": label,
            "unified_execution": True,
        },
    )
    return _attach_travel_engine_execution(
        result, kundli, question=question or "", llm_intent=llm_intent,
    )


def travel_engine_slice_meta(result: EngineResult) -> dict[str, Any]:
    pos, neg, neu = result._finalize_evidence_split()
    checks = dict(result.checks or {})
    return {
        "slice": "travel_engine_v1",
        "topic": "travel",
        "archetype": result.archetype,
        "verdict": result.verdict,
        "summary": list(result.summary or []),
        "evidence": list(result.evidence or []),
        "evidence_positive": pos,
        "evidence_negative": neg,
        "evidence_neutral": neu,
        "ignore": list(result.ignore or []),
        "checks": checks,
        "skip_llm": bool(result.skip_llm),
        "word_budget": int(result.word_budget or 75),
        "narrator_mode": "engine_facts_only",
    }
