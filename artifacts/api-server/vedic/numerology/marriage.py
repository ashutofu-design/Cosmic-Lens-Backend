"""Tier 12 — Marriage & Spouse Deep Audit engine.

Chart-based marriage prognosis (distinct from Tier 5 partner-DNA pre-screen):
Saptamesha (7th house + lord), Spouse Karaka (Venus / Jupiter), D9 spouse
picture (7th of D9 + Darakaraka — Jaimini lowest-deg karaka), Mangal Dosha
full audit with classical cancellations, current dasha marriage-timing
window, karmic marriage signatures (Rahu/Ketu/Saturn in 7th), and a
synthesis with spouse profile + actionable timing.

Hard data gate (asc + 9 grahas + dasha + D9). Refuses on missing data.
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

# Mars in these houses from Lagna OR Moon → Mangal Dosha
MANGAL_HOUSES = {1, 2, 4, 7, 8, 12}  # 2nd is included in some traditions

# Spouse profile by 7th-house sign (classical Phaladeepika / Brihat Parashara
# Hora Shastra lineage — temperament / appearance hints)
SEVENTH_SIGN_SPOUSE: Dict[str, str] = {
    "Aries": "energetic, independent, athletic build, fiery temperament; pioneer-type spouse who acts fast and dislikes being controlled.",
    "Taurus": "stable, sensual, beauty-loving, full-bodied; values comfort, loyalty, financial security; slow to anger but stubborn.",
    "Gemini": "communicative, witty, youthful-looking, restless; intellectually curious spouse who needs mental stimulation.",
    "Cancer": "emotional, nurturing, family-oriented, fair-skinned; deeply attached, moody, home-loving; mother-figure energy.",
    "Leo": "proud, dignified, charismatic, leader-type; expects respect, generous, dramatic; royal bearing and warm heart.",
    "Virgo": "analytical, service-minded, slim, detail-oriented; perfectionist, health-conscious, may delay marriage seeking the 'right' fit.",
    "Libra": "charming, diplomatic, beautiful, partnership-oriented; harmony-seeking spouse who values balance and aesthetics.",
    "Scorpio": "intense, magnetic, secretive, deeply emotional; powerful sexual chemistry; possessive but transformative bond.",
    "Sagittarius": "philosophical, optimistic, freedom-loving, well-travelled or learned; tall stature; teacher / guru energy.",
    "Capricorn": "mature, disciplined, ambitious, status-conscious; older or older-acting spouse; reserved but commitment-strong.",
    "Aquarius": "unconventional, intellectual, friend-first, humanitarian; unusual circumstances of meeting; needs space.",
    "Pisces": "compassionate, artistic, dreamy, intuitive; spiritual-emotional spouse; soft features; karmic-soul-mate type.",
}

# Verdict tokens locked for synthesis validator
SYNTHESIS_TOKENS = {
    "harmonious": "HARMONIOUS-MARRIAGE-PATH",
    "karmic": "KARMIC-MARRIAGE-PATH",
    "delayed": "DELAYED-DHARMIC-MARRIAGE",
    "transformative": "TRANSFORMATIVE-PARTNERSHIP-PATH",
}


# ── helpers ──────────────────────────────────────────────────────
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


def _compute_darakaraka(planets: List[Dict]) -> Optional[str]:
    """DK = LOWEST degrees-in-sign among 7 chara karakas (Sun..Saturn).
    Spouse-significator in Jaimini system."""
    candidates: List[Tuple[str, float]] = []
    for nm in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        lon = _planet_lon(planets, nm)
        if lon is None:
            return None
        candidates.append((nm, lon % 30.0))
    candidates.sort(key=lambda x: x[1])  # ascending — lowest = DK
    return candidates[0][0]


def _d9_seventh_sign(kundli: Dict, asc_d9: Optional[str]) -> Optional[str]:
    if asc_d9 not in SIGNS:
        return None
    return SIGNS[(SIGNS.index(asc_d9) + 6) % 12]


def _d9_data(kundli: Dict) -> Dict[str, Any]:
    d9 = (kundli.get("divisionalCharts") or {}).get("D9") \
        or (kundli.get("divisionalCharts") or {}).get("d9") or {}
    if not isinstance(d9, dict):
        return {}
    asc_d9 = d9.get("ascendant") or d9.get("Ascendant")
    plist = []
    for k in ("planets", "Planets"):
        if isinstance(d9.get(k), list):
            plist = d9[k]
            break
    return {"ascendant": asc_d9, "planets": plist}


def _planet_sign_in_chart(plist: List[Dict], name: str) -> Optional[str]:
    for p in plist:
        if isinstance(p, dict) and p.get("name") == name:
            s = p.get("sign")
            if s in SIGNS:
                return s
    return None


# ── Mangal Dosha audit ───────────────────────────────────────────
def _mangal_audit(planets: List[Dict], asc_sign: str) -> Dict[str, Any]:
    mars = _planet(planets, "Mars")
    moon = _planet(planets, "Moon")
    if not mars:
        return {"present": False, "reason": "no Mars data"}

    p_house = _planet_house(planets, asc_sign)
    mars_house_lagna = p_house.get("Mars", 0)
    mars_sign = _planet_sign(planets, "Mars") or "—"

    # Mars house from Moon
    mars_house_moon = 0
    if moon:
        moon_sign = _planet_sign(planets, "Moon")
        if moon_sign:
            mars_house_moon = ((SIGNS.index(mars_sign) - SIGNS.index(moon_sign)) % 12) + 1

    # Mars house from Venus (sometimes used too)
    venus_sign = _planet_sign(planets, "Venus")
    mars_house_venus = 0
    if venus_sign:
        mars_house_venus = ((SIGNS.index(mars_sign) - SIGNS.index(venus_sign)) % 12) + 1

    triggers: List[str] = []
    if mars_house_lagna in MANGAL_HOUSES:
        triggers.append(f"Mars in H{mars_house_lagna} from Lagna")
    if mars_house_moon in MANGAL_HOUSES:
        triggers.append(f"Mars in H{mars_house_moon} from Moon")
    if mars_house_venus in MANGAL_HOUSES:
        triggers.append(f"Mars in H{mars_house_venus} from Venus")

    present = bool(triggers)

    # Severity: based on house weight
    weight_house = {1: 3, 7: 4, 8: 4, 12: 3, 2: 2, 4: 2}
    sev_score = 0
    for h in (mars_house_lagna, mars_house_moon, mars_house_venus):
        sev_score += weight_house.get(h, 0)
    if sev_score >= 8:
        severity = "SEVERE"
    elif sev_score >= 4:
        severity = "MODERATE"
    elif sev_score >= 1:
        severity = "MILD"
    else:
        severity = "NONE"

    # Cancellations (classical)
    cancellations: List[str] = []
    mars_dignity = _dignity("Mars", mars_sign)
    if mars_dignity in ("own-sign", "exalted"):
        cancellations.append(f"Mars in {mars_sign} ({mars_dignity}) — auto-cancellation")
    # Jupiter aspect on Mars (5/7/9 from Jupiter) — approximate via house
    jup_house = p_house.get("Jupiter", 0)
    mars_h_lagna = mars_house_lagna
    if jup_house and mars_h_lagna:
        diff = ((mars_h_lagna - jup_house) % 12)
        if diff in (4, 6, 8):  # Jup's 5th/7th/9th aspects (1-indexed: +4,+6,+8)
            cancellations.append("Jupiter aspects Mars — graha-shanti cancellation")
    # Saturn in 7th = often cited cancellation
    if p_house.get("Saturn") == 7:
        cancellations.append("Saturn in 7th house — Saturn-Mars mutual neutralisation")
    # Mars in 12th in own sign
    if mars_house_lagna == 12 and mars_dignity == "own-sign":
        cancellations.append("Mars in 12th in own sign — dosha is dormant")

    if cancellations:
        if severity == "SEVERE":
            severity = "MODERATE"  # downgrade one tier
        elif severity == "MODERATE":
            severity = "MILD"
        elif severity == "MILD":
            severity = "NEUTRALISED"

    # Verdict
    if not present:
        verdict = "NO MANGAL DOSHA — no Mars-marriage friction signature"
    elif severity == "NEUTRALISED":
        verdict = "MANGAL DOSHA NEUTRALISED — classical cancellation applies; standard partnership"
    elif severity == "MILD":
        verdict = "MILD MANGAL DOSHA — minor friction; partner with Mars-balance preferred"
    elif severity == "MODERATE":
        verdict = "MODERATE MANGAL DOSHA — match with Mangal-balance partner OR perform remedies before marriage"
    else:
        verdict = "SEVERE MANGAL DOSHA — strong recommendation: match with another Mangal partner OR full Kuja-shanti remedies"

    return {
        "present": present,
        "mars_sign": mars_sign,
        "mars_dignity": mars_dignity,
        "mars_house_lagna": mars_house_lagna,
        "mars_house_moon": mars_house_moon,
        "mars_house_venus": mars_house_venus,
        "triggers": triggers,
        "severity": severity,
        "cancellations": cancellations,
        "verdict": verdict,
    }


# ── Marriage Timing Window ───────────────────────────────────────
def _marriage_timing(kundli: Dict, planets: List[Dict], asc_sign: str,
                      seventh_lord: str, spouse_karaka: str,
                      darakaraka: Optional[str]) -> Dict[str, Any]:
    dasha = kundli.get("dasha") or kundli.get("currentDasha") or {}
    md_lord = (dasha.get("mahaDasha") or dasha.get("md") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    ad_lord = (dasha.get("antarDasha") or dasha.get("ad") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    if not md_lord:
        # Try alternative shape
        md_lord = dasha.get("mahadasha_lord") if isinstance(dasha, dict) else None
        ad_lord = dasha.get("antardasha_lord") if isinstance(dasha, dict) else None

    p_house = _planet_house(planets, asc_sign)
    occ_7th = _occupants(planets, asc_sign, 7)

    # Marriage activator planets
    activators = set()
    activators.add(seventh_lord)
    activators.add(spouse_karaka)
    if darakaraka:
        activators.add(darakaraka)
    for p in occ_7th:
        activators.add(p)
    # 2nd lord (family-formation) and 11th lord (gain-of-spouse)
    asc_idx = SIGNS.index(asc_sign)
    second_lord = SIGN_LORD.get(SIGNS[(asc_idx + 1) % 12], "—")
    eleventh_lord = SIGN_LORD.get(SIGNS[(asc_idx + 10) % 12], "—")
    activators.add(second_lord)
    activators.add(eleventh_lord)
    activators.discard("—")

    md_active = md_lord in activators if md_lord else False
    ad_active = ad_lord in activators if ad_lord else False

    if md_active and ad_active:
        window_status = "HOT WINDOW NOW"
        window_note = (f"Both MD ({md_lord}) and AD ({ad_lord}) are marriage-activators "
                       f"— this is an active marriage-formation window.")
    elif md_active:
        window_status = "WARM WINDOW"
        window_note = (f"MD lord {md_lord} is a marriage-activator — primary timing pull "
                       f"is alive; wait for a supportive AD or PD for the actual event.")
    elif ad_active:
        window_status = "TACTICAL WINDOW"
        window_note = (f"AD lord {ad_lord} is a marriage-activator inside non-aligned MD "
                       f"({md_lord or 'unknown'}) — short, sharp opportunity window.")
    else:
        window_status = "PREP WINDOW"
        window_note = (f"Neither MD ({md_lord or 'unknown'}) nor AD ({ad_lord or 'unknown'}) "
                       f"is a primary marriage-activator — use this period for self-work and partner-clarity.")

    return {
        "current_md": md_lord or "—",
        "current_ad": ad_lord or "—",
        "activators": sorted(activators),
        "second_lord": second_lord,
        "eleventh_lord": eleventh_lord,
        "md_is_activator": md_active,
        "ad_is_activator": ad_active,
        "window_status": window_status,
        "window_note": window_note,
    }


# ── Karmic signatures ────────────────────────────────────────────
def _karmic_signatures(planets: List[Dict], asc_sign: str) -> Dict[str, Any]:
    p_house = _planet_house(planets, asc_sign)
    sevenths = _occupants(planets, asc_sign, 7)
    sixth_from_7 = _occupants(planets, asc_sign, 12)  # 6th from 7th = 12th of chart
    twelfth_from_7 = _occupants(planets, asc_sign, 6)  # 12th from 7th = 6th of chart

    flags: List[str] = []
    if "Rahu" in sevenths:
        flags.append("Rahu in 7th — unconventional / inter-cultural / karmic-magnetic spouse; "
                     "obsession-style attraction, learn detachment.")
    if "Ketu" in sevenths:
        flags.append("Ketu in 7th — past-life-completed marriage; risk of disinterest after "
                     "vows; spiritual-detached partner.")
    if "Saturn" in sevenths:
        flags.append("Saturn in 7th — DELAY signature (commit-readiness after age 28-32); "
                     "older / mature / responsible spouse; long-term loyalty.")
    if "Sun" in sevenths:
        flags.append("Sun in 7th — ego-clash risk; dominant spouse OR you-as-dominant; "
                     "needs respect-architecture.")
    if "Mars" in sevenths:
        flags.append("Mars in 7th — Mangal-driven friction; passionate but argumentative bond.")
    if twelfth_from_7:
        flags.append(f"12th-from-7th occupied by {', '.join(twelfth_from_7)} — "
                     f"loss-of-spouse-energy zone activated; consciously protect intimacy.")

    karmic_score = (
        (15 if "Rahu" in sevenths else 0)
        + (15 if "Ketu" in sevenths else 0)
        + (20 if "Saturn" in sevenths else 0)
        + (10 if "Mars" in sevenths else 0)
        + (8 if "Sun" in sevenths else 0)
        + (10 if twelfth_from_7 else 0)
    )

    if karmic_score >= 30:
        karmic_verdict = "STRONG-KARMIC"
    elif karmic_score >= 15:
        karmic_verdict = "MODERATE-KARMIC"
    else:
        karmic_verdict = "LIGHT-KARMIC"

    return {
        "seventh_occupants": sevenths,
        "rahu_in_7th": "Rahu" in sevenths,
        "ketu_in_7th": "Ketu" in sevenths,
        "saturn_in_7th": "Saturn" in sevenths,
        "mars_in_7th": "Mars" in sevenths,
        "twelfth_from_7th_occupants": twelfth_from_7,
        "karmic_score": karmic_score,
        "karmic_verdict": karmic_verdict,
        "flags": flags[:6],
    }


# ── main ─────────────────────────────────────────────────────────
def compute_marriage_bundle(kundli: Dict[str, Any], dob: str,
                              driver: int, conductor: int) -> Dict[str, Any]:
    """T12 Marriage bundle. Hard data gate; never fabricates."""
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

    # ── 1. Saptamesha (7th house + lord) ────────────────────────
    seventh_sign = SIGNS[(asc_idx + 6) % 12]
    seventh_lord = SIGN_LORD[seventh_sign]
    sl_house = p_house.get(seventh_lord, 0)
    sl_sign = _planet_sign(planets, seventh_lord) or "—"
    sl_dignity = _dignity(seventh_lord, sl_sign)
    seventh_occupants = _occupants(planets, asc, 7)

    # 7th-lord strength score (0-100)
    sl_strength = 50
    if sl_house in KENDRA | TRIKONA:
        sl_strength += 20
    elif sl_house in DUSTHANA:
        sl_strength -= 25
    if sl_dignity == "exalted":
        sl_strength += 25
    elif sl_dignity == "own-sign":
        sl_strength += 15
    elif sl_dignity == "debilitated":
        sl_strength -= 25
    sl_strength = max(0, min(100, sl_strength))

    if sl_strength >= 70:
        sl_verdict = "STRONG marital foundation — partnership-karma well-supported"
    elif sl_strength >= 40:
        sl_verdict = "MODERATE marital foundation — workable with conscious effort"
    else:
        sl_verdict = "FRAGILE marital foundation — needs sustained partner-work + remedies"

    saptamesha = {
        "seventh_sign": seventh_sign,
        "seventh_lord": seventh_lord,
        "lord_house": sl_house,
        "lord_sign": sl_sign,
        "lord_dignity": sl_dignity,
        "occupants": seventh_occupants,
        "strength_score": sl_strength,
        "verdict": sl_verdict,
        "spouse_temperament": SEVENTH_SIGN_SPOUSE.get(seventh_sign, "—"),
    }

    # ── 2. Spouse Karaka (Venus default — works for all charts;
    #      Jupiter as secondary karaka for female-spouse readings) ──
    karaka = "Venus"  # primary marriage-karaka in all charts
    karaka_sign = _planet_sign(planets, karaka) or "—"
    karaka_house = p_house.get(karaka, 0)
    karaka_dignity = _dignity(karaka, karaka_sign)
    karaka_strong = (karaka_house in KENDRA | TRIKONA) and karaka_dignity != "debilitated"

    jup_sign = _planet_sign(planets, "Jupiter") or "—"
    jup_house = p_house.get("Jupiter", 0)
    jup_dignity = _dignity("Jupiter", jup_sign)

    spouse_karaka = {
        "primary_karaka": karaka,
        "karaka_sign": karaka_sign,
        "karaka_house": karaka_house,
        "karaka_dignity": karaka_dignity,
        "karaka_well_placed": karaka_strong,
        "secondary_karaka": "Jupiter",
        "jupiter_sign": jup_sign,
        "jupiter_house": jup_house,
        "jupiter_dignity": jup_dignity,
        "note": ("Venus is universal marriage-karaka; Jupiter is the secondary "
                 "karaka — strong for female-spouse indication and for marital wisdom."),
    }

    # ── 3. D9 Spouse Picture + Darakaraka ───────────────────────
    d9 = _d9_data(kundli)
    d9_asc = d9.get("ascendant")
    d9_plist = d9.get("planets", []) or []
    d9_seventh = _d9_seventh_sign(kundli, d9_asc) if d9_asc in SIGNS else None
    d9_seventh_lord = SIGN_LORD.get(d9_seventh or "", "—")
    # Occupants of D9-7th
    d9_seventh_occ: List[str] = []
    if d9_seventh and d9_plist:
        for p in d9_plist:
            if isinstance(p, dict) and p.get("sign") == d9_seventh:
                d9_seventh_occ.append(p.get("name", ""))
    d9_seventh_occ = sorted([x for x in d9_seventh_occ if x])

    darakaraka = _compute_darakaraka(planets)
    dk_sign_d1 = _planet_sign(planets, darakaraka) if darakaraka else None
    dk_sign_d9 = _planet_sign_in_chart(d9_plist, darakaraka) if darakaraka else None

    d9_spouse = {
        "d9_ascendant": d9_asc or "—",
        "d9_seventh_sign": d9_seventh or "—",
        "d9_seventh_lord": d9_seventh_lord,
        "d9_seventh_occupants": d9_seventh_occ,
        "darakaraka": darakaraka or "—",
        "darakaraka_sign_d1": dk_sign_d1 or "—",
        "darakaraka_sign_d9": dk_sign_d9 or "—",
        "note": ("D9 7th = real spouse picture; Darakaraka (lowest-deg karaka, "
                 "Jaimini) = soul-spouse signature."),
    }

    # ── 4. Mangal Dosha Audit ───────────────────────────────────
    mangal = _mangal_audit(planets, asc)

    # ── 5. Marriage Timing Window ───────────────────────────────
    timing = _marriage_timing(kundli, planets, asc, seventh_lord,
                                 karaka, darakaraka)

    # ── 6. Karmic Signatures ────────────────────────────────────
    karmic = _karmic_signatures(planets, asc)

    # ── 7. Synthesis ────────────────────────────────────────────
    # Verdict token logic
    if karmic["karmic_verdict"] == "STRONG-KARMIC" and karmic["saturn_in_7th"]:
        verdict_token = SYNTHESIS_TOKENS["delayed"]
    elif karmic["karmic_verdict"] == "STRONG-KARMIC":
        verdict_token = SYNTHESIS_TOKENS["transformative"]
    elif karmic["karmic_verdict"] == "MODERATE-KARMIC" or mangal["severity"] in ("MODERATE", "SEVERE"):
        verdict_token = SYNTHESIS_TOKENS["karmic"]
    else:
        verdict_token = SYNTHESIS_TOKENS["harmonious"]

    summary_lines = [
        f"7th house {seventh_sign} (lord {seventh_lord} in H{sl_house}, {sl_dignity}) "
        f"— strength {sl_strength}/100.",
        f"Spouse karaka Venus in {karaka_sign} H{karaka_house} ({karaka_dignity}); "
        f"Jupiter in {jup_sign} H{jup_house} ({jup_dignity}).",
        f"D9 7th = {d9_seventh or '—'} (lord {d9_seventh_lord}); Darakaraka = "
        f"{darakaraka or '—'} (in {dk_sign_d1 or '—'} D1, {dk_sign_d9 or '—'} D9).",
        f"Mangal Dosha: {mangal['severity']} — {mangal['verdict']}",
        f"Karmic load: {karmic['karmic_verdict']} (score {karmic['karmic_score']}/100).",
        f"Current dasha: {timing['current_md']} → {timing['current_ad']} — {timing['window_status']}.",
    ]

    spouse_profile_lines = [
        f"Temperament from 7th sign ({seventh_sign}): {SEVENTH_SIGN_SPOUSE.get(seventh_sign, '—')}",
        f"Soul-signature from Darakaraka {darakaraka or '—'} in {dk_sign_d9 or '—'} (D9): "
        f"the spouse-soul resonates with the qualities of {dk_sign_d9 or 'this sign'} — "
        f"this is who your soul actually marries beyond surface attraction.",
    ]

    action_plan: List[str] = []
    if mangal["severity"] in ("MODERATE", "SEVERE"):
        action_plan.append("Perform Mangal-shanti before vows: Mars-day fasts (Tuesdays), "
                            "Hanuman Chalisa daily, donate red lentils, avoid marriage during "
                            "Mars-Mahadasha-start years.")
    if karmic["saturn_in_7th"]:
        action_plan.append("Saturn in 7th: avoid pre-28 marriages; build commitment muscle "
                            "through long-engagement; consult elders before vows.")
    if karmic["rahu_in_7th"]:
        action_plan.append("Rahu in 7th: beware sudden-attraction marriages; meet partner's "
                            "family before deciding; take 6+ months courtship minimum.")
    if karmic["ketu_in_7th"]:
        action_plan.append("Ketu in 7th: marriage must include a shared spiritual practice — "
                            "without it the bond goes cold. Joint sadhana = lifeline.")
    if not karmic["seventh_occupants"]:
        action_plan.append("Empty 7th house: marriage activates only via dasha-bhukti of "
                            "7th-lord/Venus/Jupiter — track those windows carefully.")
    action_plan.append(f"Strengthen Venus (universal marriage-karaka): white clothes Friday, "
                        f"Lakshmi mantra, sweet offerings to women on Fridays, donate ghee/sweets.")
    action_plan.append(f"Best dasha-window planets to watch: {', '.join(timing['activators'])}.")

    synthesis = {
        "verdict_token": verdict_token,
        "summary_lines": summary_lines,
        "spouse_profile_lines": spouse_profile_lines,
        "action_plan": action_plan[:6],
    }

    out["available"] = True
    out["saptamesha"] = saptamesha
    out["spouse_karaka"] = spouse_karaka
    out["d9_spouse"] = d9_spouse
    out["mangal"] = mangal
    out["timing"] = timing
    out["karmic"] = karmic
    out["synthesis"] = synthesis
    return out
