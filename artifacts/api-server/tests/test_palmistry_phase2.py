"""Focused contract, rule, fusion, grounding, and API tests for Phase 2."""
from __future__ import annotations

import copy
import io

import pytest
from flask import Flask

from vedic.palm_scan.engine import empty_result
from vedic.palmistry_phase2.api import create_palmistry_phase2_blueprint
from vedic.palmistry_phase2.engine import PalmistryPhase2Engine


def scan_fixture() -> dict:
    result = empty_result(scan_id="phase2-fixture")
    result["quality"].update({"status": "usable", "usable": True, "score": .92, "gate": "passed"})
    result["validation"].update({
        "status": "accepted_measurements_only", "quality_gate": "passed",
    })
    result["scan_confidence"].update({
        "value": .90, "overall": .90, "is_reliable": True, "phase_2_eligible": True,
        "phase_2_reason": "eligible_measurement_only",
        "eligible_features": {"major_lines": [], "mounts": [], "fingers": [], "markings": []},
    })
    return result


def line(scan: dict, name: str, **measurements) -> None:
    candidate_id = f"fixture_{name}"
    path = [{"x": .25, "y": .55}, {"x": .72, "y": .58}]
    feature = scan["major_lines"][name]
    feature.update({
        "status": "detected", "detected": True, "confidence": .88,
        "source_candidate_id": candidate_id, "path": path,
    })
    feature["measurements"].update(measurements)
    scan["secondary_lines"].setdefault("crease_candidates", []).append({
        "id": candidate_id, "status": "detected", "confidence": .88,
        "semantic_identity": "ambiguous", "path": path,
    })
    scan["secondary_lines"]["semantic_verification"] = {
        "status": "completed",
        "interface": "candidate_id_assignments_only",
        "coordinates_source": "crease_candidates",
    }
    scan["scan_confidence"]["eligible_features"]["major_lines"].append(name)


def finger(scan: dict, name: str, relative_length: str) -> None:
    scan["fingers"][name].update({
        "status": "detected", "confidence": .84, "relative_length": relative_length,
    })
    scan["scan_confidence"]["eligible_features"]["fingers"].append(name)


def mount(scan: dict, name: str, value: float) -> None:
    scan["mounts"][name].update({"status": "detected", "confidence": .83})
    scan["mounts"][name]["development"].update({
        "status": "detected", "confidence": .81, "value": value,
    })
    scan["scan_confidence"]["eligible_features"]["mounts"].append(name)


def test_schema_mismatch_and_missing_section_are_structured():
    value = scan_fixture()
    value["schema_version"] = "2.0"
    del value["thumb"]
    result = PalmistryPhase2Engine().analyze(value)
    assert result["status"] == "insufficient_data"
    assert {item["code"] for item in result["issues"]} == {
        "schema_version_mismatch", "missing_required_section",
    }


def test_invalid_confidence_status_readability_and_conflicts_are_rejected():
    value = scan_fixture()
    value["hand"]["confidence"] = 1.2
    value["hand"]["status"] = "invented"
    value["union_lines"]["readable"] = "yes"
    value["conflicts"] = {}
    codes = {item["code"] for item in PalmistryPhase2Engine().analyze(value)["issues"]}
    assert {"invalid_confidence", "invalid_status", "invalid_readability", "invalid_conflicts"} <= codes


@pytest.mark.parametrize("section", [
    "metadata", "quality", "hand", "palm_geometry", "preprocessing",
    "segmentation", "major_lines", "secondary_lines", "mounts", "fingers",
    "thumb", "special_markings", "union_lines", "validation", "scan_confidence",
])
def test_malformed_object_sections_never_crash(section):
    value = scan_fixture()
    value[section] = []
    result = PalmistryPhase2Engine().analyze(value)
    assert result["status"] == "insufficient_data"
    assert "invalid_section_type" in {item["code"] for item in result["issues"]}


