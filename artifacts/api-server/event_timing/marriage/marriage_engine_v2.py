"""
event_timing/marriage/marriage_engine_v2.py
============================================
COSMIC LENS MARRIAGE ENGINE v2 — clean rewrite.

Architecture: USER-SPEC PIPELINE → ACTIVATE → TRIGGER (v3).

  STEP 0   BCP ages (7H, 7L placement, 7L dual-sign, D1+D9) + early/late + focus ages
  STEP 1   D1 — names only: 7H occupants, 7H aspects, 7L, planets with 7L
  STEP 2   D9 — same name-only rules on Navamsha
  STEP 3   Merge D1+D9 → shadi de sakte planets list (7H occupants, dispositor,
           7H aspects, 7L, 7L conjunct/aspect) + weighted points
  STEP 4   KP validation (Sub-Lord sb_houses; negation; 7L never dropped)
  STEP 5   Rank significators (discrete points)
  STEP 6   Dasha — EXACT MD·AD·PD from kundli dasha tree (see marriage_pipeline_rules)
  STEP 7   Transit — Guru+Shani on FINAL dasha window only (verify, not re-pick)
  STEP 8   Obstacle flags + final gate (late BCP lock, Step5 dasha, transit → predict)

  Code map: user STEP 6 → _step5_* dasha; user STEP 7 → _attach_transit_to_window + SAV.
  Full rule text: event_timing/marriage/marriage_pipeline_rules.py
  (+ Ashtakavarga adjust, age-sanity, obstacle flags)

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
_RASHI_HI = [
    "Mesh", "Vrishabh", "Mithun", "Kark", "Singh", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
]
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

# Step 6 Dasha activation — mainly AD + PD (user spec)
_DASHA_SCORE_MD = 1
_DASHA_SCORE_AD = 5
_DASHA_SCORE_PD = 6
_MIN_AD_PD_SCORE = 5  # window must have AD and/or PD marriage lord active
_DASHA_AD_PD_CONFLUENCE_BOOST = 2.5

# Step 6 Double-transit boost
_DT_BOTH_BOOST = 2.0
_DT_ONE_BOOST = 0.75
_TRANSIT_JUPITER_ORB_DEG = 5.0
_TRANSIT_SATURN_ORB_DEG = 4.0
_TRANSIT_SAMPLE_FRACTIONS = (0.0, 0.5, 1.0)

# Window selection
_MIN_WINDOW_GAP_DAYS = 60   # ≈ 2 months between top-3 windows

# Late-age urgent scan (female 34 / male 36+): search ~12 months, PD-first
_LATE_URGENT_HORIZON_DAYS = 365
_LATE_URGENT_PD_BOOST = 4.0
_LATE_URGENT_NEAR_BOOST = 6.0   # extra if window starts within horizon

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
_BCP_FOCUS_BOOST    = 10.0   # Step-0 focus ages (e.g. 31,34) on delayed charts
# Delayed/late chart + BCP focus 3+ years out → near-term dasha must not win
# over the anchor age (e.g. age 26, BCP 31 → 2031 not Apr 2026).
_BCP_ANCHOR_MIN_GAP_YEARS = 2
_BCP_ANCHOR_GRACE_YEARS   = 1
_BCP_PRE_FOCUS_DEMOTE     = 100.0
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
        s = name_or_str.strip()
        if s in _SIGN_IDX:
            return _SIGN_IDX[s]
        tc = s.title()
        if tc in _SIGN_IDX:
            return _SIGN_IDX[tc]
        key = s.lower().replace(" ", "")
        _hi = {
            "mesh": 0, "aries": 0, "vrishabh": 1, "taurus": 1, "mithun": 2, "gemini": 2,
            "kark": 3, "karka": 3, "cancer": 3, "simha": 4, "singh": 4, "leo": 4,
            "kanya": 5, "virgo": 5, "tula": 6, "libra": 6, "vrishchik": 7, "scorpio": 7,
            "dhanu": 8, "sagittarius": 8, "makar": 9, "capricorn": 9, "kumbh": 10,
            "aquarius": 10, "meen": 11, "pisces": 11,
        }
        if key in _hi:
            return _hi[key]
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
    Rahu/Ketu: only ordinary 7th opposition is counted here; Saturn-style
    3rd/10th special aspects are not applied to nodes.
    Others: 7th only
    """
    diff = (target_si - ap_si) % 12 + 1   # houses are 1..12
    if diff == 7:
        return True
    if aspector == "Mars" and diff in (4, 8):
        return True
    if aspector == "Jupiter" and diff in (5, 9):
        return True
    if aspector == "Saturn" and diff in (3, 10):
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
    """STEP 6 — Build exact MD·AD·PD windows from kundli['dashas'].

    Prefer nested subDashas with real startDate/endDate per PD.
    Synthesize PDs only when AD has no PD list (Vimshottari 120 proportions).
    Each row: {md, ad, pd, start, end, pd_synthesized?}.
    """
    out: List[Dict[str, Any]] = []
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * _FUTURE_SCAN_HORIZON_YEARS)

    dashas = kundli.get("dashas") or []
    if isinstance(dashas, list) and dashas:
        for md in dashas:
            if not isinstance(md, dict):
                continue
            md_lord = (
                md.get("planet") or md.get("lord")
                or md.get("md_lord") or md.get("maha")
            )
            if not md_lord:
                continue
            for ad in (
                md.get("subDashas") or md.get("antar_dashas")
                or md.get("antardashas") or []
            ):
                if not isinstance(ad, dict):
                    continue
                ad_lord = (
                    ad.get("planet") or ad.get("lord")
                    or ad.get("ad_lord") or ad.get("antar")
                )
                ad_start = _parse_iso(ad.get("startDate") or ad.get("start"))
                ad_end = _parse_iso(ad.get("endDate") or ad.get("end"))
                if not (ad_lord and ad_start and ad_end):
                    continue
                if ad_end < today - timedelta(days=30) or ad_start > horizon:
                    continue
                # Build PDs inside AD
                pd_list = (
                    ad.get("subDashas") or ad.get("pratyantar_dashas")
                    or ad.get("pratyantardashas") or ad.get("pratyantar") or []
                )
                if pd_list and isinstance(pd_list, list):
                    for pd in pd_list:
                        pd_lord = (
                            pd.get("planet") or pd.get("lord")
                            or pd.get("pd_lord") or pd.get("pratyantar")
                        )
                        pd_start = _parse_iso(pd.get("startDate") or pd.get("start"))
                        pd_end = _parse_iso(pd.get("endDate") or pd.get("end"))
                        if not (pd_lord and pd_start and pd_end):
                            continue
                        if pd_end < today - timedelta(days=30):
                            continue
                        out.append({
                            "md": md_lord, "ad": ad_lord, "pd": pd_lord,
                            "start": pd_start, "end": pd_end,
                            "pd_synthesized": False,
                        })
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
                            out.append({
                                "md": md_lord, "ad": ad_lord,
                                "pd": pd_lord, "start": cursor,
                                "end": pd_end,
                                "pd_synthesized": True,
                            })
                        cursor = pd_end

    out.sort(key=lambda c: c["start"])
    return out


