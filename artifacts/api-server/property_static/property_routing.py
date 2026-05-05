"""Property question router — regex topic detection + non-timing guard.

Pure rule-based. No LLM.

Guard order:
  1. ABSOLUTE timing → False (refused; let timing engine handle later)
  2. ABSOLUTE non-property context (vehicle, jewellery, business asset) → False
  3. Property topic keyword present → True
  4. Ambiguous tokens with non-property context → False
"""
from __future__ import annotations
import re
from typing import Tuple

# ── HARD TIMING REJECT (engine is non-timing, refuse cleanly) ────────
_TIMING_REJECT_RX = re.compile(
    r"(kab\s+(milegi|milega|milne|kharid|kharidu|kharidoonga|kharidoongi|"
    r"banegi|banega|hogi|hoga|hoga\s+ghar|aayegi|aayega|tak)|"
    r"kab[\s-]?tak|"
    r"(property|ghar|makaan|makan|plot|zameen|jamin|land|flat|"
    r"apartment|home)\s+(kab|kis\s+saal|kis\s+mahine|kis\s+samay|"
    r"kis\s+waqt|kis\s+time)|"
    r"(when|date|time)\s+(will|shall|can|could|should)\s+i\s+"
    r"(buy|get|own|purchase|invest)\s+"
    r"(?:in\s+)?(?:my|a|the|some|new|first|second)?\s*"
    r"(property|home|house|land|flat|plot|real[\s-]?estate)|"
    r"when\s+can\s+i\s+(buy|get|own|purchase|invest)|"
    r"best\s+(time|year|month|date|period|window)\s+(to|for)\s+"
    r"(buy|purchase|invest)|"
    r"(sahi|good|right|achha|achchha|best|favou?rable|lucky)\s+"
    r"(samay|time|waqt|muhurat|window|period|year|date)\s*"
    r"(kya|hai|kab|for)?\s*"
    r"(?:property|ghar|makaan|home|house|plot|zameen|land|flat|"
    r"buy|purchase|invest)?|"
    r"(ghar|property|plot|zameen|home|house|flat|land|makaan|"
    r"real[\s-]?estate)\s+(lene|kharidne|buy(?:ing)?)\s+"
    r"(ka|ki|ke)\s+(sahi|good|right|achha|best)\s+"
    r"(samay|time|waqt|muhurat)|"
    r"property\s+(date|year|muhurat|timing|window|period)|"
    r"(property|ghar|home|house|plot|zameen|land|flat|makaan|"
    r"real[\s-]?estate)\s+(buy|kharid|lene|kharidne)\s+"
    r"(karne\s+)?(ka|ki|ke)\s+(muhurat|samay|time|waqt)|"
    r"registry\s+(kab|date|muhurat|ka\s+muhurat|ki\s+date|ka\s+samay)|"
    r"registry[\s-]*(?:ka|ki)?[\s-]*muhurat|"
    r"shift\s+(kab|date|karne\s+ka)|"
    r"griha[\s-]?pravesh\s+(kab|muhurat|date)|"
    r"vastu\s+muhurat)",
    re.IGNORECASE,
)

# ── PROPERTY TOPIC GATE (broad coverage for ~90% real-user phrasings) ─
_PROPERTY_TOPIC_RX = re.compile(
    r"\b("
    # Hindi/Hinglish core
    r"property|propert(y|ies)|"
    r"ghar|makaan|makan|"
    r"plot|plots|"
    r"zameen|zamin|jamin|jameen|"
    r"land|lands|"
    r"flat|flats|"
    r"apartment|apartments|"
    r"home|house|houses|"
    r"real[\s-]?estate|"
    # Action verbs (with context)
    r"property[\s-]?(yog|chance|possibility|capacity|opportunity|investment)|"
    r"(ghar|home|house|flat|plot)[\s-]?(lena|lene|kharidna|kharidna\s+hai|"
    r"buy|purchase|investment)|"
    r"buy(ing)?[\s-]?(property|home|house|flat|plot|land)|"
    r"purchas(e|ing)[\s-]?(property|home|flat|plot|land)|"
    r"investing[\s-]?in[\s-]?(property|real\s*estate|land|plot)|"
    r"property[\s-]?investment|"
    r"home[\s-]?loan|griha[\s-]?rin|"
    # Structure / type
    r"villa|bungalow|kothi|haveli|"
    r"duplex|penthouse|studio[\s-]?(flat|apartment)|"
    # Ancestral / ownership
    r"paitrik\s+sampatti|paitrik|ancestral\s+property|"
    r"hissa\s+(in|me)\s+(property|ghar|zameen|jameen|jamin)|"
    r"sampatti|sampada|"
    r"own(ing)?[\s-]?(home|house|property)|"
    # Specific scenarios
    r"property[\s-]?(dispute|matter|case|verdict|chance|prospect|stability)|"
    r"ghar[\s-]?(banwana|banwane|build|construction)|"
    r"plot[\s-]?(lena|lene|kharidna|buy)|"
    r"second[\s-]?(home|property|house)|"
    r"first[\s-]?(home|property|house)|"
    r"dream[\s-]?(home|house)|"
    r"khud[\s-]?ka[\s-]?(ghar|makaan|home|house)|"
    r"apna[\s-]?(ghar|makaan|home|house)|"
    r"new[\s-]?(home|house|flat|property)"
    r")\b",
    re.IGNORECASE,
)

