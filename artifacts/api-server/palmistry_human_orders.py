"""Palmistry two-hand extraction — founder PDF Requests queue."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from vedic.palm_scan.validation_gate import evaluate_bilateral, evaluate_hand

_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "palmistry_human_orders")
)
_SEQ_FILE = os.path.join(_BASE, "_public_seq.json")
_lock = threading.Lock()
_PUBLIC_PREFIX = "PALM"
_PUBLIC_START = 1001


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def allocate_public_order_id() -> str:
    """Serial public id per request: PALM-1001, PALM-1002, … (file counter)."""
    _ensure_dir()
    with _lock:
        nxt = _PUBLIC_START
        try:
            if os.path.isfile(_SEQ_FILE):
                with open(_SEQ_FILE, encoding="utf-8") as fh:
                    data = json.load(fh)
                nxt = int(data.get("next") or _PUBLIC_START)
                if nxt < _PUBLIC_START:
                    nxt = _PUBLIC_START
        except Exception:
            nxt = _PUBLIC_START
        code = f"{_PUBLIC_PREFIX}-{nxt}"
        try:
            with open(_SEQ_FILE, "w", encoding="utf-8") as fh:
                json.dump({"next": nxt + 1, "updated_at": _now()}, fh)
        except Exception:
            # Counter write failed — still return a unique-looking fallback.
            return f"{_PUBLIC_PREFIX}-{uuid.uuid4().hex[:8].upper()}"
        return code


def get_order(order_id: str) -> dict[str, Any] | None:
    oid = (order_id or "").strip()
    if not oid:
        return None
    path = os.path.join(_BASE, f"{oid}.json")
    if not os.path.isfile(path):
        try:
            names = os.listdir(_BASE)
        except OSError:
            return None
        # UUID prefix match OR public_order_id exact match (PALM-1001).
        matches = [
            n for n in names
            if n.endswith(".json") and n.replace(".json", "").startswith(oid)
        ]
        if len(matches) != 1:
            for n in names:
                if not n.endswith(".json") or n.startswith("_"):
                    continue
                try:
                    with open(os.path.join(_BASE, n), encoding="utf-8") as fh:
                        rec = json.load(fh)
                except Exception:
                    continue
                if not isinstance(rec, dict):
                    continue
                pub = str(rec.get("public_order_id") or "").strip().upper()
                if pub and pub == oid.upper():
                    return rec
            return None
        path = os.path.join(_BASE, matches[0])
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def save_order_record(record: dict[str, Any], *, alert: bool = False) -> str:
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, default=str)
    if alert:
        try:
            from admin_push import notify_admin_push_lifemap_order

            notify_admin_push_lifemap_order(record, kind_label="Palmistry")
        except Exception as exc:
            print(f"[palmistry_human_order] founder alert failed: {exc}", flush=True)
    return oid


def _hand_summary(scan: dict[str, Any] | None, side: str) -> dict[str, Any]:
    scan = scan if isinstance(scan, dict) else {}
    quality = scan.get("quality") if isinstance(scan.get("quality"), dict) else {}
    confidence = scan.get("scan_confidence") if isinstance(scan.get("scan_confidence"), dict) else {}
    master = scan.get("master_extraction") if isinstance(scan.get("master_extraction"), dict) else {}
    production = scan.get("production_validation") if isinstance(scan.get("production_validation"), dict) else evaluate_hand(scan, required_hand_side=side)
    return {
        "side": side,
        "scan_id": (scan.get("metadata") or {}).get("scan_id"),
        "quality_score": quality.get("score") or quality.get("overall_score"),
        "usable": bool(quality.get("usable")),
        "confidence": confidence.get("overall") or confidence.get("value"),
        "validation_status": production.get("status"),
        "validation_message": production.get("user_message"),
        "stage_scores": production.get("stage_scores") or {},
        "annotated_image_reference": scan.get("annotated_image_reference"),
        "original_image_reference": scan.get("original_decoded_image_reference"),
        "has_master_extraction": bool(master),
        "major_line_count": len([
            name for name, line in (scan.get("major_lines") or {}).items()
            if isinstance(line, dict) and line.get("status") in {"detected", "ambiguous"}
        ]),
    }


def create_order(
    *,
    session_id: str,
    writing_hand: str,
    left: dict[str, Any],
    right: dict[str, Any],
    comparison: dict[str, Any] | None,
    user_id: str | None,
    cosmo_user_id: str | None,
    name: str | None,
    urgent: bool = False,
    plan: str = "pdf",
    amount_inr: int | None = None,
    contact_method: str | None = None,
    contact_value: str | None = None,
    purchase_id: int | None = None,
    lang: str | None = None,
) -> dict[str, Any]:
    bilateral_validation = evaluate_bilateral(left, right, writing_hand=writing_hand)
    if bilateral_validation["status"] != "verified":
        raise ValueError(bilateral_validation["user_message"])
    left = dict(left)
    right = dict(right)
    left["production_validation"] = bilateral_validation["left"]
    right["production_validation"] = bilateral_validation["right"]
    uid = 0
    try:
        uid = int(user_id or 0)
    except (TypeError, ValueError):
        uid = 0
    method = (contact_method or "").strip().lower()
    value = (contact_value or "").strip()
    if plan == "vip":
        method = "whatsapp"
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits.startswith("91") and len(digits) >= 12:
            digits = digits[2:]
        if len(digits) != 10:
            raise ValueError("Video explanation requires a valid 10-digit WhatsApp number.")
        value = digits
    if method not in {"my_reports", "whatsapp"}:
        method = "my_reports"
    if method == "my_reports":
        value = str(uid) if uid else ""
    plan_norm = (plan or "pdf").strip().lower()
    if plan_norm not in {"pdf", "vip"}:
        plan_norm = "pdf"
    is_video = plan_norm == "vip"
    deliverable = "video" if is_video else "report"
    label = (
        "Palmistry Personalized Video (WhatsApp · no PDF/report)"
        if is_video
        else "Palmistry Pro Report (PDF)"
    )
    total_inr = int(amount_inr or 0)
    # Priority ₹299 for both PDF and Video (matches mobile palmistryProOffer)
    priority_fee = 0
    if urgent:
        priority_fee = 299
        if total_inr <= 0:
            base = 2999 if is_video else 1499
            total_inr = base + priority_fee
    elif total_inr <= 0:
        total_inr = 2999 if is_video else 1499
    eta_hours = 12 if urgent else 144
    eta_label = (
        "⚡ Priority — deliver within 12 hours"
        if urgent
        else "📦 Standard — 4–6 business days"
    )
    lang_norm = str(lang or "en").strip().lower()
    if lang_norm in ("hinglish", "hindi_english"):
        lang_norm = "hn"
    if lang_norm not in ("en", "hn", "hi"):
        lang_norm = "en"
    # VIP video has no PDF language — keep en as neutral default.
    if is_video:
        lang_norm = "en"
    record = {
        "order_id": str(uuid.uuid4()),
        "public_order_id": allocate_public_order_id(),
        "kind": "palmistry",
        "label": label,
        "status": "pending",
        "urgent": bool(urgent),
        "plan": plan_norm,
        "lang": lang_norm,
        "amount_inr": total_inr,
        "priority_fee_inr": priority_fee,
        "eta_hours": eta_hours,
        "eta_label": eta_label,
        "deliverable": deliverable,
        "delivery": "whatsapp_video_explanation" if is_video else "founder_manual_pdf",
        "created_at": _now(),
        "updated_at": _now(),
        "session_id": session_id,
        "writing_hand": writing_hand,
        "user_id": uid,
        "cosmo_user_id": (cosmo_user_id or "").strip(),
        "user_name": (name or "").strip(),
        "subject": (name or "Palm scan").strip() or "Palm scan",
        "contact_method": method,
        "contact_value": value,
        "purchase_id": int(purchase_id or 0) or None,
        "left_palm_scan_result": left,
        "right_palm_scan_result": right,
        "bilateral_comparison": comparison,
        "left_summary": _hand_summary(left, "left"),
        "right_summary": _hand_summary(right, "right"),
        "production_validation": bilateral_validation,
        "overall_scan_status": bilateral_validation["overall_status"],
        "overall_confidence": bilateral_validation["overall_confidence"],
        "validation_version": bilateral_validation["validation_version"],
        "processing_version": (left.get("metadata") or {}).get("engine") or "palm_scan_phase1",
        "requires_retake": False,
        "schema_version": "palmistry_admin_case/1.0",
        "extraction_engine": "palm_scan_phase1",
        "extraction_schema": (left.get("schema_version") if isinstance(left, dict) else None) or "1.0",
        "master_schema": (
            (left.get("master_extraction") or {}).get("schema_version")
            if isinstance(left, dict) else None
        ),
        "rule_engine_version": "palmistry_phase2/1.0",
        "correction_history": [],
        "human_overlays": {},
        "machine_original_preserved": True,
        "media": {"left": [], "right": []},
    }
    save_order_record(record, alert=True)
    return record


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
        rec_status = str(rec.get("status") or "pending").lower()
        if status_filter and rec_status != status_filter:
            continue
        try:
            rows.append(to_lifemap_row(rec))
        except Exception as exc:
            print(
                f"[palmistry_human_orders] skip bad order {fn}: {exc}",
                flush=True,
            )
            continue
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
    """Pending / in-progress palmistry orders for My Reports (before PDF ready)."""
    uid = 0
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
                is_video = str(row.get("deliverable") or "").lower() == "video" or str(
                    row.get("plan") or ""
                ).lower() == "vip"
                pub = str(row.get("public_order_id") or "").strip()
                oid = str(row.get("order_id") or "").strip()
                name = str(row.get("user_name") or row.get("subject") or "Palmistry").strip()
                out.append({
                    "id": pub or oid,
                    "order_id": oid,
                    "public_order_id": pub,
                    "kind": "palmistry_pro",
                    "status": "pending",
                    "deliverable": "video" if is_video else "report",
                    "report_type": (
                        "Palmistry Video Explanation"
                        if is_video
                        else "Palmistry Pro Report"
                    ),
                    "name": name,
                    "eta_label": row.get("eta_label") or "",
                    "date": row.get("created_at"),
                    "title": (
                        f"{name} — Video (WhatsApp)"
                        if is_video
                        else f"{name} — Palmistry Report"
                    ),
                })
            page_num += 1
    except Exception:
        return out
    return out


def find_order_ids_for_report(report_id: str) -> tuple[str, str]:
    """Reverse-lookup order_id / public_order_id from a delivered report_id."""
    rid = (report_id or "").strip()
    if not rid:
        return "", ""
    _ensure_dir()
    try:
        names = os.listdir(_BASE)
    except OSError:
        return "", ""
    for fn in names:
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        try:
            with open(os.path.join(_BASE, fn), encoding="utf-8") as fh:
                rec = json.load(fh)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        if str(rec.get("report_id") or "").strip() == rid:
            return (
                str(rec.get("order_id") or "").strip(),
                str(rec.get("public_order_id") or "").strip(),
            )
    return "", ""


def purchase_already_used(purchase_id: int) -> bool:
    if not purchase_id:
        return False
    _ensure_dir()
    try:
        names = os.listdir(_BASE)
    except OSError:
        return False
    for fn in names:
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        try:
            with open(os.path.join(_BASE, fn), encoding="utf-8") as fh:
                rec = json.load(fh)
            if int(rec.get("purchase_id") or 0) == int(purchase_id):
                return True
        except Exception:
            continue
    return False


def to_lifemap_row(rec: dict[str, Any]) -> dict[str, Any]:
    uid = int(rec.get("user_id") or 0)
    cosmo = str(rec.get("cosmo_user_id") or "").strip()
    if not cosmo and uid:
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo = cosmo_display_id_for_user_id(uid)
        except Exception:
            cosmo = ""
    name = str(rec.get("user_name") or rec.get("subject") or "").strip()
    plan = str(rec.get("plan") or "pdf").strip().lower()
    deliverable = str(
        rec.get("deliverable") or ("video" if plan == "vip" else "report")
    ).strip().lower()
    is_video = deliverable == "video" or plan == "vip"
    label = str(rec.get("label") or "").strip()
    if not label or label == "Palmistry":
        label = (
            "Palmistry Personalized Video (WhatsApp · no PDF/report)"
            if is_video
            else "Palmistry Pro Report (PDF)"
        )
    urgent = bool(rec.get("urgent"))
    amount = int(rec.get("amount_inr") or 0)
    priority_fee = int(rec.get("priority_fee_inr") or 0)
    if urgent and priority_fee <= 0:
        priority_fee = 299
    # Backfill amount for older orders that never stored price
    if amount <= 0:
        base = 2999 if is_video else 1499
        amount = base + (priority_fee if urgent else 0)
    eta_label = str(rec.get("eta_label") or "").strip()
    if not eta_label:
        eta_label = (
            "⚡ Priority — deliver within 12 hours"
            if urgent
            else "📦 Standard — 4–6 business days"
        )
    eta_hours = rec.get("eta_hours")
    if eta_hours in (None, ""):
        eta_hours = 12 if urgent else 144
    detail_bits = [
        eta_label,
        f"₹{amount}",
        "🎥 WhatsApp video · no PDF/report" if is_video else f"📄 PDF · writing hand {rec.get('writing_hand') or '—'}",
    ]
    return {
        "kind": "palmistry",
        "label": label,
        "order_id": rec.get("order_id") or "",
        "public_order_id": str(rec.get("public_order_id") or "").strip(),
        "created_at": rec.get("created_at"),
        "status": rec.get("status") or "pending",
        "lang": str(rec.get("lang") or "en").strip().lower() or "en",
        "urgent": urgent,
        "plan": plan,
        "deliverable": "video" if is_video else "report",
        "amount_inr": amount,
        "priority_fee_inr": priority_fee,
        "eta_hours": eta_hours,
        "eta_label": eta_label,
        "contact_method": rec.get("contact_method") or ("whatsapp" if is_video else "my_reports"),
        "contact_value": rec.get("contact_value") or "",
        "user_id": uid,
        "cosmo_user_id": cosmo,
        "user_name": name,
        "subject": name or "Palm scan",
        "detail": " · ".join(b for b in detail_bits if b),
        "admin_accepted_at": rec.get("admin_accepted_at"),
        "admin_accepted": bool(rec.get("admin_accepted_at")),
        "writing_hand": rec.get("writing_hand"),
        "session_id": rec.get("session_id"),
        "production_validation": rec.get("production_validation") or {},
        "left_summary": rec.get("left_summary") or {},
        "right_summary": rec.get("right_summary") or {},
        "has_full_extraction": bool(
            rec.get("left_palm_scan_result") and rec.get("right_palm_scan_result")
        ),
        "overall_status": rec.get("overall_scan_status") or rec.get("status") or "pending",
        "overall_confidence": rec.get("overall_confidence"),
        "has_media": bool((rec.get("media") or {}).get("left") or (rec.get("media") or {}).get("right")),
    }


def save_hand_media(order_id: str, hand: str, artifacts: dict[str, bytes]) -> list[str]:
    if hand not in {"left", "right"} or not artifacts:
        return []
    folder = os.path.join(_BASE, "media", order_id, hand)
    os.makedirs(folder, exist_ok=True)
    saved = []
    for name, payload in artifacts.items():
        safe = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_"})[:80]
        if not safe or not payload:
            continue
        path = os.path.join(folder, f"{safe}.png")
        with _lock:
            with open(path, "wb") as fh:
                fh.write(payload)
        saved.append(safe)
    rec = get_order(order_id)
    if rec is not None:
        media = rec.get("media") if isinstance(rec.get("media"), dict) else {"left": [], "right": []}
        media[hand] = sorted(set((media.get(hand) or []) + saved))
        rec["media"] = media
        save_order_record(rec)
    return saved


def media_path(order_id: str, hand: str, name: str) -> str | None:
    safe_order = "".join(ch for ch in order_id if ch.isalnum() or ch in {"-", "_"})[:80]
    safe_hand = hand if hand in {"left", "right"} else ""
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_"})[:80]
    if not safe_order or not safe_hand or not safe_name:
        return None
    path = os.path.join(_BASE, "media", safe_order, safe_hand, f"{safe_name}.png")
    return path if os.path.isfile(path) else None


def append_correction(order_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    rec = get_order(order_id)
    if rec is None:
        return None
    action = str(payload.get("action") or "note").strip().lower()
    if action not in {"confirm", "reject", "ambiguous", "correct", "note"}:
        action = "note"
    entry = {
        "correction_id": str(uuid.uuid4()),
        "changed_at": _now(),
        "changed_by": str(payload.get("changed_by") or "admin"),
        "reason": payload.get("reason") or "",
        "action": action,
        "hand_side": payload.get("hand_side"),
        "feature_path": payload.get("feature_path"),
        "feature_id": payload.get("feature_id"),
        "machine_original": payload.get("machine_original"),
        "human_corrected": payload.get("human_corrected"),
    }
    history = list(rec.get("correction_history") or [])
    history.append(entry)
    rec["correction_history"] = history
    overlays = rec.get("human_overlays") if isinstance(rec.get("human_overlays"), dict) else {}
    key = str(payload.get("feature_path") or payload.get("feature_id") or entry["correction_id"])
    overlays[key] = {
        "action": action,
        "human_corrected": payload.get("human_corrected"),
        "changed_at": entry["changed_at"],
        "changed_by": entry["changed_by"],
        "reason": entry["reason"],
    }
    rec["human_overlays"] = overlays
    rec["updated_at"] = _now()
    rec["status"] = "human_verified" if action in {"confirm", "correct", "reject", "ambiguous"} else rec.get("status")
    save_order_record(rec)
    return rec


def export_package(order_id: str) -> dict[str, Any] | None:
    rec = get_order(order_id)
    if rec is None:
        return None
    left = rec.get("left_palm_scan_result") or {}
    right = rec.get("right_palm_scan_result") or {}
    return {
        "schema_version": "palmistry_admin_export/1.0",
        "case_id": rec.get("order_id"),
        "session_id": rec.get("session_id"),
        "user_id": rec.get("user_id"),
        "cosmo_user_id": rec.get("cosmo_user_id"),
        "writing_hand": rec.get("writing_hand"),
        "created_at": rec.get("created_at"),
        "extraction_engine": rec.get("extraction_engine"),
        "extraction_schema": rec.get("extraction_schema"),
        "master_schema": rec.get("master_schema"),
        "rule_engine_version": rec.get("rule_engine_version"),
        "left_palm_scan_result": left,
        "right_palm_scan_result": right,
        "bilateral_comparison": rec.get("bilateral_comparison"),
        "verified_corrections": rec.get("correction_history") or [],
        "human_overlays": rec.get("human_overlays") or {},
        "machine_original_preserved": True,
        "confidence": {
            "left": (left.get("scan_confidence") if isinstance(left, dict) else None),
            "right": (right.get("scan_confidence") if isinstance(right, dict) else None),
        },
        "production_validation": rec.get("production_validation") or {},
        "image_references": {
            "left": (left.get("original_decoded_image_reference") if isinstance(left, dict) else None),
            "right": (right.get("original_decoded_image_reference") if isinstance(right, dict) else None),
        },
        "annotated_image_references": {
            "left": (left.get("annotated_image_reference") if isinstance(left, dict) else None),
            "right": (right.get("annotated_image_reference") if isinstance(right, dict) else None),
        },
        "persisted_media": rec.get("media") or {},
        "interpretation_excluded": True,
    }
