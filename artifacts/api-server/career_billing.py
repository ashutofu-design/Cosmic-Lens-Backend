"""Career Life Map unlock — one-time ₹1 access per user."""
from __future__ import annotations

import os
from datetime import datetime


def price_inr() -> int:
    return int(os.environ.get("CAREER_UNLOCK_PRICE_INR", "1"))


def payment_bypass() -> bool:
    return (os.environ.get("CAREER_PAYMENT_BYPASS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def payment_required() -> bool:
    if payment_bypass():
        return False
    return (os.environ.get("CAREER_PAYMENT_REQUIRED") or "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def check_access(user_id: int) -> dict:
    from models import User

    user = User.query.get(int(user_id))
    if not user:
        return {
            "entitled": False,
            "payment_required": True,
            "amount_inr": price_inr(),
            "label": "Career Analysis Unlock",
            "career_unlocked": False,
            "payment_bypass": False,
        }

    # Only real ₹1 payment unlocks career — not "payment_required=off" alone.
    unlocked = bool(getattr(user, "career_unlocked", False))
    if payment_bypass():
        return {
            "entitled": True,
            "payment_required": False,
            "amount_inr": price_inr(),
            "label": "Career Analysis Unlock",
            "career_unlocked": unlocked,
            "payment_bypass": True,
        }
    return {
        "entitled": unlocked,
        "payment_required": payment_required() and not unlocked,
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
        return mark_unlocked(int(uid), order_id=order_id)
    except (TypeError, ValueError):
        return False
