"""
Sprint 13 — Argala (Jaimini intervention) + Virodhargala (counter-intervention)
================================================================================
Argala = "bondage" or "intervention" exerted on a house by planets in specific
positions. A house's affairs are influenced (helped or harmed) by planets in:

  • 2nd from the house  → primary Argala (sustenance/resources intervention)
  • 4th from the house  → secondary Argala (foundation/comfort intervention)
  • 5th from the house  → secondary Argala (intelligence/progeny intervention)
  • 11th from the house → secondary Argala (gain/desire-fulfillment intervention)
  • 3rd from the house  → "Paap-Argala" (malefic-only intervention via valor)

Virodhargala (counter-intervention) cancels Argala from the OPPOSITE slot:
  • 12th cancels 2nd
  • 10th cancels 4th
  • 9th  cancels 5th
  • 3rd  cancels 11th
  • 11th cancels 3rd (Paap-Argala neutralised)

Net Argala verdict per house:
  • Benefics in Argala slot, no/few opposing planets → "BENEFIC ARGALA"
  • Malefics in Argala slot, no/few opposing planets → "MALEFIC ARGALA"
  • Mixed or fully cancelled                         → "NEUTRAL / CANCELLED"
"""
from typing import Any

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

BENEFIC = {"Jupiter", "Venus", "Moon", "Mercury"}
MALEFIC = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}

# (Argala house, Virodhargala house counted from the same reference)
ARGALA_PAIRS = [
    (2,  12, "primary"),    # 2nd Argala  cancelled by 12th
    (4,  10, "secondary"),  # 4th Argala  cancelled by 10th
    (5,   9, "secondary"),  # 5th Argala  cancelled by 9th
    (11,  3, "secondary"),  # 11th Argala cancelled by 3rd
]
PAAP_ARGALA = (3, 11)       # 3rd house = Paap-Argala (malefics only),
                             # cancelled by 11th


def _planet_signs(planets: list) -> dict[str, int]:
    out: dict[str, int] = {}
    if not isinstance(planets, list):
        return out
    for p in planets:
        if not isinstance(p, dict):
            continue
        name = p.get("name") or p.get("planet")
        sign = p.get("sign") or p.get("sign_name")
        if not (name and sign):
            continue
        try:
            idx = SIGNS.index(str(sign).strip().capitalize())
        except ValueError:
            continue
        out[name] = idx
    return out


def _classify(occupants: list[str]) -> tuple[list[str], list[str]]:
    benefics  = sorted(p for p in occupants if p in BENEFIC)
    malefics  = sorted(p for p in occupants if p in MALEFIC)
    return benefics, malefics


