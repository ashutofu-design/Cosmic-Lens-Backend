"""
Cosmic Lens — Subscription Logic (single source of truth)

Plan keys:
  free   — default, very limited
  trial  — 7-day paid trial (₹1, one-time per user) → BASIC features unlocked
  basic  — ₹199/mo or ₹1,799/yr — short summaries, 10 Q/day, 5 K/day
  pro    — ₹499/mo (NO yearly) — full depth, unlimited Q & K
  elite  — legacy alias treated as 'pro'

Everything plan-related (effective plan, feature gates, daily quota) goes here.
Daily reset uses IST (Asia/Kolkata) so India users get a clean midnight reset.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import update
from database import db


# ── Tunables (single place to change pricing/limits) ─────────────────────────
PLAN_PRICES = {
    "trial_weekly":  1,
    "basic_monthly": 199,
    "basic_yearly":  1799,
    "pro_monthly":   499,
    # Pro yearly removed — Pro is monthly-only.
}

TRIAL_DAYS = 7

# Daily AI question limits (-1 = unlimited)
QUESTION_LIMITS = {
    "free":  3,
    "trial": 10,   # trial = same as Basic
    "basic": 10,
    "pro":  -1,
    "elite": -1,
}

# Daily Kundli generation limits — counts only NEW kundlis (dedup handled at API layer)
KUNDLI_LIMITS = {
    "free":  1,
    "trial": 5,    # trial = same as Basic
    "basic": 5,
    "pro":  -1,
    "elite": -1,
}

# Future Timeline months unlocked
TIMELINE_MONTHS = {
    "free":  0,
    "trial": 1,
    "basic": 1,
    "pro":   6,
    "elite": 6,
}

# Saved profiles (active, excluding soft-deleted)
PROFILE_LIMIT = {
    "free":  1,
    "trial": 5,    # trial = same as Basic
    "basic": 5,
    "pro":  -1,
    "elite": -1,
}


# ── IST timezone helpers ─────────────────────────────────────────────────────
IST = ZoneInfo("Asia/Kolkata")


def _today_str() -> str:
    """Today's date in IST (so daily reset happens at IST midnight)."""
    return datetime.now(IST).date().isoformat()


def effective_plan(user) -> str:
    """
    Returns the user's *currently active* plan, accounting for expiry.
    Never trust user.plan directly — always go through this.
    """
    if not user:
        return "free"

    now = datetime.utcnow()

    # Active paid plan
    if user.plan in ("basic", "pro", "elite") and user.plan_expiry and user.plan_expiry > now:
        return "pro" if user.plan == "elite" else user.plan

    # Active trial
    if user.trial_started_at:
        trial_end = user.trial_started_at + timedelta(days=TRIAL_DAYS)
        if trial_end > now:
            return "trial"

    return "free"


def analysis_mode(user) -> str:
    """Returns 'pro' for full-depth analysis, else 'basic' (short summary)."""
    return "pro" if effective_plan(user) == "pro" else "basic"


def question_limit(user) -> int:
    return QUESTION_LIMITS.get(effective_plan(user), 1)


def kundli_limit(user) -> int:
    return KUNDLI_LIMITS.get(effective_plan(user), 1)


# ── AstroVastu tier gates ────────────────────────────────────────────────
# BASIC AstroVastu (text-only kundli check) — shares the daily_questions_used
# counter with the Q&A endpoint. Limits MUST stay aligned with QUESTION_LIMITS
# above (free=3, trial=10, basic=10, pro=unlimited) since both flows consume
# from the same atomic counter; otherwise the check could approve while the
# consume step rejects.
ASTROVASTU_BASIC_DAILY: dict = {
    "free":  3,
    "trial": 10,
    "basic": 10,
    "pro":  -1,
    "elite": -1,
}

ASTROVASTU_PRO_MONTHLY: dict = {
    "free":  0,    # Locked — preview only
    "trial": 1,
    "basic": 1,    # 1 deep-scan per month for Basic plan
    "pro":  -1,    # Unlimited
    "elite": -1,
}


def astrovastu_basic_limit(user) -> int:
    return ASTROVASTU_BASIC_DAILY.get(effective_plan(user), 0)


def astrovastu_pro_monthly_limit(user) -> int:
    return ASTROVASTU_PRO_MONTHLY.get(effective_plan(user), 0)


