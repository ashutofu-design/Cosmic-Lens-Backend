from __future__ import annotations

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def run_emotional_attachment(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    deep = bool(
        not sig.moon_afflicted
        and not sig.moon_debil
        and not sig.moon_in_8th
    )
    fragile = bool(sig.moon_afflicted or sig.moon_debil or sig.moon_d9_debil)

    if deep and not fragile:
        verdict = "Emotional attachment: capacity for deep bond — consistency matters"
    elif fragile:
        verdict = "Emotional attachment: sensitive — mood swings can affect closeness"
    else:
        verdict = "Emotional attachment: mixed — depth grows with trust over time"

    evidence = pick_notes(
        sig,
        [
            "Moon debilitated",
            "Moon under Saturn/Rahu",
            "Moon in 8th",
            "Navamsa Moon debilitated",
            "Saturn-Moon link",
            "Venus in dusthana",
            "Venus debilitated",
        ],
        limit=6,
    )
    if not evidence:
        evidence = ["Emotional signals look balanced; attachment depends on daily care."]

    return EngineResult(
        archetype="emotional_attachment",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 sentences: attachment style → reason → warm practical note.",
        summary=["Focus on feelings and bonding, not timing or spouse job."],
        evidence=evidence,
        ignore=["timing dates/windows", "breakup certainty"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "emotional_attachment",
            "moon_afflicted": bool(sig.moon_afflicted),
            "moon_debil": bool(sig.moon_debil),
        },
    )
