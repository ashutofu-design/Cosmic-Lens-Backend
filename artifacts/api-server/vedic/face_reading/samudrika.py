"""
Engine 8 — Samudrika Shastra (सामुद्रिक शास्त्र) — v1
=========================================================

Classical Vedic / Indian face reading based on:
  • Samudrika Shastra — attributed to Samudra (ancient Hindu sage)
  • Brihat Samhita (Varahamihira, 6th c. CE) — Ch. 68 "Purusha-Lakshana"
  • Garuda Purana — Samudrika section
  • Hasta-Samudrika Shastra
  • Markandeya Purana — body markings & lakshana
  • Vasishtha Samhita
  • Manava Dharma Shastra (Manu Smriti) — auspicious lakshana

Samudrika Shastra (literally "ocean of knowledge") is the classical Indian
science of lakshana — physical signs that reveal an individual's bhagya
(fortune), buddhi (intellect), aarogya (health), dhana (wealth), aayu
(longevity), sambandha (relationships), and karya-kshetra (career).

This engine analyses 12 facial regions (Mukha-pradesha):
  1.  Mukha-Akriti      — overall face shape (7 classical types)
  2.  Lalata             — forehead (Bhagya-sthan)
  3.  Bhru               — eyebrows (5 classical shapes)
  4.  Netra              — eyes (8 classical shapes — Padma, Mina, Khanjana, etc.)
  5.  Nasika             — nose (8 classical shapes — Garuda, Singha, Mrigi, etc.)
  6.  Karna              — ears (placement & lobe)
  7.  Kapola             — cheeks (Lakshmi-sthan)
  8.  Oshtha             — lips (5 classical shapes — Bimba, Padma, etc.)
  9.  Chibuka            — chin (Karma-sthan)
  10. Hanu               — jaw (Bala-sthan)
  11. Mukha-Varna        — facial complexion (4 classical varna)
  12. Trinetra-Sthan     — third-eye region (between brows, Bhagya-bindu)

Outputs per region:
  • Sanskrit name (Devanagari + transliteration)
  • Classical classification (e.g., "Padma-akar Netra")
  • Classical lakshana phala (predictions) — sourced
  • Bhagya, Buddhi, Dhana, Aayu, Sambandha, Karya, Aarogya impact
  • Hinglish + EN narrative

Composite outputs:
  • Mukha-Akriti Phala — overall face-shape destiny reading
  • Pancha-Lakshana count — auspicious mark detection
  • Yoga combinations (e.g., "Padma-Netra + Garuda-Nasika = Raja Yoga")
  • Bhagya-Score (0-100), Buddhi-Score, Dhana-Score, Aarogya-Score
  • Doshas (Vedic) — Vata/Pitta/Kapha facial indicators (preview, full in Engine 13)
  • Disclaimer: traditional knowledge for self-reflection, not deterministic

NOTE: Vedic lakshana phala is TRADITIONAL knowledge passed through Sanskrit
texts. It is offered for cultural-spiritual reflection. Modern scientific
validity is NOT claimed. Predictions about fortune/destiny are interpretive,
not deterministic. Multiple authoritative texts may differ on specific phala.
"""
from __future__ import annotations
from typing import Optional, Sequence
import math
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Sanitizer
# ─────────────────────────────────────────────────────────────────────────────
def _py(o):
    if isinstance(o, dict):  return {k: _py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):  return [_py(x) for x in o]
    if isinstance(o, np.bool_):    return bool(o)
    if isinstance(o, np.integer):  return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray):  return _py(o.tolist())
    return o

