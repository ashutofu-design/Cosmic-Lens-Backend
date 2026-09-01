"""Business Vastu — shop/office/factory photo + PDF uploads for founder manual review."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

from api_auth import authed_user_from_request

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
        photo_rooms: list[dict[str, Any]] = []
        for p in photos:
            if not isinstance(p, dict):
                continue
            photo_rooms.append(
                {
                    "room_type": str(p.get("room_type") or "").strip(),
                    "heading_deg": p.get("heading_deg"),
                }
            )
        rows.append(
            {
                "order_id": rec.get("order_id"),
                "created_at": rec.get("created_at"),
                "user_id": rec.get("user_id"),
                "cosmo_user_id": rec.get("cosmo_user_id"),
                "business_type": rec.get("business_type"),
                "property_name": rec.get("property_name"),
                "photo_count": len(photos),
                "photo_rooms": photo_rooms,
                "has_pdf": bool(fp),
                "pdf_filename": (fp or {}).get("filename") if fp else None,
                "status": rec.get("status") or "pending",
                "admin_accepted_at": rec.get("admin_accepted_at"),
                "urgent": bool(rec.get("urgent")),
                "amount_inr": rec.get("amount_inr"),
                "priority_fee_inr": rec.get("priority_fee_inr"),
                "eta_hours": rec.get("eta_hours"),
                "eta_label": rec.get("eta_label"),
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
    """Pending Business Vastu orders for My Reports (before PDF ready)."""
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
            page = list_business_vastu_orders(page=page_num, per_page=100, status=None)
            pages = max(1, int(page.get("pages") or 1))
            for row in page.get("orders") or []:
                if int(row.get("user_id") or 0) != uid:
                    continue
                st = str(row.get("status") or "pending").lower()
                if st in ("delivered", "cancelled", "canceled", "deleted"):
                    continue
                oid = str(row.get("order_id") or "").strip()
                pub = str(row.get("public_order_id") or "").strip() or (oid[:8].upper() if oid else "")
                name = (
                    str(row.get("property_name") or "").strip()
                    or str(row.get("business_type") or "").strip()
                    or "Business Vastu"
                )
                out.append({
                    "id": pub or oid,
                    "order_id": oid,
                    "public_order_id": pub,
                    "kind": "business_vastu",
                    "status": "pending",
                    "deliverable": "report",
                    "report_type": "Business Vastu Report",
                    "name": name,
                    "eta_label": row.get("eta_label") or "",
                    "date": row.get("created_at"),
                    "title": f"{name} — Business Vastu Report",
                })
            page_num += 1
    except Exception:
        return out
    return out


def get_business_vastu_order(order_id: str) -> dict[str, Any] | None:
    return _load_order(order_id)


def get_order(order_id: str) -> dict[str, Any] | None:
    """Load by uuid or unique prefix (admin accept/deliver paths)."""
    oid = (order_id or "").strip()
    if not oid:
        return None
    rec = _load_order(oid)
    if rec:
        return rec
    _ensure_dir()
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
    return _load_order(matches[0].replace(".json", ""))


def save_order_record(record: dict[str, Any]) -> str:
    """Update an existing order WITHOUT re-sending the founder alert."""
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    return oid


def register_business_vastu_human_order_routes(flask_app) -> None:
    @flask_app.route("/api/business-vastu/submit-order", methods=["POST", "OPTIONS"])
    def business_vastu_submit_order():
        if request.method == "OPTIONS":
            return "", 204

        from models import User

        data = request.get_json(silent=True) or {}
        user, err = authed_user_from_request(data)
        if err:
            return err

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
        if len(room_photos) < 1 and not has_fp:
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

        if len(cleaned_photos) < 1 and not has_fp:
            return jsonify({"error": "photos_or_pdf_required"}), 400

        urgent = bool(data.get("urgent"))

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
            "urgent": urgent,
            "priority_fee_inr": 149 if urgent else 0,
            "eta_hours": 12 if urgent else 144,
            "eta_label": (
                "⚡ Priority — deliver within 12 hours"
                if urgent
                else "📦 Standard — 4–6 business days"
            ),
        }
        if floor_plan_upload:
            record["floor_plan_upload"] = floor_plan_upload

        import business_vastu_billing as _bvb

        upload_mode = "pdf" if floor_plan_upload else "photos"
        room_count = len(cleaned_photos) if upload_mode == "photos" else 0
        cp = _bvb.cache_params(
            btype,
            property_name,
            urgent,
            upload_mode=upload_mode,
            room_count=room_count or 1,
        )
        raw_pid = data.get("purchase_id")
        purchase_id = None
        try:
            if raw_pid is not None and str(raw_pid).strip() != "":
                purchase_id = int(raw_pid)
        except (TypeError, ValueError):
            purchase_id = None
        paid_ok, pay_err = _bvb.require_paid_for_submit(user.id, cp, purchase_id)
        if not paid_ok:
            return jsonify(pay_err or {"error": "payment_required"}), 402

        record["purchase_id"] = purchase_id
        record["params_hash"] = _bvb.params_hash(cp)
        record["upload_mode"] = upload_mode
        record["room_count"] = room_count
        record["amount_inr"] = (
            0
            if _bvb.payment_bypass()
            else _bvb.amount_for(btype, urgent, upload_mode, room_count or 1)
        )

        # Optional override from client only when bypass (ignore client amount otherwise)
        if _bvb.payment_bypass():
            try:
                amt = int(data.get("amount_inr") or 0)
                if amt > 0:
                    record["amount_inr"] = amt
            except (TypeError, ValueError):
                pass

        _save_order(record)

        return jsonify(
            {
                "ok": True,
                "order_id": order_id,
                "status": "pending",
                "message": (
                    "Photos received. Priority report within 12 hours."
                    if urgent
                    else "Photos received. Our Vastu expert will review your shop and prepare your report in 4–6 business days."
                ),
                "eta_hours": 12 if urgent else 144,
            }
        ), 200
