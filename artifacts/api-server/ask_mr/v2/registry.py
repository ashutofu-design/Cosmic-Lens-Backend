"""Frozen module matrix + orchestrator routing — Architecture Freeze v1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ModuleFlag = Literal["always", "never", "timing", "optional"]

# Canonical chart module ids
CHART_MODULES = (
    "d1",
    "d9",
    "dasha",
    "transit",
    "kp",
    "ashtakavarga",
    "jaimini",
    "bcp",
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

# engine_id → module_id → flag
ENGINE_MODULE_MATRIX: dict[str, dict[str, ModuleFlag]] = {
    "loyalty_trust": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "commitment": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "compatibility": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "optional", "ashtakavarga": "always", "jaimini": "never", "bcp": "timing",
    },
    "partner_nature": {
        "d1": "always", "d9": "always", "dasha": "never", "transit": "never",
        "kp": "never", "ashtakavarga": "never", "jaimini": "always", "bcp": "never",
    },
    "communication": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "never", "bcp": "never",
    },
    "emotional_attachment": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "timing", "bcp": "never",
    },
    "secret_relationship": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "breakup_risk": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "patchup": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "family_approval": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "never", "jaimini": "never", "bcp": "always",
    },
    "long_distance": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "always",
        "kp": "timing", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "toxicity": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "timing", "bcp": "never",
    },
    "one_sided_love": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "always", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "chemistry": {
        "d1": "always", "d9": "always", "dasha": "never", "transit": "never",
        "kp": "never", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "bed_intimacy": {
        "d1": "always", "d9": "always", "dasha": "never", "transit": "never",
        "kp": "never", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "karmic_marriage": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "timing",
        "kp": "always", "ashtakavarga": "never", "jaimini": "always", "bcp": "timing",
    },
    "relationship_future": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "timing", "ashtakavarga": "always", "jaimini": "timing", "bcp": "never",
    },
    "relationship_decisions": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "relationship_verification": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "relationship_remedies": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "timing", "bcp": "always",
    },
}

_TIMING_RX = __import__("re").compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|kis\s+(saal|year|mahine|month)|milega|milegi|"
    r"dasha|antardasha|mahadasha|transit|gochar|window|phase|samay|timing"
    r")\b"
)


def question_has_timing_trigger(question: str) -> bool:
    return bool(_TIMING_RX.search(question or ""))


def modules_for_engine(engine_id: str, question: str) -> list[str]:
    """Resolve which modules to load for this engine + question."""
    eid = (engine_id or "").strip().lower()
    row = ENGINE_MODULE_MATRIX.get(eid)
    if not row:
        return ["d1"]
    timing = question_has_timing_trigger(question)
    out: list[str] = []
    for mod in CHART_MODULES:
        flag = row.get(mod, "never")
        if flag == "always":
            out.append(mod)
        elif flag == "optional":
            out.append(mod)
        elif flag == "timing" and timing:
            out.append(mod)
    return out


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

    # de-dupe preserving order
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
