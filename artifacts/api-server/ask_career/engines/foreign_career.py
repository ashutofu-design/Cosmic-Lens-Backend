from __future__ import annotations

from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader


def run_foreign_career(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    rahu = r.planet("Rahu") or {}
    lord10 = r.house_lord(10)
    p10l = r.planet(lord10) if lord10 else None

    evidence = [
        house_axis(r, 9, "Foreign/travel/dharma axis (9th house)"),
        house_axis(r, 12, "Abroad settlement axis (12th house)"),
        f"Rahu in house {rahu.get('house')} sign {rahu.get('sign')} — foreign/unconventional career channel.",
    ]
    if p10l and p10l.get("house") in (9, 12):
        evidence.append(
            f"10th lord {lord10} in house {p10l.get('house')} — career linked to foreign lands/travel."
        )
    evidence.extend(inclination_evidence(inc, limit=3))
    if "digital" in " ".join(inc.get("commercial_subtypes") or []).lower() or rahu.get("house") in (3, 9, 12):
        evidence.append("Foreign/digital career: Mercury-Rahu commercial subtype supports abroad or remote-global roles.")

    verdict = "Foreign career: 9H/12H + Rahu + 10th-lord placement indicate abroad-work potential"

    return EngineResult(
        archetype="foreign_career",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="Direct abroad-work answer → 2 chart reasons → one practical note.",
        summary=["QUESTION FOCUS: foreign/international career — not marriage abroad settlement."],
        evidence=evidence[:8],
        ignore=["timing", "visa guarantee", "exact country name"],
        checks={"slice_type": "career_engine_v1", "archetype": "foreign_career"},
    )
