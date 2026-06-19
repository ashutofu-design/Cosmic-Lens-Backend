"""Marriage / relationship non-timing chart slice for Cosmic Ask.

Sends only marriage-relevant D1 + D9 facts and pre-calculated flags to the
LLM. No dasha, no Upapada Lagna, no timing windows.
"""

from __future__ import annotations

import re
from typing import Any

from dcr_love import (
    CORE_PLANETS,
    _aspects,
    _canon_sign,
    _d9_data,
    _house_lines,
    _house_sign_lord,
    _partner_focus_line,
    _planet,
    _spouse_profession_focus_line,
)

# Union of all dcr_love bucket houses — covers partner nature, love vs
# arranged, breakup, family approval, spouse profession, intimacy, etc.
MR_HOUSES = {1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12}

MR_PLANETS = set(CORE_PLANETS) | {"Sun"}

_TIMING_RX = re.compile(
    r"\b(kab|kabhi|when|kis\s+saal|kis\s+date|timing|muhurat|muhurt|"
    r"period|tak\s+ho|ho\s+jayegi|ho\s+jayega|ho\s+jaegi|ho\s+jaega|"
    r"kis\s+month|kis\s+mahine|which\s+year|which\s+month)\b",
    re.IGNORECASE,
)

_MR_DOMAIN_RX = re.compile(
    r"\b(shaadi|shadi|marriage|wedding|biwi|wife|husband|pati|patni|spouse|"
    r"partner|boyfriend|girlfriend|bf\b|gf\b|crush|relationship|rishta|"
    r"love|pyar|pyaar|prem|romance|breakup|brek[\s-]?up|divorce|talaq|"
    r"dating|propose|commit(?:ment)?|engagement|sagai|vivah|vivaah|"
    r"saas|sasural|mangetar|fianc|arranged?|love\s*marriage|"
    r"manglik|mangal\s*dosh|intercaste|inter\s*caste|"
    r"affair|cheat|dhokha|loyal|intimacy|intimate|attachment|attraction|"
    r"chemistry|patchup|patch\s*up|separation|ek\s*tarfa|one\s*sided|"
    r"jeevan\s*sathi|jeevansathi|jeevansaathi|kalatra)\b",
    re.IGNORECASE,
)

_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_DEBIL_SIGNS = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
    "Saturn": "Aries",
}
_EXALT_SIGNS = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
    "Saturn": "Libra",
}


def is_marriage_relationship_static_question(question: str) -> bool:
    """True for non-timing marriage / relationship / love domain questions."""
    q = (question or "").strip()
    if not q:
        return False
    if _TIMING_RX.search(q):
        return False
    return bool(_MR_DOMAIN_RX.search(q))


def _lagna_sign_idx(kundli: dict) -> int | None:
    asc = _canon_sign(str(kundli.get("ascendant") or kundli.get("lagna") or ""))
    from dcr_love import SIGNS

    if asc in SIGNS:
        return SIGNS.index(asc)
    deg = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
    try:
        if deg is not None:
            return int(float(deg) % 360 / 30)
    except (TypeError, ValueError):
        pass
    return None


def _vargottama(d1_planets: list[dict], d9_planets: list[dict], name: str) -> bool:
    p1 = _planet(d1_planets, name)
    p9 = _planet(d9_planets, name)
    if not p1 or not p9:
        return False
    s1 = _canon_sign(p1.get("sign"))
    s9 = _canon_sign(p9.get("sign"))
    return bool(s1 and s9 and s1 == s9)


def _dignity_label(planet: str, sign: str) -> str:
    sign = _canon_sign(sign)
    if not sign:
        return "unknown"
    if _EXALT_SIGNS.get(planet) == sign:
        return "exalted"
    if _DEBIL_SIGNS.get(planet) == sign:
        return "debilitated"
    return "neutral"


def _planets_in_house(planets: list[dict], house: int) -> list[str]:
    return [
        str(p.get("name"))
        for p in planets or []
        if isinstance(p, dict) and p.get("house") == house and p.get("name")
    ]


def _malefics_in_house(planets: list[dict], house: int) -> list[str]:
    return [n for n in _planets_in_house(planets, house) if n in _MALEFICS]


