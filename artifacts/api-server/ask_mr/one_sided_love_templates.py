"""One-sided love engine — intent templates."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

OSLOVE_LEVELS: tuple[str, ...] = ("reciprocal", "unclear", "one_sided", "unlikely")

VERDICT_LABELS: dict[str, str] = {
    "reciprocal": "Reciprocal",
    "unclear": "Unclear",
    "one_sided": "One-sided",
    "unlikely": "Unlikely",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "reciprocal": 78,
    "unclear": 62,
    "one_sided": 46,
    "unlikely": 28,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["outlook"] = "Reciprocity outlook —"

_BASE_OPENINGS: dict[str, str] = {
    "reciprocal": "Chart ke hisaab se reciprocity / mutual pull mostly reciprocal range me dikhti hai — dono taraf effort se bond grow ho jayega.",
    "unclear": "Reciprocity signals unclear / mixed dikhte hain — abhi barabar depth confirm nahi hoti.",
    "one_sided": "One-sided pull pattern active dikhta hai — aapka effort abhi unke effort se zyada ho jayega.",
    "unlikely": "Reciprocity unlikely range me dikhti hai — mutual balance abhi weak dikhta hai, realism helpful rahega.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_one_sided": _BASE_OPENINGS,
    "reciprocity": {
        "reciprocal": "Reciprocity mostly reciprocal range me dikhti hai — wo bhi feelings invest kar sakta hai.",
        "unclear": "Reciprocity unclear zone me hai — wo bhi care karta hai par depth abhi barabar nahi.",
        "one_sided": "Reciprocity one-sided zone me dikhti hai — wo abhi utna barabar return nahi dikhata.",
        "unlikely": "Reciprocity unlikely range me dikhti hai — mutual balance abhi weak hai.",
    },
    "partner_loves_back": {
        "reciprocal": "Partner ke feelings mostly reciprocal range me dikhte hain — pyar return hone ki room hai.",
        "unclear": "Partner ke feelings mixed / unclear hain — interest hai par depth confirm nahi.",
        "one_sided": "Partner ke feelings one-sided zone me dikhte hain — aap zyada invest kar rahe ho.",
        "unlikely": "Partner ke feelings unlikely-reciprocal range me dikhte hain — realism self-worth protect karega.",
    },
    "crush": {
        "reciprocal": "Crush reciprocity relatively positive range me dikhti hai — notice + response possible hai.",
        "unclear": "Crush signals mixed hain — interest possible hai par confirm nahi.",
        "one_sided": "Crush one-sided zone me dikhta hai — aapka pull zyada active hai.",
        "unlikely": "Crush reciprocity unlikely range me dikhti hai — response weak reh jayega.",
    },
    "proposal": {
        "reciprocal": "Proposal / propose timing relatively supportive dikhti hai — positive response possible hai.",
        "unclear": "Proposal outcome unclear / mixed dikhta hai — timing + rapport dono matter karenge.",
        "one_sided": "Proposal one-sided risk zone me dikhta hai — pehle reciprocity signs check karein.",
        "unlikely": "Proposal unlikely-positive range me dikhta hai — rush propose risky reh jayega.",
    },
    "ek_tarfa": {
        "reciprocal": "Ek tarfa pattern dominant nahi — mutual pull grow karne ki room hai.",
        "unclear": "Ek tarfa vs mutual abhi unclear hai — behaviour pattern observe karein.",
        "one_sided": "Ek tarfa pyar pattern active dikhta hai — balance abhi one-sided zone me hai.",
        "unlikely": "Ek tarfa pull unlikely-to-balance range me dikhta hai — self-worth priority rakhein.",
    },
    "unrequited": {
        "reciprocal": "Unrequited theme dominant nahi — reciprocity relatively better range me dikhti hai.",
        "unclear": "Unrequited vs mixed signals unclear hain — direct check helpful rehta hai.",
        "one_sided": "Unrequited / one-sided pull active dikhta hai — return feelings weak hain.",
        "unlikely": "Unrequited pattern unlikely-to-convert range me dikhta hai — peace + boundaries zaruri hain.",
    },
    "effort_imbalance": {
        "reciprocal": "Effort imbalance dominant nahi — mutual investment relatively balanced dikhti hai.",
        "unclear": "Effort imbalance mixed signals deta hai — kabhi equal kabhi uneven.",
        "one_sided": "Effort imbalance one-sided zone me active hai — aap zyada initiate karte ho.",
        "unlikely": "Effort imbalance unlikely-to-equalize range me dikhta hai — over-invest avoid karein.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_one_sided": {
        "reciprocal": "Reciprocal matlab mutual effort se bond deepen ho jayega.",
        "unclear": "Unclear matlab abhi confirm karna jaldi hai — actions observe karein.",
        "one_sided": "One-sided matlab emotional balance abhi tilted hai — self-respect maintain karein.",
        "unlikely": "Unlikely matlab realism + boundaries peace protect karte hain.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_one_sided": {
        "reciprocal": "Mutual gestures + steady contact reciprocity strengthen karte hain.",
        "unclear": "Direct but calm baat helpful rehti hai — assumptions avoid karein.",
        "one_sided": "Over-texting / over-invest kam karein — equal effort observe karein.",
        "unlikely": "Self-worth priority rakhein — one-sided loop me repeat invest avoid karein.",
    },
    "crush": {
        "unclear": "Crush par mixed signals ko time dein — friendly consistency helpful rehti hai.",
        "one_sided": "Crush par fantasy se zyada real response track karein.",
    },
    "reciprocity": {
        "one_sided": "Wo initiate karta hai ya nahi — behaviour pattern facts se check karein.",
    },
    "partner_loves_back": {
        "unclear": "Words se zyada consistent actions matter karte hain — observe karein.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "reciprocal": "Reciprocity outlook positive hai — mutual effort se feelings deepen ho jayengi.",
    "unclear": "Unclear outlook clear hoga jab direct talk ya consistent actions dikhen.",
    "one_sided": "One-sided outlook improve tabhi jab partner effort equalize kare — wait-only approach risky rehta hai.",
    "unlikely": "Unlikely outlook me self-protection first — change possible hai par over-invest avoid karein.",
}

OSLOVE_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"5th\s*lord\s*strong|emotional\s+reopening", re.I), "5th lord strength reciprocity / romantic reopening support karta hai."),
    (re.compile(r"5th\s*lord\s*weak|fifth\s*lord\s*weak", re.I), "Weak 5th lord one-sided romantic pull la sakta hai."),
    (re.compile(r"venus.*afflict|venus_afflict|venus.*dusthana", re.I), "Afflicted Venus se affection return kam / uneven dikhti hai."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional investment imbalance amplify kar sakta hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th slow / reserved reciprocity tone la sakta hai."),
    (re.compile(r"separation_yoga|third_person", re.I), "Separation / third-person pull reciprocity ko weaken kar sakta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase reciprocity signals ko colour karti hai."),
]


def detect_one_sided_love_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_one_sided_love_angle

    q = (question or "").strip()
    angle = infer_one_sided_love_angle(q) or "general_one_sided"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("one_sided", "one_sided_love", "commitment") and angle == "general_one_sided":
        if re.search(r"(?ix)\b(crush)\b", q):
            angle = "crush"
        elif re.search(r"(?ix)\b(reciproc|mutual|wo\s+bhi)\b", q):
            angle = "reciprocity"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "unclear").strip().lower()
    ang = (angle or "general_one_sided").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_one_sided"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["unclear"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "unclear").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_one_sided").strip().lower()) or MEANING_TEMPLATES["general_one_sided"]
    return block.get(lv) or MEANING_TEMPLATES["general_one_sided"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "unclear").strip().lower()
    ang = (angle or "general_one_sided").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_one_sided"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_one_sided"].get(
        lv, "Reciprocity samajhne ke liye actions + consistent effort observe karna helpful rehta hai."
    )


def get_oslove_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "unclear").strip().lower()) or OUTLOOK_TEMPLATES["unclear"]


def oslove_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in OSLOVE_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me reciprocity-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = oslove_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
