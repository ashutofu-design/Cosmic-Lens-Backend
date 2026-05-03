#!/usr/bin/env python3
"""
KP (Krishnamurti Paddhati) Astrology Engine
- Placidus house system (KP standard)
- Sidereal zodiac with Lahiri ayanamsha
- Computes: Cusps (SL/NL/SB/SS), Planet positions, Significations
"""

import swisseph as swe
from datetime import datetime, timedelta

# ── Constants ──────────────────────────────────────────────────────────────────

VIMSHOTTARI_SEQ = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury"
]
VIMSHOTTARI_YRS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}
TOTAL_YRS = 120.0
NAKSHA_EXTENT = 360.0 / 27.0  # 13.33333...° per nakshatra

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
SIGN_SHORT = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
               "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

# One lord per sign (Aries=0 … Pisces=11)
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

ALL_PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu"
]

# Rahu and Ketu do not own signs in KP
NO_OWNERSHIP = {"Rahu", "Ketu"}


# ── Core sub-lord calculator ───────────────────────────────────────────────────

def get_kp_lords(longitude):
    """
    For a given sidereal longitude, return:
      (sign_lord, nakshatra_lord, sub_lord, sub_sub_lord)

    Algorithm:
      1. SL  = lord of the sign (every 30°)
      2. NL  = lord of the nakshatra (every 13°20'); nakshatra starts
               its sub-sequence with its own lord
      3. SB  = lord within the nakshatra subdivision (proportional to
               Vimshottari years, starting from NL)
      4. SS  = lord within the sub-subdivision (same proportionality
               applied inside the SB span)
    """
    longitude = longitude % 360.0

    # ── Sign Lord ──────────────────────────────────────────────────────────────
    sign_idx = int(longitude / 30) % 12
    sl = SIGN_LORDS[sign_idx]

    # ── Nakshatra Lord ─────────────────────────────────────────────────────────
    naksha_idx = int(longitude / NAKSHA_EXTENT) % 27
    nl_seq_start = naksha_idx % 9          # position in VIMSHOTTARI_SEQ
    nl = VIMSHOTTARI_SEQ[nl_seq_start]

    # Position inside the nakshatra (0 … NAKSHA_EXTENT)
    pos_in_naksha = longitude - (naksha_idx * NAKSHA_EXTENT)

    # ── Sub Lord ───────────────────────────────────────────────────────────────
    cum = 0.0
    sub_lord = nl
    sub_start = 0.0
    sub_span = NAKSHA_EXTENT   # fallback — whole nakshatra
    for i in range(9):
        planet = VIMSHOTTARI_SEQ[(nl_seq_start + i) % 9]
        span = (VIMSHOTTARI_YRS[planet] / TOTAL_YRS) * NAKSHA_EXTENT
        if pos_in_naksha < cum + span or i == 8:
            sub_lord = planet
            sub_start = cum
            sub_span = span
            break
        cum += span

    # ── Sub-Sub Lord ───────────────────────────────────────────────────────────
    pos_in_sub = pos_in_naksha - sub_start
    sb_seq_start = VIMSHOTTARI_SEQ.index(sub_lord)
    cum2 = 0.0
    sub_sub_lord = sub_lord
    for i in range(9):
        planet = VIMSHOTTARI_SEQ[(sb_seq_start + i) % 9]
        span2 = (VIMSHOTTARI_YRS[planet] / TOTAL_YRS) * sub_span
        if pos_in_sub < cum2 + span2 or i == 8:
            sub_sub_lord = planet
            break
        cum2 += span2

    return sl, nl, sub_lord, sub_sub_lord


# ── Helpers ────────────────────────────────────────────────────────────────────

def format_deg_sign(longitude):
    """'05°23' Ari' — degree + minute within sign + sign abbreviation."""
    longitude = longitude % 360.0
    sign_idx = int(longitude / 30) % 12
    deg_in_sign = longitude % 30
    d = int(deg_in_sign)
    m = int((deg_in_sign - d) * 60)
    return f"{d:02d}\u00b0{m:02d}' {SIGN_SHORT[sign_idx]}"


