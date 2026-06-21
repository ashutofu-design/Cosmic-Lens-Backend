from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    dim_evidence,
    load_facts,
    sub_flag,
    yogas_line,
)

_ALL_YOGAS = ("Dhana", "Lakshmi", "Kubera", "Gaja-Kesari", "Adhi", "Chandra-Mangal", "Vipreet-Raja")


def run_dhana_yoga(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    yogas = facts.get("wealth_yogas") or []
    if sub_flag(facts, "wealth_strong") or len(yogas) >= 2:
        verdict = "Strong dhan-yog active — wealth capacity real, ab discipline + dasha support chahiye"
        confidence = "high"
    elif yogas:
        verdict = "Kuch dhan-yog hain — alone shortcut nahi, effort + planning se kaam karenge"
        confidence = "medium"
    else:
        verdict = "Major dhan-yog active nahi — wealth discipline + earning se banegi, yog shortcut nahi"
        confidence = "medium"

    evidence = [yogas_line(facts)]
    for y in yogas:
        tag = " (recovery yog)" if y == "Vipreet-Raja" else ""
        evidence.append(f"Active: {y}{tag}")
    missing = [y for y in _ALL_YOGAS if y not in yogas]
    if missing:
        evidence.append(f"Not active: {', '.join(missing[:5])}")
    evidence.append(dim_evidence(facts, "wealth_potential", "Wealth potential check"))
    evidence.append(dim_evidence(facts, "saving_ability", "Saving to hold yog gains"))

    return EngineResult(
        archetype="dhana_yoga",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Kaun se yog active — plain list + final capacity line.",
        summary=["List yogas from facts only.", "No invented yog names."],
        evidence=evidence[:8],
        ignore=["timing", "guaranteed richness", "new yog invention"],
        checks={"slice_type": "finance_engine_v1", "archetype": "dhana_yoga", "yogas": yogas},
    )
