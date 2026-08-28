"""Birth Time Rectification — pay-per-request (₹999 default)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

PRODUCT_BIRTH_TIME = "birth_time_rectification"
KIND = "birth_time_rectification"

CATALOG: dict[str, dict[str, Any]] = {
    PRODUCT_BIRTH_TIME: {
        "label": "Birth Time Rectification",
        "amount_inr": int(os.environ.get("BIRTH_TIME_RECTIFICATION_PRICE_INR", "999")),
    },
}


def payment_bypass() -> bool:
    return (os.environ.get("BIRTH_TIME_RECTIFICATION_PAYMENT_BYPASS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def payment_required() -> bool:
    if payment_bypass():
        return False
    return (os.environ.get("BIRTH_TIME_RECTIFICATION_PAYMENT_REQUIRED") or "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def cache_params(
    full_name: str,
    gender: str,
    dob: str,
    approx_tob: str,
    birth_place: str,
) -> dict[str, Any]:
    return {
        "full_name": (full_name or "").strip(),
        "gender": (gender or "").strip(),
        "dob": (dob or "").strip(),
        "approx_tob": (approx_tob or "").strip(),
        "birth_place": (birth_place or "").strip(),
    }


def params_hash(cp: dict[str, Any]) -> str:
    return rc._hash_params(cp)


def catalog_for(product: str) -> dict[str, Any] | None:
    return CATALOG.get(product)


def _get_purchase_model():
    from models import CoupleReportPurchase

    return CoupleReportPurchase


def find_paid_purchase(user_id: int, phash: str):
    if not user_id:
        return None
    CoupleReportPurchase = _get_purchase_model()
    return (
        CoupleReportPurchase.query.filter_by(
            user_id=int(user_id),
            product=PRODUCT_BIRTH_TIME,
            params_hash=phash,
            status="paid",
        )
        .order_by(CoupleReportPurchase.paid_at.desc())
        .first()
    )


def check_access(user_id: int, cp: dict[str, Any]) -> dict[str, Any]:
    spec = catalog_for(PRODUCT_BIRTH_TIME) or {}
    phash = params_hash(cp)
    out: dict[str, Any] = {
        "product": PRODUCT_BIRTH_TIME,
        "params_hash": phash,
        "label": spec.get("label", PRODUCT_BIRTH_TIME),
        "amount_inr": spec.get("amount_inr", 999),
        "entitled": False,
        "payment_required": False,
        "already_paid": False,
    }

    if not payment_required():
        out["entitled"] = True
        return out

    paid = find_paid_purchase(user_id, phash)
    if paid:
        out["entitled"] = True
        out["already_paid"] = True
        return out

    out["payment_required"] = True
    return out


def create_purchase_intent(user_id: int, cp: dict[str, Any], lang: str = "en"):
    spec = catalog_for(PRODUCT_BIRTH_TIME) or {}
    phash = params_hash(cp)
    access = check_access(user_id, cp)
    if access.get("entitled"):
        return {
            "already_entitled": True,
            "already_paid": access.get("already_paid"),
            "params_hash": phash,
        }, None

    CoupleReportPurchase = _get_purchase_model()
    from models import db

    pending = (
        CoupleReportPurchase.query.filter_by(
            user_id=int(user_id),
            product=PRODUCT_BIRTH_TIME,
            params_hash=phash,
            status="created",
        )
        .order_by(CoupleReportPurchase.created_at.desc())
        .first()
    )
    if not pending:
        pending = CoupleReportPurchase(
            user_id=int(user_id),
            product=PRODUCT_BIRTH_TIME,
            params_hash=phash,
            params_json=json.dumps({"params": cp, "lang": lang}, ensure_ascii=False, default=str),
            lang=lang,
            amount=spec.get("amount_inr", 999),
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
    if not row or row.product != PRODUCT_BIRTH_TIME:
        return False
    if row.status != "paid":
        row.status = "paid"
        row.paid_at = datetime.utcnow()
        if order_id:
            row.order_id = order_id
        db.session.commit()
    log.info(
        "[birth_time_rectification] paid user=%s hash=%s",
        row.user_id,
        (row.params_hash or "")[:12],
    )
    return True


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    if tags.get("product") != PRODUCT_BIRTH_TIME and tags.get("kind") != KIND:
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
        purchase = CoupleReportPurchase.query.filter_by(
            order_id=order_id, product=PRODUCT_BIRTH_TIME
        ).first()
    if not purchase:
        return False
    return mark_paid(purchase.id, order_id=order_id or purchase.order_id)


def require_paid_for_submit(
    user_id: int,
    cp: dict[str, Any],
    purchase_id: int | None,
) -> tuple[bool, dict[str, Any] | None]:
    """Returns (ok, error_payload). error_payload is for jsonify when not ok."""
    access = check_access(user_id, cp)
    if access.get("entitled"):
        return True, None
    if not payment_required():
        return True, None
    if purchase_id:
        CoupleReportPurchase = _get_purchase_model()
        row = CoupleReportPurchase.query.get(int(purchase_id))
        phash = params_hash(cp)
        if (
            row
            and row.user_id == int(user_id)
            and row.product == PRODUCT_BIRTH_TIME
            and row.status == "paid"
            and row.params_hash == phash
        ):
            return True, None
    spec = catalog_for(PRODUCT_BIRTH_TIME) or {}
    return False, {
        "error": "payment_required",
        "message": f"Pay ₹{spec.get('amount_inr', 999)} to submit Birth Time Rectification.",
        "product": PRODUCT_BIRTH_TIME,
        "amount_inr": access.get("amount_inr"),
        "params_hash": access.get("params_hash"),
    }
