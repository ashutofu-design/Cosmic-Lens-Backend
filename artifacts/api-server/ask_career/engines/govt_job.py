"""Government / sarkari job suitability — dedicated engine (not generic sector_fit)."""
from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import (
    house_axis,
    inclination_evidence,
    load_inclination,
    reader,
    subtype_hits,
    trait_line,
)

_FOCUS_RX: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?ix)\b(ias|ips|upsc|civil\s*service)\b"), "civil_service"),
    (re.compile(r"(?ix)\b(police|ips\b)\b"), "police"),
    (re.compile(r"(?ix)\b(railway|railways)\b"), "railway"),
    (re.compile(r"(?ix)\b(bank\s*po|bank\s*job|banking\s*job)\b"), "banking"),
    (re.compile(r"(?ix)\b(ssc\s*job|ssc\s*cgl|staff\s*selection)\b"), "ssc"),
    (re.compile(r"(?ix)\b(defence|defense|army|navy|air\s*force|nda\b|cds\b)\b"), "defence"),
    (re.compile(r"(?ix)\b(teacher|teaching\s*job|lecturer|professor)\b"), "teaching"),
    (re.compile(r"(?ix)\b(psc|state\s*service)\b"), "state_service"),
]

_FOCUS_HINTS = {
    "civil_service": "IAS/IPS/UPSC civil service line: Sun authority + Saturn discipline + Jupiter learning axis.",
    "police": "Police/law-enforcement line: Mars discipline + Sun authority + structured service subtype.",
    "railway": "Railway service: Saturn routine + 6H service axis supports stable public-sector employment.",
    "banking": "Bank/govt finance job: Jupiter-Mercury finance subtype + job tilt supports banking PO/clerk lines.",
    "ssc": "SSC/staff-selection jobs: discipline + Mercury analytical prep supports clerical/govt staff roles.",
    "defence": "Defence service: Mars-Saturn discipline + structured hierarchy supports army/navy/air force path.",
    "teaching": "Govt teaching: Jupiter advisory + service subtype supports lecturer/teacher in public sector.",
    "state_service": "State PSC/service: Sun-Saturn public duty + job mode supports state-level sarkari roles.",
    "general": "General sarkari naukri: Sun-Saturn service + job subtype supports government/public employment.",
}


def _detect_focus(q: str) -> str:
    for rx, name in _FOCUS_RX:
        if rx.search(q or ""):
            return name
    return "general"


def _govt_fit(inc: dict, r, focus: str) -> tuple[bool, int, list[str]]:
    job = int(inc.get("job_pct") or 50)
    struct = int(inc.get("structure_score") or 0)
    psych = inc.get("psychology") or {}
    discipline = int(psych.get("discipline") or 50)
    authority = int(psych.get("authority_tolerance") or 50)
    job_tags = subtype_hits(inc, "job")
    tag_blob = " ".join(job_tags).lower()

    sun = r.planet("Sun") or {}
    sat = r.planet("Saturn") or {}
    jup = r.planet("Jupiter") or {}
    mars = r.planet("Mars") or {}

    score = 0
    reasons: list[str] = []

    if job >= 52:
        score += 18
        reasons.append(f"Employment tilt ~{job}% — sarkari naukri aligns with job/service mode over business.")
    elif job >= 45:
        score += 8
        reasons.append(f"Moderate job tilt ~{job}% — govt path viable alongside structured employment.")

    if discipline >= 55:
        score += 14
        reasons.append(f"Discipline score {discipline}/100 — sustained prep and hierarchy suit public service.")
    elif discipline <= 40:
        reasons.append(f"Discipline score {discipline}/100 — build routine/habits for competitive govt selection.")

    if struct >= 50:
        score += 10
        reasons.append(f"Structure score {struct}/100 — comfort with rules, seniority and org hierarchy.")
    if authority >= 52:
        score += 8
        reasons.append(f"Authority tolerance {authority}/100 — can work within govt chain-of-command.")

    if sun.get("house") in (6, 10, 11):
        score += 12
        reasons.append(
            f"Sun service signal: house {sun.get('house')} — authority through duty/public role."
        )
    if sat.get("house") in (6, 10, 11):
        score += 10
        reasons.append(
            f"Saturn service signal: house {sat.get('house')} — patience, rules and long-tenure sarkari path."
        )
    if jup.get("house") in (1, 5, 9, 10, 11):
        score += 6
        reasons.append(
            f"Jupiter learning/growth: house {jup.get('house')} — exam prep and advisory growth supported."
        )

    if any(k in tag_blob for k in ("service", "government", "public", "admin")):
        score += 12
        reasons.append(f"Job subtype signal: {', '.join(job_tags[:3])}.")

    if focus == "defence" and mars.get("house") in (1, 3, 6, 10, 11):
        score += 8
        reasons.append(f"Mars drive in house {mars.get('house')} — physical/discipline edge for defence line.")
    elif focus == "banking" and jup.get("sign"):
        score += 6
        reasons.append("Jupiter finance karak supports banking/accounts in public sector.")
    elif focus == "civil_service" and discipline >= 48 and jup.get("house"):
        score += 8
        reasons.append("Civil service mix: discipline + Jupiter learning axis for UPSC/IAS-type prep.")

    if _FOCUS_HINTS.get(focus):
        reasons.append(_FOCUS_HINTS[focus])

    suitable = score >= 52
    return suitable, score, reasons


def run_govt_job(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    focus = _detect_focus(question or "")

    evidence = [
        house_axis(r, 10, "Career authority/service (10th house)"),
        house_axis(r, 6, "Daily duty/service (6th house)"),
    ]
    evidence.extend(inclination_evidence(inc, limit=3, include_job_split=False))
    evidence.append(
        trait_line(
            inc,
            "discipline",
            high="strong for sarkari prep and long service tenure",
            low="needs external structure — build exam/service routine",
        )
    )
    evidence.append(
        trait_line(
            inc,
            "authority_tolerance",
            high="comfortable accepting hierarchy — govt chain suits",
            low="may chafe under strict hierarchy — choose flexible public roles",
        )
    )

    suitable, govt_score, reasons = _govt_fit(inc, r, focus)
    evidence.extend(reasons[:4])

    label = focus.replace("_", " ")
    if suitable:
        verdict = f"Government/sarkari job ({label}): strong suitability pattern — service path visible in chart"
    else:
        verdict = (
            f"Government/sarkari job ({label}): possible with exam prep and discipline — "
            "not the dominant career theme"
        )

    return EngineResult(
        archetype="govt_job",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 75,
        answer_plan="Direct haan/nahi for sarkari/govt job → Sun-Saturn service evidence → one prep note.",
        summary=[
            f"QUESTION FOCUS: government/sarkari job suitability ({label}).",
            "Answer haan/nahi for govt job ONLY — do NOT pivot to job vs business % split.",
            "Do NOT promise selection date or guaranteed rank.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "marriage", "exact rank/post guarantee", "spouse profession"],
        checks={
            "slice_type": "career_engine_v1",
            "archetype": "govt_job",
            "focus": focus,
            "govt_score": govt_score,
            "suitable": suitable,
            "job_pct": inc.get("job_pct"),
        },
    )
