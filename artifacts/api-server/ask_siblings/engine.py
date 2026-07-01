from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, occupants_detail, planet_line, reader
from .siblings_registry import detect_siblings_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    for h in (3, 11):
        for occ in r.occupants(h) or []:
            if occ in {"Jupiter", "Venus", "Mercury", "Moon"}:
                score += 6
            elif occ in {"Saturn", "Rahu", "Ketu"}:
                score -= 5
    mars = r.planet("Mars") or {}
    mh = mars.get("house")
    if mh and int(mh) in (3, 11):
        score += 8
    elif mh and int(mh) in (6, 8, 12):
        score -= 6
    for h in (3, 11):
        lord = r.house_lord(h)
        pl = r.planet(lord) if lord else None
        if pl and pl.get("house") and int(pl["house"]) in (1, 4, 5, 7, 9, 10, 11):
            score += 5
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 3, "Siblings/courage axis (3rd house)"),
        house_axis(r, 11, "Elder siblings/gains axis (11th house)"),
        *occupants_detail(r, 3, "3H occupant"),
        *occupants_detail(r, 11, "11H occupant"),
        planet_line(r, "Mars", "sibling karaka (Mangal)"),
    ]
    score = _score(kundli)
    lines.append(f"Sibling-bond index: {score}/100.")
    return lines[:9]


def run_siblings_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    from ask_mr.types import EngineResult  # noqa: F401

    arch = (archetype or detect_siblings_archetype(question)).strip().lower()
    score = _score(kundli)
    return gap_result(
        archetype=arch,
        slice_type="siblings_engine_v1",
        kundli=kundli,
        score=score,
        evidence=_evidence(kundli),
        verdict_high="Bhai-behen axis supportive — 3H/11H + Mars tone favour cordial bond",
        verdict_mid="Sibling bond mixed — closeness aur friction dono phases possible",
        verdict_low="Sibling axis me distance/tension tone — patience aur boundaries zaroori",
        summary=[
            "QUESTION FOCUS: siblings only — NOT spouse/children.",
            "MUST cite 3H + 11H + Mars + occupants.",
        ],
        answer_plan="Answer from 3H/11H occupants + Mars + 3L/11L only.",
        wants_explain=wants_explain,
        score_key="siblings_score",
    )
