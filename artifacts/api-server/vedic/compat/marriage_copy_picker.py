"""
Deterministic human-voice copy for marriage_basics Basic UI (no LLM).

Engine computes chart facts → tags + slots → template pool pick (stable per chart).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_TEMPLATES: dict[str, list[str]] | None = None

BAND_LABEL = {
    "Strong": "Good foundation",
    "Moderate": "Mixed signals",
    "Strained": "Needs extra care",
}

_POSITIVE_PRIORITY = (
    "h7_benefic_only",
    "lord_strong",
    "h7_empty_strong_lord",
    "karaka_strong_male",
    "karaka_strong_female",
    "kp_strong",
    "upapada_stable",
    "manglik_reduced",
    "d9_supportive",
    "positive_generic",
)

_WATCHOUT_PRIORITY = (
    "lord_weak",
    "h7_malefic_only",
    "lord_combust",
    "lord_retrograde",
    "manglik_active",
    "watchout_separation",
    "watchout_saturn_7",
    "kp_weak",
    "upapada_strained",
    "d9_weak",
    "h7_empty_weak_lord",
    "h7_mixed",
    "watchout_generic",
)


class _SafeFormat(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _load_templates() -> dict[str, list[str]]:
    global _TEMPLATES
    if _TEMPLATES is None:
        path = Path(__file__).with_name("marriage_copy_templates.json")
        with open(path, encoding="utf-8") as fh:
            _TEMPLATES = json.load(fh)
    return _TEMPLATES


def partner_copy_seed(kundli: dict, name: str) -> str:
    """Stable seed from birth chart — same chart always picks same template variants."""
    parts = [
        name.strip().lower(),
        str(kundli.get("ascendant") or ""),
        str(kundli.get("moonSign") or ""),
        str(kundli.get("nakshatra") or ""),
    ]
    for p in sorted(kundli.get("planets") or [], key=lambda x: str(x.get("name") or "")):
        parts.append(
            f"{p.get('name')}:{p.get('sign')}:{p.get('house')}:{p.get('longitude', '')}"
        )
    return "|".join(parts)


def _pick(category: str, seed: str, slots: dict[str, str]) -> str:
    templates = _load_templates()
    variants = templates.get(category)
    if not variants:
        variants = templates.get("positive_generic") or ["Chart note."]
    digest = hashlib.sha256(f"{seed}|{category}".encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(variants)
    text = variants[idx]
    try:
        return str(text).format_map(_SafeFormat(slots))
    except (ValueError, KeyError):
        return str(text)


def extract_copy_tags(partner: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    band = str(partner.get("readiness_band") or "Moderate")
    tags.append(f"band_{band.lower()}")

    d1 = partner.get("d1") or {}
    soft = len(d1.get("benefics_in_seventh") or [])
    hard = len(d1.get("malefics_in_seventh") or [])
    occ = len(d1.get("planets_in_seventh") or [])
    lord_str = str(d1.get("seventh_lord_strength") or "")

    if occ == 0:
        if lord_str == "strong":
            tags.append("h7_empty_strong_lord")
        elif lord_str == "weak":
            tags.append("h7_empty_weak_lord")
    elif soft > 0 and hard == 0:
        tags.append("h7_benefic_only")
    elif hard > 0 and soft == 0:
        tags.append("h7_malefic_only")
    elif soft > 0 and hard > 0:
        tags.append("h7_mixed")

    if lord_str == "strong":
        tags.append("lord_strong")
    elif lord_str == "weak":
        tags.append("lord_weak")
    else:
        tags.append("lord_average")

    if d1.get("seventh_lord_combust"):
        tags.append("lord_combust")
    if d1.get("seventh_lord_retrograde"):
        tags.append("lord_retrograde")

    d9 = partner.get("d9") or {}
    if d9.get("available"):
        band_d9 = str(d9.get("band") or "Mixed")
        tags.append(
            {"Supportive": "d9_supportive", "Mixed": "d9_mixed", "Weak": "d9_weak"}.get(
                band_d9, "d9_mixed"
            )
        )

    manglik = partner.get("manglik") or {}
    eff = str(manglik.get("effective") or "")
    if manglik.get("has_dosh"):
        if eff in ("reduced", "cancelled"):
            tags.append("manglik_reduced")
        elif eff == "active":
            tags.append("manglik_active")

    gender = str(partner.get("gender") or "unknown")
    karaka = partner.get("karaka") or {}
    k_str = str(karaka.get("strength") or "")
    if gender == "male":
        if k_str == "strong":
            tags.append("karaka_strong_male")
        elif k_str == "weak":
            tags.append("karaka_weak_male")
    elif gender == "female":
        if k_str == "strong":
            tags.append("karaka_strong_female")
        elif k_str == "weak":
            tags.append("karaka_weak_female")

    kp = partner.get("kp") or {}
    kv = str(kp.get("verdict") or "")
    if kv == "STRONG":
        tags.append("kp_strong")
    elif kv == "WEAK":
        tags.append("kp_weak")

    ul = partner.get("upapada") or {}
    stab = str(ul.get("stability") or "")
    if stab == "stable":
        tags.append("upapada_stable")
    elif stab == "strained":
        tags.append("upapada_strained")

    sig = partner.get("relationship_signals") or {}
    if sig.get("separation_yoga"):
        tags.append("watchout_separation")
    if sig.get("saturn_on_7th"):
        tags.append("watchout_saturn_7")

    dasha = partner.get("dasha_timeline") or {}
    if dasha.get("available"):
        if dasha.get("stress_windows"):
            tags.append("dasha_stress")
        elif dasha.get("reconnection_windows"):
            tags.append("dasha_repair")
        else:
            tags.append("dasha_neutral")
    else:
        tags.append("dasha_neutral")

    dk = partner.get("darakaraka") or {}
    if dk.get("planet"):
        tags.append("dk_spouse")

    return tags


def extract_copy_slots(partner: dict[str, Any]) -> dict[str, str]:
    d1 = partner.get("d1") or {}
    d9 = partner.get("d9") or {}
    dk = partner.get("darakaraka") or {}
    karaka = partner.get("karaka") or {}
    dasha = partner.get("dasha_timeline") or {}
    cur = dasha.get("current") or {}

    benefics = d1.get("benefics_in_seventh") or []
    malefics = d1.get("malefics_in_seventh") or []

    return {
        "name": str(partner.get("name") or "You"),
        "seventh_lord": str(d1.get("seventh_lord") or "—"),
        "seventh_lord_house": str(d1.get("seventh_lord_house") or "—"),
        "seventh_lord_sign": str(d1.get("seventh_lord_sign") or "—"),
        "benefics_in_7": ", ".join(benefics) if benefics else "—",
        "malefics_in_7": ", ".join(malefics) if malefics else "—",
        "dk_planet": str(dk.get("planet") or "—"),
        "dk_house": str(dk.get("house") or "—"),
        "karaka": str(karaka.get("primary") or "—"),
        "karaka_sign": str(karaka.get("sign") or "—"),
        "karaka_house": str(karaka.get("house") or "—"),
        "d9_band": str(d9.get("band") or "—"),
        "maha": str(cur.get("maha") or "—"),
        "antar": str(cur.get("antar") or "—"),
        "dasha_range": str(cur.get("note") or "")[:80],
    }


def _friction_category(partner: dict[str, Any]) -> str:
    blob = " ".join(
        [
            str(partner.get("friction") or ""),
            " ".join(partner.get("pressures") or []),
            " ".join(partner.get("strengths") or []),
        ]
    ).lower()
    if "saturn" in blob or "distance" in blob or "delay" in blob:
        return "friction_saturn"
    if "mars" in blob or "manglik" in blob or "fight" in blob or "anger" in blob:
        return "friction_mars"
    if "rahu" in blob or "ketu" in blob or "confusion" in blob:
        return "friction_rahu"
    if "venus" in blob and str(partner.get("gender")) == "male":
        return "friction_venus"
    if "jupiter" in blob and str(partner.get("gender")) == "female":
        return "friction_jupiter"
    return "friction_generic"


def _remedy_category(partner: dict[str, Any]) -> str:
    blob = " ".join(
        [
            str(partner.get("remedy") or ""),
            str(partner.get("friction") or ""),
            " ".join(partner.get("pressures") or []),
        ]
    ).lower()
    if "saturn" in blob or "saturday" in blob or "sesame" in blob:
        return "remedy_saturn"
    if "mars" in blob or "tuesday" in blob or "hanuman" in blob:
        return "remedy_mars"
    if "rahu" in blob or ("thursday" in blob and "vishnu" in blob):
        return "remedy_rahu"
    if "venus" in blob or "friday" in blob:
        return "remedy_venus"
    if "jupiter" in blob or "thursday" in blob:
        return "remedy_jupiter"
    return "remedy_generic"


def _collect_from_tags(
    tag_set: set[str],
    priority: tuple[str, ...],
    seed: str,
    slots: dict[str, str],
    *,
    suffix: str,
    limit: int,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for cat in priority:
        if cat not in tag_set:
            continue
        line = _pick(cat, f"{seed}:{suffix}:{cat}", slots).strip()
        if not line or line in seen:
            continue
        seen.add(line)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def build_partner_plain_copy(partner: dict[str, Any], seed: str) -> dict[str, Any]:
    """Build human-voice plain_copy block for one partner (Basic = compact Pro funnel)."""
    tags = extract_copy_tags(partner)
    tag_set = set(tags)
    slots = extract_copy_slots(partner)
    band = str(partner.get("readiness_band") or "Moderate")

    critical = partner.get("critical_alerts") or {}
    alert_count = int(critical.get("count") or 0)
    slots["alert_count"] = str(alert_count)
    slots["hidden_count"] = str(max(alert_count, 2))

    headline = _pick(f"band_{band.lower()}", f"{seed}:headline", slots)

    positives = _collect_from_tags(
        tag_set, _POSITIVE_PRIORITY, seed, slots, suffix="pos", limit=1
    )
    if not positives:
        positives = [_pick("positive_generic", f"{seed}:pos:fallback", slots)]

    watchouts = _collect_from_tags(
        tag_set, _WATCHOUT_PRIORITY, seed, slots, suffix="watch", limit=1
    )
    if not watchouts:
        watchouts = [_pick("watchout_generic", f"{seed}:watch:fallback", slots)]

    if critical.get("locked") and critical.get("teaser"):
        pro_lock_teaser = f"{critical['teaser']} — full detail in Pro."
    else:
        pro_lock_teaser = _pick("pro_lock_teaser", f"{seed}:lock", slots)

    remedy_teaser = _pick("remedy_teaser", f"{seed}:remedy_teaser", slots)
    pro_strip = _pick("pro_strip_partner", f"{seed}:strip", slots)

    # Full friction/remedy kept for Pro PDF — not shown on Basic card.
    friction = _pick(_friction_category(partner), f"{seed}:friction", slots)
    remedy = _pick(_remedy_category(partner), f"{seed}:remedy", slots)

    return {
        "band_label": BAND_LABEL.get(band, band),
        "headline": headline,
        "positives": positives,
        "watchouts": watchouts,
        "pro_lock_teaser": pro_lock_teaser,
        "remedy_teaser": remedy_teaser,
        "pro_strip": pro_strip,
        "friction": friction,
        "remedy": remedy,
        "copy_tags": tags,
    }


_COUPLE_GAP_MAP = {
    "Promising": "couple_gap_promising",
    "Workable": "couple_gap_workable",
    "High Effort": "couple_gap_high_effort",
}


def couple_copy_seed(
    kundli_p1: dict,
    kundli_p2: dict,
    p1_name: str,
    p2_name: str,
) -> str:
    return "||".join(
        [
            partner_copy_seed(kundli_p1, p1_name),
            partner_copy_seed(kundli_p2, p2_name),
        ]
    )


def _build_couple_locked_highlights(
    couple: dict[str, Any],
    p1: dict[str, Any],
    p2: dict[str, Any],
) -> list[str]:
    """Pro PDF hooks — marriage structure engine only (no Gun Milan)."""
    items: list[str] = []
    alert_count = int(couple.get("critical_alerts_total") or 0)
    if alert_count > 0:
        items.append(f"{alert_count} hidden alert(s) across both charts")

    syn = couple.get("synastry") or {}
    if syn.get("available"):
        items.append("Cross-chart 7th lord synastry — how you affect each other")

    manglik = couple.get("manglik") or {}
    if manglik.get("p1_has_dosh") or manglik.get("p2_has_dosh"):
        items.append("Manglik balance & cancellation for both charts")

    gm = couple.get("graha_maitri") or {}
    if gm.get("available") and str(gm.get("relation") or "") not in ("", "neutral"):
        items.append("Moon mood match (Graha Maitri) — daily harmony read")

    kp = couple.get("kp_couple") or {}
    if kp.get("available"):
        items.append("KP couple marriage promise — commitment depth")

    d9 = couple.get("d9_sync") or {}
    if d9.get("available"):
        items.append("D9 couple sync — long-term married life tone together")

    items.append("Marriage dasha windows — best & risky timing (both partners)")
    items.append("Full remedy chain + downloadable PDF")

    # Dedupe while preserving order; cap at 4 for Basic end card.
    seen: set[str] = set()
    out: list[str] = []
    for line in items:
        if line in seen:
            continue
        seen.add(line)
        out.append(line)
        if len(out) >= 4:
            break
    return out


def build_couple_plain_copy(
    couple: dict[str, Any],
    p1: dict[str, Any],
    p2: dict[str, Any],
    seed: str,
) -> dict[str, Any]:
    """Couple-level Pro gap copy — shown after both partner cards."""
    band = str(couple.get("structural_band") or "Workable")
    alert_count = int(couple.get("critical_alerts_total") or 0)
    slots = {
        "p1_name": str(p1.get("name") or "Partner A"),
        "p2_name": str(p2.get("name") or "Partner B"),
        "couple_score": str(couple.get("structural_score") or "—"),
        "couple_band": band,
        "alert_count": str(alert_count),
    }
    gap_cat = _COUPLE_GAP_MAP.get(band, "couple_gap_workable")
    gap_teaser = _pick(gap_cat, f"{seed}:gap", slots)
    if alert_count > 0:
        gap_teaser = _pick("couple_gap_alerts", f"{seed}:gap:alerts", slots)

    return {
        "gap_teaser": gap_teaser,
        "pro_cta_line": _pick("couple_pro_cta", f"{seed}:cta", slots),
        "alert_count": alert_count,
        "locked_highlights": _build_couple_locked_highlights(couple, p1, p2),
    }


def count_templates() -> int:
    """Total template strings in pool (for diagnostics)."""
    return sum(len(v) for v in _load_templates().values())
