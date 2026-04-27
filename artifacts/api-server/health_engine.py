"""
health_engine.py — Deterministic Health & Vitality verdict engine (Vedic / KP).

Mirror of career_engine.py + stock_engine.py + love_engine.py + marriage_engine.py
architecture (CLE format): pure-Python rule engine that consumes the already-
computed kundli + chart_intelligence + KP outputs and produces a structured
HEALTH verdict BEFORE the AI is invoked. The AI then acts purely as a
NARRATOR that converts this verdict into Hinglish prose — it MUST NOT change
verdict, score, timing window, strategy, or remedy. Brand-safety guards are
HARD STOPS — narrator MUST honour every guard (no death prediction, no
medical-advice replacement, always recommend doctor consult for serious
symptoms, sensitive treatment of mental-health / reproductive / parent-health
buckets).

Inputs:
    kundli  : dict from kundli_engine.calculate_kundli (has planets, dashas,
              currentDasha, ascendant, moonSign, divisionalCharts D6/D9/D30)
    intel   : dict from chart_intelligence.analyze_chart (has dignities,
              house_lords, yogas, mangal_dosh, sade_sati, lagna_sign)
    kp      : dict from kp_engine.calculate_kp (has cusps, planets,
              significations) — for KP cuspal sub-lord cross-check
    birth   : optional dict with at least "gender", "dob" so dasha + transit
              calculations are correct + gender-aware reproductive guidance
    question: raw user text — drives the 12-bucket question classifier
              (chronic_illness / acute_illness / mental_health /
              surgery_timing / recovery_timing / longevity_general /
              injury_accident / addiction / female_reproductive /
              male_reproductive / parent_health / general_wellness).

Output: see assess_health().__doc__

CLE Format Logic Framework (10 standard steps, mirror of career_engine):
    Step 1  — Question Type Detection (12-bucket classifier) + Tense Detector
    Step 2  — 2-Step Verdict Framework (natal_promise + current_trigger → bucket)
    Step 3  — Layer Stacking (25 layers + D9 + D6 + D30 + KP mandatory + Atmakaraka)
    Step 4  — Bucket-Gated Strategy (no contradictions allowed)
    Step 5  — Timing Window (Vimshottari + Saturn/Mars transits + KP)
    Step 6  — Remedy Selection (weakest health planet → mantra/donation/gem)
    Step 7  — Confidence Calibration (cross-system agreement)
    Step 8  — Format-for-Prompt (locked Hinglish verdict block)
    Step 9  — AI Narrator Override (turn-level rules in openai_helper)
    Step 10 — Brand-Safety Guards (medical-advice replacement / death
              prediction / surgery-skip / chronic-cure / addiction-blame /
              reproductive-guarantee / parent-death — STRICT softening)

Layer rubric (canonical CLE table — health-specific):
    A. NATAL PROMISE  (Layers 1-15)
        L1  1st house + Lagna lord (vitality/body)  (weight 14)  ⭐ CORE
        L2  6th house + 6L (disease/recovery)        (weight 16)  ⭐ CORE
        L3  8th house + 8L (chronic/longevity)       (weight 14)  ⭐ CORE
        L4  12th house + 12L (hospital/loss)         (weight 10)
        L5  Sun (heart/eyes/immune karaka)           (weight 10)
        L6  Moon (mind/fluids karaka)                (weight 10)
        L7  Mars (blood/energy/accident karaka)      (weight  8)
        L8  Saturn (chronic/bones/longevity karaka)  (weight  8)
        L9  Jupiter (liver/recovery/hope karaka)     (weight  6)
        L10 Mercury (nervous-system/skin karaka)     (weight  5)
        L11 Venus (kidneys/reproductive karaka)      (weight  5)
        L12 Rahu (allergy/mysterious illness)        (weight  6)
        L13 Ketu (sudden afflictions/surgery)        (weight  6)
        L14 Atmakaraka (Jaimini soul/vitality)       (weight 10)  ⭐ MANDATORY
        L15 Lagna-Bhava cross-aspect                  (weight  4)
    B. DIVISIONAL + KP (Layers 16-19)
        L16 D9 Navamsa overlay (sustained vitality)  (weight 10)  ⭐ MANDATORY
        L17 D6 Shashtiamsa (HEALTH D-chart)          (weight 14)  ⭐ MANDATORY
        L18 D30 Trimsamsa (illness/misfortune)       (weight  8)  ⭐ MANDATORY
        L19 KP cuspal sub-lord 1/6/8/12              (weight 12)  ⭐ MANDATORY
    C. STRENGTH (Layers 20-22)
        L20 Ashtakavarga 1H/6H/8H BAV                 (weight  5)
        L21 Shadbala (lagnesh, Sun, Moon)              (weight  5)
        L22 Bhava Bala (1/6/8)                         (weight  4)
    D. YOGAS (Layers 23-25)
        L23 Arishta yogas (disease yogas)              (weight  6  -)
        L24 Ayushkara yogas (longevity yogas)          (weight  5  +)
        L25 Sade Sati on lagna/6L/8L                   (weight  5  ±)
    E. TRIGGERS — is the natal promise activated NOW?
        T1  Vimshottari MD+AD+PD on health houses     (weight 12)
        T2  Saturn transit on 1/6/8/12                 (weight  7)
        T3  Mars + Rahu/Ketu transit on 1/6/8          (weight  6)
    F. MODIFIERS — 7 modifiers (±points, no own weight)
        M1  Lagnesh / Sun / Moon combust              (±5)
        M2  Lagnesh / 6L / 8L retrograde              (±3)
        M3  Malefic aspects on 1H/6H/8L                (±5)
        M4  Lagnesh strength (overall vitality)        (±3)
        M5  Saturn sade-sati on Moon (mental/health)  (-5)
        M6  Jupiter transit on 1H/5H/9H (recovery)     (+5)
        M7  Rahu-Ketu axis on 1/7 (sudden change)      (±5)
    G. CONDITIONALS (only when question type matches)
        C1  Chronic illness check (8H+6H+Saturn deep)
            — fires for q_type == "chronic_illness"
        C2  Acute illness check (6H + Mars/Sun aspect)
            — fires for q_type == "acute_illness"
        C3  Surgery timing check (8H + Mars/Ketu transit)
            — fires for q_type == "surgery_timing"
        C4  Mental health check (Moon+4H+Mercury affliction)
            — fires for q_type == "mental_health" or "addiction"
        C5  Longevity general (1H BAV + lagnesh + Sun/Moon strength)
            — fires for q_type == "longevity_general"
            — STRICT brand safety: NEVER predict death date / years remaining
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

# Health-relevant houses
HEALTH_HOUSES_PRIMARY = {1, 6, 8}        # body, disease, chronic/longevity
HEALTH_HOUSES_SECONDARY = {3, 11, 12}    # nadi (3), recovery (11), hospital (12)
DUSHTANA = {6, 8, 12}                    # difficult houses for vitality
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}

# Body parts ruled by each planet (for narration, not prediction)
PLANET_BODY = {
    "Sun":     "heart, eyes (right), immune system, vitality",
    "Moon":    "mind, fluids, stomach, breast (in women), eyes (left in men)",
    "Mars":    "blood, muscles, bone marrow, accidents/cuts",
    "Mercury": "nervous system, skin, lungs, speech",
    "Jupiter": "liver, fat, hips, ears",
    "Venus":   "kidneys, reproductive organs, throat, hormones",
    "Saturn":  "bones, joints, teeth, knees, chronic conditions",
    "Rahu":    "mysterious / unexplained ailments, allergies, addictions",
    "Ketu":    "sudden afflictions, surgery scars, infections, viruses",
}

_DAY_HI = {
    "Sunday":    "Ravivar",  "Monday":   "Somvar",   "Tuesday":  "Mangalvar",
    "Wednesday": "Budhvar",  "Thursday": "Guruvar",  "Friday":   "Shukravar",
    "Saturday":  "Shanivar",
}
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
# QUESTION CLASSIFIER — 12 buckets
# ─────────────────────────────────────────────────────────────────────────────
# Ordered most-specific → most-general. First match wins.
_Q_PATTERNS: list[tuple[str, list[str]]] = [
    # ── PARENT HEALTH ── (very specific — must come BEFORE generic illness)
    ("parent_health", [
        r"\b(maa|maa[- ]?ji|mom|mother|mata|mataji|amma|mummy)\b.*\b(tabiyat|health|swasth|swasthya|sehat|bimar|bimari|illness|sick|ill|theek|recovery|operation|surgery|dawai|ilaj|ilaaj)\b",
        r"\b(papa|papa[- ]?ji|dad|father|pita|pitaji|pitra|pita ji|abba|daddy)\b.*\b(tabiyat|health|swasth|swasthya|sehat|bimar|bimari|illness|sick|ill|theek|recovery|operation|surgery|dawai|ilaj|ilaaj)\b",
        r"\b(parent|parents|maa[- ]?baap|mata[- ]?pita|mom dad|mummy papa)\b.*\b(tabiyat|health|swasth|swasthya|sehat|bimar|bimari|illness|sick|ill|theek)\b",
        r"\bmother'?s?\b.*\b(health|illness|surgery|condition)\b",
        r"\bfather'?s?\b.*\b(health|illness|surgery|condition)\b",
        r"\b(माँ|माता|पिता|पापा|मम्मी|डैडी)\b.*\b(तबीयत|स्वास्थ्य|बीमार|बीमारी|इलाज|ऑपरेशन)\b",
    ]),
    # ── ADDICTION ── (very specific — must come BEFORE mental_health)
    ("addiction", [
        r"\b(addict|addiction|addicted)\b",
        r"\b(nasha|nashe|nasheelaa|nasheela|nasheeli)\b",
        r"\b(sharab|sharaab|alcohol|alcoholic|daru|daaru|drinking problem)\b",
        r"\b(cigarette|smoking|smoke|smoker|tambaku|tambakhu|tobacco|gutka|gutkha|paan masala|paan-masala)\b.*\b(chodna|chhodna|chod|chhod|quit|leave|stop|band)\b",
        r"\b(drug|drugs|drugs problem|substance abuse|cocaine|weed|ganja|ganjha|charas|hashish|opium|heroin|brown sugar|chitta)\b",
        r"\b(gambling|jua|juwa|betting addict|porn addict|porn addiction)\b",
        r"\b(rehab|rehabilitation|de[- ]?addiction|deaddiction|withdrawal)\b",
        r"\b(sharab|nasha|cigarette|smoking|drug)\b.*\b(kab|when|chodna|chhodna|chodu|chhodu|quit|stop|band|chodne)\b",
        r"\b(शराब|नशा|सिगरेट|तंबाकू|गुटखा|जुआ)\b",
    ]),
    # ── FEMALE REPRODUCTIVE ── (must come BEFORE mental_health to capture pcod/pcos/period style)
    ("female_reproductive", [
        r"\b(period|periods|menstrual|menstruation|monthly|maasik|masik dharm|maasik dharm)\b",
        r"\b(pcod|pcos|endometriosis|fibroid|fibroids|cyst|ovarian|ovary)\b",
        r"\b(garbh|garbhdharan|garbhdhaaran|conception|conceive|pregnancy|pregnant|maa banna)\b.*\b(kab|when|problem|dikkat|nahi ho|nahi hori|nahi ho rahi|issues|trouble)\b",
        r"\b(infertility|infertile|baanjh|baanjhpan|baanjpan|santaan|santan)\b.*\b(problem|issue|ilaaj|ilaj|treatment|kab)\b",
        r"\b(ivf|iui|surrogacy|fertility treatment)\b",
        r"\b(menopause|rajonivritti)\b",
        r"\b(uterine|uterus|cervical|breast)\b.*\b(health|cancer|tumor|cyst|fibroid|surgery|operation)\b",
        r"\b(gynae|gynaecology|gynecology|gyno|stree rog)\b",
        r"\b(मासिक|गर्भ|गर्भधारण|गर्भावस्था|बांझ|बांझपन|रजोनिवृत्ति)\b",
    ]),
    # ── MALE REPRODUCTIVE ──
    ("male_reproductive", [
        r"\b(prostate|prostatitis|bph)\b",
        r"\b(erectile|impoten|impotent|impotency|napunsak|napunsakta|kamzori|kamjor)\b.*\b(yaun|sex|sexual|reproduction|santaan|santan)\b",
        r"\b(sperm|shukranu|virya|veerya)\b.*\b(count|low|kam|problem|issue|test)\b",
        r"\b(testicular|testicle|hydrocele|varicocele)\b",
        r"\b(male infertility|purush baanjh|santaan baanjh)\b",
        r"\b(शुक्राणु|वीर्य|नपुंसक|नपुंसकता)\b",
    ]),
    # ── MENTAL HEALTH ── (anxiety / depression / stress / sleep)
    ("mental_health", [
        r"\b(depression|depressed|depress)\b",
        r"\b(anxiety|anxious|panic|panic attack)\b",
        r"\b(stress|stressed|tension|tensed|tensn|tnsn|stressful|over[- ]?thinking|overthinking)\b",
        r"\b(mental|manasik|maansik|psychological|psychiatric|psychiatry|mental health)\b",
        r"\b(suicidal|suicide|atmahatya|jaan dena|jaan de|self[- ]?harm|self harm)\b",
        r"\b(insomnia|sleep|nind|neend|so nahi pa|sone mein|sleeping problem|sleep disorder)\b.*\b(problem|issue|nahi|disorder|dikkat)\b",
        r"\b(bipolar|schizophrenia|schizo|ocd|adhd|ptsd)\b",
        r"\b(mood|mood swing|chid[- ]?chidaa|chidchida|irritation|irritable|irritated)\b",
        r"\b(udaasi|udaas|udaasinaata|low feel|down feel|nirashaa|nirasha|hopeless|hope nahi)\b",
        r"\b(focus|concentration|dhyaan|ekagrata)\b.*\b(problem|nahi|kam|issue)\b",
        r"\b(डिप्रेशन|चिंता|तनाव|उदास|आत्महत्या|अनिद्रा)\b",
    ]),
    # ── SURGERY TIMING ──
    ("surgery_timing", [
        r"\b(surgery|operation|operate)\b.*\b(kab|when|timing|date|achchi|achhi|sahi|theek|safe|right|best|auspicious)\b",
        r"\b(operation|surgery)\b.*\b(karaani|karwani|karwana|karaaye|karaye|karwaye|hone)\b",
        r"\b(kab|when)\b.*\b(operation|surgery|operate|knife|scalpel)\b",
        r"\b(elective surgery|planned surgery|cosmetic surgery|knee replacement|hip replacement|cataract|bypass surgery|stent|angioplasty)\b",
        r"\b(c[- ]?section|cesarean|caesarean|delivery surgery)\b.*\b(kab|when|date|timing|safe)\b",
        r"\b(transplant|transplantation|kidney transplant|liver transplant|heart transplant)\b",
        r"\b(ऑपरेशन|सर्जरी)\b.*\b(कब|समय|तारीख)\b",
    ]),
    # ── INJURY / ACCIDENT ──
    ("injury_accident", [
        r"\b(accident|accidental|durghatna|durghatnaa|chot|chote|chotein|injury|injured|injuries)\b",
        r"\b(fracture|fractured|broken bone|tooti|tut)\b.*\b(haddi|bone|leg|arm|hand)\b",
        r"\b(road accident|car accident|bike accident|fall|falling|gir gaya|gir gayi)\b",
        r"\b(burn|burnt|jal gaya|jal gayi|jalna)\b.*\b(injury|skin)\b",
        r"\b(cut|cuts|kat gaya|katne|wound|wounds|ghav)\b",
        r"\b(safe|safety)\b.*\b(travel|drive|driving|commute|journey)\b.*\b(astrology|chart|cosmic)\b",
        r"\b(दुर्घटना|चोट|फ्रैक्चर|घाव)\b",
    ]),
    # ── CHRONIC ILLNESS ──
    ("chronic_illness", [
        r"\b(chronic|long[- ]?term|long term|long lasting|purani|puraani)\b.*\b(disease|illness|condition|bimari|bimaari|rog|problem|tabiyat)\b",
        r"\b(diabetes|sugar|madhumeh|madhumey)\b",
        r"\b(blood pressure|bp|high bp|low bp|hypertension|raktchaap)\b",
        r"\b(thyroid|hypothyroid|hyperthyroid|thairoid)\b",
        r"\b(arthritis|gathiya|joint pain|knee pain|back pain|spinal|spondylitis|spondylosis)\b",
        r"\b(asthma|dama|bronchitis|copd|sinusitis)\b",
        r"\b(cancer|tumor|tumour|cancerous|carcinoma|leukemia|lymphoma)\b",
        r"\b(kidney disease|kidney stone|liver disease|liver problem|fatty liver|jaundice|peelia|peeliya|hepatitis)\b",
        r"\b(heart disease|cardiac|cardio|heart problem|heart attack|chest pain|hriday rog)\b",
        r"\b(autoimmune|lupus|psoriasis|eczema|ms|multiple sclerosis|parkinson|alzheimer|dementia)\b",
        r"\b(lifestyle disease|metabolic syndrome|obesity|motapa|cholesterol)\b",
        r"\b(मधुमेह|रक्तचाप|थायराइड|गठिया|दमा|कैंसर|हृदय रोग|रक्तदाब)\b",
    ]),
    # ── ACUTE ILLNESS ── (sudden, short-term)
    ("acute_illness", [
        r"\b(fever|bukhar|bukhaar|jukaam|jukam|cold|sardi|khansi|cough|sneezing)\b",
        r"\b(flu|viral|virus|infection|sankraman)\b",
        r"\b(diarrhea|loose motion|dast|dasht|vomiting|ulti|nausea)\b",
        r"\b(food poisoning|stomach upset|pet kharab|gas|acidity|amla|amlapitta)\b",
        r"\b(headache|migraine|sir dard|sir mein dard|head pain|sirdard)\b",
        r"\b(skin rash|allergy|allergic|alarji|kharish|khujli)\b",
        r"\b(throat infection|tonsil|sore throat|gala kharab|gala kharaab|gale mein)\b",
        r"\b(typhoid|dengue|malaria|chikungunya|covid|corona)\b",
        r"\b(बुखार|जुकाम|खांसी|दस्त|उल्टी|सर दर्द|एलर्जी)\b",
    ]),
    # ── RECOVERY TIMING ──
    ("recovery_timing", [
        r"\b(recovery|recover|recovering|theek|thik|sahi)\b.*\b(kab|when|timing|hoga|hogi|honge|hoongi|hounga|jaunga|jaungi|jaaunga|jaaungi|jayega|jayegi|jaayega|jaayegi)\b",
        r"\b(kab|when|kab tak)\b.*\b(theek|thik|sahi|healthy|recover|recovery|healed|heal)\b.*\b(hoga|hogi|honge|hounga|hoongi|jaunga|jaungi|jaaunga|jaaungi|jayega|jayegi|jaayega|jaayegi|ho jaunga|ho jaungi|ho jaaunga|ho jaaungi)\b",
        r"\b(kab tak)\b.*\b(theek|thik|sahi|healthy|recover|healed)\b",
        r"\b(jaldi|jaldee|fast)\b.*\b(theek|thik|sahi|recover|recovery|healed)\b",
        r"\b(healing|heal|swasth|swasthya prapti)\b.*\b(time|timing|kab|when|process)\b",
        r"\b(bimari|bimaari|illness|sickness)\b.*\b(kab|when)\b.*\b(jayegi|jayega|katam|khatam|end|over)\b",
        r"\b(post[- ]?surgery|post surgery|after operation|after surgery)\b.*\b(recovery|heal|theek)\b",
        r"\b(कब)\b.*\b(ठीक|स्वस्थ|रिकवरी)\b",
    ]),
    # ── LONGEVITY (very brand-safe — never predict death) ──
    ("longevity_general", [
        r"\b(longevity|aayu|ayu|umar|umr|umra|lifespan|life span|life expectancy)\b",
        r"\b(jeevan|jiwan)\b.*\b(kitna|kitne|aage|baki|bachi|long|lambi|lambaa)\b",
        r"\b(long life|lambi umr|lambi umar|lambi aayu)\b",
        r"\b(ayushman|aayushman|deergh|deergh aayu|deerghaayu|sehat aur umar)\b",
        r"\b(आयु|उम्र|दीर्घायु|जीवनकाल)\b",
    ]),
]


# Sprint-25 Fix-B: AI-Ear-trusted health bucket vocabulary. AI Ear emits
# generic `surgery_recovery`, `reproductive`, `longevity` — we expand to the
# engine's finer-grained legacy names below. `skin_beauty` is treated as
# generic wellness (engine has no dedicated branch yet).
_VALID_HEALTH_BUCKETS = frozenset({
    "chronic_illness", "acute_illness", "mental_health",
    "surgery_timing", "recovery_timing", "surgery_recovery",
    "longevity_general", "longevity",
    "injury_accident", "addiction",
    "female_reproductive", "male_reproductive", "reproductive",
    "parent_health", "skin_beauty", "general_wellness",
})
_HEALTH_BUCKET_ALIASES = {
    "surgery_recovery": "surgery_timing",
    "longevity":        "longevity_general",
    "reproductive":     "female_reproductive",  # default; gender-aware
    "skin_beauty":      "general_wellness",
}


def classify_health_question(text: str,
                             pre_classified_bucket: str | None = None) -> str:
    """Return one of:
      chronic_illness | acute_illness | mental_health | surgery_timing |
      recovery_timing | longevity_general | injury_accident | addiction |
      female_reproductive | male_reproductive | parent_health |
      general_wellness

    Default: "general_wellness" (most generic health fallback).
    Order matters — most specific patterns checked first.

    When `pre_classified_bucket` (Sprint-25 AI-Ear handoff) is in the
    engine's known vocabulary, return it directly — bypassing regex.
    """
    if pre_classified_bucket and pre_classified_bucket in _VALID_HEALTH_BUCKETS:
        return _HEALTH_BUCKET_ALIASES.get(pre_classified_bucket,
                                          pre_classified_bucket)
    if not isinstance(text, str) or not text.strip():
        return "general_wellness"
    s = text.lower().strip()
    for bucket, pats in _Q_PATTERNS:
        for pat in pats:
            try:
                if re.search(pat, s):
                    return bucket
            except re.error:
                continue
    # Fallback: if any health vocabulary present, return general_wellness
    if re.search(r"\b(health|swasthya|swasth|sehat|tabiyat|bimar|bimari|"
                 r"bimaari|beemar|beemari|rog|illness|disease|sick|"
                 r"medicine|dawai|dawaa|treatment|ilaaj|ilaj|cure|heal|"
                 r"hospital|aspataal|doctor|डॉक्टर|"
                 r"स्वास्थ्य|सेहत|बीमार|बीमारी|रोग|दवाई|इलाज)\b", s):
        return "general_wellness"
    return "general_wellness"


# ─────────────────────────────────────────────────────────────────────────────
# TENSE DETECTOR — for tense-aware narration
# ─────────────────────────────────────────────────────────────────────────────
_TENSE_FUTURE_RX = re.compile(
    r"\b(will|shall|going to|gonna|"
    r"karega|karegi|karenge|hoga|hogi|honge|dega|degi|denge|"
    r"milega|milegi|milenge|aayega|aayegi|aayenge|"
    r"banega|banegi|banenge|jayega|jayegi|jayenge|"
    r"rahega|rahegi|rahenge|rehega|rehegi|rehenge|"
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
    if planet_name == "Sun":
        return False
    sun_lon = _planet_lon(planets, "Sun")
    p_lon = _planet_lon(planets, planet_name)
    if sun_lon is None or p_lon is None:
        return False
    diff = abs(sun_lon - p_lon)
    if diff > 180:
        diff = 360 - diff
    return diff < threshold_deg


def _house_lord(intel: dict, house_num: int) -> Optional[str]:
    """Return the lord-planet for a house number from intel.house_lords.
    Tolerates BOTH shapes: dict {"1": "Sun", ...} and the chart_intelligence
    list-of-dict shape [{"house": 1, "lord": "Sun", ...}, ...]."""
    if not isinstance(intel, dict):
        return None
    hl = intel.get("house_lords")
    if isinstance(hl, list):
        for h in hl:
            if isinstance(h, dict) and (h.get("house") == house_num
                                        or h.get("house") == str(house_num)
                                        or str(h.get("house")) == str(house_num)):
                lord = h.get("lord")
                return lord if isinstance(lord, str) else None
        return None
    if isinstance(hl, dict):
        v = hl.get(str(house_num)) or hl.get(house_num)
        return v if isinstance(v, str) else None
    return None


def _planet_dignity(intel: dict, planet_name: str) -> Optional[str]:
    """Return dignity string for a planet from intel.dignities.
    Tolerates BOTH shapes: dict {"Sun": "exalted", ...} and the
    chart_intelligence list-of-dict shape
    [{"planet": "Sun", "status": "exalted"}, ...]."""
    if not isinstance(intel, dict):
        return None
    dgn = intel.get("dignities")
    if isinstance(dgn, list):
        for d in dgn:
            if isinstance(d, dict) and d.get("planet") == planet_name:
                v = d.get("status") or d.get("dignity")
                return v if isinstance(v, str) else None
        return None
    if isinstance(dgn, dict):
        v = dgn.get(planet_name)
        return v if isinstance(v, str) else None
    return None


def _dignity_pts(dignity: Optional[str]) -> int:
    if not dignity:
        return 0
    return DIGNITY_PTS.get(dignity, 0)


def _aspect_houses(planet: str, planet_house: int) -> set[int]:
    """Vedic special aspects — return houses aspected from a planet's house."""
    aspects = {((planet_house - 1 + 6) % 12) + 1}  # 7th aspect (universal)
    if planet == "Mars":
        aspects.add(((planet_house - 1 + 3) % 12) + 1)   # 4th
        aspects.add(((planet_house - 1 + 7) % 12) + 1)   # 8th
    elif planet == "Jupiter":
        aspects.add(((planet_house - 1 + 4) % 12) + 1)   # 5th
        aspects.add(((planet_house - 1 + 8) % 12) + 1)   # 9th
    elif planet == "Saturn":
        aspects.add(((planet_house - 1 + 2) % 12) + 1)   # 3rd
        aspects.add(((planet_house - 1 + 9) % 12) + 1)   # 10th
    elif planet in ("Rahu", "Ketu"):
        aspects.add(((planet_house - 1 + 4) % 12) + 1)   # 5th (some schools)
        aspects.add(((planet_house - 1 + 8) % 12) + 1)   # 9th
    return aspects


