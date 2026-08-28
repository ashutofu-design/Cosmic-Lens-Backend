"""Palmistry Pro — Razorpay pay-per-order (PDF ₹1499 / VIP ₹2999 + ₹299 priority)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

PRODUCT_PALMISTRY_PDF = "palmistry_pdf"
PRODUCT_PALMISTRY_VIP = "palmistry_vip"
VALID_PRODUCTS = {PRODUCT_PALMISTRY_PDF, PRODUCT_PALMISTRY_VIP}

PRIORITY_FEE_INR = 299

CATALOG: dict[str, dict[str, Any]] = {
    PRODUCT_PALMISTRY_PDF: {
        "label": "Palmistry Pro Report",
        "plan": "pdf",
        "amount_inr": int(os.environ.get("PALMISTRY_PDF_PRICE_INR", "1499")),
    },
    PRODUCT_PALMISTRY_VIP: {
        "label": "Palmistry VIP Video Explanation",
        "plan": "vip",
        "amount_inr": int(os.environ.get("PALMISTRY_VIP_PRICE_INR", "2999")),
    },
}


def payment_bypass() -> bool:
    return (os.environ.get("PALMISTRY_PAYMENT_BYPASS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ) or (os.environ.get("COUPLE_REPORT_PAYMENT_BYPASS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def payment_required() -> bool:
    if payment_bypass():
        return False
    return (os.environ.get("PALMISTRY_PAYMENT_REQUIRED") or "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def product_for_plan(plan: str) -> str:
    p = (plan or "pdf").strip().lower()
    return PRODUCT_PALMISTRY_VIP if p == "vip" else PRODUCT_PALMISTRY_PDF


def cache_params(plan: str, urgent: bool, session_id: str = "") -> dict[str, Any]:
    return {
        "plan": "vip" if (plan or "").strip().lower() == "vip" else "pdf",
        "urgent": bool(urgent),
        "session_id": (session_id or "").strip() or None,
        "kind": "palmistry_report",
    }


def params_hash(cp: dict[str, Any]) -> str:
    return rc._hash_params(cp)


def catalog_for(product: str) -> dict[str, Any] | None:
    return CATALOG.get(product)


def charge_inr(plan: str, urgent: bool) -> int:
    product = product_for_plan(plan)
    spec = catalog_for(product) or {}
    base = int(spec.get("amount_inr") or (2999 if product == PRODUCT_PALMISTRY_VIP else 1499))
    return base + (PRIORITY_FEE_INR if urgent else 0)


def _get_purchase_model():
    from models import CoupleReportPurchase

    return CoupleReportPurchase


def find_paid_purchase(user_id: int, product: str, phash: str):
    if not user_id:
        return None
    CoupleReportPurchase = _get_purchase_model()
    return (
        CoupleReportPurchase.query.filter_by(
            user_id=int(user_id),
            product=product,
            params_hash=phash,
            status="paid",
        )
        .order_by(CoupleReportPurchase.paid_at.desc())
        .first()
    )


def check_access(user_id: int, plan: str, urgent: bool, session_id: str = "") -> dict[str, Any]:
    product = product_for_plan(plan)
    spec = catalog_for(product) or {}
    cp = cache_params(plan, urgent, session_id)
    phash = params_hash(cp)
    amount = charge_inr(plan, urgent)
    out: dict[str, Any] = {
        "product": product,
        "params_hash": phash,
        "label": spec.get("label", product),
        "amount_inr": amount,
        "plan": cp["plan"],
        "urgent": bool(urgent),
        "entitled": False,
        "payment_required": False,
        "already_paid": False,
        "purchase_id": None,
    }

    if not payment_required():
        out["entitled"] = True
        return out

    paid = find_paid_purchase(user_id, product, phash)
    if paid:
        out["entitled"] = True
        out["already_paid"] = True
        out["purchase_id"] = paid.id
        return out

    out["payment_required"] = True
    return out


def create_purchase_intent(
    user_id: int,
    plan: str,
    urgent: bool,
    session_id: str = "",
) -> tuple[dict[str, Any], str | None]:
    product = product_for_plan(plan)
    spec = catalog_for(product) or {}
    cp = cache_params(plan, urgent, session_id)
    phash = params_hash(cp)
    amount = charge_inr(plan, urgent)

    access = check_access(user_id, plan, urgent, session_id)
    if access.get("entitled"):
        return {
            "already_entitled": True,
            "already_paid": access.get("already_paid"),
            "purchase_id": access.get("purchase_id"),
            "params_hash": phash,
            "amount": amount,
            "label": spec.get("label"),
            "product": product,
        }, None

    CoupleReportPurchase = _get_purchase_model()
    from models import db

    pending = (
        CoupleReportPurchase.query.filter_by(
            user_id=int(user_id),
            product=product,
            params_hash=phash,
            status="created",
        )
        .order_by(CoupleReportPurchase.created_at.desc())
        .first()
    )
    if not pending:
        pending = CoupleReportPurchase(
            user_id=int(user_id),
            product=product,
            params_hash=phash,
            params_json=json.dumps(
                {
                    "params": cp,
                    "plan": cp["plan"],
                    "urgent": bool(urgent),
                    "session_id": session_id,
                },
                ensure_ascii=False,
                default=str,
            ),
            lang="en",
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
        "label": spec.get("label"),
        "params_hash": phash,
        "product": product,
        "plan": cp["plan"],
        "urgent": bool(urgent),
    }, None


def mark_paid(purchase_id: int, order_id: str | None = None) -> bool:
    CoupleReportPurchase = _get_purchase_model()
    from models import db

    row = CoupleReportPurchase.query.get(purchase_id)
    if not row or (row.product or "") not in VALID_PRODUCTS:
        return False
    if row.status != "paid":
        row.status = "paid"
        row.paid_at = datetime.utcnow()
        if order_id:
            row.order_id = order_id
        db.session.commit()
    log.info("[palmistry_report] paid user=%s product=%s", row.user_id, row.product)
    return True


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    kind = str(tags.get("kind") or "")
    product = str(tags.get("product") or "")
    if kind != "palmistry_report" and product not in VALID_PRODUCTS:
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
    if not purchase or (purchase.product or "") not in VALID_PRODUCTS:
        return False
    return mark_paid(purchase.id, order_id=order_id)


def assert_paid_purchase(user_id: int, purchase_id: int, plan: str) -> tuple[Any | None, str | None]:
    """Validate purchase for admin-upload. Returns (purchase, error_code)."""
    if payment_bypass() or not payment_required():
        return None, None
    if not purchase_id:
        return None, "payment_required"
    CoupleReportPurchase = _get_purchase_model()
    purchase = CoupleReportPurchase.query.get(int(purchase_id))
    expected = product_for_plan(plan)
    if not purchase or purchase.user_id != int(user_id):
        return None, "invalid_purchase"
    if (purchase.product or "") != expected:
        return None, "wrong_product"
    if purchase.status != "paid":
        return None, "payment_not_confirmed"
    return purchase, None
