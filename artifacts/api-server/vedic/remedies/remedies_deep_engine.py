"""
Sprint 49 / Phase V — REMEDIES DEEP ENGINE
Comprehensive per-chart remedy aggregator with severity, cost, effort tiers.

12 sections (V1-V12):
  V1  Per-planet 9-graha remedies (gem/mantra/donation/day/color/yantra/fast)
  V2  Per-dosha remedies (Manglik/KalSarpa/SadeSati/Pitru/Grahan/Guru-Chandal/Angarak)
  V3  Per-yoga remedies (triggered by STRONG yogas from medical/financial engines)
  V4  House-affliction remedies (6/8/12 occupants)
  V5  Lal Kitab specific remedies
  V6  Modern reframe remedies (lifestyle/psychology)
  V7  Effort tier (LOW/MED/HIGH) summary
  V8  Cost tier (FREE/AFFORDABLE/EXPENSIVE) summary
  V9  Top-7 priority remedies for THIS chart
  V10 Daily routine card (morning/noon/evening)
  V11 Weekly day-wise card (Sun-Sat)
  V12 Mandatory disclaimer

ETHICS rules:
  • Remedies SUPPLEMENT real-world action — never substitute
  • No "must do or you will suffer" language
  • Always include FREE alternatives alongside paid (gems, yantras)
  • Modern reframe alongside traditional
"""
from __future__ import annotations
from typing import Any

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = {0:"Mars",1:"Venus",2:"Mercury",3:"Moon",4:"Sun",5:"Mercury",
              6:"Venus",7:"Mars",8:"Jupiter",9:"Saturn",10:"Saturn",11:"Jupiter"}
MALEFICS = {"Saturn","Mars","Sun","Rahu","Ketu"}

DISCLAIMER = (
    "  ⚠  REMEDY DISCLAIMER  ⚠\n"
    "    Remedies SUPPLEMENT your real-world effort — they NEVER substitute it.\n"
    "    Astrology shows tendencies; karma/action shapes outcome.\n"
    "    All paid remedies (gems, expensive yantras) have FREE alternatives.\n"
    "    Tiers — Effort: 🟢 LOW / 🟡 MED / 🔴 HIGH  •  Cost: 💰 FREE / 💰💰 AFFORDABLE / 💰💰💰 EXPENSIVE"
)

