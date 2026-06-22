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
    r"possession|registry|griha[\s-]?pravesh|handover|"
    r"construction\s+complete|builder\s+possession"
    r")\b"
)

_CAREER_MUHURAT_DEFER_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|promotion|tarakki|salary|transfer|posting|career|"
    r"interview|joining|govt|sarkari|resignation|increment|hike|"
    r"recruitment|railway|police|defence|ibps|role|onboarding|offer"
    r")\b"
)

_TIMING_RX = re.compile(
    r"(?ix)\b(kab|when|kis\s+(saal|year|mahine|month)|muhurat|timing)\b"
)


def is_property_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "property" and llm_intent.get("is_timing"):
            return True
    if _CAREER_MUHURAT_DEFER_RX.search(q) and not re.search(
        r"(?ix)\b(ghar|home|house|flat|plot|zameen|property|registry|possession)\b", q
    ):
        return False
    if is_timing_property_question(q):
        return True
    if _TIMING_RX.search(q) and _POSSESSION_TIMING_RX.search(q):
        return True
    return False
