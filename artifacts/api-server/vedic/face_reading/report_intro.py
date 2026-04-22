"""
Report intro builders — Hook page (Page 1), TL;DR page (Page 2),
and restructured Final Truth (3 strengths + 3 risks + 1 direction).

These read from already-built sections + engines + synthesis and produce
small dicts that the PDF render layer can consume directly.

Goal: instant emotional connection in first 5 seconds + value-on-skip TL;DR.
"""
from __future__ import annotations
from typing import Dict, List, Any


# ── helpers ──────────────────────────────────────────────────────────────
def _g(d: Any, *path, default=None):
    """Safe nested get."""
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def _shorten(s: str, n: int = 110) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(" ", 1)[0]
    return cut + "…"


# ── Page 1 :: HOOK ───────────────────────────────────────────────────────
def build_hook(sections: Dict, engines: Dict, person: Dict | None = None) -> Dict:
    """
    Build a tight 'hook' for cover page:
      - identity_line   : 1 deep specific line
      - shock_line      : 1 most-surprising insight
      - score_snapshot  : { vitality, charisma, leadership } 0-100
      - element + archetype tag
    """
    person = person or {}
    fs = _g(sections, "final_scores", default={}) or {}
    syn = _g(sections, "synthesis", default={}) or {}
    samu = _g(engines, "samudrika", default={}) or {}
    pers = _g(engines, "personality", default={}) or {}
    fi = _g(engines, "first_impression", default={}) or {}

    element = (fs.get("element") or _g(samu, "element_profile", "dominant_element")
               or "Balanced")
    archetype = (
        fs.get("archetype")
        or _g(pers, "archetype", "label")
        or _g(pers, "archetype", "name")
        or "Balanced Soul"
    )
    if isinstance(archetype, str) and archetype.strip().lower() == "average":
        archetype = "Balanced"
    dom_trait = fs.get("dominant_trait") or "Energy"

    # Identity line — specific, not generic
    biggest_strength = _g(sections, "section_1_power_summary",
                          "biggest_strength") or ""
    biggest_weakness = _g(sections, "section_1_power_summary",
                          "biggest_weakness") or ""
    perceived_age = _g(fi, "perceived_age", "value")

    if biggest_strength and biggest_weakness:
        identity_line = (
            f"Tum {element} element ke {archetype.lower()} ho — "
            f"superpower: {biggest_strength.rstrip('.')}; "
            f"hidden trap: {biggest_weakness.rstrip('.')}."
        )
    else:
        identity_line = (
            f"Tum {element} element ke {archetype.lower()} ho — "
            f"core energy: {dom_trait}."
        )

    # Shock line — pick the highest-confidence shock, fallback to first fused trait
    shocks = syn.get("shock_insights") or []
    confs = {c.get("label", ""): c.get("score", 0)
             for c in (syn.get("confidence_scores") or []) if isinstance(c, dict)}
    shock_line = ""
    best_score = -1
    for sh in shocks:
        if not isinstance(sh, dict):
            continue
        text = sh.get("insight", "")
        # match confidence by label-prefix
        score = 50
        for lbl, sc in confs.items():
            if text and lbl and text[:30] in lbl:
                score = sc; break
        if score > best_score and text:
            best_score = score
            shock_line = text
    if not shock_line and shocks:
        shock_line = shocks[0].get("insight", "") if isinstance(shocks[0], dict) else ""

    # Score snapshot
    vitality = float(fs.get("vitality") or _g(engines, "health", "vitality_score") or 0)
    charisma = float(_g(fi, "attractiveness", "value") or 0)
    leadership = 0
    bonus = _g(sections, "bonus_personality_score") or {}
    for blk in (bonus.get("blocks") or []):
        if not isinstance(blk, dict):
            continue
        km = blk.get("key_metric") or {}
        if "Leadership" in (km.get("label") or ""):
            v = km.get("value") or ""
            try:
                leadership = float(str(v).split("/")[0]) * 10
            except Exception:
                leadership = 0
            break

    return {
        "identity_line": identity_line,
        "shock_line":    _shorten(shock_line, 220),
        "shock_confidence": int(best_score) if best_score > 0 else 70,
        "element":       element,
        "archetype":     archetype,
        "dominant_trait": dom_trait,
        "perceived_age": perceived_age,
        "scores": {
            "vitality":   round(vitality, 1),
            "charisma":   round(charisma, 1),
            "leadership": round(leadership, 1),
        },
    }


