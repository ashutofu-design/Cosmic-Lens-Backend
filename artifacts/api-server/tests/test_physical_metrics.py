"""Tests for anatomical px→mm scaling on palm scan output."""
from __future__ import annotations

from vedic.palm_scan.physical_metrics import (
    attach_scan_physical_metrics,
    compute_px_to_mm_ratio,
    path_arc_length_mm,
)


def _landmarks():
    return [
        {"id": 0, "x": 0.50, "y": 0.86},
        {"id": 5, "x": 0.36, "y": 0.52},
        {"id": 17, "x": 0.75, "y": 0.57},
    ]


def test_px_to_mm_ratio_uses_index_pinky_anchor():
    scale = compute_px_to_mm_ratio(_landmarks(), 640, 800)
    assert scale["anchor_landmarks"] == [5, 17]
    assert scale["reference_palm_width_mm"] == 75.0
    assert scale["px_to_mm_ratio"] > 0


def test_attach_scan_physical_metrics_adds_length_mm():
    path = [{"x": 0.48, "y": 0.30}, {"x": 0.50, "y": 0.55}, {"x": 0.51, "y": 0.78}]
    result = {
        "landmarks": _landmarks(),
        "metadata": {"dimensions": {"width_px": 640, "height_px": 800}},
        "palm_geometry": {"width": {"confidence": 0.8}},
        "major_lines": {
            "fate_line": {
                "detected": True,
                "confidence": 0.7,
                "path": path,
                "start_point": path[0],
                "end_point": path[-1],
            },
            "head_line": {
                "detected": True,
                "confidence": 0.6,
                "path": [{"x": 0.40, "y": 0.45}, {"x": 0.62, "y": 0.48}],
            },
        },
    }
    attach_scan_physical_metrics(result)
    fate = result["major_lines"]["fate_line"]
    assert fate.get("length_mm") is not None
    assert fate["length_mm"] > 0
    assert fate["measurements"]["distance_to_wrist_mm"] is not None
    gaps = fate["measurements"].get("intersection_gaps_mm") or {}
    assert "gap_to_head_line_mm" in gaps
    assert result["metadata"]["physical_scale"]["px_to_mm_ratio"] > 0


def test_path_arc_length_mm_scales_with_ratio():
    path = [{"x": 0.0, "y": 0.0}, {"x": 0.1, "y": 0.0}]
    mm = path_arc_length_mm(path, 0.5, 100, 100)
    assert mm == 5.0
