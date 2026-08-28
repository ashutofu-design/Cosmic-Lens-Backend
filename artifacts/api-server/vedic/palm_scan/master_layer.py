"""Master Palmistry extraction composer.

Extends a Phase 1 PalmScanResult (schema 1.0) with a nested
``master_extraction`` object. Phase 2 still consumes the 1.0 fields only.
No personality, luck, marriage, or career claims are produced here.
"""
from __future__ import annotations

import math
from typing import Any

from .engine import MAJOR_LINE_NAMES, SCHEMA_VERSION, _feature

MASTER_SCHEMA = "palm_master_extraction/1.0"

MINOR_LINE_REGISTRY = (
    "relationship_union_lines",
    "influence_lines",
    "travel_lines",
    "intuition_line",
    "girdle_of_venus",
    "via_lascivia",
    "simian_line",
    "rascette_bracelet_1",
    "rascette_bracelet_2",
    "rascette_bracelet_3",
)

LINE_PAIRS = (
    ("heart_line", "head_line"),
    ("life_line", "head_line"),
    ("life_line", "heart_line"),
    ("fate_line", "head_line"),
    ("fate_line", "heart_line"),
    ("fate_line", "life_line"),
    ("sun_apollo_line", "heart_line"),
    ("sun_apollo_line", "head_line"),
    ("mercury_line", "heart_line"),
    ("life_line", "mars_support_line"),
)


def attach_master_extraction(
    result: dict,
    *,
    writing_hand: str | None = None,
    hand_slot: str | None = None,
) -> dict:
    """Mutate ``result`` with a nested master extraction block. Returns it."""
    side = (
        hand_slot
        or result.get("hand", {}).get("side")
        or result.get("hand", {}).get("handedness")
        or "unknown"
    )
    dominant = "unknown"
    if writing_hand in {"left", "right"} and side in {"left", "right"}:
        dominant = "dominant" if side == writing_hand else "non_dominant"
    quality = result.get("quality") or {}
    issues = quality.get("issues") or []
    retake = (not quality.get("usable")) or quality.get("gate") == "failed"
    master = {
        "schema_version": MASTER_SCHEMA,
        "parent_schema_version": result.get("schema_version", SCHEMA_VERSION),
        "scan_id": (result.get("metadata") or {}).get("scan_id"),
        "hand_side": side,
        "dominant_status": dominant,
        "writing_hand": writing_hand or "unknown",
        "image_quality": {
            **quality,
            "retake_required": bool(retake),
            "capture_decision": "retake_required" if retake else "accepted",
            "retake_reason": (issues[0].get("message") if issues else None),
            "capture_mode": "uploaded_still",
        },
        "coordinate_system": _coordinate_system(result),
        "palm_map": _palm_map(result),
        "palm_geometry": result.get("palm_geometry") or {},
        "landmarks": result.get("landmarks") or [],
        "major_lines": result.get("major_lines") or {},
        "line_stitching": result.get("line_stitching") or {},
        "minor_lines": _minor_lines(result),
        "line_segments": _line_segments(result),
        "line_micro_features": _micro_features(result),
        "mounts": _mounts(result),
        "fingers": result.get("fingers") or {},
        "fingertips": _fingertips(result),
        "thumb": result.get("thumb") or {},
        "wrist_rascette": _rascette(result),
        "special_markings": result.get("special_markings") or {},
        "line_relationships": _line_relationships(result),
        "marking_relationships": _marking_relationships(result),
        "confidence": _confidence_layers(result),
        "validation": {
            **(result.get("validation") or {}),
            "production_validation": result.get("production_validation") or {},
            "retake_required": bool(retake),
            "claims_forbidden": True,
            "policy": "unknown_over_unsupported_inference",
        },
        "detector_fusion": {
            "methods": ["mediapipe_hands", "opencv_crease", "geometric_line_namer"],
            "disagreement_policy": "ambiguous",
            "semantic_verification": (
                (result.get("secondary_lines") or {}).get("semantic_verification") or {}
            ),
        },
        "annotated_image_reference": result.get("annotated_image_reference"),
        "notes": [
            "Phase 1 records measured geometry only.",
            "Unavailable features stay unknown, ambiguous, or not_detected.",
        ],
    }
    result["master_extraction"] = master
    result["metadata"] = {
        **(result.get("metadata") or {}),
        "master_extraction_schema": MASTER_SCHEMA,
        "hand_slot": side,
        "writing_hand": writing_hand or "unknown",
        "dominant_status": dominant,
    }
    if retake:
        result["validation"] = {
            **(result.get("validation") or {}),
            "retake_required": True,
            "retake_reason": master["image_quality"]["retake_reason"],
        }
    return result


