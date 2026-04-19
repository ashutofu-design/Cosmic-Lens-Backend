"""
Sprint 36 / Phase K — Avashtas (Planetary States) — 4 systems × 9 grahas.
K1 Baladi (5 by degree)
K2 Jagradadi (3 by dignity)
K3 Lajjitadi (6 by affliction)
K4 Deeptadi (9 by combined state)
Total: 9 grahas × 4 layers = 36 classifications, with 5+3+6+9 = 23 states ⇒ 180+ combinations.
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORD = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
             "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]

# Dignity tables (sidereal Vedic)
EXALTATION = {"Sun":"Aries","Moon":"Taurus","Mars":"Capricorn","Mercury":"Virgo",
              "Jupiter":"Cancer","Venus":"Pisces","Saturn":"Libra"}
DEBILITATION = {"Sun":"Libra","Moon":"Scorpio","Mars":"Cancer","Mercury":"Pisces",
                "Jupiter":"Capricorn","Venus":"Virgo","Saturn":"Aries"}
OWN_SIGNS = {"Sun":["Leo"], "Moon":["Cancer"],
             "Mars":["Aries","Scorpio"], "Mercury":["Gemini","Virgo"],
             "Jupiter":["Sagittarius","Pisces"], "Venus":["Taurus","Libra"],
             "Saturn":["Capricorn","Aquarius"]}
MOOLATRIKONA = {"Sun":"Leo","Moon":"Taurus","Mars":"Aries","Mercury":"Virgo",
                "Jupiter":"Sagittarius","Venus":"Libra","Saturn":"Aquarius"}
FRIENDS = {
    "Sun":["Moon","Mars","Jupiter"], "Moon":["Sun","Mercury"],
    "Mars":["Sun","Moon","Jupiter"], "Mercury":["Sun","Venus"],
    "Jupiter":["Sun","Moon","Mars"], "Venus":["Mercury","Saturn"],
    "Saturn":["Mercury","Venus"],
}
ENEMIES = {
    "Sun":["Venus","Saturn"], "Moon":[],
    "Mars":["Mercury"], "Mercury":["Moon"],
    "Jupiter":["Mercury","Venus"], "Venus":["Sun","Moon"],
    "Saturn":["Sun","Moon","Mars"],
}
NATURAL_BENEFICS = {"Jupiter","Venus","Mercury","Moon"}
NATURAL_MALEFICS = {"Sun","Mars","Saturn","Rahu","Ketu"}
WATERY_SIGNS = {"Cancer","Scorpio","Pisces"}

# ─── K1 Baladi (5 by degree-in-sign) ──────────────────────────────────
BALADI_STAGES = ["Bala (infant)","Kumara (child)","Yuva (youth)",
                 "Vridha (old)","Mrita (dead)"]
BALADI_STRENGTH = [0.25, 0.50, 1.00, 0.50, 0.25]  # rashmi multiplier


def baladi_state(deg_in_sign: float, sign_idx: int) -> dict[str, Any]:
    band = int(min(4, deg_in_sign // 6))
    if sign_idx % 2 == 1:  # even sign — order reversed
        band = 4 - band
    return {
        "stage": BALADI_STAGES[band],
        "strength_multiplier": BALADI_STRENGTH[band],
    }


# ─── K2 Jagradadi (3 by dignity) ──────────────────────────────────────
def jagradadi_state(planet: str, sign: str) -> dict[str, Any]:
    if sign == EXALTATION.get(planet) or sign in OWN_SIGNS.get(planet, []):
        state, effect = "Jagrat (awake)", "Full effect, gives complete results"
    elif sign in [SIGN_NAMES[i] for i, l in enumerate(SIGN_LORD)
                  if l in FRIENDS.get(planet, [])]:
        state, effect = "Swapna (dreaming)", "Half effect, dream-like results"
    elif sign == DEBILITATION.get(planet) or sign in [SIGN_NAMES[i]
            for i, l in enumerate(SIGN_LORD) if l in ENEMIES.get(planet, [])]:
        state, effect = "Sushupti (deep sleep)", "No effect, results lost in slumber"
    else:
        state, effect = "Swapna (dreaming)", "Half effect (neutral sign)"
    return {"state": state, "effect": effect}


# ─── K3 Lajjitadi (6 by affliction context) ───────────────────────────
def lajjitadi_states(planet: str, sign: str, sign_idx: int,
                      lon: float,
                      planets_by_name: dict[str, dict]) -> list[str]:
    states = []
    # Garvit — own/exalted/moolatrikona
    if sign == EXALTATION.get(planet) or sign in OWN_SIGNS.get(planet, []) \
       or sign == MOOLATRIKONA.get(planet):
        states.append("Garvit (proud)")
    # Lajjit — with Rahu/Ketu OR aspected by malefic in 5th
    for node in ("Rahu", "Ketu"):
        n = planets_by_name.get(node)
        if n and isinstance(n.get("longitude"), (int, float)):
            d = abs(n["longitude"] - lon); d = min(d, 360 - d)
            if d <= 8.0:
                states.append("Lajjit (ashamed)")
                break
    # Kshudita — in enemy sign OR with enemy
    en = ENEMIES.get(planet, [])
    if sign in [SIGN_NAMES[i] for i, l in enumerate(SIGN_LORD) if l in en]:
        states.append("Kshudita (hungry)")
    else:
        for e in en:
            ep = planets_by_name.get(e)
            if ep and isinstance(ep.get("longitude"), (int, float)):
                d = abs(ep["longitude"] - lon); d = min(d, 360 - d)
                if d <= 8.0:
                    states.append("Kshudita (hungry)")
                    break
    # Trishit — in watery sign AND aspected by malefic
    if sign in WATERY_SIGNS:
        for mal in NATURAL_MALEFICS:
            if mal == planet: continue
            mp = planets_by_name.get(mal)
            if mp and isinstance(mp.get("longitude"), (int, float)):
                # 7th aspect (180°)
                sep = (mp["longitude"] - lon) % 360
                if abs(sep - 180) < 8.0:
                    states.append("Trishit (thirsty)")
                    break
            if "Trishit (thirsty)" in states: break
    # Mudit — with a friend
    fr = FRIENDS.get(planet, [])
    for f in fr:
        fp = planets_by_name.get(f)
        if fp and isinstance(fp.get("longitude"), (int, float)):
            d = abs(fp["longitude"] - lon); d = min(d, 360 - d)
            if d <= 8.0:
                states.append("Mudit (delighted)")
                break
    # Kshobhit — within 8° of Sun (combust = agitated)
    if planet != "Sun":
        sun = planets_by_name.get("Sun")
        if sun and isinstance(sun.get("longitude"), (int, float)):
            d = abs(sun["longitude"] - lon); d = min(d, 360 - d)
            if d <= 8.0:
                states.append("Kshobhit (agitated by Sun)")
    return states


# ─── K4 Deeptadi (9 emotional states) ─────────────────────────────────
def deeptadi_state(planet: str, sign: str,
                    planets_by_name: dict[str, dict],
                    lon: float,
                    retrograde: bool) -> dict[str, Any]:
    """Pick dominant Deeptadi state by precedence."""
    state, effect = None, None
    if sign == EXALTATION.get(planet):
        state, effect = "Deepta (resplendent)", "Brilliant, full results in karaka matters"
    elif sign in OWN_SIGNS.get(planet, []):
        state, effect = "Swastha (comfortable)", "At home, gives stable benefit"
    elif sign == MOOLATRIKONA.get(planet):
        state, effect = "Shanta (peaceful)", "Balanced, harmonious results"
    elif sign in [SIGN_NAMES[i] for i, l in enumerate(SIGN_LORD)
                  if l in FRIENDS.get(planet, [])]:
        state, effect = "Mudita (joyful)", "Friendly territory, positive emotions"
    elif sign == DEBILITATION.get(planet):
        state, effect = "Khala (mischievous)", "Debilitated — produces deception, harm"
    elif sign in [SIGN_NAMES[i] for i, l in enumerate(SIGN_LORD)
                  if l in ENEMIES.get(planet, [])]:
        state, effect = "Deena (poor)", "In enemy sign — weak, dependent results"
    else:
        state, effect = "Shanta (peaceful)", "Neutral sign — moderate results"
    # Override: combust → Peedita
    if planet != "Sun":
        sun = planets_by_name.get("Sun")
        if sun and isinstance(sun.get("longitude"), (int, float)):
            d = abs(sun["longitude"] - lon); d = min(d, 360 - d)
            combust_orb = {"Moon":12, "Mars":17, "Mercury":13, "Jupiter":11,
                           "Venus":9, "Saturn":15}.get(planet, 8)
            if d <= combust_orb:
                state, effect = "Peedita (pained)", f"Combust by Sun (within {combust_orb}°) — burnt, weak"
    # Override: retrograde → Shakta (capable, strong) per BPHS Ch.46
    if retrograde and planet not in ("Sun","Moon","Rahu","Ketu") \
       and "Peedita" not in state and "Khala" not in state:
        state, effect = "Shakta (capable, strong)", "Retrograde — powerful, near-exaltation strength"
    return {"state": state, "effect": effect}


# ─── Master orchestrator ──────────────────────────────────────────────
def compute_avashtas(kundli: dict) -> dict[str, Any]:
    planets = kundli.get("planets") or []
    if not planets:
        return {"available": False, "reason": "no planets"}
    by_name = {p.get("name"): p for p in planets if isinstance(p, dict)}
    out_per_planet: list[dict[str, Any]] = []
    for p in planets:
        if not isinstance(p, dict): continue
        nm = p.get("name")
        lon = p.get("longitude")
        if nm in (None,) or not isinstance(lon, (int, float)):
            continue
        sign = p.get("sign") or SIGN_NAMES[int(lon // 30)]
        sign_idx = SIGN_NAMES.index(sign) if sign in SIGN_NAMES else int(lon // 30)
        deg_in = p.get("deg_in_sign", lon % 30)
        retro = p.get("retrograde", False)
        entry: dict[str, Any] = {
            "planet": nm, "sign": sign,
            "deg_in_sign": round(deg_in, 2),
            "retrograde": retro,
        }
        # K1 Baladi (only for 7 grahas, not Rahu/Ketu)
        if nm not in ("Rahu","Ketu"):
            entry["K1_baladi"] = baladi_state(deg_in, sign_idx)
        # K2 Jagradadi
        if nm in EXALTATION:  # the 7 grahas
            entry["K2_jagradadi"] = jagradadi_state(nm, sign)
        # K3 Lajjitadi
        if nm in EXALTATION:
            entry["K3_lajjitadi"] = lajjitadi_states(nm, sign, sign_idx, lon, by_name)
        # K4 Deeptadi
        if nm in EXALTATION:
            entry["K4_deeptadi"] = deeptadi_state(nm, sign, by_name, lon, retro)
        out_per_planet.append(entry)
    return {"available": True, "per_planet": out_per_planet}


def format_avashtas_summary(result: dict) -> str:
    if not result or not result.get("available"):
        return f"▸ AVASHTAS: ❌ {result.get('reason','n/a') if result else 'n/a'}"
    L = ["▸ AVASHTAS — Planetary States (Sprint-36 / Phase-K)",
         "  ── 4 Systems × 7 grahas: Baladi (5) + Jagradadi (3) + Lajjitadi (6) + Deeptadi (9) ──"]
    for e in result["per_planet"]:
        L.append(f"  ★ {e['planet']:<8} {e['sign']:<11} {e['deg_in_sign']:5.2f}°"
                 + (" ®" if e['retrograde'] else ""))
        if "K1_baladi" in e:
            b = e["K1_baladi"]
            L.append(f"      K1 Baladi:    {b['stage']:<22} (rashmi ×{b['strength_multiplier']:.2f})")
        if "K2_jagradadi" in e:
            j = e["K2_jagradadi"]
            L.append(f"      K2 Jagradadi: {j['state']:<22} → {j['effect']}")
        if "K3_lajjitadi" in e:
            ls = e["K3_lajjitadi"]
            L.append(f"      K3 Lajjitadi: {', '.join(ls) if ls else '(none — neutral)'}")
        if "K4_deeptadi" in e:
            d = e["K4_deeptadi"]
            L.append(f"      K4 Deeptadi:  {d['state']:<22} → {d['effect']}")
    return "\n".join(L)
