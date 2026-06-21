from __future__ import annotations

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination, trait_line


def run_job_vs_business(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    job = int(inc.get("job_pct") or 50)
    biz = int(inc.get("business_pct") or 50)
    if job >= biz + 15:
        verdict = f"Employment path stronger — job ~{job}% vs business ~{biz}%"
    elif biz >= job + 15:
        verdict = f"Business/self-employment path stronger — business ~{biz}% vs job ~{job}%"
    else:
        verdict = f"Hybrid career — job ~{job}% and business ~{biz}% both viable"

    evidence = inclination_evidence(inc, limit=8)
    evidence.append(
        trait_line(
            inc, "independence",
            high="strong independent streak — self-directed work suits",
            low="structured team/employer setup suits better",
        )
    )
    evidence.append(
        trait_line(
            inc, "discipline",
            high="discipline supports long-term career stability",
            low="need external structure for consistency",
        )
    )

    return EngineResult(
        archetype="job_vs_business",
        verdict=verdict,
        confidence=str(inc.get("confidence") or "medium").lower(),
        word_budget=100 if wants_explain else 70,
        answer_plan="Direct job vs business answer → 2 inclination reasons → one practical note.",
        summary=[
            "Answer job OR business directly with approximate split from engine.",
            "If verdict says Employment path stronger → say JOB is better (~split), NOT 'pehle job phir business'.",
            "Only say hybrid / both viable when verdict says Hybrid career.",
            "Use ONLY inclination evidence — not marriage or finance-only axes.",
        ],
        evidence=evidence[:8],
        ignore=[
            "timing dates/windows",
            "exact salary",
            "marriage partner career",
            "pehle job phir business unless hybrid verdict",
        ],
        checks={
            "slice_type": "career_engine_v1",
            "archetype": "job_vs_business",
            "job_pct": job,
            "business_pct": biz,
            "career_mode": inc.get("career_mode"),
        },
    )
