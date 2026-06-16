"""
Deterministic human-voice copy for marriage_basics Basic UI (no LLM).

Engine computes chart facts → tags + slots → template pool pick (stable per chart).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_TEMPLATES_BY_LANG: dict[str, dict[str, list[str]]] = {}

BAND_LABEL_EN = {
    "Strong": "Good foundation",
    "Moderate": "Mixed signals",
    "Strained": "Needs extra care",
}

BAND_LABEL_HN = {
    "Strong": "Achha base",
    "Moderate": "Mixed signals",
    "Strained": "Extra care chahiye",
}

BAND_LABEL_HI = {
    "Strong": "अच्छी नींव",
    "Moderate": "मिला-जुला संकेत",
    "Strained": "अतिरिक्त ध्यान चाहिए",
}

COUPLE_BAND_LABEL_EN = {
    "Promising": "Promising",
    "Workable": "Workable",
    "High Effort": "High Effort",
}

COUPLE_BAND_LABEL_HN = {
    "Promising": "Promising",
    "Workable": "Workable",
    "High Effort": "High Effort",
}

COUPLE_BAND_LABEL_HI = {
    "Promising": "आशाजनक",
    "Workable": "काम चलने योग्य",
    "High Effort": "उच्च प्रयास",
}

_COUPLE_VERDICT = {
    "en": {
        "Promising": (
            "Both marriage axes show supportive structure — if these two marry, "
            "long-term direction can grow well with steady effort."
        ),
        "Workable": (
            "Marriage is workable but not effortless — strengths exist on both sides; "
            "friction points need conscious handling after wedding."
        ),
        "High Effort": (
            "High effort match — marriage is possible but demands patience, remedies, "
            "and realistic expectations on both charts."
        ),
    },
    "hn": {
        "Promising": (
            "Dono marriage axes supportive structure dikhate hain — shaadi ke baad "
            "steady effort se long-term direction achhi ho sakti hai."
        ),
        "Workable": (
            "Shaadi workable hai par effortless nahi — dono taraf strengths hain; "
            "friction points ko shaadi ke baad consciously handle karna hoga."
        ),
        "High Effort": (
            "High effort match — shaadi possible hai par patience, upay aur realistic "
            "expectations dono charts par chahiye."
        ),
    },
    "hi": {
        "Promising": (
            "दोनों विवाह अक्ष सहायक संरचना दिखाते हैं — यदि ये दो विवाह करें, "
            "तो निरंतर प्रयास से दीर्घकालिक दिशा अच्छी बढ़ सकती है।"
        ),
        "Workable": (
            "विवाह संभव है पर सहज नहीं — दोनों ओर शक्तियाँ हैं; "
            "घर्षण बिंदुओं को विवाह के बाद सचेत रूप से संभालना होगा।"
        ),
        "High Effort": (
            "उच्च प्रयास मिलान — विवाह संभव है पर धैर्य, उपाय और दोनों चार्ट पर "
            "यथार्थवादी अपेक्षाएँ ज़रूरी हैं।"
        ),
    },
}

_PRO_DETAIL_SUFFIX = {
    "en": "full detail in Pro.",
    "hn": "poora detail Pro mein.",
    "hi": "पूर्ण विवरण प्रो में।",
}


def normalize_marriage_lang(lang: str | None) -> str:
    """Map UI / API lang codes to marriage copy pool: en | hn | hi."""
    c = (lang or "hn").strip().lower()
    if c in ("en", "english"):
        return "en"
    if c in ("hi", "hindi"):
        return "hi"
    if c in ("hn", "hinglish"):
        return "hn"
    return "en"

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


def _template_filename(lang: str | None) -> str:
    return "marriage_copy_templates.json"


def _load_templates(lang: str | None = None) -> dict[str, list[str]]:
    key = normalize_marriage_lang(lang)
    if key not in _TEMPLATES_BY_LANG:
        if key == "en":
            from vedic.compat.marriage_copy_templates_en_data import TEMPLATES_EN

            _TEMPLATES_BY_LANG[key] = TEMPLATES_EN
        elif key == "hi":
            from vedic.compat.marriage_copy_templates_hi_data import TEMPLATES_HI

            _TEMPLATES_BY_LANG[key] = TEMPLATES_HI
        else:
            path = Path(__file__).with_name(_template_filename(lang))
            with open(path, encoding="utf-8") as fh:
                _TEMPLATES_BY_LANG[key] = json.load(fh)
    return _TEMPLATES_BY_LANG[key]


def _band_labels(lang: str | None) -> dict[str, str]:
    key = normalize_marriage_lang(lang)
    if key == "en":
        return BAND_LABEL_EN
    if key == "hi":
        return BAND_LABEL_HI
    return BAND_LABEL_HN


def couple_band_label(band: str, lang: str | None = None) -> str:
    key = normalize_marriage_lang(lang)
    maps = {
        "en": COUPLE_BAND_LABEL_EN,
        "hi": COUPLE_BAND_LABEL_HI,
        "hn": COUPLE_BAND_LABEL_HN,
    }
    return maps.get(key, COUPLE_BAND_LABEL_EN).get(band, band)


def couple_verdict_text(band: str, lang: str | None = None) -> str:
    key = normalize_marriage_lang(lang)
    pool = _COUPLE_VERDICT.get(key) or _COUPLE_VERDICT["en"]
    return pool.get(band, pool.get("Workable", ""))


def pro_detail_suffix(lang: str | None = None) -> str:
    key = normalize_marriage_lang(lang)
    return _PRO_DETAIL_SUFFIX.get(key, _PRO_DETAIL_SUFFIX["en"])


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


def _pick(
    category: str,
    seed: str,
    slots: dict[str, str],
    *,
    lang: str | None = None,
) -> str:
    templates = _load_templates(lang)
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
    lang: str | None = None,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for cat in priority:
        if cat not in tag_set:
            continue
        line = _pick(cat, f"{seed}:{suffix}:{cat}", slots, lang=lang).strip()
        if not line or line in seen:
            continue
        seen.add(line)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def build_partner_plain_copy(
    partner: dict[str, Any],
    seed: str,
    *,
    lang: str | None = None,
) -> dict[str, Any]:
    """Build human-voice plain_copy block for one partner (Basic = compact Pro funnel)."""
    tags = extract_copy_tags(partner)
    tag_set = set(tags)
    slots = extract_copy_slots(partner)
    band = str(partner.get("readiness_band") or "Moderate")
    labels = _band_labels(lang)

    critical = partner.get("critical_alerts") or {}
    alert_count = int(critical.get("count") or 0)
    slots["alert_count"] = str(alert_count)
    slots["hidden_count"] = str(max(alert_count, 2))

    headline = _pick(f"band_{band.lower()}", f"{seed}:headline", slots, lang=lang)

    positives = _collect_from_tags(
        tag_set, _POSITIVE_PRIORITY, seed, slots, suffix="pos", limit=1, lang=lang
    )
    if not positives:
        positives = [_pick("positive_generic", f"{seed}:pos:fallback", slots, lang=lang)]

    watchouts = _collect_from_tags(
        tag_set, _WATCHOUT_PRIORITY, seed, slots, suffix="watch", limit=1, lang=lang
    )
    if not watchouts:
        watchouts = [_pick("watchout_generic", f"{seed}:watch:fallback", slots, lang=lang)]

    if critical.get("locked") and critical.get("teaser"):
        pro_lock_teaser = f"{critical['teaser']} — {pro_detail_suffix(lang)}"
    else:
        pro_lock_teaser = _pick("pro_lock_teaser", f"{seed}:lock", slots, lang=lang)

    remedy_teaser = _pick("remedy_teaser", f"{seed}:remedy_teaser", slots, lang=lang)
    pro_strip = _pick("pro_strip_partner", f"{seed}:strip", slots, lang=lang)

    # Full friction/remedy kept for Pro PDF — not shown on Basic card.
    friction = _pick(_friction_category(partner), f"{seed}:friction", slots, lang=lang)
    remedy = _pick(_remedy_category(partner), f"{seed}:remedy", slots, lang=lang)

    return {
        "band_label": labels.get(band, band),
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
    *,
    lang: str | None = None,
) -> list[str]:
    """Pro PDF hooks — marriage structure engine only (no Gun Milan)."""
    key = normalize_marriage_lang(lang)
    if key == "hi":
        _t = {
            "alerts": lambda n: f"दोनों चार्ट में {n} छिपे अलर्ट",
            "synastry": "क्रॉस-चार्ट सप्तम स्वामी सिनैस्ट्री — आप एक-दूसरे को कैसे प्रभावित करते हैं",
            "manglik": "दोनों चार्ट के लिए मांगलिक संतुलन और निवारण",
            "graha_maitri": "चंद्र मन मेल (ग्रह मैत्री) — रोज़ का सामंजस्य",
            "kp": "KP कपल विवाह वादा — प्रतिबद्धता की गहराई",
            "d9": "नवांश कपल सिंक — साथ में दीर्घकालिक विवाहित जीवन का स्वर",
            "dasha": "विवाह दशा विंडो — सर्वोत्तम और जोखिम भरा समय (दोनों साथी)",
            "pdf": "पूर्ण उपाय श्रृंखला + डाउनलोड योग्य PDF",
        }
    elif key == "hn":
        _t = {
            "alerts": lambda n: f"Dono charts mein {n} hidden alert(s)",
            "synastry": "Cross-chart 7th lord synastry — aap ek doosre ko kaise affect karte hain",
            "manglik": "Dono charts ke liye Manglik balance aur cancellation",
            "graha_maitri": "Moon mood match (Graha Maitri) — daily harmony read",
            "kp": "KP couple marriage promise — commitment depth",
            "d9": "D9 couple sync — long-term married life tone together",
            "dasha": "Marriage dasha windows — best aur risky timing (dono partners)",
            "pdf": "Poori remedy chain + downloadable PDF",
        }
    else:
        _t = {
            "alerts": lambda n: f"{n} hidden alert(s) across both charts",
            "synastry": "Cross-chart 7th lord synastry — how you affect each other",
            "manglik": "Manglik balance & cancellation for both charts",
            "graha_maitri": "Moon mood match (Graha Maitri) — daily harmony read",
            "kp": "KP couple marriage promise — commitment depth",
            "d9": "D9 couple sync — long-term married life tone together",
            "dasha": "Marriage dasha windows — best & risky timing (both partners)",
            "pdf": "Full remedy chain + downloadable PDF",
        }

    items: list[str] = []
    alert_count = int(couple.get("critical_alerts_total") or 0)
    if alert_count > 0:
        items.append(_t["alerts"](alert_count))

    syn = couple.get("synastry") or {}
    if syn.get("available"):
        items.append(_t["synastry"])

    manglik = couple.get("manglik") or {}
    if manglik.get("p1_has_dosh") or manglik.get("p2_has_dosh"):
        items.append(_t["manglik"])

    gm = couple.get("graha_maitri") or {}
    if gm.get("available") and str(gm.get("relation") or "") not in ("", "neutral"):
        items.append(_t["graha_maitri"])

    kp = couple.get("kp_couple") or {}
    if kp.get("available"):
        items.append(_t["kp"])

    d9 = couple.get("d9_sync") or {}
    if d9.get("available"):
        items.append(_t["d9"])

    items.append(_t["dasha"])
    items.append(_t["pdf"])

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
    *,
    lang: str | None = None,
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
    gap_teaser = _pick(gap_cat, f"{seed}:gap", slots, lang=lang)
    if alert_count > 0:
        gap_teaser = _pick("couple_gap_alerts", f"{seed}:gap:alerts", slots, lang=lang)

    return {
        "gap_teaser": gap_teaser,
        "pro_cta_line": _pick("couple_pro_cta", f"{seed}:cta", slots, lang=lang),
        "alert_count": alert_count,
        "locked_highlights": _build_couple_locked_highlights(couple, p1, p2, lang=lang),
    }


def count_templates(lang: str | None = None) -> int:
    """Total template strings in pool (for diagnostics)."""
    return sum(len(v) for v in _load_templates(lang).values())
