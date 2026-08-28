"""Fate Line image-first detector unit tests."""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from vedic.palm_scan.detectors import LANDMARK_NAMES
from vedic.palm_scan.fate_line_detector import FateLineDetector, MIN_FATE_PATH_POINTS


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


def _rgb_with_vertical_crease(x_norm=0.50, y0=0.35, y1=0.82, width=640, height=800):
    rgb = np.full((height, width, 3), 170, dtype=np.uint8)
    x = int(x_norm * width)
    cv2.line(rgb, (x, int(y0 * height)), (x, int(y1 * height)), (40, 40, 40), 2, cv2.LINE_AA)
    palm_mask = np.ones((height, width), np.uint8) * 255
    return rgb, palm_mask


def _context(rgb, palm_mask):
    return {
        "landmarks": _landmarks(),
        "palm_geometry": {},
        "processed_rgb": rgb,
        "palm_mask": palm_mask,
    }


def _candidate(cid, path, *, norm_len=None, conf=0.6, continuity=0.9):
    return {
        "id": cid,
        "path": path,
        "normalized_length": norm_len if norm_len is not None else _path_len(path),
        "confidence": conf,
        "continuity": continuity,
        "measurements": {"continuity": continuity},
    }


def _path_len(path):
    total = 0.0
    for i in range(1, len(path)):
        total += ((path[i]["x"] - path[i - 1]["x"]) ** 2 + (path[i]["y"] - path[i - 1]["y"]) ** 2) ** 0.5
    return total


def _vertical_path(x=0.50, y0=0.35, y1=0.82, points=8):
    return [
        {"x": x, "y": round(y0 + (y1 - y0) * i / (points - 1), 4)}
        for i in range(points)
    ]


@pytest.fixture
def detector():
    return FateLineDetector()


def test_short_vertical_not_auto_fate_line(detector):
    rgb, mask = _rgb_with_vertical_crease(y0=0.60, y1=0.68)
    short = _vertical_path(y0=0.60, y1=0.68, points=4)
    out = detector.detect(
        [_candidate("c1", short, norm_len=0.08, continuity=1.0)],
        _context(rgb, mask),
    )
    fate = out["major_line"]
    assert fate["status"] in {"insufficient_evidence", "not_detected"}
    assert fate["validity"] != "detected"


def test_strong_long_image_supported_detected(detector):
    rgb, mask = _rgb_with_vertical_crease()
    long_path = _vertical_path()
    out = detector.detect([_candidate("c1", long_path, norm_len=0.47, continuity=0.95)], _context(rgb, mask))
    fate = out["major_line"]
    assert fate["status"] == "detected"
    assert len(fate["path"]) >= MIN_FATE_PATH_POINTS
    assert (fate.get("image_support") or 0) > 0.4


def test_multiple_vertical_uses_combined_evidence(detector):
    rgb, mask = _rgb_with_vertical_crease()
    rgb2 = rgb.copy()
    cv2.line(rgb2, (int(0.42 * 640), 200), (int(0.42 * 640), 500), (55, 55, 55), 1)
    weak = _vertical_path(x=0.42, y0=0.25, y1=0.62, points=6)
    strong = _vertical_path(x=0.50, y0=0.30, y1=0.85, points=10)
    out = detector.detect(
        [
            _candidate("weak", weak, norm_len=0.37, conf=0.45),
            _candidate("strong", strong, norm_len=0.55, conf=0.72),
        ],
        _context(rgb, mask),
    )
    selected = out["debug"]["selected_candidate_ids"]
    assert "strong" in selected or out["major_line"]["source_candidate_id"] == "strong"


