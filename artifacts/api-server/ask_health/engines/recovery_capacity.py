from __future__ import annotations

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim,
    dim_evidence,
    karaka_evidence,
    load_facts,
    lord_evidence,
)


def run_recovery_capacity(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "recovery_capacity")
    v = d.get("verdict", "")

    if v == "GREEN":
        verdict = "Recovery capacity strong — rest + doctor plan se body respond karna achha rehta hai"
        confidence = "high"
    elif v == "YELLOW":
        verdict = "Recovery capacity average — patience aur treatment follow-through important"
        confidence = "medium"
    else:
        verdict = "Recovery capacity weak tone — slow healing tendency, medical follow-up zaroori"
        confidence = "medium"

    evidence = [
        dim_evidence(facts, "recovery_capacity", "Recovery resistance"),
        lord_evidence(facts, "h6", "6th lord (healing)"),
        karaka_evidence(facts, "Jupiter", "Healing support"),
        karaka_evidence(facts, "Mercury", "Recovery karaka"),
        dim_evidence(facts, "overall_vitality", "Base vitality"),
    ]
    evidence.extend(affliction_lines(facts, limit=1))

    return EngineResult(
        archetype="recovery_capacity",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Recovery CAPACITY — NO recovery date. Doctor compliance primary.",
        summary=["No cure guarantee.", "No recovery date."],
        evidence=evidence[:8],
        ignore=["recovery date", "timing", "cure guarantee"],
        checks={"slice_type": "health_engine_v1", "archetype": "recovery_capacity", "recovery_v": v},
    )
