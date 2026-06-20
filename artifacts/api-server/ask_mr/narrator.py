"""Template replies for simple MR engines (skip LLM when deterministic enough)."""

from __future__ import annotations

from .types import EngineResult


def render_template(result: EngineResult) -> str | None:
    """Return user-facing text when skip_llm is set; else None."""
    if not result.skip_llm or not (result.template_text or "").strip():
        return None
    return result.template_text.strip()


def build_manglik_template(result: EngineResult) -> str:
    is_yes = bool((result.checks or {}).get("is_manglik"))
    if is_yes:
        return (
            "Haan — aapke chart mein manglik pattern dikhta hai. "
            "Iska matlab gussa ya impulse ko sambhalna zaroori ho sakta hai, "
            "lekin yeh seedha barbaadi nahi hoti. "
            "Patience aur clear baat se rishta smooth ho sakta hai."
        )
    return (
        "Nahi — classic manglik position active nahi dikhti. "
        "Phir bhi overall rishta chart ke baaki signals se decide hota hai."
    )
