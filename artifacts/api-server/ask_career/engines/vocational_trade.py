"""Vocational / skilled-trade career fit."""
from __future__ import annotations

import re

from ask_career.sector_registry import VOCATIONAL_RX
from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader

_TRADE_RX = [
    (re.compile(r"(?ix)\belectrician\b"), "electrician"),
    (re.compile(r"(?ix)\bplumber\b"), "plumber"),
    (re.compile(r"(?ix)\bmechanic\b"), "mechanic"),
    (re.compile(r"(?ix)\bcarpenter\b"), "carpenter"),
    (re.compile(r"(?ix)\bwelder\b"), "welder"),
    (re.compile(r"(?ix)\bdriver\b"), "driver"),
    (re.compile(r"(?ix)\btailor\b"), "tailor"),
    (re.compile(r"(?ix)\btechnician\b"), "technician"),
    (re.compile(r"(?ix)\bmason\b"), "mason"),
    (re.compile(r"(?ix)\bbarber\b"), "barber"),
]


def _trade(q: str) -> str:
    for rx, name in _TRADE_RX:
        if rx.search(q or ""):
            return name
    if VOCATIONAL_RX.search(q or ""):
        return "skilled_trade"
    return "skilled_trade"


def run_vocational_trade(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    trade = _trade(question or "")

    evidence = [
        house_axis(r, 6, "Daily craft/service (6th house)"),
        house_axis(r, 10, "Profession execution (10th house)"),
    ]
    evidence.extend(inclination_evidence(inc, limit=3, include_job_split=False))

    mars = r.planet("Mars") or {}
    sat = r.planet("Saturn") or {}
    merc = r.planet("Mercury") or {}
    evidence.append(
        f"Skilled trade axis: Mars execution house {mars.get('house')} + Saturn discipline house {sat.get('house')} + "
        f"Mercury skill house {merc.get('house')} — hands-on/service craft pattern."
    )
    evidence.append(
        f"Trade fit ({trade.replace('_', ' ')}): practical Mars-Saturn subtype supports vocational/skilled work."
    )

    fit = int(inc.get("psychology", {}).get("persistence", 50)) >= 45 or mars.get("house") in (3, 6, 10, 11)
    verdict = (
        f"Vocational/skilled trade ({trade.replace('_', ' ')}): suitable pattern visible"
        if fit
        else f"Vocational/skilled trade ({trade.replace('_', ' ')}): possible with apprenticeship — service craft not dominant theme"
    )

    return EngineResult(
        archetype="vocational_trade",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 65,
        answer_plan="Direct trade suitability → Mars/Saturn/Mercury evidence → skill note.",
        summary=[
            f"QUESTION FOCUS: {trade.replace('_', ' ')} / skilled trade.",
            "Answer THIS trade directly — do NOT pivot to job vs business % split.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "marriage"],
        checks={"slice_type": "career_engine_v1", "archetype": "vocational_trade", "trade": trade},
    )
