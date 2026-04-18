"""
AstroVastu PRO engine — multi-room deep-scan with mahadasha-mandatory layer.

Pipeline per room:
  1. Generic Vastu rule (room_type × direction)
  2. Tie-breakers (Sade-Sati, kaal-sarp, lagna lord, ishta devata, atmakaraka)
  3. Personalized severity multiplier
  4. *** Mahadasha-mandatory layer *** — every PRO room is checked against the
     ACTIVE Mahadasha lord's natural direction. If the room placement conflicts
     with the running dasha lord's direction, severity is escalated.

Cross-room synthesis:
  - Vastu Purusha 9-zone grid mapping (which planetary zone each room occupies)
  - Overall house score 0–100
  - Priority action plan (sorted by severity × kundli weight)

Deterministic — no LLM. No external network. Same inputs → same outputs.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from astrovastu_engine import (
    apply_tie_breakers, personalized_severity_multiplier,
    adjusted_severity_label, build_kundli_context,
)
from astrovastu_rules import (
    get_generic_room_rule, get_planet_direction, get_dasha_active_direction,
)


# ── Direction normalization (matches astrovastu_engine) ────────────────────
DIRECTION_ALIASES = {
    "n": "N", "north": "N", "N": "N",
    "ne": "NE", "north-east": "NE", "northeast": "NE", "NE": "NE",
    "e": "E", "east": "E", "E": "E",
    "se": "SE", "south-east": "SE", "southeast": "SE", "SE": "SE",
    "s": "S", "south": "S", "S": "S",
    "sw": "SW", "south-west": "SW", "southwest": "SW", "SW": "SW",
    "w": "W", "west": "W", "W": "W",
    "nw": "NW", "north-west": "NW", "northwest": "NW", "NW": "NW",
    "center": "C", "centre": "C", "c": "C", "C": "C",
}


def _norm_direction(d: str) -> str:
    return DIRECTION_ALIASES.get((d or "").strip().lower(), (d or "").strip().upper())


# Short-code → canonical long form expected by astrovastu_engine / astrovastu_rules
SHORT_TO_LONG: Dict[str, str] = {
    "N":  "North",      "NE": "North-East", "E":  "East",       "SE": "South-East",
    "S":  "South",      "SW": "South-West", "W":  "West",       "NW": "North-West",
    "C":  "Center",
}


def _to_long_direction(d: str) -> str:
    """Convert any direction representation to the long form that base
    astrovastu_engine.apply_tie_breakers / personalized_severity_multiplier expect."""
    short = _norm_direction(d)
    return SHORT_TO_LONG.get(short, d)


# ── Vastu Purusha 9-zone grid (planetary lordship per direction) ───────────
# Brihat Samhita ch. 53 — each compass direction is ruled by a planet/deity.
ZONE_LORD: Dict[str, Dict[str, str]] = {
    "N":  {"planet": "Mercury", "deity": "Kubera",  "element": "water"},
    "NE": {"planet": "Jupiter", "deity": "Ishana",  "element": "water"},
    "E":  {"planet": "Sun",     "deity": "Indra",   "element": "air"},
    "SE": {"planet": "Venus",   "deity": "Agni",    "element": "fire"},
    "S":  {"planet": "Mars",    "deity": "Yama",    "element": "fire"},
    "SW": {"planet": "Rahu",    "deity": "Nirriti", "element": "earth"},
    "W":  {"planet": "Saturn",  "deity": "Varuna",  "element": "water"},
    "NW": {"planet": "Moon",    "deity": "Vayu",    "element": "air"},
    "C":  {"planet": "Ketu",    "deity": "Brahma",  "element": "ether"},
}

# Verdict scoring (used for overall_score 0–100)
VERDICT_SCORE = {
    "Ideal":              100,
    "Acceptable":          75,
    "Adjustment Needed":   45,
    "Avoid":               15,
}

# Severity weights for priority sort
SEV_WEIGHT = {"critical": 4, "major": 3, "moderate": 2, "minor": 1}


# ── Mahadasha-mandatory rule ───────────────────────────────────────────────
def mahadasha_direction_check(direction: str, mahadasha_lord: Optional[str]) -> Dict[str, Any]:
    """
    Returns whether the room placement conflicts with the active Mahadasha
    lord's natural direction.

    Logic (Brihat Samhita-aligned):
      - If room sits in the dasha lord's OWN direction → boost (favourable)
      - If room sits in the dasha lord's 7th/opposite direction → conflict
      - Otherwise neutral
    """
    if not mahadasha_lord:
        return {"applies": False}

    md_lord = mahadasha_lord.strip().capitalize()
    dasha_info = get_dasha_active_direction(md_lord)
    if dasha_info and isinstance(dasha_info, dict):
        md_dir_raw = dasha_info.get("direction")
    else:
        md_dir_raw = get_planet_direction(md_lord)
    if not md_dir_raw:
        return {"applies": False}

    md_dir = _norm_direction(md_dir_raw)
    direction = _norm_direction(direction)

    OPPOSITE = {"N":"S","S":"N","E":"W","W":"E","NE":"SW","SW":"NE","NW":"SE","SE":"NW"}

    if direction == md_dir:
        return {
            "applies": True, "kind": "favourable", "md_lord": md_lord, "md_direction": md_dir,
            "reason_en": f"Active Mahadasha of {md_lord} amplifies this {md_dir} placement positively.",
            "reason_hi": f"Chal rahi {md_lord} Mahadasha is {md_dir} sthaan ko shubh banati hai.",
            "severity_delta": -1,    # one level lighter
        }
    if direction == OPPOSITE.get(md_dir):
        return {
            "applies": True, "kind": "conflict", "md_lord": md_lord, "md_direction": md_dir,
            "reason_en": f"Active Mahadasha of {md_lord} (rules {md_dir}) directly opposes this {direction} placement.",
            "reason_hi": f"Chal rahi {md_lord} Mahadasha ({md_dir} ka swami) is {direction} sthaan ke virodhi hai.",
            "severity_delta": +1,    # one level heavier
        }
    return {"applies": True, "kind": "neutral", "md_lord": md_lord, "md_direction": md_dir,
            "severity_delta": 0}


def _escalate_severity(sev: str, delta: int) -> str:
    order = ["minor", "moderate", "major", "critical"]
    try:
        i = order.index(sev)
    except ValueError:
        i = 0
    j = max(0, min(len(order) - 1, i + delta))
    return order[j]


# ── Per-room analysis ──────────────────────────────────────────────────────
def analyze_room(room: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full PRO pipeline on one room.
    Input  : {"room_type": str, "direction": str}
    Output : per-room verdict dict with mahadasha layer applied.
    """
    room_type = (room.get("room_type") or "").strip().lower()
    direction = _norm_direction(room.get("direction") or "")
    direction_long = _to_long_direction(direction)

    if not room_type or not direction:
        return {
            "room_type": room_type, "direction": direction,
            "verdict": "Avoid", "severity": "moderate", "multiplier": 1.0,
            "error": "missing room_type or direction",
            "mahadasha_layer": {"applies": False},
            "score": VERDICT_SCORE["Avoid"],
        }

    rule = get_generic_room_rule(room_type) or {}
    # Base engine expects long form ("North-East") — pass that, not the short code.
    tb_res  = apply_tie_breakers(room_type, direction_long, ctx)
    sev_res = personalized_severity_multiplier(direction_long, ctx)

    verdict = tb_res.get("verdict") or rule.get("verdict") or "Acceptable"
    base_severity = sev_res.get("severity", "minor")
    multiplier    = sev_res.get("multiplier", 1.0)

    # ── Mahadasha-mandatory layer ──
    md_layer = mahadasha_direction_check(direction, ctx.get("current_mahadasha"))
    severity = base_severity
    if md_layer.get("applies"):
        severity = _escalate_severity(base_severity, md_layer.get("severity_delta", 0))
        # If conflict + verdict was Ideal/Acceptable, downgrade to Adjustment Needed
        if md_layer["kind"] == "conflict" and verdict in ("Ideal", "Acceptable"):
            verdict = "Adjustment Needed"
        # If favourable + verdict was Adjustment Needed and severity ≤ moderate, upgrade
        if md_layer["kind"] == "favourable" and verdict == "Adjustment Needed" and severity in ("minor", "moderate"):
            verdict = "Acceptable"

    final_label = adjusted_severity_label(base_severity, multiplier)
    zone = ZONE_LORD.get(direction, {})

    return {
        "room_type":       room_type,
        "direction":       direction,
        "direction_long":  direction_long,
        "verdict":         verdict,
        "generic_verdict": tb_res.get("generic_verdict") or rule.get("verdict") or "Acceptable",
        "severity":        severity,
        "severity_label":  final_label,
        "multiplier":      round(multiplier, 2),
        "score":           VERDICT_SCORE.get(verdict, 50),
        "tie_breaker":     {
            "applied": tb_res.get("applied_tie_breakers", []),
            "reasons": tb_res.get("reasons", []),
        },
        "classical_refs":      tb_res.get("classical_refs", []),
        "personalization_reason": tb_res.get("personalization_reason", {"en": "", "hi": ""}),
        "personalization": {
            "reasons":    sev_res.get("reasons", []),
            "multiplier": multiplier,
        },
        "mahadasha_layer": md_layer,
        "zone": {
            "direction": direction,
            "planet":    zone.get("planet"),
            "deity":     zone.get("deity"),
            "element":   zone.get("element"),
        },
        "generic_rule": {
            "verdict":  rule.get("verdict"),
            "summary":  rule.get("summary"),
            "citation": rule.get("citation"),
        },
    }


