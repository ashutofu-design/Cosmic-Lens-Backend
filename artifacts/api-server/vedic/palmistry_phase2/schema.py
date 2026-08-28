"""Validation for the Phase 1 -> Phase 2 JSON boundary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "1.0"
OBJECT_SECTIONS = {
    "metadata", "quality", "hand", "palm_geometry", "preprocessing",
    "segmentation", "major_lines", "secondary_lines", "mounts", "fingers",
    "thumb", "special_markings", "union_lines", "validation", "scan_confidence",
}
LIST_SECTIONS = {"landmarks"}
IMAGE_REFERENCE_KEYS = {
    "annotated_image_reference", "processed_image_reference",
    "original_decoded_image_reference",
}
REQUIRED_TOP_LEVEL = OBJECT_SECTIONS | LIST_SECTIONS | IMAGE_REFERENCE_KEYS | {"schema_version"}
NAMED_LINES = {
    "heart_line", "head_line", "life_line", "fate_line", "sun_apollo_line",
    "mercury_line", "mars_support_line",
}
NAMED_MOUNTS = {
    "Jupiter", "Saturn", "Sun/Apollo", "Mercury", "Upper Mars",
    "Lower Mars", "Venus", "Moon/Luna",
}
FINGER_NAMES = {"index", "middle", "ring", "little"}
SEGMENT_NAMES = {"hand_boundary", "palm_region", "fingers", "thumb", "wrist", "visible_palm"}
STATUSES = {
    "unknown", "detected", "not_detected", "ambiguous", "reliable",
    "unreliable", "usable", "unusable", "processed", "not_evaluated",
    "accepted", "rejected", "accepted_measurements_only", "supported",
    "unsupported", "insufficient_data", "applied", "applied_by_image_io",
    "skipped", "not_needed", "ambiguous_closed_component",
    "semantic_model_unavailable", "completed", "verifier_failed",
}


@dataclass
class ValidationResult:
    valid: bool
    issues: list[dict[str, Any]]


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


PHASE2_STRIP_KEYS = frozenset({"master_extraction", "admin_session"})


def prepare_for_phase2(value: Any) -> Any:
    """Drop nested Phase 1 master fields so schema 1.0 validation stays exact."""
    if not isinstance(value, dict):
        return value
    return {key: child for key, child in value.items() if key not in PHASE2_STRIP_KEYS}


def validate_palm_scan_result(value: Any) -> ValidationResult:
    issues: list[dict[str, Any]] = []
    if not isinstance(value, dict):
        return ValidationResult(False, [_issue(
            "invalid_type", "palm_scan_result", "PalmScanResult must be a JSON object."
        )])
    _validate_no_raw_input(value, "palm_scan_result", issues)
    if value.get("schema_version") != SCHEMA_VERSION:
        issues.append(_issue(
            "schema_version_mismatch", "schema_version",
            f"Expected exact PalmScanResult schema_version {SCHEMA_VERSION}.",
        ))
    for section in sorted(REQUIRED_TOP_LEVEL - value.keys()):
        issues.append(_issue("missing_required_section", section, f"Missing required section: {section}."))
    for section in sorted(OBJECT_SECTIONS):
        if section in value and not isinstance(value[section], dict):
            issues.append(_issue("invalid_section_type", section, f"{section} must be an object."))
    if "landmarks" in value and not isinstance(value["landmarks"], list):
        issues.append(_issue("invalid_section_type", "landmarks", "landmarks must be an array."))
    elif isinstance(value.get("landmarks"), list):
        for index, landmark in enumerate(value["landmarks"]):
            if not isinstance(landmark, dict):
                issues.append(_issue("invalid_landmark_type", f"landmarks.{index}", "Landmark must be an object."))
    for key in sorted(IMAGE_REFERENCE_KEYS):
        if key in value and value[key] is not None and not isinstance(value[key], str):
            issues.append(_issue("invalid_image_reference", key, f"{key} must be a string or null."))
    if not isinstance(value.get("major_lines"), dict):
        pass
    else:
        for name in sorted(NAMED_LINES - value["major_lines"].keys()):
            issues.append(_issue("missing_required_feature", f"major_lines.{name}", "Named line is required."))
        _validate_feature_map(value["major_lines"], "major_lines", issues)
        _validate_named_line_provenance(value, issues)
    if not isinstance(value.get("mounts"), dict):
        pass
    else:
        for name in sorted(NAMED_MOUNTS - value["mounts"].keys()):
            issues.append(_issue("missing_required_feature", f"mounts.{name}", "Named mount is required."))
        _validate_feature_map(value["mounts"], "mounts", issues)
    if isinstance(value.get("fingers"), dict):
        for name in sorted(FINGER_NAMES - value["fingers"].keys()):
            issues.append(_issue("missing_required_feature", f"fingers.{name}", "Finger measurement is required."))
        _validate_feature_map(value["fingers"], "fingers", issues)
    if isinstance(value.get("segmentation"), dict):
        for name in sorted(SEGMENT_NAMES - value["segmentation"].keys()):
            issues.append(_issue("missing_required_feature", f"segmentation.{name}", "Segmentation region is required."))
        _validate_feature_map(value["segmentation"], "segmentation", issues)
    for section in ("hand", "thumb"):
        if isinstance(value.get(section), dict):
            _validate_feature_shape(value[section], section, issues)
    if isinstance(value.get("union_lines"), dict):
        readable = value["union_lines"].get("readable")
        if readable is not None and not isinstance(readable, bool):
            issues.append(_issue("invalid_readability", "union_lines.readable", "readable must be boolean."))
    if isinstance(value.get("special_markings"), dict):
        candidates = value["special_markings"].get("candidates", [])
        if not isinstance(candidates, list):
            issues.append(_issue("invalid_markings", "special_markings.candidates", "candidates must be an array."))
        else:
            for index, candidate in enumerate(candidates):
                if not isinstance(candidate, dict):
                    issues.append(_issue("invalid_marking", f"special_markings.candidates.{index}", "Marking must be an object."))
                elif candidate.get("type") in {None, "unknown", "ambiguous"} and candidate.get("status") == "detected":
                    issues.append(_issue("invalid_ambiguity", f"special_markings.candidates.{index}.type", "Detected marking requires a supported unambiguous type."))
    _validate_admission_fields(value, issues)
    _validate_common(value, "", issues)
    conflicts = value.get("conflicts")
    if conflicts is not None and not isinstance(conflicts, list):
        issues.append(_issue("invalid_conflicts", "conflicts", "conflicts must be an array when supplied."))
    return ValidationResult(not issues, issues)


def _validate_named_line_provenance(
    value: dict[str, Any], issues: list[dict[str, Any]]
) -> None:
    secondary = value.get("secondary_lines")
    candidates = (
        secondary.get("crease_candidates", [])
        if isinstance(secondary, dict) else []
    )
    candidate_by_id = {
        candidate.get("id"): candidate
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    }
    detected_lines = [
        (name, line) for name, line in value["major_lines"].items()
        if isinstance(line, dict)
        and (line.get("status") == "detected" or line.get("detected") is True)
    ]
    if detected_lines:
        verification = (
            secondary.get("semantic_verification", {})
            if isinstance(secondary, dict) else {}
        )
        if not isinstance(verification, dict) or verification.get("status") != "completed":
            issues.append(_issue(
                "unverified_named_lines", "secondary_lines.semantic_verification.status",
                "Detected named lines require completed candidate-ID semantic verification.",
            ))
    for name, line in detected_lines:
        path = f"major_lines.{name}"
        candidate_id = line.get("source_candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            issues.append(_issue(
                "missing_line_provenance", f"{path}.source_candidate_id",
                "Detected named line requires a source crease candidate ID.",
            ))
            continue
        candidate = candidate_by_id.get(candidate_id)
        if candidate is None:
            issues.append(_issue(
                "invalid_line_provenance", f"{path}.source_candidate_id",
                "Named line source candidate does not exist in secondary_lines.",
            ))
            continue
        line_points = line.get("path")
        candidate_points = candidate.get("path")
        if (
            not isinstance(line_points, list) or len(line_points) < 2
            or line_points != candidate_points
        ):
            issues.append(_issue(
                "line_path_provenance_mismatch", f"{path}.path",
                "Named line path must exactly reuse its detected source candidate path.",
            ))


def _validate_admission_fields(value: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    quality = value.get("quality")
    if isinstance(quality, dict):
        if "usable" not in quality or not isinstance(quality.get("usable"), bool):
            issues.append(_issue("invalid_admission_field", "quality.usable", "quality.usable must be boolean."))
        if "gate" not in quality or not isinstance(quality.get("gate"), str):
            issues.append(_issue("invalid_admission_field", "quality.gate", "quality.gate must be a string."))
    validation = value.get("validation")
    if isinstance(validation, dict):
        for key in ("status", "quality_gate"):
            if not isinstance(validation.get(key), str):
                issues.append(_issue("invalid_admission_field", f"validation.{key}", f"validation.{key} must be a string."))
    confidence = value.get("scan_confidence")
    if isinstance(confidence, dict):
        numeric = confidence.get("value", confidence.get("overall"))
        if isinstance(numeric, bool) or not isinstance(numeric, (int, float)) or not 0 <= numeric <= 1:
            issues.append(_issue("invalid_admission_field", "scan_confidence.value", "Scan confidence value must be between 0 and 1."))
        if not isinstance(confidence.get("phase_2_eligible"), bool):
            issues.append(_issue("invalid_admission_field", "scan_confidence.phase_2_eligible", "phase_2_eligible must be boolean."))
        if not isinstance(confidence.get("phase_2_reason"), str):
            issues.append(_issue("invalid_admission_field", "scan_confidence.phase_2_reason", "phase_2_reason must be a string."))
        eligible = confidence.get("eligible_features")
        if not isinstance(eligible, dict):
            issues.append(_issue("invalid_admission_field", "scan_confidence.eligible_features", "eligible_features must be an object."))
        else:
            for group in ("major_lines", "mounts", "fingers", "markings"):
                if not isinstance(eligible.get(group), list):
                    issues.append(_issue("invalid_admission_field", f"scan_confidence.eligible_features.{group}", "Eligibility group must be an array."))
                elif not all(isinstance(item, str) for item in eligible[group]):
                    issues.append(_issue("invalid_admission_field", f"scan_confidence.eligible_features.{group}", "Eligibility entries must be strings."))


def _validate_feature_map(value: dict[str, Any], path: str, issues: list[dict[str, Any]]) -> None:
    for name, feature in value.items():
        feature_path = f"{path}.{name}"
        if not isinstance(feature, dict):
            issues.append(_issue("invalid_feature_type", feature_path, "Feature must be an object."))
        else:
            _validate_feature_shape(feature, feature_path, issues)


def _validate_feature_shape(feature: dict[str, Any], path: str, issues: list[dict[str, Any]]) -> None:
    if not isinstance(feature.get("status"), str):
        issues.append(_issue("invalid_feature_status", f"{path}.status", "Feature status must be a string."))
    confidence = feature.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        issues.append(_issue("invalid_feature_confidence", f"{path}.confidence", "Feature confidence must be between 0 and 1."))


def _validate_no_raw_input(value: Any, path: str, issues: list[dict[str, Any]]) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        issues.append(_issue("raw_image_input_rejected", path, "Binary data is forbidden in Phase 2."))
    elif isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"image", "image_bytes", "file", "files", "image_data", "base64_image"}:
                issues.append(_issue("raw_image_input_rejected", child_path, "Raw image/file fields are forbidden in Phase 2."))
            else:
                _validate_no_raw_input(child, child_path, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_raw_input(child, f"{path}.{index}", issues)


def _validate_common(value: Any, path: str, issues: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        if "confidence" in value:
            confidence = value["confidence"]
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                issues.append(_issue("invalid_confidence", f"{path}.confidence".strip("."), "confidence must be between 0 and 1."))
        if "status" in value and (not isinstance(value["status"], str) or value["status"] not in STATUSES):
            issues.append(_issue("invalid_status", f"{path}.status".strip("."), f"Unknown status: {value['status']!r}."))
        if "ambiguous" in value and not isinstance(value["ambiguous"], bool):
            issues.append(_issue("invalid_ambiguity", f"{path}.ambiguous".strip("."), "ambiguous must be boolean."))
        for key, child in value.items():
            _validate_common(child, f"{path}.{key}".strip("."), issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_common(child, f"{path}.{index}", issues)
