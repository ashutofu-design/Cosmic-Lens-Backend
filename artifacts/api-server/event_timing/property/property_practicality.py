"""Property timing — early buy vs delay (age, afford, running vs answer window)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

# India: stable income + down payment for home loan usually 24–28+.
MIN_HOME_PURCHASE_AGE = 24
SOFT_HOME_INCOME_AGE = 27
MIN_MONTHS_IF_YOUNG_WEAK = 18


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


def _months_until(start: Optional[datetime], now: datetime) -> int:
    if start is None or start <= now:
        return 0
    return max(0, (start.year - now.year) * 12 + (start.month - now.month))


def _buy_bucket(bucket: str) -> bool:
    return str(bucket or "buy").strip().lower() in (
        "buy",
        "registry",
        "possession",
        "construction",
        "loan",
    )


def _classify_buy_mode(
    *,
    answer: dict,
    timing_source: str,
    verdict: str,
    band: str,
    too_young: bool,
    afford: str,
    user_age: Optional[int],
    months_until: int,
    current_supports: bool,
) -> tuple[str, str, str]:
    """Return (purchase_timing_mode, buy_timing_label, delay_reason)."""
    weak = "LOW_PROBABILITY" in verdict.upper() or str(band or "") == "WEAK"
    is_active = bool(
        answer.get("is_active_now")
        or timing_source == "current_dasha_active"
    )

    if too_young:
        return "TOO_EARLY_AGE", "delay", "age_below_min_home_buy"

    if afford == "WEAK" and user_age is not None and user_age < SOFT_HOME_INCOME_AGE:
        if months_until < MIN_MONTHS_IF_YOUNG_WEAK:
            return "DELAY_AFFORD", "delay", "savings_income_weak_wait"

    if timing_source == "next_dasha_scan" or months_until >= 2:
        if weak or not is_active:
            return "DELAY_WAIT", "delay", "wait_for_rank1_karaka_window"
        return "DELAY_WAIT", "delay", "better_window_ahead"

    if is_active and not weak and afford != "WEAK":
        return "ACT_NOW", "early_buy", "current_dasha_favorable"

    if is_active and weak:
        return "DELAY_WAIT", "delay", "current_dasha_weak_for_buy"

    if current_supports and not weak:
        return "ACT_NOW", "early_buy", "running_period_supports_buy"

    return "DELAY_WAIT", "delay", "chart_suggests_wait"


def _strategy_for_mode(
    mode: str,
    *,
    answer: dict,
    months_until: int,
    user_age: Optional[int],
    min_age: int,
    afford: str,
    sig_name: str,
) -> str:
    start = answer.get("start_iso") or "?"
    end = answer.get("end_iso") or "?"
    lords = answer.get("lords") or f"{answer.get('md')}/{answer.get('ad')}/{answer.get('pd')}"

    if mode == "ACT_NOW":
        return (
            f"Ghar kharidne ke liye abhi chal raha dasha favorable hai — "
            f"early buy window ACTIVE ({start}→{end}, {lords}). "
            f"Loan/title verify karke isi period mein move karo."
        )
    if mode == "TOO_EARLY_AGE":
        age_txt = f"{user_age} saal" if user_age is not None else "kam umar"
        return (
            f"Chart mein property yog ho sakta hai, par abhi {age_txt} — "
            f"ghar buy practically {min_age}+ pe realistic. "
            f"Pehle savings/job stability; realistic window {start}→{end}."
        )
    if mode == "DELAY_AFFORD":
        return (
            f"Abhi jaldi buy mat karo — 2H/11H/savings axis weak hai. "
            f"Delay rakho; pehle down-payment + EMI capacity build karo. "
            f"Pehla practical buy window {start}→{end} ({lords})."
        )
    # DELAY_WAIT — most common when Mars window is future
    wait = f"~{months_until} mahine" if months_until else "thoda"
    sig_bit = f" ({sig_name} karaka window)" if sig_name else ""
    return (
        f"Abhi property buy DELAY rakho — running dasha weak / incomplete hai property ke liye. "
        f"{wait} wait karke rank #1 window {start}→{end} {lords}{sig_bit} cite karo. "
        f"Jaldi/early buy abhi recommend mat karo."
    )


def apply_property_practicality(
    out: dict,
    kundli: dict,
    birth: Any,
    question: str = "",
) -> dict:
    """Annotate early buy vs delay; does not replace dasha_running_now."""
    if not isinstance(out, dict):
        return out

    bucket = str(out.get("bucket") or "buy")
    if not _buy_bucket(bucket):
        return out

    min_age = MIN_HOME_PURCHASE_AGE
    user_age: Optional[int] = None
    try:
        from ask_career.timing_registry import resolve_user_age  # type: ignore

        user_age = resolve_user_age(question, birth, kundli)
    except Exception:
        pass

    birth_dt = _parse_birth_dt(birth)
    earliest = _earliest_purchase_dt(birth_dt, min_age)
    try:
        from event_timing.vehicle.vehicle_practicality import affordability_band

        afford = affordability_band(out.get("top_planets") or [])
    except Exception:
        afford = "MODERATE"

    now = datetime.utcnow()
    too_young = user_age is not None and user_age < min_age

    answer = (
        dict(out.get("answer_window") or {})
        if isinstance(out.get("answer_window"), dict)
        else {}
    )
    if not answer:
        answer = (
            dict(out.get("current_window") or {})
            if isinstance(out.get("current_window"), dict)
            else {}
        )

    answer_start = _parse_window_start(answer)
    if earliest and answer_start and answer_start < earliest:
        # Shift answer to first period on/after earliest practical date
        for p in out.get("timing_periods") or []:
            if not isinstance(p, dict):
                continue
            ps = _parse_window_start(p)
            if ps and (not earliest or ps >= earliest):
                answer = dict(p)
                out["answer_window"] = answer
                out["recommended_window"] = answer
                if answer.get("start_iso") and answer.get("end_iso"):
                    out["primary_window"] = f"{answer['start_iso']}→{answer['end_iso']}"
                out["timing_source"] = "practical_deferred"
                break
        answer_start = _parse_window_start(answer)

    months_until = _months_until(answer_start, now)
    timing_source = str(out.get("timing_source") or "")
    verdict = str(out.get("verdict") or "")
    band = str(out.get("band") or "")
    current_supports = bool(out.get("current_supports"))

    primary_sig = (
        out.get("primary_significator")
        if isinstance(out.get("primary_significator"), dict)
        else {}
    )
    sig_name = str(primary_sig.get("name") or "").strip().title()

    mode, label, delay_reason = _classify_buy_mode(
        answer=answer,
        timing_source=timing_source,
        verdict=verdict,
        band=band,
        too_young=too_young,
        afford=afford,
        user_age=user_age,
        months_until=months_until,
        current_supports=current_supports,
    )

    practicality: dict[str, Any] = {
        "user_age": user_age,
        "min_purchase_age": min_age,
        "affordability": afford,
        "too_young_now": too_young,
        "earliest_practical_iso": earliest.strftime("%Y-%m-%d") if earliest else None,
        "purchase_timing_mode": mode,
        "buy_timing_label": label,
        "delay_reason": delay_reason,
        "months_until_buy_window": months_until,
        "is_early_buy": label == "early_buy",
        "is_delay_recommended": label == "delay",
    }
    out["practicality"] = practicality
    out["buy_timing_label"] = label
    out["purchase_timing_mode"] = mode

    out["strategy"] = _strategy_for_mode(
        mode,
        answer=answer,
        months_until=months_until,
        user_age=user_age,
        min_age=min_age,
        afford=afford,
        sig_name=sig_name,
    )

    factors = list(out.get("factors") or [])
    factors.insert(
        0,
        (
            f"BUY_TIMING={label.upper()} mode={mode} "
            f"months_until={months_until} afford={afford} reason={delay_reason}"
        ),
    )
    out["factors"] = factors[:16]

    warnings = list(out.get("brand_safety_warnings") or [])
    if label == "delay":
        warnings.insert(
            0,
            "LLM: pehle batao DELAY — abhi jaldi buy mat recommend karo; "
            f"rank #1 window {answer.get('start_iso', '?')} se cite karo.",
        )
    elif label == "early_buy":
        warnings.insert(
            0,
            "LLM: early buy / ACT NOW — current favorable window mein buy timing bolo; "
            "delay mat bolo jab mode=ACT_NOW.",
        )
    out["brand_safety_warnings"] = warnings

    if mode in ("DELAY_WAIT", "DELAY_AFFORD", "TOO_EARLY_AGE") and "DELAY" not in verdict:
        out["verdict"] = "PROPERTY_BUY_DELAY"
        out["band"] = out.get("band") or "MEDIUM"

    return out
