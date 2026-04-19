"""
karakas.py
──────────
Jaimini Chara Karakas — the planet with the highest degrees in its sign
becomes the Atmakaraka (soul indicator), and so on in descending order.

Standard 7-karaka scheme (Parashara/Jaimini classical):
    AK  Atmakaraka     — soul, primary life-purpose
    AmK Amatyakaraka   — career/livelihood/mind
    BK  Bhratrukaraka  — siblings, communication
    MK  Matrukaraka    — mother, comforts
    PK  Putrakaraka    — children, creativity
    GK  Gnatikaraka    — spiritual struggles, obstacles
    DK  Darakaraka     — spouse

Strict 7-karaka scheme used here: ONLY the 7 visible planets
(Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn). Rahu and Ketu are
EXCLUDED. (The 8-karaka variant adds Rahu with degree-inversion + a
Pitrukaraka role — that's a separate doctrine, not implemented here to
keep behaviour stable and unambiguous.)

Public API
──────────
    compute_karakas(planets) -> {
        "AK": "...", "AmK": "...", ..., "DK": "...",
        "details": [{role, planet, sign, deg_in_sign}],
    }
    format_karakas_summary(k) -> str
"""
from __future__ import annotations
from typing import Any

_ROLES = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
_ROLE_NAMES = {
    "AK":  "Atmakaraka (soul/life-purpose)",
    "AmK": "Amatyakaraka (career/livelihood)",
    "BK":  "Bhratrukaraka (siblings/communication)",
    "MK":  "Matrukaraka (mother/comforts)",
    "PK":  "Putrakaraka (children/creativity)",
    "GK":  "Gnatikaraka (spiritual struggles)",
    "DK":  "Darakaraka (spouse)",
}
_ELIGIBLE = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}


def _deg_in_sign(p: dict) -> float | None:
    """Extract degrees-within-sign from a planet entry. Tries several common keys."""
    for key in ("degree_in_sign", "deg_in_sign", "signDegree", "degInSign"):
        v = p.get(key)
        if isinstance(v, (int, float)):
            return float(v) % 30.0
    # Fallback: full longitude → mod 30
    for key in ("longitude", "lon", "fullDegree", "absoluteDegree"):
        v = p.get(key)
        if isinstance(v, (int, float)):
            return float(v) % 30.0
    # Some payloads provide "degree" already mod-30
    v = p.get("degree")
    if isinstance(v, (int, float)):
        return float(v) % 30.0
    return None


def compute_karakas(planets: list) -> dict[str, Any]:
    if not isinstance(planets, list):
        return {}
    rows: list[tuple[str, str, float]] = []  # (planet, sign, effective_deg)
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if nm not in _ELIGIBLE:
            continue
        deg = _deg_in_sign(p)
        if deg is None:
            continue
        rows.append((nm, p.get("sign", ""), deg))

    if len(rows) < 7:
        return {}

    rows.sort(key=lambda r: r[2], reverse=True)
    rows = rows[:7]  # 7-karaka scheme

    out: dict[str, Any] = {}
    details: list[dict] = []
    for role, (planet, sign, deg) in zip(_ROLES, rows):
        out[role] = planet
        details.append({
            "role": role, "planet": planet, "sign": sign,
            "deg_in_sign": round(deg, 2),
        })
    out["details"] = details
    return out


def format_karakas_summary(k: dict) -> str:
    if not k or "AK" not in k:
        return "▸ JAIMINI KARAKAS: (unavailable)"
    lines = ["▸ JAIMINI CHARA KARAKAS (highest-deg ranking — soul-level signatures):"]
    for d in k.get("details", []):
        role = d["role"]
        lines.append(
            f"   {role:3s} = {d['planet']:7s} ({d['sign']}, {d['deg_in_sign']}°) — {_ROLE_NAMES[role]}"
        )
    return "\n".join(lines)