def _slim_planet_line(p: dict | None) -> str:
    if not p:
        return ""
    parts = [str(p.get("name") or "?")]
    if p.get("sign"):
        parts.append(str(p.get("sign")))
    if p.get("house") is not None:
        parts.append(f"H{p.get('house')}")
    dig = p.get("dignity")
    if dig:
        parts.append(f"dignity:{dig}")
    if p.get("retrograde"):
        parts.append("retro")
    return " ".join(parts)


def _love_arranged_tilt(d1_planets: list[dict], asc: str) -> str:
    rahu_h = (_planet(d1_planets, "Rahu") or {}).get("house")
    jup_h = (_planet(d1_planets, "Jupiter") or {}).get("house")
    sat_h = (_planet(d1_planets, "Saturn") or {}).get("house")
    _, lord5 = _house_sign_lord(asc, 5)
    _, lord7 = _house_sign_lord(asc, 7)
    p5 = _planet(d1_planets, lord5)
    p7 = _planet(d1_planets, lord7)
    love_signals = 0
    arranged_signals = 0
    if rahu_h in (5, 7, 11):
        love_signals += 1
    if jup_h in (2, 7, 9) or sat_h in (2, 7, 9):
        arranged_signals += 1
    if p5 and p7:
        s5 = _canon_sign(p5.get("sign"))
        s7 = _canon_sign(p7.get("sign"))
        if s5 and s7 and (s5 == s7 or _aspects(lord5, s5, s7) or _aspects(lord7, s7, s5)):
            love_signals += 1
    ven = _planet(d1_planets, "Venus")
    mar = _planet(d1_planets, "Mars")
    if ven and mar:
        sv = _canon_sign(ven.get("sign"))
        sm = _canon_sign(mar.get("sign"))
        if sv and sm and (sv == sm or _aspects("Venus", sv, sm) or _aspects("Mars", sm, sv)):
            love_signals += 1
    if love_signals > arranged_signals:
        return "love_marriage_tilt"
    if arranged_signals > love_signals:
        return "arranged_marriage_tilt"
    return "mixed_neutral"


def _d9_marriage_verdict(d9_asc: str, d9_planets: list[dict]) -> str:
    if not d9_asc or not d9_planets:
        return "d9_unavailable"
    _, lord7 = _house_sign_lord(d9_asc, 7)
    p7l = _planet(d9_planets, lord7)
    ven = _planet(d9_planets, "Venus")
    malefics_7 = _malefics_in_house(d9_planets, 7)
    score = 0
    if p7l:
        h = p7l.get("house")
        sign = _canon_sign(p7l.get("sign"))
        if h in (1, 4, 5, 7, 9, 10, 11):
            score += 1
        if sign and _dignity_label(lord7, sign) == "exalted":
            score += 1
        if sign and _dignity_label(lord7, sign) == "debilitated":
            score -= 1
    if ven:
        vs = _canon_sign(ven.get("sign"))
        if vs and _dignity_label("Venus", vs) == "exalted":
            score += 1
        if vs and _dignity_label("Venus", vs) == "debilitated":
            score -= 1
    if malefics_7:
        score -= 1
    if score >= 2:
        return "d9_marriage_strong"
    if score <= -1:
        return "d9_marriage_strained"
    return "d9_marriage_moderate"


def _compute_manglik(d1_planets: list[dict]) -> bool:
    mars = _planet(d1_planets, "Mars")
    if not mars:
        return False
    h = mars.get("house")
    return isinstance(h, int) and h in (1, 2, 4, 7, 8, 12)


def _venus_afflicted(d1_planets: list[dict]) -> bool:
    ven = _planet(d1_planets, "Venus")
    if not ven:
        return False
    sign = _canon_sign(ven.get("sign"))
    house = ven.get("house")
    if sign and _dignity_label("Venus", sign) == "debilitated":
        return True
    if isinstance(house, int) and house in (6, 8, 12):
        return True
    if ven.get("combust") or str(ven.get("dignity", "")).lower() == "combust":
        return True
    vh = ven.get("house")
    if isinstance(vh, int):
        for p in d1_planets:
            if not isinstance(p, dict):
                continue
            name = str(p.get("name") or "")
            if name in _MALEFICS and p.get("house") == vh and name != "Venus":
                return True
    return False


