"""Face Reading PRO report — entitlement + Razorpay checkout."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from flask import jsonify, request

import face_reading_report_billing as billing
import payment_gateway as pg

log = logging.getLogger(__name__)
_UTC = timezone.utc


def _resolve_user():
    from flask_app import get_authed_user

    uid_hdr = (request.headers.get("X-User-Id") or "").strip()
    if not uid_hdr:
        return None, (jsonify({"error": "auth_required", "message": "X-User-Id required"}), 401)
    try:
        user, err = get_authed_user(int(uid_hdr))
    except (TypeError, ValueError):
        return None, (jsonify({"error": "invalid_user_id"}), 400)
    if err:
        return None, err
    return user, None


def _params_from_body(data: dict) -> tuple[dict | None, str | None]:
    lang = (data.get("lang") or data.get("language") or "hinglish").strip()
    session_id = (data.get("session_id") or "").strip()
    if not session_id:
        return None, None
    cp = billing.face_cache_params(
        session_id=session_id,
        lang=lang,
        age=(data.get("age") or None),
        gender=(data.get("gender") or None),
    )
    return cp, lang


def pdf_access_gate(user_id: int, cache_params: dict):
    access = billing.check_access(user_id, cache_params)
    if access.get("cached_pdf"):
        return access["cached_pdf"], None
    if access.get("entitled"):
        return None, None
    spec = billing.catalog_for(billing.PRODUCT_FACE_READING_PRO) or {}
    return None, (
        jsonify(
            {
                "ok": False,
                "error": "payment_required",
                "product": billing.PRODUCT_FACE_READING_PRO,
                "label": spec.get("label"),
                "amount_inr": access.get("amount_inr"),
                "params_hash": access.get("params_hash"),
                "message": "Pay ₹299 to unlock your Face Reading PRO PDF report.",
            }
        ),
        402,
    )


def register_face_reading_report_routes(app) -> None:
    @app.route("/api/face-reading-report/check", methods=["POST", "OPTIONS"])
    def face_reading_report_check():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        cp, lang = _params_from_body(data)
        if not cp:
            return jsonify({"error": "missing_fields", "message": "session_id required"}), 400
        access = billing.check_access(user.id, cp)
        return jsonify(
            {
                "entitled": bool(access.get("entitled")),
                "payment_required": bool(access.get("payment_required")),
                "cache_hit": bool(access.get("cache_hit")),
                "already_paid": bool(access.get("already_paid")),
                "is_pro": bool(access.get("is_pro")),
                "product": billing.PRODUCT_FACE_READING_PRO,
                "amount_inr": access.get("amount_inr"),
                "label": access.get("label"),
                "params_hash": access.get("params_hash"),
                "payment_bypass": billing.payment_bypass(),
            }
        )

    @app.route("/api/face-reading-report/create-order", methods=["POST", "OPTIONS"])
    def face_reading_report_create_order():
        if request.method == "OPTIONS":
            return "", 204
        if not pg.configured():
            body, code = pg.not_configured_error()
            return jsonify(body), code

        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        cp, lang = _params_from_body(data)
        if not cp:
            return jsonify({"error": "missing_fields", "message": "session_id required"}), 400

        payload, perr = billing.create_purchase_intent(user.id, cp, lang or "hinglish")
        if perr:
            return jsonify({"error": perr}), 400
        if payload.get("already_entitled"):
            return jsonify({**payload, "payment_required": False})

        purchase_id = payload["purchase_id"]
        amount = payload["amount"]
        from models import CoupleReportPurchase, db

        purchase = CoupleReportPurchase.query.get(purchase_id)
        if not purchase:
            return jsonify({"error": "purchase_not_found"}), 404

        ts = int(datetime.now(_UTC).timestamp())
        order_id = f"FR{user.id}_{purchase.id}_{ts}"

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=amount,
                notes={
                    "kind": "face_reading_report",
                    "purchase_id": str(purchase.id),
                    "product": billing.PRODUCT_FACE_READING_PRO,
                },
            )
        except Exception as e:
            log.error("[face_reading_report] Razorpay order failed: %s", e)
            return jsonify({"error": "razorpay_order_failed", "detail": str(e)}), 502

        purchase.order_id = order_id
        db.session.commit()

        return jsonify(
            pg.checkout_response(
                order_id,
                rz_order,
                amount,
                user,
                purchase_id=purchase.id,
                product=billing.PRODUCT_FACE_READING_PRO,
                label=payload.get("label"),
                params_hash=payload.get("params_hash"),
            )
        )

    @app.route(
        "/api/face-reading-report/purchase-status/<int:purchase_id>",
        methods=["GET", "OPTIONS"],
    )
    def face_reading_report_purchase_status(purchase_id: int):
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        from models import CoupleReportPurchase

        row = CoupleReportPurchase.query.get(purchase_id)
        if not row or row.user_id != user.id:
            return jsonify({"error": "not_found"}), 404

        if row.status == "created" and row.order_id and pg.configured():
            try:
                if pg.is_receipt_paid(row.order_id):
                    billing.mark_paid(row.id, order_id=row.order_id)
                    row = CoupleReportPurchase.query.get(purchase_id)
            except Exception as exc:
                log.warning("[face_reading_report] poll RZ: %s", exc)

        return jsonify(
            {
                "status": row.status,
                "entitled": row.status == "paid",
                "product": row.product,
            }
        )
