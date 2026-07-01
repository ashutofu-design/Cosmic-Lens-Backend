from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .parents_registry import detect_parents_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    for h in (4, 9, 10):
        for occ in r.occupants(h) or []:
            if occ in {"Jupiter", "Venus", "Moon"}:
                score += 5
            elif occ in {"Saturn", "Rahu", "Ketu", "Mars"}:
                score -= 4
    sun = r.planet("Sun") or {}
    moon = r.planet("Moon") or {}
    if sun.get("house") and int(sun["house"]) in (4, 9, 10, 1):
        score += 6
    if moon.get("house") and int(moon["house"]) in (4, 9, 10, 1):
        score += 6
    lord4 = r.house_lord(4)
    pl4 = r.planet(lord4) if lord4 else None
    if pl4 and pl4.get("house") and int(pl4["house"]) in (1, 4, 5, 7, 9, 10, 11):
        score += 8
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 4, "Mother/home/parents axis (4th house)"),
        house_axis(r, 9, "Father/dharma/blessings axis (9th house)"),
        house_axis(r, 10, "Authority/parent status axis (10th house)"),
        planet_line(r, "Sun", "father karaka (Surya)"),
        planet_line(r, "Moon", "mother karaka (Chandra)"),
        f"4L placement drives parent-home tone when 4H is mixed.",
    ]
    lines.append(f"Parent-bond index: {_score(kundli)}/100.")
    return lines[:9]


def run_parents_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_parents_archetype(question)).strip().lower()
    score = _score(kundli)
    return gap_result(
        archetype=arch,
        slice_type="parents_engine_v1",
        kundli=kundli,
        score=score,
        evidence=_evidence(kundli),
        verdict_high="Parents axis supportive — 4H/9H + Sun/Moon tone favour guidance aur respect",
        verdict_mid="Parent bond mixed — support hai par generation gap / distance bhi",
        verdict_low="Parent axis me strain tone — seva + patience + clear communication help",
        summary=["QUESTION FOCUS: parents relationship — NOT parent health/bimari."],
        answer_plan="Use 4H/9H/10H + Sun/Moon + 4L evidence only.",
        wants_explain=wants_explain,
        score_key="parents_score",
    )