def _seventh_afflicted(d1_planets: list[dict], asc: str) -> bool:
    if _malefics_in_house(d1_planets, 7):
        return True
    _, lord7 = _house_sign_lord(asc, 7)
    p7l = _planet(d1_planets, lord7)
    if not p7l:
        return False
    h = p7l.get("house")
    if isinstance(h, int) and h in (6, 8, 12):
        return True
    sign = _canon_sign(p7l.get("sign"))
    return bool(sign and _dignity_label(lord7, sign) == "debilitated")


def _marriage_yogas_from_intel(intel: dict) -> list[str]:
    yogas = intel.get("yogas") or []
    if not isinstance(yogas, list):
        return []
    keep = []
    for y in yogas:
        if not isinstance(y, str):
            continue
        low = y.lower()
        if any(k in low for k in (
            "kaal", "kalsarp", "kal sarp", "mangal", "manglik",
            "venus", "kalatra", "marriage", "chandra", "gajakesari",
        )):
            keep.append(y)
    return keep[:6]


def _deep_precalc_enabled() -> bool:
    return (os.environ.get("ASK_MR_SLICE_DEEP") or "").strip() == "1"


def _step0_snapshot(kundli: dict) -> dict[str, Any]:
    if not _deep_precalc_enabled():
        return {}
    out: dict[str, Any] = {}
    try:
        lagna_si = _lagna_sign_idx(kundli)
        if lagna_si is None:
            return out
        from event_timing.marriage.marriage_step0 import run_marriage_step0

        step0 = run_marriage_step0(kundli, lagna_si) or {}
        tendency = step0.get("step0_tendency") or {}
        out["step0_verdict"] = tendency.get("verdict")
        out["combined_pace"] = tendency.get("combined_pace")
        out["d1_pace"] = tendency.get("d1_pace")
        out["d9_pace"] = tendency.get("d9_pace")
        out["delay_vs_late"] = tendency.get("delay_vs_late")
        risks = step0.get("pre_risk_flags") or []
        if isinstance(risks, list):
            out["risk_flags"] = [str(r) for r in risks[:8]]
    except Exception:
        pass
    return out


def _intel_snapshot(kundli: dict) -> dict[str, Any]:
    if not _deep_precalc_enabled():
        return {}
    try:
        from chart_intelligence import analyze_chart

        return analyze_chart(kundli) or {}
    except Exception:
        return {}


def _build_precalc_flags(
    kundli: dict,
    asc: str,
    d1_planets: list[dict],
    d9_planets: list[dict],
    d9_asc: str,
) -> list[str]:
    flags: list[str] = []
    try:
        intel = _intel_snapshot(kundli)
        step0 = _step0_snapshot(kundli)
    except Exception:
        intel = {}
        step0 = {}

    manglik = _compute_manglik(d1_planets)
    md = intel.get("mangal_dosh")
    if isinstance(md, str) and md:
        flags.append(f"mangal_dosh: {md}")
    else:
        flags.append(f"manglik: {'yes' if manglik else 'no'}")

    flags.append(f"venus_afflicted: {'yes' if _venus_afflicted(d1_planets) else 'no'}")
    flags.append(f"7th_house_afflicted: {'yes' if _seventh_afflicted(d1_planets, asc) else 'no'}")

    m7 = _malefics_in_house(d1_planets, 7)
    if m7:
        flags.append(f"malefics_in_7th_D1: {','.join(m7)}")

    _, lord5 = _house_sign_lord(asc, 5)
    _, lord7 = _house_sign_lord(asc, 7)
    vargas = []
    for nm in ("Venus", lord5, lord7):
        if nm and _vargottama(d1_planets, d9_planets, nm):
            vargas.append(nm)
    flags.append(
        "vargottama: " + (", ".join(vargas) if vargas else "none")
    )

    flags.append(f"marriage_tilt: {_love_arranged_tilt(d1_planets, asc)}")
    flags.append(f"d9_marriage: {_d9_marriage_verdict(d9_asc, d9_planets)}")

    p7l = _planet(d1_planets, lord7)
    if p7l and isinstance(p7l.get("house"), int) and p7l["house"] in (6, 8, 12):
        flags.append(f"7th_lord_in_dusthana_D1: H{p7l['house']}")

    # separation / stress pattern (structural, not timing)
    if _malefics_in_house(d1_planets, 8) or _malefics_in_house(d1_planets, 12):
        flags.append("8th_or_12th_stress_for_relationship: yes")

    if step0.get("step0_verdict"):
        flags.append(f"chart_marriage_pace: {step0.get('step0_verdict')}")
    if step0.get("combined_pace"):
        flags.append(f"combined_pace: {step0['combined_pace']}")
    if step0.get("delay_vs_late"):
        flags.append(f"delay_vs_late: {step0['delay_vs_late']}")
    for rf in step0.get("risk_flags") or []:
        flags.append(f"risk: {rf}")

    yogas = _marriage_yogas_from_intel(intel)
    if yogas:
        flags.append("relevant_yogas: " + " | ".join(yogas))

    ven = _planet(d1_planets, "Venus")
    if ven:
        vs = _canon_sign(ven.get("sign"))
        flags.append(
            f"venus_D1: {vs or '?'} H{ven.get('house', '?')} "
            f"({_dignity_label('Venus', vs or '')})"
        )
    jup = _planet(d1_planets, "Jupiter")
    if jup:
        js = _canon_sign(jup.get("sign"))
        flags.append(
            f"jupiter_D1: {js or '?'} H{jup.get('house', '?')} "
            f"({_dignity_label('Jupiter', js or '')})"
        )

    return flags


