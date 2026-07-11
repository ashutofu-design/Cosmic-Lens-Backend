"""Karmic marriage engine — intent templates."""
from __future__ import annotations

import re
from typing import Any

KARM_LEVELS: tuple[str, ...] = ("strong", "present", "mixed", "weak")

VERDICT_LABELS: dict[str, str] = {
    "strong": "Strong",
    "present": "Present",
    "mixed": "Mixed",
    "weak": "Weak",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "strong": 78,
    "present": 66,
    "mixed": 52,
    "weak": 32,
}

USER_SECTION = {
    "why_verdict": "Kyun ye verdict aaya:",
    "positive": "Is verdict ko support karne wale mukhya sanket:",
    "challenges": "Dhyan dene layak challenges:",
    "meaning": "Iska practical matlab:",
    "outlook": "Karmic bond outlook:",
    "focus": "Aapko kis baat par dhyan dena chahiye:",
}

_BASE_OPENINGS: dict[str, str] = {
    "strong": "Chart ke hisaab se karmic marriage theme mostly strong range me dikhta hai — depth + lessons dono highlighted hain.",
    "present": "Karmic marriage bond present range me dikhta hai — growth dharma + effort se aati hai.",
    "mixed": "Karmic marriage signals mixed range me dikhte hain — fate aur free will dono matter karte hain.",
    "weak": "Karmic marriage signal weak range me dikhta hai — practical compatibility + daily effort zyada matter karega.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_karmic": _BASE_OPENINGS,
    "soulmate": {
        "strong": "Deep recognition / destined-partner pattern mostly strong range me dikhta hai — instant fit + nodal depth possible hai.",
        "present": "Destined-partner pattern present range me dikhta hai — pehchan wala bond grow karta hai.",
        "mixed": "Destined-partner signals mixed hain — strong pull ke saath karmic tests bhi aayenge.",
        "weak": "Destined-partner signal weak range me dikhta hai — practical bond effort se build hoga.",
    },
    "twin_flame": {
        "strong": "Twin-flame style intensity mostly strong range me dikhti hai — mirror + transformation theme active hai.",
        "present": "Twin-flame pattern present range me dikhta hai — intense recognition + growth cycles possible hain.",
        "mixed": "Twin-flame signals mixed hain — passion aur friction dono teach karenge.",
        "weak": "Twin-flame signal weak range me dikhta hai — intensity alone bond guarantee nahi karti.",
    },
    "past_life": {
        "strong": "Past-life connection theme mostly strong range me dikhta hai — instant familiarity + karmic déjà vu possible hai.",
        "present": "Past-life connection present range me dikhti hai — purani story continue hone ka feel aa sakta hai.",
        "mixed": "Past-life signals mixed hain — familiarity ke saath unfinished lessons bhi active hain.",
        "weak": "Past-life signal weak range me dikhta hai — bond mostly present-life effort se define hoga.",
    },
    "karmic_debt": {
        "strong": "Karmic debt / lesson theme mostly strong range me dikhta hai — partnership through tests deepen hoti hai.",
        "present": "Karmic debt present range me dikhta hai — repay effort + dharma se load kam hota hai.",
        "mixed": "Karmic debt signals mixed hain — lessons repeat ho sakte hain bina awareness ke.",
        "weak": "Karmic debt signal weak range me dikhta hai — practical respect + care zyada driver banenge.",
    },
    "spiritual_growth": {
        "strong": "Spiritual growth through marriage mostly strong range me dikhti hai — dharma + wisdom path active hai.",
        "present": "Spiritual growth theme present range me dikhta hai — shaadi maturity + faith deepen karti hai.",
        "mixed": "Spiritual growth signals mixed hain — growth possible hai par ego tests bhi aayenge.",
        "weak": "Spiritual growth signal weak range me dikhta hai — bond mostly practical life skills se grow karega.",
    },
    "karmic_bond": {
        "strong": "Karmic marriage / rishta bond mostly strong range me dikhta hai — purpose-driven partnership theme active hai.",
        "present": "Karmic rishta bond present range me dikhta hai — lessons + depth dono dikhenge.",
        "mixed": "Karmic bond mixed range me dikhta hai — strong pull ke saath realistic tests bhi honge.",
        "weak": "Karmic bond weak signal range me dikhta hai — compatibility + respect pehle verify karein.",
    },
    "nodes_karma": {
        "strong": "Rahu-Ketu / nodal karmic pull mostly strong range me dikhta hai — sudden bond + detachment cycles teach karte hain.",
        "present": "Nodal karmic pull present range me dikhta hai — relationship axis par twist + recognition theme active hai.",
        "mixed": "Nodal signals mixed hain — magnetism aur confusion dono phases me aayenge.",
        "weak": "Nodal karmic pull weak range me dikhta hai — bond mostly conscious choices se shape hoga.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_karmic": {
        "strong": "Strong matlab partnership me depth + lessons clearly highlighted hain — growth possible hai.",
        "present": "Present matlab karmic theme active hai par doom language fit nahi karti.",
        "mixed": "Mixed matlab fate + free will dono play karte hain — awareness helpful rehti hai.",
        "weak": "Weak matlab karmic drama se zyada practical compatibility matter karegi.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_karmic": {
        "strong": "Lessons ko growth frame me rakhein — blame game avoid karein.",
        "present": "Dharma + respect daily practice se karmic theme balance hota hai.",
        "mixed": "Repeating patterns notice karein — same fight loop break karna helpful rehta hai.",
        "weak": "Practical compatibility + values check karein — astrology excuse nahi.",
    },
    "karmic_debt": {
        "present": "Responsibility + repair effort karmic load kam karte hain — escape fantasy avoid karein.",
    },
    "spiritual_growth": {
        "mixed": "Shared values + humility growth ko support karte hain.",
    },
    "past_life": {
        "mixed": "Instant familiarity ko verify karein — actions se trust build karein.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "strong": "Karmic outlook depth wala hai — lessons hard ho sakte hain par mature bond banta hai.",
    "present": "Present outlook growth-oriented hai — steady effort se bond mature hota hai.",
    "mixed": "Mixed outlook me awareness + boundaries dono helpful rehte hain.",
    "weak": "Weak outlook me realism first — practical love daily effort se deepen hota hai.",
}

KARM_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"rahu.*7th|rahu_on_7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th sudden karmic pull + twist laate hain."),
    (re.compile(r"ketu.*7th|ketu.*5th|ketu", re.I), "Ketu past-life detachment ya deep recognition theme laata hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th|saturn.*moon", re.I), "Saturn karmic lesson + discipline through partnership highlight karta hai."),
    (re.compile(r"venus.*nodal|venus.*rahu|venus.*ketu", re.I), "Venus under nodal pull love axis ko karmic intensity deta hai."),
    (re.compile(r"5th\s*lord|fifth\s*lord|5th\s*house", re.I), "5th house romance karma past affection cycles ko carry karta hai."),
    (re.compile(r"jupiter.*7th|jupiter", re.I), "Jupiter dharma + wisdom through marriage support karta hai."),
    (re.compile(r"separation_yoga|separation", re.I), "Separation yoga karmic tests repeat karta hai bina repair ke."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase karmic signals ko colour karti hai."),
]


def detect_karmic_marriage_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_karmic_marriage_angle

    q = (question or "").strip()
    angle = infer_karmic_marriage_angle(q) or "general_karmic"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("spiritual_karmic", "karmic_marriage") and angle == "general_karmic":
        if re.search(r"(?ix)\b(soul\s*mate|soulmate)\b", q):
            angle = "soulmate"
        elif re.search(r"(?ix)\b(past\s*life|pichle\s*janam)\b", q):
            angle = "past_life"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_karmic").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_karmic"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_karmic").strip().lower()) or MEANING_TEMPLATES["general_karmic"]
    return block.get(lv) or MEANING_TEMPLATES["general_karmic"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_karmic").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_karmic"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_karmic"].get(
        lv, "Karmic theme samajhne ke liye patterns + dharma-based effort observe karna helpful rehta hai."
    )


def get_karm_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def karm_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in KARM_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me karmic-marriage factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = karm_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
