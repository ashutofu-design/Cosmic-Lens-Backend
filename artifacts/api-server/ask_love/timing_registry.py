"""Love timing routing — relationship/patch-up WHEN (not static loyalty Qs)."""
from __future__ import annotations

import re
from typing import Optional

try:
    from ask_question_normalize import prepare_ask_question
except Exception:
    def prepare_ask_question(q: str) -> str:  # type: ignore
        return (q or "").strip()

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"milega|milegi|hoga|hogi|aayega|aayegi|patchup|patch\s*up|"
    r"commitment|propose|dasha|antardasha|mahadasha|transit|gochar|timing|"
    r"shuru|khatam|khatm|trigger|break\s+ho|door\s+hongi|chalega|"
    r"vakri|retrograde"
    r")\b"
)

_LOVE_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"love|pyaar|pyar|prem|premika|premi|prem\s*sambandh|sambandh|"
    r"crush|relationship|boyfriend|girlfriend|"
    r"patchup|patch\s*up|reconcile|commitment|propose|marry\s+him|marry\s+her|"
    r"one[\s-]?sided|affair|breakup|break\s*up|rishta|"
    r"partner|ex\b|separation|separate|unblock|no[\s-]?contact|"
    r"dry\s+spell|single\s+status|soulmate|true\s+love|"
    r"approach|insaan|enter\s+karega|wapas|purana\s+pyaar|"
    r"galatfehmi\w*|misunderstanding\w*|stressful\s+phase|healing|doori|"
    r"third\s+party|teesra|loyal\w*|loyalty|dhokha|dhoka|cheat|"
    r"parents?|ghar\s*wale|raazi|societal|samaaj|"
    r"favorable\s+dasha|naya\s+partner|relationship\s+shuru|"
    r"dusra\s+chance|purane\s+rishte|dispute|"
    r"get\s+into|come\s+into|come\s+to|enter\s+into|start\s+a|"
    r"find\s+love|find\s+a\s+partner|get\s+a\s+boyfriend|get\s+a\s+girlfriend|"
    r"in\s+a\s+relationship|dating\s+life|love\s+life"
    r")\b"
)

# Marriage timing — not dating commitment ("shaadi ke liye haan kab")
_MARRIAGE_OVERRIDE_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"shaadi\s+(kab|when|kis)|vivah\s+(kab|when)|marriage\s+(kab|when)|"
    r"wedding\s+(kab|when)|biwi\s+kab|pati\s+kab|patni\s+kab|"
    r"love\s*marriage\s+(kab|when)|pyaar\s*shaadi\s+(kab|when)|"
    r"delay\s+in\s+marriage|shaadi\s+me\s+delay"
    r")\b|"
    r"\b(shaadi|vivah|marriage|wedding)\s+(hogi|hoga|milegi|milega)\b",
)

_STATIC_LOYALTY_RX = re.compile(
    r"(?ix)\b("
    r"dhokha|dhoka|betray|cheat|cheating|loyal\w*|faithful|trust|vishwas|"
    r"wafa|beimaan|dhokebaaz"
    r")\b"
)

_EXPLICIT_LOVE_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|kis\s+(?:saal|year|mahine|month)|"
    r"muhurat|timing|dasha|antardasha|mahadasha|transit|gochar"
    r")\b"
)


def is_love_static_loyalty_question(question: str) -> bool:
    """Static betrayal/loyalty/trust Q — MR engine, not love timing ('dhoka milega')."""
    q = prepare_ask_question((question or "").strip())
    if not q:
        return False
    if not _STATIC_LOYALTY_RX.search(q):
        return False
    if _EXPLICIT_LOVE_TIMING_RX.search(q):
        return False
    if _LOVE_SCOPE_RX.search(q):
        return True
    return bool(
        re.search(
            r"(?ix)\b(love|pyaar|pyar|prem|relationship|partner|rishta)\b",
            q,
        )
    )


def love_static_overrides_llm_timing(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    """True when a loyalty/betrayal Q must run MR static, not love timing."""
    _ = llm_intent
    return is_love_static_loyalty_question(question or "")


def is_love_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = prepare_ask_question((question or "").strip())
    if not q:
        return False
    try:
        from ask_mr.timing_registry import is_mr_static_question

        if is_mr_static_question(q):
            return False
    except Exception:
        pass
    if is_love_static_loyalty_question(q):
        return False
    if _MARRIAGE_OVERRIDE_RX.search(q):
        return False  # marriage engine
    if re.search(r"(?ix)\b(dost\w*|dosti|friend|friends|circle|network|dushmani|enmity)\b", q):
        if not re.search(
            r"(?ix)\b(boyfriend|girlfriend|pyaar|pyar|love|crush|affair|partner|rishta|marry)\b",
            q,
        ):
            return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "")
        if dom == "love" and llm_intent.get("is_timing"):
            if _EXPLICIT_LOVE_TIMING_RX.search(q):
                return True
            # LLM is_timing alone is not enough — need explicit when-anchor in text.
    if not _TIMING_RX.search(q):
        return False
    return bool(_LOVE_SCOPE_RX.search(q))
