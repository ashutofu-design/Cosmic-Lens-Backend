#!/usr/bin/env python3
"""
Kundli calculation engine using pyswisseph.
Reads JSON from stdin, writes JSON to stdout.
"""

import sys
import json
import math
import calendar
import swisseph as swe
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Set Lahiri ayanamsa once at module load — pyswisseph stores this as global C
# state.  Calling it once here means every subsequent swe.calc_ut / swe.houses
# call in this process uses consistent Lahiri values.
swe.set_sid_mode(swe.SIDM_LAHIRI)

# Bumped on any math/structure change to a kundli output. Used by the
# cache layer (cache_helpers.KundliCache) to invalidate stale rows.
KUNDLI_CALC_VERSION = 16

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_RULERS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury"
]

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

EXALT_SIGNS = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
    "Rahu": "Taurus", "Ketu": "Scorpio",
}

DEBIL_SIGNS = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
    "Rahu": "Scorpio", "Ketu": "Taurus",
}

OWN_SIGNS = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}

PLANET_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}

PLANET_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
CLASSICAL_DIGNITY_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
CHART_POWER_FOCUS = {
    "D1": "Overall life foundation, body, personality and visible strength",
    "D2": "Wealth, resources, food and family wealth",
    "D3": "Courage, siblings, initiative and vitality",
    "D4": "Home, property, fixed assets and inner contentment",
    "D7": "Children, progeny and creative continuation",
    "D9": "Marriage, dharma, spouse and deeper planet strength",
    "D10": "Career, profession, karma and public achievement",
    "D12": "Parents, lineage and inherited patterns",
    "D16": "Vehicles, comforts and luxuries",
    "D20": "Spirituality, sadhana and devotion",
    "D24": "Education, learning and higher knowledge",
    "D27": "Resilience, hidden strength and weakness",
    "D30": "Misfortune, hidden problems and suffering resistance",
    "D40": "Maternal lineage and auspicious patterns",
    "D45": "Paternal lineage and deep karmic inheritance",
    "D60": "Deep karma and root karmic signature",
}
DEFAULT_CHART_POWER_PROFILE = {
    "primary_houses": [1],
    "karakas": ["Jupiter"],
    "weights": {
        "lagnaLord": 20,
        "keyLords": 25,
        "karakas": 20,
        "dignity": 10,
        "placement": 10,
        "affliction": 15,
    },
}
CHART_POWER_PROFILES = {
    "D1": {
        "primary_houses": [1, 5, 9, 10],
        "karakas": ["Moon", "Sun", "Jupiter"],
        "weights": {
            "lagnaLord": 25,
            "keyLords": 15,
            "karakas": 15,
            "dignity": 15,
            "placement": 10,
            "affliction": 20,
        },
    },
    "D2": {"primary_houses": [2, 11], "karakas": ["Jupiter", "Venus"]},
    "D3": {"primary_houses": [3], "karakas": ["Mars", "Sun"]},
    "D4": {"primary_houses": [4], "karakas": ["Moon", "Mars", "Venus"]},
    "D7": {"primary_houses": [5], "karakas": ["Jupiter", "Sun"]},
    "D9": {"primary_houses": [1, 7, 9], "karakas": ["Venus", "Jupiter"]},
    "D10": {"primary_houses": [6, 10, 11], "karakas": ["Sun", "Saturn", "Mercury"]},
    "D12": {"primary_houses": [4, 9], "karakas": ["Sun", "Moon"]},
    "D16": {"primary_houses": [4], "karakas": ["Venus", "Moon"]},
    "D20": {"primary_houses": [5, 9, 12], "karakas": ["Jupiter", "Ketu"]},
    "D24": {"primary_houses": [4, 5, 9], "karakas": ["Mercury", "Jupiter"]},
    "D27": {"primary_houses": [1, 3, 6], "karakas": ["Mars", "Saturn"]},
    "D30": {"primary_houses": [6, 8, 12], "karakas": ["Saturn", "Mars", "Ketu"]},
    "D40": {"primary_houses": [4], "karakas": ["Moon", "Venus"]},
    "D45": {"primary_houses": [9], "karakas": ["Sun", "Jupiter"]},
    "D60": {"primary_houses": [1, 9, 12], "karakas": ["Jupiter", "Saturn", "Ketu"]},
}


def sign_from_lon(lon):
    return SIGNS[int(lon / 30) % 12]


def format_deg(lon):
    sign_deg = lon % 30
    d = int(sign_deg)
    m = int((sign_deg - d) * 60)
    return f"{d}\u00b0{str(m).zfill(2)}'"


def house_from_asc(planet_lon, asc_lon):
    asc_sign = int(asc_lon / 30) % 12
    planet_sign = int(planet_lon / 30) % 12
    house = (planet_sign - asc_sign) % 12 + 1
    return house


def _clamp(num, lo, hi):
    return max(lo, min(hi, num))


def _sign_index_from_name(sign):
    if sign in SIGNS:
        return SIGNS.index(sign)
    return None


def _planet_sign_index(planet):
    if not isinstance(planet, dict):
        return None
    if isinstance(planet.get("signIndex"), int):
        return planet["signIndex"] % 12
    if isinstance(planet.get("longitude"), (int, float)):
        return int(planet["longitude"] / 30.0) % 12
    return _sign_index_from_name(planet.get("sign"))


def _planet_by_name(planets, name):
    for planet in planets or []:
        if isinstance(planet, dict) and planet.get("name") == name:
            return planet
    return None


def _house_quality_points(planet_name, house):
    if house in (1, 4, 5, 7, 9, 10):
        return 1.0
    if house == 11:
        return 0.85
    if house in (2, 3):
        return 0.70
    if house == 6:
        return 0.62 if planet_name in NATURAL_MALEFICS else 0.48
    if house == 8:
        return 0.34
    if house == 12:
        return 0.40
    return 0.58


def _aspect_offsets(planet_name):
    offsets = {6}
    if planet_name == "Mars":
        offsets.update({3, 7})
    elif planet_name == "Jupiter":
        offsets.update({4, 8})
    elif planet_name == "Saturn":
        offsets.update({2, 9})
    elif planet_name in ("Rahu", "Ketu"):
        offsets.update({4, 8})
    return offsets