def get_kp_house(planet_lon, sidereal_cusps):
    """
    House number (1-12) for a planet given sidereal Placidus cusps.
    Planet is in house H if it falls in the arc cusp[H] → cusp[H+1].
    Handles 0°/360° wraparound.
    """
    planet_lon = planet_lon % 360.0
    for h in range(12):
        c1 = sidereal_cusps[h] % 360.0
        c2 = sidereal_cusps[(h + 1) % 12] % 360.0
        if c1 < c2:
            if c1 <= planet_lon < c2:
                return h + 1
        else:  # arc crosses 0°
            if planet_lon >= c1 or planet_lon < c2:
                return h + 1
    return 1


def get_owned_houses(planet_name, sidereal_cusps):
    """
    Houses owned by a planet = house numbers whose cusp falls in a sign
    lorded by that planet.  Rahu and Ketu own no signs.
    """
    if planet_name in NO_OWNERSHIP:
        return []
    owned = []
    for h in range(12):
        if SIGN_LORDS[int(sidereal_cusps[h] / 30) % 12] == planet_name:
            owned.append(h + 1)
    return sorted(set(owned))


# ── Main calculation ──────────────────────────────────────────────────────────

def calculate_kp(data):
    """
    Full KP calculation.

    Input keys (same schema as /api/kundli):
      day, month, year, hour, minute, ampm, lat, lon, tz

    Returns:
      cusps          — list of 12 cusp dicts (house, degree, sl, nl, sb, ss)
      planets        — list of 9 planet dicts (name, degree, house, nl, sb, ss)
      significations — dict keyed by planet name
      ayanamsa       — float (Lahiri, applied)
    """
    # ── UTC conversion ─────────────────────────────────────────────────────────
    day    = data["day"]
    month  = data["month"]
    year   = data["year"]
    hour   = data["hour"]
    minute = data["minute"]
    ampm   = data["ampm"]
    lat    = data["lat"]
    lon    = data["lon"]
    tz     = data["tz"]

    hour24 = hour
    if ampm == "PM" and hour != 12:
        hour24 = hour + 12
    elif ampm == "AM" and hour == 12:
        hour24 = 0

    ut_decimal = hour24 + minute / 60.0 - tz
    ut_day, ut_month, ut_year = day, month, year

    if ut_decimal < 0:
        ut_decimal += 24
        prev = datetime(year, month, day) - timedelta(days=1)
        ut_day, ut_month, ut_year = prev.day, prev.month, prev.year
    elif ut_decimal >= 24:
        ut_decimal -= 24
        nxt = datetime(year, month, day) + timedelta(days=1)
        ut_day, ut_month, ut_year = nxt.day, nxt.month, nxt.year

    # ── Swiss Ephemeris setup ──────────────────────────────────────────────────
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(ut_year, ut_month, ut_day, ut_decimal)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    # ── Placidus cusps (tropical) → sidereal ──────────────────────────────────
    cusps_trop, _ = swe.houses(jd, lat, lon, b'P')
    sidereal_cusps = [(c - ayanamsa + 360) % 360 for c in cusps_trop[:12]]

    # ── Planet longitudes (sidereal) ──────────────────────────────────────────
    flags_sid = swe.FLG_SIDEREAL | swe.FLG_SPEED
    planet_lons = {}

    for pname, pid in PLANET_IDS.items():
        result, _ = swe.calc_ut(jd, pid, flags_sid)
        planet_lons[pname] = result[0] % 360

    rahu_result, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags_sid)
    rahu_lon = rahu_result[0] % 360
    planet_lons["Rahu"] = rahu_lon
    planet_lons["Ketu"] = (rahu_lon + 180) % 360

    # ── House placement for every planet ──────────────────────────────────────
    # planet_house_map: { planet_name: house_number }
    planet_house_map = {
        pname: get_kp_house(planet_lons[pname], sidereal_cusps)
        for pname in ALL_PLANETS
    }

    # ── Helper: combined houses for a lord (occupied + owned) ─────────────────
    # For Rahu/Ketu (NO_OWNERSHIP), only the house they physically occupy
    # is returned. No dispositor / conjunct / aspect inheritance — per user
    # spec, shadow planets signify only where they sit.
    def houses_for_lord(lord_name):
        h_occ = [planet_house_map[lord_name]] if lord_name in planet_house_map else []
        h_own = get_owned_houses(lord_name, sidereal_cusps)
        return sorted(set(h_occ + h_own))

    # ── Build cusps output ────────────────────────────────────────────────────
    cusps_out = []
    for h in range(12):
        cusp_lon = sidereal_cusps[h]
        sl, nl, sb, ss = get_kp_lords(cusp_lon)
        naksha_idx = int(cusp_lon / NAKSHA_EXTENT) % 27
        cusps_out.append({
            "house":     h + 1,
            "longitude": round(cusp_lon, 4),
            "degree":    format_deg_sign(cusp_lon),
            "sign":      SIGNS[int(cusp_lon / 30) % 12],
            "sl":        sl,
            "nl":        nl,
            "sb":        sb,
            "ss":        ss,
            "nakshatra": NAKSHATRAS[naksha_idx],
        })

    # ── Build planets output + significations ─────────────────────────────────
    planets_out = []
    significations_out = {}

    for pname in ALL_PLANETS:
        plon = planet_lons[pname]
        sl, nl, sb, ss = get_kp_lords(plon)
        naksha_idx = int(plon / NAKSHA_EXTENT) % 27
        house = planet_house_map[pname]
        owned = get_owned_houses(pname, sidereal_cusps)

        planets_out.append({
            "name":      pname,
            "longitude": round(plon, 4),
            "degree":    format_deg_sign(plon),
            "sign":      SIGNS[int(plon / 30) % 12],
            "nakshatra": NAKSHATRAS[naksha_idx],
            "house":     house,
            "sl":        sl,
            "nl":        nl,
            "sb":        sb,
            "ss":        ss,
        })

        # PL houses: occupied house + owned houses (sorted unique).
        # Rahu/Ketu own no signs → PL is just the occupation house.
        pl_houses = sorted(set([house] + owned))

        significations_out[pname] = {
            "nl_lord":  nl,
            "sb_lord":  sb,
            "ss_lord":  ss,
            "pl":       pl_houses,
            "sl":       houses_for_lord(nl),
            "sb_houses": houses_for_lord(sb),
            "ss_houses": houses_for_lord(ss),
        }

    return {
        "cusps":           cusps_out,
        "planets":         planets_out,
        "significations":  significations_out,
        "ayanamsa":        round(ayanamsa, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2.8.58 — KP cache reader (ADD-ONLY)
# Returns kundli["kp"] if present and well-formed; otherwise computes fresh
# via calculate_kp(birth). Lets downstream callers (locked_facts, kp_locked_facts,
# kundli_full_context, marriage engine) skip Swiss Ephemeris recompute on every
# request now that Phase 2.8.57 bakes "kp" into chart_data at compute + cache time.
# ─────────────────────────────────────────────────────────────────────────────
def get_or_compute_kp(kundli: dict | None, birth: dict | None) -> dict:
    """
    Return cached KP block from kundli["kp"] if present and well-formed,
    else compute fresh via calculate_kp(birth). Never raises — returns {}
    on hard failure so callers can degrade gracefully.

    Cache-validity contract (architect-tightened, Phase 2.8.58):
      - cusps: list of len 12
      - planets: list of len 9 (Sun..Ketu — full canonical set)
      - significations: non-empty dict (downstream KP filter rules need it)
    A partial cache (e.g. 12 cusps + 8 planets, or empty significations)
    is REJECTED so we recompute rather than silently feed downstream rules
    a half-built payload.

    Debug bypass: set env FORCE_KP_RECOMPUTE=1 to skip cache entirely
    (useful when investigating stale-data bugs or rebuilding chart_data
    rows manually).
    """
    try:
        import os as _os
        if _os.environ.get("FORCE_KP_RECOMPUTE") == "1":
            return calculate_kp(birth) or {} if isinstance(birth, dict) else {}

        if isinstance(kundli, dict):
            cached = kundli.get("kp")
            if (isinstance(cached, dict)
                    and isinstance(cached.get("cusps"), list)
                    and isinstance(cached.get("planets"), list)
                    and isinstance(cached.get("significations"), dict)
                    and len(cached["cusps"]) == 12
                    and len(cached["planets"]) == 9
                    and len(cached["significations"]) > 0):
                return cached
        if isinstance(birth, dict):
            return calculate_kp(birth) or {}
    except Exception as exc:  # noqa: BLE001
        print(f"[kp_engine.get_or_compute_kp] failed: {exc}")
    return {}
