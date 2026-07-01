"""Fame / reputation / social image static scope (non-timing)."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({
    "fame_potential",
    "reputation_image",
    "social_media_fame",
    "general_fame",
})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"fame|famous|celebrity|viral|social\s+media|instagram|youtube|tiktok|"
    r"influencer|followers|subscribers|recognition|public\s+image|"
    r"reputation|naam\s+chalega|name\s+chalega|limelight|popular|popularity|"
    r"award|samman|izzat|bad\s+naam|defamation|neta|political|leadership"
    r")\b"
)
_CAREER_ONLY_RX = re.compile(r"(?ix)\b(promotion|naukri|salary|interview|govt\s+job)\b")


def is_fame_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q):
        return False
    try:
        from ask_fame.timing_registry import is_fame_timing_question

        if is_fame_timing_question(q, llm_intent):
            return False
    except Exception:
        if TIMING_RX.search(q):
            return False
    if _CAREER_ONLY_RX.search(q) and not re.search(
        r"(?ix)\b(fame|famous|celebrity|viral|reputation|image)\b", q
    ):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("fame", "recognition", "social_fame") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_fame_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(instagram|youtube|tiktok|viral|influencer|followers)\b", q):
        return "social_media_fame"
    if re.search(r"(?ix)\b(reputation|image|izzat|bad\s+naam|defamation)\b", q):
        return "reputation_image"
    if re.search(r"(?ix)\b(famous|celebrity|fame|naam\s+chalega)\b", q):
        return "fame_potential"
    return "general_fame"
