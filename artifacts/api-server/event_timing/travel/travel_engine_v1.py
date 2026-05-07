"""
event_timing/travel/travel_engine_v1.py
========================================
COSMIC LENS TRAVEL TIMING ENGINE v1.0 — clean build, mirrors
Health v1 / Marriage v2.4 / Finance v1 architecture.

Architecture: FILTER → VERIFY → ACTIVATE → TRIGGER (9-step pipeline,
locked May 7 2026 per user spec "traveling ke liye engine foreign
travel ke sath kab travel event ho sakta he timing wala same
structure").

  STEP 1   D1 travel-significator filter            (FILTER)
           - 3L  (short trips, courage to move)
           - 9L  (long-distance, dharma, pilgrimage, higher learning)
           - 12L (FOREIGN — settlement, distant lands, expense abroad)
           - 7L  (away-from-home, business travel, partnerships abroad)
           - 4L  (HOME — INVERTED: weak/afflicted 4L → relocation)
           - Occupants of 3 / 9 / 12
           - Planets ASPECTING the 9th house (long-travel activation)
           - Karakas: Rahu (foreign/sudden), Moon (movement/water-travel),
             Mercury (short trips/communication), Jupiter (sacred travel,
             visa-luck), Saturn (long arduous), Venus (luxury/leisure)
  STEP 2   D9 dignity verification                  (VERIFY)
  STEP 3   D4 Chaturthamsha (residence/foreign-shift) (VERIFY)
           Parashara: D4 governs residence + property + place-of-living.
           A 12L / 9L landing in 1H/4H of D4 → relocation likely.
  STEP 3.5 KP CSL of 3, 9 & 12 cusps
  STEP 4   Weighted ranking
           D1·30 + D9·20 + D4·25 + KP·15 + karaka·10
  STEP 5   Dasha activation (AD/PD primary; MD low-weight)
           AD=5, PD=6, MD=1. Signed contribution: pure travel-promoter
           (12L/9L/Rahu) raises travel score; pure home-anchor (4L
           strong) lowers it.
  STEP 6   Transit triggers
           Jupiter over 9/12 (visa-luck, sacred journey),
           Saturn over 12 (delayed/long-stay abroad / drain),
           Saturn over 4 (uprooted from home),
           Rahu over 9 (sudden long journey) or 12 (foreign-shift),
           Ketu over 4 (detachment from home),
           Mars over 3/9 (impulsive trip / accident risk),
           Sade Sati on Moon (relocation pressure)
  STEP 7   Ashtakavarga support
           SAV bindus on 9H + 12H (foreign strength)
  STEP 8   KP cuspal sub lord of 12 (foreign verdict)
  STEP 9   Yoga + hard-guard layer
           POSITIVE: Tirtha (sacred-travel), Foreign-Settlement
           (12L↔9L exchange / Rahu in 12), Vidya-Yatra (9L+5L for
           study-abroad), Travel-Yoga (3L+12L exchange)
           NEGATIVE: Sthanabhrama (no movement — 4L strong + 12L
           combust), Visa-Block (Ketu in 9H + Saturn aspect on 12H),
           Risk-Travel (Mars+Rahu in 3/9/12 — accident/legal-trouble)

Public function:
  compute_travel_window(kundli, intel, kp, birth) -> dict

Output dict (back-compat with health/finance-style consumers):
  {
    "verdict":              "TRAVEL_PROMISED" | "FAVORABLE" |
                            "LOW_PROBABILITY" | "HIGH_RISK_TRAVEL" |
                            "UNKNOWN",
    "band":                 "WEAK" | "MEDIUM" | "STRONG",
    "foreign_promised":     bool,
    "current_window":       {start_iso, end_iso, severity, triggers[]},
    "next_3_windows":       [{md, ad, pd, score, severity, window,
                              start_iso, end_iso, kind}],
    "protection_windows":   [{md, ad, pd, window, start_iso, end_iso}],
    "affected_areas":       ["foreign_settlement", "study_abroad",
                              "business_travel", ...],
    "recommendation_tier":  "watchful" | "supportive" |
                            "celebratory" | "consult",
    "top_travel_planets":   [{name, score, d1, d9, d4, kp, karaka,
                               significations[]}],
    "weighted_breakdown":   {planet: {d1, d9, d4, kp, karaka, total}},
    "kp_layer":             {csl_3, csl_9, csl_12, verdict_3,
                              verdict_9, verdict_12},
    "transits":             {saturn, rahu, ketu, mars, jupiter,
                              sade_sati, active_triggers[]},
    "ashtakavarga":         {sav_9, sav_12, foreign_band},
    "yogas":                [{name, severity, planets}],
    "risk_flags":           [str],
    "factors":              [str],
    "llm_directives":       [str],
    "remedies":             {...},
    "engine_version":       "v1.0.0",
    "engine_arch":          "FILTER→VERIFY→KP-GATE→ACTIVATE→TRIGGER",
  }

Hard guards (per user policy + replit.md):
  - Mandatory TRAVEL_DISCLAIMER (visa/legal outcome cannot be
    guaranteed by astrology)
  - NO_GUARANTEED_VISA_OUTCOME / NO_GUARANTEED_TRAVEL_DATE
  - NO_DESTINATION_NAMING (engine never names a specific country/city)
  - 3-confirmation rule for `consult` tier (high-risk travel windows)
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Thread-local cache for the most recent engine result.
_LAST_RESULT = threading.local()


def get_last_travel_result() -> Optional[Dict[str, Any]]:
    return getattr(_LAST_RESULT, "value", None)


def _store_last_result(result: Dict[str, Any]) -> None:
    _LAST_RESULT.value = result


def clear_last_travel_result() -> None:
    if hasattr(_LAST_RESULT, "value"):
        _LAST_RESULT.value = None


# ── External helpers ──
try:
    from divisional_charts import compute_d9  # type: ignore
except Exception:
    compute_d9 = None  # type: ignore

try:
    # D4 (Chaturthamsha) — residence chart. Optional; may not exist.
    from divisional_charts import compute_d4  # type: ignore
except Exception:
    compute_d4 = None  # type: ignore

try:
    from ashtakavarga import compute_ashtakavarga  # type: ignore
except Exception:
    compute_ashtakavarga = None  # type: ignore

try:
    import swisseph as swe  # type: ignore
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    _HAS_SWE = True
except Exception:
    _HAS_SWE = False
    swe = None  # type: ignore
    _SWE_FLAGS = 0


# ════════════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════════════
_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_SIGN_IDX = {s: i for i, s in enumerate(_SIGNS)}

_SIGN_LORDS: Dict[int, str] = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

_EXALT: Dict[str, int] = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
                           "Jupiter": 3, "Venus": 11, "Saturn": 6}
_DEBIL: Dict[str, int] = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
                           "Jupiter": 9, "Venus": 5, "Saturn": 0}

_OWN_SIGNS: Dict[str, Set[int]] = {
    "Sun":     {4},
    "Moon":    {3},
    "Mars":    {0, 7},
    "Mercury": {2, 5},
    "Jupiter": {8, 11},
    "Venus":   {1, 6},
    "Saturn":  {9, 10},
}

# Travel-significant houses
_TRAVEL_HOUSES  = [3, 9, 12]   # short / long / foreign
_FOREIGN_HOUSES = [9, 12]      # foreign-residence emphasis
_HOME_HOUSES    = [4]          # anchor — inverted role

_WEIGHT_D1     = 0.30
_WEIGHT_D9     = 0.20
_WEIGHT_D4     = 0.25
_WEIGHT_KP     = 0.15
_WEIGHT_KARAKA = 0.10

_DASHA_SCORE_MD = 1
_DASHA_SCORE_AD = 5
_DASHA_SCORE_PD = 6

_D1_FILTER_MIN_SCORE = 12.0
_MIN_WINDOW_GAP_DAYS = 45

# Phase 2.5.11.16 — strong-karaka floor. These planets ALWAYS survive
# STEP 1 (even if D1 score < threshold) because they are natural travel
# karakas; dropping them silently zeroes out their entire dasha period
# (e.g. Moon as MD lord for 10 years → no MD/AD contribution at all).
_KARAKA_FLOOR_SURVIVORS: Set[str] = {"Moon", "Rahu", "Mercury", "Jupiter"}

# Phase 2.5.11.16 — KP dasha-significator gate weight per role.
# A planet's KP travel-house signification (NL→SB→SS chain hits on
# 3/9/12) gives a deterministic bonus when the planet runs MD/AD/PD.
# Calibrated so Sep-2025 Moon-Moon-Mercury (Moon: 3 KP hits,
# Mercury: 2 hits) gains ~+5–7 absolute score and lifts into top-10.
_KP_DASHA_BOOST_MD = 0.4
_KP_DASHA_BOOST_AD = 1.2
_KP_DASHA_BOOST_PD = 1.5

# SAV bands (avg of 9H + 12H)
_SAV_FOREIGN_WEAK   = 25
_SAV_FOREIGN_STRONG = 32

_CONFIRMATIONS_FOR_CONSULT = 3

_VIMS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                "Jupiter", "Saturn", "Mercury"]
_VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
                "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
               "Saturn", "Rahu", "Ketu"]

# Travel-area signification per planet
_AREA_OF_PLANET: Dict[str, List[str]] = {
    "Sun":     ["govt_travel_assignment", "official_visa", "psu_overseas"],
    "Moon":    ["water_travel", "frequent_short_trips", "emotional_relocation"],
    "Mars":    ["land_travel", "military_overseas", "impulsive_journey"],
    "Mercury": ["business_travel", "communication_trip", "trade_journey"],
    "Jupiter": ["sacred_travel_pilgrimage", "study_abroad", "advisory_overseas"],
    "Venus":   ["leisure_travel", "creative_overseas", "luxury_relocation"],
    "Saturn":  ["long_arduous_journey", "labor_migration", "delayed_visa"],
    "Rahu":    ["foreign_settlement", "sudden_overseas_move",
                 "unconventional_destination"],
    "Ketu":    ["spiritual_retreat", "research_expedition", "cancelled_trip"],
}

# Functional malefics by lagna sign (travel-stress lens)
_FUNC_MALEFICS: Dict[int, Set[str]] = {
    0:  {"Mercury", "Venus", "Saturn"},
    1:  {"Moon", "Jupiter", "Venus"},
    2:  {"Mars", "Jupiter", "Sun"},
    3:  {"Mars", "Mercury", "Venus"},
    4:  {"Mercury", "Venus", "Saturn"},
    5:  {"Moon", "Mars", "Jupiter"},
    6:  {"Sun", "Jupiter", "Mars"},
    7:  {"Mercury", "Venus", "Saturn"},
    8:  {"Venus", "Mercury"},
    9:  {"Mars", "Jupiter", "Moon"},
    10: {"Sun", "Mars", "Jupiter"},
    11: {"Mercury", "Venus", "Saturn"},
}

_FUNC_BENEFICS: Dict[int, Set[str]] = {
    0:  {"Sun", "Mars", "Jupiter"},
    1:  {"Sun", "Mercury", "Saturn"},
    2:  {"Mercury", "Venus"},
    3:  {"Mars", "Jupiter", "Moon"},
    4:  {"Sun", "Mars", "Jupiter"},
    5:  {"Mercury", "Venus"},
    6:  {"Saturn", "Mercury", "Venus"},
    7:  {"Sun", "Moon", "Jupiter"},
    8:  {"Sun", "Jupiter", "Mars"},
    9:  {"Venus", "Mercury", "Saturn"},
    10: {"Venus", "Mercury", "Saturn"},
    11: {"Moon", "Mars", "Jupiter"},
}


# ════════════════════════════════════════════════════════════════════════
# Low-level helpers (aligned with finance v1 / health v1)
# ════════════════════════════════════════════════════════════════════════
def _sign_idx(name_or_str: Any) -> Optional[int]:
    if isinstance(name_or_str, int):
        return name_or_str % 12
    if isinstance(name_or_str, str):
        return _SIGN_IDX.get(name_or_str)
    return None


def _planet_house(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _planet_sign_idx(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            return _sign_idx(p.get("sign"))
    return None


def _house_lord(lagna_si: int, house: int) -> str:
    sign_at_house = (lagna_si + house - 1) % 12
    return _SIGN_LORDS[sign_at_house]


def _house_of_sign(sign_si: int, lagna_si: int) -> int:
    return ((sign_si - lagna_si) % 12) + 1


def _planets_in_house(planets: List[dict], house: int) -> List[str]:
    return [p["name"] for p in (planets or [])
            if isinstance(p, dict) and p.get("house") == house
            and p.get("name") in _PLANETS_9]


def _aspects_house(aspector: str, ap_house: int, target_house: int) -> bool:
    if not (1 <= ap_house <= 12 and 1 <= target_house <= 12):
        return False
    diff = ((target_house - ap_house) % 12) + 1
    if diff == 7:
        return True
    extras = {
        "Mars":    {4, 8},
        "Jupiter": {5, 9},
        "Saturn":  {3, 10},
        "Rahu":    {3, 10},
        "Ketu":    {3, 10},
    }
    return diff in extras.get(aspector, set())


def _kp_cusp(kp: dict, house: int) -> Optional[dict]:
    for c in (kp or {}).get("cusps", []) or []:
        if isinstance(c, dict) and c.get("house") == house:
            return c
    return None


def _planet_signified_houses(kp: dict, planet: str) -> List[int]:
    sig = (kp or {}).get("significations") or {}
    raw = sig.get(planet) or sig.get(planet.lower()) or []
    out: List[int] = []
    for v in raw:
        try:
            h = int(v)
            if 1 <= h <= 12:
                out.append(h)
        except (TypeError, ValueError):
            continue
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 1 — D1 travel-significator filter
# ════════════════════════════════════════════════════════════════════════
def _step1_d1_filter(kundli: dict, lagna_si: int
                       ) -> Dict[str, Dict[str, Any]]:
    """Identify travel-significant planets in D1.

    Inclusion (per user spec — foreign emphasis):
      • 12L (FOREIGN/distant lands)         — highest weight
      • 9L  (long-distance/dharma travel)   — high weight
      • 3L  (short trips/courage to move)   — medium weight
      • 7L  (away-from-home/business)       — medium weight
      • 4L  (HOME — INVERTED for travel)    — strong 4L = anchor;
                                              afflicted 4L = uprooted
      • Occupants of 3 / 9 / 12             — direct travel links
      • Planets aspecting the 9th house     — long-travel activation
      • Karakas: Rahu (foreign), Moon (movement), Mercury (short trips),
                  Jupiter (visa-luck/sacred), Saturn (long arduous),
                  Venus (luxury/leisure)
    """
    planets = kundli.get("planets") or []
    out: Dict[str, Dict[str, Any]] = {}
    for p in _PLANETS_9:
        out[p] = {"d1": 0.0, "in_filter": False, "links": [],
                   "is_lord_of": [], "occupies": None,
                   "aspects_9": False}

    # Lordship checks
    for h, weight, label in (
        (12, 18.0, "12L (FOREIGN/distant lands)"),
        (9,  16.0, "9L (long-distance/dharma travel)"),
        (3,  10.0, "3L (short trips/courage to move)"),
        (7,   8.0, "7L (away-from-home/business)"),
        (4,   8.0, "4L (HOME ANCHOR — inverted)"),
    ):
        lord = _house_lord(lagna_si, h)
        out[lord]["is_lord_of"].append(h)
        out[lord]["d1"] += weight
        out[lord]["links"].append(label)

    # Occupants of travel houses
    for h in (3, 9, 12):
        for pname in _planets_in_house(planets, h):
            out[pname]["occupies"] = h
            bump = {3: 8.0, 9: 12.0, 12: 14.0}[h]
            out[pname]["d1"] += bump
            out[pname]["links"].append(f"occupies {h}H (travel-house)")

    # Occupants of 4 (home anchor — record but don't auto-promote;
    # malefic in 4 = uprooting signal)
    for pname in _planets_in_house(planets, 4):
        if out[pname]["occupies"] is None:
            out[pname]["occupies"] = 4
        out[pname]["d1"] += 4.0
        out[pname]["links"].append("occupies 4H (HOME — anchor/uproot signal)")

    # Planets aspecting the 9th house
    for pname in _PLANETS_9:
        ap_house = _planet_house(planets, pname)
        if ap_house and _aspects_house(pname, ap_house, 9):
            out[pname]["aspects_9"] = True
            out[pname]["d1"] += 8.0
            out[pname]["links"].append("aspects 9H (long-travel activation)")

    # Travel karakas — always considered
    for karaka, bonus, role in (
        ("Rahu",    12.0, "foreign-settlement karaka (Rahu)"),
        ("Moon",     8.0, "movement/water-travel karaka (Moon)"),
        ("Jupiter",  8.0, "sacred-travel & visa-luck karaka (Jupiter)"),
        ("Mercury",  7.0, "short-trip/communication karaka (Mercury)"),
        ("Saturn",   7.0, "long-arduous-journey karaka (Saturn)"),
        ("Venus",    6.0, "luxury/leisure-travel karaka (Venus)"),
    ):
        out[karaka]["d1"] += bonus
        out[karaka]["links"].append(role)

    # Functional malefic surcharge (used in ranking, NOT in dasha
    # leak/travel classification — see Step5 architect-fix note)
    fm = _FUNC_MALEFICS.get(lagna_si, set())
    for pname in fm:
        out[pname]["d1"] += 4.0
        out[pname]["links"].append("functional malefic for lagna")

    for pname, info in out.items():
        info["in_filter"] = info["d1"] >= _D1_FILTER_MIN_SCORE

    # Phase 2.5.11.16 — Karaka-floor: natural travel karakas
    # (Moon=movement, Rahu=foreign, Mercury=short-trips, Jupiter=visa)
    # ALWAYS survive even if D1 placement-score < threshold. Without
    # this, e.g. a chart with Moon in lagna (no travel-house hit, not
    # 3/9/12-lord) would have its 10-year Moon Mahadasha contribute
    # ZERO to MD/AD scoring — silently breaking the engine for an
    # entire dasha period. Adds a small floor d1 score so downstream
    # ranking still differentiates floor-survivors from strong ones.
    for kp in _KARAKA_FLOOR_SURVIVORS:
        if not out[kp]["in_filter"]:
            out[kp]["in_filter"] = True
            out[kp]["links"].append("karaka-floor (natural travel karaka)")
            if out[kp]["d1"] < _D1_FILTER_MIN_SCORE:
                out[kp]["d1"] = _D1_FILTER_MIN_SCORE

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 2 — D9 dignity verification
# ════════════════════════════════════════════════════════════════════════
def _step2_d9_verify(kundli: dict, candidates: Set[str]) -> Dict[str, float]:
    out: Dict[str, float] = {p: 0.0 for p in candidates}
    if not candidates:
        return out
    d9 = None
    if compute_d9 is not None:
        try:
            d9 = compute_d9(kundli)
        except Exception:
            d9 = None
    if not d9:
        return {p: 8.0 for p in candidates}
    d9_planets = d9.get("planets") if isinstance(d9, dict) else None
    if not d9_planets:
        return {p: 8.0 for p in candidates}
    for pname in candidates:
        si = _planet_sign_idx(d9_planets, pname)
        if si is None:
            out[pname] = 8.0
            continue
        if pname in _EXALT and si == _EXALT[pname]:
            out[pname] = 25.0
        elif pname in _OWN_SIGNS and si in _OWN_SIGNS[pname]:
            out[pname] = 20.0
        elif pname in _DEBIL and si == _DEBIL[pname]:
            out[pname] = 5.0
        else:
            out[pname] = 12.0
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3 — D4 Chaturthamsha (residence/foreign-shift)
# ════════════════════════════════════════════════════════════════════════
def _step3_d4_residence(kundli: dict, candidates: Set[str],
                          lagna_si: int) -> Dict[str, float]:
    """D4 governs residence + place-of-living. A travel-significator
    landing in the 9th/12th of D4 strongly indicates relocation /
    foreign-residence. Defensive default: if D4 helper is missing, use
    a sign-based fallback derived from the 12L's natal sign dignity.

    Range 0-25.
    """
    out: Dict[str, float] = {p: 0.0 for p in candidates}
    if not candidates:
        return out
    d4 = None
    if compute_d4 is not None:
        try:
            d4 = compute_d4(kundli)
        except Exception:
            d4 = None
    if not d4 or not isinstance(d4, dict):
        # Fallback: use D1 dignity of each candidate as a proxy.
        # Travel-positive fallback so the engine doesn't silently zero
        # out an entire layer when D4 helper is missing.
        d1_planets = kundli.get("planets") or []
        for pname in candidates:
            si = _planet_sign_idx(d1_planets, pname)
            if si is None:
                out[pname] = 8.0; continue
            if pname in _EXALT and si == _EXALT[pname]:
                out[pname] = 22.0
            elif pname in _OWN_SIGNS and si in _OWN_SIGNS[pname]:
                out[pname] = 18.0
            elif pname in _DEBIL and si == _DEBIL[pname]:
                out[pname] = 6.0
            else:
                out[pname] = 12.0
        return out

    d4_planets = d4.get("planets") or []
    d4_lagna = _sign_idx(d4.get("ascendant")) if isinstance(
        d4.get("ascendant"), str) else None
    if d4_lagna is None:
        d4_lagna = lagna_si
    for pname in candidates:
        si = _planet_sign_idx(d4_planets, pname)
        if si is None:
            out[pname] = 8.0; continue
        h_in_d4 = _house_of_sign(si, d4_lagna)
        score = 8.0
        # Foreign-residence boost: 12H/9H of D4
        if h_in_d4 == 12:
            score = 22.0
        elif h_in_d4 == 9:
            score = 18.0
        elif h_in_d4 == 3:
            score = 14.0
        elif h_in_d4 == 4:
            # 4H of D4 = anchored at home (low travel score)
            score = 5.0
        # Dignity adjustment
        if pname in _EXALT and si == _EXALT[pname]:
            score = min(25.0, score + 4.0)
        elif pname in _DEBIL and si == _DEBIL[pname]:
            score = max(3.0, score - 4.0)
        out[pname] = score
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3.5 — KP layer (cuspal sub lord of 3 / 9 / 12)
# ════════════════════════════════════════════════════════════════════════
def _step3_5_kp_layer(kp: dict, lagna_si: int) -> Dict[str, Any]:
    """KP cuspal sub lord of 3, 9, 12 cusps.
    Verdict rules (KP standard for travel):
      cusp CSL signifies 3/9/12 → travel YES (matching the cusp's role)
      cusp CSL signifies 4/2    → anchored / no movement
      cusp CSL signifies 6/8    → blocked / risky travel
    """
    out = {"csl_3": None, "csl_9": None, "csl_12": None,
           "verdict_3": "UNKNOWN", "verdict_9": "UNKNOWN",
           "verdict_12": "UNKNOWN",
           "csl_3_signifies": [], "csl_9_signifies": [],
           "csl_12_signifies": []}
    if not kp:
        return out
    for h, key in ((3, "3"), (9, "9"), (12, "12")):
        c = _kp_cusp(kp, h)
        if not c:
            continue
        csl = c.get("sl") or c.get("subLord") or c.get("sub_lord")
        out[f"csl_{key}"] = csl
        if not csl:
            continue
        sig = _planet_signified_houses(kp, csl)
        out[f"csl_{key}_signifies"] = sig
        # HIGH (architect-fix May 7 2026): when CSL signifies multiple
        # categories, apply explicit precedence: BLOCKED_OR_RISKY (6/8)
        # dominates → ANCHORED (4/2) → TRAVEL_YES (3/9/12) → NEUTRAL.
        # Negative dusthana significations should NOT be masked by a
        # coincidental travel-house signification.
        has_block  = any(x in (6, 8) for x in sig)
        has_anchor = any(x in (4, 2) for x in sig)
        has_travel = any(x in _TRAVEL_HOUSES for x in sig)
        if has_block:
            out[f"verdict_{key}"] = "BLOCKED_OR_RISKY"
        elif has_anchor and not has_travel:
            out[f"verdict_{key}"] = "ANCHORED"
        elif has_travel:
            out[f"verdict_{key}"] = "TRAVEL_YES"
        else:
            out[f"verdict_{key}"] = "NEUTRAL"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3.6 — KP dasha-significator gate (Phase 2.5.11.16)
# ════════════════════════════════════════════════════════════════════════
def _kp_dasha_signifies_travel(kp: dict, planet: str,
                                target_houses: List[int] = None,
                                ) -> Dict[str, Any]:
    """Classical KP fructification rule: an event happens in the dasha
    of significators of relevant houses. For each planet, compute the
    UNION of houses it signifies via the NL→SB→SS chain (own placement
    + own ownership + star lord's houses + sub-lord's houses + sub-sub
    lord's houses) intersected with the travel houses [3, 9, 12].

    Returns:
      {"hits": sorted list of unique travel-house signification hits,
       "score": count of unique hits (0..3),
       "layers": list of layer-name strings that fired (for trace)}

    Why this matters (the bug it fixes — Phase 2.5.11.16):
      Sep 2025 Moon-Moon-Mercury on Rajalaxmi chart was a real foreign-
      travel month, but ranked #30+ in past_windows because Moon-MD
      contribution was tiny. Yet KP-wise BOTH Moon and Mercury
      strongly signify H9 + H12 via their full chain (Moon: pl=[8,12]
      + sl(Ketu)=...9... + ss(Moon)=[8,12]; Mercury: sb(Mars)=...12...
      + ss(Ketu)=...9...). This helper surfaces that signal so STEP 5
      can boost such windows.
    """
    if target_houses is None:
        target_houses = _TRAVEL_HOUSES
    out: Dict[str, Any] = {"hits": [], "score": 0, "layers": []}
    if not isinstance(kp, dict):
        return out
    sig_all = (kp.get("significations") or kp.get("significators") or {})
    if not isinstance(sig_all, dict):
        return out
    sig = sig_all.get(planet) or sig_all.get(planet.lower())
    if sig is None:
        return out
    target_set = set(target_houses)
    hits: Set[int] = set()
    # Schema adapter (Phase 2.5.11.16 architect-followup):
    #   Repo has TWO KP signification shapes in the wild —
    #   (a) DICT shape (Raj-style): {pl:[...], sl:[...], sb_houses:[...], ss_houses:[...]}
    #   (b) LIST shape (legacy):    [h1, h2, h3, ...]  (flat union, used by `_planet_signified_houses`)
    #   Without an adapter, list-shape charts would silently get score=0 here
    #   even when valid travel-house signification exists.
    if isinstance(sig, dict):
        # Layer keys in the upstream KP module:
        #   pl         = planet's own placement + ownership houses
        #   sl         = star-lord's signified houses
        #   sb_houses  = sub-lord's signified houses
        #   ss_houses  = sub-sub-lord's signified houses
        for layer_key in ("pl", "sl", "sb_houses", "ss_houses"):
            layer_houses = sig.get(layer_key) or []
            if not isinstance(layer_houses, list):
                continue
            layer_hits = [h for h in layer_houses if h in target_set]
            if layer_hits:
                for h in layer_hits:
                    hits.add(int(h))
                out["layers"].append(f"{layer_key}={sorted(set(layer_hits))}")
    elif isinstance(sig, list):
        # Legacy flat-list shape — treat as a single union layer "flat".
        # Score is degraded (no layer breakdown), but at least non-zero
        # when any travel house is present in the planet's combined chain.
        flat_hits: List[int] = []
        for v in sig:
            try:
                h = int(v)
            except (TypeError, ValueError):
                continue
            if h in target_set:
                hits.add(h)
                flat_hits.append(h)
        if flat_hits:
            out["layers"].append(f"flat={sorted(set(flat_hits))}")
    out["hits"] = sorted(hits)
    out["score"] = len(hits)
    return out


def _step3_6_kp_dasha_map(kp: dict) -> Dict[str, Dict[str, Any]]:
    """Compute KP travel-significator map for ALL 9 vimshottari planets.
    Used by STEP 5 to boost windows whose MD/AD/PD lords KP-significate
    travel houses regardless of D1 ranking."""
    out: Dict[str, Dict[str, Any]] = {}
    for p in _PLANETS_9:
        out[p] = _kp_dasha_signifies_travel(kp, p)
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 4 — Weighted ranking
# ════════════════════════════════════════════════════════════════════════
def _karaka_score(pname: str, lagna_si: int) -> float:
    base = {"Rahu": 9.0, "Moon": 7.0, "Jupiter": 7.0,
            "Mercury": 6.0, "Saturn": 6.0, "Venus": 5.0,
            "Mars": 4.0, "Sun": 4.0, "Ketu": 4.0}.get(pname, 0.0)
    if pname in _FUNC_BENEFICS.get(lagna_si, set()):
        base += 2.0
    return min(10.0, base)


def _step4_rank(d1_map: Dict[str, Dict[str, Any]],
                d9_scores: Dict[str, float],
                d4_scores: Dict[str, float],
                kp: dict, lagna_si: int) -> List[Dict[str, Any]]:
    """Score = D1·30% + D9·20% + D4·25% + KP·15% + Karaka·10%
    All sub-scores normalized to 0-25.
    """
    survivors = [p for p, info in d1_map.items() if info.get("in_filter")]
    if not survivors:
        return []
    raw_d1 = {p: d1_map[p]["d1"] for p in survivors}
    max_d1 = max(raw_d1.values()) or 1.0
    ranked: List[Dict[str, Any]] = []
    for pname in survivors:
        info = d1_map[pname]
        d1 = (raw_d1[pname] / max_d1) * 25.0
        d9 = d9_scores.get(pname, 8.0)
        d4 = d4_scores.get(pname, 8.0)
        sig = _planet_signified_houses(kp, pname)
        kp_score = 0.0
        if any(h in _TRAVEL_HOUSES for h in sig):
            kp_score = 18.0
        if 12 in sig:
            kp_score += 5.0
        if 9 in sig:
            kp_score += 3.0
        kp_score = min(25.0, kp_score) if kp_score > 0 else 6.0
        karaka = _karaka_score(pname, lagna_si) * 2.5
        total = (d1 * _WEIGHT_D1 + d9 * _WEIGHT_D9 +
                 d4 * _WEIGHT_D4 + kp_score * _WEIGHT_KP +
                 karaka * _WEIGHT_KARAKA)
        ranked.append({
            "name": pname,
            "score": round(total, 2),
            "d1": round(d1, 2), "d9": round(d9, 2),
            "d4": round(d4, 2), "kp": round(kp_score, 2),
            "karaka": round(karaka, 2),
            "links": list(info["links"]),
            "significations": _AREA_OF_PLANET.get(pname, []),
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


# ════════════════════════════════════════════════════════════════════════
# STEP 5 — Dasha activation
# ════════════════════════════════════════════════════════════════════════
def _parse_iso(s: Any) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    if isinstance(s, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(s.split("+")[0].split("Z")[0], fmt)
            except (ValueError, TypeError):
                continue
    return None


def _dasha_lord(node: dict) -> Optional[str]:
    for k in ("lord", "planet", "name", "ruler"):
        v = node.get(k)
        if v:
            return v
    return None


def _dasha_start_end(node: dict) -> Tuple[Optional[datetime], Optional[datetime]]:
    s = (node.get("start") or node.get("startDate") or
         node.get("from") or node.get("start_date"))
    e = (node.get("end") or node.get("endDate") or
         node.get("to") or node.get("end_date"))
    return _parse_iso(s), _parse_iso(e)


def _dasha_children(node: dict) -> List[dict]:
    for k in ("subDashas", "antardashas", "ad", "sub_dashas",
              "pratyantar", "pd", "children"):
        v = node.get(k)
        if isinstance(v, list):
            return v
    return []


def _flatten_dasha_chain(kundli: dict) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    dashas = kundli.get("dashas") or []
    if not isinstance(dashas, list):
        return out
    for md in dashas:
        if not isinstance(md, dict): continue
        md_lord = _dasha_lord(md)
        ads = _dasha_children(md)
        if not ads:
            ms, me = _dasha_start_end(md)
            if ms and me:
                out.append({"md": md_lord, "ad": None, "pd": None,
                             "start": ms, "end": me})
            continue
        for ad in ads:
            if not isinstance(ad, dict): continue
            ad_lord = _dasha_lord(ad)
            pds = _dasha_children(ad)
            if not pds:
                ads_, ade_ = _dasha_start_end(ad)
                if ads_ and ade_:
                    out.append({"md": md_lord, "ad": ad_lord, "pd": None,
                                 "start": ads_, "end": ade_})
                continue
            for pd in pds:
                if not isinstance(pd, dict): continue
                pds_, pde_ = _dasha_start_end(pd)
                if not (pds_ and pde_): continue
                out.append({"md": md_lord, "ad": ad_lord,
                             "pd": _dasha_lord(pd),
                             "start": pds_, "end": pde_})
    return out


def _step5_dasha_activation(chain: List[Dict[str, Any]],
                              ranked: List[Dict[str, Any]],
                              lagna_si: int,
                              now: datetime,
                              horizon_years: int = 10,
                              direction: str = "future",
                              lookback_years: int = 15,
                              kp_dasha_map: Optional[Dict[str, Dict[str, Any]]] = None,
                              ) -> List[Dict[str, Any]]:
    """Score dasha windows in either direction.

    SIGN CONVENTION: For travel, "stress" = travel-promoter activation
    (more is more travel-likely). Anchor planets (4L strong, no travel
    linkage) lower the travel score. Risk planets (Mars+Rahu in
    travel houses) raise risk_score separately.

    AD=5, PD=6, MD=1.

    Phase 2.5.11.14: `direction` kwarg added.
      • direction="future" (default) — windows from `now` to
        `now + horizon_years`. Sorted by (-score, start) so highest-
        score upcoming window is first.
      • direction="past" — windows from `now - lookback_years` to
        `now`. Sorted by (-score, -start) so the MOST RECENT
        high-score past window is first (recency wins ties).

    NOTE — architect-pattern (mirrors finance v1): "functional malefic
    for lagna" tag is INTENTIONALLY EXCLUDED from anchor classification.
    It is a Step-1 ranking modifier only.
    """
    if not chain or not ranked:
        return []
    score_map = {r["name"]: r["score"] for r in ranked}
    max_score = max(score_map.values()) or 1.0

    travel_lords: Set[str] = set()
    anchor_lords: Set[str] = set()
    risk_lords: Set[str] = set()
    _TRAVEL_TAGS = ("12L (FOREIGN", "9L (long-distance",
                     "3L (short trips", "7L (away-from-home",
                     "occupies 12H", "occupies 9H", "occupies 3H",
                     "foreign-settlement karaka",
                     "movement/water-travel karaka",
                     "sacred-travel", "short-trip",
                     "long-arduous-journey", "luxury/leisure-travel")
    _ANCHOR_TAGS = ("4L (HOME ANCHOR",)
    _RISK_TAGS = ("occupies 4H (HOME — anchor/uproot signal)",)
    for r in ranked:
        travel_count = 0
        anchor_count = 0
        for l in r["links"]:
            if any(t in l for t in _TRAVEL_TAGS):
                travel_count += 1
            if any(t in l for t in _ANCHOR_TAGS):
                anchor_count += 1
        if travel_count and anchor_count:
            if travel_count >= anchor_count:
                travel_lords.add(r["name"])
            else:
                anchor_lords.add(r["name"])
        elif travel_count:
            travel_lords.add(r["name"])
        elif anchor_count:
            anchor_lords.add(r["name"])
        # Risk: Mars or Saturn occupying 4H → uprooting / forced relocation
        # Rahu in any travel house → unsettled/sudden journey risk
        if r["name"] in ("Mars", "Saturn"):
            for l in r["links"]:
                if "occupies 4H" in l:
                    risk_lords.add(r["name"])
        if r["name"] in ("Rahu", "Ketu"):
            for l in r["links"]:
                if "occupies 12H" in l or "occupies 9H" in l:
                    risk_lords.add(r["name"])

    if direction == "past":
        window_lo = now - timedelta(days=365 * lookback_years)
        window_hi = now
    else:
        window_lo = now
        window_hi = now + timedelta(days=365 * horizon_years)
    windows: List[Dict[str, Any]] = []
    for w in chain:
        if direction == "past":
            # Past = interval-overlap with [window_lo, now). Window
            # must end strictly before now AND end after lookback floor.
            # (architect-flagged fix: do NOT gate on start, otherwise
            # long MD windows that started >15y ago but ended recently
            # would be silently dropped.)
            if w["end"] >= now or w["end"] <= window_lo:
                continue
        else:
            if w["end"] < window_lo or w["start"] > window_hi:
                continue
        travel_score = 0.0
        anchor_score = 0.0
        risk_score = 0.0
        kp_boost = 0.0
        kp_hits_total: Set[int] = set()
        triggers: List[str] = []
        _KP_BOOST_BY_ROLE = {"MD": _KP_DASHA_BOOST_MD,
                              "AD": _KP_DASHA_BOOST_AD,
                              "PD": _KP_DASHA_BOOST_PD}
        for role, lord, weight in (("MD", w["md"], _DASHA_SCORE_MD),
                                    ("AD", w["ad"], _DASHA_SCORE_AD),
                                    ("PD", w["pd"], _DASHA_SCORE_PD)):
            if not lord:
                continue
            # D1-derived contribution (existing behaviour).
            if lord in score_map:
                rel = score_map[lord] / max_score
                contrib = weight * rel
                if lord in travel_lords:
                    travel_score += contrib
                    triggers.append(f"{role}={lord}(TRAVEL_LORD,+{contrib:.2f})")
                elif lord in anchor_lords:
                    anchor_score += contrib
                    triggers.append(f"{role}={lord}(ANCHOR,-{contrib:.2f})")
                else:
                    triggers.append(f"{role}={lord}(NEUTRAL,0)")
                if lord in risk_lords:
                    risk_score += contrib * 0.5
                    triggers.append(f"  ↳ RISK_TAG:{lord}(+{contrib*0.5:.2f})")
            # Phase 2.5.11.16 — KP dasha-significator boost. Fires
            # INDEPENDENTLY of D1 ranking so a planet that's missing
            # from `ranked` (or floored low) but KP-significates 3/9/12
            # still contributes when it runs as MD/AD/PD. Classical
            # KP rule: events fructify in dasha of significators.
            if kp_dasha_map:
                kp_info = kp_dasha_map.get(lord) or {}
                hits = kp_info.get("score") or 0
                if hits:
                    boost = hits * _KP_BOOST_BY_ROLE[role]
                    kp_boost += boost
                    for h in (kp_info.get("hits") or []):
                        kp_hits_total.add(int(h))
                    triggers.append(
                        f"  ↳ KP-DASHA:{role}={lord}"
                        f"(hits={kp_info.get('hits')},+{boost:.2f})")
        net = max(0.0, travel_score - anchor_score) + kp_boost
        if net <= 0 and travel_score == 0 and risk_score == 0 and kp_boost == 0:
            continue
        # Heuristic kind: foreign vs short trip vs business
        kind = "general"
        if any(lord in ("Rahu", "Saturn", "Jupiter")
                for lord in (w["ad"], w["pd"]) if lord in travel_lords):
            kind = "long_or_foreign"
        elif w["ad"] == "Mercury" or w["pd"] == "Mercury":
            kind = "short_or_business"
        windows.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "start": w["start"], "end": w["end"],
            "score": round(net, 2),
            "travel_raw": round(travel_score, 2),
            "anchor_raw": round(anchor_score, 2),
            "risk_raw": round(risk_score, 2),
            "kp_boost": round(kp_boost, 2),
            "kp_hits": sorted(kp_hits_total),
            "kind": kind,
            "triggers": triggers,
        })
    if direction == "past":
        # Recency wins ties: most recent high-score past window first
        windows.sort(key=lambda x: (-x["score"], -x["start"].timestamp()))
    else:
        windows.sort(key=lambda x: (-x["score"], x["start"]))
    return windows


# ════════════════════════════════════════════════════════════════════════
# STEP 6 — Transit triggers (travel lens)
# ════════════════════════════════════════════════════════════════════════
def _planet_sign_at(planet_id: int, when: datetime) -> Optional[int]:
    if not _HAS_SWE:
        return None
    try:
        jd = swe.julday(when.year, when.month, when.day,
                         when.hour + when.minute / 60.0)
        lon = swe.calc_ut(jd, planet_id, _SWE_FLAGS)[0][0]
        return int(lon // 30) % 12
    except Exception:
        return None


_SWE_PLANET_IDS: Dict[str, int] = {}
def _init_swe_planet_ids():
    if not _HAS_SWE or _SWE_PLANET_IDS:
        return
    _SWE_PLANET_IDS.update({
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS, "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,  # Ketu = Rahu+180°
    })


def _step6_transits(kundli: dict, lagna_si: int,
                     planets_d1: List[dict],
                     now: datetime,
                     current_dasha_lords: Optional[Dict[str, Optional[str]]] = None,
                     ) -> Dict[str, Any]:
    out: Dict[str, Any] = {"saturn": None, "rahu": None, "ketu": None,
           "mars": None, "jupiter": None, "sade_sati": None,
           "dasha_lord_transits": [],
           "active_triggers": []}
    if not _HAS_SWE:
        out["note"] = "swisseph unavailable; transit layer skipped"
        return out
    _init_swe_planet_ids()

    moon_si = _planet_sign_idx(planets_d1, "Moon")
    saturn_si = _planet_sign_at(swe.SATURN, now)
    rahu_si = _planet_sign_at(swe.MEAN_NODE, now)
    ketu_si = (rahu_si + 6) % 12 if rahu_si is not None else None
    mars_si = _planet_sign_at(swe.MARS, now)
    jupiter_si = _planet_sign_at(swe.JUPITER, now)

    def _h(si):
        return _house_of_sign(si, lagna_si) if si is not None else None

    sat_h = _h(saturn_si); rahu_h = _h(rahu_si); ketu_h = _h(ketu_si)
    mars_h = _h(mars_si); jup_h = _h(jupiter_si)

    if sat_h == 12:
        out["saturn"] = "Saturn transiting 12H — long-stay abroad / delayed visa"
        out["active_triggers"].append(("saturn_long", 12, +0.8))
    elif sat_h == 4:
        out["saturn"] = "Saturn transiting 4H — uprooted from home / forced relocation pressure"
        out["active_triggers"].append(("saturn_uproot", 4, +0.7))
    elif sat_h == 9:
        out["saturn"] = "Saturn transiting 9H — slow long-distance journey"
        out["active_triggers"].append(("saturn_long", 9, +0.4))

    if rahu_h == 12:
        out["rahu"] = "Rahu transit on 12H — sudden foreign-shift opportunity"
        out["active_triggers"].append(("rahu_foreign", 12, +1.0))
    elif rahu_h == 9:
        out["rahu"] = "Rahu transit on 9H — sudden long-distance journey"
        out["active_triggers"].append(("rahu_long", 9, +0.7))
    elif rahu_h == 3:
        out["rahu"] = "Rahu transit on 3H — frequent unconventional short trips"
        out["active_triggers"].append(("rahu_short", 3, +0.5))

    if ketu_h == 4:
        out["ketu"] = "Ketu transit on 4H — detachment from home / spiritual relocation"
        out["active_triggers"].append(("ketu_detach", 4, +0.6))
    elif ketu_h == 9:
        out["ketu"] = "Ketu transit on 9H — distrust of long journeys / spiritual retreat"
        out["active_triggers"].append(("ketu_pause", 9, -0.3))

    if mars_h in (3, 9):
        out["mars"] = f"Mars transit in {mars_h}H — impulsive trip / accident risk"
        out["active_triggers"].append(("mars_risk", mars_h, +0.5))

    if jup_h == 9:
        out["jupiter"] = "Jupiter transit in 9H — visa-luck / sacred-journey window"
        out["active_triggers"].append(("jupiter_protect", 9, +0.9))
    elif jup_h == 12:
        out["jupiter"] = "Jupiter transit in 12H — foreign-fortune blessing"
        out["active_triggers"].append(("jupiter_foreign", 12, +0.9))
    elif jup_h == 3:
        out["jupiter"] = "Jupiter transit in 3H — courage to initiate travel"
        out["active_triggers"].append(("jupiter_short", 3, +0.5))

    if moon_si is not None and saturn_si is not None:
        delta = (saturn_si - moon_si) % 12
        if delta == 11:
            out["sade_sati"] = "first_phase (Saturn 12th from Moon — relocation pressure)"
            out["active_triggers"].append(("sade_sati", 12, +0.5))
        elif delta == 0:
            out["sade_sati"] = "peak_phase"
            out["active_triggers"].append(("sade_sati", 1, +0.4))
        elif delta == 1:
            out["sade_sati"] = "exit_phase"
            out["active_triggers"].append(("sade_sati", 2, +0.3))

    # Phase 2.5.11.16 — Current MD/AD/PD lords' LIVE transit through
    # travel houses 3/9/12. The classical generic-malefic transit
    # checks above (Saturn/Rahu/Jupiter) miss the case where the
    # *active dasha lord itself* (e.g. PD lord Mercury for Sep-2025)
    # is currently transiting a foreign house. This is a textbook
    # KP/Vedic fructification trigger.
    if current_dasha_lords:
        for role in ("MD", "AD", "PD"):
            lord = current_dasha_lords.get(role)
            if not lord:
                continue
            if lord == "Ketu":
                # Ketu = Rahu + 180° (sign-wise: opposite sign)
                rahu_id = _SWE_PLANET_IDS.get("Rahu")
                if rahu_id is None:
                    continue
                rahu_sii = _planet_sign_at(rahu_id, now)
                lord_si = (rahu_sii + 6) % 12 if rahu_sii is not None else None
            else:
                pid = _SWE_PLANET_IDS.get(lord)
                lord_si = _planet_sign_at(pid, now) if pid is not None else None
            if lord_si is None:
                continue
            lord_h = _h(lord_si)
            if lord_h in (3, 9, 12):
                weight_by_role = {"MD": 0.4, "AD": 0.7, "PD": 1.0}[role]
                msg = (f"{role}-lord {lord} transiting {lord_h}H "
                        f"(travel-house) — dasha-lord active in foreign axis")
                out["dasha_lord_transits"].append(msg)
                out["active_triggers"].append(
                    (f"dasha_lord_{role.lower()}_in_travel_h",
                     lord_h, +weight_by_role))

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 7 — Ashtakavarga support (SAV bindus on 9H + 12H)
# ════════════════════════════════════════════════════════════════════════
def _step7_ashtakavarga(kundli: dict, lagna_si: int) -> Dict[str, Any]:
    out = {"sav_9": None, "sav_12": None, "foreign_band": "UNKNOWN"}
    if compute_ashtakavarga is None:
        return out
    try:
        planets = kundli.get("planets") or []
        av = compute_ashtakavarga(planets, lagna_si)
    except Exception:
        return out
    if not isinstance(av, dict):
        return out
    sav = av.get("sav")
    if isinstance(sav, list) and len(sav) == 12:
        out["sav_9"] = sav[8]    # 9th house
        out["sav_12"] = sav[11]   # 12th house
    if (isinstance(out["sav_9"], (int, float))
            and isinstance(out["sav_12"], (int, float))):
        avg = (out["sav_9"] + out["sav_12"]) / 2.0
        if avg < _SAV_FOREIGN_WEAK:
            out["foreign_band"] = "WEAK"
        elif avg >= _SAV_FOREIGN_STRONG:
            out["foreign_band"] = "STRONG"
        else:
            out["foreign_band"] = "MEDIUM"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 9 — Yoga + hard guards
# ════════════════════════════════════════════════════════════════════════
def _detect_yogas(kundli: dict, lagna_si: int,
                   planets: List[dict]) -> List[Dict[str, Any]]:
    """Detect classical travel-relevant yogas.

    POSITIVE:
      - Foreign-Settlement Yoga (12L↔9L exchange OR Rahu in 12H)
      - Tirtha Yoga (Jupiter+9L conjunction or aspect)
      - Vidya-Yatra Yoga (9L+5L for study-abroad)
      - Travel Yoga (3L+12L exchange/aspect)
    NEGATIVE:
      - Sthanabhrama (no movement: 4L exalted/own + 12L combust/debil)
      - Visa-Block (Ketu in 9H + Saturn aspect on 12H)
      - Risk-Travel (Mars+Rahu in 3/9/12 — accident/legal-trouble)
    """
    out: List[Dict[str, Any]] = []

    h12_lord = _house_lord(lagna_si, 12)
    h9_lord  = _house_lord(lagna_si, 9)
    h3_lord  = _house_lord(lagna_si, 3)
    h5_lord  = _house_lord(lagna_si, 5)
    h4_lord  = _house_lord(lagna_si, 4)

    # Foreign-Settlement Yoga
    h12_h = _planet_house(planets, h12_lord)
    h9_h = _planet_house(planets, h9_lord)
    if h12_lord != h9_lord and h12_h and h9_h:
        # Mutual exchange (parivartana)
        if h12_h == 9 and h9_h == 12:
            out.append({"name": "Foreign-Settlement Yoga (12L↔9L parivartana)",
                        "severity": "protective",
                        "planets": [h12_lord, h9_lord]})
        elif h12_h == h9_h:
            out.append({"name": "Foreign-Settlement Yoga (12L+9L conjunction)",
                        "severity": "protective",
                        "planets": [h12_lord, h9_lord]})
        elif (_aspects_house(h12_lord, h12_h, h9_h)
              and _aspects_house(h9_lord, h9_h, h12_h)):
            out.append({"name": "Foreign-Settlement Yoga (12L↔9L mutual aspect)",
                        "severity": "protective",
                        "planets": [h12_lord, h9_lord]})
    rahu_h = _planet_house(planets, "Rahu")
    if rahu_h == 12:
        out.append({"name": "Foreign-Settlement Yoga (Rahu in 12H)",
                    "severity": "protective",
                    "planets": ["Rahu"]})

    # Tirtha Yoga: Jupiter conjunct/aspect 9L
    jup_h = _planet_house(planets, "Jupiter")
    if jup_h and h9_h:
        if jup_h == h9_h:
            out.append({"name": "Tirtha Yoga (Jupiter+9L conjunction)",
                        "severity": "protective",
                        "planets": ["Jupiter", h9_lord]})
        elif _aspects_house("Jupiter", jup_h, h9_h):
            out.append({"name": "Tirtha Yoga (Jupiter aspects 9L)",
                        "severity": "protective",
                        "planets": ["Jupiter", h9_lord]})

    # Vidya-Yatra Yoga: 9L+5L exchange/conjunction (study abroad)
    h5_h = _planet_house(planets, h5_lord)
    if h9_lord != h5_lord and h9_h and h5_h:
        if h9_h == h5_h:
            out.append({"name": "Vidya-Yatra Yoga (9L+5L conjunction)",
                        "severity": "protective",
                        "planets": [h9_lord, h5_lord]})
        elif h9_h == 5 and h5_h == 9:
            out.append({"name": "Vidya-Yatra Yoga (9L↔5L parivartana)",
                        "severity": "protective",
                        "planets": [h9_lord, h5_lord]})

    # Travel Yoga: 3L+12L exchange/aspect
    h3_h = _planet_house(planets, h3_lord)
    if h3_lord != h12_lord and h3_h and h12_h:
        if h3_h == 12 and h12_h == 3:
            out.append({"name": "Travel Yoga (3L↔12L parivartana)",
                        "severity": "protective",
                        "planets": [h3_lord, h12_lord]})
        elif h3_h == h12_h:
            out.append({"name": "Travel Yoga (3L+12L conjunction)",
                        "severity": "protective",
                        "planets": [h3_lord, h12_lord]})

    # Sthanabhrama (no-movement): 4L strong AND 12L weak
    h4_h_planet = _planet_house(planets, h4_lord)
    h4_si = _planet_sign_idx(planets, h4_lord)
    h12_si = _planet_sign_idx(planets, h12_lord)
    h4_strong = (h4_si is not None
                 and (h4_si in _OWN_SIGNS.get(h4_lord, set())
                      or h4_si == _EXALT.get(h4_lord, -1)))
    h12_weak = (h12_si is not None and h12_si == _DEBIL.get(h12_lord, -1))
    if h4_strong and h12_weak:
        out.append({"name": "Sthanabhrama (anchored — 4L strong + 12L debilitated)",
                    "severity": "high",
                    "planets": [h4_lord, h12_lord]})

    # Visa-Block: Ketu in 9H AND Saturn aspects 12H
    ketu_h = _planet_house(planets, "Ketu")
    sat_h_planet = _planet_house(planets, "Saturn")
    if ketu_h == 9 and sat_h_planet and _aspects_house("Saturn", sat_h_planet, 12):
        out.append({"name": "Visa-Block Yoga (Ketu in 9H + Saturn aspects 12H)",
                    "severity": "high",
                    "planets": ["Ketu", "Saturn"]})

    # Risk-Travel: Mars+Rahu conjunct in 3/9/12
    mars_h = _planet_house(planets, "Mars")
    if mars_h == rahu_h and mars_h in (3, 9, 12):
        out.append({"name": f"Risk-Travel Yoga (Mars+Rahu in {mars_h}H — accident/legal-trouble)",
                    "severity": "high",
                    "planets": ["Mars", "Rahu"]})

    return out


# ════════════════════════════════════════════════════════════════════════
# Helpers — verdict / severity / age
# ════════════════════════════════════════════════════════════════════════
def _parse_dob_dt(birth: Any, kundli: Any = None) -> Optional[datetime]:
    candidates = []
    for src in (birth, kundli):
        if isinstance(src, dict):
            for k in ("dob", "birth_date", "birthDate", "DOB", "date"):
                v = src.get(k)
                if v: candidates.append(v)
            try:
                d = src.get("day"); m = src.get("month"); y = src.get("year")
                if d and m and y:
                    candidates.append(f"{int(y):04d}-{int(m):02d}-{int(d):02d}")
            except Exception:
                pass
    fmts = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
            "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y")
    for c in candidates:
        if isinstance(c, datetime): return c
        if not isinstance(c, str): continue
        s = c.split("T")[0].strip()
        for fmt in fmts:
            try: return datetime.strptime(s, fmt)
            except ValueError: continue
    return None


def _compute_age(birth_dt: Optional[datetime], ref: datetime) -> Optional[int]:
    if not birth_dt: return None
    age = ref.year - birth_dt.year - (
        (ref.month, ref.day) < (birth_dt.month, birth_dt.day))
    return age if 0 <= age <= 120 else None


def _severity_of_window(score: float, transit_load: float,
                          risk_score: float = 0.0) -> str:
    """Map travel-promoter score + risk to a severity tier.
    Tiers (matching `travel` topic in remedy engine):
      celebratory : strong travel flow, low risk
      supportive  : moderate flow
      watchful    : weak flow OR mild risk
      consult     : high-risk travel (Mars+Rahu, visa-block, etc.)
    """
    s = score + max(0.0, transit_load)
    # Risk dominates: heavy risk_score → consult regardless of flow
    if risk_score >= 2.0:
        return "consult"
    if s >= 6.0 and risk_score < 0.5:
        return "celebratory"
    if s >= 3.5:
        return "supportive"
    if s >= 1.5:
        return "watchful"
    return "watchful"


def _recommendation_tier(severity: str, confirmations: int,
                          age: Optional[int]) -> str:
    if severity == "consult" and confirmations >= _CONFIRMATIONS_FOR_CONSULT:
        return "consult"
    if severity == "consult":
        return "watchful"
    return severity


def _derive_verdict(top_window_score: float,
                     foreign_band: str,
                     yogas: List[Dict[str, Any]],
                     transit_load: float,
                     foreign_promised: bool
                     ) -> Tuple[str, str]:
    """Combine top-window flow, ashtakavarga band, yogas, transits and
    foreign-promised flag into a single verdict + band.

    Mirrors finance v1 architect-fix pattern: a single `has_high_neg`
    yoga does NOT hard-override the verdict. It must coincide with low
    flow AND no protective rescue.
    """
    band = foreign_band if foreign_band in {"WEAK", "MEDIUM", "STRONG"} else "MEDIUM"
    has_high_neg = any(y.get("severity") == "high" for y in yogas)
    has_protect = any(y.get("severity") == "protective" for y in yogas)

    s = top_window_score + max(0.0, transit_load)

    # HIGH_RISK is for active negative yogas + low flow
    if s < 2.0 and has_high_neg and not has_protect:
        return "LOW_PROBABILITY", "WEAK"
    # Risk-Travel yoga at moderate flow → HIGH_RISK_TRAVEL
    risk_yoga = any("Risk-Travel" in (y.get("name") or "")
                     or "Visa-Block" in (y.get("name") or "")
                     for y in yogas)
    if risk_yoga and s >= 1.0:
        return "HIGH_RISK_TRAVEL", band

    # CRITICAL (architect-fix May 7 2026): old logic let `foreign_promised`
    # alone force TRAVEL_PROMISED regardless of flow. A composite foreign
    # signature without ANY active dasha flow should NOT promise travel —
    # the houses are promised but the timing isn't. Now foreign_promised
    # only elevates to TRAVEL_PROMISED if there is at least minimal flow
    # (s >= 3.5) OR strong flow (s >= 6.0) on its own.
    if s >= 6.0 or (foreign_promised and s >= 3.5):
        verdict = "TRAVEL_PROMISED"
        if foreign_promised:
            band = "STRONG"
        return verdict, band
    if s >= 3.5:
        return "FAVORABLE", band
    if has_protect:
        return "FAVORABLE", band
    return "LOW_PROBABILITY", band


def _detect_foreign_promised(yogas: List[Dict[str, Any]],
                               kp_layer: Dict[str, Any],
                               foreign_band: str,
                               ranked: List[Dict[str, Any]]) -> bool:
    """A composite flag — TRUE only when multiple foreign-indicators
    coincide: foreign yoga + KP 12-cusp signifies travel-houses + at
    least medium SAV foreign band + Rahu/12L ranked in top-3.
    """
    # HIGH (architect-fix May 7 2026): require positive polarity on the
    # foreign-yoga match so that any negatively-named match (or future
    # negative-tagged variants) cannot inflate the confirmation count.
    has_foreign_yoga = any(
        "Foreign-Settlement" in (y.get("name") or "")
        and y.get("severity") == "protective"
        for y in yogas
    )
    kp_12_yes = kp_layer.get("verdict_12") == "TRAVEL_YES"
    sav_ok = foreign_band in ("MEDIUM", "STRONG")
    top3_names = {r["name"] for r in ranked[:3]}
    rahu_top = "Rahu" in top3_names
    confirmations = sum([has_foreign_yoga, kp_12_yes, sav_ok, rahu_top])
    return confirmations >= 3


def _affected_areas(top_planets: List[Dict[str, Any]]) -> List[str]:
    seen: List[str] = []
    for p in top_planets[:5]:
        for a in p.get("significations", []):
            if a not in seen:
                seen.append(a)
    return seen[:6]


def _gap_ok(cand: Dict[str, Any], chosen: List[Dict[str, Any]]) -> bool:
    for c in chosen:
        gap = abs((cand["start"] - c["start"]).days)
        if gap < _MIN_WINDOW_GAP_DAYS:
            return False
    return True


def _select_top_3(scored: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chosen: List[Dict[str, Any]] = []
    for w in scored:
        if _gap_ok(w, chosen):
            chosen.append(w)
        if len(chosen) >= 3: break
    return chosen


def _format_window(start: datetime, end: datetime) -> str:
    return f"{start.strftime('%b %Y')} → {end.strftime('%b %Y')}"


def _data_sufficiency(kundli: dict, kp: dict) -> Tuple[bool, List[str]]:
    notes: List[str] = []
    ok = True
    if not kundli.get("planets"):
        notes.append("MISSING planets list"); ok = False
    if not kundli.get("dashas"):
        notes.append("MISSING dasha chain")
    if not kp:
        notes.append("MISSING KP layer (KP weights default to flat)")
    return ok, notes


# ════════════════════════════════════════════════════════════════════════
# Public entry point
# ════════════════════════════════════════════════════════════════════════
def compute_travel_window(kundli: dict, intel: Optional[dict] = None,
                           kp: Optional[dict] = None,
                           birth: Optional[Any] = None) -> dict:
    """Run the full 9-step Travel Timing Engine v1 pipeline.

    Single-exit wrapper that resets and populates the thread-local
    cache on every code path (mirror of finance v1).
    """
    clear_last_travel_result()
    result: Dict[str, Any]
    try:
        result = _compute_travel_window_impl(kundli, intel, kp, birth)
    except Exception as exc:  # noqa: BLE001
        result = {
            "verdict": "UNKNOWN", "band": "WEAK",
            "factors": [f"ENGINE_EXCEPTION {type(exc).__name__}: {str(exc)[:160]}"],
            "risk_flags": ["ENGINE_EXCEPTION"],
            "engine_version": "v1.0.0",
            "engine_arch": "FILTER→VERIFY→KP-GATE→ACTIVATE→TRIGGER",
        }
    _store_last_result(result)
    return result


def _compute_travel_window_impl(kundli: dict,
                                  intel: Optional[dict] = None,
                                  kp: Optional[dict] = None,
                                  birth: Optional[Any] = None) -> dict:
    if not isinstance(kundli, dict) or not kundli:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "factors": ["GATE kundli empty"],
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→KP-GATE→ACTIVATE→TRIGGER"}
    kp = kp or kundli.get("kp") or {}
    intel = intel or {}

    asc = kundli.get("ascendant")
    lagna_si = _sign_idx(asc) if isinstance(asc, str) else None
    if lagna_si is None:
        for key in ("lagnaSign", "ascendant_sign", "ascendantSign"):
            v = kundli.get(key)
            if isinstance(v, str):
                lagna_si = _sign_idx(v)
            elif isinstance(v, int):
                lagna_si = v % 12
            if lagna_si is not None:
                break
    if lagna_si is None:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "factors": ["GATE lagna_si is None"],
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→KP-GATE→ACTIVATE→TRIGGER"}

    ok, reasons = _data_sufficiency(kundli, kp)
    factors: List[str] = []
    if reasons:
        factors.append(f"DATA_NOTES {reasons}")
    if not ok:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "risk_flags": reasons, "factors": factors,
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→KP-GATE→ACTIVATE→TRIGGER"}

    now = datetime.utcnow()
    birth_dt = _parse_dob_dt(birth, kundli=kundli)
    age = _compute_age(birth_dt, now)
    factors.append(f"AGE user_age={age} lagna={_SIGNS[lagna_si]}")

    # ── STEP 1 ──
    d1_map = _step1_d1_filter(kundli, lagna_si)
    survivors = {p for p, info in d1_map.items() if info["in_filter"]}
    factors.append(f"STEP1 survivors={sorted(survivors)}")

    # ── STEP 2 ──
    d9_scores = _step2_d9_verify(kundli, survivors)
    factors.append(f"STEP2 D9_scores=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d9_scores.items()))

    # ── STEP 3 ──
    d4_scores = _step3_d4_residence(kundli, survivors, lagna_si)
    factors.append(f"STEP3 D4_residence=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d4_scores.items()))

    # ── STEP 3.5 ──
    kp_layer = _step3_5_kp_layer(kp, lagna_si)
    factors.append(f"STEP3.5 KP csl_3={kp_layer['csl_3']}/{kp_layer['verdict_3']} "
                    f"csl_9={kp_layer['csl_9']}/{kp_layer['verdict_9']} "
                    f"csl_12={kp_layer['csl_12']}/{kp_layer['verdict_12']}")

    # ── STEP 3.6 — KP dasha-significator gate (Phase 2.5.11.16) ──
    kp_dasha_map = _step3_6_kp_dasha_map(kp)
    _kp_summary = ",".join(
        f"{p}:{kp_dasha_map[p]['hits']}"
        for p in _PLANETS_9 if kp_dasha_map[p]['score'] > 0)
    factors.append(f"STEP3.6 KP_dasha_travel_hits={{{_kp_summary}}}")

    # ── STEP 4 ──
    ranked = _step4_rank(d1_map, d9_scores, d4_scores, kp, lagna_si)
    factors.append("STEP4 ranked=" +
                    ",".join(f"{r['name']}:{r['score']}" for r in ranked[:5]))

    # ── STEP 5 (future + past, Phase 2.5.11.14; KP-boosted 2.5.11.16) ──
    chain = _flatten_dasha_chain(kundli)
    dasha_windows = _step5_dasha_activation(chain, ranked, lagna_si, now,
                                              direction="future",
                                              kp_dasha_map=kp_dasha_map)
    past_dasha_windows = _step5_dasha_activation(chain, ranked, lagna_si, now,
                                                   direction="past",
                                                   kp_dasha_map=kp_dasha_map)
    factors.append(f"STEP5 dasha_windows_in_horizon={len(dasha_windows)} "
                    f"past_windows={len(past_dasha_windows)}")

    # ── STEP 6 ──
    planets_d1 = kundli.get("planets") or []
    # Phase 2.5.11.16 — find current MD/AD/PD lords from chain so STEP 6
    # can detect dasha-lord transit through travel houses 3/9/12.
    _current_row = next((c for c in chain
                          if c["start"] <= now <= c["end"]), None)
    _current_lords = ({"MD": _current_row["md"],
                        "AD": _current_row["ad"],
                        "PD": _current_row["pd"]}
                       if _current_row else None)
    transits = _step6_transits(kundli, lagna_si, planets_d1, now,
                                 current_dasha_lords=_current_lords)
    transit_load = sum(w for _, _, w in transits.get("active_triggers", []))
    factors.append(f"STEP6 transit_load={transit_load:.2f}")

    # ── STEP 7 ──
    ashta = _step7_ashtakavarga(kundli, lagna_si)
    factors.append(f"STEP7 SAV_9={ashta['sav_9']} SAV_12={ashta['sav_12']} "
                    f"foreign_band={ashta['foreign_band']}")

    # ── STEP 9 ──
    yogas = _detect_yogas(kundli, lagna_si, planets_d1)
    factors.append(f"STEP9 yogas={[y['name'] for y in yogas]}")

    # Foreign-promised composite flag
    foreign_promised = _detect_foreign_promised(yogas, kp_layer,
                                                  ashta["foreign_band"], ranked)
    factors.append(f"FOREIGN_PROMISED={foreign_promised}")

    # ── Window selection + severity ──
    top3 = _select_top_3(dasha_windows)
    formatted_top3: List[Dict[str, Any]] = []
    confirmations_severe = 0
    for w in top3:
        sev = _severity_of_window(w["score"], transit_load,
                                    w.get("risk_raw", 0.0))
        if sev == "consult":
            confirmations_severe += 1
        formatted_top3.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "score": w["score"], "severity": sev,
            "kind": w.get("kind", "general"),
            "kp_boost": w.get("kp_boost", 0.0),
            "kp_hits": w.get("kp_hits", []),
            "window": _format_window(w["start"], w["end"]),
            "start_iso": w["start"].isoformat(),
            "end_iso": w["end"].isoformat(),
            "triggers": w["triggers"],
        })

    # Phase 2.5.11.15 — UNIVERSAL DOUBLE TRANSIT (K.N.Rao classical rule).
    # For ANY timing window (past/present/future), annotate with Jupiter+
    # Saturn double-transit verdict on travel concern houses [3, 9, 12].
    # User mandate: "Jab bhi event prediction ki baat aayega — kab hoga,
    # kab gaya tha, kab jaaunga — Jupiter+Sani ka double transit COMPULSORY."
    from event_timing._shared.double_transit import (
        check_double_transit, midpoint, CONCERN_HOUSES,
    )
    _TRAVEL_CONCERN = CONCERN_HOUSES["travel"]   # [3, 9, 12]

    # Phase 2.5.11.15-b (architect MAJOR fix) — multi-sample (start/mid/end)
    # so a Jupiter or Saturn sign-crossing within the window does not
    # misclassify the verdict. Take the BEST sample (highest score) since
    # classical rule: event can fructify any time the double-transit is
    # active during the favorable dasha window. `samples_varied` flag
    # surfaces in output for transparency when sky changed mid-window.
    _DT_VERDICT_RANK = {"STRONG": 4, "PARTIAL_J": 3, "PARTIAL_S": 2,
                         "ABSENT": 1, "UNAVAILABLE": 0}

    def _attach_dt(window_start, window_end):
        try:
            mid = midpoint(window_start, window_end)
            samples = [
                ("start", check_double_transit(kundli, window_start, lagna_si,
                                                 planets_d1, _TRAVEL_CONCERN)),
                ("mid",   check_double_transit(kundli, mid,           lagna_si,
                                                 planets_d1, _TRAVEL_CONCERN)),
                ("end",   check_double_transit(kundli, window_end,   lagna_si,
                                                 planets_d1, _TRAVEL_CONCERN)),
            ]
            # Pick the strongest verdict (tie-broken by score).
            label_best, best = max(samples,
                key=lambda s: (s[1].get("score", 0),
                                _DT_VERDICT_RANK.get(s[1].get("verdict"), 0)))
            verdicts = {s[1].get("verdict") for s in samples}
            best["sample_used"]    = label_best
            best["samples_varied"] = len(verdicts) > 1
            if best["samples_varied"]:
                best["all_samples"] = [
                    {"at": lbl, "verdict": s.get("verdict"),
                     "score": s.get("score", 0)}
                    for lbl, s in samples
                ]
            return best
        except Exception as e:
            return {"verdict": "UNAVAILABLE", "active": False,
                     "score": 0, "note": f"dt_calc_error: {e}"}

    # Annotate next_3 windows
    for fw, raw in zip(formatted_top3, top3):
        fw["double_transit"] = _attach_dt(raw["start"], raw["end"])

    current = next((w for w in dasha_windows
                     if w["start"] <= now <= w["end"]), None)
    current_window = None
    if current:
        sev = _severity_of_window(current["score"], transit_load,
                                    current.get("risk_raw", 0.0))
        current_window = {
            "md": current["md"], "ad": current["ad"], "pd": current["pd"],
            "start_iso": current["start"].isoformat(),
            "end_iso": current["end"].isoformat(),
            "severity": sev,
            "kind": current.get("kind", "general"),
            "kp_boost": current.get("kp_boost", 0.0),
            "kp_hits": current.get("kp_hits", []),
            "triggers": current["triggers"],
            "double_transit": check_double_transit(
                kundli, now, lagna_si, planets_d1, _TRAVEL_CONCERN),
        }

    # Protection windows = upcoming where Jupiter/Venus/9L rules
    h9_lord = _house_lord(lagna_si, 9)
    benefics = {"Jupiter", "Venus", h9_lord}
    protection_windows = []
    for w in dasha_windows[:30]:
        if w["ad"] in benefics or w["pd"] in benefics:
            protection_windows.append({
                "md": w["md"], "ad": w["ad"], "pd": w["pd"],
                "window": _format_window(w["start"], w["end"]),
                "start_iso": w["start"].isoformat(),
                "end_iso": w["end"].isoformat(),
            })
        if len(protection_windows) >= 3:
            break

    top_score = formatted_top3[0]["score"] if formatted_top3 else 0.0
    verdict, band = _derive_verdict(top_score, ashta["foreign_band"],
                                       yogas, transit_load, foreign_promised)
    severity_now = (current_window["severity"]
                     if current_window else "supportive")
    rec_tier = _recommendation_tier(severity_now, confirmations_severe, age)
    # Consistency rule: HIGH_RISK_TRAVEL forces consult tier
    if verdict == "HIGH_RISK_TRAVEL":
        rec_tier = "consult"

    # LLM directives — mandatory travel safeguards
    llm_directives = ["TRAVEL_DISCLAIMER",
                       "NO_GUARANTEED_VISA_OUTCOME",
                       "NO_GUARANTEED_TRAVEL_DATE",
                       "NO_DESTINATION_NAMING",
                       f"SEVERITY_TIER:{rec_tier}"]
    if foreign_promised:
        llm_directives.append("FOREIGN_TRAVEL_INDICATED")
        llm_directives.append("CONSULT_PROFESSIONAL_FOR_LEGAL")
    if confirmations_severe >= _CONFIRMATIONS_FOR_CONSULT:
        llm_directives.append("CONSULT_TIER")
    if verdict == "HIGH_RISK_TRAVEL":
        llm_directives.append("ADVISE_TRAVEL_INSURANCE_AND_CAUTION")

    risk_flags: List[str] = []
    if ashta["foreign_band"] == "WEAK":
        risk_flags.append("LOW_SAV_FOREIGN_BAND")
    if any(y.get("severity") == "high" for y in yogas):
        risk_flags.append("NEGATIVE_TRAVEL_YOGA")
    if any("Risk-Travel" in (y.get("name") or "") for y in yogas):
        risk_flags.append("ACCIDENT_LEGAL_RISK_YOGA")
    if any("Visa-Block" in (y.get("name") or "") for y in yogas):
        risk_flags.append("VISA_BLOCK_YOGA")
    if transit_load >= 1.5 and any("risk" in t[0]
                                     for t in transits.get("active_triggers", [])):
        risk_flags.append("HEAVY_RISK_TRANSIT")
    if kp_layer.get("verdict_12") == "BLOCKED_OR_RISKY":
        risk_flags.append("KP_12CSL_DUSTHANA")

    breakdown = {
        r["name"]: {"d1": r["d1"], "d9": r["d9"], "d4": r["d4"],
                     "kp": r["kp"], "karaka": r["karaka"],
                     "total": r["score"]}
        for r in ranked
    }

    affected = _affected_areas(ranked)
    remedies = _compute_travel_remedies(ranked, affected, rec_tier)
    # Past windows (Phase 2.5.11.14, expanded to top-10 in 2.5.11.16) —
    # historical favorable windows. IMPORTANT: these are "favorable
    # opportunities astrologically", NEVER confirmation that the user
    # actually traveled. UCML must confirm event. Cap raised from 3→10
    # so legitimate KP-fortified windows (e.g. Sep-2025 Moon-Moon-Mercury
    # on Rajalaxmi chart) aren't truncated by higher-scoring older
    # windows that may not have actually fructified.
    # Phase 2.5.11.16 — MD-diversity cap so a single dominant MD (e.g.
    # 6yr Sun-MD with 12H stack) cannot monopolize all 10 past slots
    # and bury legitimate KP-fortified windows from other MDs (e.g.
    # Moon-MD's Sep-2025 Moon-Moon-Mercury). Cap each MD to ≤3 slots
    # while preserving global score order.
    # MD_CAP=4 guarantees that Moon-MD's 4th-best window (e.g.
    # Sep-2025 Moon-Moon-Mercury) can surface even when 6yr Sun-MD
    # has many higher-scoring competitors. Total cap raised 10 → 12
    # to absorb the diversified slate; locked_facts trace mirror is
    # also [:12] (still well under the 60-line hard cap).
    _MD_CAP = 4
    _PAST_TOTAL_CAP = 12
    _md_count: Dict[str, int] = {}
    _diversified: List[Dict[str, Any]] = []
    for w in past_dasha_windows:
        md = w["md"] or "?"
        if _md_count.get(md, 0) >= _MD_CAP:
            continue
        _md_count[md] = _md_count.get(md, 0) + 1
        _diversified.append(w)
        if len(_diversified) >= _PAST_TOTAL_CAP:
            break
    formatted_past3: List[Dict[str, Any]] = []
    for w in _diversified:
        formatted_past3.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "score": w["score"],
            "kind": w.get("kind", "general"),
            "kp_boost": w.get("kp_boost", 0.0),
            "kp_hits": w.get("kp_hits", []),
            "window": _format_window(w["start"], w["end"]),
            "start_iso": w["start"].isoformat(),
            "end_iso": w["end"].isoformat(),
            "triggers": w["triggers"],
            # Phase 2.5.11.15 — double transit AT the past window's midpoint
            # (NOT today). This tells us whether sky was actually supporting
            # travel during that historical window.
            "double_transit": _attach_dt(w["start"], w["end"]),
        })
    if formatted_past3:
        llm_directives.append("PAST_WINDOW_IS_OPPORTUNITY_NOT_EVENT")
    # Phase 2.5.11.16 — surface KP-dasha-fortification when ANY emitted
    # window (past/current/next) carries a non-empty KP boost.
    _has_kp_boost = (
        any(w.get("kp_boost", 0) > 0 for w in formatted_past3) or
        any(w.get("kp_boost", 0) > 0 for w in top3) or
        (current is not None and current.get("kp_boost", 0) > 0)
    )
    if _has_kp_boost:
        llm_directives.append("KP_DASHA_FORTIFIES_TRAVEL")
    # Phase 2.5.11.15 — universal directive: LLM MUST cite double-transit
    # verdict whenever it discusses any timing window.
    llm_directives.append("DOUBLE_TRANSIT_TIMING_RULE_APPLIED")

    return {
        "verdict": verdict,
        "band": band,
        "foreign_promised": foreign_promised,
        "current_window": current_window,
        "next_3_windows": formatted_top3,
        "past_windows": formatted_past3,
        "protection_windows": protection_windows,
        "affected_areas": affected,
        "recommendation_tier": rec_tier,
        "top_travel_planets": ranked[:5],
        "weighted_breakdown": breakdown,
        "kp_layer": kp_layer,
        "transits": transits,
        "ashtakavarga": ashta,
        "yogas": yogas,
        "risk_flags": risk_flags,
        "factors": factors,
        "llm_directives": llm_directives,
        "remedies": remedies,
        "engine_version": "v1.0.0",
        "engine_arch": "FILTER→VERIFY→KP-GATE→ACTIVATE→TRIGGER",
    }


# ════════════════════════════════════════════════════════════════════════
# Remedy delegation — travel topic
# ════════════════════════════════════════════════════════════════════════
def _compute_travel_remedies(ranked: Optional[List[Dict[str, Any]]],
                               affected_areas: Optional[List[str]],
                               recommendation_tier: Optional[str]
                               ) -> Dict[str, Any]:
    """Delegates to Remedy Engine v1.1 with topic="travel".

    If the remedy engine doesn't yet have a "travel" topic catalog,
    falls back to topic="career" with travel-area tags so a sensible
    PRACTICAL row (e.g. "carry copies of documents", "verify visa
    status") is still surfaced. Returns {} if remedy module missing
    entirely.
    """
    try:
        from remedy import get_remedies  # type: ignore
    except Exception:
        return {}
    try:
        out = get_remedies(
            topic    = "travel",
            planets  = ranked or [],
            areas    = affected_areas or [],
            severity = recommendation_tier,
            user_facts    = None,
            duration_days = 21,
        )
        if out:
            return out
    except Exception:
        pass
    # Graceful fallback — career topic with travel-area context
    try:
        return get_remedies(
            topic    = "career",
            planets  = ranked or [],
            areas    = (affected_areas or []) + ["travel_context"],
            severity = recommendation_tier or "watchful",
            user_facts    = None,
            duration_days = 21,
        )
    except Exception:
        return {}
