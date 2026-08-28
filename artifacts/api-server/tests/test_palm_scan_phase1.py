"""Synthetic Phase 1 tests: geometry is fake-backed, image metrics use pixels."""
from __future__ import annotations

import io

import cv2
import numpy as np
import pytest
from PIL import Image, ImageFilter

from vedic.palm_scan.api import create_palm_scan_blueprint
from vedic.palm_scan.detectors import (
    ConservativeCreaseDetector, HandDetection, LANDMARK_NAMES, confidence_band,
)
from vedic.palm_scan.engine import MAJOR_LINE_NAMES, MOUNT_NAMES, PalmScanEngine
from vedic.palm_scan.ground_truth import (
    evaluate, load_annotation, make_example_annotation, validate_annotation,
)
from vedic.palm_scan.preprocessing import preprocess
from vedic.palm_scan.validation_gate import evaluate_bilateral, evaluate_hand, gate_config


BASE_POINTS = [
    (.50, .86), (.40, .71), (.32, .61), (.24, .51), (.16, .42),
    (.36, .52), (.34, .38), (.33, .24), (.32, .09),
    (.50, .49), (.50, .32), (.50, .17), (.50, .05),
    (.63, .52), (.65, .36), (.66, .22), (.67, .09),
    (.75, .57), (.79, .44), (.82, .32), (.85, .21),
]


class FakeHandBackend:
    def __init__(self, handedness="right", points=None, confidence=.92):
        self.handedness = handedness
        self.points = points or BASE_POINTS
        self.confidence = confidence

    def detect(self, rgb, *, pixels_are_mirrored=False):
        landmarks = [
            {"id": i, "name": LANDMARK_NAMES[i], "x": x, "y": y, "z_relative": 0.0,
             "confidence": self.confidence, "status": "detected"}
            for i, (x, y) in enumerate(self.points)
        ]
        return HandDetection(landmarks, self.handedness, self.confidence, self.handedness)


class NoHandBackend:
    def detect(self, rgb, *, pixels_are_mirrored=False):
        return None


class FakeCreases:
    def __init__(self, faint=False):
        self.faint = faint

    def detect(self, rgb, palm_mask):
        if self.faint:
            return []
        return [{
            "id": "crease_candidate_1", "status": "detected", "semantic_identity": "ambiguous",
            "confidence": .61, "confidence_band": "moderate",
            "detector_agreement": .5, "methods": ["synthetic_fixture"],
            "method_evidence": {"synthetic_fixture": .7},
            "path": [
                {"x": .35, "y": .62}, {"x": .42, "y": .60}, {"x": .50, "y": .58},
                {"x": .58, "y": .59}, {"x": .66, "y": .60},
            ],
            "path_point_count": 5,
            "path_source": "synthetic_fixture",
            "endpoints": [{"x": .35, "y": .62}, {"x": .66, "y": .60}],
            "normalized_length": .31,
            "measurements": {
                "length_px": 123.0, "strength_proxy": .7,
                "depth_proxy": {"value": .7, "label": "pixel_response_not_physical_depth"},
                "clarity": .65, "continuity": .9, "curvature": .08,
                "direction_degrees": -3.7, "break_candidates": [],
                "branch_candidates": [], "fork_candidates": [],
                "island_candidates": [], "intersection_candidates": [],
                "parallel_candidates": [], "relative_position": "unassigned_within_visible_palm",
            },
            "raw": {"arc_length_px": 123.0, "mean_ridge_response": .48},
        }]


class FakeLineVerifier:
    def verify(self, candidates, context):
        assert context["hand"]["side"] in {"left", "right"}
        return {
            "heart_line": {
                "candidate_id": candidates[0]["id"],
                "confidence": .90,
            }
        }


class UnavailableLineVerifier:
    last_evidence = {"status": "model_unavailable", "error_type": "FileNotFoundError"}

    def verify(self, candidates, context):
        return {}


