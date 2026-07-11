"""Property timing routing — ghar/registry/possession WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

try:
    from property_static.property_routing import is_timing_property_question
except Exception:
    def is_timing_property_question(q: str) -> bool:  # type: ignore[misc]
        return False

_POSSESSION_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"possession|registry|griha[\s-]?pravesh|handover|chaabi|chabi|"
    r"construction|banega|banegi|loan|sanction|grahak|bik|bech|sell|"
    r"vivaad|faisla|hissa|pustaini|ancestral|zameen|makaan|ghar|"
    r"property|kharid|kharidunga|kharidungi|buy|purchase|flat|plot|"
    r"dhoka|chehra|compromise|dushman|parivaar|mansik\s+tanaav|"
    r"jhagda|suljha|vivaad|kabza|encroachment|stay\s+order"
    r")\b",
)

_CAREER_MUHURAT_DEFER_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|promotion|tarakki|salary|transfer|posting|career|"
    r"interview|joining|govt|sarkari|resignation|increment|hike|"
    r"recruitment|railway|police|defence|ibps|role|onboarding|offer"
    r")\b",
)

_EDU_LOAN_BLOCK_PROPERTY_RX = re.compile(
    r"(?ix)\b(education\s+loan|student\s+loan)\b",
)

_TIMING_RX = re.compile(
    r"(?ix)\b(kab|kab\s+tak|when|kis\s+(saal|year|mahine|month)|muhurat|timing|"
    r"banega|banegi|milega|milegi|hoga|hogi|pahuchegi|sanction|sign\s+hoga|"
    r"liquid|active|lagenge|rukhega|faisla|poora\s+hoga|paunga|paungi)\b",
)


def llm_says_property_timing(llm_intent: Optional[dict] = None) -> bool:
    """True when LLM/admin routing says property domain + timing."""
    if not isinstance(llm_intent, dict):
        return False
    dom = str(
        llm_intent.get("domain")
        or llm_intent.get("routed_domain")
        or ""
    ).strip().lower()
    if dom != "property":
        return False
    return bool(
        llm_intent.get("is_timing") or llm_intent.get("routed_timing")
    )


_VEHICLE_DEFER_RX = re.compile(
    r"(?ix)\b("
    r"car|cars|bike|bikes|scooter|scooty|motorcycle|motorbike|"
    r"vehicle|vehicles|gaadi|gadi|suv|sedan|hatchback|two[\s-]?wheeler|four[\s-]?wheeler"
    r")\b",
)


def is_property_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if llm_says_property_timing(llm_intent):
        return True
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "property" and llm_intent.get("is_timing"):
            return True
    if _CAREER_MUHURAT_DEFER_RX.search(q) and not re.search(
        r"(?ix)\b(ghar|home|house|flat|plot|zameen|property|registry|possession)\b", q
    ):
        return False
    if re.search(r"(?ix)\bbike\s+hue\b", q):
        return False
    if _VEHICLE_DEFER_RX.search(q) and not re.search(
        r"(?ix)\b(ghar|home|house|flat|plot|zameen|property|makaan|makan|registry|possession)\b",
        q,
    ):
        return False
    if is_timing_property_question(q):
        return True
    if _TIMING_RX.search(q) and _POSSESSION_TIMING_RX.search(q):
        return True
    return False
