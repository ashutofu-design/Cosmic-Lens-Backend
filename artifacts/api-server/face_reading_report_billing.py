"""Face Reading PRO report — pay-per-session (₹299 default)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

PRODUCT_FACE_READING_PRO = "face_reading_pro"

CATALOG: dict[str, dict[str, Any]] = {
    PRODUCT_FACE_READING_PRO: {
        "label": "Face Reading PRO Report",
        "amount_inr": int(os.environ.get("FACE_READING_PRO_PRICE_INR", "299")),
    },
}


def payment_bypass() -> bool:
    return (os.environ.get("FACE_READING_PAYMENT_BYPASS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def payment_required() -> bool:
    if payment_bypass():
        return False
    return (os.environ.get("FACE_READING_PAYMENT_REQUIRED") or "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def face_cache_params(
    session_id: str,
    lang: str,
    age: str | None = None,
    gender: str | None = None,
) -> dict[str, Any]:
    return {
        "session_id": (session_id or "").strip(),
        "lang": (lang or "hinglish").strip(),
        "age": (age or "").strip() or None,
        "gender": (gender or "").strip() or None,
    }


def params_hash(cache_params: dict[str, Any]) -> str:
    return rc._hash_params(cache_params)


def catalog_for(product: str) -> dict[str, Any] | None:
    return CATALOG.get(product)


def _get_purchase_model():
    from models import CoupleReportPurchase

    return CoupleReportPurchase


def _user_is_pro(user_id: int) -> bool:
    try:
        from models import User
        from subscription_helper import effective_plan

        user = User.query.get(int(user_id))
        return bool(user and effective_plan(user) == "pro")
    except Exception:
        return False


def find_paid_purchase(user_id: int, phash: str):
    if not user_id:
        return None
    CoupleReportPurchase = _get_purchase_model()
    return (
        CoupleReportPurchase.query.filter_by(
            user_id=int(user_id),
            product=PRODUCT_FACE_READING_PRO,
            params_hash=phash,
            status="paid",
        )
        .order_by(CoupleReportPurchase.paid_at.desc())
        .first()
    )


def check_access(user_id: int, cache_params: dict[str, Any]) -> dict[str, Any]:
    spec = catalog_for(PRODUCT_FACE_READING_PRO) or {}
    phash = params_hash(cache_params)
    out: dict[str, Any] = {
        "product": PRODUCT_FACE_READING_PRO,
        "params_hash": phash,
        "label": spec.get("label", PRODUCT_FACE_READING_PRO),
        "amount_inr": spec.get("amount_inr", 299),
        "entitled": False,
        "cached_pdf": None,
        "payment_required": False,
        "already_paid": False,
        "cache_hit": False,
        "is_pro": False,
    }

    if _user_is_pro(user_id):
        out["entitled"] = True
        out["is_pro"] = True
        out["cached_pdf"] = rc.find(user_id, "face_reading", cache_params)
        out["cache_hit"] = bool(out["cached_pdf"])
        return out

    if not payment_required():
        out["entitled"] = True
        out["cached_pdf"] = rc.find(user_id, "face_reading", cache_params)
        out["cache_hit"] = bool(out["cached_pdf"])
        return out

    cached = rc.find(user_id, "face_reading", cache_params)
    if cached:
        out["entitled"] = True
        out["cached_pdf"] = cached
        out["cache_hit"] = True
        return out

    paid = find_paid_purchase(user_id, phash)
    if paid:
        out["entitled"] = True
        out["already_paid"] = True
        return out

    out["payment_required"] = True
    return out


def create_purchase_intent(user_id: int, cache_params: dict[str, Any], lang: str):
    spec = catalog_for(PRODUCT_FACE_READING_PRO) or {}
    phash = params_hash(cache_params)
    access = check_access(user_id, cache_params)
    if access.get("entitled"):
        return {
            "already_entitled": True,
            "cache_hit": access.get("cache_hit"),
            "already_paid": access.get("already_paid"),
            "is_pro": access.get("is_pro"),
            "params_hash": phash,
        }, None

    CoupleReportPurchase = _get_purchase_model()
    from models import db

    pending = (
        CoupleReportPurchase.query.filter_by(
            user_id=int(user_id),
            product=PRODUCT_FACE_READING_PRO,
            params_hash=phash,
            status="created",
        )
        .order_by(CoupleReportPurchase.created_at.desc())
        .first()
    )
    if not pending:
        pending = CoupleReportPurchase(
            user_id=int(user_id),
            product=PRODUCT_FACE_READING_PRO,
            params_hash=phash,
            params_json=json.dumps(
                {"params": cache_params, "lang": lang},
                ensure_ascii=False,
                default=str,
            ),
            lang=lang,
            amount=spec.get("amount_inr", 299),
            status="created",
        )
        db.session.add(pending)
        db.session.commit()
    return {
        "purchase_id": pending.id,
        "amount": pending.amount,
        "label": spec.get("label"),
        "params_hash": phash,
    }, None


def mark_paid(purchase_id: int, order_id: str | None = None) -> bool:
    CoupleReportPurchase = _get_purchase_model()
    from models import db

    row = CoupleReportPurchase.query.get(purchase_id)
    if not row or row.product != PRODUCT_FACE_READING_PRO:
        return False
    if row.status != "paid":
        row.status = "paid"
        row.paid_at = datetime.utcnow()
        if order_id:
            row.order_id = order_id
        db.session.commit()
    log.info(
        "[face_reading] paid user=%s hash=%s",
        row.user_id,
        row.params_hash[:12],
    )
    return True


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    if tags.get("product") != PRODUCT_FACE_READING_PRO and tags.get("kind") != "face_reading_report":
        return False
    pid = tags.get("purchase_id")
    CoupleReportPurchase = _get_purchase_model()
    purchase = None
    if pid:
        try:
            purchase = CoupleReportPurchase.query.get(int(pid))
        except (TypeError, ValueError):
            purchase = None
    if not purchase and order_id:
        purchase = CoupleReportPurchase.query.filter_by(order_id=order_id).first()
    if not purchase or purchase.product != PRODUCT_FACE_READING_PRO:
        return False
    return mark_paid(purchase.id, order_id=order_id)
