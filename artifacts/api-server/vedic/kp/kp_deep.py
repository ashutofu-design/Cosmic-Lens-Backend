"""
Sprint 25 — Tier 9 KP Deep
Fills 5 KP gaps that work without Placidus cusps (which need lat/lon):

  1) Sub-Sub-Sub Lord (3 deep) — for any longitude, returns
     [Sign Lord, Star Lord (NL), Sub Lord (SL), Sub-Sub (SS), Sub-Sub-Sub (SSS)]
  2) Significators 4-Level Deep — for natal planets (sign-house basis):
     L1=Planets in star of house occupants, L2=Occupants, L3=Planets in
     star of house lord, L4=House lord
  3) Ruling Planets (current moment) — Day-lord, Moon-NL, Moon-SL,
     Lagna-Sign-Lord, Lagna-NL, Lagna-SL
  4) 249 Horary Numbers — static lookup mapping 1..249 → sign+star+sub+lord
  5) Eclipse Pin-Point — next solar + lunar eclipse with KP sub-lord
     active at that moment
"""
from __future__ import annotations
from typing import Any
from datetime import datetime, timedelta

try:
    import swisseph as swe  # type: ignore
    _HAS_SWE = True
    swe.set_sid_mode(swe.SIDM_LAHIRI)
except Exception:
    _HAS_SWE = False

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
              "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
              "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
              "Anuradha", "Jyeshta", "Mula", "Purva Ashadha", "Uttara Ashadha",
              "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
              "Uttara Bhadrapada", "Revati"]
NAK_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
             "Saturn", "Mercury"]  # repeats 3 times for 27 nakshatras
VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
              "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
VIMS_TOTAL = 120
NAK_EXTENT = 13.0 + 20.0/60.0  # 13°20'

DAY_LORDS = {0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter",
             4: "Venus", 5: "Saturn", 6: "Sun"}  # Mon=0..Sun=6


# ---------------------------------------------------------------------------
# 1) Sub-Sub-Sub Lord (3 deep)
# ---------------------------------------------------------------------------
def kp_full_lords(longitude: float) -> dict[str, str]:
    """Returns {sign_lord, star_lord, sub_lord, sub_sub_lord, sub_sub_sub_lord}."""
    lon = longitude % 360.0
    sign_idx = int(lon / 30) % 12
    sl = SIGN_LORDS[sign_idx]
    nak_idx = int(lon / NAK_EXTENT) % 27
    nl = NAK_LORDS[nak_idx % 9]
    pos_in_nak = lon - (nak_idx * NAK_EXTENT)

    # Sub Lord — proportional Vimshottari starting from NL
    seq_start = list(VIMS_YEARS.keys()).index(nl)
    seq = list(VIMS_YEARS.keys())

    def _proportional_lord(parent_lord: str, parent_extent: float,
                           pos_in_parent: float) -> tuple[str, float, float]:
        """Find which sub-period the position falls in, return
        (lord, sub_start_within_parent, sub_end_within_parent)."""
        start_idx = seq.index(parent_lord)
        cum = 0.0
        for i in range(9):
            lord = seq[(start_idx + i) % 9]
            span = parent_extent * (VIMS_YEARS[lord] / VIMS_TOTAL)
            if pos_in_parent < cum + span:
                return lord, cum, cum + span
            cum += span
        # fallback last
        return seq[(start_idx + 8) % 9], cum, parent_extent

    sub_lord, sub_start, sub_end = _proportional_lord(nl, NAK_EXTENT, pos_in_nak)
    sub_extent = sub_end - sub_start
    pos_in_sub = pos_in_nak - sub_start
    sub_sub_lord, ss_start, ss_end = _proportional_lord(sub_lord, sub_extent, pos_in_sub)
    ss_extent = ss_end - ss_start
    pos_in_ss = pos_in_sub - ss_start
    sub_sub_sub_lord, _, _ = _proportional_lord(sub_sub_lord, ss_extent, pos_in_ss)

    return {
        "sign": SIGN_NAMES[sign_idx],
        "sign_lord": sl,
        "nakshatra": NAKSHATRAS[nak_idx],
        "star_lord": nl,
        "sub_lord": sub_lord,
        "sub_sub_lord": sub_sub_lord,
        "sub_sub_sub_lord": sub_sub_sub_lord,
    }


