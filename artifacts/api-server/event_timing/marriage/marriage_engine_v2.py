"""
event_timing/marriage/marriage_engine_v2.py
============================================
COSMIC LENS MARRIAGE ENGINE v2 — clean rewrite.

Architecture: FILTER → VERIFY → ACTIVATE → TRIGGER (8-step pipeline,
locked by user spec May 6 2026).

  STEP 1   D1 marriage planet filtering        (FILTER)
  STEP 2   D9 verification                     (VERIFY)
  STEP 3   KP verification                     (VERIFY)
  STEP 4   Weighted ranking (D1·30 + D9·25 + KP·30 + karaka·15)
  STEP 5   Dasha activation (MD/AD/PD)         (ACTIVATE)
  STEP 5.5 Future activation cascade
  STEP 6   Double transit confirmation         (TRIGGER)
  STEP 7   Ashtakavarga support                (smooth vs delayed)
  STEP 8   Delay / obstacle engine

Replaces VIVAH-7 (2.8.52 → 2.10.1) entirely. Old engine permanently
removed per user direction.

Public function (preserves contract for openai_helper + locked_facts +
numerology consumers):
  compute_timing_window(kundli, intel, kp, birth) -> dict

Output dict (back-compat + new fields):
  {
    # Required for LLM block formatter (_M17_format_marriage_block):
    "verdict":             "PROMISED" | "DELAYED" | "DENIED" | "UNKNOWN",
    "band":                "WEAK" | "MEDIUM" | "STRONG",
    "top_3_windows":       [{"md", "ad", "pd", "score", "window",
                              "start_iso", "end_iso"}],
    "risk_flags":          [str],
    # Wider contract:
    "primary_window":      str | None,
    "backup_window":       str | None,
    "key_trigger":         str | None,
    "confluence_strength": "STRONG" | "MODERATE" | "WEAK" | None,
    "factors":             [str],
    # NEW (v2):
    "top_marriage_planets":   [{"name", "score", "d1", "d9", "kp",
                                "karaka", "links"}],
    "weighted_breakdown":     {planet: {d1, d9, kp, karaka, total}},
    "future_cascade_narrative": str | None,
  }
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# ── External helpers (no dependency on the old marriage_timing engine) ──
try:
    from divisional_charts import compute_d9  # type: ignore
except Exception:
    compute_d9 = None  # type: ignore

try:
    from ashtakavarga import compute_ashtakavarga  # type: ignore
except Exception:
    compute_ashtakavarga = None  # type: ignore

try:
    from dosh_engine import _manglik  # type: ignore
except Exception:
    _manglik = None  # type: ignore

try:
    from pratyantar import compute_pratyantar  # type: ignore
except Exception:
    compute_pratyantar = None  # type: ignore

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

# Sign lord by sign-idx (0..11)
_SIGN_LORDS = {0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
               5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
               9: "Saturn", 10: "Saturn", 11: "Jupiter"}

# Sign of own-rulership for each planet (for parivartana detection)
_OWN_SIGNS: Dict[str, Set[int]] = {
    "Sun":     {4},          # Leo
    "Moon":    {3},          # Cancer
    "Mars":    {0, 7},       # Aries, Scorpio
    "Mercury": {2, 5},       # Gemini, Virgo
    "Jupiter": {8, 11},      # Sagittarius, Pisces
    "Venus":   {1, 6},       # Taurus, Libra
    "Saturn":  {9, 10},      # Capricorn, Aquarius
}

# Exaltation / debilitation for D9 dignity check
_EXALT: Dict[str, int] = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
                          "Jupiter": 3, "Venus": 11, "Saturn": 6}
_DEBIL: Dict[str, int] = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
                          "Jupiter": 9, "Venus": 5, "Saturn": 0}

# Marriage core houses + obstacle houses (KP standard)
_MARRIAGE_HOUSES: List[int] = [2, 7, 11]
_OBSTACLE_HOUSES: List[int] = [1, 6, 8, 10, 12]

# Step 4 weighted-ranking weights (per user spec, locked)
_WEIGHT_D1 = 0.30
_WEIGHT_D9 = 0.25
_WEIGHT_KP = 0.30
_WEIGHT_KARAKA = 0.15

# Step 1 D1 acceptance threshold (planets below this are filtered out)
_D1_FILTER_MIN_SCORE = 15.0

# Step 5 Dasha activation scoring
_DASHA_SCORE_MD = 3
_DASHA_SCORE_AD = 4
_DASHA_SCORE_PD = 5  # PD is final trigger per spec

# Step 6 Double-transit boost
_DT_BOTH_BOOST = 2.0
_DT_ONE_BOOST = 0.75

# Window selection
_MIN_WINDOW_GAP_DAYS = 60   # ≈ 2 months between top-3 windows

# ── Age-band thresholds (Indian classical, indicative) ──────────────
# Male:   <24 EARLY | 24-30 ON_TIME | 31-35 LATE | 36+ VERY_LATE
# Female: <21 EARLY | 21-28 ON_TIME | 29-32 LATE | 33+ VERY_LATE
_AGE_BANDS_MALE   = [(24, "EARLY"), (31, "ON_TIME"), (36, "LATE"), (999, "VERY_LATE")]
_AGE_BANDS_FEMALE = [(21, "EARLY"), (29, "ON_TIME"), (33, "LATE"), (999, "VERY_LATE")]
_AGE_BANDS_NEUTRAL = [(23, "EARLY"), (30, "ON_TIME"), (35, "LATE"), (999, "VERY_LATE")]

# v2.4 — Practical-age floor (absolute lower bound below which engine
# WILL NOT recommend a near-term marriage window, even if dasha/transits
# perfectly align). This is the "akal" (sense) layer: a 17-year-old
# whose Mars-AD lights up next month is still studying — surfacing
# "shaadi 3 mahine mein" as primary window is a real-life bug. Below
# these floors, near-term windows get suppressed (pushed to backup
# bucket) and the LLM is told to lead with study/career framing.
# Indian legal minimum: 18 (F), 21 (M); we add a small practical
# buffer above legal so the engine doesn't sit exactly on the wire.
_MIN_PRACTICAL_AGE_FEMALE  = 19
_MIN_PRACTICAL_AGE_MALE    = 22
# Unknown gender → use the STRICTER of the two floors (safety-first).
# A 20-year-old male profile with missing gender field should NOT slip
# through with windows that would be blocked if gender were known.
_MIN_PRACTICAL_AGE_NEUTRAL = max(_MIN_PRACTICAL_AGE_FEMALE,
                                  _MIN_PRACTICAL_AGE_MALE)  # = 22

# Multi-format DOB parser. Real-world Indian DOB strings come in many
# shapes ("26 Nov 1992", "26-11-1992", "1992-11-26", "26/11/1992", etc).
# v2.3 only handled ISO YYYY-MM-DD which silently dropped most DOBs →
# user_age = None → entire age system dead. v2.4 fixes this.
_DOB_FORMATS = (
    "%Y-%m-%d",       # 1992-11-26
    "%Y/%m/%d",       # 1992/11/26
    "%d-%m-%Y",       # 26-11-1992
    "%d/%m/%Y",       # 26/11/1992
    "%d.%m.%Y",       # 26.11.1992
    "%d %b %Y",       # 26 Nov 1992
    "%d %B %Y",       # 26 November 1992
    "%d-%b-%Y",       # 26-Nov-1992
    "%d-%B-%Y",       # 26-November-1992
    "%b %d %Y",       # Nov 26 1992
    "%B %d %Y",       # November 26 1992
    "%b %d, %Y",      # Nov 26, 1992
    "%B %d, %Y",      # November 26, 1992
)

# When user is at/past marriageable age, boost windows that fall within
# next N days so engine surfaces near-term candidates first.
_RECENT_WINDOW_DAYS = 365
_RECENT_BOOST       = 3.0
_FUTURE_CASCADE_MAX_WINDOWS = 3
_FUTURE_SCAN_HORIZON_YEARS = 25

# Vimshottari standard
_VIMS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
               "Jupiter", "Saturn", "Mercury"]
_VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
              "Saturn", "Rahu", "Ketu"]


# ════════════════════════════════════════════════════════════════════════
# Low-level helpers
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


def _planet_nakshatra_lord(planets: List[dict], pname: str) -> Optional[str]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            return p.get("nakshatraRuler") or p.get("nakshatra_lord")
    return None


def _house_lord(lagna_si: int, house: int) -> str:
    """Lord of `house` counted from `lagna_si` (1-based house)."""
    sign_at_house = (lagna_si + house - 1) % 12
    return _SIGN_LORDS[sign_at_house]


def _compute_d9_seventh_lord(kundli: dict) -> Optional[str]:
    """Return D9 (Navamsa) 7th-lord planet name, or None if D9 unavailable.

    Classical rule: D9 7L is the supreme marriage karaka. Even if a planet
    has zero D1 marriage linkage, being D9-7L makes it indispensable for
    STEP 2 (D9 verify) and STEP 4 (weighted ranking). Used as karaka-floor
    in STEP 1 so the planet survives filtering.
    """
    if compute_d9 is None:
        return None
    planets = kundli.get("planets") or []
    if not planets:
        return None
    lagna_lon = (kundli.get("ascendantLon")
                 or kundli.get("ascendantLongitude")
                 or kundli.get("lagnaLon")
                 or kundli.get("ascendantDeg"))
    try:
        lagna_lon = float(lagna_lon) if lagna_lon is not None else None
    except (TypeError, ValueError):
        lagna_lon = None
    try:
        d9 = compute_d9(planets, lagna_lon=lagna_lon) or {}
    except Exception:
        return None
    d9_lagna = (d9.get("_lagna") or {}).get("sign_idx")
    if not isinstance(d9_lagna, int):
        return None
    d9_h7_si = (d9_lagna + 6) % 12
    return _SIGN_LORDS.get(d9_h7_si)


def _house_of_sign(sign_si: int, lagna_si: int) -> int:
    return ((sign_si - lagna_si) % 12) + 1


def _aspects_target(aspector: str, ap_si: int, target_si: int) -> bool:
    """Vedic aspects (drishti). Universal 7th + planet-specials.

    Mars: 4th, 7th, 8th
    Jupiter: 5th, 7th, 9th
    Saturn: 3rd, 7th, 10th
    Rahu/Ketu: same as Saturn (5/7/9 in some schools — using 3/7/10
    which is the most-used Krishnamurti convention)
    Others: 7th only
    """
    diff = (target_si - ap_si) % 12 + 1   # houses are 1..12
    if diff == 7:
        return True
    if aspector == "Mars" and diff in (4, 8):
        return True
    if aspector == "Jupiter" and diff in (5, 9):
        return True
    if aspector in ("Saturn", "Rahu", "Ketu") and diff in (3, 10):
        return True
    return False


def _kp_cusp(kp: dict, house: int) -> Optional[dict]:
    for c in (kp.get("cusps") or []):
        if isinstance(c, dict) and c.get("house") == house:
            return c
    return None


def _planet_signified_houses(kp: dict, planet: str) -> List[int]:
    """KP signification houses for a planet (from chart_data.kp.significations)."""
    sigs = (kp.get("significations") or {}).get(planet) or {}
    pl = sigs.get("pl") or []
    if isinstance(pl, list):
        return [int(h) for h in pl if isinstance(h, int)]
    return []


# ════════════════════════════════════════════════════════════════════════
# STEP 1 — D1 marriage planet filtering (FILTER)
# ════════════════════════════════════════════════════════════════════════
def _step1_d1_filter(kundli: dict, lagna_si: int) -> Dict[str, Dict[str, Any]]:
    """Identify ONLY planets with REAL D1 marriage linkage.

    Returns:
      {planet_name: {"d1": float 0-100, "links": [str], "in_filter": bool}}
    """
    planets = kundli.get("planets") or []
    if not planets:
        return {}

    seventh_lord = _house_lord(lagna_si, 7)
    second_lord = _house_lord(lagna_si, 2)
    eleventh_lord = _house_lord(lagna_si, 11)

    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)
    h7_si = (lagna_si + 6) % 12   # 7H sign index

    out: Dict[str, Dict[str, Any]] = {}
    for pname in _PLANETS_9:
        score = 0.0
        links: List[str] = []
        p_si = _planet_sign_idx(planets, pname)
        p_house = _planet_house(planets, pname)

        if p_si is None:
            out[pname] = {"d1": 0.0, "links": [], "in_filter": False}
            continue

        # 1. Planet sitting in 7H
        if p_house == 7:
            score += 30.0
            links.append("in 7H")

        # 2. Planet sitting in 2H or 11H (lighter)
        if p_house == 2:
            score += 12.0
            links.append("in 2H")
        if p_house == 11:
            score += 12.0
            links.append("in 11H")

        # 3. Planet aspects 7H
        if pname not in ("Rahu", "Ketu"):
            if _aspects_target(pname, p_si, h7_si):
                score += 25.0
                links.append("aspects 7H")
        else:
            if _aspects_target(pname, p_si, h7_si):
                score += 18.0
                links.append("aspects 7H")

        # 4. Planet conjunct 7L (same sign, different planet)
        if (seventh_lord_si is not None and pname != seventh_lord
                and p_si == seventh_lord_si):
            score += 25.0
            links.append(f"conjunct 7L({seventh_lord})")

        # 5. Planet aspects 7L
        if (seventh_lord_si is not None and pname != seventh_lord
                and p_si != seventh_lord_si
                and _aspects_target(pname, p_si, seventh_lord_si)):
            score += 20.0
            links.append(f"aspects 7L({seventh_lord})")

        # 6. Parivartana with 7L
        if (seventh_lord_si is not None and pname != seventh_lord
                and p_si in _OWN_SIGNS.get(seventh_lord, set())
                and seventh_lord_si in _OWN_SIGNS.get(pname, set())):
            score += 35.0
            links.append(f"parivartana with 7L({seventh_lord})")

        # 7. Nakshatra-lord linkage with 7L
        nl = _planet_nakshatra_lord(planets, pname)
        if nl and nl == seventh_lord:
            score += 18.0
            links.append(f"in nakshatra of 7L({seventh_lord})")
        if nl and nl == "Venus" and pname != "Venus":
            score += 8.0
            links.append("in nakshatra of Venus")

        # 8. IS the 7L itself
        if pname == seventh_lord:
            score += 25.0
            links.append("IS the 7L")

        # 9. IS Venus / Jupiter (natural marriage karakas — minimal floor)
        if pname == "Venus":
            score += 15.0
            links.append("Venus (kalatra-karaka)")
        if pname == "Jupiter":
            score += 10.0
            links.append("Jupiter (marriage-karaka for women)")

        # 10. IS 2L or 11L (kutumba / gain of relationship)
        if pname == second_lord and pname != seventh_lord:
            score += 10.0
            links.append(f"IS 2L (kutumba)")
        if pname == eleventh_lord and pname != seventh_lord:
            score += 10.0
            links.append(f"IS 11L (gain)")

        score = min(100.0, score)
        in_filter = (score >= _D1_FILTER_MIN_SCORE) or pname in {"Venus", "Jupiter", seventh_lord}
        out[pname] = {"d1": score, "links": links, "in_filter": in_filter}

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 2 — D9 verification (VERIFY)
# ════════════════════════════════════════════════════════════════════════
def _step2_d9_verify(kundli: dict, lagna_si: int,
                     filtered: Set[str]) -> Dict[str, Dict[str, Any]]:
    """Verify same filtered planets in D9 Navamsa.

    Returns:
      {planet_name: {"d9": float 0-100, "notes": [str], "vargottama": bool,
                     "double_confirmed": bool}}
    """
    planets = kundli.get("planets") or []
    out: Dict[str, Dict[str, Any]] = {p: {"d9": 0.0, "notes": [],
                                           "vargottama": False,
                                           "double_confirmed": False}
                                       for p in _PLANETS_9}

    if compute_d9 is None:
        return out

    # Lagna longitude — try multiple shapes
    lagna_lon = (kundli.get("ascendantLon")
                 or kundli.get("ascendantLongitude")
                 or kundli.get("lagnaLon")
                 or kundli.get("ascendantDeg"))
    try:
        lagna_lon = float(lagna_lon) if lagna_lon is not None else None
    except (TypeError, ValueError):
        lagna_lon = None

    try:
        d9 = compute_d9(planets, lagna_lon=lagna_lon) or {}
    except Exception:
        return out

    if not d9:
        return out

    # D9 lagna sign
    d9_lagna = (d9.get("_lagna") or {}).get("sign_idx")
    d9_h7_si = ((d9_lagna + 6) % 12) if isinstance(d9_lagna, int) else None
    d9_seventh_lord = _SIGN_LORDS.get(d9_h7_si) if d9_h7_si is not None else None

    for pname in _PLANETS_9:
        if pname not in filtered:
            continue
        info = d9.get(pname) or {}
        d9_si = info.get("sign_idx")
        if not isinstance(d9_si, int):
            continue
        score = 0.0
        notes: List[str] = []

        # Vargottama (D1 sign == D9 sign) — strongest D9 signal
        if info.get("vargottama"):
            score += 25.0
            notes.append("vargottama in D9")
            out[pname]["vargottama"] = True

        # D9 dignity
        if pname in _EXALT and d9_si == _EXALT[pname]:
            score += 20.0
            notes.append(f"exalted in D9 ({_SIGNS[d9_si]})")
        elif pname in _DEBIL and d9_si == _DEBIL[pname]:
            score -= 15.0
            notes.append(f"debilitated in D9 ({_SIGNS[d9_si]})")
        elif d9_si in _OWN_SIGNS.get(pname, set()):
            score += 15.0
            notes.append(f"in own sign in D9 ({_SIGNS[d9_si]})")

        # In D9's 7H
        if d9_h7_si is not None and d9_si == d9_h7_si:
            score += 22.0
            notes.append("in 7H of D9")

        # IS D9's 7L (planet rules D9 7H sign)
        # v2.2 — D9 7L is the SUPREME marriage karaka in Navamsa.
        # Bumped from +18 to +30 (parity with D1 7H occupancy) to reflect
        # classical weight: D9 IS the marriage varga, so its 7L outranks
        # most other D9 signals.
        if d9_seventh_lord and pname == d9_seventh_lord:
            score += 30.0
            notes.append(f"IS D9 7L ({d9_seventh_lord}) — supreme")

        # Conjunct another filtered marriage planet in D9
        for other in filtered:
            if other == pname:
                continue
            other_d9 = (d9.get(other) or {}).get("sign_idx")
            if other_d9 == d9_si:
                score += 8.0
                notes.append(f"conjunct {other} in D9")
                break

        # Aspects D9 7L (using D9 sign positions)
        if d9_seventh_lord and pname != d9_seventh_lord:
            other_d9 = (d9.get(d9_seventh_lord) or {}).get("sign_idx")
            if (isinstance(other_d9, int)
                    and pname not in ("Rahu", "Ketu")
                    and _aspects_target(pname, d9_si, other_d9)):
                score += 12.0
                notes.append(f"aspects D9 7L ({d9_seventh_lord})")

        score = max(0.0, min(100.0, score))
        out[pname]["d9"] = score
        out[pname]["notes"] = notes

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3 — KP verification (VERIFY)
# ════════════════════════════════════════════════════════════════════════
def _step3_kp_verify(kp: dict, filtered: Set[str],
                      d9_7l: Optional[str] = None) -> Dict[str, Any]:
    """Verify filtered planets via KP signification + 7CSL gate.

    v2.3 — D9 7L (supreme marriage karaka in Navamsa) gets boosted KP
    treatment: (1) +15 flat KP-floor bonus when it has any marriage
    signification at all, (2) extra +10 when it specifically signifies
    7H, (3) if the 7th-cusp sub-lord IS the D9 7L, csl_verdict is
    upgraded from PARTIAL/UNKNOWN to CONFIRMS — but DENIES is never
    overridden (hard-stop per v2.1 architect contract).

    Returns:
      {
        "per_planet": {planet: {"kp": float 0-100, "promise_h": [int],
                                  "deny_h": [int], "notes": [str]}},
        "csl_planet": str | None,
        "csl_verdict": "CONFIRMS" | "PARTIAL" | "DENIES" | "UNKNOWN",
        "csl_promise_h": [int],
        "csl_deny_h": [int],
        "csl_is_d9_7l": bool,
      }
    """
    per_planet: Dict[str, Dict[str, Any]] = {}
    if not isinstance(kp, dict) or not kp:
        for p in _PLANETS_9:
            per_planet[p] = {"kp": 0.0, "promise_h": [], "deny_h": [], "notes": []}
        return {"per_planet": per_planet, "csl_planet": None,
                "csl_verdict": "UNKNOWN", "csl_promise_h": [], "csl_deny_h": [],
                "csl_is_d9_7l": False}

    # Per-planet scoring
    for pname in _PLANETS_9:
        houses = set(_planet_signified_houses(kp, pname))
        promise = sorted(houses & set(_MARRIAGE_HOUSES))
        deny = sorted(houses & set(_OBSTACLE_HOUSES))

        score = 0.0
        notes: List[str] = []
        # Promise weights: 7H = strongest
        for h in promise:
            if h == 7: score += 35.0
            elif h == 2: score += 20.0
            elif h == 11: score += 22.0
            notes.append(f"signifies {h}H")
        # Deny weights: 6/8/12 strongest deniers (especially 8H)
        for h in deny:
            if h == 8: score -= 28.0
            elif h == 12: score -= 18.0
            elif h == 6: score -= 12.0
            elif h == 1: score -= 8.0
            elif h == 10: score -= 6.0
            notes.append(f"deny-house {h}H")

        # Floor at 0, ceiling at 100
        score = max(0.0, min(100.0, score + 30.0))   # +30 baseline so 0-deny ≈ 30, strong promise ≈ 90

        # v2.3 — D9 7L supreme treatment in KP layer.
        # (a) +15 flat bonus to any D9 7L (recognises classical supremacy
        #     even when its KP signification is modest).
        # (b) +10 extra when D9 7L specifically signifies 7H (the
        #     marriage house) — this is the strongest classical confluence.
        if d9_7l and pname == d9_7l:
            score = min(100.0, score + 15.0)
            notes.append("D9 7L (KP-supreme +15)")
            if 7 in promise:
                score = min(100.0, score + 10.0)
                notes.append("D9 7L signifies 7H (KP-confluence +10)")

        per_planet[pname] = {"kp": score, "promise_h": promise,
                              "deny_h": deny, "notes": notes}

    # 7th cusp sub-lord verdict
    cusp7 = _kp_cusp(kp, 7) or {}
    csl_planet = cusp7.get("sb")
    csl_verdict = "UNKNOWN"
    csl_promise = []
    csl_deny = []
    if csl_planet:
        csl_houses = set(_planet_signified_houses(kp, csl_planet))
        csl_promise = sorted(csl_houses & set(_MARRIAGE_HOUSES))
        csl_deny = sorted(csl_houses & set(_OBSTACLE_HOUSES))
        # Verdict logic (Krishnamurti standard):
        if csl_promise and not csl_deny:
            csl_verdict = "CONFIRMS"
        elif csl_promise and csl_deny:
            csl_verdict = "PARTIAL"
        elif csl_deny and not csl_promise:
            csl_verdict = "DENIES"
        else:
            csl_verdict = "UNKNOWN"

    # v2.3 — Ultimate classical confluence: if 7th-cusp sub-lord IS the
    # D9 7L, the marriage promise is doubly confirmed (Krishnamurti's
    # CSL gate AND Parashari D9-7L supremacy point to the same planet).
    # Upgrade PARTIAL/UNKNOWN → CONFIRMS. DENIES is NEVER overridden
    # (architect-locked hard-stop from v2.1).
    csl_is_d9_7l = bool(d9_7l and csl_planet and csl_planet == d9_7l)
    if csl_is_d9_7l and csl_verdict in ("PARTIAL", "UNKNOWN"):
        csl_verdict = "CONFIRMS"

    return {
        "per_planet": per_planet,
        "csl_planet": csl_planet,
        "csl_verdict": csl_verdict,
        "csl_promise_h": csl_promise,
        "csl_deny_h": csl_deny,
        "csl_is_d9_7l": csl_is_d9_7l,
    }


# ════════════════════════════════════════════════════════════════════════
# STEP 4 — Weighted ranking (D1·30 + D9·25 + KP·30 + karaka·15)
# ════════════════════════════════════════════════════════════════════════
def _karaka_score(pname: str, lagna_si: int, is_female: Optional[bool],
                   d9_7l: Optional[str] = None) -> float:
    """Natural marriage-karaka contribution (0-100).

    v2.2 — D9 7L gets parity with D1 7L (90), or stays at its higher
    natural-karaka tier if it's also Venus/Jupiter (max wins). This
    ensures D9 7L always carries strong karaka weight in STEP 4
    weighted ranking even when its D1 marriage links are weak.
    """
    seventh_lord = _house_lord(lagna_si, 7)
    base = 15.0
    if pname == "Venus":
        base = 100.0
    elif pname == "Jupiter":
        # Higher for women (stree-karaka), still strong for men
        base = 95.0 if is_female else 75.0
    elif pname == seventh_lord:
        base = 90.0
    elif pname == _house_lord(lagna_si, 2):
        base = 50.0
    elif pname == _house_lord(lagna_si, 11):
        base = 50.0
    elif pname == "Mars":
        base = 40.0   # passion / initiation
    elif pname == "Moon":
        base = 35.0   # mind / emotional bond
    elif pname in ("Mercury", "Sun"):
        base = 25.0
    # D9 7L floor — supreme marriage significator in Navamsa.
    if d9_7l and pname == d9_7l:
        base = max(base, 90.0)
    return base


def _step4_rank(d1_map: Dict[str, Dict[str, Any]],
                d9_map: Dict[str, Dict[str, Any]],
                kp_map: Dict[str, Dict[str, Any]],
                lagna_si: int,
                is_female: Optional[bool],
                d9_7l: Optional[str] = None) -> List[Dict[str, Any]]:
    """Combine 4 dimensions into final weighted score, return top-5."""
    ranked: List[Dict[str, Any]] = []
    for pname in _PLANETS_9:
        d1 = float((d1_map.get(pname) or {}).get("d1", 0.0))
        d9 = float((d9_map.get(pname) or {}).get("d9", 0.0))
        kp = float((kp_map.get(pname) or {}).get("kp", 0.0))
        kk = _karaka_score(pname, lagna_si, is_female, d9_7l=d9_7l)

        total = (_WEIGHT_D1 * d1
                 + _WEIGHT_D9 * d9
                 + _WEIGHT_KP * kp
                 + _WEIGHT_KARAKA * kk)

        # Double-confirmation bonus: D1 and D9 BOTH support
        if d1 >= 25.0 and d9 >= 25.0:
            total += 5.0
            (d9_map.get(pname) or {})["double_confirmed"] = True

        ranked.append({
            "name": pname,
            "score": round(total, 2),
            "d1": round(d1, 1),
            "d9": round(d9, 1),
            "kp": round(kp, 1),
            "karaka": round(kk, 1),
            "links": (d1_map.get(pname) or {}).get("links", []),
        })

    ranked.sort(key=lambda x: -x["score"])
    return ranked[:5]


# ════════════════════════════════════════════════════════════════════════
# STEP 5 / 5.5 — Dasha activation + future cascade (ACTIVATE)
# ════════════════════════════════════════════════════════════════════════
def _parse_iso(s: Any) -> Optional[datetime]:
    if isinstance(s, datetime):
        return s
    if not isinstance(s, str):
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:len(fmt) if fmt != "%Y-%m-%dT%H:%M:%S" else 19], fmt)
        except Exception:
            continue
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:
        return None


def _flatten_dasha_chain(kundli: dict) -> List[Dict[str, Any]]:
    """Return flat list of {md, ad, pd, start, end} chunks ordered by start."""
    out: List[Dict[str, Any]] = []
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * _FUTURE_SCAN_HORIZON_YEARS)

    dashas = kundli.get("dashas") or []
    if isinstance(dashas, list) and dashas:
        for md in dashas:
            if not isinstance(md, dict):
                continue
            md_lord = md.get("planet") or md.get("md_lord") or md.get("maha")
            if not md_lord:
                continue
            for ad in (md.get("subDashas") or md.get("antar_dashas") or []):
                if not isinstance(ad, dict):
                    continue
                ad_lord = ad.get("planet") or ad.get("ad_lord") or ad.get("antar")
                ad_start = _parse_iso(ad.get("startDate") or ad.get("start"))
                ad_end = _parse_iso(ad.get("endDate") or ad.get("end"))
                if not (ad_lord and ad_start and ad_end):
                    continue
                if ad_end < today - timedelta(days=30) or ad_start > horizon:
                    continue
                # Build PDs inside AD
                pd_list = ad.get("subDashas") or ad.get("pratyantar_dashas") or []
                if pd_list and isinstance(pd_list, list):
                    for pd in pd_list:
                        pd_lord = (pd.get("planet") or pd.get("pd_lord")
                                   or pd.get("pratyantar"))
                        pd_start = _parse_iso(pd.get("startDate") or pd.get("start"))
                        pd_end = _parse_iso(pd.get("endDate") or pd.get("end"))
                        if not (pd_lord and pd_start and pd_end):
                            continue
                        if pd_end < today - timedelta(days=30):
                            continue
                        out.append({"md": md_lord, "ad": ad_lord, "pd": pd_lord,
                                     "start": pd_start, "end": pd_end})
                else:
                    # No PD list — synthesize from AD using standard Vimshottari
                    ad_secs = (ad_end - ad_start).total_seconds()
                    if ad_secs <= 0 or ad_lord not in _VIMS_ORDER:
                        continue
                    total = sum(_VIMS_YEARS.values())
                    start_idx = _VIMS_ORDER.index(ad_lord)
                    cursor = ad_start
                    for k in range(9):
                        pd_lord = _VIMS_ORDER[(start_idx + k) % 9]
                        frac = _VIMS_YEARS[pd_lord] / total
                        pd_end = cursor + timedelta(seconds=ad_secs * frac)
                        if pd_end >= today - timedelta(days=30):
                            out.append({"md": md_lord, "ad": ad_lord,
                                         "pd": pd_lord, "start": cursor,
                                         "end": pd_end})
                        cursor = pd_end

    out.sort(key=lambda c: c["start"])
    return out


def _step5_dasha_activation(chain: List[Dict[str, Any]],
                             target_lords: Set[str],
                             now: datetime,
                             d9_7l: Optional[str] = None) -> Dict[str, Any]:
    """Find current MD-AD-PD; check overlap with target_lords.

    v2.2 — When the active MD/AD/PD is the D9 7L (supreme marriage
    significator), add a +2 bonus to active_score so its dasha
    correctly elevates verdict tier (PROMISED→STRONG) without needing
    other coincident triggers.
    """
    current = None
    for c in chain:
        if c["start"] <= now < c["end"]:
            current = c
            break
    if not current:
        return {"current": None, "active_score": 0, "active_lords": []}

    active_lords = []
    score = 0
    if current["md"] in target_lords:
        score += _DASHA_SCORE_MD
        active_lords.append(f"{current['md']} (MD)")
    if current["ad"] in target_lords:
        score += _DASHA_SCORE_AD
        active_lords.append(f"{current['ad']} (AD)")
    if current["pd"] in target_lords:
        score += _DASHA_SCORE_PD
        active_lords.append(f"{current['pd']} (PD)")
    # D9 7L dasha bonus — supreme significator amplifies activation.
    if d9_7l and d9_7l in {current["md"], current["ad"], current["pd"]}:
        score += 2
        active_lords.append(f"{d9_7l} (D9 7L bonus)")
    return {"current": current, "active_score": score,
            "active_lords": active_lords}


def _step5_5_future_cascade(chain: List[Dict[str, Any]],
                              target_lords: Set[str],
                              now: datetime,
                              current: Optional[Dict[str, Any]]
                              ) -> List[Dict[str, Any]]:
    """Cascade scan per spec:
      Priority 1: remaining PDs in current AD
      Priority 2: remaining ADs in current MD
      Priority 3: next MD's chunks
    Returns scored future windows (PD-aware) sorted by score desc.
    """
    candidates: List[Dict[str, Any]] = []
    if not chain:
        return candidates

    # Determine current MD/AD context for priority labelling
    cur_md = current["md"] if current else None
    cur_ad = current["ad"] if current else None
    cur_md_seen = False
    cur_ad_seen = False

    for c in chain:
        if c["end"] <= now:
            continue   # past
        # Score: each lord present in target adds weight
        s = 0
        triple = 0
        if c["md"] in target_lords:
            s += _DASHA_SCORE_MD; triple += 1
        if c["ad"] in target_lords:
            s += _DASHA_SCORE_AD; triple += 1
        if c["pd"] in target_lords:
            s += _DASHA_SCORE_PD; triple += 1
        if s == 0:
            continue   # no marriage planet active in this chunk

        # Priority tag
        if cur_md and c["md"] == cur_md and cur_ad and c["ad"] == cur_ad:
            priority = 1
            cur_ad_seen = True
        elif cur_md and c["md"] == cur_md:
            priority = 2
            cur_md_seen = True
        else:
            priority = 3

        candidates.append({**c, "score": float(s), "triple": triple,
                            "priority": priority})

    candidates.sort(key=lambda x: (x["priority"], -x["score"], x["start"]))
    return candidates


# ════════════════════════════════════════════════════════════════════════
# STEP 6 — Double Transit confirmation (TRIGGER)
# ════════════════════════════════════════════════════════════════════════
def _planet_sign_at(planet_id: int, when: datetime) -> Optional[int]:
    if not _HAS_SWE:
        return None
    try:
        jd = swe.julday(when.year, when.month, when.day,
                        when.hour + when.minute / 60.0)
        pos, _ = swe.calc_ut(jd, planet_id, _SWE_FLAGS)
        lon = float(pos[0]) % 360.0
        return int(lon / 30.0) % 12
    except Exception:
        return None


def _step6_double_transit(window: Dict[str, Any],
                           h7_si: int,
                           seventh_lord_si: Optional[int],
                           top_planet_signs: Set[int]) -> Dict[str, Any]:
    """Sample window midpoint; check Jupiter+Saturn against marriage targets."""
    if not _HAS_SWE:
        return {"jup_hit": False, "sat_hit": False, "dt": False, "boost": 0.0,
                "detail": "swisseph unavailable"}
    mid = window["start"] + (window["end"] - window["start"]) / 2
    jup_si = _planet_sign_at(swe.JUPITER, mid)
    sat_si = _planet_sign_at(swe.SATURN, mid)

    targets = {h7_si}
    if seventh_lord_si is not None:
        targets.add(seventh_lord_si)
    targets |= top_planet_signs

    # Jupiter on target sign OR aspects target sign (5/7/9)
    jup_hit = False
    if jup_si is not None:
        if jup_si in targets:
            jup_hit = True
        else:
            for t in targets:
                if _aspects_target("Jupiter", jup_si, t):
                    jup_hit = True
                    break

    # Saturn on target sign OR aspects (3/7/10)
    sat_hit = False
    if sat_si is not None:
        if sat_si in targets:
            sat_hit = True
        else:
            for t in targets:
                if _aspects_target("Saturn", sat_si, t):
                    sat_hit = True
                    break

    boost = 0.0
    if jup_hit and sat_hit:
        boost = _DT_BOTH_BOOST
    elif jup_hit or sat_hit:
        boost = _DT_ONE_BOOST

    detail_parts = []
    if jup_hit and jup_si is not None:
        detail_parts.append(f"Jup→{_SIGNS[jup_si]}")
    if sat_hit and sat_si is not None:
        detail_parts.append(f"Sat→{_SIGNS[sat_si]}")
    return {"jup_hit": jup_hit, "sat_hit": sat_hit, "dt": jup_hit and sat_hit,
            "boost": boost, "detail": " + ".join(detail_parts) or "no transit hit"}


# ════════════════════════════════════════════════════════════════════════
# STEP 7 — Ashtakavarga support (smooth vs delayed)
# ════════════════════════════════════════════════════════════════════════
def _step7_ashtakavarga(window: Dict[str, Any],
                          av: Dict[str, Any],
                          h7_si: int,
                          lagna_si: int) -> Tuple[float, str]:
    """Returns (score_adjustment, label)."""
    if not av or "sav" not in av:
        return 0.0, ""
    sav = av["sav"]
    h7_sav = sav[6]   # 7th house bindus
    if h7_sav >= 30:
        return 0.5, f"7H SAV={h7_sav} (smooth marriage support)"
    if h7_sav >= 25:
        return 0.0, f"7H SAV={h7_sav} (average)"
    return -0.5, f"7H SAV={h7_sav} (delayed/stress signal)"


# ════════════════════════════════════════════════════════════════════════
# STEP 8 — Delay / obstacle engine
# ════════════════════════════════════════════════════════════════════════
def _step8_obstacles(kundli: dict, lagna_si: int, kp: dict,
                      kp_csl_verdict: str) -> List[str]:
    """Return list of human-readable risk flags."""
    flags: List[str] = []
    planets = kundli.get("planets") or []
    h7_si = (lagna_si + 6) % 12
    seventh_lord = _house_lord(lagna_si, 7)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)
    sat_si = _planet_sign_idx(planets, "Saturn")
    rahu_si = _planet_sign_idx(planets, "Rahu")
    venus_si = _planet_sign_idx(planets, "Venus")

    # Saturn affliction: Saturn conjunct/aspects 7H or 7L
    if sat_si is not None:
        if sat_si == h7_si:
            flags.append("Saturn in 7H (delay-pattern)")
        elif _aspects_target("Saturn", sat_si, h7_si):
            flags.append("Saturn aspects 7H (delay/maturity-required)")
        if seventh_lord_si is not None and sat_si == seventh_lord_si:
            flags.append(f"Saturn conjunct 7L ({seventh_lord}) — delay")

    # Rahu/Ketu on relationship axis (1-7)
    if rahu_si is not None:
        rahu_house = _house_of_sign(rahu_si, lagna_si)
        if rahu_house in (1, 7):
            flags.append(f"Rahu in {rahu_house}H (1-7 axis — unconventional choice / sudden shifts)")

    # Venus combust / debilitated
    if venus_si is not None:
        if venus_si == _DEBIL.get("Venus"):
            flags.append("Venus debilitated (relationship-dignity weak)")
        sun_si = _planet_sign_idx(planets, "Sun")
        if sun_si is not None and venus_si == sun_si:
            # rough combust check (same sign as Sun)
            flags.append("Venus close to Sun (combust risk)")

    # 6/8/12 lords on 7H or vice versa
    sixth_l = _house_lord(lagna_si, 6)
    eighth_l = _house_lord(lagna_si, 8)
    twelfth_l = _house_lord(lagna_si, 12)
    for nm, h in ((sixth_l, 6), (eighth_l, 8), (twelfth_l, 12)):
        l_si = _planet_sign_idx(planets, nm)
        if l_si is not None and l_si == h7_si:
            flags.append(f"{h}L ({nm}) on 7H (obstacle-house involvement)")

    # KP CSL DENIES → strongest delay signal
    if kp_csl_verdict == "DENIES":
        flags.append("7th cusp sub-lord DENIES marriage promise (KP)")
    elif kp_csl_verdict == "PARTIAL":
        flags.append("7th cusp sub-lord PARTIAL (KP — possible with effort)")

    # Manglik
    if _manglik is not None:
        try:
            mres = _manglik(planets)
            mstatus = mres[0] if isinstance(mres, tuple) and mres else mres
            if isinstance(mstatus, str) and mstatus.lower() in ("active", "mild"):
                flags.append(f"Manglik {mstatus} (compatibility care needed)")
        except Exception:
            pass

    return flags


# ════════════════════════════════════════════════════════════════════════
# Window assembly + min-gap filter
# ════════════════════════════════════════════════════════════════════════
def _format_window(start: datetime, end: datetime) -> str:
    """Human-readable window: 'January – June 2030'."""
    if start.year == end.year:
        if start.month == end.month:
            return f"{start.strftime('%B %Y')}"
        return f"{start.strftime('%B')} – {end.strftime('%B %Y')}"
    return f"{start.strftime('%B %Y')} – {end.strftime('%B %Y')}"


def _gap_ok(cand: Dict[str, Any], chosen: List[Dict[str, Any]]) -> bool:
    """True iff cand is ≥ _MIN_WINDOW_GAP_DAYS away from each already-chosen."""
    cs, ce = cand["start"], cand["end"]
    for w in chosen:
        ws, we = w["start"], w["end"]
        if cs >= we:
            gap = (cs - we).days
        elif ws >= ce:
            gap = (ws - ce).days
        else:
            return False
        if gap < _MIN_WINDOW_GAP_DAYS:
            return False
    return True


def _select_top_3(scored: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Greedy top-3 with min-gap + AD-diversity preference."""
    if not scored:
        return []
    chosen = [scored[0]]
    used_ads = {scored[0].get("ad")}
    for cand in scored[1:]:
        if len(chosen) >= 3:
            break
        if not _gap_ok(cand, chosen):
            continue
        # Prefer different AD when possible (architect diversity rule)
        if cand.get("ad") in used_ads:
            # Look ahead — is there a same-quality different-AD cand?
            alt = next((c for c in scored
                        if c not in chosen
                        and c.get("ad") not in used_ads
                        and _gap_ok(c, chosen)
                        and (cand["score"] - c["score"]) <= 1.5), None)
            if alt is not None:
                cand = alt
        chosen.append(cand)
        used_ads.add(cand.get("ad"))
    chosen.sort(key=lambda x: x["start"])
    return chosen


