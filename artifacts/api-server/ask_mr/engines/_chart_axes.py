"""Shared deterministic house/planet evidence builders for MR engines."""
from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})


def house_sign(reader: KundliReader, house: int) -> str | None:
    asc_i = reader.asc_index()
    if not isinstance(asc_i, int):
        return None
    return SIGNS[(asc_i + house - 1) % 12]


def house_axis_evidence(
    reader: KundliReader,
    house: int,
    *,
    label: str,
) -> str:
    sign = house_sign(reader, house) or "unknown"
    lord = reader.house_lord(house)
    pl = reader.planet(lord) if lord else None
    occ = reader.occupants(house)
    lord_h = pl.get("house") if pl else None
    lord_sign = pl.get("sign") if pl else None
    lord_dig = dignity_word(reader, lord, lord_sign) if lord else "unknown"
    malefics = [o for o in (occ or []) if o in _MALEFICS]
    malefic_note = f"; malefics in house={malefics}" if malefics else ""
    return (
        f"{label}: house {house} sign {sign}; lord {lord or 'unknown'} in house "
        f"{lord_h or '?'} sign {lord_sign or '?'} (dignity {lord_dig}); "
        f"occupants={occ or 'none'}{malefic_note}."
    )


def planet_line(reader: KundliReader, planet: str, *, role: str = "") -> str | None:
    p = reader.planet(planet) or {}
    if not p.get("house"):
        return None
    sign = p.get("sign")
    dig = dignity_word(reader, planet, sign)
    retro = ", retrograde" if p.get("retrograde") else ""
    tag = f" ({role})" if role else ""
    house_mates = [
        o for o in (reader.occupants(int(p.get("house"))) or [])
        if o != planet and o in _MALEFICS
    ]
    afflict = f"; malefic co-tenant {house_mates}" if house_mates else ""
    return (
        f"{planet}{tag}: house {p.get('house')} sign {sign}, dignity {dig}{retro}{afflict} — "
        f"direct influence on this topic."
    )


def dignity_word(reader: KundliReader, planet: str, sign: str | None) -> str:
    if not sign:
        return "neutral"
    try:
        d = reader.dignity(planet, reader.sidx(sign))
    except Exception:
        return "neutral"
    if d is None:
        return "neutral"
    if d >= 1:
        return "strong"
    if d < 0:
        return "weak"
    return "neutral"


def d9_reader(kundli: dict) -> KundliReader | None:
    d9 = (kundli or {}).get("divisionalCharts") or {}
    block = d9.get("D9") or d9.get("d9")
    if not isinstance(block, dict):
        return None
    k = dict(block)
    k.setdefault("name", "D9")
    return KundliReader(k)


def d9_spouse_appearance_lines(kundli: dict) -> list[str]:
    r9 = d9_reader(kundli)
    if not r9:
        return ["Navamsa D9: data not available — use D1 7th-house appearance baseline only."]
    asc = r9.k.get("ascendant") or r9.k.get("lagna") or "?"
    sign7 = house_sign(r9, 7)
    lord7 = r9.house_lord(7)
    p7l = r9.planet(lord7) if lord7 else None
    ven = r9.planet("Venus") or {}
    lines = [
        f"Navamsa D9 lagna: {asc} — finer spouse appearance / marriage quality layer.",
        f"D9 7th house sign: {sign7 or 'unknown'} — refined partner physical tone.",
    ]
    if lord7 and p7l:
        lines.append(
            f"D9 7th lord {lord7} in house {p7l.get('house')} sign {p7l.get('sign')} — "
            "detailed look/vibe refinement."
        )
    if ven.get("house"):
        dw = dignity_word(r9, "Venus", ven.get("sign"))
        lines.append(
            f"D9 Venus in house {ven.get('house')} sign {ven.get('sign')} ({dw}) — "
            "beauty/attractiveness refinement."
        )
    return lines


SIGN7_APPEARANCE: dict[str, str] = {
    "Aries": "athletic-medium build, sharp energetic features, active presence",
    "Taurus": "pleasant well-built frame, attractive steady features, graceful look",
    "Gemini": "slim-youthful build, expressive eyes, light agile appearance",
    "Cancer": "soft roundish face, caring eyes, medium build with gentle aura",
    "Leo": "striking presence, good hair/forehead, confident attractive look",
    "Virgo": "neat refined features, medium slim build, clean composed look",
    "Libra": "balanced attractive features, charming smile, proportionate build",
    "Scorpio": "intense magnetic eyes, compact-strong presence, deep gaze",
    "Sagittarius": "tall-open frame tendency, bright face, sporty cheerful look",
    "Capricorn": "structured lean-tall tendency, mature composed features",
    "Aquarius": "distinctive unique look, tall-lean tendency, modern vibe",
    "Pisces": "soft dreamy eyes, gentle face, medium build with artistic touch",
}


def sign7_appearance_baseline(sign7: str | None) -> str:
    if not sign7:
        return "7th-house sign baseline: unknown — general partner appearance from karakas."
    desc = SIGN7_APPEARANCE.get(sign7, "distinct partnership-house appearance tone")
    return f"7th-house sign baseline ({sign7}): {desc}."
