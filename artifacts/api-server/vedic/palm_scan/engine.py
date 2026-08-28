"""Deterministic Phase 1 palm scan orchestration and canonical JSON schema."""
from __future__ import annotations

import hashlib
import math
from typing import Any

import cv2
import numpy as np

from vedic.face_reading.image_io import decode_image

from .detectors import (
    ConservativeMarkingDetector,
    ConservativeCreaseDetector,
    HandDetection,
    HandLandmarkBackend,
    LineIdentityVerifier,
    MediaPipeHandsBackend,
    confidence_band,
)
from .fate_line_detector import FateLineDetector
from .life_line_trace import trace_life_line_fallback
from .physical_metrics import attach_scan_physical_metrics
from .preprocessing import preprocess
from .segmentation import segment_hand
from .semantic_verifier import default_line_verifier

SCHEMA_VERSION = "1.0"
RELIABLE_THRESHOLD = 0.55
MIN_MAJOR_LINE_PATH_POINTS = 4
FINGER_CHAINS = {
    "thumb": (1, 2, 3, 4),
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "little": (17, 18, 19, 20),
}
MAJOR_LINE_NAMES = (
    "heart_line", "head_line", "life_line", "fate_line",
    "sun_apollo_line", "mercury_line", "mars_support_line",
)
MOUNT_NAMES = (
    "Jupiter", "Saturn", "Sun/Apollo", "Mercury",
    "Upper Mars", "Lower Mars", "Venus", "Moon/Luna",
)


def _feature(status: str = "unknown", confidence: float = 0.0, **values: Any) -> dict:
    return {
        "status": status,
        "confidence": round(float(confidence), 4),
        "confidence_band": confidence_band(confidence),
        **values,
    }


def _unknown_features(names: tuple[str, ...], reason: str) -> dict:
    return {name: _feature(reason=reason) for name in names}


def _unknown_line(reason: str) -> dict:
    return _feature(
        reason=reason, detected=False, start_point=None, end_point=None,
        endpoints=[], path=[], length=None, normalized_length=None,
        depth=None, visibility_strength=None, thickness=None,
        clarity=None, continuity=None, curvature=None,
        direction=None, segments=[], breaks=[], gaps=[], branches=[],
        forks=[], islands=[], crosses_intersections=[],
        parallel_support_lines=[], tridents=[], chains=[],
        measurements={
            "strength_proxy": None,
            "depth_proxy": {"value": None, "label": "visibility_strength_not_physical_depth"},
            "visibility_strength": None,
            "clarity": None, "continuity": None, "curvature": None,
            "direction_degrees": None, "break_candidates": [],
            "branch_candidates": [], "fork_candidates": [],
            "island_candidates": [], "intersection_candidates": [],
            "parallel_candidates": [], "relative_position": "unknown",
        },
        methods=[], detector_agreement=0.0,
    )


def _unknown_finger(reason: str) -> dict:
    return _feature(
        reason=reason, length_normalized=None, raw_length_px=None,
        raw_segment_lengths_px=[], width_normalized=None, raw_width_px=None,
        relative_length=None, proportions=[], spacing_normalized=None,
        finger_to_palm_ratio=None,
        taper=None, tip_shape={
            "status": "unknown", "confidence": 0.0,
            "confidence_band": "unreliable",
        },
        straightness=None, joints=[], flexibility=_feature(
            reason="unsupported_from_static_image"
        ),
    )


def empty_result(*, scan_id: str, decoded=None, mirror_requested: bool = False) -> dict:
    dimensions = (
        {"width_px": decoded.width, "height_px": decoded.height,
         "original_width_px": decoded.original_width, "original_height_px": decoded.original_height}
        if decoded else {}
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "scan_id": scan_id,
            "engine": "palm_scan_phase1",
            "phase": 1,
            "deterministic": True,
            "source": "image_pixels",
            "mirror_requested": bool(mirror_requested),
            "mirror_applied": bool(decoded.mirror_applied) if decoded else False,
            "image_format": decoded.format if decoded else "unknown",
            "dimensions": dimensions,
            "notes": list(decoded.notes) if decoded else [],
        },
        "quality": {
            "status": "unknown", "usable": False, "score": 0.0,
            "metrics": {}, "issues": [], "gate": "not_evaluated",
        },
        "hand": _feature(
            reason="not_evaluated", side="unknown",
            handedness="unknown", source_label="unknown",
        ),
        "palm_geometry": _unknown_features(
            (
                "center", "width", "length", "aspect_ratio", "area",
                "perimeter", "palm_axis", "wrist_width", "overall_shape",
                "orientation", "finger_base_line", "wrist_boundary",
                "palm_boundary",
            ),
            "not_evaluated",
        ),
        "landmarks": [],
        "preprocessing": {"status": "not_evaluated", "artifacts": {}, "stages": {}},
        "segmentation": {
            name: _feature(reason="not_evaluated", polygon=[], mask_reference=None, mask_stats={})
            for name in ("hand_boundary", "palm_region", "fingers", "thumb", "wrist", "visible_palm")
        },
        "major_lines": {name: _unknown_line("semantic_model_unavailable") for name in MAJOR_LINE_NAMES},
        "secondary_lines": {
            "status": "unknown", "confidence": 0.0, "confidence_band": "unreliable",
            "reason": "semantic_model_unavailable", "crease_candidates": [],
        },
        "line_stitching": {
            "status": "not_evaluated",
            "confidence": 0.0,
            "confidence_band": "unreliable",
            "policy": "do_not_connect_without_local_image_evidence",
            "stitching_applied": False,
            "groups": [],
        },
        "mounts": {
            name: _feature(
                reason="not_evaluated", region_polygon=[], area_normalized=None,
                width_normalized=None, texture={}, line_density=None, markings=[],
                development=_feature(reason="monocular_rgb_cannot_measure_3d"),
                prominence=_feature(reason="monocular_rgb_cannot_measure_3d"),
                elevation=_feature(reason="monocular_rgb_cannot_measure_3d"),
                relative_elevation=_feature(reason="monocular_rgb_cannot_measure_3d"),
            ) for name in MOUNT_NAMES
        },
        "fingers": {name: _unknown_finger("not_evaluated") for name in FINGER_CHAINS if name != "thumb"},
        "thumb": {
            **_feature(reason="not_evaluated"),
            "length": _feature(reason="not_evaluated"),
            "width": _feature(reason="not_evaluated"),
            "spread_angle": _feature(reason="not_evaluated"),
            "phalanx_proportions": _feature(reason="not_evaluated"),
            "spacing": _feature(reason="not_evaluated"),
            "taper": _feature(reason="not_evaluated"),
            "tip_shape": _feature(reason="not_evaluated"),
            "straightness": _feature(reason="not_evaluated"),
            "joints": _feature(reason="not_evaluated"),
            "flexibility": _feature(reason="unsupported_from_static_image"),
            "opening_angle": _feature(reason="not_evaluated"),
            "first_phalanx": _feature(reason="not_evaluated"),
            "second_phalanx": _feature(reason="not_evaluated"),
            "venus_connection": _feature(reason="unsupported_from_static_image"),
        },
        "special_markings": {
            "status": "not_detected", "confidence": 0.0, "confidence_band": "unreliable",
            "reason": "no_validated_marking_classifier",
            "supported_types": [
                "star", "cross", "triangle", "square", "trident", "grille",
                "island", "fork", "dot", "vertical_line", "horizontal_line",
            ],
            "candidates": [],
        },
        "union_lines": {
            "status": "unknown", "confidence": 0.0, "confidence_band": "unreliable",
            "readable": False, "reason": "outer_edge_not_visible",
            "visible_major_line_count": None, "candidates": [],
        },
        "validation": {
            "status": "not_evaluated", "quality_gate": "not_evaluated",
            "issues": [], "policy": "unknown_over_unsupported_inference",
        },
        "scan_confidence": {
            "value": 0.0, "band": "unreliable", "reliable_threshold": RELIABLE_THRESHOLD,
            "is_reliable": False, "phase_2_eligible": False,
            "phase_2_reason": "quality_not_evaluated",
            "overall": 0.0, "major_lines": 0.0, "mounts": 0.0,
            "fingers": 0.0, "markings": 0.0,
            "groups": {
                "overall": 0.0, "major_lines": 0.0, "mounts": 0.0,
                "fingers": 0.0, "markings": 0.0,
            },
            "contributions": {
                "detector_agreement": 0.0, "segmentation_quality": 0.0,
                "image_quality": 0.0, "landmark_confidence": 0.0,
            },
            "eligible_features": {
                "major_lines": [], "mounts": [], "fingers": [], "markings": [],
            },
        },
        "annotated_image_reference": None,
        "processed_image_reference": None,
        "original_decoded_image_reference": None,
    }


