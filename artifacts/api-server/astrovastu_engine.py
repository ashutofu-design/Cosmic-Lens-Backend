"""
Cosmic AstroVastu Drishti Engine — Personalization Layer
=========================================================
Wraps the kundli_engine output and produces a `kundli_context` block that
the AstroVastu prompt + scoring logic can consume.

Responsibilities (Sprint 1 scope):
  - Detect weak / strong planets (item 7)
  - Detect Sade-Sati transit (item 8)
  - Compute Atmakaraka → Ishta Devata (item 9)
  - Profile completeness checker (item 10)
  - Conflict resolution tie-breakers (item 12)
  - Personalized severity multiplier (item 13)
  - Build complete `kundli_context` block for prompts
  - Branding constants (item 15)

This module is pure logic — no Flask, no LLM. Safe to unit-test in isolation.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from astrovastu_rules import (
    ENGINE_NAME,
    ENGINE_VERSION,
    BRANDING_LINE,
    LAGNA_LORD,
    SIGN_LORD,
    PLANET_DIRECTION,
    LAGNA_DIRECTION_MAP,
    RASHI_BEDHEAD_MAP,
    DASHA_ACTIVE_DIRECTION,
    ISHTA_DEVATA_MAP,
    PLANET_HOUSE_STRESS,
    YANTRA_PRESCRIPTION,
    YOGA_COLOR_OVERRIDE,
    GENERIC_ROOM_IDEAL,
    get_lagna_directions,
    get_rashi_bedhead,
    get_nakshatra_door,
    get_dasha_active_direction,
    get_ishta_devata_for_planet,
    get_yantra_for_planet,
    get_color_for_lagna,
    get_planet_direction,
    get_generic_room_rule,
    heading_to_direction,
)


# ─────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Planet exaltation / debilitation signs (classical — BPHS Ch.3)
EXALTATION_SIGN: Dict[str, str] = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}
DEBILITATION_SIGN: Dict[str, str] = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}

# Own signs (mool trikona / swakshetra simplified)
OWN_SIGN: Dict[str, List[str]] = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}

# Combust orb (in degrees) — planet within this distance from Sun is combust
COMBUST_ORB: Dict[str, float] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
}

# Kendra houses (angular — strongest)
KENDRA_HOUSES = [1, 4, 7, 10]
# Dusthana houses (6, 8, 12 — weakest)
DUSTHANA_HOUSES = [6, 8, 12]


# ─────────────────────────────────────────────────────────────────────────
# Item 7 — Weak / strong planet detector
# ─────────────────────────────────────────────────────────────────────────
def _planet_by_name(planets: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for p in planets:
        if p.get("name") == name:
            return p
    return None


def is_planet_combust(planet: Dict[str, Any], sun: Dict[str, Any]) -> bool:
    name = planet.get("name")
    if name not in COMBUST_ORB:
        return False
    p_lon = planet.get("longitude", 0.0)
    s_lon = sun.get("longitude", 0.0)
    diff = min((p_lon - s_lon) % 360, (s_lon - p_lon) % 360)
    return diff < COMBUST_ORB[name]


def planet_strength(planet: Dict[str, Any], sun: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a dict describing the planet's natal strength signals.
    Score: -2 (very weak) → +2 (very strong)
    """
    name = planet.get("name", "")
    sign = planet.get("sign", "")
    house = planet.get("house", 0)

    score = 0
    reasons: List[str] = []

    if EXALTATION_SIGN.get(name) == sign:
        score += 2
        reasons.append("exalted")
    if DEBILITATION_SIGN.get(name) == sign:
        score -= 2
        reasons.append("debilitated")
    if sign in OWN_SIGN.get(name, []):
        score += 1
        reasons.append("own_sign")
    if house in KENDRA_HOUSES:
        score += 1
        reasons.append("kendra")
    if house in DUSTHANA_HOUSES:
        score -= 1
        reasons.append("dusthana")
    if name not in ("Sun", "Rahu", "Ketu") and is_planet_combust(planet, sun):
        score -= 1
        reasons.append("combust")

    if score >= 2:
        verdict = "strong"
    elif score <= -1:
        verdict = "weak"
    else:
        verdict = "average"

    return {
        "name":    name,
        "sign":    sign,
        "house":   house,
        "score":   score,
        "verdict": verdict,
        "reasons": reasons,
    }


