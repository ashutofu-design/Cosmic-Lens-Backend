"""Bhrigu Chakra Paddhati (BCP) — 7th-lord placement + aspect marriage ages.

Rules (user spec):
  • House where 7L sits → marriage ages when that HOUSE number activates:
      e.g. 7L in 12H → ages 12, 24, 36, 48…
  • Houses aspected by 7L → same pattern for each aspected house number.
  • **Dual-sign 7L** (Mars/Mercury/Jupiter/Venus/Saturn): har owned rashi
    jis ghar se lagna se aati hai, us ghar ke BCP ages bhi (e.g. Mars → Mesh
    + Vrishchik dono houses count; Mercury → Mithun + Kanya houses).
  • D1 + D9 dono par alag BCP list; merged master list for timing.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

_SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
# Planet → both owned sign indices (0=Aries … 11=Pisces)
_PLANET_OWN_SIGNS: Dict[str, Tuple[int, ...]] = {
    "Mars": (0, 7),
    "Mercury": (2, 5),
    "Jupiter": (8, 11),
    "Venus": (1, 6),
    "Saturn": (9, 10),
}

_BCP_MAX_AGE = 96
_BCP_WINDOW_BOOST = 3.5
_BCP_NEAR_YEAR_BOOST = 2.0
_BCP_MISSED_RECENT_BOOST = 4.0
_BCP_CURRENT_DASHA_BOOST = 5.0
_MISSED_BCP_YEARS_THRESHOLD = 2   # 34 guzar, ab 37 → missed-recent mode
_RECENT_HORIZON_DAYS = 365
_BCP_SOURCE_WEIGHTS = {
    "7th_lord_placement": 5.0,
    "7th_lord_dual_sign_houses": 3.0,
    "7th_lord_aspects": 5.0,
    "7th_lord_dispositor_linkage": 4.0,
}
_BCP_D1_D9_OVERLAP_BONUS = 4.0
_BCP_SHARED_LINKAGE_HOUSE_BONUS = 6.0
_BCP_CLUSTER_NEIGHBOR_BONUS = 1.5
_BCP_CLUSTER_MAX_BONUS = 3.0


def _house_lord(lagna_si: int, house: int) -> str:
    return _SIGN_LORDS[(lagna_si + house - 1) % 12]


def _planet_house(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            h = p.get("house")
            if isinstance(h, int) and 1 <= h <= 12:
                return h
    return None


def _planet_sign_idx(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            s = p.get("sign")
            if isinstance(s, str) and s in _SIGN_NAMES:
                return _SIGN_NAMES.index(s)
    return None


def _house_from_sign(lagna_si: int, sign_si: int) -> int:
    """Whole-sign house number for a zodiac sign from lagna."""
    return (sign_si - lagna_si) % 12 + 1


def _dual_lordship_bcp_entries(
    seventh_lord: str,
    lagna_si: int,
    *,
    placement_house: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """BCP ages from each sign the 7L owns (user rule: doosri rashi ka ghar)."""
    owned = _PLANET_OWN_SIGNS.get(seventh_lord)
    if not owned:
        return []
    entries: List[Dict[str, Any]] = []
    for sign_si in owned:
        h = _house_from_sign(lagna_si, sign_si)
        if placement_house is not None and h == placement_house:
            continue  # already covered by placement source
        ages = _activation_ages_for_house(h)
        entries.append({
            "house": h,
            "sign": _SIGN_NAMES[sign_si],
            "ages": ages,
            "label": (
                f"7L ({seventh_lord}) owned sign {_SIGN_NAMES[sign_si]} "
                f"→ {h}H BCP"
            ),
        })
    return entries


def _aspects_target(aspector: str, ap_si: int, target_si: int) -> bool:
    diff = (target_si - ap_si) % 12 + 1
    if diff == 7:
        return True
    if aspector == "Mars" and diff in (4, 8):
        return True
    if aspector == "Jupiter" and diff in (5, 9):
        return True
    if aspector in ("Saturn", "Rahu", "Ketu") and diff in (3, 10):
        return True
    return False


def _aspect_house_nums(block: Optional[Dict[str, Any]]) -> List[int]:
    if not isinstance(block, dict):
        return []
    out: List[int] = []
    for row in block.get("aspect_houses") or []:
        if isinstance(row, dict):
            h = row.get("house")
            if isinstance(h, int):
                out.append(h)
    return sorted(set(out))


def _dispositor_linkage_entries(
    seventh_lord: str,
    seventh_lord_house: Optional[int],
    planets: List[dict],
    lagna_si: int,
    *,
    division: str = "D1",
    skip_houses: Optional[Set[int]] = None,
) -> List[Dict[str, Any]]:
    """7L placement sign-lord → that lord's house + aspects → BCP ages."""
    if seventh_lord_house is None:
        return []
    skip = set(skip_houses or ())
    sign_si = (lagna_si + seventh_lord_house - 1) % 12
    dispositor = _SIGN_LORDS[sign_si]
    if dispositor == seventh_lord:
        return []
    disp_si = _planet_sign_idx(planets, dispositor)
    disp_house = _planet_house(planets, dispositor)
    entries: List[Dict[str, Any]] = []
    if disp_house is not None and disp_house not in skip:
        entries.append({
            "house": disp_house,
            "ages": _activation_ages_for_house(disp_house),
            "dispositor": dispositor,
            "label": (
                f"{division} — 7L in {seventh_lord_house}H sign-lord "
                f"{dispositor}@{disp_house}H"
            ),
            "type": "dispositor_placement",
        })
        skip.add(disp_house)
    if disp_si is not None:
        for h in _houses_aspected_by_planet(dispositor, disp_si, lagna_si):
            if h in skip:
                continue
            entries.append({
                "house": h,
                "ages": _activation_ages_for_house(h),
                "dispositor": dispositor,
                "label": (
                    f"{division} — 7L sign-lord {dispositor} aspects {h}H"
                ),
                "type": "dispositor_aspect",
            })
    return entries


