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


def run_chronic_tendency(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "chronic_tendency")
    v = d.get("verdict", "")

    if v == "GREEN":
        verdict = "Chronic long-term pressure relatively low — lifestyle maintenance enough"
        confidence = "high"
    elif v == "YELLOW":
        verdict = "Chronic tendency mixed — kuch long-term zones monitor karni pad sakti hain"
        confidence = "medium"
    else:
        verdict = "Chronic tendency strong — 8H/Saturn axis pe active long-term management chahiye"
        confidence = "medium"

    evidence = [
        dim_evidence(facts, "chronic_tendency", "Chronic axis"),
        lord_evidence(facts, "h8", "8th house (chronic)"),
        karaka_evidence(facts, "Saturn", "Saturn endurance"),
        karaka_evidence(facts, "Rahu", "Rahu imbalance"),
        dim_evidence(facts, "overall_vitality", "Base vitality"),
    ]
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="chronic_tendency",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Long-term tendency — lifestyle > chart. NO disease names.",
        summary=["Chronic = tendency not diagnosis.", "Regular checkups help."],
        evidence=evidence[:8],
        ignore=["timing", "disease names", "cure guarantee"],
        checks={"slice_type": "health_engine_v1", "archetype": "chronic_tendency", "chronic_v": v},
    )
