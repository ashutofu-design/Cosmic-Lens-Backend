"""Master extraction layer: measurement-only, nested, Phase 2 compatible."""
from __future__ import annotations

import io

import pytest
from flask import Flask

from vedic.palm_scan.api import create_palm_scan_blueprint
from vedic.palm_scan.engine import empty_result
from vedic.palm_scan.master_layer import (
    MASTER_SCHEMA,
    attach_master_extraction,
    compose_bilateral_comparison,
)
from vedic.palm_scan.store import get_session, save_hand
from palmistry_human_orders import create_order
from vedic.palmistry_phase2.engine import PalmistryPhase2Engine
from vedic.palmistry_phase2.schema import prepare_for_phase2, validate_palm_scan_result

from test_palm_scan_phase1 import FakeCreases, FakeHandBackend, image_bytes
from vedic.palm_scan.engine import PalmScanEngine


FORBIDDEN = (
    "rich", "poor", "loyal", "unfaithful", "successful", "unlucky",
    "long life", "short life", "marriage age", "career success",
    "fortune teller",
)


def _scan():
    engine = PalmScanEngine(FakeHandBackend(), FakeCreases())
    result, _ = engine.scan(image_bytes())
    return attach_master_extraction(result, writing_hand="right", hand_slot="right")


def test_master_extraction_is_nested_and_measurement_only():
    result = _scan()
    master = result["master_extraction"]
    assert result["schema_version"] == "1.0"
    assert master["schema_version"] == MASTER_SCHEMA
    assert master["hand_side"] == "right"
    assert master["dominant_status"] == "dominant"
    required = {
        "image_quality", "palm_geometry", "coordinate_system", "palm_map",
        "landmarks", "major_lines", "line_stitching", "minor_lines", "line_segments",
        "line_micro_features", "mounts", "fingers", "fingertips", "thumb",
        "wrist_rascette", "special_markings", "line_relationships",
        "marking_relationships", "confidence", "validation",
    }
    assert required <= set(master)
    assert "Plain of Mars" in master["mounts"]
    assert master["minor_lines"]["travel_lines"]["status"] in {
        "not_detected", "unknown",
    }
    assert master["wrist_rascette"]["first_bracelet_line"]["status"] == "not_detected"
    text = str(master).lower()
    for word in FORBIDDEN:
        assert word not in text
    assert "phase 2" in " ".join(master["notes"]).lower() or "measured geometry" in text


def test_empty_result_attaches_without_inventing_features():
    result = attach_master_extraction(
        empty_result(scan_id="empty-master"), writing_hand="left", hand_slot="left",
    )
    master = result["master_extraction"]
    assert master["dominant_status"] == "dominant"
    assert master["image_quality"]["capture_decision"] == "retake_required"
    assert master["thumb"]["flexibility"]["status"] == "unknown"
    validation = validate_palm_scan_result(result)
    # Nested master fields are extra; Phase 2 still requires exact 1.0 statuses.
    if not validation.valid:
        stripped = prepare_for_phase2(result)
        assert validate_palm_scan_result(stripped).valid


def test_phase2_strips_master_and_accepts_eligible_scan():
    result = empty_result(scan_id="phase2-master")
    result["quality"].update({"status": "usable", "usable": True, "score": .92, "gate": "passed"})
    result["validation"].update({
        "status": "accepted_measurements_only", "quality_gate": "passed",
    })
    result["scan_confidence"].update({
        "value": .90, "overall": .90, "is_reliable": True, "phase_2_eligible": True,
        "phase_2_reason": "eligible_measurement_only",
        "eligible_features": {"major_lines": [], "mounts": [], "fingers": [], "markings": []},
    })
    result["hand"].update({"status": "detected", "confidence": .9, "side": "right", "handedness": "right"})
    attach_master_extraction(result, writing_hand="right", hand_slot="right")
    reading = PalmistryPhase2Engine().analyze(result)
    assert reading["status"] != "invalid_palm_scan_result"
    assert "master_extraction" not in prepare_for_phase2(result)


def test_bilateral_comparison_is_geometry_only():
    left = attach_master_extraction(
        empty_result(scan_id="L"), writing_hand="right", hand_slot="left",
    )
    right = attach_master_extraction(
        empty_result(scan_id="R"), writing_hand="right", hand_slot="right",
    )
    left["palm_geometry"]["aspect_ratio"]["raw_ratio"] = 0.9
    right["palm_geometry"]["aspect_ratio"]["raw_ratio"] = 1.1
    left["scan_confidence"]["overall"] = 0.7
    right["scan_confidence"]["overall"] = 0.8
    comparison = compose_bilateral_comparison(left=left, right=right, writing_hand="right")
    assert comparison["dominant_hand"] == "right"
    assert comparison["non_dominant_hand"] == "left"
    aspect = next(item for item in comparison["comparisons"] if item["id"] == "palm_aspect_ratio")
    assert aspect["difference"] == pytest.approx(0.2)
    assert comparison["claims_forbidden"] is True
    text = str(comparison).lower()
    for word in FORBIDDEN:
        assert word not in text


def test_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PALM_SCAN_STORE", str(tmp_path))
    result = attach_master_extraction(
        empty_result(scan_id="stored"), writing_hand="left", hand_slot="left",
    )
    save_hand(
        session_id="sess1", hand_side="left", writing_hand="left",
        user_id="u1", result=result,
    )
    record = get_session("sess1")
    assert record["hands"]["left"]["palm_scan_result"]["master_extraction"]["hand_side"] == "left"
    assert record["verification"]["status"] == "machine_only"
    assert record["hands"]["left"]["validation_status"] in {"pending", "verified", "rejected"}


def test_api_persists_session_and_exposes_master(tmp_path, monkeypatch):
    monkeypatch.setenv("PALM_SCAN_STORE", str(tmp_path))
    app = Flask(__name__)
    app.register_blueprint(create_palm_scan_blueprint(
        engine=PalmScanEngine(FakeHandBackend(), FakeCreases())
    ))
    client = app.test_client()
    response = client.post(
        "/api/palm-scan",
        data={
            "image": (io.BytesIO(image_bytes()), "palm.jpg"),
            "mirror": "false",
            "hand_side": "right",
            "writing_hand": "right",
            "session_id": "web1",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["master_extraction"]["dominant_status"] == "dominant"
    assert body["admin_session"]["persisted"] is True
    listed = client.get("/api/admin/palm-scans")
    # Without flask_app admin token this may 401; session file must still exist.
    assert (tmp_path / "sessions" / "web1.json").is_file()
    page = client.get("/admin/palm-scans")
    assert page.status_code == 200
    assert b"Palm Master Extraction" in page.data
    assert listed.status_code in {200, 401, 503}


def test_create_order_rejects_failed_bilateral_validation():
    left = _scan()
    right = _scan()
    right["quality"]["usable"] = False
    right["quality"]["gate"] = "failed"
    right["quality"]["issues"] = [{"code": "blurred", "message": "Image too blurry", "severity": "error"}]
    right["validation"]["status"] = "rejected"
    right["scan_confidence"]["overall"] = 0.2
    with pytest.raises(ValueError):
        create_order(
            session_id="reject-order",
            writing_hand="right",
            left=left,
            right=right,
            comparison={},
            user_id="1",
            cosmo_user_id="COSMO1",
            name="Test User",
        )
