"""
Honest Love Reality engines — deterministic, affliction-heavy scoring.
Every chapter: score/100, risk_level, emotional_summary, reasons.
"""
from __future__ import annotations

from typing import Any

from kundli_engine import calculate_kundli

from vedic.love_reality import reader_context
from vedic.love_reality.relationship_signals import CoupleSignals, PersonSignals, analyze_couple
from vedic.love_reality.scoring_core import (
    KundliReader,
    clamp,
    current_jupiter_sign,
    d9_cancels_debil,
    dasha_lords_inimical,
    future_confidence,
    jupiter_transit_protects,
    level_future,
    level_loyalty,
    level_return,
    risk_band_high_is_bad,
    risk_band_high_is_good,
    scaled_penalty,
)


def _load_couple(p1: dict, p2: dict) -> tuple[KundliReader, KundliReader, CoupleSignals]:
    k1 = calculate_kundli({**p1, "name": p1.get("name") or "You"})
    k2 = calculate_kundli({**p2, "name": p2.get("name") or "Partner"})
    r1, r2 = KundliReader(k1), KundliReader(k2)
    return r1, r2, analyze_couple(r1, r2)


def _cap_by_affliction(score: int, sig: CoupleSignals, harsh_cap: int, moderate_cap: int) -> int:
    capped = score
    if sig.combined_affliction >= 55:
        capped = min(score, harsh_cap)
    elif sig.combined_affliction >= 35:
        capped = min(score, moderate_cap)
    return max(0, capped)


def _breakup_person_pressure(person: PersonSignals) -> float:
    """Per-chart breakup pressure — capped so two afflicted charts do not auto-sum to 100."""
    pts = 0.0
    if person.seventh_lord_dusthana:
        pts += 12
    if person.seventh_lord_debil:
        pts += 8
    if person.saturn_on_7th:
        pts += 9
    if person.mars_on_7th:
        pts += 7
    if person.rahu_on_7th_axis:
        pts += 8
    if person.venus_debil or person.moon_debil:
        pts += 6
    if person.third_person_risk:
        pts += 7
    if person.ketu_detachment:
        pts += 5
    if person.separation_yoga:
        pts += 4
    return min(pts, 28.0)


def _compute_breakup_score(sig: CoupleSignals) -> int:
    # Base ~low-moderate; two partners add capped pressure (not full double-stack to 100).
    score = 16.0 + _breakup_person_pressure(sig.p1) + _breakup_person_pressure(sig.p2)
    if sig.combined_affliction >= 55:
        score += 10
    elif sig.combined_affliction >= 40:
        score += 6
    elif sig.combined_affliction >= 25:
        score += 3
    return clamp(score)


_LOVE_COMPAT_BASE = 52
_LOVE_COMPAT_FLOOR = 15


def _partner_venus_strong(partner: PersonSignals, reader: KundliReader) -> bool:
    """Partner Venus exalted/strong — softens other's debilitated Venus penalty."""
    if partner.venus_d9_exalted:
        return True
    venus = reader.planet("Venus")
    if venus and reader.dignity("Venus", reader.sidx(venus["sign"])) >= 2:
        return True
    return False


def _venus_debil_penalty(
    person: PersonSignals, reader: KundliReader, partner: PersonSignals, partner_reader: KundliReader,
) -> tuple[float, str]:
    if not person.venus_debil:
        return 0.0, ""
    if d9_cancels_debil(reader, "Venus"):
        return -5.0, "Neech-bhang in Navamsa softens Venus debilitation"
    if _partner_venus_strong(partner, partner_reader):
        return -8.0, "Partner Venus strong — partial offset to debilitated Venus"
    return -14.0, "Love nature unstable under stress"


