from __future__ import annotations

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def run_obsession(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    obsessed = bool(
        sig.rahu_on_7th_axis
        or sig.emotional_instability
        or sig.venus_mars_conjunct_tight
        or sig.moon_rahu_afflicted
        or sig.moon_dual_flip_risk
    )
    verdict = (
        "Obsession/jealousy theme: sensitive — balance and space needed"
        if obsessed
        else "Obsession theme: moderate — awareness can prevent escalation"
    )

    evidence = pick_notes(
        sig,
        [
            "nodes on 7th",
            "Venus under nodal pull",
            "Venus-Mars conjunction",
            "Moon under Saturn/Rahu",
            "dual sign under affliction",
            "obsession",
        ],
        limit=6,
    )
    if not evidence:
        evidence = ["No strong obsession driver triggered; emotional balance looks manageable."]

    return EngineResult(
        archetype="obsession",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 sentences: obsession/jealousy pattern → reason → calm boundary advice.",
        summary=["Avoid blaming; suggest pause, space, and honest conversation."],
        evidence=evidence,
        ignore=["timing dates/windows", "accusatory language"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "obsession",
            "rahu_on_7th_axis": bool(sig.rahu_on_7th_axis),
            "emotional_instability": bool(sig.emotional_instability),
        },
    )
