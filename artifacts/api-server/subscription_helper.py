"""
Cosmic Lens — Subscription Logic (single source of truth)

Plan keys:
  free   — default, very limited
  trial  — 7-day free trial (one-time per user) → BASIC features unlocked
  basic  — ₹199/mo or ₹1,799/yr — short summaries, 10 Q/day
  pro    — ₹399/mo or ₹2,999/yr — full depth, unlimited Q
  elite  — legacy alias treated as 'pro'

Everything plan-related (effective plan, feature gates, daily quota) goes here.
"""

from datetime import datetime, timedelta, date
from database import db


# ── Tunables (single place to change pricing/limits) ─────────────────────────
PLAN_PRICES = {
    "basic_monthly": 199,
    "basic_yearly":  1799,
    "pro_monthly":   399,
    "pro_yearly":    2999,
}

TRIAL_DAYS = 7

# Daily AI question limits
QUESTION_LIMITS = {
    "free":  3,    # new users get a real taste — 3 questions/day
    "trial": 5,    # trial = basic features with slightly higher quota
    "basic": 10,
    "pro":  -1,    # unlimited
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

# Saved profiles
PROFILE_LIMIT = {
    "free":  1,
    "trial": 3,
    "basic": 5,
    "pro":  -1,
    "elite": -1,
}


def _today_str() -> str:
    return date.today().isoformat()


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
    """
    Returns 'pro' for full-depth analysis, else 'basic' (short summary).
    Use this in API responses to trim deep fields for non-pro users.
    """
    return "pro" if effective_plan(user) == "pro" else "basic"


def question_limit(user) -> int:
    """Daily AI question limit. -1 = unlimited."""
    return QUESTION_LIMITS.get(effective_plan(user), 1)


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
    """
    Begins a 7-day trial. Returns {ok, error?, expires_at?}.
    Idempotent guard against double-starting.
    """
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
    """Called from signup endpoints — gives every new user a free trial."""
    if user and not user.trial_used:
        user.trial_started_at = datetime.utcnow()
        user.trial_used = True
        # commit handled by caller


def reset_daily_quota_if_needed(user) -> None:
    today = _today_str()
    if user.daily_questions_date != today:
        user.daily_questions_date = today
        user.daily_questions_used = 0


def can_ask_question(user) -> dict:
    """
    Check (without consuming) if user can ask another question today.
    Returns {allowed, used, limit, reason?}.
    """
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
    return {
        "allowed": True,
        "used":    user.daily_questions_used,
        "limit":   limit,
    }


def consume_question(user) -> dict:
    """
    Atomically check + increment daily question counter.
    Returns {allowed, used, limit, reason?}.
    """
    check = can_ask_question(user)
    if not check["allowed"]:
        return check

    user.daily_questions_used += 1
    db.session.commit()

    return {
        "allowed": True,
        "used":    user.daily_questions_used,
        "limit":   check["limit"],
    }


def subscription_status(user) -> dict:
    """
    Full subscription snapshot for the mobile app.
    Returned by /api/subscription/status.
    """
    plan = effective_plan(user) if user else "free"
    reset_daily_quota_if_needed(user) if user else None

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
            "timeline_months":    timeline_months(user) if user else 0,
            "profile_limit":      profile_limit(user) if user else 1,
        },
        "prices":            PLAN_PRICES,
        "trial_days":        TRIAL_DAYS,
    }
