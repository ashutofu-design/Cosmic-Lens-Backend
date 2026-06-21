from __future__ import annotations

from ask_career.sector_registry import SECTOR_REGISTRY, detect_sector
from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader, subtype_hits


def _sector_fit(entry_key: str, inc: dict, r, label: str, kind: str) -> tuple[bool, list[str]]:
    extra: list[str] = []
    comm = int(inc.get("commercial_score") or 0)
    job = int(inc.get("job_pct") or 50)
    biz = int(inc.get("business_pct") or 50)
    tags = subtype_hits(inc, kind) + subtype_hits(inc, "comm") + subtype_hits(inc, "biz")
    tag_blob = " ".join(tags).lower()

    if entry_key == "government":
        extra.append("Government fit: Sun-Saturn structure + service/job subtype supports sarkari/public roles.")
        fit = job >= 52
    elif entry_key == "it":
        extra.append("IT/digital fit: Mercury-Rahu/commercial subtype supports tech-digital fields.")
        fit = comm >= 38 or "digital" in tag_blob
    elif entry_key in ("medical", "law", "teaching", "pharmacy"):
        extra.append(f"{label} fit: Jupiter-Mercury advisory/service subtype supports this professional line.")
        fit = comm >= 32
    elif entry_key in ("sales", "media", "creative", "film", "music", "fashion"):
        extra.append(f"{label} fit: Venus-Mercury public/commercial subtype supports people-facing fields.")
        fit = comm >= 28
    elif entry_key == "food":
        moon = r.planet("Moon") or {}
        ven = r.planet("Venus") or {}
        extra.append("Food/hospitality fit: Venus-Moon + service/commercial subtype supports food/cafe/catering.")
        if ven.get("house") in (2, 4, 7, 10, 11) or moon.get("house") in (2, 4, 6, 7, 10):
            extra.append(
                f"Hospitality signal: Venus house {ven.get('house')}, Moon house {moon.get('house')}."
            )
        fit = comm >= 26 or biz >= 32 or ven.get("house") in (2, 4, 7, 10, 11)
    elif entry_key in ("real_estate", "politics", "transport", "jewellery", "garment", "agriculture", "ecommerce", "franchise"):
        extra.append(f"{label} fit: Mars-Saturn/Rahu execution supports independent commerce lines.")
        fit = biz >= 38 or comm >= 30
    elif entry_key in ("defence", "aviation"):
        extra.append(f"{label} fit: Mars discipline + structured service subtype supports this line.")
        fit = job >= 48 or int(inc.get("psychology", {}).get("discipline", 50)) >= 50
    elif entry_key in ("sports", "fitness"):
        extra.append(f"{label} fit: Mars vitality + competitive drive supports active career lines.")
        fit = int(inc.get("psychology", {}).get("risk_appetite", 50)) >= 42 or comm >= 25
    elif entry_key == "coaching":
        extra.append(f"{label} fit: Jupiter advisory + commercial delivery supports teaching/coaching business.")
        fit = comm >= 30
    elif entry_key == "ca":
        extra.append(f"{label} fit: Mercury-Saturn analytical subtype supports accountancy/audit.")
        fit = comm >= 35
    elif entry_key == "banking":
        extra.append(f"{label} fit: Jupiter-Mercury finance subtype supports banking lines.")
        fit = comm >= 32
    elif entry_key == "architect":
        extra.append(f"{label} fit: Venus structure + Mercury planning supports design/architecture.")
        fit = comm >= 30
    elif entry_key == "industry":
        all_tags = subtype_hits(inc, "job") + subtype_hits(inc, "biz") + subtype_hits(inc, "comm")
        extra.append(f"Best industries: {', '.join(all_tags[:3]) if all_tags else inc.get('career_mode', 'mixed fields')}.")
        fit = True
    else:
        if tags:
            extra.append(f"Sector fit ({label}): chart subtypes — {', '.join(tags[:3])}.")
        else:
            extra.append(f"Sector fit ({label}): read from 10th lord + karakas + inclination mode {inc.get('career_mode')}.")
        fit = comm >= 28 if kind == "comm" else biz >= 35 if kind == "biz" else job >= 50

    return fit, extra


def run_sector_fit(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    entry = detect_sector(question or "")
    if entry is None:
        entry = next(e for e in SECTOR_REGISTRY if e.key == "industry")

    evidence = [
        house_axis(r, 10, "Profession execution (10th house)"),
        house_axis(r, 6, "Work style/service (6th house)"),
    ]
    evidence.extend(
        inclination_evidence(inc, limit=4, include_job_split=entry.key in ("general", "industry"))
    )
    fit, extra = _sector_fit(entry.key, inc, r, entry.label, entry.kind)
    evidence.extend(extra)

    verdict = f"{entry.label}: {'suitable pattern visible' if fit else 'possible with skill-building — not dominant chart theme'}"

    return EngineResult(
        archetype="sector_fit",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 70,
        answer_plan="Direct sector suitability → 2 chart reasons → one skill note.",
        summary=[
            f"QUESTION FOCUS: {entry.label} suitability — answer haan/nahi for THIS sector only.",
            "Stay on the named sector — do NOT pivot to job vs business % split.",
            "No exact job title guarantee.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "marriage", "spouse profession"],
        checks={"slice_type": "career_engine_v1", "archetype": "sector_fit", "sector": entry.key},
    )
