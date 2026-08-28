"""Deterministic Phase 2 rule evaluation over PalmScanResult JSON only."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .conflicts import detect_cross_domain_tensions, resolve_domain
from .narrator import DeterministicSafeNarrator, StructuredNarrator
from .rules import DOMAINS, RULES, RULESET_VERSION, Condition, Rule
from .schema import prepare_for_phase2, validate_palm_scan_result

ENGINE_VERSION = "1.0"
PRIORITY_MULTIPLIER = {3: 1.35, 2: 1.0, 1: .45}


class PalmistryPhase2Engine:
    def __init__(
        self, *, reliable_threshold: float = .55, strong_threshold: float = .75,
        narrator: StructuredNarrator | None = None,
    ):
        if not 0 <= reliable_threshold <= strong_threshold <= 1:
            raise ValueError("Thresholds must satisfy 0 <= reliable <= strong <= 1.")
        self.reliable_threshold = reliable_threshold
        self.strong_threshold = strong_threshold
        self.narrator = narrator or DeterministicSafeNarrator()

    def analyze(self, palm_scan_result: dict[str, Any]) -> dict[str, Any]:
        palm_scan_result = prepare_for_phase2(palm_scan_result)
        validation = validate_palm_scan_result(palm_scan_result)
        if not validation.valid:
            return self._insufficient("invalid_palm_scan_result", validation.issues)
        scan = deepcopy(palm_scan_result)
        scan_confidence = _number(scan["scan_confidence"].get("value", scan["scan_confidence"].get("overall", 0)))
        issues = _admission_issues(scan, scan_confidence, self.reliable_threshold)
        if issues:
            return self._insufficient("insufficient_data", issues, scan_confidence=scan_confidence)

        signals = []
        skipped = []
        for rule in RULES:
            signal, reason = self._evaluate_rule(scan, rule, scan_confidence)
            if signal:
                signals.append(signal)
            elif reason:
                skipped.append({"rule_id": rule.rule_id, "reason": reason})

        domains: dict[str, dict[str, Any]] = {}
        for domain_name, category_names in DOMAINS.items():
            domain_signals = [item for item in signals if item["domain"] == domain_name]
            resolved = resolve_domain(
                domain_signals, self.strong_threshold,
                require_multiple_families=True,
            )
            resolved["categories"] = {}
            for category in category_names:
                category_signals = [item for item in domain_signals if item["category"] == category]
                category_result = resolve_domain(category_signals, self.strong_threshold)
                category_result["status"] = (
                    "insufficient_data" if category_result["classification"] == "insufficient" else "supported"
                )
                resolved["categories"][category] = category_result
            resolved["status"] = "insufficient_data" if not domain_signals else "supported"
            domains[domain_name] = resolved

        result = {
            "schema_version": "palmistry_phase2/1.0",
            "status": "ok" if signals else "insufficient_data",
            "metadata": {
                "engine": f"palmistry_phase2/{ENGINE_VERSION}",
                "ruleset_version": RULESET_VERSION,
                "deterministic": True,
                "input_contract": "PalmScanResult/1.0 JSON only",
                "image_or_artifact_consumed": False,
                "scores": "internal_only",
                "traditional_non_scientific": True,
                "reading_scope": "single_hand",
                "bilateral_comparison_available": False,
            },
            "confidence_policy": {
                "reliable_feature_threshold": self.reliable_threshold,
                "strong_conclusion_threshold": self.strong_threshold,
                "strong_requires_independent_feature_families": 2,
                "formula": "propagated=min(scan_confidence, feature_confidence, rule_confidence); weighted_score=weight*priority_multiplier*propagated",
                "never_upgrades_source_confidence": True,
            },
            "input_scan_confidence": scan_confidence,
            "reading_completeness": {
                "mode": "single_hand",
                "score": .65,
                "bilateral_comparison_available": False,
                "message": (
                    "Single-hand reading available; bilateral comparison "
                    "is unavailable."
                ),
            },
            "final_reading_confidence": round(scan_confidence * .65, 4),
            "single_feature_signals": signals,
            "domains": domains,
            "contradictions": [
                {"domain": name, **conflict}
                for name, domain in domains.items() for conflict in domain["contradictions"]
            ],
            "cross_domain_tensions": detect_cross_domain_tensions(signals),
            "explainability": {
                "feature_to_measurement_to_rule_to_conclusion": [
                    {
                        "feature_path": item["evidence"][0]["feature_path"],
                        "measurement": item["evidence"][0]["raw_value"],
                        "rule_id": item["rule_id"],
                        "domain": item["domain"],
                        "category": item["category"],
                        "signal": item["signal"],
                    }
                    for item in signals
                ]
            },
            "skipped_rules": skipped,
        }
        if not signals:
            result["issues"] = [{
                "code": "no_reliable_interpretable_measurements",
                "message": "The valid scan contains no detected/readable measurements that meet the confidence policy.",
            }]
        result["narration"] = self.narrator.narrate(result)
        return result

    def _evaluate_rule(
        self, scan: dict[str, Any], rule: Rule, scan_confidence: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        evidence = []
        confidences = []
        for condition in rule.conditions:
            value = _get(scan, condition.path)
            if value is _MISSING:
                return None, "measurement_missing"
            feature, feature_path = _source_feature(scan, condition.path)
            usable, reason = _feature_is_usable(scan, rule, feature, feature_path, self.reliable_threshold)
            if not usable:
                return None, reason
            matched, matched_value, candidate_confidence = _matches(condition, value)
            if not matched:
                return None, None
            if rule.family == "marking":
                declared = scan["scan_confidence"].get("eligible_features", {}).get("markings")
                if isinstance(declared, list) and matched_value.get("type") not in declared:
                    return None, "not_phase1_eligible"
            feature_confidence = min(
                _feature_confidences(scan, feature_path, feature),
                default=0.0,
            )
            if candidate_confidence is not None:
                feature_confidence = min(feature_confidence, candidate_confidence)
            if feature_confidence < max(self.reliable_threshold, rule.required_confidence):
                return None, "below_rule_confidence"
            confidences.append(feature_confidence)
            evidence.append({
                "feature_path": feature_path,
                "measurement_path": condition.path,
                "raw_value": matched_value,
                "condition": {"operator": condition.operator, "expected": condition.value},
                "source_confidence": round(feature_confidence, 4),
            })
        source_confidence = min(confidences)
        propagated = min(scan_confidence, source_confidence, rule.rule_confidence)
        weighted = rule.weight * PRIORITY_MULTIPLIER[rule.priority] * propagated
        return {
            "rule_id": rule.rule_id,
            "domain": rule.domain,
            "category": rule.category,
            "family": rule.family,
            "priority": rule.priority,
            "polarity": rule.polarity,
            "signal": "positive" if rule.polarity > 0 else "negative",
            "interpretation": rule.interpretation,
            "source_tradition": rule.source_tradition,
            "evidence_paths": list(rule.evidence_paths),
            "evidence": evidence,
            "source_confidence": round(source_confidence, 4),
            "rule_confidence": rule.rule_confidence,
            "scan_confidence": scan_confidence,
            "propagated_confidence": round(propagated, 4),
            "confidence_components": {
                "scan": scan_confidence, "feature": round(source_confidence, 4),
                "rule": rule.rule_confidence, "operator": "minimum",
            },
            "weight": rule.weight,
            "priority_multiplier": PRIORITY_MULTIPLIER[rule.priority],
            "weighted_score": round(weighted, 4),
            "signed_score": round(rule.polarity * weighted, 4),
            "normalized_internal_score": round(min(1.0, weighted), 4),
        }, None

    def _insufficient(
        self, reason: str, issues: list[dict[str, Any]], *, scan_confidence: float = 0.0
    ) -> dict[str, Any]:
        result = {
            "schema_version": "palmistry_phase2/1.0",
            "status": "insufficient_data",
            "reason": reason,
            "issues": issues,
            "metadata": {
                "engine": f"palmistry_phase2/{ENGINE_VERSION}",
                "ruleset_version": RULESET_VERSION,
                "deterministic": True,
                "input_contract": "PalmScanResult/1.0 JSON only",
                "image_or_artifact_consumed": False,
                "scores": "internal_only",
                "traditional_non_scientific": True,
                "reading_scope": "single_hand",
                "bilateral_comparison_available": False,
            },
            "confidence_policy": {
                "reliable_feature_threshold": self.reliable_threshold,
                "strong_conclusion_threshold": self.strong_threshold,
                "strong_requires_independent_feature_families": 2,
                "formula": "propagated=min(scan_confidence, feature_confidence, rule_confidence); weighted_score=weight*priority_multiplier*propagated",
                "never_upgrades_source_confidence": True,
            },
            "input_scan_confidence": scan_confidence,
            "reading_completeness": {
                "mode": "single_hand",
                "score": .65 if scan_confidence > 0 else 0.0,
                "bilateral_comparison_available": False,
                "message": (
                    "Single-hand reading available; bilateral comparison "
                    "is unavailable."
                ),
            },
            "final_reading_confidence": round(scan_confidence * .65, 4),
            "single_feature_signals": [],
            "domains": {},
            "contradictions": [],
            "cross_domain_tensions": [],
            "explainability": {"feature_to_measurement_to_rule_to_conclusion": []},
            "skipped_rules": [],
        }
        for name, categories in DOMAINS.items():
            domain = resolve_domain([], self.strong_threshold)
            domain["status"] = "insufficient_data"
            domain["categories"] = {}
            for category in categories:
                category_result = resolve_domain([], self.strong_threshold)
                category_result["status"] = "insufficient_data"
                domain["categories"][category] = category_result
            result["domains"][name] = domain
        result["narration"] = self.narrator.narrate(result)
        return result


_MISSING = object()


def _get(root: Any, path: str) -> Any:
    value = root
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _number(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def _source_feature(scan: dict, path: str) -> tuple[dict, str]:
    parts = path.split(".")
    if parts[0] in {"major_lines", "mounts", "fingers"}:
        base_parts = parts[:2]
        if parts[0] in {"mounts", "fingers"} and len(parts) > 2 and isinstance(_get(scan, ".".join(parts[:3])), dict):
            base_parts = parts[:3]
    elif parts[0] == "thumb":
        base_parts = parts[:2]
    elif parts[0] in {"palm_geometry"}:
        base_parts = parts[:2]
    elif parts[0] in {"special_markings", "union_lines"}:
        base_parts = parts[:1]
    else:
        base_parts = parts[:-1]
    feature_path = ".".join(base_parts)
    feature = _get(scan, feature_path)
    return (feature if isinstance(feature, dict) else {}, feature_path)


def _feature_confidences(scan: dict, feature_path: str, feature: dict) -> list[float]:
    values = []
    if isinstance(feature.get("confidence"), (int, float)):
        values.append(float(feature["confidence"]))
    parts = feature_path.split(".")
    if len(parts) >= 3:
        outer = _get(scan, ".".join(parts[:2]))
        if isinstance(outer, dict) and isinstance(outer.get("confidence"), (int, float)):
            values.append(float(outer["confidence"]))
    return values or [0.0]


def _feature_is_usable(
    scan: dict, rule: Rule, feature: dict, feature_path: str, threshold: float
) -> tuple[bool, str | None]:
    status = feature.get("status")
    if status not in {"detected", "reliable", "usable", "supported"}:
        return False, "feature_not_detected_or_readable"
    if feature.get("ambiguous") is True or feature.get("semantic_identity") == "ambiguous":
        return False, "ambiguous_feature"
    if rule.family == "union_line" and scan["union_lines"].get("readable") is not True:
        return False, "union_lines_not_readable"
    eligible = scan["scan_confidence"].get("eligible_features")
    if isinstance(eligible, dict):
        group = None
        name = feature_path.split(".")[1] if "." in feature_path else ""
        if rule.family == "major_line":
            group = "major_lines"
        elif rule.family == "mount":
            group = "mounts"
        elif rule.family == "finger_structure":
            group = "fingers"
        elif rule.family == "marking":
            group = "markings"
        if group in eligible:
            declared = eligible[group]
            if not isinstance(declared, list):
                return False, "invalid_eligible_features"
            if rule.family == "marking":
                # Candidate-level type and confidence are still revalidated by _matches.
                if not declared:
                    return False, "not_phase1_eligible"
            elif name not in declared:
                return False, "not_phase1_eligible"
    if min(_feature_confidences(scan, feature_path, feature), default=0) < threshold:
        return False, "below_reliable_threshold"
    return True, None


def _matches(condition: Condition, actual: Any) -> tuple[bool, Any, float | None]:
    op, expected = condition.operator, condition.value
    if op == "gte":
        return (isinstance(actual, (int, float)) and not isinstance(actual, bool) and actual >= expected, actual, None)
    if op == "eq":
        return actual == expected, actual, None
    if op == "in":
        return actual in expected, actual, None
    if op == "relative_long":
        if isinstance(actual, str):
            return actual in {"long", "above_average"}, actual, None
        return (
            isinstance(actual, (int, float)) and not isinstance(actual, bool) and actual >= expected,
            actual, None,
        )
    if op == "between":
        return (isinstance(actual, (int, float)) and expected[0] <= actual <= expected[1], actual, None)
    if op == "balanced_proportions":
        if not isinstance(actual, list) or len(actual) < 2 or not all(isinstance(item, (int, float)) for item in actual[:2]):
            return False, actual, None
        return abs(float(actual[0]) - float(actual[1])) <= expected, actual, None
    if op == "nonempty":
        return bool(actual) is bool(expected), actual, None
    if op == "contains_marking":
        if not isinstance(actual, list):
            return False, actual, None
        marking_type, region = expected
        for candidate in actual:
            if not isinstance(candidate, dict):
                continue
            candidate_region = candidate.get("mount") or candidate.get("region") or candidate.get("location")
            if (
                candidate.get("type") == marking_type
                and candidate_region == region
                and candidate.get("status") in {"detected", "reliable"}
                and not candidate.get("ambiguous", False)
            ):
                return True, candidate, _number(candidate.get("confidence"))
        return False, actual, None
    if op == "contains_marking_type":
        if not isinstance(actual, list):
            return False, actual, None
        for candidate in actual:
            if (
                isinstance(candidate, dict)
                and candidate.get("type") == expected
                and candidate.get("status") in {"detected", "reliable"}
                and not candidate.get("ambiguous", False)
            ):
                return True, candidate, _number(candidate.get("confidence"))
        return False, actual, None
    return False, actual, None


def _admission_issues(scan: dict[str, Any], confidence: float, threshold: float) -> list[dict[str, Any]]:
    checks = (
        ("validation_status_not_accepted", "validation.status", scan["validation"].get("status"), "accepted_measurements_only"),
        ("validation_quality_gate_failed", "validation.quality_gate", scan["validation"].get("quality_gate"), "passed"),
        ("quality_gate_failed", "quality.gate", scan["quality"].get("gate"), "passed"),
        ("quality_not_usable", "quality.usable", scan["quality"].get("usable"), True),
        ("phase_2_not_eligible", "scan_confidence.phase_2_eligible", scan["scan_confidence"].get("phase_2_eligible"), True),
        ("phase_2_reason_incompatible", "scan_confidence.phase_2_reason", scan["scan_confidence"].get("phase_2_reason"), "eligible_measurement_only"),
    )
    issues = [
        {
            "code": code, "path": path,
            "message": f"Admission requires {path} == {expected!r}.",
            "actual": actual, "required": expected,
        }
        for code, path, actual, expected in checks if actual != expected
    ]
    if confidence < threshold:
        issues.append({
            "code": "scan_below_reliable_threshold",
            "path": "scan_confidence.value",
            "message": "Scan confidence is below the configured reliable threshold.",
            "actual": confidence, "required": threshold,
        })
    return issues
