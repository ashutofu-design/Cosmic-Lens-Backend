"""
Local admin dashboard data aggregation for Cosmic Lens.

Used by /api/admin/* routes. Set ADMIN_NO_AUTH=1 explicitly for password-free local use.
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import report_cache as rc

_UTC = timezone.utc

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


def admin_no_auth() -> bool:
    return (os.environ.get("ADMIN_NO_AUTH") or "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _now_naive() -> datetime:
    return datetime.now(_UTC).replace(tzinfo=None)


def _since(days: float = 0, hours: float = 0) -> datetime:
    return _now_naive() - timedelta(days=days, hours=hours)


def _paid_at_naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(_UTC).replace(tzinfo=None)
    return dt


def _in_range(paid_at: datetime | None, start: datetime) -> bool:
    if paid_at is None:
        return False
    p = _paid_at_naive(paid_at)
    return p is not None and p >= start


def _parse_birth_data(raw: str | None) -> dict[str, Any]:
    """Extract DOB, time, place from profile.birth_data JSON for admin display."""
    if not raw:
        return {
            "dob": "",
            "tob": "",
            "place": "",
            "lat": None,
            "lon": None,
            "tz": None,
            "gender": "",
        }
    try:
        bd = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        bd = {}
    # Occasionally double-encoded JSON in older rows.
    if isinstance(bd, str):
        try:
            bd = json.loads(bd)
        except (json.JSONDecodeError, TypeError):
            bd = {}
    if not isinstance(bd, dict):
        bd = {}
    # Some clients nest under birthData.
    nested = bd.get("birthData")
    if isinstance(nested, dict):
        bd = {**nested, **{k: v for k, v in bd.items() if k != "birthData"}}

    dob = ""
    try:
        y, m, d = int(bd.get("year", 0)), int(bd.get("month", 0)), int(bd.get("day", 0))
        if y and m and d:
            dob = f"{d:02d}/{m:02d}/{y}"
    except (TypeError, ValueError):
        pass

    tob = ""
    try:
        h, mn = int(bd.get("hour", 0)), int(bd.get("minute", 0))
        ampm = str(bd.get("ampm", "")).upper().strip()
        if h or mn or ampm:
            tob = f"{h:02d}:{mn:02d}" + (f" {ampm}" if ampm else "")
    except (TypeError, ValueError):
        pass

    place = (bd.get("place") or bd.get("pob") or "").strip()
    gender = (bd.get("gender") or "").strip()

    lat = bd.get("lat")
    lon = bd.get("lon")
    try:
        lat = float(lat) if lat is not None else None
    except (TypeError, ValueError):
        lat = None
    try:
        lon = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        lon = None

    tz = bd.get("tz")
    try:
        tz = float(tz) if tz is not None else None
    except (TypeError, ValueError):
        tz = None

    return {
        "dob": dob,
        "tob": tob.strip(),
        "place": place,
        "lat": lat,
        "lon": lon,
        "tz": tz,
        "gender": gender,
    }


def _apply_legacy_birth_fallback(row: dict[str, Any], legacy: dict[str, Any] | None) -> dict[str, Any]:
    """Fill missing DOB/time/place from legacy kundlis row when profile JSON parse is empty."""
    if not legacy:
        return row
    out = dict(row)
    if not out.get("dob") and legacy.get("dob"):
        out["dob"] = legacy["dob"]
    if not out.get("tob") and legacy.get("tob"):
        out["tob"] = legacy["tob"]
    if not out.get("place") and legacy.get("place"):
        out["place"] = legacy["place"]
    if out.get("lat") is None and legacy.get("lat") is not None:
        out["lat"] = legacy["lat"]
    if out.get("lon") is None and legacy.get("lon") is not None:
        out["lon"] = legacy["lon"]
    if not out.get("has_chart") and legacy.get("has_chart"):
        out["has_chart"] = True
    return out


def _profile_admin_row(profile, legacy: dict[str, Any] | None = None) -> dict[str, Any]:
    birth = _parse_birth_data(getattr(profile, "birth_data", None))
    row = {
        "name": profile.name or "",
        "relation": profile.relation or "",
        "gender": profile.gender or birth.get("gender") or "",
        "is_primary": bool(profile.is_primary),
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        "dob": birth["dob"],
        "tob": birth["tob"],
        "place": birth["place"],
        "lat": birth["lat"],
        "lon": birth["lon"],
        "tz": birth["tz"],
        "has_chart": bool(getattr(profile, "chart_data", None)),
    }
    if row["is_primary"] or not legacy:
        return _apply_legacy_birth_fallback(row, legacy if row["is_primary"] else None)
    return row


def _sum_amount(rows: list, amount_attr: str = "amount", since: datetime | None = None) -> int:
    total = 0
    for r in rows:
        paid = getattr(r, "paid_at", None)
        if since is not None and not _in_range(paid, since):
            continue
        try:
            total += int(getattr(r, amount_attr, 0) or 0)
        except (TypeError, ValueError):
            pass
    return total


def build_dashboard(db_session) -> dict[str, Any]:
    from models import (
        AstroVastuPurchase,
        CoupleReportPurchase,
        Profile,
        User,
    )

    now = _now_naive()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_week = _since(days=7)
    start_month = _since(days=30)

    total_users = User.query.count()

    # ── Payments from DB tables ─────────────────────────────────────────────
    try:
        couple_paid = CoupleReportPurchase.query.filter_by(status="paid").all()
    except Exception:
        couple_paid = []
    try:
        av_paid = AstroVastuPurchase.query.filter_by(status="paid").all()
    except Exception:
        av_paid = []

    def payment_totals(since: datetime | None) -> int:
        t = _sum_amount(couple_paid, since=since) + _sum_amount(av_paid, since=since)
        # Career one-time unlocks (stored on user row, not purchase table)
        try:
            from career_billing import price_inr as career_price

            career_amt = career_price()
        except Exception:
            career_amt = 1
        career_q = User.query.filter_by(career_unlocked=True)
        if since is not None:
            career_q = career_q.filter(User.career_unlocked_at >= since)
        t += career_q.count() * career_amt
        return t

    payments = {
        "today_inr": payment_totals(start_today),
        "week_inr": payment_totals(start_week),
        "month_inr": payment_totals(start_month),
        "lifetime_inr": payment_totals(None),
    }

    # ── Per-product purchase counts (paid) ───────────────────────────────────
    product_counts: Counter[str] = Counter()
    for row in couple_paid:
        product_counts[row.product or "unknown"] += 1
    av_sku_counts: Counter[str] = Counter()
    for row in av_paid:
        av_sku_counts[row.sku or "unknown"] += 1

    purchases_by_product = [
        {
            "key": k,
            "label": PRODUCT_LABELS.get(k, k.replace("_", " ").title()),
            "count": v,
        }
        for k, v in sorted(product_counts.items(), key=lambda x: -x[1])
    ]
    astrovastu_purchases = [
        {
            "sku": k,
            "label": k.replace("_", " ").title(),
            "count": v,
        }
        for k, v in sorted(av_sku_counts.items(), key=lambda x: -x[1])
    ]

    # ── Reports generated (ledger) ───────────────────────────────────────────
    ledger = rc._load_ledger()
    report_by_kind: Counter[str] = Counter()
    for row in ledger:
        kind = (row.get("kind") or row.get("report_type") or "unknown").strip()
        report_by_kind[kind] += 1

    report_rows = [
        {
            "kind": k,
            "label": PRODUCT_LABELS.get(k, k.replace("_", " ").title()),
            "count": v,
        }
        for k, v in sorted(report_by_kind.items(), key=lambda x: -x[1])
    ]
    highest = report_rows[0] if report_rows else None
    lowest = report_rows[-1] if len(report_rows) > 1 else (report_rows[0] if report_rows else None)

    total_reports_sold = sum(report_by_kind.values())

    # ── Plan breakdown (subscription placeholder data) ───────────────────────
    plan_counts: dict[str, int] = defaultdict(int)
    for u in User.query.with_entities(User.plan).all():
        plan_counts[(u.plan or "free").lower()] += 1

    return {
        "generated_at": now.isoformat() + "Z",
        "total_users": total_users,
        "payments": payments,
        "purchases_by_product": purchases_by_product,
        "astrovastu_purchases": astrovastu_purchases,
        "reports": {
            "total_generated": total_reports_sold,
            "by_kind": report_rows,
            "highest": highest,
            "lowest": lowest,
        },
        "subscriptions": {
            "enabled": False,
            "message": "Subscription billing coming soon — counts below are current plan labels on user accounts.",
            "plan_counts": dict(plan_counts),
        },
    }


def build_users_list(
    db_session,
    *,
    page: int = 1,
    per_page: int = 50,
    search: str = "",
) -> dict[str, Any]:
    from models import CoupleReportPurchase, Kundli, Profile, User

    from database import db

    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.ilike(like))
            | (User.phone.ilike(like))
            | (User.email.ilike(like))
        )

    ordered = query.order_by(User.last_active.desc(), User.created_at.desc())
    # Flask-SQLAlchemy 3.x removed Query.paginate — use db.paginate instead.
    try:
        paginated = ordered.paginate(page=page, per_page=per_page, error_out=False)
    except AttributeError:
        paginated = db.paginate(
            ordered, page=page, per_page=per_page, error_out=False
        )

    user_ids = [u.id for u in paginated.items]
    profile_counts: dict[int, int] = {}
    if user_ids:
        from sqlalchemy import func

        rows = (
            db_session.query(Profile.user_id, func.count(Profile.id))
            .filter(Profile.user_id.in_(user_ids), Profile.deleted_at.is_(None))
            .group_by(Profile.user_id)
            .all()
        )
        profile_counts = {int(uid): int(cnt) for uid, cnt in rows}

    legacy_kundli_users: set[int] = set()
    if user_ids:
        legacy_rows = (
            db_session.query(Kundli.user_id)
            .filter(Kundli.user_id.in_(user_ids))
            .distinct()
            .all()
        )
        legacy_kundli_users = {int(r[0]) for r in legacy_rows}

    # Per-user paid purchase summary
    purchase_summary: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    if user_ids:
        try:
            paid_rows = CoupleReportPurchase.query.filter(
                CoupleReportPurchase.user_id.in_(user_ids),
                CoupleReportPurchase.status == "paid",
            ).all()
        except Exception:
            paid_rows = []
        for pr in paid_rows:
            purchase_summary[pr.user_id][pr.product] += 1

    users_out = []
    for u in paginated.items:
        ps = purchase_summary.get(u.id, {})
        users_out.append(
            {
                "id": u.id,
                "name": u.name or "",
                "phone": u.phone or "",
                "email": u.email or "",
                "plan": u.plan or "free",
                "plan_expiry": u.plan_expiry.isoformat() if u.plan_expiry else None,
                "last_login": (u.last_active or u.created_at).isoformat()
                if (u.last_active or u.created_at)
                else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "kundli_profiles_count": profile_counts.get(u.id, 0)
                or (1 if u.id in legacy_kundli_users else 0),
                "purchases": {
                    "love_compatibility_pdf": ps.get("love_reality_pro", 0),
                    "milan_pro_pdf": ps.get("milan_pro", 0),
                    "face_reading_pro": ps.get("face_reading_pro", 0),
                    "life_mastery_pdf": ps.get("life_mastery", 0),
                    "total_paid_orders": sum(ps.values()),
                },
                "career_unlocked": bool(getattr(u, "career_unlocked", False)),
            }
        )

    return {
        "users": users_out,
        "total": paginated.total,
        "page": page,
        "pages": paginated.pages,
        "per_page": per_page,
    }


def build_user_detail(user_id: int) -> dict[str, Any] | None:
    from database import db
    from models import (
        AstroVastuPurchase,
        CoupleReportPurchase,
        Kundli,
        LoginActivity,
        Profile,
        User,
    )

    user = db.session.get(User, user_id)
    if not user:
        return None

    profiles = (
        Profile.query.filter_by(user_id=user_id, deleted_at=None)
        .order_by(Profile.is_primary.desc(), Profile.updated_at.desc())
        .all()
    )
    deleted_count = Profile.query.filter(
        Profile.user_id == user_id, Profile.deleted_at.isnot(None)
    ).count()

    try:
        couple_paid = (
            CoupleReportPurchase.query.filter_by(user_id=user_id, status="paid")
            .order_by(CoupleReportPurchase.paid_at.desc())
            .all()
        )
    except Exception:
        couple_paid = []
    try:
        av_paid = (
            AstroVastuPurchase.query.filter_by(user_id=user_id, status="paid")
            .order_by(AstroVastuPurchase.paid_at.desc())
            .all()
        )
    except Exception:
        av_paid = []

    try:
        reports = rc.list_for_user(user_id, limit=100)
    except Exception:
        reports = []

    try:
        recent_logins = (
            LoginActivity.query.filter_by(user_id=user_id)
            .order_by(LoginActivity.created_at.desc())
            .limit(10)
            .all()
        )
    except Exception:
        recent_logins = []

    legacy_kundli = None
    kun = Kundli.query.filter_by(user_id=user_id).first()
    if kun:
        legacy_kundli = {
            "name": kun.name or "",
            "dob": kun.dob or "",
            "tob": kun.tob or "",
            "place": kun.pob or "",
            "lat": kun.lat,
            "lon": kun.lon,
            "tz": kun.tz,
            "has_chart": bool(kun.chart_data),
        }

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "phone": user.phone or "",
            "email": user.email or "",
            "plan": user.plan,
            "plan_expiry": user.plan_expiry.isoformat() if user.plan_expiry else None,
            "last_login": (user.last_active or user.created_at).isoformat()
            if (user.last_active or user.created_at)
            else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "career_unlocked": bool(user.career_unlocked),
        },
        "kundli_profiles": {
            "active_count": len(profiles),
            "deleted_count": deleted_count,
            "profiles": [_profile_admin_row(p, legacy_kundli) for p in profiles],
        },
        "legacy_kundli": legacy_kundli,
        "recent_logins": [
            {
                "id": row.id,
                "email": row.email,
                "ip": row.ip or "",
                "success": bool(row.success),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in recent_logins
        ],
        "couple_report_purchases": [
            {
                "product": r.product,
                "label": PRODUCT_LABELS.get(r.product, r.product),
                "amount_inr": r.amount,
                "paid_at": r.paid_at.isoformat() if r.paid_at else None,
            }
            for r in couple_paid
        ],
        "astrovastu_purchases": [
            {
                "sku": r.sku,
                "amount_inr": r.amount,
                "property_name": r.property_name,
                "paid_at": r.paid_at.isoformat() if r.paid_at else None,
            }
            for r in av_paid
        ],
        "cached_reports": reports,
    }