# ── Cross-room synthesis ───────────────────────────────────────────────────
def _priority_sort_key(r: Dict[str, Any]) -> tuple:
    """Sort rooms by attention priority — highest first."""
    sev_w = SEV_WEIGHT.get(r.get("severity", "minor"), 1)
    verdict_w = {"Avoid": 4, "Adjustment Needed": 3, "Acceptable": 2, "Ideal": 1}.get(
        r.get("verdict", "Acceptable"), 2
    )
    md_w = 1 if r.get("mahadasha_layer", {}).get("kind") == "conflict" else 0
    # Higher tuple = higher priority — invert for sort ascending
    return (-(sev_w + verdict_w + md_w), r.get("room_type", ""))


def analyze_floor_plan(floor_plan: List[Dict[str, Any]],
                       kundli: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top-level PRO entry point.
    Returns a structured deep-scan result for the entire floor plan.
    """
    if not floor_plan or not isinstance(floor_plan, list):
        return {"error": "empty_floor_plan", "rooms": []}

    ctx = build_kundli_context(kundli)
    rooms = [analyze_room(r, ctx) for r in floor_plan if isinstance(r, dict)]

    # ── Aggregate metrics ──
    if rooms:
        overall_score = round(sum(r["score"] for r in rooms) / len(rooms))
    else:
        overall_score = 0

    counts = {"Ideal": 0, "Acceptable": 0, "Adjustment Needed": 0, "Avoid": 0}
    for r in rooms:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    # Priority list — most-urgent rooms first (max 5)
    priority = sorted(rooms, key=_priority_sort_key)[:5]

    # Mahadasha-wide alert (if active dasha lord found)
    md_alert = None
    md_lord = ctx.get("current_mahadasha")
    if md_lord:
        dasha_info = get_dasha_active_direction(md_lord)
        md_dir_raw = (dasha_info.get("direction")
                      if isinstance(dasha_info, dict) else None) or get_planet_direction(md_lord)
        if md_dir_raw:
            md_dir_norm = _norm_direction(md_dir_raw)
            conflicts = [r for r in rooms if r["mahadasha_layer"].get("kind") == "conflict"]
            favourables = [r for r in rooms if r["mahadasha_layer"].get("kind") == "favourable"]
            md_alert = {
                "active_lord":     md_lord,
                "lord_direction":  md_dir_norm,
                "conflict_rooms":  [r["room_type"] for r in conflicts],
                "favourable_rooms":[r["room_type"] for r in favourables],
                "summary_en":      (f"Active Mahadasha: {md_lord} (rules {md_dir_norm}). "
                                    f"{len(conflicts)} room(s) conflict, "
                                    f"{len(favourables)} room(s) favoured."),
                "summary_hi":      (f"Chal rahi Mahadasha: {md_lord} ({md_dir_norm} ka swami). "
                                    f"{len(conflicts)} kamre virodhi, "
                                    f"{len(favourables)} kamre shubh."),
            }

    return {
        "rooms":          rooms,
        "rooms_count":    len(rooms),
        "overall_score":  overall_score,
        "verdict_counts": counts,
        "priority_rooms": priority,
        "mahadasha_alert": md_alert,
        "kundli_context": {
            "lagna":        ctx.get("lagna"),
            "moon_sign":    ctx.get("moon_sign"),
            "mahadasha":    ctx.get("current_mahadasha"),
            "sade_sati":    (ctx.get("sade_sati") or {}).get("active", False)
                            if isinstance(ctx.get("sade_sati"), dict) else bool(ctx.get("sade_sati")),
            "atmakaraka":   ctx.get("atmakaraka"),
            "ishta_devata": ctx.get("ishta_devata"),
        },
    }
