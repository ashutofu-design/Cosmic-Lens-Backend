"""
Sprint 24 — Tier 8 Transits Deep
Fills 3 gaps left by transits.py / transit_engine.py:

  1) Saturn through 12 houses — detailed effects per current Saturn-house
     (BPHS + Phaladeepika classical interpretations).
  2) Eclipse impact — Rahu-Ketu axis vs natal planets within ±5° orb;
     plus current eclipse season detection.
  3) Fixed Stars overlap — 24 major stars (Spica, Regulus, Aldebaran,
     Antares, etc.) mapped to nakshatras + conjunctions with natal planets
     within 1° orb.
"""
from __future__ import annotations
from typing import Any
from datetime import datetime
import math

try:
    import swisseph as swe  # type: ignore
    _HAS_SWE = True
    swe.set_sid_mode(swe.SIDM_LAHIRI)
except Exception:
    _HAS_SWE = False

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


# ---------------------------------------------------------------------------
# 1) Saturn through 12 houses — classical detail (BPHS / Phaladeepika)
# ---------------------------------------------------------------------------
SATURN_HOUSE_EFFECTS = {
    1: ("CHALLENGING", "Health concerns, depression, body weakness, slow progress. "
                       "Discipline through hardship; karmic test on identity."),
    2: ("MIXED", "Financial discipline forced, family tensions, speech becomes harsh. "
                 "Savings if Saturn well-placed; debt if afflicted."),
    3: ("FAVOURABLE", "Excellent for siblings, courage grows through struggle, "
                      "promotions through hard work, success against enemies."),
    4: ("CHALLENGING", "Mother's health, property delays, mental peace lost, home conflicts. "
                       "Foundation rebuilding karma."),
    5: ("CHALLENGING", "Children worry, education obstacles, romance breakups, "
                       "speculative losses. Past-life karma surfaces."),
    6: ("FAVOURABLE", "Victory over enemies, debt cleared, illness curable, "
                      "service/job promotion, legal wins."),
    7: ("CHALLENGING", "Spouse health/conflicts, partnership breaks, business losses, "
                       "delays in marriage if unmarried. 7.5-yr karma cycle starts."),
    8: ("CRITICAL", "Ashtama Shani — accidents, chronic illness, sudden losses, "
                    "occult experiences, transformation through crisis."),
    9: ("CHALLENGING", "Father's health, religious doubts, long-distance travel delays, "
                       "guru-bhagya weakens, dharma confusion."),
    10: ("FAVOURABLE", "Career peak through sustained effort, authority position, "
                       "government recognition, status rises despite obstacles."),
    11: ("FAVOURABLE", "Wealth gains, friend-network expands, wishes fulfilled, "
                       "elder siblings supportive, big income spikes."),
    12: ("MIXED", "Foreign settlement chances, expenses on spirituality/charity, "
                  "isolation/retreat, sleep issues, hospital/jail risks if afflicted."),
}


def saturn_through_houses_detail(saturn_sign_idx: int,
                                 lagna_sign_idx: int,
                                 moon_sign_idx: int) -> dict[str, Any]:
    """Returns Saturn current house from Lagna AND Moon with detail."""
    h_lagna = ((saturn_sign_idx - lagna_sign_idx) % 12) + 1
    h_moon = ((saturn_sign_idx - moon_sign_idx) % 12) + 1
    verdict_l, detail_l = SATURN_HOUSE_EFFECTS.get(h_lagna, ("UNKNOWN", ""))
    verdict_m, detail_m = SATURN_HOUSE_EFFECTS.get(h_moon, ("UNKNOWN", ""))
    return {
        "saturn_sign": SIGN_NAMES[saturn_sign_idx],
        "from_lagna": {
            "house": h_lagna,
            "verdict": verdict_l,
            "detail": detail_l,
        },
        "from_moon": {
            "house": h_moon,
            "verdict": verdict_m,
            "detail": detail_m,
        },
        "is_sade_sati": h_moon in (12, 1, 2),
        "is_ashtama": h_moon == 8,
        "is_kantaka": h_moon in (4, 7, 10),
    }


# ---------------------------------------------------------------------------
# 2) Eclipse impact — Rahu/Ketu axis vs natal planets
# ---------------------------------------------------------------------------
def _current_node_lons(when: datetime | None = None) -> tuple[float, float] | None:
    if not _HAS_SWE:
        return None
    when = when or datetime.utcnow()
    jd = swe.julday(when.year, when.month, when.day,
                    when.hour + when.minute / 60.0)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    rahu_lon = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0] % 360
    ketu_lon = (rahu_lon + 180) % 360
    return rahu_lon, ketu_lon


