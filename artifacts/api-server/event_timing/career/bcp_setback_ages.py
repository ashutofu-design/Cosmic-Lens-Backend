"""BCP setback ages — 8th-lord + 11th-lord (obstacle + recovery gains)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from event_timing.career.bcp_5l_10l_ages import _lord_sources
from event_timing.career.bcp_career_ages import _house_lord, _planet_house


def compute_bcp_setback_ages(kundli: dict, lagna_si: int, user_age: Optional[int] = None,
                             birth_dt: Optional[datetime] = None) -> Dict[str, Any]:
    _ = birth_dt
    planets = kundli.get("planets") or []
    s8, a8 = _lord_sources(planets, lagna_si, 8, division="D1", prefix="8th_lord", label="8L")
    s11, a11 = _lord_sources(planets, lagna_si, 11, division="D1", prefix="11th_lord", label="11L")
    all_ages = sorted(a8 | a11)
    eighth_lord, eleventh_lord = _house_lord(lagna_si, 8), _house_lord(lagna_si, 11)

    def _asp(src, key):
        return [e for s in src if s.get("source") == key for e in (s.get("houses") or [])]

    future_m = [a for a in all_ages if user_age is None or a >= user_age]
    return {
        "eighth_lord": eighth_lord,
        "eighth_lord_house": _planet_house(planets, eighth_lord),
        "eleventh_lord": eleventh_lord,
        "eleventh_lord_house": _planet_house(planets, eleventh_lord),
        "aspect_houses_8l": _asp(s8, "8th_lord_aspects"),
        "aspect_houses_11l": _asp(s11, "11th_lord_aspects"),
        "sources": s8 + s11,
        "all_recovery_ages": all_ages,
        "future_priority_ages": future_m[:8],
        "next_activation_age": future_m[0] if future_m else None,
        "reasoning_summary": f"BCP-D1: 8L {eighth_lord} · 11L {eleventh_lord}; ages {all_ages[:12]}",
    }
