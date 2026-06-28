from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, house_axis, reader


def run_admission(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = education_snapshot(kundli)
    evidence.append(house_axis(r, 4, "School/college foundation (4th house)"))
    evidence.append(house_axis(r, 11, "Gains/admission fulfillment (11th house)"))

    h4_occ = r.occupants(4) or []
    h11_occ = r.occupants(11) or []
    lord5 = r.house_lord(5)
    h5 = r.planet(lord5) if lord5 else {}

    if h11_occ or int(h5.get("house") or 0) in {1, 4, 5, 9, 10, 11}:
        verdict = "Admission/college seat potential good — 4H-5H-11H link supports enrollment"
        confidence = "high"
    elif int(h5.get("house") or 0) in {6, 8, 12}:
        verdict = "Admission possible with backup options — chart shows effort + second-choice planning helps"
        confidence = "medium"
    else:
        verdict = "Admission mixed — improve eligibility/scores; chart supports persistence over one-shot luck"
        confidence = "medium"

    return EngineResult(
        archetype="admission",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Direct admission/seat answer → 4H + 11H + 5L evidence.",
        summary=["QUESTION FOCUS: college/university admission — NOT admission date."],
        evidence=evidence[:8],
        ignore=["timing", "exact college name", "cutoff number"],
        checks={"slice_type": "education_engine_v1", "archetype": "admission"},
    )
