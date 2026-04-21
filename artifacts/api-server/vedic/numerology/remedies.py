"""
Tier 3 — Personalized Remedies Engine for Life Mastery Report.

Pure decision logic. Takes existing engine outputs (Tier 1 extended
numerology + Tier 2 vedic_classical bundle) and returns a structured
remedy plan tailored to the native:

  1. Weakest planet (lowest score in Navagraha)         → strengthen
  2. Current Mahadasha lord                              → align with active period
  3. Sadhe Sati / Dhaiya status                          → mitigate Saturn pressure (if active)
  4. Karmic Debt(s) (13/14/16/19)                        → payback practices
  5. Karmic Lessons (missing 1-9)                        → conscious development
  6. Driver–Conductor harmony                            → daily-life balance
  7. Personal Year theme                                 → action mode for current year
  8. Ishta Devata 21-day sadhana                         → spiritual anchor
  9. Weekly remedies dashboard                           → consolidated Mon-Sun schedule

NO new astronomical computation here — this module is a structured
lookup + decision engine over data that's already been calculated.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Any, Dict, List, Optional


# ─── Per-planet remedy library ──────────────────────────────────────────────
# Each entry is a deterministic prescription: mantra, day-of-week, count,
# gem, charity, color, direction, fast (if any). Counts follow classical
# numerology (108 multipliers) and Lal Kitab heuristics.
PLANET_REMEDIES: Dict[str, Dict[str, Any]] = {
    "Sun": {
        "mantra": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "short_mantra": "Om Suryaya Namah",
        "day": "Sunday",
        "count": 7000,         # 108 × ~65 over 40 days, or 7000 lifetime
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Ruby (Manik)",
        "metal": "Copper / Gold",
        "color": "Red / Orange",
        "direction": "East",
        "best_time": "Sunrise (within 30 min)",
        "charity": "Wheat, jaggery, copper to a father-figure or priest on Sunday morning",
        "fast": "Sunday — eat once after sunrise; avoid salt",
        "do": "Surya Namaskar 12 rounds at sunrise; offer Arghya (water with red flowers)",
        "avoid": "Disrespecting father / boss; alcohol on Sunday",
    },
    "Moon": {
        "mantra": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "short_mantra": "Om Chandraya Namah",
        "day": "Monday",
        "count": 11000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Pearl (Moti)",
        "metal": "Silver",
        "color": "White / Cream",
        "direction": "North-West",
        "best_time": "Evening after moonrise",
        "charity": "Rice, milk, white cloth to mother-figure or girl child on Monday",
        "fast": "Monday — fruit-only; offer milk on Shivlinga",
        "do": "Drink water from silver glass; meditate looking at moon for 11 min",
        "avoid": "Late-night arguments; emotional reactivity",
    },
    "Mars": {
        "mantra": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "short_mantra": "Om Angarakaya Namah",
        "day": "Tuesday",
        "count": 10000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Red Coral (Moonga)",
        "metal": "Copper",
        "color": "Red",
        "direction": "South",
        "best_time": "Sunrise on Tuesday",
        "charity": "Red lentils (masoor dal), red cloth to a soldier or labourer on Tuesday",
        "fast": "Tuesday — no salt after sunset",
        "do": "Hanuman Chalisa 7 paths; physical exercise daily",
        "avoid": "Anger outbursts; non-veg on Tuesday",
    },
    "Mercury": {
        "mantra": "Om Braam Breem Braum Sah Budhaya Namah",
        "short_mantra": "Om Budhaya Namah",
        "day": "Wednesday",
        "count": 9000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Emerald (Panna)",
        "metal": "Bronze",
        "color": "Green",
        "direction": "North",
        "best_time": "Morning before noon",
        "charity": "Green moong dal, books, pens to a poor student on Wednesday",
        "fast": "Wednesday — fruit-only; donate to Ganesha temple",
        "do": "Read/write for 30 min; Vishnu Sahasranama on Wednesday",
        "avoid": "Lying, gambling, gossip on Wednesday",
    },
    "Jupiter": {
        "mantra": "Om Graam Greem Graum Sah Gurave Namah",
        "short_mantra": "Om Brihaspataye Namah",
        "day": "Thursday",
        "count": 19000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Yellow Sapphire (Pukhraj)",
        "metal": "Gold",
        "color": "Yellow",
        "direction": "North-East",
        "best_time": "Morning",
        "charity": "Yellow dal (chana), turmeric, books to a teacher or temple on Thursday",
        "fast": "Thursday — yellow food only; avoid salt",
        "do": "Vishnu Sahasranama; learn something new every Thursday",
        "avoid": "Disrespecting teachers / elders; non-veg on Thursday",
    },
    "Venus": {
        "mantra": "Om Draam Dreem Draum Sah Shukraya Namah",
        "short_mantra": "Om Shukraya Namah",
        "day": "Friday",
        "count": 16000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Diamond / White Sapphire",
        "metal": "Silver / Platinum",
        "color": "White / Pink",
        "direction": "South-East",
        "best_time": "Sunrise on Friday",
        "charity": "White sweets, silver, perfume to a young woman on Friday",
        "fast": "Friday — sweet-only fast; offer kheer to Lakshmi",
        "do": "Sri Suktam path; create something beautiful (art/music) on Friday",
        "avoid": "Conflict in relationships; harsh words to spouse",
    },
    "Saturn": {
        "mantra": "Om Praam Preem Praum Sah Shanaye Namah",
        "short_mantra": "Om Shanaicharaya Namah",
        "day": "Saturday",
        "count": 23000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Blue Sapphire (Neelam) — TEST 3 days first",
        "metal": "Iron",
        "color": "Black / Dark Blue",
        "direction": "West",
        "best_time": "Sunset on Saturday",
        "charity": "Black sesame (til), mustard oil, iron to a poor labourer on Saturday evening",
        "fast": "Saturday — one meal after sunset; no salt",
        "do": "Hanuman Chalisa 11 paths; light mustard-oil diya under Peepal tree",
        "avoid": "Ego with employees; cutting nails/hair on Saturday",
    },
    "Rahu": {
        "mantra": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
        "short_mantra": "Om Rahave Namah",
        "day": "Saturday (with Saturn)",
        "count": 18000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Hessonite (Gomedh)",
        "metal": "Mixed-metal alloy (Ashtadhatu)",
        "color": "Smoky Grey",
        "direction": "South-West",
        "best_time": "Rahu Kaal of any day (avoid important work then)",
        "charity": "Black blanket, mustard oil to a leper or beggar; feed crows",
        "fast": "Saturday — observe silence for 1 hour",
        "do": "Durga Saptashati path; donate to outcasts/refugees",
        "avoid": "Shortcuts, deception, foreign affairs during Rahu Kaal",
    },
    "Ketu": {
        "mantra": "Om Sraam Sreem Sraum Sah Ketave Namah",
        "short_mantra": "Om Ketave Namah",
        "day": "Tuesday (with Mars)",
        "count": 17000,
        "daily_count": 108,
        "duration_days": 40,
        "gem": "Cat's Eye (Lehsunia)",
        "metal": "Mixed-metal alloy (Ashtadhatu)",
        "color": "Multi-colour / Brown",
        "direction": "None (Ketu is dik-heen)",
        "best_time": "Pradosh kaal (twilight)",
        "charity": "Striped blanket to a sadhu; feed dogs",
        "fast": "Tuesday — fruit-only; donate to Ganesha temple",
        "do": "Ganesh Atharvashirsha; spend time alone in nature once a week",
        "avoid": "Sudden impulsive decisions; isolation that becomes withdrawal",
    },
}


# ─── Karmic Debt remedies (13/14/16/19) ─────────────────────────────────────
KARMIC_DEBT_REMEDIES: Dict[int, Dict[str, str]] = {
    13: {
        "theme": "Laziness from past life — must rebuild through patient hard work.",
        "remedy": "Wake before sunrise daily for 40 days. Complete one tedious task to perfection each day without shortcuts. Avoid blaming circumstances.",
        "deity": "Lord Hanuman (sustained effort)",
        "mantra": "Hanuman Chalisa daily",
    },
    14: {
        "theme": "Misuse of freedom in past life — must master self-discipline now.",
        "remedy": "Pick ONE addiction (phone, sugar, alcohol, gossip) and abstain for 21 days. Create rigid daily routine — same wake/eat/sleep times. Travel mindfully, not escapistically.",
        "deity": "Lord Shiva (master of senses)",
        "mantra": "Om Namah Shivaya — 108× daily",
    },
    16: {
        "theme": "Ego-fall — pride from past life must be dissolved through humility.",
        "remedy": "Daily 15 min of selfless service (anonymous donation, helping a stranger, cleaning a temple/public space). Never take credit publicly for 40 days. Listen more than you speak.",
        "deity": "Lord Vishnu (preserver, balancer)",
        "mantra": "Vishnu Sahasranama on Thursday",
    },
    19: {
        "theme": "Misuse of power in past life — must learn that true strength is shared.",
        "remedy": "Mentor someone weaker than you for 40 days. Refuse one easy win where you'd normally dominate. Give credit to a junior publicly. Avoid lawsuits/confrontations during this debt cycle.",
        "deity": "Lord Surya (just power)",
        "mantra": "Aditya Hridaya Stotra on Sunday",
    },
}


# ─── Karmic Lessons (missing digits 1-9 in name) ────────────────────────────
KARMIC_LESSON_REMEDIES: Dict[int, Dict[str, str]] = {
    1: {"quality": "Independence, leadership, initiative",
        "practice": "Make ONE decision daily without consulting anyone. Lead a small group activity weekly."},
    2: {"quality": "Cooperation, patience, sensitivity",
        "practice": "Practice active listening — let others finish 3 full sentences before responding. Work in pairs/teams."},
    3: {"quality": "Self-expression, creativity, joy",
        "practice": "Write/draw/sing for 15 min daily — share output once a week with someone."},
    4: {"quality": "Discipline, foundation, hard work",
        "practice": "Build ONE habit (5 min/day) and track it for 90 days. Organise your physical workspace weekly."},
    5: {"quality": "Adaptability, freedom, courage to change",
        "practice": "Take ONE new route / try ONE new food / meet ONE new person every week for 40 days."},
    6: {"quality": "Responsibility, family-care, service",
        "practice": "Take charge of one family/community duty fully for 40 days — cooking, elder-care, teaching a child."},
    7: {"quality": "Inner work, study, spiritual depth",
        "practice": "30 min daily of reading/meditation/journalling in solitude. Visit a temple/library weekly."},
    8: {"quality": "Material mastery, money-discipline, authority",
        "practice": "Track every rupee spent for 40 days. Make ONE decisive financial decision weekly. Build a small saving habit."},
    9: {"quality": "Compassion, letting-go, universal love",
        "practice": "Anonymous charity weekly (any amount). Forgive ONE person you've held resentment against. Volunteer monthly."},
}


# ─── Personal Year remedies (1-9) ───────────────────────────────────────────
PERSONAL_YEAR_REMEDIES: Dict[int, Dict[str, str]] = {
    1: {"theme": "Seed year — new beginnings",
        "do": "Start ONE major project. Update plans, branding, image. Take initiative — don't wait for permission.",
        "avoid": "Hesitation, dependency, recycling old projects."},
    2: {"theme": "Patience year — partnerships & details",
        "do": "Build relationships, listen, refine details. Form key partnerships. Cultivate diplomacy.",
        "avoid": "Forcing outcomes, going alone, big risks."},
    3: {"theme": "Expression year — creativity & visibility",
        "do": "Speak/write/perform publicly. Network actively. Express your gifts.",
        "avoid": "Scattering energy, skipping discipline, gossip."},
    4: {"theme": "Foundation year — work & discipline",
        "do": "Build systems, work hard, finalise legal/financial structures. Real-estate decisions favoured.",
        "avoid": "Chasing shortcuts, recreational excess, neglecting health."},
    5: {"theme": "Change year — freedom & movement",
        "do": "Travel, change jobs/cities if needed, embrace new experiences, sell old.",
        "avoid": "Major long-term commitments (marriage/loans), addictions, recklessness."},
    6: {"theme": "Responsibility year — family & home",
        "do": "Beautify home, marriage/birth/family commitments, mentor others, give-and-receive care.",
        "avoid": "Selfishness, avoiding domestic duties, perfectionism with loved ones."},
    7: {"theme": "Reflection year — inner work & study",
        "do": "Study deeply, meditate, retreat, journal, do solo travel/pilgrimage. Heal old wounds.",
        "avoid": "Forced socialising, big public moves, ignoring intuition."},
    8: {"theme": "Power year — money, career, recognition",
        "do": "Negotiate aggressively, ask for raise/promotion, invest, claim authority. Big-money year.",
        "avoid": "Greed, ego-conflicts with elders, impulsive spending."},
    9: {"theme": "Completion year — release & service",
        "do": "End what's outdated — relationships, jobs, possessions. Give freely. Travel for closure.",
        "avoid": "Starting brand-new ventures (do that next year), holding grudges, hoarding."},
}


# ─── Conductor (life-path style sum of full DOB without master) ─────────────
def _digits(s) -> List[int]:
    return [int(c) for c in str(s) if c.isdigit()]


def _reduce_no_master(n: int) -> int:
    n = abs(int(n))
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def compute_driver_conductor(dob: date) -> Dict[str, int]:
    """Driver = day of birth reduced. Conductor = full DOB sum reduced."""
    driver = _reduce_no_master(dob.day)
    conductor = _reduce_no_master(sum(_digits(dob.strftime("%d%m%Y"))))
    return {"driver": driver, "conductor": conductor}


# ─── Driver–Conductor harmony lookup ────────────────────────────────────────
# Friendly / neutral / hostile based on classical Indian numerology.
_NUM_FRIENDS = {
    1: {1, 2, 3, 5, 9},   2: {1, 2, 3, 5, 9},   3: {1, 2, 3, 5, 6, 7, 9},
    4: {1, 5, 6, 7, 8},   5: {1, 2, 3, 4, 5, 6, 7, 8, 9},  # 5 is universal friend
    6: {3, 4, 5, 6, 8, 9}, 7: {1, 3, 4, 5, 6, 7},
    8: {3, 4, 5, 6, 8},   9: {1, 2, 3, 5, 6, 7, 9},
}


def driver_conductor_harmony(driver: int, conductor: int) -> Dict[str, str]:
    if driver == conductor:
        verdict = "perfect"
        note = (f"Driver = Conductor = {driver}. Single-pointed personality. "
                f"Strength: clarity. Watch: rigidity, lack of versatility.")
    elif conductor in _NUM_FRIENDS.get(driver, set()):
        verdict = "friendly"
        note = (f"Driver {driver} and Conductor {conductor} are friendly numbers. "
                f"Inner self and outer life support each other — natural flow.")
    else:
        verdict = "tense"
        note = (f"Driver {driver} and Conductor {conductor} pull in different "
                f"directions. You may feel inner self vs. outer life mismatch. "
                f"Bridge them through conscious daily practice.")
    return {"verdict": verdict, "note": note,
            "driver": driver, "conductor": conductor}


# ─── Sadhe Sati / Dhaiya additional Saturn remedies ─────────────────────────
SADHE_SATI_REMEDIES: Dict[str, str] = {
    "Rising":   "Phase 1 — pressure builds in mind/health. Read Hanuman Chalisa Saturday morning. Donate mustard oil + black sesame at Shani temple. Keep diet light.",
    "Peak":     "Phase 2 — pressure on home/finances. Light a mustard-oil diya at Peepal tree every Saturday evening. Avoid lending money. Serve elders.",
    "Setting":  "Phase 3 — career/work pressure. Recite Shani Stotram Saturday. Work with discipline, never cheat. The exit phase rewards patience.",
    "Dhaiya":   "Small Panoti — focused pressure (~2.5 yrs). Monthly Hanuman temple visit. Donate iron utensils. Avoid disrespecting employees/juniors.",
    "Clear":    "Saturn is currently NOT in Sadhe Sati / Dhaiya for you. This is preventive maintenance — Hanuman Chalisa weekly keeps Shani aligned for the next cycle.",
}


# ─── Master compute ─────────────────────────────────────────────────────────
def compute_remedies_bundle(name: str, dob: str, tob: Optional[str],
                            driver: int) -> Dict[str, Any]:
    """Build the full Tier 3 remedies plan from existing engine outputs."""
    from vedic.numerology.extended import compute_extended_numerology
    from vedic.numerology.vedic_classical import compute_tier2_bundle
    from vedic.numerology import core_ext as _cx

    # Parse dob
    try:
        dob_obj = datetime.strptime(dob, "%Y-%m-%d").date()
    except Exception:
        return {"available": False, "reason": "DOB unparseable"}

    # Pull existing engine outputs
    ext = compute_extended_numerology({"name": name, "dob": dob})
    if not ext.get("available"):
        return {"available": False, "reason": "extended numerology failed"}
    t2 = compute_tier2_bundle(dob, tob, driver)

    # ── 1. Weakest planet ────────────────────────────────────────
    strengths: Dict[str, int] = t2.get("navagraha_strengths", {})
    if strengths:
        weakest_planet, weakest_score = min(strengths.items(), key=lambda kv: kv[1])
        weakest_remedy = PLANET_REMEDIES.get(weakest_planet, {})
    else:
        weakest_planet, weakest_score, weakest_remedy = None, None, {}

    # ── 2. Current Mahadasha lord remedy ─────────────────────────
    mdash = t2.get("mahadasha", {})
    cur = mdash.get("current") or {}
    dasha_lord = cur.get("lord")
    dasha_remedy = PLANET_REMEDIES.get(dasha_lord, {}) if dasha_lord else {}
    dasha_years_left = cur.get("years_remaining")

    # ── 3. Sadhe Sati remedy ─────────────────────────────────────
    ssati = t2.get("sadhe_sati", {})
    def _normalize_phase(raw: str) -> str:
        """Map engine phase labels (e.g. 'First Dhaiya (rising)', 'Peak (2nd Dhaiya)',
        'Setting (3rd Dhaiya)') to remedy-table keys (Rising/Peak/Setting)."""
        if not raw:
            return "Peak"
        low = raw.lower()
        if "rising" in low or "first" in low or "1st" in low:
            return "Rising"
        if "setting" in low or "third" in low or "3rd" in low:
            return "Setting"
        return "Peak"

    if ssati.get("available"):
        if ssati.get("active"):
            ssati_key = _normalize_phase(ssati.get("phase") or "")
        elif ssati.get("small_panoti"):
            ssati_key = "Dhaiya"
        else:
            ssati_key = "Clear"
    else:
        ssati_key = "Clear"
    ssati_remedy = SADHE_SATI_REMEDIES.get(ssati_key, SADHE_SATI_REMEDIES["Clear"])

    # ── 4. Karmic debt remedies ──────────────────────────────────
    kd = ext.get("karmic_debt", {})
    debt_remedies: List[Dict[str, Any]] = []
    if kd.get("has_karmic_debt"):
        for d in kd.get("debts", []):
            # extended.py returns list of dicts with 'value' or just ints; handle both
            num = d.get("value") if isinstance(d, dict) else d
            try:
                num = int(num)
            except Exception:
                continue
            spec = KARMIC_DEBT_REMEDIES.get(num)
            if spec:
                debt_remedies.append({"debt": num, **spec})

    # ── 5. Karmic lessons ────────────────────────────────────────
    lessons = _cx.karmic_lessons(name)
    lesson_remedies = [{"missing": n, **KARMIC_LESSON_REMEDIES[n]}
                       for n in lessons if n in KARMIC_LESSON_REMEDIES]

    # ── 6. Driver-Conductor harmony ─────────────────────────────
    dc_nums = compute_driver_conductor(dob_obj)
    harmony = driver_conductor_harmony(dc_nums["driver"], dc_nums["conductor"])

    # ── 7. Personal year remedy ──────────────────────────────────
    pc = ext.get("personal_cycles", {})
    py = int(pc.get("personal_year", 0) or 0)
    py_root = _reduce_no_master(py) if py else 0
    py_remedy = PERSONAL_YEAR_REMEDIES.get(py_root, {})
    current_year = datetime.now().year

    # ── 8. Ishta Devata sadhana ──────────────────────────────────
    deity_info = t2.get("ishta_devata", {})
    ishta_planet = deity_info.get("planet")
    ishta_remedy = PLANET_REMEDIES.get(ishta_planet, {}) if ishta_planet else {}
    ishta_sadhana = {
        "deity": deity_info.get("deity"),
        "yantra": deity_info.get("yantra"),
        "planet": ishta_planet,
        "mantra": ishta_remedy.get("short_mantra") or ishta_remedy.get("mantra"),
        "daily_count": 108,
        "duration_days": 21,
        "best_time": ishta_remedy.get("best_time", "Brahma Muhurta (4-6 AM)"),
        "color": ishta_remedy.get("color"),
        "direction": ishta_remedy.get("direction"),
    }

    # ── 9. Weekly remedies dashboard ─────────────────────────────
    DAY_PLANET = [("Monday", "Moon"), ("Tuesday", "Mars"), ("Wednesday", "Mercury"),
                  ("Thursday", "Jupiter"), ("Friday", "Venus"),
                  ("Saturday", "Saturn"), ("Sunday", "Sun")]
    weekly = []
    for day, planet in DAY_PLANET:
        spec = PLANET_REMEDIES[planet]
        weekly.append({
            "day": day,
            "planet": planet,
            "mantra": spec["short_mantra"],
            "color": spec["color"],
            "charity": spec["charity"].split(" to ")[0],  # short form
        })

    return {
        "available": True,
        "name": name,
        "weakest_planet": {
            "planet": weakest_planet,
            "score": weakest_score,
            **weakest_remedy,
        },
        "current_dasha_remedy": {
            "lord": dasha_lord,
            "years_left": dasha_years_left,
            **dasha_remedy,
        },
        "sadhe_sati": {
            "key": ssati_key,
            "remedy": ssati_remedy,
            "active": bool(ssati.get("active")),
            "small_panoti": bool(ssati.get("small_panoti")),
        },
        "karmic_debts": debt_remedies,        # list (may be empty)
        "karmic_lessons": lesson_remedies,    # list (may be empty if name has all 9)
        "harmony": harmony,
        "personal_year": {
            "year_number": py,
            "current_year": current_year,
            **py_remedy,
        },
        "ishta_sadhana": ishta_sadhana,
        "weekly_dashboard": weekly,
    }
