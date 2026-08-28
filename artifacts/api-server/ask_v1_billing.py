"""
Cosmic Intelligence V1 — question packs (one-time Razorpay).

Locked catalog (≈40–45% margin after LLM + gateway):
  starter  ₹49  ·  8 Q ·  7 days
  popular  ₹99  · 15 Q · 14 days
  power    ₹299 · 45 Q · 30 days

Wallet lives on User (ask_v1_questions_left + ask_v1_questions_total + ask_v1_expires_at).
Purchases are logged in AskV1Purchase for idempotent grants.
UI shows questions_used = total - left.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

ASK_V1_PACK_CATALOG = {
    "starter": {
        "id": "starter",
        "price_inr": 49,
        "questions": 8,
        "days": 7,
        "label": "Starter",
        "feel": "Try Cosmic Intelligence",
        "badge": None,
    },
    "popular": {
        "id": "popular",
        "price_inr": 99,
        "questions": 15,
        "days": 14,
        "label": "Popular",
        "feel": "Most popular for daily clarity",
        "badge": "popular",
    },
    "power": {
        "id": "power",
        "price_inr": 299,
        "questions": 45,
        "days": 30,
        "label": "Power",
        "feel": "Best value for deep seekers",
        "badge": "best",
    },
}


def payment_bypass() -> bool:
    if (os.environ.get("ASK_V1_PAYMENT_BYPASS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return True
    try:
        import payment_gateway as pg

        if not pg.configured():
            return True
    except Exception:
        pass
    return False


def list_packs() -> list[dict]:
    return [
        {
            "id": p["id"],
            "price_inr": p["price_inr"],
            "questions": p["questions"],
            "days": p["days"],
            "label": p["label"],
            "feel": p["feel"],
            "badge": p["badge"],
        }
        for p in ASK_V1_PACK_CATALOG.values()
    ]


def get_pack(pack_id: str) -> dict | None:
    return ASK_V1_PACK_CATALOG.get((pack_id or "").strip().lower())


def _naive_utc(dt):
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _now() -> datetime:
    return datetime.utcnow()


def pack_active(user) -> bool:
    if not user:
        return False
    left = int(getattr(user, "ask_v1_questions_left", 0) or 0)
    if left <= 0:
        return False
    exp = _naive_utc(getattr(user, "ask_v1_expires_at", None))
    if not exp or exp <= _now():
        return False
    return True


def wallet_snapshot(user) -> dict:
    left = int(getattr(user, "ask_v1_questions_left", 0) or 0) if user else 0
    total = int(getattr(user, "ask_v1_questions_total", 0) or 0) if user else 0
    exp = _naive_utc(getattr(user, "ask_v1_expires_at", None)) if user else None
    active = bool(user and left > 0 and exp and exp > _now())
    if user and left > 0 and exp and exp <= _now():
        # Soft-expire: zero out stale balance so UI stays honest.
        try:
            from database import db
            from models import User

            db.session.execute(
                update(User)
                .where(User.id == user.id)
                .where(User.ask_v1_questions_left > 0)
                .values(ask_v1_questions_left=0, ask_v1_questions_total=0)
            )
            db.session.commit()
            db.session.refresh(user)
            left = 0
            total = 0
        except Exception:
            left = 0
            total = 0
        active = False
    if active and total < left:
        # Legacy rows (column added later): prefer catalog pack size when it
        # covers the remaining balance so "used" is roughly honest.
        pack = get_pack((getattr(user, "ask_v1_pack_id", None) or ""))
        catalog_q = int(pack["questions"]) if pack else 0
        total = catalog_q if catalog_q >= left else left
        try:
            user.ask_v1_questions_total = total
            from database import db

            db.session.commit()
        except Exception:
            pass
    used = max(0, total - left) if active else 0
    free_used = int(getattr(user, "ask_v1_free_questions_used", 0) or 0) if user else 0
    bonus = int(getattr(user, "ask_v1_bonus_questions", 0) or 0) if user else 0
    free_left = max(0, 3 - free_used) + max(0, bonus)
    return {
        "active": active,
        "questions_left": left if active else 0,
        "questions_total": total if active else 0,
        "questions_used": used,
        "free_questions_left": free_left,
        "free_questions_used": free_used,
        "bonus_questions_left": max(0, bonus),
        "expires_at": exp.isoformat() + "Z" if active and exp else None,
        "pack_id": (getattr(user, "ask_v1_pack_id", None) or "") if active else "",
        "packs": list_packs(),
        "payment_bypass": payment_bypass(),
    }


def apply_pack_to_user(user, pack: dict) -> None:
    """Stack questions; extend expiry to at least now+days (or keep later expiry)."""
    now = _now()
    add_q = int(pack["questions"])
    days = int(pack["days"])
    left = int(getattr(user, "ask_v1_questions_left", 0) or 0)
    prev_total = int(getattr(user, "ask_v1_questions_total", 0) or 0)
    exp = _naive_utc(getattr(user, "ask_v1_expires_at", None))
    fresh_end = now + timedelta(days=days)

    if exp and exp > now and left > 0:
        user.ask_v1_questions_left = left + add_q
        user.ask_v1_expires_at = max(exp, fresh_end)
        base_total = prev_total if prev_total >= left else left
        user.ask_v1_questions_total = base_total + add_q
    else:
        user.ask_v1_questions_left = add_q
        user.ask_v1_expires_at = fresh_end
        user.ask_v1_questions_total = add_q
    user.ask_v1_pack_id = pack["id"]


def grant_purchase_idempotent(purchase) -> dict:
    """Mark purchase granted and credit wallet. Race-safe via atomic claim."""
    from database import db
    from models import AskV1Purchase, User

    if not purchase:
        return {"granted": False, "reason": "missing_purchase"}

    pack = get_pack(purchase.pack_id)
    if not pack:
        return {"granted": False, "reason": "unknown_pack"}

    claim = db.session.execute(
        update(AskV1Purchase)
        .where(AskV1Purchase.id == purchase.id)
        .where(AskV1Purchase.status == "paid")
        .where(AskV1Purchase.granted.is_(False))
        .values(granted=True)
    )
    if claim.rowcount != 1:
        db.session.commit()
        return {"granted": False, "reason": "already_granted_or_not_paid"}
    db.session.commit()

    try:
        user = db.session.get(User, purchase.user_id)
        if not user:
            return {"granted": True, "note": "user_missing"}
        apply_pack_to_user(user, pack)
        db.session.commit()
        try:
            import pack_referral as _pref

            _pref.grant_referrer_on_pack_purchase(
                buyer_user_id=int(purchase.user_id),
                source_kind="ask_v1",
                source_key=str(purchase.id),
            )
        except Exception:
            pass
    except Exception as exc:
        db.session.rollback()
        return {"granted": True, "note": f"wallet_side_effect_failed:{exc}"}

    return {
        "granted": True,
        "pack_id": pack["id"],
        "questions": pack["questions"],
        "days": pack["days"],
    }


def mark_purchase_paid_and_grant(purchase_id: int | None = None, order_id: str | None = None) -> dict:
    from database import db
    from models import AskV1Purchase

    purchase = None
    if purchase_id:
        purchase = AskV1Purchase.query.get(int(purchase_id))
    elif order_id:
        purchase = AskV1Purchase.query.filter_by(order_id=order_id).first()
    if not purchase:
        return {"granted": False, "reason": "not_found"}

    if purchase.status != "paid":
        purchase.status = "paid"
        purchase.paid_at = _now()
        db.session.commit()

    return grant_purchase_idempotent(purchase)


def grant_from_webhook(order_id: str, tags: dict) -> bool:
    pid = tags.get("purchase_id")
    try:
        result = mark_purchase_paid_and_grant(
            purchase_id=int(pid) if pid else None,
            order_id=order_id,
        )
        return bool(result.get("granted") or result.get("reason") == "already_granted_or_not_paid")
    except Exception:
        return False


def try_consume_pack(user) -> dict | None:
    """
    Atomic pack consume. Returns quota dict if consumed from pack,
    None if pack not available (caller should fall back to daily).
    """
    if not user or not pack_active(user):
        return None

    from database import db
    from models import User

    now = _now()
    result = db.session.execute(
        update(User)
        .where(User.id == user.id)
        .where(User.ask_v1_questions_left > 0)
        .where(User.ask_v1_expires_at.isnot(None))
        .where(User.ask_v1_expires_at > now)
        .values(
            ask_v1_questions_left=User.ask_v1_questions_left - 1,
            ask_v1_last_consume_source="pack",
        )
    )
    db.session.commit()
    if result.rowcount != 1:
        db.session.refresh(user)
        return None

    db.session.refresh(user)
    left = int(getattr(user, "ask_v1_questions_left", 0) or 0)
    total = int(getattr(user, "ask_v1_questions_total", 0) or 0)
    if total < left + 1:
        total = left + 1
        try:
            user.ask_v1_questions_total = total
            db.session.commit()
        except Exception:
            pass
    used = max(0, total - left)
    exp = _naive_utc(getattr(user, "ask_v1_expires_at", None))
    return {
        "allowed": True,
        "used": used,
        "limit": total,
        "questions_left": left,
        "questions_total": total,
        "questions_used": used,
        "expires_at": exp.isoformat() + "Z" if exp else None,
        "via": "ask_v1_pack",
        "plan": "ask_v1_pack",
    }


def try_refund_pack(user) -> bool:
    if not user:
        return False
    if (getattr(user, "ask_v1_last_consume_source", None) or "") != "pack":
        return False
    exp = _naive_utc(getattr(user, "ask_v1_expires_at", None))
    if not exp or exp <= _now():
        return False

    from database import db
    from models import User

    db.session.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            ask_v1_questions_left=User.ask_v1_questions_left + 1,
            ask_v1_last_consume_source="refunded",
        )
    )
    db.session.commit()
    db.session.refresh(user)
    return True
