"""Run dedicated job/profession engines from job_registry profiles."""
from __future__ import annotations

from ask_career.job_registry import JobEngineEntry, get_job_profile
from ask_career.types import EngineResult
from ._career_base import (
    house_axis,
    inclination_evidence,
    load_inclination,
    reader,
    subtype_hits,
    trait_line,
)


def _score_profile(profile: JobEngineEntry, inc: dict, r) -> tuple[bool, int, list[str]]:
    job = int(inc.get("job_pct") or 50)
    comm = int(inc.get("commercial_score") or 0)
    struct = int(inc.get("structure_score") or 0)
    psych = inc.get("psychology") or {}

    tags = subtype_hits(inc, profile.subtype_kind)
    tags += subtype_hits(inc, "comm")
    tag_blob = " ".join(tags).lower()

    score = 0
    reasons: list[str] = []

    if profile.min_job_pct is not None:
        if job >= profile.min_job_pct:
            score += 16
            reasons.append(
                f"Employment tilt ~{job}% — {profile.label.lower()} aligns with job/service path."
            )
        elif job >= profile.min_job_pct - 8:
            score += 6
            reasons.append(f"Moderate job tilt ~{job}% — this employment line is still viable.")
    elif job >= 52:
        score += 10
        reasons.append(f"Job mode ~{job}% supports structured employment over pure business.")

    if profile.min_comm_score is not None and comm >= profile.min_comm_score:
        score += 14
        reasons.append(f"Commercial/professional score {comm}/100 — field aptitude visible.")
    elif profile.min_comm_score is not None and comm >= profile.min_comm_score - 8:
        score += 6

    if struct >= 48:
        score += 8
        reasons.append(f"Structure score {struct}/100 — org/process comfort for this profession.")

    if profile.subtype_keywords and any(k in tag_blob for k in profile.subtype_keywords):
        score += 12
        hit = [t for t in tags if any(k in t.lower() for k in profile.subtype_keywords)][:2]
        reasons.append(f"Career subtype signal: {', '.join(hit) if hit else ', '.join(tags[:2])}.")

    for planet, role in profile.planet_roles:
        p = r.planet(planet) or {}
        if p.get("house") in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11):
            score += 6
            reasons.append(f"{planet} ({role}): house {p.get('house')} sign {p.get('sign')}.")

    for trait in profile.traits[:2]:
        tscore = int(psych.get(trait) or 50)
        if tscore >= 55:
            score += 5
        reasons.append(
            trait_line(
                inc,
                trait,
                high=f"supports {profile.label.lower()}",
                low=f"build this trait for {profile.label.lower()}",
            )
        )

    if profile.evidence_hint:
        reasons.append(profile.evidence_hint)

    suitable = score >= profile.min_score
    return suitable, score, reasons


def run_job_sector(
    kundli: dict,
    question: str,
    *,
    archetype: str,
    wants_explain: bool = False,
) -> EngineResult:
    profile = get_job_profile(archetype)
    if profile is None:
        raise ValueError(f"Unknown job archetype: {archetype}")

    inc = load_inclination(kundli)
    r = reader(kundli)

    evidence = [
        house_axis(r, 10, "Career execution (10th house)"),
        house_axis(r, 6, "Work/service style (6th house)"),
    ]
    evidence.extend(inclination_evidence(inc, limit=3, include_job_split=False))

    suitable, job_score, reasons = _score_profile(profile, inc, r)
    evidence.extend(reasons[:5])

    if suitable:
        verdict = f"{profile.label}: strong suitability pattern — employment path visible in chart"
    else:
        verdict = (
            f"{profile.label}: possible with skill-building and focus — "
            "not the dominant career theme yet"
        )

    return EngineResult(
        archetype=profile.archetype,
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 75,
        answer_plan=f"Direct haan/nahi for {profile.label.lower()} → chart evidence → one skill note.",
        summary=[
            f"QUESTION FOCUS: {profile.label} suitability.",
            "Answer haan/nahi for THIS job/profession ONLY — do NOT pivot to job vs business % split.",
            "No exact employer/post guarantee.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "marriage", "exact job title guarantee", "spouse profession"],
        checks={
            "slice_type": "career_engine_v1",
            "archetype": profile.archetype,
            "job_profile": profile.archetype,
            "job_score": job_score,
            "suitable": suitable,
            "sector": profile.archetype.replace("_job", ""),
        },
    )
