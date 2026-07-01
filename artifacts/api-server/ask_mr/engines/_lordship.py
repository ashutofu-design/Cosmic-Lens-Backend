"""Functional lordship (whole-sign) for MR engine evidence lines."""
from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader


def houses_ruled_by(reader: KundliReader, planet: str) -> list[int]:
    """Houses ruled by planet from lagna (e.g. Mercury -> [7, 10] for Gemini+Virgo signs)."""
    name = (planet or "").strip()
    if not name:
        return []
    out: list[int] = []
    for h in range(1, 13):
        if reader.house_lord(h) == name:
            out.append(h)
    return out


def lordship_clause(
    reader: KundliReader,
    planet: str,
    *,
    context_house: int | None = None,
) -> str:
    """Compact suffix for evidence: 'rules 7H+10H from lagna'."""
    ruled = houses_ruled_by(reader, planet)
    if not ruled:
        return ""
    hs = "+".join(f"{h}H" for h in ruled)
    if context_house and ruled == [context_house]:
        return f"; rules {context_house}H from lagna"
    return f"; rules {hs} from lagna"


def planet_placement_clause(
    reader: KundliReader,
    planet: str,
    *,
    role: str = "",
) -> str | None:
    """Planet in house/sign plus lordship — for evidence bullets."""
    p = reader.planet(planet) or {}
    h = p.get("house")
    if not h:
        return None
    sign = p.get("sign") or "?"
    ls = lordship_clause(reader, planet)
    tag = f" ({role})" if role else ""
    return f"{planet}{tag} in house {h} sign {sign}{ls}"
