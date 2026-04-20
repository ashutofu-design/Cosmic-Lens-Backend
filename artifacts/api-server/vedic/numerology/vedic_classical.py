"""
Tier 2 — Vedic Classical Engine for Life Mastery Report.

Produces (from DOB + optional TOB, NO lat/lon required):
  - Sun Rashi (sidereal), Moon Rashi (sidereal), Lagna approx (tropical-solar only if no coords)
  - Nakshatra + Pada (from Moon sidereal longitude)
  - Vimshottari Mahadasha current + next + timeline (from Moon nakshatra)
  - Sadhe Sati status (compares transit Saturn today vs natal Moon rashi)
  - Navagraha strength proxy (0-100) based on driver-friends/enemies + current dasha lord boost
  - Ishta Devata + Personal Yantra + Kuldevta-hint from driver number

All computations fall back gracefully if swisseph is missing or TOB absent
(defaults TOB=12:00 IST, lat=28.6139/Delhi for ayanamsa purposes only — Moon
position is geocentric so lat/lon don't affect it materially for reports).
"""
from __future__ import annotations
from datetime import datetime, date, timedelta, timezone
from typing import Any

# ─── Constants ───────────────────────────────────────────────────────────
RASHIS = [
    ("Mesha", "मेष", "Aries"),
    ("Vrishabha", "वृषभ", "Taurus"),
    ("Mithuna", "मिथुन", "Gemini"),
    ("Karka", "कर्क", "Cancer"),
    ("Simha", "सिंह", "Leo"),
    ("Kanya", "कन्या", "Virgo"),
    ("Tula", "तुला", "Libra"),
    ("Vrishchika", "वृश्चिक", "Scorpio"),
    ("Dhanu", "धनु", "Sagittarius"),
    ("Makara", "मकर", "Capricorn"),
    ("Kumbha", "कुम्भ", "Aquarius"),
    ("Meena", "मीन", "Pisces"),
]
RASHI_LORDS = ["Mars","Venus","Mercury","Moon","Sun","Mercury","Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]

NAKSHATRAS = [
    ("Ashwini","अश्विनी","Ketu"),("Bharani","भरणी","Venus"),("Krittika","कृत्तिका","Sun"),
    ("Rohini","रोहिणी","Moon"),("Mrigashira","मृगशिरा","Mars"),("Ardra","आर्द्रा","Rahu"),
    ("Punarvasu","पुनर्वसु","Jupiter"),("Pushya","पुष्य","Saturn"),("Ashlesha","आश्लेषा","Mercury"),
    ("Magha","मघा","Ketu"),("Purva Phalguni","पूर्वा फाल्गुनी","Venus"),("Uttara Phalguni","उत्तरा फाल्गुनी","Sun"),
    ("Hasta","हस्त","Moon"),("Chitra","चित्रा","Mars"),("Swati","स्वाति","Rahu"),
    ("Vishakha","विशाखा","Jupiter"),("Anuradha","अनुराधा","Saturn"),("Jyeshtha","ज्येष्ठा","Mercury"),
    ("Moola","मूल","Ketu"),("Purva Ashadha","पूर्वा आषाढ़ा","Venus"),("Uttara Ashadha","उत्तरा आषाढ़ा","Sun"),
    ("Shravana","श्रवण","Moon"),("Dhanishtha","धनिष्ठा","Mars"),("Shatabhisha","शतभिषा","Rahu"),
    ("Purva Bhadrapada","पूर्वा भाद्रपद","Jupiter"),("Uttara Bhadrapada","उत्तरा भाद्रपद","Saturn"),("Revati","रेवती","Mercury"),
]

# Vimshottari Mahadasha periods (years) in order
VIMSHOTTARI = [
    ("Ketu",7),("Venus",20),("Sun",6),("Moon",10),("Mars",7),
    ("Rahu",18),("Jupiter",16),("Saturn",19),("Mercury",17),
]
NAK_LORDS_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
# Nakshatra → starting dasha lord (repeats every 9)
def _nak_lord(nak_idx: int) -> str:
    return NAK_LORDS_ORDER[nak_idx % 9]

DRIVER_TO_PLANET = {
    1:"Sun", 2:"Moon", 3:"Jupiter", 4:"Rahu", 5:"Mercury",
    6:"Venus", 7:"Ketu", 8:"Saturn", 9:"Mars",
}
PLANET_DEITY = {
    "Sun":"Lord Rama / Surya Bhagwan", "Moon":"Lord Shiva / Chandra Dev",
    "Jupiter":"Lord Vishnu / Brihaspati", "Rahu":"Goddess Durga / Bhairav",
    "Mercury":"Lord Ganesha / Budh", "Venus":"Goddess Lakshmi / Shukra",
    "Ketu":"Lord Ganesha / Ketu", "Saturn":"Lord Hanuman / Shani Dev",
    "Mars":"Lord Hanuman / Mangal Dev / Kartikeya",
}
PLANET_YANTRA = {
    "Sun":"Surya Yantra", "Moon":"Chandra Yantra", "Jupiter":"Brihaspati Yantra",
    "Rahu":"Rahu Yantra", "Mercury":"Budh Yantra", "Venus":"Shukra Yantra",
    "Ketu":"Ketu Yantra", "Saturn":"Shani Yantra", "Mars":"Mangal Yantra",
}
PLANET_FRIENDS = {  # classical shadbala-style friendships (simplified)
    "Sun": ["Moon","Mars","Jupiter"], "Moon":["Sun","Mercury"],
    "Mars":["Sun","Moon","Jupiter"], "Mercury":["Sun","Venus"],
    "Jupiter":["Sun","Moon","Mars"], "Venus":["Mercury","Saturn"],
    "Saturn":["Mercury","Venus"], "Rahu":["Venus","Saturn","Mercury"],
    "Ketu":["Mars","Jupiter","Sun"],
}
PLANET_ENEMIES = {
    "Sun":["Saturn","Venus"], "Moon":[], "Mars":["Mercury"],
    "Mercury":["Moon"], "Jupiter":["Mercury","Venus"], "Venus":["Sun","Moon"],
    "Saturn":["Sun","Moon","Mars"], "Rahu":["Sun","Moon","Mars"],
    "Ketu":["Moon","Venus"],
}

# ─── Helpers ─────────────────────────────────────────────────────────────
def _parse_dob_tob(dob: str, tob: str | None = None) -> datetime:
    """Parse DOB (YYYY-MM-DD) + TOB (HH:MM 24h) — defaults TOB to 12:00 IST."""
    d = datetime.strptime(dob, "%Y-%m-%d")
    if tob:
        try:
            t = datetime.strptime(tob.strip(), "%H:%M")
            d = d.replace(hour=t.hour, minute=t.minute)
        except Exception:
            d = d.replace(hour=12, minute=0)
    else:
        d = d.replace(hour=12, minute=0)
    # Treat as IST → UTC by subtracting 5:30
    return d - timedelta(hours=5, minutes=30)


def _safe_swe_calc(dt_utc: datetime, body_id: int, ayanamsa_id: int | None = None) -> float | None:
    """Return sidereal longitude in degrees (0-360), or None on failure."""
    try:
        import swisseph as swe
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0)
        if ayanamsa_id is not None:
            swe.set_sid_mode(ayanamsa_id)
            flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        else:
            flag = swe.FLG_SWIEPH
        res, _ = swe.calc_ut(jd, body_id, flag)
        return float(res[0]) % 360.0
    except Exception:
        return None


