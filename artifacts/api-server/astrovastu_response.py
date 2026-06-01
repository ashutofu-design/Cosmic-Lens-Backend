"""
AstroVastu — BASIC tier deterministic response builder.

Takes the output of the AstroVastu rules engine (apply_tie_breakers +
personalized_severity_multiplier) and produces a user-facing JSON response:
verdict pill, bilingual personalization reason, prioritized remedies, dedup'd
classical references, and metadata.

Pure function — no LLM call (BASIC tier cost target ~₹0.50/check; achieved by
keeping this fully rule-based).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from astrovastu_rules import (
    BRANDING_LINE,
    ENGINE_NAME,
    ENGINE_VERSION,
    COLOR_BY_LAGNA_LORD,
    YOGA_COLOR_OVERRIDE,
    LAGNA_LORD,
    get_yantra_for_planet,
    get_dasha_active_direction,
    get_planet_direction,
)


# ─────────────────────────────────────────────────────────────────────────
# Severity → number-of-remedies budget (item 23)
# ─────────────────────────────────────────────────────────────────────────
REMEDY_BUDGET: Dict[str, int] = {
    "Avoid":             3,
    "Adjustment Needed": 3,
    "Acceptable":        2,
    "Ideal":             1,
}

VERDICT_TONE: Dict[str, str] = {
    "Avoid":             "critical",
    "Adjustment Needed": "warning",
    "Acceptable":        "ok",
    "Ideal":             "excellent",
}

# Bilingual verdict labels for UI pill
VERDICT_LABEL: Dict[str, Dict[str, str]] = {
    "Avoid":             {"en": "Avoid",            "hi": "Bachein"},
    "Adjustment Needed": {"en": "Adjustment Needed", "hi": "Sudhaar Zaroori"},
    "Acceptable":        {"en": "Acceptable",       "hi": "Theek Hai"},
    "Ideal":             {"en": "Ideal",            "hi": "Uttam"},
}

# Severity bucket → human label
SEVERITY_LABEL: Dict[str, Dict[str, str]] = {
    "minor":    {"en": "Minor",    "hi": "Halka"},
    "moderate": {"en": "Moderate", "hi": "Madhyam"},
    "major":    {"en": "Major",    "hi": "Tez"},
}


# ─────────────────────────────────────────────────────────────────────────
# Remedy generators — each returns Optional[remedy] or None if not applicable
# Each remedy: {action, hindi, english, priority (1=highest), classical_ref}
# ─────────────────────────────────────────────────────────────────────────

def _remedy_color(
    ctx: Dict[str, Any],
    direction: str,
    room_type: str,
) -> Optional[Dict[str, Any]]:
    lagna = ctx.get("lagna")
    lord  = LAGNA_LORD.get(lagna or "")
    if not lord:
        return None
    palette = COLOR_BY_LAGNA_LORD.get(lord)
    if not palette:
        return None
    avoid_line = palette["avoid"]
    # Do not paste NE-only warnings into NW/SW/SE rooms (common copy-paste bug).
    if ("NE" in avoid_line or "North-East" in avoid_line) and direction != "North-East":
        avoid_line = "heavy or clashing colours dominating this room's walls"
    if "couple bedroom" in avoid_line.lower() and room_type not in (
        "bedroom", "master_bedroom",
    ):
        avoid_line = "colours that disturb calm in this zone"
    return {
        "action":   "color",
        "english":  f"Use {palette['primary']} as primary palette in this {direction} zone; avoid {avoid_line}.",
        "hindi":    f"{direction} zone mein mukhya rang: {palette['primary']}. Bachein: {avoid_line}.",
        "priority": 2,
        "classical_ref": f"Color guidance per {lagna} Lagna lord ({lord}) — scoped to {direction}",
    }


def _remedy_yoga_color(ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    yogas = [y.lower() for y in (ctx.get("special_yogas") or [])]
    if ctx.get("sade_sati", {}).get("active"):
        yogas.append("sade_sati")
    for y in yogas:
        ov = YOGA_COLOR_OVERRIDE.get(y)
        if ov:
            parts_en = []
            parts_hi = []
            if ov.get("add"):
                parts_en.append(f"Add {ov['add']}")
                parts_hi.append(f"Jodhein: {ov['add']}")
            if ov.get("avoid"):
                parts_en.append(f"avoid {ov['avoid']}")
                parts_hi.append(f"bachein: {ov['avoid']}")
            if ov.get("soft"):
                parts_en.append(f"soft tones okay ({ov['soft']})")
                parts_hi.append(f"halke rang theek ({ov['soft']})")
            return {
                "action":   "yoga_color",
                "english":  "; ".join(parts_en).capitalize() + ".",
                "hindi":    "; ".join(parts_hi).capitalize() + ".",
                "priority": 1,
                "classical_ref": f"{y.replace('_',' ').title()} colour discipline",
            }
    return None


def _remedy_yantra_for_weak_planet(ctx: Dict[str, Any], direction: str) -> Optional[Dict[str, Any]]:
    """If a weak planet's direction matches the user's room direction, prescribe its yantra."""
    weak = ctx.get("weak_planets") or []
    for planet_entry in weak:
        # weak_planets is list of dicts {name, score, ...} OR list of names — handle both
        name = planet_entry["name"] if isinstance(planet_entry, dict) else planet_entry
        if get_planet_direction(name) == direction:
            y = get_yantra_for_planet(name)
            if y:
                return {
                    "action":   "yantra",
                    "english":  f"Place {y['yantra']} ({y['material']}) on the {y['wall']} wall; energise on {y['day']}.",
                    "hindi":    f"{y['wall']} deewar par {y['yantra']} ({y['material']}) lagayein; {y['day']} ko sthapana karein.",
                    "priority": 1,
                    "classical_ref": f"{y.get('vastu_ref','—')} / {y.get('jyotish_ref','—')}",
                }
    return None


def _remedy_dasha_care(ctx: Dict[str, Any], direction: str) -> Optional[Dict[str, Any]]:
    md = ctx.get("current_mahadasha")
    if not md:
        return None
    info = get_dasha_active_direction(md)
    if not info or info["direction"] != direction:
        return None
    return {
        "action":   "dasha_care",
        "english":  f"{md} Mahadasha is active — keep this direction clean and place {info['items']}; lamp on {info['day']}.",
        "hindi":    f"{md} Mahadasha chal rahi hai — yeh disha saaf rakhein, {info['items']} rakhein; {info['day']} ko deepak.",
        "priority": 1,
        "classical_ref": f"{info.get('vastu_ref','—')} / {info.get('jyotish_ref','—')}",
    }


def _remedy_ishta_facing(ctx: Dict[str, Any], room_type: str) -> Optional[Dict[str, Any]]:
    if room_type not in ("pooja", "study", "meditation"):
        return None
    ishta = ctx.get("ishta_devata") or {}
    deity = ishta.get("deity")
    facing = ishta.get("facing") or ishta.get("direction")
    if not (deity and facing):
        return None
    return {
        "action":   "ishta_facing",
        "english":  f"While praying/meditating, face {facing} — your Ishta Devata is {deity}.",
        "hindi":    f"Pooja/dhyaan ke samay {facing} disha mein mukh karein — aapke Ishta Devata: {deity}.",
        "priority": 1,
        "classical_ref": "BPHS Ch.32 (Karakamsa method)",
    }


def _remedy_directional_alternative(direction: str, generic_verdict: str,
                                    rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """If the chosen direction is in 'avoid' list, suggest the room's ideal direction."""
    if generic_verdict not in ("Avoid", "Adjustment Needed"):
        return None
    ideal = (rule.get("ideal") or [None])[0] if rule else None
    if not ideal or ideal == direction:
        return None
    return {
        "action":   "directional_alternative",
        "english":  f"If renovation is possible, the classical ideal for this room is the {ideal} sector.",
        "hindi":    f"Agar renovation sambhav ho, is kamre ke liye uttam disha {ideal} hai.",
        "priority": 3,
        "classical_ref": rule.get("vastu_ref", "—"),
    }


