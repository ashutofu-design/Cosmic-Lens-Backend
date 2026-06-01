"""Vivah lagna evaluation — pandit-grade filters (Lahiri sidereal)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

try:
    import swisseph as swe

    _SWE_OK = True
except Exception:
    _SWE_OK = False

_RASHI = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]
_RASHI_LORD = {
    "Mesha": "Mars", "Vrishabha": "Venus", "Mithuna": "Mercury", "Karka": "Moon",
    "Simha": "Sun", "Kanya": "Mercury", "Tula": "Venus", "Vrishchika": "Mars",
    "Dhanu": "Jupiter", "Makara": "Saturn", "Kumbha": "Saturn", "Meena": "Jupiter",
}
_VIVAH_GOOD_LAGNA = {"Vrishabha", "Mithuna", "Karka", "Tula", "Dhanu", "Kumbha"}
_VIVAH_WEAK_LAGNA = {"Mesha", "Kanya", "Vrishchika", "Makara"}
_MALEFICS = {"Mars", "Saturn", "Rahu", "Ketu", "Sun"}
_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}


def _jd(dt_utc: datetime) -> float:
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600,
    )


def _planet_longitudes_sidereal(jd: float) -> dict[str, float]:
    flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    out: dict[str, float] = {}
    for name, pid in (
        ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
        ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
    ):
        pos, _ = swe.calc_ut(jd, pid, flag)
        out[name] = float(pos[0]) % 360
    rahu, _ = swe.calc_ut(jd, swe.MEAN_NODE, flag)
    out["Rahu"] = float(rahu[0]) % 360
    out["Ketu"] = (out["Rahu"] + 180) % 360
    return out


def _sign_idx(lon: float) -> int:
    return int(lon // 30) % 12


def _house_from_lagna(planet_sign: int, lagna_sign: int) -> int:
    return (planet_sign - lagna_sign + 12) % 12 + 1


def evaluate_vivah_lagna(
    dt_local: datetime,
    *,
    lat: float,
    lng: float,
    tz_h: float,
    allowed_lagnas: frozenset[str] | None = None,
) -> dict[str, Any]:
    if not _SWE_OK:
        return {"score": 50, "lagna": "", "veto": False, "notes": ["ephemeris unavailable"]}

    dt_utc = dt_local - timedelta(hours=tz_h)
    jd = _jd(dt_utc)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    _, ascmc = swe.houses(jd, lat, lng, b"P")
    asc_lon = float(ascmc[0]) % 360
    lagna_idx = _sign_idx(asc_lon)
    lagna = _RASHI[lagna_idx]
    seventh_idx = (lagna_idx + 6) % 12
    eighth_idx = (lagna_idx + 7) % 12

    planets = _planet_longitudes_sidereal(jd)
    score = 60
    notes: list[str] = []
    veto = False

    if allowed_lagnas and lagna not in allowed_lagnas:
        score -= 20
        veto = True
        notes.append(f"{lagna} lagna — not in regional vivah lagna list")

    if lagna in _VIVAH_GOOD_LAGNA:
        score += 16
        notes.append(f"{lagna} lagna — classical vivah support")
    elif lagna in _VIVAH_WEAK_LAGNA:
        score -= 14
        notes.append(f"{lagna} lagna — weak for vivah; pandit review advised")

    lagna_lord = _RASHI_LORD.get(lagna, "")
    lord_lon = planets.get(lagna_lord, planets["Sun"])
    lord_si = _sign_idx(lord_lon)
    lord_house = _house_from_lagna(lord_si, lagna_idx)
    if lord_house in (1, 4, 5, 7, 9, 10, 11):
        score += 8
    elif lord_house in (6, 8, 12):
        score -= 12
        notes.append(f"Lagna lord in {lord_house}th — strained muhurta")

    malefics_7 = []
    malefics_8 = []
    benefics_7 = []
    for pname, lon in planets.items():
        if pname not in _MALEFICS and pname not in _BENEFICS:
            continue
        si = _sign_idx(lon)
        h = _house_from_lagna(si, lagna_idx)
        if h == 7 and pname in _MALEFICS:
            malefics_7.append(pname)
        if h == 8 and pname in _MALEFICS:
            malefics_8.append(pname)
        if h == 7 and pname in _BENEFICS:
            benefics_7.append(pname)

    if len(malefics_7) >= 2:
        score -= 15
        veto = True
        notes.append("Multiple malefics in 7th — avoid this lagna")
    elif malefics_7:
        score -= 8
    if malefics_8:
        score -= 6
    if benefics_7:
        score += 6 * min(2, len(benefics_7))
        notes.append(f"Benefics in 7th: {', '.join(benefics_7)}")

    if _sign_idx(planets["Venus"]) in (lagna_idx, seventh_idx):
        score += 8
        notes.append("Venus supports harmony for marriage")
    if _sign_idx(planets["Jupiter"]) in (lagna_idx, seventh_idx, (lagna_idx + 4) % 12):
        score += 6

    score = max(10, min(96, score))
    return {
        "score": score,
        "lagna": lagna,
        "lagna_lord": lagna_lord,
        "seventh_sign": _RASHI[seventh_idx],
        "veto": veto,
        "notes": notes[:4],
    }
