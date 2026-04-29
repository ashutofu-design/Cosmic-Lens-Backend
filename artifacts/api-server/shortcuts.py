"""Phase 6.2 (Apr 29, 2026) — Top-N shortcut layer.

Bypass the classifier + main LLM call for obvious queries (greetings,
intro, capabilities, help, farewell). Each shortcut returns a complete
response dict in the same shape as `ai_ask`, or `None` if no pattern
matches. Fail-open: any internal error returns `None` so the normal
classifier + LLM pipeline always runs as a safety net.

Why this exists:
  - "namaste" / "thanks" / "tum kaun ho" used to consume one full
    classifier call (~1.5s) plus one main answer call (~4s) = ~5.5s
    of latency for a question that has a fixed canned reply.
  - Top patterns now return in <10ms with zero OpenAI cost and zero
    quota slot consumed.

Coverage targets ~5-10% of total ask volume on initial release.
Patterns intentionally conservative: anchored, length-capped, plain
strings only. False-positive cost = wasted shortcut on a real ask
(handled by the normal pipeline never running) — never silently wrong
on a real question because anchors require the question to be JUST
the greeting/intro phrase, not a longer ask containing it.
"""
from __future__ import annotations

import re
from typing import Optional


# ── Multilingual reply text ─────────────────────────────────────────────
# Keys match canonical lang codes used by `_resolve_response_lang` in
# openai_helper.py: "en" | "hi" | "hn" (Hinglish — default).

_GREET = {
    "en": (
        "Namaste! I'm here to help you understand your kundli. "
        "Ask me about your career, marriage, health, finance, or "
        "anything else from your chart."
    ),
    "hi": (
        "नमस्ते! मैं आपकी कुंडली के बारे में मदद के लिए हूँ। "
        "करियर, विवाह, स्वास्थ्य, धन — कुछ भी पूछिए।"
    ),
    "hn": (
        "Namaste! Main aapki kundli ke baare me madad ke liye hu. "
        "Career, shaadi, health, paisa — kuch bhi puchhiye, aapke "
        "chart ke aadhar pe jawab dunga."
    ),
}

_THANK = {
    "en": (
        "You're welcome! Feel free to ask any follow-up question "
        "about your chart."
    ),
    "hi": "आपका स्वागत है! कोई और सवाल हो तो बेझिझक पूछें।",
    "hn": "Khushi se! Aur kuch puchhna ho to bilkul puchhiye.",
}

_FAREWELL = {
    "en": "Take care! Come back anytime to explore your chart further.",
    "hi": "ध्यान रखें! कभी भी अपनी कुंडली के बारे में और जानने आ सकते हैं।",
    "hn": "Khayal rakhna! Jab bhi aur kuch jaanna ho, wapas aana.",
}

_INTRO = {
    "en": (
        "I'm Cosmic Lens — a Vedic astrology AI built on your birth "
        "chart. I analyse career timing, marriage prospects, health "
        "outlook, financial direction, and your current planetary "
        "periods (dasha) — all rooted in the actual planetary "
        "positions in your kundli, not generic horoscope text."
    ),
    "hi": (
        "मैं Cosmic Lens हूँ — आपकी जन्मकुंडली पर आधारित वैदिक "
        "ज्योतिष AI। करियर, विवाह, स्वास्थ्य, धन और वर्तमान दशा का "
        "विश्लेषण कर सकता हूँ — सब आपकी असली कुंडली पर आधारित।"
    ),
    "hn": (
        "Main Cosmic Lens hu — aapki janma kundli pe based Vedic "
        "astrology AI. Career, shaadi, health, paisa, current dasha "
        "— sab analyse kar sakta hu, sirf aapke chart ke planet "
        "positions ke aadhar pe. Generic horoscope nahi."
    ),
}

_HELP = {
    "en": (
        "Try asking:\n"
        "• When will I get married?\n"
        "• Will my health be good in 2026?\n"
        "• When will my career grow?\n"
        "• Is there any dosh in my kundli?\n"
        "• What is my current dasha?"
    ),
    "hi": (
        "इन सवालों से शुरू करें:\n"
        "• मेरी शादी कब होगी?\n"
        "• 2026 में मेरी सेहत कैसी रहेगी?\n"
        "• करियर में तरक्की कब होगी?\n"
        "• कुंडली में कोई दोष है?\n"
        "• वर्तमान दशा क्या है?"
    ),
    "hn": (
        "Yeh questions try karein:\n"
        "• Meri shaadi kab hogi?\n"
        "• 2026 me meri health kaisi rahegi?\n"
        "• Career growth kab hoga?\n"
        "• Koi dosh hai kundli me?\n"
        "• Current dasha kya chal rahi hai?"
    ),
}


# ── Patterns ────────────────────────────────────────────────────────────
# Each pattern is anchored start-to-end (^...$) so it ONLY matches when
# the question is JUST the greeting/intro phrase. Length cap below also
# rejects anything > 80 chars before regex even runs.

