"""
Cosmic Lens — Daily Personalised "Aaj Ka Shubh Ank" + "Aaj Ka Shubh Rang"

NO fake fallbacks. Requires:
  • birth_data.day  (mool ank source — birth date-of-month)
  • kundli.nakshatra (janma nakshatra name) — Moon's nakshatra at birth
  • date_iso (target date)
  • today_moon_lon, today_sun_lon (sidereal degrees) — for today's nakshatra +
    tithi + tara

Output:
  {
    "shubh_ank": int 1-9,
    "shubh_rang_name": str,            # Hinglish color name
    "shubh_rang_hex":  str,            # hex code for swatch
    "mool_ank":        int,            # permanent (numerology Mulank)
    "reasoning_hinglish": str,         # 1-line user-facing explanation
    "tara":              str,          # Hinglish tara name (Mitra/Vipat etc.)
    "tara_idx":          int,
    "today_nak":         str,          # Hinglish nakshatra name
    "tithi_idx":         int,          # 0-29 (1-30 in classical)
    "weekday_idx":       int           # 0=Mon .. 6=Sun
  }
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

from energy_engine import NAKSHATRAS, TARA_NAMES
from numerology.core.phase_s import (
    NUMBER_FRIENDS, NUMBER_ENEMIES, PLANET_BY_NUMBER, _root,
)

# ─── Hinglish color palette ──────────────────────────────────────────────────
# Each planet has a primary "shubh rang" — the colour to wear / surround
# yourself with on a day governed by that planet's energy (or to invoke its
# blessing when its support is needed).
PLANET_COLOR: Dict[str, Dict[str, str]] = {
    "Sun":     {"name": "Suneheri",       "hex": "#f59e0b"},   # amber gold
    "Moon":    {"name": "Safed",          "hex": "#f3f4f6"},   # off-white
    "Mars":    {"name": "Lal",            "hex": "#dc2626"},   # red
    "Mercury": {"name": "Hara",           "hex": "#16a34a"},   # green
    "Jupiter": {"name": "Pila",           "hex": "#facc15"},   # yellow
    "Venus":   {"name": "Gulabi",         "hex": "#ec4899"},   # pink
    "Saturn":  {"name": "Gehra Neela",    "hex": "#1e3a8a"},   # deep blue
    "Rahu":    {"name": "Dhuandhla",      "hex": "#6b7280"},   # smoky grey
    "Ketu":    {"name": "Bhura",          "hex": "#92400e"},   # brown
}

# Weekday → ruling planet (Mon=0 .. Sun=6, ISO weekday-1)
WEEKDAY_PLANET = ["Moon","Mars","Mercury","Jupiter","Venus","Saturn","Sun"]

# Hinglish nakshatra names for user-facing strings (we already have english
# in NAKSHATRAS — these are pronounceable Roman-Hinglish).
NAK_HINGLISH = NAKSHATRAS  # the english spellings are already used in app UI

# Hinglish tara labels (Janma..Ati Mitra) — match TARA_NAMES order.
TARA_HINGLISH = TARA_NAMES

# Tara classification — favourable vs inauspicious
TARA_FAVOURABLE_IDX = {1, 3, 5, 7, 8}   # Sampat, Kshema, Sadhana, Mitra, Ati Mitra
TARA_INAUSPICIOUS_IDX = {0, 2, 4, 6}    # Janma, Vipat, Pratyak, Naidhana


# ─── LANG-AWARE LABELS ──────────────────────────────────────────────────────
# When a UI language is supplied, we translate (a) the tara label, (b) the
# colour name, and (c) the 1-line reasoning sentence into that language so
# the entire "Aaj Ka Shubh Ank / Rang" card can render fully in-script.
#
# Languages without an entry here (or unknown codes) fall back to "hn"
# (Hinglish) — preserves prior behaviour for users who haven't switched
# language. English ("en") falls back to English copy.

# Per-lang Tara names (must match TARA_NAMES order — 9 entries each).
_LANG_TARA: Dict[str, list] = {
    "hn": ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
           "Sadhana", "Naidhana", "Mitra", "Ati Mitra"],
    "en": ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
           "Sadhana", "Naidhana", "Mitra", "Ati Mitra"],
    "hi": ["जन्म", "सम्पत्", "विपत्", "क्षेम", "प्रत्यक्",
           "साधन", "नैधन", "मित्र", "अति मित्र"],
    "or": ["ଜନ୍ମ", "ସମ୍ପତ୍", "ବିପତ୍", "କ୍ଷେମ", "ପ୍ରତ୍ୟକ୍",
           "ସାଧନ", "ନୈଧନ", "ମିତ୍ର", "ଅତି ମିତ୍ର"],
    "mr": ["जन्म", "सम्पत्", "विपत्", "क्षेम", "प्रत्यक्",
           "साधन", "नैधन", "मित्र", "अति मित्र"],
    "bn": ["জন্ম", "সম্পত্", "বিপত্", "ক্ষেম", "প্রত্যক্",
           "সাধন", "নৈধন", "মিত্র", "অতি মিত্র"],
    "ta": ["ஜன்மா", "சம்பத்", "விபத்", "க்ஷேமா", "பிரத்யக்",
           "சாதனா", "நைதனா", "மித்ரா", "அதி மித்ரா"],
    "te": ["జన్మ", "సంపత్", "విపత్", "క్షేమ", "ప్రత్యక్",
           "సాధన", "నైధన", "మిత్ర", "అతి మిత్ర"],
    "gu": ["જન્મ", "સંપત્", "વિપત્", "ક્ષેમ", "પ્રત્યક્",
           "સાધન", "નૈધન", "મિત્ર", "અતિ મિત્ર"],
    "kn": ["ಜನ್ಮ", "ಸಂಪತ್", "ವಿಪತ್", "ಕ್ಷೇಮ", "ಪ್ರತ್ಯಕ್",
           "ಸಾಧನ", "ನೈಧನ", "ಮಿತ್ರ", "ಅತಿ ಮಿತ್ರ"],
    "ml": ["ജന്മ", "സമ്പത്", "വിപത്", "ക്ഷേമ", "പ്രത്യക്",
           "സാധന", "നൈധന", "മിത്ര", "അതി മിത്ര"],
    "pa": ["ਜਨਮ", "ਸੰਪਤ੍", "ਵਿਪਤ੍", "ਖੇਮ", "ਪ੍ਰਤਿਅਕ੍",
           "ਸਾਧਨ", "ਨੈਧਨ", "ਮਿੱਤਰ", "ਅਤਿ ਮਿੱਤਰ"],
    "as": ["জন্ম", "সম্পত্", "বিপত্", "ক্ষেম", "প্ৰত্যক্",
           "সাধন", "নৈধন", "মিত্ৰ", "অতি মিত্ৰ"],
}

# Per-lang colour-name lookup keyed by the canonical Hinglish name from
# PLANET_COLOR. Hex stays the same — only the display label changes.
_LANG_COLOR_NAMES: Dict[str, Dict[str, str]] = {
    "hn": {  # default — Hinglish (matches PLANET_COLOR.name)
        "Suneheri": "Suneheri", "Safed": "Safed", "Lal": "Lal",
        "Hara": "Hara", "Pila": "Pila", "Gulabi": "Gulabi",
        "Gehra Neela": "Gehra Neela", "Dhuandhla": "Dhuandhla",
        "Bhura": "Bhura",
    },
    "en": {
        "Suneheri": "Golden", "Safed": "White", "Lal": "Red",
        "Hara": "Green", "Pila": "Yellow", "Gulabi": "Pink",
        "Gehra Neela": "Deep Blue", "Dhuandhla": "Smoky Grey",
        "Bhura": "Brown",
    },
    "hi": {
        "Suneheri": "सुनहरी", "Safed": "सफेद", "Lal": "लाल",
        "Hara": "हरा", "Pila": "पीला", "Gulabi": "गुलाबी",
        "Gehra Neela": "गहरा नीला", "Dhuandhla": "धुएँ जैसा",
        "Bhura": "भूरा",
    },
    "or": {
        "Suneheri": "ସୁନେରୀ", "Safed": "ଧଳା", "Lal": "ଲାଲ୍",
        "Hara": "ସବୁଜ", "Pila": "ହଳଦିଆ", "Gulabi": "ଗୋଲାପୀ",
        "Gehra Neela": "ଗାଢ ନୀଳ", "Dhuandhla": "ଧୂସର",
        "Bhura": "ବାଦାମୀ",
    },
    "mr": {
        "Suneheri": "सुनेरी", "Safed": "पांढरा", "Lal": "लाल",
        "Hara": "हिरवा", "Pila": "पिवळा", "Gulabi": "गुलाबी",
        "Gehra Neela": "गडद निळा", "Dhuandhla": "धुरकट",
        "Bhura": "तपकिरी",
    },
    "bn": {
        "Suneheri": "সোনালি", "Safed": "সাদা", "Lal": "লাল",
        "Hara": "সবুজ", "Pila": "হলুদ", "Gulabi": "গোলাপি",
        "Gehra Neela": "গাঢ় নীল", "Dhuandhla": "ধূসর",
        "Bhura": "বাদামী",
    },
    "ta": {
        "Suneheri": "தங்கம்", "Safed": "வெள்ளை", "Lal": "சிவப்பு",
        "Hara": "பச்சை", "Pila": "மஞ்சள்", "Gulabi": "இளஞ்சிவப்பு",
        "Gehra Neela": "அடர் நீலம்", "Dhuandhla": "சாம்பல்",
        "Bhura": "கபில",
    },
    "te": {
        "Suneheri": "బంగారు", "Safed": "తెలుపు", "Lal": "ఎరుపు",
        "Hara": "ఆకుపచ్చ", "Pila": "పసుపు", "Gulabi": "గులాబీ",
        "Gehra Neela": "ముదురు నీలం", "Dhuandhla": "బూడిద",
        "Bhura": "గోధుమ",
    },
    "gu": {
        "Suneheri": "સુનેહરી", "Safed": "સફેદ", "Lal": "લાલ",
        "Hara": "લીલો", "Pila": "પીળો", "Gulabi": "ગુલાબી",
        "Gehra Neela": "ઘેરો વાદળી", "Dhuandhla": "ધૂંધળું",
        "Bhura": "ભૂરો",
    },
    "kn": {
        "Suneheri": "ಸುವರ್ಣ", "Safed": "ಬಿಳಿ", "Lal": "ಕೆಂಪು",
        "Hara": "ಹಸಿರು", "Pila": "ಹಳದಿ", "Gulabi": "ಗುಲಾಬಿ",
        "Gehra Neela": "ಗಾಢ ನೀಲಿ", "Dhuandhla": "ಬೂದು",
        "Bhura": "ಕಂದು",
    },
    "ml": {
        "Suneheri": "സ്വർണ്ണം", "Safed": "വെള്ള", "Lal": "ചുവപ്പ്",
        "Hara": "പച്ച", "Pila": "മഞ്ഞ", "Gulabi": "പിങ്ക്",
        "Gehra Neela": "കടും നീല", "Dhuandhla": "ചാരനിറം",
        "Bhura": "തവിട്ട്",
    },
    "pa": {
        "Suneheri": "ਸੁਨਹਿਰੀ", "Safed": "ਚਿੱਟਾ", "Lal": "ਲਾਲ",
        "Hara": "ਹਰਾ", "Pila": "ਪੀਲਾ", "Gulabi": "ਗੁਲਾਬੀ",
        "Gehra Neela": "ਗੂੜ੍ਹਾ ਨੀਲਾ", "Dhuandhla": "ਧੁੰਦਲਾ",
        "Bhura": "ਭੂਰਾ",
    },
    "as": {
        "Suneheri": "সোণালী", "Safed": "বগা", "Lal": "ৰঙা",
        "Hara": "সেউজীয়া", "Pila": "হালধীয়া", "Gulabi": "গোলাপী",
        "Gehra Neela": "গাঢ় নীলা", "Dhuandhla": "ধূসৰ",
        "Bhura": "মুগা",
    },
}

# 1-line reasoning template per lang. Two variants — favourable vs stressed
# tara — both with the same {tara}/{ank}/{color} placeholders.
_LANG_REASONING: Dict[str, Dict[str, str]] = {
    "hn": {
        "fav": ("Aaj aapka nakshatra friendship '{tara}' hai — "
                "shubh ank {ank} aur {color} rang aaj ki energy ke saath align hai."),
        "str": ("Aaj nakshatra friendship '{tara}' hai — thoda sambhal ke. "
                "Shubh ank {ank} aur protective {color} rang aapko balance dega."),
    },
    "en": {
        "fav": ("Today your nakshatra friendship is '{tara}' — "
                "lucky number {ank} and {color} colour align with today's energy."),
        "str": ("Today your nakshatra friendship is '{tara}' — be a little careful. "
                "Lucky number {ank} and protective {color} colour will keep you balanced."),
    },
    "hi": {
        "fav": ("आज आपकी नक्षत्र मित्रता '{tara}' है — "
                "शुभ अंक {ank} और {color} रंग आज की ऊर्जा से मेल खाते हैं।"),
        "str": ("आज नक्षत्र मित्रता '{tara}' है — थोड़ा सावधान रहें। "
                "शुभ अंक {ank} और सुरक्षात्मक {color} रंग संतुलन देंगे।"),
    },
    "or": {
        "fav": ("ଆଜି ଆପଣଙ୍କର ନକ୍ଷତ୍ର ମିତ୍ରତା '{tara}' — "
                "ଶୁଭ ଅଙ୍କ {ank} ଏବଂ {color} ରଙ୍ଗ ଆଜିର ଶକ୍ତି ସହିତ ସମନ୍ୱୟରେ ଅଛି।"),
        "str": ("ଆଜି ନକ୍ଷତ୍ର ମିତ୍ରତା '{tara}' — ଟିକିଏ ସାବଧାନ। "
                "ଶୁଭ ଅଙ୍କ {ank} ଏବଂ ସୁରକ୍ଷାତ୍ମକ {color} ରଙ୍ଗ ଆପଣଙ୍କୁ ସନ୍ତୁଳନ ଦେବ।"),
    },
    "mr": {
        "fav": ("आज तुमची नक्षत्र मित्रता '{tara}' आहे — "
                "शुभ अंक {ank} आणि {color} रंग आजच्या ऊर्जेशी जुळतात."),
        "str": ("आज नक्षत्र मित्रता '{tara}' आहे — थोडे सावध राहा. "
                "शुभ अंक {ank} आणि संरक्षणात्मक {color} रंग संतुलन देतील."),
    },
    "bn": {
        "fav": ("আজ আপনার নক্ষত্র মিত্রতা '{tara}' — "
                "শুভ সংখ্যা {ank} এবং {color} রঙ আজকের শক্তির সাথে সঙ্গতিপূর্ণ।"),
        "str": ("আজ নক্ষত্র মিত্রতা '{tara}' — একটু সতর্ক থাকুন। "
                "শুভ সংখ্যা {ank} এবং রক্ষাকারী {color} রঙ আপনাকে ভারসাম্য দেবে।"),
    },
    "ta": {
        "fav": ("இன்று உங்கள் நட்சத்திர நட்பு '{tara}' — "
                "அதிர்ஷ்ட எண் {ank} மற்றும் {color} நிறம் இன்றைய சக்தியுடன் ஒத்துப்போகின்றன."),
        "str": ("இன்று நட்சத்திர நட்பு '{tara}' — கொஞ்சம் கவனமாக இருங்கள். "
                "அதிர்ஷ்ட எண் {ank} மற்றும் பாதுகாப்பு {color} நிறம் சமநிலை தரும்."),
    },
    "te": {
        "fav": ("ఈరోజు మీ నక్షత్ర మిత్రత '{tara}' — "
                "శుభ సంఖ్య {ank} మరియు {color} రంగు నేటి శక్తికి అనుగుణంగా ఉన్నాయి."),
        "str": ("ఈరోజు నక్షత్ర మిత్రత '{tara}' — కొంచెం జాగ్రత్తగా ఉండండి. "
                "శుభ సంఖ్య {ank} మరియు రక్షణాత్మక {color} రంగు సమతుల్యత ఇస్తాయి."),
    },
    "gu": {
        "fav": ("આજે તમારી નક્ષત્ર મિત્રતા '{tara}' છે — "
                "શુભ અંક {ank} અને {color} રંગ આજની ઊર્જા સાથે મેળ ખાય છે."),
        "str": ("આજે નક્ષત્ર મિત્રતા '{tara}' છે — થોડું સાવધ રહો. "
                "શુભ અંક {ank} અને રક્ષણાત્મક {color} રંગ સંતુલન આપશે."),
    },
    "kn": {
        "fav": ("ಇಂದು ನಿಮ್ಮ ನಕ್ಷತ್ರ ಮೈತ್ರಿ '{tara}' — "
                "ಶುಭ ಸಂಖ್ಯೆ {ank} ಮತ್ತು {color} ಬಣ್ಣ ಇಂದಿನ ಶಕ್ತಿಯೊಂದಿಗೆ ಹೊಂದಾಣಿಕೆಯಾಗಿವೆ."),
        "str": ("ಇಂದು ನಕ್ಷತ್ರ ಮೈತ್ರಿ '{tara}' — ಸ್ವಲ್ಪ ಎಚ್ಚರವಿರಲಿ. "
                "ಶುಭ ಸಂಖ್ಯೆ {ank} ಮತ್ತು ರಕ್ಷಣಾತ್ಮಕ {color} ಬಣ್ಣ ಸಮತೋಲನ ನೀಡುತ್ತದೆ."),
    },
    "ml": {
        "fav": ("ഇന്ന് നിങ്ങളുടെ നക്ഷത്ര സൗഹൃദം '{tara}' — "
                "ഭാഗ്യ സംഖ്യ {ank}, {color} നിറം ഇന്നത്തെ ഊർജ്ജവുമായി യോജിക്കുന്നു."),
        "str": ("ഇന്ന് നക്ഷത്ര സൗഹൃദം '{tara}' — അല്പം ജാഗ്രതയോടെ. "
                "ഭാഗ്യ സംഖ്യ {ank}, സംരക്ഷക {color} നിറം സന്തുലനം നൽകും."),
    },
    "pa": {
        "fav": ("ਅੱਜ ਤੁਹਾਡੀ ਨਛੱਤਰ ਮਿੱਤਰਤਾ '{tara}' ਹੈ — "
                "ਸ਼ੁਭ ਅੰਕ {ank} ਅਤੇ {color} ਰੰਗ ਅੱਜ ਦੀ ਊਰਜਾ ਨਾਲ ਮੇਲ ਖਾਂਦੇ ਹਨ।"),
        "str": ("ਅੱਜ ਨਛੱਤਰ ਮਿੱਤਰਤਾ '{tara}' ਹੈ — ਥੋੜ੍ਹਾ ਸਾਵਧਾਨ ਰਹੋ। "
                "ਸ਼ੁਭ ਅੰਕ {ank} ਅਤੇ ਸੁਰੱਖਿਆਤਮਕ {color} ਰੰਗ ਸੰਤੁਲਨ ਦੇਣਗੇ।"),
    },
    "as": {
        "fav": ("আজি আপোনাৰ নক্ষত্ৰ মিত্ৰতা '{tara}' — "
                "শুভ সংখ্যা {ank} আৰু {color} ৰং আজিৰ শক্তিৰ সৈতে মিল খায়।"),
        "str": ("আজি নক্ষত্ৰ মিত্ৰতা '{tara}' — অলপ সাৱধান হওক। "
                "শুভ সংখ্যা {ank} আৰু সুৰক্ষাত্মক {color} ৰং সন্তুলন দিব।"),
    },
}


def _resolve_lang(lang: Optional[str]) -> str:
    """Coerce arbitrary lang code to a supported one.

    Supported set: 13 Indian UI langs (hn, en, hi, or, mr, bn, ta, te, gu,
    kn, ml, pa, as). For unsupported global UI langs (zh, es, ar, fr, pt,
    de, ru, ja, id, ko, tr) we fall back to **English**, NOT Hinglish —
    this keeps the lucky tile consistent with the frontend i18n which also
    falls back to English labels for those global langs (no
    "English headers + Hinglish body" mismatch).

    `None` / blank is treated as "no preference" → defaults to 'hn' for
    backward compatibility with old callers that don't plumb a lang code.
    """
    if not lang:
        return "hn"
    code = str(lang).strip().lower()
    if code in _LANG_REASONING:
        return code
    return "en"


def _tithi_idx(moon_lon: float, sun_lon: float) -> int:
    """Tithi index 0-29 from moon-sun longitude difference."""
    diff = (moon_lon - sun_lon) % 360.0
    return int(diff // 12.0) % 30


def _today_nak_idx(moon_lon: float) -> int:
    return int(moon_lon // (360.0 / 27.0)) % 27


def _birth_nak_idx(kundli: Dict[str, Any]) -> int:
    """Resolve janma nakshatra from saved kundli. -1 if not found."""
    nak_name = kundli.get("nakshatra")
    if not nak_name and isinstance(kundli.get("chart_data"), dict):
        nak_name = kundli["chart_data"].get("nakshatra")
    if isinstance(nak_name, str) and nak_name in NAKSHATRAS:
        return NAKSHATRAS.index(nak_name)
    # Fallback: derive from Moon's longitude in saved planets
    planets = kundli.get("planets") or (kundli.get("chart_data") or {}).get("planets") or []
    for p in planets:
        if isinstance(p, dict) and (p.get("name") == "Moon"):
            lon = p.get("lon") or p.get("longitude")
            if isinstance(lon, (int, float)):
                return int(float(lon) // (360.0 / 27.0)) % 27
    return -1


def _mool_ank_from_birth(*sources: Dict[str, Any]) -> Optional[int]:
    """Mool ank (Mulank) = digital root of birth-day (1..31 → 1..9).

    Accepts any number of dict sources (e.g. profile.birth_data, kundli) and
    returns the first valid mool ank found.
    """
    DATE_FORMATS = (
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y",
        "%d %b %Y", "%d %B %Y",          # "15 Jan 1990"
        "%b %d %Y", "%B %d %Y",
    )
    for src in sources:
        if not isinstance(src, dict):
            continue
        day = src.get("day")
        if day is None:
            for key in ("dob", "birth_date", "date"):
                v = src.get(key)
                if isinstance(v, str):
                    for fmt in DATE_FORMATS:
                        try:
                            day = datetime.strptime(v.strip(), fmt).day
                            break
                        except Exception:
                            continue
                    if day is not None:
                        break
        try:
            d = int(day)
            if 1 <= d <= 31:
                return _root(d)
        except (TypeError, ValueError):
            continue
    return None


def compute_daily_lucky(
    birth_data: Dict[str, Any],
    kundli: Dict[str, Any],
    date_iso: str,
    moon_lon: float,
    sun_lon: float,
    lang: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns {ok: True, ...} on success or {ok: False, error, message} on
    missing data. NEVER returns fake/placeholder values.
    """
    # ── 1. Mool ank (permanent) ──────────────────────────────────────────
    # Fall back to kundli's own dob field if profile birth_data is missing.
    mool_ank = _mool_ank_from_birth(birth_data, kundli)
    if mool_ank is None:
        return {"ok": False,
                "error": "no_birth_day",
                "message": "Birth date missing — kundli mein janam ki tareekh nahi mili."}

    # ── 2. Janma nakshatra (from saved kundli) ───────────────────────────
    birth_nak = _birth_nak_idx(kundli)
    if birth_nak < 0:
        return {"ok": False,
                "error": "no_birth_nakshatra",
                "message": "Janam ka nakshatra nahi mila — kundli regenerate karein."}

    # ── 3. Date-driven inputs ────────────────────────────────────────────
    try:
        d = datetime.strptime(date_iso, "%Y-%m-%d")
    except Exception:
        return {"ok": False,
                "error": "bad_date",
                "message": "Date format galat hai (YYYY-MM-DD chahiye)."}

    weekday_idx = d.weekday()                          # 0=Mon..6=Sun
    today_nak   = _today_nak_idx(moon_lon)             # 0..26
    tithi_idx   = _tithi_idx(moon_lon, sun_lon)        # 0..29
    tara_idx    = (today_nak - birth_nak) % 9          # 0..8

    # ── 4. Lucky number — pick from mool_ank's friends, seeded by today ─
    friends = NUMBER_FRIENDS.get(mool_ank, [mool_ank])[:]
    enemies = set(NUMBER_ENEMIES.get(mool_ank, []))
    # Always exclude enemies (defensive — not in stock friends list either)
    friends = [n for n in friends if n not in enemies] or [mool_ank]

    seed = (mool_ank + today_nak + tithi_idx + weekday_idx + tara_idx)

    if tara_idx in TARA_INAUSPICIOUS_IDX:
        # Inauspicious tara → prefer a friend that's NOT mool_ank itself
        # (don't double-down on a stressed natal energy).
        non_self = [n for n in friends if n != mool_ank]
        pool = non_self or friends
    else:
        pool = friends
    shubh_ank = pool[seed % len(pool)]

    # ── 5. Lucky color ──────────────────────────────────────────────────
    if tara_idx in TARA_FAVOURABLE_IDX:
        # Favourable day → wear the day-lord's color to amplify
        rang_planet = WEEKDAY_PLANET[weekday_idx]
        rang_reason = "amplify"
    else:
        # Stressed day → wear your mool ank planet's color for protection
        rang_planet = PLANET_BY_NUMBER.get(mool_ank, WEEKDAY_PLANET[weekday_idx])
        rang_reason = "protect"
    color = PLANET_COLOR.get(rang_planet, PLANET_COLOR["Jupiter"])

    # ── 6. Reasoning (1 line) — Hinglish kept for backward compat,
    #       lang-aware copy returned in `reasoning_text` + `reasoning_lang`.
    tara_name_hn = TARA_HINGLISH[tara_idx]              # always Hinglish
    color_name_hn = color["name"]                        # always Hinglish

    if tara_idx in TARA_FAVOURABLE_IDX:
        reasoning_hn = (f"Aaj aapka nakshatra friendship '{tara_name_hn}' hai — "
                        f"shubh ank {shubh_ank} aur {color_name_hn} rang aaj ki "
                        f"energy ke saath align hai.")
    else:
        reasoning_hn = (f"Aaj nakshatra friendship '{tara_name_hn}' hai — thoda "
                        f"sambhal ke. Shubh ank {shubh_ank} aur protective "
                        f"{color_name_hn} rang aapko balance dega.")

    # Lang-aware copies (fall back to "hn" for unsupported lang codes).
    lang_code = _resolve_lang(lang)
    tara_name_local = _LANG_TARA.get(lang_code, _LANG_TARA["hn"])[tara_idx]
    color_name_local = _LANG_COLOR_NAMES.get(lang_code, _LANG_COLOR_NAMES["hn"]) \
        .get(color_name_hn, color_name_hn)
    tmpl_pack = _LANG_REASONING.get(lang_code, _LANG_REASONING["hn"])
    tmpl_key = "fav" if tara_idx in TARA_FAVOURABLE_IDX else "str"
    reasoning_local = tmpl_pack[tmpl_key].format(
        tara=tara_name_local, ank=shubh_ank, color=color_name_local,
    )

    return {
        "ok": True,
        "shubh_ank":            shubh_ank,
        "shubh_rang_name":      color_name_hn,        # Hinglish (compat)
        "shubh_rang_name_local": color_name_local,    # lang-aware display name
        "shubh_rang_hex":       color["hex"],
        "shubh_rang_intent":    rang_reason,          # "amplify" | "protect"
        "mool_ank":             mool_ank,
        "reasoning_hinglish":   reasoning_hn,         # legacy field
        "reasoning_text":       reasoning_local,      # NEW — lang-aware
        "reasoning_lang":       lang_code,
        "tara":                 tara_name_hn,         # Hinglish (compat)
        "tara_local":           tara_name_local,      # lang-aware
        "tara_idx":             tara_idx,
        "today_nakshatra":      NAK_HINGLISH[today_nak],
        "today_nak_idx":        today_nak,
        "tithi_idx":            tithi_idx,
        "weekday_idx":          weekday_idx,
        "date":                 date_iso,
    }
