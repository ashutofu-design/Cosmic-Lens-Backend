"""Public structural type for Face Scan Phase 1 JSON."""
from __future__ import annotations

from typing import Any, TypedDict

SCHEMA_VERSION = "1.0"
REQUIRED_TOP_LEVEL = {
    "schema_version", "metadata", "quality", "face_detection", "landmarks",
    "face_geometry", "symmetry", "forehead", "eyebrows", "eyes", "nose",
    "mouth", "jaw", "chin", "face_shape", "skin_surface_features",
    "traditional_zones", "confidence", "validation_status",
    "annotated_image_reference",
}
FORBIDDEN_INFERENCE_KEYS = {
    "personality", "health", "ethnicity", "attractiveness", "intelligence",
    "future", "career", "money", "love", "relationship", "diagnosis",
}


class FaceScanResult(TypedDict):
    schema_version: str
    metadata: dict[str, Any]
    quality: dict[str, Any]
    face_detection: dict[str, Any]
    landmarks: dict[str, Any]
    face_geometry: dict[str, Any]
    symmetry: dict[str, Any]
    forehead: dict[str, Any]
    eyebrows: dict[str, Any]
    eyes: dict[str, Any]
    nose: dict[str, Any]
    mouth: dict[str, Any]
    jaw: dict[str, Any]
    chin: dict[str, Any]
    face_shape: dict[str, Any]
    skin_surface_features: dict[str, Any]
    traditional_zones: dict[str, Any]
    confidence: dict[str, Any]
    validation_status: dict[str, Any]
    annotated_image_reference: str | None


def validate_result(value: Any) -> list[str]:
    """Validate the public Phase 1 boundary without interpreting measurements."""
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["FaceScanResult must be an object"]
    missing = REQUIRED_TOP_LEVEL - set(value)
    if missing:
        errors.append("missing top-level keys: " + ", ".join(sorted(missing)))
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
    metadata = value.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("measurement_only") is not True:
        errors.append("metadata.measurement_only must be true")
    quality = value.get("quality")
    if not isinstance(quality, dict):
        errors.append("quality must be an object")
    else:
        if not isinstance(quality.get("usable"), bool):
            errors.append("quality.usable must be boolean")
        for key in (
            "overall_score", "resolution_score", "blur_score", "lighting_score",
            "visibility_score", "occlusion_score",
        ):
            _confidence(quality.get(key), f"quality.{key}", errors)
    detection = value.get("face_detection")
    if not isinstance(detection, dict):
        errors.append("face_detection must be an object")
    else:
        if not isinstance(detection.get("face_count"), int):
            errors.append("face_detection.face_count must be an integer")
        _confidence(
            detection.get("confidence"), "face_detection.confidence", errors
        )
    landmarks = value.get("landmarks")
    named = landmarks.get("named") if isinstance(landmarks, dict) else None
    if not isinstance(named, dict):
        errors.append("landmarks.named must be an object")
    else:
        for name, point in named.items():
            if not isinstance(point, dict):
                errors.append(f"landmarks.named.{name} must be an object")
                continue
            _confidence(
                point.get("confidence"),
                f"landmarks.named.{name}.confidence", errors,
            )
            for axis in ("normalized_x", "normalized_y"):
                _confidence(
                    point.get(axis), f"landmarks.named.{name}.{axis}", errors
                )
    _walk(value, "$", errors)
    return errors


def _confidence(value: Any, location: str, errors: list[str]) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= float(value) <= 1
    ):
        errors.append(f"{location} must be a number within 0..1")


def _walk(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_INFERENCE_KEYS:
                errors.append(f"{path}.{key} is forbidden in measurement-only output")
            if key == "confidence" and not isinstance(child, dict):
                _confidence(child, f"{path}.{key}", errors)
            _walk(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk(child, f"{path}[{index}]", errors)
