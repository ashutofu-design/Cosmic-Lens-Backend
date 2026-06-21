from __future__ import annotations

from ..types import EngineResult
from ._health_base import dim_evidence, load_facts, lord_evidence


def run_parent_health(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    verdict = (
        "Parent health ke liye chart supportive insight de sakta hai — "
        "4H/9H axis + practical doctor care primary"
    )

    evidence = [
        lord_evidence(facts, "h4", "4th (mother axis)"),
        "9th house (father axis) — check chart 9L placement for parent-care tone",
        dim_evidence(facts, "overall_vitality", "Native vitality (caregiver energy)"),
        dim_evidence(facts, "chronic_tendency", "Long-term tendency context"),
    ]

    return EngineResult(
        archetype="parent_health",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Soft tone — parent health. Doctor + caregiver action first.",
        summary=["Sensitive bucket.", "Chart is secondary to medical care."],
        evidence=evidence[:6],
        ignore=["timing", "diagnosis", "death prediction"],
        checks={"slice_type": "health_engine_v1", "archetype": "parent_health", "sensitive": "parent_health"},
    )
