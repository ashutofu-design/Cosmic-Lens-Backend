#!/usr/bin/env python3
"""
Ask Engine — strict rule-based astrology question analysis.
Covers: marriage (7-step BPHS logic), with general fallback.
"""

import swisseph as swe
from datetime import datetime

# ── Astrology constants ────────────────────────────────────────────────────────

SIGN_LORDS = [
    "Mars","Venus","Mercury","Moon","Sun","Mercury",
    "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"
]

EXALT_SIGN = {
    "Sun":0,"Moon":1,"Mars":9,"Mercury":5,
    "Jupiter":3,"Venus":11,"Saturn":6
}
DEBIL_SIGN = {
    "Sun":6,"Moon":7,"Mars":3,"Mercury":11,
    "Jupiter":9,"Venus":5,"Saturn":0
}
OWN_SIGNS = {
    "Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
    "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10],
    "Rahu":[],"Ketu":[]
}

MALEFICS = {"Sun","Mars","Saturn","Rahu","Ketu"}

# Extra aspects beyond universal 7th aspect (houses counted from planet)
EXTRA_ASPECTS = {
    "Mars":    [4, 8],
    "Jupiter": [5, 9],
    "Saturn":  [3, 10],
}

# ── Marriage keywords ─────────────────────────────────────────────────────────

MARRIAGE_KWS = [
    "marriage","marr","vivah","shaadi","shadi","wedding","wife","husband",
    "spouse","love marriage","arrange","arranged","rishta","partner",
    "relationship","pyaar","pyar","muhurat","engagement","mangni",
    "shaadi","dulha","dulhan","soulmate","life partner",
    # Hindi/Devanagari
    "शादी","विवाह","पत्नी","पति","सगाई","ब्याह","दुल्हा","दुल्हन",
    # Tamil
    "திருமணம்","கல்யாணம்",
    # Telugu
    "పెళ్ళి","వివాహం",
    # Bengali
    "বিয়ে","বিবাহ",
    # Marathi
    "लग्न","विवाह",
    # Gujarati
    "લગ્ન","વિવાહ",
]

# ── Planet names per language ─────────────────────────────────────────────────

PLANET_NAMES_L = {
    "hi": {"Sun":"सूर्य","Moon":"चंद्र","Mars":"मंगल","Mercury":"बुध",
           "Jupiter":"गुरु","Venus":"शुक्र","Saturn":"शनि","Rahu":"राहु","Ketu":"केतु"},
    "ta": {"Sun":"சூரியன்","Moon":"சந்திரன்","Mars":"செவ்வாய்","Mercury":"புதன்",
           "Jupiter":"குரு","Venus":"சுக்கிரன்","Saturn":"சனி","Rahu":"ராகு","Ketu":"கேது"},
    "te": {"Sun":"సూర్యుడు","Moon":"చంద్రుడు","Mars":"కుజుడు","Mercury":"బుధుడు",
           "Jupiter":"గురువు","Venus":"శుక్రుడు","Saturn":"శని","Rahu":"రాహువు","Ketu":"కేతువు"},
    "bn": {"Sun":"সূর্য","Moon":"চন্দ্র","Mars":"মঙ্গল","Mercury":"বুধ",
           "Jupiter":"গুরু","Venus":"শুক্র","Saturn":"শনি","Rahu":"রাহু","Ketu":"কেতু"},
    "mr": {"Sun":"सूर्य","Moon":"चंद्र","Mars":"मंगळ","Mercury":"बुध",
           "Jupiter":"गुरू","Venus":"शुक्र","Saturn":"शनि","Rahu":"राहू","Ketu":"केतू"},
    "gu": {"Sun":"સૂર્ય","Moon":"ચંદ્ર","Mars":"મંગળ","Mercury":"બુધ",
           "Jupiter":"ગુરુ","Venus":"શુક્ર","Saturn":"શનિ","Rahu":"રાહુ","Ketu":"કેતુ"},
    "en": {"Sun":"Sun","Moon":"Moon","Mars":"Mars","Mercury":"Mercury",
           "Jupiter":"Jupiter","Venus":"Venus","Saturn":"Saturn","Rahu":"Rahu","Ketu":"Ketu"},
}

def pn(lang, name):
    """Localized planet name."""
    return PLANET_NAMES_L.get(lang, PLANET_NAMES_L["en"]).get(name, name)

# ── Helpers ───────────────────────────────────────────────────────────────────

