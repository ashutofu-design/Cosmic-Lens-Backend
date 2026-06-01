"""
Celery task: Face Reading PDF generation (assemble + AI + render).
"""
from __future__ import annotations

import logging
import os
import traceback

from celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="face.generate_pdf_report",
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    max_retries=int(os.environ.get("FACE_PDF_MAX_RETRIES", "3")),
    acks_late=True,
)
def generate_face_pdf_report(self, payload: dict):
    """
    payload: session_id, lang, analysis_id, user_id, name_override?, job_id
    """
    from vedic.face_reading import face_cache as _fc
    from vedic.face_reading import session_cache
    from vedic.face_reading.pdf_pipeline import run_face_pdf_pipeline
    from vedic.face_reading.pdf_report import render_pdf
    from vedic.face_reading.progress_events import emit
    from vedic.face_reading.report_async import job_id
    import report_cache as _rc

    session_id = payload["session_id"]
    lang = payload["lang"]
    analysis_id = payload.get("analysis_id") or ""
    user_id = int(payload.get("user_id") or 0)
    name_override = payload.get("name_override")
    rerender_only = bool(payload.get("rerender_only"))
    user_plan = payload.get("user_plan")
    jid = payload.get("job_id") or job_id(session_id, lang)
    tid = self.request.id

    _fc.set_pdf_job(
        session_id,
        lang,
        "processing",
        analysis_id=analysis_id,
        task_id=tid,
        job_id=jid,
        celery_retries=self.request.retries,
    )
    emit(
        jid,
        "worker_start",
        8,
        message=f"Worker {tid[:8]} started",
        task_id=tid,
        retry=self.request.retries,
    )

    cached = session_cache.get(session_id)
    if not cached or "report_payload" not in cached:
        emit(jid, "failed", 0, status="failed", message="session_expired")
        _fc.set_pdf_job(
            session_id,
            lang,
            "failed",
            detail="no_report_in_session",
            analysis_id=analysis_id,
        )
        if analysis_id:
            _fc.release_pdf_lock(analysis_id, lang)
        return {"ok": False, "error": "no_report_in_session"}

    try:
        result = run_face_pdf_pipeline(
            session_id=session_id,
            lang=lang,
            cached_session=cached,
            assemble_report=None,
            render_pdf=render_pdf,
            report_cache_mod=_rc,
            user_id=user_id,
            name_override=name_override,
            analysis_id=analysis_id,
            emit_progress=True,
            user_plan=user_plan,
            rerender_only=rerender_only,
        )
        session_cache.put(session_id, cached)

        if not result.get("ok"):
            detail = result.get("detail") or result.get("error")
            emit(jid, "failed", 0, status="failed", message=str(detail))
            _fc.set_pdf_job(session_id, lang, "failed", detail=detail, analysis_id=analysis_id)
            if analysis_id:
                _fc.release_pdf_lock(analysis_id, lang)
            raise RuntimeError(detail or "pdf_pipeline_failed")

        _fc.set_pdf_job(
            session_id,
            lang,
            "ready",
            analysis_id=analysis_id,
            ledger_id=result.get("ledger_id"),
            cache_source=result.get("cache_source"),
        )
        return {
            "ok": True,
            "ledger_id": result.get("ledger_id"),
            "filename": result.get("filename"),
            "cache_source": result.get("cache_source"),
        }
    except Exception as exc:
        log.exception("[celery] face PDF failed session=%s", session_id[:8])
        if self.request.retries >= self.max_retries:
            emit(
                jid,
                "failed",
                0,
                status="failed",
                message=str(exc),
                traceback=traceback.format_exc()[-500:],
            )
            _fc.set_pdf_job(
                session_id,
                lang,
                "failed",
                detail=str(exc),
                analysis_id=analysis_id,
            )
            if analysis_id:
                _fc.release_pdf_lock(analysis_id, lang)
        raise
    finally:
        if analysis_id:
            try:
                st = _fc.get_pdf_job(session_id, lang) or {}
                if st.get("status") in ("ready", "failed"):
                    _fc.release_pdf_lock(analysis_id, lang)
            except Exception:
                pass
