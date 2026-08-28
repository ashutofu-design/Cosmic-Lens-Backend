"""Image-first Fate Line detection from visible crease structure."""
from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

from .detectors import confidence_band
from .fate_line_normalize import proportional_fate_corridor, trace_fate_line_normalized

MIN_FATE_PATH_POINTS = 4
MIN_IMAGE_SUPPORT_DETECT = 0.42
MIN_COVERAGE_DETECT = 0.28
MIN_NORMALIZED_LENGTH_DETECT = 0.18
DETECTED_SCORE = 0.58
AMBIGUITY_MARGIN = 0.06
STITCH_MAX_GAP = 0.072
STITCH_MIN_BRIDGE_SUPPORT = 0.26
EXTEND_STEP = 0.007
EXTEND_MAX_STEPS = 55
EXTEND_SUPPORT_RATIO = 0.78


PIPELINE_REVISION = "image_first_fate_line_detector/v8.2"
MAX_FATE_AXIS_OFFSET = 0.11
MIN_FATE_AXIS_SCORE_DETECT = 0.52


class FateLineDetector:
    """Select Fate Line from raw crease candidates using image evidence first."""

    detection_method = "image_first_fate_line_detector"
    pipeline_revision = PIPELINE_REVISION

    def detect(
        self,
        candidates: list[dict],
        context: dict,
        *,
        crease_masks: dict[str, np.ndarray] | None = None,
        excluded_candidate_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        excluded = excluded_candidate_ids or set()
        palm_ctx = self._palm_context(context)
        arrays = self._image_arrays(context, crease_masks)
        palm_ctx = self._enrich_palm_context(palm_ctx, arrays["palm_mask"])
        audit: list[dict[str, Any]] = []
        scored: list[dict[str, Any]] = []

        graph_trace = self._trace_graph_normalized(context, palm_ctx, arrays)
        if graph_trace is not None:
            graph_trace["candidate_id"] = "fate_normalized_graph_trace"
            graph_trace["audit_entry"] = {
                **graph_trace,
                "source": "normalized_affine_graph_dijkstra",
            }
            audit.append(graph_trace["audit_entry"])
            scored.append(graph_trace)

        for candidate in candidates:
            candidate_id = str(candidate.get("id") or "")
            path = list(candidate.get("path") or [])
            entry = self._evaluate_candidate(candidate, path, palm_ctx, arrays)
            entry["candidate_id"] = candidate_id
            if candidate_id in excluded:
                entry["rejection_reasons"].append("assigned_to_other_major_line")
                entry["final_score"] = round(
                    max(0.0, float(entry["final_score"]) - 0.08), 4,
                )
            audit.append(entry)
            if "path_too_short" in entry["rejection_reasons"]:
                continue
            scored.append(entry)

        stitched = self._try_stitch(scored, candidates, palm_ctx, arrays)
        if stitched:
            audit.append(stitched["audit_entry"])
            scored.append(stitched)

        chained = self._try_chain_stitch(scored, candidates, palm_ctx, arrays)
        if chained:
            audit.append(chained["audit_entry"])
            scored.append(chained)

        scored.sort(key=lambda item: item["final_score"], reverse=True)
        for rank, item in enumerate(scored, start=1):
            item["rank"] = rank

        best = self._select_best_scored(scored) if scored else None
        if best is None and audit:
            best = max(audit, key=lambda item: float(item.get("final_score") or 0.0))
        best = self._prefer_full_span_candidate(best, scored)
        second = scored[1] if len(scored) > 1 else None

        if best is not None:
            refined = self._refine_best_path(best, palm_ctx, arrays)
            if refined is not None:
                audit.append(refined["audit_entry"])
                best = refined
                scored.insert(0, refined)
                second = scored[1] if len(scored) > 1 else None
                best = self._prefer_full_span_candidate(best, scored)

        ultra = len(candidates) == 0

        needs_span_fallback = (
            best is None
            or float(best.get("final_score") or 0.0) < (0.40 if ultra else 0.55)
            or float(best.get("coverage_span") or 0.0) < MIN_COVERAGE_DETECT
        )
        if needs_span_fallback:
            corridor = self._trace_vertical_corridor(
                palm_ctx, arrays, aggressive=True, ultra=ultra,
            )
            if corridor is not None:
                corridor["candidate_id"] = "fate_corridor_trace"
                corridor["audit_entry"] = {
                    **corridor,
                    "source": "vertical_crease_corridor_trace",
                }
                audit.append(corridor["audit_entry"])
                if best is None or float(corridor["final_score"]) >= float(
                    best.get("final_score") or 0.0
                ) or float(corridor.get("coverage_span") or 0.0) > float(
                    best.get("coverage_span") or 0.0
                ):
                    best = corridor
                    scored.insert(0, corridor)
                    second = scored[1] if len(scored) > 1 else None

        if best is None:
            mask_trace = self._trace_crease_mask_vertical(palm_ctx, arrays, ultra=ultra)
            if mask_trace is not None:
                mask_trace["candidate_id"] = "fate_crease_mask_trace"
                mask_trace["audit_entry"] = {**mask_trace, "source": "crease_mask_vertical_trace"}
                audit.append(mask_trace["audit_entry"])
                best = mask_trace

        if best is None:
            skel_trace = self._trace_skeleton_vertical(palm_ctx, arrays, ultra=ultra)
            if skel_trace is not None:
                skel_trace["candidate_id"] = "fate_skeleton_trace"
                skel_trace["audit_entry"] = {**skel_trace, "source": "skeleton_vertical_trace"}
                audit.append(skel_trace["audit_entry"])
                best = skel_trace

        if best is None:
            best = self._last_resort_best(candidates, palm_ctx, arrays)
            if best is not None:
                audit.append({**best, "source": "last_resort_vertical_candidate"})

        if best is None:
            desperate = self._trace_vertical_corridor(
                palm_ctx, arrays, aggressive=True, ultra=True, desperate=True,
            )
            if desperate is not None:
                desperate["candidate_id"] = "fate_desperate_corridor_trace"
                desperate["audit_entry"] = {
                    **desperate,
                    "source": "desperate_vertical_crease_corridor_trace",
                }
                audit.append(desperate["audit_entry"])
                best = desperate
                scored.append(desperate)

        if scored:
            best = self._select_best_scored(scored)
            best_id = best.get("candidate_id")
            others = [item for item in scored if item.get("candidate_id") != best_id]
            second = self._select_best_scored(others) if others else None

        status, validity, reason = self._resolve_status(best, second)

        major_line = self._build_major_line(
            best, status, validity, reason, candidates, audit=audit,
        )
        selected_ids = set(major_line.get("source_candidate_ids") or [])
        if major_line.get("source_candidate_id"):
            selected_ids.add(str(major_line["source_candidate_id"]))
        for entry in audit:
            entry_ids = set(entry.get("source_candidate_ids") or [entry.get("candidate_id")])
            if entry_ids & selected_ids:
                entry["selected"] = status in {"detected", "ambiguous"}
            elif entry.get("rejection_reasons"):
                entry["selected"] = False
            elif best is not None:
                entry["selected"] = False
                entry.setdefault("rejection_reasons", []).append("lower_score_than_selected")
        return {
            "major_line": major_line,
            "debug": {
                "status": status,
                "validity": validity,
                "method": self.detection_method,
                "pipeline_revision": self.pipeline_revision,
                "candidates_count": len(candidates),
                "candidate_audit": audit,
                "audit_count": len(audit),
                "scored_count": len(scored),
                "best_candidate_id": (best or {}).get("candidate_id"),
                "selected_candidate_ids": major_line.get("source_candidate_ids") or [],
                "stitching_applied": bool(
                    best and (best.get("stitched") or best.get("chain_stitch"))
                ),
                "path_extension_applied": bool(best and best.get("path_extended")),
                "graph_trace_applied": bool(best and best.get("graph_trace")),
                "normalization": (best or {}).get("normalization"),
                "ridge_method": (best or {}).get("ridge_method"),
                "image_support": major_line.get("image_support"),
                "coverage_span": major_line.get("coverage_span"),
                "rejection_reason": reason if status != "detected" else None,
            },
        }

    def _trace_graph_normalized(
        self,
        context: dict,
        palm_ctx: dict,
        arrays: dict,
    ) -> dict | None:
        landmarks = context.get("landmarks") or []
        if len(landmarks) < 21:
            return None
        rgb = np.ascontiguousarray(context["processed_rgb"])
        palm_mask = arrays["palm_mask"]
        traced = trace_fate_line_normalized(rgb, palm_mask, landmarks)
        if traced is None or len(traced.get("path") or []) < MIN_FATE_PATH_POINTS:
            return None
        path = list(traced["path"])
        entry = self._evaluate_candidate(
            {
                "id": "fate_normalized_graph_trace",
                "normalized_length": traced.get("normalized_length"),
                "confidence": 0.62,
                "continuity": 0.82,
            },
            path,
            palm_ctx,
            arrays,
        )
        entry["graph_trace"] = True
        entry["normalization"] = traced.get("normalization")
        entry["ridge_method"] = traced.get("ridge_method")
        traced_cov = float(traced.get("coverage_span") or 0.0)
        if traced_cov > float(entry.get("coverage_span") or 0.0):
            entry["coverage_span"] = round(traced_cov, 4)
        traced_len = float(traced.get("normalized_length") or 0.0)
        if traced_len > float(entry.get("normalized_length") or 0.0):
            entry["normalized_length"] = round(traced_len, 6)
        entry["source_candidate_ids"] = ["fate_normalized_graph_trace"]
        entry["final_score"] = round(
            min(1.0, float(entry["final_score"]) + 0.10),
            4,
        )
        if float(entry.get("fate_axis_score") or 0.0) >= MIN_FATE_AXIS_SCORE_DETECT:
            entry["final_score"] = round(
                min(1.0, float(entry["final_score"]) + 0.05),
                4,
            )
        return entry

    def _evaluate_candidate(
        self,
        candidate: dict,
        path: list[dict],
        palm_ctx: dict,
        arrays: dict,
    ) -> dict[str, Any]:
        reasons: list[str] = []
        norm_len = float(candidate.get("normalized_length") or self._path_length(path))
        orientation = self._orientation_score(path)
        image_support = self._image_support(path, arrays)
        skeleton_support = self._skeleton_support(path, arrays)
        coverage = self._coverage_span(path, palm_ctx)
        continuity = float(
            candidate.get("continuity")
            or candidate.get("measurements", {}).get("continuity")
            or 0.0
        )
        geom = self._geometric_score(path, palm_ctx)
        trajectory = self._trajectory_score(path)
        palm_center = self._palm_center_relation(path, palm_ctx)
        fate_axis = self._fate_axis_score(path, palm_ctx)
        candidate_conf = float(candidate.get("confidence") or 0.0)

        if len(path) < 2:
            reasons.append("path_too_short")
        if len(path) < MIN_FATE_PATH_POINTS:
            reasons.append("insufficient_path_points")
        if norm_len < 0.08:
            reasons.append("fragment_normalized_length")
        if image_support < 0.25:
            reasons.append("poor_image_support")
        if coverage < 0.10:
            reasons.append("insufficient_coverage_span")
        if continuity >= 0.99 and norm_len < MIN_NORMALIZED_LENGTH_DETECT:
            reasons.append("high_continuity_but_fragment")
        if fate_axis < 0.40:
            reasons.append("off_fate_axis_middle_corridor")
        if fate_axis < 0.22:
            reasons.append("edge_crease_lunar_mount_region")

        combined_image = 0.65 * image_support + 0.35 * skeleton_support
        final_score = self._final_score(
            combined_image, coverage, norm_len, trajectory,
            geom, candidate_conf, orientation, fate_axis,
        )
        penalty = 0.0
        if len(path) < MIN_FATE_PATH_POINTS:
            penalty += 0.05
        if norm_len < MIN_NORMALIZED_LENGTH_DETECT:
            penalty += 0.08 * (1.0 - norm_len / max(MIN_NORMALIZED_LENGTH_DETECT, 1e-4))
        if image_support < MIN_IMAGE_SUPPORT_DETECT:
            penalty += 0.10 * (1.0 - image_support / max(MIN_IMAGE_SUPPORT_DETECT, 1e-4))
        if coverage < MIN_COVERAGE_DETECT:
            penalty += 0.08 * (1.0 - coverage / max(MIN_COVERAGE_DETECT, 1e-4))
        if fate_axis < MIN_FATE_AXIS_SCORE_DETECT:
            penalty += 0.22 * (1.0 - fate_axis / max(MIN_FATE_AXIS_SCORE_DETECT, 1e-4))
        if fate_axis < 0.30:
            penalty += 0.12
        final_score = float(np.clip(final_score - penalty, 0.0, 1.0))

        return {
            "candidate_id": candidate.get("id"),
            "raw_length": candidate.get("length"),
            "normalized_length": round(norm_len, 6),
            "orientation": round(orientation, 4),
            "image_support": round(image_support, 4),
            "skeleton_support": round(skeleton_support, 4),
            "continuity": round(continuity, 4),
            "coverage_span": round(coverage, 4),
            "palm_center_relation": round(palm_center, 4),
            "fate_axis_score": round(fate_axis, 4),
            "fate_axis_offset": round(self._fate_axis_offset(path, palm_ctx), 4),
            "trajectory_score": round(trajectory, 4),
            "geometric_score": round(geom, 4),
            "candidate_confidence": round(candidate_conf, 4),
            "final_score": round(final_score, 4),
            "rejection_reasons": reasons,
            "selected": False,
            "path": path,
            "stitched": False,
            "source_candidate_ids": [str(candidate.get("id") or "")],
        }

    def _resolve_status(
        self,
        best: dict | None,
        second: dict | None,
    ) -> tuple[str, str, str]:
        if best is None:
            return "not_detected", "not_detected", "no_plausible_fate_line_candidate"
        score = float(best["final_score"])
        path_len = len(best.get("path") or [])
        img = float(best.get("image_support") or 0.0)
        if score < 0.35:
            if path_len >= MIN_FATE_PATH_POINTS and img >= 0.12:
                return (
                    "insufficient_evidence",
                    "insufficient_evidence",
                    "weak_crease_evidence_best_available_path",
                )
            return "not_detected", "not_detected", "all_candidates_below_minimum_score"
        if (
            best["image_support"] < MIN_IMAGE_SUPPORT_DETECT
            or best["coverage_span"] < MIN_COVERAGE_DETECT
            or best["normalized_length"] < MIN_NORMALIZED_LENGTH_DETECT
        ):
            if (
                best.get("graph_trace")
                and float(best.get("image_support") or 0.0) >= MIN_IMAGE_SUPPORT_DETECT
                and float(best.get("coverage_span") or 0.0) >= 0.22
                and float(best.get("fate_axis_score") or 0.0) >= 0.44
                and score >= 0.48
            ):
                return "detected", "detected", "graph_trace_full_span_image_supported"
            return (
                "insufficient_evidence",
                "insufficient_evidence",
                "crease_evidence_too_weak_or_fragmentary",
            )
        if second and abs(score - float(second["final_score"])) <= AMBIGUITY_MARGIN:
            return "ambiguous", "ambiguous", "multiple_plausible_fate_line_candidates"
        if score >= DETECTED_SCORE:
            axis = float(best.get("fate_axis_score") or 0.0)
            if axis < MIN_FATE_AXIS_SCORE_DETECT:
                return (
                    "insufficient_evidence",
                    "insufficient_evidence",
                    "detected_crease_off_middle_finger_axis",
                )
            return "detected", "detected", "image_supported_fate_line_trajectory"
        return (
            "insufficient_evidence",
            "insufficient_evidence",
            "below_detected_confidence_threshold",
        )

    def _build_major_line(
        self,
        best: dict | None,
        status: str,
        validity: str,
        reason: str,
        candidates: list[dict],
        *,
        audit: list[dict] | None = None,
    ) -> dict:
        base = {
            "status": status,
            "validity": validity,
            "detected": status == "detected",
            "reason": reason,
            "detection_method": self.detection_method,
            "pipeline_revision": self.pipeline_revision,
            "branches": [],
            "forks": [],
            "path": [],
            "path_point_count": 0,
            "endpoints": [],
            "start_point": None,
            "end_point": None,
            "source_candidate_id": None,
            "source_candidate_ids": [],
            "image_support": None,
            "coverage_span": None,
            "continuity": None,
            "confidence": 0.0,
            "confidence_band": "unreliable",
            "methods": [self.detection_method],
            "measurements": {
                "validated_branch_status": "not_available",
                "validated_fork_status": "not_available",
                "raw_skeleton_junction_note": (
                    "generic_branch_points_not_validated_as_fate_line_branches"
                ),
            },
        }
        if best is None:
            if audit:
                fallback = max(
                    audit,
                    key=lambda item: float(item.get("final_score") or 0.0),
                )
                base["candidate_score"] = fallback.get("final_score")
                base["image_support"] = fallback.get("image_support")
                base["coverage_span"] = fallback.get("coverage_span")
                base["measurements"] = {
                    **base["measurements"],
                    "image_support": fallback.get("image_support"),
                    "coverage_span": fallback.get("coverage_span"),
                    "audit_fallback": True,
                }
                if fallback.get("path"):
                    path = list(fallback["path"])
                    base["path"] = path
                    base["path_point_count"] = len(path)
                    if len(path) >= 2:
                        base["start_point"] = path[0]
                        base["end_point"] = path[-1]
                        base["endpoints"] = [path[0], path[-1]]
            return base

        path = list(best.get("path") or [])
        by_id = {str(c.get("id")): c for c in candidates}
        primary_id = (best.get("source_candidate_ids") or [None])[0]
        primary = by_id.get(str(primary_id), {})

        confidence = self._major_line_confidence(best, status)
        endpoints = (
            [path[0], path[-1]] if len(path) >= 2 else list(primary.get("endpoints") or [])
        )
        base.update({
            "confidence": round(confidence, 4),
            "confidence_band": confidence_band(confidence),
            "path": path,
            "path_point_count": len(path),
            "start_point": path[0] if path else None,
            "end_point": path[-1] if path else None,
            "endpoints": endpoints,
            "length": primary.get("length"),
            "normalized_length": best.get("normalized_length"),
            "continuity": best.get("continuity"),
            "direction": primary.get("direction"),
            "curvature": primary.get("curvature"),
            "clarity": primary.get("clarity"),
            "visibility_strength": primary.get("clarity"),
            "image_support": best.get("image_support"),
            "coverage_span": best.get("coverage_span"),
            "source_candidate_id": primary_id,
            "source_candidate_ids": list(best.get("source_candidate_ids") or []),
            "candidate_score": best.get("final_score"),
            "trajectory_score": best.get("trajectory_score"),
            "geometric_score": best.get("geometric_score"),
            "fate_axis_score": best.get("fate_axis_score"),
            "stitching_applied": bool(best.get("stitched") or best.get("chain_stitch")),
            "path_extension_applied": bool(best.get("path_extended")),
            "corridor_trace_applied": bool(best.get("corridor_trace")),
            "graph_trace_applied": bool(best.get("graph_trace")),
            "normalization": best.get("normalization"),
            "ridge_method": best.get("ridge_method"),
            "measurements": {
                **(primary.get("measurements") or {}),
                "image_support": best.get("image_support"),
                "coverage_span": best.get("coverage_span"),
                "skeleton_support": best.get("skeleton_support"),
                "validated_branch_status": "not_available",
                "validated_fork_status": "not_available",
                "path_extension_applied": bool(best.get("path_extended")),
                "corridor_trace_applied": bool(best.get("corridor_trace")),
            },
        })
        base["branches"] = []
        base["forks"] = []
        base["detected"] = status == "detected"
        if len(path) < MIN_FATE_PATH_POINTS and status == "detected":
            base["status"] = "insufficient_evidence"
            base["validity"] = "insufficient_evidence"
            base["detected"] = False
            base["reason"] = f"path_has_{len(path)}_points_minimum_{MIN_FATE_PATH_POINTS}_required"
        best["selected"] = status in {"detected", "ambiguous"}
        return base

    @staticmethod
    def _major_line_confidence(best: dict, status: str) -> float:
        raw = float(best["final_score"])
        if status == "not_detected":
            return float(np.clip(raw * 0.45, 0.0, 0.32))
        if status == "ambiguous":
            raw *= 0.82
        elif status == "insufficient_evidence":
            raw *= 0.55
        return float(np.clip(raw, 0.0, 0.88))

    @staticmethod
    def _final_score(
        image: float,
        coverage: float,
        norm_len: float,
        trajectory: float,
        geom: float,
        candidate_conf: float,
        orientation: float,
        fate_axis: float,
    ) -> float:
        length_score = min(norm_len / 0.55, 1.0)
        return float(np.clip(
            0.26 * image
            + 0.16 * coverage
            + 0.12 * length_score
            + 0.08 * trajectory
            + 0.10 * geom
            + 0.22 * fate_axis
            + 0.04 * candidate_conf
            + 0.02 * orientation,
            0.0,
            1.0,
        ))

    @staticmethod
    def _select_best_scored(scored: list[dict]) -> dict:
        def rank_key(item: dict) -> float:
            final = float(item.get("final_score") or 0.0)
            axis = float(item.get("fate_axis_score") or 0.0)
            coverage = float(item.get("coverage_span") or 0.0)
            coverage_bonus = min(coverage / max(MIN_COVERAGE_DETECT, 1e-4), 1.0) * 0.22
            fragment_penalty = 0.20 if coverage < MIN_COVERAGE_DETECT else 0.0
            graph_bonus = 0.06 if item.get("graph_trace") else 0.0
            return final * 0.48 + axis * 0.30 + coverage_bonus + graph_bonus - fragment_penalty
        return max(scored, key=rank_key)

    @staticmethod
    def _prefer_full_span_candidate(best: dict | None, scored: list[dict]) -> dict | None:
        if best is None or not scored:
            return best
        coverage = float(best.get("coverage_span") or 0.0)
        if coverage >= MIN_COVERAGE_DETECT:
            return best
        image = float(best.get("image_support") or 0.0)
        alternatives = [
            item for item in scored
            if float(item.get("coverage_span") or 0.0) >= MIN_COVERAGE_DETECT
            and float(item.get("image_support") or 0.0) >= image * 0.68
            and len(item.get("path") or []) >= MIN_FATE_PATH_POINTS
        ]
        if not alternatives:
            alternatives = [
                item for item in scored
                if float(item.get("coverage_span") or 0.0) >= coverage + 0.10
                and float(item.get("image_support") or 0.0) >= image * 0.60
                and len(item.get("path") or []) >= MIN_FATE_PATH_POINTS
            ]
        if not alternatives:
            return best
        return max(
            alternatives,
            key=lambda item: (
                float(item.get("coverage_span") or 0.0) * 0.55
                + float(item.get("final_score") or 0.0) * 0.45
            ),
        )

    @staticmethod
    def _fate_axis_x(palm_ctx: dict) -> float:
        return float(
            palm_ctx.get("fate_axis_x")
            or palm_ctx.get("middle_mcp_x")
            or palm_ctx.get("palm_cx")
            or 0.5
        )

    @classmethod
    def _fate_axis_offset(cls, path: list[dict], palm_ctx: dict) -> float:
        if len(path) < 2:
            return 1.0
        axis_x = cls._fate_axis_x(palm_ctx)
        xs = [float(p["x"]) for p in path]
        return abs(sum(xs) / len(xs) - axis_x)

    @classmethod
    def _fate_axis_score(cls, path: list[dict], palm_ctx: dict) -> float:
        if len(path) < 2:
            return 0.0
        offset = cls._fate_axis_offset(path, palm_ctx)
        mean_score = float(np.clip(1.0 - offset / MAX_FATE_AXIS_OFFSET, 0.0, 1.0))
        axis_x = cls._fate_axis_x(palm_ctx)
        max_dev = max(abs(float(p["x"]) - axis_x) for p in path)
        dev_score = float(np.clip(1.0 - max_dev / (MAX_FATE_AXIS_OFFSET * 1.35), 0.0, 1.0))
        return float(np.clip(0.62 * mean_score + 0.38 * dev_score, 0.0, 1.0))

    @staticmethod
    def _column_center_weight(x: int, width: int, axis_x: float, band: float) -> float:
        offset = abs((x / max(width, 1)) - axis_x)
        return float(np.clip(1.0 - offset / max(band, 0.06), 0.08, 1.0))

    def _try_chain_stitch(
        self,
        scored: list[dict],
        candidates: list[dict],
        palm_ctx: dict,
        arrays: dict,
    ) -> dict | None:
        if len(scored) < 2:
            return None
        by_id = {str(c["id"]): c for c in candidates}
        vertical = sorted(
            [
                item for item in scored
                if float(item.get("orientation") or 0.0) >= 0.35
            ],
            key=lambda item: float(np.mean([p["y"] for p in item["path"]])),
        )
        if len(vertical) < 2:
            return None
        best_chain: dict | None = None
        best_score = max(float(item["final_score"]) for item in scored)
        for start_idx, start in enumerate(vertical):
            chain_path = list(start["path"])
            chain_ids = list(start.get("source_candidate_ids") or [start["candidate_id"]])
            chain_continuity = float(start.get("continuity") or 0.0)
            current: dict = {**start, "path": chain_path, "source_candidate_ids": chain_ids}
            merged_any = False
            merged: dict | None = None
            for nxt in vertical[start_idx + 1:]:
                if nxt["candidate_id"] in chain_ids:
                    continue
                merged = self._merge_pair(current, nxt, by_id, palm_ctx, arrays)
                if merged is None:
                    continue
                chain_path = list(merged["path"])
                chain_ids = list(merged["source_candidate_ids"])
                chain_continuity = min(chain_continuity, float(nxt.get("continuity") or 0.0))
                current = {**merged, "path": chain_path, "source_candidate_ids": chain_ids}
                merged_any = True
            if not merged_any or len(chain_ids) < 2 or merged is None:
                continue
            if float(merged["final_score"]) > best_score:
                best_score = float(merged["final_score"])
                merged["stitched"] = True
                merged["chain_stitch"] = True
                merged["audit_entry"] = {**merged, "stitched_from": chain_ids, "chain_stitch": True}
                best_chain = merged
        return best_chain

    def _refine_best_path(
        self,
        best: dict,
        palm_ctx: dict,
        arrays: dict,
    ) -> dict | None:
        path = list(best.get("path") or [])
        if len(path) < 2:
            return None
        extended = self._extend_path_along_crease(path, arrays)
        if len(extended) <= len(path):
            return None
        entry = self._evaluate_candidate(
            {
                "id": "fate_path_extended",
                "normalized_length": self._path_length(extended),
                "confidence": best.get("candidate_confidence", 0.0),
                "continuity": best.get("continuity", 0.0),
            },
            extended,
            palm_ctx,
            arrays,
        )
        entry["candidate_id"] = "fate_path_extended"
        if entry["rejection_reasons"]:
            soft_ok = (
                entry["image_support"] >= float(best["image_support"]) * 0.88
                and entry["coverage_span"] > float(best["coverage_span"])
                and entry["normalized_length"] > float(best["normalized_length"])
            )
            if not soft_ok:
                return None
            entry["rejection_reasons"] = [
                reason for reason in entry["rejection_reasons"]
                if reason not in {
                    "insufficient_path_points",
                    "high_continuity_but_fragment",
                    "fragment_normalized_length",
                }
            ]
        if float(entry["image_support"]) < float(best["image_support"]) * EXTEND_SUPPORT_RATIO:
            return None
        if float(entry["final_score"]) < float(best["final_score"]) * 0.82:
            return None
        source_ids = list(best.get("source_candidate_ids") or [best.get("candidate_id")])
        entry.update({
            "path": extended,
            "source_candidate_ids": source_ids,
            "stitched": bool(best.get("stitched")),
            "chain_stitch": bool(best.get("chain_stitch")),
            "path_extended": True,
            "selected": False,
            "audit_entry": {
                **entry,
                "refined_from": source_ids,
                "path_extension_applied": True,
            },
        })
        return entry

    def _extend_path_along_crease(
        self,
        path: list[dict],
        arrays: dict,
    ) -> list[dict]:
        if len(path) < 2:
            return path
        extended = list(path)
        extended = self._extend_one_end(extended, "start", arrays)
        extended = self._extend_one_end(extended, "end", arrays)
        return self._dedupe_path(extended)

    def _extend_one_end(
        self,
        path: list[dict],
        end: str,
        arrays: dict,
    ) -> list[dict]:
        enhanced = arrays["crease_response"]
        palm_mask = arrays["palm_mask"]
        threshold = float(arrays["response_threshold"]) * 0.75
        height, width = enhanced.shape
        if end == "start":
            anchor, guide = path[0], path[1]
        else:
            guide, anchor = path[-2], path[-1]
        dx = float(anchor["x"]) - float(guide["x"])
        dy = float(anchor["y"]) - float(guide["y"])
        norm = math.hypot(dx, dy) or 1e-6
        ux, uy = dx / norm, dy / norm
        x, y = float(anchor["x"]), float(anchor["y"])
        new_points: list[dict] = []
        for _ in range(EXTEND_MAX_STEPS):
            x += ux * EXTEND_STEP
            y += uy * EXTEND_STEP
            if not (0.02 <= x <= 0.98 and 0.02 <= y <= 0.98):
                break
            px = int(round(x * width))
            py = int(round(y * height))
            if not (0 <= px < width and 0 <= py < height):
                break
            if palm_mask[py, px] == 0:
                break
            x0, x1 = max(0, px - 6), min(width, px + 7)
            y0, y1 = max(0, py - 2), min(height, py + 3)
            patch = enhanced[y0:y1, x0:x1]
            if patch.size == 0 or float(np.max(patch)) < threshold:
                break
            peak_x = x0 + int(np.argmax(np.max(patch, axis=0)))
            new_points.append({
                "x": round(peak_x / width, 6),
                "y": round(y, 6),
            })
        if not new_points:
            return path
        if end == "start":
            return list(reversed(new_points)) + path
        return path + new_points

    @staticmethod
    def _dedupe_path(path: list[dict]) -> list[dict]:
        if not path:
            return []
        deduped = [path[0]]
        for point in path[1:]:
            last = deduped[-1]
            if math.hypot(point["x"] - last["x"], point["y"] - last["y"]) < 0.0025:
                continue
            deduped.append(point)
        return deduped

    def _trace_vertical_corridor(
        self,
        palm_ctx: dict,
        arrays: dict,
        *,
        aggressive: bool = False,
        ultra: bool = False,
        desperate: bool = False,
    ) -> dict | None:
        enhanced = arrays["crease_response"]
        palm_mask = arrays["palm_mask"]
        threshold = float(arrays["response_threshold"]) * (
            0.48 if desperate else (0.58 if ultra else (0.68 if aggressive else 0.82))
        )
        height, width = enhanced.shape
        axis_x = self._fate_axis_x(palm_ctx)
        cx = axis_x
        wrist_y = float(palm_ctx.get("wrist_y") or 0.88)
        mcp_y = float(palm_ctx.get("mcp_y") or 0.45)
        y_top = int(np.clip(min(mcp_y, wrist_y) * height, 0, height - 1))
        y_bottom = int(np.clip(max(mcp_y, wrist_y) * height, 0, height - 1))
        min_span = 0.04 if desperate else (0.06 if ultra else (0.08 if aggressive else 0.12))
        if y_bottom - y_top < int(height * min_span):
            return None

        band = 0.14 if desperate else (0.12 if ultra else (0.10 if aggressive else 0.08))
        x0 = int(max(0, (cx - band) * width))
        x1 = int(min(width, (cx + band) * width))
        best_x = int(round(cx * width))
        best_col_score = -1.0
        for x in range(x0, x1):
            column = enhanced[y_top:y_bottom, x]
            mask_col = palm_mask[y_top:y_bottom, x]
            if not np.any(mask_col):
                continue
            response = float(np.mean(column[mask_col > 0]))
            center_w = self._column_center_weight(x, width, axis_x, band)
            score = response * (0.22 + 0.78 * center_w)
            if score > best_col_score:
                best_col_score = score
                best_x = x
        min_col = threshold * (
            0.12 if desperate else (0.28 if ultra else (0.45 if aggressive else 0.65))
        )
        if best_col_score < min_col:
            return None

        step = max(
            1,
            (y_bottom - y_top) // (
                96 if desperate else (80 if ultra else (64 if aggressive else 48))
            ),
        )
        path: list[dict] = []
        min_pixel = threshold * (
            0.22 if desperate else (0.38 if ultra else (0.55 if aggressive else 0.75))
        )
        min_points = 2 if desperate else (3 if ultra else MIN_FATE_PATH_POINTS)
        x_radius = 8 if desperate else (7 if ultra else 5)
        for y in range(y_top, y_bottom + 1, step):
            x_search0 = max(0, best_x - x_radius)
            x_search1 = min(width, best_x + x_radius + 1)
            patch = enhanced[y, x_search0:x_search1]
            mask_patch = palm_mask[y, x_search0:x_search1]
            if not np.any(mask_patch):
                continue
            best_peak = -1.0
            peak_x = best_x
            for xi in range(mask_patch.size):
                if mask_patch[xi] == 0:
                    continue
                px = x_search0 + xi
                center_w = self._column_center_weight(px, width, axis_x, band)
                weighted = float(patch[xi]) * (0.30 + 0.70 * center_w)
                if weighted > best_peak:
                    best_peak = weighted
                    peak_x = px
            if best_peak < min_pixel:
                continue
            path.append({
                "x": round(peak_x / width, 6),
                "y": round(y / height, 6),
            })
        path = self._dedupe_path(path)
        if len(path) < min_points:
            return None
        entry = self._evaluate_candidate(
            {
                "id": "fate_corridor_trace",
                "normalized_length": self._path_length(path),
                "confidence": 0.45,
                "continuity": 0.75,
            },
            path,
            palm_ctx,
            arrays,
        )
        entry["corridor_trace"] = True
        entry["desperate_trace"] = desperate
        entry["source_candidate_ids"] = ["fate_corridor_trace"]
        return entry

    @staticmethod
    def _enrich_palm_context(palm_ctx: dict, palm_mask: np.ndarray) -> dict:
        ys, xs = np.where(palm_mask > 0)
        if ys.size < 64:
            return palm_ctx
        height, width = palm_mask.shape
        y_min, y_max = int(ys.min()), int(ys.max())
        x_min, x_max = int(xs.min()), int(xs.max())
        bbox_mcp = (y_min / height) + 0.05
        bbox_wrist = (y_max / height) - 0.02
        bbox_span = max(bbox_wrist - bbox_mcp, 0.08)
        bbox_cx = (x_min + x_max) / (2.0 * width)
        landmark_span = float(palm_ctx.get("span_y") or 0.0)
        if bbox_span >= max(landmark_span * 0.75, 0.12):
            middle_mcp_x = float(palm_ctx.get("middle_mcp_x") or palm_ctx.get("palm_cx") or 0.5)
            return {
                **palm_ctx,
                "mcp_y": min(float(palm_ctx.get("mcp_y") or bbox_mcp), bbox_mcp),
                "wrist_y": max(float(palm_ctx.get("wrist_y") or bbox_wrist), bbox_wrist),
                "span_y": max(landmark_span, bbox_span),
                "palm_cx": bbox_cx * 0.40 + float(palm_ctx.get("palm_cx") or 0.5) * 0.60,
                "middle_mcp_x": middle_mcp_x,
                "fate_axis_x": middle_mcp_x,
                "palm_context_source": "landmarks_plus_mask_bbox",
            }
        middle_mcp_x = float(palm_ctx.get("middle_mcp_x") or palm_ctx.get("palm_cx") or 0.5)
        return {**palm_ctx, "fate_axis_x": middle_mcp_x}

    def _trace_crease_mask_vertical(
        self,
        palm_ctx: dict,
        arrays: dict,
        *,
        ultra: bool = False,
    ) -> dict | None:
        crease_binary = arrays.get("crease_binary")
        if crease_binary is None:
            enhanced = arrays["crease_response"]
            palm_mask = arrays["palm_mask"]
            threshold = float(arrays["response_threshold"]) * (0.42 if ultra else 0.55)
            crease_binary = np.uint8(
                (enhanced >= threshold) & (palm_mask > 0),
            ) * 255
        height, width = crease_binary.shape
        axis_x = self._fate_axis_x(palm_ctx)
        wrist_y = float(palm_ctx.get("wrist_y") or 0.88)
        mcp_y = float(palm_ctx.get("mcp_y") or 0.45)
        y_top = int(np.clip(min(mcp_y, wrist_y) * height, 0, height - 1))
        y_bottom = int(np.clip(max(mcp_y, wrist_y) * height, 0, height - 1))
        if y_bottom - y_top < int(height * (0.06 if ultra else 0.08)):
            return None
        band = 0.12 if ultra else 0.10
        x0 = int(max(0, (axis_x - band) * width))
        x1 = int(min(width, (axis_x + band) * width))
        step = max(1, (y_bottom - y_top) // (72 if ultra else 56))
        min_points = 3 if ultra else MIN_FATE_PATH_POINTS
        path: list[dict] = []
        for y in range(y_top, y_bottom + 1, step):
            row = crease_binary[y, x0:x1]
            if not np.any(row):
                continue
            best_val = -1.0
            peak_x = x0
            for xi in range(row.size):
                if row[xi] == 0:
                    continue
                px = x0 + xi
                center_w = self._column_center_weight(px, width, axis_x, band)
                weighted = float(row[xi]) * (0.25 + 0.75 * center_w)
                if weighted > best_val:
                    best_val = weighted
                    peak_x = px
            path.append({"x": round(peak_x / width, 6), "y": round(y / height, 6)})
        path = self._dedupe_path(path)
        if len(path) < min_points:
            return None
        entry = self._evaluate_candidate(
            {
                "id": "fate_crease_mask_trace",
                "normalized_length": self._path_length(path),
                "confidence": 0.40,
                "continuity": 0.70,
            },
            path,
            palm_ctx,
            arrays,
        )
        entry["crease_mask_trace"] = True
        entry["source_candidate_ids"] = ["fate_crease_mask_trace"]
        return entry

    def _trace_skeleton_vertical(
        self,
        palm_ctx: dict,
        arrays: dict,
        *,
        ultra: bool = False,
    ) -> dict | None:
        skeleton = arrays.get("skeleton")
        if skeleton is None:
            return None
        height, width = skeleton.shape
        axis_x = self._fate_axis_x(palm_ctx)
        wrist_y = float(palm_ctx.get("wrist_y") or 0.88)
        mcp_y = float(palm_ctx.get("mcp_y") or 0.45)
        y_top = int(np.clip(min(mcp_y, wrist_y) * height, 0, height - 1))
        y_bottom = int(np.clip(max(mcp_y, wrist_y) * height, 0, height - 1))
        band = 0.12 if ultra else 0.10
        x0 = int(max(0, (axis_x - band) * width))
        x1 = int(min(width, (axis_x + band) * width))
        step = max(1, (y_bottom - y_top) // (72 if ultra else 56))
        min_points = 3 if ultra else MIN_FATE_PATH_POINTS
        path: list[dict] = []
        palm_mask = arrays["palm_mask"]
        for y in range(y_top, y_bottom + 1, step):
            row = skeleton[y, x0:x1]
            mask_row = palm_mask[y, x0:x1]
            active = np.where((row > 0) & (mask_row > 0))[0]
            if active.size == 0:
                continue
            best_idx = active[0]
            best_w = -1.0
            for idx in active:
                px = x0 + int(idx)
                center_w = self._column_center_weight(px, width, axis_x, band)
                weighted = center_w
                if weighted > best_w:
                    best_w = weighted
                    best_idx = idx
            peak_x = x0 + int(best_idx)
            path.append({"x": round(peak_x / width, 6), "y": round(y / height, 6)})
        path = self._dedupe_path(path)
        if len(path) < min_points:
            return None
        entry = self._evaluate_candidate(
            {
                "id": "fate_skeleton_trace",
                "normalized_length": self._path_length(path),
                "confidence": 0.38,
                "continuity": 0.72,
            },
            path,
            palm_ctx,
            arrays,
        )
        entry["skeleton_trace"] = True
        entry["source_candidate_ids"] = ["fate_skeleton_trace"]
        return entry

    def _last_resort_best(
        self,
        candidates: list[dict],
        palm_ctx: dict,
        arrays: dict,
    ) -> dict | None:
        best_entry: dict | None = None
        best_rank = -1.0
        for candidate in candidates:
            path = list(candidate.get("path") or [])
            if len(path) < 2:
                continue
            orientation = self._orientation_score(path)
            center = self._palm_center_relation(path, palm_ctx)
            rank = orientation * 0.55 + center * 0.25 + self._path_length(path) * 0.20
            if rank <= best_rank:
                continue
            entry = self._evaluate_candidate(candidate, path, palm_ctx, arrays)
            entry["candidate_id"] = str(candidate.get("id") or "")
            entry["source_candidate_ids"] = [entry["candidate_id"]]
            entry["last_resort"] = True
            best_rank = rank
            best_entry = entry
        return best_entry

    def _try_stitch(
        self,
        scored: list[dict],
        candidates: list[dict],
        palm_ctx: dict,
        arrays: dict,
    ) -> dict | None:
        if len(scored) < 2:
            return None
        by_id = {str(c["id"]): c for c in candidates}
        best_pair = None
        best_score = 0.0
        for i, a in enumerate(scored):
            for b in scored[i + 1:]:
                merged = self._merge_pair(a, b, by_id, palm_ctx, arrays)
                if merged and merged["final_score"] > best_score:
                    best_score = merged["final_score"]
                    best_pair = merged
        if best_pair is None or best_score <= max(s["final_score"] for s in scored):
            return None
        return best_pair

    def _merge_pair(
        self,
        a: dict,
        b: dict,
        by_id: dict[str, dict],
        palm_ctx: dict,
        arrays: dict,
    ) -> dict | None:
        configs = [
            (list(a["path"]) + list(b["path"])[1:], a["path"][-1], b["path"][0], a, b, True, True),
            (list(b["path"]) + list(a["path"])[1:], b["path"][-1], a["path"][0], b, a, True, True),
        ]
        for path, p1, p2, first, second, a_end, b_start in configs:
            gap = math.hypot(float(p1["x"]) - float(p2["x"]), float(p1["y"]) - float(p2["y"]))
            if gap > STITCH_MAX_GAP:
                continue
            if not self._directions_compatible(
                first["path"], second["path"], a_end, b_start,
            ):
                continue
            bridge = self._bridge_support(p1, p2, arrays)
            if bridge < STITCH_MIN_BRIDGE_SUPPORT:
                continue
            ids = list(first["source_candidate_ids"]) + list(second["source_candidate_ids"])
            entry = self._evaluate_candidate(
                {
                    "id": "+".join(ids),
                    "normalized_length": self._path_length(path),
                    "confidence": max(
                        float(by_id.get(ids[0], {}).get("confidence") or 0),
                        float(by_id.get(ids[-1], {}).get("confidence") or 0),
                    ),
                    "continuity": min(float(a["continuity"]), float(b["continuity"])),
                },
                path,
                palm_ctx,
                arrays,
            )
            if entry["rejection_reasons"]:
                continue
            entry["stitched"] = True
            entry["source_candidate_ids"] = ids
            entry["audit_entry"] = {**entry, "stitched_from": ids}
            return entry
        return None

    @staticmethod
    def _directions_compatible(
        path_a: list[dict],
        path_b: list[dict],
        a_at_end: bool,
        b_at_start: bool,
    ) -> bool:
        if len(path_a) < 2 or len(path_b) < 2:
            return False
        if a_at_end:
            p0, p1 = path_a[-2], path_a[-1]
        else:
            p0, p1 = path_a[0], path_a[1]
        t_a = math.degrees(math.atan2(p1["y"] - p0["y"], p1["x"] - p0["x"]))
        if b_at_start:
            p0, p1 = path_b[0], path_b[1]
        else:
            p0, p1 = path_b[-2], path_b[-1]
        t_b = math.degrees(math.atan2(p1["y"] - p0["y"], p1["x"] - p0["x"]))
        delta = abs((t_a - t_b + 180) % 360 - 180)
        return delta <= 35.0

    @staticmethod
    def _path_length(path: list[dict]) -> float:
        if len(path) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(path)):
            total += math.hypot(
                path[i]["x"] - path[i - 1]["x"],
                path[i]["y"] - path[i - 1]["y"],
            )
        return total

    def _image_support(self, path: list[dict], arrays: dict) -> float:
        if len(path) < 2:
            return 0.0
        enhanced = arrays["crease_response"]
        palm_mask = arrays["palm_mask"]
        height, width = enhanced.shape
        threshold = arrays["response_threshold"]
        supported, total = 0, 0
        for i in range(len(path)):
            points = [path[i]]
            if i > 0:
                points.extend(self._interpolate(path[i - 1], path[i], 4))
            for point in points:
                x = int(round(float(point["x"]) * width))
                y = int(round(float(point["y"]) * height))
                if not (0 <= x < width and 0 <= y < height):
                    continue
                if palm_mask[y, x] == 0:
                    continue
                total += 1
                y0, y1 = max(0, y - 1), min(height, y + 2)
                x0, x1 = max(0, x - 1), min(width, x + 2)
                local = float(np.max(enhanced[y0:y1, x0:x1]))
                if local >= threshold:
                    supported += 1
        return supported / max(total, 1)

    def _skeleton_support(self, path: list[dict], arrays: dict) -> float:
        skeleton = arrays.get("skeleton")
        if skeleton is None or len(path) < 2:
            return 0.0
        height, width = skeleton.shape
        hits, total = 0, 0
        for point in path:
            x = int(round(float(point["x"]) * width))
            y = int(round(float(point["y"]) * height))
            if not (0 <= x < width and 0 <= y < height):
                continue
            total += 1
            y0, y1 = max(0, y - 2), min(height, y + 3)
            x0, x1 = max(0, x - 2), min(width, x + 3)
            if np.any(skeleton[y0:y1, x0:x1] > 0):
                hits += 1
        return hits / max(total, 1)

    def _bridge_support(self, p1: dict, p2: dict, arrays: dict) -> float:
        enhanced = arrays["crease_response"]
        palm_mask = arrays["palm_mask"]
        height, width = enhanced.shape
        threshold = arrays["response_threshold"]
        samples = self._interpolate(p1, p2, 8)
        supported, total = 0, 0
        for point in samples:
            x = int(round(float(point["x"]) * width))
            y = int(round(float(point["y"]) * height))
            if not (0 <= x < width and 0 <= y < height):
                continue
            if palm_mask[y, x] == 0:
                continue
            total += 1
            if enhanced[y, x] >= threshold:
                supported += 1
        return supported / max(total, 1)

    @staticmethod
    def _interpolate(a: dict, b: dict, steps: int) -> list[dict]:
        return [
            {
                "x": a["x"] + (b["x"] - a["x"]) * t / steps,
                "y": a["y"] + (b["y"] - a["y"]) * t / steps,
            }
            for t in range(1, steps)
        ]

    @staticmethod
    def _coverage_span(path: list[dict], palm_ctx: dict) -> float:
        if len(path) < 2:
            return 0.0
        ys = [float(p["y"]) for p in path]
        span = max(float(palm_ctx.get("span_y") or 1e-4), 1e-4)
        return float(np.clip((max(ys) - min(ys)) / span, 0.0, 1.2))

    @staticmethod
    def _orientation_score(path: list[dict]) -> float:
        if len(path) < 2:
            return 0.0
        dx = path[-1]["x"] - path[0]["x"]
        dy = path[-1]["y"] - path[0]["y"]
        angle = abs(math.degrees(math.atan2(dy, dx)))
        vert = min(angle, 180 - angle)
        return float(np.clip(vert / 90.0, 0.0, 1.0))

    @staticmethod
    def _trajectory_score(path: list[dict]) -> float:
        if len(path) < 3:
            return 0.5
        angles = []
        for i in range(1, len(path) - 1):
            v1 = (path[i]["x"] - path[i - 1]["x"], path[i]["y"] - path[i - 1]["y"])
            v2 = (path[i + 1]["x"] - path[i]["x"], path[i + 1]["y"] - path[i]["y"])
            a1 = math.degrees(math.atan2(v1[1], v1[0]))
            a2 = math.degrees(math.atan2(v2[1], v2[0]))
            delta = abs((a1 - a2 + 180) % 360 - 180)
            angles.append(delta)
        consistency = 1.0 - min(float(np.mean(angles)) / 45.0, 1.0)
        vert_segments = 0
        for i in range(1, len(path)):
            dx = path[i]["x"] - path[i - 1]["x"]
            dy = path[i]["y"] - path[i - 1]["y"]
            seg_angle = abs(math.degrees(math.atan2(dy, dx)))
            if min(seg_angle, 180 - seg_angle) >= 55:
                vert_segments += 1
        vert_ratio = vert_segments / max(len(path) - 1, 1)
        return float(np.clip(0.55 * consistency + 0.45 * vert_ratio, 0.0, 1.0))

    @staticmethod
    def _geometric_score(path: list[dict], palm_ctx: dict) -> float:
        if len(path) < 2:
            return 0.0
        xs = [float(p["x"]) for p in path]
        ys = [float(p["y"]) for p in path]
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        center_x = float(palm_ctx.get("palm_cx") or 0.5)
        middle_x = float(palm_ctx.get("middle_mcp_x") or center_x)
        span = max(float(palm_ctx.get("span_y") or 1e-4), 1e-4)
        mcp_y = float(palm_ctx.get("mcp_y") or 0.5)
        y_band = 1.0 - min(abs((mean_y - mcp_y) / span - 0.45) / 0.55, 1.0)
        center_band = 1.0 - min(abs(mean_x - middle_x) / 0.18, 1.0)
        return float(np.clip(0.55 * y_band + 0.45 * center_band, 0.0, 1.0))

    @staticmethod
    def _palm_center_relation(path: list[dict], palm_ctx: dict) -> float:
        if len(path) < 2:
            return 0.0
        xs = [float(p["x"]) for p in path]
        axis_x = FateLineDetector._fate_axis_x(palm_ctx)
        return 1.0 - min(abs((sum(xs) / len(xs)) - axis_x) * 4.5, 1.0)

    @staticmethod
    def _palm_context(context: dict) -> dict:
        landmarks = context.get("landmarks") or []
        by_id = {int(p["id"]): p for p in landmarks if isinstance(p, dict) and "id" in p}
        wrist = by_id.get(0, {"x": 0.5, "y": 0.9})
        middle = by_id.get(9, {"x": 0.5, "y": 0.5})
        index = by_id.get(5, middle)
        ring = by_id.get(13, middle)
        pinky = by_id.get(17, middle)
        mcp_y = (index["y"] + middle["y"] + ring["y"] + pinky["y"]) / 4.0
        wrist_y = float(wrist["y"])
        span_y = max(abs(wrist_y - mcp_y), 1e-4)
        palm_cx = (wrist["x"] + index["x"] + middle["x"] + pinky["x"]) / 4.0
        middle_mcp_x = float(middle["x"])
        ctx = {
            "mcp_y": mcp_y,
            "wrist_y": wrist_y,
            "span_y": span_y,
            "palm_cx": palm_cx,
            "middle_mcp_x": middle_mcp_x,
            "fate_axis_x": middle_mcp_x,
        }
        if len(landmarks) >= 21:
            corridor = proportional_fate_corridor(landmarks)
            ctx.update({
                "fate_corridor": corridor,
                "mcp_y": corridor["middle_mcp_y"],
                "wrist_y": corridor["wrist_y"],
                "span_y": max(span_y, corridor["span_y"]),
                "fate_axis_x": corridor["fate_axis_x"],
                "middle_mcp_x": corridor["fate_axis_x"],
            })
        return ctx

    @staticmethod
    def _image_arrays(
        context: dict,
        crease_masks: dict[str, np.ndarray] | None,
    ) -> dict:
        rgb = np.ascontiguousarray(context["processed_rgb"])
        raw_mask = context.get("palm_mask")
        if raw_mask is None:
            palm_mask = np.ones(rgb.shape[:2], dtype=np.uint8) * 255
        else:
            palm_mask = np.ascontiguousarray(raw_mask, dtype=np.uint8)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        enhanced = cv2.createCLAHE(2.0, (8, 8)).apply(gray)
        dark = cv2.morphologyEx(
            enhanced, cv2.MORPH_BLACKHAT,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
        )
        palm_pixels = dark[palm_mask > 0]
        threshold = max(12, int(np.percentile(palm_pixels, 70))) if palm_pixels.size else 255
        skeleton = None
        crease_binary = None
        if crease_masks:
            binary = crease_masks.get("blackhat_adaptive")
            if binary is not None:
                crease_binary = np.ascontiguousarray(binary, dtype=np.uint8)
                skeleton = cv2.ximgproc.thinning(binary) if hasattr(cv2, "ximgproc") else None
                if skeleton is None:
                    skeleton = np.uint8(binary > 0) * 255
        return {
            "crease_response": dark,
            "palm_mask": palm_mask,
            "response_threshold": threshold,
            "skeleton": skeleton,
            "crease_binary": crease_binary,
        }
