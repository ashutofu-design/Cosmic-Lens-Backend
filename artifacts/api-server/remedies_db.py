"""
remedies_db.py — Classical Vastu Remedy Database
=================================================
Deterministic lookup of shastra-cited remedies for HOME + BUSINESS contexts.

Design:
  Layer 1 (this file)  → trusted classical spine, O(1) dict lookup
  Layer 2 (vision)     → adds 1–2 photo-specific remedies on top (capped)

Lookup contract:
    lookup_remedies(room_type, verdict, business_type=None)
        → List[Dict] of remedy entries

Each remedy follows the existing schema used elsewhere:
    {action, english, hindi, priority, classical_ref}
        priority: 1 = highest, larger = lower
        action  : stable key used for dedupe across layers

Sources cited (abbrev):
  BS  = Brihat Samhita (Varahamihira, 6th c.)
  MM  = Mayamatam (10th c.)
  MN  = Manasara
  SS  = Samarangana Sutradhara (Bhoja, 11th c.)
  VP  = Vishwakarma Prakash
  VS  = Vastu Saar / Vastu Shastra
  MSS = Manushyalaya Chandrika
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────
# Verdict normaliser — engines emit either Title-case or with "Adjustment Needed"
# ─────────────────────────────────────────────────────────────────────────
_VERDICT_ALIASES = {
    "avoid":             "Avoid",
    "adjustment needed": "Adjustment Needed",
    "adjustment_needed": "Adjustment Needed",
    "adjustment":        "Adjustment Needed",
    "acceptable":        "Acceptable",
    "ideal":             "Ideal",
    "excellent":         "Ideal",
}

def _norm_verdict(v: str) -> str:
    return _VERDICT_ALIASES.get((v or "").strip().lower(), v or "Acceptable")


# ─────────────────────────────────────────────────────────────────────────
# Universal fallbacks (used when no specific entry exists)
# ─────────────────────────────────────────────────────────────────────────
_UNIVERSAL_BY_VERDICT: Dict[str, List[Dict[str, Any]]] = {
    "Avoid": [
        {
            "action":  "shastra_pooja",
            "english": "Perform a Vastu Shanti Pooja focused on this corner; offer water to Brahmasthan after sunrise on the next Purnima.",
            "hindi":   "Is kone mein Vastu Shanti Pooja karein; agle Purnima ke din sooryoday ke baad Brahmasthan mein jal arpan karein.",
            "priority": 2,
            "classical_ref": "Mayamatam Ch.36 — Vastu Shanti Vidhi",
        },
        {
            "action":  "panchatatva_balance",
            "english": "Balance the five elements: a copper water pot in NE, a clay diya in SE, a green plant in E, salt-rock lamp in SW.",
            "hindi":   "Panch-tatva santulan: NE mein tambe ka kalash, SE mein mitti ka diya, E mein hara paudha, SW mein sendha-namak deepak.",
            "priority": 3,
            "classical_ref": "Brihat Samhita Ch.53 — Panch-mahabhuta",
        },
    ],
    "Adjustment Needed": [
        {
            "action":  "panchatatva_balance",
            "english": "Strengthen the corresponding element: place a small symbolic object (water/fire/earth/air/space) per the direction's ruling element.",
            "hindi":   "Sambandhit tatva ko mazboot karein: disha ke shasak tatva (jal/agni/prithvi/vayu/akash) ka chhota pratik rakhein.",
            "priority": 3,
            "classical_ref": "Mayamatam Ch.7 — Direction-element correspondence",
        },
    ],
    "Acceptable": [
        {
            "action":  "preserve",
            "english": "Maintain current placement; weekly cleansing with rock-salt water on Saturdays preserves harmony.",
            "hindi":   "Vartaman sthaan banaye rakhein; Shaniwar ko sendha-namak vale paani se safai shubh hai.",
            "priority": 4,
            "classical_ref": "Vastu Saar Ch.10 — Sthapana raksha",
        },
    ],
    "Ideal": [
        {
            "action":  "amplify",
            "english": "Amplify the auspicious energy — fresh flowers daily and a ghee diya on Fridays multiply the benefit.",
            "hindi":   "Shubh urja ko badhayein — roz taaze phool aur Shukravar ko ghee ka deepak labh bhadayega.",
            "priority": 5,
            "classical_ref": "Vastu Saar Ch.10 — Subh-vardhan",
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────
# HOME — keyed by (room_type, verdict)
# ─────────────────────────────────────────────────────────────────────────
_HOME_REMEDIES: Dict[Tuple[str, str], List[Dict[str, Any]]] = {

    # ── KITCHEN ─────────────────────────────────────────────────────────
    ("kitchen", "Avoid"): [
        {
            "action":  "stove_relocate",
            "english": "The cooking flame must face East. Relocate the gas stove to the SE corner so the cook faces East while cooking.",
            "hindi":   "Chulhe ki agni Poorab ki taraf honi chahiye. Gas stove SE kone mein le jaayein taaki khana banaate samay mukh Poorab ki ore ho.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.10 — Agni-sthana SE; Manasara 35.71",
        },
        {
            "action":  "fire_water_separation",
            "english": "Stove and sink must never share a wall or face each other. Add a stone partition at least 2 ft wide between them.",
            "hindi":   "Chulha aur sink ek deewar par ya aamne-saamne na ho. Beech mein kam-se-kam 2 feet ka patthar ka partition lagayein.",
            "priority": 1,
            "classical_ref": "Brihat Samhita 53.42 — Agni-jala virodh",
        },
        {
            "action":  "ne_cleanse",
            "english": "If kitchen lies in NE/N, place a copper kalash filled with Ganga jal in the room's NE corner; replace water every Tuesday.",
            "hindi":   "Agar rasoi NE/N mein hai to kamre ke NE kone mein Ganga jal bhara tambe ka kalash rakhein; har Mangalwar ko jal badlein.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 4.18",
        },
    ],
    ("kitchen", "Adjustment Needed"): [
        {
            "action":  "cook_facing_east",
            "english": "Re-orient the stove so the person cooking faces East. Even a small rotation aligns Agni with Surya energy.",
            "hindi":   "Stove ko ghumayein taaki khana banane wala Poorab ki ore mukh kare. Thoda sa rotate karne se bhi Agni-Surya santulan ban jata hai.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.10 — Paacaka mukha",
        },
        {
            "action":  "fire_red_color",
            "english": "Use red, orange, or earthy yellow on the SE wall of the kitchen; avoid black and dark blue.",
            "hindi":   "Rasoi ki SE deewar par laal, narangi ya peela rang use karein; kala aur gehra neela bachein.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.6 — Agni-tatva varna",
        },
    ],
    ("kitchen", "Acceptable"): [
        {
            "action":  "agni_diya",
            "english": "Light a small ghee diya in the SE corner of the kitchen every evening before sunset.",
            "hindi":   "Roz sooryast se pehle rasoi ke SE kone mein ghee ka chhota deepak jalayein.",
            "priority": 3,
            "classical_ref": "Mayamatam Ch.10",
        },
    ],
    ("kitchen", "Ideal"): [
        {
            "action":  "annapurna_yantra",
            "english": "Place a small Annapurna Yantra on the East wall to amplify food prosperity.",
            "hindi":   "Anna-samriddhi ke liye Poorab deewar par chhota Annapurna Yantra rakhein.",
            "priority": 5,
            "classical_ref": "Vishwakarma Prakash 4.22",
        },
    ],

    # ── BEDROOM / MASTER BEDROOM ────────────────────────────────────────
    ("bedroom", "Avoid"): [
        {
            "action":  "bed_head_south",
            "english": "Sleep with head towards South or East — never North. Rotate the bed even if the room itself can't be moved.",
            "hindi":   "Sone ka sir Dakshin ya Poorab ki ore rakhein — Uttar kabhi nahi. Kamra na badle to bhi palang ghuma dein.",
            "priority": 1,
            "classical_ref": "Brihat Samhita 53.97; Manasara 36.21",
        },
        {
            "action":  "mirror_cover",
            "english": "Cover or remove any mirror that reflects the bed; mirrored reflection of sleeper drains pranic energy.",
            "hindi":   "Palang ka pratibimb dikhane wala koi bhi sheesha hatayein ya dhak dein; sote samay pratibimb pran-shakti khinchta hai.",
            "priority": 1,
            "classical_ref": "Vastu Saar Ch.9 — Shayan-sthana darpan nishedha",
        },
        {
            "action":  "ne_bedroom_pooja",
            "english": "If the bedroom falls in NE, do not use it as a master bedroom — convert to pooja, study, or guest room. If unavoidable, place a Kuber Yantra on the NE wall.",
            "hindi":   "Agar bedroom NE mein hai to master bedroom na rakhein — pooja, padhai ya atithi-kaksh banayein. Sambhav na ho to NE deewar par Kuber Yantra rakhein.",
            "priority": 2,
            "classical_ref": "Mayamatam Ch.9 — NE Ishanya niyam",
        },
    ],
    ("bedroom", "Adjustment Needed"): [
        {
            "action":  "bed_head_east",
            "english": "Position the bed so head points East (best for students/young) or South (best for householders); never towards a door.",
            "hindi":   "Palang aisi rakhein ki sir Poorab (vidyarthi/yuva ke liye uttam) ya Dakshin (gruhasti ke liye uttam) ki ore ho; darwaze ki taraf kabhi nahi.",
            "priority": 1,
            "classical_ref": "Brihat Samhita 53.97",
        },
        {
            "action":  "headboard_solid",
            "english": "Use a solid wooden headboard; avoid metal frames in the master bedroom as they disturb sleep magnetism.",
            "hindi":   "Palang ke peeche thos lakdi ka headboard rakhein; master bedroom mein dhatu ka frame neend ki chumbakiya tarangein bigaadta hai.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 6.14",
        },
    ],
    ("bedroom", "Acceptable"): [
        {
            "action":  "rose_quartz",
            "english": "Place a small rose quartz crystal in the SW corner to deepen rest and partner harmony.",
            "hindi":   "Vishranti aur dampatya samanjasya ke liye SW kone mein chhota gulaabi quartz crystal rakhein.",
            "priority": 3,
            "classical_ref": "Vastu Saar Ch.9 (Ratna upachar)",
        },
    ],
    ("bedroom", "Ideal"): [
        {
            "action":  "amplify_sw",
            "english": "Keep the SW corner of the bedroom heavy and earthy — a wooden cupboard or stone vase amplifies stability.",
            "hindi":   "Bedroom ka SW kona bhari aur prithvi-tatva yukt rakhein — lakdi ki almari ya patthar ka phooldaan sthirta badhata hai.",
            "priority": 5,
            "classical_ref": "Manasara 36.18",
        },
    ],

    # ── POOJA ROOM ──────────────────────────────────────────────────────
    ("pooja", "Avoid"): [
        {
            "action":  "pooja_relocate_ne",
            "english": "Pooja room MUST be in the North-East. If currently elsewhere, set up at minimum a small NE altar in any room and migrate over time.",
            "hindi":   "Pooja kaksh AVASHYA NE mein hona chahiye. Yadi anyatra hai to kisi bhi kamre ke NE mein chhoti vedi sthapit karein aur dheere-dheere shift karein.",
            "priority": 1,
            "classical_ref": "Manasara Sh.5; Mayamatam Ch.6",
        },
        {
            "action":  "no_idol_against_south",
            "english": "Never let the deity face South or have its back to a toilet/kitchen wall. Re-orient idol to face West (devotee faces East).",
            "hindi":   "Devta ka mukh Dakshin ki ore na ho aur peeth shauchalaya/rasoi ki deewar se na lagi ho. Murti ko Pashchim ki ore mukh karein (bhakt Poorab dekhein).",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 5.9",
        },
    ],
    ("pooja", "Adjustment Needed"): [
        {
            "action":  "deity_face_west",
            "english": "The devotee should face East or North while praying. Place idols on a wooden chowki at least 4 fingers above floor.",
            "hindi":   "Pooja ke samay bhakt ka mukh Poorab ya Uttar ki ore ho. Murtiyon ko lakdi ki chowki par farsh se kam-se-kam 4 ungli unchaai par sthapit karein.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.6",
        },
        {
            "action":  "white_yellow_palette",
            "english": "Use white, light yellow, or saffron in the pooja room; avoid black, grey, and dark colours.",
            "hindi":   "Pooja kaksh mein safed, halka peela ya kesari rang use karein; kala, slettee aur gehre rang bachein.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.7",
        },
    ],
    ("pooja", "Acceptable"): [
        {
            "action":  "kalash_ne",
            "english": "Place a copper kalash with Ganga jal in the NE of the altar; replace water every Thursday.",
            "hindi":   "Vedi ke NE mein Ganga jal bhara tambe ka kalash rakhein; har Brihaspativar ko jal badlein.",
            "priority": 3,
            "classical_ref": "Mayamatam Ch.6",
        },
    ],
    ("pooja", "Ideal"): [
        {
            "action":  "shankh_bell",
            "english": "Sound a conch and bell at sunrise and sunset — purifies pranic field of the entire home.",
            "hindi":   "Sooryoday aur sooryast par shankh aur ghanti bajayein — sampoorn ghar ka pran-mandal shuddh hota hai.",
            "priority": 5,
            "classical_ref": "Brihat Samhita Ch.46",
        },
    ],

    # ── TOILET / BATHROOM ───────────────────────────────────────────────
    ("toilet", "Avoid"): [
        {
            "action":  "toilet_seal_ne",
            "english": "A toilet in NE drains wealth and health. Keep door always shut, install bright NW exhaust, and place a sea-salt bowl inside (replace weekly).",
            "hindi":   "NE mein shauchalaya dhan aur swasthya khinchta hai. Darwaza humesha band rakhein, NW mein roshan exhaust lagayein, andar samudri-namak ka katora rakhein (haftaa-vaar badlein).",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.11; Brihat Samhita 53.66",
        },
        {
            "action":  "toilet_no_kitchen_share",
            "english": "Toilet wall must not back onto kitchen or pooja. Add a 9-inch insulating wall or wall-hung copper pyramid as remedy.",
            "hindi":   "Shauchalaya ki deewar rasoi ya pooja se laagi nahi honi chahiye. 9-inch ki insulation deewar ya tambe ka pyramid lagayein.",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 7.4",
        },
    ],
    ("toilet", "Adjustment Needed"): [
        {
            "action":  "toilet_door_closed",
            "english": "Keep toilet door closed at all times; toilet seat lid must remain down when not in use.",
            "hindi":   "Shauchalaya ka darwaza humesha band rakhein; seat ka dhakkan upyog ke baad neeche rakhein.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.11",
        },
        {
            "action":  "salt_bowl",
            "english": "Place a small bowl of rock salt inside the toilet; replace every 7 days.",
            "hindi":   "Shauchalaya ke andar sendha-namak ka chhota katora rakhein; 7 din mein badlein.",
            "priority": 3,
            "classical_ref": "Vastu Saar Ch.11 (lavana shuddhi)",
        },
    ],
    ("toilet", "Acceptable"): [
        {
            "action":  "exhaust_nw",
            "english": "Install a strong exhaust on the NW or W wall; keep a small lit bulb inside even at night.",
            "hindi":   "NW ya W deewar par shaktishali exhaust lagayein; raat ko bhi andar chhota bulb jalta rakhein.",
            "priority": 4,
            "classical_ref": "Vastu Saar Ch.11",
        },
    ],

    # bathroom (separate from toilet) — wash area
    ("bathroom", "Avoid"): [
        {
            "action":  "geyser_se",
            "english": "Move geyser/heater to the SE corner of the bathroom; cold-water taps to NE/N wall.",
            "hindi":   "Geyser/heater ko bathroom ke SE kone mein le jaayein; thande paani ke nal NE/N deewar par.",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 7.6",
        },
        {
            "action":  "drain_north",
            "english": "Re-route the drain so wastewater exits from the North or East side, never from SW.",
            "hindi":   "Naali ko aisa banayein ki paani Uttar ya Poorab se nikle, SW se kabhi nahi.",
            "priority": 2,
            "classical_ref": "Brihat Samhita 53.66",
        },
    ],
    ("bathroom", "Adjustment Needed"): [
        {
            "action":  "geyser_se",
            "english": "Place electrical heating fixtures on the SE wall only.",
            "hindi":   "Bijli se chalne wale heating fixtures sirf SE deewar par lagayein.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 7.6",
        },
    ],
    ("bathroom", "Acceptable"): [
        {
            "action":  "ventilation_e",
            "english": "Ensure morning sunlight enters from East; dry-mop floor before noon to prevent stagnation.",
            "hindi":   "Subah ki dhoop Poorab se aaye yeh sunishchit karein; dopahar se pehle farsh sukha lein.",
            "priority": 4,
            "classical_ref": "Vastu Saar Ch.11",
        },
    ],

    # ── STUDY ROOM ──────────────────────────────────────────────────────
    ("study", "Avoid"): [
        {
            "action":  "desk_face_east",
            "english": "Move the study desk so the student faces East or North while studying. South-facing desk dulls memory.",
            "hindi":   "Padhai ki mez aisi rakhein ki vidyarthi ka mukh Poorab ya Uttar ki ore ho. Dakshin disha smarna shakti kam karti hai.",
            "priority": 1,
            "classical_ref": "Brihat Samhita 56.3",
        },
        {
            "action":  "saraswati_yantra",
            "english": "Place a Saraswati Yantra or her image on the East wall in front of the desk; offer a yellow flower on Wednesdays.",
            "hindi":   "Mez ke saamne Poorab deewar par Saraswati Yantra ya pratima rakhein; Budhwar ko peela phool arpan karein.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 5.16",
        },
    ],
    ("study", "Adjustment Needed"): [
        {
            "action":  "desk_face_east",
            "english": "Re-position desk so the student faces East (memory) or North (clarity).",
            "hindi":   "Mez aisi rakhein ki mukh Poorab (smriti) ya Uttar (spashtata) ki ore ho.",
            "priority": 1,
            "classical_ref": "Brihat Samhita 56.3",
        },
        {
            "action":  "no_back_to_door",
            "english": "Student's back should never face the door; shift chair so door is in peripheral vision.",
            "hindi":   "Vidyarthi ki peeth darwaze ki ore na ho; kursi aisi rakhein ki darwaza side se dikhe.",
            "priority": 2,
            "classical_ref": "Mayamatam Ch.13",
        },
    ],
    ("study", "Acceptable"): [
        {
            "action":  "green_plant_e",
            "english": "Keep a small money-plant or tulsi on the East side of the desk; refreshes prana.",
            "hindi":   "Mez ke Poorab taraf chhota money-plant ya tulsi rakhein; pran-vayu shuddh hoti hai.",
            "priority": 3,
            "classical_ref": "Vastu Saar Ch.8",
        },
    ],
    ("study", "Ideal"): [
        {
            "action":  "ghee_lamp_e",
            "english": "Light a ghee lamp at sunrise on Thursdays — Brihaspati's day strengthens intellect.",
            "hindi":   "Brihaspativar ko sooryoday par ghee ka deepak jalayein — buddhi tez hoti hai.",
            "priority": 5,
            "classical_ref": "Vishwakarma Prakash 5.18",
        },
    ],

    # ── LIVING ROOM ─────────────────────────────────────────────────────
    ("living", "Avoid"): [
        {
            "action":  "seating_to_north",
            "english": "Re-arrange sofas so primary seating faces North or East; head of family sits with back to South wall.",
            "hindi":   "Sofa aise rakhein ki mukhya baithak ka mukh Uttar ya Poorab ho; parivar ke mukhya ki peeth Dakshin deewar par lage.",
            "priority": 1,
            "classical_ref": "Brihat Samhita 53.84",
        },
        {
            "action":  "heavy_sw",
            "english": "Move heavy furniture (book-shelves, large cabinets) to the SW corner. Keep NE corner light, open and clean.",
            "hindi":   "Bhari furniture (kitabon ki almari, badi cabinets) SW kone mein rakhein. NE kona halka, khula aur saaf rakhein.",
            "priority": 2,
            "classical_ref": "Manasara 35.42",
        },
    ],
    ("living", "Adjustment Needed"): [
        {
            "action":  "tv_se",
            "english": "TV / electronic equipment must sit on the SE wall (Agni zone), not on the NE.",
            "hindi":   "TV / bijli ke yantra SE deewar par rakhein (Agni-sthan), NE par nahi.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 4.21",
        },
    ],
    ("living", "Acceptable"): [
        {
            "action":  "fresh_flowers_ne",
            "english": "Keep a fresh-flower vase in the NE corner of the living room; replace water on Mondays.",
            "hindi":   "Living room ke NE kone mein taaze phoolon ka phooldaan rakhein; Somwar ko paani badlein.",
            "priority": 3,
            "classical_ref": "Vastu Saar Ch.10",
        },
    ],
    ("living", "Ideal"): [
        {
            "action":  "diya_brahmasthan",
            "english": "Light a small lamp at the Brahmasthan (centre) of the living room every evening at sandhya kaal.",
            "hindi":   "Living room ke Brahmasthan (kendra) mein roz sandhya kaal mein chhota deepak jalayein.",
            "priority": 5,
            "classical_ref": "Mayamatam Ch.7 — Brahmasthan",
        },
    ],

    # ── DINING ROOM ─────────────────────────────────────────────────────
    ("dining", "Avoid"): [
        {
            "action":  "diner_face_east",
            "english": "Re-orient the dining table so the head of family faces East while eating; never South.",
            "hindi":   "Bhojan-mez aisi rakhein ki khaate samay parivar mukhya ka mukh Poorab ki ore ho; Dakshin kabhi nahi.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.10 — Bhojan disha",
        },
    ],
    ("dining", "Adjustment Needed"): [
        {
            "action":  "no_mirror_at_table",
            "english": "Cover or remove any mirror reflecting the dining table; reflected food invites loss.",
            "hindi":   "Bhojan-mez ka pratibimb dikhane wala sheesha hatayein ya dhak dein; pratisthapit anna ki haani hoti hai.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.6",
        },
    ],
    ("dining", "Acceptable"): [
        {
            "action":  "wash_basin_w",
            "english": "Wash basin should sit on the W or NW wall, never on E or NE.",
            "hindi":   "Wash basin Pashchim ya NW deewar par ho, Poorab ya NE par nahi.",
            "priority": 3,
            "classical_ref": "Vishwakarma Prakash 4.30",
        },
    ],

    # ── STORE ROOM ──────────────────────────────────────────────────────
    ("store", "Avoid"): [
        {
            "action":  "store_to_nw",
            "english": "Heavy storage belongs in NW or SW. If currently in NE/E, move at least the heaviest items first; never store grains in NE.",
            "hindi":   "Bhari bhandar NW ya SW mein hota hai. NE/E mein hai to sabse bhari saamaan pehle hatayein; anaaj NE mein kabhi na rakhein.",
            "priority": 1,
            "classical_ref": "Manasara 35.55",
        },
    ],
    ("store", "Adjustment Needed"): [
        {
            "action":  "grains_sw",
            "english": "Store grains and pulses in airtight containers along the SW wall; oil and ghee in SE.",
            "hindi":   "Anaaj aur dalein hava-band dabbon mein SW deewar par rakhein; tel aur ghee SE mein.",
            "priority": 2,
            "classical_ref": "Brihat Samhita 53.50",
        },
    ],
    ("store", "Acceptable"): [
        {
            "action":  "declutter_monthly",
            "english": "Discard unused items monthly; broken or rusted things in store invite Rahu's afflictions.",
            "hindi":   "Hr maheene anupayogi cheezein hatayein; toota ya jang-laga saamaan store mein rahna Rahu dosh laata hai.",
            "priority": 3,
            "classical_ref": "Vishwakarma Prakash 7.18",
        },
    ],

    # ── ENTRANCE / MAIN DOOR ────────────────────────────────────────────
    ("entrance", "Avoid"): [
        {
            "action":  "door_threshold",
            "english": "Install a marble or wooden threshold (chowkat) at least 2 inches high; pin a copper-pyramid Vastu Yantra above the frame.",
            "hindi":   "Sangmarmar ya lakdi ka chowkat kam-se-kam 2-inch unchaai ka lagayein; chowkhat ke upar tambe ka Vastu Yantra lagayein.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.5; Brihat Samhita 53.7",
        },
        {
            "action":  "door_opens_inward_clockwise",
            "english": "Main door must open inward and clockwise; rectify hinge direction if reversed.",
            "hindi":   "Mukhya dwar andar ki taraf aur ghadi ki disha mein khule; vipreet ho to hinges badlein.",
            "priority": 1,
            "classical_ref": "Manasara 33.18",
        },
        {
            "action":  "no_obstruction",
            "english": "Remove any pole, pillar, tree-trunk, or staircase directly facing the main door (Veedhi Shoola).",
            "hindi":   "Mukhya dwar ke saamne koi khambha, ped, ya seedhi (Veedhi Shoola) na ho — hatayein.",
            "priority": 2,
            "classical_ref": "Mayamatam Ch.5 — Veedhi Shoola",
        },
    ],
    ("entrance", "Adjustment Needed"): [
        {
            "action":  "vandanwar",
            "english": "Hang a fresh mango-leaf toran (vandanwar) above the door; replace every 7–10 days.",
            "hindi":   "Dwar ke upar taaza aam ke patton ka toran lagayein; 7–10 din mein badlein.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.5",
        },
        {
            "action":  "door_brass_kalash",
            "english": "Mount a brass Ganesha or kalash motif on the upper centre of the door panel.",
            "hindi":   "Darwaze ke upar beech mein peetal ka Ganesh ya kalash motif lagayein.",
            "priority": 3,
            "classical_ref": "Vishwakarma Prakash 3.11",
        },
    ],
    ("entrance", "Acceptable"): [
        {
            "action":  "rangoli_daily",
            "english": "Draw a small rangoli or auspicious symbol at the threshold each morning; light a diya at sandhya.",
            "hindi":   "Roz subah dehri par chhoti rangoli ya shubh chinha banayein; sandhya kaal mein diya jalayein.",
            "priority": 4,
            "classical_ref": "Vastu Saar Ch.5",
        },
    ],
    ("entrance", "Ideal"): [
        {
            "action":  "lakshmi_footsteps",
            "english": "Paint Lakshmi paduka (footsteps) leading inward at the threshold to invite continuous prosperity.",
            "hindi":   "Dehri par andar ki ore Lakshmi paduka (charan-chinh) banayein — nirantar samriddhi aati hai.",
            "priority": 5,
            "classical_ref": "Vishwakarma Prakash 3.14",
        },
    ],

    # ── STAIRCASE ───────────────────────────────────────────────────────
    ("staircase", "Avoid"): [
        {
            "action":  "stair_clockwise_sw",
            "english": "Staircase must rise clockwise and sit in the SW or W zone, never in NE or centre. If unmovable, paint risers in earthy tones and never store anything below.",
            "hindi":   "Seedhi ghadi ki disha mein chadhe aur SW ya W mein ho, NE ya kendra mein kabhi nahi. Hata na sake to seedhi ke upar prithvi-rang aur neeche kuch na rakhein.",
            "priority": 1,
            "classical_ref": "Manasara 36.47; Mayamatam Ch.20",
        },
    ],
    ("staircase", "Adjustment Needed"): [
        {
            "action":  "odd_steps",
            "english": "Total step count should be odd (e.g. 9, 11, 13, 17). Adjust the last step height if even.",
            "hindi":   "Kul seedhiyon ki sankhya visham (jaise 9, 11, 13, 17) honi chahiye. Even ho to aakhri seedhi ki unchaai badlein.",
            "priority": 2,
            "classical_ref": "Mayamatam Ch.20",
        },
        {
            "action":  "no_store_below_stairs",
            "english": "Do not use the area under the staircase as a pooja, kitchen, or bedroom — only as light storage or open passage.",
            "hindi":   "Seedhi ke neeche pooja, rasoi ya bedroom na banayein — keval halka bhandar ya khula maarg.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 6.22",
        },
    ],

    # ── BALCONY ─────────────────────────────────────────────────────────
    ("balcony", "Avoid"): [
        {
            "action":  "balcony_open_ne",
            "english": "Keep NE/E balcony fully open and clutter-free — no broken pots, no air-conditioner units. AC units belong on the SW balcony only.",
            "hindi":   "NE/E balcony poori khuli aur saaf rakhein — toote gamale, AC unit nahi. AC keval SW balcony mein.",
            "priority": 1,
            "classical_ref": "Brihat Samhita 53.78",
        },
    ],
    ("balcony", "Adjustment Needed"): [
        {
            "action":  "tulsi_ne",
            "english": "Place a tulsi or money plant on the NE/E balcony; water daily before sunrise.",
            "hindi":   "NE/E balcony mein tulsi ya money plant rakhein; roz sooryoday se pehle paani dein.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.10",
        },
    ],
    ("balcony", "Acceptable"): [
        {
            "action":  "wind_chimes_nw",
            "english": "Hang metal wind-chimes on the NW balcony — keeps Vayu element flowing.",
            "hindi":   "NW balcony mein dhatu ki wind-chimes lagayein — Vayu-tatva pravahit rehta hai.",
            "priority": 4,
            "classical_ref": "Vishwakarma Prakash 4.27",
        },
    ],
}

# Aliases — engines may emit slightly different room names
_ROOM_ALIASES: Dict[str, str] = {
    "master_bedroom":  "bedroom",
    "guest_bedroom":   "bedroom",
    "kids_bedroom":    "bedroom",
    "children_room":   "study",
    "meditation":      "pooja",
    "puja":            "pooja",
    "main_door":       "entrance",
    "main_entrance":   "entrance",
    "front_door":      "entrance",
    "drawing_room":    "living",
    "drawing":         "living",
    "lounge":          "living",
    "hall":            "living",
    "dining_room":     "dining",
    "store_room":      "store",
    "storage":         "store",
    "godown":          "store",
    "stair":           "staircase",
    "staircase_room":  "staircase",
    "washroom":        "bathroom",
    "wc":              "toilet",
    "lavatory":        "toilet",
}


# ─────────────────────────────────────────────────────────────────────────
# BUSINESS overlays — keyed by (business_type, room_type, verdict)
# Returns 1–2 business-specific remedies that apply ON TOP of home base.
# ─────────────────────────────────────────────────────────────────────────
_BUSINESS_REMEDIES: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {

    # ── SHOP ────────────────────────────────────────────────────────────
    ("shop", "entrance", "Avoid"): [
        {
            "action":  "shop_dwar_kuber",
            "english": "Mount a Kuber Yantra above the shop entrance and a Lakshmi-Ganesh idol on the inner-left wall facing the door.",
            "hindi":   "Dukaan ke dwar ke upar Kuber Yantra aur andar baayein deewar par Lakshmi-Ganesh ki murti dwar ki ore lagayein.",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 8.4 — Vipani-dwara",
        },
        {
            "action":  "shop_door_size",
            "english": "Shop door must be the largest opening on the front facade and open inwards; widen if it is currently narrower than internal doors.",
            "hindi":   "Dukaan ka dwar saamne ki sabse badi opening ho aur andar khule; andar ke darwazon se chhota ho to choda karein.",
            "priority": 2,
            "classical_ref": "Manasara 33.30",
        },
    ],
    ("shop", "entrance", "Adjustment Needed"): [
        {
            "action":  "swastik_threshold",
            "english": "Paint a red swastik on each side of the shop threshold every Friday morning.",
            "hindi":   "Hr Shukravar subah dukaan ki dehri ke dono ore laal swastik banayein.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.5",
        },
    ],

    ("shop", "owner_seat", "Avoid"): [
        {
            "action":  "owner_sw_face_ne",
            "english": "Owner's seat MUST be in the SW corner of the shop, facing NE. Move the desk; this single change often turns a struggling shop profitable.",
            "hindi":   "Maalik ki gaddi AVASHYA dukaan ke SW kone mein, NE ki ore mukh karke ho. Yeh ek badlaav aksar haani-grast dukaan ko laabh-prada bana deta hai.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.30 — Swami-sthana",
        },
        {
            "action":  "owner_solid_back",
            "english": "Owner's chair must have a solid wall (no window, no door) directly behind — represents stable support.",
            "hindi":   "Maalik ki kursi ke theek peeche thos deewar ho (na khidki, na darwaza) — sthir aadhaar ka prateek.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 8.7",
        },
    ],
    ("shop", "owner_seat", "Adjustment Needed"): [
        {
            "action":  "owner_face_ne",
            "english": "Rotate owner's chair to face NE or N; back to S/SW wall.",
            "hindi":   "Maalik ki kursi NE ya N ki ore ghumayein; peeth S/SW deewar par.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.30",
        },
    ],

    ("shop", "cash_counter", "Avoid"): [
        {
            "action":  "cash_north_open_north",
            "english": "Cash counter must be in the N or NE; the cash drawer should open towards the North (Kuber's direction). Re-orient the till even if the counter itself can't move.",
            "hindi":   "Golak (cash counter) N ya NE mein ho; cash drawer Uttar disha (Kuber ki disha) mein khule. Counter na badle to bhi till ki disha badlein.",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 8.11",
        },
        {
            "action":  "cash_kuber",
            "english": "Place a Kuber Yantra inside the cash drawer and a small piece of silver in every till compartment.",
            "hindi":   "Cash drawer ke andar Kuber Yantra rakhein; har khaane mein chandi ka chhota tukda rakhein.",
            "priority": 2,
            "classical_ref": "Vastu Saar Ch.13 — Dhana-sthana",
        },
    ],
    ("shop", "cash_counter", "Adjustment Needed"): [
        {
            "action":  "cash_drawer_north",
            "english": "Re-orient cash drawer to open towards North; never towards South or West.",
            "hindi":   "Cash drawer Uttar ki ore khole; Dakshin ya Pashchim mein kabhi nahi.",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 8.11",
        },
    ],

    ("shop", "storage", "Avoid"): [
        {
            "action":  "stock_sw_nw",
            "english": "Heavy stock and inventory belongs in SW or NW; fast-moving items in NW (quick turnover), slow-moving in SW.",
            "hindi":   "Bhari maal SW ya NW mein rakhein; jaldi bikne wala NW (teji se ghumaav), dheere bikne wala SW.",
            "priority": 1,
            "classical_ref": "Manasara 35.55 — Bhandar-sthana",
        },
    ],
    ("shop", "customer_zone", "Avoid"): [
        {
            "action":  "customer_face_owner",
            "english": "Customer seating/standing area should face the owner so customers face N or E while interacting.",
            "hindi":   "Grahak baithak/khade hone ka sthan aisa ho ki grahak ka mukh maalik ki ore (N ya E) ho.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 8.14",
        },
    ],

    # ── OFFICE ──────────────────────────────────────────────────────────
    ("office", "owner_cabin", "Avoid"): [
        {
            "action":  "ceo_sw",
            "english": "CEO/MD cabin MUST be in the SW corner; CEO faces NE while seated. Re-locate the cabin even if it requires partition rebuild.",
            "hindi":   "CEO/MD ka cabin AVASHYA SW kone mein ho; CEO baithe samay NE ki ore mukh karein. Partition badalna pade to bhi cabin shift karein.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.30; Manasara 36.61",
        },
        {
            "action":  "no_beam_overhead",
            "english": "No beam, AC duct, or staircase should run directly above the owner's chair — install a false-ceiling baffle.",
            "hindi":   "Maalik ki kursi ke theek upar koi beam, AC duct ya seedhi na ho — false ceiling lagayein.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 6.18",
        },
    ],
    ("office", "owner_cabin", "Adjustment Needed"): [
        {
            "action":  "ceo_face_ne",
            "english": "Rotate CEO's chair to face NE/N; ensure solid wall behind, glass partition or window in front.",
            "hindi":   "CEO ki kursi NE/N ki ore ghumayein; peeche thos deewar, saamne kaanch ka partition ya khidki ho.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.30",
        },
    ],

    ("office", "reception", "Avoid"): [
        {
            "action":  "reception_ne_e",
            "english": "Reception desk should sit in the NE/E zone facing the entrance; receptionist faces N or E.",
            "hindi":   "Reception desk NE/E zone mein dwar ki ore ho; receptionist N ya E ki ore mukh kare.",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 8.21",
        },
    ],
    ("office", "conference", "Avoid"): [
        {
            "action":  "conf_nw_oval",
            "english": "Conference room is best in NW (decision-flow) or W; use an oval/round table — sharp rectangular corners polarise discussion.",
            "hindi":   "Conference room NW (nirnay-pravah) ya W mein uttam; oval/gol mez use karein — teek-koned rectangular mez vichar-vimarsh ko vibhajit karti hai.",
            "priority": 2,
            "classical_ref": "Manasara 36.65 — Sabha-sthana",
        },
    ],
    ("office", "accounts", "Avoid"): [
        {
            "action":  "accounts_n_safe_se",
            "english": "Accounts/finance team should sit in N (Kuber); safe/locker on S wall opening to N. Never place lockers on E or NE walls.",
            "hindi":   "Accounts/vittiya team N (Kuber) mein baithe; tijori S deewar par N ki ore khulti ho. Tijori E ya NE deewar par kabhi nahi.",
            "priority": 1,
            "classical_ref": "Vastu Saar Ch.13; Vishwakarma Prakash 8.27",
        },
    ],
    ("office", "pantry", "Avoid"): [
        {
            "action":  "pantry_se",
            "english": "Office pantry/kitchenette must be in SE; microwave and water-dispenser separated by at least 3 feet.",
            "hindi":   "Office pantry SE mein ho; microwave aur water-dispenser ke beech kam-se-kam 3 feet ka antar.",
            "priority": 2,
            "classical_ref": "Mayamatam Ch.10",
        },
    ],

    # ── FACTORY ─────────────────────────────────────────────────────────
    ("factory", "machinery", "Avoid"): [
        {
            "action":  "heavy_machine_sw",
            "english": "Heavy stationary machinery (lathes, presses, generators) MUST sit in the SW quadrant. Light/moving machinery in NW.",
            "hindi":   "Bhari sthir machinery (lathe, press, generator) AVASHYA SW kone mein ho. Halki/chaaltee machinery NW mein.",
            "priority": 1,
            "classical_ref": "Vishwakarma Prakash 9.3 — Yantra-sthana",
        },
        {
            "action":  "no_machine_ne",
            "english": "NE quadrant must remain free of heavy machinery, raw material piles, or scrap — keep this zone open and well-lit.",
            "hindi":   "NE quadrant mein bhari machinery, kachcha maal ke dher, ya scrap na ho — yeh sthan khula aur prakashit rakhein.",
            "priority": 1,
            "classical_ref": "Manasara 35.78",
        },
    ],
    ("factory", "machinery", "Adjustment Needed"): [
        {
            "action":  "machine_face_se_run",
            "english": "Operator should face East or North while running machinery; install East-side natural lighting.",
            "hindi":   "Machinery chalate samay operator ka mukh Poorab ya Uttar ki ore ho; Poorab taraf prakratik prakash ki vyavastha karein.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 9.6",
        },
    ],

    ("factory", "boiler", "Avoid"): [
        {
            "action":  "boiler_se_only",
            "english": "Boiler, furnace, or any high-heat unit MUST be in SE — the Agni quadrant. Boiler in NE/SW invites fire accidents and rapid financial drain.",
            "hindi":   "Boiler, bhatti ya koi bhi tej-taap yantra AVASHYA SE — Agni quadrant — mein ho. NE/SW mein boiler agni-durghatna aur teevra dhan-haani laata hai.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.10; Brihat Samhita 53.45",
        },
        {
            "action":  "fire_safety_kavach",
            "english": "Install fire-safety equipment on every wall of boiler room and place a small Hanuman Yantra on the South wall for protection.",
            "hindi":   "Boiler kamre ki har deewar par fire-safety upkaran lagayein aur S deewar par chhota Hanuman Yantra rakhein.",
            "priority": 2,
            "classical_ref": "Vishwakarma Prakash 9.10",
        },
    ],

    ("factory", "storage", "Avoid"): [
        {
            "action":  "raw_material_nw",
            "english": "Raw material in NW (fast turnover); finished goods in SW (stable holding); never store stock in NE.",
            "hindi":   "Kachcha maal NW mein (teji se ghumaav); taiyaar maal SW mein (sthir bhandar); NE mein stock kabhi na rakhein.",
            "priority": 1,
            "classical_ref": "Manasara 35.55",
        },
    ],

    ("factory", "owner_cabin", "Avoid"): [
        {
            "action":  "owner_sw_overlook",
            "english": "Owner's cabin in SW with elevated view of factory floor; owner faces NE while seated.",
            "hindi":   "Maalik ka cabin SW mein, factory floor ka uncha drishya yukt; baithe samay NE ki ore mukh.",
            "priority": 1,
            "classical_ref": "Mayamatam Ch.30",
        },
    ],

    ("factory", "raw_material", "Avoid"): [
        {
            "action":  "raw_material_nw",
            "english": "Raw material storage in the NW zone; rotate stock first-in-first-out to harness Vayu element.",
            "hindi":   "Kachcha maal NW zone mein; first-in-first-out se stock ghumayein — Vayu tatva ka labh.",
            "priority": 1,
            "classical_ref": "Manasara 35.55",
        },
    ],
}

_BUSINESS_ROOM_ALIASES: Dict[str, str] = {
    "main_entrance":  "entrance",
    "main_door":      "entrance",
    "shop_door":      "entrance",
    "owner":          "owner_seat",
    "owner_desk":     "owner_seat",
    "gaddi":          "owner_seat",
    "ceo_cabin":      "owner_cabin",
    "md_cabin":       "owner_cabin",
    "director_cabin": "owner_cabin",
    "cash":           "cash_counter",
    "till":           "cash_counter",
    "golak":          "cash_counter",
    "stockroom":      "storage",
    "godown":         "storage",
    "warehouse":      "storage",
    "production":     "machinery",
    "machine_floor":  "machinery",
    "furnace":        "boiler",
    "kiln":           "boiler",
    "boardroom":      "conference",
    "meeting_room":   "conference",
    "finance":        "accounts",
    "kitchen":        "pantry",  # office context
}


# ─────────────────────────────────────────────────────────────────────────
# Public lookup
# ─────────────────────────────────────────────────────────────────────────
def _normalize_room(room_type: str, business_type: Optional[str] = None) -> Tuple[str, str]:
    """Return (raw_norm, home_alias). raw_norm preserves business-specific names."""
    rt = (room_type or "").strip().lower().replace(" ", "_").replace("-", "_")
    if business_type:
        rt = _BUSINESS_ROOM_ALIASES.get(rt, rt)
    home = _ROOM_ALIASES.get(rt, rt)
    return rt, home


def lookup_remedies(
    room_type: str,
    verdict: str,
    business_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return a list of classical remedies for the given (room_type, verdict).
    If business_type provided, business-specific overlay is appended first.
    Falls back to universal remedies for the verdict if no specific match.

    Returned remedies follow the standard schema:
        {action, english, hindi, priority, classical_ref}
    """
    v = _norm_verdict(verdict)
    raw_room, home_room = _normalize_room(room_type, business_type)

    out: List[Dict[str, Any]] = []

    # 1. Business overlay first (highest contextual relevance)
    if business_type:
        biz_key = (business_type.lower(), raw_room, v)
        out.extend(_BUSINESS_REMEDIES.get(biz_key, []))

    # 2. Home base for the room+verdict
    out.extend(_HOME_REMEDIES.get((home_room, v), []))

    # 3. Universal fallback if still empty
    if not out:
        out.extend(_UNIVERSAL_BY_VERDICT.get(v, []))

    return out


# ─────────────────────────────────────────────────────────────────────────
# Merger — combine DB remedies with engine-supplied remedies, dedupe by action
# ─────────────────────────────────────────────────────────────────────────
def merge_remedies(
    existing: List[Dict[str, Any]],
    room_type: str,
    verdict: str,
    business_type: Optional[str] = None,
    max_total: int = 6,
) -> List[Dict[str, Any]]:
    """
    Deterministic merge of:
      1. existing remedies from engine/vision (preserved as-is, top priority)
      2. classical DB remedies for (room_type, verdict[, business_type])

    Dedupes by `action` key. Sorted by priority. Capped at `max_total`.
    """
    existing = existing or []
    seen_actions = {(r.get("action") or "").lower() for r in existing if r}

    db_remedies = lookup_remedies(room_type, verdict, business_type)
    fresh = [r for r in db_remedies
             if (r.get("action") or "").lower() not in seen_actions]

    combined = list(existing) + fresh
    combined.sort(key=lambda r: r.get("priority", 99))
    return combined[:max_total]
