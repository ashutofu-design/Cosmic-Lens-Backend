"""Career unlock — Razorpay checkout + access check."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import jsonify, request

import career_billing as billing
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


def register_career_routes(app) -> None:
    @app.route("/api/career/check", methods=["GET", "POST", "OPTIONS"])
    def career_check():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        access = billing.check_access(user.id)
        return jsonify({**access, "payment_bypass": billing.payment_bypass()})

    @app.route("/api/career/create-order", methods=["POST", "OPTIONS"])
    def career_create_order():
        if request.method == "OPTIONS":
            return "", 204
        if not pg.configured():
            body, code = pg.not_configured_error()
            return jsonify(body), code

        user, err = _resolve_user()
        if err:
            return err

        access = billing.check_access(user.id)
        if access.get("career_unlocked") and not billing.payment_bypass():
            return jsonify(
                {
                    **access,
                    "already_entitled": True,
                    "payment_required": False,
                }
            )

        amount = billing.price_inr()
        ts = int(datetime.now(_UTC).timestamp())
        order_id = f"CA{user.id}_{ts}"

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=amount,
                notes={
                    "kind": "career_unlock",
                    "user_id": str(user.id),
                },
            )
        except Exception as exc:
            log.error("[career] Razorpay order failed: %s", exc)
            return jsonify({"error": "razorpay_order_failed", "detail": str(exc)}), 502

        from models import db

        user.career_unlock_order_id = order_id
        db.session.commit()

        return jsonify(
            pg.checkout_response(
                order_id,
                rz_order,
                amount,
                user,
                label=billing.check_access(user.id).get("label"),
            )
        )

    @app.route("/api/career/access-status", methods=["GET", "OPTIONS"])
    def career_access_status():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err

        order_id = (request.args.get("order_id") or "").strip() or (
            getattr(user, "career_unlock_order_id", None) or ""
        )

        if not getattr(user, "career_unlocked", False) and order_id and pg.configured():
            try:
                if pg.is_receipt_paid(order_id):
                    billing.mark_unlocked(user.id, order_id=order_id)
            except Exception as exc:
                log.warning("[career] poll RZ: %s", exc)

        from flask_app import User

        user = User.query.get(user.id)
        access = billing.check_access(user.id)
        return jsonify(
            {
                **access,
                "order_id": order_id or None,
                "paid_at": user.career_unlocked_at.isoformat()
                if getattr(user, "career_unlocked_at", None)
                else None,
            }
        )