# ════════════════════════════════════════════════════════════════════════
# Verdict + band derivation
# ════════════════════════════════════════════════════════════════════════
def _derive_verdict(top_score: float, kp_csl: str,
                     risk_flags: List[str]) -> Tuple[str, str]:
    """Return (verdict, band).

    KP CSL DENIES is HARD-STOP per Krishnamurti doctrine — 7th cusp sub-
    lord is the final authority on whether marriage is promised at all.
    Even strong dasha/transit confluence cannot override CSL denial; at
    most it can elevate DENIED→DELAYED (event possible but only with
    enormous remedial effort).
    """
    # ── KP-CSL hard gate (architect-fixed May 6 2026) ──
    if kp_csl == "DENIES":
        # Final authority denies. Strongest dasha confluence can only
        # soften DENIED to DELAYED, NEVER to PROMISED.
        if top_score >= 10.0:
            return "DELAYED", "WEAK"   # massive effort needed; not promised
        return "DENIED", "WEAK"

    # Standard ladder (CSL is CONFIRMS / PARTIAL / UNKNOWN)
    if top_score >= 10.0:
        verdict, band = "PROMISED", "STRONG"
    elif top_score >= 6.0:
        verdict, band = "PROMISED", "MEDIUM"
    elif top_score >= 3.0:
        verdict, band = "DELAYED", "WEAK"
    else:
        verdict, band = "UNKNOWN", "WEAK"

    # KP PARTIAL caps STRONG band (mixed CSL signals → never claim STRONG)
    if kp_csl == "PARTIAL" and band == "STRONG":
        band = "MEDIUM"
    # Saturn-affliction or KP PARTIAL nudges PROMISED-MEDIUM → DELAYED
    if verdict == "PROMISED" and band == "MEDIUM":
        if any("Saturn" in f for f in risk_flags) or kp_csl == "PARTIAL":
            verdict = "DELAYED"
    return verdict, band


