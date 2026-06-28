"""Litigation / court-case remedy catalog — 9 grahas × 3 tiers.

Practical = real legal action (lawyer, documents, court discipline).
Ayurvedic = stress/calm/body support during long cases (vaidya disclaimer).
Vedic = BPHS / Phaladeepika / Lal-Kitab consensus mantras + daan + gems.
"""
from __future__ import annotations

from typing import Any, Dict

_LITIGATION: Dict[str, Dict[str, Any]] = {
    "Mars": {
        "for_areas": "conflict, police, fight, anger, criminal friction, 6H litigation",
        "practical": {
            "action": (
                "Consult a qualified criminal/civil lawyer within 7 days + build a dated case diary "
                "(who said/did what, when) + zero social-media posts about the case + no heated "
                "arguments with opponent/police without lawyer present"
            ),
            "why": "Mars rules conflict/court-fight — uncontrolled anger and unsigned statements destroy cases faster than weak planets.",
            "time_to_result": "1-2 weeks (clarity + lawyer strategy), 6-12 weeks (case posture)",
            "kpi": "Lawyer retained, case diary started, 0 impulsive statements to police/opponent in 21 days",
            "free": True,
            "cost_inr": 5000,
        },
        "ayurvedic": {
            "practice": "Sheetali + Bhramari 10 rounds daily + cooling diet on Tuesday (avoid excess chilli/alcohol)",
            "herb": "Brahmi ½ tsp morning + Ashwagandha if sleep poor (vaidya dose)",
            "dose": "Brahmi 1× AM; Ashwagandha evening if prescribed",
            "vaidya_caveat": "Ashwagandha can sedate — skip if on sedatives. Anger spikes: vaidya for pitta balance.",
            "time_to_result": "3-4 weeks (sleep, anger control)",
        },
        "vedic": {
            "day": "Tuesday",
            "mantra": "Om Ang Angarakaya Namah",
            "count": "108",
            "donation": "Red lentils (masoor) + jaggery + red cloth Tuesday; feed poor on Tuesday",
            "gemstone": "Moonga (Red Coral) 5-7 ct, copper, ring finger",
            "gem_caveat": "TRIAL 3 days — coral can spike anger in some charts. Prefer Hanuman path first in active criminal cases.",
            "cost_inr_paid": "5,000 – 30,000 (gemstone) | 0-300 (donation)",
            "free_alt": "Hanuman Chalisa daily + Mangal-stotra Tuesday + avoid red meat Tuesday",
        },
    },
    "Saturn": {
        "for_areas": "delay, judgment, long trial, patience, 8H shock, structured defence",
        "practical": {
            "action": (
                "Never miss a hearing — calendar every date + reach court 30 min early + monthly written "
                "follow-up with advocate + accept that Saturn cases need structured patience, not shortcuts"
            ),
            "why": "Saturn governs delay and judgment — missed dates and impatient moves hurt more than weak yog.",
            "time_to_result": "4-8 weeks (process discipline), months (Saturn cases)",
            "kpi": "0 missed hearings in 90 days, 1 written advocate update/month, hearing log maintained",
            "free": True,
            "cost_inr": 0,
        },
        "ayurvedic": {
            "practice": "Warm sesame-oil foot massage Saturday evening + slow walks + serve elderly if safe",
            "herb": "Ashwagandha + Dashmool kwath (vaidya) for chronic stress",
            "dose": "Vaidya-specific — Saturn stress needs grounding herbs, not stimulants",
            "vaidya_caveat": "Dashmool needs vaidya if BP/diabetes. No self-dosing long term.",
            "time_to_result": "6-8 weeks (sleep, patience)",
        },
        "vedic": {
            "day": "Saturday",
            "mantra": "Om Sham Shanaishcharaya Namah",
            "count": "108",
            "donation": "Mustard oil + black urad + iron item to needy on Saturday",
            "gemstone": "Neelam (Blue Sapphire) 5-7 ct, silver, middle finger",
            "gem_caveat": "STRICT 3-day trial ONLY. Many street neelam are synthetic. Free Shani stotra often safer in active litigation.",
            "cost_inr_paid": "10,000 – 5,00,000 (gemstone) | 0-500 (donation)",
            "free_alt": "Shani stotra Saturday + mustard-oil lamp at peepal + serve disabled/elderly",
        },
    },
    "Rahu": {
        "for_areas": "FIR complexity, false implication fear, police, foreign legal, confusion",
        "practical": {
            "action": (
                "Never sign blank papers + verify every FIR/police page copy + second legal opinion before "
                "major compromise + keep all WhatsApp/SMS/email evidence exported weekly"
            ),
            "why": "Rahu adds complexity and trap-documents — documentation discipline beats panic.",
            "time_to_result": "1-2 weeks (paper trail), 4-8 weeks (legal clarity)",
            "kpi": "Full FIR/case paper set copied, 0 blank signatures, evidence folder with dates",
            "free": True,
            "cost_inr": 2000,
        },
        "ayurvedic": {
            "practice": "Grounding walks barefoot on grass 10 min + reduce late-night scrolling + fixed sleep window",
            "herb": "Jatamansi for anxiety + Tagara only if vaidya approves",
            "dose": "Jatamansi evening; Tagara vaidya-only",
            "vaidya_caveat": "Tagara sedating — never mix with alcohol or driving day.",
            "time_to_result": "3-4 weeks (sleep, rumination)",
        },
        "vedic": {
            "day": "Saturday",
            "mantra": "Om Bhram Bhram Rahave Namah",
            "count": "108",
            "donation": "Coconut + blue/black cloth + sesame at temple Saturday",
            "gemstone": "Gomed (Hessonite) 6-8 ct — trial only",
            "gem_caveat": "Rahu gems controversial in active criminal matters — prefer mantra/daan first.",
            "cost_inr_paid": "5,000 – 80,000 (gemstone)",
            "free_alt": "Durga Chalisa + Rahu stotra Saturday + feed birds with sesame",
        },
    },
    "Mercury": {
        "for_areas": "documents, arguments, petitions, bail papers, contracts, vakil strategy",
        "practical": {
            "action": (
                "Organize all case papers chronologically + written communication only via lawyer + "
                "prepare a 1-page fact summary for advocate before every hearing + learn exact charge/section numbers"
            ),
            "why": "Mercury wins litigation on paper — sloppy documents lose winnable cases.",
            "time_to_result": "1 week (organization), 4 weeks (stronger petitions)",
            "kpi": "Dated evidence folder, 1-page brief before each hearing, 0 verbal-only deals",
            "free": True,
            "cost_inr": 500,
        },
        "ayurvedic": {
            "practice": "Nadi shodhana 10 rounds + tongue scraping AM + reduce excess screen before sleep",
            "herb": "Brahmi + Mandukaparni for focus under cross-examination stress",
            "dose": "½ tsp Brahmi morning",
            "vaidya_caveat": "Brahmi lowers BP slightly — monitor if hypotensive.",
            "time_to_result": "4 weeks (focus, clarity)",
        },
        "vedic": {
            "day": "Wednesday",
            "mantra": "Om Bum Budhaya Namah",
            "count": "108",
            "donation": "Green moong + green cloth + books/stationery to needy student Wednesday",
            "gemstone": "Panna (Emerald) 4-6 ct, gold, little finger",
            "gem_caveat": "TRIAL 3 days. Prefer Vishnu Sahasranama + donation if case is criminal-active.",
            "cost_inr_paid": "10,000 – 1,00,000 (gemstone)",
            "free_alt": "Vishnu Sahasranama Wednesday + green moong daan + amla daily",
        },
    },
    "Jupiter": {
        "for_areas": "relief, bail protection, acquittal tone, wise counsel, dharma in dispute",
        "practical": {
            "action": (
                "Seek a senior/reputed advocate referral (Bar Council verified) + full honest disclosure to "
                "lawyer (hidden facts always surface) + explore lawful mediation if civil/family matter"
            ),
            "why": "Jupiter = protection through wise counsel and ethical strategy — hiding facts blocks relief.",
            "time_to_result": "2-4 weeks (better counsel), 8-12 weeks (relief window)",
            "kpi": "Advocate credentials verified, full fact disclosure done, 1 mediation attempt if civil",
            "free": True,
            "cost_inr": 0,
        },
        "ayurvedic": {
            "practice": "Morning gratitude 5 min + sattvic lunch + avoid intoxicants during case stress",
            "herb": "Tulsi + Yashtimadhu tea for throat/calm before court (not medical claim)",
            "dose": "Tulsi 2-3 leaves daily",
            "vaidya_caveat": "Yashtimadhu raises BP if overused — vaidya if hypertensive.",
            "time_to_result": "4 weeks (calm, voice)",
        },
        "vedic": {
            "day": "Thursday",
            "mantra": "Om Gram Greem Graum Sah Gurave Namah",
            "count": "108",
            "donation": "Yellow lentils + turmeric + yellow cloth + fruit to priest/poor Thursday",
            "gemstone": "Pukhraj (Yellow Sapphire) 5-7 ct, gold, index finger",
            "gem_caveat": "Trial 3 days. Jupiter remedies suit bail/relief themes — still not substitute for lawyer.",
            "cost_inr_paid": "15,000 – 2,00,000 (gemstone)",
            "free_alt": "Guru stotra Thursday + peepal water + teach/help one person weekly",
        },
    },
    "Sun": {
        "for_areas": "court authority, govt case, dignity, father/govt officer angle, high court tone",
        "practical": {
            "action": (
                "Maintain formal court decorum (dress, punctuality, respectful address) + never lie on oath + "
                "if govt department involved, use RTI/lawful channels with lawyer"
            ),
            "why": "Sun = authority — dignity and truthfulness before court weigh heavily in perception and process.",
            "time_to_result": "Immediate (conduct), weeks (institutional response)",
            "kpi": "100% hearing attendance, formal dress, 0 contempt-risk behaviour",
            "free": True,
            "cost_inr": 0,
        },
        "ayurvedic": {
            "practice": "Morning sunlight 10 min + Surya namaskar 6 rounds + avoid ego-driven outbursts",
            "herb": "Amla daily for vitality under stress",
            "dose": "1 amla or 1 tsp powder AM",
            "vaidya_caveat": "Skip excess amla if active acid reflux.",
            "time_to_result": "3 weeks (energy, composure)",
        },
        "vedic": {
            "day": "Sunday",
            "mantra": "Om Hraam Hreem Hraum Sah Suryaya Namah",
            "count": "108",
            "donation": "Wheat + jaggery + copper item Sunday morning",
            "gemstone": "Manik (Ruby) 3-5 ct — astrologer-fitted",
            "gem_caveat": "Ruby heats — skip if anger already high (Mars-Sun combo).",
            "cost_inr_paid": "15,000 – 2,00,000 (gemstone)",
            "free_alt": "Aditya Hridaya Stotra Sunday + water offering to Sun at sunrise",
        },
    },
    "Moon": {
        "for_areas": "mental stress, sleep, public emotion, mother/family worry during case",
        "practical": {
            "action": (
                "Tell family a realistic case timeline (Saturn delays) + fixed sleep 7+ hr + "
                "weekly emotional check-in with trusted person or counsellor if anxiety high"
            ),
            "why": "Moon = mind — sleep and emotional support prevent panic decisions that harm cases.",
            "time_to_result": "2-3 weeks (sleep/mood)",
            "kpi": "Sleep > 6.5 hr, 1 support conversation/week, no panic-driven calls to opponent",
            "free": True,
            "cost_inr": 0,
        },
        "ayurvedic": {
            "practice": "Bhramari 10 rounds at night + warm milk with nutmeg pinch + moonlight walk",
            "herb": "Jatamansi + Brahmi for sleep (vaidya)",
            "dose": "Evening dose vaidya-guided",
            "vaidya_caveat": "Sedative herbs — no driving after dose.",
            "time_to_result": "3-4 weeks (sleep)",
        },
        "vedic": {
            "day": "Monday",
            "mantra": "Om Som Somaya Namah",
            "count": "108",
            "donation": "White rice + milk + white cloth to needy Monday",
            "gemstone": "Moti (Pearl) 4-6 ct, silver",
            "gem_caveat": "Pearl for calm — avoid stacking with Rahu/Ketu gems same week.",
            "cost_inr_paid": "3,000 – 50,000 (gemstone)",
            "free_alt": "Shiva Panchakshari Monday + Chandra stotra + feed white items to cow",
        },
    },
    "Venus": {
        "for_areas": "family court, maintenance, alimony, domestic harmony, settlement tone",
        "practical": {
            "action": (
                "In family/matrimonial cases: child-welfare log + documented expenses for maintenance claims + "
                "attempt one mediated settlement session before aggressive litigation"
            ),
            "why": "Venus governs domestic balance — courts favour documented good-faith on maintenance/custody.",
            "time_to_result": "4-8 weeks (records), 12+ weeks (settlement window)",
            "kpi": "Expense log maintained, 1 mediation attempt logged, child-contact diary if custody",
            "free": True,
            "cost_inr": 0,
        },
        "ayurvedic": {
            "practice": "Speak softly at home + Friday family meal without case argument + rose-water calm",
            "herb": "Shatavari for emotional steadiness (vaidya, especially women)",
            "dose": "Vaidya-specific",
            "vaidya_caveat": "Shatavari needs vaidya in pregnancy/lactation.",
            "time_to_result": "4-6 weeks (home tone)",
        },
        "vedic": {
            "day": "Friday",
            "mantra": "Om Dram Dreem Draum Sah Shukraya Namah",
            "count": "108",
            "donation": "White sweets + white cloth + curd to needy Friday",
            "gemstone": "Heera (Diamond) or Opal — trial only; often skip in dispute cases",
            "gem_caveat": "Diamond not essential — Lakshmi stotra + harmony actions primary.",
            "cost_inr_paid": "20,000 – 5,00,000 (gemstone)",
            "free_alt": "Lakshmi stotra Friday + donate white items + avoid harsh speech at home",
        },
    },
    "Ketu": {
        "for_areas": "sudden legal shock, isolation, past-karma tone, spiritual detachment, hidden angles",
        "practical": {
            "action": (
                "Full truth to your lawyer including embarrassing facts + avoid isolation — one trusted "
                "advisor + do not ignore summons/notices even if case feels unfair"
            ),
            "why": "Ketu shocks resolve when facts are faced early — avoidance worsens outcomes.",
            "time_to_result": "1-2 weeks (disclosure), 4-8 weeks (strategy shift)",
            "kpi": "No ignored legal notices, full disclosure to counsel, 1 trusted advisor loop",
            "free": True,
            "cost_inr": 0,
        },
        "ayurvedic": {
            "practice": "10-min silent meditation daily + light fasting on Ekadashi if health allows",
            "herb": "Shankhpushpi for mental scatter (vaidya)",
            "dose": "Vaidya-guided",
            "vaidya_caveat": "Fasting not for diabetics/pregnancy without doctor.",
            "time_to_result": "4 weeks (mental steadiness)",
        },
        "vedic": {
            "day": "Tuesday or Saturday",
            "mantra": "Om Sram Srim Sraum Sah Ketave Namah",
            "count": "108",
            "donation": "Blanket + multi-colour cloth + sesame to needy",
            "gemstone": "Lehsunia (Cat's Eye) — trial only",
            "gem_caveat": "Ketu gems sensitive — mantra + Ganesh path often preferred in litigation.",
            "cost_inr_paid": "15,000 – 2,00,000 (gemstone)",
            "free_alt": "Ganesh Atharvashirsha + dogs/birds fed + one silent reflection day/week",
        },
    },
}