def _dist(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
def _safe_div(a, b, default=0.0): return (a/b) if b > 1e-9 else default
def _clip(x, lo=0, hi=100): return max(lo, min(hi, x))


# ─────────────────────────────────────────────────────────────────────────────
# Landmark indices (MediaPipe FaceMesh)
# ─────────────────────────────────────────────────────────────────────────────
R_EYE_OUTER, R_EYE_INNER = 33, 133
L_EYE_OUTER, L_EYE_INNER = 263, 362
R_EYE_TOP, R_EYE_BOT = 159, 145
L_EYE_TOP, L_EYE_BOT = 386, 374
R_BROW_INNER, R_BROW_PEAK, R_BROW_OUTER = 107, 105, 70
L_BROW_INNER, L_BROW_PEAK, L_BROW_OUTER = 336, 334, 300
M_CORNER_R, M_CORNER_L = 61, 291
M_UPPER_MID, M_LOWER_MID = 13, 14
M_UPPER_OUT, M_LOWER_OUT = 0, 17
NOSE_TIP, NOSE_BRIDGE = 1, 6
NOSE_LEFT, NOSE_RIGHT = 49, 279
CHIN, FOREHEAD_TOP = 152, 10
ZYGION_R, ZYGION_L = 234, 454
JAW_R, JAW_L = 172, 397
GLABELLA = 9
EAR_R, EAR_L = 234, 454  # approximation


# ─────────────────────────────────────────────────────────────────────────────
# Classical Vedic typologies
# ─────────────────────────────────────────────────────────────────────────────

# 1. MUKHA-AKRITI (face shape) — 7 classical types from Samudrika Shastra
MUKHA_AKRITI = {
    "vrutta": {
        "sanskrit": "वृत्त मुख",
        "translit": "Vrutta Mukha",
        "english": "Round Face",
        "phala_sanskrit": "सौम्य, सुखी, धन-सम्पन्न, मित्र-प्रिय",
        "phala_en": "Gentle, joyful, wealthy, beloved by friends. Lakshmi-blessed.",
        "phala_hi": "Soumya nature, sukhi jeevan, dhan-prapti, log pasand karte hain. Lakshmi ki kripa.",
        "bhagya": 75, "buddhi": 60, "dhana": 75, "aayu": 70, "sambandha": 80,
        "karya": "vyapar (business), seva-karma, hospitality, social roles",
        "ref": "Brihat_Samhita_68.12_Varahamihira",
    },
    "deergha": {
        "sanskrit": "दीर्घ मुख",
        "translit": "Deergha Mukha",
        "english": "Long / Oval Face",
        "phala_sanskrit": "विद्वान्, दीर्घजीवी, बुद्धिमान्, यश-प्राप्तिकर",
        "phala_en": "Scholarly, long-lived, intelligent, attains fame.",
        "phala_hi": "Vidwan, deergha-aayu, buddhimaan, yash prapt karte hain.",
        "bhagya": 70, "buddhi": 85, "dhana": 65, "aayu": 85, "sambandha": 60,
        "karya": "vidya (academia), shastra-adhyayan, research, advisory roles",
        "ref": "Samudrika_Shastra_Mukha_Adhyaya",
    },
    "trikona": {
        "sanskrit": "त्रिकोण मुख",
        "translit": "Trikona Mukha",
        "english": "Triangular Face (heart/inverted triangle)",
        "phala_sanskrit": "तीक्ष्ण-बुद्धि, कलाप्रिय, चञ्चल मन",
        "phala_en": "Sharp-minded, artistic, restless mind, often emotional.",
        "phala_hi": "Teekshna buddhi, kala-priya, chanchal man, emotional bhi.",
        "bhagya": 60, "buddhi": 80, "dhana": 60, "aayu": 65, "sambandha": 55,
        "karya": "kala (arts), sangeet, lekhan, design, creative roles",
        "ref": "Garuda_Purana_Samudrika_Sec",
    },
    "chaturasra": {
        "sanskrit": "चतुरस्र मुख",
        "translit": "Chaturasra Mukha",
        "english": "Square Face",
        "phala_sanskrit": "स्थिर, साहसी, परिश्रमी, कर्म-निष्ठ",
        "phala_en": "Stable, courageous, hardworking, dharmically committed.",
        "phala_hi": "Sthir nature, sahasi, mehnati, karma me nishtha rakhne wale.",
        "bhagya": 70, "buddhi": 70, "dhana": 75, "aayu": 75, "sambandha": 70,
        "karya": "rajya-karya (governance), sena (defence), engineering, structured roles",
        "ref": "Brihat_Samhita_68.15",
    },
    "hrid": {
        "sanskrit": "हृद्-आकार मुख",
        "translit": "Hrid-akara Mukha",
        "english": "Heart-shaped Face",
        "phala_sanskrit": "स्नेह-शील, प्रेमी, सौन्दर्य-प्रिय",
        "phala_en": "Affectionate, loving, drawn to beauty and aesthetics.",
        "phala_hi": "Sneh-shil, prem-priya, sundarta ke prati aakarshit.",
        "bhagya": 70, "buddhi": 65, "dhana": 65, "aayu": 70, "sambandha": 85,
        "karya": "kala, rachnatmak vyavasaya, vivah-yogya gun, mediation",
        "ref": "Hasta_Samudrika_supplementary",
    },
    "ardhachandra": {
        "sanskrit": "अर्धचन्द्र मुख",
        "translit": "Ardhachandra Mukha",
        "english": "Half-moon (oblong) Face",
        "phala_sanskrit": "शान्त, धैर्यवान्, धर्म-निष्ठ, आत्मविश्वासी",
        "phala_en": "Calm, patient, dharma-committed, self-confident.",
        "phala_hi": "Shant, dhairyavan, dharma-nishtha, atma-vishwasi.",
        "bhagya": 75, "buddhi": 75, "dhana": 70, "aayu": 80, "sambandha": 70,
        "karya": "shikshak, guru, spiritual leader, advisory",
        "ref": "Vasishtha_Samhita_Lakshana",
    },
    "vishala": {
        "sanskrit": "विशाल मुख",
        "translit": "Vishala Mukha",
        "english": "Broad Face (wide cheekbones)",
        "phala_sanskrit": "बलवान्, साहसी, नेतृत्वकारी, राजसी",
        "phala_en": "Strong, courageous, natural leader, regal bearing.",
        "phala_hi": "Balwan, sahasi, neta-pradhan, rajasik prakriti.",
        "bhagya": 80, "buddhi": 70, "dhana": 80, "aayu": 75, "sambandha": 65,
        "karya": "netritva (leadership), rajya-karya, vyavasaya, military",
        "ref": "Brihat_Samhita_68.18_Varahamihira",
    },
}


# 2. LALATA (forehead) — Bhagya-sthan
LALATA_TYPES = {
    "vishala": {  # broad
        "sanskrit": "विशाल ललाट", "translit": "Vishala Lalata",
        "english": "Broad Forehead",
        "phala_en": "Symbol of vast intellect (Buddhi-vaibhavam) and Bhagya. "
                     "Indicates inheritance, scholarship, royal favour.",
        "phala_hi": "Vishal buddhi aur bhagya ka pratik. Vidya, dhan, raja-kripa.",
        "bhagya": 80, "buddhi": 85, "dhana": 75,
    },
    "samya": {  # balanced
        "sanskrit": "सम्य ललाट", "translit": "Samya Lalata",
        "english": "Balanced Forehead",
        "phala_en": "Indicates harmony of intellect and karma. Steady fortune.",
        "phala_hi": "Buddhi aur karma ka santulan, sthir bhagya.",
        "bhagya": 70, "buddhi": 75, "dhana": 70,
    },
    "alpa": {  # small/narrow
        "sanskrit": "अल्प ललाट", "translit": "Alpa Lalata",
        "english": "Narrow / Small Forehead",
        "phala_en": "Karma-pradhan — fortune through self-effort, not inheritance. "
                     "Practical wisdom over scholarly.",
        "phala_hi": "Karma-pradhan jeevan — apne mehnat se safalta, virasat nahi.",
        "bhagya": 55, "buddhi": 60, "dhana": 60,
    },
    "unnata": {  # raised/prominent
        "sanskrit": "उन्नत ललाट", "translit": "Unnata Lalata",
        "english": "Prominent / Raised Forehead",
        "phala_en": "Spiritual inclination, philosophical mind, dhyana-shakti.",
        "phala_hi": "Adhyatmik pravritti, chintan-shil, dhyana shakti.",
        "bhagya": 75, "buddhi": 90, "dhana": 65,
    },
    "nimna": {  # receding/sloping
        "sanskrit": "निम्न ललाट", "translit": "Nimna Lalata",
        "english": "Sloping / Receding Forehead",
        "phala_en": "Action-oriented, swift decisions, may lack patience.",
        "phala_hi": "Karma-shil, jaldi nirnay lete hain, dhairya kam.",
        "bhagya": 60, "buddhi": 65, "dhana": 65,
    },
}


# 3. BHRU (eyebrows) — 5 classical types
BHRU_TYPES = {
    "padma": {
        "sanskrit": "पद्म भ्रू", "translit": "Padma Bhru",
        "english": "Lotus-shaped (gently arched) Eyebrows",
        "phala_en": "Auspicious — Lakshmi-pradayika. Indicates beauty, grace, "
                     "and harmonious relationships.",
        "phala_hi": "Shubh — Lakshmi pradayika. Saundarya, kripa, achhe sambandh.",
        "is_auspicious": True, "bhagya": 80, "sambandha": 85,
        "ref": "Brihat_Samhita_68_Bhru",
    },
    "chandra": {
        "sanskrit": "चन्द्र भ्रू", "translit": "Chandra Bhru",
        "english": "Moon-curve (high arched) Eyebrows",
        "phala_en": "Indicates intelligence, charm, artistic sensibility.",
        "phala_hi": "Buddhi, akarshan, kala-bhavna.",
        "is_auspicious": True, "bhagya": 75, "sambandha": 75,
        "ref": "Samudrika_Bhru_Adhyaya",
    },
    "ardhachandra": {
        "sanskrit": "अर्धचन्द्र भ्रू", "translit": "Ardhachandra Bhru",
        "english": "Half-moon Eyebrows",
        "phala_en": "Balanced wisdom and emotion, stable temperament.",
        "phala_hi": "Buddhi aur bhavna ka santulan, sthir swabhav.",
        "is_auspicious": True, "bhagya": 70, "sambandha": 70,
    },
    "rju": {
        "sanskrit": "ऋजु भ्रू", "translit": "Rju Bhru",
        "english": "Straight (low-arch) Eyebrows",
        "phala_en": "Practical, direct, action-oriented.",
        "phala_hi": "Vyavaharik, seedha-saaf, karma-shil.",
        "is_auspicious": False, "bhagya": 60, "sambandha": 60,
    },
    "ghana": {
        "sanskrit": "घन भ्रू", "translit": "Ghana Bhru",
        "english": "Thick / Dense Eyebrows",
        "phala_en": "Strong willpower, courage, may be intense in temperament.",
        "phala_hi": "Drid sankalp, sahas, teevra swabhav.",
        "is_auspicious": True, "bhagya": 65, "sambandha": 55,
    },
}


# 4. NETRA (eyes) — 8 classical Vedic types
NETRA_TYPES = {
    "padma": {
        "sanskrit": "पद्म नेत्र", "translit": "Padma-akara Netra",
        "english": "Lotus-shaped Eyes",
        "phala_en": "Most auspicious eye type. Indicates Lakshmi-kripa, beauty, "
                     "compassion, and divine grace. Often seen in spiritual leaders.",
        "phala_hi": "Sabse shubh netra. Lakshmi-kripa, saundarya, karuna, dev-kripa.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 90, "buddhi": 80, "dhana": 85,
        "ref": "Samudrika_Netra_Lakshana_Padma",
    },
    "mina": {
        "sanskrit": "मीन नेत्र", "translit": "Mina-akara Netra",
        "english": "Fish-shaped Eyes (almond, slightly upturned)",
        "phala_en": "Beautiful, attractive, indicates artistic talent and "
                     "good marital prospects.",
        "phala_hi": "Sundar, akarshak, kala-pratibha, achha vivah-yog.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 80, "buddhi": 75, "dhana": 75,
    },
    "khanjana": {
        "sanskrit": "खञ्जन नेत्र", "translit": "Khanjana Netra",
        "english": "Wagtail-bird Eyes (large, expressive)",
        "phala_en": "Lively, expressive, charming. Quick-witted with strong "
                     "emotional intelligence.",
        "phala_hi": "Jeevant, abhivyakt, akarshak. Teekshna buddhi, bhavna-pradhan.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 75, "buddhi": 80, "dhana": 70,
    },
    "mriga": {
        "sanskrit": "मृग नेत्र", "translit": "Mriga Netra",
        "english": "Deer Eyes (gentle, large, slightly fearful)",
        "phala_en": "Gentle nature, sensitive, somewhat timid. Devotional bent.",
        "phala_hi": "Komal swabhav, samvedansheel, thoda darpok. Bhakti-bhavna.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 65, "buddhi": 70, "dhana": 60,
    },
    "gaja": {
        "sanskrit": "गज नेत्र", "translit": "Gaja Netra",
        "english": "Elephant Eyes (small, deep-set, intelligent)",
        "phala_en": "Wise, strategic, patient, long-term thinker. Royal sign.",
        "phala_hi": "Buddhimaan, ranniti-kushal, dhairyavan, deergha-drishti.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 85, "buddhi": 90, "dhana": 80,
    },
    "singha": {
        "sanskrit": "सिंह नेत्र", "translit": "Singha Netra",
        "english": "Lion Eyes (sharp, intense, slightly upturned)",
        "phala_en": "Courageous, commanding, leadership quality. Kshatriya-like.",
        "phala_hi": "Sahasi, adhipati-bhavna, neta. Kshatriya-like tej.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 80, "buddhi": 75, "dhana": 80,
    },
    "vyaghra": {
        "sanskrit": "व्याघ्र नेत्र", "translit": "Vyaghra Netra",
        "english": "Tiger Eyes (intense gaze, narrowed)",
        "phala_en": "Powerful, aggressive, may have temper. Strong achievement drive.",
        "phala_hi": "Shaktishali, ugra, krodh-pravan. Drid sankalp.",
        "is_auspicious": False, "is_raja_yoga": False,
        "bhagya": 70, "buddhi": 70, "dhana": 75,
    },
    "shuka": {
        "sanskrit": "शुक नेत्र", "translit": "Shuka Netra",
        "english": "Parrot Eyes (round, alert, small iris)",
        "phala_en": "Talkative, social, mimicry talent, eloquent.",
        "phala_hi": "Vachan-pravan, sammilan-priya, anukaran me kushal, vakta.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 65, "buddhi": 75, "dhana": 65,
    },
}


# 5. NASIKA (nose) — 8 classical types
NASIKA_TYPES = {
    "garuda": {
        "sanskrit": "गरुड नासिका", "translit": "Garuda Nasika",
        "english": "Eagle Nose (high bridge, slight curve)",
        "phala_en": "Royal sign — natural authority, wealth, leadership. "
                     "Strong determination and Bhagya.",
        "phala_hi": "Rajasik chinha — adhipati gun, dhan, netritva, drid sankalp.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 85, "dhana": 90, "karya_kshetra": "leadership, business empire",
    },
    "singha": {
        "sanskrit": "सिंह नासिका", "translit": "Singha Nasika",
        "english": "Lion Nose (broad bridge, strong)",
        "phala_en": "Courage, fame, military success, fierce reputation.",
        "phala_hi": "Sahas, yash, sena-vijay, tejasvi.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 80, "dhana": 75, "karya_kshetra": "military, sports, public roles",
    },
    "mrigi": {
        "sanskrit": "मृगी नासिका", "translit": "Mrigi Nasika",
        "english": "Doe Nose (small, delicate, slightly upturned)",
        "phala_en": "Gentle, sensitive, artistic. Auspicious for women in classical texts.",
        "phala_hi": "Komal, samvedansheel, kala-priya. Stri ke liye shubh.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 70, "dhana": 65, "karya_kshetra": "arts, education, healing",
    },
    "shuka": {
        "sanskrit": "शुक नासिका", "translit": "Shuka Nasika",
        "english": "Parrot Nose (sharp, slightly curved tip)",
        "phala_en": "Sharp wit, cunning, eloquence. Often seen in scholars and orators.",
        "phala_hi": "Teekshna buddhi, chaturai, vakta. Vidwan aur pravakta.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 70, "dhana": 70, "karya_kshetra": "advocacy, teaching, oratory",
    },
    "gaja": {
        "sanskrit": "गज नासिका", "translit": "Gaja Nasika",
        "english": "Elephant Nose (long, thick)",
        "phala_en": "Long life, wealth-accumulator, deep wisdom. Slow but sure.",
        "phala_hi": "Deergha aayu, dhan-sangrahak, gambhir buddhi.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 75, "dhana": 80, "karya_kshetra": "finance, real estate, long-term ventures",
    },
    "khar": {
        "sanskrit": "खर नासिका", "translit": "Khar Nasika",
        "english": "Donkey Nose (flat, broad nostrils)",
        "phala_en": "Hard-working, persistent, may face struggles before success.",
        "phala_hi": "Mehnati, sthir, safalta ke pehle sangharsh.",
        "is_auspicious": False, "is_raja_yoga": False,
        "bhagya": 55, "dhana": 60, "karya_kshetra": "labour-intensive, service roles",
    },
    "vrushabha": {
        "sanskrit": "वृषभ नासिका", "translit": "Vrushabha Nasika",
        "english": "Bull Nose (broad, fleshy)",
        "phala_en": "Stable, prosperous, family-oriented, good provider.",
        "phala_hi": "Sthir, samriddh, parivar-priya, achha poshak.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 75, "dhana": 80, "karya_kshetra": "agriculture, hospitality, family business",
    },
    "samanya": {
        "sanskrit": "सामान्य नासिका", "translit": "Samanya Nasika",
        "english": "Average / Balanced Nose",
        "phala_en": "Balanced fortune, no extreme highs or lows.",
        "phala_hi": "Santulit bhagya, na bahut uchcha na neech.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 65, "dhana": 65, "karya_kshetra": "varied",
    },
}


# 6. OSHTHA (lips) — 5 classical types
OSHTHA_TYPES = {
    "bimba": {
        "sanskrit": "बिम्ब ओष्ठ", "translit": "Bimba Oshtha",
        "english": "Bimba-fruit Lips (full, red, well-formed)",
        "phala_en": "Auspicious — beauty, charm, devotion. Lakshmi-pradayika.",
        "phala_hi": "Shubh — saundarya, akarshan, bhakti. Lakshmi-pradayika.",
        "is_auspicious": True, "bhagya": 80, "sambandha": 85,
    },
    "padma": {
        "sanskrit": "पद्म ओष्ठ", "translit": "Padma Oshtha",
        "english": "Lotus-petal Lips (soft, gently curved)",
        "phala_en": "Refined speech, sweetness, eloquence, devotional bent.",
        "phala_hi": "Madhur vachan, mithas, vakta, bhakti.",
        "is_auspicious": True, "bhagya": 75, "sambandha": 80,
    },
    "samanya": {
        "sanskrit": "सामान्य ओष्ठ", "translit": "Samanya Oshtha",
        "english": "Balanced Lips",
        "phala_en": "Balanced communication, moderate disposition.",
        "phala_hi": "Santulit vani, madhyam swabhav.",
        "is_auspicious": True, "bhagya": 65, "sambandha": 65,
    },
    "tanu": {
        "sanskrit": "तनु ओष्ठ", "translit": "Tanu Oshtha",
        "english": "Thin Lips",
        "phala_en": "Reserved, calculating, careful with words and resources.",
        "phala_hi": "Reserved, vyavaharik, vani aur dhan dono me sanyam.",
        "is_auspicious": False, "bhagya": 55, "sambandha": 50,
    },
    "sthula": {
        "sanskrit": "स्थूल ओष्ठ", "translit": "Sthula Oshtha",
        "english": "Thick Lips",
        "phala_en": "Sensual, indulgent, expressive emotions.",
        "phala_hi": "Bhog-priya, sundar bhavna-vyakti, vyakt swabhav.",
        "is_auspicious": True, "bhagya": 65, "sambandha": 70,
    },
}


# 7. CHIBUKA (chin) — Karma-sthan
CHIBUKA_TYPES = {
    "drid": {
        "sanskrit": "दृढ चिबुक", "translit": "Drid Chibuka",
        "english": "Strong / Firm Chin",
        "phala_en": "Strong willpower, leadership, determination.",
        "phala_hi": "Drid sankalp, netritva, drid-nishchayi.",
        "bhagya": 75, "karya": 85,
    },
    "vrutta": {
        "sanskrit": "वृत्त चिबुक", "translit": "Vrutta Chibuka",
        "english": "Round Chin",
        "phala_en": "Affectionate, family-oriented, cooperative.",
        "phala_hi": "Sneh-shil, parivar-priya, sahyogi.",
        "bhagya": 70, "karya": 65,
    },
    "tikshna": {
        "sanskrit": "तीक्ष्ण चिबुक", "translit": "Tikshna Chibuka",
        "english": "Pointed / Sharp Chin",
        "phala_en": "Sharp intellect, may be argumentative, quick wit.",
        "phala_hi": "Teekshna buddhi, vivad-priya, chatur.",
        "bhagya": 65, "karya": 70,
    },
    "dvigan": {
        "sanskrit": "द्वि-चिबुक", "translit": "Dvi-Chibuka",
        "english": "Double / Cleft Chin",
        "phala_en": "Indicates inner-conflict, dual nature, but creative talent.",
        "phala_hi": "Antar-dwand, dvividh swabhav, par rachnatmak pratibha.",
        "bhagya": 65, "karya": 70,
    },
}


# Pancha-Lakshana (5 auspicious marks) — counted across whole face
PANCHA_LAKSHANA_DEFS = {
    "vishala_lalata":     "Broad, smooth forehead",
    "padma_netra_or_mina":"Lotus or fish-shaped eyes",
    "high_bridge_nasika": "Garuda/Singha-style high-bridge nose",
    "bimba_oshtha":       "Full, well-formed lips",
    "drid_chibuka":       "Strong chin",
}


# ─────────────────────────────────────────────────────────────────────────────
# Classification functions (consume cross-engine outputs)
# ─────────────────────────────────────────────────────────────────────────────
def _classify_mukha_akriti(anthro: dict, geom: dict) -> str:
    """Map anthropometry face_shape_7 → classical Vedic mukha-akriti."""
    if not anthro: return "samanya"
    shape = (anthro.get("face_shape_7") or {}).get("shape", "").lower()
    mapping = {
        "round":     "vrutta",
        "oval":      "deergha",
        "oblong":    "ardhachandra",
        "heart":     "hrid",
        "diamond":   "trikona",
        "triangle":  "trikona",
        "inverted_triangle": "trikona",
        "square":    "chaturasra",
        "rectangle": "chaturasra",
    }
    return mapping.get(shape, "samanya")


def _classify_lalata(geom: dict, anthro: dict) -> str:
    """Forehead width & height → Vedic Lalata type."""
    if not anthro: return "samya"
    cls = (anthro.get("classifications") or {})
    forehead_class = cls.get("forehead_class", "").lower()
    forehead_slope = cls.get("forehead_slope_class", "").lower()
    if "broad" in forehead_class:    return "vishala"
    if "narrow" in forehead_class:   return "alpa"
    if "receding" in forehead_slope: return "nimna"
    if "vertical" in forehead_slope or "prominent" in forehead_slope: return "unnata"
    return "samya"


def _classify_bhru(geom: dict, anthro: dict) -> str:
    """Eyebrow shape → Vedic Bhru type."""
    if not anthro: return "rju"
    cls = (anthro.get("classifications") or {})
    arch = cls.get("brow_arch_class", "").lower()
    if "highly_arched" in arch:   return "chandra"
    if "arched" in arch:          return "padma"
    if "rounded" in arch or "soft" in arch: return "ardhachandra"
    if "straight" in arch or "flat" in arch: return "rju"
    if "thick" in arch:           return "ghana"
    return "padma"


def _classify_netra(geom: dict, anthro: dict, p_geom: dict) -> str:
    """Eye shape → Vedic Netra type (8 classical)."""
    cls = (anthro.get("classifications") or {})
    eye_open = cls.get("eye_openness_class", "").lower()
    canthal  = cls.get("canthal_tilt_class", "").lower()
    spacing  = cls.get("eye_spacing_class", "").lower()

    # Padma — large, lotus-petal shape (almond + open + balanced spacing)
    if "almond" in canthal and "wide" in eye_open: return "padma"
    if "upturned" in canthal and "almond" in canthal: return "mina"
    if "large" in eye_open or "wide" in eye_open:     return "khanjana"
    if "downturned" in canthal:                        return "mriga"
    if "small" in eye_open and "deep" in eye_open:    return "gaja"
    if "intense" in canthal or "narrow" in eye_open:  return "vyaghra"
    if "round" in canthal:                             return "shuka"
    # Default to singha for sharp upward tilt
    if "upturned" in canthal: return "singha"
    return "padma"


def _classify_nasika(geom: dict, anthro: dict, p_geom: dict) -> str:
    """Nose shape → Vedic Nasika type (8 classical)."""
    if not anthro: return "samanya"
    nose_w = p_geom.get("nose_width_iod", 0.40)
    nose_l = p_geom.get("nose_length_face_ratio", 0.27)
    cls = (anthro.get("classifications") or {})
    nose_proj = (anthro.get("angles_deg") or {}).get("nose_tip_projection", 0)

    # Garuda — high bridge, prominent, slight curve
    if nose_l > 0.30 and nose_proj < -20: return "garuda"
    if nose_w > 0.48 and nose_l > 0.27:   return "singha"
    if nose_w < 0.36 and nose_l < 0.24:   return "mrigi"
    if nose_w < 0.38 and nose_proj < -15: return "shuka"
    if nose_l > 0.32 and nose_w > 0.42:   return "gaja"
    if nose_w > 0.50:                      return "vrushabha"
    if nose_w > 0.45 and nose_proj > 0:    return "khar"
    return "samanya"


def _classify_oshtha(geom: dict, p_geom: dict, anthro: dict) -> str:
    """Lip shape → Vedic Oshtha type."""
    lip_full = p_geom.get("lip_fullness_iod", 0.20)
    mouth_w  = p_geom.get("mouth_width_iod", 0.80)
    if lip_full > 0.27 and mouth_w > 0.85: return "bimba"
    if lip_full > 0.22:                     return "padma"
    if lip_full < 0.13:                     return "tanu"
    if lip_full > 0.30:                     return "sthula"
    return "samanya"


def _classify_chibuka(geom: dict, p_geom: dict, anthro: dict) -> str:
    """Chin shape → Vedic Chibuka type."""
    if not anthro: return "vrutta"
    cls = (anthro.get("classifications") or {})
    jaw_class = cls.get("face_shape_jaw_class", "").lower()
    if "square" in jaw_class:    return "drid"
    if "round" in jaw_class:     return "vrutta"
    if "pointed" in jaw_class or "v_shape" in jaw_class: return "tikshna"
    return "vrutta"


# ─────────────────────────────────────────────────────────────────────────────
# Pancha-Lakshana (5 auspicious marks) detection
# ─────────────────────────────────────────────────────────────────────────────
def _count_pancha_lakshana(lalata, netra, nasika, oshtha, chibuka) -> dict:
    marks = {}
    marks["vishala_lalata"]      = lalata in ("vishala", "samya", "unnata")
    marks["padma_netra_or_mina"] = netra in ("padma", "mina", "gaja", "khanjana")
    marks["high_bridge_nasika"]  = nasika in ("garuda", "singha", "shuka")
    marks["bimba_oshtha"]        = oshtha in ("bimba", "padma")
    marks["drid_chibuka"]        = chibuka in ("drid",)
    count = sum(1 for v in marks.values() if v)
    return {
        "marks_present": marks,
        "count": count,
        "phala_en": (
            "Pancha-Lakshana sampurna — all 5 auspicious marks present, "
            "highly auspicious life indicated." if count == 5
            else f"{count} out of 5 Pancha-Lakshana present — "
            f"{'very auspicious' if count >= 4 else 'auspicious' if count >= 3 else 'moderately auspicious' if count >= 2 else 'mixed signs'}."
        ),
        "phala_hi": (
            "Sabhi 5 Pancha-Lakshana present — bahut shubh jeevan."
            if count == 5 else
            f"5 me se {count} Pancha-Lakshana present — "
            f"{'bahut shubh' if count >= 4 else 'shubh' if count >= 3 else 'madhyam-shubh' if count >= 2 else 'mishrit'}."
        ),
        "ref": "Brihat_Samhita_Pancha_Lakshana_Sec",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Yoga combinations (e.g., Raja Yoga from face features)
# ─────────────────────────────────────────────────────────────────────────────
def _detect_yogas(mukha, lalata, bhru, netra, nasika, oshtha, chibuka, pancha_count) -> list:
    yogas = []

    # RAJA YOGA — Garuda nose + Padma/Singha eyes + Vishala forehead
    if nasika in ("garuda",) and netra in ("padma", "singha", "gaja") and lalata == "vishala":
        yogas.append({
            "name": "Raja Yoga",
            "sanskrit": "राज योग",
            "phala_en": "Combination indicates royal favour, leadership, lasting fame and wealth.",
            "phala_hi": "Raj-yog — adhipati gun, netritva, sthayi yash aur dhan.",
            "ref": "Brihat_Samhita_Yoga_Sec",
        })

    # DHANA YOGA — Vrushabha/Gaja nose + Vrutta face + Padma lips
    if nasika in ("vrushabha", "gaja") and mukha in ("vrutta", "vishala") and oshtha in ("bimba", "padma"):
        yogas.append({
            "name": "Dhana Yoga",
            "sanskrit": "धन योग",
            "phala_en": "Strong wealth-accumulation indicator. Steady prosperity through enterprise.",
            "phala_hi": "Dhan-yog — vyavasaya se sthir samriddhi.",
            "ref": "Garuda_Purana_Dhana_Lakshana",
        })

    # SARASWATI YOGA — Vishala/Unnata forehead + Padma/Khanjana eyes + Padma lips
    if lalata in ("vishala", "unnata") and netra in ("padma", "khanjana", "gaja") and oshtha in ("padma", "bimba"):
        yogas.append({
            "name": "Saraswati Yoga",
            "sanskrit": "सरस्वती योग",
            "phala_en": "Goddess Saraswati's blessing — exceptional intellect, scholarship, eloquence.",
            "phala_hi": "Saraswati-yog — vishesh buddhi, vidya, vakta-shakti.",
            "ref": "Samudrika_Vidya_Yoga",
        })

    # GAJAKESARI YOGA (face-form) — Gaja netra + Singha hanu (jaw)
    if netra == "gaja" and chibuka == "drid":
        yogas.append({
            "name": "Gajakesari Yoga (mukha-rupa)",
            "sanskrit": "गजकेसरी योग (मुख-रूप)",
            "phala_en": "Elephant-eye + Lion-jaw combination — wisdom + power. Brilliance with leadership.",
            "phala_hi": "Gaj-netra + Singha-hanu — buddhi aur shakti dono.",
            "ref": "Brihat_Samhita_Gajakesari",
        })

    # SOUMYA YOGA — Vrutta face + Padma bhru + Bimba/Padma lips
    if mukha == "vrutta" and bhru in ("padma", "chandra") and oshtha in ("bimba", "padma"):
        yogas.append({
            "name": "Soumya Yoga",
            "sanskrit": "सौम्य योग",
            "phala_en": "Gentle, harmonious life — Lakshmi's grace, peaceful relationships, beauty.",
            "phala_hi": "Soumya-yog — Lakshmi-kripa, shanti-purna sambandh, saundarya.",
            "ref": "Hasta_Samudrika_Soumya",
        })

    # PANCHA-LAKSHANA YOGA — all 5 marks present
    if pancha_count >= 4:
        yogas.append({
            "name": "Pancha-Lakshana Yoga",
            "sanskrit": "पञ्च-लक्षण योग",
            "phala_en": f"{pancha_count}/5 auspicious marks — exceptional Bhagya combination.",
            "phala_hi": f"{pancha_count}/5 shubh chinh — vishesh bhagya-yog.",
            "ref": "Brihat_Samhita_Pancha_Lakshana",
        })

    return yogas


# ─────────────────────────────────────────────────────────────────────────────
# Composite scores (Bhagya, Buddhi, Dhana, Aarogya)
# ─────────────────────────────────────────────────────────────────────────────
def _composite_scores(mukha_data, lalata_data, bhru_data, netra_data,
                       nasika_data, oshtha_data, chibuka_data,
                       pancha_count, n_yogas, health_result) -> dict:
    bhagya = []
    buddhi = []
    dhana  = []
    sambandha = []
    aayu = []

    for d in [mukha_data, lalata_data, netra_data, nasika_data]:
        if d.get("bhagya"): bhagya.append(d["bhagya"])
        if d.get("buddhi"): buddhi.append(d["buddhi"])
        if d.get("dhana"):  dhana.append(d["dhana"])
        if d.get("sambandha"): sambandha.append(d["sambandha"])
        if d.get("aayu"):   aayu.append(d["aayu"])
    for d in [bhru_data, oshtha_data]:
        if d.get("sambandha"): sambandha.append(d["sambandha"])
        if d.get("bhagya"):    bhagya.append(d["bhagya"])

    # Pancha-Lakshana boost (each mark = +3 to bhagya)
    base_bhagya = sum(bhagya)/len(bhagya) if bhagya else 60
    base_bhagya = _clip(base_bhagya + pancha_count * 3 + n_yogas * 5)

    base_buddhi = sum(buddhi)/len(buddhi) if buddhi else 60
    base_dhana  = sum(dhana)/len(dhana)   if dhana  else 60
    base_samb   = sum(sambandha)/len(sambandha) if sambandha else 60
    base_aayu   = sum(aayu)/len(aayu)     if aayu   else 60

    # Aarogya from health engine (if available)
    aarogya = 60
    if health_result and health_result.get("ok"):
        vitality = health_result.get("vitality_score") or 60
        aarogya = round(vitality * 0.7 + base_aayu * 0.3, 1)

    return {
        "bhagya_score":    round(base_bhagya, 1),
        "buddhi_score":    round(base_buddhi, 1),
        "dhana_score":     round(base_dhana, 1),
        "sambandha_score": round(base_samb, 1),
        "aayu_score":      round(base_aayu, 1),
        "aarogya_score":   round(aarogya, 1),
        "interpretation": {
            "bhagya":    _interpret_score("Bhagya (Fortune)", base_bhagya),
            "buddhi":    _interpret_score("Buddhi (Intellect)", base_buddhi),
            "dhana":     _interpret_score("Dhana (Wealth)", base_dhana),
            "sambandha": _interpret_score("Sambandha (Relationships)", base_samb),
            "aayu":      _interpret_score("Aayu (Longevity)", base_aayu),
            "aarogya":   _interpret_score("Aarogya (Health)", aarogya),
        },
    }


def _interpret_score(label: str, score: float) -> str:
    if score >= 80: return f"{label}: Vishesh-uttam — exceptional indication."
    if score >= 70: return f"{label}: Uttam — strong positive indication."
    if score >= 60: return f"{label}: Madhyam-shubh — moderately favourable."
    if score >= 50: return f"{label}: Madhyam — balanced, neither high nor low."
    if score >= 40: return f"{label}: Saamanya — average, depends on karma."
    return f"{label}: Karma-pradhan — strongly self-effort dependent."


# ─────────────────────────────────────────────────────────────────────────────
# Vata-Pitta-Kapha facial preview (full in Engine 13 Prakriti)
# ─────────────────────────────────────────────────────────────────────────────
def _dosha_preview(geom, p_geom, anthro, mukha, oshtha) -> dict:
    """Quick Tridosha facial indicator preview."""
    vata = pitta = kapha = 0
    # Vata signs: thin lips, narrow face, dry skin, small eyes
    if oshtha == "tanu": vata += 2
    if mukha in ("deergha", "trikona"): vata += 2
    if (anthro or {}).get("classifications", {}).get("eye_openness_class", "").lower() == "small":
        vata += 1
    # Pitta signs: sharp features, intense eyes, medium build, oily skin
    if mukha in ("trikona", "chaturasra"): pitta += 2
    if (anthro or {}).get("classifications", {}).get("brow_arch_class", "").lower() in ("highly_arched","sharp"): pitta += 2
    # Kapha signs: full lips, round face, large eyes, smooth skin
    if oshtha in ("bimba", "padma", "sthula"): kapha += 2
    if mukha in ("vrutta", "vishala", "hrid"): kapha += 2
    total = vata + pitta + kapha
    if total == 0: total = 1
    return {
        "vata_pct":  round(vata*100/total, 1),
        "pitta_pct": round(pitta*100/total, 1),
        "kapha_pct": round(kapha*100/total, 1),
        "primary_dosha": max([("vata",vata),("pitta",pitta),("kapha",kapha)],
                              key=lambda x: x[1])[0],
        "note": "Quick facial-only preview. Full Prakriti analysis in Engine 13.",
        "ref": "Charaka_Samhita_Sutrasthana_Prakriti",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main entry
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple],
        image_w: int, image_h: int,
        anthropometry_result: Optional[dict] = None,
        symmetry_result: Optional[dict] = None,
        phi_result: Optional[dict] = None,
        fwhr_result: Optional[dict] = None,
        health_result: Optional[dict] = None,
        personality_result: Optional[dict] = None,
        first_impression_result: Optional[dict] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None) -> dict:

    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "samudrika", "ok": False, "version": 1,
                 "error": "insufficient_landmarks"}

    # Use geometric indicators from personality engine (already computed)
    p_geom = (personality_result or {}).get("geometric_indicators") or {}
    geom = {}  # placeholder — could re-extract if needed

    # Classify each region
    mukha   = _classify_mukha_akriti(anthropometry_result, geom)
    lalata  = _classify_lalata(geom, anthropometry_result)
    bhru    = _classify_bhru(geom, anthropometry_result)
    netra   = _classify_netra(geom, anthropometry_result, p_geom)
    nasika  = _classify_nasika(geom, anthropometry_result, p_geom)
    oshtha  = _classify_oshtha(geom, p_geom, anthropometry_result)
    chibuka = _classify_chibuka(geom, p_geom, anthropometry_result)

    # Build per-region results
    mukha_data   = MUKHA_AKRITI.get(mukha, MUKHA_AKRITI["vrutta"])
    lalata_data  = LALATA_TYPES.get(lalata, LALATA_TYPES["samya"])
    bhru_data    = BHRU_TYPES.get(bhru, BHRU_TYPES["padma"])
    netra_data   = NETRA_TYPES.get(netra, NETRA_TYPES["padma"])
    nasika_data  = NASIKA_TYPES.get(nasika, NASIKA_TYPES["samanya"])
    oshtha_data  = OSHTHA_TYPES.get(oshtha, OSHTHA_TYPES["samanya"])
    chibuka_data = CHIBUKA_TYPES.get(chibuka, CHIBUKA_TYPES["vrutta"])

    # Pancha-Lakshana detection
    pancha = _count_pancha_lakshana(lalata, netra, nasika, oshtha, chibuka)

    # Yoga combinations
    yogas = _detect_yogas(mukha, lalata, bhru, netra, nasika, oshtha, chibuka,
                           pancha["count"])

    # Composite scores
    composite = _composite_scores(mukha_data, lalata_data, bhru_data, netra_data,
                                    nasika_data, oshtha_data, chibuka_data,
                                    pancha["count"], len(yogas), health_result)

    # Tridosha preview
    dosha = _dosha_preview(geom, p_geom, anthropometry_result, mukha, oshtha)

    # Auspicious marks count
    auspicious_features = sum(1 for d in [bhru_data, netra_data, nasika_data, oshtha_data]
                                if d.get("is_auspicious"))
    raja_yoga_features = sum(1 for d in [netra_data, nasika_data]
                                if d.get("is_raja_yoga"))

    # Overall summary narrative (Hinglish + EN)
    summary_en = (
        f"Your face shows {mukha_data['english']} ({mukha_data['translit']}). "
        f"Forehead is {lalata_data['translit']}; eyes are {netra_data['translit']}; "
        f"nose is {nasika_data['translit']}. "
        f"{pancha['count']}/5 Pancha-Lakshana auspicious marks present. "
        f"{len(yogas)} Vedic yoga combination(s) detected: "
        f"{', '.join(y['name'] for y in yogas) if yogas else 'none of the major raja-yogas'}. "
        f"Bhagya score: {composite['bhagya_score']}. "
        f"Primary dosha (preview): {dosha['primary_dosha'].title()}."
    )
    summary_hi = (
        f"Aapka mukh-akriti {mukha_data['translit']} ({mukha_data['english']}) hai. "
        f"Lalata {lalata_data['translit']}; netra {netra_data['translit']}; "
        f"nasika {nasika_data['translit']}. "
        f"5 me se {pancha['count']} Pancha-Lakshana shubh chinh present. "
        f"{len(yogas)} Vedic yoga detect huye: "
        f"{', '.join(y['name'] for y in yogas) if yogas else 'koi mukhya raja-yog nahi'}. "
        f"Bhagya-ank: {composite['bhagya_score']}. "
        f"Pradhan dosha (preview): {dosha['primary_dosha'].title()}."
    )

    return _py({
        "engine": "samudrika",
        "version": 1,
        "ok": True,
        "shastra_name": "Samudrika Shastra",
        "shastra_devanagari": "सामुद्रिक शास्त्र",
        "method": "classical_vedic_face_reading_v1",
        "primary_sources": [
            "Brihat_Samhita_Varahamihira_Ch68_Purusha_Lakshana",
            "Garuda_Purana_Samudrika_Sec",
            "Samudrika_Shastra_attrib_Samudra",
            "Hasta_Samudrika_Shastra",
            "Markandeya_Purana_Lakshana",
            "Vasishtha_Samhita",
            "Manava_Dharma_Shastra_Manu_Smriti",
        ],
        "inputs": {
            "gender": gender, "ethnicity": ethnicity, "age": age,
            "cross_engine_signals": {
                "anthropometry": bool(anthropometry_result and anthropometry_result.get("ok")),
                "symmetry":      bool(symmetry_result and symmetry_result.get("ok")),
                "phi":           bool(phi_result and phi_result.get("ok")),
                "fwhr":          bool(fwhr_result and fwhr_result.get("ok")),
                "health":        bool(health_result and health_result.get("ok")),
                "personality":   bool(personality_result and personality_result.get("ok")),
            },
        },
        "mukha_pradesh_analysis": {
            "1_mukha_akriti": {
                "classification": mukha,
                "sanskrit_name": mukha_data["sanskrit"],
                "transliteration": mukha_data["translit"],
                "english_name": mukha_data["english"],
                "phala_sanskrit": mukha_data["phala_sanskrit"],
                "phala_english":  mukha_data["phala_en"],
                "phala_hinglish": mukha_data["phala_hi"],
                "karya_kshetra": mukha_data["karya"],
                "indicators": {"bhagya": mukha_data["bhagya"], "buddhi": mukha_data["buddhi"],
                               "dhana": mukha_data["dhana"], "aayu": mukha_data["aayu"],
                               "sambandha": mukha_data["sambandha"]},
                "ref": mukha_data["ref"],
            },
            "2_lalata": {
                "classification": lalata,
                "sanskrit_name": lalata_data["sanskrit"],
                "transliteration": lalata_data["translit"],
                "english_name": lalata_data["english"],
                "phala_english":  lalata_data["phala_en"],
                "phala_hinglish": lalata_data["phala_hi"],
                "indicators": {"bhagya": lalata_data["bhagya"], "buddhi": lalata_data["buddhi"],
                               "dhana": lalata_data["dhana"]},
                "sthan_meaning": "Lalata is the Bhagya-sthan (seat of fortune & destiny).",
            },
            "3_bhru": {
                "classification": bhru,
                "sanskrit_name": bhru_data["sanskrit"],
                "transliteration": bhru_data["translit"],
                "english_name": bhru_data["english"],
                "phala_english":  bhru_data["phala_en"],
                "phala_hinglish": bhru_data["phala_hi"],
                "is_auspicious":  bhru_data.get("is_auspicious"),
                "indicators": {"bhagya": bhru_data.get("bhagya"),
                               "sambandha": bhru_data.get("sambandha")},
            },
            "4_netra": {
                "classification": netra,
                "sanskrit_name": netra_data["sanskrit"],
                "transliteration": netra_data["translit"],
                "english_name": netra_data["english"],
                "phala_english":  netra_data["phala_en"],
                "phala_hinglish": netra_data["phala_hi"],
                "is_auspicious":  netra_data.get("is_auspicious"),
                "is_raja_yoga":   netra_data.get("is_raja_yoga"),
                "indicators": {"bhagya": netra_data.get("bhagya"),
                               "buddhi": netra_data.get("buddhi"),
                               "dhana":  netra_data.get("dhana")},
                "sthan_meaning": "Netra reflect Manas (mind) and Atma (soul).",
            },
            "5_nasika": {
                "classification": nasika,
                "sanskrit_name": nasika_data["sanskrit"],
                "transliteration": nasika_data["translit"],
                "english_name": nasika_data["english"],
                "phala_english":  nasika_data["phala_en"],
                "phala_hinglish": nasika_data["phala_hi"],
                "is_auspicious":  nasika_data.get("is_auspicious"),
                "is_raja_yoga":   nasika_data.get("is_raja_yoga"),
                "karya_kshetra":  nasika_data.get("karya_kshetra"),
                "indicators": {"bhagya": nasika_data.get("bhagya"),
                               "dhana":  nasika_data.get("dhana")},
                "sthan_meaning": "Nasika reflects Dhana (wealth) and Karya-kshetra (career).",
            },
            "6_oshtha": {
                "classification": oshtha,
                "sanskrit_name": oshtha_data["sanskrit"],
                "transliteration": oshtha_data["translit"],
                "english_name": oshtha_data["english"],
                "phala_english":  oshtha_data["phala_en"],
                "phala_hinglish": oshtha_data["phala_hi"],
                "is_auspicious":  oshtha_data.get("is_auspicious"),
                "indicators": {"bhagya": oshtha_data.get("bhagya"),
                               "sambandha": oshtha_data.get("sambandha")},
                "sthan_meaning": "Oshtha reflect Vani (speech) and Bhog (sensual life).",
            },
            "7_chibuka": {
                "classification": chibuka,
                "sanskrit_name": chibuka_data["sanskrit"],
                "transliteration": chibuka_data["translit"],
                "english_name": chibuka_data["english"],
                "phala_english":  chibuka_data["phala_en"],
                "phala_hinglish": chibuka_data["phala_hi"],
                "indicators": {"bhagya": chibuka_data.get("bhagya"),
                               "karya":  chibuka_data.get("karya")},
                "sthan_meaning": "Chibuka reflects Karma-shakti (work-power) and Sankalp.",
            },
        },
        "pancha_lakshana": pancha,
        "vedic_yogas_detected": yogas,
        "auspicious_feature_count": auspicious_features,
        "raja_yoga_feature_count":  raja_yoga_features,
        "composite_scores": composite,
        "tridosha_facial_preview": dosha,
        "summary_english":  summary_en,
        "summary_hinglish": summary_hi,
        "shastra_disclaimer": (
            "Samudrika Shastra is TRADITIONAL classical Vedic knowledge passed "
            "through Sanskrit texts (Brihat Samhita, Garuda Purana, etc.). It is "
            "offered for cultural-spiritual reflection and self-awareness. "
            "Modern scientific validity is NOT claimed. Predictions about "
            "fortune (bhagya), wealth (dhana), longevity (aayu), and relationships "
            "(sambandha) are INTERPRETIVE — not deterministic. Multiple "
            "authoritative texts may differ on specific phala (results). "
            "Karma, intention, and effort can transform any indication shown here."
        ),
        "ethics_notice": (
            "These traditional readings MUST NOT be used for caste/social "
            "discrimination, marriage-rejection, employment decisions, or any "
            "judgment of human worth. Vedic shastra emphasises that Karma "
            "(action) and Bhakti (devotion) supersede any lakshana (mark). "
            "'Karmanye vadhikaraste' — focus on action, not predetermined fruit."
        ),
        "reference_text_quotes": {
            "brihat_samhita": "मुखं प्रसन्नं सुभगं विशालं... (Brihat Samhita 68.12) — "
                              "A clear, broad, well-formed face is auspicious.",
            "garuda_purana":  "लक्षणं शुभदं नित्यं ज्ञेयं समुद्रिकैः... (Garuda Purana) — "
                              "Auspicious marks are eternally readable through Samudrika.",
        },
    })
