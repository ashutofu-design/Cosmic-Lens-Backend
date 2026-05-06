"""Remedy Catalog — single source of truth for the 3-tier remedy stack.

Every entry follows the schema:

    CATALOG[topic][planet] = {
        "practical":  {action, why, time_to_result, kpi, free, cost_inr},
        "ayurvedic":  {practice, herb, dose, vaidya_caveat, time_to_result},
        "vedic":      {day, mantra, count, donation, gemstone, gem_caveat,
                        cost_inr_paid, free_alt},
        "for_areas":  comma-sep tags (matches systems/areas list per topic),
    }

DESIGN LOCKS (per user mandate, May 6 2026):
- Tier-1 PRACTICAL is ALWAYS shown FIRST. Vedic comes LAST.
- Every paid item carries cost ballpark + caveat ("90% of street stones
  are synthetic — buy with cert", "Trial 3 days first", etc).
- Every health remedy paired with measurable KPI (BP, sleep, weight,
  blood-test, mood-rating) so user can self-verify outcome in 21-40 d.
- Mantras + gemstones cited from BPHS / Phaladeepika / Lal-Kitab consensus.
- Ayurvedic guidance carries vaidya-consult disclaimer for any internal
  herb (Charaka principle: dose depends on prakriti, never universal).
- NEVER recommend vedic-only — engine selector forces practical pairing.

Topics covered: health, marriage, career.
Planets covered: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu,
Ketu (9 grahas).
"""
from __future__ import annotations

from typing import Any, Dict


