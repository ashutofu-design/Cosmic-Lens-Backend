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


def run_mental_stress(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "mental_stress")
    v = d.get("verdict", "")

    if v == "GREEN":
        verdict = "Mental stress pattern relatively calm — Moon/mind axis supported"
        confidence = "high"
    elif v == "YELLOW":
        verdict = "Mental stress mixed — pressure me mood swings ho sakte hain, care routine help karega"
        confidence = "medium"
    else:
        verdict = "Mental stress tendency strong — sleep, counselling aur doctor support important"
        confidence = "medium"

    evidence = [
        dim_evidence(facts, "mental_stress", "Mind-body stress"),
        karaka_evidence(facts, "Moon", "Moon (mind)"),
        lord_evidence(facts, "h4", "4th house (peace)"),
        karaka_evidence(facts, "Mercury", "Cognition"),
        karaka_evidence(facts, "Jupiter", "Calm/wisdom"),
    ]
    if sub_flag(facts, "moon_afflicted"):
        evidence.append("Moon afflicted — emotional sensitivity elevated")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="mental_stress",
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan="Mental stress tone — soft, supportive. Helpline if crisis hints.",
        summary=["Sensitive bucket.", "Counselling + sleep primary."],
        evidence=evidence[:8],
        ignore=["timing", "diagnosis", "death"],
        checks={
            "slice_type": "health_engine_v1",
            "archetype": "mental_stress",
            "mental_v": v,
            "sensitive": "mental_health",
        },
    )
