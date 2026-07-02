"""Health topic registry — scope keywords + archetype detection."""

from __future__ import annotations

import re

from health_focus_routing import detect_hard_guard, is_health_question

HEALTH_ARCHETYPES = frozenset({
    "overall_vitality",
    "chronic_tendency",
    "mental_stress",
    "surgery_risk_tone",
    "preventive_risk",
    "recovery_capacity",
    "accident_risk",
    "parent_health",
    "addiction_support",
    "reproductive_support",
    "digestive_health",
    "cardio_health",
    "nervous_health",
    "musculoskeletal_health",
    "skin_health",
    "endocrine_health",
    "respiratory_health",
    "immune_health",
    "refuse_diagnosis",
    "refuse_death",
    "refuse_cure_guarantee",
    "refuse_timing_decline",
    "refuse_timing_recovery",
    "refuse_surgery_muhurat",
    "crisis_redirect",
    "general_health",
})

_HARD_GUARD_ARCH = {
    "CRISIS_REDIRECT": "crisis_redirect",
    "REFUSE_DEATH": "refuse_death",
    "REFUSE_DIAGNOSIS": "refuse_diagnosis",
    "REFUSE_TIMING_RECOVERY": "refuse_timing_recovery",
    "REFUSE_TIMING_DECLINE": "refuse_timing_decline",
    "REFUSE_SURGERY_MUHURAT": "refuse_surgery_muhurat",
    "REFUSE_CURE_GUARANTEE": "refuse_cure_guarantee",
}

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab\s+(thik|theek|swasth|healthy|beemar|bimar|recover)|"
    r"when\s+will\s+i\s+(recover|heal|get\s+better|fall\s+ill|get\s+sick)|"
    r"recovery\s+(date|when|kab)|"
    r"health\s+(kab|when)|"
    r"muhurat\s+(operation|surgery)|"
    r"operation\s+(kab|date|when)\s*(karwau|karu)?"
    r")\b"
)

_YEAR_FORECAST_RX = re.compile(
    r"(?ix)(20\d{2}|\d{4}).{0,30}(health|sehat|swasth|tabiyat)|"
    r"(health|sehat|swasth).{0,30}(20\d{2}|\d{4})"
)

_GENERAL_RX = re.compile(
    r"(?ix)\b("
    r"health\s+picture|health\s+summary|health\s+side|"
    r"body\s+health\s+summary|meri\s+health\s+overall|health\s+overall|"
    r"overall\s+health\s+(picture|summary|side|reading)|"
    r"स्वास्थ्य\s+की\s+स्थिति"
    r")\b"
)

_REPRO_RX = re.compile(
    r"(?ix)(infertility|santaan|santan|baby|pregnan(?:cy|t)|conceive|"
    r"miscarriage|garbh|fertility|reproductive|repro\b|maa\s+banna|pita\s+banna|"
    r"गर्भधारण\s+की\s+संभावना|गर्भ)"
)

_HEALTH_MEDICAL_RX = re.compile(
    r"(?ix)\b("
    r"sehat|health|bimari|beemar|bimar|doctor|diagnos|treatment|medicine|"
    r"hospital|symptom|disease|illness|medical|hormon|pcod|pcos|"
    r"tube\s*block|uterus|ovary|sperm\s*count|test\s+result|complication"
    r")\b"
)

_PARENT_RX = re.compile(
    r"(?ix)((papa|father|dad|mummy|mother|mom|mata|pita|mata\s+pita|"
    r"parents?)\b.{0,25}\b(health|sehat|tabiyat|bimari|beemar|bimar|ill|sick)|"
    r"(health|sehat|tabiyat)\b.{0,25}\b(papa|father|mother|mummy|parents?)|"
    r"माता-पिता\s+की\s+सेहत|माता\s+पिता)"
)

_ADDICTION_RX = re.compile(
    r"(?ix)(addiction|nasha|sharab|alcohol|smoking|cigarette|drugs|"
    r"substance|intoxicat|नशे\s+की\s+लत|नशा)"
)

_ACCIDENT_RX = re.compile(
    r"(?ix)(accident|injury|chot|durghatna|trauma|fracture|"
    r"दुर्घटना\s+का\s+खतरा|दुर्घटना)"
)

