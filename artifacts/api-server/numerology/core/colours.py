"""Psychological colour associations per driver number."""
from __future__ import annotations

from typing import Any, Dict

_LUCKY_COLOURS: Dict[int, Dict[str, Any]] = {
    1: {
        "primary": ["Gold", "Bright Orange", "Deep Yellow"],
        "secondary": ["Copper", "Bronze", "Royal Red"],
        "avoid": ["Black", "Dark Blue", "Grey"],
        "vehicle": "Warm gold or cream — signals confidence and clarity on the road.",
        "business": "Gold + orange in brand — leadership and warmth.",
        "accent": "Warm metallics in accessories or UI highlights.",
    },
    2: {
        "primary": ["Pearl White", "Cream", "Silver"],
        "secondary": ["Sea Green", "Light Blue", "Soft Pink"],
        "avoid": ["Black", "Bright Red", "Dark Brown"],
        "vehicle": "Soft white/silver — calm, approachable travel tone.",
        "business": "Silver + white — trust and listening.",
        "accent": "Soft reflective tones.",
    },
    3: {
        "primary": ["Bright Yellow", "Saffron", "Golden Yellow"],
        "secondary": ["Light Pink", "Light Purple", "Cream"],
        "avoid": ["Dark Green", "Black", "Steel Grey"],
        "vehicle": "Yellow/cream — creative, optimistic mobility.",
        "business": "Yellow + purple accents — ideas + growth.",
        "accent": "Bright highlights for CTAs.",
    },
    4: {
        "primary": ["Grey", "Khaki", "Electric Blue"],
        "secondary": ["Off-White", "Navy", "Slate"],
        "avoid": ["Pure Black", "Deep Red"],
        "vehicle": "Grey/blue — structured, modern, reliable.",
        "business": "Blue + grey — systems and trust.",
        "accent": "Minimal, high-contrast UI.",
    },
    5: {
        "primary": ["Light Green", "Turquoise", "White"],
        "secondary": ["Sky Blue", "Mint", "Yellow"],
        "avoid": ["Heavy Black"],
        "vehicle": "Green/white — agile, communicative.",
        "business": "Green + white — fresh, networked brand.",
        "accent": "Motion-friendly palette.",
    },
    6: {
        "primary": ["Pink", "Light Blue", "White"],
        "secondary": ["Pastel Green", "Lavender", "Cream"],
        "avoid": ["Harsh Black", "Blood Red"],
        "vehicle": "Pink/soft blue — comfort and care.",
        "business": "Blush + sky — relational brand.",
        "accent": "Elegant pastels.",
    },
    7: {
        "primary": ["Sea Green", "Cream", "Smokey Grey"],
        "secondary": ["Light Yellow", "Muted Blue"],
        "avoid": ["Neon", "Loud Red"],
        "vehicle": "Muted green/grey — quiet focus.",
        "business": "Grey + sea green — analytical brand.",
        "accent": "Understated professional tones.",
    },
    8: {
        "primary": ["Navy", "Charcoal", "Deep Purple"],
        "secondary": ["Black", "Burgundy", "Silver"],
        "avoid": ["Chaotic multi-neon"],
        "vehicle": "Navy/charcoal — authority on the road.",
        "business": "Navy + silver — executive presence.",
        "accent": "Strong contrast, premium feel.",
    },
    9: {
        "primary": ["Red", "Crimson", "Maroon"],
        "secondary": ["Orange", "Pink", "White"],
        "avoid": ["Dull Brown-Grey"],
        "vehicle": "Red/maroon — high-energy visibility.",
        "business": "Red + white — bold mission brand.",
        "accent": "Action colour for key buttons.",
    },
}


def lucky_colours_pack(driver: int, lang: str = "hinglish") -> Dict[str, Any]:
    pack = _LUCKY_COLOURS.get(driver, _LUCKY_COLOURS[1])
    from numerology.core.weekdays import weekday_productivity_pack
    return {
        "primary": pack.get("primary", []),
        "secondary": pack.get("secondary", []),
        "avoid": pack.get("avoid", []),
        "vehicle": pack.get("vehicle", "—"),
        "business": pack.get("business", "—"),
        "accent_tone": pack.get("accent", "—"),
        "day_dress": weekday_productivity_pack(driver),
    }
