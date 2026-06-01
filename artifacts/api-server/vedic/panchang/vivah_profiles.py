"""Regional vivah rule profiles (North / South Indian traditions)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VivahProfile:
    id: str
    label: str
    nak_excellent: frozenset[str]
    nak_acceptable: frozenset[str]
    nak_avoid: frozenset[str]
    nak_panchak: frozenset[str]
    allowed_lagnas: frozenset[str]
    favoured_hora_lords: frozenset[str]


_PANCHAK = frozenset({
    "Dhanishta", "Shatabhisha", "P.Bhadrapada", "U.Bhadrapada", "Revati",
})

_NORTH = VivahProfile(
    id="north",
    label="North Indian (Lahiri)",
    nak_excellent=frozenset({
        "Rohini", "Mrigashira", "Magha", "U.Phalguni", "Hasta", "Swati",
        "Anuradha", "U.Ashadha", "Shravana", "P.Ashadha",
    }),
    nak_acceptable=frozenset({
        "Pushya", "Punarvasu", "Chitra", "Ashwini", "U.Bhadrapada",
    }),
    nak_avoid=frozenset({
        "Bharani", "Krittika", "Ardra", "Ashlesha", "Jyeshtha", "Vishakha", "Mula",
    }),
    nak_panchak=_PANCHAK,
    allowed_lagnas=frozenset({
        "Vrishabha", "Mithuna", "Karka", "Tula", "Dhanu", "Kumbha", "Meena",
    }),
    favoured_hora_lords=frozenset({"Venus", "Jupiter", "Moon", "Mercury"}),
)

_SOUTH = VivahProfile(
    id="south",
    label="South Indian (Lahiri)",
    nak_excellent=frozenset({
        "Rohini", "Mrigashira", "U.Phalguni", "Hasta", "Swati", "Anuradha",
        "U.Ashadha", "Shravana", "Revati", "U.Bhadrapada",
    }),
    nak_acceptable=frozenset({
        "Pushya", "Punarvasu", "Chitra", "Ashwini", "Magha", "P.Ashadha",
    }),
    nak_avoid=frozenset({
        "Bharani", "Krittika", "Ardra", "Ashlesha", "Jyeshtha", "Vishakha", "Mula",
    }),
    nak_panchak=_PANCHAK,
    allowed_lagnas=frozenset({
        "Vrishabha", "Mithuna", "Kanya", "Tula", "Dhanu", "Kumbha", "Meena",
    }),
    favoured_hora_lords=frozenset({"Venus", "Jupiter", "Moon"}),
)

_PROFILES = {"north": _NORTH, "south": _SOUTH, "default": _NORTH}


def get_vivah_profile(name: str | None) -> VivahProfile:
    key = (name or "north").strip().lower()
    return _PROFILES.get(key, _NORTH)
