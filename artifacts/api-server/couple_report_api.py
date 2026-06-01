"""Couple report entitlement + Razorpay checkout (Milan Pro / Love Reality Pro)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from flask import Response, jsonify, request

import couple_report_billing as billing
import payment_gateway as pg
import report_cache as rc

log = logging.getLogger(__name__)

_UTC = timezone.utc


def _resolve_user():
    from flask_app import User, get_authed_user

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


def pdf_access_gate(user_id: int, product: str, p1: dict, p2: dict, lang: str, k1=None, k2=None):
    """
    Returns (cached_pdf_bytes | None, error_response | None).
    If cached_pdf_bytes — return immediately. If error_response — abort. Else proceed.
    """
    cp = billing.cache_params_from_birth(lang, p1, p2, k1, k2)
    access = billing.check_access(user_id, product, cp)
    if access.get("cached_pdf"):
        return access["cached_pdf"], None
    if access.get("entitled"):
        return None, None
    spec = billing.catalog_for(product) or {}
    return None, (
        jsonify(
            {
                "error": "payment_required",
                "product": product,
                "label": spec.get("label"),
                "amount_inr": access.get("amount_inr"),
                "params_hash": access.get("params_hash"),
                "message": "Payment required for this couple. Same couple after pay = free re-download.",
            }
        ),
        402,
    )


def register_couple_report_routes(app) -> None:
    """Register billing routes on the Flask app."""

    @app.route("/api/couple-report/check", methods=["POST", "OPTIONS"])
    def couple_report_check():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        product = (data.get("product") or "").strip()
        if product not in billing.VALID_PRODUCTS:
            return jsonify({"error": "invalid_product", "valid": list(billing.VALID_PRODUCTS)}), 400
        p1 = data.get("p1") or {}
        p2 = data.get("p2") or {}
        lang = (data.get("lang") or "en").strip()
        cp = billing.cache_params_from_birth(lang, p1, p2)
        access = billing.check_access(user.id, product, cp)
        return jsonify(
            {
                "entitled": bool(access.get("entitled")),
                "payment_required": bool(access.get("payment_required")),
                "cache_hit": bool(access.get("cache_hit")),
                "already_paid": bool(access.get("already_paid")),
                "product": product,
                "amount_inr": access.get("amount_inr"),
                "label": access.get("label"),
                "params_hash": access.get("params_hash"),
                "payment_bypass": billing.payment_bypass(),
            }
        )

    @app.route("/api/couple-report/create-order", methods=["POST", "OPTIONS"])
    def couple_report_create_order():
        if request.method == "OPTIONS":
            return "", 204
        if not pg.configured():
            body, code = pg.not_configured_error()
            return jsonify(body), code

        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        product = (data.get("product") or "").strip()
        if product not in billing.VALID_PRODUCTS:
            return jsonify({"error": "invalid_product"}), 400
        p1 = data.get("p1") or {}
        p2 = data.get("p2") or {}
        lang = (data.get("lang") or "en").strip()
        if not isinstance(p1, dict) or not isinstance(p2, dict):
            return jsonify({"error": "expected_p1_p2"}), 400

        payload, perr = billing.create_purchase_intent(user.id, product, p1, p2, lang)
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
        order_id = f"CR{user.id}_{purchase.id}_{ts}"

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=amount,
                notes={
                    "kind": "couple_report",
                    "purchase_id": str(purchase.id),
                    "product": product,
                },
            )
        except Exception as e:
            log.error("[couple_report] Razorpay order failed: %s", e)
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
                product=product,
                label=payload.get("label"),
                params_hash=payload.get("params_hash"),
            )
        )

    @app.route("/api/couple-report/purchase-status/<int:purchase_id>", methods=["GET", "OPTIONS"])
    def couple_report_purchase_status(purchase_id: int):
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        from models import CoupleReportPurchase, db

        purchase = CoupleReportPurchase.query.get(purchase_id)
        if not purchase or purchase.user_id != user.id:
            return jsonify({"error": "not_found"}), 404

        if purchase.status == "created" and purchase.order_id and pg.configured():
            try:
                if pg.is_receipt_paid(purchase.order_id):
                    billing.mark_paid(purchase.id, order_id=purchase.order_id)
                    purchase = CoupleReportPurchase.query.get(purchase_id)
            except Exception as exc:
                log.warning("[couple_report] poll RZ: %s", exc)

        cp = json.loads(purchase.params_json or "{}")
        access = billing.check_access(
            user.id,
            purchase.product,
            billing.cache_params_from_birth(
                purchase.lang,
                cp.get("p1") or {},
                cp.get("p2") or {},
            ),
        )
        return jsonify(
            {
                "purchase_id": purchase.id,
                "status": purchase.status,
                "product": purchase.product,
                "entitled": bool(access.get("entitled")),
                "paid_at": purchase.paid_at.isoformat() if purchase.paid_at else None,
            }
        )
