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
        digits = re.sub(r"\D", "", raw)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
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
    return oid


def register_human_order_routes(flask_app) -> None:
    """Register engine snapshot + human PDF order routes."""

    if "love_reality_engine_snapshot" in flask_app.view_functions:
        return

    @flask_app.route("/api/love-reality/engine-snapshot", methods=["POST", "OPTIONS"])
    def love_reality_engine_snapshot():
        if request.method == "OPTIONS":
            return "", 204
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
    def love_reality_human_order():
        if request.method == "OPTIONS":
            return "", 204
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("p1"), dict) or not isinstance(data.get("p2"), dict):
            return jsonify({"error": "expected_p1_p2"}), 400

        method = str(data.get("contact_method") or "").strip().lower()
        contact, err = _normalize_contact(method, str(data.get("contact_value") or ""))
        if err:
            return jsonify({"error": err}), 400

        lang = str(data.get("lang") or "en").strip().lower() or "en"
        urgent = bool(data.get("urgent"))

        user_id = 0
        uid_hdr = (request.headers.get("X-User-Id") or "").strip()
        if uid_hdr:
            try:
                user_id = int(uid_hdr)
            except Exception:
                user_id = 0

        try:
            from vedic.love_reality.compute_bundle import compute_love_reality_bundle

            bundle = compute_love_reality_bundle(
                flask_app, data["p1"], data["p2"], skip_ai_insight=True
            )
            snap = build_engine_snapshot(bundle)
        except Exception as exc:
            return jsonify({"error": "engine_snapshot_failed", "detail": str(exc)}), 500

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "order_id": order_id,
            "created_at": now,
            "user_id": user_id,
            "lang": lang,
            "urgent": urgent,
            "contact_method": method,
            "contact_value": contact,
            "p1": data["p1"],
            "p2": data["p2"],
            "engine_snapshot": snap,
            "status": "pending",
            "delivery": "founder_manual_pdf",
        }
        _save_order(record)

        eta_hours = 12 if urgent else 48
        return jsonify({
            "ok": True,
            "order_id": order_id,
            "eta_hours": eta_hours,
            "message": (
                "Order received. Our astrologer will prepare your verified PDF "
                f"and send it on {method}."
            ),
        }), 200
