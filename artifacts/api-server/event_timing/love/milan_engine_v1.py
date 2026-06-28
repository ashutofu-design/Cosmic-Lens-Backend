"""Milan / compatibility engine v1 — two-chart synastry + gun-style score."""
from __future__ import annotations

import re
from typing import Any, Optional

_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_MOON_NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3


def _lagna_si(kundli: dict) -> int:
    asc = (kundli or {}).get("ascendant") or ""
    return _SIGN_NAMES.index(asc) if asc in _SIGN_NAMES else -1


def _house_lord(lagna_si: int, house: int) -> str:
    lords = [
        "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
        "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
    ]
    return lords[(lagna_si + house - 1) % 12]


def _planet_house(planets: list, name: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            h = p.get("house")
            if isinstance(h, int) and 1 <= h <= 12:
                return h
    return None


def _moon_sign_idx(planets: list) -> int:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == "Moon":
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            s = p.get("sign")
            if s in _SIGN_NAMES:
                return _SIGN_NAMES.index(s)
    return -1


def _varna_score(m1: int, m2: int) -> int:
  # simplified 0-1
    return 1 if m1 >= 0 and m2 >= 0 else 0


def _vashya_score(m1: int, m2: int) -> int:
    if m1 < 0 or m2 < 0:
        return 0
    diff = abs(m1 - m2)
    return 2 if diff in {0, 4, 8} else 1 if diff in {2, 6, 10} else 0


def _tara_score(m1: int, m2: int) -> int:
    if m1 < 0 or m2 < 0:
        return 0
    n = ((m2 - m1) % 27) + 1
  # odd = good in classical; simplified
    return 3 if n % 2 == 1 else 1.5


def _yoni_score(v1: str, v2: str) -> int:
    pairs = {("Mars", "Venus"), ("Sun", "Moon"), ("Jupiter", "Mercury")}
    return 4 if (v1, v2) in pairs or (v2, v1) in pairs else 2


def _graha_maitri(m1: int, m2: int) -> int:
    if m1 < 0 or m2 < 0:
        return 0
    l1 = _MOON_NAKSHATRA_LORDS[m1 % 27]
    l2 = _MOON_NAKSHATRA_LORDS[m2 % 27]
    friends = {
        "Sun": {"Moon", "Mars", "Jupiter"},
        "Moon": {"Sun", "Mercury"},
        "Mars": {"Sun", "Moon", "Jupiter"},
        "Mercury": {"Sun", "Venus"},
        "Jupiter": {"Sun", "Moon", "Mars"},
        "Venus": {"Mercury", "Saturn"},
        "Saturn": {"Mercury", "Venus"},
    }
    if l2 in friends.get(l1, set()) or l1 == l2:
        return 5
    return 2


def _gana_score(m1: int, m2: int) -> int:
    return 6 if m1 >= 0 and m2 >= 0 and (m1 + m2) % 3 != 0 else 3


def _bhakoot_score(m1: int, m2: int) -> int:
    if m1 < 0 or m2 < 0:
        return 0
    diff = abs(m1 - m2)
    return 0 if diff in {2, 12, 5, 7} else 7


def _nadi_score(m1: int, m2: int) -> int:
    if m1 < 0 or m2 < 0:
        return 0
    return 0 if (m1 % 3) == (m2 % 3) else 8


def assess_milan(
    kundli_a: dict,
    kundli_b: dict,
    intel_a: Optional[dict] = None,
    intel_b: Optional[dict] = None,
    question: str = "",
) -> dict:
    _ = intel_a, intel_b, question
    pa = kundli_a.get("planets") or []
    pb = kundli_b.get("planets") or []
    la, lb = _lagna_si(kundli_a), _lagna_si(kundli_b)
    ma, mb = _moon_sign_idx(pa), _moon_sign_idx(pb)

    gunas = {
        "varna": _varna_score(ma, mb),
        "vashya": _vashya_score(ma, mb),
        "tara": _tara_score(ma, mb),
        "yoni": _yoni_score("Mars", "Venus"),
        "graha_maitri": _graha_maitri(ma, mb),
        "gana": _gana_score(ma, mb),
        "bhakoot": _bhakoot_score(ma, mb),
        "nadi": _nadi_score(ma, mb),
    }
    total = round(sum(gunas.values()), 1)
    max_g = 36.0
    pct = round(100 * total / max_g, 1) if max_g else 0

    syn_why: list[str] = []
    ven_a, ven_b = _planet_house(pa, "Venus"), _planet_house(pb, "Venus")
    moon_a, moon_b = _planet_house(pa, "Moon"), _planet_house(pb, "Moon")
    if ven_a and ven_b and abs(ven_a - ven_b) <= 1:
        syn_why.append("Venus houses close — mutual attraction tone (+)")
    if moon_a and moon_b and abs(moon_a - moon_b) in {0, 4, 7}:
        syn_why.append("Moon axis supportive — emotional bond (+)")
    if la >= 0 and lb >= 0:
        l7a, l7b = _house_lord(la, 7), _house_lord(lb, 7)
        if l7a == l7b:
            syn_why.append(f"Both 7L {l7a} — partnership style match (+)")

    if total >= 28:
        level = "excellent"
        verdict = "MILAN_STRONG"
    elif total >= 22:
        level = "good"
        verdict = "MILAN_GOOD"
    elif total >= 18:
        level = "moderate"
        verdict = "MILAN_MODERATE"
    else:
        level = "needs_work"
        verdict = "MILAN_CHALLENGING"

    return {
        "engine": "milan_engine_v1",
        "guna_score": total,
        "guna_max": max_g,
        "match_percent": pct,
        "guna_breakdown": gunas,
        "synastry_why": syn_why,
        "compatibility_level": level,
        "verdict": verdict,
        "guards": [
            "Guna milan tendency hai — real relationship mein communication + values zaroori.",
            "18 se neeche = challenging, par impossible nahi — remedies + patience.",
            "Exact event guarantee nahi — compatibility probability only.",
        ],
    }


def format_milan_for_prompt(result: dict, question: str = "") -> str:
    if not result:
        return ""
    lines = [
        "=== KUNDLI MILAN ENGINE v1 (LOCKED) ===",
        f"Guna: {result.get('guna_score')}/{result.get('guna_max')} ({result.get('match_percent')}%)",
        f"Level: {result.get('compatibility_level')} · Verdict: {result.get('verdict')}",
    ]
    gb = result.get("guna_breakdown") or {}
    lines.append("  " + " · ".join(f"{k}={v}" for k, v in gb.items()))
    for w in (result.get("synastry_why") or [])[:4]:
        lines.append(f"  • {w}")
    for g in (result.get("guards") or [])[:3]:
        lines.append(f"  GUARD: {g}")
    return "\n".join(lines)


_MILAN_RX = re.compile(
    r"(?ix)\b(milan|match\s*making|kundli\s*match|guna\s*milan|compatible|"
    r"compatibility|jodi|donon\s*chart|dono\s*chart|hamari\s*jodi)\b",
)


def is_milan_question(question: str) -> bool:
    return bool(_MILAN_RX.search(question or ""))
