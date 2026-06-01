"""
Honest Love Reality engines — deterministic, affliction-heavy scoring.
Every chapter: score/100, risk_level, emotional_summary, reasons.
"""
from __future__ import annotations

from typing import Any

from kundli_engine import calculate_kundli

from vedic.love_reality import reader_context
from vedic.love_reality.relationship_signals import CoupleSignals, analyze_couple
from vedic.love_reality.scoring_core import (
    KundliReader,
    clamp,
    level_future,
    level_loyalty,
    level_return,
    risk_band_high_is_bad,
    risk_band_high_is_good,
)


def _load_couple(p1: dict, p2: dict) -> tuple[KundliReader, KundliReader, CoupleSignals]:
    k1 = calculate_kundli({**p1, "name": p1.get("name") or "You"})
    k2 = calculate_kundli({**p2, "name": p2.get("name") or "Partner"})
    r1, r2 = KundliReader(k1), KundliReader(k2)
    return r1, r2, analyze_couple(r1, r2)


def _cap_by_affliction(score: int, sig: CoupleSignals, harsh_cap: int, moderate_cap: int) -> int:
    if sig.combined_affliction >= 55:
        return min(score, harsh_cap)
    if sig.combined_affliction >= 35:
        return min(score, moderate_cap)
    return score


def _love_dimension_breakdown(score_i: int, sig: CoupleSignals) -> dict[str, int]:
    """0–100 scores for Love Compatibility UI bars (mobile expects these keys)."""
    p1, p2 = sig.p1, sig.p2

    emotional = float(score_i)
    if sig.moon_mismatch:
        emotional -= 14
    if p1.moon_debil or p2.moon_debil:
        emotional -= 10
    if p1.moon_afflicted or p2.moon_afflicted:
        emotional -= 8
    if p1.moon_in_8th or p2.moon_in_8th:
        emotional -= 6
    if not sig.moon_mismatch and not (p1.moon_debil or p2.moon_debil):
        emotional += 6

    attraction = 50.0
    if p1.venus_debil or p2.venus_debil:
        attraction -= 16
    elif p1.venus_surface_strong_only or p2.venus_surface_strong_only:
        attraction += 4
    else:
        attraction += 14
    if p1.venus_mars_conjunct or p2.venus_mars_conjunct:
        attraction += 10
    if sig.cross_rahu_venus:
        attraction += 6

    communication = float(score_i)
    if sig.moon_mismatch:
        communication -= 18
    else:
        communication += 8
    if p1.emotional_instability or p2.emotional_instability:
        communication -= 10

    karmic = 42.0
    if sig.cross_rahu_venus:
        karmic += 22
    if p1.rahu_on_7th_axis or p2.rahu_on_7th_axis:
        karmic += 14
    if p1.ketu_detachment or p2.ketu_detachment:
        karmic += 8
    if not sig.cross_rahu_venus and not (p1.rahu_on_7th_axis or p2.rahu_on_7th_axis):
        karmic -= 6

    stability = float(score_i) - 4
    if p1.seventh_lord_dusthana or p2.seventh_lord_dusthana:
        stability -= 16
    if p1.seventh_lord_debil or p2.seventh_lord_debil:
        stability -= 10
    if p1.saturn_on_7th or p2.saturn_on_7th:
        stability -= 12
    if p1.separation_yoga or p2.separation_yoga:
        stability -= 14
    elif not p1.separation_yoga and not p2.separation_yoga:
        stability += 10

    dasha_transit = float(score_i)
    if p1.separation_yoga or p2.separation_yoga:
        dasha_transit -= 12
    if p1.reconnection_yoga or p2.reconnection_yoga:
        dasha_transit += 8
    if sig.combined_affliction >= 50:
        dasha_transit -= 8
    elif sig.combined_affliction < 30:
        dasha_transit += 6

    return {
        "emotional": clamp(emotional),
        "attraction": clamp(attraction),
        "communication": clamp(communication),
        "karmic": clamp(karmic),
        "stability": clamp(stability),
        "dasha_transit": clamp(dasha_transit),
        "dosha_severity": clamp(sig.combined_affliction),
        "combined_affliction": sig.combined_affliction,
        "p1_affliction": p1.affliction_weight,
        "p2_affliction": p2.affliction_weight,
    }


