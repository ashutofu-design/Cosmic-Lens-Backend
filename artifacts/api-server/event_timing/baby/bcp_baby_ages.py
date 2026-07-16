"""BCP support ages for baby/children timing (D1 + D7 progeny axis).

BCP is a secondary age filter only. AD/PD activation remains the primary
window selector in ``baby_engine_v1``.
"""
from __future__ import annotations

from typing import Any, Optional

_SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
_SIGN_IDX = {
    "aries": 0, "taurus": 1, "gemini": 2, "cancer": 3, "leo": 4, "virgo": 5,
    "libra": 6, "scorpio": 7, "sagittarius": 8, "capricorn": 9,
    "aquarius": 10, "pisces": 11,
}
_EXTRA_ASPECTS = {"Mars": (4, 8), "Jupiter": (5, 9), "Saturn": (3, 10)}


def _sign_idx(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value % 12
    if isinstance(value, str):
        return _SIGN_IDX.get(value.strip().lower())
    return None


def _ages_for_house(house: int, max_age: int = 84) -> list[int]:
    return list(range(house, max_age + 1, 12)) if 1 <= house <= 12 else []


def _aspect_houses(planet: str, placement_house: int) -> list[int]:
    distances = (7,) + _EXTRA_ASPECTS.get(planet, ())
    return sorted({((placement_house + distance - 2) % 12) + 1 for distance in distances})


def _division_linkage(planets: list[dict], lagna_si: int) -> dict[str, Any]:
    fifth_lord = _SIGN_LORDS[(lagna_si + 4) % 12]
    lord_row = next((p for p in planets if str(p.get("name")) == fifth_lord), {})
    placement = lord_row.get("house")
    if not isinstance(placement, int):
        planet_si = _sign_idx(lord_row.get("sign_idx"))
        if planet_si is None:
            planet_si = _sign_idx(lord_row.get("sign"))
        placement = ((planet_si - lagna_si) % 12) + 1 if planet_si is not None else None
    houses = set()
    if isinstance(placement, int):
        houses.add(placement)
        houses.update(_aspect_houses(fifth_lord, placement))
    ages = sorted({age for house in houses for age in _ages_for_house(house)})
    return {
        "fifth_lord": fifth_lord,
        "fifth_lord_house": placement,
        "linkage_houses": sorted(houses),
        "activation_ages": ages,
    }


def compute_bcp_baby_ages(
    kundli: dict,
    d7_chart: Optional[dict],
    *,
    user_age: Optional[int] = None,
) -> dict[str, Any]:
    """Return D1/D7 BCP ages; shared ages are strongest secondary support."""
    d1_lagna = _sign_idx(kundli.get("ascendant"))
    if d1_lagna is None:
        d1_lagna = _sign_idx(kundli.get("lagnaSign"))
    d1 = _division_linkage(kundli.get("planets") or [], d1_lagna) if d1_lagna is not None else {}

    d7 = {}
    if isinstance(d7_chart, dict):
        d7_lagna = d7_chart.get("lagna_si")
        if isinstance(d7_lagna, int):
            d7 = _division_linkage(d7_chart.get("planets") or [], d7_lagna)

    d1_ages = set(d1.get("activation_ages") or [])
    d7_ages = set(d7.get("activation_ages") or [])
    shared = sorted(d1_ages & d7_ages)
    merged = sorted(d1_ages | d7_ages)
    if user_age is not None:
        shared = [age for age in shared if age >= user_age]
        merged = [age for age in merged if age >= user_age]
    return {
        "policy": "BCP secondary; AD/PD primary",
        "d1": d1,
        "d7": d7,
        "shared_priority_ages": shared[:8],
        "future_priority_ages": (shared + [a for a in merged if a not in shared])[:12],
        "next_activation_age": (shared or merged or [None])[0],
    }
