"""Refuse to boot production when critical security configuration is missing."""

from __future__ import annotations

import os
import sys


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def is_production() -> bool:
    if _truthy("PROD"):
        return True
    return os.environ.get("FLASK_ENV", "").strip().lower() == "production"


def _require_nonempty(name: str, errors: list[str], *, min_len: int = 1) -> None:
    val = os.environ.get(name, "").strip()
    if len(val) < min_len:
        errors.append(f"{name} is required in production")


# Placeholder values that ship in docs/templates — refuse to boot with them.
_WEAK_VALUES = frozenset(
    {
        "admin",
        "administrator",
        "root",
        "test",
        "demo",
        "password",
        "passw0rd",
        "admin123",
        "changeme",
        "change-me",
        "secret",
        "cosmiclens",
        "cosmic-lens",
        "1234",
        "12345",
        "123456",
        "0000",
        "000000",
        "111111",
        "replace-me",
        "your-secret-here",
        "xxx",
    }
)


def _reject_weak(name: str, errors: list[str]) -> None:
    val = os.environ.get(name, "").strip()
    if not val:
        return
    if val.lower() in _WEAK_VALUES:
        errors.append(f"{name} uses a default/placeholder value — set a unique secret")
    elif len(set(val)) <= 2:
        errors.append(f"{name} is not sufficiently random")


def cors_origin_errors() -> list[str]:
    """CORS_ORIGINS must be an explicit HTTPS allowlist in production.

    Empty is fine — flask_app then falls back to its hardcoded production
    allowlist. A wildcard or plain-HTTP entry is not.
    """
    if not is_production():
        return []
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        return []
    errors: list[str] = []
    for origin in (o.strip() for o in raw.split(",")):
        if not origin:
            continue
        if origin == "*":
            errors.append("CORS_ORIGINS must not contain '*' in production")
        elif not origin.lower().startswith("https://"):
            errors.append(
                f"CORS_ORIGINS entry '{origin}' must use https:// in production"
            )
    return errors


