"""Strip astrology/planet vocabulary from numerology user-facing text."""
from __future__ import annotations

import re
from typing import Any, List, Tuple

# Order matters: longer / specific phrases before generic word rules.
_REPLACEMENTS: List[Tuple[str, str]] = [
    (r"Mon-Sun\b", "Mon-Sunday"),
    (r"planetary clash", "behavioral mismatch"),
    (r"Planetary clash", "Behavioral mismatch"),
    (r"planetary energies", "number vibrations"),
    (r"Planetary energies", "Number vibrations"),
    (r"planetary energy", "number vibration"),
    (r"Planetary energy", "Number vibration"),
    (r"planetary timing", "number-cycle timing"),
    (r"Planetary timing", "Number-cycle timing"),
    (r"planetary identity", "number identity"),
    (r"planetary impact", "behavior impact"),
    (r"planetary tonic", "focus practice"),
    (r"planetary alignment", "number alignment"),
    (r"planetary frequencies", "number frequencies"),
    (r"planetary table", "weekday number table"),
    (r"planetary day", "root-number day"),
    (r"ruling planet", "core number"),
    (r"Ruling planet", "Core number"),
    (r"planet-vibration", "number vibration"),
    (r"planet vibration", "number vibration"),
    (r"planet's", "number's"),
    (r"Planet's", "Number's"),
    (r"\bplanetary\b", "behavioral"),
    (r"\bPlanetary\b", "Behavioral"),
    (r"\bplanets\b", "numbers"),
    (r"\bPlanets\b", "Numbers"),
    (r"\bplanet\b", "number"),
    (r"\bPlanet\b", "Number"),
    (r"\bgraha\b", "number"),
    (r"\bGraha\b", "Number"),
    (r"\bSun\b", "Number 1"),
    (r"\bMoon\b", "Number 2"),
    (r"\bJupiter\b", "Number 3"),
    (r"\bRahu\b", "Number 4"),
    (r"\bMercury\b", "Number 5"),
    (r"\bVenus\b", "Number 6"),
    (r"\bKetu\b", "Number 7"),
    (r"\bSaturn\b", "Number 8"),
    (r"\bMars\b", "Number 9"),
    (r"\bSurya\b", "Number 1"),
    (r"\bChandra\b", "Number 2"),
    (r"\bBrihaspati\b", "Number 3"),
    (r"\bBudha\b", "Number 5"),
    (r"\bShukra\b", "Number 6"),
    (r"\bShani\b", "Number 8"),
    (r"\bMangal\b", "Number 9"),
    # Occult / spiritual remedy language → practical habits
    (r"\bbeej mantra\b", "focus phrase"),
    (r"\bBeej mantra\b", "Focus phrase"),
    (r"\bBEEJ MANTRA\b", "FOCUS PHRASE"),
    (r"\bspiritual remedies\b", "practical habits"),
    (r"\bSpiritual remedies\b", "Practical habits"),
    (r"\bspiritual remedy\b", "practical habit"),
    (r"\bSpiritual remedy\b", "Practical habit"),
    (r"\bspiritual path\b", "life direction"),
    (r"\bSpiritual path\b", "Life direction"),
    (r"\baura cleansing\b", "energy reset routine"),
    (r"\bAura cleansing\b", "Energy reset routine"),
    (r"\btemple remedies\b", "quiet-space routine"),
    (r"\bTemple remedies\b", "Quiet-space routine"),
    (r"\bdeity worship\b", "values-based practice"),
    (r"\bDeity worship\b", "Values-based practice"),
    (r"\bIshta Devata\b", "core value focus"),
    (r"\bNavagraha\b", "nine-number map"),
    (r"\bfasting\b", "light-meal discipline"),
    (r"\bFasting\b", "Light-meal discipline"),
    (r"\bfast day\b", "focus day"),
    (r"\bFast day\b", "Focus day"),
    (r"\bpuja\b", "reflection practice"),
    (r"\bPuja\b", "Reflection practice"),
    (r"\bpooja\b", "reflection practice"),
    (r"\bPooja\b", "Reflection practice"),
    (r"\bdharma\b", "life direction"),
    (r"\bDharma\b", "Life direction"),
    (r"\bmantra\b", "affirmation"),
    (r"\bMantra\b", "Affirmation"),
    (r"\bMANTRA\b", "AFFIRMATION"),
    (r"\byantra\b", "focus board"),
    (r"\bYantra\b", "Focus board"),
    (r"\bgemstone\b", "accent colour"),
    (r"\bGemstone\b", "Accent colour"),
    (r"\bgemstones\b", "accent colours"),
    (r"\bGemstones\b", "Accent colours"),
    (r"\bgem tone\b", "accent tone"),
    (r"\bGem tone\b", "Accent tone"),
    (r"\bgemstone_tone\b", "accent_tone"),
    (r"\bdaan\b", "giving habit"),
    (r"\bDaan\b", "Giving habit"),
    (r"\bworship\b", "values practice"),
    (r"\bWorship\b", "Values practice"),
    (r"\bremedies\b", "habits"),
    (r"\bRemedies\b", "Habits"),
    (r"\bremedy\b", "habit"),
    (r"\bRemedy\b", "Habit"),
    (r"\bafflicted\b", "under stress"),
    (r"\bAfflicted\b", "Under stress"),
    (r"\bdebilitated\b", "low-energy"),
    (r"\bDebilitated\b", "Low-energy"),
    (r"\bmoving aura\b", "daily mobility pattern"),
    (r"\baura\b", "energy"),
    (r"\bAura\b", "Energy"),
]

_COMPILED = [(re.compile(p), r) for p, r in _REPLACEMENTS]


def sanitize_text(text: str) -> str:
    if not text:
        return text
    out = str(text)
    for pat, repl in _COMPILED:
        out = pat.sub(repl, out)
    return out


def sanitize_mapping(data: Any) -> Any:
    if isinstance(data, str):
        return sanitize_text(data)
    if isinstance(data, list):
        return [sanitize_mapping(x) for x in data]
    if isinstance(data, dict):
        return {k: sanitize_mapping(v) for k, v in data.items()}
    return data
