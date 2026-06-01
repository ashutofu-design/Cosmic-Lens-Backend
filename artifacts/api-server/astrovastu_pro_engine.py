"""
AstroVastu PRO — multi-room scan, placement copy, Vastu Purusha zones.
Re-exports build_kundli_context; adds analyze_room / analyze_floor_plan.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from astrovastu_dasha_layer import dasha_activation_check, mahadasha_direction_check
from astrovastu_engine import build_kundli_context, is_profile_complete
from astrovastu_report_i18n import placement_summary_hi_dev
from astrovastu_room_pipeline import apply_personalization_layers, build_context_from_chart, score_room_placement
from astrovastu_rules import DIRECTIONS, get_generic_room_rule

VERDICT_SCORE = {
    "Ideal": 92,
    "Acceptable": 78,
    "Adjustment Needed": 48,
    "Avoid": 22,
}

SEV_WEIGHT = {
    "minor": 1,
    "moderate": 2,
    "major": 3,
    "critical": 4,
}

ZONE_LORD = {
    "N": "Kubera",
    "NE": "Ishanya",
    "E": "Indra",
    "SE": "Agni",
    "S": "Yama",
    "SW": "Nairutya",
    "W": "Varuna",
    "NW": "Vayu",
    "C": "Brahma",
}

_DIR_TO_SHORT = {
    "north": "N",
    "north-east": "NE",
    "northeast": "NE",
    "east": "E",
    "south-east": "SE",
    "southeast": "SE",
    "south": "S",
    "south-west": "SW",
    "southwest": "SW",
    "west": "W",
    "north-west": "NW",
    "northwest": "NW",
    "center": "C",
    "centre": "C",
}

_SHORT_TO_LONG = {
    "N": "North",
    "NE": "North-East",
    "E": "East",
    "SE": "South-East",
    "S": "South",
    "SW": "South-West",
    "W": "West",
    "NW": "North-West",
    "C": "Center",
}


def _norm_direction(direction: str) -> str:
    d = (direction or "").strip()
    if not d:
        return ""
    if d in _SHORT_TO_LONG:
        return d
    low = d.lower().replace(" ", "-")
    if low in _DIR_TO_SHORT:
        return _DIR_TO_SHORT[low]
    for long_name in DIRECTIONS:
        if long_name.lower() == low or long_name.lower().replace("-", "") == low.replace("-", ""):
            return _DIR_TO_SHORT.get(
                {"North": "N", "North-East": "NE", "East": "E", "South-East": "SE",
                 "South": "S", "South-West": "SW", "West": "W", "North-West": "NW"}.get(long_name, ""),
                d[:2].upper(),
            )
    return d.upper()[:2] if len(d) <= 3 else d


def _to_long_direction(direction: str) -> str:
    s = _norm_direction(direction)
    if s in _SHORT_TO_LONG:
        return _SHORT_TO_LONG[s]
    for long_name in DIRECTIONS:
        if long_name.lower() == (direction or "").lower():
            return long_name
    return direction or "Unknown"


def _escalate_severity(current: str, delta: int) -> str:
    order = ["minor", "moderate", "major", "critical"]
    try:
        idx = order.index((current or "minor").lower())
    except ValueError:
        idx = 0
    return order[min(len(order) - 1, max(0, idx + delta))]


def _ideal_dirs_short(rule: Dict[str, Any]) -> str:
    ideals = rule.get("ideal") or []
    shorts: List[str] = []
    rev = {v: k for k, v in _SHORT_TO_LONG.items()}
    for d in ideals:
        shorts.append(rev.get(d, _norm_direction(d)))
    return " / ".join(shorts) if shorts else "—"


def compute_placement(
    room_type: str,
    direction: str,
    rule: Dict[str, Any],
    verdict: str,
) -> Dict[str, Any]:
    """Premium PDF placement block (Part A)."""
    cur = _norm_direction(direction)
    cur_long = _to_long_direction(direction)
    ideal_s = _ideal_dirs_short(rule)
    acc = rule.get("acceptable") or []
    acc_short = " / ".join(_norm_direction(a) for a in acc[:4])
    ideal_set = {_norm_direction(x) for x in (rule.get("ideal") or [])}
    avoid_set = {_norm_direction(x) for x in (rule.get("avoid") or [])}
    acc_set = {_norm_direction(x) for x in acc}
    acc_set.add("C")

    if cur == "C" or cur_long == "Center":
        status = "acceptable"
        action = "remedy"
    elif cur in ideal_set or cur_long in {_norm_direction(_to_long_direction(x)) for x in (rule.get("ideal") or [])}:
        status = "correct"
        action = "ok"
    elif cur in avoid_set:
        status = "wrong"
        action = "relocate_or_remedy" if verdict == "Avoid" else "relocate"
    elif cur in acc_set:
        status = "acceptable"
        action = "remedy" if verdict == "Adjustment Needed" else "ok"
    else:
        status = "wrong" if verdict in ("Avoid", "Adjustment Needed") else "mixed"
        action = "relocate_or_remedy" if verdict == "Avoid" else "remedy"

    action_labels = {
        "ok": ("No change needed", "Koi badlav zaroori nahi"),
        "remedy": ("Remedies suggested", "Upaay sujhaye gaye"),
        "relocate": ("Relocate recommended", "Sthan badalne ki sifarish"),
        "relocate_or_remedy": ("Relocate or strong remedy", "Sthan badlein ya prabal upaay"),
    }
    a_en, a_hn = action_labels.get(action, action_labels["remedy"])

    summary_en = placement_summary_hi_dev(
        room_type=room_type,
        cur=cur,
        status=status,
        ideal_s=ideal_s,
        acc_s=acc_short,
        verdict=verdict,
    )
    # English mirror (report_i18n helper is Devanagari-first for hi_dev)
    if status == "acceptable" and cur == "C":
        summary_en = (
            f"{room_type.replace('_', ' ').title()} in Brahmasthan (center) — keep light; "
            f"renovation toward {ideal_s} is better long-term."
        )
    elif status == "correct":
        summary_en = f"Placement matches your chart ideals ({ideal_s}). Maintain cleanliness."
    elif status == "wrong":
        summary_en = f"Placement needs work — ideal {ideal_s} for your chart."
    else:
        summary_en = f"Mixed placement — ideal {ideal_s}; acceptable: {acc_short}."

    return {
        "placement_status": status,
        "ideal_directions_short": ideal_s,
        "acceptable_directions_short": acc_short or "—",
        "classical_ideal_short": ideal_s,
        "action": action,
        "action_label_en": a_en,
        "action_label_hn": a_hn,
        "action_label_hi": a_hn,
        "summary_en": summary_en,
        "summary_hn": summary_en,
        "summary_hi": summary_en,
        "astro_personalized": rule.get("astro_personalized", False),
        "astro_note_en": rule.get("astro_note_en", ""),
    }


def _chart_stress_layer(ctx: Dict[str, Any], room_type: str, direction_long: str) -> Dict[str, Any]:
    hits = ctx.get("chart_stress_hits") or []
    relevant = [
        h for h in hits
        if direction_long in (h.get("amplifies_dosh_in") or [])
    ]
    if not relevant:
        return {"applied": False}
    note = relevant[0].get("note") or relevant[0].get("condition") or ""
    return {
        "applied": True,
        "chart_note_en": f"Your chart: {note}",
        "chart_note_hi": f"Aapki kundli: {note}",
    }


def analyze_room(room: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Single-room PRO analysis."""
    rt = (room.get("room_type") or "").strip().lower().replace(" ", "_")
    d_long = _to_long_direction(room.get("direction") or "")
    d_short = _norm_direction(room.get("direction") or d_long)
    scored = score_room_placement(rt, d_long, ctx, use_personalized_rule=True)
    rule = scored["effective_rule"]
    verdict = scored["verdict"]
    placement = compute_placement(rt, d_short, rule, verdict)
    stress = _chart_stress_layer(ctx, rt, d_long)

    return {
        "room_type": rt,
        "direction": d_short,
        "direction_long": d_long,
        "verdict": verdict,
        "generic_verdict": scored["generic_verdict"],
        "score": VERDICT_SCORE.get(verdict, 50),
        "severity": scored["severity"],
        "severity_label": scored["severity"].title(),
        "multiplier": scored["multiplier"],
        "zone": ZONE_LORD.get(d_short, ""),
        "tie_breaker": scored["tie_breaker"],
        "mahadasha_layer": scored["mahadasha_layer"],
        "chart_stress_layer": stress,
        "placement": placement,
        "generic_rule": get_generic_room_rule(rt) or {},
        "classical_refs": scored["classical_refs"],
        "personalization": scored["personalization"],
        "personalization_reason": scored["personalization_reason"],
        "astro_personalized": scored["astro_personalized"],
        "astro_note_en": scored["astro_note_en"],
        "astro_note_hn": scored["astro_note_hn"],
        "astro_note_hi": scored["astro_note_hi"],
    }