# ─── V1: 9-Graha master remedy table ────────────────────────────────────────
GRAHA_REMEDIES = {
    "Sun": {
        "gem": "Ruby (Manik) — 3 to 5 carat, copper ring, right ring finger, Sunday sunrise",
        "mantra": "Om Hraam Hreem Hraum Sah Suryaya Namah — 7,000 times in 40 days",
        "donation": "Wheat, jaggery, copper, red cloth — to a needy father-figure on Sunday",
        "day": "Sunday",
        "color": "Red, orange, gold",
        "yantra": "Surya Yantra — install north-east wall, daily incense",
        "fast": "Sunday fast (one meal, no salt)",
        "modern": "Morning sunlight 15 min, leadership journaling, vitamin-D check",
        "free_alt": "Sun salutation (Surya Namaskar) 12 rounds at sunrise — FREE & most powerful",
    },
    "Moon": {
        "gem": "Pearl (Moti) — 3 to 6 carat, silver ring, little finger, Monday sunrise",
        "mantra": "Om Shraam Shreem Shraum Sah Chandraya Namah — 11,000 in 40 days",
        "donation": "Rice, milk, white cloth, silver, sugar — to a mother-figure on Monday",
        "day": "Monday",
        "color": "White, silver, cream",
        "yantra": "Chandra Yantra — north-west, daily milk offering",
        "fast": "Monday fast (fruits + milk only)",
        "modern": "Sleep 7-8 hrs, meditation app, journal emotions, talk to mother weekly",
        "free_alt": "Moon-water (overnight glass under moon, sip morning) — FREE",
    },
    "Mars": {
        "gem": "Red Coral (Moonga) — 5 to 7 carat, copper/gold ring, ring finger, Tuesday",
        "mantra": "Om Kraam Kreem Kraum Sah Bhaumaya Namah — 10,000 in 40 days",
        "donation": "Red lentils (masoor), jaggery, copper, weapons-tools — Tuesday",
        "day": "Tuesday",
        "color": "Red, maroon",
        "yantra": "Mangal Yantra — south wall",
        "fast": "Tuesday fast (one meal)",
        "modern": "Cold shower, HIIT/martial arts 3x/week, anger-management therapy",
        "free_alt": "Hanuman Chalisa daily 1 round — covers Mars 100% — FREE",
    },
    "Mercury": {
        "gem": "Emerald (Panna) — 4 to 6 carat, gold ring, little finger, Wednesday",
        "mantra": "Om Braam Breem Braum Sah Budhaya Namah — 9,000 in 40 days",
        "donation": "Green moong, green cloth, books, pens — to a student/teacher Wednesday",
        "day": "Wednesday",
        "color": "Green",
        "yantra": "Budh Yantra — north wall",
        "fast": "Wednesday fast (green vegetables only)",
        "modern": "Daily journaling, language-learning app, public-speaking practice",
        "free_alt": "Vishnu Sahasranama OR Bhagavad-Gita 1 chapter daily — FREE",
    },
    "Jupiter": {
        "gem": "Yellow Sapphire (Pukhraj) — 4 to 7 carat, gold ring, index finger, Thursday",
        "mantra": "Om Graam Greem Graum Sah Gurave Namah — 19,000 in 40 days",
        "donation": "Yellow gram (chana dal), turmeric, gold, books — to a teacher/priest Thursday",
        "day": "Thursday",
        "color": "Yellow",
        "yantra": "Guru Yantra — north-east",
        "fast": "Thursday fast (banana + yellow food)",
        "modern": "Read 1 wisdom book/month, online course/quarter, mentor someone",
        "free_alt": "Sri Vishnu Sahasranama OR Guru Stotra daily — FREE",
    },
    "Venus": {
        "gem": "Diamond (Heera) OR Opal — 0.5 to 1 carat, platinum/silver, middle finger, Friday",
        "mantra": "Om Draam Dreem Draum Sah Shukraya Namah — 16,000 in 40 days",
        "donation": "White sweets, white cloth, silver, perfume — to a young woman Friday",
        "day": "Friday",
        "color": "White, pink, light blue",
        "yantra": "Shukra Yantra — south-east",
        "fast": "Friday fast (white food)",
        "modern": "Art/music practice, healthy relationships, self-care routine, beauty habits",
        "free_alt": "Sri Sukta OR Lakshmi Ashtottara daily — FREE",
    },
    "Saturn": {
        "gem": "Blue Sapphire (Neelam) — 5 to 7 carat, silver/iron ring, middle finger, Saturday — TEST 3 days first!",
        "mantra": "Om Praam Preem Praum Sah Shanaischaraya Namah — 23,000 in 40 days",
        "donation": "Black lentils (urad), iron, mustard oil, black cloth, blanket — to elderly/poor Saturday",
        "day": "Saturday",
        "color": "Black, dark blue",
        "yantra": "Shani Yantra — west wall",
        "fast": "Saturday fast (one meal, no salt)",
        "modern": "Disciplined routine, marathon training, anti-aging habits, serve elderly",
        "free_alt": "Hanuman Chalisa 1 round daily — neutralizes Saturn — FREE & SAFEST",
    },
    "Rahu": {
        "gem": "Hessonite (Gomed) — 6 to 9 carat, silver ring, middle finger, Saturday",
        "mantra": "Om Bhraam Bhreem Bhraum Sah Rahave Namah — 18,000 in 40 days",
        "donation": "Black sesame, blue cloth, blanket, electronics — Saturday",
        "day": "Saturday (also Wednesday)",
        "color": "Smokey grey, dark blue",
        "yantra": "Rahu Yantra — south-west",
        "fast": "Saturday fast",
        "modern": "Limit social media, digital detox 1 day/week, foreign-language learning",
        "free_alt": "Durga Chalisa OR Bhairav mantra daily — FREE",
    },
    "Ketu": {
        "gem": "Cat's Eye (Lehsunia) — 4 to 7 carat, silver ring, middle finger, Tuesday/Saturday",
        "mantra": "Om Sraam Sreem Sraum Sah Ketave Namah — 17,000 in 40 days",
        "donation": "Multi-coloured cloth, blanket, sesame oil — to a sadhu/mendicant",
        "day": "Tuesday",
        "color": "Multi-colour, smoky",
        "yantra": "Ketu Yantra — south-west",
        "fast": "Tuesday or Saturday fast",
        "modern": "Meditation 20 min/day, declutter monthly, silent retreat 1x/year",
        "free_alt": "Ganesha mantra OR Vipassana sit daily — FREE",
    },
}

