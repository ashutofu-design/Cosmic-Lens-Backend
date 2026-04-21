"""
Engine 7 — First Impression / Halo-Effect Snap-Judgments — v1
================================================================

What do strangers perceive in the FIRST 100 ms of seeing this face?
Willis & Todorov (Psychol Sci 2006) showed personality judgments form in 100ms
and are stable across longer exposure. This engine quantifies those snap
judgments + halo-effect contagion ("what is beautiful is good", Dion 1972).

Dimensions output (15 social-perception scores):
  1. attractiveness          — composite (symmetry + phi + skin clarity + youth)
  2. trustworthiness         — Oosterhof & Todorov 2008 valence axis
  3. dominance               — Oosterhof & Todorov 2008 dominance axis
  4. competence              — Todorov, Mandisodza, Goren, Hall 2005 (Science)
  5. likeability             — composite warmth + smile + low threat
  6. approachability         — A trait + smile + low dominance
  7. threat                  — Said, Sebe, Todorov 2009 (anger-resemblance)
  8. babyfaceness            — Berry & McArthur 1985
  9. maturity                — anti-babyface composite
 10. perceived_health        — Stephen et al. 2009 (skin colour, vitality)
 11. perceived_intelligence  — Zebrowitz et al. 2002
 12. leadership_potential    — Re, Hunter et al. 2013 + Rule & Ambady 2008
 13. memorability            — Bainbridge, Isola, Oliva 2013 (PAMI)
 14. typicality              — Said, Dotsch, Todorov 2010 (inverse memorability)
 15. perceived_age           — apparent age vs chronological age

Outputs additionally:
  • Snap-judgment narrative (Hinglish + EN) — what people "see in 100ms"
  • Halo-effect warning (positive/negative spillover risk)
  • Bias acknowledgement (race, gender, age perception bias)
  • First-glance valence (overall positive/negative impression)
  • Stereotype-vulnerability flags (e.g., babyface → underestimated competence)
  • Strengths + watch-outs lists
  • Per-dimension percentile + confidence

Inputs:
  • Landmarks (MediaPipe FaceMesh)
  • Engine 1 anthropometry result
  • Engine 2 symmetry result
  • Engine 3 phi result
  • Engine 4 fwhr result
  • Engine 5 health result
  • Engine 6 personality result (OCEAN + V-D)
  • gender, age, ethnicity

Scientific basis:
  • Willis & Todorov 2006 (Psychol Sci) — 100 ms judgments
  • Todorov, Olivola, Dotsch, Mende-Siedlecki 2015 (Annu Rev Psychol)
  • Oosterhof & Todorov 2008 (PNAS) — V-D 2D model
  • Todorov, Mandisodza et al. 2005 (Science) — competence → election outcomes
  • Said, Sebe, Todorov 2009 — emotional-resemblance basis of trait perception
  • Dion, Berscheid, Walster 1972 — halo effect ("beautiful is good")
  • Berry & McArthur 1985 — babyface stereotype
  • Zebrowitz, Hall et al. 2002 — perceived intelligence from face
  • Stephen, Coetzee, Perrett 2009 — skin → perceived health
  • Re, Hunter et al. 2013 (PLoS One) — leadership perception
  • Rule & Ambady 2008 — CEO faces predict company performance
  • Bainbridge, Isola, Oliva 2013 (IEEE PAMI) — face memorability
  • Said, Dotsch, Todorov 2010 — typicality vs distinctiveness
  • Olivola & Todorov 2010 — face inferences are POOR predictors of behavior
"""
from __future__ import annotations
from typing import Optional, Sequence
import math
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Sanitizer
# ─────────────────────────────────────────────────────────────────────────────
def _py(o):
    if isinstance(o, dict):  return {k: _py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):  return [_py(x) for x in o]
    if isinstance(o, np.bool_):    return bool(o)
    if isinstance(o, np.integer):  return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray):  return _py(o.tolist())
    return o


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _clip(x, lo=0, hi=100): return max(lo, min(hi, x))

def _to_score(value: float, lo: float, hi: float, invert: bool = False) -> float:
    if value is None: return 50.0
    if hi == lo: return 50.0
    p = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    if invert: p = 1.0 - p
    return round(p * 100, 1)

def _z_to_percentile(z: float) -> float:
    return round(50 * (1 + math.erf(z / math.sqrt(2))), 1)