def _planets_aspecting_house(planets: list, target_house: int) -> list[str]:
    """Return list of planets aspecting the given target house."""
    aspecting = []
    for p in (planets or []):
        if not isinstance(p, dict):
            continue
        name = p.get("name")
        ph = p.get("house")
        if not name or not isinstance(ph, int):
            continue
        if ph == target_house:
            continue
        if target_house in _aspect_houses(name, ph):
            aspecting.append(name)
    return aspecting


def _dasha_lords(kundli: dict) -> tuple[str, str, str]:
    """Return current (MD, AD, PD) lord names from kundli — same multi-key
    tolerance as career_engine to absorb provider naming variants."""
    cd = kundli.get("currentDasha") or {}
    md = (cd.get("mahadasha") or cd.get("maha") or cd.get("MD") or
          cd.get("md_lord") or cd.get("mahadashaLord") or "").strip()
    ad = (cd.get("antardasha") or cd.get("antar") or cd.get("AD") or
          cd.get("ad_lord") or cd.get("antardashaLord") or "").strip()
    pd = (cd.get("pratyantardasha") or cd.get("pratyantar") or
          cd.get("PD") or cd.get("pd_lord") or
          cd.get("pratyantarLord") or "").strip()

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
    sigs = kp_sigs.get(planet_name) if isinstance(kp_sigs, dict) else None
    if not isinstance(sigs, (list, set)):
        return set()
    return {int(h) for h in sigs if isinstance(h, (int, float))}


# ─────────────────────────────────────────────────────────────────────────────
# LAZY HELPER MODULE LOADERS
# ─────────────────────────────────────────────────────────────────────────────
def _maybe_shadbala(kundli: dict, lagna_idx: int) -> dict:
    try:
        from shadbala import compute_shadbala  # type: ignore
        return compute_shadbala(kundli.get("planets") or [], lagna_idx) or {}
    except Exception:
        return {}


def _maybe_ashtakavarga(kundli: dict, lagna_idx: int) -> dict:
    try:
        from ashtakavarga import compute_ashtakavarga  # type: ignore
        return compute_ashtakavarga(kundli.get("planets") or [], lagna_idx) or {}
    except Exception:
        return {}


def _maybe_bhava_bala(intel: dict, shadbala_d: dict) -> dict:
    try:
        from bhava_bala import compute_bhava_bala  # type: ignore
        return compute_bhava_bala(intel, shadbala_d) or {}
    except Exception:
        return {}


def _maybe_karakas(kundli: dict) -> dict:
    try:
        from karakas import compute_karakas  # type: ignore
        return compute_karakas(kundli.get("planets") or []) or {}
    except Exception:
        return {}


def _maybe_argala(kundli: dict) -> dict:
    try:
        from argala import compute_argala  # type: ignore
        return compute_argala(kundli.get("planets") or []) or {}
    except Exception:
        return {}


def _maybe_varga_yogas(kundli: dict, lagna_lon: Optional[float]) -> dict:
    try:
        from yogas import detect_yogas  # type: ignore
        return detect_yogas(kundli.get("planets") or [], lagna_lon) or {}
    except Exception:
        return {}


def _maybe_jupiter_transit(lagna_sign_idx: int, moon_sign_idx: Optional[int]) -> dict:
    """Live Jupiter transit windows for next 3 years over health-trigger signs.
    For health, support houses from lagna are 1 (body), 5 (purva-punya/recovery),
    9 (dharma/healing). Reuses transit_engine's jupiter_sign_changes.
    """
    try:
        from transit_engine import jupiter_sign_changes  # type: ignore
        SIGNS_LOCAL = SIGNS
        start = datetime.utcnow()
        # Health support sign-offsets from Lagna and Moon
        target_offsets = {0, 4, 8}  # 1st, 5th, 9th (0-indexed: 0, 4, 8)
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
        now_str = start.strftime("%Y-%m-%d")
        active = next((w for w in windows
                       if w["start"] <= now_str <= w["end"]), None)
        return {
            "active_window": active,
            "all_windows":   windows,
        }
    except Exception:
        return {}


