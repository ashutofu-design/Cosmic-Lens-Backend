"""Social circle / friends chart evidence — D1 11H occupants + 11L + Mars + Mercury."""

from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

_BENEFIC = {1, 4, 5, 7, 9, 10, 11}
_DUSTHANA = {6, 8, 12}
_BENEFIC_PLANETS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFIC_PLANETS = frozenset({"Saturn", "Mars", "Rahu", "Ketu", "Sun"})


def reader(kundli: dict) -> KundliReader:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    return KundliReader(k)


def house_axis(r: KundliReader, house: int, label: str) -> str:
    asc_i = r.asc_index()
    sign = SIGNS[(asc_i + house - 1) % 12] if isinstance(asc_i, int) else "unknown"
    lord = r.house_lord(house)
    pl = r.planet(lord) if lord else None
    occ = r.occupants(house)
    return (
        f"{label}: H{house} sign {sign}; lord {lord or '?'} in H"
        f"{pl.get('house') if pl else '?'} sign {pl.get('sign') if pl else '?'}; "
        f"occupants={occ or 'none'}."
    )


def planet_line(r: KundliReader, name: str, role: str) -> str:
    p = r.planet(name) or {}
    house = p.get("house")
    sign = p.get("sign")
    if not house:
        return f"{name} ({role}): placement not available."
    h = int(house)
    if h == 11:
        tone = _planet_in_11h_tone(name)
    else:
        tone = _house_tone(h)
    return f"{name} ({role}): H{h} sign {sign} — {tone}."


def _house_tone(house: int) -> str:
    if house in _BENEFIC:
        return "supports friends/social circle themes"
    if house in _DUSTHANA:
        return "social circle needs boundaries and selective trust"
    return "mixed social tone — quality depends on effort and company"


def _planet_in_11h_tone(name: str) -> str:
    tones = {
        "Jupiter": "expansive, supportive friend circle; mentors and well-wishers",
        "Venus": "harmonious, fun social circle; friends through arts/comfort",
        "Mercury": "communicative network; many acquaintances and group chats",
        "Moon": "emotionally bonded friends; circle feels like family",
        "Mars": "active/volatile circle — loyal friends but friction or competition possible",
        "Sun": "status-driven network; influential friends but ego clashes possible",
        "Saturn": "fewer but serious friends; circle matures slowly, some distance",
        "Rahu": "unusual/wide network; foreign or unconventional friends",
        "Ketu": "detached from crowd; small circle or spiritual friends",
    }
    return tones.get(name, "shapes social-circle tone directly in 11H")


def occupants_in_11h_detail(r: KundliReader) -> list[str]:
    occ = r.occupants(11) or []
    if not occ:
        return [
            "11H has no planet occupants — judge circle mainly from 11L placement + Mars/Mercury."
        ]
    lines: list[str] = []
    for name in occ:
        pl = r.planet(name) or {}
        sign = pl.get("sign") or "?"
        lines.append(
            f"PLANET IN 11H: {name} in sign {sign} — {_planet_in_11h_tone(name)}."
        )
    return lines


def network_score(kundli: dict) -> tuple[int, str]:
    r = reader(kundli)
    score = 50

    for name in r.occupants(11) or []:
        if name in _BENEFIC_PLANETS:
            score += 11
        elif name == "Mars":
            score += 4
        elif name == "Sun":
            score += 3
        elif name in {"Saturn", "Rahu", "Ketu"}:
            score -= 9

    lord11 = r.house_lord(11)
    pl11 = r.planet(lord11) if lord11 else None
    if pl11 and pl11.get("house"):
        lh = int(pl11["house"])
        if lh in _BENEFIC:
            score += 12
        elif lh in _DUSTHANA:
            score -= 10

    mars = r.planet("Mars") or {}
    mh = mars.get("house")
    if mh:
        h = int(mh)
        if h == 11:
            score += 6
        elif h in _BENEFIC:
            score += 5
        elif h in _DUSTHANA:
            score -= 5

    merc = r.planet("Mercury") or {}
    merh = merc.get("house")
    if merh:
        h = int(merh)
        if h == 11:
            score += 8
        elif h in _BENEFIC:
            score += 4

    score = max(18, min(92, score))
    if score >= 72:
        label = "supportive social circle"
    elif score >= 55:
        label = "mixed but workable network"
    else:
        label = "circle needs careful selection"
    return score, label


def circle_snapshot(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 11, "Friends/social circle axis (11th house)"),
        *occupants_in_11h_detail(r),
        planet_line(r, "Mars", "energy/conflict karaka in friendships"),
        planet_line(r, "Mercury", "friends & network karaka (Budh)"),
        house_axis(r, 3, "Peers/casual friends axis (3rd house)"),
    ]
    lord11 = r.house_lord(11)
    if lord11:
        pl11 = r.planet(lord11) or {}
        lines.append(
            f"11L {lord11} in H{pl11.get('house') or '?'} sign {pl11.get('sign') or '?'} "
            f"— main driver when 11H is empty or mixed."
        )
    score, label = network_score(kundli)
    lines.append(f"Social-circle index: {score}/100 — {label}.")
    return lines[:10]
