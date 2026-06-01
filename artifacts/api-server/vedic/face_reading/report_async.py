"""
Async Face PDF — Celery enqueue, status, concurrency.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

from . import face_cache as _fc
from .progress_events import emit, get_latest, job_id

log = logging.getLogger(__name__)


def celery_available() -> bool:
    """Celery package + app import OK."""
    if (os.environ.get("CELERY_ENABLED") or "1").strip().lower() in (
        "0", "false", "off",
    ):
        return False
    try:
        from celery_app import celery_app  # noqa: F401

        return True
    except Exception:
        return False


def celery_worker_available() -> bool:
    """True only if at least one worker responds to ping (not just import)."""
    if not celery_available():
        return False
    try:
        from celery_app import celery_app

        timeout = float(os.environ.get("CELERY_PING_TIMEOUT", "1.5"))
        insp = celery_app.control.inspect(timeout=timeout)
        ping = insp.ping() if insp else None
        if ping:
            log.debug("[report_async] celery workers: %s", list(ping.keys()))
            return True
        stats = insp.stats() if insp else None
        if stats:
            log.debug("[report_async] celery stats workers: %s", list(stats.keys()))
            return True
        log.warning("[report_async] no celery workers — PDF will run sync")
        return False
    except Exception as exc:
        log.warning("[report_async] celery ping failed: %s", exc)
        return False


def pdf_async_enabled() -> bool:
    if (os.environ.get("FACE_PDF_ASYNC") or "1").strip().lower() in (
        "0", "false", "off",
    ):
        return False
    return celery_worker_available()


def normalize_lang(raw: str) -> str:
    lang = (raw or "hinglish").strip().lower()
    if lang in ("english", "eng"):
        return "en"
    if lang in ("hindi", "hin"):
        return "hi"
    if lang in ("hg", "hinglish", "hn"):
        return "hinglish"
    if lang not in ("en", "hi", "hinglish"):
        return "hinglish"
    return lang


def status_urls(session_id: str, lang: str, base_url: str = "") -> Dict[str, str]:
    jid = job_id(session_id, lang)
    q = f"session_id={session_id}&language={lang}"
    root = (base_url or "").rstrip("/")
    return {
        "job_id": jid,
        "status_url": f"{root}/api/face_reading/report/status?{q}",
        "events_sse_url": f"{root}/api/face_reading/report/events?{q}",
        "events_ws_url": (
            f"{root.replace('http', 'ws', 1)}/api/face_reading/report/ws?{q}"
            if root.startswith("http")
            else f"/api/face_reading/report/ws?{q}"
        ),
        "download_url": f"{root}/api/face_reading/report.pdf?{q}",
    }


def enqueue_pdf_job(
    *,
    session_id: str,
    lang: str,
    analysis_id: str,
    user_id: int = 0,
    name_override: Optional[str] = None,
    rerender_only: bool = False,
    user_plan: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Enqueue Celery task (idempotent task_id).
    Returns (celery_task_id, job_state_dict).
    """
    from tasks.face_report_tasks import generate_face_pdf_report

    jid = job_id(session_id, lang)
    tid = _fc.celery_task_id(session_id, lang)

    payload = {
        "session_id": session_id,
        "lang": lang,
        "analysis_id": analysis_id,
        "user_id": user_id,
        "name_override": name_override,
        "job_id": jid,
        "rerender_only": rerender_only,
        "user_plan": user_plan,
    }

    emit(jid, "queued", 2, message="Queued for PDF worker", task_id=tid)

    _fc.set_pdf_job(
        session_id,
        lang,
        "queued",
        analysis_id=analysis_id,
        task_id=tid,
        job_id=jid,
    )

    if not _fc.try_acquire_pdf_lock(analysis_id, lang, tid):
        existing = _fc.get_pdf_job(session_id, lang) or {}
        log.info(
            "[report_async] lock held — reuse job session=%s",
            session_id[:8],
        )
        return tid, existing

    try:
        generate_face_pdf_report.apply_async(
            kwargs={"payload": payload},
            task_id=tid,
            queue=os.environ.get("CELERY_FACE_PDF_QUEUE", "face_pdf"),
        )
    except Exception as exc:
        log.warning("[report_async] apply_async failed: %s", exc)
        _fc.release_pdf_lock(analysis_id, lang)
        _fc.set_pdf_job(session_id, lang, "failed", detail=str(exc), analysis_id=analysis_id)

    return tid, _fc.get_pdf_job(session_id, lang) or {"status": "queued", "task_id": tid}


def get_job_status(session_id: str, lang: str) -> Dict[str, Any]:
    jid = job_id(session_id, lang)
    job = _fc.get_pdf_job(session_id, lang) or {}
    progress = get_latest(jid) or {}
    tid = job.get("task_id") or _fc.celery_task_id(session_id, lang)
    celery_state = None
    if celery_available() and tid:
        try:
            from celery.result import AsyncResult
            from celery_app import celery_app

            celery_state = AsyncResult(tid, app=celery_app).state
        except Exception:
            pass

    status = job.get("status") or progress.get("status") or "unknown"
    if celery_state in ("STARTED", "RETRY") and status == "queued":
        status = "processing"
    if celery_state == "SUCCESS" and status not in ("ready", "failed"):
        status = "ready"
    if celery_state == "FAILURE":
        status = "failed"

    return {
        "ok": True,
        "job_id": jid,
        "status": status,
        "celery_state": celery_state,
        "task_id": tid,
        "progress": progress,
        "analysis_id": job.get("analysis_id"),
        "detail": job.get("detail"),
    }


def wait_for_ready(
    session_id: str,
    lang: str,
    timeout_seconds: float = 120.0,
    poll_interval: float = 0.5,
) -> Dict[str, Any]:
    """Blocking poll for sync-wait mode (?wait=1)."""
    import time

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        st = get_job_status(session_id, lang)
        if st.get("status") == "ready":
            return st
        if st.get("status") == "failed":
            return st
        time.sleep(poll_interval)
    return {"ok": False, "status": "timeout", "error": "pdf_job_timeout"}