def _aspects_sign(planet_name, from_idx, target_idx):
    if from_idx is None or target_idx is None:
        return False
    return ((target_idx - from_idx) % 12) in _aspect_offsets(planet_name)


def _ang_dist(a, b):
    d = abs((a - b) % 360.0)
    return 360.0 - d if d > 180.0 else d


def _combustion_penalty(planets, planet_name):
    planet = _planet_by_name(planets, planet_name)
    sun = _planet_by_name(planets, "Sun")
    if not planet or not sun or planet_name in ("Sun", "Rahu", "Ketu"):
        return 0.0
    if not isinstance(planet.get("longitude"), (int, float)) or not isinstance(sun.get("longitude"), (int, float)):
        return 0.0
    thresholds = {
        "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
        "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
    }
    threshold = thresholds.get(planet_name, 12.0)
    return 1.0 if _ang_dist(float(planet["longitude"]), float(sun["longitude"])) <= threshold else 0.0


def _dignity_score(planet_name, sign_name):
    if planet_name not in CLASSICAL_DIGNITY_PLANETS:
        return 0.55, "neutral sign"
    if not sign_name:
        return 0.50, "unknown"
    if EXALT_SIGNS.get(planet_name) == sign_name:
        return 1.00, "exalted"
    if DEBIL_SIGNS.get(planet_name) == sign_name:
        return 0.18, "debilitated"
    if sign_name in OWN_SIGNS.get(planet_name, []):
        return 0.88, "own sign"
    sign_lord = SIGN_LORDS.get(sign_name)
    if sign_lord in PLANET_FRIENDS.get(planet_name, set()):
        return 0.72, "friendly sign"
    if sign_lord in PLANET_ENEMIES.get(planet_name, set()):
        return 0.35, "enemy sign"
    return 0.55, "neutral sign"


def _chart_power_label(score):
    if score >= 90:
        return "Very Strong", "#22c55e"
    if score >= 75:
        return "Strong", "#4ade80"
    if score >= 60:
        return "Good", "#f59e0b"
    if score >= 40:
        return "Average", "#fbbf24"
    return "Weak", "#ef4444"


def _profile_for_chart(chart_key):
    base = {
        "primary_houses": list(DEFAULT_CHART_POWER_PROFILE["primary_houses"]),
        "karakas": list(DEFAULT_CHART_POWER_PROFILE["karakas"]),
        "weights": dict(DEFAULT_CHART_POWER_PROFILE["weights"]),
    }
    override = CHART_POWER_PROFILES.get(chart_key, {})
    if "primary_houses" in override:
        base["primary_houses"] = list(override["primary_houses"])
    if "karakas" in override:
        base["karakas"] = list(override["karakas"])
    if "weights" in override:
        base["weights"].update(override["weights"])
    return base


def _lord_for_house(asc_idx, house):
    return SIGN_LORDS[SIGNS[(asc_idx + house - 1) % 12]]


def _planet_condition_score(planets, planet_name, d1_planets=None, important_houses=None):
    planet = _planet_by_name(planets, planet_name)
    if not planet:
        return 0.35, f"{planet_name} missing", None
    sign_idx = _planet_sign_index(planet)
    sign_name = SIGNS[sign_idx] if sign_idx is not None else planet.get("sign")
    house = int(planet.get("house") or 0)
    dignity, dignity_label = _dignity_score(planet_name, sign_name)
    house_q = _house_quality_points(planet_name, house)
    if important_houses and house in important_houses:
        house_q = min(1.0, house_q + 0.14)
    score = dignity * 0.64 + house_q * 0.36
    if _combustion_penalty(d1_planets or planets, planet_name):
        score -= 0.12
        dignity_label = f"{dignity_label}, combust"
    return _clamp(score, 0.0, 1.0), dignity_label, planet


def _score_lagna_lord(planets, asc_idx, max_score, strengths, challenges, d1_planets):
    lagna_lord = _lord_for_house(asc_idx, 1)
    score_unit, label, planet = _planet_condition_score(planets, lagna_lord, d1_planets, [1, 4, 5, 7, 9, 10])
    if planet:
        house = int(planet.get("house") or 0)
        if score_unit >= 0.74:
            strengths.append(f"Lagna lord {lagna_lord} is {label} in house {house}")
        elif score_unit <= 0.40:
            challenges.append(f"Lagna lord {lagna_lord} is {label} in house {house}")
    else:
        challenges.append(label)
    return score_unit * max_score


def _score_key_lords(planets, asc_idx, primary_houses, max_score, strengths, challenges, d1_planets):
    seen = []
    units = []
    for house in primary_houses:
        lord = _lord_for_house(asc_idx, house)
        if lord in seen:
            continue
        seen.append(lord)
        score_unit, label, planet = _planet_condition_score(planets, lord, d1_planets, primary_houses)
        units.append(score_unit)
        if planet:
            phouse = int(planet.get("house") or 0)
            if score_unit >= 0.74:
                strengths.append(f"{house}th lord {lord} is {label} in house {phouse}")
            elif score_unit <= 0.40:
                challenges.append(f"{house}th lord {lord} is {label} in house {phouse}")
    return (sum(units) / len(units) * max_score) if units else max_score * 0.45


def _score_karakas(planets, karakas, primary_houses, max_score, strengths, challenges, d1_planets):
    units = []
    for karaka in karakas:
        score_unit, label, planet = _planet_condition_score(planets, karaka, d1_planets, primary_houses)
        units.append(score_unit)
        if planet:
            house = int(planet.get("house") or 0)
            if score_unit >= 0.74:
                strengths.append(f"Karaka {karaka} is {label} in house {house}")
            elif score_unit <= 0.40:
                challenges.append(f"Karaka {karaka} is {label} in house {house}")
    return (sum(units) / len(units) * max_score) if units else max_score * 0.45