def _compute_love_compatibility_score(
    r1: KundliReader, r2: KundliReader, sig: CoupleSignals,
) -> tuple[int, int, list[dict[str, Any]]]:
    """
    Ordered pipeline: base → all bonuses → all penalties → floor → honesty cap.
    """
    ledger: list[dict[str, Any]] = [
        {
            "label": "Base compatibility anchor",
            "delta": None,
            "note": "Starting value 52 before chart adjustments",
            "base": _LOVE_COMPAT_BASE,
        },
    ]
    bonuses: list[tuple[str, float, str]] = []
    penalties: list[tuple[str, float, str]] = []

    if not sig.p1.separation_yoga and not sig.p2.separation_yoga:
        bonuses.append(("No active separation yoga", 5.0, "Timing less hostile to staying together"))

    person_triples = (
        (sig.p1, r1, sig.p2, r2),
        (sig.p2, r2, sig.p1, r1),
    )
    for person, reader, partner, partner_reader in person_triples:
        if person.reconnection_yoga and not person.separation_yoga:
            bonuses.append((f"{person.name}: Reconnection yoga", 6.0, "Emotional reopening capacity"))
        if not person.fifth_lord_weak and not person.venus_debil:
            bonuses.append((
                f"{person.name}: 5th lord support", 4.0, "Romance spark can hold under pressure",
            ))

    for person, reader, partner, partner_reader in person_triples:
        pen, note = _venus_debil_penalty(person, reader, partner, partner_reader)
        if pen:
            penalties.append((f"{person.name}: Venus debilitated", pen, note))
        elif person.venus_d9_weak:
            penalties.append((
                f"{person.name}: Navamsa Venus weak", -6.0, "Inner commitment layer fragile",
            ))
        if person.moon_debil or person.moon_afflicted:
            moon_w = (
                1.0
                if person.moon_debil
                else person.moon_afflicted_orb_weight
            )
            moon_pen = scaled_penalty(-11.0, moon_w)
            moon_note = "Emotional reactions unpredictable"
            if person.moon_afflicted and moon_w < 1.0:
                moon_note += " (wide orb — partial weight)"
            penalties.append((
                f"{person.name}: Moon afflicted", moon_pen, moon_note,
            ))
        if person.seventh_lord_dusthana or person.seventh_lord_debil:
            penalties.append((
                f"{person.name}: 7th lord weak", -12.0, "Partnership structure strained",
            ))
        if person.saturn_on_7th:
            sat_pen = scaled_penalty(-8.0, person.saturn_on_7th_orb_weight)
            sat_note = "Distance and delay on partnership axis"
            if person.saturn_on_7th_orb_weight < 1.0:
                sat_note += " (sign-aspect only — half weight)"
            penalties.append((
                f"{person.name}: Saturn on 7th", sat_pen, sat_note,
            ))
        if person.venus_dual_flip_risk or person.moon_dual_flip_risk:
            penalties.append((
                f"{person.name}: Love intent flip risk", -5.0,
                "Dual sign under affliction — affection intent can flip quickly",
            ))
        if person.mercury_debil:
            penalties.append((
                f"{person.name}: Mercury debilitated", -5.0, "Communication clarity drops under stress",
            ))
        if person.mercury_afflicted or person.mercury_combust:
            penalties.append((
                f"{person.name}: Mercury afflicted", -4.0, "Mixed signals / hard to read intent",
            ))

    if sig.moon_mismatch:
        penalties.append(("Moon–Moon rhythm clash", -7.0, "One holds in, the other pushes out"))
    if sig.cross_rahu_venus:
        rahu_pen = scaled_penalty(-9.0, sig.cross_rahu_venus_orb_weight)
        rahu_note = "Obsession / loyalty blur between charts"
        if sig.cross_rahu_venus_orb_weight < 1.0:
            rahu_note += " (wide same-sign orb — half weight)"
        penalties.append(("Rahu on partner Venus", rahu_pen, rahu_note))

    score = float(_LOVE_COMPAT_BASE)
    for label, delta, note in bonuses:
        score += delta
        ledger.append({
            "label": label,
            "delta": int(delta) if delta == int(delta) else delta,
            "note": note,
            "phase": "bonus",
        })
    for label, delta, note in penalties:
        score += delta
        ledger.append({
            "label": label,
            "delta": int(delta) if delta == int(delta) else delta,
            "note": note,
            "phase": "penalty",
        })

    if score < _LOVE_COMPAT_FLOOR:
        ledger.append({
            "label": "Compatibility floor",
            "delta": _LOVE_COMPAT_FLOOR - score,
            "note": f"Score raised to minimum {_LOVE_COMPAT_FLOOR} — bond still has workable baseline",
            "phase": "floor",
        })
        score = float(_LOVE_COMPAT_FLOOR)

    raw_score = clamp(score)
    score_i = _cap_by_affliction(raw_score, sig, harsh_cap=48, moderate_cap=58)
    if score_i < raw_score:
        ledger.append({
            "label": "Affliction cap applied",
            "delta": score_i - raw_score,
            "note": f"Combined affliction {sig.combined_affliction} — score capped for honesty",
            "phase": "cap",
        })
    return score_i, raw_score, ledger


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
    if p1.mercury_debil or p2.mercury_debil:
        communication -= 8
    if p1.mercury_afflicted or p2.mercury_afflicted or p1.mercury_combust or p2.mercury_combust:
        communication -= 6

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

    score_i, raw_score, ledger = _compute_love_compatibility_score(r1, r2, sig)
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
        "communication": (
            "weak"
            if sig.moon_mismatch
            or any(
                p.mercury_debil or p.mercury_afflicted or p.mercury_combust
                for p in (sig.p1, sig.p2)
            )
            else "medium"
        ),
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

    for person in (sig.p1, sig.p2):
        if person.seventh_lord_dusthana:
            reasons.append("7th lord in dusthana — bond survives emotionally but not practically.")
        if person.saturn_on_7th:
            reasons.append("Saturn on 7th axis — emotional distance and break timing active.")
        if person.mars_on_7th:
            reasons.append("Mars on 7th — fights escalate into rupture.")
        if person.rahu_on_7th_axis:
            reasons.append("Rahu on 7th — confusion, obsession, unstable commitment.")
        if person.venus_debil or person.moon_debil:
            reasons.append("Venus/Moon weakness — loyalty and affection fracture under stress.")
        if person.third_person_risk:
            reasons.append("Third-person interference risk visible in chart.")
        if person.ketu_detachment:
            reasons.append("Ketu detachment — ghosting / sudden emotional exit pattern.")

    if sig.combined_affliction >= 50:
        reasons.append("Relationship carries strong breakup signatures across both charts.")

    score_i = _compute_breakup_score(sig)
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
        pen += 9 if person.venus_d9_exalted else 18
    if person.moon_debil:
        pen += 7 if person.moon_d9_exalted else 14
    elif person.moon_afflicted or person.moon_rahu_afflicted:
        if not (person.saturn_moon_duty_bound and not person.moon_rahu_afflicted):
            pen += 14
    if person.moon_in_8th:
        pen += 14
    if person.moon_d9_debil:
        pen += 12
    if person.venus_mars_conjunct_tight:
        pen += 16
    if person.rahu_on_7th_axis or person.third_person_risk:
        pen += 14
    if person.emotional_instability:
        pen += 8
    if person.seventh_lord_dusthana or person.seventh_lord_debil:
        pen += 10
    if person.saturn_on_7th_not_lord:
        pen += 6
    return pen


