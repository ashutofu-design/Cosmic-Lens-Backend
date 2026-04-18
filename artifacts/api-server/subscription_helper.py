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
