from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, planet_line, reader


def run_coaching_support(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    merc = r.planet("Mercury") or {}
    sat = r.planet("Saturn") or {}
    evidence = education_snapshot(kundli)
    evidence.append("Coaching vs self-study axis: Mercury skill-building + Saturn structured prep.")
    evidence.append(planet_line(r, "Mercury", "self-study vs guided learning indicator"))
    evidence.append(planet_line(r, "Saturn", "structured coaching/discipline fit"))
    sh = int(sat.get("house") or 0)
    mh = int(merc.get("house") or 0)
    if sh in {1, 4, 5, 9, 10, 11} and mh not in {1, 4, 5, 9, 10, 11}:
        verdict = "Coaching/tuition suits chart — Saturn structure helps more than pure self-study right now"
        confidence = "medium"
    elif mh in {1, 4, 5, 9, 10, 11} and sh in {6, 8, 12}:
        verdict = "Self-study can work — Mercury strong; selective coaching for weak topics enough"
        confidence = "medium"
    else:
        verdict = "Hybrid best — coaching for weak areas + self-revision; chart supports guided prep"
        confidence = "medium"
    return EngineResult(
        archetype="coaching_support",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Coaching vs self-study answer → Mercury/Saturn balance.",
        summary=["QUESTION FOCUS: coaching/tuition/online course — NOT institute name."],
        evidence=evidence[:8],
        ignore=["timing", "institute name", "fee amount"],
        checks={"slice_type": "education_engine_v1", "archetype": "coaching_support"},
    )
