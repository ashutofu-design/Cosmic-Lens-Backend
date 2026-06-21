from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination, trait_line

_ENV_RX = [
    (re.compile(r"(?ix)\b(remote\s*work|work\s*from\s*home|wfh)\b"), "remote"),
    (re.compile(r"(?ix)\b(multinational|mnc|global\s*company)\b"), "mnc"),
    (re.compile(r"(?ix)\b(corporate\s*world|corporate\s*job|big\s*company)\b"), "corporate"),
    (re.compile(r"(?ix)\b(public\s*sector|government|sarkari)\b"), "public"),
    (re.compile(r"(?ix)\b(private\s*sector)\b"), "private"),
    (re.compile(r"(?ix)\b(frequent\s*travel|travel\s*wala\s*career)\b"), "travel"),
    (re.compile(r"(?ix)\b(self[\s-]?employment)\b"), "self_employed"),
    (re.compile(r"(?ix)\b(employee\s*type)\b"), "employee"),
]


def _env(q: str) -> str:
    for rx, name in _ENV_RX:
        if rx.search(q or ""):
            return name
    return "corporate"


def run_work_environment(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    env = _env(question or "")
    job = int(inc.get("job_pct") or 50)
    struct = int(inc.get("structure_score") or 0)

    evidence = inclination_evidence(inc, limit=4)
    evidence.append(f"Structure score {struct}/100 — comfort in org/system vs free-form work.")

    msgs = {
        "remote": "Remote work: Mercury/digital + independence score — virtual/client-remote roles can suit.",
        "mnc": "MNC/corporate: structured professional mode + job tilt supports large-organisation careers.",
        "corporate": f"Corporate fit: job ~{job}% + structure {struct}/100 — hierarchy and process-oriented workplaces suit.",
        "public": "Public sector: Sun-Saturn service subtype + job tilt supports government/public roles.",
        "private": "Private sector: commercial/professional subtype supports company employment with growth track.",
        "travel": "Travel-heavy career: Rahu movement + Mercury field roles (sales/consulting/operations) support frequent travel.",
    }
    if env == "self_employed":
        evidence.append(trait_line(inc, "independence", high="self-employment suits", low="employed structure better first"))
    elif env == "employee":
        evidence.append(trait_line(inc, "discipline", high="employee track suits — steady role in organisation", low="may chafe in fixed roles — seek flexible org"))
    elif env in msgs:
        evidence.append(msgs[env])

    verdict = f"Work environment ({env}): pattern from job/business split + structure/independence scores"

    return EngineResult(
        archetype="work_environment",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="Direct environment fit → 2 scores → practical note.",
        summary=[f"QUESTION FOCUS: {env} work setting."],
        evidence=evidence[:8],
        ignore=["timing", "marriage"],
        checks={"slice_type": "career_engine_v1", "archetype": "work_environment", "environment": env},
    )
