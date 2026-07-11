"""Engine orchestrator — primary + secondary engine execution."""
from __future__ import annotations

from typing import Any

from .registry import OrchestratorPlan, plan_orchestration
from .schema import EngineOutputV2


def _run_engine(engine_id: str, kundli: dict, question: str, **kwargs: Any) -> EngineOutputV2 | None:
    eid = engine_id.strip().lower()
    if eid == "commitment":
        from .engines.commitment import run_commitment_v2

        return run_commitment_v2(
            kundli,
            question,
            session_id=kwargs.get("session_id", ""),
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "loyalty_trust":
        from .engines.loyalty_trust import run_loyalty_trust_v2

        return run_loyalty_trust_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "compatibility":
        from .engines.compatibility import run_compatibility_v2

        return run_compatibility_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "breakup_risk":
        from .engines.breakup_risk import run_breakup_risk_v2

        return run_breakup_risk_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "patchup":
        from .engines.patchup import run_patchup_v2

        return run_patchup_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "secret_relationship":
        from .engines.secret_relationship import run_secret_relationship_v2

        return run_secret_relationship_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "partner_nature":
        from .engines.partner_nature import run_partner_nature_v2

        return run_partner_nature_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "communication":
        from .engines.communication import run_communication_v2

        return run_communication_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "emotional_attachment":
        from .engines.emotional_attachment import run_emotional_attachment_v2

        return run_emotional_attachment_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "family_approval":
        from .engines.family_approval import run_family_approval_v2

        return run_family_approval_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "long_distance":
        from .engines.long_distance import run_long_distance_v2

        return run_long_distance_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "toxicity":
        from .engines.toxicity import run_toxicity_v2

        return run_toxicity_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    if eid == "one_sided_love":
        from .engines.one_sided_love import run_one_sided_love_v2

        return run_one_sided_love_v2(
            kundli,
            question,
            wants_explain=kwargs.get("wants_explain", False),
            orchestrator_meta=kwargs.get("orchestrator_meta"),
        )
    # Other engines: v1 adapter until migrated
    return None


def orchestrate(
    kundli: dict,
    question: str,
    *,
    dna_bucket: str | None = None,
    primary_archetype: str | None = None,
    session_id: str = "",
    wants_explain: bool = False,
) -> dict[str, Any]:
    plan = plan_orchestration(
        question,
        dna_bucket=dna_bucket,
        primary_archetype=primary_archetype,
    )
    meta = {"primary": plan.primary, "secondary": plan.secondary, "reason": plan.reason}

    primary_out = _run_engine(
        plan.primary,
        kundli,
        question,
        session_id=session_id,
        wants_explain=wants_explain,
        orchestrator_meta=meta,
    )

    secondary_out: list[dict[str, Any]] = []
    for sec in plan.secondary:
        out = _run_engine(
            sec,
            kundli,
            question,
            session_id=session_id,
            wants_explain=wants_explain,
            orchestrator_meta={**meta, "role": "secondary"},
        )
        if out:
            secondary_out.append(out.to_json_ready())

    if primary_out is None:
        return {
            "orchestrator": meta,
            "primary": None,
            "secondary": secondary_out,
            "combined_verdict": "",
        }

    combined = primary_out.verdict.headline
    if secondary_out:
        sec_labels = [s.get("verdict", {}).get("headline", "") for s in secondary_out if s]
        combined = f"{combined} | Also: {'; '.join(x for x in sec_labels if x)}"

    return {
        "orchestrator": meta,
        "primary": primary_out.to_json_ready(),
        "secondary": secondary_out,
        "combined_verdict": combined,
    }
