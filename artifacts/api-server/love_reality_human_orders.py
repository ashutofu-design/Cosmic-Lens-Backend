"""Love Reality Pro — founder-prepared PDF orders (no LLM)."""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".cache", "love_reality_human_orders"))
_lock = threading.Lock()
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[0-9]{10,14}$")


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def _normalize_indian_mobile_digits(raw: str) -> str:
    """Accept 9876543210, +91…, 919876543210, 09876543210, 0091…"""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0091") and len(digits) >= 14:
        digits = digits[4:]
    elif digits.startswith("91") and len(digits) >= 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits


def _normalize_contact(method: str, value: str) -> tuple[str | None, str | None]:
    method = (method or "").strip().lower()
    raw = (value or "").strip()
    if not raw:
        return None, "contact_required"
    if method == "email":
        if not _EMAIL_RE.match(raw):
            return None, "invalid_email"
        return raw.lower(), None
    if method == "whatsapp":
        digits = _normalize_indian_mobile_digits(raw)
        if len(digits) != 10:
            return None, "invalid_whatsapp"
        return f"+91{digits}", None
    return None, "invalid_contact_method"


def _tool_payload(bundle: dict, key: str) -> dict:
    mapping = {
        "love-compat": "love_compatibility",
        "breakup": "breakup_chances",
        "loyalty": "loyalty_check",
        "will-return": "will_return",
        "future-outcome": "future_outcome",
    }
    raw = bundle.get(mapping.get(key, "")) or {}
    return raw if isinstance(raw, dict) else {}


def build_engine_snapshot(bundle: dict) -> dict[str, Any]:
    p1 = bundle.get("p1") if isinstance(bundle.get("p1"), dict) else {}
    p2 = bundle.get("p2") if isinstance(bundle.get("p2"), dict) else {}
    tools = {
        "love-compat": _tool_payload(bundle, "love-compat"),
        "breakup": _tool_payload(bundle, "breakup"),
        "loyalty": _tool_payload(bundle, "loyalty"),
        "will-return": _tool_payload(bundle, "will-return"),
        "future-outcome": _tool_payload(bundle, "future-outcome"),
    }
    rf = bundle.get("hidden_red_flags") if isinstance(bundle.get("hidden_red_flags"), dict) else {}
    flags = rf.get("flags")
    return {
        "p1_name": p1.get("name") or "You",
        "p2_name": p2.get("name") or "Partner",
        "tools": tools,
        "red_flag_count": len(flags) if isinstance(flags, list) else 0,
        "engine_only": True,
    }


def _save_order(record: dict) -> str:
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    try:
        print(
            f"[love_reality_human_order] saved id={oid} "
            f"lang={record.get('lang')} urgent={record.get('urgent')} "
            f"contact={record.get('contact_method')}:{record.get('contact_value')}",
            flush=True,
        )
    except Exception:
        pass
    try:
        from order_founder_alert import notify_founder_love_reality_order

        notify_founder_love_reality_order(record)
    except Exception as exc:
        try:
            print(f"[love_reality_human_order] founder alert failed: {exc}", flush=True)
        except Exception:
            pass
    return oid


