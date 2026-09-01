"""Numerology Pro — founder-prepared PDF orders (manual review queue)."""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

from api_auth import authed_user_from_request

_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "numerology_human_orders")
)
_lock = threading.Lock()
_MOBILE_RE = re.compile(r"\D")


def _normalize_indian_mobile_digits(raw: str) -> str:
    digits = _MOBILE_RE.sub("", raw or "")
    if digits.startswith("0091") and len(digits) >= 14:
        digits = digits[4:]
    elif digits.startswith("91") and len(digits) >= 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[:10]


def _normalize_whatsapp(raw: str) -> tuple[str | None, str | None]:
    digits = _normalize_indian_mobile_digits(raw)
    if len(digits) != 10:
        return None, "invalid_whatsapp"
    return f"+91{digits}", None


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def get_order(order_id: str) -> dict[str, Any] | None:
    oid = (order_id or "").strip()
    if not oid:
        return None
    path = os.path.join(_BASE, f"{oid}.json")
    if not os.path.isfile(path):
        # prefix match (8-char telegram style)
        try:
            names = os.listdir(_BASE)
        except OSError:
            return None
        matches = [
            n
            for n in names
            if n.endswith(".json") and n.replace(".json", "").startswith(oid)
        ]
        if len(matches) != 1:
            return None
        path = os.path.join(_BASE, matches[0])
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def save_order_record(record: dict[str, Any], *, alert: bool = False) -> str:
    """Persist order. Set alert=True only on first create."""
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    if alert:
        try:
            from order_founder_alert import notify_founder_numerology_order

            notify_founder_numerology_order(record)
        except Exception as exc:
            print(f"[numerology_human_order] founder alert failed: {exc}", flush=True)
    return oid


