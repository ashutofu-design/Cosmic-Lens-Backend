"""Tier 8 — Health & Longevity bundle.

Combines:
  • Ayurvedic Prakriti (V/P/K) from Moon nakshatra (classical 27-nakshatra map)
  • 6th house deep (disease/debt/enemies) — sign, lord, occupants
  • 8th house deep (longevity/transformation/chronic) — sign, lord, occupants
  • 12th house brief (hospitalization, sleep, foreign healing)
  • Markesha (Maraka) planets — 2nd-lord + 7th-lord (classical death-inflictors)
  • Saturn placement — chronic/joints/bones/teeth signature
  • Sun & Moon vitality — physical (Sun) + mental (Moon) strength
  • Body-part vulnerability map — driver-number × planetary-rulerships
  • Numerology healing toolkit — power foods, lucky gem, healing color, day
  • Current Mahadasha health-window — MD lord vs 6/8/12 houses
  • Synthesis verdict

Public API:
    compute_health_bundle(kundli, dob, driver, conductor) -> dict
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

# ── 27-Nakshatra → Ayurvedic Dosha (classical map) ────────────────
NAKSHATRA_DOSHA: Dict[str, str] = {
    "Ashwini": "Vata", "Bharani": "Pitta", "Krittika": "Kapha", "Rohini": "Kapha",
    "Mrigashira": "Pitta", "Ardra": "Vata", "Punarvasu": "Vata", "Pushya": "Kapha",
    "Ashlesha": "Kapha", "Magha": "Kapha", "Purva Phalguni": "Pitta",
    "Uttara Phalguni": "Pitta", "Hasta": "Vata", "Chitra": "Pitta", "Swati": "Kapha",
    "Vishakha": "Kapha", "Anuradha": "Pitta", "Jyeshtha": "Vata", "Mula": "Vata",
    "Purva Ashadha": "Pitta", "Uttara Ashadha": "Kapha", "Shravana": "Kapha",
    "Dhanishta": "Pitta", "Dhanishtha": "Pitta",
    "Shatabhisha": "Vata", "Purva Bhadrapada": "Vata",
    "Uttara Bhadrapada": "Pitta", "Revati": "Kapha",
}

# Canonical aliases — engine spelling variants normalize to dosha-table keys
_NAKSHATRA_ALIASES: Dict[str, str] = {
    "dhanishtha": "Dhanishta", "dhanistha": "Dhanishta",
    "purvaphalguni": "Purva Phalguni", "uttaraphalguni": "Uttara Phalguni",
    "purvashadha": "Purva Ashadha", "uttarashadha": "Uttara Ashadha",
    "purvabhadrapada": "Purva Bhadrapada", "uttarabhadrapada": "Uttara Bhadrapada",
    "shatbhisha": "Shatabhisha", "shatabhishak": "Shatabhisha",
    "moola": "Mula",
}


def _norm_nakshatra(raw: str) -> str:
    """Normalize engine nakshatra string to a canonical NAKSHATRA_DOSHA key."""
    if not raw or not isinstance(raw, str):
        return ""
    s = raw.strip()
    if s in NAKSHATRA_DOSHA:
        return s
    key = "".join(s.lower().split())
    if key in _NAKSHATRA_ALIASES:
        return _NAKSHATRA_ALIASES[key]
    # try title-case match
    t = s.title()
    if t in NAKSHATRA_DOSHA:
        return t
    return ""

DOSHA_PROFILE: Dict[str, Dict[str, str]] = {
    "Vata": {
        "element": "Air + Ether",
        "qualities": "dry, light, cold, mobile, irregular",
        "body_signs": "thin frame, dry skin, cold hands/feet, light sleeper, fast metabolism",
        "mind_signs": "creative, restless, anxious when stressed, scattered focus",
        "vulnerable_to": "anxiety, insomnia, joint pain, gas/bloating, dry skin, nervous-system disorders",
        "balancing_lifestyle": "warm cooked food, ghee, oil massage (abhyanga), regular routine, early sleep, reduce caffeine",
        "favourable_taste": "sweet, sour, salty",
        "avoid_taste": "bitter, pungent, astringent (in excess)",
    },
    "Pitta": {
        "element": "Fire + Water",
        "qualities": "hot, sharp, oily, light, intense",
        "body_signs": "medium build, warm skin, strong digestion, sharp hunger, prone to redness",
        "mind_signs": "ambitious, intelligent, sharp focus, irritable when hungry",
        "vulnerable_to": "acidity, ulcers, skin inflammation, anger issues, liver heat, hair loss/greying",
        "balancing_lifestyle": "cool foods (cucumber, milk, ghee), avoid spicy/fried, moonlight walks, breath-cooling pranayam (sheetali)",
        "favourable_taste": "sweet, bitter, astringent",
        "avoid_taste": "pungent, sour, salty (in excess)",
    },
    "Kapha": {
        "element": "Earth + Water",
        "qualities": "heavy, slow, cool, oily, stable",
        "body_signs": "sturdy frame, oily skin, slow digestion, deep sleep, stable energy",
        "mind_signs": "calm, loyal, methodical, lethargic when stressed, attached",
        "vulnerable_to": "weight gain, diabetes, congestion, lethargy, depression, water-retention, sinusitis",
        "balancing_lifestyle": "vigorous exercise, warm spiced food, avoid dairy/sweets, early rising, fasting once a week",
        "favourable_taste": "pungent, bitter, astringent",
        "avoid_taste": "sweet, sour, salty (in excess)",
    },
}

# ── Planet → body-part rulership (classical Brihat Parashara) ─────
PLANET_BODY: Dict[str, str] = {
    "Sun":     "heart, eyes (right), spine, stomach upper, vitality / immunity",
    "Moon":    "stomach, lungs, breast, body fluids, mental peace, sleep",
    "Mars":    "blood, muscles, bone marrow, forehead, surgical wounds, BP",
    "Mercury": "skin, lungs, intestines, nervous system, speech, allergies",
    "Jupiter": "liver, thighs, fat, pancreas (diabetes), ears",
    "Venus":   "kidneys, throat, reproductive, eyes (left), skin glow, sweets",
    "Saturn":  "bones, joints, knees, teeth, chronic conditions, longevity",
    "Rahu":    "nervous system, anxiety, mysterious illnesses, skin, addictions",
    "Ketu":    "feet, mysterious illnesses, parasitic, immunity collapse, viral",
}

# ── Driver-number health vulnerability map ────────────────────────
DRIVER_HEALTH: Dict[int, Dict[str, Any]] = {
    1: {"planet": "Sun",
        "vulnerable": "heart, blood-pressure, eyes, spine, fevers",
        "power_foods": "wheat, ghee, almonds, dates, citrus, jaggery",
        "avoid_foods": "excess salt, fried, late-night meals",
        "best_exercise": "morning sun-walk, surya namaskar, brisk cardio",
        "healing_practice": "Sunday sun-gazing (sunrise only), Aditya Hridaya Stotra, copper water",
        "danger_age_windows": "around 22, 31, 40 — annual eye + heart check"},
    2: {"planet": "Moon",
        "vulnerable": "stomach, sleep, anxiety, fluids retention, breast/lungs",
        "power_foods": "milk, rice, coconut water, leafy greens, melons",
        "avoid_foods": "stale food, deep-fried, excess caffeine",
        "best_exercise": "swimming, yoga (chandra namaskar), evening walks",
        "healing_practice": "Monday fasting (light), moon-gazing, silver in water, meditation",
        "danger_age_windows": "around 25, 34, 43 — mental health + digestion check"},
    3: {"planet": "Jupiter",
        "vulnerable": "liver, weight gain, diabetes, hips, ears",
        "power_foods": "yellow daal, turmeric milk, bananas, honey, ghee (moderate)",
        "avoid_foods": "excess sweets, alcohol, fried snacks, cold drinks",
        "best_exercise": "yoga, hiking, sun salutations, weight training (moderate)",
        "healing_practice": "Thursday Brihaspati pooja, fasting on Thursday, donate yellow grains",
        "danger_age_windows": "around 30, 39, 48 — liver + sugar panel"},
    4: {"planet": "Rahu",
        "vulnerable": "nervous system, anxiety, mysterious illnesses, skin, sudden injury",
        "power_foods": "moong daal, brown rice, coconut, almonds, herbal teas",
        "avoid_foods": "processed food, excessive screen-snacking, alcohol, junk",
        "best_exercise": "pranayam (anulom-vilom), mindful walking, swimming, yoga nidra",
        "healing_practice": "Saraswati mantra, mauna (silence) for 30 min/day, blue lapis",
        "danger_age_windows": "around 23, 32, 41 — mental health + skin allergy screen"},
    5: {"planet": "Mercury",
        "vulnerable": "nervous system, lungs, skin allergies, speech, intestines",
        "power_foods": "green vegetables, sprouted moong, mint, lemon water, olives",
        "avoid_foods": "spicy, gas-forming (chickpea/cabbage in excess), fast food",
        "best_exercise": "fast walking, tennis, table tennis, breathing exercises",
        "healing_practice": "Vishnu Sahasranama, Wednesday green-color clothing, emerald (if Mercury weak)",
        "danger_age_windows": "around 24, 33, 42 — lung + allergy + nervous panel"},
    6: {"planet": "Venus",
        "vulnerable": "kidneys, throat, reproductive system, sweets-induced (diabetes/PCOS), skin",
        "power_foods": "fruits, salads, dairy (curd), pomegranate, watermelon, coconut",
        "avoid_foods": "excess sugar, deep-fried, alcohol, processed cheese",
        "best_exercise": "dance, gentle yoga, partner sports, walking with music",
        "healing_practice": "Friday Lakshmi pooja, white/cream clothing, diamond/zircon, rose-quartz",
        "danger_age_windows": "around 26, 35, 44 — kidney + reproductive + sugar check"},
    7: {"planet": "Ketu",
        "vulnerable": "mysterious illnesses, parasitic infections, immunity, feet, viral",
        "power_foods": "ginger-tulsi tea, garlic, turmeric, light vegetarian, fasting",
        "avoid_foods": "non-veg in excess, alcohol, raw food (immunity-low days)",
        "best_exercise": "yoga, walking in nature, light cycling, vipassana retreat",
        "healing_practice": "Ganesh + Ketu mantra, smoky-quartz, Tuesday fasting, foot care/oil",
        "danger_age_windows": "around 28, 37, 46 — immunity + auto-immune panel"},
    8: {"planet": "Saturn",
        "vulnerable": "bones, joints, teeth, knees, chronic fatigue, depression",
        "power_foods": "black sesame, urad daal, jaggery, ginger, leafy greens, warm spices",
        "avoid_foods": "cold/raw, refined sugar, processed meat, excess cold drinks",
        "best_exercise": "weight training, yoga (consistent daily), walking, calcium-rich diet",
        "healing_practice": "Saturday Hanuman Chalisa (11x), black sesame oil massage, blue sapphire (after test)",
        "danger_age_windows": "around 27 (Saturn return), 36, 45, 54 — bone + thyroid + Vit-D"},
    9: {"planet": "Mars",
        "vulnerable": "blood pressure, accidents, surgery, fevers, inflammation, head injury",
        "power_foods": "lentils, spinach, beetroot, pomegranate, red fruits (iron)",
        "avoid_foods": "excess red meat, alcohol, very spicy (acidity)",
        "best_exercise": "running, martial arts, weights, swimming (cool down anger)",
        "healing_practice": "Tuesday Hanuman Chalisa, red coral (after test), donate red lentils, anger management",
        "danger_age_windows": "around 28, 37, 46 — BP + accident-awareness + iron panel"},
}


def _planet_house_d1(planets: List[Dict], asc_sign: str) -> Dict[str, int]:
    if not isinstance(planets, list) or asc_sign not in SIGNS:
        return {}
    asc_idx = SIGNS.index(asc_sign)
    out: Dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict): continue
        sgn = p.get("sign"); nm = p.get("name")
        if sgn in SIGNS and nm:
            sidx = SIGNS.index(sgn)
            out[nm] = ((sidx - asc_idx + 12) % 12) + 1
    return out


def _occupants(planets: List[Dict], asc_sign: str, house_num: int) -> List[str]:
    h = _planet_house_d1(planets, asc_sign)
    return sorted([nm for nm, hn in h.items() if hn == house_num])


def _resolve_md_end(kundli: Dict, md_lord: str) -> str:
    try:
        from datetime import datetime as _dt
        today = _dt.now().date()
        for entry in (kundli.get("dashas") or []):
            if entry.get("planet") != md_lord: continue
            try:
                start = _dt.strptime(entry.get("startDate", ""), "%Y-%m-%d").date()
                end = _dt.strptime(entry.get("endDate", ""), "%Y-%m-%d").date()
            except Exception:
                continue
            if start <= today <= end:
                return entry.get("endDate", "—")
        for entry in (kundli.get("dashas") or []):
            if entry.get("planet") == md_lord:
                return entry.get("endDate", "—")
    except Exception:
        pass
    return "—"


def _synergy(driver: int, conductor: int) -> str:
    try:
        from vedic.numerology.framing import _synergy_verdict
        return _synergy_verdict(driver, conductor)
    except Exception:
        return "NEUTRAL"


def compute_health_bundle(kundli: Dict[str, Any], dob: str,
                          driver: int, conductor: int) -> Dict[str, Any]:
    """Compute T8 Health bundle. Returns {'available': False, 'reason': ...} if
    core medical anchors are missing — never falls back to fabricated facts."""
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"
        return out

    # ── HARD DATA GATE: refuse to fabricate facts on missing anchors ──
    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []
    nak_raw = (kundli.get("nakshatra") or "").strip()

    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing or unknown ({asc!r})"
        return out
    if not isinstance(planets, list) or len(planets) < 7:
        out["reason"] = f"planets list incomplete (n={len(planets) if isinstance(planets, list) else 0})"
        return out
    planet_names = {p.get("name") for p in planets if isinstance(p, dict)}
    required = {"Sun", "Moon", "Saturn"}
    missing_req = required - planet_names
    if missing_req:
        out["reason"] = f"missing required planets: {sorted(missing_req)}"
        return out
    if not nak_raw:
        out["reason"] = "Moon nakshatra missing — cannot compute Prakriti"
        return out

    nak_name = _norm_nakshatra(nak_raw)
    if not nak_name:
        out["reason"] = f"nakshatra {nak_raw!r} not recognized after normalization"
        return out

    asc_idx = SIGNS.index(asc)
    p_house = _planet_house_d1(planets, asc)

    # ── 1. Ayurvedic Prakriti (Moon nakshatra → dosha) ────────────
    pak_pada = kundli.get("nakshatraPada") or 0
    moon_sign = kundli.get("moonSign") or "—"
    dosha = NAKSHATRA_DOSHA[nak_name]  # guaranteed by gate above
    dprof = DOSHA_PROFILE.get(dosha, DOSHA_PROFILE["Vata"])
    prakriti = {
        "moon_sign": moon_sign,
        "nakshatra": nak_name or "—",
        "pada": pak_pada,
        "dominant_dosha": dosha,
        "element": dprof["element"],
        "qualities": dprof["qualities"],
        "body_signs": dprof["body_signs"],
        "mind_signs": dprof["mind_signs"],
        "vulnerable_to": dprof["vulnerable_to"],
        "balancing_lifestyle": dprof["balancing_lifestyle"],
        "favourable_taste": dprof["favourable_taste"],
        "avoid_taste": dprof["avoid_taste"],
    }

    # ── 2. 6th, 8th, 12th house deep ──────────────────────────────
    def _house_block(num: int) -> Dict[str, Any]:
        sign = SIGNS[(asc_idx + num - 1) % 12]
        lord = SIGN_LORD.get(sign, "—")
        occ = _occupants(planets, asc, num)
        return {
            "house": num, "sign": sign, "lord": lord,
            "lord_house": p_house.get(lord, 0),
            "occupants": occ, "occupants_count": len(occ),
        }
    sixth = _house_block(6)   # disease, debt, enemies
    eighth = _house_block(8)  # longevity, chronic, transformation
    twelfth = _house_block(12)  # hospitalization, sleep, foreign healing

    # ── 3. Markesha (Maraka) planets — 2nd lord + 7th lord ────────
    second_sign = SIGNS[(asc_idx + 1) % 12]
    seventh_sign = SIGNS[(asc_idx + 6) % 12]
    second_lord = SIGN_LORD.get(second_sign, "—")
    seventh_lord = SIGN_LORD.get(seventh_sign, "—")
    markeshas = sorted({second_lord, seventh_lord} - {"—"})
    markesha_block = {
        "second_lord": second_lord,
        "seventh_lord": seventh_lord,
        "markeshas": markeshas,
        "markesha_houses": {m: p_house.get(m, 0) for m in markeshas},
        "note": ("Markeshas are classical 'death-inflictors' — their Mahadasha/Antardasha "
                 "periods historically correlate with health-crisis windows. Modern reading: "
                 "treat these periods as MANDATORY annual-checkup years, not as fear-triggers."),
    }

    # ── 4. Saturn profile (chronic / joints / longevity) ──────────
    sat_house = p_house.get("Saturn", 0)
    sat_sign = next((p.get("sign") for p in planets if p.get("name") == "Saturn"), "—")
    sat_in_lagna_or_dusthana = sat_house in {1, 6, 8, 12}
    saturn = {
        "house": sat_house,
        "sign": sat_sign,
        "is_chronic_signature": sat_in_lagna_or_dusthana,
        "verdict": (
            "Saturn placed in a sensitive house (1/6/8/12) — chronic-pattern signature: "
            "watch joints, bones, teeth, thyroid; be ULTRA-disciplined with diet+sleep "
            "post-age-27 (Saturn return)."
            if sat_in_lagna_or_dusthana
            else "Saturn placement is benign for health — chronic-illness drag is LOW; "
                 "still maintain bone/Vit-D check after 35."
        ),
    }

    # ── 5. Sun + Moon vitality ────────────────────────────────────
    sun_house = p_house.get("Sun", 0)
    moon_house = p_house.get("Moon", 0)
    sun_strong = sun_house in {1, 3, 5, 9, 10, 11} or (
        next((p.get("sign") for p in planets if p.get("name") == "Sun"), "") == "Leo"
    )
    moon_strong = moon_house in {1, 4, 5, 7, 9, 10, 11} or (
        next((p.get("sign") for p in planets if p.get("name") == "Moon"), "") in ("Cancer", "Taurus")
    )
    vitality = {
        "sun_house": sun_house,
        "sun_strong": sun_strong,
        "physical_vitality": "STRONG" if sun_strong else "MODERATE — daily sun-walk recommended",
        "moon_house": moon_house,
        "moon_strong": moon_strong,
        "mental_vitality": "STRONG" if moon_strong else "MODERATE — daily 10-min meditation recommended",
    }

    # ── 6. Body-part vulnerability map (driver-based + chart) ────
    dh = DRIVER_HEALTH.get(driver, DRIVER_HEALTH[1])
    body_map = {
        "primary_planet": dh["planet"],
        "primary_vulnerable": dh["vulnerable"],
        "primary_body_parts": PLANET_BODY.get(dh["planet"], ""),
        "secondary_layers": [],
    }
    # Add layers from afflicted houses (6th/8th occupants — those planets' body parts at risk)
    for plnt in (sixth["occupants"] + eighth["occupants"]):
        if plnt and PLANET_BODY.get(plnt):
            body_map["secondary_layers"].append({
                "planet": plnt,
                "body_parts": PLANET_BODY[plnt],
                "from_house": "6th" if plnt in sixth["occupants"] else "8th",
            })

    # ── 7. Numerology healing toolkit ─────────────────────────────
    healing = {
        "driver": driver,
        "primary_planet": dh["planet"],
        "power_foods": dh["power_foods"],
        "avoid_foods": dh["avoid_foods"],
        "best_exercise": dh["best_exercise"],
        "healing_practice": dh["healing_practice"],
        "danger_age_windows": dh["danger_age_windows"],
    }
    # Pull lucky color/gem from framing.LUCKY for completeness
    try:
        from vedic.numerology.framing import LUCKY
        lk = LUCKY.get(driver, {})
        healing["lucky_healing_color"] = lk.get("colors", "—")
        healing["lucky_healing_gem"] = lk.get("gem", "—")
        healing["lucky_healing_metal"] = lk.get("metal", "—")
    except Exception:
        healing["lucky_healing_color"] = "—"
        healing["lucky_healing_gem"] = "—"
        healing["lucky_healing_metal"] = "—"

    # ── 8. Current Mahadasha health-window ────────────────────────
    cur = (kundli.get("currentDasha") or {})
    md_lord = cur.get("maha") or "—"
    ad_lord = cur.get("antar") or "—"
    md_end = _resolve_md_end(kundli, md_lord) if md_lord != "—" else "—"
    md_house = p_house.get(md_lord, 0)

    if md_house in {6, 8, 12}:
        h_verdict = "HEALTH-VIGILANCE"
        h_note = (f"Current MD lord {md_lord} sits in House {md_house} (6/8/12 — "
                  f"sensitive). Treat the entire MD as a mandatory-checkup window. "
                  f"Sleep + diet discipline > heroic exercise. Check liver/kidney/thyroid yearly.")
    elif md_lord in markeshas:
        h_verdict = "MARKESHA-WINDOW"
        h_note = (f"Current MD lord {md_lord} is a Markesha (2nd/7th lord) — classical "
                  f"caution window. Modern: be DISCIPLINED with annual checkups and avoid "
                  f"reckless habits (smoking, drinking, late-night). Most people pass through "
                  f"safely with awareness.")
    elif md_house in {1, 5, 9, 11}:
        h_verdict = "ROBUST-WINDOW"
        h_note = (f"Current MD lord {md_lord} in House {md_house} — body has good fuel, "
                  f"capitalize on stamina; build long-term fitness habits NOW.")
    else:
        h_verdict = "STEADY"
        h_note = (f"Current MD lord {md_lord} in House {md_house} — neutral health window; "
                  f"normal maintenance routine sufficient.")

    health_window = {
        "md_lord": md_lord, "ad_lord": ad_lord, "md_house": md_house,
        "md_end_date": md_end, "verdict": h_verdict, "note": h_note,
    }

    # ── 9. Synthesis verdict ──────────────────────────────────────
    syn = (
        f"Prakriti = {dosha} ({dprof['qualities']}). "
        f"Driver-{driver} ({dh['planet']}) → primary vulnerability: {dh['vulnerable']}. "
        f"6th-lord {sixth['lord']} in H{sixth['lord_house']}, "
        f"8th-lord {eighth['lord']} in H{eighth['lord_house']}. "
        f"Saturn in H{sat_house} → "
        f"{'chronic-watch signature' if sat_in_lagna_or_dusthana else 'low chronic-drag'}. "
        f"Current MD ({md_lord}) → {h_verdict}. "
        f"Toolkit: {dh['healing_practice'].split(',')[0]} + diet alignment to {dosha}-pacifying."
    )

    out.update({
        "available": True,
        "prakriti": prakriti,
        "sixth_house": sixth,
        "eighth_house": eighth,
        "twelfth_house": twelfth,
        "markesha": markesha_block,
        "saturn_profile": saturn,
        "vitality": vitality,
        "body_map": body_map,
        "healing_toolkit": healing,
        "health_window": health_window,
        "numerology_synergy": _synergy(driver, conductor),
        "synthesis_verdict": syn,
    })
    return out
