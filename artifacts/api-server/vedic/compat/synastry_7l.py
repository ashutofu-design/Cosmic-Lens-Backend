"""
Phase 2.5.11.23 — 7L Synastry Engine
====================================
Deterministic cross-chart synastry: where does each partner's 7th-lord (the
"spouse karaka") sit in the OTHER partner's D1, and what does it touch?

This is the layer most apps never compute. It's the difference between
"tum dono ka match 24/36 hai" and "tumhara 7L girl ke Moon ko hit karta
hai — emotional pull strong rahega".

Outputs:
  - p1_7l_in_p2_chart: {sign, house_in_p2, planets_in_same_sign, planets_aspecting}
  - p2_7l_in_p1_chart: same shape
  - venus_overlay: each partner's Venus position vs other's lagna/7H/Moon
  - jupiter_overlay: same for Jupiter
  - nakshatra_resonance: shared nakshatra lords across key planets
  - score_0_10: synastry strength

Branding rule: never name AI/LLM. Defensive — never raises.
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
              "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
              "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
              "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
              "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
              "Uttara Bhadrapada", "Revati"]
NAK_LORDS_9 = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
               "Jupiter", "Saturn", "Mercury"]
NAK_EXTENT = 13.0 + 20.0 / 60.0
SPECIAL_ASPECT = {
    "Mars": [4, 7, 8], "Jupiter": [5, 7, 9], "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9], "Ketu": [5, 7, 9],
}
DEFAULT_ASPECT = [7]


def _sidx(sign: str | None) -> int | None:
    if isinstance(sign, str) and sign in SIGN_NAMES:
        return SIGN_NAMES.index(sign)
    return None


def _planets_map(kundli: dict) -> dict[str, dict]:
    """name → planet dict. Empty on bad input."""
    if not isinstance(kundli, dict):
        return {}
    out: dict[str, dict] = {}
    for p in kundli.get("planets") or []:
        if isinstance(p, dict) and isinstance(p.get("name"), str):
            out[p["name"]] = p
    return out


def _nak_lord(longitude: float | int | None) -> str | None:
    if not isinstance(longitude, (int, float)):
        return None
    nak_idx = int((longitude % 360) / NAK_EXTENT) % 27
    return NAK_LORDS_9[nak_idx % 9]


def _seventh_lord(kundli: dict) -> str | None:
    asc = kundli.get("ascendant") if isinstance(kundli, dict) else None
    a_idx = _sidx(asc)
    if a_idx is None:
        return None
    seventh_sign = SIGN_NAMES[(a_idx + 6) % 12]
    return SIGN_LORD[seventh_sign]


def _planet_in_other_chart(my_planet: str, other_kundli: dict) -> dict[str, Any]:
    """Find where my_planet (by name) — taken from MY chart but evaluated as a
    'transit' onto OTHER's chart — actually has no real meaning, BECAUSE
    classical synastry asks: where does OTHER's natal `my_planet` sit?
    NO. Re-read: the classical question is: my partner's 7L is X. Where
    does X sit IN MY natal chart? So we look up planet `X` (e.g. Venus) in
    `other_kundli`'s planets list and report its sign + house from other's
    lagna + which other-chart planets share that sign or aspect it.

    Returns: {sign, house, conjunctions: [], aspecting: []}
    """
    out: dict[str, Any] = {
        "available": False, "sign": None, "house": None,
        "conjunctions": [], "aspecting": [],
    }
    if not (isinstance(other_kundli, dict) and isinstance(my_planet, str)):
        return out
    pmap = _planets_map(other_kundli)
    target = pmap.get(my_planet)
    if not target:
        return out
    target_sign = target.get("sign")
    t_idx = _sidx(target_sign)
    if t_idx is None:
        return out

    # House from other's lagna
    o_asc_idx = _sidx(other_kundli.get("ascendant"))
    house = (((t_idx - o_asc_idx) % 12) + 1) if o_asc_idx is not None else None

    # Conjunctions: other-chart planets in same sign as target
    conjs = [n for n, p in pmap.items()
             if n != my_planet and _sidx(p.get("sign")) == t_idx]

    # Aspects onto target: other-chart planets whose Vedic aspect lands on t_idx
    aspecting: list[str] = []
    for n, p in pmap.items():
        if n == my_planet:
            continue
        s = _sidx(p.get("sign"))
        if s is None:
            continue
        houses = SPECIAL_ASPECT.get(n, DEFAULT_ASPECT)
        target_signs = {(s + (h - 1)) % 12 for h in houses}
        if t_idx in target_signs:
            aspecting.append(n)

    out["available"] = True
    out["sign"] = target_sign
    out["house"] = house
    out["conjunctions"] = conjs
    out["aspecting"] = aspecting
    return out


def _venus_jupiter_overlay(my_kundli: dict, other_kundli: dict, planet: str) -> dict[str, Any]:
    """Where does OTHER's `planet` (Venus or Jupiter) sit in MY chart, and
    what relationship-critical points (lagna, 7H, Moon) does it touch?"""
    out: dict[str, Any] = {
        "available": False, "house_in_my_chart": None, "touches": [],
    }
    if not (isinstance(my_kundli, dict) and isinstance(other_kundli, dict)):
        return out
    other_planet = _planets_map(other_kundli).get(planet)
    if not other_planet:
        return out
    o_idx = _sidx(other_planet.get("sign"))
    if o_idx is None:
        return out
    my_asc = _sidx(my_kundli.get("ascendant"))
    if my_asc is None:
        return out

    house = ((o_idx - my_asc) % 12) + 1
    touches: list[str] = []
    if house == 1:
        touches.append("my lagna")
    if house == 7:
        touches.append("my 7H (marriage house)")
    if house in {5, 9}:
        touches.append(f"my {house}H (love/dharma house)")
    # Moon hit
    my_moon = _planets_map(my_kundli).get("Moon")
    if my_moon:
        m_idx = _sidx(my_moon.get("sign"))
        if m_idx == o_idx:
            touches.append("my Moon (emotional resonance)")

    out["available"] = True
    out["house_in_my_chart"] = house
    out["touches"] = touches
    return out


def _nak_resonance(p1_kundli: dict, p2_kundli: dict) -> dict[str, Any]:
    """Count how many of {Sun, Moon, Venus, Mars, 7L} share a nakshatra LORD
    across charts. Each shared lord = karmic resonance."""
    out: dict[str, Any] = {"shared_lords": [], "count": 0, "details": []}
    p1_pl = _planets_map(p1_kundli)
    p2_pl = _planets_map(p2_kundli)
    keys = ["Sun", "Moon", "Venus", "Mars"]
    for k in keys:
        a = p1_pl.get(k)
        b = p2_pl.get(k)
        if not (a and b):
            continue
        la = _nak_lord(a.get("longitude"))
        lb = _nak_lord(b.get("longitude"))
        if la and lb and la == lb:
            out["shared_lords"].append(la)
            out["details"].append(f"Both {k} share star-lord {la}")
    out["count"] = len(out["shared_lords"])
    return out


def compute_synastry_7l(kundli_p1: dict, kundli_p2: dict) -> dict[str, Any]:
    """Full 7L synastry between two charts.

    Returns: {
      p1_7l, p2_7l,
      p1_7l_in_p2_chart, p2_7l_in_p1_chart,
      venus_overlay_p2_to_p1, venus_overlay_p1_to_p2,
      jupiter_overlay_p2_to_p1, jupiter_overlay_p1_to_p2,
      nakshatra_resonance,
      score_0_10,
      drivers, cautions,
    }
    Never raises.
    """
    p1_7l = _seventh_lord(kundli_p1)
    p2_7l = _seventh_lord(kundli_p2)
    cross_p1 = _planet_in_other_chart(p1_7l, kundli_p2) if p1_7l else {"available": False}
    cross_p2 = _planet_in_other_chart(p2_7l, kundli_p1) if p2_7l else {"available": False}

    venus_p2_to_p1 = _venus_jupiter_overlay(kundli_p1, kundli_p2, "Venus")
    venus_p1_to_p2 = _venus_jupiter_overlay(kundli_p2, kundli_p1, "Venus")
    jup_p2_to_p1 = _venus_jupiter_overlay(kundli_p1, kundli_p2, "Jupiter")
    jup_p1_to_p2 = _venus_jupiter_overlay(kundli_p2, kundli_p1, "Jupiter")

    nak = _nak_resonance(kundli_p1, kundli_p2)

    # Score 0-10
    score = 5.0
    drivers: list[str] = []
    cautions: list[str] = []

    for label, c in (("p1's 7L in p2", cross_p1), ("p2's 7L in p1", cross_p2)):
        if c.get("available") and c.get("house") in {1, 5, 7, 9, 11}:
            score += 0.75
            drivers.append(f"{label} sits in supportive house ({c['house']}H)")
        elif c.get("available") and c.get("house") in {6, 8, 12}:
            score -= 0.75
            cautions.append(f"{label} sits in challenging house ({c['house']}H)")

    for label, ov in (("p2's Venus on p1", venus_p2_to_p1),
                       ("p1's Venus on p2", venus_p1_to_p2)):
        if ov.get("available") and ov.get("touches"):
            score += 0.5 * min(2, len(ov["touches"]))
            drivers.append(f"{label} touches {', '.join(ov['touches'])}")

    for label, ov in (("p2's Jupiter on p1", jup_p2_to_p1),
                       ("p1's Jupiter on p2", jup_p1_to_p2)):
        if ov.get("available") and ov.get("touches"):
            score += 0.4 * min(2, len(ov["touches"]))
            drivers.append(f"{label} blesses {', '.join(ov['touches'])}")

    if nak["count"] >= 2:
        score += 1.0
        drivers.append(f"Strong nakshatra-lord resonance — {nak['count']} matches")
    elif nak["count"] == 1:
        score += 0.5
        drivers.append(f"Nakshatra-lord resonance — 1 match ({nak['shared_lords'][0]})")

    return {
        "available": bool(p1_7l and p2_7l),
        "p1_7l": p1_7l,
        "p2_7l": p2_7l,
        "p1_7l_in_p2_chart": cross_p1,
        "p2_7l_in_p1_chart": cross_p2,
        "venus_overlay_p2_to_p1": venus_p2_to_p1,
        "venus_overlay_p1_to_p2": venus_p1_to_p2,
        "jupiter_overlay_p2_to_p1": jup_p2_to_p1,
        "jupiter_overlay_p1_to_p2": jup_p1_to_p2,
        "nakshatra_resonance": nak,
        "score_0_10": max(0, min(10, round(score, 1))),
        "drivers": drivers,
        "cautions": cautions,
    }