def _maybe_saturn_transit_health(lagna_sign_idx: int, moon_sign_idx: Optional[int]) -> dict:
    """Live Saturn position + sade-sati / dhaiya status. Saturn transit on
    1H/6H/8H/12H is the classical health-stress cycle. Saturn over Moon
    (and ±1 sign) = sade-sati; over 4th/8th from Moon = ashtama / kantaka
    shani (mental + chronic stress).
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
        sat_house_from_lagna = ((sat_sign_idx - lagna_sign_idx) % 12) + 1
        # Health-stress houses (1, 6, 8, 12 from lagna)
        health_signs = {(lagna_sign_idx + h - 1) % 12 for h in (0, 5, 7, 11)}
        # 0=lagna, 5=6th, 7=8th, 11=12th (offset from lagna sign)
        on_health_house = sat_sign_idx in health_signs
        # Sade-Sati check (Moon-based)
        sade_sati_phase = None
        if moon_sign_idx is not None and moon_sign_idx >= 0:
            sade_sati_signs = {
                (moon_sign_idx - 1) % 12,  # 12th from Moon
                moon_sign_idx,             # Janma (over Moon)
                (moon_sign_idx + 1) % 12,  # 2nd from Moon
            }
            if sat_sign_idx in sade_sati_signs:
                if sat_sign_idx == (moon_sign_idx - 1) % 12: sade_sati_phase = "rising"
                elif sat_sign_idx == moon_sign_idx:           sade_sati_phase = "peak"
                elif sat_sign_idx == (moon_sign_idx + 1) % 12: sade_sati_phase = "setting"
            # Ashtama Shani (8th from Moon)
            if sat_sign_idx == (moon_sign_idx + 7) % 12:
                sade_sati_phase = "ashtama"
            # Kantaka Shani (4th from Moon)
            if sat_sign_idx == (moon_sign_idx + 3) % 12:
                sade_sati_phase = "kantaka"
        aspects = {
            ((sat_sign_idx + 6) % 12),
            ((sat_sign_idx + 2) % 12),
            ((sat_sign_idx + 9) % 12),
        }
        aspecting_health = bool(aspects & health_signs)
        return {
            "saturn_sign":             SIGNS[sat_sign_idx],
            "saturn_house_from_lagna": sat_house_from_lagna,
            "on_health_house":         on_health_house,
            "aspecting_health":        aspecting_health,
            "sade_sati_phase":         sade_sati_phase,
            "as_of":                   now.strftime("%Y-%m-%d"),
        }
    except Exception:
        return {}


def _maybe_mars_transit_health(lagna_sign_idx: int) -> dict:
    """Mars transit on 1/6/8 = injury/accident/surgery activation."""
    try:
        import swisseph as swe
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        now = datetime.utcnow()
        jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
        pos, _ = swe.calc_ut(jd, swe.MARS, flags)
        mars_lon = float(pos[0]) % 360.0
        mars_sign_idx = int(mars_lon / 30.0) % 12
        mars_house_from_lagna = ((mars_sign_idx - lagna_sign_idx) % 12) + 1
        risk_signs = {(lagna_sign_idx + h - 1) % 12 for h in (0, 5, 7)}  # 1/6/8
        on_risk_house = mars_sign_idx in risk_signs
        # Mars aspects 4, 7, 8 from itself
        aspects = {
            ((mars_sign_idx + 6) % 12),
            ((mars_sign_idx + 3) % 12),
            ((mars_sign_idx + 7) % 12),
        }
        aspecting_risk = bool(aspects & risk_signs)
        return {
            "mars_sign":             SIGNS[mars_sign_idx],
            "mars_house_from_lagna": mars_house_from_lagna,
            "on_risk_house":         on_risk_house,
            "aspecting_risk":        aspecting_risk,
            "as_of":                 now.strftime("%Y-%m-%d"),
        }
    except Exception:
        return {}


def _maybe_rahu_ketu_transit(lagna_sign_idx: int) -> dict:
    """Live Rahu/Ketu axis position. Transit on 1/7 = sudden health change."""
    try:
        import swisseph as swe
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        now = datetime.utcnow()
        jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
        pos, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags)
        rahu_lon = float(pos[0]) % 360.0
        rahu_sign_idx = int(rahu_lon / 30.0) % 12
        ketu_sign_idx = (rahu_sign_idx + 6) % 12
        rahu_house_from_lagna = ((rahu_sign_idx - lagna_sign_idx) % 12) + 1
        ketu_house_from_lagna = ((ketu_sign_idx - lagna_sign_idx) % 12) + 1
        on_axis_1_7 = (rahu_house_from_lagna in (1, 7) or
                       ketu_house_from_lagna in (1, 7))
        on_axis_6_12 = (rahu_house_from_lagna in (6, 12) or
                        ketu_house_from_lagna in (6, 12))
        return {
            "rahu_sign":             SIGNS[rahu_sign_idx],
            "ketu_sign":             SIGNS[ketu_sign_idx],
            "rahu_house_from_lagna": rahu_house_from_lagna,
            "ketu_house_from_lagna": ketu_house_from_lagna,
            "on_axis_1_7":           on_axis_1_7,
            "on_axis_6_12":          on_axis_6_12,
            "as_of":                 now.strftime("%Y-%m-%d"),
        }
    except Exception:
        return {}


def _maybe_divisional_charts(kundli: dict) -> dict:
    """Best-effort fetch of D9/D6/D30 divisional charts from upstream
    kundli payload OR compute on the fly via varga helpers."""
    out = {}
    dc = kundli.get("divisionalCharts") or {}
    for k in ("D9", "D6", "D30"):
        v = dc.get(k)
        if isinstance(v, list):
            out[k] = v
    if not (out.get("D9") and out.get("D6") and out.get("D30")):
        try:
            from divisional_charts import (  # type: ignore
                compute_d9, compute_d30,
            )
            try:
                from divisional_charts import compute_d6  # type: ignore
            except Exception:
                compute_d6 = None  # type: ignore
            planets = kundli.get("planets") or []
            asc = kundli.get("ascendant") or {}
            lagna_lon = None
            for k_ in ("longitude", "lon", "fullDegree"):
                v_ = asc.get(k_) if isinstance(asc, dict) else None
                if isinstance(v_, (int, float)):
                    lagna_lon = float(v_) % 360.0
                    break
            if lagna_lon is not None:
                if "D9" not in out:
                    out["D9"] = compute_d9(planets, lagna_lon)
                if "D30" not in out:
                    out["D30"] = compute_d30(planets, lagna_lon)
                if "D6" not in out and compute_d6 is not None:
                    out["D6"] = compute_d6(planets, lagna_lon)
        except Exception:
            pass
    return out


def _vargottama(planet_name: str, natal_planets: list, varga_planets: list) -> bool:
    """Vargottama = same sign in natal D1 + given divisional chart."""
    n_sign = _planet_sign(natal_planets, planet_name)
    v_sign = _planet_sign(varga_planets, planet_name)
    if not n_sign or not v_sign:
        return False
    return _norm(n_sign) == _norm(v_sign)


# ─────────────────────────────────────────────────────────────────────────────
# A. NATAL PROMISE LAYERS  (L1 – L15)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_lagna_first_house(intel: dict, kundli: dict) -> dict:
    """L1 — 1st house + Lagna lord deep dive (vitality, body strength)."""
    weight = 14
    score = 0
    why = []
    planets = kundli.get("planets") or []

    lagna_lord = _house_lord(intel, 1)
    if not lagna_lord:
        return {"layer": "L1_lagna_first_house", "score": 0,
                "why": ["lagna lord unknown"], "weight": weight}

    ll_house = _planet_house(planets, lagna_lord)
    ll_sign = _planet_sign(planets, lagna_lord)
    ll_dignity = _planet_dignity(intel, lagna_lord)

    # Dignity contribution
    dig_pts = _dignity_pts(ll_dignity)
    score += int(dig_pts * 0.7)
    if ll_dignity:
        why.append(f"Lagnesh ({lagna_lord}) {ll_dignity} → {dig_pts:+d}")

    # Placement contribution
    if ll_house:
        if ll_house in KENDRA or ll_house in TRIKONA:
            score += 6
            why.append(f"Lagnesh in {ll_house}H (kendra/trikona) → +6 vitality")
        elif ll_house in DUSHTANA:
            score -= 6
            why.append(f"Lagnesh in {ll_house}H (dushtana) → −6 vitality stress")
        else:
            score += 2
            why.append(f"Lagnesh in {ll_house}H → +2")

    # Combust / retrograde modifiers (small here, big later)
    if _is_combust(planets, lagna_lord):
        score -= 3
        why.append(f"Lagnesh combust → −3")
    if _is_retrograde(planets, lagna_lord):
        score -= 2
        why.append(f"Lagnesh retrograde → −2")

    # Malefics in 1H = body affliction
    first_house_planets = [p for p in planets
                           if isinstance(p, dict) and p.get("house") == 1]
    malefics_in_1 = [p["name"] for p in first_house_planets
                     if p.get("name") in NATURAL_MALEFICS]
    if malefics_in_1:
        score -= 3 * len(malefics_in_1)
        why.append(f"Malefic(s) {','.join(malefics_in_1)} in 1H → "
                   f"{-3 * len(malefics_in_1):+d} body stress")

    # Benefics in 1H
    benefics_in_1 = [p["name"] for p in first_house_planets
                     if p.get("name") in NATURAL_BENEFICS]
    if benefics_in_1:
        score += 3 * len(benefics_in_1)
        why.append(f"Benefic(s) {','.join(benefics_in_1)} in 1H → "
                   f"{3 * len(benefics_in_1):+d} body support")

    # Aspects on 1H
    aspecting = _planets_aspecting_house(planets, 1)
    bad_aspects = [p for p in aspecting if p in NATURAL_MALEFICS]
    good_aspects = [p for p in aspecting if p in NATURAL_BENEFICS]
    if "Jupiter" in good_aspects:
        score += 4
        why.append("Jupiter aspects 1H → +4 protection")
    if "Saturn" in bad_aspects:
        score -= 3
        why.append("Saturn aspects 1H → −3 chronic stress")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L1_lagna_first_house", "score": score, "weight": weight,
        "why": why,
        "lagnesh": lagna_lord, "lagnesh_house": ll_house,
        "lagnesh_sign": ll_sign, "lagnesh_dignity": ll_dignity,
    }


def _layer_sixth_house(intel: dict, kundli: dict) -> dict:
    """L2 — 6th house + 6L deep dive (disease, recovery, immunity). CORE."""
    weight = 16
    score = 0
    why = []
    planets = kundli.get("planets") or []

    sixth_lord = _house_lord(intel, 6)
    if sixth_lord:
        l6_house = _planet_house(planets, sixth_lord)
        l6_dignity = _planet_dignity(intel, sixth_lord)

        # 6L in dushtana = good for health (cancels disease)
        if l6_house in DUSHTANA:
            score += 6
            why.append(f"6L ({sixth_lord}) in {l6_house}H (dushtana) → +6 "
                       f"(viparit raj yoga — disease neutralised)")
        elif l6_house in KENDRA or l6_house in TRIKONA:
            # 6L in kendra/trikona = mixed; unless it's the 1H itself
            if l6_house == 1:
                score -= 5
                why.append(f"6L ({sixth_lord}) in 1H → −5 "
                           f"(disease attached to body)")
            else:
                score -= 2
                why.append(f"6L ({sixth_lord}) in {l6_house}H → −2 "
                           f"(disease seeking outlet)")
        else:
            score += 1
            why.append(f"6L ({sixth_lord}) in {l6_house}H → +1")

        if l6_dignity:
            dp = _dignity_pts(l6_dignity)
            # Stronger 6L = stronger immunity but also stronger pathology if
            # afflicted. For health, weak 6L is generally PREFERRED.
            score += int(-dp * 0.4)
            why.append(f"6L {l6_dignity} → {int(-dp * 0.4):+d} "
                       f"(weak 6L favours health)")

    # Planets in 6H
    sixth_house_planets = [p for p in planets
                           if isinstance(p, dict) and p.get("house") == 6]
    malefics_in_6 = [p["name"] for p in sixth_house_planets
                     if p.get("name") in NATURAL_MALEFICS]
    benefics_in_6 = [p["name"] for p in sixth_house_planets
                     if p.get("name") in NATURAL_BENEFICS]
    if malefics_in_6:
        score += 4 * len(malefics_in_6)
        why.append(f"Malefic(s) {','.join(malefics_in_6)} in 6H → "
                   f"{4 * len(malefics_in_6):+d} (good for fighting disease)")
    if benefics_in_6:
        score -= 2 * len(benefics_in_6)
        why.append(f"Benefic(s) {','.join(benefics_in_6)} in 6H → "
                   f"{-2 * len(benefics_in_6):+d} (benefic wasted in dushtana)")

    # Aspects on 6H — Jupiter on 6H reduces disease severity
    aspecting = _planets_aspecting_house(planets, 6)
    if "Jupiter" in aspecting:
        score += 3
        why.append("Jupiter aspects 6H → +3 healing/grace")
    if "Saturn" in aspecting and "Jupiter" not in aspecting:
        score -= 3
        why.append("Saturn aspects 6H without Jupiter → −3 chronic disease")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L2_sixth_house", "score": score, "weight": weight,
        "why": why,
        "sixth_lord": sixth_lord,
    }


def _layer_eighth_house(intel: dict, kundli: dict) -> dict:
    """L3 — 8th house + 8L deep dive (chronic illness, longevity, sudden
    afflictions, surgery). CORE."""
    weight = 14
    score = 0
    why = []
    planets = kundli.get("planets") or []

    eighth_lord = _house_lord(intel, 8)
    if eighth_lord:
        l8_house = _planet_house(planets, eighth_lord)
        l8_dignity = _planet_dignity(intel, eighth_lord)

        if l8_house == 8:
            score += 4
            why.append(f"8L ({eighth_lord}) in own (8H) → +4 longevity")
        elif l8_house in DUSHTANA:
            score += 3
            why.append(f"8L ({eighth_lord}) in {l8_house}H (dushtana) → +3 "
                       f"(hidden afflictions contained)")
        elif l8_house in KENDRA:
            score -= 3
            why.append(f"8L ({eighth_lord}) in {l8_house}H (kendra) → −3 "
                       f"(afflictions surface in life)")
        elif l8_house in TRIKONA and l8_house != 1:
            score -= 1
            why.append(f"8L ({eighth_lord}) in {l8_house}H trikona → −1")
        elif l8_house == 1:
            score -= 5
            why.append(f"8L ({eighth_lord}) in 1H → −5 chronic body affliction")

        if l8_dignity:
            score += _dignity_pts(l8_dignity) // 2
            why.append(f"8L {l8_dignity} → {_dignity_pts(l8_dignity)//2:+d}")

    # Saturn in 8H = longevity karaka (positive)
    eighth_house_planets = [p for p in planets
                            if isinstance(p, dict) and p.get("house") == 8]
    saturn_in_8 = any(p.get("name") == "Saturn" for p in eighth_house_planets)
    jupiter_in_8 = any(p.get("name") == "Jupiter" for p in eighth_house_planets)
    if saturn_in_8:
        score += 4
        why.append("Saturn in 8H → +4 longevity karaka in own seat")
    if jupiter_in_8:
        score -= 2
        why.append("Jupiter in 8H → −2 (Jupiter wasted in dushtana, mild)")

    # Multiple malefics in 8H = chronic risk
    malefics_in_8 = [p["name"] for p in eighth_house_planets
                     if p.get("name") in NATURAL_MALEFICS]
    if len(malefics_in_8) >= 2:
        score -= 4
        why.append(f"{len(malefics_in_8)} malefics in 8H → −4 chronic risk")

    # Mars/Ketu in 8H = surgery indication (note for narrator, neutral score)
    mars_in_8 = any(p.get("name") == "Mars" for p in eighth_house_planets)
    ketu_in_8 = any(p.get("name") == "Ketu" for p in eighth_house_planets)
    if mars_in_8 or ketu_in_8:
        why.append(f"{'Mars' if mars_in_8 else ''}{' & ' if mars_in_8 and ketu_in_8 else ''}{'Ketu' if ketu_in_8 else ''} in 8H → surgery indication")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L3_eighth_house", "score": score, "weight": weight,
        "why": why,
        "eighth_lord": eighth_lord,
        "saturn_in_8": saturn_in_8,
        "mars_in_8": mars_in_8,
        "ketu_in_8": ketu_in_8,
    }


def _layer_twelfth_house(intel: dict, kundli: dict) -> dict:
    """L4 — 12th house + 12L (hospital, expenses, mental peace, sleep loss)."""
    weight = 10
    score = 0
    why = []
    planets = kundli.get("planets") or []

    twelfth_lord = _house_lord(intel, 12)
    if twelfth_lord:
        l12_house = _planet_house(planets, twelfth_lord)
        l12_dignity = _planet_dignity(intel, twelfth_lord)

        if l12_house in DUSHTANA:
            score += 4
            why.append(f"12L ({twelfth_lord}) in {l12_house}H (dushtana) → +4")
        elif l12_house == 12:
            score += 3
            why.append(f"12L ({twelfth_lord}) in own (12H) → +3")
        elif l12_house == 1:
            score -= 4
            why.append(f"12L ({twelfth_lord}) in 1H → −4 hospitalisation/loss")
        if l12_dignity:
            score += _dignity_pts(l12_dignity) // 3
            why.append(f"12L {l12_dignity}")

    twelfth_house_planets = [p for p in planets
                             if isinstance(p, dict) and p.get("house") == 12]
    malefics_in_12 = [p["name"] for p in twelfth_house_planets
                      if p.get("name") in NATURAL_MALEFICS]
    if len(malefics_in_12) >= 2:
        score -= 3
        why.append(f"{len(malefics_in_12)} malefics in 12H → −3 sleep/peace stress")

    # Jupiter in 12H = moksha-blessing, slight + for peace
    if any(p.get("name") == "Jupiter" for p in twelfth_house_planets):
        score += 2
        why.append("Jupiter in 12H → +2 mental peace / moksha")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L4_twelfth_house", "score": score, "weight": weight,
        "why": why,
        "twelfth_lord": twelfth_lord,
    }


def _layer_sun_karaka(intel: dict, kundli: dict) -> dict:
    """L5 — Sun (heart, eyes-right, immune system, vitality)."""
    weight = 10
    score = 0
    why = []
    planets = kundli.get("planets") or []

    sun_house = _planet_house(planets, "Sun")
    sun_dignity = _planet_dignity(intel, "Sun")
    score += int(_dignity_pts(sun_dignity) * 0.7)
    if sun_dignity:
        why.append(f"Sun {sun_dignity} → {int(_dignity_pts(sun_dignity)*0.7):+d} vitality")

    if sun_house in (1, 5, 9, 10, 11):
        score += 4
        why.append(f"Sun in {sun_house}H → +4 dignity-house")
    elif sun_house in DUSHTANA:
        if sun_house == 6:
            score += 2
            why.append(f"Sun in 6H → +2 disease-fighter")
        elif sun_house == 8:
            score -= 4
            why.append(f"Sun in 8H → −4 vitality leak")
        else:  # 12
            score -= 3
            why.append(f"Sun in 12H → −3 hidden vitality drain")

    # Sun-Saturn conjunction or aspect = chronic stress on heart/bones
    saturn_house = _planet_house(planets, "Saturn")
    if sun_house and saturn_house and sun_house == saturn_house:
        score -= 3
        why.append("Sun-Saturn conjunct → −3 vitality vs duty conflict")

    if _is_combust(planets, "Saturn") or _is_combust(planets, "Mars"):
        # Sun combusting other planets = malefics weakened (good for health)
        pass

    score = max(-weight, min(weight, score))
    return {
        "layer": "L5_sun_karaka", "score": score, "weight": weight,
        "why": why,
        "sun_house": sun_house, "sun_dignity": sun_dignity,
    }


def _layer_moon_karaka(intel: dict, kundli: dict) -> dict:
    """L6 — Moon (mind, fluids, mental peace, mother-link)."""
    weight = 10
    score = 0
    why = []
    planets = kundli.get("planets") or []

    moon_house = _planet_house(planets, "Moon")
    moon_dignity = _planet_dignity(intel, "Moon")
    score += int(_dignity_pts(moon_dignity) * 0.7)
    if moon_dignity:
        why.append(f"Moon {moon_dignity} → {int(_dignity_pts(moon_dignity)*0.7):+d} mind")

    # Moon paksha bala (waxing/waning approximation by lon vs Sun lon)
    sun_lon = _planet_lon(planets, "Sun")
    moon_lon = _planet_lon(planets, "Moon")
    if sun_lon is not None and moon_lon is not None:
        diff = (moon_lon - sun_lon) % 360.0
        # Waxing if 0-180 (post-amavasya to purnima)
        if 90 <= diff <= 270:
            score += 3
            why.append("Moon waxing/full → +3 paksha bala")
        else:
            score -= 3
            why.append("Moon waning/dark → −3 weak paksha bala")

    # Moon-Rahu/Ketu conjunction = mental disturbance
    rahu_house = _planet_house(planets, "Rahu")
    ketu_house = _planet_house(planets, "Ketu")
    if moon_house and (moon_house == rahu_house):
        score -= 4
        why.append("Moon-Rahu conjunct → −4 mental anxiety/paranoia tendency")
    if moon_house and (moon_house == ketu_house):
        score -= 3
        why.append("Moon-Ketu conjunct → −3 mental detachment/loneliness")

    # Moon in dushtana
    if moon_house in DUSHTANA:
        score -= 3
        why.append(f"Moon in {moon_house}H (dushtana) → −3 mind under stress")

    # Lonely Moon (no benefic in 2H/12H from Moon)
    if moon_house:
        # Approximation: any planet 1 house before/after Moon = company
        houses_with_planets = {p.get("house") for p in planets
                               if isinstance(p, dict) and p.get("name") not in ("Sun", "Moon")}
        before = ((moon_house - 2) % 12) + 1
        after = (moon_house % 12) + 1
        if before not in houses_with_planets and after not in houses_with_planets:
            score -= 2
            why.append("Kemadruma yoga (lonely Moon) → −2 isolation tendency")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L6_moon_karaka", "score": score, "weight": weight,
        "why": why,
        "moon_house": moon_house, "moon_dignity": moon_dignity,
    }


def _layer_mars_karaka(intel: dict, kundli: dict) -> dict:
    """L7 — Mars (blood, energy, accidents, surgery, inflammation)."""
    weight = 8
    score = 0
    why = []
    planets = kundli.get("planets") or []

    mars_house = _planet_house(planets, "Mars")
    mars_dignity = _planet_dignity(intel, "Mars")
    # For Mars as health karaka, exalted/own = +; combust/debilitated = blood/anger issues
    score += int(_dignity_pts(mars_dignity) * 0.5)
    if mars_dignity:
        why.append(f"Mars {mars_dignity} → {int(_dignity_pts(mars_dignity)*0.5):+d}")

    # Mars in 1H/4H/7H/8H = manglik / accident-prone
    if mars_house in (1, 4, 7, 8, 12):
        score -= 3
        why.append(f"Mars in {mars_house}H → −3 manglik/inflammation tendency")
    elif mars_house in (3, 6, 11):
        score += 4
        why.append(f"Mars in {mars_house}H → +4 (mars-strong houses)")

    # Mars-Saturn together or aspecting = chronic inflammation, accidents
    saturn_house = _planet_house(planets, "Saturn")
    if mars_house and saturn_house:
        if mars_house == saturn_house:
            score -= 4
            why.append("Mars-Saturn conjunct → −4 accident/chronic-pain risk")
        elif saturn_house in _aspect_houses("Mars", mars_house):
            score -= 3
            why.append("Mars aspects Saturn → −3 frustration/accident tendency")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L7_mars_karaka", "score": score, "weight": weight,
        "why": why,
        "mars_house": mars_house, "mars_dignity": mars_dignity,
    }


def _layer_saturn_karaka(intel: dict, kundli: dict) -> dict:
    """L8 — Saturn (chronic, bones, joints, longevity, restriction)."""
    weight = 8
    score = 0
    why = []
    planets = kundli.get("planets") or []

    saturn_house = _planet_house(planets, "Saturn")
    saturn_dignity = _planet_dignity(intel, "Saturn")
    # Saturn well-placed = longevity karaka (positive); afflicted = chronic
    score += int(_dignity_pts(saturn_dignity) * 0.6)
    if saturn_dignity:
        why.append(f"Saturn {saturn_dignity} → {int(_dignity_pts(saturn_dignity)*0.6):+d}")

    if saturn_house in (3, 6, 11):
        score += 3
        why.append(f"Saturn in {saturn_house}H (upachaya) → +3 longevity karaka")
    elif saturn_house in (1, 4, 7, 8):
        score -= 4
        why.append(f"Saturn in {saturn_house}H → −4 chronic stress / restriction")
    elif saturn_house == 12:
        score -= 2
        why.append(f"Saturn in 12H → −2 sleep / hidden chronic")

    if _is_retrograde(planets, "Saturn"):
        score -= 1
        why.append("Saturn retrograde → −1 karmic-revisit health pattern")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L8_saturn_karaka", "score": score, "weight": weight,
        "why": why,
        "saturn_house": saturn_house, "saturn_dignity": saturn_dignity,
    }


def _layer_jupiter_karaka(intel: dict, kundli: dict) -> dict:
    """L9 — Jupiter (liver, fat, hope, recovery, healing grace)."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    jup_house = _planet_house(planets, "Jupiter")
    jup_dignity = _planet_dignity(intel, "Jupiter")
    score += int(_dignity_pts(jup_dignity) * 0.6)
    if jup_dignity:
        why.append(f"Jupiter {jup_dignity} → {int(_dignity_pts(jup_dignity)*0.6):+d}")

    if jup_house in KENDRA or jup_house in TRIKONA:
        score += 3
        why.append(f"Jupiter in {jup_house}H → +3 grace/healing support")
    elif jup_house in DUSHTANA:
        if jup_house == 6:
            score -= 1
            why.append(f"Jupiter in 6H → −1 (sweet wasted in disease)")
        else:
            score -= 2
            why.append(f"Jupiter in {jup_house}H dushtana → −2")

    # Jupiter aspects 1H = grand protection
    if jup_house and 1 in _aspect_houses("Jupiter", jup_house):
        score += 3
        why.append("Jupiter aspects 1H → +3 body grace")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L9_jupiter_karaka", "score": score, "weight": weight,
        "why": why,
        "jup_house": jup_house, "jup_dignity": jup_dignity,
    }


