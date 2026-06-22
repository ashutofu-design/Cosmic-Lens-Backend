"""Love timing routing — relationship/patch-up WHEN (not static loyalty Qs)."""
from __future__ import annotations

import re
from typing import Optional

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"milega|milegi|hoga|hogi|aayega|aayegi|patchup|patch\s*up|"
    r"commitment|propose|dasha|transit|timing"
    r")\b"
)

_LOVE_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"love|pyaar|pyar|crush|relationship|boyfriend|girlfriend|"
    r"patchup|patch\s*up|reconcile|commitment|propose|marry\s+him|marry\s+her|"
    r"one[\s-]?sided|affair|breakup|break\s*up|rishta"
    r")\b"
)

_MARRIAGE_OVERRIDE_RX = re.compile(
    r"(?ix)\b(shaadi|shadi|vivah|marriage|wedding|biwi|pati|patni)\b"
)


def is_love_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _MARRIAGE_OVERRIDE_RX.search(q):
        return False  # marriage engine
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "")
        if dom == "love" and llm_intent.get("is_timing"):
            return True
    if not _TIMING_RX.search(q):
        return False
    return bool(_LOVE_SCOPE_RX.search(q))
