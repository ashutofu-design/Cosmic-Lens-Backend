"""
dosh_engine.py — Complete Vedic Dosh Analysis Engine (16 Doshas)
Planets input: list of { name, house, longitude, sign, retrograde }
"""

import hashlib, json

# ── In-memory cache (keyed by MD5 of planets) ─────────────────────────────────
_dosh_cache: dict = {}


def _cache_key(planets: list, nakshatra: str) -> str:
    data = json.dumps(
        {"p": sorted(planets, key=lambda x: x.get("name", "")), "n": nakshatra},
        sort_keys=True
    )
    return hashlib.md5(data.encode()).hexdigest()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _house(pl: list, name: str) -> int:
    p = next((x for x in pl if x.get("name") == name), None)
    return int(p["house"]) if p else 0


def _lon(pl: list, name: str) -> float:
    p = next((x for x in pl if x.get("name") == name), None)
    return float(p.get("longitude", 0.0)) if p else 0.0


def _has(pl: list, name: str) -> bool:
    """Explicit existence check — never conflate longitude=0.0 (valid 0° Aries) with missing data."""
    return any(x.get("name") == name and "longitude" in x for x in pl)


def _planets_in_house(pl: list, house: int) -> list:
    return [p["name"] for p in pl if int(p.get("house", 0)) == house]


def _orb(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ── Sign / lord / dignity helpers (used by lord-based doshas) ────────────────
SIGN_LORD = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}
SIGN_NAMES_LOWER = {
    "aries": 1, "taurus": 2, "gemini": 3, "cancer": 4, "leo": 5, "virgo": 6,
    "libra": 7, "scorpio": 8, "sagittarius": 9, "capricorn": 10, "aquarius": 11, "pisces": 12,
}
EXALT_SIGN = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7,
}
OWN_SIGNS = {
    "Sun": {5}, "Moon": {4}, "Mars": {1, 8}, "Mercury": {3, 6},
    "Jupiter": {9, 12}, "Venus": {2, 7}, "Saturn": {10, 11},
}


def _sign_idx(p: dict) -> int:
    """Return 1-12 sign index from longitude (preferred), else from sign field."""
    if p and "longitude" in p:
        try:
            return int(float(p["longitude"]) // 30) + 1
        except (TypeError, ValueError):
            pass
    s = p.get("sign") if p else None
    if isinstance(s, int) and 1 <= s <= 12:
        return s
    if isinstance(s, str):
        return SIGN_NAMES_LOWER.get(s.strip().lower(), 0)
    return 0


def _asc_sign(pl: list) -> int:
    """Derive ascendant sign (1-12) from any planet with valid sign+house."""
    for p in pl:
        sign_idx = _sign_idx(p)
        h = p.get("house")
        if 1 <= sign_idx <= 12 and isinstance(h, int) and 1 <= h <= 12:
            return ((sign_idx - h) % 12) + 1
    return 0


def _house_lord(asc_sign: int, h: int) -> str:
    """Return planet ruling house h, given ascendant sign (1-12). Empty string if invalid."""
    if asc_sign < 1 or h < 1:
        return ""
    return SIGN_LORD[((asc_sign - 1 + h - 1) % 12) + 1]


def _planet_obj(pl: list, name: str) -> dict:
    """Find a planet dict by name. Returns empty dict if not found."""
    return next((p for p in pl if p.get("name") == name), {}) or {}


# ── Aspect helpers ────────────────────────────────────────────────────────────
# Nth house from H (counted inclusively, H itself = 1st) = ((H - 1 + N - 1) % 12) + 1
# Equivalent shorthand: ((H + N - 2) % 12) + 1

def _saturn_aspects_house(sat_h: int, target_h: int) -> bool:
    """Saturn's classical 3rd / 7th / 10th drishti (special aspects)."""
    if sat_h < 1 or target_h < 1:
        return False
    aspects = {
        (sat_h + 1) % 12 + 1,   # 3rd
        (sat_h + 5) % 12 + 1,   # 7th
        (sat_h + 8) % 12 + 1,   # 10th
    }
    return target_h in aspects


def _jupiter_aspects_house(jup_h: int, target_h: int) -> bool:
    """Jupiter's classical 5th / 7th / 9th drishti."""
    if jup_h < 1 or target_h < 1:
        return False
    aspects = {
        (jup_h + 3) % 12 + 1,   # 5th
        (jup_h + 5) % 12 + 1,   # 7th
        (jup_h + 7) % 12 + 1,   # 9th
    }
    return target_h in aspects


def _is_strong(pl: list, planet: str) -> bool:
    """A planet is classically 'strong' if in kendra/trikona, exalted, or in own sign."""
    if not planet:
        return False
    KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}
    ph = _house(pl, planet)
    p_obj = _planet_obj(pl, planet)
    p_sign = _sign_idx(p_obj)
    return (
        (ph in KENDRA_TRIKONA)
        or (p_sign and p_sign == EXALT_SIGN.get(planet))
        or (p_sign in OWN_SIGNS.get(planet, set()))
    )


def _mars_aspects_house(mars_h: int, target_h: int) -> bool:
    """Mars's classical 4th / 7th / 8th drishti."""
    if mars_h < 1 or target_h < 1:
        return False
    aspects = {
        (mars_h + 2) % 12 + 1,   # 4th
        (mars_h + 5) % 12 + 1,   # 7th
        (mars_h + 6) % 12 + 1,   # 8th
    }
    return target_h in aspects


# Debilitation sign for each graha (sign index 1-12)
DEBIL_SIGN = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
    "Jupiter": 10, "Venus": 6, "Saturn": 1,
    "Rahu": 8, "Ketu": 2,
}


def _is_combust(pl: list, planet: str, orb: float = 8.0) -> bool:
    """Planet is combust if within `orb` degrees of the Sun (excluding Sun itself)."""
    if planet == "Sun":
        return False
    sun_lon = _lon(pl, "Sun")
    p_lon = _lon(pl, planet)
    if not _has(pl, "Sun") or not _has(pl, planet):
        return False
    return _orb(sun_lon, p_lon) < orb


def _is_debilitated(pl: list, planet: str) -> bool:
    p_obj = _planet_obj(pl, planet)
    p_sign = _sign_idx(p_obj)
    return p_sign and p_sign == DEBIL_SIGN.get(planet)


# ── 1. Manglik Dosh ────────────────────────────────────────────────────────────
def _manglik(pl):
    mars_h = _house(pl, "Mars")
    if mars_h in (1, 4, 7, 8, 12):
        return (
            "Active",
            f"Mars in {mars_h}th House — Strong Manglik Dosh",
            "Mars placed in houses 1, 4, 7, 8, or 12 creates Manglik Dosh, strongly affecting marriage and relationships. Can cause tension and conflict in partnerships.",
            [
                "Perform Kumbh Vivah (symbolic marriage to a tree) before wedding",
                "Offer sindoor to Hanuman ji on every Tuesday",
                "Wear or keep a Mangal Yantra at home puja altar",
                "Donate jaggery (gur) and chana dal on Tuesdays",
                "Chant Mangal Beej mantra: Om Kram Kreem Kraum Sah Bhaumaya Namah 108×",
            ],
            f"Mars → House {mars_h}",
        )
    elif mars_h == 2:
        return (
            "Mild",
            "Mars in 2nd House — Partial Manglik Dosh",
            "Mars in the 2nd house creates a partial Manglik condition affecting speech and family harmony.",
            [
                "Worship Lord Hanuman regularly",
                "Keep Mars-related fasts on Tuesdays",
            ],
            f"Mars → House {mars_h}",
        )
    return (
        "None",
        f"Mars in {mars_h}th House — No Manglik Dosh",
        "Mars is in a neutral or beneficial position. No Manglik Dosh present in this chart.",
        [],
        f"Mars → House {mars_h}",
    )


# ── 2. Kaal Sarp Dosh ─────────────────────────────────────────────────────────
# 12 classical Kaal Sarp variants — keyed by Rahu's house (1..12)
_KAAL_SARP_VARIANTS = {
    1:  "Anant",        # Rahu H1  → Ketu H7
    2:  "Kulik",        # Rahu H2  → Ketu H8
    3:  "Vasuki",       # Rahu H3  → Ketu H9
    4:  "Shankhpal",    # Rahu H4  → Ketu H10
    5:  "Padma",        # Rahu H5  → Ketu H11
    6:  "Mahapadma",    # Rahu H6  → Ketu H12
    7:  "Takshak",      # Rahu H7  → Ketu H1
    8:  "Karkotak",     # Rahu H8  → Ketu H2
    9:  "Shankhachuda", # Rahu H9  → Ketu H3
    10: "Ghatak",       # Rahu H10 → Ketu H4
    11: "Vishdhar",     # Rahu H11 → Ketu H5
    12: "Sheshnag",     # Rahu H12 → Ketu H6
}


