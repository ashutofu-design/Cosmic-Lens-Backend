"""
Engine 8 — Samudrika Shastra (सामुद्रिक शास्त्र) — v2
=========================================================

Classical Vedic / Indian face reading. v2 adds 14 missing items audited
from v1:

  v2 ADDITIONS (over v1):
   1.  Karna (कर्ण/ears) classification — 5 classical types
   2.  Kapola (कपोल/cheeks) — Lakshmi-sthan analysis (4 types)
   3.  Hanu (हनु/jaw) separate from Chibuka — Bala-sthan (4 types)
   4.  Mukha-Varna (मुख-वर्ण) — 4 classical complexion (Gaura, Shyama,
       Krishna, Pita) using LAB skin estimate from Engine 5 health
   5.  Trinetra-sthan (त्रिनेत्र-स्थान) — third-eye Bhagya-bindu region
   6.  Classical Sanskrit shloka quotes embedded per region
   7.  Gender-specific phala — Stri-lakshana vs Purusha-lakshana
       (Brihat Samhita has separate Stri-Lakshana Adhyaya)
   8.  Marma-sthan facial energy points (Sushruta Samhita Sharir-sthan)
   9.  Tilaka / Bindu / Til (mole) detection placeholder for Tilaka-Phala
   10. Vyaghra-mukha + Pakshi-mukha added to Mukha-Akriti (now 9 types)
   11. Finer Nasika thresholds (gender-aware)
   12. 9 yogas (was 5): + Maha-Bhagya, Vipreet-Raja, Akhand-Samrajya,
       Lakshmi-Narayan
   13. Five-element / Pancha-Mahabhuta facial mapping
       (Prithvi/Jal/Agni/Vayu/Akash)
   14. Saubhagya-Phala summary in 3 timeframes (Purva/Madhya/Uttara aayu)

Sources:
  • Brihat Samhita — Varahamihira, 6th c. CE
      Ch. 68 Purusha-Lakshana, Ch. 70 Stri-Lakshana
  • Garuda Purana — Samudrika Sec
  • Samudrika Shastra — attrib. Samudra
  • Hasta-Samudrika Shastra
  • Sushruta Samhita — Sharir-sthan (Marma-sthan)
  • Charaka Samhita — Sutrasthana (Prakriti)
  • Markandeya Purana — Lakshana Sec
  • Vasishtha Samhita
  • Manava Dharma Shastra (Manu Smriti) — Adhyaya 3 (auspicious lakshana)
  • Agni Purana — Strilakshana adhyaya
  • Bhrigu Samhita — face-mark indicators

Disclaimer: traditional knowledge for self-reflection. Modern scientific
validity NOT claimed. MUST NOT be used for caste/marriage/employment
discrimination. Karma supersedes lakshana.
"""
from __future__ import annotations
from typing import Optional, Sequence
import math
import numpy as np


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
#  CLASSICAL VEDIC TYPOLOGIES (with shloka quotes)
# ─────────────────────────────────────────────────────────────────────────────

# 1. MUKHA-AKRITI — 9 classical types (v2 adds vyaghra, pakshi)
MUKHA_AKRITI = {
    "vrutta": {
        "sanskrit": "वृत्त मुख", "translit": "Vrutta Mukha", "english": "Round Face",
        "shloka": "वृत्तं सौम्यं सुखप्रदं लक्ष्म्या आश्रयम्",
        "shloka_translit": "Vruttam saumyam sukhapradam Lakshmyaa aashrayam",
        "phala_en": "Gentle, joyful, wealthy, beloved by friends. Lakshmi-blessed.",
        "phala_hi": "Soumya nature, sukhi jeevan, dhan-prapti, Lakshmi ki kripa.",
        "stri_phala": "Saubhagyavati, parivar-poshini, sukh-shantipurna grihasthi.",
        "purusha_phala": "Mitra-priya, vyapar-kushal, dhanvan grihastha.",
        "bhagya": 75, "buddhi": 60, "dhana": 75, "aayu": 70, "sambandha": 80,
        "karya": "vyapar (business), seva-karma, hospitality",
        "ref": "Brihat_Samhita_68.12_Varahamihira",
    },
    "deergha": {
        "sanskrit": "दीर्घ मुख", "translit": "Deergha Mukha", "english": "Long / Oval Face",
        "shloka": "दीर्घं वदनं विद्वान् दीर्घायुर्मनस्विनाम्",
        "shloka_translit": "Deergham vadanam vidvaan deerghaayur-manasvinaam",
        "phala_en": "Scholarly, long-lived, intelligent, attains fame.",
        "phala_hi": "Vidwan, deergha-aayu, buddhimaan, yash prapt karte hain.",
        "stri_phala": "Vidushi, dhairyavati, deergha-aayu, kala-priya.",
        "purusha_phala": "Vidvan-shiromani, lekhak, shastrajna, deergha-jeevi.",
        "bhagya": 70, "buddhi": 85, "dhana": 65, "aayu": 85, "sambandha": 60,
        "karya": "vidya (academia), shastra-adhyayan, research",
        "ref": "Samudrika_Shastra_Mukha_Adhyaya",
    },
    "trikona": {
        "sanskrit": "त्रिकोण मुख", "translit": "Trikona Mukha", "english": "Triangular Face",
        "shloka": "त्रिकोण-वदनः कलाप्रियः चञ्चलमनाः",
        "shloka_translit": "Trikona-vadanah kalaapriyah chanchala-manaah",
        "phala_en": "Sharp-minded, artistic, restless mind, often emotional.",
        "phala_hi": "Teekshna buddhi, kala-priya, chanchal man, emotional bhi.",
        "stri_phala": "Kala-vidushi, sundar, kintu chanchal-mansika.",
        "purusha_phala": "Kalakar, lekhak, kintu sankalp me drid-ta ki kami.",
        "bhagya": 60, "buddhi": 80, "dhana": 60, "aayu": 65, "sambandha": 55,
        "karya": "kala (arts), sangeet, lekhan, design",
        "ref": "Garuda_Purana_Samudrika_Sec",
    },
    "chaturasra": {
        "sanskrit": "चतुरस्र मुख", "translit": "Chaturasra Mukha", "english": "Square Face",
        "shloka": "चतुरस्रं स्थिरं धीरं कर्मनिष्ठं प्रशस्यते",
        "shloka_translit": "Chaturasram sthiram dheeram karma-nishtham prashasyate",
        "phala_en": "Stable, courageous, hardworking, dharmically committed.",
        "phala_hi": "Sthir, sahasi, mehnati, karma me nishtha.",
        "stri_phala": "Karma-nishtha, sthir, kintu kathor sambandh me.",
        "purusha_phala": "Sahasi-yodha, dharma-rakshak, sena-karya hetu yogya.",
        "bhagya": 70, "buddhi": 70, "dhana": 75, "aayu": 75, "sambandha": 70,
        "karya": "rajya-karya, sena, engineering",
        "ref": "Brihat_Samhita_68.15",
    },
    "hrid": {
        "sanskrit": "हृद्-आकार मुख", "translit": "Hrid-akara Mukha", "english": "Heart-shaped Face",
        "shloka": "हृद्-आकारं स्नेहशीलं सौन्दर्यप्रियम् उच्यते",
        "shloka_translit": "Hrid-aakaaram sneha-sheelam saundarya-priyam uchyate",
        "phala_en": "Affectionate, loving, drawn to beauty and aesthetics.",
        "phala_hi": "Sneh-shil, prem-priya, sundarta ke prati aakarshit.",
        "stri_phala": "Atyant sundar, prem-priya, vivah-yog uttam, Lakshmi-roopini.",
        "purusha_phala": "Sneh-shil, kala-priya, kavi-hriday, romantic prakriti.",
        "bhagya": 70, "buddhi": 65, "dhana": 65, "aayu": 70, "sambandha": 85,
        "karya": "kala, rachnatmak vyavasaya, mediation",
        "ref": "Hasta_Samudrika_supplementary",
    },
    "ardhachandra": {
        "sanskrit": "अर्धचन्द्र मुख", "translit": "Ardhachandra Mukha", "english": "Half-moon Face",
        "shloka": "अर्धचन्द्र-वदनो धैर्यवान् धर्मिष्ठ उच्यते",
        "shloka_translit": "Ardhachandra-vadano dhairyavaan dharmishtha uchyate",
        "phala_en": "Calm, patient, dharma-committed, self-confident.",
        "phala_hi": "Shant, dhairyavan, dharma-nishtha, atma-vishwasi.",
        "stri_phala": "Shant-swabhav, dharma-priya, pati-vrata, sushil.",
        "purusha_phala": "Dhyani, dharma-acharya, guru-pad-yogya, atma-jnani.",
        "bhagya": 75, "buddhi": 75, "dhana": 70, "aayu": 80, "sambandha": 70,
        "karya": "shikshak, guru, spiritual leader",
        "ref": "Vasishtha_Samhita_Lakshana",
    },
    "vishala": {
        "sanskrit": "विशाल मुख", "translit": "Vishala Mukha", "english": "Broad Face",
        "shloka": "विशालं वदनं राज्यं बलं सौभाग्यम् आवहेत्",
        "shloka_translit": "Vishaalam vadanam raajyam balam saubhaagyam aavahet",
        "phala_en": "Strong, courageous, natural leader, regal bearing.",
        "phala_hi": "Balwan, sahasi, neta-pradhan, rajasik prakriti.",
        "stri_phala": "Maharani-tulya, prabhavshali, samaj me pratishtha.",
        "purusha_phala": "Raja-tulya, netritva, vishal-saamrajya hetu yogya.",
        "bhagya": 80, "buddhi": 70, "dhana": 80, "aayu": 75, "sambandha": 65,
        "karya": "netritva, rajya-karya, vyavasaya",
        "ref": "Brihat_Samhita_68.18",
    },
    "vyaghra": {  # NEW v2
        "sanskrit": "व्याघ्र मुख", "translit": "Vyaghra Mukha", "english": "Tiger Face",
        "shloka": "व्याघ्र-मुखः उग्रः शूरः क्रोधनः कर्म-पटुः",
        "shloka_translit": "Vyaaghra-mukhah ugrah shoorah krodhanah karma-patuh",
        "phala_en": "Fierce, courageous, quick-tempered, action-oriented warrior nature.",
        "phala_hi": "Ugra, shoor, krodh-pravan, kintu karma me patu.",
        "stri_phala": "Tejasvini, ugra-prakriti, swatantra-priya, netritva karne wali.",
        "purusha_phala": "Yodha, sena-pati, krodh par niyantran avashyak.",
        "bhagya": 70, "buddhi": 65, "dhana": 70, "aayu": 65, "sambandha": 50,
        "karya": "sena, sports, competitive professions",
        "ref": "Samudrika_Pashu_Lakshana_Sec",
    },
    "pakshi": {  # NEW v2 (bird-face — narrow/sharp)
        "sanskrit": "पक्षि-मुख", "translit": "Pakshi Mukha", "english": "Bird-like Face (sharp & narrow)",
        "shloka": "पक्षि-मुखः चञ्चलः वाचालः बहुयायी उच्यते",
        "shloka_translit": "Pakshi-mukhah chanchalah vaachaalah bahu-yaayee uchyate",
        "phala_en": "Restless, talkative, much travel, communicative roles.",
        "phala_hi": "Chanchal, vachan-pravan, bahut yatra, sandeshvahak.",
        "stri_phala": "Vakta, chanchal, samaj-sevika, parivar me chanchalata.",
        "purusha_phala": "Patrakar, vakta, yatri, koot-niti me kushal.",
        "bhagya": 60, "buddhi": 75, "dhana": 60, "aayu": 65, "sambandha": 55,
        "karya": "patrakar, vakta, koot-niti, yatra-karya",
        "ref": "Samudrika_Pashu_Lakshana_Sec",
    },
}


