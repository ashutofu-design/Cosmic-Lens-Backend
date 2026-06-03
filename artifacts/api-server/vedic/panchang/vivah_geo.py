"""Geo-specific sunrise/sunset and inauspicious daytime periods (Swiss Ephemeris)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from vedic.panchang.swe_core import SWE_OK as _SWE_OK, sunrise_sunset as _sunrise_sunset_swe

RAHU_SEG = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_SEG = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULIKA_SEG = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}


@dataclass
class TimePeriod:
    label: str
    start: datetime
    end: datetime

    def contains(self, dt: datetime) -> bool:
        return self.start <= dt < self.end

    def overlaps(self, a: datetime, b: datetime) -> bool:
        return a < self.end and b > self.start

    def to_display(self) -> str:
        return f"{_fmt(self.start)} – {_fmt(self.end)}"


@dataclass
class DayGeo:
    d: date
    lat: float
    lng: float
    tz_h: float
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime
    rahu: TimePeriod
    yama: TimePeriod
    gulika: TimePeriod
    dur_start: datetime
    dur_end: datetime


def _fmt(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def _seg_period(
    label: str,
    seg_idx: int,
    sunrise: datetime,
    sunset: datetime,
) -> TimePeriod:
    day_seconds = max(1.0, (sunset - sunrise).total_seconds())
    seg_len = day_seconds / 8.0
    start = sunrise + timedelta(seconds=(seg_idx - 1) * seg_len)
    end = sunrise + timedelta(seconds=seg_idx * seg_len)
    return TimePeriod(label=label, start=start, end=end)


def compute_day_geo(
    target: date,
    *,
    lat: float = 28.6139,
    lng: float = 77.2090,
    tz_h: float = 5.5,
) -> DayGeo:
    """Local sunrise/sunset and Rahu/Yama/Gulika for a calendar day."""
    if _SWE_OK:
        try:
            sunrise, sunset, solar_noon = _sunrise_sunset_swe(
                target, lat=lat, lng=lng, tz_h=tz_h
            )
        except Exception:
            sunrise = datetime(target.year, target.month, target.day, 6, 14)
            sunset = datetime(target.year, target.month, target.day, 18, 47)
            solar_noon = sunrise + (sunset - sunrise) / 2
    else:
        sunrise = datetime(target.year, target.month, target.day, 6, 14)
        sunset = datetime(target.year, target.month, target.day, 18, 47)
        solar_noon = sunrise + (sunset - sunrise) / 2
    wd = target.weekday()
    rahu = _seg_period("Rahu Kaal", RAHU_SEG[wd], sunrise, sunset)
    yama = _seg_period("Yamaganda", YAMA_SEG[wd], sunrise, sunset)
    gulika = _seg_period("Gulika Kaal", GULIKA_SEG[wd], sunrise, sunset)
    dur_start = sunset - timedelta(minutes=30)
    dur_end = sunset - timedelta(minutes=24)

    return DayGeo(
        d=target,
        lat=lat,
        lng=lng,
        tz_h=tz_h,
        sunrise=sunrise,
        sunset=sunset,
        solar_noon=solar_noon,
        rahu=rahu,
        yama=yama,
        gulika=gulika,
        dur_start=dur_start,
        dur_end=dur_end,
    )


def local_to_phase_utc(dt_local: datetime, tz_h: float) -> datetime:
    return dt_local - timedelta(hours=tz_h)


def inauspicious_periods(geo: DayGeo) -> list[TimePeriod]:
    return [geo.rahu, geo.yama, geo.gulika, TimePeriod("Dur Muhurat", geo.dur_start, geo.dur_end)]


def slot_overlaps_inauspicious(geo: DayGeo, start: datetime, end: datetime) -> list[str]:
    hits: list[str] = []
    for p in inauspicious_periods(geo):
        if p.overlaps(start, end):
            hits.append(p.label)
    return hits
