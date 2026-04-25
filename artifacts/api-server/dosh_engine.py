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
    if len(in_2nd) >= 2 or (jupiter_h in (6, 8, 12) and sat_h in (1, 4, 7)):
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
    if not prev_has or not next_has:
        return (
            "Mild",
            f"Moon Partially Isolated — Mild Kemadruma Dosh",
            "One side adjacent to the Moon is empty. Mild Kemadruma effects: occasional emotional isolation and feeling unsupported.",
            [
                "Chant Chandra Beej mantra regularly",
                "Maintain close relationships with loved ones",
            ],
            f"Moon → H{moon_h} | {_fmt(prev_h, prev_planets)} (12th) | {_fmt(next_h, next_planets)} (2nd)",
        )
    return (
        "None",
        "No Kemadruma Dosh — Moon Well-Supported",
        "Moon has planetary company on adjacent houses (2nd/12th). Kemadruma Dosh is cancelled per classical Bhanga rules.",
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
    sat_aspects = [(sat_h + 2) % 12 + 1, (sat_h + 6) % 12 + 1, (sat_h + 9) % 12 + 1]
    if sat_h != 0 and moon_h in sat_aspects:
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


# ── 11. Chandra-Mangal Dosh / Yoga ─────────────────────────────────────────────
def _chandra_mangal(pl):
    moon_h   = _house(pl, "Moon")
    mars_h   = _house(pl, "Mars")
    moon_lon = _lon(pl, "Moon")
    mars_lon = _lon(pl, "Mars")
    moon_sign = int(moon_lon // 30) + 1 if _has(pl, "Moon") else 0
    SIGN_NAMES = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

    if moon_h == mars_h and moon_h != 0:
        # Cancer (4) or Taurus (2) → classical Lakshmi-yoga side (positive — wealth)
        if moon_sign in (4, 2):
            return (
                "None",
                f"Moon–Mars Conjunction in House {moon_h} (Lakshmi Yoga side)",
                "Moon and Mars together in Cancer or Taurus is classically a 'Lakshmi Yoga' — favourable for wealth through trade and bold action. The conflict-side Chandra-Mangal Dosh does not apply here.",
                [],
                f"Moon → H{moon_h} ({SIGN_NAMES[moon_sign-1]}) | Mars → H{mars_h}",
            )
        tight = _orb(moon_lon, mars_lon) < 10
        status = "Active" if tight else "Mild"
        return (
            status,
            f"Moon–Mars Conjunction in House {moon_h} — Chandra-Mangal Dosh",
            "Moon (mind) joined with Mars (anger) outside Cancer/Taurus creates emotional volatility, sudden outbursts, conflicts with mother and spouse, and impulsive decisions during emotional peaks.",
            [
                "Recite Hanuman Chalisa daily to channel Mars positively",
                "Practice 10 minutes of breath-cooling pranayama (Sheetali) before reacting",
                "Wear silver to balance Moon's reactivity",
                "Donate red lentils on Tuesdays and white sweets on Mondays",
                "Avoid alcohol and stimulants on Tuesdays",
            ],
            f"Moon → H{moon_h} | Mars → H{mars_h}",
        )
    if moon_h != 0 and mars_h != 0:
        diff = abs(moon_h - mars_h)
        diff = min(diff, 12 - diff)
        if diff == 6:
            return (
                "Mild",
                "Moon–Mars in 7th House Aspect — Mild Chandra-Mangal Tension",
                "Moon and Mars share a 7th-house mutual aspect, creating periodic emotional irritability and conflicts in close relationships during their dasha periods.",
                [
                    "Practice mindfulness before reacting in arguments",
                    "Worship Hanuman ji on Tuesdays",
                ],
                f"Moon → H{moon_h} | Mars → H{mars_h}",
            )
    return (
        "None",
        "No Chandra-Mangal Dosh — Mind and Action Aligned",
        "Moon and Mars are independent, allowing balanced emotion and assertion.",
        [],
        f"Moon → H{moon_h} | Mars → H{mars_h}",
    )


# ── 12. Sakat Yoga ─────────────────────────────────────────────────────────────
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
def _putra(pl):
    malefics = {"Saturn", "Mars", "Rahu", "Ketu"}
    h5 = _planets_in_house(pl, 5)
    malefics_in_5th = [p for p in h5 if p in malefics]
    jup_h = _house(pl, "Jupiter")  # Putra karaka

    if len(malefics_in_5th) >= 2:
        return (
            "Active",
            f"Multiple Malefics in 5th House ({', '.join(malefics_in_5th)}) — Putra Dosh",
            "Putra Dosh (afflicting the children house) forms when 2+ malefics occupy the 5th house. May indicate delays in conception, pregnancy complications, or stress around progeny matters. Always consult a medical professional for fertility concerns — these remedies supplement, never substitute, medical advice.",
            [
                "Recite Santan Gopal mantra 108 times daily",
                "Worship Lord Krishna with butter offering on Janmashtami",
                "Perform Putra Prapti Pooja at a Krishna temple",
                "Donate to a children's charity or orphanage",
                "Strengthen Jupiter — fast on Thursdays, donate yellow items",
            ],
            f"5th House: {', '.join(malefics_in_5th)} | Jupiter → H{jup_h}",
        )
    if len(malefics_in_5th) == 1 or jup_h in (6, 8, 12):
        cause = f"5th House: {malefics_in_5th[0]}" if malefics_in_5th else f"Jupiter → H{jup_h} (dusthana)"
        return (
            "Mild",
            "Mild Affliction on Children House — Partial Putra Dosh",
            "Mild affliction in the 5th house or on Jupiter (significator of children). May cause mild delays or tension regarding progeny — not severe. Always consult medical professionals for fertility concerns.",
            [
                "Chant Santan Gopal mantra weekly on Wednesdays",
                "Donate sweets to children on Krishna Janmashtami",
            ],
            cause,
        )
    return (
        "None",
        "No Putra Dosh — Children House Strong",
        "5th house and Jupiter (Putra karaka) are well-placed. No significant affliction on progeny indicators.",
        [],
        f"5th House: {', '.join(_planets_in_house(pl, 5)) or 'Empty'} | Jupiter → H{jup_h}",
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


# ── 16. Ekadhipatya Dosh ───────────────────────────────────────────────────────
def _ekadhipatya(pl):
    """Same planet lords two houses (one kendra/trikona, one dusthana) AND sits in its dusthana."""
    SIGN_LORD = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
    }
    SIGN_NAMES_LOWER = {
        "aries": 1, "taurus": 2, "gemini": 3, "cancer": 4, "leo": 5, "virgo": 6,
        "libra": 7, "scorpio": 8, "sagittarius": 9, "capricorn": 10, "aquarius": 11, "pisces": 12,
    }
    KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}
    DUSTHANA = {6, 8, 12}

    def _planet_sign_idx(p):
        """Return 1-12 sign index from longitude (preferred), else from sign field (int or string)."""
        if "longitude" in p:
            try:
                return int(float(p["longitude"]) // 30) + 1
            except (TypeError, ValueError):
                pass
        s = p.get("sign")
        if isinstance(s, int) and 1 <= s <= 12:
            return s
        if isinstance(s, str):
            return SIGN_NAMES_LOWER.get(s.strip().lower(), 0)
        return 0

    # Derive ascendant sign from any planet with usable sign+house data
    asc_sign = 0
    for p in pl:
        sign_idx = _planet_sign_idx(p)
        h = p.get("house")
        if 1 <= sign_idx <= 12 and isinstance(h, int) and 1 <= h <= 12:
            asc_sign = ((sign_idx - h) % 12) + 1
            break
    if asc_sign == 0:
        return ("None", "No Ekadhipatya Dosh — Ascendant data unavailable",
                "Cannot evaluate Ekadhipatya without ascendant sign.", [], "")

    house_lord = {h: SIGN_LORD[((asc_sign - 1 + h - 1) % 12) + 1] for h in range(1, 13)}

    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        owned = [h for h, lord in house_lord.items() if lord == planet]
        good_houses = [h for h in owned if h in KENDRA_TRIKONA]
        bad_houses  = [h for h in owned if h in DUSTHANA]
        if not good_houses or not bad_houses:
            continue
        ph = _house(pl, planet)
        if ph in DUSTHANA and ph in bad_houses:
            gh = good_houses[0]
            return (
                "Active",
                f"{planet} Owns H{gh} & H{ph}, Sits in H{ph} — Ekadhipatya Dosh",
                f"{planet} rules both a strong house (H{gh}) and a difficult house (H{ph}), and is placed in the difficult house. This structurally weakens the affairs of H{gh}. A subtle but persistent dosh whose effects show across the planet's dasha periods.",
                [
                    f"Strengthen {planet} via its weekly day rituals (recite its beej mantra)",
                    f"Wear {planet}'s gemstone after Jyotish consultation to amplify positive expression",
                    f"Engage in selfless service in the area H{gh} represents",
                    "Avoid taking up tasks that aggravate the dusthana's nature",
                ],
                f"{planet} owns H{gh} (good) + H{ph} (dusthana), placed in H{ph}",
            )
    return (
        "None",
        "No Ekadhipatya Dosh — House Lordships Balanced",
        "No planet's dual-rulership creates structural weakening in this chart.",
        [],
        f"Lagna sign: {asc_sign}",
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
    ("chandra_mangal", "Chandra-Mangal Dosh",  "चन्द्र-मंगल दोष",     "🌗", _chandra_mangal),
    ("sakat_yoga",     "Sakat Yoga",           "शकट योग",             "🛒", _sakat_yoga),
    ("putra",          "Putra Dosh",           "पुत्र दोष",           "👶", _putra),
    ("gandanta",       "Gandanta Dosh",        "गण्डान्त दोष",        "🌊", _gandanta),
    ("punar_phoo",     "Punar Phoo Dosh",      "पुनः फू दोष",         "💔", _punar_phoo),
    ("ekadhipatya",    "Ekadhipatya Dosh",     "एकाधिपत्य दोष",       "👑", _ekadhipatya),
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