def _person_loyalty_extra_rules(person) -> tuple[float, list[str]]:
    """New loyalty-specific affliction queue (serial rules 1, 3–5)."""
    delta = 0.0
    notes: list[str] = []
    if person.moon_dual_flip_risk:
        delta -= 8
        notes.append(f"{person.name}: Moon in dual sign under affliction — double-minded flip risk.")
    if person.venus_dual_flip_risk:
        delta -= 8
        notes.append(f"{person.name}: Venus in dual sign under affliction — love intent can flip.")
    if person.fifth_lord_in_twelfth or person.twelfth_lord_in_fifth:
        delta -= 10
        notes.append(
            f"{person.name}: 5th–12th lord link — secret desire lines can erode loyalty."
        )
    if person.d9_seventh_lord_weak:
        delta -= 12
        notes.append(
            f"{person.name}: Navamsa 7th lord debilitated/dusthana — inner commitment weak over time."
        )
    if person.lagna_lord_weak_or_combust:
        delta -= 7
        notes.append(
            f"{person.name}: Lagna lord weak/combust — external influence can sway commitment."
        )
    return delta, notes


def _person_loyalty_bonus(person) -> float:
    bonus = _person_loyalty_safe_bonus(person)
    if person.saturn_on_7th_as_lord:
        bonus += 5
    return bonus


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


def _compute_person_loyalty_score(person) -> int:
    score = 48.0
    score -= _person_loyalty_penalty(person)
    extra, _ = _person_loyalty_extra_rules(person)
    score += extra
    score += _person_loyalty_bonus(person)
    return clamp(score)


def _loyalty_venus_tie_rank(person) -> tuple[int, float]:
    """Higher rank = worse Venus state for loyalty tie-break."""
    rank = 0
    if person.venus_combust:
        rank += 3
    if person.venus_debil:
        rank += 2
    if person.venus_afflicted:
        rank += 1
    deg = person.venus_degree if person.venus_degree is not None else 0.0
    return rank, deg


