from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, house_axis, planet_line, reader


def run_higher_studies(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    jup = r.planet("Jupiter") or {}
    rahu = r.planet("Rahu") or {}

    evidence = education_snapshot(kundli)
    evidence.append(house_axis(r, 9, "Higher-education/dharma axis (9th house)"))
    evidence.append(planet_line(r, "Jupiter", "masters/PhD/research karaka"))
    if rahu.get("house"):
        evidence.append(planet_line(r, "Rahu", "foreign/unconventional study karaka"))

    jh = int(jup.get("house") or 0)
    rh = int(rahu.get("house") or 0)
    abroad_hint = rh in {9, 12, 3, 7} or jh in {9, 12}

    if jh in {1, 4, 5, 9, 10, 11} and rh not in {6, 8}:
        verdict = "Higher studies supported — masters/PhD/research path viable; abroad also possible" if abroad_hint else (
            "Higher studies supported — masters/PhD/research path viable in India"
        )
        confidence = "high"
    elif jh in {6, 8, 12}:
        verdict = "Higher studies possible with delay/extra effort — choose field aligned to Mercury-Jupiter strength"
        confidence = "medium"
    else:
        verdict = "Higher studies mixed — 9H/Jupiter show potential but field choice and mentor guidance matter"
        confidence = "medium"

    return EngineResult(
        archetype="higher_studies",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Direct higher-study/abroad answer → 9H + Jupiter + Rahu evidence.",
        summary=[
            "QUESTION FOCUS: masters/PhD/research/abroad study — NOT admission date.",
            "Do NOT guarantee visa or university name.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "visa date", "exact university name"],
        checks={
            "slice_type": "education_engine_v1",
            "archetype": "higher_studies",
            "abroad_hint": abroad_hint,
        },
    )
