"""
Cosmic Intelligence V3 — live session packs (one-time Razorpay).

Catalog (minutes → INR):
  15 → ₹399 · 30 → ₹699 · 45 → ₹999 · 60 → ₹1299

Payment must succeed before a live queue session is created.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import update

# Mirror cosmic_intelligence_v3_sessions.PACKS
V3_PACK_CATALOG = {
    "15": {"id": "15", "minutes": 15, "price_inr": 399, "label": "15 min"},
    "30": {"id": "30", "minutes": 30, "price_inr": 699, "label": "30 min"},
    "45": {"id": "45", "minutes": 45, "price_inr": 999, "label": "45 min"},
    "60": {"id": "60", "minutes": 60, "price_inr": 1299, "label": "60 min"},
}


def payment_bypass() -> bool:
    from billing_security import payment_bypass_from_env

    return payment_bypass_from_env(
        "ASK_V3_PAYMENT_BYPASS",
        "ASK_V1_PAYMENT_BYPASS",
    )


def get_pack(pack_id: str) -> dict | None:
    return V3_PACK_CATALOG.get((pack_id or "").strip())


def list_packs() -> list[dict]:
    return [dict(p) for p in V3_PACK_CATALOG.values()]


def _create_session_for_purchase(purchase) -> str | None:
    """Enqueue V3 live session after payment. Returns session_id."""
    from cosmic_intelligence_v3_sessions import create_v3_session_request
    from models import User

    user = User.query.get(int(purchase.user_id))
    if not user:
        return None

    cosmo_user_id = ""
    try:
        from cosmo_user_id import cosmo_display_id_for_user_id

        cosmo_user_id = cosmo_display_id_for_user_id(user.id)
    except Exception:
        cosmo_user_id = ""

    preferred = (getattr(purchase, "preferred_language", None) or "").strip()
    rec = create_v3_session_request(
        user_id=int(user.id),
        pack_id=str(purchase.pack_id),
        user_email=getattr(user, "email", None) or "",
        user_phone=getattr(user, "phone", None) or "",
        user_name=getattr(user, "name", None) or "",
        cosmo_user_id=cosmo_user_id,
        preferred_language=preferred
        or getattr(user, "preferred_language", None)
        or "",
    )
    sid = str(rec.get("session_id") or "")
    return sid or None


def grant_purchase_idempotent(purchase) -> dict:
    """Mark paid purchase granted and create V3 queue session (once)."""
    from database import db
    from models import V3LivePurchase

    if not purchase:
        return {"granted": False, "reason": "missing_purchase"}

    pack = get_pack(purchase.pack_id)
    if not pack:
        return {"granted": False, "reason": "unknown_pack"}

    # Already granted with session.
    if purchase.granted and purchase.session_id:
        return {
            "granted": True,
            "reason": "already_granted",
            "session_id": purchase.session_id,
            "pack_id": pack["id"],
            "minutes": pack["minutes"],
        }

    # Paid + granted flag but session missing (retry).
    if purchase.status == "paid" and purchase.granted and not purchase.session_id:
        try:
            session_id = _create_session_for_purchase(purchase)
            if session_id:
                purchase.session_id = session_id
                db.session.commit()
                try:
                    import pack_referral as _pref

                    _pref.grant_referrer_on_pack_purchase(
                        buyer_user_id=int(purchase.user_id),
                        source_kind="v3",
                        source_key=str(session_id),
                    )
                except Exception:
                    pass
            return {
                "granted": True,
                "session_id": session_id,
                "pack_id": pack["id"],
                "minutes": pack["minutes"],
            }
        except Exception as exc:
            return {"granted": True, "note": f"session_retry_failed:{exc}"}

    claim = db.session.execute(
        update(V3LivePurchase)
        .where(V3LivePurchase.id == purchase.id)
        .where(V3LivePurchase.status == "paid")
        .where(V3LivePurchase.granted.is_(False))
        .values(granted=True)
    )
    if claim.rowcount != 1:
        db.session.commit()
        db.session.refresh(purchase)
        if purchase.granted and purchase.session_id:
            return {
                "granted": True,
                "reason": "already_granted",
                "session_id": purchase.session_id,
                "pack_id": pack["id"],
                "minutes": pack["minutes"],
            }
        return {"granted": False, "reason": "already_granted_or_not_paid"}
    db.session.commit()

    session_id = None
    try:
        session_id = _create_session_for_purchase(purchase)
        if session_id:
            purchase.session_id = session_id
            db.session.commit()
    except Exception as exc:
        return {
            "granted": True,
            "note": f"session_create_failed:{exc}",
            "pack_id": pack["id"],
            "minutes": pack["minutes"],
        }

    try:
        import pack_referral as _pref

        _pref.grant_referrer_on_pack_purchase(
            buyer_user_id=int(purchase.user_id),
            source_kind="v3",
            source_key=str(session_id or purchase.id),
        )
    except Exception:
        pass

    # Founder / admin alerts (same as /request path)
    try:
        if session_id:
            from cosmic_intelligence_v3_sessions import get_v3_session
            from order_founder_alert import notify_founder_v3_live_chat_request

            rec = get_v3_session(session_id) or {}
            if rec:
                notify_founder_v3_live_chat_request(rec)
    except Exception:
        pass
    try:
        if session_id:
            from admin_push import notify_admin_push_v3_request
            from cosmic_intelligence_v3_sessions import get_v3_session

            rec = get_v3_session(session_id) or {}
            if rec:
                notify_admin_push_v3_request(rec)
    except Exception:
        pass

    return {
        "granted": True,
        "session_id": session_id,
        "pack_id": pack["id"],
        "minutes": pack["minutes"],
        "price_inr": pack["price_inr"],
        "label": pack["label"],
    }


def mark_purchase_paid_and_grant(
    purchase_id: int | None = None, order_id: str | None = None
) -> dict:
    from database import db
    from models import V3LivePurchase

    purchase = None
    if purchase_id:
        purchase = V3LivePurchase.query.get(int(purchase_id))
    elif order_id:
        purchase = V3LivePurchase.query.filter_by(order_id=order_id).first()
    if not purchase:
        return {"granted": False, "reason": "not_found"}

    if purchase.status != "paid":
        purchase.status = "paid"
        purchase.paid_at = datetime.utcnow()
        db.session.commit()

    return grant_purchase_idempotent(purchase)


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    try:
        pid = tags.get("purchase_id")
        from models import V3LivePurchase
        import payment_gateway as pg

        purchase = None
        if pid:
            purchase = V3LivePurchase.query.get(int(pid))
        elif order_id:
            purchase = V3LivePurchase.query.filter_by(order_id=order_id).first()
        min_inr = int(purchase.amount or 0) if purchase else None
        if not pg.is_receipt_paid(order_id, min_amount_inr=min_inr):
            return False
        result = mark_purchase_paid_and_grant(
            purchase_id=int(pid) if pid else None,
            order_id=order_id,
        )
        return bool(
            result.get("granted")
            or result.get("reason") in ("already_granted", "already_granted_or_not_paid")
        )
    except Exception:
        return False