def _build_dasha_lord_profiles(ranked: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map ranked Step-5 significators to strength/KP metadata for dasha scoring."""
    out: Dict[str, Dict[str, Any]] = {}
    for r in ranked or []:
        name = r.get("name")
        if not isinstance(name, str) or not name:
            continue
        try:
            score = float(r.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        out[name] = {
            "score": score,
            "kp_verdict": r.get("kp_verdict") or r.get("verdict"),
            "kp_points": r.get("kp_points", 0),
            "d9_points": r.get("d9_points", 0),
            "both_divisions": bool(r.get("both_divisions")),
        }
    return out


def _dasha_lord_multiplier(
    lord: str,
    profiles: Optional[Dict[str, Dict[str, Any]]] = None,
    *,
    d9_7l: Optional[str] = None,
) -> float:
    """Convert Step-5 planet quality into a bounded dasha score multiplier."""
    p = (profiles or {}).get(lord) or {}
    try:
        score = float(p.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0

    if score >= 20:
        mult = 1.45
    elif score >= 14:
        mult = 1.25
    elif score >= 8:
        mult = 1.0
    elif score > 0:
        mult = 0.75
    else:
        mult = 1.0  # Back-compat for direct helper calls without profiles.

    kp_verdict = p.get("kp_verdict")
    if kp_verdict == "CONFIRMS":
        mult += 0.15
    elif kp_verdict == "PARTIAL":
        mult -= 0.10
    elif kp_verdict == "DENIES":
        mult -= 0.45

    if p.get("both_divisions"):
        mult += 0.10
    try:
        if float(p.get("d9_points", 0.0)) >= 6.0:
            mult += 0.10
    except (TypeError, ValueError):
        pass
    if d9_7l and lord == d9_7l:
        mult += 0.10
    return max(0.35, min(1.65, mult))


def _dasha_hit_score(
    lord: str,
    base_score: float,
    profiles: Optional[Dict[str, Dict[str, Any]]] = None,
    *,
    d9_7l: Optional[str] = None,
) -> Tuple[float, str]:
    mult = _dasha_lord_multiplier(lord, profiles, d9_7l=d9_7l)
    score = round(base_score * mult, 2)
    return score, f"{lord} x{mult:.2f}={score:.2f}"


def _step5_dasha_activation(chain: List[Dict[str, Any]],
                             target_lords: Set[str],
                             now: datetime,
                             d9_7l: Optional[str] = None,
                             lord_profiles: Optional[Dict[str, Dict[str, Any]]] = None,
                             ) -> Dict[str, Any]:
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
    score = 0.0
    if current["md"] in target_lords:
        pts, detail = _dasha_hit_score(
            current["md"], _DASHA_SCORE_MD, lord_profiles, d9_7l=d9_7l,
        )
        score += pts
        active_lords.append(f"{current['md']} (MD {detail})")
    if current["ad"] in target_lords:
        pts, detail = _dasha_hit_score(
            current["ad"], _DASHA_SCORE_AD, lord_profiles, d9_7l=d9_7l,
        )
        score += pts
        active_lords.append(f"{current['ad']} (AD {detail})")
    if current["pd"] in target_lords:
        pts, detail = _dasha_hit_score(
            current["pd"], _DASHA_SCORE_PD, lord_profiles, d9_7l=d9_7l,
        )
        score += pts
        active_lords.append(f"{current['pd']} (PD {detail})")
    # D9 7L dasha bonus — supreme significator amplifies activation.
    if (d9_7l and d9_7l in target_lords
            and d9_7l in {current["md"], current["ad"], current["pd"]}):
        score += 2
        active_lords.append(f"{d9_7l} (D9 7L bonus)")
    return {"current": current, "active_score": round(score, 2),
            "active_lords": active_lords}


def _step5_5_future_cascade(chain: List[Dict[str, Any]],
                              target_lords: Set[str],
                              now: datetime,
                              current: Optional[Dict[str, Any]],
                              *,
                              late_urgent: bool = False,
                              horizon_days: int = _LATE_URGENT_HORIZON_DAYS,
                              d9_7l: Optional[str] = None,
                              lord_profiles: Optional[Dict[str, Dict[str, Any]]] = None,
                              ) -> List[Dict[str, Any]]:
    """Cascade scan — PD-aware windows (full chain, one-by-one).

    Normal mode: AD and/or PD must be marriage significators.
    Late-urgent mode (user already late by age, e.g. female 34):
      • Still walks the FULL future dasha chain — BCP/horizon never skips years.
      • `horizon_days` only adds near-term score boost (priority), not exclusion.
      • If AD is NOT a marriage significator, still keep chunk when PD is
        (har PD check — AD support optional).
      • Boost PD-only activations so near-term windows surface first.
    """
    candidates: List[Dict[str, Any]] = []
    if not chain:
        return candidates

    cur_md = current["md"] if current else None
    cur_ad = current["ad"] if current else None
    horizon_end = now + timedelta(days=horizon_days) if late_urgent else None

    for c in chain:
        if c["end"] <= now:
            continue
        # BCP / late-urgent: never drop future chunks — scan every window;
        # horizon_end used below for near-term boost + sort priority only.
        beyond_near_horizon = (
            late_urgent
            and horizon_end is not None
            and c["start"] > horizon_end
        )

        ad_hit = c["ad"] in target_lords
        pd_hit = c["pd"] in target_lords

        s = 0.0
        triple = 0
        ad_pd_score = 0.0
        pd_only = False
        dasha_detail: List[str] = []
        md_score = 0.0
        ad_score = 0.0
        pd_score = 0.0

        if late_urgent:
            # PD-first: AD weak ho tab bhi har PD alag se
            if pd_hit:
                pd_score, detail = _dasha_hit_score(
                    c["pd"], _DASHA_SCORE_PD, lord_profiles, d9_7l=d9_7l,
                )
                s += pd_score
                ad_pd_score += pd_score
                dasha_detail.append(f"PD {detail}")
                triple += 1
                if not ad_hit:
                    pd_only = True
                    s += _LATE_URGENT_PD_BOOST
                    dasha_detail.append(f"late PD-only +{_LATE_URGENT_PD_BOOST:g}")
            if ad_hit:
                ad_score, detail = _dasha_hit_score(
                    c["ad"], _DASHA_SCORE_AD, lord_profiles, d9_7l=d9_7l,
                )
                s += ad_score
                ad_pd_score += ad_score
                dasha_detail.append(f"AD {detail}")
                triple += 1
            if c["md"] in target_lords:
                md_score, detail = _dasha_hit_score(
                    c["md"], _DASHA_SCORE_MD, lord_profiles, d9_7l=d9_7l,
                )
                s += md_score
                dasha_detail.append(f"MD {detail}")
                triple += 1
            if ad_pd_score < _MIN_AD_PD_SCORE:
                continue
        else:
            if c["md"] in target_lords:
                md_score, detail = _dasha_hit_score(
                    c["md"], _DASHA_SCORE_MD, lord_profiles, d9_7l=d9_7l,
                )
                s += md_score
                dasha_detail.append(f"MD {detail}")
                triple += 1
            if ad_hit:
                ad_score, detail = _dasha_hit_score(
                    c["ad"], _DASHA_SCORE_AD, lord_profiles, d9_7l=d9_7l,
                )
                s += ad_score
                triple += 1
                ad_pd_score += ad_score
                dasha_detail.append(f"AD {detail}")
            if pd_hit:
                pd_score, detail = _dasha_hit_score(
                    c["pd"], _DASHA_SCORE_PD, lord_profiles, d9_7l=d9_7l,
                )
                s += pd_score
                triple += 1
                ad_pd_score += pd_score
                dasha_detail.append(f"PD {detail}")
            if ad_pd_score < _MIN_AD_PD_SCORE:
                continue

        if s == 0:
            continue

        ad_pd_confluence = bool(ad_hit and pd_hit)
        if ad_pd_confluence:
            conf_boost = _DASHA_AD_PD_CONFLUENCE_BOOST
            if c["ad"] == c["pd"]:
                conf_boost += 1.0
            s += conf_boost
            dasha_detail.append(f"AD+PD confluence +{conf_boost:g}")

        if late_urgent and horizon_end is not None and c["start"] <= horizon_end:
            s += _LATE_URGENT_NEAR_BOOST
            dasha_detail.append(f"near-horizon +{_LATE_URGENT_NEAR_BOOST:g}")

        # Priority: late-urgent → soonest PD windows first; far-future demoted
        if late_urgent and pd_only and not beyond_near_horizon:
            priority = 0
        elif cur_md and c["md"] == cur_md and cur_ad and c["ad"] == cur_ad:
            priority = 1
        elif cur_md and c["md"] == cur_md:
            priority = 2
        elif beyond_near_horizon:
            priority = 4   # still scanned + transit-checked; lower rank only
        else:
            priority = 3

        candidates.append({
            **c,
            "score": round(float(s), 2),
            "triple": triple,
            "priority": priority,
            "pd_only_activation": pd_only,
            "ad_supports": ad_hit,
            "pd_supports": pd_hit,
            "md_score": round(md_score, 2),
            "ad_score": round(ad_score, 2),
            "pd_score": round(pd_score, 2),
            "ad_pd_score": round(ad_pd_score, 2),
            "ad_pd_confluence": ad_pd_confluence,
            "dasha_score_detail": dasha_detail,
            "beyond_bcp_near_horizon": beyond_near_horizon,
        })

    if late_urgent:
        candidates.sort(key=lambda x: (x["priority"], x["start"], -x["score"]))
    else:
        candidates.sort(key=lambda x: (x["priority"], -x["score"], x["start"]))
    return candidates


# ════════════════════════════════════════════════════════════════════════
# STEP 6 — Double Transit confirmation (TRIGGER)
# ════════════════════════════════════════════════════════════════════════
def _planet_lon_at(planet_id: int, when: datetime) -> Optional[float]:
    if not _HAS_SWE:
        return None
    try:
        jd = swe.julday(when.year, when.month, when.day,
                        when.hour + when.minute / 60.0)
        pos, _ = swe.calc_ut(jd, planet_id, _SWE_FLAGS)
        return float(pos[0]) % 360.0
    except Exception:
        return None


def _planet_sign_at(planet_id: int, when: datetime) -> Optional[int]:
    lon = _planet_lon_at(planet_id, when)
    if lon is None:
        return None
    return int(lon / 30.0) % 12


def _extract_asc_lon(kundli: dict) -> Optional[float]:
    for key in ("ascendantLon", "ascendantLongitude", "lagnaLon", "ascendantDeg"):
        v = kundli.get(key)
        try:
            if v is not None:
                return float(v) % 360.0
        except (TypeError, ValueError):
            continue
    return None


def _planet_lon(planets: List[dict], pname: str) -> Optional[float]:
    p = next((x for x in planets or []
              if isinstance(x, dict) and x.get("name") == pname), None)
    if not isinstance(p, dict):
        return None
    for key in ("longitude", "lon", "fullDegree", "absoluteDegree",
                "eclipticLongitude"):
        v = p.get(key)
        try:
            if v is not None:
                return float(v) % 360.0
        except (TypeError, ValueError):
            pass
    sign_si = _planet_sign_idx(planets, pname)
    for key in ("degreeWithinSign", "normDegree", "degree", "deg"):
        v = p.get(key)
        try:
            if sign_si is not None and v is not None:
                deg = float(v)
                if 0.0 <= deg <= 30.0:
                    return (sign_si * 30.0 + deg) % 360.0
        except (TypeError, ValueError):
            pass
    return None


def _angular_orb(diff: float, exact: float) -> float:
    raw = abs((diff % 360.0) - exact)
    return min(raw, 360.0 - raw)


def _exact_transit_hit(
    transit_lon: float,
    planet_name: str,
    target_lon: float,
) -> Optional[Dict[str, Any]]:
    diff = (target_lon - transit_lon) % 360.0
    if planet_name == "Jupiter":
        aspects = (0.0, 120.0, 180.0, 240.0)
        orb_limit = _TRANSIT_JUPITER_ORB_DEG
    else:
        aspects = (0.0, 60.0, 180.0, 270.0)
        orb_limit = _TRANSIT_SATURN_ORB_DEG
    best_exact = min(aspects, key=lambda a: _angular_orb(diff, a))
    orb = _angular_orb(diff, best_exact)
    if orb <= orb_limit:
        return {"aspect_deg": int(best_exact), "orb": round(orb, 2)}
    return None


_MONTH_ABBR = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _iso_to_month_label(iso_date: str) -> str:
    """2029-06-30 → Jun 2029 (admin-friendly step audit)."""
    if not iso_date:
        return ""
    try:
        parts = str(iso_date)[:10].split("-")
        if len(parts) >= 2:
            y, m = parts[0], int(parts[1])
            if 1 <= m <= 12:
                return f"{_MONTH_ABBR[m - 1]} {y}"
    except (TypeError, ValueError):
        pass
    return str(iso_date)[:7]


def _month_sort_key(label: str) -> Tuple[int, int]:
    try:
        abbr, y = label.split()
        return int(y), _MONTH_ABBR.index(abbr) + 1
    except (ValueError, IndexError):
        return (0, 0)


def _lon_to_rashi_label(lon: Optional[float]) -> str:
    if lon is None:
        return ""
    try:
        si = int((float(lon) % 360.0) / 30.0) % 12
        return _RASHI_HI[si]
    except (TypeError, ValueError, IndexError):
        return ""


def _si_to_rashi_label(si: Optional[int]) -> str:
    if si is None:
        return ""
    try:
        return _RASHI_HI[int(si) % 12]
    except (TypeError, ValueError, IndexError):
        return ""


def _rashi_from_transit_sample(sample: Dict[str, Any], planet: str) -> str:
    """Guru/Shani rashi from sample row (prefer stored rashi, else lon/si)."""
    rashi_key = f"{planet}_rashi"
    if sample.get(rashi_key):
        return str(sample[rashi_key])
    lon_key = "jupiter_lon" if planet == "jupiter" else "saturn_lon"
    si_key = "jupiter_si" if planet == "jupiter" else "saturn_si"
    if sample.get(lon_key) is not None:
        return _lon_to_rashi_label(float(sample[lon_key]))
    if sample.get(si_key) is not None:
        return _si_to_rashi_label(int(sample[si_key]))
    return ""


def _transit_rashis_at_iso(iso_date: str) -> Tuple[Optional[str], Optional[str]]:
    """Compute Guru + Shani rashi on a calendar date (legacy DB repair)."""
    if not _HAS_SWE or not iso_date:
        return None, None
    try:
        y, m, d = [int(x) for x in str(iso_date)[:10].split("-")]
        dt = datetime(y, m, d)
        jup_lon = _planet_lon_at(swe.JUPITER, dt)
        sat_lon = _planet_lon_at(swe.SATURN, dt)
        guru = _lon_to_rashi_label(jup_lon) or None
        shani = _lon_to_rashi_label(sat_lon) or None
        return guru, shani
    except Exception:
        return None, None


def _parse_month_labels_from_text(text: str) -> List[str]:
    import re as _re_ml

    found = _re_ml.findall(
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}",
        text or "",
    )
    out: List[str] = []
    for label in found:
        if label not in out:
            out.append(label)
    return out


def _mid_month_iso(month_label: str) -> Optional[str]:
    try:
        abbr, y = month_label.split()
        mi = _MONTH_ABBR.index(abbr) + 1
        return f"{int(y)}-{mi:02d}-15"
    except (ValueError, IndexError):
        return None


def _collect_sign_hits(
    planet_name: str,
    p_si: Optional[int],
    h7_si: int,
    seventh_lord_si: Optional[int],
) -> List[Dict[str, Any]]:
    """Sign-level 7H / 7L transit hits for Guru or Shani."""
    hits: List[Dict[str, Any]] = []
    if p_si is None:
        return hits
    if p_si == h7_si:
        hits.append({
            "target": "7th house",
            "mode": "sign",
            "hit_type": "occupies_7th_house",
        })
    elif _aspects_target(planet_name, p_si, h7_si):
        hits.append({
            "target": "7th house",
            "mode": "sign",
            "hit_type": "aspects_7th_house",
        })
    if seventh_lord_si is not None:
        if p_si == seventh_lord_si:
            hits.append({
                "target": "7th lord sign",
                "mode": "sign",
                "hit_type": "conjunct_7th_lord",
            })
        elif _aspects_target(planet_name, p_si, seventh_lord_si):
            hits.append({
                "target": "7th lord sign",
                "mode": "sign",
                "hit_type": "aspects_7th_lord",
            })
    return hits


_HIT_ACTIVATION_LABELS = {
    "occupies_7th_house": "7th ghar me",
    "aspects_7th_house": "7th ghar drishti",
    "conjunct_7th_lord": "7th lord sign me",
    "aspects_7th_lord": "7th lord drishti",
}

_TRANSIT_TYPE_LABELS = {
    "double": "Double transit (Guru + Shani dono active)",
    "single_guru": "Single transit (sirf Guru active)",
    "single_shani": "Single transit (sirf Shani active)",
    "split": "Split transit (Guru/Shani alag mahino me — double nahi)",
    "none": "Koi 7H/7L transit active nahi",
}


def _hit_to_activation_label(hit: Dict[str, Any]) -> str:
    if hit.get("mode") == "exact_orb":
        tgt = str(hit.get("target") or "").lower()
        if "7th house" in tgt or tgt.startswith("7h"):
            return "7th ghar exact orb"
        if "7th lord" in tgt or tgt.startswith("7l"):
            return "7th lord exact orb"
        return "exact orb"
    return _HIT_ACTIVATION_LABELS.get(
        str(hit.get("hit_type") or ""),
        str(hit.get("target") or "7H/7L link"),
    )


def _activation_from_hits(hits: Optional[List[Dict[str, Any]]]) -> Tuple[bool, str]:
    hits = hits or []
    if not hits:
        return False, "7H/7L par nahi"
    labels: List[str] = []
    for h in hits:
        lab = _hit_to_activation_label(h)
        if lab and lab not in labels:
            labels.append(lab)
    return True, ", ".join(labels)


def _transit_type_label(jup_hit: bool, sat_hit: bool, dt: bool) -> str:
    if dt or (jup_hit and sat_hit):
        return "double"
    if jup_hit:
        return "single_guru"
    if sat_hit:
        return "single_shani"
    return "none"


def _derive_transit_flags_from_by_month(
    by_month: List[Dict[str, Any]],
) -> Tuple[bool, bool, bool, str]:
    """Transit type from displayed month rows — same month both active = double."""
    if not by_month:
        return False, False, False, "none"
    jup = any(bool(r.get("jupiter_active")) for r in by_month)
    sat = any(bool(r.get("saturn_active")) for r in by_month)
    double = any(
        bool(r.get("jupiter_active")) and bool(r.get("saturn_active"))
        for r in by_month
    )
    if double:
        ttype = "double"
    elif jup and sat:
        ttype = "split"
    elif jup:
        ttype = "single_guru"
    elif sat:
        ttype = "single_shani"
    else:
        ttype = "none"
    return jup, sat, double, ttype


def _build_transit_chart_context(
    lagna_si: int,
    h7_si: int,
    seventh_lord: Optional[str],
    seventh_lord_si: Optional[int],
) -> Dict[str, Any]:
    return {
        "lagna_rashi": _RASHI_HI[lagna_si % 12],
        "seventh_house_rashi": _RASHI_HI[h7_si % 12],
        "seventh_lord": seventh_lord or "",
        "seventh_lord_rashi": _si_to_rashi_label(seventh_lord_si),
        "h7_si": h7_si,
        "seventh_lord_si": seventh_lord_si,
    }


def _public_chart_context(ctx: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(ctx, dict):
        return {}
    return {
        "lagna": ctx.get("lagna_rashi"),
        "seventh_house": ctx.get("seventh_house_rashi"),
        "seventh_lord": ctx.get("seventh_lord"),
        "seventh_lord_sign": ctx.get("seventh_lord_rashi"),
    }


def _rashi_label_to_si(label: Optional[str]) -> Optional[int]:
    if not label:
        return None
    try:
        return _RASHI_HI.index(str(label).strip())
    except ValueError:
        return None


def transit_ctx_from_public_chart(cc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Rebuild ephemeris transit context from admin chart_context (legacy traces)."""
    if not isinstance(cc, dict):
        return None
    h7_si = _rashi_label_to_si(cc.get("seventh_house"))
    if h7_si is None:
        return None
    lord_si = _rashi_label_to_si(cc.get("seventh_lord_sign"))
    return {
        "lagna_rashi": cc.get("lagna"),
        "seventh_house_rashi": cc.get("seventh_house"),
        "seventh_lord": cc.get("seventh_lord"),
        "seventh_lord_rashi": cc.get("seventh_lord_sign"),
        "h7_si": h7_si,
        "seventh_lord_si": lord_si,
    }


def _format_planet_month_line(
    planet_label: str,
    rashi: str,
    active: bool,
    activation: str,
) -> str:
    if not rashi:
        return ""
    status = activation if active else "7H/7L par nahi"
    return f"{planet_label} {rashi} ({status})"


def _compact_transit_by_month(
    samples: List[Dict[str, Any]],
    transit_ctx: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    """Month + Guru/Shani rashi + 7H/7L activation (admin step7)."""
    by_month: Dict[str, Dict[str, Any]] = {}

    for sample in samples:
        month = _iso_to_month_label(str(sample.get("date") or ""))
        if not month:
            continue
        row = by_month.setdefault(month, {"month": month})
        for planet, label in (("jupiter", "Guru"), ("saturn", "Shani")):
            rashi = _rashi_from_transit_sample(sample, planet)
            if rashi:
                row[f"{planet}_rashi"] = rashi
            hits = sample.get(f"{planet}_hits") or []
            active, act = _activation_from_hits(hits)
            if active:
                row[f"{planet}_active"] = True
                row[f"{planet}_activation"] = act
            elif f"{planet}_rashi" in row and f"{planet}_activation" not in row:
                row[f"{planet}_active"] = False
                row[f"{planet}_activation"] = "7H/7L par nahi"

    month_rows: List[Dict[str, Any]] = []
    month_labels: List[str] = []
    detail_parts: List[str] = []

    for month in sorted(by_month.keys(), key=lambda m: _month_sort_key(m)):
        row = by_month[month]
        guru = row.get("jupiter_rashi")
        shani = row.get("saturn_rashi")
        if not guru and not shani:
            continue
        month_labels.append(month)
        out_row: Dict[str, Any] = {"month": month}
        line_bits: List[str] = []
        for planet, label in (("jupiter", "Guru"), ("saturn", "Shani")):
            rashi = row.get(f"{planet}_rashi")
            if not rashi:
                continue
            active = bool(row.get(f"{planet}_active"))
            act = str(row.get(f"{planet}_activation") or ("7H/7L par nahi" if not active else ""))
            out_row[f"{planet}_rashi"] = rashi
            out_row[f"{planet}_active"] = active
            out_row[f"{planet}_activation"] = act
            seg = _format_planet_month_line(label, rashi, active, act)
            if seg:
                line_bits.append(seg)
        month_rows.append(out_row)
        detail_parts.append(f"{month}: " + " · ".join(line_bits))

    detail = " · ".join(detail_parts) if detail_parts else "no transit hit"
    return detail, month_labels, month_rows


def _transit_row_at_iso(
    iso_date: str,
    transit_ctx: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """One month row with rashi + 7H/7L activation from ephemeris."""
    month = _iso_to_month_label(iso_date)
    row: Dict[str, Any] = {"month": month}
    if not month or not isinstance(transit_ctx, dict):
        guru, shani = _transit_rashis_at_iso(iso_date)
        if guru:
            row["jupiter_rashi"] = guru
        if shani:
            row["saturn_rashi"] = shani
        return row

    h7_si = transit_ctx.get("h7_si")
    seventh_lord_si = transit_ctx.get("seventh_lord_si")
    if h7_si is None or not _HAS_SWE:
        guru, shani = _transit_rashis_at_iso(iso_date)
        if guru:
            row["jupiter_rashi"] = guru
        if shani:
            row["saturn_rashi"] = shani
        return row

    try:
        y, m, d = [int(x) for x in str(iso_date)[:10].split("-")]
        dt = datetime(y, m, d)
        jup_lon = _planet_lon_at(swe.JUPITER, dt)
        sat_lon = _planet_lon_at(swe.SATURN, dt)
        jup_si = int(jup_lon / 30.0) % 12 if jup_lon is not None else None
        sat_si = int(sat_lon / 30.0) % 12 if sat_lon is not None else None
    except Exception:
        jup_si = sat_si = None

    for planet, p_si, label in (
        ("jupiter", jup_si, "Guru"),
        ("saturn", sat_si, "Shani"),
    ):
        rashi = _si_to_rashi_label(p_si)
        if rashi:
            row[f"{planet}_rashi"] = rashi
        hits = _collect_sign_hits(
            "Jupiter" if planet == "jupiter" else "Saturn",
            p_si,
            int(h7_si),
            int(seventh_lord_si) if seventh_lord_si is not None else None,
        )
        active, act = _activation_from_hits(hits)
        row[f"{planet}_active"] = active
        row[f"{planet}_activation"] = act
    return row


def _enrich_transit_month_labels(
    month_labels: List[str],
    transit_ctx: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    unique = sorted(set(month_labels), key=lambda m: _month_sort_key(m))
    by_month: List[Dict[str, Any]] = []
    parts: List[str] = []
    for month in unique:
        iso = _mid_month_iso(month)
        if not iso:
            continue
        row = _transit_row_at_iso(iso, transit_ctx)
        row["month"] = month
        by_month.append(row)
        line_bits: List[str] = []
        for planet, label in (("jupiter", "Guru"), ("saturn", "Shani")):
            rashi = row.get(f"{planet}_rashi")
            if not rashi:
                continue
            active = bool(row.get(f"{planet}_active"))
            act = str(row.get(f"{planet}_activation") or "7H/7L par nahi")
            seg = _format_planet_month_line(label, rashi, active, act)
            if seg:
                line_bits.append(seg)
        parts.append(f"{month}: " + " · ".join(line_bits) if line_bits else month)
    detail = " · ".join(parts) if parts else "no transit hit"
    return detail, [r["month"] for r in by_month], by_month


def _has_activation_rows(by_month: List[Dict[str, Any]]) -> bool:
    return bool(by_month) and any(
        isinstance(r, dict) and (r.get("jupiter_rashi") or r.get("saturn_rashi"))
        for r in by_month
    )


def finalize_transit_display(
    *,
    samples: Optional[List[Dict[str, Any]]] = None,
    detail: str = "",
    months: Optional[List[str]] = None,
    window: Optional[Dict[str, Any]] = None,
    transit_ctx: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    """Admin step7 — rashi + 7H/7L activation per month."""
    samples = samples or []
    d, m, b = _compact_transit_by_month(samples, transit_ctx)
    if _has_activation_rows(b) and any(
        "jupiter_activation" in r or "saturn_activation" in r for r in b
    ):
        return d, m, b
    if isinstance(window, dict) and window:
        w_samples = window.get("transit_samples") or []
        if w_samples and w_samples is not samples:
            d, m, b = _compact_transit_by_month(w_samples, transit_ctx)
            if _has_activation_rows(b):
                return d, m, b
        check_at = window.get("transit_check_at") or window.get("start_iso")
        if check_at:
            labels = [_iso_to_month_label(str(check_at))]
            if labels[0]:
                return _enrich_transit_month_labels(labels, transit_ctx)
    labels = list(months or []) or _parse_month_labels_from_text(detail) or _parse_month_labels_from_text(d)
    if labels:
        return _enrich_transit_month_labels(labels, transit_ctx)
    return d, m, b


def _build_step7_transit_package(
    window: Dict[str, Any],
    transit_ctx: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    detail, months, by_month = finalize_transit_display(
        samples=window.get("transit_samples") or [],
        detail=str(window.get("dt_detail") or ""),
        months=window.get("transit_months") if isinstance(window.get("transit_months"), list) else None,
        window=window,
        transit_ctx=transit_ctx,
    )
    jup_hit, sat_hit, dt, ttype = _derive_transit_flags_from_by_month(by_month)
    if ttype == "none" and not _has_activation_rows(by_month):
        jup_hit = bool(window.get("jup"))
        sat_hit = bool(window.get("sat"))
        dt = bool(window.get("dt"))
        ttype = _transit_type_label(jup_hit, sat_hit, dt)
    return {
        "detail": detail,
        "months": months,
        "by_month": by_month,
        "transit_type": ttype,
        "transit_type_label": _TRANSIT_TYPE_LABELS.get(ttype, ttype),
        "chart_context": _public_chart_context(transit_ctx),
        "jupiter_hit": jup_hit,
        "saturn_hit": sat_hit,
        "double_transit": dt,
        "transit_confirmed": bool(window.get("transit_confirmed")),
    }


def _monthify_verbose_transit_detail(
    verbose: str,
    transit_ctx: Optional[Dict[str, Any]] = None,
) -> str:
    """Legacy / month-only text → rashi + 7H/7L activation per month."""
    if not verbose or "no transit" in verbose.lower():
        return verbose or "no transit hit"

    import re as _re_m

    labels: List[str] = []
    for iso in _re_m.findall(r"\d{4}-\d{2}-\d{2}", verbose):
        month = _iso_to_month_label(iso)
        if month and month not in labels:
            labels.append(month)
    if not labels:
        labels = _parse_month_labels_from_text(verbose)
    if labels:
        return _enrich_transit_month_labels(labels, transit_ctx)[0]
    return verbose


def _transit_month_summary_from_window(
    w: Dict[str, Any],
    transit_ctx: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    pkg = _build_step7_transit_package(w, transit_ctx)
    return pkg["detail"], pkg["months"], pkg["by_month"]


def _transit_sample_dates(window: Dict[str, Any]) -> List[datetime]:
    custom = window.get("transit_sample_dates")
    if isinstance(custom, list) and custom:
        return [d for d in custom if isinstance(d, datetime)]
    start = window["start"]
    end = window["end"]
    if end <= start:
        return [start]
    samples: List[datetime] = []
    span = end - start
    for frac in _TRANSIT_SAMPLE_FRACTIONS:
        dt = start + span * frac
        if not any(abs((dt - old).total_seconds()) < 60 for old in samples):
            samples.append(dt)
    return samples


def _age_start_dt(birth_dt: Optional[datetime], age: int) -> Optional[datetime]:
    if birth_dt is None:
        return None
    try:
        return birth_dt.replace(year=birth_dt.year + age)
    except ValueError:
        return birth_dt.replace(year=birth_dt.year + age, day=28)


def _monthly_samples(start: datetime, end: datetime) -> List[datetime]:
    samples: List[datetime] = []
    cur = start
    while cur <= end:
        samples.append(cur)
        y = cur.year + (1 if cur.month == 12 else 0)
        m = 1 if cur.month == 12 else cur.month + 1
        d = min(cur.day, 28)
        cur = cur.replace(year=y, month=m, day=d)
    if not samples or samples[-1].date() != end.date():
        samples.append(end)
    return samples


def _build_transit_targets(
    kundli: dict,
    planets: List[dict],
    h7_si: int,
    seventh_lord: str,
    top_planet_names: List[str],
    d9_7l: Optional[str],
) -> List[Dict[str, Any]]:
    _ = top_planet_names, d9_7l
    targets: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, int]] = set()

    def _add(label: str, lon: Optional[float], target_type: str) -> None:
        if lon is None:
            return
        key = (label, int(round(lon * 100)))
        if key in seen:
            return
        seen.add(key)
        targets.append({
            "label": label,
            "target_type": target_type,
            "lon": lon % 360.0,
            "sign_idx": int((lon % 360.0) / 30.0) % 12,
        })

    asc_lon = _extract_asc_lon(kundli)
    if asc_lon is not None:
        _add("7th house", asc_lon + 180.0, "seventh_house")
    else:
        _add("7th house", h7_si * 30.0 + 15.0, "seventh_house")

    _add(f"7th lord {seventh_lord}", _planet_lon(planets, seventh_lord), "seventh_lord")
    return targets


def _attach_transit_to_window(
    window: Dict[str, Any],
    h7_si: int,
    seventh_lord_si: Optional[int],
    top_planet_signs: Set[int],
    transit_targets: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """STEP 7 — Guru+Shani check across final dasha window (verify only)."""
    dt_info = _step6_double_transit(
        window, h7_si, seventh_lord_si, top_planet_signs, transit_targets,
    )
    window["jup"] = dt_info["jup_hit"]
    window["sat"] = dt_info["sat_hit"]
    window["dt"] = dt_info["dt"]
    window["transit_confirmed"] = dt_info.get("transit_confirmed", False)
    window["dt_detail"] = dt_info["detail"]
    window["transit_check_at"] = dt_info.get("best_check_at") or (
        window["start"] + (window["end"] - window["start"]) / 2
    ).isoformat()[:10]
    window["transit_samples"] = dt_info.get("samples", [])
    return dt_info


def _step6_double_transit(window: Dict[str, Any],
                           h7_si: int,
                           seventh_lord_si: Optional[int],
                           top_planet_signs: Set[int],
                           transit_targets: Optional[List[Dict[str, Any]]] = None,
                           ) -> Dict[str, Any]:
    """Double transit over samples: only 7th house or 7th lord can validate."""
    _ = top_planet_signs
    if not _HAS_SWE:
        return {"jup_hit": False, "sat_hit": False, "dt": False, "boost": 0.0,
                "detail": "swisseph unavailable"}

    exact_targets = [
        t for t in (transit_targets or [])
        if t.get("target_type") in {"seventh_house", "seventh_lord"}
        or str(t.get("label", "")).startswith(("7th house", "7th lord", "7L"))
    ]

    jup_hit = False
    sat_hit = False
    samples: List[Dict[str, Any]] = []
    detail_parts: List[str] = []
    best_check_at = None

    for sample_dt in _transit_sample_dates(window):
        jup_lon = _planet_lon_at(swe.JUPITER, sample_dt)
        sat_lon = _planet_lon_at(swe.SATURN, sample_dt)
        jup_si = int(jup_lon / 30.0) % 12 if jup_lon is not None else None
        sat_si = int(sat_lon / 30.0) % 12 if sat_lon is not None else None
        sample = {
            "date": sample_dt.isoformat()[:10],
            "jupiter_lon": round(jup_lon, 3) if jup_lon is not None else None,
            "saturn_lon": round(sat_lon, 3) if sat_lon is not None else None,
            "jupiter_si": jup_si,
            "saturn_si": sat_si,
            "jupiter_rashi": _si_to_rashi_label(jup_si) or None,
            "saturn_rashi": _si_to_rashi_label(sat_si) or None,
            "jupiter_hits": [],
            "saturn_hits": [],
        }

        def _append_sign_hits(planet_name: str, p_si: Optional[int], bucket: str) -> None:
            for hit in _collect_sign_hits(
                planet_name, p_si, h7_si, seventh_lord_si,
            ):
                sample[bucket].append(hit)

        if exact_targets:
            if jup_lon is not None:
                for tgt in exact_targets:
                    hit = _exact_transit_hit(jup_lon, "Jupiter", float(tgt["lon"]))
                    if hit:
                        item = {
                            **hit,
                            "target": tgt["label"],
                            "target_type": tgt.get("target_type"),
                            "mode": "exact_orb",
                        }
                        sample["jupiter_hits"].append(item)
            if sat_lon is not None:
                for tgt in exact_targets:
                    hit = _exact_transit_hit(sat_lon, "Saturn", float(tgt["lon"]))
                    if hit:
                        item = {
                            **hit,
                            "target": tgt["label"],
                            "target_type": tgt.get("target_type"),
                            "mode": "exact_orb",
                        }
                        sample["saturn_hits"].append(item)

        # Sign-level house validation is always checked, because the rule is:
        # Jupiter/Saturn must occupy/aspect 7H or conjoin/aspect the 7L sign.
        _append_sign_hits("Jupiter", jup_si, "jupiter_hits")
        _append_sign_hits("Saturn", sat_si, "saturn_hits")

        if sample["jupiter_hits"]:
            jup_hit = True
        if sample["saturn_hits"]:
            sat_hit = True

        if sample["jupiter_hits"] or sample["saturn_hits"]:
            if best_check_at is None:
                best_check_at = sample["date"]
            samples.append(sample)

    boost = 0.0
    if jup_hit and sat_hit:
        boost = _DT_BOTH_BOOST
    elif jup_hit or sat_hit:
        boost = _DT_ONE_BOOST

    for sample in samples[:2]:
        if sample["jupiter_hits"]:
            h = sample["jupiter_hits"][0]
            detail_parts.append(
                f"{sample['date']} Jup→{h['target']}"
                + (f" orb {h['orb']}°" if "orb" in h else "")
            )
        if sample["saturn_hits"]:
            h = sample["saturn_hits"][0]
            detail_parts.append(
                f"{sample['date']} Sat→{h['target']}"
                + (f" orb {h['orb']}°" if "orb" in h else "")
            )
    transit_ok = bool(jup_hit or sat_hit)
    month_detail, month_labels, by_month = _compact_transit_by_month(samples)
    return {
        "jup_hit": jup_hit,
        "sat_hit": sat_hit,
        "dt": jup_hit and sat_hit,
        "transit_confirmed": transit_ok,
        "boost": boost if transit_ok else 0.0,
        "detail": month_detail,
        "detail_verbose": " + ".join(detail_parts) or "no transit hit",
        "months": month_labels,
        "by_month": by_month,
        "best_check_at": best_check_at,
        "samples": samples,
    }


def _try_bcp_year_transit_support(
    window: Dict[str, Any],
    *,
    birth_dt: Optional[datetime],
    focus_bcp_ages: Set[int],
    h7_si: int,
    seventh_lord_si: Optional[int],
    top_planet_signs: Set[int],
    transit_targets: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """If dasha window overlaps a BCP age, scan that whole age-year for transit."""
    if window.get("transit_confirmed"):
        return None
    hits = set(window.get("bcp_age_hits") or [])
    if focus_bcp_ages:
        hits &= set(focus_bcp_ages)
    if not hits or birth_dt is None:
        return None

    best: Optional[Dict[str, Any]] = None
    for age in sorted(hits):
        start = _age_start_dt(birth_dt, int(age))
        end = _age_start_dt(birth_dt, int(age) + 1)
        if start is None or end is None:
            continue
        end = end - timedelta(days=1)
        scan_window = {
            "start": start,
            "end": end,
            "transit_sample_dates": _monthly_samples(start, end),
        }
        info = _step6_double_transit(
            scan_window, h7_si, seventh_lord_si, top_planet_signs,
            transit_targets,
        )
        if info.get("transit_confirmed"):
            info["bcp_age"] = age
            info["bcp_scan_start"] = start.strftime("%Y-%m-%d")
            info["bcp_scan_end"] = end.strftime("%Y-%m-%d")
            best = info
            break

    if best:
        window["jup"] = bool(best.get("jup_hit"))
        window["sat"] = bool(best.get("sat_hit"))
        window["dt"] = bool(best.get("dt"))
        window["transit_confirmed"] = True
        window["bcp_year_transit_support"] = True
        window["transit_check_at"] = best.get("best_check_at")
        window["transit_samples"] = best.get("samples", [])
        note = (
            f"BCP age {best.get('bcp_age')} year transit support "
            f"{_iso_to_month_label(best.get('bcp_scan_start') or '')}"
            f"–{_iso_to_month_label(best.get('bcp_scan_end') or '')}"
        )
        window["dt_detail"] = (
            (best.get("detail") or "") + " | " + note
        ).strip(" |")
        window["bcp_note"] = (
            (window.get("bcp_note") or "") + " | " + note
        ).strip(" |")
    return best


def _ensure_transit_supported_primary(
    top_3: List[Dict[str, Any]],
    future_candidates: List[Dict[str, Any]],
    *,
    birth_dt: Optional[datetime],
    focus_bcp_ages: Set[int],
    h7_si: int,
    seventh_lord_si: Optional[int],
    top_planet_signs: Set[int],
    transit_targets: Optional[List[Dict[str, Any]]] = None,
    min_start_dt: Optional[datetime] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Primary must have Jupiter/Saturn support; BCP-year scan can rescue it."""
    notes: List[str] = []
    if not top_3:
        return top_3, notes

    def _allowed(w: Dict[str, Any]) -> bool:
        if min_start_dt is not None and w["start"] < min_start_dt:
            return False
        return True

    def _evaluate(w: Dict[str, Any]) -> None:
        if "transit_confirmed" not in w:
            _attach_transit_to_window(
                w, h7_si, seventh_lord_si, top_planet_signs, transit_targets,
            )
        if not w.get("transit_confirmed"):
            _try_bcp_year_transit_support(
                w,
                birth_dt=birth_dt,
                focus_bcp_ages=focus_bcp_ages,
                h7_si=h7_si,
                seventh_lord_si=seventh_lord_si,
                top_planet_signs=top_planet_signs,
                transit_targets=transit_targets,
            )

    for w in top_3:
        _evaluate(w)

    if top_3[0].get("transit_confirmed"):
        return top_3, notes

    skipped = top_3[0]
    skipped["skipped_as_primary_no_transit"] = True
    notes.append(
        f"STEP7 skipped primary {skipped.get('md')}-{skipped.get('ad')}-{skipped.get('pd')} "
        "because no Jupiter/Saturn transit support"
    )

    supported: List[Dict[str, Any]] = []
    for cand in future_candidates:
        if cand.get("suppressed_too_young") or cand.get("suppressed_pre_bcp_focus"):
            continue
        if not _allowed(cand):
            continue
        _evaluate(cand)
        if cand.get("transit_confirmed"):
            supported.append(cand)
            break

    if not supported:
        notes.append("STEP7 found no transit-supported alternate; keeping dasha primary as weak/backup")
        return top_3, notes

    primary = supported[0]
    primary["promoted_by_transit_support"] = True
    notes.append(
        f"STEP7 promoted transit-supported window "
        f"{primary.get('md')}-{primary.get('ad')}-{primary.get('pd')}"
    )

    selected = [primary]
    used = {id(primary)}
    for cand in top_3 + future_candidates:
        if len(selected) >= 3:
            break
        if id(cand) in used:
            continue
        if cand.get("suppressed_too_young") or cand.get("suppressed_pre_bcp_focus"):
            continue
        if not _allowed(cand):
            continue
        if not _gap_ok(cand, selected):
            continue
        selected.append(cand)
        used.add(id(cand))
    selected.sort(key=lambda x: x["start"])
    if primary in selected:
        selected.remove(primary)
        selected.insert(0, primary)
    return selected, notes


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


def _infer_birth_dt_from_age(user_age: int, ref: datetime) -> datetime:
    """Fallback when birth dict has age but no parseable DOB (anchor guard)."""
    try:
        return ref.replace(year=ref.year - int(user_age))
    except ValueError:
        return ref.replace(year=ref.year - int(user_age), day=28)


def _user_age_on_date(birth_dt: Optional[datetime], when: datetime) -> Optional[int]:
    if birth_dt is None:
        return None
    yrs = when.year - birth_dt.year - (
        (when.month, when.day) < (birth_dt.month, birth_dt.day)
    )
    return max(0, yrs)


def _bcp_activation_earliest_dt(
    birth_dt: Optional[datetime],
    activation_age: int,
) -> Optional[datetime]:
    """Calendar date when user enters BCP activation age (birthday year)."""
    return _age_start_dt(birth_dt, int(activation_age))


def _effective_bcp_anchor_age(
    primary_ref_age: Optional[int],
    focus_bcp_ages: Optional[Set[int]],
    user_age: Optional[int],
) -> Optional[int]:
    """Nearest upcoming BCP age ahead of user (focus 27 beats stale primary 24)."""
    if user_age is None:
        return primary_ref_age
    pool: List[int] = []
    if primary_ref_age is not None:
        pool.append(int(primary_ref_age))
    for a in focus_bcp_ages or ():
        pool.append(int(a))
    ahead = sorted({a for a in pool if a > int(user_age)})
    return ahead[0] if ahead else None


def _bcp_anchor_guard_active(
    chart_delayed: bool,
    primary_ref_age: Optional[int],
    user_age: Optional[int],
    focus_bcp_ages: Optional[Set[int]] = None,
) -> bool:
    eff = _effective_bcp_anchor_age(primary_ref_age, focus_bcp_ages, user_age)
    return bool(
        chart_delayed
        and eff is not None
        and user_age is not None
        and eff > int(user_age)
    )


def _bcp_anchor_min_age(primary_ref_age: int, user_age: int) -> int:
    """Strict anchor at upcoming BCP (e.g. 26→27); grace only when BCP is far."""
    gap = primary_ref_age - user_age
    if gap <= _BCP_ANCHOR_MIN_GAP_YEARS:
        return int(primary_ref_age)
    return int(primary_ref_age) - _BCP_ANCHOR_GRACE_YEARS


def _apply_bcp_anchor_guard(
    candidates: List[Dict[str, Any]],
    *,
    chart_delayed: bool,
    primary_ref_age: Optional[int],
    user_age: Optional[int],
    focus_bcp_ages: Set[int],
    birth_dt: Optional[datetime],
) -> int:
    """Demote windows that start before Step-0 BCP activation birthday."""
    eff_age = _effective_bcp_anchor_age(primary_ref_age, focus_bcp_ages, user_age)
    if not (
        _bcp_anchor_guard_active(
            chart_delayed, primary_ref_age, user_age, focus_bcp_ages,
        )
        and birth_dt is not None
        and eff_age is not None
    ):
        return 0
    anchor_min_age = _bcp_anchor_min_age(int(eff_age), int(user_age))
    activation_dt = _bcp_activation_earliest_dt(birth_dt, anchor_min_age)
    n = 0
    for c in candidates:
        too_early = False
        if activation_dt is not None and c["start"] < activation_dt:
            too_early = True
        else:
            focus_hits = set(c.get("bcp_age_hits") or []) & focus_bcp_ages
            if focus_hits:
                continue
            age_at_end = _user_age_on_date(birth_dt, c["end"])
            if age_at_end is not None and age_at_end < anchor_min_age:
                too_early = True
        if too_early:
            c["priority"] = max(c.get("priority", 3), 90)
            c["score"] = float(c.get("score", 0)) - _BCP_PRE_FOCUS_DEMOTE
            c["suppressed_pre_bcp_focus"] = True
            n += 1
    return n


def _delayed_anchor_focus_ages(
    focus_bcp_ages: Set[int],
    *,
    chart_delayed: bool,
    primary_ref_age: Optional[int],
    user_age: Optional[int],
) -> Tuple[Set[int], List[int]]:
    """Delayed charts should not let early BCP hits bypass the primary anchor."""
    focus = {int(a) for a in (focus_bcp_ages or set())}
    if not _bcp_anchor_guard_active(
        chart_delayed, primary_ref_age, user_age, focus_bcp_ages,
    ):
        return focus, []
    eff_age = _effective_bcp_anchor_age(primary_ref_age, focus_bcp_ages, user_age)
    if eff_age is None:
        return focus, []
    anchor_min_age = _bcp_anchor_min_age(int(eff_age), int(user_age))
    trimmed = {a for a in focus if a >= anchor_min_age}
    trimmed.add(int(eff_age))
    removed = sorted(a for a in focus if a < anchor_min_age)
    return trimmed, removed


def _enforce_bcp_activation_floor(
    top_3: List[Dict[str, Any]],
    future_candidates: List[Dict[str, Any]],
    *,
    chart_delayed: bool,
    primary_ref_age: Optional[int],
    focus_bcp_ages: Set[int],
    user_age: Optional[int],
    birth_dt: Optional[datetime],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Hard gate: delayed chart primary cannot start before BCP activation birthday."""
    notes: List[str] = []
    eff_age = _effective_bcp_anchor_age(primary_ref_age, focus_bcp_ages, user_age)
    if not (
        chart_delayed
        and eff_age is not None
        and user_age is not None
        and birth_dt is not None
        and top_3
    ):
        return top_3, notes
    cutoff = _bcp_activation_earliest_dt(birth_dt, int(eff_age))
    if cutoff is None or top_3[0]["start"] >= cutoff:
        return top_3, notes

    eligible = [
        c for c in future_candidates
        if c["start"] >= cutoff
        and not c.get("suppressed_too_young")
        and not c.get("suppressed_pre_bcp_focus")
    ]
    eligible.sort(
        key=lambda x: (x.get("priority", 3), -x.get("score", 0), x["start"]),
    )
    if eligible:
        new_top = _select_top_3(eligible)
        notes.append(
            f"BCP_FLOOR rejected primary before age-{eff_age} birthday "
            f"({cutoff.date()}); promoted {new_top[0]['start'].date()}→"
            f"{new_top[0]['end'].date()}"
        )
        return new_top, notes

    notes.append(
        f"BCP_FLOOR no post-{eff_age} candidates (cutoff {cutoff.date()})"
    )
    return top_3, notes


def _select_top_3(scored: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Greedy top-3 with min-gap + AD-diversity preference."""
    if not scored:
        return []
    pool = [
        c for c in scored
        if not c.get("suppressed_too_young")
        and not c.get("suppressed_pre_bcp_focus")
    ]
    if not pool:
        pool = scored
    chosen = [pool[0]]
    used_ads = {pool[0].get("ad")}
    for cand in pool[1:]:
        if len(chosen) >= 3:
            break
        if not _gap_ok(cand, chosen):
            continue
        # Prefer different AD when possible (architect diversity rule)
        if cand.get("ad") in used_ads:
            # Look ahead — is there a same-quality different-AD cand?
            alt = next((c for c in pool
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


def _ensure_dashas_on_kundli(
    kundli: dict,
    birth: Optional[Any] = None,
) -> dict:
    """Normalize dashas key; synthesize full chain from Moon+DOB when missing."""
    out = dict(kundli)
    raw = out.get("dashas") or out.get("dasha") or []
    if isinstance(raw, list) and raw:
        out["dashas"] = raw
        return out

    try:
        import swisseph as swe
        from kundli_engine import calc_vimshottari_dasha
    except Exception:
        return out

    moon_lon: Optional[float] = None
    for p in out.get("planets") or []:
        if not isinstance(p, dict) or p.get("name") != "Moon":
            continue
        for key in ("longitude", "lon", "longitudeDeg", "siderealLon", "degree"):
            v = p.get(key)
            if v is None:
                continue
            try:
                moon_lon = float(v) % 360.0
                break
            except (TypeError, ValueError):
                continue
    if moon_lon is None and out.get("moonLongitude") is not None:
        try:
            moon_lon = float(out["moonLongitude"]) % 360.0
        except (TypeError, ValueError):
            moon_lon = None
    if moon_lon is None:
        return out

    birth_dt = _extract_dob_dt(birth, kundli=out)
    if birth_dt is None:
        return out

    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        ut_h = (
            birth_dt.hour + birth_dt.minute / 60.0
            + birth_dt.second / 3600.0
        )
        jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day, ut_h)
        moon_trop_raw, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SPEED)
        moon_trop = float(moon_trop_raw[0]) % 360.0
        ayan = float(swe.get_ayanamsa_ut(jd))
        dashas = calc_vimshottari_dasha(moon_lon, moon_trop, jd, ayan)
        if isinstance(dashas, list) and dashas:
            out["dashas"] = dashas
    except Exception:
        pass
    return out


def _target_lords_for_step6(
    step_audit: Optional[Dict[str, Any]],
    ranked: Optional[List[Dict[str, Any]]] = None,
) -> Set[str]:
    """Marriage significators to scan in dasha cascade (admin + gate-fail path)."""
    audit = step_audit or {}
    step1 = (audit.get("step1") or {}).get("result") or {}
    step2 = (audit.get("step2") or {}).get("result") or {}
    step4 = audit.get("step4") or {}
    step5 = audit.get("step5") or {}
    ranked = ranked or step5.get("ranked_top") or []

    target: Set[str] = set()
    for lord in (step1.get("seventh_lord"), step2.get("seventh_lord")):
        if isinstance(lord, str) and lord:
            target.add(lord)
    for name in step4.get("common_planets") or []:
        if isinstance(name, str) and name:
            target.add(name)
    for r in ranked[:10]:
        if isinstance(r, dict):
            name = r.get("name")
            if isinstance(name, str) and name:
                target.add(name)
    return target


def _minimal_step7_audit_from_chart(
    kundli: dict,
    lagna_si: int,
    *,
    status: str = "PENDING",
) -> Dict[str, Any]:
    """Step-7 shell with 7H/7L chart context when dasha/transit not computed yet."""
    planets = (kundli or {}).get("planets") or []
    h7_si = (lagna_si + 6) % 12
    seventh_lord = _house_lord(lagna_si, 7)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)
    transit_ctx = _build_transit_chart_context(
        lagna_si, h7_si, seventh_lord, seventh_lord_si,
    )
    return {
        "name": "Transit verification (Guru/Shani → 7H/7L)",
        "status": status,
        "transit_confirmed": False,
        "per_dasha_windows": [],
        "chart_context": _public_chart_context(transit_ctx),
        "detail": (
            "swisseph unavailable — VPS par pyswisseph install karein"
            if not _HAS_SWE else ""
        ),
    }


def _dasha_window_transit_row(
    w: Dict[str, Any],
    transit_ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """Serialize one dasha window with Guru/Shani 7H/7L transit fields."""
    start = w.get("start")
    end = w.get("end")
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        start = _parse_iso(w.get("start_iso") or w.get("start"))
        end = _parse_iso(w.get("end_iso") or w.get("end"))
    window_label = w.get("window")
    if not window_label and start and end:
        window_label = _format_window(start, end)
    detail, months, by_month = _transit_month_summary_from_window(w, transit_ctx)
    return {
        "md": w.get("md"),
        "ad": w.get("ad"),
        "pd": w.get("pd"),
        "score": round(float(w.get("score", 0)), 2),
        "window": window_label,
        "start_iso": (
            start.strftime("%Y-%m-%d") if isinstance(start, datetime) else w.get("start_iso")
        ),
        "end_iso": (
            end.strftime("%Y-%m-%d") if isinstance(end, datetime) else w.get("end_iso")
        ),
        "pd_only_activation": bool(w.get("pd_only_activation")),
        "dasha_score_detail": w.get("dasha_score_detail") or [],
        "bcp_age_hits": w.get("bcp_age_hits") or [],
        "jup": bool(w.get("jup")),
        "sat": bool(w.get("sat")),
        "dt": bool(w.get("dt")),
        "transit_confirmed": bool(w.get("transit_confirmed")),
        "transit_check_at": w.get("transit_check_at"),
        "dt_detail": detail,
        "transit_months": months,
        "transit_by_month": by_month,
        "transit_samples": w.get("transit_samples") or [],
    }


def apply_step7_transit_to_dasha_windows(
    windows: List[Dict[str, Any]],
    kundli: dict,
    lagna_si: int,
    *,
    target_lords: Optional[Set[str]] = None,
    d9_7l: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """STEP 7 — Guru/Shani real transit on 7H/7L inside each dasha window.

    Returns (transit_matched, all_candidates, step7_audit).
    Final shaadi periods = transit_matched only.
    """
    planets = kundli.get("planets") or []
    h7_si = (lagna_si + 6) % 12
    seventh_lord = _house_lord(lagna_si, 7)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)
    lord_names = sorted(target_lords or [])
    top_planet_signs: Set[int] = set()
    for n in lord_names:
        s = _planet_sign_idx(planets, n)
        if s is not None:
            top_planet_signs.add(s)
    if d9_7l:
        d9_si = _planet_sign_idx(planets, d9_7l)
        if d9_si is not None:
            top_planet_signs.add(d9_si)
    transit_targets = _build_transit_targets(
        kundli, planets, h7_si, seventh_lord, lord_names, d9_7l,
    )
    transit_ctx = _build_transit_chart_context(
        lagna_si, h7_si, seventh_lord, seventh_lord_si,
    )

    all_serial: List[Dict[str, Any]] = []
    matched_serial: List[Dict[str, Any]] = []

    for raw in windows:
        w = dict(raw)
        start = w.get("start")
        end = w.get("end")
        if not isinstance(start, datetime):
            start = _parse_iso(w.get("start_iso") or w.get("start"))
        if not isinstance(end, datetime):
            end = _parse_iso(w.get("end_iso") or w.get("end"))
        if not (isinstance(start, datetime) and isinstance(end, datetime)):
            continue
        w["start"] = start
        w["end"] = end
        _attach_transit_to_window(
            w, h7_si, seventh_lord_si, top_planet_signs, transit_targets,
        )
        row = _dasha_window_transit_row(w, transit_ctx)
        all_serial.append(row)
        if row.get("transit_confirmed"):
            matched_serial.append(row)

    per_dasha: List[Dict[str, Any]] = []
    for row in all_serial:
        pkg = _build_step7_transit_package(row, transit_ctx)
        per_dasha.append({
            "md": row.get("md"),
            "ad": row.get("ad"),
            "pd": row.get("pd"),
            "window": row.get("window"),
            "start_iso": row.get("start_iso"),
            "end_iso": row.get("end_iso"),
            "transit_confirmed": bool(row.get("transit_confirmed")),
            **pkg,
        })

    if not _HAS_SWE:
        swe_note = "swisseph unavailable — VPS par pyswisseph install karein"
        for row in per_dasha:
            if not row.get("detail"):
                row["detail"] = swe_note
        status = "SWE_UNAVAILABLE"
    elif matched_serial:
        status = "DONE"
    elif all_serial:
        status = "NO_TRANSIT_MATCH"
    else:
        status = "NO_WINDOW"

    primary_pkg = (
        _build_step7_transit_package(matched_serial[0], transit_ctx)
        if matched_serial
        else (_build_step7_transit_package(all_serial[0], transit_ctx) if all_serial else {})
    )
    step7: Dict[str, Any] = {
        "name": "Transit verification (Guru/Shani → 7H/7L)",
        "status": status,
        "transit_confirmed": bool(matched_serial),
        "matched_count": len(matched_serial),
        "candidate_count": len(all_serial),
        "per_dasha_windows": per_dasha,
        "chart_context": _public_chart_context(transit_ctx),
        **primary_pkg,
    }
    if not _HAS_SWE and not step7.get("detail"):
        step7["detail"] = swe_note
    print(
        "[marriage_step7] "
        f"status={status} candidates={len(all_serial)} matched={len(matched_serial)} "
        f"swe={_HAS_SWE} 7H={transit_ctx.get('seventh_house_rashi')} "
        f"7L={transit_ctx.get('seventh_lord')}",
        flush=True,
    )
    return matched_serial, all_serial, step7


def build_marriage_step6_audit(
    kundli: dict,
    *,
    step_audit: Optional[Dict[str, Any]] = None,
    ranked: Optional[List[Dict[str, Any]]] = None,
    target_lords: Optional[Set[str]] = None,
    birth: Optional[Any] = None,
    d9_7l: Optional[str] = None,
    lagna_si: Optional[int] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Lightweight Step 6+7 — dasha windows filtered by Guru/Shani 7H/7L transit."""
    raw_n = len((kundli or {}).get("dashas") or (kundli or {}).get("dasha") or [])
    chart = _ensure_dashas_on_kundli(kundli, birth)
    dasha_n = len(chart.get("dashas") or [])
    chain = _flatten_dasha_chain(chart)
    empty_step6: Dict[str, Any] = {
        "name": "Dasha activation + future windows",
        "status": "NO_CHAIN",
        "selected_windows": [],
        "candidate_windows": [],
        "future_candidates_count": 0,
    }
    empty_step7: Dict[str, Any] = {
        "name": "Transit verification (Guru/Shani → 7H/7L)",
        "status": "NO_CHAIN",
        "transit_confirmed": False,
        "per_dasha_windows": [],
    }
    if lagna_si is None:
        lagna_si = _resolve_lagna_si_from_kundli(chart)
    if lagna_si is None:
        empty_step6["status"] = "NO_LAGNA"
        empty_step7["status"] = "NO_LAGNA"
        return empty_step6, empty_step7

    if not chain:
        print(
            "[marriage_step6] NO_CHAIN "
            f"raw_dashas={raw_n} after_ensure={dasha_n} "
            f"has_currentDasha={bool(chart.get('currentDasha'))} "
            f"has_moon={any(isinstance(p, dict) and p.get('name') == 'Moon' for p in (chart.get('planets') or []))}",
            flush=True,
        )
        return empty_step6, _minimal_step7_audit_from_chart(chart, lagna_si, status="NO_CHAIN")

    audit = step_audit or {}
    step2 = (audit.get("step2") or {}).get("result") or {}
    if not d9_7l:
        d9_7l = step2.get("seventh_lord")
    if not ranked:
        ranked = (audit.get("step5") or {}).get("ranked_top") or []
    lords = target_lords or _target_lords_for_step6(audit, ranked)
    if not lords:
        print(
            f"[marriage_step6] NO_TARGETS chain={len(chain)} ranked={len(ranked)}",
            flush=True,
        )
        empty_step6["status"] = "NO_TARGETS"
        empty_step7 = _minimal_step7_audit_from_chart(chart, lagna_si, status="NO_TARGETS")
        return empty_step6, empty_step7

    lord_profiles = _build_dasha_lord_profiles(ranked)
    now = datetime.utcnow()
    activation = _step5_dasha_activation(
        chain, lords, now, d9_7l=d9_7l, lord_profiles=lord_profiles,
    )
    future_candidates = _step5_5_future_cascade(
        chain, lords, now, activation.get("current"),
        late_urgent=False,
        d9_7l=d9_7l,
        lord_profiles=lord_profiles,
    )
    top_3 = _select_top_3(future_candidates)

    matched, candidates, step7 = apply_step7_transit_to_dasha_windows(
        top_3, chart, lagna_si, target_lords=lords, d9_7l=d9_7l,
    )

    step0_block = audit.get("step0") if isinstance(audit.get("step0"), dict) else {}
    step0_tendency = step0_block.get("result") if isinstance(step0_block.get("result"), dict) else {}
    step0a_block = audit.get("step0a") if isinstance(audit.get("step0a"), dict) else {}
    user_age_val = step0_block.get("user_age")
    birth_dt_val = _extract_dob_dt(birth, kundli=chart)
    if birth_dt_val is None and user_age_val is not None:
        birth_dt_val = _infer_birth_dt_from_age(int(user_age_val), now)
    if matched and step0_tendency:
        from event_timing.marriage.bcp_marriage_ages import (
            effective_bcp_pool_for_timing,
            rank_matched_windows_for_late_chart,
        )
        bcp_stub = {
            "d1_future_bcp_ages": step0a_block.get("d1_bcp_ages") or [],
            "d9_future_bcp_ages": step0a_block.get("d9_bcp_ages") or [],
        }
        merged_bcp = effective_bcp_pool_for_timing(
            bcp_stub,
            d1_pace=step0_tendency.get("d1_pace"),
            d9_pace=step0_tendency.get("d9_pace"),
            user_age=int(user_age_val) if user_age_val is not None else None,
        )
        focus_raw = step0a_block.get("focus_ages") or []
        matched = rank_matched_windows_for_late_chart(
            matched,
            marriage_pace=str(
                step0_tendency.get("combined_pace")
                or step0_tendency.get("marriage_pace")
                or ""
            ),
            d1_pace=step0_tendency.get("d1_pace"),
            d9_pace=step0_tendency.get("d9_pace"),
            user_age=int(user_age_val) if user_age_val is not None else None,
            birth_dt=birth_dt_val,
            focus_bcp_ages={
                int(a) for a in focus_raw if isinstance(a, (int, float))
            },
            merged_bcp_pool=merged_bcp,
            primary_ref_age=(
                int(step0a_block.get("primary_reference_age"))
                if isinstance(step0a_block.get("primary_reference_age"), (int, float))
                else None
            ),
        )
        if matched:
            first = matched[0]
            for row in step7.get("per_dasha_windows") or []:
                if not isinstance(row, dict):
                    continue
                if (
                    row.get("md") == first.get("md")
                    and row.get("ad") == first.get("ad")
                    and row.get("pd") == first.get("pd")
                ):
                    step7 = {
                        **step7,
                        "detail": row.get("detail"),
                        "months": row.get("months"),
                        "by_month": row.get("by_month"),
                        "transit_type": row.get("transit_type"),
                        "transit_type_label": row.get("transit_type_label"),
                        "jupiter_hit": row.get("jupiter_hit"),
                        "saturn_hit": row.get("saturn_hit"),
                        "double_transit": row.get("double_transit"),
                        "transit_confirmed": row.get("transit_confirmed"),
                    }
                    break

    if matched:
        step6_status = "DONE"
    elif candidates:
        step6_status = "NO_TRANSIT_MATCH"
    else:
        step6_status = "NO_WINDOW"

    print(
        "[marriage_step6] "
        f"status={step6_status} chain={len(chain)} targets={len(lords)} "
        f"candidates={len(future_candidates)} top3={len(candidates)} "
        f"transit_matched={len(matched)} lords={sorted(lords)[:6]}",
        flush=True,
    )
    step6: Dict[str, Any] = {
        "name": "Dasha activation + future windows (transit-matched final)",
        "status": step6_status,
        "current_activation": activation,
        "future_candidates_count": len(future_candidates),
        "candidate_windows": candidates[:3],
        "selected_windows": matched[:3],
    }
    return step6, step7


# ════════════════════════════════════════════════════════════════════════
# STEP 8 — Final prediction (late BCP + Step5 dasha + transit)
# ════════════════════════════════════════════════════════════════════════
def _bcp_age_to_calendar_window(
    birth_dt: Optional[datetime],
    bcp_age: Optional[int],
) -> Optional[str]:
    """Convert BCP activation age to a calendar month-year for the user reply."""
    if bcp_age is None:
        return None
    if birth_dt is not None:
        try:
            return birth_dt.replace(
                year=birth_dt.year + int(bcp_age),
            ).strftime("%B %Y")
        except (ValueError, OverflowError):
            pass
    return f"around age {int(bcp_age)}"


def apply_marriage_bcp_primary_windows(
    step8_prediction: Dict[str, Any],
    *,
    birth_dt: Optional[datetime] = None,
    dasha_window: Optional[str] = None,
    current_backup: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """User answer: BCP age window PRIMARY; dasha+transit window BACKUP/next."""
    pred = step8_prediction if isinstance(step8_prediction, dict) else {}
    bcp_age = pred.get("predicted_bcp_age")
    if not isinstance(bcp_age, (int, float)):
        bcp_age = None
    else:
        bcp_age = int(bcp_age)

    bcp_pw = str(pred.get("bcp_primary_window") or "").strip() or None
    if not bcp_pw and bcp_age is not None:
        bcp_pw = _bcp_age_to_calendar_window(birth_dt, bcp_age)

    dasha_pw = str(
        dasha_window
        or pred.get("next_dasha_window")
        or pred.get("dasha_transit_month")
        or pred.get("marriage_month_year")
        or (pred.get("primary_dasha") or {}).get("window")
        or ""
    ).strip() or None

    primary = bcp_pw or dasha_pw
    backup = str(current_backup or "").strip() or None
    if dasha_pw and primary and dasha_pw != primary:
        backup = dasha_pw
    elif dasha_pw and not primary:
        primary = dasha_pw

    if isinstance(pred, dict):
        if bcp_pw:
            pred["bcp_primary_window"] = bcp_pw
        if backup:
            pred["next_dasha_window"] = backup

    return primary, backup


def _best_transit_month_year(
    window: Optional[Dict[str, Any]],
    *,
    by_month: Optional[List[Dict[str, Any]]] = None,
    birth_dt: Optional[datetime] = None,
    bcp_age: Optional[int] = None,
) -> Dict[str, Optional[Any]]:
    """Pick clearest month+year label from Step7 by_month (double transit month first)."""
    rows = by_month or (window or {}).get("transit_by_month") or []
    best_month: Optional[str] = None
    for row in rows:
        if isinstance(row, dict) and row.get("jupiter_active") and row.get("saturn_active"):
            best_month = str(row.get("month") or "").strip() or None
            if best_month:
                break
    if not best_month:
        for row in rows:
            if not isinstance(row, dict):
                continue
            if row.get("jupiter_active") or row.get("saturn_active"):
                best_month = str(row.get("month") or "").strip() or None
                if best_month:
                    break
    if not best_month and window:
        win_label = str(window.get("window") or "").strip()
        if win_label:
            best_month = win_label
        else:
            iso = window.get("transit_check_at") or window.get("start_iso")
            if iso:
                best_month = _iso_to_month_label(str(iso)) or None

    month_name: Optional[str] = None
    cal_year: Optional[int] = None
    if best_month:
        parts = best_month.split()
        if len(parts) >= 2 and str(parts[-1]).isdigit() and len(parts) == 2:
            cal_year = int(parts[-1])
            month_name = parts[0]
        elif "–" in best_month or "-" in best_month:
            month_name = best_month
            for token in best_month.replace("–", " ").replace("-", " ").split():
                if token.isdigit() and len(token) == 4:
                    cal_year = int(token)
                    break
        elif parts and str(parts[-1]).isdigit():
            cal_year = int(parts[-1])
            month_name = " ".join(parts[:-1]) or None
        else:
            month_name = best_month

    if cal_year is None and birth_dt is not None and bcp_age is not None:
        cal_year = int(birth_dt.year) + int(bcp_age)

    month_year = best_month
    if not month_year and month_name and cal_year:
        month_year = f"{month_name} {cal_year}"
    elif not month_year and cal_year:
        month_year = str(cal_year)

    return {
        "marriage_month": month_name,
        "marriage_year": cal_year,
        "marriage_month_year": month_year,
    }


def _build_step8_final_prediction(
    *,
    step0_tendency: Dict[str, Any],
    d1_bcp_ages: List[int],
    d9_bcp_ages: List[int],
    ranked: List[Dict[str, Any]],
    matched_windows: List[Dict[str, Any]],
    user_age: Optional[int],
    primary_ref_age: Optional[int],
    focus_bcp_ages: Set[int],
    primary_window: Optional[str],
    key_trigger: Optional[str],
    birth_dt: Optional[datetime] = None,
    step7_by_month: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """D1+D9 late → late BCP only; pick age from transit-matched dasha + Step5 ranks."""
    from event_timing.marriage.bcp_marriage_ages import (
        both_divisions_late,
        filter_bcp_ages_from_current,
        rank_matched_windows_for_late_chart,
    )

    d1_pace = str(step0_tendency.get("d1_pace") or "")
    d9_pace = str(step0_tendency.get("d9_pace") or "")
    late_locked = both_divisions_late(d1_pace, d9_pace)
    marriage_pace = str(
        step0_tendency.get("combined_pace")
        or step0_tendency.get("marriage_pace")
        or ("VERY_LATE" if d1_pace == "VERY_LATE" else "")
    )

    d1_ok = filter_bcp_ages_from_current(d1_bcp_ages, user_age, both_late=late_locked)
    d9_ok = filter_bcp_ages_from_current(d9_bcp_ages, user_age, both_late=late_locked)
    merged_pool = sorted(set(d1_ok) | set(d9_ok))

    matched_windows = rank_matched_windows_for_late_chart(
        list(matched_windows or []),
        marriage_pace=marriage_pace,
        d1_pace=d1_pace,
        d9_pace=d9_pace,
        user_age=user_age,
        birth_dt=birth_dt,
        focus_bcp_ages=focus_bcp_ages,
        merged_bcp_pool=merged_pool,
        primary_ref_age=primary_ref_age,
    )

    if late_locked or d1_pace == "VERY_LATE" or marriage_pace == "VERY_LATE":
        primary_window = None

    ranked_top = [r for r in (ranked or []) if isinstance(r, dict)][:8]
    ranked_names = {str(r.get("name")) for r in ranked_top if r.get("name")}
    ranked_rank = {str(r.get("name")): i for i, r in enumerate(ranked_top) if r.get("name")}

    best_win: Optional[Dict[str, Any]] = None
    best_age: Optional[int] = None
    best_score = -1.0
    best_align: List[str] = []

    for win in matched_windows or []:
        if not isinstance(win, dict):
            continue
        lords = [x for x in (win.get("md"), win.get("ad"), win.get("pd")) if x]
        align = [str(l) for l in lords if str(l) in ranked_names]
        hits = filter_bcp_ages_from_current(
            [int(a) for a in (win.get("bcp_age_hits") or []) if isinstance(a, (int, float))],
            user_age,
            both_late=late_locked,
        )
        if merged_pool:
            in_pool = [a for a in hits if a in merged_pool]
            hits = in_pool or hits

        pick_age: Optional[int] = None
        for pref in sorted(focus_bcp_ages or []):
            if pref in hits:
                pick_age = int(pref)
                break
        if pick_age is None and primary_ref_age is not None and primary_ref_age in hits:
            pick_age = int(primary_ref_age)
        if pick_age is None and hits:
            pick_age = int(hits[0])
        elif pick_age is None and merged_pool:
            pick_age = int(merged_pool[0])

        align_score = sum(8.0 - float(ranked_rank.get(l, 8)) for l in align)
        pool_score = 3.0 if pick_age is not None and pick_age in merged_pool else 0.0
        ref_score = (
            2.0
            if pick_age is not None and primary_ref_age is not None and pick_age == int(primary_ref_age)
            else 0.0
        )
        dasha_score = float(win.get("score") or 0) * 0.12
        dt_score = 50.0 if win.get("dt") or (win.get("jup") and win.get("sat")) else 0.0
        total = align_score + pool_score + ref_score + dasha_score + dt_score

        if total > best_score:
            best_score = total
            best_win = win
            best_age = pick_age
            best_align = align

    if best_age is None and merged_pool:
        best_age = int(merged_pool[0])
        if primary_ref_age is not None and primary_ref_age in merged_pool:
            best_age = int(primary_ref_age)

    transit_ok = bool(matched_windows)
    md = best_win.get("md") if best_win else None
    ad = best_win.get("ad") if best_win else None
    pd = best_win.get("pd") if best_win else None

    parts: List[str] = []
    if late_locked:
        parts.append("D1+D9 late → sirf late BCP ages")
    if best_age is not None:
        parts.append(f"BCP age {best_age}")
    if md and ad and pd:
        parts.append(f"Dasha {md}-{ad}-{pd}")
    elif key_trigger:
        parts.append(key_trigger)
    if best_align:
        parts.append(f"Step5: {', '.join(best_align)}")
    if primary_window:
        parts.append(primary_window)
    parts.append("transit match" if transit_ok else "transit nahi")

    best_window = None
    if best_win and isinstance(best_win, dict):
        best_window = best_win.get("window")
    month_info = _best_transit_month_year(
        best_win,
        by_month=step7_by_month,
        birth_dt=birth_dt,
        bcp_age=best_age,
    )
    dasha_pw = (
        month_info.get("marriage_month_year")
        or best_window
        or primary_window
    )
    bcp_pw = _bcp_age_to_calendar_window(birth_dt, best_age)
    final_pw = bcp_pw or dasha_pw
    marriage_period = final_pw
    next_dasha_pw = dasha_pw if dasha_pw and dasha_pw != final_pw else None
    dasha_transit_month = month_info.get("marriage_month_year")

    d1_show = d1_ok if d1_ok else [
        int(a) for a in (d1_bcp_ages or [])
        if isinstance(a, (int, float)) and (user_age is None or int(a) >= int(user_age))
    ][:8]
    d9_show = d9_ok if d9_ok else [
        int(a) for a in (d9_bcp_ages or [])
        if isinstance(a, (int, float)) and (user_age is None or int(a) >= int(user_age))
    ][:8]

    return {
        "late_chart_bcp_locked": late_locked,
        "d1_pace": d1_pace,
        "d9_pace": d9_pace,
        "d1_bcp_ages": d1_show,
        "d9_bcp_ages": d9_show,
        "predicted_bcp_age": best_age,
        "bcp_primary_window": bcp_pw,
        "next_dasha_window": next_dasha_pw,
        "primary_window": final_pw,
        "marriage_period": marriage_period,
        "marriage_month": month_info.get("marriage_month") if not bcp_pw else None,
        "marriage_year": month_info.get("marriage_year") if not bcp_pw else (
            int(birth_dt.year) + int(best_age) if birth_dt is not None and best_age is not None else None
        ),
        "marriage_month_year": final_pw,
        "dasha_transit_month": dasha_transit_month,
        "primary_dasha": {
            "md": md,
            "ad": ad,
            "pd": pd,
            "start_iso": best_win.get("start_iso") if best_win else None,
            "end_iso": best_win.get("end_iso") if best_win else None,
            "window": best_win.get("window") if best_win else None,
        } if best_win else None,
        "step5_aligned_lords": best_align,
        "step5_ranked_top": [str(r.get("name")) for r in ranked_top[:6] if r.get("name")],
        "transit_confirmed": transit_ok,
        "final_prediction": " · ".join(parts) if parts else "Koi qualified final window nahi",
        "prediction_score": round(best_score, 2) if best_score >= 0 else None,
    }


# ════════════════════════════════════════════════════════════════════════
# Verdict + band derivation
# ════════════════════════════════════════════════════════════════════════
def _risk_severity_score(risk_flags: List[str]) -> Tuple[float, List[str]]:
    """Weighted severity for Step 8 risks; avoids treating all flags equally."""
    score = 0.0
    notes: List[str] = []
    for flag in risk_flags or []:
        fl = flag.lower()
        weight = 0.0
        if "7th cusp sub-lord denies" in fl:
            weight = 5.0
        elif "7th cusp sub-lord partial" in fl:
            weight = 2.5
        elif "saturn in 7h" in fl:
            weight = 3.5
        elif "saturn conjunct 7l" in fl:
            weight = 3.0
        elif "saturn aspects 7h" in fl:
            weight = 2.5
        elif "8l" in fl or "6l" in fl or "12l" in fl:
            weight = 2.5
        elif "rahu in 7h" in fl or "rahu in 1h" in fl:
            weight = 2.0
        elif "venus debilitated" in fl:
            weight = 2.5
        elif "combust" in fl:
            weight = 2.0
        elif "manglik active" in fl:
            weight = 2.0
        elif "manglik mild" in fl:
            weight = 1.0
        elif "delay" in fl or "obstacle" in fl:
            weight = 1.0
        if weight:
            score += weight
            notes.append(f"{flag} ({weight:g})")
    return round(score, 2), notes


def _derive_verdict(top_score: float, kp_csl: str,
                     risk_flags: List[str],
                     *,
                     natal_promise: bool = True,
                     kp_supported: bool = True,
                     has_qualified_window: bool = True,
                     final_transit_support: bool = False,
                     final_double_transit: bool = False,
                     timing_appropriate: bool = True) -> Tuple[str, str, Dict[str, Any]]:
    """Return weighted final verdict, band, and gate diagnostics."""
    risk_score, risk_notes = _risk_severity_score(risk_flags)
    gate_score = float(top_score)
    notes: List[str] = [f"dasha_score={round(top_score, 2)}"]

    if not has_qualified_window:
        return "UNKNOWN", "WEAK", {
            "gate_score": 0.0, "risk_score": risk_score,
            "risk_notes": risk_notes,
            "notes": notes + ["no qualified timing window"],
        }
    if not natal_promise:
        return "UNKNOWN", "WEAK", {
            "gate_score": 0.0, "risk_score": risk_score,
            "risk_notes": risk_notes,
            "notes": notes + ["natal promise missing"],
        }

    if not kp_supported:
        gate_score -= 3.0
        notes.append("KP support missing -3")

    if kp_csl == "CONFIRMS":
        gate_score += 2.0
        notes.append("KP 7CSL CONFIRMS +2")
    elif kp_csl == "PARTIAL":
        gate_score -= 1.0
        notes.append("KP 7CSL PARTIAL -1")
    elif kp_csl == "DENIES":
        gate_score -= 4.0
        notes.append("KP 7CSL DENIES -4")

    if final_double_transit:
        gate_score += 2.5
        notes.append("double transit +2.5")
    elif final_transit_support:
        gate_score += 1.0
        notes.append("single transit support +1")
    else:
        gate_score -= 2.0
        notes.append("transit support missing -2")

    risk_penalty = min(6.0, risk_score * 0.65)
    if risk_penalty:
        gate_score -= risk_penalty
        notes.append(f"risk penalty -{round(risk_penalty, 2)}")

    if not timing_appropriate:
        gate_score -= 5.0
        notes.append("timing inappropriate -5")

    if kp_csl == "DENIES":
        if gate_score >= 8.0 and final_double_transit and kp_supported:
            verdict, band = "DELAYED", "MEDIUM"
        else:
            verdict, band = "DELAYED", "WEAK"
    elif not kp_supported:
        if gate_score >= 8.0 and final_transit_support:
            verdict, band = "DELAYED", "MEDIUM"
        else:
            verdict, band = "DELAYED", "WEAK"
    elif gate_score >= 12.0:
        verdict, band = "PROMISED", "STRONG"
    elif gate_score >= 8.0:
        verdict, band = "PROMISED", "MEDIUM"
    elif gate_score >= 4.0:
        verdict, band = "DELAYED", "WEAK"
    else:
        verdict, band = "UNKNOWN", "WEAK"

    if risk_score >= 6.0 and verdict == "PROMISED":
        verdict = "DELAYED"
        if band == "STRONG":
            band = "MEDIUM"
        notes.append("high risk score caps promise to delayed")
    elif risk_score >= 4.0 and band == "STRONG":
        band = "MEDIUM"
        notes.append("moderate risk caps strong band")

    if kp_csl == "PARTIAL" and band == "STRONG":
        band = "MEDIUM"
        notes.append("KP PARTIAL caps strong band")

    diagnostics = {
        "gate_score": round(gate_score, 2),
        "risk_score": risk_score,
        "risk_notes": risk_notes,
        "risk_penalty": round(risk_penalty, 2),
        "notes": notes,
        "natal_promise": natal_promise,
        "kp_supported": kp_supported,
        "transit_support": final_transit_support,
        "double_transit": final_double_transit,
        "timing_appropriate": timing_appropriate,
    }
    return verdict, band, diagnostics


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
def _merge_natal_step_audit(
    result: Dict[str, Any],
    kundli: dict,
    lagna_si: int,
    kp: dict,
    birth: Optional[Any] = None,
) -> Dict[str, Any]:
    """Attach D1/D9/Step-3 planet list + Step-6 dasha even when timing gates fail."""
    out: Dict[str, Any] = dict(result)
    try:
        from event_timing.marriage.marriage_spec_pipeline import safe_natal_step_audit

        natal = safe_natal_step_audit(kundli, kp or {}, lagna_si)
        if natal:
            audit = out.get("step_audit")
            if not isinstance(audit, dict):
                audit = {}
            else:
                audit = dict(audit)
            audit.update(natal)
            out["step_audit"] = audit
    except Exception:
        pass

    audit = out.get("step_audit")
    if not isinstance(audit, dict):
        audit = {}
    else:
        audit = dict(audit)
    existing_s6 = audit.get("step6") if isinstance(audit.get("step6"), dict) else {}
    existing_s7 = audit.get("step7") if isinstance(audit.get("step7"), dict) else {}
    need_step67 = (
        not (existing_s6.get("selected_windows") or [])
        or not existing_s7.get("chart_context")
    )
    if need_step67:
        try:
            chart = _ensure_dashas_on_kundli(kundli, birth)
            step6, step7 = build_marriage_step6_audit(
                chart, step_audit=audit, birth=birth, lagna_si=lagna_si,
            )
            audit["step6"] = {**existing_s6, **step6}
            audit["step7"] = {**existing_s7, **step7}
            out["step_audit"] = audit
            if step6.get("selected_windows"):
                out["top_3_windows"] = step6["selected_windows"]
                pw = step6["selected_windows"][0].get("window")
                transit_ok = bool(step6["selected_windows"][0].get("transit_confirmed"))
                if pw and (transit_ok or not out.get("primary_window")):
                    out["primary_window"] = pw
            else:
                print(
                    f"[merge_natal_step_audit] step6 empty status={step6.get('status')} "
                    f"candidates={len(step6.get('candidate_windows') or [])} "
                    f"step7_status={step7.get('status')}",
                    flush=True,
                )
        except Exception as exc:
            print(
                f"[merge_natal_step_audit] step6 failed: "
                f"{type(exc).__name__}: {str(exc)[:160]}",
                flush=True,
            )
    return out


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
        for key in (
            "ascendantSignIndex", "ascendantSignIdx", "ascendant_sign_idx",
            "lagna_sign_idx", "lagnaSignIdx", "lagnaSign", "ascendant_sign",
            "ascendantSign",
        ):
            v = kundli.get(key)
            lagna_si = _sign_idx(v) if isinstance(v, str) else (
                v % 12 if isinstance(v, int) else None)
            if lagna_si is not None:
                break
    if lagna_si is None:
        for key in ("ascendantDeg", "ascendantLon", "ascendantLongitude", "lagnaLon"):
            v = kundli.get(key)
            if v is not None:
                try:
                    lagna_si = int(float(v) / 30.0) % 12
                    break
                except (TypeError, ValueError):
                    pass
    if lagna_si is None:
        lagna_si = _resolve_lagna_si_from_kundli(kundli)
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

    # KP from DB chart_data (kundli["kp"]) — not birth-only recompute
    from event_timing.marriage.kp_from_chart import resolve_kp

    kp = resolve_kp(kundli, kp, birth)

    # ── Data sufficiency gate (architect-fix: no fail-open on partial chart) ──
    ok, reasons = _data_sufficiency_check(kundli, kp)
    if not ok:
        gate_result: Dict[str, Any] = {
            "verdict": "UNKNOWN", "band": "WEAK",
            "top_3_windows": [], "risk_flags": reasons,
            "primary_window": None, "backup_window": None,
            "key_trigger": None, "confluence_strength": "WEAK",
            "factors": [f"GATE data_sufficiency_failed: {r}" for r in reasons],
            "engine_version": "v2.0.0",
            "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER",
        }
        try:
            fb = compute_timing_window_fallback(kundli, intel, kp, birth)
            if isinstance(fb, dict):
                sa = fb.get("step_audit")
                if isinstance(sa, dict) and sa:
                    gate_result["step_audit"] = sa
                if fb.get("primary_window"):
                    gate_result["primary_window"] = fb.get("primary_window")
        except Exception:
            pass
        return _merge_natal_step_audit(gate_result, kundli, lagna_si, kp, birth=birth)

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
    if birth_dt is None and user_age is not None:
        birth_dt = _infer_birth_dt_from_age(int(user_age), _now_for_age)
        factors.append(
            f"AGE birth_dt inferred from user_age={user_age} "
            f"(no DOB in birth/kundli — BCP anchor uses estimated birthday)"
        )
    earliest_practical = _earliest_practical_dt(birth_dt, min_practical_age)
    too_young = (user_age is not None
                 and user_age < min_practical_age)
    factors.append(
        f"AGE user_age={user_age} gender={gender_label} "
        f"band={age_band} urgency={urgency} "
        f"min_practical={min_practical_age} too_young={too_young}")

    # ── STEP 0: early/late + age context; STEP 0A: BCP timing plan ────
    from event_timing.marriage.bcp_marriage_ages import apply_bcp_boost_to_candidates
    from event_timing.marriage.marriage_step0 import run_marriage_step0
    from event_timing.marriage.marriage_step0a import (
        annotate_candidates_bcp_ages,
        run_marriage_step0a,
    )

    step0 = run_marriage_step0(
        kundli,
        lagna_si,
        user_age=user_age,
        birth_dt=birth_dt,
        is_female=is_female,
        kp=kp,
        min_practical_age=min_practical_age,
        years_ahead=5,
    )
    marriage_age_ctx = step0.get("marriage_age_context") or {}
    step0_verdict = (step0.get("step0_tendency") or {}).get("verdict") or ""
    _combined_pace = (
        (step0.get("marriage_pace") or {}).get("combined") or {}
    ).get("combined_pace") or "NORMAL"
    step0a = run_marriage_step0a(
        kundli,
        lagna_si,
        combined_pace=_combined_pace,
        age_ctx=marriage_age_ctx,
        user_age=user_age,
        birth_dt=birth_dt,
        years_ahead=5,
        step0_verdict=step0_verdict,
        d1_pace=(step0.get("step0_tendency") or {}).get("d1_pace"),
        d9_pace=(step0.get("step0_tendency") or {}).get("d9_pace"),
    )
    bcp_ctx = step0a.get("bcp_marriage_ages") or {}
    bcp_strategy = step0a.get("bcp_timing_strategy") or {}
    dasha_scan = step0a.get("dasha_scan_plan") or {}
    timing_appropriate = bool(marriage_age_ctx.get("timing_appropriate", True))
    _step0_tendency = step0.get("step0_tendency") or {}
    from event_timing.marriage.bcp_marriage_ages import effective_bcp_pool_for_timing

    _bcp_effective_ages = effective_bcp_pool_for_timing(
        bcp_ctx,
        d1_pace=_step0_tendency.get("d1_pace"),
        d9_pace=_step0_tendency.get("d9_pace"),
        user_age=user_age,
    )
    bcp_ctx_for_hits = dict(bcp_ctx)
    if _bcp_effective_ages:
        bcp_ctx_for_hits["all_marriage_ages"] = _bcp_effective_ages

    factors.append(step0.get("reasoning_summary", "")[:220])
    factors.append(step0a.get("reasoning_summary", "")[:220])
    try:
        from event_timing.marriage.bcp_marriage_ages import bcp_linkage_admin_lines

        for _bcp_line in bcp_linkage_admin_lines(bcp_ctx):
            factors.append(_bcp_line)
    except Exception:
        pass
    factors.append(
        f"STEP0 verdict={step0.get('step0_tendency', {}).get('verdict')} "
        f"chart_pace={step0.get('chart_marriage_pace', {}).get('chart_pace')}"
    )
    factors.append(
        f"STEP0A BCP_mode={bcp_strategy.get('timing_mode')} "
        f"next_bcp={bcp_ctx.get('next_activation_age')} "
        f"bcp_5y={dasha_scan.get('bcp_ages_next_years')}"
    )
    factors.append(
        f"STEP0 age life={marriage_age_ctx.get('life_status')} "
        f"delay_vs_late={marriage_age_ctx.get('delay_vs_late')}"
    )

    # ── STEPS 1–5: User-spec significator pipeline (D1/D9/KP/rank) ────
    from event_timing.marriage.marriage_spec_pipeline import (
        _common_planets_from_merged,
        run_user_spec_pipeline,
    )

    spec = run_user_spec_pipeline(kundli, kp, lagna_si)
    ranked = spec.get("ranked_significators") or []
    target_lords = set(spec.get("target_lords") or [])
    d9_7l = spec.get("d9_seventh_lord")
    d1_7l = spec.get("d1_seventh_lord")
    natal_promise = bool(spec.get("natal_promise"))
    kp_summary = spec.get("kp_summary") or {}
    kp_supported = bool(kp_summary.get("marriage_supported"))
    csl_verdict = kp_summary.get("csl_verdict") or "UNKNOWN"
    csl_is_d9_7l = bool(
        d9_7l and kp_summary.get("csl_planet") == d9_7l
    )
    filtered_set = set(target_lords)
    factors.append(f"SPEC {spec.get('pipeline_version')} "
                    f"natal_promise={natal_promise} kp_supported={kp_supported}")
    factors.append(spec.get("reasoning_summary", ""))
    factors.append(f"STEP5 ranked={[(r['name'], r['score']) for r in ranked[:6]]}")
    top_planet_names = [r["name"] for r in ranked[:6]]
    weighted_breakdown = {
        r["name"]: {
            "d1": r.get("d1_points", 0),
            "d9": r.get("d9_points", 0),
            "kp": r.get("kp_points", 0),
            "both_bonus": r.get("both_bonus", 0),
            "total": r.get("score", 0),
        }
        for r in ranked
    }
    dasha_lord_profiles = _build_dasha_lord_profiles(ranked)

    _chart_pre_delayed = (
        step0_verdict in ("DELAYED", "LATE")
        or marriage_age_ctx.get("delay_vs_late") == "chart_delay"
    )

    # ── STEP 5 / 5.5 — dasha (strategy from STEP 0 BCP) ───────────────
    chain = _flatten_dasha_chain(kundli)
    now = datetime.utcnow()
    activation = _step5_dasha_activation(chain, target_lords, now,
                                          d9_7l=d9_7l,
                                          lord_profiles=dasha_lord_profiles)
    cur_score = activation["active_score"]
    factors.append(f"STEP5 current_active_score={cur_score} "
                    f"lords={activation['active_lords']}")

    late_urgent_scan = bool(
        not too_young
        and dasha_scan.get("late_urgent_scan")
        and not _chart_pre_delayed
    )
    late_horizon_days = int(
        dasha_scan.get("search_horizon_days")
        or bcp_strategy.get("search_horizon_days")
        or _LATE_URGENT_HORIZON_DAYS
    )

    future_candidates = _step5_5_future_cascade(
        chain, target_lords, now, activation.get("current"),
        late_urgent=late_urgent_scan,
        horizon_days=late_horizon_days,
        d9_7l=d9_7l,
        lord_profiles=dasha_lord_profiles,
    )
    annotate_candidates_bcp_ages(
        future_candidates, bcp_ctx_for_hits, birth_dt, user_age=user_age,
    )
    factors.append(
        "STEP0 dasha_entry: " + "; ".join(dasha_scan.get("entry_notes") or [])[:200]
    )
    pd_only_n = sum(1 for c in future_candidates if c.get("pd_only_activation"))
    factors.append(
        f"STEP5.5 future_candidates={len(future_candidates)} "
        f"late_urgent={late_urgent_scan} horizon_days={late_horizon_days} "
        f"pd_only_windows={pd_only_n}"
    )

    bcp_boosted_n = apply_bcp_boost_to_candidates(
        future_candidates,
        bcp_ctx,
        birth_dt,
        now=now,
        strategy={
            **bcp_strategy,
            "prefer_current_dasha": dasha_scan.get("prefer_current_dasha"),
            "bcp_boost_future_only": dasha_scan.get("bcp_boost_future_only"),
            "chart_delayed": _chart_pre_delayed,
        },
        current_dasha=activation.get("current"),
    )
    if bcp_boosted_n:
        factors.append(f"BCP boosted {bcp_boosted_n} dasha window(s)")
        future_candidates.sort(
            key=lambda x: (x.get("priority", 3), -x.get("score", 0), x["start"])
        )

    primary_ref_age = dasha_scan.get("primary_reference_age")
    focus_bcp_ages = set(dasha_scan.get("bcp_focus_ages") or [])
    _next_bcp = (bcp_ctx or {}).get("next_activation_age")
    _pri_bcp = (bcp_ctx or {}).get("primary_priority_age")
    _focus_pri = (dasha_scan.get("late_bcp_focus") or {}).get("primary_age")
    # Delayed chart: late-focus primary (27) beats missed_bcp last_passed (24)
    # or priority-scored far age (35).
    if (
        step0_verdict in ("DELAYED", "LATE")
        and user_age is not None
        and isinstance(_focus_pri, int)
        and _focus_pri > user_age
        and (_focus_pri - user_age) <= 3
    ):
        if primary_ref_age is None or int(primary_ref_age) < _focus_pri:
            factors.append(
                f"BCP primary aligned to focus age {_focus_pri} "
                f"(was {primary_ref_age})"
            )
            primary_ref_age = _focus_pri
            focus_bcp_ages.add(_focus_pri)
    # Incidental in-list age (e.g. 2H→26) must not anchor over upcoming BCP.
    if (
        primary_ref_age is not None
        and user_age is not None
        and step0_verdict in ("DELAYED", "LATE")
    ):
        _bump: Optional[int] = None
        if isinstance(_pri_bcp, int) and _pri_bcp > user_age:
            _bump = _pri_bcp
        elif isinstance(_next_bcp, int) and _next_bcp > user_age:
            _bump = _next_bcp
        if _bump is not None and primary_ref_age <= user_age:
            factors.append(
                f"BCP primary corrected {primary_ref_age}→{_bump} "
                f"(delayed chart; incidental age skipped)"
            )
            primary_ref_age = _bump
            focus_bcp_ages.add(_bump)
    chart_delayed = step0_verdict in ("DELAYED", "LATE") or bool(
        marriage_age_ctx.get("delay_vs_late") == "chart_delay"
        and focus_bcp_ages
    )
    focus_bcp_ages, _removed_early_focus = _delayed_anchor_focus_ages(
        focus_bcp_ages,
        chart_delayed=chart_delayed,
        primary_ref_age=primary_ref_age,
        user_age=user_age,
    )
    if _removed_early_focus:
        factors.append(
            f"BCP_ANCHOR removed early focus age(s) {_removed_early_focus} "
            f"before anchor age {_bcp_anchor_min_age(int(primary_ref_age), int(user_age))}"
        )
    focus_boosted_n = 0
    if chart_delayed and focus_bcp_ages:
        for c in future_candidates:
            hits = set(c.get("bcp_age_hits") or [])
            overlap = hits & focus_bcp_ages
            if overlap:
                c["score"] = float(c["score"]) + _BCP_FOCUS_BOOST
                c["bcp_focus_boost"] = True
                c["bcp_note"] = (
                    (c.get("bcp_note") or "")
                    + f" | Step0 focus age {sorted(overlap)}"
                ).strip(" |")
                focus_boosted_n += 1
        if focus_boosted_n:
            factors.append(
                f"STEP0 focus_boost +{_BCP_FOCUS_BOOST} on {focus_boosted_n} "
                f"window(s) ages {sorted(focus_bcp_ages)}"
            )
            future_candidates.sort(
                key=lambda x: (x.get("priority", 3), -x.get("score", 0), x["start"])
            )

    # BCP anchor guard — delayed chart + focus age years ahead (e.g. 26→31).
    _bcp_anchor_n = _apply_bcp_anchor_guard(
        future_candidates,
        chart_delayed=chart_delayed,
        primary_ref_age=primary_ref_age,
        user_age=user_age,
        focus_bcp_ages=focus_bcp_ages,
        birth_dt=birth_dt,
    )
    if _bcp_anchor_n:
        factors.append(
            f"BCP_ANCHOR demoted {_bcp_anchor_n} near-term window(s) "
            f"before age {_bcp_anchor_min_age(int(primary_ref_age), int(user_age))} "
            f"(focus BCP {primary_ref_age})"
        )
        future_candidates.sort(
            key=lambda x: (x.get("priority", 3), -x.get("score", 0), x["start"])
        )

    # ── STEP 8 — Risk flags (before window pick; used in age context) ─
    planets = kundli.get("planets") or []
    risk_flags = _step8_obstacles(kundli, lagna_si, kp, csl_verdict)
    factors.append(f"STEP8 risks={len(risk_flags)}")

    h7_si = (lagna_si + 6) % 12
    seventh_lord = _house_lord(lagna_si, 7)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)

    # Refresh age context with full Step 8 risk flags (Step 0 used light flags)
    from event_timing.marriage.marriage_age_context import assess_marriage_age_context

    marriage_age_ctx = assess_marriage_age_context(
        user_age=user_age,
        is_female=is_female,
        risk_flags=risk_flags,
        kp_csl_verdict=csl_verdict,
        too_young_engine=too_young,
        min_practical_age=min_practical_age,
    )
    timing_appropriate = bool(marriage_age_ctx.get("timing_appropriate", True))
    step0["marriage_age_context_final"] = marriage_age_ctx
    factors.append(
        f"AGE_CTX(final) life={marriage_age_ctx.get('life_status')} "
        f"chart_late={marriage_age_ctx.get('chart_late_marriage')}"
    )

    # Recency boost — skip when chart is DELAYED and BCP focus is years ahead
    # (e.g. age 26 + focus 31 → do not surface Apr 2026 over 2030).
    _years_to_primary = None
    if primary_ref_age is not None and user_age is not None:
        _years_to_primary = primary_ref_age - user_age
    recent_focus = (
        timing_appropriate
        and not too_young
        and not chart_delayed
        and (
            late_urgent_scan
            or (
                age_band in ("ON_TIME", "LATE", "VERY_LATE")
                and (_years_to_primary is None or _years_to_primary <= 2)
            )
        )
    )
    if recent_focus:
        recent_cutoff = now + timedelta(
            days=late_horizon_days if late_urgent_scan else _RECENT_WINDOW_DAYS
        )
        boost_per_band = {
            "ON_TIME":   _RECENT_BOOST,
            "LATE":      _RECENT_BOOST + 1.5,
            "VERY_LATE": _RECENT_BOOST + 3.0,
        }.get(age_band or "", 0.0)
        if late_urgent_scan:
            boost_per_band += _LATE_URGENT_NEAR_BOOST
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
        future_candidates.sort(
            key=lambda x: (x["priority"], -x["score"], x["start"]))

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

    # ── STEP 6 — Pick final dasha window(s) (no transit in ranking) ───
    top_3 = _select_top_3(future_candidates)
    if _bcp_anchor_guard_active(
        chart_delayed, primary_ref_age, user_age, focus_bcp_ages,
    ):
        _post_bcp = [w for w in top_3 if not w.get("suppressed_pre_bcp_focus")]
        if _post_bcp:
            top_3 = _post_bcp
        else:
            _eligible = [
                c for c in future_candidates
                if not c.get("suppressed_pre_bcp_focus")
            ]
            if _eligible:
                top_3 = _select_top_3(_eligible)
                factors.append(
                    f"BCP_ANCHOR re-picked post-focus windows "
                    f"(anchor age {primary_ref_age})"
                )
            else:
                # No dasha chunk reaches BCP anchor — pick latest-starting window.
                _future = sorted(
                    [c for c in future_candidates if c["start"] > now],
                    key=lambda x: x["start"],
                    reverse=True,
                )
                if _future:
                    top_3 = _select_top_3(_future)
                    factors.append(
                        f"BCP_ANCHOR fallback toward age {primary_ref_age} "
                        f"(no window reached anchor in scan)"
                    )

    _bcp_floor_cutoff: Optional[datetime] = None
    if chart_delayed and birth_dt is not None and user_age is not None:
        _eff_anchor = _effective_bcp_anchor_age(
            primary_ref_age, focus_bcp_ages, user_age,
        )
        if _eff_anchor is not None and _eff_anchor > int(user_age):
            _bcp_floor_cutoff = _bcp_activation_earliest_dt(
                birth_dt, int(_eff_anchor),
            )

    top_3, _floor_notes = _enforce_bcp_activation_floor(
        top_3,
        future_candidates,
        chart_delayed=chart_delayed,
        primary_ref_age=primary_ref_age,
        focus_bcp_ages=focus_bcp_ages,
        user_age=user_age,
        birth_dt=birth_dt,
    )
    factors.extend(_floor_notes)

    # ── STEP 7 — Transit ONLY on final dasha (verify, do not re-pick) ─
    top_planet_signs: Set[int] = set()
    for n in top_planet_names:
        s = _planet_sign_idx(planets, n)
        if s is not None:
            top_planet_signs.add(s)
    if d9_7l:
        d9_7l_si = _planet_sign_idx(planets, d9_7l)
        if d9_7l_si is not None:
            top_planet_signs.add(d9_7l_si)
    transit_targets = _build_transit_targets(
        kundli, planets, h7_si, seventh_lord, top_planet_names, d9_7l,
    )

    top_3, _transit_selection_notes = _ensure_transit_supported_primary(
        top_3,
        future_candidates,
        birth_dt=birth_dt,
        focus_bcp_ages=focus_bcp_ages,
        h7_si=h7_si,
        seventh_lord_si=seventh_lord_si,
        top_planet_signs=top_planet_signs,
        transit_targets=transit_targets,
        min_start_dt=_bcp_floor_cutoff,
    )
    factors.extend(_transit_selection_notes)

    top_3, _floor_notes_post = _enforce_bcp_activation_floor(
        top_3,
        future_candidates,
        chart_delayed=chart_delayed,
        primary_ref_age=primary_ref_age,
        focus_bcp_ages=focus_bcp_ages,
        user_age=user_age,
        birth_dt=birth_dt,
    )
    factors.extend(_floor_notes_post)

    for w in top_3:
        if "transit_confirmed" not in w:
            _attach_transit_to_window(
                w, h7_si, seventh_lord_si, top_planet_signs, transit_targets,
            )
    final_transit: Dict[str, Any] = {}
    if top_3:
        final_transit = {
            "transit_confirmed": bool(top_3[0].get("transit_confirmed")),
            "dt": bool(top_3[0].get("dt")),
            "detail": top_3[0].get("dt_detail"),
        }
    if top_3:
        p = top_3[0]
        factors.append(
            f"STEP7 final_dasha={p['md']}-{p['ad']}-{p['pd']} "
            f"{p['start'].date()}→{p['end'].date()} "
            f"transit_support={final_transit.get('transit_confirmed')} "
            f"double_transit={final_transit.get('dt')} "
            f"detail={final_transit.get('detail')}"
        )

    av: Dict[str, Any] = {}
    if compute_ashtakavarga is not None and top_3:
        try:
            av = compute_ashtakavarga(planets, lagna_si) or {}
        except Exception:
            av = {}
        if av:
            adj, av_label = _step7_ashtakavarga(top_3[0], av, h7_si, lagna_si)
            top_3[0]["sav_adjust"] = adj
            if av_label:
                factors.append(f"STEP7 SAV {av_label}")
    # Filter out any suppressed windows that may have leaked through
    if too_young or not timing_appropriate:
        top_3 = [w for w in top_3 if not w.get("suppressed_too_young")]
        if too_young and earliest_practical is not None:
            top_3 = [w for w in top_3 if w["start"] >= earliest_practical]
        if not top_3:
            factors.append(
                "AGE_GUARD no_acceptable_window — user too young or all "
                "windows before practical-age floor; near-term shaadi blocked."
            )

    # ── Output assembly ────────────────────────────────────────────────
    _transit_chart_ctx = _build_transit_chart_context(
        lagna_si, h7_si, seventh_lord, seventh_lord_si,
    )
    top_3_serial: List[Dict[str, Any]] = []
    for w in top_3:
        _t_detail, _t_months, _t_by_month = _transit_month_summary_from_window(
            w, _transit_chart_ctx,
        )
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
            "transit_confirmed": bool(w.get("transit_confirmed")),
            "transit_check_at": w.get("transit_check_at"),
            "dt_detail": _t_detail,
            "transit_months": _t_months,
            "transit_by_month": _t_by_month,
            "transit_samples": w.get("transit_samples") or [],
            "bcp_year_transit_support": bool(w.get("bcp_year_transit_support")),
            "promoted_by_transit_support": bool(w.get("promoted_by_transit_support")),
            "skipped_as_primary_no_transit": bool(w.get("skipped_as_primary_no_transit")),
            "pd_only_activation": bool(w.get("pd_only_activation")),
            "ad_supports": w.get("ad_supports"),
            "ad_pd_confluence": bool(w.get("ad_pd_confluence")),
            "dasha_score_detail": w.get("dasha_score_detail") or [],
            "bcp_boost": w.get("bcp_boost"),
            "bcp_note": w.get("bcp_note"),
            "bcp_age_hits": w.get("bcp_age_hits") or [],
        })

    candidate_serial = top_3_serial[:3]
    matched_serial = [w for w in candidate_serial if w.get("transit_confirmed")]
    if matched_serial:
        from event_timing.marriage.bcp_marriage_ages import (
            effective_bcp_pool_for_timing,
            rank_matched_windows_for_late_chart,
        )
        _st0 = step0.get("step0_tendency") or {}
        _merged_bcp_full = effective_bcp_pool_for_timing(
            bcp_ctx or {},
            d1_pace=_st0.get("d1_pace"),
            d9_pace=_st0.get("d9_pace"),
            user_age=user_age,
        )
        matched_serial = rank_matched_windows_for_late_chart(
            matched_serial,
            marriage_pace=str(_combined_pace or ""),
            d1_pace=_st0.get("d1_pace"),
            d9_pace=_st0.get("d9_pace"),
            user_age=user_age,
            birth_dt=birth_dt,
            focus_bcp_ages=focus_bcp_ages,
            merged_bcp_pool=_merged_bcp_full,
            primary_ref_age=primary_ref_age,
        )
    if matched_serial:
        factors.append(
            f"STEP6/7 transit_filter kept {len(matched_serial)}/{len(candidate_serial)} "
            f"dasha window(s) with Guru/Shani on 7H/7L"
        )
    elif candidate_serial:
        factors.append(
            "STEP6/7 transit_filter none of top-3 dashas have Guru/Shani on 7H/7L"
        )

    top_3_serial = matched_serial
    primary_window = top_3_serial[0]["window"] if top_3_serial else None
    backup_window = top_3_serial[1]["window"] if len(top_3_serial) > 1 else None

    key_trigger = None
    if top_3_serial:
        p = top_3_serial[0]
        parts = [f"{p.get('md')} MD", f"{p.get('ad')} AD", f"{p.get('pd')} PD"]
        if p.get("dt"):
            parts.append("Jupiter+Saturn DT")
        elif p.get("jup"):
            parts.append("Jupiter transit")
        elif p.get("sat"):
            parts.append("Saturn transit")
        key_trigger = " + ".join(parts)

    top_score = float(top_3_serial[0]["score"]) if top_3_serial else (
        float(top_3[0]["score"]) if top_3 else 0.0
    )
    if cur_score >= _DASHA_SCORE_AD:
        top_score = max(top_score, top_score + cur_score * 0.3)

    final_transit_support = bool(matched_serial)
    final_double_transit = bool(matched_serial and matched_serial[0].get("dt"))

    has_qualified = (
        bool(matched_serial)
        and natal_promise
        and kp_supported
        and timing_appropriate
    )
    factors.append(
        f"STEP8 final_gate qualified={has_qualified} "
        f"(natal={natal_promise} kp={kp_supported} "
        f"dasha_final={bool(top_3)} "
        f"transit_on_final={final_transit_support} "
        f"double_transit={final_double_transit} "
        f"timing_appropriate={timing_appropriate})"
    )

    verdict, band, final_gate = _derive_verdict(
        top_score, csl_verdict, risk_flags,
        natal_promise=natal_promise,
        kp_supported=kp_supported,
        has_qualified_window=has_qualified,
        final_transit_support=final_transit_support,
        final_double_transit=final_double_transit,
        timing_appropriate=timing_appropriate,
    )
    if too_young:
        verdict, band = "DELAYED", "WEAK"
        final_gate["notes"].append("too young override → DELAYED/WEAK")
    confluence_strength = _confluence_label(top_score)
    if top_3_serial and final_double_transit:
        confluence_strength = "STRONG"
    elif top_3_serial and final_transit_support:
        confluence_strength = "MODERATE"
    elif top_3_serial:
        confluence_strength = "WEAK"

    cascade_narrative = _build_cascade_narrative(future_candidates, top_3,
                                                   cur_score)
    if too_young and not top_3_serial:
        cascade_narrative = (
            marriage_age_ctx.get("llm_directive")
            or "User abhi marriage-age se kam hai — near-term timing mat do."
        )

    primary_audit = top_3_serial[0] if top_3_serial else {}
    per_dasha_step7: List[Dict[str, Any]] = []
    for row in candidate_serial:
        pkg = _build_step7_transit_package(row, _transit_chart_ctx)
        per_dasha_step7.append({
            "md": row.get("md"),
            "ad": row.get("ad"),
            "pd": row.get("pd"),
            "window": row.get("window"),
            "start_iso": row.get("start_iso"),
            "end_iso": row.get("end_iso"),
            "transit_confirmed": bool(row.get("transit_confirmed")),
            **pkg,
        })
    _step7_pkg = _build_step7_transit_package(
        primary_audit, _transit_chart_ctx,
    )
    _step7_detail = _step7_pkg["detail"]
    _step7_months = _step7_pkg["months"]
    _step7_by_month = _step7_pkg["by_month"]
    audit_checks: List[Dict[str, Any]] = []
    audit_issues: List[str] = []

    dasha_traced = bool(
        primary_audit.get("md")
        and primary_audit.get("ad")
        and primary_audit.get("pd")
        and primary_audit.get("start_iso")
        and primary_audit.get("end_iso")
    )
    audit_checks.append({
        "name": "dasha_trace",
        "ok": dasha_traced,
        "detail": (
            f"{primary_audit.get('md')}-{primary_audit.get('ad')}-"
            f"{primary_audit.get('pd')} "
            f"{primary_audit.get('start_iso')}→{primary_audit.get('end_iso')}"
            if dasha_traced else "primary window missing MD/AD/PD trace"
        ),
    })
    if not dasha_traced:
        audit_issues.append("primary window has no MD/AD/PD trace")

    anchor_gap = (
        primary_ref_age - user_age
        if primary_ref_age is not None and user_age is not None
        else None
    )
    _eff_anchor = _effective_bcp_anchor_age(
        primary_ref_age, focus_bcp_ages, user_age,
    )
    anchor_min_age = (
        _bcp_anchor_min_age(int(_eff_anchor), int(user_age))
        if _eff_anchor is not None and user_age is not None else None
    )
    primary_bcp_hits = set(primary_audit.get("bcp_age_hits") or [])
    bcp_anchor_required = _bcp_anchor_guard_active(
        chart_delayed, primary_ref_age, user_age, focus_bcp_ages,
    )
    bcp_anchor_ok = True
    if bcp_anchor_required:
        bcp_anchor_ok = bool(
            anchor_min_age is not None
            and any(int(a) >= int(anchor_min_age) for a in primary_bcp_hits)
        )
    audit_checks.append({
        "name": "bcp_anchor",
        "ok": bcp_anchor_ok,
        "required": bcp_anchor_required,
        "detail": (
            f"primary_ref_age={primary_ref_age}, anchor_min_age={anchor_min_age}, "
            f"primary_bcp_hits={sorted(primary_bcp_hits)}"
        ),
    })
    if not bcp_anchor_ok:
        audit_issues.append("delayed chart primary window did not hit BCP anchor age")

    transit_ok = bool(primary_audit.get("transit_confirmed"))
    audit_checks.append({
        "name": "transit_support",
        "ok": transit_ok,
        "detail": _step7_detail,
        "double_transit": bool(primary_audit.get("dt")),
        "bcp_year_rescue": bool(primary_audit.get("bcp_year_transit_support")),
    })
    if not transit_ok:
        audit_issues.append("primary window has no Jupiter/Saturn transit support")

    _step7_by_month = (
        matched_serial[0].get("transit_by_month") if matched_serial else None
    )
    step8_prediction = _build_step8_final_prediction(
        step0_tendency=_step0_tendency,
        d1_bcp_ages=list(bcp_ctx.get("d1_future_bcp_ages") or []),
        d9_bcp_ages=list(bcp_ctx.get("d9_future_bcp_ages") or []),
        ranked=ranked,
        matched_windows=matched_serial,
        user_age=user_age,
        primary_ref_age=primary_ref_age,
        focus_bcp_ages=focus_bcp_ages,
        primary_window=primary_window,
        key_trigger=key_trigger,
        birth_dt=birth_dt,
        step7_by_month=_step7_by_month,
    )
    primary_window, backup_window = apply_marriage_bcp_primary_windows(
        step8_prediction,
        birth_dt=birth_dt,
        dasha_window=step8_prediction.get("dasha_transit_month"),
        current_backup=backup_window,
    )
    factors.append(f"STEP8 final={step8_prediction.get('final_prediction')}")
    if step8_prediction.get("next_dasha_window"):
        factors.append(
            f"STEP8 next_dasha={step8_prediction.get('next_dasha_window')}"
        )
    if step8_prediction.get("late_chart_bcp_locked"):
        factors.append(
            "STEP8 late_BCP locked "
            f"D1={step8_prediction.get('d1_bcp_ages')} "
            f"D9={step8_prediction.get('d9_bcp_ages')}"
        )

    _pred_age = step8_prediction.get("predicted_bcp_age")
    if _pred_age and primary_window:
        expected_reply = (
            f"Aapki shaadi age {_pred_age} ke around — {primary_window} ke beech hogi."
        )
    elif primary_window:
        expected_reply = (
            f"Aapki shaadi {primary_window} ke beech hogi."
        )
    else:
        expected_reply = (
            step8_prediction.get("final_prediction")
            or "Abhi chart se shaadi ka clear period nahi dikh raha."
        )
    audit_checks.append({
        "name": "answer_lock",
        "ok": bool(primary_window),
        "detail": expected_reply,
    })
    timing_audit = {
        "status": "PASS" if not audit_issues else "WARN",
        "issues": audit_issues,
        "primary_window": primary_window,
        "key_trigger": key_trigger,
        "primary_dasha": {
            "md": primary_audit.get("md"),
            "ad": primary_audit.get("ad"),
            "pd": primary_audit.get("pd"),
            "start_iso": primary_audit.get("start_iso"),
            "end_iso": primary_audit.get("end_iso"),
            "score": primary_audit.get("score"),
            "dasha_score_detail": primary_audit.get("dasha_score_detail") or [],
        },
        "bcp": {
            "primary_reference_age": primary_ref_age,
            "anchor_min_age": anchor_min_age,
            "focus_ages": sorted(focus_bcp_ages),
            "primary_bcp_hits": sorted(primary_bcp_hits),
            "late_locked": step8_prediction.get("late_chart_bcp_locked"),
            "predicted_bcp_age": step8_prediction.get("predicted_bcp_age"),
            "d1_bcp_ages": step8_prediction.get("d1_bcp_ages"),
            "d9_bcp_ages": step8_prediction.get("d9_bcp_ages"),
        },
        "transit": {
            "confirmed": transit_ok,
            "double": bool(primary_audit.get("dt")),
            "detail": _step7_detail,
            "months": _step7_months,
            "by_month": _step7_by_month,
        },
        "checks": audit_checks,
        "expected_reply": expected_reply,
        "step8_prediction": step8_prediction,
    }
    merged_items = sorted(
        (spec.get("merged") or {}).items(),
        key=lambda kv: float((kv[1] or {}).get("natal_points", 0)),
        reverse=True,
    )
    kp_details = spec.get("kp_details") or {}
    step_audit = {
        "step0": {
            "name": "Early/Late + age context",
            "status": "DONE",
            "result": step0.get("step0_tendency") or {},
            "user_age": user_age,
            "age_band": age_band,
            "timing_appropriate": timing_appropriate,
            "min_practical_age": min_practical_age,
        },
        "step0a": {
            "name": "BCP ages + dasha scan plan",
            "status": "DONE",
            "primary_reference_age": primary_ref_age,
            "timing_mode": (bcp_strategy or {}).get("timing_mode"),
            "next_activation_age": (bcp_ctx or {}).get("next_activation_age"),
            "late_urgent_scan": dasha_scan.get("late_urgent_scan"),
            "focus_ages": sorted(focus_bcp_ages),
            "bcp_ages_next_years": list(dasha_scan.get("bcp_ages_next_years") or [])[:4],
            "d1_7l_linkage_houses": (bcp_ctx or {}).get("d1_7l_linkage_houses") or [],
            "d9_7l_linkage_houses": (bcp_ctx or {}).get("d9_7l_linkage_houses") or [],
            "shared_7l_linkage_houses": (bcp_ctx or {}).get("shared_7l_linkage_houses") or [],
            "shared_house_priority_ages": (bcp_ctx or {}).get("shared_house_priority_ages") or [],
            "d1_bcp_ages": (bcp_ctx or {}).get("d1_future_bcp_ages") or [],
            "d9_bcp_ages": (bcp_ctx or {}).get("d9_future_bcp_ages") or [],
            "d1_seventh_lord": (bcp_ctx or {}).get("seventh_lord"),
            "d9_seventh_lord": ((bcp_ctx or {}).get("d9_bcp") or {}).get("seventh_lord"),
            "d1_7l_placement_house": (bcp_ctx or {}).get("seventh_lord_house"),
            "d1_7l_aspect_houses": [
                h.get("house")
                for h in ((bcp_ctx or {}).get("aspect_houses") or [])
                if isinstance(h, dict) and isinstance(h.get("house"), int)
            ],
            "d9_7l_placement_house": ((bcp_ctx or {}).get("d9_bcp") or {}).get("seventh_lord_house"),
            "d9_7l_aspect_houses": [
                h.get("house")
                for h in (((bcp_ctx or {}).get("d9_bcp") or {}).get("aspect_houses") or [])
                if isinstance(h, dict) and isinstance(h.get("house"), int)
            ],
            "bcp_house_display": (bcp_ctx or {}).get("bcp_admin_display") or {},
            "priority_ages": (bcp_ctx or {}).get("priority_marriage_ages") or [],
            "future_priority_ages": (bcp_ctx or {}).get("future_priority_ages") or [],
            "entry_notes": dasha_scan.get("entry_notes") or [],
        },
        "step1": {
            "name": "D1 marriage significator names",
            "status": "DONE",
            "result": spec.get("step1_d1") or {},
        },
        "step2": {
            "name": "D9 marriage significator names",
            "status": "DONE",
            "result": spec.get("step2_d9") or {},
        },
        "step3": {
            "name": "D1+D9 shadi de sakte planets (7H linkage)",
            "status": "DONE",
            "merged_count": len(spec.get("merged") or {}),
            "common_planets": _common_planets_from_merged(spec.get("merged") or {}),
            "marriage_giving_planets": spec.get("step3_marriage_giving_planets") or [],
            "planet_names": [
                p.get("name")
                for p in (spec.get("step3_marriage_giving_planets") or [])
                if isinstance(p, dict) and p.get("name")
            ],
            "top_merged": [
                {
                    "name": pname,
                    "natal_points": row.get("natal_points", 0),
                    "d1_points": row.get("d1_points", 0),
                    "d9_points": row.get("d9_points", 0),
                    "both_bonus": row.get("both_bonus", 0),
                    "both_divisions": row.get("both_divisions", False),
                    "strength_adjust": row.get("strength_adjust", 0),
                    "d1_links": row.get("d1_links") or [],
                    "d9_links": row.get("d9_links") or [],
                }
                for pname, row in merged_items[:8]
            ],
        },
        "step4": {
            "name": "Common planets (D1+D9)",
            "status": "DONE",
            "common_planets": _common_planets_from_merged(spec.get("merged") or {}),
            "summary": kp_summary,
            "top_kp": [
                {
                    "name": r.get("name"),
                    "verdict": (kp_details.get(r.get("name")) or {}).get("verdict"),
                    "kp_points": (kp_details.get(r.get("name")) or {}).get("kp_points"),
                    "confidence": (kp_details.get(r.get("name")) or {}).get("kp_confidence"),
                    "note": (kp_details.get(r.get("name")) or {}).get("note"),
                }
                for r in ranked[:8]
            ],
        },
        "step5": {
            "name": "Rank final significators + dasha targets",
            "status": "DONE",
            "natal_promise": natal_promise,
            "target_lords": sorted(target_lords),
            "ranked_top": [
                {
                    "name": r.get("name"),
                    "score": r.get("score"),
                    "d1_points": r.get("d1_points"),
                    "d9_points": r.get("d9_points"),
                    "both_bonus": r.get("both_bonus"),
                    "natal_points": r.get("natal_points"),
                    "kp_points": r.get("kp_points"),
                    "kp_weighted_points": r.get("kp_weighted_points"),
                    "kp_verdict": r.get("kp_verdict"),
                    "links": (r.get("links") or [])[:8],
                }
                for r in ranked[:12]
            ],
        },
        "step6": {
            "name": "Dasha activation + future windows (transit-matched final)",
            "status": (
                "DONE" if matched_serial
                else ("NO_TRANSIT_MATCH" if candidate_serial else "NO_WINDOW")
            ),
            "current_activation": activation,
            "future_candidates_count": len(future_candidates),
            "candidate_windows": candidate_serial,
            "selected_windows": [
                {
                    "window": w.get("window"),
                    "md": w.get("md"),
                    "ad": w.get("ad"),
                    "pd": w.get("pd"),
                    "start_iso": w.get("start_iso"),
                    "end_iso": w.get("end_iso"),
                    "score": w.get("score"),
                    "pd_only_activation": w.get("pd_only_activation"),
                    "bcp_age_hits": w.get("bcp_age_hits") or [],
                    "dasha_score_detail": w.get("dasha_score_detail") or [],
                    "jup": w.get("jup"),
                    "sat": w.get("sat"),
                    "dt": w.get("dt"),
                    "transit_confirmed": w.get("transit_confirmed"),
                    "dt_detail": w.get("dt_detail"),
                    "transit_months": w.get("transit_months"),
                    "transit_by_month": w.get("transit_by_month"),
                }
                for w in matched_serial[:3]
            ],
        },
        "step7": {
            "name": "Transit verification (Guru/Shani → 7H/7L)",
            "status": (
                "DONE" if matched_serial
                else ("NO_TRANSIT_MATCH" if candidate_serial else "NO_WINDOW")
            ),
            "transit_confirmed": final_transit_support,
            "double_transit": _step7_pkg.get("double_transit"),
            "transit_type": _step7_pkg.get("transit_type"),
            "transit_type_label": _step7_pkg.get("transit_type_label"),
            "chart_context": _step7_pkg.get("chart_context"),
            "jupiter_hit": _step7_pkg.get("jupiter_hit"),
            "saturn_hit": _step7_pkg.get("saturn_hit"),
            "detail": _step7_detail,
            "months": _step7_months,
            "by_month": _step7_by_month,
            "matched_count": len(matched_serial),
            "candidate_count": len(candidate_serial),
            "per_dasha_windows": per_dasha_step7,
        },
        "step8": {
            "name": "Final — late BCP + dasha + transit",
            "status": (
                "DONE" if step8_prediction.get("transit_confirmed")
                else ("PARTIAL" if step8_prediction.get("predicted_bcp_age") else "DONE")
            ),
            "risk_flags": risk_flags,
            "final_gate": final_gate,
            "verdict": verdict,
            "band": band,
            "primary_window": primary_window,
            "marriage_period": primary_window,
            **step8_prediction,
        },
    }

    return {
        # Required for LLM formatter
        "verdict": verdict,
        "band": band,
        "top_3_windows": top_3_serial,
        "risk_flags": risk_flags,
        "final_gate": final_gate,
        "risk_severity_score": final_gate.get("risk_score"),
        # Wider contract
        "primary_window": primary_window,
        "backup_window": backup_window,
        "key_trigger": key_trigger,
        "timing_audit": timing_audit,
        "step_audit": step_audit,
        "transit_chart_context": _transit_chart_ctx,
        "confluence_strength": confluence_strength,
        "factors": factors,
        # Significator pipeline (user spec Steps 1–5)
        "top_marriage_planets": ranked,
        "marriage_significators": ranked,
        "weighted_breakdown": weighted_breakdown,
        "kp_validation": spec.get("kp_details"),
        "kp_summary": kp_summary,
        "d1_seventh_lord": d1_7l,
        "natal_promise": natal_promise,
        "reasoning_summary": spec.get("reasoning_summary"),
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
        "marriage_age_context": marriage_age_ctx,
        "timing_appropriate": timing_appropriate,
        "chart_late_marriage": marriage_age_ctx.get("chart_late_marriage"),
        "delay_vs_late": marriage_age_ctx.get("delay_vs_late"),
        "life_status": marriage_age_ctx.get("life_status"),
        "late_urgent_scan": late_urgent_scan,
        "search_horizon_days": late_horizon_days if late_urgent_scan else None,
        "step0": step0,
        "step0a": step0a,
        "step0_tendency": step0.get("step0_tendency"),
        "dasha_scan_plan": dasha_scan,
        "final_transit_support": final_transit_support,
        "final_double_transit": final_double_transit,
        "final_transit_detail": final_transit.get("detail"),
        "bcp_marriage_ages": bcp_ctx,
        "bcp_timing_strategy": bcp_strategy,
        "timing_mode": bcp_strategy.get("timing_mode"),
        # Engine metadata
        "engine_version": "v3.6.0",
        "engine_arch": (
            "STEP0(early-late)→STEP0A(BCP)→D1/D9→KP→rank→STEP6(dasha)→STEP7(transit-on-final-only)→gate"),
        "kp_planet_scan": _kp_planet_scan_safe(kp, "marriage", filtered_set),
    }


def _kp_planet_scan_safe(kp, domain, survivors):
    try:
        from event_timing._shared.kp_significator_scan import compute_kp_planet_scan
        return compute_kp_planet_scan(kp, domain, set(survivors or []))
    except Exception:
        return {"domain": domain, "kp_available": False,
                 "planets": [], "deliverers": [], "missed_by_filter": []}


def _resolve_lagna_si_from_kundli(kundli: dict) -> Optional[int]:
    """Shared lagna resolution for full + fallback marriage timing paths."""
    asc = kundli.get("ascendant")
    lagna_si = _sign_idx(asc) if isinstance(asc, str) else None
    if lagna_si is None:
        for key in (
            "ascendantSignIndex", "ascendantSignIdx", "ascendant_sign_idx",
            "lagna_sign_idx", "lagnaSignIdx", "lagnaSign", "ascendant_sign",
            "ascendantSign",
        ):
            v = kundli.get(key)
            lagna_si = _sign_idx(v) if isinstance(v, str) else (
                v % 12 if isinstance(v, int) else None)
            if lagna_si is not None:
                break
    if lagna_si is None:
        for key in ("ascendantDeg", "ascendantLon", "ascendantLongitude", "lagnaLon"):
            v = kundli.get(key)
            if v is not None:
                try:
                    lagna_si = int(float(v) / 30.0) % 12
                    break
                except (TypeError, ValueError):
                    pass
    return lagna_si


def compute_timing_window_fallback(
    kundli: dict,
    intel: dict,
    kp: dict,
    birth: Optional[Any] = None,
) -> dict:
    """Step 0/0A only when full v2 pipeline fails (partial deploy / runtime error)."""
    if not isinstance(kundli, dict) or not kundli:
        return {}
    if not isinstance(kp, dict):
        kp = {}
    lagna_si = _resolve_lagna_si_from_kundli(kundli)
    if lagna_si is None:
        return {
            "verdict": "UNKNOWN", "band": "WEAK",
            "primary_window": None, "backup_window": None,
            "top_3_windows": [], "risk_flags": ["lagna sign unavailable"],
            "factors": ["FALLBACK lagna_si is None"],
            "engine_version": "v3.6.0-fallback",
            "step_audit": {},
        }

    from event_timing.marriage.kp_from_chart import resolve_kp

    kp = resolve_kp(kundli, kp, birth)

    is_female: Optional[bool] = None
    if isinstance(birth, dict):
        g = (birth.get("gender") or birth.get("sex") or "").lower()
        if g.startswith("f"):
            is_female = True
        elif g.startswith("m"):
            is_female = False

    _now_for_age = datetime.utcnow()
    user_age = _compute_age_at(birth, _now_for_age, kundli=kundli)
    age_band = _classify_age_band(user_age, is_female)
    min_practical_age = _min_practical_age(is_female)
    birth_dt = _extract_dob_dt(birth, kundli=kundli)
    if birth_dt is None and user_age is not None:
        birth_dt = _infer_birth_dt_from_age(int(user_age), _now_for_age)

    from event_timing.marriage.marriage_step0 import run_marriage_step0
    from event_timing.marriage.marriage_step0a import run_marriage_step0a

    step0 = run_marriage_step0(
        kundli, lagna_si, user_age=user_age, birth_dt=birth_dt,
        is_female=is_female, kp=kp, min_practical_age=min_practical_age,
        years_ahead=5,
    )
    marriage_age_ctx = step0.get("marriage_age_context") or {}
    step0_verdict = (step0.get("step0_tendency") or {}).get("verdict") or ""
    _combined_pace = (
        (step0.get("marriage_pace") or {}).get("combined") or {}
    ).get("combined_pace") or "NORMAL"
    step0a = run_marriage_step0a(
        kundli, lagna_si, combined_pace=_combined_pace,
        age_ctx=marriage_age_ctx, user_age=user_age, birth_dt=birth_dt,
        years_ahead=5, step0_verdict=step0_verdict,
        d1_pace=(step0.get("step0_tendency") or {}).get("d1_pace"),
        d9_pace=(step0.get("step0_tendency") or {}).get("d9_pace"),
    )
    bcp_ctx = step0a.get("bcp_marriage_ages") or {}
    bcp_strategy = step0a.get("bcp_timing_strategy") or {}
    dasha_scan = step0a.get("dasha_scan_plan") or {}
    focus_bcp_ages = dasha_scan.get("bcp_focus_ages") or []
    primary_ref_age = dasha_scan.get("primary_reference_age")

    factors: List[str] = [
        "FALLBACK: full marriage v2 pipeline unavailable — Step 0/0A only",
        step0.get("reasoning_summary", "")[:220],
        step0a.get("reasoning_summary", "")[:220],
    ]
    try:
        from event_timing.marriage.bcp_marriage_ages import bcp_linkage_admin_lines

        for _bcp_line in bcp_linkage_admin_lines(bcp_ctx):
            factors.append(_bcp_line)
    except Exception:
        pass

    primary_window: Optional[str] = None

    step_audit = {
        "step0": {
            "name": "Early/Late + age context",
            "status": "DONE",
            "result": step0.get("step0_tendency") or {},
            "user_age": user_age,
            "age_band": age_band,
            "timing_appropriate": bool(marriage_age_ctx.get("timing_appropriate", True)),
            "min_practical_age": min_practical_age,
        },
        "step0a": {
            "name": "BCP ages + dasha scan plan",
            "status": "DONE",
            "primary_reference_age": primary_ref_age,
            "timing_mode": (bcp_strategy or {}).get("timing_mode"),
            "next_activation_age": (bcp_ctx or {}).get("next_activation_age"),
            "late_urgent_scan": dasha_scan.get("late_urgent_scan"),
            "focus_ages": sorted(focus_bcp_ages) if isinstance(focus_bcp_ages, list) else [],
            "bcp_ages_next_years": list(dasha_scan.get("bcp_ages_next_years") or [])[:4],
            "d1_bcp_ages": (bcp_ctx or {}).get("d1_future_bcp_ages") or [],
            "d9_bcp_ages": (bcp_ctx or {}).get("d9_future_bcp_ages") or [],
            "d1_seventh_lord": (bcp_ctx or {}).get("seventh_lord"),
            "d9_seventh_lord": ((bcp_ctx or {}).get("d9_bcp") or {}).get("seventh_lord"),
            "d1_7l_placement_house": (bcp_ctx or {}).get("seventh_lord_house"),
            "d1_7l_aspect_houses": [
                h.get("house")
                for h in ((bcp_ctx or {}).get("aspect_houses") or [])
                if isinstance(h, dict) and isinstance(h.get("house"), int)
            ],
            "d9_7l_placement_house": ((bcp_ctx or {}).get("d9_bcp") or {}).get("seventh_lord_house"),
            "d9_7l_aspect_houses": [
                h.get("house")
                for h in (((bcp_ctx or {}).get("d9_bcp") or {}).get("aspect_houses") or [])
                if isinstance(h, dict) and isinstance(h.get("house"), int)
            ],
            "bcp_house_display": (bcp_ctx or {}).get("bcp_admin_display") or {},
            "priority_ages": (bcp_ctx or {}).get("priority_marriage_ages") or [],
            "future_priority_ages": (bcp_ctx or {}).get("future_priority_ages") or [],
            "entry_notes": dasha_scan.get("entry_notes") or [],
        },
    }
    step_audit = _merge_natal_step_audit(
        {"step_audit": step_audit}, kundli, lagna_si, kp, birth=birth,
    )["step_audit"]

    _step0_tendency = step0.get("step0_tendency") or {}
    _late_focus = step0a.get("late_bcp_focus") or {}
    _focus_pri = (
        _late_focus.get("primary_age")
        or primary_ref_age
        or dasha_scan.get("primary_reference_age")
    )
    s6 = step_audit.get("step6") if isinstance(step_audit.get("step6"), dict) else {}
    focus_set = set(dasha_scan.get("bcp_focus_ages") or [])
    matched_s6 = [
        w for w in (s6.get("selected_windows") or [])
        if isinstance(w, dict) and w.get("transit_confirmed")
    ]
    from event_timing.marriage.bcp_marriage_ages import (
        effective_bcp_pool_for_timing,
        rank_matched_windows_for_late_chart,
    )
    _merged_bcp = effective_bcp_pool_for_timing(
        bcp_ctx or {},
        d1_pace=_step0_tendency.get("d1_pace"),
        d9_pace=_step0_tendency.get("d9_pace"),
        user_age=user_age,
    )
    matched_s6 = rank_matched_windows_for_late_chart(
        matched_s6,
        marriage_pace=str(_combined_pace or _step0_tendency.get("combined_pace") or ""),
        d1_pace=_step0_tendency.get("d1_pace"),
        d9_pace=_step0_tendency.get("d9_pace"),
        user_age=user_age,
        birth_dt=birth_dt,
        focus_bcp_ages=focus_set,
        merged_bcp_pool=_merged_bcp,
        primary_ref_age=_focus_pri if isinstance(_focus_pri, int) else None,
    )
    if matched_s6:
        primary_window = (
            matched_s6[0].get("window")
            if not matched_s6[0].get("transit_by_month")
            else None
        )
    elif isinstance(_focus_pri, int) and birth_dt is not None:
        try:
            primary_window = birth_dt.replace(
                year=birth_dt.year + int(_focus_pri),
            ).strftime("%B %Y")
        except (ValueError, OverflowError):
            primary_window = f"around age {_focus_pri}"
    elif isinstance(_focus_pri, int):
        primary_window = f"around age {_focus_pri}"

    ranked_fb = (step_audit.get("step5") or {}).get("ranked_top") or []
    step8_prediction = _build_step8_final_prediction(
        step0_tendency=_step0_tendency,
        d1_bcp_ages=list((bcp_ctx or {}).get("d1_future_bcp_ages") or []),
        d9_bcp_ages=list((bcp_ctx or {}).get("d9_future_bcp_ages") or []),
        ranked=ranked_fb,
        matched_windows=matched_s6,
        user_age=user_age,
        primary_ref_age=_focus_pri if isinstance(_focus_pri, int) else None,
        focus_bcp_ages=focus_set,
        primary_window=primary_window,
        key_trigger=None,
        birth_dt=birth_dt,
        step7_by_month=(
            (step_audit.get("step7") or {}).get("by_month")
            if isinstance(step_audit.get("step7"), dict)
            else None
        ),
    )
    primary_window, backup_window = apply_marriage_bcp_primary_windows(
        step8_prediction,
        birth_dt=birth_dt,
        dasha_window=step8_prediction.get("dasha_transit_month"),
        current_backup=None,
    )
    step_audit["step8"] = {
        "name": "Final — late BCP + dasha + transit",
        "status": "DONE" if step8_prediction.get("transit_confirmed") else "PARTIAL",
        "risk_flags": ["fallback_step0_only"],
        "verdict": step0_verdict or "UNKNOWN",
        "band": "MEDIUM" if step0_verdict in ("DELAYED", "LATE") else "WEAK",
        "primary_window": primary_window,
        "marriage_period": primary_window,
        **step8_prediction,
    }

    factors.append(
        f"BCP plan: mode={bcp_strategy.get('timing_mode')} "
        f"primary_age={_focus_pri} "
        f"focus={sorted(focus_set) if focus_set else focus_bcp_ages} "
        f"late_urgent={dasha_scan.get('late_urgent_scan')}"
    )
    if step8_prediction.get("final_prediction"):
        factors.append(f"STEP8: {step8_prediction['final_prediction']}")

    verdict = step0_verdict or "UNKNOWN"
    band = "MEDIUM" if verdict in ("DELAYED", "LATE") else "WEAK"

    key_trigger = None
    _pd8 = step8_prediction.get("primary_dasha") or {}
    if _pd8.get("md") and _pd8.get("ad") and _pd8.get("pd"):
        key_trigger = f"{_pd8['md']} MD · {_pd8['ad']} AD · {_pd8['pd']} PD"

    return {
        "verdict": verdict,
        "band": band,
        "primary_window": primary_window,
        "backup_window": backup_window,
        "key_trigger": key_trigger,
        "top_3_windows": matched_s6 or (s6.get("selected_windows") or []),
        "risk_flags": ["fallback_step0_only"],
        "factors": factors,
        "step_audit": step_audit,
        "step0": step0,
        "step0a": step0a,
        "step0_tendency": step0.get("step0_tendency"),
        "user_age": user_age,
        "bcp_marriage_ages": bcp_ctx,
        "dasha_scan_plan": dasha_scan,
        "engine_version": "v3.6.0-fallback",
        "engine_arch": "FALLBACK(STEP0→STEP0A)",
    }
