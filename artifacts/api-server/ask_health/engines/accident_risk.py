from __future__ import annotations

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim_evidence,
    karaka_evidence,
    load_facts,
    lord_evidence,
)


def run_accident_risk(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    sr = (facts.get("dimensions") or {}).get("surgery_risk_tone") or {}
    pr = (facts.get("dimensions") or {}).get("preventive_risk") or {}
    v = sr.get("verdict") or pr.get("verdict") or "YELLOW"

    if v == "GREEN":
        verdict = "Accident/injury caution tone low — normal safety habits enough"
        confidence = "high"
    elif v == "YELLOW":
        verdict = "Accident caution tone moderate — rash driving / risky sports me extra dhyaan"
        confidence = "medium"
    else:
        verdict = "Accident caution tone elevated — Mars/8H pressure; safety discipline important"
        confidence = "medium"

    evidence = [
        karaka_evidence(facts, "Mars", "Mars (sudden/injury)"),
        lord_evidence(facts, "h8", "8th (sudden disruption)"),
        karaka_evidence(facts, "Ketu", "Ketu (sudden hit)"),
        dim_evidence(facts, "preventive_risk", "Risk zones"),
        dim_evidence(facts, "surgery_risk_tone", "Invasive caution"),
    ]
    evidence.extend(affliction_lines(facts, limit=1))

    return EngineResult(
        archetype="accident_risk",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Caution-window tendency — NEVER predict accident event.",
        summary=["No event prediction.", "Safety habits primary."],
        evidence=evidence[:8],
        ignore=["timing", "accident date", "event guarantee"],
        checks={"slice_type": "health_engine_v1", "archetype": "accident_risk"},
    )