def run_love_compatibility(
    p1: dict, p2: dict, *, skip_ai_insight: bool = False
) -> dict[str, Any]:
    r1, r2, sig = _load_couple(p1, p2)
    reasons = list(sig.p1.notes[:4]) + list(sig.p2.notes[:4]) + sig.synastry_notes

    score = 52.0
    ledger: list[dict[str, Any]] = [
        {
            "label": "Base compatibility anchor",
            "delta": None,
            "note": "Starting value 52 before chart adjustments",
            "base": 52,
        },
    ]

    def _add(label: str, delta: float, note: str) -> None:
        nonlocal score
        score += delta
        ledger.append({"label": label, "delta": int(delta) if delta == int(delta) else delta, "note": note})

    for person in (sig.p1, sig.p2):
        if person.venus_debil:
            _add(f"{person.name}: Venus debilitated", -14, "Love nature unstable under stress")
        elif person.venus_d9_weak:
            _add(f"{person.name}: Navamsa Venus weak", -6, "Inner commitment layer fragile")
        if person.moon_debil or person.moon_afflicted:
            _add(f"{person.name}: Moon afflicted", -11, "Emotional reactions unpredictable")
        if person.seventh_lord_dusthana or person.seventh_lord_debil:
            _add(f"{person.name}: 7th lord weak", -12, "Partnership structure strained")
        if person.saturn_on_7th:
            _add(f"{person.name}: Saturn on 7th", -8, "Distance and delay on partnership axis")
        if person.reconnection_yoga and not person.separation_yoga:
            _add(f"{person.name}: Reconnection yoga", 6, "Emotional reopening capacity")
        if not person.fifth_lord_weak and not person.venus_debil:
            _add(f"{person.name}: 5th lord support", 4, "Romance spark can hold under pressure")

    if sig.moon_mismatch:
        _add("Moon–Moon rhythm clash", -7, "One holds in, the other pushes out")
    if sig.cross_rahu_venus:
        _add("Rahu on partner Venus", -9, "Obsession / loyalty blur between charts")
    if not sig.p1.separation_yoga and not sig.p2.separation_yoga:
        _add("No active separation yoga", 5, "Timing less hostile to staying together")

    raw_score = clamp(score)
    score_i = _cap_by_affliction(raw_score, sig, harsh_cap=48, moderate_cap=58)
    if score_i < raw_score:
        ledger.append({
            "label": "Affliction cap applied",
            "delta": score_i - raw_score,
            "note": f"Combined affliction {sig.combined_affliction} — score capped for honesty",
        })
    risk = risk_band_high_is_good(score_i)

    if score_i >= 62:
        summary = "Real compatibility exists, but it needs emotional honesty — not fantasy."
    elif score_i >= 45:
        summary = "The bond runs on attachment and memory more than stable peace."
    else:
        summary = "This chart shows emotional instability and repeated separation patterns — not a easy-flow love."

    factors = {
        "emotional": "weak" if score_i < 45 else "medium" if score_i < 62 else "strong",
        "attraction": "weak" if sig.cross_rahu_venus else "medium",
        "communication": "weak" if sig.moon_mismatch else "medium",
        "karmic": "strong" if sig.cross_rahu_venus or sig.p1.rahu_on_7th_axis else "medium",
        "stability": "weak" if sig.p1.seventh_lord_dusthana or sig.p2.seventh_lord_dusthana else "medium",
    }

    payload = {
        "score": score_i,
        "risk_level": risk,
        "emotional_summary": summary,
        "factors": factors,
        "reasons": reasons[:14],
        "breakdown": {
            **_love_dimension_breakdown(score_i, sig),
            "raw_before_cap": raw_score,
        },
        "score_ledger": ledger,
        "final_score": score_i,
    }
    if not skip_ai_insight:
        try:
            from vedic.love_compat_insight import generate_relationship_insight

            payload["insight"] = generate_relationship_insight(
                score=score_i,
                breakdown=payload["breakdown"],
                reasons=payload["reasons"],
            )
        except Exception:
            payload["insight"] = None
    else:
        payload["insight"] = None
    from vedic.love_reality.chart_proof import build_chart_proof

    payload["chart_proof"] = build_chart_proof(r1, r2, sig)
    return payload


