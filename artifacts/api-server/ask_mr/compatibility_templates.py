"""Compatibility engine — intent templates (opening, meaning, practical per angle × level)."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

COMPAT_LEVELS: tuple[str, ...] = ("supportive", "moderate", "mixed", "strained")

VERDICT_LABELS: dict[str, str] = {
    "supportive": "Supportive",
    "moderate": "Moderate",
    "mixed": "Mixed",
    "strained": "Strained",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "supportive": 78,
    "moderate": 62,
    "mixed": 52,
    "strained": 38,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["growth"] = "Bond growth outlook —"

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_compatibility": {
        "supportive": "Chart ke hisaab se overall compatibility supportive dikhti hai — bond respect aur care se grow kar sakta hai.",
        "moderate": "Overall compatibility moderate range me hai — mel hai, lekin clear talk aur steady effort dono zaruri hain.",
        "mixed": "Overall compatibility mixed signals deti hai — alignment hai par friction points bhi active hain.",
        "strained": "Overall compatibility strained pattern dikhati hai — effort aur realistic boundaries dono important hain.",
    },
    "emotional_compatibility": {
        "supportive": "Emotional compatibility supportive dikhti hai — caring depth aur mood-sync dono ke beech maujood hain.",
        "moderate": "Emotional compatibility moderate hai — feelings align ho sakte hain par sensitive moments par extra care chahiye.",
        "mixed": "Emotional compatibility mixed hai — caring depth hai par mood ya distance par steady expression zaruri hai.",
        "strained": "Emotional compatibility strained zone me dikhti hai — reassurance ke bina reactions escalate ho sakte hain.",
    },
    "mental_compatibility": {
        "supportive": "Mental compatibility supportive dikhti hai — soch ka rhythm mostly align ho jayega.",
        "moderate": "Mental compatibility moderate hai — thinking styles thodi alag ho jayengi par dialogue se mel improve hota hai.",
        "mixed": "Mental compatibility mixed hai — processing style alag ho to plainly explain karna helpful rehta hai.",
        "strained": "Mental compatibility strained pattern dikhati hai — misunderstandings frequent ho jayengi bina calm talk ke.",
    },
    "intellectual_compatibility": {
        "supportive": "Intellectual compatibility supportive dikhti hai — ideas aur conversation depth match kar sakte hain.",
        "moderate": "Intellectual compatibility moderate hai — pace ya depth alag ho to adjust karna pad sakta hai.",
        "mixed": "Intellectual compatibility mixed hai — interests align hain par debate style friction la sakta hai.",
        "strained": "Intellectual compatibility strained zone me hai — conversation gaps ya ego clashes test karenge.",
    },
    "personalities_match": {
        "supportive": "Personalities match supportive dikhta hai — daily temperament mostly complement karta hai.",
        "moderate": "Personality match moderate hai — traits align hain par kuch habits adjust karni pad jayengi.",
        "mixed": "Personality match mixed hai — vibe hai par temperament clashes friction la sakte hain.",
        "strained": "Personality match strained dikhta hai — daily style differences bina respect ke conflict ban sakte hain.",
    },
    "thinking_match": {
        "supportive": "Thinking / mindset match supportive dikhta hai — soch aur priorities mostly align hain.",
        "moderate": "Thinking match moderate hai — ideas align hain par approach thoda alag ho jayega.",
        "strained": "Thinking match strained dikhta hai — core beliefs par clash bina dialogue ke widen ho jayega.",
    },
    "values_match": {
        "supportive": "Values / principles align supportive dikhte hain — ethics aur priorities mostly same range me hain.",
        "moderate": "Values match moderate hai — core ethics align hain par lifestyle choices par adjust chahiye.",
        "mixed": "Values match mixed hai — kuch principles align hain par priorities different ho jayengi.",
        "strained": "Values alignment strained dikhti hai — non-negotiables par clash realistic assessment maango.",
    },
    "life_goals_match": {
        "supportive": "Life goals match supportive dikhta hai — long-term direction mostly align ho jayega.",
        "moderate": "Life goals moderate alignment me hain — ambitions similar hain par timeline alag ho jayegi.",
        "mixed": "Life goals mixed alignment dikhate hain — sapne align hain par execution style different ho jayega.",
        "strained": "Life goals strained alignment dikhti hai — future direction par honest alignment talk zaruri hai.",
    },
    "expectations_match": {
        "supportive": "Expectations mostly match karti hain — dono ki ummeedein realistic range me align hain.",
        "moderate": "Expectations moderate match me hain — kuch priorities align hain par clarify karna helpful rahega.",
        "mixed": "Expectations mixed alignment dikhati hain — assumed expectations friction la jayengi.",
        "strained": "Expectations strained mismatch dikhta hai — unspoken ummeedein disappointment la jayengi.",
    },
    "gun_milan": {
        "supportive": "Gun milan / ashtakoot ke supportive indicators dikhte hain — traditional match score achhi range me hai.",
        "moderate": "Gun milan moderate range me dikhta hai — kuch gunas strong hain par kuch par attention chahiye.",
        "mixed": "Gun milan mixed results deta hai — supportive aur challenging gunas dono active hain.",
        "strained": "Gun milan strained pattern dikhata hai — challenging gunas zyada weight le rahe hain; remedies + understanding dono matter karte hain.",
    },
    "chemistry_match": {
        "supportive": "Chemistry / spark supportive dikhti hai — attraction aur romantic energy align ho jayengi.",
        "moderate": "Chemistry moderate range me hai — spark hai par consistency par depend karega.",
        "mixed": "Chemistry mixed hai — attraction phases me strong ho jayegi par stability test hogi.",
        "strained": "Chemistry strained zone me dikhti hai — spark ke bina emotional distance feel ho jayega.",
    },
    "overall_match": {
        "supportive": "Overall match supportive dikhta hai — rishta grow karne ke liye achha foundation hai.",
        "moderate": "Overall match moderate hai — sahi direction me hai par daily effort matter karega.",
        "mixed": "Overall match mixed signals deta hai — potential hai par friction points address karne honge.",
        "strained": "Overall match strained dikhta hai — realistic effort + boundaries ke bina bond test hoga.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_compatibility": {
        "supportive": "Supportive matlab bond grow karne ke liye foundation achha hai — respect daily practice hai.",
        "moderate": "Moderate matlab mel hai par friction ignore mat karein.",
        "mixed": "Mixed matlab align + friction dono ek saath active hain.",
        "strained": "Strained matlab effort + boundaries ke bina gap widen ho jayega.",
    },
    "emotional_compatibility": {
        "supportive": "Emotional depth present hai — caring gestures bond strengthen karte hain.",
        "mixed": "Feelings hain par expression style different ho jayega.",
        "strained": "Emotional safety pe kaam karna priority honi chahiye.",
    },
    "gun_milan": {
        "supportive": "Traditional score supportive hai — lekin daily behaviour bhi utna hi matter karta hai.",
        "mixed": "Gun milan ek guide hai — relationship success sirf score par depend nahi karti.",
        "strained": "Low gunas friction highlight karte hain — understanding + effort se manage ho jayega.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_compatibility": {
        "supportive": "Respect + small daily gestures bond ko strong rakhenge.",
        "moderate": "Weekly calm conversation friction ko early catch karega.",
        "mixed": "Friction points list karke ek-ek par calmly baat karein.",
        "strained": "Non-negotiables clear karein — unrealistic expectations adjust karein.",
    },
    "emotional_compatibility": {
        "supportive": "Emotional appreciation regularly express karein.",
        "mixed": "Mood swings par blame game avoid karein — facts se baat karein.",
        "strained": "Emotional needs plainly likh kar share karein — assume mat karein.",
    },
    "mental_compatibility": {
        "moderate": "Soch ka difference ko problem nahi, dialogue topic banayein.",
        "strained": "Repeat misunderstandings par pause + recap helpful rehta hai.",
    },
    "values_match": {
        "mixed": "Core values vs preferences alag karein — non-negotiables pe align verify karein.",
        "strained": "Values clash par compromise possible hai ya nahi — honestly assess karein.",
    },
    "gun_milan": {
        "moderate": "Weak gunas par conscious effort + remedies consider karein.",
        "strained": "Score se zyada daily behaviour pattern dekhein — gun milan guide hai, final word nahi.",
    },
}

GROWTH_TEMPLATES: dict[str, str] = {
    "supportive": "Bond grow karne ke liye foundation achha hai — consistency se compatibility aur strong ho jayegi.",
    "moderate": "Moderate compatibility grow ho jayegi jab communication steady rahe.",
    "mixed": "Mixed phase me targeted effort (trust, talk, respect) alignment improve kar sakta hai.",
    "strained": "Strained phase me realistic goals + small wins se trust rebuild ho jayega — ideal instant-match expect mat karein.",
}

COMPAT_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"moon.*support|moon-moon|emotional\s+reopen", re.I), "Emotional sync / caring depth compatibility ko support karti hai."),
    (re.compile(r"5th\s*lord\s*strong|venus.*support", re.I), "Romantic / affection layer compatibility ko strengthen karti hai."),
    (re.compile(r"saturn.*7th|saturn\s+on\s+7th", re.I), "Saturn 7th par delay aur distance friction la sakta hai."),
    (re.compile(r"mars.*7th|mars\s+on\s+7th", re.I), "Mars 7th par conflict style compatibility test karta hai."),
    (re.compile(r"moon\s+afflict|moon\s+under", re.I), "Moon affliction emotional reactions ko sensitive bana sakti hai."),
    (re.compile(r"rahu.*7th|loyalty\s+lines\s+blur", re.I), "Rahu / blur themes trust + alignment ko test karte hain."),
    (re.compile(r"mercury|mental|intellect", re.I), "Mental / communication style compatibility factor active hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase compatibility signals ko colour karti hai."),
]


def detect_compatibility_answer_focus(
    question: str,
    *,
    question_dna: dict[str, Any] | None = None,
) -> str:
    """Question + optional DNA → compatibility intent angle for template selection."""
    from ask_intent_fidelity import infer_compatibility_angle

    q = (question or "").strip()
    angle = infer_compatibility_angle(q) or "general_compatibility"

    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw

    bucket = str(item.get("bucket") or "").strip().lower()
    intent = str(item.get("intent") or "").strip().lower()

    if bucket == "compatibility" and angle == "general_compatibility":
        if re.search(r"(?ix)\b(gun|guna|ashtakoot|36)\b", q):
            angle = "gun_milan"
        elif re.search(r"(?ix)\b(emotion|dil|feel)\b", q):
            angle = "emotional_compatibility"
        elif re.search(r"(?ix)\b(mental|dimaag|thinking|soch)\b", q):
            angle = "mental_compatibility"
        elif re.search(r"(?ix)\b(value|sanskaar)\b", q):
            angle = "values_match"
    if "gun" in intent or "milan" in intent:
        angle = "gun_milan"
    elif "emotional" in intent:
        angle = "emotional_compatibility"
    elif "mental" in intent:
        angle = "mental_compatibility"

    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_compatibility").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_compatibility"]
    return block.get(lv) or block.get("moderate", block["strained"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_compatibility").strip().lower()
    block = MEANING_TEMPLATES.get(ang) or MEANING_TEMPLATES.get("general_compatibility") or {}
    return block.get(lv) or MEANING_TEMPLATES["general_compatibility"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_compatibility").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES.get("general_compatibility") or {}
    return block.get(lv) or PRACTICAL_TEMPLATES["general_compatibility"].get(lv, "Friction ko time par address karein — compatibility effort se improve hoti hai.")


def get_growth_outlook(level: str) -> str:
    lv = (level or "moderate").strip().lower()
    return GROWTH_TEMPLATES.get(lv) or GROWTH_TEMPLATES["moderate"]


def compat_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in COMPAT_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me compatibility-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = compat_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
