"""Vehicle timing — age + affordability practicality (beyond 4H dasha rules)."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

# India: license ~18, but loan/EMI + stable income usually later.
MIN_CAR_PURCHASE_AGE = 25
MIN_BIKE_PURCHASE_AGE = 19
# Below this age, weak finance chart → do not cite <12 month purchase window.
SOFT_INCOME_AGE = 23
MIN_MONTHS_IF_YOUNG_WEAK = 12


def _is_two_wheeler_question(question: str) -> bool:
    q = (question or "").strip()
    return bool(
        re.search(
            r"(?ix)\b(bike|bikes|scooter|scooty|motorcycle|motorbike|two[\s-]?wheeler)\b",
            q,
        )
        and not re.search(r"(?ix)\b(car|cars|suv|sedan|four[\s-]?wheeler)\b", q)
    )


def _min_purchase_age(question: str, bucket: str) -> int:
    if bucket in ("maintenance", "sell"):
        return MIN_BIKE_PURCHASE_AGE
    if _is_two_wheeler_question(question):
        return MIN_BIKE_PURCHASE_AGE
    return MIN_CAR_PURCHASE_AGE


def _parse_birth_dt(birth: Any) -> Optional[datetime]:
    if birth is None:
        return None
    if isinstance(birth, datetime):
        return birth
    if isinstance(birth, dict):
        for key in ("datetime", "date", "dob", "birth_date"):
            raw = birth.get(key)
            if raw:
                return _parse_birth_dt(raw)
    if isinstance(birth, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(birth.strip()[:19], fmt)
            except ValueError:
                continue
    return None


def _earliest_purchase_dt(birth_dt: Optional[datetime], min_age: int) -> Optional[datetime]:
    if birth_dt is None:
        return None
    try:
        return birth_dt.replace(year=birth_dt.year + min_age)
    except ValueError:
        return birth_dt.replace(year=birth_dt.year + min_age, day=28)


def _parse_window_start(w: dict) -> Optional[datetime]:
    raw = w.get("start_iso") or w.get("start")
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(raw)[:19], fmt)
        except ValueError:
            continue
    return None


def affordability_band(top_planets: list) -> str:
    """Chart-level purchase capacity — 2H/11H karakas, not dasha alone."""
    scores: dict[str, float] = {}
    for row in top_planets or []:
        if isinstance(row, dict) and row.get("name"):
            scores[str(row["name"])] = float(row.get("score") or 0)
    wealth = (
        scores.get("Jupiter", 0) * 1.0
        + scores.get("Venus", 0) * 0.85
        + scores.get("Mercury", 0) * 0.35
    )
    leak = scores.get("Saturn", 0) * 0.45 + scores.get("Rahu", 0) * 0.25
    net = wealth - leak
    if net >= 16:
        return "CAPABLE"
    if net >= 9:
        return "MODERATE"
    return "WEAK"


def _window_practical(
    w: dict,
    *,
    now: datetime,
    earliest: Optional[datetime],
    user_age: Optional[int],
    afford: str,
) -> bool:
    if not isinstance(w, dict) or not w.get("start_iso"):
        return False
    start = _parse_window_start(w)
    if start is None:
        return False
    if earliest and start < earliest:
        return False
    if user_age is not None and user_age < SOFT_INCOME_AGE and afford == "WEAK":
        months = (start.year - now.year) * 12 + (start.month - now.month)
        if months < MIN_MONTHS_IF_YOUNG_WEAK:
            return False
    return True


def apply_vehicle_practicality(
    out: dict,
    kundli: dict,
    birth: Any,
    question: str = "",
) -> dict:
    """Shift astro windows when age/income make near-term purchase unrealistic."""
    if not isinstance(out, dict):
        return out

    bucket = str(out.get("bucket") or "buy")
    min_age = _min_purchase_age(question, bucket)
    user_age: Optional[int] = None
    try:
        from ask_career.timing_registry import resolve_user_age  # type: ignore

        user_age = resolve_user_age(question, birth, kundli)
    except Exception:
        pass

    birth_dt = _parse_birth_dt(birth)
    earliest = _earliest_purchase_dt(birth_dt, min_age)
    afford = affordability_band(out.get("top_planets") or [])
    now = datetime.utcnow()
    too_young = user_age is not None and user_age < min_age

    practicality: dict[str, Any] = {
        "user_age": user_age,
        "min_purchase_age": min_age,
        "affordability": afford,
        "too_young_now": too_young,
        "earliest_practical_iso": earliest.strftime("%Y-%m-%d") if earliest else None,
    }
    out["practicality"] = practicality

    factors = list(out.get("factors") or [])
    factors.append(
        f"PRACTICAL age={user_age} min={min_age} afford={afford} too_young={too_young}"
    )

    primary = out.get("current_window") if isinstance(out.get("current_window"), dict) else None
    if _window_practical(
        primary or {},
        now=now,
        earliest=earliest,
        user_age=user_age,
        afford=afford,
    ):
        out["factors"] = factors
        return out

    candidates: list[dict] = []
    for w in out.get("next_3_windows") or []:
        if isinstance(w, dict):
            candidates.append(w)
    if isinstance(out.get("next_child_window"), dict):
        candidates.append(out["next_child_window"])

    chosen = None
    for w in candidates:
        if _window_practical(w, now=now, earliest=earliest, user_age=user_age, afford=afford):
            chosen = dict(w)
            break

    if chosen:
        out["current_window"] = chosen
        out["timing_source"] = "practical_deferred"
        out["current_supports"] = False
        factors.append(
            f"PRACTICAL deferred window → {chosen.get('start_iso')}→{chosen.get('end_iso')} "
            f"(age/income gate; dasha alone not enough)"
        )
        if too_young:
            out["strategy"] = (
                f"Chart dasha active ho sakta hai, par abhi umar {user_age} hai — "
                f"car/bike purchase practically {min_age}+ pe realistic. "
                f"Pehla practical window {chosen.get('start_iso')}→{chosen.get('end_iso')}."
            )
        elif afford == "WEAK":
            out["strategy"] = (
                f"Dasha 4H/11H support dikhata hai par income/savings axis weak — "
                f"pehle stability, phir {chosen.get('start_iso')}→{chosen.get('end_iso')} window."
            )
        else:
            out["strategy"] = (
                f"Practical purchase window {chosen.get('start_iso')}→{chosen.get('end_iso')} "
                f"(BCP/dasha + age/income check)."
            )
        out["verdict"] = out.get("verdict") or "VEHICLE_PURCHASE_DELAY"
        out["band"] = out.get("band") or "MEDIUM"
    else:
        label = "bike/scooter" if min_age <= MIN_BIKE_PURCHASE_AGE and _is_two_wheeler_question(question) else "car"
        age_hint = f"umr {user_age}" if user_age is not None else "umr unknown"
        earliest_txt = earliest.strftime("%Y-%m") if earliest else f"{min_age}+"
        out["strategy"] = (
            f"Dasha 4H/11H trigger ho sakta hai, par {age_hint} — {label} purchase abhi "
            f"practically realistic nahi. Pehle income/license/savings; "
            f"realistic earliest ~{earliest_txt}."
        )
        out["verdict"] = "VEHICLE_PURCHASE_DELAY"
        out["band"] = "WEAK"
        out["timing_source"] = "practical_blocked"
        factors.append("PRACTICAL no window passed age+afford gate")

    warnings = list(out.get("brand_safety_warnings") or [])
    if too_young:
        warnings.insert(
            0,
            f"User abhi {user_age} saal — {min_age}+ se pehle car purchase practical answer mat do.",
        )
    elif afford == "WEAK" and user_age is not None and user_age < SOFT_INCOME_AGE:
        warnings.insert(
            0,
            "2H/11H weak — loan/EMI capacity pehle build karo; 6 mahine mein pakka mat bolo.",
        )
    out["brand_safety_warnings"] = warnings
    out["factors"] = factors

    try:
        from event_timing._shared.step_audit import attach_timing_pipeline_audit

        return attach_timing_pipeline_audit(out, "vehicle")
    except Exception:
        return out
