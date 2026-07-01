from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .wellness_registry import detect_wellness_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    moon = r.planet("Moon") or {}
    if moon.get("house") and int(moon["house"]) in (12, 6, 8):
        score -= 8
    elif moon.get("house") and int(moon["house"]) in (1, 4, 5, 7, 9, 10, 11):
        score += 6
    for h in (2, 6, 12):
        for occ in r.occupants(h) or []:
            if occ in {"Moon", "Venus", "Mercury"}:
                score += 3
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 12, "Sleep/rest/subconscious axis (12th house)"),
        house_axis(r, 2, "Food/intake habits axis (2nd house)"),
        house_axis(r, 6, "Digestion/routine axis (6th house)"),
        planet_line(r, "Moon", "sleep + appetite sensitivity"),
    ]
    lines.append(f"Wellness-routine index: {_score(kundli)}/100.")
    return lines[:7]


def run_wellness_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_wellness_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="wellness_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Sleep/food routine supportive — Moon + 2H/12H tone balanced",
        verdict_mid="Routine mixed — chart irregular sleep/appetite phases suggest karta hai",
        verdict_low="Rest/diet discipline needed — 12H/6H stress; routine + doctor if chronic",
        summary=["QUESTION FOCUS: sleep/food habits — NOT disease diagnosis."],
        answer_plan="12H + 2H + 6H + Moon only.",
        wants_explain=wants_explain,
        score_key="wellness_score",
    )
