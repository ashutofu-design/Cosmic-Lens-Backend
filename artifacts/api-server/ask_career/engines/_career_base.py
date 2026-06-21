"""Shared career chart evidence — D1/D10 inclination + 10H/6H/2H/11H axes."""
from __future__ import annotations

from typing import Any

from vedic.career_inclination_engine import compute_career_inclination, resolve_asc_idx
from vedic.love_reality.scoring_core import KundliReader, SIGNS


def load_inclination(kundli: dict) -> dict[str, Any]:
    k = dict(kundli or {})
    planets = list(k.get("planets") or [])
    asc = resolve_asc_idx(k)
    return compute_career_inclination(planets, asc, kundli=k)


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
        f"{label}: house {house} sign {sign}; lord {lord or '?'} in house "
        f"{pl.get('house') if pl else '?'} sign {pl.get('sign') if pl else '?'}; "
        f"occupants={occ or 'none'}."
    )


def career_snapshot(kundli: dict, inc: dict | None = None) -> list[str]:
    r = reader(kundli)
    inc = inc or load_inclination(kundli)
    lines = [
        house_axis(r, 10, "Career/profession axis (10th house)"),
        house_axis(r, 6, "Daily work/service axis (6th house)"),
        house_axis(r, 2, "Income/wealth axis (2nd house)"),
        house_axis(r, 11, "Gains/network axis (11th house)"),
    ]
    for planet, role in (
        ("Sun", "authority/leadership karak"),
        ("Saturn", "discipline/structure karak"),
        ("Mercury", "skills/communication karak"),
        ("Jupiter", "growth/advisory karak"),
        ("Mars", "drive/execution karak"),
        ("Venus", "creativity/commerce karak"),
    ):
        p = r.planet(planet) or {}
        if p.get("house"):
            lines.append(
                f"{planet} ({role}): house {p.get('house')} sign {p.get('sign')}."
            )
    if inc.get("path_verdict"):
        lines.append(f"Career-path synthesis: {inc.get('path_verdict')}.")
    if inc.get("atmakaraka"):
        lines.append(f"Atmakaraka (soul drive): {inc.get('atmakaraka')}.")
    if inc.get("amatyakaraka"):
        lines.append(f"Amatyakaraka (career executor): {inc.get('amatyakaraka')}.")
    return lines[:12]


def inclination_evidence(inc: dict, *, limit: int = 6, include_job_split: bool = True) -> list[str]:
    out: list[str] = []
    if include_job_split and inc.get("job_pct") is not None:
        out.append(
            f"Job vs business split: employment ~{inc.get('job_pct')}% / "
            f"business ~{inc.get('business_pct')}% ({inc.get('confidence', 'medium')} confidence)."
        )
    if inc.get("career_mode"):
        out.append(f"Career mode: {inc.get('career_mode')}.")
    for reason in inc.get("reasoning_summary") or []:
        if len(out) >= limit:
            break
        out.append(f"Inclination signal: {reason}")
    return out[:limit]


def trait_line(inc: dict, trait: str, *, high: str, low: str, mid: str | None = None) -> str:
    score = int((inc.get("psychology") or {}).get(trait) or 50)
    if score >= 62:
        level = high
    elif score <= 42:
        level = low
    else:
        level = mid or "moderate — grows with practice and right role"
    return f"{trait.replace('_', ' ').title()} score {score}/100 — {level}."


def subtype_hits(inc: dict, kind: str) -> list[str]:
    key = {"job": "job_subtypes", "biz": "business_subtypes", "comm": "commercial_subtypes"}.get(kind, "")
    return list(inc.get(key) or [])
