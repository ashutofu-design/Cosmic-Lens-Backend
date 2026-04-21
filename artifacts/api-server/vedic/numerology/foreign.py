"""Tier 15 — Foreign Travel, Settlement & 12th House (Vyaya Bhava) Deep Audit.

Vyaya Bhava (12th house) governs foreign lands, long-distance travel,
settlement abroad, expenses, isolation, and moksha. This engine produces 7
chart-locked blocks: Vyaya Bhava strength, foreign karakas (Rahu primary,
Moon for water travel, Saturn for long-distance / industrial settlement,
Jupiter for higher-study abroad, Ketu for spiritual pilgrimage), classical
foreign-travel yogas + obstructions, settlement-vs-visit distinction
(8th + 12th + Rahu signature), travel-timing window from current dasha,
Vyaya-leak signatures (expense-drain, isolation, hospitalization risks),
and synthesis with travel-profile + country-direction + action plan.

Hard data gate: ascendant + 9 grahas. Dasha and D9 are soft-gated.
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

# 12th-sign foreign-travel character (BPHS / Phaladeepika lineage)
TWELFTH_SIGN_FOREIGN: Dict[str, str] = {
    "Aries": "fast-paced foreign trips, military/defence postings, short-burst travel; risk of hot-headed disputes abroad.",
    "Taurus": "luxury foreign settlement (Europe, Gulf), beauty/fashion industries abroad; comfort-driven NRI life.",
    "Gemini": "USA, UK, Singapore — IT/communication/media work abroad; multiple short trips, dual-country lifestyle.",
    "Cancer": "water-route migration (UK, USA via sea), emotional pull to homeland; family-led NRI move.",
    "Leo": "prestigious foreign postings, government/diplomatic abroad service, royal-style hospitality industry.",
    "Virgo": "medical/technical/service-industry abroad (USA, Germany), detail-oriented work; mid-tier salary roles.",
    "Libra": "partnership-led foreign move (spouse-visa, joint-venture abroad), arts/design/luxury industries.",
    "Scorpio": "transformative foreign chapter (research, surgery, intelligence abroad); secretive about NRI life.",
    "Sagittarius": "higher-education abroad (USA, UK, Australia), philosophy/teaching/legal work overseas, foreign-Guru.",
    "Capricorn": "long-distance/cold-country settlement (Canada, Russia, North-Europe), corporate/govt jobs abroad.",
    "Aquarius": "tech/innovation hubs (USA, Germany, Japan), unconventional foreign paths, social-cause NGO abroad.",
    "Pisces": "spiritual abroad-stay (ashram, meditation centres, charity), water-near foreign cities, foreign-divine.",
}

# Country/region direction by Rahu sign (foreign-karaka)
RAHU_SIGN_COUNTRY: Dict[str, str] = {
    "Aries": "Australia, New Zealand, defence-industry countries; warrior-cultures.",
    "Taurus": "Switzerland, Italy, France, Gulf — luxury/banking/agriculture nations.",
    "Gemini": "USA, UK, Singapore — IT, media, communication economies.",
    "Cancer": "UK, Ireland, water-near nations; family-sponsored migration paths.",
    "Leo": "France, Italy, USA East-coast — leadership, hospitality, govt service.",
    "Virgo": "Germany, Switzerland, USA — medical, engineering, service economies.",
    "Libra": "France, Italy, Japan — design, arts, partnership industries.",
    "Scorpio": "Russia, Eastern Europe, intelligence/research-driven nations.",
    "Sagittarius": "USA, UK, Australia — higher-education, legal, philosophical centres.",
    "Capricorn": "Canada, Northern Europe, Russia — cold-climate, govt/structural careers.",
    "Aquarius": "USA (Silicon Valley), Germany, Japan — tech/innovation hubs.",
    "Pisces": "spiritual centres (Bali, Thailand, USA West-coast), water-near, charity-zones.",
}

SYNTHESIS_TOKENS = {
    "blessed": "BLESSED-FOREIGN-PATH",
    "delayed": "DELAYED-FOREIGN-FORTUNE",
    "karmic": "KARMIC-EXPENSE-PATH",
    "moksha": "SPIRITUAL-MOKSHA-FOCUSED",
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


# ── Foreign Yogas Audit ─────────────────────────────────────────
def _foreign_yogas_audit(planets: List[Dict], asc_sign: str,
                          twelfth_lord: str) -> Dict[str, Any]:
    p_house = _planet_house(planets, asc_sign)
    asc_idx = SIGNS.index(asc_sign)
    ninth_lord = SIGN_LORD[SIGNS[(asc_idx + 8) % 12]]
    fourth_lord = SIGN_LORD[SIGNS[(asc_idx + 3) % 12]]

    twelfth_occ = _occupants(planets, asc_sign, 12)
    ninth_occ = _occupants(planets, asc_sign, 9)
    tl_house = p_house.get(twelfth_lord, 0)
    rahu_house = p_house.get("Rahu", 0)
    moon_house = p_house.get("Moon", 0)
    sat_house = p_house.get("Saturn", 0)

    yogas: List[str] = []

    # 1. 12L + 9L combo (foreign-fortune yoga)
    if twelfth_lord == ninth_lord or p_house.get(twelfth_lord) == p_house.get(ninth_lord):
        yogas.append(f"12L–9L Vyaya-Bhagya yoga (12L & 9L = {twelfth_lord}/{ninth_lord}) — "
                     f"classical foreign-fortune combination per BPHS.")

    # 2. Rahu in 12th (foreign-karaka in foreign-house)
    if rahu_house == 12:
        yogas.append("Rahu in 12th — foreign-karaka in Vyaya Bhava; classical NRI/foreign-"
                     "settlement yoga; long stays abroad indicated.")

    # 3. Rahu in 9th (foreign-fortune)
    if rahu_house == 9:
        yogas.append("Rahu in 9th — foreign-karaka in Bhagya Bhava; foreign higher-education "
                     "or foreign-religion path; fortune through alien lands.")

    # 4. 12L in Kendra/Trikona (well-placed lord = positive foreign exposure)
    if tl_house in (KENDRA | TRIKONA):
        yogas.append(f"12L {twelfth_lord} in H{tl_house} (Kendra/Trikona) — foreign chapter "
                     f"works in your favour; expenses convert into long-term gains.")

    # 5. 12L in 9th OR 9L in 12th (mutual exchange / strong foreign yoga)
    if tl_house == 9:
        yogas.append(f"12L {twelfth_lord} in 9th — direct foreign-Bhagya yoga; abroad-luck "
                     f"strongly active; foreign mentor / foreign-spiritual pull.")
    if p_house.get(ninth_lord) == 12:
        yogas.append(f"9L {ninth_lord} in 12th — Bhagya in Vyaya; fortune unfolds abroad; "
                     f"foreign-soil prosperity.")

    # 6. Moon in 9th or 12th (water-travel / foreign-Mata-yoga)
    if moon_house in (9, 12):
        yogas.append(f"Moon in {moon_house}th — Chandra-foreign yoga; emotional-attachment "
                     f"to foreign lands; water-route travel possible (sea/ship-mode roots).")

    # 7. Jupiter aspects 12th (Guru-drishti = blessed exits)
    if _has_aspect(planets, asc_sign, "Jupiter", 12):
        yogas.append("Jupiter aspects the 12th — Guru-drishti on Vyaya; foreign chapter "
                     "becomes dharmic, education-focused or spiritually evolutionary.")

    obstructions: List[str] = []

    if "Saturn" in twelfth_occ:
        obstructions.append("Saturn in 12th — DELAYED foreign-fortune; long-isolation periods "
                            "abroad; cold/heavy NRI life; needs Shani-shanti before move.")
    if "Sun" in twelfth_occ:
        obstructions.append("Sun in 12th — ego-isolation abroad, govt-related delays, father-"
                            "distance during foreign chapter; Surya namaskar daily helps.")
    if "Ketu" in twelfth_occ and rahu_house != 12:
        obstructions.append("Ketu in 12th — moksha-pull dominates over material foreign-gain; "
                            "spiritual ashram-life more likely than corporate NRI path.")
    if "Mars" in twelfth_occ:
        obstructions.append("Mars in 12th — conflict/disputes abroad, surgical-event risk, "
                            "expense on legal matters; Mangal-shanti before travel.")
    if tl_house in DUSTHANA and tl_house != 12:
        obstructions.append(f"12L {twelfth_lord} in H{tl_house} (Dusthana) — foreign-fortune "
                            f"karma needs purification; expense-leakage risk.")
    # Rahu/Ketu nodal axis on 12-6: Rahu+Ketu are always 180° apart (7 houses),
    # so the true 12-6 axis = (Rahu in 12 AND Ketu in 6) OR (Ketu in 12 AND Rahu in 6).
    ketu_house = p_house.get("Ketu", 0)
    if (rahu_house == 12 and ketu_house == 6) or (ketu_house == 12 and rahu_house == 6):
        obstructions.append("Rahu+Ketu axis through 12th–6th — karmic foreign chapter with "
                            "health/legal complications; not a clean NRI yoga without remedies.")
    moon_dignity = _dignity("Moon", _planet_sign(planets, "Moon"))
    if moon_dignity == "debilitated" and moon_house in (8, 12):
        obstructions.append(f"Debilitated Moon in H{moon_house} — emotional-isolation abroad, "
                            f"homesickness severe; do Sri Suktam before relocation.")

    yoga_count = len(yogas)
    obs_count = len(obstructions)
    score = max(0, min(100, 50 + (yoga_count * 12) - (obs_count * 10)))

    if score >= 70 and obs_count <= 1:
        severity = "BLESSED"
        verdict = ("Multiple foreign-yogas active with minimal obstruction — natural NRI / "
                   "long-foreign-stay path with classical fortune.")
    elif score >= 50:
        severity = "MODERATE"
        verdict = ("Mixed signals — yogas present but some obstructions; correct timing + "
                   "Vyaya-shanti will produce results.")
    elif score >= 30:
        severity = "CHALLENGED"
        verdict = ("Obstructions outweigh yogas — foreign chapter may bring more expense than "
                   "gain without remedies; verify visa/legal clarity meticulously.")
    else:
        severity = "DENSE-KARMA"
        verdict = ("Heavy Vyaya-karma signature — short trips OK but long settlement abroad "
                   "needs deep karmic preparation (12-house remedies, Saturn/Rahu shanti).")

    return {
        "yogas": yogas[:7],
        "obstructions": obstructions[:7],
        "yoga_count": yoga_count,
        "obstruction_count": obs_count,
        "score": score,
        "severity": severity,
        "verdict": verdict,
        "twelfth_occupants": twelfth_occ,
        "ninth_occupants": ninth_occ,
        "twelfth_lord_house": tl_house,
        "rahu_house": rahu_house,
        "moon_house": moon_house,
    }


# ── Settlement vs Visit Distinction ─────────────────────────────
def _settlement_picture(planets: List[Dict], asc_sign: str,
                         twelfth_lord: str) -> Dict[str, Any]:
    p_house = _planet_house(planets, asc_sign)
    rahu_house = p_house.get("Rahu", 0)
    moon_house = p_house.get("Moon", 0)
    sat_house = p_house.get("Saturn", 0)
    tl_house = p_house.get(twelfth_lord, 0)
    eighth_occ = _occupants(planets, asc_sign, 8)
    twelfth_occ = _occupants(planets, asc_sign, 12)

    settlement_score = 0
    factors: List[str] = []

    if rahu_house == 12:
        settlement_score += 25
        factors.append("Rahu in 12th = strong settlement signature (long-stay).")
    if rahu_house in (4, 7):
        settlement_score += 15
        factors.append(f"Rahu in H{rahu_house} = home/partnership pulls toward foreign roots.")
    if tl_house in (1, 9, 12):
        settlement_score += 20
        factors.append(f"12L {twelfth_lord} in H{tl_house} = self-aligned foreign chapter.")
    if moon_house in (9, 12):
        settlement_score += 15
        factors.append(f"Moon in H{moon_house} = emotional-roots abroad.")
    if sat_house == 12:
        settlement_score += 10
        factors.append("Saturn in 12th = long, slow foreign chapter (settlement vs visit).")
    if "Saturn" in eighth_occ or "Rahu" in eighth_occ:
        settlement_score += 10
        factors.append("8th-house transformation karma → permanent identity-shift abroad.")

    settlement_score = max(0, min(100, settlement_score))

    if settlement_score >= 60:
        mode = "SETTLEMENT"
        narrative = ("Chart shows strong settlement signature — long-stay or permanent NRI "
                     "life is the primary foreign pattern in this lifetime.")
    elif settlement_score >= 35:
        mode = "EXTENDED-STAY"
        narrative = ("Chart shows extended-stay signature — multi-year foreign chapters but "
                     "with eventual return-to-roots energy; both NRI and homeland active.")
    elif settlement_score >= 15:
        mode = "FREQUENT-TRAVEL"
        narrative = ("Chart shows frequent-travel signature — multiple short-to-medium foreign "
                     "trips for work/study/family rather than permanent settlement.")
    else:
        mode = "OCCASIONAL-VISIT"
        narrative = ("Chart shows occasional-visit signature — foreign travel is light; "
                     "homeland karma dominates; spiritual/family pull keeps you rooted.")

    return {
        "settlement_score": settlement_score,
        "mode": mode,
        "narrative": narrative,
        "factors": factors[:6],
    }


# ── Travel Timing Window ────────────────────────────────────────
def _travel_timing(kundli: Dict, planets: List[Dict], asc_sign: str,
                    twelfth_lord: str) -> Dict[str, Any]:
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
    occ_12 = _occupants(planets, asc_sign, 12)

    activators = {twelfth_lord, "Rahu", "Moon", ninth_lord}
    for p in occ_12:
        activators.add(p)
    activators.discard("—")

    md_active = md_lord in activators if md_lord else False
    ad_active = ad_lord in activators if ad_lord else False

    if md_active and ad_active:
        window_status = "ACTIVE TRAVEL WINDOW"
        window_note = (f"Both MD ({md_lord}) and AD ({ad_lord}) are foreign/12th activators — "
                       f"this is a strongly supportive travel/settlement window per dasha logic.")
    elif md_active:
        window_status = "WARM TRAVEL WINDOW"
        window_note = (f"MD lord {md_lord} is a foreign-activator — primary travel pull alive; "
                       f"watch for AD/PD of Rahu/Moon/12L/9L to lock the relocation.")
    elif ad_active:
        window_status = "TACTICAL TRAVEL WINDOW"
        window_note = (f"AD lord {ad_lord} is a foreign-activator inside non-aligned MD "
                       f"({md_lord or 'unknown'}) — short opportunity window; act decisively.")
    else:
        window_status = "PREP WINDOW"
        window_note = (f"Neither MD ({md_lord or 'unknown'}) nor AD ({ad_lord or 'unknown'}) "
                       f"is a primary foreign-activator — use this period for visa-prep, "
                       f"language learning, savings; avoid major relocation pushes.")

    return {
        "current_md": md_lord or "—",
        "current_ad": ad_lord or "—",
        "activators": sorted(activators),
        "twelfth_lord": twelfth_lord,
        "ninth_lord": ninth_lord,
        "md_is_activator": md_active,
        "ad_is_activator": ad_active,
        "window_status": window_status,
        "window_note": window_note,
    }


# ── Vyaya Leak / Karmic Signatures ──────────────────────────────
def _vyaya_signatures(planets: List[Dict], asc_sign: str,
                       twelfth_lord: str) -> Dict[str, Any]:
    p_house = _planet_house(planets, asc_sign)
    twelfth_occ = _occupants(planets, asc_sign, 12)

    flags: List[str] = []

    if "Saturn" in twelfth_occ:
        flags.append("Vyaya-Shani signature — Saturn in 12th: prolonged isolation abroad, "
                     "expense-drain on legal/health, monastic/quiet living; do Shani-shanti.")
    if "Mars" in twelfth_occ:
        flags.append("Vyaya-Mangal signature — Mars in 12th: surgery / hospital-expense risk "
                     "abroad, legal disputes; Hanuman Chalisa daily for protection.")
    if "Rahu" in twelfth_occ:
        flags.append("Vyaya-Rahu signature — foreign chapter is karmically intense; visa/legal "
                     "hurdles possible but eventually yields long-term abroad-life.")
    if "Ketu" in twelfth_occ:
        flags.append("Vyaya-Ketu signature — moksha/spirituality dominates 12th-house karma; "
                     "ashram-life, charity, or research-isolation more rewarding than NRI.")
    if "Sun" in twelfth_occ:
        flags.append("Vyaya-Surya signature — ego-friction with foreign-systems, govt-job "
                     "delays abroad; Aditya Hridaya stotram every Sunday.")
    moon_dignity = _dignity("Moon", _planet_sign(planets, "Moon"))
    if moon_dignity == "debilitated":
        flags.append("Debilitated Moon — homesickness/emotional-instability during long "
                     "foreign chapters; recite Sri Suktam, drink water-charged-with-silver.")
    if p_house.get("Rahu") == p_house.get(twelfth_lord) and p_house.get("Rahu"):
        flags.append(f"Rahu conjunct 12L ({twelfth_lord}) — foreign chapter is karmically "
                     f"compulsive; cannot avoid long-stay abroad; double-check all paperwork.")

    score = (
        (15 if "Saturn" in twelfth_occ else 0)
        + (10 if "Mars" in twelfth_occ else 0)
        + (10 if "Rahu" in twelfth_occ else 0)
        + (10 if "Ketu" in twelfth_occ else 0)
        + (10 if moon_dignity == "debilitated" else 0)
        + (10 if p_house.get("Rahu") == p_house.get(twelfth_lord) and p_house.get("Rahu") else 0)
    )

    if score >= 30:
        karmic_verdict = "STRONG-VYAYA-KARMA"
    elif score >= 15:
        karmic_verdict = "MODERATE-KARMIC"
    else:
        karmic_verdict = "LIGHT-KARMIC"

    # moksha-axis: heavy 12th + Ketu + spiritual = moksha-focused
    moksha_focus = ("Ketu" in twelfth_occ
                    or _planet_sign(planets, "Ketu") in ("Pisces", "Sagittarius"))

    return {
        "twelfth_occupants": twelfth_occ,
        "saturn_in_12th": "Saturn" in twelfth_occ,
        "rahu_in_12th": "Rahu" in twelfth_occ,
        "ketu_in_12th": "Ketu" in twelfth_occ,
        "mars_in_12th": "Mars" in twelfth_occ,
        "moksha_focus": moksha_focus,
        "karmic_score": score,
        "karmic_verdict": karmic_verdict,
        "flags": flags[:7],
    }


# ── main ────────────────────────────────────────────────────────
def compute_foreign_bundle(kundli: Dict[str, Any], dob: str,
                            driver: int, conductor: int) -> Dict[str, Any]:
    """T15 Foreign/Vyaya bundle. Hard data gate; never fabricates."""
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

    # ── 1. Vyaya Bhava ─────────────────────────────────────────
    twelfth_sign = SIGNS[(asc_idx + 11) % 12]
    twelfth_lord = SIGN_LORD[twelfth_sign]
    tl_house = p_house.get(twelfth_lord, 0)
    tl_sign = _planet_sign(planets, twelfth_lord) or "—"
    tl_dignity = _dignity(twelfth_lord, tl_sign)
    twelfth_occupants = _occupants(planets, asc, 12)

    tl_strength = 50
    if tl_house in KENDRA | TRIKONA:
        tl_strength += 20
    elif tl_house in DUSTHANA:
        tl_strength -= 15  # 12L in 12th is mild positive (own house pull)
        if tl_house == 12:
            tl_strength += 25  # 12L in own 12th is GOOD for foreign
    if tl_dignity == "exalted":
        tl_strength += 25
    elif tl_dignity == "own-sign":
        tl_strength += 15
    elif tl_dignity == "debilitated":
        tl_strength -= 25
    tl_strength = max(0, min(100, tl_strength))

    if tl_strength >= 70:
        tl_verdict = "STRONG Vyaya-foundation — foreign chapter well-supported"
    elif tl_strength >= 40:
        tl_verdict = "MODERATE Vyaya-foundation — workable with visa-care + remedies"
    else:
        tl_verdict = "FRAGILE Vyaya-foundation — sustained remedies + careful timing essential"

    vyaya_bhava = {
        "twelfth_sign": twelfth_sign,
        "twelfth_lord": twelfth_lord,
        "lord_house": tl_house,
        "lord_sign": tl_sign,
        "lord_dignity": tl_dignity,
        "occupants": twelfth_occupants,
        "strength_score": tl_strength,
        "verdict": tl_verdict,
        "foreign_indication": TWELFTH_SIGN_FOREIGN.get(twelfth_sign, "—"),
    }

    # ── 2. Foreign Karakas ─────────────────────────────────────
    rahu_sign = _planet_sign(planets, "Rahu") or "—"
    rahu_house = p_house.get("Rahu", 0)
    moon_sign = _planet_sign(planets, "Moon") or "—"
    moon_house = p_house.get("Moon", 0)
    moon_dignity = _dignity("Moon", moon_sign)
    sat_sign = _planet_sign(planets, "Saturn") or "—"
    sat_house = p_house.get("Saturn", 0)
    jup_sign = _planet_sign(planets, "Jupiter") or "—"
    jup_house = p_house.get("Jupiter", 0)
    ketu_sign = _planet_sign(planets, "Ketu") or "—"
    ketu_house = p_house.get("Ketu", 0)

    karakas = {
        "foreign_karaka": "Rahu",
        "rahu_sign": rahu_sign,
        "rahu_house": rahu_house,
        "water_travel_karaka": "Moon",
        "moon_sign": moon_sign,
        "moon_house": moon_house,
        "moon_dignity": moon_dignity,
        "long_distance_karaka": "Saturn",
        "saturn_sign": sat_sign,
        "saturn_house": sat_house,
        "study_abroad_karaka": "Jupiter",
        "jupiter_sign": jup_sign,
        "jupiter_house": jup_house,
        "spiritual_travel_karaka": "Ketu",
        "ketu_sign": ketu_sign,
        "ketu_house": ketu_house,
        "country_indication": RAHU_SIGN_COUNTRY.get(rahu_sign, "—"),
        "note": ("Rahu = primary foreign-karaka (NRI life), Moon = water-travel & emotional-"
                 "roots abroad, Saturn = long-distance / cold-country settlement, Jupiter = "
                 "higher-study abroad / foreign-Guru, Ketu = spiritual pilgrimage / ashram-life."),
    }

    # ── 3. Foreign Yogas Audit ─────────────────────────────────
    yogas_audit = _foreign_yogas_audit(planets, asc, twelfth_lord)

    # ── 4. Settlement vs Visit ─────────────────────────────────
    settlement = _settlement_picture(planets, asc, twelfth_lord)

    # ── 5. Travel Timing ───────────────────────────────────────
    timing = _travel_timing(kundli, planets, asc, twelfth_lord)

    # ── 6. Vyaya/Karmic Signatures ─────────────────────────────
    karmic = _vyaya_signatures(planets, asc, twelfth_lord)

    # ── 7. Synthesis ───────────────────────────────────────────
    if karmic["moksha_focus"] and karmic["karmic_verdict"] != "LIGHT-KARMIC" \
            and yogas_audit["severity"] not in ("BLESSED",):
        verdict_token = SYNTHESIS_TOKENS["moksha"]
    elif yogas_audit["severity"] == "BLESSED" and karmic["karmic_verdict"] == "LIGHT-KARMIC":
        verdict_token = SYNTHESIS_TOKENS["blessed"]
    elif karmic["karmic_verdict"] == "STRONG-VYAYA-KARMA" \
            or yogas_audit["severity"] in ("CHALLENGED", "DENSE-KARMA"):
        verdict_token = SYNTHESIS_TOKENS["karmic"]
    else:
        verdict_token = SYNTHESIS_TOKENS["delayed"]

    summary_lines = [
        f"12th house {twelfth_sign} (lord {twelfth_lord} in H{tl_house}, {tl_dignity}) — "
        f"strength {tl_strength}/100.",
        f"Foreign karaka Rahu in {rahu_sign} H{rahu_house}; Moon in {moon_sign} H{moon_house} "
        f"({moon_dignity}); Saturn in {sat_sign} H{sat_house}.",
        f"Foreign Yogas: {yogas_audit['yoga_count']} active, "
        f"{yogas_audit['obstruction_count']} obstructions — {yogas_audit['severity']} "
        f"({yogas_audit['score']}/100).",
        f"Settlement mode: {settlement['mode']} (score {settlement['settlement_score']}/100).",
        f"Karmic load: {karmic['karmic_verdict']} (score {karmic['karmic_score']}/100); "
        f"moksha-focus = {karmic['moksha_focus']}.",
        f"Current dasha: {timing['current_md']} → {timing['current_ad']} — "
        f"{timing['window_status']}.",
    ]

    profile_lines = [
        f"Foreign profile from 12th sign ({twelfth_sign}): "
        f"{TWELFTH_SIGN_FOREIGN.get(twelfth_sign, '—')}",
        f"Country/region indication from Rahu in {rahu_sign}: "
        f"{RAHU_SIGN_COUNTRY.get(rahu_sign, '—')}",
        settlement["narrative"],
    ]

    action_plan: List[str] = []
    if karmic["karmic_verdict"] == "STRONG-VYAYA-KARMA":
        action_plan.append("Vyaya-shanti before any major foreign move: 12th-house remedies "
                            "(donate to monastery, feed stray animals, support pilgrimage trusts).")
    if karmic["saturn_in_12th"]:
        action_plan.append("Saturn in 12th: Shani-shanti (Saturday fasts, sesame oil donation, "
                            "iron-pot meals to needy); avoid major settlement before age 30.")
    if karmic["rahu_in_12th"]:
        action_plan.append("Rahu in 12th: triple-verify visa/legal paperwork; avoid shortcuts; "
                            "Rahu-mantra (Om Rahave Namaha 108x Saturdays).")
    if karmic["mars_in_12th"]:
        action_plan.append("Mars in 12th: avoid risky physical activity abroad; carry health "
                            "insurance with surgical cover; Mangal-shanti before relocation.")
    if karmic["moksha_focus"]:
        action_plan.append("Moksha-focus active: balance material foreign-career with regular "
                            "spiritual practice; consider sabbatical-ashram visits.")
    action_plan.append(f"Best dasha-window planets to watch for travel/settlement: "
                        f"{', '.join(timing['activators'])}.")
    action_plan.append(f"Country direction (per Rahu in {rahu_sign}): "
                        f"{RAHU_SIGN_COUNTRY.get(rahu_sign, '—')}")

    synthesis = {
        "verdict_token": verdict_token,
        "summary_lines": summary_lines,
        "profile_lines": profile_lines,
        "action_plan": action_plan[:6],
    }

    out["available"] = True
    out["vyaya_bhava"] = vyaya_bhava
    out["karakas"] = karakas
    out["yogas_audit"] = yogas_audit
    out["settlement"] = settlement
    out["timing"] = timing
    out["karmic"] = karmic
    out["synthesis"] = synthesis
    return out
