"""Gemstone shop — MRP, self/referral discounts, Razorpay orders."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)
_UTC = timezone.utc

REFERRAL_PAYOUT_AFTER_DAYS = 7

# Per-ratti pricing — keep in sync with mobile lib/gemstonePricing.ts
GEMSTONE_SKUS: dict[str, dict[str, Any]] = {
    "ceylon_pukhraj_5ratti": {
        "label": "Ceylon Pukhraj (Yellow Sapphire) — 5 Ratti",
        "catalog_id": "yellowsapphire",
        "ratti": 5,
        "mrp_inr": 47_999,
        "self_discount_inr": 2_000,
        "referral_buyer_discount_inr": 1_000,
        "referrer_reward_inr": 2_500,
        "in_stock": True,
    },
    "ceylon_pukhraj_6ratti": {
        "label": "Ceylon Pukhraj (Yellow Sapphire) — 6 Ratti",
        "catalog_id": "yellowsapphire",
        "ratti": 6,
        "mrp_inr": 58_000,
        "self_discount_inr": 2_500,
        "referral_buyer_discount_inr": 1_500,
        "referrer_reward_inr": 3_000,
        "in_stock": True,
    },
    "ceylon_pukhraj_7ratti": {
        "label": "Ceylon Pukhraj (Yellow Sapphire) — 7 Ratti",
        "catalog_id": "yellowsapphire",
        "ratti": 7,
        "mrp_inr": 86_000,
        "self_discount_inr": 3_000,
        "referral_buyer_discount_inr": 2_000,
        "referrer_reward_inr": 3_500,
        "in_stock": True,
    },
    "ceylon_pukhraj_8ratti": {
        "label": "Ceylon Pukhraj (Yellow Sapphire) — 8 Ratti",
        "catalog_id": "yellowsapphire",
        "ratti": 8,
        "mrp_inr": 98_000,
        "self_discount_inr": 3_500,
        "referral_buyer_discount_inr": 2_500,
        "referrer_reward_inr": 4_000,
        "in_stock": True,
    },
    "ceylon_pukhraj_9ratti": {
        "label": "Ceylon Pukhraj (Yellow Sapphire) — 9 Ratti",
        "catalog_id": "yellowsapphire",
        "ratti": 9,
        "mrp_inr": 110_000,
        "self_discount_inr": 4_000,
        "referral_buyer_discount_inr": 3_000,
        "referrer_reward_inr": 4_500,
        "in_stock": True,
    },
    "ceylon_pukhraj_10ratti": {
        "label": "Ceylon Pukhraj (Yellow Sapphire) — 10 Ratti",
        "catalog_id": "yellowsapphire",
        "ratti": 10,
        "mrp_inr": 123_000,
        "self_discount_inr": 4_500,
        "referral_buyer_discount_inr": 3_500,
        "referrer_reward_inr": 5_000,
        "in_stock": True,
    },
    "zambian_emerald_5ratti": {
        "label": "Zambian Emerald — 5 Ratti",
        "catalog_id": "emerald",
        "ratti": 5,
        "mrp_inr": 65_000,
        "self_discount_inr": 2_500,
        "referral_buyer_discount_inr": 1_500,
        "referrer_reward_inr": 3_000,
        "in_stock": True,
    },
}

_REF_CODE_RE = re.compile(r"^CL(\d+)$", re.I)


def _sku_pricing(spec: dict[str, Any]) -> dict[str, int]:
    mrp = int(spec.get("mrp_inr") or 0)
    self_d = int(spec.get("self_discount_inr") or 0)
    ref_d = int(spec.get("referral_buyer_discount_inr") or 0)
    ref_reward = int(spec.get("referrer_reward_inr") or 0)
    return {
        "mrp_inr": mrp,
        "self_discount_inr": self_d,
        "referral_buyer_discount_inr": ref_d,
        "referrer_reward_inr": ref_reward,
        "self_price_inr": max(1, mrp - self_d),
        "referral_price_inr": max(1, mrp - ref_d),
    }


def catalog() -> list[dict[str, Any]]:
    items = []
    for sku, spec in GEMSTONE_SKUS.items():
        prices = _sku_pricing(spec)
        items.append(
            {
                "sku": sku,
                **{k: v for k, v in spec.items() if k != "catalog_id"},
                "catalog_id": spec.get("catalog_id"),
                **prices,
            }
        )
    items.sort(key=lambda x: int(x.get("ratti") or 0))
    return items


def referral_code_for_user(user_id: int) -> str:
    return f"CL{user_id}"


def resolve_referrer_user_id(code: str | None) -> int | None:
    raw = (code or "").strip().upper()
    if not raw:
        return None
    m = _REF_CODE_RE.match(raw)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def quote(
    sku: str,
    buyer_user_id: int,
    referral_code: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    spec = GEMSTONE_SKUS.get(sku)
    if not spec:
        return None, "invalid_sku"
    if not spec.get("in_stock", True):
        return None, "out_of_stock"

    prices = _sku_pricing(spec)
    mrp = prices["mrp_inr"]
    referrer_id = resolve_referrer_user_id(referral_code)
    discount_type = "self"
    discount_inr = prices["self_discount_inr"]
    referrer_reward_inr = 0

    if referrer_id is not None:
        if referrer_id == buyer_user_id:
            return None, "self_referral_not_allowed"
        discount_type = "referral"
        discount_inr = prices["referral_buyer_discount_inr"]
        referrer_reward_inr = prices["referrer_reward_inr"]

    amount_inr = max(1, mrp - discount_inr)
    return {
        "sku": sku,
        "label": spec.get("label"),
        "ratti": spec.get("ratti"),
        "mrp_inr": mrp,
        "discount_inr": discount_inr,
        "discount_type": discount_type,
        "amount_inr": amount_inr,
        "referral_code_used": referral_code.strip().upper() if referrer_id else None,
        "referrer_user_id": referrer_id,
        "referrer_reward_inr": referrer_reward_inr,
        "referrer_payout_note": (
            f"₹{referrer_reward_inr:,} to referrer's bank after delivery + {REFERRAL_PAYOUT_AFTER_DAYS} days"
            if referrer_id
            else None
        ),
    }, None


def create_order_intent(
    buyer_user_id: int,
    sku: str,
    referral_code: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    q, err = quote(sku, buyer_user_id, referral_code)
    if err or not q:
        return None, err or "quote_failed"

    from models import GemstoneOrder, db

    row = GemstoneOrder(
        user_id=buyer_user_id,
        sku=sku,
        mrp_inr=q["mrp_inr"],
        discount_inr=q["discount_inr"],
        amount_inr=q["amount_inr"],
        discount_type=q["discount_type"],
        referral_code_used=q.get("referral_code_used"),
        referrer_user_id=q.get("referrer_user_id"),
        referrer_reward_inr=q.get("referrer_reward_inr") or 0,
        referrer_payout_status="pending" if q.get("referrer_user_id") else "none",
        status="created",
        delivery_status="pending",
    )
    db.session.add(row)
    db.session.commit()
    return {**q, "order_row_id": row.id}, None


def mark_paid(order_row_id: int, order_id: str) -> bool:
    from models import GemstoneOrder, db

    row = GemstoneOrder.query.get(order_row_id)
    if not row:
        return False
    if row.status == "paid":
        return True
    row.status = "paid"
    row.order_id = order_id
    row.paid_at = datetime.now(_UTC).replace(tzinfo=None)
    db.session.commit()
    return True


def grant_from_webhook(receipt: str, notes: dict[str, str]) -> bool:
    if notes.get("kind") != "gemstone":
        return False
    try:
        oid = int(notes.get("gemstone_order_id") or 0)
    except (TypeError, ValueError):
        oid = 0
    if not oid:
        return False
    from models import GemstoneOrder
    import payment_gateway as pg

    row = GemstoneOrder.query.get(oid)
    min_inr = int(row.amount_inr or 0) if row else None
    if not pg.is_receipt_paid(receipt, min_amount_inr=min_inr):
        return False
    return mark_paid(oid, receipt)


def order_status_payload(row) -> dict[str, Any]:
    return {
        "id": row.id,
        "sku": row.sku,
        "status": row.status,
        "delivery_status": row.delivery_status,
        "amount_inr": row.amount_inr,
        "mrp_inr": row.mrp_inr,
        "discount_inr": row.discount_inr,
        "discount_type": row.discount_type,
        "referral_code_used": row.referral_code_used,
        "referrer_reward_inr": row.referrer_reward_inr,
        "referrer_payout_status": row.referrer_payout_status,
        "paid": row.status == "paid",
        "granted": row.status == "paid",
    }
