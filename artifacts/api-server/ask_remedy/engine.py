from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .remedy_registry import detect_remedy_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 55
    jup = r.planet("Jupiter") or {}
    if jup.get("house") and int(jup["house"]) in (1, 4, 5, 9, 10, 11):
        score += 10
    lord9 = r.house_lord(9)
    if lord9:
        pl9 = r.planet(lord9) or {}
        if pl9.get("house") and int(pl9["house"]) in (6, 8, 12):
            score -= 6
        else:
            score += 6
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lord9 = r.house_lord(9)
    pl9 = r.planet(lord9) if lord9 else {}
    lines = [
        house_axis(r, 9, "Remedy/dharma axis (9th house)"),
        planet_line(r, "Jupiter", "primary remedy/grace karaka (Guru)"),
        f"9L {lord9 or '?'} in H{pl9.get('house') or '?'} — anchor for gemstone/day/upay hints.",
        planet_line(r, "Saturn", "karmic remedy discipline karaka"),
    ]
    lines.append("Weak/afflicted graha note: suggest strengthening 9L + Jupiter tone, not random gems.")
    lines.append(f"Remedy-support index: {_score(kundli)}/100.")
    return lines[:8]


def run_remedy_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_remedy_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="remedy_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Remedy path clear — 9H/Jupiter supportive; chart-based upay/ratn direction safe",
        verdict_mid="Remedy mixed — gentle mantra/daan + discipline better than heavy gemstone jump",
        verdict_low="Remedy caution — consult qualified pandit before ratn; chart shows karmic patience need",
        summary=["QUESTION FOCUS: remedy hints from chart — NO guaranteed miracle claims."],
        answer_plan="9H + 9L + Jupiter; modest practical upay only.",
        wants_explain=wants_explain,
        score_key="remedy_score",
        ignore=["guaranteed cure", "fear-based selling", "exact carat claims"],
    )
