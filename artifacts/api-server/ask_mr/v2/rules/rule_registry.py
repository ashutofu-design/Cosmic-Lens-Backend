"""Central rule registry — engines import rules from here, not inline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .types import EngineRule
from .commitment_rules import RULE_PREFIX as COM_PREFIX
from .commitment_rules import RULES_VERSION as COM_RULES_VERSION
from .commitment_rules import commitment_rules
from .trust_rules import RULE_PREFIX as TRUST_PREFIX
from .trust_rules import RULES_VERSION as TRUST_RULES_VERSION
from .trust_rules import trust_rules
from .breakup_rules import RULE_PREFIX as BREAKUP_PREFIX
from .breakup_rules import RULES_VERSION as BREAKUP_RULES_VERSION
from .breakup_rules import breakup_rules

RulesFactory = Callable[[], list[EngineRule]]


@dataclass(frozen=True)
class RuleSetRegistration:
    rules_version: str
    rule_prefix: str
    factory: RulesFactory


RULE_REGISTRY: dict[str, RuleSetRegistration] = {
    "commitment": RuleSetRegistration(COM_RULES_VERSION, COM_PREFIX, commitment_rules),
    "loyalty_trust": RuleSetRegistration(TRUST_RULES_VERSION, TRUST_PREFIX, trust_rules),
    "breakup_risk": RuleSetRegistration(BREAKUP_RULES_VERSION, BREAKUP_PREFIX, breakup_rules),
}


def get_rule_registration(engine_id: str) -> RuleSetRegistration | None:
    return RULE_REGISTRY.get((engine_id or "").strip().lower())


def get_rules_version(engine_id: str, *, fallback_prefix: str = "GEN") -> str:
    reg = get_rule_registration(engine_id)
    if reg:
        return f"{reg.rule_prefix}-{reg.rules_version}"
    return f"{(fallback_prefix or 'GEN').strip().upper()}-1.0.0"


def get_registered_rules(engine_id: str) -> list[EngineRule] | None:
    reg = get_rule_registration(engine_id)
    if not reg:
        return None
    return reg.factory()
