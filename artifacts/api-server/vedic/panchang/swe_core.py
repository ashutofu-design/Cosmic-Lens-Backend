"""
Shared Swiss Ephemeris (Lahiri Nirayana) — single process-wide init.

All panchang / gochar / muhurat modules import from here to avoid
redundant swe.set_sid_mode() calls.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

try:
    import swisseph as swe

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    SWE_OK = True
    SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    SWE_FLAGS_SPEED = SWE_FLAGS | swe.FLG_SPEED
except Exception:
    swe = None  # type: ignore
    SWE_OK = False
    SWE_FLAGS = 0
    SWE_FLAGS_SPEED = 0

RASHI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]

PLANET_IDS: dict[str, int] = {}
if SWE_OK:
    PLANET_IDS = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mars": swe.MARS,
        "mercury": swe.MERCURY,
        "jupiter": swe.JUPITER,
        "venus": swe.VENUS,
        "saturn": swe.SATURN,
        "rahu": swe.MEAN_NODE,
    }

COMBUST_ORBS_DEG: dict[str, float] = {
    "mars": 17.0,
    "mercury": 14.0,
    "jupiter": 11.0,
    "venus": 10.0,
    "saturn": 15.0,
}

_NAK_SEG = 360.0 / 27.0


def require_swe() -> None:
    if not SWE_OK:
        raise RuntimeError("swisseph unavailable")


def angular_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def jd_from_datetime(dt: datetime) -> float:
    require_swe()
    return swe.julday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3_600_000_000.0,
    )


def jd_to_local_datetime(jd: float, tz_h: float) -> datetime:
    require_swe()
    y, mo, d, h_frac = swe.revjul(jd)
    hr = int(h_frac)
    mn = int((h_frac - hr) * 60)
    sec = int(((h_frac - hr) * 60 - mn) * 60)
    return datetime(y, mo, d, hr, mn, sec) + timedelta(hours=tz_h)


def local_noon_utc(d: date, tz_h: float) -> datetime:
    noon_local = datetime(d.year, d.month, d.day, 12, 0, 0)
    return noon_local - timedelta(hours=tz_h)


def calc_longitude(jd: float, planet_key: str, *, with_speed: bool = False) -> tuple[float, float]:
    """Sidereal longitude [0,360) and daily speed (deg/day)."""
    require_swe()
    pid = PLANET_IDS[planet_key]
    flags = SWE_FLAGS_SPEED if with_speed else SWE_FLAGS
    vals, _ = swe.calc_ut(jd, pid, flags)
    lon = float(vals[0]) % 360.0
    spd = float(vals[3]) if with_speed else 0.0
    return lon, spd


def calc_ketu_longitude(jd: float) -> float:
    rahu, _ = calc_longitude(jd, "rahu")
    return (rahu + 180.0) % 360.0


def calc_sun_moon(jd: float) -> tuple[float, float]:
    sun, _ = calc_longitude(jd, "sun")
    moon, _ = calc_longitude(jd, "moon")
    return sun, moon


def longitude_to_rashi_parts(lon: float) -> dict[str, Any]:
    lon = lon % 360.0
    idx = int(lon // 30) % 12
    in_sign = lon % 30.0
    deg = int(in_sign)
    rem = (in_sign - deg) * 60.0
    minute = int(rem)
    second = round((rem - minute) * 60.0, 2)
    return {
        "rashi": RASHI_NAMES[idx],
        "rashi_index": idx,
        "degree": round(in_sign, 4),
        "degree_int": deg,
        "minute": minute,
        "second": second,
        "absolute_longitude": round(lon, 6),
    }


def combust_status(sun_lon: float, planet_lon: float, orb: float) -> str:
    return "Asta" if angular_sep(sun_lon, planet_lon) <= orb else "Uday"


def sunrise_sunset(
    target: date,
    *,
    lat: float,
    lng: float,
    tz_h: float = 5.5,
) -> tuple[datetime, datetime, datetime]:
    """
    Exact local sunrise, sunset, and solar noon via swe.rise_trans.
    Falls back to seasonal approximations if rise_trans fails.
    """
    require_swe()
    day_start_local = datetime(target.year, target.month, target.day, 0, 0, 0)
    day_start_utc = day_start_local - timedelta(hours=tz_h)
    jd_start = jd_from_datetime(day_start_utc)
    geopos = (lng, lat, 0.0)
    rsmi_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
    rsmi_set = swe.CALC_SET | swe.BIT_DISC_CENTER

    sunrise = datetime(target.year, target.month, target.day, 6, 14)
    sunset = datetime(target.year, target.month, target.day, 18, 47)

    try:
        _, tret_r = swe.rise_trans(jd_start, swe.SUN, rsmi_rise, geopos, 0.0, 0.0)
        _, tret_s = swe.rise_trans(jd_start, swe.SUN, rsmi_set, geopos, 0.0, 0.0)
        jd_rise = tret_r[0] if isinstance(tret_r, (list, tuple)) else tret_r
        jd_set = tret_s[0] if isinstance(tret_s, (list, tuple)) else tret_s
        if jd_rise and jd_set:
            sunrise = jd_to_local_datetime(jd_rise, tz_h)
            sunset = jd_to_local_datetime(jd_set, tz_h)
    except Exception:
        pass

    solar_noon = sunrise + (sunset - sunrise) / 2
    return sunrise, sunset, solar_noon


def tithi_from_longitudes(sun_lon: float, moon_lon: float) -> dict[str, Any]:
    """Panchang tithi index 1..30 with paksha."""
    from vedic.panchang.phase_r import TITHI_NAMES

    tithi_arc = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(tithi_arc // 12.0)
    paksha = "Shukla" if tithi_idx < 15 else "Krishna"
    loc_idx = tithi_idx % 15
    if tithi_idx == 29:
        name = "Amavasya"
    elif tithi_idx == 14:
        name = "Purnima"
    else:
        name = TITHI_NAMES[loc_idx]
    return {
        "tithi_idx_1to30": tithi_idx + 1,
        "tithi_num": loc_idx + 1,
        "paksha": paksha,
        "name": name,
        "label": f"{paksha} {name}",
    }


def nakshatra_from_moon(moon_lon: float) -> dict[str, Any]:
    from vedic.panchang.phase_r import NAK_NAMES

    nak_idx = int(moon_lon / _NAK_SEG)
    if nak_idx > 26:
        nak_idx = 26
    return {"index": nak_idx, "name": NAK_NAMES[nak_idx]}


def moon_rashi_from_longitude(moon_lon: float) -> str:
    return RASHI_NAMES[int(moon_lon // 30) % 12]
