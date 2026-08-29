"""Birth Time Rectification — entitlement + Razorpay checkout."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import jsonify, request

import birth_time_rectification_billing as billing
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


def _params_from_body(data: dict) -> dict | None:
    full_name = (data.get("full_name") or "").strip()
    gender = (data.get("gender") or "").strip()
    dob = (data.get("dob") or "").strip()
    approx_tob = (data.get("approx_tob") or "").strip()
    birth_place = (data.get("birth_place") or "").strip()
    if not (full_name and gender and dob and approx_tob and birth_place):
        return None
    return billing.cache_params(full_name, gender, dob, approx_tob, birth_place)


def register_birth_time_rectification_payment_routes(app) -> None:
    @app.route("/api/birth-time-rectification/check", methods=["POST", "OPTIONS"])
    def birth_time_rectification_check():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        cp = _params_from_body(data)
        if not cp:
            return jsonify({"error": "missing_fields"}), 400
        access = billing.check_access(user.id, cp)
        return jsonify(
            {
                "entitled": bool(access.get("entitled")),
                "payment_required": bool(access.get("payment_required")),
                "already_paid": bool(access.get("already_paid")),
                "product": billing.PRODUCT_BIRTH_TIME,
                "amount_inr": access.get("amount_inr"),
                "label": access.get("label"),
                "params_hash": access.get("params_hash"),
                "payment_bypass": billing.payment_bypass(),
            }
        )

    @app.route("/api/birth-time-rectification/create-order", methods=["POST", "OPTIONS"])
    def birth_time_rectification_create_order():
        if request.method == "OPTIONS":
            return "", 204
        if not pg.configured():
            body, code = pg.not_configured_error()
            return jsonify(body), code

        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        cp = _params_from_body(data)
        if not cp:
            return jsonify({"error": "missing_fields"}), 400

        payload, perr = billing.create_purchase_intent(user.id, cp)
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
        order_id = f"BT{user.id}_{purchase.id}_{ts}"

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=amount,
                notes={
                    "kind": billing.KIND,
                    "purchase_id": str(purchase.id),
                    "product": billing.PRODUCT_BIRTH_TIME,
                },
            )
        except Exception as e:
            log.error("[birth_time_rectification] Razorpay order failed: %s", e)
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
                product=billing.PRODUCT_BIRTH_TIME,
                label=payload.get("label"),
                params_hash=payload.get("params_hash"),
            )
        )

    @app.route(
        "/api/birth-time-rectification/purchase-status/<int:purchase_id>",
        methods=["GET", "OPTIONS"],
    )
    def birth_time_rectification_purchase_status(purchase_id: int):
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        from models import CoupleReportPurchase

        purchase = CoupleReportPurchase.query.get(purchase_id)
        if (
            not purchase
            or purchase.user_id != user.id
            or purchase.product != billing.PRODUCT_BIRTH_TIME
        ):
            return jsonify({"error": "not_found"}), 404

        if purchase.status == "created" and purchase.order_id and pg.configured():
            try:
                if pg.is_receipt_paid(
                    purchase.order_id,
                    min_amount_inr=int(purchase.amount or 0) or None,
                ):
                    billing.mark_paid(purchase.id, order_id=purchase.order_id)
                    purchase = CoupleReportPurchase.query.get(purchase_id)
            except Exception as e:
                log.warning("[birth_time_rectification] status poll: %s", e)

        entitled = purchase.status == "paid" or billing.payment_bypass()
        return jsonify(
            {
                "status": purchase.status,
                "entitled": bool(entitled),
                "purchase_id": purchase.id,
                "amount": purchase.amount,
            }
        )
