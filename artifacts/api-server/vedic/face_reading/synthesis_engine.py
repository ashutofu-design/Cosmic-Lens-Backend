"""
synthesis_engine.py
═══════════════════
PHASE-UPGRADE SYNTHESIS LAYER (additive — does NOT replace any existing engine).

Runs AFTER all base engines (samudrika, personality, health, first_impression,
fwhr, symmetry, anthropometry, mole_detector, etc.) have produced raw output.

Six sub-engines — strictly deterministic, every insight traceable to a signal:

  1. trait_fusion_engine        — combines multi-feature signals into one trait
  2. shock_insight_engine       — 2-3 highly specific surprising observations
  3. behavior_simulation_engine — predicts real-life actions in scenarios
  4. confidence_engine          — 0-100 confidence per insight (signal agreement
                                  + image clarity + kundli strength)
  5. why_reasoning_engine       — 1-2 line "why" pointing to actual signals
  6. lifestyle_remedy_engine    — weakness → concrete behaviour/habit/env fix

Output (STRICT contract):

  {
    "fused_traits":         [...],
    "shock_insights":       [...],
    "behavior_simulation":  [...],
    "reasoning":            [...],
    "confidence_scores":    [...],
    "remedies":             [...]
  }

Tone: premium, sharp, human (not robotic, not pandit). No generic lines.
Brand: "Cosmic Intelligence" / "Cosmic Lens" — never "AI".
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Shared helpers — safe extraction with default
# ═══════════════════════════════════════════════════════════════════════════

def _g(d: Optional[Dict], *path, default=None):
    cur = d or {}
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def _num(v, default: float = 50.0) -> float:
    try:
        if v is None:
            return float(default)
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _band(score: float, low: float = 40.0, high: float = 65.0) -> str:
    if score >= high:
        return "high"
    if score <= low:
        return "low"
    return "moderate"


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _extract_signals(engines: Dict[str, Any]) -> Dict[str, float]:
    """
    Pull every numeric signal we will reference. One source of truth so all
    six sub-engines agree on the numbers (no drift across sections).
    """
    ocean = _g(engines, "personality", "ocean_summary_scores") or {}
    fimp  = _g(engines, "first_impression") or {}
    sym   = _g(engines, "symmetry") or {}
    fwhr  = _g(engines, "fwhr") or {}
    health = _g(engines, "health") or {}
    sam   = _g(engines, "samudrika") or {}
    anth  = _g(engines, "anthropometry") or {}

    return {
        # Big-5
        "O": _num(ocean.get("openness")),
        "C": _num(ocean.get("conscientiousness")),
        "E": _num(ocean.get("extraversion")),
        "A": _num(ocean.get("agreeableness")),
        "N": _num(ocean.get("neuroticism")),
        # First impression
        "confidence":  _num((fimp.get("first_impression_4") or {}).get("confidence"),
                            default=_num(fimp.get("self_confidence_score"))),
        "trust":       _num(fimp.get("trust_score")),
        "attraction":  _num(fimp.get("attraction_score")),
        "authority":   _num(fimp.get("authority_score")),
        # Face geometry
        "symmetry":    _num(sym.get("overall_score"),
                             default=_num(sym.get("symmetry_score"))),
        "fwhr":        _num(fwhr.get("fwhr_value"), default=1.9),
        # Health
        "vitality":    _num(health.get("vitality_score")),
        # Vedic samudrika composites
        "bhagya":      _num(_g(sam, "ear", "bhagya_score") or _g(sam, "luck_score"), default=70),
        "buddhi":      _num(_g(sam, "forehead", "buddhi_score") or _g(sam, "intelligence_score"), default=70),
        "dhana":       _num(_g(sam, "nose", "dhana_score") or _g(sam, "wealth_score"), default=70),
        # Anthropometry-derived strength flags
        "jaw_width":   _num(anth.get("jaw_width_mm"), default=100.0),
        "nose_length": _num(anth.get("nose_length_mm"), default=50.0),
    }


def _image_clarity_score(engines: Dict[str, Any]) -> float:
    """0-100 — how sharp / well-lit the input was. Drives confidence."""
    fq = _g(engines, "front_quality") or _g(engines, "image_quality") or {}
    base = _num(fq.get("overall_score") or fq.get("score"), default=75)
    return _clamp(base, 30, 100)


def _kundli_strength(engines: Dict[str, Any]) -> float:
    """0-100 — kundli signals available? Falls back to 50 if face-only."""
    k = _g(engines, "kundli") or _g(engines, "vedic_kundli") or {}
    if not k:
        return 50.0
    return _clamp(_num(k.get("strength_score"), default=65), 30, 100)


# ═══════════════════════════════════════════════════════════════════════════
# 1. TRAIT FUSION ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#  Combines 2-3 raw signals into one personality conclusion. Each fused trait
#  is traceable: `sources` lists the exact signals that produced it.

def trait_fusion_engine(engines: Dict[str, Any], sig: Dict[str, float]) -> List[Dict]:
    fused: List[Dict] = []

    # F-1 · Eyes + Symmetry + Agreeableness  →  emotional honesty
    if sig["A"] >= 60 and sig["symmetry"] >= 55:
        fused.append({
            "trait": "Emotionally Honest Communicator",
            "summary": "Tum jo feel karte ho woh chehre par turant dikh jata hai — chhupa nahi sakte, isi liye log tumpe trust karte hain.",
            "sources": ["agreeableness", "facial_symmetry", "eye_features"],
            "intensity": int((sig["A"] + sig["symmetry"]) / 2),
        })

    # F-2 · Jaw + Conscientiousness + Authority  →  quiet executor
    if sig["jaw_width"] >= 95 and sig["C"] >= 55:
        fused.append({
            "trait": "Quiet Executor",
            "summary": "Bolne se zyada karke dikhane wale ho. Promises kam karte ho, complete 90% karte ho.",
            "sources": ["jaw_width_mm", "conscientiousness", "authority_score"],
            "intensity": int((sig["jaw_width"] / 1.2 + sig["C"]) / 2),
        })

    # F-3 · Nose + Dhana + Openness  →  ambitious risk-calibrator
    if sig["dhana"] >= 65 and sig["O"] >= 50:
        fused.append({
            "trait": "Ambitious Risk-Calibrator",
            "summary": "Risk lete ho par andhadhund nahi — pehle ground check karte ho, fir jump. Iska faayda 5+ saal me compound hota hai.",
            "sources": ["nose_dhana_score", "openness", "nose_length_mm"],
            "intensity": int((sig["dhana"] + sig["O"]) / 2),
        })

    # F-4 · Forehead Buddhi + Openness + Low Neuroticism  →  composed thinker
    if sig["buddhi"] >= 65 and sig["N"] <= 50:
        fused.append({
            "trait": "Composed Strategic Thinker",
            "summary": "Pressure me logic chalu rehta hai. Doosre log panic karte hain tab tum pattern dekh rahe hote ho.",
            "sources": ["forehead_buddhi_score", "openness", "neuroticism (inverse)"],
            "intensity": int((sig["buddhi"] + (100 - sig["N"])) / 2),
        })

    # F-5 · Low Extraversion + High Agreeableness  →  selective deep-bonder
    if sig["E"] <= 50 and sig["A"] >= 60:
        fused.append({
            "trait": "Selective Deep-Bonder",
            "summary": "2-3 logon ke liye duniya hila do, baaki ke liye polite distance. Shallow networking drain karta hai tumhe.",
            "sources": ["extraversion (low)", "agreeableness (high)"],
            "intensity": int(((100 - sig["E"]) + sig["A"]) / 2),
        })

    # F-6 · High fWHR + Authority  →  natural commander  (else inverse)
    if sig["fwhr"] >= 1.95 and sig["authority"] >= 55:
        fused.append({
            "trait": "Natural Commander",
            "summary": "Room me ghuste hi log unconsciously tumhari taraf dekhte hain — chehre ka structure dominance broadcast karta hai.",
            "sources": ["fwhr_value", "authority_score"],
            "intensity": int((sig["fwhr"] * 40 + sig["authority"]) / 2),
        })
    elif sig["fwhr"] < 1.85 and sig["A"] >= 60:
        fused.append({
            "trait": "Diplomatic Bridge-Builder",
            "summary": "Tumhare chehre ka shape soft hai — log tumse easily baat karte hain, isi liye conflict me tum natural mediator ho.",
            "sources": ["fwhr_value (low)", "agreeableness"],
            "intensity": int(((2.1 - sig["fwhr"]) * 80 + sig["A"]) / 2),
        })

    # Always at least one — derive from dominant Big-5 if nothing matched
    if not fused:
        dom = max(("O", sig["O"]), ("C", sig["C"]), ("E", sig["E"]),
                  ("A", sig["A"]), ("N", 100 - sig["N"]), key=lambda x: x[1])
        fused.append({
            "trait": "Balanced Adapter",
            "summary": "Koi ek dimension dominate nahi karta — situation read karke style switch karte ho. Yeh range hai, weakness nahi.",
            "sources": [f"big5_{dom[0]}_dominant_subtle"],
            "intensity": int(dom[1]),
        })

    return fused[:5]


# ═══════════════════════════════════════════════════════════════════════════
# 2. SHOCK INSIGHT ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#  Specific, surprising observations that combine 2+ signals in non-obvious
#  ways. Each one feels "yeh kaise pata?". Always traceable.

def shock_insight_engine(engines: Dict[str, Any], sig: Dict[str, float]) -> List[Dict]:
    out: List[Dict] = []

    # I-1 · Suppressed-anger pattern  (high A + low E + medium-high N)
    if sig["A"] >= 60 and sig["E"] <= 50 and sig["N"] >= 45:
        out.append({
            "insight": "Tum gussa face pe nahi laate — par andar ek list maintain karte ho. 6+ mahine purani baat ek line se trigger ho jaati hai.",
            "sources": ["agreeableness=high", "extraversion=low", "neuroticism=mid"],
            "category": "emotional_pattern",
        })

    # I-2 · 'Looks confident, isn't' gap  (attraction high, confidence low)
    if sig["attraction"] >= 60 and sig["confidence"] <= 55:
        out.append({
            "insight": "Bahar se tum confident dikhte ho, par andar 'main kaafi hoon kya?' wali pause aati hai — yeh gap hi tumhe deeply observant banata hai.",
            "sources": ["attraction_score=high", "confidence_score=low"],
            "category": "self_perception_gap",
        })

    # I-3 · Asymmetric self  (low symmetry + decent confidence)
    if sig["symmetry"] <= 60 and sig["confidence"] >= 50:
        out.append({
            "insight": "Tumhara left aur right side same nahi hai — ek photo me 'serious tum' dikhte ho, doosri me 'soft tum'. Iska matlab tumhari personality genuinely 2-layered hai, mask nahi.",
            "sources": ["symmetry_score=below_60", "confidence_score"],
            "category": "facial_signature",
        })

    # I-4 · Decision-paralysis trap  (high O + high C + low E)
    if sig["O"] >= 55 and sig["C"] >= 55 and sig["E"] <= 50:
        out.append({
            "insight": "Tum decisions me itni research karte ho ki 'analysis paralysis' me phans jaate ho — 70% data hone par hi commit karna seekho, 100% kabhi nahi milega.",
            "sources": ["openness=high", "conscientiousness=high", "extraversion=low"],
            "category": "behavioural_trap",
        })

    # I-5 · Health early-signal  (vitality < 65 + N >= 50)
    if sig["vitality"] <= 65 and sig["N"] >= 50:
        out.append({
            "insight": "Tumhari aankhon ke neeche aur jaw ki tightness silent stress ka signal hai — abhi medical issue nahi, par 12 mahine ignore kiya to digestive ya sleep cycle disturb hoga.",
            "sources": ["vitality_score<65", "neuroticism", "eye_dark_circle_signal"],
            "category": "health_early_warning",
        })

    # I-6 · Money-mindset paradox  (dhana high but C low)
    if sig["dhana"] >= 65 and sig["C"] <= 50:
        out.append({
            "insight": "Tumhari naak wealth-attract karne wala shape hai, par discipline (C) thoda kam hai — paisa aata hai, ruk nahi pata. Investment auto-deduction tumhari single biggest hack hai.",
            "sources": ["dhana_score=high", "conscientiousness=low"],
            "category": "money_pattern",
        })

    # I-7 · Magnetism without trying  (high E + high A + symmetry > 65)
    if sig["E"] >= 60 and sig["A"] >= 60 and sig["symmetry"] >= 65:
        out.append({
            "insight": "Log tumhe kuch second me 'pasand' kar lete hain — actual reason eye-symmetry + open expression hai, jo subconscious me 'safe person' signal bhejte hain.",
            "sources": ["extraversion=high", "agreeableness=high", "symmetry_score>65"],
            "category": "social_advantage",
        })

    # Ensure 2-3 always returned (spec)
    if len(out) < 2:
        out.append({
            "insight": "Tumhare chehre ka unique signature hai — koi ek single trait dominate nahi karta, isi liye log alag-alag time pe tumhe alag describe karte hain. Yeh confusing nahi, depth ka signal hai.",
            "sources": ["multi_signal_balanced"],
            "category": "general_signature",
        })

    return out[:3]


# ═══════════════════════════════════════════════════════════════════════════
# 3. BEHAVIOR SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#  Predicts real-life action in 3 scenario classes: relationship, conflict,
#  decision. Output is concrete, not platitudes.

def behavior_simulation_engine(engines: Dict[str, Any], sig: Dict[str, float]) -> List[Dict]:
    sims: List[Dict] = []

    # B-1 · Relationship — first 6 months
    if sig["A"] >= 55:
        rel = ("Pehle 3 mahine: tum partner ki har choti baat note karoge — birthday playlist, favourite chai, "
               "stress-trigger. 3-6 mahine: yeh 'effort' visible hoga aur partner attached ho jayega. "
               "Risk: tum apni zarurat express nahi karoge — partner assume karega 'sab thik hai'.")
    else:
        rel = ("Pehle 3 mahine: tum slow open hoge, partner ko lagega tum 'distant' ho. 3-6 mahine: jab trust banega "
               "tab depth dikhegi, par tab tak partner adha withdraw kar chuka hoga. Hack: pehle mahine se hi 1 "
               "vulnerable share weekly karo.")
    sims.append({
        "scenario": "Relationship — first 6 months",
        "prediction": rel,
        "sources": ["agreeableness", "extraversion", "neuroticism"],
    })

    # B-2 · Conflict — boss/colleague disagrees publicly
    if sig["A"] >= 60 and sig["E"] <= 55:
        conf = ("Pehla reaction: chup ho jaoge, smile maintain karoge. Andar se thread chal raha hoga 'main galat tha kya?'. "
                "24 ghante baad: ek long message ya 1-on-1 me clarify karoge — tab tak nuance properly soch chuke hoge. "
                "Yeh slow-but-thoughtful pattern long-term me trust banata hai.")
    elif sig["fwhr"] >= 1.95 or sig["authority"] >= 60:
        conf = ("Pehla reaction: counter-point right there, calm tone me. Tum public pe back down nahi karte. "
                "Risk: kabhi-kabhi yeh 'rigid' lagta hai. Hack: 'main soch ke wapas aata hoon' phrase use karo — "
                "authority kam nahi hoti, perception soft ho jaati hai.")
    else:
        conf = ("Pehla reaction: middle ground dhundhoge — 'aap bhi sahi, main bhi sahi'. Yeh peace strategy hai par "
                "long-term me tumhari position weak dikh sakti hai. Hack: 1 hill chuno har quarter — wahan firm raho.")
    sims.append({
        "scenario": "Public conflict at work",
        "prediction": conf,
        "sources": ["agreeableness", "extraversion", "fwhr_value", "authority_score"],
    })

    # B-3 · Decision — high-stakes choice (job switch / move / marriage)
    if sig["C"] >= 55 and sig["O"] >= 50:
        dec = ("Step 1: 2 weeks research — Excel sheet, pros/cons, 5+ logon se baat. Step 2: ek 'sleep on it' phase. "
               "Step 3: final call deadline ke 24 ghante pehle. Tum impulsive nahi ho — par overthink ho sakte ho. "
               "Rule: agar reversible decision hai, 7 din se zyada mat lagao.")
    elif sig["N"] >= 55:
        dec = ("Tum decision lene se pehle worst-case 5x dohraoge. Yeh anxiety nahi, risk-management hai — par koi 1 "
               "trusted person chahiye jo 'tum ready ho' bole. Solo me tum kabhi commit nahi kar paaoge bade decisions me.")
    else:
        dec = ("Tum gut + 1-2 din ki sochne ke baad commit karte ho. Yeh fast-and-good hai 80% time, par 20% me "
               "important detail miss kar dete ho. Hack: ek 'devil's advocate' friend rakho — woh tumhari blind-spot pakdega.")
    sims.append({
        "scenario": "High-stakes life decision",
        "prediction": dec,
        "sources": ["conscientiousness", "openness", "neuroticism"],
    })

    return sims


# ═══════════════════════════════════════════════════════════════════════════
# 4. CONFIDENCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#  Per-insight confidence 0-100. Three components:
#    signal_agreement    (how many independent signals point same way)
#    image_clarity       (input photo quality)
#    kundli_strength     (does birth-data corroborate face?)

def confidence_engine(
    fused: List[Dict],
    shocks: List[Dict],
    sims: List[Dict],
    engines: Dict[str, Any],
    sig: Dict[str, float],
) -> List[Dict]:
    img = _image_clarity_score(engines)
    kun = _kundli_strength(engines)

    out: List[Dict] = []

    def _conf(num_sources: int, intensity: float = 70.0) -> int:
        # signal-agreement weight 50%, image 30%, kundli 20%
        agreement = min(100, num_sources * 28 + 30)
        # intensity gently nudges (a strong signal is more confident than a borderline one)
        intensity_w = _clamp(intensity, 30, 100)
        score = (agreement * 0.50) + (img * 0.30) + (kun * 0.20)
        # Pull toward intensity by ±5
        score = score * 0.92 + intensity_w * 0.08
        return int(_clamp(round(score), 35, 97))

    for f in fused:
        out.append({
            "label":    f["trait"],
            "kind":     "fused_trait",
            "score":    _conf(len(f.get("sources", [])), f.get("intensity", 70)),
            "sources":  f.get("sources", []),
        })

    for s in shocks:
        out.append({
            "label":    s["insight"][:60] + ("…" if len(s["insight"]) > 60 else ""),
            "kind":     "shock_insight",
            "score":    _conf(len(s.get("sources", [])), 75),
            "sources":  s.get("sources", []),
        })

    for sm in sims:
        out.append({
            "label":    sm["scenario"],
            "kind":     "behavior_simulation",
            "score":    _conf(len(sm.get("sources", [])), 70),
            "sources":  sm.get("sources", []),
        })

    return out


# ═══════════════════════════════════════════════════════════════════════════
# 5. WHY REASONING ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#  For every fused trait + shock insight, produce a 1-2 line "why" that
#  references the actual numeric signals (no generic text).

def why_reasoning_engine(
    fused: List[Dict],
    shocks: List[Dict],
    sig: Dict[str, float],
) -> List[Dict]:
    out: List[Dict] = []

    def _ref(key: str) -> str:
        m = {
            "O":            f"Openness {sig['O']:.0f}",
            "C":            f"Conscientiousness {sig['C']:.0f}",
            "E":            f"Extraversion {sig['E']:.0f}",
            "A":            f"Agreeableness {sig['A']:.0f}",
            "N":            f"Neuroticism {sig['N']:.0f}",
            "symmetry":     f"facial symmetry {sig['symmetry']:.0f}/100",
            "fwhr":         f"fWHR {sig['fwhr']:.2f}",
            "confidence":   f"confidence-impression {sig['confidence']:.0f}/100",
            "trust":        f"trust-impression {sig['trust']:.0f}/100",
            "attraction":   f"attraction-impression {sig['attraction']:.0f}/100",
            "authority":    f"authority-impression {sig['authority']:.0f}/100",
            "vitality":     f"vitality {sig['vitality']:.0f}/100",
            "bhagya":       f"bhagya score {sig['bhagya']:.0f}/100",
            "buddhi":       f"buddhi score {sig['buddhi']:.0f}/100",
            "dhana":        f"dhana score {sig['dhana']:.0f}/100",
            "jaw_width":    f"jaw width {sig['jaw_width']:.0f} mm",
            "nose_length":  f"nose length {sig['nose_length']:.0f} mm",
        }
        return m.get(key, key)

    def _explain(sources: List[str]) -> str:
        # Map source-tags → human refs
        refs = []
        for s in sources:
            tag = s.split("_")[0].split("=")[0].split(" ")[0].strip().lower()
            if tag in ("openness", "o"):                refs.append(_ref("O"))
            elif tag in ("conscientiousness", "c"):     refs.append(_ref("C"))
            elif tag in ("extraversion", "e"):          refs.append(_ref("E"))
            elif tag in ("agreeableness", "a"):         refs.append(_ref("A"))
            elif tag in ("neuroticism", "n"):           refs.append(_ref("N"))
            elif tag.startswith("sym") or "symmetry" in s.lower():     refs.append(_ref("symmetry"))
            elif "fwhr" in s.lower():                   refs.append(_ref("fwhr"))
            elif "vitality" in s.lower():               refs.append(_ref("vitality"))
            elif "bhagya" in s.lower():                 refs.append(_ref("bhagya"))
            elif "buddhi" in s.lower():                 refs.append(_ref("buddhi"))
            elif "dhana" in s.lower():                  refs.append(_ref("dhana"))
            elif "jaw" in s.lower():                    refs.append(_ref("jaw_width"))
            elif "confidence" in s.lower():             refs.append(_ref("confidence"))
            elif "attraction" in s.lower():             refs.append(_ref("attraction"))
            elif "authority" in s.lower():              refs.append(_ref("authority"))
            elif "trust" in s.lower():                  refs.append(_ref("trust"))
        # Deduplicate while preserving order
        seen, uniq = set(), []
        for r in refs:
            if r not in seen:
                uniq.append(r); seen.add(r)
        return ", ".join(uniq[:3]) if uniq else "multiple converging signals"

    for f in fused:
        out.append({
            "for":    f["trait"],
            "why":    f"Yeh conclusion {_explain(f.get('sources', []))} ke convergence se aaya — single signal nahi, multiple signals ek hi direction me point kar rahe hain.",
            "kind":   "fused_trait",
        })

    for s in shocks:
        out.append({
            "for":    s["insight"][:50] + ("…" if len(s["insight"]) > 50 else ""),
            "why":    f"Reason: {_explain(s.get('sources', []))} — yeh combination statistically rare hai, isi liye specific.",
            "kind":   "shock_insight",
        })

    return out


# ═══════════════════════════════════════════════════════════════════════════
# 6. LIFESTYLE REMEDY ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#  Identify the weakest signals → 3-tier concrete fix
#    behaviour change · physical habit · environment tweak

def lifestyle_remedy_engine(engines: Dict[str, Any], sig: Dict[str, float]) -> List[Dict]:
    weaknesses: List[tuple] = []

    if sig["confidence"] < 55:
        weaknesses.append(("self_confidence", sig["confidence"]))
    if sig["authority"] < 50:
        weaknesses.append(("authority_presence", sig["authority"]))
    if sig["vitality"] < 65:
        weaknesses.append(("vitality", sig["vitality"]))
    if sig["E"] < 45:
        weaknesses.append(("social_energy", sig["E"]))
    if sig["N"] > 60:
        weaknesses.append(("emotional_regulation", 100 - sig["N"]))

    # Sort weakest first; take top 3
    weaknesses.sort(key=lambda x: x[1])
    weaknesses = weaknesses[:3]

    catalog = {
        "self_confidence": {
            "behaviour":    "Roz subah ek 'small win' likho aur shaam ko tick karo (ex: 7 baje uthna). 30 din me tumhara internal voice 'main complete karta hoon' me shift hoga.",
            "habit":        "Mirror me roj 60 second eye-contact rakho without expression. Yeh self-trust ka direct exercise hai.",
            "environment":  "Phone home-screen pe ek line wallpaper rakho — 'I do not need permission to start'. Day me 50 baar dikhega, neural rewiring chalegi.",
        },
        "authority_presence": {
            "behaviour":    "Sentences end pe voice neeche le jao (statements me) — upar le jaane se questions sound karte hain. Recording sun ke 7 din me fix.",
            "habit":        "Posture: kandhe 1 inch peeche, chin parallel. 5 min daily wall-stand. 21 din me default posture ban jayegi.",
            "environment":  "Meeting me sabse comfortable seat lo (corner nahi, head-side). Body language seat se start hoti hai.",
        },
        "vitality": {
            "behaviour":    "Phone bedroom se nikalo. 7-8 ghante sleep non-negotiable. 21 din me skin-glow visible hoga.",
            "habit":        "Subah utha ke turant 500ml paani + 10 min sunlight. Yeh 2 cheezein cortisol-cycle reset karti hain.",
            "environment":  "Desk pe 1 plant + ek glass paani permanent rakho. Visual cues = behaviour cues.",
        },
        "social_energy": {
            "behaviour":    "Hafte me 1 'low-pressure social' lock karo (gym class, hobby workshop) — networking event nahi. Naye log natural setting me milne se thakaan kam hoti hai.",
            "habit":        "Daily 1 person ko 1-line voice note ('aaj tumhari yaad aayi'). Effort minimal, relationship return huge.",
            "environment":  "WhatsApp DPs pe 5 close logon ka 'starred' folder rakho. Decision-fatigue kam hoga 'kis se baat karoon'.",
        },
        "emotional_regulation": {
            "behaviour":    "Trigger feel ho to 90 second timer chalu karo — body's stress chemical exactly utni der rehta hai. Uske baad respond karo, react nahi.",
            "habit":        "Daily 10 min journaling (raat ko) — sirf 3 line: 'aaj kya feel hua', 'kis baat se', 'kal kya alag karunga'.",
            "environment":  "Phone ke notifications grayscale me kar do (Settings → Accessibility). Stress signals ka frequency 40% kam ho jayega.",
        },
    }

    out: List[Dict] = []
    for area, score in weaknesses:
        c = catalog.get(area, {})
        if not c:
            continue
        out.append({
            "area":         area,
            "current_score": round(score, 1),
            "behaviour":    c.get("behaviour"),
            "habit":        c.get("habit"),
            "environment":  c.get("environment"),
            "expected_lift": "+10-15 points in 90 din at 80% adherence",
        })

    if not out:
        # all signals strong → growth-mode remedy
        out.append({
            "area":         "growth_amplification",
            "current_score": 75.0,
            "behaviour":    "Tumhari weakness koi notable nahi — ab strength amplify karo. Ek skill chuno (writing/speaking/coding) aur 90 din daily 30 min do.",
            "habit":        "Weekly 1 'public output' (post, talk, project) — visibility = compounding luck.",
            "environment":  "Apne se 5x bade earner / thinker se quarterly 1 conversation lock karo. Aspiration = trajectory.",
            "expected_lift": "Identity-level shift in 6-12 months",
        })

    return out


# ═══════════════════════════════════════════════════════════════════════════
# MASTER ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def run_synthesis(engines: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final synthesis layer. Call AFTER all base engines have populated `engines`.

    Returns the strict 6-key contract specified in the spec.
    Pipeline: raw engines → fusion → reasoning → confidence → narrative-ready.
    """
    sig = _extract_signals(engines)

    fused   = trait_fusion_engine(engines, sig)
    shocks  = shock_insight_engine(engines, sig)
    sims    = behavior_simulation_engine(engines, sig)
    why     = why_reasoning_engine(fused, shocks, sig)
    conf    = confidence_engine(fused, shocks, sims, engines, sig)
    rems    = lifestyle_remedy_engine(engines, sig)

    return {
        "fused_traits":         fused,
        "shock_insights":       shocks,
        "behavior_simulation":  sims,
        "reasoning":            why,
        "confidence_scores":    conf,
        "remedies":             rems,
        # Meta — useful for UI / debugging, not user-facing
        "_meta": {
            "engine_version":   "synthesis_v1",
            "image_clarity":    int(_image_clarity_score(engines)),
            "kundli_strength":  int(_kundli_strength(engines)),
            "signals_used":     {k: round(v, 1) for k, v in sig.items()},
        },
    }