def _kaal_sarp(pl):
    rahu_lon = _lon(pl, "Rahu")
    rahu_h   = _house(pl, "Rahu")
    ketu_h   = _house(pl, "Ketu")
    core     = [p for p in pl if p.get("name") not in ("Rahu", "Ketu")]
    if not core:
        return ("None", "Insufficient data", "", [], "")

    # All 7 core planets must lie within the Rahu→Ketu 180° arc for full Kaal Sarp
    in_arc = [(_lon(pl, p["name"]) - rahu_lon) % 360 < 180 for p in core]
    all_in = all(in_arc)

    if all_in:
        variant = _KAAL_SARP_VARIANTS.get(rahu_h, "Unknown")
        return (
            "Active",
            f"Kaal Sarp Dosh ({variant}) — All Planets in Rahu–Ketu Arc",
            f"All seven core planets fall within the Rahu–Ketu axis (Rahu in House {rahu_h} → {variant} variant). Creates obstacles, delays, vivid dreams, sudden reversals, and a feeling of life being restrained.",
            [
                "Perform Kaal Sarp Pooja at Trimbakeshwar, Ujjain, or Nashik",
                "Offer milk to a serpent idol on Nagpanchami",
                "Chant Mahamrityunjay mantra 108 times daily",
                "Offer sesame oil at a Navagraha temple for Rahu",
                "Donate black items (sesame, cloth) on Saturdays for Ketu",
            ],
            f"Rahu → House {rahu_h} | Ketu → House {ketu_h} | Variant: {variant}",
        )
    return (
        "None",
        "No Kaal Sarp Dosh — Planets Spread Freely",
        "Not all planets fall within the Rahu–Ketu arc. Per classical rule, full Kaal Sarp requires all seven core planets enclosed between the nodes — so no Kaal Sarp Dosh is present.",
        [],
        f"Rahu → House {rahu_h} | Ketu → House {ketu_h}",
    )


# ── 3. Pitru Dosh ─────────────────────────────────────────────────────────────
# Classical Pitra Dosh (ancestor curse) — BPHS + Lal Kitab + Nadi tradition.
# Triggers (score-weighted):
#   T1: Sun + Rahu conjunction                                 +3 (strongest)
#   T2: Sun + Ketu conjunction                                 +2
#   T3: Sun + Saturn conjunction in 9th house                  +3 (father-dharma break)
#   T4: 9th lord in 6/8/12 (dusthana)                          +2
#   T5: Rahu OR Ketu placed in 9th house                       +2
#   T6: Sun in 6/8/12 (dusthana)                               +1
#   T7: Saturn aspects Sun via 3rd/7th/10th drishti            +2
#   T8: 9th lord combust (within 8° of Sun) OR debilitated     +1
#   T9: ≥2 malefics (Sat/Mars/Rah/Ket) in OR aspecting 9th     +2
# Amplifiers (each +1):
#   A1: primary trigger sits in 9th house itself
#   A2: primary trigger in dusthana 6/8/12
#   A3: 5th house also afflicted (malefic in 5th OR 5L in dusthana) — curse passes to progeny
# Bhangas (each -1):
#   B1: Jupiter 5/7/9 drishti on 9th house OR 9th lord (Guru blessings)
#   B2: 9th lord exalted OR in own sign
#   B3: Sun in own sign (Leo) OR exalted (Aries)
#   B4: 5th lord strong + Jupiter strong (progeny + dharma intact)
#   B5: 9th lord in kendra/trikona (1/4/5/7/9/10)
# Tier:
#   No triggers              → None
#   ≥2 bhanga                → forced None (curse cancelled)
#   score ≥ 4                → Active
#   score 1..3               → Mild
#   score ≤ 0                → None
def _pitru(pl):
    sun_h  = _house(pl, "Sun")
    rahu_h = _house(pl, "Rahu")
    ketu_h = _house(pl, "Ketu")
    sat_h  = _house(pl, "Saturn")
    mars_h = _house(pl, "Mars")
    jup_h  = _house(pl, "Jupiter")

    triggers = []
    score = 0
    trigger_house = 0

    # ── T1: Sun-Rahu conjunction ───────────────────────────────────────────────
    if sun_h and sun_h == rahu_h:
        triggers.append(f"Sun-Rahu Conjunction in H{sun_h}")
        trigger_house = sun_h
        score += 3
    # ── T2: Sun-Ketu conjunction ───────────────────────────────────────────────
    if sun_h and sun_h == ketu_h:
        triggers.append(f"Sun-Ketu Conjunction in H{sun_h}")
        if not trigger_house:
            trigger_house = sun_h
        score += 2
    # ── T3: Sun-Saturn conjunction in 9th house specifically ───────────────────
    if sun_h and sun_h == sat_h and sun_h == 9:
        triggers.append("Sun-Saturn Conjunction in 9th (father-dharma break)")
        if not trigger_house:
            trigger_house = 9
        score += 3

    # ── 9th lord lookups (need ascendant) ──────────────────────────────────────
    asc = _asc_sign(pl)
    L9 = _house_lord(asc, 9) if asc else ""
    L5 = _house_lord(asc, 5) if asc else ""
    L9_h = _house(pl, L9) if L9 else 0

    # ── T4: 9L in 6/8/12 ──────────────────────────────────────────────────────
    if L9 and L9_h in {6, 8, 12}:
        triggers.append(f"9th lord ({L9}) in dusthana H{L9_h}")
        if not trigger_house:
            trigger_house = L9_h
        score += 2

    # ── T5: Rahu or Ketu in 9th ───────────────────────────────────────────────
    nodes_in_9 = [n for n, h in [("Rahu", rahu_h), ("Ketu", ketu_h)] if h == 9]
    if nodes_in_9:
        triggers.append(f"{'/'.join(nodes_in_9)} in 9th house (Pitra Bhava direct affliction)")
        if not trigger_house:
            trigger_house = 9
        score += 2

    # ── T6: Sun in 6/8/12 ─────────────────────────────────────────────────────
    if sun_h in {6, 8, 12}:
        triggers.append(f"Sun in dusthana H{sun_h}")
        if not trigger_house:
            trigger_house = sun_h
        score += 1

    # ── T7: Saturn aspects Sun via 3/7/10 drishti ─────────────────────────────
    if sat_h and sun_h and sat_h != sun_h and _saturn_aspects_house(sat_h, sun_h):
        triggers.append(f"Saturn (H{sat_h}) drishti on Sun (H{sun_h})")
        if not trigger_house:
            trigger_house = sun_h
        score += 2

    # ── T8: 9L combust OR debilitated ────────────────────────────────────────
    if L9 and (_is_combust(pl, L9) or _is_debilitated(pl, L9)):
        why = "combust" if _is_combust(pl, L9) else "debilitated"
        triggers.append(f"9th lord ({L9}) {why}")
        if not trigger_house:
            trigger_house = L9_h or 9
        score += 1

    # ── T9: ≥2 malefics in or aspecting 9th ──────────────────────────────────
    malefic_hits = []
    # Placement in 9th
    for m, h in [("Saturn", sat_h), ("Mars", mars_h), ("Rahu", rahu_h), ("Ketu", ketu_h)]:
        if h == 9:
            malefic_hits.append(f"{m} in 9th")
    # Saturn aspects 9th
    if sat_h and sat_h != 9 and _saturn_aspects_house(sat_h, 9):
        malefic_hits.append(f"Saturn drishti on 9th")
    # Mars aspects 9th
    if mars_h and mars_h != 9 and _mars_aspects_house(mars_h, 9):
        malefic_hits.append(f"Mars drishti on 9th")
    if len(malefic_hits) >= 2:
        triggers.append(f"≥2 malefics on 9th: {', '.join(malefic_hits)}")
        if not trigger_house:
            trigger_house = 9
        score += 2

    # ── No triggers → clean exit ─────────────────────────────────────────────
    if not triggers:
        return (
            "None",
            "No Pitru Dosh — Ancestors at Peace",
            "Sun, 9th house, and 9th lord all clear of classical Pitra Dosh patterns.",
            [],
            f"Sun → H{sun_h} | 9L ({L9 or '?'}) → H{L9_h} | Rahu → H{rahu_h} | Ketu → H{ketu_h}",
        )

    # ── Amplifiers ───────────────────────────────────────────────────────────
    amplifiers = []
    if trigger_house == 9:
        amplifiers.append(f"Trigger in 9th house (Pitra Bhava itself)")
        score += 1
    if trigger_house in {6, 8, 12}:
        amplifiers.append(f"Trigger in dusthana H{trigger_house}")
        score += 1
    # 5th-house affliction extension
    fifth_afflicted = []
    for m, h in [("Saturn", sat_h), ("Mars", mars_h), ("Rahu", rahu_h), ("Ketu", ketu_h)]:
        if h == 5:
            fifth_afflicted.append(f"{m} in 5th")
    L5_h = _house(pl, L5) if L5 else 0
    if L5 and L5_h in {6, 8, 12}:
        fifth_afflicted.append(f"5L ({L5}) in dusthana H{L5_h}")
    if fifth_afflicted:
        amplifiers.append(f"5th house afflicted ({', '.join(fifth_afflicted)}) — curse extends to progeny")
        score += 1

    # ── Bhangas ──────────────────────────────────────────────────────────────
    bhangas = []
    # B1: Jupiter aspects 9th OR 9L's house
    jup_targets = []
    if jup_h and _jupiter_aspects_house(jup_h, 9):
        jup_targets.append("9th house")
    if jup_h and L9_h and _jupiter_aspects_house(jup_h, L9_h):
        jup_targets.append(f"9L ({L9}, H{L9_h})")
    if jup_targets:
        bhangas.append(f"Jupiter (H{jup_h}) drishti on {' & '.join(jup_targets)} (Guru shield)")
        score -= 1
    # B2: 9L exalted or own
    if L9:
        L9_obj = _planet_obj(pl, L9)
        L9_sign = _sign_idx(L9_obj)
        if L9_sign and (L9_sign == EXALT_SIGN.get(L9) or L9_sign in OWN_SIGNS.get(L9, set())):
            note = "exalted" if L9_sign == EXALT_SIGN.get(L9) else "own sign"
            bhangas.append(f"9L ({L9}) {note} ({L9_sign}) — paternal dharma intrinsically strong")
            score -= 1
    # B3: Sun own (Leo=5) or exalted (Aries=1)
    sun_obj = _planet_obj(pl, "Sun")
    sun_sign = _sign_idx(sun_obj)
    if sun_sign == 5 or sun_sign == 1:
        note = "exalted (Aries)" if sun_sign == 1 else "own (Leo)"
        bhangas.append(f"Sun {note} — father karaka strong")
        score -= 1
    # B4: 5L strong + Jupiter strong
    if L5 and _is_strong(pl, L5) and _is_strong(pl, "Jupiter"):
        bhangas.append(f"5L ({L5}) strong + Jupiter strong (progeny + dharma intact)")
        score -= 1
    # B5: 9L in kendra/trikona
    KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}
    if L9 and L9_h in KENDRA_TRIKONA:
        bhangas.append(f"9L ({L9}) in kendra/trikona H{L9_h} — ancestor blessings active")
        score -= 1

    n_bhng = len(bhangas)

    note_parts = ["Triggers: " + " | ".join(triggers)]
    if amplifiers:
        note_parts.append("Amplifiers: " + " | ".join(amplifiers))
    if bhangas:
        note_parts.append("Bhanga: " + " | ".join(bhangas))
    note_parts.append(f"Score={score}")
    planet_note = " || ".join(note_parts)

    common_remedies = [
        "Perform Pitru Tarpan on every Amavasya (new moon)",
        "Observe Pitru Paksha (16-day Mahalaya period) — Shraddh ceremony at Gaya/Trimbakeshwar/Haridwar",
        "Feed crows (पितृ-दूत) on every Amavasya with rice + curd + ghee",
        "Donate food and clothing to brahmins on Amavasya",
        "Chant Sun mantra at sunrise: 'Om Ghrini Suryaya Namah' 108×",
        "Offer water to Peepal tree every Saturday morning",
        "Recite Vishnu Sahasranama and Garuda Puran during Pitru Paksha",
    ]

    if n_bhng >= 2:
        return (
            "None",
            "Pitru Dosh Triggers Cancelled by Bhanga",
            f"{len(triggers)} Pitru trigger(s) detected but neutralised by {n_bhng} cancellation factor(s) — Jupiter blessings / 9L strength / strong father karaka shield the lineage axis.",
            [],
            planet_note,
        )
    if score >= 4:
        return (
            "Active",
            f"Pitru Dosh Active (Score {score}) — Ancestral Karma Pattern",
            "Strong classical Pitra Dosh — paternal lineage karma demanding attention. May manifest as childbirth obstacles, father-relationship friction, recurring family disharmony, or sudden financial reversals during Sun/Rahu/Ketu/9L dasha.",
            common_remedies,
            planet_note,
        )
    if score >= 1:
        return (
            "Mild",
            f"Mild Pitru Dosh (Score {score})",
            "Partial Pitra Dosh pattern. Periodic ancestor-related issues; manageable with consistent Pitra remedies.",
            common_remedies[:3],
            planet_note,
        )
    return (
        "None",
        "Pitru Dosh Triggers Neutralised",
        "Pitru triggers present but neutralised by bhanga / lack of amplification.",
        [],
        planet_note,
    )


