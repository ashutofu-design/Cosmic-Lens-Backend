"""Tier 17 — Moksha Synthesis, Karmic Portrait & Final Life-Mastery Verdict.

The capstone tier. Synthesizes the entire 17-tier audit into:
1. Moksha Bhava (12th house revisited as moksha-axis, NOT travel)
2. Atmakaraka — soul-significator (highest-degree planet) per Jaimini
3. Karakamsha — Atmakaraka's sign in D9 Navamsha (soul's arena of expression)
4. Trikona-Trishadaya synthesis — 1/5/9 dharma fortune vs 3/6/11 effort/struggle
5. Life-Mission Verdict — 5 archetypes (DHARMA-SAGE / KARMA-WARRIOR / BHAKTI-DEVOTEE
   / JNANA-SEEKER / MOKSHA-RECLUSE) chosen by composite signature
6. Spiritual Evolution Arc — current-dasha vs life-mission alignment
7. Final Life-Mastery Verdict — verdict-token + 7-step soul-blueprint + driver/conductor
   numerology integration (Option D framing closes the loop)

Hard data gate: ascendant + 9 grahas. Atmakaraka requires longitude data;
Karakamsha requires D9 navamsha; both soft-gated with graceful fallbacks.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
EXALT = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
         "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
         "Saturn": "Libra"}
DEBIL = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
         "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
         "Saturn": "Aries"}
OWN = {"Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
       "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
       "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"]}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}
UPACHAYA = {3, 6, 10, 11}
DHARMA_TRIKONA = {1, 5, 9}
KARMA_HOUSES = {3, 6, 10, 11}

# Atmakaraka calculation uses Chara Karaka system (Jaimini): the 7 grahas
# (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn — Rahu/Ketu excluded
# in the standard 7-graha scheme) ranked by longitude WITHIN their sign.
# The planet with the HIGHEST degree (within its sign) becomes Atmakaraka.
JAIMINI_KARAKA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Karakamsha sign → soul-arena per Jaimini (BPHS / Brihat Jataka lineage).
KARAKAMSHA_AREA: Dict[str, str] = {
    "Aries": "leadership / pioneering / warrior-soul — soul learns through bold first-action.",
    "Taurus": "stability / sensual-wisdom / artistic-soul — soul learns through embodied beauty.",
    "Gemini": "communication / learning / messenger-soul — soul learns through curious dialogue.",
    "Cancer": "nurturing / emotional-depth / mother-soul — soul learns through caring for life.",
    "Leo": "creative-expression / royal-service / king-soul — soul learns through dignified rule.",
    "Virgo": "service / precision / healer-soul — soul learns through careful refinement.",
    "Libra": "harmony / partnership / diplomat-soul — soul learns through balanced relationship.",
    "Scorpio": "transformation / occult-research / alchemist-soul — soul learns through depth-work.",
    "Sagittarius": "philosophy / teaching / sage-soul — soul learns through dharmic vision.",
    "Capricorn": "discipline / structure / patriarch-soul — soul learns through long-arc mastery.",
    "Aquarius": "innovation / collective-good / visionary-soul — soul learns through future-service.",
    "Pisces": "compassion / mysticism / saint-soul — soul learns through dissolution into the divine.",
}

# Life-mission archetypes (5)
LIFE_MISSIONS = {
    "dharma_sage": {
        "token": "DHARMA-SAGE",
        "description": ("Your soul-mission is DHARMIC TEACHING and WISDOM-TRANSMISSION. Strong "
                        "9th house / Jupiter / Trikona signature shapes you as one who carries "
                        "knowledge across generations. Career-success comes through teaching, "
                        "philosophy, law, publishing, spiritual leadership."),
    },
    "karma_warrior": {
        "token": "KARMA-WARRIOR",
        "description": ("Your soul-mission is ACTION-IN-THE-WORLD and OBSTACLE-CONQUEST. Strong "
                        "Mars / 3rd / 6th / 10th signature shapes you as one who builds, fights, "
                        "competes, transforms reality. Career-success comes through enterprise, "
                        "defence, sports, surgery, leadership of action."),
    },
    "bhakti_devotee": {
        "token": "BHAKTI-DEVOTEE",
        "description": ("Your soul-mission is DEVOTIONAL-LOVE and EMOTIONAL-OFFERING. Strong "
                        "Moon / Venus / 4th / 5th signature shapes you as one whose path is the "
                        "heart-opening through music, devotion, family-care, art. Career-success "
                        "comes through arts, hospitality, counselling, devotional service."),
    },
    "jnana_seeker": {
        "token": "JNANA-SEEKER",
        "description": ("Your soul-mission is KNOWLEDGE-INQUIRY and TRUTH-DISCERNMENT. Strong "
                        "Mercury / Saturn / 8th-research / Ketu signature shapes you as one "
                        "whose path is the relentless question. Career-success comes through "
                        "research, science, occult studies, deep analytical work."),
    },
    "moksha_recluse": {
        "token": "MOKSHA-RECLUSE",
        "description": ("Your soul-mission is INNER-LIBERATION and DISSOLUTION-OF-EGO. Strong "
                        "12th / Ketu / Pisces / Saturn-isolation signature shapes you as one "
                        "whose path is solitude, retreat, meditation, charity. Career-success "
                        "comes through ashram-work, hospice, monastic service, charity."),
    },
}

FINAL_VERDICT_TOKENS = {
    "blessed": "BLESSED-LIFE-MASTERY",          # Strong dharma + light karma + clear soul-arena
    "balanced": "BALANCED-MASTERY-PATH",        # Mixed dharma/karma — workable through discipline
    "intensive": "INTENSIVE-KARMIC-CURRICULUM", # Heavy karma signature — soul-school is intensive
    "moksha": "MOKSHA-EVOLUTIONARY-PATH",       # Strong moksha-axis — life is liberation-focused
}


# ── helpers ─────────────────────────────────────────────────────
def _planet(planets: List[Dict], name: str) -> Optional[Dict]:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            return p
    return None


def _planet_lon(planets: List[Dict], name: str) -> Optional[float]:
    p = _planet(planets, name)
    if p and isinstance(p.get("longitude"), (int, float)):
        return float(p["longitude"]) % 360.0
    return None


def _planet_sign(planets: List[Dict], name: str) -> Optional[str]:
    p = _planet(planets, name)
    if not p:
        return None
    s = p.get("sign")
    if s in SIGNS:
        return s
    lon = _planet_lon(planets, name)
    return SIGNS[int(lon // 30)] if lon is not None else None


def _planet_house(planets: List[Dict], asc_sign: str) -> Dict[str, int]:
    if asc_sign not in SIGNS:
        return {}
    asc_idx = SIGNS.index(asc_sign)
    out: Dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if p.get("house") and isinstance(p["house"], int):
            out[nm] = p["house"]
            continue
        sgn = _planet_sign(planets, nm) if nm else None
        if sgn:
            out[nm] = ((SIGNS.index(sgn) - asc_idx) % 12) + 1
    return out


def _occupants(planets: List[Dict], asc_sign: str, house_num: int) -> List[str]:
    h = _planet_house(planets, asc_sign)
    return sorted([nm for nm, hn in h.items() if hn == house_num])


def _dignity(planet: str, sign: Optional[str]) -> str:
    if not sign or planet not in EXALT:
        return "neutral"
    if sign == EXALT.get(planet):
        return "exalted"
    if sign == DEBIL.get(planet):
        return "debilitated"
    if sign in OWN.get(planet, []):
        return "own-sign"
    return "neutral"


def _has_aspect(planets: List[Dict], asc_sign: str, src: str, target_house: int) -> bool:
    src_house = _planet_house(planets, asc_sign).get(src, 0)
    if not src_house:
        return False
    diff = ((target_house - src_house) % 12) + 1
    aspects = {7}
    if src == "Mars":
        aspects |= {4, 8}
    elif src == "Jupiter":
        aspects |= {5, 9}
    elif src == "Saturn":
        aspects |= {3, 10}
    elif src in ("Rahu", "Ketu"):
        aspects |= {5, 9}
    return diff in aspects


# ── Atmakaraka (Jaimini Chara Karaka) ───────────────────────────
def _atmakaraka(planets: List[Dict]) -> Dict[str, Any]:
    """Identifies Atmakaraka via Jaimini Chara Karaka method: among the 7
    grahas, the one with the HIGHEST degree within its sign (i.e. lon mod 30)
    becomes the soul-significator. Soft-gates if longitude data missing.
    """
    candidates: List[tuple] = []
    missing: List[str] = []
    for nm in JAIMINI_KARAKA_PLANETS:
        lon = _planet_lon(planets, nm)
        if lon is None:
            missing.append(nm)
            continue
        deg_in_sign = lon % 30.0
        candidates.append((deg_in_sign, nm))

    # Atmakaraka requires longitude for ALL 7 Jaimini grahas — partial data
    # would yield a wrong "highest-degree" result and mislead the entire
    # capstone. Soft-gate with explicit reason rather than guessing.
    if missing:
        return {
            "available": False,
            "reason": (f"longitude missing for {len(missing)} of 7 Jaimini grahas "
                       f"({', '.join(missing)}) — Atmakaraka requires complete "
                       f"longitude data for all 7 to identify the soul-significator "
                       f"correctly."),
        }
    if not candidates:
        return {
            "available": False,
            "reason": "no longitude data — Atmakaraka requires planetary degrees",
        }

    # Sort by degree descending; highest = Atmakaraka
    candidates.sort(reverse=True, key=lambda x: x[0])
    ak_deg, ak_planet = candidates[0]
    ak_sign = _planet_sign(planets, ak_planet)
    ak_dignity = _dignity(ak_planet, ak_sign)

    return {
        "available": True,
        "atmakaraka": ak_planet,
        "atmakaraka_sign": ak_sign,
        "atmakaraka_degree": round(ak_deg, 4),
        "atmakaraka_dignity": ak_dignity,
        "method": ("Jaimini Chara Karaka — among the 7 traditional grahas (Sun through Saturn), "
                   "the one with the highest degree-within-its-sign becomes Atmakaraka "
                   "(soul-significator). This is your soul's primary teacher across lifetimes."),
        "all_karakas_ranked": [(c[1], round(c[0], 4)) for c in candidates],
    }


# ── Karakamsha (Atmakaraka's Navamsha sign) ─────────────────────
def _karakamsha(kundli: Dict, atmakaraka_planet: str) -> Dict[str, Any]:
    """Karakamsha = the sign occupied by Atmakaraka in the D9 Navamsha chart.
    This is the soul's arena of dharmic expression (Jaimini's primary
    method for life-mission discovery).
    """
    if not atmakaraka_planet:
        return {"available": False, "reason": "no atmakaraka"}

    d9 = kundli.get("d9") or kundli.get("navamsha") or kundli.get("D9")
    if not isinstance(d9, dict):
        return {
            "available": False,
            "reason": "D9 Navamsha not present in kundli — Karakamsha requires Navamsha data",
        }
    d9_planets = d9.get("planets") or []
    if not isinstance(d9_planets, list):
        return {"available": False, "reason": "D9 planets list missing"}

    ak_in_d9 = None
    for p in d9_planets:
        if isinstance(p, dict) and p.get("name") == atmakaraka_planet:
            ak_in_d9 = p
            break
    if not ak_in_d9:
        return {
            "available": False,
            "reason": f"Atmakaraka {atmakaraka_planet} not located in D9 chart",
        }

    karakamsha_sign = ak_in_d9.get("sign")
    if karakamsha_sign not in SIGNS:
        lon = ak_in_d9.get("longitude")
        if isinstance(lon, (int, float)):
            karakamsha_sign = SIGNS[int((float(lon) % 360.0) // 30)]
    if karakamsha_sign not in SIGNS:
        return {"available": False, "reason": "Karakamsha sign indeterminate"}

    return {
        "available": True,
        "karakamsha_sign": karakamsha_sign,
        "karakamsha_lord": SIGN_LORD[karakamsha_sign],
        "soul_arena": KARAKAMSHA_AREA.get(karakamsha_sign, "—"),
        "method": ("Karakamsha = Atmakaraka's sign in the D9 Navamsha chart. Per Jaimini, this "
                   "is the soul's primary arena of dharmic expression in this lifetime — the "
                   "field where the soul does its evolutionary work."),
    }


# ── Trikona-Trishadaya synthesis ────────────────────────────────
def _trikona_trishadaya(planets: List[Dict], asc_sign: str) -> Dict[str, Any]:
    """Counts dharma-trikona (1/5/9) strength vs karma-houses (3/6/10/11)
    strength to characterise the soul's primary mode this lifetime.
    """
    p_house = _planet_house(planets, asc_sign)
    asc_idx = SIGNS.index(asc_sign)

    benefics = {"Jupiter", "Venus", "Moon", "Mercury"}
    malefics = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}

    dharma_score = 0
    karma_score = 0
    dharma_planets: List[str] = []
    karma_planets: List[str] = []

    for nm, hn in p_house.items():
        if hn in DHARMA_TRIKONA:
            weight = 2 if nm in benefics else 1
            dharma_score += weight
            dharma_planets.append(f"{nm} in H{hn}")
        if hn in KARMA_HOUSES:
            # 3rd house and 11th house slightly favour malefics for action/gain;
            # 6th & 10th get malefics' work-energy. Benefic in 6/3/11 is mild.
            weight = 2 if nm in malefics else 1
            karma_score += weight
            karma_planets.append(f"{nm} in H{hn}")

    # Lagna lord placement
    lagna_lord = SIGN_LORD[asc_sign]
    ll_house = p_house.get(lagna_lord, 0)
    if ll_house in DHARMA_TRIKONA:
        dharma_score += 3
    if ll_house in KARMA_HOUSES:
        karma_score += 2

    # 9L (dharma lord) placement
    ninth_lord = SIGN_LORD[SIGNS[(asc_idx + 8) % 12]]
    nl_house = p_house.get(ninth_lord, 0)
    if nl_house in DHARMA_TRIKONA | KENDRA:
        dharma_score += 3

    # 10L (karma lord) placement
    tenth_lord = SIGN_LORD[SIGNS[(asc_idx + 9) % 12]]
    tl_house = p_house.get(tenth_lord, 0)
    if tl_house in KARMA_HOUSES | KENDRA:
        karma_score += 3

    total = dharma_score + karma_score
    if total == 0:
        dharma_pct = karma_pct = 50
    else:
        dharma_pct = round((dharma_score / total) * 100)
        karma_pct = 100 - dharma_pct

    if dharma_pct >= 60:
        mode = "DHARMA-DOMINANT"
        narrative = ("Your chart is dharma-dominant — the soul leans toward wisdom, philosophy, "
                     "teaching, blessings-flow. Effort-houses are present but secondary; you "
                     "achieve more through alignment than through struggle.")
    elif karma_pct >= 60:
        mode = "KARMA-DOMINANT"
        narrative = ("Your chart is karma-dominant — the soul learns through action, struggle, "
                     "obstacle-conquest. Dharma is woven in but you are here to BUILD, FIGHT, "
                     "TRANSFORM through sustained effort.")
    else:
        mode = "DHARMA-KARMA-BALANCED"
        narrative = ("Your chart is dharma-karma balanced — the soul oscillates between wisdom "
                     "and action; periods of teaching alternate with periods of building. This "
                     "balance IS your gift — you can move between modes consciously.")

    return {
        "dharma_score": dharma_score,
        "karma_score": karma_score,
        "dharma_pct": dharma_pct,
        "karma_pct": karma_pct,
        "mode": mode,
        "narrative": narrative,
        "dharma_planets": dharma_planets[:6],
        "karma_planets": karma_planets[:6],
        "lagna_lord": lagna_lord,
        "ninth_lord": ninth_lord,
        "tenth_lord": tenth_lord,
    }


# ── Life-Mission Verdict (5 archetypes) ─────────────────────────
def _life_mission(planets: List[Dict], asc_sign: str,
                   atmakaraka: Optional[str],
                   karakamsha_sign: Optional[str],
                   trikona_mode: str) -> Dict[str, Any]:
    """Picks one of 5 life-mission archetypes by composite signature.
    Soft-gates Atmakaraka/Karakamsha — falls back to Lagna+chart-pattern.
    """
    p_house = _planet_house(planets, asc_sign)
    twelfth_occ = _occupants(planets, asc_sign, 12)
    eighth_occ = _occupants(planets, asc_sign, 8)

    # Score each archetype 0-100 from chart signatures
    scores: Dict[str, int] = {k: 0 for k in LIFE_MISSIONS}

    # Dharma-sage signals
    if trikona_mode == "DHARMA-DOMINANT":
        scores["dharma_sage"] += 25
    if p_house.get("Jupiter") in DHARMA_TRIKONA:
        scores["dharma_sage"] += 20
    asc_idx = SIGNS.index(asc_sign)
    ninth_lord = SIGN_LORD[SIGNS[(asc_idx + 8) % 12]]
    if p_house.get(ninth_lord) in KENDRA | TRIKONA:
        scores["dharma_sage"] += 15
    if karakamsha_sign in ("Sagittarius", "Pisces"):
        scores["dharma_sage"] += 15
    if atmakaraka == "Jupiter":
        scores["dharma_sage"] += 15

    # Karma-warrior signals
    if trikona_mode == "KARMA-DOMINANT":
        scores["karma_warrior"] += 25
    if p_house.get("Mars") in KENDRA | KARMA_HOUSES:
        scores["karma_warrior"] += 20
    if p_house.get("Saturn") in (3, 6, 10, 11):
        scores["karma_warrior"] += 15
    if karakamsha_sign in ("Aries", "Scorpio", "Capricorn"):
        scores["karma_warrior"] += 15
    if atmakaraka in ("Mars", "Saturn", "Sun"):
        scores["karma_warrior"] += 12

    # Bhakti-devotee signals
    moon_dignity = _dignity("Moon", _planet_sign(planets, "Moon"))
    if moon_dignity in ("exalted", "own-sign"):
        scores["bhakti_devotee"] += 18
    if p_house.get("Venus") in KENDRA | TRIKONA:
        scores["bhakti_devotee"] += 18
    if p_house.get("Moon") in (4, 5):
        scores["bhakti_devotee"] += 15
    if karakamsha_sign in ("Cancer", "Taurus", "Libra"):
        scores["bhakti_devotee"] += 15
    if atmakaraka in ("Moon", "Venus"):
        scores["bhakti_devotee"] += 15

    # Jnana-seeker signals
    if p_house.get("Mercury") in KENDRA | TRIKONA:
        scores["jnana_seeker"] += 18
    if p_house.get("Saturn") in (8, 12):
        scores["jnana_seeker"] += 15
    if "Ketu" in eighth_occ:
        scores["jnana_seeker"] += 18
    if karakamsha_sign in ("Gemini", "Virgo", "Aquarius"):
        scores["jnana_seeker"] += 15
    if atmakaraka in ("Mercury", "Ketu"):
        scores["jnana_seeker"] += 15

    # Moksha-recluse signals
    if "Ketu" in twelfth_occ:
        scores["moksha_recluse"] += 25
    if p_house.get("Saturn") == 12:
        scores["moksha_recluse"] += 18
    if karakamsha_sign == "Pisces":
        scores["moksha_recluse"] += 18
    if len(twelfth_occ) >= 2:
        scores["moksha_recluse"] += 15
    if _planet_sign(planets, "Ketu") in ("Pisces", "Sagittarius"):
        scores["moksha_recluse"] += 12

    # Pick winner
    winner_key = max(scores, key=lambda k: scores[k])
    winner = LIFE_MISSIONS[winner_key]
    # Runner-up for nuance
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    runner_up_key = sorted_scores[1][0] if len(sorted_scores) > 1 else None
    runner_up = LIFE_MISSIONS[runner_up_key] if runner_up_key else None

    return {
        "winner_key": winner_key,
        "mission_token": winner["token"],
        "mission_description": winner["description"],
        "winner_score": scores[winner_key],
        "runner_up_token": runner_up["token"] if runner_up else None,
        "runner_up_score": sorted_scores[1][1] if len(sorted_scores) > 1 else 0,
        "all_scores": scores,
        "decision_method": ("Composite signature: trikona-mode + Atmakaraka + Karakamsha sign + "
                            "key planet placements scored across 5 archetypes; highest score = "
                            "primary mission, second-highest = secondary thread."),
    }


# ── Spiritual Evolution Arc (current dasha vs mission) ──────────
def _evolution_arc(kundli: Dict, planets: List[Dict], asc_sign: str,
                    atmakaraka: Optional[str], mission_key: str) -> Dict[str, Any]:
    """Reads current MD/AD against the mission-aligned activator set."""
    dasha = kundli.get("dasha") or kundli.get("currentDasha") or {}
    md_lord = (dasha.get("mahaDasha") or dasha.get("md") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    ad_lord = (dasha.get("antarDasha") or dasha.get("ad") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    if not md_lord:
        md_lord = dasha.get("mahadasha_lord") if isinstance(dasha, dict) else None
        ad_lord = dasha.get("antardasha_lord") if isinstance(dasha, dict) else None

    asc_idx = SIGNS.index(asc_sign)
    ninth_lord = SIGN_LORD[SIGNS[(asc_idx + 8) % 12]]
    tenth_lord = SIGN_LORD[SIGNS[(asc_idx + 9) % 12]]

    # Mission-aligned activators
    mission_activators: Dict[str, set] = {
        "dharma_sage": {"Jupiter", ninth_lord, atmakaraka or ""},
        "karma_warrior": {"Mars", "Saturn", tenth_lord, atmakaraka or ""},
        "bhakti_devotee": {"Moon", "Venus", atmakaraka or ""},
        "jnana_seeker": {"Mercury", "Saturn", "Ketu", atmakaraka or ""},
        "moksha_recluse": {"Ketu", "Saturn", SIGN_LORD[SIGNS[(asc_idx + 11) % 12]],
                            atmakaraka or ""},
    }
    activators = mission_activators.get(mission_key, set()) - {""}

    md_aligned = md_lord in activators if md_lord else False
    ad_aligned = ad_lord in activators if ad_lord else False

    if md_aligned and ad_aligned:
        arc_status = "FULL-ALIGNMENT WINDOW"
        arc_note = (f"Both MD ({md_lord}) and AD ({ad_lord}) align with your mission-activator "
                    f"set — this is a FULL-ALIGNMENT period; your soul's evolutionary current "
                    f"flows directly through your daily life. Lean fully into your mission now.")
    elif md_aligned:
        arc_status = "MISSION-ACTIVE WINDOW"
        arc_note = (f"MD lord {md_lord} aligns with your mission activators — primary current "
                    f"flowing; AD ({ad_lord or 'unknown'}) brings textural variation. Mission-"
                    f"work compounds in this window.")
    elif ad_aligned:
        arc_status = "PREPARATION WINDOW"
        arc_note = (f"AD lord {ad_lord} aligns inside non-aligned MD ({md_lord or 'unknown'}) — "
                    f"shorter sub-window for mission-work; use to prepare, learn, build "
                    f"foundations for the next aligned MD.")
    else:
        arc_status = "INTEGRATION WINDOW"
        arc_note = (f"Neither MD ({md_lord or 'unknown'}) nor AD ({ad_lord or 'unknown'}) is a "
                    f"primary mission-activator — this is an INTEGRATION period; consolidate "
                    f"prior learnings, pay debts, prepare inner ground for the next aligned arc.")

    return {
        "current_md": md_lord or "—",
        "current_ad": ad_lord or "—",
        "mission_activators": sorted(activators),
        "md_aligned": md_aligned,
        "ad_aligned": ad_aligned,
        "arc_status": arc_status,
        "arc_note": arc_note,
    }


# ── main ────────────────────────────────────────────────────────
def compute_moksha_bundle(kundli: Dict[str, Any], dob: str,
                           driver: int, conductor: int) -> Dict[str, Any]:
    """T17 Moksha synthesis bundle. Hard data gate; never fabricates.
    Asc + 9 grahas required. Atmakaraka (longitudes) and Karakamsha (D9)
    are soft-gated with graceful fallbacks.
    """
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"
        return out
    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []
    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing ({asc!r})"
        return out
    if not isinstance(planets, list) or len(planets) < 9:
        out["reason"] = "planets list incomplete"
        return out
    required = {"Sun", "Moon", "Jupiter", "Mars", "Venus", "Mercury", "Saturn", "Rahu", "Ketu"}
    pn = {p.get("name") for p in planets if isinstance(p, dict)}
    missing = required - pn
    if missing:
        out["reason"] = f"missing grahas: {sorted(missing)}"
        return out

    asc_idx = SIGNS.index(asc)
    p_house = _planet_house(planets, asc)

    # ── 1. Moksha Bhava (12th revisited as moksha-axis) ────────
    twelfth_sign = SIGNS[(asc_idx + 11) % 12]
    twelfth_lord = SIGN_LORD[twelfth_sign]
    twelfth_occ = _occupants(planets, asc, 12)
    ketu_sign = _planet_sign(planets, "Ketu") or "—"
    ketu_house = p_house.get("Ketu", 0)

    moksha_signals: List[str] = []
    if "Ketu" in twelfth_occ:
        moksha_signals.append("Ketu in 12th — strong moksha-axis; soul gravitates toward "
                              "dissolution, retreat, spiritual dispersion.")
    if "Jupiter" in twelfth_occ:
        moksha_signals.append("Jupiter in 12th — dharmic-moksha; soul liberates through "
                              "wisdom, teaching-into-silence, philosophical surrender.")
    if "Saturn" in twelfth_occ:
        moksha_signals.append("Saturn in 12th — disciplined-moksha; soul liberates through "
                              "long-arc renunciation, monastic structure, austerity.")
    if ketu_sign in ("Pisces", "Sagittarius"):
        moksha_signals.append(f"Ketu in {ketu_sign} — past-life dharmic-moksha karma carried "
                              f"forward; this lifetime continues that arc.")
    if _has_aspect(planets, asc, "Jupiter", 12):
        moksha_signals.append("Jupiter aspects 12th — Guru-blessing on the moksha-house; "
                              "spiritual study and pilgrimage accelerate liberation.")

    moksha_bhava = {
        "twelfth_sign": twelfth_sign,
        "twelfth_lord": twelfth_lord,
        "twelfth_occupants": twelfth_occ,
        "ketu_sign": ketu_sign,
        "ketu_house": ketu_house,
        "moksha_signals": moksha_signals[:6],
        "moksha_signal_count": len(moksha_signals),
        "note": ("Moksha Bhava (12th house) viewed as the soul's liberation-axis — distinct "
                 "from the foreign-travel reading in T15. Here we read 12th + Ketu signatures "
                 "for the soul's dissolution-arc and final-release karma."),
    }

    # ── 2. Atmakaraka ──────────────────────────────────────────
    ak = _atmakaraka(planets)

    # ── 3. Karakamsha ──────────────────────────────────────────
    if ak.get("available"):
        km = _karakamsha(kundli, ak["atmakaraka"])
    else:
        km = {"available": False, "reason": "atmakaraka unavailable"}

    # ── 4. Trikona-Trishadaya synthesis ────────────────────────
    trikona = _trikona_trishadaya(planets, asc)

    # ── 5. Life-Mission Verdict ────────────────────────────────
    mission = _life_mission(
        planets, asc,
        ak.get("atmakaraka") if ak.get("available") else None,
        km.get("karakamsha_sign") if km.get("available") else None,
        trikona["mode"],
    )

    # ── 6. Spiritual Evolution Arc ─────────────────────────────
    evo = _evolution_arc(
        kundli, planets, asc,
        ak.get("atmakaraka") if ak.get("available") else None,
        mission["winner_key"],
    )

    # ── 7. Final Life-Mastery Verdict ──────────────────────────
    # Decision tree (priority order):
    # 1. MOKSHA if 3+ moksha signals OR mission=moksha_recluse
    # 2. INTENSIVE if karma_pct >= 65 OR (mission=karma_warrior AND dharma_pct < 45)
    # 3. BLESSED if dharma_pct >= 60 AND moksha_signal_count <= 1 AND mission_winner_score >= 50
    # 4. BALANCED otherwise
    if (moksha_bhava["moksha_signal_count"] >= 3
            or mission["winner_key"] == "moksha_recluse"):
        final_verdict = FINAL_VERDICT_TOKENS["moksha"]
    elif (trikona["karma_pct"] >= 65
            or (mission["winner_key"] == "karma_warrior" and trikona["dharma_pct"] < 45)):
        final_verdict = FINAL_VERDICT_TOKENS["intensive"]
    elif (trikona["dharma_pct"] >= 60
            and moksha_bhava["moksha_signal_count"] <= 1
            and mission["winner_score"] >= 50):
        final_verdict = FINAL_VERDICT_TOKENS["blessed"]
    else:
        final_verdict = FINAL_VERDICT_TOKENS["balanced"]

    # 7-step soul-blueprint
    soul_blueprint: List[str] = []
    soul_blueprint.append(f"Soul-significator (Atmakaraka): "
                           f"{ak.get('atmakaraka', 'requires longitude data')} — your primary "
                           f"karmic teacher across lifetimes; align your daily actions with this "
                           f"planet's qualities.")
    if km.get("available"):
        soul_blueprint.append(f"Soul-arena (Karakamsha sign): {km['karakamsha_sign']} — "
                               f"{km['soul_arena']}")
    else:
        soul_blueprint.append("Soul-arena (Karakamsha): D9 Navamsha data not available; arena "
                               "inferred from ascendant + Atmakaraka placement above.")
    soul_blueprint.append(f"Mission archetype: {mission['mission_token']} — "
                           f"{mission['mission_description']}")
    soul_blueprint.append(f"Trikona-Karma mode: {trikona['mode']} (dharma {trikona['dharma_pct']}% "
                           f"vs karma {trikona['karma_pct']}%) — {trikona['narrative']}")
    soul_blueprint.append(f"Current evolutionary arc: {evo['arc_status']} — {evo['arc_note']}")
    soul_blueprint.append(f"Numerology integration: Driver {driver} + Conductor {conductor} "
                           f"close the karmic loop; your name + birth-vibration aligns the "
                           f"soul-mission with daily-life expression (see Tier 1 Life Path).")
    soul_blueprint.append("Practice: Synthesize all 17 tiers into one daily morning intention — "
                          "the chart is the map, but YOUR awakened CHOICE walks the path. "
                          "Re-read this report quarterly to track your own evolution.")

    summary_lines = [
        f"Moksha Bhava: 12th sign {twelfth_sign} (lord {twelfth_lord}); Ketu in "
        f"{ketu_sign} H{ketu_house}; {moksha_bhava['moksha_signal_count']} moksha signals.",
        f"Atmakaraka (soul-significator): "
        f"{ak.get('atmakaraka', 'unavailable — needs longitude data')}"
        f"{' in ' + ak['atmakaraka_sign'] if ak.get('available') and ak.get('atmakaraka_sign') else ''}.",
        f"Karakamsha (soul-arena): "
        f"{km.get('karakamsha_sign', 'D9 not available')}.",
        f"Trikona-Karma mode: {trikona['mode']} "
        f"(dharma {trikona['dharma_pct']}% / karma {trikona['karma_pct']}%).",
        f"Life-mission archetype: {mission['mission_token']} "
        f"(score {mission['winner_score']}, runner-up {mission.get('runner_up_token', '—')}).",
        f"Current evolutionary arc: {evo['arc_status']} "
        f"(MD={evo['current_md']}, AD={evo['current_ad']}).",
        f"FINAL VERDICT: {final_verdict}.",
    ]

    out.update({
        "available": True,
        "ascendant": asc,
        "moksha_bhava": moksha_bhava,
        "atmakaraka": ak,
        "karakamsha": km,
        "trikona_synthesis": trikona,
        "life_mission": mission,
        "evolution_arc": evo,
        "synthesis": {
            "final_verdict_token": final_verdict,
            "summary_lines": summary_lines,
            "soul_blueprint": soul_blueprint,
            "driver_number": driver,
            "conductor_number": conductor,
            "closing_message": ("This is the capstone of your 17-tier Life Mastery Report. The "
                                "chart shows the karma you arrived with; the choices you make "
                                "from this awareness write the next chapter. Read this report "
                                "quarterly. Live the practices. The soul evolves through "
                                "conscious participation, not through prediction."),
        },
    })
    return out