def _remedy_cleanliness(direction: str) -> Dict[str, Any]:
    """Universal fallback — direction-specific cleanliness (always safe)."""
    return {
        "action":   "cleanliness",
        "english":  f"Keep the {direction} corner clutter-free — daily wipe and weekly deep-clean.",
        "hindi":    f"{direction} kona saaf rakhein — roz pochha, hafte mein gehri safai.",
        "priority": 4,
        "classical_ref": "Mayamatam Ch.7 (general cleanliness)",
    }


def _remedy_enhancement(direction: str) -> Dict[str, Any]:
    """For Ideal verdict — small enhancement to amplify the good placement."""
    return {
        "action":   "enhancement",
        "english":  f"This placement is excellent. Enhance with fresh flowers or a small lamp in the {direction} corner.",
        "hindi":    f"Yeh sthaan uttam hai. {direction} kone mein taaze phool ya chhota deepak rakhein.",
        "priority": 5,
        "classical_ref": "Vastu Saar Ch.10 (auspicious enhancement)",
    }


# ─────────────────────────────────────────────────────────────────────────
# Main builder
# ─────────────────────────────────────────────────────────────────────────
def build_basic_response(
    *,
    room_type: str,
    direction: str,
    kundli_context: Dict[str, Any],
    tie_breaker_result: Dict[str, Any],
    severity_result: Dict[str, Any],
    generic_room_rule: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compose the full BASIC AstroVastu response.

    Inputs:
      - room_type, direction       — user's chosen placement
      - kundli_context             — output of build_kundli_context()
      - tie_breaker_result         — output of apply_tie_breakers()
      - severity_result            — output of personalized_severity_multiplier()
      - generic_room_rule          — output of get_generic_room_rule(room_type) (optional)

    Output schema (stable):
      {
        verdict:          "Ideal"|"Acceptable"|"Adjustment Needed"|"Avoid",
        verdict_label:    {en, hi},
        verdict_tone:     "excellent"|"ok"|"warning"|"critical",
        generic_verdict:  ...,
        severity:         {bucket, label:{en,hi}, multiplier, reasons[]},
        personalization_reason: {en, hi},
        remedies:         [ {action, english, hindi, priority, classical_ref} ],
        classical_refs:   [ {type, source} ],
        applied_tie_breakers: [...],
        meta:             {engine, version, branding, room_type, direction,
                           lagna, rashi, mahadasha, sade_sati, ishta_devata}
      }
    """
    verdict          = tie_breaker_result.get("verdict", "Acceptable")
    generic_verdict  = tie_breaker_result.get("generic_verdict", verdict)
    applied          = tie_breaker_result.get("applied_tie_breakers", [])
    refs             = list(tie_breaker_result.get("classical_refs", []))
    pers_reason_hi   = tie_breaker_result.get("personalization_reason", "")

    multiplier = severity_result.get("multiplier", 1.0)
    sev_reasons = severity_result.get("reasons", [])
    if multiplier >= 2.0:
        sev_bucket = "major"
    elif multiplier >= 1.2:
        sev_bucket = "moderate"
    else:
        sev_bucket = "minor"

    # ── Bilingual personalization reason ──
    if not pers_reason_hi:
        pers_reason_hi = (
            f"Aapki {kundli_context.get('lagna','—')} Lagna ke aadhaar par yeh "
            f"placement ka verdict: {VERDICT_LABEL[verdict]['hi']}."
        )
    pers_reason_en = (
        f"Based on your {kundli_context.get('lagna','—')} Lagna, the verdict for "
        f"this placement is: {VERDICT_LABEL[verdict]['en']}."
    )

    # ── Remedy generation pipeline (priority order) ──
    candidates: List[Optional[Dict[str, Any]]] = [
        _remedy_yoga_color(kundli_context),
        _remedy_yantra_for_weak_planet(kundli_context, direction),
        _remedy_dasha_care(kundli_context, direction),
        _remedy_ishta_facing(kundli_context, room_type),
        _remedy_color(kundli_context, direction, room_type),
        _remedy_directional_alternative(direction, generic_verdict, generic_room_rule or {}),
    ]
    remedies = [r for r in candidates if r is not None]

    # Always add cleanliness fallback (priority 4)
    remedies.append(_remedy_cleanliness(direction))

    # ── Ideal verdict: amplify, don't correct.
    # Enhancement must survive the budget=1 truncation, so we make it the
    # single highest-priority candidate (priority 0) for Ideal placements.
    if verdict == "Ideal":
        enh = _remedy_enhancement(direction)
        enh["priority"] = 0
        remedies = [enh] + remedies

    # Sort by priority (lowest number = highest priority) and dedupe by 'action'
    seen_actions = set()
    sorted_remedies: List[Dict[str, Any]] = []
    for r in sorted(remedies, key=lambda x: x["priority"]):
        if r["action"] in seen_actions:
            continue
        seen_actions.add(r["action"])
        sorted_remedies.append(r)

    # Apply severity-budget cap (Avoid=5, Adjustment=3, Acceptable=2, Ideal=1)
    budget = REMEDY_BUDGET.get(verdict, 3)
    sorted_remedies = sorted_remedies[:budget]

    # ── Dedupe classical refs ──
    seen_refs = set()
    deduped_refs: List[Dict[str, str]] = []
    for ref in refs:
        key = (ref.get("type", ""), ref.get("source", ""))
        if key in seen_refs or not key[1]:
            continue
        seen_refs.add(key)
        deduped_refs.append(ref)

    return {
        "verdict":          verdict,
        "verdict_label":    VERDICT_LABEL.get(verdict, {"en": verdict, "hi": verdict}),
        "verdict_tone":     VERDICT_TONE.get(verdict, "ok"),
        "generic_verdict":  generic_verdict,
        "severity": {
            "bucket":     sev_bucket,
            "label":      SEVERITY_LABEL[sev_bucket],
            "multiplier": round(float(multiplier), 2),
            "reasons":    sev_reasons,
        },
        "personalization_reason": {"en": pers_reason_en, "hi": pers_reason_hi},
        "remedies":               sorted_remedies,
        "classical_refs":         deduped_refs,
        "applied_tie_breakers":   applied,
        "meta": {
            "engine":        ENGINE_NAME,
            "version":       ENGINE_VERSION,
            "branding":      BRANDING_LINE,
            "room_type":     room_type,
            "direction":     direction,
            "lagna":         kundli_context.get("lagna"),
            "rashi":         kundli_context.get("rashi"),
            "mahadasha":     kundli_context.get("current_mahadasha"),
            "sade_sati":     bool(kundli_context.get("sade_sati", {}).get("active")),
            "ishta_devata":  kundli_context.get("ishta_devata"),
        },
    }
