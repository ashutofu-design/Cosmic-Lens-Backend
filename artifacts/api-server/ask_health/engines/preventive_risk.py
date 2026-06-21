from __future__ import annotations

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim,
    dim_evidence,
    load_facts,
    lord_evidence,
)


def run_preventive_risk(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "preventive_risk")
    v = d.get("verdict", "")

    if v == "GREEN":
        verdict = "Preventive risk zones relatively light — routine lifestyle + checkups enough"
        confidence = "high"
    elif v == "YELLOW":
        verdict = "Preventive risk mixed — kuch vulnerability zones monitor karni chahiye"
        confidence = "medium"
    else:
        verdict = "Preventive risk high tone — screenings + habits pe active focus wise"
        confidence = "medium"

    evidence = [
        dim_evidence(facts, "preventive_risk", "Preventive zones"),
        lord_evidence(facts, "h6", "6th (disease house)"),
        lord_evidence(facts, "h8", "8th (chronic)"),
        lord_evidence(facts, "h12", "12th (loss/hospital)"),
        dim_evidence(facts, "overall_vitality", "Base vitality"),
    ]
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="preventive_risk",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Future risk/tendency zones — NOT illness date.",
        summary=["Prevention focus.", "No diagnosis names."],
        evidence=evidence[:8],
        ignore=["timing", "disease names"],
        checks={"slice_type": "health_engine_v1", "archetype": "preventive_risk", "prevent_v": v},
    )