def run_breakup_chances(p1: dict, p2: dict) -> dict[str, Any]:
    r1, r2, sig = _load_couple(p1, p2)
    reasons: list[str] = []

    score = 38.0
    for person in (sig.p1, sig.p2):
        if person.seventh_lord_dusthana:
            score += 14
            reasons.append("7th lord in dusthana — bond survives emotionally but not practically.")
        if person.seventh_lord_debil:
            score += 10
        if person.saturn_on_7th:
            score += 12
            reasons.append("Saturn on 7th axis — emotional distance and break timing active.")
        if person.mars_on_7th:
            score += 9
            reasons.append("Mars on 7th — fights escalate into rupture.")
        if person.rahu_on_7th_axis:
            score += 10
            reasons.append("Rahu on 7th — confusion, obsession, unstable commitment.")
        if person.venus_debil or person.moon_debil:
            score += 8
            reasons.append("Venus/Moon weakness — loyalty and affection fracture under stress.")
        if person.third_person_risk:
            score += 11
            reasons.append("Third-person interference risk visible in chart.")
        if person.ketu_detachment:
            score += 7
            reasons.append("Ketu detachment — ghosting / sudden emotional exit pattern.")
        if person.separation_yoga:
            score += 6

    if sig.combined_affliction >= 50:
        score += 10
        reasons.append("Relationship carries strong breakup signatures across both charts.")

    score_i = clamp(score)
    if score_i <= 35 and not reasons:
        reasons.append("Charts do not show acute break pressure in this window — friction still needs care.")

    if score_i >= 72:
        summary = "Breakup pressure is high — separation signatures dominate timing."
    elif score_i >= 52:
        summary = "The bond is under real strain; breaks or near-breaks are plausible without repair."
    else:
        summary = "Break risk is present but not the only story — timing and behavior still matter."

    from vedic.love_reality.chart_proof import build_chart_proof

    return {
        "breakup_score": score_i,
        "score": score_i,
        "risk_level": risk_band_high_is_bad(score_i),
        "emotional_summary": summary,
        "factors": {
            "dasha": "severe" if score_i >= 65 else "moderate" if score_i >= 45 else "low",
            "houses": "severe" if any(p.seventh_lord_dusthana for p in (sig.p1, sig.p2)) else "moderate",
            "venus_moon": "severe" if any(p.venus_debil or p.moon_debil for p in (sig.p1, sig.p2)) else "low",
            "kp": "moderate",
        },
        "reasons": (reasons + sig.p1.notes + sig.p2.notes)[:14],
        "breakdown": {"combined_affliction": sig.combined_affliction},
        "chart_proof": build_chart_proof(r1, r2, sig),
    }


def _person_loyalty_penalty(person) -> float:
    pen = 0.0
    if person.venus_debil:
        pen += 18
    if person.moon_afflicted or person.moon_debil:
        pen += 14
    if person.moon_in_8th:
        pen += 14
    if person.moon_d9_debil:
        pen += 12
    if person.venus_mars_conjunct:
        pen += 16
    if person.rahu_on_7th_axis or person.third_person_risk:
        pen += 14
    if person.emotional_instability:
        pen += 8
    if person.seventh_lord_dusthana or person.seventh_lord_debil:
        pen += 10
    if person.saturn_on_7th:
        pen += 6
    return pen


def _person_loyalty_safe_bonus(person) -> float:
    """Only reward loyalty when chart is clean — never for 'Venus in Taurus' alone."""
    if person.loyalty_risk_high:
        return 0.0
    if person.venus_debil or person.seventh_lord_debil or person.third_person_risk:
        return 0.0
    bonus = 0.0
    if not person.venus_debil and not person.moon_debil:
        bonus += 4
    if not person.seventh_lord_dusthana and not person.mars_on_7th:
        bonus += 4
    return bonus


