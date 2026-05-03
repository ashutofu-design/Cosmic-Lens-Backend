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
KUNDLI_CALC_VERSION = 11

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
    planet_list = []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        plon = planet_positions[pname]
        spd  = planet_speeds.get(pname, 0)
        planet_list.append({
            "name":      pname,
            "sign":      sign_from_lon(plon),
            "degrees":   format_deg(plon),
            "house":     house_from_asc(plon, asc_lon),
            "longitude": round(plon, 4),
            "retrograde": spd < 0,
            "speed":      spd,
        })

    # ── Divisional Charts (Vargas) ───────────────────────────────────────────
    # D9 Navamsha — marriage, dharma, spouse, spiritual strength
    # D10 Dashamsha — career, profession, achievement
    def _d9_sign_idx(lon):
        # Parashari Navamsha: simple formula (108 divisions × 3°20' = 360°)
        return int((lon * 9.0) / 30.0) % 12

    def _d10_sign_idx(lon):
        # Parashari Dashamsha: odd signs start from self, even signs from 9th
        sidx = int(lon / 30.0) % 12
        pada = int((lon % 30.0) / 3.0)               # 0-9 (each 3°)
        if sidx % 2 == 0:                            # sign_index 0,2,4... = odd signs
            return (sidx + pada) % 12
        return (sidx + 8 + pada) % 12

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

    d9_chart  = _build_varga(_d9_sign_idx,  asc_lon, planet_positions)
    d10_chart = _build_varga(_d10_sign_idx, asc_lon, planet_positions)

    print(f"[VARGA] D9 Lagna : {d9_chart['ascendant']}", flush=True)
    print(f"[VARGA] D10 Lagna: {d10_chart['ascendant']}", flush=True)


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
        "divisionalCharts": {
            "D9":  d9_chart,
            "D10": d10_chart,
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
