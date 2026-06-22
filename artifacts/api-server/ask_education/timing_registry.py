"""Education timing routing — exam/admission/result WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

from ask_education.education_registry import _GOVT_EXAM_RX, _TIMING_RX

_EDU_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"exam|result|admission|degree|graduation|college|university|"
    r"padhai|study|course|semester|scholarship|pass|clear|"
    r"board|marks|topper|rank"
    r")\b"
)


def is_education_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _GOVT_EXAM_RX.search(q):
        return False  # career timing
    if re.search(
        r"(?ix)\b(interview|joining|offer\s+letter|onboarding|promotion|naukri|job)\b", q
    ):
        return False  # career timing
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "education" and llm_intent.get("is_timing"):
            return True
    if not _TIMING_RX.search(q):
        return False
    return bool(_EDU_SCOPE_RX.search(q))
