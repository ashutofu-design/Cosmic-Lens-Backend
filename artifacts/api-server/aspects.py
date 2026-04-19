"""
aspects.py
──────────
Graha Drishti (planetary aspects) — classical Parashari rules.

Every planet aspects the 7th house from itself (full aspect).
Special aspects:
  • Mars     → 4th and 8th houses (in addition to 7th)
  • Jupiter  → 5th and 9th houses
  • Saturn   → 3rd and 10th houses
  • Rahu/Ketu → 5th, 7th, 9th (followed by KP / some traditions)

Public API
──────────
    compute_aspects(planets, lagna_sign_idx=None) -> {
        "by_planet": { planet_name: [{house, aspected_planets:[...]}] },
        "on_planet": { planet_name: [aspecting_planets] },
        "on_house":  { 1..12: [aspecting_planets] },
        "key_aspects": [str, ...]   # human-readable highlights
    }

Returns {} if input malformed. Never raises.
"""
from __future__ import annotations
from typing import Any

_SPECIAL: dict[str, list[int]] = {
    "Sun":     [7],
    "Moon":    [7],
    "Mars":    [4, 7, 8],
    "Mercury": [7],
    "Jupiter": [5, 7, 9],
    "Venus":   [7],
    "Saturn":  [3, 7, 10],
    "Rahu":    [5, 7, 9],
    "Ketu":    [5, 7, 9],
}

_BENEFICS = {"Jupiter", "Venus", "Mercury"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def compute_aspects(planets: list, lagna_sign_idx: int | None = None) -> dict[str, Any]:
    if not isinstance(planets, list):
        return {}

    # Build {name: house} map
    house_of: dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        h  = p.get("house")
        if nm and isinstance(h, int) and 1 <= h <= 12:
            house_of[nm] = h
    if not house_of:
        return {}

    # Inverse: house → planets occupying it
    occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for nm, h in house_of.items():
        occupants[h].append(nm)

    by_planet: dict[str, list[dict]] = {}
    on_planet: dict[str, list[str]] = {nm: [] for nm in house_of}
    on_house:  dict[int, list[str]] = {h: [] for h in range(1, 13)}
    key_aspects: list[str] = []

    for nm, h in house_of.items():
        special = _SPECIAL.get(nm, [7])
        rows: list[dict] = []
        for offset in special:
            target = ((h - 1 + offset - 1) % 12) + 1
            aspected = list(occupants.get(target, []))
            on_house[target].append(nm)
            for ap in aspected:
                if ap != nm:
                    on_planet[ap].append(nm)
            rows.append({"house": target, "aspected_planets": aspected, "type": offset})
        by_planet[nm] = rows

    # Highlight notable mutual + classical aspects
    # 1) Jupiter aspect on key kendra/trikona — generally beneficial
    if "Jupiter" in house_of:
        j_targets = [r["house"] for r in by_planet["Jupiter"]]
        good_targets = [t for t in j_targets if t in (1, 4, 5, 7, 9, 10)]
        if good_targets:
            key_aspects.append(
                f"Jupiter aspects kendra/trikona houses {sorted(set(good_targets))} "
                "— protective, expansive influence"
            )
    # 2) Saturn aspect on Lagna or Moon — heavy/restrictive theme
    if "Saturn" in house_of:
        s_targets = [r["house"] for r in by_planet["Saturn"]]
        moon_h = house_of.get("Moon")
        if 1 in s_targets:
            key_aspects.append("Saturn aspects Lagna (H1) — disciplined, serious life-theme")
        if moon_h and moon_h in s_targets:
            key_aspects.append(f"Saturn aspects Moon (H{moon_h}) — emotional weight, Sade-Sati-like pressure")
    # 3) Mars aspect on 7H or 4H — aggressive/conflict potential
    if "Mars" in house_of:
        m_targets = [r["house"] for r in by_planet["Mars"]]
        if 7 in m_targets:
            key_aspects.append("Mars aspects 7H (partnership) — friction in relationships unless mitigated")
        if 4 in m_targets:
            key_aspects.append("Mars aspects 4H (home) — domestic restlessness or property disputes")
    # 4) Rahu aspect on 7H or 5H — entanglements
    if "Rahu" in house_of:
        r_targets = [r["house"] for r in by_planet["Rahu"]]
        if 7 in r_targets:
            key_aspects.append("Rahu aspects 7H — unconventional or foreign partnership theme")

    # Mutual aspect (drishti yoga) — 2 planets aspect each other
    seen: set[tuple[str, str]] = set()
    for nm, rows in by_planet.items():
        for r in rows:
            for ap in r["aspected_planets"]:
                if ap == nm:
                    continue
                # Check if `ap` aspects `nm` back, across ALL of ap's rows
                ap_targets: set[str] = set()
                for ap_row in by_planet.get(ap, []):
                    ap_targets.update(ap_row.get("aspected_planets") or [])
                if nm in ap_targets:
                    pair = tuple(sorted([nm, ap]))
                    if pair in seen:
                        continue
                    seen.add(pair)
                    key_aspects.append(f"Mutual aspect: {pair[0]} ↔ {pair[1]} — strong intertwined karmic theme")

    return {
        "by_planet":   by_planet,
        "on_planet":   on_planet,
        "on_house":    on_house,
        "key_aspects": key_aspects,
    }


def format_aspect_summary(asp: dict) -> str:
    """Compact prompt block listing only the KEY aspects (not all)."""
    if not asp or not asp.get("key_aspects"):
        return "▸ KEY ASPECTS: (none particularly notable in classical drishti rules)"
    lines = ["▸ KEY ASPECTS (classical Parashari drishti):"]
    for i, k in enumerate(asp["key_aspects"], 1):
        lines.append(f"   {i}. {k}")
    return "\n".join(lines)
