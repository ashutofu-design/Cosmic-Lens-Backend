"""
Cosmic AstroVastu — Classical 80-Rule Database
================================================
Personalized Vastu rules derived by cross-referencing classical Vastu treatises
(Brihat Samhita, Mansara Shilpa Shastra, Mayamatam, Vastu Saar) with classical
Jyotish (BPHS, Phaladeepika, Lal Kitab, Surya Siddhanta).

This module is a PURE DATA + LOOKUP module — no I/O, no LLM calls, no scoring.
The engine layer (astrovastu_engine.py) consumes these tables to produce
personalized verdicts.

Categories:
  1. Lagna → favourable / avoid directions
  2. Rashi → bedroom head direction
  3. Nakshatra → main door alignment
  4. Planet-house stress → Vastu impact amplifier
  5. Mahadasha → active direction overlay
  6. Ishta Devata → pooja room setup
  7. House lord → room mapping
  8. Color personalization
  9. Yantra prescription
 10. Conflict resolution tie-breakers (used by engine, listed for reference)
"""

from typing import Dict, List, Optional, Any


# ── Branding constant — NEVER reveal AI/ChatGPT to user ──────────────────
ENGINE_NAME    = "Cosmic AstroVastu Drishti Engine"
ENGINE_VERSION = "v1.0"
BRANDING_LINE  = "Powered by Advanced Cosmic Intelligence"


# ── Direction enum (8 cardinal + intercardinal) ──────────────────────────
DIRECTIONS = ["North", "North-East", "East", "South-East",
              "South", "South-West", "West", "North-West"]

