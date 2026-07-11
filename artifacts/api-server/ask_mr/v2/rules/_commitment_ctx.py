"""Commitment rule context helpers — planet-wise evidence from PersonSignals + chart."""
from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader


def sig(ctx: dict[str, Any]):
    return ctx.get("sig")


def reader(ctx: dict[str, Any]) -> KundliReader | None:
    r = ctx.get("reader")
    return r if isinstance(r, KundliReader) else None


def is_timing(ctx: dict[str, Any]) -> bool:
    return (ctx.get("mode") or "").strip().lower() == "timing"


def _jupiter_supports_commitment(ctx: dict[str, Any]) -> bool:
    r = reader(ctx)
    if not r:
        return False
    jup = r.planet("Jupiter")
    if not jup:
        return False
    house = int(jup.get("house") or 0)
    dig = r.dignity("Jupiter", r.sidx(jup.get("sign") or ""))
    if dig >= 1 and house in (1, 4, 5, 7, 9, 11):
        return True
    if house in (5, 7, 11) and dig >= 0:
        return True
    return "Jupiter" in (r.aspects_house(7) or [])


def _jupiter_weak_commitment(ctx: dict[str, Any]) -> bool:
    r = reader(ctx)
    if not r:
        return False
    jup = r.planet("Jupiter")
    if not jup:
        return False
    from vedic.love_reality.scoring_core import DUSTHANA

    dig = r.dignity("Jupiter", r.sidx(jup.get("sign") or ""))
    return dig <= -2 or int(jup.get("house") or 0) in DUSTHANA


def _seventh_lord_strong(ctx: dict[str, Any]) -> bool:
    s = sig(ctx)
    if not s:
        return False
    return not s.seventh_lord_dusthana and not s.seventh_lord_debil


def _planet_evidence(ctx: dict[str, Any], planet: str, *, role: str) -> str:
    from ask_mr.engines._chart_axes import planet_line

    r = reader(ctx)
    if not r:
        return f"{planet} ({role}): chart data limited"
    line = planet_line(r, planet, role=role)
    return line or f"{planet} ({role}): placement noted on commitment axis"


def _house7_evidence(ctx: dict[str, Any]) -> str:
    from ask_mr.engines._chart_axes import house_axis_evidence

    r = reader(ctx)
    if not r:
        return "7th house: partnership/commitment axis"
    return house_axis_evidence(r, 7, label="Partnership/commitment axis (7th house)")