def test_high_continuity_short_path_insufficient(detector):
    rgb, mask = _rgb_with_vertical_crease(y0=0.55, y1=0.62)
    path = _vertical_path(y0=0.55, y1=0.62, points=4)
    out = detector.detect(
        [_candidate("frag", path, norm_len=0.07, continuity=1.0)],
        _context(rgb, mask),
    )
    assert out["major_line"]["status"] in {"insufficient_evidence", "not_detected"}
    audit = out["debug"]["candidate_audit"][0]
    assert "high_continuity_but_fragment" in audit["rejection_reasons"] or audit["rejection_reasons"]


def test_compatible_fragments_stitched(detector):
    height, width = 800, 640
    rgb = np.full((height, width, 3), 170, dtype=np.uint8)
    x = int(0.50 * width)
    cv2.line(rgb, (x, 280), (x, 420), (35, 35, 35), 2)
    cv2.line(rgb, (x, 450), (x, 620), (35, 35, 35), 2)
    cv2.line(rgb, (x, 420), (x, 450), (35, 35, 35), 2)
    mask = np.ones((height, width), np.uint8) * 255
    top = _vertical_path(y0=0.35, y1=0.52, points=5)
    bottom = _vertical_path(y0=0.56, y1=0.78, points=5)
    out = detector.detect(
        [
            _candidate("seg_a", top, norm_len=0.17),
            _candidate("seg_b", bottom, norm_len=0.22),
        ],
        _context(rgb, mask),
    )
    debug = out["debug"]
    if debug.get("stitching_applied"):
        assert len(debug["selected_candidate_ids"]) >= 2
    else:
        assert out["major_line"]["status"] in {"detected", "insufficient_evidence", "ambiguous"}


def test_incompatible_fragments_not_stitched(detector):
    rgb, mask = _rgb_with_vertical_crease()
    a = _vertical_path(x=0.35, y0=0.30, y1=0.50, points=4)
    b = _vertical_path(x=0.65, y0=0.55, y1=0.80, points=4)
    out = detector.detect(
        [_candidate("a", a, norm_len=0.20), _candidate("b", b, norm_len=0.25)],
        _context(rgb, mask),
    )
    assert "+" not in str(out["major_line"].get("source_candidate_id") or "")


def _rgb_with_two_vertical_creases(
    *,
    center_x=0.50,
    edge_x=0.63,
    width=640,
    height=800,
):
    rgb = np.full((height, width, 3), 170, dtype=np.uint8)
    y0, y1 = int(0.34 * height), int(0.84 * height)
    cv2.line(
        rgb,
        (int(edge_x * width), y0),
        (int(edge_x * width), y1),
        (25, 25, 25),
        4,
        cv2.LINE_AA,
    )
    cv2.line(
        rgb,
        (int(center_x * width), y0),
        (int(center_x * width), y1),
        (48, 48, 48),
        2,
        cv2.LINE_AA,
    )
    palm_mask = np.ones((height, width), np.uint8) * 255
    return rgb, palm_mask


def test_empty_candidates_vertical_crease_corridor(detector):
    rgb, mask = _rgb_with_vertical_crease()
    out = detector.detect([], _context(rgb, mask))
    assert out["debug"]["pipeline_revision"] == "image_first_fate_line_detector/v8.2"
    assert out["major_line"]["pipeline_revision"] == "image_first_fate_line_detector/v8.2"
    assert out["debug"]["audit_count"] > 0
    assert out["major_line"]["status"] in {"detected", "insufficient_evidence", "ambiguous", "not_detected"}


def test_prefers_center_fate_axis_over_stronger_edge_crease(detector):
    rgb, mask = _rgb_with_two_vertical_creases()
    edge = _vertical_path(x=0.63, y0=0.34, y1=0.84, points=8)
    center = _vertical_path(x=0.50, y0=0.34, y1=0.84, points=8)
    out = detector.detect(
        [
            _candidate("edge", edge, norm_len=0.50, conf=0.92),
            _candidate("center", center, norm_len=0.48, conf=0.62),
        ],
        _context(rgb, mask),
    )
    path = out["major_line"].get("path") or []
    assert path
    mean_x = sum(float(p["x"]) for p in path) / len(path)
    assert mean_x < 0.56
    assert float(out["major_line"].get("fate_axis_score") or 0.0) >= 0.52