# Compass heading (degrees) → direction bucket. Each bucket is 45° wide,
# centered on the cardinal heading.
DIRECTION_HEADINGS = {
    "North":      0,
    "North-East": 45,
    "East":       90,
    "South-East": 135,
    "South":      180,
    "South-West": 225,
    "West":       270,
    "North-West": 315,
}


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 1 — Lagna → favourable / avoid direction map
# Source: Lal Kitab Adhyay 3, Brihat Samhita 53.86, BPHS Ch.3-4, Phaladeepika 15
# ─────────────────────────────────────────────────────────────────────────
LAGNA_DIRECTION_MAP: Dict[str, Dict[str, Any]] = {
    "Aries":       {"element": "Fire",  "ruler": "Mars",    "favourable": ["South", "East"],         "avoid": ["North-West"], "vastu_ref": "Lal Kitab Adh.3",       "jyotish_ref": "BPHS Ch.3"},
    "Taurus":      {"element": "Earth", "ruler": "Venus",   "favourable": ["South-East"],            "avoid": ["North-East"], "vastu_ref": "Brihat Samhita 53.86",  "jyotish_ref": "Phaladeepika 15.2"},
    "Gemini":      {"element": "Air",   "ruler": "Mercury", "favourable": ["North"],                 "avoid": ["South"],      "vastu_ref": "Mansara Sh.4.18",       "jyotish_ref": "Phaladeepika 15.4"},
    "Cancer":      {"element": "Water", "ruler": "Moon",    "favourable": ["North-West", "North"],   "avoid": ["South-East"], "vastu_ref": "Vastu Saar Ch.6",       "jyotish_ref": "BPHS Ch.3"},
    "Leo":         {"element": "Fire",  "ruler": "Sun",     "favourable": ["East"],                  "avoid": ["West"],       "vastu_ref": "Brihat Samhita 53.40",  "jyotish_ref": "Phaladeepika 15.6"},
    "Virgo":       {"element": "Earth", "ruler": "Mercury", "favourable": ["North", "North-East"],   "avoid": ["South-West"], "vastu_ref": "Mansara Sh.4.22",       "jyotish_ref": "Phaladeepika 15.5"},
    "Libra":       {"element": "Air",   "ruler": "Venus",   "favourable": ["South-East"],            "avoid": ["North-East"], "vastu_ref": "Mansara Sh.4.24",       "jyotish_ref": "BPHS Ch.4"},
    "Scorpio":     {"element": "Water", "ruler": "Mars",    "favourable": ["South"],                 "avoid": ["North"],      "vastu_ref": "Lal Kitab Adh.8",       "jyotish_ref": "Phaladeepika 15.8"},
    "Sagittarius": {"element": "Fire",  "ruler": "Jupiter", "favourable": ["North-East"],            "avoid": ["South-West"], "vastu_ref": "Brihat Samhita 53.110", "jyotish_ref": "BPHS Ch.4"},
    "Capricorn":   {"element": "Earth", "ruler": "Saturn",  "favourable": ["West"],                  "avoid": ["East"],       "vastu_ref": "Lal Kitab Adh.10",      "jyotish_ref": "Vastu Saar Ch.7"},
    "Aquarius":    {"element": "Air",   "ruler": "Saturn",  "favourable": ["West"],                  "avoid": ["North-East"], "vastu_ref": "Mansara Sh.4.30",       "jyotish_ref": "Phaladeepika 15.10"},
    "Pisces":      {"element": "Water", "ruler": "Jupiter", "favourable": ["North-East"],            "avoid": ["South-West"], "vastu_ref": "Brihat Samhita 53.122", "jyotish_ref": "BPHS Ch.4"},
}


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 2 — Rashi (Moon sign) → bedroom HEAD direction
# Element-grouped — generic "head south" rule does NOT apply for water signs
# ─────────────────────────────────────────────────────────────────────────
RASHI_BEDHEAD_MAP: Dict[str, Dict[str, Any]] = {
    "Aries":       {"element": "Fire",  "best_head": ["East", "South"],       "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.7"},
    "Leo":         {"element": "Fire",  "best_head": ["East", "South"],       "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.7"},
    "Sagittarius": {"element": "Fire",  "best_head": ["East", "South"],       "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.7"},
    "Taurus":      {"element": "Earth", "best_head": ["South", "South-West"], "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "Phaladeepika 22"},
    "Virgo":       {"element": "Earth", "best_head": ["South", "South-West"], "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "Phaladeepika 22"},
    "Capricorn":   {"element": "Earth", "best_head": ["South", "South-West"], "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "Phaladeepika 22"},
    "Gemini":      {"element": "Air",   "best_head": ["East", "North"],       "vastu_ref": "Mansara Sh.6",    "jyotish_ref": "BPHS Ch.7"},
    "Libra":       {"element": "Air",   "best_head": ["East", "North"],       "vastu_ref": "Mansara Sh.6",    "jyotish_ref": "BPHS Ch.7"},
    "Aquarius":    {"element": "Air",   "best_head": ["East", "North"],       "vastu_ref": "Mansara Sh.6",    "jyotish_ref": "BPHS Ch.7"},
    "Cancer":      {"element": "Water", "best_head": ["North", "West"],       "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.3 (Cancer)"},
    "Scorpio":     {"element": "Water", "best_head": ["North", "West"],       "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.3 (Cancer)"},
    "Pisces":      {"element": "Water", "best_head": ["North", "West"],       "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.3 (Cancer)"},
}


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 3 — Nakshatra → main door alignment (grouped by ruling planet)
# ─────────────────────────────────────────────────────────────────────────
NAKSHATRA_DOOR_GROUPS: List[Dict[str, Any]] = [
    {"nakshatras": ["Ashwini", "Bharani", "Krittika"],          "best_door": ["East", "North-East"], "ruler": "Sun-Mars",   "vastu_ref": "Mansara Sh.10",  "jyotish_ref": "BPHS Ch.7"},
    {"nakshatras": ["Rohini", "Mrigashira", "Ardra"],           "best_door": ["North", "North-East"], "ruler": "Venus-Mercury", "vastu_ref": "Brihat Samhita 56", "jyotish_ref": "Phaladeepika 18"},
    {"nakshatras": ["Punarvasu", "Pushya", "Ashlesha"],         "best_door": ["North-West"],         "ruler": "Moon",       "vastu_ref": "Vastu Saar Ch.4", "jyotish_ref": "BPHS Ch.3"},
    {"nakshatras": ["Magha", "Purva Phalguni", "Uttara Phalguni"], "best_door": ["East"],            "ruler": "Sun",        "vastu_ref": "Brihat Samhita 53.71",  "jyotish_ref": "BPHS Ch.4"},
    {"nakshatras": ["Hasta", "Chitra", "Swati"],                "best_door": ["North", "East"],      "ruler": "Mercury-Venus", "vastu_ref": "Mansara Sh.10",  "jyotish_ref": "Phaladeepika 18"},
    {"nakshatras": ["Vishakha", "Anuradha", "Jyeshtha"],        "best_door": ["South-East"],         "ruler": "Mars-Mercury", "vastu_ref": "Lal Kitab Adh.8", "jyotish_ref": "BPHS Ch.4"},
    {"nakshatras": ["Mula", "Purva Ashadha", "Uttara Ashadha"], "best_door": ["North-East"],         "ruler": "Jupiter",    "vastu_ref": "Brihat Samhita 56", "jyotish_ref": "Phaladeepika 18"},
    {"nakshatras": ["Shravana", "Dhanishta", "Shatabhisha"],    "best_door": ["West"],               "ruler": "Saturn",     "vastu_ref": "Vastu Saar Ch.4", "jyotish_ref": "Lal Kitab Adh.10"},
    {"nakshatras": ["Purva Bhadrapada", "Uttara Bhadrapada", "Revati"], "best_door": ["North-East"], "ruler": "Jupiter",    "vastu_ref": "Brihat Samhita 56", "jyotish_ref": "Phaladeepika 18"},
]


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 4 — Planet-in-house stress → Vastu severity amplifier
# Each entry: a kundli condition that makes a generic Vastu dosh worse
# ─────────────────────────────────────────────────────────────────────────
PLANET_HOUSE_STRESS: List[Dict[str, Any]] = [
    {"condition": "Saturn in 1/4/7/10",  "amplifies_dosh_in": ["South-West"],         "multiplier": 2.0, "note": "Shani in Kendra makes SW dosha critical"},
    {"condition": "Mars in 4",           "amplifies_dosh_in": ["South-East"],         "multiplier": 1.8, "note": "Mangal in Sukh sthan amplifies kitchen/fire dosha"},
    {"condition": "Rahu in 4",           "amplifies_dosh_in": ["North-East"],         "multiplier": 2.0, "note": "Rahu in 4th house — underground/septic dosh in NE deadly"},
    {"condition": "Ketu in 4",           "amplifies_dosh_in": ["North-East"],         "multiplier": 1.7, "note": "Ketu in 4th amplifies pooja-room dosha"},
    {"condition": "Sun in 12 (weak)",    "amplifies_dosh_in": ["East"],               "multiplier": 1.6, "note": "Weak Sun → dark East causes depression risk"},
    {"condition": "Moon weak (6/8/12)",  "amplifies_dosh_in": ["North-West"],         "multiplier": 1.7, "note": "Weak Moon — NW cleanliness critical"},
    {"condition": "Jupiter weak (6)",    "amplifies_dosh_in": ["North-East"],         "multiplier": 2.0, "note": "Weak Guru — NE clutter disastrous"},
    {"condition": "Venus weak (6/8)",    "amplifies_dosh_in": ["South-East"],         "multiplier": 1.6, "note": "Weak Shukra — SE dosha hits relationships"},
    {"condition": "Mercury combust",     "amplifies_dosh_in": ["East"],               "multiplier": 1.4, "note": "Mercury+Sun close — study facing East not advised"},
]


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 5 — Mahadasha → active direction during this dasha period
# ─────────────────────────────────────────────────────────────────────────
DASHA_ACTIVE_DIRECTION: Dict[str, Dict[str, Any]] = {
    "Sun":     {"direction": "East",        "color": "copper-red",  "items": "copper, ruby",         "day": "Sunday",    "vastu_ref": "Brihat Samhita 53.40", "jyotish_ref": "BPHS Ch.7"},
    "Moon":    {"direction": "North-West",  "color": "white-silver", "items": "silver, white flowers", "day": "Monday",   "vastu_ref": "Vastu Saar Ch.6", "jyotish_ref": "BPHS Ch.7"},
    "Mars":    {"direction": "South",       "color": "red",          "items": "copper, coral",        "day": "Tuesday",   "vastu_ref": "Lal Kitab Adh.3", "jyotish_ref": "Phaladeepika 22"},
    "Mercury": {"direction": "North",       "color": "green",        "items": "bronze, plants",       "day": "Wednesday", "vastu_ref": "Mansara Sh.6",    "jyotish_ref": "BPHS Ch.7"},
    "Jupiter": {"direction": "North-East",  "color": "yellow",       "items": "gold, brass",          "day": "Thursday",  "vastu_ref": "Brihat Samhita 53", "jyotish_ref": "BPHS Ch.4"},
    "Venus":   {"direction": "South-East",  "color": "white-pink",   "items": "silver, fragrance",    "day": "Friday",    "vastu_ref": "Vastu Saar Ch.6", "jyotish_ref": "Phaladeepika 22"},
    "Saturn":  {"direction": "West",        "color": "blue-black",   "items": "iron",                 "day": "Saturday",  "vastu_ref": "Lal Kitab Adh.10", "jyotish_ref": "BPHS Ch.7"},
    "Rahu":    {"direction": "South-West",  "color": "ash-grey",     "items": "stable heavy items",   "day": "Wed/Sat",   "vastu_ref": "Mayamatam Ch.7",  "jyotish_ref": "BPHS Ch.4"},
    "Ketu":    {"direction": "North-East",  "color": "white",        "items": "diya, agarbatti",      "day": "Tue/Sat",   "vastu_ref": "Vastu Saar Ch.6", "jyotish_ref": "BPHS Ch.4"},
}


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 6 — Ishta Devata → pooja room placement
# Derivation: 12th house from Karakamsa Lagna (in D9) — see astrovastu_engine
# ─────────────────────────────────────────────────────────────────────────
ISHTA_DEVATA_MAP: Dict[str, Dict[str, Any]] = {
    "Sun":     {"deity": "Shiva / Rama",            "direction": "North",      "facing": "North",  "vastu_ref": "Vastu Saar Ch.5", "jyotish_ref": "BPHS Ch.32 (Karakamsa)"},
    "Moon":    {"deity": "Krishna / Gauri",         "direction": "North-East", "facing": "East",   "vastu_ref": "Mansara Sh.5",    "jyotish_ref": "BPHS Ch.32"},
    "Mars":    {"deity": "Hanuman / Subramanya",    "direction": "South-West", "facing": "South",  "vastu_ref": "Lal Kitab Adh.3", "jyotish_ref": "BPHS Ch.32"},
    "Mercury": {"deity": "Vishnu",                  "direction": "North-East", "facing": "West",   "vastu_ref": "Brihat Samhita 56", "jyotish_ref": "BPHS Ch.32"},
    "Jupiter": {"deity": "Brihaspati / Vishnu",     "direction": "North-East", "facing": "West",   "vastu_ref": "Brihat Samhita 56", "jyotish_ref": "BPHS Ch.32"},
    "Venus":   {"deity": "Lakshmi / Mahalakshmi",   "direction": "South-East", "facing": "East",   "vastu_ref": "Vastu Saar Ch.5", "jyotish_ref": "BPHS Ch.32"},
    "Saturn":  {"deity": "Shani Bhairava / Hanuman","direction": "West",       "facing": "West",   "vastu_ref": "Lal Kitab Adh.10", "jyotish_ref": "BPHS Ch.32"},
    "Rahu":    {"deity": "Durga",                   "direction": "South-West", "facing": "North",  "vastu_ref": "Mayamatam Ch.7",  "jyotish_ref": "BPHS Ch.32"},
    "Ketu":    {"deity": "Ganesha",                 "direction": "North-East", "facing": "East",   "vastu_ref": "Vastu Saar Ch.5", "jyotish_ref": "BPHS Ch.32"},
}


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 7 — House lord → room mapping
# 2nd house lord direction = best for cash locker, etc.
# ─────────────────────────────────────────────────────────────────────────
# Astro-Vastu Pillar 1 — compass sector ↔ bhava (whole-sign chart from Lagna).
# When you live in a direction, those linked houses are "triggered" in the chart.
DIRECTION_BHAVA_GRID: Dict[str, List[int]] = {
    "East":       [1],
    "South-East": [2, 3],
    "South":      [4, 5],
    "South-West": [6, 7],
    "West":       [8, 9],
    "North-West": [10],
    "North":      [11],
    "North-East": [12],
}

HOUSE_ROOM_MAPPING: List[Dict[str, Any]] = [
    {"house": 1,  "room": "Main door / entrance / self",       "lord_direction_used": True, "vastu_ref": "Mansara Sh.10",   "jyotish_ref": "BPHS Ch.10"},
    {"house": 2,  "room": "Cash locker / safe",                "lord_direction_used": True, "vastu_ref": "Vastu Saar Ch.8", "jyotish_ref": "BPHS Ch.10"},
    {"house": 3,  "room": "Gym / exercise room",               "lord_direction_used": True, "vastu_ref": "Mansara Sh.7",    "jyotish_ref": "BPHS Ch.10"},
    {"house": 4,  "room": "Master bedroom",                    "lord_direction_used": True, "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.10"},
    {"house": 5,  "room": "Study / kids' room",                "lord_direction_used": True, "vastu_ref": "Brihat Samhita 53", "jyotish_ref": "BPHS Ch.10"},
    {"house": 6,  "room": "Bathroom / dustbin / discharge",    "lord_direction_used": True, "vastu_ref": "Mayamatam Ch.7",  "jyotish_ref": "BPHS Ch.10"},
    {"house": 7,  "room": "Couple's bedroom + drawing room",   "lord_direction_used": True, "vastu_ref": "Vastu Saar Ch.9", "jyotish_ref": "BPHS Ch.10"},
    {"house": 9,  "room": "Pooja room",                        "lord_direction_used": True, "vastu_ref": "Brihat Samhita 56", "jyotish_ref": "BPHS Ch.10"},
    {"house": 10, "room": "Office / work-from-home desk",      "lord_direction_used": True, "vastu_ref": "Mansara Sh.10",   "jyotish_ref": "BPHS Ch.10"},
    {"house": 11, "room": "Cash inflow items (passbook, ledger)", "lord_direction_used": True, "vastu_ref": "Vastu Saar Ch.8", "jyotish_ref": "BPHS Ch.10"},
]

# Planet → preferred direction (used for "lord_direction" lookups in Cat 7)
PLANET_DIRECTION: Dict[str, str] = {
    "Sun":     "East",
    "Moon":    "North-West",
    "Mars":    "South",
    "Mercury": "North",
    "Jupiter": "North-East",
    "Venus":   "South-East",
    "Saturn":  "West",
    "Rahu":    "South-West",
    "Ketu":    "North-East",
}

# Lagna → ruling planet (used to compute Lagna lord)
LAGNA_LORD: Dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Sign → ruling planet (used for house-lord computation)
SIGN_LORD: Dict[str, str] = LAGNA_LORD  # same mapping


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 8 — Color personalization (per Lagna lord + special yogas)
# ─────────────────────────────────────────────────────────────────────────
COLOR_BY_LAGNA_LORD: Dict[str, Dict[str, Any]] = {
    "Sun":     {"primary": "orange / copper-red", "avoid": "deep blue, black"},
    "Moon":    {"primary": "white / silver",       "avoid": "deep red"},
    "Mars":    {"primary": "red / coral",          "avoid": "green in South wall"},
    "Mercury": {"primary": "green",                "avoid": "red in North"},
    "Jupiter": {"primary": "yellow",               "avoid": "ash-grey in NE"},
    "Venus":   {"primary": "white / pastel pink",  "avoid": "loud red in SE"},
    "Saturn":  {"primary": "deep blue / black accent", "avoid": "orange in West"},
}

YOGA_COLOR_OVERRIDE: Dict[str, Dict[str, Any]] = {
    "sade_sati": {"add": "blue / black accents in West", "avoid": "loud red anywhere"},
    "manglik":   {"avoid": "pure red in couple bedroom", "soft": "pastel pink okay"},
    "kal_sarpa": {"add": "extra emphasis on SW + NE cleanliness"},
}


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 9 — Yantra prescription per weak planet
# ─────────────────────────────────────────────────────────────────────────
YANTRA_PRESCRIPTION: Dict[str, Dict[str, Any]] = {
    "Sun":     {"yantra": "Surya Yantra",   "material": "copper",          "wall": "East",       "day": "Sunday",    "vastu_ref": "Brihat Samhita 56.4", "jyotish_ref": "Lal Kitab Adh.1"},
    "Moon":    {"yantra": "Chandra Yantra", "material": "silver",          "wall": "North-West", "day": "Monday",    "vastu_ref": "Vastu Saar Ch.6", "jyotish_ref": "Lal Kitab Adh.2"},
    "Mars":    {"yantra": "Mangal Yantra",  "material": "copper",          "wall": "South",      "day": "Tuesday",   "vastu_ref": "Lal Kitab Adh.3", "jyotish_ref": "Lal Kitab Adh.3"},
    "Mercury": {"yantra": "Budh Yantra",    "material": "bronze",          "wall": "North",      "day": "Wednesday", "vastu_ref": "Mansara Sh.6",    "jyotish_ref": "Lal Kitab Adh.4"},
    "Jupiter": {"yantra": "Guru Yantra",    "material": "gold-plated",     "wall": "North-East", "day": "Thursday",  "vastu_ref": "Brihat Samhita 56", "jyotish_ref": "Lal Kitab Adh.5"},
    "Venus":   {"yantra": "Shukra Yantra",  "material": "silver",          "wall": "South-East", "day": "Friday",    "vastu_ref": "Vastu Saar Ch.6", "jyotish_ref": "Lal Kitab Adh.6"},
    "Saturn":  {"yantra": "Shani Yantra",   "material": "iron / black",    "wall": "West",       "day": "Saturday",  "vastu_ref": "Lal Kitab Adh.10", "jyotish_ref": "Lal Kitab Adh.7"},
    "Rahu":    {"yantra": "Rahu Yantra",    "material": "ash-grey alloy",  "wall": "South-West", "day": "Wed/Sat",   "vastu_ref": "Mayamatam Ch.7", "jyotish_ref": "Lal Kitab Adh.8"},
    "Ketu":    {"yantra": "Ketu Yantra",    "material": "mixed metal",     "wall": "North-East", "day": "Tue/Sat",   "vastu_ref": "Vastu Saar Ch.6", "jyotish_ref": "Lal Kitab Adh.9"},
}


# ─────────────────────────────────────────────────────────────────────────
# CATEGORY 10 — Conflict resolution tie-breaker rules (engine reference)
# Implementation lives in astrovastu_engine.apply_tie_breakers()
# ─────────────────────────────────────────────────────────────────────────
TIE_BREAKER_RULES: List[Dict[str, str]] = [
    {"id": "TB1", "rule": "Lagna lord overrides generic direction",                     "weight": "Highest"},
    {"id": "TB2", "rule": "Current Mahadasha trumps natal placement (active dasha priority)", "weight": "High"},
    {"id": "TB3", "rule": "Sade-Sati overrides everything for 7.5 years",               "weight": "Highest"},
    {"id": "TB4", "rule": "Manglik users follow Mars-friendly directions for marriage room", "weight": "High"},
    {"id": "TB5", "rule": "Kal Sarpa Yoga users — extra SW + NE cleanliness mandatory", "weight": "Medium"},
    {"id": "TB6", "rule": "Mool Nakshatra natives — special pooja in NE mandatory",     "weight": "Medium"},
    {"id": "TB7", "rule": "Atmakaraka direction takes priority for soul-level decisions (meditation, main idol)", "weight": "Medium"},
]


# ─────────────────────────────────────────────────────────────────────────
# Generic Vastu room → ideal direction (baseline that personalization may override)
# ─────────────────────────────────────────────────────────────────────────
GENERIC_ROOM_IDEAL: Dict[str, Dict[str, Any]] = {
    "kitchen":     {"ideal": ["South-East"],            "acceptable": ["North-West"], "avoid": ["North-East", "South-West"], "vastu_ref": "Brihat Samhita 53.42"},
    "bedroom":     {"ideal": ["South-West"],            "acceptable": ["South", "West"], "avoid": ["North-East"],           "vastu_ref": "Vastu Saar Ch.9"},
    "pooja":       {"ideal": ["North-East"],            "acceptable": ["East", "North"], "avoid": ["South", "South-West"],  "vastu_ref": "Mansara Sh.5"},
    "study":       {"ideal": ["North-East", "East"],    "acceptable": ["North"],         "avoid": ["South"],                "vastu_ref": "Brihat Samhita 56"},
    "cash_locker": {"ideal": ["South-West", "North"],   "acceptable": ["East"],          "avoid": ["South-East"],           "vastu_ref": "Vastu Saar Ch.8"},
    "main_door":   {"ideal": ["North", "East", "North-East"], "acceptable": ["West"],    "avoid": ["South", "South-West"],  "vastu_ref": "Mansara Sh.10"},
    "living":      {"ideal": ["North", "East", "North-East"], "acceptable": ["North-West"], "avoid": ["South-West"],        "vastu_ref": "Brihat Samhita 53"},
    "bathroom":    {"ideal": ["North-West", "West"],    "acceptable": ["South-East"],    "avoid": ["North-East", "South-West"], "vastu_ref": "Vastu Saar Ch.11"},
    "dining":      {"ideal": ["West", "North-West"],    "acceptable": ["East", "North", "Center"], "avoid": ["North-East", "South-West"], "vastu_ref": "Vastu Saar Ch.6"},
    "staircase":   {"ideal": ["South", "South-West", "West"], "acceptable": ["North-West"], "avoid": ["North-East", "Center"], "vastu_ref": "Mayamatam Ch.20"},
    "basement":    {"ideal": ["North-West", "West", "South-West"], "acceptable": ["South", "North"], "avoid": ["North-East", "Center"], "vastu_ref": "Vastu Saar Ch.11"},
    "garage":      {"ideal": ["North-West", "West"],             "acceptable": ["South-West", "South"], "avoid": ["North-East", "Center"], "vastu_ref": "Mayamatam Ch.7"},
}


# ─────────────────────────────────────────────────────────────────────────
# Lookup helpers — used by astrovastu_engine
# ─────────────────────────────────────────────────────────────────────────
def get_lagna_directions(lagna: str) -> Optional[Dict[str, Any]]:
    return LAGNA_DIRECTION_MAP.get(lagna)


def get_rashi_bedhead(rashi: str) -> Optional[Dict[str, Any]]:
    return RASHI_BEDHEAD_MAP.get(rashi)


def get_nakshatra_door(nakshatra: str) -> Optional[Dict[str, Any]]:
    for group in NAKSHATRA_DOOR_GROUPS:
        if nakshatra in group["nakshatras"]:
            return group
    return None


def get_dasha_active_direction(dasha_planet: str) -> Optional[Dict[str, Any]]:
    return DASHA_ACTIVE_DIRECTION.get(dasha_planet)


def get_ishta_devata_for_planet(planet: str) -> Optional[Dict[str, Any]]:
    return ISHTA_DEVATA_MAP.get(planet)


def get_yantra_for_planet(planet: str) -> Optional[Dict[str, Any]]:
    return YANTRA_PRESCRIPTION.get(planet)


def get_lagna_lord(lagna: str) -> Optional[str]:
    return LAGNA_LORD.get(lagna)


def get_sign_lord(sign: str) -> Optional[str]:
    return SIGN_LORD.get(sign)


def get_bhavas_for_direction(direction: str) -> List[int]:
    """Bhavas linked to a compass sector (Astro-Vastu direction grid)."""
    d = (direction or "").strip()
    aliases = {
        "n": "North", "north": "North", "ne": "North-East", "north-east": "North-East",
        "northeast": "North-East", "e": "East", "east": "East",
        "se": "South-East", "south-east": "South-East", "southeast": "South-East",
        "s": "South", "south": "South", "sw": "South-West", "south-west": "South-West",
        "southwest": "South-West", "w": "West", "west": "West",
        "nw": "North-West", "north-west": "North-West", "northwest": "North-West",
    }
    key = aliases.get(d.lower(), d)
    for canon, bhavas in DIRECTION_BHAVA_GRID.items():
        if canon.lower() == key.lower():
            return list(bhavas)
    return DIRECTION_BHAVA_GRID.get(key, [])


def get_directions_for_bhava(bhava: int) -> List[str]:
    out: List[str] = []
    for direction, bhavas in DIRECTION_BHAVA_GRID.items():
        if bhava in bhavas:
            out.append(direction)
    return out


def get_house_room_catalog_entry(bhava: int) -> Optional[Dict[str, Any]]:
    for row in HOUSE_ROOM_MAPPING:
        if int(row.get("house") or 0) == int(bhava):
            return row
    return None


def get_planet_direction(planet: str) -> Optional[str]:
    return PLANET_DIRECTION.get(planet)


def get_color_for_lagna(lagna: str) -> Optional[Dict[str, Any]]:
    lord = LAGNA_LORD.get(lagna)
    if not lord:
        return None
    return COLOR_BY_LAGNA_LORD.get(lord)


def get_generic_room_rule(room_type: str) -> Optional[Dict[str, Any]]:
    return GENERIC_ROOM_IDEAL.get((room_type or "").lower().replace(" ", "_"))


def heading_to_direction(heading_deg: float) -> str:
    """Convert magnetometer 0-360° heading → 8-direction bucket."""
    if heading_deg is None:
        return "Unknown"
    h = heading_deg % 360
    # Each direction occupies a 45° bucket centered on its heading
    idx = int(((h + 22.5) % 360) // 45)
    return DIRECTIONS[idx]


# ─────────────────────────────────────────────────────────────────────────
# Quick stats for engine self-check (used by tests + admin debug)
# ─────────────────────────────────────────────────────────────────────────
def rule_db_stats() -> Dict[str, int]:
    return {
        "lagna_directions":    len(LAGNA_DIRECTION_MAP),
        "rashi_bedheads":      len(RASHI_BEDHEAD_MAP),
        "nakshatra_groups":    len(NAKSHATRA_DOOR_GROUPS),
        "planet_house_stress": len(PLANET_HOUSE_STRESS),
        "dasha_directions":    len(DASHA_ACTIVE_DIRECTION),
        "ishta_devatas":       len(ISHTA_DEVATA_MAP),
        "house_room_mappings": len(HOUSE_ROOM_MAPPING),
        "color_by_lord":       len(COLOR_BY_LAGNA_LORD),
        "yantras":             len(YANTRA_PRESCRIPTION),
        "tie_breakers":        len(TIE_BREAKER_RULES),
        "generic_room_ideals": len(GENERIC_ROOM_IDEAL),
    }
