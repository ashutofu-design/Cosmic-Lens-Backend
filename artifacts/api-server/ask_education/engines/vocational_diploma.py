from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, house_axis, planet_line, reader


def run_vocational_diploma(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    merc = r.planet("Mercury") or {}
    mars = r.planet("Mars") or {}
    evidence = education_snapshot(kundli)
    evidence.append(house_axis(r, 3, "Skills/craft learning (3rd house)"))
    evidence.append(planet_line(r, "Mercury", "technical/skill learning karaka"))
    evidence.append(planet_line(r, "Mars", "hands-on/vocational execution karaka"))
    mh = int(merc.get("house") or 0)
    mah = int(mars.get("house") or 0)
    if mh in {1, 3, 5, 10, 11} or mah in {3, 6, 10, 11}:
        verdict = "Vocational/diploma/ITI path suits — 3H skill axis + Mercury-Mars support practical training"
        confidence = "high"
    else:
        verdict = "Vocational course viable — choose skill-aligned diploma; apprenticeship accelerates chart support"
        confidence = "medium"
    return EngineResult(
        archetype="vocational_diploma",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="ITI/diploma/polytechnic answer → 3H + Mercury/Mars evidence.",
        summary=["QUESTION FOCUS: diploma/ITI/vocational/certificate — NOT job salary after."],
        evidence=evidence[:8],
        ignore=["timing", "salary after course", "company name"],
        checks={"slice_type": "education_engine_v1", "archetype": "vocational_diploma"},
    )
