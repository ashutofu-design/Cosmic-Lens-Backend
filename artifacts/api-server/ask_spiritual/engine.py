from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .spiritual_registry import detect_spiritual_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    jup = r.planet("Jupiter") or {}
    ketu = r.planet("Ketu") or {}
    if jup.get("house") and int(jup["house"]) in (1, 4, 5, 9, 10, 12):
        score += 10
    if ketu.get("house") and int(ketu["house"]) in (8, 9, 12):
        score += 8
    for h in (8, 9, 12):
        for occ in r.occupants(h) or []:
            if occ in {"Jupiter", "Ketu"}:
                score += 5
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 9, "Dharma/guru/blessings axis (9th house)"),
        house_axis(r, 12, "Moksha/letting-go axis (12th house)"),
        house_axis(r, 8, "Occult/transformation axis (8th house)"),
        planet_line(r, "Ketu", "moksha/detachment karaka"),
        planet_line(r, "Jupiter", "guru/dharma karaka"),
    ]
    lines.append(f"Spiritual-inclination index: {_score(kundli)}/100.")
    return lines[:8]


def run_spiritual_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_spiritual_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="spiritual_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Spiritual path strong — 9H/12H + Jupiter/Ketu favour dharma & inner growth",
        verdict_mid="Spiritual interest mixed — chart phases of seeking + worldly duty both",
        verdict_low="Spiritual path needs patience — pehle grounding, phir steady sadhana",
        summary=["QUESTION FOCUS: spiritual tone — NOT exact deeksha date."],
        answer_plan="9H + 12H + 8H + Jupiter + Ketu only.",
        wants_explain=wants_explain,
        score_key="spiritual_score",
    )
