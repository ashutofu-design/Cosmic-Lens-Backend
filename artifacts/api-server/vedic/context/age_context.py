"""
Sprint 28 / Phase A2 — Age-context layer
Computes current_age from DOB + life-stage band + dasha-age window.
Lets AI prompts reason age-appropriately (no marriage advice for 12-yr-olds,
no career-start advice for 60-yr-olds, etc).
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Any

LIFE_STAGES = [
    (0, 7, "early childhood", "Balya — formative years; parental yogas dominate"),
    (8, 12, "late childhood", "education foundations; 4th house & Mercury key"),
    (13, 17, "adolescence", "identity formation; Mars/Venus awakening"),
    (18, 24, "young adult", "education completion + early career; 10th lord & 4th lord"),
    (25, 32, "early career & marriage window", "7th house, Venus/Jupiter karaka, Saturn maturity"),
    (33, 41, "career establishment & family", "10th house, 5th (children), 2nd (wealth) primary"),
    (42, 50, "mid-life consolidation", "Saturn return effects; 6th/8th/12th karmic review"),
    (51, 60, "wisdom & legacy", "9th house dharma, Jupiter/spiritual karakas active"),
    (61, 75, "elder phase", "12th house moksha, health (6th), retirement"),
    (76, 120, "sage phase", "spiritual culmination, Ketu themes"),
]


def _parse_dob(birth: dict, kundli: dict) -> date | None:
    src = (birth.get("dob") or birth.get("date") or birth.get("dateOfBirth")
           or birth.get("birthDate") or kundli.get("dob"))
    if isinstance(src, str) and len(src) >= 10:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(src[:10], fmt).date()
            except Exception:
                continue
        # Try "DD MMM YYYY" / "MMM DD YYYY"
        for fmt in ("%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y"):
            try:
                return datetime.strptime(src.strip(), fmt).date()
            except Exception:
                continue
    if isinstance(birth, dict) and all(k in birth for k in ("day", "month", "year")):
        try:
            return date(int(birth["year"]), int(birth["month"]), int(birth["day"]))
        except Exception:
            return None
    return None


def _life_stage(age: int) -> tuple[str, str]:
    for lo, hi, name, desc in LIFE_STAGES:
        if lo <= age <= hi:
            return name, desc
    return "unknown", "—"


def compute_age_context(birth: dict, kundli: dict,
                        current_dasha: dict | None = None) -> dict[str, Any]:
    dob = _parse_dob(birth or {}, kundli or {})
    if dob is None:
        return {"available": False, "reason": "DOB not parseable"}
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    stage, stage_desc = _life_stage(age)

    # Dasha-age window: years remaining in current MD
    dasha_remaining_years = None
    dasha_age_at_start = None
    if isinstance(current_dasha, dict):
        ed = current_dasha.get("endDate") or current_dasha.get("end") or current_dasha.get("end_date")
        sd = current_dasha.get("startDate") or current_dasha.get("start") or current_dasha.get("start_date")
        if isinstance(ed, str) and len(ed) >= 10:
            try:
                end = datetime.strptime(ed[:10], "%Y-%m-%d").date()
                dasha_remaining_years = round((end - today).days / 365.25, 1)
            except Exception:
                pass
        if isinstance(sd, str) and len(sd) >= 10:
            try:
                start = datetime.strptime(sd[:10], "%Y-%m-%d").date()
                age_at_start = start.year - dob.year - ((start.month, start.day) < (dob.month, dob.day))
                dasha_age_at_start = age_at_start
            except Exception:
                pass

    # Age-appropriate topic gates
    gates = {
        "marriage_question_appropriate": age >= 18,
        "career_question_appropriate": age >= 16,
        "education_primary_focus": age <= 24,
        "child_question_appropriate": age >= 21,
        "retirement_planning_active": age >= 50,
        "health_priority_high": age >= 45,
        "spiritual_phase_active": age >= 50,
    }

    return {
        "available": True,
        "dob": dob.isoformat(),
        "current_age": age,
        "as_of_date": today.isoformat(),
        "life_stage": stage,
        "life_stage_description": stage_desc,
        "current_dasha_age_at_start": dasha_age_at_start,
        "current_dasha_years_remaining": dasha_remaining_years,
        "age_gates": gates,
        "interpretation": (
            f"User is {age} years old ({stage}). "
            f"AI must tailor predictions to this life stage — avoid age-inappropriate advice."
        ),
    }


def format_age_context_summary(r: dict) -> str:
    if not isinstance(r, dict) or not r.get("available"):
        return ""
    lines = ["── AGE CONTEXT (Sprint 28 / Phase A2) ──"]
    lines.append(f"Current age: {r['current_age']} years (DOB {r['dob']}, as of {r['as_of_date']})")
    lines.append(f"Life stage: {r['life_stage']} — {r['life_stage_description']}")
    if r.get("current_dasha_years_remaining") is not None:
        lines.append(f"Current MD: started at age {r.get('current_dasha_age_at_start','?')}, "
                     f"{r['current_dasha_years_remaining']} years remaining")
    g = r["age_gates"]
    inappropriate = [k for k, v in g.items() if not v]
    if inappropriate:
        lines.append(f"AI MUST NOT give: {', '.join(inappropriate)}")
    lines.append(r["interpretation"])
    return "\n".join(lines)
