"""Nakshatra name normalization and tarabala / chandrabal."""
from __future__ import annotations

from vedic.panchang.phase_r import NAK_NAMES

_ALIASES: dict[str, str] = {
    "uttaraphalguni": "U.Phalguni",
    "uttara phalguni": "U.Phalguni",
    "purva phalguni": "P.Phalguni",
    "purvaphalguni": "P.Phalguni",
    "uttarashadha": "U.Ashadha",
    "uttara ashadha": "U.Ashadha",
    "purvashadha": "P.Ashadha",
    "purva ashadha": "P.Ashadha",
    "uttarabhadrapada": "U.Bhadrapada",
    "uttara bhadrapada": "U.Bhadrapada",
    "purvabhadrapada": "P.Bhadrapada",
    "purva bhadrapada": "P.Bhadrapada",
    "dhanishtha": "Dhanishta",
    "mrigashira": "Mrigashira",
    "mrigasira": "Mrigashira",
}


def normalize_nakshatra(name: str | None) -> str | None:
    if not name or not str(name).strip():
        return None
    raw = str(name).strip()
    if raw in NAK_NAMES:
        return raw
    key = raw.lower().replace(".", "").replace("-", " ")
    if key in _ALIASES:
        return _ALIASES[key]
    for canon in NAK_NAMES:
        if canon.lower() == key or canon.lower().replace(".", "") == key.replace(" ", ""):
            return canon
    return raw if raw in NAK_NAMES else None


def nakshatra_index(name: str) -> int | None:
    n = normalize_nakshatra(name)
    if not n or n not in NAK_NAMES:
        return None
    return NAK_NAMES.index(n)


# Tara 1=Janma … 9=Mitra (classical cycle from birth nak)
_TARA_BAD = {1, 3, 5, 7}


def tarabala(birth_nak: str, transit_nak: str) -> dict:
    bi = nakshatra_index(birth_nak)
    ti = nakshatra_index(transit_nak)
    if bi is None or ti is None:
        return {"ok": True, "tara": 0, "note": ""}
    diff = (ti - bi) % 27
    tara = (diff % 9) + 1
    ok = tara not in _TARA_BAD
    names = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhaka", "Vadha", "Mitra", "Ati-Mitra"]
    return {
        "ok": ok,
        "tara": tara,
        "tara_name": names[tara - 1],
        "note": "" if ok else f"Tarabala {names[tara - 1]} — avoid for vivah",
    }


_RASHI = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]


def chandrabal_ok(birth_moon_rashi: str, transit_moon_rashi: str) -> dict:
    """Moon should not be in 6, 8, 12 from birth Moon rashi."""
    try:
        b = _RASHI.index(birth_moon_rashi)
        t = _RASHI.index(transit_moon_rashi)
    except ValueError:
        return {"ok": True, "note": ""}
    house = (t - b + 12) % 12 + 1
    ok = house not in (6, 8, 12)
    return {
        "ok": ok,
        "house": house,
        "note": "" if ok else f"Chandrabal — Moon in {house}th from birth Moon",
    }