def _data_sufficiency_check(kundli: dict, kp: dict) -> Tuple[bool, List[str]]:
    """Gate: refuse to verdict on insufficient data (architect-flagged).

    Returns (ok, reasons). When ok=False, caller returns UNKNOWN verdict
    with the reasons surfaced as risk_flags so the LLM never claims
    confidence on a malformed/incomplete chart.
    """
    reasons: List[str] = []
    planets = (kundli or {}).get("planets") or []
    if not isinstance(planets, list) or len(planets) < 7:
        reasons.append(
            f"insufficient planetary data ({len(planets)} planets, need 7+)")
    dashas = (kundli or {}).get("dashas") or []
    cur = (kundli or {}).get("currentDasha") or {}
    if not (isinstance(dashas, list) and dashas) and not cur:
        reasons.append("dasha chain unavailable")
    if not isinstance(kp, dict) or not (kp.get("cusps") and kp.get("significations")):
        reasons.append("KP chart unavailable (cusps or significations missing)")
    return (len(reasons) == 0, reasons)


def _parse_dob_string(s: Any) -> Optional[datetime]:
    """v2.4 — Robust DOB string parser. Handles Indian formats like
    '26 Nov 1992', '26-11-1992', plus ISO and US variants. Returns
    None if no format matches. Tries all _DOB_FORMATS in order.
    """
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    for fmt in _DOB_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Last-ditch: ISO with time/timezone — try first 10 chars
    if len(s) >= 10:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d")
        except ValueError:
            pass
    return None