@pytest.mark.parametrize(("path", "bad_value", "code"), [
    (("validation", "status"), "rejected", "validation_status_not_accepted"),
    (("validation", "quality_gate"), "failed", "validation_quality_gate_failed"),
    (("quality", "gate"), "failed", "quality_gate_failed"),
    (("quality", "usable"), False, "quality_not_usable"),
    (("scan_confidence", "phase_2_eligible"), False, "phase_2_not_eligible"),
    (("scan_confidence", "phase_2_reason"), "below_reliable_threshold", "phase_2_reason_incompatible"),
    (("scan_confidence", "value"), .4, "scan_below_reliable_threshold"),
])
def test_every_admission_gate_returns_structured_issue(path, bad_value, code):
    value = scan_fixture()
    value[path[0]][path[1]] = bad_value
    result = PalmistryPhase2Engine().analyze(value)
    assert result["status"] == "insufficient_data"
    assert code in {item["code"] for item in result["issues"]}


def test_default_phase1_result_is_legitimately_insufficient():
    result = PalmistryPhase2Engine().analyze(empty_result(scan_id="empty"))
    assert result["status"] == "insufficient_data"
    assert all(domain["classification"] == "insufficient" for domain in result["domains"].values())


def test_individual_line_rule_has_full_evidence_and_confidence_cap():
    value = scan_fixture()
    line(value, "head_line", clarity=.8)
    result = PalmistryPhase2Engine().analyze(value)
    signal = next(item for item in result["single_feature_signals"] if item["rule_id"] == "head_clear")
    assert signal["evidence"][0]["measurement_path"] == "major_lines.head_line.measurements.clarity"
    assert signal["evidence"][0]["raw_value"] == .8
    assert signal["propagated_confidence"] <= signal["source_confidence"]
    assert signal["propagated_confidence"] <= result["input_scan_confidence"]
    assert signal["confidence_components"]["operator"] == "minimum"


def test_detected_named_line_requires_candidate_path_provenance():
    value = scan_fixture()
    value["major_lines"]["head_line"].update({
        "status": "detected", "detected": True, "confidence": .88,
    })
    value["major_lines"]["head_line"]["measurements"]["clarity"] = .8
    value["scan_confidence"]["eligible_features"]["major_lines"].append("head_line")
    result = PalmistryPhase2Engine().analyze(value)
    codes = {item["code"] for item in result["issues"]}
    assert {"unverified_named_lines", "missing_line_provenance"} <= codes


def test_combined_independent_families_can_be_strong():
    value = scan_fixture()
    line(value, "fate_line", clarity=.8)
    finger(value, "index", "long")
    result = PalmistryPhase2Engine().analyze(value)
    assert result["domains"]["career"]["classification"] == "strong"
    assert set(result["domains"]["career"]["feature_families"]) == {"major_line", "finger_structure"}


def test_conflicting_signals_are_preserved_not_max_selected():
    value = scan_fixture()
    line(value, "heart_line", clarity=.8, break_candidates=[{"x": .4, "y": .5}])
    result = PalmistryPhase2Engine().analyze(value)
    domain = result["domains"]["love_relationships"]
    assert domain["classification"] == "mixed"
    assert domain["confidence"] > 0
    assert domain["positive_evidence"] and domain["negative_evidence"]
    assert domain["contradictions"][0]["resolution"] == "mixed_signal_preserved"
    assert {
        item["signal"] for item in domain["conclusion"]["evidence"]
    } == {"positive", "negative"}


def test_single_feature_family_cannot_become_major_domain_conclusion():
    value = scan_fixture()
    line(value, "head_line", clarity=.9, curvature=.4)
    domain = PalmistryPhase2Engine().analyze(value)["domains"]["personality"]
    assert domain["feature_families"] == ["major_line"]
    assert domain["classification"] == "weak"


def test_low_confidence_unknown_and_ambiguous_markings_do_not_fire():
    value = scan_fixture()
    line(value, "sun_apollo_line", clarity=.9)
    value["major_lines"]["sun_apollo_line"]["confidence"] = .50
    value["special_markings"].update({
        "status": "detected", "confidence": .9,
        "candidates": [{
            "type": "star", "mount": "Sun/Apollo", "status": "detected",
            "confidence": .9, "ambiguous": True,
        }],
    })
    value["scan_confidence"]["eligible_features"]["markings"] = ["star"]
    result = PalmistryPhase2Engine().analyze(value)
    assert not result["single_feature_signals"]
    assert result["status"] == "insufficient_data"


