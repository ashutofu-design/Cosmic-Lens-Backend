"""
jaimini.py
──────────
Jaimini astrology computations — Sprint 7 scope:

  • Arudha Padas (A1-A12)  — image / reflection of each house
  • Upapada Lagna (UL=A12) — marriage / spouse signature
  • UL-derived marriage stability indicators (2nd-from-UL, 12th-from-UL,
    UL-lord placement, planets aspecting UL)

Algorithm (BPHS / Jaimini Sutras):
   Arudha of house H =  (2 × S_L − S_H) mod 12
   where S_H is the sign of house H, S_L is the sign occupied by the lord
   of S_H. EXCEPTION: if the resulting Arudha falls in S_H itself OR in
   the 7th from S_H, replace it with the 10th sign FROM the resulting
   Arudha (i.e. (Arudha + 9) mod 12).

Upapada Lagna is simply A12 with extra spouse-significator analysis:
   • 2nd-from-UL  — longevity / stability of marriage
   • 12th-from-UL — loss / end / separation potential
   • Lord of UL's sign and its house placement — spouse nature
"""
from __future__ import annotations
from typing import Any, Optional

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# One lord per sign (Aries=0 ... Pisces=11)
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sign_idx(sign_name: Any) -> Optional[int]:
    if not isinstance(sign_name, str):
        return None
    try:
        return SIGNS.index(sign_name.strip().capitalize())
    except ValueError:
        return None


def _planet_signs(planets: list) -> dict[str, int]:
    """{planet_name: sign_idx}"""
    out: dict[str, int] = {}
    if not isinstance(planets, list):
        return out
    for p in planets:
        if not isinstance(p, dict):
            continue
        name = p.get("name")
        si = _sign_idx(p.get("sign"))
        if isinstance(name, str) and si is not None:
            out[name] = si
    return out


# ── Arudha computation ───────────────────────────────────────────────────────

def _arudha_for_house(house: int, lagna_idx: int,
                      planet_signs: dict[str, int]) -> Optional[dict]:
    """Compute Arudha Pada for house number `house` (1-12)."""
    if not (1 <= house <= 12):
        return None
    s_h = (lagna_idx + house - 1) % 12          # sign of house H
    lord = SIGN_LORDS[s_h]
    s_l = planet_signs.get(lord)                # sign occupied by the lord
    if s_l is None:
        return None
    arudha = (2 * s_l - s_h) % 12
    note = ""
    # Classical exception: if Arudha falls in S_H itself or 7th from S_H,
    # use the 10th sign FROM the arudha.
    if arudha == s_h or arudha == (s_h + 6) % 12:
        original = arudha
        arudha = (arudha + 9) % 12
        note = (f"adjusted from {SIGNS[original]} "
                f"(would have fallen on/opposite the house itself)")
    return {
        "house":   house,
        "sign":    SIGNS[arudha],
        "sign_idx": arudha,
        "lord":    lord,
        "lord_in": SIGNS[s_l],
        "note":    note,
    }


def compute_arudha_padas(planets: list, lagna_sign: Any) -> dict[str, Any]:
    """
    Compute all 12 Arudha Padas (A1..A12).

    Returns:
        {
          "lagna_sign": "Sagittarius",
          "padas": {
            "A1":  {"house":1, "sign":"...", "lord":"...", "lord_in":"...", "note":...},
            "A2":  {...},
            ...
            "A12": {...}            # A12 == Upapada Lagna
          }
        }
    Returns {} if input insufficient.
    """
    lagna_idx = _sign_idx(lagna_sign)
    if lagna_idx is None:
        return {}
    psigns = _planet_signs(planets)
    if not psigns:
        return {}
    padas: dict[str, dict] = {}
    for h in range(1, 13):
        a = _arudha_for_house(h, lagna_idx, psigns)
        if a:
            padas[f"A{h}"] = a
    if not padas:
        return {}
    return {"lagna_sign": SIGNS[lagna_idx], "padas": padas}


# ── Upapada Lagna analysis ───────────────────────────────────────────────────

def _planet_houses_from_sign(planet_signs: dict[str, int],
                             ref_sign_idx: int) -> dict[str, int]:
    """For each planet return its house COUNTED FROM ref_sign_idx (1-12)."""
    out: dict[str, int] = {}
    for p, s in planet_signs.items():
        out[p] = ((s - ref_sign_idx) % 12) + 1
    return out


