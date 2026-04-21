"""
New Sections Builder — Sections 1, 8, 10, 14, 18, 19, 20, 21 of the
21-section Hinglish Face Intelligence Report.

These sections derive purely from the projected `engines` dict and the
13 base sections built by `section_mapper`. No new image processing.

All output is in conversational Hinglish to match the ₹1499 report tone.
"""
from __future__ import annotations
from typing import Dict, List, Any


# ──────────────────────────── helpers ────────────────────────────────────
def _g(d: Dict, *keys, default=None):
    cur = d or {}
    for k in keys:
        if not isinstance(cur, dict): return default
        cur = cur.get(k)
        if cur is None: return default
    return cur


def _num(x, default: float = 50.0) -> float:
    try:
        v = float(x)
        if v != v: return default
        return v
    except Exception:
        return default


def _ocean(engines: Dict) -> Dict[str, float]:
    s = _g(engines, "personality", "ocean_summary_scores") or {}
    return {
        "O": _num(s.get("openness")),
        "C": _num(s.get("conscientiousness")),
        "E": _num(s.get("extraversion")),
        "A": _num(s.get("agreeableness")),
        "N": _num(s.get("neuroticism")),
    }


def _band_low_high(v: float) -> str:
    if v >= 65: return "high"
    if v <= 40: return "low"
    return "medium"


# ════════════════════════════════════════════════════════════════════════
# SECTION 1 — POWER SUMMARY (3-4 line opener + 4 stat boxes)
# ════════════════════════════════════════════════════════════════════════
def section_1_power_summary(engines: Dict, base_sections: Dict) -> Dict:
    arche  = _g(engines, "personality", "archetype", "name") or "Balanced Personality"
    elem   = _g(engines, "samudrika", "element_profile", "dominant_element") or "Balanced"
    snap   = _g(engines, "first_impression", "snap_narrative", "line") or ""
    domt   = _g(engines, "personality", "dominant_trait") or "balanced"

    s7_str = (_g(base_sections, "section_7_personality_synthesis", "top_5_strengths") or [""])[0]
    s7_wk  = (_g(base_sections, "section_7_personality_synthesis", "top_5_weaknesses") or [""])[0]
    phase  = _g(base_sections, "section_15_age_wise_map", "golden_period") or "Coming years strong."

    O = _ocean(engines)
    summary = (
        f"Tum ek {arche.replace('The ', '')} ho — {elem} element dominant. "
        f"{snap} "
        f"Andar se tum {domt}-driven ho, jo tumhari sabse badi power hai aur "
        f"sometimes tumhari biggest challenge bhi. "
        f"Yeh report tumhari face ki har detail se nikla 100% personalized truth hai."
    )

    one_line_truth = f"Tum {arche} ho — {domt} tumhari shakti, balance tumhari zarurat."

    return {
        "summary_paragraph_hi": summary,
        "biggest_strength":     s7_str or "Disciplined aur focused mindset.",
        "biggest_weakness":     s7_wk  or "Kabhi-kabhi over-thinking trap me phasna.",
        "current_life_phase":   phase,
        "one_line_truth":       one_line_truth,
    }


# ════════════════════════════════════════════════════════════════════════
# SECTION 8 — LOVE & RELATIONSHIP DNA
# ════════════════════════════════════════════════════════════════════════
def section_8_love_relationship_dna(engines: Dict) -> Dict:
    """Section 8 — DEEP love DNA + classic kpis."""
    from .life_areas_deep import build_section_8_deep
    base = _section_8_classic(engines)
    deep = build_section_8_deep(engines)
    base["intro_para"] = deep["intro_para"]
    base["blocks"] = deep["blocks"]
    return base


