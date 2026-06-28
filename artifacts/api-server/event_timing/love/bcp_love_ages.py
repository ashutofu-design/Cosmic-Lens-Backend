"""BCP love ages — 5th-lord + 7th-lord (romance + partnership)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from event_timing.career.bcp_5l_10l_ages import _lord_sources
from event_timing.career.bcp_career_ages import _house_lord, _planet_house


def compute_bcp_love_ages(
    kundli: dict,
    lagna_si: int,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    _ = birth_dt
    planets = kundli.get("planets") or []
    s5, a5 = _lord_sources(planets, lagna_si, 5, division="D1", prefix="5th_lord", label="5L")
    s7, a7 = _lord_sources(planets, lagna_si, 7, division="D1", prefix="7th_lord", label="7L")
    all_ages = sorted(a5 | a7)
    fifth_lord, seventh_lord = _house_lord(lagna_si, 5), _house_lord(lagna_si, 7)

    def _asp(src, key):
        return [e for s in src if s.get("source") == key for e in (s.get("houses") or [])]

    future_m = [a for a in all_ages if user_age is None or a >= user_age]
    return {
        "fifth_lord": fifth_lord,
        "fifth_lord_house": _planet_house(planets, fifth_lord),
        "seventh_lord": seventh_lord,
        "seventh_lord_house": _planet_house(planets, seventh_lord),
        "aspect_houses_5l": _asp(s5, "5th_lord_aspects"),
        "aspect_houses_7l": _asp(s7, "7th_lord_aspects"),
        "sources": s5 + s7,
        "all_love_ages": all_ages,
        "future_priority_ages": future_m[:8],
        "next_activation_age": future_m[0] if future_m else None,
        "reasoning_summary": f"BCP-D1: 5L {fifth_lord} · 7L {seventh_lord}; ages {all_ages[:12]}",
    }
