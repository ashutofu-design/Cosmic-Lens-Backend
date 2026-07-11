"""Relationship future engine — intent templates (non-timing)."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

RFUT_LEVELS: tuple[str, ...] = ("promising", "mixed", "uncertain", "weak")

VERDICT_LABELS: dict[str, str] = {
    "promising": "Promising",
    "mixed": "Mixed",
    "uncertain": "Uncertain",
    "weak": "Weak",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "promising": 78,
    "mixed": 64,
    "uncertain": 50,
    "weak": 30,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["outlook"] = _NATURAL_SEC["rfut_outlook"]

_BASE_OPENINGS: dict[str, str] = {
    "promising": "Chart ke hisaab se relationship future mostly promising range me dikhta hai — bond steady effort se deepen hota hai.",
    "mixed": "Relationship future mixed range me dikhta hai — closeness possible hai par friction points address karne padenge.",
    "uncertain": "Relationship future uncertain zone me dikhta hai — direction abhi fully clear nahi, realistic observation helpful rehti hai.",
    "weak": "Relationship future weak signal range me dikhta hai — bina honest work bond weaken ho jayega.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_future": _BASE_OPENINGS,
    "growth_outlook": {
        "promising": "Growth outlook mostly promising range me dikhta hai — bond aage badhne ki room strong hai.",
        "mixed": "Growth outlook mixed range me dikhta hai — grow possible hai par friction ko manage karna padega.",
        "uncertain": "Growth outlook uncertain zone me dikhta hai — direction abhi mixed signals deta hai.",
        "weak": "Growth outlook weak range me dikhta hai — without repair effort bond stagnate ho jayega.",
    },
    "weak_outlook": {
        "promising": "Weakness risk dominant nahi — supportive markers bond ko anchor karte hain.",
        "mixed": "Weakness vs strength mixed range me dikhta hai — dips possible hain par repair bhi.",
        "uncertain": "Weakness signals uncertain zone me dikhte hain — pattern track karna helpful rehta hai.",
        "weak": "Weakness / decline risk weak range me active dikhta hai — realism + boundaries zaruri hain.",
    },
    "long_term_stability": {
        "promising": "Long-term stability mostly promising range me dikhti hai — relationship tikne ki room strong hai.",
        "mixed": "Long-term stability mixed range me dikhti hai — ups + downs dono phases aayenge.",
        "uncertain": "Long-term stability uncertain zone me dikhti hai — big decisions abhi rush mat karein.",
        "weak": "Long-term stability weak signal range me dikhti hai — sustain effort consistently chahiye.",
    },
    "bond_direction": {
        "promising": "Bond direction mostly promising range me dikhti hai — aage closeness deepen hoti hai.",
        "mixed": "Bond direction mixed range me dikhti hai — aage grow + test dono phases aayenge.",
        "uncertain": "Bond direction uncertain zone me dikhti hai — abhi observe + communicate karna helpful rehta hai.",
        "weak": "Bond direction weak range me dikhti hai — without change pattern repeat ho jayega.",
    },
    "relationship_mature": {
        "promising": "Maturity / deepening theme mostly promising range me dikhta hai — bond adult-level grow karta hai.",
        "mixed": "Maturity theme mixed range me dikhta hai — depth possible hai par friction lessons bhi aayenge.",
        "uncertain": "Maturity outlook uncertain zone me dikhta hai — time + consistent effort decide karenge.",
        "weak": "Maturity signal weak range me dikhta hai — surface-level pull zyada active reh jayega.",
    },
    "personal_growth_impact": {
        "promising": "Relationship aapki personal growth ke liye mostly supportive range me dikhti hai.",
        "mixed": "Growth impact mixed range me dikhta hai — kuch lessons helpful, kuch drain bhi karte hain.",
        "uncertain": "Growth impact uncertain zone me dikhta hai — boundaries + self-awareness helpful rehti hai.",
        "weak": "Growth impact weak range me dikhta hai — bond mostly comfort zone se bahar push nahi karega.",
    },
    "sustain_outlook": {
        "promising": "Sustain / continue outlook mostly promising range me dikhta hai — relationship chalne ki room strong hai.",
        "mixed": "Sustain outlook mixed range me dikhta hai — continue possible hai par effort consistent hona chahiye.",
        "uncertain": "Sustain outlook uncertain zone me dikhta hai — direction observe karein before big steps.",
        "weak": "Sustain outlook weak range me dikhta hai — without repair continuation difficult reh jayega.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_future": {
        "promising": "Promising matlab long arc positive hai — daily respect + talk bond ko anchor karte hain.",
        "mixed": "Mixed matlab direction effort se decide hoti hai — patterns notice karein.",
        "uncertain": "Uncertain matlab abhi big conclusions avoid karein — data gather karein.",
        "weak": "Weak matlab realism protect karega — change possible hai par work required hai.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_future": {
        "promising": "Weekly quality time + honest talk future bond ko strong rakhte hain.",
        "mixed": "Friction points calmly address karein — repeat fights ko pattern samajhke break karein.",
        "uncertain": "Rush decisions avoid karein — 2-3 months consistent behaviour observe karein.",
        "weak": "Boundaries + repair habits set karein — hope alone direction change nahi karta.",
    },
    "growth_outlook": {
        "mixed": "Small growth rituals (shared goals, appreciation) momentum build karte hain.",
    },
    "weak_outlook": {
        "weak": "Decline signs par early action helpful rehta hai — denial se situation worsen hoti hai.",
    },
    "long_term_stability": {
        "uncertain": "Long-term vision discuss karein — values alignment check karna helpful rehta hai.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "promising": "Future outlook positive hai — steady care se bond mature ho jayega.",
    "mixed": "Mixed outlook improve ho jayega jab friction points honestly address hon.",
    "uncertain": "Uncertain outlook clear hoga jab consistent actions 4-8 weeks observe kar len.",
    "weak": "Weak outlook me realism first — change tabhi jab both sides effort equalize karein.",
}

RFUT_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"5th\s*lord\s*strong|fifth\s*lord\s*strong|emotional\s+reopening", re.I), "Strong 5th lord / reopening future closeness ko support karta hai."),
    (re.compile(r"reconnection_yoga|reconnection", re.I), "Reconnection yoga repair + emotional reopening ko support karta hai."),
    (re.compile(r"separation_yoga|separation", re.I), "Separation yoga future friction + distance risk highlight karta hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th slow growth + tests through partnership la deta hai."),
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th sharp friction spikes future bond ko test karta hai."),
    (re.compile(r"rahu.*7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th unpredictable twists future direction ko affect karte hain."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional volatility future stability ko affect karti hai."),
    (re.compile(r"jupiter.*7th|jupiter", re.I), "Jupiter faith + long-term growth support karta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase future signals ko colour karti hai."),
]


def detect_relationship_future_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_relationship_future_angle

    q = (question or "").strip()
    angle = infer_relationship_future_angle(q) or "general_future"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("relationship_future", "general_mr") and angle == "general_future":
        if re.search(r"(?ix)\b(long[\s-]*term|chalega|sustain)\b", q):
            angle = "long_term_stability"
        elif re.search(r"(?ix)\b(grow|badheg)\b", q):
            angle = "growth_outlook"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_future").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_future"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_future").strip().lower()) or MEANING_TEMPLATES["general_future"]
    return block.get(lv) or MEANING_TEMPLATES["general_future"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_future").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_future"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_future"].get(
        lv, "Future direction samajhne ke liye patterns + consistent effort observe karna helpful rehta hai."
    )


def get_rfut_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def rfut_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in RFUT_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me relationship-future factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = rfut_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
