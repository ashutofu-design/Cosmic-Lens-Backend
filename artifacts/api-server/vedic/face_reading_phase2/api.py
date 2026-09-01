"""JSON-only Flask adapter for traditional Face Reading Phase 2."""
from __future__ import annotations

from typing import Callable

from flask import Blueprint, jsonify, request

from api_auth import auth_error_response
from .engine import FaceReadingPhase2Engine
from .rules import DEFAULT_SYSTEM_ID
from .schema import find_raw_input_paths


def create_face_reading_phase2_blueprint(
    *,
    engine: FaceReadingPhase2Engine | None = None,
    rate_limit: Callable[[str], Callable] | None = None,
    require_user: Callable[[], tuple] | None = None,
) -> Blueprint:
    interpreter = engine or FaceReadingPhase2Engine()
    blueprint = Blueprint("face_reading_phase2", __name__)

    def limit(spec: str):
        return rate_limit(spec) if rate_limit else (lambda function: function)

    @blueprint.post("/api/face-reading/interpret")
    @limit("30 per minute")
    def interpret_face():
        auth_err = auth_error_response(require_user)
        if auth_err:
            return auth_err
        if request.files or request.mimetype != "application/json":
            return jsonify({
                "status": "rejected",
                "error": {
                    "code": "json_only",
                    "message": (
                        "This endpoint accepts FaceScanResult JSON only; "
                        "images, files, and multipart input are rejected."
                    ),
                },
            }), 415
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({
                "status": "insufficient_data",
                "error": {
                    "code": "invalid_json",
                    "message": "Request body must be a JSON object.",
                },
            }), 422
        forbidden = sorted(find_raw_input_paths(payload))
        if forbidden:
            return jsonify({
                "status": "rejected",
                "error": {
                    "code": "raw_image_input_rejected",
                    "message": (
                        "Phase 2 never accepts image bytes, files, URLs, "
                        "or artifacts."
                    ),
                    "fields": forbidden,
                },
            }), 415
        allowed = {"face_scan_result", "traditional_system"}
        if (
            "face_scan_result" not in payload
            or not set(payload).issubset(allowed)
        ):
            return jsonify({
                "status": "insufficient_data",
                "error": {
                    "code": "invalid_request_shape",
                    "message": (
                        "Expected face_scan_result and optional "
                        "traditional_system only."
                    ),
                    "fields": sorted(payload),
                },
            }), 422
        system_id = payload.get("traditional_system", DEFAULT_SYSTEM_ID)
        if not isinstance(system_id, str):
            return jsonify({
                "status": "insufficient_data",
                "error": {
                    "code": "invalid_traditional_system",
                    "message": "traditional_system must be a string.",
                    "supported": sorted(interpreter.systems),
                },
            }), 422
        result = interpreter.analyze(
            payload["face_scan_result"], traditional_system=system_id
        )
        return jsonify(result), (
            422 if result["status"] == "insufficient_data" else 200
        )

    @blueprint.get("/api/face-reading/systems")
    @limit("60 per minute")
    def list_systems():
        return jsonify({
            "default": DEFAULT_SYSTEM_ID,
            "systems": [
                {
                    "system_id": system.system_id,
                    "namespace": system.namespace,
                    "version": system.version,
                    "display_name": system.display_name,
                    "rules_combined_with_other_systems": False,
                }
                for system in interpreter.systems.values()
            ],
        })

    return blueprint
