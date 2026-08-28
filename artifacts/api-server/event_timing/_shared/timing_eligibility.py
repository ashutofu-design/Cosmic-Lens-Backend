"""Shared timing eligibility — wraps Practical Manifestation Filter (PMF).

Order: PMF (age, life stage, finance, career, dependency, legal, reality)
→ earliest year → narrator lock. Engines keep dasha math.
"""
from __future__ import annotations

from typing import Any, Optional

# Re-export from PMF so UTF / callers keep stable imports.
from event_timing._shared.practical_manifestation_filter import (  # noqa: F401
    DOMAIN_MIN_ELIGIBLE_AGE,
    min_eligible_age,
    resolve_timing_age,
)


def assess_timing_eligibility(
    domain: str,
    *,
    question: str = "",
    birth: Any = None,
    kundli: Any = None,
    user_age: Optional[int] = None,
    top_planets: Any = None,
) -> dict[str, Any]:
    """PMF-backed eligibility dict (backward compatible keys)."""
    from event_timing._shared.practical_manifestation_filter import (
        run_practical_manifestation_filter,
    )

    pmf = run_practical_manifestation_filter(
        domain,
        question=question,
        birth=birth,
        kundli=kundli,
        user_age=user_age,
        top_planets=top_planets,
    )
    return {
        "domain": pmf.get("domain"),
        "user_age": pmf.get("user_age"),
        "min_eligible_age": pmf.get("min_practical_age"),
        "too_young_now": pmf.get("too_young_now"),
        "delay_years": pmf.get("delay_years"),
        "earliest_year": pmf.get("earliest_year"),
        "life_stage": pmf.get("life_stage"),
        "practical_note": pmf.get("practical_note"),
        "eligible_now": pmf.get("eligible_now"),
        "overall": pmf.get("overall"),
        "pmf": pmf,
    }


def format_eligibility_lock_lines(elig: dict[str, Any] | None) -> str:
    if not isinstance(elig, dict) or not elig:
        return ""
    pmf = elig.get("pmf") if isinstance(elig.get("pmf"), dict) else None
    if pmf:
        from event_timing._shared.practical_manifestation_filter import (
            format_pmf_lock_lines,
        )

        return format_pmf_lock_lines(pmf)
    lines = [
        "=== TIMING ELIGIBILITY (LOCKED — life-stage before dates) ===",
        f"life_stage={elig.get('life_stage')} · age={elig.get('user_age')} · "
        f"min_eligible={elig.get('min_eligible_age')} · "
        f"too_young={elig.get('too_young_now')} · earliest_year={elig.get('earliest_year')}",
        f"PRACTICAL_NOTE: {elig.get('practical_note')}",
    ]
    return "\n".join(lines)


def attach_timing_eligibility(
    raw: dict[str, Any] | None,
    *,
    domain: str,
    question: str = "",
    birth: Any = None,
    kundli: Any = None,
    user_age: Optional[int] = None,
) -> dict[str, Any]:
    """Stamp PMF onto engine raw + append lock lines to _prompt_block."""
    out = dict(raw) if isinstance(raw, dict) else {}
    top = out.get("top_planets") or out.get("ranked_significators")
    elig = assess_timing_eligibility(
        domain,
        question=question,
        birth=birth,
        kundli=kundli,
        user_age=user_age if user_age is not None else out.get("user_age"),
        top_planets=top,
    )
    out["timing_eligibility"] = elig
    out["pmf"] = elig.get("pmf")
    out["life_stage"] = elig.get("life_stage")
    out["practical_note"] = elig.get("practical_note")
    out["user_age"] = elig.get("user_age")
    if elig.get("too_young_now") or elig.get("overall") in (
        "EARLY_SIGNAL",
        "BLOCK_OR_DEFER",
    ):
        out["eligibility_deferred"] = True
        if not out.get("band"):
            out["band"] = "MEDIUM"
        warnings = list(out.get("brand_safety_warnings") or [])
        note = str(elig.get("practical_note") or "")
        if note and note not in warnings:
            warnings.insert(0, note)
        out["brand_safety_warnings"] = warnings[:8]

    lock = format_eligibility_lock_lines(elig)
    base = str(out.get("_prompt_block") or "")
    if lock and "PRACTICAL MANIFESTATION FILTER" not in base:
        out["_prompt_block"] = (base + "\n\n" + lock).strip() if base else lock
    return out


def enrich_timing_prompt_block(
    block: str,
    *,
    domain: str,
    question: str = "",
    birth: Any = None,
    kundli: Any = None,
    user_age: Optional[int] = None,
    window: str = "",
    predicted_age: Optional[int] = None,
) -> str:
    """Append PMF + AGE LOCK to an already-built marriage/career/UTF block."""
    text = (block or "").strip()
    if not text:
        return text
    elig = assess_timing_eligibility(
        domain,
        question=question,
        birth=birth,
        kundli=kundli,
        user_age=user_age,
    )
    parts = [text]
    if "PRACTICAL MANIFESTATION FILTER" not in text:
        lock = format_eligibility_lock_lines(elig)
        if lock:
            parts.append(lock)
    try:
        from event_timing._shared.age_aware_timing_reply import (
            lock_lines_for_prompt,
            resolve_user_age_for_timing,
        )

        ua = elig.get("user_age")
        if ua is None:
            ua = resolve_user_age_for_timing(
                question=question, birth=birth, kundli=kundli, user_age=user_age,
            )
        age_lock = lock_lines_for_prompt(
            domain,
            user_age=int(ua) if ua is not None else None,
            window=window or "",
            question=question,
            predicted_age=predicted_age,
        )
        if age_lock and "AGE LOCK (MANDATORY" not in text:
            parts.append(age_lock)
    except Exception:
        pass
    return "\n\n".join(p for p in parts if p).strip()
