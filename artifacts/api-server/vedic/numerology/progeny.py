"""Tier 13 — Children, Progeny & Education Deep Audit engine.

Chart-based progeny prognosis: Putra Bhava (5th house + lord), Putrakaraka
(Jupiter — primary; 5L — secondary), D7 Saptamsa picture (progeny chart),
classical Putra-prapti Yogas + obstructions audit, current dasha child-timing
window, karmic / shapa signatures (Naga/Pitru/Sarpa/Brahma/Matru shapa flags),
and a synthesis with child profile + education path + actionable plan.

Hard data gate (asc + 9 grahas + dasha). Falls back gracefully if D7 missing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

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
BENEFICS = {"Jupiter", "Venus", "Mercury"}
MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}

# Child-temperament hints by 5th-house sign (BPHS / Phaladeepika lineage)
FIFTH_SIGN_CHILD: Dict[str, str] = {
    "Aries": "energetic, athletic, fiery, leader-type child; early walker, courageous, may be hot-tempered.",
    "Taurus": "steady, sensual, art-loving, well-built child; loves food, music, comfort; loyal but stubborn.",
    "Gemini": "communicative, witty, twin-likelihood, intelligent, restless; gifted in language and learning.",
    "Cancer": "emotionally sensitive, mother-bonded, fair-skinned, intuitive; daughter-leaning indicator; nurturing nature.",
    "Leo": "proud, dignified, leader-type, dramatic child; commands attention, sometimes only-child energy.",
    "Virgo": "intelligent, analytical, slim, perfectionist child; later progeny possible; service-minded.",
    "Libra": "charming, beautiful, harmony-loving child; artistic, diplomatic; partnership-natured.",
    "Scorpio": "intense, magnetic, deep-eyed, secretive child; powerful psychic gifts; transformative bond.",
    "Sagittarius": "philosophical, optimistic, freedom-loving, well-built; teacher / wisdom child; foreign exposure likely.",
    "Capricorn": "mature beyond years, disciplined, ambitious, late-bloomer; karmic-responsibility child.",
    "Aquarius": "unconventional, intellectual, humanitarian, tech-friendly child; needs space, friend-type bond.",
    "Pisces": "compassionate, artistic, dreamy, spiritual child; soft features; karmic-soul child.",
}

# Education path by 5th-house sign
FIFTH_SIGN_EDUCATION: Dict[str, str] = {
    "Aries": "engineering, sports science, military, surgery, entrepreneurship — action-oriented fields.",
    "Taurus": "fine arts, music, finance/banking, agriculture, hospitality, beauty/luxury industry.",
    "Gemini": "communication, journalism, IT/coding, languages, marketing, teaching, writing.",
    "Cancer": "psychology, hospitality, food sciences, real estate, history, women-focused fields.",
    "Leo": "leadership, government, performance arts, politics, gold/luxury trade, public administration.",
    "Virgo": "medicine, accounting, data analysis, research, editing, audit — detail-precision fields.",
    "Libra": "law, design, fashion, diplomacy, partnership-businesses, mediation.",
    "Scorpio": "research, occult/mantra, surgery, intelligence/investigation, psychology, transformative healing.",
    "Sagittarius": "law, philosophy, higher academia, religion, foreign-affairs, publishing, international trade.",
    "Capricorn": "engineering, govt-administration, mining, structural fields, traditional professions; slow but solid mastery.",
    "Aquarius": "tech/IT, science, social work, astrology, networking, innovation, large-system reform.",
    "Pisces": "spirituality, healing arts, music, charitable service, foreign-lands work, film/imagination.",
}

# Verdict tokens locked for synthesis validator
SYNTHESIS_TOKENS = {
    "blessed": "BLESSED-PROGENY-PATH",
    "delayed": "DELAYED-DHARMIC-PROGENY",
    "karmic": "KARMIC-PROGENY-PATH",
    "shapa": "SHAPA-CLEANSING-REQUIRED",
}


# ── helpers (mirror marriage.py) ─────────────────────────────────
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


def _d7_data(kundli: Dict) -> Dict[str, Any]:
    """D7 Saptamsa = progeny chart. Falls back to empty if not present."""
    dc = kundli.get("divisionalCharts") or {}
    d7 = dc.get("D7") or dc.get("d7") or {}
    if not isinstance(d7, dict):
        return {}
    asc_d7 = d7.get("ascendant") or d7.get("Ascendant")
    plist = []
    for k in ("planets", "Planets"):
        if isinstance(d7.get(k), list):
            plist = d7[k]
            break
    return {"ascendant": asc_d7, "planets": plist}


def _planet_sign_in_chart(plist: List[Dict], name: str) -> Optional[str]:
    for p in plist:
        if isinstance(p, dict) and p.get("name") == name:
            s = p.get("sign")
            if s in SIGNS:
                return s
    return None


def _has_aspect(planets: List[Dict], asc_sign: str, src: str, target_house: int) -> bool:
    """Simple Vedic aspect check: src planet aspects target_house?
    All planets aspect 7th from self. Mars also 4,8; Jupiter 5,9; Saturn 3,10; Rahu/Ketu 5,7,9."""
    src_house = _planet_house(planets, asc_sign).get(src, 0)
    if not src_house:
        return False
    diff = ((target_house - src_house) % 12) + 1  # signs from src to target (1..12)
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


# ── Putra Yogas audit (analogous to Mangal audit) ────────────────
def _putra_yogas_audit(planets: List[Dict], asc_sign: str,
                        fifth_lord: str) -> Dict[str, Any]:
    """Detect classical Putra-prapti Yogas + obstructions."""
    p_house = _planet_house(planets, asc_sign)
    asc_idx = SIGNS.index(asc_sign)
    ninth_lord = SIGN_LORD[SIGNS[(asc_idx + 8) % 12]]
    eleventh_lord = SIGN_LORD[SIGNS[(asc_idx + 10) % 12]]
    second_lord = SIGN_LORD[SIGNS[(asc_idx + 1) % 12]]

    fifth_occ = _occupants(planets, asc_sign, 5)
    fifth_lord_house = p_house.get(fifth_lord, 0)
    jup_house = p_house.get("Jupiter", 0)
    jup_sign = _planet_sign(planets, "Jupiter")
    jup_dignity = _dignity("Jupiter", jup_sign)

    yogas: List[str] = []

    # 1. 5L + 9L conjunction or mutual aspect (most powerful Putra-yoga)
    if fifth_lord == ninth_lord or p_house.get(fifth_lord) == p_house.get(ninth_lord):
        yogas.append(f"5L–9L conjunction yoga (5L & 9L = {fifth_lord}/{ninth_lord}) — "
                     f"strong Putra-prapti combo per BPHS.")

    # 2. Jupiter in 5th in own/exalted
    if jup_house == 5 and jup_dignity in ("exalted", "own-sign"):
        yogas.append(f"Jupiter ({jup_dignity}) in 5th — premium Putra-karaka placement; "
                     f"intelligent, blessed progeny.")
    elif jup_house == 5:
        yogas.append("Jupiter in 5th — Putrakaraka in Putra Bhava; basic Putra-yoga active.")

    # 3. Jupiter aspects 5th house (5/9 aspect from another house)
    if _has_aspect(planets, asc_sign, "Jupiter", 5) and jup_house != 5:
        yogas.append(f"Jupiter aspects the 5th from H{jup_house} — Putrakaraka guards the "
                     f"Putra Bhava; supportive yoga.")

    # 4. 5L in Kendra or Trikona
    if fifth_lord_house in (KENDRA | TRIKONA):
        yogas.append(f"5L {fifth_lord} in H{fifth_lord_house} (Kendra/Trikona) — "
                     f"Putra Bhava lord well-placed.")

    # 5. 5L + 11L combo (Putra-prapti via gain-house)
    if fifth_lord == eleventh_lord or p_house.get(fifth_lord) == p_house.get(eleventh_lord):
        yogas.append(f"5L–11L combo (5L {fifth_lord}, 11L {eleventh_lord}) — "
                     f"Putra-yoga via gain-house, indicates progeny brings prosperity.")

    # 6. Moon + Jupiter conjunction (Gajakesari-flavoured progeny boost)
    if p_house.get("Moon") == p_house.get("Jupiter") and p_house.get("Moon"):
        yogas.append("Moon–Jupiter conjunction (Gajakesari resonance) — "
                     "noble-character progeny, mother–child bond strong.")

    # 7. Santati Yoga (Jup + Moon + 5L all dignified)
    if (jup_dignity in ("exalted", "own-sign") and
        _dignity("Moon", _planet_sign(planets, "Moon")) in ("exalted", "own-sign") and
        _dignity(fifth_lord, _planet_sign(planets, fifth_lord)) in ("exalted", "own-sign")):
        yogas.append("Santati Yoga (Jup + Moon + 5L all in own/exalted) — rare classical "
                     "blessing for blessed lineage.")

    obstructions: List[str] = []

    # Obstructions
    if "Saturn" in fifth_occ:
        obstructions.append("Saturn in 5th — DELAY signature for progeny (often after 30); "
                            "may indicate karmic-responsibility child.")
    if "Rahu" in fifth_occ:
        obstructions.append("Rahu in 5th — unconventional progeny path (adoption, IVF, foreign-born); "
                            "Sarpa-shapa risk; strict remedies needed.")
    if "Ketu" in fifth_occ:
        obstructions.append("Ketu in 5th — past-life-completed progeny karma; risk of detachment "
                            "or single-child; spiritual progeny indicator.")
    if "Mars" in fifth_occ:
        obstructions.append("Mars in 5th — miscarriage / aggressive progeny risk; needs Mangal-shanti "
                            "before conception attempts.")
    if "Sun" in fifth_occ:
        obstructions.append("Sun in 5th — ego-clash with progeny; fewer children; first-child often delayed.")
    if fifth_lord_house in DUSTHANA:
        obstructions.append(f"5L {fifth_lord} in H{fifth_lord_house} (Dusthana) — "
                            f"progeny karma needs purification.")
    if jup_dignity == "debilitated":
        obstructions.append("Jupiter debilitated — Putrakaraka weak; Jupiter remedies essential "
                            "(Thursday fasts, Brihaspati mantra, yellow gram donation).")

    # Severity & verdict
    yoga_count = len(yogas)
    obs_count = len(obstructions)
    score = max(0, min(100, 50 + (yoga_count * 12) - (obs_count * 10)))

    if score >= 70 and obs_count <= 1:
        severity = "BLESSED"
        verdict = ("Multiple Putra-yogas active with minimal obstruction — "
                   "natural progeny path with classical blessings.")
    elif score >= 50:
        severity = "MODERATE"
        verdict = ("Mixed signals — yogas present but some obstructions; conscious "
                   "remedies + timing-care will produce results.")
    elif score >= 30:
        severity = "CHALLENGED"
        verdict = ("Obstructions outweigh yogas — significant progeny-karma work "
                   "required; consider classical remedies and medical support together.")
    else:
        severity = "DENSE-KARMA"
        verdict = ("Heavy progeny-karma signature — shapa cleansing, classical "
                   "homas, and patient devata-aaradhana strongly indicated.")

    return {
        "yogas": yogas[:7],
        "obstructions": obstructions[:6],
        "yoga_count": yoga_count,
        "obstruction_count": obs_count,
        "score": score,
        "severity": severity,
        "verdict": verdict,
        "fifth_occupants": fifth_occ,
        "fifth_lord_house": fifth_lord_house,
    }


# ── Children Timing Window ───────────────────────────────────────
def _children_timing(kundli: Dict, planets: List[Dict], asc_sign: str,
                      fifth_lord: str) -> Dict[str, Any]:
    dasha = kundli.get("dasha") or kundli.get("currentDasha") or {}
    md_lord = (dasha.get("mahaDasha") or dasha.get("md") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    ad_lord = (dasha.get("antarDasha") or dasha.get("ad") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    if not md_lord:
        md_lord = dasha.get("mahadasha_lord") if isinstance(dasha, dict) else None
        ad_lord = dasha.get("antardasha_lord") if isinstance(dasha, dict) else None

    asc_idx = SIGNS.index(asc_sign)
    second_lord = SIGN_LORD[SIGNS[(asc_idx + 1) % 12]]   # family-formation
    eleventh_lord = SIGN_LORD[SIGNS[(asc_idx + 10) % 12]]  # gain
    occ_5th = _occupants(planets, asc_sign, 5)

    activators = {fifth_lord, "Jupiter", second_lord, eleventh_lord}
    for p in occ_5th:
        activators.add(p)
    activators.discard("—")

    md_active = md_lord in activators if md_lord else False
    ad_active = ad_lord in activators if ad_lord else False

    if md_active and ad_active:
        window_status = "ACTIVE PROGENY WINDOW"
        window_note = (f"Both MD ({md_lord}) and AD ({ad_lord}) are progeny-activators — "
                       f"this is a strongly supportive conception/birth window per dasha logic.")
    elif md_active:
        window_status = "WARM PROGENY WINDOW"
        window_note = (f"MD lord {md_lord} is a progeny-activator — primary timing pull alive; "
                       f"watch for AD/PD of Jupiter/5L/2L/11L to lock the event.")
    elif ad_active:
        window_status = "TACTICAL WINDOW"
        window_note = (f"AD lord {ad_lord} is a progeny-activator inside non-aligned MD "
                       f"({md_lord or 'unknown'}) — short opportunity window; act consciously.")
    else:
        window_status = "PREP WINDOW"
        window_note = (f"Neither MD ({md_lord or 'unknown'}) nor AD ({ad_lord or 'unknown'}) "
                       f"is a primary progeny-activator — use this period for Putra-remedies, "
                       f"Santana Gopala mantra, and physical/medical preparation.")

    return {
        "current_md": md_lord or "—",
        "current_ad": ad_lord or "—",
        "activators": sorted(activators),
        "fifth_lord": fifth_lord,
        "second_lord": second_lord,
        "eleventh_lord": eleventh_lord,
        "md_is_activator": md_active,
        "ad_is_activator": ad_active,
        "window_status": window_status,
        "window_note": window_note,
    }


# ── Karmic / Shapa Signatures ────────────────────────────────────
def _shapa_signatures(planets: List[Dict], asc_sign: str,
                       fifth_lord: str) -> Dict[str, Any]:
    """Detect classical 'shapa' (curse) signatures affecting progeny."""
    p_house = _planet_house(planets, asc_sign)
    fifth_occ = _occupants(planets, asc_sign, 5)
    ninth_occ = _occupants(planets, asc_sign, 9)

    flags: List[str] = []

    # Naga / Sarpa shapa — Rahu in 5th, or Rahu+5L conjunction, or Rahu-Ketu axis on 5/11
    if "Rahu" in fifth_occ:
        flags.append("Sarpa Shapa indicator — Rahu in 5th house; classical remedy: "
                     "Naga-pratishtha or Sarpa-suktam recitation.")
    if p_house.get("Rahu") == p_house.get(fifth_lord) and p_house.get("Rahu"):
        flags.append(f"Naga Shapa indicator — Rahu conjunct 5L ({fifth_lord}); "
                     f"perform Naga-bali or Subrahmanya puja.")
    if (p_house.get("Rahu") == 5 and p_house.get("Ketu") == 11) or \
       (p_house.get("Rahu") == 11 and p_house.get("Ketu") == 5):
        flags.append("Rahu-Ketu axis on 5/11 (progeny-gain axis) — Kala-Sarpa signature "
                     "over Putra Bhava; full Kala-Sarpa shanti recommended.")

    # Pitru shapa — Sun + Rahu in 5th or 9th
    if "Sun" in fifth_occ and "Rahu" in fifth_occ:
        flags.append("Pitru Shapa indicator — Sun+Rahu in 5th; perform Pitru-tarpana, "
                     "Tila-tarpan on Amavasya, Narayana-bali if intense.")
    if "Sun" in ninth_occ and "Rahu" in ninth_occ:
        flags.append("Pitru Shapa indicator — Sun+Rahu in 9th (Pitru bhava); "
                     "Pitru-paksha tarpana annually essential.")

    # Brahma shapa — Jupiter afflicted in 5th (Jup + Rahu/Ketu/Saturn)
    jup_h = p_house.get("Jupiter", 0)
    if jup_h == 5 and any(p in fifth_occ for p in ("Rahu", "Ketu", "Saturn")):
        flags.append("Brahma Shapa indicator — Jupiter in 5th afflicted by Rahu/Ketu/Saturn; "
                     "perform Guru-graha shanti, Vishnu-sahasranama daily, donate to learned brahmins.")

    # Matru shapa — Moon + Saturn/Rahu in 4th or 5th
    moon_h = p_house.get("Moon", 0)
    sat_h = p_house.get("Saturn", 0)
    if moon_h in (4, 5) and (sat_h == moon_h or "Rahu" in _occupants(planets, asc_sign, moon_h)):
        flags.append(f"Matru Shapa indicator — Moon afflicted in H{moon_h}; honour mother / "
                     f"maternal lineage; recite Sri Suktam, donate dairy to women.")

    # Preta shapa — Saturn + Ketu conjunction
    if p_house.get("Saturn") == p_house.get("Ketu") and p_house.get("Saturn"):
        flags.append("Preta-related karma — Saturn+Ketu conjunction; perform Pinda-dana annually "
                     "for unsatisfied ancestral souls.")

    # Karmic load score
    score = (
        (15 if "Rahu" in fifth_occ else 0)
        + (10 if "Ketu" in fifth_occ else 0)
        + (15 if "Saturn" in fifth_occ else 0)
        + (10 if "Mars" in fifth_occ else 0)
        + (8 if "Sun" in fifth_occ and "Rahu" in fifth_occ else 0)
        + (12 if jup_h == 5 and any(p in fifth_occ for p in ("Rahu", "Ketu", "Saturn")) else 0)
    )

    if score >= 30:
        karmic_verdict = "STRONG-SHAPA"
    elif score >= 15:
        karmic_verdict = "MODERATE-KARMIC"
    else:
        karmic_verdict = "LIGHT-KARMIC"

    return {
        "fifth_occupants": fifth_occ,
        "ninth_occupants": ninth_occ,
        "rahu_in_5th": "Rahu" in fifth_occ,
        "ketu_in_5th": "Ketu" in fifth_occ,
        "saturn_in_5th": "Saturn" in fifth_occ,
        "mars_in_5th": "Mars" in fifth_occ,
        "karmic_score": score,
        "karmic_verdict": karmic_verdict,
        "flags": flags[:6],
    }


# ── main ─────────────────────────────────────────────────────────
def compute_progeny_bundle(kundli: Dict[str, Any], dob: str,
                            driver: int, conductor: int) -> Dict[str, Any]:
    """T13 Progeny bundle. Hard data gate; never fabricates."""
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"
        return out
    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []
    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing or unknown ({asc!r})"
        return out
    if not isinstance(planets, list) or len(planets) < 9:
        out["reason"] = f"planets list incomplete (n={len(planets) if isinstance(planets, list) else 0})"
        return out
    required = {"Sun", "Moon", "Jupiter", "Mars", "Venus", "Mercury", "Saturn", "Rahu", "Ketu"}
    pn = {p.get("name") for p in planets if isinstance(p, dict)}
    missing = required - pn
    if missing:
        out["reason"] = f"missing required grahas: {sorted(missing)}"
        return out

    asc_idx = SIGNS.index(asc)
    p_house = _planet_house(planets, asc)

    # ── 1. Putra Bhava (5th house + lord) ──────────────────────
    fifth_sign = SIGNS[(asc_idx + 4) % 12]
    fifth_lord = SIGN_LORD[fifth_sign]
    fl_house = p_house.get(fifth_lord, 0)
    fl_sign = _planet_sign(planets, fifth_lord) or "—"
    fl_dignity = _dignity(fifth_lord, fl_sign)
    fifth_occupants = _occupants(planets, asc, 5)

    # 5th-lord strength score (0-100)
    fl_strength = 50
    if fl_house in KENDRA | TRIKONA:
        fl_strength += 20
    elif fl_house in DUSTHANA:
        fl_strength -= 25
    if fl_dignity == "exalted":
        fl_strength += 25
    elif fl_dignity == "own-sign":
        fl_strength += 15
    elif fl_dignity == "debilitated":
        fl_strength -= 25
    fl_strength = max(0, min(100, fl_strength))

    if fl_strength >= 70:
        fl_verdict = "STRONG progeny-foundation — Putra karma well-supported"
    elif fl_strength >= 40:
        fl_verdict = "MODERATE progeny-foundation — workable with conscious remedies"
    else:
        fl_verdict = "FRAGILE progeny-foundation — sustained Putra-remedies + medical support advised"

    putra_bhava = {
        "fifth_sign": fifth_sign,
        "fifth_lord": fifth_lord,
        "lord_house": fl_house,
        "lord_sign": fl_sign,
        "lord_dignity": fl_dignity,
        "occupants": fifth_occupants,
        "strength_score": fl_strength,
        "verdict": fl_verdict,
        "child_temperament": FIFTH_SIGN_CHILD.get(fifth_sign, "—"),
        "education_indication": FIFTH_SIGN_EDUCATION.get(fifth_sign, "—"),
    }

    # ── 2. Putra Karaka (Jupiter primary; 5L secondary) ────────
    jup_sign = _planet_sign(planets, "Jupiter") or "—"
    jup_house = p_house.get("Jupiter", 0)
    jup_dignity = _dignity("Jupiter", jup_sign)
    jup_strong = (jup_house in KENDRA | TRIKONA) and jup_dignity != "debilitated"

    putra_karaka = {
        "primary_karaka": "Jupiter",
        "karaka_sign": jup_sign,
        "karaka_house": jup_house,
        "karaka_dignity": jup_dignity,
        "karaka_well_placed": jup_strong,
        "secondary_karaka": fifth_lord,
        "secondary_sign": fl_sign,
        "secondary_house": fl_house,
        "secondary_dignity": fl_dignity,
        "note": ("Jupiter is the universal Putra-karaka (Putrakaraka). "
                 "The 5L is the secondary signator — together they describe "
                 "the WILL and PATH of progeny in this lifetime."),
    }

    # ── 3. D7 Saptamsa Picture ─────────────────────────────────
    d7 = _d7_data(kundli)
    d7_asc = d7.get("ascendant")
    d7_plist = d7.get("planets", []) or []
    d7_fifth_sign = None
    d7_fifth_lord = "—"
    d7_fifth_occ: List[str] = []
    if d7_asc in SIGNS:
        d7_fifth_sign = SIGNS[(SIGNS.index(d7_asc) + 4) % 12]
        d7_fifth_lord = SIGN_LORD.get(d7_fifth_sign, "—")
        if d7_plist:
            for p in d7_plist:
                if isinstance(p, dict) and p.get("sign") == d7_fifth_sign:
                    d7_fifth_occ.append(p.get("name", ""))
            d7_fifth_occ = sorted([x for x in d7_fifth_occ if x])

    jup_d7_sign = _planet_sign_in_chart(d7_plist, "Jupiter") if d7_plist else None

    d7_picture = {
        "d7_ascendant": d7_asc or "—",
        "d7_fifth_sign": d7_fifth_sign or "—",
        "d7_fifth_lord": d7_fifth_lord,
        "d7_fifth_occupants": d7_fifth_occ,
        "jupiter_d7_sign": jup_d7_sign or "—",
        "available": bool(d7_asc and d7_plist),
        "note": ("D7 Saptamsa is the classical progeny chart. The D7 Lagna shows "
                 "first-child essence; D7-5th shows progeny-strength; Jupiter's "
                 "D7 sign refines the Putrakaraka reading."),
    }

    # ── 4. Putra Yogas Audit ───────────────────────────────────
    yogas_audit = _putra_yogas_audit(planets, asc, fifth_lord)

    # ── 5. Children Timing Window ──────────────────────────────
    timing = _children_timing(kundli, planets, asc, fifth_lord)

    # ── 6. Karmic / Shapa Signatures ───────────────────────────
    karmic = _shapa_signatures(planets, asc, fifth_lord)

    # ── 7. Synthesis ───────────────────────────────────────────
    if karmic["karmic_verdict"] == "STRONG-SHAPA":
        verdict_token = SYNTHESIS_TOKENS["shapa"]
    elif yogas_audit["severity"] == "BLESSED" and karmic["karmic_verdict"] == "LIGHT-KARMIC":
        verdict_token = SYNTHESIS_TOKENS["blessed"]
    elif "Saturn" in fifth_occupants or yogas_audit["severity"] in ("MODERATE", "CHALLENGED"):
        verdict_token = SYNTHESIS_TOKENS["delayed"]
    else:
        verdict_token = SYNTHESIS_TOKENS["karmic"]

    summary_lines = [
        f"5th house {fifth_sign} (lord {fifth_lord} in H{fl_house}, {fl_dignity}) — "
        f"strength {fl_strength}/100.",
        f"Putrakaraka Jupiter in {jup_sign} H{jup_house} ({jup_dignity}); "
        f"secondary 5L {fifth_lord} in {fl_sign} H{fl_house}.",
        f"D7 Saptamsa: Lagna {d7_picture['d7_ascendant']}, 5th = "
        f"{d7_picture['d7_fifth_sign']} (lord {d7_picture['d7_fifth_lord']}).",
        f"Putra Yogas: {yogas_audit['yoga_count']} active, "
        f"{yogas_audit['obstruction_count']} obstructions — {yogas_audit['severity']} "
        f"({yogas_audit['score']}/100).",
        f"Karmic load: {karmic['karmic_verdict']} (score {karmic['karmic_score']}/100).",
        f"Current dasha: {timing['current_md']} → {timing['current_ad']} — "
        f"{timing['window_status']}.",
    ]

    child_profile_lines = [
        f"Temperament from 5th sign ({fifth_sign}): {FIFTH_SIGN_CHILD.get(fifth_sign, '—')}",
        f"Education path indication ({fifth_sign}): {FIFTH_SIGN_EDUCATION.get(fifth_sign, '—')}",
    ]
    if d7_picture["available"]:
        child_profile_lines.append(
            f"Refinement via D7 Lagna ({d7_picture['d7_ascendant']}): the first-child essence "
            f"resonates with the qualities of {d7_picture['d7_ascendant']} — this is the soul-"
            f"signature of the progeny relationship in this lifetime."
        )

    action_plan: List[str] = []
    if jup_dignity == "debilitated" or jup_house in DUSTHANA:
        action_plan.append("Strengthen Jupiter (Putrakaraka): Thursday fasts, Brihaspati mantra "
                            "(108x daily), wear yellow on Thursdays, donate yellow gram + turmeric.")
    if karmic["rahu_in_5th"] or any("Sarpa" in f or "Naga" in f for f in karmic["flags"]):
        action_plan.append("Sarpa/Naga shapa cleansing: Subrahmanya / Karthikeya temple visits, "
                            "Sarpa-Suktam, Nag-panchami observance, install Naga-pratishtha.")
    if any("Pitru" in f for f in karmic["flags"]):
        action_plan.append("Pitru shapa cleansing: annual Pitru-paksha tarpana, Tila-tarpana on "
                            "every Amavasya, donate cooked food to needy in ancestors' name.")
    if karmic["saturn_in_5th"]:
        action_plan.append("Saturn in 5th: accept progeny will arrive after 28-32; Shani-shanti "
                            "(Saturday fasts, sesame oil donation), do NOT rush conception.")
    if yogas_audit["score"] >= 60:
        action_plan.append("Strong Putra-yogas active: focus on Santana-Gopala mantra (108x daily) "
                            "during conception window; Krishna-Gopala worship.")
    action_plan.append(f"Best dasha-window planets to watch for progeny-event: "
                        f"{', '.join(timing['activators'])}.")
    action_plan.append(f"Education direction (per 5th sign {fifth_sign}): "
                        f"{FIFTH_SIGN_EDUCATION.get(fifth_sign, '—')}")

    synthesis = {
        "verdict_token": verdict_token,
        "summary_lines": summary_lines,
        "child_profile_lines": child_profile_lines,
        "action_plan": action_plan[:6],
    }

    out["available"] = True
    out["putra_bhava"] = putra_bhava
    out["putra_karaka"] = putra_karaka
    out["d7_picture"] = d7_picture
    out["yogas_audit"] = yogas_audit
    out["timing"] = timing
    out["karmic"] = karmic
    out["synthesis"] = synthesis
    return out
