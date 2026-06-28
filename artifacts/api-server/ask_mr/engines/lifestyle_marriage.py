"""Luxury, travel, social life, home environment, abroad settlement after marriage."""
from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult
from ._chart_axes import house_axis_evidence, planet_line


def _detect_focus(q: str) -> str:
    if re.search(r"(?ix)\b(luxury|luxurious|amir|affluent|high\s*class|grand)\b", q):
        return "luxury"
    if re.search(r"(?ix)\b(travel|ghumna|trip|tour|vacation)\b", q):
        return "travel"
    if re.search(r"(?ix)\b(social\s*life|party|friends|society|log\s*se\s*milna)\b", q):
        return "social"
    if re.search(r"(?ix)\b(home|ghar|mahaul|environment|domestic)\b", q):
        return "home"
    if re.search(r"(?ix)\b(abroad|foreign|videsh|settle|settlement|pravas)\b", q):
        return "abroad"
    return "lifestyle_general"


def run_lifestyle_marriage(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    focus = _detect_focus(question or "")

    ven = r.planet("Venus") or {}
    jup = r.planet("Jupiter") or {}
    moon = r.planet("Moon") or {}
    rahu = r.planet("Rahu") or {}

    evidence: list[str] = []

    if focus in ("luxury", "lifestyle_general"):
        evidence.extend(
            [
                house_axis_evidence(r, 2, label="Married-life wealth/comfort axis (2nd house)"),
                house_axis_evidence(r, 11, label="Gains and lifestyle upgrades (11th house)"),
            ]
        )
        if ven.get("house") in (2, 4, 11):
            evidence.append(
                f"Luxury marker: Venus in house {ven.get('house')} sign {ven.get('sign')} — "
                "comfort, aesthetics and pleasant lifestyle after marriage."
            )
        if jup.get("house") in (2, 4, 9, 11):
            evidence.append(
                f"Jupiter in house {jup.get('house')} — expansion of home grace and comfortable living standard."
            )
        verdict = "Married lifestyle comfort/luxury: 2nd + 11th house with Venus/Jupiter tone"

    elif focus == "travel":
        evidence.extend(
            [
                house_axis_evidence(r, 9, label="Long travel/dharma journeys (9th house)"),
                house_axis_evidence(r, 12, label="Foreign travel/abroad movement (12th house)"),
            ]
        )
        if rahu.get("house") in (3, 9, 12):
            evidence.append(
                f"Rahu in house {rahu.get('house')} — frequent or unusual travel pattern after marriage."
            )
        if jup.get("house") in (9, 12):
            evidence.append(
                f"Jupiter in house {jup.get('house')} — blessed travel, pilgrimage or foreign trips with spouse."
            )
        verdict = "Travel after marriage: 9th + 12th house with Rahu/Jupiter movement theme"

    elif focus == "social":
        evidence.append(house_axis_evidence(r, 11, label="Social circle/gains/friends axis (11th house)"))
        if ven.get("house") in (7, 11):
            evidence.append(
                f"Venus in house {ven.get('house')} — active social charm; pleasant gatherings after marriage."
            )
        if jup.get("house") in (11, 5):
            evidence.append(
                f"Jupiter in house {jup.get('house')} — respected social network; warm community life."
            )
        if len(evidence) < 2:
            evidence.append("11th house links married social life — friends, gatherings and community tone.")
        verdict = "Social life after marriage: 11th house + Venus/Jupiter social markers"

    elif focus == "home":
        evidence.append(house_axis_evidence(r, 4, label="Home/domestic peace axis (4th house)"))
        moon_line = planet_line(r, "Moon", role="home peace/emotional environment")
        if moon_line:
            evidence.append(moon_line)
        if ven.get("house") == 4:
            evidence.append("Venus in 4th — beautiful peaceful home environment after marriage.")
        if moon.get("house") == 4:
            evidence.append("Moon in 4th — emotionally nurturing home atmosphere.")
        verdict = "Home environment after marriage: 4th house + Moon/Venus domestic tone"

    else:  # abroad
        evidence.extend(
            [
                house_axis_evidence(r, 12, label="Foreign settlement axis (12th house)"),
                house_axis_evidence(r, 9, label="Distant lands / fortune abroad (9th house)"),
            ]
        )
        lord7 = r.house_lord(7)
        p7l = r.planet(lord7) if lord7 else None
        if p7l and p7l.get("house") in (9, 12):
            evidence.append(
                f"7th lord {lord7} in house {p7l.get('house')} — spouse link to foreign land / abroad settlement."
            )
        if rahu.get("house") in (7, 9, 12):
            evidence.append(
                f"Rahu in house {rahu.get('house')} — foreign culture or settlement abroad through marriage theme."
            )
        verdict = "Abroad settlement after marriage: 12th + 9th + 7th-lord in travel houses"

    return EngineResult(
        archetype="lifestyle_marriage",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 70,
        answer_plan="2–3 sentences: lifestyle answer → 2 house/planet reasons → practical note.",
        summary=[
            f"QUESTION FOCUS: {focus}.",
            "Use ONLY lifestyle house evidence (2/4/9/11/12) — not personality or breakup axes.",
        ],
        evidence=evidence[:8],
        ignore=["timing dates/windows", "exact city/country name guarantee"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "lifestyle_marriage",
            "question_focus": focus,
        },
    )