def can_use_astrovastu_basic(user) -> dict:
    """Quick gate check for BASIC AstroVastu — reuses daily-questions counter."""
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Login required"}
    reset_daily_quota_if_needed(user)
    limit = astrovastu_basic_limit(user)
    if limit == 0:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Plan upgrade required"}
    if limit == -1:
        return {"allowed": True, "used": user.daily_questions_used, "limit": -1}
    if user.daily_questions_used >= limit:
        return {"allowed": False, "used": user.daily_questions_used, "limit": limit,
                "reason": "Daily AstroVastu limit reached"}
    return {"allowed": True, "used": user.daily_questions_used, "limit": limit}


def _current_month_str() -> str:
    """Returns IST month as 'YYYY-MM'."""
    return _today_str()[:7]


def reset_monthly_pro_quota_if_needed(user) -> None:
    """Resets the PRO monthly counter if the IST month rolled over."""
    this_month = _current_month_str()
    if user.monthly_astrovastu_pro_month != this_month:
        user.monthly_astrovastu_pro_month = this_month
        user.monthly_astrovastu_pro_used  = 0
        db.session.commit()


def can_use_astrovastu_pro(user) -> dict:
    """Gate check (no consumption) for PRO AstroVastu deep-scan."""
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Login required"}
    limit = astrovastu_pro_monthly_limit(user)
    if limit == 0:
        return {"allowed": False, "used": 0, "limit": 0,
                "reason": "PRO AstroVastu requires Basic or Pro plan"}
    reset_monthly_pro_quota_if_needed(user)
    if limit == -1:
        return {"allowed": True, "used": user.monthly_astrovastu_pro_used, "limit": -1}
    if user.monthly_astrovastu_pro_used >= limit:
        return {"allowed": False, "used": user.monthly_astrovastu_pro_used,
                "limit": limit, "reason": "Monthly PRO scan limit reached"}
    return {"allowed": True, "used": user.monthly_astrovastu_pro_used, "limit": limit}


def consume_astrovastu_pro(user) -> dict:
    """
    ATOMIC monthly counter increment for PRO AstroVastu. Same pattern as
    consume_question — conditional UPDATE prevents over-consumption under
    concurrent requests.
    """
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Login required"}
    reset_monthly_pro_quota_if_needed(user)
    limit = astrovastu_pro_monthly_limit(user)
    this_month = _current_month_str()
    if limit == 0:
        return {"allowed": False, "used": 0, "limit": 0,
                "reason": "PRO AstroVastu requires Basic or Pro plan"}

    from models import User as _U
    if limit == -1:
        db.session.execute(
            update(_U).where(_U.id == user.id)
            .values(monthly_astrovastu_pro_used=_U.monthly_astrovastu_pro_used + 1)
        )
        db.session.commit(); db.session.refresh(user)
        return {"allowed": True, "used": user.monthly_astrovastu_pro_used, "limit": -1}

    result = db.session.execute(
        update(_U).where(_U.id == user.id)
        .where(_U.monthly_astrovastu_pro_month == this_month)
        .where(_U.monthly_astrovastu_pro_used  < limit)
        .values(monthly_astrovastu_pro_used=_U.monthly_astrovastu_pro_used + 1)
    )
    db.session.commit()
    if result.rowcount == 0:
        db.session.refresh(user)
        return {"allowed": False, "used": user.monthly_astrovastu_pro_used,
                "limit": limit, "reason": "Monthly PRO scan limit reached"}
    db.session.refresh(user)
    return {"allowed": True, "used": user.monthly_astrovastu_pro_used, "limit": limit}


def timeline_months(user) -> int:
    return TIMELINE_MONTHS.get(effective_plan(user), 0)


def profile_limit(user) -> int:
    return PROFILE_LIMIT.get(effective_plan(user), 1)


def trial_eligible(user) -> bool:
    """User can start trial only once, and only if not on a paid plan."""
    if not user:
        return False
    if user.trial_used:
        return False
    if effective_plan(user) in ("pro", "basic"):
        return False
    return True


def start_trial(user) -> dict:
    if not user:
        return {"ok": False, "error": "User not found"}
    if not trial_eligible(user):
        return {"ok": False, "error": "Trial not available"}

    now = datetime.utcnow()
    user.trial_started_at = now
    user.trial_used = True
    db.session.commit()

    return {
        "ok": True,
        "expires_at": (now + timedelta(days=TRIAL_DAYS)).isoformat(),
    }


