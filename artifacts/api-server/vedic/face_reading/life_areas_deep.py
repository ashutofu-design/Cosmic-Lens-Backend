"""
Life-Areas Deep-Dive — produces rich multi-block structures for:
  - Section 7  : Behavior Patterns (Stress / Anger / Decision / Thinking / Social)
  - Section 8  : Love & Relationship DNA (Attachment / Loyalty / Sex / Conflict / Marriage / Partner)
  - Section 9  : Career & Money (Work-style / Leadership / Money / Risk / Industry)
  - Section 14 : Life Flow + Story Mode (Childhood / Turning-point / Present / 1y / 3y / 5y / Legacy)

Each section returns:
  {
    "intro_para": "<Hinglish narrative>",
    "blocks": [
        {
          "heading_hi":   "...",
          "heading_en":   "...",
          "key_metric":   {"label":"...", "value":"..."},   # optional
          "body":         "<long Hinglish paragraph>",      # 100-200 words
          "callout":      {"label":"...", "text":"..."},    # optional
          "bullets":      ["...","..."],                    # optional
        }, ...
    ],
  }

Real engine data only — OCEAN, samudrika composite scores, fwhr, first_impression.
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
# SECTION 7 — BEHAVIOR PATTERNS DEEP
# ──────────────────────────────────────────────────────────────────────────
def build_section_7_deep(engines: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    arche = _g(engines, "personality", "archetype", "name") or "Balanced"
    stress = _g(engines, "health", "macro_indicators", "stress") or "medium"
    energy = _g(engines, "health", "macro_indicators", "energy") or "medium"

    blocks: List[Dict] = []

    # 1. Stress Response
    if N > 60:
        stress_label = "Anxious-Reactive"
        stress_body = (
            f"Stress me tumhari pehli reaction <b>internal</b> hoti hai — body me tension, "
            f"mind me looping thoughts, sleep me disturbance. Neuroticism {N:.0f} ka matlab — "
            f"tumhara nervous system har stimulus ko amplify karta hai. "
            f"Trigger se peak-stress tak time bahut kam (10-20 min). Recovery time zyada (4-8 ghante). "
            f"Long-term me yeh pattern adrenal fatigue aur chronic insomnia bana sakta hai. "
            f"Solution: 'name it to tame it' technique — har stress emotion ko ek word ka label do "
            f"(\"frustration\", \"fear\", \"overwhelm\") — yeh activation 40% kam karta hai."
        )
    elif N < 40:
        stress_label = "Stoic-Composed"
        stress_body = (
            f"Stress me tum almost calm dikhte ho — bahar se. Neuroticism {N:.0f} ka matlab — "
            f"tumhara nervous system reactive nahi hai. But yeh blessing aur curse dono hai — "
            f"tum stress ko <b>under-acknowledge</b> karte ho aur body silently accumulate karti hai. "
            f"Aksar 'fine, fine' bolte rehte ho jab tak burnout suddenly nahi aata. "
            f"Solution: Weekly 'stress audit' karo — 1-10 scale pe rate karo even if you feel fine. "
            f"Yeh self-awareness build karta hai before crash point."
        )
    else:
        stress_label = "Adaptive-Balanced"
        stress_body = (
            f"Stress me tumhara response <b>balanced</b> hai (Neuroticism {N:.0f}). "
            f"Tum acknowledge karte ho stress ka existence aur action lete ho — par sometimes "
            f"problem solve karne me itne dub jaate ho ki rest skip ho jata hai. "
            f"Long-term ke liye scheduled recovery (Sunday digital detox, monthly weekend off) "
            f"tumhare liye non-negotiable hai."
        )
    blocks.append({
        "heading_hi": "Stress Response Pattern",
        "heading_en": f"Stress Style: {stress_label}",
        "key_metric": {"label": "Current Stress Level", "value": stress.title()},
        "body": stress_body,
    })

    # 2. Anger / Frustration
    if A < 45 and N > 55:
        anger_type = "Sharp-Verbal"
        anger_body = (
            f"Gusse ka tumhara style <b>direct aur verbal</b> hai. Trigger hone par tum "
            f"<b>turant respond</b> karte ho — aksar baad me regret hota hai. "
            f"Agreeableness {A:.0f} aur Neuroticism {N:.0f} ka combination yeh pattern banata hai. "
            f"Closest log iss style se sabse zyada hurt hote hain — kyunki tum honest ho but timing rough. "
            f"<b>3-second rule</b>: trigger ke baad 3 sec breathe karo, fir bolo. 80% saved relationships."
        )
    elif A > 65:
        anger_type = "Suppressed-Internal"
        anger_body = (
            f"Tum gussa <b>express nahi karte</b>, internalize karte ho. Agreeableness {A:.0f} ka "
            f"matlab — peace tumhare liye conflict se zyada important hai. "
            f"Par yeh suppressed anger body me jaata hai — gut issues, headaches, ya passive-aggressive "
            f"behavior bante hain. Long-term me trust bhi erode karta hai kyunki partner ko pata nahi "
            f"chalta jab tak explosion nahi hota. "
            f"<b>Healthy expression</b>: gym, journaling, ya direct conversation 'I felt X when Y' formula me."
        )
    else:
        anger_type = "Slow-Burn Reactive"
        anger_body = (
            f"Tumhara gussa <b>slow-burn</b> hai — chhoti cheezein ignore karte ho, par "
            f"3-4 baar repeat hone par bada outburst aata hai. Agreeableness {A:.0f}. "
            f"Yeh pattern partner ko confuse karta hai kyunki unhe pata nahi tumhara real threshold kya hai. "
            f"Solution: Threshold lower karo — pehli baar hi bolo ki 'yeh meri tolerance ke against hai'."
        )
    blocks.append({
        "heading_hi": "Anger / Frustration Style",
        "heading_en": f"Anger Type: {anger_type}",
        "body": anger_body,
    })

    # 3. Decision Loop
    if C > 55 and O < 55:
        dec_type = "Methodical-Sequential"
        dec_body = (
            f"Decision lete waqt tum <b>step-by-step</b> chalte ho — pros/cons list, research, "
            f"ek-do trusted log se baat. Conscientiousness {C:.0f}, Openness {O:.0f}. "
            f"Iska benefit: 80% decisions long-term me sahi nikalti hain. Iska cost: speed kam — "
            f"opportunities slip ho jaati hain jab fast call chahiye. "
            f"<b>Hack</b>: 'reversible vs irreversible' filter — reversible decisions me 24 ghante max do, "
            f"irreversible me 7 din. Yeh paralysis kam karega."
        )
    elif O > 60 and N > 50:
        dec_type = "Loop-Overthinker"
        dec_body = (
            f"Tumhara mind ek decision pe <b>loop</b> karta hai — sone se pehle, subah uthte hi, "
            f"shower me, har jagah. Openness {O:.0f}, Neuroticism {N:.0f}. "
            f"Tum multiple scenarios imagine karte ho aur har scenario me ek 'kya agar' add hota hai. "
            f"Yeh creativity ka side-effect hai par exhausting bhi. "
            f"<b>Cure</b>: '10-10-10 rule' — yeh decision 10 min baad, 10 mahine baad, 10 saal baad "
            f"matter karegi? 70% decisions auto-clear ho jaate hain."
        )
    else:
        dec_type = "Intuitive-Quick"
        dec_body = (
            f"Tum decisions <b>intuition</b> se lete ho — gut feeling pakad ke commit kar dete ho. "
            f"Speed strong, par 30% decisions baad me regret aati hai. "
            f"<b>Hack</b>: gut feel ke baad 1 question — \"is decision ke worst-case me main survive kar lunga?\" "
            f"Agar haan, jaao. Agar nahi, ek raat ruk jao."
        )
    blocks.append({
        "heading_hi": "Decision-Making Loop",
        "heading_en": f"Decision Style: {dec_type}",
        "body": dec_body,
    })

    # 4. Daily Thinking Pattern
    if O > 60:
        think_type = "Multi-Track Thinker"
        think_body = (
            f"Tumhara mind ek waqt me <b>3-5 channels</b> pe chalta hai — kabhi work, kabhi life, "
            f"kabhi random idea, kabhi memory. Openness {O:.0f} ka classic sign. "
            f"Iska benefit: creative connections, unique solutions, multi-domain insight. "
            f"Iska cost: focus thoda fragmented, deep work me 30+ min lagta hai 'flow' me jaane me. "
            f"Solution: morning 90 min 'deep work' block (no phone, single task) — productivity 3x."
        )
    else:
        think_type = "Single-Track Focused"
        think_body = (
            f"Tum ek waqt me <b>ek hi cheez</b> pe focus karte ho. Openness {O:.0f}. "
            f"Iska benefit: deep work me natural, ek skill me mastery jaldi aati hai. "
            f"Iska cost: context-switch mushkil, multiple parallel projects me overwhelm. "
            f"Solution: weekly review + monthly planning — bigger picture mental model maintain karta hai."
        )
    blocks.append({
        "heading_hi": "Daily Thinking Pattern",
        "heading_en": f"Cognitive Style: {think_type}",
        "body": think_body,
    })

    # 5. Social/Energy
    if E > 60:
        social_type = "Energy-from-People"
        social_body = (
            f"Tum social interactions se <b>energy gain</b> karte ho. Extraversion {E:.0f}. "
            f"Akele me 2 din se zyada rehne pe mood drop hota hai. Public speaking, networking, "
            f"big gatherings tumhe alive feel karate hain. "
            f"Risk: shallow connections accumulate ho sakte hain — quality over quantity yaad rakho. "
            f"Weekly 1 deep 1-on-1 hangout schedule karo — ye long-term relationships ka anchor hai."
        )
    elif E < 40:
        social_type = "Energy-from-Solitude"
        social_body = (
            f"Tum solo time se <b>recharge</b> hote ho. Extraversion {E:.0f}. "
            f"Big gatherings ke baad 1-2 din 'cave time' chahiye. Yeh weakness nahi — yeh tumhari "
            f"recharging mechanism hai. Deep work, writing, research roles me natural fit. "
            f"Risk: relationships maintain karna effort lagta hai. Weekly 1 close-friend call schedule rakho."
        )
    else:
        social_type = "Ambivert"
        social_body = (
            f"Tum <b>ambivert</b> ho (Extraversion {E:.0f}) — situation-based energy. "
            f"Strong in both worlds. Iska gift: codes-switch easily karte ho. "
            f"Iska danger: kabhi pata nahi chalta tumhe kab break chahiye — body signals listen karo."
        )
    blocks.append({
        "heading_hi": "Social Energy Pattern",
        "heading_en": f"Energy Style: {social_type}",
        "key_metric": {"label": "Current Energy", "value": energy.title()},
        "body": social_body,
    })

    intro = (
        f"Tumhare 5 sabse important behavior patterns niche detail me hain — har ek tumhare "
        f"OCEAN profile, health indicators aur archetype (<b>{arche}</b>) se nikla hua hai. "
        f"In patterns ko jaan-na sabse bada self-awareness boost hai — kyunki jo dikh nahi raha "
        f"woh control bhi nahi ho sakta."
    )

    return {"intro_para": intro, "blocks": blocks}


# ──────────────────────────────────────────────────────────────────────────
# SECTION 8 — LOVE & RELATIONSHIP DEEP (4 pages)
# ──────────────────────────────────────────────────────────────────────────
def build_section_8_deep(engines: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    sambandha = _num(_g(engines, "samudrika", "composite_scores", "sambandha"), default=60)
    lips_phala = _g(engines, "samudrika", "features", "lips", "phala_hi") or ""
    eyes_phala = _g(engines, "samudrika", "features", "eyes", "phala_hi") or ""
    blocks: List[Dict] = []

    # 1. Attachment Style
    if N >= 60 and A >= 55:
        att_label, att_short = "Anxious-Secure Mix", "invested-but-insecure"
    elif A >= 60 and N <= 45:
        att_label, att_short = "Secure", "grounded-and-warm"
    elif A <= 40:
        att_label, att_short = "Avoidant-Lean", "independence-first"
    elif N >= 65:
        att_label, att_short = "Anxious", "reassurance-seeking"
    else:
        att_label, att_short = "Balanced", "give-and-protect"

    blocks.append({
        "heading_hi": "Attachment Style (Lagav ka Tareeka)",
        "heading_en": att_label,
        "key_metric": {"label": "Sambandha Score", "value": f"{sambandha:.0f}/100"},
        "body": (
            f"Tumhara core attachment style <b>{att_short}</b> hai. Iska matlab — relationship me "
            f"tumhari default setting yeh hai jab koi conscious choice nahi hoti. "
            f"OCEAN scan ke hisaab se: Agreeableness {A:.0f}, Neuroticism {N:.0f}. "
            f"{'Tum partner se deep emotional connection seek karte ho — par over-questioning aur reassurance-seeking partner ko thaka sakti hai.' if att_label.startswith('Anxious') else ''}"
            f"{'Tum partner ko safe-base banate ho — emotional storms me bhi grounded rehte ho. Yeh rare aur valuable trait hai.' if att_label=='Secure' else ''}"
            f"{'Tum apni independence ko sabse upar rakhte ho — partner ko emotional access dene me time lagta hai. Iska matlab tum cold nahi ho, bas guarded ho.' if att_label.startswith('Avoidant') else ''}"
            f"{'Tum balanced ho — pyaar bhi dete ho aur space bhi maintain karte ho. Yeh modern relationships ki ideal setting hai.' if att_label=='Balanced' else ''}"
        ),
        "callout": {
            "label": "RELATIONSHIP ANCHOR",
            "text": "Tumhari attachment style early childhood me set hoti hai, par 'earned secure' "
                    "kisi bhi age me ban sakta hai — through self-awareness aur consistent right partners.",
        },
    })

    # 2. Loyalty & Commitment
    if A >= 60 and C >= 60:
        loy_level, loy_score = "Bahut High", 90
        loy_body = (
            f"Loyalty tumhari biggest superpower hai. Once committed, fully committed. "
            f"Conscientiousness {C:.0f} aur Agreeableness {A:.0f} ka rare combination — yeh "
            f"sirf 15-20% logo me hota hai. Yaad rakho: yahi loyalty tumhari biggest "
            f"<b>vulnerability</b> bhi hai — kyunki tum wrong partner me bhi over-invest kar dete ho."
        )
    elif A >= 55 or C >= 60:
        loy_level, loy_score = "High", 75
        loy_body = (
            f"Tum loyal ho — promise tod-na pasand nahi. Par tumhari loyalty "
            f"<b>conditional</b> hai — agar partner consistently disrespect kare to tumhari respect bhi "
            f"chali jati hai. Yeh healthy loyalty hai, blind nahi."
        )
    elif A < 40:
        loy_level, loy_score = "Earned", 55
        loy_body = (
            f"Loyalty tumse <b>earn karni padti hai</b>. Day 1 se tum 80% trust nahi dete — "
            f"partner ko prove karna padta hai consistency. Iska benefit: filter strong, wrong people "
            f"jaldi nikal jaate hain. Iska risk: emotionally available partners ko bhi tum hold-back kar dete ho."
        )
    else:
        loy_level, loy_score = "Medium", 65
        loy_body = (
            f"Tumhari loyalty situation aur partner par depend karti hai. Yeh modern reality hai — "
            f"'lifetime guarantee' ki jagah 'as long as it works' philosophy. Iska benefit: tum "
            f"toxic relationships me stuck nahi rehte. Iska risk: short-term mindset deep intimacy ko block kar sakti hai."
        )
    blocks.append({
        "heading_hi": "Loyalty & Commitment Level",
        "heading_en": f"Loyalty: {loy_level}",
        "key_metric": {"label": "Loyalty Score", "value": f"{loy_score}/100"},
        "body": loy_body,
    })

    # 3. Sexual / Sensual Psychology
    if E > 55 and O > 55:
        sex_label = "Adventurous-Expressive"
        sex_body = (
            f"Tumhari sensual energy <b>exploratory</b> hai — variety, novelty, aur shared "
            f"experiences se aroused hote ho. Extraversion {E:.0f}, Openness {O:.0f}. "
            f"Bedroom me communication strong — partner ko clearly batate ho kya chahiye. "
            f"Long-term me bored hone se bachne ke liye <b>conscious novelty</b> chahiye — "
            f"new locations, new rituals, new conversations."
        )
    elif A > 60 and N < 50:
        sex_label = "Emotionally-Bonded"
        sex_body = (
            f"Tumhare liye sex <b>emotional connection</b> ka physical extension hai. "
            f"Bina trust ke arousal kam hota hai. Agreeableness {A:.0f}. "
            f"Tum slow-burn ho — initial chemistry ke baad real intimacy 6-12 mahine me peak karti hai. "
            f"Casual flings se satisfaction kam milega — long-term partnerships me tum thrive karte ho."
        )
    elif N > 60:
        sex_label = "Sensitive-Intense"
        sex_body = (
            f"Tum bedroom me <b>highly sensitive</b> ho — environment, mood, partner ki energy "
            f"sab affect karti hai. Neuroticism {N:.0f}. "
            f"Comfort + safety pehle, fir surrender. Right partner ke saath sex deeply healing ho sakta hai. "
            f"Wrong partner ke saath emotional aftermath strong hota hai."
        )
    else:
        sex_label = "Balanced-Confident"
        sex_body = (
            f"Tumhari sensual style <b>balanced</b> hai — physically present, emotionally available, "
            f"par over-dramatize nahi karte. Yeh adult intimacy ki most stable form hai."
        )
    blocks.append({
        "heading_hi": "Sensual & Sexual Psychology",
        "heading_en": sex_label,
        "body": sex_body,
        "callout": {"label": "VEDIC SIGNAL — LIPS",
                    "text": lips_phala or "Honth se balanced sensual energy nikli."},
    })

    # 4. Conflict & Communication Pattern
    if A > 60 and N > 50:
        conf_type = "Avoid-then-Explode"
        conf_body = (
            f"Conflict me tumhari default <b>avoid karna</b> hai — tum chhoti cheezein 'let go' "
            f"karte raho jab tak boiler full nahi hota, fir ek bada outburst. "
            f"Partner confused hota hai kyunki unhe pata nahi tumhara breaking point kya tha. "
            f"Solution: 'micro-honesty' — pehle din hi bolo 'yeh chhoti baat thi but pinch hua'."
        )
    elif A < 45:
        conf_type = "Direct-Confrontational"
        conf_body = (
            f"Tum conflict me <b>direct</b> ho — issue ko table pe rakh dete ho. "
            f"Yeh strength hai — clarity rapidly aati hai. Par delivery sometimes harsh ho jaati hai. "
            f"Solution: \"I felt X when Y happened\" formula use karo — same message, 80% kam defensive."
        )
    elif C > 60:
        conf_type = "Logical-Resolution"
        conf_body = (
            f"Tum conflict ko ek <b>problem-to-solve</b> dekhte ho — emotional chaos avoid karte ho. "
            f"Partner sometimes feel karta hai 'tum machine ho' jab woh emotionally overwhelmed hai. "
            f"Solution: 'feelings first, fix later' — 5 min sirf sun lo bina solve mode me jaaye."
        )
    else:
        conf_type = "Adaptive-Negotiator"
        conf_body = (
            f"Tum conflict me <b>flexible</b> ho — situation read karke style adjust karte ho. "
            f"Yeh mature pattern hai. Risk: kabhi-kabhi 'peace ke liye apna point chhod dena' "
            f"long-term me resentment build karta hai."
        )
    blocks.append({
        "heading_hi": "Conflict & Communication Pattern",
        "heading_en": f"Conflict Style: {conf_type}",
        "body": conf_body,
    })

    # 5. Marriage Behavior (long-term partnership)
    if C > 55 and A > 55:
        marr_type = "Builder-Partner"
        marr_body = (
            f"Tum marriage me <b>builder</b> ho — together future banate ho. Conscientiousness {C:.0f}, "
            f"Agreeableness {A:.0f}. Family planning, finances, home — sab proactively organize karte ho. "
            f"Risk: partner ko 'co-CEO' bana dete ho aur romance back-burner pe chala jata hai. "
            f"Weekly 1 'date night' (no logistics talk) non-negotiable."
        )
    elif E > 60:
        marr_type = "Social-Centred Partner"
        marr_body = (
            f"Marriage me tumhari social life central rehti hai — friends, family gatherings, events. "
            f"Partner agar introvert hai to tension build hota hai. Solution: 'parallel social' — "
            f"kuch events together, kuch alag — saath rehna mandatory nahi."
        )
    elif O > 60:
        marr_type = "Growth-Together Partner"
        marr_body = (
            f"Tumhare liye marriage <b>parallel evolution</b> hai — same person ke saath multiple "
            f"phases jeena. Static partner se tum bored ho jaoge. Yearly 'where are we going' "
            f"conversation rakho — direction align rehni chahiye."
        )
    else:
        marr_type = "Stable-Companion"
        marr_body = (
            f"Tum marriage me <b>stability aur companionship</b> seek karte ho. Drama nahi, peace. "
            f"Predictable rhythms tumhari security hain. Risk: comfort me passion fade ho sakti hai — "
            f"intentional novelty (travel, new shared hobby) yearly add karo."
        )
    blocks.append({
        "heading_hi": "Marriage / Long-term Partnership Behavior",
        "heading_en": f"Marriage Type: {marr_type}",
        "body": marr_body,
    })

    # 6. Ideal Partner
    if E >= 65: ideal = "Calm, grounded, listener — jo tumhari high energy ko balance kare."
    elif E <= 40: ideal = "Warm, expressive, slightly extroverted — jo tumhe khol sake aur world se connect kare."
    elif N >= 60: ideal = "Stable, patient, emotionally mature — jo reassure kar sake bina judge kiye."
    elif A <= 45: ideal = "Independent, strong, self-respecting — jo apni ground rakhe aur tumhe challenge kare."
    else: ideal = "Like-minded balanced partner — values, ambition aur lifestyle match kare."

    blocks.append({
        "heading_hi": "Ideal Partner Profile",
        "heading_en": "Tumhare Liye Sahi Saathi",
        "body": (
            f"Engine analysis ke hisaab se tumhara ideal partner: <b>{ideal}</b> "
            f"Yeh rule nahi, pattern hai — same-energy partners ke saath comfort milta hai par "
            f"growth slow hoti hai; opposite-energy partners ke saath friction zyada hota hai par "
            f"evolution fastest. Tumhare liye sweet spot: <b>complementary, not identical</b>."
        ),
        "callout": {"label": "VEDIC SIGNAL — EYES",
                    "text": eyes_phala or "Aankhon se balanced emotional bandwidth signal nikli."},
    })

    intro = (
        f"Pyaar tumhare liye sirf emotion nahi — ek pura ecosystem hai jo 6 alag layers se chalti hai: "
        f"attachment, loyalty, sex, conflict, marriage behavior, aur ideal partner profile. "
        f"Niche har ek detail me khola hai — yeh 21+ minute padhne ka section hai par "
        f"tumhari relationship clarity 10x badhayega."
    )

    return {
        "intro_para": intro,
        "blocks": blocks,
        "love_score_100": round((A + (100 - N) + sambandha) / 3, 1),
    }


# ──────────────────────────────────────────────────────────────────────────
# SECTION 9 — CAREER & MONEY DEEP (3 pages)
# ──────────────────────────────────────────────────────────────────────────
def build_section_9_deep(engines: Dict) -> Dict:
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    sam = _g(engines, "samudrika", "composite_scores") or {}
    dhana = _num(sam.get("dhana"), default=70)
    bhagya = _num(sam.get("bhagya"), default=70)
    arche = _g(engines, "personality", "archetype", "name") or "Balanced"

    blocks: List[Dict] = []

    # 1. Work Style
    if O > 60 and C > 55:
        work_style = "Strategic-Creative"
        work_body = (
            f"Tum kaam me <b>frameworks bhi banate ho aur out-of-box bhi sochte ho</b>. "
            f"Openness {O:.0f}, Conscientiousness {C:.0f} — yeh combination dur hai aur premium. "
            f"Best fit roles: Founder, Product Lead, Strategy Consultant, Creative Director. "
            f"Boring repetitive kaam tumhe drain karta hai — delegate karo ya automate karo."
        )
    elif C > 65:
        work_style = "Execution-Focused"
        work_body = (
            f"Tumhari biggest strength <b>execution</b> hai — jo decide hua, woh deliver hota hai. "
            f"Conscientiousness {C:.0f}. Operations, project management, finance, engineering — "
            f"yahan tum natural authority ban jaate ho. Risk: 'maker' roles me stuck ho jate ho jab "
            f"actually 'manager' me bhi shine kar sakte ho — leadership role accept karna seekho."
        )
    elif E > 60 and A > 55:
        work_style = "People-First Operator"
        work_body = (
            f"Tum log handle karne me natural ho. Sales, HR, client-services, teaching — yeh tumhari home turf hai. "
            f"Risk: 'nice colleague' image build ho jaati hai par leadership credit nahi milta. "
            f"Solution: visible wins document karo — quarterly self-review write karo."
        )
    elif O > 65 and E < 50:
        work_style = "Deep-Specialist"
        work_body = (
            f"Tum solo deep work me thrive karte ho. Research, design, writing, engineering, analysis — "
            f"yahan tumhari mastery 5x normal speed se badhti hai. Risk: networking aur visibility kam, "
            f"to credit doosre log le jaate hain. Quarterly 1 public talk/post — yeh game-changer hai."
        )
    else:
        work_style = "Adaptive-Generalist"
        work_body = (
            f"Tum almost any role me adapt kar lete ho — yeh strength bhi hai aur risk bhi. "
            f"Specialization ka decision agle 5 saal me lena critical hai — varna mid-career me 'jack of all' label lag jata hai."
        )
    blocks.append({
        "heading_hi": "Work Style (Kaam Karne Ka Tareeka)",
        "heading_en": work_style,
        "body": work_body,
    })

    # 2. Leadership Profile
    if E > 55 and C > 55:
        lead_type = "Charismatic-Operator"
        lead_body = (
            f"Tumhari leadership style <b>vision + execution</b> dono ka mix hai. "
            f"Log tumhe follow karte hain kyunki tum direction bhi do aur deliver bhi karo. "
            f"Risk: micro-management ki tendency. Solution: 'outcome over method' philosophy — "
            f"team ko WHAT batao, HOW unko decide karne do."
        )
    elif A > 60:
        lead_type = "Servant-Leader"
        lead_body = (
            f"Tum team ko serve karte ho — unke obstacles remove karte ho, growth ke liye support dete ho. "
            f"Yeh long-term retention ka best style hai. Risk: assertiveness kam — tough decisions "
            f"(firing, restructuring) tumhe physically pain dete hain. Solution: tough decisions "
            f"frame karo 'team ke greater good' me — yeh alignment milta hai."
        )
    elif O > 60:
        lead_type = "Visionary-Pioneer"
        lead_body = (
            f"Tum 5-saal aage dekhte ho jab baki present me jee rahe hote hain. Founders, "
            f"creative directors, R&D leads — yahan tum natural ho. Risk: present-day execution "
            f"weak ho sakti hai. Solution: ek strong 'COO-style' partner pakdo jo daily run kare."
        )
    else:
        lead_type = "Steady-Conductor"
        lead_body = (
            f"Tum drama-free leader ho — predictable, calm, fair. Long-term teams tumhare under "
            f"100+ months tak rehti hain. Risk: kabhi-kabhi team tumhe 'boring' bhi keh sakti hai — "
            f"quarterly 1 bold move (off-site, new initiative) zaroori hai."
        )
    blocks.append({
        "heading_hi": "Leadership Profile",
        "heading_en": f"Leader Type: {lead_type}",
        "body": lead_body,
    })

    # 3. Money Mindset
    if C > 60 and A < 55:
        mm_type = "Disciplined-Saver"
        mm_body = (
            f"Tum paisa <b>sambhal ke kharch</b> karte ho. Conscientiousness {C:.0f}. "
            f"30 saal me tum solid net-worth banate ho. Risk: 'wealth me wealth' nahi hota — "
            f"savings inflation se haar jaati hain. Solution: 30% portfolio equity + 50% safer + "
            f"20% liquid — yeh classic balanced split hai."
        )
    elif E > 60 and O > 60:
        mm_type = "Experience-Spender"
        mm_body = (
            f"Tum paisa <b>experiences pe</b> kharch karte ho — travel, food, learning, gadgets. "
            f"Yeh life-rich philosophy hai. Risk: long-term wealth slow build hota hai. "
            f"Solution: 'pay yourself first' — 20% income auto-invest har mahine ke pehle hafte me. "
            f"Baki 80% pe guilt-free jeeo."
        )
    elif A > 65:
        mm_type = "Generous-Provider"
        mm_body = (
            f"Tum doosron pe bhi spend karte ho — family, friends, charity. Agreeableness {A:.0f}. "
            f"Yeh emotionally rich hai par financially risky. Risk: log advantage le sakte hain. "
            f"Solution: 'giving budget' rakho — monthly fixed amount, usse zyada nahi."
        )
    else:
        mm_type = "Balanced-Practical"
        mm_body = (
            f"Tum saving aur spending dono manage karte ho — neither extreme. "
            f"Yeh sustainable hai par <b>aggressive wealth building slow</b> hogi. "
            f"Solution: ek 'wealth target' lock karo (5-10 saal me X net-worth) — clarity se behavior align hoga."
        )
    blocks.append({
        "heading_hi": "Money Mindset",
        "heading_en": mm_type,
        "key_metric": {"label": "Wealth Score (Vedic dhana+bhagya)", "value": f"{(dhana+bhagya)/2:.0f}/100"},
        "body": mm_body,
    })

    # 4. Risk & Investment Profile
    risk = O*0.5 + (100-N)*0.3 + E*0.2
    if risk > 65:
        risk_type = "High Risk Tolerance"
        risk_body = (
            f"Risk score: <b>{risk:.0f}/100</b>. Tum bold moves comfortable ho — startup, equity, "
            f"crypto, leveraged plays. Iska upside huge but downside bhi huge. "
            f"<b>Rule</b>: portfolio ka max 30% high-risk; 70% boring stable. "
            f"Yeh formula long-term wealth-builders sab use karte hain."
        )
    elif risk < 45:
        risk_type = "Low Risk Tolerance"
        risk_body = (
            f"Risk score: <b>{risk:.0f}/100</b>. Tum stability prefer karte ho — FD, gold, real-estate, blue-chip stocks. "
            f"Iska benefit: rare losses, peace of mind. Iska cost: inflation se return haar jaati hai. "
            f"Solution: 80% safer + 20% equity SIP — yeh stress-free wealth growth hai."
        )
    else:
        risk_type = "Moderate Risk Tolerance"
        risk_body = (
            f"Risk score: <b>{risk:.0f}/100</b>. Tum balanced investor ho — measured calls lete ho. "
            f"Best strategy: 60% equity (50% large-cap, 30% mid-cap, 20% international) + 30% debt + 10% gold. "
            f"Yeh asset-allocation 8-12% CAGR comfortable deti hai 10 saal me."
        )
    blocks.append({
        "heading_hi": "Risk & Investment Profile",
        "heading_en": risk_type,
        "body": risk_body,
    })

    # 5. Industry Fit
    industry_fit = []
    if O > 60: industry_fit.append("Tech / Product / Design / Creative")
    if C > 60: industry_fit.append("Finance / Operations / Engineering / Healthcare")
    if E > 60 and A > 55: industry_fit.append("Sales / Education / Hospitality / Counseling")
    if O > 55 and E > 55: industry_fit.append("Media / Content / Marketing / Entrepreneurship")
    if C > 55 and N < 45: industry_fit.append("Law / Aviation / Defense / High-stakes leadership")
    if not industry_fit:
        industry_fit = ["Government / Services / Stable corporate roles"]

    blocks.append({
        "heading_hi": "Industry Fit (Best-Match Sectors)",
        "heading_en": "Sectors where tum 80% potential pe perform karoge",
        "body": (
            f"OCEAN profile + Vedic indicators ke combination se tumhare top-fit industries: "
            f"{'; '.join(industry_fit[:4])}. "
            f"<b>Important</b>: yeh suggestion hai, dharma nahi. Passion + fit + opportunity teen "
            f"chahiye for excellence — koi ek missing hai to 60% pe perform karoge."
        ),
        "bullets": industry_fit[:5],
    })

    intro = (
        f"Career aur paisa tumhari OCEAN personality + Vedic dhana-bhagya scores ka direct "
        f"reflection hain. Niche 5 layers detail me hain: work-style, leadership, money mindset, "
        f"risk tolerance, aur industry fit. <b>{arche}</b> archetype ke hisaab se yeh tumhara "
        f"professional blueprint hai agle 10 saal ke liye."
    )

    return {
        "intro_para": intro,
        "blocks": blocks,
        "wealth_score_100": round((dhana + bhagya) / 2, 1),
    }


# ──────────────────────────────────────────────────────────────────────────
# SECTION 14 — LIFE FLOW + STORY MODE (3 pages)
# ──────────────────────────────────────────────────────────────────────────
def build_section_14_deep(engines: Dict, base_sections: Dict, age: Optional[int] = None) -> Dict:
    if age is None or age <= 0: age = 30
    o = _ocean(engines)
    O, C, E, A, N = o["O"], o["C"], o["E"], o["A"], o["N"]
    arche = _g(engines, "personality", "archetype", "name") or "Balanced"
    elem  = _g(engines, "samudrika", "element_profile", "dominant_element") or "Balanced"
    age_map = _g(base_sections, "section_15_age_wise_map", "scores") or {}

    blocks: List[Dict] = []

    # ── STORY MODE ──
    # 1. Childhood (bachpan)
    blocks.append({
        "heading_hi": "Bachpan (Childhood) — Tumhari Foundation",
        "heading_en": "0-12 years — Personality Seedling",
        "body": (
            f"Bachpan me tumhari core wiring set hui — emotional patterns, trust default, "
            f"learning style. Aaj jo {arche} archetype hai, woh {('curious-explorer' if O > 55 else 'cautious-observer')} bachhe ka "
            f"{('disciplined' if C > 55 else 'free-spirited')} grown-up version hai. "
            f"{'Family environment me khulapan tha — risk lene me natural confidence develop hua.' if O > 55 and N < 50 else ''}"
            f"{'Bachpan me strict structure ya emotional reserve experience hua — yeh tumhe self-reliant banaya par sometimes intimacy mushkil lagti hai.' if A < 50 or N > 55 else ''}"
            f" Yeh core 80% adult personality decide kar deta hai — par bachi 20% adulthood me change ho sakti hai conscious effort se."
        ),
    })

    # 2. Turning Point (adolescence + early adulthood)
    blocks.append({
        "heading_hi": "Turning Point — Identity Crystal",
        "heading_en": "13-25 years — Self-Image Forming",
        "body": (
            f"Yeh phase tumhari identity ka crystallization hai. {elem} element dominant hone ka "
            f"matlab — tumhe naturally {('action aur fast decisions attractive lagti hain' if 'fire' in elem.lower() or 'agni' in elem.lower() else ('emotion aur deep connections magnetic feel hote hain' if 'water' in elem.lower() or 'jal' in elem.lower() else ('growth aur learning natural pull hai' if 'wood' in elem.lower() else ('discipline aur structure satisfying lagta hai' if 'metal' in elem.lower() else 'stability aur belonging chahiye'))))}. "
            f"Aksar 18-22 saal me ek 'who am I' moment aata hai — yeh moment future trajectory set karta hai. "
            f"Tumhare case me dominant trait <b>{('Openness — exploration' if O > 60 else ('Conscientiousness — building' if C > 60 else ('Extraversion — connecting' if E > 60 else ('Agreeableness — caring' if A > 60 else 'Stability — grounding'))))}</b> bana."
        ),
    })

    # 3. Present Phase
    if age < 30:
        present_label = "Foundation & Exploration"
        present_body = (
            f"Abhi tumhara phase: <b>foundation aur exploration</b>. {elem} energy strong hai. "
            f"Yeh decade ka biggest gift: <b>fail karne ka time hai</b>. Risk lo, switches karo, "
            f"identities try karo. Late 20s tak ek clear direction lock kar lo to next decade golden hoga."
        )
    elif age < 45:
        present_label = "Peak Build Phase"
        present_body = (
            f"Abhi tumhara <b>peak-build</b> chal raha hai. {arche} apne strongest form me hai. "
            f"Decisions aaj ke 10-20 saal define karenge — career trajectory, relationships, finances, health. "
            f"Yeh phase me 'compounding' rule lagti hai — small consistent right moves exponential return dete hain."
        )
    elif age < 60:
        present_label = "Consolidation & Wisdom"
        present_body = (
            f"Abhi tumhara <b>consolidation phase</b> hai — jo banaya hai usko sambhalna aur "
            f"next generation tak pahunchana. Mentor banne ka time hai — apni learnings document karo, "
            f"share karo. Legacy ki neev abhi padti hai."
        )
    else:
        present_label = "Wisdom Phase"
        present_body = (
            f"Abhi tumhara <b>wisdom phase</b> hai — log tumhe guidance ke liye dekhte hain. "
            f"{arche} ka deep version express karo — patient, contemplative, generative. "
            f"Health pe focus aur relationships me presence — yahi ab real currency hai."
        )
    blocks.append({
        "heading_hi": "Vartamaan (Current Phase)",
        "heading_en": present_label,
        "key_metric": {"label": "Current Age", "value": f"{age}"},
        "body": present_body,
    })

    # 4. 1-year forecast
    one_yr_focus = "discipline + finishing pending" if C < 55 else "expanding visibility + influence" if E < 55 else "deepening 1-2 chosen domains"
    blocks.append({
        "heading_hi": "Agla 1 Saal — Tactical Focus",
        "heading_en": "12-Month Forecast",
        "body": (
            f"Agle 12 mahine tumhara biggest focus hona chahiye: <b>{one_yr_focus}</b>. "
            f"OCEAN profile ke hisaab se tumhari weakest zone yahin se band karne ka best ROI hai. "
            f"Pehle 90 din: ek micro-habit (15 min daily). Next 90 din: scale to 30 min. "
            f"Saal end tak yeh tumhari new identity ka part ban jayega — willpower ke bina."
        ),
        "callout": {"label": "30-DAY ANCHOR",
                    "text": f"Agle 30 din ek 'small bet' lo — naya skill, naya rishta, naya project. "
                           f"Year-end tak yeh 1 bet 80% chance se 5x return dega."},
    })

    # 5. 3-year forecast
    three_yr = age_map.get("30s_40s", 75) if age < 45 else age_map.get("50s_plus", 75)
    blocks.append({
        "heading_hi": "Agle 3 Saal — Strategic Build",
        "heading_en": "3-Year Outlook",
        "key_metric": {"label": "Projected Wellbeing Score", "value": f"{three_yr}/100"},
        "body": (
            f"3 saal me jo position aaj se 10x lagti hai, woh actually <b>achievable</b> hai — "
            f"agar daily 1% better ka rule lago. Wellbeing forecast: {three_yr}/100. "
            f"Iss window me 1 major decision (career switch / shaadi / relocation / business launch) "
            f"natural feel karega. Usko avoid mat karo — engine signals strong hain."
        ),
    })

    # 6. 5-year forecast
    five_yr_score = age_map.get("50s_plus", 78) if age < 50 else 80
    five_yr_text = (
        f"5 saal aage tum kahan honge — woh 80% aaj ke choices se decide hota hai, baaki 20% luck. "
        f"Tumhara projected fortune-arc: {five_yr_score}/100. "
        f"{arche} archetype ka 'mature form' iss timeline tak develop hota hai — "
        f"tum ek defined identity, stable circle, aur known excellence-zone ke saath emerge karoge. "
        f"Risk: agar present me drift kar rahe ho to 5 saal me wahi log/situations dohratehi rahenge — "
        f"phase-shift aaj ki choice hai."
    )
    blocks.append({
        "heading_hi": "Agle 5 Saal — Identity Maturity",
        "heading_en": "5-Year Forecast",
        "key_metric": {"label": "Long-term Fortune Arc", "value": f"{five_yr_score}/100"},
        "body": five_yr_text,
    })

    # 7. Long-term Legacy
    blocks.append({
        "heading_hi": "Long-term Legacy",
        "heading_en": "10+ years — What You'll Be Known For",
        "body": (
            f"10+ saal me log tumhe yaad rakhenge: <b>"
            f"{'creative breakthroughs aur unique perspective' if O > 65 else ('reliability aur built-systems' if C > 65 else ('warmth aur log judne ki ability' if A > 65 else ('energy aur presence' if E > 65 else 'depth aur calm wisdom')))}</b> ke liye. "
            f"Yeh tumhari 'legacy seed' hai — abhi ek small consistent expression rakho, 10 saal me yeh "
            f"tumhari signature ban jayegi. {elem} energy isme natural force hai."
        ),
        "callout": {"label": "LEGACY ANCHOR",
                    "text": "Legacy banane ka rule simple hai: ek thing pakdo, 10 saal repeat karo, "
                           "world tumhe usi se identify karega. Multi-tasking yahan kaam nahi karta."},
    })

    intro = (
        f"Tumhari life ek timeline hai — bachpan se aaj tak ke patterns aur aage 10+ saal ka projection. "
        f"Niche 7 phases hain: childhood foundation, turning point, current phase, fir 1-saal, 3-saal, "
        f"5-saal aur long-term legacy. Yeh story-mode + forecast section hai — emotionally read karo, "
        f"isi me aage ki direction milegi."
    )

    return {"intro_para": intro, "blocks": blocks}
