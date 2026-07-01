from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, occupants_detail, planet_line, reader
from .enemies_registry import detect_enemies_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    for occ in r.occupants(6) or []:
        if occ in {"Saturn", "Mars", "Rahu", "Ketu"}:
            score -= 8
        elif occ in {"Jupiter", "Venus"}:
            score += 4
    mars = r.planet("Mars") or {}
    sat = r.planet("Saturn") or {}
    if mars.get("house") and int(mars["house"]) in (6, 8, 12):
        score -= 8
    if sat.get("house") and int(sat["house"]) in (6, 8, 12):
        score -= 6
    lord6 = r.house_lord(6)
    pl6 = r.planet(lord6) if lord6 else None
    if pl6 and pl6.get("house") and int(pl6["house"]) in (6, 8, 12):
        score -= 10
    elif pl6 and pl6.get("house") and int(pl6["house"]) in (1, 4, 5, 9, 10, 11):
        score += 8
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 6, "Enemies/obstacles axis (6th house)"),
        house_axis(r, 8, "Hidden threats/crisis axis (8th house)"),
        *occupants_detail(r, 6, "6H occupant"),
        planet_line(r, "Mars", "conflict/aggression karaka"),
        planet_line(r, "Saturn", "persistent opposition karaka"),
    ]
    lines.append(f"Enemy-pressure index: {_score(kundli)}/100 (lower = more pressure).")
    return lines[:9]


def run_enemies_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_enemies_archetype(question)).strip().lower()
    score = _score(kundli)
    return gap_result(
        archetype=arch,
        slice_type="enemies_engine_v1",
        kundli=kundli,
        score=score,
        evidence=_evidence(kundli),
        verdict_high="Shatru pressure manageable — 6L/6H tone controlled, strategy se handle ho sakta hai",
        verdict_mid="Enemy/obstacle tone mixed — competitors hain par chart defence bhi deta hai",
        verdict_low="Shatru axis active — boundaries, legal hygiene aur calm strategy zaroori",
        summary=["QUESTION FOCUS: general enemies — NOT court case, NOT friend circle."],
        answer_plan="Use 6H + 6L + Mars + Saturn only.",
        wants_explain=wants_explain,
        score_key="enemies_score",
    )