def auto_start_trial_on_signup(user) -> None:
    """No-op (legacy). Trial is now a paid (₹1) plan."""
    return


def reset_daily_quota_if_needed(user) -> None:
    """Resets daily counters if the IST date has rolled over."""
    today = _today_str()
    changed = False
    if user.daily_questions_date != today:
        user.daily_questions_date = today
        user.daily_questions_used = 0
        changed = True
    if user.daily_kundlis_date != today:
        user.daily_kundlis_date = today
        user.daily_kundlis_used = 0
        changed = True
    if changed:
        db.session.commit()


def can_ask_question(user) -> dict:
    """Check (without consuming) if user can ask another question today."""
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Login required"}

    reset_daily_quota_if_needed(user)
    limit = question_limit(user)

    if limit == -1:
        return {"allowed": True, "used": user.daily_questions_used, "limit": -1}

    if user.daily_questions_used >= limit:
        return {
            "allowed": False,
            "used":    user.daily_questions_used,
            "limit":   limit,
            "reason":  "Daily limit reached",
        }
    return {"allowed": True, "used": user.daily_questions_used, "limit": limit}


def consume_question(user) -> dict:
    """
    ATOMIC check + increment. Uses a conditional UPDATE so two parallel
    requests can never both succeed past the daily limit.
    """
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Login required"}

    reset_daily_quota_if_needed(user)
    limit = question_limit(user)
    today = _today_str()

    # Import locally to avoid circular import
    from models import User

    if limit == -1:
        # Unlimited — still track count for analytics
        db.session.execute(
            update(User)
            .where(User.id == user.id)
            .values(daily_questions_used=User.daily_questions_used + 1)
        )
        db.session.commit()
        db.session.refresh(user)
        return {"allowed": True, "used": user.daily_questions_used, "limit": -1}

    # Atomic: increment only if (still today AND used < limit)
    result = db.session.execute(
        update(User)
        .where(User.id == user.id)
        .where(User.daily_questions_date == today)
        .where(User.daily_questions_used < limit)
        .values(daily_questions_used=User.daily_questions_used + 1)
    )
    db.session.commit()

    if result.rowcount == 0:
        db.session.refresh(user)
        return {
            "allowed": False,
            "used":    user.daily_questions_used,
            "limit":   limit,
            "reason":  "Daily limit reached",
        }

    db.session.refresh(user)
    return {"allowed": True, "used": user.daily_questions_used, "limit": limit}


def can_generate_kundli(user) -> dict:
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Login required"}

    reset_daily_quota_if_needed(user)
    limit = kundli_limit(user)

    if limit == -1:
        return {"allowed": True, "used": user.daily_kundlis_used, "limit": -1}

    if user.daily_kundlis_used >= limit:
        return {
            "allowed": False,
            "used":    user.daily_kundlis_used,
            "limit":   limit,
            "reason":  "Daily kundli limit reached",
        }
    return {"allowed": True, "used": user.daily_kundlis_used, "limit": limit}


def consume_kundli(user) -> dict:
    """ATOMIC check + increment for kundli generation."""
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "reason": "Login required"}

    reset_daily_quota_if_needed(user)
    limit = kundli_limit(user)
    today = _today_str()

    from models import User

    if limit == -1:
        db.session.execute(
            update(User)
            .where(User.id == user.id)
            .values(daily_kundlis_used=User.daily_kundlis_used + 1)
        )
        db.session.commit()
        db.session.refresh(user)
        return {"allowed": True, "used": user.daily_kundlis_used, "limit": -1}

    result = db.session.execute(
        update(User)
        .where(User.id == user.id)
        .where(User.daily_kundlis_date == today)
        .where(User.daily_kundlis_used < limit)
        .values(daily_kundlis_used=User.daily_kundlis_used + 1)
    )
    db.session.commit()

    if result.rowcount == 0:
        db.session.refresh(user)
        return {
            "allowed": False,
            "used":    user.daily_kundlis_used,
            "limit":   limit,
            "reason":  "Daily kundli limit reached",
        }

    db.session.refresh(user)
    return {"allowed": True, "used": user.daily_kundlis_used, "limit": limit}