_TOPIC_KEYWORDS = {
    "marriage": MARRIAGE_KWS,
    "career": ["career","job","work","promotion","business","naukri","kaam","कैरियर","नौकरी","व्यवसाय",
               "profession","employment","interview","resign","startup","entrepreneur",
               "வேலை","ఉద్యోగం","চাকরি","नोकरी","નોકરી"],
    "finance": ["money","wealth","finance","financial","richness","loan","debt","emi","invest",
                "stock","crypto","property","real estate","gold","savings","income","salary",
                "paisa","dhan","धन","पैसा","कर्ज","ऋण","निवेश","পয়সা","পৈসা","പണം","ਪੈਸਾ"],
    "health": ["health","disease","illness","sick","medical","operation","surgery","hospital",
               "doctor","fever","pain","cancer","diabetes","heart","mental","depression","anxiety",
               "rog","bimari","रोग","बीमारी","स्वास्थ्य","ஆரோக்கியம்","ఆరోగ్యం","স্বাস্থ্য"],
    "education": ["education","study","studies","exam","admission","college","university","school",
                  "phd","degree","scholarship","abroad study","padhai","पढ़ाई","शिक्षा","परीक्षा",
                  "படிப்பு","విద్య","পড়াশোনা","અભ્યાસ","अभ्यास"],
    "children": ["child","children","baby","santaan","pregnancy","conceive","fertility","ivf","son","daughter",
                 "putra","putri","santan","संतान","गर्भधारण","बच्चा","गर्भ","बेटा","बेटी",
                 "குழந்தை","సంతానం","সন্তান","બાળક"],
    "family": ["family","parents","mother","father","brother","sister","relative","in-laws",
               "parivaar","mata","pita","माता","पिता","भाई","बहन","परिवार","குடும்பம்","కుటుంబం","পরিবার"],
    "spiritual": ["spiritual","spirituality","god","mantra","meditation","puja","temple","guru",
                  "moksha","liberation","aatma","dharma","bhakti","अध्यात्म","भक्ति","मोक्ष","साधना",
                  "ஆன்மீகம்","ఆధ్యాత్మికం","আধ্যাত্মিক"],
    "travel": ["travel","abroad","foreign","visa","immigration","relocate","relocation","journey",
               "vilayat","videsh","विदेश","यात्रा","प्रवास","বিদেশ","விதேசம்"],
    "legal": ["legal","court","case","lawsuit","litigation","police","jail","prison","arrest","fir",
              "kanoon","mukadama","कानून","मुकदमा","कोर्ट","केस","போலீஸ்","కేస్","মামলা"],
    "remedies": ["remedy","remedies","upay","upaya","mantra","gemstone","ratna","yantra","pooja","puja",
                 "donation","daan","fast","vrat","उपाय","रत्न","दान","व्रत","மந்திரம்","రత్నం"],
    "timing": ["when will","timing","muhurat","auspicious time","kab","कब","अच्छा समय","muhurta",
               "good time","right time","best time","date","day","year","month","period"],
}


def detect_topics(question: str) -> list[str]:
    """Returns list of topics (multi-label). Empty list if no match → 'general'."""
    q = question.lower()
    topics = [t for t, kws in _TOPIC_KEYWORDS.items() if any(kw in q for kw in kws)]
    return topics


def detect_topic(question: str) -> str:
    """Backwards-compat: returns primary topic (first match) or 'general'."""
    topics = detect_topics(question)
    return topics[0] if topics else "general"


def find_planet(planets, name):
    return next((p for p in planets if p["name"] == name), None)


def planet_aspects_house(planet_house: int, target_house: int, planet_name: str) -> bool:
    """True if planet_name sitting in planet_house aspects target_house (Vedic graha drishti)."""
    aspects = [7] + EXTRA_ASPECTS.get(planet_name, [])
    for a in aspects:
        if (planet_house - 1 + a) % 12 + 1 == target_house:
            return True
    return False


def dignity_score(planet_name: str, longitude: float):
    sign_idx = int(longitude / 30) % 12
    if EXALT_SIGN.get(planet_name) == sign_idx:
        return 3, "exalted"
    if DEBIL_SIGN.get(planet_name) == sign_idx:
        return -3, "debilitated"
    if sign_idx in OWN_SIGNS.get(planet_name, []):
        return 2, "own sign"
    return 0, "neutral"


def house_strength_score(house: int):
    if house in [1, 4, 7, 10]:
        return 2
    if house in [5, 9]:
        return 2
    if house in [6, 8, 12]:
        return -2
    return 0


def navamsa_sign(longitude: float) -> int:
    """D9 Navamsa sign index (0=Aries … 11=Pisces)."""
    sign_idx = int(longitude / 30) % 12
    deg_in_sign = longitude % 30
    navamsa_num = int(deg_in_sign / (30.0 / 9))
    return (sign_idx * 9 + navamsa_num) % 12


# ── Ashtakavarga 7th house SAV ────────────────────────────────────────────────

