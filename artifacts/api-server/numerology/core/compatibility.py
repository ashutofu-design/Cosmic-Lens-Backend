"""Behavioral number compatibility (1–9) — no graha/planet model."""
from __future__ import annotations

from typing import Any, Dict, List

from numerology.core.digits import ARCHETYPE_BY_DRIVER, reduce_number

# T=twin, F=high sync, N=balanced, E=high friction (number psychology)
_REL: Dict[int, Dict[int, str]] = {
    1: {1: "T", 2: "F", 3: "F", 4: "E", 5: "N", 6: "E", 7: "E", 8: "E", 9: "F"},
    2: {1: "F", 2: "T", 3: "N", 4: "E", 5: "F", 6: "N", 7: "E", 8: "N", 9: "N"},
    3: {1: "F", 2: "N", 3: "T", 4: "N", 5: "E", 6: "E", 7: "N", 8: "N", 9: "F"},
    4: {1: "E", 2: "E", 3: "N", 4: "T", 5: "F", 6: "F", 7: "N", 8: "F", 9: "E"},
    5: {1: "N", 2: "F", 3: "E", 4: "F", 5: "T", 6: "F", 7: "F", 8: "N", 9: "N"},
    6: {1: "E", 2: "N", 3: "E", 4: "F", 5: "F", 6: "T", 7: "F", 8: "F", 9: "N"},
    7: {1: "E", 2: "E", 3: "N", 4: "N", 5: "F", 6: "F", 7: "T", 8: "F", 9: "E"},
    8: {1: "E", 2: "N", 3: "N", 4: "F", 5: "N", 6: "F", 7: "F", 8: "T", 9: "E"},
    9: {1: "F", 2: "N", 3: "F", 4: "E", 5: "N", 6: "N", 7: "E", 8: "E", 9: "T"},
}

_REL_SCORE = {"T": 95, "F": 80, "N": 60, "E": 30}
_REL_LABEL = {"T": "MIRROR", "F": "HIGH SYNC", "N": "BALANCED", "E": "HIGH FRICTION"}


def rel_code(a: int, b: int) -> str:
    return _REL.get(reduce_number(a), {}).get(reduce_number(b), "N")


def compat_label(code: str) -> str:
    return _REL_LABEL.get(code, "BALANCED")


def number_relationship(driver: int, other: int) -> Dict[str, Any]:
    code = rel_code(driver, other)
    base = _REL_SCORE[code]
    return {
        "code": code,
        "label": compat_label(code),
        "score": base,
        "archetype": ARCHETYPE_BY_DRIVER.get(reduce_number(other), "—"),
    }


def compatibility_row(driver: int, n: int) -> Dict[str, Any]:
    code = rel_code(driver, n)
    base = _REL_SCORE[code]
    love = base + (5 if n in (2, 6) else 0) - (5 if n == 8 else 0)
    marriage = base + (5 if n in (1, 6) else 0) - (10 if n == 7 else 0)
    business = base + (5 if n in (5, 8) else 0) - (5 if n == 7 else 0)
    return {
        "number": n,
        "archetype": ARCHETYPE_BY_DRIVER.get(n, "—"),
        "label": compat_label(code),
        "love": max(20, min(100, love)),
        "marriage": max(20, min(100, marriage)),
        "business": max(20, min(100, business)),
    }


def deep_compatibility_pack(driver: int) -> Dict[str, Any]:
    rows = [compatibility_row(driver, n) for n in range(1, 10)]
    sorted_avg = sorted(rows, key=lambda r: -(r["love"] + r["marriage"] + r["business"]))
    return {
        "driver": driver,
        "rows": rows,
        "top3_best": sorted_avg[:3],
        "top3_worst": sorted_avg[-3:][::-1],
    }