# ════════════════════════════════════════════════════════════════════════
# HEALTH — 9 planets × 3 tiers
# ════════════════════════════════════════════════════════════════════════
_HEALTH: Dict[str, Dict[str, Any]] = {
    "Sun": {
        "for_areas": "heart, eyes, vitality, bones, vitamin-D",
        "practical": {
            "action":         "Morning sunlight 15-20 min before 9 AM (eyes closed, face exposed) + ECG + Vit-D test if not done in 12 mo",
            "why":            "Sun rules vitality — direct sunlight regulates circadian + Vit-D + mood. Lab data > faith.",
            "time_to_result": "2 weeks (mood + sleep), 8 weeks (Vit-D level)",
            "kpi":            "Vit-D 30-60 ng/ml, resting HR < 75, sleep onset < 20 min",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Surya namaskar 12 rounds at sunrise + Aditya Hridaya Stotra path",
            "herb":           "Amla (1 fresh fruit OR 1 tsp powder with honey daily)",
            "dose":           "1× daily morning, empty stomach",
            "vaidya_caveat":  "Skip if acid reflux active — consult vaidya for pitta-prakriti dose",
            "time_to_result": "4-6 weeks (immunity, eye health)",
        },
        "vedic": {
            "day":            "Sunday",
            "mantra":         "Om Hraam Hreem Hraum Sah Suryaya Namah",
            "count":          "108",
            "donation":       "Wheat + jaggery + red cloth at a temple Sunday morning",
            "gemstone":       "Manik (Ruby) 3-5 ct, copper, ring finger",
            "gem_caveat":     "Astrologer-fitted only. Synthetic ₹500-2000, natural ₹15K-2L. Get IGI/GIA cert.",
            "cost_inr_paid":  "15,000 – 2,00,000 (gemstone) | 0-200 (donation)",
            "free_alt":       "Tulsi-jal arpan to Sun OR feed jaggery-water to a cow Sunday",
        },
    },
    "Moon": {
        "for_areas": "mind, sleep, fluids, digestion, mother, hormones",
        "practical": {
            "action":         "Sleep window 10:30 PM-6 AM + screen-off 1 hr before bed + 2-3 L water/day + B12+thyroid blood test if mood-low",
            "why":            "Moon governs mind & fluids — sleep hygiene + hydration + thyroid panel directly fix 60% mood/fatigue cases. Faith doesn't fix B12 deficiency.",
            "time_to_result": "2-3 weeks (mood, energy)",
            "kpi":            "Sleep > 6.5 hr, B12 > 400 pg/ml, TSH 0.4-4.0",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Bhramari pranayama 10 rounds at night + warm milk with nutmeg pinch + Sheetali pranayama for anger/heat",
            "herb":           "Brahmi (½ tsp powder OR vaidya-prescribed tablet) + Jatamansi for sleep",
            "dose":           "Brahmi 1× morning, Jatamansi 1× before bed",
            "vaidya_caveat":  "Brahmi can lower BP — skip if hypotensive. Vaidya consult for pregnancy.",
            "time_to_result": "4 weeks (sleep), 8 weeks (anxiety)",
        },
        "vedic": {
            "day":            "Monday",
            "mantra":         "Om Som Somaya Namah",
            "count":          "108",
            "donation":       "Milk + white rice + white cloth to a needy person Monday",
            "gemstone":       "Moti (Pearl) 4-6 ct, silver, ring finger",
            "gem_caveat":     "Natural ₹3K-50K. Real pearl drilled hole shows growth lines under loupe.",
            "cost_inr_paid":  "3,000 – 50,000 (gemstone)",
            "free_alt":       "Chandra namaskar at moonrise + Shiva Panchakshari japa",
        },
    },
    "Mars": {
        "for_areas": "blood, muscles, inflammation, accident-risk, surgery, anger",
        "practical": {
            "action":         "Daily 30-min walk + skip alcohol 21 days + CBC blood test in 7 days + drive defensively (no phone, seatbelt, no shortcuts)",
            "why":            "Mars rules blood + accidents — CBC catches anemia/inflammation EARLY; skipping alcohol drops BP+inflammation in 21 d; defensive driving cuts accident risk 70%.",
            "time_to_result": "1 week (CBC), 3 weeks (BP + sleep), 6 weeks (inflammation markers)",
            "kpi":            "Hb > 12 (F) / 13 (M), CRP < 3, BP < 130/85, zero close-call driving incidents",
            "free":           True,
            "cost_inr":       400,  # CBC test
        },
        "ayurvedic": {
            "practice":       "Sheetali pranayama 10 rounds + cooling diet (ghee, coconut, cucumber, mint) + avoid red meat & green chilli on Tuesday",
            "herb":           "Manjistha (½ tsp powder) for blood + Guduchi for inflammation + Ashwagandha if low energy",
            "dose":           "Manjistha 1× evening, Guduchi 1× morning",
            "vaidya_caveat":  "Manjistha thins blood — skip if on blood thinners. Pregnancy: vaidya only.",
            "time_to_result": "4-6 weeks (skin, blood markers)",
        },
        "vedic": {
            "day":            "Tuesday",
            "mantra":         "Om Ang Angarakaya Namah",
            "count":          "108",
            "donation":       "Red lentils (masoor) + red cloth + jaggery Tuesday",
            "gemstone":       "Moonga (Red Coral) 6-8 ct, copper, ring finger",
            "gem_caveat":     "TRIAL 3 days first — coral spikes anger in some. Italian deep-red genuine ₹5K-30K. Avoid 'Japanese' bleached.",
            "cost_inr_paid":  "5,000 – 30,000 (gemstone)",
            "free_alt":       "Hanuman Chalisa daily + Mangal-stotra Tuesday",
        },
    },
    "Mercury": {
        "for_areas": "skin, nervous, speech, lungs, intellect, anxiety",
        "practical": {
            "action":         "Screen-break 20-20-20 (every 20 min look 20 ft for 20 sec) + journaling 5 min/day + spirometry test if chest tight + dermatologist if skin",
            "why":            "Mercury rules nerves+lungs+skin — screen breaks fix 80% eye-strain; journaling cuts anxiety measurably (peer-reviewed); skin/lungs need real diagnosis, not mantra.",
            "time_to_result": "1 week (eye strain), 3 weeks (anxiety, journaling effect)",
            "kpi":            "Eye-strain rating < 3/10, anxiety scale (GAD-7) drop ≥ 4 pts in 3 wk",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Nadi shodhana pranayama 10 rounds + tongue scraping AM + green moong khichdi 1 meal/day",
            "herb":           "Brahmi for nerves + Mandukaparni (Gotu Kola) for skin + Vasaka for lungs",
            "dose":           "Brahmi ½ tsp morning, Vasaka as syrup if cough",
            "vaidya_caveat":  "All herbs need vaidya for prakriti-specific dose. Brahmi+Mandukaparni can sedate.",
            "time_to_result": "4-6 weeks",
        },
        "vedic": {
            "day":            "Wednesday",
            "mantra":         "Om Bum Budhaya Namah",
            "count":          "108",
            "donation":       "Green moong + green cloth + camphor at Vishnu temple Wednesday",
            "gemstone":       "Panna (Emerald) 4-6 ct, gold, little finger",
            "gem_caveat":     "TRIAL 3 days first. Natural Colombian/Zambian ₹10K-1L. Beryllium-treated cheaper but unstable.",
            "cost_inr_paid":  "10,000 – 1,00,000 (gemstone)",
            "free_alt":       "Vishnu Sahasranama path + amla daily",
        },
    },
    "Jupiter": {
        "for_areas": "liver, pancreas, fat metabolism, immunity, weight",
        "practical": {
            "action":         "Lipid + LFT (liver function) + HbA1c blood test in 7 days + walk 30 min daily + reduce sugar+maida 80% + sleep 7 hr",
            "why":            "Jupiter rules liver+sugar+fat — these labs catch fatty-liver/pre-diabetes years before symptoms. Diet+walking REVERSES early fatty-liver in 12 weeks. Mantra alone reverses none.",
            "time_to_result": "8 weeks (LFT, HbA1c reduction), 12 weeks (visible weight)",
            "kpi":            "HbA1c < 5.7, LDL < 100, ALT/AST < 35, weight drop 3-5 kg in 12 wk if overweight",
            "free":           True,
            "cost_inr":       1500,  # Lipid+LFT+HbA1c panel
        },
        "ayurvedic": {
            "practice":       "Bhastrika pranayama 5 min + bitter greens (karela, methi, neem) 4×/week + skip alcohol completely",
            "herb":           "Bhumi-Amla for liver + Triphala at night + Guggulu (Yograj/Kanchnar) for weight",
            "dose":           "Triphala 1 tsp warm water bedtime; Guggulu vaidya-prescribed",
            "vaidya_caveat":  "Guggulu strong — skip if hyperthyroid. LFT must be tracked.",
            "time_to_result": "8-12 weeks",
        },
        "vedic": {
            "day":            "Thursday",
            "mantra":         "Om Brim Brihaspataye Namah",
            "count":          "108",
            "donation":       "Chana dal + turmeric + yellow cloth Thursday at temple",
            "gemstone":       "Pukhraj (Yellow Sapphire) 4-6 ct, gold, index finger",
            "gem_caveat":     "Generally safe. Natural Sri Lankan ₹15K-1.5L. Heated treated cheaper. Get cert.",
            "cost_inr_paid":  "15,000 – 1,50,000 (gemstone)",
            "free_alt":       "Vishnu Sahasranama or Guru-stotra Thursday + turmeric milk at night",
        },
    },
    "Venus": {
        "for_areas": "kidneys, reproductive, hormones, eyes, throat, skin-glow",
        "practical": {
            "action":         "Hydration 2.5-3 L/day + thyroid + reproductive hormone panel (PCOD/testosterone) + reduce sugar + walk after dinner",
            "why":            "Venus rules hormones+kidneys — hormone tests catch PCOD/thyroid/low-T which mimic 'bad luck in love/career'. Hydration drops kidney stress measurably.",
            "time_to_result": "12 weeks (hormone normalization with diet+exercise)",
            "kpi":            "TSH 0.4-4, AMH age-appropriate, creatinine < 1.0, skin-glow self-rating ≥ 7/10",
            "free":           True,
            "cost_inr":       2500,
        },
        "ayurvedic": {
            "practice":       "Cow ghee 1 tsp/day + Sheetali pranayama + abhyanga (oil-massage) 2×/week + clean white clothes Friday",
            "herb":           "Shatavari (women) for hormones + Gokshura (men) for reproductive + Yashtimadhu for throat",
            "dose":           "Shatavari ½ tsp warm milk evening; vaidya for menopause/pregnancy",
            "vaidya_caveat":  "Shatavari + hormonal-IUD users: vaidya consult mandatory. Estrogen-sensitive cancer history: skip.",
            "time_to_result": "8-12 weeks",
        },
        "vedic": {
            "day":            "Friday",
            "mantra":         "Om Shum Shukraya Namah",
            "count":          "108",
            "donation":       "White sweets (kheer/barfi) + curd + white cloth to a girl Friday",
            "gemstone":       "Heera (Diamond) 0.5-1 ct OR Opal 4-6 ct, silver, middle finger",
            "gem_caveat":     "Opal TRIAL 3 days. Natural opal ₹5K-1L. Diamond — buy only with GIA cert.",
            "cost_inr_paid":  "5,000 – 5,00,000 (depending on stone)",
            "free_alt":       "Lakshmi-stotra Friday + cow ghee in food",
        },
    },
    "Saturn": {
        "for_areas": "joints, bones, chronic conditions, teeth, knees, longevity",
        "practical": {
            "action":         "Vit-D + B12 + RA factor blood test + weight-bearing exercise 30 min × 4/wk + dental check + posture correction (chair, screen height)",
            "why":            "Saturn rules joints+chronic — Vit-D/B12/RA labs catch osteoporosis/RA decades early; weight-bearing builds bone density; posture fixes 70% chronic neck/back. Sesame oil massage helps but doesn't replace these.",
            "time_to_result": "12 weeks (Vit-D, posture pain), 6 months (bone density)",
            "kpi":            "Vit-D > 30, B12 > 400, RA factor negative, no daily joint pain",
            "free":           True,
            "cost_inr":       1200,
        },
        "ayurvedic": {
            "practice":       "Mahanarayan oil massage 2×/week + Vata-pacifying diet (warm, oily, cooked) + serve elderly weekly",
            "herb":           "Ashwagandha for vitality + Shallaki (Boswellia) for joints + Hadjod for bone",
            "dose":           "Shallaki vaidya-prescribed; Ashwagandha 500mg-1g/day max",
            "vaidya_caveat":  "Ashwagandha can spike thyroid — skip if hyperthyroid. Pregnancy: avoid.",
            "time_to_result": "8-12 weeks",
        },
        "vedic": {
            "day":            "Saturday",
            "mantra":         "Om Sham Shanaishcharaya Namah",
            "count":          "108",
            "donation":       "Mustard oil + black urad + black cloth + iron at Shani temple Saturday",
            "gemstone":       "Neelam (Blue Sapphire) 4-6 ct, silver/panchdhatu, middle finger",
            "gem_caveat":     "STRICT 3-day TRIAL — 30% feel adverse (sleep loss, irritability) and must remove. Natural Kashmir blue ₹50K-50L. Heated Sri Lankan ₹10K-1L. Without astrologer + trial = DON'T buy.",
            "cost_inr_paid":  "10,000 – 50,00,000 (rare Kashmir)",
            "free_alt":       "Hanuman Chalisa Saturday + Shani-stotra + sesame-oil self-massage",
        },
    },
    "Rahu": {
        "for_areas": "anxiety, sudden ailments, skin allergies, addiction, mystery diagnoses",
        "practical": {
            "action":         "Allergy panel + Vit-D + thyroid + reduce phone screen 1 hr/day + therapy/counsellor if anxiety chronic + journaling",
            "why":            "Rahu = unknowns/anxiety — most 'mystery' issues are deficiencies (Vit-D/B12/iron) or anxiety. Therapy proven 4-8 wk for GAD. Allergy panel finds real triggers.",
            "time_to_result": "4 weeks (therapy effect), 8 weeks (lab-driven supplement effect)",
            "kpi":            "GAD-7 < 5, allergy triggers identified, Vit-D > 30",
            "free":           True,
            "cost_inr":       2000,  # allergy panel + supplements
        },
        "ayurvedic": {
            "practice":       "Bhramari + Sheetali pranayama + grounding walks barefoot on grass 10 min + reduce taamasic food (fried, leftover, alcohol)",
            "herb":           "Brahmi + Jatamansi for anxiety + Triphala for gut-brain axis",
            "dose":           "Brahmi morning, Jatamansi night (vaidya-fitted)",
            "vaidya_caveat":  "Standard cautions — Brahmi+Jatamansi can sedate.",
            "time_to_result": "6-8 weeks",
        },
        "vedic": {
            "day":            "Saturday (or Wednesday)",
            "mantra":         "Om Bhram Bhrim Bhraum Sah Rahave Namah",
            "count":          "108",
            "donation":       "Black urad + black cloth + coconut + radish Saturday",
            "gemstone":       "Gomed (Hessonite) 5-7 ct, silver, middle finger",
            "gem_caveat":     "TRIAL 3 days. Sri Lankan brownish-orange ₹3K-30K. Confused with citrine.",
            "cost_inr_paid":  "3,000 – 30,000",
            "free_alt":       "Durga Saptashati / Bhairav-stotra + keep silver coin under pillow",
        },
    },
    "Ketu": {
        "for_areas": "auto-immune, infections, mysterious/idiopathic, spine, eyes",
        "practical": {
            "action":         "ANA + thyroid antibody + B12 panel (auto-immune screen) + spine X-ray if back pain + meditation 10 min/day + qualified rheumatologist if labs flag",
            "why":            "Ketu = idiopathic/auto-immune — modern labs (ANA, anti-TPO) catch lupus/Hashimoto's etc that mantras NEVER fix. Meditation has measurable cortisol effect.",
            "time_to_result": "4-8 weeks (lab clarity + meditation effect)",
            "kpi":            "ANA negative or known + tracked, anti-TPO < 35, meditation streak > 21 days",
            "free":           True,
            "cost_inr":       1800,
        },
        "ayurvedic": {
            "practice":       "Pranayama + spiritual sadhana / silence 10 min + til (sesame) in diet + ghee massage on spine weekly",
            "herb":           "Ashwagandha + Guduchi for immunity + Shankhpushpi for nervous-system",
            "dose":           "Vaidya-prescribed for auto-immune (delicate)",
            "vaidya_caveat":  "Auto-immune cases — herbs can flare; ALWAYS pair with rheumatologist.",
            "time_to_result": "8-12 weeks",
        },
        "vedic": {
            "day":            "Tuesday (or Saturday)",
            "mantra":         "Om Sram Srim Sraum Sah Ketave Namah",
            "count":          "108",
            "donation":       "Sesame seeds + multi-coloured cloth + blanket Saturday",
            "gemstone":       "Lehsunia (Cat's Eye) 5-7 ct, silver, middle finger",
            "gem_caveat":     "TRIAL 3 days. Chrysoberyl natural ₹15K-2L. Many fakes — IGI cert mandatory.",
            "cost_inr_paid":  "15,000 – 2,00,000",
            "free_alt":       "Ganesh Atharvashirsha + til daan",
        },
    },
}