_MENTAL_RX = re.compile(
    r"(?ix)(stress|anxiety|depression|tension|mental\s+(health|peace|stress|state)|"
    r"man\s+(ashaant|udas|thik\s+nahi|pareshan|bechain)|"
    r"mood\s+(off|swing|low|depressed)|"
    r"udaasi|chinta|ghabrahat|panic|burnout|exhaustion|emotional\s+instability|"
    r"neend\s+nahi|insomnia|sleep\s+(problem|nahi|kharab)|"
    r"मानसिक\s+तनाव|मानसिक\s+स्वास्थ्य|नींद\s+की\s+समस्या|चिंता)"
)

_CHRONIC_RX = re.compile(
    r"(?ix)(chronic|long[\s-]?term\s+(illness|problem|bimari|issue)|"
    r"lambi\s+bimari|purani\s+bimari|"
    r"genetic\s+(disease|risk|history)|hereditary|"
    r"life[\s-]?long|hamesha\s+rehta|reh\s+jata|"
    r"लंबी\s+बीमारी\s+की\s+प्रवृत्ति|दीर्घकालिक)"
)

_SURGERY_TONE_RX = re.compile(
    r"(?ix)(?:\b("
    r"surgery\s+(risk|risky|safe|needed|required|advis|recommend)|"
    r"operation\s+(risk|risky|safe|needed|required|zaroori|karna\s+chahiye)|"
    r"operation\s+ka\s+risk|surgery\s+ka\s+risk|"
    r"shastra[\s-]?kriya\s+(ka\s+)?risk|"
    r"knife\s+lag|shastra[\s-]?kriya|"
    r"hospital\s+(risk|frequent|baar\s+baar)"
    r")\b|"
    r"ऑपरेशन\s+का\s+जोखिम|"
    r"शल्य\s+चिकित्सा\s+का\s+जोखिम)"
)

_RECOVERY_RX = re.compile(
    r"(?ix)(?:\b("
    r"recover|recovery|healing|heal|"
    r"recovery\s+resistance|recovery\s+capacity|healing\s+capacity|"
    r"bounce\s+back|bounce\s+back\s+ability|"
    r"swasth\s+hone\s+ki\s+capacity|"
    r"thik\s+(honga|hounga|ho\s+jaunga|ho\s+sakta)|"
    r"swasth\s+(honga|hounga)"
    r")\b|"
    r"ठीक\s+होने\s+की\s+क्षमता)"
)

_PREVENT_RX = re.compile(
    r"(?ix)(prevent|prevention|avoid|bachna|bachne|bachao|"
    r"future\s+(health\s+)?risk|health\s+risk|"
    r"aage\s+(chal\s+ke|jaake)|aane\s+wale|"
    r"tendency|tendencies|kya\s+kya\s+(bimari|issues?)|"
    r"prone\s+to|issues?\s+am\s+i\s+prone|"
    r"risk\s+(hai|hoga|zone)|khatra|dikkat\s+zone|vulnerable|"
    r"भविष्य\s+में\s+स्वास्थ्य\s+जोखिम)"
)

_ISSUE_NOW_RX = re.compile(
    r"(?ix)(kya\s+kya\s+(?:health\s+|sehat\s+|tabiyat\s+)?(?:issue|problem|dikkat|bimari)|"
    r"(?:health|sehat|tabiyat)\s+(?:issue|problem|dikkat)\s+ho\s+raha|"
    r"(?:issue|problem|dikkat|bimari)\s+ho\s+rahi?|"
    r"ho\s+raha\s+hai.*(?:health|issue|dikkat|tabiyat))"
)

_VITALITY_RX = re.compile(
    r"(?ix)\b("
    r"vitality|immunity|stamina|energy|constitution|"
    r"physically\s+strong|physical\s+strength|"
    r"sehat\s+kaisi|health\s+kaisi|meri\s+sehat|meri\s+health|swasthya\s+kaisa|tabiyat\s+kaisi|"
    r"tabiyat\s+(strong|weak|kharab|thik)|meri\s+tabiyat|"
    r"overall\s+health|health\s+strong|health\s+weak|"
    r"body\s+strong|sharir\s+strong|kamzor\s+hu|strong\s+hu|"
    r"क्या\s+मेरी\s+सेहत|मेरी\s+ऊर्जा|ऊर्जा\s+और\s+शरीर"
    r")\b"
)