def _layer_mercury_karaka(intel: dict, kundli: dict) -> dict:
    """L10 — Mercury (nervous system, skin, lungs, speech)."""
    weight = 5
    score = 0
    why = []
    planets = kundli.get("planets") or []

    merc_house = _planet_house(planets, "Mercury")
    merc_dignity = _planet_dignity(intel, "Mercury")
    score += int(_dignity_pts(merc_dignity) * 0.5)
    if merc_dignity:
        why.append(f"Mercury {merc_dignity} → {int(_dignity_pts(merc_dignity)*0.5):+d}")

    if merc_house in (1, 4, 5, 7, 9, 10, 11):
        score += 2
        why.append(f"Mercury in {merc_house}H → +2 nervous-system stable")
    elif merc_house in (6, 8, 12):
        score -= 2
        why.append(f"Mercury in {merc_house}H dushtana → −2 nerve/skin sensitivity")

    if _is_combust(planets, "Mercury"):
        score -= 2
        why.append("Mercury combust → −2 communication/skin stress")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L10_mercury_karaka", "score": score, "weight": weight,
        "why": why,
    }


def _layer_venus_karaka(intel: dict, kundli: dict) -> dict:
    """L11 — Venus (kidneys, reproductive, throat, hormones)."""
    weight = 5
    score = 0
    why = []
    planets = kundli.get("planets") or []

    ven_house = _planet_house(planets, "Venus")
    ven_dignity = _planet_dignity(intel, "Venus")
    score += int(_dignity_pts(ven_dignity) * 0.5)
    if ven_dignity:
        why.append(f"Venus {ven_dignity} → {int(_dignity_pts(ven_dignity)*0.5):+d}")

    if ven_house in (1, 4, 5, 7, 9, 10):
        score += 2
        why.append(f"Venus in {ven_house}H → +2 hormonal balance")
    elif ven_house in (6, 8, 12):
        score -= 2
        why.append(f"Venus in {ven_house}H dushtana → −2 reproductive/kidney stress")

    if _is_combust(planets, "Venus"):
        score -= 2
        why.append("Venus combust → −2 hormonal heat")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L11_venus_karaka", "score": score, "weight": weight,
        "why": why,
    }


def _layer_rahu_karaka(intel: dict, kundli: dict) -> dict:
    """L12 — Rahu (allergies, mysterious illnesses, addictions)."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    rahu_house = _planet_house(planets, "Rahu")
    if rahu_house in (3, 6, 10, 11):
        score += 3
        why.append(f"Rahu in {rahu_house}H → +3 (Rahu thrives in upachaya)")
    elif rahu_house in (1, 4, 5, 7, 8, 9, 12):
        score -= 3
        why.append(f"Rahu in {rahu_house}H → −3 mysterious/allergy/addiction risk")

    # Rahu with Sun/Moon = mental/eclipse afflictions
    sun_house = _planet_house(planets, "Sun")
    moon_house = _planet_house(planets, "Moon")
    if rahu_house and rahu_house == sun_house:
        score -= 3
        why.append("Rahu-Sun → −3 (solar eclipse — vitality + immunity afflict)")
    if rahu_house and rahu_house == moon_house:
        score -= 4
        why.append("Rahu-Moon → −4 (lunar eclipse — mental + addiction risk)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L12_rahu_karaka", "score": score, "weight": weight,
        "why": why,
        "rahu_house": rahu_house,
    }


def _layer_ketu_karaka(intel: dict, kundli: dict) -> dict:
    """L13 — Ketu (sudden afflictions, surgery, viral, infections, mokshakaraka)."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    ketu_house = _planet_house(planets, "Ketu")
    if ketu_house in (3, 9, 12):
        score += 2
        why.append(f"Ketu in {ketu_house}H → +2 (mokshakaraka well-placed)")
    elif ketu_house in (1, 6, 8):
        score -= 3
        why.append(f"Ketu in {ketu_house}H → −3 sudden affliction / surgery indication")

    # Ketu-Mars conjunction = surgery / cuts
    mars_house = _planet_house(planets, "Mars")
    if ketu_house and ketu_house == mars_house:
        score -= 3
        why.append("Ketu-Mars conjunct → −3 surgery / accident karma")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L13_ketu_karaka", "score": score, "weight": weight,
        "why": why,
        "ketu_house": ketu_house,
    }


def _layer_atmakaraka_health(karakas_d: dict, intel: dict, kundli: dict) -> dict:
    """L14 — Atmakaraka (Jaimini soul karaka). MANDATORY.

    Atmakaraka = highest-degree planet in chart, represents the soul/self.
    Strong AK = strong vitality at the soul level. Weak/afflicted AK =
    soul-level vitality drag (chronic, karmic patterns)."""
    weight = 10
    score = 0
    why = []
    if not karakas_d:
        return {"layer": "L14_atmakaraka", "score": 0,
                "why": ["karakas unavailable"], "weight": weight}

    ak = karakas_d.get("AK") or karakas_d.get("Atmakaraka") or {}
    if isinstance(ak, dict):
        ak_planet = ak.get("planet") or ak.get("name")
    else:
        ak_planet = ak  # might be a plain string
    if not ak_planet:
        return {"layer": "L14_atmakaraka", "score": 0,
                "why": ["AK not identified"], "weight": weight}

    ak_house = _planet_house(kundli.get("planets") or [], ak_planet)
    ak_dignity = _planet_dignity(intel, ak_planet)
    score += _dignity_pts(ak_dignity)
    if ak_dignity:
        why.append(f"AK ({ak_planet}) {ak_dignity} → {_dignity_pts(ak_dignity):+d}")

    if ak_house in (1, 4, 5, 7, 9, 10):
        score += 4
        why.append(f"AK in {ak_house}H (kendra/trikona) → +4 soul-vitality")
    elif ak_house in DUSHTANA:
        score -= 4
        why.append(f"AK in {ak_house}H (dushtana) → −4 soul-vitality drag")

    # AK in 8H = mokshakaraka in mokshasthana → spiritually positive
    # but health-wise = chronic / hidden
    if ak_house == 8:
        why.append("AK in 8H = soul-level karmic pattern (chronic tendency)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L14_atmakaraka", "score": score, "weight": weight,
        "why": why,
        "ak_planet": ak_planet, "ak_house": ak_house,
    }


def _layer_lagna_bhava_aspect(intel: dict, kundli: dict) -> dict:
    """L15 — Lagna-Bhava cross-aspect: how planets in 1/6/8 cross-aspect each
    other (mutual = strong karmic pattern)."""
    weight = 4
    score = 0
    why = []
    planets = kundli.get("planets") or []

    pl_in_1 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 1
               and p.get("name") in (NATURAL_BENEFICS | NATURAL_MALEFICS)]
    pl_in_6 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 6
               and p.get("name") in (NATURAL_BENEFICS | NATURAL_MALEFICS)]
    pl_in_8 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 8
               and p.get("name") in (NATURAL_BENEFICS | NATURAL_MALEFICS)]

    # 1H ↔ 7H universal aspect
    pl_in_7 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 7]
    cross_1_7 = bool(pl_in_1) and bool(pl_in_7)
    if cross_1_7 and any(n in NATURAL_MALEFICS for n in pl_in_7):
        score -= 2
        why.append("Malefic in 7H aspects 1H → −2 partnership-stress impacts body")

    # 6H ↔ 12H axis
    pl_in_12 = [p["name"] for p in planets
                if isinstance(p, dict) and p.get("house") == 12]
    if pl_in_6 and pl_in_12:
        if any(n in NATURAL_MALEFICS for n in pl_in_6) and \
           any(n in NATURAL_MALEFICS for n in pl_in_12):
            score -= 2
            why.append("Malefics on 6/12 axis → −2 chronic disease + hospital")

    # 8H aspect on 1H (8H → 7th aspect = 2H, not 1H universally; only Mars/Sat do)
    if pl_in_8:
        for nm in pl_in_8:
            if nm in ("Mars", "Saturn"):
                # Mars 4th aspect from 8 = 11; Saturn 3rd from 8 = 10; not 1H
                # But Mars 8th aspect from 8 = 3; not 1H either. Skip.
                pass

    if not why:
        why.append("No major lagna-bhava cross-aspect")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L15_lagna_bhava_aspect", "score": score, "weight": weight,
        "why": why,
    }


# ─────────────────────────────────────────────────────────────────────────────
# B. DIVISIONAL + KP LAYERS  (L16 – L19)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_d9_overlay(kundli: dict, intel: dict, karakas_d: dict) -> dict:
    """L16 — D9 Navamsa overlay. Sustained vitality cross-check.
    Lagnesh + AK in D9: vargottama = great strength; D9-debilitated = early
    natal promise weakens over time."""
    weight = 10
    score = 0
    why = []
    dc = _maybe_divisional_charts(kundli)
    d9 = dc.get("D9") or []
    if not d9:
        return {"layer": "L16_d9_overlay", "score": 0,
                "why": ["D9 unavailable"], "weight": weight}

    natal_planets = kundli.get("planets") or []
    lagnesh = _house_lord(intel, 1)

    # Lagnesh vargottama
    if lagnesh and _vargottama(lagnesh, natal_planets, d9):
        score += 5
        why.append(f"Lagnesh ({lagnesh}) vargottama in D9 → +5 sustained vitality")

    # Lagnesh in D9 — sign quality
    d9_lagnesh_sign = _planet_sign(d9, lagnesh) if lagnesh else None
    if d9_lagnesh_sign:
        # Approx: own/exalted via SIGN_LORDS; we mark friend-quality as +1
        if SIGN_LORDS.get(_norm(d9_lagnesh_sign)) == lagnesh:
            score += 3
            why.append(f"Lagnesh in own sign in D9 → +3")

    # AK vargottama
    ak = karakas_d.get("AK") or karakas_d.get("Atmakaraka") or {}
    ak_planet = ak.get("planet") if isinstance(ak, dict) else ak
    if ak_planet and _vargottama(ak_planet, natal_planets, d9):
        score += 4
        why.append(f"AK ({ak_planet}) vargottama in D9 → +4")

    # Sun & Moon in D9 dushtana houses (from D9 lagna)
    # Approximation: just check sign-lord-quality of Sun/Moon in D9
    for pl in ("Sun", "Moon"):
        d9_sign = _planet_sign(d9, pl)
        if d9_sign:
            ldn = SIGN_LORDS.get(_norm(d9_sign))
            if pl == "Sun" and ldn in NATURAL_MALEFICS and ldn != "Sun":
                score -= 2
                why.append(f"{pl} in D9 sign of {ldn} (malefic) → −2")
            elif pl == "Moon" and ldn in NATURAL_MALEFICS and ldn not in ("Moon",):
                score -= 2
                why.append(f"{pl} in D9 sign of {ldn} (malefic) → −2")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L16_d9_overlay", "score": score, "weight": weight,
        "why": why,
    }


