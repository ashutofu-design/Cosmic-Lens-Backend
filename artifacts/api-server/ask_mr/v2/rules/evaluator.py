"""Rule evaluator — runs engine rules against ModuleBundle."""
from __future__ import annotations

from typing import Any

from ..modules.types import ModuleBundle
from .priority import DEFAULT_RULE_PRIORITY, MODULE_PRIORITY
from .types import EngineRule, FiredRule


class RuleEvaluator:
    def evaluate(
        self,
        rules: list[EngineRule],
        bundle: ModuleBundle,
        ctx: dict[str, Any],
    ) -> list[FiredRule]:
        fired: list[FiredRule] = []
        for rule in rules:
            try:
                if not rule.condition(bundle, ctx):
                    continue
            except Exception:
                continue
            ev = ""
            if rule.evidence:
                try:
                    ev = rule.evidence(bundle, ctx) or ""
                except Exception:
                    ev = rule.label
            else:
                ev = rule.label
            pri = rule.priority if rule.priority < DEFAULT_RULE_PRIORITY else MODULE_PRIORITY.get(
                rule.module, DEFAULT_RULE_PRIORITY
            )
            fired.append(
                FiredRule(
                    rule_id=rule.rule_id,
                    module=rule.module,
                    priority=pri,
                    polarity=rule.polarity,
                    weight=rule.weight,
                    label=rule.label,
                    evidence=ev,
                )
            )
        fired.sort(key=lambda r: (r.priority, -r.weight))
        return fired
