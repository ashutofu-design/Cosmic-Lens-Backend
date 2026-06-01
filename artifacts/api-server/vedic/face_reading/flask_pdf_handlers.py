"""
Flask handlers for Face Reading PDF — sync, async (Celery), SSE, WebSocket.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from flask import Response, jsonify, request


def _stream_pdf(pdf_bytes: bytes, filename: str, cache_header: str) -> Response:
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "private, no-cache",
            "X-Face-Cache": cache_header,
        },
    )


def _pdf_meta_response(analysis_id: str, lang: str) -> Optional[Response]:
    """L4 true bypass — zero assemble / AI / render."""
    from .pdf_registry import try_bypass

    artifact = try_bypass(analysis_id, lang, load_bytes=True)
    if not artifact or not artifact.pdf_bytes:
        return None
    return _stream_pdf(
        artifact.pdf_bytes,
        artifact.filename,
        artifact.cache_tier,
    )


def handle_report_pdf_inner(
    *,
    session_id: str,
    session_cache,
    assemble_report,
    render_pdf,
    report_cache_mod,
    auth_user,
    app_logger,
) -> Any:
    from . import face_cache as _face_cache
    from .pdf_pipeline import run_face_pdf_pipeline
    from .report_async import (
        celery_available,
        enqueue_pdf_job,
        get_job_status,
        normalize_lang,
        pdf_async_enabled,
        status_urls,
        wait_for_ready,
    )

    cached = session_cache.get(session_id)
    if not cached or "report_payload" not in cached:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "no_report_in_session — analyze ko pehle run karo, fir same session_id se PDF maango",
                }
            ),
            404,
        )

    name_override = request.values.get("name")
    payload = cached["report_payload"]
    person = dict(payload.get("person") or {})
    if name_override:
        person["name"] = name_override

    analysis_id = (
        cached.get("analysis_id")
        or payload.get("analysis_id")
        or _face_cache.new_analysis_id()
    )
    lang = normalize_lang(request.values.get("language") or "hinglish")
    user_id = auth_user.id if auth_user else 0
    force_sync = (request.values.get("sync") or "").strip().lower() in (
        "1", "true", "yes",
    )
    wait_mode = (request.values.get("wait") or "").strip().lower() in (
        "1", "true", "yes",
    )

    # L4 true bypass (no assemble_report, no OpenAI, no rerender)
    if analysis_id and not (request.values.get("rerender") or "").strip() in (
        "1", "true", "yes",
    ):
        hit = _pdf_meta_response(analysis_id, lang)
        if hit:
            app_logger.info(
                "[REPORT_GEN] L4 PDF bypass analysis=%s lang=%s",
                analysis_id[:8],
                lang,
            )
            return hit

    from . import face_cache as _fc

    # Cover rename only → L3 + render, no AI
    rerender_only = bool(name_override) and bool(
        _fc.get_narration_versioned(analysis_id, lang)
    )

    user_plan = str(getattr(auth_user, "plan", "") or "") if auth_user else None

    use_async = pdf_async_enabled() and not force_sync
    if (
        not use_async
        and not force_sync
        and (os.environ.get("FACE_PDF_ASYNC") or "1").strip().lower()
        not in ("0", "false", "off")
    ):
        app_logger.info(
            "[REPORT_GEN] Celery worker unavailable — sync PDF session=%s",
            session_id[:8],
        )

    if use_async:
        job = _face_cache.get_pdf_job(session_id, lang) or {}
        st = job.get("status")

        if st == "ready" and analysis_id:
            hit = _pdf_meta_response(analysis_id, lang)
            if hit:
                return hit

        if st in ("queued", "processing") or job:
            if wait_mode:
                final = wait_for_ready(
                    session_id,
                    lang,
                    timeout_seconds=float(
                        os.environ.get("FACE_PDF_WAIT_TIMEOUT", "120")
                    ),
                )
                if final.get("status") == "ready":
                    hit = _pdf_meta_response(analysis_id, lang)
                    if hit:
                        return hit
                if final.get("status") == "failed":
                    return (
                        jsonify(
                            {
                                "ok": False,
                                "error": "pdf_job_failed",
                                "detail": final.get("detail"),
                            }
                        ),
                        500,
                    )
                return (
                    jsonify({"ok": False, "error": "pdf_job_timeout"}),
                    504,
                )

            if st not in ("queued", "processing", "ready"):
                enqueue_pdf_job(
                    session_id=session_id,
                    lang=lang,
                    analysis_id=analysis_id,
                    user_id=user_id,
                    name_override=name_override,
                    rerender_only=rerender_only,
                    user_plan=user_plan,
                )
            elif st in ("queued", "processing"):
                pass  # already running

        else:
            enqueue_pdf_job(
                session_id=session_id,
                lang=lang,
                analysis_id=analysis_id,
                user_id=user_id,
                name_override=name_override,
                rerender_only=rerender_only,
                user_plan=user_plan,
            )

        urls = status_urls(session_id, lang, request.url_root.rstrip("/"))
        job_st = get_job_status(session_id, lang)
        return (
            jsonify(
                {
                    "ok": True,
                    "async": True,
                    "status": job_st.get("status", "queued"),
                    **urls,
                    "progress": job_st.get("progress"),
                    "poll_interval_ms": int(
                        os.environ.get("FACE_PDF_POLL_MS", "800")
                    ),
                    "message": "PDF generation queued — poll status or use events URL",
                }
            ),
            202,
        )

    # ── Synchronous path (async off or ?sync=1) ───────────────────────────
    _face_cache.set_pdf_job(
        session_id, lang, "processing", analysis_id=analysis_id
    )
    user_plan = getattr(auth_user, "plan", None) if auth_user else None
    result = run_face_pdf_pipeline(
        session_id=session_id,
        lang=lang,
        cached_session=cached,
        assemble_report=assemble_report,
        render_pdf=render_pdf,
        report_cache_mod=report_cache_mod,
        user_id=user_id,
        name_override=name_override,
        analysis_id=analysis_id,
        emit_progress=True,
        user_plan=user_plan,
        rerender_only=rerender_only,
    )
    session_cache.put(session_id, cached)

    if not result.get("ok"):
        _face_cache.set_pdf_job(
            session_id,
            lang,
            "failed",
            detail=result.get("detail") or result.get("error"),
        )
        return (
            jsonify(
                {
                    "ok": False,
                    "error": result.get("error", "pdf_render_failed"),
                    "detail": result.get("detail"),
                }
            ),
            500,
        )

    _face_cache.set_pdf_job(session_id, lang, "ready", analysis_id=analysis_id)
    return _stream_pdf(
        result["pdf_bytes"],
        result.get("filename") or "cosmic_lens_face_report.pdf",
        result.get("cache_source") or "fresh",
    )


def handle_report_status(session_id: str, lang: str) -> Any:
    from .report_async import get_job_status, normalize_lang, status_urls

    if not session_id:
        return jsonify({"ok": False, "error": "missing_session_id"}), 400
    st = get_job_status(session_id, lang)
    urls = status_urls(session_id, lang, request.url_root.rstrip("/"))
    return jsonify({**st, **urls}), 200


def handle_report_events_sse(session_id: str, lang: str) -> Response:
    from .progress_events import get_latest, job_id, subscribe
    from .report_async import normalize_lang

    lang = normalize_lang(lang)
    jid = job_id(session_id, lang)
    timeout = float(os.environ.get("FACE_PDF_SSE_TIMEOUT", "120"))

    def generate():
        latest = get_latest(jid)
        if latest:
            yield f"data: {json.dumps(latest, ensure_ascii=False)}\n\n"
            if latest.get("status") in ("ready", "failed"):
                return
        for evt in subscribe(jid, timeout_seconds=timeout):
            yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
            if evt.get("status") in ("ready", "failed"):
                break

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def register_report_ws(sock) -> None:
    """Register WebSocket route on Flask-Sock instance."""
    from urllib.parse import parse_qs

    @sock.route("/api/face_reading/report/ws")
    def face_report_ws(ws):
        from .progress_events import get_latest, job_id, subscribe
        from .report_async import normalize_lang

        qs = ws.environ.get("QUERY_STRING") or ""
        params = {k: (v[0] if v else "") for k, v in parse_qs(qs).items()}
        session_id = params.get("session_id") or ""
        lang = normalize_lang(params.get("language") or "hinglish")
        if not session_id:
            ws.send(json.dumps({"ok": False, "error": "missing_session_id"}))
            return
        jid = job_id(session_id, lang)
        latest = get_latest(jid)
        if latest:
            ws.send(json.dumps(latest, ensure_ascii=False))
            if latest.get("status") in ("ready", "failed"):
                return
        timeout = float(os.environ.get("FACE_PDF_WS_TIMEOUT", "120"))
        for evt in subscribe(jid, timeout_seconds=timeout):
            ws.send(json.dumps(evt, ensure_ascii=False))
            if evt.get("status") in ("ready", "failed"):
                break
