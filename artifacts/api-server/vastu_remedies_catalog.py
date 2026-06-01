"""
vastu_remedies_catalog.py — Extended practical Vastu remedy pool (500+ room×verdict picks).

Design: templates + per (room, verdict) plan → lookup merges with remedies_db._HOME_REMEDIES.
UI still shows only top 2–3 via merge_remedies(max_total=3) and REMEDY_BUDGET.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

_VERDICTS = ("Avoid", "Adjustment Needed", "Acceptable", "Ideal")

_ALL_HOME_ROOMS = (
    "kitchen", "bedroom", "pooja", "toilet", "bathroom", "study", "living",
    "dining", "store", "entrance", "staircase", "balcony", "basement",
    "garage", "cash_locker", "guest_room", "terrace", "overhead_tank",
    "septic", "borewell", "servant_room", "home_office", "main_door",
    "master_bedroom", "pooja_room", "living_room", "dining_room",
)


def _tpl(
    action: str,
    english: str,
    hindi: str,
    priority: int,
    classical_ref: str,
) -> Dict[str, Any]:
    return {
        "action": action,
        "english": english,
        "hindi": hindi,
        "priority": priority,
        "classical_ref": classical_ref,
    }


# ── Reusable practical remedy templates (tape, salt, pyramid, folk + classical) ──
_TEMPLATES: Dict[str, Dict[str, Any]] = {}

def _reg(
    action: str,
    english: str,
    hindi: str,
    priority: int = 3,
    classical_ref: str = "Vastu Saar / folk upachar",
) -> str:
    _TEMPLATES[action] = _tpl(action, english, hindi, priority, classical_ref)
    return action


# Threshold / sealing / tape / swastik
_reg(
    "red_tape_threshold",
    "Paste red kumkum tape or swastik strips on the inner door frame of this zone for 48 days; replace if faded.",
    "Is zone ke andar wale darwaze ki chaukhat par 48 din ke liye laal kumkum tape ya swastik strip chipkayein; fade ho to badlein.",
    2,
    "Lal Kitab / Vastu threshold sealing",
)
_reg(
    "black_tape_neutralize",
    "If a zone is severely afflicted, paste black insulating tape on the outer threshold for 21 days ONLY under guidance, then remove.",
    "Gambhir dosh wale zone ki bahari dehri par 21 din ke liye kaali tape (margdarshan mein) chipka kar hatayein.",
    4,
    "Folk Vastu — temporary neutralisation",
)
_reg(
    "swastik_threshold_paint",
    "Paint red swastik on both sides of the threshold every Friday; wipe and renew weekly.",
    "Har Shukravar dehri ke dono taraf laal swastik banayein; haftaa-vaar saaf karke naya karein.",
    2,
    "Vastu Saar Ch.5",
)
_reg(
    "chowkat_marble",
    "Install a wooden or marble threshold (chowkat) at least 2 inches high at the room entrance.",
    "Kamre ke pravesh par kam-se-kam 2 inch uncha lakdi/sangmarmar ka chowkat lagayein.",
    1,
    "Mayamatam Ch.5",
)

# Salt / absorb / cleanse
_reg(
    "rock_salt_bowl",
    "Keep a glass bowl of rock salt (sendha namak) in the corner; replace fully every 7 days.",
    "Kone mein sendha namak ka kanch ka katora rakhein; har 7 din poora badlein.",
    2,
    "Vastu Saar Ch.11 — lavana shuddhi",
)
_reg(
    "salt_water_mop",
    "Mop the floor with rock-salt water every Saturday; discard water outside the home, not in sink.",
    "Har Shaniwar farsh ko namak-paani se pochhein; paani ghar ke bahar fenkein, sink mein nahi.",
    3,
    "Vastu Saar Ch.11",
)
_reg(
    "sea_salt_corners",
    "Place small sea-salt pouches in two opposite corners; replace monthly.",
    "Do ulte konon mein samudri namak ki potli rakhein; mahine mein badlein.",
    3,
    "Folk Vastu — ionic cleanse",
)

# Copper / pyramid / yantra / metal
_reg(
    "copper_pyramid_wall",
    "Fix a copper Vastu pyramid (9-inch preferred) on the afflicted wall, apex pointing up.",
    "Peedit deewar par tambe ka Vastu pyramid (9 inch) lagayein, shikhar upar ki ore.",
    2,
    "Vishwakarma Prakash — Pyramid upachar",
)
_reg(
    "copper_kalash_ne",
    "Place a copper kalash with clean water + pinch of turmeric in NE; change water every Tuesday.",
    "NE mein haldi mila saaf paani bhara tambe ka kalash rakhein; har Mangalwar paani badlein.",
    2,
    "Mayamatam Ch.6",
)
_reg(
    "brass_bell_entrance",
    "Hang a small brass bell at the entrance; ring once when entering the home.",
    "Pravesh par chhota peetal ki ghanti lagayein; ghar mein aate samay ek baar bajayein.",
    3,
    "Vastu Saar Ch.5",
)
_reg(
    "iron_nail_sw",
    "Drive one iron nail into the SW corner wall (symbolic weight); paint over neatly.",
    "SW kone ki deewar mein ek lohe ki keel thok dein (prateekatmak bhaar); upar rang kar dein.",
    4,
    "Lal Kitab — SW sthirata",
)

# Mirrors / glass / reflect
_reg(
    "mirror_cover_night",
    "Cover mirrors that reflect bed, stove, or altar at night with cloth; open only by day.",
    "Raat ko palang/chulha/vedi ka pratibimb dikhane wale sheeshe kapde se dhakein; din mein kholein.",
    1,
    "Vastu Saar Ch.9",
)
_reg(
    "no_broken_glass",
    "Remove cracked glass, broken tiles, and chipped mirrors immediately — they trap Rahu energy.",
    "Toota kaanch, tiles aur sheesha turant hatayein — Rahu urja phansati hai.",
    1,
    "Mayamatam Ch.7",
)

# Fire / agni / kitchen practical
_reg(
    "stove_face_east",
    "Rotate stove so cook faces East while flame burns; SE corner placement is ideal.",
    "Chulha ghumayein taaki pakate samay mukh Poorab ho; SE kona uttam.",
    1,
    "Mayamatam Ch.10",
)
_reg(
    "fire_water_partition",
    "Keep stove and sink on separate walls with minimum 2 ft stone/brick partition between.",
    "Chulha aur sink alag deewaron par; beech mein 2 ft patthar ki deewar.",
    1,
    "Brihat Samhita 53.42",
)
_reg(
    "agni_diya_se",
    "Light a small ghee diya in SE every evening before sunset.",
    "Har shaam sooryast se pehle SE mein ghee ka deepak jalayein.",
    3,
    "Mayamatam Ch.10",
)

# Water / drain / toilet
_reg(
    "toilet_lid_closed",
    "Keep toilet lid and bathroom door closed; exhaust fan on NW/W wall.",
    "Toilet seat dhakkan aur bathroom darwaza band; exhaust NW/W par.",
    2,
    "Vastu Saar Ch.11",
)
_reg(
    "leak_fix_urgent",
    "Repair any dripping tap or seepage within 48 hours — water leak in wrong zone drains wealth.",
    "Kisi bhi tap ki boond ya seepage 48 ghante mein theek karein.",
    1,
    "Brihat Samhita 53.66",
)

# Bedroom / sleep
_reg(
    "bed_head_south_east",
    "Sleep with head South or East; never North; solid headboard on South/W wall.",
    "Sir Dakshin ya Poorab; Uttar kabhi nahi; SW/W par thos headboard.",
    1,
    "Brihat Samhita 53.97",
)
_reg(
    "no_electronics_under_bed",
    "Remove chargers, phones, and metal storage from under the bed.",
    "Palang ke neeche se charger, phone aur metal saamaan hatayein.",
    2,
    "Vastu Saar Ch.9",
)
_reg(
    "rose_quartz_couple",
    "Place rose quartz in SW of bedroom for harmony (single piece, not under pillow).",
    "Bedroom ke SW mein rose quartz rakhein — dampatya samanjasya.",
    4,
    "Vastu Saar Ch.9",
)

# Pooja / spiritual
_reg(
    "deity_face_west_devotee_east",
    "Idols face West; devotee faces East or North; wooden chowki 4 fingers above floor.",
    "Murti Pashchim; bhakt Poorab/Uttar; lakdi ki chowki farsh se 4 ungli upar.",
    1,
    "Mayamatam Ch.6",
)
_reg(
    "camphor_camphor_burn",
    "Burn pure camphor (kapur) in a brass holder after evening aarti — ventilate well.",
    "Sandhya aarti ke baad peetal ki holder mein shuddh kapur jalayein — hawa aane dein.",
    3,
    "Folk Vastu — shuddhi",
)
_reg(
    "sandal_incense_ne",
    "Use sandal or guggul incense in NE only; avoid synthetic harsh scents in pooja zone.",
    "NE mein chandan/guggul dhup; pooja zone mein tez chemical scent na use karein.",
    3,
    "Vastu Saar Ch.7",
)

# Study / office desk
_reg(
    "desk_east_north",
    "Study/work desk faces East (memory) or North (clarity); back not to door.",
    "Mez ka mukh Poorab (smriti) ya Uttar (spashtata); peeth darwaze ki ore na ho.",
    1,
    "Brihat Samhita 56.3",
)
_reg(
    "green_plant_east_study",
    "Small money-plant or tulsi on East of desk; no cactus in study room.",
    "Mez ke Poorab tulsi/money-plant; study mein cactus nahi.",
    3,
    "Vastu Saar Ch.8",
)

# Living / dining
_reg(
    "sofa_back_south_wall",
    "Primary sofa with back to South wall; seating faces N or E.",
    "Mukhya sofa ki peeth Dakshin deewar; baithak N ya E ki ore.",
    2,
    "Brihat Samhita 53.84",
)
_reg(
    "dining_face_east",
    "Head of family faces East while eating; no TV facing dining table.",
    "Bhojan ke samay parivar mukhya ka mukh Poorab; mez ke saamne TV na ho.",
    2,
    "Mayamatam Ch.10",
)

# Entrance / door
_reg(
    "toran_mango_leaves",
    "Fresh mango-leaf toran above door; replace every 7–10 days.",
    "Dwar par taaza aam-patta toran; 7–10 din mein badlein.",
    2,
    "Vastu Saar Ch.5",
)
_reg(
    "door_inward_clockwise",
    "Main door opens inward clockwise; oil hinges monthly.",
    "Dwar andar ghadi disha mein khule; hinges mahine mein tel lagayein.",
    2,
    "Manasara 33.18",
)
_reg(
    "nameplate_north_east",
    "Nameplate and doorbell on N/NE side of entrance frame, well-lit.",
    "Naam-patti aur doorbell pravesh ke N/NE par, roshni ke saath.",
    3,
    "Vishwakarma Prakash 3.11",
)

# Storage / basement / garage / heavy
_reg(
    "heavy_sw_light_ne",
    "Move heaviest items to SW; keep NE/E light and empty.",
    "Sabse bhari cheez SW mein; NE/E halka aur khula rakhein.",
    1,
    "Manasara 35.42",
)
_reg(
    "basement_dehumidify",
    "Run dehumidifier in basement; bright white light on 4–6 hours daily; no sleeping there.",
    "Basement mein dehumidifier; roz 4–6 ghante safed light; wahan sona mana.",
    2,
    "Vastu Saar Ch.11 — adhogriha",
)
_reg(
    "garage_vehicle_sw",
    "Park vehicles in SW/W of garage; keep NE corner of garage empty.",
    "Gaadi SW/W mein; garage ka NE khula rakhein.",
    2,
    "Mayamatam Ch.7",
)

# Cash / locker
_reg(
    "locker_opens_north",
    "Safe/locker opens towards North; place Kuber yantra inside.",
    "Tijori Uttar ki ore khule; andar Kuber yantra rakhein.",
    1,
    "Vastu Saar Ch.8",
)

# Staircase
_reg(
    "stairs_odd_count",
    "Stair count should be odd (9,11,13); no storage under stairs for pooja/bed.",
    "Seedhiyon ki ginti visham; neeche pooja/bedroom na banayein.",
    2,
    "Mayamatam Ch.20",
)

# Colours / paint
_reg(
    "wall_colour_element",
    "Repaint walls to match zone element: NE light/yellow, SE red/orange, SW earthy, NW white/grey.",
    "Deewar zone ke tatva anusaar rang karein: NE halka/peela, SE laal, SW mitti, NW safed.",
    3,
    "Vastu Saar Ch.6",
)
_reg(
    "avoid_black_ne",
    "Never use black, dark grey, or heavy maroon in NE rooms — use white/cream/light yellow.",
    "NE kamron mein kala/gehra grey/maroon na rakhein — safed/cream/halka peela.",
    2,
    "Mayamatam Ch.6",
)

# Plants / wind / sound
_reg(
    "tulsi_ne_daily",
    "Tulsi in NE or East; water daily before sunrise.",
    "NE/Poorab mein tulsi; roz sooryoday se pehle paani.",
    3,
    "Vastu Saar Ch.10",
)
_reg(
    "wind_chime_nw",
    "Metal wind chimes on NW balcony/window — gentle sound only.",
    "NW balcony/khidki par metal wind-chime — halki awaaz.",
    4,
    "Vishwakarma Prakash 4.27",
)
_reg(
    "no_cactus_indoor",
    "Remove cactus, thorny plants, and dried flowers from interior rooms.",
    "Andar ke kamron se cactus, kaante wale paudhe aur sukhe phool hatayein.",
    2,
    "Vastu Saar Ch.10",
)

# Clutter / cleanliness / brahmasthan
_reg(
    "declutter_weekly",
    "Declutter this zone weekly; broken, rusted, unused items must exit the home.",
    "Is zone ki haftaa-vaar safai; toota/jang/lamba samay se bekara saamaan ghar se bahar.",
    2,
    "Vishwakarma Prakash 7.18",
)
_reg(
    "brahmasthan_open",
    "Keep centre (Brahmasthan) open — no pillar, sofa, or heavy object in exact centre.",
    "Kendra (Brahmasthan) khula rakhein — beech mein khambha/sofa/bhari cheez na ho.",
    1,
    "Mayamatam Ch.7",
)
_reg(
    "mop_camphor_water",
    "Once a week mop with water + pinch of camphor; no stale water buckets in room.",
    "Haftaa mein ek baar kapur-mila paani se pochha; kamre mein purana paani na rakhein.",
    3,
    "Folk Vastu",
)

# Electrical / EMF
_reg(
    "wifi_router_se",
    "Shift Wi‑Fi router and heavy electronics to SE/S zone, not NE or bedroom head-side.",
    "Wi‑Fi router/bhari electronics SE/S mein; NE ya sirhane ke paas nahi.",
    3,
    "Modern Vastu — EMF",
)
_reg(
    "extension_board_w",
    "Multi-plug boards on W/NW wall only in this room; avoid NE extension tangles.",
    "Multi-plug W/NW deewar par; NE mein taaron ka jhamela na ho.",
    3,
    "Modern Vastu",
)

# Shanti / pooja universal severe
_reg(
    "vastu_shanti_hint",
    "For severe dosha: book Vastu Shanti or Ganesh puja on auspicious Thursday/Saturday.",
    "Gambhir dosh par Vastu Shanti ya Guruvaar/Shanivar Ganesh puja karwayein.",
    4,
    "Mayamatam Ch.36",
)
_reg(
    "hanuman_sw_protection",
    "Hanuman image or yantra on South wall for protection in afflicted zones.",
    "Peedit zone ki Dakshin deewar par Hanuman pratima/yantra.",
    4,
    "Folk Vastu",
)

# Positive / ideal amplify
_reg(
    "fresh_flowers_daily",
    "Fresh flowers daily in this zone; remove wilted by sunset.",
    "Roz taaze phool; murjhaye shaam tak hatayein.",
    5,
    "Vastu Saar Ch.10",
)
_reg(
    "ghee_lamp_evening",
    "Light ghee lamp every evening in this zone at sandhya.",
    "Sandhya ko is zone mein ghee ka deepak jalayein.",
    5,
    "Mayamatam Ch.7",
)
_reg(
    "maintain_ideal",
    "Maintain cleanliness; this placement is excellent — amplify with gratitude and regular diya.",
    "Safai banaye rakhein; sthan uttam hai — kripa aur niyamit diya se badhayein.",
    5,
    "Vastu Saar Ch.10",
)

# Folk / threshold / protection / wealth symbols
_reg(
    "nimbu_mirchi_entrance",
    "Fresh lemon–chilli strand above main door; replace every Saturday morning.",
    "Mukhya dwar par taaza nimbu–mirch ki mala; har Shaniwar subah badlein.",
    3,
    "Folk Vastu — drishti shuddhi",
)
_reg(
    "ganesha_entrance",
    "Place a small Ganesha idol or sticker on the inner right of the entrance frame.",
    "Pravesh ki andar wali dehri ke daahine chhota Ganesh pratima/sticker lagayein.",
    2,
    "Vastu Saar Ch.5 — Vighnaharta",
)
_reg(
    "om_symbol_door",
    "Paint or affix Om / Swastik on the upper centre of the main door (inside).",
    "Mukhya darwaze ke andar upar beech mein Om/Swastik banayein ya chipkayein.",
    2,
    "Mayamatam Ch.5",
)
_reg(
    "nazar_battu_blue",
    "Hang a small blue evil-eye (nazar battu) above the afflicted room door; not in pooja.",
    "Peedit kamre ke darwaze par chhota neela nazar battu; pooja mein na rakhein.",
    4,
    "Folk Vastu — drishti",
)
_reg(
    "horseshoe_u_luck",
    "Iron horseshoe (U-shape up) above entrance on N/NE side only if advised for your chart.",
    "Lohe ki paidal (U upar) pravesh ke N/NE par — kundli margdarshan ke baad hi.",
    4,
    "Folk Vastu — Lakshmi",
)
_reg(
    "shree_yantra_wall",
    "Mount a brass or copper Shree Yantra on East wall of living or NE of home office.",
    "Living ki Poorab deewar ya home office ke NE par tamba/pital Shree Yantra lagayein.",
    3,
    "Vishwakarma Prakash — Shri chakra",
)
_reg(
    "rudraksha_door",
    "Five-mukhi rudraksha mala on entrance hook; replace if thread breaks.",
    "Pravesh par paanch-mukhi rudraksha ki mala; dhaga toote to badlein.",
    4,
    "Shiva Purana — upachar",
)
_reg(
    "sindoor_door_friday",
    "Apply sindoor tilak on door frame every Friday after cleaning.",
    "Har Shukravar darwaze ki dehri par safai ke baad sindoor tilak lagayein.",
    3,
    "Folk Vastu",
)
_reg(
    "raksha_sutra_door",
    "Tie a red–yellow raksha sutra on main door handle during Navratri or monthly renewal.",
    "Navratri ya mahine mein mukhya darwaze par laal–peela raksha sutra baandhein.",
    4,
    "Folk Vastu",
)
_reg(
    "rangoli_entrance",
    "Draw simple rangoli or kolam at entrance daily (dry colours); avoid blocking door swing.",
    "Pravesh par roz sada rangoli/kolam; darwaza kholne ki jagah na band karein.",
    4,
    "Vastu Saar Ch.5",
)
_reg(
    "shoes_outside_line",
    "Keep footwear in a closed rack outside or SW of entrance — never scattered in NE.",
    "Joota pravesh ke bahar ya SW band rack mein; NE mein bikhra na ho.",
    2,
    "Vastu Saar Ch.5",
)
_reg(
    "broom_hidden_sw",
    "Store broom and mop upside-down, hidden in SW store — never visible from main door.",
    "Jhadu–pocha ulta SW store mein chhupayein; mukhya darwaze se dikhe na.",
    2,
    "Folk Vastu",
)
_reg(
    "trash_bin_sw_lid",
    "Dustbin with tight lid in SW/W only; empty daily; never in NE or kitchen NE corner.",
    "Kachra dabba dhakkan wala SW/W; roz khali; NE/kitchen NE mein na.",
    2,
    "Vastu Saar Ch.11",
)

# Jars / grains / metals / yantra
_reg(
    "wheat_jar_sw",
    "Fill a clean glass jar with wheat in SW store; top up on every Amavasya.",
    "SW store mein gehun bhara saaf jar; har Amavasya bhari rakhein.",
    3,
    "Folk Vastu — anna sampatti",
)
_reg(
    "rice_bowl_ne",
    "Small bowl of unbroken rice in NE shelf; refresh weekly.",
    "NE shelf par akhand chawal ka katora; haftaa mein badlein.",
    3,
    "Mayamatam Ch.6",
)
_reg(
    "mustard_jar_sw",
    "Mustard seeds in a brown earthen pot in SW for stability (lid on).",
    "SW mein mitti ki handi mein sarson (dhakkan band) — sthirata ke liye.",
    4,
    "Lal Kitab — SW",
)
_reg(
    "green_moong_sw",
    "Green moong in a small jar in SW corner of cash/store room.",
    "Cash/store ke SW kone mein hari moong ka chhota jar.",
    4,
    "Folk Vastu — vriddhi",
)
_reg(
    "cowrie_shells_locker",
    "Eleven white cowrie shells in locker drawer with Kuber intent (not under bed).",
    "Tijori ki drawer mein 11 safed kaudi — Kuber sankalp; palang ke neeche nahi.",
    4,
    "Folk Vastu — Lakshmi",
)
_reg(
    "crystal_salt_lamp",
    "Himalayan salt lamp in afflicted zone 3–4 hours evening only; wipe weekly.",
    "Peedit zone mein Himalayan salt lamp shaam 3–4 ghante; haftaa saaf karein.",
    4,
    "Modern Vastu — ionic",
)
_reg(
    "bronze_tortoise_n",
    "Bronze tortoise figurine facing North in living N zone for career support.",
    "Living ke N zone mein peetal ki kachhua murti Uttar ki ore — karya.",
    4,
    "Folk Vastu — Kachhap",
)
_reg(
    "seven_horses_n",
    "Seven running horses painting on North wall (no water or sunset scene in bedroom).",
    "Uttar deewar par saat daudte ghode — bedroom mein paani/sunset scene na.",
    4,
    "Folk Vastu — urja",
)
_reg(
    "yellow_cloth_sw",
    "Pure yellow cotton cloth folded in SW locker or store on Thursday.",
    "Shukravar ko SW tijori/store mein shuddh peela kapda munda hua rakhein.",
    4,
    "Vastu Saar Ch.8",
)
_reg(
    "red_cloth_se",
    "Small red cotton square under stove platform or SE shelf (not in bedroom).",
    "Chulhe ke chabutre/SE shelf ke neeche chhota laal kapda — bedroom mein na.",
    3,
    "Mayamatam Ch.10",
)

# Water features / plants / septic / borewell / terrace
_reg(
    "small_aquarium_ne",
    "Only if zone is truly NE/E: small clean aquarium with 1–3 goldfish; no bedroom.",
    "Sirf NE/E zone ho to chhota saaf aquarium 1–3 goldfish; bedroom mein na.",
    4,
    "Vastu Saar Ch.6 — jal",
)
_reg(
    "bamboo_plant_se",
    "Lucky bamboo in water vase on SE window — change water weekly.",
    "SE khidki par paani wala lucky bamboo — haftaa paani badlein.",
    4,
    "Folk Vastu",
)
_reg(
    "septic_salt_monthly",
    "Pour one cup rock salt into septic tank access on Krishna Paksha Saturday (once/month).",
    "Krishna Paksha Shaniwar ko septic access mein ek katori sendha namak (mahine mein ek).",
    3,
    "Vastu Saar Ch.11",
)
_reg(
    "borewell_copper_ring",
    "Copper ring or wire around borewell cap; keep area lit and weed-free.",
    "Borewell cap par tamba ki ring/tar; jagah roshni aur weed-free rakhein.",
    2,
    "Mayamatam Ch.6",
)
_reg(
    "overhead_tank_sw_w",
    "Prefer overhead tank on SW/W structure; avoid NE tank weight.",
    "Overhead tank SW/W structure par rakhein; NE par bhaari tank na.",
    1,
    "Manasara 35.42",
)
_reg(
    "terrace_heavy_sw",
    "Heavy pots, AC outdoor unit, and storage on terrace SW/W; keep NE terrace open.",
    "Terrace par bhari gamle/AC outdoor SW/W; NE terrace khula.",
    2,
    "Vastu Saar Ch.7",
)
_reg(
    "fitkari_mop_water",
    "Monthly mop with water + pinch of alum (fitkari) in afflicted water zones.",
    "Peedit jal zone mein mahine mein fitkari-mila paani se pochha.",
    3,
    "Folk Vastu — shuddhi",
)
_reg(
    "clove_cinnamon_bowl",
    "Small open bowl of cloves + cinnamon sticks in store/entrance (refresh monthly).",
    "Store/pravesh mein laung–dalchini ka khula katora; mahine mein badlein.",
    4,
    "Folk Vastu",
)
_reg(
    "camphor_closet",
    "Two camphor tablets in wardrobe corners; replace when scent fades.",
    "Almari ke konon mein do kapur ki goli; khushboo kam ho to badlein.",
    3,
    "Folk Vastu",
)
_reg(
    "guest_room_fresh_linen",
    "Guest room: white/cream linen, no shoes inside, single fresh flower on East shelf.",
    "Mehman kamra: safed/cream bistar, andar joota na, Poorab shelf par ek taaza phool.",
    4,
    "Vastu Saar Ch.9",
)
_reg(
    "servant_room_bright_light",
    "Servant/helper room: bright white LED, no clutter under bed, door closes fully.",
    "Naukar kamra: chamakti safed LED, palang ke neeche samaan na, darwaza poora band.",
    3,
    "Vastu Saar Ch.9",
)
_reg(
    "clock_north_wall",
    "Wall clocks on N or E walls only; avoid South wall clocks in bedroom/living.",
    "Ghadi sirf N ya E deewar par; bedroom/living ki Dakshin deewar par na.",
    3,
    "Vastu Saar Ch.8",
)
_reg(
    "bilva_leaves_shiv",
    "Fresh bilva leaves on Shivling or image on Mondays in pooja zone only.",
    "Pooja zone mein Somvar ko Shivling/pratima par taaze bel-patra.",
    4,
    "Shiva Purana",
)
_reg(
    "crystal_pyramid_shelf",
    "Clear quartz or crystal pyramid on study shelf East — not pointed at bed.",
    "Study shelf Poorab par crystal pyramid — palang ki ore point na ho.",
    4,
    "Modern Vastu",
)
_reg(
    "havan_kund_se_outdoor",
    "Perform small agnihotra/havan in SE open yard on Poornima (smoke away from home).",
    "Poornima par SE khule aangan mein chhota havan — dhuaan ghar se door.",
    4,
    "Mayamatam Ch.36",
)

# ── Per (room, verdict) template ID lists (8–12 each → 500+ resolved picks) ─────
def _plan_for(room: str, verdict: str) -> List[str]:
    """Return ordered template action IDs for room+verdict."""
    r = room
    v = verdict

    # Universal tail by severity
    if v == "Avoid":
        universal = [
            "leak_fix_urgent", "no_broken_glass", "declutter_weekly",
            "rock_salt_bowl", "copper_pyramid_wall", "red_tape_threshold",
            "vastu_shanti_hint", "nazar_battu_blue", "fitkari_mop_water",
            "trash_bin_sw_lid", "sea_salt_corners",
        ]
    elif v == "Adjustment Needed":
        universal = [
            "declutter_weekly", "salt_water_mop", "wall_colour_element",
            "swastik_threshold_paint", "mop_camphor_water", "black_tape_neutralize",
            "clove_cinnamon_bowl", "camphor_closet",
        ]
    elif v == "Acceptable":
        universal = [
            "declutter_weekly", "tulsi_ne_daily", "fresh_flowers_daily",
            "rangoli_entrance", "bamboo_plant_se",
        ]
    else:
        universal = [
            "maintain_ideal", "fresh_flowers_daily", "ghee_lamp_evening",
            "shree_yantra_wall", "ganesha_entrance",
        ]

    kitchen = {
        "Avoid": [
            "stove_face_east", "fire_water_partition", "copper_kalash_ne",
            "avoid_black_ne", "agni_diya_se", "red_cloth_se",
        ],
        "Adjustment Needed": ["stove_face_east", "fire_water_partition", "wall_colour_element", "red_cloth_se"],
        "Acceptable": ["agni_diya_se", "declutter_weekly", "clove_cinnamon_bowl"],
        "Ideal": ["maintain_ideal", "agni_diya_se"],
    }
    bedroom = {
        "Avoid": [
            "bed_head_south_east", "mirror_cover_night", "no_electronics_under_bed",
            "avoid_black_ne",
        ],
        "Adjustment Needed": ["bed_head_south_east", "mirror_cover_night", "wall_colour_element"],
        "Acceptable": ["rose_quartz_couple", "declutter_weekly"],
        "Ideal": ["maintain_ideal", "fresh_flowers_daily"],
    }
    pooja = {
        "Avoid": ["deity_face_west_devotee_east", "avoid_black_ne", "brahmasthan_open"],
        "Adjustment Needed": [
            "deity_face_west_devotee_east", "sandal_incense_ne", "camphor_camphor_burn",
            "bilva_leaves_shiv",
        ],
        "Acceptable": ["copper_kalash_ne", "tulsi_ne_daily", "havan_kund_se_outdoor"],
        "Ideal": ["ghee_lamp_evening", "maintain_ideal", "bilva_leaves_shiv"],
    }
    toilet = {
        "Avoid": ["rock_salt_bowl", "toilet_lid_closed", "leak_fix_urgent", "copper_pyramid_wall"],
        "Adjustment Needed": ["toilet_lid_closed", "salt_water_mop", "sea_salt_corners"],
        "Acceptable": ["declutter_weekly", "mop_camphor_water"],
        "Ideal": ["maintain_ideal"],
    }
    bathroom = {
        "Avoid": ["leak_fix_urgent", "rock_salt_bowl", "toilet_lid_closed"],
        "Adjustment Needed": ["salt_water_mop", "mop_camphor_water", "declutter_weekly"],
        "Acceptable": ["declutter_weekly"],
        "Ideal": ["maintain_ideal"],
    }
    study = {
        "Avoid": ["desk_east_north", "wifi_router_se", "no_cactus_indoor"],
        "Adjustment Needed": ["desk_east_north", "green_plant_east_study"],
        "Acceptable": ["green_plant_east_study", "tulsi_ne_daily"],
        "Ideal": ["ghee_lamp_evening", "maintain_ideal"],
    }
    living = {
        "Avoid": ["sofa_back_south_wall", "heavy_sw_light_ne", "brahmasthan_open"],
        "Adjustment Needed": ["sofa_back_south_wall", "wall_colour_element", "wifi_router_se"],
        "Acceptable": ["fresh_flowers_daily", "tulsi_ne_daily"],
        "Ideal": ["ghee_lamp_evening", "brahmasthan_open"],
    }
    dining = {
        "Avoid": ["dining_face_east", "mirror_cover_night", "brahmasthan_open"],
        "Adjustment Needed": ["dining_face_east", "declutter_weekly"],
        "Acceptable": ["fresh_flowers_daily"],
        "Ideal": ["maintain_ideal"],
    }
    store = {
        "Avoid": ["heavy_sw_light_ne", "declutter_weekly", "no_broken_glass"],
        "Adjustment Needed": ["heavy_sw_light_ne", "declutter_weekly"],
        "Acceptable": ["declutter_weekly"],
        "Ideal": ["maintain_ideal"],
    }
    entrance = {
        "Avoid": [
            "chowkat_marble", "toran_mango_leaves", "door_inward_clockwise",
            "nameplate_north_east", "ganesha_entrance", "shoes_outside_line",
        ],
        "Adjustment Needed": [
            "swastik_threshold_paint", "toran_mango_leaves", "brass_bell_entrance",
            "nimbu_mirchi_entrance", "om_symbol_door",
        ],
        "Acceptable": ["fresh_flowers_daily", "ghee_lamp_evening", "rangoli_entrance"],
        "Ideal": ["maintain_ideal", "fresh_flowers_daily", "ganesha_entrance"],
    }
    staircase = {
        "Avoid": ["stairs_odd_count", "heavy_sw_light_ne", "brahmasthan_open"],
        "Adjustment Needed": ["stairs_odd_count", "declutter_weekly"],
        "Acceptable": ["declutter_weekly"],
        "Ideal": ["maintain_ideal"],
    }
    balcony = {
        "Avoid": ["heavy_sw_light_ne", "no_cactus_indoor", "declutter_weekly"],
        "Adjustment Needed": ["tulsi_ne_daily", "wind_chime_nw"],
        "Acceptable": ["wind_chime_nw", "fresh_flowers_daily"],
        "Ideal": ["maintain_ideal"],
    }
    basement = {
        "Avoid": ["basement_dehumidify", "rock_salt_bowl", "heavy_sw_light_ne", "avoid_black_ne"],
        "Adjustment Needed": ["basement_dehumidify", "salt_water_mop", "wall_colour_element"],
        "Acceptable": ["declutter_weekly", "mop_camphor_water"],
        "Ideal": ["maintain_ideal"],
    }
    garage = {
        "Avoid": ["garage_vehicle_sw", "declutter_weekly", "leak_fix_urgent"],
        "Adjustment Needed": ["garage_vehicle_sw", "wall_colour_element"],
        "Acceptable": ["declutter_weekly"],
        "Ideal": ["maintain_ideal"],
    }
    cash = {
        "Avoid": ["locker_opens_north", "copper_pyramid_wall", "mirror_cover_night", "cowrie_shells_locker"],
        "Adjustment Needed": ["locker_opens_north", "declutter_weekly", "green_moong_sw"],
        "Acceptable": ["fresh_flowers_daily", "wheat_jar_sw"],
        "Ideal": ["maintain_ideal", "yellow_cloth_sw"],
    }
    guest = {
        "Avoid": ["guest_room_fresh_linen", "mirror_cover_night", "no_electronics_under_bed"],
        "Adjustment Needed": ["guest_room_fresh_linen", "wall_colour_element", "camphor_closet"],
        "Acceptable": ["fresh_flowers_daily", "declutter_weekly"],
        "Ideal": ["maintain_ideal"],
    }
    terrace_rm = {
        "Avoid": ["terrace_heavy_sw", "heavy_sw_light_ne", "no_cactus_indoor"],
        "Adjustment Needed": ["terrace_heavy_sw", "wind_chime_nw", "declutter_weekly"],
        "Acceptable": ["tulsi_ne_daily", "fresh_flowers_daily"],
        "Ideal": ["maintain_ideal"],
    }
    septic_rm = {
        "Avoid": ["septic_salt_monthly", "rock_salt_bowl", "leak_fix_urgent", "toilet_lid_closed"],
        "Adjustment Needed": ["septic_salt_monthly", "salt_water_mop", "fitkari_mop_water"],
        "Acceptable": ["declutter_weekly", "mop_camphor_water"],
        "Ideal": ["maintain_ideal"],
    }
    borewell_rm = {
        "Avoid": ["borewell_copper_ring", "leak_fix_urgent", "rock_salt_bowl"],
        "Adjustment Needed": ["borewell_copper_ring", "copper_kalash_ne", "rice_bowl_ne"],
        "Acceptable": ["small_aquarium_ne", "tulsi_ne_daily"],
        "Ideal": ["maintain_ideal"],
    }
    tank_rm = {
        "Avoid": ["overhead_tank_sw_w", "leak_fix_urgent", "heavy_sw_light_ne"],
        "Adjustment Needed": ["overhead_tank_sw_w", "iron_nail_sw", "declutter_weekly"],
        "Acceptable": ["declutter_weekly"],
        "Ideal": ["maintain_ideal"],
    }
    servant_rm = {
        "Avoid": ["servant_room_bright_light", "declutter_weekly", "no_broken_glass"],
        "Adjustment Needed": ["servant_room_bright_light", "wall_colour_element"],
        "Acceptable": ["declutter_weekly"],
        "Ideal": ["maintain_ideal"],
    }

    maps = {
        "kitchen": kitchen, "bedroom": bedroom, "master_bedroom": bedroom,
        "pooja": pooja, "pooja_room": pooja, "toilet": toilet, "bathroom": bathroom,
        "study": study, "home_office": study, "living": living, "living_room": living,
        "dining": dining, "dining_room": dining, "store": store, "entrance": entrance,
        "main_door": entrance, "staircase": staircase, "balcony": balcony,
        "basement": basement, "garage": garage, "cash_locker": cash,
        "guest_room": guest, "terrace": terrace_rm, "overhead_tank": tank_rm,
        "septic": septic_rm, "borewell": borewell_rm, "servant_room": servant_rm,
    }

    specific = (maps.get(r) or maps.get("living", living)).get(v, universal[:6])
    # Merge specific first, then universal; dedupe preserve order
    seen: set[str] = set()
    out: List[str] = []
    for aid in specific + universal:
        if aid not in seen and aid in _TEMPLATES:
            seen.add(aid)
            out.append(aid)
    return out


# Pre-build PLAN dict for stats
PLAN: Dict[Tuple[str, str], List[str]] = {}
for _room in _ALL_HOME_ROOMS:
    for _v in _VERDICTS:
        PLAN[(_room, _v)] = _plan_for(_room, _v)


def expand_catalog(room_type: str, verdict: str) -> List[Dict[str, Any]]:
    """Resolve catalog templates for normalized room + verdict."""
    rt = (room_type or "").strip().lower().replace(" ", "_").replace("-", "_")
    v = verdict if verdict in _VERDICTS else "Acceptable"
    ids = PLAN.get((rt, v)) or _plan_for(rt, v)
    out: List[Dict[str, Any]] = []
    for aid in ids:
        t = _TEMPLATES.get(aid)
        if t:
            out.append(dict(t))
    out.sort(key=lambda x: int(x.get("priority", 99)))
    return out


def catalog_stats() -> Dict[str, int]:
    picks = sum(len(v) for v in PLAN.values())
    return {
        "templates": len(_TEMPLATES),
        "room_verdict_slots": len(PLAN),
        "total_picks": picks,
    }
