"""
Face PDF pipeline — delegates to artifact_pipeline (L4 bypass, L3 render-only).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .artifact_pipeline import run_artifact_pdf_pipeline


def run_face_pdf_pipeline(
    *,
    session_id: str,
    lang: str,
    cached_session: Dict[str, Any],
    assemble_report: Callable,
    render_pdf: Callable,
    report_cache_mod: Any,
    user_id: int = 0,
    name_override: Optional[str] = None,
    analysis_id: Optional[str] = None,
    emit_progress: bool = True,
    user_plan: Optional[str] = None,
    rerender_only: bool = False,
) -> Dict[str, Any]:
    """
    assemble_report param kept for API compatibility — not called on L3/L4 hits.
    """
    del assemble_report  # artifact-first path
    return run_artifact_pdf_pipeline(
        session_id=session_id,
        lang=lang,
        cached_session=cached_session,
        render_pdf=render_pdf,
        report_cache_mod=report_cache_mod,
        user_id=user_id,
        name_override=name_override,
        analysis_id=analysis_id,
        user_plan=user_plan,
        emit_progress=emit_progress,
        rerender_only=rerender_only,
    )
