"""Universal D1+D9 chart+LLM rules when no domain engine facts exist.

Systematic house-lord-karaka-dignity pipeline — same for static and timing
fallbacks so the LLM does not guess randomly.
"""

from __future__ import annotations

import re
from typing import Any

# Primary houses + karakas per life area (Parashari baseline).
_TOPIC_FOCUS: dict[str, dict[str, Any]] = {
    "love": {
        "houses": (5, 7, 11),
        "karakas": ("Venus", "Moon", "Mars", "Jupiter"),
        "d9": "7th lord, Venus, Moon in D9",
    },
    "marriage": {
        "houses": (7, 2, 8, 11),
        "karakas": ("Venus", "Jupiter", "Moon", "Mars"),
        "d9": "D9 lagna, 7th house, 7th lord, Venus",
    },
    "career": {
        "houses": (10, 6, 2, 11),
        "karakas": ("Sun", "Saturn", "Mercury", "Jupiter"),
        "d9": "D10 if shown else D9 10th lord",
    },
    "finance": {
        "houses": (2, 11, 5, 9),
        "karakas": ("Jupiter", "Venus", "Mercury", "Moon"),
        "d9": "2nd/11th lords in D9",
    },
    "health": {
        "houses": (1, 6, 8, 12),
        "karakas": ("Moon", "Sun", "Mars", "Saturn"),
        "d9": "Lagna lord + 6th lord in D9",
    },
    "children": {
        "houses": (5, 9, 11),
        "karakas": ("Jupiter", "Moon", "Venus"),
        "d9": "5th lord in D9",
    },
    "education": {
        "houses": (4, 5, 9),
        "karakas": ("Mercury", "Jupiter", "Moon"),
        "d9": "5th/9th lords in D9",
    },
    "property": {
        "houses": (4, 2, 11),
        "karakas": ("Mars", "Moon", "Venus", "Saturn"),
        "d9": "4th lord in D9 / Chaturthamsa if shown",
    },
    "travel": {
        "houses": (3, 9, 12),
        "karakas": ("Moon", "Rahu", "Jupiter"),
        "d9": "9th/12th lords in D9",
    },
    "litigation": {
        "houses": (6, 8, 12),
        "karakas": ("Mars", "Saturn", "Rahu"),
        "d9": "6th lord in D9",
    },
    "spiritual": {
        "houses": (9, 12, 8),
        "karakas": ("Jupiter", "Ketu", "Moon", "Saturn"),
        "d9": "9th/12th lords, Ketu in D9",
    },
    "luck": {
        "houses": (9, 5, 11),
        "karakas": ("Jupiter", "Moon", "Sun"),
        "d9": "9th lord in D9",
    },
    "general": {
        "houses": (1, 9, 10),
        "karakas": ("Lagna lord", "Moon", "Sun", "Jupiter"),
        "d9": "D9 lagna + same topic lords",
    },
}

_LOVE_RX = re.compile(
    r"(?ix)\b(love|pyaar|pyar|prem|relationship|partner|boyfriend|girlfriend|"
    r"crush|rishta|dhokha|dhoka|betray|loyal|trust|dating)\b"
)
_CAREER_RX = re.compile(
    r"(?ix)\b(career|naukri|job|promotion|boss|office|business|profession)\b"
)
_HEALTH_RX = re.compile(
    r"(?ix)\b(health|sehat|swasth|disease|illness|tabiyat)\b"
)
_FINANCE_RX = re.compile(
    r"(?ix)\b(paisa|money|dhan|income|salary|wealth|finance|debt|loan)\b"
)
_TIMING_RX = re.compile(
    r"(?ix)\b(kab|when|kis\s+(?:saal|year|mahine|month)|timing|muhurat)\b"
)

