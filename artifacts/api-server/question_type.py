"""P1.2.8 — Unified Question-Type Gate.

ONE deterministic, error-free TIMING vs STATIC classifier. Single source
of truth used by:
  - vedic.validator.timing_validator.is_timing_question (wrapper)
  - openai_helper._phase48_is_timing_question          (wrapper)
  - openai_helper._phase2855_is_timing_question_strict (wrapper)
  - property_focus_routing._detect_property_intent     (TIMING leg)
  - openai_helper ai_ask + ai_ask_stream LLM-intent override

Design rules:
  1. STRICT word-boundary regex. NO substring matching. Avoids legacy
     false-positives like "date" in "update", "din" in "finding",
     "saal" in "asaltam", "tak" in "stake", "year" in "yearn",
     "month" in "6-month-old".
  2. Default = STATIC. If no explicit timing cue, NEVER return TIMING.
     User-rule: "timing tab tak nahi bolna jab tak user na pooche
     kab/when". Conservative bias prevents hallucination of timing
     intent on ambiguous questions like "delay hoga ya early yog?".
  3. Excluded vocab (always STATIC): delay, delayed, early, jaldi,
     late, soon, slow, fast, smooth, friction, matured, nature.
     These describe NATURE/QUALITY of yog, not WHEN.
  4. Excluded bare-token vocab (substring-trap risk): din, saal, tak,
     date, month, year, window, "ke baad" — only match in compound
     forms (kitne din, kis saal, by 2026, etc.).
  5. Deterministic. Same input → same output. No LLM, no randomness.
  6. Killswitch: env UNIFIED_QTYPE_GATE=off reverts wrappers to their
     legacy bodies (for emergency rollback). Default ON.

Public API:
  classify_question_type(q: str) -> "TIMING" | "STATIC"
  is_timing(q: str) -> bool

Telemetry:
  _LAST_DECISION_REASON (module attr) — last matched cue or "no_match",
  used by callers for trace logging.
"""

from __future__ import annotations
import os
import re
from typing import Literal

_QType = Literal["TIMING", "STATIC"]

# ── Master TIMING vocabulary — strict word-boundary regex ────────────────
# Composite of every UNAMBIGUOUS timing cue from the 4 legacy classifiers,
# minus the substring-trap tokens (din/saal/tak/date/month/year/window).
# Multi-word phrases use [\s\-]? for separator flexibility.
_TIMING_RX = re.compile(
    r"(?ix)"
    r"\b("
    # ── Hindi/Hinglish "kab" family — when?
    r"kab|"
    r"kab[\s\-]?tak|kab[\s\-]?hoga|kab[\s\-]?hogi|"
    r"kab[\s\-]?milega|kab[\s\-]?milegi|"
    r"kabhi[\s\-]?kab|"
    # ── "kis/konse/kaunse + saal/mahine"
    r"kis[\s\-]?saal|kis[\s\-]?mahine|kis[\s\-]?din|"
    r"konse[\s\-]?saal|konse[\s\-]?mahine|"
    r"kaunse[\s\-]?saal|kaunse[\s\-]?mahine|"
    # ── "kitne/kitna + duration"
    r"kitne[\s\-]?saal|kitne[\s\-]?mahine|kitne[\s\-]?din|"
    r"kitne[\s\-]?hafte|kitne[\s\-]?time|kitna[\s\-]?time|"
    # ── English "when/how soon/how long/what year/which month"
    r"when|by[\s\-]?when|how[\s\-]?soon|how[\s\-]?long|"
    r"what[\s\-]?year|which[\s\-]?year|"
    r"what[\s\-]?month|which[\s\-]?month|"
    # ── "timing/date/year/month OF something"
    r"timing[\s\-]?of|date[\s\-]?of|year[\s\-]?of|month[\s\-]?of|"
    # ── Standalone time-process tokens (full word only)
    r"timing|timeline|schedule|deadline|muhurat|muhurta|"
    # ── Future-window phrases (Hinglish + English)
    r"agle[\s\-]?(?:saal|mahine|hafte|year|month|week)|"
    r"is[\s\-]?(?:saal|mahine|hafte)[\s\-]?(?:me|mein|main)?|"
    r"this[\s\-]?year|"
    r"next[\s\-]?(?:year|month|week)|"
    r"upcoming|near[\s\-]?future|"
    r"exact[\s\-]?date|tareekh|tarikh|"
    # ── "by <month> [year]" / "by <YYYY>"
    r"by[\s\-]?(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)|"
    r"by[\s\-]?(?:19|20|21)\d{2}|"
    # ── Immediate-time
    r"abhi|turant"
    r")\b"
)

# Exposed for unit-test introspection / debug only.
_LAST_DECISION_REASON: str = "init"


def _gate_enabled() -> bool:
    """Killswitch reader. Default ON. Set UNIFIED_QTYPE_GATE=off to
    fall back to legacy classifiers byte-identically."""
    return (os.environ.get("UNIFIED_QTYPE_GATE") or "on").strip().lower() != "off"


def classify_question_type(question: str) -> _QType:
    """THE single TIMING vs STATIC gate.

    Returns "TIMING" only when the question contains an explicit,
    word-boundary-bounded timing cue. All other cases (including
    "delay", "early", "jaldi", "late", and ambiguous prose) return
    "STATIC".

    Robust to None / non-str / empty input → STATIC.
    """
    global _LAST_DECISION_REASON
    if not isinstance(question, str) or not question.strip():
        _LAST_DECISION_REASON = "empty_or_non_str"
        return "STATIC"
    m = _TIMING_RX.search(question)
    if m is not None:
        _LAST_DECISION_REASON = f"timing_cue:{m.group(0).lower()}"
        return "TIMING"
    _LAST_DECISION_REASON = "no_timing_cue"
    return "STATIC"


def is_timing(question: str) -> bool:
    """Convenience boolean wrapper. Equivalent to
    classify_question_type(q) == 'TIMING'."""
    return classify_question_type(question) == "TIMING"


__all__ = [
    "classify_question_type",
    "is_timing",
    "_gate_enabled",
    "_LAST_DECISION_REASON",
    "_TIMING_RX",
]