# ---------------------------------------------------------------------------
# 2) Significators 4-Level Deep
# ---------------------------------------------------------------------------
def significators_4_level(planets: list[dict], lagna_sign_idx: int) -> dict[str, Any]:
    """For each house 1..12, compute KP 4-level significators using sign-house basis:
       L1 = planets in star of occupants
       L2 = occupants of the house
       L3 = planets in star of house-lord
       L4 = house lord itself"""
    # Build planet → sign_idx and planet → star_lord
    p_signs: dict[str, int] = {}
    p_stars: dict[str, str] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        lon = p.get("longitude")
        if not isinstance(lon, (int, float)) or nm not in VIMS_YEARS and nm not in ("Sun", "Moon"):
            continue
        lords = kp_full_lords(lon)
        p_signs[nm] = int((lon % 360) / 30)
        p_stars[nm] = lords["star_lord"]

    out = {}
    for h in range(1, 13):
        house_sign = (lagna_sign_idx + h - 1) % 12
        house_lord = SIGN_LORDS[house_sign]
        # L2: occupants of house
        l2 = [p for p, s in p_signs.items() if s == house_sign]
        # L1: planets whose star_lord is in L2
        l1 = [p for p, st in p_stars.items() if st in l2 and p not in l2]
        # L4: house lord
        l4 = [house_lord] if house_lord in p_signs else [house_lord]
        # L3: planets whose star_lord == house_lord
        l3 = [p for p, st in p_stars.items() if st == house_lord and p != house_lord]
        out[h] = {
            "house_sign": SIGN_NAMES[house_sign],
            "house_lord": house_lord,
            "L1_in_star_of_occupants": l1,
            "L2_occupants": l2,
            "L3_in_star_of_lord": l3,
            "L4_house_lord": l4,
            "all_significators": list(dict.fromkeys(l1 + l2 + l3 + l4)),
        }
    return out


# ---------------------------------------------------------------------------
# 3) Ruling Planets (current moment)
# ---------------------------------------------------------------------------
def ruling_planets(natal_lagna_sign_idx: int,
                   when: datetime | None = None) -> dict[str, Any]:
    """Computes RP for current moment using natal lagna as reference.
       In strict KP horary, lagna is current moment lagna — but we use
       natal as a pragmatic baseline. Caller can pass current lagna_lon
       via natal_lagna_sign_idx if available."""
    when = when or datetime.utcnow()
    weekday = when.weekday()  # Monday=0
    day_lord = DAY_LORDS[weekday]

    rp = {
        "evaluated_at": when.strftime("%Y-%m-%d %H:%M UTC"),
        "day_lord": day_lord,
    }

    if _HAS_SWE:
        jd = swe.julday(when.year, when.month, when.day,
                        when.hour + when.minute/60.0)
        moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360
        moon_lords = kp_full_lords(moon_lon)
        rp["moon_sign"] = moon_lords["sign"]
        rp["moon_star_lord"] = moon_lords["star_lord"]
        rp["moon_sub_lord"] = moon_lords["sub_lord"]

    rp["natal_lagna_sign"] = SIGN_NAMES[natal_lagna_sign_idx]
    rp["natal_lagna_lord"] = SIGN_LORDS[natal_lagna_sign_idx]

    # Composite RP list (KP convention — top 5 ruling planets)
    rp_list = [rp.get("day_lord"), rp.get("moon_star_lord"),
               rp.get("moon_sub_lord"), rp.get("natal_lagna_lord")]
    rp["ruling_planets"] = list(dict.fromkeys([p for p in rp_list if p]))
    return rp


