"""Razorpay payment gateway helpers for Cosmic Lens."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sys
from typing import Any

log = logging.getLogger(__name__)


def _ensure_pkg_resources() -> None:
    """Razorpay imports pkg_resources; setuptools 81+ no longer exposes it."""
    try:
        import pkg_resources  # noqa: F401
    except ModuleNotFoundError:
        try:
            import pip._vendor.pkg_resources as _pr  # type: ignore
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "pkg_resources missing — run: pip install 'setuptools>=65,<81'"
            ) from exc
        sys.modules["pkg_resources"] = _pr

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")


def configured() -> bool:
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def not_configured_error() -> tuple[dict, int]:
    return {"error": "razorpay_not_configured"}, 503


def _client():
    if not configured():
        raise RuntimeError("razorpay_not_configured")
    _ensure_pkg_resources()
    import razorpay

    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def customer_from_user(user) -> dict[str, str]:
    email = (getattr(user, "email", None) or "").strip() or f"user{user.id}@cosmiclens.app"
    raw_phone = (getattr(user, "phone", None) or "").strip()
    digits = "".join(c for c in raw_phone if c.isdigit())
    phone = digits[-10:] if len(digits) >= 10 else "9999999999"
    name = (getattr(user, "name", None) or "").strip() or "User"
    return {
        "customer_name": name,
        "customer_email": email,
        "customer_phone": phone,
    }


def _string_notes(notes: dict[str, Any]) -> dict[str, str]:
    return {str(k): str(v) for k, v in notes.items() if v is not None}


def create_order(receipt: str, amount_inr: int, notes: dict[str, Any]) -> dict:
    client = _client()
    return client.order.create(
        {
            "amount": int(amount_inr) * 100,
            "currency": "INR",
            "receipt": receipt[:40],
            "notes": _string_notes(notes),
        }
    )


def checkout_response(
    order_id: str,
    razorpay_order: dict,
    amount_inr: int,
    user,
    **extra: Any,
) -> dict[str, Any]:
    rz_id = razorpay_order["id"]
    cust = customer_from_user(user)
    payload: dict[str, Any] = {
        "order_id": order_id,
        "razorpay_order_id": rz_id,
        "razorpay_key_id": RAZORPAY_KEY_ID,
        "amount": amount_inr,
        "amount_paise": int(amount_inr) * 100,
        "currency": "INR",
        # Mobile app still reads payment_session_id for checkout order id.
        "payment_session_id": rz_id,
        "payment_link": "",
        **cust,
        **extra,
    }
    return payload


def is_receipt_paid(receipt: str) -> bool:
    if not receipt or not configured():
        return False
    try:
        client = _client()
        orders = client.order.all({"receipt": receipt})
        items = orders.get("items") or []
        if not items:
            return False
        rz_order_id = items[0]["id"]
        payments = client.order.payments(rz_order_id)
        pay_items = payments.get("items") or []
        return any(p.get("status") == "captured" for p in pay_items)
    except Exception as exc:
        log.warning("[RZ] poll error for receipt %s: %s", receipt, exc)
        return False


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    if not RAZORPAY_WEBHOOK_SECRET:
        log.warning("[RZ] webhook secret not set — skipping verification")
        return True
    if not signature:
        return False
    try:
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def parse_webhook_event(payload: dict) -> tuple[str, str, dict[str, str]]:
    """Return (event_name, receipt/order_id, notes dict)."""
    event = payload.get("event", "")
    entity = (payload.get("payload") or {}).get("order", {}).get("entity") or {}
    if not entity:
        payment = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
        notes = payment.get("notes") or {}
        receipt = notes.get("receipt") or payment.get("description") or ""
        return event, receipt, {str(k): str(v) for k, v in notes.items()}

    receipt = entity.get("receipt") or ""
    notes = entity.get("notes") or {}
    return event, receipt, {str(k): str(v) for k, v in notes.items()}


def handle_paid_webhook(payload: dict) -> tuple[str, dict[str, str]] | None:
    event, receipt, notes = parse_webhook_event(payload)
    if event not in ("payment.captured", "order.paid"):
        return None
    if not receipt:
        return None
    return receipt, notes