_UNIVERSAL_PIPELINE = """
=== UNIVERSAL CHART ANALYSIS (no domain engine — D1+D9 systematic read) ===
You have the FULL chart block below (D1 planets with sign/house/dignity/degree,
house lords, D9 Navamsa, dasha if shown). NO invented facts.

MANDATORY WORKFLOW (internal — do NOT print step labels in the reply):
STEP 1 — QUESTION LOCK
  • Restate mentally what user asked (yes/no, quality, timing, strength).
  • Do NOT drift to unrelated topics (e.g. property if they asked love).

STEP 2 — PICK TOPIC HOUSES (from TOPIC FOCUS below)
  • For each selected house: note sign, occupants, aspects if listed.
  • Find house LORD → where is lord placed (house + sign)?
  • Lord dignity: exalted / own-sign / debilitated / neutral (from chart block).
  • Malefic in house (Saturn/Mars/Rahu/Ketu/Sun) = friction; benefic = support.

STEP 3 — KARAKA PLANETS
  • For topic karakas: read house, sign, dignity, retrograde from chart.
  • Strong = exalted or own-sign in kendra/trikona; weak = debilitated or in 6/8/12.
  • Planet strength row / functional nature column — trust it if present.

STEP 4 — AFFLICTION vs STRENGTH
  • Count: debilitated lords? dusthana placement (6/8/12)? malefic tenants?
  • Mixed = some support + some affliction → answer mixed, not all-positive.

STEP 5 — D9 CROSS-CHECK
  • Same planet/lord in Navamsa: confirms if strong, fragile if weak/debilitated there.
  • Marriage/love → D9 7th; career → D10 if in block else D9 10th.

STEP 6 — ANSWER
  • Lead with clear leaning: haan / nahi / mixed (match affliction count).
  • Cite 2–4 chart factors in plain Hinglish (hide jargon unless user used it).
  • Missing data in block → say signal unclear; do NOT guess degree or sign.
"""


def infer_chart_topic(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    q = (question or "").strip()
    dom = str((llm_intent or {}).get("domain") or "").strip().lower()
    if dom in _TOPIC_FOCUS:
        return dom
    if dom in ("friends", "social_circle", "network"):
        return "general"
    try:
        from ask_intent_fidelity import infer_primary_domain

        inferred = infer_primary_domain(q)
        if inferred and inferred in _TOPIC_FOCUS:
            return inferred
    except Exception:
        pass
    if _LOVE_RX.search(q):
        return "love"
    if _CAREER_RX.search(q):
        return "career"
    if _HEALTH_RX.search(q):
        return "health"
    if _FINANCE_RX.search(q):
        return "finance"
    return "general"


def build_topic_focus_block(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    topic = infer_chart_topic(question, llm_intent)
    spec = _TOPIC_FOCUS.get(topic) or _TOPIC_FOCUS["general"]
    houses = ", ".join(f"{h}H" for h in spec["houses"])
    karakas = ", ".join(spec["karakas"])
    return (
        f"TOPIC FOCUS ({topic}): primary houses {houses}; "
        f"karakas {karakas}; D9 check — {spec['d9']}."
    )


def _timing_addon(qtype: str, question: str, llm_intent: dict[str, Any] | None) -> str:
    is_timing = (
        str(qtype or "").upper() == "TIMING"
        or bool((llm_intent or {}).get("is_timing"))
        or bool(_TIMING_RX.search(question or ""))
    )
    if not is_timing:
        return (
            "\nMODE: STATIC / pattern — do NOT invent calendar dates. "
            "Dasha in block is context only unless user asked kab/when.\n"
        )
    return (
        "\nMODE: TIMING — user asked kab/when.\n"
        "• Use ONLY Mahadasha/Antardasha periods explicitly listed in the chart block.\n"
        "• Match active dasha lords to topic houses/karakas from STEP 2–3.\n"
        "• If dasha section missing → say timing unclear from chart; do NOT invent month/year.\n"
        "• Window = broad phase (e.g. 'Jupiter antardasha me') not fake exact dates.\n"
    )


def build_universal_chart_llm_rules(
    question: str,
    *,
    qtype: str = "STATIC",
    llm_intent: dict[str, Any] | None = None,
) -> str:
    """Full extra_rules block for chart-only LLM path (static or timing)."""
    focus = build_topic_focus_block(question, llm_intent)
    timing = _timing_addon(qtype, question, llm_intent)
    summary = ""
    if isinstance(llm_intent, dict):
        s = str(llm_intent.get("question_summary") or "").strip()
        if s:
            summary = f"\nUSER ASKED (lock): {s[:400]}\n"
    return f"{_UNIVERSAL_PIPELINE}\n{focus}\n{timing}{summary}"
