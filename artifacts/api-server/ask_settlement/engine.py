from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .settlement_registry import detect_settlement_archetype


def _score(kundli: dict) -> int:
    r = reader(kundli)
    score = 50
    for h in (9, 12):
        for occ in r.occupants(h) or []:
            if occ in {"Rahu", "Jupiter", "Moon"}:
                score += 6
            elif occ == "Saturn":
                score += 3
    rahu = r.planet("Rahu") or {}
    if rahu.get("house") and int(rahu["house"]) in (3, 9, 12):
        score += 8
    lord12 = r.house_lord(12)
    pl12 = r.planet(lord12) if lord12 else None
    if pl12 and pl12.get("house") and int(pl12["house"]) in (1, 4, 5, 9, 10, 11):
        score += 8
    return clamp_score(score)


def _evidence(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 12, "Foreign lands/settlement axis (12th house)"),
        house_axis(r, 9, "Fortune/distant lands axis (9th house)"),
        house_axis(r, 4, "Homeland roots axis (4th house)"),
        planet_line(r, "Rahu", "foreign/expansion karaka"),
        planet_line(r, "Jupiter", "fortune/support for distant move"),
    ]
    lines.append(f"Foreign-settlement index: {_score(kundli)}/100.")
    return lines[:8]


def run_settlement_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_settlement_archetype(question)).strip().lower()
    return gap_result(
        archetype=arch,
        slice_type="settlement_engine_v1",
        kundli=kundli,
        score=_score(kundli),
        evidence=_evidence(kundli),
        verdict_high="Foreign settlement yog supportive — 12H/9H + Rahu tone favour abroad life",
        verdict_mid="Settlement possible with effort — chart mixed; planning + paperwork discipline key",
        verdict_low="Abroad basna challenging tone — chart roots/visa hurdles suggest patience",
        summary=["QUESTION FOCUS: settlement suitability — NOT exact visa date."],
        answer_plan="12H + 9H + 4H + Rahu evidence only.",
        wants_explain=wants_explain,
        score_key="settlement_score",
    )