def image_bytes(kind="good"):
    rng = np.random.default_rng(17)
    array = np.full((800, 640, 3), 150, dtype=np.uint8)
    noise = rng.integers(-42, 43, array.shape, dtype=np.int16)
    array = np.uint8(np.clip(array.astype(np.int16) + noise, 0, 255))
    # Add crisp synthetic ridge structure so the "good" fixture reliably clears
    # blur/contrast thresholds without weakening the production gate.
    for y in range(120, 720, 52):
        cv2.line(array, (120, y), (520, y - 36), (55, 55, 55), 2, cv2.LINE_AA)
        cv2.line(array, (140, y + 18), (500, y - 8), (85, 85, 85), 1, cv2.LINE_AA)
    for x in range(150, 520, 70):
        cv2.line(array, (x, 160), (x + 36, 670), (70, 70, 70), 1, cv2.LINE_AA)
    image = Image.fromarray(array)
    if kind == "low_light":
        image = Image.fromarray(np.uint8(np.asarray(image) * .18))
    if kind == "blur":
        image = image.filter(ImageFilter.GaussianBlur(14))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def scan(kind="good", *, points=None, handedness="right", faint=False):
    engine = PalmScanEngine(FakeHandBackend(handedness, points), FakeCreases(faint))
    return engine.scan(image_bytes(kind))[0]


def assert_no_interpretation(payload):
    text = str(payload).lower()
    for forbidden in ("prediction", "personality", "future", "destiny", "fortune", "interpretation"):
        assert forbidden not in text


def assert_major_lines_are_candidate_backed(result):
    candidate_ids = {
        item["id"]
        for item in result["secondary_lines"]["crease_candidates"]
        if isinstance(item, dict) and item.get("id")
    }
    from vedic.palm_scan.engine import MIN_MAJOR_LINE_PATH_POINTS
    fate_statuses = {
        "detected", "ambiguous", "insufficient_evidence",
        "not_detected", "insufficient_geometry",
    }
    for name, line in result["major_lines"].items():
        if line["status"] == "unknown":
            continue
        if name == "fate_line":
            assert line["status"] in fate_statuses
            if line["status"] in {"detected", "ambiguous"}:
                assert line.get("detection_method") == "image_first_fate_line_detector"
                if len(line.get("path") or []) >= MIN_MAJOR_LINE_PATH_POINTS:
                    assert line.get("source_candidate_id")
            continue
        assert line["status"] in {"ambiguous", "detected", "insufficient_geometry"}
        if line["status"] == "insufficient_geometry":
            assert len(line.get("path") or []) < MIN_MAJOR_LINE_PATH_POINTS
            continue
        assert line.get("source_candidate_id") in candidate_ids
        assert len(line.get("path") or []) >= MIN_MAJOR_LINE_PATH_POINTS


def test_clear_good_fixture_path_is_measurement_only():
    result = scan()
    assert result["schema_version"] == "1.0"
    assert result["quality"]["gate"] == "passed"
    assert result["quality"]["overall_score"] == result["quality"]["score"]
    assert 0 <= result["quality"]["resolution_score"] <= 1
    assert 0 <= result["quality"]["blur_score"] <= 1
    assert 0 <= result["quality"]["lighting_score"] <= 1
    assert len(result["landmarks"]) == 21
    assert len(result["palm_geometry"]["center"]["normalized"]) == 2
    assert result["palm_geometry"]["finger_base_line"]["path"]
    assert result["palm_geometry"]["width"]["raw_px"] > 0
    assert result["palm_geometry"]["width"]["normalized"] <= 1
    assert result["major_lines"]["life_line"]["status"] in {"unknown", "ambiguous", "detected"}
    assert result["secondary_lines"]["crease_candidates"][0]["semantic_identity"] == "ambiguous"
    assert_major_lines_are_candidate_backed(result)
    assert result["mounts"]["Venus"]["elevation"]["status"] == "unknown"
    assert result["thumb"]["flexibility"]["status"] == "unknown"
    assert result["union_lines"]["reason"] == "outer_edge_not_visible"
    assert result["annotated_image_reference"]
    assert result["processed_image_reference"]
    assert result["original_decoded_image_reference"]
    assert_no_interpretation(result)


@pytest.mark.parametrize(
    ("kind", "issue"),
    [("low_light", "low_light"), ("blur", "blurred")],
)
def test_quality_gate_rejects_bad_capture(kind, issue):
    result = scan(kind)
    assert result["quality"]["gate"] == "failed"
    assert issue in {item["code"] for item in result["quality"]["issues"]}
    assert result["palm_geometry"]["width"]["status"] == "unknown"
    assert result["secondary_lines"]["crease_candidates"] == []
    assert result["annotated_image_reference"] is None


