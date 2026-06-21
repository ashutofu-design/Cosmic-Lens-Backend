from __future__ import annotations

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim,
    dim_evidence,
    karaka_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
)


def run_surgery_risk_tone(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "surgery_risk_tone")
    v = d.get("verdict", "")

    if v == "GREEN":
        verdict = "Surgery caution tone low — agar kabhi need ho to routine surgeon guidance enough"
        confidence = "high"
    elif v == "YELLOW":
        verdict = "Surgery caution tone moderate — second opinion + experienced surgeon choose karna wise"
        confidence = "medium"
    else:
        verdict = "Surgery caution tone high — Mars-Saturn/6-8 pressure; medical team choice bahut matter karta"
        confidence = "medium"

    evidence = [
        dim_evidence(facts, "surgery_risk_tone", "Surgical caution tone"),
        karaka_evidence(facts, "Mars", "Mars (procedure karaka)"),
        karaka_evidence(facts, "Saturn", "Saturn (restriction)"),
        lord_evidence(facts, "h6", "6th house (acute)"),
        lord_evidence(facts, "h8", "8th house (invasive)"),
    ]
    if sub_flag(facts, "surgery_caution"):
        evidence.append("Surgery-caution sub-flag active — extra medical diligence advised")
    evidence.extend(affliction_lines(facts, limit=1))

    return EngineResult(
        archetype="surgery_risk_tone",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Surgery RISK TONE only — NO muhurat/date. Surgeon decides.",
        summary=["Never skip surgeon advice.", "No operation date."],
        evidence=evidence[:8],
        ignore=["muhurat", "operation date", "timing"],
        checks={"slice_type": "health_engine_v1", "archetype": "surgery_risk_tone", "surgery_v": v},
    )
