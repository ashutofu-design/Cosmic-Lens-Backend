"""Grounded narrator interfaces for structured Face Phase 2 analysis."""
from __future__ import annotations

from typing import Any, Protocol

DISCLAIMER = (
    "This is a traditional face-reading interpretation for reflective or "
    "entertainment use, not a scientific assessment. Confidence describes "
    "measurement quality and rule agreement, not truth about personality or "
    "future outcomes. Do not use it for medical, employment, financial, legal, "
    "relationship, eligibility, or other consequential decisions."
)
GUIDANCE = (
    "Treat these tradition-specific associations as symbolic reflection, "
    "and compare them only with your own lived experience."
)
FORBIDDEN = (
    "proves that you", "you are diagnosed", "you have a disease",
    "you will become", "guaranteed wealth", "criminal", "morally",
    "your ethnicity", "exact date", "scientifically proven",
)


class StructuredNarrator(Protocol):
    def narrate(self, analysis: dict[str, Any]) -> dict[str, Any]: ...


class DeterministicSafeNarrator:
    """Copies only resolved rule conclusions; it never reads FaceScanResult."""

    def narrate(self, analysis: dict[str, Any]) -> dict[str, Any]:
        sections = {
            "Overall Face Profile": _domain_statements(
                analysis, tuple(analysis["domains"]), limit=3
            ),
            "Personality & Temperament": _domain_statements(
                analysis, ("personality",)
            ),
            "Communication & Social Style": _domain_statements(
                analysis, ("social_communication",)
            ),
            "Love & Relationships": _domain_statements(
                analysis, ("relationships",)
            ),
            "Career & Work Style": _domain_statements(
                analysis, ("career",)
            ),
            "Money Tendencies": _domain_statements(
                analysis, ("money",)
            ),
            "Leadership / Recognition": _domain_statements(
                analysis, ("leadership_recognition",)
            ),
            "Strengths": _signal_statements(analysis, polarity=1),
            "Challenges": _signal_statements(analysis, polarity=-1),
            "Important Combined Patterns": (
                _combined_statements(analysis)
                + _tension_statements(analysis)
            ),
            "Traditional Face-Reading Guidance": [{
                "text": GUIDANCE,
                "rule_ids": [],
                "confidence": analysis.get("input_scan_confidence", 0.0),
                "source": "disclaimer",
            }],
            "Confidence & Limitations": [{
                "text": DISCLAIMER,
                "rule_ids": [],
                "confidence": analysis.get("input_scan_confidence", 0.0),
                "source": "disclaimer",
            }],
        }
        text = "\n".join(
            f"{heading}: " + " ".join(item["text"] for item in statements)
            for heading, statements in sections.items() if statements
        )
        lowered = text.lower()
        if any(term in lowered for term in FORBIDDEN):
            raise ValueError(
                "Narrator produced forbidden deterministic, protected, or "
                "consequential language."
            )
        return {
            "narrator": "deterministic_grounded_face/1.0",
            "grounded_only": True,
            "input": "resolved_conclusions_and_evidence_only",
            "sections": sections,
            "text": text,
            "disclaimer": DISCLAIMER,
        }


def _domain_statements(
    analysis: dict[str, Any],
    domain_names: tuple[str, ...],
    *,
    limit: int = 2,
) -> list[dict[str, Any]]:
    statements = []
    seen = set()
    for name in domain_names:
        conclusion = analysis["domains"][name].get("conclusion", {})
        for text in conclusion.get("interpretation", []):
            if text in seen:
                continue
            seen.add(text)
            statements.append({
                "text": text,
                "rule_ids": conclusion.get("rule_ids", []),
                "confidence": conclusion.get("confidence", 0.0),
                "source": f"domains.{name}.conclusion",
            })
            if len(statements) >= limit:
                return statements
    return statements


def _signal_statements(
    analysis: dict[str, Any], *, polarity: int
) -> list[dict[str, Any]]:
    return [
        {
            "text": item["interpretation"],
            "rule_ids": [item["rule_id"]],
            "confidence": item["propagated_confidence"],
            "source": "all_signals",
        }
        for item in analysis.get("all_signals", [])
        if item["polarity"] == polarity
    ][:3]


def _combined_statements(
    analysis: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "text": item["interpretation"],
            "rule_ids": [item["rule_id"]],
            "confidence": item["propagated_confidence"],
            "source": "combined_feature_signals",
        }
        for item in analysis.get("combined_feature_signals", [])
    ][:3]


def _tension_statements(
    analysis: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "text": item["interpretation"],
            "rule_ids": [
                evidence["rule_id"] for evidence in item["evidence"]
            ],
            "confidence": item["confidence"],
            "source": "cross_domain_tensions",
        }
        for item in analysis.get("cross_domain_tensions", [])
    ]


def validate_narration(
    narration: Any, analysis: dict[str, Any]
) -> None:
    """Reject narrator output that is not traceable to structured analysis."""
    if not isinstance(narration, dict) or narration.get("grounded_only") is not True:
        raise ValueError("Narration must declare grounded_only=true.")
    sections = narration.get("sections")
    if not isinstance(sections, dict):
        raise ValueError("Narration sections must be an object.")
    allowed_text = {
        item["interpretation"] for item in analysis.get("all_signals", [])
    }
    allowed_text.update(
        item["interpretation"]
        for item in analysis.get("cross_domain_tensions", [])
    )
    allowed_text.update({DISCLAIMER, GUIDANCE})
    allowed_rule_ids = {
        item["rule_id"] for item in analysis.get("all_signals", [])
    }
    for heading, statements in sections.items():
        if not isinstance(heading, str) or not isinstance(statements, list):
            raise ValueError("Narration section entries must be arrays.")
        for statement in statements:
            if not isinstance(statement, dict):
                raise ValueError("Narration statements must be objects.")
            text = statement.get("text")
            rule_ids = statement.get("rule_ids")
            if text not in allowed_text:
                raise ValueError("Narration contains an ungrounded statement.")
            if (
                not isinstance(rule_ids, list)
                or not all(
                    isinstance(rule_id, str)
                    and rule_id in allowed_rule_ids
                    for rule_id in rule_ids
                )
            ):
                raise ValueError("Narration contains an unknown rule reference.")
    expected_text = "\n".join(
        f"{heading}: " + " ".join(item["text"] for item in statements)
        for heading, statements in sections.items() if statements
    )
    if narration.get("text") != expected_text:
        raise ValueError("Narration text must be rendered from grounded sections.")
    if narration.get("disclaimer") != DISCLAIMER:
        raise ValueError("Narration must retain the required safety disclaimer.")
    combined = " ".join(
        str(value) for value in (
            narration.get("text", ""), narration.get("disclaimer", "")
        )
    ).lower()
    if any(term in combined for term in FORBIDDEN):
        raise ValueError("Narration contains forbidden claim language.")