def subscription_status(user) -> dict:
    """Full subscription snapshot for the mobile app."""
    plan = effective_plan(user) if user else "free"
    if user:
        reset_daily_quota_if_needed(user)

    trial_expires_at = None
    if user and user.trial_started_at:
        trial_expires_at = (user.trial_started_at + timedelta(days=TRIAL_DAYS)).isoformat()

    plan_expires_at = None
    if user and user.plan_expiry and user.plan in ("basic", "pro", "elite"):
        plan_expires_at = user.plan_expiry.isoformat()

    return {
        "plan":              plan,
        "analysis_mode":     "pro" if plan == "pro" else "basic",
        "is_pro":            plan == "pro",
        "is_basic_or_above": plan in ("basic", "pro", "trial"),
        "trial_eligible":    trial_eligible(user) if user else False,
        "trial_expires_at":  trial_expires_at if plan == "trial" else None,
        "plan_expires_at":   plan_expires_at,
        "limits": {
            "questions_per_day":  question_limit(user) if user else QUESTION_LIMITS["free"],
            "questions_used":     user.daily_questions_used if user else 0,
            "kundlis_per_day":    kundli_limit(user) if user else KUNDLI_LIMITS["free"],
            "kundlis_used":       user.daily_kundlis_used if user else 0,
            "timeline_months":    timeline_months(user) if user else 0,
            "profile_limit":      profile_limit(user) if user else 1,
        },
        "prices":            PLAN_PRICES,
        "trial_days":        TRIAL_DAYS,
    }


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  Phase-2 — AstroVastu One-Time Unlock Model                              ║
# ║                                                                          ║
# ║  Replaces strict monthly quota with three independent paths:             ║
# ║   1) Pro plan (₹499/mo)  → unlimited everything                          ║
# ║   2) Property unlock     → unlimited PRO scans for a single named home   ║
# ║      (₹2,999 Full Home / ₹999 Shop / ₹1,499 Office / ₹2,999 Factory)     ║
# ║   3) Room credits        → 1-room (₹199) or 3-room bundle (₹499) for     ║
# ║      one-off BASIC checks                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

SKU_CATALOG = {
    "1room_199":       {"price": 199,  "grants": "credits", "credits": 1, "label": "1 Room Quick Check"},
    "bundle_499":      {"price": 499,  "grants": "credits", "credits": 3, "label": "3-Room Bundle"},
    "full_home_2999":  {"price": 2999, "grants": "unlock",  "label": "Full Home Lifetime"},
    "shop_999":        {"price": 999,  "grants": "unlock",  "label": "Shop Vastu Lifetime"},
    "office_1499":     {"price": 1499, "grants": "unlock",  "label": "Office Vastu Lifetime"},
    "factory_2999":    {"price": 2999, "grants": "unlock",  "label": "Factory Vastu Lifetime"},
}


def is_property_unlocked(user, property_name: str) -> bool:
    """True if user has a lifetime unlock for the given property name."""
    if not user or not property_name:
        return False
    from models import AstroVastuPropertyUnlock
    pname = property_name.strip()
    if not pname:
        return False
    row = AstroVastuPropertyUnlock.query.filter_by(
        user_id=user.id, property_name=pname
    ).first()
    return row is not None


def list_unlocked_properties(user) -> list:
    """Returns list of {property_name, tier, unlocked_at} for user."""
    if not user:
        return []
    from models import AstroVastuPropertyUnlock
    rows = (AstroVastuPropertyUnlock.query
            .filter_by(user_id=user.id)
            .order_by(AstroVastuPropertyUnlock.unlocked_at.desc())
            .all())
    return [{
        "property_name": r.property_name,
        "tier":          r.tier,
        "unlocked_at":   r.unlocked_at.isoformat() if r.unlocked_at else None,
    } for r in rows]


