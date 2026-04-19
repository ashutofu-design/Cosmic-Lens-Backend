"""
Sprint 26 — Tier Jaimini Advanced (gap fill)
Adds Rashi Drishti (sign aspects) — the only missing piece in Jaimini stack.

BPHS Ch.7 Rashi Drishti rules:
  • MOVABLE signs (Aries, Cancer, Libra, Capricorn) aspect all FIXED signs
    EXCEPT the one adjacent to them.
  • FIXED signs (Taurus, Leo, Scorpio, Aquarius) aspect all MOVABLE signs
    EXCEPT the one adjacent to them.
  • DUAL signs (Gemini, Virgo, Sagittarius, Pisces) aspect all other DUAL
    signs (3 of them).

Rashi drishti is a SIGN-to-SIGN aspect (different from Parashari planet
drishti which is house-based). Used in Jaimini Karaka Kendradi & Argala
analysis.
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
MOVABLE = [0, 3, 6, 9]   # Aries, Cancer, Libra, Capricorn
FIXED   = [1, 4, 7, 10]  # Taurus, Leo, Scorpio, Aquarius
DUAL    = [2, 5, 8, 11]  # Gemini, Virgo, Sagittarius, Pisces


def _sign_class(idx: int) -> str:
    if idx in MOVABLE: return "movable"
    if idx in FIXED:   return "fixed"
    return "dual"


def signs_aspected_by(sign_idx: int) -> list[int]:
    """Returns list of sign indices that are aspected BY the given sign."""
    cls = _sign_class(sign_idx)
    if cls == "movable":
        # Aspect all FIXED signs except the one adjacent (next sign)
        adj = (sign_idx + 1) % 12
        return [s for s in FIXED if s != adj]
    if cls == "fixed":
        # Aspect all MOVABLE signs except the one adjacent (previous sign)
        adj = (sign_idx - 1) % 12
        return [s for s in MOVABLE if s != adj]
    # Dual aspects all OTHER duals
    return [s for s in DUAL if s != sign_idx]


def compute_rashi_drishti(planets: list[dict],
                          lagna_sign_idx: int | None = None) -> dict[str, Any]:
    """For each sign, returns:
       - signs it aspects
       - planets occupying it
       - planets it aspects (via planets in aspected signs)
    Plus per-planet: which signs/planets aspect THIS planet via rashi drishti."""
    # Build sign → list of planets
    sign_to_planets: dict[int, list[str]] = {i: [] for i in range(12)}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        sn = p.get("sign")
        if isinstance(sn, str) and sn in SIGN_NAMES and nm:
            sign_to_planets[SIGN_NAMES.index(sn)].append(nm)

    sign_aspects: dict[str, dict[str, Any]] = {}
    for s in range(12):
        aspected = signs_aspected_by(s)
        sign_aspects[SIGN_NAMES[s]] = {
            "class": _sign_class(s),
            "occupants": sign_to_planets[s],
            "aspects_signs": [SIGN_NAMES[a] for a in aspected],
            "aspects_planets": [p for a in aspected for p in sign_to_planets[a]],
        }

    # Reverse map — for each planet, who aspects it via Rashi Drishti
    planet_received: dict[str, list[dict]] = {}
    for s in range(12):
        for src_planet in sign_to_planets[s]:
            for tgt_sign in signs_aspected_by(s):
                for tgt_planet in sign_to_planets[tgt_sign]:
                    if tgt_planet == src_planet:
                        continue
                    planet_received.setdefault(tgt_planet, []).append({
                        "from_planet": src_planet,
                        "from_sign": SIGN_NAMES[s],
                        "to_sign": SIGN_NAMES[tgt_sign],
                    })

    # Lagna's rashi drishti (key for Karaka Kendradi)
    lagna_view = None
    if isinstance(lagna_sign_idx, int) and 0 <= lagna_sign_idx <= 11:
        asp = signs_aspected_by(lagna_sign_idx)
        lagna_view = {
            "lagna_sign": SIGN_NAMES[lagna_sign_idx],
            "lagna_class": _sign_class(lagna_sign_idx),
            "aspects_signs": [SIGN_NAMES[a] for a in asp],
            "aspects_planets": [p for a in asp for p in sign_to_planets[a]],
        }

    return {
        "available": True,
        "system": "Jaimini Rashi Drishti (BPHS Ch.7)",
        "per_sign": sign_aspects,
        "planet_received_aspects": planet_received,
        "lagna_view": lagna_view,
    }


def format_rashi_drishti_summary(result: dict) -> str:
    if not isinstance(result, dict) or not result.get("available"):
        return ""
    lines = ["── JAIMINI RASHI DRISHTI (Sprint 26) ──"]

    lv = result.get("lagna_view")
    if lv:
        lines.append(f"Lagna {lv['lagna_sign']} ({lv['lagna_class']}) Rashi-aspects: "
                     f"{', '.join(lv['aspects_signs'])}")
        if lv["aspects_planets"]:
            lines.append(f"  → planets in aspect: {', '.join(lv['aspects_planets'])}")

    pr = result.get("planet_received_aspects", {})
    if pr:
        lines.append("Planets receiving Rashi-Drishti from other planets:")
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                       "Venus", "Saturn", "Rahu", "Ketu"]:
            received = pr.get(planet, [])
            if received:
                srcs = sorted({r["from_planet"] for r in received})
                lines.append(f"  {planet}: aspected by {', '.join(srcs)}")

    return "\n".join(lines)