def _extract_dob_dt(birth: Any, kundli: Any = None) -> Optional[datetime]:
    """v2.4 — Extract a parsed datetime from birth dict OR kundli dict.
    Tries every common field name and every supported string format.
    Falls back to year/month/day numeric fields. Returns None if
    nothing usable.
    """
    sources = []
    if isinstance(birth, dict):
        sources.append(birth)
    if isinstance(kundli, dict):
        sources.append(kundli)
        # Some payloads nest birth metadata under 'birth' / 'birthDetails'
        for nest in ("birth", "birthDetails", "birth_data"):
            if isinstance(kundli.get(nest), dict):
                sources.append(kundli[nest])

    # Try string DOB across all sources/field-names
    string_keys = ("dob", "birthDate", "birth_date", "date", "dateOfBirth",
                   "DOB", "birthday")
    for src in sources:
        for k in string_keys:
            v = src.get(k)
            d = _parse_dob_string(v)
            if d is not None:
                return d

    # Try numeric year/month/day across all sources
    for src in sources:
        y = src.get("year") or src.get("birthYear") or src.get("yearOfBirth")
        m = src.get("month") or src.get("birthMonth")
        day = src.get("day") or src.get("birthDay")
        if isinstance(y, int) and 1900 <= y <= 2100:
            if isinstance(m, int) and isinstance(day, int):
                try:
                    return datetime(y, m, day)
                except ValueError:
                    pass
            # Year-only — assume mid-year for age math
            return datetime(y, 6, 30)
    return None


