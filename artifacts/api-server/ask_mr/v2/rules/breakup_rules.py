"""Breakup / separation risk rules (BREAKUP-xxx) — deepen in implementation phase."""
from __future__ import annotations

from .types import EngineRule
from ._skeleton import build_skeleton_rules

RULE_PREFIX = "BREAKUP"
RULES_VERSION = "1.0.0"


def breakup_rules() -> list[EngineRule]:
    return build_skeleton_rules(
        rule_prefix=RULE_PREFIX,
        positive_signal_keys=("reconnection_yoga",),
        negative_signal_keys=(
            "separation_yoga",
            "saturn_on_7th",
            "mars_on_7th",
            "third_person_risk",
        ),
    )
