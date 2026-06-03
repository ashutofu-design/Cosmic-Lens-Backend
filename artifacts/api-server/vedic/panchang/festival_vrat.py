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
    calc_sun_moon,
    jd_from_datetime,
    local_noon_utc,
    require_swe,
    tithi_from_longitudes,
)

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


def festivals_on_date(
    target: date,
    *,
    tz_h: float = 5.5,
) -> list[dict[str, Any]]:
    """All festival/vrat flags for a single calendar day (local noon tithi)."""
    require_swe()
    dt_utc = local_noon_utc(target, tz_h)
    jd = jd_from_datetime(dt_utc)
    sun, moon = calc_sun_moon(jd)
    t = tithi_from_longitudes(sun, moon)
    phase = compute_phase_r(dt_utc)
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
        for row in festivals_on_date(d, tz_h=tz_h):
            all_rows.append({
                "date": row["date"],
                "festival_name": row["festival_name"],
                "tithi": row["tithi"],
                "paksha": row["paksha"],
            })

    return all_rows


# CamelCase alias
getMonthlyFestivals = get_monthly_festivals
