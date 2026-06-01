"""DCR Love Layer.

Builds a compact D1+D9 love/relationship slice for static love questions.
It does not answer timing questions and does not produce final verdicts.
"""

from __future__ import annotations

import re
from typing import Any


SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
ALIASES = {
    "mesh": "Aries", "vrishabh": "Taurus", "mithun": "Gemini",
    "kark": "Cancer", "karka": "Cancer", "simha": "Leo",
    "kanya": "Virgo", "tula": "Libra", "vrishchik": "Scorpio",
    "dhanu": "Sagittarius", "makar": "Capricorn",
    "kumbh": "Aquarius", "meen": "Pisces",
}

CORE_PLANETS = {"Venus", "Mars", "Moon", "Rahu", "Ketu", "Jupiter", "Saturn", "Mercury"}

BUCKETS: dict[str, dict[str, Any]] = {
    "love_marriage_vs_arranged": {
        "rx": r"love\s*marriage|arrange|arranged|prem\s*vivah|shaadi.*love|love.*shaadi",
        "houses": {2, 5, 7, 9, 11},
        "planets": {"Venus", "Mars", "Moon", "Rahu", "Jupiter", "Saturn"},
    },
    "emotional_attachment": {
        "rx": r"emotional|attachment|attach|feelings?|dil|pyaar|pyar|prem|lagav",
        "houses": {4, 5, 7},
        "planets": {"Moon", "Venus", "Saturn", "Rahu", "Mercury"},
    },
    "practical_relationship_approach": {
        "rx": r"practical|mature|serious|commit|commitment|stable|stability",
        "houses": {2, 7, 9, 10},
        "planets": {"Saturn", "Mercury", "Jupiter", "Venus"},
    },
    "attraction_chemistry": {
        "rx": r"attraction|chemistry|physical|passion|romance|romantic|spark",
        "houses": {5, 7, 8},
        "planets": {"Venus", "Mars", "Moon", "Rahu"},
    },
    "obsession_overattachment": {
        "rx": r"obsess|obsession|over\s*attach|possessive|jealous|control",
        "houses": {5, 8, 12},
        "planets": {"Rahu", "Venus", "Moon", "Mars", "Ketu"},
    },
    "one_sided_love": {
        "rx": r"one\s*sided|ek\s*tarfa|ektarafa|crush|proposal|propose",
        "houses": {5, 7, 11, 12},
        "planets": {"Venus", "Moon", "Rahu", "Saturn"},
    },
    "secret_relationship": {
        "rx": r"secret|hidden|chhup|affair|chakkar|private",
        "houses": {5, 8, 12},
        "planets": {"Rahu", "Ketu", "Venus", "Mars", "Moon"},
    },
    "breakup_separation": {
        "rx": r"breakup|break\s*up|separation|door|dur|distance|toot|chhod",
        "houses": {6, 7, 8, 12},
        "planets": {"Saturn", "Rahu", "Ketu", "Mars", "Venus", "Moon"},
    },
    "patchup_reconciliation": {
        "rx": r"patch|patchup|reconcile|reconciliation|wapas|return|laut",
        "houses": {5, 7, 11},
        "planets": {"Venus", "Moon", "Mercury", "Jupiter", "Saturn"},
    },
    "family_approval": {
        "rx": r"family|ghar\s*wal|parents?|approval|opposition|intercaste|inter\s*caste|religion",
        "houses": {2, 7, 9, 11},
        "planets": {"Jupiter", "Saturn", "Venus", "Rahu", "Sun"},
    },
    "spouse_profession": {
        "rx": (
            r"(?:spouse|partner|husband|wife|pati|patni|jeevan\s*sathi|jeevansathi)"
            r".{0,35}(?:profession|career|job|work|business|naukri|kaam|line|field)"
            r"|(?:profession|career|job|work|business|naukri|kaam|line|field)"
            r".{0,35}(?:spouse|partner|husband|wife|pati|patni|jeevan\s*sathi|jeevansathi)"
        ),
        # 4H = 10th from 7th (spouse profession), 8H = 2nd from 7th
        # (spouse earning/speech), 12H = 6th from 7th (service/workload),
        # 5H = 11th from 7th (gains/network).
        "houses": {4, 5, 7, 8, 10, 12},
        "planets": {"Sun", "Mercury", "Saturn", "Jupiter", "Venus", "Mars", "Rahu"},
    },
    "partner_nature": {
        "rx": (
            r"partner|spouse|husband|wife|pati|patni|jeevan\s*sathi|jeevansathi|"
            r"boyfriend|girlfriend|bf|gf|nature|kaisa|kaisi"
        ),
        "houses": {5, 7},
        "planets": {"Venus", "Mars", "Moon", "Mercury", "Jupiter", "Saturn", "Rahu"},
    },
    "bed_comfort_private_life": {
        "rx": r"bed|intimacy|intimate|private\s*life|physical\s*compat|conjugal|sex|sexual",
        "houses": {7, 8, 12},
        "planets": {"Venus", "Mars", "Moon", "Rahu", "Ketu", "Saturn"},
    },
    "self_worth_boundaries": {
        "rx": r"self\s*worth|boundar|respect|value|insecure|insecurity",
        "houses": {1, 2, 5, 7},
        "planets": {"Sun", "Moon", "Venus", "Saturn", "Rahu"},
    },
}


