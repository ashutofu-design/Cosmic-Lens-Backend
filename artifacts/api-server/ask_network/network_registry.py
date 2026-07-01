"""Friends / social circle / network — static (non-timing) scope + archetypes."""

from __future__ import annotations

import re

NETWORK_ARCHETYPES = frozenset({
    "social_circle_quality",
    "friends_support",
    "enmity_in_circle",
    "influential_network",
    "general_network",
})

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:mahine|saal|year|month)|"
    r"milega|milegi|banega|banegi|aayega|aayegi|shuru\s+hoga|khatam|"
    r"dasha|antardasha|gochar|transit|muhurat|timing|kitne\s+mahine"
    r")\b"
)

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"dost\w*|dosti|friend|friends|saheli|sahel|yaar|buddy|peer|peers|"
    r"circle|social\s+circle|friend\s+circle|network|connections|contacts|"
    r"influential|bade\s+log|powerful\s+people|vip|well[\s-]?wisher|"
    r"support\s+system|social\s+support|madad\s+karenge|help\s+karenge|"
    r"dushmani|dushman|shatru|enemy|enmity|rivalry|nafrat|vair|"
    r"dhokha|dhoke|misunderstanding|galatfehmi|galat\s+fahmi|bewafai|betrayal|"
    r"11th\s+house|11h|social\s+capital|"
    r"bina\s+karan|referral|recommendation|mentor\s+network"
    r")\b"
)

_QUALITY_RX = re.compile(
    r"(?ix)\b("
    r"acha|achi|accha|theek|thik|bura|burra|kharab|kaisa|kaisi|kaise|"
    r"good|bad|strong|weak|supportive|toxic|healthy|unhealthy|"
    r"kitne|kitna|kaun\s+se|kis\s+type"
    r")\b"
)

_ROMANTIC_RX = re.compile(
    r"(?ix)\b("
    r"boyfriend|girlfriend|pyaar|pyar|love|crush|affair|"
    r"patni|pati|rishta|marry|marriage|partner|ex\b|patchup|patch\s*up"
    r")\b",
)

_FAME_SOCIAL_MEDIA_RX = re.compile(
    r"(?ix)\b("
    r"instagram|youtube|tiktok|followers|subscribers|viral|influencer|"
    r"celebrity|fame|famous|social\s+media"
    r")\b",
)

_CAREER_PRO_NETWORK_RX = re.compile(
    r"(?ix)\b("
    r"office\s+network|professional\s+network|corporate\s+network|"
    r"linkedin|job\s+referral|campus\s+placement|employer\s+network"
    r")\b",
)

_FOREIGN_NETWORK_RX = re.compile(
    r"(?ix)\b("
    r"abroad|foreign|videsh|overseas|visa|immigration|study\s+abroad"
    r")\b",
)


def _scope_excluded(q: str) -> bool:
    if _FAME_SOCIAL_MEDIA_RX.search(q) and not re.search(
        r"(?ix)\b(dost|friend|circle|dushmani|enmity|bade\s+log|influential)\b",
        q,
    ):
        return True
    if _CAREER_PRO_NETWORK_RX.search(q):
        return True
    if _FOREIGN_NETWORK_RX.search(q) and not re.search(
        r"(?ix)\b(dost|friend|circle|social\s+circle|11th\s+house)\b",
        q,
    ):
        return True
    if _ROMANTIC_RX.search(q) and not re.search(
        r"(?ix)\b(dost|dosti|friend|friends|circle|network|dushmani)\b",
        q,
    ):
        return True
    return False


def is_network_static_question(
    question: str,
    llm_intent: dict | None = None,
) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q):
        return False
    if _scope_excluded(q):
        return False

    try:
        from ask_network.timing_registry import is_network_timing_question

        if is_network_timing_question(q, llm_intent):
            return False
    except Exception:
        if _TIMING_RX.search(q) and not _QUALITY_RX.search(q):
            return False

    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").strip().lower()
        if dom in ("network", "friends", "social_circle") and not llm_intent.get("is_timing"):
            return True

    return True


def detect_network_archetype(question: str) -> str | None:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q):
        return None
    if re.search(
        r"(?ix)\b(dushman|dushmani|shatru|enemy|enmity|nafrat|vair|dhokha|bewafai|betrayal)\b",
        q,
    ):
        return "enmity_in_circle"
    if re.search(
        r"(?ix)\b(bade\s+log|influential|vip|powerful\s+people|social\s+capital)\b",
        q,
    ):
        return "influential_network"
    if re.search(
        r"(?ix)\b(madad|help|support|sahara|well[\s-]?wisher|referral)\b",
        q,
    ):
        return "friends_support"
    if re.search(
        r"(?ix)\b(social\s+circle|friend\s+circle|circle|dost\w*|friends|network)\b",
        q,
    ) and _QUALITY_RX.search(q):
        return "social_circle_quality"
    if re.search(
        r"(?ix)\b(circle|dost\w*|friends|network|dosti)\b",
        q,
    ):
        return "general_network"
    return "general_network"
