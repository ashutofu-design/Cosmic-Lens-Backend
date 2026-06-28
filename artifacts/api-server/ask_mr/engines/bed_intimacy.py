from __future__ import annotations

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def run_bed_intimacy(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    if sig.venus_mars_conjunct_tight:
        level = "strong but needs emotional balance"
    elif sig.venus_mars_conjunct:
        level = "active / passionate"
    elif sig.venus_afflicted or sig.moon_in_8th:
        level = "mixed — comfort needs emotional safety first"
    else:
        level = "moderate — grows with trust and communication"

    verdict = f"Private life / intimacy: {level}"

    evidence = pick_notes(
        sig,
        [
            "Venus-Mars conjunction",
            "Venus in dusthana",
            "Moon in 8th",
            "Venus under nodal pull",
            "Ketu influence on 7th",
        ],
        limit=6,
    )
    if not evidence:
        evidence = ["Intimacy signals look normal/mixed; comfort depends on emotional safety."]
    if len(evidence) < 2:
        evidence.append("7th house Venus/Mars tone shapes private comfort — trust builds intimacy over time.")

    return EngineResult(
        archetype="bed_intimacy",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 sentences: intimacy comfort level → reason → respectful practical note.",
        summary=["Keep tone mature and non-explicit; no graphic detail."],
        evidence=evidence,
        ignore=["timing dates/windows", "explicit sexual detail"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "bed_intimacy",
            "venus_mars_conjunct": bool(sig.venus_mars_conjunct),
        },
    )
