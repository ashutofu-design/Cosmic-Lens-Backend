"""This-customer-only tools. No unrestricted DB. Empty on failure — never invent."""
from __future__ import annotations

from typing import Any


def _safe_user_id(user: Any) -> int | None:
    try:
        uid = getattr(user, "id", None)
        return int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None


def get_user_profile(user: Any) -> dict[str, Any]:
    if user is None:
        return {"ok": False, "error": "no_user"}
    cosmo = str(getattr(user, "cosmo_user_id", None) or "").strip().upper()
    uid = _safe_user_id(user)
    if not cosmo and uid is not None:
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo = str(cosmo_display_id_for_user_id(uid) or "").strip().upper()
        except Exception:
            cosmo = f"COSMO{uid}"
    return {
        "ok": True,
        "cosmo": cosmo,
        "name": str(getattr(user, "name", None) or "").strip(),
        "ask_pack_left": max(0, int(getattr(user, "ask_v1_questions_left", 0) or 0)),
    }


def get_subscription(user: Any) -> dict[str, Any]:
    if user is None:
        return {"ok": False, "error": "no_user"}
    try:
        from support_account import _plan_label

        return {"ok": True, "plan": _plan_label(user)}
    except Exception:
        plan = str(getattr(user, "plan", None) or "free")
        return {"ok": True, "plan": plan.title() if plan else "Free"}


def get_wallet_status(user: Any) -> dict[str, Any]:
    """Cosmic Lens has no rupee wallet. Ask credits only."""
    profile = get_user_profile(user)
    return {
        "ok": True,
        "has_wallet": False,
        "ask_pack_left": int(profile.get("ask_pack_left") or 0),
        "note": "No wallet. Paid orders = Help → Transactions. Ask credits = Profile → Cosmic Packs.",
    }


def get_transactions(user: Any) -> dict[str, Any]:
    uid = _safe_user_id(user)
    if uid is None:
        return {"ok": False, "error": "no_user", "orders": []}
    orders: list[dict[str, Any]] = []
    try:
        from purchase_history import build_user_purchase_history

        for row in build_user_purchase_history(uid)[:8]:
            if not isinstance(row, dict):
                continue
            orders.append(
                {
                    "title": str(row.get("title") or "").strip()[:80],
                    "amount_inr": int(row.get("amount_inr") or 0),
                    "status": str(row.get("status") or "paid"),
                    "paid_at": str(row.get("paid_at") or "")[:16],
                }
            )
    except Exception:
        return {"ok": False, "error": "tool_failed", "orders": []}
    return {"ok": True, "orders": orders}


def get_report_status(user: Any) -> dict[str, Any]:
    uid = _safe_user_id(user)
    if uid is None:
        return {"ok": False, "error": "no_user", "reports": []}
    try:
        import report_cache as _rc

        rows = _rc.list_for_user(uid, 8)
    except Exception:
        return {"ok": False, "error": "tool_failed", "reports": []}
    reports = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        reports.append(
            {
                "type": str(r.get("report_type") or r.get("kind") or "pdf")[:40],
                "date": str(r.get("date") or "")[:16],
            }
        )
    return {"ok": True, "reports": reports}


def snapshot(user: Any) -> dict[str, Any]:
    """Run all bounded tools for this logged-in customer."""
    profile = get_user_profile(user)
    sub = get_subscription(user)
    wallet = get_wallet_status(user)
    tx = get_transactions(user)
    reports = get_report_status(user)
    lines = [
        f"get_user_profile: ok={profile.get('ok')} cosmo={profile.get('cosmo') or '(unknown)'} "
        f"name={profile.get('name') or '(on Profile)'} ask_pack_left={profile.get('ask_pack_left')}",
        f"get_subscription: ok={sub.get('ok')} plan={sub.get('plan')}",
        f"get_wallet_status: has_wallet=false ask_pack_left={wallet.get('ask_pack_left')} "
        f"note={wallet.get('note')}",
    ]
    if not tx.get("ok"):
        lines.append("get_transactions: TOOL FAILED — do not invent orders. Escalate if they ask about a payment.")
    elif not tx.get("orders"):
        lines.append("get_transactions: no paid orders on Help → Transactions.")
    else:
        bits = [
            f"{o.get('title')} ₹{o.get('amount_inr')} {o.get('status')}"
            for o in tx["orders"]
            if isinstance(o, dict)
        ]
        lines.append("get_transactions: " + "; ".join(bits[:6]))
    if not reports.get("ok"):
        lines.append("get_report_status: TOOL FAILED — do not invent PDFs. Escalate if they ask about a missing report.")
    elif not reports.get("reports"):
        lines.append("get_report_status: no PDFs in My Reports yet.")
    else:
        bits = [
            f"{r.get('type')} {r.get('date')}"
            for r in reports["reports"]
            if isinstance(r, dict)
        ]
        lines.append("get_report_status: " + "; ".join(bits[:6]))
    return {
        "profile": profile,
        "subscription": sub,
        "wallet": wallet,
        "transactions": tx,
        "reports": reports,
        "text": "\n".join(lines),
        "tx_ok": bool(tx.get("ok")),
        "tx_count": len(tx.get("orders") or []),
        "reports_ok": bool(reports.get("ok")),
    }
