"""Frozen version constants — bump rules_version when COM/TRUST rules change."""
from __future__ import annotations

SCHEMA_VERSION = "2.0"
DEFAULT_ENGINE_VERSION = "2.0.0"


def default_rules_version(rule_prefix: str) -> str:
    return f"{(rule_prefix or 'GEN').strip().upper()}-1.0.0"
