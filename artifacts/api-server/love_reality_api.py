"""Love Reality Pro PDF — Flask route registration."""
from __future__ import annotations

from flask import Response, jsonify, request

# Bump when PDF layout/renderer changes — invalidates stale server-side report cache.
LOVE_REALITY_PDF_LAYOUT_VER = "lr_pro_v24_moon_sync_llm"
# Bump to drop all saved Hindi pro-report + polish snapshots (hi only).
LOVE_REALITY_HI_CACHE_VER = "hi_purge_v19_section4_force_llm"


def love_reality_cache_params(lang: str, p1: dict, p2: dict) -> dict:
    import report_cache as _rc
    from vedic.love_reality.love_section_polish import _ASSEMBLY_VER

    cp = _rc.couple_cache_params(lang, p1, p2)
    cp["pdf_layout"] = LOVE_REALITY_PDF_LAYOUT_VER
    cp["polish_assembly"] = _ASSEMBLY_VER
    if (lang or "").strip().lower() == "hi":
        cp["hi_cache_ver"] = LOVE_REALITY_HI_CACHE_VER
    return cp


def _love_reality_cache_params(lang: str, p1: dict, p2: dict) -> dict:
    return love_reality_cache_params(lang, p1, p2)


_PURGED_HI_CACHE_VER: str | None = None


def _purge_hi_server_caches_once() -> None:
    """One-time disk purge when LOVE_REALITY_HI_CACHE_VER bumps."""
    global _PURGED_HI_CACHE_VER
    if _PURGED_HI_CACHE_VER == LOVE_REALITY_HI_CACHE_VER:
        return
    try:
        import love_reality_report_json_cache as _jcache
        import love_reality_polish_snapshot as _psnap

        n_json = _jcache.purge_all_hi_reports()
        n_snap = _psnap.purge_all_hi_snapshots()
        print(
            f"[love_reality] hi cache purge ver={LOVE_REALITY_HI_CACHE_VER} "
            f"json={n_json} snap={n_snap}",
            flush=True,
        )
    except Exception as exc:
        try:
            print(f"[love_reality] hi cache purge failed: {exc}", flush=True)
        except Exception:
            pass
    _PURGED_HI_CACHE_VER = LOVE_REALITY_HI_CACHE_VER


def _enrich_hi_section8_meta(payload: dict) -> dict:
    """Attach section7/8 canonical Hindi bodies + debug for mobile."""
    if not isinstance(payload, dict) or (payload.get("lang") or "").strip().lower() != "hi":
        return payload
    import re
    from vedic.love_reality.app_report_sections import (
        _ANALYSIS_TITLES_HI,
        _blueprint_ready_text,
        _deep_analysis_map,
        _deep_connection_body_from_analysis,
        _moon_sync_ready_text,
    )
    from vedic.love_reality.love_section_polish import (
        _breakup_chapter_body,
        _moon_sync_narrative_body,
        deep_analysis_hi_ready,
        remedies_action_hi_ready,
    )
    from vedic.love_reality.section8_gate import effective_section8_hi_text

    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    p1 = payload.get("page1") if isinstance(payload.get("page1"), dict) else {}
    bu = _breakup_chapter_body(pro)
    moon_narr = _moon_sync_narrative_body(pro)
    moon_body = ""
    for sec in payload.get("app_sections") or []:
        if isinstance(sec, dict) and str(sec.get("id") or "").lower() == "moon":
            moon_body = str(sec.get("body") or "").strip()
            break
    if len(moon_body.split()) < 55:
        moon_body = _moon_sync_ready_text(pro, "hi") or str(
            (payload.get("pdf_context") or {}).get("page5_moon", {}).get("body") or ""
        ).strip()
    s4_hi = ""
    if remedies_action_hi_ready(pro):
        s4_hi = str(pro.get("remedies_action_narrative") or "").strip()
    s5_hi = _blueprint_ready_text(pro, "hi")
    s3_hi = ""
    for sec in payload.get("app_sections") or []:
        if isinstance(sec, dict) and str(sec.get("id") or "").lower() == "deep_connection":
            s3_hi = str(sec.get("body") or "").strip()
            break
    if deep_analysis_hi_ready(pro):
        from_page1 = _deep_connection_body_from_analysis(p1.get("analysis") or [], "hi")
        s3_wc = lambda t: len(str(t or "").split())
        if s3_wc(from_page1) > s3_wc(s3_hi):
            s3_hi = from_page1
        if not s3_hi or s3_wc(s3_hi) < 200:
            da = _deep_analysis_map(pro)
            if da:
                built = _deep_connection_body_from_analysis(
                    [
                        {"title": _ANALYSIS_TITLES_HI.get(k, k), "explanation": v}
                        for k, v in da.items()
                    ],
                    "hi",
                )
                if s3_wc(built) > s3_wc(s3_hi):
                    s3_hi = built
    s7_hi = _moon_sync_ready_text(pro, "hi") or (
        moon_body if len(moon_body.split()) >= 55 else moon_narr
    )
    root_body = ""
    for sec in payload.get("app_sections") or []:
        if isinstance(sec, dict) and str(sec.get("id") or "").lower() == "root_cause":
            root_body = str(sec.get("body") or "").strip()
            break
    if len(root_body.split()) < 80:
        root_body = bu or str(
            (payload.get("pdf_context") or {}).get("page6_root_cause") or ""
        ).strip()
    dbg = {
        "gate_ver": "v13",
        "breakup_words": len(bu.split()),
        "breakup_deva": len(re.findall(r"[\u0900-\u097F]", bu)),
        "root_words": len(root_body.split()),
        "root_deva": len(re.findall(r"[\u0900-\u097F]", root_body)),
        "moon_words": len(s7_hi.split()) if s7_hi else len(moon_body.split()),
        "moon_deva": len(re.findall(r"[\u0900-\u097F]", s7_hi or moon_body or "")),
    }
    s8_hi = effective_section8_hi_text({**payload, "section8_debug": dbg})
    dbg["effective_words"] = len(s8_hi.split()) if s8_hi else 0
    dbg["effective_deva"] = len(re.findall(r"[\u0900-\u097F]", s8_hi or ""))
    dbg["polish_source"] = payload.get("polish_source")
    s4_meta = (pro.get("_meta") or {}).get("section4_remedies") if isinstance(pro.get("_meta"), dict) else {}
    return {
        **payload,
        "hi_cache_ver": LOVE_REALITY_HI_CACHE_VER,
        "section3_hi_body": s3_hi or None,
        "section4_hi_body": s4_hi or None,
        "section4_debug": {
            "words": len(s4_hi.split()) if s4_hi else 0,
            "deva": len(re.findall(r"[\u0900-\u097F]", s4_hi or "")),
            "ready": bool(s4_hi and remedies_action_hi_ready(pro)),
            "llm_source": (s4_meta or {}).get("source") if isinstance(s4_meta, dict) else None,
        },
        "section5_hi_body": s5_hi or None,
        "section7_hi_body": s7_hi or None,
        "section7_debug": {
            "moon_narr_words": len(moon_narr.split()),
            "moon_narr_deva": len(re.findall(r"[\u0900-\u097F]", moon_narr)),
            "moon_body_words": dbg["moon_words"],
            "moon_body_deva": dbg["moon_deva"],
        },
        "section8_hi_body": s8_hi or None,
        "section8_debug": dbg,
    }


