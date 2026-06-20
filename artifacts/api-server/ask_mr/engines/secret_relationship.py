from __future__ import annotations

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def run_secret_relationship(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    secret = bool(
        sig.third_person_risk
        or sig.twelfth_lord_in_fifth
        or sig.fifth_lord_in_twelfth
        or sig.rahu_on_7th_axis
    )
    verdict = (
        "Secret/hidden relationship theme: active — transparency reduces stress"
        if secret
        else "Secret relationship theme: not strongly visible — clarity still helps"
    )

    evidence = pick_notes(
        sig,
        [
            "12th lord in 5th",
            "12th lord in 7th",
            "hidden ties",
            "parallel attention",
            "secret parallel",
            "nodes on 7th",
            "Venus in dusthana",
        ],
        limit=6,
    )
    if not evidence:
        evidence = ["No strong secrecy driver triggered; treat as mixed/normal."]

    return EngineResult(
        archetype="secret_relationship",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 sentences: secrecy tendency → reason → practical honesty advice.",
        summary=["Non-judgmental tone; focus on clarity and self-protection."],
        evidence=evidence,
        ignore=["timing dates/windows", "public shaming language"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "secret_relationship",
            "third_person_risk": bool(sig.third_person_risk),
            "twelfth_lord_in_fifth": bool(sig.twelfth_lord_in_fifth),
        },
    )
