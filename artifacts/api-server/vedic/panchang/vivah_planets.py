"""Planetary states for vivah filtering — retrograde, combustion, eclipses."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

try:
    import swisseph as swe

    _SWE_OK = True
except Exception:
    _SWE_OK = False

JUP_COMB_ORB = 11.0
VEN_COMB_ORB = 10.0
ECLIPSE_PROX_DAYS = 3


def _jd(dt_utc: datetime) -> float:
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600,
    )


def _angular_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _eclipse_near_date(d: date, tz_h: float) -> bool:
    """True if solar or lunar eclipse within ±ECLIPSE_PROX_DAYS."""
    if not _SWE_OK:
        return False
    try:
        noon = datetime(d.year, d.month, d.day, 12, 0) - timedelta(hours=tz_h)
        jd = _jd(noon)
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
    jd = _jd(dt_utc)
    flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    sun, _ = swe.calc_ut(jd, swe.SUN, flag)
    jup, _ = swe.calc_ut(jd, swe.JUPITER, flag)
    ven, _ = swe.calc_ut(jd, swe.VENUS, flag)

    sun_lon = float(sun[0]) % 360
    jup_lon, ven_lon = float(jup[0]) % 360, float(ven[0]) % 360
    jup_spd, ven_spd = float(jup[3]), float(ven[3])

    guru_retro = jup_spd < 0
    shukra_retro = ven_spd < 0
    guru_combust = _angular_sep(jup_lon, sun_lon) <= JUP_COMB_ORB
    shukra_combust = _angular_sep(ven_lon, sun_lon) <= VEN_COMB_ORB
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
