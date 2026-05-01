"""
marriage_engine package
=======================
Top-level package for marriage chart analysis.

Phase 2.8.23 (1 May 2026) — converted from single file `marriage_engine.py`
to a package with sub-engines per user direction:
  "marriage engine ke andar aur 2 engine rakho ya folder rakho —
   ek marriage timing, ek love or arrange marriage"

Sub-engines:
  - marriage_timing.py    : TIMING window math (Dasha ∩ Jupiter)
  - love_or_arrange.py    : LOVE vs ARRANGED marriage classifier

This __init__.py re-exports the 4 PUBLIC FUNCTIONS that openai_helper.py
imports, so backward compatibility is fully preserved:
  - assess_marriage(kundli, intel, kp, birth)        -> dict
  - format_verdict_for_prompt(v)                     -> str
  - extract_window_str(v)                            -> str
  - extract_alt_window_str(v)                        -> str

Architecture:
  openai_helper.py
        │
        ▼
   marriage_engine.assess_marriage()    ← top-level orchestrator
        │
        ├──> marriage_timing.compute_timing_window()
        │       (returns timing dict: next_window, refined window)
        │
        └──> love_or_arrange.classify_marriage_type()
                (returns classification dict: type, scores, reasons)
        │
        ▼
   verdict_dict (merged) -> openai_helper -> LLM prompt

CURRENT STATE: all sub-engines are stubs returning {}.
Result: assess_marriage() returns merged empty dict {},
        format_verdict_for_prompt({}) returns "",
        openai_helper gracefully falls back to LLM-only mode.

User will populate sub-engines incrementally.
"""

from __future__ import annotations

from typing import Any, Optional

from .marriage_timing import compute_timing_window
from .love_or_arrange import classify_marriage_type


# ════════════════════════════════════════════════════════════════════
# PUBLIC API — must match the contract openai_helper.py imports
# ════════════════════════════════════════════════════════════════════

def assess_marriage(kundli: dict, intel: dict, kp: dict,
                    birth: Optional[Any] = None) -> dict:
    """Top-level orchestrator. Calls each sub-engine and merges results.

    Returns merged verdict dict. While all sub-engines are stubs,
    returns {} so openai_helper falls back to LLM-only mode.
    """
    timing = compute_timing_window(kundli, intel, kp, birth) or {}
    classify = classify_marriage_type(kundli, intel, kp, birth) or {}

    if not timing and not classify:
        return {}

    verdict: dict = {}
    if timing:
        verdict.update(timing)
    if classify:
        verdict["marriage_type"] = classify
    return verdict


def format_verdict_for_prompt(v: dict) -> str:
    """Render verdict dict as authoritative prompt block for LLM.

    Empty / falsy verdict -> empty string (openai_helper skips the block).
    """
    if not v:
        return ""
    # User will fill in formatter once sub-engines populate verdict dict.
    return ""


def extract_window_str(v: dict) -> str:
    """Extract human-readable timing window string from verdict.

    Used by openai_helper to surface the engine's locked window
    (e.g. "April 2027 to August 2028"). Empty when timing engine
    has not yet computed a window.
    """
    if not v:
        return ""
    nw = v.get("next_window") or {}
    if not nw:
        return ""
    # User will fill in the human-readable formatter (e.g. _ym_to_human).
    return ""


def extract_alt_window_str(v: dict) -> str:
    """Extract alternate (fallback) window string from verdict.

    Empty when no alternate window is available.
    """
    if not v:
        return ""
    return ""


# Make these names importable via `from marriage_engine import ...`
__all__ = [
    "assess_marriage",
    "format_verdict_for_prompt",
    "extract_window_str",
    "extract_alt_window_str",
]
