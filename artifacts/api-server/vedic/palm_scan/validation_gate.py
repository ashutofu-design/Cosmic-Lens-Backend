"""Production validation gate for palm scan promotion."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any


VALIDATION_VERSION = "production_validation/1.1"


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return float(default)
    try:
        return float(raw)
    except ValueError:
        return float(default)


def _env_bool(name: str, default: bool) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def gate_config() -> dict[str, Any]:
    strict = _env_bool("PALM_VALIDATION_STRICT", False)
    return {
        "validation_version": os.environ.get("PALM_VALIDATION_VERSION", VALIDATION_VERSION),
        "strict_validation": strict,
        "minimum_quality": _env_float("PALM_MIN_QUALITY", 0.48 if strict else 0.0),
        "minimum_confidence": _env_float("PALM_MIN_CONFIDENCE", 0.45 if strict else 0.0),
        "minimum_hand_confidence": _env_float("PALM_MIN_HAND_CONFIDENCE", 0.58 if strict else 0.0),
        "minimum_palm_boundary_confidence": _env_float("PALM_MIN_PALM_BOUNDARY_CONFIDENCE", 0.55 if strict else 0.0),
        "minimum_geometry_confidence": _env_float("PALM_MIN_GEOMETRY_CONFIDENCE", 0.55 if strict else 0.0),
        "minimum_crease_confidence": _env_float("PALM_MIN_CREASE_CONFIDENCE", 0.28 if strict else 0.0),
        "minimum_landmark_coverage": _env_float("PALM_MIN_LANDMARK_COVERAGE", 0.95 if strict else 0.0),
        "minimum_line_coverage": _env_float("PALM_MIN_LINE_COVERAGE", 0.35 if strict else 0.0),
        "minimum_major_line_candidates": int(_env_float("PALM_MIN_MAJOR_LINE_CANDIDATES", 1 if strict else 0)),
        "max_orientation_degrees": _env_float("PALM_MAX_ORIENTATION_DEGREES", 55.0 if strict else 180.0),
        "both_hands_required": _env_bool("PALM_BOTH_HANDS_REQUIRED", True),
        "enforce_side_match": _env_bool("PALM_ENFORCE_SIDE_MATCH", strict),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _avg_confidence(values: list[dict[str, Any]]) -> float:
    nums = [_as_float(item.get("confidence")) for item in values if isinstance(item, dict)]
    return round(sum(nums) / len(nums), 4) if nums else 0.0


def _first_issue_message(issues: list[dict[str, Any]]) -> str | None:
    for issue in issues:
        if isinstance(issue, dict) and issue.get("message"):
            return str(issue["message"])
    return None


def _issue_codes(scan: dict[str, Any]) -> set[str]:
    quality = _as_dict(scan.get("quality"))
    validation = _as_dict(scan.get("validation"))
    issues = _as_list(quality.get("issues")) + _as_list(validation.get("issues"))
    return {
        str(item.get("code"))
        for item in issues
        if isinstance(item, dict) and item.get("code")
    }


def _user_message_from_codes(codes: set[str], fallback: str | None = None) -> str:
    priority = [
        ("hand_not_detected", "Hand not detected. Please upload one open palm against a plain background."),
        ("low_hand_detection_confidence", "The image does not clearly contain one open palm. Please retake the photo."),
        ("palm_cropped", "Your palm is partially cropped. Retake the photo with the complete palm and wrist visible."),
        ("fingers_hidden_or_cropped", "Fingers are not fully visible. Retake the photo with all fingertips visible."),
        ("wrist_not_visible", "The wrist boundary is missing. Retake the photo with the full palm and wrist visible."),
        ("extreme_orientation", "Palm orientation is invalid. Keep fingers pointing upward and the palm facing the camera."),
        ("hand_not_open", "Open and gently separate all fingers before retaking the photo."),
        ("resolution_low", "Insufficient resolution. Please upload a clearer, higher-resolution palm image."),
        ("blurred", "Image too blurry. Please retake the palm photo with minimal blur."),
        ("low_light", "Poor lighting. Please retake the palm photo in brighter, even lighting."),
        ("overexposed", "Excessive glare or overexposure detected. Reduce glare and retake the photo."),
        ("low_contrast", "Palm lines are not sufficiently visible. Use even light and a contrasting background."),
        ("side_mismatch", "The uploaded hand does not match the requested hand side. Please retake the correct hand."),
        ("geometry_unreliable", "Palm geometry could not be established reliably. Please retake the photo with the full palm visible."),
        ("crease_visibility_low", "Fine palm creases could not be extracted with sufficient confidence. Retake the photo in brighter, even lighting."),
        ("major_line_candidates_missing", "Palm lines are not sufficiently visible for structured extraction. Please retake the photo."),
        ("extraction_confidence_low", "Palm extraction confidence is too low. Please retake the photo with better lighting and less blur."),
    ]
    for code, message in priority:
        if code in codes:
            return message
    return fallback or (
        "Your palm image is not clear enough for analysis. Please retake the photo with your complete palm visible, good lighting and minimal blur."
    )


def evaluate_hand(scan: dict[str, Any] | None, *, required_hand_side: str | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or gate_config()
    scan = _as_dict(scan)
    quality = _as_dict(scan.get("quality"))
    hand = _as_dict(scan.get("hand"))
    scan_conf = _as_dict(scan.get("scan_confidence"))
    validation = _as_dict(scan.get("validation"))
    segmentation = _as_dict(scan.get("segmentation"))
    palm_geometry = _as_dict(scan.get("palm_geometry"))
    fingers = _as_dict(scan.get("fingers"))
    thumb = _as_dict(scan.get("thumb"))
    major_lines = _as_dict(scan.get("major_lines"))
    secondary_lines = _as_dict(scan.get("secondary_lines"))
    continuity = _as_dict(scan.get("line_stitching"))
    landmarks = _as_list(scan.get("landmarks"))
    metadata = _as_dict(scan.get("metadata"))

    issue_codes = _issue_codes(scan)
    issue_payloads = _as_list(quality.get("issues")) + _as_list(validation.get("issues"))
    detected_side = str(hand.get("side") or hand.get("handedness") or "unknown")
    warnings = sorted({
        str(item.get("code"))
        for item in issue_payloads
        if isinstance(item, dict) and item.get("severity") == "warning" and item.get("code")
    })
    hand_confidence = _as_float(hand.get("confidence"))
    quality_score = round(_as_float(quality.get("score")), 4)
    confidence_score = round(max(_as_float(scan_conf.get("overall")), _as_float(scan_conf.get("value"))), 4)
    hand_detected = hand.get("status") == "detected"
    orientation_angle = _as_float(_as_dict(_as_dict(quality.get("metrics")).get("orientation")).get("angle_from_vertical_deg"))
    orientation_valid = hand_detected and abs(orientation_angle) <= cfg["max_orientation_degrees"] and "extreme_orientation" not in issue_codes
    palm_boundary = _as_dict(segmentation.get("palm_region"))
    visible_palm = _as_dict(segmentation.get("visible_palm"))
    wrist = _as_dict(segmentation.get("wrist"))
    palm_boundary_valid = (
        palm_boundary.get("status") == "detected"
        and visible_palm.get("status") == "detected"
        and wrist.get("status") == "detected"
        and min(
            _as_float(palm_boundary.get("confidence")),
            _as_float(visible_palm.get("confidence")),
            _as_float(wrist.get("confidence")),
        ) >= cfg["minimum_palm_boundary_confidence"]
        and "palm_cropped" not in issue_codes
        and "wrist_not_visible" not in issue_codes
    )
    landmark_coverage = round(len(landmarks) / 21.0, 4) if landmarks else 0.0
    landmarks_valid = landmark_coverage >= cfg["minimum_landmark_coverage"]
    geometry_score = _avg_confidence([
        _as_dict(palm_geometry.get("width")),
        _as_dict(palm_geometry.get("length")),
        _as_dict(palm_geometry.get("orientation")),
        palm_boundary,
        visible_palm,
        wrist,
        *_as_dict(fingers).values(),
        _as_dict(thumb),
    ])
    crease_candidates = _as_list(secondary_lines.get("crease_candidates"))
    major_detected = [
        item for item in _as_dict(major_lines).values()
        if isinstance(item, dict) and item.get("status") in {"detected", "probable", "ambiguous"}
    ]
    continuity_groups = _as_list(continuity.get("groups"))
    crease_visibility = max(
        _as_float(secondary_lines.get("confidence")),
        _avg_confidence([item for item in crease_candidates if isinstance(item, dict)]),
        _avg_confidence([item for item in continuity_groups if isinstance(item, dict)]),
    )
    crease_detection_valid = bool(crease_candidates) and crease_visibility >= cfg["minimum_line_coverage"]
    major_lines_valid = len(major_detected) >= int(cfg["minimum_major_line_candidates"])
    processing_complete = bool(metadata.get("dimensions")) and validation.get("status") in {"accepted_measurements_only", "rejected"}
    quality_ready = quality.get("gate") in {"passed", "failed"}

    strict = bool(cfg.get("strict_validation"))
    check_failures: list[str] = []
    if quality.get("usable") is not True or quality.get("gate") != "passed" or quality_score < cfg["minimum_quality"]:
        check_failures.extend(sorted(issue_codes or {"quality_gate_failed"}))
        if quality_score < cfg["minimum_quality"]:
            check_failures.append("quality_score_below_threshold")
    if not hand_detected or hand_confidence < cfg["minimum_hand_confidence"]:
        check_failures.append("hand_not_detected" if not hand_detected else "low_hand_detection_confidence")
    if required_hand_side in {"left", "right"} and cfg["enforce_side_match"] and detected_side in {"left", "right"} and detected_side != required_hand_side:
        check_failures.append("side_mismatch")
    if not orientation_valid:
        check_failures.append("orientation_invalid")
    if not palm_boundary_valid:
        check_failures.append("palm_boundary_invalid")
    if not landmarks_valid:
        check_failures.append("landmarks_invalid")
    if geometry_score < cfg["minimum_geometry_confidence"]:
        check_failures.append("geometry_unreliable")
    if crease_visibility < cfg["minimum_crease_confidence"]:
        check_failures.append("crease_visibility_low")
    if not crease_detection_valid:
        check_failures.append("crease_detection_invalid")
    if not major_lines_valid:
        check_failures.append("major_lines_invalid")
    if confidence_score < cfg["minimum_confidence"] or validation.get("status") != "accepted_measurements_only":
        check_failures.append("confidence_below_threshold" if confidence_score < cfg["minimum_confidence"] else "validation_not_accepted")

    check_failures = list(dict.fromkeys(reason for reason in check_failures if reason))
    scan_payload_ready = bool(metadata.get("dimensions"))
    if strict:
        if not processing_complete or not quality_ready:
            status = "pending"
        elif check_failures:
            status = "rejected"
        else:
            status = "verified"
        validation_errors = check_failures
        audit_warnings = warnings
    else:
        validation_errors = []
        if not hand_detected:
            validation_errors.append("hand_not_detected")
        if scan_payload_ready and hand_detected and not validation_errors:
            status = "verified"
        elif hand_detected:
            status = "pending"
        elif validation_errors:
            status = "rejected"
        else:
            status = "pending"
        audit_warnings = sorted(set(warnings) | set(check_failures))

    fallback_message = _first_issue_message([item for item in issue_payloads if isinstance(item, dict)])
    user_message = (
        "Production validation passed."
        if status == "verified"
        else "Production validation in progress."
        if status == "pending"
        else _user_message_from_codes(set(validation_errors) | issue_codes, fallback_message)
    )
    return {
        "status": status,
        "strict_validation": strict,
        "required_hand_side": required_hand_side if required_hand_side in {"left", "right"} else None,
        "detected_hand_side": detected_side,
        "quality_gate": quality.get("gate") or validation.get("quality_gate") or "not_evaluated",
        "validation_version": cfg["validation_version"],
        "processing_timestamp": _now(),
        "quality_score": quality_score,
        "confidence_score": confidence_score,
        "hand_detected": hand_detected,
        "orientation_valid": orientation_valid,
        "palm_boundary_valid": palm_boundary_valid,
        "landmarks_valid": landmarks_valid,
        "major_lines_valid": major_lines_valid,
        "crease_detection_valid": crease_detection_valid,
        "landmark_coverage": landmark_coverage,
        "validation_errors": validation_errors,
        "validation_warnings": audit_warnings,
        "quality_warnings": audit_warnings if not strict else [],
        "rejection_reasons": validation_errors,
        "user_message": user_message,
        "stage_scores": {
            "image_quality": quality_score,
            "hand_detection": round(hand_confidence, 4),
            "geometry": round(geometry_score, 4),
            "crease_visibility": round(crease_visibility, 4),
            "extraction_confidence": confidence_score,
        },
        "thresholds": {
            "PALM_MIN_QUALITY": cfg["minimum_quality"],
            "PALM_MIN_CONFIDENCE": cfg["minimum_confidence"],
            "PALM_MIN_LANDMARK_COVERAGE": cfg["minimum_landmark_coverage"],
            "PALM_MIN_LINE_COVERAGE": cfg["minimum_line_coverage"],
            "minimum_hand_confidence": cfg["minimum_hand_confidence"],
            "minimum_palm_boundary_confidence": cfg["minimum_palm_boundary_confidence"],
            "minimum_geometry_confidence": cfg["minimum_geometry_confidence"],
            "minimum_crease_confidence": cfg["minimum_crease_confidence"],
            "minimum_major_line_candidates": cfg["minimum_major_line_candidates"],
            "max_orientation_degrees": cfg["max_orientation_degrees"],
            "enforce_side_match": cfg["enforce_side_match"],
            "strict_validation": strict,
        },
        "raw_issue_codes": sorted(issue_codes),
    }


def evaluate_bilateral(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
    *,
    writing_hand: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or gate_config()
    left_eval = evaluate_hand(left, required_hand_side="left", config=cfg) if left else None
    right_eval = evaluate_hand(right, required_hand_side="right", config=cfg) if right else None
    issues: list[str] = []
    warnings: list[str] = []
    if cfg["both_hands_required"]:
        if left_eval is None:
            issues.append("left_hand_missing")
        if right_eval is None:
            issues.append("right_hand_missing")
    if left_eval and left_eval["status"] == "rejected":
        issues.append("left_hand_failed")
    if right_eval and right_eval["status"] == "rejected":
        issues.append("right_hand_failed")
    if left_eval and left_eval["status"] == "pending":
        warnings.append("left_hand_pending")
    if right_eval and right_eval["status"] == "pending":
        warnings.append("right_hand_pending")
    confidence_values = [_as_float(_as_dict(left_eval).get("confidence_score")), _as_float(_as_dict(right_eval).get("confidence_score"))]
    usable_confidences = [value for value in confidence_values if value > 0]
    overall_confidence = round(min(usable_confidences), 4) if usable_confidences else 0.0
    if issues:
        status = "rejected"
    elif (cfg["both_hands_required"] and (left_eval is None or right_eval is None)) or warnings:
        status = "pending"
    elif left_eval and right_eval and left_eval["status"] == "verified" and right_eval["status"] == "verified":
        status = "verified"
    else:
        status = "pending"
    return {
        "status": status,
        "overall_status": "VERIFIED" if status == "verified" else "REJECTED" if status == "rejected" else "PENDING",
        "overall_confidence": overall_confidence,
        "writing_hand": writing_hand if writing_hand in {"left", "right"} else "unknown",
        "validation_version": cfg["validation_version"],
        "processing_timestamp": _now(),
        "both_hands_required": bool(cfg["both_hands_required"]),
        "issues": issues,
        "validation_errors": issues,
        "validation_warnings": warnings,
        "left": left_eval,
        "right": right_eval,
        "user_message": (
            "Both palm scans passed production validation."
            if status == "verified" else "Production validation in progress."
            if status == "pending" else (
                (left_eval or {}).get("user_message")
                or (right_eval or {}).get("user_message")
                or "One or more palm scans failed validation. Please retake the rejected hand image."
            )
        ),
    }


def is_hand_pass(scan: dict[str, Any] | None, *, required_hand_side: str | None = None, config: dict[str, Any] | None = None) -> bool:
    return evaluate_hand(scan, required_hand_side=required_hand_side, config=config)["status"] == "verified"


def is_bilateral_pass(left: dict[str, Any] | None, right: dict[str, Any] | None, *, writing_hand: str | None = None, config: dict[str, Any] | None = None) -> bool:
    return evaluate_bilateral(left, right, writing_hand=writing_hand, config=config)["status"] == "verified"
