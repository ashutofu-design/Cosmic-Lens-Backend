"""Dataset-ready face scan annotation validation and neutral evaluation."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ANNOTATION_SCHEMA = "face_scan_annotation/1.0"


def make_example_annotation() -> dict:
    """Return structurally valid illustrative data, not an accuracy fixture."""
    return {
        "annotation_schema": ANNOTATION_SCHEMA,
        "image_id": "synthetic-example",
        "coordinate_space": "normalized_0_1",
        "bbox": {"x": .2, "y": .1, "width": .6, "height": .8},
        "landmarks": [
            {"name": "nose_tip", "normalized_x": .5, "normalized_y": .52}
        ],
        "zones": {
            "middle": {"polygon": [
                {"x": .3, "y": .32}, {"x": .7, "y": .32},
                {"x": .65, "y": .65}, {"x": .35, "y": .65},
            ]}
        },
        "feature_regions": {
            "nose": {"polygon": [
                {"x": .43, "y": .36}, {"x": .57, "y": .36},
                {"x": .58, "y": .64}, {"x": .42, "y": .64},
            ]}
        },
        "measurements": {
            "face_geometry.aspect_ratio": {"value": 1.3, "tolerance": .1}
        },
        "face_shape": {"label": "oval"},
    }


def load_annotation(value: dict | str | Path) -> dict:
    annotation = value if isinstance(value, dict) else json.loads(
        Path(value).read_text(encoding="utf-8")
    )
    errors = validate_annotation(annotation)
    if errors:
        raise ValueError("Invalid face scan annotation: " + "; ".join(errors))
    return annotation


def validate_annotation(annotation: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(annotation, dict):
        return ["annotation must be an object"]
    if annotation.get("annotation_schema") != ANNOTATION_SCHEMA:
        errors.append(f"annotation_schema must equal {ANNOTATION_SCHEMA}")
    if not annotation.get("image_id"):
        errors.append("image_id is required")
    if annotation.get("coordinate_space") != "normalized_0_1":
        errors.append("coordinate_space must be normalized_0_1")
    bbox = annotation.get("bbox")
    if not isinstance(bbox, dict):
        errors.append("bbox is required")
    else:
        for key in ("x", "y", "width", "height"):
            _normalized(bbox.get(key), f"bbox.{key}", errors)
        if all(isinstance(bbox.get(key), (int, float))
               for key in ("x", "y", "width", "height")):
            if bbox["width"] <= 0 or bbox["height"] <= 0:
                errors.append("bbox width and height must be positive")
            if bbox["x"] + bbox["width"] > 1 or bbox["y"] + bbox["height"] > 1:
                errors.append("bbox must fit normalized image bounds")
    landmarks = annotation.get("landmarks", [])
    if not isinstance(landmarks, list):
        errors.append("landmarks must be an array")
        landmarks = []
    for index, point in enumerate(landmarks):
        if not isinstance(point, dict):
            errors.append(f"landmarks[{index}] must be an object")
            continue
        if not point.get("name"):
            errors.append(f"landmarks[{index}].name is required")
        _normalized(point.get("normalized_x"), f"landmarks[{index}].normalized_x", errors)
        _normalized(point.get("normalized_y"), f"landmarks[{index}].normalized_y", errors)
    for section_name in ("zones", "feature_regions"):
        section = annotation.get(section_name, {})
        if not isinstance(section, dict):
            errors.append(f"{section_name} must be an object")
            continue
        for name, region in section.items():
            if not isinstance(region, dict):
                errors.append(f"{section_name}.{name} must be an object")
                continue
            polygon = region.get("polygon", [])
            if not isinstance(polygon, list) or len(polygon) < 3:
                errors.append(
                    f"{section_name}.{name}.polygon requires at least three points"
                )
                continue
            for index, point in enumerate(polygon):
                if not isinstance(point, dict):
                    errors.append(
                        f"{section_name}.{name}.polygon[{index}] must be an object"
                    )
                    continue
                _normalized(
                    point.get("x"),
                    f"{section_name}.{name}.polygon[{index}].x", errors,
                )
                _normalized(
                    point.get("y"),
                    f"{section_name}.{name}.polygon[{index}].y", errors,
                )
    measurements = annotation.get("measurements", {})
    if not isinstance(measurements, dict):
        errors.append("measurements must be an object")
    else:
        for name, measurement in measurements.items():
            if not isinstance(measurement, dict):
                errors.append(f"measurements.{name} must be an object")
                continue
            if not isinstance(measurement.get("value"), (int, float)):
                errors.append(f"measurements.{name}.value must be numeric")
            if not isinstance(measurement.get("tolerance"), (int, float)):
                errors.append(f"measurements.{name}.tolerance must be numeric")
    shape = annotation.get("face_shape", {})
    if not isinstance(shape.get("label"), str) or not shape.get("label"):
        errors.append("face_shape.label is required")
    return errors


def _normalized(value: Any, location: str, errors: list[str]) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= 1
    ):
        errors.append(f"{location} must be within 0..1")


def evaluate(annotation: dict, output: dict, *, raster_size: int = 256) -> dict:
    """Compute dataset metrics without making a benchmark accuracy claim."""
    errors = validate_annotation(annotation)
    if errors:
        raise ValueError("Invalid face scan annotation: " + "; ".join(errors))
    predicted_landmarks = output.get("landmarks", {}).get("named", {})
    landmark_errors = []
    calibration_pairs = []
    for truth in annotation.get("landmarks", []):
        predicted = predicted_landmarks.get(truth["name"])
        if predicted:
            error = math.hypot(
                float(predicted["normalized_x"]) - truth["normalized_x"],
                float(predicted["normalized_y"]) - truth["normalized_y"],
            )
            landmark_errors.append(error)
            calibration_pairs.append((float(predicted.get("confidence", 0)), error <= .03))

    truth_bbox = annotation["bbox"]
    predicted_bbox = output.get("face_detection", {}).get("bbox")
    bbox_iou = None
    if predicted_bbox:
        predicted_simple = {
            "x": predicted_bbox["normalized_x"],
            "y": predicted_bbox["normalized_y"],
            "width": predicted_bbox["normalized_width"],
            "height": predicted_bbox["normalized_height"],
        }
        bbox_iou = _bbox_iou(truth_bbox, predicted_simple)

    zone_ious = {}
    predicted_zones = output.get("traditional_zones", {}).get("zones", {})
    for name, truth in annotation.get("zones", {}).items():
        predicted = predicted_zones.get(name, {}).get("polygon", [])
        if predicted:
            first = _polygon_mask(truth["polygon"], raster_size)
            second = _polygon_mask(predicted, raster_size)
            intersection = np.count_nonzero((first > 0) & (second > 0))
            union = np.count_nonzero((first > 0) | (second > 0))
            zone_ious[name] = float(intersection / max(union, 1))

    feature_region_ious = {}
    predicted_regions = output.get("feature_regions") or predicted_zones
    for name, truth in annotation.get("feature_regions", {}).items():
        predicted = predicted_regions.get(name, {}).get("polygon", [])
        if predicted:
            first = _polygon_mask(truth["polygon"], raster_size)
            second = _polygon_mask(predicted, raster_size)
            intersection = np.count_nonzero((first > 0) & (second > 0))
            union = np.count_nonzero((first > 0) | (second > 0))
            feature_region_ious[name] = float(intersection / max(union, 1))

    measurement_errors = {}
    for path, truth in annotation.get("measurements", {}).items():
        predicted = _nested_value(output, path)
        if isinstance(predicted, dict):
            predicted = predicted.get("value", predicted.get("normalized"))
        if isinstance(predicted, (int, float)):
            absolute_error = abs(float(predicted) - float(truth["value"]))
            measurement_errors[path] = {
                "predicted": float(predicted),
                "truth": float(truth["value"]),
                "absolute_error": absolute_error,
                "within_tolerance": absolute_error <= float(truth["tolerance"]),
            }

    truth_shape = annotation["face_shape"]["label"]
    predicted_shape = output.get("face_shape", {})
    predicted_label = predicted_shape.get("label")
    shape_correct = predicted_label == truth_shape
    shape_confidence = float(predicted_shape.get("confidence", 0))
    calibration_pairs.append((shape_confidence, shape_correct))
    brier = float(np.mean([
        (confidence - float(correct)) ** 2 for confidence, correct in calibration_pairs
    ])) if calibration_pairs else None
    return {
        "annotation_schema": ANNOTATION_SCHEMA,
        "landmark_normalized_error": {
            "mean": float(np.mean(landmark_errors)) if landmark_errors else None,
            "median": float(np.median(landmark_errors)) if landmark_errors else None,
            "matched": len(landmark_errors),
        },
        "bbox_iou": bbox_iou,
        "zone_iou": zone_ious,
        "feature_region_iou": feature_region_ious,
        "measurement_errors": measurement_errors,
        "face_shape_classification": {
            "truth": truth_shape, "predicted": predicted_label,
            "correct": shape_correct,
        },
        "confidence_calibration": {
            "brier_score": brier, "sample_count": len(calibration_pairs)
        },
        "disclaimer": "Offline evaluation only; no benchmark accuracy is claimed.",
    }


def _bbox_iou(first: dict, second: dict) -> float:
    left = max(first["x"], second["x"])
    top = max(first["y"], second["y"])
    right = min(first["x"] + first["width"], second["x"] + second["width"])
    bottom = min(first["y"] + first["height"], second["y"] + second["height"])
    intersection = max(0, right - left) * max(0, bottom - top)
    first_area = first["width"] * first["height"]
    second_area = second["width"] * second["height"]
    return float(intersection / max(first_area + second_area - intersection, 1e-12))


def _nested_value(value: dict, path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _polygon_mask(points: list[dict], size: int) -> np.ndarray:
    mask = np.zeros((size, size), np.uint8)
    polygon = np.int32([
        [round(point["x"] * (size - 1)), round(point["y"] * (size - 1))]
        for point in points
    ])
    cv2.fillPoly(mask, [polygon], 255)
    return mask
