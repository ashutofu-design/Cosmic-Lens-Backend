"""
career_engine.py — Deterministic Career & Profession verdict engine (Vedic / KP).

Mirror of love_engine.py + marriage_engine.py + stock_engine.py architecture
(CLE format): pure-Python rule engine that consumes the already-computed
kundli + chart_intelligence + KP outputs and produces a structured career
verdict BEFORE the AI is invoked. The AI then acts purely as a NARRATOR
that converts this verdict into Hinglish prose — it MUST NOT change verdict,
score, timing window, strategy, or remedy.

Inputs:
    kundli  : dict from kundli_engine.calculate_kundli (has planets, dashas,
              currentDasha, ascendant, moonSign, divisionalCharts D9/D10...)
    intel   : dict from chart_intelligence.analyze_chart (has dignities,
              house_lords, yogas, mangal_dosh, sade_sati, lagna_sign)
    kp      : dict from kp_engine.calculate_kp (has cusps, planets,
              significations) — for KP cuspal sub-lord cross-check
    birth   : optional dict with at least "gender", "dob" so dasha + transit
              calculations are correct
    question: raw user text — drives the 8-bucket question classifier
              (job_change / promotion / govt_job / transfer / resignation /
              career_setback / career_field_choice / general_career).
    boss_kundli    : optional dict — boss/manager natal, activates boss synastry
    partner_kundli : optional dict — business-partner natal, activates partner synastry

Output: see assess_career().__doc__

CLE Format Logic Framework (10 standard steps, mirror of love_engine):
    Step 1  — Question Type Detection (8-bucket classifier) + Tense Detector
    Step 2  — 2-Step Verdict Framework (natal_promise + current_trigger → bucket)
    Step 3  — Layer Stacking (32 layers + D9 + D10 + KP mandatory + Amatyakaraka)
    Step 4  — Bucket-Gated Strategy (no contradictions allowed)
    Step 5  — Timing Window (Vimshottari + Yogini + Saturn/Jupiter transits + KP)
    Step 6  — Remedy Selection (weakest career planet → mantra/donation/gemstone)
    Step 7  — Confidence Calibration (cross-system agreement)
    Step 8  — Format-for-Prompt (locked Hinglish verdict block)
    Step 9  — AI Narrator Override (turn-level rules in openai_helper)
    Step 10 — Brand-Safety Guards (govt-job, resignation softening)

Layer rubric (canonical CLE table — career-specific):
    A. NATAL PROMISE  (Layers 1-18)
        L1  10th house + 10L deep dive            (weight 16)  ⭐ CORE career
        L2  Sun (authority/govt karaka)           (weight 12)
        L3  Saturn (service/karma karaka)         (weight 12)
        L4  Mercury (business/commerce karaka)    (weight 10)
        L5  Mars (technical/competition karaka)   (weight  8)
        L6  Jupiter (wisdom/expansion karaka)     (weight 10)
        L7  Venus (creative/luxury karaka)        (weight  5)
        L8  Moon (public-facing karaka)           (weight  5)
        L9  6th house + 6L (job/service)          (weight 10)
        L10 2nd house + 2L (income capacity)      (weight  9)
        L11 11th house + 11L (gains/promotion)    (weight 10)
        L12 7th house + 7L (business/partners)    (weight  8)
        L13 9th house + 9L (luck/foreign)         (weight  7)
        L14 5th house + 5L (speculation/leader)   (weight  6)
        L15 Lagna lord position (self-strength)   (weight  6)
        L16 Amatyakaraka (Jaimini career karaka)  (weight 10)  ⭐ MANDATORY
        L17 Atmakaraka in 10/2/11/6 (soul aligned)(weight  6)
        L18 D9 Navamsa overlay (10L+AmK)          (weight 10)  ⭐ MANDATORY
    B. DIVISIONAL + KP (Layers 19-23)
        L19 D10 Dashamsa overlay                  (weight 14)  ⭐ MANDATORY
        L20 D24 Chaturvimshamsa (education feed)  (weight  4)
        L22 KP cuspal sub-lord 6/10/2/11          (weight 12)  ⭐ MANDATORY
        L23 KP Ruling Planets (prashna)           (weight  5)
    C. STRENGTH LAYERS (Layers 24-27)
        L24 Ashtakavarga 10H BAV + Sun/Saturn BAV (weight  6)
        L25 Shadbala (10L, Sun, Sat, Mer, Jup)    (weight  6)
        L26 Bhava Bala (10/6/2/11)                (weight  5)
        L27 Char karakas longitude order          (weight  4)
    D. YOGA LAYERS (Layers 28-30) ⭐ critical for career
        L28 Raja Yogas (Kendra-Trikona, 9L+10L)   (weight  9)
        L29 Dhana Yogas (2L+11L, 5L+11L)          (weight  8)
        L30 Pancha-Mahapurusha + Career-yogas     (weight  9)
    E. ANTI-YOGA + ECLIPSE LAYERS (Layers 31-32)
        L31 Daridra/Kemadruma/Nicha-bhanga         (weight  5  ±)
        L32 Sade Sati on 10H/10L + Eclipse on 10L (weight  5  ±)
    F. CROSS-CHECK LAYERS
        L34 10H-2H-11H wealth-creation triad      (weight  6)
    G. TRIGGER LAYERS — is the natal promise activated NOW?
        T1  Vimshottari MD+AD+PD timing            (weight 12)
        T2  Saturn transit on 10H/10L (career chg) (weight  7)
        T3  Jupiter transit on 10H/2H/11H + Yogini (weight  7)
    H. MODIFIERS (±points, no own weight)
        M1  10L / Sun / Mercury combust            (±5)
        M2  10L / Saturn / Jupiter retrograde      (±3)
        M3  Malefic aspects on 10H/10L/AmK          (±5)
        M4  Lagnesh strength (self-capability)      (±3)
        M5  Saturn transit modifier (sade-sati/dhaiya)(-5)
        M6  Jupiter transit on 10/2/11             (+6)
        M8  Rahu-Ketu axis on 10/4 (sudden change) (±5)
    I. CONDITIONALS (only when question type matches) — each uses
        bucket-tuned KP cusp/CSL check via _kp_bucket_assist().
        C1  Govt-job check (Sun strong + 10L exalt + Sun-Mars-Jup combo)
            — fires for q_type == "govt_job" or strong govt-promise
        C4  Promotion-window check (current AD/PD activates 10H/11H)
            — fires for q_type == "promotion"
        C5  Career-setback recovery check (when next Jupiter clears
            + KP cusps 8/12/11 cross-check)
            — fires for q_type == "career_setback"
        C7  Transfer probability (Saturn transit + KP cusps 3/12/10)
            — fires for q_type == "transfer"
        C8  Resignation viability (KP cusps 12/6/1 + AD lord exit signal)
            — fires for q_type == "resignation"
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

# Career-favourable houses (KP rule for 6/10/2/11 cusps)
CAREER_PROMISE  = {2, 6, 10, 11}     # 2=income, 6=service/job, 10=karma/profession, 11=gains
CAREER_DENIAL   = {5, 8, 12}          # 5=speculation/leisure, 8=obstacles, 12=loss/expenses
BUSINESS_HOUSES = {7, 10, 11}         # 7=public/partnership, 10=karma, 11=fulfillment
SERVICE_HOUSES  = {6, 10, 2}          # 6=service, 10=karma, 2=salary
GOVT_HOUSES     = {10, 9, 1}          # 10=karma, 9=dharma/govt, 1=self-status
FOREIGN_HOUSES  = {9, 12, 3}          # 9=long-journey, 12=foreign-land, 3=short-travel

# Career planet → field mapping (for field_recommendation logic)
PLANET_FIELDS = {
    "Sun":     ["government", "PSU", "leadership", "administration", "politics",
                "civil services", "medicine (head/heart specialist)", "gold/jewelry"],
    "Saturn":  ["service/corporate job", "labour-intensive industry", "iron/steel",
                "mining", "construction", "elder-care", "long-term roles", "judiciary clerk"],
    "Mercury": ["business", "commerce", "IT/software", "accounting", "writing",
                "communications", "banking", "trading", "publishing", "data analytics"],
    "Mars":    ["engineering", "military/police", "sports", "surgery", "real-estate",
                "manufacturing", "metals", "construction", "technical roles", "fitness"],
    "Jupiter": ["teaching", "advisory/consulting", "judiciary", "law", "religious work",
                "finance/banking-guru", "content creation", "spiritual coaching"],
    "Venus":   ["arts", "fashion", "media", "hospitality", "luxury goods", "design",
                "music/dance", "cosmetics", "vehicles", "entertainment"],
    "Moon":    ["public-facing roles", "hospitality", "water/dairy industry",
                "healthcare", "psychology/counselling", "mother-related work",
                "imports", "fluid-related business"],
    "Rahu":    ["foreign work", "technology", "electronics", "photography/videography",
                "aviation", "social media", "cinema", "crypto/unconventional finance",
                "pharmaceuticals", "research/science"],
    "Ketu":    ["research", "occult/spirituality", "IT (deep-tech)",
                "medical research", "moksha-related work", "niche specialisations"],
}

# One-line emergency fallback (used only if remedies.py unavailable)
_FALLBACK_REMEDY = (
    'Apne ishta-devta ki upasana karein aur ek mahine tak roz '
    'Aditya Hridaya Stotra padhein'
)

# Day-name → Hindi vaar (for narration)
_DAY_HI = {
    "Sunday":    "Ravivar",  "Monday":   "Somvar",   "Tuesday":  "Mangalvar",
    "Wednesday": "Budhvar",  "Thursday": "Guruvar",  "Friday":   "Shukravar",
    "Saturday":  "Shanivar",
}

# Months for human-readable window strings
_MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]


def _ym_to_human(ym: str) -> str:
    """Convert 'YYYY-MM' to 'Mmm YYYY' for narration."""
    if not isinstance(ym, str) or len(ym) < 7:
        return ym or ""
    try:
        y, m = ym.split("-")[:2]
        mi = int(m)
        if 1 <= mi <= 12:
            return f"{_MONTH_NAMES[mi-1]} {y}"
    except (ValueError, IndexError):
        pass
    return ym


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION CLASSIFIER — 8 buckets
# ─────────────────────────────────────────────────────────────────────────────
# Ordered most-specific → most-general. First match wins. Each bucket has
# multiple regex patterns covering English, Hinglish, and Devanagari Hindi
# question phrasings.
_Q_PATTERNS: list[tuple[str, list[str]]] = [
    # ── GOVERNMENT JOB ── (high-priority — must beat generic job_change)
    ("govt_job", [
        r"\b(govt|govt\.?|government|sarkari|saarkari|sarkar)\b.*\b(job|naukri|naukari|kaam|exam|service)\b",
        r"\b(job|naukri|naukari|service)\b.*\b(govt|govt\.?|government|sarkari|saarkari)\b",
        r"\b(upsc|ssc|ibps|rrb|cgl|chsl|bank po|po exam|psc|mpsc|uppsc|bpsc)\b",
        r"\b(ias|ips|ifs|irs|ies|isro|drdo|psu|psu job|ongc|sail|bhel)\b",
        r"\b(railway|defense|defence|army|navy|airforce|air force|police|cisf|crpf|bsf)\b.*\b(job|exam|naukri|joining|selection)\b",
        r"\b(competitive exam|competitive)\b.*\b(crack|clear|pass|select)\b",
        r"\bक्या\b.*\b(सरकारी|राज्य)\b.*\b(नौकरी|काम)\b",
        r"\b(सरकारी|राज्य)\b.*\b(नौकरी|काम|एग्जाम|परीक्षा)\b",
    ]),
    # ── PROMOTION / SALARY HIKE ──
    ("promotion", [
        r"\b(promotion|promote|promoted|elevated|elevation)\b",
        r"\b(salary|hike|increment|appraisal|raise|bonus)\b.*\b(kab|when|milegi|milega|hoga|hogi)\b",
        r"\b(salary|hike|increment|appraisal|raise)\b",
        r"\b(badhti|badhega|badhegi|barhegi|barhega)\b.*\b(salary|tankhwah|paisa|kamayi)\b",
        r"\b(higher position|senior role|lead role|manager|head|director)\b.*\b(milega|milegi|kab|when|hoga)\b",
        r"\b(rank|position|grade|level)\b.*\b(badhega|badhegi|upgrade|promote)\b",
        r"\b(प्रमोशन|पदोन्नति|वेतन वृद्धि|तरक्की)\b",
    ]),
    # ── RESIGNATION (must come BEFORE job_change for "resign/quit/notice"
    # specificity, but does NOT match generic "company chod di" — that goes
    # to job_change because it implies switching, not quitting outright) ──
    ("resignation", [
        r"\b(resign|resignation|resignations|notice de|notice serve)\b",
        r"\b(quit|quitting)\b.*\b(job|naukri|sahi|theek|achha|right|karna|karu|chahiye)\b",
        r"\b(quit|leaving|leave)\b.*\b(job|naukri)\b",
        r"\b(chod|chhod|chodu|chhodu|chodna|chhodna|chodkar|chod kar|chhod kar)\b.*\b(job|naukri|kaam)\b",
        # Reverse word-order: "naukri chod kar..." (Hinglish OBJ-VERB) — only
        # job/naukri/kaam, not "company" (company-chod = job_change).
        r"\b(job|naukri|naukari|kaam)\b.*\b(chod|chhod|chodu|chhodu|chodna|chhodna|chodkar|chod kar|chhod kar|chodne|chhodne)\b",
        r"\b(notice period|serve notice)\b",
        r"\b(istefa|istifa)\b",
        r"\b(त्यागपत्र|इस्तीफा|नौकरी छोड़|काम छोड़)\b",
    ]),
    # ── TRANSFER ──
    ("transfer", [
        r"\b(transfer|posting|relocation|relocate)\b",
        r"\b(transfer|posting)\b.*\b(kab|when|hoga|hogi|milegi)\b",
        r"\b(shift|move)\b.*\b(office|branch|location|city|posting)\b",
        r"\b(deputation|secondment)\b",
        r"\b(तबादला|ट्रांसफर|पोस्टिंग)\b",
    ]),
    # ── CAREER SETBACK ──
    ("career_setback", [
        r"\b(career)\b.*\b(stuck|setback|down|bad|loss|failed|fail|crisis|problem)\b",
        r"\b(notice|warning|terminat|fire|fired|laid off|layoff|lay-?off|sack|sacked)\b",
        r"\b(job|naukri|kaam|career)\b.*\b(loss|chala gaya|gaya|gayi|gone|kho|khoya|khoyi)\b",
        r"\b(fail|failed|not selected|rejected|reject|hara|haar|haara)\b.*\b(interview|exam|job|naukri|selection)\b",
        r"\b(downgrade|demoted|demotion|step down)\b",
        r"\b(career)\b.*\b(end|over|tabaah|barbaad|barbad|finished)\b",
        r"\b(कैरियर|करियर)\b.*\b(अटका|खराब|बंद|खत्म|डूब)\b",
    ]),
    # ── JOB CHANGE ──
    ("job_change", [
        r"\b(job|naukri|naukari|kaam|company|firm|organization|organisation)\b.*\b(change|switch|badal|badalna|change karu|switch karu|chod|chhod)\b",
        r"\b(change|switch|badal|badalna)\b.*\b(job|naukri|naukari|kaam|company|firm)\b",
        r"\b(switch|switching)\b.*\b(karu|karna|karoge|karenge|sahi|theek|right|company|firm|kaam|industry)\b",
        r"\b(new|naya|nayi|naye|fresh)\b.*\b(job|naukri|opportunity|kaam|role|position|company)\b.*\b(change|switch|join)\b",
        r"\b(career|profession)\b.*\b(change|switch|badal|shift)\b",
        r"\b(company)\b.*\b(chod|chhod|chodi|chhodi|chod di|chhod di|left|leave)\b",
        r"\b(छोड़कर|बदल|स्विच|चेंज)\b.*\b(नौकरी|काम|कंपनी)\b",
    ]),
    # ── CAREER FIELD CHOICE ──
    ("career_field_choice", [
        r"\b(it|software|engineering|engineer|cs|coding|developer)\b.*\b(vs|ya|ya phir|or)\b.*\b(govt|sarkari|business|finance|banking|teaching|medicine|doctor|cas)\b",
        r"\b(career|kaam|profession|field)\b.*\b(choose|chunna|chuno|select|pick|decide|lu|lun|loon|le lu)\b",
        r"\b(kaunsi|kaun si|kaunsa|kaun sa|konsa|konsi|which)\b.*\b(field|career|line|profession|industry|sector|stream|path|career path)\b",
        r"\b(career path|career stream)\b",
        r"\b(stream|specialisation|specialization)\b.*\b(galat|sahi|theek|right|wrong|kharab|achha|change|badal)\b",
        r"\b(arts|commerce|science|engineering|medical|law|management)\b.*\b(better|achha|theek|sahi|prefer)\b",
        r"\b(field|line|profession|career path)\b.*\b(suitable|sahi|theek|achha|right|best)\b.*\b(mere|mera|me|my)\b",
        r"\b(किस|कौन सी|कौनसी)\b.*\b(लाइन|फील्ड|करियर|पेशा)\b",
    ]),
]


# Sprint-25 Fix-B: AI-Ear-trusted career bucket vocabulary.
_VALID_CAREER_BUCKETS = frozenset({
    "govt_job", "promotion", "resignation",
    "transfer", "career_setback",
    "job_change", "career_field_choice", "general_career",
})


def classify_career_question(text: str,
                             pre_classified_bucket: str | None = None) -> str:
    """Return one of:
      govt_job | promotion | resignation | transfer | career_setback |
      job_change | career_field_choice | general_career

    Default: "general_career" (most generic career fallback).
    Order matters — most specific patterns checked first.

    When `pre_classified_bucket` (Sprint-25 AI-Ear handoff) is in the
    engine's known vocabulary, return it directly — bypassing regex.
    """
    if pre_classified_bucket and pre_classified_bucket in _VALID_CAREER_BUCKETS:
        return pre_classified_bucket
    if not isinstance(text, str) or not text.strip():
        return "general_career"
    s = text.lower().strip()
    for bucket, pats in _Q_PATTERNS:
        for pat in pats:
            try:
                if re.search(pat, s):
                    return bucket
            except re.error:
                continue
    # Fallback: if any career vocabulary present, return general_career
    if re.search(r"\b(career|job|naukri|kaam|business|profession|service|"
                 r"vyapar|dhanda|kaam-dhandha|career path|line|field|"
                 r"नौकरी|काम|व्यापार|करियर|पेशा)\b", s):
        return "general_career"
    return "general_career"


# ─────────────────────────────────────────────────────────────────────────────
# TENSE DETECTOR — for tense-aware narration (FUTURE prediction vs PRESENT
# diagnosis vs GENERAL/timeless). Same pattern as love_engine.
#   - PRESENT  → emphasise CURRENT Maha-Antar-Pratyantar lords + active transit
#   - FUTURE   → emphasise next dasha window + upcoming Saturn/Jupiter transits
#   - GENERAL  → balance both
# ─────────────────────────────────────────────────────────────────────────────
_TENSE_FUTURE_RX = re.compile(
    r"\b(will|shall|going to|gonna|"
    r"karega|karegi|karenge|hoga|hogi|honge|dega|degi|denge|"
    r"milega|milegi|milenge|aayega|aayegi|aayenge|"
    r"banega|banegi|banenge|jayega|jayegi|jayenge|"
    r"lagega|lagegi|lagenge|"
    r"nikleg|niklega|niklegi|nikalega|nikalegi|sakega|sakegi|"
    r"future|aage|aage chal|baad mein|baad me|"
    r"kab|kab tak|jaldi|kabhi|kabhi bhi|never)\b"
    r"|भविष्य|आगे|कब|करेगा|करेगी|होगा|होगी|मिलेगा|मिलेगी|"
    r"देगा|देगी|देंगे|जाएगा|जाएगी|बनेगा|बनेगी|आएगा|आएगी|निकलेगा|निकलेगी|लगेगा|लगेगी",
    re.IGNORECASE,
)
_TENSE_PRESENT_RX = re.compile(
    r"\b(now|right now|currently|today|"
    r"abhi|aaj|aaj kal|aajkal|filhal|fil[- ]?haal|"
    r"chal raha|chal rahi|chal rahe|kar raha|kar rahi|kar rahe|"
    r"ho raha|ho rahi|ho rahe|de raha|de rahi|de rahe|"
    r"mil raha|mil rahi|mil rahe|"
    r"hai kya|hai\?|hai$|present(?:ly)?)\b"
    r"|अभी|आज|आजकल|वर्तमान|चल रहा|कर रहा|हो रहा",
    re.IGNORECASE,
)


def detect_question_tense(text: str) -> str:
    """Return 'future' | 'present' | 'general'.
    PRESENT wins on tie when explicit present markers (abhi/currently/chal raha).
    """
    if not isinstance(text, str) or not text.strip():
        return "general"
    s = text.lower().strip()
    has_present = bool(_TENSE_PRESENT_RX.search(s))
    has_future  = bool(_TENSE_FUTURE_RX.search(s))
    if has_present and not has_future:
        return "present"
    if has_future and not has_present:
        return "future"
    if has_present and has_future:
        if re.search(r"\b(abhi|aaj kal|aajkal|currently|right now|now|"
                     r"chal raha|kar raha|ho raha|de raha|mil raha)\b", s):
            return "present"
        return "future"
    return "general"


# ─────────────────────────────────────────────────────────────────────────────
# COMMON HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _sign_idx(name: str) -> int:
    """Return 0..11 sign index for sign name; -1 if unknown."""
    if not isinstance(name, str):
        return -1
    n = name.strip().capitalize()
    return SIGNS.index(n) if n in SIGNS else -1


def _norm(name: str) -> str:
    return (name or "").strip().capitalize()


def _planet_house(planets: list, planet_name: str) -> Optional[int]:
    """Find a planet's house from the planets list."""
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _planet_sign(planets: list, planet_name: str) -> Optional[str]:
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            return p.get("sign")
    return None


def _planet_lon(planets: list, planet_name: str) -> Optional[float]:
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            for k in ("longitude", "lon", "fullDegree", "absoluteDegree"):
                v = p.get(k)
                if isinstance(v, (int, float)):
                    return float(v) % 360.0
    return None


def _is_retrograde(planets: list, planet_name: str) -> bool:
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            return bool(p.get("retrograde") or p.get("isRetro"))
    return False


def _is_combust(planets: list, planet_name: str, threshold_deg: float = 8.0) -> bool:
    """Combust = within threshold degrees of Sun (sidereal). Sun itself never combust."""
    if planet_name == "Sun":
        return False
    sun_lon = _planet_lon(planets, "Sun")
    p_lon = _planet_lon(planets, planet_name)
    if sun_lon is None or p_lon is None:
        return False
    diff = abs(sun_lon - p_lon)
    if diff > 180:
        diff = 360 - diff
    # Tighter threshold for Mercury (per classical rule), looser for Saturn/Jupiter
    thr = {"Mercury": 12.0, "Venus": 10.0, "Mars": 17.0,
           "Jupiter": 11.0, "Saturn": 15.0, "Moon": 12.0}.get(planet_name, threshold_deg)
    return diff < thr


def _house_lord(intel: dict, house_num: int) -> Optional[str]:
    """Return the lord-planet of a house from intel.house_lords."""
    for h in (intel.get("house_lords") or []):
        if isinstance(h, dict) and h.get("house") == house_num:
            return h.get("lord")
    return None


def _planet_dignity(intel: dict, planet_name: str) -> Optional[str]:
    """Return dignity string for a planet from intel.dignities."""
    for d in (intel.get("dignities") or []):
        if isinstance(d, dict) and d.get("planet") == planet_name:
            return d.get("status") or d.get("dignity")
    return None


def _dignity_pts(dignity: Optional[str]) -> int:
    """Convert dignity string → ±points."""
    if not dignity:
        return 0
    return DIGNITY_PTS.get(dignity.lower().replace("_", "-"), 0)


