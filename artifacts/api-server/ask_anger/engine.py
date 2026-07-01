from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .anger_registry import detect_anger_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    mars = r.planet("Mars") or {}
    moon = r.planet("Moon") or {}
    if mars.get("house"):
        h = int(mars["house"])
        if h in (1, 3, 6, 8, 12):
            score -= 10
        elif h in (4, 5, 9, 10, 11):
            score += 4
    if moon.get("house") and int(moon["house"]) in (6, 8, 12):
        score -= 6
    for occ in r.occupants(3) or []:
        if occ == "Mars":
            score -= 6
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        planet_line(r, "Mars", "anger/energy karaka (primary)"),
        planet_line(r, "Moon", "emotional trigger tone"),
        house_axis(r, 3, "Courage/impulse axis (3rd house)"),
        house_axis(r, 6, "Conflict/stress axis (6th house)"),
    ]
    lines.append(f"Anger-intensity index: {_score(kundli)}/100 (lower = hotter temper risk).")
    return lines[:7]


def run_anger_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_anger_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="anger_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Anger manageable — Mars/Moon tone balanced with awareness",
        verdict_mid="Gussa kabhi-kabhi sharp — chart impulse + stress triggers dikhata hai",
        verdict_low="Temper flare risk — Mars in dusthana/impulse houses; pause + breath work help",
        summary=["QUESTION FOCUS: anger temperament — practical coping line ok."],
        answer_plan="Mars + Moon + 3H/6H evidence only.",
        wants_explain=wants_explain,
        score_key="anger_score",
    )
