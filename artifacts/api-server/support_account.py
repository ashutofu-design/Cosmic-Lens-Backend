"""Customer-safe account facts for Help & Support AI.

Only fields the user may already see in the app. Never api keys, admin flags,
tokens, paths, or other customers.
"""
from __future__ import annotations

from typing import Any


def _mask_phone(raw: str) -> str:
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if len(digits) < 4:
        return ""
    return f"ending {digits[-4:]}"


def _short_date(iso: str) -> str:
    s = (iso or "").strip()
    if not s:
        return ""
    return s.replace("T", " ")[:16]


def _plan_label(user: Any) -> str:
    try:
        from models import _as_utc_naive, _utc_naive_now

        plan = str(getattr(user, "plan", None) or "free").strip().lower() or "free"
        expiry = _as_utc_naive(getattr(user, "plan_expiry", None))
        active = plan != "free" and expiry is not None and expiry > _utc_naive_now()
        if not active:
            return "Free"
        until = expiry.date().isoformat() if expiry else ""
        name = {"trial": "Trial", "basic": "Basic", "pro": "Pro", "elite": "Pro"}.get(
            plan, plan.title()
        )
        return f"{name} (until {until})" if until else name
    except Exception:
        plan = str(getattr(user, "plan", None) or "free")
        return plan.title() if plan else "Free"


def build_customer_facts(user: Any) -> dict[str, Any]:
    """Structured + text card. Safe to show this user. Empty if user missing."""
    empty: dict[str, Any] = {
        "cosmo": "",
        "name": "",
        "plan": "Free",
        "ask_left": 0,
        "purchases": [],
        "card": "",
    }
    if user is None:
        return empty
    cosmo = str(getattr(user, "cosmo_user_id", None) or "").strip().upper()
    uid = getattr(user, "id", None)
    if not cosmo and uid is not None:
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo = str(cosmo_display_id_for_user_id(int(uid)) or "").strip().upper()
        except Exception:
            if str(uid).isdigit():
                cosmo = f"COSMO{uid}"
    name = str(getattr(user, "name", None) or "").strip()
    phone = _mask_phone(str(getattr(user, "phone", None) or ""))
    plan = _plan_label(user)
    ask_left = 0
    try:
        ask_left = max(0, int(getattr(user, "ask_v1_questions_left", 0) or 0))
    except (TypeError, ValueError):
        ask_left = 0
    free_left = 0
    try:
        used = int(getattr(user, "ask_v1_free_questions_used", 0) or 0)
        bonus = int(getattr(user, "ask_v1_bonus_questions", 0) or 0)
        free_left = max(0, 3 - used) + max(0, bonus)
    except (TypeError, ValueError):
        free_left = 0

    purchases: list[dict[str, Any]] = []
    try:
        from purchase_history import build_user_purchase_history

        if uid is not None:
            for row in build_user_purchase_history(int(uid))[:8]:
                if not isinstance(row, dict):
                    continue
                purchases.append(
                    {
                        "title": str(row.get("title") or "").strip()[:80],
                        "amount": int(row.get("amount_inr") or 0),
                        "status": str(row.get("status") or "paid"),
                        "when": _short_date(str(row.get("paid_at") or "")),
                    }
                )
    except Exception:
        purchases = []

    lines = [
        f"User ID: {cosmo or 'on Profile'}",
        f"Name: {name or 'on Profile'}",
        f"Plan: {plan}",
    ]
    if phone:
        lines.append(f"Login phone: {phone}")
    if ask_left:
        lines.append(f"Ask pack questions left: {ask_left} (Profile → Cosmic Packs)")
    elif free_left:
        lines.append(f"Free Ask questions left: {free_left}")
    else:
        lines.append("Ask questions: 0 left — buy a pack in Profile → Cosmic Packs")
    if purchases:
        lines.append("Recent payments (same as Help → Transactions):")
        for p in purchases[:6]:
            amt = f" ₹{p['amount']}" if p.get("amount") else ""
            when = f" · {p['when']}" if p.get("when") else ""
            lines.append(f"- {p['title']}{amt} ({p.get('status') or 'paid'}){when}")
    else:
        lines.append("Recent payments: none yet. Paid orders show on Help → Transactions.")
    lines.append("Paid Pro PDFs arrive in My Reports (usually 24h, priority 12h).")
    return {
        "cosmo": cosmo,
        "name": name,
        "plan": plan,
        "ask_left": ask_left,
        "purchases": purchases,
        "card": "\n".join(lines),
    }
