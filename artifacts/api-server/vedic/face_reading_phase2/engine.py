"""Deterministic traditional face-reading analysis over FaceScanResult JSON."""
from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from .conflicts import detect_cross_domain_tensions
from .domains import analyze_domains
from .narrator import (
    DeterministicSafeNarrator,
    StructuredNarrator,
    validate_narration,
)
from .rules import (
    DEFAULT_SYSTEM_ID,
    DOMAINS,
    RULE_FORMAT_VERSION,
    SYSTEMS,
    Condition,
    Rule,
    RuleSystem,
)
from .schema import admission_issues, issue, validate_face_scan_result

ENGINE_VERSION = "1.0"
PRIORITY_MULTIPLIER = {4: 1.35, 3: 1.0, 2: .70, 1: .30}
PHASE1_ZONE_NAMES = {
    "upper", "middle", "lower", "forehead", "eyebrow_eye", "nose",
    "right_cheek", "left_cheek", "mouth", "chin", "right_face", "left_face",
}
FORBIDDEN_RULE_TERMS = {
    "scientifically proven", "diagnos", "criminal", "ethnicity",
    "guaranteed", "proves that", "will become",
}
_MISSING = object()


class FaceReadingPhase2Engine:
    def __init__(
        self,
        *,
        reliable_threshold: float = .55,
        strong_threshold: float = .75,
        narrator: StructuredNarrator | None = None,
        systems: dict[str, RuleSystem] | None = None,
    ):
        if not 0 <= reliable_threshold <= strong_threshold <= 1:
            raise ValueError(
                "Thresholds must satisfy 0 <= reliable <= strong <= 1."
            )
        self.reliable_threshold = reliable_threshold
        self.strong_threshold = strong_threshold
        self.narrator = narrator or DeterministicSafeNarrator()
        self.systems = dict(systems or SYSTEMS)
        _validate_system_registry(self.systems)

    def analyze(
        self,
        face_scan_result: dict[str, Any],
        *,
        traditional_system: str = DEFAULT_SYSTEM_ID,
    ) -> dict[str, Any]:
        system = self.systems.get(traditional_system)
        if system is None:
            return self._insufficient(
                "unsupported_traditional_system",
                [issue(
                    "unsupported_traditional_system", "traditional_system",
                    "Select exactly one registered traditional rule system.",
                    actual=traditional_system,
                    supported=sorted(self.systems),
                )],
                traditional_system=traditional_system,
            )
        validation = validate_face_scan_result(face_scan_result)
        if not validation.valid:
            return self._insufficient(
                "invalid_face_scan_result", validation.issues, system=system
            )
        scan = deepcopy(face_scan_result)
        scan_confidence = _number(scan["confidence"].get("overall"))
        issues = admission_issues(scan, self.reliable_threshold)
        if issues:
            return self._insufficient(
                "insufficient_data", issues, scan_confidence=scan_confidence,
                system=system,
            )

        signals = []
        skipped = []
        for rule in system.rules:
            signal, reason = self._evaluate_rule(
                scan, rule, scan_confidence
            )
            if signal:
                signals.append(signal)
            elif reason:
                skipped.append({"rule_id": rule.rule_id, "reason": reason})

        supported_categories = _supported_categories(system)
        domains = self._domains(signals, supported_categories)
        zones = self._zone_analysis(
            scan, signals, self.reliable_threshold
        )
        result = {
            "schema_version": "face_reading_phase2/1.0",
            "status": "ok" if signals else "insufficient_data",
            "metadata": {
                "engine": f"face_reading_phase2/{ENGINE_VERSION}",
                "rule_format_version": RULE_FORMAT_VERSION,
                "ruleset_version": system.version,
                "traditional_system": system.system_id,
                "traditional_namespace": system.namespace,
                "traditional_system_display_name": system.display_name,
                "traditional_system_disclaimer": system.disclaimer,
                "supported_categories": {
                    name: sorted(categories)
                    for name, categories in supported_categories.items()
                },
                "systems_combined": False,
                "deterministic": True,
                "input_contract": "FaceScanResult/1.0 JSON only",
                "image_or_artifact_consumed": False,
                "traditional_non_scientific": True,
                "consequential_decision_use": "forbidden",
            },
            "confidence_policy": self._confidence_policy(),
            "input_scan_confidence": scan_confidence,
            "single_feature_signals": [
                item for item in signals if item["scope"] == "single"
            ],
            "combined_feature_signals": [
                item for item in signals if item["scope"] == "cross"
            ],
            "all_signals": signals,
            "zone_analysis": zones,
            "domains": domains,
            "internal_domain_scores": {
                name: {
                    "score": domain["internal_score"],
                    "visibility": "internal_only",
                    "not_a_probability": True,
                }
                for name, domain in domains.items()
            },
            "contradictions": [
                {"domain": name, **conflict}
                for name, domain in domains.items()
                for conflict in domain["contradictions"]
            ],
            "cross_domain_tensions": detect_cross_domain_tensions(signals),
            "explainability": {
                "feature_to_measurement_to_rule_to_signal_to_conclusion": [
                    {
                        "feature": evidence["feature_path"],
                        "measurement": evidence["measurement_path"],
                        "raw_value": evidence["raw_value"],
                        "rule_id": item["rule_id"],
                        "signal": item["signal_name"],
                        "domain": item["domain"],
                        "category": item["category"],
                        "propagated_confidence": item[
                            "propagated_confidence"
                        ],
                    }
                    for item in signals for evidence in item["evidence"]
                ]
            },
            "skipped_rules": skipped,
        }
        if not signals:
            result["issues"] = [issue(
                "no_reliable_interpretable_measurements", "face_scan_result",
                "No measured feature met the selected system's confidence rules.",
            )]
        result["narration"] = self.narrator.narrate(result)
        validate_narration(result["narration"], result)
        return result

    def _evaluate_rule(
        self, scan: dict[str, Any], rule: Rule, scan_confidence: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        evidence = []
        confidences = []
        for condition in rule.conditions:
            actual = _get(scan, condition.path)
            if actual is _MISSING:
                return None, "measurement_missing"
            feature = _get(scan, condition.feature_path)
            if not isinstance(feature, dict):
                return None, "feature_missing"
            usable, reason, feature_confidence = _feature_is_usable(
                feature, self.reliable_threshold, rule.minimum_confidence
            )
            if not usable:
                return None, reason
            matched, matched_value, candidate_confidence = _matches(
                condition, actual
            )
            if not matched:
                return None, None
            container_confidence = feature_confidence
            effective_confidence = feature_confidence
            if candidate_confidence is not None:
                effective_confidence = min(
                    container_confidence, candidate_confidence
                )
                if effective_confidence < max(
                    self.reliable_threshold, rule.minimum_confidence
                ):
                    return None, "candidate_below_rule_confidence"
            confidences.append(effective_confidence)
            evidence.append({
                "feature_path": condition.feature_path,
                "measurement_path": condition.path,
                "raw_value": matched_value,
                "condition": {
                    "operator": condition.operator,
                    "expected": condition.value,
                },
                "container_confidence": round(container_confidence, 4),
                "candidate_confidence": (
                    round(candidate_confidence, 4)
                    if candidate_confidence is not None else None
                ),
                "effective_feature_confidence": round(
                    effective_confidence, 4
                ),
                "source_confidence": round(effective_confidence, 4),
            })
        source_confidence = min(confidences)
        propagated = min(
            scan_confidence, source_confidence, rule.rule_confidence
        )
        weighted = (
            rule.weight * PRIORITY_MULTIPLIER[rule.priority] * propagated
        )
        return {
            "rule_id": rule.rule_id,
            "system_id": rule.system_id,
            "domain": rule.domain,
            "category": rule.category,
            "signal_name": rule.signal_name,
            "signal": "positive" if rule.polarity > 0 else "negative",
            "polarity": rule.polarity,
            "scope": rule.scope,
            "feature_families": list(rule.feature_families),
            "zones": list(rule.zones),
            "priority": rule.priority,
            "interpretation": rule.interpretation,
            "evidence_requirements": list(rule.evidence_requirements),
            "evidence": evidence,
            "source_confidence": round(source_confidence, 4),
            "rule_confidence": rule.rule_confidence,
            "scan_confidence": scan_confidence,
            "propagated_confidence": round(propagated, 4),
            "confidence_components": {
                "scan": scan_confidence,
                "feature": round(source_confidence, 4),
                "rule": rule.rule_confidence,
                "operator": "minimum",
                "feature_inputs": [
                    {
                        "feature_path": item["feature_path"],
                        "container": item["container_confidence"],
                        "candidate": item["candidate_confidence"],
                        "effective": item["effective_feature_confidence"],
                    }
                    for item in evidence
                ],
            },
            "weight": rule.weight,
            "priority_multiplier": PRIORITY_MULTIPLIER[rule.priority],
            "weighted_score": round(weighted, 4),
            "signed_score": round(rule.polarity * weighted, 4),
        }, None

    def _domains(
        self,
        signals: list[dict[str, Any]],
        supported_categories: dict[str, set[str]],
    ) -> dict[str, dict[str, Any]]:
        return analyze_domains(
            signals, self.strong_threshold, supported_categories
        )

    @staticmethod
    def _zone_analysis(
        scan: dict[str, Any],
        signals: list[dict[str, Any]],
        reliable_threshold: float,
    ) -> dict[str, dict[str, Any]]:
        source_zones = scan.get("traditional_zones", {}).get("zones", {})
        output = {}
        for zone_name, source in source_zones.items():
            if not isinstance(source, dict):
                continue
            candidate_signals = [
                item for item in signals if zone_name in item["zones"]
            ]
            source_confidence = _number(source.get("confidence"))
            source_available = (
                source.get("status") == "derived"
                and source_confidence >= reliable_threshold
            )
            zone_signals = candidate_signals if source_available else []
            confidence = min(
                [source_confidence] + [
                    item["propagated_confidence"] for item in zone_signals
                ]
            ) if zone_signals else source_confidence
            output[zone_name] = {
                "status": (
                    "unavailable" if not source_available
                    else "supported" if zone_signals
                    else "no_rules_triggered"
                ),
                "source_status": source.get("status", "unknown"),
                "confidence": round(confidence, 4),
                "features": list(dict.fromkeys(
                    evidence["feature_path"]
                    for item in zone_signals for evidence in item["evidence"]
                )),
                "rules_triggered": [
                    item["rule_id"] for item in zone_signals
                ],
                "signals": [
                    {
                        "signal": item["signal_name"],
                        "confidence": item["propagated_confidence"],
                        "domain": item["domain"],
                    }
                    for item in zone_signals
                ],
                "suppressed_rules": [
                    item["rule_id"] for item in candidate_signals
                ] if not source_available else [],
            }
        return output

    def _insufficient(
        self,
        reason: str,
        issues: list[dict[str, Any]],
        *,
        scan_confidence: float = 0.0,
        system: RuleSystem | None = None,
        traditional_system: str | None = None,
    ) -> dict[str, Any]:
        system_id = (
            system.system_id if system else traditional_system or DEFAULT_SYSTEM_ID
        )
        supported_categories = (
            _supported_categories(system) if system else {}
        )
        domains = analyze_domains(
            [], self.strong_threshold,
            supported_categories if system else None,
        )
        result = {
            "schema_version": "face_reading_phase2/1.0",
            "status": "insufficient_data",
            "reason": reason,
            "issues": issues,
            "metadata": {
                "engine": f"face_reading_phase2/{ENGINE_VERSION}",
                "traditional_system": system_id,
                "traditional_namespace": system.namespace if system else None,
                "ruleset_version": system.version if system else None,
                "traditional_system_disclaimer": (
                    system.disclaimer if system else None
                ),
                "supported_categories": {
                    name: sorted(categories)
                    for name, categories in supported_categories.items()
                },
                "systems_combined": False,
                "deterministic": True,
                "input_contract": "FaceScanResult/1.0 JSON only",
                "image_or_artifact_consumed": False,
                "traditional_non_scientific": True,
                "consequential_decision_use": "forbidden",
            },
            "confidence_policy": self._confidence_policy(),
            "input_scan_confidence": scan_confidence,
            "single_feature_signals": [],
            "combined_feature_signals": [],
            "all_signals": [],
            "zone_analysis": {},
            "domains": domains,
            "internal_domain_scores": {
                name: {
                    "score": .5, "visibility": "internal_only",
                    "not_a_probability": True,
                }
                for name in domains
            },
            "contradictions": [],
            "cross_domain_tensions": [],
            "explainability": {
                "feature_to_measurement_to_rule_to_signal_to_conclusion": []
            },
            "skipped_rules": [],
        }
        result["narration"] = self.narrator.narrate(result)
        validate_narration(result["narration"], result)
        return result

    def _confidence_policy(self) -> dict[str, Any]:
        return {
            "reliable_feature_threshold": self.reliable_threshold,
            "strong_conclusion_threshold": self.strong_threshold,
            "strong_requires_independent_feature_families": 2,
            "formula": (
                "propagated=min(scan_confidence, feature_confidence, "
                "rule_confidence); weighted_score=weight*priority*propagated"
            ),
            "never_upgrades_source_confidence": True,
            "ambiguous_features_are_excluded": True,
        }


def _get(root: Any, path: str) -> Any:
    value = root
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _number(value: Any) -> float:
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(float(value))
        else 0.0
    )