def get_order(order_id: str) -> dict[str, Any] | None:
    """Load full Love Reality human order by uuid or unique prefix."""
    oid = (order_id or "").strip()
    if not oid:
        return None
    path = os.path.join(_BASE, f"{oid}.json")
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)
            return rec if isinstance(rec, dict) else None
        except Exception:
            return None
    _ensure_dir()
    try:
        names = os.listdir(_BASE)
    except OSError:
        return None
    matches = [
        n for n in names if n.endswith(".json") and n.replace(".json", "").startswith(oid)
    ]
    if len(matches) != 1:
        return None
    try:
        with open(os.path.join(_BASE, matches[0]), encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def save_order_record(record: dict[str, Any]) -> str:
    """Update an existing order without re-sending founder alert."""
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    return oid


def list_human_orders(*, page: int = 1, per_page: int = 50, status: str | None = None) -> dict[str, Any]:
    """Admin: list founder-prepared Love Reality PDF orders (newest first)."""
    _ensure_dir()
    rows: list[dict[str, Any]] = []
    try:
        names = sorted(os.listdir(_BASE), reverse=True)
    except OSError:
        names = []
    status_filter = (status or "").strip().lower()
    for fn in names:
        if not fn.endswith(".json"):
            continue
        path = os.path.join(_BASE, fn)
        try:
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        if status_filter and str(rec.get("status") or "").lower() != status_filter:
            continue
        snap = rec.get("engine_snapshot") if isinstance(rec.get("engine_snapshot"), dict) else {}
        p1 = rec.get("p1") if isinstance(rec.get("p1"), dict) else {}
        p2 = rec.get("p2") if isinstance(rec.get("p2"), dict) else {}
        cosmo_id = (str(rec.get("cosmo_user_id") or "").strip().upper())
        uid = int(rec.get("user_id") or 0)
        if not cosmo_id and uid:
            try:
                from cosmo_user_id import cosmo_display_id_for_user_id

                cosmo_id = cosmo_display_id_for_user_id(uid)
            except Exception:
                cosmo_id = ""
        rows.append(
            {
                "order_id": rec.get("order_id") or fn.replace(".json", ""),
                "created_at": rec.get("created_at"),
                "status": rec.get("status") or "pending",
                "lang": rec.get("lang") or "en",
                "urgent": bool(rec.get("urgent")),
                "deliverable": rec.get("deliverable") or "report",
                "amount_inr": rec.get("amount_inr"),
                "priority_fee_inr": rec.get("priority_fee_inr"),
                "eta_hours": rec.get("eta_hours"),
                "eta_label": rec.get("eta_label"),
                "contact_method": rec.get("contact_method"),
                "contact_value": rec.get("contact_value"),
                "user_id": uid,
                "cosmo_user_id": cosmo_id,
                "p1_name": snap.get("p1_name") or p1.get("name") or "—",
                "p2_name": snap.get("p2_name") or p2.get("name") or "—",
                "p1": p1 or None,
                "p2": p2 or None,
                "engine_snapshot": snap or None,
                "admin_accepted_at": rec.get("admin_accepted_at"),
            }
        )
    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    total = len(rows)
    page = max(1, int(page))
    per_page = max(1, min(100, int(per_page)))
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "orders": rows[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


def list_pending_for_user(user_id: int) -> list[dict[str, Any]]:
    """Pending Love Reality Pro orders for My Reports (before PDF ready)."""
    try:
        uid = int(user_id or 0)
    except (TypeError, ValueError):
        uid = 0
    if uid <= 0:
        return []
    out: list[dict[str, Any]] = []
    try:
        page_num = 1
        pages = 1
        while page_num <= pages:
            page = list_human_orders(page=page_num, per_page=100, status=None)
            pages = max(1, int(page.get("pages") or 1))
            for row in page.get("orders") or []:
                if int(row.get("user_id") or 0) != uid:
                    continue
                st = str(row.get("status") or "pending").lower()
                if st in ("delivered", "cancelled", "canceled", "deleted"):
                    continue
                is_video = str(row.get("deliverable") or "").lower() == "video"
                oid = str(row.get("order_id") or "").strip()
                pub = str(row.get("public_order_id") or "").strip() or (oid[:8].upper() if oid else "")
                p1 = str(row.get("p1_name") or "You").strip() or "You"
                p2 = str(row.get("p2_name") or "Partner").strip() or "Partner"
                couple = f"{p1} & {p2}"
                out.append({
                    "id": pub or oid,
                    "order_id": oid,
                    "public_order_id": pub,
                    "kind": "love_reality_pro",
                    "status": "pending",
                    "deliverable": "video" if is_video else "report",
                    "report_type": (
                        "Love Reality Video Explanation"
                        if is_video
                        else "Love Reality Pro Report"
                    ),
                    "name": couple,
                    "eta_label": row.get("eta_label") or "",
                    "date": row.get("created_at"),
                    "title": (
                        f"{couple} — Video (WhatsApp)"
                        if is_video
                        else f"{couple} — Love Reality Report"
                    ),
                })
            page_num += 1
    except Exception:
        return out
    return out


def register_human_order_routes(flask_app, rate_limit=None) -> None:
    """Register engine snapshot + human PDF order routes."""

    if "love_reality_engine_snapshot" in flask_app.view_functions:
        return

    from api_auth import require_authed_user
    import couple_report_billing as crb

    def _rl(spec):
        def deco(fn):
            if rate_limit:
                return rate_limit(spec)(fn)
            return fn

        return deco

    @flask_app.route("/api/love-reality/engine-snapshot", methods=["POST", "OPTIONS"])
    @_rl("20 per minute")
    def love_reality_engine_snapshot():
        if request.method == "OPTIONS":
            return "", 204
        user, err = require_authed_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
            return jsonify({"error": "expected_p1_p2"}), 400
        try:
            from vedic.love_reality.compute_bundle import compute_love_reality_bundle

            bundle = compute_love_reality_bundle(
                flask_app, data["p1"], data["p2"], skip_ai_insight=True
            )
            snap = build_engine_snapshot(bundle)
            return jsonify({"ok": True, "snapshot": snap}), 200
        except Exception as exc:
            return jsonify({"error": "engine_snapshot_failed", "detail": str(exc)}), 500

    @flask_app.route("/api/love-reality/human-order", methods=["POST", "OPTIONS"])
    @_rl("10 per minute")
    def love_reality_human_order():
        if request.method == "OPTIONS":
            return "", 204
        user, err = require_authed_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
            return jsonify({"error": "expected_p1_p2"}), 400

        lang = str(data.get("lang") or "en").strip().lower() or "en"
        urgent = bool(data.get("urgent"))
        deliverable = str(data.get("deliverable") or "report").strip().lower()
        if deliverable not in ("report", "video"):
            deliverable = "report"

        user_id = int(user.id)

        method = str(data.get("contact_method") or "my_reports").strip().lower()
        raw_contact = str(data.get("contact_value") or data.get("whatsapp") or "").strip()
        if deliverable == "video":
            method = "whatsapp"
            contact, err = _normalize_contact(method, raw_contact)
            if err:
                return jsonify({"error": err}), 400
        elif raw_contact:
            contact, err = _normalize_contact(method, raw_contact)
            if err:
                return jsonify({"error": err}), 400
        else:
            method = "my_reports"
            contact = str(user_id) if user_id else "in_app"

        try:
            from vedic.love_reality.compute_bundle import compute_love_reality_bundle

            bundle = compute_love_reality_bundle(
                flask_app, data["p1"], data["p2"], skip_ai_insight=True
            )
            snap = build_engine_snapshot(bundle)
        except Exception as exc:
            return jsonify({"error": "engine_snapshot_failed", "detail": str(exc)}), 500

        amount_inr = crb.amount_for(crb.PRODUCT_LOVE, deliverable, urgent)
        priority_fee_inr = int(crb._PRIORITY_FEES.get(crb.PRODUCT_LOVE, 299) if urgent else 0)

        if crb.payment_required() and not crb.payment_bypass() and not crb.love_reality_pro_free():
            cache_params = crb.cache_params_from_birth(lang, data["p1"], data["p2"])
            access = crb.check_access(user.id, crb.PRODUCT_LOVE, cache_params)
            if not access.get("entitled"):
                return jsonify(
                    {
                        "error": "payment_required",
                        "message": "Complete Love Reality Pro payment before placing this order.",
                    }
                ), 402

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        cosmo_user_id = (
            str(data.get("cosmo_user_id") or request.headers.get("X-Cosmo-User-Id") or "")
            .strip()
            .upper()
        )
        if not cosmo_user_id and user_id:
            try:
                from cosmo_user_id import cosmo_display_id_for_user_id

                cosmo_user_id = cosmo_display_id_for_user_id(user_id)
            except Exception:
                cosmo_user_id = ""
        record = {
            "order_id": order_id,
            "created_at": now,
            "user_id": user_id,
            "cosmo_user_id": cosmo_user_id,
            "lang": lang,
            "urgent": urgent,
            "contact_method": method,
            "contact_value": contact,
            "p1": data["p1"],
            "p2": data["p2"],
            "engine_snapshot": snap,
            "status": "pending",
            "deliverable": deliverable,
            "delivery": "whatsapp_video_explanation" if deliverable == "video" else "founder_manual_pdf",
            "amount_inr": amount_inr,
            "priority_fee_inr": priority_fee_inr,
            "eta_hours": 12 if urgent else 144,
            "eta_label": (
                "⚡ Priority — deliver within 12 hours"
                if urgent
                else "📦 Standard — 4–6 business days"
            ),
        }
        _save_order(record)

        eta_hours = 12 if urgent else 144
        video_msg = (
            "Order received. Personalized Video Explanation will be delivered on WhatsApp. "
            "No PDF/report is included."
        )
        pdf_msg = (
            "Order received. Our astrologer will prepare your verified PDF "
            "and save it in My Reports."
        )
        return jsonify({
            "ok": True,
            "order_id": order_id,
            "eta_hours": eta_hours,
            "message": video_msg if deliverable == "video" else pdf_msg,
        }), 200

    try:
        from love_reality_telegram_deliver import register_telegram_deliver_routes

        register_telegram_deliver_routes(flask_app)
    except Exception as _tg_exc:
        try:
            print(f"[love_reality_human_orders] telegram deliver routes failed: {_tg_exc}", flush=True)
        except Exception:
            pass
