"""
Organ vulnerability heatmap — 6 body zones.

v2: D1 house-cusp signs, D9 karaka check, benefic/exalt relief,
    8H chronic layer, dampened cross-zone planet hits, per-planet budget.

Status: high | moderate | stable (no medical diagnosis language).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from vedic.life_specifics import SIGN_ORGAN

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
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}
OWN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}
_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFICS = frozenset({"Saturn", "Mars", "Rahu", "Ketu", "Sun"})
_DUSTHANA = frozenset({6, 8, 12})
_PLANET_BUDGET = 4.5

_ZONE_SPECS: List[Dict[str, Any]] = [
    {
        "id": "digestion",
        "dosha": "pitta",
        "houses": (5, 6),
        "planets": ("Mars", "Sun", "Mercury"),
        "issue_keys": ("digest", "stomach", "intestin", "abdomen", "acidity", "liver", "intestines"),
        "cusp_keys": ("intestin", "digest", "abdomen", "stomach"),
    },
    {
        "id": "respiratory",
        "dosha": "kapha",
        "houses": (4,),
        "planets": ("Saturn", "Rahu", "Moon", "Mercury"),
        "issue_keys": ("lung", "chest", "throat", "respir", "cough", "vocal", "shoulder"),
        "cusp_keys": ("lung", "chest", "throat", "vocal", "shoulder"),
    },
    {
        "id": "joints_nerves",
        "dosha": "vata",
        "houses": (1, 6, 8),
        "planets": ("Saturn", "Rahu", "Mercury", "Mars"),
        "issue_keys": ("joint", "bone", "knee", "nerve", "vata", "anxiety", "chronic", "skin"),
        "cusp_keys": ("joint", "bone", "knee", "nervous", "skin", "pelvis", "colon"),
    },
    {
        "id": "heart_circulation",
        "dosha": "pitta",
        "houses": (4, 5, 8),
        "planets": ("Sun", "Mars"),
        "issue_keys": ("heart", "bp", "circulat", "blood pressure", "spine", "back"),
        "cusp_keys": ("heart", "spine", "back", "circulat"),
    },
    {
        "id": "mind_sleep",
        "dosha": "kapha",
        "houses": (12, 4),
        "planets": ("Moon", "Saturn", "Rahu", "Mercury"),
        "issue_keys": ("mind", "sleep", "mood", "mental", "anxiety", "stress", "hormon"),
        "cusp_keys": ("mind", "sleep", "lymphatic", "immunity"),
    },
    {
        "id": "metabolism",
        "dosha": "pitta",
        "houses": (5, 6, 8, 9),
        "planets": ("Jupiter", "Sun", "Venus"),
        "issue_keys": ("liver", "sugar", "metabol", "weight", "pancrea", "diabetes", "kidney", "urinary"),
        "cusp_keys": ("liver", "kidney", "urinary", "thigh", "hip"),
    },
]

# Primary zone owner per house — others get dampened planet-in-house weight.
_HOUSE_PRIMARY: Dict[int, str] = {
    1: "joints_nerves",
    4: "respiratory",
    5: "digestion",
    6: "digestion",
    8: "joints_nerves",
    9: "metabolism",
    12: "mind_sleep",
}

_HOUSE_SECONDARY: Dict[int, Tuple[Tuple[str, float], ...]] = {
    4: (("heart_circulation", 0.45), ("mind_sleep", 0.35)),
    5: (("heart_circulation", 0.4), ("metabolism", 0.35)),
    6: (("joints_nerves", 0.5), ("metabolism", 0.4)),
    8: (("metabolism", 0.4), ("heart_circulation", 0.35), ("mind_sleep", 0.3)),
}


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _house_sign(asc_idx: int, house: int) -> str:
    return SIGNS[(asc_idx + house - 1) % 12]


def _status(score: float) -> str:
    if score >= 5.5:
        return "high"
    if score >= 3.0:
        return "moderate"
    return "stable"


def _issue_blob(issues: List[dict]) -> str:
    parts: List[str] = []
    for it in issues or []:
        parts.append(str(it.get("organs") or ""))
        parts.append(str(it.get("reason") or ""))
        parts.append(str(it.get("area") or ""))
    return " ".join(parts).lower()


def _varga_chart(kundli: Optional[dict], key: str) -> Optional[dict]:
    if not kundli:
        return None
    dv = kundli.get("divisionalCharts") or {}
    ch = dv.get(key) or dv.get(key.lower())
    if isinstance(ch, dict) and ch.get("planets"):
        return ch
    return None


def _d9_dignity(pname: str, d9: Optional[dict]) -> str:
    if not d9:
        return "neutral"
    p = _find_p(d9.get("planets") or [], pname)
    if not p:
        return "neutral"
    sg = str(p.get("sign") or "")
    if pname in EXALT and sg == EXALT[pname]:
        return "strong"
    if pname in OWN and sg in OWN[pname]:
        return "strong"
    if pname in DEBIL and sg == DEBIL[pname]:
        return "weak"
    return "neutral"


def _is_harsh_malefic(pname: str, sign: str) -> bool:
    if pname not in _MALEFICS:
        return False
    if pname == "Sun" and (sign == "Leo" or sign == EXALT.get("Sun")):
        return False
    if pname == "Mars" and sign in ("Aries", "Scorpio", "Capricorn"):
        return False
    if pname == "Saturn" and sign in ("Capricorn", "Aquarius", "Libra"):
        return False
    return True


def _dignity_relief(pname: str, sign: str) -> float:
    relief = 0.0
    if pname in EXALT and sign == EXALT[pname]:
        relief += 2.0
    elif pname in OWN and sign in OWN.get(pname, []):
        relief += 1.5
    return relief


def _house_weight(zone_id: str, house: int) -> float:
    if _HOUSE_PRIMARY.get(house) == zone_id:
        return 1.0
    for zid, factor in _HOUSE_SECONDARY.get(house, ()):
        if zid == zone_id:
            return factor
    if house in _DUSTHANA and zone_id in ("joints_nerves", "metabolism", "mind_sleep"):
        return 0.25
    return 0.0


def _budget_add(
    budget: Dict[str, float],
    pname: str,
    amount: float,
) -> float:
    """Return points actually applied after per-planet global cap."""
    if amount <= 0:
        return amount
    used = budget.get(pname, 0.0)
    room = max(0.0, _PLANET_BUDGET - used)
    applied = min(amount, room)
    budget[pname] = used + applied
    return applied


class _ZoneScorer:
    def __init__(self, zid: str, spec: dict, asc_idx: int, planets: List[dict],
                 blob: str, dosha_balance: Dict[str, int], d9: Optional[dict],
                 budget: Dict[str, float], lord6: str, lord6_house: Optional[int]):
        self.zid = zid
        self.spec = spec
        self.asc_idx = asc_idx
        self.planets = planets
        self.blob = blob
        self.dosha_balance = dosha_balance
        self.d9 = d9
        self.budget = budget
        self.lord6 = lord6
        self.lord6_house = lord6_house
        self.score = 0.0

    def add(self, amount: float, pname: str = "") -> None:
        if amount == 0:
            return
        if pname and amount > 0:
            amount = _budget_add(self.budget, pname, amount)
        self.score += amount

    def run(self) -> float:
        dk = str(self.spec["dosha"])
        dpct = int(self.dosha_balance.get(dk) or 0)
        if dpct >= 40:
            self.add(2.0)
        elif dpct >= 36:
            self.add(1.0)

        for h in self.spec["houses"]:
            hw = _house_weight(self.zid, h)
            if hw <= 0:
                continue

            cusp_sign = _house_sign(self.asc_idx, h)
            cusp_organ = SIGN_ORGAN.get(cusp_sign, "").lower()
            for key in self.spec["cusp_keys"]:
                if key in cusp_organ:
                    self.add(1.2 * hw)
                    break

            if h == 8 and self.zid in ("joints_nerves", "metabolism", "heart_circulation"):
                self.add(0.8 * hw)

            for p in self.planets:
                if p.get("house") != h:
                    continue
                nm = str(p.get("name") or "")
                sg = str(p.get("sign") or "")

                relief = _dignity_relief(nm, sg) * hw
                if relief:
                    self.add(-relief)

                if nm in _BENEFICS and not (nm in DEBIL and sg == DEBIL.get(nm)):
                    self.add(-0.8 * hw)

                if _is_harsh_malefic(nm, sg):
                    self.add(2.0 * hw, nm)
                elif nm in self.spec["planets"]:
                    self.add(1.0 * hw, nm)

        for nm in self.spec["planets"]:
            p = _find_p(self.planets, nm)
            if not p:
                continue
            sg = str(p.get("sign") or "")
            ph = int(p.get("house") or 0)

            if nm in DEBIL and sg == DEBIL[nm]:
                self.add(1.8, nm)
            if ph in _DUSTHANA:
                self.add(1.2, nm)

            d9t = _d9_dignity(nm, self.d9)
            if d9t == "weak":
                self.add(1.2, nm)
            elif d9t == "strong":
                self.add(-1.0)

        for key in self.spec["issue_keys"]:
            if key in self.blob:
                self.add(1.8)
                break

        if self.lord6_house in _DUSTHANA:
            if self.zid == "digestion":
                self.add(1.5, self.lord6)
            elif self.zid in ("joints_nerves", "metabolism"):
                self.add(0.8, self.lord6)

        self._special_rules()
        return max(0.0, self.score)

    def _special_rules(self) -> None:
        moon = _find_p(self.planets, "Moon")
        sat = _find_p(self.planets, "Saturn")

        if self.zid == "mind_sleep" and moon:
            sg = str(moon.get("sign") or "")
            if sg == DEBIL["Moon"]:
                self.add(1.8, "Moon")
            if moon.get("house") in _DUSTHANA:
                self.add(2.0, "Moon")
            if sat and moon.get("house") and sat.get("house"):
                if abs(int(moon.get("house") or 0) - int(sat.get("house") or 0)) <= 1:
                    self.add(1.0, "Moon")

        if self.zid == "joints_nerves" and sat:
            if sat.get("house") in (1, 6, 8):
                self.add(1.5, "Saturn")


def compute_organ_vulnerability_matrix(
    planets: List[dict],
    asc_idx: int,
    issues: Optional[List[dict]] = None,
    dosha_balance: Optional[Dict[str, int]] = None,
    kundli: Optional[dict] = None,
) -> List[Dict[str, Any]]:
    """Six-zone vulnerability heatmap for Life Map Health."""
    issues = issues or []
    dosha_balance = dosha_balance or {}
    blob = _issue_blob(issues)
    d9 = _varga_chart(kundli, "D9")
    budget: Dict[str, float] = {}

    sign_6 = _house_sign(asc_idx, 6)
    lord6 = SIGN_LORD.get(sign_6, "")
    lord6_p = _find_p(planets, lord6) if lord6 else None
    lord6_house = int(lord6_p.get("house") or 0) if lord6_p else None

    out: List[Dict[str, Any]] = []
    for spec in _ZONE_SPECS:
        zid = str(spec["id"])
        scorer = _ZoneScorer(
            zid, spec, asc_idx, planets or [], blob, dosha_balance, d9, budget, lord6, lord6_house,
        )
        raw = scorer.run()
        out.append({
            "id": zid,
            "status": _status(raw),
            "score": round(raw, 1),
            "engine": "health_organ_matrix_v2",
        })

    out.sort(key=lambda z: (-{"high": 3, "moderate": 2, "stable": 1}[z["status"]], -z["score"]))
    return out
