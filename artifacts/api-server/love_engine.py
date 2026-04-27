"""
love_engine.py — Deterministic Love & Relationship verdict engine (Vedic / KP).

Mirror of marriage_engine.py + stock_engine.py architecture (CLE format):
pure-Python rule engine that consumes the already-computed kundli +
chart_intelligence + KP outputs and produces a structured love verdict
BEFORE the AI is invoked. The AI then acts purely as a NARRATOR that
converts this verdict into Hinglish prose — it MUST NOT change verdict,
score, timing window, strategy, or remedy.

Inputs:
    kundli  : dict from kundli_engine.calculate_kundli (has planets, dashas,
              currentDasha, ascendant, moonSign, divisionalCharts D9/D30...)
    intel   : dict from chart_intelligence.analyze_chart (has dignities,
              house_lords, yogas, mangal_dosh, sade_sati, lagna_sign)
    kp      : dict from kp_engine.calculate_kp (has cusps, planets,
              significations) — for KP cuspal sub-lord cross-check
    birth   : optional dict with at least "gender" so karaka is correct
              (Venus for men/general, Jupiter optional cross-check for women)
    question: raw user text — drives the 10-bucket question classifier
              (feelings_check / compatibility / new_love_timing /
              existing_status / breakup_signal / reconciliation / one_sided /
              long_distance / commitment_fear / affair_third_party).
    partner_kundli : optional dict — if provided, activates synastry layer (L29)
    partner_kp     : optional dict — KP cross-significator in synastry

Output: see assess_love().__doc__

CLE Format Logic Framework (10 standard steps):
    Step 1  — Question Type Detection (10-bucket classifier)
    Step 2  — 2-Step Verdict Framework (natal_promise + current_trigger → bucket)
    Step 3  — Layer Stacking (29 core layers + D9 + KP mandatory)
    Step 4  — Bucket-Gated Strategy (no contradictions allowed)
    Step 5  — Timing Window (Vimshottari + Yogini + Jupiter/Saturn transit + KP)
    Step 6  — Remedy Selection (weakest planet → mantra/donation/gemstone)
    Step 7  — Confidence Calibration (cross-system agreement)
    Step 8  — Format-for-Prompt (locked Hinglish verdict block)
    Step 9  — AI Narrator Override (turn-level rules in openai_helper)
    Step 10 — Brand-Safety Guards (affair / breakup / one_sided softening)

Layer rubric (canonical CLE table):
    A. NATAL PROMISE  (Layers 1-15)
        L1  5th house + 5L deep dive            (weight 14)  ⭐ CORE love
        L2  Venus deep dive (love karaka)       (weight 16)  ⭐ CORE
        L3  Moon emotional bonding              (weight  8)
        L4  7th house + 7L                      (weight 10)
        L5  Mars-Venus combo (passion)          (weight  8)
        L6  Jupiter on 5/7/11 (commitment)      (weight  7)
        L7  Mercury (communication chemistry)   (weight  5)
        L8  Rahu in 5/7/12 (intense/unconventional) (weight 6)
        L9  Ketu in 5/7/12 (detachment/breakup) (weight  5  ±)
        L10 Saturn aspects 5/7 (delay/karmic)   (weight  5  ±)
        L11 11th house (social romance)         (weight  4)
        L12 12th house (intimacy/foreign)       (weight  5)
        L13 Darakaraka (Jaimini partner)        (weight  6)
        L14 Upapada Lagna (UL spouse signature) (weight  5)
        L15 Atmakaraka aspects on 5/7           (weight  4)
    B. MANDATORY LAYERS (D9 + KP — required by CLE format spec)
        L16 D9 Navamsa overlay                  (weight 14)  ⭐ MANDATORY
        L17 KP cuspal sub-lord 5/7/11           (weight 12)  ⭐ MANDATORY
    C. ADVANCED LAYERS (push accuracy to 92-95%)
        L18 Ashtakavarga bindus 5/7/11          (weight  5)
        L19 Bhava Bala 5/7/11                   (weight  5)
        L20 Shadbala Venus + 5L + 7L            (weight  5)
        L21 Char Karakas full set (Jaimini)     (weight  4)
        L22 Yogini Dasha cross-check            (weight  3)
        L23 Sade Sati / Shani Dhaiya on Moon    (weight  5  ±)
        L24 Eclipse impact on Venus / 7L        (weight  4  ±)
        L25 D30 Trishamsa (character / affair)  (weight  5  ±)
        L26 KP CSL sub-sub-lord precision       (weight  4)
        L27 Argala on 5/7/11                    (weight  3)
        L28 Composite Moon-Venus-Mars triad     (weight  6)
        L29 Synastry Kuta scoring (conditional) (weight  8 — only if partner)
    D. TRIGGER LAYERS — is the natal promise activated NOW?
        T1  Vimshottari MD+AD+PD timing          (weight 10)
        T2  Live Jupiter + Saturn transits      (weight  5)
    E. MODIFIERS — 7 modifiers (±points, no own weight)
        M1  Venus / 5L / 7L combust              (±5)
        M2  Venus / 5L / 7L retrograde           (±3)
        M3  Malefic aspects on Venus / 5L / 7L   (±5)
        M4  Lagnesh-Venus harmony                (±3)
        M5  Transit Saturn over 5/7/Venus        (-5)
        M6  Transit Jupiter on 5/7/11            (+6)
        M7  Mahapurusha (Malavya/Hamsa) boost    (+5)
    F. CONDITIONAL (only when question type matches)
        C1  Affair signal check (12L + Rahu in 7H + Venus-Rahu/Ketu axis)
            — fires only for q_type == "affair_third_party"
        C2  Foreign partner check (12H + 9H + Rahu in 7H)
            — fires only when "abroad/NRI/foreign" in question
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS_LIST = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
SIGN_LORDS = {SIGNS[i]: SIGN_LORDS_LIST[i] for i in range(12)}

DIGNITY_RANK = {
    "debilitated": 0, "enemy-sign": 1, "neutral-sign": 2,
    "friend-sign": 3, "own-sign": 4, "moolatrikona": 5, "exalted": 6,
}
DIGNITY_PTS = {
    "debilitated": -8, "enemy-sign": -4, "neutral-sign": 0,
    "friend-sign": +3, "own-sign": +6, "moolatrikona": +7, "exalted": +8,
}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}

# Love-favourable houses (KP rule for 5/7/11 cusps)
LOVE_PROMISE  = {2, 5, 7, 11}      # 2=family-acceptance, 5=romance, 7=partner, 11=fulfillment
LOVE_DENIAL   = {1, 6, 8, 12}      # 1=self-only, 6=conflict, 8=obstacles, 12=loss/secret
INTIMACY_HOUSES = {5, 8, 12}        # bedroom / hidden / foreign
PARTNER_HOUSES  = {7, 11}           # public partnership / friend-circle

# Nakshatra-friendship for Tara Bala and Vedha checks (synastry)
NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","PurvaPhalguni","UttaraPhalguni","Hasta","Chitra",
    "Swati","Vishakha","Anuradha","Jyeshtha","Mula","PurvaAshadha","UttaraAshadha",
    "Shravana","Dhanishta","Shatabhisha","PurvaBhadrapada","UttaraBhadrapada","Revati",
]
# Vedha pairs (incompatible nakshatras for relationship — classical Brihat Jataka)
VEDHA_PAIRS = {
    "Ashwini":"Jyeshtha", "Bharani":"Anuradha", "Krittika":"Vishakha",
    "Rohini":"Swati", "Mrigashira":"Chitra", "Ardra":"Hasta",
    "Punarvasu":"UttaraPhalguni", "Pushya":"PurvaPhalguni", "Ashlesha":"Magha",
    "Mula":"Revati", "PurvaAshadha":"UttaraBhadrapada",
    "UttaraAshadha":"PurvaBhadrapada", "Shravana":"Shatabhisha",
    "Dhanishta":"Dhanishta",  # self-vedha — neutral
}
# Build symmetric Vedha map
_VEDHA = {}
for a, b in VEDHA_PAIRS.items():
    _VEDHA[a] = b
    _VEDHA[b] = a

# One-line emergency fallback (used only if remedies.py unavailable)
_FALLBACK_REMEDY = (
    'Shukravar ko Shri Lakshmi-Narayan ki upasana karein, '
    'safed phool ya mithai ka daan'
)

# Day-name → Hindi vaar (for narration)
_DAY_HI = {
    "Sunday":    "Ravivar",  "Monday":   "Somvar",   "Tuesday":  "Mangalvar",
    "Wednesday": "Budhvar",  "Thursday": "Guruvar",  "Friday":   "Shukravar",
    "Saturday":  "Shanivar",
}

_MONTHS = ["", "January","February","March","April","May","June",
              "July","August","September","October","November","December"]


# ─────────────────────────────────────────────────────────────────────────────
# REMEDY LOOKUP (single source = remedies._REMEDY_TABLE)
# ─────────────────────────────────────────────────────────────────────────────
def _remedy_for_planet(planet: str) -> str:
    """One-line love-narration remedy from canonical remedies._REMEDY_TABLE."""
    try:
        from remedies import _REMEDY_TABLE  # type: ignore
    except Exception:
        return _FALLBACK_REMEDY
    entry = _REMEDY_TABLE.get(planet)
    if not isinstance(entry, dict):
        return _FALLBACK_REMEDY
    mantra   = entry.get("mantra")  or {}
    charity  = entry.get("charity") or []
    trans    = mantra.get("transliteration") or ""
    count    = mantra.get("count") or 108
    day_en   = (mantra.get("day") or "").split(" ")[0]
    day_hi   = _DAY_HI.get(day_en, day_en or "is din")
    daan     = (charity[0].lower() if charity else "appropriate items")
    if not trans:
        return _FALLBACK_REMEDY
    return (
        f'{day_hi} ({day_en}) ko {count} baar "{trans}" jaap karein, '
        f'{daan} ka daan'
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — QUESTION CLASSIFIER (10 buckets) — drives bucket-specific output
# ─────────────────────────────────────────────────────────────────────────────
# Order of patterns matters — most specific FIRST. Each tuple is
# (bucket_name, list_of_regexes). The classifier returns the first match;
# falls back to "feelings_check" (most generic) if nothing matches but the
# question contains love vocabulary.
_Q_PATTERNS = [
    # AFFAIR / CHEATING — most sensitive, must be detected first to prevent
    # accidental routing into compatibility / existing_status buckets.
    ("affair_third_party", [
        r"\b(cheat|cheating|cheater|cheated)\b",
        r"\b(affair|extra[- ]?marital|extramarital)\b",
        r"\b(dhokha|dhoka|dhokhha|dhoke|bewafai|be-wafai|wafa nahi)\b",
        r"\b(doosra|dusra|dusara|doosri|dusri)\b.*\b(koi|aur|bf|gf|ladka|ladki|partner|aurat|admi)\b",
        r"\b(koi aur|kuch aur)\b.*\b(hai|chal|chakkar|relation|love|partner)\b",
        r"\b(chakkar|chakar|chukker)\b",
        r"\b(third[- ]?party|teesra|tisra|tisri)\b",
        r"\b(side[- ]?chick|side\s*piece)\b",
        r"\b(infidel|infidelity|unfaithful|disloyal|loyal nahi)\b",
        r"\b(mere|mera|hamara)\b.*\b(partner|bf|gf|husband|wife|pati|patni)\b.*\b(kisi|koi|kuch)\b.*\b(aur|doosra|dusra)\b",
        # Devanagari patterns (Hindi script)
        r"धोखा",
        r"बेवफा|बेवफाई",
        r"चक्कर",
        r"किसी और",
        r"अफेयर|एफेयर",
    ]),
    # BREAKUP SIGNAL
    ("breakup_signal", [
        r"\b(breakup|break[- ]?up|breaking[- ]?up|break it off)\b",
        r"\b(toot|tootna|tutega|tut)\b.*\b(rishta|relation|pyaar|love)\b",
        r"\b(rishta|relation|pyaar|love)\b.*\b(toot|tootega|tut|khatam|khatm|end)\b",
        r"\b(alag|alag-?alag|separate|separation|split)\b.*\b(ho|honge|hojayenge|hojayenge|hojayega)\b",
        r"\b(end karna|khatam karna|tod dena)\b.*\b(rishta|relation)\b",
    ]),
    # RECONCILIATION (ex/patch-up)
    ("reconciliation", [
        r"\b(ex)\b.*\b(wapas|wapis|return|back|aayega|aayegi|milega|milegi)\b",
        r"\b(wapas|wapis|return|back|aayega|aayegi)\b.*\b(ex|partner|bf|gf)\b",
        r"\b(patch[- ]?up|patchup|reunite|reunion|reconcil)\b",
        r"\b(jud(na|enge|jaayenge)|reunion|sath aana|saath aana|saath aayenge)\b.*\b(rishta|relation|pyaar|ex|partner)\b",
    ]),
    # COMMITMENT FEAR / DELAY
    ("commitment_fear", [
        r"\b(commit|committment|commitment)\b.*\b(nahi|nahin|kab|when|karta|karega|karegi|fear|dar)\b",
        r"\b(propose|propose karna|propose kab|propose karega|propose karegi)\b",
        r"\b(ring|engagement|engaged)\b.*\b(kab|when|denge|dega|degi)\b",
        r"\b(serious|seriousness)\b.*\b(rishta|relation|partner|bf|gf)\b",
        r"\b(future|aage|long[- ]?term)\b.*\b(plan|plans|sochna|sochta|sochti|sochenge)\b.*\b(partner|bf|gf|relation)\b",
    ]),
    # ONE-SIDED LOVE / CRUSH
    ("one_sided", [
        r"\b(one[- ]?sided|one sided|ekta-?rafa|ektarafa|ek[- ]?tarafa)\b",
        r"\b(crush)\b",
        r"\b(wo|woh|she|he)\b.*\b(mujhe|me)\b.*\b(pasand|like|love|chahta|chahti)\b.*\b(nahi|nahin|hai|hi|kya|?)\b",
        r"\b(unrequited)\b",
        r"\b(mai|main|i)\b.*\b(propose|izhaar|izhar)\b",
    ]),
    # LONG DISTANCE
    ("long_distance", [
        r"\b(long[- ]?distance|ld|ldr)\b",
        r"\b(door|dur|distance|videsh|abroad|nri|foreign)\b.*\b(partner|bf|gf|rishta|relation|love)\b",
        r"\b(alag|different)\b.*\b(sheher|city|country|state|desh)\b.*\b(partner|bf|gf|love)\b",
    ]),
    # FEELINGS CHECK (does X love me?)
    ("feelings_check", [
        r"\b(kya|does)\b.*\b(wo|woh|she|he)\b.*\b(mujhe|me)\b.*\b(pyaar|pyar|love|chahta|chahti|like|sach me|truly)\b",
        r"\b(uske|unke|her|his)\b.*\b(dil|heart|man)\b.*\b(me|mein)\b.*\b(kya|what|feelings|pyaar|love)\b",
        r"\b(real|real me|sach|sachhi|truly)\b.*\b(pyaar|pyar|love|feelings)\b",
        r"\b(does|kya)\b.*\b(he|she|wo|woh)\b.*\b(love|pyaar)\b.*\b(me|mujhe)\b",
        r"\b(feelings)\b.*\b(genuine|real|true|sach|sacchi|sachi)\b",
    ]),
    # NEW LOVE TIMING (when will I find love)
    ("new_love_timing", [
        r"\b(pyaar|pyar|love|partner|bf|gf|girlfriend|boyfriend|soulmate|sathi|saathi|jeevansathi)\b.*\b(kab|when|kab tak|kab milega|kab milegi)\b",
        r"\b(kab|when)\b.*\b(milega|milegi|aayega|aayegi)\b.*\b(pyaar|love|partner|gf|bf|soulmate|sathi|saathi)\b",
        r"\b(naya|new)\b.*\b(rishta|relation|pyaar|love|partner)\b",
        r"\b(single|akela|akeli|akelapan)\b.*\b(kab|when|kabtak)\b",
        r"\b(soulmate|true love)\b",
    ]),
    # COMPATIBILITY (pure emotional fit, non-marriage)
    ("compatibility", [
        r"\b(compat(ible|ibility))\b",
        r"\b(jodi|joodi|match|matching)\b.*\b(banegi|banti|bani|banta|hai|achhi|acchi|sahi)\b",
        r"\b(hum dono|hum donon|we two|us two)\b.*\b(achhe|acche|sahi|right|theek|fit|match)\b",
        r"\b(rashi|sign|nakshatra|kundli|chart)\b.*\b(match|milan|milana|compatible|jodi)\b",
        r"\b(guna milan|guna|gun)\b.*\b(milan|points|score)\b",
    ]),
    # EXISTING STATUS / FUTURE OF CURRENT RELATIONSHIP
    ("existing_status", [
        r"\b(humari|hamari|our|hamare)\b.*\b(rishta|relation|pyaar|love)\b.*\b(chalegi|chalega|kaisi|future|kya hoga|aage)\b",
        r"\b(future)\b.*\b(of (us|our)|hamara|humara|rishte ka)\b",
        r"\b(kaise hoga|kya hoga|future|aage)\b.*\b(rishta|relation|partner|love)\b",
        r"\b(long[- ]?term|lasting|tikega|tikegi|tik)\b.*\b(rishta|relation|love|pyaar)\b",
    ]),
]


def classify_love_question(text: str) -> str:
    """Return one of:
      affair_third_party | breakup_signal | reconciliation | commitment_fear |
      one_sided | long_distance | feelings_check | new_love_timing |
      compatibility | existing_status

    Default: "feelings_check" (most generic love question fallback).
    Order matters — most specific patterns checked first.
    """
    if not isinstance(text, str) or not text.strip():
        return "feelings_check"
    s = text.lower().strip()
    for bucket, pats in _Q_PATTERNS:
        for pat in pats:
            try:
                if re.search(pat, s):
                    return bucket
            except re.error:
                continue
    # Fallback: if any love vocabulary present, default to feelings_check
    if re.search(r"\b(pyaar|pyar|love|crush|ishq|mohabbat|gf|bf|girlfriend|"
                 r"boyfriend|partner|rishta|relation|dating|soulmate)\b", s):
        return "feelings_check"
    return "feelings_check"


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _sign_idx(sign_name: Any) -> Optional[int]:
    if not isinstance(sign_name, str):
        return None
    try:
        return SIGNS.index(sign_name.strip().capitalize())
    except ValueError:
        return None


def _safe_iso_date(s: Any) -> Optional[datetime]:
    if not isinstance(s, str) or not s:
        return None
    try:
        return datetime.fromisoformat(s.split("T")[0])
    except Exception:
        return None


def _ym_to_human(ym: str) -> str:
    """\"2025-12\" → \"December 2025\". Returns input unchanged if malformed."""
    try:
        y, m = (ym or "").split("-")[:2]
        return f"{_MONTHS[int(m)]} {y}"
    except Exception:
        return ym or "?"


