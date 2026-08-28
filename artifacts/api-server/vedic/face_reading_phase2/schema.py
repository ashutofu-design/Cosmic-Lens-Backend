"""Strict validation for the FaceScanResult -> Phase 2 JSON boundary."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from vedic.face_scan.schema import SCHEMA_VERSION, validate_result

OBJECT_SECTIONS = {
    "metadata", "quality", "face_detection", "landmarks", "face_geometry",
    "symmetry", "forehead", "eyebrows", "eyes", "nose", "mouth", "jaw",
    "chin", "face_shape", "skin_surface_features", "traditional_zones",
    "confidence", "validation_status",
}
RAW_INPUT_KEYS = {
    "image", "image_bytes", "image_data", "base64_image", "file", "files",
    "image_url", "artifact", "artifacts", "annotated_image",
}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: list[dict[str, Any]]


def issue(code: str, path: str, message: str, **details: Any) -> dict[str, Any]:
    return {"code": code, "path": path, "message": message, **details}


def validate_face_scan_result(value: Any) -> ValidationResult:
    issues: list[dict[str, Any]] = []
    if not isinstance(value, dict):
        return ValidationResult(False, [issue(
            "invalid_type", "face_scan_result",
            "FaceScanResult must be a JSON object.",
        )])
    _reject_raw_input(value, "face_scan_result", issues)
    if value.get("schema_version") != SCHEMA_VERSION:
        issues.append(issue(
            "schema_version_mismatch", "schema_version",
            f"Expected exact FaceScanResult schema_version {SCHEMA_VERSION}.",
            actual=value.get("schema_version"), required=SCHEMA_VERSION,
        ))
    for section in sorted(OBJECT_SECTIONS):
        if section not in value:
            issues.append(issue(
                "missing_required_section", section,
                f"Missing required section: {section}.",
            ))
        elif not isinstance(value[section], dict):
            issues.append(issue(
                "invalid_section_type", section, f"{section} must be an object."
            ))
    if "annotated_image_reference" not in value:
        issues.append(issue(
            "missing_required_section", "annotated_image_reference",
            "Missing required section: annotated_image_reference.",
        ))
    reference = value.get("annotated_image_reference")
    if reference is not None and not isinstance(reference, str):
        issues.append(issue(
            "invalid_image_reference", "annotated_image_reference",
            "annotated_image_reference must be a string or null.",
        ))
    confidence = value.get("confidence")
    if isinstance(confidence, dict):
        overall = confidence.get("overall")
        if (
            isinstance(overall, bool)
            or not isinstance(overall, (int, float))
            or not math.isfinite(float(overall))
            or not 0 <= float(overall) <= 1
        ):
            issues.append(issue(
                "invalid_scan_confidence", "confidence.overall",
                "Overall confidence must be a finite number within 0..1.",
                actual=overall,
            ))
    if not issues:
        for error in validate_result(value):
            issues.append(issue(
                "invalid_phase1_contract", "face_scan_result", error
            ))
    return ValidationResult(not issues, issues)


def admission_issues(
    scan: dict[str, Any], reliable_threshold: float
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    quality = scan.get("quality", {})
    validation = scan.get("validation_status", {})
    confidence = scan.get("confidence", {})
    checks = (
        ("quality_gate_failed", "quality.gate", quality.get("gate"), "passed"),
        ("quality_not_usable", "quality.usable", quality.get("usable"), True),
        (
            "phase1_validation_not_accepted", "validation_status.status",
            validation.get("status"), "valid_measurements",
        ),
        (
            "primary_face_not_selected",
            "face_detection.primary_selection_status",
            scan.get("face_detection", {}).get("primary_selection_status"),
            "selected",
        ),
    )
    for code, path, actual, required in checks:
        if actual != required:
            issues.append(issue(
                code, path, f"Admission requires {path} == {required!r}.",
                actual=actual, required=required,
            ))
    raw_overall = confidence.get("overall")
    if (
        isinstance(raw_overall, bool)
        or not isinstance(raw_overall, (int, float))
        or not math.isfinite(float(raw_overall))
        or not 0 <= float(raw_overall) <= 1
    ):
        issues.append(issue(
            "invalid_scan_confidence", "confidence.overall",
            "Overall confidence must be a finite number within 0..1.",
            actual=raw_overall,
        ))
        overall = 0.0
    else:
        overall = float(raw_overall)
    if overall < reliable_threshold and not any(
        item["code"] == "invalid_scan_confidence" for item in issues
    ):
        issues.append(issue(
            "scan_below_reliable_threshold", "confidence.overall",
            "Overall FaceScanResult confidence is below the reliable threshold.",
            actual=overall, required=reliable_threshold,
        ))
    method = validation.get("method_agreement")
    if isinstance(method, dict) and method.get("status") == "ambiguous":
        issues.append(issue(
            "detector_method_disagreement",
            "validation_status.method_agreement.status",
            "Phase 1 detector methods disagree substantially.",
        ))
    return issues


def _reject_raw_input(
    value: Any, path: str, issues: list[dict[str, Any]]
) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        issues.append(issue(
            "raw_image_input_rejected", path,
            "Binary image data is forbidden in Phase 2.",
        ))
    elif isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and key.lower() in RAW_INPUT_KEYS:
                issues.append(issue(
                    "raw_image_input_rejected", child_path,
                    "Raw image, URL, file, or artifact fields are forbidden in Phase 2.",
                ))
            else:
                _reject_raw_input(child, child_path, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_input(child, f"{path}.{index}", issues)


def find_raw_input_paths(value: Any, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, (bytes, bytearray, memoryview)):
        paths.append(path)
    elif isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and key.lower() in RAW_INPUT_KEYS:
                paths.append(child_path)
            else:
                paths.extend(find_raw_input_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(find_raw_input_paths(child, f"{path}.{index}"))
    return paths


def _number(value: Any) -> float:
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(float(value))
        else 0.0
    )