_CAREER_PRIMARY_RX = re.compile(
    r"(?ix)(naukri|job|promotion|salary|boss|office|kaam|career|colleague|workplace)"
)
_FINANCE_PRIMARY_RX = re.compile(
    r"(?ix)(paisa|money|fd\b|loan|saving|savings|insurance|bachat|debt|finance|"
    r"wealth|expense|bill|emi|karz|udhar)"
)
_HEALTH_BODY_RX = re.compile(
    r"(?ix)(health|sehat|tabiyat|swasth|swasthya|bimari|beemar|bimar|body|sharir|"
    r"hospital|doctor|pain|dard|vitality|immune|digest|heart|mental|stress.*health|"
    r"health.*stress|health.*kharab|kharab.*health)"
)

# "dil se pyaar" = emotional heart — NOT cardio / 4th-house health
_LOVE_EMOTIONAL_RX = re.compile(
    r"(?ix)\b(pyaar|pyar|prem|mohabbat|ishq|love|pasand|rishta|partner|crush)\b"
)
_LOVE_DIL_IDIOM_RX = re.compile(
    r"(?ix)\b("
    r"dil\s+se|dil\s+me|dil\s+ki|dil\s+lag|from\s+(the\s+)?heart|wholehearted|"
    r"jisse\s+pyaar|pyaar\s+karta|pyaar\s+karti|love\s+her|love\s+him"
    r")\b"
)
_LOVE_RECIPROCITY_RX = re.compile(
    r"(?ix)\b("
    r"kya\s+wo\s+bhi|does\s+(she|he|they)\s+love|love\s+me\s+back|"
    r"utna\s+hi\s+pyaar|jitna\s+main|reciproc|mutual\s+love"
    r")\b"
)


def is_love_emotional_dil_question(question: str) -> bool:
    """Romantic 'dil' idiom — must not route to cardio_health."""
    q = (question or "").strip()
    if not q:
        return False
    if _LOVE_RECIPROCITY_RX.search(q) and _LOVE_EMOTIONAL_RX.search(q):
        return True
    if _LOVE_DIL_IDIOM_RX.search(q) and _LOVE_EMOTIONAL_RX.search(q):
        return True
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        if is_marriage_relationship_static_question(q) and _LOVE_DIL_IDIOM_RX.search(q):
            return True
    except Exception:
        pass
    return False


def is_present_health_issue_question(question: str) -> bool:
    """Present-tense 'what issues am I having' — static health, NOT timing."""
    return bool(_ISSUE_NOW_RX.search((question or "").strip()))


def _has_real_health_intent(q: str) -> bool:
    """True when the user wants a body/health chart read — not incidental 'health'."""
    if re.search(
        r"(?ix)(tabiyat|sehat|swasth|swasthya|bimari|beemar|bimar|body|sharir|"
        r"mental|stress|kharab|pain|dard|vitality|immune|hospital|doctor|"
        r"digest|heart|pain|accident|surgery|recovery|immunity|chronic|anxiety|"
        r"depression|insomnia|addiction|fertility|pregnanc)",
        q,
    ):
        return True
    if re.search(
        r"(?ix)(meri|my|overall|chart).{0,12}\bhealth\b|"
        r"\bhealth\s+(kaisi|strong|weak|picture|summary|risk|issue|side|zone|tendency)",
        q,
    ):
        return True
    return False


def _is_cross_domain_non_health(q: str) -> bool:
    """Career/finance questions that mention health only incidentally."""
    try:
        from ask_career.classifier import is_career_static_question
        from ask_finance.classifier import is_finance_static_question

        car = is_career_static_question(q)
        fin = is_finance_static_question(q)
    except Exception:
        car = False
        fin = False

    if _CAREER_PRIMARY_RX.search(q) and not _has_real_health_intent(q):
        return True
    if fin and _FINANCE_PRIMARY_RX.search(q) and not _has_real_health_intent(q):
        return True
    try:
        from ask_vehicle.timing_registry import is_vehicle_timing_question  # type: ignore

        if is_vehicle_timing_question(q):
            return True
    except Exception:
        pass
    try:
        from ask_vehicle.vehicle_registry import is_vehicle_static_question  # type: ignore

        if is_vehicle_static_question(q):
            return True
    except Exception:
        pass
    if re.search(
        r"(?ix)(health\s+ke\s+liye|medical\s+expense|hospital\s+bill|health\s+insurance|"
        r"insurance\s+me\s+paisa|fd\b|bachat|saving|loan|debt|salary|promotion|naukri)",
        q,
    ) and not _has_real_health_intent(q):
        return True
    return False