def _future_ages_from_division_block(
    block: Optional[Dict[str, Any]],
    user_age: Optional[int],
    *,
    limit: int = 6,
) -> List[int]:
    """Unique BCP ages for one division from current age onward."""
    if not isinstance(block, dict):
        return []
    pool = block.get("future_activation_ages")
    if not isinstance(pool, list):
        pool = [
            a for a in (block.get("all_marriage_ages") or [])
            if isinstance(a, int)
        ]
    ordered = sorted(a for a in pool if user_age is None or a >= user_age)
    return ordered[:limit]


def _houses_aspected_by_planet(
    planet: str, planet_si: int, lagna_si: int,
) -> List[int]:
    out: List[int] = []
    for h in range(1, 13):
        target_si = (lagna_si + h - 1) % 12
        if _aspects_target(planet, planet_si, target_si):
            out.append(h)
    return out


def _activation_ages_for_house(house: int, max_age: int = _BCP_MAX_AGE) -> List[int]:
    """BCP ages when this house number activates from Lagna (h, h+12, h+24…)."""
    if not (1 <= house <= 12):
        return []
    ages: List[int] = []
    a = house
    while a <= max_age:
        ages.append(a)
        a += 12
    return ages


def _bcp_7l_linkage_houses(block: Optional[Dict[str, Any]]) -> Set[int]:
    """7L placement + aspects + sign-lord of 7L house (dispositor linkage)."""
    if not isinstance(block, dict):
        return set()
    houses: Set[int] = set()
    ph = block.get("seventh_lord_house")
    if isinstance(ph, int):
        houses.add(ph)
    for ae in block.get("aspect_houses") or []:
        if not isinstance(ae, dict):
            continue
        h = ae.get("house")
        if isinstance(h, int):
            houses.add(h)
    for src in block.get("sources") or []:
        if not isinstance(src, dict):
            continue
        if src.get("source") != "7th_lord_dispositor_linkage":
            continue
        for row in src.get("houses") or []:
            if isinstance(row, dict) and isinstance(row.get("house"), int):
                houses.add(row["house"])
    return houses


def _shared_d1_d9_linkage_houses(
    d1: Dict[str, Any],
    d9: Optional[Dict[str, Any]],
) -> List[int]:
    """Houses where D1 and D9 7L sit/aspect overlap — priority BCP linkage."""
    if not isinstance(d9, dict):
        return []
    return sorted(_bcp_7l_linkage_houses(d1) & _bcp_7l_linkage_houses(d9))


def _priority_ages_from_shared_houses(
    shared_houses: List[int],
    user_age: Optional[int],
    *,
    limit: int = 8,
) -> List[int]:
    pool: Set[int] = set()
    for h in shared_houses:
        pool.update(_activation_ages_for_house(h))
    ordered = sorted(pool)
    if user_age is not None:
        ordered = [a for a in ordered if a >= user_age]
    return ordered[:limit]


def _merge_age_priority_lists(
    primary: List[int],
    secondary: List[int],
    *,
    limit: int = 12,
) -> List[int]:
    seen: Set[int] = set()
    out: List[int] = []
    for a in list(primary) + list(secondary):
        if not isinstance(a, int) or a in seen:
            continue
        seen.add(a)
        out.append(a)
        if len(out) >= limit:
            break
    return out


def _bcp_display_ages_from_current(
    *,
    shared_priority: List[int],
    focus_ages: List[int],
    all_ages: List[int],
    user_age: Optional[int],
    years_ahead: int = 5,
    limit: int = 4,
) -> List[int]:
    """Admin + Step0A: shared D1/D9 house ages first, then focus, from current age."""
    hi = (user_age + years_ahead) if user_age is not None else None
    shared_ok = [
        a for a in shared_priority
        if user_age is None or (a >= user_age and (hi is None or a <= hi))
    ]
    focus_ok = [
        a for a in focus_ages
        if user_age is None or (a >= user_age and (hi is None or a <= hi))
    ]
    all_ok = [
        a for a in all_ages
        if user_age is None or (a >= user_age and (hi is None or a <= hi))
    ]
    return _merge_age_priority_lists(
        shared_ok,
        _merge_age_priority_lists(focus_ok, all_ok, limit=limit),
        limit=limit,
    )


def _active_house_for_age(age: int) -> int:
    """Lagna BCP: age N → house ((N-1) % 12) + 1."""
    if age < 1:
        return 1
    return ((age - 1) % 12) + 1