# ── 4. Guru Chandal Dosh ──────────────────────────────────────────────────────
def _guru_chandal(pl):
    jup_h  = _house(pl, "Jupiter")
    rahu_h = _house(pl, "Rahu")
    ketu_h = _house(pl, "Ketu")

    # Strict-classical (per user): only Jupiter–Rahu counts. Ketu fully excluded.
    # Binary Active/None. Two valid triggers:
    #   (a) Same house  → conjunction
    #   (b) Rahu in 7th house from Jupiter → mutual aspect via Jupiter's 7th drishti
    # No 5th/9th nodal aspects, no Jupiter–Ketu pairing.
    opp_of_jup = (jup_h + 5) % 12 + 1   # 7th house from Jupiter

    if jup_h == rahu_h:
        return (
            "Active",
            f"Jupiter–Rahu Conjunction in House {jup_h} — Guru Chandal Dosh",
            "Guru Chandal Dosh forms when Jupiter (Guru) conjuncts Rahu (Chandal) in the same house. Pollutes wisdom, attracts misleading teachers, and causes ethical confusion in major decisions.",
            [
                "Recite Guru Beej mantra: Om Gram Greem Graum Sah Gurave Namah 108×",
                "Donate yellow cloth and chana dal on Thursdays",
                "Perform Jupiter Shanti Pooja at a Vishnu temple",
                "Feed cows with jaggery on Thursdays",
                "Avoid making major decisions during Jupiter–Rahu periods",
            ],
            f"Jupiter → House {jup_h} | Rahu → House {rahu_h} (same house)",
        )
    if rahu_h == opp_of_jup:
        return (
            "Active",
            f"Rahu Opposite Jupiter (H{jup_h} ↔ H{rahu_h}) — Guru Chandal Dosh",
            "Jupiter and Rahu sit exactly opposite (7th from each other). Jupiter's 7th aspect on Rahu creates a mutual affliction, polluting wisdom and dharmic clarity.",
            [
                "Recite Guru Beej mantra: Om Gram Greem Graum Sah Gurave Namah 108×",
                "Donate yellow cloth and chana dal on Thursdays",
                "Perform Jupiter Shanti Pooja at a Vishnu temple",
                "Feed cows with jaggery on Thursdays",
                "Avoid making major decisions during Jupiter–Rahu periods",
            ],
            f"Jupiter → House {jup_h} | Rahu → House {rahu_h} (7th from Jupiter)",
        )
    return (
        "None",
        "No Guru Chandal Dosh — Jupiter Unafflicted",
        "Jupiter is neither conjunct nor opposite Rahu. Wisdom and dharma are clear and unobstructed.",
        [],
        f"Jupiter → House {jup_h} | Rahu → House {rahu_h}",
    )


# ── 5. Grahan Dosh ────────────────────────────────────────────────────────────
def _grahan(pl):
    sun_h  = _house(pl, "Sun")
    moon_h = _house(pl, "Moon")
    rahu_h = _house(pl, "Rahu")
    ketu_h = _house(pl, "Ketu")

    sun_lon  = _lon(pl, "Sun")
    moon_lon = _lon(pl, "Moon")
    rahu_lon = _lon(pl, "Rahu")
    ketu_lon = _lon(pl, "Ketu")

    solar = sun_h in (rahu_h, ketu_h)
    lunar = moon_h in (rahu_h, ketu_h)
    solar_tight = _orb(sun_lon, rahu_lon) < 10 or _orb(sun_lon, ketu_lon) < 10
    lunar_tight = _orb(moon_lon, rahu_lon) < 10 or _orb(moon_lon, ketu_lon) < 10

    if solar and lunar:
        return (
            "Active",
            "Sun & Moon Both with Rahu/Ketu — Strongest Grahan Dosh",
            "Both luminaries are eclipsed by nodal influence. The strongest form of Grahan Dosh, affecting health, mind, vitality, and life purpose simultaneously.",
            [
                "Perform Surya and Chandra Grahan Shanti Pooja",
                "Offer water to the Sun daily at sunrise",
                "Chant Maha Mrityunjaya mantra 108 times daily",
                "Donate copper on Sundays and silver on Mondays",
            ],
            f"Sun → H{sun_h} | Moon → H{moon_h} | Rahu → H{rahu_h} | Ketu → H{ketu_h}",
        )
    if solar:
        node = "Rahu" if sun_h == rahu_h else "Ketu"
        return (
            "Active",
            f"Sun–{node} Conjunction — Solar Grahan Dosh",
            f"Sun is conjunct {node}, creating Solar Grahan Dosh. Affects authority, father, self-confidence, and vitality.",
            [
                "Offer Arghya (water) to Sun at sunrise daily",
                "Donate copper items on Sundays",
                "Chant Aditya Hridayam",
            ],
            f"Sun → H{sun_h} | {node} → H{rahu_h if node == 'Rahu' else ketu_h}",
        )
    if lunar:
        node = "Rahu" if moon_h == rahu_h else "Ketu"
        return (
            "Active",
            f"Moon–{node} Conjunction — Lunar Grahan Dosh",
            f"Moon is conjunct {node}, creating Lunar Grahan Dosh. Affects mind, mother, emotions, and mental stability.",
            [
                "Offer white flowers to Moon idol on Purnima",
                "Donate silver items on Mondays",
                "Chant Chandra Kavach stotram",
            ],
            f"Moon → H{moon_h} | {node} → H{rahu_h if node == 'Rahu' else ketu_h}",
        )
    if solar_tight or lunar_tight:
        return (
            "Mild",
            "Luminary Close to Node — Mild Grahan Dosh",
            "Sun or Moon is within 10 degrees of a node. Mild eclipse effects on mind or vitality possible.",
            ["Perform regular Navagraha puja monthly"],
            f"Sun → H{sun_h} | Moon → H{moon_h}",
        )
    return (
        "None",
        "No Grahan Dosh — Luminaries Clear",
        "Sun and Moon are free from Rahu/Ketu nodal affliction. No Grahan Dosh present.",
        [],
        f"Sun → H{sun_h} | Moon → H{moon_h}",
    )


