from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, house_axis, planet_line, reader


def run_marks_performance(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    merc = r.planet("Mercury") or {}
    jup = r.planet("Jupiter") or {}
    evidence = education_snapshot(kundli)
    evidence.append(house_axis(r, 5, "Marks/intellect performance (5th house)"))
    evidence.append(planet_line(r, "Mercury", "exam-writing/analytical marks karaka"))
    evidence.append(planet_line(r, "Jupiter", "wisdom/retention for higher marks"))
    mh = int(merc.get("house") or 0)
    jh = int(jup.get("house") or 0)
    if mh in {1, 4, 5, 9, 10, 11} and jh in {1, 4, 5, 9, 10, 11}:
        verdict = "Marks/percentage potential strong — Mercury-Jupiter + 5H support good scores with revision"
        confidence = "high"
    elif mh in {6, 8, 12}:
        verdict = "Marks improve with method — chart shows effort-gap; answer-writing practice lifts percentage"
        confidence = "medium"
    else:
        verdict = "Marks performance mixed — smart topic selection + mock papers decide final percentage band"
        confidence = "medium"
    return EngineResult(
        archetype="marks_performance",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Direct marks/grade/topper answer → 5H + Mercury/Jupiter — NO exact numbers.",
        summary=[
            "QUESTION FOCUS: marks/percentage/grade/topper — NOT exact score prediction.",
            "Never invent a percentage or rank number.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "exact marks", "exact percentage", "exact rank"],
        checks={"slice_type": "education_engine_v1", "archetype": "marks_performance"},
    )