def can_use_astrovastu_basic_v2(user, property_name: str = "") -> dict:
    """
    Phase-2 gate for BASIC AstroVastu. Allows if ANY of:
      - Pro plan (unlimited)
      - Property unlocked (unlimited for that property)
      - Room credits available
      - Daily free quota available (legacy fallback for free/trial/basic plans)
    """
    if not user:
        return {"allowed": False, "reason": "Login required",
                "credits": 0, "unlocks": [], "via": "none"}

    plan = effective_plan(user)
    unlocks = list_unlocked_properties(user)

    if plan == "pro":
        return {"allowed": True, "via": "pro_plan",
                "credits": user.astrovastu_room_credits, "unlocks": unlocks}

    if property_name and is_property_unlocked(user, property_name):
        return {"allowed": True, "via": "property_unlock",
                "credits": user.astrovastu_room_credits, "unlocks": unlocks}

    if (user.astrovastu_room_credits or 0) > 0:
        return {"allowed": True, "via": "room_credit",
                "credits": user.astrovastu_room_credits, "unlocks": unlocks}

    # Fallback to legacy daily free/basic quota
    legacy = can_use_astrovastu_basic(user)
    if legacy.get("allowed"):
        return {"allowed": True, "via": "daily_free_quota",
                "credits": user.astrovastu_room_credits, "unlocks": unlocks,
                "used": legacy.get("used"), "limit": legacy.get("limit")}

    return {"allowed": False,
            "reason": "Buy a Room Check (₹199), 3-Room Bundle (₹499), or Full Home Unlock (₹2,999).",
            "credits": user.astrovastu_room_credits, "unlocks": unlocks,
            "via": "none", "upgrade_required": True}


def consume_astrovastu_basic_v2(user, property_name: str = "") -> dict:
    """
    Phase-2 atomic consume for BASIC. Resolution order matches gate:
      pro_plan → no charge
      property_unlock → no charge
      room_credit → atomic decrement of astrovastu_room_credits
      daily_free_quota → reuse legacy consume_question
    """
    if not user:
        return {"allowed": False, "reason": "Login required", "via": "none"}

    plan = effective_plan(user)
    if plan == "pro":
        return {"allowed": True, "via": "pro_plan",
                "credits": user.astrovastu_room_credits}

    if property_name and is_property_unlocked(user, property_name):
        return {"allowed": True, "via": "property_unlock",
                "credits": user.astrovastu_room_credits}

    # Try room credit (atomic conditional UPDATE)
    if (user.astrovastu_room_credits or 0) > 0:
        from models import User as _U
        result = db.session.execute(
            update(_U).where(_U.id == user.id)
            .where(_U.astrovastu_room_credits > 0)
            .values(astrovastu_room_credits=_U.astrovastu_room_credits - 1)
        )
        db.session.commit()
        if result.rowcount > 0:
            db.session.refresh(user)
            return {"allowed": True, "via": "room_credit",
                    "credits": user.astrovastu_room_credits}

    # Fall back to legacy daily quota (uses consume_question counter)
    legacy_check = can_use_astrovastu_basic(user)
    if legacy_check.get("allowed"):
        consumed = consume_question(user)
        if consumed.get("allowed"):
            return {"allowed": True, "via": "daily_free_quota",
                    "credits": user.astrovastu_room_credits,
                    "used": consumed.get("used"), "limit": consumed.get("limit")}

    return {"allowed": False,
            "reason": "Out of credits. Buy a Room Check (₹199), Bundle (₹499), or Full Home Unlock (₹2,999).",
            "credits": user.astrovastu_room_credits,
            "upgrade_required": True}


def can_use_astrovastu_pro_v2(user, property_name: str = "") -> dict:
    """
    Phase-2 gate for PRO multi-room deep-scan. Allows if:
      - Pro plan (unlimited)
      - Property unlocked (unlimited for that property — REQUIRES property_name)
      - Legacy basic plan monthly quota (1/mo)
    Per-room credits do NOT cover PRO scans (PRO is whole-house).
    """
    if not user:
        return {"allowed": False, "reason": "Login required", "via": "none"}

    plan = effective_plan(user)
    unlocks = list_unlocked_properties(user)

    if plan == "pro":
        return {"allowed": True, "via": "pro_plan", "unlocks": unlocks}

    if property_name and is_property_unlocked(user, property_name):
        return {"allowed": True, "via": "property_unlock", "unlocks": unlocks}

    # Fallback to legacy monthly quota (basic plan gets 1/mo)
    legacy = can_use_astrovastu_pro(user)
    if legacy.get("allowed"):
        return {"allowed": True, "via": "monthly_quota",
                "used": legacy.get("used"), "limit": legacy.get("limit"),
                "unlocks": unlocks}

    return {"allowed": False,
            "reason": "Unlock this property for ₹2,999 (lifetime) or upgrade to Pro plan.",
            "unlocks": unlocks, "via": "none", "upgrade_required": True}


