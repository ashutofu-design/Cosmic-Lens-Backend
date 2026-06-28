"""Finance timing routing — paisa/income/wealth WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

from ask_career.timing_registry import TIMING_RX
from ask_finance.routing import finance_overrides_career

_CAREER_ANCHOR_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|promotion|salary\s+hike|office|company|transfer|"
    r"posting|interview|govt\s+job|sarkari|employer|work\s+permit"
    r")\b"
)

_STOCK_RX = re.compile(
    r"(?ix)\b("
    r"nifty|sensex|share[\s-]*market|stock|intraday|sip|crypto|portfolio"
    r")\b"
)


def is_finance_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _STOCK_RX.search(q):
        return False
    try:
        from ask_property.timing_registry import is_property_timing_question  # type: ignore
        if is_property_timing_question(q, llm_intent):
            return False
    except Exception:
        pass
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "finance" and llm_intent.get("is_timing"):
            return True
    if not TIMING_RX.search(q):
        return False
    if _CAREER_ANCHOR_RX.search(q):
        return False
    return finance_overrides_career(q)
