"""
Dynamic Festival & Vrat engine — Tithi / paksha triggers from Swiss Ephemeris Panchang.

Uses swe_core + phase_r lunar month for Shivratri marking.
"""
from __future__ import annotations

import calendar
from datetime import date
from typing import Any, Literal

from vedic.panchang.phase_r import compute_phase_r
from vedic.panchang.swe_core import (
    require_swe,
    sunrise_sunset,
    tithi_from_longitudes,
)
from vedic.panchang.vivah_geo import local_to_phase_utc

DEFAULT_LAT = 28.6139
DEFAULT_LNG = 77.2090

Paksha = Literal["Shukla", "Krishna"]

# Tithi index 1..30 (classical lunar day numbering)
_EKADASHI = frozenset({11, 26})
_PRADOSH = frozenset({13, 28})
_PURNIMA = 15
_AMAVASYA = 30
_SANKASHTI = frozenset({19})
_SHIVRATRI = frozenset({29})


def _festival_flags(tithi_1to30: int, paksha: str, maasa: str | None) -> list[tuple[str, str]]:
    """Return list of (festival_name, paksha) for a tithi."""
    out: list[tuple[str, str]] = []
    p: Paksha = "Shukla" if paksha == "Shukla" else "Krishna"

    if tithi_1to30 in _EKADASHI:
        label = "Shukla Ekadashi Vrat" if tithi_1to30 == 11 else "Krishna Ekadashi Vrat"
        out.append((label, p))

    if tithi_1to30 in _PRADOSH:
        label = "Shukla Pradosh Vrat" if tithi_1to30 == 13 else "Krishna Pradosh Vrat"
        out.append((label, p))

    if tithi_1to30 == _PURNIMA:
        out.append(("Purnima", p))
    if tithi_1to30 == _AMAVASYA:
        out.append(("Amavasya", p))

    if tithi_1to30 in _SANKASHTI:
        out.append(("Sankashti Chaturthi", p))

    if tithi_1to30 in _SHIVRATRI:
        if maasa and maasa.lower() in ("phalguna", "phalgun"):
            out.append(("Maha Shivratri", p))
        else:
            out.append(("Monthly Shivratri", p))

    return out


def _tithi_at_sunrise(
    target: date,
    *,
    lat: float = DEFAULT_LAT,
    lng: float = DEFAULT_LNG,
    tz_h: float = 5.5,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Panchang tithi at local sunrise (standard for vrat / festival day)."""
    require_swe()
    sunrise, _, _ = sunrise_sunset(target, lat=lat, lng=lng, tz_h=tz_h)
    dt_utc = local_to_phase_utc(sunrise, tz_h)
    phase = compute_phase_r(dt_utc)
    if "r1_tithi" not in phase:
        raise RuntimeError("phase_r tithi unavailable")
    t_meta = phase["r1_tithi"]
    idx30 = int(t_meta["tithi_idx_1to30"])
    t = {
        "tithi_idx_1to30": idx30,
        "tithi_num": (idx30 - 1) % 15 + 1,
        "paksha": t_meta.get("paksha") or "Shukla",
        "name": t_meta.get("name") or "",
        "label": f"{t_meta.get('paksha', '')} {t_meta.get('name', '')}".strip(),
    }
    return t, phase


def festivals_on_date(
    target: date,
    *,
    lat: float = DEFAULT_LAT,
    lng: float = DEFAULT_LNG,
    tz_h: float = 5.5,
) -> list[dict[str, Any]]:
    """All festival/vrat flags for a calendar day (tithi at local sunrise)."""
    require_swe()
    t, phase = _tithi_at_sunrise(target, lat=lat, lng=lng, tz_h=tz_h)
    maasa = None
    if "r6_ritu_ayana_maasa" in phase:
        maasa = phase["r6_ritu_ayana_maasa"].get("maasa")

    rows: list[dict[str, Any]] = []
    for name, paksha in _festival_flags(t["tithi_idx_1to30"], t["paksha"], maasa):
        rows.append({
            "date": target.isoformat(),
            "festival_name": name,
            "tithi": t["tithi_idx_1to30"],
            "paksha": paksha,
            "tithi_label": t["label"],
            "maasa": maasa,
        })
    return rows


def get_monthly_festivals(
    month: int,
    year: int,
    *,
    lat: float = DEFAULT_LAT,
    lng: float = DEFAULT_LNG,
    tz_h: float = 5.5,
) -> list[dict[str, Any]]:
    """
    Scan every day in month/year; return festival/vrat events.

    Output: [{ date, festival_name, tithi, paksha }, ...]
    """
    require_swe()
    if month < 1 or month > 12:
        raise ValueError("month must be 1..12")

    last_day = calendar.monthrange(year, month)[1]
    all_rows: list[dict[str, Any]] = []

    for day in range(1, last_day + 1):
        d = date(year, month, day)
        for row in festivals_on_date(d, lat=lat, lng=lng, tz_h=tz_h):
            all_rows.append({
                "date": row["date"],
                "festival_name": row["festival_name"],
                "tithi": row["tithi"],
                "paksha": row["paksha"],
            })

    return all_rows


def get_ekadashi_schedule(
    start: date,
    *,
    years: int = 5,
    lat: float = DEFAULT_LAT,
    lng: float = DEFAULT_LNG,
    tz_h: float = 5.5,
) -> dict[str, Any]:
    """
    Ekadashi vrat dates from start through start + years, grouped by civil month.
    Only Shukla / Krishna Ekadashi (tithi 11 & 26).
    """
    from dateutil.relativedelta import relativedelta

    from vedic.panchang.phase_r import WEEKDAY_NAME

    require_swe()
    if isinstance(start, str):
        start = date.fromisoformat(start)
    years = max(1, min(5, int(years)))
    end = start + relativedelta(years=years)

    months_out: list[dict[str, Any]] = []
    cur = date(start.year, start.month, 1)

    while cur < end:
        rows = get_monthly_festivals(cur.month, cur.year, lat=lat, lng=lng, tz_h=tz_h)
        ek_dates: list[dict[str, Any]] = []
        for r in rows:
            if "Ekadashi" not in r.get("festival_name", ""):
                continue
            d = date.fromisoformat(r["date"])
            if d < start or d >= end:
                continue
            ek_dates.append({
                "date": r["date"],
                "display": d.strftime("%d %b"),
                "weekday": WEEKDAY_NAME[d.weekday()],
                "festival_name": r["festival_name"],
                "paksha": r["paksha"],
                "tithi": r["tithi"],
            })
        months_out.append({
            "year": cur.year,
            "month": cur.month,
            "month_key": f"{cur.year}-{cur.month:02d}",
            "label": cur.strftime("%B %Y"),
            "dates": ek_dates,
            "count": len(ek_dates),
        })
        cur += relativedelta(months=1)

    total = sum(m["count"] for m in months_out)
    return {
        "scan_from": start.isoformat(),
        "scan_years": years,
        "scan_to": end.isoformat(),
        "total": total,
        "months": months_out,
    }


getEkadashiSchedule = get_ekadashi_schedule

# CamelCase alias
getMonthlyFestivals = get_monthly_festivals
