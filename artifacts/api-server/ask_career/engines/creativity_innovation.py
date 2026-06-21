"""Creativity / content-career engine — YouTuber, influencer, creative fields."""
from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination, reader, subtype_hits


def run_creativity_innovation(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    q = (question or "").lower()
    is_youtube = bool(re.search(r"(?ix)\b(youtuber|youtube|vlogger|streamer)\b", q))

    ven = r.planet("Venus") or {}
    merc = r.planet("Mercury") or {}
    rahu = r.planet("Rahu") or {}

    evidence = inclination_evidence(inc, limit=3, include_job_split=False)
    evidence.append(
        f"Creative axis: Venus house {ven.get('house')} + Mercury house {merc.get('house')} — "
        "design/communication/creative expression in work."
    )
    comm_tags = subtype_hits(inc, "comm")
    if comm_tags:
        evidence.append(f"Creative/commercial subtypes: {', '.join(comm_tags)}.")
    if rahu.get("house") in (3, 5, 10, 11):
        evidence.append(
            f"Rahu in house {rahu.get('house')} — innovation/unconventional creative or tech ideas."
        )
    if is_youtube:
        evidence.append(
            "YouTube/content creator fit: Mercury-Venus communication + public-facing "
            "commercial subtype supports camera, content, audience-building work."
        )
        if merc.get("house") in (3, 5, 7, 10, 11) or ven.get("house") in (3, 5, 7, 10, 11):
            evidence.append(
                f"Content signal: Mercury house {merc.get('house')}, Venus house {ven.get('house')} — "
                "expressive on-camera / audience connection potential."
            )

    comm = int(inc.get("commercial_score") or 0)
    fit = comm >= 32 or merc.get("house") in (3, 5, 7, 10, 11) or ven.get("house") in (3, 5, 7, 10, 11)

    if is_youtube:
        verdict = (
            "YouTube/content creator: suitable pattern visible"
            if fit
            else "YouTube/content creator: possible with consistent content habit — chart not dominant creator theme"
        )
        focus = "YouTube/content creator path"
    else:
        verdict = (
            "Creative/innovation career: suitable pattern visible"
            if fit
            else "Creative/innovation career: possible with skill-building — not dominant chart theme"
        )
        focus = "Creative/innovation career path"

    return EngineResult(
        archetype="creativity_innovation",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 70,
        answer_plan="Direct yes/no for the creative path asked → 2 creative-axis reasons.",
        summary=[
            f"QUESTION FOCUS: {focus} — answer ban sakta hun / suit karega directly.",
            "Do NOT answer job vs business % split — user asked about THIS creative path.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "marriage", "job vs business split"],
        checks={"slice_type": "career_engine_v1", "archetype": "creativity_innovation", "focus": "youtube" if is_youtube else "creative"},
    )