# ── Page 2 :: TL;DR SUMMARY ──────────────────────────────────────────────
def build_tldr(sections: Dict, engines: Dict) -> Dict:
    """
    Value-on-skip page — reader gets full essence even if they read nothing else.
      - top_5_traits      : list of {trait, score}
      - top_3_strengths   : list of strings
      - top_3_weaknesses  : list of strings
      - life_pattern      : single sentence
    """
    fs = _g(sections, "final_scores", default={}) or {}
    syn = _g(sections, "synthesis", default={}) or {}
    pers = _g(engines, "personality", default={}) or {}
    s1 = _g(sections, "section_1_power_summary", default={}) or {}
    s7 = _g(sections, "section_7_personality_synthesis", default={}) or {}
    s21 = _g(sections, "section_21_final_truth", default={}) or {}

    # ── Top 5 personality traits (OCEAN ordered by deviation from 50) ────
    ocean = fs.get("ocean") or {}
    label_map = {
        "openness":         ("Openness",          "Naye anubhav, creativity, curiosity"),
        "conscientiousness":("Conscientiousness", "Discipline, organisation, on-time delivery"),
        "extraversion":     ("Extraversion",      "Social energy, group me khulna"),
        "agreeableness":    ("Agreeableness",     "Cooperation, empathy, trust"),
        "neuroticism":      ("Neuroticism",       "Stress sensitivity, mood swings"),
    }
    traits = []
    for k, (lbl, desc) in label_map.items():
        v = ocean.get(k)
        if v is None:
            continue
        try:
            v = float(v)
        except Exception:
            continue
        # tag direction
        direction = "high" if v >= 60 else ("low" if v <= 40 else "balanced")
        traits.append({
            "name":  lbl,
            "score": round(v, 1),
            "tag":   direction,
            "desc":  desc,
        })
    # Order by deviation from 50 (most defining traits first)
    traits.sort(key=lambda x: abs(x["score"] - 50), reverse=True)
    top_5_traits = traits[:5]

    # ── Top 3 strengths (from s1, s7 blocks, fused traits, OCEAN highs) ──
    strengths: List[str] = []
    if s1.get("biggest_strength"):
        strengths.append(s1["biggest_strength"].rstrip("."))
    # fused traits — full pool, not just first 3
    for ft in (syn.get("fused_traits") or []):
        if isinstance(ft, dict):
            t = ft.get("trait")
            if t and str(t) not in strengths:
                strengths.append(str(t))
    # OCEAN high traits as fallback (high score → user-friendly strength)
    _OCEAN_STRENGTH_LABEL = {
        "openness":          "Curious learner — naye ideas pe khulkar sochte ho",
        "conscientiousness": "Disciplined executor — commitments time pe deliver karte ho",
        "extraversion":      "Social energiser — group me naturally chamak jaate ho",
        "agreeableness":     "Empathetic collaborator — log tum par easily trust karte hain",
        "neuroticism":       "Emotionally calm — pressure me steady rehte ho",  # only when LOW
    }
    if len(strengths) < 3:
        for k, v in (ocean.items() if isinstance(ocean, dict) else []):
            try: vf = float(v)
            except Exception: continue
            # Neuroticism flips: low-N is the strength
            high = (vf <= 40) if k == "neuroticism" else (vf >= 60)
            if high and _OCEAN_STRENGTH_LABEL.get(k):
                lbl = _OCEAN_STRENGTH_LABEL[k]
                if lbl not in strengths:
                    strengths.append(lbl)
            if len(strengths) >= 3: break
    # Balanced-profile fallback: when no trait stands out, the profile itself is the strength
    _BALANCED_FALLBACKS = [
        "Versatile adapter — har tarah ke role aur log ke saath fit ho jaate ho",
        "Emotional steadiness — extreme reactions nahi, calm decision-maker",
        "No-drama presence — log tumhare paas peace dhundte hain",
    ]
    if len(strengths) < 3:
        for lbl in _BALANCED_FALLBACKS:
            if lbl not in strengths:
                strengths.append(lbl)
            if len(strengths) >= 3: break
    # dedupe + cap
    strengths = list(dict.fromkeys([s for s in strengths if s]))[:3]

    # ── Top 3 weaknesses (from s1, red flags, OCEAN extremes, behaviour) ─
    weaknesses: List[str] = []
    brutal_norm = (s21.get("brutal_truth") or "").strip().rstrip(".").lower()
    mistake_norm = (s21.get("biggest_mistake_hi") or "").strip().rstrip(".").lower()

    def _wadd(text: str):
        if not text: return
        t = text.rstrip(".").strip()
        # Don't echo brutal_truth (it gets its own banner in Final Truth)
        norm = t.lower()
        if norm and norm != brutal_norm and norm != mistake_norm and t not in weaknesses:
            weaknesses.append(t)

    _wadd(s1.get("biggest_weakness"))
    rf = _g(sections, "section_10_red_flags", default={}) or {}
    for blk in (rf.get("blocks") or []):
        if isinstance(blk, dict):
            _wadd(blk.get("heading_en") or blk.get("heading_hi") or "")
        if len(weaknesses) >= 3: break

    # OCEAN-derived blind spots
    _OCEAN_WEAK_LABEL = {
        "openness":          ("Routine-loving — nayi cheezein avoid karne ki tendency", "low"),
        "conscientiousness": ("Follow-through gap — execution slip-ups occasional", "low"),
        "extraversion":      ("Networking aur self-promotion avoid karte ho", "low"),
        "agreeableness":     ("Conflict me thoda blunt — diplomacy effort lagta hai", "low"),
        "neuroticism":       ("Stress reactivity — chhoti baat pe trigger hote ho", "high"),
    }
    if len(weaknesses) < 3:
        for k, (lbl, dir_) in _OCEAN_WEAK_LABEL.items():
            try: vf = float(ocean.get(k))
            except Exception: continue
            hit = (vf >= 60) if dir_ == "high" else (vf <= 40)
            if hit:
                _wadd(lbl)
            if len(weaknesses) >= 3: break

    # Generic blind-spot fallbacks when nothing else surfaces (used for very
    # balanced profiles where neither extreme nor red-flag triggers).
    _BALANCED_BLINDSPOTS = [
        "Decision lateness — perfect option dhundhte dhundhte timing miss kar dete ho",
        "Self-marketing gap — kaam strong hai par log ko pata kam chalta hai",
        "Boundary softness — 'na' bolne me extra effort lagta hai",
    ]
    if len(weaknesses) < 3:
        for lbl in _BALANCED_BLINDSPOTS:
            _wadd(lbl)
            if len(weaknesses) >= 3: break

    weaknesses = list(dict.fromkeys([w for w in weaknesses if w]))[:3]

    # ── Life pattern (one line) ───────────────────────────────────────────
    life_pattern = (
        s7.get("behaviour_pattern")
        or _g(sections, "section_14_life_flow", "summary_hi")
        or _g(sections, "section_14_life_flow", "summary")
        or ""
    )
    life_pattern = _shorten(str(life_pattern), 220)
    if not life_pattern:
        element = fs.get("element", "Balanced")
        archetype = fs.get("archetype", "Balanced Soul")
        life_pattern = (
            f"{element}-driven {archetype.lower()} — slow start, "
            f"deep middle, steady late-life climb."
        )

    return {
        "top_5_traits":     top_5_traits,
        "top_3_strengths":  strengths or ["Calm under pressure",
                                          "Deep thinker",
                                          "Reliable executor"],
        "top_3_weaknesses": weaknesses or ["Avoids self-promotion",
                                           "Slow to open up",
                                           "Skips recovery time"],
        "life_pattern":     life_pattern,
    }


