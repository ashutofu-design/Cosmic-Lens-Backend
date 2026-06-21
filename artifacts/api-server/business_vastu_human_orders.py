"""Business Vastu — shop/office/factory photo + PDF uploads for founder manual review."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "business_vastu_human_orders")
)
_lock = threading.Lock()


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
            f"[business_vastu_human_order] saved id={oid} "
            f"type={record.get('business_type')} "
            f"property={record.get('property_name')} "
            f"photos={len(record.get('room_photos') or [])}",
            flush=True,
        )
    except Exception:
        pass
    try:
        from order_founder_alert import notify_founder_business_vastu_order

        notify_founder_business_vastu_order(record)
    except Exception as exc:
        try:
            print(f"[business_vastu_human_order] founder alert failed: {exc}", flush=True)
        except Exception:
            pass
    return oid


def _load_order(order_id: str) -> dict[str, Any] | None:
    _ensure_dir()
    path = os.path.join(_BASE, f"{order_id}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def list_business_vastu_orders(
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
        photos = rec.get("room_photos") if isinstance(rec.get("room_photos"), list) else []
        fp = rec.get("floor_plan_upload") if isinstance(rec.get("floor_plan_upload"), dict) else None
        rows.append(
            {
                "order_id": rec.get("order_id"),
                "created_at": rec.get("created_at"),
                "user_id": rec.get("user_id"),
                "cosmo_user_id": rec.get("cosmo_user_id"),
                "business_type": rec.get("business_type"),
                "property_name": rec.get("property_name"),
                "photo_count": len(photos),
                "has_pdf": bool(fp),
                "pdf_filename": (fp or {}).get("filename") if fp else None,
                "status": rec.get("status") or "pending",
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


def get_business_vastu_order(order_id: str) -> dict[str, Any] | None:
    return _load_order(order_id)


def register_business_vastu_human_order_routes(flask_app) -> None:
    @flask_app.route("/api/business-vastu/submit-order", methods=["POST", "OPTIONS"])
    def business_vastu_submit_order():
        if request.method == "OPTIONS":
            return "", 204

        from models import User

        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        api_key = (request.headers.get("X-API-Key") or "").strip()
        if not user_id or not api_key:
            return jsonify({"error": "auth_required"}), 401
        user = User.query.filter_by(id=user_id, api_key=api_key).first()
        if not user:
            return jsonify({"error": "invalid_credentials"}), 401

        btype = (data.get("business_type") or "").strip().lower()
        if btype not in ("shop", "office", "factory"):
            return jsonify({"error": "invalid_business_type"}), 400

        property_name = (data.get("property_name") or "").strip()
        if not property_name:
            return jsonify({"error": "property_name_required"}), 400

        room_photos = data.get("room_photos")
        if not isinstance(room_photos, list):
            room_photos = []
        fp_upload = data.get("floor_plan_upload")
        has_fp = isinstance(fp_upload, dict) and (
            fp_upload.get("data_url") or fp_upload.get("base64")
        )
        if len(room_photos) < 2 and not has_fp:
            return jsonify({"error": "photos_or_pdf_required"}), 400

        cleaned_photos: list[dict[str, Any]] = []
        for i, p in enumerate(room_photos[:6]):
            if not isinstance(p, dict):
                continue
            room_type = (p.get("room_type") or "").strip()
            img = (p.get("image_data_url") or p.get("data_url") or "").strip()
            if not room_type or not img:
                continue
            entry: dict[str, Any] = {"room_type": room_type, "image_data_url": img}
            if isinstance(p.get("heading_deg"), (int, float)):
                entry["heading_deg"] = float(p["heading_deg"])
            cleaned_photos.append(entry)

        if len(cleaned_photos) < 2 and not has_fp:
            return jsonify({"error": "photos_or_pdf_required"}), 400

        floor_plan_upload = None
        if has_fp:
            floor_plan_upload = {
                "type": fp_upload.get("type") or "pdf",
                "north_at": fp_upload.get("north_at") or "top",
            }
            if fp_upload.get("filename"):
                floor_plan_upload["filename"] = fp_upload["filename"]
            if fp_upload.get("data_url"):
                floor_plan_upload["data_url"] = fp_upload["data_url"]
            if fp_upload.get("base64"):
                floor_plan_upload["base64"] = fp_upload["base64"]

        cosmo_user_id = ""
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo_user_id = cosmo_display_id_for_user_id(user.id)
        except Exception:
            cosmo_user_id = ""

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record: dict[str, Any] = {
            "order_id": order_id,
            "created_at": now,
            "user_id": user.id,
            "cosmo_user_id": cosmo_user_id,
            "business_type": btype,
            "property_name": property_name,
            "room_photos": cleaned_photos,
            "status": "pending",
            "delivery": "founder_manual_business_vastu_report",
        }
        if floor_plan_upload:
            record["floor_plan_upload"] = floor_plan_upload

        _save_order(record)

        return jsonify(
            {
                "ok": True,
                "order_id": order_id,
                "status": "pending",
                "message": (
                    "Photos received. Our Vastu expert will review your shop "
                    "and prepare your report within 24–48 hours."
                ),
                "eta_hours": 48,
            }
        ), 200
