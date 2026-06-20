from __future__ import annotations

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def run_one_sided_love(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    # Heuristic: weak 5th + Saturn/Rahu on love axis → one-sided risk
    one_sided = bool(
        sig.fifth_lord_weak
        or sig.fifth_lord_in_twelfth
        or sig.moon_afflicted
        or sig.venus_afflicted
    )
    verdict = (
        "One-sided love risk: noticeable — balance expectations"
        if one_sided
        else "One-sided love risk: moderate — mutual effort can balance it"
    )

    evidence = pick_notes(
        sig,
        [
            "5th lord",
            "Venus in dusthana",
            "Venus debilitated",
            "Moon under Saturn/Rahu",
            "Rahu",
            "Saturn on 7th",
        ],
        limit=6,
    )
    if not evidence:
        evidence = ["Love axis signals look mixed; reciprocity depends on actions more than chart alone."]

    return EngineResult(
        archetype="one_sided_love",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 sentences: one-sided tilt → reason → gentle advice (self-respect).",
        summary=["Avoid harsh rejection language; encourage clarity and boundaries."],
        evidence=evidence,
        ignore=["timing dates/windows", "spouse profession"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "one_sided_love",
            "fifth_lord_weak": bool(sig.fifth_lord_weak),
            "venus_afflicted": bool(sig.venus_afflicted),
        },
    )