def compose_bilateral_comparison(
    *,
    left: dict,
    right: dict,
    writing_hand: str,
) -> dict:
    """Geometry-only left/right and dominant/non-dominant comparison."""
    if writing_hand not in {"left", "right"}:
        writing_hand = "unknown"
    scans = {"left": left or {}, "right": right or {}}
    comparisons = []
    for path, label in (
        ("palm_geometry.aspect_ratio.raw_ratio", "palm_aspect_ratio"),
        ("palm_geometry.width.normalized", "palm_width"),
        ("palm_geometry.length.normalized", "palm_length"),
        ("palm_geometry.area.normalized", "palm_area"),
        ("thumb.spread_angle.raw_degrees", "thumb_spread"),
        ("thumb.length.normalized", "thumb_length"),
        ("scan_confidence.overall", "scan_confidence"),
        ("quality.score", "image_quality"),
        ("major_lines.heart_line.visibility_strength", "heart_line_visibility"),
        ("major_lines.head_line.visibility_strength", "head_line_visibility"),
        ("major_lines.life_line.visibility_strength", "life_line_visibility"),
        ("major_lines.fate_line.normalized_length", "fate_line_length"),
        ("fingers.index.length_normalized", "index_length"),
        ("fingers.middle.length_normalized", "middle_length"),
        ("fingers.ring.length_normalized", "ring_length"),
        ("fingers.little.length_normalized", "little_length"),
    ):
        left_value = _nested(scans["left"], path)
        right_value = _nested(scans["right"], path)
        if not isinstance(left_value, (int, float)) or not isinstance(right_value, (int, float)):
            comparisons.append({
                "id": label, "path": path, "left_value": left_value,
                "right_value": right_value, "difference": None,
                "confidence": 0.0, "status": "unknown",
            })
            continue
        difference = float(right_value) - float(left_value)
        comparisons.append({
            "id": label, "path": path,
            "left_value": round(float(left_value), 6),
            "right_value": round(float(right_value), 6),
            "difference": round(difference, 6),
            "confidence": min(
                _nested(scans["left"], "scan_confidence.overall") or 0,
                _nested(scans["right"], "scan_confidence.overall") or 0,
            ),
            "status": "detected",
        })
    dominant = writing_hand if writing_hand in scans else "unknown"
    non_dominant = "left" if dominant == "right" else ("right" if dominant == "left" else "unknown")
    return {
        "schema_version": "palm_bilateral_comparison/1.0",
        "writing_hand": writing_hand,
        "dominant_hand": dominant,
        "non_dominant_hand": non_dominant,
        "dominant_hand_data": _hand_summary(scans.get(dominant) or {}),
        "non_dominant_hand_data": _hand_summary(scans.get(non_dominant) or {}),
        "comparisons": comparisons,
        "claims_forbidden": True,
        "status": "ok" if writing_hand in {"left", "right"} else "insufficient_data",
    }


def _hand_summary(scan: dict) -> dict:
    if not scan:
        return {"status": "unknown", "confidence": 0.0}
    master = scan.get("master_extraction") or {}
    lines = scan.get("major_lines") or {}
    return {
        "status": "detected" if scan.get("hand", {}).get("status") == "detected" else "unknown",
        "confidence": float((scan.get("scan_confidence") or {}).get("overall") or 0),
        "hand_side": master.get("hand_side") or scan.get("hand", {}).get("side"),
        "scan_id": (scan.get("metadata") or {}).get("scan_id"),
        "palm_geometry": scan.get("palm_geometry") or {},
        "major_line_visibility": {
            name: line.get("visibility_strength") or line.get("clarity")
            for name, line in lines.items() if isinstance(line, dict)
        },
        "finger_lengths": {
            name: finger.get("length_normalized")
            for name, finger in (scan.get("fingers") or {}).items()
            if isinstance(finger, dict)
        },
        "marking_count": len((scan.get("special_markings") or {}).get("candidates") or []),
    }


def _coordinate_system(result: dict) -> dict:
    dims = (result.get("metadata") or {}).get("dimensions") or {}
    return {
        "space": "processed_normalized",
        "origin": "top_left",
        "x_axis": "left_to_right",
        "y_axis": "top_to_bottom",
        "normalized_range": [0.0, 1.0],
        "width_px": dims.get("width_px"),
        "height_px": dims.get("height_px"),
        "every_feature_has_normalized_xy": True,
    }