def _score_to_percentile(score: float) -> float:
    z = (score - 50) / 15.0
    return _z_to_percentile(z)

def _bayesian_shrink(score: float, alpha: float = 0.30) -> float:
    """First-impression effects are real but modest; shrink toward 50."""
    return round(50 + (1 - alpha) * (score - 50), 1)

def _class_label(score: float) -> str:
    if score >= 80: return "very_high"
    if score >= 65: return "high"
    if score >= 50: return "moderate_high"
    if score >= 35: return "moderate_low"
    if score >= 20: return "low"
    return "very_low"


# ─────────────────────────────────────────────────────────────────────────────
# Cross-engine extractors (schema-correct from v6 audit)
# ─────────────────────────────────────────────────────────────────────────────
def _get_fwhr(fwhr_result):
    if not fwhr_result or not fwhr_result.get("ok"): return None
    return (fwhr_result.get("primary") or {}).get("value")

def _get_dom_z(fwhr_result):
    if not fwhr_result or not fwhr_result.get("ok"): return None
    return ((fwhr_result.get("composite_scores") or {})
            .get("dominance_signal") or {}).get("z")

def _get_phi(phi_result):
    if not phi_result or not phi_result.get("ok"): return None
    return phi_result.get("overall_phi_score")

def _get_sym(symmetry_result):
    if not symmetry_result or not symmetry_result.get("ok"): return None
    return symmetry_result.get("overall_score")

def _get_vitality(health_result):
    if not health_result or not health_result.get("ok"): return None
    return health_result.get("vitality_score")

def _get_skin_clarity(health_result):
    if not health_result or not health_result.get("ok"): return None
    inflam = (health_result.get("composite_scores") or {}).get("inflammation_index")
    return None if inflam is None else round(100 - inflam, 1)

def _get_dark_circles(health_result):
    if not health_result or not health_result.get("ok"): return None
    dc = (health_result.get("indicators") or {}).get("dark_circles") or {}
    L_drop = max(abs(dc.get("L_drop_left") or 0), abs(dc.get("L_drop_right") or 0))
    return round(min(100, L_drop * 8), 1)

def _get_aging_score(health_result):
    """Aggregate aging from health.indicators.aging_signs."""
    if not health_result or not health_result.get("ok"): return None
    aging = (health_result.get("indicators") or {}).get("aging_signs") or {}
    if not aging: return None
    score_map = {"low": 15, "minimal": 10, "moderate": 50, "med": 50,
                  "marked": 80, "high": 85, "severe": 95}
    vals = []
    for k, v in aging.items():
        if isinstance(v, str): vals.append(score_map.get(v.lower(), 30))
        elif isinstance(v, (int, float)):
            vals.append(min(100, v*100) if v <= 1.0 else min(100, v))
    return round(sum(vals)/len(vals), 1) if vals else None

def _get_personality(p_result):
    if not p_result or not p_result.get("ok"): return None
    return p_result.get("ocean_summary_scores") or {}

def _get_vd(p_result):
    if not p_result or not p_result.get("ok"): return None
    return p_result.get("valence_dominance_2D") or {}

def _get_babyface(p_result):
    if not p_result or not p_result.get("ok"): return None
    return (p_result.get("geometric_indicators") or {}).get("babyface_index")


# ─────────────────────────────────────────────────────────────────────────────
# Core dimension calculators
# ─────────────────────────────────────────────────────────────────────────────
def _attractiveness(sym, phi, skin_clarity, vitality, aging, age, gender):
    """Attractiveness composite — symmetry + phi + skin + youth (Rhodes 2006)."""
    parts = []
    if sym is not None:           parts.append(("symmetry", sym, 0.30))
    if phi is not None:           parts.append(("phi_alignment", phi, 0.25))
    if skin_clarity is not None:  parts.append(("skin_clarity", skin_clarity, 0.20))
    if vitality is not None:      parts.append(("vitality", vitality, 0.15))
    if aging is not None and age is not None:
        # Youth premium up to ~30; after 50 minimal effect (age-bias acknowledged)
        expected_aging = max(0, (age - 20) * 1.5)
        youth_score = _clip(100 - max(0, aging - expected_aging))
        parts.append(("youth_premium", youth_score, 0.10))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    score = sum(s*w for _,s,w in parts) / wsum
    return round(_clip(score), 1), parts


