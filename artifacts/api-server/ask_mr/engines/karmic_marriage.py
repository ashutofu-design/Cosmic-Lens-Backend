"""Soulmate, karmic debt, past-life connection, spiritual growth through marriage."""
from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult
from ._chart_axes import house_axis_evidence, planet_line
from ._person_signals import build_person_signals, pick_notes


def _detect_focus(q: str) -> str:
    if re.search(r"(?ix)\b(soul\s*mate|soulmate|twin\s*flame)\b", q):
        return "soulmate"
    if re.search(r"(?ix)\b(past\s*life|pichle\s*janam|purva\s*janm)\b", q):
        return "past_life"
    if re.search(r"(?ix)\b(karmic|karma\s*debt|rin|debt)\b", q):
        return "karmic_debt"
    if re.search(r"(?ix)\b(spiritual\s*growth|aadhyatmik|dharma\s*through\s*marriage)\b", q):
        return "spiritual_growth"
    return "karmic_general"


def run_karmic_marriage(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    sig = build_person_signals(k)
    focus = _detect_focus(question or "")

    rahu = r.planet("Rahu") or {}
    ketu = r.planet("Ketu") or {}
    sat = r.planet("Saturn") or {}
    ven = r.planet("Venus") or {}
    occ7 = r.occupants(7)
    occ5 = r.occupants(5)

    evidence: list[str] = [
        house_axis_evidence(r, 7, label="Marriage/karma axis (7th house)"),
        house_axis_evidence(r, 5, label="Past merit/romance karma axis (5th house)"),
        f"Rahu in house {rahu.get('house')} sign {rahu.get('sign')} — karmic twist / sudden bond theme.",
        f"Ketu in house {ketu.get('house')} sign {ketu.get('sign')} — past-life detachment or deep recognition theme.",
    ]

    karmic_hits = pick_notes(
        sig,
        [
            "nodes on 7th",
            "Ketu influence on 7th",
            "Rahu on 7th axis",
            "Saturn on 7th",
            "Saturn-Moon link",
            "Venus under nodal pull",
            "hidden ties",
        ],
        limit=5,
    )
    for line in karmic_hits:
        evidence.append(f"Karmic signal: {line}")

    if focus == "soulmate":
        if "Venus" in occ7 or ven.get("house") in (1, 5, 7, 9):
            evidence.append(
                "Soulmate marker: Venus strong on partnership/love axis — deep recognition and natural fit bond."
            )
        if "Moon" in occ7:
            evidence.append("Moon in 7th — soulmate-type emotional mirror; feels like 'pehchan' from early bond.")
        if "Jupiter" in occ7:
            evidence.append("Jupiter in 7th — dharmic soulmate tone; growth-oriented sacred partnership.")
        verdict = "Soulmate pattern: Venus-Jupiter-Moon on 7th/5th with nodal depth if present"
    elif focus == "past_life":
        if ketu.get("house") in (5, 7) or "Ketu" in str(occ7):
            evidence.append(
                "Ketu on love/marriage axis — past-life connection feel; instant familiarity or karmic déjà vu."
            )
        if rahu.get("house") in (5, 7) or sig.rahu_on_7th_axis:
            evidence.append(
                "Rahu on relationship axis — unfinished past-life story pulling toward this bond."
            )
        verdict = "Past-life connection: Ketu/Rahu on 5th-7th relationship axis"
    elif focus == "karmic_debt":
        if sat.get("house") in (5, 7, 8) or sig.saturn_on_7th:
            evidence.append(
                f"Saturn in house {sat.get('house')} on marriage axis — karmic lesson/debt to repay through patience in relationship."
            )
        if sig.separation_yoga:
            evidence.append(
                "Separation-repair yoga — karmic debt shows as tests; effort and dharma reduce karmic load."
            )
        verdict = "Karmic debt in marriage: Saturn + nodes on 5H/7H/8H — lessons through partnership"
    elif focus == "spiritual_growth":
        jup = planet_line(r, "Jupiter", role="dharma/spiritual growth")
        if jup:
            evidence.append(jup)
        evidence.append(house_axis_evidence(r, 9, label="Dharma/spiritual growth axis (9th house)"))
        if "Jupiter" in occ7 or (r.planet("Jupiter") or {}).get("house") in (1, 5, 9, 12):
            evidence.append(
                "Jupiter linked to partnership — marriage becomes path of wisdom, faith and spiritual maturity."
            )
        verdict = "Spiritual growth through marriage: Jupiter + 9th house dharma linked to 7th bond"
    else:
        verdict = "Karmic marriage theme: nodes + Saturn on relationship axis — purpose-driven bond"

    if "Moon" in occ5:
        evidence.append("Moon in 5th — emotional karma from past affection cycles carried into this love path.")

    return EngineResult(
        archetype="karmic_marriage",
        verdict=verdict,
        confidence="medium",
        word_budget=100 if wants_explain else 75,
        answer_plan="2–3 sentences: karmic theme → 2 evidence reasons → hopeful dharma note (not doom).",
        summary=[
            f"QUESTION FOCUS: {focus}.",
            "Tone: karmic but hopeful — lessons + growth, not fatalistic curse language.",
            "Use Rahu/Ketu/Saturn/5H/7H evidence only for this question.",
        ],
        evidence=evidence[:10],
        ignore=["timing dates/windows", "exact past-life story invention", "cursed marriage language"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "karmic_marriage",
            "question_focus": focus,
        },
    )