def _feature_is_usable(
    feature: dict[str, Any], threshold: float, rule_threshold: float
) -> tuple[bool, str | None, float]:
    status = feature.get("status")
    if status is not None and status not in {
        "measured", "detected", "classified", "derived", "supported",
    }:
        return False, (
            "ambiguous_feature" if status == "ambiguous"
            else "feature_not_measured"
        ), 0.0
    if (
        feature.get("ambiguous") is True
        or feature.get("label") == "ambiguous"
        or feature.get("classification") == "ambiguous"
    ):
        return False, "ambiguous_feature", 0.0
    confidence = _number(feature.get("confidence"))
    required = max(threshold, rule_threshold)
    if confidence < required:
        return False, "below_rule_confidence", confidence
    return True, None, confidence


def _matches(
    condition: Condition, actual: Any
) -> tuple[bool, Any, float | None]:
    operator, expected = condition.operator, condition.value
    numeric = isinstance(actual, (int, float)) and not isinstance(actual, bool)
    if operator == "gte":
        return numeric and actual >= expected, actual, None
    if operator == "lte":
        return numeric and actual <= expected, actual, None
    if operator == "between":
        return (
            numeric and expected[0] <= actual <= expected[1],
            actual, None,
        )
    if operator == "eq":
        return actual == expected, actual, None
    if operator == "in":
        return actual in expected, actual, None
    if operator == "balanced_measurements":
        if not isinstance(actual, list) or len(actual) < 3:
            return False, actual, None
        values = []
        confidences = []
        for item in actual:
            if not isinstance(item, dict):
                return False, actual, None
            value = item.get("normalized")
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, actual, None
            values.append(float(value))
            confidences.append(_number(item.get("confidence")))
        spread = max(values) - min(values)
        return spread <= expected, {
            "values": values, "spread": round(spread, 6)
        }, min(confidences, default=0.0)
    if operator == "contains_verified_marking":
        if not isinstance(actual, list):
            return False, actual, None
        for candidate in actual:
            if (
                isinstance(candidate, dict)
                and candidate.get("status") in {"detected", "measured"}
                and candidate.get("location") == expected
                and candidate.get("type") not in {None, "unknown", "ambiguous"}
                and candidate.get("ambiguous") is not True
            ):
                return True, candidate, _number(candidate.get("confidence"))
        return False, actual, None
    return False, actual, None


