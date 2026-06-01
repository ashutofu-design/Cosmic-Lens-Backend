"""
Artifact-first PDF pipeline — L4 → L3 → L2 → render.

Never calls assemble_report() when L3/L4 satisfied.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, Optional

from . import face_cache as _fc
from .pdf_registry import PdfArtifact, register as register_pdf, try_bypass
from .progress_events import emit, job_id
from .report_version import NARRATION_VERSION, PDF_RENDER_VERSION

log = logging.getLogger(__name__)


def hydrate_report_for_render(
    report: Dict[str, Any],
    payload: Dict[str, Any],
    *,
    cached_session: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    L3/L1 narration cache strips engines — merge from analyze payload for PDF charts/map.
    """
    report = dict(report)
    engines = payload.get("engines") or (cached_session or {}).get("report_payload", {}).get(
        "engines"
    )
    if engines and not report.get("engines"):
        report["engines"] = engines
    analysis_id = payload.get("analysis_id") or (cached_session or {}).get("analysis_id")
    if not report.get("engines") and analysis_id:
        try:
            snap = _fc.get_analysis(analysis_id)
            if isinstance(snap, dict) and snap.get("engines"):
                report["engines"] = snap["engines"]
        except Exception:
            pass
    if payload.get("synthesis") and not report.get("synthesis"):
        report["synthesis"] = payload.get("synthesis")
    if payload.get("front_quality"):
        report["front_quality"] = payload.get("front_quality")
    if not report.get("appendix_sections"):
        try:
            from .face_report_blocks import appendix_sections, use_12_block_layout

            if use_12_block_layout() and payload.get("sections"):
                report["appendix_sections"] = appendix_sections(payload["sections"])
        except Exception:
            pass
    return report


def apply_cover_overlay(report: Dict[str, Any], person: Dict[str, Any], name_override: Optional[str]) -> Dict[str, Any]:
    """Rename / cover tweaks without AI."""
    report = dict(report)
    p = dict(person or {})
    if name_override:
        p["name"] = name_override
    cover = dict(report.get("cover") or {})
    cover["name"] = p.get("name") or cover.get("name") or "Insan"
    report["cover"] = cover
    return report


def build_narrated_report(
    *,
    sections: Dict[str, Any],
    engines: Dict[str, Any],
    person: Dict[str, Any],
    lang: str,
    front_quality: Optional[Dict] = None,
    front_image_bytes: Optional[bytes] = None,
    front_points_norm: Optional[list] = None,
    session_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    user_id: int = 0,
    user_plan: Optional[str] = None,
    force_template: bool = False,
) -> tuple[Dict[str, Any], str]:
    """
    L3 narration cache or skeleton + budgeted AI enrich.
    Returns (report_dict, cache_source).
    """
    from .narrator import build_report_skeleton, enrich_report_narration

    if analysis_id:
        cached = _fc.get_narration_versioned(analysis_id, lang)
        if cached:
            log.info("[artifact] L3 narration HIT %s/%s", analysis_id[:8], lang)
            return dict(cached), "L3-narration"

    skeleton = build_report_skeleton(
        sections,
        engines,
        person=person,
        front_quality=front_quality,
        front_image_bytes=front_image_bytes,
        front_points_norm=front_points_norm,
        language=lang,
    )

    enrich_report_narration(
        skeleton,
        sections=sections,
        engines=engines,
        person=person,
        lang=lang,
        session_id=session_id,
        analysis_id=analysis_id,
        user_id=user_id,
        user_plan=user_plan,
        force_template=force_template,
    )

    if analysis_id:
        _fc.put_narration(
            analysis_id,
            lang,
            skeleton,
            narration_version=NARRATION_VERSION,
            render_version=PDF_RENDER_VERSION,
        )

    return skeleton, "L2-fresh-narration"


def render_and_register_pdf(
    report: Dict[str, Any],
    *,
    session_id: str,
    lang: str,
    analysis_id: str,
    user_id: int,
    person: Dict[str, Any],
    render_pdf: Callable,
    report_cache_mod: Any,
    cache_source: str,
) -> Dict[str, Any]:
    """ReportLab render + L4 registry."""
    safe_name = (
        re.sub(r"[^a-zA-Z0-9_-]+", "_", (person.get("name") or "report"))[:40]
        or "report"
    )
    filename = f"cosmic_lens_face_report_{safe_name}.pdf"

    pdf_bytes, render_err = report_cache_mod.safe_render(
        f"face_reading user={user_id}",
        lambda: render_pdf(report),
    )
    if render_err or not pdf_bytes:
        return {
            "ok": False,
            "error": "pdf_render_failed",
            "detail": render_err or "empty",
        }

    ledger_id = report_cache_mod.save(
        user_id,
        "face_reading",
        "Face Reading Report",
        {
            "name": person.get("name", ""),
            "lang": lang,
            "session": session_id,
            "analysis_id": analysis_id,
        },
        pdf_bytes,
        filename,
    )
    if analysis_id and ledger_id:
        path = report_cache_mod.path_for_id(ledger_id)
        register_pdf(
            analysis_id,
            lang,
            ledger_id=ledger_id,
            path=path,
            filename=filename,
            size_bytes=len(pdf_bytes),
            narration_version=NARRATION_VERSION,
        )

    return {
        "ok": True,
        "pdf_bytes": pdf_bytes,
        "filename": filename,
        "ledger_id": ledger_id,
        "cache_source": cache_source,
        "analysis_id": analysis_id,
    }