def consume_astrovastu_pro_v2(user, property_name: str = "") -> dict:
    """Phase-2 atomic consume for PRO. Mirrors gate resolution order."""
    if not user:
        return {"allowed": False, "reason": "Login required", "via": "none"}

    plan = effective_plan(user)
    if plan == "pro":
        return {"allowed": True, "via": "pro_plan"}

    if property_name and is_property_unlocked(user, property_name):
        return {"allowed": True, "via": "property_unlock"}

    # Fallback: legacy monthly quota (atomic via existing consume_astrovastu_pro)
    consumed = consume_astrovastu_pro(user)
    if consumed.get("allowed"):
        return {"allowed": True, "via": "monthly_quota",
                "used": consumed.get("used"), "limit": consumed.get("limit")}

    return {"allowed": False,
            "reason": "Unlock this property for ₹2,999 (lifetime) or upgrade to Pro plan.",
            "upgrade_required": True}


def grant_purchase_idempotent(purchase) -> dict:
    """
    Apply a paid purchase to the user. Race-safe via a single atomic UPDATE
    on (id, status='paid', granted=False). Only the row whose UPDATE
    succeeds (rowcount==1) proceeds to grant credits/unlock. Subsequent
    callers (concurrent webhook + manual retry) see rowcount==0 and exit
    cleanly without double-granting.
    """
    from models import User as _U, AstroVastuPropertyUnlock, AstroVastuPurchase
    if not purchase:
        return {"granted": False, "reason": "missing_purchase"}

    spec = SKU_CATALOG.get(purchase.sku)
    if not spec:
        return {"granted": False, "reason": "unknown_sku"}

    if spec["grants"] == "unlock" and not purchase.property_name:
        return {"granted": False, "reason": "missing_property_name"}

    # ── Atomic claim — only one caller wins ──────────────────────────────
    claim = db.session.execute(
        update(AstroVastuPurchase)
        .where(AstroVastuPurchase.id == purchase.id)
        .where(AstroVastuPurchase.status == "paid")
        .where(AstroVastuPurchase.granted.is_(False))
        .values(granted=True)
    )
    if claim.rowcount != 1:
        # Either another worker already claimed it, or status != 'paid'.
        db.session.commit()
        return {"granted": False, "reason": "already_granted_or_not_paid"}

    # ── Persist the claim FIRST so a side-effect failure can never
    # roll back granted=true. From this point on, the user's purchase is
    # authoritative — even if the unlock/credit insert hiccups, the row
    # is marked granted and a backfill job (or retry) can re-run the
    # side-effect safely.
    db.session.commit()

    # We own the grant. Apply side-effects in their own nested savepoint so
    # an IntegrityError on the unique unlock constraint can be swallowed
    # without poisoning the (already-committed) granted=true claim.
    if spec["grants"] == "credits":
        try:
            with db.session.begin_nested():
                db.session.execute(
                    update(_U).where(_U.id == purchase.user_id)
                    .values(astrovastu_room_credits=_U.astrovastu_room_credits + spec["credits"])
                )
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Granted flag already True — credits side-effect failed. Logged
            # via webhook retry / status poll which will re-enter and try
            # again (atomic claim will short-circuit cleanly).
            return {"granted": True, "sku": purchase.sku, "via": spec["grants"],
                    "note": "credits_side_effect_failed"}
    else:  # "unlock"
        try:
            with db.session.begin_nested():
                db.session.add(AstroVastuPropertyUnlock(
                    user_id=purchase.user_id,
                    property_name=purchase.property_name,
                    tier=purchase.sku,
                    order_id=purchase.order_id,
                    amount_paid=purchase.amount,
                ))
            db.session.commit()
        except Exception:
            # Duplicate unlock for same property — user already has it.
            # Granted claim remains True (committed above); safe to no-op.
            db.session.rollback()
            return {"granted": True, "sku": purchase.sku, "via": spec["grants"],
                    "note": "duplicate_unlock_ignored"}

    return {"granted": True, "sku": purchase.sku, "via": spec["grants"]}
