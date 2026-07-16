"""Practical Manifestation Filter (PMF) — one timing gate for real-world readiness.

Runs INSIDE timing (after dasha candidates exist conceptually; before narrator):
  1. Age
  2. Life stage
  3. Financial readiness (chart wealth signals)
  4. Career stability (age + 10H/karaka signals)
  5. Event dependency (job → vehicle → property chain)
  6. Legal eligibility
  7. Practical reality (aggregate)

Does NOT invent calendar dates — only floors, flags, and locked notes for narrator.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

PMF_VERSION = "pmf_v1"

# Practical floors — synced with product rules / property_practicality.
DOMAIN_MIN_ELIGIBLE_AGE: dict[str, int] = {
    "marriage": 22,
    "love": 18,
    "property": 24,
    "career": 18,
    "education": 14,
    "foreign_education": 16,
    "travel": 18,
    "vehicle": 18,
    "finance": 18,
    "health": 12,
    "children": 20,
    "litigation": 18,
    "spiritual": 16,
    "fame": 16,
    "network": 14,
    "universal": 16,
    "general": 16,
}

_PROPERTY_RENT_RX = re.compile(
    r"(?ix)\b(rent|kiraya|kiraaya|lease|pg\b|paying\s*guest)\b"
)
_VEHICLE_BIKE_RX = re.compile(
    r"(?ix)\b(bike|scooter|two[\s-]?wheeler|motorcycle|activa)\b"
)


def resolve_timing_age(
    question: str = "",
    birth: Any = None,
    kundli: Any = None,
) -> Optional[int]:
    try:
        from ask_career.timing_registry import resolve_user_age

        return resolve_user_age(question, birth, kundli)
    except Exception:
        return None


def min_eligible_age(domain: str, question: str = "") -> int:
    d = (domain or "universal").strip().lower()
    q = question or ""
    if d == "property" and _PROPERTY_RENT_RX.search(q):
        return 18
    if d == "vehicle" and _VEHICLE_BIKE_RX.search(q):
        return 19
    if d == "vehicle":
        return 25
    return int(DOMAIN_MIN_ELIGIBLE_AGE.get(d, 16))


# Legal floors (India-oriented; soft product rules).
_LEGAL_MIN: dict[str, int] = {
    "marriage": 18,  # absolute legal floor; practical age is higher
    "love": 18,
    "vehicle": 18,  # license
    "property": 18,  # contract capacity
    "litigation": 18,
    "children": 18,
    "career": 14,
    "finance": 18,
}

# Typical life-stack order for dependency checks.
_EVENT_STACK = (
    "education",
    "career",
    "vehicle",
    "property",
    "children",
    "marriage",
)

_JOB_HINT_RX = re.compile(
    r"(?ix)\b(job|naukri|salary|career|employed|business|income|kamai)\b"
)


def _planet_scores_from_kundli(kundli: dict | None) -> dict[str, float]:
    scores: dict[str, float] = {}
    if not isinstance(kundli, dict):
        return scores
    for p in kundli.get("planets") or []:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name") or p.get("planet") or "").strip().title()
        if not name:
            continue
        # Dignity / house weight — light heuristic only.
        house = p.get("house")
        try:
            h = int(house) if house is not None else 0
        except (TypeError, ValueError):
            h = 0
        base = 8.0
        if h in (1, 2, 9, 10, 11):
            base += 4.0
        if h in (6, 8, 12):
            base -= 2.0
        scores[name] = max(scores.get(name, 0.0), base)
    return scores


def _financial_readiness(
    domain: str,
    *,
    age: Optional[int],
    kundli: dict | None,
    top_planets: Any = None,
) -> dict[str, Any]:
    d = (domain or "").lower()
    # Domains where money capacity matters for manifestation.
    money_domains = {"property", "vehicle", "finance", "travel", "education", "foreign_education"}
    if d not in money_domains:
        return {
            "status": "NA",
            "band": "NA",
            "ok": True,
            "detail": "Financial readiness not primary for this domain",
        }

    band = "MODERATE"
    try:
        from event_timing.vehicle.vehicle_practicality import affordability_band

        rows = top_planets
        if not rows:
            scores = _planet_scores_from_kundli(kundli)
            rows = [{"name": k, "score": v} for k, v in scores.items()]
        band = affordability_band(rows if isinstance(rows, list) else [])
    except Exception:
        band = "MODERATE"

    ok = band != "WEAK"
    # Very young + weak finance → hard defer signal.
    if age is not None and age < 23 and band == "WEAK" and d in ("property", "vehicle"):
        ok = False
    return {
        "status": "PASS" if ok else "DEFER",
        "band": band,
        "ok": ok,
        "detail": f"Chart wealth/afford signal={band}",
    }


def _career_stability(domain: str, *, age: Optional[int], kundli: dict | None) -> dict[str, Any]:
    d = (domain or "").lower()
    needs_career = d in ("property", "vehicle", "finance", "children", "marriage")
    if not needs_career:
        return {
            "status": "NA",
            "ok": True,
            "detail": "Career stability not required for this event",
        }

    scores = _planet_scores_from_kundli(kundli)
    tenth = 0.0
    # Proxy: Saturn/Sun/Mercury strength as career stability signal.
    for nm in ("Saturn", "Sun", "Mercury", "Jupiter"):
        tenth += float(scores.get(nm, 0.0))
    strong = tenth >= 24.0

    if age is not None and age < 22:
        return {
            "status": "EARLY",
            "ok": False,
            "detail": f"Age {age} — career phase usually still forming (score~{tenth:.0f})",
            "career_signal": "FORMING",
        }
    if age is not None and age < 25 and not strong:
        return {
            "status": "EMERGING",
            "ok": False,
            "detail": "Career stability emerging — big purchase/commitment soft-defer",
            "career_signal": "EMERGING",
        }
    return {
        "status": "PASS" if strong or (age is not None and age >= 25) else "SOFT",
        "ok": True,
        "detail": f"Career stability signal={'STRONG' if strong else 'ADEQUATE'}",
        "career_signal": "STABLE" if strong or (age is not None and age >= 27) else "ADEQUATE",
    }


def _event_dependency(domain: str, *, age: Optional[int], question: str) -> dict[str, Any]:
    """job → car → property style prerequisites."""
    d = (domain or "").lower()
    missing: list[str] = []
    q = question or ""

    if d == "property":
        if age is not None and age < 24:
            missing.append("stable_income_phase")
        if age is not None and age < 22:
            missing.append("career_foundation")
        missing.append("down_payment_capacity")  # always soft flag for buy
    elif d == "vehicle" and not re.search(r"(?ix)\b(bike|scooter)\b", q):
        if age is not None and age < 23:
            missing.append("stable_job_or_income")
    elif d == "children":
        if age is not None and age < 22:
            missing.append("adult_life_stability")
    elif d == "marriage":
        if age is not None and age < 21:
            missing.append("legal_and_maturity_floor")

    # If user explicitly says unemployed / student for heavy purchases.
    if d in ("property", "vehicle") and re.search(
        r"(?ix)\b(student|padhai|unemployed|berozgar|college)\b", q
    ):
        missing.append("post_study_income")

    ok = not any(
        m in missing
        for m in ("career_foundation", "post_study_income", "legal_and_maturity_floor")
    )
    return {
        "status": "PASS" if not missing else ("BLOCK" if not ok else "SOFT"),
        "ok": ok,
        "missing_prereqs": missing[:6],
        "stack_hint": "education → career/income → vehicle → property",
        "detail": (
            "Prerequisites clear"
            if not missing
            else "Pending: " + ", ".join(missing[:4])
        ),
    }


def _legal_eligibility(domain: str, *, age: Optional[int], question: str) -> dict[str, Any]:
    d = (domain or "").lower()
    legal = int(_LEGAL_MIN.get(d, 16))
    # Marriage gender-neutral product floor stays in practical age; legal is 18+.
    if age is None:
        return {
            "status": "UNKNOWN",
            "ok": True,
            "legal_min_age": legal,
            "detail": "Age unknown — assume legal check with user",
        }
    ok = age >= legal
    return {
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "legal_min_age": legal,
        "detail": (
            f"Age {age} meets legal floor {legal}+"
            if ok
            else f"Age {age} below legal floor {legal}+ for {d}"
        ),
    }


def _life_stage(age: Optional[int], min_practical: int) -> dict[str, Any]:
    if age is None:
        return {"status": "UNKNOWN", "label": "unknown", "ok": True}
    if age < min_practical:
        return {"status": "EARLY", "label": "early", "ok": False}
    if age < min_practical + 3:
        return {"status": "EMERGING", "label": "emerging", "ok": True}
    return {"status": "READY", "label": "ready", "ok": True}


def run_practical_manifestation_filter(
    domain: str,
    *,
    question: str = "",
    birth: Any = None,
    kundli: Any = None,
    user_age: Optional[int] = None,
    top_planets: Any = None,
) -> dict[str, Any]:
    """Single PMF pass — all practical checks for timing manifestation."""
    d = (domain or "universal").strip().lower()
    age = user_age if user_age is not None else resolve_timing_age(question, birth, kundli)
    min_prac = min_eligible_age(d, question)
    now_y = datetime.utcnow().year

    age_ok = age is None or age >= min_prac
    age_check = {
        "status": "UNKNOWN" if age is None else ("PASS" if age_ok else "FAIL"),
        "ok": age_ok,
        "user_age": age,
        "min_practical_age": min_prac,
        "detail": (
            f"Age unknown; practical floor {min_prac}+"
            if age is None
            else (
                f"Age {age} ≥ practical floor {min_prac}"
                if age_ok
                else f"Age {age} < practical floor {min_prac}"
            )
        ),
    }
    life = _life_stage(age, min_prac)
    finance = _financial_readiness(
        d, age=age, kundli=kundli if isinstance(kundli, dict) else None, top_planets=top_planets,
    )
    career = _career_stability(
        d, age=age, kundli=kundli if isinstance(kundli, dict) else None,
    )
    dependency = _event_dependency(d, age=age, question=question or "")
    legal = _legal_eligibility(d, age=age, question=question or "")

    blockers: list[str] = []
    soft: list[str] = []
    if not legal.get("ok"):
        blockers.append("legal_eligibility")
    if not age_check.get("ok") and age is not None:
        blockers.append("age_practical_floor")
    if not life.get("ok"):
        soft.append("life_stage_early")
    if finance.get("status") == "DEFER":
        soft.append("financial_readiness_weak")
    if career.get("status") in ("EARLY", "EMERGING"):
        soft.append("career_stability")
    if dependency.get("status") == "BLOCK":
        blockers.append("event_dependency")
    elif dependency.get("status") == "SOFT":
        soft.append("event_dependency")

    delay_years = 0
    if age is not None and age < min_prac:
        delay_years = int(min_prac - age)
    # Extra delay if finance/career weak for heavy domains.
    if d in ("property", "vehicle") and (
        finance.get("status") == "DEFER" or career.get("status") in ("EARLY", "EMERGING")
    ):
        delay_years = max(delay_years, 1 if age and age >= min_prac else delay_years)

    earliest_year = now_y + delay_years if delay_years else now_y

    if blockers:
        overall = "BLOCK_OR_DEFER"
        reality_ok = False
    elif soft or not age_check.get("ok"):
        overall = "EARLY_SIGNAL"
        reality_ok = False
    else:
        overall = "READY"
        reality_ok = True

    practical_reality = {
        "status": "PASS" if reality_ok and overall == "READY" else "DEFER",
        "ok": reality_ok and overall == "READY",
        "overall": overall,
        "blockers": blockers,
        "soft_flags": soft,
        "detail": (
            "Practical manifestation ready — dasha window actionable"
            if overall == "READY"
            else "Dasha yog ho sakta hai; practical manifestation later / softer framing"
        ),
    }

    # Narrator-facing note
    if overall == "READY":
        note = (
            f"PMF READY — age={age}, finance={finance.get('band')}, "
            f"career={career.get('career_signal')}. Primary dasha window = sahi time."
        )
    elif overall == "EARLY_SIGNAL":
        note = (
            f"PMF EARLY — user age={age}, practical floor={min_prac}, "
            f"flags={','.join(soft) or 'life_stage'}. Near dasha = prepare/early yog; "
            f"actionable sahi time ~{earliest_year}+ (age {min_prac}+ / readiness clear)."
        )
    else:
        note = (
            f"PMF DEFER — blockers={','.join(blockers)}. "
            f"Legal/age/dependency clear hone ke baad timing window cite karo "
            f"(earliest ~{earliest_year})."
        )

    return {
        "filter": "Practical Manifestation Filter",
        "version": PMF_VERSION,
        "domain": d,
        "user_age": age,
        "min_practical_age": min_prac,
        "earliest_year": earliest_year,
        "delay_years": delay_years,
        "overall": overall,
        "too_young_now": bool(age is not None and age < min_prac),
        "life_stage": life.get("label"),
        "eligible_now": overall == "READY",
        "practical_note": note,
        "checks": {
            "age": age_check,
            "life_stage": life,
            "financial_readiness": finance,
            "career_stability": career,
            "event_dependency": dependency,
            "legal_eligibility": legal,
            "practical_reality": practical_reality,
        },
    }


def format_pmf_lock_lines(pmf: dict[str, Any] | None) -> str:
    if not isinstance(pmf, dict) or not pmf:
        return ""
    checks = pmf.get("checks") if isinstance(pmf.get("checks"), dict) else {}
    lines = [
        "=== PRACTICAL MANIFESTATION FILTER (PMF — LOCKED) ===",
        f"overall={pmf.get('overall')} · life_stage={pmf.get('life_stage')} · "
        f"age={pmf.get('user_age')} · min_practical={pmf.get('min_practical_age')} · "
        f"earliest_year={pmf.get('earliest_year')}",
    ]
    for key in (
        "age",
        "life_stage",
        "financial_readiness",
        "career_stability",
        "event_dependency",
        "legal_eligibility",
        "practical_reality",
    ):
        c = checks.get(key) if isinstance(checks.get(key), dict) else {}
        if not c:
            continue
        lines.append(
            f"• {key}: {c.get('status')} — {c.get('detail') or c.get('label') or ''}"
        )
    lines.append(f"PRACTICAL_NOTE: {pmf.get('practical_note')}")
    lines.append(
        "RULE: Dasha dates invent mat karo. overall=READY → primary window sahi time. "
        "EARLY_SIGNAL/BLOCK_OR_DEFER → near window prepare bolo; actionable time "
        "earliest_year / readiness clear hone ke baad."
    )
    return "\n".join(lines)
