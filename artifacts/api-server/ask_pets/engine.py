from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .pets_registry import detect_pets_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    venus = r.planet("Venus") or {}
    if venus.get("house") and int(venus["house"]) in (2, 4, 6, 11):
        score += 8
    for occ in r.occupants(6) or []:
        if occ in {"Venus", "Moon", "Mercury"}:
            score += 5
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 6, "Small animals/service/pets axis (6th house)"),
        house_axis(r, 2, "Family comforts axis (2nd house)"),
        planet_line(r, "Venus", "affection/comfort karaka for pets"),
        planet_line(r, "Moon", "nurturing tone"),
    ]
    lines.append(f"Pet-compatibility index: {_score(kundli)}/100.")
    return lines[:7]


def run_pets_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_pets_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="pets_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Pet keeping supportive — 6H/Venus tone favour caring bond with animals",
        verdict_mid="Pet possible with routine — chart mixed; responsibility clear rakho",
        verdict_low="Pet timing caution — busy/health schedule pehle settle karo",
        summary=["QUESTION FOCUS: pets tone — practical care line."],
        answer_plan="6H + Venus + 2H evidence only.",
        wants_explain=wants_explain,
        score_key="pets_score",
    )
