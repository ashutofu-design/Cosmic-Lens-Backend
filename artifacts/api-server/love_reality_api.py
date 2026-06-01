"""Love Reality Pro PDF — Flask route registration."""
from __future__ import annotations

from flask import Response, jsonify, request


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
        from couple_report_api import pdf_access_gate

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

        if _billing.payment_required() and not user_id:
            return jsonify(
                {
                    "error": "auth_required",
                    "message": "Login required to generate Love Reality Pro PDF",
                }
            ), 401

        cached_pdf, pay_err = pdf_access_gate(
            user_id, _billing.PRODUCT_LOVE, data["p1"], data["p2"], lang
        )
        if pay_err:
            return pay_err
        if cached_pdf:
            p1n = (data["p1"].get("name") or "p1")
            p2n = (data["p2"].get("name") or "p2")
            safe = lambda s: "".join(c for c in str(s) if c.isalnum() or c in "_-")[:32] or "x"
            cache_params = _rc.couple_cache_params(lang, data["p1"], data["p2"])
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

        cache_params = _rc.couple_cache_params(lang, data["p1"], data["p2"])

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
            if render_err or not pdf_bytes:
                return jsonify({"error": "love_reality_pro_pdf_failed", "detail": render_err}), 500
        except Exception as exc:
            try:
                print(f"[love_reality_pro_pdf] failed: {exc}", flush=True)
            except Exception:
                pass
            return jsonify({"error": "love_reality_pro_pdf_failed"}), 500

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
