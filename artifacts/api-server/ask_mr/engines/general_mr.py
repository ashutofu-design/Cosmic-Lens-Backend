from __future__ import annotations

from vedic.love_reality.scoring_core import risk_band_high_is_good

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def _quality_verdict(score: int, sig) -> str:
    band = risk_band_high_is_good(score)
    if band == "low":
        return "Marriage/relationship quality: generally supportive"
    if band == "medium":
        return "Marriage/relationship quality: mixed — effort and communication matter"
    if band == "high":
        return "Marriage/relationship quality: strained patterns visible — repair habits needed"
    return "Marriage/relationship quality: fragile — patience and boundaries essential"


def run_general_mr(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    w = int(sig.affliction_weight or 0)
    quality_score = max(0, min(100, 100 - int(round(w * 1.2))))
    verdict = _quality_verdict(quality_score, sig)

    evidence = pick_notes(
        sig,
        [
            "5th lord strong",
            "Saturn on 7th",
            "Mars on 7th",
            "7th lord in dusthana",
            "7th lord debilitated",
            "Venus in dusthana",
            "Venus debilitated",
            "Moon under Saturn/Rahu",
            "nodes on 7th",
            "Navamsa Venus weak",
            "Navamsa Moon debilitated",
        ],
        limit=6,
    )
    if sig.reconnection_yoga and "5th lord strong" not in str(evidence).lower():
        evidence.insert(0, "5th lord strong — emotional reconnection capacity present.")
    if not evidence:
        evidence = ["No dominant marriage-quality driver; overall pattern looks mixed/normal."]

    summary = [
        "Answer marriage happiness/quality without guaranteeing fate.",
        "If mixed: suggest communication, respect, and realistic expectations.",
    ]
    if sig.separation_yoga:
        summary.append("Separation theme exists — emphasize repair time, not doom.")
    if quality_score >= 72:
        summary.append("Tone can be warm and encouraging.")

    return EngineResult(
        archetype="general_mr",
        verdict=verdict,
        confidence="medium" if quality_score >= 35 else "low",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 short sentences: quality outlook → 1–2 reasons → soft practical line.",
        summary=summary[:4],
        evidence=evidence[:6],
        ignore=["timing dates/windows", "exact job title for spouse"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "general_mr",
            "quality_score": quality_score,
            "affliction_weight": w,
            "separation_yoga": bool(sig.separation_yoga),
            "reconnection_yoga": bool(sig.reconnection_yoga),
        },
    )
