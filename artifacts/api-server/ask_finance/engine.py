from __future__ import annotations

import os

from .classifier import classify_finance_archetype
from .types import EngineResult


def run_finance_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_FINANCE_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_FINANCE_ENGINE=0 — caller should use legacy finance path")

    archetype = (archetype or "").strip().lower() or classify_finance_archetype(question)

    if archetype == "income_source":
        from .engines.income_source import run_income_source
        return run_income_source(kundli, question, wants_explain=wants_explain)
    if archetype == "savings_capacity":
        from .engines.savings_capacity import run_savings_capacity
        return run_savings_capacity(kundli, question, wants_explain=wants_explain)
    if archetype == "expense_pattern":
        from .engines.expense_pattern import run_expense_pattern
        return run_expense_pattern(kundli, question, wants_explain=wants_explain)
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
