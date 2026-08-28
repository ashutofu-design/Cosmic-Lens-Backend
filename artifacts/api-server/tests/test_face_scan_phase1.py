"""Synthetic tests for isolated, measurement-only Face Scan Phase 1."""
from __future__ import annotations

import io
import json

import numpy as np
import pytest
from PIL import Image, ImageFilter

from vedic.face_scan.api import create_face_scan_blueprint
from vedic.face_scan.backend import DetectionBatch, FaceCandidate
from vedic.face_scan.engine import FaceScanEngine, NAMED_INDICES
from vedic.face_scan.ground_truth import (
    evaluate, load_annotation, make_example_annotation, validate_annotation,
)
from vedic.face_scan.schema import validate_result


def image_bytes(kind="good", size=(720, 900)):
    rng = np.random.default_rng(42)
    pixels = np.full((size[1], size[0], 3), 145, dtype=np.int16)
    pixels += rng.integers(-35, 36, pixels.shape, dtype=np.int16)
    image = Image.fromarray(np.uint8(np.clip(pixels, 0, 255)))
    if kind == "low_light":
        image = Image.fromarray(np.uint8(np.asarray(image) * .15))
    elif kind == "blur":
        image = image.filter(ImageFilter.GaussianBlur(18))
    output = io.BytesIO()
    image.save(output, "JPEG", quality=92)
    return output.getvalue()


def mesh():
    points = [(0.5, 0.5, 0.0) for _ in range(478)]
    values = {
        "forehead_center": (.50, .12), "face_left": (.20, .52),
        "face_right": (.80, .52), "chin_tip": (.50, .90),
        "nose_bridge": (.50, .38), "nose_tip": (.50, .61),
        "nose_left": (.43, .60), "nose_right": (.57, .60),
        "mouth_left": (.39, .72), "mouth_right": (.61, .72),
        "upper_lip": (.50, .70), "lower_lip": (.50, .75),
        "right_eye_outer": (.29, .43), "right_eye_inner": (.44, .43),
        "right_eye_top": (.365, .405), "right_eye_bottom": (.365, .455),
        "left_eye_inner": (.56, .43), "left_eye_outer": (.71, .43),
        "left_eye_top": (.635, .405), "left_eye_bottom": (.635, .455),
        "right_iris_center": (.365, .43), "left_iris_center": (.635, .43),
        "right_brow_outer": (.28, .35), "right_brow_inner": (.45, .36),
        "right_brow_top": (.365, .33), "left_brow_inner": (.55, .36),
        "left_brow_outer": (.72, .35), "left_brow_top": (.635, .33),
        "right_jaw": (.28, .75), "left_jaw": (.72, .75),
        "right_chin": (.40, .86), "left_chin": (.60, .86),
        "right_temple": (.24, .30), "left_temple": (.76, .30),
        "right_cheek": (.20, .52), "left_cheek": (.80, .52),
    }
    for name, (x, y) in values.items():
        points[NAMED_INDICES[name]] = (x, y, 0.0)
    return points


def candidate(*, confidence=.93, bbox=(.18, .08, .64, .84), pose=None,
              evidence=None, points=None):
    return FaceCandidate(
        points or mesh(), confidence, bbox, pose or {
            "yaw_degrees": 0, "pitch_degrees": 0, "roll_degrees": 0,
        }, evidence=evidence or {},
    )


class FakeBackend:
    def __init__(self, candidates=None, face_count=None):
        self.candidates = [candidate()] if candidates is None else candidates
        self.face_count = len(self.candidates) if face_count is None else face_count

    def detect(self, image_bytes_value, rgb):
        return DetectionBatch(self.candidates, self.face_count, "synthetic")


def scan(kind="good", backend=None):
    return FaceScanEngine(backend or FakeBackend()).scan_with_artifacts(
        image_bytes(kind)
    )[0]


def test_measurement_only_schema_and_named_coordinates():
    result = scan()
    required = {
        "metadata", "quality", "face_detection", "landmarks", "face_geometry",
        "symmetry", "forehead", "eyebrows", "eyes", "nose", "mouth", "jaw",
        "chin", "face_shape", "skin_surface_features", "traditional_zones",
        "confidence", "validation_status", "annotated_image_reference",
    }
    assert result["schema_version"] == "1.0"
    assert validate_result(result) == []
    assert required <= set(result)
    assert result["quality"]["gate"] == "passed"
    point = result["landmarks"]["named"]["nose_tip"]
    assert {"x", "y", "normalized_x", "normalized_y", "confidence", "status"} <= set(point)
    assert len(result["landmarks"]["full_mesh_compact"]) == 478
    assert result["face_geometry"]["chin_projection"]["status"] == "unknown"


