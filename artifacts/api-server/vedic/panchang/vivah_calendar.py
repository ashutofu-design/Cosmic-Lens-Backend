"""Lunar calendar rules: Adhik Maas, Dagdha tithi, Kharmas."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from vedic.panchang.phase_r import compute_phase_r
from vedic.panchang.vivah_geo import local_to_phase_utc

# Dagdha (burnt) tithi — weekday + tithi name (classical North-Indian almanac set)
DAGDHA_PAIRS: set[tuple[str, str]] = {
    ("Sunday", "Pratipada"), ("Sunday", "Shashthi"), ("Sunday", "Ekadashi"),
    ("Monday", "Chaturthi"), ("Monday", "Navami"),
    ("Tuesday", "Dwitiya"), ("Tuesday", "Saptami"), ("Tuesday", "Dwadashi"),
    ("Wednesday", "Tritiya"), ("Wednesday", "Ashtami"), ("Wednesday", "Trayodashi"),
    ("Thursday", "Chaturthi"), ("Thursday", "Navami"),
    ("Friday", "Shashthi"), ("Friday", "Ekadashi"),
    ("Saturday", "Saptami"), ("Saturday", "Dwadashi"),
}


def _sun_sign_idx(dt_local: datetime, tz_h: float) -> int:
    pr = compute_phase_r(local_to_phase_utc(dt_local, tz_h))
    return int((pr.get("r6_ritu_ayana_maasa") or {}).get("sun_sign_idx") or 0)


def _tithi_key(dt_local: datetime, tz_h: float) -> tuple[str, str, str]:
    pr = compute_phase_r(local_to_phase_utc(dt_local, tz_h))
    t = pr.get("r1_tithi") or {}
    v = pr.get("r5_vaar") or {}
    return (v.get("weekday") or "", t.get("paksha") or "", t.get("name") or "")


def is_dagdha_tithi(dt_local: datetime, tz_h: float) -> bool:
    vaar, _, tithi = _tithi_key(dt_local, tz_h)
    return (vaar, tithi) in DAGDHA_PAIRS


def _find_amavasya_boundary(
    anchor: date,
    tz_h: float,
    *,
    forward: bool,
) -> date | None:
    """Walk day-by-day to nearest Amavasya (tithi name)."""
    step = 1 if forward else -1
    d = anchor
    for _ in range(40):
        noon = datetime(d.year, d.month, d.day, 12, 0)
        _, _, tithi = _tithi_key(noon, tz_h)
        if tithi == "Amavasya":
            return d
        d = d + timedelta(days=step)
    return None


def _sankranti_count(d0: date, d1: date, tz_h: float) -> int:
    """Count sidereal solar sign ingresses between dates inclusive."""
    if d1 < d0:
        d0, d1 = d1, d0
    last = _sun_sign_idx(datetime(d0.year, d0.month, d0.day, 12, 0), tz_h)
    count = 0
    d = d0 + timedelta(days=1)
    while d <= d1:
        si = _sun_sign_idx(datetime(d.year, d.month, d.day, 12, 0), tz_h)
        if si != last:
            count += 1
            last = si
        d += timedelta(days=1)
    return count


def lunar_month_flags(target: date, tz_h: float) -> dict[str, Any]:
    """Detect Adhik Maas (0 sankranti in synodic month) for the day."""
    prev_am = _find_amavasya_boundary(target, tz_h, forward=False)
    next_am = _find_amavasya_boundary(target, tz_h, forward=True)
    if not prev_am or not next_am or prev_am >= next_am:
        return {"adhik_maas": False, "kshaya_month": False, "notes": []}

    sank = _sankranti_count(prev_am, next_am, tz_h)
    adhik = sank == 0
    kshaya = sank >= 2
    notes: list[str] = []
    if adhik:
        notes.append("Adhik Maas — vivah traditionally postponed")
    if kshaya:
        notes.append("Kshaya maas — extra caution for muhurta")
    return {"adhik_maas": adhik, "kshaya_month": kshaya, "sankranti_count": sank, "notes": notes}
