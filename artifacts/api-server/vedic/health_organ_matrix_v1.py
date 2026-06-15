"""
Organ vulnerability heatmap — 6 body zones, deterministic D1 + tridosha.

Status: high | moderate | stable (no medical diagnosis language).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_MALEFICS = frozenset({"Saturn", "Mars", "Rahu", "Ketu", "Sun"})
_DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}

_ZONE_SPECS: List[Dict[str, Any]] = [
    {
        "id": "digestion",
        "dosha": "pitta",
        "houses": (5, 6),
        "signs": ("Virgo",),
        "planets": ("Mars", "Sun", "Mercury"),
        "issue_keys": ("digest", "stomach", "intestin", "abdomen", "acidity", "liver"),
    },
    {
        "id": "respiratory",
        "dosha": "kapha",
        "houses": (4,),
        "signs": ("Gemini", "Cancer"),
        "planets": ("Saturn", "Rahu", "Moon"),
        "issue_keys": ("lung", "chest", "throat", "respir", "cough", "vocal"),
    },
    {
        "id": "joints_nerves",
        "dosha": "vata",
        "houses": (1, 6),
        "signs": ("Capricorn", "Aquarius", "Gemini"),
        "planets": ("Saturn", "Rahu", "Mercury"),
        "issue_keys": ("joint", "bone", "knee", "nerve", "vata", "anxiety"),
    },
    {
        "id": "heart_circulation",
        "dosha": "pitta",
        "houses": (4, 5),
        "signs": ("Leo", "Scorpio"),
        "planets": ("Sun", "Mars"),
        "issue_keys": ("heart", "bp", "circulat", "blood pressure", "spine"),
    },
    {
        "id": "mind_sleep",
        "dosha": "kapha",
        "houses": (12, 4),
        "signs": ("Pisces", "Cancer"),
        "planets": ("Moon", "Saturn", "Rahu"),
        "issue_keys": ("mind", "sleep", "mood", "mental", "anxiety", "stress"),
    },
    {
        "id": "metabolism",
        "dosha": "pitta",
        "houses": (5, 6, 9),
        "signs": ("Sagittarius", "Virgo"),
        "planets": ("Jupiter", "Sun"),
        "issue_keys": ("liver", "sugar", "metabol", "weight", "pancrea", "diabetes"),
    },
]


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _status(score: float) -> str:
    if score >= 5.0:
        return "high"
    if score >= 2.5:
        return "moderate"
    return "stable"


def _issue_blob(issues: List[dict]) -> str:
    parts: List[str] = []
    for it in issues or []:
        parts.append(str(it.get("organs") or ""))
        parts.append(str(it.get("reason") or ""))
        parts.append(str(it.get("area") or ""))
    return " ".join(parts).lower()


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
    moon = _find_p(planets, "Moon")
    sat = _find_p(planets, "Saturn")
    out: List[Dict[str, Any]] = []

    for spec in _ZONE_SPECS:
        zid = str(spec["id"])
        score = 0.0
        triggers: List[str] = []

        dk = str(spec["dosha"])
        dpct = int(dosha_balance.get(dk) or 0)
        if dpct >= 40:
            score += 2.5
            triggers.append(f"{dk}_elevated")
        elif dpct >= 36:
            score += 1.5

        for h in spec["houses"]:
            for p in planets or []:
                if p.get("house") != h:
                    continue
                nm = str(p.get("name") or "")
                if nm in _MALEFICS:
                    score += 2.5
                    triggers.append(f"malefic_{nm}_h{h}")
                elif nm in spec["planets"]:
                    score += 1.5
                    triggers.append(f"{nm}_h{h}")
                sg = str(p.get("sign") or "")
                if sg in spec["signs"]:
                    score += 0.5

        for nm in spec["planets"]:
            p = _find_p(planets, nm)
            if not p:
                continue
            if nm in _DEBIL and p.get("sign") == _DEBIL[nm]:
                score += 2.0
                triggers.append(f"{nm}_debil")
            if int(p.get("house") or 0) in (6, 8, 12):
                score += 1.5
                triggers.append(f"{nm}_dusthana")

        for key in spec["issue_keys"]:
            if key in blob:
                score += 2.0
                triggers.append("chart_issue")
                break

        if zid == "mind_sleep" and moon:
            if moon.get("sign") == _DEBIL["Moon"]:
                score += 2.0
                triggers.append("moon_debil")
            if moon.get("house") in (6, 8, 12):
                score += 2.5
                triggers.append("moon_dusthana")
            if sat and moon.get("house") and sat.get("house"):
                if abs(int(moon.get("house") or 0) - int(sat.get("house") or 0)) <= 1:
                    score += 1.5
                    triggers.append("moon_saturn_near")

        if zid == "joints_nerves" and sat and sat.get("house") in (1, 6):
            score += 2.0
            triggers.append("saturn_vata_house")

        st = _status(score)
        out.append({
            "id": zid,
            "status": st,
            "score": round(score, 1),
            "engine": "health_organ_matrix_v1",
        })

    out.sort(key=lambda z: (-{"high": 3, "moderate": 2, "stable": 1}[z["status"]], -z["score"]))
    return out
