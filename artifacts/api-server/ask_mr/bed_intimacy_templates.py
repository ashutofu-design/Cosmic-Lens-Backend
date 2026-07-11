"""Bed intimacy / physical intimacy engine — intent templates."""
from __future__ import annotations

import re
from typing import Any

INTIM_LEVELS: tuple[str, ...] = ("harmonious", "mixed", "sensitive", "strained")

VERDICT_LABELS: dict[str, str] = {
    "harmonious": "Harmonious",
    "mixed": "Mixed",
    "sensitive": "Sensitive",
    "strained": "Strained",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "harmonious": 78,
    "mixed": 64,
    "sensitive": 50,
    "strained": 30,
}

USER_SECTION = {
    "why_verdict": "Kyun ye verdict aaya:",
    "positive": "Is verdict ko support karne wale mukhya sanket:",
    "challenges": "Dhyan dene layak challenges:",
    "meaning": "Iska practical matlab:",
    "outlook": "Intimacy outlook:",
    "focus": "Aapko kis baat par dhyan dena chahiye:",
}

_BASE_OPENINGS: dict[str, str] = {
    "harmonious": "Chart ke hisaab se physical intimacy mostly harmonious range me dikhti hai — comfort + consent align reh sakte hain.",
    "mixed": "Physical intimacy mixed range me dikhti hai — closeness grow karti hai par needs clearly discuss karna helpful rehta hai.",
    "sensitive": "Physical intimacy sensitive zone me dikhti hai — stress ya emotional distance closeness ko affect karti hai.",
    "strained": "Physical intimacy strained range me dikhti hai — emotional safety pehle priority honi chahiye.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_intimacy": _BASE_OPENINGS,
    "suhag_raat": {
        "harmonious": "Suhag raat / early intimacy mostly harmonious range me dikhti hai — comfort gradually build hota hai.",
        "mixed": "Suhag raat / early intimacy mixed range me dikhti hai — nervousness normal hai, pace respect karna helpful rehta hai.",
        "sensitive": "Suhag raat / early intimacy sensitive zone me dikhti hai — emotional safety pehle matter karegi.",
        "strained": "Suhag raat / early intimacy strained range me dikhti hai — rush avoid karein, trust build priority rakhein.",
    },
    "bedroom_compat": {
        "harmonious": "Bedroom compatibility mostly harmonious range me dikhti hai — private comfort align rehta hai.",
        "mixed": "Bedroom compatibility mixed range me dikhti hai — needs + pace dono discuss karna helpful rehta hai.",
        "sensitive": "Bedroom compatibility sensitive zone me dikhti hai — mood swings closeness ko affect kar sakte hain.",
        "strained": "Bedroom compatibility strained range me dikhti hai — pressure ya mismatch comfort ko strain karta hai.",
    },
    "sexual_intimacy": {
        "harmonious": "Sexual intimacy mostly harmonious range me dikhti hai — physical comfort + respect align reh sakte hain.",
        "mixed": "Sexual intimacy mixed range me dikhti hai — comfort grow karta hai par open needs-talk helpful rehta hai.",
        "sensitive": "Sexual intimacy sensitive zone me dikhti hai — emotional safety pehle build karna zaruri rehta hai.",
        "strained": "Sexual intimacy strained range me dikhti hai — consent + boundaries clearly maintain karein.",
    },
    "conjugal_compat": {
        "harmonious": "Conjugal / private-life compatibility mostly harmonious range me dikhti hai — shared comfort grow karta hai.",
        "mixed": "Conjugal compatibility mixed range me dikhti hai — routine + affection balance helpful rehta hai.",
        "sensitive": "Conjugal compatibility sensitive zone me dikhti hai — stress private life ko affect karta hai.",
        "strained": "Conjugal compatibility strained range me dikhti hai — emotional repair pehle intimacy se pehle helpful rehta hai.",
    },
    "physical_compat": {
        "harmonious": "Physical compatibility mostly harmonious range me dikhti hai — body-level comfort align rehta hai.",
        "mixed": "Physical compatibility mixed range me dikhti hai — pull + comfort dono fluctuate karte hain.",
        "sensitive": "Physical compatibility sensitive zone me dikhti hai — comfort emotional safety se linked rehta hai.",
        "strained": "Physical compatibility strained range me dikhti hai — force ya pressure avoid karein.",
    },
    "emotional_safety": {
        "harmonious": "Emotional safety mostly supportive range me dikhti hai — trust build hone par intimacy deepen hoti hai.",
        "mixed": "Emotional safety mixed range me dikhti hai — vulnerability gradually open karna helpful rehta hai.",
        "sensitive": "Emotional safety sensitive zone me dikhti hai — past hurt ya insecurity closeness ko slow karti hai.",
        "strained": "Emotional safety strained range me dikhti hai — repair + reassurance pehle physical push se zyada matter karega.",
    },
    "intimacy_drive": {
        "harmonious": "Intimacy drive / desire mostly harmonious range me dikhti hai — mutual pull relatively balanced rehta hai.",
        "mixed": "Intimacy drive mixed range me dikhti hai — desire mismatch phases aayenge — calmly address karna helpful rehta hai.",
        "sensitive": "Intimacy drive sensitive zone me dikhti hai — stress ya fatigue desire ko affect karti hai.",
        "strained": "Intimacy drive strained range me dikhti hai — mismatch ko blame game se zyada calm talk se handle karein.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_intimacy": {
        "harmonious": "Harmonious matlab physical closeness comfort + respect ke saath grow karti hai.",
        "mixed": "Mixed matlab intimacy possible hai par needs clearly samajhna zaruri rehta hai.",
        "sensitive": "Sensitive matlab emotional state closeness ko zyada affect karti hai.",
        "strained": "Strained matlab physical push se pehle safety + trust repair priority hai.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_intimacy": {
        "harmonious": "Affection + respectful pace maintain karein — comfort naturally deepen hota hai.",
        "mixed": "Needs calmly discuss karein — assumptions avoid karein.",
        "sensitive": "Stress kam karein — emotional warmth pehle build karein.",
        "strained": "Pressure avoid karein — boundaries clear rakhein, repair pehle.",
    },
    "sexual_intimacy": {
        "mixed": "Consent + comfort check regular rakhein — rush avoid karein.",
        "strained": "Professional support ya couple talk helpful rehti hai jab strain repeat ho.",
    },
    "emotional_safety": {
        "sensitive": "Trust-building gestures + reassurance intimacy ko support karte hain.",
    },
    "intimacy_drive": {
        "mixed": "Desire mismatch par calmly sync karein — blame avoid karein.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "harmonious": "Intimacy outlook positive hai — comfort + affection steadily deepen hoti hai.",
    "mixed": "Mixed outlook improve ho jayega jab needs openly discuss hon aur pace respect ho.",
    "sensitive": "Sensitive outlook me emotional repair ke baad closeness improve hoti hai — rush avoid karein.",
    "strained": "Strained outlook me safety first — change possible hai par pressure se intimacy worsen hoti hai.",
}

INTIM_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"venus.*mars|venus_mars|venus-mars", re.I), "Venus-Mars link passion + physical closeness ko colour karta hai."),
    (re.compile(r"venus.*afflict|venus_afflict|venus.*dusthana|venus.*debil", re.I), "Afflicted Venus intimacy comfort uneven ya sensitive banati hai."),
    (re.compile(r"moon.*8th|moon_in_8th", re.I), "Moon 8th emotional vulnerability private life ko sensitive banata hai."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional safety ko strain karta hai — intimacy sensitive rehti hai."),
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th passion + friction dono private dynamics ko affect karta hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th slow / reserved intimacy tone la deta hai."),
    (re.compile(r"5th\s*lord\s*strong|fifth\s*lord\s*strong", re.I), "Strong 5th lord romantic warmth + playful closeness support karta hai."),
    (re.compile(r"ketu.*7th|nodes?\s+on\s+7th", re.I), "Ketu / nodes on 7th detachment ya unusual pull intimacy ko sensitive bana sakte hain."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase intimacy signals ko colour karti hai."),
]


def detect_bed_intimacy_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_bed_intimacy_angle

    q = (question or "").strip()
    angle = infer_bed_intimacy_angle(q) or "general_intimacy"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("physical_intimacy", "bed_intimacy") and angle == "general_intimacy":
        if re.search(r"(?ix)\b(sexual|sex|physical\s*intim)\b", q):
            angle = "sexual_intimacy"
        elif re.search(r"(?ix)\b(conjugal|private)\b", q):
            angle = "conjugal_compat"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_intimacy").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_intimacy"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_intimacy").strip().lower()) or MEANING_TEMPLATES["general_intimacy"]
    return block.get(lv) or MEANING_TEMPLATES["general_intimacy"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_intimacy").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_intimacy"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_intimacy"].get(
        lv, "Intimacy samajhne ke liye comfort + consent + emotional safety observe karna helpful rehta hai."
    )


def get_intim_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def intim_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in INTIM_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me intimacy-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = intim_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
