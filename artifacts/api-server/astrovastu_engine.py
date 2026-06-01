"""
Cosmic AstroVastu — core kundli context, tie-breakers (incl. TB2b Antardasha), severity.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from astrovastu_chart_vastu import DEBILITATION, enrich_chart_vastu_context
from astrovastu_dasha_layer import dasha_activation_check, tie_breaker_dasha_notes
from astrovastu_rules import (
    DIRECTIONS,
    ISHTA_DEVATA_MAP,
    LAGNA_LORD,
    get_dasha_active_direction,
    get_generic_room_rule,
    get_ishta_devata_for_planet,
    get_lagna_directions,
    get_planet_direction,
    get_sign_lord,
)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

MOOL_NAKSHATRAS = {
    "Ashwini", "Ashlesha", "Magha", "Jyeshtha", "Mula", "Revati",
}


def _norm_planet(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return ""
    return n[0].upper() + n[1:].lower() if len(n) > 1 else n.upper()


def _parse_dasha(chart: Dict[str, Any]) -> Tuple[str, str]:
    cd = chart.get("currentDasha") or chart.get("current_dasha") or {}
    if not isinstance(cd, dict):
        cd = {}
    md = _norm_planet(
        cd.get("maha") or cd.get("mahadasha") or cd.get("md") or chart.get("mahadasha") or ""
    )
    ad = _norm_planet(
        cd.get("antar") or cd.get("antardasha") or cd.get("ad") or cd.get("bhukti") or ""
    )
    return md, ad


def _weak_planets(planets: List[dict]) -> List[str]:
    weak: List[str] = []
    for p in planets or []:
        name = _norm_planet(p.get("name") or "")
        if not name:
            continue
        house = int(p.get("house") or 0)
        sign = (p.get("sign") or "").strip()
        if house in (6, 8, 12):
            weak.append(name)
        elif DEBILITATION.get(name) == sign:
            weak.append(name)
    out: List[str] = []
    seen: set[str] = set()
    for w in weak:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def _sade_sati(planets: List[dict], moon_sign: str) -> Dict[str, Any]:
    moon_idx = SIGNS.index(moon_sign) if moon_sign in SIGNS else -1
    saturn = next(
        (p for p in (planets or []) if (p.get("name") or "").lower() == "saturn"),
        None,
    )
    if moon_idx < 0 or not saturn:
        return {"active": False}
    s_idx = SIGNS.index((saturn.get("sign") or "").strip()) if saturn.get("sign") in SIGNS else -1
    if s_idx < 0:
        return {"active": False}
    # Saturn in 12th, 1st, or 2nd from Moon
    rel = (s_idx - moon_idx) % 12
    active = rel in (11, 0, 1)
    return {"active": active, "moon_sign": moon_sign}


def _atmakaraka(planets: List[dict]) -> Optional[str]:
    best = None
    best_lon = -1.0
    for p in planets or []:
        name = (p.get("name") or "").strip()
        if name in ("Rahu", "Ketu", "Ascendant", "Lagna"):
            continue
        lon = float(p.get("longitude") or 0)
        if lon > best_lon:
            best_lon = lon
            best = _norm_planet(name)
    return best


def _ishta_devata(planets: List[dict]) -> Dict[str, Any]:
    ak = _atmakaraka(planets)
    if not ak:
        return {}
    return dict(get_ishta_devata_for_planet(ak) or ISHTA_DEVATA_MAP.get(ak) or {})


def _special_yogas(ctx: Dict[str, Any], planets: List[dict]) -> List[str]:
    yogas: List[str] = []
    if ctx.get("sade_sati", {}).get("active"):
        yogas.append("sade_sati")
    mars = next((p for p in planets if (p.get("name") or "") == "Mars"), None)
    if mars and int(mars.get("house") or 0) in (1, 4, 7, 8, 12):
        yogas.append("manglik")
    rahu_h = {int(p.get("house") or 0) for p in planets if (p.get("name") or "") == "Rahu"}
    ketu_h = {int(p.get("house") or 0) for p in planets if (p.get("name") or "") == "Ketu"}
    if rahu_h and ketu_h and all(h in rahu_h | ketu_h for h in range(1, 13) if h % 2):
        pass  # simplified — flag if Rahu in kendra and all planets on one side
    for p in planets:
        if (p.get("name") or "") == "Rahu" and int(p.get("house") or 0) in (1, 4, 7, 10):
            if len({int(x.get("house") or 0) for x in planets if (x.get("name") or "") not in ("Rahu", "Ketu")}) <= 6:
                yogas.append("kal_sarpa")
                break
    nak = (ctx.get("nakshatra") or "").strip()
    if nak in MOOL_NAKSHATRAS:
        yogas.append("mool_nakshatra")
    return yogas


def build_kundli_context(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw chart_data → engine context dict."""
    chart = chart or {}
    lagna = (chart.get("ascendant") or chart.get("lagna") or "").strip()
    moon = (chart.get("moonSign") or chart.get("moon_sign") or chart.get("rashi") or "").strip()
    planets = list(chart.get("planets") or [])
    md, ad = _parse_dasha(chart)
    weak = _weak_planets(planets)
    sade = _sade_sati(planets, moon)
    ctx: Dict[str, Any] = {
        "lagna": lagna,
        "rashi": moon,
        "moon_sign": moon,
        "nakshatra": chart.get("nakshatra") or "",
        "planets": planets,
        "current_mahadasha": md,
        "current_antardasha": ad,
        "weak_planets": weak,
        "sade_sati": sade,
        "atmakaraka": _atmakaraka(planets),
        "ishta_devata": _ishta_devata(planets),
        "lagna_lord": LAGNA_LORD.get(lagna),
    }
    ctx["special_yogas"] = _special_yogas(ctx, planets)
    return enrich_chart_vastu_context(ctx, planets)


