"""
AstroVastu — chart-personalized room ideals (classical Vastu + horoscope blend).

Generic house rules stay the spine; Mahadasha, Lagna, weak planets,
and Ishta Devata adjust which directions are ideal/acceptable FOR THIS USER.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Set

from astrovastu_rules import (
    get_dasha_active_direction,
    get_generic_room_rule,
    get_lagna_directions,
    get_planet_direction,
)

try:
    from astrovastu_chart_vastu import ROOM_BHAVA, bhava_lord_placement
except ImportError:
    ROOM_BHAVA = {}
    bhava_lord_placement = None  # type: ignore

# Mahadasha / bhava boosts must not push NE for heavy/private zones.
_NO_DASHA_BOOST_DIRS: Dict[str, Set[str]] = {
    "bedroom": {"North-East"},
    "master_bedroom": {"North-East"},
    "kitchen": {"North-East"},
    "pooja": {"South-West"},
    "pooja_room": {"South-West"},
}

# Mahadasha lord → extra ideal directions per room (classical + jyotish blend)
_DASHA_ROOM_BOOST: Dict[str, Dict[str, List[str]]] = {
    "kitchen": {
        "Sun":     ["East", "South-East"],
        "Moon":    ["North-West"],
        "Mars":    ["South", "South-East"],
        "Mercury": ["North"],
        "Jupiter": ["North-East"],
        "Venus":   ["South-East"],
        "Saturn":  ["West"],
    },
    "bedroom": {
        "Moon":    ["North-West", "West"],
        "Mars":    ["South", "South-West"],
        "Venus":   ["South-West", "West"],
        "Saturn":  ["West", "South-West"],
        "Jupiter": ["North-East"],
        "Sun":     ["East"],
    },
    "pooja": {
        "Sun":     ["East", "North-East"],
        "Moon":    ["North-East"],
        "Jupiter": ["North-East"],
        "Ketu":    ["North-East"],
        "Mercury": ["North", "East"],
        "Venus":   ["East"],
    },
    "pooja_room": {
        "Sun": ["East", "North-East"],
        "Moon": ["North-East"],
        "Jupiter": ["North-East"],
        "Ketu": ["North-East"],
    },
    "living": {
        "Sun":     ["East", "North-East"],
        "Moon":    ["North", "North-West"],
        "Jupiter": ["North-East"],
        "Mercury": ["North", "East"],
        "Venus":   ["East"],
    },
    "living_room": {
        "Sun": ["East", "North-East"],
        "Jupiter": ["North-East"],
        "Moon": ["North", "North-West"],
    },
    "bathroom": {
        "Moon":    ["North-West", "West"],
        "Saturn":  ["West"],
        "Mars":    ["South-East"],
        "Venus":   ["West"],
    },
    "toilet": {
        "Moon":   ["North-West", "West"],
        "Saturn": ["West"],
        "Mars":   ["South-East"],
    },
    "study": {
        "Mercury": ["North", "East", "North-East"],
        "Jupiter": ["North-East"],
        "Sun":     ["East"],
        "Moon":    ["North"],
    },
    "main_door": {
        "Sun":     ["East", "North-East"],
        "Moon":    ["North", "North-West"],
        "Jupiter": ["North-East"],
        "Mercury": ["North", "East"],
        "Venus":   ["East"],
    },
    "entrance": {
        "Sun": ["East", "North-East"],
        "Jupiter": ["North-East"],
        "Moon": ["North", "North-West"],
    },
    "dining": {
        "Moon":  ["West", "North-West"],
        "Venus": ["West"],
        "Sun":   ["East"],
        "Saturn":["West"],
    },
    "staircase": {
        "Mars":   ["South", "South-West"],
        "Saturn": ["South", "West", "South-West"],
        "Sun":    ["South"],
    },
}

_WEAK_PLANET_ROOM_HINT: Dict[str, Dict[str, str]] = {
    "Mars": {
        "kitchen": (
            "Weak Mars — keep kitchen in South-East (Agni); do not use South as your "
            "primary kitchen zone."
        ),
        "bedroom": "Weak Mars — master bedroom in South/SW is more sensitive for you.",
    },
    "Moon": {
        "bedroom": "Weak Moon — NW/W bedroom directions need calm, white tones, no clutter.",
        "bathroom": "Weak Moon — keep NW/W wet zones spotless.",
    },
    "Saturn": {
        "bedroom": "Weak Saturn — SW bedroom/heavy zone needs regular upkeep.",
    },
    "Jupiter": {
        "pooja": "Weak Jupiter — NE pooja/study must stay open and clean.",
        "pooja_room": "Weak Jupiter — NE pooja zone is critical for your chart.",
    },
}


def _norm_room_key(room_type: str) -> str:
    return (room_type or "").strip().lower().replace(" ", "_")


def _ordinal(n: int) -> str:
    """1 → 1st, 2 → 2nd, 4 → 4th (not 1th)."""
    if 11 <= (n % 100) <= 13:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _dedupe_dirs(directions: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for d in directions or []:
        key = (d or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def get_effective_room_rule(
    room_type: str,
    kundli_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classical GENERIC_ROOM_IDEAL + personalized overlay from the user's chart.
    Returns same shape as generic rule plus astro_* metadata for PDF/UI.
    """
    ctx = kundli_context or {}
    lagna = ctx.get("lagna")
    key = _norm_room_key(room_type)
    base = get_generic_room_rule(key) or get_generic_room_rule(
        _norm_room_key(key.replace("room", "").strip("_"))
    ) or {}
    base = copy.deepcopy(base) if base else {}

    classical_ideal = list(base.get("ideal") or [])
    classical_acc = list(base.get("acceptable") or [])
    avoid = list(base.get("avoid") or [])

    ideal = list(classical_ideal)
    acceptable = list(classical_acc)
    notes_en: List[str] = []
    notes_hn: List[str] = []
    notes_hi_dev: List[str] = []

    weak_set = set(ctx.get("weak_planets") or [])
    planets = ctx.get("planets") or []
    maha = (ctx.get("current_mahadasha") or "").strip()
    if maha:
        boosts = list((_DASHA_ROOM_BOOST.get(key) or {}).get(maha) or [])
        blocked = _NO_DASHA_BOOST_DIRS.get(key, set())
        boosts = [d for d in boosts if d not in blocked]
        # Weak Mars: South is Mars's direction — not ideal for kitchen; SE (Agni) stays universal.
        if key == "kitchen" and "Mars" in weak_set:
            boosts = [d for d in boosts if d != "South"]
        added_boosts: List[str] = []
        for d in boosts:
            if d not in avoid and d not in ideal:
                ideal.insert(0, d)
                added_boosts.append(d)
        if added_boosts:
            btxt = ", ".join(added_boosts[:3])
            notes_en.append(
                f"Your active {maha} Mahadasha supports {btxt} for this room "
                f"(not applied where classical Vastu forbids that zone)."
            )
            notes_hn.append(
                f"Chal rahi {maha} Mahadasha is room ke liye {btxt} ko support karti hai "
                f"(jahan shastriya Vastu mana karta hai wahan apply nahi)."
            )
            try:
                from astrovastu_report_i18n import DIR_LONG_HI
                btxt_hi = ", ".join(DIR_LONG_HI.get(d, d) for d in added_boosts[:3])
                notes_hi_dev.append(
                    f"चल रही {maha} महादशा इस कक्ष के लिए {btxt_hi} को सहारा देती है "
                    f"(जहाँ शास्त्रीय वास्तु मना करता है वहाँ लागू नहीं)।"
                )
            except Exception:
                notes_hi_dev.append(notes_hn[-1])

    # Bhava lord: ownership sign vs planet's actual placement in the natal chart.
    bhava = ROOM_BHAVA.get(key)
    if bhava and lagna and bhava_lord_placement:
        bl = bhava_lord_placement(lagna, bhava, planets)
        if bl:
            bdir = bl.get("placement_direction") or bl.get("direction")
            if bdir and bdir not in avoid and bdir not in ideal:
                ideal.insert(0, bdir)
            hs = bl.get("house_sign") or bl.get("sign")
            lord = bl.get("lord")
            ps = bl.get("placed_sign")
            ph = bl.get("placed_house")
            if ps:
                place_bit = f"{lord} is placed in {ps}"
                if ph:
                    place_bit += f" (house {ph})"
                notes_en.append(
                    f"Your {_ordinal(bhava)} house is {hs} (lord {lord}); {place_bit} in your chart. "
                    f"Placement-based overlay for this room: {bdir}."
                )
                notes_hn.append(
                    f"Aapka {_ordinal(bhava)} bhav {hs} hai (swami {lord}); chart mein {place_bit}. "
                    f"Placement overlay: {bdir}."
                )
                try:
                    from astrovastu_report_i18n import bhava_placement_note_hi_dev
                    notes_hi_dev.append(
                        bhava_placement_note_hi_dev(
                            bhava, hs, lord, ps, ph, bdir or "",
                        )
                    )
                except Exception:
                    notes_hi_dev.append(notes_hn[-1])
            else:
                notes_en.append(
                    f"Your {_ordinal(bhava)} house is {hs} (lord {lord}); "
                    f"classical overlay direction: {bdir}."
                )
                notes_hn.append(
                    f"Aapka {_ordinal(bhava)} bhav {hs} (swami {lord}); overlay: {bdir}."
                )
                try:
                    from astrovastu_report_i18n import bhava_placement_note_hi_dev
                    notes_hi_dev.append(
                        bhava_placement_note_hi_dev(bhava, hs, lord, None, None, bdir or "")
                    )
                except Exception:
                    notes_hi_dev.append(notes_hn[-1])

    lag_info = get_lagna_directions(lagna) if lagna else None
    if lag_info:
        fav = lag_info.get("favourable") or []
        added = []
        for d in fav:
            if d not in avoid and d not in ideal and d not in acceptable:
                acceptable.append(d)
                added.append(d)
        if added:
            notes_en.append(
                f"{lagna} Lagna ({lag_info.get('element', '')} sign) supports "
                f"{', '.join(fav[:2])} — listed as acceptable for your chart."
            )
            notes_hn.append(
                f"{lagna} Lagna {', '.join(fav[:2])} ko aapke chart ke liye supportive maanti hai."
            )

    for wp in ctx.get("weak_planets") or []:
        hint = (_WEAK_PLANET_ROOM_HINT.get(wp) or {}).get(key)
        if hint:
            notes_en.append(hint)
            notes_hn.append(hint.replace("Weak ", "Kamzor ").replace("needs", "zarurat"))
            notes_hi_dev.append(
                hint.replace("Weak ", "कमज़ोर ")
                .replace("needs regular upkeep", "नियमित देखभाल ज़रूरी")
                .replace("needs", "आवश्यकता")
            )

    if key == "kitchen" and "Mars" in weak_set:
        ideal = [d for d in ideal if d != "South"]
        notes_en.append(
            "Universal Vastu: kitchen South-East (Agni). With weak Mars, South is not recommended."
        )
        notes_hn.append(
            "Shastriya Vastu: kitchen South-East (Agni). Kamzor Mars me South kitchen primary zone na rakhein."
        )
        notes_hi_dev.append(
            "शास्त्रीय वास्तु: रसोई दक्षिण-पूर्व (अग्नि)। कमज़ोर मंगल में दक्षिण को प्राथमिक रसोई क्षेत्र न बनाएं।"
        )

    if key in ("pooja", "pooja_room"):
        ishta = ctx.get("ishta_devata") or {}
        if isinstance(ishta, dict):
            id_dir = (ishta.get("direction") or "").strip()
            if id_dir and id_dir not in avoid and id_dir not in ideal:
                ideal.insert(0, id_dir)
                notes_en.append(
                    f"Ishta Devata ({ishta.get('deity') or 'deity'}) favours {id_dir} for pooja in your chart."
                )
                notes_hn.append(
                    f"Ishta Devata ke liye {id_dir} aapke chart me pooja ke liye shubh hai."
                )

    if ctx.get("sade_sati", {}).get("active") if isinstance(ctx.get("sade_sati"), dict) else ctx.get("sade_sati"):
        notes_en.append("Sade Sati active — West/SW zones need extra care in your chart.")
        notes_hn.append("Sade Sati chal rahi hai — West/SW par vishesh dhyan.")
        notes_hi_dev.append("साढ़े साती चल रही है — पश्चिम/दक्षिण-पश्चिम पर विशेष ध्यान।")

    ideal = _dedupe_dirs(ideal)
    acceptable = _dedupe_dirs(acceptable)

    personalized = (
        ideal != classical_ideal
        or acceptable != classical_acc
        or bool(notes_en)
    )

    base["ideal"] = ideal
    base["acceptable"] = acceptable
    base["avoid"] = avoid
    base["classical_ideal"] = classical_ideal
    base["classical_acceptable"] = classical_acc
    base["astro_personalized"] = personalized
    base["astro_note_en"] = " ".join(notes_en[:3])
    base["astro_note_hn"] = " ".join(notes_hn[:3])
    base["astro_note_hi"] = " ".join(notes_hi_dev[:3])
    base["astro_note_hi_dev"] = base["astro_note_hi"]
    base["chart_lagna"] = lagna
    base["chart_mahadasha"] = maha
    return base
