"""Unit tests use annotation arrays only; no real data or accuracy claims."""
from __future__ import annotations

import json
import hashlib

import cv2
import numpy as np
import pytest

from vedic.palm_scan.dataset import (
    LINE_CLASSES,
    MASK_CLASSES,
    MOUNT_CLASSES,
    create_manifest,
    calibrate_thresholds_numpy,
    dataset_statistics,
    grouped_split,
    line_supervision_weights,
    rasterize_sample,
    semantic_metrics_numpy,
    validate_local_assets,
    validate_manifest,
)
from vedic.palm_scan.semantic_verifier import OpenCVDNNSemanticLineVerifier


def sample(image_id="image-1", subject_id="person-1", split="unassigned"):
    polygon = [
        {"x": .2, "y": .2}, {"x": .8, "y": .2},
        {"x": .8, "y": .9}, {"x": .2, "y": .9},
    ]
    lines = {
        name: {"readability": "unknown", "confidence": 0.0, "path": []}
        for name in LINE_CLASSES
    }
    lines["heart_line"] = {
        "readability": "clear", "confidence": .9,
        "path": [{"x": .25, "y": .5}, {"x": .75, "y": .5}],
    }
    return {
        "subject_id": subject_id,
        "split": split,
        "handedness": "right",
        "image": {
            "id": image_id,
            "path": f"images/{image_id}.jpg",
            "width": 640,
            "height": 800,
            "sha256": "0" * 64,
            "license": "test-only",
            "consent": {
                "status": "granted",
                "allowed_uses": ["annotation", "model_training", "evaluation"],
                "record_id": "test-consent-record",
                "recorded_at": "2026-08-18T00:00:00Z",
            },
            "source": "unit-test",
        },
        "annotations": {
            "coordinate_space": "normalized_0_1",
            "landmarks": [{
                "id": 0, "name": "wrist", "normalized_x": .5,
                "normalized_y": .85, "confidence": .9,
            }],
            "segmentations": {
                "hand": {"polygon": polygon, "confidence": .9},
                "palm": {"polygon": polygon, "confidence": .9},
            },
            "major_lines": lines,
            "mounts": {
                name: {"polygon": polygon, "confidence": .7}
                for name in MOUNT_CLASSES
            },
            "markings": [],
        },
        "capture_quality": {
            "overall": "good", "lighting": "good", "focus": "good",
            "occlusion": "good", "framing": "good",
        },
        "review": {
            "status": "approved", "annotator_id": "annotator-a",
            "reviewer_id": "reviewer-b",
        },
        "provenance": {
            "created_at": "2026-08-18T00:00:00Z",
            "annotation_tool": "unit-test",
            "annotation_version": "1",
        },
    }


def manifest_with(*samples):
    manifest = create_manifest("unit-test")
    manifest["samples"] = list(samples)
    return manifest


def test_manifest_contract_and_coordinate_bounds():
    manifest = manifest_with(sample())
    assert validate_manifest(manifest) == []
    manifest["samples"][0]["annotations"]["landmarks"][0]["normalized_x"] = 1.01
    assert any("within 0..1" in error for error in validate_manifest(manifest))


def test_training_consent_is_structured_and_withdrawal_is_enforced(tmp_path):
    value = sample()
    value["image"]["consent"]["status"] = "withdrawn"
    assert validate_manifest(manifest_with(value)) == []
    errors = validate_local_assets(
        manifest_with(value), tmp_path, require_training_consent=True
    )
    assert any("does not authorize model_training" in error for error in errors)


@pytest.mark.parametrize("unsafe", ["../secret.jpg", "/tmp/image.jpg", "images\\palm.jpg", "C:/palm.jpg"])
def test_manifest_rejects_unsafe_image_paths(unsafe):
    value = sample()
    value["image"]["path"] = unsafe
    assert any(".image.path" in error for error in validate_manifest(manifest_with(value)))


