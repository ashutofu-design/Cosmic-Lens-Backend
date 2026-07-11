"""Chemistry / attraction engine — intent templates."""
from __future__ import annotations

import re
from typing import Any

CHEM_LEVELS: tuple[str, ...] = ("strong", "moderate", "uneven", "low")

VERDICT_LABELS: dict[str, str] = {
    "strong": "Strong",
    "moderate": "Moderate",
    "uneven": "Uneven",
    "low": "Low",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "strong": 78,
    "moderate": 64,
    "uneven": 50,
    "low": 32,
}

USER_SECTION = {
    "why_verdict": "Kyun ye verdict aaya:",
    "positive": "Is verdict ko support karne wale mukhya sanket:",
    "challenges": "Dhyan dene layak challenges:",
    "meaning": "Iska practical matlab:",
    "outlook": "Chemistry outlook:",
    "focus": "Aapko kis baat par dhyan dena chahiye:",
}

_BASE_OPENINGS: dict[str, str] = {
    "strong": "Chart ke hisaab se chemistry / attraction mostly strong range me dikhti hai — spark visible + pull active reh sakti hai.",
    "moderate": "Chemistry / attraction moderate range me dikhti hai — comfort ke saath spark grow karti hai.",
    "uneven": "Chemistry uneven zone me dikhti hai — pull kabhi strong kabhi weak fluctuate karegi.",
    "low": "Chemistry / attraction low range me dikhti hai — emotional bond comfort se zyada matter karega.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_chemistry": _BASE_OPENINGS,
    "dyad_chemistry": {
        "strong": "Dono ke beech chemistry mostly strong range me dikhti hai — mutual spark active reh sakti hai.",
        "moderate": "Dono ke beech chemistry moderate range me dikhti hai — comfort build hone par spark deepen hoti hai.",
        "uneven": "Dono ke beech chemistry uneven zone me dikhti hai — pull fluctuate karegi.",
        "low": "Dono ke beech chemistry low range me dikhti hai — bond comfort + effort se build hoga.",
    },
    "physical_attraction": {
        "strong": "Physical attraction / pull mostly strong range me dikhti hai — body-level spark active reh sakti hai.",
        "moderate": "Physical attraction moderate range me dikhti hai — comfort ke saath physical pull grow karti hai.",
        "uneven": "Physical attraction uneven zone me dikhti hai — intensity up-down fluctuate karegi.",
        "low": "Physical attraction low range me dikhti hai — emotional closeness zyada driver ban sakti hai.",
    },
    "passion_intensity": {
        "strong": "Passion / intensity mostly strong range me dikhti hai — intense pull phases active reh sakte hain.",
        "moderate": "Passion moderate range me dikhti hai — intensity steady grow karti hai.",
        "uneven": "Passion uneven zone me dikhti hai — intense phases ke baad cool-down cycles aayenge.",
        "low": "Passion / intensity low range me dikhti hai — calm bond comfort se drive hoga.",
    },
    "romance_spark": {
        "strong": "Romance + spark mostly strong range me dikhti hai — romantic pull active reh sakti hai.",
        "moderate": "Romance moderate range me dikhti hai — small gestures se spark maintain hoti hai.",
        "uneven": "Romance uneven zone me dikhti hai — romantic phases fluctuate karenge.",
        "low": "Romance / spark low range me dikhti hai — routine se conscious effort chahiye.",
    },
    "spark_strength": {
        "strong": "Spark / chemistry strength mostly strong range me dikhti hai — visible mutual pull active hai.",
        "moderate": "Spark strength moderate range me dikhti hai — grow karne ki room hai.",
        "uneven": "Spark strength uneven zone me dikhti hai — strong moments ke baad dip possible hai.",
        "low": "Spark strength low range me dikhti hai — pull weak reh jayegi bina effort ke.",
    },
    "native_attraction": {
        "strong": "Aapki native attraction pattern mostly strong range me dikhti hai — pull naturally active rehti hai.",
        "moderate": "Native attraction moderate range me dikhti hai — right partner par spark deepen hoti hai.",
        "uneven": "Native attraction uneven zone me dikhti hai — pull situation par depend karegi.",
        "low": "Native attraction low range me dikhti hai — emotional depth comfort se zyada matter karegi.",
    },
    "attraction_level": {
        "strong": "Attraction level mostly strong range me dikhta hai — pull consistently active reh sakti hai.",
        "moderate": "Attraction level moderate range me dikhta hai — steady build-up possible hai.",
        "uneven": "Attraction level uneven zone me dikhta hai — intensity fluctuate karegi.",
        "low": "Attraction level low range me dikhta hai — bond effort se deepen hoga.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_chemistry": {
        "strong": "Strong matlab spark + pull dono active range me hain — chemistry visible rehti hai.",
        "moderate": "Moderate matlab attraction grow karti hai — instant fireworks zaruri nahi.",
        "uneven": "Uneven matlab pull stable nahi — highs + lows dono expect karein.",
        "low": "Low matlab physical spark kam hai — emotional bond zyada anchor ban sakta hai.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_chemistry": {
        "strong": "Spark maintain karne ke liye quality time + playful energy helpful rehti hai.",
        "moderate": "Comfort build karein — small romantic gestures spark deepen karte hain.",
        "uneven": "Dip phases par overreact mat karein — pattern track karna helpful rehta hai.",
        "low": "Emotional closeness + shared activities se bond deepen karein — rush force mat karein.",
    },
    "dyad_chemistry": {
        "uneven": "Dono ke beech pull fluctuate ho to direct baat + shared experiences helpful rehti hain.",
    },
    "physical_attraction": {
        "low": "Physical pull kam ho to emotional safety + affection gestures se closeness build karein.",
    },
    "passion_intensity": {
        "uneven": "Intense phases ke baad rest + affection balance rakhein — burnout avoid karein.",
    },
    "romance_spark": {
        "low": "Routine me small romantic surprises spark revive karte hain.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "strong": "Chemistry outlook positive hai — spark active rehne ki room strong dikhti hai.",
    "moderate": "Moderate outlook steady grow karega jab comfort + effort dono active rahein.",
    "uneven": "Uneven outlook me pull fluctuate karegi — pattern track karna helpful rehta hai.",
    "low": "Low outlook me emotional bond effort se deepen ho jayega — chemistry alone driver nahi rehni chahiye.",
}

CHEM_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"venus.*mars|venus_mars|venus-mars", re.I), "Venus-Mars link passion + physical spark ko strong karta hai."),
    (re.compile(r"venus.*afflict|venus_afflict|venus.*dusthana|venus.*debil", re.I), "Afflicted Venus attraction pull uneven ya weak kar sakti hai."),
    (re.compile(r"5th\s*lord\s*strong|fifth\s*lord\s*strong", re.I), "Strong 5th lord romantic reopening + playful chemistry support karta hai."),
    (re.compile(r"5th\s*lord\s*weak|fifth\s*lord\s*weak", re.I), "Weak 5th lord spark / romantic pull kam dikha sakta hai."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional warmth fluctuate kar sakti hai — pull uneven ban sakti hai."),
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th par passion spikes + friction dono chemistry ko colour karte hain."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th slow / reserved romantic tone la sakta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase chemistry signals ko colour karti hai."),
]


def detect_chemistry_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_chemistry_angle

    q = (question or "").strip()
    angle = infer_chemistry_angle(q) or "general_chemistry"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("chemistry", "attraction_chemistry", "physical_intimacy") and angle == "general_chemistry":
        if re.search(r"(?ix)\b(physical|sharirik)\b", q):
            angle = "physical_attraction"
        elif is_dyadic_couple_question(q):
            angle = "dyad_chemistry"
    return angle


def is_dyadic_couple_question(question: str) -> bool:
    from ask_intent_fidelity import is_dyadic_couple_question as _dyad

    return _dyad(question)


def get_opening(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_chemistry").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_chemistry"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["moderate"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_chemistry").strip().lower()) or MEANING_TEMPLATES["general_chemistry"]
    return block.get(lv) or MEANING_TEMPLATES["general_chemistry"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_chemistry").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_chemistry"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_chemistry"].get(
        lv, "Chemistry samajhne ke liye pull pattern + consistent effort observe karna helpful rehta hai."
    )


def get_chem_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "moderate").strip().lower()) or OUTLOOK_TEMPLATES["moderate"]


def chem_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in CHEM_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me chemistry-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = chem_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
