from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, planet_line, reader


def run_learning_ability(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    merc = r.planet("Mercury") or {}
    moon = r.planet("Moon") or {}
    jup = r.planet("Jupiter") or {}
    evidence = education_snapshot(kundli)
    evidence.append(planet_line(r, "Mercury", "intellect/memory/analytical ability"))
    evidence.append(planet_line(r, "Moon", "mind/retention/concentration base"))
    evidence.append(planet_line(r, "Jupiter", "wisdom/grasping depth"))
    mh = int(merc.get("house") or 0)
    if mh in {1, 4, 5, 9, 10, 11}:
        verdict = "Learning ability strong — sharp buddhi/memory axis; weak subjects improve with targeted drill"
        confidence = "high"
    elif mh in {6, 8, 12}:
        verdict = "Learning ability needs technique — chart shows mind works better with visuals/practice than rote"
        confidence = "medium"
    else:
        verdict = "Learning ability moderate — consistency beats raw talent; coaching helps weak subjects most"
        confidence = "medium"
    return EngineResult(
        archetype="learning_ability",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Answer buddhi/memory/subject-weakness → Mercury/Moon/Jupiter evidence.",
        summary=["QUESTION FOCUS: intelligence/memory/weak subject — NOT IQ score or diagnosis."],
        evidence=evidence[:8],
        ignore=["timing", "iq score", "learning disability label"],
        checks={"slice_type": "education_engine_v1", "archetype": "learning_ability"},
    )