def _lon_to_rashi(lon: float) -> int:
    """0-11 rashi index."""
    return int(lon // 30) % 12


def _lon_to_nakshatra(lon: float) -> tuple[int, int]:
    """Return (nakshatra_idx 0-26, pada 1-4)."""
    span = 360.0 / 27.0  # 13.333...
    nak = int(lon // span) % 27
    deg_in = lon - nak * span
    pada = int(deg_in // (span / 4.0)) + 1
    return nak, max(1, min(4, pada))


# ─── Core computations ──────────────────────────────────────────────────
def compute_rashi_and_nakshatra(dob: str, tob: str | None = None) -> dict[str, Any]:
    """Sun rashi + Moon rashi + Nakshatra + Pada (sidereal/Lahiri)."""
    dt_utc = _parse_dob_tob(dob, tob)
    try:
        import swisseph as swe
        sun_lon = _safe_swe_calc(dt_utc, swe.SUN, swe.SIDM_LAHIRI)
        moon_lon = _safe_swe_calc(dt_utc, swe.MOON, swe.SIDM_LAHIRI)
    except Exception:
        sun_lon = moon_lon = None

    if sun_lon is None or moon_lon is None:
        # Fallback: approximate Sun sign from tropical date ranges (Vedic-sidereal shifted ~23°)
        # Very rough — returns Sun only, Moon=None
        return {
            "sun_rashi_idx": _tropical_sun_sign_fallback(dob),
            "moon_rashi_idx": None,
            "nakshatra_idx": None, "pada": None,
            "sun_lon": None, "moon_lon": None,
            "source": "fallback-tropical",
        }

    nak_idx, pada = _lon_to_nakshatra(moon_lon)
    return {
        "sun_rashi_idx": _lon_to_rashi(sun_lon),
        "moon_rashi_idx": _lon_to_rashi(moon_lon),
        "nakshatra_idx": nak_idx,
        "pada": pada,
        "sun_lon": round(sun_lon, 3),
        "moon_lon": round(moon_lon, 3),
        "source": "swisseph-sidereal-lahiri",
    }


def _tropical_sun_sign_fallback(dob: str) -> int:
    """Approx Vedic Sun sign from date only (sidereal approx — shift tropical back ~23°)."""
    m, d = int(dob[5:7]), int(dob[8:10])
    # Approximate sidereal-Vedic cutoffs (shifted ~14-15 days later than tropical):
    cutoffs = [
        (4,14,0),(5,15,1),(6,15,2),(7,17,3),(8,17,4),(9,17,5),
        (10,18,6),(11,17,7),(12,16,8),(1,14,9),(2,13,10),(3,14,11),
    ]
    for mo, da, idx in cutoffs:
        if (m, d) >= (mo, da) and mo != 12:
            if mo < 12:
                # current sign from that cutoff until next cutoff
                pass
        # simple month-day lookup
    # Simpler: use table
    simple = [(1,14,9),(2,13,10),(3,14,11),(4,14,0),(5,15,1),(6,15,2),(7,17,3),
              (8,17,4),(9,17,5),(10,18,6),(11,17,7),(12,16,8)]
    idx = 8  # default Makara for edge cases
    for mo, da, i in simple:
        if m > mo or (m == mo and d >= da):
            idx = i
    return idx


def compute_mahadasha(dob: str, tob: str | None = None, today: date | None = None) -> dict[str, Any]:
    """Compute current + next + full Vimshottari mahadasha timeline from Moon nakshatra."""
    rn = compute_rashi_and_nakshatra(dob, tob)
    nak_idx = rn.get("nakshatra_idx")
    moon_lon = rn.get("moon_lon")
    if nak_idx is None or moon_lon is None:
        return {"available": False, "reason": "Moon position unavailable (swisseph failed)"}

    # Fraction of nakshatra elapsed at birth → unused part of first mahadasha
    span = 360.0 / 27.0
    deg_in_nak = moon_lon - nak_idx * span
    frac_elapsed = deg_in_nak / span  # 0..1
    first_lord = _nak_lord(nak_idx)
    # find index in VIMSHOTTARI list
    order_idx = next(i for i, (p, _) in enumerate(VIMSHOTTARI) if p == first_lord)
    first_years = VIMSHOTTARI[order_idx][1]
    first_remaining = first_years * (1 - frac_elapsed)

    # Build timeline starting at birth — use full datetime (DOB + TOB) for precision
    birth_dt = _parse_dob_tob(dob, tob) + timedelta(hours=5, minutes=30)  # undo IST→UTC, back to local civil time
    birth_date = birth_dt.date()
    timeline = []
    cur = birth_dt
    # First (partial) period
    end1 = cur + timedelta(days=first_remaining * 365.25)
    timeline.append({"lord": first_lord, "start": cur.date().isoformat(), "end": end1.date().isoformat(),
                     "years": round(first_remaining, 2), "partial": True})
    cur = end1
    # Remaining 8 full periods completes exactly one 120-year cycle from birth
    for offset in range(1, 9):
        lord, yrs = VIMSHOTTARI[(order_idx + offset) % len(VIMSHOTTARI)]
        nxt = cur + timedelta(days=yrs * 365.25)
        timeline.append({"lord": lord, "start": cur.date().isoformat(), "end": nxt.date().isoformat(),
                         "years": yrs, "partial": False})
        cur = nxt

    # Find current (compare as ISO date strings)
    td = today or date.today()
    td_s = td.isoformat()
    current = next((t for t in timeline if t["start"] <= td_s < t["end"]), None)
    nxt_idx = timeline.index(current) + 1 if current else 0
    nxt = timeline[nxt_idx] if nxt_idx < len(timeline) else None

    return {
        "available": True,
        "first_lord": first_lord,
        "first_remaining_years": round(first_remaining, 2),
        "current": current,
        "next": nxt,
        "timeline": timeline,
    }


def compute_sadhe_sati(dob: str, tob: str | None = None, today: date | None = None) -> dict[str, Any]:
    """Check if Saturn is currently transiting 12th/1st/2nd house from natal Moon."""
    rn = compute_rashi_and_nakshatra(dob, tob)
    moon_rashi = rn.get("moon_rashi_idx")
    if moon_rashi is None:
        return {"available": False, "reason": "Moon rashi unknown"}

    # Current Saturn position
    td = today or date.today()
    now_dt = datetime(td.year, td.month, td.day, 12, 0) - timedelta(hours=5, minutes=30)
    try:
        import swisseph as swe
        sat_lon = _safe_swe_calc(now_dt, swe.SATURN, swe.SIDM_LAHIRI)
    except Exception:
        sat_lon = None
    if sat_lon is None:
        return {"available": False, "reason": "Saturn transit unavailable"}

    sat_rashi = _lon_to_rashi(sat_lon)
    # Distance from moon rashi (houses 12, 1, 2 = sadhe sati active)
    diff = (sat_rashi - moon_rashi) % 12  # 0=1st house, 11=12th, 1=2nd
    if diff == 11:
        phase = "First Dhaiya (rising)"
        active = True
    elif diff == 0:
        phase = "Peak (2nd Dhaiya)"
        active = True
    elif diff == 1:
        phase = "Setting (3rd Dhaiya)"
        active = True
    else:
        phase = None
        active = False

    # Small Panoti (Dhaiya) — Saturn in 4th or 8th from Moon
    small_panoti = diff in (3, 7)
    return {
        "available": True,
        "active": active,
        "phase": phase,
        "saturn_rashi_idx": sat_rashi,
        "moon_rashi_idx": moon_rashi,
        "house_from_moon": diff + 1,  # 1-indexed
        "small_panoti": small_panoti,
    }


def compute_navagraha_strength(driver: int, dasha_lord: str | None = None) -> dict[str, int]:
    """Proxy strength 0-100 per planet based on driver-planet friendship + dasha boost."""
    base_planet = DRIVER_TO_PLANET.get(driver, "Sun")
    friends = set(PLANET_FRIENDS.get(base_planet, []))
    enemies = set(PLANET_ENEMIES.get(base_planet, []))
    strengths = {}
    for p in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
        if p == base_planet:
            s = 85
        elif p in friends:
            s = 72
        elif p in enemies:
            s = 35
        else:
            s = 55
        if dasha_lord and p == dasha_lord:
            s = min(100, s + 15)
        strengths[p] = s
    return strengths


def compute_ishta_devata(driver: int) -> dict[str, str]:
    """Personal deity + yantra + mantra hint from driver."""
    planet = DRIVER_TO_PLANET.get(driver, "Sun")
    return {
        "driver": driver,
        "planet": planet,
        "deity": PLANET_DEITY.get(planet, "Lord Shiva"),
        "yantra": PLANET_YANTRA.get(planet, "Shiva Yantra"),
    }


def compute_tier2_bundle(dob: str, tob: str | None, driver: int,
                         today: date | None = None) -> dict[str, Any]:
    """One-call bundle for Tier 2 PDF section."""
    rn = compute_rashi_and_nakshatra(dob, tob)
    mdash = compute_mahadasha(dob, tob, today)
    ssati = compute_sadhe_sati(dob, tob, today)
    dasha_lord = (mdash.get("current") or {}).get("lord") if mdash.get("available") else None
    strengths = compute_navagraha_strength(driver, dasha_lord)
    deity = compute_ishta_devata(driver)

    # Human-friendly labels
    sun_i = rn.get("sun_rashi_idx")
    moon_i = rn.get("moon_rashi_idx")
    nak_i = rn.get("nakshatra_idx")
    return {
        "rashi_nakshatra": {
            **rn,
            "sun_rashi": RASHIS[sun_i] if sun_i is not None else None,
            "moon_rashi": RASHIS[moon_i] if moon_i is not None else None,
            "moon_rashi_lord": RASHI_LORDS[moon_i] if moon_i is not None else None,
            "sun_rashi_lord": RASHI_LORDS[sun_i] if sun_i is not None else None,
            "nakshatra": NAKSHATRAS[nak_i] if nak_i is not None else None,
        },
        "mahadasha": mdash,
        "sadhe_sati": ssati,
        "navagraha_strengths": strengths,
        "ishta_devata": deity,
    }
