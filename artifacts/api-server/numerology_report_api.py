"""Life Mastery numerology report — entitlement + Razorpay checkout."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from flask import jsonify, request

import numerology_report_billing as billing
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
    lang = (data.get("lang") or "hinglish").strip()
    params = data.get("params")
    if isinstance(params, dict) and params.get("name") and params.get("dob"):
        cp = billing.numerology_cache_params(
            lang=lang,
            name=str(params.get("name", "")).strip(),
            dob=str(params.get("dob", "")).strip(),
            mobile=(params.get("mobile") or None),
            vehicle=(params.get("vehicle") or None),
            house=(params.get("house") or None),
            tob=(params.get("tob") or None),
            lat=params.get("lat"),
            lon=params.get("lon"),
            tz=params.get("tz"),
            place=(params.get("place") or None),
        )
        return cp, lang
    name = (data.get("name") or "").strip()
    dob = (data.get("dob") or "").strip()
    if not name or not dob:
        return None, None
    cp = billing.numerology_cache_params(
        lang=lang,
        name=name,
        dob=dob,
        mobile=(data.get("mobile") or None),
        vehicle=(data.get("vehicle") or None),
        house=(data.get("house") or None),
        tob=(data.get("tob") or None),
        lat=data.get("lat"),
        lon=data.get("lon"),
        tz=data.get("tz"),
        place=(data.get("place") or None),
    )
    return cp, lang


def pdf_access_gate(user_id: int, cache_params: dict):
    access = billing.check_access(user_id, cache_params)
    if access.get("cached_pdf"):
        return access["cached_pdf"], None
    if access.get("entitled"):
        return None, None
    spec = billing.catalog_for(billing.PRODUCT_LIFE_MASTERY) or {}
    return None, (
        jsonify(
            {
                "error": "payment_required",
                "product": billing.PRODUCT_LIFE_MASTERY,
                "label": spec.get("label"),
                "amount_inr": access.get("amount_inr"),
                "params_hash": access.get("params_hash"),
                "message": "Payment required for Life Mastery Report. Same inputs after pay = free re-download.",
            }
        ),
        402,
    )


def register_numerology_report_routes(app) -> None:
    @app.route("/api/numerology-report/check", methods=["POST", "OPTIONS"])
    def numerology_report_check():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        cp, lang = _params_from_body(data)
        if not cp:
            return jsonify({"error": "missing_fields", "message": "name and dob required"}), 400
        access = billing.check_access(user.id, cp)
        return jsonify(
            {
                "entitled": bool(access.get("entitled")),
                "payment_required": bool(access.get("payment_required")),
                "cache_hit": bool(access.get("cache_hit")),
                "already_paid": bool(access.get("already_paid")),
                "product": billing.PRODUCT_LIFE_MASTERY,
                "amount_inr": access.get("amount_inr"),
                "label": access.get("label"),
                "params_hash": access.get("params_hash"),
                "payment_bypass": billing.payment_bypass(),
            }
        )

    @app.route("/api/numerology-report/create-order", methods=["POST", "OPTIONS"])
    def numerology_report_create_order():
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
            return jsonify({"error": "missing_fields"}), 400

        payload, perr = billing.create_purchase_intent(user.id, cp, lang or cp.get("lang", "hinglish"))
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
        order_id = f"NM{user.id}_{purchase.id}_{ts}"

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=amount,
                notes={
                    "kind": "numerology_report",
                    "purchase_id": str(purchase.id),
                    "product": billing.PRODUCT_LIFE_MASTERY,
                },
            )
        except Exception as e:
            log.error("[numerology_report] Razorpay order failed: %s", e)
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
                product=billing.PRODUCT_LIFE_MASTERY,
                label=payload.get("label"),
                params_hash=payload.get("params_hash"),
            )
        )

    @app.route("/api/numerology-report/purchase-status/<int:purchase_id>", methods=["GET", "OPTIONS"])
    def numerology_report_purchase_status(purchase_id: int):
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        from models import CoupleReportPurchase, db

        purchase = CoupleReportPurchase.query.get(purchase_id)
        if not purchase or purchase.user_id != user.id or purchase.product != billing.PRODUCT_LIFE_MASTERY:
            return jsonify({"error": "not_found"}), 404

        if purchase.status == "created" and purchase.order_id and pg.configured():
            try:
                if pg.is_receipt_paid(purchase.order_id):
                    billing.mark_paid(purchase.id, order_id=purchase.order_id)
                    purchase = CoupleReportPurchase.query.get(purchase_id)
            except Exception as exc:
                log.warning("[numerology_report] poll RZ: %s", exc)

        stored = json.loads(purchase.params_json or "{}")
        cp = stored.get("params") or {}
        access = billing.check_access(user.id, cp)
        return jsonify(
            {
                "purchase_id": purchase.id,
                "status": purchase.status,
                "product": purchase.product,
                "entitled": bool(access.get("entitled")),
                "paid_at": purchase.paid_at.isoformat() if purchase.paid_at else None,
            }
        )
