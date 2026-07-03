"""
Career top matches from D1 + D10 blend.

Uses:
  • Planets in D1 10th house (primary, dignity-weighted, dominant occupant first)
  • D10 10th house occupants (profession-chart blend)
  • 10th lord's house placement — secondary themes
  • Empty D1 10th → 10th lord planet jobs
  • Jaimini Amatyakaraka career nudge
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from vedic.life_specifics import DEBIL, EXALT, OWN, SIGNS, SIGN_LORD

# Planet → short career labels
_PLANET_JOBS: Dict[str, Tuple[str, ...]] = {
    "Sun": (
        "Government / Administration",
        "Leadership / Management",
        "Medical / Health leadership",
    ),
    "Moon": (
        "Hospitality / Public-facing roles",
        "Media / Communication",
        "Counseling / Care services",
    ),
    "Mars": (
        "Engineering / Technical",
        "Defense / Police / Security",
        "Real estate / Construction",
    ),
    "Mercury": (
        "Tech / Software",
        "Finance / Banking",
        "Business / Trading",
        "Media / Communication",
        "Education / Teaching",
    ),
    "Jupiter": (
        "Finance / Banking",
        "Education / Teaching",
        "Spiritual / Religious leadership",
        "Law / Advisory",
    ),
    "Venus": (
        "Media / Communication",
        "Creative / Arts",
        "Finance / Luxury trade",
        "Hospitality",
    ),
    "Saturn": (
        "Finance / Banking",
        "Engineering / Manufacturing",
        "Government / Public service",
        "Research / Long-term projects",
    ),
    "Rahu": (
        "Tech / AI",
        "Media / Communication",
        "Business / Trading",
        "Foreign / Import-export",
    ),
    "Ketu": (
        "Spiritual / Research",
        "Education / Healing arts",
        "Tech / Analysis",
    ),
}

_LORD_HOUSE_JOBS: Dict[int, Tuple[str, ...]] = {
    1: ("Leadership / Independent career",),
    2: ("Finance / Banking", "Family business / Accounts"),
    3: ("Media / Communication", "Marketing / Writing"),
    4: ("Education", "Real estate / Property"),
    5: ("Education / Teaching", "Creative / Advisory"),
    6: ("Service sector", "Law / Medical support", "Engineering"),
    7: ("Business / Trading", "Partnership-based work"),
    8: ("Research", "Finance / Insurance", "Technical depth roles"),
    9: ("Education / Teaching", "Spiritual / Religious", "Law / Publishing"),
    10: ("Government / Leadership", "Corporate authority roles"),
    11: ("Finance / Banking", "Tech / Networks", "Large organisations"),
    12: ("Spiritual / Foreign-linked work", "Hospitals / Export"),
}

# Dominant occupant gets full weight; co-occupants diminish.
_OCCUPANT_WEIGHTS = (1.0, 0.72, 0.55, 0.42)
_D10_BLEND_WEIGHT = 26.0
_D1_OCCUPANT_BASE = 40.0
_AMK_BLEND_WEIGHT = 14.0


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _dignity_multiplier(planet: str, sign: str) -> float:
    if not planet or not sign:
        return 1.0
    if sign == EXALT.get(planet):
        return 1.15
    if sign in OWN.get(planet, []):
        return 1.08
    if sign == DEBIL.get(planet):
        return 0.82
    return 1.0


def _occupant_sort_key(p: dict) -> float:
    nm = str(p.get("name") or "")
    sg = str(p.get("sign") or "")
    return _dignity_multiplier(nm, sg)


def _d10_context(kundli: Optional[dict]) -> tuple[List[dict], int]:
    """D10 planets with houses + D10 asc index, or empty."""
    if not kundli:
        return [], 0
    try:
        from vedic.career_inclination_engine import ensure_planet_houses, resolve_asc_idx

        d10 = (kundli.get("divisionalCharts") or {}).get("D10") or {}
        raw = list(d10.get("planets") or [])
        if not raw:
            return [], 0
        asc = resolve_asc_idx({"ascendant": d10.get("ascendant"), **d10})
        return ensure_planet_houses(raw, asc), asc
    except Exception:
        return [], 0


def _add_planet_jobs(
    field_scores: Dict[str, float],
    field_rules: Dict[str, List[str]],
    planet: str,
    sign: str,
    points: float,
    rule: str,
) -> None:
    mult = _dignity_multiplier(planet, sign)
    for job in _PLANET_JOBS.get(planet, ()):
        pts = points * mult
        if not job or pts <= 0:
            continue
        field_scores[job] = field_scores.get(job, 0.0) + pts
        field_rules.setdefault(job, [])
        if rule and rule not in field_rules[job]:
            field_rules[job].append(rule)


def compute_classical_top_careers(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict] = None,
    *,
    top_n: int = 5,
) -> Dict[str, Any]:
    """Return suitable_fields[] for career UI. Never raises."""
    amatyakaraka: Optional[str] = None
    try:
        from karakas import compute_karakas
        from vedic.career_inclination_engine import ensure_planet_houses

        karakas = compute_karakas(planets or [])
        amatyakaraka = karakas.get("AmK") if karakas else None

        normed = ensure_planet_houses(list(planets or []), asc_idx)
        sign_10 = SIGNS[(asc_idx + 9) % 12]
        lord_10 = SIGN_LORD[sign_10]
        occupants_10 = sorted(
            [p for p in normed if int(p.get("house") or 0) == 10 and p.get("name")],
            key=_occupant_sort_key,
            reverse=True,
        )

        l10 = next((p for p in normed if p.get("name") == lord_10), None)
        l10_house = int(l10.get("house") or 0) if l10 else 0
        l10_sign = str(l10.get("sign") or "") if l10 else ""

        field_scores: Dict[str, float] = {}
        field_rules: Dict[str, List[str]] = {}

        # ── D1: planets in 10th (dominant occupant weighted higher) ───────
        if occupants_10:
            for idx, p in enumerate(occupants_10):
                nm = str(p.get("name") or "")
                sg = str(p.get("sign") or "")
                occ_w = _OCCUPANT_WEIGHTS[min(idx, len(_OCCUPANT_WEIGHTS) - 1)]
                _add_planet_jobs(
                    field_scores,
                    field_rules,
                    nm,
                    sg,
                    _D1_OCCUPANT_BASE * occ_w,
                    f"{nm} in 10th house ({sg})" + (" — primary" if idx == 0 else ""),
                )
        else:
            for job in _PLANET_JOBS.get(lord_10, ()):
                pts = 35.0
                field_scores[job] = field_scores.get(job, 0.0) + pts
                field_rules.setdefault(job, [])
                rule = f"10th empty — 10th lord {lord_10} ({sign_10})"
                if rule not in field_rules[job]:
                    field_rules[job].append(rule)

        # ── D10: profession-chart 10th occupants ────────────────────────
        d10_planets, d10_asc = _d10_context(kundli)
        d10_occ = sorted(
            [p for p in d10_planets if int(p.get("house") or 0) == 10 and p.get("name")],
            key=_occupant_sort_key,
            reverse=True,
        )
        for idx, p in enumerate(d10_occ):
            nm = str(p.get("name") or "")
            sg = str(p.get("sign") or "")
            occ_w = _OCCUPANT_WEIGHTS[min(idx, len(_OCCUPANT_WEIGHTS) - 1)]
            _add_planet_jobs(
                field_scores,
                field_rules,
                nm,
                sg,
                _D10_BLEND_WEIGHT * occ_w,
                f"D10: {nm} in 10th ({sg})" + (" — primary" if idx == 0 else ""),
            )

        # ── 10th lord house theme ─────────────────────────────────────────
        if l10_house:
            for job in _LORD_HOUSE_JOBS.get(l10_house, ()):
                pts = 18.0
                field_scores[job] = field_scores.get(job, 0.0) + pts
                field_rules.setdefault(job, [])
                rule = f"10th lord {lord_10} in {l10_house}th house"
                if rule not in field_rules[job]:
                    field_rules[job].append(rule)

        # ── Amatyakaraka career karaka ────────────────────────────────────
        if amatyakaraka:
            amk_p = next((p for p in normed if p.get("name") == amatyakaraka), None)
            amk_sign = str(amk_p.get("sign") or "") if amk_p else ""
            _add_planet_jobs(
                field_scores,
                field_rules,
                amatyakaraka,
                amk_sign,
                _AMK_BLEND_WEIGHT,
                f"Amatyakaraka {amatyakaraka} — livelihood karaka",
            )

        if not field_scores:
            return {
                "suitable_fields": [],
                "classical_summary": "10th house data missing for career mapping.",
                "amatyakaraka": amatyakaraka,
            }

        ranked = sorted(field_scores.items(), key=lambda x: -x[1])
        max_s = ranked[0][1] if ranked else 1.0
        suitable_fields = []
        for field, raw in ranked[:top_n]:
            rules = field_rules.get(field, [])
            suitable_fields.append({
                "field": field,
                "score": int(_clamp(round(raw * 100 / max_s), 22, 98)),
                "driver": rules[0] if rules else field,
                "rules": rules[:3],
            })

        occ_names = [p.get("name") for p in occupants_10]
        d10_names = [p.get("name") for p in d10_occ]
        occ_txt = ", ".join(occ_names) if occ_names else "none (using 10th lord)"
        d10_txt = ", ".join(d10_names) if d10_names else "none"
        summary = (
            f"D1 10th {sign_10}, lord {lord_10} in {l10_house}H ({l10_sign or '?'})"
            f" — occupants: [{occ_txt}]. D10 10th: [{d10_txt}]."
        )
        if amatyakaraka:
            summary += f" AmK: {amatyakaraka}."

        return {
            "suitable_fields": suitable_fields,
            "classical_summary": summary,
            "tenth_lord_planet": lord_10,
            "tenth_sign": sign_10,
            "tenth_occupants": occ_names,
            "tenth_lord_house": l10_house,
            "amatyakaraka": amatyakaraka,
            "d10_tenth_occupants": d10_names,
        }
    except Exception as exc:
        return {
            "suitable_fields": [],
            "classical_summary": f"Career mapping unavailable ({exc}).",
            "error": str(exc),
            "amatyakaraka": amatyakaraka,
        }
