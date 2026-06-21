from __future__ import annotations

from ..types import EngineResult
from ._health_base import (
    dim_evidence,
    karaka_evidence,
    load_facts,
    lord_evidence,
)


def run_addiction_support(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    ms = (facts.get("dimensions") or {}).get("mental_stress") or {}
    v = ms.get("verdict") or "YELLOW"

    if v == "RED":
        verdict = "Addiction tendency zone active — counselling/recovery groups primary, chart ek input"
        confidence = "medium"
    else:
        verdict = "Escapism tendency manageable — professional support + routine se nikalna realistic"
        confidence = "medium"

    evidence = [
        karaka_evidence(facts, "Rahu", "Rahu (illusion/escapism)"),
        karaka_evidence(facts, "Moon", "Moon (habit loop)"),
        lord_evidence(facts, "h12", "12th (escape/hidden)"),
        dim_evidence(facts, "mental_stress", "Mind stress axis"),
    ]

    return EngineResult(
        archetype="addiction_support",
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan="Addiction support tone — recovery groups primary.",
        summary=["Sensitive bucket.", "No shame — seek help."],
        evidence=evidence[:6],
        ignore=["timing", "diagnosis", "guarantee cure"],
        checks={"slice_type": "health_engine_v1", "archetype": "addiction_support", "sensitive": "addiction"},
    )
