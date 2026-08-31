"""
Signup-only V1 Ask free questions — one lifetime grant per phone/email/Firebase UID.

Claims persist after account deletion so delete + re-register cannot replay the gift.
All identities are canonicalized (spaces, +91 variants, Gmail +alias / dots).
"""
from __future__ import annotations

import re

from sqlalchemy.exc import IntegrityError

from database import db

_IN10_RE = re.compile(r"^[6-9]\d{9}$")
_BACKFILL_V2 = "__signup_gift_backfill_v2__"


def canonical_phone_e164(phone: str | None) -> str | None:
    """Normalize Indian mobiles to +91XXXXXXXXXX (spaces/dashes/+91 variants stripped)."""
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        return None
    if digits.startswith("91"):
        if len(digits) != 12:
            return None
        digits = digits[2:]
    elif len(digits) != 10:
        return None
    if not _IN10_RE.match(digits):
        return None
    return f"+91{digits}"


def canonical_in10(phone: str | None) -> str | None:
    e164 = canonical_phone_e164(phone)
    return e164[3:] if e164 else None


def canonical_email(email: str | None) -> str | None:
    raw = (email or "").strip().lower()
    if not raw or "@" not in raw:
        return raw or None
    local, domain = raw.rsplit("@", 1)
    domain = domain.strip()
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def canonical_firebase_uid(uid: str | None) -> str | None:
    u = (uid or "").strip()
    return u or None


def _identity_keys(
    *,
    phone: str | None = None,
    email: str | None = None,
    firebase_uid: str | None = None,
) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    p = canonical_phone_e164(phone)
    if p:
        keys.append(("phone", p))
        in10 = p[3:]
        keys.append(("in10", in10))
    e = canonical_email(email)
    if e:
        keys.append(("email", e))
    uid = canonical_firebase_uid(firebase_uid)
    if uid:
        keys.append(("firebase_uid", uid))
    # Dedupe while preserving order
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for item in keys:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


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


def signup_gift_already_claimed(
    *,
    phone: str | None = None,
    email: str | None = None,
    firebase_uid: str | None = None,
) -> bool:
    for kind, value in _identity_keys(
        phone=phone, email=email, firebase_uid=firebase_uid
    ):
        if identity_claimed(kind, value):
            return True
    return False


def initial_free_questions_used(
    *,
    phone: str | None = None,
    email: str | None = None,
    firebase_uid: str | None = None,
) -> int:
    """0 = grant 3 free signup questions; 3 = already claimed for this identity."""
    from subscription_helper import QUESTION_LIMITS

    if signup_gift_already_claimed(
        phone=phone, email=email, firebase_uid=firebase_uid
    ):
        return int(QUESTION_LIMITS["free"])
    return 0


def record_signup_gift_claims(
    *,
    phone: str | None = None,
    email: str | None = None,
    firebase_uid: str | None = None,
    user_id: int | None = None,
    source: str = "signup",
    commit: bool = True,
) -> int:
    """Idempotent. Returns count of new claim rows inserted."""
    from models import SignupFreeGiftClaim

    inserted = 0
    for kind, raw in _identity_keys(
        phone=phone, email=email, firebase_uid=firebase_uid
    ):
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
    """Lock phone/email/Firebase UID before user row is removed."""
    if not user:
        return
    record_signup_gift_claims(
        phone=getattr(user, "phone", None),
        email=getattr(user, "email", None),
        firebase_uid=(getattr(user, "google_id", None) or None),
        user_id=getattr(user, "id", None),
        source="account_delete",
        commit=True,
    )


def _renormalize_claim_row(row) -> int:
    """Rewrite one claim to canonical identity; drop duplicates. Returns inserts net."""
    from models import SignupFreeGiftClaim

    kind = (row.identity_kind or "").strip()
    value = (row.identity_value or "").strip()
    if not kind or not value or kind == "system":
        return 0

    if kind == "phone":
        canon = canonical_phone_e164(value)
        targets = [("phone", canon), ("in10", canon[3:] if canon else None)]
    elif kind == "in10":
        canon10 = canonical_in10(value) or (
            value if _IN10_RE.match(value) else None
        )
        targets = [
            ("in10", canon10),
            ("phone", canonical_phone_e164(canon10) if canon10 else None),
        ]
    elif kind == "email":
        targets = [("email", canonical_email(value))]
    elif kind == "firebase_uid":
        targets = [("firebase_uid", canonical_firebase_uid(value))]
    else:
        targets = [(kind, value)]

    inserted = 0
    for target_kind, target_value in targets:
        if not target_value:
            continue
        if identity_claimed(target_kind, target_value):
            continue
        db.session.add(
            SignupFreeGiftClaim(
                identity_kind=target_kind,
                identity_value=target_value,
                source=(row.source or "renorm")[:32],
                first_user_id=row.first_user_id,
            )
        )
        inserted += 1

    db.session.delete(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return 0
    return inserted


def renormalize_existing_claims() -> int:
    """One-time: canonicalize legacy claim rows (spaces, Gmail aliases, in10)."""
    from models import SignupFreeGiftClaim, User

    if identity_claimed("system", _BACKFILL_V2):
        return 0

    total = 0
    rows = (
        SignupFreeGiftClaim.query.filter(SignupFreeGiftClaim.identity_kind != "system")
        .order_by(SignupFreeGiftClaim.id.asc())
        .all()
    )
    for row in list(rows):
        if not db.session.get(SignupFreeGiftClaim, row.id):
            continue
        total += _renormalize_claim_row(row)

    rows_users = User.query.with_entities(
        User.id, User.phone, User.email, User.google_id
    ).all()
    for user_id, phone, email, google_id in rows_users:
        total += record_signup_gift_claims(
            phone=phone,
            email=email,
            firebase_uid=google_id,
            user_id=int(user_id),
            source="backfill_v2",
            commit=True,
        )

    db.session.add(
        SignupFreeGiftClaim(
            identity_kind="system",
            identity_value=_BACKFILL_V2,
            source="backfill_v2",
        )
    )
    db.session.commit()
    return total


def backfill_signup_free_gift_claims() -> int:
    """One-time: existing users' phones/emails cannot replay signup gift after delete."""
    from models import SignupFreeGiftClaim, User

    if identity_claimed("system", "__signup_gift_backfill_v1__"):
        return renormalize_existing_claims()

    total = 0
    rows = User.query.with_entities(
        User.id, User.phone, User.email, User.google_id
    ).all()
    for user_id, phone, email, google_id in rows:
        total += record_signup_gift_claims(
            phone=phone,
            email=email,
            firebase_uid=google_id,
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

    return total + renormalize_existing_claims()
