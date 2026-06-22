"""Travel timing routing — foreign/settlement/visa WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

from ask_travel.travel_registry import (
    _TIMING_RX as TIMING_RX,
    _STRONG_TRAVEL_RX,
    is_career_job_abroad_question,
    is_education_study_abroad_question,
    is_mr_settle_abroad_question,
)

_SETTLEMENT_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"settle\s+(?:kab|when)|settlement\s+(?:kab|when)|"
    r"bas\s+(?:jaunga|jaungi|paunga|paungi)\s+(?:kab|when)|"
    r"foreign\s+settlement\s+(?:kab|when)|abroad\s+shift\s+(?:kab|when)|"
    r"videsh\s+(?:basna|bas\s+sakta|me\s+rahena)\s+(?:kab|when)|"
    r"pr\s+(?:kab|when)|green\s+card\s+(?:kab|when)|"
    r"immigration\s+(?:kab|when)|citizenship\s+(?:kab|when)"
    r")\b"
)


def is_travel_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "travel" and llm_intent.get("is_timing"):
            return True
    has_timing = bool(TIMING_RX.search(q)) or bool(_SETTLEMENT_TIMING_RX.search(q))
    if not has_timing:
        return False
    if is_education_study_abroad_question(q) and not re.search(
        r"(?ix)\b(job|naukri|work|career)\b", q
    ):
        return False
    if is_mr_settle_abroad_question(q):
        return False
    if is_career_job_abroad_question(q) and re.search(
        r"(?ix)\b(job|naukri|salary|promotion|office|company)\b", q
    ):
        return False
    if _SETTLEMENT_TIMING_RX.search(q):
        return True
    if re.search(r"(?ix)\b(videsh|foreign|abroad|overseas|visa|passport|pr\b|immigration)\b", q):
        return True
    return bool(_STRONG_TRAVEL_RX.search(q))


def classify_travel_timing_bucket(question: str) -> str:
    ql = (question or "").lower()
    if re.search(r"(?ix)\b(visa|passport)\b", ql):
        return "visa_theme"
    if re.search(r"(?ix)\b(settle|settlement|pr\b|green card|immigration|basna)\b", ql):
        return "foreign_settlement"
    if re.search(r"(?ix)\b(relocat|shift|move)\b", ql):
        return "relocation_abroad"
    if re.search(r"(?ix)\b(return|wapas)\b.{0,20}(india|bharat)\b", ql):
        return "return_india"
    if re.search(r"(?ix)\b(pilgrim|teerth|yatra)\b", ql):
        return "pilgrimage_travel"
    return "general_travel"