def run_artifact_pdf_pipeline(
    *,
    session_id: str,
    lang: str,
    cached_session: Dict[str, Any],
    render_pdf: Callable,
    report_cache_mod: Any,
    user_id: int = 0,
    name_override: Optional[str] = None,
    analysis_id: Optional[str] = None,
    user_plan: Optional[str] = None,
    emit_progress: bool = True,
    rerender_only: bool = False,
) -> Dict[str, Any]:
    """
    Target flow:
      L4 PDF bypass → return
      L3 narration → render only
      else → Pass A/B (budgeted) → render → L4 register
    """
    jid = job_id(session_id, lang)
    payload = cached_session.get("report_payload") or {}
    person = dict(payload.get("person") or {})
    if name_override:
        person["name"] = name_override

    analysis_id = (
        analysis_id
        or cached_session.get("analysis_id")
        or payload.get("analysis_id")
        or _fc.new_analysis_id()
    )

    _front_bytes = cached_session.get("front_image_bytes") or payload.get("front_image_bytes")
    _front_pts = payload.get("front_points_norm")

    def _prog(stage: str, pct: int, msg: str = "", **extra):
        if emit_progress:
            emit(jid, stage, pct, message=msg, extra=extra)

    # ── L4 true bypass ─────────────────────────────────────────────────────
    _prog("cache_check", 3, "L4 PDF artifact check")
    artifact = try_bypass(analysis_id, lang)
    if artifact and artifact.pdf_bytes and not rerender_only:
        _prog("ready", 100, "L4 PDF bypass", status="ready", tier="L4")
        return {
            "ok": True,
            "pdf_bytes": artifact.pdf_bytes,
            "filename": artifact.filename,
            "ledger_id": artifact.ledger_id,
            "cache_source": artifact.cache_tier,
            "analysis_id": analysis_id,
            "bypass": True,
        }

    # ── L3 narration → render only (no assemble_report, no AI) ─────────────
    report = None
    narr_source = ""
    if analysis_id and not rerender_only:
        report = _fc.get_narration_versioned(analysis_id, lang)
        if report:
            narr_source = "L3-narration"

    if report is None:
        _rlc = cached_session.setdefault("_report_lang_cache", {})
        cached_lang = _rlc.get(lang)
        if isinstance(cached_lang, dict) and cached_lang.get("_narration_version") == NARRATION_VERSION:
            report = cached_lang
            narr_source = "L1-session-narration"

    if report is None:
        _prog("narration", 20, "Building narration (budgeted AI)")
        report, narr_source = build_narrated_report(
            sections=payload["sections"],
            engines=payload["engines"],
            person=person,
            lang=lang,
            front_quality=payload.get("front_quality"),
            front_image_bytes=_front_bytes,
            front_points_norm=_front_pts,
            session_id=session_id,
            analysis_id=analysis_id,
            user_id=user_id,
            user_plan=user_plan,
        )
        _rlc = cached_session.setdefault("_report_lang_cache", {})
        report["_narration_version"] = NARRATION_VERSION
        _rlc[lang] = report
    else:
        _prog("narration", 20, f"Narration cache ({narr_source}) — no AI")

    report = hydrate_report_for_render(report, payload, cached_session=cached_session)
    report = apply_cover_overlay(report, person, name_override)
    report["front_image_bytes"] = _front_bytes
    report["front_points_norm"] = _front_pts

    _prog("render", 72, "Rendering PDF only")
    result = render_and_register_pdf(
        report,
        session_id=session_id,
        lang=lang,
        analysis_id=analysis_id,
        user_id=user_id,
        person=person,
        render_pdf=render_pdf,
        report_cache_mod=report_cache_mod,
        cache_source=narr_source or "render-only",
    )
    if result.get("ok"):
        _prog("ready", 100, "PDF ready", status="ready", tier="L4-new")
    return result
