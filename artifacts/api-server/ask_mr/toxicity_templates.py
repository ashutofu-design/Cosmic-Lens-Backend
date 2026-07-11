"""Toxicity / red-flag engine — intent templates."""
from __future__ import annotations

import re
from typing import Any

TOX_LEVELS: tuple[str, ...] = ("low", "moderate", "elevated", "high")

VERDICT_LABELS: dict[str, str] = {
    "low": "Low",
    "moderate": "Moderate",
    "elevated": "Elevated",
    "high": "High",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "low": 76,
    "moderate": 60,
    "elevated": 44,
    "high": 28,
}

USER_SECTION = {
    "why_verdict": "Kyun ye verdict aaya:",
    "positive": "Is verdict ko support karne wale mukhya sanket:",
    "challenges": "Dhyan dene layak challenges:",
    "meaning": "Iska practical matlab:",
    "outlook": "Toxicity outlook:",
    "focus": "Aapko kis baat par dhyan dena chahiye:",
}

_BASE_OPENINGS: dict[str, str] = {
    "low": "Chart ke hisaab se toxicity / red-flag signals mostly low range me dikhte hain — friction repairable range me hai.",
    "moderate": "Toxicity pattern moderate zone me dikhta hai — repeated friction boundaries maangta hai.",
    "elevated": "Toxicity / control themes elevated zone me active hain — harm-normalizing cycles avoid karna zaruri hai.",
    "high": "Toxicity / safety-risk signals high zone me active hain — self-protection + boundaries abhi priority honi chahiye.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_toxicity": _BASE_OPENINGS,
    "toxic_dynamic": {
        "low": "Toxic relationship dynamic ke strong signals dominant nahi — awareness + boundaries enough rehenge.",
        "moderate": "Toxic dynamic moderate zone me dikhta hai — control/jealousy ya harsh cycles test karenge.",
        "elevated": "Toxic dynamic elevated zone me active hai — repeated harm patterns boundaries maangte hain.",
        "high": "Toxic dynamic high-risk zone me dikhta hai — safety + space priority honi chahiye.",
    },
    "abuse_risk": {
        "low": "Abuse / violence ke dominant high-risk signals nahi dikhte — phir bhi boundaries maintain karein.",
        "moderate": "Abuse-risk moderate zone me dikhta hai — harsh conflict cycles escalate ho sakte hain bina limits ke.",
        "elevated": "Abuse-risk elevated zone me active hai — harm patterns seriously address karna zaruri hai.",
        "high": "Abuse / violence risk high zone me dikhta hai — safety, support aur boundaries immediate priority hain.",
    },
    "control_pattern": {
        "low": "Control / manipulation ke strong signals dominant nahi — healthy autonomy mostly preserved dikhti hai.",
        "moderate": "Control / manipulation moderate zone me dikhta hai — possessive or dominating cycles test karenge.",
        "elevated": "Control pattern elevated zone me active hai — autonomy regularly squeeze ho jayegi bina limits ke.",
        "high": "Control / manipulation high-risk zone me dikhta hai — coercive dynamics normalize mat hone dein.",
    },
    "gaslighting": {
        "low": "Gaslighting ke strong signals dominant nahi — reality-check mostly manageable rehta hai.",
        "moderate": "Gaslighting moderate zone me dikhta hai — doubt spikes boundaries maang sakte hain.",
        "elevated": "Gaslighting elevated zone me active hai — reality distortion trust ko seriously test karega.",
        "high": "Gaslighting high-risk pattern active hai — external support + firm boundaries zaruri hain.",
    },
    "red_flags": {
        "low": "Red-flag signals mostly low range me dikhte hain — small warnings observe karte rahein.",
        "moderate": "Red flags moderate zone me active hain — repeated warning signs ignore mat karein.",
        "elevated": "Red flags elevated zone me dikhte hain — pattern repeat ho raha hai ya nahi track karein.",
        "high": "Red flags high-risk zone me active hain — serious reassessment + safety planning zaruri dikhti hai.",
    },
    "unhealthy_dynamic": {
        "low": "Unhealthy dynamic ke strong signals dominant nahi — bond mostly workable range me dikhta hai.",
        "moderate": "Unhealthy relationship pattern moderate zone me dikhta hai — stress cycles boundaries maangte hain.",
        "elevated": "Unhealthy dynamic elevated zone me active hai — emotional harm loops widen ho sakte hain.",
        "high": "Unhealthy dynamic high-risk zone me dikhta hai — staying without change risky rehta hai.",
    },
    "jealousy_toxic": {
        "low": "Jealousy-driven toxicity ke dominant signals nahi — manageable insecurity range me dikhti hai.",
        "moderate": "Jealousy toxicity moderate zone me dikhti hai — possessive spikes friction badha sakte hain.",
        "elevated": "Jealousy elevated zone me active hai — control + suspicion cycles test karenge.",
        "high": "Jealousy toxicity high-risk zone me dikhti hai — restrictive behaviour normalize mat hone dein.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_toxicity": {
        "low": "Low matlab dominant harm pattern nahi — phir bhi boundaries healthy rakhein.",
        "moderate": "Moderate matlab friction repeat ho rahi hai — direct limits helpful rehte hain.",
        "elevated": "Elevated matlab harm-normalizing cycles serious zone me hain.",
        "high": "High matlab safety + self-protection immediate priority hai — astrology excuse nahi.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_toxicity": {
        "low": "Small warning signs par calmly observe karein — pattern repeat track karein.",
        "moderate": "Boundary set karein — harsh cycles ke baad repair tabhi jab respect return ho.",
        "elevated": "Trusted support person se baat karein — isolation harm patterns badhata hai.",
        "high": "Safety plan + distance options realistically assess karein — normalize mat karein.",
    },
    "abuse_risk": {
        "moderate": "Escalation signs par immediate limit set karein — argument peak me engage mat karein.",
        "high": "Professional support / safe space priority rakhein — harm justify mat hone dein.",
    },
    "control_pattern": {
        "moderate": "Autonomy areas clearly define karein — control requests ko calmly push back karein.",
        "elevated": "Coercive behaviour ko name karein — blame-shift pattern break karein.",
    },
    "gaslighting": {
        "moderate": "Facts journal / message record helpful rehta hai — memory-doubt loops break karta hai.",
    },
    "red_flags": {
        "moderate": "Red flag list likhke pattern repeat check karein — words se zyada behaviour matter karta hai.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "low": "Outlook relatively manageable hai — awareness se escalation avoid ho jayegi.",
    "moderate": "Moderate outlook improve ho jayega jab boundaries consistent rahein.",
    "elevated": "Elevated outlook me change tabhi jab partner accountability show kare — wait-only approach risky rehta hai.",
    "high": "High-risk outlook me self-protection first — change possible hai par safety non-negotiable rehni chahiye.",
}

TOX_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th par sharp conflict / control spikes amplify ho sakte hain."),
    (re.compile(r"rahu.*7th|rahu_on_7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th unpredictable pull + blur boundaries la sakte hain."),
    (re.compile(r"moon.*afflict|moon_afflict|moon.*rahu", re.I), "Afflicted Moon emotional volatility reactions spike kar sakti hai."),
    (re.compile(r"venus.*mars|venus_mars", re.I), "Venus-Mars tight pull passion + impulse control issues la sakta hai."),
    (re.compile(r"obsession|hidden\s+ties|parallel", re.I), "Obsession / hidden-ties pattern control + jealousy amplify kar sakta hai."),
    (re.compile(r"12th.*7th|12th\s*lord", re.I), "12th-7th link secrecy + hidden stress toxicity ko colour karta hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th cold/control tone relationship friction la sakta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase toxicity signals ko colour karti hai."),
]


def detect_toxicity_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_toxicity_angle

    q = (question or "").strip()
    angle = infer_toxicity_angle(q) or "general_toxicity"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("toxicity_red_flags", "toxicity"):
        if re.search(r"(?ix)\b(jealous\w*|jalan)\b", q):
            angle = "jealousy_toxic"
        elif re.search(r"(?ix)\b(control|manipulat\w*)\b", q) and angle == "general_toxicity":
            angle = "control_pattern"
        elif re.search(r"(?ix)\b(red\s*flag)\b", q) and angle == "general_toxicity":
            angle = "red_flags"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    if lv == "watch":
        lv = "moderate"
    ang = (angle or "general_toxicity").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_toxicity"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["moderate"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    if lv == "watch":
        lv = "moderate"
    block = MEANING_TEMPLATES.get((angle or "general_toxicity").strip().lower()) or MEANING_TEMPLATES["general_toxicity"]
    return block.get(lv) or MEANING_TEMPLATES["general_toxicity"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    if lv == "watch":
        lv = "moderate"
    ang = (angle or "general_toxicity").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_toxicity"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_toxicity"].get(
        lv, "Toxicity pattern samajhne ke liye behaviour tracking + boundaries helpful rehte hain."
    )


def get_tox_outlook(level: str) -> str:
    lv = (level or "moderate").strip().lower()
    if lv == "watch":
        lv = "moderate"
    return OUTLOOK_TEMPLATES.get(lv) or OUTLOOK_TEMPLATES["moderate"]


def tox_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in TOX_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me toxicity-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = tox_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