@pytest.mark.parametrize("unsafe", ["../escape", "folder/name", "C:drive", "has space"])
def test_manifest_rejects_unsafe_image_ids_used_as_export_names(unsafe):
    value = sample()
    value["image"]["id"] = unsafe
    assert any(".image.id" in error for error in validate_manifest(manifest_with(value)))


def test_grouped_split_is_deterministic_and_has_no_identity_leakage():
    samples = [
        sample(f"image-{person}-{capture}", f"person-{person}")
        for person in range(10) for capture in range(2)
    ]
    source = manifest_with(*samples)
    first = grouped_split(source, seed=19)
    second = grouped_split(source, seed=19)
    assert first == second
    subject_splits = {}
    for item in first["samples"]:
        subject_splits.setdefault(item["subject_id"], set()).add(item["split"])
    assert all(len(splits) == 1 for splits in subject_splits.values())
    assert validate_manifest(first) == []


def test_raster_channel_order_unknown_and_faint_handling():
    value = sample()
    value["annotations"]["major_lines"]["head_line"] = {
        "readability": "faint", "confidence": .4,
        "path": [{"x": .25, "y": .6}, {"x": .75, "y": .6}],
    }
    targets, names = rasterize_sample(value, (64, 80))
    assert names == MASK_CLASSES
    assert targets.shape == (9, 64, 80)
    assert np.count_nonzero(targets[0]) > 0
    assert np.count_nonzero(targets[1]) > 0
    assert np.count_nonzero(targets[2]) == 0
    assert np.count_nonzero(targets[7]) >= np.count_nonzero(targets[8])


def test_statistics_never_claim_accuracy():
    stats = dataset_statistics(manifest_with(sample()))
    assert stats["sample_count"] == 1
    assert stats["subject_count"] == 1
    assert stats["line_readability"]["heart_line"]["clear"] == 1
    assert stats["accuracy_claim"] is None


def test_readability_controls_supervision_without_changing_raster_api():
    value = sample()
    value["annotations"]["major_lines"]["head_line"] = {
        "readability": "faint", "confidence": .5,
        "path": [{"x": .2, "y": .6}, {"x": .8, "y": .6}],
    }
    value["annotations"]["major_lines"]["life_line"] = {
        "readability": "occluded", "confidence": .5,
        "path": [{"x": .3, "y": .3}, {"x": .4, "y": .7}],
    }
    weights = line_supervision_weights(value, faint_weight=.25)
    assert weights[0] == 1
    assert weights[1] == .25
    assert weights[2] == 0
    assert weights[3] == 0  # unknown
    targets, names = rasterize_sample(value, (32, 32))
    assert targets.shape[0] == len(names)


def test_numpy_metrics_and_calibration_skip_unsupervised_classes():
    probabilities = np.zeros((1, len(LINE_CLASSES), 8, 8), np.float32)
    targets = np.zeros_like(probabilities)
    supervision = np.zeros((1, len(LINE_CLASSES)), np.float32)
    calibration = calibrate_thresholds_numpy(
        probabilities, targets, supervision
    )
    thresholds = {name: .5 for name in LINE_CLASSES}
    metrics = semantic_metrics_numpy(
        probabilities, targets, supervision, thresholds
    )
    assert calibration["heart_line"] == {
        "status": "not_evaluated", "threshold": None,
    }
    assert metrics["heart_line"]["status"] == "not_evaluated"
    assert metrics["heart_line"]["iou"] is None


def _write_image(path, shape=(12, 10), value=255):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full((*shape, 3), value, np.uint8)
    assert cv2.imwrite(str(path), image)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_mask_path_requires_root_and_merges_binary_mask(tmp_path):
    value = sample()
    mask_path = tmp_path / "masks" / "heart.png"
    mask_path.parent.mkdir(parents=True)
    mask = np.zeros((800, 640), np.uint8)
    mask[100:200, 100:200] = 255
    assert cv2.imwrite(str(mask_path), mask)
    line = value["annotations"]["major_lines"]["heart_line"]
    line["mask_path"] = "masks/heart.png"
    line["mask_sha256"] = hashlib.sha256(mask_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="explicit asset_root"):
        rasterize_sample(value, (64, 64))
    targets, _ = rasterize_sample(value, (64, 64), asset_root=tmp_path)
    assert targets[0, 32, 32] == 1  # normalized path
    assert targets[0, 12, 15] == 1  # external binary mask


