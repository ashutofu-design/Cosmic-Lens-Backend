from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim,
    dim_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
    yogas_line,
)


def run_property_money(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    wp = dim(facts, "wealth_potential")
    sa = dim(facts, "saving_ability")
    debt_high = sub_flag(facts, "debt_burden_high")
    mars = (facts.get("karakas") or {}).get("Mars") or {}
    mars_dig = mars.get("dignity") or "?"

    wp_v = wp.get("verdict", "")
    if wp_v == "GREEN" and sa.get("verdict") != "RED" and not debt_high:
        verdict = "Property/ghar ke liye paisa jama karne ka pattern strong — planned purchase realistic"
        confidence = "high"
    elif wp_v == "YELLOW" or sa.get("verdict") == "YELLOW":
        verdict = "Property possible par discipline chahiye — bachat + planned home-loan mix realistic"
        confidence = "medium"
    elif debt_high or sa.get("verdict") == "RED":
        verdict = "Abhi property purchase tight — pehle saving aur karz control, phir ghar plan karo"
        confidence = "medium"
    else:
        verdict = "Property money slow-build pattern — long-term saving se ghar realistic, jaldi nahi"
        confidence = "low"

    evidence = [
        lord_evidence(facts, "h4", "Home/property axis (4th house)"),
        lord_evidence(facts, "h2", "Accumulated wealth (2nd)"),
        lord_evidence(facts, "h11", "Gains for big purchase (11th)"),
        dim_evidence(facts, "wealth_potential", "Long-term wealth for asset"),
        dim_evidence(facts, "saving_ability", "Saving for down-payment"),
        f"Real-estate karaka Mars dignity: {mars_dig}",
        yogas_line(facts),
    ]
    if "real-estate" in " ".join(sub_flag(facts, "income_affinity", []) or []):
        evidence.append("Income affinity includes real-estate/engineering — property theme linked to earning path")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="property_money",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Ghar/property ke liye paisa pattern — saving + loan capacity, no exact price.",
        summary=["No property location/date.", "Focus money readiness for home purchase."],
        evidence=evidence[:8],
        ignore=["timing", "exact property price", "location guarantee"],
        checks={"slice_type": "finance_engine_v1", "archetype": "property_money", "wealth_v": wp_v},
    )
