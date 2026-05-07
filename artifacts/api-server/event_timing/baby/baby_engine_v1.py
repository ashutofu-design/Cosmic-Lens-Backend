"""
event_timing/baby/baby_engine_v1.py
====================================
COSMIC LENS BABY (CHILDBIRTH) TIMING ENGINE v1.0 — clean build,
mirrors Health v1 / Marriage v2.4 / Finance v1 / Travel v1
architecture.

Architecture: FILTER → VERIFY → ACTIVATE → TRIGGER (9-step pipeline,
locked May 7 2026 per user spec "baby timing ke liye d1 d7 kp ko mila
kar timing engine").

  STEP 1   D1 child-significator filter             (FILTER)
           - 5L  (PUTRASTHANA — primary children house)
           - 9L  (dharma/grace, secondary support)
           - 11L (gain/fulfillment of desires)
           - 7L  (spouse/conception partner)
           - 2L  (family expansion / kutumb)
           - Occupants of 5 / 9 / 11
           - Planets ASPECTING the 5th house (most powerful trigger)
           - Karakas: Jupiter (PRIMARY putra karaka), Sun, Moon
             (fertility/water), Venus (procreative seed), Mars (vigor)
  STEP 2   D9 dignity verification                  (VERIFY)
  STEP 3   D7 Saptamsha (children chart)            (VERIFY)
           Parashara: D7 governs children & progeny. Each sign divides
           into 7 parts (~4°17'). Odd signs count from same sign;
           even signs count from 7th sign. Falls back to D1-dignity
           when divisional_charts.compute_d7 helper missing.
  STEP 3.5 KP CSL of 5 & 11 cusps
  STEP 4   Weighted ranking
           D1·30 + D9·20 + D7·25 + KP·15 + karaka·10
  STEP 5   Dasha activation (AD/PD primary; MD low-weight)
           AD=5, PD=6, MD=1. Signed contribution: pure child-promoter
           (5L/9L/Jupiter) raises score; obstruction-bearer
           (6L/8L/12L) lowers it.
  STEP 6   Transit triggers
           Jupiter on 5/9/11 = conception window (PRIMARY trigger),
           Saturn on 5H = delay/postponement,
           Rahu on 5H = unconventional (IVF/adoption) route,
           Mars on 8/12 = miscarriage risk,
           Sade Sati on Moon = emotional family stress
  STEP 7   Ashtakavarga support (SAV bindus on 5H + 11H — santan band)
  STEP 8   KP cuspal sub lord of 5 (child verdict)
  STEP 9   Yoga + hard-guard layer
           POSITIVE: Putra Yoga (5L+9L conjunction/exchange),
           Santan-Prapti (Jupiter aspects 5H or 5L),
           Putra-Karaka-Bala (Jupiter exalted/own sign)
           NEGATIVE: Bandhya Yoga (5L in 6/8/12 + Jupiter weak),
           Putra-Dosha (5H surrounded by malefics, no Jupiter aspect),
           Miscarriage-Yoga (8L+5L conjunction with malefic),
           Adoption-Indicated (5L in 12H + Rahu on 5H)

Public function:
  compute_baby_window(kundli, intel, kp, birth) -> dict

Output dict (back-compat with health/finance/travel-style consumers):
  {
    "verdict":              "CHILD_PROMISED" | "FAVORABLE" |
                            "DELAYED" | "OBSTRUCTED" | "UNKNOWN",
    "band":                 "WEAK" | "MEDIUM" | "STRONG",
    "child_promised":       bool,                      # composite flag
    "current_window":       {start_iso, end_iso, severity, triggers[]},
    "next_3_windows":       [{md, ad, pd, score, severity, window,
                              start_iso, end_iso, kind}],
    "protection_windows":   [{md, ad, pd, window, start_iso, end_iso}],
    "affected_areas":       ["natural_conception", "ivf_route",
                              "adoption_path", ...],
    "recommendation_tier":  "watchful" | "supportive" |
                            "celebratory" | "consult",
    "top_child_planets":    [{name, score, d1, d9, d7, kp, karaka,
                               significations[]}],
    "weighted_breakdown":   {planet: {d1, d9, d7, kp, karaka, total}},
    "kp_layer":             {csl_5, csl_11, verdict_5, verdict_11},
    "transits":             {jupiter, saturn, rahu, mars,
                              sade_sati, active_triggers[]},
    "ashtakavarga":         {sav_5, sav_11, santan_band},
    "yogas":                [{name, severity, planets}],
    "risk_flags":           [str],
    "factors":              [str],
    "llm_directives":       [str],
    "remedies":             {...},
    "engine_version":       "v1.0.0",
    "engine_arch":          "FILTER→VERIFY→ACTIVATE→TRIGGER",
  }

Hard guards (per user policy + replit.md):
  - Mandatory BABY_DISCLAIMER (medical fertility outcome cannot be
    guaranteed by astrology)
  - NOT_MEDICAL_ADVICE / NO_GUARANTEED_CONCEPTION / NO_GUARANTEED_DATE
  - **NO_GENDER_PREDICTION** — engine NEVER predicts boy/girl
    (PCPNDT Act compliance + global ethical norm)
  - 3-confirmation rule for `consult` tier (high-risk fertility)
  - Conditional CONSULT_FERTILITY_SPECIALIST when OBSTRUCTED
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Thread-local cache for the most recent engine result.
_LAST_RESULT = threading.local()


def get_last_baby_result() -> Optional[Dict[str, Any]]:
    return getattr(_LAST_RESULT, "value", None)


def _store_last_result(result: Dict[str, Any]) -> None:
    _LAST_RESULT.value = result


def clear_last_baby_result() -> None:
    if hasattr(_LAST_RESULT, "value"):
        _LAST_RESULT.value = None


# ── External helpers ──
try:
    from divisional_charts import compute_d9  # type: ignore
except Exception:
    compute_d9 = None  # type: ignore

try:
    # D7 (Saptamsha) — children chart. Optional; may not exist.
    from divisional_charts import compute_d7  # type: ignore
except Exception:
    compute_d7 = None  # type: ignore

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

# 27 nakshatras spanning 360° (each = 13°20′ = 13.3333…°). Used by
# Step 6 for exact transit position labelling (no extra computation —
# straight longitude → nakshatra + pada lookup).
_NAK_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
_NAK_SPAN = 360.0 / 27.0  # 13.3333…°
_PADA_SPAN = _NAK_SPAN / 4.0  # 3.3333…°

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

# Child-significant houses
_CHILD_HOUSES       = [5, 9, 11]   # primary fertility/progeny
_OBSTRUCTION_HOUSES = [6, 8, 12]   # delay / loss / miscarriage
_FAMILY_HOUSES      = [2, 7]       # support (kutumb / partner)

# KP classical childbirth significator houses (2-5-11 rule).
#   2  = family expansion (kutumb-vridhi)
#   5  = progeny (putrasthana)
#   11 = fulfillment of desire / gain of children
# Negation houses for child = 1 (self only), 4 (home stillness),
# 10 (career-opposite-family). A planet whose star-lord OR sub-lord
# signifies ONLY negation houses with zero 2-5-11 link cannot promise
# a child in its dasha — classical Krishnamurti Paddhati rule.
_KP_CHILD_HOUSES    = {2, 5, 11}
_KP_NEGATION_HOUSES = {1, 4, 10}

_WEIGHT_D1     = 0.30
_WEIGHT_D9     = 0.20
_WEIGHT_D7     = 0.25
_WEIGHT_KP     = 0.15
_WEIGHT_KARAKA = 0.10

_DASHA_SCORE_MD = 1
_DASHA_SCORE_AD = 5
_DASHA_SCORE_PD = 6

_D1_FILTER_MIN_SCORE = 12.0
_MIN_WINDOW_GAP_DAYS = 45

# SAV bands (avg of 5H + 11H — santan strength)
_SAV_SANTAN_WEAK   = 25
_SAV_SANTAN_STRONG = 32

_CONFIRMATIONS_FOR_CONSULT = 3

_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
               "Saturn", "Rahu", "Ketu"]

# Child-area signification per planet (NEVER includes gender)
_AREA_OF_PLANET: Dict[str, List[str]] = {
    "Sun":     ["family_lineage_continuation", "vitality_for_conception"],
    "Moon":    ["fertility_emotional_readiness", "maternal_health",
                 "natural_conception"],
    "Mars":    ["procreative_vigor", "blood_health_for_conception"],
    "Mercury": ["nervous_system_balance",
                 "communication_with_fertility_team"],
    "Jupiter": ["progeny_grace", "natural_conception",
                 "spiritual_blessing_for_child"],
    "Venus":   ["reproductive_health", "harmonious_relationship_for_child"],
    "Saturn":  ["delayed_conception", "ivf_or_assisted_route",
                 "structured_family_planning"],
    "Rahu":    ["unconventional_route", "ivf_route",
                 "surrogacy_or_adoption_consideration"],
    "Ketu":    ["spiritual_detachment_phase", "miscarriage_history_check",
                 "adoption_path"],
}

# Functional benefics by lagna sign (used by Step 4 karaka boost).
# Functional MALEFICS table was removed in Phase 2.5.2 lean refactor —
# obstruction signal lives in Step 5 (6/8/12 occupancy + Saturn/Mars/Ketu
# risk tags) and dignity lives in Step 2 (D9) + Step 3 (D7); a separate
# malefic surcharge double-counted both.
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
# Low-level helpers (aligned with travel v1 / finance v1 / health v1)
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


def _planet_longitude(planets: List[dict], pname: str) -> Optional[float]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            lon = p.get("longitude")
            if isinstance(lon, (int, float)):
                return float(lon)
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


def _get_planet_kp_lords(kp: dict,
                          planet: str
                          ) -> Tuple[Optional[str], Optional[str]]:
    """Return (nakshatra_lord, sub_lord) for a planet from the KP block.
    Tolerant of multiple key spellings (`nl`/`nakshatra_lord`,
    `sb`/`sub_lord`/`subLord`). Returns (None, None) when KP data
    is missing or the planet isn't found.
    """
    if not kp:
        return None, None
    for p in (kp.get("planets") or []):
        if not isinstance(p, dict):
            continue
        if str(p.get("name", "")).lower() != planet.lower():
            continue
        nl = (p.get("nl") or p.get("nakshatra_lord")
                or p.get("starLord") or p.get("star_lord"))
        sb = (p.get("sb") or p.get("sub_lord")
                or p.get("subLord") or p.get("sl"))
        return nl, sb
    return None, None


# ════════════════════════════════════════════════════════════════════════
# STEP 1 — D1 child-significator filter
# ════════════════════════════════════════════════════════════════════════
def _step1_d1_filter(kundli: dict, lagna_si: int
                       ) -> Dict[str, Dict[str, Any]]:
    """Identify child-significant planets in D1 — LEAN core only.

    Inclusion (Parashara minimum-viable, no over-engineering):
      • 5L (PUTRASTHANA — primary children house)  — highest weight
      • 9L (dharma / grace — bhagya support)        — high weight
      • 11L (gain / fulfillment of desires)         — medium weight
      • Occupants of 5 / 9 / 11                      — direct evidence
      • Planets aspecting 5H                         — most powerful trigger
      • Karakas: Jupiter (PRIMARY) + Moon + Venus    — natural significators

    Deliberately EXCLUDED (handled elsewhere or low-signal):
      • 7L, 2L                — out of scope for baby; over-engineering
      • 6/8/12 occupant boost — fertility-leak handled in Step 5
                                 (dasha obstruction-bearer classification)
      • Sun, Mars karaka      — double-counts lordship/occupancy
      • Functional-malefic    — Step 4 ranking handles dignity already
    """
    planets = kundli.get("planets") or []
    out: Dict[str, Dict[str, Any]] = {}
    for p in _PLANETS_9:
        out[p] = {"d1": 0.0, "in_filter": False, "links": [],
                   "is_lord_of": [], "occupies": None,
                   "aspects_5": False}

    # 1) Lordship — 5L / 9L / 11L only
    for h, weight, label in (
        (5,  18.0, "5L (PUTRASTHANA — primary children house)"),
        (9,  12.0, "9L (dharma/grace, secondary support)"),
        (11, 10.0, "11L (gain/fulfillment of desires)"),
    ):
        lord = _house_lord(lagna_si, h)
        out[lord]["is_lord_of"].append(h)
        out[lord]["d1"] += weight
        out[lord]["links"].append(label)

    # 2) Occupants of child houses 5 / 9 / 11
    for h in (5, 9, 11):
        for pname in _planets_in_house(planets, h):
            out[pname]["occupies"] = h
            bump = {5: 14.0, 9: 10.0, 11: 8.0}[h]
            out[pname]["d1"] += bump
            out[pname]["links"].append(f"occupies {h}H (child-house)")

    # 3) Planets aspecting the 5th house (most powerful trigger)
    for pname in _PLANETS_9:
        ap_house = _planet_house(planets, pname)
        if ap_house and _aspects_house(pname, ap_house, 5):
            out[pname]["aspects_5"] = True
            out[pname]["d1"] += 9.0
            out[pname]["links"].append("aspects 5H (child-house activation)")

    # 4) Child karakas — Jupiter PRIMARY, Moon + Venus secondary
    for karaka, bonus, role in (
        ("Jupiter", 14.0, "PROGENY-KARAKA (primary — Jupiter)"),
        ("Moon",     8.0, "fertility/maternal karaka (Moon)"),
        ("Venus",    7.0, "reproductive-health karaka (Venus)"),
    ):
        out[karaka]["d1"] += bonus
        out[karaka]["links"].append(role)

    for pname, info in out.items():
        info["in_filter"] = info["d1"] >= _D1_FILTER_MIN_SCORE

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 2 — D9 dignity verification
# ════════════════════════════════════════════════════════════════════════
def _build_d9_chart(kundli: dict) -> Optional[Dict[str, Any]]:
    """Compute the full D9 Navamsha chart once, with proper D9 lagna +
    D9-house assignment per planet. Mirrors `_build_d7_chart` shape so
    Step 2 (dignity), Step 3c (cross-chart filter), and any future D9
    consumer use the same structure.

    Returns:
        {"lagna_si": int, "planets": [{name, sign, sign_idx, house}], ...}
        or None if D9 helper unavailable / longitudes missing.
    """
    if compute_d9 is None:
        return None
    d1_planets = kundli.get("planets") or []
    if not d1_planets:
        return None
    asc_lon = kundli.get("ascendant_longitude")
    try:
        ext = compute_d9(d1_planets,
                          float(asc_lon)
                          if isinstance(asc_lon, (int, float)) else None)
    except Exception:
        return None
    if not isinstance(ext, dict) or not ext:
        return None

    d9_lagna_si: Optional[int] = None
    d9_planet_map: Dict[str, int] = {}
    for k, v in ext.items():
        if k == "_lagna" and isinstance(v, dict):
            si = v.get("sign_idx")
            if isinstance(si, int):
                d9_lagna_si = si % 12
            continue
        if isinstance(v, dict):
            si = v.get("sign_idx")
            if isinstance(si, int) and k in _PLANETS_9:
                d9_planet_map[k] = si % 12

    if d9_lagna_si is None or not d9_planet_map:
        return None

    planets_list: List[Dict[str, Any]] = []
    for nm in _PLANETS_9:
        if nm in d9_planet_map:
            si = d9_planet_map[nm]
            planets_list.append({
                "name":     nm,
                "sign":     _SIGNS[si],
                "sign_idx": si,
                "house":    _house_of_sign(si, d9_lagna_si),
            })
    return {"lagna_si": d9_lagna_si, "planets": planets_list}


def _step2_d9_verify(kundli: dict, candidates: Set[str],
                       d9_chart: Optional[Dict[str, Any]] = None
                       ) -> Dict[str, float]:
    """Verify D1 survivors via D9 dignity (exalted 25 / own 20 /
    neutral 12 / debilitated 5 / unknown 8 fallback). Uses pre-built
    `d9_chart` when supplied — same chart Step 3c consumes for
    cross-chart confirmation, so dignity and confirmation can never
    disagree.
    """
    out: Dict[str, float] = {p: 0.0 for p in candidates}
    if not candidates:
        return out
    if d9_chart is None:
        d9_chart = _build_d9_chart(kundli)
    d9_planets = (d9_chart or {}).get("planets") or []
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
# STEP 3 — D7 Saptamsha (children chart)
# ════════════════════════════════════════════════════════════════════════
def _compute_d7_sign(longitude: float, natal_sign_si: int) -> int:
    """Compute Saptamsha sign for a given longitude.

    Rule (Parashara): each sign (30°) divides into 7 parts of ~4°17'8".
    For ODD signs (Aries, Gemini, Leo, ...): D7 count starts from
        the same sign.
    For EVEN signs (Taurus, Cancer, ...): D7 count starts from the
        7th sign from the natal sign.
    """
    deg_in_sign = longitude % 30.0
    part = int(deg_in_sign / (30.0 / 7.0))   # 0-6
    # Sign-numbering convention: Aries = sign #1 (ODD), Taurus = #2 (EVEN),
    # Gemini = #3 (ODD), etc. In 0-indexed `_SIGN_IDX`, those map to:
    #   ODD signs (1,3,5,7,9,11)  → idx 0,2,4,6,8,10  → idx % 2 == 0
    #   EVEN signs (2,4,6,8,10,12) → idx 1,3,5,7,9,11 → idx % 2 == 1
    # So `natal_sign_si % 2 == 0` correctly classifies an ODD-NUMBERED sign.
    # Verified by tests: Aries@0° → Aries (D7 part 0 of odd sign).
    if natal_sign_si % 2 == 0:               # odd-numbered natal sign
        start = natal_sign_si
    else:                                     # even-numbered natal sign
        start = (natal_sign_si + 6) % 12      # count from 7th
    return (start + part) % 12


def _build_d7_chart(kundli: dict, lagna_si: int
                     ) -> Optional[Dict[str, Any]]:
    """Compute the full D7 Saptamsha chart once and return a structured
    snapshot reusable by Step 3 (scoring) and Step 3b (picture).

    Returns:
        {
          "lagna_si": int,                       # D7 ascendant sign idx
          "planets":  [{name, sign, sign_idx, house}],  # all D7 positions
          "source":   "external"|"internal"
        }
        or None if longitudes are unavailable for all 9 planets.

    Tier-1: try external `divisional_charts.compute_d7`.
    Tier-2: internal longitude-based computation (Parashara odd/even rule).
    """
    d1_planets = kundli.get("planets") or []
    asc_lon = kundli.get("ascendant_longitude")

    # Tier-1: external compute_d7 helper. divisional_charts returns a
    # dict keyed by planet name with {sign, sign_idx, vargottama} +
    # an optional `_lagna` key.
    d7_lagna_si: Optional[int] = None
    d7_planet_map: Dict[str, int] = {}      # name → D7 sign_idx
    if compute_d7 is not None:
        try:
            ext = compute_d7(d1_planets,
                              float(asc_lon)
                              if isinstance(asc_lon, (int, float))
                              else None)
            if isinstance(ext, dict) and ext:
                for k, v in ext.items():
                    if k == "_lagna" and isinstance(v, dict):
                        si = v.get("sign_idx")
                        if isinstance(si, int):
                            d7_lagna_si = si % 12
                        continue
                    if isinstance(v, dict):
                        si = v.get("sign_idx")
                        if isinstance(si, int) and k in _PLANETS_9:
                            d7_planet_map[k] = si % 12
        except Exception:
            d7_planet_map = {}

    source = "external" if d7_planet_map else "internal"

    # Tier-2: internal longitude-based computation as fallback / primary
    # for any planet missing from the external map.
    for p in d1_planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if nm not in _PLANETS_9 or nm in d7_planet_map:
            continue
        lon = p.get("longitude")
        si = p.get("sign_idx")
        if isinstance(si, str):
            si = _sign_idx(si)
        if isinstance(lon, (int, float)) and isinstance(si, int):
            d7_planet_map[nm] = _compute_d7_sign(float(lon), si % 12)

    # D7 lagna fallback. We DO NOT silently default to natal lagna_si
    # when neither the external `_lagna` key nor `ascendant_longitude`
    # is available — D7 lagna depends on ascendant longitude (Parashara
    # odd/even partitioning), so a sign-only fallback would silently
    # mis-place the D7 1L / 5L. Degrade the chart instead, letting Step
    # 3 fall through to its D1-dignity proxy and the picture report
    # `available=False`.
    if d7_lagna_si is None:
        if isinstance(asc_lon, (int, float)):
            d7_lagna_si = _compute_d7_sign(float(asc_lon), lagna_si)
        else:
            return None

    if not d7_planet_map:
        return None

    planets_list: List[Dict[str, Any]] = []
    for nm in _PLANETS_9:
        if nm in d7_planet_map:
            si = d7_planet_map[nm]
            planets_list.append({
                "name":     nm,
                "sign":     _SIGNS[si],
                "sign_idx": si,
                "house":    _house_of_sign(si, d7_lagna_si),
            })
    return {"lagna_si": d7_lagna_si,
            "planets":  planets_list,
            "source":   source}


def _step3_d7_progeny(kundli: dict, candidates: Set[str],
                        lagna_si: int,
                        d7_chart: Optional[Dict[str, Any]] = None
                        ) -> Dict[str, float]:
    """D7 governs children & progeny — Parashara's children chart.

    Uses pre-built `d7_chart` if provided (preferred — same chart as the
    Step 3b picture). Falls back to a fresh build, then to D1-dignity
    proxy if no longitudes are available. Range 0-25.
    """
    out: Dict[str, float] = {p: 0.0 for p in candidates}
    if not candidates:
        return out

    if d7_chart is None:
        d7_chart = _build_d7_chart(kundli, lagna_si)

    # Tier-3: D1-dignity fallback proxy if D7 unavailable
    if not d7_chart or not d7_chart.get("planets"):
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

    d7_planets = d7_chart["planets"]
    for pname in candidates:
        si = _planet_sign_idx(d7_planets, pname)
        if si is None:
            out[pname] = 8.0; continue
        h_in_d7 = _planet_house(d7_planets, pname) or 0
        score = 8.0
        # Child-promise boost: 5H/9H/11H of D7
        if h_in_d7 == 5:
            score = 22.0
        elif h_in_d7 == 9:
            score = 18.0
        elif h_in_d7 == 11:
            score = 16.0
        elif h_in_d7 in (6, 8, 12):
            # Obstruction houses in D7 → score down
            score = 5.0
        # Dignity adjustment
        if pname in _EXALT and si == _EXALT[pname]:
            score = min(25.0, score + 4.0)
        elif pname in _DEBIL and si == _DEBIL[pname]:
            score = max(3.0, score - 4.0)
        out[pname] = score
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3b — D7 Picture (lord positions, occupants, aspects, dignity)
# ════════════════════════════════════════════════════════════════════════
def _dignity_label(pname: str, sign_si: int) -> str:
    """Avastha label for a planet in a sign.

    Returns one of: "exalted" | "own" | "debilitated" | "neutral".
    """
    if pname in _EXALT and sign_si == _EXALT[pname]:
        return "exalted"
    if pname in _OWN_SIGNS and sign_si in _OWN_SIGNS[pname]:
        return "own"
    if pname in _DEBIL and sign_si == _DEBIL[pname]:
        return "debilitated"
    return "neutral"


def _step3b_d7_picture(d7_chart: Optional[Dict[str, Any]],
                         lagna_si: int) -> Dict[str, Any]:
    """User-requested D7 progeny snapshot.

    Captures, *inside* the D7 Saptamsha chart:
      • D7 lagna sign + D7 1L (lord of D7 lagna): which sign, which D7
        house, dignity (exalted/own/debilitated/neutral), aspecting-or-
        not the D7 5H.
      • D7 5L (lord of D7 5H): which sign, which D7 house, dignity,
        and whether it occupies a child-house (5/9/11) of the D7.
      • D7 1H occupants and D7 5H occupants.
      • Planets aspecting D7 1H and D7 5H.
      • A small `flags` block summarising the picture for verdict use:
          - jupiter_aspects_d7_5h  (strong protective signal)
          - benefic_in_d7_5h       (Jupiter / Venus / Mercury / Moon)
          - malefic_in_d7_5h       (Sun / Mars / Saturn / Rahu / Ketu)
          - d7_5l_in_dusthana      (D7 5L in D7 6/8/12 — Bandhya signal)
          - d7_5l_well_placed      (D7 5L in D7 1/5/9/11 with non-debil)

    Returns an `available` flag (False when no D7 longitudes exist) so
    downstream consumers can render a graceful fallback.
    """
    out: Dict[str, Any] = {
        "available":              False,
        "source":                 "none",
        "d7_lagna":               None,
        "d7_lagna_sign_idx":      None,
        "first_lord":             None,
        "fifth_lord":             None,
        "first_house_occupants":  [],
        "fifth_house_occupants":  [],
        "aspects_to_first_house": [],
        "aspects_to_fifth_house": [],
        "flags":                  {},
        "note":                   "",
    }
    if not d7_chart or not d7_chart.get("planets"):
        out["note"] = ("D7 Saptamsha chart unavailable (no planet "
                        "longitudes); progeny analysis falling back "
                        "to D1 dignity proxy.")
        return out

    d7_lagna_si = d7_chart["lagna_si"]
    d7_planets = d7_chart["planets"]
    out["available"] = True
    out["source"] = d7_chart.get("source", "internal")
    out["d7_lagna"] = _SIGNS[d7_lagna_si]
    out["d7_lagna_sign_idx"] = d7_lagna_si

    # ── D7 1L (lord of D7 lagna sign) ──
    first_lord = _SIGN_LORDS[d7_lagna_si]
    fl_si = _planet_sign_idx(d7_planets, first_lord)
    fl_h  = _planet_house(d7_planets, first_lord)
    out["first_lord"] = {
        "planet":         first_lord,
        "sign":           _SIGNS[fl_si] if fl_si is not None else None,
        "sign_idx":       fl_si,
        "house_in_d7":    fl_h,
        "dignity":        (_dignity_label(first_lord, fl_si)
                           if fl_si is not None else "unknown"),
        "aspects_d7_5h":  (_aspects_house(first_lord, fl_h, 5)
                            if fl_h else False),
    }

    # ── D7 5L (lord of D7 5th sign from D7 lagna) ──
    fifth_sign_si = (d7_lagna_si + 4) % 12
    fifth_lord = _SIGN_LORDS[fifth_sign_si]
    fih_si = _planet_sign_idx(d7_planets, fifth_lord)
    fih_h  = _planet_house(d7_planets, fifth_lord)
    fih_dignity = (_dignity_label(fifth_lord, fih_si)
                    if fih_si is not None else "unknown")
    in_dusthana = fih_h in _OBSTRUCTION_HOUSES if fih_h else False
    in_child_house = fih_h in _CHILD_HOUSES if fih_h else False
    in_kendra_or_trine = fih_h in (1, 4, 5, 7, 9, 10) if fih_h else False
    well_placed = (in_kendra_or_trine
                    and fih_dignity != "debilitated"
                    and not in_dusthana)
    out["fifth_lord"] = {
        "planet":         fifth_lord,
        "sign":           _SIGNS[fih_si] if fih_si is not None else None,
        "sign_idx":       fih_si,
        "house_in_d7":    fih_h,
        "dignity":        fih_dignity,
        "in_child_house": in_child_house,
        "in_dusthana":    in_dusthana,
        "well_placed":    well_placed,
    }

    # ── D7 1H + 5H occupants ──
    out["first_house_occupants"] = _planets_in_house(d7_planets, 1)
    out["fifth_house_occupants"] = _planets_in_house(d7_planets, 5)

    # ── Aspects to D7 1H and D7 5H ──
    asp_1h: List[str] = []
    asp_5h: List[str] = []
    for pname in _PLANETS_9:
        ph = _planet_house(d7_planets, pname)
        if not ph:
            continue
        if ph != 1 and _aspects_house(pname, ph, 1):
            asp_1h.append(pname)
        if ph != 5 and _aspects_house(pname, ph, 5):
            asp_5h.append(pname)
    out["aspects_to_first_house"] = asp_1h
    out["aspects_to_fifth_house"] = asp_5h

    # ── Summary flags for verdict / yoga consumers ──
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    occ5 = set(out["fifth_house_occupants"])
    asp5 = set(asp_5h)
    flags = {
        "jupiter_aspects_d7_5h": ("Jupiter" in asp5
                                    or "Jupiter" in occ5),
        "benefic_in_d7_5h":      bool(occ5 & benefics),
        "malefic_in_d7_5h":      bool(occ5 & malefics),
        "d7_5l_in_dusthana":     in_dusthana,
        "d7_5l_well_placed":     well_placed,
        "d7_5l_in_child_house":  in_child_house,
        "d7_1l_aspects_5h":      out["first_lord"]["aspects_d7_5h"],
    }
    out["flags"] = flags
    out["note"] = (
        f"D7 lagna {out['d7_lagna']} → 1L {first_lord} "
        f"({out['first_lord']['dignity']}, "
        f"H{fl_h or '?'}); 5L {fifth_lord} "
        f"({fih_dignity}, H{fih_h or '?'})."
    )
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3c — Cross-chart 5H confirmation filter (D1 ∩ D9 ∩ D7)
# ════════════════════════════════════════════════════════════════════════
def _has_5h_link(planet: str, lagna_si: int,
                  planets: List[Dict[str, Any]]) -> List[str]:
    """Return list of 5H-connection labels for a planet inside ANY chart
    (D1 / D9 / D7). Connection counts if planet is:
      • the 5L of that chart's lagna
      • occupant of that chart's 5H
      • aspecting that chart's 5H
      • Jupiter (always — natural progeny karaka)
    """
    links: List[str] = []
    if planet == "Jupiter":
        links.append("karaka")
    if _house_lord(lagna_si, 5) == planet:
        links.append("5L")
    h = _planet_house(planets, planet)
    if h == 5:
        links.append("in_5H")
    if h and _aspects_house(planet, h, 5):
        links.append("aspects_5H")
    return links


def _step3c_cross_chart_filter(
        d1_map: Dict[str, Dict[str, Any]],
        kundli: dict,
        lagna_si: int,
        d9_chart: Optional[Dict[str, Any]],
        d7_chart: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Cross-chart 5H confirmation — a planet truly "gives baby in its
    AD/PD" only when its progeny credentials show up in MULTIPLE charts.

    For each Step-1 survivor, count 5H-connections across:
      • D1 — derived from existing d1_map (5L / occupies 5 / aspects 5
              / Jupiter karaka)
      • D9 — using the pre-built D9 chart (D9 5L of D9 lagna, D9 5H
              occupant, D9 5H aspector, Jupiter)
      • D7 — using the pre-built D7 chart (D7 5L of D7 lagna, D7 5H
              occupant, D7 5H aspector, Jupiter)

    A planet is `cross_confirmed` when confirmations ≥ 2 of 3.
    Returns a dict per planet with `confirmations`, `confirmed_in`,
    `chart_links`, and `cross_confirmed`. Planets unavailable in D9 or
    D7 fall back to the available subset (so a missing D7 doesn't auto-
    fail an otherwise strong D1+D9 planet).
    """
    out: Dict[str, Dict[str, Any]] = {}
    survivors = [p for p, info in d1_map.items() if info.get("in_filter")]

    d1_planets = kundli.get("planets") or []
    d9_planets = (d9_chart or {}).get("planets") or []
    d7_planets = (d7_chart or {}).get("planets") or []
    d9_lagna = (d9_chart or {}).get("lagna_si")
    d7_lagna = (d7_chart or {}).get("lagna_si")

    for p in survivors:
        chart_links: Dict[str, List[str]] = {}

        # D1 — read from d1_map (already computed)
        info = d1_map[p]
        d1_links: List[str] = []
        if 5 in (info.get("is_lord_of") or []):
            d1_links.append("5L")
        if info.get("occupies") == 5:
            d1_links.append("in_5H")
        if info.get("aspects_5"):
            d1_links.append("aspects_5H")
        if p == "Jupiter":
            d1_links.append("karaka")
        if d1_links:
            chart_links["D1"] = d1_links

        # D9
        if d9_planets and d9_lagna is not None:
            d9_links = _has_5h_link(p, d9_lagna, d9_planets)
            if d9_links:
                chart_links["D9"] = d9_links

        # D7
        if d7_planets and d7_lagna is not None:
            d7_links = _has_5h_link(p, d7_lagna, d7_planets)
            if d7_links:
                chart_links["D7"] = d7_links

        confirmed_in = sorted(chart_links.keys())
        out[p] = {
            "confirmations":     len(confirmed_in),
            "confirmed_in":      confirmed_in,
            "chart_links":       chart_links,
            "cross_confirmed":   len(confirmed_in) >= 2,
        }
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3.5 — KP layer (cuspal sub lord of 5 / 11)
# ════════════════════════════════════════════════════════════════════════
def _step3_5_kp_layer(kp: dict, lagna_si: int) -> Dict[str, Any]:
    """KP cuspal sub lord of 5 & 11 cusps.

    Verdict precedence (architect-pattern from travel v1):
      OBSTRUCTED (6/8/12 dusthana) > ANCHORED (only 1H static) >
      CHILD_YES (5/9/11) > NEUTRAL.
    """
    out = {"csl_5": None, "csl_11": None,
           "verdict_5": "UNKNOWN", "verdict_11": "UNKNOWN",
           "csl_5_signifies": [], "csl_11_signifies": []}
    if not kp:
        return out
    for h, key in ((5, "5"), (11, "11")):
        c = _kp_cusp(kp, h)
        if not c:
            continue
        csl = c.get("sl") or c.get("subLord") or c.get("sub_lord")
        out[f"csl_{key}"] = csl
        if not csl:
            continue
        sig = _planet_signified_houses(kp, csl)
        out[f"csl_{key}_signifies"] = sig
        # Precedence: obstruction dominates
        has_obstruct = any(x in (6, 8, 12) for x in sig)
        has_static = sig == [1] or sig == []
        has_child = any(x in _CHILD_HOUSES for x in sig)
        if has_obstruct:
            out[f"verdict_{key}"] = "OBSTRUCTED"
        elif has_static:
            out[f"verdict_{key}"] = "ANCHORED"
        elif has_child:
            out[f"verdict_{key}"] = "CHILD_YES"
        else:
            out[f"verdict_{key}"] = "NEUTRAL"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 4 — Weighted ranking
