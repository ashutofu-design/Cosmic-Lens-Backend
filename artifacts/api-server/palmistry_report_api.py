"""Palmistry Pro — entitlement + Razorpay checkout."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import jsonify, request

import palmistry_report_billing as billing
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


def _plan_urgent(data: dict) -> tuple[str, bool, str]:
    plan = str(data.get("plan") or "pdf").strip().lower()
    if plan not in ("pdf", "vip"):
        plan = "pdf"
    urgent = bool(data.get("urgent") or data.get("priority"))
    session_id = str(data.get("session_id") or "").strip()
    return plan, urgent, session_id


def register_palmistry_report_routes(app) -> None:
    @app.route("/api/palmistry-report/check", methods=["POST", "OPTIONS"])
    def palmistry_report_check():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        plan, urgent, session_id = _plan_urgent(data)
        access = billing.check_access(user.id, plan, urgent, session_id)
        return jsonify(
            {
                "entitled": bool(access.get("entitled")),
                "payment_required": bool(access.get("payment_required")),
                "already_paid": bool(access.get("already_paid")),
                "product": access.get("product"),
                "amount_inr": access.get("amount_inr"),
                "label": access.get("label"),
                "params_hash": access.get("params_hash"),
                "purchase_id": access.get("purchase_id"),
                "plan": plan,
                "urgent": urgent,
                "payment_bypass": billing.payment_bypass(),
            }
        )

    @app.route("/api/palmistry-report/create-order", methods=["POST", "OPTIONS"])
    def palmistry_report_create_order():
        if request.method == "OPTIONS":
            return "", 204
        if not pg.configured():
            body, code = pg.not_configured_error()
            return jsonify(body), code

        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        plan, urgent, session_id = _plan_urgent(data)

        payload, perr = billing.create_purchase_intent(user.id, plan, urgent, session_id)
        if perr:
            return jsonify({"error": perr}), 400
        if payload.get("already_entitled"):
            return jsonify({**payload, "payment_required": False})

        purchase_id = payload["purchase_id"]
        amount = int(payload["amount"])
        from models import CoupleReportPurchase, db

        purchase = CoupleReportPurchase.query.get(purchase_id)
        if not purchase:
            return jsonify({"error": "purchase_not_found"}), 404

        ts = int(datetime.now(_UTC).timestamp())
        order_id = f"PL{user.id}_{purchase.id}_{ts}"

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=amount,
                notes={
                    "kind": "palmistry_report",
                    "purchase_id": str(purchase.id),
                    "product": payload.get("product") or billing.product_for_plan(plan),
                    "plan": plan,
                    "urgent": "1" if urgent else "0",
                },
            )
        except Exception as e:
            log.error("[palmistry_report] Razorpay order failed: %s", e)
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
                product=payload.get("product"),
                label=payload.get("label"),
                params_hash=payload.get("params_hash"),
            )
        )

    @app.route("/api/palmistry-report/purchase-status/<int:purchase_id>", methods=["GET", "OPTIONS"])
    def palmistry_report_purchase_status(purchase_id: int):
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
            or (purchase.product or "") not in billing.VALID_PRODUCTS
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
            except Exception as exc:
                log.warning("[palmistry_report] poll RZ: %s", exc)

        return jsonify(
            {
                "purchase_id": purchase.id,
                "status": purchase.status,
                "product": purchase.product,
                "entitled": purchase.status == "paid",
                "paid_at": purchase.paid_at.isoformat() if purchase.paid_at else None,
                "amount": purchase.amount,
            }
        )