# ─── V2: Per-dosha remedies ────────────────────────────────────────────────
DOSHA_REMEDIES = {
    "Manglik": [
        "Kumbh Vivah (with peepal/banana tree) before marriage",
        "Hanuman Chalisa daily — STRONGEST Manglik neutralizer",
        "Marry another Manglik OR after age 28 (Mars matures)",
        "Donate red lentils Tuesdays, fast on Tuesdays",
        "Modern: couples therapy + anger-management before marriage",
    ],
    "KalSarpa": [
        "Rahu+Ketu Shanti puja at Trimbakeshwar/Kalahasti (once)",
        "Sarp Sukta path 11 times daily for 40 days",
        "Donate black sesame & multi-coloured cloth on Saturday",
        "Feed snakes (visit serpent temple) on Naga Panchami",
        "Modern: face the deepest fear directly — KalSarpa breaks via courage",
    ],
    "SadeSati": [
        "Hanuman Chalisa daily 1 round — universal Saturn pacifier",
        "Donate to elderly, the disabled, or labourers Saturdays",
        "Wear iron ring on middle finger (no gem)",
        "Mustard-oil lamp under peepal tree Saturday evening",
        "Modern: build long-haul discipline NOW — Saturn rewards what looks like punishment",
    ],
    "PitruDosh": [
        "Pitra Paksha tarpan (Sept-Oct annually)",
        "Feed Brahmins/cows/crows on Amavasya (no-moon)",
        "Plant peepal/banyan tree, water it weekly",
        "Donate to old-age homes monthly",
        "Modern: reconcile with parents/ancestors emotionally; write letter, even if not delivered",
    ],
    "Grahan": [
        "Rahu/Ketu mantra 108 times daily",
        "Donate during eclipses (sesame, blanket, food)",
        "Avoid eclipse-time meals; chant during eclipse",
        "Modern: digital detox during eclipse; deep meditation",
    ],
    "Guru-Chandal": [
        "Brihaspati mantra 108 daily",
        "Yellow gram + turmeric donation Thursdays",
        "Avoid taking advice from manipulators",
        "Modern: vet your gurus carefully; trust verified mentors only",
    ],
    "Angarak": [
        "Hanuman Chalisa + Mars mantra daily",
        "Avoid driving on Tuesdays, no risky decisions",
        "Donate red lentils + jaggery Tuesday",
        "Modern: HIIT/martial arts to channel aggression productively",
    ],
}

# ─── V5: Lal Kitab signature remedies (free, action-based) ────────────────
LAL_KITAB_FREE = {
    "Sun":     "Offer water to Sun at sunrise (copper vessel + red flower)",
    "Moon":    "Drink water from a silver glass; never refuse milk to anyone",
    "Mars":    "Throw red lentils into running water on Tuesday",
    "Mercury": "Feed parrots green chilies; never break a friend's trust",
    "Jupiter": "Apply turmeric/saffron tilak; never disrespect elders",
    "Venus":   "Donate cow-fodder Friday; respect women in family",
    "Saturn":  "Pour mustard oil at threshold Saturday; serve labourers food",
    "Rahu":    "Throw 400gm raw coal/coconut in running water on Saturday",
    "Ketu":    "Keep silver chain on right ankle; feed dogs",
}

