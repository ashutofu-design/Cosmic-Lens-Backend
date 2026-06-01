"""User-facing purchase / transaction history (paid orders only)."""
from __future__ import annotations

from typing import Any

PRODUCT_LABELS: dict[str, str] = {
    "milan_pro": "Kundli Milan Pro PDF",
    "love_reality_pro": "Love Compatibility PDF",
    "face_reading_pro": "Face Reading PRO",
    "life_mastery": "Life Mastery (Numerology) PDF",
    "numerology_pro": "Numerology Pro PDF",
    "numerology_basic": "Numerology Basic PDF",
    "face_reading": "Face Reading Report",
    "vastu_pro": "AstroVastu PRO Scan",
    "business_vastu": "Business Vastu",
}


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def build_user_purchase_history(user_id: int) -> list[dict[str, Any]]:
    from models import (
        AstroVastuPropertyUnlock,
        AstroVastuPurchase,
        CoupleReportPurchase,
        User,
    )
    from subscription_helper import PLAN_PRICES, SKU_CATALOG

    user = User.query.get(user_id)
    if not user:
        return []

    rows: list[dict[str, Any]] = []

    for p in (
        CoupleReportPurchase.query.filter_by(user_id=user_id, status="paid")
        .order_by(CoupleReportPurchase.paid_at.desc(), CoupleReportPurchase.id.desc())
        .all()
    ):
        rows.append(
            {
                "id": f"cr-{p.id}",
                "kind": "report",
                "title": PRODUCT_LABELS.get(p.product, p.product.replace("_", " ").title()),
                "subtitle": p.lang.upper() if p.lang else "",
                "amount_inr": int(p.amount or 0),
                "order_id": p.order_id or "",
                "status": "paid",
                "paid_at": _iso(p.paid_at) or _iso(p.created_at),
            }
        )

    for p in (
        AstroVastuPurchase.query.filter_by(user_id=user_id, status="paid")
        .order_by(AstroVastuPurchase.paid_at.desc(), AstroVastuPurchase.id.desc())
        .all()
    ):
        spec = SKU_CATALOG.get(p.sku, {})
        title = spec.get("label", p.sku)
        rows.append(
            {
                "id": f"av-{p.id}",
                "kind": "astrovastu",
                "title": title,
                "subtitle": (p.property_name or "").strip(),
                "amount_inr": int(p.amount or spec.get("price") or 0),
                "order_id": p.order_id or "",
                "status": "paid",
                "paid_at": _iso(p.paid_at) or _iso(p.created_at),
            }
        )

    av_order_ids = {p.order_id for p in AstroVastuPurchase.query.filter_by(user_id=user_id, status="paid").all() if p.order_id}

    for u in (
        AstroVastuPropertyUnlock.query.filter_by(user_id=user_id)
        .order_by(AstroVastuPropertyUnlock.unlocked_at.desc(), AstroVastuPropertyUnlock.id.desc())
        .all()
    ):
        if u.order_id and u.order_id in av_order_ids:
            continue
        spec = SKU_CATALOG.get(u.tier, {})
        rows.append(
            {
                "id": f"avpu-{u.id}",
                "kind": "property_unlock",
                "title": spec.get("label", u.tier.replace("_", " ").title()),
                "subtitle": u.property_name or "",
                "amount_inr": int(u.amount_paid or spec.get("price") or 0),
                "order_id": u.order_id or "",
                "status": "paid",
                "paid_at": _iso(u.unlocked_at),
            }
        )

    if user.plan_order_id and user.plan and user.plan != "free":
        plan_key = user.plan
        amount = 0
        if plan_key == "trial":
            amount = int(PLAN_PRICES.get("trial_weekly", 1))
        elif plan_key == "basic":
            amount = int(PLAN_PRICES.get("basic_monthly", 199))
        elif plan_key in ("pro", "elite"):
            amount = int(PLAN_PRICES.get("pro_monthly", 499))
        rows.append(
            {
                "id": f"sub-{user.plan_order_id}",
                "kind": "subscription",
                "title": f"{plan_key.title()} subscription",
                "subtitle": "",
                "amount_inr": amount,
                "order_id": user.plan_order_id,
                "status": "paid",
                "paid_at": _iso(user.plan_expiry) or _iso(user.trial_started_at) or _iso(user.created_at),
            }
        )

    if getattr(user, "career_unlocked", False):
        try:
            from career_billing import price_inr as career_price

            career_amt = int(career_price())
        except Exception:
            career_amt = 0
        rows.append(
            {
                "id": f"career-{user.career_unlock_order_id or user.id}",
                "kind": "career",
                "title": "Career Life Map",
                "subtitle": "",
                "amount_inr": career_amt,
                "order_id": user.career_unlock_order_id or "",
                "status": "paid",
                "paid_at": _iso(getattr(user, "career_unlocked_at", None)),
            }
        )

    rows.sort(key=lambda r: r.get("paid_at") or "", reverse=True)
    return rows


