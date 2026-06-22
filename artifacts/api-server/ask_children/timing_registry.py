"""Children timing routing — conception/pregnancy/santan WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"kitna\s+time|dasha|transit|gochar|muhurat|timing"
    r")\b"
)

_CHILD_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"bachcha|bachche|baby|child|children|santan|pregnancy|pregnant|"
    r"conceive|conception|delivery|garbh|progeny|putra|putri|"
    r"become\s+a\s+parent|mata|pita\s+banna"
    r")\b"
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
    if not _TIMING_RX.search(q):
        return False
    return bool(_CHILD_SCOPE_RX.search(q))