@pytest.mark.parametrize(("name", "relative", "rule_id"), [
    ("index", "long", "index_long"),
    ("ring", "above_average", "ring_long"),
    ("little", "long", "little_long"),
    ("middle", "long", "middle_long"),
])
def test_different_finger_structures(name, relative, rule_id):
    value = scan_fixture()
    finger(value, name, relative)
    ids = {item["rule_id"] for item in PalmistryPhase2Engine().analyze(value)["single_feature_signals"]}
    assert rule_id in ids


def test_palm_and_thumb_structure_use_phase1_measurements():
    value = scan_fixture()
    value["palm_geometry"]["aspect_ratio"].update({
        "status": "detected", "confidence": .88, "raw_ratio": .95,
    })
    value["thumb"]["spread_angle"].update({
        "status": "detected", "confidence": .86, "raw_degrees": 52,
    })
    ids = {item["rule_id"] for item in PalmistryPhase2Engine().analyze(value)["single_feature_signals"]}
    assert {"palm_broad", "thumb_spread"} <= ids


def test_tip_spacing_and_line_branch_rules_require_reliable_measurements():
    value = scan_fixture()
    finger(value, "index", "long")
    value["fingers"]["index"].update({"spacing_normalized": .22})
    value["fingers"]["index"]["tip_shape"] = {
        "status": "detected", "confidence": .74, "classification": "tapered",
    }
    line(value, "heart_line", branch_candidates=[{"x": .4, "y": .4}])
    ids = {item["rule_id"] for item in PalmistryPhase2Engine().analyze(value)["single_feature_signals"]}
    assert {"index_tip_tapered", "finger_spacing_open", "heart_branches"} <= ids


def test_mount_requires_actual_development_not_texture():
    value = scan_fixture()
    value["mounts"]["Venus"].update({"status": "detected", "confidence": .9, "texture": {"score": .9}})
    value["scan_confidence"]["eligible_features"]["mounts"].append("Venus")
    assert not PalmistryPhase2Engine().analyze(value)["single_feature_signals"]
    mount(value, "Venus", .75)
    assert "venus_developed" in {
        item["rule_id"] for item in PalmistryPhase2Engine().analyze(value)["single_feature_signals"]
    }


def test_union_lines_must_be_explicitly_readable():
    value = scan_fixture()
    value["union_lines"].update({
        "status": "detected", "confidence": .85, "visible_major_line_count": 2, "readable": False,
    })
    assert not PalmistryPhase2Engine().analyze(value)["single_feature_signals"]
    value["union_lines"]["readable"] = True
    assert "union_readable_multiple" in {
        item["rule_id"] for item in PalmistryPhase2Engine().analyze(value)["single_feature_signals"]
    }


def test_minor_marking_cannot_override_multiple_major_signals():
    value = scan_fixture()
    line(value, "heart_line", clarity=.8, break_candidates=[])
    mount(value, "Venus", .75)
    value["special_markings"].update({
        "status": "detected", "confidence": .9,
        "candidates": [{"type": "grille", "mount": "Venus", "status": "detected", "confidence": .9}],
    })
    value["scan_confidence"]["eligible_features"]["markings"] = ["grille"]
    domain = PalmistryPhase2Engine().analyze(value)["domains"]["love_relationships"]
    assert sum(x["weighted_score"] for x in domain["positive_evidence"]) > sum(
        x["weighted_score"] for x in domain["negative_evidence"]
    )
    assert domain["normalized_score"] > 0


def test_evidence_mapping_and_deterministic_golden_regression():
    value = scan_fixture()
    line(value, "head_line", clarity=.8)
    mount(value, "Saturn", .7)
    engine = PalmistryPhase2Engine()
    first = engine.analyze(value)
    second = engine.analyze(copy.deepcopy(value))
    assert first == second
    mapping = first["explainability"]["feature_to_measurement_to_rule_to_conclusion"]
    assert {(item["rule_id"], item["domain"]) for item in mapping} == {
        ("head_clear", "personality"), ("saturn_developed", "personality"),
    }
    assert [(item["rule_id"], item["propagated_confidence"]) for item in first["single_feature_signals"]] == [
        ("head_clear", .82), ("saturn_developed", .81),
    ]
    assert first["domains"]["personality"]["classification"] == "strong"