def _compute_age_at(birth: Any, ref: datetime,
                     kundli: Any = None) -> Optional[int]:
    """Compute age in years at `ref` from birth dict (or kundli fallback).
    v2.4 — Now uses _extract_dob_dt for multi-format/multi-source parsing.
    """
    d = _extract_dob_dt(birth, kundli=kundli)
    if d is None:
        return None
    yrs = ref.year - d.year - ((ref.month, ref.day) < (d.month, d.day))
    return max(0, yrs)


def _min_practical_age(is_female: Optional[bool]) -> int:
    """v2.4 — Absolute floor age below which marriage windows are
    suppressed regardless of how strong dashas/transits are."""
    if is_female is True:
        return _MIN_PRACTICAL_AGE_FEMALE
    if is_female is False:
        return _MIN_PRACTICAL_AGE_MALE
    return _MIN_PRACTICAL_AGE_NEUTRAL


def _earliest_practical_dt(birth_dt: Optional[datetime],
                             min_age: int) -> Optional[datetime]:
    """Compute the calendar date when user reaches `min_age` years."""
    if birth_dt is None:
        return None
    try:
        return birth_dt.replace(year=birth_dt.year + min_age)
    except ValueError:   # Feb 29 + leap-year edge
        return birth_dt.replace(year=birth_dt.year + min_age, day=28)


