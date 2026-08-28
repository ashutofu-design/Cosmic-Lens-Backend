"""Deterministic Phase 1 face measurements with no interpretive inference."""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

import cv2
import numpy as np

from vedic.face_reading import image_io

from .backend import DetectionBatch, FaceCandidate, FaceLandmarkBackend, LegacyMediaPipeBackend
from .schema import SCHEMA_VERSION, validate_result

# Stable practical subset of MediaPipe Face Mesh (478 with refined irises).
NAMED_INDICES = {
    "forehead_center": 10, "face_left": 234, "face_right": 454,
    "glabella": 9, "chin_tip": 152, "nose_bridge": 168, "nose_bridge_mid": 197,
    "nose_tip": 1, "subnasale": 2,
    "nose_left": 98, "nose_right": 327, "mouth_left": 61, "mouth_right": 291,
    "upper_lip_top": 0, "upper_lip": 13, "lower_lip": 14,
    "lower_lip_bottom": 17, "philtrum_top": 164,
    "right_eye_outer": 33, "right_eye_inner": 133, "right_eye_top": 159,
    "right_eye_bottom": 145, "left_eye_inner": 362, "left_eye_outer": 263,
    "left_eye_top": 386, "left_eye_bottom": 374,
    "right_iris_center": 468, "left_iris_center": 473,
    "right_brow_outer": 70, "right_brow_inner": 107, "right_brow_top": 105,
    "left_brow_inner": 336, "left_brow_outer": 300, "left_brow_top": 334,
    "right_jaw": 172, "left_jaw": 397, "right_chin": 176, "left_chin": 400,
    "right_temple": 127, "left_temple": 356,
    "right_cheek": 234, "left_cheek": 454,
}

GROUPS = {
    "boundary": ["forehead_center", "face_left", "chin_tip", "face_right"],
    "eyebrows": ["right_brow_outer", "right_brow_top", "right_brow_inner",
                 "left_brow_inner", "left_brow_top", "left_brow_outer"],
    "eyes": ["right_eye_outer", "right_eye_top", "right_eye_inner", "right_eye_bottom",
             "left_eye_inner", "left_eye_top", "left_eye_outer", "left_eye_bottom"],
    "nose": ["nose_bridge", "nose_tip", "nose_left", "nose_right"],
    "mouth": ["mouth_left", "upper_lip", "mouth_right", "lower_lip"],
    "jaw_chin": ["face_left", "right_jaw", "right_chin", "chin_tip",
                 "left_chin", "left_jaw", "face_right"],
}

PAIR_GROUPS = {
    "forehead": [("right_temple", "left_temple")],
    "eyes": [("right_eye_outer", "left_eye_outer"), ("right_eye_inner", "left_eye_inner"),
             ("right_eye_top", "left_eye_top"), ("right_eye_bottom", "left_eye_bottom")],
    "eyebrows": [("right_brow_outer", "left_brow_outer"),
                 ("right_brow_inner", "left_brow_inner"),
                 ("right_brow_top", "left_brow_top")],
    "nose": [("nose_left", "nose_right")],
    "mouth": [("mouth_left", "mouth_right")],
    "jaw": [("right_jaw", "left_jaw"), ("face_left", "face_right")],
    "chin": [("right_chin", "left_chin")],
}


