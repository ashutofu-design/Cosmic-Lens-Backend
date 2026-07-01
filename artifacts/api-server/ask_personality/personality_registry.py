"""Self personality / looks / swabhav static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"personality_nature", "self_appearance", "general_personality"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"personality|swabhav|nature|character|kaun\s+hu|who\s+am\s+i|"
    r"handsome|beautiful|good\s+looking|attractive|surat|look|looks|"
    r"mera\s+swabhav|meri?\s+nature|main\s+kaisa"
    r")\b"
)
_NATIVE_RX = re.compile(
    r"(?ix)\b(mere?\s+(?:bare|baare)|about\s+me|mujhe?\s+baare|kuch\s+batao)\b"
)
_DOMAIN_RX = re.compile(
    r"(?ix)\b(shaadi|career|health|paisa|luck|dost|bhai|property|visa)\b"
)


def is_personality_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or TIMING_RX.search(q):
        return False
    if _NATIVE_RX.search(q) and not _SCOPE_RX.search(q):
        return False
    if _DOMAIN_RX.search(q) and not _SCOPE_RX.search(q):
        return False
    if not _SCOPE_RX.search(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("personality", "self", "native") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_personality_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(handsome|beautiful|attractive|look|looks|surat)\b", q):
        return "self_appearance"
    if re.search(r"(?ix)\b(personality|swabhav|nature|character|kaun\s+hu)\b", q):
        return "personality_nature"
    return "general_personality"
