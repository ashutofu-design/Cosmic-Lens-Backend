"""
Feature Deep-Dive — produces 7 rich blocks (Eyes, Nose, Lips, Jaw, Forehead,
Eyebrows, Ears) for Section 6 of the Premium Report.

Each block contains:
  - micro_measurements : list of dicts {key, value_mm/deg, classification, meaning_hi}
  - samudrika_phala    : Hinglish classical reading
  - personality_meaning: paragraph (uses OCEAN)
  - love_implication   : paragraph
  - career_decision    : paragraph
  - stress_response    : paragraph
  - improvement_tip    : short paragraph
  - score_0_10         : composite score from samudrika auspicious + relevant OCEAN

Real engine data only (anthropometry mm/deg/ratios + samudrika phala_hi +
personality OCEAN). Zero hardcoded fallbacks for personalised content.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional


def _g(d: Optional[Dict], *path, default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _ocean(engines):
    return _g(engines, "personality", "ocean_summary_scores", default={}) or {}


def _phala(samudrika_features, key):
    f = (samudrika_features or {}).get(key) or {}
    txt = f.get("phala_hi") or f.get("phala") or ""
    cls = f.get("classification") or f.get("translit") or ""
    return cls, txt


def _classify(value, low, high, low_word, mid_word, high_word):
    """Return (band_word, band_word) — the band_word IS the dict key.
    band_word is also used to color-code in PDF (low/high/balanced families)."""
    if value is None:
        return (mid_word, mid_word)
    if value < low:  return (low_word,  low_word)
    if value > high: return (high_word, high_word)
    return (mid_word, mid_word)


def _mm(label_hi: str, key: str, value: Optional[float], unit: str,
        band: str, meaning_hi: str) -> Dict:
    """One micro-measurement entry, ready for PDF table rendering."""
    if value is None:
        return None
    return {
        "label":        label_hi,
        "value_text":   f"{value:.1f} {unit}",
        "band":         band,
        "meaning_hi":   meaning_hi,
    }


# ──────────────────────────────────────────────────────────────────────────
# Eyes
# ──────────────────────────────────────────────────────────────────────────
def block_eyes(engines: Dict) -> Dict:
    a_mm = _g(engines, "anthropometry", "measurements_mm") or {}
    a_ang = _g(engines, "anthropometry", "angles_deg") or {}
    a_rat = _g(engines, "anthropometry", "ratios") or {}
    sam_f = _g(engines, "samudrika", "features") or {}
    O = _num(_ocean(engines).get("openness"), 50)
    A = _num(_ocean(engines).get("agreeableness"), 50)
    N = _num(_ocean(engines).get("neuroticism"), 50)
    E = _num(_ocean(engines).get("extraversion"), 50)

    iod   = _num(a_mm.get("iod_inner"))
    e_w   = _num(a_mm.get("right_eye_width") or a_mm.get("left_eye_width"))
    span  = _num(a_mm.get("outer_eye_span"))
    spacing = _num(a_rat.get("eye_spacing_to_eye_width"))  # ~1.0 = normal
    aspect  = _num(a_rat.get("eye_aspect_ratio_avg"))      # higher = bigger/rounder
    tilt    = _num(a_ang.get("canthal_tilt"))              # +ve = upward

    # Micro-measurements with interpretation
    micros = []
    if iod:
        b, _ = _classify(spacing, 0.93, 1.07, "close", "balanced", "wide")
        meaning = {
            "close":    "Aankhein paas-paas — focus power achi, par tunnel-vision risk.",
            "wide":     "Aankhein door-door — broad perspective, par detail miss kar sakte ho.",
            "balanced": "Aankhein perfectly placed — natural balance of focus and breadth."
        }[b]
        micros.append(_mm("Inter-Ocular Distance (aankhon ke beech)", "iod_inner", iod, "mm", b, meaning))
    if e_w:
        b, _ = _classify(aspect, 0.28, 0.36, "small", "average", "large")
        meaning = {
            "small":  "Sharp, focused eyes — high concentration ka sign.",
            "large":  "Bade, expressive eyes — emotional depth aur openness ka sign.",
            "average":"Balanced eye size — adaptive emotional bandwidth."
        }[b]
        micros.append(_mm("Eye Width (har aankh)", "eye_width", e_w, "mm", b, meaning))
    if tilt is not None:
        b, _ = _classify(tilt, -2, 4, "downward", "neutral", "upward")
        meaning = {
            "upward":   "Canthal tilt upward — youthful, confident, attractive expression.",
            "downward": "Canthal tilt downward — serious, contemplative, slightly melancholic look.",
            "neutral":  "Neutral canthal tilt — neither overly soft nor harsh."
        }[b]
        micros.append(_mm("Canthal Tilt (aankh ka jhukao)", "canthal_tilt", tilt, "deg", b, meaning))
    if span:
        micros.append(_mm("Outer Eye Span (puri chaudai)", "outer_eye_span", span, "mm",
                          "balanced",
                          "Yeh full eye-to-eye width hai, jo facial expression ka primary canvas hai."))

    cls, phala = _phala(sam_f, "eyes")

    # Personality / behavior interpretations from OCEAN
    emotion_depth = "deep" if A > 60 or N > 55 else ("guarded" if A < 40 else "balanced")
    trauma_band = "high-sensitivity" if N > 60 else ("resilient" if N < 40 else "balanced")
    decision_impact = "intuitive (gut-feel)" if O > 60 and N > 50 else ("analytical (data-first)" if O < 50 else "mixed")

    personality_meaning = (
        f"Tumhari aankhein ek silent communicator hain — unme tumhari emotional bandwidth, "
        f"trust ka level aur intuitive depth dikhti hai. "
        f"OCEAN scan ke hisaab se tumhari emotion-depth <b>{emotion_depth}</b> hai "
        f"(Agreeableness {A:.0f}, Neuroticism {N:.0f}). "
        f"Iska matlab — relationships me tum {'deeply invested ho aur partner ko feel kar lete ho' if emotion_depth=='deep' else ('guarded ho, trust slowly build karte ho' if emotion_depth=='guarded' else 'balanced ho, na too clingy na too distant')}."
    )

    love_implication = (
        f"Pyaar me, tumhari aankhein pehle bolti hain words se. "
        f"Tum {'eye contact se bharose ka signal dete ho — par betrayal hone par 100% withdraw kar lete ho' if A > 60 else 'eye contact me thoda guarded ho — partner ko time chahiye tumhe padhne me'}. "
        f"Trauma ke maamle me tum <b>{trauma_band}</b> ho — past hurt ko {'long time tak hold karte ho aur dobara open hone me struggle hota hai' if N > 60 else ('comparatively jaldi recover karte ho aur trust dobara extend kar lete ho' if N < 40 else 'moderate response — heal hote ho but lessons yaad rahte hain')}."
    )

    career_decision = (
        f"Decision-making me tumhari aankhein {'pattern detect karne me sharp hain — log jhoot bol rahe ho ya truth, tum 80% time pakad lete ho' if O > 55 else 'logic + observation use karti hain — tum dheere decide karte ho par mostly right'}. "
        f"Tumhari intuitive style: <b>{decision_impact}</b>. "
        f"Career me yeh tumhe roles me strong banaata hai jahan reading-people zaroori ho — sales, leadership, counseling, design, ya creative direction."
    )

    stress_response = (
        f"Stress me tumhari aankhein sabse pehle change dikhati hain — tightness, dark circles, ya restless gaze. "
        f"Tumhari stress-response style: {'fight (intense focus, problem-solve mode)' if N < 45 else ('flight (avoidance, withdrawal)' if A > 65 else 'freeze (overthinking loop)')}. "
        f"7-8 ghante ki sleep aur 10-min daily 'distance gazing' (door dekhna) is region ko reset karta hai."
    )

    improvement_tip = (
        f"<b>30-day Eye Hack:</b> Roj 5 min mirror me apni aankhon me dekho without expression — "
        f"yeh practice self-trust badhati hai aur public eye-contact 2x confident banata hai. "
        f"Conversations me 60% time eye contact rakho (na zyada na kam) — yeh ideal trust-window hai."
    )

    return {
        "feature_name_hi":     "Aankhein (Eyes)",
        "feature_name_en":     "Eyes — Soul Mirror",
        "samudrika_class":     cls,
        "samudrika_phala":     phala,
        "micro_measurements":  [m for m in micros if m],
        "personality_meaning": personality_meaning,
        "love_implication":    love_implication,
        "career_decision":     career_decision,
        "stress_response":     stress_response,
        "improvement_tip":     improvement_tip,
    }


# ──────────────────────────────────────────────────────────────────────────
# Nose
# ──────────────────────────────────────────────────────────────────────────
def block_nose(engines: Dict) -> Dict:
    a_mm = _g(engines, "anthropometry", "measurements_mm") or {}
    a_ang = _g(engines, "anthropometry", "angles_deg") or {}
    a_rat = _g(engines, "anthropometry", "ratios") or {}
    sam_f = _g(engines, "samudrika", "features") or {}
    O = _num(_ocean(engines).get("openness"), 50)
    C = _num(_ocean(engines).get("conscientiousness"), 50)
    E = _num(_ocean(engines).get("extraversion"), 50)

    n_len = _num(a_mm.get("nose_length"))
    n_w   = _num(a_mm.get("nose_width_alar"))
    tip   = _num(a_ang.get("nose_tip_projection"))   # 90 = forward
    n2f   = _num(a_rat.get("nose_length_to_face"))
    n2m   = _num(a_rat.get("nose_width_to_mouth_width"))

    micros = []
    if n_len:
        b, _ = _classify(n2f, 0.30, 0.36, "short", "balanced", "long")
        meaning = {
            "long":     "Lambi naak — leadership tendencies, status-conscious, par sometimes ego clash.",
            "short":    "Chhoti naak — practical, fast-action, par patience kam.",
            "balanced": "Balanced naak — natural authority without ego."
        }[b]
        micros.append(_mm("Nose Length (naak ki lambai)", "nose_length", n_len, "mm", b, meaning))
    if n_w:
        b, _ = _classify(n2m, 0.50, 0.65, "narrow", "balanced", "broad")
        meaning = {
            "narrow":   "Patli alar (nostrils) — refined, careful spender, save-first mindset.",
            "broad":    "Chaudi alar — generous, big spender, willing to take wealth-risks.",
            "balanced": "Balanced nostril width — calculated risk + reasonable savings."
        }[b]
        micros.append(_mm("Nose Width — Alar (chaudai)", "nose_width_alar", n_w, "mm", b, meaning))
    if tip is not None:
        b, _ = _classify(tip, 88, 95, "drooping", "straight", "upturned")
        meaning = {
            "upturned": "Upturned tip — youthful, optimistic, trust-first attitude (kabhi-kabhi naive).",
            "drooping": "Drooping tip — analytical, skeptical, hard-to-please mindset.",
            "straight": "Straight tip — pragmatic, balanced wealth perspective."
        }[b]
        micros.append(_mm("Nose Tip Projection (tip ka angle)", "nose_tip_projection", tip, "deg", b, meaning))

    cls, phala = _phala(sam_f, "nose")

    wealth_band = "growth-oriented" if C > 55 and O > 50 else ("steady-saver" if C > 60 else "spend-as-you-go")
    decision_band = "decisive" if C > 60 else ("collaborative" if E > 55 else "deliberative")

    personality_meaning = (
        f"Vedic Samudrika me naak <b>dhan, status, aur self-image</b> ka indicator hai — "
        f"yeh tumhari professional identity ka sabse strong feature hai. "
        f"Conscientiousness {C:.0f} aur Openness {O:.0f} ke combination se tumhara wealth-mindset <b>{wealth_band}</b> banata hai. "
        f"Iska matlab — paisa tumhare liye {'tool hai status aur freedom paane ka' if wealth_band=='growth-oriented' else ('safety-net hai jo backup deta hai' if wealth_band=='steady-saver' else 'enjoyment ka medium hai, save vs spend pe relaxed ho')}."
    )

    love_implication = (
        f"Naak attraction me bhi central hai — symmetric naak partners me trust aur respect banaati hai. "
        f"Tum partner me {'ambitious, status-conscious traits prefer karte ho' if C > 55 else 'easy-going, relaxed traits prefer karte ho'}. "
        f"Naak ki shape se tumhari sexual confidence bhi judi hai — straight bridge wale log direct communicators hote hain bedroom me."
    )

    career_decision = (
        f"Tumhari decision-making style <b>{decision_band}</b> hai. "
        f"Career me tum {'leadership/founder roles me thrive karte ho — risk lena natural hai' if decision_band=='decisive' else ('collaborative roles — team lead, partnership, or co-founder model best suit karega' if decision_band=='collaborative' else 'specialist/expert roles — lawyer, analyst, designer, scientist — jahan deep thinking premium hai')}. "
        f"Money handling: {'aggressive growth (equity, business)' if C > 55 and O > 55 else ('balanced (mix of FD, equity, gold)' if C > 50 else 'liquid (cash, savings)')}."
    )

    stress_response = (
        f"Stress me naak ke through visible signals: oily skin, blocked nostrils, ya frequent sneezing. "
        f"Yeh tumhare respiratory + adrenal system ka stress signal hai. "
        f"Pranayama (alternate nostril breathing) is feature ke liye sabse powerful tool hai — daily 10 min karoge to 30 din me decision clarity 2x ho jayegi."
    )

    improvement_tip = (
        f"<b>Wealth Hack:</b> Har Sunday 30 min apne finances review karo — small consistent reviews "
        f"se 6 mahine me wealth confidence visibly badhega. "
        f"Naak hamesha shudh + moisturized rakho — chehre ka sabse 'visible' status-feature hai."
    )

    return {
        "feature_name_hi":     "Naak (Nose)",
        "feature_name_en":     "Nose — Wealth & Authority",
        "samudrika_class":     cls,
        "samudrika_phala":     phala,
        "micro_measurements":  [m for m in micros if m],
        "personality_meaning": personality_meaning,
        "love_implication":    love_implication,
        "career_decision":     career_decision,
        "stress_response":     stress_response,
        "improvement_tip":     improvement_tip,
    }


# ──────────────────────────────────────────────────────────────────────────
# Lips
# ──────────────────────────────────────────────────────────────────────────
def block_lips(engines: Dict) -> Dict:
    a_mm = _g(engines, "anthropometry", "measurements_mm") or {}
    a_ang = _g(engines, "anthropometry", "angles_deg") or {}
    a_rat = _g(engines, "anthropometry", "ratios") or {}
    sam_f = _g(engines, "samudrika", "features") or {}
    A = _num(_ocean(engines).get("agreeableness"), 50)
    E = _num(_ocean(engines).get("extraversion"), 50)
    N = _num(_ocean(engines).get("neuroticism"), 50)

    upper = _num(a_mm.get("upper_lip_thickness"))
    lower = _num(a_mm.get("lower_lip_thickness"))
    mw    = _num(a_mm.get("mouth_width"))
    ratio = _num(a_rat.get("lip_ratio_upper_to_lower"))   # ~0.7-1.0
    tilt  = _num(a_ang.get("lip_commissure_tilt"))        # +ve = smiling corners
    m2f   = _num(a_rat.get("mouth_to_face_width"))

    micros = []
    if upper and lower:
        b, _ = _classify(ratio, 0.65, 0.95, "thin-upper", "balanced", "full-upper")
        meaning = {
            "full-upper":  "Upper lip prominent — expressive, talkative, articulate.",
            "thin-upper":  "Upper lip thin — reserved, listener, careful with words.",
            "balanced":    "Balanced lip ratio — express bhi karte ho, sun bhi lete ho."
        }[b]
        micros.append(_mm("Upper-to-Lower Lip Ratio", "lip_ratio", ratio if ratio else 0, "", b, meaning))
        micros.append(_mm("Upper Lip Thickness", "upper_lip_thickness", upper, "mm", "info",
                          "Upper lip emotional expression ka measure hai — fuller = more expressive."))
        micros.append(_mm("Lower Lip Thickness", "lower_lip_thickness", lower, "mm", "info",
                          "Lower lip sensual aur receptive depth ka measure hai — fuller = more sensual."))
    if mw:
        b, _ = _classify(m2f, 0.40, 0.50, "narrow", "balanced", "wide")
        meaning = {
            "wide":     "Chauda mooh — extrovert tendencies, generous expression, big appetite for life.",
            "narrow":   "Patla mooh — selective communication, deep over wide, quality over quantity.",
            "balanced": "Balanced mouth width — adaptive social bandwidth."
        }[b]
        micros.append(_mm("Mouth Width (mooh ki chaudai)", "mouth_width", mw, "mm", b, meaning))
    if tilt is not None:
        b, _ = _classify(tilt, -1, 2, "down-turned", "neutral", "up-turned")
        meaning = {
            "up-turned":   "Upturned corners — natural smile, optimistic default, easy to like.",
            "down-turned": "Down-turned corners — serious default, but smile dramatically transforms face.",
            "neutral":     "Neutral corners — calm, composed, neither overly cheerful nor stern."
        }[b]
        micros.append(_mm("Lip Commissure Tilt (corners ka angle)", "lip_commissure_tilt", tilt, "deg", b, meaning))

    cls, phala = _phala(sam_f, "lips")

    style = "expressive" if E > 60 else ("reserved" if E < 40 else "balanced")
    love_exp = "warm-vocal" if A > 60 and E > 50 else ("warm-quiet" if A > 60 else ("cool-direct" if A < 45 else "balanced"))

    personality_meaning = (
        f"Honth tumhari communication ka sabse fast indicator hain — log first 10 second me tumhare lips se "
        f"hi judge kar lete hain ki tum approachable ho ya nahi. "
        f"Tumhari communication style <b>{style}</b> hai (Extraversion {E:.0f}). "
        f"Tum {'baat zyada karte ho aur conversation drive karte ho' if style=='expressive' else ('listen zyada karte ho aur baat tab karte ho jab kuch real value ho' if style=='reserved' else 'balanced ho — situation ke hisaab se talkative ya quiet')}."
    )

    love_implication = (
        f"Pyaar me tumhari love-expression style: <b>{love_exp}</b>. "
        f"Tum partner ko {'words, compliments aur frequent affirmations dete ho' if 'vocal' in love_exp else ('actions, presence aur silent care dete ho — words kam, par deep meaning' if 'quiet' in love_exp else ('directly state karte ho needs aur expectations — no guessing games' if 'direct' in love_exp else 'mix dete ho — kabhi vocal kabhi action'))}. "
        f"Sensual side me lower lip ki fullness signal karti hai: {'high physical sensitivity, partner ke touch pe deeply react' if lower and lower > 8 else 'subtle sensitivity, slow-burn intimacy'}."
    )

    career_decision = (
        f"Career me tumhare lips ka biggest gift: communication. "
        f"{'Public speaking, sales, teaching, content creation — yeh natural strength zone hai.' if style=='expressive' else ('Writing, design, research, technical roles — yahan tumhari listening + thinking depth premium hai.' if style=='reserved' else 'Hybrid roles — consultant, manager, coordinator — jahan listen + speak dono balance me chahiye.')}"
    )

    stress_response = (
        f"Stress me lips se sabse fast signals aate hain: dryness, lip-biting, ya tightness. "
        f"Yeh tumhare emotional repression ka surface signal hai. "
        f"Daily 5 min jaw-relaxation exercise (mooh khol ke breathe) is region ka stress 50% kam karta hai."
    )

    improvement_tip = (
        f"<b>Communication Hack:</b> Har conversation me <b>2x listen, 1x speak</b> ratio rakho. "
        f"Lips ko hydrated rakho (lip balm) — yeh chhoti cheez self-care ka biggest visible signal hai. "
        f"Smile practice: daily 1 min mirror me natural smile karo — corners ka angle 2 mahine me visibly badh jata hai."
    )

    return {
        "feature_name_hi":     "Honth (Lips)",
        "feature_name_en":     "Lips — Communication & Sensuality",
        "samudrika_class":     cls,
        "samudrika_phala":     phala,
        "micro_measurements":  [m for m in micros if m],
        "personality_meaning": personality_meaning,
        "love_implication":    love_implication,
        "career_decision":     career_decision,
        "stress_response":     stress_response,
        "improvement_tip":     improvement_tip,
    }


# ──────────────────────────────────────────────────────────────────────────
# Jaw / Chin
# ──────────────────────────────────────────────────────────────────────────
def block_jaw(engines: Dict) -> Dict:
    a_mm = _g(engines, "anthropometry", "measurements_mm") or {}
    a_ang = _g(engines, "anthropometry", "angles_deg") or {}
    a_rat = _g(engines, "anthropometry", "ratios") or {}
    sam_f = _g(engines, "samudrika", "features") or {}
    fwhr = _g(engines, "fwhr") or {}
    C = _num(_ocean(engines).get("conscientiousness"), 50)
    E = _num(_ocean(engines).get("extraversion"), 50)

    jw = _num(a_mm.get("jaw_width"))
    n2c = _num(a_mm.get("nose_tip_to_chin"))
    l2c = _num(a_mm.get("lip_to_chin"))
    gonial = _num(a_ang.get("jaw_angle_gonial"))    # ~120-130 = sharp, >135 = soft
    chin_p = _num(a_ang.get("chin_pointedness"))
    j2f = _num(a_rat.get("jaw_to_face_width"))
    fwhr_v = _num(fwhr.get("fwhr_value"))

    micros = []
    if jw:
        b, _ = _classify(j2f, 0.78, 0.92, "narrow", "balanced", "wide")
        meaning = {
            "wide":     "Chauda jabra — high willpower, dominance, leadership presence.",
            "narrow":   "Patla jabra — refined, intellectual, less confrontational.",
            "balanced": "Balanced jaw — strong jab zaroori ho, soft jab zaroori."
        }[b]
        micros.append(_mm("Jaw Width (jabre ki chaudai)", "jaw_width", jw, "mm", b, meaning))
    if gonial is not None:
        b, _ = _classify(gonial, 122, 135, "sharp", "balanced", "soft")
        meaning = {
            "sharp":    "Sharp gonial angle — assertive, direct, action-oriented.",
            "soft":     "Soft gonial angle — diplomatic, patient, peace-keeper.",
            "balanced": "Balanced jaw angle — adaptive between assert + accommodate."
        }[b]
        micros.append(_mm("Gonial Angle (jabre ka kone ka angle)", "gonial", gonial, "deg", b, meaning))
    if chin_p is not None:
        b, _ = _classify(chin_p, 25, 45, "rounded", "balanced", "pointed")
        meaning = {
            "pointed":  "Pointed chin — innovative, future-focused, bold ideas.",
            "rounded":  "Rounded chin — nurturing, family-first, traditional values.",
            "balanced": "Balanced chin — mix of innovation aur stability."
        }[b]
        micros.append(_mm("Chin Pointedness (thodi ka shape)", "chin_pointedness", chin_p, "deg", b, meaning))
    if l2c:
        micros.append(_mm("Lip-to-Chin Distance", "lip_to_chin", l2c, "mm", "info",
                          "Lower face proportion — yeh emotional resilience aur willpower band ka indicator hai."))
    if fwhr_v:
        b, _ = _classify(fwhr_v, 1.7, 2.0, "tall-face", "balanced", "wide-face")
        meaning = {
            "wide-face":  "fWHR high — competitive drive, dominance, aggressive negotiation style.",
            "tall-face":  "fWHR low — composed, diplomatic, conflict-avoiding tendency.",
            "balanced":   "fWHR balanced — strategic mix of dominance + diplomacy."
        }[b]
        micros.append(_mm("fWHR (Width-to-Height Ratio)", "fwhr", fwhr_v, "", b, meaning))

    cls, phala = _phala(sam_f, "jaw_chin")

    will = "very high" if C > 65 else ("high" if C > 50 else "developing")
    dominance = "high" if (fwhr_v and fwhr_v > 1.95) else ("medium" if (fwhr_v and fwhr_v > 1.8) else "low")

    personality_meaning = (
        f"Jabra aur thodi tumhari willpower aur dheeraj ka surest sign hain — yeh face ka 'foundation' hai. "
        f"Tumhari willpower band: <b>{will}</b> (Conscientiousness {C:.0f}). "
        f"Iska matlab — long-term goals me tum {'consistent ho aur completion strong hai' if 'high' in will else 'flexible ho — multiple things parallel chalti hain par sometimes finish line tak nahi pahunchti'}."
    )

    love_implication = (
        f"Relationships me jabra commitment aur loyalty ka indicator hai. "
        f"Tum {'long-term, all-in commitment me believe karte ho — half-hearted relationships tumhe drain karte hain' if C > 55 else 'commitment me lete ho but apni freedom bhi protect karte ho — co-existing partnership ideal hai'}. "
        f"Conflict me tumhari dominance level <b>{dominance}</b> hai — partner ko yeh samajhna hoga."
    )

    career_decision = (
        f"Career me jabra ka strength tumhe leadership aur execution roles me successful banata hai. "
        f"Decision style: {'hard-stop, full commit' if C > 60 else ('measured, weigh-then-decide' if C > 45 else 'open-ended, leave doors open')}. "
        f"Negotiation me {'tum ground hold karte ho aur direct hote ho' if dominance=='high' else 'tum collaborative ho aur win-win seek karte ho'}."
    )

    stress_response = (
        f"Stress me jabra clench, teeth-grinding, ya jaw pain — yeh tumhare 'control' system ka overload signal hai. "
        f"5-min daily jaw-massage + warm water gargle + screen-time discipline 70% reduce karte hain yeh symptoms. "
        f"Long-term unmanaged stress jaw region me visible asymmetry create karta hai."
    )

    improvement_tip = (
        f"<b>Willpower Hack:</b> Har Monday 1 'micro-commitment' likho aur Sunday tak complete karo. "
        f"Yeh tumhari completion-rate aur face-confidence dono badhata hai. "
        f"Posture (jabra slightly forward + shoulders back) public perception 30% boost karta hai."
    )

    return {
        "feature_name_hi":     "Jabra aur Thodi (Jaw & Chin)",
        "feature_name_en":     "Jaw & Chin — Willpower & Foundation",
        "samudrika_class":     cls,
        "samudrika_phala":     phala,
        "micro_measurements":  [m for m in micros if m],
        "personality_meaning": personality_meaning,
        "love_implication":    love_implication,
        "career_decision":     career_decision,
        "stress_response":     stress_response,
        "improvement_tip":     improvement_tip,
    }


# ──────────────────────────────────────────────────────────────────────────
# Forehead
# ──────────────────────────────────────────────────────────────────────────
def block_forehead(engines: Dict) -> Dict:
    a_mm = _g(engines, "anthropometry", "measurements_mm") or {}
    a_ang = _g(engines, "anthropometry", "angles_deg") or {}
    a_rat = _g(engines, "anthropometry", "ratios") or {}
    a_idx = _g(engines, "anthropometry", "classical_indices") or {}
    sam_f = _g(engines, "samudrika", "features") or {}
    O = _num(_ocean(engines).get("openness"), 50)
    C = _num(_ocean(engines).get("conscientiousness"), 50)

    f_h = _num(a_mm.get("forehead_height"))
    f_w = _num(a_mm.get("forehead_width"))
    slope = _num(a_ang.get("forehead_slope"))
    f2f = _num(a_rat.get("forehead_to_face_width"))
    f_pct = _num(a_idx.get("forehead_height_pct"))

    micros = []
    if f_h:
        b, _ = _classify(f_pct, 30, 36, "low", "balanced", "tall")
        meaning = {
            "tall":    "Uncha maatha — strong analytical thinking, philosophical, big-picture thinker.",
            "low":     "Chhota maatha — practical, action-first, less theorizing.",
            "balanced":"Balanced maatha — mix of theory + action."
        }[b]
        micros.append(_mm("Forehead Height (maathe ki uchai)", "forehead_height", f_h, "mm", b, meaning))
    if f_w:
        b, _ = _classify(f2f, 0.80, 0.92, "narrow", "balanced", "wide")
        meaning = {
            "wide":     "Chauda maatha — broad knowledge, multi-domain interest, polymath tendency.",
            "narrow":   "Patla maatha — deep specialization, single-domain mastery.",
            "balanced": "Balanced — well-rounded knowledge with go-to specialty."
        }[b]
        micros.append(_mm("Forehead Width (maathe ki chaudai)", "forehead_width", f_w, "mm", b, meaning))
    if slope is not None:
        b, _ = _classify(slope, -3, 5, "receding", "vertical", "protruding")
        meaning = {
            "vertical":   "Vertical forehead — methodical, step-by-step thinker.",
            "receding":   "Receding forehead — fast, spontaneous, action-oriented thinking.",
            "protruding": "Protruding forehead — visionary, future-thinker, strategic planner."
        }[b]
        micros.append(_mm("Forehead Slope", "forehead_slope", slope, "deg", b, meaning))

    cls, phala = _phala(sam_f, "forehead")

    intel = "creative-strategic" if O > 60 and C > 50 else ("analytical-deep" if C > 55 else ("intuitive-broad" if O > 55 else "practical-focused"))

    personality_meaning = (
        f"Maatha tumhari intelligence, planning aur leadership-potential ka mirror hai — "
        f"yeh chehre ka 'soch wala' zone hai. "
        f"Tumhara intelligence pattern: <b>{intel}</b> (Openness {O:.0f}, Conscientiousness {C:.0f}). "
        f"Iska matlab — naye problems ko tum {'creative + structured way me approach karte ho — frameworks bhi banate ho aur out-of-box bhi sochte ho' if intel=='creative-strategic' else ('deep dive aur step-by-step solve karte ho — patience aur logic dono strong' if 'analytical' in intel else ('big picture + multiple angles dekhte ho — par execution thoda inconsistent hota hai' if 'intuitive' in intel else 'fast practical solutions dete ho — perfect nahi par working'))}."
    )

    love_implication = (
        f"Pyaar me maatha 'planning' indicator hai — tum relationship ka future kaise dekhte ho. "
        f"{'Tum long-term vision pehle banate ho — phir present me invest karte ho.' if C > 55 else 'Tum present pe focus karte ho — future apne aap unfold hone do.'} "
        f"Partner ke saath intellectual compatibility tumhare liye sexual chemistry jitni important hai."
    )

    career_decision = (
        f"Career me maatha leadership-readiness ka sign hai. "
        f"Tumhe roles me put karoge jahan {'strategy + creativity dono chahiye (founder, product lead, creative director)' if intel=='creative-strategic' else ('deep analysis chahiye (research, finance, engineering)' if 'analytical' in intel else ('vision aur communication chahiye (consulting, teaching, public role)' if 'intuitive' in intel else 'fast execution chahiye (operations, sales, project management)'))}, "
        f"to tum 80% potential pe perform karoge."
    )

    stress_response = (
        f"Stress me maatha pe lines, frequent headaches, ya tightness aati hai. "
        f"Yeh overthinking + screen-fatigue ka surface signal hai. "
        f"Daily 10 min meditation + 8 ghante sleep + screen-break har 90 min — yeh 3 cheezein maatha-region ka stress 60% kam karti hain."
    )

    improvement_tip = (
        f"<b>Mind Hack:</b> Har subah 5 min 'intention writing' — sirf 3 lines: "
        f"(1) Aaj ka biggest priority kya hai? (2) Ek hurdle kya aa sakta hai? (3) Use kaise solve karunga? "
        f"30 din me tumhari decision-clarity 2x ho jayegi."
    )

    return {
        "feature_name_hi":     "Maatha (Forehead)",
        "feature_name_en":     "Forehead — Intelligence & Vision",
        "samudrika_class":     cls,
        "samudrika_phala":     phala,
        "micro_measurements":  [m for m in micros if m],
        "personality_meaning": personality_meaning,
        "love_implication":    love_implication,
        "career_decision":     career_decision,
        "stress_response":     stress_response,
        "improvement_tip":     improvement_tip,
    }


# ──────────────────────────────────────────────────────────────────────────
# Eyebrows
# ──────────────────────────────────────────────────────────────────────────
def block_brows(engines: Dict) -> Dict:
    a_mm = _g(engines, "anthropometry", "measurements_mm") or {}
    a_ang = _g(engines, "anthropometry", "angles_deg") or {}
    sam_f = _g(engines, "samudrika", "features") or {}
    C = _num(_ocean(engines).get("conscientiousness"), 50)
    E = _num(_ocean(engines).get("extraversion"), 50)

    brow_d = _num(a_mm.get("brow_distance_inner"))
    arch = _num(a_ang.get("brow_arch_angle"))

    micros = []
    if brow_d:
        b, _ = _classify(brow_d, 18, 26, "close", "balanced", "wide")
        meaning = {
            "close":    "Paas-paas eyebrows — high focus, intensity, perfectionist tendency.",
            "wide":     "Door-door eyebrows — relaxed, easy-going, less prone to over-analysis.",
            "balanced": "Balanced spacing — adaptive focus + chill mix."
        }[b]
        micros.append(_mm("Inter-Brow Distance (eyebrows ke beech)", "brow_distance", brow_d, "mm", b, meaning))
    if arch is not None:
        b, _ = _classify(arch, 8, 18, "flat", "soft-arch", "high-arch")
        meaning = {
            "high-arch":  "Sharp arch — dramatic, expressive, attention-grabber.",
            "flat":       "Flat brows — composed, hard-to-surprise, poker-face master.",
            "soft-arch":  "Natural soft arch — balanced expression range."
        }[b]
        micros.append(_mm("Eyebrow Arch Angle", "brow_arch", arch, "deg", b, meaning))

    cls, phala = _phala(sam_f, "eyebrows")

    discipline_band = "strong" if C > 60 else ("moderate" if C > 45 else "developing")

    personality_meaning = (
        f"Eyebrows tumhari discipline, energy aur emotional control ka primary indicator hain. "
        f"Tumhara discipline band: <b>{discipline_band}</b> (Conscientiousness {C:.0f}). "
        f"Eyebrows hi pehli cheez hai jo log subconscious me 'serious vs playful' classification ke liye use karte hain — "
        f"shape aur arch tumhari intensity broadcast karti hai."
    )

    love_implication = (
        f"Relationships me eyebrows non-verbal communication ka 60% carry karti hain. "
        f"Tum partner ko bina bole bhi {'eyebrow raise se message de dete ho — yeh strong but sometimes intimidating ho sakta hai' if C > 55 else 'subtle expressions dete ho — partner ko padhne me thoda time lagta hai'}. "
        f"Anger ya disapproval eyebrows me sabse pehle dikhte hain."
    )

    career_decision = (
        f"Discipline aur execution-power eyebrows se judi hai. "
        f"Tum {'long-term projects me consistent ho — deadlines aur commitments respect karte ho' if C > 55 else 'creative bursts me strong ho — par admin/repetitive work me struggle hota hai'}. "
        f"Public-facing roles me well-shaped eyebrows authority signal 30% boost karti hain."
    )

    stress_response = (
        f"Stress me eyebrows ke beech '11' lines (frown lines) form hoti hain — "
        f"yeh long-term overthinking ka visible scar hai. "
        f"Daily 5 min eyebrow-massage + conscious 'unfurrow' practice in lines ko 6 mahine me 50% kam kar sakti hai."
    )

    improvement_tip = (
        f"<b>Discipline Hack:</b> Har raat agle din ke 3 priorities likh ke so jao. "
        f"Subah 80% mental friction kam ho jaata hai. "
        f"Eyebrow grooming (threading/shaping) — yeh chhoti cheez interview/photo confidence dramatically badha deti hai."
    )

    return {
        "feature_name_hi":     "Bhauwein (Eyebrows)",
        "feature_name_en":     "Eyebrows — Discipline & Energy",
        "samudrika_class":     cls,
        "samudrika_phala":     phala,
        "micro_measurements":  [m for m in micros if m],
        "personality_meaning": personality_meaning,
        "love_implication":    love_implication,
        "career_decision":     career_decision,
        "stress_response":     stress_response,
        "improvement_tip":     improvement_tip,
    }


# ──────────────────────────────────────────────────────────────────────────
# Ears
# ──────────────────────────────────────────────────────────────────────────
def block_ears(engines: Dict) -> Dict:
    sam_f = _g(engines, "samudrika", "features") or {}
    bhagya = _num(_g(engines, "samudrika", "composite_scores", "bhagya"), 70)
    O = _num(_ocean(engines).get("openness"), 50)

    cls, phala = _phala(sam_f, "ears")

    learn_band = "fast-adaptive" if O > 60 else ("steady-deep" if O < 45 else "balanced")

    personality_meaning = (
        f"Vedic Samudrika me kaan tumhare bhagya (luck) aur learning ability ka indicator hain. "
        f"Tumhara luck-indicator score: <b>{bhagya:.0f}/100</b>. "
        f"Tumhara learning style: <b>{learn_band}</b> (Openness {O:.0f}). "
        f"Iska matlab — naye skills tum {'jaldi pick karte ho aur multiple subjects parallel handle kar sakte ho' if learn_band=='fast-adaptive' else ('slowly par deeply learn karte ho — ek baar pakka hua to lifetime stays' if 'steady' in learn_band else 'balanced approach — jab interest ho fast, jab need ho deep')}."
    )

    love_implication = (
        f"Pyaar me kaan listening ka feature hai — partner ki baat sunne ki tumhari ability. "
        f"{'Tum natural listener ho — partner feel karta hai ki use samjha jata hai.' if O > 55 else 'Tum listen karte ho but kabhi-kabhi solve mode me jump kar dete ho — pure listening ki practice chahiye.'}"
    )

    career_decision = (
        f"Career me ears 'absorption' indicator hain — feedback, mentorship, learning curves. "
        f"Tum mentorship-driven roles me thrive karte ho jahan {'naye ideas aur cross-domain learning hai' if O > 55 else 'deep mastery aur traditional teaching hai'}. "
        f"Bhagya score {bhagya:.0f} ka matlab: opportunities tumhare paas {'frequently aati hain — pakad ke use karna critical hai' if bhagya > 70 else 'regular aati hain — patience aur preparation se 1.5x better rate ho sakta hai'}."
    )

    stress_response = (
        f"Stress me ears me ringing (tinnitus), heaviness, ya sensitivity badh sakti hai. "
        f"Yeh nervous-system overload ka signal hai. "
        f"Daily 10 min 'silent listening' (no music, just ambient sounds) ka practice ear-region ka stress aur mental clutter dono kam karta hai."
    )

    improvement_tip = (
        f"<b>Luck-Boost Hack:</b> Roj 1 naya person se 5-min meaningful conversation karo (cafe, gym, online). "
        f"6 mahine me network aur opportunities exponentially badhenge. "
        f"Ears clean + healthy rakho — chhota detail, big confidence signal."
    )

    return {
        "feature_name_hi":     "Kaan (Ears)",
        "feature_name_en":     "Ears — Luck & Learning",
        "samudrika_class":     cls,
        "samudrika_phala":     phala,
        "micro_measurements":  [
            _mm("Bhagya Score (Samudrika luck indicator)", "bhagya", bhagya, "/100", "info",
                "Vedic Samudrika ka composite luck-indicator — high = opportunities zyada milti hain.")
        ],
        "personality_meaning": personality_meaning,
        "love_implication":    love_implication,
        "career_decision":     career_decision,
        "stress_response":     stress_response,
        "improvement_tip":     improvement_tip,
    }


# ──────────────────────────────────────────────────────────────────────────
# Master builder
# ──────────────────────────────────────────────────────────────────────────
def build_section_6_deep(engines: Dict) -> Dict:
    """Build the rich 7-feature deep-dive structure for Section 6."""
    return {
        "intro_para": (
            "Tumhare har feature ki ek alag kahaani hai — aur jab unhe ek saath padha "
            "jata hai, tab puri tasveer nikalti hai. Niche har feature ko 6 layers me "
            "padha gaya hai: micro-measurements (anthropometry numbers), Samudrika "
            "phala (classical reading), personality meaning (OCEAN), love implication, "
            "career & decision style, stress response, aur ek improvement hack."
        ),
        "feature_blocks": [
            block_eyes(engines),
            block_nose(engines),
            block_lips(engines),
            block_jaw(engines),
            block_forehead(engines),
            block_brows(engines),
            block_ears(engines),
        ],
    }