def run_loyalty_check(p1: dict, p2: dict) -> dict[str, Any]:
    r1, r2, sig = _load_couple(p1, p2)
    reasons: list[str] = []

    score = 48.0
    for person in (sig.p1, sig.p2):
        pen = _person_loyalty_penalty(person)
        if pen > 0:
            score -= pen
        score += _person_loyalty_safe_bonus(person)
        for note in person.notes:
            if "do NOT read" in note or "loyalty risk" in note.lower() or "surface warmth" in note:
                reasons.append(note)
            elif any(
                x in note.lower()
                for x in (
                    "8th",
                    "venus-mars",
                    "debilitated",
                    "third-person",
                    "rahu",
                    "nodes on 7th",
                    "navamsa moon",
                )
            ):
                reasons.append(note)

    if sig.cross_rahu_venus:
        score -= 15
        reasons.append("Partner Rahu on your Venus — loyalty blur, obsession, external pull.")

    score_raw = _cap_by_affliction(clamp(score), sig, harsh_cap=35, moderate_cap=45)
    pg = reader_context.normalize_reader_gender(p1)
    score_i = reader_context.loyalty_score_reader_nudge(
        score_raw,
        pg,
        p1_reader_risk_high=sig.p1.loyalty_risk_high,
    )

    narrative_locks: list[str] = []
    for person in (sig.p1, sig.p2):
        if person.loyalty_risk_high or score_raw < 52:
            narrative_locks.append(
                f"NEVER describe {person.name} as 'naturally loyal', 'devoted', or 'faithful by nature'. "
                f"Chart shows passion/hidden layers that can contradict surface Venus strength."
            )
        if person.venus_mars_conjunct:
            narrative_locks.append(
                f"{person.name}: Venus-Mars — impulsive attraction; NOT a loyalty guarantee."
            )
        if person.venus_surface_strong_only and person.loyalty_risk_high:
            narrative_locks.append(
                f"{person.name}: strong Venus sign (e.g. Taurus) is STYLE only — real-world betrayal risk remains."
            )

    narrative_locks.extend(
        reader_context.loyalty_narrative_holds(
            pg,
            p1_reader_risk_high=sig.p1.loyalty_risk_high,
            p2_partner_risk_high=sig.p2.loyalty_risk_high,
        )
    )
    if score_i >= 68:
        summary = "Loyalty indicators are relatively strong — protective attachment pattern visible."
        behavior = "loyal"
    elif score_i >= 48:
        summary = "Loyalty is mixed — warmth on surface, consistency breaks under stress or temptation."
        behavior = "emotionally unstable"
    else:
        summary = (
            "Loyalty stability is weak — chart shows secrecy, impulse, or external pull; "
            "do not trust 'strong Venus' labels alone."
        )
        behavior = "tempted" if sig.p1.third_person_risk or sig.p2.third_person_risk else "dual-nature"

    # Dedupe reasons
    seen: set[str] = set()
    unique: list[str] = []
    for r in reasons + sig.synastry_notes:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    from vedic.love_reality.chart_proof import build_chart_proof

    return {
        "loyalty_score": score_i,
        "score": score_i,
        "risk_level": risk_band_high_is_good(score_i),
        "loyalty_level": level_loyalty(score_i),
        "behavior_type": behavior,
        "time_factor": "long_term_pattern" if score_i < 45 else "temporary_phase",
        "emotional_summary": summary,
        "narrative_locks": narrative_locks,
        "factors": {
            "venus": "weak" if any(p.venus_debil or p.venus_mars_conjunct for p in (sig.p1, sig.p2)) else "mixed",
            "moon": "weak" if any(p.moon_afflicted or p.moon_in_8th or p.moon_d9_debil for p in (sig.p1, sig.p2)) else "medium",
            "7th_house": "afflicted" if any(p.saturn_on_7th or p.mars_on_7th for p in (sig.p1, sig.p2)) else "stable",
            "rahu": "active" if sig.cross_rahu_venus or sig.p1.rahu_on_7th_axis else "quiet",
        },
        "reasons": unique[:14],
        "breakdown": {
            "combined_affliction": sig.combined_affliction,
            "p1_loyalty_risk": sig.p1.loyalty_risk_high,
            "p2_loyalty_risk": sig.p2.loyalty_risk_high,
        },
        "chart_proof": build_chart_proof(r1, r2, sig),
    }


