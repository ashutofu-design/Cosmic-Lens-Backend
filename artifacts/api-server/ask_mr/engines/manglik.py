from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader, MANGLIK_HOUSES

from ..narrator import build_manglik_template
from ..types import EngineResult


def run_manglik(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    mars = r.planet("Mars")
    mars_house = mars.get("house") if mars else None
    is_manglik = isinstance(mars_house, int) and mars_house in MANGLIK_HOUSES

    verdict = "Manglik: yes" if is_manglik else "Manglik: no (classic Mangal position not active)"
    confidence = "high" if mars_house is not None else "low"

    evidence: list[str] = []
    if mars_house is None:
        evidence.append("Mars placement missing — manglik signal unclear from available chart data.")
    else:
        evidence.append(f"Mars is placed in house {mars_house} (classic manglik houses: 1/4/7/8/12).")
        if is_manglik and mars_house == 7:
            evidence.append("Mars on partnership axis can bring quick triggers/arguments if communication is rough.")
        elif is_manglik and mars_house in (8, 12):
            evidence.append("This placement can show intense expectations + privacy/secrecy stress in relationships.")
        elif is_manglik and mars_house in (1, 4):
            evidence.append("This placement can show strong will/temper — adjustment + patience becomes important.")
        else:
            evidence.append("Manglik pattern is not dominant; stability depends more on overall relationship signals.")

    summary = [
        "Answer should be calm and non-alarming; mention adjustment/communication, not doom.",
    ]

    result = EngineResult(
        archetype="manglik",
        verdict=verdict,
        confidence=confidence,
        word_budget=70 if wants_explain else 45,
        answer_plan="Seedha haan/nahi → 1 soft reason → 1 practical line.",
        summary=summary,
        evidence=evidence[:6],
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "love-vs-arranged",
            "breakup prediction certainty",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "manglik",
            "mars_house": mars_house,
            "is_manglik": is_manglik,
        },
    )

    if not wants_explain and mars_house is not None:
        result.skip_llm = True
        result.template_text = build_manglik_template(result)

    return result

