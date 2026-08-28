"""Tests for image-first life line fallback tracing."""
from __future__ import annotations

import cv2
import numpy as np

from vedic.palm_scan.detectors import LANDMARK_NAMES
from vedic.palm_scan.life_line_trace import trace_life_line_fallback


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


def _palm_with_life_arc():
    rgb = np.full((800, 640, 3), 180, dtype=np.uint8)
    # Thumb-side life-like arc
    pts = np.array([[220, 620], [210, 520], [205, 420], [215, 320], [240, 240]], np.int32)
    cv2.polylines(rgb, [pts], False, (40, 40, 40), 2, cv2.LINE_AA)
    mask = np.ones((800, 640), np.uint8) * 255
    return rgb, mask


def test_life_line_fallback_returns_path():
    rgb, mask = _palm_with_life_arc()
    out = trace_life_line_fallback(_landmarks(), rgb, mask)
    assert out is not None
    assert len(out["path"]) >= 4
    assert out["detection_method"] == "image_first_life_line_trace"
    assert out["confidence"] > 0