def _score_selected_dignity(planets, selected_names, max_score, strengths, challenges, d1_planets):
    units = []
    dignified_count = 0
    weak_count = 0
    for name in selected_names:
        planet = _planet_by_name(planets, name)
        if not planet:
            continue
        sign_idx = _planet_sign_index(planet)
        sign_name = SIGNS[sign_idx] if sign_idx is not None else planet.get("sign")
        dignity, label = _dignity_score(name, sign_name)
        if _combustion_penalty(d1_planets or planets, name):
            dignity = max(0.0, dignity - 0.16)
        units.append(dignity)
        if label in ("exalted", "own sign", "friendly sign"):
            dignified_count += 1
        elif label in ("debilitated", "enemy sign"):
            weak_count += 1
    if dignified_count:
        strengths.append(f"{dignified_count} selected planet(s) are in friendly/own/exalted dignity")
    if weak_count:
        challenges.append(f"{weak_count} selected planet(s) are in enemy/debilitated dignity")
    return (sum(units) / len(units) * max_score) if units else max_score * 0.45


def _score_selected_placements(planets, primary_houses, max_score, strengths, challenges):
    score_unit = 0.50
    for house in primary_houses:
        occupants = [p for p in planets if int(p.get("house") or 0) == house]
        if not occupants:
            continue
        benefics = [p.get("name") for p in occupants if p.get("name") in NATURAL_BENEFICS]
        malefics = [p.get("name") for p in occupants if p.get("name") in NATURAL_MALEFICS]
        score_unit += len(benefics) * 0.10
        score_unit -= len(malefics) * 0.07
        if benefics:
            strengths.append(f"House {house} receives benefic occupant(s): {', '.join(benefics)}")
        if malefics:
            challenges.append(f"House {house} receives malefic pressure: {', '.join(malefics)}")
    return _clamp(score_unit, 0.0, 1.0) * max_score


def _score_affliction_balance(planets, asc_idx, primary_houses, selected_names, max_score, strengths, challenges):
    target_signs = {asc_idx}
    for house in primary_houses:
        target_signs.add((asc_idx + house - 1) % 12)
    for name in selected_names:
        planet = _planet_by_name(planets, name)
        pidx = _planet_sign_index(planet)
        if pidx is not None:
            target_signs.add(pidx)

    support = 0
    pressure = 0
    for p in planets:
        pname = p.get("name")
        pidx = _planet_sign_index(p)
        phouse = int(p.get("house") or 0)
        for target_idx in target_signs:
            target_house = ((target_idx - asc_idx + 12) % 12) + 1
            hits = pidx == target_idx or _aspects_sign(pname, pidx, target_idx)
            if not hits:
                continue
            if pname in NATURAL_BENEFICS:
                support += 1
            elif pname in NATURAL_MALEFICS:
                pressure += 1
            if phouse in (6, 8, 12) and pname in selected_names:
                pressure += 1
            if target_house in primary_houses and pname in NATURAL_BENEFICS:
                support += 1

    score_unit = 0.55 + support * 0.045 - pressure * 0.04
    if support:
        strengths.append(f"Benefic support count on key points: {support}")
    if pressure:
        challenges.append(f"Affliction pressure count on key points: {pressure}")
    return _clamp(score_unit, 0.0, 1.0) * max_score


def _score_chart_power(chart_key, chart, d1_planets=None):
    planets = [p for p in (chart or {}).get("planets", []) if isinstance(p, dict)]
    asc_idx = (chart or {}).get("ascendantSignIndex")
    if not isinstance(asc_idx, int):
        asc_idx = _sign_index_from_name((chart or {}).get("ascendant"))
    if asc_idx is None or not planets:
        label, color = _chart_power_label(0)
        return {
            "chart": chart_key,
            "score": 0,
            "label": label,
            "color": color,
            "focus": CHART_POWER_FOCUS.get(chart_key, "Divisional chart strength"),
            "summary": f"{chart_key} chart power unavailable due to missing placements.",
            "factors": [],
            "strengths": [],
            "challenges": ["Chart placements missing"],
            "rules": [],
        }

    asc_idx %= 12
    profile = _profile_for_chart(chart_key)
    primary_houses = profile["primary_houses"]
    karakas = profile["karakas"]
    weights = profile["weights"]
    selected_names = list(dict.fromkeys([_lord_for_house(asc_idx, h) for h in primary_houses] + karakas + [_lord_for_house(asc_idx, 1)]))
    strengths = []
    challenges = []

    lagna_lord_score = _score_lagna_lord(planets, asc_idx, weights["lagnaLord"], strengths, challenges, d1_planets)
    key_lords_score = _score_key_lords(planets, asc_idx, primary_houses, weights["keyLords"], strengths, challenges, d1_planets)
    karakas_score = _score_karakas(planets, karakas, primary_houses, weights["karakas"], strengths, challenges, d1_planets)
    dignity_score = _score_selected_dignity(planets, selected_names, weights["dignity"], strengths, challenges, d1_planets)
    placement_score = _score_selected_placements(planets, primary_houses, weights["placement"], strengths, challenges)
    affliction_score = _score_affliction_balance(planets, asc_idx, primary_houses, selected_names, weights["affliction"], strengths, challenges)

    factor_rows = [
        ("lagnaLord", "Lagna lord strength", lagna_lord_score, weights["lagnaLord"]),
        ("keyLords", "Selected house lords", key_lords_score, weights["keyLords"]),
        ("karakas", "Chart karaka planets", karakas_score, weights["karakas"]),
        ("dignity", "Friend/enemy dignity", dignity_score, weights["dignity"]),
        ("placement", "Selected house placement", placement_score, weights["placement"]),
        ("affliction", "Affliction/support balance", affliction_score, weights["affliction"]),
    ]
    total = int(_clamp(round(sum(row[2] for row in factor_rows)), 0, 100))
    label, color = _chart_power_label(total)
    return {
        "chart": chart_key,
        "score": total,
        "label": label,
        "color": color,
        "focus": CHART_POWER_FOCUS.get(chart_key, "Divisional chart strength"),
        "summary": f"{chart_key} chart power is {label} ({total}/100).",
        "primaryHouses": primary_houses,
        "karakas": karakas,
        "factors": [
            {
                "key": key,
                "label": label_text,
                "score": round(score, 1),
                "max": max_score,
                "weightPct": max_score,
            }
            for key, label_text, score, max_score in factor_rows
        ],
        "strengths": list(dict.fromkeys(strengths))[:5],
        "challenges": list(dict.fromkeys(challenges))[:5],
        "rules": [
            f"Selected houses for {chart_key}: {', '.join(str(h) for h in primary_houses)}",
            f"Selected karakas for {chart_key}: {', '.join(karakas)}",
            "Friend/enemy/own/exalted/debilitated dignity is applied only to classical 7 planets",
            "Affliction balance counts natural benefic/malefic occupation and aspects on selected points",
        ],
    }