# ── 6. Daridra Dosh ───────────────────────────────────────────────────────────
def _daridra(pl):
    """
    Strict-classical Daridra Yog (Brihat Parashara, Phaladeepika, Saravali).
    Six classical triggers + four classical bhanga (cancellation) rules.
    Tier:
      - None  → 0 triggers, OR triggers ≤ bhanga count and bhanga ≥ 2 (strong cancellation)
      - Mild  → 1 trigger and 0 bhanga, OR 2+ triggers with 1 bhanga (partial cancel)
      - Active → 2+ triggers and 0 bhanga
    """
    asc = _asc_sign(pl)
    if not asc:
        return (
            "None",
            "No Daridra Dosh — Ascendant Data Unavailable",
            "Cannot evaluate Daridra without ascendant sign.",
            [],
            "Insufficient sign/house data for lord-based rules.",
        )

    DUSTHANA = {6, 8, 12}
    KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}
    MALEFICS = {"Saturn", "Mars", "Rahu"}

    L1  = _house_lord(asc, 1)    # Lagnesh
    L2  = _house_lord(asc, 2)    # Dhanesh (wealth lord)
    L11 = _house_lord(asc, 11)   # Labhesh (gains lord)

    L1_h  = _house(pl, L1)  if L1  else 0
    L2_h  = _house(pl, L2)  if L2  else 0
    L11_h = _house(pl, L11) if L11 else 0

    moon_h = _house(pl, "Moon")
    mars_h = _house(pl, "Mars")
    sat_h  = _house(pl, "Saturn")
    jup_h  = _house(pl, "Jupiter")

    triggers = []

    # ── Trigger 1: Dhanesh (2L) in 6/8/12 ─────────────────────────────────────
    if L2_h in DUSTHANA:
        triggers.append(f"Dhanesh ({L2}) in dusthana H{L2_h}")

    # ── Trigger 2: Labhesh (11L) in 6/8/12 ────────────────────────────────────
    if L11_h in DUSTHANA:
        triggers.append(f"Labhesh ({L11}) in dusthana H{L11_h}")

    # ── Trigger 3: Dhanesh OR Labhesh conjunct with malefic (Saturn/Mars/Rahu)
    if L2_h:
        afflict_2 = [m for m in MALEFICS if m != L2 and _house(pl, m) == L2_h]
        if afflict_2:
            triggers.append(f"Dhanesh ({L2}@H{L2_h}) afflicted by {'/'.join(afflict_2)}")
    if L11_h:
        afflict_11 = [m for m in MALEFICS if m != L11 and _house(pl, m) == L11_h]
        if afflict_11:
            triggers.append(f"Labhesh ({L11}@H{L11_h}) afflicted by {'/'.join(afflict_11)}")

    # ── Trigger 4: Lagnesh (1L) in 6/8/12 (weak self / weak earning capacity) ──
    if L1_h in DUSTHANA:
        triggers.append(f"Lagnesh ({L1}) in dusthana H{L1_h}")

    # ── Trigger 5: Chandra-Mangal Shashtashtak (Moon-Mars in 6/8 from each other)
    if moon_h and mars_h:
        mars_from_moon = ((mars_h - moon_h) % 12) + 1   # 1=same house
        if mars_from_moon in (6, 8):
            triggers.append(f"Chandra-Mangal Shashtashtak (Moon H{moon_h} ↔ Mars H{mars_h})")

    # ── Trigger 6: Saturn + Moon both in 2nd house (Punarphoo-style dhana drain)
    if sat_h == 2 and moon_h == 2:
        triggers.append("Saturn–Moon conjunct in 2nd house (savings drained)")

    # ── Bhanga 1: Dhanesh (2L) exalted or in own sign ────────────────────────
    bhanga = []
    L2_obj = _planet_obj(pl, L2)
    L2_sign = _sign_idx(L2_obj)
    if L2 and L2_sign:
        if L2_sign == EXALT_SIGN.get(L2):
            bhanga.append(f"Dhanesh ({L2}) exalted")
        elif L2_sign in OWN_SIGNS.get(L2, set()):
            bhanga.append(f"Dhanesh ({L2}) in own sign")

    # ── Bhanga 2: Jupiter aspects 2nd OR 11th house (5th/7th/9th drishti) ────
    if jup_h:
        jup_aspects = {
            (jup_h + 3) % 12 + 1,   # 5th aspect
            (jup_h + 5) % 12 + 1,   # 7th aspect
            (jup_h + 7) % 12 + 1,   # 9th aspect
        }
        protected = [str(h) for h in (2, 11) if h in jup_aspects]
        if protected:
            bhanga.append(f"Jupiter (H{jup_h}) aspects H{'/H'.join(protected)}")

    # ── Bhanga 3: Dhana Yoga — 2L & 11L conjunct in kendra/trikona, OR parivartan
    if L2 and L11 and L2_h and L11_h:
        if L2_h == L11_h and L2_h in KENDRA_TRIKONA:
            bhanga.append(f"Dhana Yoga: {L2} & {L11} conjunct in H{L2_h}")
        else:
            sign_of_2nd  = ((asc - 1 + 1)  % 12) + 1
            sign_of_11th = ((asc - 1 + 10) % 12) + 1
            L11_obj = _planet_obj(pl, L11)
            L11_sign = _sign_idx(L11_obj)
            if L2_sign == sign_of_11th and L11_sign == sign_of_2nd:
                bhanga.append(f"Dhana Parivartan ({L2} ↔ {L11} sign exchange)")

    # ── Bhanga 4: Lagnesh strong + Venus strong (Lakshmi-rakshak combo) ──────
    def _is_strong(planet: str) -> bool:
        if not planet:
            return False
        ph = _house(pl, planet)
        p_obj = _planet_obj(pl, planet)
        p_sign = _sign_idx(p_obj)
        return (
            (ph in KENDRA_TRIKONA)
            or (p_sign and p_sign == EXALT_SIGN.get(planet))
            or (p_sign in OWN_SIGNS.get(planet, set()))
        )
    if _is_strong(L1) and _is_strong("Venus"):
        bhanga.append(f"Lagnesh ({L1}) strong + Venus strong (Lakshmi-rakshak)")

    # ── Tier decision ────────────────────────────────────────────────────────
    n_trig = len(triggers)
    n_bhng = len(bhanga)

    common_remedies = [
        "Recite Shri Suktam daily (Goddess Lakshmi)",
        "Worship Goddess Lakshmi on Fridays with Kanakdhara Stotra",
        "Donate yellow / food items on Thursdays",
        "Light a ghee lamp at home puja every Friday evening",
        "Keep a Sri Yantra or Kubera Yantra at home",
    ]

    note_parts = []
    if triggers:
        note_parts.append("Triggers: " + " | ".join(triggers))
    if bhanga:
        note_parts.append("Bhanga: " + " | ".join(bhanga))
    if not triggers:
        note_parts.append(
            f"Lagnesh={L1}@H{L1_h} | Dhanesh={L2}@H{L2_h} | Labhesh={L11}@H{L11_h}"
        )
    planet_note = " || ".join(note_parts)

    if n_trig == 0:
        return (
            "None",
            "No Daridra Dosh — Wealth Indicators Favorable",
            "No classical Daridra trigger fires. Wealth and gain indicators are clear.",
            [],
            planet_note,
        )
    if n_bhng >= 2:
        return (
            "None",
            "Daridra Triggers Cancelled by Bhanga",
            f"{n_trig} Daridra trigger(s) detected but neutralised by {n_bhng} cancellation factor(s) — Lakshmi-yog / Dhana-yog / Jupiter-aspect protect the wealth axis.",
            [],
            planet_note,
        )
    if n_trig >= 2 and n_bhng == 0:
        return (
            "Active",
            f"Daridra Dosh Active — {n_trig} Classical Triggers",
            "Multiple wealth-house afflictions detected. Income may not stabilise; expect financial drain, debt cycles, or savings erosion.",
            common_remedies,
            planet_note,
        )
    return (
        "Mild",
        f"Mild Daridra — {n_trig} Trigger / {n_bhng} Bhanga",
        "Partial wealth-house affliction detected. Periodic financial obstacles possible but remediable with consistent Lakshmi sadhana.",
        common_remedies[:2],
        planet_note,
    )


# ── 7. Angarak Dosh ───────────────────────────────────────────────────────────
def _angarak(pl):
    mars_h   = _house(pl, "Mars")
    rahu_h   = _house(pl, "Rahu")
    mars_lon = _lon(pl, "Mars")
    rahu_lon = _lon(pl, "Rahu")

    if mars_h == rahu_h:
        tight = _orb(mars_lon, rahu_lon) < 10
        status = "Active" if tight else "Mild"
        label  = "Exact" if tight else "Wide"
        return (
            status,
            f"Mars–Rahu Conjunction ({label}) in House {mars_h} — Angarak Dosh",
            "Angarak Dosh forms when Mars and Rahu occupy the same house. Creates explosive energy, risk of accidents, uncontrolled anger, and sudden violent or shocking events.",
            [
                "Recite Hanuman Chalisa daily without fail",
                "Donate red cloth and red lentils on Tuesdays",
                "Wear Red Coral (Moonga) only after Jyotish consultation",
                "Avoid starting important work on Tuesdays",
                "Avoid high-risk activities (driving at night, dangerous sports)",
            ],
            f"Mars → H{mars_h} | Rahu → H{rahu_h}",
        )
    if _orb(mars_lon, rahu_lon) < 30:
        return (
            "Mild",
            "Mars–Rahu Near Conjunction — Mild Angarak Dosh",
            "Mars and Rahu are within 30 degrees. Mild Angarak effects: irritability, impulsive decisions, and minor accidents possible.",
            [
                "Practice patience and mindfulness daily",
                "Worship Lord Hanuman on Saturdays",
            ],
            f"Mars → H{mars_h} | Rahu → H{rahu_h}",
        )
    return (
        "None",
        "No Angarak Dosh — Mars–Rahu Well Separated",
        "Mars and Rahu are in separate positions with sufficient distance. No Angarak Dosh.",
        [],
        f"Mars → H{mars_h} | Rahu → H{rahu_h}",
    )