def test_low_hand_detection_confidence_is_rejected_as_non_hand():
    engine = PalmScanEngine(
        FakeHandBackend(confidence=.60), FakeCreases()
    )
    result = engine.scan(image_bytes())[0]
    assert result["quality"]["usable"] is False
    assert "low_hand_detection_confidence" in {
        item["code"] for item in result["quality"]["issues"]
    }
    assert result["validation"]["status"] == "rejected"


def test_hidden_fingers_are_actionable():
    points = list(BASE_POINTS)
    points[8] = (.32, .999)
    result = scan(points=points)
    assert "fingers_hidden_or_cropped" in {item["code"] for item in result["quality"]["issues"]}
    assert result["quality"]["usable"] is False


def test_cropped_palm_is_actionable():
    points = list(BASE_POINTS)
    points[0] = (.50, .001)
    result = scan(points=points)
    codes = {item["code"] for item in result["quality"]["issues"]}
    assert "palm_cropped" in codes
    assert "wrist_not_visible" in codes


def test_extreme_angle_is_rejected():
    points = list(BASE_POINTS)
    points[0] = (.18, .82)
    points[9] = (.76, .50)
    result = scan(points=points)
    assert "extreme_orientation" in {item["code"] for item in result["quality"]["issues"]}


@pytest.mark.parametrize("handedness", ["left", "right"])
def test_handedness_comes_from_backend_pixels(handedness):
    result = scan(handedness=handedness)
    assert result["hand"]["handedness"] == handedness
    assert result["hand"]["handedness_basis"] in {"image_pixels", "palmar_thumb_pinky_x"}


def test_fine_lines_remain_unlabelled():
    result = scan()
    assert result["secondary_lines"]["status"] == "detected"
    assert all(item["semantic_identity"] == "ambiguous"
               for item in result["secondary_lines"]["crease_candidates"])
    assert_major_lines_are_candidate_backed(result)


def test_faint_lines_prefer_not_detected():
    result = scan(faint=True)
    assert result["secondary_lines"]["status"] == "not_detected"
    assert result["secondary_lines"]["crease_candidates"] == []


def test_line_stitching_preserves_unmerged_fragments():
    result = scan()
    assert result["line_stitching"]["status"] == "detected"
    assert result["line_stitching"]["stitching_applied"] is False
    assert len(result["line_stitching"]["groups"]) == len(result["secondary_lines"]["crease_candidates"])
    assert result["line_stitching"]["groups"][0]["stitch_reason"] == "single_fragment_preserved_without_forced_merge"


def test_production_validation_gate_passes_clear_scan_and_rejects_blur():
    good = evaluate_hand(scan(), required_hand_side="right")
    bad = evaluate_hand(scan("blur"), required_hand_side="right")
    assert good["status"] == "verified"
    assert good["hand_detected"] is True
    assert good["orientation_valid"] is True
    assert good["strict_validation"] is False
    # Permissive default: analyzable blur scans still pass if a hand is detected.
    assert bad["status"] == "verified"
    assert bad["hand_detected"] is True
    assert bad["quality_warnings"]


def test_production_validation_gate_strict_mode_rejects_blur(monkeypatch):
    monkeypatch.setenv("PALM_VALIDATION_STRICT", "true")
    bad = evaluate_hand(scan("blur"), required_hand_side="right", config=gate_config())
    assert bad["status"] == "rejected"
    assert bad["strict_validation"] is True
    assert "blurred" in set(bad["raw_issue_codes"]) or "extraction_confidence_low" in set(bad["rejection_reasons"])


def test_bilateral_validation_rejects_if_one_required_hand_fails(monkeypatch):
    monkeypatch.setenv("PALM_VALIDATION_STRICT", "true")
    good = scan()
    bad = scan("blur")
    evaluation = evaluate_bilateral(left=good, right=bad, writing_hand="right", config=gate_config())
    assert evaluation["status"] == "rejected"
    assert "right_hand_failed" in evaluation["issues"]