# ── ABSOLUTE non-property contexts (win even over property words) ─────
# Vehicle/jewellery/business-asset Qs sometimes use "kharidna/lena"
# with property-adjacent words; block those routing here.
_ABSOLUTE_NON_PROPERTY_RX = re.compile(
    r"\b(car|gaadi|gadi|bike|scooter|vehicle|"
    r"jewell?ery|gold|sona|silver|chandi|"
    r"shop|dukaan|dukan|business[\s-]?(setup|investment|asset)|"
    r"office[\s-]?space|warehouse(?!\s+at\s+home)|"
    r"factory|machinery|equipment|"
    r"share|stock|crypto|mutual[\s-]?fund|sip|fd)\b",
    re.IGNORECASE,
)

# ── Ambiguous tokens (need property context to fire) ──────────────────
_AMBIGUOUS_PROPERTY_TOKENS_RX = re.compile(
    r"\b(invest(ment)?|kharidna|lena|sampatti|hissa|"
    r"own(ing)?|buy(ing)?|purchase)\b",
    re.IGNORECASE,
)
_STRONG_PROPERTY_RX = re.compile(
    r"\b(property|ghar|makaan|makan|plot|zameen|zamin|jamin|jameen|"
    r"land|flat|apartment|home|house|houses|real[\s-]?estate|"
    r"villa|bungalow|kothi|haveli|griha|paitrik)\b",
    re.IGNORECASE,
)
_NON_PROPERTY_CTX_RX = re.compile(
    r"\b(career|kaa?riyar|job|naukri|"
    r"marriage|shaadi|partner|relationship|love|"
    r"health|sehat|swasthya|bimari|body|"
    r"stock|share|trading|crypto|mutual[\s-]?fund|"
    r"business(?!\s+(home|property))|"
    r"car|gaadi|bike)\b",
    re.IGNORECASE,
)


def _is_ambiguous_only_match(question: str) -> bool:
    """True if Q matches property regex ONLY via ambiguous tokens."""
    if not _AMBIGUOUS_PROPERTY_TOKENS_RX.search(question):
        return False
    return not _STRONG_PROPERTY_RX.search(question)


def is_timing_property_question(question: str) -> bool:
    """True if Q is about property TIMING (engine refuses).

    Requires BOTH a timing trigger AND a property-context keyword
    (or a property-specific timing phrase). Prevents non-property
    timing Qs (e.g. "shaadi kab hogi") from falsely matching here."""
    if not isinstance(question, str):
        return False
    if not _TIMING_REJECT_RX.search(question):
        return False
    # Require property-context (strong property keyword OR a
    # property-specific timing phrase like "registry/griha-pravesh")
    if _STRONG_PROPERTY_RX.search(question):
        return True
    if re.search(r"\b(registry|griha[\s-]?pravesh|vastu\s+muhurat|"
                 r"property|real[\s-]?estate|shift)\b",
                 question, re.IGNORECASE):
        return True
    return False


def is_property_question(question: str) -> bool:
    """True if Q is about STATIC property analysis.

    Returns False for:
      - Timing Qs (kab/when/muhurat/registry-date) — non-timing engine
      - Vehicle/jewellery/stock/business-asset Qs
      - Ambiguous-token-only Qs in non-property context
    """
    if not isinstance(question, str) or not question.strip():
        return False
    # Hard timing reject
    if _TIMING_REJECT_RX.search(question):
        return False
    # Absolute non-property wins
    if _ABSOLUTE_NON_PROPERTY_RX.search(question):
        # ...unless strong property word ALSO present
        if not _STRONG_PROPERTY_RX.search(question):
            return False
    if not _PROPERTY_TOPIC_RX.search(question):
        return False
    # Ambiguous-only context guard
    if _is_ambiguous_only_match(question) and \
       _NON_PROPERTY_CTX_RX.search(question):
        return False
    return True


def route_property_question(question: str) -> Tuple[str, str]:
    """Returns (mode, route_id).

    Modes:
      WARNING  — timing reject (cannot answer)
      DIRECT   — pure engine (no LLM)
      HYBRID   — engine signal-pack + LLM expression (default)
    """
    q = (question or "").lower()
    if _TIMING_REJECT_RX.search(q):
        return ("WARNING", "TIMING_PROPERTY_BLOCKED")
    # Default everyone to HYBRID — signal-pack + LLM expression.
    # This is the bread-and-butter path that handles ~90% of real Qs.
    return ("HYBRID", "general_property_overview")


# ── Locked timing-reject template ────────────────────────────────────
TIMING_REJECT_TEMPLATE = (
    "Property ka exact timing (kab milegi / kab kharidu) static chart "
    "analysis se predict karna sahi nahi — yeh muhurat aur transit ka "
    "vishay hai, jo alag se dekhna padta hai.\n\n"
    "Lekin chart se yeh zaroor pata chal sakta hai: aapki property "
    "lene ki capacity, yog ki strength, aur kis tarah ki property "
    "(plot / new home / luxury / ancestral) aapke liye fit hai. Iske "
    "liye poochho: \"meri property capacity kaisi hai\" ya \"property "
    "yog kaisa hai chart me\".\n\n"
    "👉 Final: Timing ke liye muhurat consultation lijiye. Static "
    "analysis se yog/capacity/risk dekh sakta hoon."
)
