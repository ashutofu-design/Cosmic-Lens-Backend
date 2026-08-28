"""Small Flask Blueprint for the Phase 1 palm scanner."""
from __future__ import annotations

import os
from collections import OrderedDict
import logging
from threading import Lock
from typing import Callable

import cv2
import numpy as np
from flask import Blueprint, Response, jsonify, request

from .engine import PalmScanEngine
from .master_layer import attach_master_extraction, compose_bilateral_comparison
from . import store as palm_store
from .validation_gate import evaluate_bilateral, evaluate_hand

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
_ARTIFACTS: OrderedDict[str, dict[str, bytes]] = OrderedDict()
_ANNOTATIONS_LOCK = Lock()
_MAX_SCANS = 32
_LOG = logging.getLogger(__name__)


def _admin_error():
    if (os.environ.get("ADMIN_NO_AUTH") or "0").strip().lower() in {"1", "true", "yes", "on"}:
        return None
    admin_secret = os.environ.get("ADMIN_SECRET", "").strip()
    if not admin_secret:
        return jsonify({"error": "Admin auth is not configured"}), 503
    token = request.headers.get("X-Admin-Token", "")
    if not token or token != admin_secret:
        return jsonify({"error": "Unauthorized"}), 401
    return None


def _json_safe(value):
    """Convert numpy scalars/arrays so Flask jsonify does not 500."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _artifact_bundle(scan_id: str) -> dict[str, bytes]:
    with _ANNOTATIONS_LOCK:
        return dict(_ARTIFACTS.get(scan_id) or {})


def _store_artifacts(scan_id: str, artifacts: dict) -> None:
    encoded_artifacts = {}
    for name, image in artifacts.items():
        if image is None:
            continue
        value = image
        if name not in {"annotated"} and getattr(value, "ndim", 0) == 3:
            value = cv2.cvtColor(value, cv2.COLOR_RGB2BGR)
        ok, encoded = cv2.imencode(".png", value)
        if ok:
            encoded_artifacts[name] = encoded.tobytes()
    with _ANNOTATIONS_LOCK:
        _ARTIFACTS[scan_id] = encoded_artifacts
        _ARTIFACTS.move_to_end(scan_id)
        while len(_ARTIFACTS) > _MAX_SCANS:
            _ARTIFACTS.popitem(last=False)


def _stamp_production_validation(result: dict, *, required_hand_side: str | None = None) -> dict:
    evaluation = evaluate_hand(result, required_hand_side=required_hand_side)
    result["production_validation"] = evaluation
    validation = result.get("validation") or {}
    result["validation"] = {
        **validation,
        "production_status": evaluation["status"],
        "production_rejection_reasons": evaluation["rejection_reasons"],
        "production_user_message": evaluation["user_message"],
        "validation_version": evaluation["validation_version"],
    }
    metadata = result.get("metadata") or {}
    result["metadata"] = {
        **metadata,
        "validation_version": evaluation["validation_version"],
    }
    return evaluation


def create_palm_scan_blueprint(
    *,
    engine: PalmScanEngine | None = None,
    rate_limit: Callable[[str], Callable] | None = None,
) -> Blueprint:
    scanner = engine or PalmScanEngine()
    blueprint = Blueprint("palm_scan", __name__)

    def limit(spec: str):
        return rate_limit(spec) if rate_limit else (lambda function: function)

    @blueprint.post("/api/palm-scan")
    @limit("10 per minute")
    def scan_palm():
        upload = request.files.get("image")
        if upload is None:
            return jsonify({
                "error": {"code": "missing_image", "message": "Provide an image multipart field.", "field": "image"}
            }), 400
        content_type = (upload.mimetype or "").lower()
        if content_type and not content_type.startswith("image/"):
            return jsonify({
                "error": {"code": "invalid_content_type", "message": "The image field must have an image content type."}
            }), 415
        payload = upload.stream.read(MAX_UPLOAD_BYTES + 1)
        if len(payload) > MAX_UPLOAD_BYTES:
            return jsonify({
                "error": {"code": "file_too_large", "message": "Image exceeds the 12 MB limit."}
            }), 413
        mirror_value = (request.form.get("mirror") or "false").strip().lower()
        if mirror_value not in {"true", "false", "1", "0"}:
            return jsonify({
                "error": {"code": "invalid_mirror_option", "message": "mirror must be true or false.", "field": "mirror"}
            }), 400
        result, artifacts = scanner.scan_with_artifacts(
            payload, mirror=mirror_value in {"true", "1"}
        )
        if artifacts:
            _store_artifacts(result["metadata"]["scan_id"], artifacts)
        if result["annotated_image_reference"] and "annotated" not in artifacts:
            result["annotated_image_reference"] = None
        hand_slot = (request.form.get("hand_side") or request.form.get("hand") or "").strip().lower()
        writing_hand = (request.form.get("writing_hand") or "").strip().lower()
        session_id = (request.form.get("session_id") or "").strip()
        user_id = (request.form.get("user_id") or "").strip() or None
        if hand_slot not in {"left", "right"}:
            hand_slot = None
        if writing_hand not in {"left", "right"}:
            writing_hand = None
        attach_master_extraction(
            result, writing_hand=writing_hand, hand_slot=hand_slot,
        )
        production_validation = _stamp_production_validation(result, required_hand_side=hand_slot)
        result = _json_safe(result)
        persistable = {key: value for key, value in result.items() if key != "admin_session"}
        if session_id and hand_slot:
            try:
                palm_store.save_hand(
                    session_id=session_id,
                    hand_side=hand_slot,
                    writing_hand=writing_hand,
                    user_id=user_id,
                    result=persistable,
                )
                result["admin_session"] = {
                    "session_id": session_id,
                    "hand_side": hand_slot,
                    "persisted": True,
                    "audit_only": production_validation["status"] != "pass",
                }
            except Exception:
                result["admin_session"] = {"session_id": session_id, "persisted": False}
        if production_validation["status"] != "verified":
            _LOG.info(
                "Palm scan validation %s for scan_id=%s side=%s errors=%s warnings=%s",
                production_validation["status"],
                result.get("metadata", {}).get("scan_id"),
                hand_slot,
                production_validation.get("validation_errors"),
                production_validation.get("validation_warnings"),
            )
        hand = result.get("hand")
        hand_detected = isinstance(hand, dict) and hand.get("status") == "detected"
        if production_validation["status"] == "verified":
            status = 200
        elif hand_detected and result.get("schema_version"):
            # Return analyzable scan payload so clients can show overlays + retake guidance.
            status = 200
        else:
            status = 422
        return jsonify(result), status

    @blueprint.post("/api/palm-scan/session")
    @limit("10 per minute")
    def save_palm_session():
        payload = request.get_json(silent=True) or {}
        session_id = str(payload.get("session_id") or "").strip()
        writing_hand = str(payload.get("writing_hand") or "").strip().lower()
        if not session_id or writing_hand not in {"left", "right"}:
            return jsonify({
                "error": {
                    "code": "invalid_session",
                    "message": "session_id and writing_hand=left|right are required.",
                }
            }), 400
        # Body preferred; X-User-Id fallback (same as numerology / Love Reality).
        resolved_user_id = (
            str(payload.get("user_id") or "").strip()
            or str(request.headers.get("X-User-Id") or "").strip()
            or None
        )
        resolved_cosmo = (
            str(payload.get("cosmo_user_id") or "").strip()
            or str(request.headers.get("X-Cosmo-User-Id") or "").strip()
            or None
        )
        plan_norm = str(payload.get("plan") or "pdf").strip().lower()
        if plan_norm not in {"pdf", "vip"}:
            plan_norm = "pdf"
        # PDF → My Reports needs a real app user; guest uploads cannot be delivered.
        # PDF / VIP both need login for Razorpay + delivery.
        if not resolved_user_id:
            return jsonify({
                "error": {
                    "code": "auth_required",
                    "message": "Login required for Palmistry checkout.",
                },
                "pdf_request": {
                    "ok": False,
                    "error": "Login required — pehle sign in karo.",
                },
            }), 401

        # Razorpay gate — require paid purchase_id (unless payment bypass).
        purchase_id = 0
        try:
            purchase_id = int(payload.get("purchase_id") or 0)
        except (TypeError, ValueError):
            purchase_id = 0
        paid_amount = None
        try:
            import palmistry_report_billing as _prb

            if _prb.payment_required() and not _prb.payment_bypass():
                uid_int = int(resolved_user_id)
                purchase, pay_err = _prb.assert_paid_purchase(
                    uid_int, purchase_id, plan_norm
                )
                if pay_err:
                    msg = {
                        "payment_required": "Payment required before uploading to admin.",
                        "invalid_purchase": "Invalid purchase for this account.",
                        "wrong_product": "Paid product does not match selected plan.",
                        "payment_not_confirmed": "Payment not confirmed yet. Wait a moment and retry.",
                    }.get(pay_err, pay_err)
                    return jsonify({
                        "error": {"code": pay_err, "message": msg},
                        "pdf_request": {"ok": False, "error": msg},
                    }), 402 if pay_err in ("payment_required", "payment_not_confirmed") else 400
                from palmistry_human_orders import purchase_already_used

                if purchase_id and purchase_already_used(purchase_id):
                    return jsonify({
                        "error": {
                            "code": "purchase_already_submitted",
                            "message": "This payment was already used for an order.",
                        },
                        "pdf_request": {
                            "ok": False,
                            "error": "This payment was already used for an order.",
                        },
                    }), 409
                if purchase is not None:
                    paid_amount = int(purchase.amount or 0) or None
        except Exception as pay_exc:
            _LOG.warning("palmistry payment gate failed: %s", pay_exc)

        person = {
            "user_id": resolved_user_id,
            "cosmo_user_id": resolved_cosmo,
            "name": str(payload.get("name") or "") or None,
        }
        left = payload.get("left_palm_scan_result")
        right = payload.get("right_palm_scan_result")
        left_gate = evaluate_hand(left, required_hand_side="left") if isinstance(left, dict) else None
        right_gate = evaluate_hand(right, required_hand_side="right") if isinstance(right, dict) else None
        bilateral_gate = evaluate_bilateral(
            left if isinstance(left, dict) else None,
            right if isinstance(right, dict) else None,
            writing_hand=writing_hand,
        )
        if isinstance(left, dict):
            left["production_validation"] = left_gate
        if isinstance(right, dict):
            right["production_validation"] = right_gate
        comparison = compose_bilateral_comparison(
            left=left if isinstance(left, dict) else {},
            right=right if isinstance(right, dict) else {},
            writing_hand=writing_hand,
        )
        record = None
        if isinstance(left, dict):
            record = palm_store.save_hand(
                session_id=session_id, hand_side="left",
                writing_hand=writing_hand,
                user_id=resolved_user_id,
                result=left,
                person=person,
            )
        if isinstance(right, dict):
            record = palm_store.save_hand(
                session_id=session_id, hand_side="right",
                writing_hand=writing_hand,
                user_id=resolved_user_id,
                result=right,
                person=person,
            )
        if record is not None:
            record["bilateral_comparison"] = comparison
            record["production_validation"] = bilateral_gate
        order = None
        if bilateral_gate["status"] != "verified":
            _LOG.info(
                "Bilateral palm validation %s for session_id=%s issues=%s warnings=%s",
                bilateral_gate["status"],
                session_id,
                bilateral_gate.get("validation_errors"),
                bilateral_gate.get("validation_warnings"),
            )
        if isinstance(left, dict) and isinstance(right, dict) and bilateral_gate["status"] == "verified":
            try:
                from palmistry_human_orders import create_order as create_palmistry_order

                order = create_palmistry_order(
                    session_id=session_id,
                    writing_hand=writing_hand,
                    left=left,
                    right=right,
                    comparison=comparison,
                    user_id=resolved_user_id,
                    cosmo_user_id=resolved_cosmo,
                    name=str(payload.get("name") or "") or None,
                    urgent=bool(payload.get("urgent")),
                    plan=plan_norm,
                    amount_inr=paid_amount
                    or int(payload.get("amount_inr") or 0)
                    or None,
                    contact_method=str(payload.get("contact_method") or "") or None,
                    contact_value=str(payload.get("contact_value") or payload.get("whatsapp") or "") or None,
                    purchase_id=purchase_id or None,
                    lang=str(payload.get("lang") or "en") or "en",
                )
                try:
                    from palmistry_human_orders import save_hand_media

                    left_id = str((left.get("metadata") or {}).get("scan_id") or "")
                    right_id = str((right.get("metadata") or {}).get("scan_id") or "")
                    if left_id:
                        save_hand_media(order["order_id"], "left", _artifact_bundle(left_id))
                    if right_id:
                        save_hand_media(order["order_id"], "right", _artifact_bundle(right_id))
                except Exception as media_exc:
                    _LOG.warning("palmistry media save failed: %s", media_exc)
            except Exception as exc:
                _LOG.exception("palmistry create_order failed session_id=%s", session_id)
                order = {"error": str(exc)[:300]}
        response = {
            "session_id": session_id,
            "writing_hand": writing_hand,
            "bilateral_comparison": comparison,
            "production_validation": bilateral_gate,
            "admin_session": record,
            "pdf_request": {
                "ok": bool(order and order.get("order_id")),
                "order_id": (order or {}).get("order_id"),
                "public_order_id": (order or {}).get("public_order_id"),
                "queue": "PDF Requests → Palmistry",
                "error": (order or {}).get("error"),
            },
        }
        if bilateral_gate["status"] != "verified":
            response["error"] = {
                "code": "validation_failed",
                "message": bilateral_gate.get("user_message") or "Palm validation failed.",
                "issues": bilateral_gate.get("issues") or [],
            }
            return jsonify(response), 422
        if not (order and order.get("order_id")):
            err_msg = (order or {}).get("error") or "Could not create Palmistry admin order."
            response["error"] = {
                "code": "order_create_failed",
                "message": err_msg,
            }
            response["pdf_request"]["error"] = err_msg
            return jsonify(response), 500
        return jsonify(response)

    @blueprint.post("/api/palmistry/admin-upload")
    @limit("10 per minute")
    def palmistry_admin_upload():
        return save_palm_session()

    @blueprint.get("/api/admin/palmistry-orders/<order_id>")
    @limit("30 per minute")
    def admin_get_palmistry_order(order_id: str):
        err = _admin_error()
        if err:
            return err
        from palmistry_human_orders import get_order

        record = get_order(order_id)
        if record is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify(record)

    @blueprint.get("/api/admin/palmistry-orders/<order_id>/export")
    @limit("20 per minute")
    def admin_export_palmistry_order(order_id: str):
        err = _admin_error()
        if err:
            return err
        from palmistry_human_orders import export_package

        package = export_package(order_id)
        if package is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify(package)

    @blueprint.post("/api/admin/palmistry-orders/<order_id>/corrections")
    @limit("40 per minute")
    def admin_correct_palmistry_order(order_id: str):
        err = _admin_error()
        if err:
            return err
        from palmistry_human_orders import append_correction

        payload = request.get_json(silent=True) or {}
        record = append_correction(order_id, payload)
        if record is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify({
            "ok": True,
            "correction_history": record.get("correction_history") or [],
            "human_overlays": record.get("human_overlays") or {},
            "status": record.get("status"),
        })

    @blueprint.get("/api/admin/palmistry-orders/<order_id>/media/<hand>/<name>")
    @limit("60 per minute")
    def admin_palmistry_media(order_id: str, hand: str, name: str):
        err = _admin_error()
        if err:
            return err
        from palmistry_human_orders import media_path

        path = media_path(order_id, hand, name)
        if not path:
            return jsonify({"error": "not_found"}), 404
        with open(path, "rb") as fh:
            payload = fh.read()
        return Response(payload, mimetype="image/png", headers={"Cache-Control": "private, max-age=300"})

    @blueprint.get("/api/admin/palm-scans")
    @limit("30 per minute")
    def admin_list_palm_scans():
        err = _admin_error()
        if err:
            return err
        return jsonify({"sessions": palm_store.list_sessions()})

    @blueprint.get("/api/admin/palm-scans/<session_id>")
    @limit("30 per minute")
    def admin_get_palm_scan(session_id: str):
        err = _admin_error()
        if err:
            return err
        record = palm_store.get_session(session_id)
        if record is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify(record)

    @blueprint.post("/api/admin/palm-scans/<session_id>/verify")
    @limit("20 per minute")
    def admin_verify_palm_scan(session_id: str):
        err = _admin_error()
        if err:
            return err
        payload = request.get_json(silent=True) or {}
        record = palm_store.save_verification(session_id, payload)
        if record is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify(record)

    @blueprint.get("/admin/palm-scans")
    def admin_palm_scans_page():
        return Response(_ADMIN_HTML, mimetype="text/html")

    @blueprint.get("/api/palm-scan/<scan_id>/annotated")
    @limit("30 per minute")
    def palm_annotation(scan_id: str):
        with _ANNOTATIONS_LOCK:
            encoded = _ARTIFACTS.get(scan_id, {}).get("annotated")
        if encoded is None:
            return jsonify({
                "error": {"code": "annotation_not_found", "message": "Annotation is unavailable or expired."}
            }), 404
        return Response(encoded, mimetype="image/png", headers={"Cache-Control": "private, max-age=300"})

    @blueprint.get("/api/palm-scan/<scan_id>/artifacts/<artifact_name>")
    @limit("30 per minute")
    def palm_artifact(scan_id: str, artifact_name: str):
        allowed = {
            "original", "processed", "crease-enhanced", "foreground-mask",
            "segmentation-hand_boundary", "segmentation-palm_region",
            "segmentation-fingers", "segmentation-thumb", "segmentation-wrist",
            "segmentation-visible_palm", "crease-blackhat_adaptive", "crease-canny_ridge",
            "edge-map", "skeleton-map", "line-map",
            "normalized", "background-removed", "palm-segmented",
            "contrast-enhanced",
        }
        if artifact_name not in allowed:
            return jsonify({
                "error": {"code": "artifact_not_found", "message": "Artifact is unavailable or expired."}
            }), 404
        with _ANNOTATIONS_LOCK:
            encoded = _ARTIFACTS.get(scan_id, {}).get(artifact_name)
        if encoded is None:
            return jsonify({
                "error": {"code": "artifact_not_found", "message": "Artifact is unavailable or expired."}
            }), 404
        return Response(encoded, mimetype="image/png", headers={"Cache-Control": "private, max-age=300"})

    return blueprint


_ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Admin · Palm Extraction</title>
<style>
body{font-family:sans-serif;background:#0b1020;color:#e5e7eb;margin:0;padding:24px}
input,button,select,textarea{background:#111827;color:#e5e7eb;border:1px solid #374151;border-radius:8px;padding:8px}
pre{white-space:pre-wrap;background:#111827;padding:16px;border-radius:12px;overflow:auto;max-height:48vh}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0;align-items:center}
.card{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:12px;margin:8px 0;cursor:pointer}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
img{max-width:100%;border-radius:12px;background:#030712}
.feature{font-size:13px;padding:6px 0;border-bottom:1px solid #1f2937;cursor:pointer}
</style>
</head>
<body>
<h1>Palm Master Extraction</h1>
<p>User scans stay simple. This page is the full measurement dataset.</p>
<div class="row">
  <input id="token" placeholder="X-Admin-Token" style="min-width:280px"/>
  <button id="load">Load sessions</button>
  <select id="status">
    <option value="confirmed">confirm</option>
    <option value="rejected">reject</option>
    <option value="corrected">correct</option>
    <option value="ambiguous">ambiguous</option>
  </select>
  <button id="verify">Save verification</button>
</div>
<div id="list"></div>
<div class="grid">
  <div>
    <h3>Left</h3>
    <img id="leftImg" alt="left annotated"/>
    <div id="leftMap"></div>
  </div>
  <div>
    <h3>Right</h3>
    <img id="rightImg" alt="right annotated"/>
    <div id="rightMap"></div>
  </div>
</div>
<pre id="detail">Select a session. Click a mapped feature for coordinates, confidence, and detector method.</pre>
<script>
let current = null;
const headers = () => ({"X-Admin-Token": document.getElementById("token").value || ""});
function renderHand(side, record) {
  const hand = ((record.hands || {})[side] || {}).palm_scan_result || {};
  const master = hand.master_extraction || {};
  const img = document.getElementById(side + "Img");
  img.src = hand.annotated_image_reference || "";
  const box = document.getElementById(side + "Map");
  box.innerHTML = "";
  (master.palm_map || []).forEach((item) => {
    const el = document.createElement("div");
    el.className = "feature";
    el.textContent = item.kind + " · " + item.name + " · " + Math.round((item.confidence||0)*100) + "%";
    el.onclick = () => {
      document.getElementById("detail").textContent = JSON.stringify(item, null, 2);
    };
    box.appendChild(el);
  });
}
document.getElementById("load").onclick = async () => {
  const res = await fetch("/api/admin/palm-scans", {headers: headers()});
  const data = await res.json();
  const list = document.getElementById("list");
  list.innerHTML = "";
  (data.sessions || []).forEach((item) => {
    const el = document.createElement("div");
    el.className = "card";
    el.textContent = item.session_id + " · " + (item.hands||[]).join("+") + " · " + ((item.person||{}).name || item.user_id || "") + " · " + (item.verification_status||"");
    el.onclick = async () => {
      current = await fetch("/api/admin/palm-scans/" + item.session_id, {headers: headers()}).then(r=>r.json());
      renderHand("left", current);
      renderHand("right", current);
      document.getElementById("detail").textContent = JSON.stringify(current, null, 2);
    };
    list.appendChild(el);
  });
};
document.getElementById("verify").onclick = async () => {
  if (!current) return;
  const res = await fetch("/api/admin/palm-scans/" + current.session_id + "/verify", {
    method: "POST",
    headers: Object.assign({"Content-Type": "application/json"}, headers()),
    body: JSON.stringify({status: document.getElementById("status").value}),
  });
  current = await res.json();
  document.getElementById("detail").textContent = JSON.stringify(current.verification, null, 2);
};
</script>
</body></html>
"""
