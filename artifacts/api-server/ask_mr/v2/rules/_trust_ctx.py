"""Loyalty/trust rule context helpers — planet-wise evidence."""
from __future__ import annotations

from typing import Any

from ._commitment_ctx import (
    _planet_evidence,
    _seventh_lord_strong,
    is_timing,
    reader,
    sig,
)


def house5_evidence(ctx: dict[str, Any]) -> str:
    from ask_mr.engines._chart_axes import house_axis_evidence

    r = reader(ctx)
    if not r:
        return "5th house: romance/trust axis"
    return house_axis_evidence(r, 5, label="Romance/trust axis (5th house)")


def house7_evidence(ctx: dict[str, Any]) -> str:
    from ask_mr.engines._chart_axes import house_axis_evidence

    r = reader(ctx)
    if not r:
        return "7th house: partnership/loyalty axis"
    return house_axis_evidence(r, 7, label="Partnership/loyalty axis (7th house)")


def house8_evidence(ctx: dict[str, Any]) -> str:
    from ask_mr.engines._chart_axes import house_axis_evidence

    r = reader(ctx)
    if not r:
        return "8th house: secrecy/deep-bond axis"
    return house_axis_evidence(r, 8, label="Secrecy/emotional-depth axis (8th house)")


def venus_surface_risk_dominates(ctx: dict[str, Any]) -> bool:
    s = sig(ctx)
    if not s or not s.venus_surface_strong_only:
        return False
    return bool(
        s.loyalty_risk_high
        or s.moon_in_8th
        or s.moon_d9_debil
        or s.venus_mars_conjunct
        or s.third_person_risk
        or s.seventh_lord_dusthana
    )


def loyalty_safe_bonus(ctx: dict[str, Any]) -> bool:
    """Port of love_reality _person_loyalty_safe_bonus — clean chart only."""
    s = sig(ctx)
    if not s:
        return False
    if s.loyalty_risk_high or s.venus_debil or s.seventh_lord_debil or s.third_person_risk:
        return False
    return not s.venus_debil and not s.moon_debil and not s.seventh_lord_dusthana and not s.mars_on_7th
