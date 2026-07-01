from __future__ import annotations

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

# Trust/commitment evidence — same relationship signal notes as general_mr/breakup (planet+meaning).
_LOYALTY_NEGATIVE_KEYS = [
    "Saturn on 7th",
    "Mars on 7th",
    "7th lord in dusthana",
    "7th lord debilitated",
    "Moon under Saturn/Rahu",
    "Moon in 8th",
    "nodes on 7th",
    "Ketu influence on 7th",
    "Venus-Mars conjunction",
    "12th lord in 7th",
    "12th lord in 5th",
    "hidden ties",
    "parallel attention",
    "Navamsa Moon debilitated",
    "Venus in dusthana",
    "Mercury debilitated",
    "obsession, pull, loyalty blur",
]

_LOYALTY_SUPPORT_KEYS = [
    "5th lord strong",
    "Saturn-Moon link",
    "Saturn as 7th lord in 7th",
]


def _pick_loyalty_evidence(sig) -> tuple[list[str], list[str]]:
    negative = pick_notes(sig, _LOYALTY_NEGATIVE_KEYS, limit=6)
    support = pick_notes(sig, _LOYALTY_SUPPORT_KEYS, limit=2)
    return negative, support


def _trust_level(sig, negative: list[str]) -> str:
    """Deterministic loyalty/commitment posture from chart signals + evidence."""
    if sig.third_person_risk or sig.venus_mars_conjunct_tight or sig.moon_in_8th:
        return "risky"
    if sig.loyalty_risk_high or sig.venus_mars_conjunct or sig.rahu_on_7th_axis:
        return "unstable"

    w = int(sig.affliction_weight or 0)
    n = len(negative)

    if n >= 3 or w >= 38:
        return "unstable"
    if n >= 2 or w >= 22 or (sig.saturn_on_7th and sig.mars_on_7th):
        return "mixed"
    if n >= 1 or w >= 14 or sig.saturn_on_7th or sig.mars_on_7th or sig.moon_afflicted:
        return "mixed"
    return "moderate"


def _trust_verdict(level: str) -> str:
    return {
        "moderate": "Trust/loyalty: mostly stable — clear talk keeps commitment strong",
        "mixed": "Trust/loyalty: mixed — commitment rehta hai par distance or friction trust test karta hai",
        "unstable": "Trust/loyalty: sensitive — clarity and boundaries keep bond safe",
        "risky": "Trust/loyalty: high-risk pattern — secrecy and impulse loyalty ko weak karte hain",
    }[level]


def run_loyalty_trust(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    from vedic.love_reality.scoring_core import KundliReader

    from ._chart_axes import house_axis_evidence, planet_line

    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    sig = build_person_signals(kundli)
    negative, support = _pick_loyalty_evidence(sig)
    level = _trust_level(sig, negative)
    verdict = _trust_verdict(level)

    evidence: list[str] = [
        house_axis_evidence(r, 5, label="Romance/trust axis (5th house)"),
        house_axis_evidence(r, 7, label="Partnership/loyalty axis (7th house)"),
    ]
    ven_line = planet_line(r, "Venus", role="love/trust karak")
    moon_line = planet_line(r, "Moon", role="emotional trust")
    if ven_line:
        evidence.append(ven_line)
    if moon_line:
        evidence.append(moon_line)
    for line in negative[:4]:
        evidence.append(f"Trust challenge: {line}")
    for line in support[:2]:
        if len(evidence) >= 6:
            break
        evidence.append(f"Trust support: {line}")

    if not evidence:
        evidence = ["No strong trust driver triggered; loyalty/commitment pattern looks normal."]

    summary = [
        "Answer loyalty/commitment level directly — confident pattern voice.",
        "NO shayad/ho sakta hai/lagta hai. Avoid accusations; focus on trust + boundaries.",
    ]
    if level in ("mixed", "unstable", "risky"):
        summary.append("Name the friction (distance/fights/hidden stress) then one practical trust habit.")
    if support:
        summary.append("Include one Trust support line (duty/loyalty strength) so answer is balanced.")

    return EngineResult(
        archetype="loyalty_trust",
        verdict=verdict,
        confidence="high" if level == "moderate" and len(negative) == 0 else "medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="2–3 short sentences: loyalty level → 1–2 chart reasons → one practical trust line.",
        summary=summary,
        evidence=evidence[:8],
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "love-vs-arranged",
            "manglik (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "loyalty_trust",
            "trust_level": level,
            "loyalty_risk_high": bool(sig.loyalty_risk_high),
            "third_person_risk": bool(sig.third_person_risk),
            "affliction_weight": int(sig.affliction_weight or 0),
            "negative_signal_count": len(negative),
        },
    )
