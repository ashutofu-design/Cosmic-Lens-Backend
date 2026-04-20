"""
Tier-1 Core Numerology Extras — calc helpers NOT already in extended.py.

Adds:
  • maturity_number(life_path, expression)
  • balance_number(name)  — sum of first letter of each name-word (Pyth)
  • hidden_passion(name)  — most-repeated letter value (1-9)
  • karmic_lessons(name)  — digits 1-9 missing from name's Pyth values

Pinnacles & Challenges are already available in vedic.numerology.practical
(compute_pinnacles_challenges). This file intentionally does NOT duplicate.
"""
from __future__ import annotations
from typing import Dict, List, Any
from collections import Counter

_PYTH = {c: ((i % 9) + 1) for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}
MASTER = {11, 22, 33}


def _reduce(n: int, keep_master: bool = True) -> int:
    n = abs(int(n))
    while n > 9:
        if keep_master and n in MASTER:
            return n
        n = sum(int(d) for d in str(n))
    return n


def maturity_number(life_path: int, expression: int) -> int:
    """Maturity = reduce(LP + Expression). Activates around age 35+."""
    if not life_path or not expression:
        return 0
    return _reduce(_reduce(life_path, keep_master=False)
                   + _reduce(expression, keep_master=False), keep_master=False)


def balance_number(name: str) -> int:
    """Balance = reduce(sum of Pythagorean value of first letter of each word)."""
    if not name:
        return 0
    parts = [p for p in name.strip().split() if p]
    initials = [p[0].lower() for p in parts if p[0].isalpha()]
    if not initials:
        return 0
    return _reduce(sum(_PYTH[c] for c in initials), keep_master=False)


def hidden_passion(name: str) -> Dict[str, Any]:
    """Hidden Passion = Pythagorean value of the most-repeated letter value.

    If a tie, returns all tied values (list).
    """
    if not name:
        return {"value": 0, "values": [], "count": 0}
    letters = [c.lower() for c in name if c.isalpha()]
    if not letters:
        return {"value": 0, "values": [], "count": 0}
    vals = [_PYTH[c] for c in letters]
    counter = Counter(vals)
    max_count = max(counter.values())
    top = sorted([v for v, c in counter.items() if c == max_count])
    return {"value": top[0], "values": top, "count": max_count}


def karmic_lessons(name: str) -> List[int]:
    """Karmic Lessons = digits 1-9 NOT present in name's Pyth letter values."""
    if not name:
        return list(range(1, 10))
    present = set()
    for c in name.lower():
        if c.isalpha():
            present.add(_PYTH[c])
    return sorted([n for n in range(1, 10) if n not in present])