def _user_snapshot(user_cache: dict[int, dict[str, Any]], user_id: int) -> dict[str, Any]:
    if user_id not in user_cache:
        from models import User

        u = User.query.get(user_id)
        user_cache[user_id] = {
            "user_id": user_id,
            "user_name": (u.name or "") if u else "",
            "user_email": (u.email or u.phone or "") if u else "",
        }
    return user_cache[user_id]


def build_admin_transactions(*, page: int = 1, per_page: int = 50) -> dict[str, Any]:
    """All paid transactions across users — for admin panel."""
    from models import (
        AstroVastuPropertyUnlock,
        AstroVastuPurchase,
        CoupleReportPurchase,
        User,
    )
    from subscription_helper import PLAN_PRICES, SKU_CATALOG

    page = max(1, page)
    per_page = max(1, min(200, per_page))
    user_cache: dict[int, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    for p in CoupleReportPurchase.query.filter_by(status="paid").all():
        base = {
            "id": f"cr-{p.id}",
            "kind": "report",
            "title": PRODUCT_LABELS.get(p.product, p.product.replace("_", " ").title()),
            "subtitle": p.lang.upper() if p.lang else "",
            "amount_inr": int(p.amount or 0),
            "order_id": p.order_id or "",
            "status": "paid",
            "paid_at": _iso(p.paid_at) or _iso(p.created_at),
        }
        rows.append({**_user_snapshot(user_cache, p.user_id), **base})

    av_order_ids: set[str] = set()
    for p in AstroVastuPurchase.query.filter_by(status="paid").all():
        if p.order_id:
            av_order_ids.add(p.order_id)
        spec = SKU_CATALOG.get(p.sku, {})
        base = {
            "id": f"av-{p.id}",
            "kind": "astrovastu",
            "title": spec.get("label", p.sku),
            "subtitle": (p.property_name or "").strip(),
            "amount_inr": int(p.amount or spec.get("price") or 0),
            "order_id": p.order_id or "",
            "status": "paid",
            "paid_at": _iso(p.paid_at) or _iso(p.created_at),
        }
        rows.append({**_user_snapshot(user_cache, p.user_id), **base})

    for u in AstroVastuPropertyUnlock.query.all():
        if u.order_id and u.order_id in av_order_ids:
            continue
        spec = SKU_CATALOG.get(u.tier, {})
        base = {
            "id": f"avpu-{u.id}",
            "kind": "property_unlock",
            "title": spec.get("label", u.tier.replace("_", " ").title()),
            "subtitle": u.property_name or "",
            "amount_inr": int(u.amount_paid or spec.get("price") or 0),
            "order_id": u.order_id or "",
            "status": "paid",
            "paid_at": _iso(u.unlocked_at),
        }
        rows.append({**_user_snapshot(user_cache, u.user_id), **base})

    for user in User.query.filter(User.plan_order_id.isnot(None), User.plan != "free").all():
        plan_key = user.plan or "free"
        amount = 0
        if plan_key == "trial":
            amount = int(PLAN_PRICES.get("trial_weekly", 1))
        elif plan_key == "basic":
            amount = int(PLAN_PRICES.get("basic_monthly", 199))
        elif plan_key in ("pro", "elite"):
            amount = int(PLAN_PRICES.get("pro_monthly", 499))
        base = {
            "id": f"sub-{user.plan_order_id}",
            "kind": "subscription",
            "title": f"{plan_key.title()} subscription",
            "subtitle": "",
            "amount_inr": amount,
            "order_id": user.plan_order_id or "",
            "status": "paid",
            "paid_at": _iso(user.trial_started_at) or _iso(user.created_at),
        }
        rows.append({**_user_snapshot(user_cache, user.id), **base})

    for user in User.query.filter_by(career_unlocked=True).all():
        try:
            from career_billing import price_inr as career_price

            career_amt = int(career_price())
        except Exception:
            career_amt = 0
        base = {
            "id": f"career-{user.career_unlock_order_id or user.id}",
            "kind": "career",
            "title": "Career Life Map",
            "subtitle": "",
            "amount_inr": career_amt,
            "order_id": user.career_unlock_order_id or "",
            "status": "paid",
            "paid_at": _iso(getattr(user, "career_unlocked_at", None)),
        }
        rows.append({**_user_snapshot(user_cache, user.id), **base})

    rows.sort(key=lambda r: r.get("paid_at") or "", reverse=True)
    total = len(rows)
    start = (page - 1) * per_page
    end = start + per_page
    pages = max(1, (total + per_page - 1) // per_page)

    return {
        "transactions": rows[start:end],
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
    }
