"""Anatomical px→mm scaling and physical measurements for palm lines."""
from __future__ import annotations

import math
from typing import Any

import numpy as np

REFERENCE_PALM_WIDTH_MM = 75.0
INDEX_MCP_ID = 5
PINKY_MCP_ID = 17
WRIST_ID = 0


def landmarks_by_id(landmarks: list[dict]) -> dict[int, dict]:
    return {
        int(p["id"]): p
        for p in landmarks
        if isinstance(p, dict) and "id" in p
    }


def palm_width_px(landmarks: list[dict], width: int, height: int) -> float:
    by_id = landmarks_by_id(landmarks)
    index = by_id.get(INDEX_MCP_ID)
    pinky = by_id.get(PINKY_MCP_ID)
    if not index or not pinky:
        return float(max(width, height)) * 0.35
    p5 = np.array([float(index["x"]) * width, float(index["y"]) * height], dtype=np.float64)
    p17 = np.array([float(pinky["x"]) * width, float(pinky["y"]) * height], dtype=np.float64)
    return float(max(np.linalg.norm(p5 - p17), 8.0))


def compute_px_to_mm_ratio(
    landmarks: list[dict],
    width: int,
    height: int,
    *,
    reference_palm_width_mm: float = REFERENCE_PALM_WIDTH_MM,
) -> dict[str, Any]:
    width_px = palm_width_px(landmarks, width, height)
    ratio = reference_palm_width_mm / width_px
    return {
        "px_to_mm_ratio": round(ratio, 6),
        "reference_palm_width_mm": reference_palm_width_mm,
        "palm_width_px": round(width_px, 3),
        "anchor_landmarks": [INDEX_MCP_ID, PINKY_MCP_ID],
        "method": "index_pinky_mcp_euclidean_anchor",
    }


def _path_points_px(path: list[dict], width: int, height: int) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for point in path:
        if not isinstance(point, dict):
            continue
        points.append((float(point["x"]) * width, float(point["y"]) * height))
    return points


def path_arc_length_px(path: list[dict], width: int, height: int) -> float:
    points = _path_points_px(path, width, height)
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = points[i][1] - points[i - 1][1]
        total += math.hypot(dx, dy)
    return float(total)


def path_arc_length_mm(path: list[dict], px_to_mm: float, width: int, height: int) -> float:
    return round(path_arc_length_px(path, width, height) * px_to_mm, 2)


def point_to_landmark_distance_mm(
    point: dict,
    landmark: dict,
    px_to_mm: float,
    width: int,
    height: int,
) -> float:
    px = float(point["x"]) * width
    py = float(point["y"]) * height
    lx = float(landmark["x"]) * width
    ly = float(landmark["y"]) * height
    return round(math.hypot(px - lx, py - ly) * px_to_mm, 2)


def distance_to_wrist_mm(
    path: list[dict],
    wrist: dict,
    px_to_mm: float,
    width: int,
    height: int,
    *,
    use_nearest: bool = True,
) -> float | None:
    if not path:
        return None
    if use_nearest:
        return min(
            point_to_landmark_distance_mm(point, wrist, px_to_mm, width, height)
            for point in path
        )
    return point_to_landmark_distance_mm(path[-1], wrist, px_to_mm, width, height)


def polyline_min_distance_mm(
    path_a: list[dict],
    path_b: list[dict],
    px_to_mm: float,
    width: int,
    height: int,
) -> float | None:
    pts_a = _path_points_px(path_a, width, height)
    pts_b = _path_points_px(path_b, width, height)
    if len(pts_a) < 2 or len(pts_b) < 2:
        return None
    best = 1e18
    for ax, ay in pts_a:
        for bx, by in pts_b:
            best = min(best, math.hypot(ax - bx, ay - by))
    return round(best * px_to_mm, 2)


def enrich_line_physical_measurements(
    line: dict,
    landmarks: list[dict],
    width: int,
    height: int,
    *,
    other_lines: dict[str, list[dict]] | None = None,
) -> dict:
    scale = compute_px_to_mm_ratio(landmarks, width, height)
    px_to_mm = float(scale["px_to_mm_ratio"])
    path = list(line.get("path") or [])
    by_id = landmarks_by_id(landmarks)
    wrist = by_id.get(WRIST_ID, {"x": 0.5, "y": 0.9})

    measurements = dict(line.get("measurements") or {})
    measurements["physical_scale"] = scale
    if len(path) >= 2:
        arc_mm = path_arc_length_mm(path, px_to_mm, width, height)
        measurements["length_mm"] = arc_mm
        measurements["arc_length_mm"] = arc_mm
        measurements["distance_to_wrist_mm"] = distance_to_wrist_mm(
            path, wrist, px_to_mm, width, height,
        )
        if line.get("start_point"):
            measurements["start_distance_to_wrist_mm"] = point_to_landmark_distance_mm(
                line["start_point"], wrist, px_to_mm, width, height,
            )
        if line.get("end_point"):
            measurements["end_distance_to_wrist_mm"] = point_to_landmark_distance_mm(
                line["end_point"], wrist, px_to_mm, width, height,
            )
        gaps: dict[str, float] = {}
        for other_name, other_path in (other_lines or {}).items():
            gap = polyline_min_distance_mm(path, other_path, px_to_mm, width, height)
            if gap is not None:
                gaps[f"gap_to_{other_name}_mm"] = gap
        if gaps:
            measurements["intersection_gaps_mm"] = gaps

    line["length_mm"] = measurements.get("length_mm")
    line["measurements"] = measurements
    return line


def attach_scan_physical_metrics(result: dict) -> None:
    landmarks = result.get("landmarks") or []
    dims = (result.get("metadata") or {}).get("dimensions") or {}
    width = int(dims.get("width_px") or 0)
    height = int(dims.get("height_px") or 0)
    if not landmarks or width <= 0 or height <= 0:
        return

    scale = compute_px_to_mm_ratio(landmarks, width, height)
    palm_geom = result.setdefault("palm_geometry", {})
    palm_geom["physical_scale"] = {
        "status": "detected",
        "confidence": palm_geom.get("width", {}).get("confidence", 0.7),
        **scale,
    }
    result.setdefault("metadata", {})["physical_scale"] = scale

    major = result.get("major_lines") or {}
    paths = {
        name: list((line or {}).get("path") or [])
        for name, line in major.items()
        if isinstance(line, dict)
    }
    for name, line in major.items():
        if not isinstance(line, dict):
            continue
        others = {k: v for k, v in paths.items() if k != name and len(v) >= 2}
        enrich_line_physical_measurements(line, landmarks, width, height, other_lines=others)
