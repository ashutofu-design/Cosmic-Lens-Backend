"""
Signup-only V1 Ask free questions — one lifetime grant per phone/email.

Claims persist after account deletion so delete + re-register cannot replay the gift.
"""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from database import db


def _norm_phone(phone: str | None) -> str | None:
    p = (phone or "").strip()
    return p or None


def _norm_email(email: str | None) -> str | None:
    e = (email or "").strip().lower()
    return e or None


def identity_claimed(kind: str, value: str) -> bool:
    from models import SignupFreeGiftClaim

    raw = (value or "").strip()
    if not raw:
        return False
    return (
        SignupFreeGiftClaim.query.filter_by(
            identity_kind=kind,
            identity_value=raw,
        ).first()
        is not None
    )


def signup_gift_already_claimed(*, phone: str | None = None, email: str | None = None) -> bool:
    p = _norm_phone(phone)
    e = _norm_email(email)
    if p and identity_claimed("phone", p):
        return True
    if e and identity_claimed("email", e):
        return True
    return False


def initial_free_questions_used(*, phone: str | None = None, email: str | None = None) -> int:
    """0 = grant 3 free signup questions; 3 = already claimed for this identity."""
    from subscription_helper import QUESTION_LIMITS

    if signup_gift_already_claimed(phone=phone, email=email):
        return int(QUESTION_LIMITS["free"])
    return 0


def record_signup_gift_claims(
    *,
    phone: str | None = None,
    email: str | None = None,
    user_id: int | None = None,
    source: str = "signup",
    commit: bool = True,
) -> int:
    """Idempotent. Returns count of new claim rows inserted."""
    from models import SignupFreeGiftClaim

    inserted = 0
    for kind, raw in (("phone", _norm_phone(phone)), ("email", _norm_email(email))):
        if not raw:
            continue
        if identity_claimed(kind, raw):
            continue
        db.session.add(
            SignupFreeGiftClaim(
                identity_kind=kind,
                identity_value=raw,
                source=(source or "signup")[:32],
                first_user_id=int(user_id) if user_id is not None else None,
            )
        )
        inserted += 1

    if not inserted:
        return 0

    try:
        if commit:
            db.session.commit()
        else:
            db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return 0
    return inserted


def ensure_claims_on_account_delete(user) -> None:
    """Lock phone/email before user row is removed."""
    if not user:
        return
    record_signup_gift_claims(
        phone=getattr(user, "phone", None),
        email=getattr(user, "email", None),
        user_id=getattr(user, "id", None),
        source="account_delete",
        commit=True,
    )


def backfill_signup_free_gift_claims() -> int:
    """One-time: existing users' phones/emails cannot replay signup gift after delete."""
    from models import SignupFreeGiftClaim, User

    if identity_claimed("system", "__signup_gift_backfill_v1__"):
        return 0

    total = 0
    rows = User.query.with_entities(User.id, User.phone, User.email).all()
    for user_id, phone, email in rows:
        total += record_signup_gift_claims(
            phone=phone,
            email=email,
            user_id=int(user_id),
            source="backfill",
            commit=True,
        )

    if not identity_claimed("system", "__signup_gift_backfill_v1__"):
        db.session.add(
            SignupFreeGiftClaim(
                identity_kind="system",
                identity_value="__signup_gift_backfill_v1__",
                source="backfill",
            )
        )
        db.session.commit()
    return total
