"""Finance static engine — unified finance_engine_execution_v1 by default."""

from __future__ import annotations

import os
from typing import Any

from .classifier import classify_finance_archetype
from .types import EngineResult


def _legacy_slice_enabled() -> bool:
    return (os.environ.get("ASK_FINANCE_ENGINE") or "1").strip() == "0"


def _legacy_archetype_engines_enabled() -> bool:
    return (os.environ.get("ASK_FINANCE_LEGACY_ARCHETYPE_ENGINES") or "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _resolve_finance_archetype_label(question: str, archetype: str | None) -> str:
    archetype = (archetype or "").strip().lower()
    if not archetype:
        archetype = classify_finance_archetype(question)
    return archetype or "general_finance"


def _attach_finance_engine_execution(
    result: EngineResult,
    kundli: dict,
    *,
    question: str = "",
    llm_intent: dict | None = None,
) -> EngineResult:
    try:
        from finance_static.finance_facts import compute_finance_engine_execution

        pack = compute_finance_engine_execution(
            kundli if isinstance(kundli, dict) else {},
            question=question or "",
            routing_label=result.archetype or "",
            llm_intent=llm_intent,
        )
        checks = dict(result.checks or {})
        checks["finance_engine_execution"] = pack
        checks["d1_finance_facts"] = pack.get("d1") or {}
        checks["d9_finance_facts"] = pack.get("d9") or {}
        checks["engine_version"] = "finance_engine_execution_v1"
        checks["unified_execution"] = True
        checks["routing_label"] = result.archetype
        result.checks = checks
    except Exception as exc:
        checks = dict(result.checks or {})
        checks["finance_engine_execution_error"] = str(exc)[:180]
        result.checks = checks
    return result


def _run_legacy_archetype_engines(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str,
) -> EngineResult:
    if archetype == "income_source":
        from .engines.income_source import run_income_source
        return run_income_source(kundli, question, wants_explain=wants_explain)
    if archetype == "savings_capacity":
        from .engines.savings_capacity import run_savings_capacity
        return run_savings_capacity(kundli, question, wants_explain=wants_explain)
    if archetype == "save_vs_spend":
        from .engines.save_vs_spend import run_save_vs_spend
        return run_save_vs_spend(kundli, question, wants_explain=wants_explain)
    if archetype == "expense_pattern":
        from .engines.expense_pattern import run_expense_pattern
        return run_expense_pattern(kundli, question, wants_explain=wants_explain)
    if archetype == "spending_personality":
        from .engines.spending_personality import run_spending_personality
        return run_spending_personality(kundli, question, wants_explain=wants_explain)
    if archetype == "financial_discipline":
        from .engines.financial_discipline import run_financial_discipline
        return run_financial_discipline(kundli, question, wants_explain=wants_explain)
    if archetype == "investment_risk":
        from .engines.investment_risk import run_investment_risk
        return run_investment_risk(kundli, question, wants_explain=wants_explain)
    if archetype == "debt_loan":
        from .engines.debt_loan import run_debt_loan
        return run_debt_loan(kundli, question, wants_explain=wants_explain)
    if archetype == "property_money":
        from .engines.property_money import run_property_money
        return run_property_money(kundli, question, wants_explain=wants_explain)
    if archetype == "sudden_gain_loss":
        from .engines.sudden_gain_loss import run_sudden_gain_loss
        return run_sudden_gain_loss(kundli, question, wants_explain=wants_explain)
    if archetype == "business_profit":
        from .engines.business_profit import run_business_profit
        return run_business_profit(kundli, question, wants_explain=wants_explain)
    if archetype == "loss_reasons":
        from .engines.loss_reasons import run_loss_reasons
        return run_loss_reasons(kundli, question, wants_explain=wants_explain)
    if archetype == "wealth_potential":
        from .engines.wealth_potential import run_wealth_potential
        return run_wealth_potential(kundli, question, wants_explain=wants_explain)
    if archetype == "dhana_yoga":
        from .engines.dhana_yoga import run_dhana_yoga
        return run_dhana_yoga(kundli, question, wants_explain=wants_explain)

    from .engines.general_finance import run_general_finance
    return run_general_finance(kundli, question, wants_explain=wants_explain)


def run_finance_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
    llm_intent: dict | None = None,
) -> EngineResult:
    """Finance static — unified finance_engine_execution_v1 by default.

    Archetype is a routing label. Set ASK_FINANCE_LEGACY_ARCHETYPE_ENGINES=1
    to restore per-archetype score engines (EE pack still attached).
    """
    if _legacy_slice_enabled():
        raise RuntimeError("ASK_FINANCE_ENGINE=0 — caller should use legacy finance path")

    label = _resolve_finance_archetype_label(question, archetype)

    if _legacy_archetype_engines_enabled():
        result = _run_legacy_archetype_engines(
            kundli, question, wants_explain=wants_explain, archetype=label,
        )
        return _attach_finance_engine_execution(
            result, kundli, question=question or "", llm_intent=llm_intent,
        )

    dims_hint = ""
    try:
        from finance_static.finance_facts import compute_finance_facts

        facts = compute_finance_facts(kundli if isinstance(kundli, dict) else {})
        dims = facts.get("dimensions") or {}
        bits = []
        for k in ("wealth_potential", "income_stability", "saving_ability", "risk_leak"):
            row = dims.get(k) if isinstance(dims, dict) else None
            if isinstance(row, dict) and row.get("verdict"):
                bits.append(f"{k}={row.get('verdict')}")
        if bits:
            dims_hint = "; ".join(bits)
    except Exception:
        pass

    result = EngineResult(
        archetype=label,
        verdict=dims_hint or "",
        confidence="medium",
        word_budget=85 if wants_explain else 65,
        answer_plan=(
            "Read FINANCE_ENGINE_EXECUTION_JSON (D1 + D9). "
            f"routing_label={label} is the answer focus only — answer the user's exact "
            "finance/wealth question in warm Hinglish using pack facts, not invented placements."
        ),
        summary=[
            "Unified finance pack: D1 + D9 wealth axes (2L/11L / Jupiter / yogas).",
            f"Routing label (focus): {label}",
        ],
        evidence=[],
        ignore=["stock tips", "lottery guarantee", "exact money date"],
        checks={
            "slice_type": "finance_engine_v1",
            "archetype": label,
            "routing_label": label,
            "unified_execution": True,
        },
    )
    return _attach_finance_engine_execution(
        result, kundli, question=question or "", llm_intent=llm_intent,
    )


def finance_engine_slice_meta(result: EngineResult) -> dict[str, Any]:
    pos, neg, neu = result._finalize_evidence_split()
    checks = dict(result.checks or {})
    return {
        "slice": "finance_engine_v1",
        "topic": "finance",
        "archetype": result.archetype,
        "verdict": result.verdict,
        "summary": list(result.summary or []),
        "evidence": list(result.evidence or []),
        "evidence_positive": pos,
        "evidence_negative": neg,
        "evidence_neutral": neu,
        "ignore": list(result.ignore or []),
        "checks": checks,
        "skip_llm": bool(result.skip_llm),
        "word_budget": int(result.word_budget or 70),
        "narrator_mode": "engine_facts_only",
    }