def _section_8_classic(engines: Dict) -> Dict:
    o = _ocean(engines)
    A, N, E, C, O = o["A"], o["N"], o["E"], o["C"], o["O"]
    sambandha = _num(_g(engines, "samudrika", "composite_scores", "sambandha"), default=60)
    lips_phala = _g(engines, "samudrika", "features", "lips", "phala_hi") or ""

    # Attachment style
    if N >= 60 and A >= 55:
        attach = "Anxious-Secure mix — pyaar me invested ho but kabhi-kabhi insecurity aati hai."
    elif A >= 60 and N <= 45:
        attach = "Secure — pyaar me healthy aur grounded, partner ko safe mehsoos hota hai."
    elif A <= 40:
        attach = "Avoidant lean — independence pehle, emotional distance maintain karte ho."
    elif N >= 65:
        attach = "Anxious — partner se reassurance ki need rehti hai, overthinking zyada."
    else:
        attach = "Balanced attachment — pyaar dete bhi ho, apni space bhi maintain karte ho."

    # Loyalty
    if A >= 60 and C >= 60: loyalty = "Bahut high — once committed, fully committed."
    elif A >= 55 or C >= 60: loyalty = "High — promise tod-na pasand nahi."
    elif A < 40: loyalty = "Conditional — loyalty earn karni padti hai tumse."
    else: loyalty = "Medium — situation aur partner par depend karta hai."

    # Emotional behaviour
    if N >= 65: emo = "Emotional aur sensitive — chhoti baat bhi dil pe leti ho."
    elif N <= 40: emo = "Stable aur calm — fights me bhi cool rehte ho."
    else: emo = "Mostly stable, but trigger hone par strong reaction."

    # Breakup triggers (top 3 weaknesses applied to relationships)
    triggers = []
    if N >= 60: triggers.append("Insecurity aur over-questioning se partner thak jata hai.")
    if A <= 40: triggers.append("Apni baat zyada important — partner ki feelings ignore ho jati hain.")
    if E >= 65: triggers.append("Friends/social life me partner kam time milta hai.")
    if C <= 40: triggers.append("Promises bhul jana ya plans cancel karna trust ko hilata hai.")
    if O >= 70: triggers.append("Routine se bore — partner ko unstable feel hota hai.")
    if not triggers: triggers = ["Communication gap aur taken-for-granted feeling."]
    triggers = triggers[:3]

    # Ideal partner
    if E >= 65: ideal = "Calm, grounded, listener — jo tumhari energy balance kare."
    elif E <= 40: ideal = "Warm, expressive, slightly extroverted — jo tumhe khol sake."
    elif N >= 60: ideal = "Stable, patient, emotionally mature partner — jo reassure kar sake."
    elif A <= 45: ideal = "Independent, strong, self-respecting partner — jo apni ground rakhe."
    else: ideal = "Like-minded balanced partner — values aur lifestyle match kare."

    return {
        "love_score_100":      round((A + (100 - N) + sambandha + (lips_phala and 70 or 60)) / 4, 1),
        "attachment_style":    attach,
        "loyalty_level":       loyalty,
        "emotional_behavior":  emo,
        "breakup_triggers":    triggers,
        "ideal_partner_type":  ideal,
        "lips_signal_hi":      lips_phala or "Lips se balanced communicator nikla.",
    }


