"""Shared helpers for chart-module rule conditions."""
from __future__ import annotations

from ..modules.types import ModuleBundle


def mod_score(bundle: ModuleBundle, mod: str, threshold: int, op: str) -> bool:
    m = bundle.modules.get(mod)
    if not m or not m.loaded:
        return False
    if op == "gte":
        return m.score >= threshold
    if op == "lte":
        return m.score <= threshold
    return False


def has_factor(bundle: ModuleBundle, mod: str, polarity: str) -> bool:
    m = bundle.modules.get(mod)
    if not m:
        return False
    return m.polarity == polarity
