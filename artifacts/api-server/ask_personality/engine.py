from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from vedic.love_reality.scoring_core import SIGNS
from .personality_registry import detect_personality_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 52
    asc = kundli.get("ascendant") or ""
    if asc:
        score += 4
    moon = r.planet("Moon") or {}
    sun = r.planet("Sun") or {}
    if moon.get("house") and int(moon["house"]) in (1, 4, 5, 7, 9, 10, 11):
        score += 8
    if sun.get("house") and int(sun["house"]) in (1, 5, 9, 10):
        score += 6
    venus = r.planet("Venus") or {}
    if venus.get("house") and int(venus["house"]) in (1, 2, 4, 7, 11):
        score += 6
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    asc_i = r.asc_index()
    asc_sign = SIGNS[asc_i] if isinstance(asc_i, int) else (kundli.get("ascendant") or "?")
    lord1 = r.house_lord(1)
    pl1 = r.planet(lord1) if lord1 else {}
    lines = [
        f"Lagna/Ascendant: {asc_sign} — core personality shell.",
        f"1L {lord1 or '?'} in H{pl1.get('house') or '?'} sign {pl1.get('sign') or '?'} — self-expression style.",
        house_axis(r, 1, "Self/body/appearance axis (1st house)"),
        planet_line(r, "Moon", "mind + emotional nature"),
        planet_line(r, "Sun", "ego + vitality tone"),
        planet_line(r, "Venus", "charm/appearance karaka"),
    ]
    lines.append(f"Self-personality index: {_score(kundli)}/100.")
    return lines[:9]


def run_personality_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_personality_archetype(question)).strip().lower()
    score = _score(kundli)
    return gap_result(
        archetype=arch,
        slice_type="personality_engine_v1",
        kundli=kundli,
        score=score,
        evidence=_evidence(kundli),
        verdict_high="Personality/appearance axis strong — lagna + Moon/Venus supportive",
        verdict_mid="Personality mixed — strengths aur blind spots dono chart me",
        verdict_low="Self-expression me effort chahiye — chart patience + self-work suggest karta hai",
        summary=["QUESTION FOCUS: native self only — NOT spouse/in-laws."],
        answer_plan="Use lagna + 1L + Moon + Venus; do NOT drift to 7H marriage.",
        wants_explain=wants_explain,
        score_key="personality_score",
    )
