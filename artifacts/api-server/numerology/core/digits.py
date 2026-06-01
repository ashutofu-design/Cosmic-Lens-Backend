"""Digit meanings and driver archetypes — no astrology mapping."""
from __future__ import annotations

from typing import Dict, Tuple

ARCHETYPE_BY_DRIVER: Dict[int, str] = {
    1: "Leader / Pioneer",
    2: "Diplomat / Empath",
    3: "Creator / Communicator",
    4: "Builder / Strategist",
    5: "Explorer / Networker",
    6: "Harmonizer / Nurturer",
    7: "Analyst / Seeker",
    8: "Executive / Authority",
    9: "Humanitarian / Catalyst",
}

ARCHETYPE_SHORT: Dict[int, str] = {
    1: "Leader",
    2: "Diplomat",
    3: "Creator",
    4: "Builder",
    5: "Explorer",
    6: "Harmonizer",
    7: "Analyst",
    8: "Executive",
    9: "Humanitarian",
}

# Direct digit psychology (no planetary mapping)
NUMBER_MEANING: Dict[int, str] = {
    1: "leadership",
    2: "cooperation",
    3: "creativity",
    4: "discipline",
    5: "adaptability",
    6: "responsibility",
    7: "analysis",
    8: "power",
    9: "completion",
}

# Core psychology per digit 0–9
DIGIT_TRAITS: Dict[int, Dict[str, str]] = {
    0: {
        "theme": "reset / amplification of prior digit",
        "behavior": "softens or magnifies the digit before it",
    },
    1: {
        "theme": "leadership / initiation",
        "behavior": "decisive, independent, visibility-seeking",
    },
    2: {
        "theme": "sensitivity / cooperation",
        "behavior": "relational, patient, detail-aware",
    },
    3: {
        "theme": "creativity / expression",
        "behavior": "communicative, optimistic, idea-driven",
    },
    4: {
        "theme": "structure / discipline",
        "behavior": "systematic, steady, risk-aware",
    },
    5: {
        "theme": "movement / adaptability",
        "behavior": "versatile, curious, change-tolerant",
    },
    6: {
        "theme": "responsibility / harmony",
        "behavior": "supportive, aesthetic, duty-oriented",
    },
    7: {
        "theme": "analysis / introspection",
        "behavior": "research-minded, private, quality-focused",
    },
    8: {
        "theme": "power / material mastery",
        "behavior": "ambitious, accountable, results-driven",
    },
    9: {
        "theme": "completion / humanitarianism",
        "behavior": "intense, generous, closure-oriented",
    },
}


def reduce_number(n: int) -> int:
    n = abs(int(n))
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n


def archetype_for(driver: int) -> str:
    return ARCHETYPE_BY_DRIVER.get(reduce_number(driver), "—")


def number_meaning_for(n: int) -> str:
    """Single-word psychology label for digit 1–9."""
    return NUMBER_MEANING.get(reduce_number(n), "—")


def digit_trait(d: int) -> Tuple[str, str]:
    t = DIGIT_TRAITS.get(int(d) % 10, DIGIT_TRAITS[0])
    return t["theme"], t["behavior"]
