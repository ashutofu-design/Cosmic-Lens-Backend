"""Children, parenting style, family values — 5H / 11-from-7 / 9H axes."""
from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult
from ._chart_axes import house_axis_evidence, planet_line


def _detect_focus(q: str) -> str:
    if re.search(r"(?ix)\b(parenting|parent\s*style|bachon\s*ke\s*saath|bacchon|children)\b", q):
        if re.search(r"(?ix)\b(bond|saath|rishta|connect|pyaar)\b", q):
            return "children_bond"
        return "parenting_style"
    if re.search(r"(?ix)\b(family\s*values?|sanskaar|tradition|ritual|dharma)\b", q):
        return "family_values"
    if re.search(r"(?ix)\b(bach|child|kids?)\b", q):
        return "children_bond"
    return "parenting_style"


def run_children_parenting(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    focus = _detect_focus(question or "")

    # 5H = children; 11H = 5th from 7th = spouse's role toward children/gains;
    # 9H = dharma/values; 2H = family traditions.
    evidence: list[str] = [
        house_axis_evidence(r, 5, label="Children axis (5th house)"),
        house_axis_evidence(r, 11, label="Spouse-with-children axis (5th from spouse / 11th house)"),
    ]
    jup = planet_line(r, "Jupiter", role="children/blessing karak")
    if jup:
        evidence.append(jup)
    moon = planet_line(r, "Moon", role="nurture/emotional parenting")
    if moon:
        evidence.append(moon)

    if focus == "parenting_style":
        lord5 = r.house_lord(5)
        p5l = r.planet(lord5) if lord5 else None
        occ11 = r.occupants(11)
        if p5l:
            evidence.append(
                f"Parenting style: 5th lord {lord5} in house {p5l.get('house')} sign {p5l.get('sign')} — "
                "how spouse guides/disciplines children."
            )
        if "Jupiter" in occ11:
            evidence.append(
                "Jupiter in 11th-from-7th axis — spouse parenting: wise, fair, teaching-oriented with kids."
            )
        if "Saturn" in occ11:
            evidence.append(
                "Saturn in 11th-from-7th axis — spouse parenting: structured, disciplined, duty-first with children."
            )
        if "Moon" in occ11:
            evidence.append(
                "Moon in 11th-from-7th axis — spouse parenting: emotionally involved, nurturing daily care."
            )
        verdict = "Spouse parenting style: read from 5th house + 11th-from-spouse + Jupiter"
    elif focus == "children_bond":
        occ5 = r.occupants(5)
        ven = r.planet("Venus") or {}
        evidence.append(
            f"Children bond: planets in 5th house {occ5 or 'none'} — emotional play/affection with kids."
        )
        if ven.get("house") in (5, 7, 11):
            evidence.append(
                f"Venus in house {ven.get('house')} — warm affectionate bond with children through love/play."
            )
        if "Moon" in occ5:
            evidence.append("Moon in 5th — deep emotional attachment and protective bond with children.")
        verdict = "Spouse bond with children: 5th house + Venus/Moon nurture markers"
    else:
        evidence.append(house_axis_evidence(r, 9, label="Dharma/family values axis (9th house)"))
        evidence.append(house_axis_evidence(r, 2, label="Family tradition axis (2nd house)"))
        jup_h = (r.planet("Jupiter") or {}).get("house")
        if jup_h in (2, 9, 5):
            evidence.append(
                f"Jupiter in house {jup_h} — strong family values, ethics and tradition in home life."
            )
        verdict = "Family values after marriage: 9th + 2nd house dharma/tradition pattern"

    return EngineResult(
        archetype="children_parenting",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 70,
        answer_plan="2–3 sentences: direct answer → 2 chart reasons → one practical family note.",
        summary=[
            f"QUESTION FOCUS: {focus} — use children/values axes ONLY, not 7H personality.",
            "Do NOT promise number of children unless classical rule explicitly in evidence.",
        ],
        evidence=evidence[:8],
        ignore=["timing dates/windows", "exact child count guarantee", "7th house partner personality"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "children_parenting",
            "question_focus": focus,
        },
    )
