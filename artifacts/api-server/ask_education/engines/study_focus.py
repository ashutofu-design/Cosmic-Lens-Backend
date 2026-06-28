from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, planet_line, reader


def run_study_focus(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    moon = r.planet("Moon") or {}
    merc = r.planet("Mercury") or {}
    sat = r.planet("Saturn") or {}

    evidence = education_snapshot(kundli)
    evidence.append("Study focus/concentration axis: Moon mind stability + Mercury study habit link.")
    evidence.append(planet_line(r, "Moon", "mind/concentration karaka"))
    evidence.append(planet_line(r, "Mercury", "study discipline karaka"))
    evidence.append(planet_line(r, "Saturn", "consistency/structure karaka"))

    mh = int(moon.get("house") or 0)
    sh = int(sat.get("house") or 0)
    if mh in {6, 8, 12} or sh in {6, 8, 12}:
        verdict = "Focus wavers when routine missing — short study blocks + fixed timing build discipline"
        confidence = "medium"
    elif int(merc.get("house") or 0) in {1, 4, 5, 9, 10, 11}:
        verdict = "Study focus can be strong — chart supports concentration when distractions are controlled"
        confidence = "high"
    else:
        verdict = "Study focus improves with habit-system — chart shows mind needs structure more than motivation speeches"
        confidence = "medium"

    return EngineResult(
        archetype="study_focus",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Acknowledge focus issue → Moon/Mercury/Saturn evidence → one practical study habit.",
        summary=["QUESTION FOCUS: concentration/motivation in study — NOT timing."],
        evidence=evidence[:8],
        ignore=["timing", "medical diagnosis", "addiction labels"],
        checks={"slice_type": "education_engine_v1", "archetype": "study_focus"},
    )