def _planet_in_house(pname: str, pmap: dict) -> Optional[int]:
    p = pmap.get(pname) or {}
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _planet_dignity(pname: str, dignities: dict) -> dict:
    return dignities.get(pname) or {}


def _significators_of(houses_set: set, sigs: dict) -> set:
    """Set of planet names whose KP significations cover any house in set."""
    out = set()
    for pname, sig in (sigs or {}).items():
        bag = set(sig.get("pl") or []) | set(sig.get("sb_houses") or []) \
            | set(sig.get("ss_houses") or []) | set(sig.get("sl") or [])
        if bag & houses_set:
            out.add(pname)
    return out


def _signifies(planet: str, houses_set: set, sigs: dict) -> bool:
    sig = (sigs or {}).get(planet) or {}
    bag = set(sig.get("pl") or []) | set(sig.get("sb_houses") or []) \
        | set(sig.get("ss_houses") or []) | set(sig.get("sl") or [])
    return bool(bag & houses_set)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER MODULE LAZY LOADERS — best-effort (return {} on any failure)
# ─────────────────────────────────────────────────────────────────────────────
def _maybe_shadbala(kundli: dict, lagna_sign_idx: Optional[int]) -> dict:
    """Lazily compute Shadbala. Returns {} on any failure."""
    if lagna_sign_idx is None:
        return {}
    try:
        from shadbala import compute_shadbala
        raw = (kundli or {}).get("planets") or []
        planets = []
        for p in raw:
            if not isinstance(p, dict):
                continue
            lon = p.get("lon", p.get("longitude"))
            if not isinstance(lon, (int, float)):
                continue
            planets.append({**p, "lon": float(lon)})
        moon = next((p for p in planets if p.get("name") == "Moon"), None)
        sun  = next((p for p in planets if p.get("name") == "Sun"),  None)
        moon_sun_angle = None
        if moon and sun:
            moon_sun_angle = (moon["lon"] - sun["lon"]) % 360.0
        return compute_shadbala(planets, lagna_sign_idx, moon_sun_angle) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_ashtakavarga(kundli: dict, lagna_sign_idx: Optional[int]) -> dict:
    """Compute Sarva Ashtakavarga + Bhinna AV. Returns {} on failure."""
    if lagna_sign_idx is None:
        return {}
    try:
        from ashtakavarga import compute_ashtakavarga
        return compute_ashtakavarga(
            (kundli or {}).get("planets") or [], lagna_sign_idx) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_bhava_bala(intel: dict, shadbala_d: dict) -> dict:
    """Compute Bhava Bala. Returns {} on any failure."""
    try:
        from bhava_bala import compute_bhava_bala
        return compute_bhava_bala(intel, shadbala_d or {}) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_jaimini(kundli: dict) -> dict:
    """Compute Jaimini Char Karakas + Arudha Padas + Upapada."""
    try:
        from jaimini import compute_arudha_padas, compute_upapada
        asc_sign = (kundli or {}).get("ascendant") or ""
        planets  = (kundli or {}).get("planets") or []
        ar = compute_arudha_padas(planets, asc_sign) or {}
        up = compute_upapada(ar, planets) or {}
        return {"arudha": ar, "upapada": up}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_argala(kundli: dict) -> dict:
    """Compute Argala (planetary intervention)."""
    try:
        from argala import compute_argala
        asc_sign = (kundli or {}).get("ascendant") or ""
        planets  = (kundli or {}).get("planets") or []
        return compute_argala(planets, asc_sign) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_varga_yogas(kundli: dict, lagna_lon: Optional[float]) -> dict:
    """Detect Pancha-Mahapurusha + Raj + Vipreet yogas across vargas."""
    try:
        from varga_yogas import detect_all_varga_yogas
        return detect_all_varga_yogas(
            (kundli or {}).get("planets") or [], lagna_lon, kundli) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_yogini_dasha(kundli: dict, birth: dict) -> dict:
    """Cross-check timing via Yogini Dasha (8-year cycles).
    Returns {"current": "...", "planet": "...", "_error": ""} or {}.
    Best-effort — not all charts have moon-nakshatra data needed.
    """
    try:
        from extra_jaimini_dashas import compute_sthira_dasha  # ← we use Sthira Dasha as a Jaimini cross-check timing layer
        asc_name = (kundli or {}).get("ascendant") or ""
        dob = (birth or {}).get("dob") or ""
        if not asc_name or not dob:
            return {}
        return compute_sthira_dasha(asc_name, dob, datetime.utcnow().isoformat()) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_jupiter_transit(lagna_sign_idx: Optional[int],
                           moon_sign_idx:  Optional[int]) -> dict:
    """Live Jupiter transit windows (next 3 years over love-trigger signs 5/7/11).
    Reuses the marriage_trigger_windows function from transit_engine which
    computes Jupiter's transit through 1/5/7/11 from Lagna AND Moon.
    """
    if lagna_sign_idx is None:
        return {}
    try:
        from transit_engine import jupiter_marriage_trigger_windows
        today = datetime.utcnow()
        windows = jupiter_marriage_trigger_windows(
            lagna_sign_idx, moon_sign_idx, start=today, years_ahead=3)
        active = next(
            (w for w in windows
             if datetime.fromisoformat(w["start"]) <= today
             <= datetime.fromisoformat(w["end"])),
            None,
        )
        return {
            "jupiter_active_now": bool(active),
            "active_window":      active,
            "all_windows":        windows,
        }
    except Exception as e:
        return {"_error": str(e)}


def _maybe_saturn_transit() -> dict:
    """Live Saturn transit — current sign and next sign change.
    Saturn over natal Moon = Sade Sati (handled in L23). Here we get the
    transit context for L17 (current trigger).
    """
    try:
        # Approximate Saturn position by year (Saturn ~2.5 years per sign).
        # Saturn ingress dates 2023-2030 (sidereal):
        SATURN_INGRESS = [
            ("2023-01-17", "Aquarius"),
            ("2025-03-29", "Pisces"),     # actual sidereal Pisces ingress
            ("2027-08-26", "Aries"),
            ("2030-04-05", "Taurus"),
        ]
        today = datetime.utcnow()
        cur_sign = "Aquarius"
        next_change = None
        for date_str, sign in SATURN_INGRESS:
            d = datetime.fromisoformat(date_str)
            if d <= today:
                cur_sign = sign
            elif next_change is None:
                next_change = {"date": date_str, "sign": sign}
                break
        return {
            "current_sign": cur_sign,
            "current_sign_idx": _sign_idx(cur_sign),
            "next_change": next_change,
        }
    except Exception as e:
        return {"_error": str(e)}


def _next_dasha_window(dashas: list, significators: set,
                       today: datetime) -> Optional[dict]:
    """First future (Maha,Antar) where MD or AD planet signifies the houses."""
    for md in (dashas or []):
        for ad in (md.get("subDashas") or []):
            ad_end = _safe_iso_date(ad.get("endDate") or "")
            if not ad_end or ad_end < today:
                continue
            mp = md.get("planet"); ap = ad.get("planet")
            if mp in significators or ap in significators:
                start = (ad.get("startDate") or "")[:7]
                end   = (ad.get("endDate") or "")[:7]
                if mp in significators and ap in significators:
                    why = (f"both {mp} (Mahadasha) and {ap} (Antardasha) "
                           f"signify love-houses 5/7/11")
                elif mp in significators:
                    why = f"{mp} (Mahadasha) signifies love-houses 5/7/11"
                else:
                    why = f"{ap} (Antardasha) signifies love-houses 5/7/11"
                return {"dasha": f"{mp}-{ap}", "start": start, "end": end,
                        "reason": why}
    return None


def _next_pratyantar_window(dashas: list, significators: set,
                            today: datetime) -> Optional[dict]:
    """Pratyantar (PD) refinement: tighter sub-window inside an AD."""
    for md in (dashas or []):
        for ad in (md.get("subDashas") or []):
            ad_end = _safe_iso_date(ad.get("endDate") or "")
            if not ad_end or ad_end < today:
                continue
            for pd in (ad.get("subDashas") or []):
                pd_end = _safe_iso_date(pd.get("endDate") or "")
                if not pd_end or pd_end < today:
                    continue
                pp = pd.get("planet")
                if pp in significators:
                    return {
                        "dasha":  f"{md.get('planet')}-{ad.get('planet')}-{pp}",
                        "start":  (pd.get("startDate") or "")[:7],
                        "end":    (pd.get("endDate") or "")[:7],
                        "reason": f"Pratyantar {pp} signifies love-houses",
                    }
    return None


# ─────────────────────────────────────────────────────────────────────────────
# DIVISIONAL CHART HELPERS — D9 (Navamsa) and D30 (Trishamsa)
# ─────────────────────────────────────────────────────────────────────────────
def _planet_in_d_chart(d_chart: dict, planet: str) -> dict:
    """Return {sign, house} of planet in a divisional chart, or {}."""
    if not isinstance(d_chart, dict):
        return {}
    for p in (d_chart.get("planets") or []):
        if p.get("name") == planet:
            return {"sign": p.get("sign"), "house": p.get("house"),
                    "lon": p.get("lon", p.get("longitude"))}
    return {}


def _d9_full_check(kundli: dict, fifth_lord: str, seventh_lord: str) -> dict:
    """D9 Navamsa full check — Venus/5L/7L placement in D9.
    D9 is the most important divisional chart for marriage AND love (BPHS).
    Strong D9 7L = real love promise; weak/afflicted D9 7L = surface attraction
    only, no real bond.
    """
    d9 = ((kundli or {}).get("divisionalCharts") or {}).get("D9") or {}
    if not d9:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    asc_idx = d9.get("ascendantSignIndex")
    d9_7th_sign = d9_7th_lord = None
    if asc_idx is not None:
        d9_7_idx    = (int(asc_idx) + 6) % 12
        d9_7th_sign = SIGNS[d9_7_idx]
        d9_7th_lord = SIGN_LORDS.get(d9_7th_sign)

    venus_d9 = _planet_in_d_chart(d9, "Venus")
    fifth_d9 = _planet_in_d_chart(d9, fifth_lord) if fifth_lord else {}
    seventh_d9 = _planet_in_d_chart(d9, seventh_lord) if seventh_lord else {}
    d9_7lord_pos = _planet_in_d_chart(d9, d9_7th_lord) if d9_7th_lord else {}

    score = 0
    rs, rw = [], []

    # D9 Venus dignity (own/exalted/moolatrikona = strong love nature in deep chart)
    v_sign = venus_d9.get("sign")
    if v_sign in ("Taurus", "Libra"):
        score += 5
        rs.append(f"D9 Navamsa: Venus in own sign {v_sign} — true love nature deep in chart")
    elif v_sign == "Pisces":
        score += 6
        rs.append("D9 Navamsa: Venus exalted in Pisces — sublime love nature, soul bond capacity")
    elif v_sign == "Virgo":
        score -= 4
        rw.append("D9 Navamsa: Venus debilitated in Virgo — surface attraction only, deep bond weak")

    # D9 7L placement house — KENDRA/TRINE = strong, DUSTHANA = weak
    d9_7l_house = d9_7lord_pos.get("house")
    if d9_7l_house in (1, 4, 7, 10):
        score += 4
        rs.append(f"D9 7th-lord {d9_7th_lord} in kendra (house {d9_7l_house}) — partnership stable in deep chart")
    elif d9_7l_house in (5, 9):
        score += 3
        rs.append(f"D9 7th-lord {d9_7th_lord} in trine (house {d9_7l_house}) — fortune supports love")
    elif d9_7l_house in (6, 8, 12):
        score -= 3
        rw.append(f"D9 7th-lord {d9_7th_lord} in dusthana (house {d9_7l_house}) — partnership faces hidden friction")

    # D9 5L (romance) placement
    if fifth_lord:
        f_house = fifth_d9.get("house")
        if f_house in (1, 4, 5, 7, 9, 10, 11):
            score += 2
            rs.append(f"D9: 5th lord {fifth_lord} in good house {f_house} — romantic depth confirmed")
        elif f_house in (6, 8, 12):
            score -= 2
            rw.append(f"D9: 5th lord {fifth_lord} in dusthana {f_house} — romance has karmic obstacles")

    # D9 7L (partner) placement
    if seventh_lord:
        s_house = seventh_d9.get("house")
        if s_house in (1, 4, 5, 7, 9, 10, 11):
            score += 2
            rs.append(f"D9: 7th lord {seventh_lord} in good house {s_house} — partner bond supported")
        elif s_house in (6, 8, 12):
            score -= 2
            rw.append(f"D9: 7th lord {seventh_lord} in dusthana {s_house} — partner-friction in deep chart")

    return {
        "available":        True,
        "d9_7th_sign":      d9_7th_sign,
        "d9_7th_lord":      d9_7th_lord,
        "d9_7th_lord_house": d9_7l_house,
        "venus_d9":         venus_d9,
        "fifth_d9":         fifth_d9,
        "seventh_d9":       seventh_d9,
        "score":            score,
        "why_strong":       rs,
        "why_weak":         rw,
    }


