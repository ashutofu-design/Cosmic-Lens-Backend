"""
Public Cosmic Lens user IDs: COSMO100, COSMO101, … (starts at 100).
Assigned once at signup; shown read-only in Personal Details.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from models import User

COSMO_PREFIX = "COSMO"
COSMO_MIN = 100
_COSMO_RE = re.compile(r"^COSMO(\d+)$", re.IGNORECASE)
_COL_AVAILABLE: bool | None = None


def users_have_cosmo_column() -> bool:
    """True when DB schema includes users.cosmo_user_id (migration applied)."""
    global _COL_AVAILABLE
    if _COL_AVAILABLE is not None:
        return _COL_AVAILABLE
    try:
        from sqlalchemy import inspect

        from database import db

        cols = {c["name"] for c in inspect(db.engine).get_columns("users")}
        _COL_AVAILABLE = "cosmo_user_id" in cols
    except Exception:
        _COL_AVAILABLE = False
    return _COL_AVAILABLE


def format_cosmo_user_id(n: int) -> str:
    return f"{COSMO_PREFIX}{n}"


def parse_cosmo_number(cosmo_user_id: str | None) -> int | None:
    if not cosmo_user_id:
        return None
    m = _COSMO_RE.match(str(cosmo_user_id).strip())
    return int(m.group(1)) if m else None


def _max_assigned_number() -> int:
    from models import User

    mx = COSMO_MIN - 1
    rows = User.query.with_entities(User.cosmo_user_id).filter(
        User.cosmo_user_id.isnot(None),
    ).all()
    for (cid,) in rows:
        n = parse_cosmo_number(cid)
        if n is not None:
            mx = max(mx, n)
    return mx


def allocate_cosmo_user_id() -> str:
    """Next ID after current max (unique constraint + retry on race)."""
    n = _max_assigned_number() + 1
    if n < COSMO_MIN:
        n = COSMO_MIN
    return format_cosmo_user_id(n)


def ensure_user_cosmo_id(user: "User") -> str:
    """Assign cosmo_user_id if missing; returns the user's public id (or "")."""
    if not users_have_cosmo_column():
        return ""

    existing = (getattr(user, "cosmo_user_id", None) or "").strip()
    if existing:
        return existing.upper()

    from database import db

    try:
        for _ in range(25):
            cid = allocate_cosmo_user_id()
            user.cosmo_user_id = cid
            try:
                with db.session.begin_nested():
                    db.session.flush()
                return cid
            except IntegrityError:
                user.cosmo_user_id = None
                continue
    except Exception:
        user.cosmo_user_id = None
        return ""
    return ""


def backfill_missing_cosmo_user_ids() -> int:
    """Assign IDs to legacy users in account creation order."""
    if not users_have_cosmo_column():
        return 0

    from database import db
    from models import User

    missing = (
        User.query.filter(
            (User.cosmo_user_id.is_(None)) | (User.cosmo_user_id == ""),
        )
        .order_by(User.id.asc())
        .all()
    )
    count = 0
    for user in missing:
        ensure_user_cosmo_id(user)
        count += 1
    if count:
        db.session.commit()
    return count