def date_to_iso(dt):
    return dt.strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# DASHA ENGINE — clean rebuild using Swiss Ephemeris + relativedelta
# ─────────────────────────────────────────────────────────────────────────────

def _frac_to_rd(years):
    """
    Convert a fractional year count to (whole_years, whole_months, whole_days)
    using the Vimshottari convention: 1 year = 12 months, 1 month = 30 days.

    Example: 2.4 → 2y 4m 24d
    """
    y = int(years)
    rem = years - y
    m_float = rem * 12
    m = int(m_float)
    d = round((m_float - m) * 30)
    return y, m, d


def _add_years(dt, years):
    """Add fractional dasha years to a datetime using relativedelta."""
    y, m, d = _frac_to_rd(years)
    return dt + relativedelta(years=y, months=m, days=d)


def _sub_years(dt, years):
    """Subtract fractional dasha years from a datetime using relativedelta."""
    y, m, d = _frac_to_rd(years)
    return dt + relativedelta(years=-y, months=-m, days=-d)


def _build_pds(ad_planet, ad_full_yrs, ad_start_dt):
    """
    Build all 9 Pratyantar Dashas (PD) inside an Antardasha.
    PD_duration = (AD_full_years × PD_planet_years) / 120
    Chained: each PD starts exactly where the previous ends. No gaps, no clamps.
    """
    pd_seq = DASHA_ORDER.index(ad_planet)
    prats  = []
    cur    = ad_start_dt
    for k in range(len(DASHA_ORDER)):
        pd_planet = DASHA_ORDER[(pd_seq + k) % len(DASHA_ORDER)]
        pd_yrs    = (ad_full_yrs * DASHA_YEARS[pd_planet]) / 120.0
        nxt       = _add_years(cur, pd_yrs)
        prats.append({
            "planet":    pd_planet,
            "startDate": date_to_iso(cur),
            "endDate":   date_to_iso(nxt),
            "years":     round(pd_yrs, 6),
        })
        cur = nxt
    return prats


def calc_vimshottari_dasha(moon_sidereal, moon_tropical, birth_jd, ayanamsa):
    """
    REBUILT Vimshottari Dasha engine — ephemeris-based, no shortcuts.

    RULES:
      1. Nakshatra from Moon sidereal longitude (Lahiri ayanamsa applied by caller)
      2. fraction_elapsed  = position_in_nakshatra / 13.333...
      3. elapsed_years     = fraction_elapsed × full_MD_years_of_birth_ruler
      4. MD_start          = birth_datetime − elapsed_years   (traditional anchor)
      5. MD_end            = MD_start + full_MD_years          (calendar-correct)
      6. Next MD chains:   start = prev_end, end = start + full_years
      7. AD_duration       = (MD_full_years × AD_planet_years) / 120
      8. PD_duration       = (AD_full_years × PD_planet_years) / 120
      9. No clamping, no rounding hacks, no forcing end dates
    """
    NAKSHATRA_SIZE = 360.0 / 27.0          # 13.33333...°

    nakshatra_idx    = int(moon_sidereal / NAKSHATRA_SIZE) % 27
    position_in_nak  = moon_sidereal % NAKSHATRA_SIZE
    fraction_elapsed = position_in_nak / NAKSHATRA_SIZE
    fraction_remain  = 1.0 - fraction_elapsed

    birth_ruler  = NAKSHATRA_RULERS[nakshatra_idx]
    md_yrs_ruler = float(DASHA_YEARS[birth_ruler])
    elapsed_yrs  = fraction_elapsed * md_yrs_ruler
    balance_yrs  = fraction_remain  * md_yrs_ruler

    birth_unix = (birth_jd - 2440587.5) * 86400.0
    birth_dt   = datetime.utcfromtimestamp(birth_unix)

    # Traditional anchor: MD started BEFORE birth; elapsed portion already consumed
    md0_start = _sub_years(birth_dt, elapsed_yrs)

    # ── Debug output — full precision, no rounding ────────────────────────────
    print(f"[Dasha] Moon tropical         : {repr(moon_tropical)}°", flush=True)
    print(f"[Dasha] Moon sidereal         : {repr(moon_sidereal)}°", flush=True)
    print(f"[Dasha] Ayanamsa (Lahiri)     : {repr(ayanamsa)}°", flush=True)
    print(f"[Dasha] Nakshatra index       : {nakshatra_idx}  ({NAKSHATRAS[nakshatra_idx]})", flush=True)
    print(f"[Dasha] Nakshatra start       : {repr(nakshatra_idx * NAKSHATRA_SIZE)}°", flush=True)
    print(f"[Dasha] Nakshatra end         : {repr((nakshatra_idx + 1) * NAKSHATRA_SIZE)}°", flush=True)
    print(f"[Dasha] Position in nakshatra : {repr(position_in_nak)}°", flush=True)
    print(f"[Dasha] Fraction elapsed      : {repr(fraction_elapsed)}", flush=True)
    print(f"[Dasha] Fraction remaining    : {repr(fraction_remain)}", flush=True)
    print(f"[Dasha] Elapsed years         : {repr(elapsed_yrs)}", flush=True)
    print(f"[Dasha] Balance dasha years   : {repr(balance_yrs)}", flush=True)
    print(f"[Dasha] Birth ruler           : {birth_ruler}  (full dasha = {md_yrs_ruler}y)", flush=True)
    print(f"[Dasha] MD0 start (before birth): {md0_start.strftime('%Y-%m-%d')}", flush=True)
    print(f"[Dasha] MD0 end               : {_add_years(md0_start, md_yrs_ruler).strftime('%Y-%m-%d')}", flush=True)
    print(f"[Dasha] Balance check         : birth + balance = {_add_years(birth_dt, balance_yrs).strftime('%Y-%m-%d')}", flush=True)

    start_idx   = DASHA_ORDER.index(birth_ruler)
    dashas      = []
    md_start_dt = md0_start

    for i in range(len(DASHA_ORDER) * 3):
        md_planet   = DASHA_ORDER[(start_idx + i) % len(DASHA_ORDER)]
        md_full_yrs = float(DASHA_YEARS[md_planet])
        md_end_dt   = _add_years(md_start_dt, md_full_yrs)

        print(f"[MD] {md_planet}: {md_start_dt.strftime('%Y-%m-%d')} → "
              f"{md_end_dt.strftime('%Y-%m-%d')} ({md_full_yrs}y)", flush=True)

        # ADs: sequence starts with the MD planet, full canonical durations
        ad_seq_start = DASHA_ORDER.index(md_planet)
        sub_dashas   = []
        ad_cur       = md_start_dt

        for j in range(len(DASHA_ORDER)):
            ad_planet   = DASHA_ORDER[(ad_seq_start + j) % len(DASHA_ORDER)]
            ad_full_yrs = (md_full_yrs * DASHA_YEARS[ad_planet]) / 120.0
            ad_end_dt   = _add_years(ad_cur, ad_full_yrs)

            print(f"  [AD] {md_planet}/{ad_planet}: "
                  f"{ad_cur.strftime('%Y-%m-%d')} → "
                  f"{ad_end_dt.strftime('%Y-%m-%d')} ({ad_full_yrs:.6f}y)", flush=True)

            prats = _build_pds(ad_planet, ad_full_yrs, ad_cur)

            sub_dashas.append({
                "planet":    ad_planet,
                "startDate": date_to_iso(ad_cur),
                "endDate":   date_to_iso(ad_end_dt),
                "years":     round(ad_full_yrs, 6),
                "subDashas": prats,
            })
            ad_cur = ad_end_dt

        dashas.append({
            "planet":    md_planet,
            "startDate": date_to_iso(md_start_dt),
            "endDate":   date_to_iso(md_end_dt),
            "years":     round(md_full_yrs, 6),
            "subDashas": sub_dashas,
        })
        md_start_dt = md_end_dt

    return dashas


