"""Relationship verification engine — intent templates (consistency / proof)."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

RVER_LEVELS: tuple[str, ...] = ("consistent", "mixed", "inconsistent", "unreliable")

VERDICT_LABELS: dict[str, str] = {
    "consistent": "Consistent",
    "mixed": "Mixed",
    "inconsistent": "Inconsistent",
    "unreliable": "Unreliable",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "consistent": 78,
    "mixed": 62,
    "inconsistent": 46,
    "unreliable": 28,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["outlook"] = _NATURAL_SEC["rver_outlook"]

_BASE_OPENINGS: dict[str, str] = {
    "consistent": "Chart ke hisaab se relationship verification mostly consistent range me dikhti hai — words + actions alignment supportive dikhta hai.",
    "mixed": "Verification mixed range me dikhti hai — kuch signals align hain par proof gaps bhi active hain.",
    "inconsistent": "Verification inconsistent range me dikhti hai — bolne aur karne me gap visible dikhta hai.",
    "unreliable": "Verification unreliable range me dikhti hai — promises par blind trust risky reh sakta hai.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_verification": _BASE_OPENINGS,
    "words_actions": {
        "consistent": "Words vs actions mostly consistent range me dikhte hain — partner ki baat aur behaviour align dikhti hai.",
        "mixed": "Words vs actions mixed range me dikhte hain — kuch areas match, kuch mismatch test karte hain.",
        "inconsistent": "Words vs actions inconsistent range me dikhte hain — bolne aur karne me gap active hai.",
        "unreliable": "Words vs actions unreliable range me dikhte hain — promises aur daily actions match nahi karte.",
    },
    "proof_gap": {
        "consistent": "Proof gap mostly narrow dikhta hai — supportive markers genuine intent ko back karte hain.",
        "mixed": "Proof gap mixed range me dikhta hai — kuch evidence hai par full cross-check helpful rehti hai.",
        "inconsistent": "Proof gap inconsistent range me dikhta hai — actions se zyada words par depend ho raha hai.",
        "unreliable": "Proof gap unreliable range me dikhta hai — proof over promises stance zaruri hai.",
    },
    "genuine_intent": {
        "consistent": "Genuine intent mostly consistent range me dikhta hai — real care + follow-through visible hai.",
        "mixed": "Genuine intent mixed range me dikhta hai — interest hai par consistency verify karni padegi.",
        "inconsistent": "Genuine intent inconsistent range me dikhta hai — intent aur action dono align nahi karte.",
        "unreliable": "Genuine intent unreliable range me dikhta hai — surface charm zyada, depth kam dikhti hai.",
    },
    "behaviour_consistency": {
        "consistent": "Behaviour consistency mostly consistent range me dikhti hai — daily actions steady rehte hain.",
        "mixed": "Behaviour consistency mixed range me dikhti hai — ups + downs dono phases aayenge.",
        "inconsistent": "Behaviour consistency inconsistent range me dikhti hai — mood ya effort fluctuate karta hai.",
        "unreliable": "Behaviour consistency unreliable range me dikhti hai — pattern unpredictable reh sakta hai.",
    },
    "promise_reality": {
        "consistent": "Promise vs reality mostly consistent range me dikhti hai — wade aur kaam align dikhte hain.",
        "mixed": "Promise vs reality mixed range me dikhti hai — kuch wade follow hote hain, kuch delay hote hain.",
        "inconsistent": "Promise vs reality inconsistent range me dikhti hai — gap repeat hota dikhta hai.",
        "unreliable": "Promise vs reality unreliable range me dikhti hai — words zyada, delivery kam dikhti hai.",
    },
    "cross_check": {
        "consistent": "Cross-check need mostly low dikhti hai — alignment markers strong hain, phir bhi healthy verify useful rehta hai.",
        "mixed": "Cross-check mixed range me helpful dikhti hai — facts + behaviour dono track karein.",
        "inconsistent": "Cross-check inconsistent zone me zaruri dikhti hai — gaps honestly address karein.",
        "unreliable": "Cross-check unreliable zone me critical dikhti hai — proof over promises rule follow karein.",
    },
    "reliability_signal": {
        "consistent": "Reliability signal mostly consistent range me dikhta hai — partner dependable pattern dikhata hai.",
        "mixed": "Reliability signal mixed range me dikhta hai — dependable moments hain par gaps bhi.",
        "inconsistent": "Reliability signal inconsistent range me dikhta hai — trust easily shake hota dikhta hai.",
        "unreliable": "Reliability signal unreliable range me dikhta hai — dependability weak dikhti hai.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_verification": {
        "consistent": "Consistent matlab words + actions mostly same direction me hain — trust verify karte rahein.",
        "mixed": "Mixed matlab proof aur gap dono active hain — pattern track karna helpful rehta hai.",
        "inconsistent": "Inconsistent matlab mismatch repeat hota dikhta hai — facts collect karein.",
        "unreliable": "Unreliable matlab blind trust risky hai — boundaries + proof first.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_verification": {
        "consistent": "Weekly small promises track karein — follow-through consistency confirm karti hai.",
        "mixed": "3-4 hafte behaviour log rakhein — pattern samajhne me help milti hai.",
        "inconsistent": "Mismatch points calmly discuss karein — repeat pattern break karein.",
        "unreliable": "Big decisions tabhi jab actions 4-6 hafte steady hon.",
    },
    "proof_gap": {
        "mixed": "Proof = repeated actions, not only sweet words — timeline note karein.",
    },
    "cross_check": {
        "inconsistent": "Facts cross-check karein — social media, plans, aur availability align hon.",
    },
    "words_actions": {
        "inconsistent": "Jo bola tha vs jo hua — 2-3 recent examples likhke compare karein.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "consistent": "Verification outlook stable hai — steady respect se trust deepen hota hai.",
    "mixed": "Mixed outlook improve hoga jab proof gaps honestly address hon.",
    "inconsistent": "Inconsistent outlook tabhi better hoga jab actions consistently match hon.",
    "unreliable": "Unreliable outlook me realism first — change tabhi jab proof steady ho.",
}

RVER_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"5th\s*lord\s*strong|fifth\s*lord\s*strong|emotional\s+reopening", re.I), "Strong 5th lord / reopening words-actions alignment ko support karta hai."),
    (re.compile(r"saturn.*moon|saturn-moon", re.I), "Saturn-Moon link steady follow-through + emotional accountability support karta hai."),
    (re.compile(r"third_person|hidden\s+ties|parallel", re.I), "Hidden ties / third-person signal proof gap widen karta hai."),
    (re.compile(r"loyalty_risk|affair", re.I), "Loyalty risk cross-check + verify stance ko strengthen karta hai."),
    (re.compile(r"jupiter.*7th|jupiter", re.I), "Jupiter wise pacing + honest intent ko support karta hai."),
    (re.compile(r"rahu.*7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th unpredictable behaviour swings verification ko affect karte hain."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional inconsistency verification pattern ko affect karti hai."),
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th sharp reaction spikes words-actions gap badha sakta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase verification signals ko colour karti hai."),
]


def detect_relationship_verification_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_relationship_verification_angle

    q = (question or "").strip()
    angle = infer_relationship_verification_angle(q) or "general_verification"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    intent = str(item.get("intent") or "").strip().lower()
    if bucket == "relationship_verification" and angle == "general_verification":
        if "proof" in intent or "evidence" in intent:
            angle = "proof_gap"
        elif "consistent" in intent or "actions" in intent:
            angle = "words_actions"
        elif "reliable" in intent:
            angle = "reliability_signal"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_verification").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_verification"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_verification").strip().lower()) or MEANING_TEMPLATES["general_verification"]
    return block.get(lv) or MEANING_TEMPLATES["general_verification"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_verification").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_verification"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_verification"].get(
        lv, "Verification samajhne ke liye words + repeated actions observe karna helpful rehta hai."
    )


def get_rver_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def rver_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in RVER_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me relationship-verification factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = rver_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