# ── 8. Shrapit Dosh ───────────────────────────────────────────────────────────
# Classical Shrapit Yog (curse-yog) — Lal Kitab + nadi tradition + BPHS peripheral.
# Triggers (severity-weighted):
#   Hard T1: Sat + Rahu same house (conjunction)               score +3
#   Hard T2: Sat aspects Rahu via 3rd/7th/10th drishti          score +2
#   Soft T3: Sat + Ketu same house (secondary form)             score +1
# House amplifiers (apply to the trigger-house, max one per category):
#   A1: trigger-house in dusthana 6/8/12                        score +1
#   A2: trigger-house in karmic 1/5/9 (ancestor curse)          score +1
#   A3: trigger-house in 2/7   (family / marriage curse)        score +1
# Bhangas (cancellation):
#   B1: Jupiter 5/7/9 drishti on Saturn OR Rahu                 score -1
#   B2: Saturn in own sign (Cap/Aqu) OR Rahu in friendly sign   score -1
#   B3: 9th lord strong + Jupiter strong                        score -1
# Tier (after no-trigger short-circuit):
#   ≥2 bhanga → forced None (strong cancellation)
#   score ≥ 3 → Active ; 1..2 → Mild ; ≤ 0 → None
def _shrapit(pl):
    sat_h  = _house(pl, "Saturn")
    rahu_h = _house(pl, "Rahu")
    ketu_h = _house(pl, "Ketu")
    jup_h  = _house(pl, "Jupiter")

    triggers = []
    score = 0
    trigger_house = 0

    # ── Hard T1: Sat–Rahu conjunction ─────────────────────────────────────────
    if sat_h and sat_h == rahu_h:
        triggers.append(f"Sat–Rahu Conjunction in H{sat_h}")
        trigger_house = sat_h
        score += 3
    # ── Hard T2: Sat aspects Rahu (only if no conjunction already) ────────────
    elif _saturn_aspects_house(sat_h, rahu_h):
        triggers.append(f"Saturn (H{sat_h}) drishti on Rahu (H{rahu_h})")
        trigger_house = rahu_h
        score += 2

    # ── Soft T3: Sat–Ketu conjunction (independent secondary form) ────────────
    if sat_h and sat_h == ketu_h:
        triggers.append(f"Sat–Ketu Conjunction in H{sat_h} (secondary)")
        if not trigger_house:
            trigger_house = sat_h
        score += 1

    # No trigger fired → clean result, skip the rest
    if not triggers:
        return (
            "None",
            "No Shrapit Dosh — Saturn–Rahu/Ketu Separated",
            "Saturn does not conjunct or aspect Rahu, and is not conjunct Ketu. No Shrapit pattern present.",
            [],
            f"Saturn → H{sat_h} | Rahu → H{rahu_h} | Ketu → H{ketu_h}",
        )

    # ── House amplifiers (only on the primary trigger-house) ──────────────────
    amplifiers = []
    if trigger_house in {6, 8, 12}:
        amplifiers.append(f"Dusthana amplification (H{trigger_house})")
        score += 1
    if trigger_house in {1, 5, 9}:
        amplifiers.append(f"Karmic-house amplification (H{trigger_house}, ancestor curse)")
        score += 1
    if trigger_house in {2, 7}:
        amplifiers.append(f"Family/marriage amplification (H{trigger_house})")
        score += 1

    # ── Bhanga 1: Jupiter aspects Saturn or Rahu ──────────────────────────────
    bhangas = []
    jup_targets = []
    if jup_h and sat_h and _jupiter_aspects_house(jup_h, sat_h):
        jup_targets.append(f"Saturn(H{sat_h})")
    if jup_h and rahu_h and _jupiter_aspects_house(jup_h, rahu_h):
        jup_targets.append(f"Rahu(H{rahu_h})")
    if jup_targets:
        bhangas.append(f"Jupiter (H{jup_h}) drishti on {' & '.join(jup_targets)} (karmic shield)")
        score -= 1

    # ── Bhanga 2: Saturn in own sign OR Rahu in friendly sign ────────────────
    sat_obj = _planet_obj(pl, "Saturn")
    rahu_obj = _planet_obj(pl, "Rahu")
    sat_sign = _sign_idx(sat_obj)
    rahu_sign = _sign_idx(rahu_obj)
    RAHU_FRIENDLY = {2, 3, 6, 7, 11}   # Taurus, Gemini, Virgo, Libra, Aquarius
    dignity_notes = []
    if sat_sign in OWN_SIGNS.get("Saturn", set()):
        dignity_notes.append(f"Saturn own sign ({sat_sign})")
    if rahu_sign in RAHU_FRIENDLY:
        dignity_notes.append(f"Rahu friendly sign ({rahu_sign})")
    if dignity_notes:
        bhangas.append(f"Dignity bhanga: {' + '.join(dignity_notes)}")
        score -= 1

    # ── Bhanga 3: 9th lord strong AND Jupiter strong (ancestor blessings) ────
    asc = _asc_sign(pl)
    if asc:
        L9 = _house_lord(asc, 9)
        if L9 and _is_strong(pl, L9) and _is_strong(pl, "Jupiter"):
            bhangas.append(f"9th lord ({L9}) strong + Jupiter strong (ancestor blessings)")
            score -= 1

    # ── Tier decision ────────────────────────────────────────────────────────
    n_bhng = len(bhangas)

    note_parts = ["Triggers: " + " | ".join(triggers)]
    if amplifiers:
        note_parts.append("Amplifiers: " + " | ".join(amplifiers))
    if bhangas:
        note_parts.append("Bhanga: " + " | ".join(bhangas))
    note_parts.append(f"Score={score}")
    planet_note = " || ".join(note_parts)

    common_remedies = [
        "Perform Shrapit Dosh Nivaran Pooja at Trimbakeshwar / Kalahasti",
        "Chant Shani Chalisa every Saturday",
        "Donate black sesame, black cloth, and mustard oil on Saturdays",
        "Feed crows black sesame and rice every Saturday",
        "Recite Navagraha mantra and perform havan on Saturdays",
    ]

    # ≥2 bhanga forced cancellation
    if n_bhng >= 2:
        return (
            "None",
            "Shrapit Triggers Cancelled by Bhanga",
            f"{len(triggers)} Shrapit trigger(s) detected but neutralised by {n_bhng} cancellation factor(s) — Jupiter/dignity/ancestor blessings shield the karmic axis.",
            [],
            planet_note,
        )
    if score >= 3:
        return (
            "Active",
            f"Shrapit Dosh Active (Score {score}) — Karmic Curse Pattern",
            "Saturn–Rahu (or Saturn–Ketu) creates a strong karmic-curse pattern. Sudden unexplained losses, repeating obstacles, ancestor displeasure, and persistent bad luck — peaks during Saturn / Rahu dasha.",
            common_remedies,
            planet_note,
        )
    if score >= 1:
        return (
            "Mild",
            f"Mild Shrapit Dosh (Score {score})",
            "Partial Shrapit pattern. Periodic karmic obstacles or ancestor-related issues; manageable with consistent Saturn/ancestor remedies.",
            common_remedies[:2],
            planet_note,
        )
    return (
        "None",
        "Shrapit Triggers Neutralised",
        "Shrapit triggers present but neutralised by bhanga / lack of amplification.",
        [],
        planet_note,
    )


# ── 9. Kemadruma Dosh ─────────────────────────────────────────────────────────
def _kemadruma(pl):
    moon_h = _house(pl, "Moon")
    prev_h = (moon_h - 2) % 12 + 1   # 12th from Moon
    next_h = moon_h % 12 + 1          # 2nd from Moon

    # BPHS Ch.8 V.51-52 (literal): ANY graha except Moon itself in 2nd/12th
    # from Moon (or with Moon) cancels Kemadruma. Modern standard (KN Rao,
    # BV Raman, Hart de Fouw) includes Sun + Rahu + Ketu as cancellers.
    cancellers = {"Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"}

    def _planets_in(h):
        return [p.get("name") for p in pl
                if p.get("name") in cancellers and int(p.get("house", 0)) == h]

    prev_planets = _planets_in(prev_h)
    next_planets = _planets_in(next_h)
    moon_companions = _planets_in(moon_h)

    prev_has = bool(prev_planets)
    next_has = bool(next_planets)
    moon_companion = bool(moon_companions)

    def _fmt(h, planets):
        return f"H{h}: {', '.join(planets) if planets else 'empty'}"

    # Strict BPHS Bhanga rule: even ONE graha (other than Moon) in 2nd/12th
    # from Moon, OR conjunct Moon, fully cancels Kemadruma. No Mild tier.
    if not prev_has and not next_has and not moon_companion:
        return (
            "Active",
            f"Moon Isolated in House {moon_h} — Kemadruma Dosh",
            "Kemadruma Dosh forms when no planets occupy houses adjacent to Moon (2nd and 12th) and no planet sits with Moon. Creates emotional isolation, mental vulnerability, and a feeling of being unsupported.",
            [
                "Worship Lord Shiva on every Monday",
                "Wear Pearl (Moti) after Jyotish consultation",
                "Chant Chandra mantra: Om Shram Shreem Shraum Sah Chandraya Namah 108×",
                "Keep white flowers or jasmine at home to strengthen Moon",
                "Maintain close, nurturing relationships with family",
            ],
            f"Moon → H{moon_h} | {_fmt(prev_h, prev_planets)} (12th) | {_fmt(next_h, next_planets)} (2nd)",
        )
    return (
        "None",
        "No Kemadruma Dosh — Moon Supported (Bhanga)",
        "At least one graha sits in 2nd/12th from Moon or conjunct Moon. Per classical Bhanga rule (BPHS Ch.8), Kemadruma Dosh is fully cancelled.",
        [],
        f"Moon → H{moon_h} | {_fmt(prev_h, prev_planets)} (12th) | {_fmt(next_h, next_planets)} (2nd)",
    )