def test_no_plausible_fate_line_not_detected(detector):
    rgb = np.full((800, 640, 3), 180, dtype=np.uint8)
    mask = np.ones((800, 640), np.uint8) * 255
    horiz = [{"x": 0.2 + 0.1 * i, "y": 0.55} for i in range(6)]
    out = detector.detect([_candidate("h", horiz, norm_len=0.40)], _context(rgb, mask))
    assert out["major_line"]["status"] in {"not_detected", "insufficient_evidence"}


def test_poor_image_support_rejected(detector):
    rgb = np.full((800, 640, 3), 180, dtype=np.uint8)
    mask = np.ones((800, 640), np.uint8) * 255
    path = _vertical_path()
    out = detector.detect([_candidate("ghost", path, norm_len=0.50, conf=0.9)], _context(rgb, mask))
    assert out["major_line"]["status"] in {"not_detected", "insufficient_evidence"}
    assert (out["major_line"].get("image_support") or 0) < 0.35


def test_unusual_geometry_still_eligible(detector):
    rgb, mask = _rgb_with_vertical_crease()
    curved = [
        {"x": 0.48, "y": 0.35},
        {"x": 0.52, "y": 0.45},
        {"x": 0.49, "y": 0.55},
        {"x": 0.51, "y": 0.65},
        {"x": 0.50, "y": 0.75},
        {"x": 0.50, "y": 0.82},
    ]
    out = detector.detect([_candidate("curved", curved, norm_len=0.47)], _context(rgb, mask))
    audit = out["debug"]["candidate_audit"][0]
    assert "poor_image_support" not in audit.get("rejection_reasons", []) or audit["final_score"] > 0


def test_confidence_not_high_from_orientation_alone(detector):
    rgb = np.full((800, 640, 3), 180, dtype=np.uint8)
    mask = np.ones((800, 640), np.uint8) * 255
    path = _vertical_path(y0=0.40, y1=0.85, points=6)
    out = detector.detect([_candidate("v", path, norm_len=0.45, conf=0.8)], _context(rgb, mask))
    assert out["major_line"]["confidence"] < 0.65


def test_branches_forks_not_available(detector):
    rgb, mask = _rgb_with_vertical_crease()
    path = _vertical_path()
    cand = _candidate("c1", path, norm_len=0.47)
    cand["branches"] = [{"x": 0.5, "y": 0.5}] * 5
    cand["forks"] = cand["branches"]
    out = detector.detect([cand], _context(rgb, mask))
    fate = out["major_line"]
    assert fate.get("branches") == []
    assert fate.get("forks") == []
    assert fate["measurements"]["validated_branch_status"] == "not_available"


def test_not_detected_still_reports_best_metrics(detector):
    rgb = np.full((800, 640, 3), 180, dtype=np.uint8)
    mask = np.ones((800, 640), np.uint8) * 255
    short = _vertical_path(y0=0.55, y1=0.62, points=3)
    out = detector.detect(
        [_candidate("tiny", short, norm_len=0.05, continuity=1.0)],
        _context(rgb, mask),
    )
    fate = out["major_line"]
    assert fate["status"] in {"not_detected", "insufficient_evidence"}
    assert fate.get("image_support") is not None or fate.get("path")


def test_short_seed_extends_along_visible_crease(detector):
    rgb, mask = _rgb_with_vertical_crease()
    short = _vertical_path(y0=0.48, y1=0.58, points=5)
    out = detector.detect(
        [_candidate("mid", short, norm_len=0.10, continuity=0.95)],
        _context(rgb, mask),
    )
    fate = out["major_line"]
    assert len(fate.get("path") or []) > len(short)
    assert out["debug"].get("path_extension_applied") is True
    assert fate["detection_method"] == "image_first_fate_line_detector"