# ════════════════════════════════════════════════════════════════════════
def _karaka_score(pname: str, lagna_si: int) -> float:
    base = {"Jupiter": 10.0, "Moon": 7.0, "Venus": 6.0,
            "Sun": 5.0, "Mars": 5.0, "Mercury": 4.0,
            "Saturn": 4.0, "Rahu": 4.0, "Ketu": 3.0}.get(pname, 0.0)
    if pname in _FUNC_BENEFICS.get(lagna_si, set()):
        base += 2.0
    return min(10.0, base)


def _step4_rank(d1_map: Dict[str, Dict[str, Any]],
                d9_scores: Dict[str, float],
                d7_scores: Dict[str, float],
                kp: dict, lagna_si: int) -> List[Dict[str, Any]]:
    """Score = D1·30% + D9·20% + D7·25% + KP·15% + Karaka·10%
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
        d7 = d7_scores.get(pname, 8.0)
        sig = _planet_signified_houses(kp, pname)
        kp_score = 0.0
        if any(h in _CHILD_HOUSES for h in sig):
            kp_score = 18.0
        if 5 in sig:
            kp_score += 5.0
        if 11 in sig:
            kp_score += 3.0
        kp_score = min(25.0, kp_score) if kp_score > 0 else 6.0
        karaka = _karaka_score(pname, lagna_si) * 2.5
        total = (d1 * _WEIGHT_D1 + d9 * _WEIGHT_D9 +
                 d7 * _WEIGHT_D7 + kp_score * _WEIGHT_KP +
                 karaka * _WEIGHT_KARAKA)
        ranked.append({
            "name": pname,
            "score": round(total, 2),
            "d1": round(d1, 2), "d9": round(d9, 2),
            "d7": round(d7, 2), "kp": round(kp_score, 2),
            "karaka": round(karaka, 2),
            "links": list(info["links"]),
            "significations": _AREA_OF_PLANET.get(pname, []),
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


# ════════════════════════════════════════════════════════════════════════
# STEP 4c — KP 2-5-11 significator filter (final pre-dasha gate)
# ════════════════════════════════════════════════════════════════════════
def _step4c_kp_significator_filter(
        ranked: List[Dict[str, Any]],
        kp: dict,
        ) -> Dict[str, Any]:
    """Classical KP childbirth significator filter.

    KP rule (Krishnamurti Paddhati, Childbirth chapter):
      A planet PROMISES a child in its dasha only if BOTH its
      nakshatra-lord (star-lord / NL) AND its sub-lord (SBL)
      signify at least one of the child houses {2, 5, 11}.

    Houses:
      • 2  = family expansion (kutumb-vridhi)
      • 5  = primary progeny (putrasthana)
      • 11 = fulfillment of desire / gain of children

    Negation flag (informational): a planet whose NL/SBL signifies
    ONLY {1, 4, 10} (no 2/5/11 link at all) is recorded as
    `kp_negated=True`. The hard gate is the AND-of-positive rule
    above; negation is exposed for trace transparency.

    Returns:
      {
        "available":   bool,
        "rule":        str,
        "passed":      [planet, ...],   # planets where BOTH NL+SBL signify ≥1 of {2,5,11}
        "blocked":     [planet, ...],
        "per_planet":  {planet: {nl, sbl, nl_houses, sbl_houses,
                                 nl_signifies_child, sbl_signifies_child,
                                 kp_promotes_child, kp_negated}, ...},
      }
    """
    out: Dict[str, Any] = {
        "available":   False,
        "rule":        ("KP childbirth: planet promises child only if "
                        "BOTH nakshatra-lord AND sub-lord signify "
                        "≥1 of houses {2,5,11}"),
        "passed":      [],
        "blocked":     [],
        "unknown":     [],
        "per_planet":  {},
    }
    # Architect-fix: require BOTH kp.planets AND kp.significations to
    # be present and non-empty. Activating with only one side present
    # leaves NL/SBL or significations resolution empty and produces
    # phantom hard-blocks that can collapse legitimate child windows.
    if (not kp
            or not (kp.get("planets") or [])
            or not (kp.get("significations") or {})):
        return out
    out["available"] = True

    for r in ranked:
        pname = r["name"]
        nl, sbl = _get_planet_kp_lords(kp, pname)
        nl_houses  = _planet_signified_houses(kp, nl)  if nl  else []
        sbl_houses = _planet_signified_houses(kp, sbl) if sbl else []
        nl_child  = bool(set(nl_houses)  & _KP_CHILD_HOUSES)
        sbl_child = bool(set(sbl_houses) & _KP_CHILD_HOUSES)
        # Tri-state result (architect-fix). UNKNOWN when data is
        # genuinely missing (NL/SBL absent or signified-houses lookup
        # empty) — these are data-quality gaps, NOT true KP negatives.
        # Unknown planets are treated as neutral (not hard-blocked) by
        # the final-gate composition layer, so degraded KP input can
        # never zero out promoter eligibility on its own.
        nl_known  = bool(nl)  and bool(nl_houses)
        sbl_known = bool(sbl) and bool(sbl_houses)
        # Strict-only negation: true ONLY when signified-houses set
        # is a non-empty subset of {1,4,10} (pure negation, no
        # mitigation from any other house). Phase 2.5.4-r3: this is
        # now a HARD BLOCK — if NL or SBL is purely in negation
        # houses, the planet cannot promise a child even if the
        # other lord signifies 2/5/11.
        def _neg_only(houses: List[int]) -> bool:
            s = set(houses)
            return bool(s) and s.issubset(_KP_NEGATION_HOUSES)
        nl_neg  = _neg_only(nl_houses)
        sbl_neg = _neg_only(sbl_houses)
        kp_negated = nl_neg or sbl_neg
        if not (nl_known and sbl_known):
            kp_status = "unknown"
            kp_promotes_child: Optional[bool] = None
        elif kp_negated:
            # Pure-negation planet — hard block regardless of any
            # 2/5/11 link on the OTHER lord.
            kp_status = "fail"
            kp_promotes_child = False
        elif nl_child and sbl_child:
            kp_status = "pass"
            kp_promotes_child = True
        else:
            kp_status = "fail"
            kp_promotes_child = False
        out["per_planet"][pname] = {
            "nl":                    nl,
            "sbl":                   sbl,
            "nl_houses":             nl_houses,
            "sbl_houses":            sbl_houses,
            "nl_signifies_child":    nl_child,
            "sbl_signifies_child":   sbl_child,
            "kp_promotes_child":     kp_promotes_child,
            "kp_status":             kp_status,
            "kp_negated":            kp_negated,
        }
        if kp_status == "pass":
            out["passed"].append(pname)
        elif kp_status == "fail":
            out["blocked"].append(pname)
        else:
            out["unknown"].append(pname)
    out["passed"].sort()
    out["blocked"].sort()
    out["unknown"].sort()
    return out


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
                              cross_map: Optional[Dict[str, Dict[str, Any]]]
                                  = None,
                              ) -> List[Dict[str, Any]]:
    """Score each upcoming dasha window.

    SIGN CONVENTION: For baby/conception, "flow" = child-promoter
    activation (more is more conception-favorable). Obstruction-bearer
    planets (6L/8L/12L, occupants of 6/8/12) lower the flow. Risk
    planets (Mars/Saturn in 8H, Ketu on 5H) raise risk_score
    separately.

    AD=5, PD=6, MD=1.

    NOTE — architect-pattern (mirrors travel v1 / finance v1):
    "functional malefic for lagna" tag is INTENTIONALLY EXCLUDED from
    obstruction classification. It is a Step-1 ranking modifier only.

    Phase 2.5.3 — Cross-Chart Gate: when `cross_map` is supplied
    (Step 3c result), a planet is admitted to `promoter_lords` only if
    it is `cross_confirmed` (5H credentials in ≥2 of D1/D9/D7).
    Otherwise its dasha contribution is NEUTRAL even if it carries
    promoter tags. This blocks "D1-only paper promise" planets from
    masquerading as true child-givers in their AD/PD. Obstructor /
    risk classifications are unaffected (they always apply).
    """
    if not chain or not ranked:
        return []
    score_map = {r["name"]: r["score"] for r in ranked}
    max_score = max(score_map.values()) or 1.0

    promoter_lords: Set[str] = set()
    obstructor_lords: Set[str] = set()
    risk_lords: Set[str] = set()
    _PROMOTER_TAGS = ("5L (PUTRASTHANA", "9L (dharma", "11L (gain",
                       "occupies 5H", "occupies 9H", "occupies 11H",
                       "PUTRA-KARAKA", "fertility/maternal karaka",
                       "reproductive-health karaka",
                       "procreative-vigor karaka",
                       "lineage-vitality karaka")
    _OBSTRUCTOR_TAGS = ("occupies 6H (OBSTRUCTION",
                         "occupies 8H (OBSTRUCTION",
                         "occupies 12H (OBSTRUCTION")
    for r in ranked:
        promoter_count = 0
        obstruct_count = 0
        for l in r["links"]:
            if any(t in l for t in _PROMOTER_TAGS):
                promoter_count += 1
            if any(t in l for t in _OBSTRUCTOR_TAGS):
                obstruct_count += 1
        # Cross-chart gate: only admit as PROMOTER when D1∩D9∩D7
        # cross-confirmation is satisfied (or cross_map not supplied).
        cross_ok = True
        if cross_map is not None:
            cross_ok = bool(cross_map.get(r["name"], {})
                              .get("cross_confirmed"))
        if promoter_count and obstruct_count:
            if promoter_count >= obstruct_count and cross_ok:
                promoter_lords.add(r["name"])
            else:
                obstructor_lords.add(r["name"])
        elif promoter_count and cross_ok:
            promoter_lords.add(r["name"])
        elif obstruct_count:
            obstructor_lords.add(r["name"])
        # Risk: Saturn/Mars in 8H = miscarriage risk; Ketu on 5H = loss
        if r["name"] in ("Saturn", "Mars"):
            for l in r["links"]:
                if "occupies 8H" in l or "occupies 12H" in l:
                    risk_lords.add(r["name"])
        if r["name"] == "Ketu":
            for l in r["links"]:
                if "occupies 5H" in l:
                    risk_lords.add("Ketu")

    horizon_end = now + timedelta(days=365 * horizon_years)
    windows: List[Dict[str, Any]] = []
    for w in chain:
        if w["end"] < now or w["start"] > horizon_end:
            continue
        promoter_score = 0.0
        obstruct_score = 0.0
        risk_score = 0.0
        triggers: List[str] = []
        for role, lord, weight in (("MD", w["md"], _DASHA_SCORE_MD),
                                    ("AD", w["ad"], _DASHA_SCORE_AD),
                                    ("PD", w["pd"], _DASHA_SCORE_PD)):
            if not (lord and lord in score_map):
                continue
            rel = score_map[lord] / max_score
            contrib = weight * rel
            if lord in promoter_lords:
                promoter_score += contrib
                triggers.append(f"{role}={lord}(CHILD_PROMOTER,+{contrib:.2f})")
            elif lord in obstructor_lords:
                obstruct_score += contrib
                triggers.append(f"{role}={lord}(OBSTRUCTOR,-{contrib:.2f})")
            else:
                triggers.append(f"{role}={lord}(NEUTRAL,0)")
            if lord in risk_lords:
                risk_score += contrib * 0.5
                triggers.append(f"  ↳ RISK_TAG:{lord}(+{contrib*0.5:.2f})")
        net = max(0.0, promoter_score - obstruct_score)
        if net <= 0 and promoter_score == 0 and risk_score == 0:
            continue
        # Heuristic kind: natural vs assisted vs delayed
        kind = "general"
        if w["ad"] == "Jupiter" or w["pd"] == "Jupiter":
            kind = "natural_grace"
        elif (w["ad"] in ("Saturn", "Rahu")
              or w["pd"] in ("Saturn", "Rahu")):
            kind = "assisted_or_delayed"
        # Phase 2.5.5 — ACTIVE-WINDOW MARKING (user-requested):
        # Beyond the weighted score, explicitly mark windows where
        # the FINAL-GATE-PASSED promoter planets (survived Step 3c
        # cross-chart ∩ Step 4c KP) become MD/AD/PD lord. This is
        # the simple, classical "kab promoter dasha aa rahi hai"
        # check the user wants surfaced cleanly, separate from the
        # weighted scoring noise. Priority hierarchy:
        #   PEAK    = AD AND PD both gate-passed promoters
        #   STRONG  = AD is a gate-passed promoter
        #   TRIGGER = PD is a gate-passed promoter (short pulse)
        #   BACKGROUND = only MD is a gate-passed promoter
        #   None    = no gate-passed promoter ruling this window
        ad_active = w["ad"] in promoter_lords
        pd_active = w["pd"] in promoter_lords
        md_active = w["md"] in promoter_lords
        if ad_active and pd_active:
            active_priority = "PEAK"
        elif ad_active:
            active_priority = "STRONG"
        elif pd_active:
            active_priority = "TRIGGER"
        elif md_active:
            active_priority = "BACKGROUND"
        else:
            active_priority = None
        active_lords_in_window = [
            f"{role}={lord}"
            for role, lord in (("MD", w["md"]),
                                ("AD", w["ad"]),
                                ("PD", w["pd"]))
            if lord in promoter_lords
        ]
        windows.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "start": w["start"], "end": w["end"],
            "score": round(net, 2),
            "promoter_raw": round(promoter_score, 2),
            "obstruct_raw": round(obstruct_score, 2),
            "risk_raw": round(risk_score, 2),
            "kind": kind,
            "triggers": triggers,
            "active_window":          active_priority is not None,
            "active_priority":        active_priority,
            "active_lords_in_window": active_lords_in_window,
        })
    windows.sort(key=lambda x: (-x["score"], x["start"]))
    return windows


# ════════════════════════════════════════════════════════════════════════
# STEP 6 — Transit triggers (baby lens)
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


def _planet_position_at(planet_id: int,
                          when: datetime) -> Optional[Dict[str, Any]]:
    """Phase 2.5.6 — EXACT transit position helper.

    Returns rich position dict for `planet_id` at `when` UT:
      { lon_deg, sign_idx, sign_name, deg_in_sign, deg_str,
        nak_idx, nak_name, pada, retrograde, speed_deg_per_day }

    Sidereal (Lahiri) longitude. Pure swisseph passthrough — no
    derived/interpretive fields, no future projections.
    """
    if not _HAS_SWE:
        return None
    try:
        jd = swe.julday(when.year, when.month, when.day,
                         when.hour + when.minute / 60.0)
        # FLG_SPEED gives us instantaneous angular velocity → retro detect
        flags = _SWE_FLAGS | swe.FLG_SPEED
        result = swe.calc_ut(jd, planet_id, flags)
        lon = float(result[0][0]) % 360.0
        speed = float(result[0][3])  # deg / day in longitude
        sign_idx = int(lon // 30) % 12
        deg_in_sign = lon - (sign_idx * 30.0)
        deg_int = int(deg_in_sign)
        deg_min = int(round((deg_in_sign - deg_int) * 60.0))
        if deg_min == 60:
            deg_min = 0
            deg_int += 1
        nak_idx = int(lon // _NAK_SPAN) % 27
        nak_offset = lon - (nak_idx * _NAK_SPAN)
        pada = int(nak_offset // _PADA_SPAN) + 1
        if pada > 4: pada = 4
        return {
            "lon_deg":             round(lon, 4),
            "sign_idx":            sign_idx,
            "sign_name":           _SIGNS[sign_idx],
            "deg_in_sign":         round(deg_in_sign, 4),
            "deg_str":             f"{deg_int:02d}°{deg_min:02d}′",
            "nak_idx":             nak_idx,
            "nak_name":            _NAK_NAMES[nak_idx],
            "pada":                pada,
            "retrograde":          speed < 0.0,
            "speed_deg_per_day":   round(speed, 4),
        }
    except Exception:
        return None


def _step6_transits(kundli: dict, lagna_si: int,
                     planets_d1: List[dict],
                     now: datetime) -> Dict[str, Any]:
    """Phase 2.5.7 — CLASSICAL DOUBLE TRANSIT (Jupiter + Saturn only).

    Per K.N. Rao's Double Transit Theory: for any event to fructify,
    BOTH Jupiter AND Saturn must transit either the relevant BHAVA
    (house) OR its LORD (sign). For child = 5H + 5L (PUTRASTHANA).

    Trigger taxonomy:
      DOUBLE_TRANSIT  → Jupiter AND Saturn each on 5H-sign OR 5L-sign
                        (strongest classical conception window)
      SINGLE_JUPITER  → Jupiter only on 5H-sign or 5L-sign
      SINGLE_SATURN   → Saturn only on 5H-sign or 5L-sign
      NONE            → neither

    Other transit bodies (Rahu/Mars/Sade Sati/Sun/Moon/Venus/Mercury)
    are deliberately EXCLUDED — user-requested narrowing to keep the
    transit layer aligned with one classical, validated rule rather
    than scattering noise across multiple unverified heuristics.
    """
    out = {"jupiter": None, "saturn": None,
           "double_transit": None,
           "active_triggers": [],
           "positions": {},
           "as_of_utc": now.isoformat()}
    if not _HAS_SWE:
        out["note"] = "swisseph unavailable; transit layer skipped"
        return out

    # Exact sidereal positions — Jupiter + Saturn only.
    pos_jup = _planet_position_at(swe.JUPITER, now)
    pos_sat = _planet_position_at(swe.SATURN,  now)

    def _enrich(pos):
        if not pos: return None
        h = _house_of_sign(pos["sign_idx"], lagna_si)
        return {**pos, "house_from_lagna": h}

    out["positions"] = {
        "Jupiter": _enrich(pos_jup),
        "Saturn":  _enrich(pos_sat),
    }

    jup_si = pos_jup["sign_idx"] if pos_jup else None
    sat_si = pos_sat["sign_idx"] if pos_sat else None

    # 5H sign (whole-sign from lagna) and 5L's natal sign.
    h5_sign  = (lagna_si + 4) % 12
    h5_lord  = _house_lord(lagna_si, 5)
    h5l_sign = _planet_sign_idx(planets_d1, h5_lord)

    def _on_5h_or_5l(si):
        if si is None:
            return None
        if si == h5_sign and h5l_sign is not None and si == h5l_sign:
            return "5H+5L (same sign)"
        if si == h5_sign:
            return "5H (PUTRASTHANA)"
        if h5l_sign is not None and si == h5l_sign:
            return f"5L sign ({h5_lord} natal sign)"
        return None

    jup_hit = _on_5h_or_5l(jup_si)
    sat_hit = _on_5h_or_5l(sat_si)

    if jup_hit:
        out["jupiter"] = (f"Jupiter transiting {jup_hit} — "
                           f"karaka activation of progeny axis")
    if sat_hit:
        out["saturn"] = (f"Saturn transiting {sat_hit} — "
                          f"maturation/timing of progeny axis")

    # Double Transit verdict + trigger emission
    if jup_hit and sat_hit:
        out["double_transit"] = {
            "active":          True,
            "rule":            "Jupiter+Saturn both on 5H or 5L",
            "jupiter_anchor":  jup_hit,
            "saturn_anchor":   sat_hit,
            "h5_sign":         _SIGNS[h5_sign],
            "h5_lord":         h5_lord,
            "h5_lord_sign":    (_SIGNS[h5l_sign]
                                  if h5l_sign is not None else None),
        }
        out["active_triggers"].append(
            ("DOUBLE_TRANSIT_5H_5L", 5, +1.5))
    elif jup_hit:
        out["double_transit"] = {"active": False,
                                   "partial": "JUPITER_ONLY"}
        out["active_triggers"].append(
            ("SINGLE_TRANSIT_JUPITER", 5, +0.6))
    elif sat_hit:
        out["double_transit"] = {"active": False,
                                   "partial": "SATURN_ONLY"}
        out["active_triggers"].append(
            ("SINGLE_TRANSIT_SATURN", 5, +0.4))
    else:
        out["double_transit"] = {"active": False, "partial": None}

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 7 — Ashtakavarga support (SAV bindus on 5H + 11H)
# ════════════════════════════════════════════════════════════════════════
def _step7_ashtakavarga(kundli: dict, lagna_si: int) -> Dict[str, Any]:
    out = {"sav_5": None, "sav_11": None, "santan_band": "UNKNOWN"}
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
        out["sav_5"] = sav[4]    # 5th house
        out["sav_11"] = sav[10]   # 11th house
    if (isinstance(out["sav_5"], (int, float))
            and isinstance(out["sav_11"], (int, float))):
        avg = (out["sav_5"] + out["sav_11"]) / 2.0
        if avg < _SAV_SANTAN_WEAK:
            out["santan_band"] = "WEAK"
        elif avg >= _SAV_SANTAN_STRONG:
            out["santan_band"] = "STRONG"
        else:
            out["santan_band"] = "MEDIUM"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 9 — Yoga + hard guards
# ════════════════════════════════════════════════════════════════════════
def _detect_yogas(kundli: dict, lagna_si: int,
                   planets: List[dict]) -> List[Dict[str, Any]]:
    """Detect classical baby/progeny-relevant yogas.

    POSITIVE:
      - Putra Yoga (5L+9L conjunction OR exchange OR mutual aspect)
      - Santan-Prapti Yoga (Jupiter aspects 5H or 5L)
      - Putra-Karaka-Bala (Jupiter exalted/own-sign)
    NEGATIVE:
      - Bandhya Yoga (5L in 6/8/12 + Jupiter in dusthana)
      - Putra-Dosha (5H surrounded by malefics, NO Jupiter aspect)
      - Miscarriage-Yoga (8L+5L conjunction)
      - Adoption-Indicated (5L in 12H + Rahu/Ketu on 5H — neutral
        severity — describes route, not obstruction)
    """
    out: List[Dict[str, Any]] = []

    h5_lord  = _house_lord(lagna_si, 5)
    h9_lord  = _house_lord(lagna_si, 9)
    h8_lord  = _house_lord(lagna_si, 8)

    # CRITICAL ETHICAL NOTE (architect-fix May 7 2026): yoga labels MUST
    # be gender-neutral. "Putra" literally means "son" in Sanskrit; using
    # it leaks gender vocabulary downstream even though the engine carries
    # NO_GENDER_PREDICTION directive. We use "Progeny" / "Child-Promise"
    # / "Child-Karaka" labels instead. "Santan" (offspring), "Bandhya"
    # (barren), "Miscarriage", "Adoption" are gender-neutral classical
    # terms and may be retained.
    # Progeny Yoga: 5L+9L conjunction / exchange / mutual aspect
    h5_h = _planet_house(planets, h5_lord)
    h9_h = _planet_house(planets, h9_lord)
    if h5_lord != h9_lord and h5_h and h9_h:
        if h5_h == 9 and h9_h == 5:
            out.append({"name": "Progeny Yoga (5L↔9L parivartana)",
                        "severity": "protective",
                        "planets": [h5_lord, h9_lord]})
        elif h5_h == h9_h:
            out.append({"name": "Progeny Yoga (5L+9L conjunction)",
                        "severity": "protective",
                        "planets": [h5_lord, h9_lord]})
        elif (_aspects_house(h5_lord, h5_h, h9_h)
              and _aspects_house(h9_lord, h9_h, h5_h)):
            out.append({"name": "Progeny Yoga (5L↔9L mutual aspect)",
                        "severity": "protective",
                        "planets": [h5_lord, h9_lord]})

    # Santan-Prapti Yoga: Jupiter aspects 5H or 5L
    jup_h = _planet_house(planets, "Jupiter")
    if jup_h:
        if jup_h == 5:
            out.append({"name": "Santan-Prapti Yoga (Jupiter in 5H)",
                        "severity": "protective",
                        "planets": ["Jupiter"]})
        elif _aspects_house("Jupiter", jup_h, 5):
            out.append({"name": "Santan-Prapti Yoga (Jupiter aspects 5H)",
                        "severity": "protective",
                        "planets": ["Jupiter"]})
        elif h5_h and _aspects_house("Jupiter", jup_h, h5_h):
            out.append({"name": "Santan-Prapti Yoga (Jupiter aspects 5L)",
                        "severity": "protective",
                        "planets": ["Jupiter", h5_lord]})

    # Child-Karaka-Bala: Jupiter exalted or own-sign
    jup_si = _planet_sign_idx(planets, "Jupiter")
    if jup_si is not None:
        if jup_si == _EXALT["Jupiter"]:
            out.append({"name": "Child-Karaka-Bala (Jupiter exalted)",
                        "severity": "protective",
                        "planets": ["Jupiter"]})
        elif jup_si in _OWN_SIGNS["Jupiter"]:
            out.append({"name": "Child-Karaka-Bala (Jupiter own-sign)",
                        "severity": "protective",
                        "planets": ["Jupiter"]})

    # Bandhya Yoga: 5L in 6/8/12 AND Jupiter in dusthana
    if h5_h in (6, 8, 12) and jup_h in (6, 8, 12):
        out.append({"name": "Bandhya Yoga (5L+Jupiter both in dusthana)",
                    "severity": "high",
                    "planets": [h5_lord, "Jupiter"]})

    # Progeny-Dosha: 5H surrounded by malefics with NO Jupiter aspect
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    occupants_5 = set(_planets_in_house(planets, 5))
    aspecting_5 = set()
    for pname in _PLANETS_9:
        ap_h = _planet_house(planets, pname)
        if ap_h and _aspects_house(pname, ap_h, 5):
            aspecting_5.add(pname)
    afflicting = (occupants_5 | aspecting_5) & malefics
    jup_protects = ("Jupiter" in occupants_5
                     or "Jupiter" in aspecting_5)
    if len(afflicting) >= 2 and not jup_protects:
        out.append({"name": "Progeny-Dosha (5H afflicted by malefics, no Jupiter rescue)",
                    "severity": "high",
                    "planets": list(afflicting)})

    # Miscarriage-Yoga: 8L+5L conjunction
    h8_h = _planet_house(planets, h8_lord)
    if h5_lord != h8_lord and h5_h and h8_h and h5_h == h8_h:
        out.append({"name": "Miscarriage-Yoga (5L+8L conjunction)",
                    "severity": "high",
                    "planets": [h5_lord, h8_lord]})

    # Adoption-Indicated (informational — neutral severity)
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")
    if h5_h == 12 and (rahu_h == 5 or ketu_h == 5):
        out.append({"name": "Adoption-Indicated Yoga (5L in 12H + Rahu/Ketu on 5H)",
                    "severity": "informational",
                    "planets": [h5_lord, "Rahu" if rahu_h == 5 else "Ketu"]})

    return out


def _detect_d7_yogas(d7_picture: Dict[str, Any]) -> List[Dict[str, Any]]:
    """D7-Saptamsha-specific yogas, derived from the Step 3b picture.

    Mirrors the gender-neutral labelling rule used in `_detect_yogas`.
    Emits:
      • "D7-Progeny-Yoga" (protective) when the D7 5L is well-placed in
        D7 (kendra/trine, non-debilitated, not in dusthana) AND either
        Jupiter aspects/occupies D7 5H or a benefic occupies it.
      • "D7-Bandhya" (high) when the D7 5L sits in D7 6/8/12 AND there
        is no Jupiter aspect/occupation of D7 5H (no rescue).
      • "D7-Lagna-Activation" (protective) when D7 1L aspects D7 5H
        (lagna lord lending strength to the children house).
    """
    out: List[Dict[str, Any]] = []
    if not d7_picture or not d7_picture.get("available"):
        return out
    flags = d7_picture.get("flags", {}) or {}
    fl  = d7_picture.get("first_lord")  or {}
    fih = d7_picture.get("fifth_lord")  or {}

    if (flags.get("d7_5l_well_placed")
        and (flags.get("jupiter_aspects_d7_5h")
              or flags.get("benefic_in_d7_5h"))):
        out.append({"name": "D7-Progeny-Yoga (D7 5L well-placed + benefic on D7 5H)",
                    "severity": "protective",
                    "planets": [fih.get("planet"), "Jupiter"]})

    if (flags.get("d7_5l_in_dusthana")
        and not flags.get("jupiter_aspects_d7_5h")):
        out.append({"name": "D7-Bandhya (D7 5L in D7 dusthana, no Jupiter rescue)",
                    "severity": "high",
                    "planets": [fih.get("planet")]})

    if flags.get("d7_1l_aspects_5h"):
        out.append({"name": "D7-Lagna-Activation (D7 1L aspects D7 5H — progeny strength)",
                    "severity": "protective",
                    "planets": [fl.get("planet")]})

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
    """Map child-promoter score + risk to a severity tier.
    Tiers (matches `baby` topic in remedy engine):
      celebratory : strong flow, low risk
      supportive  : moderate flow
      watchful    : weak flow OR mild risk
      consult     : high-risk fertility (Bandhya, miscarriage, etc.)
    """
    s = score + max(0.0, transit_load)
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
                     santan_band: str,
                     yogas: List[Dict[str, Any]],
                     transit_load: float,
                     child_promised: bool,
                     kp_layer: Optional[Dict[str, Any]] = None
                     ) -> Tuple[str, str]:
    """Combine top-window flow, ashtakavarga band, yogas, transits,
    child-promised flag and KP layer into a single verdict + band.

    Mirrors travel v1 architect-fix pattern, plus baby-specific
    safeguards (architect HIGH#5 — May 7 2026):
      - `child_promised=True` alone with low flow does NOT elevate
        verdict (houses promised ≠ timing promised; flow gate s>=3.5).
      - `has_high_neg` yoga doesn't hard-override; must coincide with
        low flow AND no protective rescue.
      - Progeny-Dosha / Bandhya / Miscarriage at moderate flow →
        OBSTRUCTED (not just DELAYED).
      - **NEW**: Bandhya/Miscarriage yoga + KP 5-CSL = OBSTRUCTED
        forces OBSTRUCTED REGARDLESS of flow. A natal medical-block
        signature combined with a KP confirmation should never surface
        as CHILD_PROMISED — flow merely indicates active dasha, not a
        clinical green light. This protects the user from medically
        unsafe framing.
    """
    band = santan_band if santan_band in {"WEAK", "MEDIUM", "STRONG"} else "MEDIUM"
    has_high_neg = any(y.get("severity") == "high" for y in yogas)
    has_protect = any(y.get("severity") == "protective" for y in yogas)

    s = top_window_score + max(0.0, transit_load)

    # Specific high-severity yoga
    obstructive_yoga = any(
        any(tag in (y.get("name") or "") for tag in
             ("Bandhya", "Progeny-Dosha", "Miscarriage"))
        and y.get("severity") == "high"
        for y in yogas
    )
    kp_5_obstructed = bool(kp_layer
                            and kp_layer.get("verdict_5") == "OBSTRUCTED")

    # NEW: clinical-block override — Bandhya/Miscarriage + KP_5_OBSTRUCTED
    # forces OBSTRUCTED regardless of dasha flow. A natal medical-block
    # signature with a KP confirmation should never surface as
    # CHILD_PROMISED. This is the safest framing for a fertility user.
    if obstructive_yoga and kp_5_obstructed:
        return "OBSTRUCTED", "WEAK"

    # OBSTRUCTED takes precedence when negative yogas + low flow
    if s < 2.0 and has_high_neg and not has_protect:
        return "OBSTRUCTED", "WEAK"

    if obstructive_yoga and s < 4.0:
        return "OBSTRUCTED", band

    # CHILD_PROMISED: strong flow OR (composite flag + minimum flow)
    if s >= 6.0 or (child_promised and s >= 3.5):
        verdict = "CHILD_PROMISED"
        if child_promised:
            band = "STRONG"
        return verdict, band

    if s >= 3.5:
        return "FAVORABLE", band

    # DELAYED: protective yoga but low flow
    if has_protect and s < 3.5:
        return "DELAYED", band

    if has_high_neg and not has_protect:
        return "DELAYED", band

    return "FAVORABLE", band if s >= 1.5 else "WEAK"


def _detect_child_promised(yogas: List[Dict[str, Any]],
                              kp_layer: Dict[str, Any],
                              santan_band: str,
                              ranked: List[Dict[str, Any]]) -> bool:
    """A composite flag — TRUE only when multiple progeny-indicators
    coincide: positive Putra/Santan yoga + KP 5-cusp signifies child
    houses + at least medium SAV santan band + Jupiter in top-3 ranked.
    """
    has_putra_yoga = any(
        any(tag in (y.get("name") or "") for tag in
             ("Progeny Yoga", "Santan-Prapti", "Child-Karaka-Bala"))
        and y.get("severity") == "protective"
        for y in yogas
    )
    kp_5_yes = kp_layer.get("verdict_5") == "CHILD_YES"
    sav_ok = santan_band in ("MEDIUM", "STRONG")
    top3_names = {r["name"] for r in ranked[:3]}
    jupiter_top = "Jupiter" in top3_names
    confirmations = sum([has_putra_yoga, kp_5_yes, sav_ok, jupiter_top])
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
def compute_baby_window(kundli: dict, intel: Optional[dict] = None,
                          kp: Optional[dict] = None,
                          birth: Optional[Any] = None) -> dict:
    """Run the full 9-step Baby (Childbirth) Timing Engine v1 pipeline.

    Single-exit wrapper that resets and populates the thread-local
    cache on every code path (mirror of travel v1).
    """
    clear_last_baby_result()
    result: Dict[str, Any]
    try:
        result = _compute_baby_window_impl(kundli, intel, kp, birth)
    except Exception as exc:  # noqa: BLE001
        result = {
            "verdict": "UNKNOWN", "band": "WEAK",
            "factors": [f"ENGINE_EXCEPTION {type(exc).__name__}: {str(exc)[:160]}"],
            "risk_flags": ["ENGINE_EXCEPTION"],
            "engine_version": "v1.0.0",
            "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER",
        }
    _store_last_result(result)
    return result


def _compute_baby_window_impl(kundli: dict,
                                intel: Optional[dict] = None,
                                kp: Optional[dict] = None,
                                birth: Optional[Any] = None) -> dict:
    if not isinstance(kundli, dict) or not kundli:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "factors": ["GATE kundli empty"],
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER"}
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
                "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER"}

    ok, reasons = _data_sufficiency(kundli, kp)
    factors: List[str] = []
    if reasons:
        factors.append(f"DATA_NOTES {reasons}")
    if not ok:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "risk_flags": reasons, "factors": factors,
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER"}

    now = datetime.utcnow()
    birth_dt = _parse_dob_dt(birth, kundli=kundli)
    age = _compute_age(birth_dt, now)
    factors.append(f"AGE user_age={age} lagna={_SIGNS[lagna_si]}")

    # ── STEP 1 ──
    d1_map = _step1_d1_filter(kundli, lagna_si)
    survivors = {p for p, info in d1_map.items() if info["in_filter"]}
    factors.append(f"STEP1 survivors={sorted(survivors)}")

    # ── STEP 2 ──
    # Build D9 chart once and reuse for both dignity (Step 2) and
    # cross-chart filter (Step 3c). Single source of truth.
    d9_chart = _build_d9_chart(kundli)
    d9_scores = _step2_d9_verify(kundli, survivors, d9_chart=d9_chart)
    factors.append(f"STEP2 D9_scores=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d9_scores.items()))

    # ── STEP 3 ──
    # Build D7 chart once and reuse for both the score (Step 3) and the
    # picture (Step 3b). Same chart guarantees the score and the picture
    # never disagree.
    d7_chart = _build_d7_chart(kundli, lagna_si)
    d7_scores = _step3_d7_progeny(kundli, survivors, lagna_si,
                                     d7_chart=d7_chart)
    factors.append(f"STEP3 D7_progeny=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d7_scores.items()))

    # ── STEP 3b — D7 picture (1L/5L positions, 1H/5H occupants, aspects) ──
    d7_picture = _step3b_d7_picture(d7_chart, lagna_si)
    if d7_picture.get("available"):
        fl = d7_picture["first_lord"]
        fih = d7_picture["fifth_lord"]
        factors.append(
            f"STEP3b D7_lagna={d7_picture['d7_lagna']} "
            f"1L={fl['planet']}@H{fl['house_in_d7']}/{fl['dignity']} "
            f"5L={fih['planet']}@H{fih['house_in_d7']}/{fih['dignity']} "
            f"5H_occ={d7_picture['fifth_house_occupants']} "
            f"5H_asp={d7_picture['aspects_to_fifth_house']}"
        )
    else:
        factors.append("STEP3b D7_picture=unavailable (D1-dignity fallback)")

    # ── STEP 3c — Cross-chart 5H confirmation (D1 ∩ D9 ∩ D7) ──
    cross_map = _step3c_cross_chart_filter(d1_map, kundli, lagna_si,
                                              d9_chart, d7_chart)
    cross_confirmed = sorted(p for p, c in cross_map.items()
                              if c.get("cross_confirmed"))
    # Availability-aware gate: if BOTH D9 and D7 are unavailable, the
    # ≥2/3 rule is unreachable from D1 alone, which would collapse all
    # promoter classifications. In that degraded-data case we disable
    # the gate (cross_map_for_gate=None) so Step 5 falls back to the
    # legacy D1-only promoter logic — partial data must not flip a
    # valid chart into "no windows". The cross_chart_filter block in
    # the result still reports the partial confirmations transparently.
    d9_available = bool((d9_chart or {}).get("planets"))
    d7_available = bool((d7_chart or {}).get("planets"))
    cross_map_for_gate: Optional[Dict[str, Dict[str, Any]]] = cross_map
    if not (d9_available or d7_available):
        cross_map_for_gate = None
        factors.append("STEP3c cross_chart_gate=DISABLED "
                        "(D9+D7 both unavailable — degraded data)")
    else:
        factors.append("STEP3c cross_confirmed=" + (",".join(
            f"{p}({len(cross_map[p]['confirmed_in'])}/3:{','.join(cross_map[p]['confirmed_in'])})"
            for p in cross_confirmed) or "<none>") +
            f" [D9={d9_available} D7={d7_available}]")

    # ── STEP 3.5 ──
    kp_layer = _step3_5_kp_layer(kp, lagna_si)
    factors.append(f"STEP3.5 KP csl_5={kp_layer['csl_5']}/{kp_layer['verdict_5']} "
                    f"csl_11={kp_layer['csl_11']}/{kp_layer['verdict_11']}")

    # ── STEP 4 ──
    ranked = _step4_rank(d1_map, d9_scores, d7_scores, kp, lagna_si)
    factors.append("STEP4 ranked=" +
                    ",".join(f"{r['name']}:{r['score']}" for r in ranked[:5]))

    # ── STEP 4c — KP 2-5-11 significator filter (final pre-dasha gate) ──
    # Classical Krishnamurti Paddhati childbirth rule: a planet only
    # promises a child in its AD/PD if BOTH its nakshatra-lord AND
    # sub-lord signify houses 2/5/11. We AND this with the Step 3c
    # cross-chart gate to build the FINAL promoter eligibility set
    # passed into Step 5.
    kp_filter = _step4c_kp_significator_filter(ranked, kp)
    if kp_filter["available"]:
        factors.append("STEP4c KP_2-5-11 passed=" +
                        (",".join(kp_filter["passed"]) or "<none>") +
                        " blocked=" +
                        (",".join(kp_filter["blocked"]) or "<none>") +
                        " unknown=" +
                        (",".join(kp_filter.get("unknown") or [])
                          or "<none>"))
    else:
        factors.append("STEP4c KP_2-5-11=DISABLED (KP data unavailable)")

    # Build the FINAL gate map combining Step 3c + Step 4c.
    # Each gate is independently safety-disabled when its data is
    # unavailable (Step 3c → cross_map_for_gate; Step 4c → kp_filter).
    # Final rule: promoter eligibility = (cross_confirmed if gate
    # active else True) AND (kp_promotes_child if KP gate active
    # else True). If BOTH gates are disabled we fall back to legacy
    # D1-only promoter logic by passing cross_map=None to Step 5.
    cross_active = cross_map_for_gate is not None
    kp_active    = kp_filter["available"]
    if cross_active or kp_active:
        final_gate_map: Dict[str, Dict[str, Any]] = {}
        for r in ranked:
            pname = r["name"]
            base = (cross_map.get(pname, {}) if cross_map else {})
            cross_pass = (bool(base.get("cross_confirmed"))
                           if cross_active else True)
            kp_info = kp_filter["per_planet"].get(pname, {})
            # Tri-state aware: pass=True / fail=False / unknown=True
            # (do not hard-block on missing per-planet KP data).
            if kp_active:
                kp_status = kp_info.get("kp_status", "unknown")
                kp_pass_raw = (kp_status != "fail")
            else:
                kp_status = "unknown"
                kp_pass_raw = True
            # Phase 2.5.4-r4 — STRONG-CROSS-CHART RESCUE:
            # If a planet is confirmed in ALL THREE charts (D1+D9+D7
            # all show a 5H credential — 5L of that chart / occupant
            # of 5H / aspecting 5H / Jupiter karaka), it is too
            # strong a child-significator to be vetoed by a KP fail.
            # Classical rule: KP is a TIMING refinement, not a
            # promise-killer when D1/D9/D7 are unanimously positive.
            # Override applies only when:
            #   - cross gate is active (we have D9/D7 to count),
            #   - KP gate is active and says "fail",
            #   - confirmations == 3 (full cross-chart unanimity).
            confirmations = int(base.get("confirmations", 0))
            kp_override_by_strength = (
                cross_active and kp_active
                and kp_status == "fail"
                and confirmations >= 3
            )
            kp_pass = kp_pass_raw or kp_override_by_strength
            final_pass = cross_pass and kp_pass
            final_gate_map[pname] = {
                **base,
                "cross_confirmed":          final_pass,
                "cross_pass":               cross_pass,
                "kp_pass":                  kp_pass,
                "kp_status":                kp_status,
                "kp_override_by_strength":  kp_override_by_strength,
            }
        gate_for_step5 = final_gate_map
    else:
        gate_for_step5 = None

    # ── STEP 5 ──
    chain = _flatten_dasha_chain(kundli)
    dasha_windows = _step5_dasha_activation(chain, ranked, lagna_si, now,
                                                cross_map=gate_for_step5)
    factors.append(f"STEP5 dasha_windows_in_horizon={len(dasha_windows)}")

    # ── STEP 6 ──
    planets_d1 = kundli.get("planets") or []
    transits = _step6_transits(kundli, lagna_si, planets_d1, now)
    transit_load = sum(w for _, _, w in transits.get("active_triggers", []))
    factors.append(f"STEP6 transit_load={transit_load:.2f}")

    # ── STEP 7 ──
    ashta = _step7_ashtakavarga(kundli, lagna_si)
    factors.append(f"STEP7 SAV_5={ashta['sav_5']} SAV_11={ashta['sav_11']} "
                    f"santan_band={ashta['santan_band']}")

    # ── STEP 9 ──
    yogas = _detect_yogas(kundli, lagna_si, planets_d1)
    # Merge in D7-specific yogas derived from the Step 3b picture. These
    # share the same severity vocabulary (protective/high/informational)
    # so all downstream consumers (verdict, child_promised, risk_flags,
    # remedies) handle them identically without special-casing.
    yogas.extend(_detect_d7_yogas(d7_picture))
    factors.append(f"STEP9 yogas={[y['name'] for y in yogas]}")

    # Child-promised composite flag
    child_promised = _detect_child_promised(yogas, kp_layer,
                                              ashta["santan_band"], ranked)
    factors.append(f"CHILD_PROMISED={child_promised}")

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
            "window": _format_window(w["start"], w["end"]),
            "start_iso": w["start"].isoformat(),
            "end_iso": w["end"].isoformat(),
            "triggers": w["triggers"],
        })

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
            "triggers": current["triggers"],
        }

    # Protection windows = upcoming where Jupiter / 5L / 9L rules
    h5_lord = _house_lord(lagna_si, 5)
    h9_lord = _house_lord(lagna_si, 9)
    benefics = {"Jupiter", h5_lord, h9_lord}
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
    verdict, band = _derive_verdict(top_score, ashta["santan_band"],
                                       yogas, transit_load, child_promised,
                                       kp_layer=kp_layer)
    severity_now = (current_window["severity"]
                     if current_window else "supportive")
    rec_tier = _recommendation_tier(severity_now, confirmations_severe, age)
    # Consistency rules: OBSTRUCTED forces consult tier
    if verdict == "OBSTRUCTED":
        rec_tier = "consult"

    # LLM directives — mandatory baby/fertility safeguards
    llm_directives = ["BABY_DISCLAIMER",
                       "NOT_MEDICAL_ADVICE",
                       "NO_GUARANTEED_CONCEPTION",
                       "NO_GUARANTEED_DATE",
                       "NO_GENDER_PREDICTION",   # PCPNDT Act + global ethics
                       f"SEVERITY_TIER:{rec_tier}"]
    if child_promised:
        llm_directives.append("CHILD_PROMISED_INDICATED")
    if confirmations_severe >= _CONFIRMATIONS_FOR_CONSULT:
        llm_directives.append("CONSULT_TIER")
    if verdict == "OBSTRUCTED":
        llm_directives.append("CONSULT_FERTILITY_SPECIALIST")
    if any("Miscarriage" in (y.get("name") or "")
            or "Bandhya" in (y.get("name") or "")
            for y in yogas):
        llm_directives.append("MEDICAL_PRECAUTION_RECOMMENDED")
    # Age guard for medical realism
    if age is not None:
        if age < 20:
            llm_directives.append("USER_TOO_YOUNG_FRAMING")
        elif age >= 45:
            llm_directives.append("ADVANCED_AGE_FERTILITY_CONTEXT")

    risk_flags: List[str] = []
    if ashta["santan_band"] == "WEAK":
        risk_flags.append("LOW_SAV_SANTAN_BAND")
    if any(y.get("severity") == "high" for y in yogas):
        risk_flags.append("NEGATIVE_PROGENY_YOGA")
    if any("Miscarriage" in (y.get("name") or "") for y in yogas):
        risk_flags.append("MISCARRIAGE_RISK_YOGA")
    if any("Bandhya" in (y.get("name") or "") for y in yogas):
        risk_flags.append("BANDHYA_YOGA")
    if any("Progeny-Dosha" in (y.get("name") or "") for y in yogas):
        risk_flags.append("PROGENY_DOSHA")
    if transit_load >= 1.5 and any("risk" in t[0]
                                     for t in transits.get("active_triggers", [])):
        risk_flags.append("HEAVY_RISK_TRANSIT")
    if kp_layer.get("verdict_5") == "OBSTRUCTED":
        risk_flags.append("KP_5CSL_DUSTHANA")

    breakdown = {
        r["name"]: {"d1": r["d1"], "d9": r["d9"], "d7": r["d7"],
                     "kp": r["kp"], "karaka": r["karaka"],
                     "total": r["score"]}
        for r in ranked
    }

    affected = _affected_areas(ranked)
    remedies = _compute_baby_remedies(ranked, affected, rec_tier)

    # Phase 2.5.5 — CHILD-ACTIVE WINDOWS (user-requested simple view):
    # Chronological list of upcoming dasha windows where a final-gate-
    # passed promoter planet is ruling at AD/PD/MD level. Distinct from
    # `next_3_windows` (which is score-sorted and may include non-active
    # high-score windows) — this list answers "kab filter-passed planet
    # dasha me aa raha hai" directly. Priority order: PEAK > STRONG >
    # TRIGGER > BACKGROUND. Capped at next 8 to keep result lean.
    _PRIORITY_RANK = {"PEAK": 0, "STRONG": 1, "TRIGGER": 2,
                       "BACKGROUND": 3}
    active_chrono = sorted(
        (w for w in dasha_windows if w.get("active_window")),
        key=lambda x: x["start"]
    )
    child_active_windows = [{
        "md": w["md"], "ad": w["ad"], "pd": w["pd"],
        "priority":              w["active_priority"],
        "active_lords":          w["active_lords_in_window"],
        "window":                _format_window(w["start"], w["end"]),
        "start_iso":             w["start"].isoformat(),
        "end_iso":               w["end"].isoformat(),
        "score":                 w["score"],
        "kind":                  w.get("kind", "general"),
        "risk_raw":              w.get("risk_raw", 0.0),
    } for w in active_chrono[:8]]
    next_child_window = child_active_windows[0] if child_active_windows else None
    factors.append(
        f"STEP5b active_windows_in_horizon={len(active_chrono)} "
        f"next_priority={next_child_window['priority'] if next_child_window else '<none>'}"
    )

    return {
        "verdict": verdict,
        "band": band,
        "child_promised": child_promised,
        "current_window": current_window,
        "next_3_windows": formatted_top3,
        "child_active_windows": child_active_windows,
        "next_child_window": next_child_window,
        "protection_windows": protection_windows,
        "affected_areas": affected,
        "recommendation_tier": rec_tier,
        "top_child_planets": ranked[:5],
        "weighted_breakdown": breakdown,
        "kp_layer": kp_layer,
        "d7_picture": d7_picture,
        "cross_chart_filter": {
            "confirmed_planets": cross_confirmed,
            "per_planet": cross_map,
            "rule": "≥2 of {D1,D9,D7} 5H-link required for CHILD_PROMOTER",
            "available_charts": {"D1": True,
                                  "D9": d9_available,
                                  "D7": d7_available},
            "gate_active": cross_map_for_gate is not None,
        },
        "kp_significator_filter": kp_filter,
        "transits": transits,
        "ashtakavarga": ashta,
        "yogas": yogas,
        "risk_flags": risk_flags,
        "factors": factors,
        "llm_directives": llm_directives,
        "remedies": remedies,
        "engine_version": "v1.0.0",
        "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER",
    }


# ════════════════════════════════════════════════════════════════════════
# Remedy delegation — baby topic
# ════════════════════════════════════════════════════════════════════════
def _compute_baby_remedies(ranked: Optional[List[Dict[str, Any]]],
                              affected_areas: Optional[List[str]],
                              recommendation_tier: Optional[str]
                              ) -> Dict[str, Any]:
    """Delegates to Remedy Engine v1.1 with topic="baby".

    If the remedy engine doesn't yet have a "baby" topic catalog,
    falls back to topic="health" with progeny-area tags so a sensible
    PRACTICAL row (e.g. "consult fertility specialist", "track
    ovulation") is still surfaced. Returns {} if remedy module
    missing entirely.
    """
    try:
        from remedy import get_remedies  # type: ignore
    except Exception:
        return {}
    try:
        out = get_remedies(
            topic    = "baby",
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
    # Graceful fallback — health topic with progeny-area context
    try:
        return get_remedies(
            topic    = "health",
            planets  = ranked or [],
            areas    = (affected_areas or []) + ["progeny_context"],
            severity = recommendation_tier or "watchful",
            user_facts    = None,
            duration_days = 21,
        )
    except Exception:
        return {}