def compute_argala(planets: list, lagna_sign: Any) -> dict[str, Any]:
    """
    Returns per-house Argala/Virodhargala summary for all 12 houses
    counted from the LAGNA. Each entry contains:
      {
        house_num: int,
        house_sign: str,
        argala_signals: [
            {slot, kind, planets_argala, planets_virodha, net_verdict}
        ],
        paap_argala: {planets, virodha_planets, net_verdict},
        overall: "STRONG-BENEFIC" | "STRONG-MALEFIC" | "MIXED" | "NEUTRAL"
      }
    """
    psigns = _planet_signs(planets)
    if not psigns:
        return {}

    # normalise lagna
    if isinstance(lagna_sign, dict):
        lagna_sign = lagna_sign.get("sign") or lagna_sign.get("name")
    try:
        lagna_idx = SIGNS.index(str(lagna_sign).strip().capitalize())
    except (ValueError, AttributeError, TypeError):
        return {}

    houses: dict[int, Any] = {}
    for h in range(1, 13):
        h_sign_idx = (lagna_idx + h - 1) % 12
        argala_signals = []
        b_score = 0  # net benefic strength
        m_score = 0  # net malefic strength

        for arg_house, virodh_house, kind in ARGALA_PAIRS:
            arg_idx    = (h_sign_idx + arg_house    - 1) % 12
            virodh_idx = (h_sign_idx + virodh_house - 1) % 12
            arg_occ    = sorted(p for p, s in psigns.items() if s == arg_idx)
            virodh_occ = sorted(p for p, s in psigns.items() if s == virodh_idx)

            arg_b, arg_m = _classify(arg_occ)
            v_b,   v_m   = _classify(virodh_occ)

            # Net: benefics in Argala minus benefics in virodha
            net_b = max(0, len(arg_b) - len(v_b))
            net_m = max(0, len(arg_m) - len(v_m))

            verdict_parts = []
            if net_b and not net_m:
                verdict_parts.append("BENEFIC ARGALA")
            elif net_m and not net_b:
                verdict_parts.append("MALEFIC ARGALA")
            elif net_b and net_m:
                verdict_parts.append("MIXED ARGALA")
            elif arg_occ and not (net_b or net_m):
                verdict_parts.append("CANCELLED by Virodhargala")
            else:
                verdict_parts.append("no Argala")

            b_score += net_b * (2 if kind == "primary" else 1)
            m_score += net_m * (2 if kind == "primary" else 1)

            if arg_occ or virodh_occ:
                argala_signals.append({
                    "slot":             arg_house,
                    "slot_sign":        SIGNS[arg_idx],
                    "kind":             kind,
                    "planets_argala":   arg_occ,
                    "planets_virodha":  virodh_occ,
                    "verdict":          " · ".join(verdict_parts),
                })

        # Paap-Argala (3rd house — malefics only)
        paap_h, paap_v = PAAP_ARGALA
        paap_idx       = (h_sign_idx + paap_h - 1) % 12
        paap_v_idx     = (h_sign_idx + paap_v - 1) % 12
        paap_occ       = sorted(p for p, s in psigns.items() if s == paap_idx)
        paap_v_occ     = sorted(p for p, s in psigns.items() if s == paap_v_idx)
        paap_m         = [p for p in paap_occ   if p in MALEFIC]
        paap_v_m       = [p for p in paap_v_occ if p in MALEFIC]
        net_paap       = max(0, len(paap_m) - len(paap_v_m))
        if net_paap:
            m_score += net_paap

        paap_block = None
        if paap_m or paap_v_m:
            if net_paap:
                paap_verdict = f"PAAP-ARGALA active ({', '.join(paap_m)})"
            else:
                paap_verdict = "Paap-Argala CANCELLED"
            paap_block = {
                "planets":         paap_m,
                "virodha_planets": paap_v_m,
                "verdict":         paap_verdict,
            }

        # Overall verdict for this house
        if   b_score >= 2 and m_score == 0: overall = "STRONG-BENEFIC"
        elif m_score >= 2 and b_score == 0: overall = "STRONG-MALEFIC"
        elif b_score and m_score:           overall = "MIXED"
        elif b_score:                       overall = "MILD-BENEFIC"
        elif m_score:                       overall = "MILD-MALEFIC"
        else:                                overall = "NEUTRAL"

        houses[h] = {
            "house_num":      h,
            "house_sign":     SIGNS[h_sign_idx],
            "argala_signals": argala_signals,
            "paap_argala":    paap_block,
            "overall":        overall,
            "benefic_score":  b_score,
            "malefic_score":  m_score,
        }

    return houses


# Topic → most-relevant houses for argala citation
TOPIC_HOUSES = {
    "marriage":  [7, 2, 8, 12],
    "career":    [10, 6, 2, 11],
    "finance":   [2, 11, 5, 9],
    "child":     [5, 9, 2, 11],
    "health":    [1, 6, 8, 12],
    "education": [4, 5, 9, 2],
    "general":   [1, 10, 7, 4],
}


def format_argala_summary(argala: dict, topic: str = "general",
                          max_houses: int = 3) -> str:
    """Produce a short LOCKED-FACTS string of Argala for top houses by topic."""
    if not argala:
        return ""
    pri = TOPIC_HOUSES.get(topic, TOPIC_HOUSES["general"])[:max_houses]
    lines = []
    for h in pri:
        info = argala.get(h)
        if not info:
            continue
        bits = [f"H{h} ({info['house_sign']}) — overall {info['overall']}"]
        for sig in info["argala_signals"]:
            if sig["planets_argala"]:
                bits.append(
                    f"{sig['slot']}-house Argala ({sig['slot_sign']}): "
                    f"{', '.join(sig['planets_argala'])} "
                    f"[{sig['verdict']}]"
                )
        if info["paap_argala"]:
            bits.append(f"Paap-Argala: {info['paap_argala']['verdict']}")
        lines.append("   ▸ " + " · ".join(bits))
    if not lines:
        return ""
    return ("▸ ARGALA / VIRODHARGALA (Jaimini intervention — for "
            f"{topic} houses):\n" + "\n".join(lines))