def _hi_section4_block_response(payload: dict):
    """412 when Section 4 LLM remedies not ready — no generic fallback report."""
    from vedic.love_reality.section4_gate import section4_hi_load_gate

    ok, reason = section4_hi_load_gate(payload)
    if ok:
        return None
    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    llm_meta = (pro.get("_meta") or {}).get("section4_remedies") if isinstance(pro.get("_meta"), dict) else {}
    return jsonify({
        "error": "section4_not_ready",
        "detail": reason,
        "section": "recommendations",
        "section4_llm": llm_meta or None,
    }), 412


def _hi_script_block_response(payload: dict, lang: str):
    """412 when report is hi_partial — KPI/narrative not fully देवनागरी."""
    if lang != "hi":
        return None
    script = str(payload.get("content_script") or "").strip().lower()
    if script == "hi":
        return None
    detail = (
        "Report poori देवनागरी Hindi nahi bani — KPI ya koi section abhi English/mixed hai. "
        "Mobile dubara LLM chalayega."
    )
    if script == "hi_partial":
        detail = (
            "Report abhi aadhi Hindi hai (hi_partial) — sab KPI labels aur sections "
            "देवनागरी hone chahiye."
        )
    elif script == "en_mismatch":
        detail = "Report English/mixed hai — Hindi localize abhi complete nahi hua."
    return jsonify({
        "error": "hi_not_fully_localized",
        "detail": detail,
        "content_script": script or "unknown",
    }), 412


def _hi_report_block_response(payload: dict, lang: str):
    """Section 4 + Section 8 + full Hindi script gates — cache hits and fresh builds."""
    if lang != "hi":
        return None
    blocked4 = _hi_section4_block_response(payload)
    if blocked4:
        return blocked4
    blocked8 = _hi_section8_block_response(payload)
    if blocked8:
        return blocked8
    return _hi_script_block_response(payload, lang)


def _hi_section8_block_response(payload: dict):
    """412 when Section 8 LLM explanation not ready — exact reason for mobile."""
    from vedic.love_reality.section8_gate import section8_hi_load_gate

    ok, reason = section8_hi_load_gate(payload)
    if ok:
        return None
    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    llm_meta = (pro.get("_meta") or {}).get("section8_breakup") if isinstance(pro.get("_meta"), dict) else {}
    llm_reason = str((llm_meta or {}).get("reason") or "").strip()
    if llm_reason:
        reason = f"{reason} (LLM: {llm_reason})"
    return jsonify({
        "error": "section8_not_ready",
        "detail": reason,
        "section": "root_cause",
        "section8_llm": llm_meta or None,
    }), 412


def _en_saved_report_stale(payload: dict) -> bool:
    """English/Hinglish saved JSON — regenerate when narrative assembly bumps."""
    if not isinstance(payload, dict):
        return True
    from vedic.love_reality.love_section_polish import _ASSEMBLY_VER

    if str(payload.get("polish_assembly") or "").strip() != _ASSEMBLY_VER:
        return True
    return False


