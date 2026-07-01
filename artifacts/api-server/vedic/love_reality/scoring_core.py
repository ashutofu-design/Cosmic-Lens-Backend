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
DUAL_SIGNS = frozenset({"Gemini", "Virgo", "Sagittarius", "Pisces"})
COMBUST_THRESHOLDS = {
    "Moon": 12.0,
    "Mars": 17.0,
    "Mercury": 14.0,
    "Jupiter": 11.0,
    "Venus": 10.0,
    "Saturn": 15.0,
}

# Love-compat orb: ≤8° full weight; wider same-sign / loose = half penalty
ORB_TIGHT_DEG = 8.0
ORB_MAX_DEG = 10.0
ORB_SIGN_ONLY_WEIGHT = 0.5


def clamp(n: float, lo: float = 0, hi: float = 100) -> int:
    return int(max(lo, min(hi, round(n))))


def angular_distance_deg(lon_a: float, lon_b: float) -> float:
    d = abs((float(lon_a) - float(lon_b)) % 360.0)
    return 360.0 - d if d > 180.0 else d


def planet_longitude(reader: "KundliReader", name: str) -> float | None:
    p = reader.planet(name)
    if not p:
        return None
    lon = p.get("longitude")
    if isinstance(lon, (int, float)):
        return float(lon)
    deg = reader.planet_deg_in_sign(name)
    if deg is None:
        return None
    sign = p.get("sign")
    if not sign:
        return None
    return reader.sidx(sign) * 30.0 + float(deg)


def cross_chart_orb_distance(
    reader_a: "KundliReader",
    planet_a: str,
    reader_b: "KundliReader",
    planet_b: str,
) -> float | None:
    la = planet_longitude(reader_a, planet_a)
    lb = planet_longitude(reader_b, planet_b)
    if la is None or lb is None:
        return None
    return angular_distance_deg(la, lb)


def orb_penalty_multiplier(
    distance: float | None,
    *,
    sign_only: bool = False,
) -> float:
    """
    Scale affliction penalties by planetary closeness.
    sign_only=True → whole-sign aspect/occupancy without tight conjunction (0.5).
    """
    if sign_only:
        return ORB_SIGN_ONLY_WEIGHT
    if distance is None:
        return 1.0
    if distance <= ORB_TIGHT_DEG:
        return 1.0
    return ORB_SIGN_ONLY_WEIGHT


def scaled_penalty(base: float, multiplier: float) -> float:
    return round(base * multiplier, 1)


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

    def houses_ruled_by(self, planet: str) -> list[int]:
        """Whole-sign houses ruled by planet from lagna."""
        name = (planet or "").strip()
        if not name:
            return []
        return [h for h in range(1, 13) if self.house_lord(h) == name]

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

    def planet_deg_in_sign(self, name: str) -> float | None:
        p = self.planet(name)
        if not p:
            return None
        if isinstance(p.get("longitude"), (int, float)):
            return float(p["longitude"]) % 30.0
        deg = p.get("degreeInSign") or p.get("deg_in_sign")
        return float(deg) if deg is not None else None

    def planets_within_degrees(self, planet_a: str, planet_b: str, max_deg: float = 10.0) -> bool:
        pa, pb = self.planet(planet_a), self.planet(planet_b)
        if not pa or not pb:
            return False
        la, lb = pa.get("longitude"), pb.get("longitude")
        if isinstance(la, (int, float)) and isinstance(lb, (int, float)):
            d = abs(float(la) - float(lb))
            if d > 180.0:
                d = 360.0 - d
            return d <= max_deg
        if not self.share_house(planet_a, planet_b):
            return False
        if pa.get("sign") != pb.get("sign"):
            return False
        da, db = self.planet_deg_in_sign(planet_a), self.planet_deg_in_sign(planet_b)
        if da is None or db is None:
            return False
        return abs(da - db) <= max_deg

    def is_combust(self, planet_name: str) -> bool:
        planet = self.planet(planet_name)
        sun = self.planet("Sun")
        if not planet or not sun or planet_name in ("Sun", "Rahu", "Ketu"):
            return False
        la, ls = planet.get("longitude"), sun.get("longitude")
        if not isinstance(la, (int, float)) or not isinstance(ls, (int, float)):
            return False
        threshold = COMBUST_THRESHOLDS.get(planet_name, 12.0)
        d = abs(float(la) - float(ls))
        if d > 180.0:
            d = 360.0 - d
        return d <= threshold

    def is_retrograde(self, planet_name: str) -> bool:
        p = self.planet(planet_name)
        return bool(p and p.get("retrograde"))

    def d9_chart(self) -> dict[str, Any]:
        return (self.k.get("divisionalCharts") or {}).get("D9") or {}

    def d9_asc_index(self) -> int:
        d9 = self.d9_chart()
        si = d9.get("ascendantSignIndex")
        if si is not None:
            return int(si)
        asc = d9.get("ascendant")
        return self.sidx(asc) if isinstance(asc, str) else self.asc_index()

    def d9_house_lord(self, house: int) -> str:
        return SIGN_LORDS[(self.d9_asc_index() + house - 1) % 12]

    def d9_planet(self, name: str) -> dict | None:
        for p in self.d9_chart().get("planets") or []:
            if p.get("name") == name:
                return p
        return None

    def saturn_moon_connected(self) -> bool:
        if self.share_house("Saturn", "Moon"):
            return True
        moon_asps = self.aspects_planet("Moon")
        sat_asps = self.aspects_planet("Saturn")
        return "Saturn" in moon_asps or "Moon" in sat_asps

    def saturn_is_seventh_lord(self) -> bool:
        return self.house_lord(7) == "Saturn"

    def saturn_in_seventh_house(self) -> bool:
        sat = self.planet("Saturn")
        return bool(sat and sat.get("house") == 7)

    def is_dual_sign(self, sign_name: str | None) -> bool:
        return bool(sign_name and sign_name in DUAL_SIGNS)


