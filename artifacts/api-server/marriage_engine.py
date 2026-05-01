"""
marriage_engine.py
==================
LEAN rewrite of the old marriage_engine.py (1480 lines) which was wiped
on 1 May 2026 (Phase 2.8.21) per user direction.

Phase 2.8.22 (1 May 2026) — file renamed back to `marriage_engine.py` per
user direction: "marriage timing ko rename karo marriage engine". The
original public API contract (used by openai_helper.py) is preserved here.

This file is intentionally LEAN.

The previous engine had bloated to 22 sections / 6 focus-block layers /
~1070 tokens per verdict block. After architectural review, the user
correctly identified that the engine's IRREDUCIBLE responsibilities are
only what the LLM cannot do reliably:

  1. TIMING        — locked Dasha window math (LLM hallucinates dates)
  2. VERDICT/SCORE — deterministic yes/no with confidence (LLM gives random scores)
  3. REMEDY PLANET — weakest-factor identification (LLM picks random planet)

Everything else (Manglik intensity, Vargottam, Argala, SAV scores, KP per-planet
scan, spouse description, Saturn transit blocking, etc.) can be handled by
GPT-5.4 reading the whole-kundli context already sent in the prompt.

CURRENT STATE: scaffolds + safe-default stubs only.

The 4 public functions exposed below preserve the API contract that
openai_helper.py expects, so the API server boots cleanly. While these stubs
are in place, marriage questions are answered by the LLM using the whole
kundli context (no engine-locked dates / scores / remedies).

User will populate this file incrementally with the new lean implementation.

Old 1480-line file recoverable from git: `git show d1741bf:artifacts/api-server/marriage_engine.py`
"""

from __future__ import annotations

from typing import Any, Optional


# ════════════════════════════════════════════════════════════════════
# PUBLIC API — must match the contract openai_helper.py imports
# ════════════════════════════════════════════════════════════════════

def assess_marriage(kundli: dict, intel: dict, kp: dict,
                    birth: Optional[Any] = None) -> dict:
    """Stub — returns empty verdict dict.

    While empty, openai_helper.py's marriage routing will detect the empty
    verdict and gracefully fall back to whole-kundli LLM-only narration.

    User will fill this in with the new lean 3-core implementation:
      - timing window (Dasha intersection math)
      - verdict + score (deterministic yes/no)
      - remedy planet (weakest-factor pick)
    """
    return {}


def format_verdict_for_prompt(v: dict) -> str:
    """Stub — returns empty string when verdict dict is empty.

    openai_helper.py checks for falsy/empty return and skips inserting
    the marriage verdict block into the LLM prompt.
    """
    if not v:
        return ""
    return ""


def extract_window_str(v: dict) -> str:
    """Stub — returns empty string.

    openai_helper.py uses this to surface the engine's locked window
    string (e.g. "April 2027 to August 2028"). Empty string means
    "no engine-locked window — let LLM narrate from whole kundli".
    """
    if not v:
        return ""
    return ""


def extract_alt_window_str(v: dict) -> str:
    """Stub — returns empty string.

    openai_helper.py uses this for an alternate (fallback) window.
    Empty string means "no alternate window from engine".
    """
    if not v:
        return ""
    return ""
