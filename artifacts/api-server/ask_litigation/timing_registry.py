"""Litigation timing routing — case/bail/verdict WHEN questions."""
from __future__ import annotations

from typing import Optional

from ask_litigation.litigation_registry import is_litigation_timing_question as _lit_timing


def is_litigation_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "litigation" and llm_intent.get("is_timing"):
            return True
    try:
        from ask_litigation.litigation_registry import is_career_police_job_question  # type: ignore

        if is_career_police_job_question(q):
            return False
    except Exception:
        pass
    return _lit_timing(q)