def _loyalty_tie_breaker(
    p1_score: int,
    p2_score: int,
    sig,
) -> dict[str, Any] | None:
    level1 = level_loyalty(p1_score)
    level2 = level_loyalty(p2_score)
    if p1_score != p2_score or level1 != level2:
        return None
    if level1 not in ("moderate", "unstable"):
        return None
    r1 = _loyalty_venus_tie_rank(sig.p1)
    r2 = _loyalty_venus_tie_rank(sig.p2)
    if r1 == r2:
        return None
    lower = "p1" if r1 > r2 else "p2"
    worse_name = sig.p1.name if lower == "p1" else sig.p2.name
    return {
        "applied": True,
        "lower_side": lower,
        "shared_score": p1_score,
        "shared_level": level1,
        "note": (
            f"Tie at {level1} ({p1_score}/100) — {worse_name}'s Venus state "
            f"(combust/afflicted/degree) positions loyalty baseline lower."
        ),
        "p1_venus_rank": r1[0],
        "p2_venus_rank": r2[0],
        "p1_venus_degree": r1[1],
        "p2_venus_degree": r2[1],
    }


def run_loyalty_check(p1: dict, p2: dict) -> dict[str, Any]:
    r1, r2, sig = _load_couple(p1, p2)
    reasons: list[str] = []

    score = 48.0
    duty_bound_any = False
    for person in (sig.p1, sig.p2):
        pen = _person_loyalty_penalty(person)
        if pen > 0:
            score -= pen
        extra, extra_notes = _person_loyalty_extra_rules(person)
        score += extra
        reasons.extend(extra_notes)
        score += _person_loyalty_bonus(person)
        if person.saturn_moon_duty_bound:
            duty_bound_any = True
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
        if person.venus_mars_conjunct_tight:
            narrative_locks.append(
                f"{person.name}: Venus-Mars (≤10°) — impulsive attraction; NOT a loyalty guarantee."
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

    if duty_bound_any and score_i >= 45:
        summary = (
            "Duty-bound loyalty pattern visible (Saturn–Moon) — may endure pain in silence "
            "without a cheating signature."
        )
        if behavior == "dual-nature":
            behavior = "emotionally unstable"

    p1_person_score = _compute_person_loyalty_score(sig.p1)
    p2_person_score = _compute_person_loyalty_score(sig.p2)
    tie_breaker = _loyalty_tie_breaker(p1_person_score, p2_person_score, sig)

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
            "venus": "weak" if any(
                p.venus_debil or p.venus_mars_conjunct_tight or p.venus_dual_flip_risk
                for p in (sig.p1, sig.p2)
            ) else "mixed",
            "moon": "weak" if any(
                p.moon_afflicted or p.moon_in_8th or p.moon_d9_debil or p.moon_dual_flip_risk
                for p in (sig.p1, sig.p2)
            ) else "medium",
            "7th_house": "afflicted" if any(
                p.saturn_on_7th_not_lord or p.mars_on_7th for p in (sig.p1, sig.p2)
            ) else "stable",
            "rahu": "active" if sig.cross_rahu_venus or sig.p1.rahu_on_7th_axis else "quiet",
        },
        "reasons": unique[:14],
        "is_duty_bound_loyal": duty_bound_any,
        "p1_loyalty_score": p1_person_score,
        "p2_loyalty_score": p2_person_score,
        "p1_loyalty_level": level_loyalty(p1_person_score),
        "p2_loyalty_level": level_loyalty(p2_person_score),
        "per_person": {
            "p1": {
                "name": sig.p1.name,
                "score": p1_person_score,
                "loyalty_level": level_loyalty(p1_person_score),
                "is_duty_bound_loyal": sig.p1.saturn_moon_duty_bound,
                "venus_degree": sig.p1.venus_degree,
                "venus_combust": sig.p1.venus_combust,
                "venus_afflicted": sig.p1.venus_afflicted,
            },
            "p2": {
                "name": sig.p2.name,
                "score": p2_person_score,
                "loyalty_level": level_loyalty(p2_person_score),
                "is_duty_bound_loyal": sig.p2.saturn_moon_duty_bound,
                "venus_degree": sig.p2.venus_degree,
                "venus_combust": sig.p2.venus_combust,
                "venus_afflicted": sig.p2.venus_afflicted,
            },
        },
        "loyalty_tie_breaker": tie_breaker,
        "breakdown": {
            "combined_affliction": sig.combined_affliction,
            "p1_person_score": p1_person_score,
            "p2_person_score": p2_person_score,
            "p1_loyalty_risk": sig.p1.loyalty_risk_high,
            "p2_loyalty_risk": sig.p2.loyalty_risk_high,
            "p1_duty_bound": sig.p1.saturn_moon_duty_bound,
            "p2_duty_bound": sig.p2.saturn_moon_duty_bound,
        },
        "chart_proof": build_chart_proof(r1, r2, sig),
        "engine_version": "loyalty_compare_v2",
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
    total_afflictions = 0

    score = 48.0
    if sig.p1.seventh_lord_dusthana and sig.p2.seventh_lord_dusthana:
        score -= 15
        total_afflictions += 1
        reasons.append("Both charts show weak 7th-lord foundation — long-term drift likely.")
    elif sig.p1.seventh_lord_dusthana or sig.p2.seventh_lord_dusthana:
        score -= 8
        total_afflictions += 1

    if sig.p1.venus_debil and sig.p2.venus_debil:
        venus_pen = 6 if (
            d9_cancels_debil(r1, "Venus") or d9_cancels_debil(r2, "Venus")
        ) else 12
        score -= venus_pen
        total_afflictions += 1
        if venus_pen == 6:
            reasons.append(
                "Both Venus debilitated in D1 — Navamsa neech-bhang softens long-term love drain."
            )

    if sig.moon_mismatch:
        score -= 8
        total_afflictions += 1

    if sig.p1.reconnection_yoga or sig.p2.reconnection_yoga:
        score += 8
    if not sig.p1.separation_yoga and not sig.p2.separation_yoga:
        score += 6

    jup_sign = current_jupiter_sign()
    jupiter_buffer = jupiter_transit_protects(r1, r2, jup_sign)
    if jupiter_buffer:
        score += 10
        reasons.append(
            "Transiting Jupiter aspects Lagna, 5th, or 7th axis — healing buffer against separation."
        )

    score_i = _cap_by_affliction(clamp(score), sig, harsh_cap=40, moderate_cap=52)
    if score_i < 0:
        score_i = 0
    score_i = clamp(score_i)
    outcome = level_future(score_i)

    dasha_down = dasha_lords_inimical(r1, r2)
    breakup_score = _compute_breakup_score(sig)
    breakup_high = breakup_score > 55
    strained_band = 28 <= score_i <= 41
    timeline_warning: str | None = None
    if strained_band and breakup_high:
        timeline_warning = "Current timeline validation high risk zone mein chal rahi hai."
        reasons.insert(0, timeline_warning)

    if score_i >= 60:
        summary = "Trajectory can grow if both stop repeating the same emotional loop."
        phase = "Repair window open"
    elif score_i >= 42:
        summary = "Future is mixed — attachment continues while peace stays uneven."
        phase = "Uncertain bonding phase"
    else:
        summary = "Charts lean toward emotional exhaustion — long-term stability is not assured."
        phase = "Closure or distance phase strengthening"

    if dasha_down:
        next_shift = "Down trend — running dasha lords in Shashtashtak / Dwidwadasa stress window"
        trend_3m = "down"
        trend_6m = "down"
    else:
        next_shift = "3–6 months — dasha/transit will tilt the emotional tone"
        trend_3m = "mixed"
        trend_6m = "up" if score_i >= 55 else "down"

    from vedic.love_reality.chart_proof import build_chart_proof

    return {
        "future_score": score_i,
        "score": score_i,
        "risk_level": risk_band_high_is_good(score_i),
        "outcome": outcome,
        "confidence": future_confidence(total_afflictions),
        "current_phase": phase,
        "next_shift": next_shift,
        "next_shift_trend": "down" if dasha_down else "mixed",
        "timeline_flow": [
            {"period": "Now", "trend": "mixed" if score_i >= 42 else "down", "reason": summary},
            {
                "period": "3 months",
                "trend": trend_3m,
                "reason": (
                    "Running dasha lords clash — warmth likely fades"
                    if dasha_down
                    else "Venus/Moon periods decide warmth vs withdrawal"
                ),
            },
            {"period": "6+ months", "trend": trend_6m, "reason": outcome},
        ],
        "emotional_summary": summary,
        "factors": {
            "combined_affliction": str(sig.combined_affliction),
            "jupiter_transit_buffer": str(jupiter_buffer),
            "dasha_lords_inimical": str(dasha_down),
            "total_afflictions": str(total_afflictions),
        },
        "reasons": (reasons + sig.synastry_notes)[:12],
        "breakdown": {
            "combined_affliction": sig.combined_affliction,
            "total_afflictions": total_afflictions,
            "breakup_cross_score": breakup_score,
        },
        "timeline_validation_warning": timeline_warning,
        "generated_at": None,
        "chart_proof": build_chart_proof(r1, r2, sig),
        "engine_version": "future_outcome_v2",
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
