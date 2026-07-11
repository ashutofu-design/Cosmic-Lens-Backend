"""Relationship decisions engine — intent templates (stay/leave/suitability)."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

RDEC_LEVELS: tuple[str, ...] = ("favorable", "wait", "cautious", "avoid")

VERDICT_LABELS: dict[str, str] = {
    "favorable": "Favorable",
    "wait": "Wait",
    "cautious": "Cautious",
    "avoid": "Avoid",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "favorable": 78,
    "wait": 62,
    "cautious": 48,
    "avoid": 28,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["outlook"] = _NATURAL_SEC["rdec_outlook"]

_BASE_OPENINGS: dict[str, str] = {
    "favorable": "Chart ke hisaab se relationship decision mostly favorable range me dikhta hai — honest effort se aage badhne ki room strong hai.",
    "wait": "Decision wait range me dikhta hai — abhi rush se bachkar 2-4 hafte consistent behaviour observe karna helpful rehta hai.",
    "cautious": "Decision cautious range me dikhta hai — pros + cons dono active hain, big step se pehle self-respect check zaruri hai.",
    "avoid": "Decision avoid-impulse range me dikhta hai — chart friction heavy dikhta hai, boundaries pehle set karna zaruri hai.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_decision": _BASE_OPENINGS,
    "stay_or_leave": {
        "favorable": "Stay vs leave choice mostly favorable-lean range me dikhti hai — repair + honest talk se stay path strong dikhta hai.",
        "wait": "Stay vs leave abhi wait range me dikhta hai — dono options ko data ke saath weigh karein, jaldi decide mat karein.",
        "cautious": "Stay vs leave cautious range me dikhta hai — friction heavy hai, self-respect + pattern check pehle karein.",
        "avoid": "Stay vs leave avoid-impulse range me dikhta hai — repeated hurt ya trust gap par stay blindly mat karein.",
    },
    "second_chance": {
        "favorable": "Second chance mostly favorable range me dikhta hai — reconnection support visible hai par equal effort chahiye.",
        "wait": "Second chance wait range me dikhta hai — partner ke actions 3-4 hafte observe karein before full reopen.",
        "cautious": "Second chance cautious range me dikhta hai — past pattern repeat ho to boundary set karna zaruri hai.",
        "avoid": "Second chance avoid range me dikhta hai — same cycle repeat hone ka risk zyada active hai.",
    },
    "leave_decision": {
        "favorable": "Leave/move-on lean dominant nahi — repair markers abhi stay path ko support karte hain.",
        "wait": "Leave decision wait range me dikhta hai — emotional spike me decide mat karein, calm window choose karein.",
        "cautious": "Leave decision cautious range me dikhta hai — self-respect + repeated friction dono weigh karein.",
        "avoid": "Leave/move-on lean avoid-impulse ke opposite — chart pressure heavy hai, exit ya hard boundary consider karein.",
    },
    "stay_continue": {
        "favorable": "Stay/continue mostly favorable range me dikhta hai — bond repair + steady effort se chal sakta hai.",
        "wait": "Stay/continue wait range me dikhta hai — partner consistency prove hone tak observe mode helpful rehta hai.",
        "cautious": "Stay/continue cautious range me dikhta hai — effort one-sided na ho, balance check karein.",
        "avoid": "Stay/continue avoid range me dikhta hai — chart me pressure zyada hai, blind continuation drain karega.",
    },
    "overall_suitability": {
        "favorable": "Overall suitability mostly favorable range me dikhti hai — values + respect alignment supportive dikhta hai.",
        "wait": "Suitability wait range me dikhti hai — long-term fit abhi fully clear nahi, time + observation helpful rehti hai.",
        "cautious": "Suitability cautious range me dikhti hai — kuch alignment hai par core friction points address karne padenge.",
        "avoid": "Suitability avoid range me dikhti hai — chart mismatch + pressure zyada active reh sakta hai.",
    },
    "move_forward": {
        "favorable": "Move-forward step mostly favorable range me dikhta hai — propose/official step ko chart support karta hai.",
        "wait": "Move-forward wait range me dikhta hai — next step se pehle emotional + practical alignment confirm karein.",
        "cautious": "Move-forward cautious range me dikhta hai — big leap se pehle trust + stability check karein.",
        "avoid": "Move-forward avoid range me dikhta hai — abhi next step rush karna friction badha sakta hai.",
    },
    "should_i": {
        "favorable": "Should-I framing mostly favorable lean deti hai — chart stay/continue path ko zyada support karta hai.",
        "wait": "Should-I answer wait range me dikhta hai — list pros/cons, 2-3 hafte observe karke decide karein.",
        "cautious": "Should-I answer cautious range me dikhta hai — decision self-respect + facts par base karein.",
        "avoid": "Should-I answer avoid-impulse range me dikhta hai — pressure ya guilt se decide mat karein.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_decision": {
        "favorable": "Favorable matlab chart aage badhne ko support karta hai — daily respect + honest talk anchor rehte hain.",
        "wait": "Wait matlab timing + data abhi mixed hai — observation window decision ko sharpen karti hai.",
        "cautious": "Cautious matlab risk + reward balance hai — rush se bachna helpful rehta hai.",
        "avoid": "Avoid matlab impulse decisions se bachna zaruri — boundaries protect karti hain.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_decision": {
        "favorable": "Pros/cons list likhke partner se calm talk karein — aligned step aage badhata hai.",
        "wait": "2-4 hafte consistent actions track karein — pattern clear hone ke baad step lein.",
        "cautious": "Non-negotiables define karein — self-respect compromise na ho.",
        "avoid": "Emotional spike me text/call decisions avoid karein — cool-down window rakhein.",
    },
    "stay_or_leave": {
        "wait": "Stay vs leave list banayein — har option ka 30-day realistic outcome likhein.",
        "cautious": "Trusted friend ya journal se reality-check karein before final call.",
    },
    "second_chance": {
        "cautious": "Second chance par clear boundaries + one repeat-rule set karein.",
    },
    "leave_decision": {
        "cautious": "Exit plan practical rakhein — support system + safety pehle secure karein.",
    },
    "overall_suitability": {
        "wait": "Values, respect, effort balance — teen pillars par score dein (1-5).",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "favorable": "Decision outlook positive hai — aligned action se bond improve hota hai.",
    "wait": "Wait outlook clear hoga jab consistent behaviour 3-4 hafte observe ho jaye.",
    "cautious": "Cautious outlook improve hoga jab friction points honestly address hon.",
    "avoid": "Avoid outlook me self-protection first — change tabhi jab effort mutual ho.",
}

RDEC_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"5th\s*lord\s*strong|fifth\s*lord\s*strong|emotional\s+reopening", re.I), "Strong 5th lord / reopening stay-or-repair path ko support karta hai."),
    (re.compile(r"reconnection_yoga|reconnection", re.I), "Reconnection yoga second chance + repair ko support karta hai."),
    (re.compile(r"separation_yoga|separation", re.I), "Separation yoga leave-pressure + distance risk highlight karta hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th slow tests + delay decision ko weigh karta hai."),
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th sharp friction stay/leave choice ko complicate karta hai."),
    (re.compile(r"rahu.*7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th unpredictable twists decision direction ko affect karte hain."),
    (re.compile(r"third_person|hidden\s+ties|parallel", re.I), "Hidden ties / third-person signal trust check pehle zaruri banata hai."),
    (re.compile(r"loyalty_risk|affair", re.I), "Loyalty risk pause-and-verify stance ko strengthen karta hai."),
    (re.compile(r"jupiter.*7th|jupiter", re.I), "Jupiter growth + wise pacing decision ko support karta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase decision lean ko colour karti hai."),
]


def detect_relationship_decisions_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_relationship_decisions_angle

    q = (question or "").strip()
    angle = infer_relationship_decisions_angle(q) or "general_decision"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    intent = str(item.get("intent") or "").strip().lower()
    if bucket == "relationship_decisions" and angle == "general_decision":
        if "stay" in intent or "leave" in intent:
            angle = "stay_or_leave"
        elif "suitability" in intent or "sahi" in intent:
            angle = "overall_suitability"
        elif "second" in intent or "chance" in intent:
            angle = "second_chance"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "wait").strip().lower()
    ang = (angle or "general_decision").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_decision"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["wait"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "wait").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_decision").strip().lower()) or MEANING_TEMPLATES["general_decision"]
    return block.get(lv) or MEANING_TEMPLATES["general_decision"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "wait").strip().lower()
    ang = (angle or "general_decision").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_decision"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_decision"].get(
        lv, "Decision samajhne ke liye facts + consistent behaviour observe karna helpful rehta hai."
    )


def get_rdec_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "wait").strip().lower()) or OUTLOOK_TEMPLATES["wait"]


def rdec_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in RDEC_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me relationship-decision factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = rdec_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
