"""
Couple report pay-per-couple entitlement (Milan Pro + Love Reality Pro).

- Same birth pair + product + user → pay once, regenerate while cache TTL valid.
- Partner/birth change → new params_hash → new payment.
- Set COUPLE_REPORT_PAYMENT_BYPASS=1 to skip gates (dev / testing).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

PRODUCT_MILAN = "milan_pro"
PRODUCT_LOVE = "love_reality_pro"
VALID_PRODUCTS = {PRODUCT_MILAN, PRODUCT_LOVE}

CATALOG: dict[str, dict[str, Any]] = {
    PRODUCT_MILAN: {
        "label": "Kundli Milan Pro",
        "amount_inr": int(os.environ.get("MILAN_PRO_PRICE_INR", "299")),
    },
    PRODUCT_LOVE: {
        "label": "Love Reality Pro",
        "amount_inr": int(os.environ.get("LOVE_REALITY_PRO_PRICE_INR", "149")),
    },
}


def payment_bypass() -> bool:
    return (os.environ.get("COUPLE_REPORT_PAYMENT_BYPASS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def payment_required() -> bool:
    if payment_bypass():
        return False
    return (os.environ.get("COUPLE_REPORT_PAYMENT_REQUIRED") or "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def cache_params_from_birth(
    lang: str,
    p1: dict | None,
    p2: dict | None,
    kundli_p1: dict | None = None,
    kundli_p2: dict | None = None,
) -> dict[str, Any]:
    return rc.couple_cache_params(lang, p1, p2, kundli_p1, kundli_p2)


def params_hash(cache_params: dict[str, Any]) -> str:
    return rc._hash_params(cache_params)


def catalog_for(product: str) -> dict[str, Any] | None:
    return CATALOG.get(product)


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


def check_access(
    user_id: int,
    product: str,
    cache_params: dict[str, Any],
) -> dict[str, Any]:
    """
    Returns:
      entitled: bool — may generate PDF
      cached_pdf: bytes | None — serve without regenerate
      payment_required: bool
      already_paid: bool — paid row exists (cache may have expired)
      amount_inr, label, params_hash
    """
    spec = catalog_for(product) or {}
    phash = params_hash(cache_params)
    out: dict[str, Any] = {
        "product": product,
        "params_hash": phash,
        "label": spec.get("label", product),
        "amount_inr": spec.get("amount_inr", 0),
        "entitled": False,
        "cached_pdf": None,
        "payment_required": False,
        "already_paid": False,
        "cache_hit": False,
    }

    if not payment_required():
        out["entitled"] = True
        out["cached_pdf"] = rc.find(user_id, product, cache_params)
        out["cache_hit"] = bool(out["cached_pdf"])
        return out

    cached = rc.find(user_id, product, cache_params)
    if cached:
        out["entitled"] = True
        out["cached_pdf"] = cached
        out["cache_hit"] = True
        return out

    paid = find_paid_purchase(user_id, product, phash)
    if paid:
        out["entitled"] = True
        out["already_paid"] = True
        return out

    out["payment_required"] = True
    return out


def store_params_json(p1: dict, p2: dict, lang: str) -> str:
    return json.dumps({"p1": p1, "p2": p2, "lang": lang}, ensure_ascii=False, default=str)


def create_purchase_intent(
    user_id: int,
    product: str,
    p1: dict,
    p2: dict,
    lang: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Create or reuse pending purchase. Returns (payload, error_code)."""
    if product not in VALID_PRODUCTS:
        return None, "invalid_product"
    spec = catalog_for(product) or {}
    cp = cache_params_from_birth(lang, p1, p2)
    phash = params_hash(cp)
    access = check_access(user_id, product, cp)
    if access.get("entitled"):
        return {
            "already_entitled": True,
            "cache_hit": access.get("cache_hit"),
            "already_paid": access.get("already_paid"),
            "params_hash": phash,
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
            params_json=store_params_json(p1, p2, lang),
            lang=lang,
            amount=spec.get("amount_inr", 0),
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
    if not row:
        return False
    if row.status != "paid":
        row.status = "paid"
        row.paid_at = datetime.utcnow()
        if order_id:
            row.order_id = order_id
        db.session.commit()
    log.info(
        "[couple_report] paid user=%s product=%s hash=%s",
        row.user_id,
        row.product,
        row.params_hash[:12],
    )
    return True


def grant_from_webhook(order_id: str, tags: dict) -> bool:
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
    if not purchase and order_id and order_id.startswith("CR"):
        try:
            purchase = CoupleReportPurchase.query.get(int(order_id.split("_")[1]))
        except (IndexError, ValueError):
            pass
    if not purchase:
        return False
    return mark_paid(purchase.id, order_id=order_id)