# ════════════════════════════════════════════════════════════════════════
# MARRIAGE — 9 planets × 3 tiers
# Focus: relationship readiness, partner-search, marital harmony
# ════════════════════════════════════════════════════════════════════════
_MARRIAGE: Dict[str, Dict[str, Any]] = {
    "Venus": {
        "for_areas": "love-attraction, partner-quality, marital harmony",
        "practical": {
            "action":         "Update profiles (matrimony/social) with REAL recent photos + write 100-word self-honest bio + decide 5 non-negotiables in writing + meet 4 new people/month (event, hobby class, intro-via-friend)",
            "why":            "Venus = attraction. Engine timing only opens DOOR — practical reach (4 introductions/month vs 0) statistically multiplies match probability 8x. Writing non-negotiables prevents wrong choices in haste.",
            "time_to_result": "8-12 weeks (1-2 serious conversations)",
            "kpi":            "≥ 4 new introductions/month, profile updated, non-negotiables list written, 1 second-date",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Cow ghee in food + abhyanga 2×/week + rose-water on face + soft white/cream clothes Friday",
            "herb":           "Shatavari (women) / Gokshura (men) for hormonal balance",
            "dose":           "½ tsp warm milk evening (vaidya-fitted)",
            "vaidya_caveat":  "Standard — pregnancy/hormonal disorder vaidya consult.",
            "time_to_result": "6-8 weeks (skin glow, confidence)",
        },
        "vedic": {
            "day":            "Friday",
            "mantra":         "Om Shum Shukraya Namah  AND  Om Kleem Kamadevaya Namah (108 each)",
            "count":          "108",
            "donation":       "White sweets + curd + white cloth to an unmarried girl Friday",
            "gemstone":       "Heera (Diamond) 0.5-1 ct OR Opal 4-6 ct, silver, middle finger",
            "gem_caveat":     "Opal trial 3 days. Diamond GIA cert mandatory.",
            "cost_inr_paid":  "5,000 – 5,00,000",
            "free_alt":       "Lakshmi-stotra Friday + visit Krishna/Radha temple weekly",
        },
    },
    "Jupiter": {
        "for_areas": "groom-quality (women), wisdom partner, in-laws, dharma alignment",
        "practical": {
            "action":         "Define values match (faith, family, finance) BEFORE meeting + ask discriminating Qs by date 3 (kids/career/parents) + family meet by date 6",
            "why":            "Jupiter = wisdom + values. Most marriages fail on UNSPOKEN value mismatch. Asking by D3 saves 6 months of confusion. Engine can't make good groom appear if you don't filter.",
            "time_to_result": "12 weeks (clear shortlist)",
            "kpi":            "Value-match scoring done for 3 prospects, family-meet for 1+",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Vishnu Sahasranama + turmeric milk at night + chana-jaggery-sprouts in diet",
            "herb":           "Triphala + Ashwagandha for vitality",
            "dose":           "Standard",
            "vaidya_caveat":  "—",
            "time_to_result": "6 weeks (vitality)",
        },
        "vedic": {
            "day":            "Thursday",
            "mantra":         "Om Brim Brihaspataye Namah  AND  Om Gam Ganapataye Namah",
            "count":          "108",
            "donation":       "Chana dal + turmeric + yellow cloth + banana to a brahmin/teacher Thursday",
            "gemstone":       "Pukhraj (Yellow Sapphire) 4-6 ct, gold, index finger — TRADITIONALLY recommended for women seeking marriage",
            "gem_caveat":     "Generally safe. Natural Sri Lankan ₹15K-1.5L.",
            "cost_inr_paid":  "15,000 – 1,50,000",
            "free_alt":       "Thursday vrat (banana fast) + Vishnu temple weekly",
        },
    },
    "Mars": {
        "for_areas": "Mangal Dosh, marriage-energy, partner-aggression",
        "practical": {
            "action":         "Couples-counsellor session BEFORE marriage if both serious + temper-management book/course if quick anger + transparent about Mangal status with prospect (DON'T hide)",
            "why":            "Mangal Dosh statistical impact is OVERSTATED in popular astrology — 60-70% Indian women have it. Real predictor of marital trouble is communication/temper, NOT Mars. Counsellor 2 sessions catches 80% incompatibilities.",
            "time_to_result": "Immediate (transparency); 4 wk (temper drills)",
            "kpi":            "1 couple-counsellor session done OR 1 temper-mgmt course completed",
            "free":           True,
            "cost_inr":       3000,  # 1-2 counselor sessions
        },
        "ayurvedic": {
            "practice":       "Sheetali pranayama 10 rounds + cooling diet (ghee, mint, cucumber, coconut water) + skip red meat & green chilli Tuesday",
            "herb":           "Manjistha + Brahmi for cooling",
            "dose":           "Standard",
            "vaidya_caveat":  "—",
            "time_to_result": "4-6 weeks",
        },
        "vedic": {
            "day":            "Tuesday",
            "mantra":         "Om Ang Angarakaya Namah  AND  Hanuman Chalisa daily",
            "count":          "108",
            "donation":       "Red lentils + red cloth + jaggery Tuesday",
            "gemstone":       "Moonga (Red Coral) — but TRIAL first, can spike anger",
            "gem_caveat":     "Mangal Dosh classical remedies: Mangal Dosh Nivaran Puja (if both partners genuinely concerned). Cost ₹2K-25K — choose verified pandit.",
            "cost_inr_paid":  "2,000 – 25,000 (puja) | 5K-30K (coral)",
            "free_alt":       "Hanuman Chalisa Tuesday + visit Hanuman temple",
        },
    },
    "Moon": {
        "for_areas": "emotional connection, mother/family approval, intuition in choice",
        "practical": {
            "action":         "Sleep + mood baseline FIXED first (Moon-care basics) + don't make marriage decision in low-mood phase + journal 'what would I want my partner to know' 5 min/wk",
            "why":            "Moon = mind. Decisions made in unstable mood-state have 3x higher regret rate (psych research). Stabilize first, choose later.",
            "time_to_result": "3-4 weeks (mood baseline)",
            "kpi":            "Sleep > 6.5 hr × 21 days, journal kept ≥ 4 wk",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Bhramari pranayama at night + warm milk with nutmeg + Brahmi/Jatamansi if anxious",
            "herb":           "Brahmi + Shankhpushpi",
            "dose":           "Standard, vaidya for pregnancy",
            "vaidya_caveat":  "Same as health.Moon",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Monday",
            "mantra":         "Om Som Somaya Namah",
            "count":          "108",
            "donation":       "Milk + white rice + white cloth Monday",
            "gemstone":       "Moti (Pearl) 4-6 ct, silver, ring finger",
            "gem_caveat":     "Standard pearl quality check (loupe).",
            "cost_inr_paid":  "3,000 – 50,000",
            "free_alt":       "Monday vrat (one-meal) + Shiva temple",
        },
    },
    "Saturn": {
        "for_areas": "marriage delay, age-gap concerns, late-but-stable matches, in-law duty",
        "practical": {
            "action":         "Accept the delay productively — invest delay-years in (a) financial corpus 6-12 mo emergency fund, (b) skill upgrade, (c) sharper non-negotiables list. Saturn-delayed marriages historically more stable BECAUSE of better self-knowledge.",
            "why":            "Saturn delay is real but the OUTCOME post-delay is statistically BETTER than rushed Mars-Venus matches. Use the time. Don't panic-marry.",
            "time_to_result": "12-24 months (corpus + skill); marriage when chart opens",
            "kpi":            "6-mo emergency fund saved, 1 new skill certified, non-negotiables sharpened",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Mahanarayan oil massage + Vata-pacifying diet + serve elderly weekly",
            "herb":           "Ashwagandha 500mg/day for vitality",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6-8 weeks",
        },
        "vedic": {
            "day":            "Saturday",
            "mantra":         "Om Sham Shanaishcharaya Namah",
            "count":          "108",
            "donation":       "Mustard oil + black urad + black cloth + iron Shani temple",
            "gemstone":       "Neelam (Blue Sapphire) — STRICT trial — only if astrologer confirms benefic",
            "gem_caveat":     "30% adverse rate. Free alternatives strongly preferred.",
            "cost_inr_paid":  "10,000 – 50,00,000",
            "free_alt":       "Saturday Hanuman Chalisa + serve elderly weekly + Shani-stotra",
        },
    },
    "Sun": {
        "for_areas": "ego balance, father/family approval, public-image of partner",
        "practical": {
            "action":         "Father-conversation 1×/month if his approval matters + work on public-self confidence (1 social-skill book OR Toastmasters) + accept partner's ego-needs respectfully",
            "why":            "Sun = ego/father. 40% Indian marriage breakdowns trace to in-law/parent conflict. Direct conversation > silent assumption.",
            "time_to_result": "8 weeks",
            "kpi":            "Monthly call with father logged, 1 confidence-skill course done",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Surya namaskar 12 rounds + Aditya Hridaya Stotra Sunday",
            "herb":           "Amla daily",
            "dose":           "Standard",
            "vaidya_caveat":  "—",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Sunday",
            "mantra":         "Om Hraam Hreem Hraum Sah Suryaya Namah",
            "count":          "108",
            "donation":       "Wheat + jaggery Sunday",
            "gemstone":       "Manik (Ruby) — astrologer-fitted",
            "gem_caveat":     "Standard ruby caveats.",
            "cost_inr_paid":  "15,000 – 2,00,000",
            "free_alt":       "Tulsi-jal arpan to Sun + Aditya Hridaya Stotra",
        },
    },
    "Mercury": {
        "for_areas": "communication, intellectual compatibility, friendship-base",
        "practical": {
            "action":         "Communication-skill book (e.g. Crucial Conversations) + practice 'I-statements' instead of 'You always' + weekly 30-min uninterrupted talk with prospect/partner",
            "why":            "Mercury = communication. 70% of marital fights are bad-communication, not bad-people. Skill is learnable.",
            "time_to_result": "6 weeks",
            "kpi":            "1 book read, weekly talk-slot kept × 6 wk",
            "free":           True,
            "cost_inr":       400,  # 1 book
        },
        "ayurvedic": {
            "practice":       "Nadi shodhana + green moong khichdi 1 meal",
            "herb":           "Brahmi",
            "dose":           "½ tsp morning",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Wednesday",
            "mantra":         "Om Bum Budhaya Namah",
            "count":          "108",
            "donation":       "Green moong + green cloth Wednesday",
            "gemstone":       "Panna (Emerald) — trial",
            "gem_caveat":     "Standard emerald.",
            "cost_inr_paid":  "10,000 – 1,00,000",
            "free_alt":       "Vishnu Sahasranama + amla daily",
        },
    },
    "Rahu": {
        "for_areas": "unconventional matches, inter-caste/foreign, sudden engagement",
        "practical": {
            "action":         "Verify identity HEAVILY (background, social, in-person family meet) + slow down impulsive engagement decisions + 90-day cooling-off rule for online-only relationships before commit",
            "why":            "Rahu = sudden + illusion. Online-romance fraud at all-time high in India. 90-day rule cuts risk 75%. Verify > trust.",
            "time_to_result": "Immediate risk-cut",
            "kpi":            "Background-check done, family meet done, 90-day rule observed",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Bhramari + grounding walks barefoot grass",
            "herb":           "Brahmi + Jatamansi",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Saturday",
            "mantra":         "Om Bhram Bhrim Bhraum Sah Rahave Namah",
            "count":          "108",
            "donation":       "Black urad + coconut Saturday",
            "gemstone":       "Gomed — trial",
            "gem_caveat":     "Standard hessonite.",
            "cost_inr_paid":  "3,000 – 30,000",
            "free_alt":       "Durga Saptashati path",
        },
    },
    "Ketu": {
        "for_areas": "spiritual partner, past-life karma, second-marriage healing",
        "practical": {
            "action":         "If second marriage / past trauma: 4-8 sessions trauma-informed therapy BEFORE re-marrying; 6-month healing minimum after divorce; spiritual partner search → check action-aligned values not just words",
            "why":            "Ketu = past-karma + detachment. Therapy after divorce statistically halves re-marriage breakdown. Skipping it perpetuates pattern.",
            "time_to_result": "8 weeks (therapy effect)",
            "kpi":            "≥ 4 therapy sessions, 6-mo healing window respected",
            "free":           True,
            "cost_inr":       8000,  # 4 sessions
        },
        "ayurvedic": {
            "practice":       "Meditation + til + ghee on spine",
            "herb":           "Ashwagandha + Shankhpushpi",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "8 weeks",
        },
        "vedic": {
            "day":            "Tuesday",
            "mantra":         "Om Sram Srim Sraum Sah Ketave Namah",
            "count":          "108",
            "donation":       "Sesame + multi-color cloth Saturday",
            "gemstone":       "Lehsunia — trial",
            "gem_caveat":     "Standard cat's eye.",
            "cost_inr_paid":  "15,000 – 2,00,000",
            "free_alt":       "Ganesh Atharvashirsha + til daan",
        },
    },
}


