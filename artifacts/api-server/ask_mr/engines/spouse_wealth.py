from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader, SIGNS

from ..types import EngineResult


def _house_sign_and_lord(reader: KundliReader, house: int) -> tuple[str, str]:
    asc_i = reader.asc_index()
    sign = SIGNS[(asc_i + house - 1) % 12]
    lord = reader.house_lord(house)
    return sign, lord


def run_spouse_wealth(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    # Spouse wealth axis: 2nd from 7th = 8H, gains from spouse = 11th from 7th = 5H, spouse bank = 8th from 7th = 2H
    axes = [
        ("spouse wealth / shared resources (2nd from spouse)", 8),
        ("spouse financial strength (8th from spouse)", 2),
        ("gains through spouse (11th from spouse)", 5),
    ]

    evidence: list[str] = []
    jup = r.planet("Jupiter") or {}
    ven = r.planet("Venus") or {}
    if jup:
        evidence.append(
            f"Jupiter (prosperity karaka) in house {jup.get('house')} sign {jup.get('sign')} — overall abundance tone."
        )
    if ven:
        evidence.append(
            f"Venus (comfort/wealth tone) in house {ven.get('house')} sign {ven.get('sign')} — lifestyle comfort marker."
        )

    for label, h in axes:
        sign, lord = _house_sign_and_lord(r, h)
        pl = r.planet(lord) or {}
        occ = r.occupants(h)
        evidence.append(
            f"{label}: house {h} sign {sign}; lord {lord} in house {pl.get('house')} sign {pl.get('sign')}; "
            f"occupants={occ or 'none'}."
        )

    verdict = "Spouse wealth / financial comfort: pattern from spouse-wealth houses (not exact income figure)"

    return EngineResult(
        archetype="spouse_wealth",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="2–3 sentences: comfort level → 1–2 reasons → no exact salary promise.",
        summary=[
            "Give broad comfort/prosperity tone — stable, moderate, or mixed.",
            "Do NOT quote exact salary or net worth.",
            "NO shayad/ho sakta hai/lagta hai.",
        ],
        evidence=evidence[:6],
        ignore=["timing dates/windows", "exact income number", "job title"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "spouse_wealth",
        },
    )
