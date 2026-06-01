"""Day hora (planetary hour) for vivah windows."""
from __future__ import annotations

from datetime import datetime, timedelta

from vedic.panchang.vivah_geo import DayGeo

# Weekday lords: Mon=Moon … Sun=Sun
_WD_LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
_HORA_CYCLE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]


def _lord_index(lord: str) -> int:
    return _HORA_CYCLE.index(lord)


def hora_lord_at(dt: datetime, geo: DayGeo) -> str:
    """Planetary hour lord at local time (day hora from sunrise)."""
    if dt < geo.sunrise:
        return ""
    day_len = (geo.sunset - geo.sunrise).total_seconds()
    if day_len <= 0:
        return ""
    hora_len = day_len / 12.0
    elapsed = (dt - geo.sunrise).total_seconds()
    if elapsed >= day_len:
        return ""
    wd = geo.d.weekday()
    first = _WD_LORD[wd]
    idx = (_lord_index(first) + int(elapsed // hora_len)) % 7
    return _HORA_CYCLE[idx]


def hora_covers_window(
    start: datetime,
    end: datetime,
    geo: DayGeo,
    favoured_lords: frozenset[str],
) -> tuple[bool, str]:
    """Midpoint hora must be favourable; start/end should not be Saturn/Mars only."""
    mid = start + (end - start) / 2
    lord = hora_lord_at(mid, geo)
    if lord in favoured_lords:
        return True, lord
    l0 = hora_lord_at(start + timedelta(minutes=5), geo)
    l1 = hora_lord_at(end - timedelta(minutes=5), geo)
    if l0 in favoured_lords and l1 in favoured_lords:
        return True, l0
    return False, lord
