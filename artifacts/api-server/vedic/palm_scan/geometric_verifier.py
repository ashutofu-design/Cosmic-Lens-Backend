"""Landmark-geometry line namer for pixel crease candidates.

Does not invent paths. It only assigns Life / Heart / Head / Fate identities
to crease polylines the pixel detector already found.
"""
from __future__ import annotations

import math
from typing import Any


class GeometricLineVerifier:
    last_evidence: dict[str, Any]

    def __init__(self, minimum_score: float = 0.46):
        self.minimum_score = minimum_score
        self.last_evidence = {"status": "ready", "method": "geometric_landmark_regions"}

    def verify(self, candidates: list[dict], context: dict) -> dict[str, dict]:
        landmarks = context.get("landmarks") or []
        by_id = {
            int(point["id"]): point
            for point in landmarks
            if isinstance(point, dict) and "id" in point
        }
        if len(by_id) < 21 or not candidates:
            self.last_evidence = {
                "status": "insufficient_landmarks_or_candidates",
                "method": "geometric_landmark_regions",
                "candidate_count": len(candidates),
                "landmark_count": len(by_id),
            }
            return {}

        wrist = by_id[0]
        index_mcp = by_id[5]
        middle_mcp = by_id[9]
        pinky_mcp = by_id[17]
        thumb_mcp = by_id[2]
        mcp_y = (index_mcp["y"] + middle_mcp["y"] + by_id[13]["y"] + pinky_mcp["y"]) / 4.0
        wrist_y = float(wrist["y"])
        span_y = max(abs(wrist_y - mcp_y), 1e-4)
        palm_cx = (
            wrist["x"] + index_mcp["x"] + middle_mcp["x"] + pinky_mcp["x"]
        ) / 4.0
        thumb_side = 1.0 if float(thumb_mcp["x"]) >= palm_cx else -1.0
        web = {
            "x": (thumb_mcp["x"] + index_mcp["x"]) / 2.0,
            "y": (thumb_mcp["y"] + index_mcp["y"]) / 2.0,
        }

        ranked: dict[str, list[tuple[float, str]]] = {
            "heart_line": [], "head_line": [], "life_line": [], "fate_line": [],
        }
        for candidate in candidates:
            candidate_id = candidate.get("id")
            path = candidate.get("path") or []
            if not isinstance(candidate_id, str) or len(path) < 2:
                continue
            scores = self._scores(
                candidate, path, mcp_y, wrist_y, span_y, palm_cx,
                thumb_side, web, middle_mcp,
            )
            for name, score in scores.items():
                if score >= self.minimum_score:
                    ranked[name].append((score, candidate_id))

        used: set[str] = set()
        assignments: dict[str, dict] = {}
        soft_minimum = max(0.30, self.minimum_score - 0.14)
        for name in ("life_line", "heart_line", "head_line", "fate_line"):
            options = sorted(ranked[name], key=lambda item: item[0], reverse=True)
            for score, candidate_id in options:
                if candidate_id in used:
                    continue
                assignments[name] = {
                    "candidate_id": candidate_id,
                    "confidence": round(min(0.86, 0.50 + 0.40 * score), 4),
                    "method": "geometric_landmark_regions",
                }
                used.add(candidate_id)
                break
            if name not in assignments and options and options[0][0] >= soft_minimum:
                score, candidate_id = options[0]
                if candidate_id not in used:
                    assignments[name] = {
                        "candidate_id": candidate_id,
                        "confidence": round(min(0.72, 0.42 + 0.35 * score), 4),
                        "method": "geometric_landmark_regions_soft",
                    }
                    used.add(candidate_id)

        self.last_evidence = {
            "status": "completed",
            "method": "geometric_landmark_regions",
            "assigned": sorted(assignments),
            "candidate_count": len(candidates),
        }
        return assignments

    @staticmethod
    def _scores(
        candidate: dict, path: list[dict], mcp_y: float, wrist_y: float,
        span_y: float, palm_cx: float, thumb_side: float, web: dict,
        middle_mcp: dict,
    ) -> dict[str, float]:
        xs = [float(point["x"]) for point in path]
        ys = [float(point["y"]) for point in path]
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        start, end = path[0], path[-1]
        direction = float(candidate.get("direction") or candidate.get("measurements", {}).get("direction_degrees") or 0.0)
        curvature = float(candidate.get("curvature") or candidate.get("measurements", {}).get("curvature") or 0.0)
        horiz = 1.0 - min(_heading_from_horizontal(direction) / 90.0, 1.0)
        vert = min(_heading_from_horizontal(direction) / 90.0, 1.0)
        y_from_mcp = (mean_y - mcp_y) / span_y if wrist_y >= mcp_y else (mcp_y - mean_y) / span_y

        heart = _clamp(
            0.38 * _band(y_from_mcp, 0.06, 0.32)
            + 0.34 * horiz
            + 0.16 * (1.0 - min(curvature / 1.2, 1.0))
            + 0.12 * (1.0 - min(abs(mean_x - palm_cx) * 2.2, 1.0))
        )
        head = _clamp(
            0.36 * _band(y_from_mcp, 0.22, 0.52)
            + 0.32 * horiz
            + 0.18 * (1.0 - min(curvature / 1.4, 1.0))
            + 0.14 * (1.0 - min(abs(mean_x - palm_cx) * 2.0, 1.0))
        )
        web_dist = min(_dist(start, web), _dist(end, web))
        wrist_point = {"x": palm_cx, "y": wrist_y}
        wrist_dist = min(_dist(start, wrist_point), _dist(end, wrist_point))
        thumb_half = 1.0 if (mean_x - palm_cx) * thumb_side > 0 else 0.35
        life = _clamp(
            0.28 * (1.0 - min(web_dist / 0.18, 1.0))
            + 0.22 * (1.0 - min(wrist_dist / 0.28, 1.0))
            + 0.22 * thumb_half
            + 0.16 * min(curvature / 0.8, 1.0)
            + 0.12 * _band(y_from_mcp, 0.18, 0.95)
        )
        fate = _clamp(
            0.42 * vert
            + 0.28 * (1.0 - min(abs(mean_x - float(middle_mcp["x"])) / 0.16, 1.0))
            + 0.18 * _band(y_from_mcp, 0.20, 0.95)
            + 0.12 * (1.0 - min(curvature / 1.5, 1.0))
        )
        return {
            "heart_line": heart,
            "head_line": head,
            "life_line": life,
            "fate_line": fate,
        }


def _heading_from_horizontal(degrees: float) -> float:
    angle = abs(degrees) % 180.0
    return min(angle, 180.0 - angle)


def _band(value: float, lo: float, hi: float) -> float:
    if lo <= value <= hi:
        return 1.0
    span = max(hi - lo, 1e-6)
    return max(0.0, 1.0 - min(abs(value - lo), abs(value - hi)) / span)


def _dist(a: dict, b: dict) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