def _clip(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _distance(first: dict, second: dict) -> float:
    return math.hypot(first["x"] - second["x"], first["y"] - second["y"])


def _bbox_iou(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    intersection_width = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    intersection_height = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    intersection = intersection_width * intersection_height
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0


def _measurement(
    value: float | None,
    scale: float | None = None,
    *,
    method: str,
    confidence: float = 0.0,
) -> dict:
    if value is None:
        return {
            "status": "unknown", "raw_px": None, "normalized": None,
            "method": method, "confidence": 0.0,
        }
    return {
        "status": "measured",
        "raw_px": round(float(value), 3),
        "normalized": round(float(value) / scale, 6) if scale else None,
        "method": method,
        "confidence": _clip(confidence),
    }


def _issue(
    code: str,
    severity: str,
    message: str,
    observable: bool = True,
    *,
    detail_code: str | None = None,
) -> dict:
    value = {
        "code": code, "severity": severity, "message": message,
        "observable": observable,
    }
    if detail_code:
        value["detail_code"] = detail_code
    return value


class FaceScanEngine:
    def __init__(self, backend: FaceLandmarkBackend | None = None, *, include_mesh: bool = True):
        self.backend = backend or LegacyMediaPipeBackend()
        self.include_mesh = include_mesh

    def scan(self, image_bytes: bytes, *, mirror: bool = False) -> tuple[dict, np.ndarray | None]:
        result, artifacts = self.scan_with_artifacts(image_bytes, mirror=mirror)
        return result, artifacts.get("annotated")

    def scan_with_artifacts(
        self, image_bytes: bytes, *, mirror: bool = False
    ) -> tuple[dict, dict[str, np.ndarray]]:
        scan_id = uuid.uuid4().hex
        decoded, error = image_io.decode_image(image_bytes, mirror=mirror)
        metadata = {
            "scan_id": scan_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "measurement_only": True,
            "coordinate_space": "image_pixels_and_normalized_0_1",
            "dimensions": None,
            "image_format": None,
            "bytes_in": len(image_bytes),
            "mirror_applied": bool(mirror),
            "detector_backend": None,
        }
        if decoded is None:
            quality = self._empty_quality(error or "decode_failed")
            return self._empty_result(metadata, quality), {}

        rgb = decoded.rgb
        height, width = rgb.shape[:2]
        metadata.update({
            "dimensions": {"width": width, "height": height},
            "image_format": decoded.format,
            "original_dimensions": {
                "width": decoded.original_width, "height": decoded.original_height,
            },
            "downscaled": decoded.downscaled,
            "mirror_applied": decoded.mirror_applied,
        })
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        batch = self.backend.detect(image_bytes, rgb)
        metadata["detector_backend"] = batch.backend
        metadata["detector_notes"] = list(batch.notes)
        primary, selection_issue = self._select_primary(batch)
        quality = self._quality(gray, batch, primary, selection_issue)
        if primary is None or not quality["usable"]:
            return self._empty_result(metadata, quality, batch=batch), {}

        landmarks = self._project_landmarks(primary, width, height)
        if not self.include_mesh:
            landmarks["full_mesh_compact"] = []
        if len(landmarks["named"]) < 20:
            quality["issues"].append(_issue(
                "incomplete_landmarks", "error", "Required facial landmarks are incomplete."
            ))
            quality["gate"] = "failed"
            quality["usable"] = False
            quality["overall_score"] = _clip(quality["overall_score"] * .45)
            return self._empty_result(metadata, quality, batch=batch), {}

        face_detection = self._face_detection(batch, primary, width, height)
        measurement_confidence = min(primary.confidence, quality["overall_score"])
        geometry = self._geometry(
            landmarks["named"], width, height, measurement_confidence
        )
        symmetry = self._symmetry(
            landmarks["named"], width, measurement_confidence
        )
        regions = self._regions(
            landmarks["named"], geometry, symmetry, width, height,
            measurement_confidence,
        )
        zones = self._zones(landmarks["named"], measurement_confidence)
        surface = self._surface(
            rgb, face_detection["bbox"], measurement_confidence
        )
        shape = self._face_shape(geometry, measurement_confidence)
        confidence = self._confidence(primary, quality, geometry, symmetry, shape)
        method_agreement = self._method_agreement(primary)
        result = {
            "schema_version": SCHEMA_VERSION,
            "metadata": metadata,
            "quality": quality,
            "face_detection": face_detection,
            "landmarks": landmarks,
            "face_geometry": geometry,
            "symmetry": symmetry,
            "forehead": regions["forehead"],
            "eyebrows": regions["eyebrows"],
            "eyes": regions["eyes"],
            "nose": regions["nose"],
            "mouth": regions["mouth"],
            "jaw": regions["jaw"],
            "chin": regions["chin"],
            "face_shape": shape,
            "skin_surface_features": surface,
            "traditional_zones": zones,
            "confidence": confidence,
            "validation_status": {
                "status": "valid_measurements",
                "schema_version": SCHEMA_VERSION,
                "warnings": [item["code"] for item in quality["issues"]
                             if item["severity"] == "warning"],
                "method_agreement": method_agreement,
            },
            "annotated_image_reference": f"/api/face-scan/{scan_id}/annotated",
        }
        schema_errors = validate_result(result)
        if schema_errors:
            result["validation_status"] = {
                "status": "invalid_schema",
                "schema_version": SCHEMA_VERSION,
                "warnings": [],
                "errors": schema_errors,
            }
            result["annotated_image_reference"] = None
            return result, {}
        annotated = self._annotate_from_result(rgb, result)
        return result, {"annotated": annotated}

    @staticmethod
    def _select_primary(
        batch: DetectionBatch,
    ) -> tuple[FaceCandidate | None, dict | None]:
        candidates = list(batch.candidates)
        if batch.face_count <= 0 or not candidates:
            return None, _issue("face_not_detected", "error", "No face was detected.")
        if batch.face_count != len(candidates):
            return None, _issue(
                "multiple_faces_ambiguous", "error",
                "Detector did not expose enough per-face evidence to select a primary."
            )
        if len(candidates) == 1:
            return candidates[0], None
        ranked = sorted(
            candidates,
            key=lambda item: item.bbox[2] * item.bbox[3] * max(item.confidence, .01),
            reverse=True,
        )
        first, second = ranked[:2]
        first_area = first.bbox[2] * first.bbox[3]
        second_area = second.bbox[2] * second.bbox[3]
        dominant = (
            first.evidence.get("dominant_primary") is True
            or (first_area >= second_area * 1.5 and first.confidence >= second.confidence - .08)
        )
        if not dominant:
            return None, _issue(
                "multiple_faces_ambiguous", "error",
                "Multiple faces are present without a dominant primary."
            )
        return first, _issue(
            "multiple_faces_primary_selected", "warning",
            "A dominant primary face was selected using area and confidence evidence."
        )

    def _quality(
        self,
        gray: np.ndarray,
        batch: DetectionBatch,
        primary: FaceCandidate | None,
        selection_issue: dict | None,
    ) -> dict:
        height, width = gray.shape
        minimum = min(height, width)
        resolution = _clip((minimum - 256) / 512)
        blur_value = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blur = _clip(blur_value / 120.0)
        brightness = float(gray.mean())
        contrast = float(gray.std())
        brightness_score = _clip(1.0 - abs(brightness - 135.0) / 120.0)
        contrast_score = _clip(contrast / 45.0)
        lighting = _clip(.65 * brightness_score + .35 * contrast_score)
        exposure = _clip(1.0 - float(((gray < 8) | (gray > 247)).mean()) * 2.5)
        area = primary.bbox[2] * primary.bbox[3] if primary else 0.0
        area_visibility = _clip(area / .18)
        pose = primary.pose if primary else {}
        yaw = abs(float(pose.get("yaw_degrees", 0)))
        pitch = abs(float(pose.get("pitch_degrees", 0)))
        roll = abs(float(pose.get("roll_degrees", 0)))
        pose_score = _clip(1.0 - (yaw / 45 + pitch / 40 + roll / 35) / 3)
        evidence = primary.evidence if primary else {}
        detector_bbox = evidence.get("independent_detection_bbox")
        bbox_iou = (
            _bbox_iou(primary.bbox, tuple(detector_bbox))
            if primary and isinstance(detector_bbox, (list, tuple))
            and len(detector_bbox) == 4 else None
        )
        visible_parts = {
            name: bool(evidence.get(f"{name}_visible", True if primary else False))
            for name in ("eyes", "nose", "mouth", "chin")
        }
        feature_visibility = sum(visible_parts.values()) / 4.0
        visibility = _clip(.6 * area_visibility + .4 * feature_visibility)
        occlusion_flags = {
            "glasses": bool(evidence.get("glasses_observed", False)),
            "mask": bool(evidence.get("mask_observed", False)),
            "hair_obstruction": bool(evidence.get("hair_obstruction_observed", False)),
        }
        occlusion = _clip(
            feature_visibility
            - .1 * sum(occlusion_flags.values())
        )
        issues = []
        for note in batch.notes:
            issues.append(_issue(
                "detector_warning", "warning",
                note.replace("_", " ").capitalize(), detail_code=note,
            ))
        if selection_issue:
            issues.append(selection_issue)
        if minimum < 256:
            issues.append(_issue(
                "insufficient_resolution", "error", "Image resolution is too low."
            ))
        elif minimum < 512:
            issues.append(_issue("limited_resolution", "warning", "Image resolution limits detail."))
        if blur < .18:
            issues.append(_issue(
                "excessive_blur", "error", "Image is too blurred for measurement."
            ))
        elif blur < .35:
            issues.append(_issue("soft_focus", "warning", "Image focus is soft."))
        if brightness < 42:
            issues.append(_issue(
                "poor_lighting", "error", "Image is too dark.",
                detail_code="low_light",
            ))
        elif brightness > 238:
            issues.append(_issue(
                "poor_lighting", "error", "Image is overexposed.",
                detail_code="overexposed",
            ))
        elif contrast < 12:
            issues.append(_issue("low_contrast", "warning", "Image contrast is limited."))
        if primary and area < .05:
            issues.append(_issue("face_too_small", "error", "Face is too small in frame."))
        elif primary and area > .82:
            issues.append(_issue("face_too_close", "warning", "Face is very close to camera."))
        if primary:
            x, y, w, h = primary.bbox
            if min(x, y, 1 - x - w, 1 - y - h) < .008:
                issues.append(_issue("face_cropped", "error", "Face boundary is cropped."))
        if bbox_iou is not None and bbox_iou < .35:
            issues.append(_issue(
                "detector_disagreement", "error",
                "Face detector and landmark mesh boundaries disagree substantially."
            ))
        if yaw > 28:
            issues.append(_issue(
                "extreme_angle", "error", "Head yaw is too large.",
                detail_code="excessive_yaw",
            ))
        if pitch > 28:
            issues.append(_issue(
                "extreme_angle", "error", "Head pitch is too large.",
                detail_code="excessive_pitch",
            ))
        if roll > 22:
            issues.append(_issue(
                "extreme_angle", "error", "Head roll is too large.",
                detail_code="head_tilt",
            ))
        for name, visible in visible_parts.items():
            if not visible:
                issues.append(_issue(
                    "important_landmarks_hidden", "error",
                    f"{name.title()} region is not visible.",
                    detail_code=f"{name}_not_visible",
                ))
        for name, observed in occlusion_flags.items():
            if observed:
                issues.append(_issue(
                    f"{name}_obstruction", "warning",
                    f"{name.replace('_', ' ').title()} was observed.", True
                ))
        hard = any(item["severity"] == "error" for item in issues)
        overall = _clip(np.mean([
            resolution, blur, lighting, exposure, visibility, occlusion, pose_score
        ]) * (0.5 if hard else 1.0))
        return {
            "gate": "failed" if hard else "passed",
            "usable": not hard,
            "overall_score": overall,
            "resolution_score": resolution,
            "blur_score": blur,
            "lighting_score": lighting,
            "visibility_score": visibility,
            "occlusion_score": occlusion,
            "exposure_score": exposure,
            "pose_score": pose_score,
            "raw_evidence": {
                "width_px": width, "height_px": height,
                "brightness_mean": round(brightness, 3),
                "contrast_stddev": round(contrast, 3),
                "laplacian_variance": round(blur_value, 3),
                "face_area_ratio": round(area, 6),
                "pose_degrees": {"yaw": yaw, "pitch": pitch, "roll": roll},
                "feature_visibility": visible_parts,
                "observable_obstructions": occlusion_flags,
                "detector_mesh_bbox_iou": round(bbox_iou, 6)
                if bbox_iou is not None else None,
            },
            "issues": issues,
        }

    @staticmethod
    def _project_landmarks(candidate: FaceCandidate, width: int, height: int) -> dict:
        named = {}
        for name, index in NAMED_INDICES.items():
            if index >= len(candidate.landmarks):
                continue
            x, y, z = candidate.landmarks[index]
            confidence = (
                candidate.landmark_confidences[index]
                if index < len(candidate.landmark_confidences)
                else candidate.confidence
            )
            valid = 0 <= x <= 1 and 0 <= y <= 1
            point = {
                "index": index, "x": round(x * width, 3), "y": round(y * height, 3),
                "normalized_x": round(x, 6), "normalized_y": round(y, 6),
                "z_relative": round(z, 6), "confidence": _clip(confidence),
                "status": "detected" if valid else "out_of_frame",
            }
            if valid:
                named[name] = point
        full_mesh = [
            [round(x, 6), round(y, 6), round(z, 6),
             _clip(candidate.landmark_confidences[index]
                   if index < len(candidate.landmark_confidences) else candidate.confidence),
             "detected" if 0 <= x <= 1 and 0 <= y <= 1 else "out_of_frame"]
            for index, (x, y, z) in enumerate(candidate.landmarks)
        ]
        return {
            "coordinate_contract": {
                "x_y": "decoded_image_pixels",
                "normalized_x_y": "strict_image_normalized_0_1",
                "z_relative": "backend_relative_not_physical_depth",
            },
            "named": named,
            "groups": GROUPS,
            "full_mesh_compact": full_mesh,
            "full_mesh_fields": [
                "normalized_x", "normalized_y", "z_relative", "confidence", "status"
            ],
        }

    @staticmethod
    def _face_detection(
        batch: DetectionBatch, primary: FaceCandidate, image_width: int, image_height: int
    ) -> dict:
        x, y, width, height = primary.bbox
        yaw = float(primary.pose.get("yaw_degrees", 0))
        orientation = (
            "front" if abs(yaw) < 8
            else "slight_left" if -28 <= yaw < 0
            else "slight_right" if 0 < yaw <= 28
            else "extreme_angle"
        )
        return {
            "face_count": batch.face_count,
            "selection_policy": "single_or_dominant_area_confidence",
            "primary_selection_status": "selected",
            "bbox": {
                "normalized_x": round(x, 6), "normalized_y": round(y, 6),
                "normalized_width": round(width, 6), "normalized_height": round(height, 6),
                "x_px": round(x * image_width, 3),
                "y_px": round(y * image_height, 3),
                "width_px": round(width * image_width, 3),
                "height_px": round(height * image_height, 3),
            },
            "center": {
                "normalized_x": round(x + width / 2, 6),
                "normalized_y": round(y + height / 2, 6),
                "x_px": round((x + width / 2) * image_width, 3),
                "y_px": round((y + height / 2) * image_height, 3),
            },
            "pose": {
                "yaw_degrees": round(yaw, 3),
                "pitch_degrees": round(float(primary.pose.get("pitch_degrees", 0)), 3),
                "roll_degrees": round(float(primary.pose.get("roll_degrees", 0)), 3),
                "tilt_degrees": round(float(primary.pose.get("roll_degrees", 0)), 3),
            },
            "orientation": {
                "label": orientation,
                "confidence": _clip(primary.confidence),
                "method": "head_pose_yaw_threshold",
            },
            "confidence": _clip(primary.confidence),
        }

    @staticmethod
    def _geometry(
        points: dict, width: int, height: int, confidence: float
    ) -> dict:
        def d(a: str, b: str) -> float | None:
            return _distance(points[a], points[b]) if a in points and b in points else None

        face_length = d("forehead_center", "chin_tip")
        face_width = d("face_left", "face_right")
        thirds = []
        if all(name in points for name in ("forehead_center", "nose_bridge", "nose_tip", "chin_tip")):
            thirds = [
                _measurement(d("forehead_center", "nose_bridge"), face_length,
                             method="landmark_euclidean", confidence=confidence),
                _measurement(d("nose_bridge", "nose_tip"), face_length,
                             method="landmark_euclidean", confidence=confidence),
                _measurement(d("nose_tip", "chin_tip"), face_length,
                             method="landmark_euclidean", confidence=confidence),
            ]
        return {
            "confidence": _clip(confidence),
            "face_length": _measurement(
                face_length, height, method="landmark_euclidean",
                confidence=confidence,
            ),
            "face_width": _measurement(
                face_width, width, method="landmark_euclidean",
                confidence=confidence,
            ),
            "aspect_ratio": {
                "status": "measured" if face_length and face_width else "unknown",
                "value": round(face_length / face_width, 6) if face_length and face_width else None,
                "method": "face_length_divided_by_width",
                "confidence": _clip(confidence) if face_length and face_width else 0.0,
            },
            "forehead_width": _measurement(d("right_temple", "left_temple"), width,
                                            method="landmark_euclidean",
                                            confidence=confidence),
            "cheek_width": _measurement(d("right_cheek", "left_cheek"), width,
                                        method="landmark_euclidean",
                                        confidence=confidence),
            "jaw_width": _measurement(d("right_jaw", "left_jaw"), width,
                                      method="landmark_euclidean",
                                      confidence=confidence),
            "chin_width": _measurement(d("right_chin", "left_chin"), width,
                                       method="landmark_euclidean",
                                       confidence=confidence),
            "chin_height": _measurement(
                d("lower_lip_bottom", "chin_tip"), height,
                method="landmark_euclidean", confidence=confidence,
            ),
            "facial_thirds": thirds,
            "facial_fifths": {
                "status": "measured" if face_width else "unknown",
                "reference_fifth_px": round(face_width / 5, 3) if face_width else None,
                "note": "equal-width reference only; no normative judgment",
                "confidence": _clip(confidence) if face_width else 0.0,
            },
            "interocular_distance": _measurement(d("right_eye_inner", "left_eye_inner"), width,
                                                   method="landmark_euclidean",
                                                   confidence=confidence),
            "interpupillary_distance": _measurement(d("right_iris_center", "left_iris_center"),
                                                      width, method="iris_center_euclidean",
                                                      confidence=confidence),
            "right_eye_width": _measurement(d("right_eye_outer", "right_eye_inner"), width,
                                             method="landmark_euclidean",
                                             confidence=confidence),
            "left_eye_width": _measurement(d("left_eye_inner", "left_eye_outer"), width,
                                            method="landmark_euclidean",
                                            confidence=confidence),
            "right_eye_height": _measurement(
                d("right_eye_top", "right_eye_bottom"), height,
                method="landmark_euclidean", confidence=confidence,
            ),
            "left_eye_height": _measurement(
                d("left_eye_top", "left_eye_bottom"), height,
                method="landmark_euclidean", confidence=confidence,
            ),
            "eyebrow_span": _measurement(d("right_brow_outer", "left_brow_outer"), width,
                                         method="landmark_euclidean",
                                         confidence=confidence),
            "nose_width": _measurement(d("nose_left", "nose_right"), width,
                                       method="landmark_euclidean",
                                       confidence=confidence),
            "nose_length": _measurement(d("nose_bridge", "nose_tip"), height,
                                        method="landmark_euclidean",
                                        confidence=confidence),
            "mouth_width": _measurement(d("mouth_left", "mouth_right"), width,
                                        method="landmark_euclidean",
                                        confidence=confidence),
            "lip_aperture": _measurement(d("upper_lip", "lower_lip"), height,
                                         method="landmark_euclidean",
                                         confidence=confidence),
            "upper_lip_height": _measurement(
                d("upper_lip_top", "upper_lip"), height,
                method="landmark_euclidean", confidence=confidence,
            ),
            "lower_lip_height": _measurement(
                d("lower_lip", "lower_lip_bottom"), height,
                method="landmark_euclidean", confidence=confidence,
            ),
            "philtrum_length": _measurement(
                d("philtrum_top", "upper_lip_top"), height,
                method="landmark_euclidean", confidence=confidence,
            ),
            "jaw_to_chin": _measurement(d("right_jaw", "chin_tip"), height,
                                        method="right_landmark_euclidean",
                                        confidence=confidence),
            "ratios": {
                "confidence": _clip(confidence),
                "jaw_to_cheek_width": round(
                    d("right_jaw", "left_jaw") / d("right_cheek", "left_cheek"), 6
                ) if d("right_jaw", "left_jaw") and d("right_cheek", "left_cheek") else None,
                "forehead_to_jaw_width": round(
                    d("right_temple", "left_temple") / d("right_jaw", "left_jaw"), 6
                ) if d("right_temple", "left_temple") and d("right_jaw", "left_jaw") else None,
                "mouth_to_nose_width": round(
                    d("mouth_left", "mouth_right") / d("nose_left", "nose_right"), 6
                ) if d("mouth_left", "mouth_right") and d("nose_left", "nose_right") else None,
                "nose_to_face_width": round(
                    d("nose_left", "nose_right") / face_width, 6
                ) if d("nose_left", "nose_right") and face_width else None,
                "mouth_to_face_width": round(
                    d("mouth_left", "mouth_right") / face_width, 6
                ) if d("mouth_left", "mouth_right") and face_width else None,
                "chin_to_face_height": round(
                    d("lower_lip_bottom", "chin_tip") / face_length, 6
                ) if d("lower_lip_bottom", "chin_tip") and face_length else None,
            },
            "chin_projection": {
                "status": "unknown",
                "reason": "monocular_frontal_image_does_not_support_physical_projection",
            },
            "scale": {"width_px": width, "height_px": height, "physical_scale": "unknown"},
        }

    @staticmethod
    def _symmetry(points: dict, width: int, confidence: float) -> dict:
        center_x = points.get("nose_bridge", points.get("nose_tip", {})).get("x")
        if center_x is None:
            return {
                "status": "unknown", "regions": {},
                "overall_error_normalized": None, "confidence": 0.0,
            }
        regions = {}
        all_errors = []
        for region, pairs in PAIR_GROUPS.items():
            evidence = []
            for right, left in pairs:
                if right not in points or left not in points:
                    continue
                horizontal = abs(abs(points[right]["x"] - center_x) -
                                 abs(points[left]["x"] - center_x)) / width
                vertical = abs(points[right]["y"] - points[left]["y"]) / width
                error = math.hypot(horizontal, vertical)
                evidence.append({
                    "pair": [right, left],
                    "horizontal_error_normalized": round(horizontal, 6),
                    "vertical_error_normalized": round(vertical, 6),
                    "combined_error_normalized": round(error, 6),
                })
                all_errors.append(error)
            regions[region] = {
                "status": "measured" if evidence else "unknown",
                "pair_evidence": evidence,
                "mean_error_normalized": round(float(np.mean(
                    [item["combined_error_normalized"] for item in evidence]
                )), 6) if evidence else None,
                "confidence": _clip(confidence) if evidence else 0.0,
            }
        return {
            "status": "measured" if all_errors else "unknown",
            "midline_x_px": round(center_x, 3),
            "regions": regions,
            "overall_error_normalized": round(float(np.mean(all_errors)), 6)
            if all_errors else None,
            "confidence": _clip(confidence) if all_errors else 0.0,
        }

    @staticmethod
    def _regions(
        points: dict,
        geometry: dict,
        symmetry: dict,
        width: int,
        height: int,
        confidence: float,
    ) -> dict:
        def distance(a: str, b: str, scale: float) -> dict:
            return _measurement(
                _distance(points[a], points[b]) if a in points and b in points else None,
                scale, method="landmark_euclidean", confidence=confidence,
            )

        def angle(a: str, b: str) -> dict:
            if a not in points or b not in points:
                return {"status": "unknown", "degrees": None, "confidence": 0.0}
            value = math.degrees(math.atan2(
                points[b]["y"] - points[a]["y"],
                points[b]["x"] - points[a]["x"],
            ))
            return {
                "status": "measured", "degrees": round(value, 4),
                "confidence": _clip(confidence), "method": "image_plane_landmark_angle",
            }

        def ratio(first: dict, second: dict, method: str) -> dict:
            a, b = first.get("raw_px"), second.get("raw_px")
            return {
                "status": "measured" if a is not None and b else "unknown",
                "value": round(a / b, 6) if a is not None and b else None,
                "confidence": _clip(confidence) if a is not None and b else 0.0,
                "method": method,
            }

        def extent(names: list[str], axis: str, scale: float) -> dict:
            values = [points[name][axis] for name in names if name in points]
            value = max(values) - min(values) if len(values) == len(names) else None
            return _measurement(
                value, scale, method=f"landmark_{axis}_extent",
                confidence=confidence,
            )

        unknown_2d = {
            "status": "unknown", "value": None, "confidence": 0.0,
            "reason": "not_reliably_supported_by_selected_2d_landmarks",
        }
        right_eye_height = geometry["right_eye_height"]
        left_eye_height = geometry["left_eye_height"]
        right_brow_eye = distance("right_brow_top", "right_eye_top", height)
        left_brow_eye = distance("left_brow_top", "left_eye_top", height)
        upper_lip = geometry["upper_lip_height"]
        lower_lip = geometry["lower_lip_height"]
        jaw_symmetry = symmetry.get("regions", {}).get("jaw", {})
        chin_symmetry = symmetry.get("regions", {}).get("chin", {})
        return {
            "forehead": {
                "status": "measured",
                "confidence": _clip(confidence),
                "width": geometry["forehead_width"],
                "height": distance("forehead_center", "glabella", height),
                "height_to_face_ratio": ratio(
                    distance("forehead_center", "glabella", height),
                    geometry["face_length"], "forehead_height_divided_by_face_length",
                ),
                "slope": {
                    "status": "unknown", "degrees": None, "confidence": 0.0,
                    "reason": "physical_slope_not_reliable_from_monocular_image",
                },
                "contour": dict(unknown_2d),
                "symmetry": symmetry.get("regions", {}).get("forehead", {}),
                "visible_lines": {
                    "status": "ambiguous", "count": None, "confidence": 0.0,
                    "reason": "surface_lines_are_not_semantically_classified",
                },
            },
            "eyebrows": {
                "status": "measured",
                "confidence": _clip(confidence),
                "right": {
                    "length": distance("right_brow_outer", "right_brow_inner", width),
                    "width": extent(
                        ["right_brow_outer", "right_brow_top", "right_brow_inner"],
                        "x", width,
                    ),
                    "height": extent(
                        ["right_brow_outer", "right_brow_top", "right_brow_inner"],
                        "y", height,
                    ),
                    "arch_height": distance("right_brow_top", "right_brow_inner", height),
                    "arch_position": ratio(
                        distance("right_brow_outer", "right_brow_top", width),
                        distance("right_brow_outer", "right_brow_inner", width),
                        "outer_to_arch_distance_divided_by_brow_length",
                    ),
                    "angle": angle("right_brow_outer", "right_brow_inner"),
                    "distance_from_eye": right_brow_eye,
                    "thickness": dict(unknown_2d), "hair_density": dict(unknown_2d),
                },
                "left": {
                    "length": distance("left_brow_inner", "left_brow_outer", width),
                    "width": extent(
                        ["left_brow_inner", "left_brow_top", "left_brow_outer"],
                        "x", width,
                    ),
                    "height": extent(
                        ["left_brow_inner", "left_brow_top", "left_brow_outer"],
                        "y", height,
                    ),
                    "arch_height": distance("left_brow_top", "left_brow_inner", height),
                    "arch_position": ratio(
                        distance("left_brow_inner", "left_brow_top", width),
                        distance("left_brow_inner", "left_brow_outer", width),
                        "inner_to_arch_distance_divided_by_brow_length",
                    ),
                    "angle": angle("left_brow_inner", "left_brow_outer"),
                    "distance_from_eye": left_brow_eye,
                    "thickness": dict(unknown_2d), "hair_density": dict(unknown_2d),
                },
                "inner_spacing": distance("right_brow_inner", "left_brow_inner", width),
                "symmetry": symmetry.get("regions", {}).get("eyebrows", {}),
            },
            "eyes": {
                "status": "measured",
                "confidence": _clip(confidence),
                "right": {
                    "width": geometry["right_eye_width"], "height": right_eye_height,
                    "aspect_ratio": ratio(
                        geometry["right_eye_width"], right_eye_height,
                        "eye_width_divided_by_height",
                    ),
                    "eye_to_face_ratio": ratio(
                        geometry["right_eye_width"], geometry["face_width"],
                        "eye_width_divided_by_face_width",
                    ),
                    "corner_angle": angle("right_eye_outer", "right_eye_inner"),
                    "eyelid_visibility": dict(unknown_2d),
                    "iris_region": {
                        "status": "detected" if "right_iris_center" in points else "unknown",
                        "center_landmark": "right_iris_center",
                        "confidence": _clip(confidence)
                        if "right_iris_center" in points else 0.0,
                    },
                },
                "left": {
                    "width": geometry["left_eye_width"], "height": left_eye_height,
                    "aspect_ratio": ratio(
                        geometry["left_eye_width"], left_eye_height,
                        "eye_width_divided_by_height",
                    ),
                    "eye_to_face_ratio": ratio(
                        geometry["left_eye_width"], geometry["face_width"],
                        "eye_width_divided_by_face_width",
                    ),
                    "corner_angle": angle("left_eye_inner", "left_eye_outer"),
                    "eyelid_visibility": dict(unknown_2d),
                    "iris_region": {
                        "status": "detected" if "left_iris_center" in points else "unknown",
                        "center_landmark": "left_iris_center",
                        "confidence": _clip(confidence)
                        if "left_iris_center" in points else 0.0,
                    },
                },
                "interocular_distance": geometry["interocular_distance"],
                "interpupillary_distance": geometry["interpupillary_distance"],
                "symmetry": symmetry.get("regions", {}).get("eyes", {}),
            },
            "nose": {
                "status": "measured", "confidence": _clip(confidence),
                "width": geometry["nose_width"], "length": geometry["nose_length"],
                "nostril_width": geometry["nose_width"],
                "bridge_width": dict(unknown_2d),
                "bridge_height_or_shape": dict(unknown_2d),
                "tip_width": dict(unknown_2d),
                "tip_position": {
                    "status": "detected" if "nose_tip" in points else "unknown",
                    "coordinates": {
                        "x": points["nose_tip"]["normalized_x"],
                        "y": points["nose_tip"]["normalized_y"],
                    } if "nose_tip" in points else None,
                    "confidence": _clip(confidence)
                    if "nose_tip" in points else 0.0,
                },
                "angle": angle("nose_bridge", "nose_tip"),
                "nose_to_face_ratio": {
                    "status": "measured", "value": geometry["ratios"]["nose_to_face_width"],
                    "confidence": _clip(confidence),
                    "method": "nose_width_divided_by_face_width",
                },
                "symmetry": symmetry.get("regions", {}).get("nose", {}),
            },
            "mouth": {
                "status": "measured", "confidence": _clip(confidence),
                "width": geometry["mouth_width"], "lip_aperture": geometry["lip_aperture"],
                "upper_lip_height": upper_lip, "lower_lip_height": lower_lip,
                "lip_thickness": {
                    "upper": upper_lip, "lower": lower_lip,
                    "method": "visible_vertical_lip_height_proxy",
                    "confidence": _clip(confidence),
                },
                "upper_lower_lip_ratio": ratio(
                    upper_lip, lower_lip, "upper_lip_height_divided_by_lower",
                ),
                "mouth_to_face_ratio": {
                    "status": "measured", "value": geometry["ratios"]["mouth_to_face_width"],
                    "confidence": _clip(confidence),
                    "method": "mouth_width_divided_by_face_width",
                },
                "corner_angle": angle("mouth_left", "mouth_right"),
                "philtrum_length": geometry["philtrum_length"],
                "symmetry": symmetry.get("regions", {}).get("mouth", {}),
            },
            "jaw": {
                "status": "measured", "confidence": _clip(confidence),
                "width": geometry["jaw_width"], "right_to_chin": geometry["jaw_to_chin"],
                "angle": {
                    "status": "unknown", "degrees": None, "confidence": 0.0,
                    "reason": "gonial_angle_requires_more_reliable_pose_normalization",
                },
                "curvature": dict(unknown_2d), "symmetry": jaw_symmetry,
            },
            "chin": {
                "status": "measured", "confidence": _clip(confidence),
                "width": geometry["chin_width"], "projection": geometry["chin_projection"],
                "height": geometry["chin_height"],
                "chin_to_face_ratio": {
                    "status": "measured",
                    "value": geometry["ratios"]["chin_to_face_height"],
                    "confidence": _clip(confidence),
                    "method": "chin_height_divided_by_face_length",
                },
                "symmetry": chin_symmetry,
            },
        }

    @staticmethod
    def _zones(points: dict, confidence: float) -> dict:
        definitions = {
            "upper": ["forehead_center", "right_temple", "right_brow_outer",
                      "left_brow_outer", "left_temple"],
            "middle": ["right_brow_outer", "face_left", "nose_tip",
                       "face_right", "left_brow_outer"],
            "lower": ["nose_tip", "face_left", "chin_tip", "face_right"],
            "forehead": ["forehead_center", "right_temple", "right_brow_outer",
                         "left_brow_outer", "left_temple"],
            "eyebrow_eye": ["right_brow_outer", "right_eye_outer",
                            "right_eye_inner", "left_eye_inner", "left_eye_outer",
                            "left_brow_outer"],
            "nose": ["nose_bridge", "nose_left", "nose_tip", "nose_right"],
            "right_cheek": ["right_eye_outer", "face_left", "right_jaw", "nose_tip"],
            "left_cheek": ["nose_tip", "left_jaw", "face_right", "left_eye_outer"],
            "mouth": ["nose_left", "mouth_left", "lower_lip_bottom",
                      "mouth_right", "nose_right"],
            "chin": ["mouth_left", "right_chin", "chin_tip",
                     "left_chin", "mouth_right"],
            "right_face": ["forehead_center", "right_temple", "face_left",
                           "right_jaw", "chin_tip", "nose_tip", "nose_bridge"],
            "left_face": ["forehead_center", "nose_bridge", "nose_tip",
                          "chin_tip", "left_jaw", "face_right", "left_temple"],
        }
        zones = {}
        for name, names in definitions.items():
            polygon = [
                {"x": points[item]["normalized_x"], "y": points[item]["normalized_y"]}
                for item in names if item in points
            ]
            zones[name] = {
                "status": "derived" if len(polygon) >= 3 else "unknown",
                "polygon": polygon if len(polygon) >= 3 else [],
                "source_landmarks": names,
                "confidence": _clip(confidence) if len(polygon) >= 3 else 0.0,
            }
        return {
            "status": "derived",
            "confidence": _clip(confidence),
            "coordinate_space": "normalized_0_1",
            "derivation": "named_landmark_polygons",
            "zones": zones,
        }

    @staticmethod
    def _surface(rgb: np.ndarray, bbox: dict, confidence: float) -> dict:
        height, width = rgb.shape[:2]
        x0 = max(0, int(bbox["normalized_x"] * width))
        y0 = max(0, int(bbox["normalized_y"] * height))
        x1 = min(width, int((bbox["normalized_x"] + bbox["normalized_width"]) * width))
        y1 = min(height, int((bbox["normalized_y"] + bbox["normalized_height"]) * height))
        roi = cv2.cvtColor(rgb[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY)
        if not roi.size:
            return {
                "status": "unknown", "reason": "empty_face_roi",
                "ambiguous_points": [], "confidence": 0.0,
            }
        laplacian = cv2.Laplacian(roi, cv2.CV_64F)
        edges = cv2.Canny(roi, 60, 140)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 24,
                                minLineLength=max(8, roi.shape[1] // 20), maxLineGap=5)
        candidates = []
        if lines is not None:
            for line in lines[:64]:
                ax, ay, bx, by = map(int, line[0])
                candidates.append({
                    "coordinates": [
                        {"x": round((x0 + ax) / width, 6), "y": round((y0 + ay) / height, 6)},
                        {"x": round((x0 + bx) / width, 6), "y": round((y0 + by) / height, 6)},
                    ],
                    "semantic_identity": "ambiguous_surface_line",
                    "method": "canny_hough_pixel_response",
                })
        return {
            "status": "measured",
            "confidence": _clip(confidence),
            "roi": {"x": round(x0 / width, 6), "y": round(y0 / height, 6),
                    "width": round((x1 - x0) / width, 6),
                    "height": round((y1 - y0) / height, 6)},
            "texture": {
                "laplacian_absolute_mean": round(float(np.mean(np.abs(laplacian))), 6),
                "grayscale_stddev": round(float(roi.std()), 6),
                "label": "pixel_texture_proxy_not_skin_condition",
                "confidence": _clip(confidence),
            },
            "line_density": {
                "edge_pixel_ratio": round(float((edges > 0).mean()), 6),
                "candidate_count_per_megapixel": round(
                    len(candidates) / max(roi.size / 1_000_000, .000001), 6
                ),
                "confidence": _clip(confidence),
            },
            "ambiguous_coordinates": candidates,
            "fine_lines_or_creases": {
                "status": "ambiguous" if candidates else "not_detected",
                "candidates": candidates,
                "confidence": 0.0,
                "reason": "pixel_responses_have_no_semantic_identity",
            },
            "pigmentation_regions": {
                "status": "unknown", "items": [], "confidence": 0.0,
                "reason": "not_reliably_distinguishable_from_lighting",
            },
            "scars": {
                "status": "unknown", "items": [], "confidence": 0.0,
                "reason": "not_reliably_distinguishable_from_image_only",
            },
            "visible_marks_or_moles": {
                "status": "unknown", "items": [], "confidence": 0.0,
                "reason": "no_validated_semantic_detector_configured",
            },
        }

    @staticmethod
    def _face_shape(geometry: dict, measurement_confidence: float) -> dict:
        aspect = geometry["aspect_ratio"]["value"]
        jaw_cheek = geometry["ratios"]["jaw_to_cheek_width"]
        forehead_jaw = geometry["ratios"]["forehead_to_jaw_width"]
        if None in (aspect, jaw_cheek, forehead_jaw):
            return {"label": "unknown", "confidence": 0.0, "status": "unknown",
                    "method": "geometry_thresholds"}
        forehead_cheek = forehead_jaw * jaw_cheek
        prototypes = {
            "oval": (1.35, .90, .82),
            "round": (1.10, .95, .90),
            "square": (1.15, .98, .98),
            "rectangular": (1.52, .98, .95),
            "oblong": (1.68, .90, .86),
            "heart": (1.30, 1.02, .76),
            "diamond": (1.38, .78, .74),
            "triangle": (1.25, .76, 1.00),
        }
        scores = {}
        for label, (target_aspect, target_forehead, target_jaw) in prototypes.items():
            distance = math.sqrt(
                ((aspect - target_aspect) / .5) ** 2
                + ((forehead_cheek - target_forehead) / .35) ** 2
                + ((jaw_cheek - target_jaw) / .35) ** 2
            )
            scores[label] = max(0.0, 1.0 - distance / math.sqrt(3))
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1]
        confidence = min(_clip(.45 + margin), _clip(measurement_confidence))
        ambiguous = margin < .08 or ranked[0][1] < .25
        return {
            "label": "ambiguous" if ambiguous else ranked[0][0],
            "candidate": ranked[0][0],
            "confidence": confidence if not ambiguous else _clip(confidence * .65),
            "status": "ambiguous" if ambiguous else "classified",
            "method": "raw_geometry_threshold_proximity",
            "evidence": {
                "aspect_ratio": aspect, "jaw_to_cheek_width": jaw_cheek,
                "forehead_to_jaw_width": forehead_jaw,
                "forehead_to_cheek_width": round(forehead_cheek, 6),
                "candidate_scores": {key: round(value, 6) for key, value in scores.items()},
                "top_margin": round(margin, 6),
            },
        }

    @staticmethod
    def _confidence(
        primary: FaceCandidate, quality: dict, geometry: dict, symmetry: dict, shape: dict
    ) -> dict:
        groups = {
            "detection": _clip(primary.confidence),
            "quality": quality["overall_score"],
            "landmarks": _clip(primary.confidence),
            "geometry": geometry.get("confidence", 0.0),
            "symmetry": symmetry.get("confidence", 0.0),
            "face_shape": shape["confidence"],
            "surface": min(
                _clip(quality["lighting_score"] * quality["blur_score"]),
                _clip(primary.confidence),
            ),
        }
        return {
            "overall": round(min(
                float(np.mean(list(groups.values()))),
                _clip(primary.confidence),
                quality["overall_score"],
            ), 4),
            "groups": groups,
            "methods": ["detector_confidence", "capture_quality", "landmark_completeness"],
            "disagreement": {
                "preserved": True,
                "face_shape_top_margin": shape.get("evidence", {}).get("top_margin"),
                "detector_mesh_bbox_iou": (
                    quality.get("raw_evidence", {}).get("detector_mesh_bbox_iou")
                ),
            },
        }

    @staticmethod
    def _method_agreement(primary: FaceCandidate) -> dict:
        detector_bbox = primary.evidence.get("independent_detection_bbox")
        if not isinstance(detector_bbox, (list, tuple)) or len(detector_bbox) != 4:
            return {
                "status": "not_evaluated",
                "methods": ["landmark_mesh"],
                "reason": "independent_detector_bbox_unavailable",
            }
        overlap = _bbox_iou(primary.bbox, tuple(map(float, detector_bbox)))
        return {
            "status": "consistent" if overlap >= .35 else "ambiguous",
            "methods": ["independent_face_detector", "landmark_mesh"],
            "bbox_iou": round(overlap, 6),
            "threshold": .35,
            "raw_bboxes": {
                "landmark_mesh": list(primary.bbox),
                "independent_detector": list(detector_bbox),
            },
        }

    @staticmethod
    def _empty_quality(code: str) -> dict:
        return {
            "gate": "failed", "usable": False, "overall_score": 0.0,
            "resolution_score": 0.0, "blur_score": 0.0, "lighting_score": 0.0,
            "visibility_score": 0.0, "occlusion_score": 0.0,
            "exposure_score": 0.0, "pose_score": 0.0, "raw_evidence": {},
            "issues": [_issue(code.split(" ", 1)[0], "error", code)],
        }

    def _empty_result(
        self, metadata: dict, quality: dict, *, batch: DetectionBatch | None = None
    ) -> dict:
        unknown = {
            "status": "unknown", "reason": "quality_gate_failed",
            "confidence": 0.0,
        }
        result = {
            "schema_version": SCHEMA_VERSION, "metadata": metadata, "quality": quality,
            "face_detection": {
                "face_count": batch.face_count if batch else 0,
                "primary_selection_status": "not_selected", "bbox": None,
                "center": None, "pose": None, "confidence": 0.0,
                "selection_policy": "single_or_dominant_area_confidence",
            },
            "landmarks": {"named": {}, "groups": GROUPS, "full_mesh_compact": [],
                          "full_mesh_fields": []},
            "face_geometry": dict(unknown), "symmetry": dict(unknown),
            "forehead": dict(unknown), "eyebrows": dict(unknown), "eyes": dict(unknown),
            "nose": dict(unknown), "mouth": dict(unknown), "jaw": dict(unknown),
            "chin": dict(unknown), "face_shape": {
                "label": "unknown", "confidence": 0.0, **unknown
            },
            "skin_surface_features": dict(unknown),
            "traditional_zones": {
                "status": "unknown", "confidence": 0.0,
                "coordinate_space": "normalized_0_1", "zones": {}
            },
            "confidence": {"overall": 0.0, "groups": {}, "methods": [], "disagreement": {}},
            "validation_status": {
                "status": "unusable_input", "schema_version": SCHEMA_VERSION,
                "warnings": [item["code"] for item in quality["issues"]],
            },
            "annotated_image_reference": None,
        }
        schema_errors = validate_result(result)
        if schema_errors:
            result["validation_status"]["status"] = "invalid_schema"
            result["validation_status"]["errors"] = schema_errors
        return result

    @staticmethod
    def _annotate_from_result(rgb: np.ndarray, result: dict) -> np.ndarray:
        """Draw only coordinates serialized in the public result."""
        output = cv2.cvtColor(rgb.copy(), cv2.COLOR_RGB2BGR)
        height, width = output.shape[:2]
        bbox = result.get("face_detection", {}).get("bbox")
        if bbox:
            p1 = (round(bbox["normalized_x"] * width), round(bbox["normalized_y"] * height))
            p2 = (round((bbox["normalized_x"] + bbox["normalized_width"]) * width),
                  round((bbox["normalized_y"] + bbox["normalized_height"]) * height))
            cv2.rectangle(output, p1, p2, (90, 220, 90), 2)
        named = result.get("landmarks", {}).get("named", {})
        for point in named.values():
            cv2.circle(output, (round(point["x"]), round(point["y"])), 2, (0, 220, 255), -1)
        group_colors = {
            "boundary": (90, 220, 90),
            "eyebrows": (255, 120, 40),
            "eyes": (255, 220, 30),
            "nose": (60, 180, 255),
            "mouth": (80, 80, 255),
            "jaw_chin": (180, 100, 255),
        }
        groups = result.get("landmarks", {}).get("groups", {})
        for group_name, source_names in groups.items():
            coordinates = [
                [round(named[name]["x"]), round(named[name]["y"])]
                for name in source_names if name in named
            ]
            if len(coordinates) >= 2:
                cv2.polylines(
                    output, [np.int32(coordinates)],
                    group_name in {"boundary", "mouth"},
                    group_colors.get(group_name, (200, 200, 200)), 1,
                )
        thirds = result.get("face_geometry", {}).get("facial_thirds", [])
        if bbox and thirds:
            x1 = round(bbox["normalized_x"] * width)
            x2 = round((bbox["normalized_x"] + bbox["normalized_width"]) * width)
            for name in ("nose_bridge", "nose_tip"):
                if name in named:
                    y = round(named[name]["y"])
                    cv2.line(output, (x1, y), (x2, y), (255, 180, 0), 1)
        for zone in result.get("traditional_zones", {}).get("zones", {}).values():
            polygon = zone.get("polygon", [])
            if len(polygon) >= 3:
                pts = np.int32([[round(p["x"] * width), round(p["y"] * height)]
                                for p in polygon])
                cv2.polylines(output, [pts], True, (210, 80, 210), 1)
        return output
