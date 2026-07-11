"""Relationship remedies engine — intent templates (upay / mantra / puja)."""
from __future__ import annotations

import re
from typing import Any

REM_LEVELS: tuple[str, ...] = ("supportive", "moderate", "cautious", "limited")

VERDICT_LABELS: dict[str, str] = {
    "supportive": "Supportive",
    "moderate": "Moderate",
    "cautious": "Cautious",
    "limited": "Limited",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "supportive": 78,
    "moderate": 64,
    "cautious": 48,
    "limited": 28,
}

USER_SECTION = {
    "why_verdict": "Kyun ye verdict aaya:",
    "positive": "Is verdict ko support karne wale mukhya sanket:",
    "challenges": "Dhyan dene layak challenges:",
    "meaning": "Iska practical matlab:",
    "outlook": "Relationship remedy outlook:",
    "focus": "Aapko kis baat par dhyan dena chahiye:",
}

_BASE_OPENINGS: dict[str, str] = {
    "supportive": "Chart ke hisaab se relationship remedies mostly supportive range me dikhte hain — gentle upay + daily habit harmony ko help karte hain.",
    "moderate": "Remedy scope moderate range me dikhta hai — mantra/prayer helpful hain par behaviour change bhi zaruri hai.",
    "cautious": "Remedy scope cautious range me dikhta hai — pattern fix pehle, shortcut upay baad me.",
    "limited": "Remedy scope limited range me dikhta hai — toxic dynamics sirf upay se replace nahi hote.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_remedy": _BASE_OPENINGS,
    "mantra_upay": {
        "supportive": "Mantra upay mostly supportive range me dikhta hai — steady jap + simple seva bond ko anchor karta hai.",
        "moderate": "Mantra upay moderate range me dikhta hai — daily jap helpful hai par talk + respect bhi chahiye.",
        "cautious": "Mantra upay cautious range me dikhta hai — mantra ke saath friction pattern bhi address karein.",
        "limited": "Mantra upay limited range me dikhta hai — repeated hurt par sirf mantra enough nahi rehta.",
    },
    "puja_totka": {
        "supportive": "Puja / totka scope mostly supportive range me dikhta hai — simple ritual + faith harmony support karte hain.",
        "moderate": "Puja / totka moderate range me dikhta hai — ritual helpful hai par daily behaviour equal important hai.",
        "cautious": "Puja / totka cautious range me dikhta hai — symptom cover se zyada root pattern fix karein.",
        "limited": "Puja / totka limited range me dikhta hai — unhealthy bond par ritual alone kaam nahi karta.",
    },
    "love_harmony": {
        "supportive": "Love harmony remedies mostly supportive range me dikhte hain — small kindness rituals closeness badhate hain.",
        "moderate": "Love harmony remedies moderate range me dikhte hain — upay + consistent care dono chahiye.",
        "cautious": "Love harmony remedies cautious range me dikhte hain — pehle respect/boundary, phir upay.",
        "limited": "Love harmony remedies limited range me dikhte hain — one-sided effort par upay weak pad jata hai.",
    },
    "marriage_remedy": {
        "supportive": "Marriage remedies mostly supportive range me dikhte hain — steady prayer + shared seva helpful rehti hai.",
        "moderate": "Marriage remedies moderate range me dikhte hain — ritual + practical alignment dono zaruri hain.",
        "cautious": "Marriage remedies cautious range me dikhte hain — family pressure me blind ritual avoid karein.",
        "limited": "Marriage remedies limited range me dikhte hain — mismatch par upay alone marriage fix nahi karta.",
    },
    "friction_fix": {
        "supportive": "Friction-fix remedies mostly supportive range me dikhte hain — calm talk + simple upay repair ko help karte hain.",
        "moderate": "Friction-fix remedies moderate range me dikhte hain — upay ke saath argument pattern bhi break karein.",
        "cautious": "Friction-fix remedies cautious range me dikhte hain — repeated fight par boundary + upay dono chahiye.",
        "limited": "Friction-fix remedies limited range me dikhte hain — abuse/toxic pattern par upay substitute nahi hai.",
    },
    "gemstone_query": {
        "supportive": "Gemstone route dominant nahi — chart simple habit + mantra ko zyada support karta hai.",
        "moderate": "Gemstone query moderate range me dikhti hai — ratna optional hai, behaviour + prayer base rakhein.",
        "cautious": "Gemstone query cautious range me dikhti hai — expensive stone bina proof ke avoid karein.",
        "limited": "Gemstone query limited range me dikhti hai — gem shortcut toxic friction replace nahi karta.",
    },
    "daan_seva": {
        "supportive": "Daan / seva remedies mostly supportive range me dikhte hain — humility + kindness bond soften karte hain.",
        "moderate": "Daan / seva moderate range me dikhte hain — seva helpful hai par daily respect bhi zaruri hai.",
        "cautious": "Daan / seva cautious range me dikhte hain — daan guilt-fix ke liye nahi, sincere intent se karein.",
        "limited": "Daan / seva limited range me dikhte hain — deep mismatch par sirf daan enough nahi rehta.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_remedy": {
        "supportive": "Supportive matlab gentle upay chart friction ko soften kar sakte hain — consistency key hai.",
        "moderate": "Moderate matlab upay helpful hain par behaviour shift bina sustain nahi hote.",
        "cautious": "Cautious matlab pehle pattern samjhein, phir upay choose karein.",
        "limited": "Limited matlab remedies toxic dynamics ka replacement nahi hain.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_remedy": {
        "supportive": "Ek simple Friday Venus prayer + weekly kind gesture — 4 hafte consistent rakhein.",
        "moderate": "Mantra ke saath calm talk ritual add karein — upay + action dono track karein.",
        "cautious": "Upay se pehle non-negotiable boundary set karein — repeat hurt par pause karein.",
        "limited": "Safety first — professional help ya exit plan upay se pehle consider karein.",
    },
    "mantra_upay": {
        "supportive": "Daily 108× simple Venus/Guru mantra — same time, same place, 21 din.",
    },
    "puja_totka": {
        "moderate": "Simple home puja Friday evening — fancy ritual se zyada sincerity matter karti hai.",
    },
    "friction_fix": {
        "cautious": "Fight ke baad 24-hour cool-down rule + short repair talk — upay ke saath habit fix karein.",
    },
    "gemstone_query": {
        "cautious": "Gemstone tabhi jab qualified astrologer + multi-factor proof ho — otherwise mantra/habit base rakhein.",
    },
    "daan_seva": {
        "supportive": "Thursday ko simple seva/daan — white sweets ya clothes, humble intent ke saath.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "supportive": "Remedy outlook positive hai — steady upay + respect se bond improve hota hai.",
    "moderate": "Moderate outlook improve hoga jab ritual aur behaviour dono align hon.",
    "cautious": "Cautious outlook better hoga jab root friction honestly address ho.",
    "limited": "Limited outlook me realism first — change tabhi jab effort mutual ho.",
}

REM_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"jupiter.*7th|jupiter_supportive|jupiter", re.I), "Jupiter support gentle prayer + wisdom-based upay ko help karta hai."),
    (re.compile(r"5th\s*lord\s*strong|fifth\s*lord\s*strong", re.I), "Strong 5th lord romance rituals + emotional reopening ko support karta hai."),
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th harsh speech friction — Tuesday calm-talk remedy helpful rehti hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th slow tests — Saturday seva/mantra steady effort maangta hai."),
    (re.compile(r"rahu.*7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th chaos — routine + simple Shiva prayer grounding deti hai."),
    (re.compile(r"venus.*debilit|venus_afflict|venus.*dusthana", re.I), "Venus affliction affection rituals + Friday prayer ko highlight karta hai."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional volatility — Monday calm habits remedy ko support karte hain."),
    (re.compile(r"hidden\s+ties|third_person", re.I), "Hidden ties transparency habits pehle zaruri banate hain — upay alone kaafi nahi."),
    (re.compile(r"reconnection_yoga|reconnection", re.I), "Reconnection yoga repair-focused gentle upay ko support karta hai."),
]


def detect_relationship_remedies_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_relationship_remedies_angle

    q = (question or "").strip()
    angle = infer_relationship_remedies_angle(q) or "general_remedy"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    intent = str(item.get("intent") or "").strip().lower()
    if bucket == "relationship_remedies" and angle == "general_remedy":
        if "mantra" in intent:
            angle = "mantra_upay"
        elif "marriage" in intent or "shaadi" in intent:
            angle = "marriage_remedy"
        elif "gem" in intent or "stone" in intent:
            angle = "gemstone_query"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_remedy").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_remedy"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["moderate"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_remedy").strip().lower()) or MEANING_TEMPLATES["general_remedy"]
    return block.get(lv) or MEANING_TEMPLATES["general_remedy"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_remedy").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_remedy"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_remedy"].get(
        lv, "Remedy samajhne ke liye simple daily habit + sincere prayer observe karna helpful rehta hai."
    )


def get_rem_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "moderate").strip().lower()) or OUTLOOK_TEMPLATES["moderate"]


def rem_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in REM_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me relationship-remedy factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = rem_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