def test_mask_path_traversal_is_rejected():
    value = sample()
    line = value["annotations"]["major_lines"]["heart_line"]
    line["mask_path"] = "../heart.png"
    line["mask_sha256"] = "a" * 64
    assert any("mask_path" in error for error in validate_manifest(manifest_with(value)))


def test_local_asset_integrity_checks_hash_and_dimensions(tmp_path):
    value = sample()
    image_path = tmp_path / value["image"]["path"]
    digest = _write_image(image_path)
    value["image"].update({"width": 10, "height": 12, "sha256": digest})
    assert validate_local_assets(manifest_with(value), tmp_path) == []
    value["image"]["sha256"] = "f" * 64
    assert any("sha256 does not match" in error for error in validate_local_assets(
        manifest_with(value), tmp_path
    ))
    value["image"]["sha256"] = digest
    value["image"]["width"] = 11
    assert any("dimensions" in error for error in validate_local_assets(
        manifest_with(value), tmp_path
    ))


def test_local_mask_integrity_checks_hash_and_dimensions(tmp_path):
    value = sample()
    image_path = tmp_path / value["image"]["path"]
    image_digest = _write_image(image_path)
    value["image"].update({"width": 10, "height": 12, "sha256": image_digest})
    mask_path = tmp_path / "masks" / "heart.png"
    mask_digest = _write_image(mask_path, value=1)
    line = value["annotations"]["major_lines"]["heart_line"]
    line.update({"mask_path": "masks/heart.png", "mask_sha256": mask_digest})
    assert validate_local_assets(manifest_with(value), tmp_path) == []
    line["mask_sha256"] = "e" * 64
    assert any("mask_sha256" in error for error in validate_local_assets(
        manifest_with(value), tmp_path
    ))
    line["mask_sha256"] = mask_digest
    _write_image(mask_path, shape=(13, 10), value=1)
    line["mask_sha256"] = hashlib.sha256(mask_path.read_bytes()).hexdigest()
    assert any("mask_path dimensions" in error for error in validate_local_assets(
        manifest_with(value), tmp_path
    ))


def test_offline_asset_preflight_rejects_remote_samples(tmp_path):
    value = sample()
    value["image"].pop("path")
    value["image"]["uri"] = "https://controlled.example/palm.jpg"
    errors = validate_local_assets(
        manifest_with(value), tmp_path, reject_remote=True
    )
    assert any("materialize" in error for error in errors)


class FakeNet:
    def setInput(self, blob):
        assert blob.shape == (1, 3, 64, 64)

    def forward(self):
        output = np.zeros((1, len(LINE_CLASSES), 64, 64), np.float32)
        output[:, 0, 30:35, 12:52] = .95
        return output