# 2. LALATA (forehead) — Bhagya-sthan
LALATA_TYPES = {
    "vishala": {
        "sanskrit": "विशाल ललाट", "translit": "Vishala Lalata", "english": "Broad Forehead",
        "shloka": "विशालं ललाटं विद्या-धनयोः आश्रयः",
        "shloka_translit": "Vishaalam lalaatam vidyaa-dhanayoh aashrayah",
        "phala_en": "Vast intellect (Buddhi-vaibhavam) and Bhagya. Inheritance, scholarship, royal favour.",
        "phala_hi": "Vishal buddhi aur bhagya ka pratik. Vidya, dhan, raja-kripa.",
        "bhagya": 80, "buddhi": 85, "dhana": 75,
    },
    "samya": {
        "sanskrit": "सम्य ललाट", "translit": "Samya Lalata", "english": "Balanced Forehead",
        "shloka": "सम्य-ललाटं समभाग्यं समबुद्धिं प्रदर्शयेत्",
        "shloka_translit": "Samya-lalaatam sama-bhaagyam sama-buddhim pradarshayet",
        "phala_en": "Harmony of intellect and karma. Steady fortune.",
        "phala_hi": "Buddhi aur karma ka santulan, sthir bhagya.",
        "bhagya": 70, "buddhi": 75, "dhana": 70,
    },
    "alpa": {
        "sanskrit": "अल्प ललाट", "translit": "Alpa Lalata", "english": "Narrow / Small Forehead",
        "shloka": "अल्प-ललाटः कर्म-शीलः स्व-प्रयत्न-सिद्धि-भाक्",
        "shloka_translit": "Alpa-lalaatah karma-sheelah sva-prayatna-siddhi-bhaak",
        "phala_en": "Karma-pradhan — fortune through self-effort, not inheritance.",
        "phala_hi": "Karma-pradhan jeevan — apne mehnat se safalta.",
        "bhagya": 55, "buddhi": 60, "dhana": 60,
    },
    "unnata": {
        "sanskrit": "उन्नत ललाट", "translit": "Unnata Lalata", "english": "Prominent Forehead",
        "shloka": "उन्नत-ललाटो ध्यानी आध्यात्मिक-प्रवृत्तिकः",
        "shloka_translit": "Unnata-lalaato dhyaanee aadhyaatmika-pravrittikah",
        "phala_en": "Spiritual inclination, philosophical mind, dhyana-shakti.",
        "phala_hi": "Adhyatmik pravritti, chintan-shil, dhyana shakti.",
        "bhagya": 75, "buddhi": 90, "dhana": 65,
    },
    "nimna": {
        "sanskrit": "निम्न ललाट", "translit": "Nimna Lalata", "english": "Sloping / Receding Forehead",
        "shloka": "निम्न-ललाटः शीघ्र-कर्ता धैर्य-हीनो भवेत् क्वचित्",
        "shloka_translit": "Nimna-lalaatah sheeghra-kartaa dhairya-heeno bhavet kvachit",
        "phala_en": "Action-oriented, swift decisions, may lack patience.",
        "phala_hi": "Karma-shil, jaldi nirnay lete hain, dhairya kam.",
        "bhagya": 60, "buddhi": 65, "dhana": 65,
    },
}


# 3. BHRU (eyebrows) — 5 types
BHRU_TYPES = {
    "padma": {
        "sanskrit": "पद्म भ्रू", "translit": "Padma Bhru", "english": "Lotus-arched Eyebrows",
        "shloka": "पद्म-भ्रू सौभाग्यवती लक्ष्मी-पदा प्रिया",
        "shloka_translit": "Padma-bhroo saubhaagyavatee Lakshmi-padaa priyaa",
        "phala_en": "Most auspicious — Lakshmi-pradayika. Beauty, grace, harmonious relations.",
        "phala_hi": "Atyant shubh — Lakshmi pradayika. Saundarya, kripa, sambandh.",
        "is_auspicious": True, "bhagya": 80, "sambandha": 85,
    },
    "chandra": {
        "sanskrit": "चन्द्र भ्रू", "translit": "Chandra Bhru", "english": "Moon-curve Eyebrows",
        "shloka": "चन्द्र-भ्रू बुद्धि-वैभवं कला-प्रियत्वं ददाति",
        "shloka_translit": "Chandra-bhroo buddhi-vaibhavam kalaa-priyatvam dadaati",
        "phala_en": "Intelligence, charm, artistic sensibility.",
        "phala_hi": "Buddhi, akarshan, kala-bhavna.",
        "is_auspicious": True, "bhagya": 75, "sambandha": 75,
    },
    "ardhachandra": {
        "sanskrit": "अर्धचन्द्र भ्रू", "translit": "Ardhachandra Bhru", "english": "Half-moon Eyebrows",
        "shloka": "अर्धचन्द्र-भ्रू सम-बुद्धिं स्थिर-स्वभावं सूचयेत्",
        "shloka_translit": "Ardhachandra-bhroo sama-buddhim sthira-svabhaavam soochayet",
        "phala_en": "Balanced wisdom and emotion, stable temperament.",
        "phala_hi": "Buddhi aur bhavna ka santulan, sthir swabhav.",
        "is_auspicious": True, "bhagya": 70, "sambandha": 70,
    },
    "rju": {
        "sanskrit": "ऋजु भ्रू", "translit": "Rju Bhru", "english": "Straight Eyebrows",
        "shloka": "ऋजु-भ्रू सरलः कर्मठः व्यवहार-कुशलः",
        "shloka_translit": "Rju-bhroo saralah karmathah vyavahaara-kushalah",
        "phala_en": "Practical, direct, action-oriented.",
        "phala_hi": "Vyavaharik, seedha-saaf, karma-shil.",
        "is_auspicious": False, "bhagya": 60, "sambandha": 60,
    },
    "ghana": {
        "sanskrit": "घन भ्रू", "translit": "Ghana Bhru", "english": "Thick / Dense Eyebrows",
        "shloka": "घन-भ्रू दृढ-संकल्पः शूरः उग्र-स्वभावकः",
        "shloka_translit": "Ghana-bhroo dridha-sankalpah shoorah ugra-svabhaavakah",
        "phala_en": "Strong willpower, courage, intense temperament.",
        "phala_hi": "Drid sankalp, sahas, teevra swabhav.",
        "is_auspicious": True, "bhagya": 65, "sambandha": 55,
    },
}


# 4. NETRA (eyes) — 8 classical
NETRA_TYPES = {
    "padma": {
        "sanskrit": "पद्म नेत्र", "translit": "Padma-akara Netra", "english": "Lotus-shaped Eyes",
        "shloka": "पद्म-नेत्रो महा-भाग्यः लक्ष्मी-कान्त-स्वरूपकः",
        "shloka_translit": "Padma-netro mahaa-bhaagyah Lakshmi-kaanta-svaroopakah",
        "phala_en": "Most auspicious — Lakshmi-kripa, beauty, compassion, divine grace.",
        "phala_hi": "Sabse shubh netra. Lakshmi-kripa, saundarya, karuna.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 90, "buddhi": 80, "dhana": 85,
    },
    "mina": {
        "sanskrit": "मीन नेत्र", "translit": "Mina-akara Netra", "english": "Fish-shaped Eyes",
        "shloka": "मीन-नेत्रा सुन्दरा कलावती शुभ-वैवाहिकी",
        "shloka_translit": "Meena-netraa sundaraa kalaavatee shubha-vaivaahikee",
        "phala_en": "Beautiful, attractive, artistic talent, good marital prospects.",
        "phala_hi": "Sundar, akarshak, kala-pratibha, achha vivah-yog.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 80, "buddhi": 75, "dhana": 75,
    },
    "khanjana": {
        "sanskrit": "खञ्जन नेत्र", "translit": "Khanjana Netra", "english": "Wagtail Eyes",
        "shloka": "खञ्जन-नेत्रः चतुरः वाक्-पटुः रसिकः",
        "shloka_translit": "Khanjana-netrah chaturah vaak-patuh rasikah",
        "phala_en": "Lively, expressive, charming, quick-witted.",
        "phala_hi": "Jeevant, abhivyakt, akarshak.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 75, "buddhi": 80, "dhana": 70,
    },
    "mriga": {
        "sanskrit": "मृग नेत्र", "translit": "Mriga Netra", "english": "Deer Eyes",
        "shloka": "मृग-नेत्रः मृदु-स्वभावी भक्ति-परायणः",
        "shloka_translit": "Mriga-netrah mridu-svabhaavee bhakti-paraayanah",
        "phala_en": "Gentle, sensitive, devotional bent.",
        "phala_hi": "Komal swabhav, samvedansheel, bhakti-bhavna.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 65, "buddhi": 70, "dhana": 60,
    },
    "gaja": {
        "sanskrit": "गज नेत्र", "translit": "Gaja Netra", "english": "Elephant Eyes",
        "shloka": "गज-नेत्रः धीरो रण-नीति-कुशलः चिर-जीवी",
        "shloka_translit": "Gaja-netrah dheero rana-neeti-kushalah chira-jeevee",
        "phala_en": "Wise, strategic, patient, long-term thinker. Royal sign.",
        "phala_hi": "Buddhimaan, ranniti-kushal, dhairyavan, deergha-drishti.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 85, "buddhi": 90, "dhana": 80,
    },
    "singha": {
        "sanskrit": "सिंह नेत्र", "translit": "Singha Netra", "english": "Lion Eyes",
        "shloka": "सिंह-नेत्रः शूरः क्षात्र-तेजसा युक्तः",
        "shloka_translit": "Simha-netrah shoorah kshaatra-tejasaa yuktah",
        "phala_en": "Courageous, commanding, leadership, Kshatriya-like.",
        "phala_hi": "Sahasi, adhipati-bhavna, neta. Kshatriya-tej.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 80, "buddhi": 75, "dhana": 80,
    },
    "vyaghra": {
        "sanskrit": "व्याघ्र नेत्र", "translit": "Vyaghra Netra", "english": "Tiger Eyes",
        "shloka": "व्याघ्र-नेत्रः उग्रः क्रोधी कर्म-वीरः",
        "shloka_translit": "Vyaaghra-netrah ugrah krodhee karma-veerah",
        "phala_en": "Powerful, aggressive, may have temper.",
        "phala_hi": "Shaktishali, ugra, krodh-pravan.",
        "is_auspicious": False, "is_raja_yoga": False,
        "bhagya": 70, "buddhi": 70, "dhana": 75,
    },
    "shuka": {
        "sanskrit": "शुक नेत्र", "translit": "Shuka Netra", "english": "Parrot Eyes",
        "shloka": "शुक-नेत्रः वाचालः अनुकर्ता मधुर-वाक्",
        "shloka_translit": "Shuka-netrah vaachaalah anukartaa madhura-vaak",
        "phala_en": "Talkative, social, mimicry, eloquent.",
        "phala_hi": "Vachan-pravan, sammilan-priya, anukaran me kushal.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 65, "buddhi": 75, "dhana": 65,
    },
}