def calculate_kundli(data):
    day = data["day"]
    month = data["month"]
    year = data["year"]
    hour = data["hour"]
    minute = data["minute"]
    ampm = data["ampm"]
    lat = data["lat"]
    lon = data["lon"]
    tz = data["tz"]
    name = data["name"]
    place = data["place"]

    # Convert 12h to 24h
    hour24 = hour
    if ampm == "PM" and hour != 12:
        hour24 = hour + 12
    elif ampm == "AM" and hour == 12:
        hour24 = 0

    # Local time as decimal hours
    local_decimal = hour24 + minute / 60.0
    # Convert to UTC
    ut_decimal = local_decimal - tz

    # Handle day rollover
    ut_day = day
    ut_month = month
    ut_year = year
    if ut_decimal < 0:
        ut_decimal += 24
        prev = datetime(year, month, day) - timedelta(days=1)
        ut_day = prev.day
        ut_month = prev.month
        ut_year = prev.year
    elif ut_decimal >= 24:
        ut_decimal -= 24
        nxt = datetime(year, month, day) + timedelta(days=1)
        ut_day = nxt.day
        ut_month = nxt.month
        ut_year = nxt.year

    # Debug: print input IST and converted UTC
    ut_h = int(ut_decimal)
    ut_m = round((ut_decimal - ut_h) * 60)
    print(f"[BIRTH] Input IST  : {hour24:02d}:{minute:02d} (tz=+{tz}h)  |  {day:02d}/{month:02d}/{year}")
    print(f"[BIRTH] Converted UTC: {ut_h:02d}:{ut_m:02d}  |  {ut_day:02d}/{ut_month:02d}/{ut_year}")

    # Julian Day Number (UT)
    jd = swe.julday(ut_year, ut_month, ut_day, ut_decimal)

    # CRITICAL: set Lahiri sidereal mode here, not just at module load.
    # Flask uses a thread pool — global C-state in pyswisseph can default to
    # Fagan-Bradley (mode 0) in threads that didn't run the module-level init.
    # Calling per-request ensures every calc uses Lahiri regardless of thread.
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    flags_sid  = swe.FLG_SIDEREAL | swe.FLG_SPEED
    flags_trop = swe.FLG_SPEED                       # tropical — no FLG_SIDEREAL

    # Sidereal planet positions — Swiss Ephemeris applies Lahiri internally
    planet_positions = {}
    planet_speeds    = {}
    for pname, pid in PLANET_IDS.items():
        result, _ = swe.calc_ut(jd, pid, flags_sid)
        planet_positions[pname] = result[0] % 360
        planet_speeds[pname]    = round(result[3], 6)

    # Rahu (Mean Node)
    result, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags_sid)
    rahu_lon = result[0] % 360
    planet_positions["Rahu"] = rahu_lon
    planet_positions["Ketu"] = (rahu_lon + 180) % 360
    planet_speeds["Rahu"]    = round(result[3], 6)
    planet_speeds["Ketu"]    = round(result[3], 6)

    # Ayanamsa via UT-based getter (same JD convention as calc_ut)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    # Tropical Moon — separate call without FLG_SIDEREAL, for debug only
    moon_tropical_raw, _ = swe.calc_ut(jd, swe.MOON, flags_trop)
    moon_tropical_lon    = moon_tropical_raw[0] % 360

    # Ascendant — houses() gives tropical; subtract ayanamsa for sidereal
    cusps, ascmc  = swe.houses(jd, lat, lon, b'W')
    asc_tropical  = ascmc[0]
    asc_sidereal  = (asc_tropical - ayanamsa + 360) % 360
    asc_lon       = asc_sidereal

    print(f"Tropical ASC    : {round(asc_tropical, 4)}", flush=True)
    print(f"Ayanamsa (Lahiri): {repr(ayanamsa)}", flush=True)
    print(f"Sidereal ASC    : {round(asc_sidereal, 4)} ({sign_from_lon(asc_sidereal)})", flush=True)
    print(f"Moon tropical   : {repr(moon_tropical_lon)}", flush=True)
    print(f"Moon sidereal   : {repr(planet_positions['Moon'])}", flush=True)

    # Moon nakshatra
    moon_lon = planet_positions["Moon"]
    nakshatra_size = 360.0 / 27.0
    nakshatra_idx = int(moon_lon / nakshatra_size) % 27
    nakshatra_name = NAKSHATRAS[nakshatra_idx]
    position_in_nak = moon_lon % nakshatra_size
    pada = int(position_in_nak / (nakshatra_size / 4)) + 1

    _nak_start      = nakshatra_idx * nakshatra_size
    _nak_end        = (nakshatra_idx + 1) * nakshatra_size
    _frac_elapsed   = position_in_nak / nakshatra_size
    _frac_remaining = 1.0 - _frac_elapsed
    _birth_ruler    = NAKSHATRA_RULERS[nakshatra_idx]
    _balance_yrs    = DASHA_YEARS[_birth_ruler] * _frac_remaining

    # Vimshottari Dasha — full rebuild with traditional anchoring
    # moon_lon is already sidereal (via FLG_SIDEREAL); moon_tropical_lon is real tropical
    dashas = calc_vimshottari_dasha(moon_lon, moon_tropical_lon, jd, ayanamsa)

    print(f"1. Moon sidereal longitude : {moon_lon}", flush=True)
    print(f"2. Nakshatra start degree  : {_nak_start}", flush=True)
    print(f"3. Nakshatra end degree    : {_nak_end}", flush=True)
    print(f"4. Position inside nakshatra: {position_in_nak}", flush=True)
    print(f"5. Fraction elapsed        : {_frac_elapsed}", flush=True)
    print(f"6. Fraction remaining      : {_frac_remaining}", flush=True)
    print(f"7. Balance dasha years     : {_balance_yrs}", flush=True)
    print(f"8. MD start date           : {dashas[0]['startDate']}", flush=True)
    print(f"9. MD end date             : {dashas[0]['endDate']}", flush=True)

    # Current dasha
    now_dt = datetime.utcnow()
    now_date = now_dt.date()
    current_maha = None
    current_antar = None
    for d in dashas:
        ds = datetime.strptime(d["startDate"], "%Y-%m-%d").date()
        de = datetime.strptime(d["endDate"],   "%Y-%m-%d").date()
        if ds <= now_date < de:
            current_maha = d
            for s in d["subDashas"]:
                ss = datetime.strptime(s["startDate"], "%Y-%m-%d").date()
                se = datetime.strptime(s["endDate"],   "%Y-%m-%d").date()
                if ss <= now_date < se:
                    current_antar = s
                    break
            break
    if not current_maha:
        current_maha = dashas[0]
    if not current_antar:
        current_antar = current_maha["subDashas"][0]

    # Build planet list
    # Phase 2.8.78 (FIX F1): each planet now carries nakshatra + pada + ruler
    # so downstream consumers (UI, validators, narrators) don't have to recompute.
    _nak_size = 360.0 / 27.0
    planet_list = []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        plon = planet_positions[pname]
        spd  = planet_speeds.get(pname, 0)
        _p_nak_idx = int(plon / _nak_size) % 27
        _p_pos_in_nak = plon % _nak_size
        planet_list.append({
            "name":      pname,
            "sign":      sign_from_lon(plon),
            "degrees":   format_deg(plon),
            "house":     house_from_asc(plon, asc_lon),
            "longitude": round(plon, 4),
            "retrograde": spd < 0,
            "speed":      spd,
            "nakshatra":      NAKSHATRAS[_p_nak_idx],
            "nakshatraPada":  int(_p_pos_in_nak / (_nak_size / 4)) + 1,
            "nakshatraRuler": NAKSHATRA_RULERS[_p_nak_idx],
        })

    # ── Divisional Charts (Vargas) ───────────────────────────────────────────
    # D2..D60 vargas used by the mobile divisional-chart screen.
    _MOVABLE_SIGNS = {0, 3, 6, 9}
    _FIXED_SIGNS   = {1, 4, 7, 10}
    _FIRE_SIGNS    = {0, 4, 8}
    _EARTH_SIGNS   = {1, 5, 9}
    _AIR_SIGNS     = {2, 6, 10}

    def _sign_idx(lon):
        return int(lon / 30.0) % 12

    def _part_idx(lon, parts):
        deg_in_sign = lon % 30.0
        return min(parts - 1, int(deg_in_sign / (30.0 / float(parts))))

    def _modality_seed(sidx):
        if sidx in _MOVABLE_SIGNS:
            return 0
        if sidx in _FIXED_SIGNS:
            return 4
        return 8

    def _d2_sign_idx(lon):
        # Hora: odd signs Sun/Moon, even signs Moon/Sun.
        sidx = _sign_idx(lon)
        first_half = (lon % 30.0) < 15.0
        if sidx % 2 == 0:
            return 4 if first_half else 3
        return 3 if first_half else 4

    def _d3_sign_idx(lon):
        # Drekkana: self, 5th, 9th.
        sidx = _sign_idx(lon)
        return (sidx + _part_idx(lon, 3) * 4) % 12

    def _d4_sign_idx(lon):
        # BPHS Chaturthamsa: 4 parts of 7°30'; kendra offsets 1-4-7-10 from natal sign
        sidx = _sign_idx(lon)
        p_idx = _part_idx(lon, 4)
        return (sidx + p_idx * 3) % 12

    def _d7_sign_idx(lon):
        # BPHS Saptamsha: 7 parts per sign; odd signs count from self, even from 7th
        sidx = _sign_idx(lon)
        p_idx = _part_idx(lon, 7)
        seed = sidx if sidx % 2 == 0 else (sidx + 6) % 12
        return (seed + p_idx) % 12

    def _d9_sign_idx(lon):
        # BPHS Navamsha: movable/fixed/dual seed signs (matches divisional_charts.py)
        sidx = _sign_idx(lon)
        n_idx = _part_idx(lon, 9)
        if sidx in _MOVABLE_SIGNS:
            seed = sidx
        elif sidx in _FIXED_SIGNS:
            seed = (sidx + 8) % 12
        else:
            seed = (sidx + 4) % 12
        return (seed + n_idx) % 12

    def _d10_sign_idx(lon):
        # Parashari Dashamsha: odd signs start from self, even signs from 9th
        sidx = _sign_idx(lon)
        pada = _part_idx(lon, 10)                    # 0-9 (each 3°)
        if sidx % 2 == 0:                            # sign_index 0,2,4... = odd signs
            return (sidx + pada) % 12
        return (sidx + 8 + pada) % 12

    def _d12_sign_idx(lon):
        sidx = _sign_idx(lon)
        return (sidx + _part_idx(lon, 12)) % 12

    def _d16_sign_idx(lon):
        sidx = _sign_idx(lon)
        return (_modality_seed(sidx) + _part_idx(lon, 16)) % 12

    def _d20_sign_idx(lon):
        # BPHS Vimsamsa: 20 parts of 1°30'; Movable→Aries, Fixed→Sagittarius, Dual→Leo
        sidx = _sign_idx(lon)
        p_idx = _part_idx(lon, 20)
        if sidx in _MOVABLE_SIGNS:
            seed = 0
        elif sidx in _FIXED_SIGNS:
            seed = 8
        else:
            seed = 4
        return (seed + p_idx) % 12

    def _d24_sign_idx(lon):
        sidx = _sign_idx(lon)
        seed = 4 if sidx % 2 == 0 else 3
        return (seed + _part_idx(lon, 24)) % 12

    def _d27_sign_idx(lon):
        sidx = _sign_idx(lon)
        if sidx in _FIRE_SIGNS:
            seed = 0
        elif sidx in _EARTH_SIGNS:
            seed = 3
        elif sidx in _AIR_SIGNS:
            seed = 6
        else:
            seed = 9
        return (seed + _part_idx(lon, 27)) % 12

    def _d30_sign_idx(lon):
        sidx = _sign_idx(lon)
        deg = lon % 30.0
        if sidx % 2 == 0:
            if deg < 5.0:
                return 0   # Mars: Aries
            if deg < 10.0:
                return 10  # Saturn: Aquarius
            if deg < 18.0:
                return 8   # Jupiter: Sagittarius
            if deg < 25.0:
                return 2   # Mercury: Gemini
            return 6       # Venus: Libra
        if deg < 5.0:
            return 1       # Venus: Taurus
        if deg < 12.0:
            return 5       # Mercury: Virgo
        if deg < 20.0:
            return 11      # Jupiter: Pisces
        if deg < 25.0:
            return 9       # Saturn: Capricorn
        return 7           # Mars: Scorpio

    def _d40_sign_idx(lon):
        sidx = _sign_idx(lon)
        seed = 0 if sidx % 2 == 0 else 6
        return (seed + _part_idx(lon, 40)) % 12

    def _d45_sign_idx(lon):
        sidx = _sign_idx(lon)
        return (_modality_seed(sidx) + _part_idx(lon, 45)) % 12

    def _d60_sign_idx(lon):
        sidx = _sign_idx(lon)
        p_idx = _part_idx(lon, 60)
        if sidx % 2 == 0:
            return (sidx + p_idx) % 12
        return (sidx - p_idx + 120) % 12

    def _build_varga(sign_fn, asc_deg, positions):
        asc_idx = sign_fn(asc_deg)
        planets_varga = []
        for pname_v in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
            plon_v = positions[pname_v]
            sidx_v = sign_fn(plon_v)
            planets_varga.append({
                "name":       pname_v,
                "sign":       SIGNS[sidx_v],
                "signIndex":  sidx_v,
                "house":      ((sidx_v - asc_idx + 12) % 12) + 1,
            })
        return {
            "ascendant":           SIGNS[asc_idx],
            "ascendantSignIndex":  asc_idx,
            "planets":             planets_varga,
        }

    d2_chart  = _build_varga(_d2_sign_idx,  asc_lon, planet_positions)
    d3_chart  = _build_varga(_d3_sign_idx,  asc_lon, planet_positions)
    d4_chart  = _build_varga(_d4_sign_idx,  asc_lon, planet_positions)
    d7_chart  = _build_varga(_d7_sign_idx,  asc_lon, planet_positions)
    d9_chart  = _build_varga(_d9_sign_idx,  asc_lon, planet_positions)
    d10_chart = _build_varga(_d10_sign_idx, asc_lon, planet_positions)
    d12_chart = _build_varga(_d12_sign_idx, asc_lon, planet_positions)
    d16_chart = _build_varga(_d16_sign_idx, asc_lon, planet_positions)
    d20_chart = _build_varga(_d20_sign_idx, asc_lon, planet_positions)
    d24_chart = _build_varga(_d24_sign_idx, asc_lon, planet_positions)
    d27_chart = _build_varga(_d27_sign_idx, asc_lon, planet_positions)
    d30_chart = _build_varga(_d30_sign_idx, asc_lon, planet_positions)
    d40_chart = _build_varga(_d40_sign_idx, asc_lon, planet_positions)
    d45_chart = _build_varga(_d45_sign_idx, asc_lon, planet_positions)
    d60_chart = _build_varga(_d60_sign_idx, asc_lon, planet_positions)

    for _varga_name, _varga_chart in [
        ("D2", d2_chart), ("D3", d3_chart), ("D4", d4_chart), ("D7", d7_chart),
        ("D9", d9_chart), ("D10", d10_chart), ("D12", d12_chart), ("D16", d16_chart),
        ("D20", d20_chart), ("D24", d24_chart), ("D27", d27_chart), ("D30", d30_chart),
        ("D40", d40_chart), ("D45", d45_chart), ("D60", d60_chart),
    ]:
        print(f"[VARGA] {_varga_name} Lagna: {_varga_chart['ascendant']}", flush=True)

    d1_chart_for_power = {
        "ascendant": sign_from_lon(asc_lon),
        "ascendantSignIndex": int(asc_lon / 30.0) % 12,
        "planets": planet_list,
    }
    chart_powers = {
        "D1": _score_chart_power("D1", d1_chart_for_power, planet_list),
        "D2": _score_chart_power("D2", d2_chart, planet_list),
        "D3": _score_chart_power("D3", d3_chart, planet_list),
        "D4": _score_chart_power("D4", d4_chart, planet_list),
        "D7": _score_chart_power("D7", d7_chart, planet_list),
        "D9": _score_chart_power("D9", d9_chart, planet_list),
        "D10": _score_chart_power("D10", d10_chart, planet_list),
        "D12": _score_chart_power("D12", d12_chart, planet_list),
        "D16": _score_chart_power("D16", d16_chart, planet_list),
        "D20": _score_chart_power("D20", d20_chart, planet_list),
        "D24": _score_chart_power("D24", d24_chart, planet_list),
        "D27": _score_chart_power("D27", d27_chart, planet_list),
        "D30": _score_chart_power("D30", d30_chart, planet_list),
        "D40": _score_chart_power("D40", d40_chart, planet_list),
        "D45": _score_chart_power("D45", d45_chart, planet_list),
        "D60": _score_chart_power("D60", d60_chart, planet_list),
    }
    for _varga_name, _varga_chart in [
        ("D2", d2_chart), ("D3", d3_chart), ("D4", d4_chart), ("D7", d7_chart),
        ("D9", d9_chart), ("D10", d10_chart), ("D12", d12_chart), ("D16", d16_chart),
        ("D20", d20_chart), ("D24", d24_chart), ("D27", d27_chart), ("D30", d30_chart),
        ("D40", d40_chart), ("D45", d45_chart), ("D60", d60_chart),
    ]:
        _varga_chart["power"] = chart_powers[_varga_name]


    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dob_str = f"{day} {month_names[month - 1]} {year}"
    time_str = f"{str(hour).zfill(2)}:{str(minute).zfill(2)} {ampm}"

    # Balance of birth-ruler dasha remaining at birth (in years)
    birth_ruler_years_val = DASHA_YEARS[NAKSHATRA_RULERS[nakshatra_idx]]
    fraction_elapsed_val  = (moon_lon % (360.0 / 27.0)) / (360.0 / 27.0)
    birth_dasha_balance   = round(birth_ruler_years_val * (1.0 - fraction_elapsed_val), 6)

    result = {
        "name": name,
        "dob": dob_str,
        "time": time_str,
        "place": place,
        "ascendant": sign_from_lon(asc_lon),
        "ascendantDeg": round(asc_lon, 4),
        "moonSign": sign_from_lon(moon_lon),
        "sunSign": sign_from_lon(planet_positions["Sun"]),
        "nakshatra": nakshatra_name,
        "nakshatraPada": pada,
        "nakshatraRuler": NAKSHATRA_RULERS[nakshatra_idx],
        "moonLongitude": round(moon_lon, 6),
        "dashaBalance":  birth_dasha_balance,
        "calcVersion":   KUNDLI_CALC_VERSION,
        "planets": planet_list,
        "chartPowers": chart_powers,
        "divisionalCharts": {
            "D2":  d2_chart,
            "D3":  d3_chart,
            "D4":  d4_chart,
            "D7":  d7_chart,
            "D9":  d9_chart,
            "D10": d10_chart,
            "D12": d12_chart,
            "D16": d16_chart,
            "D20": d20_chart,
            "D24": d24_chart,
            "D27": d27_chart,
            "D30": d30_chart,
            "D40": d40_chart,
            "D45": d45_chart,
            "D60": d60_chart,
        },
        "dashas": dashas,
        "currentDasha": {
            "maha": current_maha["planet"],
            "antar": current_antar["planet"],
            "startDate": current_antar["startDate"],
            "endDate": current_antar["endDate"]
        },
        "currentPhase": {
            "name": f"{current_maha['planet']} – {current_antar['planet']}",
            "start": current_antar["startDate"],
            "end": current_antar["endDate"]
        }
    }

    # ── Phase 2.8.78 (FIX F4): bake current Pratyantar (PD) into currentDasha
    # so UI / engines that read kundli["currentDasha"] see all 3 levels (MD/AD/PD)
    # without separate compute_pratyantar() calls. Non-fatal — silently skip on error.
    try:
        from pratyantar import compute_pratyantar  # local import — avoid cycles
        _pd = compute_pratyantar(result["currentDasha"]) or {}
        _cur = _pd.get("current_pd") or {}
        if _cur.get("lord"):
            result["currentDasha"]["pratyantar"] = _cur["lord"]
            result["currentDasha"]["pratyantarStart"] = _cur.get("start")
            result["currentDasha"]["pratyantarEnd"]   = _cur.get("end")
    except Exception as exc:
        print(f"[kundli_engine] pratyantar bake failed (non-fatal): {exc}", flush=True)

    # ── KP cache (Phase 2.8.57 — bake full KP into chart_data) ─────────────
    # ADD-ONLY: same birth dict drives kp_engine.calculate_kp so the cusps +
    # planet sub-lord chain (NL/SB/SS) are computed ONCE and stored on the
    # kundli row. Downstream callers (engines, locked_facts, marriage filter)
    # can then read kundli["kp"] instead of recomputing every request.
    # Failure is non-fatal — kundli still returns without `kp` key, callers
    # already have a fallback path that recomputes from birth details.
    try:
        from kp_engine import calculate_kp  # local import — avoids cycle on cold load
        result["kp"] = calculate_kp({
            "day": day, "month": month, "year": year,
            "hour": hour, "minute": minute, "ampm": ampm,
            "lat": lat, "lon": lon, "tz": tz,
        })
    except Exception as exc:
        print(f"[kundli_engine.calculate_kundli] KP cache failed (non-fatal): {exc}", flush=True)

    return result


if __name__ == "__main__":
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        output = calculate_kundli(data)
        print(json.dumps(output))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