class PalmScanEngine:
    def __init__(
        self,
        hand_backend: HandLandmarkBackend | None = None,
        crease_detector=None,
        marking_detector=None,
        line_verifier: LineIdentityVerifier | None = None,
    ):
        self.hand_backend = hand_backend or MediaPipeHandsBackend()
        self.crease_detector = crease_detector or ConservativeCreaseDetector()
        self.marking_detector = marking_detector or ConservativeMarkingDetector()
        self.line_verifier = (
            line_verifier if line_verifier is not None else default_line_verifier()
        )

    def scan(self, image_bytes: bytes, *, mirror: bool = False) -> tuple[dict, np.ndarray | None]:
        result, artifacts = self.scan_with_artifacts(image_bytes, mirror=mirror)
        return result, artifacts.get("annotated")

    def scan_with_artifacts(self, image_bytes: bytes, *, mirror: bool = False) -> tuple[dict, dict]:
        scan_id = hashlib.sha256(image_bytes).hexdigest()[:24] if image_bytes else "empty"
        decoded, error = decode_image(image_bytes, mirror=mirror)
        result = empty_result(scan_id=scan_id, decoded=decoded, mirror_requested=mirror)
        if error:
            result["quality"].update({
                "status": "unusable", "gate": "failed", "issues": [
                    {"code": error.split(" ", 1)[0], "severity": "error",
                     "message": "Upload a supported JPEG, PNG, WebP, GIF, BMP, TIFF, or HEIC image of at least 256px."}
                ],
            })
            result["scan_confidence"]["phase_2_reason"] = "decode_failed"
            result["validation"] = {
                "status": "rejected", "quality_gate": "failed",
                "issues": result["quality"]["issues"],
                "policy": "unknown_over_unsupported_inference",
            }
            return result, {}

        rgb = decoded.rgb
        detection = self.hand_backend.detect(rgb, pixels_are_mirrored=False)
        quality = self._quality(rgb, detection)
        result["quality"] = quality
        prepared = preprocess(
            rgb, detection.landmarks if detection else None,
            allow_perspective=quality["usable"],
        )
        result["preprocessing"] = {
            **prepared.metadata,
            "status": "processed",
        }
        artifact_prefix = f"/api/palm-scan/{scan_id}/artifacts"
        refs = {
            "original": f"{artifact_prefix}/original",
            "processed": f"{artifact_prefix}/processed",
            "normalized": f"{artifact_prefix}/normalized",
            "contrast_enhanced": f"{artifact_prefix}/contrast-enhanced",
            "crease_enhanced": f"{artifact_prefix}/crease-enhanced",
            "foreground_mask": f"{artifact_prefix}/foreground-mask",
            "background_removed": f"{artifact_prefix}/background-removed",
            "palm_segmented": f"{artifact_prefix}/palm-segmented",
            "edge_map": f"{artifact_prefix}/edge-map",
            "line_map": f"{artifact_prefix}/line-map",
            "skeleton_map": f"{artifact_prefix}/skeleton-map",
        }
        result["preprocessing"]["artifacts"] = refs
        result["preprocessing"]["variants"] = [
            "original", "normalized", "background_removed", "palm_segmented",
            "contrast_enhanced", "crease_enhanced", "edge_map", "line_map",
            "skeleton_map",
        ]
        result["original_decoded_image_reference"] = refs["original"]
        result["processed_image_reference"] = refs["processed"]
        background_removed = prepared.processed_rgb.copy()
        if prepared.foreground_mask is not None:
            background_removed[prepared.foreground_mask == 0] = 0
        artifacts = {
            "original": prepared.original_rgb,
            "processed": prepared.processed_rgb,
            "normalized": prepared.processed_rgb,
            "contrast-enhanced": prepared.crease_enhanced,
            "crease-enhanced": prepared.crease_enhanced,
            "foreground-mask": prepared.foreground_mask,
            "background-removed": background_removed,
        }
        if detection:
            detection = self._transform_detection(
                detection, prepared.metadata,
                prepared.processed_rgb.shape[:2],
            )
            result["landmarks"] = [
                {
                    **point,
                    "normalized_x": point["x"],
                    "normalized_y": point["y"],
                    "x_px": round(point["x"] * prepared.processed_rgb.shape[1], 3),
                    "y_px": round(point["y"] * prepared.processed_rgb.shape[0], 3),
                    "x_pixel": round(point["x"] * prepared.processed_rgb.shape[1], 3),
                    "y_pixel": round(point["y"] * prepared.processed_rgb.shape[0], 3),
                    "coordinate_space": "processed",
                    "confidence_band": confidence_band(point["confidence"]),
                }
                for point in detection.landmarks
            ]
            result["hand"] = _feature(
                "detected", detection.confidence,
                side=detection.handedness,
                handedness=detection.handedness,
                source_label=detection.source_handedness_label,
                handedness_basis="palmar_thumb_pinky_x",
                mediapipe_mirrored_input_assumption_corrected=True,
            )
        else:
            result["hand"] = _feature("not_detected", 0.0, reason="no_hand_landmarks",
                                      side="unknown", handedness="unknown",
                                      source_label="unknown")

        segmentation = None
        if detection:
            segmentation = segment_hand(
                prepared.processed_rgb.shape[:2], detection.landmarks,
                detection.confidence, prepared.foreground_mask,
            )
            result["segmentation"] = segmentation.sections
            for name, mask_value in segmentation.masks.items():
                key = f"segmentation-{name}"
                artifacts[key] = mask_value
                result["segmentation"][name]["mask_reference"] = f"{artifact_prefix}/{key}"
            artifacts["palm-segmented"] = segmentation.masks.get("palm_region")

        if not quality["usable"]:
            reason = "quality_gate_failed"
            result["palm_geometry"] = _unknown_features(tuple(result["palm_geometry"]), reason)
            result["fingers"] = {
                name: _unknown_finger(reason) for name in FINGER_CHAINS if name != "thumb"
            }
            result["thumb"]["status"] = "unknown"
            result["thumb"]["reason"] = reason
            result["scan_confidence"]["phase_2_reason"] = reason
            result["validation"] = {
                "status": "rejected", "quality_gate": "failed",
                "issues": quality["issues"],
                "policy": "unknown_over_unsupported_inference",
            }
            return result, artifacts

        assert detection is not None and segmentation is not None
        self._measure_anatomy(
            result, prepared.processed_rgb, detection,
            segmentation.masks, prepared.crease_enhanced,
        )
        mask = segmentation.masks["visible_palm"]
        crease_result = self.crease_detector.detect(prepared.processed_rgb, mask)
        if isinstance(crease_result, list):  # compatibility for injected Phase 1 fixtures
            crease_result = {
                "candidates": crease_result, "methods": {"injected": {"candidate_count": len(crease_result)}},
                "agreement": .5 if crease_result else 0.0, "masks": {},
            }
        candidates = crease_result["candidates"]
        for name, mask_value in crease_result.get("masks", {}).items():
            artifacts[f"crease-{name}"] = mask_value
            if name in crease_result.get("methods", {}):
                crease_result["methods"][name]["mask_reference"] = (
                    f"{artifact_prefix}/crease-{name}"
                )
        if crease_result.get("masks", {}).get("canny_ridge") is not None:
            artifacts["edge-map"] = crease_result["masks"]["canny_ridge"]
        if crease_result.get("masks", {}).get("blackhat_adaptive") is not None:
            artifacts["line-map"] = crease_result["masks"]["blackhat_adaptive"]
            artifacts["skeleton-map"] = crease_result["masks"]["blackhat_adaptive"]
        result["secondary_lines"] = {
            **_feature("detected" if candidates else "not_detected",
                       max((c["confidence"] for c in candidates), default=0.0)),
            "reason": "generic_observable_crease_candidates_only",
            "crease_candidates": candidates,
            "methods": crease_result.get("methods", {}),
            "detector_agreement": crease_result.get("agreement", 0.0),
        }
        result["major_lines"] = {
            name: _unknown_line("semantic_assignment_ambiguous")
            for name in MAJOR_LINE_NAMES
        }
        verification_status = "semantic_model_unavailable"
        if self.line_verifier is not None:
            try:
                assignments = self.line_verifier.verify(
                    candidates,
                    {
                        "hand": result["hand"],
                        "landmarks": result.get("landmarks") or [],
                        "palm_geometry": result["palm_geometry"],
                        "segmentation": result["segmentation"],
                        "quality": result["quality"],
                        # Runtime-only model input; never copied into result JSON.
                        "processed_rgb": prepared.processed_rgb,
                        "palm_mask": mask,
                    },
                )
                assignments.pop("fate_line", None)
                self._apply_line_assignments(result["major_lines"], candidates, assignments)
                evidence_status = getattr(
                    self.line_verifier, "last_evidence", {}
                ).get("status")
                if evidence_status == "model_unavailable":
                    verification_status = "semantic_model_unavailable"
                else:
                    # Keep the PalmScanResult 1.0 status enum stable. Detailed
                    # quality/no-candidate outcomes stay in model_evidence.
                    verification_status = "completed"
            except Exception:
                # A replaceable verifier must not make the deterministic scan
                # fail or manufacture named paths when it is unavailable.
                verification_status = "verifier_failed"
        try:
            self._apply_life_line_fallback(
                result["major_lines"],
                result.get("landmarks") or [],
                prepared.processed_rgb,
                mask,
                crease_result.get("masks") or {},
            )
        except Exception:
            pass
        if candidates:
            used_candidate_ids = {
                str(value.get("source_candidate_id") or "")
                for name, value in result["major_lines"].items()
                if name != "fate_line"
                and isinstance(value, dict)
                and value.get("source_candidate_id")
            }
        else:
            used_candidate_ids = set()
        fate_detector = (
            self.fate_line_detector
            if getattr(self, "fate_line_detector", None) is not None
            else FateLineDetector()
        )
        try:
            fate_out = fate_detector.detect(
                candidates,
                {
                    "landmarks": result.get("landmarks") or [],
                    "palm_geometry": result["palm_geometry"],
                    "processed_rgb": prepared.processed_rgb,
                    "palm_mask": mask,
                },
                crease_masks=crease_result.get("masks") or {},
                excluded_candidate_ids=used_candidate_ids,
            )
        except Exception as exc:
            fate_out = {
                "major_line": {
                    "status": "not_detected",
                    "validity": "not_detected",
                    "detected": False,
                    "reason": "fate_line_detector_failed",
                    "detection_method": FateLineDetector.detection_method,
                    "pipeline_revision": getattr(
                        FateLineDetector, "pipeline_revision", "unknown",
                    ),
                    "confidence": 0.0,
                    "path": [],
                },
                "debug": {
                    "status": "not_detected",
                    "method": FateLineDetector.detection_method,
                    "pipeline_revision": getattr(
                        FateLineDetector, "pipeline_revision", "unknown",
                    ),
                    "error": str(exc),
                    "candidate_audit": [],
                },
            }
        result["major_lines"]["fate_line"] = fate_out["major_line"]
        result["secondary_lines"]["fate_line_detection"] = fate_out["debug"]
        result["metadata"]["fate_line_pipeline"] = FateLineDetector.detection_method
        result["metadata"]["fate_line_pipeline_revision"] = (
            getattr(FateLineDetector, "pipeline_revision", "unknown")
        )
        if not candidates:
            result["metadata"]["fate_line_note"] = (
                "no_crease_candidates_used_corridor_fallback"
            )
        result["secondary_lines"]["semantic_verification"] = {
            "status": verification_status,
            "interface": "candidate_id_assignments_only",
            "coordinates_source": "crease_candidates",
            "model_evidence": dict(
                getattr(self.line_verifier, "last_evidence", {})
            ) if self.line_verifier is not None else {},
        }
        accepted_ids = {
            str(value.get("source_candidate_id") or "")
            for value in result["major_lines"].values()
            if isinstance(value, dict) and value.get("source_candidate_id")
        }
        for value in result["major_lines"].values():
            if not isinstance(value, dict):
                continue
            for candidate_id in value.get("source_candidate_ids") or []:
                if candidate_id:
                    accepted_ids.add(str(candidate_id))
        candidate_buckets = {
            "accepted": [],
            "rejected": [],
            "ambiguous": [],
            "missed_or_unresolved": [],
        }
        for candidate in result["secondary_lines"]["crease_candidates"]:
            candidate_id = str(candidate.get("id") or "")
            confidence = float(candidate.get("confidence") or 0.0)
            assigned = candidate_id in accepted_ids
            if assigned:
                audit_status = "accepted"
            elif confidence >= RELIABLE_THRESHOLD:
                audit_status = "missed_or_unresolved"
            elif confidence >= 0.35:
                audit_status = "ambiguous"
            else:
                audit_status = "rejected"
            candidate["audit_status"] = audit_status
            candidate["source_mapping"] = {
                "coordinates_source": "visible_image_crease_pixels",
                "classification_source": "line_identity_verifier",
                "accepted_as_major_line": assigned,
            }
            candidate_buckets[audit_status].append(candidate_id)
        result["secondary_lines"]["audit"] = {
            "status_buckets": candidate_buckets,
            "accepted_candidate_count": len(candidate_buckets["accepted"]),
            "rejected_candidate_count": len(candidate_buckets["rejected"]),
            "ambiguous_candidate_count": len(candidate_buckets["ambiguous"]),
            "missed_or_unresolved_candidate_count": len(candidate_buckets["missed_or_unresolved"]),
            "rule": "raw crease evidence is source of truth; unassigned visible candidates stay unresolved instead of fabricated into named lines",
        }
        result["line_stitching"] = self._build_line_stitching(
            result["secondary_lines"]["crease_candidates"]
        )
        result["special_markings"] = self.marking_detector.detect(crease_result)
        detector_agreement = float(crease_result.get("agreement", 0.0))
        seg_quality = segmentation.quality
        confidence = round(
            min(quality["score"], detection.confidence)
            * (.75 + .125 * detector_agreement + .125 * seg_quality), 4
        )
        mount_confidence = float(np.mean([
            value["confidence"] for value in result["mounts"].values()
        ]))
        finger_confidence = float(np.mean([
            value["confidence"] for value in result["fingers"].values()
        ]))
        marking_confidence = float(result["special_markings"]["confidence"])
        major_confidence = float(np.mean([
            value["confidence"] for value in result["major_lines"].values()
        ]))
        eligible_features = {
            "major_lines": [
                name for name, value in result["major_lines"].items()
                if value["confidence"] >= RELIABLE_THRESHOLD and value.get("detected")
            ],
            "mounts": [
                name for name, value in result["mounts"].items()
                if value["confidence"] >= RELIABLE_THRESHOLD
            ],
            "fingers": [
                name for name, value in result["fingers"].items()
                if value["confidence"] >= RELIABLE_THRESHOLD
            ],
            "markings": [
                value.get("type", "ambiguous")
                for value in result["special_markings"].get("candidates", [])
                if value.get("confidence", 0) >= RELIABLE_THRESHOLD
            ],
        }
        result["scan_confidence"] = {
            "value": confidence, "band": confidence_band(confidence),
            "reliable_threshold": RELIABLE_THRESHOLD,
            "is_reliable": confidence >= RELIABLE_THRESHOLD,
            "phase_2_eligible": confidence >= RELIABLE_THRESHOLD,
            "phase_2_reason": "eligible_measurement_only" if confidence >= RELIABLE_THRESHOLD else "below_reliable_threshold",
            "overall": confidence,
            "major_lines": round(major_confidence, 4),
            "mounts": round(mount_confidence, 4),
            "fingers": round(finger_confidence, 4),
            "markings": round(marking_confidence, 4),
            "groups": {
                "overall": confidence,
                "major_lines": round(major_confidence, 4),
                "mounts": round(mount_confidence, 4),
                "fingers": round(finger_confidence, 4),
                "markings": round(marking_confidence, 4),
            },
            "contributions": {
                "detector_agreement": round(detector_agreement, 4),
                "segmentation_quality": round(seg_quality, 4),
                "image_quality": quality["score"],
                "landmark_confidence": round(detection.confidence, 4),
            },
            "eligible_features": eligible_features,
        }
        result["validation"] = {
            "status": "accepted_measurements_only",
            "quality_gate": "passed", "issues": quality["issues"],
            "policy": "unknown_over_unsupported_inference",
        }
        attach_scan_physical_metrics(result)
        annotated = self._annotate_from_result(prepared.processed_rgb, result)
        result["annotated_image_reference"] = f"/api/palm-scan/{scan_id}/annotated"
        artifacts["annotated"] = annotated
        return result, artifacts

    @staticmethod
    def _build_line_stitching(candidates: list[dict]) -> dict:
        if not candidates:
            return {
                "status": "not_detected",
                "confidence": 0.0,
                "confidence_band": confidence_band(0.0),
                "policy": "do_not_connect_without_local_image_evidence",
                "stitching_applied": False,
                "groups": [],
            }
        groups = []
        for index, candidate in enumerate(candidates):
            confidence = float(candidate.get("confidence", 0.0))
            group_status = (
                "detected" if confidence >= RELIABLE_THRESHOLD
                else "ambiguous" if confidence >= 0.35
                else "probable"
            )
            groups.append({
                "group_id": f"continuity_group_{index + 1}",
                "status": group_status,
                "confidence": round(confidence, 4),
                "confidence_band": confidence_band(confidence),
                "source_candidate_ids": [candidate.get("id")],
                "path": list(candidate.get("path") or []),
                "segments": [
                    {
                        "candidate_id": candidate.get("id"),
                        "path": list(candidate.get("path") or []),
                        "confidence": round(confidence, 4),
                    }
                ],
                "start_point": candidate.get("start_point"),
                "end_point": candidate.get("end_point"),
                "length": candidate.get("length"),
                "normalized_length": candidate.get("normalized_length"),
                "curvature": candidate.get("curvature"),
                "continuity": candidate.get("continuity"),
                "thickness_estimate": candidate.get("thickness") or candidate.get("measurements", {}).get("width_px"),
                "local_image_evidence": candidate.get("raw_crease_evidence") or {},
                "stitch_reason": "single_fragment_preserved_without_forced_merge",
            })
        confidence = float(np.mean([group["confidence"] for group in groups])) if groups else 0.0
        return {
            "status": "detected",
            "confidence": round(confidence, 4),
            "confidence_band": confidence_band(confidence),
            "policy": "do_not_connect_without_local_image_evidence",
            "stitching_applied": False,
            "groups": groups,
        }

    @staticmethod
    def _apply_life_line_fallback(
        major_lines: dict,
        landmarks: list[dict],
        processed_rgb: np.ndarray,
        palm_mask: np.ndarray,
        crease_masks: dict[str, np.ndarray] | None,
    ) -> None:
        life = major_lines.get("life_line") or {}
        path = list(life.get("path") or [])
        status = str(life.get("status") or "unknown")
        needs_fallback = (
            len(path) < MIN_MAJOR_LINE_PATH_POINTS
            or status in {"unknown", "not_detected", "insufficient_geometry"}
            or (life.get("reason") == "semantic_assignment_ambiguous")
        )
        if not needs_fallback:
            return
        traced = trace_life_line_fallback(
            landmarks,
            processed_rgb,
            palm_mask,
            crease_masks=crease_masks,
        )
        if traced is None:
            return
        major_lines["life_line"] = {
            **life,
            **traced,
            "fallback_applied": True,
        }

    @staticmethod
    def _apply_line_assignments(
        named_lines: dict, candidates: list[dict], assignments: dict[str, dict]
    ) -> None:
        by_id = {candidate.get("id"): candidate for candidate in candidates}
        used_candidates: set[str] = set()
        for name, assignment in assignments.items():
            if name not in named_lines or not isinstance(assignment, dict):
                continue
            candidate_id = assignment.get("candidate_id")
            candidate = by_id.get(candidate_id)
            if candidate is None or candidate_id in used_candidates:
                continue
            verifier_confidence = float(np.clip(assignment.get("confidence", 0), 0, 1))
            candidate_confidence = float(candidate.get("confidence", 0))
            confidence = float(np.clip(
                0.35 * candidate_confidence + 0.65 * verifier_confidence, 0, 0.92
            ))
            measurements = candidate.get("measurements", {})
            endpoints = candidate.get("endpoints", [])
            path = list(candidate.get("path") or [])
            visibility = candidate.get(
                "clarity", measurements.get("clarity", measurements.get("strength_proxy"))
            )
            if len(path) < MIN_MAJOR_LINE_PATH_POINTS:
                named_lines[name] = _feature(
                    "insufficient_geometry",
                    confidence,
                    reason=(
                        f"path_has_{len(path)}_points_"
                        f"minimum_{MIN_MAJOR_LINE_PATH_POINTS}_required"
                    ),
                    detected=False,
                    start_point=candidate.get("start_point") or (endpoints[0] if endpoints else None),
                    end_point=candidate.get("end_point") or (endpoints[-1] if endpoints else None),
                    endpoints=endpoints,
                    path=path,
                    path_point_count=len(path),
                    length=candidate.get("length", measurements.get("length_px")),
                    normalized_length=candidate.get("normalized_length"),
                    methods=list(candidate.get("methods", [])) + ["line_identity_verifier"],
                    detector_agreement=candidate.get("detector_agreement", 0.0),
                    source_candidate_id=candidate_id,
                    source_layer=candidate.get("source_layer", "visible_palm"),
                    source_image_region=candidate.get("image_region"),
                    raw_crease_evidence=candidate.get("raw_crease_evidence"),
                    classification_confidence=round(verifier_confidence, 6),
                )
                used_candidates.add(candidate_id)
                continue
            reliable = bool(confidence >= RELIABLE_THRESHOLD)
            named_lines[name] = _feature(
                "detected" if reliable else "ambiguous", confidence,
                reason="candidate_and_verifier_agree" if reliable else "below_reliable_threshold",
                detected=reliable,
                start_point=candidate.get("start_point") or (endpoints[0] if endpoints else None),
                end_point=candidate.get("end_point") or (endpoints[-1] if endpoints else None),
                endpoints=endpoints,
                path=path,
                path_point_count=len(path),
                length=candidate.get("length", measurements.get("length_px")),
                normalized_length=candidate.get("normalized_length"),
                depth=None,
                visibility_strength=visibility,
                thickness=candidate.get("thickness", measurements.get("width_px")),
                clarity=visibility,
                continuity=candidate.get("continuity", measurements.get("continuity")),
                curvature=candidate.get("curvature", measurements.get("curvature")),
                direction=candidate.get("direction", measurements.get("direction_degrees")),
                segments=[],
                breaks=list(candidate.get("breaks", measurements.get("break_candidates", []))),
                gaps=list(candidate.get("gaps", measurements.get("gap_candidates", []))),
                branches=list(candidate.get("branches", measurements.get("branch_candidates", []))),
                forks=list(candidate.get("forks", measurements.get("fork_candidates", []))),
                islands=list(candidate.get("islands", measurements.get("island_candidates", []))),
                crosses_intersections=list(candidate.get(
                    "crosses_intersections", measurements.get("intersection_candidates", [])
                )),
                parallel_support_lines=list(candidate.get(
                    "parallel_support_lines", measurements.get("parallel_candidates", [])
                )),
                measurements={
                    **measurements,
                    "visibility_strength": visibility,
                    "depth_proxy": {
                        "value": visibility,
                        "label": "visibility_strength_not_physical_depth",
                    },
                },
                methods=list(candidate.get("methods", [])) + ["line_identity_verifier"],
                detector_agreement=candidate.get("detector_agreement", 0.0),
                source_candidate_id=candidate_id,
                source_layer=candidate.get("source_layer", "visible_palm"),
                source_image_region=candidate.get("image_region"),
                raw_crease_evidence=candidate.get("raw_crease_evidence"),
                classification_confidence=round(verifier_confidence, 6),
            )
            used_candidates.add(candidate_id)

    @staticmethod
    def _transform_detection(
        detection: HandDetection, metadata: dict, output_shape: tuple[int, int]
    ) -> HandDetection:
        stage = metadata["stages"]["perspective_normalization"]
        matrix = np.float32(stage["homography"])
        points = np.float32([(p["x"], p["y"]) for p in detection.landmarks])
        height, width = output_shape
        pixel_points = points * np.float32([width, height])
        transformed = cv2.perspectiveTransform(pixel_points[None, :, :], matrix)[0]
        normalized = transformed / np.float32([width, height])
        landmarks = [
            {**point, "x": round(float(np.clip(x, 0, 1)), 8),
             "y": round(float(np.clip(y, 0, 1)), 8)}
            for point, (x, y) in zip(detection.landmarks, normalized)
        ]
        return HandDetection(
            landmarks, detection.handedness, detection.confidence,
            detection.source_handedness_label,
        )

    def _quality(self, rgb: np.ndarray, detection: HandDetection | None) -> dict:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        height, width = gray.shape
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        blur_region = gray
        if detection and len(detection.landmarks) == 21:
            xs = [float(point["x"]) * width for point in detection.landmarks]
            ys = [float(point["y"]) * height for point in detection.landmarks]
            x0 = max(0, int(min(xs) - 16))
            x1 = min(width, int(max(xs) + 16))
            y0 = max(0, int(min(ys) - 16))
            y1 = min(height, int(max(ys) + 16))
            roi = gray[y0:y1, x0:x1]
            if roi.size >= 400:
                blur_region = roi
        blur = float(cv2.Laplacian(blur_region, cv2.CV_64F).var())
        issues: list[dict] = []
        if min(width, height) < 480:
            issues.append({"code": "resolution_low", "severity": "error", "message": "Use an image at least 480px on its short edge."})
        if brightness < 45:
            issues.append({"code": "low_light", "severity": "error", "message": "Retake in brighter, even light."})
        elif brightness > 235:
            issues.append({"code": "overexposed", "severity": "error", "message": "Reduce glare and direct flash."})
        if contrast < 18:
            issues.append({"code": "low_contrast", "severity": "error", "message": "Use even light and a contrasting background."})
        if blur < 12:
            issues.append({
                "code": "blurred",
                "severity": "error",
                "message": "This uploaded photo is too soft to measure palm lines. Choose a sharper, well-lit still image.",
            })
        elif blur < 40:
            issues.append({
                "code": "blurred",
                "severity": "warning",
                "message": "The uploaded photo is a bit soft from compression. A sharper still image will improve line measurements.",
            })

        palm_visible = finger_visible = wrist_visible = False
        orientation = openness = _feature(reason="hand_not_detected")
        occlusion = _feature(reason="cannot_assess_without_hand")
        if detection and len(detection.landmarks) == 21:
            if detection.confidence < 0.65:
                issues.append({
                    "code": "low_hand_detection_confidence",
                    "severity": "error",
                    "message": (
                        "The uploaded image is not confidently recognized as "
                        "one open hand. Upload a clear palm-only photo."
                    ),
                })
            points = np.array([(p["x"], p["y"]) for p in detection.landmarks])
            palm_visible = bool(all(
                0.02 < float(points[i, 0]) < 0.98 and 0.02 < float(points[i, 1]) < 0.98
                for i in (0, 5, 9, 13, 17)
            ))
            visible_tips = sum(
                0.015 < float(points[i, 0]) < 0.985 and 0.015 < float(points[i, 1]) < 0.985
                for i in (4, 8, 12, 16, 20)
            )
            finger_visible = visible_tips == 5
            wrist_visible = bool(
                0.01 < float(points[0, 0]) < 0.99 and 0.01 < float(points[0, 1]) < 0.99
            )
            palm_axis = points[9] - points[0]
            angle = math.degrees(math.atan2(float(palm_axis[0]), float(-palm_axis[1])))
            orientation = _feature("detected", detection.confidence, angle_from_vertical_deg=round(angle, 3))
            palm_scale = max(float(np.linalg.norm(points[5] - points[17])), 1e-6)
            spread = float(np.mean([np.linalg.norm(points[i] - points[9]) for i in (4, 8, 12, 16, 20)]) / palm_scale)
            openness = _feature("detected", detection.confidence, normalized_tip_spread=round(spread, 4),
                                category="open" if spread >= 1.05 else "partly_closed")
            occlusion = _feature("unknown", 0.0, reason="single_rgb_view_cannot_disambiguate_occlusion")
            if not palm_visible:
                issues.append({"code": "palm_cropped", "severity": "error", "message": "Keep the full palm and wrist inside the frame."})
            if not finger_visible:
                issues.append({"code": "fingers_hidden_or_cropped", "severity": "error", "message": "Show all five fingertips with fingers separated."})
            if not wrist_visible:
                issues.append({"code": "wrist_not_visible", "severity": "error", "message": "Include the wrist boundary."})
            if abs(angle) > 55:
                issues.append({"code": "extreme_orientation", "severity": "error", "message": "Align fingers toward the top of the image."})
            if spread < 0.82:
                issues.append({"code": "hand_not_open", "severity": "error", "message": "Open and gently separate all fingers."})
        else:
            issues.append({"code": "hand_not_detected", "severity": "error", "message": "Photograph one open palm against a plain background."})

        usable = not any(i["severity"] == "error" for i in issues)
        score = float(np.clip(
            0.25 * min(blur / 120.0, 1.0)
            + 0.20 * min(contrast / 45.0, 1.0)
            + 0.15 * (1.0 - min(abs(brightness - 135.0) / 135.0, 1.0))
            + 0.40 * (1.0 if palm_visible and finger_visible and wrist_visible else 0.0),
            0.0, 1.0,
        ))
        return {
            "status": "usable" if usable else "unusable", "usable": usable,
            "score": round(score, 4), "overall_score": round(score, 4),
            "resolution_score": round(min(min(width, height) / 720.0, 1.0), 4),
            "blur_score": round(min(blur / 120.0, 1.0), 4),
            "lighting_score": round(
                1.0 - min(abs(brightness - 135.0) / 135.0, 1.0), 4
            ),
            "visibility_score": 1.0 if palm_visible and finger_visible and wrist_visible else 0.0,
            "occlusion_score": None,
            "gate": "passed" if usable else "failed",
            "metrics": {
                "dimensions": _feature("detected", 1.0, width_px=width, height_px=height,
                                       short_edge_px=min(width, height)),
                "resolution": _feature(
                    "detected", 1.0, total_pixels=width * height,
                    megapixels=round((width * height) / 1_000_000.0, 4),
                    meets_minimum=bool(min(width, height) >= 480),
                ),
                "blur": _feature("detected", 1.0, laplacian_variance=round(blur, 3)),
                "brightness": _feature("detected", 1.0, mean_luma=round(brightness, 3)),
                "contrast": _feature("detected", 1.0, luma_stddev=round(contrast, 3)),
                "palm_visibility": _feature("detected" if detection else "not_detected",
                                            detection.confidence if detection else 0.0,
                                            visible=palm_visible,
                                            estimated_percentage=1.0 if palm_visible else 0.0,
                                            method="landmark_boundary_proxy"),
                "finger_visibility": _feature("detected" if detection else "not_detected",
                                              detection.confidence if detection else 0.0, all_tips_visible=finger_visible),
                "wrist_visibility": _feature("detected" if detection else "not_detected",
                                             detection.confidence if detection else 0.0, visible=wrist_visible),
                "occlusion": occlusion, "orientation": orientation, "openness": openness,
                "flatness": _feature("unknown", 0.0, reason="unsupported_from_single_monocular_rgb"),
                "glare": _feature(
                    "detected", 1.0,
                    highlight_fraction=round(float(np.mean(gray > 245)), 4),
                ),
                "shadows": _feature(
                    "detected", 1.0,
                    dark_fraction=round(float(np.mean(gray < 28)), 4),
                ),
                "compression": _feature(
                    "detected", 1.0,
                    laplacian_variance=round(blur, 3),
                    note="uploaded_still_softness_proxy",
                ),
                "focus": _feature(
                    "detected", 1.0,
                    laplacian_variance=round(blur, 3),
                ),
                "thumb_visibility": _feature(
                    "detected" if detection else "not_detected",
                    detection.confidence if detection else 0.0,
                    visible=bool(
                        detection and 0.015 < float(detection.landmarks[4]["x"]) < 0.985
                        and 0.015 < float(detection.landmarks[4]["y"]) < 0.985
                    ) if detection and len(detection.landmarks) == 21 else False,
                ),
                "cropping": _feature(
                    "detected" if detection else "unknown",
                    detection.confidence if detection else 0.0,
                    palm_inside_frame=palm_visible,
                    fingers_inside_frame=finger_visible,
                    wrist_inside_frame=wrist_visible,
                ),
                "rotation": orientation,
                "perspective": _feature(
                    "unknown", 0.0,
                    reason="single_view_cannot_measure_true_perspective_distortion",
                ),
                "background_interference": _feature(
                    "unknown", 0.0,
                    reason="background_classifier_not_calibrated",
                ),
                "finger_overlap": _feature(
                    "unknown", 0.0,
                    reason="overlap_not_confirmed_from_2d_landmarks_alone",
                ),
                "lines_obscured": _feature(
                    "unknown", 0.0,
                    reason="cannot_prove_crease_occlusion_without_clear_ridge_map",
                ),
            },
            "issues": issues,
        }

    def _measure_anatomy(
        self, result: dict, rgb: np.ndarray, detection: HandDetection,
        masks: dict[str, np.ndarray], crease_enhanced: np.ndarray,
    ) -> None:
        height, width = rgb.shape[:2]
        points = np.array([(p["x"], p["y"]) for p in detection.landmarks], dtype=float)
        px = points * np.array([width, height])
        confidence = detection.confidence
        palm_width = float(np.linalg.norm(px[5] - px[17]))
        palm_length = float(np.linalg.norm(px[0] - px[9]))
        hull = cv2.convexHull(np.float32(px[[0, 1, 5, 9, 13, 17]]))
        area = float(cv2.contourArea(hull))
        perimeter = float(cv2.arcLength(hull, True))
        wrist_width = float(np.linalg.norm(px[5] - px[17]) * 0.72)
        palm_axis_angle = math.degrees(math.atan2(
            float(points[9][0] - points[0][0]),
            float(-(points[9][1] - points[0][1])),
        ))
        aspect = palm_width / max(palm_length, 1e-6)
        shape_label = "square" if 0.85 <= aspect <= 1.15 else "rectangular"
        result["palm_geometry"] = {
            "center": _feature(
                "detected", confidence,
                normalized=[
                    round(float(np.mean(points[[0, 5, 9, 13, 17]], axis=0)[0]), 6),
                    round(float(np.mean(points[[0, 5, 9, 13, 17]], axis=0)[1]), 6),
                ],
            ),
            "width": _feature("detected", confidence, normalized=round(palm_width / width, 6), raw_px=round(palm_width, 3)),
            "length": _feature("detected", confidence, normalized=round(palm_length / height, 6), raw_px=round(palm_length, 3)),
            "aspect_ratio": _feature("detected", confidence, raw_ratio=round(aspect, 5)),
            "area": _feature("detected", confidence, normalized=round(area / (width * height), 6), raw_px2=round(area, 3)),
            "perimeter": _feature(
                "detected", confidence,
                normalized=round(perimeter / max(width + height, 1e-6), 6),
                raw_px=round(perimeter, 3),
            ),
            "palm_axis": _feature(
                "detected", confidence,
                start={"x": round(float(points[0][0]), 6), "y": round(float(points[0][1]), 6)},
                end={"x": round(float(points[9][0]), 6), "y": round(float(points[9][1]), 6)},
                angle_from_vertical_deg=round(palm_axis_angle, 3),
            ),
            "wrist_width": _feature(
                "detected", confidence,
                normalized=round(wrist_width / width, 6),
                raw_px=round(wrist_width, 3),
                method="finger_base_width_proxy",
            ),
            "overall_shape": _feature(
                "detected", confidence,
                classification=shape_label,
                method="width_to_length_geometry",
            ),
            "orientation": result["quality"]["metrics"]["orientation"],
            "finger_base_line": _feature(
                "detected", confidence,
                path=[
                    {"x": round(float(points[index][0]), 6),
                     "y": round(float(points[index][1]), 6)}
                    for index in (5, 9, 13, 17)
                ],
            ),
            "wrist_boundary": _feature(
                result["segmentation"]["wrist"]["status"],
                result["segmentation"]["wrist"]["confidence"],
                polygon=result["segmentation"]["wrist"]["polygon"],
            ),
            "palm_boundary": _feature(
                result["segmentation"]["palm_region"]["status"],
                result["segmentation"]["palm_region"]["confidence"],
                polygon=result["segmentation"]["palm_region"]["polygon"],
            ),
        }
        distance = cv2.distanceTransform(masks["hand_boundary"], cv2.DIST_L2, 5)
        finger_values = {}
        for name, chain in FINGER_CHAINS.items():
            segments = [float(np.linalg.norm(px[b] - px[a])) for a, b in zip(chain, chain[1:])]
            total = sum(segments)
            pip_index = chain[1]
            tip_index = chain[-1]
            pip_xy = np.int32(np.clip(px[pip_index], [0, 0], [width - 1, height - 1]))
            tip_xy = np.int32(np.clip(px[tip_index], [0, 0], [width - 1, height - 1]))
            width_px = float(distance[pip_xy[1], pip_xy[0]] * 2)
            tip_width_px = float(distance[tip_xy[1], tip_xy[0]] * 2)
            taper = tip_width_px / max(width_px, 1e-6)
            straightness = float(np.linalg.norm(px[chain[-1]] - px[chain[0]]) / max(total, 1e-6))
            tip_label = "tapered" if taper < .72 else ("broad" if taper > 1.12 else "rounded_or_square_ambiguous")
            finger_values[name] = _feature(
                "detected", confidence, length_normalized=round(total / height, 6),
                raw_length_px=round(total, 3), raw_segment_lengths_px=[round(v, 3) for v in segments],
                width_normalized=round(width_px / width, 6), raw_width_px=round(width_px, 3),
                relative_length=None,
                finger_to_palm_ratio=round(total / max(palm_length, 1e-6), 5),
                proportions=[round(value / max(total, 1e-6), 5) for value in segments],
                phalanx_lengths_px=[round(v, 3) for v in segments],
                spacing_normalized=None,
                taper=round(taper, 4),
                tip_location={
                    "x": round(float(points[tip_index][0]), 6),
                    "y": round(float(points[tip_index][1]), 6),
                },
                tip_shape={
                    "status": "detected" if tip_label != "rounded_or_square_ambiguous" else "ambiguous",
                    "classification": tip_label,
                    "confidence": round(confidence * .65, 4),
                    "confidence_band": confidence_band(confidence * .65),
                    "method": "segmentation_width_geometry_proxy",
                },
                straightness=round(straightness, 5),
                joints=[
                    {"landmark_id": index, "x": round(points[index][0], 6),
                     "y": round(points[index][1], 6)}
                    for index in chain[1:-1]
                ],
                flexibility=_feature("unknown", 0.0, reason="unsupported_from_static_image"),
            )
        longest = max(value["raw_length_px"] for value in finger_values.values())
        ordered = ("index", "middle", "ring", "little")
        for position, name in enumerate(ordered):
            value = finger_values[name]
            value["relative_length"] = round(value["raw_length_px"] / max(longest, 1e-6), 5)
            if position < len(ordered) - 1:
                next_name = ordered[position + 1]
                spacing = float(np.linalg.norm(
                    px[FINGER_CHAINS[name][-1]] - px[FINGER_CHAINS[next_name][-1]]
                ) / max(palm_width, 1e-6))
                value["spacing_normalized"] = round(spacing, 5)
        result["fingers"] = {name: finger_values[name] for name in ordered}
        thumb_vector = px[4] - px[2]
        index_vector = px[5] - px[2]
        denom = max(np.linalg.norm(thumb_vector) * np.linalg.norm(index_vector), 1e-9)
        angle = math.degrees(math.acos(float(np.clip(np.dot(thumb_vector, index_vector) / denom, -1, 1))))
        result["thumb"] = {
            **_feature("detected", confidence),
            "length": _feature(
                "detected", confidence,
                normalized=finger_values["thumb"]["length_normalized"],
                raw_px=finger_values["thumb"]["raw_length_px"],
                relative_to_middle=round(
                    finger_values["thumb"]["raw_length_px"]
                    / max(finger_values["middle"]["raw_length_px"], 1e-6), 5
                ),
            ),
            "width": _feature(
                "detected", confidence,
                normalized=finger_values["thumb"]["width_normalized"],
                raw_px=finger_values["thumb"]["raw_width_px"],
            ),
            "spread_angle": _feature("detected", confidence, raw_degrees=round(angle, 3)),
            "phalanx_proportions": _feature(
                "detected", confidence, values=finger_values["thumb"]["proportions"]
            ),
            "spacing": _feature(
                "detected", confidence,
                normalized=round(float(np.linalg.norm(px[4] - px[8]) / max(palm_width, 1e-6)), 5),
            ),
            "taper": _feature("detected", confidence, ratio=finger_values["thumb"]["taper"]),
            "tip_shape": finger_values["thumb"]["tip_shape"],
            "straightness": _feature(
                "detected", confidence, ratio=finger_values["thumb"]["straightness"]
            ),
            "joints": _feature("detected", confidence, points=finger_values["thumb"]["joints"]),
            "flexibility": _feature("unknown", 0.0, reason="unsupported_from_static_image"),
            "opening_angle": _feature("detected", confidence, raw_degrees=round(angle, 3)),
            "first_phalanx": _feature(
                "detected", confidence,
                ratio=(finger_values["thumb"]["proportions"] or [None])[0],
            ),
            "second_phalanx": _feature(
                "detected" if len(finger_values["thumb"]["proportions"]) > 1 else "unknown",
                confidence if len(finger_values["thumb"]["proportions"]) > 1 else 0.0,
                ratio=(finger_values["thumb"]["proportions"][1]
                       if len(finger_values["thumb"]["proportions"]) > 1 else None),
            ),
            "venus_connection": _feature(
                "unknown", 0.0, reason="static_image_cannot_confirm_mount_attachment"
            ),
        }
        center = np.mean(points[[0, 5, 9, 13, 17]], axis=0)
        mount_regions = {
            "Jupiter": np.array([points[5], points[6], (points[5] + center) / 2, (points[9] + center) / 2]),
            "Saturn": np.array([points[9], points[10], (points[9] + center) / 2, (points[13] + center) / 2]),
            "Sun/Apollo": np.array([points[13], points[14], (points[13] + center) / 2, (points[17] + center) / 2]),
            "Mercury": np.array([points[17], points[18], (points[17] + center) / 2, center]),
            "Upper Mars": np.array([points[17], center, (points[17] + points[0]) / 2]),
            "Lower Mars": np.array([points[5], points[2], center, (points[5] + points[0]) / 2]),
            "Venus": np.array([points[1], points[2], points[5], center, points[0]]),
            "Moon/Luna": np.array([points[0], center, points[13], points[17]]),
        }
        result["mounts"] = {
            name: self._texture_region(
                rgb, region, confidence * .78, crease_enhanced
            ) for name, region in mount_regions.items()
        }

    @staticmethod
    def _texture_region(
        rgb: np.ndarray, region: np.ndarray, confidence: float,
        crease_enhanced: np.ndarray,
    ) -> dict:
        height, width = rgb.shape[:2]
        polygon = np.int32(region * np.array([width, height]))
        mask = np.zeros((height, width), np.uint8)
        cv2.fillConvexPoly(mask, polygon, 255)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        values = gray[mask > 0]
        if not len(values):
            return _feature("not_detected", 0.0, reason="empty_region",
                            region_polygon=[], area_normalized=0.0,
                            width_normalized=0.0, texture={},
                            line_density=None, markings=[],
                            development=_feature(
                                reason="monocular_rgb_cannot_measure_3d"
                            ),
                            prominence=_feature(
                                reason="monocular_rgb_cannot_measure_3d"
                            ),
                            elevation=_feature(
                                reason="monocular_rgb_cannot_measure_3d"
                            ),
                            relative_elevation=_feature(
                                reason="monocular_rgb_cannot_measure_3d"
                            ))
        texture = float(cv2.Laplacian(gray, cv2.CV_64F)[mask > 0].var())
        responses = crease_enhanced[mask > 0]
        threshold = max(10.0, float(np.percentile(responses, 75)))
        line_density = float(np.mean(responses >= threshold))
        return _feature(
            "detected", confidence,
            region_polygon=[
                {"x": round(float(x), 6), "y": round(float(y), 6)}
                for x, y in region
            ],
            area_normalized=round(len(values) / mask.size, 6),
            width_normalized=round(
                float(np.ptp(region[:, 0])) if len(region) else 0.0, 6
            ),
            texture={
                "mean_luma": round(float(np.mean(values)), 3),
                "laplacian_variance": round(texture, 3),
                "label": "pixel_texture_proxy",
            },
            line_density=round(line_density, 5), markings=[],
            development=_feature(
                "unknown", 0.0, reason="monocular_rgb_cannot_measure_3d"
            ),
            prominence=_feature("unknown", 0.0, reason="monocular_rgb_cannot_measure_3d"),
            elevation=_feature("unknown", 0.0, reason="monocular_rgb_cannot_measure_3d"),
            relative_elevation=_feature(
                "unknown", 0.0, reason="monocular_rgb_cannot_measure_3d"
            ),
        )

    @staticmethod
    def _palm_mask(shape: tuple[int, int], landmarks: list[dict]) -> np.ndarray:
        height, width = shape
        points = np.array([(p["x"] * width, p["y"] * height) for p in landmarks], np.int32)
        mask = np.zeros((height, width), np.uint8)
        cv2.fillConvexPoly(mask, cv2.convexHull(points[[0, 1, 2, 5, 9, 13, 17]]), 255)
        return mask

    @staticmethod
    def _annotate_from_result(rgb: np.ndarray, result: dict) -> np.ndarray:
        output = cv2.cvtColor(rgb.copy(), cv2.COLOR_RGB2BGR)
        height, width = rgb.shape[:2]
        palm_polygon = result.get("segmentation", {}).get("palm_region", {}).get("polygon", [])
        if len(palm_polygon) >= 3:
            polygon = np.array([
                (round(point["x"] * width), round(point["y"] * height))
                for point in palm_polygon
            ], np.int32)
            cv2.polylines(output, [polygon], True, (180, 180, 180), 1)
        mount_colors = [
            (255, 120, 60), (220, 160, 40), (180, 200, 40), (120, 220, 80),
            (60, 220, 180), (60, 170, 240), (150, 100, 240), (220, 80, 180),
        ]
        for color, mount in zip(mount_colors, result.get("mounts", {}).values()):
            region = mount.get("region_polygon", [])
            if mount.get("status") == "detected" and len(region) >= 3:
                polygon = np.array([
                    (round(point["x"] * width), round(point["y"] * height))
                    for point in region
                ], np.int32)
                cv2.polylines(output, [polygon], True, color, 1)
        for point in result["landmarks"]:
            if point.get("status") == "detected":
                cv2.circle(output, (round(point["x"] * width), round(point["y"] * height)), 3, (0, 220, 0), -1)
        major_line_colors = {
            "heart_line": (80, 80, 255),
            "head_line": (255, 160, 40),
            "life_line": (80, 220, 80),
            "fate_line": (220, 80, 220),
            "sun_apollo_line": (40, 210, 255),
            "mercury_line": (220, 220, 80),
            "mars_support_line": (120, 120, 255),
        }
        for name, line in result.get("major_lines", {}).items():
            path_points = line.get("path", [])
            if line.get("status") == "detected" and len(path_points) >= 2:
                path = np.array([
                    (round(point["x"] * width), round(point["y"] * height))
                    for point in path_points
                ], np.int32)
                cv2.polylines(
                    output, [path], False,
                    major_line_colors.get(name, (255, 255, 255)), 2,
                )
        for candidate in result["secondary_lines"]["crease_candidates"]:
            path = np.array([(round(p["x"] * width), round(p["y"] * height)) for p in candidate["path"]], np.int32)
            if len(path) >= 2:
                cv2.polylines(output, [path], False, (255, 180, 0), 1)
        for marking in result.get("special_markings", {}).get("candidates", []):
            for point in marking.get("coordinates", []):
                cv2.drawMarker(
                    output,
                    (round(point["x"] * width), round(point["y"] * height)),
                    (0, 0, 255), cv2.MARKER_CROSS, 7, 1,
                )
        return output
