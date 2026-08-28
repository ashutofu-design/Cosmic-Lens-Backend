"""Kundli Milan Pro — founder-prepared marriage compatibility PDF orders."""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".cache", "milan_human_orders"))
_lock = threading.Lock()
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[0-9]{10,14}$")


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def _normalize_indian_mobile_digits(raw: str) -> str:
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


def build_marriage_engine_snapshot(marriage_basics: dict[str, Any]) -> dict[str, Any]:
    p1 = marriage_basics.get("p1") if isinstance(marriage_basics.get("p1"), dict) else {}
    p2 = marriage_basics.get("p2") if isinstance(marriage_basics.get("p2"), dict) else {}
    couple = marriage_basics.get("couple") if isinstance(marriage_basics.get("couple"), dict) else {}
    syn = couple.get("synastry") if isinstance(couple.get("synastry"), dict) else {}
    return {
        "p1_name": p1.get("name") or "Partner A",
        "p2_name": p2.get("name") or "Partner B",
        "couple_score": couple.get("structural_score"),
        "couple_band": couple.get("structural_band"),
        "alert_count": int(couple.get("critical_alerts_total") or 0),
        "p1_readiness": p1.get("readiness_score"),
        "p2_readiness": p2.get("readiness_score"),
        "synastry_available": bool(syn.get("available")),
        "engine_only": True,
    }


def _compute_marriage_basics_from_birth(p1: dict, p2: dict, *, lang: str | None = None) -> dict[str, Any]:
    from cache_helpers import get_or_compute_kundli
    from vedic.compat.marriage_basics import compute_marriage_basics

    bp1 = dict(p1)
    bp2 = dict(p2)
    for bp in (bp1, bp2):
        bp.setdefault("name", "Partner")
        bp.setdefault("place", "")
        bp.setdefault("minute", 0)
        bp.setdefault("ampm", "AM")
    k1 = get_or_compute_kundli(bp1) or {}
    k2 = get_or_compute_kundli(bp2) or {}
    if not (k1.get("planets") and k2.get("planets")):
        raise ValueError("Kundli chart unavailable for one or both partners")
    return compute_marriage_basics(
        k1,
        k2,
        p1_name=str(bp1.get("name") or "Partner A"),
        p2_name=str(bp2.get("name") or "Partner B"),
        p1_gender=bp1.get("gender"),
        p2_gender=bp2.get("gender"),
        lang=lang,
    )


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
            f"[milan_human_order] saved id={oid} "
            f"lang={record.get('lang')} urgent={record.get('urgent')} "
            f"contact={record.get('contact_method')}:{record.get('contact_value')}",
            flush=True,
        )
    except Exception:
        pass
    try:
        from order_founder_alert import notify_founder_milan_order

        notify_founder_milan_order(record)
    except Exception as exc:
        try:
            print(f"[milan_human_order] founder alert failed: {exc}", flush=True)
        except Exception:
            pass
    return oid


def get_order(order_id: str) -> dict[str, Any] | None:
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
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    return oid


def list_milan_human_orders(*, page: int = 1, per_page: int = 50, status: str | None = None) -> dict[str, Any]:
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
                "couple_score": snap.get("couple_score"),
                "couple_band": snap.get("couple_band"),
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
    """Pending Kundli Milan Pro orders for My Reports (before PDF ready)."""
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
            page = list_milan_human_orders(page=page_num, per_page=100, status=None)
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
                    "kind": "milan_pro",
                    "status": "pending",
                    "deliverable": "video" if is_video else "report",
                    "report_type": (
                        "Kundli Milan Video Explanation"
                        if is_video
                        else "Kundli Milan Pro Report"
                    ),
                    "name": couple,
                    "eta_label": row.get("eta_label") or "",
                    "date": row.get("created_at"),
                    "title": (
                        f"{couple} — Video (WhatsApp)"
                        if is_video
                        else f"{couple} — Kundli Milan Report"
                    ),
                })
            page_num += 1
    except Exception:
        return out
    return out


def register_milan_human_order_routes(flask_app) -> None:
    if "kundli_milan_human_order" in flask_app.view_functions:
        return

    @flask_app.route("/api/kundli-milan/engine-snapshot", methods=["POST", "OPTIONS"])
    def kundli_milan_engine_snapshot():
        if request.method == "OPTIONS":
            return "", 204
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
            return jsonify({"error": "expected_p1_p2"}), 400
        try:
            mb = _compute_marriage_basics_from_birth(
                data["p1"], data["p2"], lang=data.get("lang")
            )
            snap = build_marriage_engine_snapshot(mb)
            return jsonify({"ok": True, "snapshot": snap}), 200
        except Exception as exc:
            return jsonify({"error": "engine_snapshot_failed", "detail": str(exc)}), 500

    @flask_app.route("/api/kundli-milan/human-order", methods=["POST", "OPTIONS"])
    def kundli_milan_human_order():
        if request.method == "OPTIONS":
            return "", 204
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
            return jsonify({"error": "expected_p1_p2"}), 400

        lang = str(data.get("lang") or "en").strip().lower() or "en"
        urgent = bool(data.get("urgent"))
        deliverable = str(data.get("deliverable") or "report").strip().lower()
        if deliverable not in ("report", "video"):
            deliverable = "report"

        user_id = 0
        uid_hdr = (request.headers.get("X-User-Id") or "").strip()
        if uid_hdr:
            try:
                user_id = int(uid_hdr)
            except Exception:
                user_id = 0

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
            mb = _compute_marriage_basics_from_birth(data["p1"], data["p2"], lang=lang)
            snap = build_marriage_engine_snapshot(mb)
        except Exception as exc:
            return jsonify({"error": "engine_snapshot_failed", "detail": str(exc)}), 500

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
            "product": "milan_pro_video" if deliverable == "video" else "milan_pro",
            "amount_inr": int(data.get("amount_inr") or 0) or None,
            "priority_fee_inr": int(data.get("priority_fee_inr") or 0) or (299 if urgent else 0),
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
            "Order received. Our astrologer will prepare your Marriage Compatibility PDF "
            "and save it in My Reports."
        )
        return jsonify({
            "ok": True,
            "order_id": order_id,
            "eta_hours": eta_hours,
            "message": video_msg if deliverable == "video" else pdf_msg,
        }), 200

    try:
        from milan_telegram_deliver import register_milan_telegram_routes

        register_milan_telegram_routes(flask_app)
    except Exception as _tg_exc:
        try:
            print(f"[milan_human_orders] telegram deliver routes failed: {_tg_exc}", flush=True)
        except Exception:
            pass
