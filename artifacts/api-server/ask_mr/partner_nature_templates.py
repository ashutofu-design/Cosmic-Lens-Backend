"""Partner nature engine — intent templates."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

NATURE_LEVELS: tuple[str, ...] = ("balanced", "mixed", "complex", "challenging")

VERDICT_LABELS: dict[str, str] = {
    "balanced": "Balanced",
    "mixed": "Mixed",
    "complex": "Complex",
    "challenging": "Challenging",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "balanced": 78,
    "mixed": 62,
    "complex": 48,
    "challenging": 32,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["outlook"] = "Partner nature outlook —"

_BASE_OPENINGS: dict[str, str] = {
    "balanced": "Chart ke hisaab se partner ka nature mostly balanced dikhta hai — steady temperament ke saath grow karne ki room hai.",
    "mixed": "Partner ke nature me mixed traits dikhte hain — strengths aur friction dono present hain.",
    "complex": "Partner ka nature complex pattern dikhata hai — strong pulls clear boundaries maangte hain.",
    "challenging": "Partner ke nature me challenging patterns active hain — realism + respect dono zaruri hain.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_nature": _BASE_OPENINGS,
    "personality_traits": _BASE_OPENINGS,
    "temper_anger": {
        "balanced": "Partner ka temper mostly balanced dikhta hai — gussa short-lived reh sakta hai.",
        "mixed": "Partner ke temper me mixed pattern hai — jaldi react karta hai par calm baat se settle ho jata hai.",
        "complex": "Partner ke gusse ka pattern complex hai — triggers identify karna helpful rahega.",
        "challenging": "Partner ke temper challenging zone me dikhta hai — conflict spikes frequent ho sakte hain bina calm approach ke.",
    },
    "emotional_style": {
        "balanced": "Partner emotionally balanced expressive range me dikhta hai — feelings share karta hai par guarded bhi reh sakta hai.",
        "mixed": "Partner emotionally mixed style me hai — kabhi expressive kabhi reserved.",
        "complex": "Emotional style complex hai — trust ke baad zyada khulta hai.",
        "challenging": "Emotional style challenging dikhta hai — distance ya mood swings closeness test karenge.",
    },
    "dominant_cooperative": {
        "balanced": "Partner nature balanced leadership dikhati hai — cooperative bhi, assertive bhi where needed.",
        "mixed": "Dominant aur cooperative dono sides dikhte hain — situation ke hisaab se shift hota hai.",
        "complex": "Dominance-cooperation balance complex hai — ego clashes avoid karne ke liye respect zaruri.",
        "challenging": "Dominant side zyada active dikhti hai — cooperative balance ke liye clear boundaries chahiye.",
    },
    "love_language": _BASE_OPENINGS,
    "family_background": _BASE_OPENINGS,
    "appearance_personality": _BASE_OPENINGS,
    "spiritual_practical": _BASE_OPENINGS,
    "attachment_depth": {
        "balanced": "Emotional attachment depth balanced dikhti hai — closeness grow ho jayegi with care.",
        "mixed": "Attachment depth mixed hai — caring moments ke saath distance phases bhi.",
        "complex": "Attachment complex pattern dikhata hai — reassurance + space dono matter karte hain.",
        "challenging": "Attachment challenging zone me dikhta hai — felt closeness easily fluctuate ho jayegi.",
    },
    "respect_behavior": _BASE_OPENINGS,
    "ideal_spouse": _BASE_OPENINGS,
    "qualities_attract": _BASE_OPENINGS,
    "culture_background": _BASE_OPENINGS,
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_nature": {
        "balanced": "Balanced matlab partner temperament mostly steady hai — daily life manageable rehti hai.",
        "mixed": "Mixed matlab traits align bhi hain aur test bhi karte hain.",
        "complex": "Complex matlab decode karna time lega — rush judgment avoid karein.",
        "challenging": "Challenging matlab unrealistic fantasy avoid karke realistic bond build karein.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_nature": {
        "balanced": "Steady respect + small gestures bond strong rakhenge.",
        "mixed": "Friction points calmly discuss karein — decode style over time.",
        "complex": "Boundaries clear rakhein — strong pulls ko manage karein.",
        "challenging": "Self-respect priority rakhein — toxic loops me repeat reaction avoid karein.",
    },
    "temper_anger": {
        "mixed": "Trigger moments par pause lein — react karne se pehle ek deep breath helpful rehta hai.",
        "challenging": "Conflict ke baad repair conversation zaruri — blame cycle break karein.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "balanced": "Nature mostly steady hai — understanding + respect se bond deepen ho jayega.",
    "mixed": "Mixed traits manage ho jayenge jab communication steady rahe.",
    "complex": "Complex nature samajhne me time lagega — consistent observation matter karega.",
    "challenging": "Challenging patterns realistic assessment maangte hain — change possible hai par effort dono taraf se chahiye.",
}

NATURE_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"jupiter.*support|jupiter\s+in\s+7", re.I), "Jupiter support partner nature ko fair + growth-oriented bana sakta hai."),
    (re.compile(r"mars.*7th|mars\s+on\s+7th", re.I), "Mars 7th par assertive / temper traits amplify ho sakte hain."),
    (re.compile(r"moon.*7th|moon\s+in\s+7", re.I), "Moon 7th emotional expressiveness ko colour karta hai."),
    (re.compile(r"saturn.*7th|saturn\s+on\s+7th", re.I), "Saturn 7th reserved / duty-bound nature la sakta hai."),
    (re.compile(r"rahu.*7th|rahu\s+on\s+7th", re.I), "Rahu 7th unconventional / complex personality traits la sakta hai."),
    (re.compile(r"venus.*mars|venus-mars", re.I), "Venus-Mars chemistry passion + impulse traits ko strong karta hai."),
    (re.compile(r"5th\s*lord\s*strong", re.I), "5th lord strength affection + warmth support karta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase partner-nature signals ko colour karti hai."),
]


def detect_partner_nature_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_partner_nature_angle

    q = (question or "").strip()
    angle = infer_partner_nature_angle(q) or "general_nature"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    if str(item.get("bucket") or "").strip().lower() == "partner_nature" and angle == "general_nature":
        if re.search(r"(?ix)\b(gussa|temper|anger)\b", q):
            angle = "temper_anger"
        elif re.search(r"(?ix)\b(expressive|reserved)\b", q):
            angle = "emotional_style"
        elif re.search(r"(?ix)\b(dominant|cooperative)\b", q):
            angle = "dominant_cooperative"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_nature").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_nature"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_nature").strip().lower()) or MEANING_TEMPLATES["general_nature"]
    return block.get(lv) or MEANING_TEMPLATES["general_nature"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_nature").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_nature"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_nature"].get(lv, "Partner style samajhne ke liye consistent observation helpful rehta hai.")


def get_nature_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def nature_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in NATURE_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me partner-nature related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = nature_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
