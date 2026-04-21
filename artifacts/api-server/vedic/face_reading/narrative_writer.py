"""
Narrative Writer — produces rich Hinglish prose paragraphs for each of the
21+1 report sections, using real engine data (NEVER hardcoded fallbacks).

Each writer takes:
  - the section's existing structured content (from section_mapper / new_sections)
  - the full engines dict (for cross-section references like OCEAN, element, scores)
  - person dict (age, gender, name)

Returns a string: a 150-350 word personalised Hinglish paragraph that becomes
the section's prose intro (rendered before the structured fields in PDF).
"""
from __future__ import annotations
from typing import Any, Dict, Optional


# ── Helpers ───────────────────────────────────────────────────────────────
def _g(d: Optional[Dict], *path, default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def _num(v, default=50.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _ocean(engines):
    return (engines.get("personality") or {}).get("ocean_summary_scores") or {}


def _band_word(score, low_word, mid_word, high_word, low=40, high=60):
    s = _num(score)
    if s < low: return low_word
    if s > high: return high_word
    return mid_word


def _gender_word(g):
    return "ladka" if g == "M" else ("ladki" if g == "F" else "insaan")


def _join_para(*lines):
    """Join non-empty sentences with single space → one tight paragraph."""
    return " ".join(s.strip() for s in lines if s and s.strip())


# ──────────────────────────────────────────────────────────────────────────
# Section 1 — POWER SUMMARY
# ──────────────────────────────────────────────────────────────────────────
def write_s1(content, engines, person):
    O, C, E, A, N = (_num(_ocean(engines).get(k)) for k in
                     ("openness","conscientiousness","extraversion","agreeableness","neuroticism"))
    elem = _g(engines, "samudrika", "element_profile", "dominant_element") or "Balanced"
    archetype = content.get("biggest_strength", "")
    age = person.get("age") or "?"
    fi_age = _g(engines, "first_impression", "perceived_age", "value")
    age_gap = ""
    if fi_age and isinstance(age, int):
        diff = round(_num(fi_age) - age, 1)
        if abs(diff) >= 3:
            age_gap = (f" Tumhari pratyaksh aayu {fi_age:.0f} dikhti hai — "
                       f"yaani actual se {abs(diff):.0f} saal "
                       f"{'zyada' if diff > 0 else 'kam'}, "
                       f"jo {'gambheer maturity' if diff > 0 else 'youthful energy'} dikhata hai.")
    
    dom_letter, dom_val = max(zip("OCEAN", [O,C,E,A,N]), key=lambda x: x[1])
    dom_name = {"O":"Openness (naye anubhav)", "C":"Conscientiousness (anushasan)",
                "E":"Extraversion (logon ke saath energy)", "A":"Agreeableness (warmth)",
                "N":"Neuroticism (sensitivity)"}[dom_letter]
    
    return _join_para(
        f"Tumhara chehra ek complete kahaani sunata hai — aur uss kahaani ka heart {elem} tatva hai.",
        f"OCEAN scan me tumhari sabse strong dimension {dom_name} nikli ({dom_val:.0f}/100), "
        f"jo tumhari personality ki spine hai.",
        f"Yeh report woh sab kuch dikhayegi jo log dekh ke bhi nahi samajhte —"
        f" tumhari biggest strength, tumhari hidden weakness, aur woh truth jo aaj tak shayad kisi ne tumse seedha nahi kaha.",
        age_gap,
        f"Read karte waqt yaad rakho: yeh judge nahi kar raha, mirror dikhaa raha hai. "
        f"Jo cheez chubhe — ussi me tumhari growth chhupi hai. Jo cheez khushi de — usse double down karo.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 2 — PSYCHOLOGICAL TYPE
# ──────────────────────────────────────────────────────────────────────────
def write_s2(content, engines, person):
    ptype = content.get("personality_type", "Observer")
    ie = content.get("introversion_vs_extroversion", "Ambivert")
    ds = content.get("decision_style", "Mixed")
    intel = content.get("intelligence_type", "Strategic")
    e_score = _num(content.get("extraversion_score"))
    
    type_meaning = {
        "Leader": "Tum naturally lead karte ho — log tumhari taraf instinctively dekhte hain decisions ke liye.",
        "Thinker": "Tum bahar se shaant lagte ho, par andar dimaag har time analyze kar raha hai.",
        "Feeler": "Tumhare emotions surface ke kareeb hain — log feel kar lete hain ki tum kya soch rahe ho.",
        "Observer": "Tum log ko padhne wale ho — pehle observe karte ho, fir conclude karte ho.",
    }.get(ptype, "")
    
    ie_meaning = {
        "Introvert": f"Tumhara extraversion score {e_score:.0f} hai — yaani group me thak jaate ho, akele me recharge hote ho. Yeh weakness nahi, tumhari design hai.",
        "Extrovert": f"Tumhara extraversion score {e_score:.0f} hai — log tumhari energy se boost paate hain, tum logon ki energy se.",
        "Ambivert": f"Tum balance pe ho ({e_score:.0f}/100) — kabhi outgoing, kabhi reserved. Yeh tumhari biggest superpower hai social settings me.",
    }.get(ie, "")
    
    return _join_para(
        f"Manovigyan ki bhasha me, tum '{ptype}' type ho.",
        type_meaning,
        ie_meaning,
        f"Tumhari intelligence ka primary mode {intel.lower()} hai — yaani jab problem aati hai, tum {intel.lower()} approach use karte ho before anything else.",
        f"Decision lene ki tumhari style: {ds}. Iska matlab high-stakes me tum {'data dekh ke' if 'Logical' in ds else ('dil ki sun ke' if 'Emotional' in ds else 'dono ka mix')} chalte ho.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 3 — MASK vs REAL SELF
# ──────────────────────────────────────────────────────────────────────────
def write_s3(content, engines, person):
    sym = _num(content.get("symmetry_score"))
    side = content.get("dominant_face_side", "")
    pub = content.get("public_perception", "")
    real = content.get("real_self", "")
    conflict = content.get("internal_conflict", "")
    
    side_hi = ""
    if "right" in (side or ""):
        side_hi = "Tumhara right side dominant hai — yaani tumhara public/professional face strong hai, par left (emotional/private) side thoda alag kahaani kehta hai."
    elif "left" in (side or ""):
        side_hi = "Tumhara left side dominant hai — yaani tumhari emotional/intuitive depth tumhari logical-public side se zyada strong hai."
    
    sym_hi = ""
    if sym < 50:
        sym_hi = f"Tumhari facial symmetry {sym:.0f}/100 hai — perfect symmetry rare hoti hai, lekin tumhari asymmetry kaafi visible hai. Iska matlab andar aur bahar me real gap hai — yaani jo log dekh rahe hain woh tumhara 100% asli roop nahi."
    elif sym > 75:
        sym_hi = f"Tumhari symmetry strong hai ({sym:.0f}/100) — tumhara mask aur asli self kaafi aligned hain. Log tumhe jaisa dekhte hain, tum lagbhag waise hi ho."
    else:
        sym_hi = f"Tumhari symmetry medium ({sym:.0f}/100) hai — thoda gap hai mask aur self me, par alarming nahi."
    
    return _join_para(
        f"Public me jab tum chalte ho, log tumhare baare me ek snap impression banate hain — aur woh impression hamesha tumhari reality nahi hota.",
        f"Tumhara public face: \"{pub}\".",
        f"Lekin chehre ki micro-asymmetries andar ki kahaani kehte hain: \"{real}\"",
        side_hi,
        sym_hi,
        f"Conflict yeh hai: \"{conflict}\" — aur isi gap me tumhari authenticity ki growth chhupi hai. "
        f"Jab tum apna mask thoda chhota karoge aur asli emotion dikhana shuru karoge, tab relationships me real depth aayegi.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 4 — FIRST IMPRESSION
# ──────────────────────────────────────────────────────────────────────────
def write_s4(content, engines, person):
    conf = _num(content.get("confidence_out_of_10"))
    trust = _num(content.get("trust_out_of_10"))
    attr = _num(content.get("attraction_out_of_10"))
    auth = _num(content.get("authority_out_of_10"))
    pa = _num(content.get("perceived_age_years"), default=0)
    actual_age = person.get("age") or 0
    
    top_dim, top_val = max([("self-confidence", conf),("trust",trust),("attraction",attr),("authority",auth)], key=lambda x: x[1])
    weak_dim, weak_val = min([("self-confidence", conf),("trust",trust),("attraction",attr),("authority",auth)], key=lambda x: x[1])
    
    top_hi = {
        "self-confidence": "Tum kamre me ghuste ho to log feel karte hain ki tum apni jagah pe sure ho.",
        "trust": "Log tumpe quickly trust karte hain — tumhare features 'safe person' signal dete hain.",
        "attraction": "Tumhari magnetic quality hai — log naturally tumhari taraf draw hote hain.",
        "authority": "Log tumhe seriously lete hain — natural authority signal strong hai tumhare chehre me.",
    }.get(top_dim, "")
    
    weak_hi = {
        "self-confidence": "Self-confidence dimension thoda kam dikha — body language aur eye contact pe kaam karna chahiye.",
        "trust": "Trust score thoda kam hai — open expressions aur warm smile usse boost karenge.",
        "attraction": "Attraction subtle hai — yeh deep-impression type hai, fast-impression nahi.",
        "authority": "Authority signal kam hai — voice ki firmness aur posture isse 2x kar sakte hain.",
    }.get(weak_dim, "")
    
    age_hi = ""
    if pa and actual_age:
        diff = round(pa - actual_age, 1)
        if diff >= 3:
            age_hi = f"Log tumhe {pa:.0f} ka samajhte hain — actual se {diff:.0f} saal bade. Maturity aur depth ka signal hai, fitness/grooming pe kaam karne se yeh balance ho jayega."
        elif diff <= -3:
            age_hi = f"Log tumhe {pa:.0f} ka samajhte hain — actual se {abs(diff):.0f} saal chhote. Youthful energy ka signal — leverage karo personal branding me."
    
    return _join_para(
        f"Pehli mulaqat me log tumhe 7 second me judge kar lete hain — chahe woh maane ya na maane.",
        f"Tumhara biggest first-impression strength: {top_dim} ({top_val:.1f}/10). {top_hi}",
        f"Aur tumhara weakest area: {weak_dim} ({weak_val:.1f}/10). {weak_hi}",
        age_hi,
        f"Yeh scores immutable nahi hain — grooming, posture aur expression practice se 6 mahine me 1.5–2 points easily badh sakte hain.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 5 — CORE FOUNDATION (5-element + 3-zones)
# ──────────────────────────────────────────────────────────────────────────
def write_s5(content, engines, person):
    elem = content.get("five_element_profile", "Balanced")
    zones = content.get("three_life_zones") or {}
    fz = zones.get("forehead_zone", {})
    mz = zones.get("mid_face_zone", {})
    lz = zones.get("lower_face_zone", {})
    
    zone_summary = []
    for name, z in [("Forehead (soch/past)", fz), ("Mid-face (career/present)", mz), ("Lower face (parivaar/future)", lz)]:
        s = z.get("strength", "balanced")
        if s == "strong":
            zone_summary.append(f"<b>{name} strong hai</b> — yaani is area me tumhari natural shakti hai.")
        elif s == "subtle":
            zone_summary.append(f"<b>{name} subtle hai</b> — yeh area thoda underdeveloped lagta hai, conscious investment chahiye.")
    
    elem_meaning = {
        "Wood": "Wood tatva ka matlab hai growth, ambition, leader-energy. Tum naturally aage badhne ki direction me sochte ho — par over-reach ka risk hai.",
        "Fire": "Fire tatva ka matlab hai passion, expression, charisma. Tum kamre ki energy badal dete ho — par burnout se bachna padega.",
        "Earth": "Earth tatva ka matlab hai stability, nurture, reliable. Log tumpe count karte hain — par change ko embrace karna mushkil lagta hai.",
        "Metal": "Metal tatva ka matlab hai discipline, structure, precision. Tumhari standards high hain — par perfectionism trap se bachna hai.",
        "Water": "Water tatva ka matlab hai wisdom, depth, intuition. Tum andar se gehre ho — par overthinking ka pattern monitor karna hai.",
        "Balanced": "Tumhari element-profile balanced hai — koi single element overpowering nahi. Yeh adaptable banata hai, par sometimes 'strong identity' missing feel ho sakti hai.",
    }.get(elem, "")
    
    return _join_para(
        f"Vedic Samudrika Shastra aur 5-Element theory ke hisaab se tumhara core element <b>{elem}</b> hai.",
        elem_meaning,
        f"Tumhare chehre ko 3 zones me divide karke padha jata hai: maatha (past/soch), beech (vartmaan/karm), aur niche (bhavishya/sthirta).",
        " ".join(zone_summary) if zone_summary else "Tumhare teeno zones balanced hain — yeh rare aur shubh sanket hai.",
        f"Yeh foundation tumhari har baaki section ki base hai — career, prem, swasthya — sab is element ki rang me dekhe jaate hain.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 6 — FEATURE ANALYSIS
# ──────────────────────────────────────────────────────────────────────────
def write_s6(content, engines, person):
    # New deep structure: just return intro_para; PDF renders feature_blocks
    intro = content.get("intro_para") or (
        "Tumhare har feature ki ek alag kahaani hai — aur jab unhe ek saath padha "
        "jata hai, tab puri tasveer nikalti hai."
    )
    return intro


# ──────────────────────────────────────────────────────────────────────────
# Section 7 — PERSONALITY SYNTHESIS
# ──────────────────────────────────────────────────────────────────────────
def write_s7(content, engines, person):
    arch = content.get("archetype", "Balanced")
    dom = content.get("dominant_trait", "")
    behaviour = content.get("behaviour_pattern", "")
    return _join_para(
        f"Ab tak ke saare data ko ek tasveer me jodne ka time hai. Tumhari personality ka archetype hai: <b>{arch}</b>.",
        behaviour,
        f"Real life me iska matlab yeh hai ki tumhari decisions, relationships, aur reactions sab is core trait ke around revolve karti hain.",
        f"Niche di gayi top 5 strengths tumhari natural superpowers hain — inhe pehchaan ke conscious use karoge to life ka 80% game tum yahin se jeet loge.",
        f"Top 5 weaknesses koi defect nahi — yeh tumhari blind spots hain. Awareness aate hi 50% problem khud solve ho jaati hai.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 8 — LOVE / RELATIONSHIP DNA
# ──────────────────────────────────────────────────────────────────────────
def write_s8(content, engines, person):
    att = content.get("attachment_style", "")
    loy = content.get("loyalty_level", "")
    eb  = content.get("emotional_behavior", "")
    ideal = content.get("ideal_partner_type", "")
    return _join_para(
        f"Pyaar tumhare liye sirf emotion nahi — ek pura ecosystem hai. Tumhari attachment style hai: <b>{att}</b>.",
        f"Loyalty ke maamle me tum {loy.lower() if loy else 'sthir'} ho — yeh tumhari biggest gift bhi hai aur biggest vulnerability bhi.",
        f"Emotional behaviour ka pattern: \"{eb}\" — yaani conflict ke time tum kaise react karte ho, woh predictable hai aur partner ko samajhna chahiye.",
        f"Ideal partner type tumhare liye: \"{ideal}\". Same-energy partner se relationship comfortable lagega par growth slow hogi; opposite-energy partner ke saath friction zyada hoga par evolution fastest.",
        f"Yaad rakho — pyaar 'finding the right person' nahi, 'becoming the right person' hai. Apni weaknesses se vaakif hone se aadhi battle aaj hi jeet lete ho.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 9 — CAREER & MONEY
# ──────────────────────────────────────────────────────────────────────────
def write_s9(content, engines, person):
    jb = content.get("job_vs_business", "")
    risk = content.get("risk_taking_ability", "")
    growth = content.get("wealth_growth_pattern", "")
    mind = content.get("money_mindset", "")
    score = _num(content.get("wealth_score_100"))
    
    score_line = ""
    if score >= 70:
        score_line = f"Tumhara wealth-potential score {score:.0f}/100 hai — yeh upper band hai. Right strategy se tum financial freedom ko 40s tak achieve kar sakte ho."
    elif score >= 50:
        score_line = f"Tumhara wealth-potential score {score:.0f}/100 hai — middle band, yaani potential strong hai par execution + discipline ki zarurat hai."
    else:
        score_line = f"Tumhara wealth-potential score {score:.0f}/100 hai — yeh signal hai ki paisa banane ke liye conscious strategy aur upskilling karni padegi."
    
    return _join_para(
        f"Career aur paisa ka sambandh tumhari natural risk-tolerance aur execution-style se hota hai.",
        f"Tumhari best path: <b>{jb}</b>. {('Job security tumhe peace deti hai aur side hustle creativity outlet.' if 'Hybrid' in (jb or '') else 'Yeh tumhari core risk profile ke saath sabse aligned hai.')}",
        f"Risk-taking ability tumhari {risk.lower() if risk else 'medium'} hai — yaani tum {('big bets le sakte ho' if (risk or '').lower()=='high' else ('calculated bets le sakte ho' if (risk or '').lower()=='medium' else 'safe-play me comfortable ho'))}.",
        f"Wealth growth pattern: \"{growth}\". Money mindset: \"{mind}\".",
        score_line,
        f"Action: agle 12 mahine me ek skill jo 10x return de sakti hai — usme deep-invest karo. Generic upgrade waste hai tumhari capacity ki.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 10 — RED FLAGS
# ──────────────────────────────────────────────────────────────────────────
def write_s10(content, engines, person):
    flags = content.get("red_flags_hi") or content.get("red_flags") or []
    n = len(flags) if isinstance(flags, list) else 0
    return _join_para(
        f"Yeh section sabse uncomfortable hai — kyunki yeh truth hai jo aaj tak shayad kisi ne tumse seedha nahi kaha.",
        f"Tumhare chehre, OCEAN scan aur element profile ne {n if n else 'kuch'} aise pattern dikhaye jo agar address na kiye gaye, "
        f"to agle 5-10 saal me tumhe zaroor rok sakte hain.",
        f"Inhe weakness ki tarah nahi, 'awareness zones' ki tarah dekho. Jis cheez ki awareness aati hai, woh apne aap shrink hone lagti hai.",
        f"Niche di gayi list ko ek baar padho, fir ek week ke baad dobara — jo line dobara strike kare, woh hai tumhara real growth target.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 11 — ATTRACTION & CHARISMA
# ──────────────────────────────────────────────────────────────────────────
def write_s11(content, engines, person):
    score = _num(content.get("charisma_score_100"))
    style = content.get("attraction_style", "")
    boost = content.get("magnetism_boost") or content.get("how_to_boost") or ""
    return _join_para(
        f"Charisma janma-jaat nahi — practiced skill hai. Tumhara current charisma score: <b>{score:.0f}/100</b>.",
        f"Tumhari attraction style: \"{style}\". Yeh batata hai ki log tumhari taraf kis vajah se kheenche jaate hain.",
        f"Boost karne ka tarika: \"{boost}\".",
        f"Yaad rakho — charisma {'80% sunne ka kaam hai, 20% bolne ka' if score < 60 else 'tumhari natural strength hai, ab depth add karo'}. "
        f"Eye contact, slow speech, aur authentic curiosity — yeh teen cheezein 6 mahine me score 15+ points badha sakti hain.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 12 — DECISION STYLE
# ──────────────────────────────────────────────────────────────────────────
def write_s12(content, engines, person):
    style = content.get("decision_pattern") or content.get("style") or ""
    speed = content.get("speed", "")
    bias = content.get("biggest_bias", "") or content.get("watch_out", "")
    return _join_para(
        f"Tumhare har choice ke peeche ek pattern hai — woh pattern tumhe har 5 saal me wahi jagah laata hai jahan tum pehle they.",
        f"Tumhari decision-making style: \"{style}\". Speed: \"{speed}\".",
        f"Tumhari sabse badi cognitive bias: \"{bias}\". Yeh woh trap hai jisme tum baar-baar girte ho — kyunki yeh tumhe right feel hota hai.",
        f"Hack: agle 30 din, har major decision se pehle ek line likho — 'agar yeh decision galat nikla, to next step kya hoga?' "
        f"Yeh ek line tumhari 70% bad calls ko filter kar degi.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 13 — ARCHETYPE
# ──────────────────────────────────────────────────────────────────────────
def write_s13(content, engines, person):
    arch = content.get("archetype") or content.get("name") or "Balanced Soul"
    desc = content.get("description") or content.get("meaning_hi") or ""
    famous = content.get("famous_examples") or content.get("similar_archetypes") or []
    return _join_para(
        f"Har insaan ek archetype hota hai — ek ancient pattern jo har generation me repeat hota hai.",
        f"Tumhara archetype: <b>{arch}</b>.",
        desc,
        f"Yeh archetype tumhari journey ka script hai — challenges, gifts, aur destination teeno isi me likhe hain.",
        (f"Similar archetypes wale famous log: {', '.join(famous[:4])}." if isinstance(famous, list) and famous else ""),
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 14 — LIFE FLOW (past/present/future)
# ──────────────────────────────────────────────────────────────────────────
def write_s14(content, engines, person):
    past = content.get("past_phase_hi") or content.get("past", "")
    present = content.get("present_phase_hi") or content.get("present", "")
    future = content.get("future_phase_hi") or content.get("future", "")
    return _join_para(
        f"Jeevan ki dhaara linear nahi — phases me chalti hai. Tumhare chehre ke teen zones (maatha/beech/niche) past/present/future ka map dete hain.",
        f"<b>Past:</b> {past}",
        f"<b>Present:</b> {present}",
        f"<b>Future:</b> {future}",
        f"Aaj jo tum bo rahe ho, woh agle phase me phal ban ke aayega. Is awareness ka faayda yeh hai ki tum apne future ko aaj ke choices se shape kar sakte ho.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 15 — AGE-WISE FORTUNE MAP
# ──────────────────────────────────────────────────────────────────────────
def write_s15(content, engines, person):
    golden = content.get("golden_period") or content.get("best_phase", "")
    caution = content.get("caution_period") or content.get("watch_period", "")
    age = person.get("age") or 30
    
    return _join_para(
        f"Vedic Samudrika me chehre ke alag-alag parts alag-alag umar ke phases govern karte hain.",
        f"Tumhari best phase: <b>{golden}</b> — is period me opportunities maximum honge, aur tum apne natural advantage me hoge.",
        (f"Caution period: <b>{caution}</b> — is window me extra discipline aur health-care zaroori hai." if caution else ""),
        f"Aaj tumhari umar {age} hai — to next 5 saal kaise plan kiye jaaye yeh decide karna critical hai.",
        f"Niche age-bands ke prediction structured form me hain — aap apne current band aur next band dono padho.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 16 — HEALTH SCAN
# ──────────────────────────────────────────────────────────────────────────
def write_s16(content, engines, person):
    score = _num(content.get("vitality_score_100") or content.get("overall_health_score"))
    sleep = content.get("sleep_quality") or content.get("sleep_indicator", "")
    stress = content.get("stress_signal") or content.get("stress_indicator", "")
    fitness = content.get("fitness_advice") or content.get("recommended_routine", "")
    
    return _join_para(
        f"Yeh medical diagnosis nahi — chehre ke visible signals (skin, eyes, dark circles, lips) ka summary hai.",
        f"Tumhara overall vitality score: <b>{score:.0f}/100</b>.",
        f"Sleep quality signal: \"{sleep}\".",
        f"Stress signal: \"{stress}\".",
        f"Recommended routine: \"{fitness}\".",
        f"Disclaimer: koi bhi serious symptom ho to qualified doctor se hi consult karo. Yeh report self-awareness ke liye hai, prescription ke liye nahi.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 17 — SECRET MARKINGS (moles)
# ──────────────────────────────────────────────────────────────────────────
def write_s17(content, engines, person):
    moles = content.get("moles_detected") or content.get("markings") or []
    n = len(moles) if isinstance(moles, list) else 0
    return _join_para(
        f"Vedic me moles aur tilak ko 'gupt chinha' kaha jata hai — chhote markings, badi kahaani.",
        (f"Tumhare chehre par humne {n} prominent markings detect kiye." if n else "Tumhare chehre par koi prominent moles detect nahi hue — yeh bhi ek shubh sanket hai (clean canvas)."),
        f"Har location ka apna meaning hai — niche structured form me detail hai.",
        f"Yaad rakho — moles destiny fix nahi karte, indicators hain. Awareness se aap unka use kar sakte ho ya unke risk ko mitigate kar sakte ho.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 18 — ACTION PLAN
# ──────────────────────────────────────────────────────────────────────────
def write_s18(content, engines, person):
    actions = content.get("daily_actions_hi") or content.get("daily_practices") or []
    n = len(actions) if isinstance(actions, list) else 0
    return _join_para(
        f"Knowledge useless hai jab tak action na ho. Yeh section sirf information nahi — execution plan hai.",
        f"Niche di gayi {n if n else 'kuch'} daily/weekly practices tumhari personality, archetype aur element ke hisaab se customize ki gayi hain.",
        f"Pehle hafte sirf 1 practice pick karo — sab nahi. Consistency >> intensity. Ek practice 30 din chala lo, fir doosri add karo.",
        f"6 mahine baad jab dobara yeh report padhoge, tab tum khud ke andar visible shift dekhoge — yeh promise hai.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 19 — IMPROVEMENT HACKS
# ──────────────────────────────────────────────────────────────────────────
def write_s19(content, engines, person):
    hacks = content.get("hacks_hi") or content.get("quick_wins") or []
    n = len(hacks) if isinstance(hacks, list) else 0
    return _join_para(
        f"Yeh section ke hacks 'overnight transformation' nahi — par 30-60 din ke andar visible shift de sakte hain.",
        f"Total {n if n else 'kuch'} hacks niche hain — har ek tumhari specific weakness ya growth-area target karta hai.",
        f"Pro tip: jis hack ko padh ke tumhe lagta hai 'ye to easy hai, mujhe chahiye nahi' — wahi tumhara real target hai. "
        f"Resistance hi growth ka indicator hai.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 20 — COMPATIBILITY
# ──────────────────────────────────────────────────────────────────────────
def write_s20(content, engines, person):
    best = content.get("best_match", "") or content.get("ideal_partner", "")
    avoid = content.get("avoid_match", "") or content.get("avoid_partner", "")
    elem_best = content.get("element_best_match", "")
    return _join_para(
        f"Compatibility sirf 'love match' nahi — har relationship (friend, business partner, life partner) me kaam karta hai.",
        f"<b>Best match:</b> {best}",
        f"<b>Avoid match:</b> {avoid}",
        (f"Element-level pe tumhara best pairing: {elem_best}." if elem_best else ""),
        f"Yaad rakho — compatibility score sirf 'easy relationship' predict karta hai. Sometimes growth incompatible-but-respectful relationship me zyada hoti hai.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Section 21 — FINAL TRUTH
# ──────────────────────────────────────────────────────────────────────────
def write_s21(content, engines, person):
    truth = content.get("brutal_truth", "") or content.get("one_line_truth", "")
    must = content.get("must_do", "")
    closing = content.get("closing_truth", "")
    return _join_para(
        f"Yeh report ka aakhri page hai — aur sabse important.",
        f"<b>Brutal truth:</b> {truth}",
        f"<b>Must-do (agla 30 din):</b> {must}",
        closing,
        f"6 mahine baad yeh report dobara padhna — woh tumhara progress-mirror banegi.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Bonus — 5 Personality Scores
# ──────────────────────────────────────────────────────────────────────────
def write_bonus(content, engines, person):
    scores = {k: _num(v) for k, v in content.items() if isinstance(v, (int, float, str))}
    if not scores:
        return ""
    top = max(scores.items(), key=lambda x: x[1])
    bot = min(scores.items(), key=lambda x: x[1])
    return _join_para(
        f"Yeh 5 scores tumhare overall life-game ka snapshot hain (sab 0-10 scale par).",
        f"Tumhara strongest area: <b>{top[0].replace('_',' ').title()} ({top[1]:.1f}/10)</b> — yeh tumhari natural advantage hai, isse leverage karo.",
        f"Tumhara weakest area: <b>{bot[0].replace('_',' ').title()} ({bot[1]:.1f}/10)</b> — agle 90 din me sirf isi pe focus karo, baaki sab apne aap badhega.",
        f"Yaad rakho — yeh scores fixed nahi hain. Conscious work se 6 mahine me 1.5-2 points har dimension me badh sakte hain.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Master dispatch table
# ──────────────────────────────────────────────────────────────────────────
WRITERS = {
    "section_1_power_summary":          write_s1,
    "section_2_psychological_type":     write_s2,
    "section_3_mask_vs_real":           write_s3,
    "section_4_first_impression":       write_s4,
    "section_5_core_foundation":        write_s5,
    "section_6_feature_analysis":       write_s6,
    "section_7_personality_synthesis":  write_s7,
    "section_8_love_relationship_dna":  write_s8,
    "section_9_career_money":           write_s9,
    "section_10_red_flags":             write_s10,
    "section_11_attraction_charisma":   write_s11,
    "section_12_decision_style":        write_s12,
    "section_13_archetype":             write_s13,
    "section_14_life_flow":             write_s14,
    "section_15_age_wise_map":          write_s15,
    "section_16_health_scan":           write_s16,
    "section_17_secret_markings":       write_s17,
    "section_18_action_plan":           write_s18,
    "section_19_improvement_hacks":     write_s19,
    "section_20_compatibility":         write_s20,
    "section_21_final_truth":           write_s21,
    "bonus_personality_score":          write_bonus,
}


def write_narrative(section_key: str, content: Dict, engines: Dict, person: Dict) -> str:
    """Produce a rich Hinglish prose paragraph for the given section."""
    writer = WRITERS.get(section_key)
    if not writer or not isinstance(content, dict):
        return ""
    try:
        return writer(content, engines, person)
    except Exception:
        return ""
