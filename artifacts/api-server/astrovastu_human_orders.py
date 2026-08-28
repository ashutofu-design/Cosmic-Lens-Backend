"""AstroVastu Pro — paid room photo uploads for founder manual Vastu review."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".cache", "astrovastu_human_orders"))
_lock = threading.Lock()
_MANUAL_ROOM_SKUS = frozenset({"room_expert_199", "room_expert_99"})


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


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
            f"[astrovastu_human_order] saved id={oid} "
            f"room={record.get('room_type')} dir={record.get('direction')} "
            f"purchase_id={record.get('purchase_id')}",
            flush=True,
        )
    except Exception:
        pass
    try:
        from order_founder_alert import notify_founder_astrovastu_room_order

        notify_founder_astrovastu_room_order(record)
    except Exception as exc:
        try:
            print(f"[astrovastu_human_order] founder alert failed: {exc}", flush=True)
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
    """Update order without re-sending founder alert."""
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    return oid


def list_human_orders(*, page: int = 1, per_page: int = 50, status: str | None = None) -> dict[str, Any]:
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
        rec = _promote_draft_if_paid(rec)
        if status_filter and str(rec.get("status") or "").lower() != status_filter:
            continue
        preview = rec.get("image_data_url") or rec.get("data_url") or ""
        media_kind = ""
        if isinstance(preview, str):
            if preview.startswith("data:application/pdf"):
                media_kind = "pdf"
            elif preview.startswith("data:image"):
                media_kind = "image"
        rows.append({
            "order_id": rec.get("order_id"),
            "created_at": rec.get("created_at"),
            "user_id": rec.get("user_id"),
            "cosmo_user_id": rec.get("cosmo_user_id"),
            "room_type": rec.get("room_type"),
            "direction": rec.get("direction"),
            "purchase_id": rec.get("purchase_id"),
            "amount_inr": rec.get("amount_inr"),
            "priority_fee_inr": rec.get("priority_fee_inr"),
            "urgent": bool(rec.get("urgent")),
            "eta_hours": rec.get("eta_hours"),
            "eta_label": rec.get("eta_label"),
            "sku": rec.get("sku"),
            "status": rec.get("status") or "pending",
            "has_image": bool(preview),
            "media_kind": media_kind or None,
            "admin_accepted_at": rec.get("admin_accepted_at"),
        })
    total = len(rows)
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    start = (page - 1) * per_page
    return {
        "items": rows[start : start + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def list_pending_for_user(user_id: int) -> list[dict[str, Any]]:
    """Pending AstroVastu Pro orders for My Reports (before PDF ready)."""
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
            for row in page.get("items") or []:
                if int(row.get("user_id") or 0) != uid:
                    continue
                st = str(row.get("status") or "pending").lower()
                if st in ("delivered", "cancelled", "canceled", "deleted", "awaiting_payment", "draft"):
                    continue
                oid = str(row.get("order_id") or "").strip()
                pub = str(row.get("public_order_id") or "").strip() or (oid[:8].upper() if oid else "")
                room = str(row.get("room_type") or row.get("sku") or "Room").strip() or "Room"
                out.append({
                    "id": pub or oid,
                    "order_id": oid,
                    "public_order_id": pub,
                    "kind": "astrovastu_pro",
                    "status": "pending",
                    "deliverable": "report",
                    "report_type": "AstroVastu Pro Report",
                    "name": room,
                    "eta_label": row.get("eta_label") or "",
                    "date": row.get("created_at"),
                    "title": f"{room} — AstroVastu Report",
                })
            page_num += 1
    except Exception:
        return out
    return out


def _find_by_purchase(purchase_id: int) -> dict[str, Any] | None:
    _ensure_dir()
    try:
        names = os.listdir(_BASE)
    except OSError:
        return None
    for fn in names:
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(_BASE, fn), encoding="utf-8") as fh:
                rec = json.load(fh)
            if isinstance(rec, dict) and int(rec.get("purchase_id") or 0) == purchase_id:
                return rec
        except Exception:
            continue
    return None


def _promote_draft_if_paid(rec: dict[str, Any]) -> dict[str, Any]:
    """Draft saved before payment → flip to pending once the purchase is paid.

    Runs server-side (admin list), so delivery never depends on the mobile app
    calling back after payment.
    """
    if str(rec.get("status") or "").lower() != "awaiting_payment":
        return rec
    try:
        from models import AstroVastuPurchase

        purchase = AstroVastuPurchase.query.get(int(rec.get("purchase_id") or 0))
        if not purchase or purchase.status != "paid":
            return rec
        rec["status"] = "pending"
        rec["amount_inr"] = purchase.amount
        rec["sku"] = purchase.sku
        rec["paid_promoted_at"] = datetime.now(timezone.utc).isoformat()
        save_order_record(rec)
        if not rec.get("founder_alert_sent"):
            try:
                from order_founder_alert import notify_founder_astrovastu_room_order

                notify_founder_astrovastu_room_order(rec)
                rec["founder_alert_sent"] = True
                save_order_record(rec)
            except Exception:
                pass
    except Exception:
        pass
    return rec


def _cosmo_id(user_id: int) -> str:
    try:
        from cosmo_user_id import cosmo_display_id_for_user_id

        return cosmo_display_id_for_user_id(user_id)
    except Exception:
        return ""


def _payment_bypass_active() -> bool:
    """Free-submit mode: explicit env flag, or Razorpay not configured.

    Keeps the ₹199 UI intact while letting uploads reach the founder queue
    without a payment. Restoring Razorpay keys re-enables the paid flow
    automatically (unless the env flag forces bypass).
    """
    if (os.environ.get("ROOM_UPLOAD_PAYMENT_BYPASS") or "").strip() == "1":
        return True
    try:
        import payment_gateway as pg

        return not pg.configured()
    except Exception:
        return False


def register_astrovastu_human_order_routes(flask_app) -> None:
    @flask_app.route("/api/astrovastu/room-upload-draft", methods=["POST", "OPTIONS"])
    def astrovastu_room_upload_draft():
        """Save the room photo BEFORE payment (status=awaiting_payment).

        Server promotes it to pending automatically once the purchase turns
        paid — so the founder queue never depends on the app surviving the
        payment round-trip.
        """
        if request.method == "OPTIONS":
            return "", 204

        from models import AstroVastuPurchase, User

        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        api_key = (request.headers.get("X-API-Key") or "").strip()
        if not user_id or not api_key:
            return jsonify({"error": "auth_required"}), 401
        user = User.query.filter_by(id=user_id, api_key=api_key).first()
        if not user:
            return jsonify({"error": "invalid_credentials"}), 401

        room_type = (data.get("room_type") or "").strip()
        direction = (data.get("direction") or "").strip().upper()
        data_url = (data.get("data_url") or data.get("image_data_url") or "").strip()
        urgent = bool(data.get("urgent"))
        try:
            purchase_id = int(data.get("purchase_id") or 0)
        except (TypeError, ValueError):
            purchase_id = 0

        if not room_type or not direction or not data_url:
            return jsonify({"error": "room_direction_image_required"}), 400
        if not purchase_id:
            return jsonify({"error": "purchase_id_required"}), 400

        purchase = AstroVastuPurchase.query.get(purchase_id)
        if not purchase or purchase.user_id != user.id:
            return jsonify({"error": "invalid_purchase"}), 400
        if purchase.sku not in _MANUAL_ROOM_SKUS:
            return jsonify({"error": "wrong_sku_for_manual_upload"}), 400

        existing = _find_by_purchase(purchase_id)
        if existing:
            return jsonify({
                "ok": True,
                "order_id": existing.get("order_id"),
                "status": existing.get("status"),
            }), 200

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "order_id": order_id,
            "created_at": now,
            "user_id": user.id,
            "cosmo_user_id": _cosmo_id(user.id),
            "room_type": room_type,
            "direction": direction,
            "image_data_url": data_url,
            "data_url": data_url,
            "purchase_id": purchase_id,
            "amount_inr": purchase.amount,
            "sku": purchase.sku,
            "status": "pending" if purchase.status == "paid" else "awaiting_payment",
            "delivery": "founder_manual_vastu_report",
        }
        if purchase.status == "paid":
            save_order_record(record)
            try:
                from order_founder_alert import notify_founder_astrovastu_room_order

                notify_founder_astrovastu_room_order(record)
                record["founder_alert_sent"] = True
                save_order_record(record)
            except Exception:
                pass
        else:
            save_order_record(record)
            try:
                print(
                    f"[astrovastu_human_order] draft saved id={order_id} "
                    f"purchase_id={purchase_id} (awaiting payment)",
                    flush=True,
                )
            except Exception:
                pass

        return jsonify({"ok": True, "order_id": order_id, "status": record["status"]}), 200

    @flask_app.route("/api/astrovastu/room-upload-order", methods=["POST", "OPTIONS"])
    def astrovastu_room_upload_order():
        if request.method == "OPTIONS":
            return "", 204

        from models import AstroVastuPurchase, User

        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        api_key = (request.headers.get("X-API-Key") or "").strip()
        if not user_id or not api_key:
            return jsonify({"error": "auth_required"}), 401
        user = User.query.filter_by(id=user_id, api_key=api_key).first()
        if not user:
            return jsonify({"error": "invalid_credentials"}), 401

        room_type = (data.get("room_type") or "").strip()
        direction = (data.get("direction") or "").strip().upper()
        data_url = (data.get("data_url") or data.get("image_data_url") or "").strip()
        urgent = bool(data.get("urgent"))
        try:
            purchase_id = int(data.get("purchase_id") or 0)
        except (TypeError, ValueError):
            purchase_id = 0

        if not room_type or not direction or not data_url:
            return jsonify({"error": "room_direction_image_required"}), 400

        amount_inr = 199
        sku = "room_expert_199"
        if purchase_id:
            purchase = AstroVastuPurchase.query.get(purchase_id)
            if not purchase or purchase.user_id != user.id:
                return jsonify({"error": "invalid_purchase"}), 400
            if purchase.status != "paid":
                return jsonify({"error": "payment_not_confirmed"}), 402
            if purchase.sku not in _MANUAL_ROOM_SKUS:
                return jsonify({"error": "wrong_sku_for_manual_upload"}), 400
            amount_inr = purchase.amount
            sku = purchase.sku
            if int(purchase.amount or 0) > 199:
                urgent = True

            existing = _find_by_purchase(purchase_id)
            if existing:
                # Draft already uploaded pre-payment → promote it now.
                if str(existing.get("status") or "").lower() == "awaiting_payment":
                    existing = _promote_draft_if_paid(existing)
                return jsonify({
                    "ok": True,
                    "order_id": existing.get("order_id"),
                    "status": existing.get("status"),
                    "message": (
                        "Photo received. Priority report within 12 hours."
                        if urgent
                        else "Photo received. Our Vastu expert will review and add your report in 4–6 business days."
                    ),
                    "eta_hours": 12 if urgent else 144,
                }), 200
        # No purchase_id → free/bypass submit. UI still shows ₹199; when
        # Razorpay is back the client sends a real purchase_id instead.

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "order_id": order_id,
            "created_at": now,
            "user_id": user.id,
            "cosmo_user_id": _cosmo_id(user.id),
            "room_type": room_type,
            "direction": direction,
            "image_data_url": data_url,
            "data_url": data_url,
            "purchase_id": purchase_id or None,
            "amount_inr": amount_inr,
            "sku": sku,
            "status": "pending",
            "delivery": "founder_manual_vastu_report",
            "urgent": urgent,
            "priority_fee_inr": 149 if urgent else 0,
            "eta_hours": 12 if urgent else 144,
            "eta_label": (
                "⚡ Priority — deliver within 12 hours"
                if urgent
                else "📦 Standard — 4–6 business days"
            ),
        }
        if not purchase_id:
            record["payment_bypassed"] = True
        _save_order(record)

        return jsonify({
            "ok": True,
            "order_id": order_id,
            "status": "pending",
            "message": (
                "Photo received. Priority report within 12 hours."
                if urgent
                else "Photo received. Our Vastu expert will review and add your report in 4–6 business days."
            ),
            "eta_hours": 12 if urgent else 144,
        }), 200
