"""Family approval engine — intent templates."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

FAMILY_LEVELS: tuple[str, ...] = ("supportive", "mixed", "resistant", "unlikely")

VERDICT_LABELS: dict[str, str] = {
    "supportive": "Supportive",
    "mixed": "Mixed",
    "resistant": "Resistant",
    "unlikely": "Unlikely",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "supportive": 78,
    "mixed": 62,
    "resistant": 44,
    "unlikely": 28,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["outlook"] = "Family approval outlook —"

_BASE_OPENINGS: dict[str, str] = {
    "supportive": "Chart ke hisaab se family approval mostly supportive dikhti hai — respectful steady approach se elders soften ho sakte hain.",
    "mixed": "Family approval mixed signals dikhati hai — support aur resistance dono present hain.",
    "resistant": "Family approval resistant zone me dikhti hai — social/family friction active hai, diplomacy zaruri hai.",
    "unlikely": "Family approval unlikely-soon pattern active hai — expectation clash strong dikhta hai, realistic planning zaruri hai.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_approval": _BASE_OPENINGS,
    "parents_approval": {
        "supportive": "Parents approval mostly supportive range me dikhti hai — respectful dialogue se raazi hona possible hai.",
        "mixed": "Parents approval mixed signals dete hain — initial hesitation ke baad soften ho jayega.",
        "resistant": "Parents approval resistant zone me dikhti hai — tradition/expectation friction active hai.",
        "unlikely": "Parents approval unlikely-soon pattern dikhta hai — strong clash abhi dominant dikhta hai.",
    },
    "inter_caste": {
        "supportive": "Inter-caste theme me family support relatively better dikhti hai — steady respectful proof helpful rahega.",
        "mixed": "Inter-caste marriage me mixed family signals hain — elders ko time + dignity se approach chahiye.",
        "resistant": "Inter-caste theme resistant zone me hai — social tradition friction zyada active dikhti hai.",
        "unlikely": "Inter-caste approval unlikely-soon pattern dikhta hai — expectation gap abhi wide dikhta hai.",
    },
    "inter_religion": {
        "supportive": "Inter-religion theme me supportive elders signals relatively better dikhte hain.",
        "mixed": "Inter-religion marriage me mixed approval — tradition vs choice tension manage karni hogi.",
        "resistant": "Inter-religion theme resistant zone me hai — value/tradition clash friction badha sakta hai.",
        "unlikely": "Inter-religion approval unlikely-soon dikhti hai — family expectation clash strong hai.",
    },
    "court_marriage": {
        "supportive": "Court marriage theme me family eventually supportive ho sakti dikhti hai — formal proof + dialogue matter karega.",
        "mixed": "Court marriage me mixed family reaction — independent choice par initial friction possible hai.",
        "resistant": "Court marriage theme resistant zone me hai — ritual/tradition gap friction create karega.",
        "unlikely": "Court marriage approval unlikely-soon pattern — elders ko formal union accept karne me time lagega.",
    },
    "family_involvement": {
        "supportive": "Family involvement mostly balanced/supportive dikhti hai — elders engaged par respectful rehenge.",
        "mixed": "Family involvement mixed level dikhta hai — guidance ke saath interference bhi possible hai.",
        "resistant": "Family involvement resistant tone me dikhta hai — over-control friction create kar sakta hai.",
        "unlikely": "Family involvement unlikely-as-support pattern — elders distant ya strongly opposing dikhte hain.",
    },
    "societal_recognition": {
        "supportive": "Societal recognition relatively supportive range me dikhti hai — family + society accept gradually possible.",
        "mixed": "Social recognition mixed signals deti hai — acceptance time le sakti hai.",
        "resistant": "Societal recognition resistant zone me hai — social stigma/friction active dikhti hai.",
        "unlikely": "Social recognition unlikely-soon pattern — public acceptance abhi weak dikhti hai.",
    },
    "in_laws_approval": {
        "supportive": "In-laws / saas-sasur approval mostly supportive range me dikhti hai.",
        "mixed": "In-laws approval mixed hai — initial testing ke baad rapport build ho jayega.",
        "resistant": "In-laws approval resistant zone me dikhti hai — traditional expectations friction la sakti hain.",
        "unlikely": "In-laws approval unlikely-soon pattern — strong resistance initially dikhta hai.",
    },
    "family_resistance": {
        "supportive": "Strong family resistance ke dominant signals nahi — friction mostly manageable dikhti hai.",
        "mixed": "Family resistance mixed level par hai — oppose + soften dono phases possible hain.",
        "resistant": "Family resistance resistant zone me active hai — opposition theme strong dikhta hai.",
        "unlikely": "Family resistance unlikely-to-soften-soon pattern — clash abhi intense dikhta hai.",
    },
    "family_pressure": {
        "supportive": "Heavy family pressure ke strong signals dominant nahi — autonomy relatively better dikhti hai.",
        "mixed": "Family pressure mixed hai — guidance ke saath expectation weight bhi feel ho jayega.",
        "resistant": "Family pressure resistant zone me hai — forceful expectations bond ko test karenge.",
        "unlikely": "Family pressure unlikely-to-ease pattern — controlling tone zyada active dikhta hai.",
    },
    "accept_partner": {
        "supportive": "Partner / pasand accept karne ke supportive signals zyada dikhte hain.",
        "mixed": "Partner accept karne me mixed family reaction — time + proof se improve ho jayega.",
        "resistant": "Partner accept karne me resistant zone active hai — choice vs tradition clash dikhta hai.",
        "unlikely": "Partner accept unlikely-soon pattern — elders ki strong objection initially dikhti hai.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_approval": {
        "supportive": "Supportive matlab elders eventually soften ho sakte hain — respect + steady proof key hai.",
        "mixed": "Mixed matlab outcome approach par depend karega — rushed confrontation risky hai.",
        "resistant": "Resistant matlab diplomacy + boundaries dono zaruri hain.",
        "unlikely": "Unlikely-soon matlab immediate yes kam probable hai — long-term strategy realistic hai.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_approval": {
        "supportive": "Respectful family dialogue + steady proof of match helpful rahega.",
        "mixed": "Elders ko time dein — facts + calm tone se resistance soften ho sakti hai.",
        "resistant": "Confrontation avoid karein — mediator ya senior trusted relative helpful rehta hai.",
        "unlikely": "Realistic timeline rakhein — forced decision se friction aur badh sakti hai.",
    },
    "inter_caste": {
        "mixed": "Inter-caste case me dignity + family honour dono address karein — blame tone avoid karein.",
        "resistant": "Elders ke core concern samajh kar step-by-step dialogue approach rakhein.",
    },
    "accept_partner": {
        "mixed": "Partner ko family ke saath gradual respectful introduction helpful rehta hai.",
        "resistant": "Choice defend karte waqt calm examples + stability proof share karein.",
    },
    "parents_approval": {
        "resistant": "Parents ke concern ko sunna + practical reassurance dono matter karte hain.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "supportive": "Approval outlook relatively open hai — respectful approach se elders align ho sakte hain.",
    "mixed": "Mixed outlook manage ho jayega jab dialogue steady aur proof consistent rahe.",
    "resistant": "Resistant outlook improve ho jayega par time + diplomacy dono chahiye.",
    "unlikely": "Unlikely-soon outlook me realistic expectation rakhein — change possible hai par delay expected hai.",
}

FAMILY_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"rahu.*7th|rahu_on_7th|nodes?\s+on\s+7th", re.I), "Rahu on relationship axis unconventional match ko amplify kar sakta hai."),
    (re.compile(r"jupiter.*support|jupiter_support", re.I), "Jupiter support elders soften hone me help kar sakta hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th tradition/authority friction la sakta hai."),
    (re.compile(r"2nd|9th|family\s+axis", re.I), "Family/dharma axis elders ki involvement level colour karti hai."),
    (re.compile(r"inter[\s-]?caste|caste", re.I), "Inter-caste theme social tradition friction ko highlight karta hai."),
    (re.compile(r"inter[\s-]?religion|religion", re.I), "Inter-religion theme value-gap friction la sakta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase family-approval signals ko colour karti hai."),
]


def detect_family_approval_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_family_approval_angle

    q = (question or "").strip()
    angle = infer_family_approval_angle(q) or "general_approval"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("family_approval", "family_social_acceptance") and angle == "general_approval":
        if re.search(r"(?ix)\b(inter[\s-]?caste|intercaste|jaati)\b", q):
            angle = "inter_caste"
        elif re.search(r"(?ix)\b(parents?|maanenge|manenge)\b", q):
            angle = "parents_approval"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_approval").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_approval"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_approval").strip().lower()) or MEANING_TEMPLATES["general_approval"]
    return block.get(lv) or MEANING_TEMPLATES["general_approval"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_approval").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_approval"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_approval"].get(
        lv, "Family stance samajhne ke liye steady respectful approach helpful rehta hai."
    )


def get_family_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def family_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in FAMILY_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me family-approval related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = family_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out