def is_health_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    try:
        from chart_fact_answer import _detect_divisional

        if _detect_divisional(q):
            return False
    except Exception:
        pass
    try:
        from chart_fact_answer import is_domain_life_area_interpretation_question

        if is_domain_life_area_interpretation_question(q):
            return False
    except Exception:
        pass
    try:
        from ask_intent_fidelity import is_partner_relationship_question

        if is_partner_relationship_question(q):
            return False
    except Exception:
        pass
    if is_love_emotional_dil_question(q):
        return False
    try:
        from ask_children.children_registry import is_children_static_question

        if is_children_static_question(q) and not (
            _REPRO_RX.search(q) and re.search(r"(?ix)\b(chart|kundli|health|kaisi)\b", q)
        ):
            return False
    except Exception:
        pass
    try:
        from health_focus_routing import _ABSOLUTE_NON_HEALTH_RX

        if _ABSOLUTE_NON_HEALTH_RX.search(q):
            return False
    except Exception:
        pass
    if is_present_health_issue_question(q):
        return True
    try:
        from ask_health.timing_registry import is_health_timing_question  # type: ignore

        if is_health_timing_question(q):
            return False
    except Exception:
        pass
    if detect_hard_guard(q):
        return True
    if _is_cross_domain_non_health(q):
        return False
    if _YEAR_FORECAST_RX.search(q) and not detect_hard_guard(q):
        return False
    if _TIMING_RX.search(q) and not detect_hard_guard(q):
        return False
    if detect_health_archetype(q):
        return True
    return bool(is_health_question(q))


def detect_health_archetype(question: str) -> str | None:
    q = (question or "").strip()
    if not q:
        return None
    try:
        from chart_fact_answer import is_domain_life_area_interpretation_question

        if is_domain_life_area_interpretation_question(q):
            return None
    except Exception:
        pass
    try:
        from ask_intent_fidelity import is_partner_relationship_question

        if is_partner_relationship_question(q):
            return None
    except Exception:
        pass
    if is_love_emotional_dil_question(q):
        return None

    hard = detect_hard_guard(q)
    if hard:
        return _HARD_GUARD_ARCH.get(hard)

    if _REPRO_RX.search(q):
        try:
            from ask_children.children_registry import is_children_static_question

            if is_children_static_question(q):
                return None
        except Exception:
            pass
        return "reproductive_support"
    if _HEALTH_MEDICAL_RX.search(q) and re.search(
        r"(?ix)\b(sperm|uterus|hormon|complication|diagnosis|test\s+result|medicine|treatment|hospital)\b",
        q,
    ) and re.search(
        r"(?ix)\b(pregnan|fertility|infertil|garbh|conceive|santan|reproductive|sperm|uterus)\b",
        q,
    ):
        return "reproductive_support"
    if _PARENT_RX.search(q):
        return "parent_health"
    if _ADDICTION_RX.search(q):
        return "addiction_support"
    if _ACCIDENT_RX.search(q):
        return "accident_risk"
    if _RECOVERY_RX.search(q):
        return "recovery_capacity"
    # Body-system subdomains (pet/heart/breath etc.) before generic mental/chronic
    try:
        from .engines.system_health import detect_system_archetype

        sys_arch = detect_system_archetype(q)
        if sys_arch:
            return sys_arch
    except Exception:
        pass
    if _MENTAL_RX.search(q):
        return "mental_stress"
    if _ISSUE_NOW_RX.search(q):
        return "general_health"
    if _CHRONIC_RX.search(q):
        return "chronic_tendency"
    if _SURGERY_TONE_RX.search(q):
        return "surgery_risk_tone"
    if _PREVENT_RX.search(q):
        return "preventive_risk"
    if _GENERAL_RX.search(q):
        return "general_health"
    if _VITALITY_RX.search(q):
        return "overall_vitality"
    return None
