"""Bilateral palm comparison, confidence, role, and API tests."""
from __future__ import annotations

import copy

from flask import Flask

from vedic.palm_scan.engine import empty_result
from vedic.palmistry_phase2.api import create_palmistry_phase2_blueprint
from vedic.palmistry_phase2.bilateral import BilateralPalmistryEngine
from vedic.palmistry_phase2.engine import PalmistryPhase2Engine


def scan_fixture(side: str, clarity: float = .8) -> dict:
    scan = empty_result(scan_id=f"{side}-fixture")
    scan["quality"].update({
        "status": "usable", "usable": True, "score": .92, "gate": "passed",
    })
    scan["validation"].update({
        "status": "accepted_measurements_only", "quality_gate": "passed",
    })
    scan["hand"].update({
        "status": "detected", "confidence": .94, "side": side,
        "handedness": side,
    })
    scan["scan_confidence"].update({
        "value": .90, "overall": .90, "is_reliable": True,
        "phase_2_eligible": True,
        "phase_2_reason": "eligible_measurement_only",
        "eligible_features": {
            "major_lines": ["head_line"], "mounts": [],
            "fingers": [], "markings": [],
        },
    })
    candidate_id = f"{side}_head"
    path = [{"x": .25, "y": .55}, {"x": .72, "y": .58}]
    scan["major_lines"]["head_line"].update({
        "status": "detected", "detected": True, "confidence": .88,
        "source_candidate_id": candidate_id, "path": path,
    })
    scan["major_lines"]["head_line"]["measurements"].update({
        "clarity": clarity, "curvature": .10,
    })
    scan["secondary_lines"]["crease_candidates"] = [{
        "id": candidate_id, "status": "detected", "confidence": .88,
        "semantic_identity": "ambiguous", "path": path,
    }]
    scan["secondary_lines"]["semantic_verification"] = {
        "status": "completed",
        "interface": "candidate_id_assignments_only",
        "coordinates_source": "crease_candidates",
    }
    return scan


def test_single_hand_reading_is_explicitly_partial():
    result = PalmistryPhase2Engine().analyze(scan_fixture("right"))
    assert result["status"] == "ok"
    assert result["reading_completeness"]["mode"] == "single_hand"
    assert result["reading_completeness"]["score"] < 1
    assert result["reading_completeness"][
        "bilateral_comparison_available"
    ] is False
    assert result["final_reading_confidence"] < result["input_scan_confidence"]


def test_right_writing_hand_maps_roles_and_detects_development_difference():
    left = scan_fixture("left", clarity=.70)
    right = scan_fixture("right", clarity=.90)
    result = BilateralPalmistryEngine().analyze(
        left_palm_scan_result=left,
        right_palm_scan_result=right,
        writing_hand="right",
    )
    assert result["status"] == "ok"
    assert result["hands"]["dominant"]["side"] == "right"
    assert result["hands"]["non_dominant"]["side"] == "left"
    assert result["reading_completeness"]["score"] == 1
    comparison = next(
        item for item in result["comparisons"]
        if item["comparison_id"] == "head_clarity"
    )
    assert comparison["direction"] == "higher_in_dominant"
    assert comparison["dominant_value"] == .90
    assert comparison["non_dominant_value"] == .70
    assert comparison["confidence"] <= .88
    assert result["combined_domains"]["personality"][
        "status"
    ] == "comparative_difference"


def test_left_writing_hand_reverses_dominant_and_baseline_roles():
    result = BilateralPalmistryEngine().analyze(
        left_palm_scan_result=scan_fixture("left", clarity=.90),
        right_palm_scan_result=scan_fixture("right", clarity=.70),
        writing_hand="left",
    )
    assert result["hands"]["dominant"]["side"] == "left"
    assert result["hands"]["non_dominant"]["side"] == "right"
    comparison = next(
        item for item in result["comparisons"]
        if item["comparison_id"] == "head_clarity"
    )
    assert comparison["direction"] == "higher_in_dominant"


def test_side_mismatch_invalid_writing_hand_and_low_confidence_fail_closed():
    left = scan_fixture("right")
    right = scan_fixture("right")
    right["hand"]["confidence"] = .4
    result = BilateralPalmistryEngine().analyze(
        left_palm_scan_result=left,
        right_palm_scan_result=right,
        writing_hand="unknown",
    )
    codes = {item["code"] for item in result["issues"]}
    assert {
        "invalid_writing_hand", "hand_side_mismatch",
        "handedness_below_reliable_threshold",
    } <= codes
    assert result["status"] == "insufficient_data"
    assert result["reading_completeness"]["score"] == 0


def test_bilateral_result_is_deterministic_and_does_not_consume_images():
    left = scan_fixture("left", clarity=.70)
    right = scan_fixture("right", clarity=.90)
    engine = BilateralPalmistryEngine()
    first = engine.analyze(
        left_palm_scan_result=left,
        right_palm_scan_result=right,
        writing_hand="right",
    )
    second = engine.analyze(
        left_palm_scan_result=copy.deepcopy(left),
        right_palm_scan_result=copy.deepcopy(right),
        writing_hand="right",
    )
    assert first == second
    assert first["metadata"]["image_or_artifact_consumed"] is False
    assert first["narration"]["grounded_only"] is True
    assert "not a scientific assessment" in first["narration"]["disclaimer"]


def test_bilateral_api_requires_exact_two_scan_contract():
    app = Flask(__name__)
    app.register_blueprint(create_palmistry_phase2_blueprint())
    client = app.test_client()
    incomplete = client.post(
        "/api/palm-reading/interpret-bilateral",
        json={"left_palm_scan_result": scan_fixture("left")},
    )
    assert incomplete.status_code == 422
    nested_raw = scan_fixture("left")
    nested_raw["metadata"]["Image"] = "base64"
    rejected = client.post(
        "/api/palm-reading/interpret-bilateral",
        json={
            "left_palm_scan_result": nested_raw,
            "right_palm_scan_result": scan_fixture("right"),
            "writing_hand": "right",
        },
    )
    assert rejected.status_code == 415
    success = client.post(
        "/api/palm-reading/interpret-bilateral",
        json={
            "left_palm_scan_result": scan_fixture("left", clarity=.70),
            "right_palm_scan_result": scan_fixture("right", clarity=.90),
            "writing_hand": "right",
        },
    )
    assert success.status_code == 200
    assert success.get_json()["reading_completeness"]["mode"] == "bilateral"
