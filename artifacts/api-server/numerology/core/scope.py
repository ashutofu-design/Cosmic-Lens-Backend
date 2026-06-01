"""Numerology report scope — pure numerology product only."""
from __future__ import annotations

import os


def include_extended_extras() -> bool:
    return os.environ.get("NUMEROLOGY_INCLUDE_EXTENDED_EXTRAS", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def include_celebrity_match() -> bool:
    return os.environ.get("NUMEROLOGY_INCLUDE_CELEBRITY", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def ai_section_allowed(section_key: str) -> bool:
    sk = (section_key or "").lower()
    return sk.startswith("tier1.") or sk.startswith("numpro.")


def report_product_title(lang: str = "hinglish") -> str:
    if lang == "hindi":
        return "उन्नत अंक बुद्धिमत्ता — लाइफ मास्टरी रिपोर्ट"
    return "ADVANCED NUMEROLOGY INTELLIGENCE"


def report_product_subtitle(lang: str = "hinglish") -> str:
    if lang == "hindi":
        return "— डेटा-आधारित व्यक्तिगत संख्या ब्लूप्रिंट —"
    return "— Data-driven personal number blueprint —"


BRAND_NAME = "Numerology Lens"
