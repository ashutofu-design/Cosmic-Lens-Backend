"""Cosmic Intelligence V1 question-pack routes — Razorpay checkout + wallet."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import jsonify, request

import ask_v1_billing as billing
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


def register_ask_v1_routes(app) -> None:
    @app.route("/api/ask-v1/packs", methods=["GET", "OPTIONS"])
    def ask_v1_packs():
        if request.method == "OPTIONS":
            return "", 204
        return jsonify({"ok": True, "packs": billing.list_packs()})

    @app.route("/api/ask-v1/wallet", methods=["GET", "OPTIONS"])
    def ask_v1_wallet():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        return jsonify({"ok": True, **billing.wallet_snapshot(user)})

    @app.route("/api/ask-v1/create-order", methods=["POST", "OPTIONS"])
    def ask_v1_create_order():
        if request.method == "OPTIONS":
            return "", 204

        user, err = _resolve_user()
        if err:
            return err

        data = request.get_json(silent=True) or {}
        pack_id = (data.get("pack_id") or "").strip().lower()
        pack = billing.get_pack(pack_id)
        if not pack:
            return jsonify({"error": "invalid_pack", "packs": billing.list_packs()}), 400

        referral_code = (data.get("referral_code") or data.get("ref") or "").strip()
        if referral_code:
            try:
                import pack_referral as _pref

                _pref.attach_referrer(user, referral_code)
            except Exception:
                pass

        # Dev / no Razorpay: grant instantly so UI can be tested.
        if billing.payment_bypass():
            from database import db
            from models import AskV1Purchase

            ts = int(datetime.now(_UTC).timestamp())
            order_id = f"AQ{user.id}_{pack_id}_{ts}"
            purchase = AskV1Purchase(
                user_id=user.id,
                pack_id=pack["id"],
                amount=pack["price_inr"],
                order_id=order_id,
                status="paid",
                granted=False,
                paid_at=datetime.utcnow(),
            )
            db.session.add(purchase)
            db.session.commit()
            billing.grant_purchase_idempotent(purchase)
            snap = billing.wallet_snapshot(user)
            return jsonify(
                {
                    "ok": True,
                    "already_entitled": True,
                    "payment_required": False,
                    "payment_bypass": True,
                    "pack_id": pack["id"],
                    "order_id": order_id,
                    **snap,
                }
            )

        if not pg.configured():
            return jsonify({"error": "razorpay_not_configured"}), 503

        from database import db
        from models import AskV1Purchase

        ts = int(datetime.now(_UTC).timestamp())
        order_id = f"AQ{user.id}_{pack_id}_{ts}"
        purchase = AskV1Purchase(
            user_id=user.id,
            pack_id=pack["id"],
            amount=pack["price_inr"],
            order_id=order_id,
            status="created",
            granted=False,
        )
        db.session.add(purchase)
        db.session.commit()

        try:
            rz_order = pg.create_order(
                receipt=order_id,
                amount_inr=pack["price_inr"],
                notes={
                    "kind": "ask_v1_pack",
                    "user_id": str(user.id),
                    "pack_id": pack["id"],
                    "purchase_id": str(purchase.id),
                },
            )
        except Exception as exc:
            log.error("[ask_v1] Razorpay order failed: %s", exc)
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
                    label=f"V1 {pack['label']} · {pack['questions']} questions",
                ),
                "purchase_id": purchase.id,
                "pack_id": pack["id"],
                "questions": pack["questions"],
                "days": pack["days"],
            }
        )

    @app.route(
        "/api/ask-v1/purchase-status/<int:purchase_id>",
        methods=["GET", "OPTIONS"],
    )
    def ask_v1_purchase_status(purchase_id: int):
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err

        from models import AskV1Purchase

        purchase = AskV1Purchase.query.get(purchase_id)
        if not purchase or purchase.user_id != user.id:
            return jsonify({"error": "not_found"}), 404

        if purchase.status == "created" and purchase.order_id and pg.configured():
            try:
                if pg.is_receipt_paid(
                    purchase.order_id,
                    min_amount_inr=int(purchase.amount or 0) or None,
                ):
                    billing.mark_purchase_paid_and_grant(purchase_id=purchase.id)
                    purchase = AskV1Purchase.query.get(purchase_id)
            except Exception as exc:
                log.warning("[ask_v1] poll RZ: %s", exc)

        snap = billing.wallet_snapshot(user)
        return jsonify(
            {
                "ok": True,
                "purchase_id": purchase.id,
                "pack_id": purchase.pack_id,
                "status": purchase.status,
                "granted": bool(purchase.granted),
                "paid": purchase.status == "paid",
                "entitled": snap.get("active"),
                **snap,
            }
        )