def list_human_orders(
    *, page: int = 1, per_page: int = 50, status: str | None = None
) -> dict[str, Any]:
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
        person = rec.get("person") if isinstance(rec.get("person"), dict) else {}
        params = rec.get("params") if isinstance(rec.get("params"), dict) else {}
        uid = int(rec.get("user_id") or 0)
        cosmo_id = (str(rec.get("cosmo_user_id") or "").strip().upper())
        if not cosmo_id and uid:
            try:
                from cosmo_user_id import cosmo_display_id_for_user_id

                cosmo_id = cosmo_display_id_for_user_id(uid)
            except Exception:
                cosmo_id = ""
        name = (
            person.get("name")
            or params.get("name")
            or rec.get("subject_name")
            or "—"
        )
        dob = person.get("dob") or params.get("dob") or ""
        rows.append(
            {
                "order_id": rec.get("order_id") or fn.replace(".json", ""),
                "created_at": rec.get("created_at"),
                "status": rec.get("status") or "pending",
                "lang": rec.get("lang") or "en",
                "urgent": bool(rec.get("urgent")),
                "deliverable": rec.get("deliverable") or "report",
                "contact_method": rec.get("contact_method") or "my_reports",
                "contact_value": rec.get("contact_value") or "",
                "user_id": uid,
                "cosmo_user_id": cosmo_id,
                "subject_name": name,
                "dob": dob,
                "mobile": person.get("mobile") or params.get("mobile") or "",
                "place": person.get("place") or params.get("place") or "",
                "purchase_id": rec.get("purchase_id"),
                "amount_inr": rec.get("amount_inr"),
                "priority_fee_inr": rec.get("priority_fee_inr"),
                "eta_hours": rec.get("eta_hours"),
                "eta_label": rec.get("eta_label"),
                "person": person or None,
                "params": params or None,
                "admin_accepted_at": rec.get("admin_accepted_at"),
            }
        )
    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    total = len(rows)
    page = max(1, int(page))
    per_page = max(1, min(100, int(per_page)))
    start = (page - 1) * per_page
    return {
        "orders": rows[start : start + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


def list_pending_for_user(user_id: int) -> list[dict[str, Any]]:
    """Pending Numerology Pro orders for My Reports (before PDF ready)."""
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
                pub = str(row.get("public_order_id") or "").strip() or oid[:8].upper()
                name = str(row.get("subject_name") or "Numerology").strip() or "Numerology"
                out.append({
                    "id": pub or oid,
                    "order_id": oid,
                    "public_order_id": pub,
                    "kind": "numerology_pro",
                    "status": "pending",
                    "deliverable": "video" if is_video else "report",
                    "report_type": (
                        "Numerology Video Explanation"
                        if is_video
                        else "Numerology Pro Report"
                    ),
                    "name": name,
                    "eta_label": row.get("eta_label") or "",
                    "date": row.get("created_at"),
                    "title": (
                        f"{name} — Video (WhatsApp)"
                        if is_video
                        else f"{name} — Numerology Report"
                    ),
                })
            page_num += 1
    except Exception:
        return out
    return out


def _purchase_already_used(purchase_id: int) -> bool:
    if not purchase_id:
        return False
    _ensure_dir()
    try:
        names = os.listdir(_BASE)
    except OSError:
        return False
    for fn in names:
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(_BASE, fn), encoding="utf-8") as fh:
                rec = json.load(fh)
            if int(rec.get("purchase_id") or 0) == purchase_id:
                return True
        except Exception:
            continue
    return False


def register_numerology_human_order_routes(flask_app) -> None:
    @flask_app.route("/api/numerology/human-order", methods=["POST", "OPTIONS"])
    def numerology_human_order():
        if request.method == "OPTIONS":
            return "", 204

        from models import CoupleReportPurchase, User

        data = request.get_json(silent=True) or {}
        user, err = authed_user_from_request(data)
        if err:
            return err

        params = data.get("params") if isinstance(data.get("params"), dict) else {}
        name = str(data.get("name") or params.get("name") or "").strip()
        dob = str(data.get("dob") or params.get("dob") or "").strip()
        if not name or not dob:
            return jsonify({"error": "name_dob_required"}), 400

        lang = str(data.get("lang") or params.get("lang") or "en").strip().lower()
        if lang not in ("en", "hn", "hi"):
            lang = "en"
        urgent = bool(data.get("urgent"))
        deliverable = str(data.get("deliverable") or "report").strip().lower()
        if deliverable not in ("report", "video"):
            deliverable = "report"

        raw_whatsapp = str(
            data.get("whatsapp") or data.get("contact_value") or ""
        ).strip()
        if deliverable == "video":
            contact, err = _normalize_whatsapp(raw_whatsapp)
            if err:
                return jsonify({"error": err}), 400
            contact_method = "whatsapp"
            contact_value = contact
        else:
            contact_method = "my_reports"
            contact_value = str(user.id)

        purchase_id = 0
        try:
            purchase_id = int(data.get("purchase_id") or 0)
        except (TypeError, ValueError):
            purchase_id = 0

        amount_inr = None
        priority_fee_inr = (
            int(data.get("priority_fee_inr") or 0)
            or (299 if urgent and deliverable == "video" else (149 if urgent else 0))
        )
        from numerology_report_billing import (
            payment_bypass as _nrb_bypass,
            payment_required as _nrb_payment_required,
        )

        if purchase_id:
            if _purchase_already_used(purchase_id):
                return jsonify({"error": "purchase_already_submitted"}), 409
            purchase = CoupleReportPurchase.query.get(purchase_id)
            if not purchase or purchase.user_id != user.id:
                return jsonify({"error": "invalid_purchase"}), 400
            if purchase.status != "paid":
                return jsonify({"error": "payment_not_confirmed"}), 402
            if (purchase.product or "") != "life_mastery":
                return jsonify({"error": "wrong_product"}), 400
            amount_inr = purchase.amount
        elif _nrb_payment_required():
            # A human-written report is a paid deliverable — no purchase, no order.
            return (
                jsonify(
                    {
                        "error": "payment_required",
                        "message": "Complete payment before submitting this order.",
                    }
                ),
                402,
            )

        # Always persist display amount for admin (paid total, or catalog when bypass).
        if amount_inr is None or int(amount_inr or 0) <= 0:
            try:
                from numerology_report_billing import CATALOG, PRODUCT_LIFE_MASTERY

                base = int(CATALOG[PRODUCT_LIFE_MASTERY].get("amount_inr") or 299)
            except Exception:
                base = 299
            if deliverable == "video":
                base = int(
                    __import__("os").environ.get("LIFE_MASTERY_VIDEO_PRICE_INR", "799")
                )
            amount_inr = base + (priority_fee_inr if urgent else 0)
        # Client-supplied amount is honoured only under a dev payment bypass;
        # otherwise the amount always comes from the purchase or the catalog.
        if _nrb_bypass():
            try:
                client_amt = int(data.get("amount_inr") or 0)
                if client_amt > 0:
                    amount_inr = client_amt
            except (TypeError, ValueError):
                pass

        cosmo_user_id = (str(data.get("cosmo_user_id") or "").strip().upper())
        if not cosmo_user_id:
            try:
                from cosmo_user_id import cosmo_display_id_for_user_id

                cosmo_user_id = cosmo_display_id_for_user_id(user.id)
            except Exception:
                cosmo_user_id = ""

        person = {
            "name": name,
            "dob": dob,
            "tob": str(data.get("tob") or params.get("tob") or "").strip(),
            "mobile": str(data.get("mobile") or params.get("mobile") or "").strip(),
            "place": str(data.get("place") or params.get("place") or "").strip(),
            "lat": params.get("lat"),
            "lon": params.get("lon"),
            "tz": params.get("tz"),
        }

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "order_id": order_id,
            "created_at": now,
            "user_id": user.id,
            "cosmo_user_id": cosmo_user_id,
            "lang": lang,
            "urgent": urgent,
            "subject_name": name,
            "person": person,
            "params": params,
            "purchase_id": purchase_id or None,
            "amount_inr": amount_inr,
            "priority_fee_inr": priority_fee_inr,
            "eta_hours": 12 if urgent else 144,
            "eta_label": (
                "⚡ Priority — deliver within 12 hours"
                if urgent
                else "📦 Standard — 4–6 business days"
            ),
            "status": "pending",
            "deliverable": deliverable,
            "delivery": (
                "whatsapp_video_explanation"
                if deliverable == "video"
                else "founder_manual_pdf"
            ),
            "contact_method": contact_method,
            "contact_value": contact_value,
        }
        save_order_record(record, alert=True)

        eta = 12 if urgent else 144
        video_msg = (
            "Order received. Personalized Video Explanation will be delivered on WhatsApp. "
            "No PDF/report is included."
        )
        pdf_msg = (
            f"Order received. Your Numerology Pro report will appear in "
            f"My Reports within {eta} hours."
        )
        return jsonify(
            {
                "ok": True,
                "order_id": order_id,
                "status": "pending",
                "eta_hours": eta,
                "message": video_msg if deliverable == "video" else pdf_msg,
            }
        ), 200
