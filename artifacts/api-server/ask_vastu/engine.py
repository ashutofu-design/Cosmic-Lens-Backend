from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from vedic.love_reality.scoring_core import SIGNS
from .vastu_registry import detect_vastu_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 52
    for occ in r.occupants(4) or []:
        if occ in {"Jupiter", "Venus", "Moon"}:
            score += 6
        elif occ in {"Mars", "Saturn", "Rahu"}:
            score -= 4
    mars = r.planet("Mars") or {}
    if mars.get("house") and int(mars["house"]) == 4:
        score -= 6
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    asc_i = r.asc_index()
    asc_sign = SIGNS[asc_i] if isinstance(asc_i, int) else (kundli.get("ascendant") or "?")
    lines = [
        f"Lagna {asc_sign} — home orientation baseline for vastu tone.",
        house_axis(r, 4, "Home/land/property peace axis (4th house)"),
        planet_line(r, "Mars", "construction/heat energy in home matters"),
        planet_line(r, "Saturn", "structure/stability karaka"),
    ]
    lines.append(f"Home-vastu harmony index: {_score(kundli)}/100.")
    return lines[:7]


def run_vastu_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_vastu_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="vastu_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Home vastu tone supportive — 4H + benefic influence favour peaceful grah",
        verdict_mid="Vastu mixed — simple layout + cleanliness + light remedies help",
        verdict_low="Vastu stress tone — Mars/Saturn in 4H link; practical vastu consultant useful",
        summary=["QUESTION FOCUS: vastu from chart-home axis — not full architectural audit."],
        answer_plan="4H + lagna + Mars/Saturn only.",
        wants_explain=wants_explain,
        score_key="vastu_score",
    )