def _model_files(tmp_path):
    model = tmp_path / "semantic.onnx"
    model.write_bytes(b"test-placeholder")
    metadata = {
        "trained": True,
        "model_version": "unit-test/1",
        "class_order": list(LINE_CLASSES),
        "preprocessing_version": "palm_semantic_rgb/1.0",
        "output_activation": "probabilities",
        "dataset_manifest_sha256": "a" * 64,
        "thresholds": {name: .6 for name in LINE_CLASSES},
        "calibration_by_class": {
            name: {
                "status": "evaluated",
                "threshold": .6,
                "supervised_examples": 2,
            }
            for name in LINE_CLASSES
        },
        "input": {
            "width": 64, "height": 64, "channels": 3, "color_order": "RGB",
        },
        "normalization": {
            "scale": 1.0 / 255.0,
            "mean": [.485, .456, .406],
            "std": [.229, .224, .225],
        },
        "class_weights": {name: 1.0 for name in LINE_CLASSES},
        "supervision_policy": {
            "clear": 1.0, "faint": .35, "unknown": 0.0, "occluded": 0.0,
        },
    }
    model.with_suffix(".metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return model


def test_fake_opencv_inference_assigns_overlap_without_coordinates(tmp_path):
    verifier = OpenCVDNNSemanticLineVerifier(
        _model_files(tmp_path),
        input_size=(64, 64),
        net_loader=lambda _: FakeNet(),
        overlap_threshold=.3,
    )
    candidate = {
        "id": "candidate-1", "confidence": .9,
        "path": [{"x": .2, "y": .5}, {"x": .8, "y": .5}],
    }
    assignments = verifier.verify(
        [candidate],
        {
            "processed_rgb": np.full((80, 80, 3), 128, np.uint8),
            "palm_mask": np.full((80, 80), 255, np.uint8),
            "quality": {"usable": True, "score": .9},
        },
    )
    assert assignments["heart_line"]["candidate_id"] == "candidate-1"
    assert set(assignments["heart_line"]) == {"candidate_id", "confidence"}
    assert "path" not in str(assignments)
    assert verifier.last_evidence["model_version"] == "unit-test/1"


def test_uncalibrated_class_cannot_be_assigned(tmp_path):
    model = _model_files(tmp_path)
    metadata_path = model.with_suffix(".metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["calibration_by_class"]["heart_line"] = {
        "status": "not_evaluated", "threshold": None,
    }
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    verifier = OpenCVDNNSemanticLineVerifier(
        model, input_size=(64, 64), net_loader=lambda _: FakeNet(),
        overlap_threshold=.3,
    )
    result = verifier.verify(
        [{
            "id": "candidate-1", "confidence": .9,
            "path": [{"x": .2, "y": .5}, {"x": .8, "y": .5}],
        }],
        {
            "processed_rgb": np.full((64, 64, 3), 128, np.uint8),
            "palm_mask": np.full((64, 64), 255, np.uint8),
            "quality": {"usable": True, "score": .9},
        },
    )
    assert "heart_line" not in result


def test_absent_model_is_unknown_safe(tmp_path):
    verifier = OpenCVDNNSemanticLineVerifier(tmp_path / "missing.onnx")
    assert verifier.verify([], {}) == {}
    assert verifier.last_evidence["status"] == "model_unavailable"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("threshold", 1.5),
        ("normalization", [0.0, 0.0, 0.0]),
        ("manifest_hash", "invalid"),
        ("model_version", ""),
    ],
)
def test_incompatible_model_metadata_is_rejected(tmp_path, field, value):
    model = _model_files(tmp_path)
    metadata_path = model.with_suffix(".metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if field == "threshold":
        metadata["thresholds"]["heart_line"] = value
    elif field == "normalization":
        metadata["normalization"]["mean"] = value
    elif field == "manifest_hash":
        metadata["dataset_manifest_sha256"] = value
    else:
        metadata["model_version"] = value
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    verifier = OpenCVDNNSemanticLineVerifier(
        model, net_loader=lambda _: pytest.fail("invalid metadata loaded a net")
    )
    assert verifier.net is None
    assert verifier.last_evidence["status"] == "model_unavailable"


def test_constructor_input_size_cannot_override_model_metadata(tmp_path):
    verifier = OpenCVDNNSemanticLineVerifier(
        _model_files(tmp_path),
        input_size=(128, 128),
        net_loader=lambda _: pytest.fail("mismatched model loaded"),
    )
    assert verifier.net is None


def test_quality_disagreement_returns_no_assignment(tmp_path):
    verifier = OpenCVDNNSemanticLineVerifier(
        _model_files(tmp_path), input_size=(64, 64), net_loader=lambda _: FakeNet()
    )
    result = verifier.verify(
        [{"id": "other", "confidence": .9,
          "path": [{"x": .2, "y": .8}, {"x": .8, "y": .8}]}],
        {
            "processed_rgb": np.zeros((64, 64, 3), np.uint8),
            "palm_mask": np.ones((64, 64), np.uint8),
            "quality": {"usable": True, "score": .9},
        },
    )
    assert result == {}