def validate_production_config() -> list[str]:
    if not is_production():
        return []
    errors: list[str] = []

    _require_nonempty("ADMIN_SECRET", errors, min_len=32)
    _require_nonempty("ADMIN_LOGIN_USER", errors)
    _require_nonempty("ADMIN_LOGIN_PASS", errors, min_len=12)
    _require_nonempty("ADMIN_LOGIN_MPIN", errors, min_len=4)
    _require_nonempty("SESSION_SECRET", errors, min_len=32)
    _reject_weak("ADMIN_SECRET", errors)
    _reject_weak("SESSION_SECRET", errors)
    _reject_weak("ADMIN_LOGIN_USER", errors)
    _reject_weak("ADMIN_LOGIN_PASS", errors)
    _reject_weak("ADMIN_LOGIN_MPIN", errors)
    _reject_weak("ADMIN_ENROLL_CODE", errors)
    _require_nonempty("DATABASE_URL", errors)
    _require_nonempty("RAZORPAY_KEY_ID", errors)
    _require_nonempty("RAZORPAY_KEY_SECRET", errors)
    _require_nonempty("RAZORPAY_WEBHOOK_SECRET", errors)

    if _truthy("ADMIN_NO_AUTH"):
        errors.append("ADMIN_NO_AUTH must not be enabled in production")
    if _truthy("ADMIN_SECURITY_RELAXED"):
        errors.append("ADMIN_SECURITY_RELAXED must not be enabled in production")
    if _truthy("ADMIN_ALLOW_ALL_DEVICES"):
        errors.append("ADMIN_ALLOW_ALL_DEVICES must be 0 in production")
    if not os.environ.get("ADMIN_ENROLL_CODE", "").strip():
        errors.append("ADMIN_ENROLL_CODE is required in production")

    bypass_flags = (
        "COUPLE_REPORT_PAYMENT_BYPASS",
        "DEV_PAYMENT_BYPASS",
        "CAREER_PAYMENT_BYPASS",
        "ASK_V1_PAYMENT_BYPASS",
        "ASK_V3_PAYMENT_BYPASS",
        "NUMEROLOGY_REPORT_PAYMENT_BYPASS",
        "PALMISTRY_PAYMENT_BYPASS",
        "FACE_READING_PAYMENT_BYPASS",
        "BIRTH_TIME_RECTIFICATION_PAYMENT_BYPASS",
        "BUSINESS_VASTU_PAYMENT_BYPASS",
        "ROOM_UPLOAD_PAYMENT_BYPASS",
    )
    for flag in bypass_flags:
        if _truthy(flag):
            errors.append(f"{flag} must not be enabled in production")

    paywall_flags = (
        "COUPLE_REPORT_PAYMENT_REQUIRED",
        "NUMEROLOGY_REPORT_PAYMENT_REQUIRED",
        "PALMISTRY_PAYMENT_REQUIRED",
        "FACE_READING_PAYMENT_REQUIRED",
        "BIRTH_TIME_RECTIFICATION_PAYMENT_REQUIRED",
        "BUSINESS_VASTU_PAYMENT_REQUIRED",
        "CAREER_PAYMENT_REQUIRED",
    )
    for flag in paywall_flags:
        raw = os.environ.get(flag)
        if raw is not None and raw.strip() and not _truthy(flag):
            errors.append(f"{flag} must not be disabled in production")

    if _truthy("LOVE_REALITY_PRO_FREE"):
        errors.append("LOVE_REALITY_PRO_FREE must be 0 in production")

    if _truthy("ASTROVASTU_DEV_GRANT_ENABLED"):
        errors.append("ASTROVASTU_DEV_GRANT_ENABLED must not be enabled in production")
    if _truthy("ASK_QUOTA_BYPASS"):
        errors.append("ASK_QUOTA_BYPASS must be 0 in production")
    if _truthy("KUNDLI_QUOTA_BYPASS"):
        errors.append("KUNDLI_QUOTA_BYPASS must be 0 in production")
    if _truthy("HEALTH_STATIC_BYPASS"):
        errors.append("HEALTH_STATIC_BYPASS must be 0 in production")
    if _truthy("ASTROVASTU_DEBUG_ERRORS"):
        errors.append("ASTROVASTU_DEBUG_ERRORS must be 0 in production")

    errors.extend(cors_origin_errors())

    if _truthy("PLAY_INTEGRITY_REQUIRED"):
        has_creds = bool(
            os.environ.get("PLAY_INTEGRITY_SERVICE_ACCOUNT_JSON", "").strip()
            or os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
            or os.environ.get("PLAY_INTEGRITY_CREDENTIALS_PATH", "").strip()
        )
        if not has_creds:
            errors.append(
                "PLAY_INTEGRITY_REQUIRED=1 but no Play Integrity service account configured"
            )

    if _truthy("APP_CHECK_REQUIRED") and not (
        os.environ.get("FIREBASE_PROJECT_NUMBER", "").strip()
        or os.environ.get("APP_CHECK_PROJECT_NUMBER", "").strip()
    ):
        errors.append(
            "APP_CHECK_REQUIRED=1 but FIREBASE_PROJECT_NUMBER is not configured"
        )

    # Shared rate-limit storage: without it every gunicorn worker keeps its own
    # counters, so the effective limit is silently multiplied by worker count.
    if not (
        os.environ.get("RATELIMIT_STORAGE_URI", "").strip()
        or os.environ.get("REDIS_URL", "").strip()
    ):
        errors.append(
            "REDIS_URL (or RATELIMIT_STORAGE_URI) is required in production "
            "so rate limits are shared across workers"
        )

    if _truthy("ALLOW_HTTP_API"):
        errors.append("ALLOW_HTTP_API must not be enabled in production")

    # Telegram webhook mode accepts order-fulfilment updates — it needs its own
    # unguessable path secret, and polling mode needs none.
    if os.environ.get("TELEGRAM_USE_POLLING", "").strip() == "0":
        _require_nonempty("TELEGRAM_WEBHOOK_SECRET", errors, min_len=24)
        _reject_weak("TELEGRAM_WEBHOOK_SECRET", errors)

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url.startswith("sqlite"):
        errors.append("DATABASE_URL must not be SQLite in production")

    return errors


def enforce_production_config() -> None:
    if not is_production():
        return
    errors = validate_production_config()
    if not errors:
        return
    msg = "Production startup blocked — fix security configuration:\n" + "\n".join(
        f"  - {e}" for e in errors
    )
    print(msg, file=sys.stderr, flush=True)
    raise SystemExit(1)
