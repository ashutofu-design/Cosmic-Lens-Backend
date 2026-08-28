"""Priority-aware conflict resolution for traditional face-reading signals."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

TENSION_PATTERN_VERSION = "1.0"
TENSION_PATTERNS = (
    {
        "pattern_id": "independence_social_expression_tension",
        "left": {"domain": "personality", "categories": {"independence"}},
        "right": {
            "domain": "social_communication",
            "categories": {"communication", "social_presentation"},
        },
        "interpretation": (
            "The selected traditional system contains both independence and "
            "outward-social symbolism; this is retained as a mixed pattern."
        ),
    },
)


def resolve_domain(
    signals: list[dict[str, Any]],
    strong_threshold: float,
    *,
    require_multiple_families: bool = False,
) -> dict[str, Any]:
    positive = [item for item in signals if item["signed_score"] > 0]
    negative = [item for item in signals if item["signed_score"] < 0]
    support = sum(item["weighted_score"] for item in positive)
    contradict = sum(item["weighted_score"] for item in negative)
    total = support + contradict
    net = support - contradict
    all_families = sorted({
        family
        for item in signals
        for family in item.get("feature_families", [])
    })
    mixed = bool(
        positive and negative
        and min(support, contradict) >= .20 * max(support, contradict)
    )
    prevailing = positive if net >= 0 else negative
    conclusion_items = signals if mixed else prevailing
    conclusion_families = sorted({
        family
        for item in conclusion_items
        for family in item.get("feature_families", [])
    })
    maximum_source = max(
        (
            item["propagated_confidence"]
            for item in conclusion_items
        ),
        default=0.0,
    )
    if mixed:
        balance = min(support, contradict) / max(support, contradict)
        confidence = min(maximum_source, balance * min(1.0, total))
    else:
        agreement = abs(net) / total if total else 0.0
        confidence = min(maximum_source, agreement * min(1.0, total))
    if not signals:
        classification = "insufficient"
    elif mixed:
        classification = "mixed"
    elif require_multiple_families and len(conclusion_families) < 2:
        classification = "weak"
    elif confidence >= strong_threshold and len(conclusion_families) >= 2:
        classification = "strong"
    elif confidence >= .60:
        classification = "moderate"
    else:
        classification = "weak"

    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        by_category[signal["category"]].append(signal)
    contradictions = []
    for category, items in by_category.items():
        supporting_ids = [
            item["rule_id"] for item in items if item["polarity"] > 0
        ]
        contradictory_ids = [
            item["rule_id"] for item in items if item["polarity"] < 0
        ]
        if supporting_ids and contradictory_ids:
            contradictions.append({
                "category": category,
                "supporting_rule_ids": supporting_ids,
                "contradictory_rule_ids": contradictory_ids,
                "resolution": "mixed_signal_preserved",
            })
    if positive and negative and not contradictions:
        contradictions.append({
            "category": "cross_category_domain_conflict",
            "supporting_rule_ids": [item["rule_id"] for item in positive],
            "contradictory_rule_ids": [item["rule_id"] for item in negative],
            "resolution": "mixed_signal_preserved",
        })

    interpretations = list(dict.fromkeys(
        item["interpretation"] for item in conclusion_items
    ))
    evidence = [
        {
            "feature": entry["feature_path"],
            "measurement": entry["measurement_path"],
            "raw_measurement": entry["raw_value"],
            "signal": item["signal_name"],
            "polarity": item["signal"],
            "confidence": entry["source_confidence"],
            "propagated_confidence": item["propagated_confidence"],
            "rule_ids": [item["rule_id"]],
        }
        for item in conclusion_items
        for entry in item["evidence"]
    ]
    return {
        "classification": classification,
        "confidence": round(confidence, 4),
        "mixed_signal": mixed,
        "feature_families": all_families,
        "conclusion_feature_families": conclusion_families,
        "normalized_score": round(net / total, 4) if total else 0.0,
        "internal_score": round((net / total + 1) / 2, 4) if total else .5,
        "score_metadata": {
            "visibility": "internal_only", "not_a_probability": True,
        },
        "positive_evidence": positive,
        "negative_evidence": negative,
        "supporting_evidence": prevailing,
        "contradictory_evidence": negative if net >= 0 else positive,
        "contradictions": contradictions,
        "conclusion": {
            "conclusion": (
                ("Mixed traditional signals: " if mixed else "")
                + " ".join(interpretations)
                if interpretations else "Insufficient reliable measured evidence."
            ),
            "interpretation": interpretations,
            "confidence": round(confidence, 4),
            "classification": classification,
            "evidence": evidence,
            "rule_ids": list(dict.fromkeys(
                item["rule_id"] for item in conclusion_items
            )),
        },
    }


def detect_cross_domain_tensions(
    signals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    tensions = []
    for pattern in TENSION_PATTERNS:
        left = [
            item for item in signals
            if item["domain"] == pattern["left"]["domain"]
            and item["category"] in pattern["left"]["categories"]
            and item["polarity"] > 0
        ]
        right = [
            item for item in signals
            if item["domain"] == pattern["right"]["domain"]
            and item["category"] in pattern["right"]["categories"]
            and item["polarity"] > 0
        ]
        if not left or not right:
            continue
        evidence = [
            {
                "domain": item["domain"],
                "category": item["category"],
                "rule_id": item["rule_id"],
                "confidence": item["propagated_confidence"],
                "feature_paths": [
                    entry["feature_path"] for entry in item["evidence"]
                ],
            }
            for item in left + right
        ]
        tensions.append({
            "pattern_version": TENSION_PATTERN_VERSION,
            "pattern_id": pattern["pattern_id"],
            "classification": "mixed_tension",
            "mixed_signal": True,
            "interpretation": pattern["interpretation"],
            "confidence": round(min(
                item["propagated_confidence"] for item in left + right
            ), 4),
            "evidence": evidence,
        })
    return tensions
