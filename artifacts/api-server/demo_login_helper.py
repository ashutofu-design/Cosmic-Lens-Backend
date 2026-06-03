"""
Bulletproof demo login for VPS — patches missing User columns, then upserts demo user.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from database import db, get_database_url
from sqlalchemy import text

DEMO_PHONE = "+919999000001"

# Idempotent PostgreSQL patches (one commit each — partial failure won't block the rest).
_PG_USER_PATCHES: tuple[str, ...] = (
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(64)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS country_code VARCHAR(4) DEFAULT '91'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(4)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS cosmo_user_id VARCHAR(16)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS personal_name_locked BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS personal_phone_locked BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS career_unlocked BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS career_unlock_order_id VARCHAR(200)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS career_unlocked_at TIMESTAMP",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS astrovastu_room_credits INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS astrovastu_floor_scan_wallet TEXT NOT NULL DEFAULT '{}'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_astrovastu_pro_used INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_astrovastu_pro_month VARCHAR(7) NOT NULL DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_kundlis_used INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_kundlis_date VARCHAR(10) NOT NULL DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_questions_used INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_questions_date VARCHAR(10) NOT NULL DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS push_enabled BOOLEAN NOT NULL DEFAULT TRUE",
)


def patch_users_table_for_demo() -> None:
    if "postgresql" not in get_database_url():
        return
    for sql in _PG_USER_PATCHES:
        try:
            with db.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception as exc:
            print(f"[demo-login] schema patch skipped: {exc}", flush=True)


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _demo_payload(
    *,
    user_id: int,
    api_key: str,
    is_new: bool,
    name: str = "Demo User",
    cosmo_user_id: str | None = None,
    subscription: dict | None = None,
) -> dict[str, Any]:
    expiry = _utc_naive_now() + timedelta(days=365 * 10)
    return {
        "ok": True,
        "id": user_id,
        "api_key": api_key,
        "name": name,
        "phone": DEMO_PHONE,
        "country_code": "91",
        "email": "",
        "cosmo_user_id": (cosmo_user_id or "").strip().upper() or None,
        "is_pro": True,
        "plan": "pro",
        "plan_expiry": expiry.isoformat(),
        "preferred_language": None,
        "personal_name_locked": False,
        "personal_phone_locked": False,
        "career_unlocked": False,
        "created_at": _utc_naive_now().isoformat(),
        "is_new_user": is_new,
        "subscription": subscription
        or {"plan": "pro", "is_pro": True, "analysis_mode": "pro"},
    }


def _sql_demo_login() -> dict[str, Any]:
    """Minimal SQL path when ORM model/schema is out of sync."""
    now = _utc_naive_now()
    expiry = now + timedelta(days=365 * 10)

    row = (
        db.session.execute(
            text(
                "SELECT id, api_key, name FROM users WHERE phone = :phone LIMIT 1"
            ),
            {"phone": DEMO_PHONE},
        )
        .mappings()
        .first()
    )

    is_new = False
    if row is None:
        is_new = True
        api_key = secrets.token_hex(32)
        ins = (
            db.session.execute(
                text(
                    """
                    INSERT INTO users (
                        name, phone, country_code, api_key, is_pro, plan, plan_expiry,
                        created_at, last_active
                    )
                    VALUES (
                        'Demo User', :phone, '91', :api_key, TRUE, 'pro', :expiry,
                        :now, :now
                    )
                    RETURNING id, api_key
                    """
                ),
                {"phone": DEMO_PHONE, "api_key": api_key, "expiry": expiry, "now": now},
            )
            .mappings()
            .first()
        )
        if not ins:
            raise RuntimeError("demo user insert returned no row")
        user_id = int(ins["id"])
        api_key = str(ins["api_key"] or api_key)
    else:
        user_id = int(row["id"])
        api_key = str(row["api_key"] or "") or secrets.token_hex(32)
        db.session.execute(
            text(
                """
                UPDATE users
                SET is_pro = TRUE, plan = 'pro', plan_expiry = :expiry,
                    api_key = :api_key, last_active = :now
                WHERE id = :id
                """
            ),
            {"id": user_id, "api_key": api_key, "expiry": expiry, "now": now},
        )

    db.session.commit()
    return _demo_payload(
        user_id=user_id,
        api_key=api_key,
        is_new=is_new,
        name=str(row["name"]) if row and row.get("name") else "Demo User",
    )


def _orm_demo_login() -> dict[str, Any]:
    from models import User

    from subscription_helper import subscription_status

    user = User.query.filter_by(phone=DEMO_PHONE).first()
    is_new = False
    if not user:
        is_new = True
        user = User(
            name="Demo User",
            phone=DEMO_PHONE,
            country_code="91",
            api_key=secrets.token_hex(32),
        )
        db.session.add(user)
    else:
        if not user.api_key:
            user.api_key = secrets.token_hex(32)
        user.last_active = _utc_naive_now()

    user.is_pro = True
    user.plan = "pro"
    user.plan_expiry = _utc_naive_now() + timedelta(days=365 * 10)
    db.session.flush()

    try:
        from cosmo_user_id import ensure_user_cosmo_id

        ensure_user_cosmo_id(user)
    except Exception:
        pass

    db.session.commit()

    cosmo = (getattr(user, "cosmo_user_id", None) or "").strip().upper() or None
    try:
        sub = subscription_status(user)
    except Exception:
        sub = {"plan": "pro", "is_pro": True, "analysis_mode": "pro"}

    return _demo_payload(
        user_id=int(user.id),
        api_key=str(user.api_key or ""),
        is_new=is_new,
        name=str(user.name or "Demo User"),
        cosmo_user_id=cosmo,
        subscription=sub,
    )


def perform_demo_login() -> tuple[dict[str, Any], int]:
    """Returns (json_body, http_status)."""
    from database import run_schema_migrations

    try:
        run_schema_migrations()
    except Exception:
        pass
    patch_users_table_for_demo()

    try:
        return _orm_demo_login(), 200
    except Exception as orm_exc:
        db.session.rollback()
        print(f"[demo-login] ORM path failed, trying SQL: {orm_exc}", flush=True)
        try:
            return _sql_demo_login(), 200
        except Exception as sql_exc:
            db.session.rollback()
            raise RuntimeError(f"ORM: {orm_exc} | SQL: {sql_exc}") from sql_exc
