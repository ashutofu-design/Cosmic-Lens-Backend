"""
Daily muhuratas, personal tarabala/chandrabala, and Sankranti detection.

Uses vedic.panchang.swe_core (Lahiri Swiss Ephemeris).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from vedic.panchang import swe_core
from vedic.panchang.swe_core import (
    RASHI_NAMES,
    calc_sun_moon,
    jd_from_datetime,
    local_noon_utc,
    moon_rashi_from_longitude,
    nakshatra_from_moon,
    require_swe,
    sunrise_sunset,
)
from vedic.panchang.vivah_geo import GULIKA_SEG, RAHU_SEG, YAMA_SEG
from vedic.panchang.vivah_nakshatra import chandrabal_ok, tarabala

# Re-export camelCase alias
getTarabalaAndChandrabala = None  # set after function def


def _fmt(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def _seg_period(
    label: str,
    seg_idx: int,
    sunrise: datetime,
    sunset: datetime,
) -> dict[str, Any]:
    day_seconds = max(1.0, (sunset - sunrise).total_seconds())
    seg_len = day_seconds / 8.0
    start = sunrise + timedelta(seconds=(seg_idx - 1) * seg_len)
    end = sunrise + timedelta(seconds=seg_idx * seg_len)
    return {
        "label": label,
        "start": _fmt(start),
        "end": _fmt(end),
        "start_iso": start.isoformat(),
        "end_iso": end.isoformat(),
    }


def compute_sunrise_sunset(
    target: date,
    *,
    lat: float = 28.6139,
    lng: float = 77.2090,
    tz_h: float = 5.5,
) -> dict[str, str]:
    """Exact local sunrise / sunset / solar noon for a calendar day."""
    sunrise, sunset, solar_noon = sunrise_sunset(target, lat=lat, lng=lng, tz_h=tz_h)
    return {
        "date": target.isoformat(),
        "lat": lat,
        "lng": lng,
        "tz": tz_h,
        "sunrise": _fmt(sunrise),
        "sunset": _fmt(sunset),
        "solar_noon": _fmt(solar_noon),
        "sunrise_iso": sunrise.isoformat(),
        "sunset_iso": sunset.isoformat(),
        "solar_noon_iso": solar_noon.isoformat(),
    }


def compute_day_muhuratas(
    target: date,
    *,
    lat: float = 28.6139,
    lng: float = 77.2090,
    tz_h: float = 5.5,
) -> dict[str, Any]:
    """
    Sunrise/sunset plus Rahu Kaal, Gulika, Yamaganda, Abhijit, Brahma Muhurta.
    Segments derived from computed sunrise→sunset (8 equal parts).
    """
    sunrise, sunset, solar_noon = sunrise_sunset(target, lat=lat, lng=lng, tz_h=tz_h)
    wd = target.weekday()

    rahu = _seg_period("Rahu Kaal", RAHU_SEG[wd], sunrise, sunset)
    gulika = _seg_period("Gulika Kaal", GULIKA_SEG[wd], sunrise, sunset)
    yama = _seg_period("Yamaganda", YAMA_SEG[wd], sunrise, sunset)

    abhijit_start = solar_noon - timedelta(minutes=24)
    abhijit_end = solar_noon + timedelta(minutes=24)
    brahma_start = sunrise - timedelta(minutes=96)
    brahma_end = sunrise - timedelta(minutes=48)

    return {
        "date": target.isoformat(),
        "lat": lat,
        "lng": lng,
        "tz": tz_h,
        "ephemeris": "swisseph_lahiri_sidereal",
        "sunrise": _fmt(sunrise),
        "sunset": _fmt(sunset),
        "solar_noon": _fmt(solar_noon),
        "brahma_muhurta": {
            "start": _fmt(brahma_start),
            "end": _fmt(brahma_end),
        },
        "abhijit_muhurat": {
            "start": _fmt(abhijit_start),
            "end": _fmt(abhijit_end),
            "note": "Solar noon ± 24 min (48-min muhurta)",
        },
        "rahu_kaal": rahu,
        "gulika_kaal": gulika,
        "yamaghanta": yama,
        # legacy string fields
        "rahu_kaal_str": f"{rahu['start']} – {rahu['end']}",
        "gulika": f"{gulika['start']} – {gulika['end']}",
        "abhijit_muhurta_str": f"{_fmt(abhijit_start)} – {_fmt(abhijit_end)}",
    }


def get_tarabala_and_chandrabala(
    natal_moon_sign: str,
    natal_nakshatra: str,
    transit_date: date,
    *,
    tz_h: float = 5.5,
) -> dict[str, Any]:
    """
    Personal daily strength from natal Moon sign/nakshatra vs transit Moon.
    Computes transit nakshatra & rashi from Swiss Ephemeris at local noon.
    """
    require_swe()
    if isinstance(transit_date, datetime):
        transit_date = transit_date.date()

    dt_utc = local_noon_utc(transit_date, tz_h)
    jd = jd_from_datetime(dt_utc)
    _, moon_lon = calc_sun_moon(jd)
    transit_nak = nakshatra_from_moon(moon_lon)["name"]
    transit_rashi = moon_rashi_from_longitude(moon_lon)

    tb = tarabala(natal_nakshatra, transit_nak)
    cb = chandrabal_ok(natal_moon_sign, transit_rashi)

    score = 50
    if tb["ok"]:
        score += 25
    else:
        score -= 20
    if cb["ok"]:
        score += 25
    else:
        score -= 20
    score = max(5, min(95, score))

    if score >= 75:
        band = "Shubh"
    elif score >= 45:
        band = "Mishrit"
    else:
        band = "Ashubh"

    return {
        "date": transit_date.isoformat(),
        "natal_moon_sign": natal_moon_sign,
        "natal_nakshatra": natal_nakshatra,
        "transit_moon_sign": transit_rashi,
        "transit_nakshatra": transit_nak,
        "tarabala": tb,
        "chandrabala": cb,
        "overall_ok": tb["ok"] and cb["ok"],
        "strength_score": score,
        "strength_band": band,
    }


getTarabalaAndChandrabala = get_tarabala_and_chandrabala


def detect_sankrantis(
    start: date,
    end: date,
    *,
    tz_h: float = 5.5,
) -> list[dict[str, Any]]:
    """
    Detect Sun sign (Sankranti) boundary crossings between start and end (inclusive).
    Uses noon samples then refines crossing to ~minute precision.
    """
    require_swe()
    events: list[dict[str, Any]] = []
    prev_jd = jd_from_datetime(local_noon_utc(start, tz_h))
    prev_sun, _ = calc_sun_moon(prev_jd)
    prev_sign = int(prev_sun // 30) % 12

    d = start + timedelta(days=1)
    while d <= end:
        jd = jd_from_datetime(local_noon_utc(d, tz_h))
        sun, _ = calc_sun_moon(jd)
        sign = int(sun // 30) % 12
        if sign != prev_sign:
            # refine between previous day noon and this day noon
            lo_jd = prev_jd
            hi_jd = jd
            for _ in range(28):
                mid = (lo_jd + hi_jd) / 2.0
                mid_sun, _ = calc_sun_moon(mid)
                mid_sign = int(mid_sun // 30) % 12
                if mid_sign == prev_sign:
                    lo_jd = mid
                else:
                    hi_jd = mid
            cross_jd = hi_jd
            cross_local = swe_core.jd_to_local_datetime(cross_jd, tz_h)
            events.append({
                "date": cross_local.date().isoformat(),
                "datetime_local": cross_local.isoformat(),
                "from_rashi": RASHI_NAMES[prev_sign],
                "to_rashi": RASHI_NAMES[sign],
                "from_longitude": round(prev_sign * 30.0, 4),
                "to_longitude": round(sign * 30.0, 4),
                "sankranti": f"{RASHI_NAMES[sign]} Sankranti",
            })
            prev_sign = sign
        prev_jd = jd
        d += timedelta(days=1)

    return events


def sankranti_on_date(
    target: date,
    *,
    tz_h: float = 5.5,
) -> dict[str, Any] | None:
    """Return Sankranti event if Sun crosses a 30° boundary on this calendar day."""
    prev = target - timedelta(days=1)
    hits = detect_sankrantis(prev, target, tz_h=tz_h)
    for ev in hits:
        if ev["date"] == target.isoformat():
            return ev
    return None
