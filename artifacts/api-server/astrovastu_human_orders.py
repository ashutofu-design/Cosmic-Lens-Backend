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
        if status_filter and str(rec.get("status") or "").lower() != status_filter:
            continue
        preview = rec.get("image_data_url") or rec.get("data_url") or ""
        rows.append({
            "order_id": rec.get("order_id"),
            "created_at": rec.get("created_at"),
            "user_id": rec.get("user_id"),
            "cosmo_user_id": rec.get("cosmo_user_id"),
            "room_type": rec.get("room_type"),
            "direction": rec.get("direction"),
            "purchase_id": rec.get("purchase_id"),
            "amount_inr": rec.get("amount_inr"),
            "status": rec.get("status") or "pending",
            "has_image": bool(preview),
            "image_preview": (preview[:80] + "…") if isinstance(preview, str) and len(preview) > 80 else preview,
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


def _purchase_already_used(purchase_id: int) -> bool:
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


def register_astrovastu_human_order_routes(flask_app) -> None:
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
        if purchase.status != "paid":
            return jsonify({"error": "payment_not_confirmed"}), 402
        if purchase.sku not in _MANUAL_ROOM_SKUS:
            return jsonify({"error": "wrong_sku_for_manual_upload"}), 400
        if _purchase_already_used(purchase_id):
            return jsonify({"error": "purchase_already_submitted"}), 409

        cosmo_user_id = ""
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo_user_id = cosmo_display_id_for_user_id(user.id)
        except Exception:
            cosmo_user_id = ""

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "order_id": order_id,
            "created_at": now,
            "user_id": user.id,
            "cosmo_user_id": cosmo_user_id,
            "room_type": room_type,
            "direction": direction,
            "image_data_url": data_url,
            "data_url": data_url,
            "purchase_id": purchase_id,
            "amount_inr": purchase.amount,
            "sku": purchase.sku,
            "status": "pending",
            "delivery": "founder_manual_vastu_report",
        }
        _save_order(record)

        return jsonify({
            "ok": True,
            "order_id": order_id,
            "status": "pending",
            "message": "Photo received. Our Vastu expert will review and add your report within 24–48 hours.",
            "eta_hours": 48,
        }), 200
