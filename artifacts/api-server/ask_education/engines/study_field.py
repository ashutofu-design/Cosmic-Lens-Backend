from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, planet_line, reader


def run_study_field(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    merc = r.planet("Mercury") or {}
    jup = r.planet("Jupiter") or {}
    ven = r.planet("Venus") or {}
    mars = r.planet("Mars") or {}

    evidence = education_snapshot(kundli)
    hints: list[str] = []
    mh = int(merc.get("house") or 0)
    jh = int(jup.get("house") or 0)
    vh = int(ven.get("house") or 0)
    mah = int(mars.get("house") or 0)

    if mh in {3, 5, 10} or jh in {5, 9}:
        hints.append("analytical/teaching/research lines (Mercury-Jupiter strong)")
    if vh in {2, 5, 7, 10, 11} or mah in {3, 6, 10}:
        hints.append("creative/commerce/technical-applied lines (Venus-Mars support)")
    if jh in {9, 12}:
        hints.append("law/spiritual/higher-academic lines (Jupiter 9/12 link)")
    if not hints:
        hints.append("balanced chart — choose stream by interest + Mercury house strength")

    evidence.append(planet_line(r, "Mercury", "stream/intellect indicator"))
    evidence.append(planet_line(r, "Jupiter", "higher-field indicator"))
    evidence.append(f"Field synthesis: {hints[0]}.")

    verdict = f"Best study field: {hints[0]} — align course with strongest karaka house"

    return EngineResult(
        archetype="study_field",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Name 1-2 suitable streams/fields from Mercury/Jupiter/Venus evidence.",
        summary=["QUESTION FOCUS: which stream/subject/course — NOT career job line."],
        evidence=evidence[:8],
        ignore=["timing", "exact college name", "job package"],
        checks={"slice_type": "education_engine_v1", "archetype": "study_field", "field_hint": hints[0]},
    )
