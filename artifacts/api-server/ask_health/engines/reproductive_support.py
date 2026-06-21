from __future__ import annotations

from ..types import EngineResult
from ._health_base import dim_evidence, karaka_evidence, load_facts, lord_evidence


def run_reproductive_support(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    ov = (facts.get("dimensions") or {}).get("overall_vitality") or {}
    v = ov.get("verdict") or "YELLOW"

    if v == "GREEN":
        verdict = "Reproductive-energy tone supported — fertility specialist consult still primary"
        confidence = "medium"
    else:
        verdict = "Reproductive axis mixed — specialist + lifestyle support dono matter karte hain"
        confidence = "medium"

    evidence = [
        "5th house (children) + 7th/8th cluster — reproductive energy from chart",
        karaka_evidence(facts, "Jupiter", "Jupiter (santaan karaka)"),
        karaka_evidence(facts, "Venus", "Venus (vitality)"),
        karaka_evidence(facts, "Mars", "Mars (procreation energy)"),
        dim_evidence(facts, "overall_vitality", "Base vitality"),
    ]

    return EngineResult(
        archetype="reproductive_support",
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan="Reproductive tendency — energetic framing, specialist primary.",
        summary=["Sensitive bucket.", "No medical diagnosis."],
        evidence=evidence[:6],
        ignore=["timing", "diagnosis", "guarantee pregnancy"],
        checks={"slice_type": "health_engine_v1", "archetype": "reproductive_support", "sensitive": "reproductive"},
    )