LITIGATION_SYSTEM_PRACTICES: Dict[str, Dict[str, str]] = {
    "legal_documents": {
        "practice": "Date-index every paper + 2 physical copies + cloud backup + never sign blank forms",
    },
    "court_attendance": {
        "practice": "Never miss hearing + reach 30 min early + formal dress + switch phone silent in court",
    },
    "advocate_strategy": {
        "practice": "Written 1-page brief before each hearing + weekly case-status note to lawyer + no social media about case",
    },
    "bail_support": {
        "practice": "Keep surety/address proofs ready + comply 100% with bail conditions + report to lawyer if any breach risk",
    },
    "police_fir": {
        "practice": "Lawyer present before detailed police statement + get copy of every FIR page + record IO name/badge",
    },
    "conflict_calm": {
        "practice": "Zero heated arguments with opponent/police + all contact via lawyer + walk away if provoked",
    },
    "delay_patience": {
        "practice": "Monthly case log + follow advocate every 3 weeks + accept structured patience (Saturn cases run long)",
    },
    "criminal_defence": {
        "practice": "Full disclosure to criminal lawyer + alibi witness list + preserve CCTV/phone evidence early",
    },
    "civil_dispute": {
        "practice": "Contract + payment trail organized + registered notices where possible + mediation attempt once",
    },
    "family_court": {
        "practice": "Child-welfare diary + expense records for maintenance + calm speech in family settings",
    },
    "legal_stress": {
        "practice": "Sleep 7+ hr + no alcohol under stress + 10-min daily breathing + counsellor if anxiety persists",
    },
    "acquittal_relief": {
        "practice": "Lawful discharge steps with lawyer + preserve acquittal/quash orders in multiple copies",
    },
}
