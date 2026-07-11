"""Secret relationship engine — intent templates."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

SECRET_LEVELS: tuple[str, ...] = ("low", "possible", "likely", "high")

VERDICT_LABELS: dict[str, str] = {
    "low": "Low",
    "possible": "Possible",
    "likely": "Likely",
    "high": "High",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "low": 72,
    "possible": 58,
    "likely": 44,
    "high": 28,
}

USER_SECTION = dict(_NATURAL_SEC)

_OPENING_COMMON: dict[str, str] = {
    "low": "Secret / hidden relationship ke strong indicators dominant nahi — transparency mostly manageable dikhti hai.",
    "possible": "Secret / hidden attention ke possible signals hain — verify karna zaruri hai, final proof nahi.",
    "likely": "Secret / parallel attention ke likely indicators active hain — secrecy patterns trust test karte hain.",
    "high": "Secret / hidden relationship ke high-risk indicators active hain — parallel attention trust ko weaken kar sakta hai. Ye final proof nahi, par transparency verify karna zaruri hai.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "secret_affair": {
        "low": "Strong secret-affair signal dominant nahi — transparency mostly manageable dikhti hai.",
        "possible": "Secret affair / chakkar ke possible indicators hain — facts verify karein.",
        "likely": "Secret affair ke likely patterns active hain — hidden attention trust test karega.",
        "high": "Secret affair ke high-risk indicators active hain — parallel attention trust ko seriously test karta hai.",
    },
    "chupke_rishta": {
        "low": "Chupke / hidden rishta ke strong yog kam dikhte hain.",
        "possible": "Chupke rishta ke possible signals hain — behaviour pattern verify karein.",
        "likely": "Chupke / hidden rishta ke likely indicators active hain.",
        "high": "Chupke / hidden rishta ke high-risk pattern dikh rahe hain — secrecy trust ko weaken karti hai.",
    },
    "parallel_attention": _OPENING_COMMON,
    "multiple_relationships": {
        "low": "Multiple / parallel relationship ke strong indicators nahi dikhte.",
        "possible": "Multiple attention ke possible signals hain — verify karna zaruri hai.",
        "likely": "Parallel / multiple relationship ke likely indicators active hain.",
        "high": "Multiple / parallel relationship ke high-risk pattern chart me active dikh rahe hain.",
    },
    "hidden_behavior": _OPENING_COMMON,
    "third_person_risk": {
        "low": "Partner kisi aur me interest ke strong signals dominant nahi — attention mostly aapki taraf dikhti hai.",
        "possible": "Partner kisi aur / third person me interest ke possible signals hain — behaviour pattern verify karna zaruri hai.",
        "likely": "Partner kisi aur me interest ke likely indicators active hain — parallel attention trust ko test karti hai.",
        "high": "Partner kisi aur me interest ke high-risk indicators active hain — ye final proof nahi, par transparency check zaruri hai.",
    },
    "general_secrecy": _OPENING_COMMON,
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_secrecy": {
        "low": "Low risk matlab secrecy dominant theme nahi — phir bhi facts se verify karte rahein.",
        "possible": "Possible matlab suspicion ke liye evidence incomplete hai — pattern observe karein.",
        "likely": "Likely matlab secrecy signals active hain — blind trust avoid karein.",
        "high": "High risk matlab secrecy pattern strong hai — realistic assessment + boundaries zaruri hain.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_secrecy": {
        "low": "Low dominant risk par bhi healthy transparency maintain karein.",
        "possible": "Words se zyada repeated behaviour pattern observe karein.",
        "likely": "Accusation se pehle facts collect karein — calm approach rakhein.",
        "high": "Serious conversation + boundaries set karein — emotional peak me decision avoid karein.",
    },
    "secret_affair": {
        "likely": "Pattern repeat ho raha hai ya nahi — facts based check karein.",
        "high": "Trust rebuild tabhi possible jab transparency consistently improve ho.",
    },
}

TRANSPARENCY_TEMPLATES: dict[str, str] = {
    "low": "Transparency mostly manageable hai — open facts se trust maintain rehta hai.",
    "possible": "Transparency verify karna helpful rahega — assumptions avoid karein.",
    "likely": "Transparency abhi sensitive zone me hai — repeated secrecy trust test karegi.",
    "high": "Transparency abhi high-risk zone me hai — consistent openness ke bina trust weak rehta hai.",
}

SECRET_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"third[\s-]?person|parallel\s+attention|hidden\s+ties", re.I), "Hidden / parallel attention secrecy ko amplify kar sakta hai."),
    (re.compile(r"12th.*5th|5th.*12th|hidden[\s-]?link", re.I), "12th-5th hidden-link theme secret attention ko support kar sakta hai."),
    (re.compile(r"rahu.*7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th secrecy + blur boundaries la sakte hain."),
    (re.compile(r"venus.*dusthana|venus\s+in\s+12", re.I), "Venus in hidden-house tone secret romance signals ko colour karta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase secrecy signals ko colour karti hai."),
]


def detect_secret_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_secret_angle

    q = (question or "").strip()
    angle = infer_secret_angle(q) or "general_secrecy"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("third_person_infidelity", "secret_relationship") and angle == "general_secrecy":
        if re.search(r"(?ix)\b(chupke|chhupa|hidden)\b", q):
            angle = "chupke_rishta"
        elif re.search(r"(?ix)\b(affair|chakkar)\b", q):
            angle = "secret_affair"
        elif re.search(r"(?ix)\b(parallel|multiple|do\s+rishte)\b", q):
            angle = "parallel_attention"
        elif re.search(
            r"(?ix)\b(kisi\s+aur|kis[ei]\s+aur|dusre\s+(?:me|se)|someone\s+else|interested|flirt)\b",
            q,
        ):
            angle = "third_person_risk"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "possible").strip().lower()
    ang = (angle or "general_secrecy").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_secrecy"]
    return block.get(lv) or _OPENING_COMMON.get(lv, _OPENING_COMMON["possible"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "possible").strip().lower()
    ang = (angle or "general_secrecy").strip().lower()
    block = MEANING_TEMPLATES.get(ang) or MEANING_TEMPLATES["general_secrecy"]
    return block.get(lv) or MEANING_TEMPLATES["general_secrecy"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "possible").strip().lower()
    ang = (angle or "general_secrecy").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_secrecy"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_secrecy"].get(lv, "Pattern observe karein — facts se verify karein.")


def get_transparency_outlook(level: str) -> str:
    return TRANSPARENCY_TEMPLATES.get((level or "possible").strip().lower()) or TRANSPARENCY_TEMPLATES["possible"]


def secret_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in SECRET_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me secrecy-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = secret_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
