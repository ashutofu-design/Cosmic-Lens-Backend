"""Tests for landmark-normalized fate line graph tracing."""
from __future__ import annotations

import cv2
import numpy as np

from vedic.palm_scan.detectors import LANDMARK_NAMES
from vedic.palm_scan.fate_line_normalize import (
    proportional_fate_corridor,
    trace_fate_line_normalized,
    wrist_middle_rotation_degrees,
)
from vedic.palm_scan.fate_line_detector import FateLineDetector


def _landmarks():
    points = [
        (.50, .86), (.40, .71), (.32, .61), (.24, .51), (.16, .42),
        (.36, .52), (.34, .38), (.33, .24), (.32, .09),
        (.50, .49), (.50, .32), (.50, .17), (.50, .05),
        (.63, .52), (.65, .36), (.66, .22), (.67, .09),
        (.75, .57), (.79, .44), (.82, .32), (.85, .21),
    ]
    return [
        {"id": i, "name": LANDMARK_NAMES[i], "x": x, "y": y}
        for i, (x, y) in enumerate(points)
    ]


def _tilted_palm_with_center_crease():
    rgb = np.full((800, 640, 3), 175, dtype=np.uint8)
    # Center vertical crease
    cv2.line(rgb, (320, 280), (320, 660), (45, 45, 45), 2, cv2.LINE_AA)
    # Stronger off-center decoy
    cv2.line(rgb, (400, 290), (405, 650), (30, 30, 30), 3, cv2.LINE_AA)
    mask = np.ones((800, 640), np.uint8) * 255
    return rgb, mask


def test_proportional_corridor_scales_with_landmarks():
    corridor = proportional_fate_corridor(_landmarks())
    assert corridor["x_half"] > 0.04
    assert corridor["y_bottom"] > corridor["y_top"]


def test_wrist_middle_rotation_is_finite():
    angle = wrist_middle_rotation_degrees(_landmarks())
    assert abs(angle) < 90.0


def test_graph_trace_prefers_center_on_tilted_palm():
    rgb, mask = _tilted_palm_with_center_crease()
    out = trace_fate_line_normalized(rgb, mask, _landmarks())
    assert out is not None
    path = out["path"]
    assert len(path) >= 4
    mean_x = sum(p["x"] for p in path) / len(path)
    assert mean_x < 0.58
    assert out["graph_trace"] is True
    assert float(out.get("coverage_span") or 0) >= 0.28


def test_detector_v8_includes_graph_trace_and_remap():
    rgb, mask = _tilted_palm_with_center_crease()
    detector = FateLineDetector()
    result = detector.detect(
        [],
        {
            "landmarks": _landmarks(),
            "palm_geometry": {},
            "processed_rgb": rgb,
            "palm_mask": mask,
        },
    )
    assert result["debug"]["pipeline_revision"] == "image_first_fate_line_detector/v8.2"
    audit_sources = [
        entry.get("source")
        for entry in result["debug"]["candidate_audit"]
    ]
    assert "normalized_affine_graph_dijkstra" in audit_sources


def test_inverse_remap_metadata_on_trace():
    rgb, mask = _tilted_palm_with_center_crease()
    out = trace_fate_line_normalized(rgb, mask, _landmarks())
    assert out is not None
    norm = out["normalization"]
    assert norm.get("coordinate_frame") == "original_image_normalized"
    assert norm.get("dynamic_graph_endpoints") is True
    assert float(norm.get("inverse_remap_max_error_px", 99)) < 2.0