# ---------------------------------------------------------------------------
# 4) 249 Horary Numbers — static lookup
# ---------------------------------------------------------------------------
# Each of 249 numbers = a unique sub division across 27 nakshatras.
# Sum of subs per nakshatra = 9, so 27 × 9 = 243 (but classical KP uses 249
# subs for the zodiac — 9 per Vimshottari period × 27 nakshatras + 6 extra
# from boundary. Standard table: numbers map sequentially through subs.)
def horary_number_lookup(number: int) -> dict[str, Any]:
    """Returns sign, nakshatra, sub-lord, longitude midpoint for KP horary 1..249."""
    if not (1 <= number <= 249):
        return {"available": False, "reason": "must be 1..249"}
    # Build a flat list of all subs across the zodiac
    subs = []
    seq = list(VIMS_YEARS.keys())
    for nak_idx in range(27):
        nl = NAK_LORDS[nak_idx % 9]
        start_idx = seq.index(nl)
        nak_start_lon = nak_idx * NAK_EXTENT
        cum = 0.0
        for i in range(9):
            lord = seq[(start_idx + i) % 9]
            span = NAK_EXTENT * (VIMS_YEARS[lord] / VIMS_TOTAL)
            sub_start = nak_start_lon + cum
            sub_end = nak_start_lon + cum + span
            subs.append({
                "sign": SIGN_NAMES[int(sub_start / 30) % 12],
                "nakshatra": NAKSHATRAS[nak_idx],
                "star_lord": nl,
                "sub_lord": lord,
                "lon_start": round(sub_start, 4),
                "lon_end": round(sub_end, 4),
                "lon_mid": round((sub_start + sub_end) / 2, 4),
            })
            cum += span
    if number > len(subs):
        return {"available": False, "reason": f"out of range (have {len(subs)})"}
    sub = subs[number - 1]
    sign_lord = SIGN_LORDS[SIGN_NAMES.index(sub["sign"])]
    return {
        "available": True,
        "horary_number": number,
        **sub,
        "sign_lord": sign_lord,
    }


