"""Gemstone shop API — pricing, referral codes, Razorpay checkout."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import jsonify, request

import gemstone_billing as billing
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


def register_gemstone_routes(app) -> None:
    @app.route("/api/gemstone/catalog", methods=["GET", "OPTIONS"])
    def gemstone_catalog():
        if request.method == "OPTIONS":
            return "", 204
        return jsonify({"items": billing.catalog()})

    @app.route("/api/gemstone/my-referral", methods=["GET", "OPTIONS"])
    def gemstone_my_referral():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        code = billing.referral_code_for_user(user.id)
        return jsonify(
            {
                "referral_code": code,
                "share_message": (
                    f"Use my Cosmic Lens code {code} on Ceylon Pukhraj purchase — "
                    "you get a referral discount, I earn a reward after delivery."
                ),
            }
        )

    @app.route("/api/gemstone/quote", methods=["POST", "OPTIONS"])
    def gemstone_quote():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        sku = (data.get("sku") or "").strip()
        referral_code = (data.get("referral_code") or "").strip() or None
        q, perr = billing.quote(sku, user.id, referral_code)
        if perr:
            return jsonify({"error": perr}), 400
        return jsonify(q)

    @app.route("/api/gemstone/create-order", methods=["POST", "OPTIONS"])
    def gemstone_create_order():
        if request.method == "OPTIONS":
            return "", 204
        if not pg.configured():
            body, code = pg.not_configured_error()
            return jsonify(body), code

        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        sku = (data.get("sku") or "").strip()
        referral_code = (data.get("referral_code") or "").strip() or None

        payload, perr = billing.create_order_intent(user.id, sku, referral_code)
        if perr:
            return jsonify({"error": perr}), 400
        if not payload:
            return jsonify({"error": "order_failed"}), 400

        order_row_id = payload["order_row_id"]
        amount = payload["amount_inr"]
        ts = int(datetime.now(_UTC).timestamp())
        order_id = f"GM{user.id}_{order_row_id}_{ts}"

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=amount,
                notes={
                    "kind": "gemstone",
                    "gemstone_order_id": str(order_row_id),
                    "sku": sku,
                    "user_id": str(user.id),
                    "referrer_user_id": str(payload.get("referrer_user_id") or ""),
                },
            )
        except Exception as exc:
            log.error("[gemstone] Razorpay order failed: %s", exc)
            return jsonify({"error": "razorpay_order_failed", "detail": str(exc)}), 502

        from models import GemstoneOrder, db

        row = GemstoneOrder.query.get(order_row_id)
        if row:
            row.order_id = order_id
            db.session.commit()

        return jsonify(
            pg.checkout_response(
                order_id,
                rz_order,
                amount,
                user,
                purchase_id=order_row_id,
                gemstone_order_id=order_row_id,
                sku=sku,
                label=payload.get("label"),
                discount_type=payload.get("discount_type"),
                mrp_inr=payload.get("mrp_inr"),
                discount_inr=payload.get("discount_inr"),
            )
        )

    @app.route("/api/gemstone/purchase-status/<int:order_row_id>", methods=["GET", "OPTIONS"])
    def gemstone_purchase_status(order_row_id: int):
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        from models import GemstoneOrder

        row = GemstoneOrder.query.get(order_row_id)
        if not row or row.user_id != user.id:
            return jsonify({"error": "not_found"}), 404

        if row.status == "created" and row.order_id and pg.configured():
            try:
                if pg.is_receipt_paid(
                    row.order_id,
                    min_amount_inr=int(row.amount or 0) or None,
                ):
                    billing.mark_paid(row.id, order_id=row.order_id)
                    row = GemstoneOrder.query.get(order_row_id)
            except Exception as exc:
                log.warning("[gemstone] poll RZ: %s", exc)

        return jsonify(billing.order_status_payload(row))

    @app.route("/gemstone_media/<path:filename>", methods=["GET"])
    def gemstone_media(filename: str):
        import os
        from flask import send_from_directory

        base = os.path.join(os.path.dirname(__file__), "gemstone_media")
        return send_from_directory(base, filename)
