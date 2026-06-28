from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, house_axis, planet_line, reader


def run_degree_completion(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    sat = r.planet("Saturn") or {}
    jup = r.planet("Jupiter") or {}
    evidence = education_snapshot(kundli)
    evidence.append(house_axis(r, 9, "Degree/higher-learning completion (9th house)"))
    evidence.append(planet_line(r, "Saturn", "discipline/completion karaka"))
    evidence.append(planet_line(r, "Jupiter", "graduation/grace karaka"))
    sh = int(sat.get("house") or 0)
    if sh in {1, 4, 5, 9, 10, 11}:
        verdict = "Degree/graduation completion supported — Saturn discipline + 9H show finish capacity"
        confidence = "high"
    elif sh in {6, 8, 12}:
        verdict = "Degree completion possible with delay — chart shows extra semesters/backlog clear karna padega"
        confidence = "medium"
    else:
        verdict = "Degree completion mixed — consistent attendance + exam clears decide graduation timeline"
        confidence = "medium"
    return EngineResult(
        archetype="degree_completion",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Direct degree/graduation completion answer → 9H + Saturn/Jupiter.",
        summary=["QUESTION FOCUS: degree complete/graduate/pass-out — NOT graduation date."],
        evidence=evidence[:8],
        ignore=["timing", "exact year", "dropout guarantee"],
        checks={"slice_type": "education_engine_v1", "archetype": "degree_completion"},
    )