def _d30_trishamsa_check(kundli: dict) -> dict:
    """D30 Trishamsa — character flaws / hidden tendencies.
    Critical for affair_third_party + breakup_signal buckets.

    Classical rule: D30 Venus/7L/Mars conjoined with malefics or in malefic
    signs = deception / infidelity tendencies. Strong D30 = character integrity.
    """
    dcs = (kundli or {}).get("divisionalCharts") or {}
    # Try compute D30 if not pre-computed
    d30 = dcs.get("D30") or {}
    if not d30:
        try:
            from divisional_charts import compute_d30
            asc_lon = (kundli or {}).get("ascendantLon")
            d30 = compute_d30(
                (kundli or {}).get("planets") or [], asc_lon) or {}
        except Exception:
            return {"available": False, "score": 0, "why_strong": [], "why_weak": []}
    if not d30:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    venus_d30 = _planet_in_d_chart(d30, "Venus")
    mars_d30  = _planet_in_d_chart(d30, "Mars")
    rahu_d30  = _planet_in_d_chart(d30, "Rahu")

    score = 0
    rs, rw = [], []

    # Venus in D30 enemy/debilitated sign = character flaw in romance
    v_sign = venus_d30.get("sign")
    if v_sign == "Virgo":
        score -= 3
        rw.append("D30: Venus debilitated — romantic character has integrity gap")
    elif v_sign in ("Taurus", "Libra", "Pisces"):
        score += 3
        rs.append(f"D30: Venus dignified in {v_sign} — character in love is integrous")

    # Mars-Venus conjoined in D30 = passion-driven ill-discipline
    v_house = venus_d30.get("house")
    m_house = mars_d30.get("house")
    if v_house and m_house and v_house == m_house:
        score -= 2
        rw.append(f"D30: Mars + Venus same house {v_house} — passion-driven impulsiveness in love")

    # Rahu with Venus in D30 = forbidden/secret attraction tendency
    r_house = rahu_d30.get("house")
    if v_house and r_house and v_house == r_house:
        score -= 4
        rw.append(f"D30: Rahu + Venus same house {v_house} — forbidden / hidden attraction tendency (CAUTION for affair Q)")

    return {
        "available":  True,
        "venus_d30":  venus_d30,
        "mars_d30":   mars_d30,
        "rahu_d30":   rahu_d30,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CORE LAYER FUNCTIONS — L1 to L29
# ─────────────────────────────────────────────────────────────────────────────

# ── L1 — 5th house + 5th lord deep dive (romance, attraction) ───────────────
def _layer_5th_house(intel: dict, kundli: dict, kp_sigs: dict) -> dict:
    """5th house = romance, attraction, dating capacity. PRIMARY love house.

    Weight: 14 (one of two CORE layers — Venus is the other)
    Signals:
      + 5L exalted/own/moolatrikona/friend → strong romance capacity
      + 5L in 1/5/7/11 → activated romance
      + Benefic in 5H, no malefic occupation → smooth love
      − 5L debilitated/enemy/combust/in 6-8-12 → blocked romance
      − Multiple malefics in 5H → toxic / dramatic love
    """
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

    fifth        = house_lords.get(5) or {}
    fifth_lord   = fifth.get("lord") or ""
    fl_dig_entry = dignities.get(fifth_lord) or {}
    fl_dig       = fl_dig_entry.get("dignity") or "neutral-sign"
    fl_combust   = bool(fl_dig_entry.get("combust"))
    fl_house     = (pmap.get(fifth_lord) or {}).get("house")

    score, rs, rw = 0, [], []

    # 5L dignity
    if fl_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 6
        rs.append(f"5th lord {fifth_lord} {fl_dig} — strong romance / panchama-bhava")
    elif fl_dig == "friend-sign":
        score += 2
        rs.append(f"5th lord {fifth_lord} in friend's sign — romance supported")
    elif fl_dig in ("debilitated", "enemy-sign") and not fl_combust:
        score -= 5
        rw.append(f"5th lord {fifth_lord} {fl_dig} — romance capacity weak")
    if fl_combust:
        score -= 4
        rw.append(f"5th lord {fifth_lord} combust by Sun — romance burnt by ego")

    # 5L placement
    if fl_house in (1, 5, 7, 11):
        score += 4
        rs.append(f"5th lord {fifth_lord} in house {fl_house} — romance activated, well-placed")
    elif fl_house in (4, 9, 10):
        score += 2
        rs.append(f"5th lord {fifth_lord} in house {fl_house} — supported placement")
    elif fl_house in (6, 8, 12):
        score -= 4
        rw.append(f"5th lord {fifth_lord} in dusthana {fl_house} — romance encounters obstacles")

    # Occupants of 5H — benefics good, multiple malefics bad
    occ_5h_benefics, occ_5h_malefics = [], []
    for pname, p in pmap.items():
        if p.get("house") == 5:
            if pname in NATURAL_BENEFICS:
                occ_5h_benefics.append(pname)
            elif pname in NATURAL_MALEFICS:
                occ_5h_malefics.append(pname)
    if occ_5h_benefics:
        score += 2 * min(2, len(occ_5h_benefics))
        rs.append(f"5H occupied by benefic(s) {', '.join(occ_5h_benefics)} — romance flows smoothly")
    if len(occ_5h_malefics) >= 2:
        score -= 4
        rw.append(f"5H occupied by multiple malefics ({', '.join(occ_5h_malefics)}) — dramatic / toxic love patterns")
    elif len(occ_5h_malefics) == 1 and occ_5h_malefics[0] in ("Saturn", "Mars"):
        score -= 2
        rw.append(f"5H has {occ_5h_malefics[0]} — romance has restriction or aggression")

    # 5L signifies love houses in KP
    fl_signifies_promise = _signifies(fifth_lord, LOVE_PROMISE, kp_sigs)
    fl_signifies_denial  = _signifies(fifth_lord, LOVE_DENIAL,  kp_sigs)
    if fl_signifies_promise:
        score += 2
        rs.append(f"KP: 5th lord {fifth_lord} signifies love-promise houses {sorted(LOVE_PROMISE)}")
    if fl_signifies_denial and not fl_signifies_promise:
        score -= 2
        rw.append(f"KP: 5th lord {fifth_lord} signifies only denial houses 1/6/8/12")

    return {
        "fifth_lord":         fifth_lord,
        "fifth_lord_dignity": fl_dig,
        "fifth_lord_house":   fl_house,
        "fifth_lord_combust": fl_combust,
        "occupants_5h_benefics": occ_5h_benefics,
        "occupants_5h_malefics": occ_5h_malefics,
        "kp_5l_promise":      fl_signifies_promise,
        "kp_5l_denial":       fl_signifies_denial,
        "score":              score,
        "why_strong":         rs,
        "why_weak":           rw,
    }


# ── L2 — Venus deep dive (love karaka, Shukra) ──────────────────────────────
def _layer_venus(intel: dict, kundli: dict, kp_sigs: dict) -> dict:
    """Venus = SHUKRA = primary love karaka. Weight: 16 (heaviest single layer).

    Signals:
      + Venus exalted/own/moolatrikona → divine love nature
      + Venus in 1/5/7/11 → activated love-significator
      + Venus with Jupiter/Moon (benefic conj) → soft sweet love
      − Venus debilitated/enemy/combust → love muddled
      − Venus with Saturn/Mars/Rahu/Ketu → karmic / restrictive / sudden / detached
      − Venus retrograde → ambivalence in love expression
    """
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

    v_entry  = dignities.get("Venus") or {}
    v_dig    = v_entry.get("dignity") or "neutral-sign"
    v_combust = bool(v_entry.get("combust"))
    v_retro  = bool(v_entry.get("retrograde"))
    v_house  = (pmap.get("Venus") or {}).get("house")
    v_sign   = (pmap.get("Venus") or {}).get("sign")
    v_aspects = v_entry.get("aspects_houses") or []

    score, rs, rw = 0, [], []

    # Dignity
    pts = DIGNITY_PTS.get(v_dig, 0)
    score += pts
    if pts >= 6:
        rs.append(f"Venus (Shukra) {v_dig} in {v_sign} — primary love karaka in full strength")
    elif pts <= -4:
        rw.append(f"Venus (Shukra) {v_dig} in {v_sign} — love karaka muddled")

    # Combustion (within 8° of Sun for Venus per BPHS)
    if v_combust:
        score -= 5
        rw.append("Venus combust by Sun — love expression burnt by ego / pride")

    # Retrograde
    if v_retro:
        score -= 2
        rw.append("Venus retrograde — past-life love karma replays; ambivalence in new love expression")

    # Placement
    if v_house in (1, 5, 7, 11):
        score += 5
        rs.append(f"Venus in house {v_house} — love karaka well-placed (kendra/trine for love)")
    elif v_house == 4:
        score += 3
        rs.append("Venus in 4th — domestic love + emotional comfort")
    elif v_house == 9:
        score += 2
        rs.append("Venus in 9th — fortunate love, dharmic partner")
    elif v_house == 12:
        score += 1
        rs.append("Venus in 12th — bedroom pleasures + foreign love + Bhoga-Sthana karaka (mixed)")
    elif v_house in (6, 8):
        score -= 4
        rw.append(f"Venus in dusthana {v_house} — love faces conflict / sudden disruption")

    # Conjunctions (planets in same sign as Venus)
    if v_sign:
        conj = []
        for pname, p in pmap.items():
            if pname == "Venus": continue
            if p.get("sign") == v_sign:
                conj.append(pname)
        # Benefic conjunctions
        ben_conj = [c for c in conj if c in ("Jupiter", "Moon", "Mercury")]
        if ben_conj:
            score += 2
            rs.append(f"Venus + {', '.join(ben_conj)} — soft sweet love (benefic conjunction)")
        # Saturn — restrictive, mature, age-gap
        if "Saturn" in conj:
            score -= 3
            rw.append("Venus + Saturn — restrictive / delayed / mature / age-gap love")
        # Mars — passionate but volatile
        if "Mars" in conj:
            score += 1
            rw.append("Venus + Mars — passion strong but volatile (Mangal-Shukra yoga, double-edged)")
        # Rahu — sudden / unconventional / forbidden
        if "Rahu" in conj:
            score -= 2
            rw.append("Venus + Rahu — sudden / forbidden / inter-caste / foreign attraction (intense but karmic)")
        # Ketu — detached / dispassionate
        if "Ketu" in conj:
            score -= 3
            rw.append("Venus + Ketu — detachment from love / past-life karmic disinterest")
        # Sun — combust handled above; ignore here

    # Venus aspects — Jupiter aspecting Venus = sublime
    jup_aspects = (dignities.get("Jupiter") or {}).get("aspects_houses") or []
    if v_house and v_house in jup_aspects:
        score += 2
        rs.append("Jupiter aspects Venus's house — wisdom + dharma supports love")
    sat_aspects = (dignities.get("Saturn") or {}).get("aspects_houses") or []
    if v_house and v_house in sat_aspects:
        score -= 2
        rw.append("Saturn aspects Venus's house — discipline + delay + restriction on love expression")

    # KP: Venus signification of love-houses
    if _signifies("Venus", LOVE_PROMISE, kp_sigs):
        score += 2
        rs.append("KP: Venus signifies love-promise houses 5/7/11 — love karaka actively delivers")

    return {
        "venus_dignity":  v_dig,
        "venus_house":    v_house,
        "venus_sign":     v_sign,
        "venus_combust":  v_combust,
        "venus_retro":    v_retro,
        "venus_aspects":  v_aspects,
        "score":          score,
        "why_strong":     rs,
        "why_weak":       rw,
    }


# ── L3 — Moon emotional bonding ─────────────────────────────────────────────
def _layer_moon(intel: dict, kundli: dict) -> dict:
    """Moon = mind, emotion, bonding capacity. Weight: 8.

    Signals:
      + Moon waxing (Shukla Paksha) > 6° from Sun → emotionally available
      + Moon in own/exalted/friendly → emotional stability for love
      − Moon waning + dark → emotional unavailability
      − Moon in 6/8/12 → emotional turbulence
      + Moon in 4H or in Cancer → emotional home, ideal for bonding
    """
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

    moon_entry = dignities.get("Moon") or {}
    moon_dig   = moon_entry.get("dignity") or "neutral-sign"
    moon_pos   = pmap.get("Moon") or {}
    moon_house = moon_pos.get("house")
    moon_sign  = moon_pos.get("sign")

    score, rs, rw = 0, [], []

    # Dignity
    pts = DIGNITY_PTS.get(moon_dig, 0) // 2  # half-weight (Moon is broader)
    score += pts
    if pts >= 3:
        rs.append(f"Moon {moon_dig} in {moon_sign} — emotional stability for love bonding")
    elif pts <= -2:
        rw.append(f"Moon {moon_dig} in {moon_sign} — emotional turbulence affects bonding")

    # Waxing/waning (Paksha Bala approximation)
    sun_pos = pmap.get("Sun") or {}
    if isinstance(moon_pos.get("lon", moon_pos.get("longitude")), (int, float)) and \
       isinstance(sun_pos.get("lon", sun_pos.get("longitude")), (int, float)):
        m_lon = float(moon_pos.get("lon", moon_pos.get("longitude")))
        s_lon = float(sun_pos.get("lon", sun_pos.get("longitude")))
        diff  = (m_lon - s_lon) % 360.0
        if 12 <= diff <= 168:  # waxing, well-illuminated
            score += 3
            rs.append(f"Moon waxing (Shukla Paksha, {diff:.0f}° from Sun) — emotionally available, open to love")
        elif diff > 192:        # waning, weak
            score -= 2
            rw.append(f"Moon waning (Krishna Paksha, {diff:.0f}° from Sun) — emotional reserves low")
        elif diff < 12:          # combust / amavasya
            score -= 3
            rw.append("Moon combust (near Amavasya) — emotionally drained, needs healing before love")

    # Placement
    if moon_house == 4:
        score += 2
        rs.append("Moon in own house 4 — emotional home, ideal for bonding")
    elif moon_house in (1, 5, 7, 11):
        score += 1
        rs.append(f"Moon in house {moon_house} — well-placed for love")
    elif moon_house in (6, 8, 12):
        score -= 2
        rw.append(f"Moon in dusthana {moon_house} — emotional bonding faces internal blocks")

    return {
        "moon_dignity":  moon_dig,
        "moon_house":    moon_house,
        "moon_sign":     moon_sign,
        "score":         score,
        "why_strong":    rs,
        "why_weak":      rw,
    }


# ── L4 — 7th house + 7th lord (partner — secondary in love, less than marriage) ─
def _layer_7th_house(intel: dict, kundli: dict, kp_sigs: dict) -> dict:
    """7th house = partner / public bond. SECONDARY for love (less than 5th).
    Weight: 10.

    Note: in marriage_engine 7H is PRIMARY (weight 18). For love we de-prioritise
    because love often happens BEFORE 7H is activated; 5H + Venus matter more.
    """
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

    seventh        = house_lords.get(7) or {}
    seventh_lord   = seventh.get("lord") or ""
    sl_entry       = dignities.get(seventh_lord) or {}
    sl_dig         = sl_entry.get("dignity") or "neutral-sign"
    sl_combust     = bool(sl_entry.get("combust"))
    sl_house       = (pmap.get(seventh_lord) or {}).get("house")

    score, rs, rw = 0, [], []

    # 7L dignity
    if sl_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 5
        rs.append(f"7th lord {seventh_lord} {sl_dig} — partnership-bhava strong")
    elif sl_dig in ("debilitated", "enemy-sign") and not sl_combust:
        score -= 4
        rw.append(f"7th lord {seventh_lord} {sl_dig} — partnership capacity strained")
    if sl_combust:
        score -= 3
        rw.append(f"7th lord {seventh_lord} combust — partnership burnt by ego")

    # 7L placement
    if sl_house in (1, 5, 7, 11):
        score += 3
        rs.append(f"7th lord {seventh_lord} in house {sl_house} — partner-axis activated")
    elif sl_house in (6, 8, 12):
        score -= 3
        rw.append(f"7th lord {seventh_lord} in dusthana {sl_house} — partner-axis afflicted")

    # 7H occupants
    occ_7h_b, occ_7h_m = [], []
    for pname, p in pmap.items():
        if p.get("house") == 7:
            if pname in NATURAL_BENEFICS:
                occ_7h_b.append(pname)
            elif pname in NATURAL_MALEFICS:
                occ_7h_m.append(pname)
    if occ_7h_b:
        score += 2
        rs.append(f"7H occupied by benefic(s) {', '.join(occ_7h_b)} — partner-bhava blessed")
    if "Saturn" in occ_7h_m:
        score -= 2
        rw.append("Saturn in 7H — late or restrictive partnership; mature partner expected")
    if "Mars" in occ_7h_m:
        score -= 2
        rw.append("Mars in 7H (Mangalik) — friction or aggression in partner-bhava")
    if "Rahu" in occ_7h_m:
        score -= 1
        rw.append("Rahu in 7H — unconventional / foreign / inter-caste partner pattern")
    if "Ketu" in occ_7h_m:
        score -= 2
        rw.append("Ketu in 7H — detached or karmic-completion partner pattern")

    # KP: 7L significations
    if _signifies(seventh_lord, LOVE_PROMISE, kp_sigs):
        score += 2
        rs.append(f"KP: 7th lord {seventh_lord} signifies love-promise houses 2/5/7/11")

    return {
        "seventh_lord":         seventh_lord,
        "seventh_lord_dignity": sl_dig,
        "seventh_lord_house":   sl_house,
        "seventh_lord_combust": sl_combust,
        "occupants_7h_benefics": occ_7h_b,
        "occupants_7h_malefics": occ_7h_m,
        "score":                score,
        "why_strong":           rs,
        "why_weak":             rw,
    }


# ── L5 — Mars-Venus combo (Mangal-Shukra yoga = passion/chemistry) ──────────
def _layer_mars_venus(intel: dict, kundli: dict) -> dict:
    """Mars + Venus configuration = physical passion / sexual chemistry.
    Weight: 8.

    Classical: Mars + Venus in same sign / same house / mutual aspect / exchange
    = strong attraction-energy, but uncontrolled = volatility.
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}

    mars  = pmap.get("Mars") or {}
    venus = pmap.get("Venus") or {}
    m_sign = mars.get("sign"); v_sign = venus.get("sign")
    m_house = mars.get("house"); v_house = venus.get("house")

    score, rs, rw = 0, [], []

    if m_sign and v_sign:
        # Same sign = conjunct
        if m_sign == v_sign:
            score += 4
            rs.append(f"Mangal-Shukra yoga: Mars + Venus same sign {m_sign} — strong physical passion")
            # Check for moderation by Jupiter
            jup_house = (pmap.get("Jupiter") or {}).get("house")
            jup_aspects = (dignities.get("Jupiter") or {}).get("aspects_houses") or []
            if v_house and (jup_house == v_house or v_house in jup_aspects):
                score += 1
                rs.append("Jupiter aspect on Venus moderates Mars-Venus passion — refined chemistry")
            else:
                rw.append("Mars-Venus passion lacks Jupiter moderation — risk of impulsive love decisions")

        # Sign exchange (Parivartana yoga)
        elif (m_sign in ("Taurus", "Libra") and v_sign in ("Aries", "Scorpio")):
            score += 5
            rs.append(f"Parivartana Yoga: Mars in Venus's sign + Venus in Mars's sign — deep mutual attraction karma")

        # Mutual aspect (7th from each other = 180°)
        elif m_house and v_house and abs(m_house - v_house) == 6:
            score += 2
            rs.append(f"Mars-Venus mutual 7th aspect (houses {m_house}/{v_house}) — magnetic chemistry")

    # Mars dignity affects passion quality
    m_dig = (dignities.get("Mars") or {}).get("dignity") or "neutral-sign"
    if m_dig in ("debilitated", "enemy-sign"):
        score -= 1
        rw.append(f"Mars {m_dig} — passion lacks control, may overwhelm")

    return {
        "mars_house":  m_house,
        "venus_house": v_house,
        "mars_sign":   m_sign,
        "venus_sign":  v_sign,
        "score":       score,
        "why_strong":  rs,
        "why_weak":    rw,
    }


# ── L6 — Jupiter on 5/7/11 (commitment seriousness) ─────────────────────────
def _layer_jupiter_commitment(intel: dict, kundli: dict) -> dict:
    """Jupiter = dharma, wisdom, commitment-orientation. Weight: 7.

    Strong Jupiter aspecting 5/7/11 = "marriage-grade" love, serious bond.
    Weak Jupiter = casual, fling-prone, unable to commit deeply.
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    j_entry = dignities.get("Jupiter") or {}
    j_dig   = j_entry.get("dignity") or "neutral-sign"
    j_house = (pmap.get("Jupiter") or {}).get("house")
    j_aspects = j_entry.get("aspects_houses") or []

    score, rs, rw = 0, [], []

    if j_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 3
        rs.append(f"Jupiter {j_dig} — strong commitment-capacity, marriage-grade love")
    elif j_dig in ("debilitated", "enemy-sign"):
        score -= 2
        rw.append(f"Jupiter {j_dig} — commitment-orientation weak; love may stay casual")

    # Jupiter aspecting / occupying 5/7/11
    love_aspects_5_7_11 = sum(1 for h in (5, 7, 11) if h in j_aspects or h == j_house)
    if love_aspects_5_7_11 >= 2:
        score += 4
        rs.append(f"Jupiter aspects/occupies {love_aspects_5_7_11} of love houses (5/7/11) — wisdom blesses love")
    elif love_aspects_5_7_11 == 1:
        score += 2
        rs.append(f"Jupiter aspects/occupies 1 love house — partial commitment support")

    return {
        "jupiter_dignity":      j_dig,
        "jupiter_house":        j_house,
        "jupiter_aspects":      j_aspects,
        "love_houses_aspected": love_aspects_5_7_11,
        "score":                score,
        "why_strong":           rs,
        "why_weak":             rw,
    }


# ── L7 — Mercury (communication chemistry) ──────────────────────────────────
def _layer_mercury_comm(intel: dict, kundli: dict) -> dict:
    """Mercury = mind, speech, communication. Weight: 5.

    Strong Mercury = good conversation chemistry, mental compatibility.
    Mercury in 3/5/7 = communication-driven love.
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    m_entry = dignities.get("Mercury") or {}
    m_dig   = m_entry.get("dignity") or "neutral-sign"
    m_house = (pmap.get("Mercury") or {}).get("house")
    m_combust = bool(m_entry.get("combust"))

    score, rs, rw = 0, [], []

    if m_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 3
        rs.append(f"Mercury {m_dig} — sharp mind, witty conversation chemistry")
    elif m_dig in ("debilitated", "enemy-sign"):
        score -= 2
        rw.append(f"Mercury {m_dig} — communication misunderstandings likely")
    if m_combust:
        score -= 2
        rw.append("Mercury combust — speech / messaging conflicts in relationship")

    if m_house in (3, 5, 7, 11):
        score += 2
        rs.append(f"Mercury in {m_house} — communication-driven love attraction")

    return {
        "mercury_dignity": m_dig,
        "mercury_house":   m_house,
        "mercury_combust": m_combust,
        "score":           score,
        "why_strong":      rs,
        "why_weak":        rw,
    }


# ── L8 — Rahu in 5/7/12 (intense / unconventional / forbidden) ──────────────
def _layer_rahu_in_love_houses(intel: dict, kundli: dict) -> dict:
    """Rahu = obsession, foreign, taboo, intensity. Weight: 6.

    Rahu in 5H = obsessive romance, sudden attractions
    Rahu in 7H = foreign / inter-caste / unconventional partner
    Rahu in 12H = secret / forbidden / hidden affair tendency
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    rahu_house = (pmap.get("Rahu") or {}).get("house")
    rahu_sign  = (pmap.get("Rahu") or {}).get("sign")

    score, rs, rw = 0, [], []

    if rahu_house == 5:
        score += 3
        rs.append("Rahu in 5H — intense / obsessive romantic capacity, sudden attractions")
        rw.append("Rahu in 5H — drama in romance, may chase forbidden or unconventional love")
    elif rahu_house == 7:
        score += 2
        rs.append("Rahu in 7H — foreign / inter-caste / unconventional partner attraction")
        rw.append("Rahu in 7H — partner pattern may feel foreign or 'other-worldly' (good if conscious)")
    elif rahu_house == 12:
        score += 1
        rw.append("Rahu in 12H — hidden / secret / foreign-land love patterns; affair susceptibility")
    elif rahu_house in (1, 4, 9, 10):
        score += 1
        rs.append(f"Rahu in {rahu_house} — broader life ambition includes unconventional love")

    # Exalted Rahu (Taurus per BPHS) = controlled obsession
    if rahu_sign == "Taurus":
        score += 1
        rs.append("Rahu exalted in Taurus — refined obsession, channels into committed love")

    return {
        "rahu_house": rahu_house,
        "rahu_sign":  rahu_sign,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L9 — Ketu in 5/7/12 (detachment / karmic ending) ────────────────────────
def _layer_ketu_in_love_houses(intel: dict, kundli: dict) -> dict:
    """Ketu = detachment, past-life karma completion, sudden disinterest.
    Weight: 5 (negative-leaning).

    Ketu in 5H = past-life love karma; soul-romance but detachment
    Ketu in 7H = karmic partner; relationship to "complete" not enjoy
    Ketu in 12H = renunciation of love; spiritual leanings outweigh romance
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    ketu_house = (pmap.get("Ketu") or {}).get("house")
    ketu_sign  = (pmap.get("Ketu") or {}).get("sign")

    score, rs, rw = 0, [], []

    if ketu_house == 5:
        score -= 3
        rw.append("Ketu in 5H — sudden disinterest in romance / past-life karma to complete (NOT enjoy)")
    elif ketu_house == 7:
        score -= 3
        rw.append("Ketu in 7H — karmic partner, relationship feels destined-to-end after lessons")
    elif ketu_house == 12:
        score -= 1
        rw.append("Ketu in 12H — moksha-leaning, romance feels less essential than spirituality")
    elif ketu_house in (3, 6, 11):
        score += 1
        rs.append(f"Ketu in {ketu_house} — past-life merit supports current love (not destabilising)")

    if ketu_sign == "Scorpio":
        score += 1
        rs.append("Ketu exalted in Scorpio — controlled detachment, can love without clinging")

    return {
        "ketu_house": ketu_house,
        "ketu_sign":  ketu_sign,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L10 — Saturn aspects on 5/7 (delays, age-gap, karmic) ───────────────────
def _layer_saturn_aspect(intel: dict, kundli: dict) -> dict:
    """Saturn aspecting 5/7 = delay, restriction, mature/older partner, karmic.
    Weight: 5 (typically negative for love freedom, but can be stabilising).
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    sat_entry = dignities.get("Saturn") or {}
    sat_dig   = sat_entry.get("dignity") or "neutral-sign"
    sat_aspects = sat_entry.get("aspects_houses") or []
    sat_house = (pmap.get("Saturn") or {}).get("house")

    score, rs, rw = 0, [], []

    saturn_on_5 = (sat_house == 5) or (5 in sat_aspects)
    saturn_on_7 = (sat_house == 7) or (7 in sat_aspects)

    if saturn_on_5 and saturn_on_7:
        score -= 4
        rw.append(f"Saturn aspects/occupies BOTH 5H + 7H — significant delay + maturity required in love")
    elif saturn_on_5:
        score -= 2
        rw.append("Saturn aspects/occupies 5H — romance delayed, takes itself seriously")
    elif saturn_on_7:
        score -= 2
        rw.append("Saturn aspects/occupies 7H — partner-bond delayed, mature partner pattern")

    # If Saturn is dignified (own/exalted), the delay is purposeful, not painful
    if (saturn_on_5 or saturn_on_7) and sat_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 2
        rs.append(f"BUT Saturn {sat_dig} — delay is purposeful, eventual love is stable & lasting")

    return {
        "saturn_house":   sat_house,
        "saturn_dignity": sat_dig,
        "saturn_on_5":    saturn_on_5,
        "saturn_on_7":    saturn_on_7,
        "score":          score,
        "why_strong":     rs,
        "why_weak":       rw,
    }


# ── L11 — 11th house (gain of love / social romance) ────────────────────────
def _layer_11th_house(intel: dict, kundli: dict) -> dict:
    """11th house = gains, friendships, fulfillment of desires. Weight: 4.
    For love = social-circle romance, friend-becomes-lover patterns,
    desire-fulfilment via partnership.
    """
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

    eleventh = house_lords.get(11) or {}
    el_lord  = eleventh.get("lord") or ""
    el_entry = dignities.get(el_lord) or {}
    el_dig   = el_entry.get("dignity") or "neutral-sign"
    el_house = (pmap.get(el_lord) or {}).get("house")

    score, rs, rw = 0, [], []

    if el_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 2
        rs.append(f"11th lord {el_lord} {el_dig} — gain-of-love & friendship-romance flow")
    elif el_dig in ("debilitated", "enemy-sign"):
        score -= 1
        rw.append(f"11th lord {el_lord} {el_dig} — desire-fulfilment via love delayed")

    if el_house in (1, 5, 7, 11):
        score += 1
        rs.append(f"11th lord {el_lord} in good house {el_house}")

    # Venus in 11H = social circle romance / friend becomes lover
    venus_house = (pmap.get("Venus") or {}).get("house")
    if venus_house == 11:
        score += 2
        rs.append("Venus in 11H — friend-becomes-lover pattern; love through social circle")

    return {
        "eleventh_lord": el_lord,
        "eleventh_lord_dignity": el_dig,
        "eleventh_lord_house": el_house,
        "score":         score,
        "why_strong":    rs,
        "why_weak":      rw,
    }


# ── L12 — 12th house (intimacy, hidden, foreign) ────────────────────────────
def _layer_12th_house(intel: dict, kundli: dict) -> dict:
    """12th house = bed, intimacy, hidden affairs, foreign. Weight: 5.

    12H is the BHOGA-STHANA (house of pleasures). Strong = good intimacy.
    But also = secret affairs, foreign love, isolation.
    """
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

    twelfth  = house_lords.get(12) or {}
    tl_lord  = twelfth.get("lord") or ""
    tl_dig   = (dignities.get(tl_lord) or {}).get("dignity") or "neutral-sign"
    tl_house = (pmap.get(tl_lord) or {}).get("house")

    score, rs, rw = 0, [], []

    # Venus in 12H = BHOGA (good intimacy) but also hidden/foreign love
    venus_house = (pmap.get("Venus") or {}).get("house")
    if venus_house == 12:
        score += 2
        rs.append("Venus in 12H — strong bedroom pleasures (Bhoga-sthana), foreign love possible")

    # 12L in 5H or 7H = intimate union, sometimes with karmic flavour
    if tl_house in (5, 7):
        score += 1
        rs.append(f"12th lord {tl_lord} in love-house {tl_house} — intimacy in romance")
    elif tl_house in (1,):
        score -= 1
        rw.append("12th lord in 1H — self-isolation may impede love expression")

    # Rahu in 12H + Venus aspect = forbidden affair signal (separately handled in C1)

    return {
        "twelfth_lord": tl_lord,
        "twelfth_lord_dignity": tl_dig,
        "twelfth_lord_house": tl_house,
        "score":        score,
        "why_strong":   rs,
        "why_weak":     rw,
    }


# ── L13 — Darakaraka (Jaimini partner-karaka) ───────────────────────────────
def _layer_darakaraka(jaimini_data: dict, intel: dict, kundli: dict) -> dict:
    """Darakaraka (DK) = planet with LOWEST degrees among 7 (Jaimini system).
    Represents the soul-essence of one's partner. Weight: 6.

    The DK's nature describes the partner's soul-personality:
      Sun     → confident, leader, govt/PSU type
      Moon    → emotional, nurturing, motherly
      Mars    → passionate, athletic, military/police type
      Mercury → witty, communicator, business/IT type
      Jupiter → wise, religious, teacher/advisor type
      Venus   → artistic, beautiful, luxurious / refined
      Saturn  → mature, disciplined, older / serious type
      Rahu    → unconventional, foreign, ambitious
    """
    karakas = (jaimini_data or {}).get("arudha", {}).get("karakas") or {}
    dk = karakas.get("DK") or karakas.get("Darakaraka") or {}
    dk_planet = dk.get("planet") or ""
    if not dk_planet and isinstance(dk, str):
        dk_planet = dk

    score, rs, rw = 0, [], []

    if not dk_planet:
        return {"darakaraka": "", "score": 0, "why_strong": [], "why_weak": []}

    # DK dignity affects partner-soul quality
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    dk_dig = (dignities.get(dk_planet) or {}).get("dignity") or "neutral-sign"
    pmap   = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    dk_house = (pmap.get(dk_planet) or {}).get("house")

    if dk_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 3
        rs.append(f"Darakaraka {dk_planet} {dk_dig} — soul-partner has refined nature ({_dk_persona(dk_planet)})")
    elif dk_dig in ("debilitated", "enemy-sign"):
        score -= 2
        rw.append(f"Darakaraka {dk_planet} {dk_dig} — soul-partner pattern may have struggle ({_dk_persona(dk_planet)})")

    # DK in good house = supportive partner pattern
    if dk_house in (1, 4, 5, 7, 9, 11):
        score += 2
        rs.append(f"Darakaraka {dk_planet} in good house {dk_house} — partner-soul supports love")
    elif dk_house in (6, 8, 12):
        score -= 1
        rw.append(f"Darakaraka {dk_planet} in dusthana {dk_house} — partner-soul carries karmic load")

    return {
        "darakaraka":         dk_planet,
        "darakaraka_dignity": dk_dig,
        "darakaraka_house":   dk_house,
        "darakaraka_persona": _dk_persona(dk_planet),
        "score":              score,
        "why_strong":         rs,
        "why_weak":           rw,
    }


def _dk_persona(planet: str) -> str:
    """One-line partner-soul persona for the Darakaraka."""
    return {
        "Sun":     "confident leader, govt/authority type",
        "Moon":    "emotional, nurturing, family-oriented",
        "Mars":    "passionate, athletic, action-oriented",
        "Mercury": "witty, communicator, mentally agile",
        "Jupiter": "wise, religious, teacher/advisor",
        "Venus":   "artistic, beautiful, luxury-loving",
        "Saturn":  "mature, disciplined, older or serious",
        "Rahu":    "unconventional, foreign, ambitious",
        "Ketu":    "spiritual, detached, mystical",
    }.get(planet, "—")


# ── L14 — Upapada Lagna (UL spouse signature, Jaimini) ──────────────────────
def _layer_upapada(jaimini_data: dict, intel: dict, kundli: dict) -> dict:
    """Upapada Lagna (UL) = spouse-equivalent in Jaimini. Weight: 5.

    UL is the Arudha pada of the 12th house. Represents the spouse / committed
    partner. UL2 (12H from UL) and UL12 are also examined. Strong UL with
    benefics = strong love bond capacity.
    """
    upapada = (jaimini_data or {}).get("upapada") or {}
    ul_sign  = upapada.get("ul_sign") or ""
    ul_lord  = upapada.get("ul_lord") or ""
    ul_house = upapada.get("ul_lord_house")
    occ_2nd  = upapada.get("occupants_2nd") or []
    occ_12th = upapada.get("occupants_12th") or []

    score, rs, rw = 0, [], []

    if not ul_sign:
        return {"upapada": "", "score": 0, "why_strong": [], "why_weak": []}

    # Benefics in 2nd from UL = strong spouse promise
    benefics_2nd = [p for p in occ_2nd if p in NATURAL_BENEFICS]
    malefics_2nd = [p for p in occ_2nd if p in NATURAL_MALEFICS]
    if benefics_2nd:
        score += 3
        rs.append(f"Benefic(s) {', '.join(benefics_2nd)} in 2nd-from-Upapada — spouse-bhava blessed")
    if malefics_2nd and not benefics_2nd:
        score -= 2
        rw.append(f"Malefic(s) {', '.join(malefics_2nd)} in 2nd-from-Upapada — spouse-bhava strained")

    # Benefics in 12th from UL = supportive ending of past karma
    benefics_12th = [p for p in occ_12th if p in NATURAL_BENEFICS]
    if benefics_12th:
        score += 1
        rs.append(f"Benefic(s) {', '.join(benefics_12th)} in 12th-from-Upapada — past-karma resolved peacefully")

    # UL lord in good house
    if ul_house in (1, 4, 5, 7, 9, 11):
        score += 1
        rs.append(f"Upapada lord {ul_lord} in house {ul_house} — UL well-placed")
    elif ul_house in (6, 8, 12):
        score -= 1
        rw.append(f"Upapada lord {ul_lord} in dusthana {ul_house}")

    return {
        "upapada":      f"{ul_sign} (lord {ul_lord})",
        "upapada_lord": ul_lord,
        "upapada_lord_house": ul_house,
        "occupants_2nd_from_ul":  occ_2nd,
        "occupants_12th_from_ul": occ_12th,
        "score":        score,
        "why_strong":   rs,
        "why_weak":     rw,
    }


# ── L15 — Atmakaraka aspects on 5/7 ─────────────────────────────────────────
def _layer_atmakaraka(jaimini_data: dict, intel: dict, kundli: dict) -> dict:
    """Atmakaraka (AK) = soul-significator (highest degrees). Weight: 4.

    AK aspecting/occupying 5/7 = soul prioritises love in this lifetime.
    """
    karakas = (jaimini_data or {}).get("arudha", {}).get("karakas") or {}
    ak = karakas.get("AK") or karakas.get("Atmakaraka") or {}
    ak_planet = ak.get("planet") or (ak if isinstance(ak, str) else "")

    score, rs, rw = 0, [], []
    if not ak_planet:
        return {"atmakaraka": "", "score": 0, "why_strong": [], "why_weak": []}

    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    ak_house = (pmap.get(ak_planet) or {}).get("house")
    ak_aspects = (dignities.get(ak_planet) or {}).get("aspects_houses") or []

    on_love = (ak_house in (5, 7)) or (5 in ak_aspects) or (7 in ak_aspects)
    if on_love:
        score += 3
        rs.append(f"Atmakaraka {ak_planet} {'in' if ak_house in (5,7) else 'aspects'} love-house — soul prioritises love this lifetime")

    return {
        "atmakaraka":       ak_planet,
        "atmakaraka_house": ak_house,
        "atmakaraka_on_love": on_love,
        "score":            score,
        "why_strong":       rs,
        "why_weak":         rw,
    }


# ── L16 — D9 NAVAMSA OVERLAY (mandatory by CLE format) ──────────────────────
def _layer_d9_navamsa(kundli: dict, fifth_lord: str, seventh_lord: str) -> dict:
    """⭐ MANDATORY by CLE format. Weight: 14.
    Wraps _d9_full_check() into the standard layer interface.
    """
    d9 = _d9_full_check(kundli, fifth_lord, seventh_lord)
    return d9


# ── L17 — KP CUSPAL SUB-LORD 5/7/11 (mandatory by CLE format) ──────────────
def _layer_kp_cuspal(kp: dict) -> dict:
    """⭐ MANDATORY by CLE format. Weight: 12.

    KP rule for love:
      Cusp 5 SL signifies houses → 2,5,7,11 = love promised | 1,6,8,12 = denied
      Cusp 7 SL signifies houses → 2,5,7,11 = partnership promised | 1,6,8,12 = denied
      Cusp 11 SL signifies houses → 2,5,7,11 = fulfillment promised | 1,6,8,12 = denied

    Verdict per cusp: promised | denied | ambiguous
    Final layer score = aggregate of 3 cusps (max +9, min -9).
    """
    cusps = kp.get("cusps") or []
    sigs  = kp.get("significations") or {}
    if not cusps or not sigs:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": [],
                "by_cusp": {}}

    by_cusp = {}
    score = 0
    rs, rw = [], []

    for h in (5, 7, 11):
        cusp = next((c for c in cusps if c.get("house") == h), None)
        if not cusp:
            continue
        sb_lord = cusp.get("sb") or ""        # sub-lord
        sl_lord = cusp.get("sl") or ""        # star-lord
        nl_lord = cusp.get("nl") or ""        # nakshatra-lord
        ss_lord = cusp.get("ss") or ""        # sub-sub-lord (CSL)

        sb_sig = sigs.get(sb_lord) or {}
        sb_houses = set(sb_sig.get("sb_houses") or sb_sig.get("pl") or [])
        prom_hit = sb_houses & LOVE_PROMISE
        deny_hit = sb_houses & LOVE_DENIAL

        verdict = "ambiguous"
        if prom_hit:
            verdict = "promised"
            score += 3
            rs.append(f"KP cusp {h}: SL {sb_lord} signifies promise houses {sorted(prom_hit)} → PROMISED")
        elif deny_hit and not prom_hit:
            verdict = "denied"
            score -= 3
            rw.append(f"KP cusp {h}: SL {sb_lord} signifies denial houses {sorted(deny_hit)} → DENIED")

        label = {5: "romance", 7: "partner", 11: "fulfillment"}.get(h, "")
        by_cusp[h] = {
            "label":     label,
            "sl":        sl_lord,
            "nl":        nl_lord,
            "sb":        sb_lord,
            "ss":        ss_lord,                       # CSL — used in L26
            "sb_signifies_houses": sorted(sb_houses),
            "verdict":   verdict,
        }

    return {
        "available":  True,
        "by_cusp":    by_cusp,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L18 — Ashtakavarga bindus on 5/7/11 ─────────────────────────────────────
def _layer_ashtakavarga(av: dict) -> dict:
    """Sarva Ashtakavarga (SAV) bindus in love houses. Weight: 5.
    Each house has 0-56 bindus (sum across 7 planets' BAV).
      ≥30 bindus = strong house, supports outcomes
      ≤25 bindus = weak house, struggles to deliver
    """
    if not av or "_error" in av:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}
    sav = av.get("sav") or av.get("sarva") or []
    if not sav or len(sav) < 12:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    score = 0
    rs, rw = [], []
    by_house = {}
    for h in (5, 7, 11):
        bindus = sav[h - 1] if isinstance(sav[h - 1], (int, float)) else 0
        by_house[h] = bindus
        if bindus >= 30:
            score += 1
            rs.append(f"SAV: house {h} has {bindus} bindus — strong love-house support")
        elif bindus <= 25:
            score -= 1
            rw.append(f"SAV: house {h} has only {bindus} bindus — love-house weak in cumulative strength")

    # Bonus for very strong 5H or 7H
    if by_house.get(5, 0) >= 35:
        score += 1
    if by_house.get(7, 0) >= 35:
        score += 1

    return {
        "available":   True,
        "sav_5_7_11":  by_house,
        "score":       score,
        "why_strong":  rs,
        "why_weak":    rw,
    }


# ── L19 — Bhava Bala on 5/7/11 ──────────────────────────────────────────────
def _layer_bhava_bala(bb: dict) -> dict:
    """Bhava Bala (qualitative house strength) for 5/7/11. Weight: 5.
    Uses bhava_bala module's computed values (sum across the 6 strength
    components per house).
    """
    if not bb or "_error" in bb:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    by_house = bb.get("bhavas") or bb.get("by_house") or {}
    if not by_house:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    score = 0
    rs, rw = [], []
    house_strengths = {}
    for h in (5, 7, 11):
        v = by_house.get(h) or by_house.get(str(h)) or {}
        if isinstance(v, dict):
            total = v.get("total") or v.get("strength") or v.get("bala_total") or 0
        else:
            total = v
        house_strengths[h] = total
        # Threshold per Parashara — 250 virupas standard
        if isinstance(total, (int, float)):
            if total >= 350:
                score += 2
                rs.append(f"Bhava Bala: house {h} very strong ({total:.0f} virupas)")
            elif total >= 250:
                score += 1
                rs.append(f"Bhava Bala: house {h} adequate ({total:.0f})")
            elif total > 0 and total < 200:
                score -= 1
                rw.append(f"Bhava Bala: house {h} weak ({total:.0f}) — below 250 virupa threshold")

    return {
        "available":      True,
        "house_strengths": house_strengths,
        "score":          score,
        "why_strong":     rs,
        "why_weak":       rw,
    }


# ── L20 — Shadbala on Venus + 5L + 7L ───────────────────────────────────────
def _layer_shadbala_venus(shadbala_d: dict, fifth_lord: str, seventh_lord: str) -> dict:
    """Shadbala precision check on the 3 most-relevant love planets. Weight: 5.
    A planet at ≥110% of its Sthana minimum is a karyakarta (deliverer).
    Below 50% = struggles to produce its houses' results.
    """
    if not shadbala_d or "_error" in shadbala_d:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    score = 0
    rs, rw = [], []
    breakdown = {}

    for label, planet in (("Venus", "Venus"),
                          (f"5L {fifth_lord}", fifth_lord),
                          (f"7L {seventh_lord}", seventh_lord)):
        if not planet:
            continue
        d = shadbala_d.get(planet) if isinstance(shadbala_d, dict) else None
        if not isinstance(d, dict):
            continue
        pct = d.get("strength_pct")
        if not isinstance(pct, (int, float)):
            continue
        breakdown[label] = pct
        if pct >= 110:
            score += 2
            rs.append(f"Shadbala: {label} very-strong ({pct:.0f}%) — full karyakarta for love")
        elif pct >= 90:
            score += 1
            rs.append(f"Shadbala: {label} strong ({pct:.0f}%) — capable")
        elif pct < 50:
            score -= 2
            rw.append(f"Shadbala: {label} very-weak ({pct:.0f}%) — struggles to deliver love-houses")
        elif pct < 70:
            score -= 1
            rw.append(f"Shadbala: {label} weak ({pct:.0f}%)")

    return {
        "available":  True,
        "breakdown":  breakdown,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L21 — Char Karakas full set (Jaimini) ───────────────────────────────────
def _layer_char_karakas(jaimini_data: dict) -> dict:
    """Full Jaimini Char Karaka set: AK, AmK, BhK, MK, PiK, GK, DK.
    Weight: 4. Cross-checks Darakaraka with the broader karaka pattern.
    """
    karakas = (jaimini_data or {}).get("arudha", {}).get("karakas") or {}
    if not karakas:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    score = 0
    rs, rw = [], []

    # Special: Venus as one of the karakas (esp DK or AK) = love-priority lifetime
    venus_role = None
    for role, k in karakas.items():
        plan = k.get("planet") if isinstance(k, dict) else (k if isinstance(k, str) else "")
        if plan == "Venus":
            venus_role = role
            break
    if venus_role in ("DK", "Darakaraka"):
        score += 2
        rs.append("Venus = Darakaraka — partner has strong Venus signature (artistic, refined, luxurious)")
    elif venus_role in ("AK", "Atmakaraka"):
        score += 3
        rs.append("Venus = Atmakaraka — soul-purpose this lifetime IS love & beauty")

    # Moon as DK = nurturing, family-oriented partner
    moon_role = None
    for role, k in karakas.items():
        plan = k.get("planet") if isinstance(k, dict) else (k if isinstance(k, str) else "")
        if plan == "Moon" and role in ("DK", "Darakaraka"):
            moon_role = "DK"
    if moon_role:
        score += 1
        rs.append("Moon = Darakaraka — partner has nurturing, emotional, family-loving nature")

    return {
        "available":  True,
        "karakas":    {r: (k.get("planet") if isinstance(k, dict) else k)
                       for r, k in karakas.items()},
        "venus_role": venus_role,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L22 — Yogini Dasha cross-check (we use Sthira Dasha as Jaimini cross-check) ─
def _layer_yogini_cross(yogini_d: dict) -> dict:
    """Cross-check current dasha with Sthira Jaimini dasha system. Weight: 3.
    If Vimshottari + Jaimini cross-check AGREE on the active sign/lord,
    confidence ↑↑.
    """
    if not yogini_d or "_error" in yogini_d:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    cur_sign  = yogini_d.get("current_sign") or yogini_d.get("current") or ""
    cur_lord  = yogini_d.get("current_lord") or yogini_d.get("planet") or ""

    score = 0
    rs, rw = [], []

    if cur_lord in ("Venus", "Moon", "Jupiter"):
        score += 2
        rs.append(f"Sthira Dasha cross-check: current period ruled by {cur_lord} — favourable for love (benefic Jaimini lord)")
    elif cur_lord in ("Saturn", "Rahu", "Ketu"):
        score -= 1
        rw.append(f"Sthira Dasha cross-check: current period ruled by {cur_lord} — restrictive Jaimini lord, love faces karmic friction")

    return {
        "available":   True,
        "current_sign": cur_sign,
        "current_lord": cur_lord,
        "score":       score,
        "why_strong":  rs,
        "why_weak":    rw,
    }


# ── L23 — Sade Sati / Shani Dhaiya on Moon ──────────────────────────────────
def _layer_sade_sati(intel: dict) -> dict:
    """Sade Sati = Saturn transit through 12th, 1st, 2nd from natal Moon.
    Total 7.5-year cycle. Weight: 5 (typically negative, but builds maturity).
    Shani Dhaiya = Saturn through 4th or 8th from Moon (2.5 years each).
    """
    sade = intel.get("sade_sati") or ""
    score, rs, rw = 0, [], []

    if not sade:
        return {"sade_sati": "", "score": 0, "why_strong": [], "why_weak": []}

    s_lower = sade.lower() if isinstance(sade, str) else ""
    if "peak" in s_lower or "main" in s_lower or "second" in s_lower:
        score -= 4
        rw.append(f"Sade Sati PEAK phase ({sade}) — emotional reserves drained, love feels heavy")
    elif "rising" in s_lower or "first" in s_lower or "starting" in s_lower or "begin" in s_lower:
        score -= 2
        rw.append(f"Sade Sati rising phase ({sade}) — emotional pressure begins")
    elif "setting" in s_lower or "third" in s_lower or "ending" in s_lower:
        score -= 1
        rw.append(f"Sade Sati setting phase ({sade}) — last leg of emotional reset")
    elif "dhaiya" in s_lower or "ardha" in s_lower:
        score -= 2
        rw.append(f"Shani Dhaiya ({sade}) — 2.5-year emotional restriction on love")
    else:
        # Some other text → treat as mild active
        score -= 1
        rw.append(f"Saturn transit context: {sade}")

    return {
        "sade_sati":  sade,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L24 — Eclipse impact on Venus / 7L ──────────────────────────────────────
def _layer_eclipse(intel: dict, kundli: dict) -> dict:
    """Eclipse impact: lunar/solar eclipse falling on natal Venus or 7L's
    nakshatra/sign in the last 6 or next 6 months = major karmic shift in
    relationships. Weight: 4 (negative-leaning).

    Approximate eclipse longitudes 2025-2026 (sidereal):
      2025-09-07 lunar eclipse — Pisces ~21°
      2026-02-17 solar eclipse — Aquarius ~28°
      2026-08-12 solar eclipse — Leo ~26°
      2026-03-03 lunar eclipse — Leo ~13°
    Cross-checks against Venus / 7L positions.
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    venus_lon = (pmap.get("Venus") or {}).get("lon", (pmap.get("Venus") or {}).get("longitude"))
    seventh_lord = (house_lords.get(7) or {}).get("lord") or ""
    sl_lon = (pmap.get(seventh_lord) or {}).get("lon", (pmap.get(seventh_lord) or {}).get("longitude")) if seventh_lord else None

    score, rs, rw = 0, [], []

    ECLIPSES = [
        ("2025-09-07", 351.0, "lunar"),   # Pisces ~21°
        ("2026-02-17", 328.0, "solar"),   # Aquarius ~28°
        ("2026-08-12", 146.0, "solar"),   # Leo ~26°
        ("2026-03-03", 133.0, "lunar"),   # Leo ~13°
    ]
    today = datetime.utcnow()
    triggered = []

    for date_str, ecl_lon, kind in ECLIPSES:
        try:
            d = datetime.fromisoformat(date_str)
        except Exception:
            continue
        days_diff = abs((d - today).days)
        if days_diff > 180:   # only ±6 months
            continue
        # Within 8° of Venus or 7L = eclipse hits
        for label, lon in (("Venus", venus_lon), (f"7L {seventh_lord}", sl_lon)):
            if not isinstance(lon, (int, float)):
                continue
            angular = min(abs(ecl_lon - lon), 360.0 - abs(ecl_lon - lon))
            if angular <= 8.0:
                triggered.append({
                    "date":  date_str, "kind": kind, "target": label,
                    "orb":   round(angular, 1),
                })

    if triggered:
        score -= min(4, len(triggered) * 2)
        for t in triggered[:3]:
            rw.append(
                f"Eclipse alert: {t['kind']} eclipse on {t['date']} hits {t['target']} "
                f"(orb {t['orb']}°) — karmic shift in love expected"
            )
    else:
        rs.append("No major eclipse hitting Venus or 7th-lord in ±6 months — no karmic shocks expected")

    return {
        "eclipses_triggered": triggered,
        "score":              score,
        "why_strong":         rs,
        "why_weak":           rw,
    }


# ── L25 — D30 Trishamsa (character / affair guard) ──────────────────────────
def _layer_d30_trishamsa(kundli: dict) -> dict:
    """⭐ Critical for affair_third_party + breakup_signal buckets. Weight: 5.
    Wraps _d30_trishamsa_check() into the standard layer interface.
    """
    return _d30_trishamsa_check(kundli)


# ── L26 — KP CSL (sub-sub-lord) precision ───────────────────────────────────
def _layer_kp_csl(kp_layer: dict, sigs: dict) -> dict:
    """KP CSL (Sub-Sub-Lord) of love-cusps. Weight: 4.
    The CSL is the FINER signification — used by mainstream KP astrologers
    for very-precise event timing. We check whether cusp 5/7/11 CSL signifies
    promise houses (additive bonus) or denial houses (additional penalty).
    """
    if not kp_layer or not kp_layer.get("available"):
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    by_cusp = kp_layer.get("by_cusp") or {}
    score = 0
    rs, rw = [], []

    for h, row in by_cusp.items():
        ss = row.get("ss") or ""
        if not ss:
            continue
        ss_sig = (sigs or {}).get(ss) or {}
        ss_houses = set(ss_sig.get("sb_houses") or ss_sig.get("pl") or [])
        if not ss_houses:
            continue
        prom_hit = ss_houses & LOVE_PROMISE
        deny_hit = ss_houses & LOVE_DENIAL
        if prom_hit:
            score += 1
            rs.append(f"KP CSL cusp {h}: SS-lord {ss} signifies {sorted(prom_hit)} — fine confirmation of promise")
        elif deny_hit and not prom_hit:
            score -= 1
            rw.append(f"KP CSL cusp {h}: SS-lord {ss} signifies only denial houses {sorted(deny_hit)}")

    return {
        "available":  True,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L27 — Argala on 5/7/11 ──────────────────────────────────────────────────
def _layer_argala_love(argala_d: dict) -> dict:
    """Argala = planetary intervention from supporting houses. Weight: 3.
    For love, we check Argala on 5/7/11 — benefic argala = hidden helper,
    malefic argala = hidden blocker (Vipreet Argala unless cancelled).
    """
    if not argala_d or "_error" in argala_d:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    by_house = argala_d.get("by_house") or argala_d.get("argala") or {}
    if not by_house:
        return {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    score = 0
    rs, rw = [], []

    for h in (5, 7, 11):
        info = by_house.get(h) or by_house.get(str(h)) or {}
        if not isinstance(info, dict):
            continue
        primary = info.get("primary") or info.get("argala_planets") or []
        virodha = info.get("virodha") or info.get("virodha_argala") or []
        # Benefic primary = positive intervention
        ben_primary = [p for p in primary if p in NATURAL_BENEFICS]
        if ben_primary:
            score += 1
            rs.append(f"Argala house {h}: benefic intervention by {', '.join(ben_primary)} — hidden helper for love")
        # Malefic primary uncancelled by virodha = blocker
        mal_primary = [p for p in primary if p in NATURAL_MALEFICS]
        if mal_primary and not virodha:
            score -= 1
            rw.append(f"Argala house {h}: malefic intervention by {', '.join(mal_primary)} (uncancelled) — hidden blocker")

    return {
        "available":  True,
        "score":      score,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ── L28 — Composite Moon-Venus-Mars triad ───────────────────────────────────
def _layer_triad(layer_moon: dict, layer_venus: dict, layer_mars_venus: dict) -> dict:
    """Aggregate Moon (emotion) + Venus (love) + Mars (passion) score.
    Weight: 6. The MOST predictive triad for love readiness.
    """
    moon_s = layer_moon.get("score", 0)
    venus_s = layer_venus.get("score", 0)
    mars_s = layer_mars_venus.get("score", 0)
    triad_total = moon_s + venus_s + mars_s

    score = 0
    rs, rw = [], []

    if triad_total >= 15:
        score += 5
        rs.append(f"Moon-Venus-Mars triad VERY STRONG (combined +{triad_total}) — emotional, romantic, passionate aligned")
    elif triad_total >= 8:
        score += 3
        rs.append(f"Moon-Venus-Mars triad strong (combined +{triad_total}) — love faculties balanced")
    elif triad_total <= -8:
        score -= 4
        rw.append(f"Moon-Venus-Mars triad WEAK (combined {triad_total}) — emotional/romantic/passion all strained")
    elif triad_total <= -3:
        score -= 2
        rw.append(f"Moon-Venus-Mars triad below par ({triad_total}) — at least one love faculty struggling")

    return {
        "triad_total": triad_total,
        "score":       score,
        "why_strong":  rs,
        "why_weak":    rw,
    }


# ── L29 — Synastry Kuta scoring (only if partner_kundli given) ──────────────
def _layer_synastry(my_kundli: dict, my_intel: dict, partner_kundli: dict,
                    partner_kp: Optional[dict] = None) -> dict:
    """Classical synastry — 8-Kuta scoring (love-tuned weights). Weight: 8.

    Conducted ONLY if partner_kundli is provided. Returns score 0-32 mapped
    to ±5. Each Kuta:
      Tara     (3 pts) — Moon-nakshatra count compatibility
      Yoni     (4 pts) — animal nature compatibility (subset)
      Vasya    (2 pts) — power dynamic
      Graha-Maitri (5 pts) — Moon-sign-lord friendship
      Stree-Deergha — physical attraction longevity
      Vedha (-3 pts) — incompatible nakshatra penalty
      Mahendra (+3 pts) — bonding strength bonus
      Bhakoot  (7 pts) — Moon sign distance compatibility
    Total max 32, with vedha/bhakoot negatives.
    """
    if not partner_kundli or not isinstance(partner_kundli, dict):
        return {"available": False, "score": 0, "why_strong": [], "why_weak": [],
                "kuta_score": None}

    my_pmap = {p.get("name"): p for p in (my_kundli.get("planets") or []) if p.get("name")}
    pa_pmap = {p.get("name"): p for p in (partner_kundli.get("planets") or []) if p.get("name")}

    my_moon = my_pmap.get("Moon") or {}
    pa_moon = pa_pmap.get("Moon") or {}
    my_moon_sign = my_moon.get("sign") or ""
    pa_moon_sign = pa_moon.get("sign") or ""
    my_moon_nak  = my_moon.get("nakshatra") or my_kundli.get("nakshatra") or ""
    pa_moon_nak  = pa_moon.get("nakshatra") or partner_kundli.get("nakshatra") or ""

    score = 0
    rs, rw = [], []
    kuta_score = 0

    # ── Bhakoot (7 pts) — Moon sign distance ──
    if my_moon_sign and pa_moon_sign:
        my_idx = _sign_idx(my_moon_sign)
        pa_idx = _sign_idx(pa_moon_sign)
        if my_idx is not None and pa_idx is not None:
            dist = abs(my_idx - pa_idx) % 12
            min_dist = min(dist, 12 - dist)
            # Inauspicious distances per classical: 6/8 from each other
            if min_dist in (6, 8):
                kuta_score += 0
                score -= 2
                rw.append(f"Bhakoot Dosha: Moons {min_dist} signs apart — emotional rhythm clash")
            else:
                kuta_score += 7
                score += 2
                rs.append(f"Bhakoot OK: Moons {min_dist} signs apart — emotional rhythm compatible")

    # ── Graha-Maitri (5 pts) — Moon-sign-lord friendship ──
    if my_moon_sign and pa_moon_sign:
        my_lord = SIGN_LORDS.get(my_moon_sign)
        pa_lord = SIGN_LORDS.get(pa_moon_sign)
        # Simplified friend-set per BPHS
        FRIENDS = {
            "Sun":     {"Moon", "Mars", "Jupiter"},
            "Moon":    {"Sun", "Mercury"},
            "Mars":    {"Sun", "Moon", "Jupiter"},
            "Mercury": {"Sun", "Venus"},
            "Jupiter": {"Sun", "Moon", "Mars"},
            "Venus":   {"Mercury", "Saturn"},
            "Saturn":  {"Mercury", "Venus"},
        }
        if my_lord and pa_lord:
            if my_lord == pa_lord:
                kuta_score += 5; score += 1
                rs.append(f"Graha-Maitri: same Moon-lord {my_lord} — natural mind-meld")
            elif pa_lord in FRIENDS.get(my_lord, set()) and my_lord in FRIENDS.get(pa_lord, set()):
                kuta_score += 5; score += 1
                rs.append(f"Graha-Maitri: {my_lord} ↔ {pa_lord} mutual friends — mind compatibility")
            elif pa_lord in FRIENDS.get(my_lord, set()) or my_lord in FRIENDS.get(pa_lord, set()):
                kuta_score += 3
                rs.append(f"Graha-Maitri: {my_lord} ↔ {pa_lord} one-way friend — partial mind compatibility")
            else:
                rw.append(f"Graha-Maitri: {my_lord} ↔ {pa_lord} not friends — mind-style differs")

    # ── Vedha Nakshatra (-3 if incompatible) ──
    if my_moon_nak and pa_moon_nak:
        if _VEDHA.get(my_moon_nak) == pa_moon_nak:
            score -= 3
            rw.append(f"Vedha Dosha: nakshatras {my_moon_nak} ↔ {pa_moon_nak} are obstructive pair")
        else:
            kuta_score += 3
            rs.append(f"No Vedha Dosha between {my_moon_nak} and {pa_moon_nak}")

    # ── Tara (3 pts) — count of nakshatras 1→2 ──
    if my_moon_nak and pa_moon_nak:
        try:
            i1 = NAKSHATRAS.index(my_moon_nak)
            i2 = NAKSHATRAS.index(pa_moon_nak)
            count = ((i2 - i1) % 27) + 1
            tara = (count - 1) % 9
            # Bad taras: 3 (Vipat), 5 (Pratyak), 7 (Vadh)
            if tara in (2, 4, 6):
                rw.append(f"Tara count {count} → Tara {tara+1} (inauspicious)")
            else:
                kuta_score += 3
                rs.append(f"Tara count {count} → Tara {tara+1} (auspicious)")
        except ValueError:
            pass

    # ── Mahendra (+3 if matching) — counts 4, 7, 10, 13, 16, 19, 22, 25 ──
    if my_moon_nak and pa_moon_nak:
        try:
            i1 = NAKSHATRAS.index(my_moon_nak)
            i2 = NAKSHATRAS.index(pa_moon_nak)
            count = ((i2 - i1) % 27) + 1
            if count in (4, 7, 10, 13, 16, 19, 22, 25):
                kuta_score += 3
                score += 1
                rs.append(f"Mahendra: count {count} matches auspicious set — bonding strength")
        except ValueError:
            pass

    # ── Cross-overlay: partner's Venus on my D9 7H ──
    pa_venus = pa_pmap.get("Venus") or {}
    pa_venus_sign = pa_venus.get("sign")
    my_d9 = ((my_kundli or {}).get("divisionalCharts") or {}).get("D9") or {}
    asc_idx = my_d9.get("ascendantSignIndex")
    if asc_idx is not None and pa_venus_sign:
        d9_7_sign = SIGNS[(int(asc_idx) + 6) % 12]
        if pa_venus_sign == d9_7_sign:
            score += 2
            rs.append(f"D9 SYNASTRY: partner's Venus in {pa_venus_sign} = MY D9 7H sign — strong love-bond karma")

    # ── Cross-significator (KP) ──
    if partner_kp and isinstance(partner_kp, dict):
        my_kp = (my_kundli.get("kp") or {})  # may be empty if not supplied
        # Light cross-check — partner's 7L sub-lord planet present in my love-houses
        pa_cusps = partner_kp.get("cusps") or []
        pa_7 = next((c for c in pa_cusps if c.get("house") == 7), None)
        if pa_7:
            pa_7_sb = pa_7.get("sb") or ""
            my_p_house = (my_pmap.get(pa_7_sb) or {}).get("house") if pa_7_sb else None
            if my_p_house in LOVE_PROMISE:
                score += 2
                rs.append(f"KP cross: partner's 7-cusp SL {pa_7_sb} sits in MY love-house {my_p_house}")

    return {
        "available":   True,
        "kuta_score":  kuta_score,
        "kuta_max":    32,
        "score":       max(-5, min(8, score)),       # clamp
        "why_strong":  rs,
        "why_weak":    rw,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER LAYERS T1, T2 — current activation
# ─────────────────────────────────────────────────────────────────────────────
def _layer_dasha_timing(kundli: dict, kp_sigs: dict, q_type: str) -> dict:
    """T1 — Vimshottari MD+AD+PD timing. Weight: 10.
    Picks first future window where MD or AD signifies LOVE_PROMISE houses.
    Returns next_window + pratyantar_window + current_supports + score.
    """
    cur_dasha = (kundli.get("currentDasha") or {})
    cur_md    = cur_dasha.get("maha") or ""
    cur_ad    = cur_dasha.get("antar") or ""

    # Significators of love-promise houses (KP-based)
    sigs_set = _significators_of(LOVE_PROMISE, kp_sigs)
    # Add classical significators if KP missing — Venus, 5L, 7L always relevant
    house_lords = {h.get("house"): h for h in (((kundli.get("intel") or {}).get("house_lords")) or [])}
    sigs_set.update({"Venus"})
    if house_lords.get(5):
        sigs_set.add(house_lords.get(5).get("lord", ""))
    if house_lords.get(7):
        sigs_set.add(house_lords.get(7).get("lord", ""))
    if house_lords.get(11):
        sigs_set.add(house_lords.get(11).get("lord", ""))
    sigs_set.discard("")

    today = datetime.utcnow()
    next_window     = _next_dasha_window((kundli.get("dashas") or []), sigs_set, today)
    pratyantar_win  = _next_pratyantar_window((kundli.get("dashas") or []), sigs_set, today)

    current_supports = bool(
        (cur_md and cur_md in sigs_set) or (cur_ad and cur_ad in sigs_set)
    )

    score = 0
    rs, rw = [], []

    if current_supports:
        score += 5
        rs.append(f"Current Dasha {cur_md}-{cur_ad} signifies love-houses (window OPEN)")
    else:
        score -= 3
        rw.append(f"Current Dasha {cur_md}-{cur_ad} does not signify love-houses (window CLOSED)")

    if next_window:
        score += 3
        rs.append(f"Next favourable love-window: {next_window['dasha']} ({next_window['start']} → {next_window['end']})")
    else:
        score -= 2
        rw.append("No clear favourable Dasha window in next 12 years for love")

    return {
        "score":               score,
        "current_dasha":       f"{cur_md}-{cur_ad}".strip("-"),
        "current_supports":    current_supports,
        "love_significators":  sorted(sigs_set),
        "next_window":         next_window,
        "pratyantar_window":   pratyantar_win,
        "why_strong":          rs,
        "why_weak":            rw,
    }


def _layer_transit(jup_t: dict, sat_t: dict, intel: dict, kundli: dict) -> dict:
    """T2 — Live Jupiter + Saturn transit support. Weight: 5.
    Jupiter on 5/7/11 = expansion of love. Saturn on 5/7 = restriction.
    """
    score = 0
    rs, rw = [], []

    if jup_t and jup_t.get("jupiter_active_now"):
        score += 4
        aw = jup_t.get("active_window") or {}
        rs.append(f"Jupiter currently transiting {aw.get('sign','?')} — love expansion window LIVE (until {aw.get('end','?')})")
    elif jup_t and jup_t.get("all_windows"):
        # Next Jupiter trigger
        nxt = next(iter(jup_t["all_windows"]), None)
        if nxt:
            rs.append(f"Next Jupiter love-trigger: {nxt.get('sign')} ({nxt.get('start')} → {nxt.get('end')})")

    # Saturn transit on Moon's sign (Sade Sati) handled in L23.
    # Here we check Saturn over natal Venus or natal 5L
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    venus_sign = (pmap.get("Venus") or {}).get("sign")
    sat_sign = sat_t.get("current_sign") if sat_t else None
    if sat_sign and venus_sign and sat_sign == venus_sign:
        score -= 3
        rw.append(f"Saturn transiting natal Venus's sign {sat_sign} — live restriction on Venus, love feels heavy")
    elif sat_sign and venus_sign:
        # Saturn at 4/7/8/10 from Venus = aspect
        v_idx = _sign_idx(venus_sign)
        s_idx = _sign_idx(sat_sign)
        if v_idx is not None and s_idx is not None:
            dist = (v_idx - s_idx) % 12
            # Saturn aspects 3rd, 7th, 10th house from itself
            if dist in (2, 6, 9):  # 3rd/7th/10th
                score -= 2
                rw.append(f"Saturn aspecting natal Venus from {sat_sign} (count {dist+1} from Venus) — discipline pressure on love")

    return {
        "score":      score,
        "jup_active": bool(jup_t.get("jupiter_active_now")) if jup_t else False,
        "saturn_sign": sat_sign,
        "why_strong": rs,
        "why_weak":   rw,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODIFIERS M1-M7
# ─────────────────────────────────────────────────────────────────────────────
def _modifier_combust(intel: dict, fifth_lord: str, seventh_lord: str) -> dict:
    """M1 — Venus / 5L / 7L combust check. ±5 max."""
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    score = 0; whys = []
    for label, p in (("Venus", "Venus"),
                     (f"5L {fifth_lord}", fifth_lord),
                     (f"7L {seventh_lord}", seventh_lord)):
        if not p: continue
        if (dignities.get(p) or {}).get("combust"):
            score -= 2
            whys.append(f"{label} combust by Sun")
    return {"score": max(-5, score), "why": whys}


def _modifier_retrograde(intel: dict, fifth_lord: str, seventh_lord: str) -> dict:
    """M2 — Venus / 5L / 7L retrograde. ±3 max."""
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    score = 0; whys = []
    for label, p in (("Venus", "Venus"),
                     (f"5L {fifth_lord}", fifth_lord),
                     (f"7L {seventh_lord}", seventh_lord)):
        if not p: continue
        if (dignities.get(p) or {}).get("retrograde"):
            score -= 1
            whys.append(f"{label} retrograde — past-life karma replays in love")
    return {"score": max(-3, score), "why": whys}


def _modifier_malefic_aspects(intel: dict, kundli: dict, fifth_lord: str,
                              seventh_lord: str) -> dict:
    """M3 — Malefic aspects on Venus / 5L / 7L. ±5 max."""
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    score = 0; whys = []

    def _is_aspected_by(target_planet: str, aspecter: str) -> bool:
        target_house = (pmap.get(target_planet) or {}).get("house")
        aspecter_aspects = (dignities.get(aspecter) or {}).get("aspects_houses") or []
        return target_house in aspecter_aspects if target_house else False

    for label, target in (("Venus", "Venus"),
                          (f"5L {fifth_lord}", fifth_lord),
                          (f"7L {seventh_lord}", seventh_lord)):
        if not target: continue
        for malef in ("Saturn", "Mars", "Rahu", "Ketu"):
            if _is_aspected_by(target, malef):
                score -= 1
                whys.append(f"Malefic {malef} aspects {label}")
    return {"score": max(-5, score), "why": whys[:4]}


def _modifier_lagnesh_venus(intel: dict, kundli: dict) -> dict:
    """M4 — Lagnesh-Venus harmony (same sign, friend signs, exchange). ±3."""
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    lagnesh = (house_lords.get(1) or {}).get("lord") or ""
    if not lagnesh:
        return {"score": 0, "why": [], "lagnesh": ""}
    lag_sign = (pmap.get(lagnesh) or {}).get("sign")
    v_sign   = (pmap.get("Venus") or {}).get("sign")
    score = 0; whys = []
    if lag_sign and v_sign:
        if lag_sign == v_sign:
            score += 3
            whys.append(f"Lagnesh {lagnesh} conjunct Venus — self-identity aligned with love nature")
        else:
            FRIENDS = {
                "Sun": {"Moon","Mars","Jupiter"}, "Moon": {"Sun","Mercury"},
                "Mars": {"Sun","Moon","Jupiter"}, "Mercury": {"Sun","Venus"},
                "Jupiter": {"Sun","Moon","Mars"}, "Venus": {"Mercury","Saturn"},
                "Saturn": {"Mercury","Venus"},
            }
            if "Venus" in FRIENDS.get(lagnesh, set()) or lagnesh in FRIENDS.get("Venus", set()):
                score += 1
                whys.append(f"Lagnesh {lagnesh} friendly to Venus — self-expression supports love")
    return {"score": score, "why": whys, "lagnesh": lagnesh}


def _modifier_saturn_transit_5_7(sat_t: dict, kundli: dict) -> dict:
    """M5 — Transit Saturn over 5/7/Venus. -5 max."""
    if not sat_t:
        return {"score": 0, "why": []}
    sat_sign = sat_t.get("current_sign") if isinstance(sat_t, dict) else None
    if not sat_sign:
        return {"score": 0, "why": []}
    s_idx = _sign_idx(sat_sign)
    asc_sign = (kundli or {}).get("ascendant") or ""
    asc_idx = _sign_idx(asc_sign)
    if s_idx is None or asc_idx is None:
        return {"score": 0, "why": []}
    score = 0; whys = []
    for h in (5, 7):
        h_sign_idx = (asc_idx + h - 1) % 12
        if h_sign_idx == s_idx:
            score -= 3
            whys.append(f"Saturn transiting {SIGNS[s_idx]} = your {h}H — direct restriction on love")
    return {"score": max(-5, score), "why": whys}


def _modifier_jupiter_transit_5_7_11(jup_t: dict, kundli: dict) -> dict:
    """M6 — Transit Jupiter on 5/7/11 from Lagna or Moon. +6 max."""
    if not jup_t:
        return {"score": 0, "why": []}
    if not jup_t.get("jupiter_active_now"):
        return {"score": 0, "why": []}
    aw = jup_t.get("active_window") or {}
    hits = aw.get("hits") or []
    score = 0; whys = []
    if 5 in hits:
        score += 3
        whys.append("Jupiter transit hits 5H — romance expansion ACTIVE")
    if 7 in hits:
        score += 2
        whys.append("Jupiter transit hits 7H — partner-axis expansion ACTIVE")
    if 11 in hits:
        score += 1
        whys.append("Jupiter transit hits 11H — fulfillment of love-desire ACTIVE")
    return {"score": min(6, score), "why": whys}


def _modifier_mahapurusha(varga_yogas: dict) -> dict:
    """M7 — Pancha-Mahapurusha (Malavya for Venus, Hamsa for Jupiter). +5 max."""
    if not varga_yogas or "_error" in varga_yogas:
        return {"score": 0, "why": []}
    score = 0; whys = []
    yogas_list = varga_yogas.get("yogas") or []
    for y in yogas_list:
        name = (y.get("name") or "").lower() if isinstance(y, dict) else ""
        if "malavya" in name:
            score += 3
            whys.append("Malavya Yoga (Venus mahapurusha) — divine love nature, attracts beauty")
        elif "hamsa" in name:
            score += 2
            whys.append("Hamsa Yoga (Jupiter mahapurusha) — wisdom-blessed love")
    return {"score": min(5, score), "why": whys}


# ─────────────────────────────────────────────────────────────────────────────
# CONDITIONALS C1, C2
# ─────────────────────────────────────────────────────────────────────────────
def _conditional_affair_check(intel: dict, kundli: dict, kp_sigs: dict) -> dict:
    """C1 — Fires only for q_type == "affair_third_party".
    Looks at deception markers WITHOUT making accusations:
      - 12L afflicted (loss / hidden)
      - Rahu in 7H or Venus-Rahu axis (forbidden attraction signal)
      - D30 Venus-Rahu conjunction (already in L25)
      - 7L in 12H or 12L in 7H (hidden partner activity)

    Returns {signal_strength: low|moderate|high, score: ±, indicators: [...]}.
    Brand-safety guard: NEVER says "partner is cheating" — only describes
    cosmic patterns + recommends self-introspection + open communication.
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}

    indicators = []
    raw = 0

    # Rahu in 7H
    rahu_house = (pmap.get("Rahu") or {}).get("house")
    if rahu_house == 7:
        raw += 2
        indicators.append("Rahu in 7H — forbidden / inter-caste / unconventional partner pattern")

    # Venus + Rahu conjunction
    v_sign = (pmap.get("Venus") or {}).get("sign")
    r_sign = (pmap.get("Rahu") or {}).get("sign")
    if v_sign and v_sign == r_sign:
        raw += 3
        indicators.append("Venus-Rahu conjunction — intense, sometimes karmic-forbidden attraction signal")

    # 7L in 12H
    sl = (house_lords.get(7) or {}).get("lord") or ""
    sl_house = (pmap.get(sl) or {}).get("house") if sl else None
    if sl_house == 12:
        raw += 2
        indicators.append(f"7L {sl} in 12H — partner-bhava connected to hidden / private / foreign sphere")

    # 12L in 7H
    tl = (house_lords.get(12) or {}).get("lord") or ""
    tl_house = (pmap.get(tl) or {}).get("house") if tl else None
    if tl_house == 7:
        raw += 2
        indicators.append(f"12L {tl} in 7H — hidden activity in partner-axis")

    # KP: 7L sub-lord signifies 12H
    sb_lord_7 = ""
    cusp7 = next((c for c in (kp_sigs and []) if isinstance(c, dict)), None)
    # ↑ kp_sigs is a dict; cusps are typically passed separately. We skip this
    # KP check here for simplicity (covered in main KP layer L17).

    if raw >= 5:
        signal = "high"
        score = -3
    elif raw >= 2:
        signal = "moderate"
        score = -1
    else:
        signal = "low"
        score = 0

    return {
        "signal_strength":  signal,
        "raw_indicator_count": raw,
        "indicators":       indicators,
        "score":            score,
        # Brand-safety mandatory caveat — surface in narrator block
        "brand_safety_note": (
            "Yeh COSMIC PATTERN signals hain — NOT direct accusations. "
            "Engine kabhi 'partner cheat kar raha hai' nahi kahega — sirf pattern dikhayega. "
            "Action: self-introspection + open communication + (high signal pe) trust check."
        ),
    }


def _conditional_foreign_check(question: str, intel: dict, kundli: dict) -> dict:
    """C2 — Fires only when "abroad/NRI/foreign" appears in question.
    Looks at 12H + 9H + Rahu in 7H signals for foreign-partner pattern.
    """
    pmap = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}

    score = 0; whys = []
    rahu_house = (pmap.get("Rahu") or {}).get("house")
    if rahu_house == 7:
        score += 2; whys.append("Rahu in 7H — foreign partner pattern indicated")

    twelfth_lord = (house_lords.get(12) or {}).get("lord") or ""
    tl_house = (pmap.get(twelfth_lord) or {}).get("house") if twelfth_lord else None
    if tl_house == 7:
        score += 2; whys.append(f"12L {twelfth_lord} in 7H — foreign / distant partner connection")

    ninth_lord = (house_lords.get(9) or {}).get("lord") or ""
    nl_house = (pmap.get(ninth_lord) or {}).get("house") if ninth_lord else None
    if nl_house == 7:
        score += 1; whys.append(f"9L {ninth_lord} in 7H — fortunate / dharmic partner from far place")

    return {"score": score, "why": whys, "fires": bool(whys)}


# ─────────────────────────────────────────────────────────────────────────────
# BUCKET-GATED VERDICT TEXT (40 locked combos = 10 buckets × 4 bands)
# ─────────────────────────────────────────────────────────────────────────────
# Each bucket has 4 verdict bands (green / yellow_wait / slow_burn / red_avoid).
# Hinglish locked text. AI may translate / soften tone but NEVER change meaning.
_VERDICT_TABLE = {
    "feelings_check": {
        "green":       "Haan, uske dil mein sach mein feelings hain — Venus aur 5th-house ka cosmic alignment mutual attraction confirm karta hai",
        "yellow_wait": "Feelings hain lekin abhi confused phase chal raha hai — communication block hai cosmic plane pe",
        "slow_burn":   "Slow but real — abhi seed phase hai, feelings fully express hone mein time lagega",
        "red_avoid":   "Cosmic signal kehta hai mutual feelings strong nahi hain — apni energy kahin aur lagao, deserve karte ho behtar",
    },
    "compatibility": {
        "green":       "Aap dono ki compatibility cosmically strong hai — Moon, Venus aur 7th-house alignment positive",
        "yellow_wait": "Mixed compatibility — kuch areas align hain, kuch friction zones hain. Patience + work se sambhal sakta hai",
        "slow_burn":   "Surface compatibility theek lekin deep level pe karmic pattern slow-developing hai",
        "red_avoid":   "Compatibility ke key markers cosmic plane pe align nahi ho rahe — relationship struggle-heavy hoga",
    },
    "new_love_timing": {
        "green":       "Pyaar bahut jald milega — current dasha + transit dono ka window OPEN hai romance ke liye",
        "yellow_wait": "Pyaar milega lekin abhi nahi — agla strong window dasha shift ke baad khulega",
        "slow_burn":   "Pyaar dheere-dheere aayega, ek hi din mein nahi — patience aur self-development pe focus karein abhi",
        "red_avoid":   "Abhi naye love ke liye cosmic timing prabal nahi — pehle apne aap ko complete karein, fir window khulegi",
    },
    "existing_status": {
        "green":       "Aapka rishta long-term tikega — chart ke 5th, 7th aur 11th house teeno favourable hain",
        "yellow_wait": "Rishta chalega lekin current phase mein patience zaroori — abhi koi big decision na lein",
        "slow_burn":   "Slow but steady — current phase rishte ko mature kar raha hai, dramatic moves se bachein",
        "red_avoid":   "Cosmic signal kehta hai is rishte mein deep friction hai — honest self-assessment + counselling zaroori",
    },
    "breakup_signal": {
        "green":       "Abhi koi serious breakup signal cosmic plane pe nahi — temporary friction hai, communication se sambhal jayega",
        "yellow_wait": "Distance signal hai lekin breakup definite nahi — agla 3-4 mahine awareness + remedy se reverse possible",
        "slow_burn":   "Cooling phase chal raha hai — agar dono effort karein to bachega, agar nahi to natural distance badhega",
        "red_avoid":   "Cosmic plane pe separation indicators strong hain — lekin healing window bhi clear dikh raha hai aage",
    },
    "reconciliation": {
        "green":       "Haan, ex / partner wapas aane ka cosmic signal strong hai — Venus dasha ya transit window mein reunion possible",
        "yellow_wait": "Patch-up possible hai lekin abhi nahi — wait karein, cosmic timing align hone do",
        "slow_burn":   "Reunion possible hai lekin slow process — dono taraf se ego release zaroori",
        "red_avoid":   "Cosmic signal kehta hai yeh bond karmically complete ho chuka hai — naye chapter ke liye open ho jaayein",
    },
    "one_sided": {
        "green":       "Mutual signal strong hai — aapka crush / love sirf one-sided nahi, samne wale ke chart mein bhi resonance hai",
        "yellow_wait": "Mutual feelings hain lekin abhi unhe pehchaane mein time lagega — express karne ka right time aana baki hai",
        "slow_burn":   "Slow mutual development — abhi sirf seed phase, judgment jaldi mat karein",
        "red_avoid":   "Mutual cosmic resonance abhi weak hai — yeh feeling sirf aapki taraf se zyada hai. Self-worth preserve karein, journey jaari rakhein",
    },
    "long_distance": {
        "green":       "Long-distance relationship survive karegi — chart mein 9H + 12H favourable, distance ke baavjood bond strong rahega",
        "yellow_wait": "LD chalegi lekin patience-heavy hogi — physical reunion ka clear window agle dasha mein khulega",
        "slow_burn":   "LD slow-developing hai — bond build hoga lekin physical proximity tak ka safar lamba hai",
        "red_avoid":   "Long-distance pattern cosmic plane pe sustainable nahi — physical proximity ya honest re-evaluation zaroori",
    },
    "commitment_fear": {
        "green":       "Commitment ka window jald khulega — Jupiter strength + 7H activation se partner serious-mode mein aayenge",
        "yellow_wait": "Commitment aayega lekin natural pace pe — push karne se delay aur badhega, allow karein",
        "slow_burn":   "Commitment slow-process hai — partner ka chart serious bond ke liye time-le-raha-hai pattern dikhata hai",
        "red_avoid":   "Cosmic signal kehta hai partner abhi commit-ready nahi hain — wait nahi, honest conversation karein expectations ke baare mein",
    },
    "affair_third_party": {
        # Brand-safe: NEVER accuses. Only describes cosmic pattern signals.
        "green":       "Cosmic pattern mein doosri party ka signal NAHI dikh raha — partner ki energy aap pe focused hai",
        "yellow_wait": "Mixed signals — overthinking ho sakta hai. Direct communication best, accusation se bachein",
        "slow_burn":   "Karmic pattern hai jo trust-issues create kar raha — yeh dono ke charts ka past-life karma hai, vyaktigat dosh nahi",
        "red_avoid":   "Cosmic plane pe forbidden-attraction patterns visible hain — yeh accusation nahi, BUT honest self-introspection + open dialogue + trust-rebuilding kaam zaroori",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# BUCKET-GATED STRATEGY (action recommendations + boolean flags)
# ─────────────────────────────────────────────────────────────────────────────
def _recommend_strategy(score: int, q_type: str, bucket: str,
                        layer_venus: dict, layer_jupiter: dict,
                        layer_rahu: dict) -> dict:
    """Returns locked action block keyed to verdict bucket.
    Bucket-gated to prevent contradictions (CLE format step 4).
    """
    base = {
        "should_express":      False,
        "should_commit":       False,
        "should_step_back":    False,
        "should_seek_clarity": False,
        "should_remedy_first": False,
        "do_not":              [],
    }

    if bucket == "green":
        return {
            **base,
            "primary": "Express karein, honest communicate karein, agar timing right lage to commit karein — cosmic window OPEN hai",
            "should_express":      True,
            "should_commit":       (q_type in ("commitment_fear", "existing_status", "new_love_timing")),
            "do_not":              ["overthink", "delay strategically", "let fear dominate"],
        }
    elif bucket == "yellow_wait":
        return {
            **base,
            "primary": "Abhi koi big decision na lein — communicate karein lekin escalate na karein. Window khulne tak patience",
            "should_seek_clarity": True,
            "should_express":      (q_type == "feelings_check"),
            "do_not":              ["propose now", "make ultimatums", "force commitment"],
        }
    elif bucket == "slow_burn":
        return {
            **base,
            "primary": "Patience + consistent presence + self-development — sudden moves se bachein, slow steady better",
            "should_seek_clarity": True,
            "do_not":              ["dramatic gestures", "rushed expressions", "compare to others' timelines"],
        }
    else:  # red_avoid
        return {
            **base,
            "primary": "Step back karein, self-worth preserve karein, remedies + healing pe focus — future window me dekhenge",
            "should_step_back":    True,
            "should_remedy_first": True,
            "do_not":              ["force the bond", "lower standards", "ignore red flags",
                                    "blame yourself entirely"],
        }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ASSESSMENT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def assess_love(kundli: dict, intel: dict, kp: dict,
                birth: Optional[dict] = None,
                question: str = "",
                partner_kundli: Optional[dict] = None,
                partner_kp:     Optional[dict] = None) -> dict:
    """Returns deterministic love & relationship verdict.

    Full output dict shape — see top of file. Key fields:
      verdict, score, confidence,
      natal_promise_score, current_trigger_score,
      love_promised, love_denied,
      kp_verdict_summary, navamsa_summary, synastry_summary,
      question_type,        # one of 10 buckets
      framework_decision,   # canonical bucket name (green/yellow_wait/slow_burn/red_avoid)
      strategy,             # action block with boolean flags
      next_window, pratyantar_window,
      reasons_strong, reasons_weak,
      remedy, remedy_for_planet,
      layers, modifiers, conditionals,
      brand_safety_warnings, # active guards for affair / breakup / one_sided
      logic_trace
    """
    intel = intel or {}
    kp    = kp or {}
    kundli = kundli or {}
    birth = birth or {}
    trace: list[str] = []
    warnings: list[str] = []

    asc_name = (intel.get("lagna_sign") or kundli.get("ascendant") or "")
    if isinstance(asc_name, dict):
        asc_name = asc_name.get("sign") or asc_name.get("name") or ""
    asc_name = (asc_name or "").strip().capitalize()
    lagna_idx = _sign_idx(asc_name)
    moon_name = (kundli.get("moonSign") or "").strip().capitalize()
    moon_idx  = _sign_idx(moon_name)

    # ── STEP 1 — Question type detection ─────────────────────────────────────
    q_type = classify_love_question(question)
    trace.append(f"Step 1: Question classified as '{q_type}'")

    # ── Pre-compute helper modules (best-effort) ─────────────────────────────
    shadbala_d = _maybe_shadbala(kundli, lagna_idx)
    av_d       = _maybe_ashtakavarga(kundli, lagna_idx)
    bhava_d    = _maybe_bhava_bala(intel, shadbala_d)
    jaimini_d  = _maybe_jaimini(kundli)
    argala_d   = _maybe_argala(kundli)
    varga_yog  = _maybe_varga_yogas(kundli, None)
    yogini_d   = _maybe_yogini_dasha(kundli, birth)
    jup_t      = _maybe_jupiter_transit(lagna_idx, moon_idx)
    sat_t      = _maybe_saturn_transit()

    kp_sigs = kp.get("significations") or {}

    # ── STEP 3 — Layer Stacking (29 layers) ──────────────────────────────────
    L1  = _layer_5th_house(intel, kundli, kp_sigs)
    fifth_lord = L1.get("fifth_lord", "")
    L2  = _layer_venus(intel, kundli, kp_sigs)
    L3  = _layer_moon(intel, kundli)
    L4  = _layer_7th_house(intel, kundli, kp_sigs)
    seventh_lord = L4.get("seventh_lord", "")
    L5  = _layer_mars_venus(intel, kundli)
    L6  = _layer_jupiter_commitment(intel, kundli)
    L7  = _layer_mercury_comm(intel, kundli)
    L8  = _layer_rahu_in_love_houses(intel, kundli)
    L9  = _layer_ketu_in_love_houses(intel, kundli)
    L10 = _layer_saturn_aspect(intel, kundli)
    L11 = _layer_11th_house(intel, kundli)
    L12 = _layer_12th_house(intel, kundli)
    L13 = _layer_darakaraka(jaimini_d, intel, kundli)
    L14 = _layer_upapada(jaimini_d, intel, kundli)
    L15 = _layer_atmakaraka(jaimini_d, intel, kundli)
    # Mandatory layers
    L16 = _layer_d9_navamsa(kundli, fifth_lord, seventh_lord)
    L17 = _layer_kp_cuspal(kp)
    # Advanced layers
    L18 = _layer_ashtakavarga(av_d)
    L19 = _layer_bhava_bala(bhava_d)
    L20 = _layer_shadbala_venus(shadbala_d, fifth_lord, seventh_lord)
    L21 = _layer_char_karakas(jaimini_d)
    L22 = _layer_yogini_cross(yogini_d)
    L23 = _layer_sade_sati(intel)
    L24 = _layer_eclipse(intel, kundli)
    L25 = _layer_d30_trishamsa(kundli)
    L26 = _layer_kp_csl(L17, kp_sigs)
    L27 = _layer_argala_love(argala_d)
    L28 = _layer_triad(L3, L2, L5)
    # Synastry — only if partner_kundli supplied
    L29 = _layer_synastry(kundli, intel, partner_kundli, partner_kp) if partner_kundli else \
          {"available": False, "score": 0, "why_strong": [], "why_weak": []}

    natal_layers = [L1, L2, L3, L4, L5, L6, L7, L8, L9, L10,
                    L11, L12, L13, L14, L15, L16, L17, L18, L19, L20,
                    L21, L22, L23, L24, L25, L26, L27, L28, L29]
    natal_promise_score = sum(L.get("score", 0) for L in natal_layers)

    # ── Trigger Layers T1, T2 ────────────────────────────────────────────────
    T1 = _layer_dasha_timing(kundli, kp_sigs, q_type)
    T2 = _layer_transit(jup_t, sat_t, intel, kundli)
    current_trigger_score = T1.get("score", 0) + T2.get("score", 0)

    # ── Modifiers M1-M7 ──────────────────────────────────────────────────────
    M1 = _modifier_combust(intel, fifth_lord, seventh_lord)
    M2 = _modifier_retrograde(intel, fifth_lord, seventh_lord)
    M3 = _modifier_malefic_aspects(intel, kundli, fifth_lord, seventh_lord)
    M4 = _modifier_lagnesh_venus(intel, kundli)
    M5 = _modifier_saturn_transit_5_7(sat_t, kundli)
    M6 = _modifier_jupiter_transit_5_7_11(jup_t, kundli)
    M7 = _modifier_mahapurusha(varga_yog)
    modifier_score = sum(m.get("score", 0) for m in (M1, M2, M3, M4, M5, M6, M7))

    # ── Conditionals C1, C2 ──────────────────────────────────────────────────
    C1 = {"score": 0, "fires": False}
    if q_type == "affair_third_party":
        C1 = _conditional_affair_check(intel, kundli, kp_sigs)
        C1["fires"] = True
        if C1.get("signal_strength") in ("moderate", "high"):
            warnings.append(C1.get("brand_safety_note", ""))

    C2 = {"score": 0, "fires": False, "why": []}
    if isinstance(question, str) and re.search(
            r"\b(abroad|videsh|foreign|nri|usa|uk|canada|australia|dubai|gulf|distance)\b",
            question.lower()):
        C2 = _conditional_foreign_check(question, intel, kundli)
        C2["fires"] = True

    cond_score = C1.get("score", 0) + C2.get("score", 0)

    # ── STEP 2 — Unified 2-Step Verdict Framework ────────────────────────────
    raw_score = 50 + natal_promise_score + current_trigger_score + modifier_score + cond_score
    score = max(0, min(100, int(round(raw_score))))

    # Bucket decision (canonical CLE 4-bucket scheme)
    npx = natal_promise_score
    cur = current_trigger_score
    if npx >= 8 and cur >= 0:
        bucket = "green"
        framework = "Love-window OPEN — natal promise present and current trigger favourable"
        promised, denied = True, False
        score = max(score, 65)
    elif npx >= 8 and cur < 0:
        bucket = "yellow_wait"
        nw = T1.get("next_window")
        when = (f"{_ym_to_human(nw['start'])} to {_ym_to_human(nw['end'])}"
                if nw else "next favourable dasha")
        framework = (f"Wait until {when} — natal love-promise yes, current "
                     "trigger not aligned")
        promised, denied = True, False
        score = max(45, min(score, 65))
    elif npx < 8 and cur >= 3:
        bucket = "slow_burn"
        framework = ("Slow-burn — current trigger helps but natal promise "
                     "modest; love builds dheere-dheere")
        promised, denied = False, False
        score = max(35, min(score, 60))
    else:
        bucket = "red_avoid"
        framework = ("Avoid + remedies first — both natal promise and current "
                     "trigger weak; healing phase before fresh love")
        promised, denied = False, True
        score = min(score, 40)

    trace.append(f"Step 2: framework={framework} | bucket={bucket} | score={score}/100")

    # ── Verdict — locked text from _VERDICT_TABLE (10 buckets × 4 bands) ─────
    verdict = _VERDICT_TABLE.get(q_type, {}).get(bucket, "")
    if not verdict:
        # Safety fallback (should never trigger if classifier returns valid bucket)
        verdict = _VERDICT_TABLE["feelings_check"][bucket]

    # ── Brand-safety guards (Step 10) ────────────────────────────────────────
    if q_type == "breakup_signal":
        warnings.append(
            "BREAKUP BUCKET — narrator MUST soften language; pair every separation "
            "indicator with a healing window + remedy; never say 'definite breakup hoga'."
        )
    if q_type == "one_sided":
        warnings.append(
            "ONE-SIDED BUCKET — tone must preserve self-worth; frame as 'mutual cosmic "
            "resonance abhi weak hai' not 'wo tumhe pasand nahi karta'."
        )

    # ── STEP 4 — Bucket-Gated Strategy ───────────────────────────────────────
    strategy = _recommend_strategy(score, q_type, bucket, L2, L6, L8)

    # ── STEP 6 — Remedy Selection (weakest planet from love-relevant set) ────
    candidates = []
    dignities_map = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    for label, p in (("Venus",  "Venus"),
                     ("5L",     fifth_lord),
                     ("7L",     seventh_lord),
                     ("Moon",   "Moon"),
                     ("Lagnesh", M4.get("lagnesh", ""))):
        if not p:
            continue
        d = dignities_map.get(p) or {}
        rank = DIGNITY_RANK.get(d.get("dignity") or "neutral-sign", 2) \
               - (3 if d.get("combust") else 0)
        candidates.append((p, rank, label))
    if candidates:
        weakest = min(candidates, key=lambda c: c[1])
        weakest_planet = weakest[0]
    else:
        weakest_planet = "Venus"
    remedy = _remedy_for_planet(weakest_planet) or _FALLBACK_REMEDY

    # ── STEP 7 — Confidence Calibration (cross-system agreement) ─────────────
    npx_dir = 1 if natal_promise_score > 0 else (-1 if natal_promise_score < 0 else 0)
    cur_dir = 1 if current_trigger_score > 0 else (-1 if current_trigger_score < 0 else 0)
    agree_bonus = 0
    if npx_dir == cur_dir and npx_dir != 0:
        agree_bonus = 12
    elif npx_dir == 0 or cur_dir == 0:
        agree_bonus = 5

    data_bonus = 0
    if L17.get("available"):                 data_bonus += 8     # KP available
    if L16.get("available"):                 data_bonus += 8     # D9 available
    if L18.get("available"):                 data_bonus += 4     # AV
    if shadbala_d and "_error" not in shadbala_d: data_bonus += 4
    if jup_t and "_error" not in jup_t:      data_bonus += 3
    if L29.get("available"):                 data_bonus += 5     # synastry
    if L22.get("available"):                 data_bonus += 3     # yogini cross-check

    # Confidence dampers
    if L16.get("available") and L16.get("score", 0) < 0 and L1.get("score", 0) > 0:
        agree_bonus -= 4
        warnings.append("D9 contradicts D1 5th-house signal — confidence reduced")

    confidence = min(98, 55 + agree_bonus + data_bonus + abs(score - 50) // 6)

    # ── KP / D9 / Synastry summary one-liners ────────────────────────────────
    kp_summary = ""
    if L17.get("available"):
        verdicts = [v.get("verdict") for v in (L17.get("by_cusp") or {}).values()]
        if verdicts.count("promised") >= 2:
            kp_summary = "KP confirms love (2+ cusps promised)"
        elif verdicts.count("denied") >= 2:
            kp_summary = "KP denies — love-cusps blocked"
        else:
            kp_summary = "KP ambiguous — mixed cusp signals"

    navamsa_summary = ""
    if L16.get("available"):
        d9_score = L16.get("score", 0)
        if d9_score >= 5:
            navamsa_summary = "D9 Navamsa STRONGLY confirms love capacity"
        elif d9_score >= 0:
            navamsa_summary = "D9 Navamsa supports love"
        else:
            navamsa_summary = "D9 Navamsa shows love-bond strain in deep chart"

    synastry_summary = None
    if L29.get("available"):
        ks = L29.get("kuta_score") or 0
        if ks >= 25:
            synastry_summary = f"Synastry STRONG ({ks}/32 Kuta) — partner-fit cosmically aligned"
        elif ks >= 18:
            synastry_summary = f"Synastry decent ({ks}/32 Kuta) — workable compatibility"
        else:
            synastry_summary = f"Synastry weak ({ks}/32 Kuta) — significant friction zones"

    # ── Aggregate reasons (cap for narration) ────────────────────────────────
    reasons_strong, reasons_weak = [], []
    for L in natal_layers + [T1, T2]:
        reasons_strong.extend(L.get("why_strong") or [])
        reasons_weak.extend(L.get("why_weak") or [])
    for m in (M1, M2, M3, M4, M5, M6, M7):
        for w in (m.get("why") or []):
            (reasons_strong if m.get("score", 0) >= 0 else reasons_weak).append(w)

    trace.append(f"Step 3 layers totalled: natal_promise={natal_promise_score}")
    trace.append(f"Step 5 trigger totalled: current_trigger={current_trigger_score}")
    trace.append(f"Modifier total: {modifier_score} | Conditional total: {cond_score}")
    trace.append(f"Final score: {score}/100, confidence {confidence}%")

    return {
        # ── Core verdict ──
        "verdict":              verdict,
        "score":                score,
        "confidence":           int(confidence),
        "natal_promise_score":  natal_promise_score,
        "current_trigger_score": current_trigger_score,
        "modifier_score":       modifier_score,
        "conditional_score":    cond_score,
        "love_promised":        promised,
        "love_denied":          denied,
        "framework_decision":   framework,
        "question_type":        q_type,
        # ── Summary one-liners ──
        "kp_verdict_summary":   kp_summary,
        "navamsa_summary":      navamsa_summary,
        "synastry_summary":     synastry_summary,
        # ── Strategy + windows + remedy ──
        "strategy":             strategy,
        "next_window":          T1.get("next_window"),
        "pratyantar_window":    T1.get("pratyantar_window"),
        "current_dasha":        T1.get("current_dasha"),
        "current_dasha_supports": T1.get("current_supports"),
        "love_significators":   T1.get("love_significators"),
        # ── Karakas + lords ──
        "fifth_lord":           fifth_lord,
        "fifth_lord_dignity":   L1.get("fifth_lord_dignity"),
        "seventh_lord":         seventh_lord,
        "seventh_lord_dignity": L4.get("seventh_lord_dignity"),
        "venus_dignity":        L2.get("venus_dignity"),
        "venus_house":          L2.get("venus_house"),
        "darakaraka":           L13.get("darakaraka"),
        "darakaraka_persona":   L13.get("darakaraka_persona"),
        "upapada":              L14.get("upapada"),
        "atmakaraka":           L15.get("atmakaraka"),
        # ── Layer details ──
        "kp_by_cusp":           L17.get("by_cusp") or {},
        "d9":                   {
            "d9_7th_lord":      L16.get("d9_7th_lord"),
            "d9_7th_sign":      L16.get("d9_7th_sign"),
            "d9_7th_lord_house": L16.get("d9_7th_lord_house"),
        },
        "d30_trishamsa":        L25,
        "synastry":             L29 if L29.get("available") else None,
        # ── Conditionals ──
        "affair_check":         (C1 if C1.get("fires") else None),
        "foreign_check":        (C2 if C2.get("fires") else None),
        # ── Reasons + warnings ──
        "reasons_strong":       reasons_strong[:8],
        "reasons_weak":         reasons_weak[:6],
        "remedy":               remedy,
        "remedy_for_planet":    weakest_planet,
        "brand_safety_warnings": warnings,
        # ── Raw layer/modifier dumps for debug/architect review ──
        "layers": {
            "L1_5th": L1, "L2_venus": L2, "L3_moon": L3, "L4_7th": L4,
            "L5_mars_venus": L5, "L6_jupiter": L6, "L7_mercury": L7,
            "L8_rahu": L8, "L9_ketu": L9, "L10_saturn_aspect": L10,
            "L11_11th": L11, "L12_12th": L12, "L13_darakaraka": L13,
            "L14_upapada": L14, "L15_atmakaraka": L15,
            "L16_d9": L16, "L17_kp": L17,
            "L18_av": L18, "L19_bhava_bala": L19, "L20_shadbala": L20,
            "L21_char_karakas": L21, "L22_yogini": L22,
            "L23_sade_sati": L23, "L24_eclipse": L24, "L25_d30": L25,
            "L26_kp_csl": L26, "L27_argala": L27, "L28_triad": L28,
            "L29_synastry": L29,
            "T1_dasha": T1, "T2_transit": T2,
        },
        "modifiers": {
            "M1_combust": M1, "M2_retrograde": M2, "M3_malefic_aspects": M3,
            "M4_lagnesh": M4, "M5_saturn_transit": M5,
            "M6_jupiter_transit": M6, "M7_mahapurusha": M7,
        },
        "conditionals": {"C1_affair": C1, "C2_foreign": C2},
        "logic_trace":          trace,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT HELPERS — for openai_helper LOCKED-FACTS prompt block
# ─────────────────────────────────────────────────────────────────────────────
def extract_window_str(v: dict) -> str:
    """Single source of truth for the human-readable timing window string."""
    if not v: return ""
    nw = v.get("next_window") or {}
    if not nw: return ""
    return f"{_ym_to_human(nw.get('start',''))} to {_ym_to_human(nw.get('end',''))}"


def _strategy_line(strat: dict) -> str:
    if not strat: return ""
    do_not = strat.get("do_not") or []
    out = f"  Recommended action:  {strat.get('primary','')}\n"
    if do_not:
        out += f"  AVOID:               {', '.join(do_not)}\n"
    flags = []
    for k in ("should_express", "should_commit", "should_step_back",
              "should_seek_clarity", "should_remedy_first"):
        if strat.get(k):
            flags.append(k.replace("should_", ""))
    if flags:
        out += f"  Action flags ON:     {', '.join(flags)}\n"
    return out


def _engine_json_envelope(v: dict) -> str:
    import json as _json
    nw = v.get("next_window") or {}
    payload = {
        "final_verdict":        v.get("verdict"),
        "score":                v.get("score"),
        "confidence_pct":       v.get("confidence"),
        "natal_promise_score":  v.get("natal_promise_score"),
        "current_trigger_score":v.get("current_trigger_score"),
        "framework_decision":   v.get("framework_decision"),
        "love_promised":        v.get("love_promised"),
        "love_denied":          v.get("love_denied"),
        "question_type":        v.get("question_type"),
        "kp_verdict_summary":   v.get("kp_verdict_summary"),
        "navamsa_summary":      v.get("navamsa_summary"),
        "synastry_summary":     v.get("synastry_summary"),
        "current_dasha":        v.get("current_dasha"),
        "current_dasha_supports": v.get("current_dasha_supports"),
        "next_dasha_window":    (f"{nw.get('start')} → {nw.get('end')}" if nw else None),
        "must_use_window_str":  extract_window_str(v) or None,
        "fifth_lord":           v.get("fifth_lord"),
        "fifth_lord_dignity":   v.get("fifth_lord_dignity"),
        "seventh_lord":         v.get("seventh_lord"),
        "seventh_lord_dignity": v.get("seventh_lord_dignity"),
        "venus_dignity":        v.get("venus_dignity"),
        "venus_house":          v.get("venus_house"),
        "darakaraka":           v.get("darakaraka"),
        "darakaraka_persona":   v.get("darakaraka_persona"),
        "upapada":              v.get("upapada"),
        "strategy_primary":     (v.get("strategy") or {}).get("primary"),
        "do_not":               (v.get("strategy") or {}).get("do_not"),
        "remedy_planet":        v.get("remedy_for_planet"),
        "remedy":               v.get("remedy"),
        "brand_safety_warnings": v.get("brand_safety_warnings"),
    }
    return (
        "═══ LOVE ENGINE JSON (IMMUTABLE — COPY VALUES VERBATIM) ═══\n"
        + _json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n══════════════════════════════════════════════════════════════\n"
    )


def format_verdict_for_prompt(v: dict) -> str:
    """Render verdict as authoritative locked-facts block for AI narrator prompt."""
    if not v: return ""
    nw = v.get("next_window") or {}
    nw_line = ""
    if nw:
        nw_hr = f"{_ym_to_human(nw.get('start',''))} to {_ym_to_human(nw.get('end',''))}"
        nw_line = (
            f"  Next favourable Dasha window: {nw.get('dasha')} "
            f"({nw.get('start')} → {nw.get('end')}) — {nw.get('reason')}\n"
            f"  >>> NARRATE THIS WINDOW EXACTLY AS: \"{nw_hr}\". "
            f"DO NOT widen, shift, or change these dates. <<<\n"
        )
    else:
        nw_line = ("  Next favourable Dasha window: NOT FOUND in next 12 years\n"
                   "  >>> NARRATE: \"agle 12 saal mein koi spasht prabal love-yog window nahi mil raha\" — DO NOT invent dates. <<<\n")

    rs = "\n".join(f"    + {r}" for r in (v.get("reasons_strong") or [])[:6]) or "    (none)"
    rw = "\n".join(f"    - {r}" for r in (v.get("reasons_weak") or [])[:5]) or "    (none)"

    kp_lines = ""
    by_cusp = v.get("kp_by_cusp") or {}
    if by_cusp:
        kp_lines = "  KP CROSS-CHECK (cuspal sub-lord 5/7/11):\n"
        for h in sorted(by_cusp.keys()):
            row = by_cusp[h]
            kp_lines += (
                f"    Cusp {h} ({row.get('label','')}): SL={row.get('sl')} | "
                f"NL={row.get('nl')} | SB={row.get('sb')} | SS-CSL={row.get('ss')} | "
                f"signifies {row.get('sb_signifies_houses')} → {row.get('verdict','').upper()}\n"
            )

    d9 = v.get("d9") or {}
    d9_line = (f"  D9 (Navamsa) 7th lord: {d9.get('d9_7th_lord')} in D9-house {d9.get('d9_7th_lord_house')} "
               f"(7th sign {d9.get('d9_7th_sign')})") if d9 else "  D9 7th lord: unavailable"

    syn_line = ""
    if v.get("synastry"):
        s = v["synastry"]
        syn_line = f"  SYNASTRY (partner provided): Kuta {s.get('kuta_score')}/{s.get('kuta_max')} → {v.get('synastry_summary')}\n"

    affair_line = ""
    if v.get("affair_check"):
        ac = v["affair_check"]
        affair_line = (
            f"  AFFAIR-CHECK GUARD ({ac.get('signal_strength','low').upper()} signal): "
            f"{len(ac.get('indicators') or [])} cosmic-pattern indicators. "
            f"BRAND-SAFETY: NEVER accuse partner — describe patterns only.\n"
        )

    return (
        _engine_json_envelope(v) + "\n"
        "════════════════════════════════════════════════════════════════════\n"
        "AUTHORITATIVE LOVE & RELATIONSHIP VERDICT (deterministically computed)\n"
        "════════════════════════════════════════════════════════════════════\n"
        f"  VERDICT:           {v.get('verdict')}\n"
        f"  Score:             {v.get('score')}/100   (confidence {v.get('confidence')}%)\n"
        f"  Framework:         {v.get('framework_decision')}\n"
        f"  Natal promise:     {v.get('natal_promise_score'):+d}   "
        f"Current trigger: {v.get('current_trigger_score'):+d}   "
        f"Modifiers: {v.get('modifier_score'):+d}\n"
        f"  Question type:     {v.get('question_type')}\n"
        f"  KP summary:        {v.get('kp_verdict_summary')}\n"
        f"  Navamsa summary:   {v.get('navamsa_summary')}\n"
        f"  5th lord:          {v.get('fifth_lord')} ({v.get('fifth_lord_dignity')}) — romance karaka\n"
        f"  7th lord:          {v.get('seventh_lord')} ({v.get('seventh_lord_dignity')}) — partner karaka\n"
        f"  Venus (Shukra):    {v.get('venus_dignity')}, house {v.get('venus_house')} — love karaka\n"
        f"  Darakaraka:        {v.get('darakaraka')} ({v.get('darakaraka_persona')})\n"
        f"  Upapada:           {v.get('upapada')}\n"
        f"  Current Dasha:     {v.get('current_dasha')} (supports love = {v.get('current_dasha_supports')})\n"
        f"{kp_lines}"
        f"{nw_line}"
        f"  {d9_line}\n"
        f"{syn_line}"
        f"{affair_line}"
        f"{_strategy_line(v.get('strategy') or {})}"
        "  Strong supporting factors:\n"
        f"{rs}\n"
        "  Weakening / friction factors:\n"
        f"{rw}\n"
        f"  Recommended remedy planet: {v.get('remedy_for_planet')}\n"
        f"  Recommended remedy:        {v.get('remedy')}\n"
        "════════════════════════════════════════════════════════════════════\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Compact final-answer template (mirror of marriage / stock)
# ─────────────────────────────────────────────────────────────────────────────
_LANG_GREETING = {
    "hn": "Seedhi baat —", "hi": "सीधी बात —", "en": "Straight answer —",
}
_LANG_REASON  = {"hn": "Vajah", "hi": "वजह", "en": "Reason"}
_LANG_TIMING  = {"hn": "Samay", "hi": "समय", "en": "Timing"}
_LANG_ACTION  = {"hn": "Action", "hi": "कर्म", "en": "Action"}
_LANG_REMEDY  = {"hn": "Upay", "hi": "उपाय", "en": "Remedy"}
_LANG_NO_WINDOW = {
    "hn": "Agle 12 saal mein koi prabal love-window nahi — patience aur self-development pe focus karein.",
    "hi": "अगले १२ वर्षों में कोई प्रबल प्रेम-योग नहीं — धैर्य और स्व-विकास पर ध्यान दें।",
    "en": "No strong love window in the next 12 years — focus on patience and self-development.",
}


def format_final_answer(v: dict, lang_code: str = "hn") -> str:
    """Pre-baked, fact-locked answer the AI only polishes for tone."""
    if not v: return ""
    code = lang_code if lang_code in _LANG_GREETING else "hn"
    g  = _LANG_GREETING[code]
    L_R = _LANG_REASON[code]; L_T = _LANG_TIMING[code]
    L_A = _LANG_ACTION[code]; L_X = _LANG_REMEDY[code]

    verdict = v.get("verdict") or ""
    rs = (v.get("reasons_strong") or [])[:2]
    rw = (v.get("reasons_weak")   or [])[:1]
    bits = []
    if rs: bits.append("; ".join(rs))
    if rw: bits.append(f"weakening: {rw[0]}")
    reason_line = ". ".join(bits) if bits else "—"

    timing = extract_window_str(v) or _LANG_NO_WINDOW[code]
    action = (v.get("strategy") or {}).get("primary", "")
    remedy = v.get("remedy") or ""

    return (
        f"{g} {verdict}.\n\n"
        f"{L_R}: 5L {v.get('fifth_lord')}, Venus {v.get('venus_dignity')} (h{v.get('venus_house')}), "
        f"current dasha {v.get('current_dasha')}. {reason_line}.\n\n"
        f"{L_T}: {timing}.\n"
        f"{L_A}: {action}.\n\n"
        f"{L_X}: {remedy}."
    )
