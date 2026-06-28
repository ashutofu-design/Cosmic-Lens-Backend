"""Friends, network & circle timing — 11H WHEN questions (Mercury / Rahu)."""
from __future__ import annotations

import re
from typing import Optional

_EXPLICIT_WHEN_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|"
    r"kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"kis\s+dasha|dasha\s+me|gochar|transit|muhurat|kitne\s+mahine|"
    r"trigger\s+hoga|active\s+hoga|shuru\s+hoga|shant\s+hogi|khatam\s+hogi"
    r")\b|(?:कब|कितना\s+समय)"
)

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"milega|milegi|hoga|hogi|honge|aayega|aayegi|banega|banegi|"
    r"shuru\s+hoga|khatam|khatam\s+hogi|theek\s+hogi|thik\s+hogi|"
    r"shant|shaant|sulah|band\s+hogi|khatam\s+honge|"
    r"active|dasha|antardasha|gochar|transit|muhurat|timing|"
    r"turning\s+point|lagenge|mil\s+jayega|"
    r"kitne\s+mahine|help\s+karenge|madad\s+karenge"
    r")\b|(?:कब|कितना\s+समय)"
)

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"dost\w*|dosti|friend|friends|saheli|sahel|yaar|buddy|peer|peers|"
    r"circle|social\s+circle|friend\s+circle|network|connections|contacts|"
    r"influential|bade\s+log|powerful\s+people|vip|well[\s-]?wisher|"
    r"support\s+system|social\s+support|help\s+karenge|madad\s+karenge|"
    r"dushmani|dushman|shatru|enemy|enmity|rivalry|nafrat|vair|"
    r"dhokha|dhoke|misunderstanding|galatfehmi|galat\s+fahmi|bewafai|betrayal|"
    r"11th\s+house|11h|budh|mercury|social\s+capital|"
    r"bina\s+karan|referral|recommendation|mentor\s+network"
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


def is_network_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if re.search(r"(?ix)\bkya\b", q) and not _EXPLICIT_WHEN_RX.search(q):
        return False
    if _FAME_SOCIAL_MEDIA_RX.search(q) and not re.search(
        r"(?ix)\b(dost|friend|circle|dushmani|enmity|bade\s+log|influential)\b",
        q,
    ):
        return False
    if _CAREER_PRO_NETWORK_RX.search(q):
        return False
    if _FOREIGN_NETWORK_RX.search(q) and not re.search(
        r"(?ix)\b(dost|friend|circle|social\s+circle|11th\s+house)\b",
        q,
    ):
        return False
    if _ROMANTIC_RX.search(q) and not re.search(
        r"(?ix)\b(dost|dosti|friend|friends|circle|network|dushmani)\b",
        q,
    ):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("network", "friends", "social_circle") and llm_intent.get("is_timing"):
            return True
    if not _SCOPE_RX.search(q):
        return False
    if not _TIMING_RX.search(q) and not _EXPLICIT_WHEN_RX.search(q):
        return False
    return True


def classify_network_timing_bucket(question: str) -> str:
    from event_timing.network.network_timing_v1 import classify_network_timing_bucket as _classify

    return _classify(question)
