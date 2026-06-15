"""
raj_yoga_engine_v1 — Raj Yog from kendra-trikona lord links + placements + Vipreet.

Lord-pair link (each pair counts once):
  conjunction OR mutual aspect OR parivartana between kendra (1/4/7/10) and trikona (1/5/9) lords.

Also: Vipreet Raj (dusthana lords together), Yogakaraka strong, trikona lord in 10H,
kendra lord in trikona house.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from vedic.dhan_yoga_engine_v1 import (
    _find_p,
    _house_lord,
    _lord_pair_link,
    _planet_house,
)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
EXALT = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}
OWN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}
_KENDRA = frozenset({1, 4, 7, 10})
_TRIKONA = frozenset({1, 5, 9})
_STRONG = _KENDRA | _TRIKONA
_DUSTHANA = frozenset({6, 8, 12})

# (kendra_h, trikona_h, yoga_name, parivartana_name, detail_link, detail_parivartana)
_KENDRA_TRIKONA_SPECS: Tuple[Tuple[int, int, str, str, str, str], ...] = (
    (
        10, 9,
        "Dharma-Karmadhipati Yoga",
        "Dharma-Karmadhipati Parivartana",
        "9th and 10th lords connected — fortune meets career, premier raj yoga.",
        "9th and 10th lords exchange signs — dharma and karma rise together.",
    ),
    (
        1, 9,
        "Lagna-Bhagya Raj Yoga",
        "Lagna-Bhagya Parivartana",
        "1st and 9th lords connected — self aligned with fortune and status.",
        "1st and 9th lords exchange signs — identity and luck reinforce authority.",
    ),
    (
        1, 5,
        "Lagna-Lakshmi Raj Yoga",
        "Lagna-Lakshmi Parivartana",
        "1st and 5th lords connected — merit and self-expression lift status.",
        "1st and 5th lords exchange signs — personal merit supports recognition.",
    ),
    (
        4, 9,
        "Kendra-Bhagya Raj Yoga",
        "Kendra-Bhagya Parivartana",
        "4th and 9th lords connected — comfort base and fortune build authority.",
        "4th and 9th lords exchange signs — stability and luck support rise.",
    ),
    (
        4, 5,
        "Kendra-Lakshmi Raj Yoga",
        "Kendra-Lakshmi Parivartana",
        "4th and 5th lords connected — property/comfort and merit aid status.",
        "4th and 5th lords exchange signs — foundation and creativity lift rank.",
    ),
    (
        7, 9,
        "Saptam-Bhagya Raj Yoga",
        "Saptam-Bhagya Parivartana",
        "7th and 9th lords connected — partnerships and fortune aid recognition.",
        "7th and 9th lords exchange signs — alliances and luck support authority.",
    ),
    (
        7, 5,
        "Saptam-Lakshmi Raj Yoga",
        "Saptam-Lakshmi Parivartana",
        "7th and 5th lords connected — partnerships and merit build status.",
        "7th and 5th lords exchange signs — deals and creativity lift recognition.",
    ),
    (
        10, 5,
        "Karma-Lakshmi Raj Yoga",
        "Karma-Lakshmi Parivartana",
        "10th and 5th lords connected — career and merit combine for authority.",
        "10th and 5th lords exchange signs — profession and past merit reinforce rank.",
    ),
    (
        10, 1,
        "Karma-Lagna Raj Yoga",
        "Karma-Lagna Parivartana",
        "10th and 1st lords connected — career and self-image rise together.",
        "10th and 1st lords exchange signs — work and identity reinforce status.",
    ),
    (
        4, 1,
        "Kendra-Lagna Raj Yoga",
        "Kendra-Lagna Parivartana",
        "4th and 1st lords connected — home base and self support authority.",
        "4th and 1st lords exchange signs — stability and identity lift recognition.",
    ),
    (
        7, 1,
        "Saptam-Lagna Raj Yoga",
        "Saptam-Lagna Parivartana",
        "7th and 1st lords connected — partnerships and self-image aid status.",
        "7th and 1st lords exchange signs — alliances and identity build authority.",
    ),
)

_YOGAKARAKA_BY_ASC: Dict[int, str] = {
    1: "Saturn",   # Taurus
    3: "Mars",     # Cancer
    4: "Mars",     # Leo
    6: "Saturn",   # Libra
    9: "Venus",    # Capricorn
    10: "Venus",   # Aquarius
}


def _yoga_key(y: Dict[str, Any]) -> Tuple[str, Tuple[str, ...], str]:
    return (
        str(y.get("name") or ""),
        tuple(sorted(str(p) for p in (y.get("planets") or []))),
        str(y.get("link") or ""),
    )


def _yoga_from_kendra_trikona_pair(
    planets: List[dict],
    asc_idx: int,
    k_h: int,
    t_h: int,
    yoga_name: str,
    parivartana_name: str,
    detail_link: str,
    detail_parivartana: str,
) -> Optional[Dict[str, Any]]:
    lord_k = _house_lord(asc_idx, k_h)
    lord_t = _house_lord(asc_idx, t_h)
    if lord_k == lord_t:
        return None
    link = _lord_pair_link(planets, asc_idx, k_h, t_h)
    if not link:
        return None
    if link == "parivartana":
        return {
            "name": parivartana_name,
            "detail": detail_parivartana,
            "kind": "raj",
            "planets": [lord_k, lord_t],
            "link": link,
            "houses": [k_h, t_h],
        }
    return {
        "name": yoga_name,
        "detail": detail_link,
        "kind": "raj",
        "planets": [lord_k, lord_t],
        "link": link,
        "houses": [k_h, t_h],
    }


def _scan_vipreet_raj_yogas(planets: List[dict], asc_idx: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    dust_lords = {_house_lord(asc_idx, h) for h in _DUSTHANA}
    by_house: Dict[int, List[str]] = {}
    for dl in dust_lords:
        h = _planet_house(planets, dl)
        if h in _DUSTHANA:
            by_house.setdefault(h, []).append(dl)
    seen: Set[Tuple[str, ...]] = set()
    for h, lords in by_house.items():
        if len(lords) < 2:
            continue
        key = tuple(sorted(lords))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "name": "Vipreet Raj Yoga",
            "detail": (
                f"Dusthana lords {', '.join(lords)} together in {h}th house — "
                "adversity can convert into unexpected rise."
            ),
            "kind": "raj",
            "planets": lords,
            "link": "conjunction",
            "houses": [h],
        })
    return out


def _scan_yogakaraka_raj(planets: List[dict], asc_idx: int) -> Optional[Dict[str, Any]]:
    yk = _YOGAKARAKA_BY_ASC.get(asc_idx)
    if not yk:
        return None
    p = _find_p(planets, yk)
    if not p:
        return None
    h = int(p.get("house") or 0)
    if h not in _STRONG:
        return None
    sg = str(p.get("sign") or "")
    if sg not in OWN.get(yk, []) and sg != EXALT.get(yk):
        return None
    return {
        "name": "Yogakaraka Yoga",
        "detail": (
            f"{yk} is yogakaraka for this ascendant, dignified in house {h} — "
            "exceptional support for status and authority."
        ),
        "kind": "raj",
        "planets": [yk],
        "link": "placement",
        "houses": [h],
    }


def _scan_trikona_lord_in_10th(planets: List[dict], asc_idx: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for t_h in (1, 5, 9):
        lord = _house_lord(asc_idx, t_h)
        if _planet_house(planets, lord) == 10:
            out.append({
                "name": "Trikona Lord in 10th",
                "detail": (
                    f"{lord} ({t_h}th lord) sits in the 10th house — "
                    "fortune/merit directly shapes career and public status."
                ),
                "kind": "raj",
                "planets": [lord],
                "link": "placement",
                "houses": [t_h, 10],
            })
    return out


def _scan_kendra_lord_in_trikona(planets: List[dict], asc_idx: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for k_h in (1, 4, 7, 10):
        lord = _house_lord(asc_idx, k_h)
        h = _planet_house(planets, lord)
        if h in _TRIKONA:
            out.append({
                "name": "Kendra Lord in Trikona",
                "detail": (
                    f"{lord} ({k_h}th lord) sits in {h}th trikona — "
                    "action houses feed merit and recognition."
                ),
                "kind": "raj",
                "planets": [lord],
                "link": "placement",
                "houses": [k_h, h],
            })
    return out


def _scan_gaja_kesari(planets: List[dict]) -> Optional[Dict[str, Any]]:
    moon = _find_p(planets, "Moon")
    jup = _find_p(planets, "Jupiter")
    if not moon or not jup:
        return None
    mh = int(moon.get("house") or 0)
    jh = int(jup.get("house") or 0)
    if not mh or not jh:
        return None
    kendra_from_moon = {((mh + o - 1) % 12) + 1 for o in (0, 3, 6, 9)}
    if jh not in kendra_from_moon:
        return None
    return {
        "name": "Gaja Kesari Yoga",
        "detail": (
            "Jupiter sits in a kendra from the Moon — wisdom, protection, "
            "and public respect support status rise."
        ),
        "kind": "raj",
        "planets": ["Moon", "Jupiter"],
        "link": "placement",
        "houses": [mh, jh],
    }


def scan_raj_yogas(planets: List[dict], asc_idx: int) -> List[Dict[str, Any]]:
    """All raj yogas: kendra-trikona links + Vipreet + Yogakaraka + placements."""
    yogas: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, Tuple[str, ...], str]] = set()

    def _add(y: Optional[Dict[str, Any]]) -> None:
        if not y:
            return
        key = _yoga_key(y)
        if key in seen:
            return
        seen.add(key)
        yogas.append(y)

    for spec in _KENDRA_TRIKONA_SPECS:
        _add(_yoga_from_kendra_trikona_pair(planets, asc_idx, *spec))

    for y in _scan_vipreet_raj_yogas(planets, asc_idx):
        _add(y)

    _add(_scan_yogakaraka_raj(planets, asc_idx))
    _add(_scan_gaja_kesari(planets))

    for y in _scan_trikona_lord_in_10th(planets, asc_idx):
        _add(y)

    for y in _scan_kendra_lord_in_trikona(planets, asc_idx):
        _add(y)

    return yogas