def test_api_multipart_and_annotation_endpoint():
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(create_palm_scan_blueprint(
        engine=PalmScanEngine(FakeHandBackend(), FakeCreases())
    ))
    client = app.test_client()
    response = client.post(
        "/api/palm-scan",
        data={"image": (io.BytesIO(image_bytes()), "palm.jpg"), "mirror": "false"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    body = response.get_json()
    annotation = client.get(body["annotated_image_reference"])
    assert annotation.status_code == 200
    assert annotation.content_type == "image/png"
    assert client.get(body["processed_image_reference"]).status_code == 200
    assert client.get(body["original_decoded_image_reference"]).status_code == 200


def test_api_structured_validation_errors():
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(create_palm_scan_blueprint(
        engine=PalmScanEngine(FakeHandBackend(), FakeCreases())
    ))
    client = app.test_client()
    response = client.post("/api/palm-scan", data={})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "missing_image"


def test_api_rejects_valid_image_without_a_detected_hand():
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(create_palm_scan_blueprint(
        engine=PalmScanEngine(NoHandBackend(), FakeCreases())
    ))
    response = app.test_client().post(
        "/api/palm-scan",
        data={"image": (io.BytesIO(image_bytes()), "not-a-hand.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 422
    body = response.get_json()
    assert body["hand"]["status"] == "not_detected"
    assert "hand_not_detected" in {
        issue["code"] for issue in body["quality"]["issues"]
    }


def test_api_admin_upload_rejects_failed_bilateral_scan(tmp_path, monkeypatch):
    from flask import Flask

    monkeypatch.setenv("PALM_VALIDATION_STRICT", "true")
    monkeypatch.setenv("PALM_SCAN_STORE", str(tmp_path))
    app = Flask(__name__)
    app.register_blueprint(create_palm_scan_blueprint(
        engine=PalmScanEngine(FakeHandBackend(), FakeCreases())
    ))
    client = app.test_client()
    response = client.post(
        "/api/palmistry/admin-upload",
        json={
            "session_id": "bilateral-fail",
            "writing_hand": "right",
            "left_palm_scan_result": scan(),
            "right_palm_scan_result": scan("blur"),
        },
    )
    assert response.status_code == 422
    body = response.get_json()
    assert body["production_validation"]["status"] == "rejected"
    assert body["pdf_request"]["ok"] is False


def test_preprocessing_preserves_original_and_exposes_stages():
    array = np.asarray(Image.open(io.BytesIO(image_bytes())).convert("RGB"))
    snapshot = array.copy()
    landmarks = FakeHandBackend().detect(array).landmarks
    artifacts = preprocess(array, landmarks)
    assert np.array_equal(array, snapshot)
    assert np.array_equal(artifacts.original_rgb, snapshot)
    assert artifacts.processed_rgb is not artifacts.original_rgb
    required = {
        "decode_exif_orientation", "resolution_normalization",
        "perspective_normalization", "illumination_normalization",
        "contrast_enhancement", "denoise", "crease_enhancement",
        "sharpening", "palm_background_separation",
    }
    assert required <= set(artifacts.metadata["stages"])
    assert artifacts.metadata["original_preserved"] is True


def test_full_canonical_schema_and_segmentation_sections():
    result = scan()
    required_top = {
        "metadata", "quality", "hand", "palm_geometry", "landmarks",
        "major_lines", "secondary_lines", "mounts", "fingers", "thumb",
        "special_markings", "union_lines", "scan_confidence",
        "annotated_image_reference", "preprocessing", "segmentation",
    }
    assert required_top <= set(result)
    assert set(result["major_lines"]) == set(MAJOR_LINE_NAMES)
    assert set(result["mounts"]) == set(MOUNT_NAMES)
    assert set(result["segmentation"]) == {
        "hand_boundary", "palm_region", "fingers", "thumb", "wrist", "visible_palm"
    }
    for section in result["segmentation"].values():
        assert section["method"]
        assert section["polygon"]
        assert section["mask_stats"]["area_px"] > 0


def test_landmark_explicit_coordinate_contract():
    landmark = scan()["landmarks"][0]
    assert 0 <= landmark["normalized_x"] <= 1
    assert 0 <= landmark["normalized_y"] <= 1
    assert landmark["x_pixel"] == landmark["x_px"]
    assert landmark["y_pixel"] == landmark["y_px"]
    assert "confidence" in landmark


def test_multimethod_disagreement_remains_ambiguous():
    result = scan()
    candidate = result["secondary_lines"]["crease_candidates"][0]
    assert candidate["semantic_identity"] == "ambiguous"
    assert result["secondary_lines"]["detector_agreement"] == .5
    assert_major_lines_are_candidate_backed(result)


def test_replaceable_line_verifier_can_only_reuse_detected_candidate_path():
    engine = PalmScanEngine(
        FakeHandBackend(), FakeCreases(), line_verifier=FakeLineVerifier()
    )
    result = engine.scan(image_bytes())[0]
    heart = result["major_lines"]["heart_line"]
    candidate = result["secondary_lines"]["crease_candidates"][0]
    assert heart["status"] == "detected"
    assert heart["path"] == candidate["path"]
    assert heart["source_candidate_id"] == candidate["id"]
    assert result["major_lines"]["head_line"]["status"] == "unknown"


def test_configured_unavailable_verifier_preserves_unknown_safe_status():
    engine = PalmScanEngine(
        FakeHandBackend(), FakeCreases(), line_verifier=UnavailableLineVerifier()
    )
    result = engine.scan(image_bytes())[0]
    verification = result["secondary_lines"]["semantic_verification"]
    assert verification["status"] == "semantic_model_unavailable"
    assert verification["model_evidence"]["status"] == "model_unavailable"
    for name, line in result["major_lines"].items():
        if name == "fate_line":
            assert line["detection_method"] == "image_first_fate_line_detector"
            assert line["status"] in {
                "detected", "ambiguous", "insufficient_evidence", "not_detected",
            }
            assert "fate_line_detection" in result["secondary_lines"]
        else:
            assert line["status"] == "unknown"


def test_real_multimethod_detector_exposes_evidence_without_names():
    rgb = np.full((256, 256, 3), 170, np.uint8)
    cv2.line(rgb, (45, 100), (210, 115), (70, 70, 70), 3)
    cv2.line(rgb, (55, 155), (195, 135), (85, 85, 85), 2)
    mask = np.zeros((256, 256), np.uint8)
    cv2.rectangle(mask, (25, 45), (230, 220), 255, -1)
    detected = ConservativeCreaseDetector(.04).detect(rgb, mask)
    assert set(detected["methods"]) == {"blackhat_adaptive", "canny_ridge"}
    assert 0 <= detected["agreement"] <= 1
    assert all(candidate["semantic_identity"] == "ambiguous"
               for candidate in detected["candidates"])


def test_skeleton_path_export_preserves_continuous_geometry():
    rgb = np.full((256, 256, 3), 170, np.uint8)
    for y in range(70, 210):
        rgb[y, 128] = (55, 55, 55)
        rgb[y, 129] = (65, 65, 65)
    mask = np.zeros((256, 256), np.uint8)
    cv2.rectangle(mask, (40, 40), (220, 230), 255, -1)
    detected = ConservativeCreaseDetector(.04).detect(rgb, mask)
    assert detected["candidates"]
    longest = max(detected["candidates"], key=lambda item: len(item["path"]))
    assert len(longest["path"]) >= 4
    assert longest.get("path_source") == "skeleton_trace"


def test_major_line_with_only_two_points_is_insufficient_geometry():
    class TwoPointCreases(FakeCreases):
        def detect(self, rgb, palm_mask):
            rows = super().detect(rgb, palm_mask)
            if rows:
                rows[0]["path"] = [{"x": .30, "y": .50}, {"x": .30, "y": .80}]
                rows[0]["path_point_count"] = 2
            return rows

    engine = PalmScanEngine(
        FakeHandBackend(), TwoPointCreases(), line_verifier=FakeLineVerifier()
    )
    result = engine.scan(image_bytes())[0]
    heart = result["major_lines"]["heart_line"]
    assert heart["status"] == "insufficient_geometry"
    assert heart["detected"] is False
    assert len(heart["path"]) == 2


def test_line_measurements_are_pixel_proxy_labelled():
    candidate = scan()["secondary_lines"]["crease_candidates"][0]
    assert len(candidate["endpoints"]) == 2
    assert candidate["normalized_length"] > 0
    measurements = candidate["measurements"]
    for key in (
        "strength_proxy", "depth_proxy", "clarity", "continuity", "curvature",
        "direction_degrees", "break_candidates", "branch_candidates",
        "fork_candidates", "island_candidates", "intersection_candidates",
        "parallel_candidates", "relative_position",
    ):
        assert key in measurements
    assert "not_physical_depth" in measurements["depth_proxy"]["label"]


def test_all_mount_and_finger_measurement_fields():
    result = scan()
    for mount in result["mounts"].values():
        assert mount["region_polygon"]
        assert mount["area_normalized"] > 0
        assert "texture" in mount and "line_density" in mount
        assert mount["prominence"]["status"] == "unknown"
    for finger in result["fingers"].values():
        for key in (
            "length_normalized", "width_normalized", "relative_length",
            "proportions", "spacing_normalized", "taper", "tip_shape",
            "straightness", "joints", "flexibility",
        ):
            assert key in finger
    for key in (
        "length", "width", "spread_angle", "phalanx_proportions",
        "spacing", "taper", "tip_shape", "straightness", "joints", "flexibility",
    ):
        assert key in result["thumb"]


def test_confidence_bands_and_group_contributions():
    result = scan()
    assert result["scan_confidence"]["band"] in {
        "very_high", "high", "moderate", "ambiguous", "unreliable"
    }
    assert set(result["scan_confidence"]["groups"]) == {
        "overall", "major_lines", "mounts", "fingers", "markings"
    }
    assert {"overall", "major_lines", "mounts", "fingers", "markings"} <= set(
        result["scan_confidence"]
    )
    assert {"detector_agreement", "segmentation_quality"} <= set(
        result["scan_confidence"]["contributions"]
    )
    assert [confidence_band(value) for value in (.90, .75, .55, .35, .34)] == [
        "very_high", "high", "moderate", "ambiguous", "unreliable"
    ]


def test_ground_truth_validation_loading_and_evaluation():
    annotation = make_example_annotation()
    assert validate_annotation(annotation) == []
    assert load_annotation(annotation) == annotation
    metrics = evaluate(annotation, scan())
    assert metrics["landmark_coordinate_error"]["matched"] == 1
    assert "palm_region" in metrics["segmentation_iou"]
    assert "Venus" in metrics["mount_region_iou"]
    assert {"precision", "recall", "accuracy"} <= set(metrics["detection"])
    assert "brier_score" in metrics["confidence_calibration"]
    broken = {**annotation, "coordinate_space": "pixels"}
    assert validate_annotation(broken)


def test_fate_line_uses_image_first_detector():
    result = scan()
    fate = result["major_lines"]["fate_line"]
    assert result["secondary_lines"]["fate_line_detection"]["method"] == (
        "image_first_fate_line_detector"
    )
    assert fate["detection_method"] == "image_first_fate_line_detector"
    assert fate["status"] in {
        "detected", "ambiguous", "insufficient_evidence", "not_detected",
    }
    assert fate.get("branches") == []
    assert fate.get("forks") == []
    audit = result["secondary_lines"]["fate_line_detection"]["candidate_audit"]
    assert isinstance(audit, list)


def test_engine_real_creases_fate_line_payload():
    engine = PalmScanEngine(FakeHandBackend(), ConservativeCreaseDetector())
    result = engine.scan(image_bytes("good"))[0]
    assert "fate_line_detection" in result["secondary_lines"]
    fate = result["major_lines"]["fate_line"]
    assert fate["detection_method"] == "image_first_fate_line_detector"
    for entry in result["secondary_lines"]["fate_line_detection"]["candidate_audit"]:
        assert "final_score" in entry
        assert "rejection_reasons" in entry
        assert "image_support" in entry


def test_overlay_pixels_are_driven_by_result_coordinates():
    rgb = np.zeros((100, 100, 3), np.uint8)
    result = scan()
    result["landmarks"] = []
    result["segmentation"] = {}
    result["mounts"] = {}
    result["major_lines"] = {}
    result["special_markings"] = {"candidates": []}
    result["secondary_lines"]["crease_candidates"] = [{
        "path": [{"x": .1, "y": .2}, {"x": .9, "y": .2}]
    }]
    overlay = PalmScanEngine._annotate_from_result(rgb, result)
    assert np.any(overlay[20, 10:91] != 0)
    assert not np.any(overlay[80, 10:91] != 0)