def compute_bcp_for_division(
    planets: List[dict],
    lagna_si: int,
    *,
    division: str = "D1",
    user_age: Optional[int] = None,
) -> Dict[str, Any]:
    """BCP marriage-age map for one division (D1 or D9)."""
    seventh_lord = _house_lord(lagna_si, 7)
    seventh_lord_house = _planet_house(planets, seventh_lord)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)

    sources: List[Dict[str, Any]] = []

    placement_ages: List[int] = []
    if seventh_lord_house is not None:
        placement_ages = _activation_ages_for_house(seventh_lord_house)
        sources.append({
            "source": "7th_lord_placement",
            "house": seventh_lord_house,
            "label": f"{division} — 7L ({seventh_lord}) in {seventh_lord_house}H",
            "ages": placement_ages,
        })

    dual_entries = _dual_lordship_bcp_entries(
        seventh_lord, lagna_si, placement_house=seventh_lord_house,
    )
    if dual_entries:
        sources.append({
            "source": "7th_lord_dual_sign_houses",
            "houses": dual_entries,
            "label": f"{division} — 7L ({seventh_lord}) owned signs → houses",
        })

    aspect_entries: List[Dict[str, Any]] = []
    if seventh_lord_si is not None:
        skip_h = {seventh_lord_house}
        skip_h.update(e["house"] for e in dual_entries)
        for h in _houses_aspected_by_planet(seventh_lord, seventh_lord_si, lagna_si):
            if h in skip_h:
                continue
            ages = _activation_ages_for_house(h)
            aspect_entries.append({
                "house": h,
                "ages": ages,
                "label": f"{division} — 7L ({seventh_lord}) aspects {h}H",
            })
        if aspect_entries:
            sources.append({
                "source": "7th_lord_aspects",
                "houses": aspect_entries,
            })

    skip_for_disp: Set[int] = set()
    if seventh_lord_house is not None:
        skip_for_disp.add(seventh_lord_house)
    skip_for_disp.update(e["house"] for e in dual_entries)
    skip_for_disp.update(e["house"] for e in aspect_entries)
    dispositor_entries = _dispositor_linkage_entries(
        seventh_lord,
        seventh_lord_house,
        planets,
        lagna_si,
        division=division,
        skip_houses=skip_for_disp,
    )
    if dispositor_entries:
        sources.append({
            "source": "7th_lord_dispositor_linkage",
            "houses": dispositor_entries,
        })

    all_ages: Set[int] = set(placement_ages)
    for de in dual_entries:
        all_ages.update(de.get("ages") or [])
    for ae in aspect_entries:
        all_ages.update(ae.get("ages") or [])
    for de in dispositor_entries:
        all_ages.update(de.get("ages") or [])

    sorted_all = sorted(all_ages)
    past = [a for a in sorted_all if user_age is not None and a < user_age]
    future = [a for a in sorted_all if user_age is None or a >= user_age]
    next_act = future[0] if future else None

    upcoming_year_ages: List[int] = []
    if user_age is not None:
        for a in sorted_all:
            if user_age <= a <= user_age + 1:
                upcoming_year_ages.append(a)

    last_passed = past[-1] if past else None
    dual_houses = [e["house"] for e in dual_entries]

    return {
        "division": division,
        "lagna_sign_idx": lagna_si,
        "seventh_lord": seventh_lord,
        "seventh_lord_house": seventh_lord_house,
        "dual_sign_houses": dual_houses,
        "seventh_house_ages": [],
        "placement_ages": placement_ages,
        "dual_lord_ages": sorted(
            {a for e in dual_entries for a in (e.get("ages") or [])}
        ),
        "aspect_houses": aspect_entries,
        "sources": sources,
        "all_marriage_ages": sorted_all,
        "past_activation_ages": past,
        "future_activation_ages": future,
        "next_activation_age": next_act,
        "last_passed_bcp_age": last_passed,
        "years_since_last_bcp": (
            (user_age - last_passed) if (user_age is not None and last_passed) else None
        ),
        "years_to_next_bcp": (
            (next_act - user_age) if (user_age is not None and next_act is not None) else None
        ),
        "current_bcp_house": (
            _active_house_for_age(user_age) if user_age is not None else None
        ),
        "upcoming_year_bcp_ages": upcoming_year_ages,
        "future_bcp_ages": future[:6],
        "reasoning_summary": (
            f"BCP-{division}: 7L {seventh_lord}@{seventh_lord_house}H; "
            f"dual-sign houses {dual_houses}; "
            f"ages {sorted_all[:10]}{'…' if len(sorted_all) > 10 else ''}"
        ),
    }


def _future_ages_for_house(
    house: int,
    user_age: Optional[int] = None,
    *,
    limit: int = 4,
) -> List[int]:
    ages = _activation_ages_for_house(house)
    if user_age is not None:
        ages = [a for a in ages if a >= user_age]
    return ages[:limit]


def build_bcp_admin_linkage_display(
    bcp: Dict[str, Any] | None,
    *,
    user_age: Optional[int] = None,
) -> Dict[str, Any]:
    """Admin Step 2: 7L sit/aspect houses each with BCP ages from current age."""
    if not isinstance(bcp, dict):
        return {}
    d9 = bcp.get("d9_bcp") if isinstance(bcp.get("d9_bcp"), dict) else {}

    def _division_rows(block: Dict[str, Any], division: str) -> Dict[str, Any]:
        lord = block.get("seventh_lord")
        sit = block.get("seventh_lord_house")
        items: List[Dict[str, Any]] = []
        if isinstance(sit, int):
            ages = _future_ages_for_house(sit, user_age)
            items.append({
                "type": "placement",
                "house": sit,
                "ages": ages,
            })
        for ae in block.get("aspect_houses") or []:
            if not isinstance(ae, dict):
                continue
            h = ae.get("house")
            if not isinstance(h, int):
                continue
            raw = ae.get("ages") if isinstance(ae.get("ages"), list) else None
            if raw:
                ages = [int(a) for a in raw if isinstance(a, int)]
                if user_age is not None:
                    ages = [a for a in ages if a >= user_age]
                ages = ages[:4]
            else:
                ages = _future_ages_for_house(h, user_age)
            items.append({
                "type": "aspect",
                "house": h,
                "ages": ages,
            })
        for src in block.get("sources") or []:
            if not isinstance(src, dict):
                continue
            if src.get("source") != "7th_lord_dispositor_linkage":
                continue
            for row in src.get("houses") or []:
                if not isinstance(row, dict) or not isinstance(row.get("house"), int):
                    continue
                h = int(row["house"])
                raw = row.get("ages") if isinstance(row.get("ages"), list) else None
                if raw:
                    ages = [int(a) for a in raw if isinstance(a, int)]
                    if user_age is not None:
                        ages = [a for a in ages if a >= user_age]
                    ages = ages[:4]
                else:
                    ages = _future_ages_for_house(h, user_age)
                kind = row.get("type") or "dispositor"
                items.append({
                    "type": kind,
                    "house": h,
                    "ages": ages,
                })
        return {
            "division": division,
            "seventh_lord": lord,
            "placement_house": sit,
            "aspect_houses": _aspect_house_nums(block),
            "items": items,
        }

    d1_rows = _division_rows(bcp, "D1")
    d9_rows = _division_rows(d9, "D9") if d9 else {}
    shared = sorted(set(bcp.get("shared_7l_linkage_houses") or []))
    shared_age_items = [
        {"house": h, "ages": _future_ages_for_house(h, user_age)}
        for h in shared
    ]

    return {
        "d1": d1_rows,
        "d9": d9_rows,
        "shared_houses": shared,
        "shared_house_ages": _priority_ages_from_shared_houses(shared, user_age, limit=4),
        "shared_house_items": shared_age_items,
    }


