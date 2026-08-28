"""Two-hand comparison over two validated PalmScanResult objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .engine import PalmistryPhase2Engine
from .rules import DOMAINS
from .schema import prepare_for_phase2, validate_palm_scan_result

BILATERAL_SCHEMA_VERSION = "palmistry_bilateral/1.0"


@dataclass(frozen=True)
class ComparisonSpec:
    comparison_id: str
    path: str
    feature_path: str
    family: str
    domain: str
    threshold: float


COMPARISON_SPECS = (
    ComparisonSpec(
        "heart_clarity", "major_lines.heart_line.measurements.clarity",
        "major_lines.heart_line", "major_line", "love_relationships", .10,
    ),
    ComparisonSpec(
        "heart_continuity", "major_lines.heart_line.measurements.continuity",
        "major_lines.heart_line", "major_line", "love_relationships", .10,
    ),
    ComparisonSpec(
        "head_clarity", "major_lines.head_line.measurements.clarity",
        "major_lines.head_line", "major_line", "personality", .10,
    ),
    ComparisonSpec(
        "head_curvature", "major_lines.head_line.measurements.curvature",
        "major_lines.head_line", "major_line", "personality", .10,
    ),
    ComparisonSpec(
        "life_continuity", "major_lines.life_line.measurements.continuity",
        "major_lines.life_line", "major_line", "traditional_vitality", .10,
    ),
    ComparisonSpec(
        "fate_clarity", "major_lines.fate_line.measurements.clarity",
        "major_lines.fate_line", "major_line", "career", .10,
    ),
    ComparisonSpec(
        "sun_clarity", "major_lines.sun_apollo_line.measurements.clarity",
        "major_lines.sun_apollo_line", "major_line",
        "recognition_success", .10,
    ),
    ComparisonSpec(
        "mercury_clarity", "major_lines.mercury_line.measurements.clarity",
        "major_lines.mercury_line", "major_line", "money", .10,
    ),
    ComparisonSpec(
        "palm_aspect_ratio", "palm_geometry.aspect_ratio.raw_ratio",
        "palm_geometry.aspect_ratio", "hand_structure", "personality", .08,
    ),
    ComparisonSpec(
        "thumb_spread", "thumb.spread_angle.raw_degrees",
        "thumb.spread_angle", "thumb_structure", "personality", 8.0,
    ),
)


class BilateralPalmistryEngine:
    def __init__(
        self,
        *,
        single_engine: PalmistryPhase2Engine | None = None,
        reliable_threshold: float = .55,
    ):
        self.single_engine = single_engine or PalmistryPhase2Engine(
            reliable_threshold=reliable_threshold
        )
        self.reliable_threshold = reliable_threshold

    def analyze(
        self,
        *,
        left_palm_scan_result: dict[str, Any],
        right_palm_scan_result: dict[str, Any],
        writing_hand: str,
    ) -> dict[str, Any]:
        left_palm_scan_result = prepare_for_phase2(left_palm_scan_result)
        right_palm_scan_result = prepare_for_phase2(right_palm_scan_result)
        issues = self._validate_inputs(
            left_palm_scan_result, right_palm_scan_result, writing_hand
        )
        if issues:
            return self._insufficient(issues, writing_hand)
        scans = {
            "left": left_palm_scan_result,
            "right": right_palm_scan_result,
        }
        dominant_side = writing_hand
        non_dominant_side = "left" if dominant_side == "right" else "right"
        dominant_scan = scans[dominant_side]
        non_dominant_scan = scans[non_dominant_side]
        dominant_reading = self.single_engine.analyze(dominant_scan)
        non_dominant_reading = self.single_engine.analyze(non_dominant_scan)
        if (
            dominant_reading["status"] == "insufficient_data"
            or non_dominant_reading["status"] == "insufficient_data"
        ):
            return self._insufficient([{
                "code": "hand_interpretation_insufficient",
                "path": "hands",
                "message": (
                    "Both hands need independently eligible measurements for "
                    "a bilateral reading."
                ),
                "dominant_status": dominant_reading["status"],
                "non_dominant_status": non_dominant_reading["status"],
            }], writing_hand)

        comparisons = self._compare(dominant_scan, non_dominant_scan)
        combined_domains = self._combine_domains(
            dominant_reading, non_dominant_reading, comparisons
        )
        paired_confidence = min(
            (item["confidence"] for item in comparisons),
            default=min(
                _scan_confidence(dominant_scan),
                _scan_confidence(non_dominant_scan),
            ),
        )
        scan_confidence = min(
            _scan_confidence(dominant_scan),
            _scan_confidence(non_dominant_scan),
            _feature_confidence(dominant_scan.get("hand", {})),
            _feature_confidence(non_dominant_scan.get("hand", {})),
            paired_confidence,
        )
        result = {
            "schema_version": BILATERAL_SCHEMA_VERSION,
            "status": "ok",
            "metadata": {
                "engine": "palmistry_bilateral/1.0",
                "input_contract": "two PalmScanResult/1.0 JSON objects",
                "image_or_artifact_consumed": False,
                "writing_hand_source": "explicit_user_answer",
                "dominant_side": dominant_side,
                "non_dominant_side": non_dominant_side,
                "dominant_role": "current_or_developed_symbolism",
                "non_dominant_role": "baseline_or_underlying_symbolism",
                "traditional_non_scientific": True,
                "deterministic": True,
            },
            "reading_completeness": {
                "mode": "bilateral",
                "score": 1.0,
                "bilateral_comparison_available": True,
                "missing_hands": [],
            },
            "confidence_policy": {
                "formula": (
                    "min(left_scan, right_scan, left_handedness, "
                    "right_handedness, paired_feature_confidence)"
                ),
                "never_upgrades_source_confidence": True,
            },
            "confidence": round(scan_confidence, 4),
            "hands": {
                "dominant": {
                    "side": dominant_side,
                    "scan_id": dominant_scan["metadata"].get("scan_id"),
                    "role": "current_or_developed_symbolism",
                    "reading": dominant_reading,
                },
                "non_dominant": {
                    "side": non_dominant_side,
                    "scan_id": non_dominant_scan["metadata"].get("scan_id"),
                    "role": "baseline_or_underlying_symbolism",
                    "reading": non_dominant_reading,
                },
            },
            "comparisons": comparisons,
            "combined_domains": combined_domains,
        }
        result["narration"] = _narrate(result)
        return result

    def _validate_inputs(
        self, left: Any, right: Any, writing_hand: Any
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        if writing_hand not in {"left", "right"}:
            issues.append({
                "code": "invalid_writing_hand", "path": "writing_hand",
                "message": "writing_hand must be left or right.",
            })
        for expected_side, scan in (("left", left), ("right", right)):
            validation = validate_palm_scan_result(scan)
            issues.extend({
                **item, "path": f"{expected_side}_palm_scan_result.{item['path']}"
            } for item in validation.issues)
            if not isinstance(scan, dict):
                continue
            hand = scan.get("hand", {})
            actual_side = hand.get("side") or hand.get("handedness")
            if actual_side != expected_side:
                issues.append({
                    "code": "hand_side_mismatch",
                    "path": f"{expected_side}_palm_scan_result.hand.side",
                    "message": (
                        f"Expected a detected {expected_side} hand scan."
                    ),
                    "actual": actual_side, "required": expected_side,
                })
            if _feature_confidence(hand) < self.reliable_threshold:
                issues.append({
                    "code": "handedness_below_reliable_threshold",
                    "path": f"{expected_side}_palm_scan_result.hand.confidence",
                    "message": "Detected hand side confidence is too low.",
                    "actual": _feature_confidence(hand),
                    "required": self.reliable_threshold,
                })
        return issues

    def _compare(
        self, dominant: dict[str, Any], non_dominant: dict[str, Any]
    ) -> list[dict[str, Any]]:
        comparisons = []
        for spec in COMPARISON_SPECS:
            dominant_feature = _get(dominant, spec.feature_path)
            baseline_feature = _get(non_dominant, spec.feature_path)
            if not (
                _usable(dominant_feature, self.reliable_threshold)
                and _usable(baseline_feature, self.reliable_threshold)
            ):
                continue
            dominant_value = _number(_get(dominant, spec.path))
            baseline_value = _number(_get(non_dominant, spec.path))
            if dominant_value is None or baseline_value is None:
                continue
            delta = dominant_value - baseline_value
            direction = (
                "higher_in_dominant" if delta >= spec.threshold
                else "lower_in_dominant" if delta <= -spec.threshold
                else "aligned"
            )
            confidence = min(
                _feature_confidence(dominant_feature),
                _feature_confidence(baseline_feature),
                _scan_confidence(dominant),
                _scan_confidence(non_dominant),
            )
            comparisons.append({
                "comparison_id": spec.comparison_id,
                "feature_path": spec.path,
                "family": spec.family,
                "domain": spec.domain,
                "dominant_value": dominant_value,
                "non_dominant_value": baseline_value,
                "delta": round(delta, 4),
                "direction": direction,
                "difference_threshold": spec.threshold,
                "confidence": round(confidence, 4),
                "interpretation": (
                    f"The dominant-hand {spec.comparison_id.replace('_', ' ')} "
                    f"measurement is {direction.replace('_', ' ')} relative "
                    "to the non-dominant hand. Traditional bilateral palmistry "
                    "records this as a comparative observation, not proof of "
                    "a life event or fixed trait."
                ),
                "evidence": {
                    "dominant": {
                        "path": spec.path, "raw_value": dominant_value,
                        "confidence": _feature_confidence(dominant_feature),
                    },
                    "non_dominant": {
                        "path": spec.path, "raw_value": baseline_value,
                        "confidence": _feature_confidence(baseline_feature),
                    },
                },
            })
        return comparisons

    @staticmethod
    def _combine_domains(
        dominant: dict[str, Any],
        non_dominant: dict[str, Any],
        comparisons: list[dict[str, Any]],
    ) -> dict[str, Any]:
        combined = {}
        for domain in DOMAINS:
            current = dominant["domains"][domain]
            baseline = non_dominant["domains"][domain]
            changes = [
                item for item in comparisons if item["domain"] == domain
                and item["direction"] != "aligned"
            ]
            confidence_values = [
                value for value in (
                    current.get("confidence"), baseline.get("confidence"),
                    *[item["confidence"] for item in changes],
                ) if isinstance(value, (int, float))
            ]
            combined[domain] = {
                "status": (
                    "comparative_difference" if changes
                    else "aligned_or_no_reliable_difference"
                ),
                "confidence": round(
                    min(confidence_values, default=0.0), 4
                ),
                "baseline": baseline["conclusion"],
                "current_or_developed": current["conclusion"],
                "development_signals": changes,
                "evidence_rule_ids": {
                    "baseline": baseline["conclusion"].get("rule_ids", []),
                    "current": current["conclusion"].get("rule_ids", []),
                },
            }
        return combined

    @staticmethod
    def _insufficient(
        issues: list[dict[str, Any]], writing_hand: Any
    ) -> dict[str, Any]:
        return {
            "schema_version": BILATERAL_SCHEMA_VERSION,
            "status": "insufficient_data",
            "issues": issues,
            "metadata": {
                "engine": "palmistry_bilateral/1.0",
                "writing_hand_source": "explicit_user_answer",
                "dominant_side": (
                    writing_hand if writing_hand in {"left", "right"} else None
                ),
                "image_or_artifact_consumed": False,
                "traditional_non_scientific": True,
            },
            "reading_completeness": {
                "mode": "bilateral_unavailable",
                "score": 0.0,
                "bilateral_comparison_available": False,
            },
            "confidence": 0.0,
            "hands": {},
            "comparisons": [],
            "combined_domains": {},
            "narration": {
                "grounded_only": True,
                "text": (
                    "Bilateral reading is unavailable until both reliable "
                    "left- and right-hand scans are supplied."
                ),
                "disclaimer": _DISCLAIMER,
            },
        }


_MISSING = object()
_DISCLAIMER = (
    "Traditional bilateral palmistry is not a scientific assessment. "
    "Dominant/non-dominant roles are symbolic conventions, not proven facts."
)


def _get(root: Any, path: str) -> Any:
    value = root
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _number(value: Any) -> float | None:
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        else None
    )


def _feature_confidence(feature: Any) -> float:
    if not isinstance(feature, dict):
        return 0.0
    value = feature.get("confidence")
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        and 0 <= value <= 1 else 0.0
    )


def _scan_confidence(scan: dict[str, Any]) -> float:
    confidence = scan.get("scan_confidence", {})
    value = confidence.get("value", confidence.get("overall"))
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        and 0 <= value <= 1 else 0.0
    )


def _usable(feature: Any, threshold: float) -> bool:
    return (
        isinstance(feature, dict)
        and feature.get("status") in {"detected", "reliable", "usable"}
        and feature.get("ambiguous") is not True
        and _feature_confidence(feature) >= threshold
    )


def _narrate(result: dict[str, Any]) -> dict[str, Any]:
    dominant = result["hands"]["dominant"]["reading"]["narration"]
    baseline = result["hands"]["non_dominant"]["reading"]["narration"]
    changes = [
        item["interpretation"] for item in result["comparisons"]
        if item["direction"] != "aligned"
    ]
    sections = {
        "Current / Developed Pattern (Dominant Hand)": dominant["text"],
        "Baseline / Underlying Pattern (Non-Dominant Hand)": baseline["text"],
        "Measured Development Differences": " ".join(changes) if changes else (
            "No reliable paired measurement exceeded its configured "
            "difference threshold."
        ),
        "Confidence & Limitations": _DISCLAIMER,
    }
    return {
        "grounded_only": True,
        "sections": sections,
        "text": "\n".join(
            f"{heading}: {text}" for heading, text in sections.items()
        ),
        "disclaimer": _DISCLAIMER,
    }