def test_expanded_unsupported_categories_and_conclusion_evidence_chain():
    value = scan_fixture()
    line(value, "head_line", clarity=.8)
    result = PalmistryPhase2Engine().analyze(value)
    assert result["domains"]["money"]["categories"]["saving_spending"]["status"] == "insufficient_data"
    assert result["domains"]["love_relationships"]["categories"]["trust_tendency"]["classification"] == "insufficient"
    conclusion = result["domains"]["personality"]["categories"]["thinking_style"]["conclusion"]
    assert conclusion["conclusion"]
    assert conclusion["confidence"] > 0
    evidence = conclusion["evidence"][0]
    assert {"feature_path", "raw_measurement", "signal", "source_confidence", "rule_ids"} <= evidence.keys()


def test_cross_domain_commitment_independence_tension_is_structured():
    value = scan_fixture()
    value["union_lines"].update({
        "status": "detected", "confidence": .84, "readable": True,
        "visible_major_line_count": 1,
    })
    value["thumb"]["spread_angle"].update({
        "status": "detected", "confidence": .86, "raw_degrees": 55,
    })
    result = PalmistryPhase2Engine().analyze(value)
    tension = result["cross_domain_tensions"][0]
    assert tension["pattern_version"] == "1.0"
    assert tension["pattern_id"] == "commitment_independence_tension"
    assert {item["domain"] for item in tension["evidence"]} == {"marriage", "personality"}


def test_narrator_is_grounded_and_has_no_forbidden_claims():
    value = scan_fixture()
    line(value, "life_line", continuity=.9)
    result = PalmistryPhase2Engine().analyze(value)
    narration = result["narration"]
    assert narration["grounded_only"] is True
    assert set(narration["sections"]) == {
        "Overall Palm Profile", "Personality", "Emotional & Relationship Nature",
        "Love/Marriage", "Career", "Money", "Strengths", "Challenges",
        "Important Patterns", "Traditional Palmistry Guidance",
        "Confidence & Limitations",
    }
    allowed = {item["interpretation"] for item in result["single_feature_signals"]}
    for statements in narration["sections"].values():
        for statement in statements:
            assert (
                statement["text"] in allowed
                or statement["source"] in {"cross_domain_tensions", "disclaimer"}
            )
    assert "not a scientific assessment" in narration["disclaimer"]
    text = (narration["text"] + narration["disclaimer"]).lower()
    for forbidden in ("you will die", "death date", "guaranteed wealth", "will become rich", "exactly on"):
        assert forbidden not in text


def test_api_json_only_invalid_insufficient_and_success():
    app = Flask(__name__)
    app.register_blueprint(create_palmistry_phase2_blueprint())
    client = app.test_client()
    multipart = client.post(
        "/api/palm-reading/interpret",
        data={"image": (io.BytesIO(b"pixels"), "palm.jpg")},
        content_type="multipart/form-data",
    )
    assert multipart.status_code == 415
    assert multipart.get_json()["error"]["code"] == "json_only"
    raw = client.post("/api/palm-reading/interpret", json={"image": "base64"})
    assert raw.status_code == 415
    mismatch = client.post("/api/palm-reading/interpret", json={"palm_scan_result": {"schema_version": "9"}})
    assert mismatch.status_code == 422
    insufficient = client.post("/api/palm-reading/interpret", json={"palm_scan_result": empty_result(scan_id="empty")})
    assert insufficient.status_code == 422
    value = scan_fixture()
    line(value, "head_line", clarity=.8)
    success = client.post("/api/palm-reading/interpret", json={"palm_scan_result": value})
    assert success.status_code == 200
    assert success.get_json()["metadata"]["image_or_artifact_consumed"] is False
