"""Career Life Map unlock — one-time ₹1 access per user."""
from __future__ import annotations

import logging
import os
from datetime import datetime

log = logging.getLogger(__name__)


def price_inr() -> int:
    return int(os.environ.get("CAREER_UNLOCK_PRICE_INR", "1"))


def payment_bypass() -> bool:
    from billing_security import payment_bypass_from_env

    return payment_bypass_from_env("CAREER_PAYMENT_BYPASS")


def payment_required() -> bool:
    """Paywall on in production unless explicitly disabled."""
    if payment_bypass():
        return False
    from billing_security import is_production

    flag = (os.environ.get("CAREER_PAYMENT_REQUIRED") or "").strip().lower()
    if not flag:
        return is_production()
    return flag in ("1", "true", "yes", "on")


def check_access(user_id: int) -> dict:
    from models import User

    user = User.query.get(int(user_id))
    if not user:
        return {
            "entitled": not payment_required(),
            "payment_required": payment_required(),
            "amount_inr": price_inr(),
            "label": "Career Analysis Unlock",
            "career_unlocked": False,
            "payment_bypass": payment_bypass(),
        }

    unlocked = bool(getattr(user, "career_unlocked", False))
    bypass = payment_bypass()
    paywall = payment_required() and not unlocked
    if bypass or not payment_required():
        return {
            "entitled": True,
            "payment_required": False,
            "amount_inr": price_inr(),
            "label": "Career Analysis Unlock",
            "career_unlocked": unlocked,
            "payment_bypass": bypass,
        }
    return {
        "entitled": unlocked,
        "payment_required": paywall,
        "amount_inr": price_inr(),
        "label": "Career Analysis Unlock",
        "career_unlocked": unlocked,
        "payment_bypass": False,
    }


def mark_unlocked(user_id: int, order_id: str | None = None) -> bool:
    from models import User, db

    user = User.query.get(int(user_id))
    if not user:
        return False
    if getattr(user, "career_unlocked", False):
        return True
    user.career_unlocked = True
    if order_id:
        user.career_unlock_order_id = order_id
    user.career_unlocked_at = datetime.utcnow()
    db.session.commit()
    return True


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    uid = tags.get("user_id")
    if not uid:
        if order_id and order_id.startswith("CA"):
            try:
                uid = order_id.split("_")[0][2:]
            except (IndexError, ValueError):
                return False
        else:
            return False
    try:
        import payment_gateway as pg

        if not pg.is_receipt_paid(order_id, min_amount_inr=price_inr()):
            log.warning("[career] webhook grant blocked order=%s", order_id)
            return False
        return mark_unlocked(int(uid), order_id=order_id)
    except (TypeError, ValueError):
        return False
