from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .fame_registry import detect_fame_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    sun = r.planet("Sun") or {}
    rahu = r.planet("Rahu") or {}
    if sun.get("house") and int(sun["house"]) in (1, 5, 10):
        score += 10
    if rahu.get("house") and int(rahu["house"]) in (1, 5, 10, 11):
        score += 8
    for h in (1, 5, 10):
        for occ in r.occupants(h) or []:
            if occ in {"Sun", "Rahu", "Jupiter"}:
                score += 5
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 1, "Self/public personality axis (1st house)"),
        house_axis(r, 5, "Creativity/recognition axis (5th house)"),
        house_axis(r, 10, "Career/fame/karma axis (10th house)"),
        planet_line(r, "Sun", "authority/visibility karaka"),
        planet_line(r, "Rahu", "mass fame/unconventional spotlight karaka"),
    ]
    lines.append(f"Fame-recognition index: {_score(kundli)}/100.")
    return lines[:8]


def run_fame_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_fame_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="fame_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Fame/recognition yog supportive — 1H/5H/10H + Sun/Rahu active",
        verdict_mid="Public image mixed — visibility aayegi par consistency chahiye",
        verdict_low="Mass fame tone modest — chart niche recognition + slow build suggest karta hai",
        summary=["QUESTION FOCUS: fame/reputation — NOT exact viral date."],
        answer_plan="1H + 5H + 10H + Sun + Rahu only.",
        wants_explain=wants_explain,
        score_key="fame_score",
    )
