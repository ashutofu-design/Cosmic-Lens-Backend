from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .dreams_registry import detect_dreams_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    moon = r.planet("Moon") or {}
    ketu = r.planet("Ketu") or {}
    if moon.get("house") and int(moon["house"]) in (8, 12):
        score -= 6
    if ketu.get("house") and int(ketu["house"]) in (8, 9, 12):
        score += 4
    for h in (8, 9, 12):
        for occ in r.occupants(h) or []:
            if occ in {"Moon", "Ketu", "Rahu"}:
                score += 3
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 9, "Dreams/dharma/subconscious axis (9th house)"),
        house_axis(r, 12, "Sleep/subconscious/foreign axis (12th house)"),
        house_axis(r, 8, "Hidden fear/transformation axis (8th house)"),
        planet_line(r, "Moon", "mind + dream sensitivity"),
        planet_line(r, "Ketu", "subconscious/spiritual dream karaka"),
    ]
    lines.append(f"Dream-sensitivity index: {_score(kundli)}/100.")
    return lines[:8]


def run_dreams_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_dreams_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="dreams_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Dream/subconscious axis active — intuitive dreams meaningful ho sakte hain",
        verdict_mid="Dream theme mixed — chart symbolic hints deta hai, over-fear mat karo",
        verdict_low="Night fear tone — Moon/8H/12H se anxiety dreams; grounding + rest help",
        summary=["QUESTION FOCUS: dreams symbolic tone — NO exact future event dates."],
        answer_plan="Use 9H/12H/8H + Moon + Ketu only.",
        wants_explain=wants_explain,
        score_key="dreams_score",
    )
