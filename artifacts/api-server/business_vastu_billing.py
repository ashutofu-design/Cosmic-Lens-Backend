"""Business Vastu Pro — room photos (per room) or full PDF pricing."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

PRODUCT_BUSINESS_VASTU = "business_vastu"
KIND = "business_vastu"

VALID_TYPES = ("shop", "office", "factory")

# Legacy sticker prices (not used for Razorpay — kept for env overrides / admin)
BASE_PRICES: dict[str, int] = {
    "shop": int(os.environ.get("BUSINESS_VASTU_SHOP_INR", "999")),
    "office": int(os.environ.get("BUSINESS_VASTU_OFFICE_INR", "1499")),
    "factory": int(os.environ.get("BUSINESS_VASTU_FACTORY_INR", "2999")),
}

# Room photos — per photo (matches mobile BUSINESS_VASTU_ROOM_PHOTO_PRICES)
ROOM_PHOTO_PRICES: dict[str, int] = {
    "shop": int(os.environ.get("BUSINESS_VASTU_SHOP_ROOM_INR", "399")),
    "office": int(os.environ.get("BUSINESS_VASTU_OFFICE_ROOM_INR", "499")),
    "factory": int(os.environ.get("BUSINESS_VASTU_FACTORY_ROOM_INR", "999")),
}

# Full floor-plan PDF (matches mobile BUSINESS_VASTU_PDF_PRICES)
PDF_PRICES: dict[str, int] = {
    "shop": int(os.environ.get("BUSINESS_VASTU_SHOP_PDF_INR", "2999")),
    "office": int(os.environ.get("BUSINESS_VASTU_OFFICE_PDF_INR", "6999")),
    "factory": int(os.environ.get("BUSINESS_VASTU_FACTORY_PDF_INR", "14999")),
}

PRIORITY_FEE_INR = int(os.environ.get("BUSINESS_VASTU_PRIORITY_FEE_INR", "149"))

LABELS: dict[str, str] = {
    "shop": "Business Vastu — Shop",
    "office": "Business Vastu — Office",
    "factory": "Business Vastu — Factory",
}


def payment_bypass() -> bool:
    from billing_security import payment_bypass_from_env

    return payment_bypass_from_env("BUSINESS_VASTU_PAYMENT_BYPASS")


def payment_required() -> bool:
    from billing_security import payment_required_flag

    if payment_bypass():
        return False
    return payment_required_flag("BUSINESS_VASTU_PAYMENT_REQUIRED")


def normalize_upload_mode(raw: Any) -> str:
    m = str(raw or "photos").strip().lower()
    return "pdf" if m == "pdf" else "photos"


def amount_for(
    business_type: str,
    urgent: bool = False,
    upload_mode: str = "photos",
    room_count: int = 1,
) -> int:
    """Razorpay charge: PDF flat OR per-room × count (+ priority)."""
    btype = (business_type or "").strip().lower()
    mode = normalize_upload_mode(upload_mode)
    if mode == "pdf":
        base = int(PDF_PRICES.get(btype, PDF_PRICES["shop"]))
    else:
        per = int(ROOM_PHOTO_PRICES.get(btype, ROOM_PHOTO_PRICES["shop"]))
        try:
            n = int(room_count or 1)
        except (TypeError, ValueError):
            n = 1
        n = max(1, min(6, n))
        base = per * n
    return int(base) + (PRIORITY_FEE_INR if urgent else 0)


def label_for(
    business_type: str,
    urgent: bool = False,
    upload_mode: str = "photos",
    room_count: int = 1,
) -> str:
    btype = (business_type or "").strip().lower()
    label = LABELS.get(btype, "Business Vastu")
    mode = normalize_upload_mode(upload_mode)
    if mode == "pdf":
        label = f"{label} — Full PDF"
    else:
        try:
            n = max(1, min(6, int(room_count or 1)))
        except (TypeError, ValueError):
            n = 1
        label = f"{label} — {n} photo{'s' if n != 1 else ''}"
    if urgent:
        return f"{label} (Priority)"
    return label


def cache_params(
    business_type: str,
    property_name: str,
    urgent: bool = False,
    upload_mode: str = "photos",
    room_count: int = 1,
) -> dict[str, Any]:
    mode = normalize_upload_mode(upload_mode)
    try:
        n = max(1, min(6, int(room_count or 1)))
    except (TypeError, ValueError):
        n = 1
    return {
        "business_type": (business_type or "").strip().lower(),
        "property_name": (property_name or "").strip().lower(),
        "urgent": bool(urgent),
        "upload_mode": mode,
        "room_count": n if mode == "photos" else 0,
    }


def params_hash(cp: dict[str, Any]) -> str:
    return rc._hash_params(cp)


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
            product=PRODUCT_BUSINESS_VASTU,
            params_hash=phash,
            status="paid",
        )
        .order_by(CoupleReportPurchase.paid_at.desc())
        .first()
    )


def check_access(user_id: int, cp: dict[str, Any]) -> dict[str, Any]:
    btype = str(cp.get("business_type") or "shop")
    urgent = bool(cp.get("urgent"))
    mode = normalize_upload_mode(cp.get("upload_mode"))
    try:
        room_count = int(cp.get("room_count") or 1)
    except (TypeError, ValueError):
        room_count = 1
    phash = params_hash(cp)
    amount = amount_for(btype, urgent, mode, room_count)
    out: dict[str, Any] = {
        "product": PRODUCT_BUSINESS_VASTU,
        "params_hash": phash,
        "label": label_for(btype, urgent, mode, room_count),
        "amount_inr": amount,
        "business_type": btype,
        "urgent": urgent,
        "upload_mode": mode,
        "room_count": room_count if mode == "photos" else 0,
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
    btype = str(cp.get("business_type") or "shop")
    if btype not in VALID_TYPES:
        return None, "invalid_business_type"
    urgent = bool(cp.get("urgent"))
    mode = normalize_upload_mode(cp.get("upload_mode"))
    try:
        room_count = int(cp.get("room_count") or 1)
    except (TypeError, ValueError):
        room_count = 1
    phash = params_hash(cp)
    access = check_access(user_id, cp)
    if access.get("entitled"):
        return {
            "already_entitled": True,
            "already_paid": access.get("already_paid"),
            "params_hash": phash,
            "amount": access.get("amount_inr"),
            "label": access.get("label"),
        }, None

    CoupleReportPurchase = _get_purchase_model()
    from models import db

    amount = amount_for(btype, urgent, mode, room_count)
    pending = (
        CoupleReportPurchase.query.filter_by(
            user_id=int(user_id),
            product=PRODUCT_BUSINESS_VASTU,
            params_hash=phash,
            status="created",
        )
        .order_by(CoupleReportPurchase.created_at.desc())
        .first()
    )
    if not pending:
        pending = CoupleReportPurchase(
            user_id=int(user_id),
            product=PRODUCT_BUSINESS_VASTU,
            params_hash=phash,
            params_json=json.dumps({"params": cp, "lang": lang}, ensure_ascii=False, default=str),
            lang=lang,
            amount=amount,
            status="created",
        )
        db.session.add(pending)
        db.session.commit()
    elif int(pending.amount or 0) != amount:
        pending.amount = amount
        db.session.commit()

    return {
        "purchase_id": pending.id,
        "amount": pending.amount,
        "label": label_for(btype, urgent, mode, room_count),
        "params_hash": phash,
    }, None


def mark_paid(purchase_id: int, order_id: str | None = None) -> bool:
    CoupleReportPurchase = _get_purchase_model()
    from models import db

    row = CoupleReportPurchase.query.get(purchase_id)
    if not row or row.product != PRODUCT_BUSINESS_VASTU:
        return False
    if row.status != "paid":
        row.status = "paid"
        row.paid_at = datetime.utcnow()
        if order_id:
            row.order_id = order_id
        db.session.commit()
    log.info(
        "[business_vastu] paid user=%s hash=%s",
        row.user_id,
        (row.params_hash or "")[:12],
    )
    return True


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    if tags.get("product") != PRODUCT_BUSINESS_VASTU and tags.get("kind") != KIND:
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
            order_id=order_id, product=PRODUCT_BUSINESS_VASTU
        ).first()
    if not purchase:
        return False
    import payment_gateway as pg

    if not pg.is_receipt_paid(
        order_id or purchase.order_id or "",
        min_amount_inr=int(purchase.amount or 0) or None,
    ):
        log.warning("[business_vastu] webhook grant blocked order=%s", order_id)
        return False
    return mark_paid(purchase.id, order_id=order_id or purchase.order_id)


def require_paid_for_submit(
    user_id: int,
    cp: dict[str, Any],
    purchase_id: int | None,
) -> tuple[bool, dict[str, Any] | None]:
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
            and row.product == PRODUCT_BUSINESS_VASTU
            and row.status == "paid"
            and row.params_hash == phash
        ):
            return True, None
    return False, {
        "error": "payment_required",
        "message": f"Pay ₹{access.get('amount_inr', 999)} to submit Business Vastu.",
        "product": PRODUCT_BUSINESS_VASTU,
        "amount_inr": access.get("amount_inr"),
        "params_hash": access.get("params_hash"),
        "label": access.get("label"),
    }