def _trustworthiness(p_vd, sym, A_score, smile_proxy):
    """Trustworthiness — Oosterhof V-D valence + agreeableness signals."""
    parts = []
    if p_vd and p_vd.get("valence_trustworthiness") is not None:
        parts.append(("vd_valence", p_vd["valence_trustworthiness"], 0.50))
    if A_score is not None:    parts.append(("agreeableness", A_score, 0.20))
    if sym is not None:        parts.append(("symmetry", sym, 0.15))
    if smile_proxy is not None:parts.append(("smile_signal", smile_proxy, 0.15))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _dominance(p_vd, fwhr, dom_z, jaw_angle, brow_height):
    """Dominance — V-D dominance axis + jaw firmness + low brow."""
    parts = []
    if p_vd and p_vd.get("dominance_power") is not None:
        parts.append(("vd_dominance", p_vd["dominance_power"], 0.40))
    if fwhr is not None:
        parts.append(("fwhr", _to_score(fwhr, 1.7, 2.1), 0.20))
    if dom_z is not None:
        parts.append(("dom_z", _to_score(dom_z, -1.5, 1.5), 0.15))
    if jaw_angle is not None:
        parts.append(("jaw_firm", _to_score(jaw_angle, 105, 145, invert=True), 0.15))
    if brow_height is not None:
        parts.append(("low_brow", _to_score(brow_height, 0.10, 0.28, invert=True), 0.10))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _competence(C_score, attract, dom, sym, jaw_angle):
    """Competence (Todorov 2005 Science) — ~ attractive + mature + symmetric."""
    parts = []
    if C_score is not None:    parts.append(("conscientiousness", C_score, 0.25))
    if attract is not None:    parts.append(("attractiveness_halo", attract, 0.25))
    if dom is not None:        parts.append(("moderate_dominance", _bell(dom, 60, 25), 0.20))
    if sym is not None:        parts.append(("symmetry", sym, 0.15))
    if jaw_angle is not None:
        parts.append(("mature_jaw", _to_score(jaw_angle, 105, 145, invert=True), 0.15))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _bell(value, peak, width):
    """Bell-curve score: peaks at `peak`, falls off either side."""
    if value is None: return 50.0
    return round(_clip(100 - abs(value - peak) * (100 / width)), 1)


