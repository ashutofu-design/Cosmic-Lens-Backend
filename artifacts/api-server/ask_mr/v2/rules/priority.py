"""Rule priority tiers — Architecture Freeze v1."""
from __future__ import annotations

# Lower number = evaluated first / wins ties
MODULE_PRIORITY: dict[str, int] = {
    "safety": 0,
    "d1": 10,
    "d9": 20,
    "ashtakavarga": 25,
    "bcp": 28,
    "jaimini": 30,
    "dasha": 40,
    "transit": 50,
    "kp": 60,
}

DEFAULT_RULE_PRIORITY = 100


def rule_sort_key(fired: dict) -> tuple[int, float]:
    """Sort fired rules: priority asc, weight desc."""
    pri = int(fired.get("priority") or DEFAULT_RULE_PRIORITY)
    w = float(fired.get("weight") or 0)
    return (pri, -w)
