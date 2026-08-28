"""
Cosmic Pack referral — share code; when referred user buys any V1 or V3 pack,
referrer gets +3 free Ask (V1) questions. Once per referred buyer.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy import update

BONUS_QUESTIONS = 3
_REF_CODE_RE = re.compile(r"^CL(\d+)$", re.I)


def referral_code_for_user(user_id: int) -> str:
    return f"CL{int(user_id)}"


def resolve_referrer_user_id(code: str | None) -> int | None:
    raw = (code or "").strip().upper()
    if not raw:
        return None
    m = _REF_CODE_RE.match(raw)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def attach_referrer(buyer_user, code: str | None) -> dict[str, Any]:
    """Save referred_by once. Returns {ok, error?}."""
    from database import db

    if not buyer_user:
        return {"ok": False, "error": "auth_required"}

    existing = getattr(buyer_user, "referred_by_user_id", None)
    if existing:
        return {
            "ok": True,
            "already": True,
            "referred_by_user_id": int(existing),
            "referral_code": referral_code_for_user(int(existing)),
        }

    referrer_id = resolve_referrer_user_id(code)
    if referrer_id is None:
        return {"ok": False, "error": "invalid_code"}
    if referrer_id == int(buyer_user.id):
        return {"ok": False, "error": "self_referral_not_allowed"}

    from models import User

    referrer = db.session.get(User, referrer_id)
    if not referrer:
        return {"ok": False, "error": "invalid_code"}

    buyer_user.referred_by_user_id = referrer_id
    db.session.commit()
    return {
        "ok": True,
        "referred_by_user_id": referrer_id,
        "referral_code": referral_code_for_user(referrer_id),
    }


def grant_referrer_on_pack_purchase(
    *,
    buyer_user_id: int,
    source_kind: str,
    source_key: str,
) -> dict[str, Any]:
    """
    If buyer has referred_by and has never triggered a pack-referral reward,
    credit referrer with +3 bonus free questions.
    """
    from database import db
    from models import PackReferralReward, User

    buyer_id = int(buyer_user_id)
    kind = (source_kind or "").strip().lower()[:20]
    key = (source_key or "").strip()[:80]
    if not kind or not key:
        return {"ok": False, "error": "bad_source"}

    # One reward lifetime per referred buyer.
    prior = (
        PackReferralReward.query.filter_by(buyer_user_id=buyer_id).first()
    )
    if prior:
        return {"ok": True, "already": True, "reward_id": prior.id}

    buyer = db.session.get(User, buyer_id)
    if not buyer:
        return {"ok": False, "error": "buyer_missing"}
    referrer_id = getattr(buyer, "referred_by_user_id", None)
    if not referrer_id:
        return {"ok": True, "skipped": True, "reason": "no_referrer"}
    referrer_id = int(referrer_id)
    if referrer_id == buyer_id:
        return {"ok": False, "error": "self_referral"}

    referrer = db.session.get(User, referrer_id)
    if not referrer:
        return {"ok": False, "error": "referrer_missing"}

    row = PackReferralReward(
        referrer_user_id=referrer_id,
        buyer_user_id=buyer_id,
        source_kind=kind,
        source_key=key,
        questions_granted=BONUS_QUESTIONS,
    )
    try:
        db.session.add(row)
        db.session.flush()
    except Exception:
        db.session.rollback()
        # Race: another grant won
        prior2 = PackReferralReward.query.filter_by(buyer_user_id=buyer_id).first()
        if prior2:
            return {"ok": True, "already": True, "reward_id": prior2.id}
        raise

    db.session.execute(
        update(User)
        .where(User.id == referrer_id)
        .values(
            ask_v1_bonus_questions=User.ask_v1_bonus_questions + BONUS_QUESTIONS,
        )
    )
    db.session.commit()
    return {
        "ok": True,
        "granted": True,
        "referrer_user_id": referrer_id,
        "questions": BONUS_QUESTIONS,
        "source_kind": kind,
        "source_key": key,
    }


def mine_payload(user) -> dict[str, Any]:
    from models import PackReferralReward

    code = referral_code_for_user(int(user.id))
    rewards = (
        PackReferralReward.query.filter_by(referrer_user_id=int(user.id))
        .order_by(PackReferralReward.created_at.desc())
        .limit(20)
        .all()
    )
    earned_q = sum(int(r.questions_granted or 0) for r in rewards)
    share = (
        f"Join Cosmic Lens and use my code {code} when you buy any Cosmic Pack (V1 or V3).\n"
        f"Code: {code}"
    )
    return {
        "ok": True,
        "referral_code": code,
        "share_message": share,
        "reward_per_referral": BONUS_QUESTIONS,
        "friends_converted": len(rewards),
        "questions_earned": earned_q,
        "bonus_questions_left": int(getattr(user, "ask_v1_bonus_questions", 0) or 0),
        "how_it_works": [
            "Share your referral code",
            "Your friend enters the code on Cosmic Packs and buys any V1 or V3 pack",
            "You get 3 free Ask questions (once per friend)",
        ],
    }
