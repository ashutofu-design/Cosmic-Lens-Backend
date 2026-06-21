from __future__ import annotations

from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader


def run_fame_recognition(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    sun = r.planet("Sun") or {}
    ven = r.planet("Venus") or {}

    evidence = [
        house_axis(r, 10, "Public reputation/career visibility (10th house)"),
        house_axis(r, 11, "Gains/fame/network reach (11th house)"),
        f"Sun (public image) in house {sun.get('house')} sign {sun.get('sign')} — visibility and recognition tone.",
        f"Venus (popularity/charm) in house {ven.get('house')} sign {ven.get('sign')} — audience appeal in profession.",
    ]
    evidence.extend(inclination_evidence(inc, limit=3))
    if int((inc.get("psychology") or {}).get("leadership") or 0) >= 60:
        evidence.append("Leadership score high — public recognition grows through authority roles.")
    if sun.get("house") in (1, 10, 11):
        evidence.append("Sun in visibility houses — name/fame in career field is chart-supported.")

    verdict = "Fame/recognition in career: 10H/11H + Sun/Venus public-image markers"

    return EngineResult(
        archetype="fame_recognition",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="Direct fame/recognition level → 2 public-image reasons → humble practical note.",
        summary=["QUESTION FOCUS: career fame/recognition — not social media vanity guarantee."],
        evidence=evidence[:8],
        ignore=["timing", "viral guarantee"],
        checks={"slice_type": "career_engine_v1", "archetype": "fame_recognition"},
    )