def _classify_age_band(age: Optional[int], is_female: Optional[bool]
                        ) -> Optional[str]:
    """Return EARLY / ON_TIME / LATE / VERY_LATE for given age + gender."""
    if age is None:
        return None
    if is_female is True:
        ladder = _AGE_BANDS_FEMALE
    elif is_female is False:
        ladder = _AGE_BANDS_MALE
    else:
        ladder = _AGE_BANDS_NEUTRAL
    for cutoff, label in ladder:
        if age < cutoff:
            return label
    return "VERY_LATE"


def _urgency_from_band(band: Optional[str]) -> str:
    """Map age band → urgency tier consumed by LLM tone selection."""
    return {
        "EARLY":     "RELAXED",
        "ON_TIME":   "ACTIVE",
        "LATE":      "URGENT",
        "VERY_LATE": "VERY_URGENT",
    }.get(band or "", "UNKNOWN")


def _confluence_label(score: float) -> str:
    if score >= 10.0:
        return "STRONG"
    if score >= 6.0:
        return "MODERATE"
    return "WEAK"


def _build_cascade_narrative(future: List[Dict[str, Any]],
                              top_3: List[Dict[str, Any]],
                              current_active_score: int) -> Optional[str]:
    """When current dasha is weak, explain WHEN + WHY next strong window opens."""
    if current_active_score >= 7:
        return None   # Current dasha already strong — narrative not needed
    if not top_3:
        return ("Aane wale 25 saal mein koi strong marriage activation window "
                "clearly visible nahi ho raha. Chart mixed signals de raha hai.")
    first = top_3[0]
    when = _format_window(first["start"], first["end"])
    triggers = []
    if first["md"] != first["ad"]:
        triggers.append(f"{first['md']}-{first['ad']} dasha activation")
    else:
        triggers.append(f"{first['md']} mahadasha")
    if first.get("pd"):
        triggers.append(f"{first['pd']} pratyantar trigger")
    if first.get("dt"):
        triggers.append("Jupiter + Saturn double-transit confluence")
    why = ", ".join(triggers) if triggers else "marriage planet activation"
    return (f"Abhi current period mein marriage planets active nahi hain. "
            f"Next strong activation window: {when} (driver: {why}).")


