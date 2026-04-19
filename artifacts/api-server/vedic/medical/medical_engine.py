"""
Sprint 46 — MEDICAL ASTROLOGY ENGINE (Full Deep Engine)
Comprehensive 20-check chart-driven medical analyzer.

Coverage:
  M1.  Kalapurusha — 12 signs → body parts (full anatomy)
  M2.  Drekkana 36 organs — head-to-feet division
  M3.  Planet → body-system rulership (heart/blood/bones/nerves/skin/etc.)
  M4.  Roga Bhavas (6/8/12) — disease, chronic, hospitalization analysis
  M5.  Roga-bala — disease-strength score
  M6.  50+ classical disease yogas (diabetes, BP, cancer, mental, skin, etc.)
  M7.  Constitutional type (Vata/Pitta/Kapha) from chart
  M8.  Nadi from Janma Nakshatra (Aadi/Madhya/Antya)
  M9.  Maraka (life-shortening) planets
  M10. Disease activation windows from current Mahadasha/Antardasha
  M11. Mental health markers (Moon/Mercury/4th)
  M12. Hereditary disease indicators (5th/9th house affliction)
  M13. Per-organ deep analysis: heart/liver/kidney/eyes/lungs/stomach/reproductive/skin/bones/nervous
  M14. Ayurvedic dosha imbalance
  M15. Hospitalization windows (8/12 lord activation)
  M16. Surgical timing rules (Moon-sign avoidance)
  M17. Recovery / longevity indicators
  M18. Acute vs chronic disease classification
  M19. Per-organ weakness scorecard (0-10)
  M20. Body-part report card (all 36 drekkana parts + affliction state)
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
              "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
SIGN_ELEMENT = ["Fire","Earth","Air","Water","Fire","Earth",
                "Air","Water","Fire","Earth","Air","Water"]
SIGN_DOSHA = ["Pitta","Vata","Vata","Kapha","Pitta","Vata",
              "Vata","Kapha","Pitta","Vata","Vata","Kapha"]

# M1 — Kalapurusha sign→body part
KALAPURUSHA = [
    ("Aries",       "Head, brain, skull, face"),
    ("Taurus",      "Face, throat, neck, vocal cords, thyroid"),
    ("Gemini",      "Shoulders, arms, hands, lungs, nervous system"),
    ("Cancer",      "Chest, ribs, stomach, breasts, lymphatic"),
    ("Leo",         "Heart, upper back, spine, blood circulation"),
    ("Virgo",       "Intestines, digestion, abdomen, spleen"),
    ("Libra",       "Kidneys, lower back, lumbar, ovaries, urinary"),
    ("Scorpio",     "Reproductive organs, bladder, prostate, rectum"),
    ("Sagittarius", "Hips, thighs, liver, sciatic nerves, pelvis"),
    ("Capricorn",   "Knees, joints, bones, skin, teeth"),
    ("Aquarius",    "Calves, ankles, circulation, nervous system"),
    ("Pisces",      "Feet, toes, lymphatic, immune, glandular"),
]

# M2 — 36 Drekkanas (each sign has 3 drekkanas; ascending body part assignment)
DREKKANA_ORGANS = [
    "Head","Face","Neck","Right shoulder","Right upper arm","Right forearm",
    "Right hand & fingers","Heart","Chest","Abdomen (upper)","Abdomen (mid)",
    "Abdomen (lower)","Right hip","Right thigh","Right knee","Right calf",
    "Right ankle","Right foot",
    "Left foot","Left ankle","Left calf","Left knee","Left thigh","Left hip",
    "Pelvis","Reproductive organs","Bladder","Anus","Lower back","Mid back",
    "Upper back","Left hand & fingers","Left forearm","Left upper arm",
    "Left shoulder","Crown / brain"
]

# M3 — Planet → body-system rulership (classical)
PLANET_BODY = {
    "Sun":     ["Heart","Right eye","Bones","Spine","Vitality","Stomach acid"],
    "Moon":    ["Mind","Blood","Body fluids","Left eye","Lungs","Breasts","Lymph"],
    "Mars":    ["Blood","Bone marrow","Muscles","Energy","Genitals","Head injury risk"],
    "Mercury": ["Nervous system","Skin","Speech","Tongue","Intellect","Respiratory tract"],
    "Jupiter": ["Liver","Pancreas","Fat","Hips","Thighs","Hearing","Diabetes axis"],
    "Venus":   ["Reproductive","Kidneys","Throat","Ovaries","Hormones","Skin glow","Diabetes axis"],
    "Saturn":  ["Bones","Joints","Knees","Teeth","Nerves","Chronic ailments","Longevity"],
    "Rahu":    ["Mysterious illness","Mental confusion","Poisoning","Allergies","Skin"],
    "Ketu":    ["Surgical wounds","Infections","Mystery diseases","Spinal","Eye floaters"],
}

# M6 — 50+ classical disease yogas (chart-trigger predicates)
def _make_yogas():
    return [
      ("Diabetes (Madhumeha)",              "Jupiter+Venus weak/afflicted",
        lambda h,p,si,sb: ("Jupiter" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))) or
                         ("Venus" in (h.get(6,[])+h.get(8,[])+h.get(12,[])))),
      ("Hypertension (BP)",                 "Sun+Mars in fire/in malefic axis",
        lambda h,p,si,sb: ("Sun" in p and si.get("Sun",0) in (0,4,8)) and "Mars" in p),
      ("Heart disease",                     "Sun afflicted in 4/5/6",
        lambda h,p,si,sb: "Sun" in (h.get(4,[])+h.get(5,[])+h.get(6,[])) and
                          any(m in (h.get(4,[])+h.get(5,[])+h.get(6,[]))
                              for m in ("Saturn","Rahu","Ketu","Mars"))),
      ("Cancer risk (general)",             "Moon-Saturn-Rahu axis",
        lambda h,p,si,sb: "Moon" in p and "Saturn" in p and "Rahu" in p and
                          abs((si.get("Moon",0)-si.get("Saturn",0))%12) in (0,6,7)),
      ("Mental disturbance",                "Moon-Saturn or Moon-Rahu",
        lambda h,p,si,sb: ("Saturn" in h.get(4,[]) or "Rahu" in h.get(4,[])) or
                          (abs((si.get("Moon",0)-si.get("Saturn",0))%12) in (0,7))),
      ("Depression (Vishada)",              "Moon-Saturn conjunction or 4th afflicted",
        lambda h,p,si,sb: si.get("Moon")==si.get("Saturn") or
                          "Saturn" in h.get(4,[])),
      ("Skin disease (Kushtha)",            "Mercury+Moon weak; Saturn/Rahu on Moon",
        lambda h,p,si,sb: "Saturn" in h.get(6,[]) or
                          ("Mercury" in (h.get(6,[])+h.get(8,[])+h.get(12,[])))),
      ("Eye disease (right eye)",           "Sun in 6/8/12 or with malefic",
        lambda h,p,si,sb: "Sun" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Eye disease (left eye)",            "Moon in 6/8/12 or with malefic",
        lambda h,p,si,sb: "Moon" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Liver / Pancreas issue",            "Jupiter weak in 6/8/12",
        lambda h,p,si,sb: "Jupiter" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Kidney / Urinary",                  "Venus afflicted; 7th house malefic",
        lambda h,p,si,sb: "Venus" in (h.get(6,[])+h.get(8,[])+h.get(12,[])) or
                          any(m in h.get(7,[]) for m in ("Saturn","Rahu","Ketu"))),
      ("Joint / Arthritis",                 "Saturn in 1/6/8",
        lambda h,p,si,sb: "Saturn" in (h.get(1,[])+h.get(6,[])+h.get(8,[]))),
      ("Asthma / Respiratory",              "Mercury+Moon in 6/8/12; airy signs",
        lambda h,p,si,sb: "Mercury" in (h.get(6,[])+h.get(8,[])+h.get(12,[])) and
                          "Moon" in p),
      ("Allergies",                         "Rahu in 6/8/12 or with Mercury",
        lambda h,p,si,sb: "Rahu" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Anaemia / Blood disorder",          "Mars+Moon weak/afflicted",
        lambda h,p,si,sb: "Mars" in (h.get(6,[])+h.get(8,[])+h.get(12,[])) and
                          "Moon" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Migraine / headache",               "Mars/Sun in 1st or 11th",
        lambda h,p,si,sb: "Mars" in h.get(1,[]) or "Sun" in h.get(1,[]) or "Mars" in h.get(11,[])),
      ("Stomach / digestive",               "Moon+Mercury afflicted; 5th house",
        lambda h,p,si,sb: any(m in h.get(5,[]) for m in ("Saturn","Mars","Rahu","Ketu"))),
      ("Reproductive / Infertility",        "Jupiter+Venus afflicted; 5th house",
        lambda h,p,si,sb: any(m in h.get(5,[]) for m in ("Saturn","Rahu","Ketu","Mars")) and
                          ("Jupiter" in (h.get(6,[])+h.get(8,[])+h.get(12,[])))),
      ("Sexual dysfunction",                "Venus+Mars afflicted; 7th/8th",
        lambda h,p,si,sb: any(m in h.get(8,[]) for m in ("Saturn","Rahu","Ketu"))),
      ("Bone / fracture",                   "Saturn-Mars in kendras",
        lambda h,p,si,sb: ("Saturn" in p and "Mars" in p and
                           abs((si.get("Saturn",0)-si.get("Mars",0))%12) in (0,3,6,9))),
      ("Teeth / dental",                    "Saturn in 2/7",
        lambda h,p,si,sb: "Saturn" in (h.get(2,[])+h.get(7,[]))),
      ("Hearing / ear issue",               "Jupiter weak; Mercury in 3/11",
        lambda h,p,si,sb: "Jupiter" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Speech defect",                     "2nd house afflicted; Mercury weak",
        lambda h,p,si,sb: any(m in h.get(2,[]) for m in ("Saturn","Rahu","Ketu","Mars"))),
      ("Thyroid",                           "2nd lord weak; Mercury affliction",
        lambda h,p,si,sb: "Saturn" in h.get(2,[]) or "Rahu" in h.get(2,[])),
      ("Cholesterol",                       "Jupiter+Saturn axis with 5th/9th",
        lambda h,p,si,sb: "Jupiter" in p and "Saturn" in p and
                          abs((si.get("Jupiter",0)-si.get("Saturn",0))%12) in (0,7)),
      ("Stroke risk",                       "Sun-Saturn-Rahu in fire signs",
        lambda h,p,si,sb: "Sun" in p and "Saturn" in p and "Rahu" in p and
                          si.get("Sun",0) in (0,4,8)),
      ("Paralysis",                         "Saturn+Rahu in kendras",
        lambda h,p,si,sb: ("Saturn" in p and "Rahu" in p and
                           abs((si.get("Saturn",0)-si.get("Rahu",0))%12) in (0,3,6,9))),
      ("Insomnia",                          "Moon-Saturn or 4th afflicted",
        lambda h,p,si,sb: si.get("Moon")==si.get("Saturn") or "Saturn" in h.get(4,[])),
      ("Anxiety / panic",                   "Mercury-Rahu or Moon-Rahu",
        lambda h,p,si,sb: si.get("Mercury")==si.get("Rahu") or si.get("Moon")==si.get("Rahu")),
      ("Obesity",                           "Jupiter strong + Moon water sign",
        lambda h,p,si,sb: si.get("Moon",0) in (3,7,11) and "Jupiter" in p),
      ("Underweight",                       "Saturn strong + Mars-Sun weak",
        lambda h,p,si,sb: "Saturn" in (h.get(1,[])+h.get(2,[])) and
                          "Mars" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Acne / Skin pigmentation",          "Venus afflicted; Sun-Mars axis",
        lambda h,p,si,sb: "Venus" in (h.get(6,[])+h.get(8,[])+h.get(12,[])) and
                          ("Sun" in p and "Mars" in p)),
      ("Hair loss / baldness",              "Sun+Mars in 11th or Saturn in 1st",
        lambda h,p,si,sb: "Sun" in h.get(11,[]) or "Mars" in h.get(11,[]) or "Saturn" in h.get(1,[])),
      ("Auto-immune",                       "Ketu in 6/8/12 with Moon",
        lambda h,p,si,sb: "Ketu" in (h.get(6,[])+h.get(8,[])+h.get(12,[])) and "Moon" in p),
      ("Blood-pressure low",                "Moon-Saturn-Ketu in watery sign",
        lambda h,p,si,sb: si.get("Moon",0) in (3,7,11) and "Saturn" in p and "Ketu" in p),
      ("Acidity / Ulcer",                   "Mars in 5th or Sun in 5th",
        lambda h,p,si,sb: "Mars" in h.get(5,[]) or "Sun" in h.get(5,[])),
      ("Constipation / Piles",              "Saturn in 7th/8th",
        lambda h,p,si,sb: "Saturn" in (h.get(7,[])+h.get(8,[]))),
      ("Tuberculosis",                      "Moon-Mars-Saturn weak combo",
        lambda h,p,si,sb: ("Moon" in p and "Saturn" in p and
                           abs((si.get("Moon",0)-si.get("Saturn",0))%12) in (0,7))),
      ("Epilepsy",                          "Moon-Saturn-Mars axis to Mercury",
        lambda h,p,si,sb: ("Mercury" in p and "Saturn" in p and "Moon" in p and
                           si.get("Mercury")==si.get("Saturn"))),
      ("Vertigo",                           "Mercury weak + Vata signs",
        lambda h,p,si,sb: si.get("Mercury",0) in (1,2,5,6,9,10) and
                          "Mercury" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Migraine chronic",                  "Mars in 9th or 1st with Rahu",
        lambda h,p,si,sb: "Mars" in h.get(1,[]) and "Rahu" in p),
      ("Spinal issue",                      "Sun afflicted in 5th/8th",
        lambda h,p,si,sb: "Sun" in (h.get(5,[])+h.get(8,[]))),
      ("Sciatica",                          "Saturn in 9th",
        lambda h,p,si,sb: "Saturn" in h.get(9,[])),
      ("Gout / Uric acid",                  "Saturn-Mars-Jupiter axis",
        lambda h,p,si,sb: "Saturn" in p and "Mars" in p and "Jupiter" in p and
                          abs((si.get("Saturn",0)-si.get("Mars",0))%12) in (0,7)),
      ("Tumour / Cyst",                     "Rahu-Saturn in 6/8/12",
        lambda h,p,si,sb: any(p_ in (h.get(6,[])+h.get(8,[])+h.get(12,[]))
                              for p_ in ("Rahu","Saturn"))),
      ("Vision blurring",                   "Sun+Moon both in 6/8/12",
        lambda h,p,si,sb: "Sun" in (h.get(6,[])+h.get(8,[])+h.get(12,[])) and
                          "Moon" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
      ("Anaesthesia / Surgery sensitivity", "Ketu in 1/8",
        lambda h,p,si,sb: "Ketu" in (h.get(1,[])+h.get(8,[]))),
      ("Auto-accident proneness",           "Mars+Rahu in 1/4/7/10",
        lambda h,p,si,sb: ("Mars" in p and "Rahu" in p and
                           abs((si.get("Mars",0)-si.get("Rahu",0))%12) in (0,3,6,9))),
      ("Poisoning / drug reactions",        "Rahu in 1st",
        lambda h,p,si,sb: "Rahu" in h.get(1,[])),
      ("Liver cirrhosis (alcohol)",         "Jupiter-Rahu axis to 6/8/12",
        lambda h,p,si,sb: "Jupiter" in p and "Rahu" in p and
                          abs((si.get("Jupiter",0)-si.get("Rahu",0))%12) in (0,7)),
      ("Throat / vocal cord",               "2nd house with Saturn or Rahu",
        lambda h,p,si,sb: "Saturn" in h.get(2,[]) or "Rahu" in h.get(2,[])),
      ("Headache (general)",                "Mars in 1st",
        lambda h,p,si,sb: "Mars" in h.get(1,[])),
      ("Lung weakness",                     "Mercury-Moon in 6/8/12",
        lambda h,p,si,sb: "Mercury" in (h.get(6,[])+h.get(8,[])+h.get(12,[])) and
                          "Moon" in (h.get(6,[])+h.get(8,[])+h.get(12,[]))),
    ]

DISEASE_YOGAS = _make_yogas()

# M8 — Nakshatra → Nadi (1=Vata/Aadi, 2=Pitta/Madhya, 3=Kapha/Antya), 27 nakshatras
NAKSHATRA_NADI = [1,2,3,3,2,1,1,2,3,3,2,1,1,2,3,3,2,1,1,2,3,3,2,1,1,2,3]
NADI_NAMES = {1:"Aadi (Vata)", 2:"Madhya (Pitta)", 3:"Antya (Kapha)"}

# M13 — Specific organs deep table
ORGAN_RULERS = {
    "Heart":              ("Sun, Leo, 4th/5th house",            ["Sun","Moon"]),
    "Brain":              ("Mercury, Aries, 1st house",           ["Mercury","Moon"]),
    "Liver":              ("Jupiter, Sagittarius, 9th house",     ["Jupiter"]),
    "Kidney":             ("Venus, Libra, 7th house",             ["Venus"]),
    "Stomach":            ("Moon, Cancer/Virgo, 5th",             ["Moon","Mercury"]),
    "Lungs":              ("Mercury, Gemini, 3rd house",          ["Mercury","Moon"]),
    "Eyes (R/L)":         ("Sun (R) / Moon (L), 2nd/12th",        ["Sun","Moon"]),
    "Reproductive":       ("Venus, Scorpio, 8th house",           ["Venus","Mars"]),
    "Skin":               ("Mercury+Saturn, Capricorn",           ["Mercury","Saturn"]),
    "Bones / Joints":     ("Saturn, Capricorn, 10th",             ["Saturn"]),
    "Nervous system":     ("Mercury, Gemini/Virgo",               ["Mercury"]),
    "Digestive":          ("Moon+Mars, Cancer/Virgo, 5th",        ["Moon","Mars"]),
    "Respiratory":        ("Mercury+Moon, Gemini",                ["Mercury","Moon"]),
    "Endocrine / Hormones":("Jupiter+Venus",                      ["Jupiter","Venus"]),
    "Blood":              ("Mars+Moon",                            ["Mars","Moon"]),
}


def _build_house_map(planets, lagna_si):
    h_map = {i: [] for i in range(1,13)}
    p_si = {}
    p_lon = {}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon,(int,float)): continue
        si = int(lon // 30) % 12
        h = ((si - lagna_si) % 12) + 1
        h_map[h].append(p["name"])
        p_si[p["name"]] = si
        p_lon[p["name"]] = lon
    return h_map, p_si, p_lon


def run_medical_engine(kundli: dict, birth: dict | None = None,
                       shadbala: dict | None = None,
                       current_dasha: dict | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"available": True, "checks_run": 20}
    planets = kundli.get("planets") or []
    lag = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    try: lagna_si = SIGN_NAMES.index(lag)
    except Exception: lagna_si = 0

    h_map, p_si, p_lon = _build_house_map(planets, lagna_si)
    planet_set = set(p_si.keys())

    sb_total = {}
    if isinstance(shadbala, dict):
        for k, v in (shadbala.get("planets") or shadbala or {}).items():
            if isinstance(v, dict):
                t = v.get("total_rupas") or v.get("total") or v.get("rupas")
                if isinstance(t,(int,float)): sb_total[k] = float(t)

    # M1 Kalapurusha map
    out["m1_kalapurusha"] = [
        {"sign": s, "body_parts": parts,
         "planets_here": [p for p,si in p_si.items() if SIGN_NAMES[si]==s]}
        for s, parts in KALAPURUSHA
    ]

    # M2 Drekkana 36 organs
    drekkana_planets: dict[int, list[str]] = {i: [] for i in range(36)}
    for p_name, lon in p_lon.items():
        si = int(lon//30) % 12
        deg = lon % 30
        drek_in_sign = int(deg // 10)  # 0,1,2
        idx = si*3 + drek_in_sign
        drekkana_planets[idx % 36].append(p_name)
    out["m2_drekkana_36_organs"] = [
        {"index": i+1, "organ": DREKKANA_ORGANS[i % 36],
         "planets_here": drekkana_planets[i]}
        for i in range(36)
    ]

    # M3 Planet → body system
    out["m3_planet_body_systems"] = [
        {"planet": pl, "rules": rules,
         "in_house": next((h for h,plist in h_map.items() if pl in plist), None),
         "afflicted": pl in (h_map.get(6,[])+h_map.get(8,[])+h_map.get(12,[]))}
        for pl, rules in PLANET_BODY.items()
    ]

    # M4 Roga Bhavas
    roga = {h: h_map.get(h,[]) for h in (6,8,12)}
    lord6 = SIGN_LORDS[(lagna_si+5)%12]
    lord8 = SIGN_LORDS[(lagna_si+7)%12]
    lord12= SIGN_LORDS[(lagna_si+11)%12]
    out["m4_roga_bhavas"] = {
        "houses": roga,
        "sixth_lord": lord6, "eighth_lord": lord8, "twelfth_lord": lord12,
        "sixth_lord_house":  next((h for h,pl in h_map.items() if lord6  in pl), None),
        "eighth_lord_house": next((h for h,pl in h_map.items() if lord8  in pl), None),
        "twelfth_lord_house":next((h for h,pl in h_map.items() if lord12 in pl), None),
    }

    # M5 Roga-bala (disease score)
    score = 0
    score += 2*len(roga[6]) + 3*len(roga[8]) + 2*len(roga[12])
    if any(m in roga[6]+roga[8]+roga[12] for m in ("Saturn","Rahu","Ketu","Mars")):
        score += 5
    if "Moon" in roga[6]+roga[8]+roga[12]: score += 3
    if "Sun" in roga[6]+roga[8]+roga[12]:  score += 2
    rb_rating = ("LOW" if score<=4 else "MODERATE" if score<=10 else "HIGH" if score<=18 else "VERY HIGH")
    out["m5_roga_bala"] = {"score": score, "rating": rb_rating,
                           "interpretation": f"{rb_rating} disease vulnerability"}

    # M6 Disease yogas — run all
    triggered = []
    for name, basis, fn in DISEASE_YOGAS:
        try:
            if fn(h_map, planet_set, p_si, sb_total):
                triggered.append({"yoga": name, "basis": basis})
        except Exception:
            pass
    out["m6_disease_yogas"] = {"total_checked": len(DISEASE_YOGAS),
                               "triggered_count": len(triggered),
                               "triggered": triggered}

    # M7 Constitutional type
    dosha_count = {"Vata":0, "Pitta":0, "Kapha":0}
    for name, si in p_si.items():
        if name in ("Rahu","Ketu"): continue
        dosha_count[SIGN_DOSHA[si]] += 1
    dosha_count[SIGN_DOSHA[lagna_si]] += 2  # lagna gets weight
    primary = max(dosha_count, key=dosha_count.get)
    secondary = sorted(dosha_count, key=dosha_count.get, reverse=True)[1]
    out["m7_constitution"] = {"counts": dosha_count, "primary_dosha": primary,
                               "secondary_dosha": secondary,
                               "type": f"{primary}-{secondary} predominant"}

    # M8 Nadi from Janma Nakshatra
    moon_lon = p_lon.get("Moon")
    nadi = None; nak_idx = None
    if moon_lon is not None:
        nak_idx = int(moon_lon // (360/27)) % 27
        nadi = NAKSHATRA_NADI[nak_idx]
    out["m8_nadi"] = {"nakshatra_index": nak_idx,
                      "nadi": NADI_NAMES.get(nadi) if nadi else None}

    # M9 Maraka
    lord2 = SIGN_LORDS[(lagna_si+1)%12]
    lord7 = SIGN_LORDS[(lagna_si+6)%12]
    out["m9_marakas"] = {"second_lord_maraka": lord2, "seventh_lord_maraka": lord7,
                         "rule":"2nd & 7th lords activate health-critical periods in their dasha"}

    # M10 Disease activation windows (current dasha)
    md_lord = (current_dasha or {}).get("md_lord") or (current_dasha or {}).get("mahadasha")
    ad_lord = (current_dasha or {}).get("ad_lord") or (current_dasha or {}).get("antardasha")
    activation_risk = "LOW"
    risk_reason = []
    for L, label in ((md_lord,"MD"), (ad_lord,"AD")):
        if not L: continue
        if L in (h_map.get(6,[])+h_map.get(8,[])+h_map.get(12,[])):
            activation_risk = "HIGH"
            risk_reason.append(f"{label} lord {L} in 6/8/12")
        elif L in (lord6, lord8, lord12, lord2, lord7):
            activation_risk = "MODERATE" if activation_risk!="HIGH" else activation_risk
            risk_reason.append(f"{label} lord {L} = roga/maraka lord")
    out["m10_dasha_health_window"] = {
        "current_md": md_lord, "current_ad": ad_lord,
        "activation_risk": activation_risk, "reasons": risk_reason}

    # M11 Mental health markers
    mh_score = 0; mh_notes = []
    if "Saturn" in h_map.get(4,[]):  mh_score += 3; mh_notes.append("Saturn in 4th — depressive tendency")
    if "Rahu" in h_map.get(4,[]):    mh_score += 3; mh_notes.append("Rahu in 4th — anxiety/confusion")
    if p_si.get("Moon")==p_si.get("Saturn"): mh_score += 4; mh_notes.append("Moon-Saturn — chronic gloom risk")
    if p_si.get("Moon")==p_si.get("Rahu"):   mh_score += 4; mh_notes.append("Moon-Rahu — irrational fears")
    if "Mercury" in (h_map.get(6,[])+h_map.get(8,[])+h_map.get(12,[])): mh_score+=2; mh_notes.append("Mercury weak — overthinking")
    out["m11_mental_health"] = {"score": mh_score,
        "rating": "FRAGILE" if mh_score>=7 else "VULNERABLE" if mh_score>=4 else "STABLE",
        "markers": mh_notes}

    # M12 Hereditary disease (5th=mother-line, 9th=father-line)
    h5 = h_map.get(5, []); h9 = h_map.get(9, [])
    out["m12_hereditary"] = {
        "fifth_house_planets": h5,
        "ninth_house_planets": h9,
        "maternal_line_risk": [p for p in h5 if p in ("Saturn","Rahu","Ketu","Mars")],
        "paternal_line_risk": [p for p in h9 if p in ("Saturn","Rahu","Ketu","Mars")],
    }

    # M13 Per-organ deep
    organ_report = []
    afflicting = set(h_map.get(6,[])+h_map.get(8,[])+h_map.get(12,[]))
    for organ, (rule, planets_) in ORGAN_RULERS.items():
        weak_planets = [p for p in planets_ if p in afflicting]
        organ_report.append({"organ": organ, "rule": rule,
                             "ruling_planets": planets_,
                             "afflicted_rulers": weak_planets,
                             "status": "WEAK" if weak_planets else "OK"})
    out["m13_organs"] = organ_report

    # M14 Ayurvedic dosha imbalance
    out["m14_dosha_imbalance"] = {
        "primary": out["m7_constitution"]["primary_dosha"],
        "balance_advice": {
            "Vata":"Warm/oily food, oil massage, regular routine, avoid cold/raw",
            "Pitta":"Cool/sweet food, avoid spice & sun, ghee, coconut",
            "Kapha":"Light/spicy food, exercise, dry/warm, avoid dairy/sweet",
        }.get(out["m7_constitution"]["primary_dosha"])
    }

    # M15 Hospitalization windows
    out["m15_hospitalization_window"] = {
        "trigger_lords": [lord8, lord12],
        "rule":"Hospitalization peaks during MD/AD of 8th or 12th lord, especially when transit Saturn aspects natal Moon"
    }

    # M16 Surgical timing
    out["m16_surgical_timing_rules"] = {
        "avoid_rule":"Avoid surgery when transit Moon is in the SIGN of the body part being operated",
        "favourable_tithis":"Shukla Paksha (waxing Moon) preferred; avoid Krishna Paksha for elective surgery",
        "avoid_nakshatras":["Bharani","Krittika","Ardra","Ashlesha","Magha","Mula","Jyeshtha"],
        "favourable_horas":"Mercury, Jupiter, Venus hora best",
    }

    # M17 Recovery / longevity
    lord1 = SIGN_LORDS[lagna_si]
    out["m17_longevity_recovery"] = {
        "lagna_lord": lord1,
        "lagna_lord_house": next((h for h,pl in h_map.items() if lord1 in pl), None),
        "ayur_indicator": "STRONG" if (sb_total.get(lord1,0)>=6 if sb_total else
                                        lord1 not in afflicting) else "MODERATE",
        "rule":"Lagna lord in kendra/trikona = good recovery; in dushtana = slow healing",
    }

    # M18 Acute vs chronic
    chronic_planets = [p for p in h_map.get(6,[])+h_map.get(8,[])+h_map.get(12,[])
                       if p in ("Saturn","Rahu","Ketu")]
    acute_planets = [p for p in h_map.get(6,[])+h_map.get(8,[])+h_map.get(12,[])
                     if p in ("Mars","Sun")]
    out["m18_acute_vs_chronic"] = {
        "chronic_indicators": chronic_planets,
        "acute_indicators": acute_planets,
        "dominant": ("CHRONIC" if len(chronic_planets)>len(acute_planets)
                     else "ACUTE" if acute_planets else "BALANCED")
    }

    # M19 Per-organ weakness scorecard (0-10)
    scorecard = []
    for o in organ_report:
        s = 10
        for ap in o["afflicted_rulers"]:
            s -= 3
        s = max(0, s)
        scorecard.append({"organ": o["organ"], "weakness_score": 10-s,
                          "strength_score": s,
                          "status": "WEAK" if s<=4 else "OK" if s<=7 else "STRONG"})
    out["m19_organ_scorecard"] = scorecard

    # M20 Body-part report card (36 drekkana parts + affliction)
    body_card = []
    for d in out["m2_drekkana_36_organs"]:
        afflictors = [p for p in d["planets_here"] if p in ("Saturn","Mars","Rahu","Ketu","Sun")]
        body_card.append({"organ": d["organ"], "drekkana_index": d["index"],
                          "planets_here": d["planets_here"],
                          "afflictors": afflictors,
                          "status": "AFFLICTED" if afflictors else
                                    "ENERGIZED" if d["planets_here"] else "NEUTRAL"})
    out["m20_body_part_card"] = body_card

    return out


def format_medical_engine(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ MEDICAL ASTROLOGY ENGINE: ❌ unavailable"
    L = ["▸ MEDICAL ASTROLOGY ENGINE — FULL DEEP AUDIT (Sprint-46) — 20 checks"]

    # M1
    L.append("  M1 KALAPURUSHA (12-sign body map):")
    for x in r["m1_kalapurusha"]:
        marker = f" ← planets: {x['planets_here']}" if x["planets_here"] else ""
        L.append(f"      ▪ {x['sign']:<11} → {x['body_parts']}{marker}")

    # M2
    L.append("  M2 DREKKANA 36 ORGANS (head→feet, with planet placements):")
    for d in r["m2_drekkana_36_organs"]:
        if d["planets_here"]:
            L.append(f"      ▪ #{d['index']:<2} {d['organ']:<22} ← {', '.join(d['planets_here'])}")

    # M3
    L.append("  M3 PLANET → BODY SYSTEMS (with affliction flag):")
    for x in r["m3_planet_body_systems"]:
        flag = " ⚠AFFLICTED" if x["afflicted"] else ""
        L.append(f"      ▪ {x['planet']:<8} (H{x['in_house']}){flag} → {', '.join(x['rules'])}")

    # M4
    rb = r["m4_roga_bhavas"]
    L.append(f"  M4 ROGA BHAVAS (6/8/12) — H6:{rb['houses'][6]} H8:{rb['houses'][8]} H12:{rb['houses'][12]}")
    L.append(f"      ▪ 6th-lord {rb['sixth_lord']} in H{rb['sixth_lord_house']}, "
             f"8th-lord {rb['eighth_lord']} in H{rb['eighth_lord_house']}, "
             f"12th-lord {rb['twelfth_lord']} in H{rb['twelfth_lord_house']}")

    # M5
    rb5 = r["m5_roga_bala"]
    L.append(f"  M5 ROGA-BALA disease score: {rb5['score']} → {rb5['rating']} — {rb5['interpretation']}")

    # M6
    dy = r["m6_disease_yogas"]
    L.append(f"  M6 DISEASE YOGAS — {dy['triggered_count']}/{dy['total_checked']} triggered:")
    for y in dy["triggered"]:
        L.append(f"      ⚠ {y['yoga']} — basis: {y['basis']}")
    if not dy["triggered"]:
        L.append("      ▪ No major disease yogas detected ✅")

    # M7
    c = r["m7_constitution"]
    L.append(f"  M7 CONSTITUTION (Ayurvedic): {c['type']} — counts {c['counts']}")

    # M8
    n = r["m8_nadi"]
    if n["nadi"]:
        L.append(f"  M8 NADI (Janma): {n['nadi']}")

    # M9
    m9 = r["m9_marakas"]
    L.append(f"  M9 MARAKAS — 2nd-lord {m9['second_lord_maraka']}, 7th-lord {m9['seventh_lord_maraka']}")

    # M10
    m10 = r["m10_dasha_health_window"]
    if m10["current_md"]:
        L.append(f"  M10 CURRENT DASHA HEALTH WINDOW: MD={m10['current_md']} AD={m10['current_ad']} "
                 f"→ {m10['activation_risk']} risk")
        for r_ in m10["reasons"]: L.append(f"        • {r_}")

    # M11
    mh = r["m11_mental_health"]
    L.append(f"  M11 MENTAL HEALTH — score {mh['score']} → {mh['rating']}:")
    for m_ in mh["markers"]: L.append(f"        • {m_}")
    if not mh["markers"]: L.append("        • No mental-health red flags ✅")

    # M12
    h = r["m12_hereditary"]
    L.append(f"  M12 HEREDITARY — maternal-line risks: {h['maternal_line_risk']}, "
             f"paternal-line risks: {h['paternal_line_risk']}")

    # M13
    L.append("  M13 PER-ORGAN STATUS:")
    for o in r["m13_organs"]:
        L.append(f"      ▪ {o['organ']:<22} {o['status']:<5} (rulers {o['ruling_planets']}, "
                 f"afflicted: {o['afflicted_rulers'] or 'none'})")

    # M14
    d = r["m14_dosha_imbalance"]
    L.append(f"  M14 DOSHA BALANCE — primary {d['primary']}: {d['balance_advice']}")

    # M15
    h_ = r["m15_hospitalization_window"]
    L.append(f"  M15 HOSPITALIZATION WINDOW — trigger lords {h_['trigger_lords']}: {h_['rule']}")

    # M16
    s_ = r["m16_surgical_timing_rules"]
    L.append(f"  M16 SURGICAL TIMING:")
    L.append(f"        • {s_['avoid_rule']}")
    L.append(f"        • Favorable: {s_['favourable_tithis']}")
    L.append(f"        • Avoid nakshatras: {', '.join(s_['avoid_nakshatras'])}")
    L.append(f"        • Best horas: {s_['favourable_horas']}")

    # M17
    lr = r["m17_longevity_recovery"]
    L.append(f"  M17 LONGEVITY/RECOVERY — Lagna-lord {lr['lagna_lord']} in H{lr['lagna_lord_house']} "
             f"→ {lr['ayur_indicator']} recovery capacity")

    # M18
    ac = r["m18_acute_vs_chronic"]
    L.append(f"  M18 ACUTE vs CHRONIC: dominant = {ac['dominant']} "
             f"(chronic: {ac['chronic_indicators']}, acute: {ac['acute_indicators']})")

    # M19
    L.append("  M19 ORGAN STRENGTH SCORECARD (0=dead, 10=robust):")
    for s in r["m19_organ_scorecard"]:
        bar = "█"*s["strength_score"] + "·"*(10-s["strength_score"])
        L.append(f"      ▪ {s['organ']:<22} [{bar}] {s['strength_score']}/10 {s['status']}")

    # M20 (afflicted only)
    L.append("  M20 BODY-PART CARD (36 drekkana, only afflicted/energized shown):")
    for b in r["m20_body_part_card"]:
        if b["status"] != "NEUTRAL":
            mark = "⚠" if b["status"]=="AFFLICTED" else "•"
            L.append(f"      {mark} #{b['drekkana_index']:<2} {b['organ']:<22} "
                     f"({b['status']}) ← {b['planets_here']}")

    return "\n".join(L)