def is_love_static_question(question: str) -> bool:
    q = (question or "").lower()
    if re.search(r"\b(kab|when|kis\s+saal|timing|date|period)\b", q):
        return False
    return bool(re.search(
        r"love|pyaar|pyar|prem|romance|relationship|partner|crush|bf\b|gf\b|"
        r"boyfriend|girlfriend|breakup|patchup|attachment|attraction|arrange|"
        r"shaadi.*love|love.*shaadi|spouse|husband|wife|pati|patni|"
        r"jeevan\s*sathi|jeevansathi|intimacy|private\s*life",
        q,
    ))


def classify_buckets(question: str, limit: int = 3) -> list[str]:
    q = (question or "").lower()
    found: list[str] = []
    for name, cfg in BUCKETS.items():
        if re.search(cfg["rx"], q):
            found.append(name)
    if not found:
        found = ["partner_nature"]
    return ["core_love_base"] + found[:limit]


def _canon_sign(sign: Any) -> str:
    if not isinstance(sign, str):
        return ""
    s = sign.strip()
    return ALIASES.get(s.lower(), s.title())


def _planet(planets: list[dict], name: str) -> dict | None:
    for p in planets or []:
        if isinstance(p, dict) and str(p.get("name", "")).lower() == name.lower():
            return p
    return None


def _house_sign_lord(asc: str, house: int) -> tuple[str, str]:
    asc = _canon_sign(asc)
    if asc not in SIGNS:
        return "", ""
    sign = SIGNS[(SIGNS.index(asc) + house - 1) % 12]
    return sign, SIGN_LORD[sign]


def _planet_line(p: dict | None) -> str:
    if not p:
        return ""
    parts = [str(p.get("name") or "?")]
    if p.get("sign"):
        parts.append(str(p.get("sign")))
    if p.get("house") is not None:
        parts.append(f"H{p.get('house')}")
    if p.get("nakshatra"):
        parts.append(f"nak:{p.get('nakshatra')}")
    if p.get("dignity"):
        parts.append(f"dignity:{p.get('dignity')}")
    if p.get("retrograde"):
        parts.append("retro")
    return " ".join(parts)


def _house_lines(asc: str, planets: list[dict], houses: set[int]) -> tuple[list[str], set[str]]:
    lines = []
    lord_names = set()
    for h in sorted(houses):
        sign, lord = _house_sign_lord(str(asc), h)
        if sign and lord:
            lord_names.add(lord)
            occupants = [
                p.get("name") for p in planets
                if isinstance(p, dict) and p.get("house") == h
            ]
            lines.append(
                f"{h}H={sign}, lord={lord}, occupants={occupants or []}"
            )
    return lines, lord_names


def _partner_focus_line(label: str, asc: str, planets: list[dict]) -> str:
    sign, lord = _house_sign_lord(str(asc), 7)
    lord_line = _planet_line(_planet(planets, lord)) if lord else ""
    occupants = [
        p.get("name") for p in planets
        if isinstance(p, dict) and p.get("house") == 7
    ]
    if not sign or not lord:
        return f"{label} partner focus: not available"
    return (
        f"{label} partner focus: 7H={sign}, 7L={lord}"
        + (f" ({lord_line})" if lord_line else "")
        + f", 7H occupants={occupants or []}"
    )


def _spouse_profession_focus_line(label: str, asc: str, planets: list[dict]) -> str:
    if _canon_sign(asc) not in SIGNS:
        return f"{label} spouse profession focus: not available"
    items = []
    for title, house in (
        ("10th from spouse/profession", 4),
        ("2nd from spouse/income style", 8),
        ("6th from spouse/work service", 12),
        ("11th from spouse/gains", 5),
    ):
        sign, lord = _house_sign_lord(str(asc), house)
        lord_line = _planet_line(_planet(planets, lord)) if lord else ""
        occupants = [
            p.get("name") for p in planets
            if isinstance(p, dict) and p.get("house") == house
        ]
        if sign and lord:
            items.append(
                f"{title}: H{house}={sign}, lord={lord}"
                + (f" ({lord_line})" if lord_line else "")
                + f", occupants={occupants or []}"
            )
    return f"{label} spouse profession focus: " + " | ".join(items)


