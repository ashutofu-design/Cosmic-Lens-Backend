"""Shared Vedic chart helpers for Love Reality engines (D1 + D9)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
DEBIL = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9, "Venus": 5, "Saturn": 0}
OWN = {
    "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
    "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10],
}
BENEFIC = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC = {"Saturn", "Mars", "Rahu", "Ketu"}
DUSTHANA = {6, 8, 12}
ROMANCE_HOUSES = {5, 7, 11}
MANGLIK_HOUSES = {1, 4, 7, 8, 12}


def clamp(n: float, lo: float = 0, hi: float = 100) -> int:
    return int(max(lo, min(hi, round(n))))


def risk_band_high_is_bad(score: int) -> str:
    """score 0-100 where higher = worse (breakup risk)."""
    if score <= 30:
        return "low"
    if score <= 55:
        return "medium"
    if score <= 75:
        return "high"
    return "very high"


def risk_band_high_is_good(score: int) -> str:
    """score 0-100 where higher = better (love, loyalty, return, future)."""
    if score >= 72:
        return "low"
    if score >= 52:
        return "medium"
    if score >= 35:
        return "high"
    return "very high"


def level_loyalty(score: int) -> str:
    if score >= 72:
        return "high"
    if score >= 52:
        return "moderate"
    if score >= 35:
        return "unstable"
    return "risky"


def level_return(score: int) -> str:
    if score < 28:
        return "unlikely"
    if score < 48:
        return "possible"
    if score < 68:
        return "strong"
    return "very strong"


def level_future(score: int) -> str:
    if score >= 75:
        return "thriving — long-term trajectory"
    if score >= 58:
        return "growing — effort can deepen the bond"
    if score >= 42:
        return "mixed — stability depends on timing"
    if score >= 28:
        return "strained — emotional fatigue building"
    return "fading — closure energy stronger than growth"


@dataclass
class KundliReader:
    k: dict[str, Any]

    @property
    def name(self) -> str:
        return self.k.get("name") or "Partner"

    def sidx(self, sign_name: str) -> int:
        try:
            return SIGNS.index(sign_name)
        except ValueError:
            return 0

    def planet(self, name: str) -> dict | None:
        for p in self.k.get("planets") or []:
            if p.get("name") == name:
                return p
        return None

    def d9(self, name: str) -> dict | None:
        d9 = (self.k.get("divisionalCharts") or {}).get("D9") or {}
        for p in d9.get("planets") or []:
            if p.get("name") == name:
                return p
        return None

    def dignity(self, planet: str, sign_index: int) -> int:
        if EXALT.get(planet) == sign_index:
            return 2
        if DEBIL.get(planet) == sign_index:
            return -2
        if sign_index in OWN.get(planet, []):
            return 1
        return 0

    def dignity_word(self, d: int) -> str:
        return {2: "exalted", 1: "own-sign", 0: "neutral", -2: "debilitated"}.get(d, "neutral")

    def asc_index(self) -> int:
        return self.sidx(self.k.get("ascendant") or "Aries")

    def house_lord(self, house: int) -> str:
        return SIGN_LORDS[(self.asc_index() + house - 1) % 12]

    def lord_in_house(self, planet: str) -> int | None:
        pl = self.planet(planet)
        return pl.get("house") if pl else None

    def share_house(self, planet_a: str, planet_b: str) -> bool:
        pa, pb = self.planet(planet_a), self.planet(planet_b)
        if not pa or not pb:
            return False
        return pa.get("house") is not None and pa.get("house") == pb.get("house")

    def d9_sign_index(self, name: str) -> int | None:
        p = self.d9(name)
        if not p:
            return None
        si = p.get("signIndex")
        if si is not None:
            return int(si)
        sign = p.get("sign")
        return self.sidx(sign) if isinstance(sign, str) else None

    def occupants(self, house: int) -> list[str]:
        return [p["name"] for p in self.k.get("planets") or [] if p.get("house") == house]

    def aspects_planet(self, target: str) -> list[str]:
        tgt = self.planet(target)
        if not tgt:
            return []
        ts = self.sidx(tgt["sign"])
        hits: list[str] = []
        for p in self.k.get("planets") or []:
            if p["name"] == target:
                continue
            ps = self.sidx(p["sign"])
            d = (ts - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":
                ok = ok or d in (3, 7)
            if p["name"] == "Jupiter":
                ok = ok or d in (4, 8)
            if p["name"] == "Saturn":
                ok = ok or d in (2, 9)
            if p["name"] in ("Rahu", "Ketu"):
                ok = ok or d in (4, 8)
            if ok:
                hits.append(p["name"])
        return hits

    def aspects_house(self, house: int) -> list[str]:
        tgt_sign = (self.asc_index() + house - 1) % 12
        hits: list[str] = []
        for p in self.k.get("planets") or []:
            ps = self.sidx(p["sign"])
            d = (tgt_sign - ps + 12) % 12
            ok = d == 6
            if p["name"] == "Mars":
                ok = ok or d in (3, 7)
            if p["name"] == "Jupiter":
                ok = ok or d in (4, 8)
            if p["name"] == "Saturn":
                ok = ok or d in (2, 9)
            if p["name"] in ("Rahu", "Ketu"):
                ok = ok or d in (4, 8)
            if ok:
                hits.append(p["name"])
        return hits

    def dasha_triple(self) -> tuple[str | None, str | None, str | None]:
        cd = self.k.get("currentDasha") or {}
        return cd.get("maha"), cd.get("antar"), cd.get("pratyantar")

    def manglik(self) -> bool:
        mars = self.planet("Mars")
        return bool(mars and mars.get("house") in MANGLIK_HOUSES)