# ════════════════════════════════════════════════════════════════════════
# CAREER — 9 planets × 3 tiers
# Focus: job-search, promotion, business, skill, role-fit
# ════════════════════════════════════════════════════════════════════════
_CAREER: Dict[str, Dict[str, Any]] = {
    "Sun": {
        "for_areas": "leadership, government, authority, visibility, promotion",
        "practical": {
            "action":         "Updated CV + LinkedIn + 5-line elevator pitch + apply to 8 roles/week + ask manager DIRECTLY 'what's needed for promotion' in 1:1",
            "why":            "Sun = visibility. 'Direct ask' to manager moves promotion 6-12 mo faster (HR data). 8 apps/wk vs 1 statistically yields offer 6x faster.",
            "time_to_result": "8-12 weeks (first interview), 6 mo (promotion talk)",
            "kpi":            "8 applications/wk × 6 wk, 1 manager 1:1 with explicit ask",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Surya namaskar + Aditya Hridaya Stotra Sunday + amla",
            "herb":           "Amla + Brahmi for confidence",
            "dose":           "Standard",
            "vaidya_caveat":  "—",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Sunday",
            "mantra":         "Om Hraam Hreem Hraum Sah Suryaya Namah",
            "count":          "108",
            "donation":       "Wheat + jaggery + copper item Sunday",
            "gemstone":       "Manik (Ruby) — astrologer-fitted",
            "gem_caveat":     "Standard ruby.",
            "cost_inr_paid":  "15,000 – 2,00,000",
            "free_alt":       "Aditya Hridaya Stotra Sunday + Tulsi-jal to Sun",
        },
    },
    "Saturn": {
        "for_areas": "long-grind careers, service, justice, labour, persistence",
        "practical": {
            "action":         "Skill-deepening (Saturn rewards depth, not breadth) — pick ONE skill, 200 hours focused practice. Avoid job-hopping under Saturn — stay 18+ mo unless toxic. Build 12-mo emergency fund.",
            "why":            "Saturn = mastery via time. Job-hoppers under Saturn dasha penalized in resume gaps; stayers compound. 200 hr (Cal Newport rule) of deep work is the floor for promotion-grade skill.",
            "time_to_result": "6-12 months (visible skill jump)",
            "kpi":            "200 hr logged on 1 skill, 18-mo job-tenure milestone, 12-mo fund saved",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Mahanarayan oil massage + Vata diet + serve elderly",
            "herb":           "Ashwagandha 500mg + Brahmi for focus",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks (focus, energy)",
        },
        "vedic": {
            "day":            "Saturday",
            "mantra":         "Om Sham Shanaishcharaya Namah",
            "count":          "108",
            "donation":       "Mustard oil + black urad Saturday",
            "gemstone":       "Neelam — STRICT trial only",
            "gem_caveat":     "Free alternatives strongly preferred for career.",
            "cost_inr_paid":  "10,000 – 50,00,000",
            "free_alt":       "Saturday Hanuman Chalisa + serve elderly + Shani-stotra",
        },
    },
    "Mercury": {
        "for_areas": "IT, communication, sales, writing, accounts, analysis",
        "practical": {
            "action":         "1 cert/quarter (AWS/PMP/data/copy) + 1 portfolio piece public/quarter + reach out to 5 strangers on LinkedIn/wk for advice (cold-DM 100-word) — networking compounds",
            "why":            "Mercury = info exchange + cert/portfolio = direct hireability proof. 'Cold DM 100' rule generates 5-10 warm intros / 100 messages — measured.",
            "time_to_result": "12 weeks (visible portfolio + 1 cert)",
            "kpi":            "1 cert done, 1 portfolio piece live, 60 DMs sent in qtr",
            "free":           True,
            "cost_inr":       8000,  # 1 cert
        },
        "ayurvedic": {
            "practice":       "Nadi shodhana + green moong + tongue scraping",
            "herb":           "Brahmi + Mandukaparni for focus",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Wednesday",
            "mantra":         "Om Bum Budhaya Namah",
            "count":          "108",
            "donation":       "Green moong + green cloth + camphor at Vishnu temple Wednesday",
            "gemstone":       "Panna (Emerald) — trial",
            "gem_caveat":     "Standard emerald.",
            "cost_inr_paid":  "10,000 – 1,00,000",
            "free_alt":       "Vishnu Sahasranama Wednesday + amla daily",
        },
    },
    "Jupiter": {
        "for_areas": "teaching, finance, law, advisory, dharma-aligned roles",
        "practical": {
            "action":         "Find a real mentor (DM 5/wk till 1 says yes) + read 1 domain-classic/quarter + take on 1 mentee yourself (teaching = 2x retention) + ethical-finance habit (10% save+invest auto-debit)",
            "why":            "Jupiter = guru + dharma. Mentorship measurably accelerates career 2-3 yr. Teaching others compounds your own depth. Finance discipline gives RUNWAY for right opportunity (vs panic-take wrong role).",
            "time_to_result": "6 months (mentor + classic), 12 mo (financial cushion)",
            "kpi":            "1 mentor monthly call, 4 classics read in year, 10% auto-save active",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Bhastrika pranayama + bitter greens + skip alcohol",
            "herb":           "Triphala + Bhumi-Amla for liver clarity",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "8 weeks",
        },
        "vedic": {
            "day":            "Thursday",
            "mantra":         "Om Brim Brihaspataye Namah",
            "count":          "108",
            "donation":       "Chana dal + turmeric + yellow cloth + banana to teacher Thursday",
            "gemstone":       "Pukhraj (Yellow Sapphire) — generally safe, get cert",
            "gem_caveat":     "Standard pukhraj.",
            "cost_inr_paid":  "15,000 – 1,50,000",
            "free_alt":       "Thursday Vishnu Sahasranama + visit a teacher/guru weekly",
        },
    },
    "Mars": {
        "for_areas": "engineering, military, sports, sales-target, surgery, real-estate",
        "practical": {
            "action":         "Set 1 hard quarterly target (number-based) + daily morning 5-min planning + 30-min cardio 4×/wk + transparent peer-competition (state your goal publicly to 3 people for accountability)",
            "why":            "Mars = drive. Number-based targets (e.g. '20% revenue', 'Sub-3 marathon') compound; vague goals fail. Public commitment doubles follow-through (psych).",
            "time_to_result": "12 weeks (1 target met)",
            "kpi":            "1 quarterly number-target hit, 4 cardio sessions/wk × 12 wk",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Sheetali pranayama + cooling diet + skip Tuesday red-meat",
            "herb":           "Manjistha + Brahmi (anger-calming)",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Tuesday",
            "mantra":         "Om Ang Angarakaya Namah",
            "count":          "108",
            "donation":       "Red lentils + jaggery Tuesday",
            "gemstone":       "Moonga (Coral) — trial 3 days",
            "gem_caveat":     "Standard coral.",
            "cost_inr_paid":  "5,000 – 30,000",
            "free_alt":       "Hanuman Chalisa Tuesday",
        },
    },
    "Venus": {
        "for_areas": "creative, design, hospitality, beauty, luxury, fashion, arts",
        "practical": {
            "action":         "Build a public portfolio (Behance/Insta/website) + 1 paid client/quarter (even tiny) + invest 5% revenue into craft tools + style/grooming budget IS career-investment in these fields",
            "why":            "Venus = aesthetic + value. Visible portfolio + 1 paid client beats 'still learning' claim 10x to recruiters. In creative fields presentation IS the product.",
            "time_to_result": "12 weeks (portfolio + 1 paid)",
            "kpi":            "Portfolio live, 1 paid project done, 5% craft-tool reinvest",
            "free":           True,
            "cost_inr":       3000,  # tools / website
        },
        "ayurvedic": {
            "practice":       "Cow ghee + abhyanga + rose-water + clean Friday clothes",
            "herb":           "Shatavari/Gokshura per gender",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks (skin-glow, energy)",
        },
        "vedic": {
            "day":            "Friday",
            "mantra":         "Om Shum Shukraya Namah",
            "count":          "108",
            "donation":       "White sweets + curd Friday",
            "gemstone":       "Heera/Opal — trial",
            "gem_caveat":     "Standard.",
            "cost_inr_paid":  "5,000 – 5,00,000",
            "free_alt":       "Lakshmi-stotra Friday",
        },
    },
    "Moon": {
        "for_areas": "people-roles (HR, hospitality, healthcare, public-facing), market-emotion (trading, journalism)",
        "practical": {
            "action":         "Sleep + mood baseline FIRST (Moon-care basics) + emotional-intelligence skill (1 EI book + practice naming-emotions journal) + don't make career switch in low-mood phase",
            "why":            "Moon = emotion. People-roles need stable mood baseline. EI score predicts 58% of job performance in service roles (Goleman).",
            "time_to_result": "4 weeks (mood), 8 wk (EI)",
            "kpi":            "Sleep > 6.5 hr × 21 d, 1 EI book read, journal kept 6 wk",
            "free":           True,
            "cost_inr":       400,
        },
        "ayurvedic": {
            "practice":       "Bhramari + warm milk + Brahmi/Jatamansi if anxious",
            "herb":           "Brahmi + Jatamansi",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Monday",
            "mantra":         "Om Som Somaya Namah",
            "count":          "108",
            "donation":       "Milk + white rice Monday",
            "gemstone":       "Moti (Pearl)",
            "gem_caveat":     "Standard",
            "cost_inr_paid":  "3,000 – 50,000",
            "free_alt":       "Monday Shiva temple + Chandra namaskar",
        },
    },
    "Rahu": {
        "for_areas": "tech, foreign, novel/unconventional, viral/influencer, crypto, gambling-domains",
        "practical": {
            "action":         "Go where the FUTURE is (1 emerging tech: AI/ML/blockchain/biotech — 100 hr learning) + foreign market exposure + AVOID get-rich-quick schemes (Rahu's trap) + verify every offer 2× before commit",
            "why":            "Rahu = unconventional + sudden. Genuine Rahu success comes from EARLY adoption of REAL emerging field, not gambling. 100 hr in AI/ML in 2026 = 5-yr career multiplier. Get-rich schemes = life-savings loss.",
            "time_to_result": "6 months (skill + offer)",
            "kpi":            "100 hr logged on emerging tech, 0 get-rich schemes joined",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Bhramari + grounding walks + reduce screen 1 hr",
            "herb":           "Brahmi + Jatamansi",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "6 weeks",
        },
        "vedic": {
            "day":            "Saturday",
            "mantra":         "Om Bhram Bhrim Bhraum Sah Rahave Namah",
            "count":          "108",
            "donation":       "Black urad + coconut Saturday",
            "gemstone":       "Gomed — trial",
            "gem_caveat":     "Standard hessonite.",
            "cost_inr_paid":  "3,000 – 30,000",
            "free_alt":       "Durga Saptashati Saturday",
        },
    },
    "Ketu": {
        "for_areas": "research, spiritual, occult, niche-specialist, code-deep-work, isolated-mastery",
        "practical": {
            "action":         "Pick a NICHE (Ketu rewards depth) + 1000-hour rule on it + minimal social-media + do work that doesn't need recognition (will arrive late but compound)",
            "why":            "Ketu = detachment + mastery. Niche specialists out-earn generalists 2-5x in long-tail (Pareto). Less social-media = more deep work. Recognition lag is real but compensates.",
            "time_to_result": "12-24 months (visible niche authority)",
            "kpi":            "1 niche chosen, 250 hr logged in qtr, social-media usage < 30 min/day",
            "free":           True,
            "cost_inr":       0,
        },
        "ayurvedic": {
            "practice":       "Meditation 10 min + til + ghee spine massage",
            "herb":           "Ashwagandha + Shankhpushpi",
            "dose":           "Standard",
            "vaidya_caveat":  "Standard",
            "time_to_result": "8 weeks",
        },
        "vedic": {
            "day":            "Tuesday",
            "mantra":         "Om Sram Srim Sraum Sah Ketave Namah",
            "count":          "108",
            "donation":       "Sesame + multi-color cloth Saturday",
            "gemstone":       "Lehsunia — trial",
            "gem_caveat":     "Standard.",
            "cost_inr_paid":  "15,000 – 2,00,000",
            "free_alt":       "Ganesh Atharvashirsha + til daan",
        },
    },
}


