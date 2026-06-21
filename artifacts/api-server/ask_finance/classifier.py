from __future__ import annotations

import re

from .finance_registry import (
    detect_finance_archetype,
    is_finance_static_question,
)

__all__ = [
    "classify_finance_archetype",
    "is_finance_static_question",
]


def classify_finance_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_finance"

    found = detect_finance_archetype(q)
    if found:
        return found

    # Broad finance keywords → general overview engine
    if re.search(
        r"(?ix)\b(paisa|paise|money|wealth|dhan|finance|financial|mutual|sip)\b",
        q,
    ):
        return "general_finance"
    return "general_finance"