def run_will_return(p1: dict, p2: dict) -> dict[str, Any]:
    """p1 = primary (person asking). p2 = partner synastry."""
    r1, r2, sig = _load_couple(p1, p2)
    primary = sig.p1
    reasons: list[str] = []

    score = 42.0
    if primary.reconnection_yoga:
        score += 14
        reasons.append("5th/Venus reconnection yogas active — emotional thread not fully cut.")
    if primary.fifth_lord_weak:
        score -= 12
    if primary.venus_debil or primary.moon_debil:
        score -= 16
        reasons.append("Venus/Moon afflicted — return may be felt emotionally, not acted cleanly.")
    if primary.separation_yoga or primary.saturn_on_7th:
        score -= 18
        reasons.append("Separation yogas dominate — physical return probability currently low.")
    if primary.ketu_detachment:
        score -= 12
        reasons.append("Ketu detachment — closure energy stronger than reunion.")
    if primary.mars_on_7th:
        score -= 6
        reasons.append("Mars on 7th — reunion attempts may turn into conflict quickly.")

    if sig.p2.reconnection_yoga and not primary.separation_yoga:
        score += 5
        reasons.append("Partner chart shows some reopening energy — mutual pull possible but unstable.")

    score_prior = reader_context.will_return_with_population_prior(score)
    score_i = _cap_by_affliction(clamp(score_prior), sig, harsh_cap=24, moderate_cap=34)
    reasons.insert(
        0,
        "Population prior: most estranged / post-breakup bonds do not see X come back in a real way — "
        "only strong reunion yogas lift that reading.",
    )

    chance = level_return(score_i)
    if score_i >= 58:
        summary = "Reconnection energy is active — return is possible, not guaranteed."
        reunion = "unstable"
        window = "within 2–6 months if both engage"
    elif score_i >= 38:
        summary = "Emotional attachment remains, but stability for a real return looks weak."
        reunion = "temporary"
        window = "6–12 months — may be contact without commitment"
    else:
        summary = "This connection appears emotionally unfinished, but a real reunion looks difficult now."
        reunion = "unstable"
        window = "unlikely in near term — closure energy stronger"

    from vedic.love_reality.chart_proof import build_chart_proof

    return {
        "return_probability": score_i,
        "score": score_i,
        "risk_level": risk_band_high_is_good(score_i),
        "return_chance": chance,
        "time_window": window,
        "reunion_type": reunion,
        "initiator": "person A" if score_i >= 45 else "mutual",
        "emotional_summary": summary,
        "factors": {
            "dasha": "mixed",
            "transit": "mixed",
            "love_houses": "active" if primary.reconnection_yoga else "weak",
            "separation_houses": "active" if primary.separation_yoga else "quiet",
        },
        "reasons": (reasons + primary.notes[:6])[:14],
        "breakdown": {"combined_affliction": sig.combined_affliction},
        "chart_proof": build_chart_proof(r1, r2, sig),
    }


