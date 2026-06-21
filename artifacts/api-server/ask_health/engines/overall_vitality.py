from __future__ import annotations

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim,
    dim_evidence,
    karaka_evidence,
    load_facts,
    lord_evidence,
    vitality_line,
)


def run_overall_vitality(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "overall_vitality")
    v = d.get("verdict", "")
    score = facts.get("vitality_score") or 50

    if v == "GREEN":
        verdict = f"Overall vitality strong — energy/immunity base achha ({score}/100)"
        confidence = "high"
    elif v == "YELLOW":
        verdict = f"Overall vitality mixed — kuch zones strong, kuch pe dhyan ({score}/100)"
        confidence = "medium"
    else:
        verdict = f"Overall vitality weak tone — body extra care maang rahi hai ({score}/100)"
        confidence = "medium"

    evidence = [
        vitality_line(facts),
        dim_evidence(facts, "overall_vitality", "Constitution"),
        lord_evidence(facts, "h1", "Lagnesh axis"),
        karaka_evidence(facts, "Sun", "Vitality karaka"),
        karaka_evidence(facts, "Moon", "Mind-fluid karaka"),
        dim_evidence(facts, "preventive_risk", "Preventive zones"),
    ]
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="overall_vitality",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Direct vitality/immunity answer — NO dasha, NO disease names.",
        summary=["Static vitality only.", "Doctor for symptoms."],
        evidence=evidence[:8],
        ignore=["timing", "disease names", "death", "recovery date"],
        checks={"slice_type": "health_engine_v1", "archetype": "overall_vitality", "vitality_v": v},
    )
