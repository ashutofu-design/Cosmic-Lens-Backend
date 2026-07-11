"""Emotional attachment engine — intent templates."""
from __future__ import annotations

import re
from typing import Any

ATTACH_LEVELS: tuple[str, ...] = ("secure", "mixed", "anxious", "volatile")

VERDICT_LABELS: dict[str, str] = {
    "secure": "Secure",
    "mixed": "Mixed",
    "anxious": "Anxious",
    "volatile": "Volatile",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "secure": 78,
    "mixed": 62,
    "anxious": 46,
    "volatile": 30,
}

USER_SECTION = {
    "why_verdict": "Kyun ye verdict aaya:",
    "positive": "Is verdict ko support karne wale mukhya sanket:",
    "challenges": "Dhyan dene layak challenges:",
    "meaning": "Iska practical matlab:",
    "outlook": "Bonding outlook:",
    "focus": "Aapko kis baat par dhyan dena chahiye:",
}

_BASE_OPENINGS: dict[str, str] = {
    "secure": "Chart ke hisaab se felt closeness mostly secure dikhti hai — steady care se bond deepen ho jayega.",
    "mixed": "Emotional bonding mixed pattern dikhati hai — warmth ke saath sensitivity bhi active hai.",
    "anxious": "Felt closeness anxious zone me dikhti hai — fear-of-loss ya reassurance gaps reactions spike kar sakte hain.",
    "volatile": "Bonding volatile pattern active hai — emotional highs aur lows closeness ko test karenge.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_attachment": _BASE_OPENINGS,
    "attachment_style": {
        "secure": "Attachment style mostly secure dikhta hai — steady warmth + manageable sensitivity.",
        "mixed": "Attachment style mixed hai — caring moments ke saath withdrawal phases bhi.",
        "anxious": "Attachment style anxious zone me dikhta hai — reassurance need zyada ho sakti hai.",
        "volatile": "Attachment style volatile dikhta hai — intensity spikes closeness ko rollercoaster bana sakte hain.",
    },
    "emotional_needs": {
        "secure": "Emotional needs mostly fulfill ho sakti dikhti hain — care + respect balance rehta hai.",
        "mixed": "Emotional needs mixed pattern dikhati hain — kabhi poori kabhi incomplete feel ho sakti hain.",
        "anxious": "Emotional needs anxious zone me dikhti hain — unmet needs reactions amplify kar sakti hain.",
        "volatile": "Emotional needs volatile pattern me dikhti hain — highs ke baad low phases feel ho sakte hain.",
    },
    "bond_depth": {
        "secure": "Emotional bond depth secure range me dikhti hai — gehra lagav grow karne ki room hai.",
        "mixed": "Bond depth mixed hai — closeness grow hoti hai par consistency matter karegi.",
        "anxious": "Bond depth anxious zone me dikhti hai — felt closeness easily fluctuate ho jayegi.",
        "volatile": "Bond depth volatile pattern active hai — intense pulls ke saath sudden distance possible hai.",
    },
    "emotional_security": {
        "secure": "Emotionally safe feel karne ka pattern mostly supportive dikhta hai.",
        "mixed": "Emotional safety mixed hai — trust build hoga par testing moments aayenge.",
        "anxious": "Felt safety anxious zone me dikhti hai — doubt spikes reassurance maang sakte hain.",
        "volatile": "Emotional safety volatile zone me hai — security easily shake ho jayegi bina grounding ke.",
    },
    "fear_of_loss": {
        "secure": "Fear-of-loss ke strong spikes dominant nahi — bond mostly steady dikhta hai.",
        "mixed": "Loss-fear mixed pattern dikhata hai — stress moments par insecurity brief spikes de sakti hai.",
        "anxious": "Fear-of-loss anxious zone me active hai — separation worry reactions badha sakti hai.",
        "volatile": "Loss-fear volatile pattern me hai — intense worry + sudden calm swings possible hain.",
    },
    "mood_sensitivity": {
        "secure": "Mood sensitivity manageable range me dikhti hai — closeness mostly steady rehti hai.",
        "mixed": "Mood swings mixed impact dete hain — good days strong, low days distance feel ho sakti hai.",
        "anxious": "Mood sensitivity anxious zone me hai — low mood closeness ko quickly test karega.",
        "volatile": "Mood sensitivity volatile pattern active hai — emotional weather bond ko frequently shake karegi.",
    },
    "clinginess": {
        "secure": "Clingy / possessive spikes dominant nahi — space + closeness balance mostly healthy dikhta hai.",
        "mixed": "Clinginess mixed pattern dikhati hai — kabhi close kabhi space maangna.",
        "anxious": "Clingy / possessive pull anxious zone me active hai — reassurance loop possible hai.",
        "volatile": "Possessive intensity volatile zone me hai — tight hold + sudden pull-back dono possible.",
    },
    "emotional_distance": {
        "secure": "Emotional distance ke strong patterns dominant nahi — warmth mostly accessible dikhti hai.",
        "mixed": "Emotional distance mixed hai — close phases ke saath withdrawal windows.",
        "anxious": "Emotional distance anxious zone me test karegi — felt disconnect insecurity badha sakti hai.",
        "volatile": "Distance pattern volatile hai — closeness aur cold phases alternate ho sakte hain.",
    },
    "vulnerability": {
        "secure": "Vulnerability / khulne ka pattern mostly open dikhta hai — trust ke saath depth badhegi.",
        "mixed": "Vulnerability mixed hai — kabhi khula kabhi guarded rehna.",
        "anxious": "Vulnerability anxious zone me dikhti hai — open hone me hesitation + fear mix ho sakta hai.",
        "volatile": "Vulnerability volatile pattern me hai — deep share ke baad sudden guard possible hai.",
    },
    "reassurance": {
        "secure": "Reassurance need mostly manageable dikhti hai — steady affection enough rehta hai.",
        "mixed": "Reassurance need mixed hai — kabhi zyada kabhi kam validation chahiye.",
        "anxious": "Reassurance need anxious zone me active hai — repeated validation helpful rehta hai.",
        "volatile": "Reassurance pattern volatile hai — intense reassurance ke baad doubt wapas aa sakta hai.",
    },
    "emotional_intensity": {
        "secure": "Emotional intensity mostly balanced dikhti hai — passion steady warmth ke saath rehti hai.",
        "mixed": "Intensity mixed hai — strong moments ke saath calm phases.",
        "anxious": "Intensity anxious zone me spike ho sakti hai — fear + passion mix reactions la sakta hai.",
        "volatile": "Emotional intensity volatile pattern active hai — highs aur lows dono strong honge.",
    },
    "emotional_capacity": _BASE_OPENINGS,
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_attachment": {
        "secure": "Secure matlab felt closeness mostly steady hai — daily care bond ko hold karti hai.",
        "mixed": "Mixed matlab warmth aur sensitivity dono present hain — consistency matter karegi.",
        "anxious": "Anxious matlab reassurance + steady presence dono helpful rahenge.",
        "volatile": "Volatile matlab emotional grounding zaruri hai — reaction control important hai.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_attachment": {
        "secure": "Small caring gestures + respect bond ko steady rakhenge.",
        "mixed": "Low phases me calm presence rakhein — assumption se react mat karein.",
        "anxious": "Reassurance through actions, not only words — consistency key hai.",
        "volatile": "Emotional peak me decision avoid karein — cool-down ke baad baat karein.",
    },
    "fear_of_loss": {
        "anxious": "Loss-fear spike par facts + calm talk helpful rehti hai — panic reaction avoid karein.",
        "volatile": "Grounding rituals (walk, journal, pause) emotional swings manage karne me help karte hain.",
    },
    "emotional_needs": {
        "mixed": "Needs ko clearly express karein — partner mind-reading expect mat karein.",
        "anxious": "Unmet need par blame se pehle specific request helpful rehti hai.",
    },
    "bond_depth": {
        "mixed": "Depth badhane ke liye consistent small moments zyada matter karte hain grand gestures se.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "secure": "Bonding mostly steady hai — care + respect se depth badhegi.",
    "mixed": "Mixed phases manage ho jayenge jab emotional needs clearly share hon.",
    "anxious": "Anxious pattern improve ho sakta hai par steady reassurance + boundaries dono chahiye.",
    "volatile": "Volatile zone me realistic grounding plan helpful hai — change possible hai par effort consistent hona chahiye.",
}

ATTACH_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional sensitivity + mood-linked closeness la sakta hai."),
    (re.compile(r"moon.*debil|moon_debil", re.I), "Debilitated Moon felt safety ko test kar sakta hai."),
    (re.compile(r"moon.*8th|moon_in_8th", re.I), "Moon in 8th deep emotional intensity + privacy needs la sakta hai."),
    (re.compile(r"saturn.*moon|saturn_moon", re.I), "Saturn-Moon link emotional reserve ya slow warmth la sakta hai."),
    (re.compile(r"venus.*dusthana|venus_debil", re.I), "Venus stress affection expression ko colour karta hai."),
    (re.compile(r"5th\s*lord\s*strong|emotional\s+reopening", re.I), "5th lord / reopening support warm bonding ko help karta hai."),
    (re.compile(r"separation_yoga|obsession_pull", re.I), "Separation / obsession pull anxious bonding spikes la sakta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase bonding signals ko colour karti hai."),
]


def detect_emotional_attachment_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_emotional_attachment_angle

    q = (question or "").strip()
    angle = infer_emotional_attachment_angle(q) or "general_attachment"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("emotional_attachment", "emotional_bonding", "love_feelings") and angle == "general_attachment":
        if re.search(r"(?ix)\b(needs|zarurat)\b", q):
            angle = "emotional_needs"
        elif re.search(r"(?ix)\b(bond|gehra|depth)\b", q):
            angle = "bond_depth"
        elif re.search(r"(?ix)\b(style|pattern)\b", q):
            angle = "attachment_style"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_attachment").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_attachment"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_attachment").strip().lower()) or MEANING_TEMPLATES["general_attachment"]
    return block.get(lv) or MEANING_TEMPLATES["general_attachment"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_attachment").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_attachment"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_attachment"].get(
        lv, "Bonding style samajhne ke liye consistent observation helpful rehta hai."
    )


def get_attach_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def attach_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in ATTACH_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me bonding-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = attach_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