@pytest.mark.parametrize(("kind", "code"), [
    ("low_light", "poor_lighting"), ("blur", "excessive_blur"),
])
def test_quality_gate_stops_measurements(kind, code):
    result = scan(kind)
    assert result["quality"]["usable"] is False
    assert code in {issue["code"] for issue in result["quality"]["issues"]}
    assert result["face_geometry"]["status"] == "unknown"
    assert result["annotated_image_reference"] is None


@pytest.mark.parametrize(("pose_key", "value", "code"), [
    ("yaw_degrees", 35, "extreme_angle"),
    ("pitch_degrees", -34, "extreme_angle"),
    ("roll_degrees", 28, "extreme_angle"),
])
def test_rotation_quality_codes(pose_key, value, code):
    pose = {"yaw_degrees": 0, "pitch_degrees": 0, "roll_degrees": 0}
    pose[pose_key] = value
    result = scan(backend=FakeBackend([candidate(pose=pose)]))
    assert code in {issue["code"] for issue in result["quality"]["issues"]}


@pytest.mark.parametrize("yaw", [-15, 15])
def test_slight_left_and_right_rotation_remain_measurable(yaw):
    result = scan(backend=FakeBackend([
        candidate(pose={
            "yaw_degrees": yaw, "pitch_degrees": 0, "roll_degrees": 0,
        })
    ]))
    assert result["quality"]["usable"] is True
    assert result["face_detection"]["pose"]["yaw_degrees"] == yaw


def test_crop_distance_and_observable_obstruction_flags():
    evidence = {
        "glasses_observed": True, "hair_obstruction_observed": True,
        "mask_observed": True,
        "eyes_visible": True, "nose_visible": True, "mouth_visible": True,
        "chin_visible": True,
    }
    result = scan(backend=FakeBackend([
        candidate(bbox=(0, .01, .18, .20), evidence=evidence)
    ]))
    codes = {issue["code"] for issue in result["quality"]["issues"]}
    assert {"face_cropped", "face_too_small", "glasses_obstruction",
            "mask_obstruction", "hair_obstruction"} <= codes


def test_limited_resolution_is_scored_and_flagged():
    result = FaceScanEngine(FakeBackend()).scan_with_artifacts(
        image_bytes(size=(400, 400))
    )[0]
    assert 0 <= result["quality"]["resolution_score"] <= 1
    assert "limited_resolution" in {issue["code"] for issue in result["quality"]["issues"]}


def test_no_face_and_incomplete_landmarks_fail_closed():
    assert scan(backend=FakeBackend([], 0))["face_detection"]["face_count"] == 0
    incomplete = candidate(points=mesh()[:100])
    result = scan(backend=FakeBackend([incomplete]))
    assert "incomplete_landmarks" in {i["code"] for i in result["quality"]["issues"]}
    assert result["quality"]["usable"] is False


def test_multiple_faces_ambiguous_without_dominance():
    result = scan(backend=FakeBackend([
        candidate(bbox=(.1, .1, .35, .5)),
        candidate(bbox=(.52, .1, .35, .5)),
    ]))
    assert result["face_detection"]["primary_selection_status"] == "not_selected"
    assert "multiple_faces_ambiguous" in {i["code"] for i in result["quality"]["issues"]}


def test_multiple_faces_dominant_selection_uses_evidence():
    result = scan(backend=FakeBackend([
        candidate(bbox=(.15, .08, .62, .82), confidence=.94),
        candidate(bbox=(.78, .12, .15, .20), confidence=.89),
    ]))
    assert result["quality"]["usable"] is True
    assert result["face_detection"]["face_count"] == 2
    assert "multiple_faces_primary_selected" in {
        issue["code"] for issue in result["quality"]["issues"]
    }


def test_independent_detector_disagreement_fails_closed():
    result = scan(backend=FakeBackend([
        candidate(evidence={"independent_detection_bbox": (.82, .82, .1, .1)})
    ]))
    assert result["quality"]["usable"] is False
    assert "detector_disagreement" in {
        issue["code"] for issue in result["quality"]["issues"]
    }


