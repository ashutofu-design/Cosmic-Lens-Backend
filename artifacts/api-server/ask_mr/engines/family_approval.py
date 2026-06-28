from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult


def run_family_approval(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    rahu_h = (r.planet("Rahu") or {}).get("house")
    sat_h = (r.planet("Saturn") or {}).get("house")
    jup_h = (r.planet("Jupiter") or {}).get("house")
    sun_h = (r.planet("Sun") or {}).get("house")

    friction = 0
    support = 0
    evidence: list[str] = []

    if rahu_h in (5, 7, 9, 11):
        friction += 2
        evidence.append("Rahu on relationship/dharma axis → family may find it unconventional at first.")
    if re.search(r"(?ix)\b(inter[\s-]?caste|intercaste|jaati|caste)\b", question or ""):
        evidence.append(
            "Inter-caste theme: Rahu/unconventional axis active — elders may resist at first; "
            "steady respectful approach + time softens resistance."
        )
        friction += 1
    if re.search(r"(?ix)\b(inter[\s-]?religion|interreligion|dharm|religion)\b", question or ""):
        evidence.append(
            "Inter-religion theme: tradition vs choice tension — patience and family dialogue reduce friction."
        )
        friction += 1
    if re.search(r"(?ix)\b(court\s*marriage)\b", question or ""):
        evidence.append(
            "Court marriage theme: independent choice over ritual — family may need time to accept formal union."
        )
    if sat_h in (2, 7, 9) or sun_h in (2, 9):
        friction += 1
        evidence.append("Authority/tradition indicators active → approval may need patience and proof.")
    if jup_h in (2, 9, 11):
        support += 2
        evidence.append("Jupiter connected to family/dharma support → elders can soften with time.")

    if support > friction:
        verdict = "Family approval: chances improve with steady approach"
        conf = "medium"
    elif friction > support:
        verdict = "Family approval: initial resistance likely; patience + process needed"
        conf = "medium"
    else:
        verdict = "Family approval: mixed signals; approach matters more than fate"
        conf = "low"

    if not evidence:
        evidence = ["No strong family-approval driver visible; treat as mixed/normal."]

    if len(evidence) < 2:
        evidence.append(
            "Family axis (2nd/9th/Jupiter) sets how much elders engage — respectful steady proof helps approval."
        )

    if re.search(r"(?ix)\b(family\s*involve|kitna\s*involve|ghar\s*walon\s*ka\s*role)\b", question or ""):
        evidence.append(
            "Family involvement level: Jupiter/Rahu on family axis — elders stay engaged; "
            "how much depends on respectful dialogue and steady proof of match."
        )

    return EngineResult(
        archetype="family_approval",
        verdict=verdict,
        confidence=conf,
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 short sentences: approval outlook → 1–2 reasons → practical approach.",
        summary=[
            "Avoid absolutes; suggest respectful communication and gradual trust-building.",
        ],
        evidence=evidence[:6],
        ignore=[
            "timing dates/windows",
            "breakup risk (unless asked)",
            "manglik (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "family_approval",
            "rahu_house": rahu_h,
            "saturn_house": sat_h,
            "jupiter_house": jup_h,
        },
    )

