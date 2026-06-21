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
    r"when\s+will\s+i\s+(recover|heal|get\s+better|fall\s+ill)|"
    r"recovery\s+(date|when|kab)|"
    r"health\s+(kab|when)|"
    r"muhurat\s+(operation|surgery)|"
    r"operation\s+(kab|date|when)\s*(karwau|karu)?"
    r")\b"
)

_REPRO_RX = re.compile(
    r"(?ix)\b("
    r"infertility|santaan|santan|baby|pregnan(?:cy|t)|conceive|"
    r"miscarriage|garbh|fertility|reproductive|repro\b|maa\s+banna|pita\s+banna"
    r")\b"
)

_PARENT_RX = re.compile(
    r"(?ix)\b("
    r"(papa|father|dad|mummy|mother|mom|mata|pita|mata\s+pita|"
    r"parents?)\b.{0,25}\b("
    r"health|sehat|tabiyat|bimari|beemar|bimar|ill|sick"
    r")\b|"
    r"(health|sehat|tabiyat)\b.{0,25}\b(papa|father|mother|mummy|parents?)"
    r")\b"
)

_ADDICTION_RX = re.compile(
    r"(?ix)\b("
    r"addiction|nasha|sharab|alcohol|smoking|cigarette|drugs|"
    r"substance|intoxicat"
    r")\b"
)

_ACCIDENT_RX = re.compile(
    r"(?ix)\b("
    r"accident|injury|chot|durghatna|trauma|fracture"
    r")\b"
)

_MENTAL_RX = re.compile(
    r"(?ix)\b("
    r"stress|anxiety|depression|tension|mental\s+(health|peace|stress|state)|"
    r"man\s+(ashaant|udas|thik\s+nahi|pareshan|bechain)|"
    r"mood\s+(off|swing|low|depressed)|"
    r"udaasi|chinta|ghabrahat|panic|"
    r"neend\s+nahi|insomnia|sleep\s+(problem|nahi|kharab)"
    r")\b"
)

_CHRONIC_RX = re.compile(
    r"(?ix)\b("
    r"chronic|long[\s-]?term\s+(illness|problem|bimari|issue)|"
    r"lambi\s+bimari|purani\s+bimari|"
    r"genetic\s+(disease|risk|history)|hereditary|"
    r"life[\s-]?long|hamesha\s+rehta|reh\s+jata"
    r")\b"
)

_SURGERY_TONE_RX = re.compile(
    r"(?ix)\b("
    r"surgery\s+(risk|safe|needed|required|advis|recommend)|"
    r"operation\s+(risk|safe|needed|required|zaroori|karna\s+chahiye)|"
    r"operation\s+ka\s+risk|surgery\s+ka\s+risk|"
    r"knife\s+lag|shastra[\s-]?kriya\s+(risk|safe|needed)|"
    r"hospital\s+(risk|frequent|baar\s+baar)"
    r")\b"
)

_RECOVERY_RX = re.compile(
    r"(?ix)\b("
    r"recover|recovery|healing|heal|"
    r"thik\s+(honga|hounga|ho\s+jaunga|ho\s+sakta)|"
    r"swasth\s+(honga|hounga)|"
    r"recovery\s+capacity|healing\s+capacity"
    r")\b"
)

_PREVENT_RX = re.compile(
    r"(?ix)\b("
    r"prevent|prevention|avoid|bachna|bachne|bachao|"
    r"future\s+(health\s+)?risk|health\s+risk|"
    r"aage\s+(chal\s+ke|jaake)|aane\s+wale|"
    r"tendency|tendencies|kya\s+kya\s+(bimari|issues?)|"
    r"risk\s+(hai|hoga|zone)|khatra|dikkat\s+zone|vulnerable"
    r")\b"
)

_VITALITY_RX = re.compile(
    r"(?ix)\b("
    r"vitality|immunity|stamina|energy|constitution|"
    r"sehat\s+kaisi|meri\s+sehat|swasthya\s+kaisa|tabiyat\s+kaisi|"
    r"overall\s+health|general\s+health|health\s+strong|health\s+weak|"
    r"body\s+strong|sharir\s+strong|kamzor\s+hu|strong\s+hu"
    r")\b"
)


def is_health_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if detect_hard_guard(q):
        return True
    if _TIMING_RX.search(q) and not detect_hard_guard(q):
        return False
    if detect_health_archetype(q):
        return True
    return bool(is_health_question(q))


def detect_health_archetype(question: str) -> str | None:
    q = (question or "").strip()
    if not q:
        return None

    hard = detect_hard_guard(q)
    if hard:
        return _HARD_GUARD_ARCH.get(hard)

    if _REPRO_RX.search(q):
        return "reproductive_support"
    if _PARENT_RX.search(q):
        return "parent_health"
    if _ADDICTION_RX.search(q):
        return "addiction_support"
    if _ACCIDENT_RX.search(q):
        return "accident_risk"
    if _MENTAL_RX.search(q):
        return "mental_stress"
    if _CHRONIC_RX.search(q):
        return "chronic_tendency"
    if _SURGERY_TONE_RX.search(q):
        return "surgery_risk_tone"
    if _RECOVERY_RX.search(q):
        return "recovery_capacity"
    if _PREVENT_RX.search(q):
        return "preventive_risk"
    if _VITALITY_RX.search(q):
        return "overall_vitality"
    return None