def d9_cancels_debil(k: KundliReader, planet: str) -> bool:
    """Neech-bhang: D1 debilitated but D9 exalted or in own sign."""
    pl = k.planet(planet)
    if not pl:
        return False
    if k.dignity(planet, k.sidx(pl["sign"])) > -2:
        return False
    si = k.d9_sign_index(planet)
    if si is None:
        return False
    return k.dignity(planet, si) >= 1


def current_jupiter_sign() -> int | None:
    try:
        import swisseph as swe
        from datetime import datetime

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        now = datetime.utcnow()
        jd = swe.julday(
            now.year, now.month, now.day,
            now.hour + now.minute / 60.0 + now.second / 3600.0,
        )
        res, _ = swe.calc_ut(jd, swe.JUPITER, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        return int(res[0] / 30) % 12
    except Exception:
        return None


def _transit_jupiter_aspects_house(jupiter_sign: int, ref_asc: int, house: int) -> bool:
    tgt_sign = (ref_asc + house - 1) % 12
    d = (tgt_sign - jupiter_sign + 12) % 12
    return d in (0, 4, 6, 8)


def jupiter_transit_protects(r1: KundliReader, r2: KundliReader, jupiter_sign: int | None) -> bool:
    """Guru gochar on Lagna, 5th, or 7th axis — protective buffer for future bond."""
    if jupiter_sign is None:
        return False
    for r in (r1, r2):
        asc = r.asc_index()
        for house in (1, 5, 7):
            if _transit_jupiter_aspects_house(jupiter_sign, asc, house):
                return True
    return False


def dasha_lords_inimical(r1: KundliReader, r2: KundliReader) -> bool:
    """Shashtashtak / Dwidwadasa: running MD lords sit 6th, 8th, or 12th from each other."""
    l1, l2 = r1.dasha_triple()[0], r2.dasha_triple()[0]
    if not l1 or not l2:
        return False
    p1, p2 = r1.planet(l1), r2.planet(l2)
    if not p1 or not p2:
        return False
    s1, s2 = r1.sidx(p1["sign"]), r2.sidx(p2["sign"])
    for a, b in ((s1, s2), (s2, s1)):
        house = ((b - a) % 12) + 1
        if house in (6, 8, 12):
            return True
    return False


def future_confidence(total_afflictions: int) -> int:
    if total_afflictions <= 2:
        return 90
    return max(30, 90 - (total_afflictions * 5))
