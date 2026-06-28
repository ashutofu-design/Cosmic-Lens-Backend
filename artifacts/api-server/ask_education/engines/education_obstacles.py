from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, house_axis, planet_line, reader


def run_education_obstacles(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    sat = r.planet("Saturn") or {}
    rahu = r.planet("Rahu") or {}
    evidence = education_snapshot(kundli)
    evidence.append("Education obstacle/backlog axis: 8H delay lessons + Saturn recovery discipline.")
    evidence.append(house_axis(r, 8, "Obstacles/transformations in study (8th house)"))
    evidence.append(house_axis(r, 12, "Breaks/gaps/foreign-study detours (12th house)"))
    evidence.append(planet_line(r, "Saturn", "delay/discipline lessons in education"))
    evidence.append(planet_line(r, "Rahu", "sudden breaks or unconventional study path"))
    sh = int(sat.get("house") or 0)
    if sh in {6, 8, 12}:
        verdict = "Education obstacles real but workable — backlog/gap clear ho sakta hai with Saturn-style routine"
        confidence = "medium"
    else:
        verdict = "Education obstacles temporary — chart shows recovery path after structured catch-up plan"
        confidence = "medium"
    return EngineResult(
        archetype="education_obstacles",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Acknowledge obstacle/backlog/gap → 8H/Saturn evidence → practical recovery step.",
        summary=[
            "QUESTION FOCUS: backlog/gap/fail/delay in study — NOT when obstacle ends.",
            "Do NOT say padhai chhod do.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "dropout advice", "exact semester count"],
        checks={"slice_type": "education_engine_v1", "archetype": "education_obstacles"},
    )
