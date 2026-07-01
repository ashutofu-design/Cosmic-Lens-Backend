from __future__ import annotations

import re

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_RECIPROCITY_Q = re.compile(
    r"(?ix)\b(kya\s+wo\s+bhi|utna\s+hi\s+pyaar|jitna\s+main|love\s+me\s+back|"
    r"dil\s+se\s+.*pyaar)\b"
)


def run_one_sided_love(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    q = question or ""
    reciprocity_q = bool(_RECIPROCITY_Q.search(q))

    one_sided = bool(
        sig.fifth_lord_weak
        or sig.fifth_lord_in_twelfth
        or sig.moon_afflicted
        or sig.venus_afflicted
    )
    if reciprocity_q and one_sided:
        verdict = "Reciprocity: kam / one-sided — wo abhi utna barabar pyaar nahi dikhata"
    elif reciprocity_q:
        verdict = "Reciprocity: mixed — pyaar hai lekin abhi barabar depth nahi"
    elif one_sided:
        verdict = "One-sided love risk: noticeable — balance expectations"
    else:
        verdict = "One-sided love risk: moderate — mutual effort can balance it"

    evidence = pick_notes(
        sig,
        [
            "5th lord",
            "Venus in dusthana",
            "Venus debilitated",
            "Moon under Saturn/Rahu",
            "Saturn on 7th",
        ],
        limit=5,
    )
    evidence = [
        e for e in evidence
        if "dasha" not in (e or "").lower() and "timing" not in (e or "").lower()
    ]
    if not evidence:
        evidence = ["Love axis signals look mixed; reciprocity depends on actions more than chart alone."]

    return EngineResult(
        archetype="one_sided_love",
        verdict=verdict,
        confidence="medium",
        word_budget=75 if wants_explain else 55,
        answer_plan=(
            "Line 1: seedha haan/naa/mixed (kya wo bhi utna pyaar karti hai). "
            "Line 2: ek chart reason. Line 3: short practical tip."
        ),
        summary=[
            "Reciprocity sawal — pehle direct jawab, phir reason; harsh rejection mat karo.",
        ],
        evidence=evidence,
        ignore=["timing dates/windows", "dasha periods", "spouse profession"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "one_sided_love",
            "reciprocity_question": reciprocity_q,
            "fifth_lord_weak": bool(sig.fifth_lord_weak),
            "venus_afflicted": bool(sig.venus_afflicted),
        },
    )
