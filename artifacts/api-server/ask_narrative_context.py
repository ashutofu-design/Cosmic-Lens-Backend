"""Focused D1 + D9 + selected divisional context for narrative (non-timing) Ask."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

_SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_ALIASES = {
    "mesh": "Aries", "vrishabh": "Taurus", "mithun": "Gemini",
    "kark": "Cancer", "karka": "Cancer", "simha": "Leo",
    "kanya": "Virgo", "tula": "Libra", "vrishchik": "Scorpio",
    "dhanu": "Sagittarius", "makar": "Capricorn",
    "kumbh": "Aquarius", "meen": "Pisces",
}

_TOPIC_VARGAS: Dict[str, Tuple[List[int], List[str]]] = {
    "marriage": ([7, 5, 8], ["D9"]),
    "career": ([10, 6, 2, 11], ["D10"]),
    "health": ([1, 6, 8, 12], ["D12"]),
    "finance": ([2, 11, 5], ["D2", "D11"]),
    "children": ([5], ["D7"]),
    "property": ([4, 11, 12], ["D4"]),
    "travel": ([9, 12, 3], ["D9"]),
    "education": ([4, 5, 9], ["D24"]),
    "general": ([1], ["D9"]),
}

_HOUSE_RX = re.compile(
    r"(?ix)"
    r"(?:\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:house|bhav|bhaav|ghar)\b|"
    r"\b(\d{1,2})\s*h\b)"
)


def _canon_sign(raw: Any) -> Optional[str]:
    if not raw:
        return None
    key = str(raw).strip()
    if not key:
        return None
    titled = key.title()
    if titled in _SIGNS:
        return titled
    return _ALIASES.get(key.lower())


def _asc_idx(kundli: dict) -> Optional[int]:
    asc = _canon_sign((kundli.get("ascendant") or kundli.get("lagna")))
    return _SIGNS.index(asc) if asc in _SIGNS else None


def _house_lord(asc_idx: int, house: int) -> str:
    sign_idx = (asc_idx + int(house) - 1) % 12
    return _SIGN_LORDS[sign_idx]


def _extract_houses(question: str) -> List[int]:
    out: List[int] = []
    for m in _HOUSE_RX.finditer(question or ""):
        h = m.group(1) or m.group(2)
        if h:
            n = int(h)
            if 1 <= n <= 12 and n not in out:
                out.append(n)
    return out


def _detect_topics(question: str) -> List[str]:
    try:
        from ask_engine import detect_topics

        return detect_topics(question) or []
    except Exception:
        return []


def _pick_focus(question: str) -> Tuple[List[int], List[str]]:
    topics = _detect_topics(question)
    houses: Set[int] = set(_extract_houses(question))
    vargas: Set[str] = set()

    for t in topics:
        if t in _TOPIC_VARGAS:
            hs, vs = _TOPIC_VARGAS[t]
            houses.update(hs)
            vargas.update(vs)

    q = (question or "").lower()
    if any(w in q for w in ("partner", "spouse", "shaadi", "shadi", "marriage", "dikh")):
        houses.update([7, 5])
        vargas.add("D9")
    if any(w in q for w in ("career", "naukri", "job", "direction", "business")):
        houses.update([10, 6])
        vargas.add("D10")
    if any(w in q for w in ("health", "sehat", "bimari", "rog")):
        houses.update([1, 6, 8])
        vargas.add("D12")
    if any(w in q for w in ("ghar", "property", "home", "makaan")):
        houses.update([4])
        vargas.add("D4")
    if any(w in q for w in ("bachcha", "child", "santaan", "pregnancy")):
        houses.update([5])
        vargas.add("D7")

    if not houses:
        houses.add(1)
    if not vargas:
        vargas.add("D9")

    return sorted(houses), sorted(vargas)


def _fmt_planets(planets: List[dict], houses: Optional[Set[int]] = None) -> List[str]:
    lines: List[str] = []
    for p in planets:
        if not isinstance(p, dict):
            continue
        house = p.get("house")
        if houses is not None and house not in houses:
            continue
        name = p.get("name", "?")
        sign = p.get("sign", "?")
        retro = " [R]" if p.get("retrograde") else ""
        lines.append(f"  • {name}: {sign} (House {house}){retro}")
    return lines


def _fmt_varga(kundli: dict, key: str, focus_houses: Set[int]) -> List[str]:
    div = kundli.get("divisionalCharts") or {}
    chart = div.get(key) or div.get(key.lower())
    if not isinstance(chart, dict):
        return []
    label = {
        "D9": "D9 NAVAMSA (marriage / dharma / strength)",
        "D10": "D10 DASHAMSA (career / profession)",
        "D12": "D12 DWADASHAMSA (health patterns)",
        "D7": "D7 SAPTAMSA (children / progeny)",
        "D4": "D4 CHATURTHAMSA (property / home)",
        "D2": "D2 HORA (wealth flow)",
        "D11": "D11 EKADASHAMSA (gains)",
        "D24": "D24 CHATURVIMSAMSA (education)",
    }.get(key, key)
    lines = [f"\n=== {label} ==="]
    asc = chart.get("ascendant") or chart.get("lagna")
    if asc:
        lines.append(f"Ascendant: {asc}")
    planets = chart.get("planets") or []
    if isinstance(planets, list):
        pl = _fmt_planets(planets, focus_houses if focus_houses else None)
        if pl:
            lines.extend(pl)
        else:
            lines.extend(_fmt_planets(planets, None))
    return lines if len(lines) > 1 else []


def build_narrative_chart_context(kundli: Any, question: str = "") -> str:
    """D1 focus houses + lords, D9, and topic-selected divisional charts."""
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return "(no chart data available)"

    focus_houses, varga_keys = _pick_focus(question or "")
    focus_set = set(focus_houses)
    asc_i = _asc_idx(kundli)
    lines: List[str] = [
        "=== NARRATIVE MODE — D1 + SELECTED VARGAS (no timing dates) ===",
        "Read the focused house(s), their lords in D1, then check the same "
        "lord/planet in D9 and the divisional charts below.",
    ]

    asc = kundli.get("ascendant") or kundli.get("lagna")
    if asc:
        lines.append(f"\nD1 Ascendant (Lagna): {asc}")

    if asc_i is not None:
        lines.append("\nFOCUS HOUSES (D1):")
        for h in focus_houses:
            sign = _SIGNS[(asc_i + h - 1) % 12]
            lord = _house_lord(asc_i, h)
            lines.append(f"  • {h}H = {sign} | lord = {lord}")

    planets = kundli.get("planets") or []
    if isinstance(planets, list):
        d1_lines = _fmt_planets(planets, focus_set)
        if d1_lines:
            lines.append("\nD1 planets in focus houses:")
            lines.extend(d1_lines)
        # Always show planets user named explicitly
        q_low = (question or "").lower()
        for pname in (
            "Rahu", "Ketu", "Saturn", "Shani", "Jupiter", "Guru",
            "Venus", "Shukra", "Mars", "Mangal", "Moon", "Chandra",
            "Sun", "Surya", "Mercury", "Budh",
        ):
            if pname.lower() in q_low or pname in q_low:
                p = next(
                    (x for x in planets if isinstance(x, dict) and x.get("name") == pname),
                    None,
                )
                if p and f"  • {pname}:" not in "\n".join(lines):
                    lines.append(
                        f"  • {pname}: {p.get('sign','?')} "
                        f"(House {p.get('house','?')})"
                    )

    for vk in varga_keys:
        lines.extend(_fmt_varga(kundli, vk, focus_set))

    lines.append(
        "\nRULE: Short human answer only (25-45 words). Answer exactly what "
        "was asked. No timing dates on narrative Qs. Plain Hinglish — no "
        "[Checked] line, no essay."
    )
    return "\n".join(lines)


__all__ = ["build_narrative_chart_context"]