BAV_TABLE = {
    "Sun":     [[1,2,4,7,8,9,10,11],[3,6,10,11],[1,2,4,7,8,9,10,11],[3,5,6,9,10,11,12],
                [5,6,9,11],[6,7,12],[1,2,4,7,8,9,10,11],[3,4,6,10,11,12]],
    "Moon":    [[3,6,7,8,10,11],[1,3,6,7,10,11],[2,3,5,6,9,10,11],[1,3,4,5,7,8,10,11,12],
                [1,4,7,8,10,11],[3,4,5,7,9,10,11],[3,5,6,11],[3,6,10,11]],
    "Mars":    [[3,5,6,10,11],[3,6,11],[1,2,4,7,8,10,11],[3,5,6,11],
                [6,10,11,12],[6,8,11,12],[1,4,7,8,9,10,11],[1,3,6,10,11]],
    "Mercury": [[5,6,9,11,12],[2,4,6,8,10,11],[1,2,4,7,8,9,10,11],[1,3,5,6,9,10,11,12],
                [6,8,11,12],[1,2,3,4,5,8,9,11],[1,2,4,7,8,9,10,11],[1,2,4,6,8,10,11]],
    "Jupiter": [[1,2,3,4,7,8,9,10,11],[2,5,7,9,11],[1,2,4,7,8,10,11],[1,2,4,5,6,9,10,11],
                [1,2,3,4,7,8,10,11],[2,5,6,9,10,11],[3,5,6,12],[1,2,4,5,6,7,9,10,11]],
    "Venus":   [[8,11,12],[1,2,3,4,5,8,9,11,12],[3,5,6,9,11,12],[3,5,6,9,11],
                [5,8,9,10,11],[1,2,3,4,5,8,9,10,11],[3,4,5,8,9,10,11],[1,2,3,4,5,8,9,11]],
    "Saturn":  [[1,2,4,7,8,10,11],[3,6,11],[3,5,6,10,11,12],[6,8,9,10,11,12],
                [5,6,11,12],[6,11,12],[3,5,6,11],[1,3,4,6,10,11]],
}
_BAV_PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]

def calc_7th_sav(planets, lagna_rashi: int) -> int:
    target = (lagna_rashi + 6) % 12
    src = []
    for pname in _BAV_PLANETS:
        p = find_planet(planets, pname)
        src.append(int(p["longitude"] / 30) % 12 if p else 0)
    src.append(lagna_rashi)   # 8th contributor = Lagna

    total = 0
    for pi, pname in enumerate(_BAV_PLANETS):
        for c in range(8):
            rel = ((target - src[c] + 12) % 12) + 1
            if rel in BAV_TABLE[pname][c]:
                total += 1
    return total


# ── Live transits ─────────────────────────────────────────────────────────────

