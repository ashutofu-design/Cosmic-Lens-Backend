"""
Career top matches from D1 — simplified for UI.

Only uses:
  • Planets sitting in the 10th house (career bhava) — primary
  • 10th lord's house placement — one theme line of suitable work
  • If 10th is empty → 10th sign lord's planet jobs only

No Atmakaraka, conjunction catalog, D10, or 127 micro-niches.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from vedic.life_specifics import DEBIL, EXALT, OWN, SIGNS, SIGN_LORD

# Planet → short career labels (finance / education / media style)
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
        "Finance / Banking",
        "Education / Teaching",
        "Business / Trading",
        "Media / Communication",
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

# Where 10th lord sits → extra career themes (bhava phala)
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


def compute_classical_top_careers(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict] = None,
    *,
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Return suitable_fields[] for career UI. Never raises.
    """
    del kundli  # D10 not used in simplified path

    try:
        from vedic.career_inclination_engine import ensure_planet_houses

        normed = ensure_planet_houses(list(planets or []), asc_idx)
        sign_10 = SIGNS[(asc_idx + 9) % 12]
        lord_10 = SIGN_LORD[sign_10]
        occupants_10 = [
            p for p in normed if int(p.get("house") or 0) == 10 and p.get("name")
        ]

        l10 = next((p for p in normed if p.get("name") == lord_10), None)
        l10_house = int(l10.get("house") or 0) if l10 else 0
        l10_sign = str(l10.get("sign") or "") if l10 else ""

        field_scores: Dict[str, float] = {}
        field_rules: Dict[str, List[str]] = {}

        def _add(field: str, points: float, rule: str) -> None:
            if not field or points <= 0:
                return
            field_scores[field] = field_scores.get(field, 0.0) + points
            field_rules.setdefault(field, [])
            if rule and rule not in field_rules[field]:
                field_rules[field].append(rule)

        # ── Primary: planets in 10th house ────────────────────────────────
        if occupants_10:
            for p in occupants_10:
                nm = str(p.get("name") or "")
                sg = str(p.get("sign") or "")
                mult = _dignity_multiplier(nm, sg)
                for job in _PLANET_JOBS.get(nm, ()):
                    _add(job, 40 * mult, f"{nm} in 10th house ({sg})")
        else:
            # Empty 10th → 10th lord planet only
            for job in _PLANET_JOBS.get(lord_10, ()):
                _add(job, 35, f"10th empty — 10th lord {lord_10} ({sign_10})")

        # ── Secondary: 10th lord's house theme ────────────────────────────
        if l10_house:
            for job in _LORD_HOUSE_JOBS.get(l10_house, ()):
                _add(job, 18, f"10th lord {lord_10} in {l10_house}th house")

        if not field_scores:
            return {
                "suitable_fields": [],
                "classical_summary": "10th house data missing for career mapping.",
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
                "rules": rules[:2],
            })

        occ_names = [p.get("name") for p in occupants_10]
        occ_txt = ", ".join(occ_names) if occ_names else "none (using 10th lord)"
        summary = (
            f"10th {sign_10}, lord {lord_10} in {l10_house}H"
            f" ({l10_sign or '?'}) — occupants: [{occ_txt}]."
        )

        return {
            "suitable_fields": suitable_fields,
            "classical_summary": summary,
            "tenth_lord_planet": lord_10,
            "tenth_sign": sign_10,
            "tenth_occupants": occ_names,
            "tenth_lord_house": l10_house,
        }
    except Exception as exc:
        return {
            "suitable_fields": [],
            "classical_summary": f"Career mapping unavailable ({exc}).",
            "error": str(exc),
        }