# 5. NASIKA (nose) — 8 classical
NASIKA_TYPES = {
    "garuda": {
        "sanskrit": "गरुड नासिका", "translit": "Garuda Nasika", "english": "Eagle Nose",
        "shloka": "गरुड-नासिको राजा सम्पन्न-धनो भवेत्",
        "shloka_translit": "Garuda-naasiko raajaa sampanna-dhano bhavet",
        "phala_en": "Royal sign — natural authority, wealth, leadership.",
        "phala_hi": "Rajasik chinha — adhipati gun, dhan, netritva.",
        "is_auspicious": True, "is_raja_yoga": True,
        "bhagya": 85, "dhana": 90, "karya_kshetra": "leadership, business empire",
    },
    "singha": {
        "sanskrit": "सिंह नासिका", "translit": "Singha Nasika", "english": "Lion Nose",
        "shloka": "सिंह-नासिको शूरो यशस्वी रण-दक्षः",
        "shloka_translit": "Simha-naasiko shooro yashasvee rana-dakshah",
        "phala_en": "Courage, fame, military success.",
        "phala_hi": "Sahas, yash, sena-vijay.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 80, "dhana": 75, "karya_kshetra": "military, sports, public roles",
    },
    "mrigi": {
        "sanskrit": "मृगी नासिका", "translit": "Mrigi Nasika", "english": "Doe Nose",
        "shloka": "मृगी-नासिका सुन्दरा कला-प्रिया स्त्रीणां शुभा",
        "shloka_translit": "Mrigee-naasikaa sundaraa kalaa-priyaa streenaam shubhaa",
        "phala_en": "Gentle, sensitive, artistic. Auspicious for women in classical texts.",
        "phala_hi": "Komal, samvedansheel, kala-priya. Stri ke liye shubh.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 70, "dhana": 65, "karya_kshetra": "arts, education, healing",
    },
    "shuka": {
        "sanskrit": "शुक नासिका", "translit": "Shuka Nasika", "english": "Parrot Nose",
        "shloka": "शुक-नासिको चतुरः पण्डितः वक्तृ-शिरोमणिः",
        "shloka_translit": "Shuka-naasiko chaturah panditah vaktru-shiromanih",
        "phala_en": "Sharp wit, cunning, eloquence, scholar/orator.",
        "phala_hi": "Teekshna buddhi, chaturai, vakta. Vidwan.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 70, "dhana": 70, "karya_kshetra": "advocacy, teaching, oratory",
    },
    "gaja": {
        "sanskrit": "गज नासिका", "translit": "Gaja Nasika", "english": "Elephant Nose",
        "shloka": "गज-नासिको दीर्घायुः धन-संग्राहकः धीरः",
        "shloka_translit": "Gaja-naasiko deerghaayuh dhana-sangraahakah dheerah",
        "phala_en": "Long life, wealth-accumulator, deep wisdom.",
        "phala_hi": "Deergha aayu, dhan-sangrahak, gambhir buddhi.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 75, "dhana": 80, "karya_kshetra": "finance, real estate",
    },
    "khar": {
        "sanskrit": "खर नासिका", "translit": "Khar Nasika", "english": "Donkey Nose",
        "shloka": "खर-नासिको परिश्रमी संघर्षात्-सिद्धि-भाक्",
        "shloka_translit": "Khara-naasiko parishramee sangharshaat-siddhi-bhaak",
        "phala_en": "Hard-working, persistent, struggles before success.",
        "phala_hi": "Mehnati, sthir, pehle sangharsh.",
        "is_auspicious": False, "is_raja_yoga": False,
        "bhagya": 55, "dhana": 60, "karya_kshetra": "labour-intensive roles",
    },
    "vrushabha": {
        "sanskrit": "वृषभ नासिका", "translit": "Vrushabha Nasika", "english": "Bull Nose",
        "shloka": "वृषभ-नासिकः समृद्धः कुटुम्ब-वत्सलो भवेत्",
        "shloka_translit": "Vrishabha-naasikah samriddhah kutumba-vatsalo bhavet",
        "phala_en": "Stable, prosperous, family-oriented.",
        "phala_hi": "Sthir, samriddh, parivar-priya.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 75, "dhana": 80, "karya_kshetra": "agriculture, hospitality",
    },
    "samanya": {
        "sanskrit": "सामान्य नासिका", "translit": "Samanya Nasika", "english": "Average Nose",
        "shloka": "सामान्य-नासिको मध्यम-भाग्यो भवेत् सदा",
        "shloka_translit": "Saamaanya-naasiko madhyama-bhaagyo bhavet sadaa",
        "phala_en": "Balanced fortune, no extreme highs or lows.",
        "phala_hi": "Santulit bhagya.",
        "is_auspicious": True, "is_raja_yoga": False,
        "bhagya": 65, "dhana": 65, "karya_kshetra": "varied",
    },
}


# 6. OSHTHA (lips) — 5 types
OSHTHA_TYPES = {
    "bimba": {
        "sanskrit": "बिम्ब ओष्ठ", "translit": "Bimba Oshtha", "english": "Bimba-fruit Lips",
        "shloka": "बिम्ब-ओष्ठा सुन्दरी लक्ष्मी-समा प्रिया-दर्शना",
        "shloka_translit": "Bimba-oshthaa sundaree Lakshmi-samaa priyaa-darshanaa",
        "phala_en": "Auspicious — beauty, charm, devotion. Lakshmi-pradayika.",
        "phala_hi": "Shubh — saundarya, akarshan, bhakti.",
        "is_auspicious": True, "bhagya": 80, "sambandha": 85,
    },
    "padma": {
        "sanskrit": "पद्म ओष्ठ", "translit": "Padma Oshtha", "english": "Lotus-petal Lips",
        "shloka": "पद्म-ओष्ठो मधुर-वाक् वक्तृ भक्ति-परः सदा",
        "shloka_translit": "Padma-oshtho madhura-vaak vaktru bhakti-parah sadaa",
        "phala_en": "Refined speech, sweetness, eloquence.",
        "phala_hi": "Madhur vachan, mithas, vakta.",
        "is_auspicious": True, "bhagya": 75, "sambandha": 80,
    },
    "samanya": {
        "sanskrit": "सामान्य ओष्ठ", "translit": "Samanya Oshtha", "english": "Balanced Lips",
        "shloka": "सामान्य-ओष्ठो मध्यम-व्यक्तिः समभावेन वर्तते",
        "shloka_translit": "Saamaanya-oshtho madhyama-vyaktih samabhaavena vartate",
        "phala_en": "Balanced communication, moderate disposition.",
        "phala_hi": "Santulit vani, madhyam swabhav.",
        "is_auspicious": True, "bhagya": 65, "sambandha": 65,
    },
    "tanu": {
        "sanskrit": "तनु ओष्ठ", "translit": "Tanu Oshtha", "english": "Thin Lips",
        "shloka": "तनु-ओष्ठो गूढ-भावी संयमी मित-भाषकः",
        "shloka_translit": "Tanu-oshtho gooDha-bhaavee samyamee mita-bhaashakah",
        "phala_en": "Reserved, calculating, careful with words.",
        "phala_hi": "Reserved, vyavaharik, sanyam.",
        "is_auspicious": False, "bhagya": 55, "sambandha": 50,
    },
    "sthula": {
        "sanskrit": "स्थूल ओष्ठ", "translit": "Sthula Oshtha", "english": "Thick Lips",
        "shloka": "स्थूल-ओष्ठो भोग-प्रियो रसिक-स्वभावकः सदा",
        "shloka_translit": "Sthoola-oshtho bhoga-priyo rasika-svabhaavakah sadaa",
        "phala_en": "Sensual, indulgent, expressive emotions.",
        "phala_hi": "Bhog-priya, vyakt swabhav.",
        "is_auspicious": True, "bhagya": 65, "sambandha": 70,
    },
}


# 7. CHIBUKA (chin) — Karma-sthan
CHIBUKA_TYPES = {
    "drid": {
        "sanskrit": "दृढ चिबुक", "translit": "Drid Chibuka", "english": "Strong / Firm Chin",
        "shloka": "दृढ-चिबुकः नायकः दृढ-संकल्पः कर्म-सिद्धः",
        "shloka_translit": "Dridha-chibukah naayakah dridha-sankalpah karma-siddhah",
        "phala_en": "Strong willpower, leadership, determination.",
        "phala_hi": "Drid sankalp, netritva.",
        "bhagya": 75, "karya": 85,
    },
    "vrutta": {
        "sanskrit": "वृत्त चिबुक", "translit": "Vrutta Chibuka", "english": "Round Chin",
        "shloka": "वृत्त-चिबुकः स्नेही कुटुम्ब-वत्सलो जनः",
        "shloka_translit": "Vritta-chibukah snehee kutumba-vatsalo janah",
        "phala_en": "Affectionate, family-oriented, cooperative.",
        "phala_hi": "Sneh-shil, parivar-priya, sahyogi.",
        "bhagya": 70, "karya": 65,
    },
    "tikshna": {
        "sanskrit": "तीक्ष्ण चिबुक", "translit": "Tikshna Chibuka", "english": "Pointed Chin",
        "shloka": "तीक्ष्ण-चिबुकः चतुरः वाक्-चतुरः विवाद-प्रियः",
        "shloka_translit": "Teekshna-chibukah chaturah vaak-chaturah vivaada-priyah",
        "phala_en": "Sharp intellect, may be argumentative.",
        "phala_hi": "Teekshna buddhi, vivad-priya.",
        "bhagya": 65, "karya": 70,
    },
    "dvigan": {
        "sanskrit": "द्वि-चिबुक", "translit": "Dvi-Chibuka", "english": "Double / Cleft Chin",
        "shloka": "द्वि-चिबुकः अन्तर्द्वन्द्वी कलात्-रत्न उच्यते",
        "shloka_translit": "Dvi-chibukah antardvandvee kalaat-ratna uchyate",
        "phala_en": "Inner-conflict, dual nature, but creative talent.",
        "phala_hi": "Antar-dwand, par rachnatmak pratibha.",
        "bhagya": 65, "karya": 70,
    },
}