# ── 10. Vish Yoga ──────────────────────────────────────────────────────────────
def _vish_yoga(pl):
    sat_h    = _house(pl, "Saturn")
    moon_h   = _house(pl, "Moon")
    sat_lon  = _lon(pl, "Saturn")
    moon_lon = _lon(pl, "Moon")

    if sat_h == moon_h and sat_h != 0:
        tight = _orb(sat_lon, moon_lon) < 10
        status = "Active" if tight else "Mild"
        return (
            status,
            f"Saturn–Moon Conjunction in House {sat_h} — Vish Yoga",
            "Vish Yoga (literally 'poison combination') forms when Saturn conjuncts Moon, infusing the mind with heaviness. Causes chronic worry, depression, mental fatigue, and emotional poison that lingers — especially during Saturn or Moon dasha periods.",
            [
                "Chant Mahamrityunjay mantra 108 times daily",
                "Wear Pearl (Moti) after Jyotish consultation to strengthen Moon",
                "Worship Lord Shiva on every Monday with milk abhishekam",
                "Donate white items (rice, sugar, milk) on Mondays",
                "Practice 10 minutes of breathing meditation daily",
            ],
            f"Saturn → H{sat_h} | Moon → H{moon_h}",
        )
    if sat_h != 0 and _saturn_aspects_house(sat_h, moon_h):
        return (
            "Mild",
            f"Saturn Aspects Moon (H{moon_h}) — Mild Vish Yoga",
            "Saturn's aspect on Moon creates emotional dampness, periods of low mood, and a tendency toward overthinking. Manageable with consistent practice.",
            [
                "Maintain a regular sleep schedule (Moon thrives on routine)",
                "Avoid heavy decisions during emotionally low phases",
                "Chant 'Om Namah Shivaya' 108 times before sleep",
            ],
            f"Saturn → H{sat_h} (aspects H{moon_h}) | Moon → H{moon_h}",
        )
    return (
        "None",
        "No Vish Yoga — Mind Free of Saturnine Heaviness",
        "Saturn and Moon are not in conjunction or aspect. Mental clarity is unobstructed.",
        [],
        f"Saturn → H{sat_h} | Moon → H{moon_h}",
    )


# ── 11. Sakat Yoga ─────────────────────────────────────────────────────────────
def _sakat_yoga(pl):
    """Classical Shakata Yoga — Moon in 6th, 8th, or 12th from Jupiter (or vice versa).
    Per Brihat Parashara Hora Shastra; matches repo's classical_yogas convention.
    """
    moon_h = _house(pl, "Moon")
    jup_h  = _house(pl, "Jupiter")
    if moon_h == 0 or jup_h == 0:
        return ("None", "Insufficient data", "", [], "")

    # Vedic count: Moon's nth-position from Jupiter = ((moon_h - jup_h) % 12) + 1
    # Classical Shakata: Moon in 6th/8th/12th FROM Jupiter (single direction per Brihat Parashara
    # and repo's classical_yogas.py convention).
    moon_from_jup = ((moon_h - jup_h) % 12) + 1
    classical_positions = {6, 8, 12}

    if moon_from_jup in classical_positions:
        return (
            "Active",
            f"Moon (H{moon_h}) is {moon_from_jup}th from Jupiter (H{jup_h}) — Sakat Yoga",
            "Sakat Yoga ('cart-wheel yoga') forms when the Moon sits in the 6th, 8th, or 12th house from Jupiter. Wealth comes and goes in cycles — repeated rise-and-fall patterns, financial setbacks despite hard work.",
            [
                "Worship Lord Ganesh every Wednesday and offer modaks",
                "Recite Vishnu Sahasranama on Thursdays",
                "Donate yellow items (turmeric, gram dal, banana) on Thursdays",
                "Keep finances diversified — do not put all wealth in one venture",
                "Strengthen Jupiter via gold or yellow sapphire (after Jyotish consultation)",
            ],
            f"Moon → H{moon_h} ({moon_from_jup}th from Jupiter at H{jup_h})",
        )
    # Mild: Moon adjacent to classical positions (5/7/9/11 from Jupiter) — partial wealth-cycle tendency
    near_positions = {5, 7, 9, 11}
    if moon_from_jup in near_positions:
        return (
            "Mild",
            "Moon — Jupiter Near 6/8/12 Axis — Mild Sakat Tendency",
            "Moon and Jupiter are close to but not exactly in the 6/8/12 position. Mild cycles of gain and loss possible during their dashas.",
            [
                "Practice disciplined savings habits",
                "Recite Vishnu Sahasranama on Thursdays",
            ],
            f"Moon → H{moon_h} | Jupiter → H{jup_h}",
        )
    return (
        "None",
        "No Sakat Yoga — Moon and Jupiter Well Placed",
        "Moon and Jupiter are not in adverse mutual position. Wealth flow is stable.",
        [],
        f"Moon → H{moon_h} | Jupiter → H{jup_h}",
    )