def analyze_floor_plan(
    floor_plan: List[Dict[str, Any]],
    chart_or_ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """Multi-room scan; `chart_or_ctx` may be raw chart_data or pre-built context."""
    if chart_or_ctx.get("lagna") and chart_or_ctx.get("planets") is not None:
        ctx = apply_personalization_layers(chart_or_ctx)
    else:
        ctx = build_context_from_chart(chart_or_ctx)

    rooms = [analyze_room(r, ctx) for r in floor_plan if isinstance(r, dict)]
    counts = {"Ideal": 0, "Acceptable": 0, "Adjustment Needed": 0, "Avoid": 0}
    for r in rooms:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    overall = round(sum(r["score"] for r in rooms) / len(rooms)) if rooms else 0

    def _priority_key(r: Dict[str, Any]) -> tuple:
        sev = SEV_WEIGHT.get(r.get("severity", "minor"), 1)
        vw = {"Avoid": 4, "Adjustment Needed": 3, "Acceptable": 2, "Ideal": 1}.get(r["verdict"], 2)
        md_w = 1 if r.get("mahadasha_layer", {}).get("kind") == "conflict" else 0
        return (-(sev + vw + md_w), r.get("room_type", ""))

    priority = sorted(rooms, key=_priority_key)[:5]

    md_alert = None
    md = ctx.get("current_mahadasha")
    if md:
        from astrovastu_rules import get_planet_direction
        md_dir = _norm_direction(get_planet_direction(md) or "")
        conflicts = [r for r in rooms if r["mahadasha_layer"].get("kind") == "conflict"]
        fav = [r for r in rooms if r["mahadasha_layer"].get("kind") == "favourable"]
        md_alert = {
            "active_lord": md,
            "antardasha": ctx.get("current_antardasha"),
            "lord_direction": md_dir,
            "conflict_rooms": [r["room_type"] for r in conflicts],
            "favourable_rooms": [r["room_type"] for r in fav],
            "summary_en": (
                f"Active Mahadasha {md}"
                + (f" / Antardasha {ctx.get('current_antardasha')}" if ctx.get("current_antardasha") else "")
                + f" — {len(conflicts)} conflict(s), {len(fav)} favoured room(s)."
            ),
            "summary_hi": (
                f"Chal rahi Mahadasha {md}"
                + (f" / Antardasha {ctx.get('current_antardasha')}" if ctx.get("current_antardasha") else "")
                + f" — {len(conflicts)} virodhi, {len(fav)} shubh kamre."
            ),
        }

    return {
        "rooms": rooms,
        "rooms_count": len(rooms),
        "overall_score": overall,
        "verdict_counts": counts,
        "priority_rooms": priority,
        "mahadasha_alert": md_alert,
        "kundli_context": {
            "lagna": ctx.get("lagna"),
            "moon_sign": ctx.get("moon_sign"),
            "mahadasha": ctx.get("current_mahadasha"),
            "antardasha": ctx.get("current_antardasha"),
            "sade_sati": bool(ctx.get("sade_sati", {}).get("active")),
            "atmakaraka": ctx.get("atmakaraka"),
            "ishta_devata": ctx.get("ishta_devata"),
            "weak_planets": ctx.get("weak_planets", []),
            "chart_vastu_active": ctx.get("chart_vastu_active"),
            "chart_stress_hits": ctx.get("chart_stress_hits", []),
            "dasha_activation": ctx.get("dasha_activation"),
        },
    }


__all__ = [
    "analyze_room",
    "analyze_floor_plan",
    "build_kundli_context",
    "compute_placement",
    "dasha_activation_check",
    "is_profile_complete",
    "mahadasha_direction_check",
    "VERDICT_SCORE",
    "SEV_WEIGHT",
    "ZONE_LORD",
    "_norm_direction",
    "_to_long_direction",
    "_escalate_severity",
]