# 8. KARNA (ears) — 5 types — NEW v2
KARNA_TYPES = {
    "deergha": {
        "sanskrit": "दीर्घ कर्ण", "translit": "Deergha Karna", "english": "Long Ears",
        "shloka": "दीर्घ-कर्णो दीर्घायुः बुद्धि-सम्पन्नः सदा",
        "shloka_translit": "Deergha-karno deerghaayuh buddhi-sampannah sadaa",
        "phala_en": "Long life (deergha-aayu), wisdom, royal indication. Buddha-like.",
        "phala_hi": "Deergha aayu, buddhi-sampann, raja-tulya. Buddha-jaisa.",
        "is_auspicious": True, "aayu": 90, "buddhi": 85,
    },
    "vrutta": {
        "sanskrit": "वृत्त कर्ण", "translit": "Vrutta Karna", "english": "Round Ears",
        "shloka": "वृत्त-कर्णः सुख-भोगी मित्र-वत्सल उच्यते",
        "shloka_translit": "Vritta-karnah sukha-bhogee mitra-vatsala uchyate",
        "phala_en": "Sukh-priya, friend-loving, prosperity.",
        "phala_hi": "Sukh-priya, mitra-vatsal, samriddhi.",
        "is_auspicious": True, "aayu": 70, "buddhi": 65,
    },
    "lambit": {
        "sanskrit": "लम्बित कर्ण", "translit": "Lambit Karna", "english": "Hanging Lobed Ears",
        "shloka": "लम्बित-कर्णः धन-धान्य-सम्पन्नः सौभाग्यवान्",
        "shloka_translit": "Lambita-karnah dhana-dhaanya-sampannah saubhaagyavaan",
        "phala_en": "Hanging lobes — wealth, grain, fortune. Highly auspicious in Buddhist & Hindu texts.",
        "phala_hi": "Lambe karna-pal — dhan, dhanya, saubhagya. Buddha-lakshana.",
        "is_auspicious": True, "aayu": 80, "buddhi": 75,
    },
    "alpa": {
        "sanskrit": "अल्प कर्ण", "translit": "Alpa Karna", "english": "Small Ears",
        "shloka": "अल्प-कर्णः चञ्चलः क्वचित् धैर्य-हीन उच्यते",
        "shloka_translit": "Alpa-karnah chanchalah kvachit dhairya-heena uchyate",
        "phala_en": "Restless, may lack patience, quick-tempered.",
        "phala_hi": "Chanchal, dhairya kam, jaldi krodh.",
        "is_auspicious": False, "aayu": 60, "buddhi": 60,
    },
    "samya": {
        "sanskrit": "सम्य कर्ण", "translit": "Samya Karna", "english": "Balanced Ears",
        "shloka": "सम्य-कर्णः मध्यम-भाग्यः सम-स्वभावी जनः",
        "shloka_translit": "Samya-karnah madhyama-bhaagyah sama-svabhaavee janah",
        "phala_en": "Balanced, moderate fortune, even disposition.",
        "phala_hi": "Santulit, madhyam bhagya.",
        "is_auspicious": True, "aayu": 70, "buddhi": 70,
    },
}


# 9. KAPOLA (cheeks) — Lakshmi-sthan — NEW v2
KAPOLA_TYPES = {
    "purna": {
        "sanskrit": "पूर्ण कपोल", "translit": "Purna Kapola", "english": "Full Cheeks",
        "shloka": "पूर्ण-कपोलो धनवान् लक्ष्मी-वासः शुभ-प्रदः",
        "shloka_translit": "Poorna-kapolo dhanavaan Lakshmi-vaasah shubha-pradah",
        "phala_en": "Wealth, Lakshmi-vaasa (abode of fortune), prosperous life.",
        "phala_hi": "Dhanvan, Lakshmi-vaas, samriddh jeevan.",
        "is_auspicious": True, "dhana": 85, "saubhagya": 85,
    },
    "ucca": {
        "sanskrit": "उच्च कपोल", "translit": "Ucca Kapola", "english": "High Cheekbones",
        "shloka": "उच्च-कपोलः शूरः कीर्ति-मान् नायक-स्वभावः",
        "shloka_translit": "Uchcha-kapolah shoorah keerti-maan naayaka-svabhaavah",
        "phala_en": "Courageous, famous, leadership quality.",
        "phala_hi": "Sahasi, yashasvi, neta.",
        "is_auspicious": True, "dhana": 70, "saubhagya": 75,
    },
    "ksheen": {
        "sanskrit": "क्षीण कपोल", "translit": "Ksheen Kapola", "english": "Thin / Hollow Cheeks",
        "shloka": "क्षीण-कपोलः चिन्तातुरः धन-कष्टम् अनुभवेत्",
        "shloka_translit": "Ksheena-kapolah chintaaturah dhana-kashtam anubhavet",
        "phala_en": "Anxious tendency, wealth-related struggles.",
        "phala_hi": "Chinta-pravan, dhan-sambandhi sangharsh.",
        "is_auspicious": False, "dhana": 50, "saubhagya": 50,
    },
    "samanya": {
        "sanskrit": "सामान्य कपोल", "translit": "Samanya Kapola", "english": "Average Cheeks",
        "shloka": "सामान्य-कपोलो मध्यम-भाग्यो भवेत् सदा",
        "shloka_translit": "Saamaanya-kapolo madhyama-bhaagyo bhavet sadaa",
        "phala_en": "Balanced fortune, moderate.",
        "phala_hi": "Santulit bhagya.",
        "is_auspicious": True, "dhana": 65, "saubhagya": 65,
    },
}


# 10. HANU (jaw) — Bala-sthan — NEW v2
HANU_TYPES = {
    "mahabala": {
        "sanskrit": "महा-बल हनु", "translit": "Mahabala Hanu", "english": "Strong / Wide Jaw",
        "shloka": "महा-बल-हनुः शूरः कर्म-निष्ठो दृढ-व्रतः",
        "shloka_translit": "Mahaa-bala-hanuh shoorah karma-nishtho dridha-vratah",
        "phala_en": "Great strength, action-committed, dharma-firm.",
        "phala_hi": "Maha-bal, karma-nishth, dharma-drid.",
        "bala": 90, "karya": 85,
    },
    "samya": {
        "sanskrit": "सम्य हनु", "translit": "Samya Hanu", "english": "Balanced Jaw",
        "shloka": "सम्य-हनुः मध्यम-बलो स्थिर-स्वभावी सदा",
        "shloka_translit": "Samya-hanuh madhyama-balo sthira-svabhaavee sadaa",
        "phala_en": "Moderate strength, stable disposition.",
        "phala_hi": "Madhyam-bal, sthir swabhav.",
        "bala": 70, "karya": 70,
    },
    "tanu": {
        "sanskrit": "तनु हनु", "translit": "Tanu Hanu", "english": "Thin / Narrow Jaw",
        "shloka": "तनु-हनुः मृदु-शीलः कोमल-स्वभावकः क्वचित्",
        "shloka_translit": "Tanu-hanuh mridu-sheelah komala-svabhaavakah kvachit",
        "phala_en": "Soft-natured, refined, may lack physical aggression.",
        "phala_hi": "Komal, mridu, sharirik bal kam.",
        "bala": 50, "karya": 60,
    },
    "vakra": {
        "sanskrit": "वक्र हनु", "translit": "Vakra Hanu", "english": "Asymmetric Jaw",
        "shloka": "वक्र-हनुः कुटिल-भावी कर्म-विघ्न-योगकः",
        "shloka_translit": "Vakra-hanuh kutila-bhaavee karma-vighna-yogakah",
        "phala_en": "May face karma-obstacles, traditional reading suggests guarded behaviour.",
        "phala_hi": "Karma me vighn-yog, paramparik reading.",
        "bala": 55, "karya": 55,
    },
}


# 11. MUKHA-VARNA (4 classical complexion) — NEW v2
MUKHA_VARNA = {
    "gaura": {
        "sanskrit": "गौर वर्ण", "translit": "Gaura Varna", "english": "Fair / Lustrous",
        "shloka": "गौर-वर्णः सौभाग्यवान् राज-कुल-समाश्रितः",
        "shloka_translit": "Gaura-varnah saubhaagyavaan raaja-kula-samaashritah",
        "phala_en": "Auspicious in classical texts — luminous, royal-kula. (Modern note: ALL varna are equally noble; this is classical text wording only).",
        "phala_hi": "Shubh — Lakshmi-pradayak. (Aaj ke samay me sabhi varna saman hain).",
        "guna": "Sattva-pradhan",
    },
    "shyama": {
        "sanskrit": "श्याम वर्ण", "translit": "Shyama Varna", "english": "Wheat / Medium",
        "shloka": "श्याम-वर्णः मध्यम-भोगी कर्म-शीलो जनः",
        "shloka_translit": "Shyaama-varnah madhyama-bhogee karma-sheelo janah",
        "phala_en": "Medium complexion — balanced enjoyment, action-oriented. Krishna-varna in some texts.",
        "phala_hi": "Madhyam-bhog, karma-shil. Krishna-varna bhi kaha gaya.",
        "guna": "Sattva-Rajas mishrit",
    },
    "krishna": {
        "sanskrit": "कृष्ण वर्ण", "translit": "Krishna Varna", "english": "Dark / Deep",
        "shloka": "कृष्ण-वर्णः गम्भीरः बुद्धिमान् दीर्घ-दर्शी सदा",
        "shloka_translit": "Krishna-varnah gambheerah buddhimaan deergha-darshee sadaa",
        "phala_en": "Deep complexion — depth of character, wisdom, far-sighted. (Lord Krishna himself is Krishna-varna; classical texts honour this varna for gambhirta).",
        "phala_hi": "Gambhirta, buddhi, deergha-drishti. Krishna-bhagwan ka varna.",
        "guna": "Rajas-Tamas mishrit (gambhir)",
    },
    "pita": {
        "sanskrit": "पीत वर्ण", "translit": "Pita Varna", "english": "Yellowish / Golden",
        "shloka": "पीत-वर्णः कान्तिमान् पित्त-प्रकृति-युक्तः",
        "shloka_translit": "Peeta-varnah kaantimaan pitta-prakriti-yuktah",
        "phala_en": "Golden lustre — Pitta-prakriti, intelligence, charisma.",
        "phala_hi": "Kanti-yukt, Pitta-prakriti, buddhi, akarshan.",
        "guna": "Pitta-pradhan",
    },
}