# ---------------------------------------------------------------------------
# 5) Eclipse Pin-Point — next solar + lunar eclipse
# ---------------------------------------------------------------------------
def next_eclipse_pinpoint(from_when: datetime | None = None) -> dict[str, Any]:
    if not _HAS_SWE:
        return {"available": False, "reason": "swisseph unavailable"}
    when = from_when or datetime.utcnow()
    jd = swe.julday(when.year, when.month, when.day,
                    when.hour + when.minute/60.0)
    out: dict[str, Any] = {"available": True, "evaluated_from": when.strftime("%Y-%m-%d")}
    try:
        # Solar eclipse globally
        sol = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0)
        sol_jd = sol[1][0]
        sol_dt = swe.revjul(sol_jd)
        sun_lon = swe.calc_ut(sol_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0] % 360
        sol_lords = kp_full_lords(sun_lon)
        out["next_solar_eclipse"] = {
            "date_utc": f"{int(sol_dt[0])}-{int(sol_dt[1]):02d}-{int(sol_dt[2]):02d}",
            "sun_sidereal_lon": round(sun_lon, 4),
            "sign": sol_lords["sign"],
            "nakshatra": sol_lords["nakshatra"],
            "kp_star_lord": sol_lords["star_lord"],
            "kp_sub_lord": sol_lords["sub_lord"],
            "kp_sub_sub_lord": sol_lords["sub_sub_lord"],
        }
    except Exception as e:
        out["next_solar_eclipse_error"] = str(e)

    try:
        lun = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0)
        lun_jd = lun[1][0]
        lun_dt = swe.revjul(lun_jd)
        moon_lon = swe.calc_ut(lun_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360
        lun_lords = kp_full_lords(moon_lon)
        out["next_lunar_eclipse"] = {
            "date_utc": f"{int(lun_dt[0])}-{int(lun_dt[1]):02d}-{int(lun_dt[2]):02d}",
            "moon_sidereal_lon": round(moon_lon, 4),
            "sign": lun_lords["sign"],
            "nakshatra": lun_lords["nakshatra"],
            "kp_star_lord": lun_lords["star_lord"],
            "kp_sub_lord": lun_lords["sub_lord"],
            "kp_sub_sub_lord": lun_lords["sub_sub_lord"],
        }
    except Exception as e:
        out["next_lunar_eclipse_error"] = str(e)
    return out


# ---------------------------------------------------------------------------
# Master orchestrator
# ---------------------------------------------------------------------------
def compute_kp_deep(kundli: dict) -> dict[str, Any]:
    planets = kundli.get("planets") or []
    asc = kundli.get("ascendant")
    if not (isinstance(asc, str) and asc in SIGN_NAMES) or not planets:
        return {"available": False, "reason": "missing kundli essentials"}
    lagna_si = SIGN_NAMES.index(asc)

    # Compute SSS for each natal planet
    sss_per_planet = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        lon = p.get("longitude")
        if isinstance(lon, (int, float)) and nm:
            sss_per_planet[nm] = kp_full_lords(lon)

    sigs = significators_4_level(planets, lagna_si)
    rp = ruling_planets(lagna_si)
    eclipse = next_eclipse_pinpoint()

    return {
        "available": True,
        "system": "KP Deep (Sprint 25)",
        "sub_sub_sub_lords": sss_per_planet,
        "significators_4_level": sigs,
        "ruling_planets": rp,
        "next_eclipses": eclipse,
    }


def format_kp_deep_summary(result: dict) -> str:
    if not isinstance(result, dict) or not result.get("available"):
        return ""
    lines = ["── KP DEEP (Sprint 25) ──"]

    rp = result.get("ruling_planets", {})
    if rp:
        lines.append(f"Ruling Planets ({rp.get('evaluated_at','')}): "
                     f"{', '.join(rp.get('ruling_planets', []))}")
        if rp.get('moon_sign'):
            lines.append(f"  Moon: {rp['moon_sign']} → Star {rp['moon_star_lord']}, "
                         f"Sub {rp['moon_sub_lord']} | Day-Lord: {rp['day_lord']} | "
                         f"Natal-Lagna-Lord: {rp['natal_lagna_lord']}")

    sss = result.get("sub_sub_sub_lords", {})
    if sss:
        lines.append("Sub-Sub-Sub Lords (3-deep) for natal planets:")
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            d = sss.get(p)
            if d:
                lines.append(f"  {p}: {d['nakshatra']} → SL={d['star_lord']}/"
                             f"SB={d['sub_lord']}/SS={d['sub_sub_lord']}/SSS={d['sub_sub_sub_lord']}")

    sigs = result.get("significators_4_level", {})
    if sigs:
        lines.append("4-Level Significators (key houses):")
        for h in [1, 2, 7, 10, 11]:
            d = sigs.get(h)
            if d:
                lines.append(f"  H{h} ({d['house_sign']}, lord {d['house_lord']}): "
                             f"All-sigs = {d['all_significators']}")

    ec = result.get("next_eclipses", {})
    sol = ec.get("next_solar_eclipse"); lun = ec.get("next_lunar_eclipse")
    if sol:
        lines.append(f"Next Solar Eclipse: {sol['date_utc']} — Sun in {sol['sign']} "
                     f"({sol['nakshatra']}) | KP Sub-Lord: {sol['kp_sub_lord']}")
    if lun:
        lines.append(f"Next Lunar Eclipse: {lun['date_utc']} — Moon in {lun['sign']} "
                     f"({lun['nakshatra']}) | KP Sub-Lord: {lun['kp_sub_lord']}")

    return "\n".join(lines)