CATALOG: Dict[str, Dict[str, Dict[str, Any]]] = {
    "health":   _HEALTH,
    "marriage": _MARRIAGE,
    "career":   _CAREER,
}


# ─── System / Area daily-practice tables (tier-1.5 — daily habits keyed
# by affected_systems / life-areas, NOT by planet) ─────────────────────

SYSTEM_PRACTICES: Dict[str, Dict[str, str]] = {
    # health systems (mirror health_engine `_affected_systems()` tags)
    "heart":         {"practice": "Anulom-vilom 10 min + walk 30 min + reduce salt + 1 fruit/day"},
    "eyes":          {"practice": "Trataka 5 min + 20-20-20 screen rule + triphala-water eye-wash"},
    "vitality":      {"practice": "Surya namaskar + ashwagandha (vaidya) + 7-8 hr sleep"},
    "bones":         {"practice": "Calcium-rich (sesame, ragi) + 15 min sun + weight-bearing"},
    "mind":          {"practice": "Bhramari 10 rounds + 10-min meditation + reduce caffeine"},
    "sleep":         {"practice": "Brahmi/jatamansi (vaidya) + screen-off 1 hr pre-bed + warm milk"},
    "fluids":        {"practice": "2-3 L water + jeera-saunf-ajwain water + reduce cold drinks"},
    "digestion":     {"practice": "Triphala bedtime + ginger pre-meals + eat sitting slowly"},
    "blood":         {"practice": "Anar/beetroot juice + tulsi water + iron-rich greens"},
    "muscles":       {"practice": "Light yoga + ashwagandha + sesame oil massage 2x/wk"},
    "inflammation":  {"practice": "Turmeric-pepper-water + omega-3 (flax/walnut) + reduce sugar+maida"},
    "accident_risk": {"practice": "Hanuman Chalisa + Mahamrityunjaya 11x + extra mindfulness driving"},
    "liver":         {"practice": "Bhastrika pranayama + bitter greens + skip alcohol"},
    "skin":          {"practice": "Neem-tulsi water bath + amla daily + reduce night-out fried"},
    "nervous":       {"practice": "Brahmi + abhyanga 2x/wk + nadi shodhana"},
    "kidneys":       {"practice": "Hydration + reduce salt + coriander seed water"},
    "reproductive":  {"practice": "Shatavari/Gokshura (vaidya) + pelvic yoga"},
    "joints":        {"practice": "Vata-pacifying diet + Mahanarayan oil massage"},
    "chronic":       {"practice": "Same daily dincharya + Mahamrityunjaya jaap; no shortcuts"},
    "anxiety":       {"practice": "Bhramari + Sheetali + grounding walks barefoot grass"},
    "auto-immune":   {"practice": "Anti-inflammatory diet + stress mgmt + qualified physician"},
    # marriage / relationship areas
    "communication": {"practice": "I-statements + weekly 30-min uninterrupted talk + 1 EI book"},
    "harmony":       {"practice": "Joint Friday meal + 1 weekly walk together + Lakshmi-stotra"},
    "in-laws":       {"practice": "Monthly call + 1 family meet/qtr + boundaries-with-respect script"},
    "trust":         {"practice": "100-day no-secret-sharing rule with partner + transparent finances"},
    # career areas
    "leadership":    {"practice": "Daily 5-min planning + monthly skip-level chat + 1 mentee"},
    "skill_depth":   {"practice": "200-hr deep-work block + 1 cert/qtr + portfolio piece public"},
    "networking":    {"practice": "5 cold-DMs/wk + 1 coffee-chat/wk + LinkedIn weekly post"},
    "stability":     {"practice": "12-mo emergency fund + 18-mo tenure + 10% auto-invest"},
}
