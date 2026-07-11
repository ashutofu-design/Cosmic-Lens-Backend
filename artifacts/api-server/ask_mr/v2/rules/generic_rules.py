"""Generic rules fallback for engines without a dedicated rule file yet."""
from __future__ import annotations

from ..engine_spec import EngineSpec
from ._skeleton import build_skeleton_rules
from .types import EngineRule


def generic_rules_for(spec: EngineSpec) -> list[EngineRule]:
    return build_skeleton_rules(
        rule_prefix=spec.rule_prefix,
        positive_signal_keys=spec.positive_signal_keys,
        negative_signal_keys=spec.negative_signal_keys,
    )
