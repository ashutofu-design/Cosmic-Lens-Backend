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
    """Build human-voice plain_copy block for one partner."""
    tags = extract_copy_tags(partner)
    tag_set = set(tags)
    slots = extract_copy_slots(partner)
    band = str(partner.get("readiness_band") or "Moderate")

    headline = _pick(f"band_{band.lower()}", f"{seed}:headline", slots)

    positives = _collect_from_tags(
        tag_set, _POSITIVE_PRIORITY, seed, slots, suffix="pos", limit=3
    )
    if not positives:
        positives = [_pick("positive_generic", f"{seed}:pos:fallback", slots)]

    watchouts = _collect_from_tags(
        tag_set, _WATCHOUT_PRIORITY, seed, slots, suffix="watch", limit=3
    )
    if not watchouts:
        watchouts = [_pick("watchout_generic", f"{seed}:watch:fallback", slots)]

    spouse_line = (
        _pick("dk_spouse", f"{seed}:spouse", slots) if "dk_spouse" in tag_set else None
    )

    long_term_line = None
    for d9_cat in ("d9_supportive", "d9_mixed", "d9_weak"):
        if d9_cat in tag_set:
            long_term_line = _pick(d9_cat, f"{seed}:longterm", slots)
            break

    manglik_line = None
    if "manglik_active" in tag_set:
        manglik_line = _pick("manglik_active", f"{seed}:manglik", slots)
    elif "manglik_reduced" in tag_set:
        manglik_line = _pick("manglik_reduced", f"{seed}:manglik", slots)

    timing_line = None
    for dash_cat in ("dasha_stress", "dasha_repair", "dasha_neutral"):
        if dash_cat in tag_set:
            timing_line = _pick(dash_cat, f"{seed}:timing", slots)
            break

    friction = _pick(_friction_category(partner), f"{seed}:friction", slots)
    remedy = _pick(_remedy_category(partner), f"{seed}:remedy", slots)

    return {
        "band_label": BAND_LABEL.get(band, band),
        "headline": headline,
        "positives": positives,
        "watchouts": watchouts,
        "spouse_line": spouse_line,
        "long_term_line": long_term_line,
        "manglik_line": manglik_line,
        "timing_line": timing_line,
        "friction": friction,
        "remedy": remedy,
        "copy_tags": tags,
    }


def count_templates() -> int:
    """Total template strings in pool (for diagnostics)."""
    return sum(len(v) for v in _load_templates().values())