def test_numeric_symmetry_geometry_shape_and_surface_contracts():
    result = scan()
    assert "interpretation" not in result["symmetry"]
    assert result["symmetry"]["regions"]["eyes"]["mean_error_normalized"] >= 0
    assert result["face_geometry"]["face_width"]["raw_px"] > 0
    assert result["face_geometry"]["face_width"]["normalized"] > 0
    assert result["face_geometry"]["face_width"]["confidence"] > 0
    assert result["eyes"]["right"]["height"]["confidence"] > 0
    assert result["mouth"]["philtrum_length"]["confidence"] > 0
    assert result["forehead"]["slope"]["status"] == "unknown"
    assert result["face_shape"]["status"] in {"classified", "ambiguous"}
    assert result["face_shape"]["candidate"] in {
        "oval", "round", "square", "rectangular", "oblong", "heart",
        "diamond", "triangle",
    }
    assert {
        "forehead", "eyebrow_eye", "nose", "right_cheek", "left_cheek",
        "mouth", "chin", "right_face", "left_face",
    } <= set(result["traditional_zones"]["zones"])
    surface = result["skin_surface_features"]
    assert "pixel_texture_proxy" in surface["texture"]["label"]
    assert all(item["semantic_identity"] == "ambiguous_surface_line"
               for item in surface["ambiguous_coordinates"])


def test_forbidden_inference_keys_and_words_absent():
    payload = json.dumps(scan(), sort_keys=True).lower()
    for forbidden in (
        "personality", "first_impression", "ethnicity", "attractiveness",
        "diagnosis", "disease", "samudrika", "mole_phala", "percentile",
        "billing", "fortune", "destiny",
    ):
        assert forbidden not in payload


def test_overlay_is_exclusively_driven_by_result_coordinates():
    rgb = np.zeros((100, 100, 3), np.uint8)
    result = scan()
    result["face_detection"]["bbox"] = None
    result["landmarks"]["named"] = {
        "only": {"x": 20, "y": 30, "normalized_x": .2, "normalized_y": .3}
    }
    result["face_geometry"]["facial_thirds"] = []
    result["traditional_zones"]["zones"] = {}
    overlay = FaceScanEngine._annotate_from_result(rgb, result)
    assert np.any(overlay[28:33, 18:23] != 0)
    assert not np.any(overlay[75:90, 75:90] != 0)


def test_api_multipart_and_private_annotation_endpoint():
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(create_face_scan_blueprint(
        engine=FaceScanEngine(FakeBackend())
    ))
    client = app.test_client()
    response = client.post(
        "/api/face-scan",
        data={"image": (io.BytesIO(image_bytes()), "face.jpg"), "mirror": "false"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    body = response.get_json()
    annotation = client.get(body["annotated_image_reference"])
    assert annotation.status_code == 200
    assert annotation.content_type == "image/png"
    assert "private" in annotation.headers["Cache-Control"]
    assert client.post("/api/face-scan", data={}).status_code == 400
    unusable_app = Flask(__name__)
    unusable_app.register_blueprint(create_face_scan_blueprint(
        engine=FaceScanEngine(FakeBackend([]))
    ))
    unusable = unusable_app.test_client().post(
        "/api/face-scan",
        data={"image": (io.BytesIO(image_bytes()), "face.jpg")},
        content_type="multipart/form-data",
    )
    assert unusable.status_code == 422


def test_ground_truth_strict_validation_and_evaluation():
    annotation = make_example_annotation()
    assert validate_annotation(annotation) == []
    assert load_annotation(annotation) == annotation
    result = scan()
    metrics = evaluate(annotation, result)
    assert metrics["landmark_normalized_error"]["matched"] == 1
    assert 0 <= metrics["bbox_iou"] <= 1
    assert "middle" in metrics["zone_iou"]
    assert "nose" in metrics["feature_region_iou"]
    assert "face_geometry.aspect_ratio" in metrics["measurement_errors"]
    assert "brier_score" in metrics["confidence_calibration"]
    invalid = {**annotation, "coordinate_space": "pixels"}
    assert validate_annotation(invalid)
    malformed = {**annotation, "landmarks": ["not-an-object"]}
    assert validate_annotation(malformed)
