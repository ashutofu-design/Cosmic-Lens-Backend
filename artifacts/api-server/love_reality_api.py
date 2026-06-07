"""Love Reality Pro PDF — Flask route registration."""
from __future__ import annotations

from flask import Response, jsonify, request

# Bump when PDF layout/renderer changes — invalidates stale server-side report cache.
LOVE_REALITY_PDF_LAYOUT_VER = "lr_pro_v3_premium_page1"


def _love_reality_cache_params(lang: str, p1: dict, p2: dict) -> dict:
    import report_cache as _rc

    cp = _rc.couple_cache_params(lang, p1, p2)
    cp["pdf_layout"] = LOVE_REALITY_PDF_LAYOUT_VER
    return cp


def _force_regenerate_requested() -> bool:
    hdr = (request.headers.get("X-Force-Regenerate") or "").strip().lower()
    body = request.get_json(silent=True) or {}
    flag = str(body.get("force_regenerate") or "").strip().lower()
    return hdr in ("1", "true", "yes", "on") or flag in ("1", "true", "yes", "on")


def register_love_reality_routes(flask_app) -> None:
    """Register POST /api/love-reality/pro-pdf (idempotent if already present)."""
    endpoint = "love_reality_pro_pdf"
    rule = "/api/love-reality/pro-pdf"
    if endpoint in flask_app.view_functions:
        return

    @flask_app.route(rule, methods=["POST", "OPTIONS", "GET"])
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
        from vedic.love_reality.compute_bundle import compute_love_reality_bundle
        from vedic.love_reality.pdf_locale import normalize_love_reality_pdf_lang
        from vedic.love_reality.premium_polish import polish_love_reality_premium
        from love_reality_pdf import render_love_reality_pro_pdf

        lang = normalize_love_reality_pdf_lang(data.get("lang"))
        if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
            return jsonify({"error": "expected_p1_p2"}), 400

        import report_cache as _rc
        import couple_report_billing as _billing

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

        cache_params = _love_reality_cache_params(lang, data["p1"], data["p2"])
        force_regen = _force_regenerate_requested()
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
                },
            )

        try:
            bundle = compute_love_reality_bundle(
                flask_app, data["p1"], data["p2"], skip_ai_insight=True
            )
            pro = polish_love_reality_premium(bundle, lang=lang)
            merged = dict(bundle)
            merged["pro_premium"] = pro
            merged["pdf_lang"] = lang
            pdf_bytes, render_err = _rc.safe_render(
                "love_reality_pro",
                lambda: render_love_reality_pro_pdf(merged, lang=lang),
            )
            render_status = "SUCCESS" if pdf_bytes and not render_err else "FAILED"
            try:
                from vedic.compat.openai_pdf_telemetry import update_last_pdf_generation_fields

                update_last_pdf_generation_fields(pdf_render_status=render_status)
            except Exception:
                pass
            try:
                import pdf_generation_log as _pgl

                pg = (pro.get("_meta") or {}).get("pdf_generation") if isinstance(pro, dict) else None
                _pgl.record_from_telemetry(
                    kind=_billing.PRODUCT_LOVE,
                    user_id=user_id,
                    pdf_gen=pg if isinstance(pg, dict) else None,
                    report_cache_hit=False,
                    force_regenerate=force_regen,
                    render_status=render_status,
                )
            except Exception:
                pass
            if render_err or not pdf_bytes:
                return jsonify({"error": "love_reality_pro_pdf_failed", "detail": render_err}), 500
        except Exception as exc:
            try:
                print(f"[love_reality_pro_pdf] failed: {exc}", flush=True)
            except Exception:
                pass
            return jsonify({"error": "love_reality_pro_pdf_failed", "detail": str(exc)}), 500

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
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{fname}"',
                "Content-Length": str(len(pdf_bytes)),
                "Cache-Control": "private, max-age=3600",
                "X-Report-Cache": "miss",
            },
        )

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
