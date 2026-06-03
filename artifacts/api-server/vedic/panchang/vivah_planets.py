"""Planetary states for vivah filtering — retrograde, combustion, eclipses."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from vedic.panchang.swe_core import (
    COMBUST_ORBS_DEG,
    SWE_OK as _SWE_OK,
    angular_sep,
    calc_sun_moon,
    combust_status,
    jd_from_datetime,
)

JUP_COMB_ORB = COMBUST_ORBS_DEG["jupiter"]
VEN_COMB_ORB = COMBUST_ORBS_DEG["venus"]
ECLIPSE_PROX_DAYS = 3


def _eclipse_near_date(d: date, tz_h: float) -> bool:
    """True if solar or lunar eclipse within ±ECLIPSE_PROX_DAYS."""
    if not _SWE_OK:
        return False
    try:
        import swisseph as swe

        noon = datetime(d.year, d.month, d.day, 12, 0) - timedelta(hours=tz_h)
        jd = jd_from_datetime(noon)
        for func in (swe.sol_eclipse_when_glob, swe.lun_eclipse_when):
            try:
                ret = func(jd - ECLIPSE_PROX_DAYS, swe.FLG_SWIEPH, 0, backwards=True)
                tret = ret[1] if isinstance(ret, (list, tuple)) and len(ret) > 1 else ret
                ejd = tret[0] if isinstance(tret, (list, tuple)) else tret
                if ejd and abs(ejd - jd) <= ECLIPSE_PROX_DAYS + 0.5:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def day_planetary_flags(d: date, tz_h: float) -> dict[str, Any]:
    """Guru/Shukra asta and eclipse checks for a calendar day."""
    noon = datetime(d.year, d.month, d.day, 12, 0)
    if not _SWE_OK:
        return {
            "guru_ast": False, "shukra_ast": False,
            "guru_retro": False, "shukra_retro": False,
            "eclipse_risk": False, "notes": [],
        }

    dt_utc = noon - timedelta(hours=tz_h)
    jd = jd_from_datetime(dt_utc)
    from vedic.panchang.swe_core import calc_longitude

    sun_lon, _ = calc_sun_moon(jd)
    jup_lon, jup_spd = calc_longitude(jd, "jupiter", with_speed=True)
    ven_lon, ven_spd = calc_longitude(jd, "venus", with_speed=True)

    guru_retro = jup_spd < 0
    shukra_retro = ven_spd < 0
    guru_combust = combust_status(sun_lon, jup_lon, JUP_COMB_ORB) == "Asta"
    shukra_combust = combust_status(sun_lon, ven_lon, VEN_COMB_ORB) == "Asta"
    guru_ast = guru_retro or guru_combust
    shukra_ast = shukra_retro or shukra_combust
    eclipse_risk = _eclipse_near_date(d, tz_h)

    notes: list[str] = []
    if guru_ast:
        notes.append("Guru asta — many traditions postpone vivah")
    if shukra_ast:
        notes.append("Shukra asta — marriage muhurta restricted")
    if eclipse_risk:
        notes.append("Eclipse within 3 days — avoid ceremonies")

    return {
        "guru_ast": guru_ast,
        "shukra_ast": shukra_ast,
        "guru_retro": guru_retro,
        "shukra_retro": shukra_retro,
        "guru_combust": guru_combust,
        "shukra_combust": shukra_combust,
        "eclipse_risk": eclipse_risk,
        "notes": notes,
    }
