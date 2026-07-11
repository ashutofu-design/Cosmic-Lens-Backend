from __future__ import annotations

import re

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, risk_band_high_is_bad
from vedic.love_reality.relationship_signals import PersonSignals, _analyze_person  # type: ignore

from ..types import EngineResult


_BREAKUP_KEYWORDS_IGNORE = [
    "spouse profession",
    "love vs arranged",
    "timing dates/windows",
    "manglik (unless asked)",
]


def _risk_level_from_weight(w: int) -> str:
    # Map affliction_weight (~0-80+) to a 0-100 risk score band
    # (high score = worse). Keep deterministic + simple.
    score = min(100, max(0, int(round(w * 1.25))))
    return risk_band_high_is_bad(score)


def _pick_evidence(sig: PersonSignals) -> list[str]:
    # Use engine-written notes so planet+meaning is already embedded.
    # Filter to the breakup/separation domain; keep top drivers first.
    out: list[str] = []
    notes = list(sig.notes or [])

    def keep(rx: str) -> None:
        for n in notes:
            if len(out) >= 8:
                return
            if rx.lower() in n.lower() and n not in out:
                out.append(n.replace(f"{sig.name}'s ", "").replace(f"{sig.name}: ", ""))

    # Highest-signal breakup drivers first
    keep("Saturn on 7th")
    keep("Mars on 7th")
    keep("nodes on 7th")
    keep("7th lord in dusthana")
    keep("Moon under Saturn/Rahu")
    keep("Moon in 8th")
    keep("Venus in dusthana")
    keep("12th lord in 5th")
    keep("5th lord")
    keep("Ketu influence on 7th")
    keep("hidden ties")

    # De-duplicate + cap
    clean: list[str] = []
    for n in out:
        n2 = (n or "").strip()
        if n2 and n2 not in clean:
            clean.append(n2)
    return clean[:6]


def run_breakup_risk(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    try:
        from ask_mr.v2 import v2_enabled_for
        from ask_mr.v2.adapter import v2_to_engine_result
        from ask_mr.v2.engines.breakup_risk import run_breakup_risk_v2

        if v2_enabled_for("breakup_risk"):
            out = run_breakup_risk_v2(kundli, question, wants_explain=wants_explain)
            return v2_to_engine_result(out)
    except Exception:
        pass

    # Ensure KundliReader name is stable so notes are predictable.
    k = dict(kundli or {})
    k.setdefault("name", "You")
    reader = KundliReader(k)
    sig = _analyze_person(reader)

    risk = _risk_level_from_weight(int(sig.affliction_weight or 0))
    recon = bool(sig.reconnection_yoga)
    sep = bool(sig.separation_yoga)

    verdict = f"Breakup/separation risk: {risk}"
    if sep and not recon:
        verdict += " (distance theme stronger than repair)"
    elif sep and recon:
        verdict += " (repair possible with effort)"
    elif (not sep) and recon:
        verdict += " (repair capacity present)"

    evidence = _pick_evidence(sig)
    if re.search(r"(?ix)\b(toxic|manipulat|unhealthy)\b", question or ""):
        if sig.rahu_on_7th_axis or sig.third_person_risk:
            evidence.insert(0, "Toxic pattern: Rahu/hidden-stress on partnership axis — emotional drain if boundaries weak.")
        if sig.mars_on_7th and sig.saturn_on_7th:
            evidence.insert(0, "Toxic pattern: Mars+Saturn on 7th — heated conflicts + cold distance cycle; repair needs both calm.")
    if not evidence:
        evidence = ["No strong separation driver triggered; signals look mixed/normal."]
    if re.search(r"(?ix)\b(toot\w*|tut\w*|breakup|separation|divorce)\b", question or ""):
        evidence.insert(0, f"Breakup/separation signal: {verdict} — chart friction on partnership axis.")

    summary: list[str] = []
    summary.append("Answer should be cautious and practical (repair advice), not fatalistic.")
    if recon:
        summary.append("Reconnection capacity exists — repair habits can change the outcome.")
    if sig.third_person_risk or sig.loyalty_risk_high:
        summary.append("Trust/loyalty axis is sensitive — avoid assumptions; communicate clearly.")

    word_budget = 55 if not wants_explain else 85
    return EngineResult(
        archetype="breakup_risk",
        verdict=verdict,
        confidence="medium" if risk in ("medium", "high") else "high",
        word_budget=word_budget,
        answer_plan="2–3 short sentences: direct risk → 1–2 reasons → soft repair/outlook line.",
        summary=summary[:4],
        evidence=evidence,
        ignore=_BREAKUP_KEYWORDS_IGNORE,
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "breakup_risk",
            "affliction_weight": int(sig.affliction_weight or 0),
            "risk_level": risk,
            "separation_yoga": bool(sig.separation_yoga),
            "reconnection_yoga": bool(sig.reconnection_yoga),
            "third_person_risk": bool(sig.third_person_risk),
            "loyalty_risk_high": bool(sig.loyalty_risk_high),
        },
    )

