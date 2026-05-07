"""
event_timing/_shared/double_transit.py
=======================================
COSMIC LENS — UNIVERSAL DOUBLE-TRANSIT CHECKER (K.N.Rao classical rule)

Phase 2.5.11.15 (May 7 2026) — promoted from baby_engine_v1 STEP 6 into a
generic, engine-agnostic helper usable by ANY timing engine (health,
finance, marriage, baby, travel, career, ...) for ANY date (past, present,
future).

USER MANDATE (recorded in replit.md preferences):
  > "Jab bhi event prediction ki baat aayega — yani timing ki baat aayega
  > — future ho present ho ya past ('kab hoga / kab gaya tha / kab jaaunga'),
  > to hamesha ek chiz dhyan rakhna he: Jupiter+Sani ka double transit
  > lagu hoga yeh COMPULSORY he, concerned house aur concerned house lords
  > ke upar."

CLASSICAL RULE (K.N.Rao Double Transit Theory):
  For an event to FRUCTIFY at a given date, BOTH Jupiter AND Saturn
  must — at that date — either OCCUPY or ASPECT either:
    (a) the concerned bhava (house from lagna), OR
    (b) the concerned bhava-LORD's natal sign.

  Strength tiers:
    STRONG    — both J+S each touch (house OR lord) of >=1 concern house
    PARTIAL_J — only Jupiter touches concern axis
    PARTIAL_S — only Saturn touches concern axis
    ABSENT    — neither touches

ASPECT MODEL (Vedic full-strength aspects):
  Jupiter:  5th, 7th, 9th from itself
  Saturn:   3rd, 7th, 10th from itself
  (Occupation = 1st-from-self; counted as "touch")

OUTPUT (returned dict):
  {
    "as_of_utc":          ISO datetime,
    "concern_houses":     [int, ...],
    "jupiter": {"sign_idx": int, "sign_name": str, "house_from_lagna": int,
                 "touches": [{"house": int, "via": "occupy"|"aspect"|"lord"}]},
    "saturn":  same shape,
    "verdict":            "STRONG" | "PARTIAL_J" | "PARTIAL_S" | "ABSENT",
    "active":             bool   (verdict == "STRONG"),
    "anchors":            [str, ...]   (human-readable trigger reasons),
    "score":              0..100        (continuous strength)
  }

If swisseph is unavailable or the chart is malformed, returns:
  {"verdict": "UNAVAILABLE", "active": False, "score": 0,
   "note": "swisseph unavailable" | reason}
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import swisseph as swe  # type: ignore
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    _HAS_SWE = True
except Exception:
    _HAS_SWE = False
    swe = None  # type: ignore
    _SWE_FLAGS = 0


_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

_SIGN_LORDS: Dict[int, str] = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

# Vedic full-strength aspects (1st = occupation; rest = drishti)
_JUPITER_ASPECTS = (1, 5, 7, 9)   # 5/7/9 from self
_SATURN_ASPECTS  = (1, 3, 7, 10)  # 3/7/10 from self


def _planet_sign_at(planet_id: int, when: datetime) -> Optional[int]:
    """Return sidereal sign_idx (0..11) of `planet_id` at UT `when`."""
    if not _HAS_SWE:
        return None
    try:
        jd = swe.julday(when.year, when.month, when.day,
                         when.hour + when.minute / 60.0)
        result = swe.calc_ut(jd, planet_id, _SWE_FLAGS)
        lon = float(result[0][0]) % 360.0
        return int(lon // 30) % 12
    except Exception:
        return None


def _planet_natal_sign(planets_d1: List[Dict[str, Any]],
                        pname: str) -> Optional[int]:
    """Look up natal sign_idx of `pname` from the D1 planets list."""
    for p in planets_d1 or []:
        if isinstance(p, dict) and p.get("name") == pname:
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            sign = p.get("sign")
            if isinstance(sign, str) and sign in _SIGNS:
                return _SIGNS.index(sign)
    return None


def _house_lord(lagna_si: int, house: int) -> str:
    sign_at_house = (lagna_si + house - 1) % 12
    return _SIGN_LORDS[sign_at_house]


def _house_of_sign(sign_si: int, lagna_si: int) -> int:
    return ((sign_si - lagna_si) % 12) + 1


def _aspects_house(planet_sign_si: int, target_house: int,
                    lagna_si: int, aspect_offsets) -> bool:
    """True if a planet sitting in `planet_sign_si` aspects `target_house`
    (whole-sign Vedic aspects). Includes occupation (offset 1).

    Phase 2.5.11.15-c BUG FIX: previous formula
      `((planet_house + off - 1) % 12) + 1`
    was off-by-one — houses are 1-indexed but the modular math treated
    them as 0-indexed. Example: Jupiter in H7, 5th aspect (off=5) returned
    H12 instead of the correct H11 (count 5 inclusive from H7: 7,8,9,10,11).
    Correct formula subtracts 1 first to convert 1-indexed→0-indexed,
    adds the inclusive offset (off-1), then converts back."""
    planet_house = _house_of_sign(planet_sign_si, lagna_si)
    return any(((planet_house - 1 + off - 1) % 12) + 1 == target_house
                for off in aspect_offsets)


def _aspects_sign(planet_sign_si: int, target_sign_si: int,
                   aspect_offsets) -> bool:
    """True if planet in `planet_sign_si` aspects `target_sign_si`."""
    return any((planet_sign_si + (off - 1)) % 12 == target_sign_si
                for off in aspect_offsets)


def check_double_transit(kundli: Dict[str, Any],
                          target_date: datetime,
                          lagna_si: int,
                          planets_d1: List[Dict[str, Any]],
                          concern_houses: List[int]) -> Dict[str, Any]:
    """K.N.Rao Double Transit check at `target_date` for `concern_houses`.

    Args:
      kundli:         full chart dict (kept for future use; currently unused
                      since we re-compute J/S sky positions from swisseph)
      target_date:    UT datetime — past, present, or future
      lagna_si:       natal lagna sign_idx (0..11)
      planets_d1:     list of natal D1 planet dicts (need name + sign_idx)
      concern_houses: list of house numbers (1..12) relevant to the engine
                      (e.g. travel=[3,9,12], health=[1,6,8,12],
                       finance=[2,5,9,11], marriage=[7], baby=[5,11])

    Returns:
      dict per module docstring (verdict / score / anchors / per-planet detail)
    """
    out: Dict[str, Any] = {
        "as_of_utc":      target_date.isoformat(),
        "concern_houses": list(concern_houses),
        "jupiter":        None,
        "saturn":         None,
        "verdict":        "UNAVAILABLE",
        "active":         False,
        "anchors":        [],
        "score":          0,
    }

    if not _HAS_SWE:
        out["note"] = "swisseph unavailable"
        return out

    if not concern_houses:
        out["note"] = "no concern_houses provided"
        return out

    jup_si = _planet_sign_at(swe.JUPITER, target_date)
    sat_si = _planet_sign_at(swe.SATURN,  target_date)
    if jup_si is None or sat_si is None:
        out["note"] = "ephemeris lookup failed"
        return out

    # Pre-compute concern house signs + concern lord natal signs.
    house_signs: Dict[int, int] = {}
    lord_signs: Dict[int, Dict[str, Any]] = {}
    for h in concern_houses:
        if not isinstance(h, int) or h < 1 or h > 12:
            continue
        house_signs[h] = (lagna_si + h - 1) % 12
        lord = _house_lord(lagna_si, h)
        lord_signs[h] = {
            "lord":      lord,
            "natal_si":  _planet_natal_sign(planets_d1, lord),
        }

    def _scan(planet_name: str, planet_sign_si: int,
                aspect_offsets) -> Dict[str, Any]:
        touches: List[Dict[str, Any]] = []
        for h, h_si in house_signs.items():
            # House touched directly?
            if _aspects_house(planet_sign_si, h, lagna_si, aspect_offsets):
                touches.append({"house": h, "via": "house"})
            # Or the house-LORD's natal sign?
            llord = lord_signs[h]
            if (llord["natal_si"] is not None
                and _aspects_sign(planet_sign_si, llord["natal_si"],
                                    aspect_offsets)):
                touches.append({
                    "house": h, "via": "lord",
                    "lord":  llord["lord"],
                })
        return {
            "sign_idx":          planet_sign_si,
            "sign_name":         _SIGNS[planet_sign_si],
            "house_from_lagna":  _house_of_sign(planet_sign_si, lagna_si),
            "touches":           touches,
        }

    out["jupiter"] = _scan("Jupiter", jup_si, _JUPITER_ASPECTS)
    out["saturn"]  = _scan("Saturn",  sat_si, _SATURN_ASPECTS)

    jup_hits = bool(out["jupiter"]["touches"])
    sat_hits = bool(out["saturn"]["touches"])

    # Anchors (human-readable)
    anchors: List[str] = []
    for t in out["jupiter"]["touches"]:
        if t["via"] == "house":
            anchors.append(f"Jupiter→H{t['house']}")
        else:
            anchors.append(f"Jupiter→{t['lord']} (lord of H{t['house']})")
    for t in out["saturn"]["touches"]:
        if t["via"] == "house":
            anchors.append(f"Saturn→H{t['house']}")
        else:
            anchors.append(f"Saturn→{t['lord']} (lord of H{t['house']})")
    out["anchors"] = anchors

    # Verdict + score
    if jup_hits and sat_hits:
        out["verdict"] = "STRONG"
        out["active"]  = True
        # Both touch — base 70, +10 each "house+lord" combo per concern.
        score = 70
        for h in concern_houses:
            j_house = any(t["house"] == h and t["via"] == "house"
                            for t in out["jupiter"]["touches"])
            j_lord  = any(t["house"] == h and t["via"] == "lord"
                            for t in out["jupiter"]["touches"])
            s_house = any(t["house"] == h and t["via"] == "house"
                            for t in out["saturn"]["touches"])
            s_lord  = any(t["house"] == h and t["via"] == "lord"
                            for t in out["saturn"]["touches"])
            if (j_house or j_lord) and (s_house or s_lord):
                score += 10  # both planets touch the SAME concern house
            if (j_house and s_house):
                score += 5   # both on the actual house (not just lord)
        out["score"] = min(score, 100)
    elif jup_hits:
        out["verdict"] = "PARTIAL_J"
        out["score"]   = 35
    elif sat_hits:
        out["verdict"] = "PARTIAL_S"
        out["score"]   = 30
    else:
        out["verdict"] = "ABSENT"
        out["score"]   = 0

    return out


# ════════════════════════════════════════════════════════════════════════
# Concern-house presets per engine (single source of truth)
# ════════════════════════════════════════════════════════════════════════
CONCERN_HOUSES = {
    "travel":   [3, 9, 12],
    "health":   [1, 6, 8, 12],
    "finance":  [2, 5, 9, 11],
    "marriage": [7, 2, 8, 11],
    "baby":     [5, 11],
    "career":   [10, 6, 2, 11],
}


def midpoint(start: datetime, end: datetime) -> datetime:
    """Return midpoint UT datetime of [start, end] — for past/future window
    double-transit checks."""
    return start + (end - start) / 2