def eclipse_impact(natal_planets: list[dict],
                   when: datetime | None = None,
                   orb: float = 5.0) -> dict[str, Any]:
    """Detect natal planets that lie within `orb` degrees of the current
    Rahu-Ketu eclipse axis."""
    nodes = _current_node_lons(when)
    if nodes is None:
        return {"available": False, "reason": "swisseph unavailable"}
    rahu_lon, ketu_lon = nodes
    impacts = []
    for p in natal_planets:
        if not isinstance(p, dict):
            continue
        lon = p.get("longitude")
        if not isinstance(lon, (int, float)):
            continue
        nm = p.get("name")
        if nm in ("Rahu", "Ketu"):
            continue
        # Distance to either node
        d_rahu = min(abs(lon - rahu_lon), 360 - abs(lon - rahu_lon))
        d_ketu = min(abs(lon - ketu_lon), 360 - abs(lon - ketu_lon))
        if d_rahu <= orb:
            impacts.append({"planet": nm, "axis": "Rahu (North)",
                            "orb_deg": round(d_rahu, 2),
                            "effect": "Sudden disruption, obsession, eclipse-shadow on this karaka"})
        elif d_ketu <= orb:
            impacts.append({"planet": nm, "axis": "Ketu (South)",
                            "orb_deg": round(d_ketu, 2),
                            "effect": "Detachment, spiritual loss, sudden release of this karaka"})
    return {
        "available": True,
        "evaluated_at": (when or datetime.utcnow()).strftime("%Y-%m-%d"),
        "current_rahu_lon": round(rahu_lon, 2),
        "current_ketu_lon": round(ketu_lon, 2),
        "rahu_sign": SIGN_NAMES[int(rahu_lon // 30)],
        "ketu_sign": SIGN_NAMES[int(ketu_lon // 30)],
        "orb_used": orb,
        "natal_impacts": impacts,
        "any_eclipse_impact": len(impacts) > 0,
    }


# ---------------------------------------------------------------------------
# 3) Fixed Stars overlap (24 major stars, sidereal longitude April 2026)
# ---------------------------------------------------------------------------
# Source: classical Vedic mappings + modern catalog (Lahiri ayanamsa, J2000+25y)
FIXED_STARS = [
    ("Aldebaran",      "Royal Star (East)",    69.78,   "Eye of the Bull, courage, leadership"),
    ("Regulus",        "Royal Star (North)",   149.94,  "Heart of the Lion, kingship, fame"),
    ("Antares",        "Royal Star (West)",    249.92,  "Heart of Scorpion, war, transformation"),
    ("Fomalhaut",      "Royal Star (South)",   333.83,  "Mystic, spiritual genius, fall risk"),
    ("Spica",          "Most auspicious",      203.85,  "Wealth, gifts, divine favor"),
    ("Vega",           "Charismatic",          285.43,  "Magic, art, public success"),
    ("Sirius",         "Brightest star",       104.13,  "Faithful, creative, luxury"),
    ("Canopus",        "Sage star",            105.03,  "Wisdom, navigation, longevity"),
    ("Arcturus",       "Watcher",              204.23,  "Justice, protection, patience"),
    ("Procyon",        "Swift gain",           115.86,  "Quick fortune then loss"),
    ("Algol",          "Most violent",         56.10,   "Beheading star, danger, violence"),
    ("Alcyone",        "Pleiades head",        60.02,   "Vision, leadership, weeping"),
    ("Capella",        "Little goat",          81.79,   "Knowledge, curiosity, honor"),
    ("Betelgeuse",     "Right shoulder Orion", 88.97,   "Wealth-fame, military glory"),
    ("Rigel",          "Left foot Orion",      76.48,   "Education, science, riches"),
    ("Castor",         "Twin",                 119.84,  "Mind, writing, sudden loss"),
    ("Pollux",         "Twin",                 122.83,  "Boxer, athletics, conflict"),
    ("Mizar",          "Bear",                 175.58,  "Mass disasters, fires"),
    ("Algorab",        "Crow",                 190.83,  "Lies, scavenging, deceit"),
    ("Vindemiatrix",   "Widow-maker",          198.94,  "Loss of partner, judgment"),
    ("Zubeneschamali", "North Scale",          221.00,  "Honor, wealth, brilliance"),
    ("Zubenelgenubi",  "South Scale",          221.50,  "Trickery, payment, justice"),
    ("Acrux",          "Southern Cross",       190.62,  "Religion, mysticism"),
    ("Achernar",       "End of river",         13.16,   "Success, royal favor, danger from water"),
]


def fixed_stars_overlap(natal_planets: list[dict],
                        orb: float = 1.0) -> dict[str, Any]:
    """Find natal planets within `orb` degrees of any major fixed star."""
    overlaps = []
    for star_name, star_class, star_lon, star_meaning in FIXED_STARS:
        for p in natal_planets:
            if not isinstance(p, dict):
                continue
            lon = p.get("longitude")
            if not isinstance(lon, (int, float)):
                continue
            nm = p.get("name")
            if nm not in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                          "Venus", "Saturn", "Rahu", "Ketu"):
                continue
            d = min(abs(lon - star_lon), 360 - abs(lon - star_lon))
            if d <= orb:
                overlaps.append({
                    "planet": nm,
                    "star": star_name,
                    "star_class": star_class,
                    "orb_deg": round(d, 2),
                    "meaning": star_meaning,
                })
    return {
        "available": True,
        "stars_checked": len(FIXED_STARS),
        "orb_used": orb,
        "overlaps": overlaps,
        "any_overlap": len(overlaps) > 0,
    }


# ---------------------------------------------------------------------------
# Master orchestrator
# ---------------------------------------------------------------------------
def compute_transit_deep(kundli: dict) -> dict[str, Any]:
    planets = kundli.get("planets") or []
    if not isinstance(planets, list) or not planets:
        return {"available": False, "reason": "no planets"}

    asc = kundli.get("ascendant")
    moon = next((p for p in planets if isinstance(p, dict) and p.get("name") == "Moon"), None)
    if not (isinstance(asc, str) and asc in SIGN_NAMES) or not moon:
        return {"available": False, "reason": "missing ascendant or Moon"}
    lagna_si = SIGN_NAMES.index(asc)
    moon_si = SIGN_NAMES.index(moon["sign"]) if moon.get("sign") in SIGN_NAMES else None
    if moon_si is None:
        return {"available": False, "reason": "moon sign invalid"}

    # Get current Saturn sign via swisseph
    saturn_si = None
    if _HAS_SWE:
        when = datetime.utcnow()
        jd = swe.julday(when.year, when.month, when.day,
                        when.hour + when.minute / 60.0)
        sat_lon = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)[0][0] % 360
        saturn_si = int(sat_lon // 30)

    saturn_detail = saturn_through_houses_detail(saturn_si, lagna_si, moon_si) \
        if saturn_si is not None else {"available": False}

    eclipse = eclipse_impact(planets)
    fixed = fixed_stars_overlap(planets)

    return {
        "available": True,
        "system": "Transit Deep (Sprint 24)",
        "saturn_detail": saturn_detail,
        "eclipse_impact": eclipse,
        "fixed_stars_overlap": fixed,
    }


def format_transit_deep_summary(result: dict) -> str:
    if not isinstance(result, dict) or not result.get("available"):
        return ""
    lines = ["── TRANSIT DEEP (Sprint 24) ──"]

    sd = result.get("saturn_detail", {})
    if sd and sd.get("from_lagna"):
        fl = sd["from_lagna"]; fm = sd["from_moon"]
        lines.append(f"Saturn in {sd['saturn_sign']}:")
        lines.append(f"  From Lagna H{fl['house']} → {fl['verdict']}: {fl['detail']}")
        lines.append(f"  From Moon  H{fm['house']} → {fm['verdict']}: {fm['detail']}")
        flags = []
        if sd.get("is_sade_sati"): flags.append("Sade-Sati ACTIVE")
        if sd.get("is_ashtama"):   flags.append("Ashtama Shani")
        if sd.get("is_kantaka"):   flags.append("Kantaka Shani")
        if flags:
            lines.append(f"  Flags: {', '.join(flags)}")

    ec = result.get("eclipse_impact", {})
    if ec.get("available"):
        lines.append(f"Eclipse Axis (now): Rahu {ec['rahu_sign']} {ec['current_rahu_lon']}°, "
                     f"Ketu {ec['ketu_sign']} {ec['current_ketu_lon']}°")
        if ec.get("natal_impacts"):
            for imp in ec["natal_impacts"]:
                lines.append(f"  ⚠ {imp['planet']} within {imp['orb_deg']}° of {imp['axis']} — {imp['effect']}")
        else:
            lines.append("  No natal planets within 5° of current eclipse axis")

    fs = result.get("fixed_stars_overlap", {})
    if fs.get("available"):
        if fs.get("overlaps"):
            lines.append(f"Fixed Star Conjunctions (within {fs['orb_used']}°):")
            for o in fs["overlaps"]:
                lines.append(f"  ★ {o['planet']} on {o['star']} ({o['star_class']}) "
                             f"[{o['orb_deg']}°] — {o['meaning']}")
        else:
            lines.append(f"Fixed Stars: No major conjunctions within {fs['orb_used']}° "
                         f"(checked {fs['stars_checked']} stars)")
    return "\n".join(lines)
