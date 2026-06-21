"""
money_habits_v1 — Chart-matched money habits (D1 only).

Up to 3 human-sounding tips from ~18 templates. No dasha, transit, or astro jargon.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}
_DUSTHANA = frozenset({6, 8, 12})
_MAX_HABITS = 3
_MIN_HABITS = 2

# (priority desc, message) — higher shown first
_TEMPLATES: Dict[str, Tuple[int, str]] = {
    "lord2_dusthana": (
        85,
        "Money tends to slip through small gaps. Track spending for one month — "
        "the leaks are usually boring subscriptions, not one big splurge.",
    ),
    "lord2_debil": (
        75,
        "Get-rich-quick rarely works for you. Pick one steady path and give it "
        "a year before you judge results.",
    ),
    "lord11_dusthana": (
        80,
        "One income stream isn't enough cushion for you. Build a backup skill or "
        "side source, even if it starts small.",
    ),
    "lord11_debil": (
        70,
        "Your earnings have good months and slow months. Auto-transfer a fixed "
        "slice to savings on payday — especially when income feels high.",
    ),
    "ketu_2h": (
        82,
        "Cash can drain without you noticing. Once a week for a month, open your "
        "bank app and scan for charges you don't recognise.",
    ),
    "saturn_2h": (
        78,
        "Wealth builds slowly for you — and that's fine. A small monthly SIP started "
        "now beats a big plan you'll start 'next year'.",
    ),
    "rahu_mars_2h": (
        88,
        "Big buys feel urgent in the moment. Wait 48 hours before anything that "
        "crosses your monthly comfort limit.",
    ),
    "drain_12h": (
        76,
        "Hidden costs pile up quietly. Cancel subscriptions and memberships you "
        "haven't opened in 90 days.",
    ),
    "swing_8h": (
        84,
        "Surprise expenses can land hard. Keep 3–6 months of living costs in a "
        "separate account — don't mix it with daily spending.",
    ),
    "stress_spend_6h": (
        72,
        "When work gets heavy, spending can spike. Set a small guilt-free 'fun money' "
        "cap each month and stop when it's done.",
    ),
    "speculation_5_8": (
        86,
        "Trading and crypto will tempt you. Only risk what you can afford to lose "
        "entirely — rent and EMI money stays off the table.",
    ),
    "windfall_discipline": (
        74,
        "Bonus or sudden inflow feels like free money. Move 30% to savings the same "
        "day — before lifestyle upgrades creep in.",
    ),
    "lifestyle_creep": (
        65,
        "When income rises, bump savings before lifestyle. Most people upgrade spends "
        "first and wonder where the raise went.",
    ),
    "fallback_track": (
        45,
        "If you only fix one habit: once a month, read where last month's salary went. "
        "Half the battle is just seeing it.",
    ),
    "fallback_payday": (
        44,
        "On salary day, move savings first — then spend what's left. Doing it in "
        "reverse rarely sticks.",
    ),
    "fallback_sleep": (
        43,
        "For purchases over your comfort zone, sleep on it. Morning-you almost always "
        "makes the calmer choice.",
    ),
    "fallback_buffer": (
        42,
        "Everyone needs a buffer. Even a small weekly transfer into a separate account "
        "beats waiting for the 'perfect' time to start.",
    ),
    "fallback_quarterly": (
        41,
        "Pick one evening a quarter to cancel apps and services you're not using. "
        "It's boring — and it works.",
    ),
}

_FALLBACK_ORDER = (
    "fallback_track",
    "fallback_payday",
    "fallback_sleep",
    "fallback_buffer",
    "fallback_quarterly",
)


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _planet_house(planets: List[dict], name: str) -> Optional[int]:
    p = _find_p(planets, name)
    if not p:
        return None
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _scan_habit_keys(
    planets: List[dict],
    asc_idx: int,
    wealth_category: str,
    pattern_signals: Dict[str, bool],
) -> List[str]:
    keys: List[str] = []
    lord_2 = SIGN_LORD[SIGNS[(asc_idx + 1) % 12]]
    lord_11 = SIGN_LORD[SIGNS[(asc_idx + 10) % 12]]

    l2 = _find_p(planets, lord_2)
    if l2:
        h2 = int(l2.get("house") or 0)
        sg2 = str(l2.get("sign") or "")
        if h2 in _DUSTHANA:
            keys.append("lord2_dusthana")
        if lord_2 in DEBIL and sg2 == DEBIL[lord_2]:
            keys.append("lord2_debil")

    l11 = _find_p(planets, lord_11)
    if l11:
        h11 = int(l11.get("house") or 0)
        sg11 = str(l11.get("sign") or "")
        if h11 in _DUSTHANA:
            keys.append("lord11_dusthana")
        if lord_11 in DEBIL and sg11 == DEBIL[lord_11]:
            keys.append("lord11_debil")

    for p in planets:
        h = int(p.get("house") or 0)
        nm = p.get("name") or ""
        if h == 2 and nm == "Ketu":
            keys.append("ketu_2h")
        elif h == 2 and nm == "Saturn":
            keys.append("saturn_2h")
        elif h == 2 and nm in ("Rahu", "Mars"):
            keys.append("rahu_mars_2h")
        elif h == 12 and nm in ("Saturn", "Rahu", "Ketu"):
            keys.append("drain_12h")
        elif h == 8 and nm in ("Mars", "Rahu", "Saturn", "Ketu"):
            keys.append("swing_8h")
        elif h == 6 and nm in ("Saturn", "Rahu", "Mars"):
            keys.append("stress_spend_6h")

    rahu = _find_p(planets, "Rahu")
    if rahu and int(rahu.get("house") or 0) in (5, 8):
        keys.append("speculation_5_8")

    if pattern_signals.get("rahu_8") or pattern_signals.get("rahu_11"):
        keys.append("windfall_discipline")

    if wealth_category == "middle_class":
        keys.append("lifestyle_creep")

    return keys


def derive_money_habits(
    planets: List[dict],
    asc_idx: int,
    wealth_category: str,
    pattern_signals: Dict[str, bool],
) -> List[str]:
    """Return 2–3 chart-matched money habits, highest-priority templates first."""
    keys = _scan_habit_keys(planets, asc_idx, wealth_category, pattern_signals)

    ranked: List[Tuple[int, str]] = []
    seen_keys: set = set()
    for key in keys:
        if key in seen_keys or key not in _TEMPLATES:
            continue
        seen_keys.add(key)
        ranked.append(_TEMPLATES[key])

    ranked.sort(key=lambda item: item[0], reverse=True)

    out: List[str] = []
    seen_msgs: set = set()
    for _, msg in ranked:
        if msg in seen_msgs:
            continue
        seen_msgs.add(msg)
        out.append(msg)
        if len(out) >= _MAX_HABITS:
            break

    if len(out) < _MIN_HABITS:
        for key in _FALLBACK_ORDER:
            msg = _TEMPLATES[key][1]
            if msg in seen_msgs:
                continue
            seen_msgs.add(msg)
            out.append(msg)
            if len(out) >= _MIN_HABITS:
                break

    return out[:_MAX_HABITS]
