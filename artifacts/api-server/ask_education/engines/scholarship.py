from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, house_axis, planet_line, reader


def run_scholarship(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    jup = r.planet("Jupiter") or {}
    merc = r.planet("Mercury") or {}
    evidence = education_snapshot(kundli)
    evidence.append(house_axis(r, 11, "Gains/scholarship fulfillment (11th house)"))
    evidence.append(house_axis(r, 2, "Resources/fee support (2nd house)"))
    evidence.append(planet_line(r, "Jupiter", "merit/grace karaka for scholarship"))
    jh = int(jup.get("house") or 0)
    mh = int(merc.get("house") or 0)
    if jh in {1, 4, 5, 9, 10, 11} and mh in {1, 4, 5, 9, 10, 11}:
        verdict = "Scholarship/financial-aid potential good — Jupiter-Mercury + 11H support merit funding"
        confidence = "high"
    elif jh in {6, 8, 12}:
        verdict = "Scholarship possible via effort — apply broadly; chart shows merit but needs strong application"
        confidence = "medium"
    else:
        verdict = "Scholarship mixed — 11H/2H link moderate; merit + alternate funding routes both needed"
        confidence = "medium"
    return EngineResult(
        archetype="scholarship",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Direct scholarship/stipend answer → 11H/2H + Jupiter evidence.",
        summary=["QUESTION FOCUS: scholarship/stipend/fee aid — NOT loan EMI timing."],
        evidence=evidence[:8],
        ignore=["timing", "exact amount", "bank name"],
        checks={"slice_type": "education_engine_v1", "archetype": "scholarship"},
    )