# Pancha-Lakshana (5 auspicious marks) — v2 expands to 7 (Sapta-Lakshana)
SAPTA_LAKSHANA_DEFS = {
    "vishala_lalata":     "Broad, smooth forehead",
    "padma_netra":        "Lotus/fish/elephant eyes",
    "high_bridge_nasika": "Garuda/Singha-style nose",
    "bimba_oshtha":       "Full, well-formed lips",
    "drid_chibuka":       "Strong chin",
    "deergha_karna":      "Long ears (Buddha-lakshana)",  # NEW
    "purna_kapola":       "Full Lakshmi-vaasa cheeks",     # NEW
}


# ─────────────────────────────────────────────────────────────────────────────
#  CLASSIFIERS
# ─────────────────────────────────────────────────────────────────────────────
def _classify_mukha_akriti(anthro, geom, p_geom):
    if not anthro: return "samanya"
    shape = (anthro.get("face_shape_7") or {}).get("shape", "").lower()
    fwhr  = (p_geom or {}).get("fwhr", 0)
    mapping = {
        "round":"vrutta","oval":"deergha","oblong":"ardhachandra",
        "heart":"hrid","diamond":"trikona","triangle":"trikona",
        "inverted_triangle":"trikona","square":"chaturasra","rectangle":"chaturasra",
    }
    base = mapping.get(shape, "samanya")
    # Vyaghra override — very high fWHR + square jaw
    if fwhr and fwhr > 2.05 and base in ("chaturasra","vishala"): return "vyaghra"
    # Pakshi override — long+narrow
    if base == "deergha" and (anthro.get("ratios") or {}).get("face_height_to_width", 1.45) > 1.65:
        return "pakshi"
    return base

def _classify_lalata(anthro):
    if not anthro: return "samya"
    cls = (anthro.get("classifications") or {})
    fc = cls.get("forehead_class","").lower()
    fs = cls.get("forehead_slope_class","").lower()
    if "broad" in fc:    return "vishala"
    if "narrow" in fc:   return "alpa"
    if "receding" in fs: return "nimna"
    if "vertical" in fs or "prominent" in fs: return "unnata"
    return "samya"

def _classify_bhru(anthro):
    if not anthro: return "padma"
    arch = (anthro.get("classifications") or {}).get("brow_arch_class","").lower()
    if "highly_arched" in arch:                  return "chandra"
    if "arched" in arch:                          return "padma"
    if "rounded" in arch or "soft" in arch:       return "ardhachandra"
    if "straight" in arch or "flat" in arch:      return "rju"
    if "thick" in arch:                            return "ghana"
    return "padma"

def _classify_netra(anthro, p_geom):
    cls = (anthro or {}).get("classifications", {})
    eo = cls.get("eye_openness_class","").lower()
    ct = cls.get("canthal_tilt_class","").lower()
    if "almond" in ct and "wide" in eo: return "padma"
    if "upturned" in ct and "almond" in ct: return "mina"
    if "large" in eo or "wide" in eo: return "khanjana"
    if "downturned" in ct: return "mriga"
    if "small" in eo and "deep" in eo: return "gaja"
    if "intense" in ct or "narrow" in eo: return "vyaghra"
    if "round" in ct: return "shuka"
    if "upturned" in ct: return "singha"
    return "padma"

def _classify_nasika(anthro, p_geom, gender):
    if not anthro: return "samanya"
    nw = (p_geom or {}).get("nose_width_iod", 0.40)
    nl = (p_geom or {}).get("nose_length_face_ratio", 0.27)
    np_ = (anthro.get("angles_deg") or {}).get("nose_tip_projection", 0)
    # gender-aware thresholds (M tend to broader/longer)
    g = (gender or "U").upper()
    nw_garuda = 0.42 if g == "M" else 0.38
    if nl > 0.29 and np_ < -10 and nw < nw_garuda + 0.02: return "garuda"
    if nw > 0.46 and nl > 0.27: return "singha"
    if nw < 0.36 and nl < 0.25: return "mrigi"
    if nw < 0.39 and np_ < -10: return "shuka"
    if nl > 0.30 and nw > 0.40: return "gaja"
    if nw > 0.50: return "vrushabha"
    if nw > 0.45 and np_ > 5: return "khar"
    return "samanya"

def _classify_oshtha(p_geom):
    lf = (p_geom or {}).get("lip_fullness_iod", 0.20)
    mw = (p_geom or {}).get("mouth_width_iod", 0.80)
    if lf > 0.27 and mw > 0.85: return "bimba"
    if lf > 0.22:                return "padma"
    if lf < 0.13:                return "tanu"
    if lf > 0.30:                return "sthula"
    return "samanya"

def _classify_chibuka(anthro):
    if not anthro: return "vrutta"
    jc = (anthro.get("classifications") or {}).get("face_shape_jaw_class","").lower()
    if "square" in jc: return "drid"
    if "round" in jc:  return "vrutta"
    if "pointed" in jc or "v_shape" in jc: return "tikshna"
    return "vrutta"

def _classify_karna(anthro, p_geom):
    """Ear classification — uses ear-to-face ratio if available, else heuristics."""
    if not anthro: return "samya"
    # Approximate via face height & ear region (Mediapipe limited for ears)
    face_h = (anthro.get("ratios") or {}).get("face_height_to_width", 1.45)
    if face_h > 1.55: return "deergha"   # long face → likely longer ears
    if face_h < 1.30: return "vrutta"
    return "samya"

def _classify_kapola(anthro, p_geom, fwhr_result):
    """Cheek classification — uses cheek prominence + fWHR."""
    cp = (p_geom or {}).get("cheek_prominence", 0.5)
    fwhr_val = ((fwhr_result or {}).get("fwhr") or {}).get("primary", {}).get("value", 1.85)
    if cp > 0.62 and fwhr_val > 1.95: return "ucca"
    if cp > 0.55: return "purna"
    if cp < 0.40: return "ksheen"
    return "samanya"

def _classify_hanu(anthro, fwhr_result, symmetry_result):
    """Jaw — separate from chin. Uses jaw width + asymmetry."""
    if not anthro: return "samya"
    fwhr_val = ((fwhr_result or {}).get("fwhr") or {}).get("primary", {}).get("value", 1.85)
    asym = ((symmetry_result or {}).get("global_asymmetry_score") or 0)
    if asym > 8.0: return "vakra"
    if fwhr_val > 2.0: return "mahabala"
    if fwhr_val < 1.65: return "tanu"
    return "samya"

def _classify_mukha_varna(health_result):
    """Complexion classification from skin LAB (Engine 5)."""
    if not health_result or not health_result.get("ok"):
        return "shyama"  # default to medium
    skin = (health_result.get("skin_quality") or {})
    L = skin.get("lab_L_mean", 60)
    b = skin.get("lab_b_mean", 15)
    if L > 70: return "gaura"
    if L < 45: return "krishna"
    if b > 20: return "pita"
    return "shyama"