def _aspect_houses(planet: str, planet_house: int) -> set[int]:
    """Return houses aspected by a planet sitting in `planet_house` (Parashari).
    All planets aspect the 7th. Mars also aspects 4th + 8th. Jupiter aspects
    5th + 9th. Saturn aspects 3rd + 10th. Rahu/Ketu treated like Saturn.
    """
    if not isinstance(planet_house, int) or planet_house < 1 or planet_house > 12:
        return set()
    out = {((planet_house - 1 + 6) % 12) + 1}  # 7th from self
    if planet == "Mars":
        out.add(((planet_house - 1 + 3) % 12) + 1)   # 4th
        out.add(((planet_house - 1 + 7) % 12) + 1)   # 8th
    elif planet == "Jupiter":
        out.add(((planet_house - 1 + 4) % 12) + 1)   # 5th
        out.add(((planet_house - 1 + 8) % 12) + 1)   # 9th
    elif planet in ("Saturn", "Rahu", "Ketu"):
        out.add(((planet_house - 1 + 2) % 12) + 1)   # 3rd
        out.add(((planet_house - 1 + 9) % 12) + 1)   # 10th
    return out


def _planets_aspecting_house(planets: list, target_house: int) -> list[str]:
    """Return list of planet names whose Parashari aspects fall on target_house."""
    out: list[str] = []
    for p in (planets or []):
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        ph = p.get("house")
        if not nm or not isinstance(ph, int):
            continue
        if target_house in _aspect_houses(nm, ph):
            out.append(nm)
    return out


def _dasha_lords(kundli: dict) -> tuple[str, str, str]:
    """Return current (MD, AD, PD) lord names from kundli.currentDasha
    (best-effort across multiple naming conventions used by upstream
    chart providers).

    Recognised key variants:
      MD: mahadasha | maha | MD | md_lord | mahadashaLord
      AD: antardasha | antar | AD | ad_lord | antardashaLord
      PD: pratyantardasha | pratyantar | PD | pd_lord | pratyantarLord

    If `currentDasha` is absent, falls back to `currentPhase.name` which
    typical providers format as `"<MD> – <AD>"` (en-dash separated).
    PD is then derived from kundli.dashas hierarchy if available.
    """
    cd = kundli.get("currentDasha") or {}
    md = (cd.get("mahadasha") or cd.get("maha") or cd.get("MD") or
          cd.get("md_lord") or cd.get("mahadashaLord") or "").strip()
    ad = (cd.get("antardasha") or cd.get("antar") or cd.get("AD") or
          cd.get("ad_lord") or cd.get("antardashaLord") or "").strip()
    pd = (cd.get("pratyantardasha") or cd.get("pratyantar") or
          cd.get("PD") or cd.get("pd_lord") or
          cd.get("pratyantarLord") or "").strip()

    # Fallback 1 — parse currentPhase.name "Rahu – Sun"
    if not md or not ad:
        cp = kundli.get("currentPhase") or {}
        nm = (cp.get("name") or "").strip()
        if nm:
            for sep in ("–", "-", "—", "/", "→"):
                if sep in nm:
                    parts = [p.strip() for p in nm.split(sep) if p.strip()]
                    if len(parts) >= 1 and not md: md = parts[0]
                    if len(parts) >= 2 and not ad: ad = parts[1]
                    if len(parts) >= 3 and not pd: pd = parts[2]
                    break

    # Fallback 2 — derive PD from nested dashas hierarchy at "now"
    if (md and ad) and not pd:
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).date().isoformat()
            for top in (kundli.get("dashas") or []):
                if not isinstance(top, dict): continue
                if top.get("planet") != md: continue
                if not (str(top.get("startDate","")) <= now <= str(top.get("endDate","9999"))):
                    continue
                for sub in (top.get("subDashas") or []):
                    if sub.get("planet") != ad: continue
                    if not (str(sub.get("startDate","")) <= now <= str(sub.get("endDate","9999"))):
                        continue
                    for sub2 in (sub.get("subDashas") or []):
                        if str(sub2.get("startDate","")) <= now <= str(sub2.get("endDate","9999")):
                            pd = (sub2.get("planet") or "").strip()
                            break
                    break
                break
        except Exception:
            pass

    return md, ad, pd


def _planet_significates_houses(planet_name: str, kp_sigs: dict) -> set[int]:
    """Return set of houses a planet signifies per KP significations.

    Accepts BOTH payload shapes:
      A) Legacy flat list:  {planet: [house, house, ...]}
      B) kp_engine.calculate_kp output: {planet: {pl: [...], sl: [...],
         sb_houses: [...], ss_houses: [...]}}  → union of all four lists
         per KP doctrine (planet signifies houses via planet itself, its
         nakshatra-lord, its sub-lord, and sub-sub-lord ownership).
    """
    if not isinstance(kp_sigs, dict):
        return set()
    sigs = kp_sigs.get(planet_name)
    if sigs is None:
        return set()
    out: set[int] = set()
    if isinstance(sigs, (list, set, tuple)):
        for h in sigs:
            if isinstance(h, (int, float)):
                out.add(int(h))
        return out
    if isinstance(sigs, dict):
        for key in ("pl", "sl", "sb_houses", "ss_houses"):
            arr = sigs.get(key) or []
            if isinstance(arr, (list, set, tuple)):
                for h in arr:
                    if isinstance(h, (int, float)):
                        out.add(int(h))
        return out
    return out


# ─────────────────────────────────────────────────────────────────────────────
# KP BUCKET-TUNED CUSP/CSL ASSIST
# Each conditional asks "for THIS question type, which cusps' CSLs matter?"
# Polarity "+" = CSL signifying CAREER_PROMISE houses adds weight (favourable
# answer to bucket question). Polarity "-" = CSL signifying CAREER_DENIAL
# houses adds weight (the negative event being asked about is CONFIRMED).
# ─────────────────────────────────────────────────────────────────────────────
_BUCKET_KP_CUSPS: dict[str, list[tuple[int, str, int, str]]] = {
    "govt_job":            [(10, "karma",            5, "+"),
                            (6,  "service",          4, "+"),
                            (1,  "self-status",      3, "+")],
    "promotion":           [(11, "gains",            5, "+"),
                            (10, "recognition",      5, "+"),
                            (6,  "rivals-defeated",  3, "+")],
    "career_setback":      [(8,  "obstacles",        4, "-"),
                            (12, "loss",             4, "-"),
                            (6,  "active-struggles", 3, "-"),
                            (11, "recovery-gains",   5, "+"),
                            (5,  "creative-relief",  2, "+")],
    "job_change":          [(6,  "new-service",      4, "+"),
                            (10, "career-shift",     4, "+"),
                            (3,  "courage",          2, "+")],
    "career_field_choice": [(10, "primary-field",    5, "+"),
                            (5,  "passion",          3, "+"),
                            (3,  "skills",           2, "+")],
    "resignation":         [(12, "exit",             5, "+"),
                            (1,  "self-departing",   3, "+"),
                            (6,  "current-frictions",3, "-")],
    "transfer":            [(3,  "short-moves",      5, "+"),
                            (12, "place-change",     4, "+"),
                            (10, "posting",          3, "+")],
    "general_career":      [(10, "karma",            4, "+"),
                            (6,  "service",          3, "+"),
                            (11, "gains",            3, "+")],
}


def _kp_bucket_assist(kp: dict, bucket: str) -> dict:
    """Bucket-tuned KP cusp+CSL check. Reads kp['cusps'] and kp['significations']
    (both produced by kp_engine.calculate_kp), looks up the bucket's cusp map
    in _BUCKET_KP_CUSPS, and scores each cusp by what its CSL signifies.

    Polarity rules (asymmetric on purpose):
      "+" cusps (favourable-event question, e.g. govt_job karma cusp 10):
            CSL signifies CAREER_PROMISE → +weight
            CSL signifies CAREER_DENIAL  → -weight
            mixed (signifies BOTH)       → +1 token (small lean)
      "-" cusps (negative-event question, e.g. setback cusp 8 obstacles):
            CSL signifies CAREER_DENIAL  → +weight (event CONFIRMED firing)
            CSL signifies CAREER_PROMISE → -weight (event NOT firing)
            mixed (signifies BOTH)       → 0  (CONSERVATIVE — never confirm
                                              a negative event on weak evidence)

    Returns {score, why, summary, per_cusp}. `per_cusp` contains an entry for
    EVERY cusp checked (even ones that scored 0 because their CSL gave no
    clear signal under polarity rules), so callers like C5_setback_recovery
    can split contributions by polarity. `summary` lists only cusps that
    contributed a non-zero score (cleaner for downstream LLM narration).
    Safe-empty when KP unavailable.
    """
    out: dict = {"score": 0, "why": [], "summary": "KP unavailable", "per_cusp": {}}
    if not isinstance(kp, dict):
        return out
    cusps = kp.get("cusps") or []
    sigs  = kp.get("significations") or {}
    if not cusps:
        return out

    cusp_map = _BUCKET_KP_CUSPS.get(bucket) or _BUCKET_KP_CUSPS["general_career"]
    score = 0
    why: list[str] = []
    bits: list[str] = []
    per_cusp: dict = {}

    for cnum, label, weight, polarity in cusp_map:
        cusp = None
        for c in cusps:
            if not isinstance(c, dict):
                continue
            num = c.get("number") or c.get("cusp") or c.get("house")
            try:
                if int(num) == cnum:
                    cusp = c
                    break
            except (TypeError, ValueError):
                continue
        if not cusp:
            continue
        # KP doctrine: cuspal SUB-LORD ("sb" in kp_engine output) is the
        # deciding planet. Accept legacy keys too for forward-compat.
        csl = (cusp.get("sb")
               or cusp.get("subLord")
               or cusp.get("sub_lord")
               or cusp.get("CSL")
               or cusp.get("subLordName"))
        if not csl or not isinstance(csl, str):
            continue
        sig_houses = _planet_significates_houses(csl, sigs)
        if not sig_houses:
            continue
        favour = sig_houses & CAREER_PROMISE
        deny   = sig_houses & CAREER_DENIAL
        # Per-cusp score is tracked separately so callers (e.g. C5 setback
        # recovery) can split positive-polarity vs negative-polarity cusps
        # cleanly instead of inverting the whole net.
        cusp_score = 0
        if polarity == "+":
            if favour and not deny:
                cusp_score = weight
                why.append(f"KP cusp{cnum}({label}) CSL {csl} signifies {sorted(favour)} — bucket-promise +{weight}")
                bits.append(f"c{cnum}={csl}+{weight}")
            elif deny and not favour:
                cusp_score = -weight
                why.append(f"KP cusp{cnum}({label}) CSL {csl} signifies {sorted(deny)} — bucket-denial -{weight}")
                bits.append(f"c{cnum}={csl}-{weight}")
            elif favour and deny:
                cusp_score = 1
                bits.append(f"c{cnum}={csl}±1")
        else:  # polarity "-": negative event being asked about
            if deny and not favour:
                cusp_score = weight
                why.append(f"KP cusp{cnum}({label}) CSL {csl} signifies {sorted(deny)} — confirms bucket-event +{weight}")
                bits.append(f"c{cnum}={csl}+{weight}")
            elif favour and not deny:
                cusp_score = -weight
                why.append(f"KP cusp{cnum}({label}) CSL {csl} signifies {sorted(favour)} — bucket-event NOT firing -{weight}")
                bits.append(f"c{cnum}={csl}-{weight}")
        score += cusp_score
        per_cusp[cnum] = {"label": label, "polarity": polarity, "weight": weight, "score": cusp_score, "csl": csl}

    out["score"] = score
    out["why"] = why
    out["summary"] = " | ".join(bits) if bits else "KP cusps insufficient signification data"
    out["per_cusp"] = per_cusp
    return out


# ─────────────────────────────────────────────────────────────────────────────
# LAZY HELPER MODULE LOADERS (so import never crashes if a helper is missing)
# ─────────────────────────────────────────────────────────────────────────────
def _maybe_shadbala(kundli: dict, lagna_idx: int) -> dict:
    try:
        from shadbala import compute_shadbala
        return compute_shadbala(kundli.get("planets") or [], lagna_idx) or {}
    except Exception:
        return {}


def _maybe_ashtakavarga(kundli: dict, lagna_idx: int) -> dict:
    try:
        from ashtakavarga import compute_ashtakavarga
        return compute_ashtakavarga(kundli.get("planets") or [], lagna_idx) or {}
    except Exception:
        return {}


def _maybe_bhava_bala(intel: dict, shadbala_d: dict) -> dict:
    try:
        from bhava_bala import compute_bhava_bala
        return compute_bhava_bala(intel, shadbala_d) or {}
    except Exception:
        return {}


def _maybe_jaimini(kundli: dict) -> dict:
    """Compute Arudha + Upapada via jaimini.py."""
    try:
        from jaimini import compute_arudha_padas, compute_upapada
        planets = kundli.get("planets") or []
        asc = kundli.get("ascendant") or {}
        lagna_sign = asc.get("sign") if isinstance(asc, dict) else asc
        ar = compute_arudha_padas(planets, lagna_sign) or {}
        up = compute_upapada(ar, planets) or {}
        return {"arudha": ar, "upapada": up}
    except Exception:
        return {}


def _maybe_karakas(kundli: dict) -> dict:
    """Compute Jaimini Char Karakas (AK/AmK/BK/MK/PK/GK/DK)."""
    try:
        from karakas import compute_karakas
        return compute_karakas(kundli.get("planets") or []) or {}
    except Exception:
        return {}


def _maybe_varga_yogas(kundli: dict, lagna_lon: Optional[float]) -> dict:
    try:
        from varga_yogas import detect_all_varga_yogas
        return detect_all_varga_yogas(kundli.get("planets") or [], lagna_lon) or {}
    except Exception:
        return {}


def _maybe_yogini_dasha(kundli: dict, birth: Optional[dict]) -> dict:
    """Yogini Dasha cross-check via extra_jaimini_dashas."""
    try:
        from extra_jaimini_dashas import compute_sthira_dasha
        asc = kundli.get("ascendant") or {}
        lagna_sign = asc.get("sign") if isinstance(asc, dict) else asc
        dob = (birth or {}).get("dob") or kundli.get("dob")
        return compute_sthira_dasha(lagna_sign, dob) or {}
    except Exception:
        return {}


def _maybe_jupiter_transit(lagna_sign_idx: int, moon_sign_idx: Optional[int]) -> dict:
    """Live Jupiter transit windows for next 3 years over career-trigger signs.
    For career, trigger houses from lagna are 10 (karma), 2 (income), 11 (gains).
    Reuses transit_engine's underlying jupiter_sign_changes via custom mapping.
    """
    try:
        from transit_engine import jupiter_sign_changes
        SIGNS_LOCAL = SIGNS
        start = datetime.utcnow()
        # Career trigger sign-offsets from Lagna and Moon
        target_offsets = {0, 1, 9, 10}  # 1st, 2nd, 10th, 11th (0-indexed: 0, 1, 9, 10)
        targets: dict[int, list[str]] = {}
        for off in target_offsets:
            s_l = (lagna_sign_idx + off) % 12
            targets.setdefault(s_l, []).append(f"L{off + 1}")
            if moon_sign_idx is not None and moon_sign_idx >= 0:
                s_m = (moon_sign_idx + off) % 12
                targets.setdefault(s_m, []).append(f"M{off + 1}")
        segments = jupiter_sign_changes(start, years_ahead=3)
        windows = []
        for seg in segments:
            sidx = seg["sign_idx"]
            if sidx in targets:
                windows.append({
                    "start": seg["start"],
                    "end":   seg["end"],
                    "sign":  SIGNS_LOCAL[sidx],
                    "hits":  sorted(set(targets[sidx])),
                })
        # Find which is currently active
        now_str = start.strftime("%Y-%m-%d")
        active = next((w for w in windows
                       if w["start"] <= now_str <= w["end"]), None)
        return {
            "active_window":      active,
            "all_windows":        windows,
        }
    except Exception:
        return {}


