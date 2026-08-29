"""Shared payment-bypass and production guards for billing modules."""

from __future__ import annotations

import os


def is_production() -> bool:
    if os.environ.get("PROD", "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    if os.environ.get("FLASK_ENV", "").strip().lower() == "production":
        return True
    return False


def dev_payment_bypass_enabled() -> bool:
    """Local/staging only — never honored when is_production()."""
    if is_production():
        return False
    return os.environ.get("DEV_PAYMENT_BYPASS", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def payment_bypass_from_env(*flag_names: str) -> bool:
    """True only in non-production when DEV_PAYMENT_BYPASS=1 and a product flag is set."""
    if not dev_payment_bypass_enabled():
        return False
    for name in flag_names:
        if os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on"):
            return True
    return False


def payment_required_flag(env_name: str, *, default: str = "1") -> bool:
    """Paywall switch for one product.

    Production is never allowed to turn a paywall off: the ``*_PAYMENT_REQUIRED``
    env vars exist so local and staging can exercise the flow without money.
    """
    if is_production():
        return True
    raw = os.environ.get(env_name)
    if raw is None or not str(raw).strip():
        raw = default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def free_mode_enabled(env_name: str) -> bool:
    """Give-it-away switch — always off in production."""
    if is_production():
        return False
    return os.environ.get(env_name, "").strip().lower() in ("1", "true", "yes", "on")


def env_bool(name: str, *, production_default: str, dev_default: str) -> bool:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        raw = production_default if is_production() else dev_default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")