_GREET_RX = re.compile(
    r"^\s*(hi+|hello+|hey+|namaste|namaskar|namashkar|pranam|salaam|"
    r"good\s*morning|good\s*evening|good\s*afternoon|gm|ge|ga|"
    r"shubh\s*prabhat|shubh\s*sandhya)\s*[!.?,]*\s*$",
    re.IGNORECASE,
)

_THANK_RX = re.compile(
    r"^\s*(thanks+|thank\s*you+|thank\s*u|tysm|ty|"
    r"dhanyavaad|dhanyawad|dhanyavad|shukriya|shukria|"
    r"thx|thnx|thnks|bahut\s*shukriya|bahut\s*dhanyavaad)\s*[!.?,]*\s*$",
    re.IGNORECASE,
)

_FAREWELL_RX = re.compile(
    r"^\s*(bye+|goodbye|good\s*bye|alvida|tata|"
    r"see\s*you|see\s*ya|cya|"
    r"chalta\s*hu|chalti\s*hu|phir\s*milte\s*hain)\s*[!.?,]*\s*$",
    re.IGNORECASE,
)

_INTRO_RX = re.compile(
    r"^\s*("
    r"(tum|aap|tu|you)\s*kaun\s*(ho|hain|hai|are|are\s*you)|"
    r"who\s+are\s+(you|u)|"
    r"what\s+are\s+(you|u)|"
    r"(ye|yeh|this)\s+(app|kya)\s+(kya\s*hai|hai|is|kya)|"
    r"kya\s+(ye|yeh|this)\s+(app|hai|is)|"
    r"introduce\s+(yourself|urself)|"
    r"about\s+(you|this\s+app)"
    r")\s*[?.!,]*\s*$",
    re.IGNORECASE,
)

_CAPABILITIES_RX = re.compile(
    r"^\s*("
    r"kya\s+kar\s+sakte(\s+ho)?|"
    r"kya\s+kar\s+sakta(\s+hai|\s+ho)?|"
    r"kya\s+(puchh|pucho|pooch)|"
    r"what\s+can\s+(you|u)\s+do|"
    r"what\s+do\s+you\s+do|"
    r"capabilities|features|"
    r"how\s+(can|do)\s+you\s+help"
    r")\s*[?.!,]*\s*$",
    re.IGNORECASE,
)

_HELP_RX = re.compile(
    r"^\s*(help+|madad|sahayata|sahayta|"
    r"kaise\s+(puchh|pucho|use)|how\s+to\s+use)\s*[?.!,]*\s*$",
    re.IGNORECASE,
)


def _pick(translations: dict, lang: str) -> str:
    """Pick text by lang, falling back through hn → en."""
    return translations.get(lang) or translations.get("hn") or translations["en"]


def _normalise_lang(lang: Optional[str]) -> str:
    """Map any incoming lang token to one of {en, hi, hn}."""
    if not lang:
        return "hn"
    l = lang.strip().lower()
    if l in ("en", "english"):
        return "en"
    if l in ("hi", "hindi"):
        return "hi"
    # Default: hn (Hinglish) covers "hn", "hinglish", "auto", and unknowns.
    return "hn"


def try_shortcut(question: str, lang: str = "hn") -> Optional[dict]:
    """Return a canned response dict if the question matches a shortcut,
    else None. Never raises — failure paths return None so the caller's
    normal pipeline takes over.

    Response shape mirrors `ai_ask()` so route handlers can return it
    verbatim:
        { text, topic, confidence, source, follow_ups }
    The route layer is responsible for adding `quota` and `plan`.
    """
    try:
        q = (question or "").strip()
        if not q:
            return None
        # Length cap: anything beyond a short greeting / intro is a real
        # ask and must go through the normal pipeline. Hard cap = 80 chars.
        if len(q) > 80:
            return None

        eff_lang = _normalise_lang(lang)

        if _GREET_RX.match(q):
            text = _pick(_GREET, eff_lang)
            kind = "greet"
        elif _THANK_RX.match(q):
            text = _pick(_THANK, eff_lang)
            kind = "thank"
        elif _FAREWELL_RX.match(q):
            text = _pick(_FAREWELL, eff_lang)
            kind = "farewell"
        elif _INTRO_RX.match(q):
            text = _pick(_INTRO, eff_lang)
            kind = "intro"
        elif _CAPABILITIES_RX.match(q):
            text = _pick(_HELP, eff_lang)
            kind = "capabilities"
        elif _HELP_RX.match(q):
            text = _pick(_HELP, eff_lang)
            kind = "help"
        else:
            return None

        return {
            "text":       text,
            "topic":      "general",
            "confidence": 1.0,
            "source":     f"shortcut:{kind}",
            "follow_ups": [],
        }
    except Exception:
        # Fail open — never let a shortcut bug break the ask flow.
        return None