def is_profile_complete(chart: Optional[Dict[str, Any]]) -> bool:
    if not chart:
        return False
    if not (chart.get("ascendant") or chart.get("lagna")):
        return False
    return bool(chart.get("planets"))


def _generic_verdict(direction: str, rule: Dict[str, Any]) -> str:
    ideal = set(rule.get("ideal") or [])
    acc = set(rule.get("acceptable") or [])
    avoid = set(rule.get("avoid") or [])
    if direction in ideal:
        return "Ideal"
    if direction in avoid:
        return "Avoid"
    if direction in acc:
        return "Acceptable"
    return "Adjustment Needed"


def apply_tie_breakers(
    room_type: str,
    direction: str,
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Classical generic verdict + TB1–TB7 overlays (TB2 Mahadasha, TB2b Antardasha).
    """
    key = (room_type or "").strip().lower().replace(" ", "_")
    rule = get_generic_room_rule(key) or {}
    generic = _generic_verdict(direction, rule)
    verdict = generic
    applied: List[str] = []
    refs: List[Dict[str, str]] = []
    reasons: List[str] = []

    lagna = ctx.get("lagna") or ""
    lagna_lord = LAGNA_LORD.get(lagna)
    ll_dir = get_planet_direction(lagna_lord or "") if lagna_lord else None

    # TB1 — Lagna lord direction boosts acceptable→ideal when aligned
    if ll_dir == direction and verdict != "Avoid":
        if verdict == "Acceptable":
            verdict = "Ideal"
        applied.append("TB1")
        reasons.append(f"{lagna} Lagna lord ({lagna_lord}) favours {direction}.")

    # TB2 + TB2b — MD + AD same timing layer
    dasha_notes = tie_breaker_dasha_notes(ctx, direction)
    md = ctx.get("current_mahadasha")
    ad = ctx.get("current_antardasha")
    if md:
        dinfo = get_dasha_active_direction(md) or {}
        if (dinfo.get("direction") or get_planet_direction(md)) == direction:
            if verdict in ("Adjustment Needed", "Acceptable"):
                verdict = "Ideal"
            applied.append("TB2")
    if ad and ad != md:
        ainfo = get_dasha_active_direction(ad) or {}
        if (ainfo.get("direction") or get_planet_direction(ad)) == direction:
            if verdict == "Adjustment Needed":
                verdict = "Acceptable"
            applied.append("TB2b")
    reasons.extend(dasha_notes)

    # TB3 — Sade Sati: West/SW care; downgrade SW placements
    if ctx.get("sade_sati", {}).get("active"):
        applied.append("TB3")
        reasons.append("Sade Sati active — West/South-West zones need extra discipline.")
        if direction in ("West", "South-West") and verdict == "Ideal":
            verdict = "Acceptable"

    # TB4 — Manglik bedroom
    if "manglik" in (ctx.get("special_yogas") or []) and key in ("bedroom", "master_bedroom"):
        applied.append("TB4")
        if direction in ("North-East",):
            if verdict == "Ideal":
                verdict = "Adjustment Needed"
            reasons.append("Manglik chart — NE bedroom needs Mars-friendly remedies.")

    # TB5 — Kal Sarpa
    if "kal_sarpa" in (ctx.get("special_yogas") or []):
        applied.append("TB5")
        reasons.append("Kal Sarpa yoga — keep NE and SW exceptionally clean.")

    # TB6 — Mool Nakshatra
    if "mool_nakshatra" in (ctx.get("special_yogas") or []):
        applied.append("TB6")
        reasons.append("Mool Nakshatra — NE pooja discipline is mandatory.")

    # TB7 — Atmakaraka for soul rooms
    if key in ("pooja", "pooja_room", "study", "meditation"):
        ak = ctx.get("atmakaraka")
        ak_dir = get_planet_direction(ak or "")
        if ak_dir == direction and verdict != "Avoid":
            applied.append("TB7")
            reasons.append(f"Atmakaraka ({ak}) aligns with {direction} for spiritual focus.")

    if lagna:
        lag_info = get_lagna_directions(lagna)
        if lag_info and lag_info.get("vastu_ref"):
            refs.append({"type": "vastu", "source": lag_info["vastu_ref"]})
    if rule.get("vastu_ref"):
        refs.append({"type": "vastu", "source": rule["vastu_ref"]})

    pers_hi = " ".join(reasons[:3]) if reasons else ""
    return {
        "verdict": verdict,
        "generic_verdict": generic,
        "applied_tie_breakers": applied,
        "classical_refs": refs,
        "personalization_reason": pers_hi,
        "reasons": reasons,
    }


def personalized_severity_multiplier(
    direction: str,
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """
  Chart stress + direction-grid aspects + dasha activation → severity multiplier.
    """
    multiplier = 1.0
    reasons: List[str] = []

    for hit in ctx.get("chart_stress_hits") or []:
        amp_dirs = hit.get("amplifies_dosh_in") or []
        if direction in amp_dirs:
            mult = float(hit.get("multiplier") or 1.0)
            multiplier = max(multiplier, mult)
            reasons.append(hit.get("note") or hit.get("condition") or "Chart stress")

    for note in ctx.get("direction_grid_aspects") or []:
        if note.get("direction") == direction:
            multiplier = max(multiplier, 1.3)
            reasons.append(note.get("note") or "Malefic aspect on linked bhava")

    act = dasha_activation_check(ctx)
    if direction in (act.get("amplified_directions") or []):
        multiplier = max(multiplier, 1.5)
        reasons.append(act.get("note_en") or "Dasha activates chart stress")

    if ctx.get("sade_sati", {}).get("active") and direction in ("West", "South-West"):
        multiplier = max(multiplier, 1.4)
        reasons.append("Sade Sati — West/SW sensitivity")

    return {
        "multiplier": round(multiplier, 2),
        "reasons": reasons[:5],
    }
