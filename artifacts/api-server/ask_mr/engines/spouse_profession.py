from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader, SIGNS

from ..types import EngineResult


def _house_sign_and_lord(reader: KundliReader, house: int) -> tuple[str, str]:
    asc_i = reader.asc_index()
    sign = SIGNS[(asc_i + house - 1) % 12]
    lord = reader.house_lord(house)
    return sign, lord


def run_spouse_profession(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    # Deterministic Vedic heuristic: spouse profession = 10th from 7th = 4th house.
    # Additional support: 8th (2nd from spouse), 12th (6th from spouse), 5th (11th from spouse).
    focus_houses = [
        ("profession axis (10th from spouse)", 4),
        ("income style (2nd from spouse)", 8),
        ("service/workload (6th from spouse)", 12),
        ("gains/network (11th from spouse)", 5),
    ]

    evidence: list[str] = []
    for label, h in focus_houses:
        sign, lord = _house_sign_and_lord(r, h)
        pl = r.planet(lord) or {}
        lord_house = pl.get("house")
        lord_sign = pl.get("sign")
        occ = r.occupants(h)
        evidence.append(
            f"{label}: house {h} sign {sign}; lord {lord} placed in house {lord_house} sign {lord_sign}; "
            f"occupants={occ or 'none'}."
        )

    verdict = "Spouse profession: pattern read from spouse-profession axis (not a fixed job title)"

    return EngineResult(
        archetype="spouse_profession",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 65,
        answer_plan="2–3 sentences: broad field vibe → why → soft caveat (not exact title).",
        summary=[
            "Do not output exact job title; give broad direction (service/tech/management/creative).",
        ],
        evidence=evidence[:8],
        ignore=[
            "timing dates/windows",
            "breakup prediction",
            "manglik (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "spouse_profession",
        },
    )

