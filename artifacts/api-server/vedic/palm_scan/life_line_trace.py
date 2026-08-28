"""Image-first Life Line fallback when crease verifier assigns nothing."""
from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

from .detectors import confidence_band


MIN_LIFE_PATH_POINTS = 4
DETECTION_METHOD = "image_first_life_line_trace"


def _landmarks_by_id(landmarks: list[dict]) -> dict[int, dict]:
    return {
        int(p["id"]): p
        for p in landmarks
        if isinstance(p, dict) and "id" in p
    }


def _dedupe_path(path: list[dict]) -> list[dict]:
    if not path:
        return []
    out = [path[0]]
    for point in path[1:]:
        last = out[-1]
        if math.hypot(point["x"] - last["x"], point["y"] - last["y"]) < 0.0025:
            continue
        out.append(point)
    return out


def _path_length(path: list[dict]) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(path)):
        dx = path[i]["x"] - path[i - 1]["x"]
        dy = path[i]["y"] - path[i - 1]["y"]
        total += math.hypot(dx, dy)
    return float(total)


def _build_crease_response(rgb: np.ndarray, palm_mask: np.ndarray) -> tuple[np.ndarray, float]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    enhanced = cv2.createCLAHE(2.0, (8, 8)).apply(gray)
    dark = cv2.morphologyEx(
        enhanced,
        cv2.MORPH_BLACKHAT,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
    )
    palm_pixels = dark[palm_mask > 0]
    threshold = max(10, int(np.percentile(palm_pixels, 68))) if palm_pixels.size else 255
    return dark, float(threshold)


def trace_life_line_fallback(
    landmarks: list[dict],
    processed_rgb: np.ndarray,
    palm_mask: np.ndarray,
    *,
    crease_masks: dict[str, np.ndarray] | None = None,
) -> dict[str, Any] | None:
    """Trace thumb-side life arc from web toward wrist on visible crease response."""
    if len(landmarks) < 21:
        return None
    by_id = _landmarks_by_id(landmarks)
    wrist = by_id.get(0)
    thumb = by_id.get(2)
    index = by_id.get(5)
    middle = by_id.get(9)
    ring = by_id.get(13)
    pinky = by_id.get(17)
    if not all([wrist, thumb, index, middle, ring, pinky]):
        return None

    rgb = np.ascontiguousarray(processed_rgb)
    mask = np.ascontiguousarray(palm_mask, dtype=np.uint8)
    height, width = rgb.shape[:2]
    enhanced, threshold = _build_crease_response(rgb, mask)

    skeleton = None
    if crease_masks:
        binary = crease_masks.get("blackhat_adaptive")
        if binary is not None:
            binary = np.ascontiguousarray(binary, dtype=np.uint8)
            if hasattr(cv2, "ximgproc"):
                skeleton = cv2.ximgproc.thinning(binary)
            else:
                skeleton = np.uint8(binary > 0) * 255

    palm_cx = (
        float(wrist["x"]) + float(index["x"]) + float(middle["x"]) + float(pinky["x"])
    ) / 4.0
    thumb_side = 1.0 if float(thumb["x"]) >= palm_cx else -1.0
    web_x = (float(thumb["x"]) + float(index["x"])) / 2.0
    web_y = (float(thumb["y"]) + float(index["y"])) / 2.0
    mcp_y = (float(index["y"]) + float(middle["y"]) + float(ring["y"]) + float(pinky["y"])) / 4.0
    wrist_y = float(wrist["y"])
    span_y = max(abs(wrist_y - mcp_y), 1e-4)

    axis_x = web_x + thumb_side * 0.03
    y_top = min(web_y, mcp_y) - 0.04 * span_y
    y_bottom = wrist_y + 0.05 * span_y
    y0 = int(np.clip(y_top * height, 0, height - 1))
    y1 = int(np.clip(y_bottom * height, 0, height - 1))
    if y1 - y0 < int(height * 0.10):
        return None

    band = 0.14
    step = max(1, (y1 - y0) // 56)
    path: list[dict] = []
    for y in range(y0, y1 + 1, step):
        cx = axis_x + thumb_side * min(0.06, 0.02 + (y - y0) / max(y1 - y0, 1) * 0.04)
        x0 = int(max(0, (cx - band) * width))
        x1 = int(min(width, (cx + band) * width))
        best_val = -1.0
        best_x = int(round(cx * width))
        for x in range(x0, x1):
            if mask[y, x] == 0:
                continue
            thumb_bias = 1.0 - min(abs(x / width - cx) / band, 1.0)
            val = float(enhanced[y, x]) * (0.35 + 0.65 * thumb_bias)
            if skeleton is not None and skeleton[y, x] > 0:
                val *= 1.18
            if val > best_val:
                best_val = val
                best_x = x
        if best_val >= threshold * 0.55:
            path.append({"x": round(best_x / width, 6), "y": round(y / height, 6)})

    path = _dedupe_path(path)
    if len(path) < MIN_LIFE_PATH_POINTS:
        return None

    norm_len = _path_length(path)
    ys = [p["y"] for p in path]
    coverage = (max(ys) - min(ys)) / span_y if ys else 0.0
    image_support = sum(
        1 for p in path
        if enhanced[
            int(np.clip(p["y"] * height, 0, height - 1)),
            int(np.clip(p["x"] * width, 0, width - 1)),
        ] >= threshold * 0.65
    ) / max(len(path), 1)

    confidence = float(np.clip(
        0.38 + 0.28 * min(coverage / 0.55, 1.0) + 0.34 * image_support,
        0.0,
        0.82,
    ))
    status = "detected" if confidence >= 0.55 and coverage >= 0.22 else "ambiguous"
    if coverage < 0.14:
        status = "insufficient_evidence"

    return {
        "status": status,
        "validity": status,
        "detected": status == "detected",
        "reason": "image_supported_life_line_arc_trace",
        "detection_method": DETECTION_METHOD,
        "confidence": round(confidence, 4),
        "confidence_band": confidence_band(confidence),
        "path": path,
        "path_point_count": len(path),
        "start_point": path[0],
        "end_point": path[-1],
        "endpoints": [path[0], path[-1]],
        "normalized_length": round(norm_len, 6),
        "coverage_span": round(float(np.clip(coverage, 0.0, 1.2)), 4),
        "continuity": round(min(0.95, 0.62 + 0.30 * image_support), 4),
        "image_support": round(float(image_support), 4),
        "source_candidate_id": "life_line_image_trace",
        "methods": [DETECTION_METHOD],
        "measurements": {
            "coverage_span": round(float(np.clip(coverage, 0.0, 1.2)), 4),
            "image_support": round(float(image_support), 4),
            "continuity": round(min(0.95, 0.62 + 0.30 * image_support), 4),
        },
    }