# ── 13. Putra (Santaan) Dosh ───────────────────────────────────────────────────
# Classical Putra Dosh — affliction to progeny (5th house, 5L, Jupiter as Santan Karaka).
# BPHS + Phaladeepika + Saravali tradition.
# Triggers (score-weighted):
#   T1: ≥2 malefics (Sat/Mars/Rah/Ket) in 5th house        +3 (strongest)
#   T2: exactly 1 malefic in 5th house                      +1
#   T3: 5th lord in dusthana 6/8/12                         +2
#   T4: 5th lord combust OR debilitated                     +1
#   T5: Jupiter (Putra Karaka) in dusthana 6/8/12           +2
#   T6: Jupiter combust OR debilitated                      +1
#   T7: Jupiter conjunct Sat/Mars/Rahu/Ketu                 +2
#   T8: 5th lord conjunct Rahu OR Ketu                      +2
#   T9: ≥2 malefics aspecting 5th house                     +2
#   T10: Sun placed in 5th (ego friction with progeny)      +1
# Amplifiers (each +1):
#   A1: BOTH 5L and Jupiter afflicted (double-axis)
#   A2: 9th house also afflicted (lineage extension)
#   A3: 5L specifically in 8th (worst dusthana for putra)
# Bhangas (each -1):
#   B1: Jupiter classically strong (kendra/trikona / exalted / own)
#   B2: 5L exalted OR in own sign
#   B3: 5L in kendra/trikona (1/4/5/7/9/10)
#   B4: Natural benefic (Jupiter/Venus/Mercury) placed in 5th
#   B5: 5L conjunct Jupiter (Guru blesses 5L directly)
# Tier:
#   No triggers  → None
#   ≥2 bhanga    → forced None
#   score ≥ 4    → Active
#   score 1..3   → Mild
#   score ≤ 0    → None
def _putra(pl):
    MALEFICS    = {"Saturn", "Mars", "Rahu", "Ketu"}
    BENEFICS    = {"Jupiter", "Venus", "Mercury"}
    NODES       = {"Rahu", "Ketu"}
    KENDRA_TRIK = {1, 4, 5, 7, 9, 10}

    sat_h  = _house(pl, "Saturn")
    mars_h = _house(pl, "Mars")
    rahu_h = _house(pl, "Rahu")
    ketu_h = _house(pl, "Ketu")
    jup_h  = _house(pl, "Jupiter")
    sun_h  = _house(pl, "Sun")

    asc = _asc_sign(pl)
    L5 = _house_lord(asc, 5) if asc else ""
    L9 = _house_lord(asc, 9) if asc else ""
    L5_h = _house(pl, L5) if L5 else 0

    h5_planets         = _planets_in_house(pl, 5)
    malefics_in_5th    = [p for p in h5_planets if p in MALEFICS]
    benefics_in_5th    = [p for p in h5_planets if p in BENEFICS]

    triggers = []
    score = 0

    # ── T1 / T2: malefics in 5th ─────────────────────────────────────────────
    if len(malefics_in_5th) >= 2:
        triggers.append(f"≥2 malefics in 5th: {', '.join(malefics_in_5th)}")
        score += 3
    elif len(malefics_in_5th) == 1:
        triggers.append(f"{malefics_in_5th[0]} in 5th house")
        score += 1

    # ── T3: 5L in dusthana ───────────────────────────────────────────────────
    if L5 and L5_h in {6, 8, 12}:
        triggers.append(f"5th lord ({L5}) in dusthana H{L5_h}")
        score += 2

    # ── T4: 5L combust or debilitated ────────────────────────────────────────
    L5_afflicted = False
    if L5 and (_is_combust(pl, L5) or _is_debilitated(pl, L5)):
        why = "combust" if _is_combust(pl, L5) else "debilitated"
        triggers.append(f"5th lord ({L5}) {why}")
        score += 1
        L5_afflicted = True

    # ── T5: Jupiter in dusthana ──────────────────────────────────────────────
    jupiter_afflicted = False
    if jup_h in {6, 8, 12}:
        triggers.append(f"Jupiter (Putra Karaka) in dusthana H{jup_h}")
        score += 2
        jupiter_afflicted = True

    # ── T6: Jupiter combust or debilitated ───────────────────────────────────
    if _is_combust(pl, "Jupiter") or _is_debilitated(pl, "Jupiter"):
        why = "combust" if _is_combust(pl, "Jupiter") else "debilitated"
        triggers.append(f"Jupiter {why}")
        score += 1
        jupiter_afflicted = True

    # ── T7: Jupiter conjunct malefic ─────────────────────────────────────────
    jup_conjuncts = [m for m in MALEFICS if m != "Jupiter" and _house(pl, m) == jup_h and jup_h]
    if jup_conjuncts:
        triggers.append(f"Jupiter conjunct {'/'.join(jup_conjuncts)} in H{jup_h}")
        score += 2
        jupiter_afflicted = True

    # ── T8: 5L conjunct node ─────────────────────────────────────────────────
    if L5 and L5 not in NODES:
        node_with_L5 = [n for n in NODES if _house(pl, n) == L5_h and L5_h]
        if node_with_L5:
            triggers.append(f"5th lord ({L5}) conjunct {'/'.join(node_with_L5)} in H{L5_h}")
            score += 2
            L5_afflicted = True

    # ── T9: ≥2 malefics aspecting 5th ────────────────────────────────────────
    aspect_hits = []
    for m, h in [("Saturn", sat_h), ("Mars", mars_h)]:
        if h and h != 5:
            if m == "Saturn" and _saturn_aspects_house(h, 5):
                aspect_hits.append("Saturn drishti on 5th")
            if m == "Mars" and _mars_aspects_house(h, 5):
                aspect_hits.append("Mars drishti on 5th")
    if len(aspect_hits) >= 2:
        triggers.append(f"≥2 malefic drishti on 5th: {', '.join(aspect_hits)}")
        score += 2

    # ── T10: Sun in 5th ──────────────────────────────────────────────────────
    if sun_h == 5:
        triggers.append("Sun in 5th (ego friction with progeny)")
        score += 1

    # ── No triggers → clean exit ─────────────────────────────────────────────
    if not triggers:
        return (
            "None",
            "No Putra Dosh — Children House Strong",
            "5th house, 5th lord, and Jupiter (Putra Karaka) all clear of classical affliction patterns.",
            [],
            f"5th House: {', '.join(h5_planets) or 'Empty'} | 5L ({L5 or '?'}) → H{L5_h} | Jupiter → H{jup_h}",
        )

    # ── Amplifiers ───────────────────────────────────────────────────────────
    amplifiers = []
    if L5_afflicted and jupiter_afflicted:
        amplifiers.append("BOTH 5L and Jupiter afflicted (double-axis)")
        score += 1
    # 9th house also afflicted
    ninth_hits = []
    h9_planets = _planets_in_house(pl, 9)
    malefics_in_9th = [p for p in h9_planets if p in MALEFICS]
    if malefics_in_9th:
        ninth_hits.append(f"malefics in 9th: {', '.join(malefics_in_9th)}")
    L9_h = _house(pl, L9) if L9 else 0
    if L9 and L9_h in {6, 8, 12}:
        ninth_hits.append(f"9L ({L9}) in dusthana H{L9_h}")
    if ninth_hits:
        amplifiers.append(f"9th-axis also weak ({'; '.join(ninth_hits)}) — lineage strain")
        score += 1
    # 5L specifically in 8th
    if L5 and L5_h == 8:
        amplifiers.append(f"5L ({L5}) in 8th specifically (worst dusthana for putra)")
        score += 1

    # ── Bhangas ──────────────────────────────────────────────────────────────
    bhangas = []
    # B1: Jupiter strong
    if _is_strong(pl, "Jupiter") and not jupiter_afflicted:
        bhangas.append(f"Jupiter classically strong in H{jup_h} (Putra Karaka shield)")
        score -= 1
    # B2: 5L exalted/own
    if L5:
        L5_obj = _planet_obj(pl, L5)
        L5_sign = _sign_idx(L5_obj)
        if L5_sign and (L5_sign == EXALT_SIGN.get(L5) or L5_sign in OWN_SIGNS.get(L5, set())):
            note = "exalted" if L5_sign == EXALT_SIGN.get(L5) else "own sign"
            bhangas.append(f"5L ({L5}) {note} ({L5_sign}) — progeny axis intrinsically strong")
            score -= 1
    # B3: 5L in kendra/trikona
    if L5 and L5_h in KENDRA_TRIK and L5_h not in {6, 8, 12}:
        bhangas.append(f"5L ({L5}) in kendra/trikona H{L5_h}")
        score -= 1
    # B4: Benefic in 5th
    if benefics_in_5th:
        bhangas.append(f"Benefic in 5th: {', '.join(benefics_in_5th)} (sanctifies progeny house)")
        score -= 1
    # B5: 5L conjunct Jupiter
    if L5 and L5 != "Jupiter" and L5_h and L5_h == jup_h:
        bhangas.append(f"5L ({L5}) conjunct Jupiter in H{jup_h} — Guru blesses progeny lord")
        score -= 1

    n_bhng = len(bhangas)

    note_parts = ["Triggers: " + " | ".join(triggers)]
    if amplifiers:
        note_parts.append("Amplifiers: " + " | ".join(amplifiers))
    if bhangas:
        note_parts.append("Bhanga: " + " | ".join(bhangas))
    note_parts.append(f"Score={score}")
    planet_note = " || ".join(note_parts)

    common_remedies = [
        "Recite Santan Gopal mantra 108× daily — 'ॐ देवकी सुत गोविन्द वासुदेव जगत्पते। देहि मे तनयं कृष्ण त्वामहं शरणं गत:।।'",
        "Worship Lord Krishna with butter + tulsi offering on Janmashtami and every Ashtami",
        "Strengthen Jupiter — fast on Thursdays, donate yellow items (turmeric, chana dal, banana)",
        "Perform Putra Prapti Pooja at Krishna temple (Mathura/Vrindavan/Udupi most powerful)",
        "Donate to children's charity, orphanage, or sponsor a child's education",
        "Feed cows with jaggery + roti on Thursdays (Jupiter strengthening)",
        "IMPORTANT: Always consult a medical professional for fertility concerns — these remedies supplement, never substitute, medical advice",
    ]

    if n_bhng >= 2:
        return (
            "None",
            "Putra Dosh Triggers Cancelled by Bhanga",
            f"{len(triggers)} progeny-affliction trigger(s) detected but neutralised by {n_bhng} cancellation factor(s) — strong Jupiter / 5L strength / benefic in 5th provide the classical shield.",
            [],
            planet_note,
        )
    if score >= 4:
        return (
            "Active",
            f"Putra Dosh Active (Score {score}) — Children-House Affliction",
            "Strong classical Putra Dosh — significant affliction on the progeny axis (5th house, 5th lord, Jupiter). May manifest as conception delays, pregnancy complications, recurring health issues in children, or strained parent-child bond. Always pair these remedies with proper medical consultation.",
            common_remedies,
            planet_note,
        )
    if score >= 1:
        return (
            "Mild",
            f"Mild Putra Dosh (Score {score})",
            "Partial affliction on the children axis. Periodic progeny-related concerns; manageable with consistent Santan-Gopal practice and Jupiter strengthening. Always consult medical professionals for fertility concerns.",
            common_remedies[:4],
            planet_note,
        )
    return (
        "None",
        "Putra Dosh Triggers Neutralised",
        "Triggers present but neutralised by bhanga / lack of amplification.",
        [],
        planet_note,
    )