def build_marriage_relationship_slice(
    kundli: dict,
    question: str = "",
) -> tuple[str, dict]:
    """Build compact marriage/relationship slice (no dasha)."""
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return "(no chart data available)", {}

    asc = str(kundli.get("ascendant") or kundli.get("lagna") or "")
    d1_planets = kundli.get("planets") or []
    d9_asc, d9_planets = _d9_data(kundli)

    house_lines, lord_names = _house_lines(asc, d1_planets, MR_HOUSES)
    d9_house_lines, d9_lord_names = _house_lines(str(d9_asc), d9_planets, MR_HOUSES)
    planets = set(MR_PLANETS) | lord_names | d9_lord_names

    d1_planet_lines = []
    for name in sorted(planets):
        line = _slim_planet_line(_planet(d1_planets, name))
        if line:
            d1_planet_lines.append(line)

    d9_planet_lines = []
    for name in sorted(planets):
        line = _slim_planet_line(_planet(d9_planets, name))
        if line:
            d9_planet_lines.append(line)

    precalc: list[str] = []
    try:
        precalc = _build_precalc_flags(kundli, asc, d1_planets, d9_planets, str(d9_asc))
    except Exception:
        precalc = ["precalc_error: lightweight flags only"]

    block = [
        "=== MARRIAGE / RELATIONSHIP SLICE (narrative — NOT timing) ===",
        "TOPIC: marriage_and_relationship",
        "Instruction: Answer in plain Hinglish. Use only facts below.",
        "Do NOT cite dasha dates/windows. Do NOT invent missing placements.",
        f"D1 ascendant: {asc or 'unknown'}",
        _partner_focus_line("D1", asc, d1_planets),
        _spouse_profession_focus_line("D1", asc, d1_planets),
        "D1 houses: " + " | ".join(house_lines),
        "D1 key planets: " + " | ".join(d1_planet_lines),
        f"D9 ascendant: {d9_asc or 'unknown'}",
        _partner_focus_line("D9", str(d9_asc), d9_planets),
        _spouse_profession_focus_line("D9", str(d9_asc), d9_planets),
        "D9 houses: " + (" | ".join(d9_house_lines) if d9_house_lines else "not available"),
        "D9 key planets: " + (" | ".join(d9_planet_lines) if d9_planet_lines else "not available"),
        "PRE-CALCULATED FLAGS:",
    ]
    block.extend(f"  • {f}" for f in precalc)

    meta = {
        "slice": "marriage_relationship",
        "topic": "marriage_and_relationship",
        "houses": sorted(MR_HOUSES),
        "planets": sorted(planets),
        "flags": precalc,
        "question": (question or "")[:200],
    }
    return "\n".join(block), meta


__all__ = [
    "build_marriage_relationship_slice",
    "is_marriage_relationship_static_question",
]
