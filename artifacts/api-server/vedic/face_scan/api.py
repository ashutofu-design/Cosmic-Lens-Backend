"""Flask Blueprint for isolated Phase 1 face measurements."""
from __future__ import annotations

from collections import OrderedDict
from threading import Lock
from typing import Callable

import cv2
from flask import Blueprint, Response, jsonify, request

from .engine import FaceScanEngine

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
_MAX_SCANS = 32
_ANNOTATIONS: OrderedDict[str, bytes] = OrderedDict()
_LOCK = Lock()


def _store_annotation(scan_id: str, image) -> bool:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        return False
    with _LOCK:
        _ANNOTATIONS[scan_id] = encoded.tobytes()
        _ANNOTATIONS.move_to_end(scan_id)
        while len(_ANNOTATIONS) > _MAX_SCANS:
            _ANNOTATIONS.popitem(last=False)
    return True


def create_face_scan_blueprint(
    *,
    engine: FaceScanEngine | None = None,
    rate_limit: Callable[[str], Callable] | None = None,
) -> Blueprint:
    scanner = engine or FaceScanEngine()
    blueprint = Blueprint("face_scan", __name__)

    def limit(spec: str):
        return rate_limit(spec) if rate_limit else (lambda function: function)

    @blueprint.post("/api/face-scan")
    @limit("10 per minute")
    def scan_face():
        upload = request.files.get("image")
        if upload is None:
            return jsonify({"error": {
                "code": "missing_image",
                "message": "Provide an image multipart field.",
                "field": "image",
            }}), 400
        content_type = (upload.mimetype or "").lower()
        if content_type and not content_type.startswith("image/"):
            return jsonify({"error": {
                "code": "invalid_content_type",
                "message": "The image field must have an image content type.",
            }}), 415
        payload = upload.stream.read(MAX_UPLOAD_BYTES + 1)
        if len(payload) > MAX_UPLOAD_BYTES:
            return jsonify({"error": {
                "code": "file_too_large", "message": "Image exceeds the 12 MB limit."
            }}), 413
        mirror = (request.form.get("mirror") or "false").strip().lower()
        if mirror not in {"true", "false", "1", "0"}:
            return jsonify({"error": {
                "code": "invalid_mirror_option",
                "message": "mirror must be true or false.",
                "field": "mirror",
            }}), 400
        result, artifacts = scanner.scan_with_artifacts(
            payload, mirror=mirror in {"true", "1"}
        )
        annotated = artifacts.get("annotated")
        if annotated is not None:
            stored = _store_annotation(result["metadata"]["scan_id"], annotated)
            if not stored:
                result["annotated_image_reference"] = None
        if result["validation_status"]["status"] == "invalid_schema":
            status = 500
        else:
            status = 200 if result["quality"]["usable"] else 422
        return jsonify(result), status

    @blueprint.get("/api/face-scan/<scan_id>/annotated")
    @limit("30 per minute")
    def face_annotation(scan_id: str):
        with _LOCK:
            encoded = _ANNOTATIONS.get(scan_id)
        if encoded is None:
            return jsonify({"error": {
                "code": "annotation_not_found",
                "message": "Annotation is unavailable or expired.",
            }}), 404
        return Response(
            encoded,
            mimetype="image/png",
            headers={"Cache-Control": "private, max-age=300"},
        )

    return blueprint