def _supported_categories(system: RuleSystem) -> dict[str, set[str]]:
    supported = {name: set() for name in DOMAINS}
    for rule in system.rules:
        supported[rule.domain].add(rule.category)
    return supported


def _validate_system_registry(systems: dict[str, RuleSystem]) -> None:
    if not systems:
        raise ValueError("At least one traditional rule system is required.")
    for key, system in systems.items():
        if key != system.system_id:
            raise ValueError("Rule-system registry key must match system_id.")
        seen = set()
        for rule in system.rules:
            if rule.rule_id in seen:
                raise ValueError(f"Duplicate rule_id: {rule.rule_id}")
            seen.add(rule.rule_id)
            if (
                rule.system_id != system.system_id
                or not rule.rule_id.startswith(f"{system.system_id}.")
            ):
                raise ValueError(
                    f"Rule {rule.rule_id} is outside its system namespace."
                )
            if rule.domain not in DOMAINS:
                raise ValueError(f"Unknown rule domain: {rule.domain}")
            if rule.category not in DOMAINS[rule.domain]:
                raise ValueError(
                    f"Unknown category {rule.domain}.{rule.category}"
                )
            if rule.scope not in {"single", "cross"}:
                raise ValueError(f"Unknown rule scope: {rule.scope}")
            if rule.scope == "cross" and len(set(rule.feature_families)) < 2:
                raise ValueError(
                    f"Cross-feature rule {rule.rule_id} needs two families."
                )
            if not set(rule.zones).issubset(PHASE1_ZONE_NAMES):
                raise ValueError(
                    f"Rule {rule.rule_id} references an unknown Phase 1 zone."
                )
            if rule.priority not in PRIORITY_MULTIPLIER:
                raise ValueError(f"Unknown rule priority: {rule.priority}")
            for value, name in (
                (rule.minimum_confidence, "minimum_confidence"),
                (rule.rule_confidence, "rule_confidence"),
                (rule.weight, "weight"),
            ):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    or not 0 <= float(value) <= 1
                ):
                    raise ValueError(
                        f"Rule {rule.rule_id} has invalid {name}."
                    )
            lowered = rule.interpretation.lower()
            if any(term in lowered for term in FORBIDDEN_RULE_TERMS):
                raise ValueError(
                    f"Rule {rule.rule_id} contains forbidden claim language."
                )
