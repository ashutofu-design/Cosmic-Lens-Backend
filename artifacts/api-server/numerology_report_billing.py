"""Life Mastery numerology report — pay-per-report (₹249 default)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

PRODUCT_LIFE_MASTERY = "life_mastery"
VALID_PRODUCTS = {PRODUCT_LIFE_MASTERY}

CATALOG: dict[str, dict[str, Any]] = {
    PRODUCT_LIFE_MASTERY: {
        "label": "Life Mastery Report",
        "amount_inr": int(os.environ.get("LIFE_MASTERY_PRICE_INR", "249")),
    },
}


def payment_bypass() -> bool:
    return (os.environ.get("NUMEROLOGY_REPORT_PAYMENT_BYPASS") or "").strip().lower() in (
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
    return (os.environ.get("NUMEROLOGY_REPORT_PAYMENT_REQUIRED") or "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def numerology_cache_params(
    lang: str,
    name: str,
    dob: str,
    mobile: str | None = None,
    vehicle: str | None = None,
    house: str | None = None,
    tob: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tz: float | None = None,
    place: str | None = None,
) -> dict[str, Any]:
    """Must match pdf_pro cache_params keys."""
    return {
        "name": name,
        "dob": dob,
        "tob": tob,
        "lang": lang,
        "mobile": mobile,
        "vehicle": vehicle,
        "house": house,
        "lat": lat,
        "lon": lon,
        "tz": tz,
        "place": place,
    }


def params_hash(cache_params: dict[str, Any]) -> str:
    return rc._hash_params(cache_params)


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
            product=PRODUCT_LIFE_MASTERY,
            params_hash=phash,
            status="paid",
        )
        .order_by(CoupleReportPurchase.paid_at.desc())
        .first()
    )


def check_access(user_id: int, cache_params: dict[str, Any]) -> dict[str, Any]:
    spec = catalog_for(PRODUCT_LIFE_MASTERY) or {}
    phash = params_hash(cache_params)
    out: dict[str, Any] = {
        "product": PRODUCT_LIFE_MASTERY,
        "params_hash": phash,
        "label": spec.get("label", PRODUCT_LIFE_MASTERY),
        "amount_inr": spec.get("amount_inr", 249),
        "entitled": False,
        "cached_pdf": None,
        "payment_required": False,
        "already_paid": False,
        "cache_hit": False,
    }

    if not payment_required():
        out["entitled"] = True
        out["cached_pdf"] = rc.find(user_id, "numerology_pro", cache_params)
        out["cache_hit"] = bool(out["cached_pdf"])
        return out

    cached = rc.find(user_id, "numerology_pro", cache_params)
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
    spec = catalog_for(PRODUCT_LIFE_MASTERY) or {}
    phash = params_hash(cache_params)
    access = check_access(user_id, cache_params)
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
            product=PRODUCT_LIFE_MASTERY,
            params_hash=phash,
            status="created",
        )
        .order_by(CoupleReportPurchase.created_at.desc())
        .first()
    )
    if not pending:
        pending = CoupleReportPurchase(
            user_id=int(user_id),
            product=PRODUCT_LIFE_MASTERY,
            params_hash=phash,
            params_json=json.dumps({"params": cache_params, "lang": lang}, ensure_ascii=False, default=str),
            lang=lang,
            amount=spec.get("amount_inr", 249),
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
    if not row or row.product != PRODUCT_LIFE_MASTERY:
        return False
    if row.status != "paid":
        row.status = "paid"
        row.paid_at = datetime.utcnow()
        if order_id:
            row.order_id = order_id
        db.session.commit()
    log.info(
        "[numerology_report] paid user=%s hash=%s",
        row.user_id,
        row.params_hash[:12],
    )
    return True


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    if tags.get("product") != PRODUCT_LIFE_MASTERY and tags.get("kind") != "numerology_report":
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
    if not purchase or purchase.product != PRODUCT_LIFE_MASTERY:
        return False
    return mark_paid(purchase.id, order_id=order_id)
