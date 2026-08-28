"""Contract, rule, system isolation, conflict, grounding, and API tests."""
from __future__ import annotations

import copy
import io
import json
from dataclasses import replace

import numpy as np
import pytest
from flask import Flask
from PIL import Image

from vedic.face_reading_phase2.api import (
    create_face_reading_phase2_blueprint,
)
from vedic.face_reading_phase2.conflicts import resolve_domain
from vedic.face_reading_phase2.engine import FaceReadingPhase2Engine
from vedic.face_reading_phase2.rules import (
    DEFAULT_SYSTEM_ID,
    SYSTEMS,
    RuleSystem,
)
from vedic.face_scan.backend import DetectionBatch, FaceCandidate
from vedic.face_scan.engine import FaceScanEngine, NAMED_INDICES


def _image_bytes() -> bytes:
    rng = np.random.default_rng(42)
    pixels = np.full((900, 720, 3), 145, dtype=np.int16)
    pixels += rng.integers(-35, 36, pixels.shape, dtype=np.int16)
    output = io.BytesIO()
    Image.fromarray(np.uint8(np.clip(pixels, 0, 255))).save(
        output, "JPEG", quality=92
    )
    return output.getvalue()


def _mesh() -> list[tuple[float, float, float]]:
    points = [(0.5, 0.5, 0.0) for _ in range(478)]
    values = {
        "forehead_center": (.50, .12), "glabella": (.50, .26),
        "face_left": (.20, .52), "face_right": (.80, .52),
        "chin_tip": (.50, .90), "nose_bridge": (.50, .38),
        "nose_bridge_mid": (.50, .48), "nose_tip": (.50, .61),
        "subnasale": (.50, .64), "nose_left": (.43, .60),
        "nose_right": (.57, .60), "mouth_left": (.39, .72),
        "mouth_right": (.61, .72), "upper_lip_top": (.50, .67),
        "upper_lip": (.50, .70), "lower_lip": (.50, .75),
        "lower_lip_bottom": (.50, .78), "philtrum_top": (.50, .64),
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


class _Backend:
    def detect(self, image_bytes, rgb):
        candidate = FaceCandidate(
            landmarks=_mesh(),
            confidence=.93,
            bbox=(.18, .08, .64, .84),
            pose={"yaw_degrees": 0, "pitch_degrees": 0, "roll_degrees": 0},
        )
        return DetectionBatch([candidate], 1, "phase2_fixture")


def scan_fixture() -> dict:
    result, _ = FaceScanEngine(_Backend()).scan_with_artifacts(_image_bytes())
    assert result["validation_status"]["status"] == "valid_measurements"
    assert result["confidence"]["overall"] >= .55
    return result


def _signal(
    rule_id: str, polarity: int, family: str, score: float = .8
) -> dict:
    return {
        "rule_id": rule_id,
        "category": "same_category",
        "polarity": polarity,
        "signed_score": polarity * score,
        "weighted_score": score,
        "propagated_confidence": .8,
        "feature_families": [family],
        "interpretation": f"Traditional symbolic statement {rule_id}.",
        "signal_name": rule_id,
        "signal": "positive" if polarity > 0 else "negative",
        "evidence": [{
            "feature_path": family,
            "measurement_path": f"{family}.value",
            "raw_value": 1,
            "source_confidence": .8,
        }],
    }


def test_schema_mismatch_missing_section_and_raw_image_are_rejected():
    value = scan_fixture()
    value["schema_version"] = "2.0"
    del value["nose"]
    value["image"] = "base64"
    result = FaceReadingPhase2Engine().analyze(value)
    assert result["status"] == "insufficient_data"
    codes = {item["code"] for item in result["issues"]}
    assert {
        "schema_version_mismatch", "missing_required_section",
        "raw_image_input_rejected",
    } <= codes


def test_raw_input_keys_are_rejected_case_insensitively_at_any_depth():
    scan = scan_fixture()
    scan["metadata"]["IMAGE_URL"] = "https://example.invalid/face.jpg"
    result = FaceReadingPhase2Engine().analyze(scan)
    assert result["status"] == "insufficient_data"
    assert "raw_image_input_rejected" in {
        item["code"] for item in result["issues"]
    }


@pytest.mark.parametrize(("path", "value", "code"), [
    (("quality", "gate"), "failed", "quality_gate_failed"),
    (("quality", "usable"), False, "quality_not_usable"),
    (
        ("validation_status", "status"), "unusable_input",
        "phase1_validation_not_accepted",
    ),
    (("confidence", "overall"), .4, "scan_below_reliable_threshold"),
    (("confidence", "overall"), 1.2, "invalid_scan_confidence"),
    (("confidence", "overall"), float("inf"), "invalid_scan_confidence"),
    (
        ("face_detection", "primary_selection_status"), "not_selected",
        "primary_face_not_selected",
    ),
])
def test_admission_gates_return_structured_insufficient_data(path, value, code):
    scan = scan_fixture()
    scan[path[0]][path[1]] = value
    result = FaceReadingPhase2Engine().analyze(scan)
    assert result["status"] == "insufficient_data"
    assert code in {item["code"] for item in result["issues"]}
    assert all(
        domain["classification"] == "insufficient"
        for domain in result["domains"].values()
    )


def test_individual_rule_preserves_measurement_and_confidence_chain():
    result = FaceReadingPhase2Engine().analyze(scan_fixture())
    signal = next(
        item for item in result["all_signals"]
        if item["rule_id"] == f"{DEFAULT_SYSTEM_ID}.NOSE_LENGTH"
    )
    evidence = signal["evidence"][0]
    assert evidence["measurement_path"] == "nose.length.normalized"
    assert evidence["raw_value"] > 0
    assert signal["propagated_confidence"] <= signal["source_confidence"]
    assert signal["propagated_confidence"] <= result["input_scan_confidence"]
    assert signal["confidence_components"]["operator"] == "minimum"


def test_cross_feature_rule_requires_every_independent_feature():
    engine = FaceReadingPhase2Engine()
    scan = scan_fixture()
    result = engine.analyze(scan)
    ids = {item["rule_id"] for item in result["combined_feature_signals"]}
    target = f"{DEFAULT_SYSTEM_ID}.CAREER_RESOURCE_COMBINATION"
    assert target in ids
    scan["chin"]["chin_to_face_ratio"]["confidence"] = .40
    result = engine.analyze(scan)
    assert target not in {
        item["rule_id"] for item in result["combined_feature_signals"]
    }


def test_low_confidence_and_ambiguous_features_do_not_fire():
    scan = scan_fixture()
    scan["nose"]["length"]["confidence"] = .40
    scan["face_shape"].update({
        "status": "ambiguous", "label": "ambiguous", "confidence": .90,
    })
    result = FaceReadingPhase2Engine().analyze(scan)
    ids = {item["rule_id"] for item in result["all_signals"]}
    assert f"{DEFAULT_SYSTEM_ID}.NOSE_LENGTH" not in ids
    assert f"{DEFAULT_SYSTEM_ID}.FACE_OVAL" not in ids
    assert f"{DEFAULT_SYSTEM_ID}.FACE_SQUARE" not in ids


def test_ambiguous_visible_marking_is_never_forced_into_a_rule():
    scan = scan_fixture()
    feature = scan["skin_surface_features"]["visible_marks_or_moles"]
    feature.update({
        "status": "detected", "confidence": .90,
        "items": [{
            "type": "mole", "location": "forehead", "status": "detected",
            "confidence": .90, "ambiguous": True,
        }],
    })
    result = FaceReadingPhase2Engine().analyze(scan)
    assert f"{DEFAULT_SYSTEM_ID}.VERIFIED_FOREHEAD_MARK" not in {
        item["rule_id"] for item in result["all_signals"]
    }


def test_candidate_confidence_is_preserved_separately_and_propagated():
    scan = scan_fixture()
    feature = scan["skin_surface_features"]["visible_marks_or_moles"]
    feature.update({
        "status": "detected", "confidence": .90,
        "items": [{
            "type": "mole", "location": "forehead", "status": "detected",
            "confidence": .75, "ambiguous": False,
        }],
    })
    signal = next(
        item for item in FaceReadingPhase2Engine().analyze(scan)["all_signals"]
        if item["rule_id"] == f"{DEFAULT_SYSTEM_ID}.VERIFIED_FOREHEAD_MARK"
    )
    evidence = signal["evidence"][0]
    assert evidence["container_confidence"] == .90
    assert evidence["candidate_confidence"] == .75
    assert evidence["effective_feature_confidence"] == .75
    assert signal["propagated_confidence"] <= .75


@pytest.mark.parametrize(("shape", "expected"), [
    ("oval", "FACE_OVAL"),
    ("square", "FACE_SQUARE"),
    ("rectangular", "FACE_SQUARE"),
])
def test_different_face_shapes_use_explicit_shape_rules(shape, expected):
    scan = scan_fixture()
    scan["face_shape"].update({
        "status": "classified", "label": shape, "confidence": .88,
    })
    ids = {item["rule_id"] for item in FaceReadingPhase2Engine().analyze(
        scan
    )["all_signals"]}
    assert f"{DEFAULT_SYSTEM_ID}.{expected}" in ids


def test_conflicts_are_mixed_and_minor_signal_cannot_override_structure():
    strong = _signal("STRUCTURE_POSITIVE", 1, "face_structure", .9)
    minor = _signal("MARKING_NEGATIVE", -1, "visible_marking", .25)
    resolved = resolve_domain([strong, minor], .75, require_multiple_families=True)
    assert resolved["normalized_score"] > 0
    assert resolved["supporting_evidence"][0]["rule_id"] == "STRUCTURE_POSITIVE"
    balanced_negative = _signal(
        "STRUCTURE_NEGATIVE", -1, "jaw_structure", .85
    )
    mixed = resolve_domain(
        [strong, balanced_negative], .75, require_multiple_families=True
    )
    assert mixed["classification"] == "mixed"
    assert mixed["mixed_signal"] is True
    assert mixed["contradictions"][0]["resolution"] == "mixed_signal_preserved"


def test_prevailing_confidence_and_family_count_ignore_losing_evidence():
    support = _signal("SUPPORT", 1, "face_structure", .9)
    support["propagated_confidence"] = .55
    losing = _signal("LOSING", -1, "visible_marking", .1)
    losing["propagated_confidence"] = .99
    resolved = resolve_domain(
        [support, losing], .50, require_multiple_families=True
    )
    assert resolved["confidence"] <= .55
    assert resolved["classification"] == "weak"
    assert resolved["conclusion_feature_families"] == ["face_structure"]


def test_single_feature_family_cannot_become_strong_domain_conclusion():
    scan = scan_fixture()
    for feature in (
        scan["forehead"]["height_to_face_ratio"],
        scan["eyebrows"]["inner_spacing"],
        scan["eyes"]["interocular_distance"],
        scan["face_shape"],
    ):
        feature["confidence"] = .2
    result = FaceReadingPhase2Engine().analyze(scan)
    personality = result["domains"]["personality"]
    assert personality["classification"] != "strong"


def test_zone_analysis_uses_only_phase1_zone_names_and_rule_evidence():
    scan = scan_fixture()
    result = FaceReadingPhase2Engine().analyze(scan)
    assert set(result["zone_analysis"]) == set(
        scan["traditional_zones"]["zones"]
    )
    nose = result["zone_analysis"]["nose"]
    assert nose["rules_triggered"]
    assert "nose" in nose["features"][0]
    assert all(item["confidence"] <= scan["confidence"]["overall"]
               for item in nose["signals"])


def test_unavailable_phase1_zone_never_claims_supported_rules():
    scan = scan_fixture()
    scan["traditional_zones"]["zones"]["nose"].update({
        "status": "unknown", "confidence": 0.0, "polygon": [],
    })
    result = FaceReadingPhase2Engine().analyze(scan)
    zone = result["zone_analysis"]["nose"]
    assert zone["status"] == "unavailable"
    assert zone["rules_triggered"] == []
    assert zone["signals"] == []
    assert zone["suppressed_rules"]


def test_traditional_systems_are_isolated_and_not_silently_combined():
    scan = scan_fixture()
    engine = FaceReadingPhase2Engine()
    indian = engine.analyze(scan, traditional_system="indian_samudrik_v1")
    chinese = engine.analyze(
        scan, traditional_system="chinese_mian_xiang_v1"
    )
    assert indian["metadata"]["systems_combined"] is False
    assert chinese["metadata"]["systems_combined"] is False
    assert all(
        item["rule_id"].startswith("indian_samudrik_v1.")
        for item in indian["all_signals"]
    )
    assert all(
        item["rule_id"].startswith("chinese_mian_xiang_v1.")
        for item in chinese["all_signals"]
    )
    assert {
        item["rule_id"] for item in indian["all_signals"]
    }.isdisjoint({item["rule_id"] for item in chinese["all_signals"]})
    unsupported = engine.analyze(scan, traditional_system="mixed_all")
    assert unsupported["status"] == "insufficient_data"


def test_rule_registry_is_versioned_modular_and_unique():
    for system_id, system in SYSTEMS.items():
        ids = [rule.rule_id for rule in system.rules]
        assert len(ids) == len(set(ids))
        assert system.version == "1.0"
        assert all(rule.system_id == system_id for rule in system.rules)
        assert all(rule.rule_id.startswith(f"{system_id}.") for rule in system.rules)
        assert all(rule.evidence_requirements for rule in system.rules)
        assert all(rule.priority in {1, 2, 3, 4} for rule in system.rules)
        assert all(
            rule.scope != "cross" or len(set(rule.feature_families)) >= 2
            for rule in system.rules
        )


def test_registry_rejects_cross_rules_without_independent_families():
    system = SYSTEMS[DEFAULT_SYSTEM_ID]
    invalid_rule = replace(
        system.rules[0], scope="cross", feature_families=("face_structure",)
    )
    invalid_system = RuleSystem(
        system.system_id, system.namespace, system.version,
        system.display_name, (invalid_rule,), system.disclaimer,
    )
    with pytest.raises(ValueError, match="needs two families"):
        FaceReadingPhase2Engine(systems={system.system_id: invalid_system})


def test_selected_system_marks_unimplemented_categories_explicitly():
    result = FaceReadingPhase2Engine().analyze(scan_fixture())
    category = result["domains"]["money"]["categories"]["earning_orientation"]
    assert category["status"] == "not_supported_by_ruleset"
    assert category["supported_by_selected_system"] is False




def test_deterministic_regression_and_unrelated_rule_stability():
    scan = scan_fixture()
    engine = FaceReadingPhase2Engine()
    first = engine.analyze(scan)
    second = engine.analyze(copy.deepcopy(scan))
    assert first == second
    ids = [item["rule_id"] for item in first["all_signals"]]
    assert ids[:4] == [
        "indian_samudrik_v1.FACE_LONG",
        "indian_samudrik_v1.THIRDS_BALANCED",
        "indian_samudrik_v1.SYMMETRY_LOW_ERROR",
        "indian_samudrik_v1.FOREHEAD_RELATIVE_HIGH",
    ]
    altered = copy.deepcopy(scan)
    altered["nose"]["length"]["confidence"] = .2
    changed = engine.analyze(altered)
    unaffected = {
        rule_id for rule_id in ids if ".NOSE_" not in rule_id
        and ".CAREER_RESOURCE_COMBINATION" not in rule_id
    }
    assert unaffected <= {item["rule_id"] for item in changed["all_signals"]}


def test_narrator_is_grounded_traditional_and_has_required_sections():
    result = FaceReadingPhase2Engine().analyze(scan_fixture())
    narration = result["narration"]
    assert narration["grounded_only"] is True
    assert set(narration["sections"]) == {
        "Overall Face Profile", "Personality & Temperament",
        "Communication & Social Style", "Love & Relationships",
        "Career & Work Style", "Money Tendencies",
        "Leadership / Recognition", "Strengths", "Challenges",
        "Important Combined Patterns", "Traditional Face-Reading Guidance",
        "Confidence & Limitations",
    }
    allowed = {item["interpretation"] for item in result["all_signals"]}
    for statements in narration["sections"].values():
        for statement in statements:
            assert (
                statement["text"] in allowed
                or statement["source"] in {
                    "cross_domain_tensions", "disclaimer",
                }
            )
    text = (narration["text"] + narration["disclaimer"]).lower()
    assert "not a scientific assessment" in text
    for forbidden in (
        "proves that you", "diagnosed", "guaranteed wealth",
        "criminality", "your ethnicity", "exact date",
    ):
        assert forbidden not in text


def test_custom_narrator_cannot_inject_an_ungrounded_claim():
    class UnsafeNarrator:
        def narrate(self, analysis):
            return {
                "grounded_only": True,
                "sections": {
                    "Overall Face Profile": [{
                        "text": "Invented unsupported conclusion.",
                        "rule_ids": [],
                    }]
                },
                "text": "Invented unsupported conclusion.",
                "disclaimer": "",
            }

    with pytest.raises(ValueError, match="ungrounded"):
        FaceReadingPhase2Engine(
            narrator=UnsafeNarrator()
        ).analyze(scan_fixture())


def test_api_is_json_only_lists_systems_and_never_consumes_artifacts():
    app = Flask(__name__)
    app.register_blueprint(create_face_reading_phase2_blueprint())
    client = app.test_client()
    multipart = client.post(
        "/api/face-reading/interpret",
        data={"image": (io.BytesIO(b"pixels"), "face.jpg")},
        content_type="multipart/form-data",
    )
    assert multipart.status_code == 415
    assert multipart.get_json()["error"]["code"] == "json_only"
    raw = client.post(
        "/api/face-reading/interpret", json={"image": "base64"}
    )
    assert raw.status_code == 415
    mixed_case_raw = client.post(
        "/api/face-reading/interpret", json={"Image": "base64"}
    )
    assert mixed_case_raw.status_code == 415
    nested = scan_fixture()
    nested["metadata"]["Artifact"] = "hidden-image-reference"
    nested_raw = client.post(
        "/api/face-reading/interpret",
        json={"face_scan_result": nested},
    )
    assert nested_raw.status_code == 415
    success = client.post(
        "/api/face-reading/interpret",
        json={"face_scan_result": scan_fixture()},
    )
    assert success.status_code == 200
    body = success.get_json()
    assert body["metadata"]["image_or_artifact_consumed"] is False
    assert "image" not in json.dumps(body["explainability"]).lower()
    systems = client.get("/api/face-reading/systems")
    assert systems.status_code == 200
    assert len(systems.get_json()["systems"]) == 2
