from __future__ import annotations

import re

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_RECIPROCITY_Q = re.compile(
    r"(?ix)\b(kya\s+wo\s+bhi|utna\s+hi\s+pyaar|jitna\s+main|love\s+me\s+back)\b"
)


def run_emotional_attachment(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    reciprocity_q = bool(_RECIPROCITY_Q.search(question or ""))

    deep = bool(
        not sig.moon_afflicted
        and not sig.moon_debil
        and not sig.moon_in_8th
    )
    fragile = bool(sig.moon_afflicted or sig.moon_debil or sig.moon_d9_debil)

    if reciprocity_q and fragile:
        verdict = "Reciprocity: mixed/kam — feelings hain lekin barabar depth abhi nahi"
    elif reciprocity_q and deep:
        verdict = "Reciprocity: haan — emotional depth possible, consistency se badhega"
    elif deep and not fragile:
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
    evidence = [e for e in evidence if "dasha" not in (e or "").lower()]
    if not evidence:
        evidence = ["Emotional signals look balanced; attachment depends on daily care."]

    return EngineResult(
        archetype="emotional_attachment",
        verdict=verdict,
        confidence="medium",
        word_budget=75 if wants_explain else 55,
        answer_plan=(
            "Line 1: seedha haan/naa/mixed (partner ke pyaar ka level). "
            "Line 2: ek Moon/Venus reason. Line 3: warm practical note."
        ),
        summary=["Focus on reciprocity/feeling depth — direct jawab pehle."],
        evidence=evidence,
        ignore=["timing dates/windows", "dasha periods", "breakup certainty"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "emotional_attachment",
            "reciprocity_question": reciprocity_q,
            "moon_afflicted": bool(sig.moon_afflicted),
            "moon_debil": bool(sig.moon_debil),
        },
    )