# ── Page :: FINAL TRUTH v2 (3+3+1 format) ────────────────────────────────
def build_final_truth_v2(sections: Dict, engines: Dict, tldr: Dict | None = None) -> Dict:
    """
    Restructure final truth into impact format:
      - 3 strengths   (one-liners)
      - 3 risks       (one-liners)
      - 1 direction   (single life-direction sentence)
      - brutal_truth  (kept from original)
    """
    s21 = _g(sections, "section_21_final_truth", default={}) or {}
    tldr = tldr or build_tldr(sections, engines)

    strengths = list(tldr.get("top_3_strengths") or [])[:3]
    risks = list(tldr.get("top_3_weaknesses") or [])[:3]

    brutal = s21.get("brutal_truth") or s21.get("closing_truth", "")
    brutal_norm = (brutal or "").strip().rstrip(".").lower()

    # Dedup: ensure no risk line echoes the brutal_truth banner
    risks = [r for r in risks if (r or "").strip().rstrip(".").lower() != brutal_norm][:3]

    # Direction — use must_do, fallback to a generic action-line, but NEVER the
    # brutal-truth or biggest_mistake (those would reprint above).
    direction_candidates = [s21.get("must_do")]
    fb_action = "Apni biggest strength ko har hafte 1 naya audience dikhao — visibility tumhari sabse badi missing piece hai."
    direction = next(
        (d for d in direction_candidates
         if isinstance(d, str) and d.strip()
         and d.strip().rstrip(".").lower() != brutal_norm),
        fb_action,
    )
    direction = _shorten(str(direction), 220)

    return {
        "strengths": strengths,
        "risks":     risks,
        "direction": direction,
        "brutal_truth": _shorten(str(brutal), 320),
    }