def bcp_compact_admin_lines(
    bcp: Dict[str, Any] | None,
    *,
    user_age: Optional[int] = None,
) -> List[str]:
    """Admin Step 2: D1 ages line + D9 ages line (from current age)."""
    if not isinstance(bcp, dict):
        return ["D1: —", "D9: —"]
    if user_age is None:
        try:
            ua = bcp.get("user_age")
            if ua is not None:
                user_age = int(ua)
        except (TypeError, ValueError):
            pass
    d1 = bcp.get("d1_future_bcp_ages")
    if not isinstance(d1, list):
        d1 = _future_ages_from_division_block(bcp.get("d1_bcp") or {}, user_age)
    d9_block = bcp.get("d9_bcp") if isinstance(bcp.get("d9_bcp"), dict) else {}
    d9 = bcp.get("d9_future_bcp_ages")
    if not isinstance(d9, list):
        d9 = _future_ages_from_division_block(d9_block, user_age)
    d1s = ", ".join(str(a) for a in d1) if d1 else "—"
    d9s = ", ".join(str(a) for a in d9) if d9 else "—"
    return [f"D1: {d1s}", f"D9: {d9s}"]


def bcp_linkage_admin_lines(bcp: Dict[str, Any] | None) -> List[str]:
    """Compact admin/evidence lines: D1/D9 7L sit + aspect houses + ages."""
    if not isinstance(bcp, dict):
        return []
    user_age = None
    try:
        ua = bcp.get("user_age")
        if ua is not None:
            user_age = int(ua)
    except (TypeError, ValueError):
        pass
    display = build_bcp_admin_linkage_display(bcp, user_age=user_age)
    lines: List[str] = []
    d9 = bcp.get("d9_bcp") if isinstance(bcp.get("d9_bcp"), dict) else {}
    d1l = bcp.get("seventh_lord")
    d1p = bcp.get("seventh_lord_house")
    d1a = _aspect_house_nums(bcp)
    if d1l and d1p is not None:
        asp = ",".join(str(x) for x in d1a)
        lines.append(f"BCP_LINKAGE D1 7L={d1l} placement={d1p} aspects={asp}")
    d9l = d9.get("seventh_lord")
    d9p = d9.get("seventh_lord_house")
    d9a = _aspect_house_nums(d9)
    if d9l and d9p is not None:
        asp = ",".join(str(x) for x in d9a)
        lines.append(f"BCP_LINKAGE D9 7L={d9l} placement={d9p} aspects={asp}")
    for div_key, div in (("D1", display.get("d1")), ("D9", display.get("d9"))):
        if not isinstance(div, dict):
            continue
        for item in div.get("items") or []:
            if not isinstance(item, dict):
                continue
            h = item.get("house")
            kind = item.get("type") or "house"
            ages = item.get("ages") or []
            if isinstance(h, int):
                asp = ",".join(str(a) for a in ages)
                lines.append(f"BCP_HOUSE {div_key} {kind}={h} ages={asp}")
    shared = bcp.get("shared_7l_linkage_houses") or []
    if shared:
        lines.append(f"BCP_SHARED_HOUSES {','.join(str(h) for h in shared)}")
    return lines


