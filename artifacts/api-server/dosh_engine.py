"""
dosh_engine.py — Complete Vedic Dosh Analysis Engine (9 Doshas)
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


def _planets_in_house(pl: list, house: int) -> list:
    return [p["name"] for p in pl if int(p.get("house", 0)) == house]


def _orb(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


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
def _kaal_sarp(pl):
    rahu_lon = _lon(pl, "Rahu")
    rahu_h   = _house(pl, "Rahu")
    ketu_h   = _house(pl, "Ketu")
    core     = [p for p in pl if p.get("name") not in ("Rahu", "Ketu")]
    if not core:
        return ("None", "Insufficient data", "", [], "")

    in_arc = [(_lon(pl, p["name"]) - rahu_lon) % 360 < 180 for p in core]
    all_in = all(in_arc)
    any_in = any(in_arc)

    if all_in:
        return (
            "Active",
            "Full Kaal Sarp Dosh — All Planets in Rahu–Ketu Arc",
            "All planets fall between Rahu and Ketu. This strongest form creates severe obstacles, delays, vivid dreams, sudden reversals, and a feeling of life being restrained.",
            [
                "Perform Kaal Sarp Pooja at Trimbakeshwar, Ujjain, or Nashik",
                "Offer milk to a serpent idol on Nagpanchami",
                "Chant Mahamrityunjay mantra 108 times daily",
                "Offer sesame oil at a Navagraha temple for Rahu",
                "Donate black items (sesame, cloth) on Saturdays for Ketu",
            ],
            f"Rahu → House {rahu_h} | Ketu → House {ketu_h}",
        )
    elif any_in:
        return (
            "Mild",
            "Partial Kaal Sarp — Some Planets Outside Arc",
            "Some planets lie outside the Rahu–Ketu arc. Partial Kaal Sarp creates occasional obstacles, mild delays, and periods of uncertainty.",
            [
                "Chant Rahu Beej mantra: Om Bhram Bhreem Bhraum Sah Rahave Namah",
                "Wear Hessonite (Gomed) after consulting a Jyotishi",
            ],
            f"Rahu → House {rahu_h} | Ketu → House {ketu_h}",
        )
    return (
        "None",
        "No Kaal Sarp Dosh — Planets Spread Freely",
        "Planets are distributed on both sides of the Rahu–Ketu axis. No Kaal Sarp Dosh present.",
        [],
        f"Rahu → House {rahu_h} | Ketu → House {ketu_h}",
    )


# ── 3. Pitru Dosh ─────────────────────────────────────────────────────────────
def _pitru(pl):
    sun_h  = _house(pl, "Sun")
    rahu_h = _house(pl, "Rahu")
    ketu_h = _house(pl, "Ketu")

    if sun_h == rahu_h or sun_h == ketu_h:
        node = "Rahu" if sun_h == rahu_h else "Ketu"
        return (
            "Active",
            f"Sun–{node} Conjunction — Pitru Dosh Present",
            "Pitru Dosh forms when the Sun (significator of father and ancestors) conjuncts Rahu or Ketu. Indicates unresolved ancestral karma that needs healing.",
            [
                "Perform Pitru Tarpan on every Amavasya (new moon)",
                "Donate food and clothing to brahmins on Pitru Paksha",
                "Recite Pitru Stotra daily (108 times)",
                "Feed crows and brahmins on new moon days",
                "Plant a Peepal tree and water it on Saturdays",
            ],
            f"Sun → House {sun_h} | {node} → House {rahu_h if node == 'Rahu' else ketu_h}",
        )
    # Mild: Rahu aspects 9th lord (Sun in 9th or Rahu aspects 9th)
    if sun_h == 9 and rahu_h in (1, 3, 5, 9):
        return (
            "Mild",
            "Sun in 9th House with Rahu Influence — Partial Pitru Dosh",
            "Rahu's influence on the 9th house Sun creates partial ancestral karma requiring attention.",
            ["Perform Pitra Tarpan on important ancestral dates"],
            f"Sun → House {sun_h} | Rahu → House {rahu_h}",
        )
    return (
        "None",
        "No Pitru Dosh — Ancestors at Peace",
        "Sun is free from Rahu/Ketu conjunction. No Pitru Dosh detected in this chart.",
        [],
        f"Sun → House {sun_h} | Rahu → House {rahu_h} | Ketu → House {ketu_h}",
    )


# ── 4. Guru Chandal Dosh ──────────────────────────────────────────────────────
def _guru_chandal(pl):
    jup_h  = _house(pl, "Jupiter")
    rahu_h = _house(pl, "Rahu")
    ketu_h = _house(pl, "Ketu")

    if jup_h == rahu_h:
        return (
            "Active",
            f"Jupiter–Rahu Conjunction in House {jup_h} — Guru Chandal Dosh",
            "Guru Chandal Dosh forms when Jupiter (Guru) conjuncts Rahu (Chandal). Pollutes wisdom, attracts deceitful teachers, and causes ethical confusion in important decisions.",
            [
                "Recite Guru Beej mantra: Om Gram Greem Graum Sah Gurave Namah 108×",
                "Donate yellow cloth and chana dal on Thursdays",
                "Perform Jupiter Shanti Pooja at a Vishnu temple",
                "Feed cows with jaggery on Thursdays",
                "Avoid making major decisions during Jupiter–Rahu periods",
            ],
            f"Jupiter → House {jup_h} | Rahu → House {rahu_h}",
        )
    if jup_h == ketu_h:
        return (
            "Mild",
            f"Jupiter–Ketu Conjunction in House {jup_h} — Mild Guru Chandal",
            "Jupiter with Ketu creates spiritual confusion and detachment from traditional wisdom and dharmic path.",
            [
                "Worship Lord Ganesh on Wednesdays",
                "Donate green cloth or moong dal on Thursdays",
            ],
            f"Jupiter → House {jup_h} | Ketu → House {ketu_h}",
        )
    # Rahu aspects 5th, 7th, 9th from its house
    rahu_aspects = [(rahu_h + 4) % 12 + 1, (rahu_h + 6) % 12 + 1, (rahu_h + 8) % 12 + 1]
    if jup_h in rahu_aspects:
        return (
            "Mild",
            f"Rahu Aspects Jupiter — Partial Guru Chandal",
            "Rahu's special aspect on Jupiter weakens wisdom and may attract misleading guidance.",
            ["Chant Vishnu Sahasranama regularly"],
            f"Jupiter → House {jup_h} | Rahu → House {rahu_h} (aspects H{jup_h})",
        )
    return (
        "None",
        "No Guru Chandal Dosh — Jupiter Unafflicted",
        "Jupiter is free from Rahu/Ketu influence. Wisdom and dharma are clear and unobstructed.",
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
    malefics = {"Saturn", "Mars", "Rahu", "Ketu"}
    h2 = _planets_in_house(pl, 2)
    in_2nd = [p for p in h2 if p in malefics]
    venus_h  = _house(pl, "Venus")
    sat_h    = _house(pl, "Saturn")
    rahu_h   = _house(pl, "Rahu")
    jupiter_h = _house(pl, "Jupiter")

    # Strong: 2+ malefics in 2nd OR Jupiter (natural wealth significator) severely afflicted
    if len(in_2nd) >= 2 or (jupiter_h in (6, 8, 12) and saturn_h in (1, 4, 7)):
        cause = f"2nd House: {', '.join(in_2nd)}" if len(in_2nd) >= 2 else f"Jupiter → H{jupiter_h} + Saturn → H{sat_h}"
        return (
            "Active",
            "Wealth House Severely Afflicted — Daridra Dosh",
            "Multiple malefics in the 2nd house (wealth) or Jupiter severely afflicted creates Daridra Dosh — financial struggles, instability, and obstacles to prosperity.",
            [
                "Recite Shri Suktam daily (linked to Goddess Lakshmi)",
                "Donate food to the needy on Fridays",
                "Keep a Kubera Yantra or Sri Yantra at home",
                "Light a ghee lamp at home puja every Friday evening",
                "Avoid lending money on Saturdays",
            ],
            cause,
        )
    if len(in_2nd) == 1:
        return (
            "Mild",
            f"{in_2nd[0]} in 2nd House — Mild Daridra Dosh",
            f"{in_2nd[0]} in the 2nd house (wealth house) may create periodic financial obstacles and spending instability.",
            [
                "Worship Goddess Lakshmi on Fridays",
                "Recite Kanakdhara Stotra for wealth blessings",
            ],
            f"2nd House: {in_2nd[0]}",
        )
    if venus_h in (6, 8, 12):
        return (
            "Mild",
            f"Venus in Dusthana (House {venus_h}) — Mild Daridra",
            "Venus in a dusthana house (6th, 8th, 12th) creates mild financial constraints and luxury deprivation.",
            ["Keep Ruby or Opal as per Jyotish guidance", "Worship Goddess Lakshmi on Fridays"],
            f"Venus → House {venus_h}",
        )
    return (
        "None",
        "No Daridra Dosh — Wealth Indicators Favorable",
        "No significant malefic affliction on wealth indicators. Financial path appears clear and progressive.",
        [],
        f"2nd House: {', '.join(_planets_in_house(pl, 2)) or 'Empty'} | Venus → H{venus_h}",
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
def _shrapit(pl):
    sat_h    = _house(pl, "Saturn")
    rahu_h   = _house(pl, "Rahu")
    sat_lon  = _lon(pl, "Saturn")
    rahu_lon = _lon(pl, "Rahu")

    if sat_h == rahu_h:
        return (
            "Active",
            f"Saturn–Rahu Conjunction in House {sat_h} — Shrapit Dosh",
            "Shrapit Dosh (cursed birth) forms from Saturn–Rahu conjunction. Signifies past-life curses or unfulfilled karmic debts, causing chronic delays, hardships, relationship obstacles, and persistent bad luck.",
            [
                "Perform Shrapit Dosh Nivaran Pooja at Trimbakeshwar",
                "Chant Shani Chalisa every Saturday",
                "Donate black sesame, black cloth, and mustard oil on Saturdays",
                "Feed crows black sesame and rice every Saturday",
                "Recite Navagraha mantra and perform havan on Saturdays",
            ],
            f"Saturn → H{sat_h} | Rahu → H{rahu_h}",
        )
    # Saturn aspects 3rd, 7th, 10th from its position
    sat_aspects = [(sat_h + 2) % 12 + 1, (sat_h + 6) % 12 + 1, (sat_h + 9) % 12 + 1]
    if rahu_h in sat_aspects:
        return (
            "Mild",
            f"Saturn Aspects Rahu (H{rahu_h}) — Mild Shrapit Dosh",
            "Saturn's aspect on Rahu's house creates mild Shrapit effects — delays, karmic lessons, and periodic hardships.",
            [
                "Offer black sesame to Shani temple on Saturdays",
                "Recite Shani Stotra every Saturday",
            ],
            f"Saturn → H{sat_h} (aspects H{rahu_h}) | Rahu → H{rahu_h}",
        )
    if _orb(sat_lon, rahu_lon) < 30:
        return (
            "Mild",
            "Saturn–Rahu Close Degrees — Mild Shrapit",
            "Saturn and Rahu are within close degrees across houses, creating mild Shrapit karmic debt.",
            ["Practice karma yoga and selfless service (seva)"],
            f"Saturn → H{sat_h} | Rahu → H{rahu_h}",
        )
    return (
        "None",
        "No Shrapit Dosh — Saturn–Rahu Separated",
        "Saturn and Rahu are well-separated in the chart. No Shrapit Dosh present.",
        [],
        f"Saturn → H{sat_h} | Rahu → H{rahu_h}",
    )


# ── 9. Kemadruma Dosh ─────────────────────────────────────────────────────────
def _kemadruma(pl):
    moon_h = _house(pl, "Moon")
    prev_h = (moon_h - 2) % 12 + 1   # 12th from Moon
    next_h = moon_h % 12 + 1          # 2nd from Moon

    # Rahu, Ketu, Sun (upagraha) don't break Kemadruma in classical texts
    benefics = {"Mercury", "Venus", "Jupiter", "Mars", "Saturn"}

    prev_has = any(p.get("name") in benefics and int(p.get("house", 0)) == prev_h for p in pl)
    next_has = any(p.get("name") in benefics and int(p.get("house", 0)) == next_h for p in pl)
    moon_companion = any(
        p.get("name") in benefics and int(p.get("house", 0)) == moon_h for p in pl
    )

    if not prev_has and not next_has and not moon_companion:
        return (
            "Active",
            f"Moon Isolated in House {moon_h} — Kemadruma Dosh",
            "Kemadruma Dosh forms when no planets occupy houses adjacent to Moon (2nd and 12th). Creates profound emotional isolation, mental vulnerability, and a lifelong feeling of being unsupported.",
            [
                "Worship Lord Shiva on every Monday",
                "Wear Pearl (Moti) after Jyotish consultation",
                "Chant Chandra mantra: Om Shram Shreem Shraum Sah Chandraya Namah 108×",
                "Keep white flowers or jasmine at home to strengthen Moon",
                "Maintain close, nurturing relationships with family",
            ],
            f"Moon → H{moon_h} | H{prev_h} (12th): empty | H{next_h} (2nd): empty",
        )
    if not prev_has or not next_has:
        return (
            "Mild",
            f"Moon Partially Isolated — Mild Kemadruma Dosh",
            "One side adjacent to the Moon is empty. Mild Kemadruma effects: occasional emotional isolation and feeling unsupported.",
            [
                "Chant Chandra Beej mantra regularly",
                "Maintain close relationships with loved ones",
            ],
            f"Moon → H{moon_h} | H{prev_h}: {'occupied' if prev_has else 'empty'} | H{next_h}: {'occupied' if next_has else 'empty'}",
        )
    return (
        "None",
        "No Kemadruma Dosh — Moon Well-Supported",
        "Moon has planetary company on both adjacent sides. Emotional and mental support is strong. No Kemadruma Dosh.",
        [],
        f"Moon → H{moon_h} | Adjacent houses occupied",
    )


# ── Master config ──────────────────────────────────────────────────────────────
DOSH_CONFIGS = [
    ("manglik",      "Manglik Dosh",      "मांगलिक दोष",     "🔴", _manglik),
    ("kaal_sarp",    "Kaal Sarp Dosh",    "कालसर्प दोष",     "🐍", _kaal_sarp),
    ("pitru",        "Pitru Dosh",        "पितृ दोष",         "👣", _pitru),
    ("guru_chandal", "Guru Chandal Dosh", "गुरु चांडाल दोष",  "🪐", _guru_chandal),
    ("grahan",       "Grahan Dosh",       "ग्रहण दोष",        "🌑", _grahan),
    ("daridra",      "Daridra Dosh",      "दरिद्र दोष",       "💰", _daridra),
    ("angarak",      "Angarak Dosh",      "अंगारक दोष",       "🔥", _angarak),
    ("shrapit",      "Shrapit Dosh",      "श्रापित दोष",      "⛓", _shrapit),
    ("kemadruma",    "Kemadruma Dosh",    "केमद्रुम दोष",     "🌙", _kemadruma),
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
