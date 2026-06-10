"""Love Reality Pro PDF — Flask route registration."""
from __future__ import annotations

from flask import Response, jsonify, request

# Bump when PDF layout/renderer changes — invalidates stale server-side report cache.
LOVE_REALITY_PDF_LAYOUT_VER = "lr_pro_v24_moon_sync_llm"


def love_reality_cache_params(lang: str, p1: dict, p2: dict) -> dict:
    import report_cache as _rc
    from vedic.love_reality.love_section_polish import _ASSEMBLY_VER

    cp = _rc.couple_cache_params(lang, p1, p2)
    cp["pdf_layout"] = LOVE_REALITY_PDF_LAYOUT_VER
    cp["polish_assembly"] = _ASSEMBLY_VER
    return cp


def _love_reality_cache_params(lang: str, p1: dict, p2: dict) -> dict:
    return love_reality_cache_params(lang, p1, p2)


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
    bust = payload.get("cache_bust")
    if bust is not None and str(bust).strip() not in ("", "0"):
        return True
    return False


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
            return cached, "polish_snapshot"

    if render_only:
        return None, "render_only_miss"

    pro = polish_love_reality_premium(bundle, lang=lang, force_llm=force_llm)
    if not isinstance(pro, dict):
        pro = {}
    if pro:
        from vedic.love_reality.love_section_polish import _assembly_depth_ok

        if _assembly_depth_ok(pro):
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
                    from vedic.love_reality.app_pdf_parity import validate_app_sections_parity

                    parity_err = validate_app_sections_parity(
                        app_sections=app_sections,
                        page1=client_page1 or {},
                        pdf_context=client_ctx or {},
                        lang=lang,
                    )
                except Exception as exc:
                    return jsonify({
                        "error": "app_pdf_parity_failed",
                        "detail": f"Parity check failed: {exc}",
                    }), 412
                if parity_err:
                    return jsonify({
                        "error": "app_pdf_parity_failed",
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

            json_cache_params = _json_cache.cache_params(user_id, lang, data["p1"], data["p2"])
            snap_params = _snap.snapshot_params(user_id, lang, data["p1"], data["p2"])
            force_full = _pro_report_force_llm(data)
            if force_full:
                _json_cache.invalidate(json_cache_params)
                _snap.invalidate(snap_params)
            if not force_full:
                cached_json = _json_cache.load(json_cache_params)
                if cached_json:
                    from vedic.love_reality.pdf_text_safe import love_pro_payload_matches_lang

                    if not love_pro_payload_matches_lang(cached_json, lang):
                        cached_json = None
                    elif lang in ("hn", "hi"):
                        from vedic.love_reality.pdf_page1_data import _localize_page1_dashboard

                        p1_cached = cached_json.get("page1")
                        if isinstance(p1_cached, dict):
                            summary = " ".join([
                                str(p1_cached.get("relationship_summary") or ""),
                                str(p1_cached.get("verdict") or ""),
                            ])
                            import re

                            already_local = (
                                lang == "hi"
                                and len(re.findall(r"[\u0900-\u097F]", summary)) >= 24
                            ) or (
                                lang == "hn"
                                and summary
                                and not re.search(r"[\u0900-\u097F]", summary[:400])
                                and re.search(
                                    r"\b(aap|rishte|kya|hai|hain|nahi)\b",
                                    summary,
                                    re.I,
                                )
                            )
                            if not already_local:
                                cached_json = {
                                    **cached_json,
                                    "page1": _localize_page1_dashboard(p1_cached, lang),
                                }
                                if not love_pro_payload_matches_lang(cached_json, lang):
                                    cached_json = None
                if cached_json:
                    resp = jsonify(cached_json)
                    resp.headers["X-Report-Cache"] = "hit"
                    return resp

            import report_cache as _rc

            try:
                bundle = compute_love_reality_bundle(
                    flask_app, data["p1"], data["p2"], skip_ai_insight=True
                )
                if force_full:
                    try:
                        from vedic.love_reality.premium_polish import bust_love_polish_all_caches

                        bust_love_polish_all_caches(bundle, lang)
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
                    force_llm=force_full,
                )
                if pro is None:
                    return jsonify({
                        "error": "polish_snapshot_required",
                        "detail": "No saved report text for this couple yet.",
                    }), 412
                pro = sanitize_love_reality_pro_premium(pro, bundle, lang=lang)
                from vedic.love_reality.pdf_data_v2 import build_love_reality_pdf_v2_context
                from vedic.love_reality.pdf_page1_data import build_love_reality_page1_data
                from vedic.love_reality.pdf_text_safe import love_pro_payload_matches_lang

                def _build_payload(pro_block: dict, source: str) -> dict:
                    pdf_ctx = build_love_reality_pdf_v2_context(
                        bundle, pro_block, data["p1"], data["p2"], lang=lang
                    )
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
                    return {
                        "ok": True,
                        "lang": lang,
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
                        from vedic.love_reality.premium_polish import bust_love_polish_all_caches

                        bust_love_polish_all_caches(bundle, lang)
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
                        payload = _build_payload(pro, polish_source)
                if lang in ("hn", "hi") and not love_pro_payload_matches_lang(payload, lang):
                    resp = jsonify({
                        "error": "love_reality_pro_report_failed",
                        "detail": f"Report text did not match language={lang} after LLM — retry Update Report.",
                    })
                    resp.headers["X-Content-Lang-Mismatch"] = lang
                    return resp, 412
                if not force_full:
                    _json_cache.save(json_cache_params, payload)
                    _rc.invalidate(user_id, _billing.PRODUCT_LOVE, cache_params)
                else:
                    _json_cache.save(json_cache_params, payload)
                resp = jsonify(payload)
                resp.headers["X-Report-Cache"] = "miss"
                resp.headers["X-Polish-Source"] = polish_source
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
