"""Frozen module matrix + orchestrator routing — Architecture Freeze v1."""
from __future__ import annotations

from dataclasses import dataclass

from .module_registry import (
    CHART_MODULES,
    ENGINE_MODULE_MATRIX,
    ModuleFlag,
    modules_for_engine,
    modules_for_engine_static,
    question_has_timing_trigger,
)

FROZEN_ENGINE_IDS: frozenset[str] = frozenset({
    "loyalty_trust",
    "commitment",
    "compatibility",
    "partner_nature",
    "communication",
    "emotional_attachment",
    "secret_relationship",
    "breakup_risk",
    "patchup",
    "family_approval",
    "long_distance",
    "toxicity",
    "one_sided_love",
    "chemistry",
    "bed_intimacy",
    "karmic_marriage",
    "relationship_future",
    "relationship_decisions",
    "relationship_verification",
    "relationship_remedies",
})


@dataclass(frozen=True)
class OrchestratorPlan:
    primary: str
    secondary: list[str]
    reason: str


def plan_orchestration(
    question: str,
    *,
    dna_bucket: str | None = None,
    primary_archetype: str | None = None,
) -> OrchestratorPlan:
    """Primary + secondary engines for multi-theme questions."""
    q = (question or "").strip().lower()
    bucket = (dna_bucket or "").strip().lower()
    primary = (primary_archetype or "").strip().lower()

    secondary: list[str] = []

    affair_kw = __import__("re").search(
        r"(?ix)\b(another\s+girl|another\s+boy|dusri|kisi\s+aur|third\s+person|"
        r"affair|chakkar|secret|hidden)\b",
        q,
    )
    trust_kw = __import__("re").search(
        r"(?ix)\b(trust|loyal|vishwas|cheat|dhokha|faithful)\b",
        q,
    )

    if not primary:
        if bucket == "trust_loyalty" or (trust_kw and not bucket):
            primary = "loyalty_trust"
        elif bucket == "commitment":
            primary = "commitment"
        elif bucket == "third_person_infidelity":
            primary = "secret_relationship"
        else:
            primary = "commitment"

    if primary == "loyalty_trust" and affair_kw:
        secondary.append("secret_relationship")
    elif primary == "commitment" and affair_kw:
        secondary.extend(["loyalty_trust", "secret_relationship"])
    elif primary == "relationship_decisions" and affair_kw:
        secondary.append("secret_relationship")
    elif bucket == "communication" and trust_kw:
        secondary.append("loyalty_trust")

    seen = {primary}
    sec_clean: list[str] = []
    for s in secondary:
        if s not in seen and s in FROZEN_ENGINE_IDS:
            seen.add(s)
            sec_clean.append(s)

    reason = f"primary={primary}"
    if sec_clean:
        reason += f"; secondary={','.join(sec_clean)}"
    return OrchestratorPlan(primary=primary, secondary=sec_clean, reason=reason)
