"""Frozen birth profiles for Love Compatibility golden tests (deterministic Lahiri)."""
from __future__ import annotations

from typing import Any

_DELHI = {"lat": 28.61, "lon": 77.21, "tz": 5.5, "place": "Delhi"}
_MUMBAI = {"lat": 19.08, "lon": 72.88, "tz": 5.5, "place": "Mumbai"}
_CHENNAI = {"lat": 13.08, "lon": 80.27, "tz": 5.5, "place": "Chennai"}
_KOLKATA = {"lat": 22.57, "lon": 88.36, "tz": 5.5, "place": "Kolkata"}


def _p(name: str, geo: dict[str, Any], **birth: Any) -> dict[str, Any]:
    return {"name": name, **geo, **birth}


# Smoke pair used across honest-engine tests
GOLDEN_DELHI_MUMBAI = {
    "id": "delhi_mumbai_default",
    "p1": _p("You", _DELHI, day=15, month=3, year=1995, hour=10, minute=30, ampm="AM"),
    "p2": _p("Partner", _MUMBAI, day=22, month=8, year=1997, hour=6, minute=0, ampm="PM"),
}

GOLDEN_CHENNAI_PAIR = {
    "id": "chennai_oct_feb",
    "p1": _p("You", _CHENNAI, day=5, month=10, year=1990, hour=3, minute=15, ampm="AM"),
    "p2": _p("Partner", _CHENNAI, day=18, month=2, year=1992, hour=11, minute=45, ampm="PM"),
}

GOLDEN_NEWYEAR_PAIR = {
    "id": "delhi_newyear_summer",
    "p1": _p("You", _DELHI, day=1, month=1, year=1988, hour=12, minute=0, ampm="PM"),
    "p2": _p("Partner", _DELHI, day=15, month=7, year=1990, hour=6, minute=30, ampm="AM"),
}

GOLDEN_SPRING_AUTUMN = {
    "id": "mumbai_may_nov",
    "p1": _p("You", _MUMBAI, day=20, month=5, year=1993, hour=8, minute=0, ampm="AM"),
    "p2": _p("Partner", _MUMBAI, day=9, month=11, year=1995, hour=10, minute=0, ampm="PM"),
}

GOLDEN_WINTER_SPRING = {
    "id": "kolkata_dec_apr",
    "p1": _p("You", _KOLKATA, day=12, month=12, year=1985, hour=5, minute=30, ampm="AM"),
    "p2": _p("Partner", _KOLKATA, day=25, month=4, year=1987, hour=9, minute=15, ampm="PM"),
}

GOLDEN_YOUNG_PAIR = {
    "id": "delhi_aug_mar",
    "p1": _p("You", _DELHI, day=7, month=8, year=1998, hour=2, minute=0, ampm="AM"),
    "p2": _p("Partner", _DELHI, day=14, month=3, year=2000, hour=7, minute=45, ampm="PM"),
}

GOLDEN_EVENING_MORNING = {
    "id": "mumbai_evening_morning",
    "p1": _p("You", _MUMBAI, day=3, month=6, year=1991, hour=9, minute=30, ampm="PM"),
    "p2": _p("Partner", _MUMBAI, day=27, month=9, year=1994, hour=4, minute=20, ampm="AM"),
}

GOLDEN_LATE_NIGHT = {
    "id": "chennai_late_night",
    "p1": _p("You", _CHENNAI, day=16, month=4, year=1989, hour=11, minute=55, ampm="PM"),
    "p2": _p("Partner", _CHENNAI, day=2, month=10, year=1991, hour=1, minute=10, ampm="AM"),
}

ALL_GOLDEN_CASES = (
    GOLDEN_DELHI_MUMBAI,
    GOLDEN_CHENNAI_PAIR,
    GOLDEN_NEWYEAR_PAIR,
    GOLDEN_SPRING_AUTUMN,
    GOLDEN_WINTER_SPRING,
    GOLDEN_YOUNG_PAIR,
    GOLDEN_EVENING_MORNING,
    GOLDEN_LATE_NIGHT,
)