def weak_strong_summary(planets: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Return weak / strong planet name lists (item 7)."""
    sun = _planet_by_name(planets, "Sun") or {"longitude": 0.0}
    weak:    List[str] = []
    strong:  List[str] = []
    average: List[str] = []
    for p in planets:
        if p.get("name") in ("Rahu", "Ketu"):
            continue
        s = planet_strength(p, sun)
        if s["verdict"] == "weak":
            weak.append(p["name"])
        elif s["verdict"] == "strong":
            strong.append(p["name"])
        else:
            average.append(p["name"])
    return {"weak": weak, "strong": strong, "average": average}


# ─────────────────────────────────────────────────────────────────────────
# Item 8 — Sade-Sati detector (transit Saturn vs natal Moon)
# ─────────────────────────────────────────────────────────────────────────
def _current_saturn_sidereal_lon(asof: Optional[date] = None) -> float:
    """Current sidereal Saturn longitude using Lahiri ayanamsa."""
    if asof is None:
        asof = datetime.utcnow().date()
    # Compute JD at noon UT of the given date — adequate for sign-level transit
    jd = swe.julday(asof.year, asof.month, asof.day, 12.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    res, _ = swe.calc_ut(jd, swe.SATURN, flags)
    return res[0] % 360


def is_sade_sati_active(natal_moon_sign: str, asof: Optional[date] = None) -> Dict[str, Any]:
    """
    Sade-Sati: Saturn transiting 12th, 1st, or 2nd from natal Moon sign.
    Returns: { active: bool, phase: str, saturn_sign: str }
    """
    if natal_moon_sign not in SIGNS:
        return {"active": False, "phase": None, "saturn_sign": None}

    saturn_lon = _current_saturn_sidereal_lon(asof)
    saturn_sign_idx = int(saturn_lon // 30) % 12
    saturn_sign     = SIGNS[saturn_sign_idx]
    moon_idx        = SIGNS.index(natal_moon_sign)
    diff = (saturn_sign_idx - moon_idx) % 12   # 0=same, 11=12th from moon

    phase = None
    active = False
    if diff == 11:
        phase, active = "rising (12th from Moon)", True
    elif diff == 0:
        phase, active = "peak (over Moon)", True
    elif diff == 1:
        phase, active = "setting (2nd from Moon)", True

    return {"active": active, "phase": phase, "saturn_sign": saturn_sign}


# ─────────────────────────────────────────────────────────────────────────
# Item 9 — Atmakaraka → Ishta Devata (BPHS Ch.32 — Karakamsa method)
# ─────────────────────────────────────────────────────────────────────────
def compute_atmakaraka(planets: List[Dict[str, Any]]) -> Optional[str]:
    """
    Atmakaraka = the planet (among 7 — Sun..Saturn, optionally Rahu) with the
    highest degree within its own sign (i.e., longitude % 30).
    Classical Jaimini convention: 7 chara karakas. We exclude Ketu.

    Rahu is retrograde — Jaimini reverses its degree (30 − deg). At sign-boundary
    (deg == 0) we clamp via modulo to keep the value in [0, 30).
    """
    candidates = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]
    best: Optional[Tuple[str, float]] = None
    for name in candidates:
        p = _planet_by_name(planets, name)
        if not p:
            continue
        lon = p.get("longitude", 0.0)
        if name == "Rahu":
            deg_in_sign = (-lon) % 30.0     # = 30 − (lon%30) when lon%30>0; = 0 at boundary
        else:
            deg_in_sign = lon % 30.0
        if best is None or deg_in_sign > best[1]:
            best = (name, deg_in_sign)
    return best[0] if best else None


def derive_ishta_devata(
    planets: List[Dict[str, Any]],
    d9_chart: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ishta Devata derivation (BPHS Ch.32):
      1. Find Atmakaraka.
      2. Find Karakamsa = Atmakaraka's sign in the Navamsa (D9) chart.
      3. The deity ruling the planet placed in the 12th house from Karakamsa
         is the Ishta Devata. If empty, fall back to the lord of the 12th
         from Karakamsa.
      4. If no D9 available, use Atmakaraka's own deity mapping.
    """
    ak = compute_atmakaraka(planets)
    if not ak:
        return {"atmakaraka": None, "ishta_devata": None, "method": "none"}

    if not d9_chart or "planets" not in d9_chart:
        info = get_ishta_devata_for_planet(ak) or {}
        return {
            "atmakaraka":   ak,
            "ishta_devata": info.get("deity"),
            "direction":    info.get("direction"),
            "facing":       info.get("facing"),
            "method":       "fallback_from_atmakaraka",
            "vastu_ref":    info.get("vastu_ref"),
            "jyotish_ref": info.get("jyotish_ref"),
        }

    # 1. Find AK's sign in D9
    ak_d9 = next((p for p in d9_chart["planets"] if p.get("name") == ak), None)
    if not ak_d9:
        info = get_ishta_devata_for_planet(ak) or {}
        return {
            "atmakaraka":   ak,
            "ishta_devata": info.get("deity"),
            "direction":    info.get("direction"),
            "facing":       info.get("facing"),
            "method":       "fallback_d9_missing_ak",
        }

    karakamsa_sign_idx = ak_d9.get("signIndex", 0)
    twelfth_sign_idx   = (karakamsa_sign_idx - 1) % 12   # 12th from karakamsa
    twelfth_sign       = SIGNS[twelfth_sign_idx]

    # 2. Find any planet placed in that sign in D9
    occupants = [p for p in d9_chart["planets"]
                 if p.get("signIndex") == twelfth_sign_idx]

    if occupants:
        deity_planet = occupants[0]["name"]
        method       = "d9_12th_occupant"
    else:
        # Fallback: lord of 12th from karakamsa
        deity_planet = SIGN_LORD.get(twelfth_sign, ak)
        method       = "d9_12th_lord"

    info = get_ishta_devata_for_planet(deity_planet) or {}
    return {
        "atmakaraka":     ak,
        "karakamsa_sign": SIGNS[karakamsa_sign_idx],
        "twelfth_sign":   twelfth_sign,
        "deity_planet":   deity_planet,
        "ishta_devata":   info.get("deity"),
        "direction":      info.get("direction"),
        "facing":         info.get("facing"),
        "method":         method,
        "vastu_ref":      info.get("vastu_ref"),
        "jyotish_ref":   info.get("jyotish_ref"),
    }


# ─────────────────────────────────────────────────────────────────────────
# Item 10 — Profile completeness checker
# ─────────────────────────────────────────────────────────────────────────
REQUIRED_PROFILE_FIELDS = ["day", "month", "year", "hour", "minute", "ampm",
                           "lat", "lon", "tz", "place"]


def is_profile_complete(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns: { complete: bool, missing: [field_names], message: str }
    AstroVastu PRO requires birth date + time + place — without this we cannot
    compute Lagna / Mahadasha and personalization is impossible.
    """
    if not profile:
        return {
            "complete": False,
            "missing":  REQUIRED_PROFILE_FIELDS,
            "message":  "Janam vivaran (date, time, place) required for AstroVastu",
        }
    missing = [f for f in REQUIRED_PROFILE_FIELDS
               if profile.get(f) is None or profile.get(f) == ""]
    if missing:
        return {
            "complete": False,
            "missing":  missing,
            "message":  f"Profile mein ye field missing hai: {', '.join(missing)}",
        }
    return {"complete": True, "missing": [], "message": "Profile complete"}


# ─────────────────────────────────────────────────────────────────────────
# Item 12 — Conflict resolution tie-breakers
# ─────────────────────────────────────────────────────────────────────────
def apply_tie_breakers(
    room_type: str,
    direction: str,
    kundli_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Decide whether the user's room/direction combination is "Ideal",
    "Acceptable", "Adjustment Needed", or "Avoid" — applying the 7 tie-breaker
    rules from CATEGORY 10 in priority order.

    Returns:
      {
        verdict: "Ideal"|"Acceptable"|"Adjustment Needed"|"Avoid",
        generic_verdict: same scale (no personalization),
        applied_tie_breakers: [{id, rule, effect}],
        personalization_reason: human-readable explanation,
        classical_refs: [{type, source}]
      }
    """
    refs: List[Dict[str, str]] = []
    applied: List[Dict[str, str]] = []

    # Step 1 — Generic verdict from room/direction lookup
    rule = get_generic_room_rule(room_type) or {}
    generic_verdict = "Acceptable"
    if direction in (rule.get("ideal") or []):
        generic_verdict = "Ideal"
    elif direction in (rule.get("acceptable") or []):
        generic_verdict = "Acceptable"
    elif direction in (rule.get("avoid") or []):
        generic_verdict = "Avoid"
    else:
        generic_verdict = "Adjustment Needed"

    if rule.get("vastu_ref"):
        refs.append({"type": "vastu", "source": rule["vastu_ref"]})

    verdict       = generic_verdict
    personal_note = ""

    lagna       = kundli_context.get("lagna")
    rashi       = kundli_context.get("rashi")
    nakshatra   = kundli_context.get("nakshatra")
    mahadasha   = kundli_context.get("current_mahadasha")
    sade_sati   = kundli_context.get("sade_sati", {}).get("active", False)
    yogas       = kundli_context.get("special_yogas", []) or []

    # ── TB1: Lagna lord overrides generic direction ──
    lag_info = get_lagna_directions(lagna) if lagna else None
    if lag_info:
        if direction in lag_info["favourable"]:
            if generic_verdict in ("Avoid", "Adjustment Needed"):
                verdict = "Acceptable"
                applied.append({
                    "id": "TB1",
                    "rule": "Lagna lord favours this direction",
                    "effect": f"Generic '{generic_verdict}' upgraded to 'Acceptable' for {lagna} Lagna",
                })
            personal_note = (
                f"Aapki {lagna} Lagna ({lag_info['element']} element) ke liye "
                f"{direction} favourable direction hai."
            )
        elif direction in lag_info["avoid"]:
            if verdict in ("Ideal", "Acceptable"):
                verdict = "Adjustment Needed"
                applied.append({
                    "id": "TB1",
                    "rule": "Lagna lord avoids this direction",
                    "effect": f"Generic '{generic_verdict}' downgraded — {lagna} Lagna ke liye {direction} avoid",
                })
        refs.append({"type": "vastu",   "source": lag_info["vastu_ref"]})
        refs.append({"type": "jyotish", "source": lag_info["jyotish_ref"]})

    # ── TB2: Current Mahadasha overlay ──
    dasha_info = get_dasha_active_direction(mahadasha) if mahadasha else None
    if dasha_info and direction == dasha_info["direction"]:
        if verdict == "Avoid":
            verdict = "Adjustment Needed"   # dasha helps mitigate
        applied.append({
            "id": "TB2",
            "rule": f"Current {mahadasha} Mahadasha activates this direction",
            "effect": f"{direction} is the active dasha direction — extra attention needed",
        })
        refs.append({"type": "jyotish", "source": dasha_info["jyotish_ref"]})

    # ── TB3: Sade-Sati hard override for Saturn directions (W / SW) ──
    # During the 7.5-yr Sade-Sati period, Saturn's directions cannot be "Ideal"
    # — they always require active maintenance. Per spec: TB3 overrides everything.
    if sade_sati and direction in ("West", "South-West"):
        # Force verdict to at most "Adjustment Needed"
        if verdict in ("Ideal", "Acceptable"):
            verdict = "Adjustment Needed"
        applied.append({
            "id":     "TB3",
            "rule":   "Sade-Sati active — Saturn's direction requires constant care",
            "effect": f"{direction} cannot be 'Ideal' during Sade-Sati; verdict capped at 'Adjustment Needed'",
        })

    # ── TB4: Manglik couple-room rule ──
    if "manglik" in [y.lower() for y in yogas] and room_type == "bedroom":
        applied.append({
            "id": "TB4",
            "rule": "Manglik dosha — couple's bedroom uses Mars-friendly direction",
            "effect": "Avoid pure red walls; soft pink okay; South facing acceptable",
        })

    # ── TB5: Kal Sarpa cleanliness (canonical key: 'kaal_sarp' from dosh_engine) ──
    if "kaal_sarp" in [y.lower() for y in yogas]:
        if direction in ("South-West", "North-East"):
            applied.append({
                "id": "TB5",
                "rule": "Kal Sarpa Yoga — extra SW + NE cleanliness required",
                "effect": "Heightened diligence in this direction",
            })

    # ── TB6: Mool Nakshatra pooja rule ──
    if nakshatra == "Mula" and room_type == "pooja":
        applied.append({
            "id": "TB6",
            "rule": "Mool Nakshatra — special NE pooja mandatory",
            "effect": "Pooja in NE corner with daily lamp",
        })

    # ── TB7: Atmakaraka direction priority for spiritual rooms ──
    ak = kundli_context.get("atmakaraka")
    if ak and room_type in ("pooja", "study"):
        ak_dir = get_planet_direction(ak)
        if ak_dir == direction:
            applied.append({
                "id": "TB7",
                "rule": "Atmakaraka direction matches — soul-level alignment",
                "effect": f"Strongly recommended for {room_type}",
            })
            if verdict == "Adjustment Needed":
                verdict = "Acceptable"

    return {
        "verdict":                 verdict,
        "generic_verdict":         generic_verdict,
        "applied_tie_breakers":    applied,
        "personalization_reason":  personal_note,
        "classical_refs":          refs,
    }


# ─────────────────────────────────────────────────────────────────────────
# Item 13 — Personalized severity multiplier
# ─────────────────────────────────────────────────────────────────────────
SEVERITY_BASE: Dict[str, float] = {"minor": 3.0, "moderate": 6.0, "major": 12.0}
SEVERITY_FROM_SCORE: List[Tuple[float, str]] = [
    (3.5,  "major"),     # multiplier ≥ 3.5 of moderate → major
    (1.5,  "moderate"),
    (0.0,  "minor"),
]


def personalized_severity_multiplier(
    direction: str,
    kundli_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Returns a multiplier (float) and the reasons that contributed.
    Multiplier range: 0.3 (blessing for you) → 3.0 (extra critical).
    """
    multiplier = 1.0
    reasons: List[str] = []

    lagna     = kundli_context.get("lagna")
    rashi     = kundli_context.get("rashi")
    nakshatra = kundli_context.get("nakshatra")
    mahadasha = kundli_context.get("current_mahadasha")
    weak_planets   = set(kundli_context.get("weak_planets", []))
    yogas          = [y.lower() for y in (kundli_context.get("special_yogas") or [])]

    # 1. Lagna favourable direction → 0.6x (blessing)
    lag_info = get_lagna_directions(lagna) if lagna else None
    if lag_info:
        if direction in lag_info["favourable"]:
            multiplier *= 0.6
            reasons.append(f"{lagna} Lagna favours {direction} (×0.6)")
        elif direction in lag_info["avoid"]:
            multiplier *= 1.6
            reasons.append(f"{lagna} Lagna avoids {direction} (×1.6)")

    # 2. Current Mahadasha direction → 1.5x severity
    dasha_info = get_dasha_active_direction(mahadasha) if mahadasha else None
    if dasha_info and direction == dasha_info["direction"]:
        multiplier *= 1.5
        reasons.append(f"{mahadasha} Mahadasha active in {direction} (×1.5)")

    # 3. Weak planet's direction → 1.4x
    for wp in weak_planets:
        wd = get_planet_direction(wp)
        if wd == direction:
            multiplier *= 1.4
            reasons.append(f"Weak {wp}'s direction ({direction}) more vulnerable (×1.4)")
            break  # cap at one weak planet bonus

    # 4. Sade-Sati + West/SW = 2.0x
    if kundli_context.get("sade_sati", {}).get("active") and direction in ("West", "South-West"):
        multiplier *= 2.0
        reasons.append("Sade-Sati active + Saturn direction (×2.0)")

    # 5. Manglik + South = 1.3x
    if "manglik" in yogas and direction == "South":
        multiplier *= 1.3
        reasons.append("Manglik + South (×1.3)")

    # 6. Kal Sarpa + SW/NE = 1.4x
    if "kal_sarpa" in yogas and direction in ("South-West", "North-East"):
        multiplier *= 1.4
        reasons.append("Kal Sarpa Yoga + nodal direction (×1.4)")

    # Clamp to [0.3, 3.0]
    multiplier = max(0.3, min(3.0, multiplier))
    return {"multiplier": round(multiplier, 2), "reasons": reasons}


def adjusted_severity_label(
    generic_severity: str,
    multiplier: float,
) -> str:
    """Map (generic_severity × multiplier) → personalized severity label."""
    base   = SEVERITY_BASE.get(generic_severity, 6.0)
    scaled = base * multiplier / 6.0   # normalize against moderate
    for threshold, label in SEVERITY_FROM_SCORE:
        if scaled >= threshold:
            return label
    return "minor"


# ─────────────────────────────────────────────────────────────────────────
# Build complete kundli_context block (for prompts + UI)
# ─────────────────────────────────────────────────────────────────────────
def build_kundli_context(kundli: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take a kundli dict (from kundli_engine.calculate_kundli) and produce the
    `kundli_context` block consumed by the AstroVastu prompt + scoring.

    Output keys:
      lagna, lagna_lord, rashi, rashi_lord, nakshatra,
      current_mahadasha, mahadasha_remaining_years,
      current_antardasha,
      weak_planets, strong_planets,
      sade_sati: {active, phase, saturn_sign},
      special_yogas: [...],
      atmakaraka, ishta_devata: {deity, direction, facing},
      active_directions_today: [direction list]
    """
    lagna = kundli.get("ascendant") or kundli.get("lagna")
    rashi = kundli.get("moonSign")  or kundli.get("rashi")
    nakshatra = kundli.get("nakshatra")
    planets   = kundli.get("planets") or []
    d9        = (kundli.get("divisionalCharts") or {}).get("D9")

    cur = kundli.get("currentDasha") or {}
    maha  = cur.get("maha")
    antar = cur.get("antar")

    # Mahadasha remaining years
    maha_remaining_years = None
    for d in (kundli.get("dashas") or []):
        if d.get("planet") == maha:
            try:
                end = datetime.strptime(d["endDate"], "%Y-%m-%d").date()
                today = datetime.utcnow().date()
                days = (end - today).days
                maha_remaining_years = round(days / 365.25, 2)
            except Exception:
                pass
            break

    ws = weak_strong_summary(planets)
    sade = is_sade_sati_active(rashi) if rashi else {"active": False, "phase": None}
    ishta = derive_ishta_devata(planets, d9)

    # Special yogas — pull from dosh_engine if available, else empty
    yogas: List[str] = []
    try:
        from dosh_engine import analyze_doshas
        dosh_result = analyze_doshas(planets, nakshatra or "")
        for d in dosh_result.get("dosh_list", []):
            if d.get("status") == "Active" and d.get("key") in ("manglik", "kaal_sarp"):
                yogas.append(d["key"])
    except Exception:
        pass

    # Active directions today = current Mahadasha direction (+ Antardasha if different)
    active_dirs: List[str] = []
    md_info = get_dasha_active_direction(maha) if maha else None
    ad_info = get_dasha_active_direction(antar) if antar else None
    if md_info: active_dirs.append(md_info["direction"])
    if ad_info and ad_info["direction"] not in active_dirs:
        active_dirs.append(ad_info["direction"])

    return {
        "lagna":                     lagna,
        "lagna_lord":                LAGNA_LORD.get(lagna),
        "rashi":                     rashi,
        "rashi_lord":                LAGNA_LORD.get(rashi),
        "nakshatra":                 nakshatra,
        "current_mahadasha":         maha,
        "mahadasha_remaining_years": maha_remaining_years,
        "current_antardasha":        antar,
        "weak_planets":              ws["weak"],
        "strong_planets":            ws["strong"],
        "sade_sati":                 sade,
        "special_yogas":             yogas,
        "atmakaraka":                ishta.get("atmakaraka"),
        "ishta_devata":              {
            "deity":     ishta.get("ishta_devata"),
            "direction": ishta.get("direction"),
            "facing":    ishta.get("facing"),
            "method":    ishta.get("method"),
        },
        "active_directions_today":   active_dirs,
        "engine":                    f"{ENGINE_NAME} {ENGINE_VERSION}",
        "branding":                  BRANDING_LINE,
    }


# ─────────────────────────────────────────────────────────────────────────
# Self-check entry point
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Smoke test with synthetic kundli
    sample = {
        "ascendant": "Cancer",
        "moonSign":  "Cancer",
        "nakshatra": "Pushya",
        "planets": [
            {"name": "Sun",     "sign": "Aries",     "house": 10, "longitude":  15.0},
            {"name": "Moon",    "sign": "Cancer",    "house": 1,  "longitude": 105.0},
            {"name": "Mars",    "sign": "Capricorn", "house": 7,  "longitude": 285.0},
            {"name": "Mercury", "sign": "Pisces",    "house": 9,  "longitude": 350.0},
            {"name": "Jupiter", "sign": "Cancer",    "house": 1,  "longitude": 110.0},
            {"name": "Venus",   "sign": "Pisces",    "house": 9,  "longitude": 355.0},
            {"name": "Saturn",  "sign": "Libra",     "house": 4,  "longitude": 195.0},
            {"name": "Rahu",    "sign": "Gemini",    "house": 12, "longitude":  75.0},
            {"name": "Ketu",    "sign": "Sagittarius","house": 6, "longitude": 255.0},
        ],
        "currentDasha": {"maha": "Moon", "antar": "Saturn"},
        "dashas": [{"planet": "Moon", "endDate": "2030-03-14"}],
        "divisionalCharts": {"D9": None},
    }
    ctx = build_kundli_context(sample)
    import json
    print(json.dumps(ctx, indent=2, default=str))
    print("\nVerdict for kitchen in West:")
    v = apply_tie_breakers("kitchen", "West", ctx)
    print(json.dumps(v, indent=2))
    print("\nMultiplier for SW dosh:")
    m = personalized_severity_multiplier("South-West", ctx)
    print(json.dumps(m, indent=2))
