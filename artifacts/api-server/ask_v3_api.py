"""Cosmic Intelligence V3 live-pack routes — Razorpay checkout then queue."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import jsonify, request

import ask_v3_billing as billing
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


def register_ask_v3_routes(app) -> None:
    @app.route("/api/ask-v3/packs", methods=["GET", "OPTIONS"])
    def ask_v3_packs():
        if request.method == "OPTIONS":
            return "", 204
        return jsonify({"ok": True, "packs": billing.list_packs()})

    @app.route("/api/ask-v3/create-order", methods=["POST", "OPTIONS"])
    def ask_v3_create_order():
        if request.method == "OPTIONS":
            return "", 204

        user, err = _resolve_user()
        if err:
            return err

        data = request.get_json(silent=True) or {}
        pack_id = str(data.get("pack_id") or "").strip()
        pack = billing.get_pack(pack_id)
        if not pack:
            return jsonify({"error": "invalid_pack", "packs": billing.list_packs()}), 400

        preferred_language = str(
            data.get("preferred_language") or data.get("lang") or ""
        ).strip()
        referral_code = (data.get("referral_code") or data.get("ref") or "").strip()
        if referral_code:
            try:
                import pack_referral as _pref

                _pref.attach_referrer(user, referral_code)
            except Exception:
                pass

        from database import db
        from models import V3LivePurchase

        # Dev / no Razorpay: charge as paid + enqueue immediately.
        if billing.payment_bypass():
            ts = int(datetime.now(_UTC).timestamp())
            order_id = f"V3{user.id}_{pack_id}_{ts}"
            purchase = V3LivePurchase(
                user_id=user.id,
                pack_id=pack["id"],
                amount=pack["price_inr"],
                order_id=order_id,
                status="paid",
                granted=False,
                preferred_language=preferred_language or None,
                paid_at=datetime.utcnow(),
            )
            db.session.add(purchase)
            db.session.commit()
            result = billing.grant_purchase_idempotent(purchase)
            return jsonify(
                {
                    "ok": True,
                    "already_entitled": True,
                    "payment_required": False,
                    "payment_bypass": True,
                    "pack_id": pack["id"],
                    "order_id": order_id,
                    "purchase_id": purchase.id,
                    "session_id": result.get("session_id") or purchase.session_id,
                    "granted": True,
                    "entitled": True,
                    "minutes": pack["minutes"],
                    "label": pack["label"],
                    "amount": pack["price_inr"],
                }
            )

        if not pg.configured():
            return jsonify({"error": "razorpay_not_configured"}), 503

        ts = int(datetime.now(_UTC).timestamp())
        order_id = f"V3{user.id}_{pack_id}_{ts}"
        purchase = V3LivePurchase(
            user_id=user.id,
            pack_id=pack["id"],
            amount=pack["price_inr"],
            order_id=order_id,
            status="created",
            granted=False,
            preferred_language=preferred_language or None,
        )
        db.session.add(purchase)
        db.session.commit()

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=pack["price_inr"],
                notes={
                    "kind": "ask_v3_live",
                    "user_id": str(user.id),
                    "pack_id": pack["id"],
                    "purchase_id": str(purchase.id),
                },
            )
        except Exception as exc:
            log.error("[ask_v3] Razorpay order failed: %s", exc)
            purchase.status = "failed"
            db.session.commit()
            return jsonify({"error": "razorpay_order_failed", "detail": str(exc)}), 502

        return jsonify(
            {
                **pg.checkout_response(
                    order_id,
                    rz_order,
                    pack["price_inr"],
                    user,
                    label=f"V3 Live · {pack['label']}",
                ),
                "purchase_id": purchase.id,
                "pack_id": pack["id"],
                "minutes": pack["minutes"],
            }
        )

    @app.route(
        "/api/ask-v3/purchase-status/<int:purchase_id>",
        methods=["GET", "OPTIONS"],
    )
    def ask_v3_purchase_status(purchase_id: int):
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err

        from models import V3LivePurchase

        purchase = V3LivePurchase.query.get(purchase_id)
        if not purchase or purchase.user_id != user.id:
            return jsonify({"error": "not_found"}), 404

        if purchase.status == "created" and purchase.order_id and pg.configured():
            try:
                if pg.is_receipt_paid(
                    purchase.order_id,
                    min_amount_inr=int(purchase.amount or 0) or None,
                ):
                    billing.mark_purchase_paid_and_grant(purchase_id=purchase.id)
                    purchase = V3LivePurchase.query.get(purchase_id)
            except Exception as exc:
                log.warning("[ask_v3] poll RZ: %s", exc)

        # Paid but session missing — finish grant.
        if purchase and purchase.status == "paid" and not purchase.granted:
            billing.grant_purchase_idempotent(purchase)
            purchase = V3LivePurchase.query.get(purchase_id)
        elif purchase and purchase.granted and not purchase.session_id:
            billing.grant_purchase_idempotent(purchase)
            purchase = V3LivePurchase.query.get(purchase_id)

        pack = billing.get_pack(purchase.pack_id) or {}
        return jsonify(
            {
                "ok": True,
                "purchase_id": purchase.id,
                "pack_id": purchase.pack_id,
                "status": purchase.status,
                "granted": bool(purchase.granted),
                "paid": purchase.status == "paid",
                "entitled": bool(purchase.granted and purchase.session_id),
                "session_id": purchase.session_id or "",
                "minutes": pack.get("minutes"),
                "label": pack.get("label"),
                "amount": purchase.amount,
            }
        )