def _likeability(A_score, E_score, smile_proxy, threat):
    parts = []
    if A_score is not None:    parts.append(("agreeableness", A_score, 0.30))
    if E_score is not None:    parts.append(("extraversion", E_score, 0.20))
    if smile_proxy is not None:parts.append(("smile_signal", smile_proxy, 0.30))
    if threat is not None:     parts.append(("low_threat", 100 - threat, 0.20))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _approachability(A_score, smile_proxy, dom, vitality):
    parts = []
    if A_score is not None:    parts.append(("agreeableness", A_score, 0.35))
    if smile_proxy is not None:parts.append(("smile_signal", smile_proxy, 0.25))
    if dom is not None:        parts.append(("low_dominance", 100 - dom, 0.20))
    if vitality is not None:   parts.append(("vitality", vitality, 0.20))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _threat(brow_height, mouth_drop, fwhr, dark_circles, smile_proxy):
    """Threat = anger-resemblance (Said et al. 2009) — low brow, tight mouth, high fWHR."""
    parts = []
    if brow_height is not None:
        parts.append(("low_brow_anger", _to_score(brow_height, 0.10, 0.28, invert=True), 0.30))
    if mouth_drop is not None:
        parts.append(("mouth_drop", _to_score(mouth_drop, 0, 0.04), 0.20))
    if fwhr is not None:
        parts.append(("high_fwhr", _to_score(fwhr, 1.7, 2.1), 0.20))
    if smile_proxy is not None:
        parts.append(("absence_of_smile", 100 - smile_proxy, 0.20))
    if dark_circles is not None:
        parts.append(("fatigue_signal", dark_circles, 0.10))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _perceived_health(skin_clarity, vitality, dark_circles, sym):
    """Stephen et al. 2009 — skin colour and clarity drive health perception."""
    parts = []
    if skin_clarity is not None:  parts.append(("skin_clarity", skin_clarity, 0.35))
    if vitality is not None:      parts.append(("vitality", vitality, 0.30))
    if dark_circles is not None:  parts.append(("low_fatigue", 100 - dark_circles, 0.20))
    if sym is not None:           parts.append(("symmetry", sym, 0.15))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _perceived_intelligence(C_score, O_score, attract, forehead_h):
    """Zebrowitz 2002 — perceived intelligence ≈ mature + symmetric + high forehead."""
    parts = []
    if C_score is not None:     parts.append(("conscientiousness", C_score, 0.25))
    if O_score is not None:     parts.append(("openness", O_score, 0.20))
    if attract is not None:     parts.append(("attract_halo", attract, 0.25))
    if forehead_h is not None:
        parts.append(("forehead_height", _to_score(forehead_h, 0.18, 0.32), 0.30))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _leadership(competence, dom, attract, age, gender):
    """Re et al. 2013, Rule & Ambady 2008 — leadership ≈ competence + moderate dom + maturity."""
    parts = []
    if competence is not None:  parts.append(("competence", competence, 0.40))
    if dom is not None:         parts.append(("moderate_dominance", _bell(dom, 65, 30), 0.30))
    if attract is not None:     parts.append(("attract_halo", attract, 0.20))
    if age is not None:
        # Leadership perception peaks 35-55
        age_score = _bell(age, 45, 25)
        parts.append(("age_appropriate", age_score, 0.10))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _memorability(sym, attract, distinctiveness):
    """Bainbridge 2013 — memorability ≈ moderate distinctiveness × moderate attractiveness."""
    parts = []
    if distinctiveness is not None:
        # Memorable faces are MORE distinctive; bell-curve avoids extreme outliers
        parts.append(("distinctiveness", distinctiveness, 0.45))
    if attract is not None:
        parts.append(("attract_moderate", _bell(attract, 65, 30), 0.30))
    if sym is not None:
        parts.append(("symmetry_moderate", _bell(sym, 60, 25), 0.25))
    if not parts: return None, []
    wsum = sum(w for _,_,w in parts) or 1.0
    return round(_clip(sum(s*w for _,s,w in parts)/wsum), 1), parts


def _perceived_age(aging_score, vitality, dark_circles, chrono_age):
    """Apparent age vs chronological age."""
    if chrono_age is None: return None, None
    age_shift = 0.0
    n = 0
    if aging_score is not None:
        # Aging score above expected → older
        expected = max(0, (chrono_age - 20) * 1.5)
        age_shift += (aging_score - expected) * 0.15
        n += 1
    if vitality is not None:
        # Low vitality → older
        age_shift += (50 - vitality) * 0.08
        n += 1
    if dark_circles is not None:
        age_shift += dark_circles * 0.05
        n += 1
    if n == 0: return None, None
    apparent = round(chrono_age + age_shift, 1)
    diff = round(apparent - chrono_age, 1)
    return apparent, diff


# ─────────────────────────────────────────────────────────────────────────────
# Smile proxy + distinctiveness from personality result
# ─────────────────────────────────────────────────────────────────────────────
def _smile_proxy(p_result):
    if not p_result or not p_result.get("ok"): return None
    g = p_result.get("geometric_indicators") or {}
    upturn = g.get("mouth_corner_upturn", 0)
    width = g.get("mouth_width_iod", 0.80)
    return round(_clip((_to_score(upturn, -0.03, 0.06) * 0.6 +
                         _to_score(width, 0.65, 0.95) * 0.4)), 1)


def _distinctiveness(phi_score, novel_proportions):
    """Distance from average — inverse of phi alignment."""
    if phi_score is not None:
        return round(100 - phi_score, 1)
    return novel_proportions


