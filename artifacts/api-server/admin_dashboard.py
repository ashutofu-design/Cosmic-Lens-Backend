"""
Local admin dashboard data aggregation for Cosmic Lens.

Used by /api/admin/* routes. Set ADMIN_NO_AUTH=1 explicitly for password-free local use.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import report_cache as rc

_DASHBOARD_CACHE_TTL_S = float(os.environ.get("ADMIN_DASHBOARD_CACHE_TTL_S", "45"))
_dashboard_cache: dict[str, Any] = {"at": 0.0, "payload": None}


def resolve_login_activity_display(
    row: Any,
    user: Any | None = None,
) -> dict[str, str]:
    """Map login_activity row + optional User → method label and identifier for admin UI."""
    provider = str(getattr(row, "provider", None) or "").strip().lower()
    row_email = str(getattr(row, "email", None) or "").strip()
    user_email = str(getattr(user, "email", None) or "").strip() if user else ""
    user_phone = str(getattr(user, "phone", None) or "").strip() if user else ""
    email = row_email or user_email

    if provider == "google" or ("@" in email and provider != "phone"):
        return {"login_method": "gmail", "login_id": email}
    if provider == "phone" or user_phone:
        return {"login_method": "phone", "login_id": user_phone or email}
    if "@" in email:
        return {"login_method": "gmail", "login_id": email}
    if email:
        return {"login_method": "gmail", "login_id": email}
    return {"login_method": "unknown", "login_id": user_phone or "—"}

_UTC = timezone.utc

PLAN_LABELS: dict[str, str] = {
    "free": "Free",
    "trial": "Trial",
    "basic": "Basic",
    "pro": "Pro",
    "elite": "Elite",
}


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


def batch_profile_counts(db_session, user_ids: list[int]) -> dict[int, int]:
    """Active profile count per user (legacy kundli alone counts as 1)."""
    if not user_ids:
        return {}
    from models import Kundli, Profile
    from sqlalchemy import func

    ids = [int(x) for x in user_ids]
    rows = (
        db_session.query(Profile.user_id, func.count(Profile.id))
        .filter(Profile.user_id.in_(ids), Profile.deleted_at.is_(None))
        .group_by(Profile.user_id)
        .all()
    )
    counts: dict[int, int] = {int(uid): int(cnt) for uid, cnt in rows}
    legacy_rows = (
        db_session.query(Kundli.user_id)
        .filter(Kundli.user_id.in_(ids))
        .distinct()
        .all()
    )
    for (uid,) in legacy_rows:
        u = int(uid)
        if counts.get(u, 0) == 0:
            counts[u] = 1
    for uid in ids:
        counts.setdefault(uid, 0)
    return counts


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


def build_dashboard(db_session, *, force_refresh: bool = False) -> dict[str, Any]:
    now_ts = time.time()
    cached = _dashboard_cache.get("payload")
    if (
        not force_refresh
        and cached
        and now_ts - float(_dashboard_cache.get("at") or 0.0) < _DASHBOARD_CACHE_TTL_S
    ):
        return cached

    from sqlalchemy import func

    from models import (
        AstroVastuPurchase,
        CoupleReportPurchase,
        Kundli,
        Profile,
        User,
    )

    now = _now_naive()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_week = _since(days=7)
    start_month = _since(days=30)

    total_users = User.query.count()
    pro_users = User.query.filter_by(is_pro=True).count()
    active_cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
    active_today = User.query.filter(User.last_active >= active_cutoff).count()
    total_kundli = Kundli.query.count()

    # ── Payments from DB tables (SQL aggregates — avoid loading all rows) ───
    def _sum_couple_since(since: datetime | None) -> int:
        q = CoupleReportPurchase.query.filter_by(status="paid")
        if since is not None:
            q = q.filter(CoupleReportPurchase.paid_at >= since)
        return int(q.with_entities(func.coalesce(func.sum(CoupleReportPurchase.amount), 0)).scalar() or 0)

    def _sum_av_since(since: datetime | None) -> int:
        q = AstroVastuPurchase.query.filter_by(status="paid")
        if since is not None:
            q = q.filter(AstroVastuPurchase.paid_at >= since)
        return int(q.with_entities(func.coalesce(func.sum(AstroVastuPurchase.amount), 0)).scalar() or 0)

    def payment_totals(since: datetime | None) -> int:
        t = _sum_couple_since(since) + _sum_av_since(since)
        try:
            from career_billing import price_inr as career_price

            career_amt = career_price()
        except Exception:
            career_amt = 1
        career_q = User.query.filter_by(career_unlocked=True)
        if since is not None:
            career_q = career_q.filter(User.career_unlocked_at >= since)
        t += career_q.count() * career_amt
        try:
            from models import AstroVastuPropertyUnlock

            pu_q = AstroVastuPropertyUnlock.query
            if since is not None:
                pu_q = pu_q.filter(AstroVastuPropertyUnlock.unlocked_at >= since)
            t += int(
                pu_q.with_entities(
                    func.coalesce(func.sum(AstroVastuPropertyUnlock.amount_paid), 0)
                ).scalar()
                or 0
            )
        except Exception:
            pass
        return t

    payments = {
        "today_inr": payment_totals(start_today),
        "week_inr": payment_totals(start_week),
        "month_inr": payment_totals(start_month),
        "lifetime_inr": payment_totals(None),
    }

    # ── Per-product purchase counts (paid) ───────────────────────────────────
    product_counts: Counter[str] = Counter()
    try:
        for product, cnt in (
            CoupleReportPurchase.query.filter_by(status="paid")
            .with_entities(CoupleReportPurchase.product, func.count())
            .group_by(CoupleReportPurchase.product)
            .all()
        ):
            product_counts[product or "unknown"] += int(cnt or 0)
    except Exception:
        pass
    av_sku_counts: Counter[str] = Counter()
    try:
        for sku, cnt in (
            AstroVastuPurchase.query.filter_by(status="paid")
            .with_entities(AstroVastuPurchase.sku, func.count())
            .group_by(AstroVastuPurchase.sku)
            .all()
        ):
            av_sku_counts[sku or "unknown"] += int(cnt or 0)
    except Exception:
        pass

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

    payload = {
        "generated_at": now.isoformat() + "Z",
        "total_users": total_users,
        "pro_users": pro_users,
        "active_today": active_today,
        "total_kundli": total_kundli,
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
            "enabled": True,
            "message": "Plan counts = current labels on user accounts (phone + Gmail login).",
            "plan_counts": dict(plan_counts),
        },
    }

    _dashboard_cache["at"] = now_ts
    _dashboard_cache["payload"] = payload
    return payload


def build_users_list(
    db_session,
    *,
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    plan: str = "",
) -> dict[str, Any]:
    from models import CoupleReportPurchase, Kundli, Profile, User

    from database import db

    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.ilike(like))
            | (User.email.ilike(like))
        )
    plan_filter = (plan or "").strip().lower()
    if plan_filter:
        query = query.filter(User.plan == plan_filter)

    ordered = query.order_by(User.last_active.desc(), User.created_at.desc())
    # Flask-SQLAlchemy 3.x removed Query.paginate — use db.paginate instead.
    try:
        paginated = ordered.paginate(page=page, per_page=per_page, error_out=False)
    except AttributeError:
        paginated = db.paginate(
            ordered, page=page, per_page=per_page, error_out=False
        )

    user_ids = [u.id for u in paginated.items]
    profile_counts = batch_profile_counts(db_session, user_ids) if user_ids else {}

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
                "email": u.email or "",
                "plan": u.plan or "free",
                "plan_expiry": u.plan_expiry.isoformat() if u.plan_expiry else None,
                "last_login": (u.last_active or u.created_at).isoformat()
                if (u.last_active or u.created_at)
                else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "kundli_profiles_count": profile_counts.get(u.id, 0),
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


def _service_queues_for_user(user_id: int) -> list[dict[str, Any]]:
    """File-queue intakes linked to a user (not Razorpay purchase rows)."""
    rows: list[dict[str, Any]] = []

    def _match(uid: Any) -> bool:
        try:
            return int(uid or 0) == int(user_id)
        except (TypeError, ValueError):
            return False

    try:
        from love_reality_human_orders import list_human_orders

        for row in list_human_orders(page=1, per_page=100).get("orders") or []:
            if _match(row.get("user_id")):
                rows.append(
                    {
                        "kind": "love_reality_human",
                        "label": "Love Reality founder PDF",
                        "ref": row.get("order_id") or "",
                        "status": row.get("status") or "",
                        "created_at": row.get("created_at"),
                        "detail": f"{row.get('p1_name') or '—'} & {row.get('p2_name') or '—'}",
                    }
                )
    except Exception:
        pass

    try:
        from milan_human_orders import list_milan_human_orders

        for row in list_milan_human_orders(page=1, per_page=100).get("orders") or []:
            if _match(row.get("user_id")):
                rows.append(
                    {
                        "kind": "milan_human",
                        "label": "Kundli Milan founder PDF",
                        "ref": row.get("order_id") or "",
                        "status": row.get("status") or "",
                        "created_at": row.get("created_at"),
                        "detail": f"{row.get('p1_name') or '—'} & {row.get('p2_name') or '—'}",
                    }
                )
    except Exception:
        pass

    try:
        from business_vastu_human_orders import list_business_vastu_orders

        for row in list_business_vastu_orders(page=1, per_page=100).get("orders") or []:
            if _match(row.get("user_id")):
                rows.append(
                    {
                        "kind": "business_vastu",
                        "label": "Business Vastu intake",
                        "ref": row.get("order_id") or "",
                        "status": row.get("status") or "",
                        "created_at": row.get("created_at"),
                        "detail": row.get("property_name") or row.get("business_type") or "",
                    }
                )
    except Exception:
        pass

    try:
        from birth_time_rectification_orders import list_birth_time_rectification_orders

        for row in list_birth_time_rectification_orders(page=1, per_page=100).get(
            "orders"
        ) or []:
            if _match(row.get("user_id")):
                rows.append(
                    {
                        "kind": "birth_time_rectification",
                        "label": "Birth Time Rectification",
                        "ref": row.get("order_id") or "",
                        "status": row.get("status") or "",
                        "created_at": row.get("created_at"),
                        "detail": row.get("full_name") or "",
                    }
                )
    except Exception:
        pass

    try:
        from cosmic_intelligence_v3_sessions import list_v3_sessions

        for row in list_v3_sessions(page=1, per_page=100).get("sessions") or []:
            if _match(row.get("user_id")):
                rows.append(
                    {
                        "kind": "v3_live",
                        "label": "V3 Live Chat",
                        "ref": row.get("session_id") or "",
                        "status": row.get("status") or "",
                        "created_at": row.get("created_at"),
                        "detail": row.get("label") or f"{row.get('minutes') or '—'} min",
                    }
                )
    except Exception:
        pass

    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return rows[:40]


def build_user_detail(user_id: int) -> dict[str, Any] | None:
    from datetime import datetime, timedelta

    from database import db
    from models import (
        AppUsageDay,
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
        from purchase_history import build_user_purchase_history

        purchase_history = build_user_purchase_history(user_id)
    except Exception:
        purchase_history = []

    try:
        today_ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()
        since = (today_ist - timedelta(days=29)).isoformat()
        usage_rows = (
            AppUsageDay.query.filter(
                AppUsageDay.user_id == user_id,
                AppUsageDay.usage_date >= since,
            )
            .order_by(AppUsageDay.usage_date.desc())
            .all()
        )
    except Exception:
        usage_rows = []
        today_ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()

    usage_total = sum(max(0, int(row.foreground_seconds or 0)) for row in usage_rows)
    active_days = len([row for row in usage_rows if (row.foreground_seconds or 0) > 0])
    today_usage = next(
        (
            max(0, int(row.foreground_seconds or 0))
            for row in usage_rows
            if row.usage_date == today_ist.isoformat()
        ),
        0,
    )
    seven_day_cutoff = (today_ist - timedelta(days=6)).isoformat()
    seven_day_total = sum(
        max(0, int(row.foreground_seconds or 0))
        for row in usage_rows
        if row.usage_date >= seven_day_cutoff
    )
    bought_couple_products = {row.product for row in couple_paid}
    has_astrovastu_purchase = bool(av_paid)
    has_gemstone_purchase = any(
        row.get("kind") == "gemstone" for row in purchase_history
    )
    product_access = [
        {
            "key": "subscription",
            "label": "Paid subscription",
            "owned": bool(user.plan and user.plan != "free"),
            "detail": (user.plan or "free").title(),
        },
        {
            "key": "milan_pro",
            "label": "Kundli Milan Pro PDF",
            "owned": "milan_pro" in bought_couple_products,
            "detail": "",
        },
        {
            "key": "love_reality_pro",
            "label": "Love Compatibility PDF",
            "owned": "love_reality_pro" in bought_couple_products,
            "detail": "",
        },
        {
            "key": "astrovastu",
            "label": "AstroVastu purchase",
            "owned": has_astrovastu_purchase,
            "detail": "",
        },
        {
            "key": "career",
            "label": "Career Life Map",
            "owned": bool(user.career_unlocked),
            "detail": "",
        },
        {
            "key": "gemstone",
            "label": "Gemstone order",
            "owned": has_gemstone_purchase,
            "detail": "",
        },
    ]

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

    pack_referral: dict[str, Any] = {
        "referral_code": f"CL{int(user_id)}",
        "referred_by_user_id": getattr(user, "referred_by_user_id", None),
        "friends_signed_up": 0,
        "friends_converted": 0,
        "questions_earned": 0,
        "bonus_questions_left": int(getattr(user, "ask_v1_bonus_questions", 0) or 0),
        "recent_signups": [],
        "recent_conversions": [],
    }
    try:
        from pack_referral import referral_code_for_user

        pack_referral["referral_code"] = referral_code_for_user(int(user_id))
    except Exception:
        pass
    try:
        from models import PackReferralReward

        signed_up = (
            User.query.filter_by(referred_by_user_id=user_id)
            .order_by(User.created_at.desc())
            .limit(20)
            .all()
        )
        pack_referral["friends_signed_up"] = User.query.filter_by(
            referred_by_user_id=user_id
        ).count()
        pack_referral["recent_signups"] = [
            {
                "user_id": u.id,
                "name": u.name or "",
                "email": u.email or "",
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in signed_up
        ]
        rewards = (
            PackReferralReward.query.filter_by(referrer_user_id=user_id)
            .order_by(PackReferralReward.created_at.desc())
            .limit(20)
            .all()
        )
        pack_referral["friends_converted"] = PackReferralReward.query.filter_by(
            referrer_user_id=user_id
        ).count()
        try:
            from sqlalchemy import func

            earned_total = (
                db.session.query(
                    func.coalesce(func.sum(PackReferralReward.questions_granted), 0)
                )
                .filter(PackReferralReward.referrer_user_id == user_id)
                .scalar()
            )
            pack_referral["questions_earned"] = int(earned_total or 0)
        except Exception:
            pack_referral["questions_earned"] = sum(
                int(r.questions_granted or 0) for r in rewards
            )
        pack_referral["recent_conversions"] = [
            {
                "buyer_user_id": r.buyer_user_id,
                "source_kind": r.source_kind,
                "questions_granted": int(r.questions_granted or 0),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rewards
        ]
    except Exception:
        pass

    return {
        "user": {
            "id": user.id,
            "cosmo_user_id": (getattr(user, "cosmo_user_id", None) or "").strip(),
            "name": user.name,
            "email": user.email or "",
            "plan": user.plan,
            "plan_expiry": user.plan_expiry.isoformat() if user.plan_expiry else None,
            "preferred_language": getattr(user, "preferred_language", None),
            "daily_questions_used": int(getattr(user, "daily_questions_used", 0) or 0),
            "daily_questions_date": getattr(user, "daily_questions_date", "") or "",
            "daily_kundlis_used": int(getattr(user, "daily_kundlis_used", 0) or 0),
            "daily_kundlis_date": getattr(user, "daily_kundlis_date", "") or "",
            "astrovastu_room_credits": int(
                getattr(user, "astrovastu_room_credits", 0) or 0
            ),
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
                **resolve_login_activity_display(row, user),
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
        "purchase_history": purchase_history,
        "purchase_summary": {
            "total_orders": len(purchase_history),
            "total_spent_inr": sum(
                max(0, int(row.get("amount_inr") or 0)) for row in purchase_history
            ),
        },
        "product_access": product_access,
        "service_queues": _service_queues_for_user(user_id),
        "app_usage": {
            "tracking_started": bool(usage_rows),
            "today_seconds": today_usage,
            "last_7_days_seconds": seven_day_total,
            "last_30_days_seconds": usage_total,
            "active_days_last_30": active_days,
            "avg_seconds_per_active_day": round(usage_total / active_days)
            if active_days
            else 0,
            "daily": [
                {
                    "date": row.usage_date,
                    "seconds": max(0, int(row.foreground_seconds or 0)),
                    "sessions": max(0, int(row.session_count or 0)),
                }
                for row in usage_rows[:14]
            ],
        },
        "pack_referral": pack_referral,
        "cached_reports": reports,
    }


def build_gmail_profiles_view(
    *,
    email: str = "",
    user_id: int | None = None,
) -> dict[str, Any]:
    """Minimal profile list for admin Gmail logins → View (name, DOB, time, place only)."""
    from database import db
    from models import Kundli, Profile, User

    email_norm = (email or "").strip()
    user = None
    if user_id:
        user = db.session.get(User, user_id)
    elif email_norm:
        user = User.query.filter(
            db.func.lower(User.email) == email_norm.lower()
        ).first()

    profiles_out: list[dict[str, Any]] = []
    legacy_dict: dict[str, Any] | None = None

    if user:
        legacy_k = Kundli.query.filter_by(user_id=user.id).first()
        if legacy_k:
            legacy_dict = {
                "name": legacy_k.name or "",
                "dob": legacy_k.dob or "",
                "tob": legacy_k.tob or "",
                "place": legacy_k.pob or "",
                "has_chart": bool(legacy_k.chart_data),
            }

        active = (
            Profile.query.filter_by(user_id=user.id, deleted_at=None)
            .order_by(Profile.is_primary.desc(), Profile.updated_at.desc())
            .all()
        )
        for p in active:
            row = _profile_admin_row(p, legacy_dict)
            profiles_out.append(
                {
                    "id": p.id,
                    "legacy": False,
                    "name": row["name"] or "—",
                    "dob": row["dob"] or "—",
                    "tob": row["tob"] or "—",
                    "place": row["place"] or "—",
                }
            )

        if not profiles_out and legacy_dict:
            profiles_out.append(
                {
                    "id": None,
                    "legacy": True,
                    "name": legacy_dict.get("name") or user.name or "—",
                    "dob": legacy_dict.get("dob") or "—",
                    "tob": legacy_dict.get("tob") or "—",
                    "place": legacy_dict.get("place") or "—",
                }
            )

    subscription: dict[str, Any] | None = None
    purchases_out: list[dict[str, Any]] = []

    if user:
        plan_key = (user.plan or "free").lower()
        plan_active = (
            plan_key != "free"
            and user.plan_expiry is not None
            and user.plan_expiry > _now_naive()
        )
        active_plan = plan_key if plan_active else "free"
        subscription = {
            "plan": active_plan,
            "plan_label": PLAN_LABELS.get(active_plan, active_plan.title()),
            "plan_expiry": user.plan_expiry.isoformat() if user.plan_expiry else None,
        }

        from purchase_history import build_user_purchase_history

        for row in build_user_purchase_history(user.id):
            purchases_out.append(
                {
                    "name": row.get("title") or "—",
                    "amount_inr": int(row.get("amount_inr") or 0),
                    "paid_at": row.get("paid_at"),
                }
            )

    return {
        "email": email_norm or (user.email if user else ""),
        "user_id": user.id if user else None,
        "user_name": (user.name or "") if user else "",
        "subscription": subscription,
        "purchases": purchases_out,
        "profiles": profiles_out,
    }


def build_pdf_generations(
    *,
    page: int = 1,
    per_page: int = 50,
    kind: str | None = None,
) -> dict[str, Any]:
    """OpenAI token + INR ledger for admin PDF cost tab."""
    from pdf_generation_log import list_generations

    return list_generations(page=page, per_page=per_page, kind=kind or None)


def build_ask_questions(
    *,
    page: int = 1,
    per_page: int = 50,
    user_id: int | None = None,
    email: str | None = None,
) -> dict[str, Any]:
    """Ask Q&A + OpenAI token + INR ledger for admin panel."""
    from question_history import list_admin_ask_questions

    return list_admin_ask_questions(
        page=page,
        per_page=per_page,
        user_id=user_id,
        email=email,
    )


def build_ask_question_detail(question_id: str) -> dict[str, Any] | None:
    from question_history import get_admin_ask_question

    return get_admin_ask_question(question_id)
