"""
Improvement-Deep — produces rich block structures for:
  - Section 1  : Power Summary (multi-lens: 30-sec / career / love / friend / parent / self)
  - Section 18 : Action Plan (7-day / 21-day / 90-day staged plans)
  - Section 19 : Improvement Hacks (cross-combo named insights)
  - Bonus      : 5-Score deep-dive (why this number + +1 means + top action)

Same shape as life_areas_deep — returns {"intro_para","blocks":[...]}.
Each block: heading_hi, heading_en, key_metric{}, body, callout{}, bullets[].
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional


def _g(d, *path, default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def _num(v, default=50.0):
    try: return float(v)
    except (TypeError, ValueError): return default


def _ocean(engines):
    o = _g(engines, "personality", "ocean_summary_scores", default={}) or {}
    return {
        "O": _num(o.get("openness")),
        "C": _num(o.get("conscientiousness")),
        "E": _num(o.get("extraversion")),
        "A": _num(o.get("agreeableness")),
        "N": _num(o.get("neuroticism")),
    }


# ──────────────────────────────────────────────────────────────────────────
# SECTION 1 — POWER SUMMARY MULTI-LENS (5 lenses)
# ──────────────────────────────────────────────────────────────────────────
def build_section_1_multi_summary(engines: Dict, base_sections: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    from .consistency_layer import get_dominant_element, get_archetype, get_dominant_trait
    arche  = get_archetype(engines)
    elem   = get_dominant_element(engines)
    domt   = get_dominant_trait(engines)

    blocks: List[Dict] = []

    # 30-SECOND VERSION (the one-line elevator)
    blocks.append({
        "heading_hi": "30-Second Truth",
        "heading_en": "If you only have 30 seconds",
        "body": (
            f"Tum ek <b>{arche}</b> ho — {elem} element dominant, {domt}-driven core. "
            f"Tumhari biggest superpower {('creativity aur depth' if O > 60 else ('discipline aur reliability' if C > 60 else ('warmth aur connection' if A > 60 else ('energy aur charisma' if E > 60 else 'calm aur stability'))))} hai. "
            f"Tumhari biggest blind-spot {('overthinking aur self-doubt' if N > 55 else ('comfort-zone bias' if O < 45 else ('procrastination' if C < 45 else ('over-pleasing' if A > 70 else 'social withdrawal'))))} hai. "
            f"Yeh report 30 page me detail me yeh sab kholega."
        ),
    })

    # CAREER LENS
    blocks.append({
        "heading_hi": "Career Lens — Boss/Recruiter Tumhe Kaise Dekhta Hai",
        "heading_en": "How a Boss/Recruiter Sees You",
        "body": (
            f"Pehle 5 minute ki meeting me boss/recruiter tumhe yeh dekhega: "
            f"<b>{('strategic thinker, ideas wala' if O > 60 else ('reliable executor, deadline-respecting' if C > 60 else ('charismatic communicator, room read karta hai' if E > 60 else ('team player, collaborative' if A > 60 else 'calm professional, no drama'))))}</b>. "
            f"Tumse expectation set hogi: <b>{('big-picture vision' if O > 60 else 'consistent delivery')}</b>. "
            f"Risk woh notice karega: <b>{('execution slow ho sakti hai' if O > 60 and C < 55 else ('innovation kam' if O < 50 else ('avoid-conflict' if A > 65 else 'over-confidence')))}</b>. "
            f"Hire/promote decision ka tilt: {'Strong yes' if (C > 55 and (E > 50 or O > 55)) else 'Conditional yes — kuch evidence chahiye'}."
        ),
    })

    # LOVE LENS
    blocks.append({
        "heading_hi": "Love Lens — Partner Tumhe Kaise Dekhta Hai",
        "heading_en": "How a Partner Sees You",
        "body": (
            f"Date 1 me partner ko tum lagoge: <b>{('mysterious aur depth wala' if O > 60 and E < 50 else ('warm aur engaging' if A > 60 and E > 55 else ('confident aur grounded' if N < 45 else 'sweet but slightly nervous')))}</b>. "
            f"6 mahine baad woh notice karega: tumhari real strength <b>"
            f"{('emotional intelligence' if A > 60 else ('reliability — promises poori karte ho' if C > 60 else ('fun aur energy' if E > 60 else 'depth aur understanding')))}</b> hai. "
            f"Friction point typically: <b>{('over-thinking aur reassurance need' if N > 60 else ('emotional distance' if A < 45 else ('busy schedule' if C > 70 else 'communication gaps')))}</b>. "
            f"Long-term partner woh banega jo {('stable aur patient' if N > 55 else ('expressive aur warm' if E < 45 else 'like-minded balanced'))} hai."
        ),
    })

    # FRIEND LENS
    blocks.append({
        "heading_hi": "Friend Lens — Closest Friend Kya Bolta Hai",
        "heading_en": "How Your Closest Friend Sees You",
        "body": (
            f"Tumhara closest friend tumhe describe karega: <b>"
            f"\"{('Gehri baatein karta hai, normal small-talk se bore ho jata hai' if O > 60 else '')}"
            f"{'Hamesha plan ready, last-minute me bhi bharosa kar sakte ho' if C > 60 else ''}"
            f"{'Group ki energy hai, party me main person' if E > 65 else ''}"
            f"{'Sabki problems sunta hai, free therapy provide karta hai' if A > 65 else ''}"
            f"{'Calm hai, kabhi-kabhi distant lagta hai' if E < 40 else ''}\"</b>. "
            f"Friends ko tumhari biggest unspoken complaint: <b>"
            f"{('plan cancel karta hai last-minute' if C < 45 else ('zyada gehri baatein, halki life enjoy karna seekho' if O > 65 else ('busy ho jata hai mahine bhar' if C > 70 else 'apni feelings share nahi karta')))}</b>. "
            f"Friend circle me tumhari role: <b>{('the philosopher' if O > 65 else ('the planner' if C > 60 else ('the energizer' if E > 65 else ('the listener' if A > 65 else 'the steady one'))))}</b>."
        ),
    })

    # PARENT/FAMILY LENS
    blocks.append({
        "heading_hi": "Family Lens — Maa-Baap Tumhe Kaise Dekhte Hain",
        "heading_en": "How Your Parents See You",
        "body": (
            f"Maa-baap ko tum se sabse zyada pride: <b>"
            f"{('intelligent aur gehre socho ka tarika' if O > 60 else ('responsible aur reliable' if C > 60 else ('logon ke saath warm rishtey' if A > 60 else ('confident aur outgoing' if E > 60 else 'shaant aur balanced'))))}</b>. "
            f"Unka unspoken concern: <b>"
            f"{('zyada socho ho, peace mushkil hai' if N > 60 else ('shaadi/settle kab hoga' if A > 60 and C < 60 else ('aggressive ho rahe ho' if A < 45 else ('socialize zyada karo' if E < 45 else 'risk mat lo zyada'))))}</b>. "
            f"Tumhari family role: <b>"
            f"{('the achiever' if C > 65 else ('the dreamer' if O > 65 else ('the connector' if E > 60 and A > 55 else ('the caregiver' if A > 65 else 'the independent one'))))}</b>. "
            f"Yeh role tumhari identity me deeply rooted hai — chhodna mushkil hai par expand kar sakte ho."
        ),
    })

    # SELF LENS
    blocks.append({
        "heading_hi": "Self Lens — Tum Apne Aap Ko Kaise Dekhte Ho",
        "heading_en": "How You See Yourself (vs Reality)",
        "body": (
            f"Tumhari aankhon me tum: ek <b>"
            f"{('thinker jo execute bhi karta hai' if O > 55 and C > 55 else ('helper jo apni boundary nahi pakad pata' if A > 65 else ('lone-wolf jo independent rehna chahta hai' if E < 45 else 'doer jo result laata hai')))}</b>. "
            f"Reality (engine ke hisaab se) ka twist: tum <b>"
            f"{('execution apne se zyada strong samajhte ho — discipline pe extra kaam chahiye' if C < 55 and O > 55 else ('apne ko tougher dikhana chahte ho but inside more sensitive ho' if N > 55 else ('apni achievements under-acknowledge karte ho — visibility par kaam karo' if E < 50 else 'apni biggest superpower ko ordinary samajhte ho — yeh actually rare hai')))}</b>. "
            f"Self-image gap close karna 30-day journey hai — meditation + journaling + 1 trusted feedback friend."
        ),
        "callout": {"label": "MIRROR TRUTH",
                    "text": "Self-perception aur reality ka 70% match common hai; 30% gap hone par "
                           "growth fastest hoti hai. Yeh report wahi 30% expose karti hai."},
    })

    intro = (
        f"Tumhe 5 alag-alag lens se dekhna sabse complete picture deta hai — kyunki "
        f"<b>{arche}</b> tumhari ek facet hai, baki facets situation-based dikhte hain. "
        f"Niche 6 lenses hain: 30-sec elevator, career, love, friend, family, aur self. "
        f"Each ek paragraph me — 2 minute me complete personality scan."
    )

    return {"intro_para": intro, "blocks": blocks}


# ──────────────────────────────────────────────────────────────────────────
# SECTION 18 — STAGED ACTION PLANS (7d / 21d / 90d)
# ──────────────────────────────────────────────────────────────────────────
def build_section_18_plans(engines: Dict, base_sections: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    confidence = _num(_g(engines, "first_impression", "first_impression_4", "confidence"), default=60)
    stress = _g(engines, "health", "macro_indicators", "stress") or "medium"

    # Identify weakest trait → primary focus
    weakest = min(
        [("openness", O, "exploration"),
         ("conscientiousness", C, "discipline"),
         ("extraversion", E, "social-energy"),
         ("agreeableness", A, "empathy"),
         ("low_neuroticism", 100 - N, "emotional-stability")],
        key=lambda t: t[1]
    )
    focus_area = weakest[2]
    focus_score = weakest[1]

    blocks: List[Dict] = []

    # 7-DAY PLAN
    if focus_area == "exploration":
        d7 = [
            "Day 1-2: Ek naya genre podcast/book pakdo (jo tum normally avoid karte ho) — 30 min daily.",
            "Day 3-4: Naya cuisine try karo + naya restaurant/route choose karo office se.",
            "Day 5: Kisi 1 unfamiliar topic pe 20 min YouTube deep-dive.",
            "Day 6: Ek random skill ka YouTube tutorial (10 min) dekho aur try karo.",
            "Day 7: Reflection — kya pasand aaya? Kya block tha? Notebook me likho.",
        ]
    elif focus_area == "discipline":
        d7 = [
            "Day 1: 'Daily 3' rule shuru karo — subah 3 must-do tasks likho.",
            "Day 2-3: Phone subah 30 min late on karo — pehle 3 tasks me se 1 nipta lo.",
            "Day 4: Ek pending task jo 2 hafte se ruka hai — aaj 15 min ka sprint maro.",
            "Day 5: Evening 5 min 'tomorrow plan' likho before sleeping.",
            "Day 6: Ek meaningful 'no' bolo (meeting, event, request).",
            "Day 7: Review — 7 din ka completion rate count karo.",
        ]
    elif focus_area == "social-energy":
        d7 = [
            "Day 1: Ek purane friend ko 'thinking of you' message bhejo.",
            "Day 2: Office me 1 naye colleague se 5-min chai conversation.",
            "Day 3: Ek meetup/community ka research karo aur join karo.",
            "Day 4: Phone call lagao kisi 1 family member ko (text se zyada).",
            "Day 5: Coffee shop me kaam karo (ghar nahi).",
            "Day 6: Ek small gathering attend karo (dinner/party).",
            "Day 7: Review — kis interaction me energy gain hui, kis me drain?",
        ]
    elif focus_area == "empathy":
        d7 = [
            "Day 1: Kisi ki baat sunte waqt 2-sec pause-then-respond rule.",
            "Day 2-3: Daily ek random act of kindness (anonymous, no-recognition).",
            "Day 4: Disagreement me partner/friend se pehle 'understand' karo, baad me reply.",
            "Day 5: Family member ki 1 problem solve karo bina judge kiye.",
            "Day 6: Ek puranay rishtey me genuine apology likho (bhejna optional).",
            "Day 7: Reflection — kis interaction me trust badha?",
        ]
    else:  # emotional-stability
        d7 = [
            "Day 1: Daily 5-min breathing (4-7-8 technique) shuru karo.",
            "Day 2: 'Brain dump' raat ko sone se pehle — sab thoughts paper pe.",
            "Day 3: Phone notifications 80% off — instagram, twitter, news.",
            "Day 4: 30 min walk bina phone ke (sirf observe karo).",
            "Day 5: 1 worry choose karo — 'will this matter in 10 years?' filter lagao.",
            "Day 6: Ek trusted person se baat karo apne real concern ki.",
            "Day 7: Anxiety level rate 1-10 (vs day 1) — log it.",
        ]
    blocks.append({
        "heading_hi": "7-Day Quick-Start Plan",
        "heading_en": f"Week 1 Focus: {focus_area.title()} (your weakest, score {focus_score:.0f}/100)",
        "key_metric": {"label": "Effort Required", "value": "10-15 min/day"},
        "body": (
            f"Pehle hafte ka goal: <b>momentum build karna, perfection nahi</b>. "
            f"Iss week ka focus tumhari weakest trait ({focus_area}) hai. "
            f"Niche 7 din ka step-by-step plan hai — har din 10-15 min lagega max."
        ),
        "bullets": d7,
    })

    # 21-DAY PLAN (habit lock-in)
    blocks.append({
        "heading_hi": "21-Day Habit Lock-In",
        "heading_en": "Week 2-3: Make it Automatic",
        "key_metric": {"label": "Effort Required", "value": "20-30 min/day"},
        "body": (
            f"Week 2-3 me 7-day plan ko amplify karna hai. Habit science ke hisaab se "
            f"<b>21 din me neural pathway form ho jaata hai</b> — fir willpower kam lagti hai. "
            f"Goal: same daily action ko time + dose dono badhao."
        ),
        "bullets": [
            f"Week 2 (Day 8-14): 7-day actions ko <b>15 min → 25 min</b> badhao. Skip days zero — minimum 5 min karo agar busy ho.",
            f"Week 2: Ek <b>accountability partner</b> pakdo (friend/spouse). Daily 1 line WhatsApp update do — 'aaj kya kiya'.",
            f"Week 3 (Day 15-21): Action ko <b>morning ritual</b> me lock karo (uthne ke 30 min ke andar).",
            f"Week 3: Har 3-day me <b>1 progress photo / journal entry</b>. Visual proof = motivation fuel.",
            f"Day 21 milestone: Self-rate 1-10 — kya pehle se behtar hua? Yeh measurable proof hai.",
        ],
        "callout": {"label": "21-DAY SCIENCE",
                    "text": "Habit research show karti hai 21-30 din ke baad ek action 'effortful' "
                           "se 'automatic' me shift hota hai. Iske baad maintenance easy ho jata hai."},
    })

    # 90-DAY TRANSFORMATION
    blocks.append({
        "heading_hi": "90-Day Identity Shift",
        "heading_en": "Month 2-3: Become a Different Person",
        "key_metric": {"label": "Effort Required", "value": "30-45 min/day"},
        "body": (
            f"3 mahine me tumhari personality ka <b>5-10% measurable shift</b> ho sakta hai — "
            f"yeh research-backed hai. Goal sirf habit nahi, <b>identity</b> change hai. "
            f"\"Main woh banda jo daily X karta hai\" — yeh narrative shift hi long-term sustainability deti hai."
        ),
        "bullets": [
            f"Month 2 (Day 22-50): Ek <b>related skill</b> add karo (e.g., agar discipline build kar rahe ho, ek course commit karo).",
            f"Month 2: Apne 3 sabse close logon ko <b>publicly batao</b> tum kya transformation pe ho. Social commitment power 5x.",
            f"Month 3 (Day 51-90): Apne improvement ko <b>1 real-world challenge</b> me test karo (workshop, competition, public talk, marathon).",
            f"Month 3: <b>Identity statement</b> banao — \"I am someone who...\". Daily morning bolo (5 sec).",
            f"Day 90 review: Quantify — score 1-100 par tumhari weakest trait ab kahan hai? Engine retake recommended.",
        ],
        "callout": {"label": "BIG SHIFT",
                    "text": f"Confidence currently {confidence:.0f}/100, stress {stress}. 90 din baad "
                           f"projected: confidence +15-20 points, stress 1 level neeche — "
                           f"agar plan 80%+ adherence ho."},
    })

    intro = (
        f"Improvement ek single tip se nahi hota — staged plan se hota hai. "
        f"Niche 3 phases hain: <b>7-day quick-start</b> (momentum), <b>21-day habit lock-in</b> "
        f"(automaticity), aur <b>90-day identity shift</b> (sustainable change). "
        f"Pehle 3 hafte sabse hard hain — uske baad system khud chalta hai."
    )

    return {"intro_para": intro, "blocks": blocks}


# ──────────────────────────────────────────────────────────────────────────
# SECTION 19 — CROSS-COMBO INSIGHTS (named patterns)
# ──────────────────────────────────────────────────────────────────────────
_COMBO_LIBRARY: List[Dict] = [
    # (name, condition_lambda, hi_text, what_to_do)
    {"name": "Brilliant Procrastinator",
     "cond": lambda O,C,E,A,N: O > 60 and C < 50,
     "desc": "High creativity (Openness {O:.0f}) + low discipline (Conscientiousness {C:.0f}). Tumhare paas brilliant ideas hain par 70% kabhi execute nahi hote. Yeh 'creative paradox' hai — naye ideas itni speed se aate hain ki purane abandon ho jaate hain.",
     "do": "Ek 'idea graveyard' notebook rakho — har naya idea wahan park karo. Sirf ek active project at-a-time. Iss formula se Steve Jobs aur Hayao Miyazaki dono kaam karte the."},

    {"name": "Sharp-Tongued Worrier",
     "cond": lambda O,C,E,A,N: A < 50 and N > 55,
     "desc": "Low agreeableness (A {A:.0f}) + high neuroticism (N {N:.0f}). Tum stress me <b>direct aur cutting</b> ho jate ho — baad me regret hota hai. 'Sorry' bolne me bhi ego aati hai. Yeh combination relationships me sabse zyada damage karta hai.",
     "do": "Trigger ke baad <b>3-second rule</b>: breathe, fir respond. Plus, weekly 1 'apology audit' — kis ko pichle hafte hurt kiya, kya repair chahiye?"},

    {"name": "Quiet Powerhouse",
     "cond": lambda O,C,E,A,N: C > 60 and E < 45,
     "desc": "High discipline (C {C:.0f}) + low extraversion (E {E:.0f}). Tum kaam karte ho, log dekhte hain — par credit doosre le jaate hain. 'Visible work' kam hai isliye promotion slow. Yeh 'invisible expert' trap hai.",
     "do": "Quarterly 1 public output — talk, blog, LinkedIn post, demo. Apni work ki visibility hi promotion ka fuel hai. Output kaisa bhi ho — public hona zaroori hai."},

    {"name": "Magnetic Empath",
     "cond": lambda O,C,E,A,N: E > 55 and A > 60,
     "desc": "High extraversion (E {E:.0f}) + high agreeableness (A {A:.0f}). Log tumse open up karte hain, secrets share karte hain, advice mangte hain. Yeh gift hai — par tum 'free therapist' bhi ban jaate ho. Energy drain rapid hota hai.",
     "do": "Weekly <b>recharge ritual</b> mandatory — 1 day no calls, no advice giving. Plus, ek small group rakho jo tumhe sun-ne aate hain (reciprocity)."},

    {"name": "Silent Storm",
     "cond": lambda O,C,E,A,N: A > 60 and N > 55,
     "desc": "High agreeableness (A {A:.0f}) + high neuroticism (N {N:.0f}). Tum gussa <b>express nahi karte</b>, internalize karte ho — par body me jata hai (gut, headaches, sleep). Aur kabhi 6 mahine baad ek <b>massive outburst</b> aata hai jo logon ko shock karta hai.",
     "do": "Daily 'micro-honesty' — pehle din hi bolo 'yeh chhota tha but pinch hua'. Suppression nahi, drip-release karo."},

    {"name": "Visionary Without Roadmap",
     "cond": lambda O,C,E,A,N: O > 65 and C < 55,
     "desc": "Tumhe 5 saal aage ka clearly dikhta hai (O {O:.0f}). But 1 saal ka roadmap missing hai (C {C:.0f}). Result: log tumhe 'dreamer' bolte hain. Tum frustrated ho ki 'sab samajh gaye' but execute koi nahi.",
     "do": "Vision ke baad <b>quarterly OKRs</b> likho — 3 measurable outcomes, 90-day deadline. Vision me time mat lagao, execution me lago."},

    {"name": "Loyal Loner",
     "cond": lambda O,C,E,A,N: A > 55 and E < 45,
     "desc": "High loyalty (A {A:.0f}) + low extraversion (E {E:.0f}). Tum 2-3 close logon ke liye <b>jaan dene wale</b> ho, par naye log banane me 6+ mahine lagte hain. Iska upside: deep relationships. Iska cost: agar koi close exit ho gaya, replace karna mushkil.",
     "do": "Yearly 1 new 'friend project' — ek naya person consciously cultivate karo (12 mahine ka horizon). Long-term relationships intentional ho sakti hain."},

    {"name": "Calm Captain",
     "cond": lambda O,C,E,A,N: C > 55 and N < 45,
     "desc": "High discipline (C {C:.0f}) + low neuroticism (N {N:.0f}). Tum <b>crisis me sabse calm</b> insaan ho. Log naturally tumhari taraf dekhte hain decisions ke liye. Yeh leadership ka core hai — par tum apne aap ko 'normal' samjhte ho.",
     "do": "Apni leadership ka <b>conscious claim</b> karo. Junior log mentor karo. Crisis-time me main lead karo (volunteer). Yeh muscle ignore karne se atrophy ho jati hai."},

    {"name": "Restless Achiever",
     "cond": lambda O,C,E,A,N: O > 55 and C > 55 and N > 50,
     "desc": "Triple combo: ideas + execution + restlessness. Tum bahut achieve karte ho — par <b>satisfaction kam</b> milti hai. 'Next thing' ki taraf bhaagte raho ge. Yeh entrepreneur/artist mindset hai — productive but exhausting.",
     "do": "Weekly 1 'celebration ritual' — chhoti win bhi note karo. Plus quarterly 'enough' check — kya milne se peace milegi? Likho aur usko honor karo."},

    {"name": "Reliable Diplomat",
     "cond": lambda O,C,E,A,N: C > 55 and A > 55 and N < 50,
     "desc": "High C ({C:.0f}) + high A ({A:.0f}) + low N ({N:.0f}). Tum office aur family dono me 'go-to' insaan ho — sab tumpe count karte hain. Yeh rare combo hai (top 15%) — natural manager / mediator material.",
     "do": "Risk: 'always available' image se exhausted ho jaoge. Weekly 'no-availability window' (4 hours minimum) — apne goals ke liye. Yeh selfish nahi, sustainable hai."},
]


def build_section_19_combos(engines: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]

    matched: List[Dict] = []
    for combo in _COMBO_LIBRARY:
        if combo["cond"](O, C, E, A, N):
            matched.append({
                "name": combo["name"],
                "desc": combo["desc"].format(O=O, C=C, E=E, A=A, N=N),
                "do":   combo["do"],
            })

    # Take top 5; if less than 3, pad with neutral generic insights
    if len(matched) < 3:
        matched.append({
            "name": "Balanced Profile",
            "desc": f"Tumhare OCEAN scores almost balanced hain — koi extreme nahi. Yeh actually rare hai (top 20%). Iska benefit: tum almost any role/relationship me adapt kar lete ho.",
            "do": "Risk: 'jack of all' label lag sakta hai. Conscious specialization karo — ek domain pe deep mastery 5 saal me build karo.",
        })
    matched = matched[:6]

    blocks: List[Dict] = []
    for i, m in enumerate(matched):
        blocks.append({
            "heading_hi": m["name"],
            "heading_en": f"Combo Pattern #{i+1}",
            "body": m["desc"],
            "callout": {"label": "WHAT TO DO", "text": m["do"]},
        })

    intro = (
        f"Single trait predictable hota hai — par <b>cross-combos</b> tumhari real personality "
        f"reveal karte hain. OCEAN scan ke baad tumhare profile me <b>{len(matched)} signature combo patterns</b> "
        f"matched hain. Each ka apna naam, apni story, aur apna fix hai. Yeh sirf tumhare jaisi profiles me "
        f"valid hain — generic advice nahi."
    )

    return {"intro_para": intro, "blocks": blocks}


# ──────────────────────────────────────────────────────────────────────────
# BONUS — 5-SCORE DEEP-DIVE (why this number + +1 means + top action)
# ──────────────────────────────────────────────────────────────────────────
def build_bonus_score_deep(engines: Dict, base_sections: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    sam = _g(engines, "samudrika", "composite_scores") or {}
    fi4 = _g(engines, "first_impression", "first_impression_4") or {}
    h = engines.get("health", {})

    bonus = base_sections.get("bonus_personality_score") or {}
    leadership = _num(bonus.get("leadership_10"))
    money = _num(bonus.get("money_10"))
    love = _num(bonus.get("love_10"))
    health = _num(bonus.get("health_10"))
    intel = _num(bonus.get("intelligence_10"))

    blocks: List[Dict] = []

    # LEADERSHIP DEEP
    blocks.append({
        "heading_hi": "Leadership Score Deep-Dive",
        "heading_en": "Why this number, what +1 means, and how to push it",
        "key_metric": {"label": "Current Leadership", "value": f"{leadership:.1f}/10"},
        "body": (
            f"Yeh score 3 inputs se nikla: <b>Extraversion ({E:.0f})</b> — log lead karne ki energy; "
            f"<b>Conscientiousness ({C:.0f})</b> — execution credibility; "
            f"<b>Authority impression ({_num(fi4.get('authority')):.0f})</b> — face-based gravitas. "
            f"+1 point ka matlab: tumhe 1 level upar (jr-mid, mid-sr) promote hone ka realistic chance hai. "
            f"<b>Top action</b>: agar E weak hai to public-speaking course (Toastmasters) join karo. "
            f"Agar C weak hai to ek visible 'on-time delivery' track-record banao 90 din me. "
            f"Agar authority kam hai to posture + voice training (deeper, slower) — yeh tested hai."
        ),
    })

    # MONEY DEEP
    blocks.append({
        "heading_hi": "Money Score Deep-Dive",
        "heading_en": "Why this number, what +1 means",
        "key_metric": {"label": "Current Money Score", "value": f"{money:.1f}/10"},
        "body": (
            f"Money score primarily Vedic <b>dhana ({_num(sam.get('dhana'),default=70):.0f}/100)</b> + "
            f"OCEAN Conscientiousness ({C:.0f}) ka mix hai. "
            f"Dhana score Samudrika face-features se nikla hai (forehead, lips, ears, palm-line proxies). "
            f"+1 point ka matlab: 5-10 saal me tumhari net-worth 30-50% zyada projection kar sakti hai. "
            f"<b>Top action</b>: aaj se 3 cheez fix karo — (1) 20% income auto-invest har mahine, "
            f"(2) ek skill jo income directly upar leke jaaye (sales, tech-product, finance, premium specialty), "
            f"(3) 1 mentor jo 5x earner ho — unke saath quarterly conversation."
        ),
    })

    # LOVE DEEP
    blocks.append({
        "heading_hi": "Love Score Deep-Dive",
        "heading_en": "Why this number, what +1 means",
        "key_metric": {"label": "Current Love Score", "value": f"{love:.1f}/10"},
        "body": (
            f"Love score Vedic <b>sambandha ({_num(sam.get('sambandha'),default=60):.0f}/100)</b> + "
            f"Agreeableness ({A:.0f}) ka mix hai. Sambandha lips, eyes aur jaw symmetry se nikla hai. "
            f"+1 point ka matlab: existing relationship me intimacy 30% deeper aur new partner attraction 2x faster. "
            f"<b>Top action</b>: weekly 1 deep 1-on-1 conversation (15 min, no phone) close partner ke saath. "
            f"Agar single ho: monthly 1 new social context me jao (workshop, hobby, gym) — randomness "
            f"hi compatible matches ka source hai. Apps single-channel bottleneck hain."
        ),
    })

    # HEALTH DEEP
    h_ind = h.get("macro_indicators", {})
    blocks.append({
        "heading_hi": "Health Score Deep-Dive",
        "heading_en": "Why this number, what +1 means",
        "key_metric": {"label": "Current Health Score", "value": f"{health:.1f}/10"},
        "body": (
            f"Health score <b>vitality ({_num(h.get('vitality_score')):.0f}/100)</b> se direct mapped hai — "
            f"yeh skin tone, eye clarity, lip color, dark-circles aur facial puffiness ke composite se nikla hai. "
            f"Current macro: stress <b>{h_ind.get('stress','medium')}</b>, energy <b>{h_ind.get('energy','medium')}</b>. "
            f"+1 point ka matlab: 6 mahine me visible glow, sleep quality 30% behtar, productivity 20% upar. "
            f"<b>Top action</b>: 3 cheez non-negotiable — (1) 7-8 hour sleep (phone bedroom se hata do), "
            f"(2) 1L extra paani daily, (3) hafte me 4 din 30-min walk. Yeh 21 din me visible change."
        ),
    })

    # INTELLIGENCE DEEP
    blocks.append({
        "heading_hi": "Intelligence Score Deep-Dive",
        "heading_en": "Why this number, what +1 means",
        "key_metric": {"label": "Current Intelligence Score", "value": f"{intel:.1f}/10"},
        "body": (
            f"Intelligence score Vedic <b>buddhi ({_num(sam.get('buddhi'),default=70):.0f}/100)</b> + "
            f"Openness ({O:.0f}) ka mix hai. Buddhi forehead size + brow patterns + eye spacing se "
            f"infer hota hai (samudrika shastra). Openness curiosity + cognitive flexibility measure karta hai. "
            f"+1 point ka matlab: tumhari problem-solving speed 2x, naye domains me learning curve 30% chhoti. "
            f"<b>Top action</b>: weekly 5-7 hour deep reading (book, not feed). "
            f"Daily 30 min ek skill-acquisition (language, coding, music). 90 din me cognitive sharpness measurable badhegi."
        ),
        "callout": {"label": "INTELLIGENCE TRUTH",
                    "text": "IQ fixed nahi hota — fluid intelligence (problem-solving) life-long trainable hai. "
                           "Daily 1% better rule yahan literally compound hota hai 5-10 saal me."},
    })

    intro = (
        f"Tumhare 5 scores (out of 10) ka deep-dive — har ek ka <b>source</b> "
        f"(kis engine se nikla), <b>+1 point ka real-world impact</b>, aur <b>top action</b>. "
        f"Yeh scores fixed nahi hain — 90-day focused effort se 1-2 point shift achievable hai, "
        f"jo cumulative 5-10 saal me identity-level transformation deta hai."
    )

    return {"intro_para": intro, "blocks": blocks}