def _hi_saved_report_stale(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return True
    if payload.get("polish_source") == "hn_translate":
        return True
    if payload.get("hi_from_hn"):
        return True
    if payload.get("hi_cache_ver") != LOVE_REALITY_HI_CACHE_VER:
        return True
    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    try:
        from vedic.love_reality.love_section_polish import (
            blueprint_section_hi_ready,
            breakup_chapter_hi_ready,
            deep_analysis_hi_ready,
            moon_sync_narrative_hi_ready,
            remedies_action_hi_ready,
        )

        if pro and not breakup_chapter_hi_ready(pro):
            return True
        if pro and not moon_sync_narrative_hi_ready(pro):
            return True
        if pro and not blueprint_section_hi_ready(pro):
            return True
        if pro and not deep_analysis_hi_ready(pro):
            return True
        if pro and not remedies_action_hi_ready(pro):
            return True
    except Exception:
        pass
    return False


def _pdf_layout_headers(*, cache_hit: bool) -> dict[str, str]:
    from love_reality_pdf import get_last_page1_style

    return {
        "X-PDF-Layout-Version": LOVE_REALITY_PDF_LAYOUT_VER,
        "X-PDF-Page1-Style": "cached-previous" if cache_hit else get_last_page1_style(),
    }


def _force_regenerate_requested() -> bool:
    """Skip saved PDF file only — does NOT force a new OpenAI / LLM call."""
    hdr = (request.headers.get("X-Force-Regenerate") or "").strip().lower()
    body = request.get_json(silent=True) or {}
    flag = str(body.get("force_regenerate") or "").strip().lower()
    if hdr in ("1", "true", "yes", "on") or flag in ("1", "true", "yes", "on"):
        return True
    layout_refresh = (request.headers.get("X-PDF-Layout-Refresh") or "").strip().lower()
    if layout_refresh in ("1", "true", "yes", "on"):
        return True
    return False


def _force_llm_requested() -> bool:
    """Force fresh OpenAI polish even if a saved snapshot exists."""
    import os

    hdr = (request.headers.get("X-Force-LLM") or "").strip().lower()
    body = request.get_json(silent=True) or {}
    flag = str(body.get("force_llm") or "").strip().lower()
    if hdr in ("1", "true", "yes", "on") or flag in ("1", "true", "yes", "on"):
        return True

    full_hdr = (request.headers.get("X-Love-Report-Full-Update") or "").strip().lower()
    full_flag = str(body.get("force_update") or "").strip().lower()
    if full_hdr in ("1", "true", "yes", "on") or full_flag in ("1", "true", "yes", "on"):
        return True

    layout_refresh = (request.headers.get("X-PDF-Layout-Refresh") or "").strip().lower()
    if layout_refresh in ("1", "true", "yes", "on"):
        return False

    return (os.environ.get("LOVE_REALITY_FORCE_LLM") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _pro_report_force_llm(data: dict | None = None) -> bool:
    """In-app Update Report — always rerun LLM, never reuse L1/snapshot."""
    payload = data if isinstance(data, dict) else (request.get_json(silent=True) or {})
    if _force_llm_requested():
        return True
    if _force_regenerate_requested():
        return True
    flag = str(payload.get("force_update") or "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    return False


def _relocalize_sections_requested() -> bool:
    """Fast path — re-translate app_sections from saved JSON, no LLM."""
    hdr = (request.headers.get("X-Relocalize-Sections") or "").strip().lower()
    body = request.get_json(silent=True) or {}
    flag = str(body.get("relocalize_sections") or "").strip().lower()
    return hdr in ("1", "true", "yes", "on") or flag in ("1", "true", "yes", "on")


def _pdf_render_only_requested() -> bool:
    """Never call OpenAI — reuse saved polish snapshot or return 412."""
    import os

    hdr = (request.headers.get("X-PDF-Render-Only") or "").strip().lower()
    body = request.get_json(silent=True) or {}
    flag = str(body.get("pdf_render_only") or "").strip().lower()
    if hdr in ("1", "true", "yes", "on") or flag in ("1", "true", "yes", "on"):
        return True
    return (os.environ.get("LOVE_REALITY_PDF_RENDER_ONLY") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _in_app_report_snapshot_requested() -> bool:
    hdr = (request.headers.get("X-In-App-Report-Snapshot") or "").strip().lower()
    body = request.get_json(silent=True) or {}
    flag = str(body.get("in_app_report_snapshot") or "").strip().lower()
    return hdr in ("1", "true", "yes", "on") or flag in ("1", "true", "yes", "on")


def _attach_llm_cost_inr(payload: dict) -> dict:
    """Rounded INR LLM cost for operator UI — no tokens exposed."""
    if not isinstance(payload, dict):
        return payload
    pro = payload.get("pro_premium")
    if not isinstance(pro, dict):
        return payload
    meta = pro.get("_meta")
    if not isinstance(meta, dict):
        return payload
    pg = meta.get("pdf_generation")
    if not isinstance(pg, dict):
        return payload
    try:
        inr = float(pg.get("estimated_cost_inr") or 0)
    except (TypeError, ValueError):
        inr = 0.0
    if inr > 0:
        return {**payload, "llm_cost_inr": int(round(inr))}
    return payload


def _with_app_sections(payload: dict, lang: str) -> dict:
    """In-app scroll sections — backfill LLM gaps + Hindi labels + localize."""
    p1 = payload.get("page1")
    ctx = payload.get("pdf_context")
    pro = payload.get("pro_premium")
    if not isinstance(p1, dict) or not isinstance(ctx, dict):
        return _attach_llm_cost_inr(payload)
    try:
        from vedic.love_reality.app_report_sections import build_localized_app_sections

        sections, script, p1_out, ctx_out = build_localized_app_sections(
            p1, ctx, pro if isinstance(pro, dict) else {}, lang
        )
        return _attach_llm_cost_inr({
            **payload,
            "page1": p1_out,
            "pdf_context": ctx_out,
            "app_sections": sections,
            "content_script": script,
        })
    except Exception as exc:
        try:
            print(f"[love_reality_pro_report] app_sections build failed: {exc}", flush=True)
        except Exception:
            pass
        return _attach_llm_cost_inr({**payload, "content_script": "unknown"})


def _client_report_layout(data: dict) -> tuple[dict | None, dict | None, bool]:
    ctx = data.get("pdf_context")
    page1 = data.get("page1")
    pro = data.get("pro_premium")
    ok = (
        isinstance(ctx, dict)
        and bool(ctx)
        and isinstance(page1, dict)
        and bool(page1)
        and isinstance(pro, dict)
        and bool(pro)
    )
    if not ok:
        return None, None, False
    return ctx, page1, True


def _pro_premium_from_client_report(
    bundle: dict,
    *,
    client_pro: dict,
    lang: str,
    user_id: int,
    p1: dict,
    p2: dict,
) -> tuple[dict | None, str]:
    """Seed polish snapshot from in-app report JSON so PDF matches the scroll view."""
    from vedic.love_reality.pdf_text_safe import sanitize_love_reality_pro_premium
    import love_reality_polish_snapshot as _snap

    pro = sanitize_love_reality_pro_premium(client_pro, bundle, lang=lang)
    if not isinstance(pro, dict) or not pro:
        return None, "client_report_invalid"
    snap_params = _snap.snapshot_params(user_id, lang, p1, p2)
    _snap.save(snap_params, pro)
    return pro, "client_report"


def _resolve_pro_premium(
    bundle: dict,
    *,
    lang: str,
    user_id: int,
    p1: dict,
    p2: dict,
    force_llm: bool = False,
) -> tuple[dict | None, str]:
    """
    Return (pro_premium, source).
    source: polish_snapshot | llm | render_only_miss
    """
    import love_reality_polish_snapshot as _snap
    from vedic.love_reality.premium_polish import polish_love_reality_premium

    snap_params = _snap.snapshot_params(user_id, lang, p1, p2)
    render_only = _pdf_render_only_requested()
    force_llm = bool(force_llm or _force_llm_requested())

    if not force_llm:
        cached = _snap.load(snap_params)
        if cached:
            if lang in ("hn", "hi"):
                from vedic.love_reality.pdf_text_safe import prose_matches_lang

                verdict = str(cached.get("verdict") or "")
                if not prose_matches_lang(verdict, lang):
                    cached = None
            if cached and lang == "hi":
                from vedic.love_reality.love_section_polish import (
                    blueprint_section_hi_ready,
                    breakup_chapter_hi_ready,
                    deep_analysis_hi_ready,
                    moon_sync_narrative_hi_ready,
                    remedies_action_hi_ready,
                )

                if (
                    not breakup_chapter_hi_ready(cached)
                    or not moon_sync_narrative_hi_ready(cached)
                    or not blueprint_section_hi_ready(cached)
                    or not deep_analysis_hi_ready(cached)
                    or not remedies_action_hi_ready(cached)
                ):
                    cached = None
                    force_llm = True
            if cached:
                return cached, "polish_snapshot"

    if render_only:
        return None, "render_only_miss"

    pro = polish_love_reality_premium(bundle, lang=lang, force_llm=force_llm)
    if not isinstance(pro, dict):
        pro = {}
    if pro:
        from vedic.love_reality.love_section_polish import _assembly_depth_ok

        if _assembly_depth_ok(pro):
            from vedic.love_reality.love_section_polish import (
                blueprint_section_hi_ready,
                breakup_chapter_hi_ready,
                deep_analysis_hi_ready,
                moon_sync_narrative_hi_ready,
                remedies_action_hi_ready,
            )

            if lang != "hi" or (
                breakup_chapter_hi_ready(pro)
                and moon_sync_narrative_hi_ready(pro)
                and blueprint_section_hi_ready(pro)
                and deep_analysis_hi_ready(pro)
                and remedies_action_hi_ready(pro)
            ):
                _snap.save(snap_params, pro)
    return pro, "llm"


def register_love_reality_routes(flask_app) -> None:
    """Register Love Reality Pro routes (idempotent per endpoint)."""

    if "love_reality_pro_pdf" not in flask_app.view_functions:

        @flask_app.route("/api/love-reality/pro-pdf", methods=["POST", "OPTIONS", "GET"])
        def love_reality_pro_pdf():
            if request.method == "OPTIONS":
                return "", 204
            if request.method == "GET":
                return jsonify({
                    "ok": True,
                    "endpoint": "love-reality-pro-pdf",
                    "methods": ["POST"],
                }), 200

            data = request.get_json(silent=True) or {}
            if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
                return jsonify({"error": "expected_p1_p2"}), 400

            try:
                from vedic.love_reality.compute_bundle import compute_love_reality_bundle
                from vedic.love_reality.pdf_locale import normalize_love_reality_pdf_lang
                from love_reality_pdf import render_love_reality_pro_pdf
                import report_cache as _rc
                import couple_report_billing as _billing
            except Exception as exc:
                return jsonify({
                    "error": "love_reality_pro_pdf_failed",
                    "detail": f"import_failed: {exc}",
                }), 500

            lang = normalize_love_reality_pdf_lang(data.get("lang"))

            user_id = 0
            uid_hdr = (request.headers.get("X-User-Id") or "").strip()
            if uid_hdr:
                try:
                    from flask_app import get_authed_user

                    auth_user, _err = get_authed_user(int(uid_hdr))
                    if auth_user is not None:
                        user_id = int(auth_user.id)
                except Exception:
                    pass

            if _billing.payment_required() and not _billing.love_reality_pro_free() and not user_id:
                return jsonify(
                    {
                        "error": "auth_required",
                        "message": "Login required to generate Love Reality Pro PDF",
                    }
                ), 401

            client_ctx, client_page1, has_client_layout = _client_report_layout(data)
            app_sections = data.get("app_sections")
            has_app_mirror = isinstance(app_sections, list) and len(app_sections) > 0
            cache_params = _love_reality_cache_params(lang, data["p1"], data["p2"])
            if has_app_mirror:
                cache_params = {**cache_params, "pdf_renderer": "app_mirror"}
                if not has_client_layout:
                    return jsonify({
                        "error": "app_pdf_parity_failed",
                        "detail": (
                            "Report snapshot missing — reload Love Reality Pro on screen, "
                            "then tap Download PDF again."
                        ),
                    }), 412
                try:
                    from vedic.love_reality.app_pdf_parity import validate_wysiwyg_screen_to_pdf

                    parity_err = validate_wysiwyg_screen_to_pdf(
                        app_sections=app_sections,
                        lang=lang,
                    )
                except Exception as exc:
                    return jsonify({
                        "error": "pdf_conversion_failed",
                        "detail": f"Error converting to PDF — validation failed: {exc}",
                    }), 412
                if parity_err:
                    return jsonify({
                        "error": "pdf_conversion_failed",
                        "detail": parity_err,
                    }), 412
            force_regen = (
                _force_regenerate_requested()
                or has_client_layout
                or has_app_mirror
                or _in_app_report_snapshot_requested()
            )
            access = _billing.check_access(user_id, _billing.PRODUCT_LOVE, cache_params)
            if not access.get("entitled"):
                spec = _billing.catalog_for(_billing.PRODUCT_LOVE) or {}
                return (
                    jsonify(
                        {
                            "error": "payment_required",
                            "product": _billing.PRODUCT_LOVE,
                            "label": spec.get("label"),
                            "amount_inr": access.get("amount_inr"),
                            "params_hash": access.get("params_hash"),
                            "message": "Payment required for this couple. Same couple after pay = free re-download.",
                        }
                    ),
                    402,
                )
            cached_pdf = None if force_regen else access.get("cached_pdf")
            if cached_pdf and has_app_mirror:
                cached_pdf = None
            if cached_pdf:
                try:
                    import pdf_generation_log as _pgl

                    _pgl.record_from_telemetry(
                        kind=_billing.PRODUCT_LOVE,
                        user_id=user_id,
                        pdf_gen={
                            "model": "—",
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "total_tokens": 0,
                            "estimated_cost_inr": 0,
                            "estimated_cost_usd": 0,
                            "openai_call_count": 0,
                            "regen_count": 0,
                            "retry_count": 0,
                            "openai_skipped": True,
                            "cache_hit": False,
                            "final_status": "REPORT_CACHE",
                        },
                        report_cache_hit=True,
                        force_regenerate=force_regen,
                        render_status="SUCCESS",
                    )
                except Exception:
                    pass
                p1n = (data["p1"].get("name") or "p1")
                p2n = (data["p2"].get("name") or "p2")
                safe = lambda s: "".join(c for c in str(s) if c.isalnum() or c in "_-")[:32] or "x"
                fname = f"Love_Reality_Pro_{safe(p1n)}_{safe(p2n)}.pdf"
                return Response(
                    cached_pdf,
                    mimetype="application/pdf",
                    headers={
                        "Content-Disposition": f'inline; filename="{fname}"',
                        "Content-Length": str(len(cached_pdf)),
                        "Cache-Control": "private, max-age=3600",
                        "X-Report-Cache": "hit",
                        **_pdf_layout_headers(cache_hit=True),
                    },
                )

            try:
                bundle = compute_love_reality_bundle(
                    flask_app, data["p1"], data["p2"], skip_ai_insight=True
                )
                client_pro = data.get("pro_premium")
                if has_client_layout and isinstance(client_pro, dict):
                    pro = client_pro
                    polish_source = "client_report_layout"
                    try:
                        import love_reality_polish_snapshot as _snap

                        _snap.save(
                            _snap.snapshot_params(user_id, lang, data["p1"], data["p2"]),
                            pro,
                        )
                    except Exception:
                        pass
                elif isinstance(client_pro, dict) and client_pro:
                    pro, polish_source = _pro_premium_from_client_report(
                        bundle,
                        client_pro=client_pro,
                        lang=lang,
                        user_id=user_id,
                        p1=data["p1"],
                        p2=data["p2"],
                    )
                else:
                    pro, polish_source = _resolve_pro_premium(
                        bundle,
                        lang=lang,
                        user_id=user_id,
                        p1=data["p1"],
                        p2=data["p2"],
                        force_llm=_force_llm_requested(),
                    )
                if pro is None:
                    return jsonify({
                        "error": "polish_snapshot_required",
                        "detail": (
                            "No saved LLM text for this couple. Open the report once, "
                            "then tap Save PDF again."
                        ),
                    }), 412
                merged = dict(bundle)
                merged["pro_premium"] = pro
                merged["pdf_lang"] = lang
                merged["p1"] = data["p1"]
                merged["p2"] = data["p2"]
                if has_client_layout and client_ctx and client_page1:
                    merged["pdf_context"] = client_ctx
                    merged["page1"] = client_page1
                    rid = client_page1.get("report_id")
                    if rid:
                        merged["report_id"] = str(rid)
                if has_app_mirror:
                    merged["app_sections"] = app_sections
                    scores = data.get("scores")
                    if isinstance(scores, dict):
                        merged["scores"] = scores
                pdf_bytes, render_err = _rc.safe_render(
                    "love_reality_pro",
                    lambda: render_love_reality_pro_pdf(merged, lang=lang),
                )
                render_status = "SUCCESS" if pdf_bytes and not render_err else "FAILED"
                pdf_telemetry: dict | None = None
                if polish_source != "polish_snapshot":
                    try:
                        from vedic.compat.openai_pdf_telemetry import (
                            get_last_pdf_generation_telemetry,
                            merge_pdf_generation_into_meta,
                            republish_last_telemetry_summary,
                            update_last_pdf_generation_fields,
                        )

                        update_last_pdf_generation_fields(pdf_render_status=render_status)
                        republish_last_telemetry_summary()
                        pdf_telemetry = get_last_pdf_generation_telemetry()
                        if pdf_telemetry and isinstance(pro, dict):
                            merge_pdf_generation_into_meta(pro.setdefault("_meta", {}), pdf_telemetry)
                    except Exception:
                        pass
                try:
                    import pdf_generation_log as _pgl

                    snap = pdf_telemetry
                    if not snap and isinstance(pro, dict):
                        snap = (pro.get("_meta") or {}).get("pdf_generation")
                    if polish_source == "polish_snapshot" and not snap:
                        snap = {
                            "model": "—",
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "total_tokens": 0,
                            "estimated_cost_inr": 0,
                            "estimated_cost_usd": 0,
                            "openai_call_count": 0,
                            "openai_skipped": True,
                            "cache_hit": True,
                            "final_status": "POLISH_SNAPSHOT",
                        }
                    _pgl.record_from_telemetry(
                        kind=_billing.PRODUCT_LOVE,
                        user_id=user_id,
                        pdf_gen=snap if isinstance(snap, dict) else None,
                        report_cache_hit=False,
                        force_regenerate=force_regen,
                        render_status=render_status,
                    )
                except Exception:
                    pass
                if render_err or not pdf_bytes:
                    return jsonify({"error": "love_reality_pro_pdf_failed", "detail": render_err}), 500

                p1n = (bundle.get("p1") or {}).get("name") or "p1"
                p2n = (bundle.get("p2") or {}).get("name") or "p2"
                safe = lambda s: "".join(c for c in str(s) if c.isalnum() or c in "_-")[:32] or "x"
                fname = f"Love_Reality_Pro_{safe(p1n)}_{safe(p2n)}.pdf"
                _rc.save(
                    user_id,
                    "love_reality_pro",
                    "Love Reality Pro",
                    cache_params,
                    pdf_bytes,
                    fname,
                )
                pdf_headers: dict[str, str] = {
                    "Content-Disposition": f'inline; filename="{fname}"',
                    "Content-Length": str(len(pdf_bytes)),
                    "Cache-Control": "private, max-age=3600",
                    "X-Report-Cache": "miss",
                    "X-Polish-Source": polish_source,
                    **_pdf_layout_headers(cache_hit=False),
                }
                if has_app_mirror:
                    pdf_headers["X-PDF-Source"] = "app_mirror_fresh"
                try:
                    from vedic.compat.openai_pdf_telemetry import (
                        get_last_pdf_generation_telemetry,
                        response_telemetry_headers,
                    )

                    _pg = get_last_pdf_generation_telemetry()
                    if _pg:
                        pdf_headers.update(response_telemetry_headers(_pg))
                except Exception:
                    pass
                return Response(
                    pdf_bytes,
                    mimetype="application/pdf",
                    headers=pdf_headers,
                )
            except Exception as exc:
                try:
                    print(f"[love_reality_pro_pdf] failed: {exc}", flush=True)
                except Exception:
                    pass
                return jsonify({"error": "love_reality_pro_pdf_failed", "detail": str(exc)}), 500

    if "love_reality_pro_report" not in flask_app.view_functions:

        @flask_app.route("/api/love-reality/pro-report", methods=["POST", "OPTIONS", "GET"])
        def love_reality_pro_report():
            """Full Love Reality Pro narrative as JSON — for in-app scroll report (all languages)."""
            if request.method == "OPTIONS":
                return "", 204
            if request.method == "GET":
                return jsonify({
                    "ok": True,
                    "endpoint": "love-reality-pro-report",
                    "methods": ["POST"],
                }), 200

            data = request.get_json(silent=True) or {}
            if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
                return jsonify({"error": "expected_p1_p2"}), 400

            try:
                from vedic.love_reality.compute_bundle import compute_love_reality_bundle
                from vedic.love_reality.pdf_locale import normalize_love_reality_pdf_lang
                from vedic.love_reality.pdf_text_safe import sanitize_love_reality_pro_premium
                import couple_report_billing as _billing
            except Exception as exc:
                return jsonify({
                    "error": "love_reality_pro_report_failed",
                    "detail": f"import_failed: {exc}",
                }), 500

            lang = normalize_love_reality_pdf_lang(data.get("lang"))

            user_id = 0
            uid_hdr = (request.headers.get("X-User-Id") or "").strip()
            if uid_hdr:
                try:
                    from flask_app import get_authed_user

                    auth_user, _err = get_authed_user(int(uid_hdr))
                    if auth_user is not None:
                        user_id = int(auth_user.id)
                except Exception:
                    pass

            if _billing.payment_required() and not _billing.love_reality_pro_free() and not user_id:
                return jsonify({
                    "error": "auth_required",
                    "message": "Login required to read Love Reality Pro report",
                }), 401

            cache_params = _love_reality_cache_params(lang, data["p1"], data["p2"])
            access = _billing.check_access(user_id, _billing.PRODUCT_LOVE, cache_params)
            if not access.get("entitled"):
                spec = _billing.catalog_for(_billing.PRODUCT_LOVE) or {}
                return jsonify({
                    "error": "payment_required",
                    "product": _billing.PRODUCT_LOVE,
                    "label": spec.get("label"),
                    "amount_inr": access.get("amount_inr"),
                    "params_hash": access.get("params_hash"),
                    "message": "Payment required for this couple.",
                }), 402

            import love_reality_report_json_cache as _json_cache
            import love_reality_polish_snapshot as _snap
            import report_cache as _rc

            json_cache_params = _json_cache.cache_params(user_id, lang, data["p1"], data["p2"])
            snap_params = _snap.snapshot_params(user_id, lang, data["p1"], data["p2"])

            if lang == "hi":
                _purge_hi_server_caches_once()

            force_full = _pro_report_force_llm(data)
            prefer_server_cache = (
                (request.headers.get("X-Prefer-Server-Cache") or "").strip() == "1"
            )
            relocalize_only = _relocalize_sections_requested() and not force_full
            if force_full:
                _json_cache.invalidate(json_cache_params)
                _snap.invalidate(snap_params)
            if prefer_server_cache and not force_full and lang in ("en", "hn"):
                restored = _json_cache.load(json_cache_params)
                if restored and lang in ("en", "hn") and _en_saved_report_stale(restored):
                    restored = None
                    _json_cache.invalidate(json_cache_params)
                if restored and restored.get("ok"):
                    payload_out = _with_app_sections(restored, lang)
                    resp = jsonify(payload_out)
                    resp.headers["X-Report-Cache"] = "hit"
                    resp.headers["X-Server-Restore"] = "1"
                    resp.headers["X-Content-Script"] = str(payload_out.get("content_script") or "")
                    return resp
            if relocalize_only:
                cached_json = _json_cache.load(json_cache_params)
                if cached_json and lang == "hi" and _hi_saved_report_stale(cached_json):
                    cached_json = None
                if cached_json:
                    payload_out = _enrich_hi_section8_meta(_with_app_sections(cached_json, lang))
                    blocked = _hi_report_block_response(payload_out, lang)
                    if blocked:
                        _json_cache.invalidate(json_cache_params)
                        _snap.invalidate(snap_params)
                    else:
                        resp = jsonify(payload_out)
                        resp.headers["X-Report-Cache"] = "relocalize"
                        resp.headers["X-Content-Script"] = str(payload_out.get("content_script") or "")
                        return resp
            if not force_full and lang != "hi":
                cached_json = _json_cache.load(json_cache_params)
                if cached_json and lang == "hi" and _hi_saved_report_stale(cached_json):
                    _json_cache.invalidate(json_cache_params)
                    _snap.invalidate(snap_params)
                    cached_json = None
                if cached_json:
                    if lang in ("en", "hn") and _en_saved_report_stale(cached_json):
                        _json_cache.invalidate(json_cache_params)
                        _snap.invalidate(snap_params)
                        cached_json = None
                    if cached_json and lang == "en":
                        from vedic.love_reality.love_section_polish import (
                            _remedies_mentions_religious_ritual,
                            breakup_chapter_lane_ready,
                        )

                        pro_cached = (
                            cached_json.get("pro_premium")
                            if isinstance(cached_json.get("pro_premium"), dict)
                            else {}
                        )
                        s4_narr = str(pro_cached.get("remedies_action_narrative") or "")
                        if (
                            not breakup_chapter_lane_ready(pro_cached, "en")
                            or _remedies_mentions_religious_ritual(s4_narr)
                        ):
                            _json_cache.invalidate(json_cache_params)
                            cached_json = None
                if cached_json:
                    payload_out = _enrich_hi_section8_meta(_with_app_sections(cached_json, lang))
                    blocked = _hi_report_block_response(payload_out, lang)
                    if blocked:
                        _json_cache.invalidate(json_cache_params)
                        _snap.invalidate(snap_params)
                    else:
                        resp = jsonify(payload_out)
                        resp.headers["X-Report-Cache"] = "hit"
                        resp.headers["X-Content-Script"] = str(payload_out.get("content_script") or "")
                        return resp

            try:
                bundle = compute_love_reality_bundle(
                    flask_app, data["p1"], data["p2"], skip_ai_insight=True
                )
                if force_full:
                    try:
                        from vedic.love_reality.love_section_polish import bust_love_polish_section_caches

                        bust_love_polish_section_caches(bundle, lang)
                    except Exception as exc:
                        try:
                            print(f"[love_reality_pro_report] cache bust failed: {exc}", flush=True)
                        except Exception:
                            pass
                pro, polish_source = _resolve_pro_premium(
                    bundle,
                    lang=lang,
                    user_id=user_id,
                    p1=data["p1"],
                    p2=data["p2"],
                    force_llm=force_full or lang == "hi",
                )
                if pro is None:
                    return jsonify({
                        "error": "polish_snapshot_required",
                        "detail": "No saved report text for this couple yet.",
                    }), 412
                from vedic.love_reality.love_section_polish import (
                    blueprint_section_hi_ready,
                    breakup_chapter_hi_ready,
                    breakup_chapter_word_count,
                    bust_love_polish_section_caches,
                    deep_analysis_hi_ready,
                    ensure_blueprint_section5_llm,
                    ensure_breakup_section8_llm,
                    ensure_moon_sync_section7_llm,
                    ensure_remedies_action_llm,
                    moon_sync_narrative_hi_ready,
                    remedies_action_hi_ready,
                    strip_non_hindi_breakup_chapter,
                )
                from vedic.love_reality.premium_polish import ensure_deep_analysis_llm

                if lang == "hi":
                    strip_non_hindi_breakup_chapter(pro)
                    for attempt in range(3):
                        pro = ensure_breakup_section8_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        pro = ensure_moon_sync_section7_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        pro = ensure_blueprint_section5_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        pro = ensure_deep_analysis_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        pro = ensure_remedies_action_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        if lang == "hi":
                            if (
                                breakup_chapter_hi_ready(pro)
                                and moon_sync_narrative_hi_ready(pro)
                                and blueprint_section_hi_ready(pro)
                                and deep_analysis_hi_ready(pro)
                                and remedies_action_hi_ready(pro)
                            ):
                                break
                        if attempt < 2:
                            bust_love_polish_section_caches(bundle, lang)
                else:
                    pro = ensure_breakup_section8_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=force_full,
                    )
                    pro = ensure_moon_sync_section7_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=force_full,
                    )
                    pro = ensure_blueprint_section5_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=force_full,
                    )
                    pro = ensure_deep_analysis_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=force_full,
                    )
                    pro = ensure_remedies_action_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=force_full,
                    )
                if lang == "hi" and not remedies_action_hi_ready(pro):
                    from vedic.love_reality.love_section_polish import _bust_remedies_action_scope_file_cache

                    for _ in range(5):
                        _bust_remedies_action_scope_file_cache(bundle, lang)
                        pro = ensure_remedies_action_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        if remedies_action_hi_ready(pro):
                            break
                if lang == "hi" and not breakup_chapter_hi_ready(pro):
                    s8_meta = (pro.get("_meta") or {}).get("section8_breakup") if isinstance(pro.get("_meta"), dict) else {}
                    llm_hint = ""
                    if isinstance(s8_meta, dict):
                        llm_hint = str(s8_meta.get("reject") or s8_meta.get("reason") or "").strip()
                    detail = (
                        "Report load nahi hua — Section 8 ke liye LLM se poori देवनागरी Hindi "
                        "chapter nahi bani (English/mixed reject ho gaya)."
                    )
                    if llm_hint:
                        detail += f" (LLM: {llm_hint})"
                    detail += " «रिपोर्ट अपडेट करें» dubara dabao — 2–3 min wait."
                    return jsonify({
                        "error": "section8_not_ready",
                        "detail": detail,
                        "section8_llm": s8_meta or None,
                    }), 412
                pro = sanitize_love_reality_pro_premium(pro, bundle, lang=lang)
                if lang == "hi":
                    strip_non_hindi_breakup_chapter(pro)
                if lang == "hi":
                    pro = ensure_moon_sync_section7_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=True,
                    )
                    pro = ensure_blueprint_section5_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=lang == "hi",
                    )
                    pro = ensure_deep_analysis_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=lang == "hi",
                    )
                    pro = ensure_remedies_action_llm(
                        bundle,
                        pro,
                        lang,
                        force_llm=lang == "hi",
                    )
                    if lang == "hi" and not breakup_chapter_hi_ready(pro):
                        pro = ensure_breakup_section8_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                from vedic.love_reality.pdf_data_v2 import build_love_reality_pdf_v2_context
                from vedic.love_reality.pdf_page1_data import (
                    build_love_reality_page1_data,
                    localize_love_pdf_context,
                )
                from vedic.love_reality.pdf_text_safe import love_pro_payload_matches_lang

                def _build_payload(pro_block: dict, source: str) -> dict:
                    pdf_ctx = build_love_reality_pdf_v2_context(
                        bundle, pro_block, data["p1"], data["p2"], lang=lang
                    )
                    pdf_ctx = localize_love_pdf_context(pdf_ctx, lang)
                    p1_data = build_love_reality_page1_data(
                        pdf_ctx, bundle, pro_block, data["p1"], data["p2"], lang=lang
                    )
                    lc = bundle.get("love_compatibility") or {}
                    bu = bundle.get("breakup_chances") or {}
                    ly = bundle.get("loyalty_check") or {}
                    wr = bundle.get("will_return") or {}
                    fo = bundle.get("future_outcome") or {}
                    p1n = str(data["p1"].get("name") or "You")
                    p2n = str(data["p2"].get("name") or "Partner")
                    from vedic.love_reality.love_section_polish import _ASSEMBLY_VER

                    return {
                        "ok": True,
                        "lang": lang,
                        "polish_assembly": _ASSEMBLY_VER,
                        "polish_source": source,
                        "p1_name": str(p1n),
                        "p2_name": str(p2n),
                        "scores": {
                            "love": int(lc.get("score") or lc.get("love_score") or 0),
                            "breakup": int(bu.get("score") or bu.get("breakup_score") or 0),
                            "loyalty": int(ly.get("score") or ly.get("loyalty_score") or 0),
                            "return": int(wr.get("return_probability") or wr.get("score") or 0),
                            "future": int(fo.get("future_score") or fo.get("score") or 0),
                        },
                        "pro_premium": pro_block,
                        "pdf_context": pdf_ctx,
                        "page1": p1_data,
                    }

                payload = _build_payload(pro, polish_source)
                if lang in ("hn", "hi") and not love_pro_payload_matches_lang(payload, lang):
                    try:
                        from vedic.love_reality.love_section_polish import bust_love_polish_section_caches

                        bust_love_polish_section_caches(bundle, lang)
                    except Exception:
                        pass
                    pro_retry, polish_source = _resolve_pro_premium(
                        bundle,
                        lang=lang,
                        user_id=user_id,
                        p1=data["p1"],
                        p2=data["p2"],
                        force_llm=True,
                    )
                    if pro_retry:
                        pro = sanitize_love_reality_pro_premium(pro_retry, bundle, lang=lang)
                        if lang == "hi":
                            strip_non_hindi_breakup_chapter(pro)
                        pro = ensure_breakup_section8_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        pro = ensure_remedies_action_llm(
                            bundle,
                            pro,
                            lang,
                            force_llm=True,
                        )
                        if lang == "hi" and not breakup_chapter_hi_ready(pro):
                            s8_meta = (pro.get("_meta") or {}).get("section8_breakup") or {}
                            return jsonify({
                                "error": "section8_not_ready",
                                "detail": "Section 8 LLM Hindi retry failed after lang mismatch.",
                                "section8_llm": s8_meta,
                            }), 412
                        payload = _build_payload(pro, polish_source)
                payload = _with_app_sections(payload, lang)
                if lang == "hi":
                    payload = _enrich_hi_section8_meta(payload)
                if lang in ("hn", "hi") and not love_pro_payload_matches_lang(payload, lang):
                    payload = {
                        **payload,
                        "lang_mismatch_recovered": True,
                        "content_script": payload.get("content_script") or (
                            "hi_partial" if lang == "hi" else "en_mismatch"
                        ),
                    }
                blocked4 = _hi_section4_block_response(payload) if lang == "hi" else None
                if blocked4:
                    return blocked4
                blocked = _hi_section8_block_response(payload)
                if blocked and lang == "hi":
                    _snap.invalidate(snap_params)
                    bust_love_polish_section_caches(bundle, lang)
                    chapters = [
                        c for c in (pro.get("chapters") or [])
                        if not (
                            isinstance(c, dict)
                            and str(c.get("key") or "").strip().lower() == "breakup"
                        )
                    ]
                    pro["chapters"] = chapters
                    for _ in range(3):
                        pro = ensure_breakup_section8_llm(
                            bundle,
                            pro,
                            "hi",
                            force_llm=True,
                        )
                        if not breakup_chapter_hi_ready(pro):
                            bust_love_polish_section_caches(bundle, lang)
                            continue
                        pro = sanitize_love_reality_pro_premium(pro, bundle, lang=lang)
                        payload = _build_payload(pro, polish_source)
                        payload = _with_app_sections(payload, lang)
                        payload = {**payload, "hi_cache_ver": LOVE_REALITY_HI_CACHE_VER}
                        blocked = _hi_section8_block_response(payload)
                        if not blocked:
                            break
                if blocked:
                    return blocked
                if lang == "hi":
                    for _ in range(2):
                        script = str(payload.get("content_script") or "").strip().lower()
                        if script == "hi":
                            break
                        payload = _enrich_hi_section8_meta(_with_app_sections(payload, lang))
                    blocked_script = _hi_script_block_response(payload, lang)
                    if blocked_script:
                        return blocked_script
                if not force_full:
                    _json_cache.save(json_cache_params, payload)
                    _rc.invalidate(user_id, _billing.PRODUCT_LOVE, cache_params)
                else:
                    _json_cache.save(json_cache_params, payload)
                resp = jsonify(payload)
                resp.headers["X-Report-Cache"] = "miss"
                resp.headers["X-Polish-Source"] = polish_source
                resp.headers["X-Report-Lang"] = lang
                resp.headers["X-Content-Script"] = str(payload.get("content_script") or "")
                if force_full:
                    resp.headers["X-Love-Report-Full-Update"] = "1"
                return resp
            except Exception as exc:
                return jsonify({
                    "error": "love_reality_pro_report_failed",
                    "detail": str(exc),
                }), 500

    if "loyalty_compare" not in flask_app.view_functions:

        @flask_app.route("/api/loyalty-compare", methods=["POST", "OPTIONS"])
        def loyalty_compare():
            if request.method == "OPTIONS":
                return "", 204
            data = request.get_json(silent=True) or {}
            if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
                return jsonify({"error": "expected_p1_p2"}), 400
            try:
                from vedic.love_reality.engines import run_loyalty_check

                r = run_loyalty_check(data["p1"], data["p2"])
                return jsonify({
                    "engine_version": r.get("engine_version", "loyalty_compare_v2"),
                    "per_person": r.get("per_person"),
                    "p1_loyalty_score": r.get("p1_loyalty_score"),
                    "p2_loyalty_score": r.get("p2_loyalty_score"),
                    "p1_loyalty_level": r.get("p1_loyalty_level"),
                    "p2_loyalty_level": r.get("p2_loyalty_level"),
                    "loyalty_tie_breaker": r.get("loyalty_tie_breaker"),
                    "is_duty_bound_loyal": r.get("is_duty_bound_loyal"),
                })
            except Exception as exc:
                return jsonify({"error": f"loyalty_compare_failed: {exc}"}), 500
