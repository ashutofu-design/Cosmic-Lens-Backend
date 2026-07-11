"""Property timing engine v1 — 4H + Mars/Shani karakas; ghar/registry/dispute windows."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

# Classical property: 4H axis + Mangal (bhumi/construction) + Shani (immovable/delay)
_PROPERTY_CFG = DomainTimingConfig(
    domain="property",
    engine_version="property_timing_v1.1",
    concern_houses=[
        (4, 20.0, "4H property axis (Mars/Shani)"),
        (11, 10.0, "11H property gain/fulfilment"),
    ],
    leak_houses=[
        (8, 8.0, "8H sudden property obstacle"),
        (12, 10.0, "12H legal/expense drain on property"),
    ],
    occupant_bumps=[
        (4, 12.0, "occupies 4H (home/property)"),
    ],
    aspect_target_houses=[
        (4, 8.0, "aspects 4H (property activation)"),
    ],
    karakas=[
        ("Mars", 14.0, "Mangal — bhumi, plot, construction karaka"),
        ("Saturn", 12.0, "Shani — immovable property, structure, delay karaka"),
    ],
    kp_cusps=[4],
    promote_tags=("4L", "4H", "Mars", "Saturn", "Mangal", "Shani", "occupies 4H"),
    obstruct_tags=("8L", "12L", "8H", "12H"),
    double_transit_houses=[4],
    promised_label="PROPERTY_WINDOW_OPEN",
    favourable_label="PROPERTY_WINDOW_MODERATE",
    caution_label="PROPERTY_DELAY",
    defer_label="PROPERTY_LOW_PROBABILITY",
    brand_safety=[
        "Sirf probability window — exact registry date / price / address guarantee nahi.",
        "Title, RERA, loan — practical verification zaroori.",
    ],
    llm_directives=[
        "NO_EXACT_PRICE",
        "NO_LEGAL_OUTCOME_CERTAINTY",
    ],
)

_RELEVANT_FACTOR = re.compile(
    r"(?ix)4H|4L|11H|11L|mars|saturn|mangal|shani|property|home|ghar|"
    r"registry|construction|bhumi|immovable|karaka",
)

_BUCKET_RX = [
    ("dispute", re.compile(
        r"(?ix)\b(vivaad|vivad|dispute|court\s+case|litigation|suljhega|suljhegi|"
        r"faisla|kabza|encroachment|stay\s+order|injunction|illegal\s+kabza|"
        r"property\s+fight|land\s+case|challenge\s+kar)\b",
    )),
    ("inheritance", re.compile(
        r"(?ix)\b(paitrik|pustaini|ancestral|virasat|inherit|inheritance|"
        r"vasiyat|will\b|hissa\s+(?:kab|milega|milegi|percent)|pitri\s+dhan|"
        r"parental\s+property|dowry\s+me)\b",
    )),
    ("loan", re.compile(
        r"(?ix)\b(home\s+loan|house\s+loan|property\s+loan|bank\s+loan|"
        r"loan\s+sanction|emi|griha\s*rin|mortgage)\b",
    )),
    ("registry", re.compile(r"(?ix)\b(registry|griha[\s-]?pravesh|registration)\b")),
    ("possession", re.compile(
        r"(?ix)\b(possession|handover|builder\s+possession|chaabi|chabi)\b",
    )),
    ("construction", re.compile(
        r"(?ix)\b(construction|build|ban[\s-]?(?:ega|egi|wana|wane)|makaan\s+ban|"
        r"renovation|repairing)\b",
    )),
    ("sell", re.compile(
        r"(?ix)\b(sell|bech|bechega|bechegi|bikega|bikegi|sale|grahak|buyer|"
        r"bik\s+nahi|liquidate|bayaana|agreement\s+sign)\b",
    )),
    ("buy", re.compile(
        r"(?ix)\b(buy|purchase|kharid|khareed|lena|ghar\s+len|makaan\s+len|"
        r"flat\s+len|down[\s-]?payment|token\s+money|dda|mhada|awas\s+yojna|"
        r"housing\s+scheme|invest)\b",
    )),
]


def classify_property_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if rx.search(q):
            return name
    return "buy"


def _mars_saturn_snapshot(kundli: dict) -> list[str]:
    lines: list[str] = []
    for p in kundli.get("planets") or []:
        if not isinstance(p, dict) or p.get("name") not in ("Mars", "Saturn"):
            continue
        name = p["name"]
        label = "Mangal" if name == "Mars" else "Shani"
        sign = p.get("sign") or "?"
        house = p.get("house")
        house_s = f"{house}H" if isinstance(house, int) else "?H"
        lines.append(f"{label} ({name}): {sign} · {house_s}")
    return lines


def _filter_property_factors(factors: list) -> list[str]:
    out: list[str] = []
    for f in factors or []:
        if isinstance(f, str) and _RELEVANT_FACTOR.search(f):
            out.append(f)
    return out[:5]


def _norm_lord(name: Any) -> str:
    return str(name or "").strip().title()


def _lords_in_window(w: dict) -> set[str]:
    return {
        _norm_lord(w.get("md")),
        _norm_lord(w.get("ad")),
        _norm_lord(w.get("pd")),
    } - {""}


def _window_has_planet(w: dict, planet: str) -> bool:
    return bool(planet) and _norm_lord(planet) in _lords_in_window(w)


def _period_score(p: dict) -> float:
    return float(p.get("activation_score") or p.get("score") or 0)


def _reconcile_property_answer_window(out: dict) -> dict:
    """Rank periods by activation; answer = best Mars/Shani karaka window, not weak running PD."""
    periods = [dict(p) for p in (out.get("timing_periods") or []) if isinstance(p, dict)]
    if periods:
        periods.sort(
            key=lambda p: (_period_score(p), float(p.get("score") or 0)),
            reverse=True,
        )
        for i, p in enumerate(periods[:3]):
            p["rank"] = i + 1
        out["timing_periods"] = periods

    current = (
        dict(out.get("current_window") or {})
        if isinstance(out.get("current_window"), dict)
        else {}
    )
    min_act = float(out.get("min_current_activation") or 9.0)
    running_act = float(
        out.get("current_running_activation_score")
        or current.get("activation_score")
        or 0
    )
    running_now = bool(
        current.get("is_active_now")
        or str(out.get("timing_source") or "") == "current_dasha_active"
    )

    primary_sig = (
        out.get("primary_significator")
        if isinstance(out.get("primary_significator"), dict)
        else {}
    )
    sig_name = _norm_lord(primary_sig.get("name"))

    verdict = str(out.get("verdict") or "")
    weak = "LOW_PROBABILITY" in verdict.upper() or str(out.get("band") or "") == "WEAK"

    best = periods[0] if periods else None
    best_score = _period_score(best) if best else 0.0

    sig_periods = [p for p in periods if sig_name and _window_has_planet(p, sig_name)]
    best_sig = max(sig_periods, key=_period_score) if sig_periods else None
    best_sig_score = _period_score(best_sig) if best_sig else 0.0
    current_has_sig = bool(sig_name and current and _window_has_planet(current, sig_name))

    answer: dict = {}
    timing_source = str(out.get("timing_source") or "")
    current_supports = bool(out.get("current_supports"))

    if (
        running_now
        and running_act >= min_act
        and current_has_sig
        and not weak
        and running_act >= best_score
    ):
        answer = dict(current)
        timing_source = "current_dasha_active"
        current_supports = True
    elif best_sig and (weak or not current_has_sig or best_sig_score > running_act):
        answer = dict(best_sig)
        timing_source = "next_dasha_scan"
        current_supports = running_act >= min_act if running_now else False
        factors = list(out.get("factors") or [])
        factors.insert(
            0,
            (
                f"PROPERTY_ANSWER=rank #{answer.get('rank')} — TOP karaka {sig_name} "
                f"via {answer.get('ad')}/{answer.get('pd')} "
                f"(running PD {_norm_lord(current.get('pd'))} weak for property buy)"
            ),
        )
        out["factors"] = factors[:14]
    elif best:
        answer = dict(best)
        if answer.get("is_active_now") and running_now:
            timing_source = "current_dasha_active"
            current_supports = True
        else:
            timing_source = "next_dasha_scan"
            current_supports = running_act >= min_act if running_now else False
    elif current:
        answer = dict(current)
    else:
        timing_source = "no_qualified_window"
        current_supports = False

    if answer:
        if not answer.get("lords"):
            answer["lords"] = "/".join(
                x
                for x in (
                    _norm_lord(answer.get("md")),
                    _norm_lord(answer.get("ad")),
                    _norm_lord(answer.get("pd")),
                )
                if x
            )
        out["answer_window"] = answer
        out["recommended_window"] = answer
        if answer.get("start_iso") and answer.get("end_iso"):
            out["primary_window"] = f"{answer['start_iso']}→{answer['end_iso']}"

    out["timing_source"] = timing_source
    out["current_supports"] = current_supports
    return out


def compute_property_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_property_timing_bucket(question)
    out = compute_generic_timing_window(
        kundli, _PROPERTY_CFG, intel, kp, birth, question, b,
    )
    karakas = _mars_saturn_snapshot(kundli)
    if karakas:
        out["property_karakas"] = karakas
    raw_factors = list(out.get("factors") or [])
    filtered = _filter_property_factors(raw_factors)
    if filtered:
        out["factors"] = filtered
    elif karakas:
        out["factors"] = karakas
    try:
        from event_timing.property.bcp_property_ages import (
            compute_bcp_property_ages,
            resolve_property_lagna_si,
        )

        lagna_si = resolve_property_lagna_si(kundli)
        user_age: Optional[int] = None
        try:
            from ask_career.timing_registry import resolve_user_age  # type: ignore

            user_age = resolve_user_age(question, birth, kundli)
        except Exception:
            pass
        if user_age is not None:
            out["user_age"] = user_age
        if lagna_si is not None:
            bcp = compute_bcp_property_ages(kundli, lagna_si, user_age=user_age)
            out["bcp_property_ages"] = bcp
            bcp_lines = []
            try:
                from event_timing.property.bcp_property_ages import bcp_property_admin_lines

                bcp_lines = bcp_property_admin_lines(bcp)
            except Exception:
                pass
            if bcp_lines:
                factors = list(out.get("factors") or [])
                factors[:0] = bcp_lines[:3]
                out["factors"] = factors[:16]
    except Exception as exc:
        factors = list(out.get("factors") or [])
        factors.append(f"bcp_property_ages skipped: {exc}")
        out["factors"] = factors[:16]
    extra: list[str] = []
    if b == "dispute":
        extra.append("Property vivaad — court outcome guarantee nahi; legal + mediation parallel rakho.")
    elif b == "inheritance":
        extra.append("Ancestral/paitrik hissa — family settlement + legal heir certificate verify karo.")
    if extra:
        warnings = list(out.get("brand_safety_warnings") or [])
        warnings.extend(extra)
        out["brand_safety_warnings"] = warnings
    out = _reconcile_property_answer_window(out)
    try:
        from event_timing.property.property_practicality import apply_property_practicality

        out = apply_property_practicality(out, kundli, birth, question)
    except Exception as exc:
        factors = list(out.get("factors") or [])
        factors.append(f"property_practicality skipped: {exc}")
        out["factors"] = factors[:16]
    try:
        from event_timing._shared.step_audit import attach_timing_pipeline_audit

        out = attach_timing_pipeline_audit(out, "property")
    except Exception:
        pass
    return out


def format_property_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "=== PROPERTY TIMING ENGINE v1 (LOCKED) — 4H · Mangal · Shani ===",
        f"Bucket: {v.get('bucket')} · Verdict: {v.get('verdict')} · Band: {v.get('band')}",
    ]
    for k in (v.get("property_karakas") or [])[:2]:
        lines.append(f"  KARAK: {k}")
    bcp = v.get("bcp_property_ages") if isinstance(v.get("bcp_property_ages"), dict) else {}
    if bcp:
        lord = bcp.get("fourth_lord") or "?"
        sit = bcp.get("fourth_lord_house")
        asp = bcp.get("d1_aspect_houses") or []
        focus = bcp.get("focus_ages") or bcp.get("future_priority_ages") or []
        lines.append(
            f"▸ BCP 4L: {lord} in {sit}H · aspects {','.join(str(h) for h in asp) or '—'}"
        )
        if focus:
            lines.append(
                f"▸ BCP focus ages (4L sit+aspect): {', '.join(str(a) for a in focus[:6])}"
            )
    periods = v.get("timing_periods") or []
    if periods:
        lines.append("▸ THREE RANKED PROPERTY PERIODS (engine locked):")
        for p in periods[:3]:
            if not isinstance(p, dict):
                continue
            rank = p.get("rank") or "?"
            lords = p.get("lords") or "/".join(
                x for x in (p.get("md"), p.get("ad"), p.get("pd")) if x
            )
            lines.append(
                f"  #{rank} {p.get('start_iso')}→{p.get('end_iso')} "
                f"MD/AD/PD={lords} act={p.get('activation_score')}"
            )
        lines.append(
            ">>> DEFAULT ANSWER: cite rank #1 ONLY. "
            "User 'dusra/2nd/agla window' → rank #2; 'teesra/3rd' → rank #3."
        )
    ans = v.get("answer_window") if isinstance(v.get("answer_window"), dict) else {}
    cw = ans if (ans.get("start_iso") or ans.get("md")) else (v.get("current_window") or {})
    if v.get("timing_source") == "no_qualified_window":
        lines.append(
            ">>> NO QUALIFIED WINDOW — activation below threshold. "
            "Do NOT cite sub-threshold dasha periods."
        )
    elif not periods and cw.get("start_iso") and cw.get("end_iso"):
        active = (
            "ACTIVE NOW"
            if cw.get("is_active_now") or v.get("timing_source") == "current_dasha_active"
            else "UPCOMING"
        )
        lords = cw.get("lords") or "/".join(
            x for x in (cw.get("md"), cw.get("ad"), cw.get("pd")) if x
        )
        lines.append(
            f"▸ PRIMARY window ({active}): {cw.get('start_iso')} → {cw.get('end_iso')} "
            f"MD/AD/PD={lords or '?'}"
        )
    elif periods and cw.get("start_iso"):
        lords = cw.get("lords") or "/".join(
            x for x in (cw.get("md"), cw.get("ad"), cw.get("pd")) if x
        )
        active = (
            "ACTIVE NOW"
            if cw.get("is_active_now") or v.get("timing_source") == "current_dasha_active"
            else "UPCOMING"
        )
        lines.append(
            f">>> NARRATE rank #1 ({active}) — MD/AD/PD {lords or '?'} "
            f"({cw.get('start_iso')}→{cw.get('end_iso')})."
        )
        if v.get("timing_source") == "next_dasha_scan" and v.get("current_supports"):
            run = v.get("dasha_running_now") if isinstance(v.get("dasha_running_now"), dict) else {}
            lines.append(
                f">>> NOTE: abhi running {run.get('lords') or 'dasha'} — "
                "property buy ke liye rank #1 upcoming window cite karo; "
                "current Saturn-only PD ko best timing mat bolo."
            )
    for f in (v.get("factors") or [])[:4]:
        if isinstance(f, str) and not f.startswith("STEP"):
            lines.append(f"  • {f}")
    dt = v.get("double_transit") or {}
    if dt.get("active") and dt.get("verdict"):
        lines.append(f"▸ Shani/Guru 4H transit: {dt.get('verdict')}")
    for g in (v.get("brand_safety_warnings") or [])[:3]:
        lines.append(f"  GUARD: {g}")
    prac = v.get("practicality") if isinstance(v.get("practicality"), dict) else {}
    if prac:
        mode = prac.get("purchase_timing_mode") or v.get("purchase_timing_mode") or "?"
        label = prac.get("buy_timing_label") or v.get("buy_timing_label") or "?"
        months = prac.get("months_until_buy_window")
        months_txt = f" · ~{months} mahine wait" if months else ""
        lines.append(
            f"▸ BUY TIMING: {str(label).upper()} ({mode})"
            f"{months_txt} · afford={prac.get('affordability', '?')} · "
            f"age={prac.get('user_age', '?')}/{prac.get('min_purchase_age', '?')}"
        )
    if v.get("strategy"):
        lines.append(f"▸ DIRECTIVE: {v['strategy']}")
    lines.append(
        "RULE: 4H + Mars/Shani dasha AND early-buy vs delay practicality — "
        "delay mode mein abhi buy mat bolo; ACT_NOW mein current window cite karo."
    )
    return "\n".join(lines)
