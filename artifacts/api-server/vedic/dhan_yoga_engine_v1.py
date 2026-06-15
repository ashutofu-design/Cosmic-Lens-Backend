"""
dhan_yoga_engine_v1 — Dhan Yog from lord-pair links + Kubera + Budhaditya.

Lord-pair link (each pair counts once):
  conjunction (same house) OR mutual aspect OR parivartana (sign exchange).

Pairs: 1–2, 2–5, 2–9, 2–11, 5–9, 5–11, 9–11
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
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

# (house_a, house_b) sorted key → yoga labels
_LORD_PAIR_SPECS: Tuple[Tuple[int, int, str, str, str, str], ...] = (
    (
        1, 2,
        "Lagna-Dhana Yoga",
        "Lagna-Dhana Parivartana",
        "1st and 2nd lords together or in mutual aspect — self and wealth aligned.",
        "1st and 2nd lords exchange signs — identity and savings strongly linked.",
    ),
    (
        2, 5,
        "Dhana-Lakshmi Yoga",
        "Dhana-Lakshmi Parivartana",
        "2nd and 5th lords together or mutual aspect — savings and fortune blend.",
        "2nd and 5th lords exchange signs — wealth and luck from creativity/speculation.",
    ),
    (
        2, 9,
        "Dhana-Bhagya Yoga",
        "Dhana-Bhagya Parivartana",
        "2nd and 9th lords together or mutual aspect — wealth supported by fortune.",
        "2nd and 9th lords exchange signs — savings and dharma-luck loop.",
    ),
    (
        2, 11,
        "Dhana Yoga",
        "Dhana-Labha Parivartana",
        "2nd and 11th lords together or mutual aspect — strong income and savings flow.",
        "2nd and 11th lords exchange signs — savings and gains strongly linked.",
    ),
    (
        5, 9,
        "Lakshmi-Bhagya Yoga",
        "Lakshmi-Bhagya Parivartana",
        "5th and 9th lords together or mutual aspect — fortune and merit support wealth.",
        "5th and 9th lords exchange signs — luck and past merit reinforce gains.",
    ),
    (
        5, 11,
        "Lakshmi-Labha Yoga",
        "Lakshmi-Labha Parivartana",
        "5th and 11th lords together or mutual aspect — gains through merit and networks.",
        "5th and 11th lords exchange signs — creative fortune meets income streams.",
    ),
    (
        9, 11,
        "Bhagya-Labha Yoga",
        "Bhagya-Labha Parivartana",
        "9th and 11th lords together or mutual aspect — fortune and gains support each other.",
        "9th and 11th lords exchange signs — destiny and income reinforce each other.",
    ),
)


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _house_lord(asc_idx: int, house: int) -> str:
    return SIGN_LORD[SIGNS[(asc_idx + house - 1) % 12]]


def _planet_house(planets: List[dict], name: str) -> Optional[int]:
    p = _find_p(planets, name)
    if not p:
        return None
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _sign_idx(p: Optional[dict]) -> Optional[int]:
    if not p:
        return None
    sg = str(p.get("sign") or "")
    return SIGNS.index(sg) if sg in SIGNS else None


def _has_parivartana(planets: List[dict], asc_idx: int, house_a: int, house_b: int) -> bool:
    lord_a = _house_lord(asc_idx, house_a)
    lord_b = _house_lord(asc_idx, house_b)
    if lord_a == lord_b:
        return False
    ha = _planet_house(planets, lord_a)
    hb = _planet_house(planets, lord_b)
    return ha == house_b and hb == house_a


def _planet_aspects_sign(from_p: Optional[dict], target_sign_idx: Optional[int]) -> bool:
    if from_p is None or target_sign_idx is None:
        return False
    ps = _sign_idx(from_p)
    if ps is None:
        return False
    d = (target_sign_idx - ps + 12) % 12
    nm = str(from_p.get("name") or "")
    if d == 6:
        return True
    if nm == "Mars" and d in (3, 7):
        return True
    if nm == "Jupiter" and d in (4, 8):
        return True
    if nm in ("Rahu", "Ketu") and d in (4, 8):
        return True
    if nm == "Saturn" and d in (2, 9):
        return True
    return False


def _mutual_aspect(planets: List[dict], lord_a: str, lord_b: str) -> bool:
    pa, pb = _find_p(planets, lord_a), _find_p(planets, lord_b)
    sa, sb = _sign_idx(pa), _sign_idx(pb)
    if sa is None or sb is None:
        return False
    return _planet_aspects_sign(pa, sb) and _planet_aspects_sign(pb, sa)


def _lords_same_house(planets: List[dict], lord_a: str, lord_b: str) -> bool:
    ha = _planet_house(planets, lord_a)
    hb = _planet_house(planets, lord_b)
    return bool(ha and hb and ha == hb)


def _lord_pair_link(
    planets: List[dict],
    asc_idx: int,
    house_a: int,
    house_b: int,
) -> Optional[str]:
    """Return link type: parivartana | conjunction | mutual_aspect."""
    lord_a = _house_lord(asc_idx, house_a)
    lord_b = _house_lord(asc_idx, house_b)
    if lord_a == lord_b:
        return None
    if _has_parivartana(planets, asc_idx, house_a, house_b):
        return "parivartana"
    if _lords_same_house(planets, lord_a, lord_b):
        return "conjunction"
    if _mutual_aspect(planets, lord_a, lord_b):
        return "mutual_aspect"
    return None


def _yoga_from_lord_pair(
    planets: List[dict],
    asc_idx: int,
    house_a: int,
    house_b: int,
    yoga_name: str,
    parivartana_name: str,
    detail_link: str,
    detail_parivartana: str,
) -> Optional[Dict[str, Any]]:
    lord_a = _house_lord(asc_idx, house_a)
    lord_b = _house_lord(asc_idx, house_b)
    link = _lord_pair_link(planets, asc_idx, house_a, house_b)
    if not link:
        return None
    if link == "parivartana":
        return {
            "name": parivartana_name,
            "detail": detail_parivartana,
            "kind": "dhan",
            "planets": [lord_a, lord_b],
            "link": link,
            "houses": [house_a, house_b],
        }
    return {
        "name": yoga_name,
        "detail": detail_link,
        "kind": "dhan",
        "planets": [lord_a, lord_b],
        "link": link,
        "houses": [house_a, house_b],
    }


def scan_dhan_yogas(planets: List[dict], asc_idx: int) -> List[Dict[str, Any]]:
    """All dhan yogas: 7 lord-pair links + Kubera + Budhaditya."""
    yogas: List[Dict[str, Any]] = []

    for spec in _LORD_PAIR_SPECS:
        y = _yoga_from_lord_pair(planets, asc_idx, spec[0], spec[1], *spec[2:])
        if y:
            yogas.append(y)

    jup = _find_p(planets, "Jupiter")
    if jup and int(jup.get("house") or 0) in _STRONG:
        sg = str(jup.get("sign") or "")
        if sg in OWN.get("Jupiter", []) or sg == EXALT.get("Jupiter"):
            yogas.append({
                "name": "Kubera Yoga",
                "detail": "Jupiter dignified in kendra/trikona — wealth protection and steady growth.",
                "kind": "dhan",
                "planets": ["Jupiter"],
                "link": "karaka",
                "houses": [],
            })

    sun, merc = _find_p(planets, "Sun"), _find_p(planets, "Mercury")
    if sun and merc and sun.get("house") == merc.get("house"):
        if int(sun.get("house") or 0) in _STRONG:
            yogas.append({
                "name": "Budhaditya Yoga",
                "detail": "Sun and Mercury united in a strong house — sharp intelligence for earning.",
                "kind": "dhan",
                "planets": ["Sun", "Mercury"],
                "link": "conjunction",
                "houses": [],
            })

    return yogas