# ════════════════════════════════════════════════════════════════════════
# PUBLIC API — compute_timing_window
# ════════════════════════════════════════════════════════════════════════
def compute_timing_window(kundli: dict, intel: dict, kp: dict,
                          birth: Optional[Any] = None) -> dict:
    """Run the full 8-step Marriage Engine v2 pipeline.

    Returns the canonical verdict dict (back-compat with existing
    LLM block formatter + LOCKED FACTS consumers).
    """
    if not isinstance(kundli, dict) or not kundli:
        return {}
    if not isinstance(kp, dict):
        kp = {}

    # Resolve lagna sign idx
    asc = kundli.get("ascendant")
    lagna_si = _sign_idx(asc) if isinstance(asc, str) else None
    if lagna_si is None:
        # Try other shapes
        for key in ("lagnaSign", "ascendant_sign", "ascendantSign"):
            v = kundli.get(key)
            lagna_si = _sign_idx(v) if isinstance(v, str) else (
                v % 12 if isinstance(v, int) else None)
            if lagna_si is not None:
                break
    if lagna_si is None:
        return {
            "verdict": "UNKNOWN", "band": "WEAK",
            "top_3_windows": [], "risk_flags": ["lagna sign unavailable"],
            "primary_window": None, "backup_window": None,
            "key_trigger": None, "confluence_strength": "WEAK",
            "factors": ["GATE lagna_si is None"],
            "engine_version": "v2.0.0",
            "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER",
        }

    # ── Data sufficiency gate (architect-fix: no fail-open on partial chart) ──
    ok, reasons = _data_sufficiency_check(kundli, kp)
    if not ok:
        return {
            "verdict": "UNKNOWN", "band": "WEAK",
            "top_3_windows": [], "risk_flags": reasons,
            "primary_window": None, "backup_window": None,
            "key_trigger": None, "confluence_strength": "WEAK",
            "factors": [f"GATE data_sufficiency_failed: {r}" for r in reasons],
            "engine_version": "v2.0.0",
            "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER",
        }

    factors: List[str] = []

    # Resolve gender hint for karaka weighting
    is_female: Optional[bool] = None
    if isinstance(birth, dict):
        g = (birth.get("gender") or birth.get("sex") or "").lower()
        if g.startswith("f"):
            is_female = True
        elif g.startswith("m"):
            is_female = False

    # ── Age + age-band (used for urgency + recent-window boost) ───────
    # v2.4: pass kundli as fallback source so DOBs stored in chart payload
    # are picked up even when birth dict is empty/sparse. Multi-format
    # parser handles "26 Nov 1992" / "26-11-1992" / ISO / numeric.
    _now_for_age = datetime.utcnow()
    user_age = _compute_age_at(birth, _now_for_age, kundli=kundli)
    age_band = _classify_age_band(user_age, is_female)
    urgency = _urgency_from_band(age_band)
    gender_label = "female" if is_female is True else (
        "male" if is_female is False else "unknown")
    # v2.4 — practical-age floor + earliest acceptable window
    min_practical_age = _min_practical_age(is_female)
    birth_dt = _extract_dob_dt(birth, kundli=kundli)
    earliest_practical = _earliest_practical_dt(birth_dt, min_practical_age)
    too_young = (user_age is not None
                 and user_age < min_practical_age)
    factors.append(
        f"AGE user_age={user_age} gender={gender_label} "
        f"band={age_band} urgency={urgency} "
        f"min_practical={min_practical_age} too_young={too_young}")

    # ── STEP 1 ────────────────────────────────────────────────────────
    d1_map = _step1_d1_filter(kundli, lagna_si)
    try:
        from event_timing._shared.kp_significator_scan import kp_promote_survivors
        _kp_prom = kp_promote_survivors(d1_map, kp, "marriage")
        if _kp_prom:
            factors.append(f"STEP1 KP-promoted={sorted(_kp_prom)}")
    except Exception as _e:
        factors.append(f"STEP1 KP-promote-error={type(_e).__name__}")
    filtered_set = {p for p, info in d1_map.items() if info.get("in_filter")}
    factors.append(f"STEP1 filtered={sorted(filtered_set)}")

    # ── STEP 1.5 — D9-7L karaka floor (v2.2, May 6 2026) ──────────────
    # Classical Parashari rule: D9 (Navamsa) 7L is the SUPREME marriage
    # significator — even more critical than D1 7L for marriage timing
    # because D9 IS the marriage varga. A planet that has zero D1 link
    # but rules D9's 7H must still be evaluated (D9 score, KP signification,
    # weighted rank, dasha activation). Without this floor the engine
    # silently drops the most important Navamsa planet.
    d9_7l = _compute_d9_seventh_lord(kundli)
    if d9_7l and d9_7l not in filtered_set:
        filtered_set.add(d9_7l)
        if d9_7l in d1_map:
            d1_map[d9_7l]["in_filter"] = True
            d1_map[d9_7l]["links"].append("D9 7L (karaka floor)")
        factors.append(f"STEP1.5 D9_7L_FLOOR added={d9_7l}")
    else:
        factors.append(f"STEP1.5 D9_7L={d9_7l} (already in filter or unavailable)")

    # ── STEP 2 ────────────────────────────────────────────────────────
    d9_map = _step2_d9_verify(kundli, lagna_si, filtered_set)
    d9_strong = [p for p, info in d9_map.items() if info.get("d9", 0.0) >= 30.0]
    factors.append(f"STEP2 d9_strong={sorted(d9_strong)}")

    # ── STEP 3 ────────────────────────────────────────────────────────
    kp_result = _step3_kp_verify(kp, filtered_set, d9_7l=d9_7l)
    kp_per = kp_result["per_planet"]
    csl_verdict = kp_result["csl_verdict"]
    csl_is_d9_7l = kp_result.get("csl_is_d9_7l", False)
    factors.append(f"STEP3 7CSL={kp_result.get('csl_planet')}/{csl_verdict} "
                    f"promise={kp_result.get('csl_promise_h')} "
                    f"deny={kp_result.get('csl_deny_h')}"
                    + (f" [7CSL IS D9 7L — ultimate confluence]"
                       if csl_is_d9_7l else ""))

    # ── STEP 4 ────────────────────────────────────────────────────────
    ranked = _step4_rank(d1_map, d9_map, kp_per, lagna_si, is_female,
                          d9_7l=d9_7l)
    top_planet_names = [r["name"] for r in ranked[:5]]
    target_lords = set(top_planet_names)
    # v2.2 — D9 7L is mandatory in target_lords. Even if its weighted
    # rank doesn't reach top-5 (e.g. because D1 link is absent), its
    # dasha period MUST still trigger marriage windows. Without this
    # line, STEP 5/5.5 cascade would silently skip the most important
    # Navamsa lord's dashas.
    if d9_7l and d9_7l not in target_lords:
        target_lords.add(d9_7l)
        factors.append(f"STEP4+ target_lords force-added D9_7L={d9_7l}")
    factors.append(f"STEP4 top5={[(r['name'], r['score']) for r in ranked]}")
    weighted_breakdown = {r["name"]: {"d1": r["d1"], "d9": r["d9"],
                                        "kp": r["kp"], "karaka": r["karaka"],
                                        "total": r["score"]}
                            for r in ranked}

    # ── STEP 5 / 5.5 ──────────────────────────────────────────────────
    chain = _flatten_dasha_chain(kundli)
    now = datetime.utcnow()
    activation = _step5_dasha_activation(chain, target_lords, now,
                                          d9_7l=d9_7l)
    cur_score = activation["active_score"]
    factors.append(f"STEP5 current_active_score={cur_score} "
                    f"lords={activation['active_lords']}")

    future_candidates = _step5_5_future_cascade(chain, target_lords, now,
                                                  activation.get("current"))
    factors.append(f"STEP5.5 future_candidates={len(future_candidates)}")

    # ── STEP 6 — Double transit on each future candidate ──────────────
    planets = kundli.get("planets") or []
    h7_si = (lagna_si + 6) % 12
    seventh_lord = _house_lord(lagna_si, 7)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)
    top_planet_signs: Set[int] = set()
    for n in top_planet_names:
        s = _planet_sign_idx(planets, n)
        if s is not None:
            top_planet_signs.add(s)
    # v2.2 — Always include D9 7L's natal D1 sign in transit targets,
    # even if D9 7L isn't in top-5 ranked. Jupiter/Saturn transiting
    # over (or aspecting) the D9 7L's natal sign is a classical
    # marriage trigger that must not be silently dropped.
    if d9_7l:
        d9_7l_si = _planet_sign_idx(planets, d9_7l)
        if d9_7l_si is not None:
            top_planet_signs.add(d9_7l_si)

    for c in future_candidates:
        dt_info = _step6_double_transit(c, h7_si, seventh_lord_si,
                                          top_planet_signs)
        c["jup"] = dt_info["jup_hit"]
        c["sat"] = dt_info["sat_hit"]
        c["dt"] = dt_info["dt"]
        c["dt_detail"] = dt_info["detail"]
        c["score"] = float(c["score"]) + dt_info["boost"]

    # ── STEP 7 — Ashtakavarga adjustment ──────────────────────────────
    av: Dict[str, Any] = {}
    if compute_ashtakavarga is not None:
        try:
            av = compute_ashtakavarga(planets, lagna_si) or {}
        except Exception:
            av = {}
    av_label = ""
    if av:
        for c in future_candidates:
            adj, label = _step7_ashtakavarga(c, av, h7_si, lagna_si)
            c["score"] += adj
            if label and not av_label:
                av_label = label
        if av_label:
            factors.append(f"STEP7 {av_label}")

    # ── Recency boost: if user is already at/past marriageable age,
    # boost windows starting within next _RECENT_WINDOW_DAYS so the
    # engine surfaces near-term candidates first instead of distant ones.
    recent_focus = age_band in ("ON_TIME", "LATE", "VERY_LATE")
    if recent_focus:
        recent_cutoff = now + timedelta(days=_RECENT_WINDOW_DAYS)
        boost_per_band = {
            "ON_TIME":   _RECENT_BOOST,           # 3.0
            "LATE":      _RECENT_BOOST + 1.5,     # 4.5
            "VERY_LATE": _RECENT_BOOST + 3.0,     # 6.0
        }.get(age_band or "", 0.0)
        boosted_n = 0
        for c in future_candidates:
            if c["start"] <= recent_cutoff:
                c["score"] = float(c["score"]) + boost_per_band
                c["recent_boost"] = boost_per_band
                boosted_n += 1
        if boosted_n:
            factors.append(
                f"AGE_RECENCY boosted {boosted_n} window(s) within "
                f"{_RECENT_WINDOW_DAYS}d by +{boost_per_band}")

    # Re-sort after STEP 6/7 adjustments
    future_candidates.sort(key=lambda x: (x["priority"], -x["score"], x["start"]))

    # ── STEP 8 — Risk flags (separate from window-scoring) ────────────
    risk_flags = _step8_obstacles(kundli, lagna_si, kp, csl_verdict)
    factors.append(f"STEP8 risks={len(risk_flags)}")

    # ── v2.4 AGE-SANITY GUARD — suppress windows that start before the
    # user reaches the practical-age floor. Without this, a 17-year-old
    # whose dasha/PD lights up next month would still see "shaadi 3
    # mahine mein" as primary window — a real-life bug ("akal" missing).
    # We DON'T delete those windows entirely (they remain visible to the
    # cascade narrative), but we demote their priority so they cannot
    # claim the top-3 slots ahead of post-floor windows.
    windows_suppressed_too_young = 0
    if too_young and earliest_practical is not None:
        for c in future_candidates:
            if c["start"] < earliest_practical:
                # Demote to lowest priority bucket + nuke score
                c["priority"] = max(c.get("priority", 0), 99)
                c["score"] = -1000.0  # ensures it sorts to bottom
                c["suppressed_too_young"] = True
                windows_suppressed_too_young += 1
        # Re-sort after demotion so top-3 picker sees post-floor windows
        future_candidates.sort(
            key=lambda x: (x["priority"], -x["score"], x["start"]))
        if windows_suppressed_too_young:
            factors.append(
                f"AGE_GUARD suppressed {windows_suppressed_too_young} "
                f"window(s) before age={min_practical_age} "
                f"(reaches on {earliest_practical.strftime('%Y-%m-%d')})")

    # ── Window selection (gap-filter + diversity) ─────────────────────
    top_3 = _select_top_3(future_candidates)
    # Filter out any suppressed windows that may have leaked through
    if too_young:
        top_3 = [w for w in top_3 if not w.get("suppressed_too_young")]
        # Deterministic flag for the LLM/UI when nothing acceptable exists
        # in scan horizon after the practical-age floor — prevents the LLM
        # from inventing a window or misreading an empty top-3.
        if not top_3:
            factors.append(
                "AGE_GUARD no_acceptable_window_in_horizon — all "
                "candidate windows fall before practical-age floor; "
                "engine returns empty top-3 by design.")

    # ── Output assembly ────────────────────────────────────────────────
    top_3_serial: List[Dict[str, Any]] = []
    for w in top_3:
        top_3_serial.append({
            "md": w["md"],
            "ad": w["ad"],
            "pd": w["pd"],
            "score": round(float(w["score"]), 2),
            "window": _format_window(w["start"], w["end"]),
            "start_iso": w["start"].strftime("%Y-%m-%d"),
            "end_iso": w["end"].strftime("%Y-%m-%d"),
            "dt": bool(w.get("dt")),
            "jup": bool(w.get("jup")),
            "sat": bool(w.get("sat")),
        })

    primary_window = top_3_serial[0]["window"] if top_3_serial else None
    backup_window = top_3_serial[1]["window"] if len(top_3_serial) > 1 else None

    key_trigger = None
    if top_3:
        p = top_3[0]
        parts = [f"{p['md']} MD", f"{p['ad']} AD", f"{p['pd']} PD"]
        if p.get("dt"):
            parts.append("Jupiter+Saturn DT")
        elif p.get("jup"):
            parts.append("Jupiter transit")
        elif p.get("sat"):
            parts.append("Saturn transit")
        key_trigger = " + ".join(parts)

    top_score = float(top_3[0]["score"]) if top_3 else 0.0
    # Boost top_score if current dasha already active
    if cur_score >= _DASHA_SCORE_AD:
        top_score = max(top_score, top_score + cur_score * 0.3)

    verdict, band = _derive_verdict(top_score, csl_verdict, risk_flags)
    confluence_strength = _confluence_label(top_score)

    cascade_narrative = _build_cascade_narrative(future_candidates, top_3,
                                                   cur_score)

    return {
        # Required for LLM formatter
        "verdict": verdict,
        "band": band,
        "top_3_windows": top_3_serial,
        "risk_flags": risk_flags,
        # Wider contract
        "primary_window": primary_window,
        "backup_window": backup_window,
        "key_trigger": key_trigger,
        "confluence_strength": confluence_strength,
        "factors": factors,
        # NEW v2 fields
        "top_marriage_planets": ranked,
        "weighted_breakdown": weighted_breakdown,
        "future_cascade_narrative": cascade_narrative,
        # Age + urgency context (NEW)
        "user_age": user_age,
        "user_gender": gender_label,
        "age_band": age_band,
        "urgency": urgency,
        "recent_year_focus": recent_focus,
        # v2.3 — D9 7L exposure (supreme marriage karaka, Navamsa)
        "d9_seventh_lord": d9_7l,
        # v2.4 — Age-sanity guard fields
        "min_practical_age": min_practical_age,
        "too_young_for_marriage": bool(too_young),
        "earliest_practical_window_start_iso": (
            earliest_practical.strftime("%Y-%m-%d")
            if earliest_practical is not None else None),
        "windows_suppressed_too_young": windows_suppressed_too_young,
        # Engine metadata
        "engine_version": "v2.4.0",
        "engine_arch": (
            "FILTER→VERIFY→ACTIVATE→TRIGGER + D9-7L supreme + age-sanity"),
        "kp_planet_scan": _kp_planet_scan_safe(kp, "marriage", filtered_set),
    }


def _kp_planet_scan_safe(kp, domain, survivors):
    try:
        from event_timing._shared.kp_significator_scan import compute_kp_planet_scan
        return compute_kp_planet_scan(kp, domain, set(survivors or []))
    except Exception:
        return {"domain": domain, "kp_available": False,
                 "planets": [], "deliverers": [], "missed_by_filter": []}
