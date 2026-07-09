"""Contradiction detector — D1 vs D9 vs Dasha vs Transit conflicts."""
from __future__ import annotations

from .modules.types import ModuleBundle
from .schema import ContradictionReport


def detect_contradictions(bundle: ModuleBundle) -> ContradictionReport:
    pol: dict[str, str] = {}
    for mod_id, res in bundle.modules.items():
        if res.loaded:
            pol[mod_id] = res.polarity

    d1 = pol.get("d1")
    d9 = pol.get("d9")
    dasha = pol.get("dasha")
    transit = pol.get("transit")

    # Strong promise + temporary stress
    promise_pos = d1 in ("positive", "mixed") and d9 == "positive"
    stress_now = transit == "negative" or dasha == "negative"

    if promise_pos and stress_now:
        return ContradictionReport(
            detected=True,
            pattern="strong_promise_temporary_stress",
            summary="Mixed — strong marriage promise, temporary stress in dasha/transit",
            module_polarity=pol,
        )

    if d1 == "positive" and d9 == "negative":
        return ContradictionReport(
            detected=True,
            pattern="d1_d9_split",
            summary="Mixed — D1 promise stronger than D9 marriage sustenance",
            module_polarity=pol,
        )

    if d1 == "negative" and d9 == "positive":
        return ContradictionReport(
            detected=True,
            pattern="d9_rescue",
            summary="Mixed — D9 supports bond though D1 shows friction",
            module_polarity=pol,
        )

    if dasha == "positive" and transit == "negative":
        return ContradictionReport(
            detected=True,
            pattern="dasha_good_transit_bad",
            summary="Mixed — dasha supportive, transit phase stressful",
            module_polarity=pol,
        )

    return ContradictionReport(detected=False, module_polarity=pol)
