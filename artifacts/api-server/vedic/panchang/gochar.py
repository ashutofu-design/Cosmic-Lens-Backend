"""
Live Planetary Gochar (Transit) engine — Lahiri sidereal longitudes.

Uses vedic.panchang.swe_core (single Swiss Ephemeris init).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from vedic.panchang.swe_core import (
    COMBUST_ORBS_DEG,
    SWE_OK,
    calc_ketu_longitude,
    calc_longitude,
    combust_status,
    jd_from_datetime,
    longitude_to_rashi_parts,
    require_swe,
)

_GOCHAR_KEYS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
)


def _planet_row(
    key: str,
    lon: float,
    speed: float,
    sun_lon: float | None = None,
) -> dict[str, Any]:
    parts = longitude_to_rashi_parts(lon)
    retro = speed < 0.0 if key not in ("sun", "moon", "rahu", "ketu") else False
    # Rahu/Ketu: mean node — treat retro as False (nodes move backward always)
    if key in ("rahu", "ketu"):
        retro = True

    row: dict[str, Any] = {
        "rashi": parts["rashi"],
        "rashi_index": parts["rashi_index"],
        "degree": parts["degree"],
        "degree_int": parts["degree_int"],
        "minute": parts["minute"],
        "second": parts["second"],
        "absolute_longitude": parts["absolute_longitude"],
        "is_retrograde": retro,
        "motion": "Vakri" if retro else "Direct",
        "speed_deg_per_day": round(speed, 6),
    }

    if key in COMBUST_ORBS_DEG and sun_lon is not None:
        st = combust_status(sun_lon, lon, COMBUST_ORBS_DEG[key])
        row["status"] = st
    return row


def get_current_gochar(
    timestamp: datetime | None = None,
    *,
    lat: float = 28.6139,
    lng: float = 77.2090,
    tz_h: float = 5.5,
) -> dict[str, Any]:
    """
    Real-time (or requested) planetary transits in Nirayana zodiac.

    Returns:
      { timestamp, lat, lng, tz, ephemeris, planets: { sun: {...}, jupiter: {...}, ... } }
    """
    require_swe()

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

    # Interpret naive timestamp as local civil time in tz_h
    if timestamp.tzinfo is not None:
        ts_local = timestamp.astimezone(timezone(timedelta(hours=tz_h))).replace(tzinfo=None)
    else:
        ts_local = timestamp

    dt_utc = ts_local - timedelta(hours=tz_h)
    jd = jd_from_datetime(dt_utc)

    sun_lon, sun_spd = calc_longitude(jd, "sun", with_speed=True)
    planets: dict[str, Any] = {
        "sun": _planet_row("sun", sun_lon, sun_spd),
    }

    for key in ("moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu"):
        lon, spd = calc_longitude(jd, key, with_speed=True)
        planets[key] = _planet_row(key, lon, spd, sun_lon=sun_lon)

    ketu_lon = calc_ketu_longitude(jd)
    _, rahu_spd = calc_longitude(jd, "rahu", with_speed=True)
    planets["ketu"] = _planet_row("ketu", ketu_lon, -rahu_spd, sun_lon=sun_lon)

    return {
        "timestamp": ts_local.isoformat(),
        "lat": lat,
        "lng": lng,
        "tz": tz_h,
        "ephemeris": "swisseph_lahiri_sidereal",
        "planets": planets,
    }


getCurrentGochar = get_current_gochar
