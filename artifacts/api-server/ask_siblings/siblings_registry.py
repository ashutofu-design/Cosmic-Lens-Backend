"""Siblings / bhai-behen static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"elder_sibling", "younger_sibling", "sibling_bond", "general_siblings"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"bhai|behen|behan|sibling|siblings|brother|sister|"
    r"bhai\s*behen|bhai-behen|bahan|bhain"
    r")\b"
)
_ELDER_RX = re.compile(r"(?ix)\b(bade?\s+bhai|badi\s+behen|elder\s+sibling)\b")
_YOUNGER_RX = re.compile(r"(?ix)\b(chhot[ae]\s+bhai|choti\s+behen|younger\s+sibling)\b")
_BOND_RX = re.compile(r"(?ix)\b(rishta|relation|supportive|ladai|fight|bond|saath)\b")


def is_siblings_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if re.search(r"(?ix)\b(cousin|mama|mami|chacha|mausi|relative|rishtedar)\b", q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("siblings", "family") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_siblings_archetype(question: str) -> str:
    q = (question or "").strip()
    if _ELDER_RX.search(q):
        return "elder_sibling"
    if _YOUNGER_RX.search(q):
        return "younger_sibling"
    if _BOND_RX.search(q):
        return "sibling_bond"
    return "general_siblings"