def _layer_d6_overlay(kundli: dict, intel: dict) -> dict:
    """L17 — D6 Shashtiamsa overlay. THE health D-chart. MANDATORY.

    D6 specifically signifies disease, debt, enemies. Lagnesh + 6L + Saturn in
    D6 sign analysis. If lagnesh is debilitated/dushtana in D6 = chronic
    health pattern at finer karmic level."""
    weight = 14
    score = 0
    why = []
    dc = _maybe_divisional_charts(kundli)
    d6 = dc.get("D6") or []
    if not d6:
        return {"layer": "L17_d6_overlay", "score": 0,
                "why": ["D6 unavailable"], "weight": weight}

    lagnesh = _house_lord(intel, 1)
    sixth_lord = _house_lord(intel, 6)

    # Lagnesh in D6
    if lagnesh:
        d6_l_sign = _planet_sign(d6, lagnesh)
        if d6_l_sign:
            ldn = SIGN_LORDS.get(_norm(d6_l_sign))
            if ldn == lagnesh:
                score += 5
                why.append(f"D6: Lagnesh ({lagnesh}) in own sign → +5 disease-resilience")
            elif ldn in NATURAL_BENEFICS:
                score += 2
                why.append(f"D6: Lagnesh in benefic sign of {ldn} → +2")
            elif ldn in NATURAL_MALEFICS and ldn != lagnesh:
                score -= 4
                why.append(f"D6: Lagnesh in malefic sign of {ldn} → −4 disease pattern")

    # 6L in D6 — weak 6L in D6 = good (disease neutralised)
    if sixth_lord:
        d6_6l_sign = _planet_sign(d6, sixth_lord)
        if d6_6l_sign:
            ldn = SIGN_LORDS.get(_norm(d6_6l_sign))
            if ldn in NATURAL_BENEFICS:
                score -= 2
                why.append(f"D6: 6L ({sixth_lord}) in benefic sign → −2 (disease empowered)")
            elif ldn in NATURAL_MALEFICS:
                score += 3
                why.append(f"D6: 6L ({sixth_lord}) in malefic sign → +3 (disease weakened)")

    # Natural malefics in D6 — count
    natal_planets = kundli.get("planets") or []
    for mp in ("Saturn", "Mars", "Rahu", "Ketu"):
        if _vargottama(mp, natal_planets, d6):
            score -= 2
            why.append(f"D6: {mp} vargottama → −2 (chronic karmic pattern)")

    # Jupiter strong in D6 = healing grace
    if _vargottama("Jupiter", natal_planets, d6):
        score += 4
        why.append("D6: Jupiter vargottama → +4 healing grace karmic")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L17_d6_overlay", "score": score, "weight": weight,
        "why": why,
    }


def _layer_d30_overlay(kundli: dict, intel: dict) -> dict:
    """L18 — D30 Trimsamsa overlay. Misfortune/illness D-chart. MANDATORY."""
    weight = 8
    score = 0
    why = []
    dc = _maybe_divisional_charts(kundli)
    d30 = dc.get("D30") or []
    if not d30:
        return {"layer": "L18_d30_overlay", "score": 0,
                "why": ["D30 unavailable"], "weight": weight}

    natal_planets = kundli.get("planets") or []
    lagnesh = _house_lord(intel, 1)

    if lagnesh and _vargottama(lagnesh, natal_planets, d30):
        score += 4
        why.append(f"D30: Lagnesh ({lagnesh}) vargottama → +4 misfortune-resistance")

    # Saturn / Mars in D30 strong = chronic-misfortune pattern
    for mp in ("Saturn", "Mars"):
        d30_sign = _planet_sign(d30, mp)
        if d30_sign:
            ldn = SIGN_LORDS.get(_norm(d30_sign))
            if ldn == mp:
                score -= 3
                why.append(f"D30: {mp} in own sign → −3 chronic misfortune pattern")

    # Jupiter / Venus in D30 in benefic sign = grace
    for bp in ("Jupiter", "Venus"):
        d30_sign = _planet_sign(d30, bp)
        if d30_sign:
            ldn = SIGN_LORDS.get(_norm(d30_sign))
            if ldn in NATURAL_BENEFICS:
                score += 2
                why.append(f"D30: {bp} in benefic sign → +2 grace")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L18_d30_overlay", "score": score, "weight": weight,
        "why": why,
    }


def _layer_kp_csl_health(kp: dict) -> dict:
    """L19 — KP cuspal sub-lord 1/6/8/12. MANDATORY.

    KP rule for health:
      - 1H CSL signifying 1/5/9/10/11 → strong vitality
      - 1H CSL signifying 6/8/12 → vitality at risk
      - 6H CSL signifying 1/5/11 → recovery/cure flowing
      - 6H CSL signifying 6/8/12 → disease persists
      - 8H CSL signifying 5/9/11 → longevity boost
      - 8H CSL signifying 6/8/12 → longevity stress
      - 12H CSL signifying 6/8/12 → hospitalisation-prone
    """
    weight = 12
    score = 0
    why = []
    if not kp:
        return {"layer": "L19_kp_csl_health", "score": 0,
                "why": ["KP unavailable"], "weight": weight}

    cusps = kp.get("cusps") or []
    sigs = kp.get("significations") or {}

    def _csl_for(house_num: int) -> Optional[str]:
        for c in cusps:
            if isinstance(c, dict) and c.get("house") == house_num:
                return c.get("subLord") or c.get("sub_lord") or c.get("sl")
        return None

    csl_1 = _csl_for(1)
    csl_6 = _csl_for(6)
    csl_8 = _csl_for(8)
    csl_12 = _csl_for(12)

    if csl_1:
        sigs_1 = _planet_significates_houses(csl_1, sigs)
        favourable = sigs_1 & {1, 5, 9, 10, 11}
        unfavourable = sigs_1 & {6, 8, 12}
        if favourable and not unfavourable:
            score += 4
            why.append(f"KP 1H CSL ({csl_1}) signifies {sorted(favourable)} → +4 vitality")
        elif unfavourable and not favourable:
            score -= 4
            why.append(f"KP 1H CSL ({csl_1}) signifies {sorted(unfavourable)} → −4 vitality risk")

    if csl_6:
        sigs_6 = _planet_significates_houses(csl_6, sigs)
        recovery = sigs_6 & {1, 5, 11}
        disease = sigs_6 & {6, 8, 12}
        if recovery and not disease:
            score += 3
            why.append(f"KP 6H CSL ({csl_6}) → recovery flow {sorted(recovery)}")
        elif disease and not recovery:
            score -= 3
            why.append(f"KP 6H CSL ({csl_6}) → disease persists {sorted(disease)}")

    if csl_8:
        sigs_8 = _planet_significates_houses(csl_8, sigs)
        longevity = sigs_8 & {5, 9, 11}
        leak = sigs_8 & {6, 8, 12}
        if longevity and not leak:
            score += 3
            why.append(f"KP 8H CSL ({csl_8}) → longevity boost")
        elif leak and not longevity:
            score -= 3
            why.append(f"KP 8H CSL ({csl_8}) → longevity stress")

    if csl_12:
        sigs_12 = _planet_significates_houses(csl_12, sigs)
        leak = sigs_12 & {6, 8, 12}
        if leak:
            score -= 2
            why.append(f"KP 12H CSL ({csl_12}) → hospitalisation-prone")

    if not why:
        why.append("KP CSL data inconclusive for health houses")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L19_kp_csl_health", "score": score, "weight": weight,
        "why": why,
        "csl_1": csl_1, "csl_6": csl_6, "csl_8": csl_8, "csl_12": csl_12,
    }


# ─────────────────────────────────────────────────────────────────────────────
# C. STRENGTH LAYERS  (L20 – L22)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_ashtakavarga_health(av: dict) -> dict:
    """L20 — Ashtakavarga BAV for 1H/6H/8H."""
    weight = 5
    score = 0
    why = []
    if not av:
        return {"layer": "L20_ashtakavarga", "score": 0,
                "why": ["ashtakavarga unavailable"], "weight": weight}
    bav = av.get("bhinna") or av.get("bav") or {}
    h1 = (bav.get("1") or bav.get(1) or {}).get("total") if isinstance(bav.get("1") or bav.get(1), dict) else (bav.get("1") or bav.get(1))
    h6 = (bav.get("6") or bav.get(6) or {}).get("total") if isinstance(bav.get("6") or bav.get(6), dict) else (bav.get("6") or bav.get(6))
    h8 = (bav.get("8") or bav.get(8) or {}).get("total") if isinstance(bav.get("8") or bav.get(8), dict) else (bav.get("8") or bav.get(8))

    if isinstance(h1, (int, float)):
        if h1 >= 30:
            score += 3
            why.append(f"AV 1H BAV={h1} → +3 strong vitality")
        elif h1 < 25:
            score -= 2
            why.append(f"AV 1H BAV={h1} → −2 weak vitality")

    if isinstance(h6, (int, float)):
        # Higher 6H BAV = better disease-resistance (paradox: strong 6H = strong against disease)
        if h6 >= 30:
            score += 2
            why.append(f"AV 6H BAV={h6} → +2 immunity")
        elif h6 < 25:
            score -= 1
            why.append(f"AV 6H BAV={h6} → −1 weak immunity")

    if isinstance(h8, (int, float)):
        if h8 >= 30:
            score += 2
            why.append(f"AV 8H BAV={h8} → +2 longevity strength")
        elif h8 < 22:
            score -= 2
            why.append(f"AV 8H BAV={h8} → −2 longevity stress")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L20_ashtakavarga", "score": score, "weight": weight,
        "why": why,
    }


def _layer_shadbala_health(sb: dict, intel: dict) -> dict:
    """L21 — Shadbala for lagnesh, Sun, Moon."""
    weight = 5
    score = 0
    why = []
    if not sb:
        return {"layer": "L21_shadbala", "score": 0,
                "why": ["shadbala unavailable"], "weight": weight}

    lagnesh = _house_lord(intel, 1)
    targets = [lagnesh, "Sun", "Moon"]
    for pl in targets:
        if not pl: continue
        v = sb.get(pl)
        if isinstance(v, dict):
            v = v.get("total") or v.get("rupas") or v.get("score")
        if isinstance(v, (int, float)):
            if v >= 7:
                score += 2
                why.append(f"Shadbala {pl}={v:.1f} → +2 strong")
            elif v < 5:
                score -= 2
                why.append(f"Shadbala {pl}={v:.1f} → −2 weak")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L21_shadbala", "score": score, "weight": weight,
        "why": why,
    }


def _layer_bhava_bala_health(bb: dict) -> dict:
    """L22 — Bhava Bala for 1H/6H/8H."""
    weight = 4
    score = 0
    why = []
    if not bb:
        return {"layer": "L22_bhava_bala", "score": 0,
                "why": ["bhava bala unavailable"], "weight": weight}

    for h in (1, 6, 8):
        v = bb.get(str(h)) or bb.get(h) or {}
        if isinstance(v, dict):
            v = v.get("total") or v.get("rupas")
        if isinstance(v, (int, float)):
            if v >= 7:
                score += 1
                why.append(f"Bhava Bala {h}H={v:.1f} → +1")
            elif v < 5:
                score -= 1
                why.append(f"Bhava Bala {h}H={v:.1f} → −1")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L22_bhava_bala", "score": score, "weight": weight,
        "why": why,
    }


