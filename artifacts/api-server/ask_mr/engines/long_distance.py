from __future__ import annotations

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def run_long_distance(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    distance_hits = 0
    if sig.saturn_on_7th:
        distance_hits += 2
    if sig.moon_afflicted or sig.moon_in_8th:
        distance_hits += 1
    if sig.separation_yoga:
        distance_hits += 1
    if sig.rahu_on_7th_axis:
        distance_hits += 1

    if distance_hits >= 3:
        level = "demanding — bond needs clear routines or distance strains trust"
    elif distance_hits >= 2:
        level = "workable — distance tests the bond but repair habits help"
    elif sig.reconnection_yoga:
        level = "manageable — connection can stay alive with steady contact"
    else:
        level = "moderate — closeness grows when communication stays regular"

    verdict = f"Long-distance / separation-in-relationship: {level}"

    evidence = pick_notes(
        sig,
        [
            "Saturn on 7th",
            "12th lord in 7th",
            "Moon under Saturn/Rahu",
            "Moon in 8th",
            "nodes on 7th",
            "Rahu",
            "foreign",
        ],
        limit=6,
    )
    if sig.reconnection_yoga:
        evidence.append("5th lord strong — emotional reconnection capacity helps long-distance.")
    if not evidence:
        evidence = ["Distance theme looks mixed; routine calls and clear plans matter most."]

    return EngineResult(
        archetype="long_distance",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="2–3 sentences: LDR viability → 1–2 chart reasons → one practical habit.",
        summary=[
            "Answer long-distance / door rehkar rishta directly.",
            "Include one practical trust habit (fixed calls, visits, clarity).",
            "NO shayad/ho sakta hai/lagta hai.",
        ],
        evidence=evidence[:6],
        ignore=["timing dates/windows", "exact relocation month"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "long_distance",
            "distance_hits": distance_hits,
            "reconnection_yoga": bool(sig.reconnection_yoga),
        },
    )