def compute_upapada(arudha_result: dict, planets: list) -> dict[str, Any]:
    """
    Build the Upapada Lagna (A12) marriage signature:
      • UL sign and its lord
      • 2nd-from-UL (sustenance / stability of marriage)
      • 12th-from-UL (loss / separation potential)
      • Planets occupying UL  (their nature colours marriage)
      • Planets occupying 2nd-from-UL  (benefics here = stable union;
                                        malefics = strain)
      • UL-lord's placement counted from UL (good in 1/4/5/7/9/10/11)

    Returns {} if upstream Arudha computation failed.
    """
    if not isinstance(arudha_result, dict):
        return {}
    padas = arudha_result.get("padas") or {}
    a12 = padas.get("A12")
    if not isinstance(a12, dict):
        return {}

    psigns = _planet_signs(planets)
    if not psigns:
        return {}

    ul_idx        = a12["sign_idx"]
    ul_sign       = a12["sign"]
    ul_lord       = SIGN_LORDS[ul_idx]
    second_idx    = (ul_idx + 1) % 12
    twelfth_idx   = (ul_idx - 1) % 12

    occupants_ul     = sorted(p for p, s in psigns.items() if s == ul_idx)
    occupants_2nd    = sorted(p for p, s in psigns.items() if s == second_idx)
    occupants_12th   = sorted(p for p, s in psigns.items() if s == twelfth_idx)

    ul_lord_sign_idx = psigns.get(ul_lord)
    if ul_lord_sign_idx is None:
        ul_lord_house_from_ul = None
        ul_lord_in_sign       = None
    else:
        ul_lord_house_from_ul = ((ul_lord_sign_idx - ul_idx) % 12) + 1
        ul_lord_in_sign       = SIGNS[ul_lord_sign_idx]

    # Classical benefic/malefic split (gentle-purpose for marriage tone)
    BENEFIC = {"Jupiter", "Venus", "Moon", "Mercury"}
    MALEFIC = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}

    second_benefics = [p for p in occupants_2nd if p in BENEFIC]
    second_malefics = [p for p in occupants_2nd if p in MALEFIC]

    # Verdict for marriage stability
    verdict_parts: list[str] = []
    if second_benefics and not second_malefics:
        verdict_parts.append("STABLE — benefics in 2nd-from-UL")
    elif second_malefics and not second_benefics:
        verdict_parts.append("STRAINED — malefics in 2nd-from-UL")
    elif second_benefics and second_malefics:
        verdict_parts.append("MIXED — both benefics & malefics in 2nd-from-UL")
    else:
        verdict_parts.append("NEUTRAL — 2nd-from-UL empty (no major signal)")

    # Lord-of-UL placement quality (Jaimini treats kendras+trikonas+upachayas as good)
    GOOD_HOUSES_FROM_UL = {1, 4, 5, 7, 9, 10, 11}
    if ul_lord_house_from_ul in GOOD_HOUSES_FROM_UL:
        verdict_parts.append(f"UL-lord {ul_lord} well-placed ({ul_lord_house_from_ul}th from UL)")
    elif ul_lord_house_from_ul in {6, 8, 12}:
        verdict_parts.append(f"UL-lord {ul_lord} in dusthana ({ul_lord_house_from_ul}th from UL) — caution")

    return {
        "ul_sign":          ul_sign,
        "ul_lord":          ul_lord,
        "ul_lord_in":       ul_lord_in_sign,
        "ul_lord_house":    ul_lord_house_from_ul,
        "second_from_ul":   SIGNS[second_idx],
        "twelfth_from_ul":  SIGNS[twelfth_idx],
        "occupants_ul":     occupants_ul,
        "occupants_2nd":    occupants_2nd,
        "occupants_12th":   occupants_12th,
        "verdict":          " · ".join(verdict_parts),
        "note":             a12.get("note") or "",
    }


# ── Formatter for LOCKED FACTS ───────────────────────────────────────────────

def format_jaimini_summary(arudha_result: dict, upapada: dict) -> str:
    if not isinstance(arudha_result, dict) or not arudha_result.get("padas"):
        return ""
    padas = arudha_result["padas"]

    lines: list[str] = []
    lines.append("▸ JAIMINI ARUDHA PADAS (image/reflection of each house — perception):")
    house_label = {
        1: "self/image",      2: "wealth-image",   3: "courage/sibs",
        4: "home/comfort",    5: "creativity/kids", 6: "enemies/work",
        7: "partnership-img", 8: "transform",      9: "fortune/dharma",
        10: "career-image",   11: "gains-image",   12: "loss/spouse-img",
    }
    for h in range(1, 13):
        a = padas.get(f"A{h}")
        if not a:
            continue
        note = f"  ⚠️ {a['note']}" if a.get("note") else ""
        lines.append(
            f"   ▸ A{h} ({house_label[h]}): {a['sign']} — "
            f"lord {a['lord']} in {a['lord_in']}{note}"
        )

    if upapada:
        lines.append("")
        lines.append("▸ UPAPADA LAGNA (UL = A12 — Jaimini marriage signature):")
        lines.append(
            f"   ▸ UL sign: {upapada['ul_sign']}  (lord {upapada['ul_lord']} "
            f"in {upapada.get('ul_lord_in') or '(unknown)'} — "
            f"{upapada.get('ul_lord_house') or '?'}th from UL)"
        )
        lines.append(
            f"   ▸ 2nd-from-UL: {upapada['second_from_ul']}  "
            f"(occupants: {', '.join(upapada['occupants_2nd']) or 'none'})"
        )
        lines.append(
            f"   ▸ 12th-from-UL: {upapada['twelfth_from_ul']}  "
            f"(occupants: {', '.join(upapada['occupants_12th']) or 'none'})"
        )
        if upapada.get("occupants_ul"):
            lines.append(
                f"   ▸ Planets in UL itself: {', '.join(upapada['occupants_ul'])}"
            )
        lines.append(f"   ▸ MARRIAGE VERDICT (Jaimini UL): {upapada['verdict']}")
        lines.append(
            "   Legend: STABLE = harmonious marriage; STRAINED = friction "
            "needs work; MIXED = good-and-bad together; dusthana 6/8/12 "
            "from UL = obstacles."
        )
    return "\n".join(lines)