def run_future_outcome(p1: dict, p2: dict) -> dict[str, Any]:
    r1, r2, sig = _load_couple(p1, p2)
    reasons: list[str] = []

    score = 48.0
    if sig.p1.seventh_lord_dusthana and sig.p2.seventh_lord_dusthana:
        score -= 15
        reasons.append("Both charts show weak 7th-lord foundation — long-term drift likely.")
    elif sig.p1.seventh_lord_dusthana or sig.p2.seventh_lord_dusthana:
        score -= 8

    if sig.p1.venus_debil and sig.p2.venus_debil:
        score -= 12
    if sig.moon_mismatch:
        score -= 8
    if sig.p1.reconnection_yoga or sig.p2.reconnection_yoga:
        score += 8
    if not sig.p1.separation_yoga and not sig.p2.separation_yoga:
        score += 6

    score_i = _cap_by_affliction(clamp(score), sig, harsh_cap=40, moderate_cap=52)
    outcome = level_future(score_i)

    if score_i >= 60:
        summary = "Trajectory can grow if both stop repeating the same emotional loop."
        phase = "Repair window open"
    elif score_i >= 42:
        summary = "Future is mixed — attachment continues while peace stays uneven."
        phase = "Uncertain bonding phase"
    else:
        summary = "Charts lean toward emotional exhaustion — long-term stability is not assured."
        phase = "Closure or distance phase strengthening"

    from vedic.love_reality.chart_proof import build_chart_proof

    return {
        "future_score": score_i,
        "score": score_i,
        "risk_level": risk_band_high_is_good(score_i),
        "outcome": outcome,
        "confidence": clamp(55 + (100 - sig.combined_affliction) // 3, 30, 88),
        "current_phase": phase,
        "next_shift": "3–6 months — dasha/transit will tilt the emotional tone",
        "timeline_flow": [
            {"period": "Now", "trend": "mixed" if score_i >= 42 else "down", "reason": summary},
            {"period": "3 months", "trend": "mixed", "reason": "Venus/Moon periods decide warmth vs withdrawal"},
            {"period": "6+ months", "trend": "up" if score_i >= 55 else "down", "reason": outcome},
        ],
        "emotional_summary": summary,
        "factors": {
            "combined_affliction": str(sig.combined_affliction),
        },
        "reasons": (reasons + sig.synastry_notes)[:12],
        "breakdown": {"combined_affliction": sig.combined_affliction},
        "generated_at": None,
        "chart_proof": build_chart_proof(r1, r2, sig),
    }


def run_red_flags(p1: dict, p2: dict, breakup: dict) -> dict[str, Any]:
    """Hidden red flags — derived from afflictions + breakup, sharper copy."""
    _, _, sig = _load_couple(p1, p2)
    flags: list[str] = []
    if sig.p1.third_person_risk or sig.p2.third_person_risk:
        flags.append("Third-person or secrecy pattern on the love axis — trust erosion risk.")
    if sig.cross_rahu_venus:
        flags.append("Obsessive pull (Rahu–Venus) — bond feels fated but destabilizing.")
    if any(p.ketu_detachment for p in (sig.p1, sig.p2)):
        flags.append("Sudden emotional withdrawal / ghosting signature present.")
    if breakup.get("breakup_score", 0) >= 65:
        flags.append("Breakup pressure in timing — denial will cost more than clarity.")
    if not flags:
        flags.append("Subtle pride and unspoken resentment may grow if issues stay unaddressed.")

    score = clamp(breakup.get("breakup_score", 50) + 5)
    return {
        **breakup,
        "score": score,
        "risk_level": risk_band_high_is_bad(score),
        "emotional_summary": flags[0],
        "reasons": flags[:6],
        "source_engine": "love_reality_honest",
    }


def run_all_love_reality_engines(
    p1: dict, p2: dict, *, skip_ai_insight: bool = False
) -> dict[str, Any]:
    k1_raw = calculate_kundli({**p1, "name": p1.get("name") or "You"})
    k2_raw = calculate_kundli({**p2, "name": p2.get("name") or "Partner"})
    r1, r2 = KundliReader(k1_raw), KundliReader(k2_raw)

    lc = run_love_compatibility(p1, p2, skip_ai_insight=skip_ai_insight)
    bu = run_breakup_chances(p1, p2)
    ly = run_loyalty_check(p1, p2)
    wr = run_will_return(p1, p2)
    fo = run_future_outcome(p1, p2)
    rf = run_red_flags(p1, p2, bu)

    rd = reader_context.normalize_reader_gender(p1)

    from vedic.love_reality.chart_facts import enrich_bundle_for_pdf

    couple_sig = analyze_couple(r1, r2)

    base = {
        "p1": {
            "name": r1.name,
            "gender": p1.get("gender"),
            "nakshatra": k1_raw.get("nakshatra"),
            "rashi": k1_raw.get("moonSign"),
            "moonSign": k1_raw.get("moonSign"),
            "ascendant": k1_raw.get("ascendant"),
            "planets": k1_raw.get("planets") or [],
        },
        "p2": {
            "name": r2.name,
            "gender": p2.get("gender"),
            "nakshatra": k2_raw.get("nakshatra"),
            "rashi": k2_raw.get("moonSign"),
            "moonSign": k2_raw.get("moonSign"),
            "ascendant": k2_raw.get("ascendant"),
            "planets": k2_raw.get("planets") or [],
        },
        "love_compatibility": lc,
        "breakup_chances": bu,
        "loyalty_check": ly,
        "will_return": wr,
        "future_outcome": fo,
        "hidden_red_flags": rf,
        "kundli_p1": k1_raw,
        "kundli_p2": k2_raw,
        "reader_context": {
            "primary_gender_inferred": rd,
            "primary_gender_raw": (p1.get("gender") or "").strip() or None,
            "loyalty_reader_nudge_note": "Small score tilt validates primary profile when chart clean.",
            "will_return_note": "Prior assumes most exes do not return unless reunion yogas are strong.",
        },
        "couple_signals": {
            "combined_affliction": couple_sig.combined_affliction,
            "synastry_notes": couple_sig.synastry_notes,
            "moon_mismatch": couple_sig.moon_mismatch,
        },
    }
    return enrich_bundle_for_pdf(base)
