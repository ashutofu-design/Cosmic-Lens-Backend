"""
love_engine.py — LEAN STUB (Phase 2.8.24)

The original 3454-line love_engine.py was permanently deleted per user
direction. Reason: bloat (Vargottam scoring, Argala chains, SAV maps,
KP per-planet trees, spouse-description blocks, Saturn-transit math,
etc.) was being computed deterministically when the LLM (with full
locked-facts whole-kundli context) was already producing higher-quality
love verdicts. The 3 IRREDUCIBLE love-engine cores are:

  1. CLASSIFY  — is the question about LOVE vs marriage vs general?
  2. VERDICT   — score + window for a love question (if any)
  3. TONE      — brand-safety tone rules for love responses

This stub preserves the EXACT 5 public symbols that openai_helper.py
imports (assess_love, format_verdict_for_prompt, extract_window_str,
classify_love_question, LOVE_TONE_RULES) so no openai_helper.py changes
are needed. All callable stubs return empty/neutral defaults — when
empty the openai_helper try/except path falls through gracefully and
the LLM handles the love question via the whole-kundli context.

LOVE_TONE_RULES is intentionally kept as a small but meaningful tuple
of brand-safety floors (no breakup-encouragement, no toxic-trait
labels, etc.) so the L14224 fallback OR this engine import yields the
same minimum tone floor — preserving brand safety even with the lean
engine.

Future: when love_or_arrange.py classifier (in marriage_engine package)
matures, a fuller love-question engine can be re-added here OR this
stub can be reconnected to a richer scoring path.
"""

from __future__ import annotations
from typing import Any


# ── Public constant: brand-safety floor for love responses ────────────────
LOVE_TONE_RULES: tuple = (
    "Never encourage breakup or separation; offer perspective only.",
    "Do not label a partner with toxic-trait diagnoses.",
    "Avoid blaming the user or their partner; describe pattern, not fault.",
    "Honour user's emotional state — empathise before any chart-talk.",
    "If question is purely emotional, give emotional-first reply (no jargon).",
    "Never promise love-marriage timing as certainty; give phrasing like 'window'.",
)


# ── Public function: classify a question's love-relevance ─────────────────
def classify_love_question(text: str, *args: Any, **kwargs: Any) -> str:
    """STUB. Returns 'general' so the openai_helper love path falls through
    to the LLM whole-kundli flow. Original returned a bucket like 'crush',
    'breakup', 'compatibility', 'soulmate', etc. — re-add when needed."""
    return "general"


# ── Public function: deterministic love verdict ───────────────────────────
def assess_love(kundli: dict, intel: dict, kp: dict, birth: Any,
                question: str = "", *args: Any, **kwargs: Any) -> dict:
    """STUB. Returns {} so openai_helper.py's
    `if love_verdict_obj:` check skips the love-block path and the LLM
    answers from whole-kundli context. Original returned a verdict dict
    with keys: question_type, verdict, score, natal_promise_score,
    current_trigger_score, window, dasha_window, etc."""
    return {}


# ── Public function: format verdict for LLM prompt injection ──────────────
def format_verdict_for_prompt(verdict: dict, *args: Any, **kwargs: Any) -> str:
    """STUB. Returns '' since assess_love returns {}. Original formatted
    the verdict dict into a multi-line LOVE_FACTS prompt block."""
    return ""


# ── Public function: extract human-readable timing window ─────────────────
def extract_window_str(verdict: dict, *args: Any, **kwargs: Any) -> str:
    """STUB. Returns '' since assess_love returns {}. Original extracted
    a human-readable window like 'Aug 2026 - Mar 2027' from the verdict's
    dasha+transit intersection."""
    return ""


# ── Sentinel for callers that introspect ──────────────────────────────────
__all__ = [
    "LOVE_TONE_RULES",
    "classify_love_question",
    "assess_love",
    "format_verdict_for_prompt",
    "extract_window_str",
]
