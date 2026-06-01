"""
Deterministic lifelong career inclination engine (D1 + D10).

Static tendency only — no dasha/transit timing.
D1 = nature (75–80%); D10 = execution validation (confidence + small nudge).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ALIASES = {
    "mesh": 0, "mesha": 0, "aries": 0,
    "vrish": 1, "vrishabha": 1, "vrushabh": 1, "taurus": 1,
    "mithun": 2, "mithuna": 2, "gemini": 2,
    "kark": 3, "karka": 3, "cancer": 3,
    "simh": 4, "simha": 4, "leo": 4,
    "kanya": 5, "virgo": 5,
    "tula": 6, "libra": 6,
    "vrishchik": 7, "vrishchika": 7, "scorpio": 7,
    "dhanu": 8, "dhanus": 8, "sagittarius": 8,
    "makar": 9, "makara": 9, "capricorn": 9,
    "kumbh": 10, "kumbha": 10, "aquarius": 10,
    "meen": 11, "meena": 11, "pisces": 11,
}
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
EXALT = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}
OWN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}
MOOLTRIKONA = {
    "Sun": "Leo", "Moon": "Taurus", "Mars": "Aries", "Mercury": "Virgo",
    "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Aquarius",
}
JOB_PLANETS = frozenset({"Sun", "Saturn", "Jupiter"})
BIZ_PLANETS = frozenset({"Mercury", "Mars", "Rahu", "Venus"})
STRUCTURE_PLANETS = frozenset({"Saturn", "Sun", "Jupiter"})
MALEFIC = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})
DUSTHANA = frozenset({6, 8, 12})

_PLANET_CAP = 4
_DIMINISH = 0.72


@dataclass
class Signal:
    axis: str
    weight: float
    source: str
    planet: Optional[str] = None


@dataclass
class ScoreLedger:
    job: float = 0.0
    business: float = 0.0
    commercial: float = 0.0
    freelance: float = 0.0
    structure: float = 0.0
    independence: float = 0.0
    execution: float = 0.0
    affliction: float = 0.0
    instability: float = 0.0
    stability_penalty: float = 0.0
    signals: List[Signal] = field(default_factory=list)
    planet_hits: Dict[str, int] = field(default_factory=dict)

    def add(self, sig: Signal) -> None:
        key = f"{sig.axis}:{sig.planet or 'general'}"
        n = self.planet_hits.get(key, 0)
        if n >= _PLANET_CAP:
            return
        w = sig.weight * (_DIMINISH ** n)
        self.planet_hits[key] = n + 1
        axis_map = {
            "job": "job",
            "business": "business",
            "commercial": "commercial",
            "freelance": "freelance",
            "structure": "structure",
            "independence": "independence",
            "execution": "execution",
        }
        attr = axis_map.get(sig.axis)
        if attr:
            setattr(self, attr, getattr(self, attr) + w)
        if len(self.signals) < 32:
            self.signals.append(sig)


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _sign_idx(name: str) -> int:
    try:
        return SIGNS.index(name)
    except ValueError:
        alias = SIGN_ALIASES.get((name or "").strip().lower())
        return alias if alias is not None else 0


def resolve_asc_idx(kundli: Optional[dict]) -> int:
    if not kundli:
        return 0
    if kundli.get("ascendantSignIndex") is not None:
        return int(kundli["ascendantSignIndex"]) % 12
    deg = kundli.get("ascendantDeg")
    if deg is not None:
        try:
            return int(float(deg) / 30.0) % 12
        except (TypeError, ValueError):
            pass
    asc = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    if isinstance(asc, str):
        if asc in SIGNS:
            return SIGNS.index(asc)
        alias = SIGN_ALIASES.get(asc.strip().lower())
        if alias is not None:
            return alias
    return 0


def ensure_planet_houses(planets: List[dict], asc_idx: int) -> List[dict]:
    for p in planets:
        if p.get("house"):
            continue
        sign = p.get("sign") or ""
        if sign in SIGNS:
            si = SIGNS.index(sign)
            p["house"] = (si - asc_idx) % 12 + 1
        elif isinstance(sign, str):
            si = SIGN_ALIASES.get(sign.strip().lower())
            if si is not None:
                p["house"] = (si - asc_idx) % 12 + 1
                p["sign"] = SIGNS[si]
    return planets


class CareerChart:
    def __init__(self, planets: List[dict], asc_idx: int, kundli: Optional[dict] = None):
        self.planets = planets or []
        self.asc_idx = asc_idx
        self.kundli = kundli or {}
        self._by_name = {p["name"]: p for p in self.planets if p.get("name")}
        d10 = (self.kundli.get("divisionalCharts") or {}).get("D10") or {}
        self.d10_planets: List[dict] = d10.get("planets") or []
        self._d10_by_name = {p["name"]: p for p in self.d10_planets if p.get("name")}

    def p(self, name: str, d10: bool = False) -> Optional[dict]:
        return (self._d10_by_name if d10 else self._by_name).get(name)

    def lord(self, house: int) -> str:
        return SIGN_LORD[SIGNS[(self.asc_idx + house - 1) % 12]]

    def occupants(self, house: int, d10: bool = False) -> List[str]:
        src = self.d10_planets if d10 else self.planets
        return [p["name"] for p in src if p.get("house") == house]

    def dignity_score(self, planet: str, d10: bool = False) -> float:
        pl = self.p(planet, d10=d10)
        if not pl:
            return 1.0
        sign = pl.get("sign") or ""
        if sign == EXALT.get(planet):
            base = 1.28
        elif sign == DEBIL.get(planet):
            base = 0.72
        elif sign in OWN.get(planet, []):
            base = 1.14
        elif sign == MOOLTRIKONA.get(planet):
            base = 1.18
        else:
            base = 1.0
        if pl.get("combust"):
            base *= 0.86
        if bool(pl.get("retrograde")) and planet not in ("Rahu", "Ketu"):
            base *= 1.04 if planet in ("Saturn", "Mars") else 0.92
        return _clamp(base, 0.65, 1.35)

    def is_strong(self, planet: str, d10: bool = False) -> bool:
        return self.dignity_score(planet, d10=d10) >= 1.05

    def is_weak(self, planet: str, d10: bool = False) -> bool:
        return self.dignity_score(planet, d10=d10) < 0.88

    def _aspect_distance(self, from_sign: str, to_sign: str) -> int:
        return (_sign_idx(to_sign) - _sign_idx(from_sign) + 12) % 12

    def aspects_on_house(self, house: int, d10: bool = False) -> List[Tuple[str, float]]:
        tgt_sign = SIGNS[(self.asc_idx + house - 1) % 12]
        hits: List[Tuple[str, float]] = []
        src = self.d10_planets if d10 else self.planets
        for pl in src:
            nm = pl.get("name")
            if not nm:
                continue
            ps = pl.get("sign") or ""
            d = self._aspect_distance(ps, tgt_sign)
            ok = d == 6
            if nm == "Mars":
                ok = ok or d in (3, 7)
            elif nm == "Jupiter":
                ok = ok or d in (4, 8)
            elif nm == "Saturn":
                ok = ok or d in (2, 9)
            elif nm in ("Rahu", "Ketu"):
                ok = ok or d in (4, 8)
            if ok:
                orb = 1.0 if d in (6, 7) else 0.82
                hits.append((nm, orb * self.dignity_score(nm, d10=d10)))
        return hits

    def aspects_on_planet(self, target: str, d10: bool = False) -> List[Tuple[str, float]]:
        tgt = self.p(target, d10=d10)
        if not tgt:
            return []
        ts = tgt.get("sign") or ""
        hits: List[Tuple[str, float]] = []
        src = self.d10_planets if d10 else self.planets
        for pl in src:
            nm = pl.get("name")
            if not nm or nm == target:
                continue
            ps = pl.get("sign") or ""
            d = self._aspect_distance(ps, ts)
            ok = d == 6
            if nm == "Mars":
                ok = ok or d in (3, 7)
            elif nm == "Jupiter":
                ok = ok or d in (4, 8)
            elif nm == "Saturn":
                ok = ok or d in (2, 9)
            elif nm in ("Rahu", "Ketu"):
                ok = ok or d in (4, 8)
            if ok:
                orb = 1.0 if d in (6, 7) else 0.82
                hits.append((nm, orb * self.dignity_score(nm, d10=d10)))
        return hits

    def conjunct(self, a: str, b: str, d10: bool = False) -> bool:
        pa, pb = self.p(a, d10=d10), self.p(b, d10=d10)
        if not pa or not pb:
            return False
        return pa.get("house") is not None and pa.get("house") == pb.get("house")


def _score_mercury_by_house(chart: CareerChart, ledger: ScoreLedger) -> None:
    merc = chart.p("Mercury")
    if not merc:
        return
    h = int(merc.get("house") or 0)
    m = chart.dignity_score("Mercury")
    if h in (3, 7, 11):
        ledger.add(Signal("business", 11 * m, "Mercury in 3/7/11 — trade/commerce", "Mercury"))
        ledger.add(Signal("independence", 4 * m, "Mercury — skill monetization", "Mercury"))
    elif h in (6, 10):
        ledger.add(Signal("commercial", 12 * m, "Mercury in 6/10 — analyst/consultant profession", "Mercury"))
        ledger.add(Signal("job", 5 * m, "Mercury in 6/10 — corporate/service delivery", "Mercury"))
    elif h == 1:
        ledger.add(Signal("freelance", 6 * m, "Mercury in 1st — independent professional", "Mercury"))


def _apply_commercial_profession_layer(chart: CareerChart, ledger: ScoreLedger) -> None:
    """Doctor, lawyer, CA, consultant, architect — not pure job or pure business."""
    lord_10 = chart.lord(10)
    l10 = chart.p(lord_10)
    str_mod = chart.dignity_score(lord_10) if l10 else 1.0

    for nm in chart.occupants(6):
        mod = chart.dignity_score(nm)
        if nm in ("Mercury", "Jupiter"):
            ledger.add(Signal("commercial", 9 * mod, f"{nm} in 6th — professional service craft", nm))
        if nm == "Sun":
            ledger.add(Signal("job", 6 * mod, f"{nm} in 6th — institutional service", nm))

    for nm in chart.occupants(10):
        mod = chart.dignity_score(nm)
        if nm in ("Mercury", "Jupiter", "Venus"):
            ledger.add(Signal("commercial", 8 * mod, f"{nm} in 10th — commercial profession visibility", nm))

    if chart.conjunct("Mercury", "Jupiter"):
        ledger.add(Signal("commercial", 14, "Mercury–Jupiter — law/advisory/teaching profession", "Mercury"))
    if chart.conjunct("Mercury", "Venus"):
        ledger.add(Signal("commercial", 10, "Mercury–Venus — design/media profession", "Mercury"))
    if chart.conjunct("Mercury", "Saturn"):
        ledger.add(Signal("commercial", 11, "Mercury–Saturn — CA/audit/technical profession", "Mercury"))

    if l10 and int(l10.get("house") or 0) in (6, 10) and lord_10 in ("Mercury", "Jupiter"):
        ledger.add(Signal("commercial", 10 * str_mod, f"10L {lord_10} in professional house — specialist path", lord_10))

    for nm, orb in chart.aspects_on_planet(lord_10):
        if nm in ("Mercury", "Jupiter"):
            ledger.add(Signal("commercial", 6 * orb, f"{nm} aspects 10L — advisory/commercial craft", nm))


def _apply_execution_layer(chart: CareerChart, ledger: ScoreLedger) -> None:
    sat = chart.p("Saturn")
    mars = chart.p("Mars")
    merc = chart.p("Mercury")
    moon = chart.p("Moon")
    rahu = chart.p("Rahu")
    if sat and mars and chart.is_strong("Saturn") and chart.is_strong("Mars"):
        ledger.add(Signal("execution", 14, "Saturn+Mars strength — sustained execution", "Saturn"))
    if merc and sat and chart.is_strong("Mercury"):
        ledger.add(Signal("execution", 12, "Mercury+Saturn — planning and delivery", "Mercury"))
    if rahu and sat and int((rahu.get("house") or 0)) in (7, 10, 11):
        ledger.add(Signal("execution", 10, "Rahu+Saturn pattern — scalable operations", "Rahu"))
    if moon and sat and chart.is_strong("Moon"):
        ledger.add(Signal("execution", 9, "Moon+Saturn stability — consistency", "Moon"))
    elif moon and chart.is_weak("Moon"):
        ledger.stability_penalty += 10


def _apply_freelance_layer(chart: CareerChart, ledger: ScoreLedger) -> None:
    """Independence without full business risk — consulting/freelance."""
    indep = ledger.independence
    struct = ledger.structure
    if indep >= 12 and struct >= 8 and ledger.business < ledger.job + 15:
        ledger.add(Signal("freelance", 10, "High independence with structure — freelance/consulting fit", None))
    merc = chart.p("Mercury")
    if merc and int(merc.get("house") or 0) in (3, 11) and chart.is_strong("Mercury"):
        ledger.add(Signal("freelance", 9, "Mercury in 3/11 — independent skilled income", "Mercury"))
    l10 = chart.p(chart.lord(10))
    if l10 and int(l10.get("house") or 0) in (3, 11):
        ledger.add(Signal("freelance", 8, "10L in 3/11 — portfolio/consulting career", chart.lord(10)))


def _apply_placement_layer(chart: CareerChart, ledger: ScoreLedger) -> None:
    lord_10 = chart.lord(10)
    lord_7 = chart.lord(7)
    lord_6 = chart.lord(6)
    l10 = chart.p(lord_10)
    str_mod = chart.dignity_score(lord_10) if l10 else 1.0

    if lord_10 == lord_7 and l10:
        h_dl = int(l10.get("house") or 0)
        if h_dl == 7:
            ledger.add(Signal("business", 16 * str_mod, f"Dual lord {lord_10} in 7th — commerce-led career", lord_10))
            ledger.add(Signal("commercial", 6 * str_mod, "Dual lord 7th — client professional work", lord_10))
        elif h_dl == 10:
            ledger.add(Signal("commercial", 12 * str_mod, f"Dual lord {lord_10} in 10th — professional specialist", lord_10))
            ledger.add(Signal("job", 8 * str_mod, "Dual lord 10th — visible career role", lord_10))

    moon = chart.p("Moon")
    if moon and int(moon.get("house") or 0) == 7:
        m = chart.dignity_score("Moon")
        ledger.add(Signal("business", 7 * m, "Moon in 7th — public/partnership interface", "Moon"))
        ledger.add(Signal("commercial", 4 * m, "Moon in 7th — client-facing profession", "Moon"))

    if l10:
        h = int(l10.get("house") or 0)
        if h == 6:
            ledger.add(Signal("job", 14 * str_mod, f"10L in 6th — service/employment karma", lord_10))
            ledger.add(Signal("commercial", 6 * str_mod, "10L in 6th — specialist service craft", lord_10))
            ledger.add(Signal("structure", 8 * str_mod, "10L in 6th — institutional discipline", lord_10))
        elif h == 8:
            ledger.instability += 5
            ledger.add(Signal("commercial", 9 * str_mod, "10L in 8th — research/finance/crisis professions", lord_10))
            if lord_10 in ("Mercury", "Saturn"):
                ledger.add(Signal("commercial", 5 * str_mod, "10L in 8th — analytical/finance specialist", lord_10))
            else:
                ledger.add(Signal("job", 4 * str_mod, "10L in 8th — institutional research roles", lord_10))
        elif h == 12:
            ledger.instability += 7
            ledger.affliction += 4
        elif h == 7:
            ledger.add(Signal("business", 14 * str_mod, "10L in 7th — trade/partnership", lord_10))
            ledger.add(Signal("independence", 6 * str_mod, "10L in 7th — client autonomy", lord_10))
        elif h in (1, 2, 11):
            ledger.add(Signal("business", 11 * str_mod, f"10L in {h}th — self/wealth income", lord_10))
            ledger.add(Signal("independence", 8 * str_mod, f"10L in {h}th — self-directed path", lord_10))
        elif h == 10:
            ledger.add(Signal("job", 9 * str_mod, "10L in 10th — professional visibility", lord_10))
            ledger.add(Signal("commercial", 7 * str_mod, "10L in 10th — authority profession", lord_10))

        if lord_10 in JOB_PLANETS:
            ledger.add(Signal("job", 7 * str_mod, f"10L {lord_10} — structured delivery", lord_10))
        elif lord_10 in BIZ_PLANETS:
            ledger.add(Signal("business", 8 * str_mod, f"10L {lord_10} — commercial delivery", lord_10))

    for nm in chart.occupants(6):
        mod = chart.dignity_score(nm)
        if nm in ("Saturn", "Sun"):
            ledger.add(Signal("job", 9 * mod, f"{nm} in 6th — employment/service", nm))
            ledger.add(Signal("structure", 6 * mod, f"{nm} in 6th — duty systems", nm))
        if nm == "Mercury":
            ledger.add(Signal("commercial", 8 * mod, "Mercury in 6th — analyst/consultant (not raw business)", "Mercury"))
        if nm == "Mars":
            ledger.add(Signal("job", 5 * mod, "Mars in 6th — competitive workplace", "Mars"))

    for nm in chart.occupants(7):
        mod = chart.dignity_score(nm)
        if nm in ("Mercury", "Venus", "Rahu"):
            ledger.add(Signal("business", 10 * mod, f"{nm} in 7th — commerce/trade", nm))
            if nm == "Rahu":
                ledger.add(Signal("independence", 8 * mod, "Rahu in 7th — unconventional income", "Rahu"))
        if nm == "Jupiter":
            ledger.add(Signal("commercial", 9 * mod, "Jupiter in 7th — advisory/consulting/public dealing", "Jupiter"))
            ledger.add(Signal("job", 4 * mod, "Jupiter in 7th — guided professional roles", "Jupiter"))
        if nm == "Moon":
            ledger.add(Signal("commercial", 5 * mod, "Moon in 7th — public-facing profession", "Moon"))
        if nm == "Saturn":
            if chart.is_strong("Saturn"):
                ledger.add(Signal("commercial", 7 * mod, "Strong Saturn in 7th — long-term structured partnerships", "Saturn"))
                ledger.add(Signal("structure", 6 * mod, "Saturn in 7th — compliance-heavy ventures", "Saturn"))
            else:
                ledger.add(Signal("job", 5 * mod, "Weak Saturn in 7th — dependent/slow partnerships", "Saturn"))
                ledger.affliction += 3

    for nm in chart.occupants(10):
        mod = chart.dignity_score(nm)
        if nm in JOB_PLANETS:
            ledger.add(Signal("job", 8 * mod, f"{nm} in 10th — authority/institution", nm))
            ledger.add(Signal("structure", 6 * mod, f"{nm} in 10th — system career", nm))
        if nm in BIZ_PLANETS and nm != "Mercury":
            ledger.add(Signal("business", 8 * mod, f"{nm} in 10th — commercial visibility", nm))
            if nm == "Rahu":
                ledger.add(Signal("independence", 7 * mod, "Rahu in 10th — non-traditional path", "Rahu"))

    _score_mercury_by_house(chart, ledger)

    sat = chart.p("Saturn")
    if sat and int(sat.get("house") or 0) in (6, 10, 11):
        m = chart.dignity_score("Saturn")
        ledger.add(Signal("job", 10 * m, "Saturn in 6/10/11 — long-haul structured work", "Saturn"))
        ledger.add(Signal("structure", 11 * m, "Saturn — system endurance", "Saturn"))

    rahu = chart.p("Rahu")
    if rahu and int(rahu.get("house") or 0) in (7, 10, 11):
        m = chart.dignity_score("Rahu")
        ledger.add(Signal("business", 12 * m, "Rahu in 7/10/11 — enterprise/commerce drive", "Rahu"))
        ledger.add(Signal("independence", 9 * m, "Rahu — autonomy appetite", "Rahu"))

    sun = chart.p("Sun")
    if sun and int(sun.get("house") or 0) in (10, 11):
        m = chart.dignity_score("Sun")
        ledger.add(Signal("job", 9 * m, "Sun in 10/11 — organizational authority", "Sun"))
        ledger.add(Signal("structure", 7 * m, "Sun — authority tolerance", "Sun"))

    mars = chart.p("Mars")
    if mars:
        mh = int(mars.get("house") or 0)
        m = chart.dignity_score("Mars")
        if mh in (3, 7):
            ledger.add(Signal("business", 6 * m, f"Mars in {mh} — enterprise drive", "Mars"))
            ledger.add(Signal("independence", 7 * m, "Mars — self-start energy", "Mars"))
        elif mh == 10:
            ledger.add(Signal("execution", 6 * m, "Mars in 10th — execution in career", "Mars"))

    if lord_7 in ("Mercury", "Venus") and any(
        chart.conjunct(lord_7, x) for x in ("Mercury", "Rahu", "Venus")
    ):
        ledger.add(Signal("business", 7, "7th-lord commerce yoga", lord_7))
    if lord_6 in ("Saturn", "Sun") and chart.occupants(6):
        ledger.add(Signal("job", 5, "6th-lord service yoga", lord_6))


def _apply_d10_readout(chart: CareerChart) -> Tuple[float, float, float, float]:
    """D10 lean for alignment only — does not heavily rewrite D1 nature."""
    d10_job = d10_biz = d10_comm = 0.0
    if not chart.d10_planets:
        return 0.0, 0.0, 0.0, 0.0

    for nm in chart.occupants(10, d10=True):
        mod = chart.dignity_score(nm, d10=True)
        if nm in JOB_PLANETS:
            d10_job += 7 * mod
        if nm in BIZ_PLANETS and nm != "Mercury":
            d10_biz += 7 * mod
        if nm in ("Mercury", "Jupiter", "Venus"):
            d10_comm += 6 * mod

    for pl in chart.d10_planets:
        if pl.get("name") == chart.lord(10):
            h = int(pl.get("house") or 0)
            mod = chart.dignity_score(chart.lord(10), d10=True)
            if h in (6, 10):
                d10_job += 6 * mod
                d10_comm += 4 * mod
            elif h in (7, 11):
                d10_biz += 6 * mod
            break
    return d10_job, d10_biz, d10_comm, d10_job + d10_biz + d10_comm


def _apply_aspect_layer(chart: CareerChart, ledger: ScoreLedger) -> None:
    for nm, orb in chart.aspects_on_house(10):
        if nm == "Saturn":
            ledger.add(Signal("job", 7 * orb, "Saturn aspects 10th — structure", "Saturn"))
            ledger.add(Signal("structure", 8 * orb, "Saturn on 10th", "Saturn"))
        elif nm == "Jupiter":
            ledger.add(Signal("commercial", 6 * orb, "Jupiter aspects 10th — advisory profession", "Jupiter"))
        elif nm in ("Rahu", "Ketu"):
            ledger.add(Signal("independence", 4 * orb, f"{nm} on 10th — unconventional pull", nm))
            ledger.instability += 2 * orb
        elif nm == "Mars":
            ledger.add(Signal("execution", 5 * orb, "Mars aspects 10th — drive", "Mars"))

    lord_10 = chart.lord(10)
    for nm, orb in chart.aspects_on_planet(lord_10):
        if nm in MALEFIC and nm != "Saturn":
            ledger.affliction += 3 * orb
        if nm == "Jupiter":
            ledger.add(Signal("commercial", 5 * orb, "Jupiter aspects 10L — supported profession", "Jupiter"))
        if nm == "Rahu":
            ledger.add(Signal("business", 5 * orb, "Rahu aspects 10L — commercial disruption", "Rahu"))
        if nm == "Ketu":
            ledger.instability += 4 * orb

    for nm, orb in chart.aspects_on_planet("Mercury"):
        if nm == "Rahu":
            ledger.add(Signal("business", 6 * orb, "Rahu aspects Mercury — digital/commercial mind", "Rahu"))
        if nm in ("Saturn", "Mars"):
            ledger.add(Signal("commercial", 4 * orb, f"{nm} aspects Mercury — technical profession", nm))

    if chart.conjunct("Rahu", "Moon"):
        ledger.instability += 5
        ledger.add(Signal("independence", 5, "Rahu with Moon — restless income drive", "Rahu"))
    if chart.conjunct("Rahu", "Mercury"):
        ledger.add(Signal("business", 6, "Rahu with Mercury — startup/trading bias", "Rahu"))
    if chart.conjunct("Ketu", lord_10) or any(n == "Ketu" for n, _ in chart.aspects_on_planet(lord_10)):
        ledger.instability += 5


def _apply_affliction_layer(chart: CareerChart, ledger: ScoreLedger) -> None:
    lord_10 = chart.lord(10)
    l10 = chart.p(lord_10)
    if not l10:
        return

    if (l10.get("sign") or "") == DEBIL.get(lord_10):
        ledger.affliction += 10
        ledger.add(Signal("job", -3, "10L debilitated — role instability", lord_10))
        ledger.add(Signal("business", -2, "10L debilitated — enterprise risk", lord_10))

    if l10.get("combust"):
        ledger.affliction += 6

    if len([n for n in chart.occupants(10) if n in MALEFIC]) >= 2:
        ledger.affliction += 5

    moon = chart.p("Moon")
    if moon and (moon.get("sign") or "") == DEBIL.get("Moon"):
        ledger.stability_penalty += 12
    if moon and chart.is_weak("Moon"):
        ledger.stability_penalty += 6

    merc = chart.p("Mercury")
    if merc and (merc.get("sign") or "") == DEBIL.get("Mercury"):
        ledger.affliction += 4
        if any(n in MALEFIC for n, _ in chart.aspects_on_planet("Mercury")):
            ledger.affliction += 3


def _d1_d10_alignment(
    d1_job: float, d1_biz: float, d1_comm: float,
    d10_job: float, d10_biz: float, d10_comm: float,
) -> str:
    d1_total = max(d1_job + d1_biz + d1_comm, 1.0)
    d10_total = max(d10_job + d10_biz + d10_comm, 1.0)
    if d10_total < 2:
        return "neutral"

    def _lean(j, b, c, t):
        return ((j - b) / t, c / t)

    d1_lean, d1_c = _lean(d1_job, d1_biz, d1_comm, d1_total)
    d10_lean, d10_c = _lean(d10_job, d10_biz, d10_comm, d10_total)

    if d1_lean * d10_lean > 0 and abs(d1_lean) > 0.12 and abs(d10_lean) > 0.1:
        return "aligned"
    if d1_lean * d10_lean < 0 and abs(d1_lean) > 0.08 and abs(d10_lean) > 0.08:
        return "contradictory"
    if abs(d1_c - d10_c) > 0.2:
        return "mixed"
    return "mixed"


def _compute_directional_scores(ledger: ScoreLedger) -> Tuple[float, float, float, float, float]:
    """Map multi-axis ledger to job vs business directional weights (D1 only)."""
    afflict_mult = _clamp(1.0 - ledger.affliction / 130.0, 0.84, 1.0)
    inst_mult = _clamp(1.0 - ledger.instability / 80.0, 0.88, 1.0)
    mult = afflict_mult * inst_mult

    d_job = max(ledger.job, 0) * mult
    d_biz = max(ledger.business, 0) * mult
    d_comm = max(ledger.commercial, 0) * mult
    d_free = max(ledger.freelance, 0) * mult

    exec_score = _clamp(ledger.execution, 0, 100)
    if exec_score < 22 and d_biz > d_job + 8:
        d_biz *= 0.88
        d_job += d_biz * 0.06

    effective_job = d_job + d_comm * 0.54 + d_free * 0.38 + ledger.structure * 0.06 * mult
    effective_biz = d_biz + d_comm * 0.26 + d_free * 0.22 + ledger.independence * 0.08 * mult

    return effective_job, effective_biz, d_comm, d_free, exec_score


def _apply_d10_nudge(
    job_pct: int,
    align_state: str,
    d10_job: float,
    d10_biz: float,
) -> int:
    if d10_job + d10_biz < 2:
        return job_pct
    d10_lean = d10_job - d10_biz
    nudge = 0
    if align_state == "aligned":
        nudge = 4 if d10_lean > 0 else -4
    elif align_state == "contradictory":
        nudge = -2 if job_pct > 50 else 2
    return int(_clamp(job_pct + nudge, 18, 82))


def _confidence(
    gap_pct: float,
    alignment: str,
    affliction: float,
    stability_penalty: float,
    d10_total: float,
    align_state: str,
) -> Tuple[str, int]:
    clarity = gap_pct * 2.2
    if alignment == "aligned":
        clarity += 18
    elif alignment == "contradictory":
        clarity -= 22
    elif alignment == "mixed":
        clarity -= 6
    clarity -= affliction * 0.28
    clarity -= stability_penalty * 0.45
    if d10_total > 5:
        clarity += 6
    clarity = int(_clamp(clarity, 0, 100))

    if clarity >= 72:
        return "High", clarity
    if clarity >= 52:
        return "Medium-High", clarity
    if clarity >= 32:
        return "Medium", clarity
    return "Low", clarity


def _psychology_traits(chart: CareerChart) -> Dict[str, int]:
    def _trait(planet: str, houses: Tuple[int, ...], base: int) -> int:
        pl = chart.p(planet)
        if not pl:
            return base
        h = int(pl.get("house") or 0)
        mod = chart.dignity_score(planet)
        bonus = 12 if h in houses else 0
        if (pl.get("sign") or "") == EXALT.get(planet):
            bonus += 8
        elif (pl.get("sign") or "") == DEBIL.get(planet):
            bonus -= 8
        return int(_clamp((base + bonus) * mod, 20, 95))

    return {
        "discipline": _trait("Saturn", (6, 10, 11), 48),
        "risk_appetite": (_trait("Mars", (3, 7, 10), 42) + _trait("Rahu", (7, 10, 11), 20)) // 2,
        "leadership": _trait("Sun", (1, 10, 11), 45),
        "communication": _trait("Mercury", (3, 6, 10), 50),
        "emotional_stability": _trait("Moon", (4, 7, 10), 48),
        "authority_tolerance": (_trait("Sun", (10,), 30) + _trait("Saturn", (10,), 30)) // 2,
        "independence": (_trait("Rahu", (1, 7, 10), 35) + _trait("Mars", (1, 3, 10), 35)) // 2,
        "persistence": _trait("Saturn", (6, 8, 10), 50),
        "adaptability": (_trait("Mercury", (3, 6), 30) + _trait("Moon", (3, 7), 30)) // 2,
    }


def _classify_subtypes(chart: CareerChart) -> Dict[str, List[str]]:
    job_tags: List[str] = []
    biz_tags: List[str] = []
    comm_tags: List[str] = []

    pairs = [
        (("Sun", "Saturn"), "administration / government", "job"),
        (("Mercury", "Jupiter"), "law / advisory / teaching", "comm"),
        (("Mars", "Saturn"), "engineering / operations", "comm"),
        (("Venus", "Mercury"), "media / design profession", "comm"),
        (("Moon", "Jupiter"), "care / education / public sector", "job"),
        (("Mercury", "Rahu"), "digital / startup / trading", "biz"),
        (("Venus", "Mercury"), "branding / luxury commerce", "biz"),
        (("Jupiter", "Mercury"), "consulting / education practice", "comm"),
        (("Rahu", "Saturn"), "scalable operations", "biz"),
    ]
    for (a, b), label, kind in pairs:
        if chart.conjunct(a, b) or (
            chart.p(a) and chart.p(b) and chart.p(a).get("house") == chart.p(b).get("house")
        ):
            if kind == "biz":
                biz_tags.append(label)
            elif kind == "comm":
                comm_tags.append(label)
            else:
                job_tags.append(label)
    return {
        "job_subtypes": job_tags[:3],
        "business_subtypes": biz_tags[:3],
        "commercial_subtypes": comm_tags[:3],
    }


def _career_mode(
    job_pct: int,
    business_pct: int,
    commercial_raw: float,
    freelance_raw: float,
    exec_score: float,
    struct: float,
    indep: float,
    traits: Dict[str, int],
    subtypes: Dict[str, List[str]],
) -> str:
    gap = abs(job_pct - business_pct)
    comm_dom = commercial_raw >= max(job_pct, business_pct) * 0.45

    if comm_dom and commercial_raw >= 14:
        if subtypes.get("commercial_subtypes"):
            return "Commercial Professional"
        return "Advisory / Consulting"

    if freelance_raw >= 10 and indep >= struct and gap <= 12:
        return "Independent Professional"

    if gap <= 8:
        return "Hybrid Career"

    if job_pct >= 72 and struct >= indep + 6:
        return "Pure Service"

    if job_pct >= 58:
        if traits.get("authority_tolerance", 0) >= 60:
            return "Authority-Oriented"
        return "Structured Professional"

    if business_pct >= 68 and exec_score >= 28:
        return "Entrepreneurial"

    if business_pct >= 55:
        if indep >= struct + 8 and exec_score >= 22:
            return "Independent Professional"
        return "Hybrid Career"

    if traits.get("communication", 0) >= 62:
        return "Advisory / Consulting"

    return "Structured Professional"


def _verdict(
    job_pct: int,
    business_pct: int,
    mode: str,
    confidence: str,
    align_state: str,
    commercial_raw: float,
) -> str:
    j, b = job_pct, business_pct

    if mode == "Commercial Professional":
        base = (
            "A skilled commercial profession (consulting, advisory, technical, or client-facing) "
            "fits better than pure employment or raw entrepreneurship."
        )
    elif mode == "Independent Professional":
        base = (
            "Independent or freelance professional work suits you more than a fixed job "
            "or high-risk business ownership."
        )
    elif mode in ("Hybrid Career",) or abs(j - b) <= 8:
        base = (
            "Employment and independent income both appear viable; sustainability depends on role fit "
            "more than a single fixed label."
        )
    elif j > b:
        if j >= 65:
            base = "Structured employment appears more sustainable as the primary long-term path."
        else:
            base = (
                "Service-oriented work shows a modest edge; commercial or independent income "
                "can remain strong secondary channels."
            )
    else:
        if b >= 65:
            base = "Self-directed or commercial paths appear stronger than long-term fixed employment."
        else:
            base = (
                "Commercial or independent work shows a modest edge; stable employment can still anchor income."
            )

    if commercial_raw >= 12 and mode not in ("Commercial Professional",):
        base += " Strong professional-craft indicators are also present."

    if align_state == "contradictory":
        base += " D1 nature and D10 execution differ — flexibility is advisable."
    elif confidence in ("Low", "Medium"):
        base += " Signals are not sharply one-sided."

    return base


def _reasoning_summary(signals: List[Signal], top_n: int = 6) -> List[str]:
    axis_label = {
        "job": "employment",
        "business": "business",
        "commercial": "commercial profession",
        "freelance": "freelance/consulting",
        "structure": "structure",
        "independence": "independence",
        "execution": "execution",
    }
    ranked = sorted(signals, key=lambda s: -abs(s.weight))[:top_n]
    return [
        f"{'+' if s.weight >= 0 else '−'} {axis_label.get(s.axis, s.axis)}: {s.source}"
        for s in ranked
    ]


def compute_career_inclination(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict] = None,
) -> Dict[str, Any]:
    try:
        if kundli:
            asc_idx = resolve_asc_idx(kundli)
        planets = ensure_planet_houses(list(planets or []), asc_idx)
        chart = CareerChart(planets, asc_idx, kundli)
        ledger = ScoreLedger()

        _apply_placement_layer(chart, ledger)
        _apply_commercial_profession_layer(chart, ledger)
        _apply_execution_layer(chart, ledger)
        _apply_freelance_layer(chart, ledger)
        _apply_aspect_layer(chart, ledger)
        _apply_affliction_layer(chart, ledger)

        d10_job, d10_biz, d10_comm, d10_total = _apply_d10_readout(chart)

        eff_job, eff_biz, comm_raw, free_raw, exec_score = _compute_directional_scores(ledger)
        align_state = _d1_d10_alignment(
            ledger.job, ledger.business, ledger.commercial,
            d10_job, d10_biz, d10_comm,
        )

        total = max(eff_job + eff_biz, 1.0)
        job_pct = int(round(eff_job * 100 / total))
        business_pct = 100 - job_pct

        job_pct = _apply_d10_nudge(job_pct, align_state, d10_job, d10_biz)
        business_pct = 100 - job_pct

        gap = abs(job_pct - 50)
        if gap <= 2:
            job_pct = 50
            business_pct = 50

        confidence_label, confidence_score = _confidence(
            float(gap), align_state, ledger.affliction,
            ledger.stability_penalty, d10_total, align_state,
        )
        traits = _psychology_traits(chart)
        subtypes = _classify_subtypes(chart)
        struct_raw = ledger.structure
        indep_raw = ledger.independence

        mode = _career_mode(
            job_pct, business_pct, comm_raw, free_raw, exec_score,
            struct_raw, indep_raw, traits, subtypes,
        )
        verdict = _verdict(job_pct, business_pct, mode, confidence_label, align_state, comm_raw)
        reasons = _reasoning_summary(ledger.signals)

        if job_pct > business_pct:
            dominant, secondary = "job", "business"
        elif business_pct > job_pct:
            dominant, secondary = "business", "job"
        else:
            dominant, secondary = "hybrid", "hybrid"

        return {
            "job_pct": job_pct,
            "business_pct": business_pct,
            "confidence": confidence_label,
            "confidence_score": confidence_score,
            "dominant": dominant if dominant != "hybrid" else "balanced",
            "secondary_path": secondary,
            "career_mode": mode,
            "path_verdict": verdict,
            "reasoning_summary": reasons,
            "psychology": traits,
            "structure_score": int(_clamp(struct_raw, 0, 100)),
            "independence_score": int(_clamp(indep_raw, 0, 100)),
            "commercial_score": int(_clamp(comm_raw, 0, 100)),
            "execution_score": int(_clamp(exec_score, 0, 100)),
            "freelance_score": int(_clamp(free_raw, 0, 100)),
            "d1_d10_alignment": align_state,
            "affliction_load": round(ledger.affliction, 1),
            "stability_penalty": round(ledger.stability_penalty, 1),
            "job_subtypes": subtypes.get("job_subtypes", []),
            "business_subtypes": subtypes.get("business_subtypes", []),
            "commercial_subtypes": subtypes.get("commercial_subtypes", []),
            "factors": [
                {"axis": s.axis, "weight": round(s.weight, 2), "source": s.source, "planet": s.planet}
                for s in ledger.signals[:20]
            ],
        }
    except Exception as exc:
        return {
            "job_pct": 50,
            "business_pct": 50,
            "confidence": "Low",
            "confidence_score": 0,
            "dominant": "balanced",
            "secondary_path": "hybrid",
            "career_mode": "Hybrid Career",
            "path_verdict": "Insufficient chart data for a clear career-path read.",
            "reasoning_summary": [],
            "error": str(exc),
        }
