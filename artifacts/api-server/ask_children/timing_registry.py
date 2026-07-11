"""Children timing routing — conception/pregnancy/santan WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"kitna\s+time|dasha|transit|gochar|muhurat|timing|"
    r"hoga|hogi|milega|milegi|banega|banegi"
    r")\b"
)

_CHILD_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"bachcha|bachche|bachha|baby|child|children|santan|santaan|pregnancy|pregnant|"
    r"conceive|conception|delivery|garbh|progeny|putra|putri|"
    r"become\s+a\s+parent|mata|pita\s+banna|aulad"
    r")\b"
)


def llm_says_children_timing(llm_intent: Optional[dict] = None) -> bool:
    """True when LLM/admin routing says children domain + timing."""
    if not isinstance(llm_intent, dict):
        return False
    dom = str(
        llm_intent.get("domain")
        or llm_intent.get("routed_domain")
        or ""
    ).strip().lower()
    if dom != "children":
        return False
    return bool(
        llm_intent.get("is_timing") or llm_intent.get("routed_timing")
    )


def is_children_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "children" and llm_intent.get("is_timing"):
            return True
    if llm_says_children_timing(llm_intent):
        return True
    if not _TIMING_RX.search(q):
        return False
    return bool(_CHILD_SCOPE_RX.search(q))
