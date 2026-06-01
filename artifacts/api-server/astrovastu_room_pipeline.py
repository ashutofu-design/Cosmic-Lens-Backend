"""
Shared BASIC + PRO room pipeline — personalization layers then scoring inputs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from astrovastu_astro_rules import get_effective_room_rule
from astrovastu_chart_vastu import enrich_chart_vastu_context
from astrovastu_dasha_layer import dasha_activation_check, mahadasha_direction_check
from astrovastu_engine import apply_tie_breakers, build_kundli_context, personalized_severity_multiplier
from astrovastu_rules import get_generic_room_rule


def apply_personalization_layers(
    ctx: Dict[str, Any],
    chart: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Enrich kundli context for both BASIC and PRO:
      chart stress, direction-grid aspects, dasha activation snapshot.
    """
    planets = (chart or {}).get("planets") if chart else None
    out = enrich_chart_vastu_context(dict(ctx), planets)
    out["dasha_activation"] = dasha_activation_check(out)
    return out


def build_context_from_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Full context path used by routes."""
    return apply_personalization_layers(build_kundli_context(chart), chart)


def score_room_placement(
    room_type: str,
    direction_long: str,
    ctx: Dict[str, Any],
    *,
    use_personalized_rule: bool = True,
) -> Dict[str, Any]:
    """
    Core verdict + severity for one room (BASIC and PRO).
    """
    key = (room_type or "").strip().lower().replace(" ", "_")
    rule = (
        get_effective_room_rule(key, ctx)
        if use_personalized_rule
        else (get_generic_room_rule(key) or {})
    )
    tb = apply_tie_breakers(key, direction_long, ctx)
    sev = personalized_severity_multiplier(direction_long, ctx)
    md_layer = mahadasha_direction_check(key, direction_long, ctx)

    # Mahadasha conflict can pull verdict down one step
    verdict = tb["verdict"]
    if md_layer.get("kind") == "conflict" and verdict == "Ideal":
        verdict = "Acceptable"
    elif md_layer.get("kind") == "conflict" and verdict == "Acceptable":
        verdict = "Adjustment Needed"
    elif md_layer.get("kind") == "favourable" and verdict == "Adjustment Needed":
        verdict = "Acceptable"

    mult = float(sev.get("multiplier") or 1.0)
    if mult >= 2.0:
        severity = "major"
    elif mult >= 1.4:
        severity = "moderate"
    else:
        severity = "minor"
    if verdict == "Avoid" and severity == "minor":
        severity = "moderate"
    if verdict == "Avoid" and mult >= 1.8:
        severity = "major"

    return {
        "verdict": verdict,
        "generic_verdict": tb.get("generic_verdict"),
        "tie_breaker": {
            "applied": tb.get("applied_tie_breakers", []),
            "reasons": tb.get("reasons", []),
        },
        "severity": severity,
        "multiplier": mult,
        "personalization": {"reasons": sev.get("reasons", [])},
        "mahadasha_layer": md_layer,
        "effective_rule": rule,
        "classical_refs": tb.get("classical_refs", []),
        "personalization_reason": {
            "en": " ".join(tb.get("reasons") or [])[:400],
            "hi": tb.get("personalization_reason") or "",
        },
        "astro_personalized": bool(rule.get("astro_personalized")),
        "astro_note_en": rule.get("astro_note_en") or "",
        "astro_note_hn": rule.get("astro_note_hn") or "",
        "astro_note_hi": rule.get("astro_note_hi") or rule.get("astro_note_hi_dev") or "",
    }
