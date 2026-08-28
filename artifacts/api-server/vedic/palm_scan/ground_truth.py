"""Versioned annotation loading, validation, and offline evaluation utilities."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ANNOTATION_SCHEMA = "palm_scan_annotation/1.0"


def make_example_annotation() -> dict:
    """Small valid factory for tests/tooling; coordinates are illustrative GT."""
    return {
        "annotation_schema": ANNOTATION_SCHEMA,
        "image_id": "synthetic-example",
        "coordinate_space": "normalized_0_1",
        "landmarks": [
            {"id": 0, "name": "wrist", "normalized_x": .5, "normalized_y": .85}
        ],
        "paths": [{
            "id": "crease-1", "semantic_identity": "ambiguous",
            "points": [{"x": .3, "y": .6}, {"x": .7, "y": .6}],
        }],
        "segmentations": {
            "palm_region": {
                "polygon": [
                    {"x": .3, "y": .4}, {"x": .7, "y": .4},
                    {"x": .7, "y": .85}, {"x": .3, "y": .85},
                ]
            }
        },
        "mounts": {
            "Venus": {
                "polygon": [
                    {"x": .30, "y": .52}, {"x": .47, "y": .50},
                    {"x": .50, "y": .80}, {"x": .36, "y": .84},
                ]
            }
        },
        "markings": [],
        "detections": [{"type": "ambiguous_crease", "present": True}],
    }


def load_annotation(value: dict | str | Path) -> dict:
    if isinstance(value, dict):
        annotation = value
    else:
        text = Path(value).read_text(encoding="utf-8")
        annotation = json.loads(text)
    errors = validate_annotation(annotation)
    if errors:
        raise ValueError("Invalid palm annotation: " + "; ".join(errors))
    return annotation


def validate_annotation(annotation: Any) -> list[str]:
    errors = []
    if not isinstance(annotation, dict):
        return ["annotation must be an object"]
    if annotation.get("annotation_schema") != ANNOTATION_SCHEMA:
        errors.append(f"annotation_schema must equal {ANNOTATION_SCHEMA}")
    if not annotation.get("image_id"):
        errors.append("image_id is required")
    if annotation.get("coordinate_space") != "normalized_0_1":
        errors.append("coordinate_space must be normalized_0_1")
    for index, point in enumerate(annotation.get("landmarks", [])):
        _check_point(point, f"landmarks[{index}]", errors, normalized_keys=True)
    for path_index, path in enumerate(annotation.get("paths", [])):
        if len(path.get("points", [])) < 2:
            errors.append(f"paths[{path_index}].points requires at least two points")
        for point_index, point in enumerate(path.get("points", [])):
            _check_point(point, f"paths[{path_index}].points[{point_index}]", errors)
    for name, section in annotation.get("segmentations", {}).items():
        if len(section.get("polygon", [])) < 3:
            errors.append(f"segmentations.{name}.polygon requires at least three points")
        for index, point in enumerate(section.get("polygon", [])):
            _check_point(point, f"segmentations.{name}.polygon[{index}]", errors)
    for name, mount in annotation.get("mounts", {}).items():
        if len(mount.get("polygon", [])) < 3:
            errors.append(f"mounts.{name}.polygon requires at least three points")
        for index, point in enumerate(mount.get("polygon", [])):
            _check_point(point, f"mounts.{name}.polygon[{index}]", errors)
    for index, marking in enumerate(annotation.get("markings", [])):
        if not marking.get("type"):
            errors.append(f"markings[{index}].type is required")
        for point_index, point in enumerate(marking.get("coordinates", [])):
            _check_point(point, f"markings[{index}].coordinates[{point_index}]", errors)
    return errors


def _check_point(point: dict, location: str, errors: list[str], normalized_keys: bool = False) -> None:
    x_key, y_key = ("normalized_x", "normalized_y") if normalized_keys else ("x", "y")
    for key in (x_key, y_key):
        value = point.get(key)
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            errors.append(f"{location}.{key} must be within 0..1")


def evaluate(annotation: dict, output: dict, *, raster_size: int = 256) -> dict:
    """Compare output to GT. Metrics are dataset-neutral; no accuracy claim."""
    errors = validate_annotation(annotation)
    if errors:
        raise ValueError("Invalid palm annotation: " + "; ".join(errors))
    output_landmarks = {
        item.get("name", str(item.get("id"))): item for item in output.get("landmarks", [])
    }
    landmark_errors = []
    for truth in annotation.get("landmarks", []):
        predicted = output_landmarks.get(truth.get("name", str(truth.get("id"))))
        if predicted:
            dx = float(predicted.get("normalized_x", predicted.get("x", 0))) - truth["normalized_x"]
            dy = float(predicted.get("normalized_y", predicted.get("y", 0))) - truth["normalized_y"]
            landmark_errors.append(float(np.hypot(dx, dy)))

    predicted_paths = [
        item.get("path", []) for item in output.get("secondary_lines", {}).get("crease_candidates", [])
        if len(item.get("path", [])) >= 2
    ]
    path_errors = []
    for truth_path in annotation.get("paths", []):
        truth_points = np.array([(p["x"], p["y"]) for p in truth_path["points"]])
        if predicted_paths:
            path_errors.append(min(
                _chamfer(truth_points, np.array([(p["x"], p["y"]) for p in candidate]))
                for candidate in predicted_paths
            ))

    ious = {}
    for name, truth_section in annotation.get("segmentations", {}).items():
        predicted = output.get("segmentation", {}).get(name, {}).get("polygon", [])
        if predicted:
            truth_mask = _polygon_mask(truth_section["polygon"], raster_size)
            predicted_mask = _polygon_mask(predicted, raster_size)
            intersection = np.count_nonzero((truth_mask > 0) & (predicted_mask > 0))
            union = np.count_nonzero((truth_mask > 0) | (predicted_mask > 0))
            ious[name] = float(intersection / max(union, 1))

    mount_ious = {}
    for name, truth_mount in annotation.get("mounts", {}).items():
        predicted = output.get("mounts", {}).get(name, {}).get("region_polygon", [])
        if predicted:
            truth_mask = _polygon_mask(truth_mount["polygon"], raster_size)
            predicted_mask = _polygon_mask(predicted, raster_size)
            intersection = np.count_nonzero((truth_mask > 0) & (predicted_mask > 0))
            union = np.count_nonzero((truth_mask > 0) | (predicted_mask > 0))
            mount_ious[name] = float(intersection / max(union, 1))

    truth_detections = annotation.get("detections", [])
    truth_labels = [
        str(item.get("type")) for item in truth_detections if item.get("present")
    ]
    predicted_items = []
    for item in output.get("secondary_lines", {}).get("crease_candidates", []):
        semantic = item.get("semantic_identity", "ambiguous")
        predicted_items.append((
            "ambiguous_crease" if semantic == "ambiguous" else str(semantic),
            float(item.get("confidence", 0)),
        ))
    for item in output.get("special_markings", {}).get("candidates", []):
        predicted_items.append((str(item.get("type", "ambiguous")), float(item.get("confidence", 0))))
    remaining_truth = Counter(truth_labels)
    outcomes = []
    for label, _ in predicted_items:
        matched = remaining_truth[label] > 0
        outcomes.append(1.0 if matched else 0.0)
        if matched:
            remaining_truth[label] -= 1
    true_positive = int(sum(outcomes))
    false_positive = len(predicted_items) - true_positive
    false_negative = sum(remaining_truth.values())
    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)
    accuracy = true_positive / max(true_positive + false_positive + false_negative, 1)

    paired = [
        (confidence, outcome)
        for (_, confidence), outcome in zip(predicted_items, outcomes)
    ]
    brier = float(np.mean([(confidence - outcome) ** 2 for confidence, outcome in paired])) if paired else None
    calibration_gap = float(np.mean([
        abs(confidence - outcome) for confidence, outcome in paired
    ])) if paired else None
    semantic_metrics, semantic_pairs = _semantic_line_metrics(
        annotation, output, raster_size
    )
    semantic_brier = (
        float(np.mean([(confidence - outcome) ** 2
                       for confidence, outcome in semantic_pairs]))
        if semantic_pairs else None
    )
    return {
        "annotation_schema": ANNOTATION_SCHEMA,
        "landmark_coordinate_error": {
            "mean_normalized": float(np.mean(landmark_errors)) if landmark_errors else None,
            "matched": len(landmark_errors),
        },
        "path_error": {
            "mean_symmetric_chamfer_normalized": float(np.mean(path_errors)) if path_errors else None,
            "matched": len(path_errors),
        },
        "segmentation_iou": ious,
        "mount_region_iou": mount_ious,
        "detection": {
            "precision": precision, "recall": recall,
            "accuracy": accuracy, "detection_accuracy": accuracy,
            "true_positive": true_positive, "false_positive": false_positive,
            "false_negative": false_negative,
        },
        "confidence_calibration": {
            "brier_score": brier, "mean_absolute_calibration_gap": calibration_gap,
            "sample_count": len(paired),
            "semantic_line_brier_score": semantic_brier,
            "semantic_line_sample_count": len(semantic_pairs),
        },
        "semantic_line_metrics": semantic_metrics,
        "disclaimer": "Offline comparison only; no benchmark accuracy is claimed.",
    }


def _chamfer(first: np.ndarray, second: np.ndarray) -> float:
    distances = np.linalg.norm(first[:, None, :] - second[None, :, :], axis=2)
    return float((np.mean(np.min(distances, axis=1)) + np.mean(np.min(distances, axis=0))) / 2)


def _polygon_mask(points: list[dict], size: int) -> np.ndarray:
    mask = np.zeros((size, size), np.uint8)
    polygon = np.int32([
        [round(point["x"] * (size - 1)), round(point["y"] * (size - 1))]
        for point in points
    ])
    cv2.fillPoly(mask, [polygon], 255)
    return mask


def _semantic_line_metrics(
    annotation: dict, output: dict, size: int
) -> tuple[dict, list[tuple[float, float]]]:
    """Evaluate named paths from either legacy paths or dataset-style lines."""
    truth: dict[str, dict] = {}
    for item in annotation.get("paths", []):
        name = item.get("semantic_identity")
        if name and name not in {"ambiguous", "unknown"}:
            truth[str(name)] = {"path": item.get("points", []), "readability": "clear"}
    for name, item in annotation.get("major_lines", {}).items():
        if isinstance(item, dict):
            truth[str(name)] = item
    predicted = output.get("major_lines", {})
    metrics: dict[str, dict] = {}
    calibration: list[tuple[float, float]] = []
    for name, expected in truth.items():
        truth_path = expected.get("path", [])
        readability = expected.get("readability", "clear")
        actual = predicted.get(name, {}) if isinstance(predicted, dict) else {}
        actual_path = actual.get("path", []) if isinstance(actual, dict) else []
        expected_present = readability != "unknown" and len(truth_path) >= 2
        predicted_present = bool(actual.get("detected") and len(actual_path) >= 2)
        confidence = float(np.clip(actual.get("confidence", 0), 0, 1))
        calibration.append((confidence, 1.0 if expected_present == predicted_present else 0.0))
        item = {
            "readability": readability,
            "expected_present": expected_present,
            "predicted_present": predicted_present,
            "path_chamfer_normalized": None,
            "mask_iou": None,
            "dice": None,
        }
        if expected_present and predicted_present:
            truth_points = np.asarray([(point["x"], point["y"]) for point in truth_path])
            actual_points = np.asarray([(point["x"], point["y"]) for point in actual_path])
            item["path_chamfer_normalized"] = _chamfer(truth_points, actual_points)
            truth_mask = _line_mask(truth_path, size)
            actual_mask = _line_mask(actual_path, size)
            intersection = np.count_nonzero((truth_mask > 0) & (actual_mask > 0))
            truth_count = np.count_nonzero(truth_mask)
            actual_count = np.count_nonzero(actual_mask)
            union = np.count_nonzero((truth_mask > 0) | (actual_mask > 0))
            item["mask_iou"] = float(intersection / max(union, 1))
            item["dice"] = float(2 * intersection / max(truth_count + actual_count, 1))
        metrics[name] = item
    return metrics, calibration


def _line_mask(points: list[dict], size: int) -> np.ndarray:
    mask = np.zeros((size, size), np.uint8)
    path = np.int32([
        [round(point["x"] * (size - 1)), round(point["y"] * (size - 1))]
        for point in points
    ])
    if len(path) >= 2:
        cv2.polylines(mask, [path], False, 255, max(2, round(size * .012)))
    return mask