# ════════════════════════════════════════════════════════════════════════
# SECTION 10 — RED FLAGS (3 brutal truths)
# ════════════════════════════════════════════════════════════════════════
def section_10_red_flags(engines: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    stress = _g(engines, "health", "macro_indicators", "stress") or "medium"

    candidates: List[tuple] = []   # (priority_score, flag_hi)
    if N >= 65:
        candidates.append((N, "Overthinking tumhari sabse badi enemy hai — chhoti problems ko bada bana lete ho aur khud hi exhaust ho jate ho."))
    if A <= 40:
        candidates.append((100 - A, "Doosron ki feelings ignore karne ki aadat hai — log hurt hote hain but tumhe pata bhi nahi chalta."))
    if C <= 40:
        candidates.append((100 - C, "Discipline aur follow-through weak hai — bahut shuru karte ho, kam complete karte ho. Yahi tumhari biggest career block hai."))
    if E >= 70 and C <= 50:
        candidates.append((E, "Promises bahut karte ho, deliver kam hota hai — log dheere-dheere bharosa khone lagte hain."))
    if O <= 35:
        candidates.append((100 - O, "Naye ideas aur change se darte ho — jo opportunities aati hain, tum 'safe' khel ke chhod dete ho."))
    if E <= 35:
        candidates.append((100 - E, "Networking aur self-promotion se bachte ho — talent hai but world ko dikh nahi raha."))
    if N >= 55 and stress in ("high", "medium"):
        candidates.append((N, "Stress ko ignore karte ho jab tak body break nahi hoti — burnout ka pattern banta jaa raha hai."))
    if A >= 75:
        candidates.append((A - 50, "Itne nice ho ki log advantage le lete hain — 'No' bolna nahi seekha to apni hi growth ruk jayegi."))
    if O >= 75 and C <= 50:
        candidates.append((O - 50, "Itne ideas hain ki kuch bhi finish nahi hota — focus ek cheez par karo, baaki bahar phenko."))

    candidates.sort(key=lambda t: t[0], reverse=True)
    flags = [c[1] for c in candidates[:3]]
    if not flags:
        flags = [
            "Tum almost balanced ho — but iska matlab boring nahi, iska matlab consistent hona padega.",
            "Apni biggest strength ko granted le lete ho — usse aur sharpen karo.",
            "Comfort zone me reh ke 70% potential use kar rahe ho — 100% chahiye to discomfort embrace karo.",
        ]
    return {"red_flags_hi": flags}


# ════════════════════════════════════════════════════════════════════════
# SECTION 14 — LIFE FLOW (Past / Present / Future)
# ════════════════════════════════════════════════════════════════════════
def section_14_life_flow(engines: Dict, base_sections: Dict, age: int = None) -> Dict:
    """Section 14 — DEEP life flow + story mode + classic past/present/future."""
    from .life_areas_deep import build_section_14_deep
    base = _section_14_classic(engines, base_sections, age=age)
    deep = build_section_14_deep(engines, base_sections, age=age)
    base["intro_para"] = deep["intro_para"]
    base["blocks"] = deep["blocks"]
    return base


def _section_14_classic(engines: Dict, base_sections: Dict, age: int = None) -> Dict:
    age_map = _g(base_sections, "section_15_age_wise_map", "scores") or {}
    arche = _g(engines, "personality", "archetype", "name") or "Balanced Personality"
    domt  = _g(engines, "personality", "dominant_trait") or "balanced"
    elem  = _g(engines, "samudrika", "element_profile", "dominant_element") or "Balanced"

    if age is None or age <= 0: age = 30

    # Past pattern
    if age < 30:
        past_score = age_map.get("20s", 70)
        past = f"Teenage aur early 20s me tum {domt}-leaning the. Identity build hone ka phase tha — kuch struggle, kuch breakthroughs."
    elif age < 50:
        past_score = age_map.get("20s", 70)
        past = f"20s me tumhari foundation pad gayi — score {past_score}/100. Jo aaj ho, woh us decade ki mehnat ka result hai."
    else:
        past_score = age_map.get("30s_40s", 75)
        past = f"30s-40s tumhara productive peak tha — score {past_score}/100. Career, family, identity sab settle hua."

    # Present
    if age < 30:
        present = f"Abhi tumhara phase: foundation aur exploration. {elem} energy strong hai — risks lene ka best time yahi hai."
    elif age < 45:
        present = f"Abhi tumhara peak-build phase chal raha hai — {arche} archetype apne strongest form me hai. Decisions aaj ke 10 saal define karenge."
    elif age < 60:
        present = f"Abhi tumhara consolidation phase hai — jo banaya hai usko sambhalna aur next generation tak pahunchana."
    else:
        present = f"Abhi tumhara wisdom phase hai — log tumhe guidance ke liye dekhte hain. {arche} ka woh role nibhao."

    # Future
    if age < 35:
        fut_score = age_map.get("30s_40s", 75)
        future = f"Agle 10-15 saal tumhara golden window hai — projected score {fut_score}/100. Yahi pe wealth, career, family teeno banenge."
    elif age < 55:
        fut_score = age_map.get("50s_plus", 75)
        future = f"50s+ me tumhari fortune rise karegi — projected score {fut_score}/100. Late bloom strong dikh raha hai."
    else:
        future = f"Aage tumhari journey legacy aur peace ki taraf hai. {elem} energy se grounded raho, sab acha hoga."

    return {
        "past_pattern_hi":      past,
        "present_situation_hi": present,
        "future_direction_hi":  future,
    }


# ════════════════════════════════════════════════════════════════════════
# SECTION 18 — ACTION PLAN (Behavioural / Confidence / Lifestyle)
# ════════════════════════════════════════════════════════════════════════
def section_18_action_plan(engines: Dict, base_sections: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    confidence = _num(_g(engines, "first_impression", "first_impression_4", "confidence"), default=60)
    stress = _g(engines, "health", "macro_indicators", "stress") or "medium"
    energy = _g(engines, "health", "macro_indicators", "energy") or "medium"

    # Behavioural fix → weakest trait
    weakest = min(
        [("openness", O), ("conscientiousness", C), ("extraversion", E), ("agreeableness", A), ("low_neuroticism", 100 - N)],
        key=lambda t: t[1]
    )
    behav_map = {
        "openness":           "Har hafte ek nayi cheez try karo — naya cuisine, nayi route, naya skill 30 min. Comfort zone slowly tutegi.",
        "conscientiousness":  "Ek 'Daily 3' rule lagao — har subah 3 chhote tasks likho, raat tak khatam karo. Discipline 30 din me build hogi.",
        "extraversion":       "Hafte me 2 baar kisi naye insaan se 5-min baat karo (cafe, gym, online). Energy aur network dono badhenge.",
        "agreeableness":      "Daily ek kaam doosre ke liye karo bina kuch expect kiye. Empathy muscle banti hai.",
        "low_neuroticism":    "Daily 10-min breathing ya meditation lagao. Overthinking 50% kam hogi 21 din me.",
    }
    behaviour_fix = behav_map[weakest[0]]

    # Confidence
    if confidence < 55:
        conf_fix = "Confidence kam dikh raha hai. Posture fix karo (chest open, shoulders back), eye contact 3 sec rakho, aur har subah ek thing achieve karo. 30 din me visible change."
    elif confidence < 70:
        conf_fix = "Confidence theek hai but consistent nahi. Public speaking ki 1 video roz dekho, ek skill par master bano — authority confidence se zyada strong hoti hai."
    else:
        conf_fix = "Confidence already strong hai — ab use leadership me convert karo. Doosron ko mentor karna shuru karo."

    # Lifestyle
    if stress == "high" or energy == "low":
        lifestyle = "Sleep 7-8 ghante non-negotiable. Phone bedroom se hata do. Hafte me 4 din 30 min walk + 1L extra paani roz. 3 hafte me energy 30% badhegi."
    elif stress == "medium":
        lifestyle = "Routine acha hai but sharpen karo — fixed sone-uthne ka time, weekly digital detox 4 ghante, aur green vegetables daily."
    else:
        lifestyle = "Lifestyle solid hai — strength training week me 3 din add karo aur cognitive games (chess, sudoku) dimaag sharp rakhenge."

    return {
        "behavioural_fix_hi":      behaviour_fix,
        "confidence_improvement_hi": conf_fix,
        "lifestyle_suggestion_hi":   lifestyle,
    }


# ════════════════════════════════════════════════════════════════════════
# SECTION 19 — IMPROVEMENT HACKS (3 quick tips)
# ════════════════════════════════════════════════════════════════════════
def section_19_improvement_hacks(engines: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    elem = _g(engines, "samudrika", "element_profile", "dominant_element") or "Balanced"

    hacks: List[str] = []

    # Hack 1: Mental clarity
    if N >= 60:
        hacks.append("📓 Sone se pehle 5 min 'brain dump' karo — jo bhi mind me chal raha ho kaagaz par likh do. Anxiety 40% kam hoti hai.")
    elif O >= 70:
        hacks.append("🧠 Har idea ko 'parking lot' notebook me likh ke ek hafta wait karo — 80% ideas khud filter ho jayenge, 20% pe focus.")
    else:
        hacks.append("📚 Hafte me 1 ghanta apne field se hat ke kuch padho — psychology, history, biographies — perspective expand hoga.")

    # Hack 2: Social / charisma
    if E <= 45:
        hacks.append("👥 Hafte me 1 social commitment lagao — small dinner, gym class, meetup. Forced exposure se network organic banta hai.")
    elif A <= 45:
        hacks.append("🤝 Sabki baat sunte waqt 'pause-then-respond' rule lagao — 2 sec pause se rishtey 50% behtar honge.")
    else:
        hacks.append("✨ Apni story 30-sec elevator pitch me ready rakho — hyper-clarity attractive hoti hai aur opportunities aati hain.")

    # Hack 3: Physical / energy / element-based
    elem_l = (elem or "").lower()
    if "fire" in elem_l or "agni" in elem_l:
        hacks.append("🔥 Tum Agni-dominant ho — heating spices kam (mirch, lehsun) aur cooling foods (cucumber, coconut, milk) zyada lo. Anger control hoga.")
    elif "water" in elem_l or "jal" in elem_l:
        hacks.append("💧 Tum Jal-dominant ho — emotionally heavy ho. Daily 15 min sunlight + warm water 1L roz lo. Mood stable rahega.")
    elif "wood" in elem_l:
        hacks.append("🌳 Tum Wood-element ho — growth-driven ho. Har 90 din me ek nayi badi goal set karo, varna restless feel karoge.")
    elif "metal" in elem_l:
        hacks.append("⚒️ Tum Metal-element ho — discipline strong hai. But weekly 1 din 'no rules' day rakho varna rigid ban jaoge.")
    elif "earth" in elem_l:
        hacks.append("🌱 Tum Prithvi-element ho — grounded ho. But movement add karo (walk, yoga) varna stuck feel karoge.")
    else:
        hacks.append("🌿 Roj subah 10 min sunlight + 30 min movement — yeh combo har element ke liye kaam karta hai.")

    return {"hacks_hi": hacks[:3]}


# ════════════════════════════════════════════════════════════════════════
# SECTION 20 — COMPATIBILITY SNAPSHOT
# ════════════════════════════════════════════════════════════════════════
def section_20_compatibility(engines: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    elem = (_g(engines, "samudrika", "element_profile", "dominant_element") or "Balanced").lower()

    # Best match by complementary trait
    if E >= 65 and N <= 45:
        best = "Calm, thoughtful, slightly introverted partner — jo tumhari energy ko grounding de."
    elif E <= 45:
        best = "Warm, expressive, slightly extroverted partner — jo tumhe khol sake aur social bridge bane."
    elif N >= 60:
        best = "Stable, patient, emotionally mature partner — jo storm me anchor ban sake."
    elif A <= 45:
        best = "Independent, self-respecting, strong-minded partner — jo apni boundaries jaante ho."
    elif C >= 65:
        best = "Spontaneous, creative, flexible partner — jo tumhari structure ko life de sake."
    else:
        best = "Like-minded grounded partner — values aur life-vision match kare, baaki sab fit hoga."

    # Avoid
    if N >= 60: avoid = "Doosra anxious-overthinker partner — dono burnout ho jaoge."
    elif A <= 40: avoid = "Doosra tough-headed partner — har baat fight ban jayegi."
    elif E >= 70: avoid = "Doosra hyper-social partner — quiet time kabhi nahi milega."
    else: avoid = "Insecure aur control-freak partner — tumhari freedom kuchal degi."

    # Element compatibility (Wu Xing 5-element cycle)
    elem_match = {
        "wood":    ("Fire (energetic, expressive)",  "Metal (rigid, controlling)"),
        "fire":    ("Earth (grounded, warm)",        "Water (cold, distant)"),
        "earth":   ("Metal (clear, organized)",      "Wood (pushy, growth-obsessed)"),
        "metal":   ("Water (flexible, calming)",     "Fire (volatile, impulsive)"),
        "water":   ("Wood (growth-oriented, kind)",  "Earth (slow, stubborn)"),
        "agni":    ("Earth (grounded, warm)",        "Water (cold, distant)"),
        "jal":     ("Wood (growth-oriented, kind)",  "Earth (slow, stubborn)"),
        "vayu":    ("Earth (grounded)",              "Vayu (chaos × chaos)"),
        "akash":   ("Prithvi (grounding)",           "Akash (no anchor)"),
        "prithvi": ("Akash (vision)",                "Prithvi (no movement)"),
    }
    em = next((v for k, v in elem_match.items() if k in elem), ("Complementary element", "Same dominant element"))

    return {
        "best_match_hi":          best,
        "avoid_match_hi":         avoid,
        "element_best_match":     em[0],
        "element_avoid_match":    em[1],
    }


# ════════════════════════════════════════════════════════════════════════
# SECTION 21 — FINAL TRUTH PAGE
# ════════════════════════════════════════════════════════════════════════
def section_21_final_truth(engines: Dict, base_sections: Dict, new_sections: Dict) -> Dict:
    arche = _g(engines, "personality", "archetype", "name") or "Balanced Soul"
    elem  = _g(engines, "samudrika", "element_profile", "dominant_element") or "Balanced"
    domt  = _g(engines, "personality", "dominant_trait") or "balanced"

    s7_str = (_g(base_sections, "section_7_personality_synthesis", "top_5_strengths") or [""])[0]
    red_flags = _g(new_sections, "section_10_red_flags", "red_flags_hi") or []
    biggest_mistake = red_flags[0] if red_flags else "Apni biggest strength ko granted lena."

    fixes = _g(new_sections, "section_18_action_plan") or {}
    must_do = fixes.get("behavioural_fix_hi") or "Daily ek chhota commitment khud se karo aur nibhao."

    who_you_are = (
        f"Tum {arche} ho — {elem} element dominant, {domt}-driven soul. "
        f"Tumhari face me likha hai ki tum naturally apne path par akele chalne wale ho — "
        f"crowd follow nahi karte, crowd tumhe follow karta hai."
    )

    closing_truth = (
        f"Yaad rakho — kismat face me likhi hoti hai, "
        f"par badalti choices se hai. Tumhari biggest power: {s7_str.split('.')[0] if s7_str else 'self-awareness'}. "
        f"Tumhari biggest trap: {biggest_mistake.split('—')[0].strip() if '—' in biggest_mistake else 'comfort zone'}. "
        f"Aaj se ek kaam shuru karo — '{must_do.split('.')[0]}.' "
        f"6 mahine baad wapas yeh report padhna — tab tum khud apne aap ko pehchanoge nahi."
    )

    return {
        "who_you_are_hi":      who_you_are,
        "biggest_strength_hi": s7_str or "Tumhari self-awareness aur growth mindset.",
        "biggest_mistake_hi":  biggest_mistake,
        "must_do_hi":          must_do,
        "closing_truth_hi":    closing_truth,
        "report_signature":    "— Cosmic Lens · Face Intelligence Report v1",
    }


# ════════════════════════════════════════════════════════════════════════
# Master orchestrator
# ════════════════════════════════════════════════════════════════════════
def build_new_sections(engines: Dict,
                       base_sections: Dict,
                       mole_section_17: Dict = None,
                       age: int = None) -> Dict:
    """Build all 9 step-3 sections (1, 8, 10, 14, 17, 18, 19, 20, 21)."""
    s1  = section_1_power_summary(engines, base_sections)
    s8  = section_8_love_relationship_dna(engines)
    s10 = section_10_red_flags(engines)
    s14 = section_14_life_flow(engines, base_sections, age=age)
    s17 = mole_section_17 or {"moles_found": 0, "moles": [], "summary_hi": "Mole detection skipped."}
    s18 = section_18_action_plan(engines, base_sections)
    s19 = section_19_improvement_hacks(engines)
    s20 = section_20_compatibility(engines)
    new_sec_dict = {
        "section_10_red_flags": s10,
        "section_18_action_plan": s18,
    }
    s21 = section_21_final_truth(engines, base_sections, new_sec_dict)

    return {
        "section_1_power_summary":         s1,
        "section_8_love_relationship_dna": s8,
        "section_10_red_flags":            s10,
        "section_14_life_flow":            s14,
        "section_17_secret_markings":      s17,
        "section_18_action_plan":          s18,
        "section_19_improvement_hacks":    s19,
        "section_20_compatibility":        s20,
        "section_21_final_truth":          s21,
    }