# ─────────────────────────────────────────────────────────────────────────────
# D. YOGA LAYERS  (L23 – L25)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_arishta_yogas(yogas_d: dict, intel: dict, kundli: dict) -> dict:
    """L23 — Arishta yogas (disease/affliction yogas). Negative-weight."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    # Sample arishta detections (from upstream yogas dict OR direct check)
    # 1. Daridra yoga: 11L in dushtana from lagna
    eleventh_lord = _house_lord(intel, 11)
    if eleventh_lord:
        h = _planet_house(planets, eleventh_lord)
        if h in DUSHTANA:
            score -= 3
            why.append(f"11L ({eleventh_lord}) in {h}H → −3 daridra-arishta")

    # 2. Nicha-bhanga absent + lagnesh debilitated
    lagnesh = _house_lord(intel, 1)
    if lagnesh and _planet_dignity(intel, lagnesh) == "debilitated":
        score -= 4
        why.append(f"Lagnesh ({lagnesh}) debilitated → −4 arishta")

    # 3. Sun-Moon together with Rahu/Ketu = balarishta tendency
    sun_h = _planet_house(planets, "Sun")
    moon_h = _planet_house(planets, "Moon")
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")
    if sun_h == moon_h == rahu_h or sun_h == moon_h == ketu_h:
        score -= 3
        why.append("Sun-Moon-Rahu/Ketu cluster → −3 eclipse arishta")

    # 4. Multiple malefics in 6/8/12
    mal_in_dush = sum(1 for p in planets
                      if isinstance(p, dict)
                      and p.get("house") in DUSHTANA
                      and p.get("name") in NATURAL_MALEFICS)
    if mal_in_dush >= 3:
        score -= 2
        why.append(f"{mal_in_dush} malefics across 6/8/12 → −2 cumulative arishta")

    # Yogas dict from upstream
    if isinstance(yogas_d, dict):
        for k in ("balarishta", "alpayu", "kemadruma_arishta"):
            if yogas_d.get(k):
                score -= 2
                why.append(f"Yoga: {k} present → −2")

    if not why:
        why.append("No major arishta yogas detected")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L23_arishta_yogas", "score": score, "weight": weight,
        "why": why,
    }


def _layer_ayushkara_yogas(yogas_d: dict, intel: dict, kundli: dict) -> dict:
    """L24 — Ayushkara/longevity yogas (positive)."""
    weight = 5
    score = 0
    why = []
    planets = kundli.get("planets") or []

    # Saturn well-placed = ayushkaraka
    sat_dgn = _planet_dignity(intel, "Saturn")
    sat_h = _planet_house(planets, "Saturn")
    if sat_dgn in ("exalted", "moolatrikona", "own-sign"):
        score += 3
        why.append(f"Saturn {sat_dgn} → +3 ayushkaraka")
    if sat_h in (3, 6, 11):
        score += 2
        why.append(f"Saturn in {sat_h}H upachaya → +2 longevity")

    # Jupiter aspects 1H or 8H = grace
    jup_h = _planet_house(planets, "Jupiter")
    if jup_h:
        ja = _aspect_houses("Jupiter", jup_h)
        if 1 in ja:
            score += 2
            why.append("Jupiter aspects 1H → +2 ayushya grace")
        if 8 in ja:
            score += 2
            why.append("Jupiter aspects 8H → +2 longevity grace")

    # Lagnesh and 8L mutually friendly / connected
    lagnesh = _house_lord(intel, 1)
    eighth_lord = _house_lord(intel, 8)
    if lagnesh and eighth_lord:
        l_h = _planet_house(planets, lagnesh)
        e_h = _planet_house(planets, eighth_lord)
        if l_h and e_h and l_h == e_h:
            score += 2
            why.append(f"Lagnesh + 8L conjunct in {l_h}H → +2 longevity link")

    if not why:
        why.append("No specific ayushkara yogas detected")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L24_ayushkara_yogas", "score": score, "weight": weight,
        "why": why,
    }


def _layer_sade_sati_health(intel: dict, kundli: dict) -> dict:
    """L25 — Sade Sati on lagna/6L/8L (Saturn natal aspect approximation)."""
    weight = 5
    score = 0
    why = []
    sade = intel.get("sade_sati") or {}
    if isinstance(sade, dict):
        active = sade.get("active") or sade.get("isActive")
        phase = sade.get("phase") or sade.get("currentPhase") or ""
        if active:
            if "peak" in str(phase).lower() or "janma" in str(phase).lower():
                score -= 4
                why.append(f"Sade Sati PEAK active → −4 mind/body stress")
            elif "rising" in str(phase).lower() or "setting" in str(phase).lower():
                score -= 2
                why.append(f"Sade Sati ({phase}) active → −2 mild stress")
            else:
                score -= 2
                why.append(f"Sade Sati active → −2")
    if not why:
        why.append("Sade Sati not active or data unavailable")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L25_sade_sati", "score": score, "weight": weight,
        "why": why,
    }


# ─────────────────────────────────────────────────────────────────────────────
# E. TRIGGERS  (T1 – T3) — is the natal promise activated NOW?
# ─────────────────────────────────────────────────────────────────────────────

def _trigger_vimshottari(kundli: dict, intel: dict, karakas_d: dict) -> dict:
    """T1 — Vimshottari MD+AD+PD on health houses/karakas."""
    weight = 12
    score = 0
    why = []
    md, ad, pd = _dasha_lords(kundli)
    planets = kundli.get("planets") or []

    if not md and not ad:
        return {"layer": "T1_vimshottari", "score": 0,
                "why": ["dasha lords unknown"], "weight": weight}

    lagnesh = _house_lord(intel, 1)
    sixth_lord = _house_lord(intel, 6)
    eighth_lord = _house_lord(intel, 8)
    twelfth_lord = _house_lord(intel, 12)
    ak = karakas_d.get("AK") or karakas_d.get("Atmakaraka") or {}
    ak_planet = ak.get("planet") if isinstance(ak, dict) else ak

    health_lords = {lagnesh, sixth_lord, eighth_lord, twelfth_lord, ak_planet} - {None, ""}
    weak_lords = {sixth_lord, eighth_lord, twelfth_lord} - {None, ""}

    def _eval(role: str, planet: str, weight_factor: float):
        nonlocal score
        if not planet:
            return
        h = _planet_house(planets, planet)
        dgn = _planet_dignity(intel, planet)
        # Lagnesh / AK in {role} = vitality testing
        if planet == lagnesh:
            if dgn in ("exalted", "moolatrikona", "own-sign"):
                score += int(4 * weight_factor)
                why.append(f"{role} {planet}=Lagnesh strong → {int(4*weight_factor):+d}")
            elif dgn == "debilitated":
                score -= int(4 * weight_factor)
                why.append(f"{role} {planet}=Lagnesh debilitated → {-int(4*weight_factor):+d}")
        elif planet == ak_planet:
            if dgn in ("exalted", "moolatrikona", "own-sign"):
                score += int(3 * weight_factor)
                why.append(f"{role} {planet}=AK strong → {int(3*weight_factor):+d}")
            else:
                why.append(f"{role} {planet}=AK active")
        elif planet in (sixth_lord, eighth_lord, twelfth_lord):
            score -= int(3 * weight_factor)
            why.append(f"{role} {planet}=dushtana lord → {-int(3*weight_factor):+d}")
        elif planet in NATURAL_BENEFICS:
            score += int(2 * weight_factor)
            why.append(f"{role} {planet} (benefic) → {int(2*weight_factor):+d}")
        elif planet in NATURAL_MALEFICS:
            if h in DUSHTANA:
                why.append(f"{role} {planet} in {h}H dushtana — neutral")
            else:
                score -= int(2 * weight_factor)
                why.append(f"{role} {planet} (malefic) → {-int(2*weight_factor):+d}")

    if md: _eval("MD", md, 1.0)
    if ad: _eval("AD", ad, 0.7)
    if pd: _eval("PD", pd, 0.4)

    score = max(-weight, min(weight, score))
    return {
        "layer": "T1_vimshottari", "score": score, "weight": weight,
        "why": why,
        "md": md, "ad": ad, "pd": pd,
    }


def _trigger_saturn_transit_health(saturn_t: dict, intel: dict) -> dict:
    """T2 — Saturn transit on 1/6/8/12 + sade-sati phases."""
    weight = 7
    score = 0
    why = []
    if not saturn_t:
        return {"layer": "T2_saturn_transit", "score": 0,
                "why": ["saturn transit data unavailable"], "weight": weight}

    house = saturn_t.get("saturn_house_from_lagna")
    if house in (1, 6):
        score -= 3
        why.append(f"Saturn transiting {house}H → −3 chronic stress")
    elif house == 8:
        score -= 4
        why.append(f"Saturn transiting 8H (ashtama) → −4 chronic / longevity stress")
    elif house == 12:
        score -= 2
        why.append(f"Saturn transiting 12H → −2 sleep / hidden")
    elif saturn_t.get("aspecting_health"):
        score -= 2
        why.append(f"Saturn aspects health house → −2")

    phase = saturn_t.get("sade_sati_phase")
    if phase == "peak":
        score -= 4
        why.append(f"Saturn sade-sati PEAK over Moon → −4")
    elif phase in ("rising", "setting"):
        score -= 2
        why.append(f"Saturn sade-sati {phase} → −2")
    elif phase == "ashtama":
        score -= 3
        why.append(f"Ashtama Shani over Moon → −3")
    elif phase == "kantaka":
        score -= 2
        why.append(f"Kantaka Shani over Moon → −2")

    if not why:
        why.append(f"Saturn neutral position ({saturn_t.get('saturn_sign')})")

    score = max(-weight, min(weight, score))
    return {
        "layer": "T2_saturn_transit", "score": score, "weight": weight,
        "why": why,
    }


def _trigger_mars_rahu_transit(mars_t: dict, rk_t: dict) -> dict:
    """T3 — Mars transit on 1/6/8 + Rahu/Ketu axis on 1/7."""
    weight = 6
    score = 0
    why = []

    if mars_t:
        mhouse = mars_t.get("mars_house_from_lagna")
        if mhouse in (1, 6):
            score -= 2
            why.append(f"Mars transit {mhouse}H → −2 inflammation/anger")
        elif mhouse == 8:
            score -= 3
            why.append(f"Mars transit 8H → −3 surgery/accident risk")
        elif mars_t.get("aspecting_risk"):
            score -= 2
            why.append("Mars aspects 1/6/8 → −2")

    if rk_t:
        if rk_t.get("on_axis_1_7"):
            score -= 2
            why.append("Rahu/Ketu on 1/7 axis → −2 sudden change")
        if rk_t.get("on_axis_6_12"):
            score -= 1
            why.append("Rahu/Ketu on 6/12 axis → −1 hidden afflictions")

    if not why:
        why.append("Mars + Rahu/Ketu transits neutral for health houses")

    score = max(-weight, min(weight, score))
    return {
        "layer": "T3_mars_rahu_transit", "score": score, "weight": weight,
        "why": why,
    }


# ─────────────────────────────────────────────────────────────────────────────
# F. MODIFIERS (M1 – M7)
# ─────────────────────────────────────────────────────────────────────────────

def _modifier_combust(intel: dict, kundli: dict) -> dict:
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    lagnesh = _house_lord(intel, 1)
    for pl in (lagnesh, "Sun", "Moon"):
        if pl and _is_combust(planets, pl):
            delta -= 2
            why.append(f"{pl} combust → −2")
    return {"mod": "M1_combust", "delta": delta, "why": why}


def _modifier_retrograde(intel: dict, kundli: dict) -> dict:
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    lagnesh = _house_lord(intel, 1)
    sixth_lord = _house_lord(intel, 6)
    eighth_lord = _house_lord(intel, 8)
    for pl in (lagnesh, sixth_lord, eighth_lord):
        if pl and _is_retrograde(planets, pl):
            delta -= 1
            why.append(f"{pl} retrograde → −1 karmic-revisit")
    return {"mod": "M2_retrograde", "delta": delta, "why": why}


def _modifier_malefic_aspects(intel: dict, kundli: dict) -> dict:
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    for h in (1, 6):
        aspecting = _planets_aspecting_house(planets, h)
        bad = [p for p in aspecting if p in ("Saturn", "Mars", "Rahu", "Ketu")]
        good = [p for p in aspecting if p in ("Jupiter", "Venus")]
        if bad:
            delta -= len(bad)
            why.append(f"{','.join(bad)} aspect {h}H → {-len(bad):+d}")
        if good:
            delta += len(good)
            why.append(f"{','.join(good)} aspect {h}H → {+len(good):+d}")
    eighth_lord = _house_lord(intel, 8)
    if eighth_lord:
        eh = _planet_house(planets, eighth_lord)
        if eh:
            mal = [p for p in _planets_aspecting_house(planets, eh)
                   if p in ("Saturn", "Mars", "Rahu", "Ketu")]
            if mal:
                delta -= 1
                why.append(f"Malefics aspect 8L ({eighth_lord}) → −1")
    return {"mod": "M3_malefic_aspects", "delta": delta, "why": why}


def _modifier_lagnesh_strength(intel: dict) -> dict:
    delta = 0
    why = []
    lagnesh = _house_lord(intel, 1)
    if lagnesh:
        dgn = _planet_dignity(intel, lagnesh)
        if dgn in ("exalted", "moolatrikona"):
            delta += 2
            why.append(f"Lagnesh {dgn} → +2 vitality")
        elif dgn == "debilitated":
            delta -= 2
            why.append(f"Lagnesh debilitated → −2 vitality")
    return {"mod": "M4_lagnesh_strength", "delta": delta, "why": why}


def _modifier_sade_sati_mod(intel: dict, kundli: dict) -> dict:
    delta = 0
    why = []
    sade = intel.get("sade_sati") or {}
    if isinstance(sade, dict) and sade.get("active"):
        delta -= 3
        why.append("Sade-sati active → −3 mind/body modifier")
    return {"mod": "M5_sade_sati", "delta": delta, "why": why}


def _modifier_jupiter_transit_health(jup_t: dict) -> dict:
    delta = 0
    why = []
    if not jup_t:
        return {"mod": "M6_jupiter_transit", "delta": 0, "why": []}
    aw = jup_t.get("active_window")
    if aw and aw.get("hits"):
        # Hits include L1/L5/L9 = grace
        if any("L1" in h or "L5" in h or "L9" in h or "M1" in h or "M5" in h or "M9" in h
               for h in aw.get("hits", [])):
            delta += 3
            why.append(f"Jupiter transiting health-grace house ({','.join(aw['hits'])}) → +3")
    return {"mod": "M6_jupiter_transit", "delta": delta, "why": why}


def _modifier_rahu_ketu_axis(rk_t: dict) -> dict:
    delta = 0
    why = []
    if not rk_t:
        return {"mod": "M7_rahu_ketu_axis", "delta": 0, "why": []}
    if rk_t.get("on_axis_1_7"):
        delta -= 2
        why.append("Rahu/Ketu on 1/7 → −2 sudden-change health")
    return {"mod": "M7_rahu_ketu_axis", "delta": delta, "why": why}


# ─────────────────────────────────────────────────────────────────────────────
# G. CONDITIONALS (C1 – C5) — only when question type matches
# ─────────────────────────────────────────────────────────────────────────────

def _conditional_chronic(intel: dict, kundli: dict, saturn_t: dict) -> dict:
    """C1 — Chronic illness deep dive (8H+6H+Saturn)."""
    score = 0
    why = []
    planets = kundli.get("planets") or []
    eighth_lord = _house_lord(intel, 8)
    sixth_lord = _house_lord(intel, 6)
    sat_h = _planet_house(planets, "Saturn")
    sat_dgn = _planet_dignity(intel, "Saturn")

    chronic_signs = []
    if sat_h in (1, 4, 6, 8) and sat_dgn in ("debilitated", "enemy-sign"):
        chronic_signs.append(f"Saturn {sat_dgn} in {sat_h}H")
        score -= 3
    if eighth_lord and _planet_house(planets, eighth_lord) == 1:
        chronic_signs.append(f"8L ({eighth_lord}) in 1H")
        score -= 3
    if sixth_lord and _planet_house(planets, sixth_lord) in KENDRA:
        chronic_signs.append(f"6L ({sixth_lord}) in kendra")
        score -= 2
    if saturn_t and saturn_t.get("on_health_house"):
        chronic_signs.append(f"Saturn transit {saturn_t.get('saturn_house_from_lagna')}H")
        score -= 2
    if saturn_t and saturn_t.get("sade_sati_phase") in ("peak", "ashtama"):
        chronic_signs.append(f"Saturn {saturn_t.get('sade_sati_phase')}")
        score -= 2

    if chronic_signs:
        why.append(f"Chronic-pattern signs: {', '.join(chronic_signs)}")
    else:
        why.append("Chronic pattern not strongly indicated")

    return {"cond": "C1_chronic", "score": score, "why": why,
            "chronic_signs": chronic_signs}


def _conditional_acute(intel: dict, kundli: dict) -> dict:
    """C2 — Acute illness check (6H + Mars/Sun aspect)."""
    score = 0
    why = []
    planets = kundli.get("planets") or []
    sixth_lord = _house_lord(intel, 6)
    mars_h = _planet_house(planets, "Mars")
    sun_h = _planet_house(planets, "Sun")
    mars_aspects_6 = mars_h and 6 in _aspect_houses("Mars", mars_h)
    sun_aspects_6 = sun_h and 6 in _aspect_houses("Sun", sun_h)

    if mars_aspects_6 or sun_aspects_6:
        score += 2
        why.append("Mars/Sun aspect 6H → quick disease-clearing capacity")
    if sixth_lord and _planet_dignity(intel, sixth_lord) in ("exalted", "moolatrikona"):
        score -= 2
        why.append(f"6L ({sixth_lord}) strong → acute illness intensifies briefly")
    return {"cond": "C2_acute", "score": score, "why": why}


def _conditional_surgery(intel: dict, kundli: dict, mars_t: dict) -> dict:
    """C3 — Surgery timing check (8H + Mars/Ketu transit)."""
    score = 0
    why = []
    planets = kundli.get("planets") or []
    mars_in_8 = _planet_house(planets, "Mars") == 8
    ketu_in_8 = _planet_house(planets, "Ketu") == 8
    if mars_in_8 or ketu_in_8:
        score -= 2
        why.append(f"Mars/Ketu in 8H — surgery indication noted")
    if mars_t and mars_t.get("mars_house_from_lagna") in (1, 6, 8):
        score -= 2
        why.append(f"Mars transit through {mars_t['mars_house_from_lagna']}H — "
                   f"avoid elective surgery / be extra careful with planned procedures")
    return {"cond": "C3_surgery", "score": score, "why": why,
            "mars_in_8": mars_in_8, "ketu_in_8": ketu_in_8}


def _conditional_mental(intel: dict, kundli: dict, saturn_t: dict) -> dict:
    """C4 — Mental health (Moon + 4H + Mercury affliction)."""
    score = 0
    why = []
    planets = kundli.get("planets") or []
    moon_h = _planet_house(planets, "Moon")
    moon_dgn = _planet_dignity(intel, "Moon")
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")
    sat_h = _planet_house(planets, "Saturn")
    fourth_lord = _house_lord(intel, 4)

    if moon_h and (moon_h == rahu_h or moon_h == ketu_h):
        score -= 4
        why.append("Moon-Rahu/Ketu — anxiety / overthinking tendency")
    if moon_dgn == "debilitated":
        score -= 2
        why.append("Moon debilitated — emotional fragility")
    if sat_h and sat_h == moon_h:
        score -= 3
        why.append("Saturn-Moon conjunct — depression tendency (manas-doha)")
    if saturn_t and saturn_t.get("sade_sati_phase") in ("peak", "kantaka"):
        score -= 2
        why.append(f"Saturn {saturn_t['sade_sati_phase']} on Moon — current mental stress")
    if fourth_lord:
        f_h = _planet_house(planets, fourth_lord)
        if f_h in DUSHTANA:
            score -= 2
            why.append(f"4L ({fourth_lord}) in {f_h}H — emotional foundation stress")

    if not why:
        why.append("No major mental-health afflictions detected — favourable mind")

    return {"cond": "C4_mental", "score": score, "why": why}


def _conditional_longevity(intel: dict, kundli: dict, av: dict) -> dict:
    """C5 — Longevity general (1H BAV + lagnesh + Sun/Moon strength).
    STRICT brand safety — engine returns a QUALITATIVE band only
    (favourable / mixed / needs-care). NEVER predict death date or years left.
    """
    band = "mixed"
    why = []
    score = 0
    planets = kundli.get("planets") or []

    lagnesh = _house_lord(intel, 1)
    lag_dgn = _planet_dignity(intel, lagnesh) if lagnesh else None
    sun_dgn = _planet_dignity(intel, "Sun")
    moon_dgn = _planet_dignity(intel, "Moon")
    sat_dgn = _planet_dignity(intel, "Saturn")

    pos_count = sum(1 for d in (lag_dgn, sun_dgn, moon_dgn, sat_dgn)
                    if d in ("exalted", "moolatrikona", "own-sign", "friend-sign"))
    neg_count = sum(1 for d in (lag_dgn, sun_dgn, moon_dgn, sat_dgn)
                    if d in ("debilitated", "enemy-sign"))

    h1_bav = None
    if av:
        bav = av.get("bhinna") or av.get("bav") or {}
        v = bav.get("1") or bav.get(1)
        if isinstance(v, dict): v = v.get("total")
        if isinstance(v, (int, float)): h1_bav = v

    if pos_count >= 3 and (h1_bav is None or h1_bav >= 28):
        band = "favourable"
        score += 3
        why.append(f"Lagnesh/Sun/Moon/Sat strong (pos={pos_count}); 1H BAV={h1_bav}")
    elif neg_count >= 2 or (h1_bav is not None and h1_bav < 22):
        band = "needs_care"
        score -= 3
        why.append(f"Multiple weak vitality factors (neg={neg_count}); 1H BAV={h1_bav}")
    else:
        band = "mixed"
        why.append(f"Balanced vitality factors (pos={pos_count}, neg={neg_count}); 1H BAV={h1_bav}")

    why.append("⚠ ENGINE RULE: Never predict specific death date / 'X years left'. "
               "Output is qualitative band only.")

    return {"cond": "C5_longevity", "score": score, "band": band, "why": why}


# ─────────────────────────────────────────────────────────────────────────────
# REMEDY SELECTION
# ─────────────────────────────────────────────────────────────────────────────
_REMEDY_BY_PLANET = {
    "Sun": {
        "mantra":    "Om Suryaya Namah (108x daily, sunrise)",
        "donation":  "Wheat, jaggery, copper to a needy person on Sundays",
        "gemstone":  "Ruby — only after qualified astrologer's gemstone-suitability check",
        "lifestyle": "Surya Namaskar daily; eye-care; cardio check-up annually",
    },
    "Moon": {
        "mantra":    "Om Chandraya Namah (108x daily, evening)",
        "donation":  "Rice, white cloth, milk on Mondays",
        "gemstone":  "Pearl — only after qualified astrologer's check",
        "lifestyle": "Sleep hygiene; meditation; hydration; reduce screen-time at night",
    },
    "Mars": {
        "mantra":    "Om Mangalaya Namah (108x daily, Tuesday morning)",
        "donation":  "Red lentils (masoor dal), copper on Tuesdays",
        "gemstone":  "Red Coral — only after qualified astrologer's check",
        "lifestyle": "Anger management; avoid risky travel during Mars retrograde; "
                     "blood-test annually (BP, hemoglobin, lipid)",
    },
    "Mercury": {
        "mantra":    "Om Budhaya Namah (108x daily, Wednesday)",
        "donation":  "Green moong dal, green cloth on Wednesdays",
        "gemstone":  "Emerald — only after qualified astrologer's check",
        "lifestyle": "Nervous-system care: yoga, pranayama, skin care, allergy testing",
    },
    "Jupiter": {
        "mantra":    "Om Brihaspataye Namah (108x daily, Thursday)",
        "donation":  "Yellow dal (chana), turmeric, books on Thursdays",
        "gemstone":  "Yellow Sapphire — only after qualified astrologer's check",
        "lifestyle": "Liver-friendly diet (less oily, less alcohol); annual lipid + LFT check",
    },
    "Venus": {
        "mantra":    "Om Shukraya Namah (108x daily, Friday)",
        "donation":  "Sugar, rice, white cloth, perfume on Fridays",
        "gemstone":  "Diamond — only after qualified astrologer's check",
        "lifestyle": "Hormone + kidney profile annually; reproductive-health check; hydration",
    },
    "Saturn": {
        "mantra":    "Om Shanaye Namah (108x daily, Saturday evening)",
        "donation":  "Black sesame (til), iron, mustard oil, black cloth on Saturdays",
        "gemstone":  "Blue Sapphire — STRICT trial period required, only via qualified astrologer",
        "lifestyle": "Bone & joint care; vitamin D + B12 check annually; consistent routine",
    },
    "Rahu": {
        "mantra":    "Om Rahave Namah (108x daily) + Durga Saptashati path",
        "donation":  "Mixed grains, blue cloth, mustard oil to needy",
        "gemstone":  "Hessonite (Gomed) — only via qualified astrologer",
        "lifestyle": "Allergy testing; addiction-awareness; avoid sudden lifestyle shifts",
    },
    "Ketu": {
        "mantra":    "Om Ketave Namah (108x daily) + Ganesha Atharvashirsha",
        "donation":  "Multi-coloured cloth, blanket, sesame oil to needy",
        "gemstone":  "Cat's Eye (Lehsuniya) — only via qualified astrologer",
        "lifestyle": "Spinal-care; immunity boosters; meditation for clarity",
    },
}


def _select_health_remedy(intel: dict, kundli: dict, karakas_d: dict,
                          layers: dict) -> dict:
    """Choose weakest health-related planet (lagnesh, AK, Sun, Moon, 6L, 8L)
    and return its remedy bundle."""
    planets_to_check = []
    lagnesh = _house_lord(intel, 1)
    sixth_lord = _house_lord(intel, 6)
    eighth_lord = _house_lord(intel, 8)
    ak = karakas_d.get("AK") or karakas_d.get("Atmakaraka") or {}
    ak_planet = ak.get("planet") if isinstance(ak, dict) else ak

    candidates = [lagnesh, ak_planet, "Sun", "Moon", sixth_lord, eighth_lord]
    seen = set()
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            planets_to_check.append(c)

    weakest = None
    weakest_score = 999
    for pl in planets_to_check:
        dgn = _planet_dignity(intel, pl)
        rank = DIGNITY_RANK.get(dgn, 2)
        # combust/retrograde => add penalty
        penalty = 0
        if _is_combust(kundli.get("planets") or [], pl):
            penalty += 1
        if _is_retrograde(kundli.get("planets") or [], pl):
            penalty += 1
        adj = rank - penalty
        if adj < weakest_score:
            weakest_score = adj
            weakest = pl

    if not weakest:
        return {"remedy_planet": None,
                "remedy_text":   "Daily 10-minute meditation + balanced diet + annual full-body check-up.",
                "details":       {}}

    bundle = _REMEDY_BY_PLANET.get(weakest, {})
    text = (f"Strengthen {weakest} (your weakest health-significator): "
            f"{bundle.get('mantra','')}. "
            f"{bundle.get('lifestyle','')}.")
    return {
        "remedy_planet": weakest,
        "remedy_text":   text,
        "details":       bundle,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BRAND-SAFETY GUARDS — STRICT for health
# ─────────────────────────────────────────────────────────────────────────────
def _brand_safety_warnings(bucket: str, verdict: str, conditional_results: dict,
                           birth: Optional[dict] = None) -> list[str]:
    """Health is the highest brand-risk domain — every output MUST honour
    these guards. Narrator turns these into Hinglish caveats."""
    warnings: list[str] = []

    # Universal — ALWAYS apply, no exceptions
    warnings.append(
        "Cosmic verdict ek probabilistic guidance hai — yeh medical diagnosis "
        "ya prescription ka VIKALP NAHI hai. Kisi bhi serious symptom ke "
        "liye qualified doctor / specialist se consult zaroor karein."
    )
    warnings.append(
        "Hum kabhi koi specific bimari diagnose nahi karte aur kabhi koi "
        "medicine recommend nahi karte. Cosmic insights sirf timing + "
        "support ke liye hain — actual treatment doctor decide karenge."
    )

    if bucket == "longevity_general":
        warnings.append(
            "Hum kabhi kisi vyakti ki aayu (life span) ya marne ki date "
            "predict nahi karte — yeh unethical aur galat hai. Cosmic "
            "guidance sirf qualitative band (favourable / mixed / "
            "needs-care) deta hai, exact saal/mahina nahi."
        )
        warnings.append(
            "Vitality maintain karne ke liye consistent sleep, balanced diet, "
            "regular preventive check-up (annual full-body), aur stress "
            "management essential hain — chart sirf inn habits ka multiplier hai."
        )

    if bucket == "chronic_illness":
        warnings.append(
            "Chronic conditions (diabetes, BP, thyroid, arthritis, heart, "
            "cancer, autoimmune) ka management astrology se possible nahi "
            "hai — doctor-prescribed medicine, regular monitoring, aur "
            "lifestyle compliance HI primary treatment hai. Cosmic insights "
            "sirf timing + emotional support ke liye hain."
        )
        warnings.append(
            "Medicine kabhi bina doctor ki salah ke band na karein, chahe "
            "remedy ya mantra start karein. Self-medication life-threatening "
            "ho sakti hai."
        )

    if bucket == "acute_illness":
        warnings.append(
            "Fever, persistent cough, severe pain, breathing difficulty, "
            "ya kisi bhi rapidly worsening symptom ke liye 24 ghante ke "
            "andar doctor se milein — astrology yahan delay ka reason "
            "nahi banni chahiye."
        )

    if bucket == "mental_health":
        warnings.append(
            "Depression, anxiety, panic attacks, suicidal thoughts, ya "
            "severe insomnia ke liye qualified mental-health professional "
            "(psychiatrist / psychologist / therapist) se baat karna "
            "ESSENTIAL hai. India mein iCall (9152987821) aur Vandrevala "
            "Foundation (1860-2662-345) free helplines hain. Cosmic "
            "insights replacement nahi, additional support hai."
        )
        warnings.append(
            "Agar self-harm ya suicidal thoughts aa rahe hain — please "
            "abhi kisi trusted vyakti ko bataayein aur professional help "
            "lein. Aap akele nahi hain."
        )

    if bucket == "addiction":
        warnings.append(
            "Addiction (sharab, smoking, drugs, gambling) ka root cause "
            "chart se isolated nahi hota — yeh psychological + biological "
            "+ social ek combined challenge hai. Rehab centre, qualified "
            "therapist, aur support groups (AA / NA / SMART Recovery) "
            "primary intervention hain. Cosmic timing sirf supportive "
            "context deta hai."
        )
        warnings.append(
            "Kabhi achaanak high-dose addiction (alcohol, opioids, "
            "benzodiazepines) chodna jaan-leva ho sakta hai. Hamesha "
            "medical supervision ke under taper karein."
        )

    if bucket == "surgery_timing":
        warnings.append(
            "Surgery timing ka final decision aapke surgeon + treating "
            "doctor par hai — cosmic favourable window sirf supportive "
            "context hai. Kabhi medically urgent surgery ko astrology ki "
            "wajah se postpone NA karein."
        )
        warnings.append(
            "Pre-operative protocol (fasting, medicine adjustment, second "
            "opinion, hospital safety) follow karna mandatory hai — "
            "cosmic timing iska supplement hai, replacement nahi."
        )

    if bucket == "recovery_timing":
        warnings.append(
            "Recovery timing individual healing rate, treatment compliance, "
            "rest, nutrition, aur underlying condition par depend karti "
            "hai. Cosmic window sirf supportive backdrop hai — actual "
            "milestones aapke doctor define karenge."
        )

    if bucket == "injury_accident":
        warnings.append(
            "Accident-prone window mein extra cautious driving, helmet/seat-"
            "belt, road-safety rules, aur risky activities (extreme sports, "
            "late-night driving) ko avoid karein. Cosmic guidance sirf "
            "awareness ke liye hai — fate nahi."
        )

    if bucket == "female_reproductive":
        warnings.append(
            "Reproductive health (period issues, PCOD/PCOS, fertility, "
            "pregnancy, menopause) ke liye gynaecologist + fertility "
            "specialist se consult zaroor karein. Cosmic insights timing "
            "+ emotional support ke liye hain — clinical evaluation ka "
            "vikalp nahi."
        )
        warnings.append(
            "Fertility / IVF / pregnancy ke baare mein hum kabhi guarantee "
            "nahi dete — har case individual hai aur medical evaluation "
            "ke baad hi clarity aati hai."
        )

    if bucket == "male_reproductive":
        warnings.append(
            "Male reproductive health (prostate, sperm count, erectile "
            "function, fertility) ke liye urologist / andrologist se "
            "consult karein. Astrological guidance supportive hai, "
            "diagnostic nahi."
        )

    if bucket == "parent_health":
        warnings.append(
            "Hum kabhi kisi parent (maa/papa/relative) ki bimari ya life "
            "span predict nahi karte. Aapke parents ki health ke liye "
            "unke treating doctor + family support primary hain. Cosmic "
            "insights aapko emotional resilience + supportive timing "
            "samajhne ke liye hain."
        )
        warnings.append(
            "Senior-citizen health ke liye annual check-up, medicine "
            "compliance, aur emergency contact list essential hain."
        )

    if verdict == "red_avoid":
        warnings.append(
            "Currently major elective health decisions (cosmetic surgery, "
            "elective procedures, drastic diet changes) defer karein. "
            "Existing treatment + recovery par focus karein."
        )

    # Cap at 8 (per CLE rule for narrator override — health gets +1 over career)
    return warnings[:8]


# ─────────────────────────────────────────────────────────────────────────────
# ASSESS_HEALTH — main orchestrator
# ─────────────────────────────────────────────────────────────────────────────
def assess_health(kundli: dict,
                  intel: dict,
                  kp: Optional[dict] = None,
                  birth: Optional[dict] = None,
                  question: str = "",
                  pre_classified_bucket: str | None = None) -> dict:
    """Full deterministic health verdict. Returns dict with:
      bucket            — one of 12 question buckets
      tense             — future / present / general
      verdict           — green_go / yellow_wait / slow_burn / red_avoid
      score, confidence — 0-100
      score_breakdown   — layer/trigger/modifier/cond split
      strategy          — Hinglish action verbatim
      timing_window     — { start, end, lords }
      remedy            — weakest-planet remedy bundle
      brand_safety_warnings — list of bullets narrator MUST honour
      layers/triggers/modifiers/conditionals — full audit trail
    """
    bucket = classify_health_question(question, pre_classified_bucket)
    tense  = detect_question_tense(question)
    intel = intel or {}
    kp = kp or {}
    birth = birth or {}

    asc = kundli.get("ascendant") or {}
    lagna_sign = (asc.get("sign") if isinstance(asc, dict) else None) or intel.get("lagna_sign")
    lagna_idx = _sign_idx(lagna_sign) if lagna_sign else 0
    if lagna_idx < 0: lagna_idx = 0
    moon_sign = kundli.get("moonSign") or _planet_sign(kundli.get("planets") or [], "Moon")
    moon_idx = _sign_idx(moon_sign) if moon_sign else -1

    # Lazy-load helpers
    sb = _maybe_shadbala(kundli, lagna_idx)
    av = _maybe_ashtakavarga(kundli, lagna_idx)
    bb = _maybe_bhava_bala(intel, sb)
    karakas_d = _maybe_karakas(kundli)
    yogas_d = _maybe_varga_yogas(kundli, _planet_lon(kundli.get("planets") or [], "Asc"))
    jup_t = _maybe_jupiter_transit(lagna_idx, moon_idx if moon_idx >= 0 else None)
    sat_t = _maybe_saturn_transit_health(lagna_idx, moon_idx if moon_idx >= 0 else None)
    mars_t = _maybe_mars_transit_health(lagna_idx)
    rk_t = _maybe_rahu_ketu_transit(lagna_idx)

    # ── A. Natal layers (L1-L15) ────────────────────────────────────────────
    L = {}
    L["L1"]  = _layer_lagna_first_house(intel, kundli)
    L["L2"]  = _layer_sixth_house(intel, kundli)
    L["L3"]  = _layer_eighth_house(intel, kundli)
    L["L4"]  = _layer_twelfth_house(intel, kundli)
    L["L5"]  = _layer_sun_karaka(intel, kundli)
    L["L6"]  = _layer_moon_karaka(intel, kundli)
    L["L7"]  = _layer_mars_karaka(intel, kundli)
    L["L8"]  = _layer_saturn_karaka(intel, kundli)
    L["L9"]  = _layer_jupiter_karaka(intel, kundli)
    L["L10"] = _layer_mercury_karaka(intel, kundli)
    L["L11"] = _layer_venus_karaka(intel, kundli)
    L["L12"] = _layer_rahu_karaka(intel, kundli)
    L["L13"] = _layer_ketu_karaka(intel, kundli)
    L["L14"] = _layer_atmakaraka_health(karakas_d, intel, kundli)
    L["L15"] = _layer_lagna_bhava_aspect(intel, kundli)

    # ── B. Divisional + KP (L16-L19) ────────────────────────────────────────
    L["L16"] = _layer_d9_overlay(kundli, intel, karakas_d)
    L["L17"] = _layer_d6_overlay(kundli, intel)
    L["L18"] = _layer_d30_overlay(kundli, intel)
    L["L19"] = _layer_kp_csl_health(kp)

    # ── C. Strength (L20-L22) ───────────────────────────────────────────────
    L["L20"] = _layer_ashtakavarga_health(av)
    L["L21"] = _layer_shadbala_health(sb, intel)
    L["L22"] = _layer_bhava_bala_health(bb)

    # ── D. Yogas (L23-L25) ──────────────────────────────────────────────────
    L["L23"] = _layer_arishta_yogas(yogas_d, intel, kundli)
    L["L24"] = _layer_ayushkara_yogas(yogas_d, intel, kundli)
    L["L25"] = _layer_sade_sati_health(intel, kundli)

    layer_score = sum(L[k].get("score", 0) for k in L)

    # ── E. Triggers ─────────────────────────────────────────────────────────
    T = {}
    T["T1"] = _trigger_vimshottari(kundli, intel, karakas_d)
    T["T2"] = _trigger_saturn_transit_health(sat_t, intel)
    T["T3"] = _trigger_mars_rahu_transit(mars_t, rk_t)
    trigger_score = sum(T[k].get("score", 0) for k in T)

    # ── F. Modifiers ────────────────────────────────────────────────────────
    M = {}
    M["M1"] = _modifier_combust(intel, kundli)
    M["M2"] = _modifier_retrograde(intel, kundli)
    M["M3"] = _modifier_malefic_aspects(intel, kundli)
    M["M4"] = _modifier_lagnesh_strength(intel)
    M["M5"] = _modifier_sade_sati_mod(intel, kundli)
    M["M6"] = _modifier_jupiter_transit_health(jup_t)
    M["M7"] = _modifier_rahu_ketu_axis(rk_t)
    modifier_delta = sum(M[k].get("delta", 0) for k in M)

    # ── G. Conditionals (only those matching bucket) ────────────────────────
    conditionals = {}
    if bucket == "chronic_illness":
        conditionals["C1"] = _conditional_chronic(intel, kundli, sat_t)
    if bucket == "acute_illness":
        conditionals["C2"] = _conditional_acute(intel, kundli)
    if bucket == "surgery_timing":
        conditionals["C3"] = _conditional_surgery(intel, kundli, mars_t)
    if bucket in ("mental_health", "addiction"):
        conditionals["C4"] = _conditional_mental(intel, kundli, sat_t)
    if bucket == "longevity_general":
        conditionals["C5"] = _conditional_longevity(intel, kundli, av)
    cond_bonus = sum(c.get("score", 0) for c in conditionals.values())

    # ── Total score (weighted, normalised to 0-100) ─────────────────────────
    raw = layer_score + trigger_score + modifier_delta + cond_bonus
    # Layer max ≈ 14+16+14+10+10+10+8+8+6+5+5+6+6+10+4 + 10+14+8+12 + 5+5+4 + 6+5+5 = 206
    # Trigger max ≈ 12+7+6 = 25
    # Modifier range ≈ ±15
    # Conditional ±5
    LAYER_MAX = 206
    TRIGGER_MAX = 25
    # Map raw to 0-100. Center at 50 when raw=0.
    normalised = 50 + (raw / (LAYER_MAX + TRIGGER_MAX) * 50)
    total_score = int(max(0, min(100, normalised)))

    # ── Verdict resolution (bucket-gated) ───────────────────────────────────
    natal_promise_strong = layer_score > 10
    trigger_active = trigger_score > 2
    if total_score >= 65 and trigger_active:
        verdict = "green_go"
    elif total_score >= 55:
        verdict = "yellow_wait"
    elif total_score >= 40:
        verdict = "slow_burn"
    else:
        verdict = "red_avoid"
    # Tense override: if user asks PRESENT and trigger weak → yellow not green
    if tense == "present" and trigger_score < 3 and verdict == "green_go":
        verdict = "yellow_wait"
    # Bucket-specific clamps
    if bucket == "longevity_general":
        # Longevity question → never red_avoid (brand safety: don't scare)
        if verdict == "red_avoid":
            verdict = "slow_burn"

    # Confidence — agreement across systems
    agreement_signals = 0
    if L["L19"].get("score", 0) != 0: agreement_signals += 1   # KP active
    if L["L16"].get("score", 0) != 0: agreement_signals += 1   # D9 active
    if L["L17"].get("score", 0) != 0: agreement_signals += 1   # D6 active
    if T["T1"].get("score", 0) != 0:  agreement_signals += 1   # Dasha active
    if av:                            agreement_signals += 1
    if sb:                            agreement_signals += 1
    confidence = min(95, 55 + agreement_signals * 6)

    # ── Strategy ────────────────────────────────────────────────────────────
    strategy = _strategy_for(bucket, verdict)

    # ── Timing window ───────────────────────────────────────────────────────
    timing_window = _build_timing_window(kundli, intel, sat_t, mars_t, jup_t)

    # ── Remedy ──────────────────────────────────────────────────────────────
    remedy = _select_health_remedy(intel, kundli, karakas_d, L)

    # ── Top concern + supportive planets ────────────────────────────────────
    layer_planet_signals = []
    for k, ld in L.items():
        if ld.get("score", 0) <= -3:
            layer_planet_signals.append((ld.get("score", 0), k, ld.get("layer", k)))
    layer_planet_signals.sort()
    top_concerns = [{"layer": s[2], "score": s[0]} for s in layer_planet_signals[:3]]

    layer_supportive = []
    for k, ld in L.items():
        if ld.get("score", 0) >= 4:
            layer_supportive.append((ld.get("score", 0), k, ld.get("layer", k)))
    layer_supportive.sort(reverse=True)
    top_supportive = [{"layer": s[2], "score": s[0]} for s in layer_supportive[:3]]

    # ── Brand-safety warnings ───────────────────────────────────────────────
    warnings = _brand_safety_warnings(bucket, verdict, conditionals, birth)

    # ── Reasons audit (top facts) ───────────────────────────────────────────
    reasons = []
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

    return {
        "bucket":               bucket,
        "tense":                tense,
        "verdict":              verdict,
        "confidence":           confidence,
        "score":                total_score,
        "score_breakdown": {
            "layer_score":    layer_score,
            "trigger_score":  trigger_score,
            "modifier_delta": modifier_delta,
            "cond_bonus":     cond_bonus,
        },
        "natal_promise_score":  layer_score,
        "current_trigger_score": trigger_score,
        "strategy":             strategy,
        "timing_window":        timing_window,
        "remedy":               remedy,
        "top_concerns":         top_concerns,
        "top_supportive":       top_supportive,
        "brand_safety_warnings": warnings,
        "layers":               L,
        "triggers":             T,
        "modifiers":            M,
        "conditionals":         conditionals,
        "reasons":              reasons,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY + TIMING WINDOW HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _strategy_for(bucket: str, verdict: str) -> str:
    """One-line bucket-x-verdict Hinglish action."""
    if verdict == "green_go":
        base = {
            "chronic_illness":     "Treatment compliance + lifestyle discipline ka strong window — doctor ke saath review karke optimised plan banayein.",
            "acute_illness":       "Healing fast hoga — rest + hydration + prescribed medicine maintain karein.",
            "mental_health":       "Mental clarity + therapy/support ka favourable phase — consistency build karein.",
            "surgery_timing":      "Cosmic backdrop supportive — surgeon se medical-window confirm karke proceed karein.",
            "recovery_timing":     "Recovery momentum positive hai — patience + protocol-adherence par focus.",
            "longevity_general":   "Vitality ke supportive cosmic signals — preventive habits (sleep, diet, check-up) consistent rakhein.",
            "injury_accident":     "Awareness rakhein but no major risk window — basic safety pe focus.",
            "addiction":           "De-addiction window favourable — professional rehab + support group join karein.",
            "female_reproductive": "Reproductive system supportive phase — gynae consult + nutrition focus.",
            "male_reproductive":   "Reproductive health stable — urologist ke saath routine check kar lein.",
            "parent_health":       "Parents ki health relatively supportive — annual check-up + emotional bonding maintain karein.",
            "general_wellness":    "Wellness routine ka best phase — habits formalise karein.",
        }
        return base.get(bucket, "Cosmic window supportive — disciplined wellness routine maintain karein.")
    if verdict == "yellow_wait":
        return ("Mixed signals — kisi bhi health decision se pehle qualified doctor "
                "se consult karein. Lifestyle discipline + preventive testing prioritise karein.")
    if verdict == "slow_burn":
        return ("Promise hai but timing slow hai — long-term commitment, consistent "
                "treatment / lifestyle discipline, aur patience zaroori hai. "
                "Quick fix expectation rakh kar mat chalein.")
    if verdict == "red_avoid":
        return ("Currently health-decision risk window hai — major elective decisions "
                "(elective surgery, drastic diet change, supplement experiments) "
                "defer karein. Existing treatment + doctor supervision par focus karein.")
    return "Doctor consultation + balanced lifestyle prioritise karein."


def _build_timing_window(kundli: dict, intel: dict,
                         sat_t: dict, mars_t: dict, jup_t: dict) -> dict:
    """Construct the must-use timing window dict from current dasha + transits.
    Returns:
      {
        current: { md, ad, pd, start, end },
        next:    { md, ad, start, end, why },
        risk:    { window_str, reason } — when transit-driven risk active
      }
    """
    md, ad, pd = _dasha_lords(kundli)
    cur_start = ""
    cur_end = ""
    cd = kundli.get("currentDasha") or {}
    cur_start = (cd.get("startDate") or cd.get("start") or "")[:10]
    cur_end = (cd.get("endDate") or cd.get("end") or "")[:10]
    if not cur_start or not cur_end:
        # Walk dashas hierarchy for AD window
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).date().isoformat()
            for top in (kundli.get("dashas") or []):
                if top.get("planet") != md: continue
                for sub in (top.get("subDashas") or []):
                    if sub.get("planet") != ad: continue
                    if str(sub.get("startDate","")) <= now <= str(sub.get("endDate","9999")):
                        cur_start = str(sub.get("startDate",""))[:10]
                        cur_end = str(sub.get("endDate",""))[:10]
                        break
                break
        except Exception:
            pass

    # Next AD window — peek into upcoming
    nxt_md, nxt_ad, nxt_start, nxt_end, why_nxt = "", "", "", "", ""
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).date().isoformat()
        seen_current = False
        for top in (kundli.get("dashas") or []):
            for sub in (top.get("subDashas") or []):
                s, e = str(sub.get("startDate",""))[:10], str(sub.get("endDate",""))[:10]
                if not s or not e: continue
                if not seen_current and s <= now <= e:
                    seen_current = True
                    continue
                if seen_current and s > now:
                    nxt_md = top.get("planet")
                    nxt_ad = sub.get("planet")
                    nxt_start = s
                    nxt_end = e
                    why_nxt = f"Next AD: {nxt_md}/{nxt_ad} ({_ym_to_human(s[:7])} → {_ym_to_human(e[:7])})"
                    break
            if nxt_ad:
                break
    except Exception:
        pass

    # Risk window — transit-driven
    risk_str = ""
    risk_reason = ""
    if sat_t and sat_t.get("sade_sati_phase") in ("peak", "ashtama"):
        risk_str = f"Saturn {sat_t.get('sade_sati_phase')} (active now)"
        risk_reason = "Sustained mental + chronic stress — extra preventive care needed."
    elif mars_t and mars_t.get("on_risk_house"):
        risk_str = f"Mars transiting {mars_t.get('mars_house_from_lagna')}H"
        risk_reason = "Accident / inflammation / surgery awareness window."

    return {
        "current": {
            "md": md, "ad": ad, "pd": pd,
            "start": cur_start, "end": cur_end,
            "lords": f"{md}/{ad}" if (md and ad) else (md or ad or ""),
        },
        "next": {
            "md": nxt_md, "ad": nxt_ad,
            "start": nxt_start, "end": nxt_end,
            "why": why_nxt,
        },
        "risk": {"window_str": risk_str, "reason": risk_reason},
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT HELPERS — verdict block for AI narrator (LOCKED FACTS)
# ─────────────────────────────────────────────────────────────────────────────
_VERDICT_HI = {
    "green_go":    "GREEN — Supportive window, disciplined wellness routine maintain karein",
    "yellow_wait": "YELLOW — Mixed signals, doctor consult + cautious approach",
    "slow_burn":   "SLOW BURN — Long-term promise, patience + consistency zaroori",
    "red_avoid":   "RED — High-risk window, defer elective decisions",
}

_BUCKET_HI = {
    "chronic_illness":     "Chronic / Long-term Bimari",
    "acute_illness":       "Acute / Sudden Illness",
    "mental_health":       "Mental Health",
    "surgery_timing":      "Surgery Timing",
    "recovery_timing":     "Recovery Timing",
    "longevity_general":   "Longevity (General)",
    "injury_accident":     "Injury / Accident Awareness",
    "addiction":           "Addiction / De-addiction",
    "female_reproductive": "Female Reproductive Health",
    "male_reproductive":   "Male Reproductive Health",
    "parent_health":       "Parent Health",
    "general_wellness":    "General Wellness",
}


def format_verdict_for_prompt(v: dict, question: str = "") -> str:
    """Build the LOCKED-FACTS block that the AI narrator MUST embed verbatim
    (no wording changes, no number changes, no verdict changes).
    Brand-safety bullets at the bottom are MANDATORY for the narrator to honour."""
    if not isinstance(v, dict):
        return "(health verdict unavailable)"

    bucket = v.get("bucket", "general_wellness")
    tense  = v.get("tense", "general")
    verdict = v.get("verdict", "yellow_wait")
    score = v.get("score", 0)
    confidence = v.get("confidence", 0)

    bucket_hi = _BUCKET_HI.get(bucket, bucket)
    verdict_hi = _VERDICT_HI.get(verdict, verdict)

    lines = []
    lines.append("════════════════════════════════════════════════════════════")
    lines.append("⭐ COSMIC HEALTH VERDICT — LOCKED FACTS (do NOT modify)")
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
        lines.append(f"   • Natal layers (25): {sb.get('layer_score',0):+d}")
        lines.append(f"   • Trigger layers (3): {sb.get('trigger_score',0):+d}")
        lines.append(f"   • Modifiers (7): {sb.get('modifier_delta',0):+d}")
        lines.append(f"   • Conditionals: {sb.get('cond_bonus',0):+d}")
        lines.append("")

    # Top reasons
    reasons = v.get("reasons") or []
    top_reasons = [r for r in reasons if "⭐" in r or "Vargottama" in r
                   or "MANDATORY" in r or "vargottama" in r][:5]
    if not top_reasons:
        top_reasons = reasons[:5]
    if top_reasons:
        lines.append("▸ TOP COSMIC FACTORS:")
        for r in top_reasons:
            lines.append(f"   • {r}")
        lines.append("")

    # Timing window — narrator MUST cite the heading line verbatim
    tw = v.get("timing_window") or {}
    cur = tw.get("current") or {}
    nxt = tw.get("next") or {}
    risk = tw.get("risk") or {}

    if cur.get("md") and cur.get("ad"):
        cur_s_h = _ym_to_human(str(cur.get("start") or "")[:7])
        cur_e_h = _ym_to_human(str(cur.get("end") or "")[:7])
        # CRITICAL: heading regex `(marriage|career|...|health) window:` —
        # MUST emit lower-case "health window:" so validator detects it.
        if cur_s_h and cur_e_h:
            lines.append(
                f"▸ Health window: {cur_s_h} → {cur_e_h} — "
                f"{cur.get('md')} Mahadasha / {cur.get('ad')} Antardasha"
            )
        else:
            lines.append(
                f"▸ Health window: {cur.get('md')} Mahadasha / "
                f"{cur.get('ad')} Antardasha (current)"
            )
        # Also surface PD (pratyantar) for narrator detail
        if cur.get("pd"):
            lines.append(
                f"   • Sub-period (Pratyantar): {cur.get('pd')}"
            )
        # Dasha aliases line (helps validator's dasha-key tolerance)
        lines.append(
            f"   • Dasha lords (verbatim): MD={cur.get('md')}, "
            f"AD={cur.get('ad')}, PD={cur.get('pd') or '-'}"
        )
    if nxt.get("md") and nxt.get("ad"):
        s_h = _ym_to_human(str(nxt.get("start") or "")[:7])
        e_h = _ym_to_human(str(nxt.get("end") or "")[:7])
        if s_h and e_h:
            lines.append(
                f"▸ Next health window: {s_h} → {e_h} — "
                f"{nxt.get('md')} Mahadasha / {nxt.get('ad')} Antardasha"
            )
    if risk.get("window_str"):
        lines.append(f"▸ ⚠ ACTIVE RISK CONTEXT: {risk.get('window_str')}")
        if risk.get("reason"):
            lines.append(f"   • {risk.get('reason')}")
    lines.append("")

    # Top concerns
    tc = v.get("top_concerns") or []
    if tc:
        lines.append("▸ TOP CONCERN AREAS (chart-level):")
        for c in tc:
            lines.append(f"   • {c.get('layer')} (signal {c.get('score')})")
        lines.append("")

    ts = v.get("top_supportive") or []
    if ts:
        lines.append("▸ TOP SUPPORTIVE FACTORS:")
        for c in ts:
            lines.append(f"   • {c.get('layer')} (signal {c.get('score')})")
        lines.append("")

    # Strategy
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
        det = rem.get("details") or {}
        if det.get("donation"):
            lines.append(f"   • Donation: {det.get('donation')}")
        if det.get("lifestyle"):
            lines.append(f"   • Lifestyle: {det.get('lifestyle')}")
        lines.append("")

    # Brand-safety guards (MANDATORY for health)
    warnings = v.get("brand_safety_warnings") or []
    if warnings:
        lines.append("▸ BRAND-SAFETY GUARDS — narrator MUST honour ALL of these:")
        for i, w in enumerate(warnings, 1):
            lines.append(f"   {i}. {w}")
        lines.append("")

    lines.append("════════════════════════════════════════════════════════════")
    lines.append("⛔ NARRATOR RULES (HEALTH — STRICT):")
    lines.append("   1. Do NOT change verdict, score, confidence, lords, or windows.")
    lines.append("   2. NEVER predict death date, life span, or 'X years left' — "
                 "even if user explicitly asks. Politely decline + redirect to "
                 "qualitative guidance.")
    lines.append("   3. NEVER diagnose specific medical conditions. NEVER replace "
                 "medical advice. ALWAYS recommend qualified doctor consult for "
                 "any serious symptom.")
    lines.append("   4. For mental-health / suicidal content — ALWAYS surface "
                 "iCall (9152987821) and Vandrevala Foundation (1860-2662-345) "
                 "free helplines.")
    lines.append("   5. Frame in TENSE detected above (PRESENT → 'abhi/aaj kal'; "
                 "FUTURE → 'aage chal kar').")
    lines.append("   6. Use 'Cosmic Intelligence' / 'cosmic signature' — "
                 "NEVER 'AI/LLM'.")
    lines.append("   7. Embed STRATEGY text verbatim (translate keywords only "
                 "if needed).")
    lines.append("   8. Honour ALL brand-safety bullets above as caveats.")
    lines.append("   9. Hinglish-first — natural code-mix preferred over pure "
                 "Hindi or pure English.")
    lines.append("════════════════════════════════════════════════════════════")

    return "\n".join(lines)


def format_final_answer(v: dict, question: str = "") -> str:
    """Compact pre-baked Hinglish answer for fallback when narrator unavailable."""
    if not isinstance(v, dict):
        return "Cosmic Intelligence se health guidance abhi available nahi hai."
    bucket = v.get("bucket", "general_wellness")
    verdict = v.get("verdict", "yellow_wait")
    score = v.get("score", 0)
    bucket_hi = _BUCKET_HI.get(bucket, bucket)
    verdict_hi = _VERDICT_HI.get(verdict, verdict)
    strat = v.get("strategy") or ""
    rem = v.get("remedy") or {}
    rem_text = rem.get("remedy_text") or ""
    tw = v.get("timing_window") or {}
    cur = tw.get("current") or {}
    win_line = ""
    if cur.get("md") and cur.get("ad"):
        s_h = _ym_to_human(str(cur.get("start") or "")[:7])
        e_h = _ym_to_human(str(cur.get("end") or "")[:7])
        if s_h and e_h:
            win_line = (f"Current window: {s_h} → {e_h} — "
                        f"{cur.get('md')} Mahadasha / {cur.get('ad')} Antardasha.")

    parts = [
        f"🌿 Cosmic Health View ({bucket_hi}):",
        f"Verdict: {verdict_hi}  •  Score: {score}/100.",
        win_line,
        strat,
        f"Remedy: {rem_text}" if rem_text else "",
        ("⚠ Yeh guidance medical advice ka VIKALP NAHI hai — kisi bhi "
         "serious symptom ke liye qualified doctor se zaroor consult karein."),
    ]
    return "\n\n".join([p for p in parts if p])
