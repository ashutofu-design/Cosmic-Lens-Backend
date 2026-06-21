from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import career_snapshot, house_axis, inclination_evidence, load_inclination, reader, subtype_hits

_SECTOR_MAP: list[tuple[str, re.Pattern[str], str, str]] = [
    ("government", re.compile(r"(?ix)\b(government|govt|sarkari|public\s*sector|ups\s*ssc)\b"), "job", "Government/service"),
    ("private", re.compile(r"(?ix)\b(private\s*sector|corporate|company\s*job|mnc)\b"), "job", "Private corporate"),
    ("it", re.compile(r"(?ix)\b(it\b|software|tech|developer|coding|digital)\b"), "comm", "IT/digital"),
    ("medical", re.compile(r"(?ix)\b(medical|doctor|healthcare|nurse|hospital)\b"), "comm", "Medical/healing"),
    ("law", re.compile(r"(?ix)\b(law|legal|advocate|lawyer|court)\b"), "comm", "Law/advisory"),
    ("finance", re.compile(r"(?ix)\b(finance\s*sector|banking|bank\s*job|accountant|ca\b)\b"), "comm", "Finance/commerce"),
    ("teaching", re.compile(r"(?ix)\b(teaching|teacher|professor|education\s*field|tutor)\b"), "comm", "Teaching/education"),
    ("creative", re.compile(r"(?ix)\b(creative|design|art|artist|media\s*design)\b"), "comm", "Creative/design"),
    ("technical", re.compile(r"(?ix)\b(technical|engineering|engineer|mechanical|tech\s*field)\b"), "comm", "Technical/engineering"),
    ("management", re.compile(r"(?ix)\b(management|manager|leadership\s*role|admin)\b"), "job", "Management/administration"),
    ("sales", re.compile(r"(?ix)\b(sales|marketing|business\s*development)\b"), "comm", "Sales/marketing"),
    ("research", re.compile(r"(?ix)\b(research|analyst|scientist|r\s*&\s*d)\b"), "comm", "Research/analysis"),
    ("real_estate", re.compile(r"(?ix)\b(real\s*estate|property\s*business|builder)\b"), "biz", "Real estate/commerce"),
    ("consulting", re.compile(r"(?ix)\b(consulting|consultant|advisory)\b"), "comm", "Consulting/advisory"),
    ("media", re.compile(r"(?ix)\b(media|journalism|content\s*creation|influencer)\b"), "comm", "Media/content"),
    ("ngo", re.compile(r"(?ix)\b(ngo|social\s*work|non[\s-]?profit)\b"), "job", "Social/NGO service"),
    ("politics", re.compile(r"(?ix)\b(politics|political|neta|election)\b"), "job", "Politics/public influence"),
    ("industry", re.compile(r"(?ix)\b(industry|field|line|profession|kaunsi)\b"), "comm", "Best industry"),
]


def _detect_sector(q: str) -> tuple[str, str, str]:
    for key, rx, kind, label in _SECTOR_MAP:
        if rx.search(q or ""):
            return key, kind, label
    return "general", "comm", "Career field"


def run_sector_fit(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    key, kind, label = _detect_sector(question or "")

    evidence = [
        house_axis(r, 10, "Profession execution (10th house)"),
        house_axis(r, 6, "Work style/service (6th house)"),
    ]
    evidence.extend(inclination_evidence(inc, limit=4))

    tags = subtype_hits(inc, kind)
    if tags:
        evidence.append(f"Sector fit ({label}): chart subtypes — {', '.join(tags)}.")
    else:
        evidence.append(f"Sector fit ({label}): read from 10th lord + karakas + inclination mode {inc.get('career_mode')}.")

    comm = int(inc.get("commercial_score") or 0)
    job = int(inc.get("job_pct") or 50)
    biz = int(inc.get("business_pct") or 50)

    if key == "government":
        evidence.append(
            "Government fit: Sun-Saturn structure + service/job subtype supports sarkari/public sector tone."
        )
        fit = job >= 52
    elif key == "it":
        evidence.append("IT/digital fit: Mercury-Rahu/commercial subtype supports tech-digital fields.")
        fit = comm >= 40 or "digital" in " ".join(tags).lower()
    elif key in ("medical", "law", "teaching"):
        evidence.append(f"{label} fit: Jupiter-Mercury advisory/commercial subtype supports professional service fields.")
        fit = comm >= 35
    elif key in ("sales", "media", "creative"):
        evidence.append(f"{label} fit: Venus-Mercury commercial subtype supports people-facing creative/commerce fields.")
        fit = comm >= 30
    elif key in ("real_estate", "politics"):
        evidence.append(f"{label} fit: Mars-Saturn/Rahu execution supports high-stakes independent fields.")
        fit = biz >= 45
    elif key == "industry":
        all_tags = subtype_hits(inc, "job") + subtype_hits(inc, "biz") + subtype_hits(inc, "comm")
        evidence.append(
            f"Best industries: {', '.join(all_tags[:3]) if all_tags else inc.get('career_mode', 'mixed fields')}."
        )
        fit = True
    else:
        fit = True

    verdict = f"{label}: {'suitable pattern visible' if fit else 'possible with skill-building — not dominant chart theme'}"

    return EngineResult(
        archetype="sector_fit",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 70,
        answer_plan="Direct sector suitability → 2 chart reasons → one skill note.",
        summary=[f"QUESTION FOCUS: {key} sector/industry fit.", "No exact job title guarantee."],
        evidence=evidence[:8],
        ignore=["timing", "marriage", "spouse profession"],
        checks={"slice_type": "career_engine_v1", "archetype": "sector_fit", "sector": key},
    )
