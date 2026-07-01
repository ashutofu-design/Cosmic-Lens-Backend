from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .charity_registry import detect_charity_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 52
    jup = r.planet("Jupiter") or {}
    if jup.get("house") and int(jup["house"]) in (1, 4, 5, 9, 10, 11, 12):
        score += 10
    for h in (5, 9, 12):
        for occ in r.occupants(h) or []:
            if occ in {"Jupiter", "Moon", "Venus"}:
                score += 4
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 9, "Dharma/charity axis (9th house)"),
        house_axis(r, 12, "Letting-go/seva axis (12th house)"),
        house_axis(r, 5, "Purva punya axis (5th house)"),
        planet_line(r, "Jupiter", "daan/dharma karaka (Guru)"),
    ]
    lines.append(f"Charity/punya index: {_score(kundli)}/100.")
    return lines[:7]


def run_charity_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_charity_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="charity_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Daan/punya path strong — 9H/Jupiter favour selfless giving",
        verdict_mid="Charity helpful — chart mixed; steady small seva better than show",
        verdict_low="Charity with discipline — pehle stability, phir structured daan",
        summary=["QUESTION FOCUS: charity/punya tone — humble practical line."],
        answer_plan="9H + 12H + 5H + Jupiter only.",
        wants_explain=wants_explain,
        score_key="charity_score",
    )