def compute_bcp_marriage_ages(
    kundli: dict,
    lagna_si: int,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
    *,
    d9_lagna_si: Optional[int] = None,
    d9_planets: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """D1 BCP + optional D9; merged master list for Step 0 / Step 5."""
    _ = birth_dt  # reserved for future solar-year BCP
    planets = kundli.get("planets") or []
    d1 = compute_bcp_for_division(planets, lagna_si, division="D1", user_age=user_age)

    d9_block: Optional[Dict[str, Any]] = None
    merged_ages: Set[int] = set(d1.get("all_marriage_ages") or [])

    if isinstance(d9_lagna_si, int) and d9_planets:
        d9_block = compute_bcp_for_division(
            d9_planets, d9_lagna_si, division="D9", user_age=user_age,
        )
        merged_ages.update(d9_block.get("all_marriage_ages") or [])

    sorted_merged = sorted(merged_ages)
    shared_houses = _shared_d1_d9_linkage_houses(d1, d9_block)
    shared_priority_ages = _priority_ages_from_shared_houses(
        shared_houses, user_age, limit=8,
    )
    scored_ages = _score_merged_bcp_ages(
        d1, d9_block, user_age=user_age, shared_linkage_houses=shared_houses,
    )
    priority_ages = [r["age"] for r in scored_ages]
    future_priority_ages = [
        a for a in _merge_age_priority_lists(shared_priority_ages, priority_ages)
        if user_age is None or a >= user_age
    ]
    past_m = [a for a in sorted_merged if user_age is not None and a < user_age]
    future_m = [a for a in sorted_merged if user_age is None or a >= user_age]
    next_act = _resolve_next_activation_age(
        sorted_merged, future_priority_ages, user_age,
    )

    _bcp_for_display = {
        "seventh_lord": d1["seventh_lord"],
        "seventh_lord_house": d1["seventh_lord_house"],
        "aspect_houses": d1["aspect_houses"],
        "d9_bcp": d9_block,
        "shared_7l_linkage_houses": shared_houses,
        "shared_house_priority_ages": shared_priority_ages,
        "user_age": user_age,
    }

    base = {
        "seventh_lord": d1["seventh_lord"],
        "seventh_lord_house": d1["seventh_lord_house"],
        "dual_sign_houses_d1": d1.get("dual_sign_houses"),
        "seventh_house_ages": d1["seventh_house_ages"],
        "placement_ages": d1["placement_ages"],
        "dual_lord_ages": d1.get("dual_lord_ages"),
        "aspect_houses": d1["aspect_houses"],
        "sources": d1["sources"],
        "d1_bcp": d1,
        "d9_bcp": d9_block,
        "d1_7l_linkage_houses": sorted(_bcp_7l_linkage_houses(d1)),
        "d9_7l_linkage_houses": sorted(_bcp_7l_linkage_houses(d9_block)),
        "shared_7l_linkage_houses": shared_houses,
        "shared_house_priority_ages": shared_priority_ages,
        "bcp_admin_display": build_bcp_admin_linkage_display(
            _bcp_for_display, user_age=user_age,
        ),
        "d1_future_bcp_ages": _future_ages_from_division_block(d1, user_age),
        "d9_future_bcp_ages": _future_ages_from_division_block(d9_block, user_age),
        "bcp_compact_lines": bcp_compact_admin_lines(
            {
                "d1_future_bcp_ages": _future_ages_from_division_block(d1, user_age),
                "d9_future_bcp_ages": _future_ages_from_division_block(d9_block, user_age),
                "user_age": user_age,
            },
            user_age=user_age,
        ),
        "bcp_age_list": format_bcp_age_list(d1, d9_block),
        "all_marriage_ages": sorted_merged,
        "bcp_age_scores": scored_ages,
        "priority_marriage_ages": priority_ages,
        "future_priority_ages": future_priority_ages,
        "primary_priority_age": future_priority_ages[0] if future_priority_ages else None,
        "past_activation_ages": past_m,
        "future_activation_ages": future_m,
        "next_activation_age": next_act,
        "last_passed_bcp_age": past_m[-1] if past_m else None,
        "years_since_last_bcp": (
            (user_age - past_m[-1]) if (user_age is not None and past_m) else None
        ),
        "years_to_next_bcp": (
            (next_act - user_age)
            if (user_age is not None and next_act is not None) else None
        ),
        "current_bcp_house": d1.get("current_bcp_house"),
        "upcoming_year_bcp_ages": sorted(
            {a for a in sorted_merged if user_age is not None and user_age <= a <= user_age + 1}
        ),
        "reasoning_summary": d1.get("reasoning_summary", ""),
    }
    if d9_block:
        base["reasoning_summary"] += " | " + d9_block.get("reasoning_summary", "")
    base.update(resolve_bcp_timing_strategy(base, user_age))
    return base


def _iter_bcp_source_hits(block: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(block, dict):
        return []
    division = block.get("division") or "D1"
    hits: List[Dict[str, Any]] = []
    for src in block.get("sources") or []:
        kind = src.get("source")
        weight = _BCP_SOURCE_WEIGHTS.get(kind, 0.0)
        if not weight:
            continue
        if kind == "7th_lord_placement":
            rows = [{
                "house": src.get("house"),
                "ages": src.get("ages") or [],
                "label": src.get("label"),
            }]
        else:
            rows = src.get("houses") or []
        for row in rows:
            for age in row.get("ages") or []:
                if not isinstance(age, int):
                    continue
                hits.append({
                    "age": age,
                    "division": division,
                    "source": kind,
                    "house": row.get("house"),
                    "label": row.get("label"),
                    "weight": weight,
                })
    return hits


def _score_merged_bcp_ages(
    d1: Dict[str, Any],
    d9: Optional[Dict[str, Any]],
    *,
    user_age: Optional[int] = None,
    shared_linkage_houses: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """Score BCP ages before dasha: source strength + D1/D9 overlap + clusters."""
    shared_house_set = set(shared_linkage_houses or [])
    if not shared_house_set and d9:
        shared_house_set = set(_shared_d1_d9_linkage_houses(d1, d9))
    by_age: Dict[int, Dict[str, Any]] = {}
    for hit in _iter_bcp_source_hits(d1) + _iter_bcp_source_hits(d9):
        age = hit["age"]
        row = by_age.setdefault(age, {
            "age": age,
            "score": 0.0,
            "sources": [],
            "divisions": set(),
            "rules": set(),
            "houses": set(),
            "overlap_d1_d9": False,
            "shared_linkage_house": False,
            "cluster_neighbors": [],
        })
        row["score"] += float(hit["weight"])
        row["sources"].append(hit)
        row["divisions"].add(hit["division"])
        row["rules"].add(hit["source"])
        if isinstance(hit.get("house"), int):
            row["houses"].add(hit["house"])

    ages = set(by_age)
    for age, row in by_age.items():
        if {"D1", "D9"}.issubset(row["divisions"]):
            row["score"] += _BCP_D1_D9_OVERLAP_BONUS
            row["overlap_d1_d9"] = True
        if shared_house_set and (row["houses"] & shared_house_set):
            row["score"] += _BCP_SHARED_LINKAGE_HOUSE_BONUS
            row["shared_linkage_house"] = True
        neighbors = sorted(a for a in ages if a != age and abs(a - age) <= 1)
        if neighbors:
            cluster_bonus = min(
                _BCP_CLUSTER_MAX_BONUS,
                len(neighbors) * _BCP_CLUSTER_NEIGHBOR_BONUS,
            )
            row["score"] += cluster_bonus
            row["cluster_neighbors"] = neighbors

    out: List[Dict[str, Any]] = []
    for row in by_age.values():
        divisions = sorted(row["divisions"])
        rules = sorted(row["rules"])
        houses = sorted(row["houses"])
        out.append({
            "age": row["age"],
            "score": round(float(row["score"]), 2),
            "divisions": divisions,
            "rules": rules,
            "houses": houses,
            "overlap_d1_d9": bool(row["overlap_d1_d9"]),
            "shared_linkage_house": bool(row["shared_linkage_house"]),
            "cluster_neighbors": row["cluster_neighbors"],
            "is_future": user_age is None or row["age"] >= user_age,
            "sources": row["sources"],
        })
    out.sort(key=lambda r: (-float(r["score"]), r["age"]))
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return out


def _bcp_score_lookup(bcp: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    return {
        int(r["age"]): r
        for r in (bcp.get("bcp_age_scores") or [])
        if isinstance(r, dict) and isinstance(r.get("age"), int)
    }


def format_bcp_age_list(
    d1: Dict[str, Any],
    d9: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Human-readable BCP sources → age rows for UI / LLM."""
    rows: List[Dict[str, Any]] = []

    def _walk(block: Dict[str, Any]) -> None:
        div = block.get("division") or "D1"
        for src in block.get("sources") or []:
            kind = src.get("source")
            if kind == "7th_lord_placement":
                rows.append({
                    "division": div,
                    "rule": "7L placement",
                    "detail": src.get("label"),
                    "ages": src.get("ages") or [],
                })
            elif kind == "7th_lord_dual_sign_houses":
                for h in src.get("houses") or []:
                    rows.append({
                        "division": div,
                        "rule": "7L dual-sign house",
                        "detail": h.get("label"),
                        "ages": h.get("ages") or [],
                    })
            elif kind == "7th_lord_aspects":
                for h in src.get("houses") or []:
                    rows.append({
                        "division": div,
                        "rule": "7L aspect",
                        "detail": h.get("label"),
                        "ages": h.get("ages") or [],
                    })
            elif kind == "7th_lord_dispositor_linkage":
                for h in src.get("houses") or []:
                    rows.append({
                        "division": div,
                        "rule": "7L sign-lord linkage",
                        "detail": h.get("label"),
                        "ages": h.get("ages") or [],
                    })

    _walk(d1)
    if d9:
        _walk(d9)
    return rows


def resolve_late_marriage_bcp_focus(
    bcp: Dict[str, Any],
    *,
    marriage_pace: str,
    user_age: Optional[int],
    years_ahead: int = 8,
) -> Dict[str, Any]:
    """Late marriage → directly grab current BCP year or next late-cycle ages.

    Skips marketing past early BCP (7,12,19) when chart is late and user
  already crossed them — anchor on upcoming 24/31/36-style activations.
    """
    all_ages = bcp.get("all_marriage_ages") or []
    past = bcp.get("past_activation_ages") or []
    future = bcp.get("future_activation_ages") or []
    score_map = _bcp_score_lookup(bcp)
    is_late_chart = marriage_pace in ("LATE", "VERY_LATE", "DELAYED")

    def _priority_sort(ages: List[int]) -> List[int]:
        return sorted(
            ages,
            key=lambda a: (-(score_map.get(a) or {}).get("score", 0), a),
        )

    if is_late_chart and user_age is not None:
        # Late chart: skip incidental current-age hits and pick strongest BCP
        # zone by source/overlap/cluster score, not just the earliest age.
        last_p = past[-1] if past else None
        hi = user_age + years_ahead
        focus = [
            a for a in future
            if a <= hi
            and a >= 24
            and (a > user_age or a >= 31)
            and (last_p is None or a >= last_p or a >= 31)
        ]
        focus = _priority_sort(focus)
        if not focus and future:
            focus = _priority_sort([a for a in future if a >= 24])[:4] or _priority_sort(future)[:4]
        primary = focus[0] if focus else bcp.get("next_activation_age")

        if (
            user_age in all_ages
            and primary is not None
            and user_age == primary
        ):
            return {
                "mode": "current_bcp_activation",
                "focus_ages": [user_age],
                "primary_age": user_age,
                "directive": (
                    f"Abhi user ki umar {user_age} khud BCP marriage age hai — "
                    "isi saal/current dasha ko pakdo."
                ),
            }
        return {
            "mode": "late_chart_upcoming_bcp",
            "focus_ages": focus,
            "primary_age": primary,
            "between_ages": (
                f"{last_p} guzar → ab {user_age} → priority BCP {primary}"
                if last_p and primary else None
            ),
            "directive": (
                f"Chart late — past chhoti BCP ages mat bolo. "
                f"Direct focus: priority marriage BCP ages {focus[:5]}."
            ),
        }

    if user_age is not None and user_age in all_ages:
        return {
            "mode": "current_bcp_activation",
            "focus_ages": [user_age],
            "primary_age": user_age,
            "directive": (
                f"Abhi user ki umar {user_age} khud BCP marriage age hai — "
                "isi saal/current dasha ko pakdo."
            ),
        }

    priority_future = bcp.get("future_priority_ages") or []
    nxt = priority_future[0] if priority_future else bcp.get("next_activation_age")
    return {
        "mode": "standard_next_bcp",
        "focus_ages": [
            a for a in priority_future
            if user_age is None or a <= user_age + years_ahead
        ][:6],
        "primary_age": nxt,
        "directive": f"Priority BCP activation age {nxt}.",
    }


def compute_bcp_marriage_ages_d1_only(
    kundli: dict,
    lagna_si: int,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Back-compat: D1-only BCP (calls merged helper without D9)."""
    _ = birth_dt
    return compute_bcp_marriage_ages(kundli, lagna_si, user_age=user_age)


def _near_bcp_activation_ages(
    bcp: Dict[str, Any],
    user_age: Optional[int],
    within_years: int = 2,
) -> List[int]:
    """Raw BCP ages due within `within_years` (not priority-scored far ages)."""
    if user_age is None:
        return []
    hi = user_age + within_years
    return [
        int(a) for a in (bcp.get("all_marriage_ages") or [])
        if isinstance(a, int) and user_age < a <= hi
    ]


def _resolve_next_activation_age(
    sorted_merged: List[int],
    future_priority_ages: List[int],
    user_age: Optional[int],
) -> Optional[int]:
    """Next BCP activation — skip incidental in-list age (e.g. 2H→26 at user 26)."""
    if user_age is None:
        return sorted_merged[0] if sorted_merged else None
    for a in future_priority_ages:
        if a > user_age:
            return a
    future_m = [a for a in sorted_merged if a >= user_age]
    if not future_m:
        return None
    if future_m[0] > user_age:
        return future_m[0]
    return future_m[1] if len(future_m) > 1 else future_m[0]


def resolve_bcp_timing_strategy(
    bcp: Dict[str, Any],
    user_age: Optional[int],
) -> Dict[str, Any]:
    """STEP 0 — BCP age first: PRIORITY (boost/sort), never skip non-BCP years.

    All modes still scan the full future dasha chain one-by-one; each window
    gets its own transit check. search_horizon_days / late_urgent only bias
    near-term windows — they do NOT exclude later years.

    Modes:
      upcoming_bcp     — next BCP age within ~2 years (extra boost near that age)
      current_bcp_year — user is IN a BCP activation age this year
      missed_bcp_recent — last BCP passed (e.g. 34), user older (37);
                          lead with recent 12mo but still scan all future dasha
      standard         — normal pipeline
    """
    if user_age is None:
        return {
            "timing_mode": "standard",
            "search_horizon_days": _RECENT_HORIZON_DAYS,
            "late_urgent_scan": False,
            "prefer_current_dasha": False,
            "bcp_boost_future_only": True,
            "pipeline_order": "bcp_age→age→significators→dasha→transit",
            "llm_directive": "User age unknown — use dasha+transit windows.",
        }

    last_passed = bcp.get("last_passed_bcp_age")
    next_act = bcp.get("next_activation_age")
    upcoming = bcp.get("upcoming_year_bcp_ages") or []
    years_since = bcp.get("years_since_last_bcp")
    years_to_next = bcp.get("years_to_next_bcp")

    # User is in the merged BCP list — only "this year" when that age heads
    # the priority queue. Incidental hits (e.g. 2H→26 while 7H→31 is next for
    # a late chart) must NOT force current_bcp_year / near-term 2026 windows.
    pri_head = bcp.get("primary_priority_age")
    if user_age in (bcp.get("all_marriage_ages") or []):
        if pri_head is not None and user_age == int(pri_head):
            return {
                "timing_mode": "current_bcp_year",
                "search_horizon_days": _RECENT_HORIZON_DAYS,
                "late_urgent_scan": True,
                "prefer_current_dasha": True,
                "bcp_boost_future_only": False,
                "primary_reference_age": user_age,
                "pipeline_order": "bcp_age→age→significators→dasha→transit",
                "llm_directive": (
                    f"User abhi BCP marriage activation age {user_age} par hai — "
                    "current dasha+transit ko primary batao; is saal window strong."
                ),
            }

    # Near raw BCP age (e.g. 27 when user is 26) beats priority-scored far age (35).
    near_act = _near_bcp_activation_ages(bcp, user_age, within_years=2)
    if near_act:
        act = near_act[0]
        ytn = act - int(user_age)
        return {
            "timing_mode": "upcoming_bcp",
            "search_horizon_days": max(_RECENT_HORIZON_DAYS, ytn * 366),
            "late_urgent_scan": ytn <= 1,
            "prefer_current_dasha": False,
            "bcp_boost_future_only": False,
            "primary_reference_age": act,
            "pipeline_order": "bcp_age→age→significators→dasha→transit",
            "llm_directive": (
                f"BCP activation age {act} ({ytn} saal mein) — "
                "dasha windows is age ke around align karo."
            ),
        }

    # Next BCP age soon (within 2 years) — priority-scored queue
    if years_to_next is not None and years_to_next <= 2:
        return {
            "timing_mode": "upcoming_bcp",
            "search_horizon_days": max(_RECENT_HORIZON_DAYS, years_to_next * 366),
            "late_urgent_scan": years_to_next <= 1,
            "prefer_current_dasha": False,
            "bcp_boost_future_only": False,
            "primary_reference_age": next_act,
            "pipeline_order": "bcp_age→age→significators→dasha→transit",
            "llm_directive": (
                f"BCP next marriage age {next_act} ({years_to_next} saal mein) — "
                "dasha windows is age ke around align karo."
            ),
        }

    # Missed: e.g. BCP 34, user 37, next 40 — NOT young user 26 past incidental 24
    if (
        last_passed is not None
        and years_since is not None
        and years_since >= 2
        and user_age is not None
        and user_age > int(last_passed) + 2
        and (years_to_next is None or years_to_next > _MISSED_BCP_YEARS_THRESHOLD)
        and not near_act
    ):
        return {
            "timing_mode": "missed_bcp_recent",
            "search_horizon_days": _RECENT_HORIZON_DAYS,
            "late_urgent_scan": True,
            "prefer_current_dasha": True,
            "bcp_boost_future_only": True,
            "primary_reference_age": last_passed,
            "pipeline_order": "bcp_age→age→significators→dasha→transit",
            "llm_directive": (
                f"BCP marriage age {last_passed} guzar chuka (user ab {user_age}). "
                f"Agla BCP age {next_act} abhi door hai — past {last_passed} mat bolo "
                "'ab hogi'. Pehle current/near-term dasha+transit batao; "
                "door ke saal bhi scan hue hain — strong dasha+transit wahan "
                "backup window ho sakti hai."
            ),
        }

    if upcoming:
        years_to_first = (
            (upcoming[0] - user_age) if user_age is not None else 99
        )
        return {
            "timing_mode": "upcoming_bcp",
            "search_horizon_days": max(
                _RECENT_HORIZON_DAYS, years_to_first * 366,
            ),
            "late_urgent_scan": years_to_first <= 1,
            "prefer_current_dasha": False,
            "bcp_boost_future_only": False,
            "primary_reference_age": upcoming[0],
            "pipeline_order": "bcp_age→age→significators→dasha→transit",
            "llm_directive": (
                f"BCP activation age {upcoming[0]} jaldi aa raha — "
                "near-term dasha+transit check karo."
            ),
        }

    return {
        "timing_mode": "standard",
        "search_horizon_days": _RECENT_HORIZON_DAYS,
        "late_urgent_scan": False,
        "prefer_current_dasha": False,
        "bcp_boost_future_only": True,
        "pipeline_order": "bcp_age→age→significators→dasha→transit",
        "llm_directive": "Standard BCP+dasha+transit merge.",
    }


def _age_span_in_chunk(
    birth_dt: Optional[datetime],
    start: datetime,
    end: datetime,
) -> Tuple[Optional[int], Optional[int]]:
    if birth_dt is None:
        return None, None
    try:
        min_a = max(0, (start.date() - birth_dt.date()).days // 365)
        max_a = max(0, (end.date() - birth_dt.date()).days // 365)
        return min_a, max_a
    except Exception:
        return None, None


def bcp_boost_for_window(
    bcp: Dict[str, Any],
    birth_dt: Optional[datetime],
    start: datetime,
    end: datetime,
    *,
    now: Optional[datetime] = None,
    strategy: Optional[Dict[str, Any]] = None,
) -> Tuple[float, str]:
    """Score boost when dasha window overlaps a BCP marriage activation age."""
    strategy = strategy or {}
    mode = strategy.get("timing_mode", "standard")
    ages = set(bcp.get("all_marriage_ages") or [])
    score_map = _bcp_score_lookup(bcp)
    if not ages:
        return 0.0, ""

    min_a, max_a = _age_span_in_chunk(birth_dt, start, end)
    now = now or datetime.utcnow()

    # Missed BCP: only boost windows in next 12 months, not far future BCP (40)
    if mode == "missed_bcp_recent" and not strategy.get("chart_delayed"):
        if start > now + timedelta(days=_RECENT_HORIZON_DAYS):
            return 0.0, ""
        if start <= now + timedelta(days=_RECENT_HORIZON_DAYS):
            return _BCP_MISSED_RECENT_BOOST, "missed-BCP → recent 12mo window"
        return 0.0, ""

    hits: List[int] = []
    if min_a is not None and max_a is not None:
        for a in ages:
            if min_a <= a <= max_a:
                hits.append(a)

    if hits:
        if strategy.get("bcp_boost_future_only") and min_a is not None:
            last_passed = bcp.get("last_passed_bcp_age")
            if last_passed and min_a < last_passed:
                return 0.0, ""
        best_age = max(
            hits,
            key=lambda a: (score_map.get(a) or {}).get("score", 0),
        )
        best_score = float((score_map.get(best_age) or {}).get("score", 0.0))
        boost = _BCP_WINDOW_BOOST + min(4.0, best_score * 0.35)
        return round(boost, 2), (
            f"BCP age hit {hits} in window; priority age {best_age} "
            f"score={round(best_score, 2)}"
        )

    next_a = bcp.get("primary_priority_age") or bcp.get("next_activation_age")
    if next_a is not None and min_a is not None and abs(next_a - min_a) <= 1:
        return _BCP_NEAR_YEAR_BOOST, f"BCP near next activation age {next_a}"

    return 0.0, ""


def apply_bcp_boost_to_candidates(
    candidates: List[Dict[str, Any]],
    bcp: Dict[str, Any],
    birth_dt: Optional[datetime],
    *,
    now: Optional[datetime] = None,
    strategy: Optional[Dict[str, Any]] = None,
    current_dasha: Optional[Dict[str, Any]] = None,
) -> int:
    """Mutate candidates in place; return count boosted."""
    now = now or datetime.utcnow()
    strategy = strategy or {}
    n = 0
    for c in candidates:
        boost, note = bcp_boost_for_window(
            bcp, birth_dt, c["start"], c["end"],
            now=now, strategy=strategy,
        )
        if strategy.get("prefer_current_dasha") and current_dasha:
            cur = current_dasha
            if (c.get("md") == cur.get("md")
                    and c.get("ad") == cur.get("ad")
                    and c.get("pd") == cur.get("pd")):
                boost += _BCP_CURRENT_DASHA_BOOST
                note = (note + "; current MD-AD-PD") if note else "current MD-AD-PD"
            elif c["start"] <= now < c["end"]:
                boost += _BCP_CURRENT_DASHA_BOOST * 0.6
                note = (note + "; active now") if note else "active now"
        if boost > 0:
            c["score"] = float(c.get("score", 0)) + boost
            c["bcp_boost"] = boost
            c["bcp_note"] = note
            n += 1
    return n
