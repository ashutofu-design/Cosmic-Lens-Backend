"""
Swiss Ephemeris (Lahiri sidereal) marriage-date engine.

Public API:
  generate_marriage_dates(start_date) -> list[dict]

Filters (classical vivah panchang):
  Step 1 — 5-anga from Sun/Moon longitudes (tithi, nakshatra, yoga, karana)
  Step 2 — Guru/Shukra combustion (asta) from angular separation with Sun
  Step 3 — Solar sign windows (exclude Chaturmas & non-vivah saur maas)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, TypedDict

from dateutil.relativedelta import relativedelta

from vedic.panchang.swe_core import (
    SWE_OK as _SWE_OK,
    angular_sep,
    calc_sun_moon,
    jd_from_datetime,
    local_noon_utc,
    require_swe,
)
from vedic.panchang.phase_r import (
    KARANA_NAMES,
    NAK_NAMES,
    TITHI_NAMES,
    WEEKDAY_NAME,
    YOGA_NAMES,
)

# ── Step 1 constants ─────────────────────────────────────────────────────────
ALLOWED_TITHI_NUM = frozenset({2, 3, 5, 7, 10, 11, 12})
RIKTA_TITHI_NUM = frozenset({4, 9, 14})
EXCLUDED_TITHI_NUM = frozenset({1}) | RIKTA_TITHI_NUM  # + Amavasya handled separately

ALLOWED_NAK_IDX = frozenset({3, 4, 11, 12, 14, 16, 20, 21, 22, 25, 26})
MALEFIC_YOGAS = frozenset({"Vyatipata", "Vaidhriti"})

# ── Step 2 combustion orbs (degrees) ─────────────────────────────────────────
JUP_COMB_ORB = 11.0
VEN_COMB_ORB = 10.0

# ── Step 3 solar longitude windows (sidereal degrees) ────────────────────────
# Allowed: Mesha–Mithuna [0,90), Vrishchika [210,240), Makara–Kumbha [270,330)
# Blocked: Chaturmas [90,210), Dhanu [240,270), Meena [330,360)

_SUN_MEAN_DEG_PER_DAY = 0.9856
_NAK_SEG = 360.0 / 27.0
_TITHI_DEG = 12.0

DEFAULT_TZ_H = 5.5
SCAN_YEARS = 5


class MarriageDateRow(TypedDict, total=False):
    date: str
    display: str
    weekday: str
    tithi: str
    nakshatra: str
    jupiter_status: str
    venus_status: str


def _jd_local_noon(d: date, tz_h: float) -> float:
    return jd_from_datetime(local_noon_utc(d, tz_h))


def _calc_longitudes(jd: float) -> tuple[float, float, float, float]:
    from vedic.panchang.swe_core import calc_longitude

    sun, moon = calc_sun_moon(jd)
    jup, _ = calc_longitude(jd, "jupiter")
    ven, _ = calc_longitude(jd, "venus")
    return sun, moon, jup, ven


def _sun_longitude_allowed(sun_lon: float) -> bool:
    if 0.0 <= sun_lon < 90.0:
        return True
    if 210.0 <= sun_lon < 240.0:
        return True
    if 270.0 <= sun_lon < 330.0:
        return True
    return False


def _days_until_sun_longitude(sun_lon: float, target_lon: float) -> int:
    """Forward days until Sun reaches target_lon (mod 360), for skip optimization."""
    cur = sun_lon % 360.0
    tgt = target_lon % 360.0
    if tgt <= cur:
        delta = (360.0 - cur) + tgt
    else:
        delta = tgt - cur
    return max(1, int(delta / _SUN_MEAN_DEG_PER_DAY) + 1)


def _skip_days_for_sun_block(sun_lon: float) -> int:
    """Skip ahead across long blocked solar stretches (Chaturmas, Dhanu, Meena)."""
    lon = sun_lon % 360.0
    if 90.0 <= lon < 210.0:
        return _days_until_sun_longitude(lon, 210.0)
    if 240.0 <= lon < 270.0:
        return _days_until_sun_longitude(lon, 270.0)
    if 330.0 <= lon < 360.0:
        return _days_until_sun_longitude(lon, 360.0)
    return 1


def _combust_status(sun_lon: float, planet_lon: float, orb: float) -> str:
    return "Asta" if angular_sep(planet_lon, sun_lon) <= orb else "Uday"


def _panchang_anga(sun_lon: float, moon_lon: float) -> dict[str, Any]:
    """5-anga from ephemeris longitudes (matches phase_r / Lahiri)."""
    tithi_arc = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(tithi_arc // _TITHI_DEG)  # 0..29
    paksha = "Shukla" if tithi_idx < 15 else "Krishna"
    loc_idx = tithi_idx % 15
    tithi_num = loc_idx + 1

    if tithi_idx == 29:
        tithi_name = "Amavasya"
    elif tithi_idx == 14:
        tithi_name = "Purnima"
    else:
        tithi_name = TITHI_NAMES[loc_idx]

    nak_idx = int(moon_lon / _NAK_SEG)
    if nak_idx > 26:
        nak_idx = 26
    nak_name = NAK_NAMES[nak_idx]

    yoga_arc = (sun_lon + moon_lon) % 360.0
    yoga_idx = int(yoga_arc / _NAK_SEG)
    if yoga_idx > 26:
        yoga_idx = 26
    yoga_name = YOGA_NAMES[yoga_idx]

    karana_pos = int(tithi_arc / 6.0)
    if karana_pos == 0:
        karana_name = "Kimstughna"
    elif karana_pos >= 57:
        ki = karana_pos - 57 + 7
        karana_name = KARANA_NAMES[ki + 1]
    else:
        ki = (karana_pos - 1) % 7
        karana_name = KARANA_NAMES[ki]

    return {
        "tithi_idx": tithi_idx,
        "tithi_num": tithi_num,
        "tithi_name": tithi_name,
        "paksha": paksha,
        "nak_idx": nak_idx,
        "nak_name": nak_name,
        "yoga_name": yoga_name,
        "karana_name": karana_name,
        "tithi_label": f"{paksha} {tithi_name}",
    }


def _step1_passes(anga: dict[str, Any]) -> bool:
    if anga["tithi_idx"] == 29:
        return False
    if anga["tithi_num"] in EXCLUDED_TITHI_NUM:
        return False
    if anga["tithi_num"] not in ALLOWED_TITHI_NUM:
        return False
    if anga["nak_idx"] not in ALLOWED_NAK_IDX:
        return False
    kn = (anga["karana_name"] or "").lower()
    if "vishti" in kn or "bhadra" in kn:
        return False
    if anga["yoga_name"] in MALEFIC_YOGAS:
        return False
    return True


def _step2_passes(sun_lon: float, jup_lon: float, ven_lon: float) -> tuple[bool, str, str]:
    jup_st = _combust_status(sun_lon, jup_lon, JUP_COMB_ORB)
    ven_st = _combust_status(sun_lon, ven_lon, VEN_COMB_ORB)
    ok = jup_st == "Uday" and ven_st == "Uday"
    return ok, jup_st, ven_st


def generate_marriage_dates(
    start_date: date,
    *,
    tz_h: float = DEFAULT_TZ_H,
    years: int = SCAN_YEARS,
) -> list[MarriageDateRow]:
    """
    Return all valid vivah dates from start_date through start_date + years.

    Uses Swiss Ephemeris (Lahiri) at local noon — same setup as kundli_engine /
    vivah_planets / phase_r.
    """
    require_swe()

    if isinstance(start_date, datetime):
        start_date = start_date.date()

    end_date = start_date + relativedelta(years=years)
    results: list[MarriageDateRow] = []
    d = start_date

    while d < end_date:
        jd = _jd_local_noon(d, tz_h)
        sun_lon, moon_lon, jup_lon, ven_lon = _calc_longitudes(jd)

        if not _sun_longitude_allowed(sun_lon):
            d += timedelta(days=_skip_days_for_sun_block(sun_lon))
            continue

        jup_st = _combust_status(sun_lon, jup_lon, JUP_COMB_ORB)
        ven_st = _combust_status(sun_lon, ven_lon, VEN_COMB_ORB)
        if jup_st != "Uday" or ven_st != "Uday":
            d += timedelta(days=1)
            continue

        anga = _panchang_anga(sun_lon, moon_lon)
        if not _step1_passes(anga):
            d += timedelta(days=1)
            continue

        results.append(
            {
                "date": d.isoformat(),
                "display": d.strftime("%d %b"),
                "weekday": WEEKDAY_NAME[d.weekday()],
                "tithi": anga["tithi_label"],
                "nakshatra": anga["nak_name"],
                "jupiter_status": jup_st,
                "venus_status": ven_st,
            }
        )
        d += timedelta(days=1)

    return results


# CamelCase alias for API consumers
generateMarriageDates = generate_marriage_dates
