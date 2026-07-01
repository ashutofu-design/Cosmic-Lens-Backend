"""Shared helpers for small Ask gap static engines."""

from __future__ import annotations

import re
from typing import Callable

from ask_mr.types import EngineResult
from vedic.love_reality.scoring_core import KundliReader, SIGNS

TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:mahine|saal|year|month)|"
    r"milega|milegi|hoga|hogi|honge|aayega|aayegi|banega|banegi|"
    r"shuru\s+hoga|khatam|dasha|antardasha|gochar|transit|muhurat|timing|kitne\s+mahine"
    r")\b"
)

_BENEFIC = {1, 4, 5, 7, 9, 10, 11}
_DUSTHANA = {6, 8, 12}


def reader(kundli: dict) -> KundliReader:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    return KundliReader(k)


def house_axis(r: KundliReader, house: int, label: str) -> str:
    asc_i = r.asc_index()
    sign = SIGNS[(asc_i + house - 1) % 12] if isinstance(asc_i, int) else "unknown"
    lord = r.house_lord(house)
    pl = r.planet(lord) if lord else None
    occ = r.occupants(house)
    return (
        f"{label}: H{house} sign {sign}; lord {lord or '?'} in H"
        f"{pl.get('house') if pl else '?'} sign {pl.get('sign') if pl else '?'}; "
        f"occupants={occ or 'none'}."
    )


def planet_line(r: KundliReader, name: str, role: str, *, in_house_note: str = "") -> str:
    p = r.planet(name) or {}
    house = p.get("house")
    sign = p.get("sign")
    if not house:
        return f"{name} ({role}): placement not available."
    h = int(house)
    if in_house_note:
        tone = in_house_note
    elif h in _BENEFIC:
        tone = "supportive tone for this theme"
    elif h in _DUSTHANA:
        tone = "needs care, discipline and boundaries"
    else:
        tone = "mixed — effort and awareness both matter"
    return f"{name} ({role}): H{h} sign {sign} — {tone}."


def occupants_detail(r: KundliReader, house: int, label: str) -> list[str]:
    occ = r.occupants(house) or []
    if not occ:
        return [f"{label}: H{house} empty — judge from house lord placement."]
    return [f"{label}: {name} in H{house}." for name in occ]


def clamp_score(score: int) -> int:
    return max(18, min(92, score))


def score_label(score: int, high: str, mid: str, low: str) -> tuple[str, str]:
    if score >= 72:
        return high, "high"
    if score >= 55:
        return mid, "medium"
    return low, "low"


def gap_result(
    *,
    archetype: str,
    slice_type: str,
    kundli: dict,
    score: int,
    evidence: list[str],
    verdict_high: str,
    verdict_mid: str,
    verdict_low: str,
    summary: list[str],
    answer_plan: str,
    wants_explain: bool = False,
    score_key: str = "gap_score",
    ignore: list[str] | None = None,
) -> EngineResult:
    verdict, confidence = score_label(score, verdict_high, verdict_mid, verdict_low)
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 85,
        answer_plan=answer_plan,
        summary=summary,
        evidence=evidence,
        ignore=ignore or ["invented names", "exact dates", "guaranteed outcomes"],
        checks={
            "slice_type": slice_type,
            "archetype": archetype,
            score_key: score,
            "open_chart_qa": True,
        },
    )


def static_not_timing(question: str, scope_rx: re.Pattern[str]) -> bool:
    q = (question or "").strip()
    if not q or not scope_rx.search(q):
        return False
    return not TIMING_RX.search(q)