# ─── V6: Modern lifestyle remedies (psychology + neuroscience) ────────────
MODERN_REMEDIES = {
    "Sun":     "Morning sunlight 15min, leadership coaching, take ownership in 1 area daily",
    "Moon":    "Sleep hygiene (10pm-6am), meditation app, EFT/tapping for emotions",
    "Mars":    "Cold shower 2min/day, MMA/HIIT 3x/week, anger-journal before reacting",
    "Mercury": "Daily journaling 10min, language app, public-speaking (Toastmasters)",
    "Jupiter": "1 wisdom book/month, online course/quarter, mentor 1 person",
    "Venus":   "Art/music practice 30min/week, gratitude journal, self-care Sunday",
    "Saturn":  "Disciplined routine, marathon training, anti-aging diet, serve elders weekly",
    "Rahu":    "Digital detox 1 day/week, foreign-language learning, controlled risk-taking",
    "Ketu":    "20min meditation, monthly declutter, annual silent retreat",
}


def _planet_houses(planets: list, lagna_si: int) -> dict:
    out = {}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon,(int,float)): continue
        si = int(lon // 30) % 12
        h = ((si - lagna_si) % 12) + 1
        out[p["name"]] = {"si": si, "h": h, "sign": SIGNS[si]}
    return out


def run_remedies_engine(kundli: dict, doshas: list[str] | None = None,
                        weak_planets: list[str] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"available": True, "disclaimer": DISCLAIMER}
    planets = kundli.get("planets") or []
    lag = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    try: lagna_si = SIGNS.index(lag)
    except Exception: lagna_si = 0

    p_data = _planet_houses(planets, lagna_si)
    if not p_data:
        out["available"] = False; return out

    # Auto-detect "needy" planets if not supplied:
    #   - planets in 6/8/12 (afflicted) → need pacification
    #   - planets in own/exalted sign → already strong, optional boost
    afflicted = [p for p,d in p_data.items() if d["h"] in (6,8,12)]
    needy = list(set((weak_planets or []) + afflicted))
    if not needy:
        # boost the lagna lord by default
        lord = SIGN_LORDS[lagna_si]
        if lord in p_data: needy = [lord]

    # Auto-detect doshas from chart if not supplied
    if not doshas:
        doshas = []
        # Manglik: Mars in 1/4/7/8/12
        if p_data.get("Mars",{}).get("h") in (1,4,7,8,12):
            doshas.append("Manglik")
        # KalSarpa: all 7 planets between Rahu-Ketu axis (rough check)
        if "Rahu" in p_data and "Ketu" in p_data:
            r_si = p_data["Rahu"]["si"]; k_si = p_data["Ketu"]["si"]
            non_node_signs = [d["si"] for n,d in p_data.items() if n not in ("Rahu","Ketu")]
            if non_node_signs:
                # crude: all between Rahu→Ketu (forward arc) OR all between Ketu→Rahu
                arc1 = all((s - r_si) % 12 < (k_si - r_si) % 12 for s in non_node_signs)
                arc2 = all((s - k_si) % 12 < (r_si - k_si) % 12 for s in non_node_signs)
                if arc1 or arc2: doshas.append("KalSarpa")
        # Guru-Chandal: Jupiter conj Rahu/Ketu
        if p_data.get("Jupiter",{}).get("si") == p_data.get("Rahu",{}).get("si"): doshas.append("Guru-Chandal")
        if p_data.get("Jupiter",{}).get("si") == p_data.get("Ketu",{}).get("si"): doshas.append("Guru-Chandal")
        # Angarak: Mars conj Rahu
        if p_data.get("Mars",{}).get("si") == p_data.get("Rahu",{}).get("si"): doshas.append("Angarak")
        # Grahan: Sun/Moon conj Rahu/Ketu
        if p_data.get("Sun",{}).get("si") in (p_data.get("Rahu",{}).get("si"), p_data.get("Ketu",{}).get("si")):
            doshas.append("Grahan")
        if p_data.get("Moon",{}).get("si") in (p_data.get("Rahu",{}).get("si"), p_data.get("Ketu",{}).get("si")):
            doshas.append("Grahan")

    # ─── V1: per-planet remedy cards for "needy" planets ───────────────────
    v1 = []
    for p in needy:
        if p in GRAHA_REMEDIES:
            v1.append({"planet": p, **GRAHA_REMEDIES[p]})

    # ─── V2: per-dosha remedies ────────────────────────────────────────────
    v2 = []
    for d in set(doshas):
        if d in DOSHA_REMEDIES:
            v2.append({"dosha": d, "remedies": DOSHA_REMEDIES[d]})

    # ─── V3: per-yoga remedies (placeholder — future hook from medical/financial) ─
    v3 = []  # (future: scan medical_str/financial_str for STRONG yogas)

    # ─── V4: house-affliction remedies (6/8/12 occupants) ─────────────────
    v4 = []
    for h, label in [(6,"Enemies/Disease"), (8,"Crisis/Transformation"), (12,"Loss/Foreign/Moksha")]:
        occ = [n for n,d in p_data.items() if d["h"] == h]
        if occ:
            v4.append({"house": h, "label": label, "occupants": occ,
                       "free_remedy": " • ".join(LAL_KITAB_FREE.get(p,"—") for p in occ)})

    # ─── V5: Lal Kitab free remedies for needy planets ────────────────────
    v5 = [{"planet": p, "free_action": LAL_KITAB_FREE.get(p,"—")} for p in needy]

    # ─── V6: modern lifestyle remedies for needy planets ──────────────────
    v6 = [{"planet": p, "lifestyle": MODERN_REMEDIES.get(p,"—")} for p in needy]

    # ─── V7-V8: effort/cost summary ───────────────────────────────────────
    has_gem_advice = bool(needy)
    v7 = "🟢 LOW — daily 10-min mantra+sunlight (start here)" if not v2 else \
         ("🟡 MED — daily mantra + weekly fast + monthly donation" if len(v2) <= 1 else
          "🔴 HIGH — multi-dosha pattern; structured 40-day sadhana recommended")
    v8 = "💰 FREE alternatives sufficient for ALL planets (Hanuman Chalisa covers most)" if not has_gem_advice else \
         "💰💰 AFFORDABLE: mantras + donations are FREE; gems optional (₹3K-₹20K) AFTER 3-day test"

    # ─── V9: top-7 priority remedies for THIS chart ───────────────────────
    v9 = []
    # Always #1: Hanuman Chalisa (universal pacifier)
    v9.append("1. Hanuman Chalisa — 1 round daily (covers Mars+Saturn+general protection — FREE)")
    # Sun salutation
    v9.append("2. Surya Namaskar 12 rounds at sunrise (covers Sun + cardiovascular health — FREE)")
    # Most-needy planet mantra
    if needy:
        first = needy[0]
        gr = GRAHA_REMEDIES.get(first,{})
        if gr.get("free_alt"):
            v9.append(f"3. {first} pacifier: {gr['free_alt']}")
    # Top dosha
    if v2:
        d0 = v2[0]
        if d0["remedies"]:
            v9.append(f"4. {d0['dosha']} remedy: {d0['remedies'][0]}")
    # Modern lifestyle anchor
    v9.append("5. Daily 10-min meditation app (Insight Timer / Calm) — covers Moon+Ketu — FREE")
    # Donation routine
    v9.append("6. Weekly donation (Saturday): food/clothes to elderly or labourers — Saturn pacifier")
    # Journaling
    v9.append("7. Daily 10-min journaling — Mercury+Moon clarity boost — FREE")

    # ─── V10: daily routine card ──────────────────────────────────────────
    v10 = {
        "MORNING (5-9am)":  "Sun salute 12 + 5min meditation + drink moon-water + Hanuman Chalisa",
        "NOON (12-2pm)":    "Mindful lunch + 5min walk in sunlight + gratitude pause",
        "EVENING (6-9pm)":  "Mantra of weak planet + journal + family call (mother/father/teacher)",
        "NIGHT (before bed)":"3-min breathwork + read 1 wisdom page + sleep by 10:30pm",
    }

    # ─── V11: weekly day-wise card ────────────────────────────────────────
    weekly = {
        "Sunday":    "Sun mantra + wheat/jaggery donation + sunlight 30min",
        "Monday":    "Moon mantra + milk/rice donation + call mother",
        "Tuesday":   "Hanuman Chalisa + red-lentil donation + cold shower + HIIT",
        "Wednesday": "Vishnu mantra + green-vegetable diet + journaling + learning hour",
        "Thursday":  "Guru mantra + chana-dal/turmeric donation + read wisdom book",
        "Friday":    "Lakshmi mantra + white-sweet donation + art/music + self-care",
        "Saturday":  "Hanuman Chalisa + serve elderly + mustard-oil lamp + minimalist day",
    }
    v11 = weekly

    out.update({
        "v1_planet_remedies": v1,
        "v2_dosha_remedies": v2,
        "v3_yoga_remedies": v3,
        "v4_house_remedies": v4,
        "v5_lal_kitab_free": v5,
        "v6_modern_lifestyle": v6,
        "v7_effort_tier": v7,
        "v8_cost_tier": v8,
        "v9_top_priority": v9,
        "v10_daily_routine": v10,
        "v11_weekly_card": v11,
        "auto_detected_doshas": list(set(doshas)),
        "auto_detected_needy": needy,
    })
    return out


def format_remedies_engine(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ REMEDIES DEEP ENGINE: ❌ unavailable"
    L = ["▸ REMEDIES DEEP ENGINE — Sprint-49/Phase-V (deep + ethical + modern)",
         r["disclaimer"], "  " + "═"*78,
         f"  ⚐ Auto-detected needy planets: {', '.join(r['auto_detected_needy']) or 'none'}",
         f"  ⚐ Auto-detected doshas: {', '.join(r['auto_detected_doshas']) or 'none'}"]

    L.append("  V1 PER-PLANET 9-GRAHA REMEDY CARDS:")
    for p in r["v1_planet_remedies"]:
        L.append(f"      ━━━ {p['planet']} ━━━")
        L.append(f"          💎 Gem:      {p['gem']}")
        L.append(f"          📿 Mantra:   {p['mantra']}")
        L.append(f"          🎁 Donation: {p['donation']} ({p['day']})")
        L.append(f"          🎨 Color:    {p['color']}  •  Yantra: {p['yantra']}")
        L.append(f"          🍽 Fast:     {p['fast']}")
        L.append(f"          🆓 FREE alt: {p['free_alt']}")
        L.append(f"          🧠 Modern:   {p['modern']}")

    L.append("  V2 DOSHA REMEDIES (auto-detected):")
    if r["v2_dosha_remedies"]:
        for d in r["v2_dosha_remedies"]:
            L.append(f"      ▪ {d['dosha']}:")
            for rem in d["remedies"]:
                L.append(f"           ▸ {rem}")
    else:
        L.append("      ▪ No major doshas auto-detected — universal remedies apply")

    L.append("  V4 HOUSE-AFFLICTION REMEDIES (6/8/12 occupants):")
    if r["v4_house_remedies"]:
        for h in r["v4_house_remedies"]:
            L.append(f"      ▪ H{h['house']} ({h['label']}) — occupants: {', '.join(h['occupants'])}")
            L.append(f"           Free Lal Kitab: {h['free_remedy']}")
    else:
        L.append("      ▪ No 6/8/12 occupants — favourable")

    L.append("  V5 LAL KITAB FREE ACTIONS (for needy planets):")
    for x in r["v5_lal_kitab_free"]:
        L.append(f"      ▪ {x['planet']:<8} — {x['free_action']}")

    L.append("  V6 MODERN LIFESTYLE REMEDIES (for needy planets):")
    for x in r["v6_modern_lifestyle"]:
        L.append(f"      ▪ {x['planet']:<8} — {x['lifestyle']}")

    L.append(f"  V7 EFFORT TIER:  {r['v7_effort_tier']}")
    L.append(f"  V8 COST TIER:    {r['v8_cost_tier']}")

    L.append("  V9 TOP-7 PRIORITY REMEDIES for THIS chart:")
    for line in r["v9_top_priority"]:
        L.append(f"      ★ {line}")

    L.append("  V10 DAILY ROUTINE CARD:")
    for slot, action in r["v10_daily_routine"].items():
        L.append(f"      ▸ {slot:<22} → {action}")

    L.append("  V11 WEEKLY DAY-WISE CARD:")
    for day, action in r["v11_weekly_card"].items():
        L.append(f"      ▸ {day:<10} → {action}")

    return "\n".join(L)
