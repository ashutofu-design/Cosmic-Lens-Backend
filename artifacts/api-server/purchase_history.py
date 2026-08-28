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
        GemstoneOrder,
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

    for p in (
        GemstoneOrder.query.filter_by(user_id=user_id, status="paid")
        .order_by(GemstoneOrder.paid_at.desc(), GemstoneOrder.id.desc())
        .all()
    ):
        rows.append(
            {
                "id": f"gem-{p.id}",
                "kind": "gemstone",
                "title": (p.sku or "Gemstone").replace("_", " ").title(),
                "subtitle": f"Delivery: {p.delivery_status or 'pending'}",
                "amount_inr": int(p.amount_inr or 0),
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

    # ── Cosmic Intelligence V1 question packs ───────────────────────────────
    try:
        from ask_v1_billing import ASK_V1_PACK_CATALOG
        from models import AskV1Purchase

        for p in (
            AskV1Purchase.query.filter_by(user_id=user_id, status="paid")
            .order_by(AskV1Purchase.paid_at.desc(), AskV1Purchase.id.desc())
            .all()
        ):
            pack = ASK_V1_PACK_CATALOG.get((p.pack_id or "").strip().lower()) or {}
            q = int(pack.get("questions") or 0)
            days = int(pack.get("days") or 0)
            label = str(pack.get("label") or p.pack_id or "V1 Pack").title()
            rows.append(
                {
                    "id": f"av1-{p.id}",
                    "kind": "ask_v1",
                    "title": f"Cosmic Intelligence V1 · {label}",
                    "subtitle": f"{q} questions · {days} days" if q else "",
                    "amount_inr": int(p.amount or pack.get("price_inr") or 0),
                    "order_id": p.order_id or "",
                    "status": "paid",
                    "paid_at": _iso(p.paid_at) or _iso(p.created_at),
                }
            )
    except Exception:
        pass

    # ── Cosmic Intelligence V3 live sessions ────────────────────────────────
    try:
        from cosmic_intelligence_v3_sessions import list_v3_transactions_for_user

        rows.extend(list_v3_transactions_for_user(user_id))
    except Exception:
        pass

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


def build_admin_transactions(
    *,
    page: int = 1,
    per_page: int = 50,
    email: str = "",
    user_id: int | None = None,
    status: str = "paid",
) -> dict[str, Any]:
    """All transactions across users — for admin panel (paid / failed / all).

    Includes reports, AstroVastu, gemstones, subscriptions, career unlock,
    Cosmic Intelligence V1 packs, and V3 live sessions.
    """
    from models import (
        AskV1Purchase,
        AstroVastuPropertyUnlock,
        AstroVastuPurchase,
        CoupleReportPurchase,
        GemstoneOrder,
        User,
    )
    from subscription_helper import PLAN_PRICES, SKU_CATALOG

    page = max(1, page)
    per_page = max(1, min(200, per_page))
    status_norm = (status or "paid").strip().lower()
    email_q = (email or "").strip().lower()
    user_cache: dict[int, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    # Fast path: recent-window merge (avoids loading every purchase into RAM).
    use_fast_path = not email_q and user_id is None
    fetch_cap = min(500, max(per_page * page * 3, 120)) if use_fast_path else None

    def _limited(q, date_col):
        ordered = q.order_by(date_col.desc())
        if fetch_cap is not None:
            return ordered.limit(fetch_cap).all()
        return ordered.all()

    def _matches_user(uid: int) -> bool:
        if user_id is not None and uid != user_id:
            return False
        if email_q:
            snap = _user_snapshot(user_cache, uid)
            em = (snap.get("user_email") or "").lower()
            if email_q not in em:
                return False
        return True

    couple_statuses = ["paid"]
    av_statuses = ["paid"]
    pack_statuses = ["paid"]
    gem_statuses = ["paid"]
    if status_norm == "failed":
        couple_statuses = ["created", "failed", "expired"]
        av_statuses = ["created", "failed", "expired"]
        pack_statuses = ["created", "failed"]
        gem_statuses = ["created", "failed"]
    elif status_norm == "all":
        couple_statuses = []  # no filter
        av_statuses = []
        pack_statuses = []
        gem_statuses = []

    cq = CoupleReportPurchase.query
    if couple_statuses:
        cq = cq.filter(CoupleReportPurchase.status.in_(couple_statuses))
    if user_id is not None:
        cq = cq.filter(CoupleReportPurchase.user_id == user_id)

    for p in _limited(cq, CoupleReportPurchase.paid_at):
        if not _matches_user(p.user_id):
            continue
        base = {
            "id": f"cr-{p.id}",
            "kind": "report",
            "title": PRODUCT_LABELS.get(p.product, p.product.replace("_", " ").title()),
            "subtitle": p.lang.upper() if p.lang else "",
            "amount_inr": int(p.amount or 0),
            "order_id": p.order_id or "",
            "status": p.status or "paid",
            "paid_at": _iso(p.paid_at) or _iso(p.created_at),
        }
        rows.append({**_user_snapshot(user_cache, p.user_id), **base})

    av_order_ids: set[str] = set()
    aq = AstroVastuPurchase.query
    if av_statuses:
        aq = aq.filter(AstroVastuPurchase.status.in_(av_statuses))
    if user_id is not None:
        aq = aq.filter(AstroVastuPurchase.user_id == user_id)

    for p in _limited(aq, AstroVastuPurchase.paid_at):
        if not _matches_user(p.user_id):
            continue
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
            "status": p.status or "paid",
            "paid_at": _iso(p.paid_at) or _iso(p.created_at),
        }
        rows.append({**_user_snapshot(user_cache, p.user_id), **base})

    # ── Gemstone orders ─────────────────────────────────────────────────────
    gq = GemstoneOrder.query
    if gem_statuses:
        gq = gq.filter(GemstoneOrder.status.in_(gem_statuses))
    if user_id is not None:
        gq = gq.filter(GemstoneOrder.user_id == user_id)

    for p in _limited(gq, GemstoneOrder.paid_at):
        if not _matches_user(p.user_id):
            continue
        base = {
            "id": f"gem-{p.id}",
            "kind": "gemstone",
            "title": (p.sku or "Gemstone").replace("_", " ").title(),
            "subtitle": f"Delivery: {p.delivery_status or 'pending'}",
            "amount_inr": int(p.amount_inr or 0),
            "order_id": p.order_id or "",
            "status": p.status or "paid",
            "paid_at": _iso(p.paid_at) or _iso(p.created_at),
        }
        rows.append({**_user_snapshot(user_cache, p.user_id), **base})

    # ── Cosmic Intelligence V1 question packs ───────────────────────────────
    try:
        from ask_v1_billing import ASK_V1_PACK_CATALOG

        v1q = AskV1Purchase.query
        if pack_statuses:
            v1q = v1q.filter(AskV1Purchase.status.in_(pack_statuses))
        if user_id is not None:
            v1q = v1q.filter(AskV1Purchase.user_id == user_id)

        for p in _limited(v1q, AskV1Purchase.paid_at):
            if not _matches_user(p.user_id):
                continue
            pack = ASK_V1_PACK_CATALOG.get((p.pack_id or "").strip().lower()) or {}
            q = int(pack.get("questions") or 0)
            days = int(pack.get("days") or 0)
            label = str(pack.get("label") or p.pack_id or "V1 Pack").title()
            base = {
                "id": f"av1-{p.id}",
                "kind": "ask_v1",
                "title": f"Cosmic Intelligence V1 · {label}",
                "subtitle": f"{q} questions · {days} days" if q else "",
                "amount_inr": int(p.amount or pack.get("price_inr") or 0),
                "order_id": p.order_id or "",
                "status": p.status or "paid",
                "paid_at": _iso(p.paid_at) or _iso(p.created_at),
            }
            rows.append({**_user_snapshot(user_cache, p.user_id), **base})
    except Exception:
        pass

    # ── Cosmic Intelligence V3 live sessions ────────────────────────────────
    try:
        from cosmic_intelligence_v3_sessions import list_v3_transactions_admin

        for base in list_v3_transactions_admin(user_id=user_id, status_mode=status_norm):
            uid = int(base.pop("user_id", 0) or 0)
            if uid <= 0 or not _matches_user(uid):
                continue
            rows.append({**_user_snapshot(user_cache, uid), **base})
    except Exception:
        pass

    if status_norm in ("paid", "all"):
        for u in AstroVastuPropertyUnlock.query.all():
            if user_id is not None and u.user_id != user_id:
                continue
            if not _matches_user(u.user_id):
                continue
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
            if user_id is not None and user.id != user_id:
                continue
            if not _matches_user(user.id):
                continue
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
            if user_id is not None and user.id != user_id:
                continue
            if not _matches_user(user.id):
                continue
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
    if use_fast_path:
        total = cq.count() + aq.count() + gq.count()
        if "v1q" in locals():
            total += v1q.count()
        if status_norm in ("paid", "all"):
            total += AstroVastuPropertyUnlock.query.count()
            total += User.query.filter(
                User.plan_order_id.isnot(None), User.plan != "free"
            ).count()
            total += User.query.filter_by(career_unlocked=True).count()
        total = max(total, len(rows))
    else:
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