# ─────────────────────────────────────────────────────────────────────────────
#  TRINETRA-STHAN (third-eye region) — NEW v2
# ─────────────────────────────────────────────────────────────────────────────
def _trinetra_analysis(anthro, symmetry_result):
    """Bhagya-bindu region between brows."""
    if not anthro: return None
    bs = (anthro.get("ratios") or {}).get("brow_separation_iod", 0.95)
    sym_score = (symmetry_result or {}).get("symmetry_score", 75)
    if bs > 1.10:
        cls = "vishala_trinetra"
        phala_en = "Wide Trinetra-sthan — open mind, spiritual receptivity, artistic vision."
        phala_hi = "Vishal trinetra-sthan — khula man, aadhyatmik gun, kala-drishti."
        bhagya = 80
    elif bs < 0.80:
        cls = "sankuchit_trinetra"
        phala_en = "Narrow Trinetra-sthan — focused mind, may be intense or worried."
        phala_hi = "Sankuchit — kendrit man, par chinta-pravan."
        bhagya = 60
    else:
        cls = "samya_trinetra"
        phala_en = "Balanced Trinetra-sthan — harmonious between intuition and reason."
        phala_hi = "Santulit — antar-jnan aur tark dono ka mel."
        bhagya = 75
    return {
        "sanskrit": "त्रिनेत्र-स्थान",
        "translit": "Trinetra-Sthan (Bhagya-Bindu)",
        "english": "Third-eye / Glabella region",
        "classification": cls,
        "shloka": "त्रिनेत्र-स्थानं भाग्य-बिन्दुः आज्ञा-चक्र-समाश्रितम्",
        "shloka_translit": "Trinetra-sthaanam bhaagya-binduh aajnaa-chakra-samaashritam",
        "phala_english": phala_en,
        "phala_hinglish": phala_hi,
        "bhagya_indicator": bhagya,
        "spiritual_note": "Aajna-chakra ka sthal — Bhrumadhya. Dhyan + tilaka isi sthan par.",
        "ref": "Yoga_Tattva_Upanishad_Aajna_Chakra",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  MARMA-STHAN (Sushruta Samhita facial Marmas) — NEW v2
# ─────────────────────────────────────────────────────────────────────────────
def _marma_sthan_facial():
    """Sushruta Samhita Sharir-sthan describes 107 marmas; 12 on face/head."""
    return {
        "ref": "Sushruta_Samhita_Sharir_Sthana_6_Pratyeka_Marma",
        "total_facial_marmas": 12,
        "primary_facial_marmas": [
            {"name": "Sthapani", "sanskrit": "स्थापनी",
             "location": "Trinetra-sthan / glabella (between brows)",
             "type": "Sira-marma", "vital_organ": "Manas (mind), Aajna-chakra",
             "english": "Sthapani Marma — most vital facial energy point. Tilaka here activates intuition."},
            {"name": "Apanga", "sanskrit": "अपाङ्ग",
             "location": "Outer canthus of each eye (×2)",
             "type": "Sira-marma", "vital_organ": "Eyes, vision",
             "english": "Apanga Marma — outer eye corner. Governs eyesight & emotional expression."},
            {"name": "Avarta", "sanskrit": "आवर्त",
             "location": "Above middle of each eyebrow (×2)",
             "type": "Sira-marma", "vital_organ": "Eye function, brow energy",
             "english": "Avarta Marma — over each brow. Governs facial expression & forehead vital force."},
            {"name": "Shankha", "sanskrit": "शङ्ख",
             "location": "Temple region (×2)",
             "type": "Asthi-marma", "vital_organ": "Sushumna-nadi, hearing",
             "english": "Shankha Marma — temples. Critical vital point; governs auditory function."},
            {"name": "Utkshepa", "sanskrit": "उत्क्षेप",
             "location": "Above ear (×2)",
             "type": "Snayu-marma", "vital_organ": "Cranial nerves",
             "english": "Utkshepa Marma — above-ear. Mild stimulation aids mental clarity."},
            {"name": "Phana", "sanskrit": "फण",
             "location": "Side of nose / nostril ridge (×2)",
             "type": "Sira-marma", "vital_organ": "Olfactory function, Prana-vahini",
             "english": "Phana Marma — nostril side. Governs breath and smell perception."},
            {"name": "Shringataka", "sanskrit": "शृङ्गाटक",
             "location": "Inside head — convergence of nasal, ophthalmic, lingual, auditory channels",
             "type": "Sira-marma", "vital_organ": "All cranial sense organs",
             "english": "Shringataka Marma — internal cranial confluence. One of 3 maha-marmas of head."},
        ],
        "wellness_note": "Daily Mukha-Abhyanga (face oil massage) over these marmas "
                          "with sesame/coconut oil promotes Ojas, calms Vata, balances dosha.",
        "disclaimer": "For wellness reference. Marma therapy must be done by trained Ayurveda practitioner.",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  TILAKA / BINDU / TIL — NEW v2
# ─────────────────────────────────────────────────────────────────────────────
def _tilaka_phala_placeholder():
    """Mole/bindu phala framework — actual detection in Engine 19."""
    return {
        "status": "framework_only",
        "note": "Til (mole) detection requires colour blob analysis — implemented in Engine 19 Predictive Synthesis.",
        "classical_phala_chart": {
            "lalata_madhya":  "Forehead centre — Bhagya-vardhak (fortune-enhancing)",
            "lalata_dakshin": "Right forehead — Yash, but Karya-vighn",
            "lalata_vaam":    "Left forehead — Vidya, sambandh me utar-chadhav",
            "bhru_madhya":    "Between brows — Sthapani-marma — atyant shubh, dhyani gun",
            "kapola_dakshin": "Right cheek — Saubhagya, pati/patni-sukh",
            "kapola_vaam":    "Left cheek — Dhan-sangrah me badha",
            "nasika_agra":    "Nose tip — Karya-vighn, jaldi-baazi",
            "oshtha_upari":   "Upper lip — Vakta, akarshan",
            "chibuka":        "Chin — Drid sankalp, kintu zid",
        },
        "ref": "Bhrigu_Samhita_Til_Lakshana + Samudrika_Til_Adhyaya",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  PANCHA-MAHABHUTA (5 elements facial mapping) — NEW v2
# ─────────────────────────────────────────────────────────────────────────────
def _pancha_mahabhuta(mukha, oshtha, anthro, p_geom, health_result):
    """Map face features to 5 elements — Prithvi/Jal/Agni/Vayu/Akash.

    v3 — continuous scoring: every element gets a baseline + categorical bonuses
    + continuous geometric/skin signals. Avoids "single element gets 100%" bias.
    """
    # Continuous inputs (with safe defaults)
    ratios = (anthro or {}).get("ratios") or {}
    fwhr   = ratios.get("fwhr") or ratios.get("fwhr_value") or 1.85
    jaw_w  = ratios.get("jaw_width_iod") or 1.0
    face_h = ratios.get("face_height_iod") or 1.85
    bs     = ratios.get("brow_separation_iod") or 0.95
    lip_th = ratios.get("lip_thickness_iod") or 0.18
    foreh  = ratios.get("forehead_height_iod") or 0.65

    cp = (p_geom or {}).get("cheek_prominence", 0.5)
    skin = (health_result or {}).get("skin_clarity_0_100") or \
           (health_result or {}).get("macro_indicators", {}).get("skin_clarity") or 50
    vit  = (health_result or {}).get("vitality_0_100") or \
           (health_result or {}).get("macro_indicators", {}).get("vitality") or 50

    # ── Baseline 1.0 each, so no element collapses to 0 unless all signals oppose ──
    prithvi = jal = agni = vayu = akash = 1.0

    # Prithvi (earth) — broad/stable: square face, wide jaw, full lips, low fwhr
    if mukha in ("chaturasra", "vishala", "vrutta"): prithvi += 2.0
    if oshtha in ("sthula", "bimba"):                prithvi += 1.0
    prithvi += max(0.0, (jaw_w - 0.95) * 6.0)        # wide jaw → up to +2
    prithvi += max(0.0, (1.85 - fwhr) * 2.5)         # low fwhr → grounded

    # Jal (water) — soft/full: round face, full lips, smooth skin
    if mukha in ("vrutta", "hrid"):                  jal += 2.0
    if oshtha in ("bimba", "padma", "sthula"):       jal += 1.0
    jal += max(0.0, (lip_th - 0.18) * 12.0)          # plumper lips → +0..3
    jal += max(0.0, (skin - 60) / 40.0) * 1.5        # clear skin → +0..1.5

    # Agni (fire) — sharp/intense: triangular face, high cheek, high fwhr, high vitality
    if mukha in ("trikona", "vyaghra"):              agni += 2.0
    agni += max(0.0, (cp - 0.50) * 6.0)              # cheekbones → +0..3
    agni += max(0.0, (fwhr - 1.85) * 2.5)            # high fwhr → fire
    agni += max(0.0, (vit - 55) / 45.0) * 1.5        # vitality → fire

    # Vayu (air) — narrow/thin: long face, thin lips, dry/asymmetric
    if mukha in ("deergha", "pakshi"):               vayu += 2.0
    if oshtha == "tanu":                             vayu += 1.0
    vayu += max(0.0, (face_h - 1.85) * 2.5)          # taller face → vayu
    vayu += max(0.0, (0.18 - lip_th) * 12.0)         # thinner lips → vayu

    # Akash (ether) — spacious/open: wide brow gap, tall forehead
    akash += max(0.0, (bs - 0.95) * 8.0)             # brow separation → +0..2
    akash += max(0.0, (foreh - 0.60) * 6.0)          # tall forehead → +0..2
    if mukha in ("vishala",):                        akash += 1.0

    total = prithvi + jal + agni + vayu + akash
    if total <= 0: total = 1.0
    pcts = {
        "prithvi_pct": round(prithvi*100/total, 1),
        "jal_pct":     round(jal*100/total, 1),
        "agni_pct":    round(agni*100/total, 1),
        "vayu_pct":    round(vayu*100/total, 1),
        "akash_pct":   round(akash*100/total, 1),
    }
    primary = max(pcts.items(), key=lambda x: x[1])[0].replace("_pct","")
    element_meaning = {
        "prithvi": "Earth — sthirta, bal, sahan-shakti, dhairya.",
        "jal":     "Water — bhavna, prem, prabhav, raam.",
        "agni":    "Fire — tej, krodh, netritva, parivartan.",
        "vayu":    "Air — chanchalata, vichar, vakta, gati.",
        "akash":   "Ether — vishalta, vairagya, atma-jnan, anant.",
    }
    return {
        **pcts,
        "primary_mahabhuta": primary,
        "primary_meaning":  element_meaning.get(primary,""),
        "ref": "Sankhya_Darshan_Pancha_Mahabhuta + Charaka_Samhita",
        "note": "Mahabhuta dominance shapes prakriti, nature, and life themes per Vedic darshan.",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  YOGAS (9 — v2 added 4)
# ─────────────────────────────────────────────────────────────────────────────
def _detect_yogas(mukha, lalata, bhru, netra, nasika, oshtha, chibuka,
                   karna, kapola, hanu, varna, sapta_count):
    yogas = []
    def add(name, sk, en, hi, ref):
        yogas.append({"name": name, "sanskrit": sk, "phala_en": en, "phala_hi": hi, "ref": ref})

    if nasika == "garuda" and netra in ("padma","singha","gaja") and lalata == "vishala":
        add("Raja Yoga", "राज योग",
            "Royal favour, leadership, lasting fame and wealth.",
            "Adhipati gun, netritva, sthayi yash aur dhan.",
            "Brihat_Samhita_Yoga_Sec")
    if nasika in ("vrushabha","gaja") and mukha in ("vrutta","vishala") and oshtha in ("bimba","padma"):
        add("Dhana Yoga", "धन योग",
            "Strong wealth-accumulation. Steady prosperity through enterprise.",
            "Vyavasaya se sthir samriddhi.",
            "Garuda_Purana_Dhana_Lakshana")
    if lalata in ("vishala","unnata") and netra in ("padma","khanjana","gaja") and oshtha in ("padma","bimba"):
        add("Saraswati Yoga", "सरस्वती योग",
            "Saraswati's blessing — exceptional intellect, scholarship, eloquence.",
            "Vishesh buddhi, vidya, vakta-shakti.",
            "Samudrika_Vidya_Yoga")
    if netra == "gaja" and chibuka == "drid":
        add("Gajakesari Yoga (mukha-rupa)", "गजकेसरी योग (मुख-रूप)",
            "Gaja-eyes + Lion-jaw — wisdom + power.",
            "Buddhi aur shakti dono.",
            "Brihat_Samhita_Gajakesari")
    if mukha == "vrutta" and bhru in ("padma","chandra") and oshtha in ("bimba","padma"):
        add("Soumya Yoga", "सौम्य योग",
            "Lakshmi-kripa, peaceful relationships, beauty.",
            "Lakshmi-kripa, shanti-purna sambandh, saundarya.",
            "Hasta_Samudrika_Soumya")
    if sapta_count >= 5:
        add("Sapta-Lakshana Yoga", "सप्त-लक्षण योग",
            f"{sapta_count}/7 auspicious marks — exceptional Bhagya combination.",
            f"{sapta_count}/7 shubh chinh — vishesh bhagya-yog.",
            "Brihat_Samhita_Pancha_Lakshana_Extended")

    # NEW v2 yogas
    if karna == "deergha" and lalata == "vishala" and netra in ("padma","gaja"):
        add("Maha-Bhagya Yoga", "महा-भाग्य योग",
            "Long ears + broad forehead + lotus eyes — Buddha-like supreme fortune.",
            "Buddha-jaisa maha-bhagya-yog.",
            "Lakshana_Sangraha_Maha_Bhagya")

    # Vipreet-Raja: small features but highly auspicious arrangement
    if mukha == "alpa" and netra in ("padma","gaja") and nasika == "garuda":
        add("Vipreet-Raja Yoga", "विपरीत-राज योग",
            "Reversal-yoga — adversity becomes the path to greatness.",
            "Vipatti hi vijay ka maarg banti hai.",
            "Phala_Deepika_Vipreet")

    if kapola == "purna" and oshtha == "bimba" and mukha in ("vrutta","hrid"):
        add("Lakshmi-Narayan Yoga", "लक्ष्मी-नारायण योग",
            "Full cheeks + Bimba lips + round/heart face — divine couple's blessing, marital bliss + wealth.",
            "Lakshmi-Narayan ki sanyukt kripa — vivah-sukh aur dhan.",
            "Lakshmi_Tantra_Lakshana")

    if hanu == "mahabala" and mukha == "vishala" and nasika in ("garuda","singha"):
        add("Akhand-Samrajya Yoga", "अखण्ड-साम्राज्य योग",
            "Unbroken-empire yoga — leadership over a vast domain (literal or metaphorical).",
            "Vishal kshetra par adhipatya — vyavasaya/karya me.",
            "Brihat_Parashara_Akhand_Samrajya")

    return yogas


# ─────────────────────────────────────────────────────────────────────────────
#  PANCHA → SAPTA-LAKSHANA (now 7 marks)
# ─────────────────────────────────────────────────────────────────────────────
def _count_sapta_lakshana(lalata, netra, nasika, oshtha, chibuka, karna, kapola):
    marks = {
        "vishala_lalata":     lalata in ("vishala","samya","unnata"),
        "padma_netra":        netra in ("padma","mina","gaja","khanjana"),
        "high_bridge_nasika": nasika in ("garuda","singha","shuka"),
        "bimba_oshtha":       oshtha in ("bimba","padma"),
        "drid_chibuka":       chibuka in ("drid",),
        "deergha_karna":      karna in ("deergha","lambit"),     # NEW
        "purna_kapola":       kapola in ("purna","ucca"),         # NEW
    }
    count = sum(1 for v in marks.values() if v)
    return {
        "marks_present": marks,
        "count": count,
        "total": 7,
        "phala_en": (
            f"Sapta-Lakshana sampurna — all 7 auspicious marks present, supreme bhagya."
            if count == 7 else
            f"{count}/7 Sapta-Lakshana present — "
            f"{'atyant shubh' if count >= 6 else 'bahut shubh' if count >= 5 else 'shubh' if count >= 3 else 'madhyam'}."
        ),
        "phala_hi": (
            f"7 me se {count} Sapta-Lakshana shubh chinh — "
            f"{'atyant shubh — maha-bhagya' if count >= 6 else 'bahut shubh' if count >= 5 else 'shubh' if count >= 3 else 'madhyam-shubh'}."
        ),
        "ref": "Brihat_Samhita_Pancha_Lakshana_Sapta_Vistaar",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  SAUBHAGYA-PHALA in 3 timeframes (Purva/Madhya/Uttara aayu) — NEW v2
# ─────────────────────────────────────────────────────────────────────────────
def _saubhagya_phala_aayu(composite, sapta_count, n_yogas, gender):
    bhagya = composite["bhagya_score"]
    purva  = round(_clip(bhagya - 5 + sapta_count*1), 1)  # early life
    madhya = round(_clip(bhagya + n_yogas*2), 1)          # mid life
    uttara = round(_clip(bhagya + 5 + n_yogas*1), 1)      # later life
    return {
        "purva_aayu_0_25": {
            "score": purva,
            "phala_en": f"Early life — Bhagya score {purva}. " +
                         ("Foundational stability and family support indicated."
                          if purva >= 65 else "Karma-pradhan early years; effort builds foundation."),
            "phala_hi": "Bal-yauvan kaal — " +
                         ("Sthir base, parivar-poshak." if purva >= 65 else "Mehnat se neev banegi."),
        },
        "madhya_aayu_25_50": {
            "score": madhya,
            "phala_en": f"Middle life — Bhagya score {madhya}. " +
                         ("Peak career & wealth period; yoga-fal active."
                          if madhya >= 70 else "Steady progress through dharma & karma."),
            "phala_hi": "Madhya-kaal — " +
                         ("Karya-yog ka shikhar." if madhya >= 70 else "Dharma-karma se sthir gati."),
        },
        "uttara_aayu_50_plus": {
            "score": uttara,
            "phala_en": f"Later life — Bhagya score {uttara}. " +
                         ("Wisdom recognition, respect, spiritual fruition."
                          if uttara >= 70 else "Reflective period; emphasis on bhakti-marg."),
            "phala_hi": "Uttara-kaal — " +
                         ("Jnan, samman, atma-prapti." if uttara >= 70 else "Bhakti-marg, antar-mukhata."),
        },
        "ref": "Brihat_Samhita_Aayu_Phala + Phala_Deepika",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  COMPOSITE SCORES
# ─────────────────────────────────────────────────────────────────────────────
def _composite_scores(mukha_d, lalata_d, bhru_d, netra_d, nasika_d, oshtha_d,
                       chibuka_d, karna_d, kapola_d, hanu_d, sapta_count, n_yogas,
                       health_result):
    bhagya, buddhi, dhana, sambandha, aayu, bala = [], [], [], [], [], []
    for d in [mukha_d, lalata_d, netra_d, nasika_d]:
        for k, lst in [("bhagya",bhagya),("buddhi",buddhi),("dhana",dhana),
                        ("sambandha",sambandha),("aayu",aayu)]:
            if d.get(k): lst.append(d[k])
    for d in [bhru_d, oshtha_d]:
        if d.get("bhagya"):    bhagya.append(d["bhagya"])
        if d.get("sambandha"): sambandha.append(d["sambandha"])
    if karna_d.get("aayu"):    aayu.append(karna_d["aayu"])
    if karna_d.get("buddhi"):  buddhi.append(karna_d["buddhi"])
    if kapola_d.get("dhana"):  dhana.append(kapola_d["dhana"])
    if kapola_d.get("saubhagya"): bhagya.append(kapola_d["saubhagya"])
    if hanu_d.get("bala"):     bala.append(hanu_d["bala"])

    base_b = sum(bhagya)/len(bhagya) if bhagya else 60
    base_b = _clip(base_b + sapta_count*2 + n_yogas*4)
    cs = {
        "bhagya_score":    round(base_b,1),
        "buddhi_score":    round(sum(buddhi)/len(buddhi) if buddhi else 60,1),
        "dhana_score":     round(sum(dhana)/len(dhana)   if dhana   else 60,1),
        "sambandha_score": round(sum(sambandha)/len(sambandha) if sambandha else 60,1),
        "aayu_score":      round(sum(aayu)/len(aayu)     if aayu    else 60,1),
        "bala_score":      round(sum(bala)/len(bala)     if bala    else 65,1),
    }
    aarogya = 60
    if health_result and health_result.get("ok"):
        vit = health_result.get("vitality_score") or 60
        aarogya = round(vit*0.7 + cs["aayu_score"]*0.3, 1)
    cs["aarogya_score"] = aarogya

    cs["interpretation"] = {
        k.replace("_score",""): _interp(k.replace("_score","").title(), v)
        for k, v in cs.items() if k.endswith("_score")
    }
    return cs

def _interp(label, s):
    if s >= 80: return f"{label}: Vishesh-uttam — exceptional."
    if s >= 70: return f"{label}: Uttam — strong positive."
    if s >= 60: return f"{label}: Madhyam-shubh — moderately favourable."
    if s >= 50: return f"{label}: Madhyam — balanced."
    if s >= 40: return f"{label}: Saamanya — average, karma-dependent."
    return f"{label}: Karma-pradhan — strongly self-effort dependent."


def _dosha_preview(anthro, mukha, oshtha):
    vata = pitta = kapha = 0
    if oshtha == "tanu": vata += 2
    if mukha in ("deergha","trikona","pakshi"): vata += 2
    if (anthro or {}).get("classifications",{}).get("eye_openness_class","").lower() == "small": vata += 1
    if mukha in ("trikona","chaturasra","vyaghra"): pitta += 2
    if (anthro or {}).get("classifications",{}).get("brow_arch_class","").lower() in ("highly_arched","sharp"): pitta += 2
    if oshtha in ("bimba","padma","sthula"): kapha += 2
    if mukha in ("vrutta","vishala","hrid"): kapha += 2
    total = vata + pitta + kapha
    if total == 0: total = 1
    return {
        "vata_pct":  round(vata*100/total,1),
        "pitta_pct": round(pitta*100/total,1),
        "kapha_pct": round(kapha*100/total,1),
        "primary_dosha": max([("vata",vata),("pitta",pitta),("kapha",kapha)],key=lambda x:x[1])[0],
        "note": "Quick facial-only preview. Full Prakriti analysis in Engine 13.",
        "ref": "Charaka_Samhita_Sutrasthana_Prakriti",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN ENTRY
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
        return {"engine": "samudrika", "ok": False, "version": 2,
                 "error": "insufficient_landmarks"}

    p_geom = (personality_result or {}).get("geometric_indicators") or {}

    # Classify all 12 regions
    mukha   = _classify_mukha_akriti(anthropometry_result, {}, p_geom)
    lalata  = _classify_lalata(anthropometry_result)
    bhru    = _classify_bhru(anthropometry_result)
    netra   = _classify_netra(anthropometry_result, p_geom)
    nasika  = _classify_nasika(anthropometry_result, p_geom, gender)
    oshtha  = _classify_oshtha(p_geom)
    chibuka = _classify_chibuka(anthropometry_result)
    karna   = _classify_karna(anthropometry_result, p_geom)        # NEW
    kapola  = _classify_kapola(anthropometry_result, p_geom, fwhr_result)  # NEW
    hanu    = _classify_hanu(anthropometry_result, fwhr_result, symmetry_result)  # NEW
    varna   = _classify_mukha_varna(health_result)                  # NEW

    mukha_d   = MUKHA_AKRITI.get(mukha, MUKHA_AKRITI["vrutta"])
    lalata_d  = LALATA_TYPES.get(lalata, LALATA_TYPES["samya"])
    bhru_d    = BHRU_TYPES.get(bhru, BHRU_TYPES["padma"])
    netra_d   = NETRA_TYPES.get(netra, NETRA_TYPES["padma"])
    nasika_d  = NASIKA_TYPES.get(nasika, NASIKA_TYPES["samanya"])
    oshtha_d  = OSHTHA_TYPES.get(oshtha, OSHTHA_TYPES["samanya"])
    chibuka_d = CHIBUKA_TYPES.get(chibuka, CHIBUKA_TYPES["vrutta"])
    karna_d   = KARNA_TYPES.get(karna, KARNA_TYPES["samya"])
    kapola_d  = KAPOLA_TYPES.get(kapola, KAPOLA_TYPES["samanya"])
    hanu_d    = HANU_TYPES.get(hanu, HANU_TYPES["samya"])
    varna_d   = MUKHA_VARNA.get(varna, MUKHA_VARNA["shyama"])

    # gender-specific phala
    g = (gender or "U").upper()
    gender_specific_mukha_phala = mukha_d.get(
        "stri_phala" if g == "F" else "purusha_phala", ""
    )
    gender_lakshana_source = (
        "Brihat_Samhita_Ch70_Stri_Lakshana" if g == "F"
        else "Brihat_Samhita_Ch68_Purusha_Lakshana"
    )

    sapta = _count_sapta_lakshana(lalata, netra, nasika, oshtha, chibuka, karna, kapola)
    yogas = _detect_yogas(mukha, lalata, bhru, netra, nasika, oshtha, chibuka,
                           karna, kapola, hanu, varna, sapta["count"])

    composite = _composite_scores(mukha_d, lalata_d, bhru_d, netra_d, nasika_d,
                                    oshtha_d, chibuka_d, karna_d, kapola_d, hanu_d,
                                    sapta["count"], len(yogas), health_result)
    saubhagya = _saubhagya_phala_aayu(composite, sapta["count"], len(yogas), gender)

    dosha   = _dosha_preview(anthropometry_result, mukha, oshtha)
    trinetra = _trinetra_analysis(anthropometry_result, symmetry_result)
    marma   = _marma_sthan_facial()
    tilaka  = _tilaka_phala_placeholder()
    mahabhuta = _pancha_mahabhuta(mukha, oshtha, anthropometry_result, p_geom, health_result)

    auspicious_count = sum(1 for d in [bhru_d, netra_d, nasika_d, oshtha_d, karna_d, kapola_d]
                              if d.get("is_auspicious"))
    raja_count = sum(1 for d in [netra_d, nasika_d] if d.get("is_raja_yoga"))

    summary_en = (
        f"Mukha-Akriti: {mukha_d['english']} ({mukha_d['translit']}). "
        f"Mukha-Varna: {varna_d['translit']}. "
        f"{sapta['count']}/7 Sapta-Lakshana auspicious marks. "
        f"{len(yogas)} Vedic yoga-yog: {', '.join(y['name'] for y in yogas) if yogas else 'none of major raja-yogas'}. "
        f"Bhagya-Score: {composite['bhagya_score']}. "
        f"Pancha-Mahabhuta dominance: {mahabhuta['primary_mahabhuta'].title()}. "
        f"Primary Dosha: {dosha['primary_dosha'].title()}."
    )
    summary_hi = (
        f"Aapka mukh-akriti {mukha_d['translit']} hai, varna {varna_d['translit']}. "
        f"7 me se {sapta['count']} Sapta-Lakshana shubh chinh present. "
        f"{len(yogas)} Vedic yoga: {', '.join(y['name'] for y in yogas) if yogas else 'koi mukhya raja-yog nahi'}. "
        f"Bhagya-ank: {composite['bhagya_score']}. "
        f"Pradhan Mahabhuta: {mahabhuta['primary_mahabhuta'].title()}. "
        f"Pradhan Dosha: {dosha['primary_dosha'].title()}."
    )

    return _py({
        "engine": "samudrika",
        "version": 2,
        "ok": True,
        "shastra_name": "Samudrika Shastra",
        "shastra_devanagari": "सामुद्रिक शास्त्र",
        "method": "classical_vedic_face_reading_v2_with_shloka_marma_mahabhuta",
        "primary_sources": [
            "Brihat_Samhita_Varahamihira_Ch68_Purusha_Lakshana",
            "Brihat_Samhita_Ch70_Stri_Lakshana",
            "Garuda_Purana_Samudrika_Sec",
            "Samudrika_Shastra_attrib_Samudra",
            "Hasta_Samudrika_Shastra",
            "Sushruta_Samhita_Sharir_Sthana_Marma",
            "Charaka_Samhita_Sutrasthana_Prakriti",
            "Markandeya_Purana_Lakshana",
            "Vasishtha_Samhita",
            "Manava_Dharma_Shastra_Manu_Smriti",
            "Agni_Purana_Stri_Lakshana",
            "Bhrigu_Samhita_Til_Lakshana",
            "Yoga_Tattva_Upanishad_Aajna_Chakra",
            "Sankhya_Darshan_Pancha_Mahabhuta",
        ],
        "inputs": {
            "gender": gender, "ethnicity": ethnicity, "age": age,
            "gender_lakshana_source_used": gender_lakshana_source,
            "cross_engine_signals": {
                "anthropometry": bool(anthropometry_result and anthropometry_result.get("ok")),
                "symmetry":      bool(symmetry_result and symmetry_result.get("ok")),
                "phi":           bool(phi_result and phi_result.get("ok")),
                "fwhr":          bool(fwhr_result and fwhr_result.get("ok")),
                "health":        bool(health_result and health_result.get("ok")),
                "personality":   bool(personality_result and personality_result.get("ok")),
                "first_impression": bool(first_impression_result and first_impression_result.get("ok")),
            },
        },
        "mukha_pradesh_analysis": {
            "01_mukha_akriti": {
                "classification": mukha,
                "sanskrit_name": mukha_d["sanskrit"], "transliteration": mukha_d["translit"],
                "english_name": mukha_d["english"],
                "shloka": mukha_d["shloka"], "shloka_translit": mukha_d["shloka_translit"],
                "phala_sanskrit": mukha_d.get("phala_sanskrit",""),
                "phala_english":  mukha_d["phala_en"],
                "phala_hinglish": mukha_d["phala_hi"],
                "gender_specific_phala": gender_specific_mukha_phala,
                "karya_kshetra": mukha_d["karya"],
                "indicators": {"bhagya": mukha_d["bhagya"], "buddhi": mukha_d["buddhi"],
                               "dhana": mukha_d["dhana"], "aayu": mukha_d["aayu"],
                               "sambandha": mukha_d["sambandha"]},
                "ref": mukha_d["ref"],
            },
            "02_lalata": _region_pack(lalata, lalata_d,
                "Lalata is the Bhagya-sthan (seat of fortune & destiny)."),
            "03_bhru":   _region_pack(bhru, bhru_d,
                "Bhru govern emotional expression and Buddhi."),
            "04_netra":  _region_pack(netra, netra_d,
                "Netra reflect Manas (mind) and Atma (soul)."),
            "05_nasika": _region_pack(nasika, nasika_d,
                "Nasika reflects Dhana (wealth) and Karya-kshetra (career)."),
            "06_oshtha": _region_pack(oshtha, oshtha_d,
                "Oshtha reflect Vani (speech) and Bhog (sensual life)."),
            "07_chibuka": _region_pack(chibuka, chibuka_d,
                "Chibuka reflects Karma-shakti (work-power) and Sankalp."),
            "08_karna":  _region_pack(karna, karna_d,
                "Karna reflect Aayu (longevity) and Buddhi-shravana (listening wisdom)."),
            "09_kapola": _region_pack(kapola, kapola_d,
                "Kapola is Lakshmi-vaasa (abode of wealth-goddess)."),
            "10_hanu":   _region_pack(hanu, hanu_d,
                "Hanu reflects Bala (physical strength) and karma-execution."),
            "11_mukha_varna": {
                "classification": varna,
                "sanskrit_name": varna_d["sanskrit"], "transliteration": varna_d["translit"],
                "english_name": varna_d["english"],
                "shloka": varna_d["shloka"], "shloka_translit": varna_d["shloka_translit"],
                "phala_english":  varna_d["phala_en"],
                "phala_hinglish": varna_d["phala_hi"],
                "guna":           varna_d["guna"],
                "modern_note": "Classical Vedic complexion classification is descriptive only. "
                                "All varna are equally noble. App will NEVER use varna for any "
                                "discriminatory purpose.",
                "ref": "Brihat_Samhita_Varna_Lakshana",
            },
            "12_trinetra_sthan": trinetra,
        },
        "sapta_lakshana": sapta,
        "vedic_yogas_detected": yogas,
        "auspicious_feature_count": auspicious_count,
        "raja_yoga_feature_count":  raja_count,
        "composite_scores": composite,
        "saubhagya_phala_by_aayu": saubhagya,
        "tridosha_facial_preview": dosha,
        "pancha_mahabhuta_facial_mapping": mahabhuta,
        "marma_sthan_facial": marma,
        "tilaka_til_phala": tilaka,
        "summary_english":  summary_en,
        "summary_hinglish": summary_hi,
        "shastra_disclaimer": (
            "Samudrika Shastra is TRADITIONAL classical Vedic knowledge from Sanskrit "
            "texts (Brihat Samhita, Garuda Purana, Sushruta Samhita, Charaka Samhita, "
            "etc.). Offered for cultural-spiritual reflection only. Modern scientific "
            "validity NOT claimed. Predictions are INTERPRETIVE, not deterministic. "
            "Multiple authoritative texts may differ on phala. Karma, intention, and "
            "effort transform any indication shown here."
        ),
        "ethics_notice": (
            "These traditional readings MUST NOT be used for caste/social discrimination, "
            "marriage-rejection, employment decisions, or judgement of human worth. "
            "The classical complexion (Mukha-Varna) classification is purely descriptive "
            "from ancient texts; ALL varna are equally noble. Lord Krishna himself is "
            "Krishna-varna. Vedic shastra emphasises Karma + Bhakti supersede any lakshana. "
            "'Karmanye vadhikaraste maa phaleshu kadachana' — Bhagavad Gita 2.47."
        ),
    })


def _region_pack(classification, d, sthan_meaning=""):
    pack = {
        "classification": classification,
        "sanskrit_name": d["sanskrit"],
        "transliteration": d["translit"],
        "english_name": d["english"],
        "shloka": d.get("shloka",""),
        "shloka_translit": d.get("shloka_translit",""),
        "phala_english":  d.get("phala_en",""),
        "phala_hinglish": d.get("phala_hi",""),
    }
    if d.get("is_auspicious") is not None: pack["is_auspicious"] = d["is_auspicious"]
    if d.get("is_raja_yoga") is not None:  pack["is_raja_yoga"]  = d["is_raja_yoga"]
    if d.get("karya_kshetra"):              pack["karya_kshetra"] = d["karya_kshetra"]
    inds = {}
    for k in ("bhagya","buddhi","dhana","aayu","sambandha","karya","bala","saubhagya"):
        if d.get(k) is not None: inds[k] = d[k]
    if inds: pack["indicators"] = inds
    if sthan_meaning: pack["sthan_meaning"] = sthan_meaning
    return pack
