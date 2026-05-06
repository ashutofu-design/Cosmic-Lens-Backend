"""
intent_splitter.py — P1.2.10 (B1)
==================================
Multi-intent orchestrator. Reads domain_splitter hits and decides:
  - 0 hits → MultiIntent=None (downstream pipeline unchanged)
  - 1 hit  → MultiIntent=None (downstream pipeline unchanged)
  - 2+ hits → MultiIntent(primary, secondaries) → engine post-injects a
              deterministic acknowledge line at the END of the LLM answer.

Strategy = B1 ("Primary + Quick Mention"):
  - LLM answers focused on PRIMARY domain (no extra prompt changes needed —
    existing topic-router already focuses the response).
  - Engine appends 1-line ack: "(Aapne shaadi aur job bhi puche the —
    alag se pucho to detail me batata hoon.)"

Public API
----------
    from intent_splitter import analyze, build_acknowledge_line, MultiIntent

    mi = analyze(question)
    if mi:
        ack = build_acknowledge_line(mi.secondaries, lang="hinglish")
        # ack is a 1-line bracketed Hinglish/Hindi/English string

Killswitch: env MULTI_INTENT_SPLIT=off → analyze() always returns None.
"""
from __future__ import annotations

import os
from typing import List, Optional

from domain_splitter import (
    DomainHit, DOMAIN_LABELS, extract_domains,
)


# ── Configuration ───────────────────────────────────────────────────────────
def _env_on(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() not in ("0", "off", "false", "no", "")


SPLITTER_ENABLED: bool = _env_on("MULTI_INTENT_SPLIT", True)

# Maximum secondary domains to mention in the ack line. Beyond 3 reads weird.
_MAX_SECONDARIES: int = 3


# ── MultiIntent ─────────────────────────────────────────────────────────────
class MultiIntent:
    """Result of analyze(). primary = highest-confidence domain."""

    __slots__ = ("primary", "secondaries", "all_hits")

    def __init__(self, primary: str, secondaries: List[str],
                 all_hits: List[DomainHit]):
        self.primary = primary
        self.secondaries = secondaries
        self.all_hits = all_hits

    def __repr__(self) -> str:
        return (f"MultiIntent(primary={self.primary!r}, "
                f"secondaries={self.secondaries!r}, "
                f"n_hits={len(self.all_hits)})")

    def telemetry(self) -> dict:
        return {
            "primary":     self.primary,
            "secondaries": self.secondaries,
            "n_domains":   len(self.all_hits),
            "all_domains": [h.name for h in self.all_hits],
            "phase":       "P1.2.10_B1",
        }


# ── Lang resolution (mirrors question_length_gate convention) ───────────────
def _resolve_lang(lang: Optional[str]) -> str:
    if not lang:
        return "hinglish"
    s = str(lang).strip().lower()
    if s in ("hinglish", "hng", "hinen", "hi-en", "en-hi"):
        return "hinglish"
    if s in ("hi", "hindi", "in", "in-hi"):
        return "hi"
    if s.startswith("en"):
        return "en"
    return "hinglish"


# ── Acknowledge templates per language ──────────────────────────────────────
_ACK_TEMPLATES = {
    "hinglish": {
        # 1 secondary
        1: "📝 *Aapne {a} bhi pucha tha — alag se pucho to usme detail me batata hoon.*",
        # 2 secondaries
        2: "📝 *Aapne {a} aur {b} bhi puche the — har ek pe alag se pucho to detail milegi.*",
        # 3 secondaries
        3: "📝 *Aapne {a}, {b} aur {c} bhi puche the — har ek pe alag se pucho to detail milegi.*",
    },
    "hi": {
        1: "📝 *Aapne {a} bhi poochha tha — alag se pooche to detail me bataunga.*",
        2: "📝 *Aapne {a} aur {b} bhi poochhe the — har ek alag se pooche to detail milegi.*",
        3: "📝 *Aapne {a}, {b} aur {c} bhi poochhe the — har ek alag se pooche to detail milegi.*",
    },
    "en": {
        1: "📝 *You also asked about {a} — please ask separately for a detailed answer.*",
        2: "📝 *You also asked about {a} and {b} — please ask each separately for a detailed answer.*",
        3: "📝 *You also asked about {a}, {b} and {c} — please ask each separately for a detailed answer.*",
    },
}


# ── Public API ──────────────────────────────────────────────────────────────
def analyze(question: str) -> Optional[MultiIntent]:
    """
    Inspect `question` for multi-intent. Returns MultiIntent only if ≥2
    distinct domains detected. Killswitch returns None.
    """
    if not SPLITTER_ENABLED:
        return None
    hits = extract_domains(question or "")
    # Need ≥2 DISTINCT domains
    if len(hits) < 2:
        return None
    primary = hits[0].name
    secondaries = [h.name for h in hits[1:1 + _MAX_SECONDARIES]]
    return MultiIntent(primary=primary, secondaries=secondaries, all_hits=hits)


def build_acknowledge_line(secondaries: List[str],
                           lang: Optional[str] = "hinglish") -> str:
    """
    Build a 1-line acknowledge string for the given secondary domains.
    Returns "" if secondaries is empty or unsupported.

    Example:
        >>> build_acknowledge_line(["marriage", "career"], "hinglish")
        '📝 *Aapne shaadi aur job/career bhi puche the — har ek pe alag se pucho to detail milegi.*'
    """
    if not secondaries:
        return ""
    lang_resolved = _resolve_lang(lang)
    label_map = DOMAIN_LABELS.get(lang_resolved) or DOMAIN_LABELS["hinglish"]
    labels = [label_map.get(s, s) for s in secondaries[:3]]

    n = len(labels)
    template_set = _ACK_TEMPLATES.get(lang_resolved) or _ACK_TEMPLATES["hinglish"]
    template = template_set.get(n)
    if not template:
        return ""

    if n == 1:
        return template.format(a=labels[0])
    if n == 2:
        return template.format(a=labels[0], b=labels[1])
    if n == 3:
        return template.format(a=labels[0], b=labels[1], c=labels[2])
    return ""


def is_already_acknowledged(text: str, secondaries: List[str]) -> bool:
    """
    Heuristic: if the LLM answer already mentions ALL secondary-domain labels
    near the end (last 200 chars) AND uses an "alag se" / "separately" cue,
    skip the post-injection to avoid duplication. Conservative — defaults to
    False so the safety-net line nearly always fires.
    """
    if not text or not secondaries:
        return False
    tail = text[-200:].lower()
    cue_present = any(c in tail for c in (
        "alag se pucho", "alag se pooche", "ask separately",
        "separately for", "alag question",
    ))
    if not cue_present:
        return False
    # Need every secondary label root to appear in tail
    for s in secondaries:
        label_hng = (DOMAIN_LABELS["hinglish"].get(s) or s).split("/")[0].lower()
        if label_hng not in tail:
            return False
    return True


def is_enabled() -> bool:
    """True if MULTI_INTENT_SPLIT killswitch is on (default ON)."""
    return SPLITTER_ENABLED