def _palm_map(result: dict) -> list[dict]:
    objects: list[dict] = []
    for landmark in result.get("landmarks") or []:
        objects.append(_map_object(
            "landmark", landmark.get("name") or f"lm_{landmark.get('id')}",
            landmark.get("normalized_x", landmark.get("x")),
            landmark.get("normalized_y", landmark.get("y")),
            region="anatomy",
            size=None,
            orientation=None,
            confidence=landmark.get("confidence", 0),
        ))
    for name, line in (result.get("major_lines") or {}).items():
        path = line.get("path") or []
        if len(path) >= 1:
            mid = path[len(path) // 2]
            objects.append(_map_object(
                "major_line", name, mid.get("x"), mid.get("y"),
                region="palm", size=line.get("normalized_length"),
                orientation=line.get("direction"),
                confidence=line.get("confidence", 0),
            ))
    for name, mount in (result.get("mounts") or {}).items():
        poly = mount.get("region_polygon") or []
        if poly:
            cx = sum(p.get("x", 0) for p in poly) / len(poly)
            cy = sum(p.get("y", 0) for p in poly) / len(poly)
            objects.append(_map_object(
                "mount", name, cx, cy, region=name,
                size=mount.get("area_normalized"),
                orientation=None,
                confidence=mount.get("confidence", 0),
            ))
    for marking in (result.get("special_markings") or {}).get("candidates") or []:
        coords = marking.get("coordinates") or marking.get("location") or []
        point = coords[0] if isinstance(coords, list) and coords else (
            coords if isinstance(coords, dict) else {}
        )
        if isinstance(point, dict) and "x" in point:
            objects.append(_map_object(
                "marking", marking.get("type") or "ambiguous",
                point.get("x"), point.get("y"),
                region=marking.get("region") or "unknown",
                size=marking.get("size"),
                orientation=marking.get("orientation"),
                confidence=marking.get("confidence", 0),
            ))
    return [item for item in objects if item["normalized_x"] is not None]


def _map_object(kind, name, x, y, *, region, size, orientation, confidence):
    nx = None if x is None else round(float(x), 6)
    ny = None if y is None else round(float(y), 6)
    return {
        "kind": kind, "name": name,
        "x": nx, "y": ny,
        "normalized_x": nx, "normalized_y": ny,
        "region": region, "size": size, "orientation": orientation,
        "confidence": float(confidence or 0),
        "status": "detected" if nx is not None else "unknown",
    }


def _minor_lines(result: dict) -> dict:
    union = result.get("union_lines") or {}
    out = {}
    for name in MINOR_LINE_REGISTRY:
        if name == "relationship_union_lines":
            out[name] = {
                "status": union.get("status") or "not_detected",
                "confidence": float(union.get("confidence") or 0),
                "reason": union.get("reason") or "insufficient_visibility",
                "candidates": union.get("candidates") or [],
            }
        elif name.startswith("rascette"):
            out[name] = {
                "status": "unknown",
                "confidence": 0.0,
                "reason": "insufficient_visibility",
                "candidates": [],
            }
        else:
            out[name] = {
                "status": "not_detected",
                "confidence": 0.0,
                "reason": "insufficient_visibility",
                "candidates": [],
            }
    return out


def _line_segments(result: dict) -> dict:
    segments = {}
    for name, line in (result.get("major_lines") or {}).items():
        path = line.get("path") or []
        if len(path) < 2:
            segments[name] = []
            continue
        chunks = []
        step = max(1, len(path) // 4)
        for index in range(0, max(len(path) - 1, 1), step):
            piece = path[index:index + step + 1]
            if len(piece) < 2:
                continue
            chunks.append({
                "segment_index": len(chunks),
                "coordinates": piece,
                "visibility_strength": line.get("clarity") or line.get("measurements", {}).get("clarity"),
                "thickness": None,
                "direction": line.get("direction"),
                "curvature": line.get("curvature"),
                "confidence": line.get("confidence", 0),
                "status": line.get("status") or "unknown",
                "depth_note": "visibility_strength_proxy_not_physical_depth",
            })
        segments[name] = chunks
    return segments


def _micro_features(result: dict) -> list[dict]:
    features = []
    for name, line in (result.get("major_lines") or {}).items():
        mapping = {
            "breaks": "break", "gaps": "gap", "branches": "branch",
            "forks": "fork", "islands": "island",
            "crosses_intersections": "cross",
            "parallel_support_lines": "parallel_line",
        }
        for field, kind in mapping.items():
            items = line.get(field) or line.get("measurements", {}).get(f"{field.rstrip('s')}_candidates", []) or []
            if not isinstance(items, list):
                continue
            for index, item in enumerate(items):
                point = item if isinstance(item, dict) else {}
                x = point.get("x")
                y = point.get("y")
                if x is None or y is None:
                    continue
                features.append({
                    "marking_id": f"{name}_{kind}_{index}",
                    "type": kind,
                    "coordinates": {"x": x, "y": y, "normalized_x": x, "normalized_y": y},
                    "size": point.get("size"),
                    "orientation": point.get("orientation") or point.get("angle"),
                    "parent_line": name,
                    "parent_feature": name,
                    "region": "unknown",
                    "confidence": min(float(line.get("confidence") or 0), 0.55),
                    "status": "ambiguous",
                })
    return features


def _mounts(result: dict) -> dict:
    mounts = dict(result.get("mounts") or {})
    landmarks = result.get("landmarks") or []
    if "Plain of Mars" not in mounts and len(landmarks) >= 18:
        center = (result.get("palm_geometry") or {}).get("center") or {}
        cx = (center.get("normalized") or [None, None])[0]
        cy = (center.get("normalized") or [None, None])[1]
        if cx is not None and cy is not None:
            poly = [
                {"x": round(float(landmarks[5]["x"]), 6), "y": round(float(landmarks[5]["y"]), 6)},
                {"x": round(float(landmarks[9]["x"]), 6), "y": round(float(landmarks[9]["y"]), 6)},
                {"x": round(float(landmarks[13]["x"]), 6), "y": round(float(landmarks[13]["y"]), 6)},
                {"x": round(float(landmarks[17]["x"]), 6), "y": round(float(landmarks[17]["y"]), 6)},
                {"x": round(float(cx), 6), "y": round(float(cy), 6)},
            ]
            mounts["Plain of Mars"] = _feature(
                "detected",
                min(float((result.get("hand") or {}).get("confidence") or 0), 0.7),
                reason="geometry_from_finger_bases_and_palm_center",
                region_polygon=poly,
                area_normalized=None,
                markings=[],
                prominence_estimate=_feature("unknown", 0.0, reason="monocular_rgb_cannot_measure_3d"),
            )
        else:
            mounts["Plain of Mars"] = _feature(
                "unknown", 0.0,
                reason="region_derived_when_palm_center_is_detected",
                region_polygon=[], markings=[],
            )
    elif "Plain of Mars" not in mounts:
        mounts["Plain of Mars"] = _feature(
            "unknown", 0.0,
            reason="region_derived_when_upper_and_lower_mars_are_both_detected",
            region_polygon=[], markings=[],
        )
    return mounts


def _fingertips(result: dict) -> dict:
    tips = {}
    for name, finger in (result.get("fingers") or {}).items():
        tip = finger.get("tip_shape") or {}
        classification = tip.get("classification") or "unknown"
        mapped = {
            "tapered": "conic",
            "broad": "spatulate",
            "rounded_or_square_ambiguous": "unknown",
            "square": "square",
            "rounded": "rounded",
            "conic": "conic",
            "pointed": "pointed",
            "spatulate": "spatulate",
            "mixed": "mixed",
        }.get(classification, "unknown")
        tips[name] = {
            "status": "unknown" if mapped == "unknown" else (tip.get("status") or finger.get("status") or "unknown"),
            "classification": mapped,
            "measurements": {
                "taper": finger.get("taper"),
                "width_normalized": finger.get("width_normalized"),
                "tip_location": finger.get("tip_location"),
            },
            "confidence": float(tip.get("confidence") or 0) if mapped != "unknown" else 0.0,
        }
    thumb = (result.get("thumb") or {}).get("tip_shape") or {}
    tips["thumb"] = {
        "status": thumb.get("status") or "unknown",
        "classification": thumb.get("classification") or "unknown",
        "measurements": {},
        "confidence": float(thumb.get("confidence") or 0),
    }
    return tips


def _rascette(result: dict) -> dict:
    wrist = (result.get("segmentation") or {}).get("wrist") or {}
    return {
        "wrist_boundary": wrist,
        "first_bracelet_line": {"status": "not_detected", "confidence": 0.0, "reason": "insufficient_visibility"},
        "second_bracelet_line": {"status": "not_detected", "confidence": 0.0, "reason": "insufficient_visibility"},
        "third_bracelet_line": {"status": "not_detected", "confidence": 0.0, "reason": "insufficient_visibility"},
        "additional_visible_lines": [],
        "breaks": [], "chains": [], "crossings": [], "markings": [],
    }


def _line_relationships(result: dict) -> list[dict]:
    lines = result.get("major_lines") or {}
    out = []
    for left_name, right_name in LINE_PAIRS:
        left = lines.get(left_name) or {}
        right = lines.get(right_name) or {}
        left_path = left.get("path") or []
        right_path = right.get("path") or []
        rel = {
            "relationship": f"{left_name}_{right_name}",
            "coordinates": None,
            "distance": None,
            "angle": None,
            "confidence": 0.0,
            "status": "unknown",
        }
        if len(left_path) < 2 or len(right_path) < 2:
            out.append(rel)
            continue
        distance, point = _min_path_distance(left_path, right_path)
        angle = _path_heading_delta(left, right)
        conf = min(float(left.get("confidence") or 0), float(right.get("confidence") or 0))
        rel.update({
            "coordinates": point,
            "distance": round(distance, 6),
            "angle": round(angle, 3) if angle is not None else None,
            "intersects": bool(distance < 0.015),
            "confidence": round(conf, 4),
            "status": "detected" if conf >= 0.55 else "ambiguous",
        })
        out.append(rel)
    return out


def _marking_relationships(result: dict) -> list[dict]:
    mounts = result.get("mounts") or {}
    polygons = {
        name: mount.get("region_polygon") or []
        for name, mount in mounts.items()
        if isinstance(mount, dict)
    }
    out = []
    for marking in (result.get("special_markings") or {}).get("candidates") or []:
        point = None
        coords = marking.get("coordinates") or []
        if isinstance(coords, list) and coords and isinstance(coords[0], dict):
            point = coords[0]
        elif isinstance(coords, dict):
            point = coords
        if not point or "x" not in point:
            continue
        region = "unknown"
        for name, poly in polygons.items():
            if _point_in_polygon(point, poly):
                region = name
                break
        out.append({
            "marking_type": marking.get("type") or "ambiguous",
            "region": region,
            "coordinates": {"x": point.get("x"), "y": point.get("y")},
            "confidence": float(marking.get("confidence") or 0),
            "status": "detected" if region != "unknown" else "unknown",
            "guessed": False,
        })
    return out


def _confidence_layers(result: dict) -> dict:
    scan = result.get("scan_confidence") or {}
    quality = result.get("quality") or {}
    hand = result.get("hand") or {}
    landmarks = result.get("landmarks") or []
    landmark_conf = 0.0
    if landmarks:
        landmark_conf = sum(float(p.get("confidence") or 0) for p in landmarks) / len(landmarks)
    return {
        "image": float(quality.get("score") or 0),
        "hand": float(hand.get("confidence") or 0),
        "landmark": round(landmark_conf, 4),
        "line": float(scan.get("major_lines") or 0),
        "segment": float(scan.get("major_lines") or 0),
        "marking": float(scan.get("markings") or 0),
        "mount": float(scan.get("mounts") or 0),
        "measurement": float(scan.get("overall") or 0),
        "relationship": round(min(float(scan.get("major_lines") or 0), landmark_conf), 4),
        "overall": float(scan.get("overall") or 0),
        "phase_2_eligible": bool(scan.get("phase_2_eligible")),
    }


def _nested(value: Any, path: str):
    current = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _min_path_distance(left: list[dict], right: list[dict]) -> tuple[float, dict]:
    best = 9.0
    point = {"x": None, "y": None}
    for a in left:
        for b in right:
            dist = math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))
            if dist < best:
                best = dist
                point = {
                    "x": round((float(a["x"]) + float(b["x"])) / 2.0, 6),
                    "y": round((float(a["y"]) + float(b["y"])) / 2.0, 6),
                }
    return best, point


def _path_heading_delta(left: dict, right: dict) -> float | None:
    a = left.get("direction")
    b = right.get("direction")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return None
    delta = abs(float(a) - float(b)) % 180.0
    return min(delta, 180.0 - delta)


def _point_in_polygon(point: dict, polygon: list[dict]) -> bool:
    if len(polygon) < 3:
        return False
    x, y = float(point["x"]), float(point["y"])
    inside = False
    j = len(polygon) - 1
    for i, vertex in enumerate(polygon):
        xi, yi = float(vertex.get("x", 0)), float(vertex.get("y", 0))
        xj, yj = float(polygon[j].get("x", 0)), float(polygon[j].get("y", 0))
        intersect = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside
