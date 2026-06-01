"""
Token budget engine — per-user, per-report, tier caps, AI downgrade routing.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from . import face_cache as _fc
from . import redis_manager as _rm
from . import redis_codec as _codec

log = logging.getLogger(__name__)

_PREFIX = (os.environ.get("FACE_REDIS_PREFIX") or "face").strip().rstrip(":")


class AIMode(str, Enum):
    """Resolved narration strategy for one report build."""
    FULL = "full"              # Pass A (canonical) + Pass B (4o)
    MINI_ONLY = "mini_only"    # Pass A / localize only — no 4o
    LOCALIZE_ONLY = "localize_only"  # Canonical EN → target lang mini
    TEMPLATE_ONLY = "template_only"  # No OpenAI


@dataclass
class BudgetSnapshot:
    tier: str
    mode: AIMode
    user_daily_usd: float
    report_reserved_usd: float
    global_daily_usd: float
    reason: str


def _k(*parts: str) -> str:
    return f"{_PREFIX}:" + ":".join(str(p) for p in parts if p)


def user_tier(user_id: Optional[int], plan: Optional[str] = None) -> str:
    """Map user/plan → budget tier."""
    if plan:
        p = plan.strip().lower()
        if p in ("elite", "pro", "premium"):
            return p
    if user_id and int(user_id) > 0:
        return os.environ.get("FACE_DEFAULT_USER_TIER", "standard")
    return "anonymous"


def tier_limits(tier: str) -> Dict[str, float]:
    """USD caps per tier (daily user / per-report)."""
    defaults = {
        "anonymous": {"daily": 0.15, "report": 0.08, "pass_b": 0.04},
        "standard": {"daily": 2.0, "report": 0.35, "pass_b": 0.12},
        "pro": {"daily": 5.0, "report": 0.60, "pass_b": 0.25},
        "premium": {"daily": 8.0, "report": 0.90, "pass_b": 0.40},
        "elite": {"daily": 15.0, "report": 1.20, "pass_b": 0.55},
    }
    tier = tier if tier in defaults else "standard"
    out = dict(defaults[tier])
    out["daily"] = float(
        os.environ.get(f"FACE_TIER_{tier.upper()}_DAILY_USD", str(out["daily"]))
    )
    out["report"] = float(
        os.environ.get(f"FACE_TIER_{tier.upper()}_REPORT_USD", str(out["report"]))
    )
    return out


def _report_spend_key(analysis_id: str) -> str:
    return _k("token", "report", analysis_id)


def get_report_spend(analysis_id: str) -> float:
    raw = _rm.get_raw(_report_spend_key(analysis_id))
    return float(_codec.loads(raw) or 0) if raw else 0.0


def add_report_spend(analysis_id: str, usd: float) -> None:
    if usd <= 0 or not analysis_id:
        return
    cur = get_report_spend(analysis_id)
    _rm.set_raw(
        _report_spend_key(analysis_id),
        _codec.dumps(round(cur + usd, 6)),
        int(os.environ.get("FACE_ANALYSIS_TTL", str(24 * 3600))),
    )


def _queue_overloaded() -> bool:
    if (os.environ.get("FACE_AI_DOWNGRADE_QUEUE") or "").strip().lower() in (
        "1", "true", "yes",
    ):
        return True
    try:
        from celery_app import celery_app

        insp = celery_app.control.inspect(timeout=1.0)
        active = insp.active() or {}
        n = sum(len(v or []) for v in active.values())
        cap = int(os.environ.get("FACE_PDF_QUEUE_BUSY_THRESHOLD", "4"))
        return n >= cap
    except Exception:
        return False


def resolve_ai_mode(
    user_id: Optional[int] = None,
    *,
    analysis_id: Optional[str] = None,
    lang: str = "hinglish",
    tier: Optional[str] = None,
    plan: Optional[str] = None,
    force_template: bool = False,
) -> BudgetSnapshot:
    """
    Decide AI depth without failing report generation.
    """
    t = tier or user_tier(user_id, plan)
    limits = tier_limits(t)
    user_usd = _fc.get_daily_spend(user_id)
    global_usd = _fc.get_daily_spend(None)
    report_usd = get_report_spend(analysis_id or "")

    global_cap = float(os.environ.get("OPENAI_DAILY_CAP_USD", "15"))
    emergency = float(os.environ.get("FACE_EMERGENCY_GLOBAL_CAP_USD", str(global_cap)))

    reason = "ok"
    mode = AIMode.FULL

    if force_template or (os.environ.get("FACE_READING_AI_NARRATOR", "1").strip() in ("0", "false")):
        return BudgetSnapshot(t, AIMode.TEMPLATE_ONLY, user_usd, report_usd, global_usd, "ai_disabled")

    if global_usd >= emergency:
        return BudgetSnapshot(t, AIMode.TEMPLATE_ONLY, user_usd, report_usd, global_usd, "emergency_global_cap")

    if _fc.is_daily_token_capped(user_id):
        return BudgetSnapshot(t, AIMode.TEMPLATE_ONLY, user_usd, report_usd, global_usd, "daily_cap")

    if user_usd >= limits["daily"]:
        return BudgetSnapshot(t, AIMode.MINI_ONLY, user_usd, report_usd, global_usd, "user_daily_soft_cap")

    if report_usd >= limits["report"]:
        return BudgetSnapshot(t, AIMode.MINI_ONLY, user_usd, report_usd, global_usd, "report_cap")

    if _queue_overloaded():
        return BudgetSnapshot(t, AIMode.MINI_ONLY, user_usd, report_usd, global_usd, "queue_busy")

    # Cross-language: if not English and canonical exists → localize only (handled in orchestrator)
    from .narration_artifact import CANONICAL_LANG, has_canonical_insights

    lang_n = lang.strip().lower()
    if lang_n not in ("en", "english", "eng") and analysis_id and has_canonical_insights(analysis_id):
        return BudgetSnapshot(t, AIMode.LOCALIZE_ONLY, user_usd, report_usd, global_usd, "canonical_localize")

    if report_usd >= limits.get("pass_b", 0.12):
        mode = AIMode.MINI_ONLY
        reason = "pass_b_budget"

    return BudgetSnapshot(t, mode, user_usd, report_usd, global_usd, reason)


def allow_pass_b(snapshot: BudgetSnapshot) -> bool:
    return snapshot.mode == AIMode.FULL


def record_spend(
    usd: float,
    user_id: Optional[int] = None,
    *,
    analysis_id: Optional[str] = None,
) -> None:
    _fc.record_token_spend(usd, user_id)
    if analysis_id:
        add_report_spend(analysis_id, usd)
