from __future__ import annotations

from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader


def run_retirement_legacy(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    sat = r.planet("Saturn") or {}
    jup = r.planet("Jupiter") or {}

    evidence = [
        house_axis(r, 10, "Career peak/legacy axis (10th house)"),
        house_axis(r, 9, "Dharma/long-term purpose (9th house)"),
        f"Saturn (long-cycle maturity) in house {sat.get('house')} — late-career discipline and legacy building.",
        f"Jupiter in house {jup.get('house')} — wisdom/mentorship legacy after active career phase.",
    ]
    evidence.extend(inclination_evidence(inc, limit=3))
    evidence.append(
        f"Late-career tone: structure score {inc.get('structure_score')}/100 — "
        "stable senior roles or advisory legacy suit mature phase."
    )

    verdict = "Retirement/legacy: Saturn-Jupiter + 9H/10H show long-term career footprint and mentorship legacy"

    return EngineResult(
        archetype="retirement_legacy",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="Legacy tone → Saturn/Jupiter evidence → dignified mature-phase note.",
        summary=["QUESTION FOCUS: late career / legacy — not retirement age number."],
        evidence=evidence[:8],
        ignore=["timing", "exact retirement age"],
        checks={"slice_type": "career_engine_v1", "archetype": "retirement_legacy"},
    )