# ── 14. Gandanta Dosh ──────────────────────────────────────────────────────────
def _gandanta(pl):
    """Moon at junction of water-fire signs: Pisces→Aries, Cancer→Leo, Scorpio→Sagittarius."""
    if not _has(pl, "Moon"):
        return ("None", "Insufficient data", "", [], "")
    moon_lon = _lon(pl, "Moon")
    sign_idx    = int(moon_lon // 30) + 1
    deg_in_sign = moon_lon % 30
    SIGN_NAMES  = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

    in_water_end  = (sign_idx in (12, 4, 8) and deg_in_sign >= 27)
    in_fire_start = (sign_idx in (1, 5, 9)  and deg_in_sign <= 3)
    pos_str = f"Moon → {SIGN_NAMES[sign_idx-1]} {deg_in_sign:.1f}°"

    if in_water_end or in_fire_start:
        tight = (in_water_end and deg_in_sign >= 29.2) or (in_fire_start and deg_in_sign <= 0.8)
        status = "Active" if tight else "Mild"
        return (
            status,
            "Moon at Sandhi (Junction) — Gandanta Dosh",
            "Gandanta Dosh forms when the Moon falls at the junction of water and fire signs. Indicates an extremely sensitive birth — classically associated with vulnerability in early life and a need for protective rituals. Modern interpretation: heightened emotional sensitivity that, when consciously channelled, becomes deep intuition.",
            [
                "Perform Gandanta Shanti Pooja (within first year of birth, or now if missed)",
                "Recite Mahamrityunjay mantra 108 times daily",
                "Worship Lord Vishnu with tulsi every Thursday",
                "Donate gold or yellow items to a temple",
                "Wear protective Vedic talisman after Jyotish consultation",
            ],
            pos_str,
        )
    return (
        "None",
        "No Gandanta Dosh — Moon in Stable Zone",
        "Moon is not at a sign-junction. No Gandanta sensitivity present.",
        [],
        pos_str,
    )


# ── 15. Punar Phoo Dosh ────────────────────────────────────────────────────────
def _punar_phoo(pl):
    """Classical Punarphoo Dosh per Brihat Parashara Hora Shastra — primarily formed by
    Saturn–Moon affliction (conjunction or 7th-house aspect). Saturn–Venus involvement
    in/aspecting the 7th house extends this to marriage-disruption interpretation in
    modern Vedic practice. Both pathways are evaluated.
    """
    sat_h   = _house(pl, "Saturn")
    moon_h  = _house(pl, "Moon")
    venus_h = _house(pl, "Venus")
    if sat_h == 0 or moon_h == 0:
        return ("None", "Insufficient data", "", [], "")

    # Saturn casts 3rd, 7th, 10th aspects → houses sat_h+2, sat_h+6, sat_h+9 (mod 12, 1-indexed)
    sat_aspects = {((sat_h - 1 + 2) % 12) + 1, ((sat_h - 1 + 6) % 12) + 1, ((sat_h - 1 + 9) % 12) + 1}

    # ── Classical primary: Saturn–Moon affliction ──
    sat_moon_conj   = (sat_h == moon_h)
    sat_aspects_moon = (moon_h in sat_aspects)
    moon_in_7th      = (moon_h == 7)
    sat_in_or_aspects_7th = (sat_h == 7) or (7 in sat_aspects)

    # ── Marriage-extension secondary: Saturn–Venus involving 7th ──
    sat_venus_conj_in_7th = (venus_h != 0 and sat_h == venus_h == 7)
    venus_afflicted       = (venus_h in (6, 8, 12))

    # Active: classical Saturn–Moon conjunction in 7th, OR Saturn–Moon conjunction generally,
    # OR Saturn–Venus conjunction in 7th (modern marriage extension)
    if sat_moon_conj and moon_in_7th:
        return (
            "Active",
            "Saturn–Moon Conjunction in 7th House — Strong Punar Phoo",
            "Saturn and Moon together in the 7th house forms classical Punar Phoo Dosh. Repeated obstacles in partnerships, emotional restraint, and a sense of 'starting over' in close relationships. Demands conscious patience and mature commitment.",
            [
                "Perform Saturn–Moon Shanti Pooja before marriage",
                "Recite Mahamrityunjay mantra 108× daily",
                "Worship Lord Shiva with Parvati every Monday",
                "Donate white sweets and sesame oil on Saturdays",
                "Couples counselling alongside spiritual remedies recommended",
            ],
            f"Saturn → H{sat_h} | Moon → H{moon_h} (conjunction in 7th)",
        )
    if sat_moon_conj or sat_aspects_moon:
        return (
            "Active",
            f"Saturn Afflicts Moon (Saturn H{sat_h}, Moon H{moon_h}) — Punar Phoo",
            "Saturn's conjunction with or aspect on the Moon forms classical Punar Phoo Dosh. Repeated emotional restraints, delays in mental peace, and recurring obstacle patterns through Saturn–Moon dasha periods.",
            [
                "Recite Mahamrityunjay mantra 108× daily",
                "Worship Lord Shiva every Monday with white flowers",
                "Donate sesame, mustard oil, and white cloth on Saturdays",
                "Maintain stable daily routine — Moon thrives on regularity",
                "Avoid major emotional decisions during Saturn transits over natal Moon",
            ],
            f"Saturn → H{sat_h} | Moon → H{moon_h}",
        )
    if sat_venus_conj_in_7th:
        return (
            "Active",
            "Saturn–Venus Conjunction in 7th House — Punar Phoo (Marriage Extension)",
            "Saturn and Venus together in the 7th house, in modern Vedic practice, extends Punar Phoo to marriage matters — separation phases, late marriage, or repeat-marriage indications. Demands extra patience and conscious commitment from both partners.",
            [
                "Perform Saturn–Venus Shanti Pooja before marriage",
                "Donate sugar, white sweets, and silver on Fridays",
                "Worship Lord Shiva with Parvati every Monday",
                "Avoid impulsive separation decisions during Saturn dasha",
                "Couples counselling alongside spiritual remedies recommended",
            ],
            f"Saturn → H{sat_h} | Venus → H{venus_h}",
        )

    # Mild: Saturn influences 7th + Venus afflicted (marriage extension), or Moon in dusthana with Saturn nearby
    if sat_in_or_aspects_7th and venus_afflicted:
        return (
            "Mild",
            "Saturn Influences 7th + Venus in Dusthana — Mild Punar Phoo",
            "Saturn's influence on the 7th house combined with Venus in a dusthana (6/8/12) indicates marriage delays and periods of disconnection. Manageable with mature commitment.",
            [
                "Recite Shukra Beej mantra on Fridays",
                "Practice weekly relationship rituals (gratitude, communication night)",
                "Donate white cloth and sweets on Fridays",
            ],
            f"Saturn → H{sat_h} | Venus → H{venus_h}",
        )
    if moon_h in (6, 8, 12) and (sat_h in (6, 8, 12) or sat_aspects & {6, 8, 12}):
        return (
            "Mild",
            "Saturn–Moon Both Touch Dusthanas — Mild Punar Phoo",
            "Both Saturn and Moon influence dusthana houses (6/8/12), creating mild recurring obstacle patterns. Manageable with consistent spiritual practice.",
            [
                "Recite Mahamrityunjay mantra weekly",
                "Donate white items on Mondays",
            ],
            f"Saturn → H{sat_h} | Moon → H{moon_h}",
        )
    return (
        "None",
        "No Punar Phoo Dosh — Saturn and Moon Stable",
        "Saturn does not afflict the Moon, and the marriage indicators (Venus, 7th house) are clear. No Punar Phoo pattern present.",
        [],
        f"Saturn → H{sat_h} | Moon → H{moon_h} | Venus → H{venus_h}",
    )


# ── Master config ──────────────────────────────────────────────────────────────
DOSH_CONFIGS = [
    ("manglik",        "Manglik Dosh",         "मांगलिक दोष",        "🔴", _manglik),
    ("kaal_sarp",      "Kaal Sarp Dosh",       "कालसर्प दोष",        "🐍", _kaal_sarp),
    ("pitru",          "Pitru Dosh",           "पितृ दोष",            "👣", _pitru),
    ("guru_chandal",   "Guru Chandal Dosh",    "गुरु चांडाल दोष",     "🪐", _guru_chandal),
    ("grahan",         "Grahan Dosh",          "ग्रहण दोष",           "🌑", _grahan),
    ("daridra",        "Daridra Dosh",         "दरिद्र दोष",          "💰", _daridra),
    ("angarak",        "Angarak Dosh",         "अंगारक दोष",          "🔥", _angarak),
    ("shrapit",        "Shrapit Dosh",         "श्रापित दोष",         "⛓",  _shrapit),
    ("kemadruma",      "Kemadruma Dosh",       "केमद्रुम दोष",        "🌙", _kemadruma),
    ("vish_yoga",      "Vish Yoga",            "विष योग",             "🦂", _vish_yoga),
    ("sakat_yoga",     "Sakat Yoga",           "शकट योग",             "🛒", _sakat_yoga),
    ("putra",          "Putra Dosh",           "पुत्र दोष",           "👶", _putra),
    ("gandanta",       "Gandanta Dosh",        "गण्डान्त दोष",        "🌊", _gandanta),
    ("punar_phoo",     "Punar Phoo Dosh",      "पुनः फू दोष",         "💔", _punar_phoo),
]


# ── Main entry point ───────────────────────────────────────────────────────────
def analyze_doshas(planets: list, nakshatra: str = "") -> dict:
    """
    Run full 9-dosh analysis. Cached per unique planet configuration.
    Returns:
      { total_dosh, active_count, mild_count, none_count, dosh_list }
    """
    ck = _cache_key(planets, nakshatra)
    if ck in _dosh_cache:
        return _dosh_cache[ck]

    dosh_list   = []
    active_cnt  = 0
    mild_cnt    = 0

    for dkey, name, name_hindi, icon, fn in DOSH_CONFIGS:
        try:
            status, headline, description, remedies, planet_note = fn(planets)
        except Exception as exc:
            status, headline, description, remedies, planet_note = (
                "None", "Calculation skipped", str(exc), [], ""
            )

        if status == "Active":
            active_cnt += 1
        elif status == "Mild":
            mild_cnt += 1

        dosh_list.append({
            "key":         dkey,
            "name":        name,
            "name_hindi":  name_hindi,
            "icon":        icon,
            "status":      status,
            "headline":    headline,
            "description": description,
            "remedies":    remedies,
            "planet_note": planet_note,
        })

    result = {
        "total_dosh":   active_cnt + mild_cnt,
        "active_count": active_cnt,
        "mild_count":   mild_cnt,
        "none_count":   len(DOSH_CONFIGS) - active_cnt - mild_cnt,
        "dosh_list":    dosh_list,
    }
    _dosh_cache[ck] = result
    return result


def clear_cache():
    """Clear dosh cache (call when birth details change)."""
    _dosh_cache.clear()
