"""Thin JSON-only Flask adapter for Palmistry Phase 2."""
from __future__ import annotations

from typing import Callable

from flask import Blueprint, jsonify, request

from api_auth import auth_error_response
from .bilateral import BilateralPalmistryEngine
from .engine import PalmistryPhase2Engine

RAW_INPUT_KEYS = {
    "image", "image_bytes", "file", "files", "artifact",
    "image_url", "annotated_image", "processed_image",
}


def _raw_input_paths(value, path="payload"):
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and key.lower() in RAW_INPUT_KEYS:
                paths.append(child_path)
            else:
                paths.extend(_raw_input_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_raw_input_paths(child, f"{path}.{index}"))
    return paths


def create_palmistry_phase2_blueprint(
    *, engine: PalmistryPhase2Engine | None = None,
    bilateral_engine: BilateralPalmistryEngine | None = None,
    rate_limit: Callable[[str], Callable] | None = None,
    require_user: Callable[[], tuple] | None = None,
) -> Blueprint:
    interpreter = engine or PalmistryPhase2Engine()
    bilateral = bilateral_engine or BilateralPalmistryEngine(
        single_engine=interpreter
    )
    blueprint = Blueprint("palmistry_phase2", __name__)

    def limit(spec: str):
        return rate_limit(spec) if rate_limit else (lambda function: function)

    @blueprint.post("/api/palm-reading/interpret")
    @limit("30 per minute")
    def interpret_palm():
        auth_err = auth_error_response(require_user)
        if auth_err:
            return auth_err
        if request.files or request.mimetype != "application/json":
            return jsonify({
                "status": "rejected",
                "error": {
                    "code": "json_only",
                    "message": "This endpoint accepts PalmScanResult JSON only; images, files, and multipart input are rejected.",
                },
            }), 415
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({
                "status": "insufficient_data",
                "error": {"code": "invalid_json", "message": "Request body must be a JSON object."},
            }), 422
        forbidden = sorted(_raw_input_paths(payload))
        if forbidden:
            return jsonify({
                "status": "rejected",
                "error": {
                    "code": "raw_image_input_rejected",
                    "message": "Phase 2 never accepts or analyzes image bytes, files, URLs, or artifacts.",
                    "fields": forbidden,
                },
            }), 415
        if set(payload) != {"palm_scan_result"}:
            return jsonify({
                "status": "insufficient_data",
                "error": {
                    "code": "invalid_request_shape",
                    "message": "Expected exactly one field: palm_scan_result.",
                    "fields": sorted(payload),
                },
            }), 422
        result = interpreter.analyze(payload["palm_scan_result"])
        return jsonify(result), (422 if result["status"] == "insufficient_data" else 200)

    @blueprint.post("/api/palm-reading/interpret-bilateral")
    @limit("20 per minute")
    def interpret_bilateral_palm():
        auth_err = auth_error_response(require_user)
        if auth_err:
            return auth_err
        if request.files or request.mimetype != "application/json":
            return jsonify({
                "status": "rejected",
                "error": {
                    "code": "json_only",
                    "message": (
                        "This endpoint accepts two PalmScanResult JSON objects "
                        "only; images and multipart input are rejected."
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
        expected = {
            "left_palm_scan_result",
            "right_palm_scan_result",
            "writing_hand",
        }
        forbidden = sorted(_raw_input_paths(payload))
        if forbidden:
            return jsonify({
                "status": "rejected",
                "error": {
                    "code": "raw_image_input_rejected",
                    "message": "Bilateral Phase 2 never accepts raw images.",
                    "fields": forbidden,
                },
            }), 415
        if set(payload) != expected:
            return jsonify({
                "status": "insufficient_data",
                "error": {
                    "code": "invalid_request_shape",
                    "message": (
                        "Expected left_palm_scan_result, "
                        "right_palm_scan_result, and writing_hand."
                    ),
                    "fields": sorted(payload),
                },
            }), 422
        result = bilateral.analyze(
            left_palm_scan_result=payload["left_palm_scan_result"],
            right_palm_scan_result=payload["right_palm_scan_result"],
            writing_hand=payload["writing_hand"],
        )
        return jsonify(result), (
            422 if result["status"] == "insufficient_data" else 200
        )

    return blueprint