def _aspect_diff(a_sign: str, b_sign: str) -> int | None:
    a = _canon_sign(a_sign)
    b = _canon_sign(b_sign)
    if a not in SIGNS or b not in SIGNS:
        return None
    return (SIGNS.index(b) - SIGNS.index(a)) % 12 + 1


def _aspects(aspector: str, a_sign: str, b_sign: str) -> bool:
    diff = _aspect_diff(a_sign, b_sign)
    if diff is None:
        return False
    if diff == 7:
        return True
    if aspector == "Mars" and diff in (4, 8):
        return True
    if aspector == "Jupiter" and diff in (5, 9):
        return True
    if aspector == "Saturn" and diff in (3, 10):
        return True
    return False


def _d9_data(kundli: dict) -> tuple[str, list[dict]]:
    div = kundli.get("divisionalCharts") or {}
    d9 = div.get("D9") or div.get("d9") or kundli.get("navamsa") or {}
    if not isinstance(d9, dict):
        return "", []
    return d9.get("ascendant") or d9.get("lagna") or "", d9.get("planets") or []


def build_dcr_love_context(kundli: dict, question: str) -> tuple[str, dict]:
    if not isinstance(kundli, dict) or not is_love_static_question(question):
        return "", {}

    buckets = classify_buckets(question)
    houses = {5, 7}
    planets = set(CORE_PLANETS)
    for b in buckets:
        cfg = BUCKETS.get(b) or {}
        houses |= set(cfg.get("houses") or set())
        planets |= set(cfg.get("planets") or set())

    asc = kundli.get("ascendant") or kundli.get("lagna") or ""
    d1_planets = kundli.get("planets") or []
    d9_asc, d9_planets = _d9_data(kundli)

    house_lines, lord_names = _house_lines(str(asc), d1_planets, houses)
    d9_house_lines, d9_lord_names = _house_lines(str(d9_asc), d9_planets, houses)
    planets |= lord_names | d9_lord_names

    d1_lines = []
    for name in sorted(planets):
        line = _planet_line(_planet(d1_planets, name))
        if line:
            d1_lines.append(line)

    d9_lines = []
    for name in sorted(planets):
        line = _planet_line(_planet(d9_planets, name))
        if line:
            d9_lines.append(line)

    links = []
    sign5, lord5 = _house_sign_lord(str(asc), 5)
    sign7, lord7 = _house_sign_lord(str(asc), 7)
    p5 = _planet(d1_planets, lord5)
    p7 = _planet(d1_planets, lord7)
    if p5 and p7:
        s5 = _canon_sign(p5.get("sign"))
        s7 = _canon_sign(p7.get("sign"))
        if s5 and s7 and s5 == s7:
            links.append(f"5L-7L conjunction/sign overlap: {lord5}+{lord7} in {s5}")
        elif s5 and s7 and (_aspects(lord5, s5, s7) or _aspects(lord7, s7, s5)):
            links.append(f"5L-7L aspect link: {lord5}({s5}) <-> {lord7}({s7})")
        else:
            links.append(f"5L-7L direct link not obvious: {lord5}({s5}) / {lord7}({s7})")

    for a, b in (("Venus", "Mars"), ("Moon", "Venus")):
        pa, pb = _planet(d1_planets, a), _planet(d1_planets, b)
        if pa and pb:
            sa, sb = _canon_sign(pa.get("sign")), _canon_sign(pb.get("sign"))
            if sa and sb and (sa == sb or _aspects(a, sa, sb) or _aspects(b, sb, sa)):
                links.append(f"{a}-{b} link visible: {sa}/{sb}")

    block = [
        "=== DCR LOVE SLICE (use for love/relationship static answer) ===",
        f"selected_buckets: {buckets}",
        "Instruction: Use only relevant bucket facts. Do not invent missing love factors. Timing is excluded.",
        f"D1 ascendant: {asc}",
        _partner_focus_line("D1", str(asc), d1_planets),
        _spouse_profession_focus_line("D1", str(asc), d1_planets),
        "D1 houses: " + " | ".join(house_lines),
        "D1 relevant planets: " + " | ".join(d1_lines),
        f"D9 ascendant: {d9_asc or 'unknown'}",
        _partner_focus_line("D9", str(d9_asc), d9_planets),
        _spouse_profession_focus_line("D9", str(d9_asc), d9_planets),
        "D9 houses: " + (" | ".join(d9_house_lines) if d9_house_lines else "not available"),
        "D9 relevant planets: " + (" | ".join(d9_lines) if d9_lines else "not available"),
        "Computed love links: " + (" | ".join(links) if links else "not clear"),
        "Checked factors should come from selected_buckets + visible facts only.",
    ]
    meta = {
        "buckets": buckets,
        "houses": sorted(houses),
        "planets": sorted(planets),
    }
    return "\n".join(block), meta


__all__ = ["build_dcr_love_context", "classify_buckets", "is_love_static_question"]