def _maybe_saturn_transit_career(lagna_sign_idx: int) -> dict:
    """Live Saturn position relative to natal 10H. Saturn transit on/aspecting
    10H is the classical "career-change" cycle (occurs every ~7-8 years as
    Saturn transits each sign for ~2.5 years). Returns current Saturn sign,
    which natal house it's transiting, and whether it's aspecting/sitting on
    10H or 10L sign.
    """
    try:
        import swisseph as swe
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        now = datetime.utcnow()
        jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
        pos, _ = swe.calc_ut(jd, swe.SATURN, flags)
        sat_lon = float(pos[0]) % 360.0
        sat_sign_idx = int(sat_lon / 30.0) % 12
        # House from lagna
        sat_house_from_lagna = ((sat_sign_idx - lagna_sign_idx) % 12) + 1
        # 10H sign index
        tenth_sign_idx = (lagna_sign_idx + 9) % 12
        on_tenth = (sat_sign_idx == tenth_sign_idx)
        # Saturn aspects 3rd + 10th from itself
        aspects = {
            ((sat_sign_idx + 6) % 12),   # 7th
            ((sat_sign_idx + 2) % 12),   # 3rd
            ((sat_sign_idx + 9) % 12),   # 10th
        }
        aspecting_tenth = tenth_sign_idx in aspects
        return {
            "saturn_sign":             SIGNS[sat_sign_idx],
            "saturn_house_from_lagna": sat_house_from_lagna,
            "on_tenth":                on_tenth,
            "aspecting_tenth":         aspecting_tenth,
            "as_of":                   now.strftime("%Y-%m-%d"),
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# CORE LAYER FUNCTIONS  (L1 – L18)
# ─────────────────────────────────────────────────────────────────────────────

# ── L1 — 10H + 10L deep dive ─────────────────────────────────────────────────
def _layer_tenth_house(intel: dict, kundli: dict) -> dict:
    """⭐ CORE career layer. Weight: 16.

    Analyses 10H (karma/profession) + its lord (10L):
      - 10L sign + dignity + house placement
      - Planets occupying 10H + their dignities
      - Aspects on 10H
      - Lagna lord and 10L relationship
    """
    score = 0
    why: list[str] = []

    tenth_lord = _house_lord(intel, 10)
    planets = kundli.get("planets") or []

    # 10L dignity
    if tenth_lord:
        dgn = _planet_dignity(intel, tenth_lord)
        pts = _dignity_pts(dgn)
        score += pts
        if dgn:
            why.append(f"10L {tenth_lord} is {dgn} ({pts:+d}) — career strength signature")
        # 10L house placement
        tl_h = _planet_house(planets, tenth_lord)
        if tl_h is not None:
            if tl_h in CAREER_PROMISE:
                score += 4
                why.append(f"10L {tenth_lord} placed in career-promise house {tl_h} (+4)")
            elif tl_h in (8, 12):
                score -= 4
                why.append(f"10L {tenth_lord} placed in dusthana {tl_h} (-4) — career obstacle/loss signal")
            elif tl_h == 6:
                score += 2
                why.append(f"10L {tenth_lord} in 6H (+2) — service/competition strength")

    # Planets occupying 10H
    occupants = [p for p in planets
                 if isinstance(p, dict) and p.get("house") == 10 and p.get("name")]
    for p in occupants:
        nm = p.get("name")
        dgn = _planet_dignity(intel, nm)
        pts = _dignity_pts(dgn)
        if nm in NATURAL_BENEFICS:
            score += 3 + max(0, pts // 2)
            why.append(f"{nm} (benefic) in 10H — supports profession (+{3 + max(0, pts // 2)})")
        elif nm in {"Sun", "Mars", "Saturn"}:
            score += 4
            why.append(f"{nm} in 10H — strong career karma signature (+4) [authority/drive/service]")
        elif nm == "Rahu":
            score += 3
            why.append(f"Rahu in 10H — sudden rise / unconventional career path (+3)")
        elif nm == "Ketu":
            score -= 1
            why.append(f"Ketu in 10H — research/spiritual career, instability in conventional path (-1)")

    # Aspects on 10H
    aspectors = _planets_aspecting_house(planets, 10)
    benefic_aspects = [p for p in aspectors if p in NATURAL_BENEFICS]
    malefic_aspects = [p for p in aspectors if p in {"Saturn", "Mars", "Rahu", "Ketu"}]
    if benefic_aspects:
        score += min(4, len(benefic_aspects) * 2)
        why.append(f"10H aspected by benefic(s) {', '.join(benefic_aspects)} (+{min(4, len(benefic_aspects)*2)})")
    if malefic_aspects:
        # Note: Saturn aspecting 10H from outside can be GOOD for career (Saturn = karma karaka)
        sat_in_aspects = "Saturn" in malefic_aspects
        if sat_in_aspects:
            score += 2
            why.append("Saturn aspects 10H — adds karma-yoga discipline (+2)")
        non_sat_malefic = [p for p in malefic_aspects if p != "Saturn"]
        if non_sat_malefic:
            score -= len(non_sat_malefic) * 2
            why.append(f"10H aspected by malefic(s) {', '.join(non_sat_malefic)} ({-len(non_sat_malefic)*2:+d})")

    return {
        "score": score,
        "why":   why,
        "tenth_lord": tenth_lord,
        "tenth_lord_dignity": _planet_dignity(intel, tenth_lord) if tenth_lord else None,
        "tenth_house_occupants": [o.get("name") for o in occupants],
        "tenth_house_aspectors": aspectors,
    }


# ── L2 — Sun (authority / govt karaka) ───────────────────────────────────────
def _layer_sun_karaka(intel: dict, kundli: dict) -> dict:
    """Weight: 12. Sun = Atmakaraka of authority/govt. Strong Sun → leadership,
    govt-job, autonomous role; Weak Sun → ego/recognition struggles."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    sun_dgn = _planet_dignity(intel, "Sun")
    sun_house = _planet_house(planets, "Sun")
    sun_sign = _planet_sign(planets, "Sun")

    pts = _dignity_pts(sun_dgn)
    score += pts
    if sun_dgn:
        why.append(f"Sun is {sun_dgn} ({pts:+d}) — authority/govt-job karaka")

    # Sun in kendra (1/4/7/10) or trikona (1/5/9) is excellent for career
    if sun_house in {1, 5, 9, 10}:
        score += 4
        why.append(f"Sun in kendra/trikona (h{sun_house}) — career visibility/respect (+4)")
    elif sun_house in {6, 11}:
        score += 2
        why.append(f"Sun in upachaya house {sun_house} — long-term career growth (+2)")
    elif sun_house in {8, 12}:
        score -= 3
        why.append(f"Sun in dusthana {sun_house} — recognition/health challenges (-3)")

    # Sun combust handled in modifier M1; but flag here for narration
    if _is_combust(planets, "Sun"):
        why.append("Sun is itself the centre — never combust (informational only)")

    return {
        "score": score,
        "why": why,
        "sun_dignity": sun_dgn,
        "sun_house": sun_house,
        "sun_sign": sun_sign,
    }


# ── L3 — Saturn (service / karma karaka) ─────────────────────────────────────
def _layer_saturn_karaka(intel: dict, kundli: dict) -> dict:
    """Weight: 12. Saturn = karma karaka, longevity-in-job, service.
    Strong Saturn → stable corporate/govt service; Weak → frequent changes."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    sat_dgn = _planet_dignity(intel, "Saturn")
    sat_house = _planet_house(planets, "Saturn")
    sat_sign = _planet_sign(planets, "Saturn")

    pts = _dignity_pts(sat_dgn)
    score += pts
    if sat_dgn:
        why.append(f"Saturn is {sat_dgn} ({pts:+d}) — service/karma karaka")

    # Saturn in 10H is EXCELLENT (own karma) — but only if not debilitated
    if sat_house == 10 and sat_dgn != "debilitated":
        score += 6
        why.append("Saturn in 10H (own karma house) — exceptional service-career signature (+6)")
    elif sat_house in {3, 6, 11}:
        score += 4
        why.append(f"Saturn in upachaya house {sat_house} — improves over time (+4)")
    elif sat_house in {1, 4}:
        score -= 2
        why.append(f"Saturn in h{sat_house} — Saturn-style restraint on personality/comfort (-2)")
    elif sat_house in {8, 12}:
        score -= 3
        why.append(f"Saturn in dusthana {sat_house} — chronic service struggles (-3)")

    if _is_retrograde(planets, "Saturn"):
        # Retrograde Saturn often gives RESEARCH/TECH/depth careers (mixed)
        score += 1
        why.append("Saturn retrograde — depth/research-orientation in career (+1)")

    return {
        "score": score,
        "why": why,
        "saturn_dignity": sat_dgn,
        "saturn_house": sat_house,
        "saturn_sign": sat_sign,
    }


# ── L4 — Mercury (business / commerce karaka) ────────────────────────────────
def _layer_mercury_karaka(intel: dict, kundli: dict) -> dict:
    """Weight: 10. Mercury = business/commerce/communication karaka.
    Strong Mercury → business, IT, analytics, banking, writing excellence."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    mer_dgn = _planet_dignity(intel, "Mercury")
    mer_house = _planet_house(planets, "Mercury")

    pts = _dignity_pts(mer_dgn)
    score += pts
    if mer_dgn:
        why.append(f"Mercury is {mer_dgn} ({pts:+d}) — business/commerce karaka")

    if mer_house in {1, 2, 3, 5, 7, 9, 10, 11}:
        score += 3
        why.append(f"Mercury in house {mer_house} — commerce/IT/intellectual career strength (+3)")
    elif mer_house in {6, 8, 12}:
        score -= 2
        why.append(f"Mercury in dusthana {mer_house} — communication career obstacles (-2)")

    if _is_combust(planets, "Mercury"):
        # Bhuta-aditya combust Mercury can sometimes give Budha-Aditya yoga
        # but generally weakens commerce
        sun_dgn = _planet_dignity(intel, "Sun")
        if sun_dgn in ("exalted", "own-sign"):
            score += 1
            why.append("Mercury combust + strong Sun → Budha-Aditya yoga (royal + commercial intelligence)(+1)")
        else:
            score -= 2
            why.append("Mercury combust by weak Sun — commerce expressed through ego struggles (-2)")

    if _is_retrograde(planets, "Mercury"):
        score += 1
        why.append("Mercury retrograde — sharp analytical/research depth (+1)")

    return {
        "score": score,
        "why": why,
        "mercury_dignity": mer_dgn,
        "mercury_house": mer_house,
    }


# ── L5 — Mars (technical / drive / competition karaka) ───────────────────────
def _layer_mars_karaka(intel: dict, kundli: dict) -> dict:
    """Weight: 8. Mars = drive/courage/technical/competition karaka.
    Strong Mars → engineering, military, sports, surgery, real-estate."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    mars_dgn = _planet_dignity(intel, "Mars")
    mars_house = _planet_house(planets, "Mars")

    pts = _dignity_pts(mars_dgn)
    score += pts
    if mars_dgn:
        why.append(f"Mars is {mars_dgn} ({pts:+d}) — drive/technical/competition karaka")

    # Mars in 3/6/10/11 is upachaya (excellent for action-careers)
    if mars_house in {3, 6, 10, 11}:
        score += 4
        why.append(f"Mars in upachaya/karma house {mars_house} — action/competition strength (+4)")
    elif mars_house == 1:
        score += 2
        why.append("Mars in Lagna — ruchaka-yoga potential, leadership drive (+2)")
    elif mars_house in {4, 7}:
        score -= 1
        why.append(f"Mars in h{mars_house} — Mangal Dosh territory; relationship/comfort friction (-1)")
    elif mars_house in {8, 12}:
        score -= 2
        why.append(f"Mars in dusthana {mars_house} — drive misdirected (-2)")

    return {
        "score": score,
        "why": why,
        "mars_dignity": mars_dgn,
        "mars_house": mars_house,
    }


# ── L6 — Jupiter (wisdom / expansion karaka) ─────────────────────────────────
def _layer_jupiter_karaka(intel: dict, kundli: dict) -> dict:
    """Weight: 10. Jupiter = wisdom/expansion/Guru-tatva.
    Strong Jupiter → teaching, advisory, judiciary, finance-guru, content."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    jup_dgn = _planet_dignity(intel, "Jupiter")
    jup_house = _planet_house(planets, "Jupiter")

    pts = _dignity_pts(jup_dgn)
    score += pts
    if jup_dgn:
        why.append(f"Jupiter is {jup_dgn} ({pts:+d}) — wisdom/expansion karaka")

    # Jupiter in kendra (1/4/7/10) or trikona (1/5/9) is excellent
    if jup_house in {1, 4, 5, 7, 9, 10}:
        score += 4
        why.append(f"Jupiter in kendra/trikona (h{jup_house}) — career grace/expansion (+4)")
    elif jup_house in {2, 11}:
        score += 3
        why.append(f"Jupiter in dhana house {jup_house} — wealth-creation through wisdom (+3)")
    elif jup_house in {6, 8, 12}:
        score -= 2
        why.append(f"Jupiter in dusthana {jup_house} — wisdom obstructed (-2)")

    # Jupiter aspecting 10H or 10L is excellent
    tenth_lord = _house_lord(intel, 10)
    aspectors_10 = _planets_aspecting_house(planets, 10)
    if "Jupiter" in aspectors_10:
        score += 5
        why.append("Jupiter aspects 10H — Guru drishti on karma-bhava (+5) [career grace signature]")
    if tenth_lord:
        tl_h = _planet_house(planets, tenth_lord)
        if tl_h is not None and "Jupiter" in _planets_aspecting_house(planets, tl_h):
            score += 3
            why.append(f"Jupiter aspects 10L {tenth_lord} — wisdom protects career (+3)")

    return {
        "score": score,
        "why": why,
        "jupiter_dignity": jup_dgn,
        "jupiter_house": jup_house,
    }


# ── L7 — Venus (creative / luxury / arts karaka) ─────────────────────────────
def _layer_venus_karaka(intel: dict, kundli: dict) -> dict:
    """Weight: 5. Venus = arts/fashion/media/luxury/hospitality karaka."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    ven_dgn = _planet_dignity(intel, "Venus")
    ven_house = _planet_house(planets, "Venus")

    pts = _dignity_pts(ven_dgn)
    score += pts
    if ven_dgn:
        why.append(f"Venus is {ven_dgn} ({pts:+d}) — arts/luxury/creative-career karaka")

    # Venus in 4 (own kendra) or 7 (own house) or 1/5/9 strong
    if ven_house in {1, 4, 5, 7, 10}:
        score += 2
        why.append(f"Venus in kendra/trikona (h{ven_house}) — creative-career potential (+2)")
    elif ven_house in {2, 11}:
        score += 2
        why.append(f"Venus in dhana house {ven_house} — luxury-driven income (+2)")

    return {
        "score": score,
        "why": why,
        "venus_dignity": ven_dgn,
        "venus_house": ven_house,
    }


# ── L8 — Moon (public-facing / hospitality / mind-work karaka) ───────────────
def _layer_moon_karaka(intel: dict, kundli: dict) -> dict:
    """Weight: 5. Moon = mind/public/hospitality karaka.
    Strong Moon → people-facing roles, hospitality, healthcare, psychology."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    moon_dgn = _planet_dignity(intel, "Moon")
    moon_house = _planet_house(planets, "Moon")

    pts = _dignity_pts(moon_dgn)
    score += pts
    if moon_dgn:
        why.append(f"Moon is {moon_dgn} ({pts:+d}) — mind/public-facing karaka")

    if moon_house in {1, 4, 5, 7, 9, 10, 11}:
        score += 2
        why.append(f"Moon in supportive house {moon_house} — emotional career-fit (+2)")
    elif moon_house in {6, 8, 12}:
        score -= 2
        why.append(f"Moon in dusthana {moon_house} — emotional career-strain (-2)")

    # Kemadruma yoga check (Moon isolated — no planet in 12th or 2nd from Moon)
    # handled in L31 anti-yoga layer

    return {
        "score": score,
        "why": why,
        "moon_dignity": moon_dgn,
        "moon_house": moon_house,
    }


# ── L9 — 6H + 6L (job / service / competition) ───────────────────────────────
def _layer_sixth_house(intel: dict, kundli: dict) -> dict:
    """Weight: 10. 6H = job/service, daily routine, competition, employees.
    Strong 6H = strong job-market presence; weak 6H = self-employment leaning."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    sixth_lord = _house_lord(intel, 6)
    if sixth_lord:
        dgn = _planet_dignity(intel, sixth_lord)
        pts = _dignity_pts(dgn)
        # 6L paradox: a STRONG 6L often gives WEAKER job-market success
        # because 6 is dusthana. Functional rule: 6L well-placed in upachaya
        # (3/6/10/11) is excellent.
        sl_h = _planet_house(planets, sixth_lord)
        if sl_h in {3, 6, 10, 11}:
            score += 4
            why.append(f"6L {sixth_lord} in upachaya {sl_h} — job/service strength (+4)")
        elif sl_h in {8, 12}:
            score += 3
            why.append(f"6L {sixth_lord} in dusthana {sl_h} — Vipreet Raj Yoga territory (+3)")
        else:
            score += pts
            if dgn:
                why.append(f"6L {sixth_lord} is {dgn} ({pts:+d}) in h{sl_h}")

    # Planets in 6H
    occupants = [p for p in planets if isinstance(p, dict) and p.get("house") == 6 and p.get("name")]
    for p in occupants:
        nm = p.get("name")
        if nm in {"Saturn", "Mars", "Sun"}:
            score += 3
            why.append(f"{nm} in 6H — strong service/competition signature (+3)")
        elif nm == "Mercury":
            score += 2
            why.append("Mercury in 6H — analytical/service-oriented mind (+2)")
        elif nm == "Rahu":
            score += 4
            why.append("Rahu in 6H — Vipreet-Rahu, defeats enemies/competitors (+4)")
        elif nm == "Ketu":
            score += 2
            why.append("Ketu in 6H — niche/research service (+2)")
        elif nm in NATURAL_BENEFICS:
            score -= 1
            why.append(f"{nm} (benefic) in 6H — slightly weakens service competitiveness (-1)")

    return {
        "score": score,
        "why": why,
        "sixth_lord": sixth_lord,
        "sixth_lord_dignity": _planet_dignity(intel, sixth_lord) if sixth_lord else None,
    }


# ── L10 — 2H + 2L (income capacity, family wealth) ───────────────────────────
def _layer_second_house(intel: dict, kundli: dict) -> dict:
    """Weight: 9. 2H = earned income, accumulated wealth, family resources."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    second_lord = _house_lord(intel, 2)
    if second_lord:
        dgn = _planet_dignity(intel, second_lord)
        pts = _dignity_pts(dgn)
        score += pts
        sl_h = _planet_house(planets, second_lord)
        if sl_h in {1, 2, 5, 9, 10, 11}:
            score += 3
            why.append(f"2L {second_lord} in dhana/karma house {sl_h} — strong earning potential (+3)")
        elif sl_h in {6, 8, 12}:
            score -= 3
            why.append(f"2L {second_lord} in dusthana {sl_h} — income drainage (-3)")
        if dgn:
            why.append(f"2L {second_lord} is {dgn} ({pts:+d})")

    # Planets in 2H
    occupants = [p for p in planets if isinstance(p, dict) and p.get("house") == 2 and p.get("name")]
    for p in occupants:
        nm = p.get("name")
        if nm in NATURAL_BENEFICS:
            score += 3
            why.append(f"{nm} (benefic) in 2H — supports income flow (+3)")
        elif nm in {"Sun", "Mars", "Saturn"}:
            score += 1
            why.append(f"{nm} in 2H — disciplined earning style (+1)")
        elif nm == "Rahu":
            score += 2
            why.append("Rahu in 2H — sudden/unconventional income channels (+2)")
        elif nm == "Ketu":
            score -= 1
            why.append("Ketu in 2H — fluctuating savings, detachment from accumulation (-1)")

    return {
        "score": score,
        "why": why,
        "second_lord": second_lord,
        "second_lord_dignity": _planet_dignity(intel, second_lord) if second_lord else None,
    }


# ── L11 — 11H + 11L (gains / promotion / fulfillment / network) ──────────────
def _layer_eleventh_house(intel: dict, kundli: dict) -> dict:
    """Weight: 10. 11H = labha-bhava — gains, promotions, fulfillment of
    desires, network/friend-circle. Strong 11H is the single most important
    indicator for promotion, bonus, and goal-fulfillment."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    eleventh_lord = _house_lord(intel, 11)
    if eleventh_lord:
        dgn = _planet_dignity(intel, eleventh_lord)
        pts = _dignity_pts(dgn)
        score += pts
        el_h = _planet_house(planets, eleventh_lord)
        if el_h in {1, 2, 5, 9, 10, 11}:
            score += 4
            why.append(f"11L {eleventh_lord} in supportive house {el_h} — strong gains/promotion potential (+4)")
        elif el_h in {6, 8, 12}:
            score -= 2
            why.append(f"11L {eleventh_lord} in dusthana {el_h} — gains delayed (-2)")
        if dgn:
            why.append(f"11L {eleventh_lord} is {dgn} ({pts:+d})")

    # Planets in 11H — 11H is upachaya, so most planets enhance gains
    occupants = [p for p in planets if isinstance(p, dict) and p.get("house") == 11 and p.get("name")]
    for p in occupants:
        nm = p.get("name")
        if nm in NATURAL_BENEFICS:
            score += 3
            why.append(f"{nm} (benefic) in 11H — multiple income streams (+3)")
        elif nm in {"Sun", "Mars", "Saturn"}:
            score += 4
            why.append(f"{nm} in 11H (upachaya) — strong gains over time (+4)")
        elif nm == "Rahu":
            score += 5
            why.append("Rahu in 11H — exceptional gain potential, fulfillment of all desires (+5)")
        elif nm == "Ketu":
            score -= 1
            why.append("Ketu in 11H — fluctuating gains, detachment from rewards (-1)")

    return {
        "score": score,
        "why": why,
        "eleventh_lord": eleventh_lord,
        "eleventh_lord_dignity": _planet_dignity(intel, eleventh_lord) if eleventh_lord else None,
    }


# ── L12 — 7H + 7L (business / partnership / public dealing) ──────────────────
def _layer_seventh_house(intel: dict, kundli: dict) -> dict:
    """Weight: 8. 7H = business, public-dealing, partnerships, contracts.
    Strong 7H favours business and partnership ventures."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    seventh_lord = _house_lord(intel, 7)
    if seventh_lord:
        dgn = _planet_dignity(intel, seventh_lord)
        pts = _dignity_pts(dgn)
        score += pts
        sl_h = _planet_house(planets, seventh_lord)
        if sl_h in {1, 2, 5, 7, 10, 11}:
            score += 3
            why.append(f"7L {seventh_lord} in supportive house {sl_h} — partnership/business strength (+3)")
        elif sl_h in {6, 8, 12}:
            score -= 2
            why.append(f"7L {seventh_lord} in dusthana {sl_h} — partnership friction (-2)")
        if dgn:
            why.append(f"7L {seventh_lord} is {dgn} ({pts:+d})")

    # Planets in 7H
    occupants = [p for p in planets if isinstance(p, dict) and p.get("house") == 7 and p.get("name")]
    for p in occupants:
        nm = p.get("name")
        if nm in {"Mercury", "Venus", "Jupiter"}:
            score += 3
            why.append(f"{nm} in 7H — favourable for business / public dealing (+3)")
        elif nm == "Rahu":
            score += 2
            why.append("Rahu in 7H — international/large-scale business potential (+2)")
        elif nm == "Mars":
            score -= 2
            why.append("Mars in 7H — partnership friction (Mangal Dosh territory) (-2)")

    return {
        "score": score,
        "why": why,
        "seventh_lord": seventh_lord,
        "seventh_lord_dignity": _planet_dignity(intel, seventh_lord) if seventh_lord else None,
    }


# ── L13 — 9H + 9L (luck / dharma / foreign / mentor) ─────────────────────────
def _layer_ninth_house(intel: dict, kundli: dict) -> dict:
    """Weight: 7. 9H = bhagya-bhava (luck), dharma alignment, higher ed,
    foreign opportunity, mentor/guru blessings."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    ninth_lord = _house_lord(intel, 9)
    if ninth_lord:
        dgn = _planet_dignity(intel, ninth_lord)
        pts = _dignity_pts(dgn)
        score += pts
        nl_h = _planet_house(planets, ninth_lord)
        if nl_h in {1, 4, 5, 7, 9, 10, 11}:
            score += 3
            why.append(f"9L {ninth_lord} in kendra/trikona/upachaya {nl_h} — strong bhagya/foreign signal (+3)")
        elif nl_h == 12:
            score += 2
            why.append(f"9L {ninth_lord} in 12H — foreign-luck signature (+2)")
        elif nl_h in {6, 8}:
            score -= 2
            why.append(f"9L {ninth_lord} in dusthana {nl_h} — bhagya delayed (-2)")
        if dgn:
            why.append(f"9L {ninth_lord} is {dgn} ({pts:+d})")

    # 9L + 10L conjunction = Dharma-Karmadhipati Yoga (RAJ YOGA)
    # — handled in L28 yoga layer; flag here
    tenth_lord = _house_lord(intel, 10)
    if ninth_lord and tenth_lord and ninth_lord == tenth_lord:
        score += 2
        why.append(f"9L = 10L = {ninth_lord} (same planet rules both) — single karaka holds dharma+karma (+2)")

    return {
        "score": score,
        "why": why,
        "ninth_lord": ninth_lord,
        "ninth_lord_dignity": _planet_dignity(intel, ninth_lord) if ninth_lord else None,
    }


# ── L14 — 5H + 5L (intelligence / speculation / leadership) ──────────────────
def _layer_fifth_house(intel: dict, kundli: dict) -> dict:
    """Weight: 6. 5H = intelligence (purva-punya), speculation, leadership,
    creative/authority capacity."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    fifth_lord = _house_lord(intel, 5)
    if fifth_lord:
        dgn = _planet_dignity(intel, fifth_lord)
        pts = _dignity_pts(dgn)
        score += pts
        fl_h = _planet_house(planets, fifth_lord)
        if fl_h in {1, 5, 9, 10, 11}:
            score += 2
            why.append(f"5L {fifth_lord} in trikona/karma house {fl_h} — leadership/intelligence support (+2)")
        if dgn:
            why.append(f"5L {fifth_lord} is {dgn} ({pts:+d})")

    return {
        "score": score,
        "why": why,
        "fifth_lord": fifth_lord,
        "fifth_lord_dignity": _planet_dignity(intel, fifth_lord) if fifth_lord else None,
    }


# ── L15 — Lagna lord position (self-strength to handle career) ───────────────
def _layer_lagna_lord(intel: dict, kundli: dict) -> dict:
    """Weight: 6. Lagnesh = ability of self to claim/sustain career."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    lagna_lord = _house_lord(intel, 1)
    if lagna_lord:
        dgn = _planet_dignity(intel, lagna_lord)
        pts = _dignity_pts(dgn)
        score += pts
        ll_h = _planet_house(planets, lagna_lord)
        if ll_h in {1, 4, 5, 7, 9, 10, 11}:
            score += 3
            why.append(f"Lagnesh {lagna_lord} in supportive house {ll_h} — strong self-fit for career (+3)")
        elif ll_h in {6, 8, 12}:
            score -= 3
            why.append(f"Lagnesh {lagna_lord} in dusthana {ll_h} — self-undermining tendency (-3)")
        if dgn:
            why.append(f"Lagnesh {lagna_lord} is {dgn} ({pts:+d})")

    return {
        "score": score,
        "why": why,
        "lagna_lord": lagna_lord,
        "lagna_lord_dignity": _planet_dignity(intel, lagna_lord) if lagna_lord else None,
    }


# ── L16 — Amatyakaraka (Jaimini career karaka) ⭐ MANDATORY ──────────────────
def _layer_amatyakaraka(karakas_d: dict, intel: dict, kundli: dict) -> dict:
    """⭐ MANDATORY (CLE rule). Weight: 10.

    Amatyakaraka (AmK) = the planet with 2nd-highest longitude (in degrees-
    within-sign) among the 7 char-karakas. In Jaimini astrology, AmK is THE
    karaka of profession. Its sign, dignity, and house placement reveal the
    soul-level career signature — what kind of work the soul has come to do.
    """
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    amk = (karakas_d or {}).get("AmK")
    if not amk:
        return {"score": 0, "why": ["Amatyakaraka unavailable (need full birth data)"],
                "amatyakaraka": None, "amatyakaraka_persona": None}

    amk_dgn = _planet_dignity(intel, amk)
    amk_house = _planet_house(planets, amk)
    amk_sign = _planet_sign(planets, amk)

    pts = _dignity_pts(amk_dgn)
    score += pts
    if amk_dgn:
        why.append(f"Amatyakaraka {amk} is {amk_dgn} ({pts:+d}) — soul-career karaka")

    # AmK in 10H is exceptional (Amatya-in-Karma = perfect career alignment)
    if amk_house == 10:
        score += 6
        why.append(f"Amatyakaraka {amk} in 10H — perfect karma alignment (+6) [ideal soul-career signature]")
    elif amk_house in {1, 5, 9}:
        score += 4
        why.append(f"Amatyakaraka {amk} in trikona {amk_house} — dharmic-career alignment (+4)")
    elif amk_house in {2, 11}:
        score += 3
        why.append(f"Amatyakaraka {amk} in dhana house {amk_house} — wealth-creating profession (+3)")
    elif amk_house in {6, 8, 12}:
        score -= 3
        why.append(f"Amatyakaraka {amk} in dusthana {amk_house} — career soul-misalignment (-3)")

    # Persona (which kind of profession AmK suggests)
    persona = {
        "Sun":     "Authority / govt-leadership / administration / medicine",
        "Saturn":  "Service-driven / labour / construction / mining / longevity-roles",
        "Mercury": "Business / commerce / IT / writing / analysis / banking",
        "Mars":    "Engineering / military / sports / technical / real-estate",
        "Jupiter": "Teaching / advisory / law / finance-guru / spiritual coaching",
        "Venus":   "Arts / fashion / hospitality / luxury / design / entertainment",
        "Moon":    "Public-facing / hospitality / healthcare / psychology",
        "Rahu":    "Foreign / technology / unconventional / aviation / cinema",
        "Ketu":    "Research / occult / spirituality / niche specialisation",
    }.get(amk, "career-undefined persona")

    return {
        "score": score,
        "why": why,
        "amatyakaraka": amk,
        "amatyakaraka_dignity": amk_dgn,
        "amatyakaraka_house": amk_house,
        "amatyakaraka_sign": amk_sign,
        "amatyakaraka_persona": persona,
    }


# ── L17 — Atmakaraka (soul-karaka) in career houses ──────────────────────────
def _layer_atmakaraka_career(karakas_d: dict, intel: dict, kundli: dict) -> dict:
    """Weight: 6. Atmakaraka in 10H or 2H or 11H or 6H = career is part of
    soul's primary purpose."""
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    ak = (karakas_d or {}).get("AK")
    if not ak:
        return {"score": 0, "why": ["Atmakaraka unavailable"], "atmakaraka": None}

    ak_house = _planet_house(planets, ak)
    if ak_house == 10:
        score += 5
        why.append(f"Atmakaraka {ak} in 10H — career IS soul-purpose (+5)")
    elif ak_house in {2, 11}:
        score += 3
        why.append(f"Atmakaraka {ak} in {ak_house}H — wealth/gain-creation is soul-aligned (+3)")
    elif ak_house == 6:
        score += 3
        why.append(f"Atmakaraka {ak} in 6H — service/competition is soul-purpose (+3)")
    elif ak_house in {7, 1, 9, 5}:
        score += 1
        why.append(f"Atmakaraka {ak} in {ak_house}H — supportive but not direct career signal (+1)")

    return {
        "score": score,
        "why": why,
        "atmakaraka": ak,
        "atmakaraka_house": ak_house,
    }


# ── L18 — D9 Navamsa overlay on 10L + AmK ⭐ MANDATORY (CLE rule) ────────────
def _layer_d9_overlay(kundli: dict, intel: dict, karakas_d: dict) -> dict:
    """⭐ MANDATORY (permanent CLE rule). Weight: 10.

    D9 Navamsa is the soul-promise of the rasi (D1) chart. For career, we
    check:
      - 10L's D9 sign + dignity (does career promise hold up in soul-chart?)
      - AmK's D9 sign + dignity (Jaimini soul-career validation)
      - Vargottama planets (same sign in D1+D9 = locked promise)
    """
    score = 0
    why: list[str] = []

    # Use divisional_charts.compute_d9 + summarize for career
    try:
        from divisional_charts import compute_d9
        planets = kundli.get("planets") or []
        asc = kundli.get("ascendant") or {}
        lagna_lon = None
        if isinstance(asc, dict):
            for k in ("longitude", "lon", "fullDegree"):
                v = asc.get(k)
                if isinstance(v, (int, float)):
                    lagna_lon = float(v)
                    break
        d9 = compute_d9(planets, lagna_lon)
    except Exception:
        d9 = {}

    if not d9:
        return {"score": 0, "why": ["D9 Navamsa unavailable (need planet longitudes)"],
                "d9_summary": "unavailable"}

    tenth_lord = _house_lord(intel, 10)

    # 10L in D9 — what sign + does it survive?
    if tenth_lord and tenth_lord in d9 and isinstance(d9[tenth_lord], dict):
        d9_info = d9[tenth_lord]
        d9_sign_idx = d9_info.get("sign_idx")
        d9_sign = d9_info.get("sign")
        if d9_sign_idx is not None:
            # Check if 10L is in own/exalt sign in D9
            own_signs_idx = {i for i, lord in enumerate(SIGN_LORDS_LIST) if lord == tenth_lord}
            if d9_sign_idx in own_signs_idx:
                score += 4
                why.append(f"D9: 10L {tenth_lord} in own sign {d9_sign} — career promise locked (+4) [Vargottama-like strength]")
            # Vargottama bonus
            if d9_info.get("vargottama"):
                score += 5
                why.append(f"D9: 10L {tenth_lord} is VARGOTTAMA (same sign D1+D9) — exceptional career stability (+5)")

    # AmK in D9
    amk = (karakas_d or {}).get("AmK")
    if amk and amk in d9 and isinstance(d9[amk], dict):
        d9_info = d9[amk]
        d9_sign_idx = d9_info.get("sign_idx")
        if d9_sign_idx is not None:
            own_signs_idx = {i for i, lord in enumerate(SIGN_LORDS_LIST) if lord == amk}
            if d9_sign_idx in own_signs_idx:
                score += 3
                why.append(f"D9: Amatyakaraka {amk} in own sign — soul-career karaka strong in Navamsa (+3)")
            if d9_info.get("vargottama"):
                score += 4
                why.append(f"D9: Amatyakaraka {amk} VARGOTTAMA — soul career-fit locked (+4)")

    # Vargottama planets generally
    vargottama_planets = [p for p, info in d9.items()
                          if isinstance(info, dict) and info.get("vargottama") and not p.startswith("_")]
    if vargottama_planets:
        why.append(f"D9 Vargottama planets: {', '.join(vargottama_planets)} (locked-promise indicators)")

    summary_bits = []
    if tenth_lord and tenth_lord in d9:
        summary_bits.append(f"10L {tenth_lord} → {d9[tenth_lord].get('sign')}")
    if amk and amk in d9:
        summary_bits.append(f"AmK {amk} → {d9[amk].get('sign')}")
    summary = "; ".join(summary_bits) if summary_bits else "D9 partial"

    return {
        "score": score,
        "why": why,
        "d9_summary":          summary,
        "d9_tenth_lord_sign":  d9.get(tenth_lord, {}).get("sign") if tenth_lord else None,
        "d9_amk_sign":         d9.get(amk, {}).get("sign") if amk else None,
        "d9_vargottama":       vargottama_planets,
    }


# ── L19 — D10 Dashamsa overlay ⭐ MANDATORY (career-specific D-chart) ────────
def _layer_d10_overlay(kundli: dict, intel: dict, karakas_d: dict) -> dict:
    """⭐ MANDATORY (CLE permanent rule). Weight: 14.

    D10 Dashamsa is THE divisional chart for career — it shows the actual
    profession, public reputation, and karma fruits. For career analysis,
    D10 is more important than D9 (D9 is generic soul, D10 is profession-
    specific). We check:
      - 10L's D10 sign + dignity (where the D1 promise actually manifests)
      - Sun's D10 sign (authority signature in profession)
      - Saturn's D10 sign (service/longevity in profession)
      - AmK's D10 sign (Jaimini career karaka in career-chart)
      - Vargottama planets in D10 (locked profession promise)
    """
    score = 0
    why: list[str] = []

    try:
        from divisional_charts import compute_d10, summarize_d10_for_career
        planets = kundli.get("planets") or []
        asc = kundli.get("ascendant") or {}
        lagna_lon = None
        if isinstance(asc, dict):
            for k in ("longitude", "lon", "fullDegree"):
                v = asc.get(k)
                if isinstance(v, (int, float)):
                    lagna_lon = float(v)
                    break
        d10 = compute_d10(planets, lagna_lon)
        d10_summary = summarize_d10_for_career(d10, intel) if d10 else {}
    except Exception:
        d10 = {}
        d10_summary = {}

    if not d10:
        return {"score": 0, "why": ["D10 Dashamsa unavailable (need planet longitudes)"],
                "d10_summary": "unavailable"}

    tenth_lord = _house_lord(intel, 10)

    # 10L in D10 — strongest career signal
    if tenth_lord and tenth_lord in d10 and isinstance(d10[tenth_lord], dict):
        d10_info = d10[tenth_lord]
        d10_sign_idx = d10_info.get("sign_idx")
        d10_sign = d10_info.get("sign")
        if d10_sign_idx is not None:
            own_signs_idx = {i for i, lord in enumerate(SIGN_LORDS_LIST) if lord == tenth_lord}
            if d10_sign_idx in own_signs_idx:
                score += 6
                why.append(f"D10: 10L {tenth_lord} in own sign {d10_sign} — career promise CONFIRMED in profession-chart (+6)")
            if d10_info.get("vargottama"):
                score += 7
                why.append(f"D10: 10L {tenth_lord} VARGOTTAMA — exceptional career stability + recognition (+7)")
            # Strength flag from summary
            tl_strength = d10_summary.get("10L_d10_strength")
            if tl_strength == "strong":
                score += 4
                why.append(f"D10: 10L {tenth_lord} strong placement — profession-chart supports career (+4)")
            elif tl_strength == "weak":
                score -= 3
                why.append(f"D10: 10L {tenth_lord} weak placement — profession-chart shows weakness (-3)")

    # Sun in D10 — authority/recognition signature
    if "Sun" in d10 and isinstance(d10["Sun"], dict):
        sun_d10_sign = d10["Sun"].get("sign")
        sun_d10_str = d10_summary.get("sun_d10_strength")
        if sun_d10_str == "strong":
            score += 3
            why.append(f"D10: Sun strong in {sun_d10_sign} — authority/recognition in profession (+3)")
        elif sun_d10_str == "weak":
            score -= 2
            why.append(f"D10: Sun weak in {sun_d10_sign} — recognition struggles (-2)")
        if d10["Sun"].get("vargottama"):
            score += 3
            why.append(f"D10: Sun VARGOTTAMA — locked authority signature (+3)")

    # Saturn in D10 — service/longevity signature
    if "Saturn" in d10 and isinstance(d10["Saturn"], dict):
        sat_d10_sign = d10["Saturn"].get("sign")
        sat_d10_str = d10_summary.get("saturn_d10_strength")
        if sat_d10_str == "strong":
            score += 3
            why.append(f"D10: Saturn strong in {sat_d10_sign} — service longevity locked (+3)")
        elif sat_d10_str == "weak":
            score -= 1
            why.append(f"D10: Saturn weak in {sat_d10_sign} — service stability fluctuating (-1)")
        if d10["Saturn"].get("vargottama"):
            score += 3
            why.append(f"D10: Saturn VARGOTTAMA — service-karma anchor locked (+3)")

    # AmK in D10 — soul-career karaka in career chart
    amk = (karakas_d or {}).get("AmK")
    if amk and amk in d10 and isinstance(d10[amk], dict):
        d10_info = d10[amk]
        d10_sign_idx = d10_info.get("sign_idx")
        if d10_sign_idx is not None:
            own_signs_idx = {i for i, lord in enumerate(SIGN_LORDS_LIST) if lord == amk}
            if d10_sign_idx in own_signs_idx:
                score += 4
                why.append(f"D10: Amatyakaraka {amk} in own sign — soul-career signature CONFIRMED in profession-chart (+4)")
            if d10_info.get("vargottama"):
                score += 5
                why.append(f"D10: Amatyakaraka {amk} VARGOTTAMA — soul-career & profession aligned at deepest level (+5)")

    # Vargottama planets in D10
    vargottama_d10 = d10_summary.get("vargottama") or []
    if vargottama_d10:
        why.append(f"D10 Vargottama planets: {', '.join(vargottama_d10)} (locked-profession indicators)")

    summary_bits = []
    if "10L" in d10_summary:
        summary_bits.append(f"10L {d10_summary['10L']} → {d10_summary.get('10L_d10_sign')} ({d10_summary.get('10L_d10_strength')})")
    if "sun_d10_sign" in d10_summary:
        summary_bits.append(f"Sun → {d10_summary['sun_d10_sign']} ({d10_summary.get('sun_d10_strength')})")
    if "saturn_d10_sign" in d10_summary:
        summary_bits.append(f"Saturn → {d10_summary['saturn_d10_sign']} ({d10_summary.get('saturn_d10_strength')})")
    summary = "; ".join(summary_bits) if summary_bits else "D10 partial"

    return {
        "score": score,
        "why": why,
        "d10_summary": summary,
        "d10_tenth_lord_sign":  d10_summary.get("10L_d10_sign"),
        "d10_sun_sign":         d10_summary.get("sun_d10_sign"),
        "d10_saturn_sign":      d10_summary.get("saturn_d10_sign"),
        "d10_vargottama":       vargottama_d10,
    }


# ── L20 — D24 Chaturvimshamsa (education + skill foundation) ─────────────────
def _layer_d24_overlay(kundli: dict, intel: dict) -> dict:
    """Weight: 4. D24 = education-chart; the skill/credential layer feeding
    profession. We check Mercury and Jupiter (vidya karakas) in D24 for own/
    vargottama positions which strengthen credential-driven careers."""
    score = 0
    why: list[str] = []

    try:
        from divisional_charts import compute_d16
        # D24 is sometimes computed in same module as compute_d24
        try:
            from divisional_charts import compute_d24  # type: ignore
            planets = kundli.get("planets") or []
            asc = kundli.get("ascendant") or {}
            lagna_lon = None
            if isinstance(asc, dict):
                for k in ("longitude", "lon", "fullDegree"):
                    v = asc.get(k)
                    if isinstance(v, (int, float)):
                        lagna_lon = float(v)
                        break
            d24 = compute_d24(planets, lagna_lon)
        except ImportError:
            d24 = {}
    except Exception:
        d24 = {}

    if not d24:
        return {"score": 0, "why": ["D24 unavailable — using D16 / Mercury-Jupiter in D1 as proxy"],
                "d24_summary": "unavailable"}

    for p in ("Mercury", "Jupiter"):
        if p in d24 and isinstance(d24[p], dict):
            d24_info = d24[p]
            d24_sign_idx = d24_info.get("sign_idx")
            if d24_sign_idx is not None:
                own_signs_idx = {i for i, lord in enumerate(SIGN_LORDS_LIST) if lord == p}
                if d24_sign_idx in own_signs_idx:
                    score += 2
                    why.append(f"D24: {p} in own sign — credential/skill foundation (+2)")
                if d24_info.get("vargottama"):
                    score += 2
                    why.append(f"D24: {p} VARGOTTAMA — locked credential strength (+2)")

    return {
        "score": score,
        "why": why,
        "d24_summary": "D24 mercury+jupiter checked",
    }


# ── L22 — KP cuspal sub-lord 6/10/2/11 ⭐ MANDATORY (CLE rule) ───────────────
def _layer_kp_csl_career(kp: dict) -> dict:
    """⭐ MANDATORY (permanent CLE rule). Weight: 12.

    KP cuspal sub-lord (CSL) of cusps 6, 10, 2, 11 must signify CAREER_PROMISE
    houses {2, 6, 10, 11} for career affairs to manifest.

    This is the precision layer — it's the difference between "natal promise
    exists" and "promise actually fires for THIS person at THIS time".
    """
    score = 0
    why: list[str] = []

    if not isinstance(kp, dict):
        return {"score": 0, "why": ["KP data unavailable"], "csl_summary": "unavailable"}

    cusps = kp.get("cusps") or []
    sigs = kp.get("significations") or {}
    if not cusps:
        return {"score": 0, "why": ["KP cusps unavailable"], "csl_summary": "unavailable"}

    # Cusp 6 (job/service), 10 (karma), 2 (income), 11 (gains)
    summary_bits: list[str] = []
    for cusp_num, label, weight in [(10, "karma/profession", 5),
                                     (6, "job/service", 4),
                                     (2, "income", 3),
                                     (11, "gains/promotion", 4)]:
        cusp = next((c for c in cusps if c.get("number") == cusp_num
                     or c.get("cusp") == cusp_num
                     or c.get("house") == cusp_num), None)
        if not cusp:
            continue
        csl = cusp.get("sb") or cusp.get("subLord") or cusp.get("sub_lord") or cusp.get("CSL") or cusp.get("subLordName")
        if not csl:
            continue
        sig_houses = _planet_significates_houses(csl, sigs)
        favours = sig_houses & CAREER_PROMISE
        denies = sig_houses & CAREER_DENIAL
        if favours and not denies:
            score += weight
            summary_bits.append(f"cusp{cusp_num}({label}) CSL {csl} → houses {sorted(favours)} (FAVOURABLE +{weight})")
            why.append(f"KP CSL of cusp{cusp_num}({label}): {csl} signifies {sorted(favours)} — career-promise CONFIRMED (+{weight})")
        elif denies and not favours:
            score -= weight
            summary_bits.append(f"cusp{cusp_num}({label}) CSL {csl} → houses {sorted(denies)} (DENIES -{weight})")
            why.append(f"KP CSL of cusp{cusp_num}({label}): {csl} signifies {sorted(denies)} — career-DENIAL signal ({-weight:+d})")
        elif favours and denies:
            score += weight // 2
            summary_bits.append(f"cusp{cusp_num} CSL {csl} → mixed (favour={sorted(favours)}, deny={sorted(denies)})")
            why.append(f"KP CSL of cusp{cusp_num}: {csl} mixed signification — partial promise (+{weight // 2})")

    csl_summary = " | ".join(summary_bits) if summary_bits else "KP CSL: data partial"

    return {
        "score": score,
        "why": why,
        "csl_summary": csl_summary,
    }


# ── L23 — KP Ruling Planets (prashna/horary cross-check) ─────────────────────
def _layer_kp_ruling_planets(kp: dict) -> dict:
    """Weight: 5. KP Ruling Planets at the moment of judgement (today's date)
    cross-validate the natal CSL findings. RPs that signify CAREER_PROMISE
    houses add confirmatory weight; RPs signifying DENIAL subtract."""
    score = 0
    why: list[str] = []

    if not isinstance(kp, dict):
        return {"score": 0, "why": ["KP data unavailable"], "rp_summary": "unavailable"}

    sigs = kp.get("significations") or {}
    rps = kp.get("rulingPlanets") or kp.get("ruling_planets") or []
    if not rps:
        return {"score": 0, "why": ["KP Ruling Planets not in payload"], "rp_summary": "unavailable"}

    rp_planets = []
    for rp in rps:
        if isinstance(rp, str):
            rp_planets.append(rp)
        elif isinstance(rp, dict):
            nm = rp.get("planet") or rp.get("name")
            if nm:
                rp_planets.append(nm)

    favourable_rps = []
    denying_rps = []
    for p in rp_planets:
        sig_houses = _planet_significates_houses(p, sigs)
        if sig_houses & CAREER_PROMISE:
            favourable_rps.append(p)
        if sig_houses & CAREER_DENIAL:
            denying_rps.append(p)

    if favourable_rps:
        pts = min(5, len(favourable_rps) * 2)
        score += pts
        why.append(f"KP Ruling Planets {favourable_rps} signify career-promise houses (+{pts})")
    if denying_rps:
        pts = min(3, len(denying_rps))
        score -= pts
        why.append(f"KP Ruling Planets {denying_rps} signify denial houses (-{pts})")

    return {
        "score": score,
        "why": why,
        "rp_summary": f"RPs: {rp_planets}; favour={favourable_rps}; deny={denying_rps}",
    }


# ── L24 — Ashtakavarga (10H BAV + Sun/Saturn BAV) ────────────────────────────
def _layer_ashtakavarga_career(av: dict) -> dict:
    """Weight: 6. Ashtakavarga BAV gives a 0-8 strength score per planet per
    sign. For career we look at:
      - 10H total bindus (>30 strong, <22 weak)
      - Sun's BAV bindus in 10H
      - Saturn's BAV bindus in 10H
    """
    score = 0
    why: list[str] = []

    if not av:
        return {"score": 0, "why": ["Ashtakavarga unavailable"], "av_summary": "unavailable"}

    sav = av.get("sav") or av.get("SAV")
    bav = av.get("bav") or av.get("BAV")

    # Note: SAV is keyed by sign-index (0..11) representing 1H..12H from lagna
    # We need 10H sign-index from lagna sign
    lagna_sign_idx = av.get("lagna_sign_idx")
    tenth_sign_idx = None
    if isinstance(lagna_sign_idx, int):
        tenth_sign_idx = (lagna_sign_idx + 9) % 12

    summary_bits = []
    if isinstance(sav, list) and tenth_sign_idx is not None and tenth_sign_idx < len(sav):
        tenth_sav = sav[tenth_sign_idx]
        summary_bits.append(f"10H SAV={tenth_sav}")
        if tenth_sav >= 30:
            score += 4
            why.append(f"10H SAV bindus = {tenth_sav} (≥30) — STRONG career house (+4)")
        elif tenth_sav <= 22:
            score -= 3
            why.append(f"10H SAV bindus = {tenth_sav} (≤22) — WEAK career house (-3)")
        else:
            why.append(f"10H SAV bindus = {tenth_sav} (moderate)")

    if isinstance(bav, dict) and tenth_sign_idx is not None:
        for planet in ("Sun", "Saturn", "Mercury"):
            bav_list = bav.get(planet)
            if isinstance(bav_list, list) and tenth_sign_idx < len(bav_list):
                bav_pts = bav_list[tenth_sign_idx]
                summary_bits.append(f"{planet} BAV in 10H = {bav_pts}")
                if bav_pts >= 5:
                    score += 1
                    why.append(f"{planet} contributes {bav_pts} bindus to 10H — supportive (+1)")
                elif bav_pts <= 1:
                    score -= 1
                    why.append(f"{planet} contributes only {bav_pts} bindu to 10H — weak (-1)")

    return {
        "score": score,
        "why": why,
        "av_summary": "; ".join(summary_bits) if summary_bits else "Ashtakavarga partial",
    }


# ── L25 — Shadbala (10L, Sun, Saturn, Mercury, Jupiter) ──────────────────────
def _layer_shadbala_career(sb: dict, intel: dict) -> dict:
    """Weight: 6. Shadbala gives total 6-fold strength of each planet (in
    rupas / shashtiamshas). For career we check 10L and the 5 career karakas
    (Sun, Saturn, Mercury, Mars, Jupiter)."""
    score = 0
    why: list[str] = []

    if not sb:
        return {"score": 0, "why": ["Shadbala unavailable"], "sb_summary": "unavailable"}

    totals = sb.get("totals") or sb.get("total") or sb
    minimums = sb.get("minimums") or {}

    tenth_lord = _house_lord(intel, 10)
    summary_bits = []

    # 10L shadbala
    if tenth_lord and tenth_lord in totals:
        tl_total = totals.get(tenth_lord)
        tl_min = minimums.get(tenth_lord, 0)
        if isinstance(tl_total, (int, float)):
            ratio = tl_total / max(tl_min, 1) if tl_min else 0
            summary_bits.append(f"10L {tenth_lord} shadbala = {tl_total:.1f}")
            if ratio >= 1.2:
                score += 3
                why.append(f"Shadbala: 10L {tenth_lord} = {tl_total:.1f} (≥120% of minimum) — strong (+3)")
            elif ratio < 1.0 and tl_min:
                score -= 2
                why.append(f"Shadbala: 10L {tenth_lord} = {tl_total:.1f} (below minimum {tl_min:.1f}) — weak (-2)")

    # Career karakas
    for karaka in ("Sun", "Saturn", "Mercury", "Jupiter"):
        if karaka in totals:
            kt = totals[karaka]
            km = minimums.get(karaka, 0)
            if isinstance(kt, (int, float)):
                summary_bits.append(f"{karaka}={kt:.1f}")
                ratio = kt / max(km, 1) if km else 0
                if ratio >= 1.3:
                    score += 1
                    why.append(f"Shadbala: {karaka} = {kt:.1f} (well above minimum) — supportive (+1)")
                elif ratio < 1.0 and km:
                    score -= 1
                    why.append(f"Shadbala: {karaka} = {kt:.1f} (below minimum) — weakens its karaka domain (-1)")

    return {
        "score": score,
        "why": why,
        "sb_summary": "; ".join(summary_bits) if summary_bits else "Shadbala partial",
    }


# ── L26 — Bhava Bala on 10/6/2/11 ────────────────────────────────────────────
def _layer_bhava_bala_career(bb: dict) -> dict:
    """Weight: 5. Bhava Bala = combined house strength (occupant + lord +
    aspect contributions). For career, 10H and 6H matter most; 2H and 11H
    secondary."""
    score = 0
    why: list[str] = []

    if not bb:
        return {"score": 0, "why": ["Bhava Bala unavailable"], "bb_summary": "unavailable"}

    house_strengths = bb.get("strengths") or bb.get("houses") or {}
    if not isinstance(house_strengths, dict):
        return {"score": 0, "why": ["Bhava Bala data malformed"], "bb_summary": "malformed"}

    summary_bits = []
    for h, weight in [(10, 3), (6, 2), (11, 2), (2, 2)]:
        s = house_strengths.get(h) or house_strengths.get(str(h))
        if isinstance(s, (int, float)):
            summary_bits.append(f"H{h}={s:.1f}")
            if s >= 8.0:
                score += weight
                why.append(f"Bhava Bala: H{h} strength {s:.1f} (strong) (+{weight})")
            elif s <= 4.0:
                score -= weight - 1
                why.append(f"Bhava Bala: H{h} strength {s:.1f} (weak) ({-(weight-1):+d})")

    return {
        "score": score,
        "why": why,
        "bb_summary": "; ".join(summary_bits) if summary_bits else "Bhava Bala partial",
    }


# ── L27 — Char karakas full set (Jaimini soul-roles) ─────────────────────────
def _layer_char_karakas_career(karakas_d: dict, intel: dict, kundli: dict) -> dict:
    """Weight: 4. Cross-reference the full 7-karaka set for career context.
    Particular focus: PK (putra-karaka, 5th-house leader-karaka) and BK
    (bhratru-karaka, sibling/colleague karaka)."""
    score = 0
    why: list[str] = []

    if not karakas_d:
        return {"score": 0, "why": ["Char karakas unavailable"], "karaka_set": {}}

    pk = karakas_d.get("PK")  # Putra karaka
    bk = karakas_d.get("BK")  # Bhratru karaka

    planets = kundli.get("planets") or []

    if pk:
        pk_h = _planet_house(planets, pk)
        if pk_h in {5, 10, 11}:
            score += 2
            why.append(f"Putra-karaka {pk} in {pk_h}H — leadership/intelligence supports career (+2)")

    if bk:
        bk_h = _planet_house(planets, bk)
        if bk_h in {3, 6, 10, 11}:
            score += 2
            why.append(f"Bhratru-karaka {bk} in {bk_h}H — colleague/team support strong (+2)")
        elif bk_h in {8, 12}:
            score -= 1
            why.append(f"Bhratru-karaka {bk} in {bk_h}H — colleague friction risk (-1)")

    karaka_set = {role: karakas_d.get(role) for role in ("AK","AmK","BK","MK","PK","GK","DK") if karakas_d.get(role)}

    return {
        "score": score,
        "why": why,
        "karaka_set": karaka_set,
    }


# ── L28 — Raja Yogas (Kendra-Trikona, 9L+10L) ⭐ key for career ──────────────
def _layer_raj_yogas(yogas_d: dict, intel: dict, kundli: dict) -> dict:
    """Weight: 9. Raja Yogas = power/authority/recognition combinations.
    Critical for career advancement, govt-job, leadership roles.

    We use detect_all_varga_yogas() result for D1 + manual checks for:
      - 9L+10L conjunction or mutual aspect (Dharma-Karmadhipati Yoga)
      - Lagnesh + 9L conjunction (Bhagyesh-Lagnesh combo)
      - 10L in trikona OR trikona-lord in 10H
    """
    score = 0
    why: list[str] = []

    raj_yogas = []
    if isinstance(yogas_d, dict):
        d1_yogas = yogas_d.get("D1") or yogas_d.get("d1") or {}
        if isinstance(d1_yogas, dict):
            raj_yogas = d1_yogas.get("raj_yogas") or []

    for ry in raj_yogas[:5]:
        if isinstance(ry, dict):
            label = ry.get("name") or ry.get("type") or "Raj Yoga"
            score += 3
            why.append(f"⭐ {label} detected — career power/recognition signature (+3)")

    # Manual: 9L + 10L combination
    nl = _house_lord(intel, 9)
    tl = _house_lord(intel, 10)
    planets = kundli.get("planets") or []
    if nl and tl and nl != tl:
        nl_h = _planet_house(planets, nl)
        tl_h = _planet_house(planets, tl)
        if nl_h is not None and tl_h is not None and nl_h == tl_h:
            score += 5
            why.append(f"⭐ Dharma-Karmadhipati Yoga: 9L {nl} + 10L {tl} conjunct in {nl_h}H — exceptional career-luck combo (+5)")
        # Mutual aspect (7th from each)
        elif nl_h is not None and tl_h is not None and abs(nl_h - tl_h) == 6:
            score += 3
            why.append(f"⭐ 9L {nl} & 10L {tl} mutual 7th aspect — Dharma-Karma soft yoga (+3)")

    # Trikona-lord in 10H
    for trikona in (1, 5, 9):
        tklord = _house_lord(intel, trikona)
        if tklord:
            tk_h = _planet_house(planets, tklord)
            if tk_h == 10:
                score += 2
                why.append(f"Trikona-lord {tklord} (of {trikona}H) in 10H — Raj-yoga bonus (+2)")

    return {
        "score": score,
        "why": why,
        "raj_yoga_count": len(raj_yogas),
    }


# ── L29 — Dhana Yogas (2L+11L, 5L+11L, etc.) ─────────────────────────────────
def _layer_dhana_yogas(intel: dict, kundli: dict) -> dict:
    """Weight: 8. Dhana Yogas = wealth-creation combinations through career.
    Core combos:
      - 2L + 11L conjunction or mutual aspect (income+gains lord combo)
      - 5L + 11L combination (purva-punya driving gains)
      - 9L + 2L combination (luck driving income)
    """
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    sl  = _house_lord(intel, 2)
    fl  = _house_lord(intel, 5)
    nl  = _house_lord(intel, 9)
    el  = _house_lord(intel, 11)

    pairs = [
        (sl, el, "2L+11L"),
        (fl, el, "5L+11L"),
        (nl, sl, "9L+2L"),
        (sl, _house_lord(intel, 1), "Lagnesh+2L"),
    ]

    seen = set()
    for a, b, label in pairs:
        if not a or not b or a == b:
            continue
        key = tuple(sorted([a, b]))
        if key in seen:
            continue
        seen.add(key)
        a_h = _planet_house(planets, a)
        b_h = _planet_house(planets, b)
        if a_h is not None and b_h is not None:
            if a_h == b_h:
                score += 3
                why.append(f"Dhana Yoga: {label} ({a}+{b}) conjunct in {a_h}H — wealth-creation combo (+3)")
            elif abs(a_h - b_h) == 6:
                score += 2
                why.append(f"Dhana Yoga: {label} ({a}↔{b}) 7th-aspect — soft wealth combo (+2)")

    # Lakshmi Yoga: 9L in own/exalted in kendra/trikona + Venus strong
    if nl:
        nl_h = _planet_house(planets, nl)
        nl_dgn = _planet_dignity(intel, nl)
        if nl_h in {1, 4, 5, 7, 9, 10} and nl_dgn in ("own-sign", "exalted", "moolatrikona"):
            ven_dgn = _planet_dignity(intel, "Venus")
            if ven_dgn in ("own-sign", "exalted", "moolatrikona", "friend-sign"):
                score += 4
                why.append(f"⭐ Lakshmi Yoga: 9L {nl} ({nl_dgn}) in kendra + Venus {ven_dgn} — wealth-grace yoga (+4)")

    return {
        "score": score,
        "why": why,
    }


# ── L30 — Pancha-Mahapurusha + career-yogas (Bhadra/Hamsa/Ruchaka/etc) ──────
def _layer_mahapurusha_yogas(yogas_d: dict, intel: dict, kundli: dict) -> dict:
    """Weight: 9. Pancha-Mahapurusha yogas = single planet in own/exalt sign
    in a kendra house. Each gives a distinct career-personality boost:
      - Ruchaka (Mars)   → military/police/sports/engineering excellence
      - Bhadra (Mercury) → business/IT/commerce excellence
      - Hamsa (Jupiter)  → teaching/advisory/judiciary excellence
      - Malavya (Venus)  → arts/luxury/entertainment excellence
      - Sasha (Saturn)   → service/administration/govt-job excellence
    """
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    mahapurusha = []
    if isinstance(yogas_d, dict):
        d1_yogas = yogas_d.get("D1") or yogas_d.get("d1") or {}
        if isinstance(d1_yogas, dict):
            mahapurusha = d1_yogas.get("mahapurusha") or d1_yogas.get("pancha_mahapurusha") or []

    # Iterate detected yogas
    for mp in mahapurusha[:5]:
        if isinstance(mp, dict):
            label = mp.get("name") or mp.get("yoga") or "Mahapurusha"
            planet = mp.get("planet")
            score += 5
            why.append(f"⭐ {label} ({planet}) — Pancha-Mahapurusha career-personality activated (+5)")

    # Backup detection (in case yogas_d empty) — manual Sasha (Saturn) since
    # this is the most career-relevant
    if not mahapurusha:
        sat_dgn = _planet_dignity(intel, "Saturn")
        sat_h = _planet_house(planets, "Saturn")
        if sat_dgn in ("own-sign", "exalted") and sat_h in {1, 4, 7, 10}:
            score += 5
            why.append(f"⭐ SASHA YOGA (Saturn {sat_dgn} in kendra h{sat_h}) — service/administration excellence (+5)")
        # Manual Bhadra (Mercury)
        mer_dgn = _planet_dignity(intel, "Mercury")
        mer_h = _planet_house(planets, "Mercury")
        if mer_dgn in ("own-sign", "exalted") and mer_h in {1, 4, 7, 10}:
            score += 5
            why.append(f"⭐ BHADRA YOGA (Mercury {mer_dgn} in kendra h{mer_h}) — business/commerce excellence (+5)")
        # Manual Hamsa (Jupiter)
        jup_dgn = _planet_dignity(intel, "Jupiter")
        jup_h = _planet_house(planets, "Jupiter")
        if jup_dgn in ("own-sign", "exalted") and jup_h in {1, 4, 7, 10}:
            score += 5
            why.append(f"⭐ HAMSA YOGA (Jupiter {jup_dgn} in kendra h{jup_h}) — wisdom/advisory excellence (+5)")

    # Gajakesari (Jupiter-Moon kendra relationship)
    jup_h = _planet_house(planets, "Jupiter")
    moon_h = _planet_house(planets, "Moon")
    if jup_h is not None and moon_h is not None:
        diff = abs(jup_h - moon_h)
        if diff in (0, 3, 6, 9):
            score += 3
            why.append(f"Gajakesari Yoga (Jupiter h{jup_h} ↔ Moon h{moon_h} — kendra) — fame/dignity (+3)")

    # Vipreet Raj Yoga
    vipreet = []
    if isinstance(yogas_d, dict):
        d1_yogas = yogas_d.get("D1") or yogas_d.get("d1") or {}
        if isinstance(d1_yogas, dict):
            vipreet = d1_yogas.get("vipreet_raj_yogas") or d1_yogas.get("vipreet") or []
    for vr in vipreet[:3]:
        if isinstance(vr, dict):
            label = vr.get("name") or "Vipreet Raj Yoga"
            score += 3
            why.append(f"⭐ {label} — adversity-converted-to-success career signature (+3)")

    return {
        "score": score,
        "why": why,
        "mahapurusha_count": len(mahapurusha),
    }


# ── L31 — Anti-yogas: Daridra / Kemadruma / Nicha-bhanga ─────────────────────
def _layer_anti_yogas(intel: dict, kundli: dict) -> dict:
    """Weight: 5 (±). Wealth-blocking and career-blocking yogas:
      - Daridra Yoga: 11L in 6/8/12 (gains lord debilitated)
      - Kemadruma Yoga: Moon isolated (no planet in 2nd or 12th from Moon)
      - Nicha-bhanga: debilitated planet's debility cancelled — converts to bonus
    """
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    # Daridra
    el = _house_lord(intel, 11)
    if el:
        el_h = _planet_house(planets, el)
        el_dgn = _planet_dignity(intel, el)
        if el_h in {6, 8, 12} or el_dgn == "debilitated":
            score -= 4
            why.append(f"⚠ Daridra Yoga signal: 11L {el} weak ({el_dgn or 'house'} h{el_h}) — gains-blocking (-4)")

    # Kemadruma — Moon isolated
    moon_h = _planet_house(planets, "Moon")
    if moon_h is not None:
        prev_h = ((moon_h - 2) % 12) + 1   # 12th from Moon
        next_h = (moon_h % 12) + 1          # 2nd from Moon
        # Sun excluded from supporting Moon
        supporting_planets = [p for p in planets if isinstance(p, dict)
                              and p.get("name") not in ("Moon", "Sun", "Rahu", "Ketu")
                              and p.get("house") in (prev_h, next_h)]
        if not supporting_planets:
            score -= 3
            why.append(f"⚠ Kemadruma Yoga: Moon (h{moon_h}) isolated — emotional career-isolation (-3)")
        else:
            why.append(f"Kemadruma cancelled — Moon supported by {[p.get('name') for p in supporting_planets]}")

    # Nicha-bhanga (debility cancellation)
    for d in (intel.get("dignities") or []):
        if isinstance(d, dict) and d.get("status") == "debilitated":
            planet = d.get("planet")
            ph = _planet_house(planets, planet)
            psign = _planet_sign(planets, planet)
            sidx = _sign_idx(psign or "")
            if sidx >= 0:
                # Lord of debility sign in kendra from lagna OR from Moon = nicha-bhanga
                deb_sign_lord = SIGN_LORDS_LIST[sidx]
                dsl_h = _planet_house(planets, deb_sign_lord)
                if dsl_h in {1, 4, 7, 10}:
                    score += 3
                    why.append(f"⭐ Nicha-Bhanga: {planet} debility cancelled (sign-lord {deb_sign_lord} in kendra h{dsl_h}) — converts to Raj-yoga (+3)")

    return {
        "score": score,
        "why": why,
    }


# ── L32 — Sade Sati on Moon + Eclipse on 10L ─────────────────────────────────
def _layer_sade_sati_eclipse(intel: dict, kundli: dict) -> dict:
    """Weight: 5 (±). Sade Sati (Saturn 7.5-yr period over 12-1-2 from Moon)
    is the classic career-stress phase. Also flag eclipse impact on 10L."""
    score = 0
    why: list[str] = []

    sade = intel.get("sade_sati") or kundli.get("sadeSati") or {}
    if isinstance(sade, dict):
        active = sade.get("active") or sade.get("isActive") or False
        phase = sade.get("phase") or sade.get("state") or ""
        if active:
            if str(phase).lower() in ("first", "rising", "ascending"):
                score -= 2
                why.append(f"⚠ Sade Sati FIRST phase active — initial pressure on career (-2)")
            elif str(phase).lower() in ("peak", "second", "second-phase"):
                score -= 4
                why.append(f"⚠ Sade Sati PEAK phase — heavy career stress / restructuring (-4)")
            elif str(phase).lower() in ("setting", "third", "rising-out"):
                score -= 1
                why.append(f"⚠ Sade Sati SETTING phase — easing, but still tail-risk (-1)")
            else:
                score -= 2
                why.append(f"⚠ Sade Sati active — career-pressure window (-2)")

    # Shani Dhaiya (2.5-yr Saturn transit on 4H or 8H from Moon — milder Sade-Sati)
    dhaiya = intel.get("shani_dhaiya") or kundli.get("shaniDhaiya") or {}
    if isinstance(dhaiya, dict) and dhaiya.get("active"):
        score -= 1
        why.append("Shani Dhaiya active — lighter career pressure window (-1)")

    return {
        "score": score,
        "why": why,
    }


# ── L34 — 10H-2H-11H wealth-creation triad cohesion ──────────────────────────
def _layer_wealth_triad(intel: dict, kundli: dict) -> dict:
    """Weight: 6. The "wealth triad" = 2H (income) + 10H (karma) + 11H (gains).
    When the LORDS of these 3 houses are mutually connected (conjunction or
    aspect), the triad fires — sustainable wealth-from-career signature.
    """
    score = 0
    why: list[str] = []
    planets = kundli.get("planets") or []

    sl = _house_lord(intel, 2)
    tl = _house_lord(intel, 10)
    el = _house_lord(intel, 11)

    if not (sl and tl and el):
        return {"score": 0, "why": ["Wealth triad lords incomplete"], "triad": []}

    sl_h = _planet_house(planets, sl)
    tl_h = _planet_house(planets, tl)
    el_h = _planet_house(planets, el)

    # All 3 in same house = mahaapurna triad
    if sl_h is not None and sl_h == tl_h == el_h:
        score += 7
        why.append(f"⭐⭐ TRIAD: 2L {sl} + 10L {tl} + 11L {el} all conjunct in {sl_h}H — Maha-Lakshmi wealth signature (+7)")
    elif sl_h is not None and tl_h is not None and sl_h == tl_h:
        score += 3
        why.append(f"Triad 2-leg: 2L+10L conjunct in {sl_h}H (+3)")
    if tl_h is not None and el_h is not None and tl_h == el_h:
        score += 3
        why.append(f"Triad 2-leg: 10L+11L conjunct in {tl_h}H (+3)")
    if sl_h is not None and el_h is not None and sl_h == el_h:
        score += 2
        why.append(f"Triad 2-leg: 2L+11L conjunct in {sl_h}H (+2)")

    # Mutual 7th aspects
    if sl_h is not None and tl_h is not None and abs(sl_h - tl_h) == 6:
        score += 1
        why.append(f"Triad aspect: 2L↔10L 7th-aspect (+1)")
    if tl_h is not None and el_h is not None and abs(tl_h - el_h) == 6:
        score += 1
        why.append(f"Triad aspect: 10L↔11L 7th-aspect (+1)")

    return {
        "score": score,
        "why": why,
        "triad": [sl, tl, el],
    }


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER LAYERS — T1, T2, T3
# Is the natal promise activated NOW? When will it fire next?
# ─────────────────────────────────────────────────────────────────────────────

# ── T1 — Vimshottari MD+AD+PD timing ─────────────────────────────────────────
def _trigger_vimshottari(kundli: dict, intel: dict, karakas_d: dict) -> dict:
    """Weight: 12. Find the next MD/AD/PD window in which the lords signify
    CAREER_PROMISE houses {2, 6, 10, 11}. Returns:
      - current_window: {start, end, lords:(MD,AD,PD), score} — favourable if
        current MD/AD lords own/significate CAREER_PROMISE
      - next_career_window: same, for next AD where 10L or AmK or 11L or 2L
        becomes the AD lord OR aspects/rules CAREER_PROMISE houses
    """
    score = 0
    why: list[str] = []

    md, ad, pd = _dasha_lords(kundli)
    cd = kundli.get("currentDasha") or {}
    cp = kundli.get("currentPhase") or {}
    # Recognise multiple key conventions for AD start/end emitted by
    # different chart providers (startDate/endDate, start/end,
    # antardashaStart/antardashaEnd, ad_start/ad_end). currentPhase is
    # used as a final fallback because it always represents the
    # currently-active AD window.
    cur_start = (cd.get("startDate") or cd.get("start")
                 or cd.get("antardashaStart") or cd.get("ad_start")
                 or cp.get("start"))
    cur_end = (cd.get("endDate") or cd.get("end")
               or cd.get("antardashaEnd") or cd.get("ad_end")
               or cp.get("end"))

    tenth_lord = _house_lord(intel, 10)
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    sixth_lord = _house_lord(intel, 6)
    amk = (karakas_d or {}).get("AmK")
    career_lords = {tenth_lord, second_lord, eleventh_lord, sixth_lord, amk}
    career_lords.discard(None)

    planets = kundli.get("planets") or []

    # ── Score current MD lord
    if md:
        md_h = _planet_house(planets, md)
        md_dgn = _planet_dignity(intel, md)
        if md in career_lords:
            score += 5
            why.append(f"Current MD = {md} (one of career-significator lords) (+5)")
        if md_h in CAREER_PROMISE:
            score += 4
            why.append(f"Current MD lord {md} sits in career-promise h{md_h} (+4)")
        elif md_h in CAREER_DENIAL:
            score -= 3
            why.append(f"Current MD lord {md} sits in denial h{md_h} (-3)")
        if md_dgn in ("exalted", "own-sign", "moolatrikona"):
            score += 2
            why.append(f"Current MD lord {md} {md_dgn} — supports its mahadasha effects (+2)")
        elif md_dgn == "debilitated":
            score -= 2
            why.append(f"Current MD lord {md} debilitated — weakens MD effects (-2)")

    # ── Score current AD lord
    if ad:
        ad_h = _planet_house(planets, ad)
        ad_dgn = _planet_dignity(intel, ad)
        if ad in career_lords:
            score += 4
            why.append(f"Current AD = {ad} (career-significator) — career window ACTIVE (+4)")
        if ad_h in CAREER_PROMISE:
            score += 3
            why.append(f"Current AD lord {ad} in career-promise h{ad_h} (+3)")
        elif ad_h in CAREER_DENIAL:
            score -= 2
            why.append(f"Current AD lord {ad} in denial h{ad_h} (-2)")
        if ad_dgn == "debilitated":
            score -= 1
            why.append(f"Current AD lord {ad} debilitated — fragile window (-1)")

    # ── Score current PD lord
    if pd:
        if pd in career_lords:
            score += 2
            why.append(f"Current PD = {pd} (career-significator) — fine-tuned career sub-window (+2)")

    # ── Find next career-AD window from upcoming dasha periods
    upcoming = kundli.get("upcomingDashas") or kundli.get("antardashas") or []
    next_career_window = None
    if isinstance(upcoming, list):
        for u in upcoming[:30]:  # check next 30 sub-periods
            if not isinstance(u, dict):
                continue
            ad_lord = u.get("antardasha") or u.get("ad") or u.get("lord")
            if ad_lord in career_lords:
                next_career_window = {
                    "md":   u.get("mahadasha") or md,
                    "ad":   ad_lord,
                    "start": u.get("start") or u.get("startDate"),
                    "end":   u.get("end") or u.get("endDate"),
                    "reason": f"AD {ad_lord} is career-significator",
                }
                break

    return {
        "score": score,
        "why": why,
        "current_lords":      f"{md}/{ad}/{pd}",
        "current_window":     {"start": cur_start, "end": cur_end},
        "next_career_window": next_career_window,
        "career_lords_set":   sorted(career_lords),
    }


# ── T2 — Saturn transit on 10H/10L (career-change cycle) ─────────────────────
def _trigger_saturn_transit(saturn_t: dict, intel: dict) -> dict:
    """Weight: 7. Saturn transit on/aspecting 10H is the classical career-
    change cycle (recurs ~7-8 yrs as Saturn shifts each sign every 2.5 yrs).
    On-tenth = restructuring/recognition; aspecting-tenth = pressure-from-
    outside force on career.
    """
    score = 0
    why: list[str] = []

    if not saturn_t:
        return {"score": 0, "why": ["Saturn transit data unavailable"], "saturn_transit": {}}

    if saturn_t.get("on_tenth"):
        score += 5
        why.append(f"⭐ Saturn currently in your 10H (sign={saturn_t.get('saturn_sign')}) — restructure/recognition window ACTIVE (+5)")
    elif saturn_t.get("aspecting_tenth"):
        score += 2
        why.append(f"Saturn currently aspecting 10H (from sign={saturn_t.get('saturn_sign')}, h{saturn_t.get('saturn_house_from_lagna')}) — outside-pressure window (+2)")

    sh = saturn_t.get("saturn_house_from_lagna")
    if sh in {1, 4, 8}:
        score -= 2
        why.append(f"Saturn currently in h{sh} from lagna — internal slowdown phase (-2)")
    elif sh in {3, 6, 11}:
        score += 2
        why.append(f"Saturn currently in upachaya h{sh} from lagna — long-term gains (+2)")

    return {
        "score": score,
        "why": why,
        "saturn_transit": saturn_t,
    }


# ── T3 — Jupiter transit on 10H/2H/11H + Yogini cross-check ──────────────────
def _trigger_jupiter_yogini(jup_t: dict, yogini_d: dict, karakas_d: dict, intel: dict) -> dict:
    """Weight: 7. Jupiter transit on 10/2/11 = career-blessing window (Guru
    grace on karma/income/gains). Yogini Dasha cross-check confirms the
    Vimshottari signal independently."""
    score = 0
    why: list[str] = []

    if jup_t and jup_t.get("active_window"):
        aw = jup_t["active_window"]
        score += 5
        why.append(f"⭐ Jupiter currently transiting {aw.get('sign')} — hits {aw.get('hits')} (career-blessing window ACTIVE) (+5)")
    elif jup_t and jup_t.get("all_windows"):
        # Find next upcoming window
        future = [w for w in jup_t["all_windows"]
                  if w.get("start") > datetime.utcnow().strftime("%Y-%m-%d")]
        if future:
            nxt = future[0]
            why.append(f"Next Jupiter career-window: {nxt.get('start')} → {nxt.get('end')} in {nxt.get('sign')} (hits {nxt.get('hits')})")

    # Yogini Dasha cross-check
    if yogini_d:
        yog_lord = yogini_d.get("currentLord") or yogini_d.get("lord") or yogini_d.get("current_dasha_lord")
        amk = (karakas_d or {}).get("AmK")
        tl = _house_lord(intel, 10)
        if yog_lord and (yog_lord == amk or yog_lord == tl):
            score += 3
            why.append(f"Yogini current lord {yog_lord} = career-significator — INDEPENDENT confirmation (+3)")

    return {
        "score": score,
        "why": why,
        "jupiter_transit_active": (jup_t or {}).get("active_window"),
        "yogini_lord":            (yogini_d or {}).get("currentLord") or (yogini_d or {}).get("lord"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODIFIERS — 8 modifiers (±points to total score, no own weight)
# ─────────────────────────────────────────────────────────────────────────────

# ── M1 — 10L / Sun / Mercury combust ─────────────────────────────────────────
def _modifier_combust(intel: dict, kundli: dict) -> dict:
    """±5. Combust = within ~8-12° of Sun (depending on planet). Combust
    planets lose visible expression — career karaka burnt = stalled
    public-recognition aspect of career."""
    delta = 0
    why: list[str] = []
    planets = kundli.get("planets") or []
    tenth_lord = _house_lord(intel, 10)

    for planet in {tenth_lord, "Mercury", "Venus", "Saturn", "Mars"}:
        if not planet:
            continue
        if _is_combust(planets, planet):
            d = -2 if planet in ("Mercury", tenth_lord) else -1
            delta += d
            why.append(f"M1: {planet} combust → recognition/expression suppressed ({d:+d})")
    return {"delta": delta, "why": why, "name": "M1_combust"}


# ── M2 — 10L / Saturn / Jupiter retrograde ──────────────────────────────────
def _modifier_retrograde(intel: dict, kundli: dict) -> dict:
    """±3. Retrograde = past-life/internal mode of expression.
    For career: retro karakas often mean DELAYED but DEEPER outcomes."""
    delta = 0
    why: list[str] = []
    planets = kundli.get("planets") or []
    tenth_lord = _house_lord(intel, 10)
    amk_planets = {tenth_lord, "Saturn", "Jupiter", "Mercury"}

    for planet in amk_planets:
        if not planet:
            continue
        if _is_retrograde(planets, planet):
            if planet in ("Saturn", "Jupiter"):
                # Retrograde benefics often add depth (+1)
                delta += 1
                why.append(f"M2: {planet} retrograde → adds depth/research-orientation (+1)")
            elif planet == tenth_lord:
                delta -= 1
                why.append(f"M2: 10L {planet} retrograde → career delays / re-do cycles (-1)")
            else:
                why.append(f"M2: {planet} retrograde → mixed effect (0)")
    return {"delta": delta, "why": why, "name": "M2_retrograde"}


# ── M3 — Malefic aspects on 10H / 10L / AmK ──────────────────────────────────
def _modifier_malefic_aspects(intel: dict, kundli: dict, karakas_d: dict) -> dict:
    """±5. Mars/Saturn/Rahu/Ketu aspects on career-key points create
    friction (Mars=conflict, Saturn=delay, Rahu=manipulation, Ketu=detachment).
    Saturn's aspect on 10H is treated as NEUTRAL (Saturn = karma karaka)."""
    delta = 0
    why: list[str] = []
    planets = kundli.get("planets") or []
    tenth_lord = _house_lord(intel, 10)
    amk = (karakas_d or {}).get("AmK")

    aspectors_10 = _planets_aspecting_house(planets, 10)
    bad_aspectors = [p for p in aspectors_10 if p in {"Mars", "Rahu", "Ketu"}]
    if bad_aspectors:
        delta -= min(3, len(bad_aspectors) * 2)
        why.append(f"M3: 10H aspected by {bad_aspectors} → friction signature ({-min(3, len(bad_aspectors)*2):+d})")

    if tenth_lord:
        tl_h = _planet_house(planets, tenth_lord)
        if tl_h is not None:
            tl_aspectors = _planets_aspecting_house(planets, tl_h)
            tl_bad = [p for p in tl_aspectors if p in {"Mars", "Rahu", "Ketu"}]
            if tl_bad:
                delta -= 1
                why.append(f"M3: 10L {tenth_lord} aspected by {tl_bad} (-1)")

    if amk:
        amk_h = _planet_house(planets, amk)
        if amk_h is not None:
            amk_aspectors = _planets_aspecting_house(planets, amk_h)
            amk_bad = [p for p in amk_aspectors if p in {"Mars", "Rahu", "Ketu"}]
            if amk_bad:
                delta -= 1
                why.append(f"M3: Amatyakaraka {amk} aspected by {amk_bad} (-1)")

    return {"delta": delta, "why": why, "name": "M3_malefic_aspects"}


# ── M4 — Lagnesh strength (self-capability) ──────────────────────────────────
def _modifier_lagnesh(intel: dict) -> dict:
    """±3. Strong lagnesh = self can sustain demands of career;
    Weak lagnesh = good promise wasted due to self-undermining."""
    delta = 0
    why: list[str] = []
    ll = _house_lord(intel, 1)
    if ll:
        d = _planet_dignity(intel, ll)
        if d in ("exalted", "moolatrikona", "own-sign"):
            delta += 3
            why.append(f"M4: Lagnesh {ll} {d} — self capable of carrying career demands (+3)")
        elif d == "debilitated":
            delta -= 3
            why.append(f"M4: Lagnesh {ll} debilitated — self-undermining, blocks career (-3)")
        elif d == "enemy-sign":
            delta -= 1
            why.append(f"M4: Lagnesh {ll} enemy-sign — minor self-friction (-1)")
    return {"delta": delta, "why": why, "name": "M4_lagnesh"}


# ── M5 — Saturn transit modifier (Sade-Sati / Dhaiya intensity) ──────────────
def _modifier_sade_sati(intel: dict, kundli: dict) -> dict:
    """-5. Already partially in L32; this modifier ADDS to the verdict tilt
    when Sade Sati PEAK is active — overall career outlook trends restrictive
    regardless of natal promise."""
    delta = 0
    why: list[str] = []
    sade = intel.get("sade_sati") or kundli.get("sadeSati") or {}
    if isinstance(sade, dict) and sade.get("active"):
        phase = str(sade.get("phase") or "").lower()
        if phase in ("peak", "second", "second-phase"):
            delta -= 3
            why.append(f"M5: Sade Sati PEAK active — career restructuring window (-3)")
        elif phase in ("first", "rising"):
            delta -= 1
            why.append("M5: Sade Sati FIRST phase — initial restraint (-1)")
    return {"delta": delta, "why": why, "name": "M5_sade_sati"}


# ── M6 — Jupiter transit on 10/2/11 ──────────────────────────────────────────
def _modifier_jupiter_transit(jup_t: dict) -> dict:
    """+6. Jupiter currently transiting 10H/2H/11H sign = active grace window.
    Already partially scored in T3; this modifier PUSHES the final verdict
    when an active window exists (acts as a verdict-tilt)."""
    delta = 0
    why: list[str] = []
    if jup_t and jup_t.get("active_window"):
        aw = jup_t["active_window"]
        hits = aw.get("hits") or []
        if any("10" in h or "11" in h or "2" in h for h in hits):
            delta += 4
            why.append(f"M6: Jupiter active in {aw.get('sign')} hitting {hits} — grace window now (+4)")
    return {"delta": delta, "why": why, "name": "M6_jupiter_transit"}


# ── M8 — Rahu-Ketu axis on 10/4 (sudden change tilt) ─────────────────────────
def _modifier_rahu_ketu_axis(kundli: dict) -> dict:
    """±5. Rahu in 10H or 4H signals sudden, unconventional career changes.
    Ketu opposite (in 4H/10H) = detachment-from-foundation pattern.
    This is a SUDDEN-EVENT modifier — career is volatile but high-amplitude.
    """
    delta = 0
    why: list[str] = []
    planets = kundli.get("planets") or []
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")
    if rahu_h == 10:
        delta += 2
        why.append("M8: Rahu in 10H — sudden rise / unconventional / foreign career tilt (+2)")
    elif rahu_h == 4:
        delta -= 1
        why.append("M8: Rahu in 4H — career disrupts home/comfort base (-1)")
    if ketu_h == 10:
        delta -= 1
        why.append("M8: Ketu in 10H — detachment from conventional career (-1)")
    elif ketu_h == 4:
        delta += 1
        why.append("M8: Ketu in 4H + Rahu (likely 10H) — foundation-detached career launch (+1)")
    return {"delta": delta, "why": why, "name": "M8_rahu_ketu_axis"}


# ─────────────────────────────────────────────────────────────────────────────
# CONDITIONALS — fire only when question type matches
# ─────────────────────────────────────────────────────────────────────────────

# ── C1 — Govt-job check ──────────────────────────────────────────────────────
def _conditional_govt_job(intel: dict, kundli: dict, karakas_d: dict, kp: Optional[dict] = None) -> dict:
    """Fires for q_type == 'govt_job' or strong Sun-driven natal chart.

    Govt-job classical recipe (any 2 of these → strong govt-promise):
      1. Sun in own/exalted sign in kendra/trikona
      2. 10L exalted or in own sign
      3. Sun-Mars-Jupiter combination (Atmakaraka or 10H involvement)
      4. AmK = Sun
      5. 10L = Sun OR 10H Sun-occupied
      6. Sasha-yoga (Saturn for PSU/govt-service)
      7. Sun-Saturn combo (conjunct OR mutual 7th aspect) in D1
      8. Sun-Saturn combo in D9 Navamsha (soul-confirmation, +bonus)
      9. Saturn in 2nd/5th/9th from Sun (artha+kona-trine) in D1
      10. Same trine rule applied in D10 Dashamsha (career-chart, +bonus)
      11. 6L in 10H OR 10L in 6H (classical naukri/service yoga)
      12. 10L conjunct Sun (career-lord fused with govt-karaka)
      + KP cusps 10/6/1 CSL signification cross-check.
    """
    score = 0
    why: list[str] = []
    flags: list[str] = []
    planets = kundli.get("planets") or []

    sun_dgn = _planet_dignity(intel, "Sun")
    sun_h = _planet_house(planets, "Sun")
    if sun_dgn in ("exalted", "own-sign", "moolatrikona") and sun_h in {1, 4, 5, 7, 9, 10}:
        score += 4
        flags.append("Sun strong in kendra/trikona")
        why.append(f"⭐ C1: Sun {sun_dgn} in h{sun_h} (kendra/trikona) — govt-authority signature (+4)")

    tenth_lord = _house_lord(intel, 10)
    if tenth_lord:
        tl_dgn = _planet_dignity(intel, tenth_lord)
        if tl_dgn in ("exalted", "own-sign"):
            score += 3
            flags.append("10L strong")
            why.append(f"C1: 10L {tenth_lord} {tl_dgn} — career promise locked (+3)")

    # Sun-Mars-Jupiter combo (any 2 conjunct or aspecting 10H)
    sun_h = _planet_house(planets, "Sun")
    mars_h = _planet_house(planets, "Mars")
    jup_h = _planet_house(planets, "Jupiter")
    combo_in_career = sum(1 for h in (sun_h, mars_h, jup_h) if h in {1, 5, 9, 10})
    if combo_in_career >= 2:
        score += 3
        flags.append(f"{combo_in_career}-of Sun/Mars/Jupiter in kendra/trikona")
        why.append(f"C1: {combo_in_career} of (Sun/Mars/Jupiter) in kendra/trikona — govt-recipe combo (+3)")

    # AmK = Sun
    amk = (karakas_d or {}).get("AmK")
    if amk == "Sun":
        score += 4
        flags.append("AmK = Sun")
        why.append("⭐ C1: Amatyakaraka = Sun — soul-career = govt/authority (+4)")

    # 10L = Sun OR Sun in 10H
    if tenth_lord == "Sun":
        score += 3
        flags.append("10L = Sun")
        why.append("C1: 10L = Sun — career-house lord IS govt karaka (+3)")
    if sun_h == 10:
        score += 3
        flags.append("Sun in 10H")
        why.append("C1: Sun in 10H — direct govt-career signature (+3)")

    # Saturn for PSU/service-govt
    sat_dgn = _planet_dignity(intel, "Saturn")
    sat_h = _planet_house(planets, "Saturn")
    if sat_dgn in ("own-sign", "exalted") and sat_h in {1, 4, 7, 10}:
        score += 2
        flags.append("Sasha-yoga (PSU/admin)")
        why.append(f"C1: Sasha-yoga (Saturn {sat_dgn} in kendra h{sat_h}) — PSU/service-govt (+2)")

    # ── Phase 2.8.32 ADD-ONLY rules (user-specified govt-job classical combos) ──
    # Helper: Sun-Saturn combo in any chart (conjunction OR mutual 7th aspect).
    # Returns (points, why_msg) or (0, None). bonus stacks for divisional-chart confirmation.
    def _sun_sat_combo(chart_planets: list, chart_label: str, bonus: int = 0):
        s_h = _planet_house(chart_planets, "Sun")
        st_h = _planet_house(chart_planets, "Saturn")
        if not s_h or not st_h:
            return 0, None
        if s_h == st_h:
            pts = 3 + bonus
            return pts, f"C1: Sun-Saturn conjunct in h{s_h} ({chart_label}) — authority + discipline yoga (+{pts})"
        if abs(s_h - st_h) == 6:
            pts = 2 + bonus
            return pts, f"C1: Sun-Saturn mutual 7th aspect ({chart_label}) — govt-power axis (+{pts})"
        return 0, None

    # Helper: Saturn in 2nd/5th/9th FROM Sun (kona-trine + artha-axis).
    def _sat_trine_from_sun(chart_planets: list, chart_label: str, bonus: int = 0):
        s_h = _planet_house(chart_planets, "Sun")
        st_h = _planet_house(chart_planets, "Saturn")
        if not s_h or not st_h:
            return 0, None
        from_sun = ((st_h - s_h + 12) % 12) + 1
        if from_sun in (5, 9):
            pts = 3 + bonus
            return pts, f"C1: Saturn in {from_sun}th from Sun ({chart_label}) — kona-trine govt yoga (+{pts})"
        if from_sun == 2:
            pts = 2 + bonus
            return pts, f"C1: Saturn in 2nd from Sun ({chart_label}) — artha-axis govt support (+{pts})"
        return 0, None

    # Rule 7: Sun-Saturn combo in D1
    pts, msg = _sun_sat_combo(planets, "D1")
    if pts:
        score += pts
        flags.append("Sun-Saturn combo D1")
        why.append(msg)

    # Rule 8: Sun-Saturn combo in D9 Navamsha (+1 bonus — soul-chart confirmation)
    d9_planets = ((kundli.get("divisionalCharts") or {}).get("D9") or {}).get("planets") or []
    pts, msg = _sun_sat_combo(d9_planets, "D9 Navamsha", bonus=1)
    if pts:
        score += pts
        flags.append("Sun-Saturn combo D9")
        why.append(msg)

    # Rule 9: Saturn-trine-from-Sun in D1
    pts, msg = _sat_trine_from_sun(planets, "D1")
    if pts:
        score += pts
        flags.append("Saturn trine-from-Sun D1")
        why.append(msg)

    # Rule 10: Saturn-trine-from-Sun in D10 Dashamsha (+1 bonus — career-chart)
    d10_planets = ((kundli.get("divisionalCharts") or {}).get("D10") or {}).get("planets") or []
    pts, msg = _sat_trine_from_sun(d10_planets, "D10 Dashamsha", bonus=1)
    if pts:
        score += pts
        flags.append("Saturn trine-from-Sun D10")
        why.append(msg)

    # Rule 11: 6-10 exchange (classical naukri/service yoga)
    sixth_lord = _house_lord(intel, 6)
    sixth_lord_h = _planet_house(planets, sixth_lord) if sixth_lord else None
    tenth_lord_h = _planet_house(planets, tenth_lord) if tenth_lord else None
    if sixth_lord and sixth_lord_h == 10:
        score += 3
        flags.append("6L in 10H (naukri yoga)")
        why.append(f"C1: 6L {sixth_lord} in 10H — naukri/service yoga (+3)")
    if tenth_lord and tenth_lord_h == 6:
        score += 3
        flags.append("10L in 6H (naukri yoga)")
        why.append(f"C1: 10L {tenth_lord} in 6H — career via service/employment (+3)")

    # Rule 12: 10L conjunct Sun (career-lord fused with govt-karaka, distinct from Rule 5a)
    if tenth_lord and tenth_lord != "Sun" and sun_h and tenth_lord_h == sun_h:
        score += 3
        flags.append("10L conjunct Sun")
        why.append(f"C1: 10L {tenth_lord} conjunct Sun in h{sun_h} — career fused with govt-karaka (+3)")

    # KP bucket-tuned cross-check
    kp_assist = _kp_bucket_assist(kp or {}, "govt_job")
    if kp_assist["score"] != 0 or kp_assist["why"]:
        score += kp_assist["score"]
        why.extend(kp_assist["why"])
        if kp_assist["score"] > 0:
            flags.append("KP cusps confirm")

    promise = "high" if score >= 8 else ("moderate" if score >= 4 else "low")
    return {
        "fired": True,
        "score": score,
        "why": why,
        "flags": flags,
        "govt_promise_level": promise,
        "kp_summary": kp_assist["summary"],
    }


# ── C4 — Promotion-window check ──────────────────────────────────────────────
def _conditional_promotion_window(t1_d: dict, intel: dict, jup_t: dict, saturn_t: dict, kp: Optional[dict] = None) -> dict:
    """Fires for q_type == 'promotion'.

    Promotion-window confirmed if at least 2 of:
      - Current AD lord = 10L or 11L or AmK
      - Jupiter currently transiting natal 10H/11H sign
      - Next career-AD window within 18 months
      - Saturn aspecting natal 10H (recognition transit)
    """
    confirmed = 0
    why: list[str] = []

    if not t1_d:
        return {"fired": True, "promotion_signal": "low", "why": ["T1 unavailable for promotion check"]}

    cur_lords = (t1_d or {}).get("current_lords") or ""
    parts = cur_lords.split("/")
    ad = parts[1].strip() if len(parts) > 1 else ""
    el = _house_lord(intel, 11)
    tl = _house_lord(intel, 10)
    if ad and (ad == el or ad == tl):
        confirmed += 1
        why.append(f"✓ Current AD = {ad} (career/gain lord)")

    if jup_t and jup_t.get("active_window"):
        aw = jup_t["active_window"]
        hits = aw.get("hits") or []
        if any("10" in h or "11" in h for h in hits):
            confirmed += 1
            why.append(f"✓ Jupiter active in {aw.get('sign')} (hits {hits})")

    nxt = (t1_d or {}).get("next_career_window")
    if nxt and nxt.get("start"):
        # Check within 18 months
        try:
            start_dt = datetime.fromisoformat(str(nxt["start"]).split("T")[0] + (
                "" if len(str(nxt["start"]).split("T")[0]) == 10 else "-01"
            ))
            if (start_dt - datetime.utcnow()).days <= 540:
                confirmed += 1
                why.append(f"✓ Next career-AD ({nxt.get('ad')}) starts {nxt.get('start')} (within 18 mo)")
        except Exception:
            pass

    if saturn_t and (saturn_t.get("on_tenth") or saturn_t.get("aspecting_tenth")):
        confirmed += 1
        why.append(f"✓ Saturn on/aspecting 10H (recognition cycle)")

    # KP bucket-tuned cross-check (cusps 11/10/6 — gains+recognition+rivals)
    kp_assist = _kp_bucket_assist(kp or {}, "promotion")
    if kp_assist["score"] >= 5:
        confirmed += 1
        why.append(f"✓ KP cusps confirm promotion ({kp_assist['summary']})")
    elif kp_assist["score"] <= -5:
        confirmed = max(0, confirmed - 1)
        why.append(f"✗ KP cusps deny promotion ({kp_assist['summary']})")
    why.extend(kp_assist["why"])

    if confirmed >= 3:
        signal = "STRONG"
    elif confirmed == 2:
        signal = "moderate"
    elif confirmed == 1:
        signal = "weak"
    else:
        signal = "none-active"

    return {
        "fired": True,
        "promotion_signal": signal,
        "confirmed_count": confirmed,
        "why": why,
        "kp_summary": kp_assist["summary"],
    }


# ── C5 — Career-setback recovery check ───────────────────────────────────────
def _conditional_setback_recovery(t1_d: dict, jup_t: dict, intel: dict, kp: Optional[dict] = None) -> dict:
    """Fires for q_type == 'career_setback'.

    Recovery signals (when stress will ease):
      - Sade Sati phase moving to 'setting' or already past
      - Next AD lord is benefic (Jupiter/Venus/Mercury) or = career-significator
      - Jupiter transit upcoming on natal 1H/5H/9H/10H/11H
      - Current AD ending within 6 months
    """
    why: list[str] = []
    recovery_score = 0

    sade = intel.get("sade_sati") or {}
    if isinstance(sade, dict):
        if not sade.get("active"):
            recovery_score += 2
            why.append("✓ Sade Sati not active — recovery foundation present")
        elif str(sade.get("phase") or "").lower() in ("setting", "third"):
            recovery_score += 1
            why.append("✓ Sade Sati setting phase — pressure easing")

    if t1_d:
        nxt = t1_d.get("next_career_window") or {}
        nxt_ad = nxt.get("ad")
        if nxt_ad in NATURAL_BENEFICS:
            recovery_score += 3
            why.append(f"✓ Next career-AD = {nxt_ad} (benefic) — soft recovery window")
        elif nxt_ad:
            recovery_score += 1
            why.append(f"○ Next career-AD = {nxt_ad}")

    if jup_t:
        future = [w for w in (jup_t.get("all_windows") or [])
                  if w.get("start") > datetime.utcnow().strftime("%Y-%m-%d")]
        if future:
            nxt_jw = future[0]
            recovery_score += 2
            why.append(f"✓ Jupiter career-window incoming: {nxt_jw.get('start')} → {nxt_jw.get('end')} ({nxt_jw.get('sign')})")

    # KP bucket-tuned cross-check.
    # career_setback bucket has MIXED polarity:
    #   - cusps 8/12/6 carry polarity "-" → cusp-score is +weight when CSL
    #     signifies CAREER_DENIAL (event confirmed = setback CONTINUING).
    #     For RECOVERY outlook we SUBTRACT these contributions (setback firing
    #     means recovery weak).
    #   - cusps 11/5 carry polarity "+" → cusp-score is +weight when CSL
    #     signifies CAREER_PROMISE (recovery cusps active). For RECOVERY
    #     outlook we ADD these directly.
    # We split per-cusp instead of inverting the entire net (per-cusp respects
    # genuine recovery signals even when stronger setback signals are present).
    kp_assist = _kp_bucket_assist(kp or {}, "career_setback")
    setback_component = 0   # contribution from polarity "-" cusps (8/12/6)
    recovery_component = 0  # contribution from polarity "+" cusps (11/5)
    for cnum, info in (kp_assist.get("per_cusp") or {}).items():
        if info.get("polarity") == "-":
            setback_component += int(info.get("score") or 0)
        else:
            recovery_component += int(info.get("score") or 0)
    kp_recovery_delta = recovery_component - setback_component
    if kp_recovery_delta != 0:
        recovery_score += kp_recovery_delta
        why.append(f"○ KP recovery-net {kp_recovery_delta:+d} (recovery-cusps {recovery_component:+d}, setback-cusps {setback_component:+d})")
    why.extend(kp_assist["why"])

    if recovery_score >= 5:
        outlook = "STRONG_RECOVERY"
    elif recovery_score >= 3:
        outlook = "moderate_recovery"
    elif recovery_score >= 1:
        outlook = "slow_recovery"
    else:
        outlook = "no_clear_signal"

    return {
        "fired": True,
        "recovery_outlook": outlook,
        "recovery_score": recovery_score,
        "why": why,
        "kp_summary": kp_assist["summary"],
    }


# ── C7 — Transfer probability ────────────────────────────────────────────────
def _conditional_transfer(intel: dict, kundli: dict, saturn_t: dict, kp: Optional[dict] = None) -> dict:
    """Fires for q_type == 'transfer'. Checks short-relocation/job-posting
    likelihood. Combines:
      - 3H (short journeys) + 12H (place-change) lords' position
      - Saturn transit on 10H/3H/12H (career-displacement transit)
      - Rahu involvement with 3/12 (sudden-move axis)
      - KP cusps 3 + 12 + 10 CSLs
    """
    score = 0
    why: list[str] = []
    flags: list[str] = []
    planets = kundli.get("planets") or []

    third_lord   = _house_lord(intel, 3)
    twelfth_lord = _house_lord(intel, 12)
    for label, lord in (("3L", third_lord), ("12L", twelfth_lord)):
        if lord:
            lh = _planet_house(planets, lord)
            if lh in {3, 9, 10, 12}:
                score += 2
                flags.append(f"{label} {lord} in h{lh}")
                why.append(f"C7: {label} {lord} in h{lh} — relocation karma active (+2)")

    rahu_h = _planet_house(planets, "Rahu")
    if rahu_h in {3, 12, 10}:
        score += 2
        flags.append(f"Rahu in h{rahu_h}")
        why.append(f"C7: Rahu in h{rahu_h} — sudden-move axis live (+2)")

    if isinstance(saturn_t, dict):
        if saturn_t.get("on_tenth") or saturn_t.get("aspecting_tenth"):
            score += 3
            flags.append("Saturn on/aspecting 10H")
            why.append("C7: Saturn transit on/aspecting 10H — posting/transfer cycle (+3)")

    # KP bucket cross-check (cusps 3, 12, 10)
    kp_assist = _kp_bucket_assist(kp or {}, "transfer")
    score += kp_assist["score"]
    why.extend(kp_assist["why"])

    if score >= 7:
        verdict = "STRONG_TRANSFER_LIKELY"
    elif score >= 4:
        verdict = "moderate_chance"
    elif score >= 1:
        verdict = "low_chance"
    else:
        verdict = "stay_put"

    return {
        "fired": True,
        "transfer_verdict": verdict,
        "score": score,
        "flags": flags,
        "why": why,
        "kp_summary": kp_assist["summary"],
    }


# ── C8 — Resignation viability ───────────────────────────────────────────────
def _conditional_resignation(t1_d: dict, intel: dict, kp: Optional[dict] = None) -> dict:
    """Fires for q_type == 'resignation'. Should the user quit?
    Green-signal recipe (any 2-3):
      - Current AD lord = 12L or 8L (exit-house lord) → graceful exit window
      - 6L weak/afflicted → current-job dharma exhausted
      - Next AD lord favours 10/11 (gain after exit)
      - KP cusp 12 CSL signifies promise (clean exit) +
        cusp 6 CSL signifies denial (current-job frictions confirming exit)
    """
    score = 0
    why: list[str] = []
    flags: list[str] = []

    twelfth_lord = _house_lord(intel, 12)
    eighth_lord  = _house_lord(intel, 8)
    sixth_lord   = _house_lord(intel, 6)

    if t1_d:
        cur_lords = (t1_d or {}).get("current_lords") or ""
        parts = cur_lords.split("/")
        ad = parts[1].strip() if len(parts) > 1 else ""
        if ad and ad in {twelfth_lord, eighth_lord}:
            score += 4
            flags.append(f"AD = exit-house lord ({ad})")
            why.append(f"⭐ C8: Current AD = {ad} (12L/8L) — exit window OPEN (+4)")

        nxt = (t1_d or {}).get("next_career_window") or {}
        nxt_ad = nxt.get("ad")
        tl = _house_lord(intel, 10)
        el = _house_lord(intel, 11)
        if nxt_ad and nxt_ad in {tl, el}:
            score += 3
            flags.append(f"Next AD ({nxt_ad}) = career/gain lord")
            why.append(f"✓ C8: Next AD {nxt_ad} = 10L/11L — gain after exit confirmed (+3)")

    # 6L afflicted: check dignity
    if sixth_lord:
        sxl_dgn = _planet_dignity(intel, sixth_lord)
        if sxl_dgn in ("debilitated", "enemy-sign"):
            score += 2
            flags.append(f"6L {sixth_lord} {sxl_dgn}")
            why.append(f"C8: 6L {sixth_lord} {sxl_dgn} — current-job dharma fading (+2)")

    # KP bucket cross-check (cusps 12, 1, 6)
    kp_assist = _kp_bucket_assist(kp or {}, "resignation")
    score += kp_assist["score"]
    why.extend(kp_assist["why"])

    if score >= 8:
        verdict = "RESIGN_NOW"
    elif score >= 4:
        verdict = "plan_exit_3_to_6mo"
    elif score >= 1:
        verdict = "wait_for_window"
    else:
        verdict = "stay_no_exit_signal"

    return {
        "fired": True,
        "resignation_verdict": verdict,
        "score": score,
        "flags": flags,
        "why": why,
        "kp_summary": kp_assist["summary"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# SYNASTRY-EQUIVALENT (BOSS + BUSINESS PARTNER)
# ─────────────────────────────────────────────────────────────────────────────
def _synastry_career(self_kundli: dict, self_intel: dict,
                     other_kundli: Optional[dict],
                     role: str = "boss") -> dict:
    """Optional layer. Activates only when boss_kundli or partner_kundli
    is provided. Compares your 10H/6H lords' rasi with other's planets
    and detects favourable/conflict overlays.

    Inputs:
      role: "boss" — checks your 10L vs boss's planets in your houses
            "partner" — checks your 7L vs partner's planets in your houses
    """
    if not other_kundli:
        return {"fired": False, "score": 0, "why": [f"No {role}_kundli provided — synastry skipped"]}

    score = 0
    why: list[str] = []
    self_planets = self_kundli.get("planets") or []
    other_planets = other_kundli.get("planets") or []

    # Get the relevant lord from self
    if role == "boss":
        self_lord = _house_lord(self_intel, 10)
        target_houses_in_self = {6, 10, 11}  # boss occupying these = supportive
        target_houses_bad    = {8, 12}
    elif role == "partner":
        self_lord = _house_lord(self_intel, 7)
        target_houses_in_self = {7, 10, 11}
        target_houses_bad    = {6, 8, 12}
    else:
        return {"fired": False, "score": 0, "why": [f"Unknown synastry role: {role}"]}

    # Find other's planets that occupy your career-key houses
    self_lagna_idx = _sign_idx((self_kundli.get("ascendant") or {}).get("sign", "")
                               if isinstance(self_kundli.get("ascendant"), dict) else "")
    if self_lagna_idx < 0:
        return {"fired": True, "score": 0, "why": [f"{role.title()} synastry: self lagna unknown"]}

    overlay_supportive = []
    overlay_blocking = []
    for op in other_planets:
        if not isinstance(op, dict):
            continue
        op_name = op.get("name")
        op_sign = op.get("sign")
        op_sign_idx = _sign_idx(op_sign or "")
        if op_sign_idx < 0:
            continue
        # Compute which house of YOUR chart their planet falls in
        house_in_self = ((op_sign_idx - self_lagna_idx) % 12) + 1
        if house_in_self in target_houses_in_self:
            if op_name in NATURAL_BENEFICS:
                score += 2
                overlay_supportive.append(f"{op_name}→h{house_in_self}")
                why.append(f"{role.title()}'s {op_name} in your h{house_in_self} — supportive overlay (+2)")
            elif op_name in ("Sun", "Saturn", "Mars"):
                score += 1
                overlay_supportive.append(f"{op_name}→h{house_in_self}")
                why.append(f"{role.title()}'s {op_name} in your h{house_in_self} — disciplinary support (+1)")
        elif house_in_self in target_houses_bad:
            if op_name in {"Mars", "Saturn", "Rahu", "Ketu"}:
                score -= 2
                overlay_blocking.append(f"{op_name}→h{house_in_self}")
                why.append(f"{role.title()}'s {op_name} in your h{house_in_self} — blocking overlay (-2)")

    # Cross-aspect: other's Sun aspecting your 10L
    if self_lord:
        other_sun_h_self = None
        for op in other_planets:
            if isinstance(op, dict) and op.get("name") == "Sun":
                op_sign_idx = _sign_idx(op.get("sign") or "")
                if op_sign_idx >= 0:
                    other_sun_h_self = ((op_sign_idx - self_lagna_idx) % 12) + 1
        self_lord_h = _planet_house(self_planets, self_lord)
        if other_sun_h_self and self_lord_h:
            if abs(other_sun_h_self - self_lord_h) == 6:
                score += 2
                why.append(f"{role.title()}'s Sun 7th-aspects your {self_lord} — authority recognition (+2)")

    return {
        "fired": True,
        "score": score,
        "why": why,
        "overlay_supportive": overlay_supportive,
        "overlay_blocking":   overlay_blocking,
        "role": role,
    }


# ─────────────────────────────────────────────────────────────────────────────
# REMEDY SELECTION (career-specific)
# ─────────────────────────────────────────────────────────────────────────────
def _select_career_remedy(intel: dict, kundli: dict, karakas_d: dict,
                          weakest_planet: Optional[str]) -> dict:
    """Use remedies.select_remedies() to pick a planet-specific remedy
    based on the WEAKEST career-relevant planet (10L or AmK or Sun/Saturn/
    Mercury/Jupiter — whichever is weakest). Returns a dict with mantra +
    donation + day + gemstone alternatives."""
    try:
        from remedies import select_remedies
    except Exception:
        return {
            "remedy_text": _FALLBACK_REMEDY,
            "weakest_planet": weakest_planet,
            "source": "fallback (remedies module unavailable)",
        }

    planet_verdicts = {}

    # Build a planet → verdict-strength dict for remedies module
    for d in (intel.get("dignities") or []):
        if isinstance(d, dict):
            p = d.get("planet")
            s = d.get("status") or d.get("dignity")
            if p and s:
                # Map dignity → verdict signal
                if s in ("debilitated", "enemy-sign"):
                    planet_verdicts[p] = "weak"
                elif s in ("exalted", "own-sign", "moolatrikona"):
                    planet_verdicts[p] = "strong"
                else:
                    planet_verdicts[p] = "neutral"

    try:
        remedies_list = select_remedies(planet_verdicts)
    except Exception:
        remedies_list = []

    if not remedies_list:
        return {
            "remedy_text": _FALLBACK_REMEDY,
            "weakest_planet": weakest_planet,
            "source": "fallback (no remedies returned)",
        }

    # Prefer remedy targeting the weakest career planet
    chosen = None
    if weakest_planet:
        chosen = next((r for r in remedies_list if r.get("planet") == weakest_planet), None)
    if not chosen:
        chosen = remedies_list[0]

    return {
        "remedy_text":   chosen.get("text") or chosen.get("remedy") or _FALLBACK_REMEDY,
        "weakest_planet": weakest_planet,
        "remedy_planet": chosen.get("planet"),
        "remedy_type":   chosen.get("type"),
        "source": "remedies.select_remedies",
    }


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY GENERATOR — bucket × verdict → pre-baked Hinglish actions
# ─────────────────────────────────────────────────────────────────────────────
# Verdict labels (4 buckets — career-relabeled):
#   green_go      : favourable; act now
#   yellow_wait   : mixed; wait for trigger
#   slow_burn     : long-term promise; patience needed
#   red_avoid     : adverse; defer/restructure
#
# 12 question-buckets × 4 verdicts = 48 strategy variants.
# Each strategy is a 2-3 sentence Hinglish action that the AI narrator
# embeds verbatim into the final response.
_STRATEGY_TABLE: dict[str, dict[str, str]] = {
    # ── job_change ──
    "job_change": {
        "green_go": (
            "Naukri change ke liye yeh window favourable hai — aap actively "
            "interview/applications shuru kar dein. Jo offer pehle aaye usko "
            "carefully evaluate karein, role + culture + manager dono dekhein."
        ),
        "yellow_wait": (
            "Switch ka mann hai par signals mixed hain — current role mein "
            "skills upgrade aur networking par focus karein. Final move next "
            "favourable transit window mein karein, abhi rush nahi."
        ),
        "slow_burn": (
            "Naukri change long-term mein hogi par foundation abhi banani "
            "hai — courses, certifications, profile-building par 3-6 mahine "
            "lagaayein. Patience rakhein, soft transition better hoga."
        ),
        "red_avoid": (
            "Abhi switch karna risk hai — current dasha aur transit dono "
            "stable role demand kar rahe hain. 4-6 mahine ruk jaayein, "
            "tab tak existing role mein consolidate karein."
        ),
    },
    # ── promotion ──
    "promotion": {
        "green_go": (
            "Promotion / appraisal favourable hai — manager se proactively "
            "review-meeting maango, achievements ek doc mein document karein, "
            "aur next-level role ki responsibility abhi se shoulder karein."
        ),
        "yellow_wait": (
            "Promotion ke signals mixed hain — visibility-projects par "
            "kaam karein, cross-functional contribution dikhayein, par "
            "formal announcement next cycle mein hi expect karein."
        ),
        "slow_burn": (
            "Promotion ki preparation abhi karein — leadership skills, "
            "team-management exposure, aur business-impact metrics build "
            "karein. 12-18 mahine ka cycle hai, patient reward milega."
        ),
        "red_avoid": (
            "Is cycle promotion mushkil hai — current Saturn / dasha "
            "structural hai. Ego ko side karein, kaam ki quality par "
            "concentrate karein. Restructuring/redeployment ke liye prepare rahein."
        ),
    },
    # ── govt_job ──
    "govt_job": {
        "green_go": (
            "Govt-job ke liye chart strong hai — UPSC/SSC/PSU jo bhi exam "
            "target ho, daily 4-6 ghante disciplined study + previous "
            "papers + mock-tests routine bana lein. Coaching + self-study "
            "dono balance rakhein."
        ),
        "yellow_wait": (
            "Selection signals mixed hain — preparation continue karein "
            "par parallel backup options (PSU, state-level exams) bhi "
            "explore karein. Multi-attempt mindset rakhein."
        ),
        "slow_burn": (
            "Govt-job destiny mein hai par 2-3 attempts lag sakte hain — "
            "long-term commitment, consistency, aur mental health par "
            "dhyaan dein. Family/financial backup zaruri hai."
        ),
        "red_avoid": (
            "Govt-exam path currently strain de raha hai — agar 2+ "
            "attempts ho gaye, parallel career line consider karein. "
            "Ek hi route par identity attach karna avoid karein."
        ),
    },
    # ── transfer ──
    "transfer": {
        "green_go": (
            "Transfer / posting favourable hai — apni preferred location "
            "ka formal request HR ko dein, supporting documents ready "
            "rakhein, aur networking through senior contacts use karein."
        ),
        "yellow_wait": (
            "Transfer ke signals mixed — current location 6-12 mahine "
            "aur consolidate karein, fir formal request dein. Forced "
            "transfer ke risk se bachne ke liye performance up rakhein."
        ),
        "slow_burn": (
            "Transfer hoga par slow process hai — patience aur seniority "
            "build karein. Right-cycle aane ka wait karein, force karne "
            "se uncomfortable posting mil sakti hai."
        ),
        "red_avoid": (
            "Transfer-request ka outcome currently unfavourable — abhi "
            "request karna better opportunity reject ho jaane ka risk "
            "hai. Current posting mein achievements log karein."
        ),
    },
    # ── resignation ──
    "resignation": {
        "green_go": (
            "Naukri chodne ke liye timing acchi hai — par 60-90 din ka "
            "financial buffer, next-role offer letter (preferably hand mein), "
            "aur clean exit (notice + handover) zaroor karein. Burn-bridges nahi."
        ),
        "yellow_wait": (
            "Resignation ka mann hai par signals mixed — pehle next role "
            "secure karein, exit terms negotiate karein, fir resign karein. "
            "Impulsive exit avoid karein."
        ),
        "slow_burn": (
            "Resignation eventually hogi par abhi rush nahi — 6-12 "
            "mahine plan karein: skills, finances, family alignment "
            "sab settle karein, fir clean transition karein."
        ),
        "red_avoid": (
            "Abhi resign karna financial + career-trajectory dono ke liye "
            "risk hai — current role mein patience rakhein. Triggering "
            "issues ko HR/internal-transfer se address karein."
        ),
    },
    # ── career_setback ──
    "career_setback": {
        "green_go": (
            "Setback se recovery active phase mein hai — confidence rebuild "
            "karein, network re-activate karein, aur ek targeted next-step "
            "(role, skill, certification) decide karein. 90-180 din mein turnaround possible hai."
        ),
        "yellow_wait": (
            "Recovery slow lekin steady — kaam ki quality par focus, "
            "mental health par dhyaan, aur financial discipline (savings, "
            "minimal expenses) maintain karein. 6-12 mahine ka window hai."
        ),
        "slow_burn": (
            "Setback se ubhrne mein time lagega — professional counselling, "
            "skill-pivot, aur supportive family/friend circle build karein. "
            "Rush karne se decisions galat ho sakte hain."
        ),
        "red_avoid": (
            "Abhi setback ka peak phase hai — financial cuts, emotional "
            "support seek karein, ego-driven moves avoid karein. Saturn / "
            "dasha karmic-restructuring kar raha hai, surrender + patience zaroori hai."
        ),
    },
    # ── career_field_choice ──
    "career_field_choice": {
        "green_go": (
            "Field-choice clarity emerge ho rahi hai — chart Amatyakaraka "
            "+ 10L combo se jo professions match hain, unhi mein 3-6 "
            "mahine deeper exploration karein. Mentor + aptitude-test "
            "dono use karein."
        ),
        "yellow_wait": (
            "Field-choice mein 2-3 options viable hain — har ek mein "
            "shadow-experience (internship/job-shadow) lekar decide karein. "
            "Forced commitment se bachein, exploration period rakhein."
        ),
        "slow_burn": (
            "Field-choice clarity time-sapeksh hai — basic skills + multiple "
            "exposures (volunteer, part-time, courses) se identity slowly "
            "form hogi. 1-2 saal ka exploration window healthy hai."
        ),
        "red_avoid": (
            "Field-choice par confusion ka phase hai — major commitment "
            "(degree, expensive course) abhi defer karein. Counsellor + "
            "aptitude-test + family discussion se foundation banayein."
        ),
    },
    # ── general_career ──
    "general_career": {
        "green_go": (
            "Career trajectory favourable hai — abhi action-mode mein "
            "rahein. Visibility-tasks, networking, skill-stacking par "
            "consistent invest karein. Cosmic momentum aapke saath hai."
        ),
        "yellow_wait": (
            "Career ka phase mixed hai — patience + preparation parallel "
            "rakhein. Major decisions next favourable window ke liye "
            "save karein, abhi consolidation phase hai."
        ),
        "slow_burn": (
            "Career long-term mein build hoga — daily discipline, "
            "consistent effort, aur ego-control hi key hain. Quick wins "
            "expect mat karein, deep skill-roots banayein."
        ),
        "red_avoid": (
            "Currently career stress-heavy phase hai — major moves defer "
            "karein, mental health + financial buffer prioritize karein. "
            "3-6 mahine baad situation re-evaluate karein."
        ),
    },
}


def _strategy_for(bucket: str, verdict: str) -> str:
    """Return pre-baked Hinglish strategy for (bucket, verdict)."""
    bucket_table = _STRATEGY_TABLE.get(bucket) or _STRATEGY_TABLE["general_career"]
    return bucket_table.get(verdict) or bucket_table.get("yellow_wait") or ""


# ─────────────────────────────────────────────────────────────────────────────
# FIELD RECOMMENDATION (which industry / sector suits)
# ─────────────────────────────────────────────────────────────────────────────
def _recommend_fields(intel: dict, kundli: dict, karakas_d: dict) -> dict:
    """Return a ranked list of recommended career fields based on:
      - 10L planet (primary career-house lord)
      - AmK planet (Jaimini soul-career)
      - Strongest planet in 10H (if any)
      - Atmakaraka domain
    """
    planets = kundli.get("planets") or []
    candidates: dict[str, int] = {}

    def _bump(planet: str, weight: int):
        if planet in PLANET_FIELDS:
            for field in PLANET_FIELDS[planet]:
                candidates[field] = candidates.get(field, 0) + weight

    tl = _house_lord(intel, 10)
    if tl:
        _bump(tl, 4)
    amk = (karakas_d or {}).get("AmK")
    if amk:
        _bump(amk, 4)
    ak = (karakas_d or {}).get("AK")
    if ak:
        _bump(ak, 2)

    occ_10 = [p.get("name") for p in planets
              if isinstance(p, dict) and p.get("house") == 10 and p.get("name")]
    for op in occ_10:
        _bump(op, 3)

    # Sort and take top 5
    ranked = sorted(candidates.items(), key=lambda kv: -kv[1])[:5]

    return {
        "top_fields":   [{"field": f, "score": s} for f, s in ranked],
        "drivers":      {"10L": tl, "AmK": amk, "AK": ak, "10H_occupants": occ_10},
    }


# ─────────────────────────────────────────────────────────────────────────────
# BRAND-SAFETY GUARD GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def _brand_safety_warnings(bucket: str, verdict: str, conditional_results: dict) -> list[str]:
    """Generate per-bucket brand-safety bullets that the narrator MUST honour.
    These prevent harmful claims (e.g. guaranteeing govt-exam selection,
    promising business success without execution caveats, telling someone
    to quit job without backup, etc.)."""
    warnings: list[str] = []

    # Universal — these always apply
    warnings.append(
        "Cosmic verdict ek probabilistic guidance hai — final outcome aapke "
        "effort, environment, aur free-will par bhi depend karta hai."
    )
    warnings.append(
        "Hum aapko career-path ya kisi specific company/exam/visa ka "
        "GUARANTEED outcome kabhi nahi denge — yeh unethical hai."
    )

    if bucket == "govt_job":
        warnings.append(
            "Govt-exam selection 100% astrology se predict nahi hoti — hard "
            "work, syllabus coverage, aur consistent practice without exception zaroor karein."
        )
        warnings.append(
            "Multiple attempts ka mental + financial cost realistic rakhein. "
            "Backup career path bhi parallel develop karein."
        )

    if bucket == "resignation":
        warnings.append(
            "Naukri chodne se pehle 60-90 din ka financial buffer aur ideally "
            "next role ka offer letter zaroor secure karein. Impulsive exit "
            "regret ka cause ban sakta hai."
        )
        warnings.append(
            "Notice period clean serve karein, exit-interview professional "
            "rakhein — bridges burn nahi karne hain."
        )

    if bucket == "career_setback":
        warnings.append(
            "Setback ke phase mein professional mental-health support "
            "(therapist/counsellor) lena strength ka sign hai, kamzori nahi. "
            "Family + close friends ko involve karein."
        )
        warnings.append(
            "Drastic financial decisions (loans, investments, large "
            "purchases) abhi defer karein. Stability return hone tak "
            "minimal expense rakhein."
        )

    if verdict == "red_avoid":
        warnings.append(
            "Currently major risk-taking decisions defer karein. Existing "
            "stability protect karna hi pehla priority hai."
        )

    # Cap at 7 (per CLE rule for narrator override)
    return warnings[:7]


# ─────────────────────────────────────────────────────────────────────────────
# ASSESS_CAREER — main orchestrator
# ─────────────────────────────────────────────────────────────────────────────
def assess_career(kundli: dict,
                  intel: dict,
                  kp: Optional[dict] = None,
                  birth: Optional[dict] = None,
                  question: str = "",
                  boss_kundli: Optional[dict] = None,
                  partner_kundli: Optional[dict] = None,
                  pre_classified_bucket: str | None = None) -> dict:
    """Full deterministic career verdict.

    Returns dict with:
      bucket            — one of 12 question buckets
      tense             — future / present / general
      verdict           — green_go / yellow_wait / slow_burn / red_avoid
      confidence        — 0..100 (cross-system agreement)
      score             — total weighted score across all layers
      strategy          — pre-baked Hinglish strategy text
      timing_window     — {start, end, lords, source}
      remedy            — dict with mantra/donation/day
      field_recommendations — ranked list
      brand_safety_warnings — list of bullets narrator MUST honour
      layers            — full layer-by-layer breakdown
      conditionals      — fired conditional details
      synastry          — boss/partner overlay results
      reasons           — flat list of all "why" strings (for transparency)
    """

    bucket = classify_career_question(question, pre_classified_bucket)
    tense  = detect_question_tense(question)

    # Lagna context
    asc = kundli.get("ascendant") or {}
    lagna_sign = asc.get("sign") if isinstance(asc, dict) else asc
    lagna_idx = _sign_idx(lagna_sign or "")
    lagna_lon = None
    if isinstance(asc, dict):
        for k in ("longitude", "lon", "fullDegree"):
            v = asc.get(k)
            if isinstance(v, (int, float)):
                lagna_lon = float(v)
                break

    moon_sign = kundli.get("moonSign") or kundli.get("moon_sign")
    moon_sign_idx = _sign_idx(moon_sign or "") if moon_sign else None

    # ── Compute helper modules
    sb         = _maybe_shadbala(kundli, lagna_idx)
    av         = _maybe_ashtakavarga(kundli, lagna_idx)
    bb         = _maybe_bhava_bala(intel, sb)
    karakas_d  = _maybe_karakas(kundli)
    jaimini_d  = _maybe_jaimini(kundli)
    yogas_d    = _maybe_varga_yogas(kundli, lagna_lon)
    yogini_d   = _maybe_yogini_dasha(kundli, birth)
    jup_t      = _maybe_jupiter_transit(lagna_idx, moon_sign_idx) if lagna_idx >= 0 else {}
    saturn_t   = _maybe_saturn_transit_career(lagna_idx) if lagna_idx >= 0 else {}

    # Attach lagna_sign_idx into AV for layer use
    if isinstance(av, dict):
        av["lagna_sign_idx"] = lagna_idx

    # ── Run all 35 layers
    L: dict[str, dict] = {}
    L["L1_tenth_house"]      = _layer_tenth_house(intel, kundli)
    L["L2_sun_karaka"]       = _layer_sun_karaka(intel, kundli)
    L["L3_saturn_karaka"]    = _layer_saturn_karaka(intel, kundli)
    L["L4_mercury_karaka"]   = _layer_mercury_karaka(intel, kundli)
    L["L5_mars_karaka"]      = _layer_mars_karaka(intel, kundli)
    L["L6_jupiter_karaka"]   = _layer_jupiter_karaka(intel, kundli)
    L["L7_venus_karaka"]     = _layer_venus_karaka(intel, kundli)
    L["L8_moon_karaka"]      = _layer_moon_karaka(intel, kundli)
    L["L9_sixth_house"]      = _layer_sixth_house(intel, kundli)
    L["L10_second_house"]    = _layer_second_house(intel, kundli)
    L["L11_eleventh_house"]  = _layer_eleventh_house(intel, kundli)
    L["L12_seventh_house"]   = _layer_seventh_house(intel, kundli)
    L["L13_ninth_house"]     = _layer_ninth_house(intel, kundli)
    L["L14_fifth_house"]     = _layer_fifth_house(intel, kundli)
    L["L15_lagna_lord"]      = _layer_lagna_lord(intel, kundli)
    L["L16_amatyakaraka"]    = _layer_amatyakaraka(karakas_d, intel, kundli)
    L["L17_atmakaraka"]      = _layer_atmakaraka_career(karakas_d, intel, kundli)
    L["L18_d9_overlay"]      = _layer_d9_overlay(kundli, intel, karakas_d)
    L["L19_d10_overlay"]     = _layer_d10_overlay(kundli, intel, karakas_d)
    L["L20_d24_overlay"]     = _layer_d24_overlay(kundli, intel)
    L["L22_kp_csl"]          = _layer_kp_csl_career(kp or {})
    L["L23_kp_rp"]           = _layer_kp_ruling_planets(kp or {})
    L["L24_ashtakavarga"]    = _layer_ashtakavarga_career(av)
    L["L25_shadbala"]        = _layer_shadbala_career(sb, intel)
    L["L26_bhava_bala"]      = _layer_bhava_bala_career(bb)
    L["L27_char_karakas"]    = _layer_char_karakas_career(karakas_d, intel, kundli)
    L["L28_raj_yogas"]       = _layer_raj_yogas(yogas_d, intel, kundli)
    L["L29_dhana_yogas"]     = _layer_dhana_yogas(intel, kundli)
    L["L30_mahapurusha"]     = _layer_mahapurusha_yogas(yogas_d, intel, kundli)
    L["L31_anti_yogas"]      = _layer_anti_yogas(intel, kundli)
    L["L32_sade_sati"]       = _layer_sade_sati_eclipse(intel, kundli)
    L["L34_wealth_triad"]    = _layer_wealth_triad(intel, kundli)

    # ── Trigger layers
    T: dict[str, dict] = {}
    T["T1_vimshottari"]     = _trigger_vimshottari(kundli, intel, karakas_d)
    T["T2_saturn_transit"]  = _trigger_saturn_transit(saturn_t, intel)
    T["T3_jupiter_yogini"]  = _trigger_jupiter_yogini(jup_t, yogini_d, karakas_d, intel)

    # ── Modifiers
    M: dict[str, dict] = {}
    M["M1_combust"]          = _modifier_combust(intel, kundli)
    M["M2_retrograde"]       = _modifier_retrograde(intel, kundli)
    M["M3_malefic_aspects"]  = _modifier_malefic_aspects(intel, kundli, karakas_d)
    M["M4_lagnesh"]          = _modifier_lagnesh(intel)
    M["M5_sade_sati"]        = _modifier_sade_sati(intel, kundli)
    M["M6_jupiter_transit"]  = _modifier_jupiter_transit(jup_t)
    M["M8_rahu_ketu_axis"]   = _modifier_rahu_ketu_axis(kundli)

    # ── Conditionals (fire only when relevant). Each receives `kp` so its
    # bucket-tuned _kp_bucket_assist call can fire on the right cusps.
    conditionals: dict[str, dict] = {}
    if bucket == "govt_job" or _planet_dignity(intel, "Sun") in ("exalted", "own-sign", "moolatrikona"):
        conditionals["C1_govt_job"] = _conditional_govt_job(intel, kundli, karakas_d, kp)
    if bucket == "promotion":
        conditionals["C4_promotion_window"] = _conditional_promotion_window(
            T["T1_vimshottari"], intel, jup_t, saturn_t, kp
        )
    if bucket == "career_setback":
        conditionals["C5_setback_recovery"] = _conditional_setback_recovery(
            T["T1_vimshottari"], jup_t, intel, kp
        )
    if bucket == "transfer":
        conditionals["C7_transfer"] = _conditional_transfer(intel, kundli, saturn_t, kp)
    if bucket == "resignation":
        conditionals["C8_resignation"] = _conditional_resignation(
            T["T1_vimshottari"], intel, kp
        )
    # ── Synastry (only if other-kundli provided)
    synastry: dict[str, dict] = {}
    if boss_kundli:
        synastry["boss"] = _synastry_career(kundli, intel, boss_kundli, role="boss")
    if partner_kundli:
        synastry["partner"] = _synastry_career(kundli, intel, partner_kundli, role="partner")

    # ── Aggregate score
    layer_score = sum((L[k].get("score") or 0) for k in L)
    trigger_score = sum((T[k].get("score") or 0) for k in T)
    modifier_delta = sum((M[k].get("delta") or 0) for k in M)

    cond_bonus = 0
    for ck, cv in conditionals.items():
        if isinstance(cv, dict):
            cv_score = (cv.get("score") or 0)
            # C1 side-fires on Sun-strong charts even when bucket != "govt_job"
            # (intentional cross-cut, since Sun = career karaka). Phase 2.8.32 added
            # 6 govt-specific rules pushing C1 max from ~22 to ~45, so its full score
            # would distort promotion/etc verdicts on Sun-strong charts.
            # Dampen C1 to 35% when it's a side-fire; full weight only when the user
            # actually asked about govt_job. Internal C1 score + promise_level label
            # stay honest for the dedicated narrator block.
            if ck == "C1_govt_job" and bucket != "govt_job":
                cv_score = round(cv_score * 0.35)
            cond_bonus += cv_score

    syn_bonus = sum((synastry[r].get("score") or 0) for r in synastry)

    total_score = layer_score + trigger_score + modifier_delta + cond_bonus + syn_bonus

    # ── Map score → verdict
    if total_score >= 50:
        verdict = "green_go"
    elif total_score >= 25:
        verdict = "yellow_wait"
    elif total_score >= 5:
        verdict = "slow_burn"
    else:
        verdict = "red_avoid"

    # Confidence — based on cross-system agreement
    # Count how many of {natal-strong, KP-CSL-favourable, T1-active, D10-strong}
    # are positive.
    confidence_signals = 0
    confidence_total = 4
    if layer_score >= 30:
        confidence_signals += 1
    csl_score = L["L22_kp_csl"].get("score") or 0
    if csl_score >= 5:
        confidence_signals += 1
    t1_score = T["T1_vimshottari"].get("score") or 0
    if t1_score >= 5:
        confidence_signals += 1
    d10_score = L["L19_d10_overlay"].get("score") or 0
    if d10_score >= 4:
        confidence_signals += 1

    confidence = int((confidence_signals / confidence_total) * 100)
    # Tense modulation: PRESENT questions need more current-trigger evidence
    if tense == "present" and trigger_score < 5:
        confidence = max(40, confidence - 15)

    # ── Pick weakest career planet for remedy
    career_planet_dignity_pts = {}
    for p in ("Sun", "Saturn", "Mercury", "Mars", "Jupiter", "Venus", "Moon"):
        d = _planet_dignity(intel, p)
        if d:
            career_planet_dignity_pts[p] = DIGNITY_PTS.get(d, 0)
    tl = _house_lord(intel, 10)
    if tl and tl not in career_planet_dignity_pts:
        d = _planet_dignity(intel, tl)
        if d:
            career_planet_dignity_pts[tl] = DIGNITY_PTS.get(d, 0)
    weakest = min(career_planet_dignity_pts, key=career_planet_dignity_pts.get) if career_planet_dignity_pts else None

    remedy = _select_career_remedy(intel, kundli, karakas_d, weakest)

    # ── Strategy
    strategy = _strategy_for(bucket, verdict)

    # ── Timing window
    cur = T["T1_vimshottari"].get("current_window") or {}
    nxt = T["T1_vimshottari"].get("next_career_window") or {}
    timing_window = {
        "current": {
            "lords": T["T1_vimshottari"].get("current_lords"),
            "start": cur.get("start"),
            "end":   cur.get("end"),
        },
        "next_career": nxt,
        "saturn_transit": saturn_t,
        "jupiter_active": (jup_t or {}).get("active_window"),
    }

    # ── Field recommendations
    field_rec = _recommend_fields(intel, kundli, karakas_d)

    # ── Brand-safety warnings
    warnings = _brand_safety_warnings(bucket, verdict, conditionals)

    # ── Aggregate reasons
    reasons: list[str] = []
    for k in L:
        for w in (L[k].get("why") or []):
            reasons.append(w)
    for k in T:
        for w in (T[k].get("why") or []):
            reasons.append(w)
    for k in M:
        for w in (M[k].get("why") or []):
            reasons.append(w)
    for k in conditionals:
        for w in (conditionals[k].get("why") or []):
            reasons.append(w)
    for r in synastry:
        for w in (synastry[r].get("why") or []):
            reasons.append(w)

    return {
        "bucket":              bucket,
        "tense":               tense,
        "verdict":             verdict,
        "confidence":          confidence,
        "score":               total_score,
        "score_breakdown": {
            "layer_score":    layer_score,
            "trigger_score":  trigger_score,
            "modifier_delta": modifier_delta,
            "cond_bonus":     cond_bonus,
            "synastry_bonus": syn_bonus,
        },
        "strategy":            strategy,
        "timing_window":       timing_window,
        "remedy":              remedy,
        "field_recommendations": field_rec,
        "brand_safety_warnings": warnings,
        "layers":              L,
        "triggers":            T,
        "modifiers":           M,
        "conditionals":        conditionals,
        "synastry":            synastry,
        "reasons":             reasons,
        "weakest_planet":      weakest,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT HELPERS — verdict block + final answer for AI narrator
# ─────────────────────────────────────────────────────────────────────────────
def _format_window_human(window: dict) -> str:
    """Format a single dasha window for narration."""
    if not window or not isinstance(window, dict):
        return "(window data unavailable)"
    lords = window.get("lords") or window.get("md", "")
    if window.get("ad"):
        lords = f"{window.get('md','?')}/{window.get('ad','?')}"
    s = _ym_to_human(str(window.get("start") or "")[:7])
    e = _ym_to_human(str(window.get("end") or "")[:7])
    if s and e:
        return f"{lords} ({s} → {e})"
    return lords or "(unknown window)"


_VERDICT_HI = {
    "green_go":    "GREEN — Aage badhein",
    "yellow_wait": "YELLOW — Wait & prepare",
    "slow_burn":   "SLOW BURN — Long-term promise, patience zaroori",
    "red_avoid":   "RED — Defer / restructure",
}

_BUCKET_HI = {
    "job_change":          "Naukri Change",
    "promotion":           "Promotion / Salary Hike",
    "govt_job":            "Sarkari Naukri",
    "transfer":            "Transfer / Posting",
    "resignation":         "Naukri Chodna (Resignation)",
    "career_setback":      "Career Setback / Recovery",
    "career_field_choice": "Career Field Choice",
    "general_career":      "General Career Outlook",
}


def format_verdict_for_prompt(v: dict, question: str = "") -> str:
    """Build the LOCKED-FACTS block that the AI narrator MUST embed verbatim
    (no wording changes, no number changes, no verdict changes).

    This is the "prompt-armor" — the AI cannot soften, exaggerate, or
    reinterpret these facts. Brand-safety bullets at the bottom are
    MANDATORY for the narrator to honour."""

    if not isinstance(v, dict):
        return "(career verdict unavailable)"

    bucket = v.get("bucket", "general_career")
    tense  = v.get("tense", "general")
    verdict = v.get("verdict", "yellow_wait")
    score = v.get("score", 0)
    confidence = v.get("confidence", 0)

    bucket_hi = _BUCKET_HI.get(bucket, bucket)
    verdict_hi = _VERDICT_HI.get(verdict, verdict)

    lines = []
    lines.append("════════════════════════════════════════════════════════════")
    lines.append(f"⭐ COSMIC CAREER VERDICT — LOCKED FACTS (do NOT modify)")
    lines.append("════════════════════════════════════════════════════════════")
    lines.append(f"▸ QUESTION TYPE: {bucket_hi}  ({bucket})")
    lines.append(f"▸ QUESTION TENSE: {tense.upper()}")
    lines.append(f"▸ VERDICT: {verdict_hi}")
    lines.append(f"▸ COSMIC SCORE: {score}  |  CONFIDENCE: {confidence}%")
    lines.append("")

    # Score breakdown
    sb = v.get("score_breakdown") or {}
    if sb:
        lines.append("▸ SCORE BREAKDOWN:")
        lines.append(f"   • Natal layers (35): {sb.get('layer_score',0):+d}")
        lines.append(f"   • Trigger layers (3): {sb.get('trigger_score',0):+d}")
        lines.append(f"   • Modifiers (8): {sb.get('modifier_delta',0):+d}")
        lines.append(f"   • Conditionals: {sb.get('cond_bonus',0):+d}")
        if sb.get('synastry_bonus'):
            lines.append(f"   • Synastry: {sb.get('synastry_bonus',0):+d}")
        lines.append("")

    # Top reasons
    reasons = v.get("reasons") or []
    top_reasons = [r for r in reasons if "⭐" in r or "Vargottama" in r or "MANDATORY" in r][:5]
    if not top_reasons:
        top_reasons = reasons[:5]
    if top_reasons:
        lines.append("▸ TOP COSMIC FACTORS:")
        for r in top_reasons:
            lines.append(f"   • {r}")
        lines.append("")

    # Timing window — emit in validator-friendly form (lowercase "window:"
    # + topic keyword + explicit "X Mahadasha / Y Antardasha" wording so
    # the timing_validator (vedic/validator/timing_validator.py) can match
    # both the dasha names and the month-year tokens that the AI cites.
    tw = v.get("timing_window") or {}
    cur = tw.get("current") or {}
    cur_lords = cur.get("lords")
    # Normalise lords (tuple/list/str) → md/ad/pd
    md = ad = pd = ""
    if cur_lords:
        if isinstance(cur_lords, (tuple, list)):
            md = (cur_lords[0] if len(cur_lords) > 0 else "") or ""
            ad = (cur_lords[1] if len(cur_lords) > 1 else "") or ""
            pd = (cur_lords[2] if len(cur_lords) > 2 else "") or ""
        else:
            parts = [p.strip() for p in str(cur_lords).replace("/", "-").split("-") if p.strip()]
            md = parts[0] if len(parts) > 0 else ""
            ad = parts[1] if len(parts) > 1 else ""
            pd = parts[2] if len(parts) > 2 else ""
    # Only emit the engine window line when we ACTUALLY have at least
    # one real dasha lord. This prevents the "(dasha unavailable)"
    # placeholder string from leaking into the system prompt → into the
    # AI's narration. The narrator will then either honestly omit dasha
    # citation or rely on engine-cited Sthira / Chara dashas elsewhere.
    if md or ad:
        cur_s_h = _ym_to_human(str(cur.get("start") or "")[:7])
        cur_e_h = _ym_to_human(str(cur.get("end") or "")[:7])
        dasha_str_parts = []
        if md: dasha_str_parts.append(f"{md} Mahadasha")
        if ad: dasha_str_parts.append(f"{ad} Antardasha")
        if pd: dasha_str_parts.append(f"{pd} Pratyantardasha")
        dasha_str = " / ".join(dasha_str_parts)
        if cur_s_h or cur_e_h:
            lines.append(f"▸ Current Career window: {cur_s_h} → {cur_e_h} — {dasha_str}")
        else:
            lines.append(f"▸ Current Career window: {dasha_str}")
        # Emit alias forms so the timing-validator's regex matches whatever
        # phrasing the narrator chooses ("Saturn dasha", "Saturn MD",
        # "Saturn maha", "Saturn antar", etc.).
        alias_parts = []
        for role, planet, abbr, full in (
            ("MD", md, "MD", "Mahadasha"),
            ("AD", ad, "AD", "Antardasha"),
            ("PD", pd, "PD", "Pratyantardasha"),
        ):
            if not planet:
                continue
            alias_parts.append(
                f"{planet} {full} (also: {planet} {abbr}, {planet} dasha, "
                f"{planet} maha, {planet} antar)"
            )
        if alias_parts:
            lines.append(f"   • Dasha aliases (validator-safe): {' | '.join(alias_parts)}")
    nxt = tw.get("next_career") or {}
    if nxt and nxt.get("ad"):
        s_h = _ym_to_human(str(nxt.get("start") or "")[:7])
        e_h = _ym_to_human(str(nxt.get("end") or "")[:7])
        nxt_md = nxt.get("md") or ""
        nxt_ad = nxt.get("ad") or ""
        nxt_dasha_parts = []
        if nxt_md: nxt_dasha_parts.append(f"{nxt_md} Mahadasha")
        if nxt_ad: nxt_dasha_parts.append(f"{nxt_ad} Antardasha")
        nxt_dasha = " / ".join(nxt_dasha_parts) if nxt_dasha_parts else "(dasha unavailable)"
        lines.append(f"▸ Next Career window: {s_h} → {e_h} — {nxt_dasha}")
        if nxt.get("reason"):
            lines.append(f"   • Reason: {nxt.get('reason')}")
    sat_t = tw.get("saturn_transit") or {}
    if sat_t and (sat_t.get("on_tenth") or sat_t.get("aspecting_tenth")):
        which = "in 10H" if sat_t.get("on_tenth") else "aspecting 10H"
        lines.append(f"▸ SATURN CYCLE: {which} (sign={sat_t.get('saturn_sign')}, h{sat_t.get('saturn_house_from_lagna')} from lagna)")
    jup_act = tw.get("jupiter_active") or {}
    if jup_act and jup_act.get("sign"):
        lines.append(f"▸ JUPITER GRACE WINDOW ACTIVE: {jup_act.get('sign')} until {jup_act.get('end')} (hits {jup_act.get('hits')})")
    lines.append("")

    # Conditionals — verbose for the bucket
    conds = v.get("conditionals") or {}
    if "C1_govt_job" in conds:
        c = conds["C1_govt_job"]
        lines.append(f"▸ GOVT-JOB PROMISE: {c.get('govt_promise_level','?').upper()}")
        for f in (c.get("flags") or [])[:3]:
            lines.append(f"   • {f}")
        lines.append("")
    if "C4_promotion_window" in conds:
        c = conds["C4_promotion_window"]
        lines.append(f"▸ PROMOTION-WINDOW SIGNAL: {c.get('promotion_signal','?')}")
        for w in (c.get("why") or [])[:3]:
            lines.append(f"   • {w}")
        lines.append("")
    if "C5_setback_recovery" in conds:
        c = conds["C5_setback_recovery"]
        lines.append(f"▸ RECOVERY OUTLOOK: {c.get('recovery_outlook','?')}")
        for w in (c.get("why") or [])[:3]:
            lines.append(f"   • {w}")
        lines.append("")

    # Synastry
    syn = v.get("synastry") or {}
    for role, sd in syn.items():
        if sd.get("fired"):
            lines.append(f"▸ {role.upper()} SYNASTRY: score {sd.get('score',0):+d}")
            for w in (sd.get("why") or [])[:3]:
                lines.append(f"   • {w}")
            lines.append("")

    # Field recommendations
    fr = v.get("field_recommendations") or {}
    fields = fr.get("top_fields") or []
    if fields:
        lines.append("▸ RECOMMENDED CAREER FIELDS (top 5, ranked):")
        for f in fields:
            lines.append(f"   • {f.get('field')} (signal {f.get('score')})")
        drv = fr.get("drivers") or {}
        lines.append(f"   ↳ Drivers: 10L={drv.get('10L')}, AmK={drv.get('AmK')}, AK={drv.get('AK')}")
        lines.append("")

    # Strategy (Hinglish action)
    strat = v.get("strategy") or ""
    if strat:
        lines.append("▸ STRATEGY (verbatim — embed in answer):")
        lines.append(f"   {strat}")
        lines.append("")

    # Remedy
    rem = v.get("remedy") or {}
    if rem.get("remedy_text"):
        lines.append(f"▸ REMEDY: {rem.get('remedy_text')}")
        if rem.get("remedy_planet"):
            lines.append(f"   • Planet target: {rem.get('remedy_planet')}")
        lines.append("")

    # Brand-safety guards (MANDATORY)
    warnings = v.get("brand_safety_warnings") or []
    if warnings:
        lines.append("▸ BRAND-SAFETY GUARDS — narrator MUST honour ALL of these:")
        for i, w in enumerate(warnings, 1):
            lines.append(f"   {i}. {w}")
        lines.append("")

    lines.append("════════════════════════════════════════════════════════════")
    lines.append("⛔ NARRATOR RULES:")
    lines.append("   1. Do NOT change verdict, score, confidence, lords, or windows.")
    lines.append("   2. Do NOT promise GUARANTEED outcomes (selection, promotion, profit).")
    lines.append("   3. Frame in TENSE detected above (PRESENT → 'abhi/aaj kal'; FUTURE → 'aage chal kar').")
    lines.append("   4. Use 'Cosmic Intelligence' / 'cosmic signature' — NEVER 'AI/LLM'.")
    lines.append("   5. Embed STRATEGY text verbatim (translate keywords only if needed).")
    lines.append("   6. Honour ALL brand-safety bullets above as caveats.")
    lines.append("   7. Hinglish-first — natural code-mix preferred over pure Hindi or pure English.")
    lines.append("════════════════════════════════════════════════════════════")

    return "\n".join(lines)


def format_final_answer(v: dict, question: str = "") -> str:
    """Build a compact pre-baked Hinglish answer that can be served when the
    AI narrator is unavailable (rare). Mirrors love_engine.format_final_answer."""

    if not isinstance(v, dict):
        return "Cosmic data abhi available nahi hai. Thodi der baad try karein."

    bucket = v.get("bucket", "general_career")
    verdict = v.get("verdict", "yellow_wait")
    bucket_hi = _BUCKET_HI.get(bucket, "Career")
    verdict_hi = _VERDICT_HI.get(verdict, verdict)
    score = v.get("score", 0)
    confidence = v.get("confidence", 0)

    parts: list[str] = []

    parts.append(f"🎯 *Cosmic Career Verdict — {bucket_hi}*")
    parts.append("")
    parts.append(f"Verdict: *{verdict_hi}*  (Score: {score}, Confidence: {confidence}%)")
    parts.append("")

    # Strategy
    strat = v.get("strategy") or ""
    if strat:
        parts.append(f"📋 *Action Plan:*")
        parts.append(strat)
        parts.append("")

    # Timing
    tw = v.get("timing_window") or {}
    nxt = tw.get("next_career") or {}
    if nxt and nxt.get("ad"):
        s_h = _ym_to_human(str(nxt.get("start") or "")[:7])
        e_h = _ym_to_human(str(nxt.get("end") or "")[:7])
        parts.append(f"⏰ *Next Favourable Window:* {nxt.get('md','?')}/{nxt.get('ad','?')} ({s_h} → {e_h})")
        parts.append("")
    sat_t = tw.get("saturn_transit") or {}
    if sat_t and sat_t.get("on_tenth"):
        parts.append(f"🪐 *Saturn Transit:* Currently in your 10H ({sat_t.get('saturn_sign')}) — career restructuring active.")
        parts.append("")

    # Conditionals — bucket-specific
    conds = v.get("conditionals") or {}
    if "C1_govt_job" in conds:
        parts.append(f"🏛 *Govt-Job Promise:* {conds['C1_govt_job'].get('govt_promise_level','?').upper()}")
    if "C4_promotion_window" in conds:
        parts.append(f"📈 *Promotion Signal:* {conds['C4_promotion_window'].get('promotion_signal','?')}")
    if "C5_setback_recovery" in conds:
        parts.append(f"🔄 *Recovery Outlook:* {conds['C5_setback_recovery'].get('recovery_outlook','?')}")

    if any(k in conds for k in ("C1_govt_job","C4_promotion_window","C5_setback_recovery")):
        parts.append("")

    # Field recommendations
    fr = v.get("field_recommendations") or {}
    fields = (fr.get("top_fields") or [])[:3]
    if fields:
        parts.append(f"💼 *Top Recommended Fields:* {', '.join(f.get('field') for f in fields)}")
        parts.append("")

    # Remedy
    rem = v.get("remedy") or {}
    if rem.get("remedy_text"):
        parts.append(f"🕉 *Cosmic Remedy:* {rem.get('remedy_text')}")
        parts.append("")

    # Brand-safety (compressed)
    warnings = (v.get("brand_safety_warnings") or [])[:2]
    if warnings:
        parts.append("⚠️ *Important:*")
        for w in warnings:
            parts.append(f"  • {w}")

    parts.append("")
    parts.append("_Powered by Advanced Cosmic Intelligence_")

    return "\n".join(parts)