# ─────────────────────────────────────────────────────────────────────────────
# Halo-effect detector
# ─────────────────────────────────────────────────────────────────────────────
def _halo_effect(attract, scores):
    """Detect halo (positive attract → boosts other ratings) and reverse-halo."""
    if attract is None or attract == 50:
        return {"present": False, "direction": "neutral", "magnitude": 0,
                 "note": "Insufficient signal."}
    direction = "positive" if attract >= 60 else "negative" if attract <= 40 else "mild"
    magnitude = abs(attract - 50)
    affected = []
    for dim, sc in scores.items():
        if sc is None: continue
        # If non-attract scores trend with attract, halo is operating
        if (attract >= 60 and sc >= 60) or (attract <= 40 and sc <= 40):
            affected.append(dim)
    return {
        "present": magnitude >= 10,
        "direction": direction,
        "magnitude": round(magnitude, 1),
        "affected_dimensions": affected,
        "note": ("High attractiveness creates positive bias on other trait perceptions "
                 "(Dion 1972 'beautiful is good')." if direction == "positive"
                 else "Lower attractiveness may unfairly drag other perceptions down."
                 if direction == "negative" else "Mild halo influence."),
        "ref": "Dion_Berscheid_Walster_1972_halo",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Stereotype-vulnerability flags
# ─────────────────────────────────────────────────────────────────────────────
def _stereotype_flags(scores: dict, babyface) -> list:
    flags = []
    if babyface is not None and babyface >= 65:
        flags.append({
            "flag": "babyface_underestimation",
            "note": "Babyface appearance — may be perceived as less competent / more naive (Berry & McArthur 1985). "
                    "Counter by demonstrated expertise and assertive communication.",
            "ref": "Berry_McArthur_1985",
        })
    if scores.get("dominance") and scores["dominance"] >= 70:
        flags.append({
            "flag": "high_dominance_threat_perception",
            "note": "High perceived dominance — may be read as intimidating in collaborative contexts. "
                    "Counter with warm signals (smiling, open posture).",
            "ref": "Oosterhof_Todorov_2008",
        })
    if scores.get("trustworthiness") and scores["trustworthiness"] <= 35:
        flags.append({
            "flag": "low_trust_perception",
            "note": "First-glance trust signal is below average — strangers may need more reassurance. "
                    "Counter with consistent eye contact, measured speech, smile.",
            "ref": "Todorov_2008",
        })
    if scores.get("threat") and scores["threat"] >= 65:
        flags.append({
            "flag": "high_threat_perception",
            "note": "Resemblance to anger expression elevates threat reading (Said et al. 2009). "
                    "Often misread; conscious smile/relaxed brow neutralises it.",
            "ref": "Said_Sebe_Todorov_2009",
        })
    if scores.get("attractiveness") and scores["attractiveness"] >= 75:
        flags.append({
            "flag": "high_attract_competence_overestimation",
            "note": "Strong attractiveness halo — may be assumed more competent than reality (or vice versa). "
                    "Be aware others' first impressions are inflated.",
            "ref": "Dion_Berscheid_Walster_1972",
        })
    return flags


# ─────────────────────────────────────────────────────────────────────────────
# First-glance valence (single positive/negative summary)
# ─────────────────────────────────────────────────────────────────────────────
def _first_glance_valence(scores: dict) -> dict:
    pos_dims = ["attractiveness", "trustworthiness", "likeability", "approachability",
                 "perceived_health", "perceived_intelligence", "competence"]
    neg_dims = ["threat"]
    pos = [scores[d] for d in pos_dims if scores.get(d) is not None]
    neg = [scores[d] for d in neg_dims if scores.get(d) is not None]
    if not pos: return {"valence": None, "label": "unknown"}
    pos_avg = sum(pos) / len(pos)
    neg_avg = sum(neg) / len(neg) if neg else 30
    valence = round(_clip(pos_avg - 0.4 * (neg_avg - 30)), 1)
    label = ("strongly_positive" if valence >= 70 else
              "positive" if valence >= 58 else
              "neutral" if valence >= 45 else
              "mildly_negative" if valence >= 35 else
              "negative")
    return {"valence_0_100": valence, "label": label,
             "based_on_positive_dims": pos_dims, "based_on_threat": neg_dims}


# ─────────────────────────────────────────────────────────────────────────────
# Hinglish + EN snap-judgment narratives
# ─────────────────────────────────────────────────────────────────────────────
NARRATIVES = {
    "strongly_positive": {
        "en": "Strangers form an immediately warm, capable impression — high trust + likeability halo.",
        "hi": "Pehli nazar me hi log warm aur capable maante hain — strong positive halo.",
    },
    "positive": {
        "en": "Generally positive first impression — approachable and competent.",
        "hi": "Pehli nazar me positive — approachable aur capable lagte hain.",
    },
    "neutral": {
        "en": "Balanced first impression — neither strongly inviting nor distancing.",
        "hi": "Balanced first impression — na bahut inviting na distant.",
    },
    "mildly_negative": {
        "en": "Mixed first impression — strangers may need a moment to warm up.",
        "hi": "Mixed first impression — log thoda time lete hain warm hone me."
    },
    "negative": {
        "en": "First glance reads as reserved or guarded — easily corrected with brief warmth signals.",
        "hi": "Pehli nazar me reserved/guarded lagte hain — chhoti smile turant change kar sakti hai."
    },
}

DIMENSION_NARRATIVES = {
    "attractiveness":         {"en": "Overall facial attractiveness perception (composite).",
                                "hi": "Overall chehre ki attractiveness."},
    "trustworthiness":        {"en": "Snap judgment of how trustworthy the face appears.",
                                "hi": "Pehli nazar me kitne trustworthy lagte ho."},
    "dominance":              {"en": "Perceived social power / assertiveness.",
                                "hi": "Perceived dominance / assertiveness."},
    "competence":             {"en": "Perceived ability and capability (Todorov 2005).",
                                "hi": "Perceived capability (Todorov 2005)."},
    "likeability":            {"en": "Overall warmth / 'I'd like this person' signal.",
                                "hi": "Overall likeability — 'pasand aate hain' signal."},
    "approachability":        {"en": "How approachable strangers perceive you to be.",
                                "hi": "Strangers ke liye kitne approachable lagte ho."},
    "threat":                 {"en": "Perceived threat (anger-resemblance, Said 2009).",
                                "hi": "Perceived threat / intimidation."},
    "babyfaceness":           {"en": "Baby-face features (large eyes, round, soft jaw).",
                                "hi": "Babyface features — bade eyes, round features, soft jaw."},
    "maturity":               {"en": "Perceived adult maturity (anti-babyface).",
                                "hi": "Perceived maturity."},
    "perceived_health":       {"en": "Perceived health from skin, vitality, symmetry.",
                                "hi": "Perceived health (skin, vitality, symmetry)."},
    "perceived_intelligence": {"en": "Perceived intelligence (forehead, attractive halo).",
                                "hi": "Perceived intelligence."},
    "leadership_potential":   {"en": "Leadership-style first impression (Re 2013).",
                                "hi": "Leadership impression (Re 2013)."},
    "memorability":           {"en": "How memorable the face is to strangers (Bainbridge 2013).",
                                "hi": "Kitne memorable lagte ho."},
    "typicality":             {"en": "How typical / average the face appears.",
                                "hi": "Kitne typical / average lagte ho."},
    "perceived_age":          {"en": "Apparent age inferred vs chronological.",
                                "hi": "Apparent age vs actual age."},
}


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple],
        image_w: int, image_h: int,
        anthropometry_result: Optional[dict] = None,
        symmetry_result: Optional[dict] = None,
        phi_result: Optional[dict] = None,
        fwhr_result: Optional[dict] = None,
        health_result: Optional[dict] = None,
        personality_result: Optional[dict] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None) -> dict:

    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "first_impression", "ok": False, "version": 1,
                 "error": "insufficient_landmarks"}

    # Cross-engine signal extraction
    fwhr_value  = _get_fwhr(fwhr_result)
    dom_z       = _get_dom_z(fwhr_result)
    phi_score   = _get_phi(phi_result)
    sym         = _get_sym(symmetry_result)
    vitality    = _get_vitality(health_result)
    skin_clar   = _get_skin_clarity(health_result)
    dc_score    = _get_dark_circles(health_result)
    aging_score = _get_aging_score(health_result)
    ocean       = _get_personality(personality_result) or {}
    p_vd        = _get_vd(personality_result) or {}
    babyface    = _get_babyface(personality_result)
    smile_prox  = _smile_proxy(personality_result)

    # Geom from personality engine
    p_geom = (personality_result or {}).get("geometric_indicators") or {}
    jaw_angle    = p_geom.get("jaw_angle_deg")
    brow_height  = p_geom.get("brow_height_iod")
    mouth_drop   = p_geom.get("mouth_corner_drop")
    forehead_h   = p_geom.get("forehead_height_ratio")

    O_sc = ocean.get("O"); C_sc = ocean.get("C"); E_sc = ocean.get("E")
    A_sc = ocean.get("A"); N_sc = ocean.get("N")

    # Compute all dimensions
    attract,  e_attr   = _attractiveness(sym, phi_score, skin_clar, vitality, aging_score, age, gender)
    threat,   e_thr    = _threat(brow_height, mouth_drop, fwhr_value, dc_score, smile_prox)
    trust,    e_trust  = _trustworthiness(p_vd, sym, A_sc, smile_prox)
    dom,      e_dom    = _dominance(p_vd, fwhr_value, dom_z, jaw_angle, brow_height)
    compet,   e_comp   = _competence(C_sc, attract, dom, sym, jaw_angle)
    likeab,   e_like   = _likeability(A_sc, E_sc, smile_prox, threat)
    approach, e_appr   = _approachability(A_sc, smile_prox, dom, vitality)
    perc_h,   e_ph     = _perceived_health(skin_clar, vitality, dc_score, sym)
    perc_i,   e_pi     = _perceived_intelligence(C_sc, O_sc, attract, forehead_h)
    leader,   e_lead   = _leadership(compet, dom, attract, age, gender)
    distinct = _distinctiveness(phi_score, None)
    memora,   e_mem    = _memorability(sym, attract, distinct)
    typical = (100 - distinct) if distinct is not None else None
    babyf_score = babyface
    maturity = (100 - babyface) if babyface is not None else None
    apparent_age, age_diff = _perceived_age(aging_score, vitality, dc_score, age)

    # Bayesian shrinkage on all dimensions
    def _shr(s): return None if s is None else _bayesian_shrink(s, alpha=0.30)
    raw_scores = {
        "attractiveness": attract, "trustworthiness": trust, "dominance": dom,
        "competence": compet, "likeability": likeab, "approachability": approach,
        "threat": threat, "babyfaceness": babyf_score, "maturity": maturity,
        "perceived_health": perc_h, "perceived_intelligence": perc_i,
        "leadership_potential": leader, "memorability": memora, "typicality": typical,
    }
    shrunk_scores = {k: _shr(v) for k, v in raw_scores.items()}
    percentiles   = {k: (None if v is None else _score_to_percentile(v))
                      for k, v in shrunk_scores.items()}
    classes       = {k: (None if v is None else _class_label(v))
                      for k, v in shrunk_scores.items()}

    # Halo effect
    halo = _halo_effect(shrunk_scores.get("attractiveness"), shrunk_scores)

    # Stereotype-vulnerability flags
    flags = _stereotype_flags(shrunk_scores, babyface)

    # First-glance valence
    valence = _first_glance_valence(shrunk_scores)
    label = valence.get("label") or "neutral"
    nar   = NARRATIVES.get(label, NARRATIVES["neutral"])

    # Strengths + watch-outs
    strengths = []
    watchouts = []
    for dim, sc in shrunk_scores.items():
        if sc is None: continue
        if dim == "threat":
            if sc <= 35: strengths.append(f"low_{dim}")
            elif sc >= 65: watchouts.append(f"high_{dim}")
        elif dim in ("babyfaceness", "typicality"):
            continue
        else:
            if sc >= 65: strengths.append(f"high_{dim}")
            elif sc <= 35: watchouts.append(f"low_{dim}")

    # Per-dimension contributors (compact)
    contributors = {
        "attractiveness":         e_attr,   "trustworthiness": e_trust,
        "dominance":              e_dom,    "competence":      e_comp,
        "likeability":            e_like,   "approachability": e_appr,
        "threat":                 e_thr,    "perceived_health": e_ph,
        "perceived_intelligence": e_pi,     "leadership_potential": e_lead,
        "memorability":           e_mem,
    }
    contrib_clean = {
        k: ([{"key": kn, "raw_score": round(s, 1), "weight": w} for kn, s, w in v] if v else [])
        for k, v in contributors.items()
    }

    # Confidence per dim
    def _confidence(contribs):
        if not contribs: return "low"
        n = len(contribs)
        if n >= 4: return "high"
        if n >= 2: return "medium"
        return "low"
    confidences = {k: _confidence(v) for k, v in contributors.items()}

    n_signals_used = sum(1 for v in [sym, phi_score, fwhr_value, vitality, skin_clar,
                                       smile_prox, A_sc, C_sc, E_sc, jaw_angle] if v is not None)

    return _py({
        "engine": "first_impression",
        "version": 1,
        "ok": True,
        "model": "Snap_Judgment_100ms_HaloEffect",
        "method": "first_impression_inference_v1",
        "perceived_trait_disclaimer": (
            "First-impression scores reflect SOCIAL PERCEPTION research (Willis & "
            "Todorov 2006, Oosterhof & Todorov 2008). They predict how STRANGERS may "
            "judge in 100ms — NOT actual personality, ability, or character."
        ),
        "do_not_use_for_hiring": True,
        "ethics_notice": (
            "Face-based first impressions are widely shown to be POOR predictors of "
            "actual behaviour (Olivola & Todorov 2010). Outputs MUST NOT be used for "
            "hiring, lending, dating decisions, law-enforcement, or any high-stakes "
            "judgment. Research base is predominantly Western university students; "
            "generalisation to other populations is uncertain. These scores reveal "
            "what bias others may project — they do not measure your actual qualities."
        ),
        "inputs": {
            "gender": gender, "ethnicity": ethnicity, "age": age,
            "n_cross_engine_signals_used": n_signals_used,
            "cross_engine_signals_available": {
                "anthropometry": anthropometry_result is not None and anthropometry_result.get("ok", False),
                "symmetry":      symmetry_result is not None and symmetry_result.get("ok", False),
                "phi":           phi_result is not None and phi_result.get("ok", False),
                "fwhr":          fwhr_result is not None and fwhr_result.get("ok", False),
                "health":        health_result is not None and health_result.get("ok", False),
                "personality":   personality_result is not None and personality_result.get("ok", False),
            },
            "extracted_values": {
                "fwhr": fwhr_value, "dom_z": dom_z, "phi": phi_score, "sym": sym,
                "vitality": vitality, "skin_clarity": skin_clar, "dark_circles": dc_score,
                "aging_score": aging_score, "smile_proxy": smile_prox,
                "babyface_index": babyface, "jaw_angle": jaw_angle,
                "brow_height": brow_height, "forehead_h": forehead_h,
                "ocean": ocean, "vd": p_vd,
            },
        },
        "snap_judgment_scores": shrunk_scores,
        "raw_scores_pre_shrinkage": raw_scores,
        "percentiles":             percentiles,
        "classes":                 classes,
        "confidences":             confidences,
        "contributors":            contrib_clean,
        "perceived_age": {
            "chronological_age": age,
            "apparent_age":      apparent_age,
            "shift_years":       age_diff,
            "interpretation": (None if age_diff is None
                                else "appears_younger" if age_diff <= -2
                                else "appears_older" if age_diff >= 2
                                else "age_appropriate"),
        },
        "first_glance_valence": valence,
        "snap_narrative": nar,
        "halo_effect_analysis": halo,
        "stereotype_vulnerability_flags": flags,
        "strengths": strengths,
        "watch_outs": watchouts,
        "dimension_descriptions": DIMENSION_NARRATIVES,
        "evidence_refs": [
            "Willis_Todorov_2006_PsycholSci_100ms",
            "Oosterhof_Todorov_2008_PNAS_VD",
            "Todorov_Mandisodza_2005_Science_competence",
            "Said_Sebe_Todorov_2009_threat",
            "Dion_Berscheid_Walster_1972_halo",
            "Berry_McArthur_1985_babyface",
            "Stephen_Coetzee_Perrett_2009_health",
            "Zebrowitz_Hall_2002_intelligence",
            "Re_Hunter_2013_leadership",
            "Rule_Ambady_2008_CEO_faces",
            "Bainbridge_Isola_Oliva_2013_memorability",
            "Said_Dotsch_Todorov_2010_typicality",
            "Olivola_Todorov_2010_face_inferences_poor",
        ],
        "caveats": [
            "Snap-judgment effects are real but MODEST; v1 applies Bayesian shrinkage (α=0.30).",
            "Single-frame static photo — does not capture micro-expression dynamics.",
            "Scores describe BIAS in how strangers perceive — not your actual traits.",
            "Halo effect: high attractiveness inflates other ratings (Dion 1972).",
            "First impressions can be intentionally shifted: smile, posture, eye contact.",
            "Research base is predominantly Western — cross-cultural generalisation uncertain.",
        ],
        "disclaimer": (
            "These are PERCEIVED first-impression scores — what observers may judge in "
            "100ms — NOT validated personality or ability assessments. Face-based "
            "judgments are POOR predictors of actual behaviour (Olivola & Todorov 2010). "
            "Use only for self-awareness of stereotype-vulnerability and impression management."
        ),
    })