def get_transits():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    now = datetime.utcnow()
    jd  = swe.julday(now.year, now.month, now.day,
                     now.hour + now.minute / 60.0 + now.second / 3600.0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    out = {}
    for name, pid in [("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN), ("Mars", swe.MARS)]:
        try:
            res, _ = swe.calc_ut(jd, pid, flags)
            lon = res[0] % 360
            out[name] = {"longitude": round(lon, 2), "sign": int(lon / 30) % 12}
        except Exception:
            out[name] = {"longitude": 0.0, "sign": 0}
    return out


# ── Marriage analysis (7-step BPHS) ──────────────────────────────────────────

def analyze_marriage(kundli: dict) -> dict:
    planets     = kundli.get("planets", [])
    asc_deg     = kundli.get("ascendantDeg", 0)
    lagna_rashi = int(asc_deg / 30) % 12
    dashas      = kundli.get("dashas", [])

    # STEP 1 — Marriage Promise ────────────────────────────────────────────────
    seventh_rashi    = (lagna_rashi + 6) % 12
    seventh_lord_nm  = SIGN_LORDS[seventh_rashi]
    seventh_lord_pl  = find_planet(planets, seventh_lord_nm)
    seventh_lord_h   = seventh_lord_pl["house"] if seventh_lord_pl else 7

    planets_in_7th   = [p for p in planets if p["house"] == 7]

    venus   = find_planet(planets, "Venus")
    jupiter = find_planet(planets, "Jupiter")

    afflictions  = []
    delay_factors = []

    for p in planets_in_7th:
        if p["name"] in MALEFICS:
            afflictions.append(p["name"])
            if p["name"] in ("Saturn", "Rahu"):
                delay_factors.append(f"{p['name']} sits in 7th house")

    for p in planets:
        if p["name"] in MALEFICS and p["name"] != seventh_lord_nm:
            if planet_aspects_house(p["house"], seventh_lord_h, p["name"]):
                afflictions.append(f"{p['name']} aspects {seventh_lord_nm}")
                if p["name"] == "Saturn":
                    delay_factors.append(f"Saturn aspects 7th lord {seventh_lord_nm}")

    # STEP 2 — Planet Strength Score ──────────────────────────────────────────
    second_lord_nm  = SIGN_LORDS[(lagna_rashi + 1) % 12]
    eleventh_lord_nm = SIGN_LORDS[(lagna_rashi + 10) % 12]
    key_pnames = list(dict.fromkeys(
        [seventh_lord_nm, "Venus", "Jupiter", second_lord_nm, eleventh_lord_nm]
    ))

    total_score = 0
    for pname in key_pnames:
        p = find_planet(planets, pname)
        if not p:
            continue
        ds, _ = dignity_score(pname, p["longitude"])
        hs     = house_strength_score(p["house"])
        retro  = -1 if p.get("retrograde") else 0
        total_score += ds + hs + retro

    max_score     = len(key_pnames) * 5
    strength_pct  = max(0, min(100, int((total_score / max(max_score, 1) + 1) * 50)))

    # STEP 3 — Dasha Analysis ─────────────────────────────────────────────────
    trigger_set = set([seventh_lord_nm, "Venus", "Jupiter",
                       second_lord_nm, eleventh_lord_nm])
    for p in planets_in_7th:
        trigger_set.add(p["name"])

    now_str = datetime.utcnow().strftime("%Y-%m-%d")

    def iso(d):
        return d[:10] if isinstance(d, str) else str(d)[:10]

    current_md = current_ad = current_pd = None
    for md in dashas:
        if iso(md["startDate"]) <= now_str < iso(md["endDate"]):
            current_md = md
            for ad in md.get("subDashas", []):
                if iso(ad["startDate"]) <= now_str < iso(ad["endDate"]):
                    current_ad = ad
                    for pd in ad.get("subDashas", []):
                        if iso(pd["startDate"]) <= now_str < iso(pd["endDate"]):
                            current_pd = pd
                            break
                    break
            break

    dasha_trigger = False
    dasha_label   = "N/A"
    if current_md and current_ad:
        md_p = current_md["planet"]
        ad_p = current_ad["planet"]
        pd_p = current_pd["planet"] if current_pd else None
        dasha_label = f"{md_p}-{ad_p}" + (f"-{pd_p}" if pd_p else "")
        if md_p in trigger_set or ad_p in trigger_set:
            dasha_trigger = True

    # Upcoming windows (next 3 years)
    future_cut = str(datetime.utcnow().year + 3) + "-12-31"
    upcoming = []
    for md in dashas:
        if iso(md["endDate"]) < now_str or iso(md["startDate"]) > future_cut:
            continue
        for ad in md.get("subDashas", []):
            ad_s, ad_e = iso(ad["startDate"]), iso(ad["endDate"])
            if ad_e < now_str or ad_s > future_cut:
                continue
            if md["planet"] in trigger_set and ad["planet"] in trigger_set:
                upcoming.append({
                    "md": md["planet"], "ad": ad["planet"],
                    "start": ad_s[:7], "end": ad_e[:7],
                })

    # STEP 4 — Transit Trigger ────────────────────────────────────────────────
    transits = get_transits()
    jup_h = (transits["Jupiter"]["sign"] - lagna_rashi + 12) % 12 + 1
    sat_h = (transits["Saturn"]["sign"]  - lagna_rashi + 12) % 12 + 1

    jup_activates = jup_h == 7 or planet_aspects_house(jup_h, 7, "Jupiter") \
                    or planet_aspects_house(jup_h, seventh_lord_h, "Jupiter")
    sat_activates = sat_h == 7 or planet_aspects_house(sat_h, 7, "Saturn") \
                    or planet_aspects_house(sat_h, seventh_lord_h, "Saturn")
    double_transit = jup_activates and sat_activates

    # STEP 5 — Ashtakavarga ───────────────────────────────────────────────────
    sav_7th    = calc_7th_sav(planets, lagna_rashi)
    bav_strong = sav_7th >= 28

    # STEP 6 — Navamsa (D9) ───────────────────────────────────────────────────
    d9_lagna = navamsa_sign(asc_deg)
    d9_strong = False
    if seventh_lord_pl:
        d9_7L_sign  = navamsa_sign(seventh_lord_pl["longitude"])
        d9_7L_house = (d9_7L_sign - d9_lagna + 12) % 12 + 1
        d9_strong   = d9_7L_house in [1, 2, 4, 5, 7, 9, 10, 11]

    # STEP 7 — Final Assessment ───────────────────────────────────────────────
    supports = int(dasha_trigger) + int(jup_activates) + int(sat_activates) \
               + int(bav_strong) + int(d9_strong)

    confidence = "High" if supports >= 4 else ("Medium" if supports >= 2 else "Low")

    # Build timing string
    if dasha_trigger and double_transit and current_ad:
        timing = f"NOW ({dasha_label} + double transit active)"
    elif upcoming:
        w = upcoming[0]
        timing = f"{w['start']} – {w['end']} ({w['md']}-{w['ad']} dasha)"
    else:
        timing = "No strong window in next 3 years — patience required"

    return {
        "seventh_lord":      seventh_lord_nm,
        "seventh_lord_h":    seventh_lord_h,
        "planets_in_7th":    [p["name"] for p in planets_in_7th],
        "afflictions":       afflictions,
        "delay_factors":     delay_factors,
        "strength_pct":      strength_pct,
        "dasha_trigger":     dasha_trigger,
        "dasha_label":       dasha_label,
        "jup_h":             jup_h,
        "sat_h":             sat_h,
        "jup_activates":     jup_activates,
        "sat_activates":     sat_activates,
        "double_transit":    double_transit,
        "sav_7th":           sav_7th,
        "bav_strong":        bav_strong,
        "d9_strong":         d9_strong,
        "confidence":        confidence,
        "timing":            timing,
        "supports":          supports,
        "current_dasha":     dasha_label,
        "upcoming":          upcoming,
    }


# ── Response formatter ────────────────────────────────────────────────────────

MONTH_ABB = {
    "01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
    "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"
}

def _fmt_ym(ym):
    try:
        y, m = ym.split("-")
        return f"{MONTH_ABB.get(m, m)} {y}"
    except Exception:
        return ym


def format_marriage_response(result: dict, lang: str) -> str:
    conf    = result["confidence"]
    sl      = result["seventh_lord"]
    sl_h    = result["seventh_lord_h"]
    dasha   = result["dasha_label"]
    delay   = result["delay_factors"]
    sav     = result["sav_7th"]
    jh      = result["jup_h"]
    sh      = result["sat_h"]
    timing  = result["timing"]
    d_trig  = result["dasha_trigger"]
    dt      = result["double_transit"]

    delay_str = delay[0] if delay else None

    # ── Hindi / Hinglish ──────────────────────────────────────────────────────
    if lang == "hi":
        sun = pn("hi", sl)
        if conf == "High":
            lines = [
                f"आपकी कुंडली में विवाह के बहुत strong संकेत हैं ✨",
                f"7th lord {sun} H{sl_h} में well-placed है और dasha {dasha} activate है।",
                f"{'Double transit active — Jupiter H'+str(jh)+' + Saturn H'+str(sh)+' दोनों 7th axis को trigger कर रहे हैं।' if dt else 'Jupiter H'+str(jh)+', Saturn H'+str(sh)+' में transit कर रहे हैं।'}",
                f"Ashtakavarga 7th house SAV = {sav} — {'strong support ✅' if sav >= 28 else 'average ⚠️'}।",
                f"Timing: {timing} — विवाह की probability बहुत high है।",
            ]
        elif conf == "Medium":
            lines = [
                f"विवाह के योग हैं, पर अभी पूरी तरह activate नहीं हुए।",
                f"7th lord {sun} H{sl_h} में है।{' ' + delay_str + ' की वजह से delay संभव।' if delay_str else ''}",
                f"Current dasha {dasha} — {'trigger planet है ✅' if d_trig else 'direct marriage trigger नहीं है।'}",
                f"7th house SAV = {sav} {'✅' if sav >= 28 else '⚠️'} | Jupiter H{jh}, Saturn H{sh}।",
                f"अगली strong window: {timing}",
            ]
        else:
            lines = [
                f"अभी विवाह के लिए conditions पूरी तरह ready नहीं हैं।",
                f"कारण: {delay_str if delay_str else 'Dasha और transit का पर्याप्त support नहीं।'}",
                f"Dasha {dasha} — marriage trigger नहीं है। 7th house SAV = {sav}।",
                f"{'Double transit नहीं है — Jupiter H'+str(jh)+', Saturn H'+str(sh)+'।' if not dt else ''}",
                f"Patience रखें — {timing}।",
            ]

    # ── Marathi ───────────────────────────────────────────────────────────────
    elif lang == "mr":
        sun = pn("mr", sl)
        if conf == "High":
            lines = [
                f"तुमच्या कुंडलीत विवाहाचे अतिशय strong संकेत आहेत ✨",
                f"सप्तम स्थानाधिपती {sun} H{sl_h} मध्ये आहे आणि दशा {dasha} active आहे।",
                f"{'दुहेरी गोचर active — गुरू H'+str(jh)+' + शनि H'+str(sh)+'।' if dt else 'गुरू H'+str(jh)+', शनि H'+str(sh)+' मध्ये आहेत।'}",
                f"अष्टकवर्ग सप्तम SAV = {sav} — {'बळकट ✅' if sav >= 28 else 'सामान्य ⚠️'}।",
                f"वेळ: {timing}",
            ]
        elif conf == "Medium":
            lines = [
                f"विवाहाचे योग आहेत, पण अजून पूर्ण activate झालेले नाहीत।",
                f"सप्तमेश {sun} H{sl_h} मध्ये।{' ' + delay_str + ' मुळे विलंब शक्य।' if delay_str else ''}",
                f"सध्याची दशा {dasha} — {'trigger आहे ✅' if d_trig else 'direct trigger नाही।'}",
                f"SAV = {sav} | गुरू H{jh}, शनि H{sh}।",
                f"पुढील window: {timing}",
            ]
        else:
            lines = [
                f"सध्या विवाहासाठी conditions पूर्ण तयार नाहीत।",
                f"कारण: {delay_str if delay_str else 'दशा आणि गोचराचा पुरेसा आधार नाही।'}",
                f"दशा {dasha} — marriage trigger नाही। SAV = {sav}।",
                f"संयम ठेवा — {timing}।",
            ]

    # ── Bengali ───────────────────────────────────────────────────────────────
    elif lang == "bn":
        sun = pn("bn", sl)
        if conf == "High":
            lines = [
                f"আপনার কুণ্ডলীতে বিবাহের অত্যন্ত strong সংকেত আছে ✨",
                f"৭ম ভাবের স্বামী {sun} H{sl_h}-তে আছে, দশা {dasha} active।",
                f"{'দ্বৈত গোচর active — গুরু H'+str(jh)+' + শনি H'+str(sh)+'।' if dt else 'গুরু H'+str(jh)+', শনি H'+str(sh)+'-তে।'}",
                f"অষ্টকবর্গ SAV = {sav} — {'শক্তিশালী ✅' if sav >= 28 else 'গড় ⚠️'}।",
                f"সময়: {timing}",
            ]
        elif conf == "Medium":
            lines = [
                f"বিবাহের যোগ আছে কিন্তু এখনো পুরোপুরি activate হয়নি।",
                f"৭ম স্বামী {sun} H{sl_h}-তে।{' ' + delay_str + ' কারণে দেরি সম্ভব।' if delay_str else ''}",
                f"বর্তমান দশা {dasha} — {'trigger ✅' if d_trig else 'সরাসরি trigger নয়।'}",
                f"SAV = {sav} | গুরু H{jh}, শনি H{sh}।",
                f"পরবর্তী window: {timing}",
            ]
        else:
            lines = [
                f"এখন বিবাহের conditions প্রস্তুত নয়।",
                f"কারণ: {delay_str if delay_str else 'দশা ও গোচরের পর্যাপ্ত সমর্থন নেই।'}",
                f"দশা {dasha} — marriage trigger নয়। SAV = {sav}।",
                f"ধৈর্য রাখুন — {timing}।",
            ]

    # ── Gujarati ──────────────────────────────────────────────────────────────
    elif lang == "gu":
        sun = pn("gu", sl)
        if conf == "High":
            lines = [
                f"તમારી કુંડળીમાં લગ્નના ઘણા strong સંકેત છે ✨",
                f"7મા ભાવના સ્વામી {sun} H{sl_h}માં છે અને દશા {dasha} active છે।",
                f"{'ડબલ ટ્રાન્ઝિટ — ગુરુ H'+str(jh)+' + શનિ H'+str(sh)+'।' if dt else 'ગુરુ H'+str(jh)+', શનિ H'+str(sh)+'।'}",
                f"અષ્ટકવર્ગ SAV = {sav} — {'strong ✅' if sav >= 28 else 'સાધારણ ⚠️'}।",
                f"સમય: {timing}",
            ]
        elif conf == "Medium":
            lines = [
                f"લગ્નના યોગ છે, પણ હજુ fully activate નથી।",
                f"7મા સ્વામી {sun} H{sl_h}માં।{' ' + delay_str + ' ને કારણે વિલંબ.'  if delay_str else ''}",
                f"હાલની દશા {dasha} — {'trigger ✅' if d_trig else 'direct trigger નહી।'}",
                f"SAV = {sav} | ગુરુ H{jh}, શનિ H{sh}।",
                f"આગળની window: {timing}",
            ]
        else:
            lines = [
                f"અત્યારે લગ્ન માટે conditions ready નહી।",
                f"કારણ: {delay_str if delay_str else 'દશા-ગ્રહ-ટ્રાન્ઝિટ support નથી।'}",
                f"દશા {dasha} — marriage trigger નથી। SAV = {sav}।",
                f"ધૈર્ય રાખો — {timing}।",
            ]

    # ── Tamil ─────────────────────────────────────────────────────────────────
    elif lang == "ta":
        sun = pn("ta", sl)
        if conf == "High":
            lines = [
                f"உங்கள் ஜாதகத்தில் திருமணத்திற்கு மிகவும் வலிமையான அமைப்பு உள்ளது ✨",
                f"7ம் ஆதிபதி {sun} H{sl_h}ல் உள்ளார், தசை {dasha} active।",
                f"{'இரட்டை கோசாரம் — குரு H'+str(jh)+' + சனி H'+str(sh)+'।' if dt else 'குரு H'+str(jh)+', சனி H'+str(sh)+'।'}",
                f"அஷ்டகவர்க SAV = {sav} — {'வலிமை ✅' if sav >= 28 else 'சராசரி ⚠️'}।",
                f"நேரம்: {timing}",
            ]
        elif conf == "Medium":
            lines = [
                f"திருமண யோகம் உள்ளது, ஆனால் இன்னும் முழுமையாக activate ஆகவில்லை।",
                f"7ம் ஆதிபதி {sun} H{sl_h}ல்।{' ' + delay_str + ' காரணம் தாமதம் possible.' if delay_str else ''}",
                f"தசை {dasha} — {'trigger ✅' if d_trig else 'நேரடி trigger இல்லை।'}",
                f"SAV = {sav} | குரு H{jh}, சனி H{sh}।",
                f"அடுத்த window: {timing}",
            ]
        else:
            lines = [
                f"இப்போது திருமணத்திற்கு conditions சரியாக இல்லை।",
                f"காரணம்: {delay_str if delay_str else 'தசை மற்றும் கோசாரம் support இல்லை।'}",
                f"தசை {dasha} — marriage trigger இல்லை। SAV = {sav}।",
                f"பொறுமையாக இருங்கள் — {timing}।",
            ]

    # ── Telugu ────────────────────────────────────────────────────────────────
    elif lang == "te":
        sun = pn("te", sl)
        if conf == "High":
            lines = [
                f"మీ కుండలిలో వివాహానికి చాలా బలమైన సంకేతాలు ఉన్నాయి ✨",
                f"7వ అధిపతి {sun} H{sl_h}లో ఉన్నారు, దశ {dasha} active।",
                f"{'డబుల్ ట్రాన్సిట్ — గురువు H'+str(jh)+' + శని H'+str(sh)+'।' if dt else 'గురువు H'+str(jh)+', శని H'+str(sh)+'।'}",
                f"అష్టకవర్గ SAV = {sav} — {'బలంగా ✅' if sav >= 28 else 'సాధారణ ⚠️'}।",
                f"సమయం: {timing}",
            ]
        elif conf == "Medium":
            lines = [
                f"వివాహ యోగం ఉంది, కానీ ఇంకా fully activate కాలేదు।",
                f"7వ అధిపతి {sun} H{sl_h}లో।{' ' + delay_str + ' వల్ల ఆలస్యం possible.' if delay_str else ''}",
                f"దశ {dasha} — {'trigger ✅' if d_trig else 'direct trigger కాదు।'}",
                f"SAV = {sav} | గురువు H{jh}, శని H{sh}।",
                f"తదుపరి window: {timing}",
            ]
        else:
            lines = [
                f"ప్రస్తుతం వివాహానికి conditions సిద్ధంగా లేవు।",
                f"కారణం: {delay_str if delay_str else 'దశ మరియు transit support లేదు।'}",
                f"దశ {dasha} — marriage trigger కాదు। SAV = {sav}।",
                f"ఓపికగా ఉండండి — {timing}।",
            ]

    # ── English (default) ─────────────────────────────────────────────────────
    else:
        if conf == "High":
            lines = [
                f"Strong marriage indicators in your chart! ✨",
                f"7th lord {sl} is in H{sl_h}, and dasha {dasha} is a marriage trigger.",
                f"{'Double transit active — Jupiter H'+str(jh)+' + Saturn H'+str(sh)+' both triggering 7th axis.' if dt else 'Jupiter H'+str(jh)+', Saturn H'+str(sh)+' in transit.'}",
                f"Ashtakavarga 7th house SAV = {sav} — {'strong support ✅' if sav >= 28 else 'average ⚠️'}.",
                f"Timing: {timing} — high probability for marriage.",
            ]
        elif conf == "Medium":
            lines = [
                f"Marriage promise exists but not fully activated yet.",
                f"7th lord {sl} in H{sl_h}.{' ' + delay_str + ' — delay possible.' if delay_str else ''}",
                f"Dasha {dasha} — {'marriage trigger ✅' if d_trig else 'not a direct trigger.'}",
                f"SAV = {sav} {'✅' if sav >= 28 else '⚠️'} | Jupiter H{jh}, Saturn H{sh}.",
                f"Next window: {timing}",
            ]
        else:
            lines = [
                f"Marriage timing is not imminent — more alignment needed.",
                f"Challenge: {delay_str if delay_str else 'Dasha and transit lack sufficient marriage support.'}",
                f"Dasha {dasha} — not a marriage trigger. SAV = {sav}.",
                f"Stay patient — {timing}.",
            ]

    return "\n".join(lines)


# ── General replies (per language, rotating) ──────────────────────────────────

GENERAL_REPLIES = {
    "hi": [
        "आपकी कुंडली में वर्तमान दशा interesting phase में है। अपने लक्ष्य पर focused रहें — ग्रह आपके साथ हैं।",
        "शनि का अनुशासन और बृहस्पति का आशीर्वाद मिलकर इस समय को transformation का काल बना रहे हैं। प्रक्रिया पर भरोसा रखें।",
        "आपके ग्रहों की current position एक नई शुरुआत की ओर इशारा कर रही है। सही समय पर सही कदम उठाएं।",
    ],
    "ta": [
        "உங்கள் ஜாதகத்தில் தற்போதைய தசை ஒரு முக்கியமான கட்டத்தில் உள்ளது. இலக்கில் கவனம் வையுங்கள்.",
        "சனியின் ஒழுக்கமும் குருவின் ஆசீர்வாதமும் இந்த காலத்தை மாற்றத்தின் காலமாக மாற்றுகின்றன.",
        "உங்கள் கிரகங்களின் நிலை ஒரு புதிய தொடக்கத்தை சுட்டுகிறது. சரியான நேரத்தில் சரியான படி எடுங்கள்.",
    ],
    "te": [
        "మీ కుండలిలో ప్రస్తుత దశ ఒక ముఖ్యమైన దశలో ఉంది. మీ లక్ష్యంపై దృష్టి పెట్టండి.",
        "శని యొక్క క్రమశిక్షణ మరియు గురువు యొక్క ఆశీర్వాదం ఈ కాలాన్ని మార్పు కాలంగా చేస్తున్నాయి.",
        "మీ గ్రహాల స్థితి ఒక కొత్త ప్రారంభాన్ని సూచిస్తోంది. సరైన సమయంలో సరైన అడుగు వేయండి.",
    ],
    "bn": [
        "আপনার কুণ্ডলীতে বর্তমান দশা একটি গুরুত্বপূর্ণ পর্যায়ে আছে। লক্ষ্যে মনোযোগ রাখুন।",
        "শনির শৃঙ্খলা ও বৃহস্পতির আশীর্বাদ এই সময়কে রূপান্তরের কাল করে তুলছে।",
        "আপনার গ্রহের অবস্থান একটি নতুন সূচনার দিকে ইঙ্গিত করছে।",
    ],
    "mr": [
        "तुमच्या कुंडलीतील सध्याची दशा एका महत्त्वाच्या टप्प्यात आहे. ध्येयावर लक्ष केंद्रित करा।",
        "शनीची शिस्त आणि गुरूचे आशीर्वाद मिळून हा काळ परिवर्तनाचा काळ बनवत आहेत।",
        "तुमच्या ग्रहांची सध्याची स्थिती एका नव्या सुरुवातीकडे निर्देश करत आहे।",
    ],
    "gu": [
        "તમારી કુંડળીની વર્તમાન દશા એક મહત્વપૂર્ણ તબક્કામાં છે। ધ્યેય પર ધ્યાન આપો।",
        "શનિની શિસ્ત અને ગુરુના આશીર્વાદ આ સમયને પરિવર્તનનો કાળ બનાવી રહ્યા છે।",
        "તમારા ગ્રહોની સ્થિતિ એક નવી શરૂઆત તરફ ઈશારો કરી રહી છે।",
    ],
    "en": [
        "Based on your current dasha and planetary positions, this is a transformative period. Stay focused on your goals.",
        "Your chart shows strong indicators for the coming months. Trust the process and be patient.",
        "The current planetary alignment suggests a period of growth and self-reflection. Act with intention.",
    ],
}


# ── Main entry point ──────────────────────────────────────────────────────────

def process_ask(question: str, kundli: dict | None, lang: str, reply_idx: int = 0) -> dict:
    """
    Returns {"text": str, "topic": str, "confidence": str | None}
    """
    topic = detect_topic(question)

    if topic == "marriage" and kundli:
        try:
            result   = analyze_marriage(kundli)
            text     = format_marriage_response(result, lang)
            return {
                "text":       text,
                "topic":      "marriage",
                "confidence": result["confidence"],
            }
        except Exception:
            import traceback
            traceback.print_exc()

    # General fallback
    replies = GENERAL_REPLIES.get(lang) or GENERAL_REPLIES["en"]
    return {
        "text":       replies[reply_idx % len(replies)],
        "topic":      "general",
        "confidence": None,
    }
