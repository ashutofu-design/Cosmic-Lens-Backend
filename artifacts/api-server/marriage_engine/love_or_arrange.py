"""
marriage_engine/love_or_arrange.py
==================================
LOVE vs ARRANGED Marriage Classifier — Phase 2.8.25

ARCHITECTURE: 25 RULES + 3 TRUST LAYERS
  Engine 1 — Parashari D1 (10 rules, weight 30%)
  Engine 2 — D9 Navamsha   (4 rules, weight 25%)
  Engine 3 — KP CSL        (4 levels + 7 advanced rules, weight 45%)

  Trust Layer 1 — Self-disclosure honoring (NLP parser)
                  If user states "love marriage hua tha", engine NEVER
                  contradicts. Switches to EXPLAIN mode.

  Trust Layer 2 — Multi-engine consensus check
                  Run all 3 engines INDEPENDENTLY. If all 3 agree -> high
                  confidence. If they disagree -> honestly say "MIXED".

  Trust Layer 3 — 5-band confidence calibration
                  Translate raw score -> humble verdict text:
                    STRONG (90-100), HIGH (75-89), MODERATE (60-74),
                    MIXED (40-59), LOW (0-39)

DESIGN PRINCIPLE: Trust > Accuracy
  A wrong "definite" verdict destroys devotee trust forever.
  A humble "leaning" verdict is forgivable even when wrong.
  Engine ALWAYS uses confidence-aware tone.

Public function:
  classify_marriage_type(kundli, intel, kp, birth, question="") -> dict
"""

from __future__ import annotations

import re
from typing import Any, Optional


# ════════════════════════════════════════════════════════════════════════
# TRUST LAYER 1 — Self-Disclosure Honoring (NLP Parser)
# ════════════════════════════════════════════════════════════════════════

# User has STATED love marriage already happened
_LOVE_DECLARED_PATTERNS = [
    r"love\s*marriage\s*(?:hu[ai]\s*tha|ho\s*gay[ai]|kar\s*liy[ae]|hai)",
    r"love\s*me(?:i)?n?\s*shaadi",
    r"love\s*se\s*shaadi",
    r"pyaar\s*me(?:i)?n?\s*shaadi",
    r"pyaar\s*se\s*shaadi",
    r"love\s*marriage\s*ki\s*hai",
    r"\bhad\s+a\s+love\s+marriage\b",
    r"\blove\s+married\b",
    r"\bmarried\s+for\s+love\b",
    r"प्रेम\s*विवाह",
    r"लव\s*मैरिज",
]

# User has STATED arranged marriage already happened
_ARRANGE_DECLARED_PATTERNS = [
    r"arranged\s*marriage\s*(?:hu[ai]\s*tha|ho\s*gay[ai]|hai)",
    r"family\s*ne\s*kar(?:wa|a)y[ai]",
    r"ghar\s*walon\s*ne\s*kar(?:wa|a)y[ai]",
    r"ghar\s*walo[n]?\s*ne",
    r"rishta\s*aaya\s*tha",
    r"\barranged\s+marriage\b",
    r"अरेंज्ड\s*मैरिज",
    r"घरवालों\s*ने",
]

# Tense markers
_PAST_TENSE_PATTERNS = [
    r"\bhu[ai]\s+th[ai]\b", r"\bho\s+gay[ai]\b", r"\bho\s+chuk[ai]\b",
    r"\bkar\s+liy[ae]\b", r"\bhui\s+thi\b",
    r"\bkar\w*\s+th[ai]\b",            # karwayi thi, kari thi, kiya tha
    r"\bki\s+th[ai]\b",                # ki thi
    r"\bgay[ai]\s+th[ai]\b",           # gayi thi, gaya tha
    r"\bwas\b", r"\bwere\b", r"\bhad\b", r"\bdid\b",
]

_FUTURE_TENSE_PATTERNS = [
    r"\bhog[ai]\b", r"\bkarunga\b", r"\bkarungi\b",
    r"\baage\b", r"\bfuture\b", r"\bkab\b",
    r"\bwill\b", r"\bgoing\s+to\b",
]

_SELF_REF_PATTERNS = [
    r"\bmer[ai]\b", r"\bmujhe\b", r"\bhumar[ai]\b",
    r"\bmy\b", r"\bI\b", r"\bme\b",
]


def _detect_self_disclosure(question: str) -> dict:
    """Trust Layer 1 core. Parse user question and detect:
      - Has user already STATED their marriage type? (mode = EXPLAIN)
      - Is it past / present / future tense?
      - Is it self-referential or general?

    Returns dict:
      {
        "mode":          "EXPLAIN" | "VERIFY" | "PREDICT" | "GENERAL",
        "stated_type":   "LOVE" | "ARRANGED" | None,
        "tense":         "PAST" | "PRESENT" | "FUTURE" | "UNKNOWN",
        "self_ref":      bool,
      }
    """
    if not question or not isinstance(question, str):
        return {"mode": "PREDICT", "stated_type": None,
                "tense": "UNKNOWN", "self_ref": False}

    q = question.lower().strip()

    # Compile-once regex helpers
    def _any(patterns):
        return any(re.search(p, q, re.IGNORECASE) for p in patterns)

    self_ref = _any(_SELF_REF_PATTERNS)

    # Tense
    if _any(_FUTURE_TENSE_PATTERNS):
        tense = "FUTURE"
    elif _any(_PAST_TENSE_PATTERNS):
        tense = "PAST"
    else:
        tense = "PRESENT"

    # Stated type
    stated_type = None
    if _any(_LOVE_DECLARED_PATTERNS):
        stated_type = "LOVE"
    elif _any(_ARRANGE_DECLARED_PATTERNS):
        stated_type = "ARRANGED"

    # Mode determination
    #   EXPLAIN: user has stated their type AND it's first-person experiential
    #            (either explicit self-ref OR past tense — past-tense
    #             marriage statements are inherently first-person.)
    if stated_type and (self_ref or tense == "PAST"):
        mode = "EXPLAIN"   # User told us answer; engine just explains why
    elif tense == "PAST" and self_ref:
        mode = "VERIFY"    # User asking past — be careful
    elif tense == "FUTURE":
        mode = "PREDICT"   # Full engine power
    elif self_ref:
        mode = "PREDICT"   # Default predict for self-Q
    else:
        mode = "GENERAL"   # Educational / non-specific

    return {"mode": mode, "stated_type": stated_type,
            "tense": tense, "self_ref": self_ref}


# ════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES — extract data from kundli/intel/kp/d9 dicts
# ════════════════════════════════════════════════════════════════════════

def _planet_house(kundli: dict, planet_name: str) -> Optional[int]:
    """Find which house a planet is in from kundli['planets'] list."""
    for p in (kundli.get("planets") or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            h = p.get("house")
            return int(h) if isinstance(h, int) else None
    return None


def _house_lord(intel: dict, house: int) -> Optional[str]:
    """Lord of given house from intel['house_lords']."""
    for hl in (intel.get("house_lords") or []):
        if isinstance(hl, dict) and hl.get("house") == house:
            return hl.get("lord")
    return None


def _lord_in_house(intel: dict, house: int) -> Optional[int]:
    """In which house does the lord of `house` sit?"""
    for hl in (intel.get("house_lords") or []):
        if isinstance(hl, dict) and hl.get("house") == house:
            v = hl.get("lord_in_house")
            return int(v) if isinstance(v, int) else None
    return None


def _are_conjunct(kundli: dict, p1: str, p2: str) -> bool:
    """Two planets are conjunct iff both in same house."""
    h1 = _planet_house(kundli, p1)
    h2 = _planet_house(kundli, p2)
    return h1 is not None and h1 == h2


def _kp_cusp(kp: dict, house: int) -> Optional[dict]:
    """Get the KP cusp dict for a given house number (1-12)."""
    for c in (kp.get("cusps") or []):
        if isinstance(c, dict) and c.get("house") == house:
            return c
    return None


def _kp_significators_of(kp: dict, house: int) -> set:
    """Compute KP significators of a house using 4-level CCS:
      L1: planets occupying house
      L2: lord of house cusp sign (sl) and the cusp's nl/sb
      L3: planets whose nl is one of the L1+L2 set
      L4: planets whose sb is one of the L1+L2 set

    Returns a set of planet names that signify this house.
    """
    sigs: set = set()
    # L1: planets in this house
    for p in (kp.get("planets") or []):
        if isinstance(p, dict) and p.get("house") == house:
            n = p.get("name")
            if n:
                sigs.add(n)
    # L2: cusp's sl/nl/sb
    cusp = _kp_cusp(kp, house)
    if cusp:
        for k in ("sl", "nl", "sb"):
            v = cusp.get(k)
            if v:
                sigs.add(v)
    # L3 + L4: planets whose nl/sb is in the seed set
    seed = set(sigs)
    for p in (kp.get("planets") or []):
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if not nm:
            continue
        if p.get("nl") in seed:
            sigs.add(nm)
        if p.get("sb") in seed:
            sigs.add(nm)
    return sigs


def _planets_in_kp_house(kp: dict, house: int) -> set:
    """Planets occupying the given house in KP chart."""
    out: set = set()
    for p in (kp.get("planets") or []):
        if isinstance(p, dict) and p.get("house") == house:
            n = p.get("name")
            if n:
                out.add(n)
    return out


def _kp_planet_record(kp: dict, planet_name: str) -> Optional[dict]:
    """Return the KP planet dict for a given planet name (or None)."""
    if not planet_name:
        return None
    for p in (kp.get("planets") or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            return p
    return None


def _csl_chain(kp: dict, csl_planet: str) -> dict:
    """In KP, the X-th CSL is itself a PLANET. Its 'star lord' / 'sub-sub
    lord' are NOT the cusp's nl/ss — they are the NL/SS of the *CSL planet*
    looked up in the planet table.

    Returns:
      {"csl": csl_planet, "star": <nl of csl_planet>, "sub_sub": <ss of csl_planet>}
    Empty dict if CSL planet is None / not found.
    """
    rec = _kp_planet_record(kp, csl_planet)
    if not rec:
        return {}
    return {
        "csl":     csl_planet,
        "star":    rec.get("nl"),
        "sub_sub": rec.get("ss"),
    }


# ════════════════════════════════════════════════════════════════════════
# ENGINE 1 — PARASHARI D1 (10 RULES)
# ════════════════════════════════════════════════════════════════════════

def _engine_parashari_d1(kundli: dict, intel: dict) -> dict:
    """Score 10 classical Parashari rules from D1 (rashi) chart.

    LOVE rules (6):
      P1. 5L in 7H                            (Pancham-Saptam yoga)
      P2. 7L in 5H                            (reverse exchange)
      P3. Venus + Rahu conjunction
      P4. Venus + Mars conjunction
      P5. Rahu in 7H
      P6. Moon + Venus conjunction

    ARRANGED rules (4):
      P7. Jupiter aspect on 7H                (Jupiter in 3/5/9 from 7th)
      P8. 9L in 7H or conjunct 7L             (parents involvement)
      P9. 2L conjunct 7L                      (family/kutumb approval)
      P10. Saturn in 7H without Rahu          (traditional/delayed)
    """
    love = 0
    arr = 0
    rsl: list = []
    rsa: list = []

    seventh_lord = _house_lord(intel, 7)
    fifth_lord   = _house_lord(intel, 5)
    ninth_lord   = _house_lord(intel, 9)
    second_lord  = _house_lord(intel, 2)
    fifth_lord_in  = _lord_in_house(intel, 5)
    seventh_lord_in = _lord_in_house(intel, 7)

    # P1: 5L in 7H
    if fifth_lord_in == 7:
        love += 18
        rsl.append(f"D1: 5L ({fifth_lord}) in 7H — Pancham-Saptam yoga")

    # P2: 7L in 5H
    if seventh_lord_in == 5:
        love += 18
        rsl.append(f"D1: 7L ({seventh_lord}) in 5H — marriage-romance bridge")

    # P3: Venus + Rahu conjunction
    if _are_conjunct(kundli, "Venus", "Rahu"):
        love += 16
        h = _planet_house(kundli, "Venus")
        rsl.append(f"D1: Venus + Rahu conjunct in {h}H — unconventional romance")

    # P4: Venus + Mars conjunction
    if _are_conjunct(kundli, "Venus", "Mars"):
        love += 12
        h = _planet_house(kundli, "Venus")
        rsl.append(f"D1: Venus + Mars conjunct in {h}H — passion-driven union")

    # P5: Rahu in 7H
    if _planet_house(kundli, "Rahu") == 7:
        love += 14
        rsl.append("D1: Rahu in 7H — unconventional/foreign spouse")

    # P6: Moon + Venus conjunction
    if _are_conjunct(kundli, "Moon", "Venus"):
        love += 10
        rsl.append("D1: Moon + Venus conjunct — emotional + romantic temperament")

    # P7: Jupiter aspect on 7H
    #   Jupiter aspects 5th, 7th, 9th from itself.
    #   Jupiter aspecting 7H means Jupiter in 1H (7th aspect),
    #   Jupiter in 3H (5th from 3 = 7), or Jupiter in 11H (9th from 11 = 7).
    jup_h = _planet_house(kundli, "Jupiter")
    if jup_h in (1, 3, 11):
        arr += 18
        rsa.append(f"D1: Jupiter in {jup_h}H aspects 7H — sanctified by guru/elders")

    # P8: 9L in 7H OR 9L conjunct 7L
    ninth_lord_in = _lord_in_house(intel, 9)
    if ninth_lord_in == 7:
        arr += 16
        rsa.append(f"D1: 9L ({ninth_lord}) in 7H — direct parental involvement")
    elif ninth_lord and seventh_lord and _are_conjunct(kundli, ninth_lord, seventh_lord):
        arr += 14
        rsa.append(f"D1: 9L ({ninth_lord}) conjunct 7L ({seventh_lord}) — dharma-led union")

    # P9: 2L conjunct 7L
    if second_lord and seventh_lord and _are_conjunct(kundli, second_lord, seventh_lord):
        arr += 10
        rsa.append(f"D1: 2L ({second_lord}) conjunct 7L — family lineage approval")

    # P10: Saturn in 7H without Rahu
    sat_h = _planet_house(kundli, "Saturn")
    rahu_h = _planet_house(kundli, "Rahu")
    if sat_h == 7 and rahu_h != 7:
        arr += 12
        rsa.append("D1: Saturn in 7H (no Rahu) — patient + traditional marriage")

    love = min(100, love)
    arr  = min(100, arr)
    return {
        "name": "Parashari D1",
        "love_score": love,
        "arr_score": arr,
        "verdict": _engine_verdict(love, arr),
        "reasons_love": rsl,
        "reasons_arr": rsa,
    }


# ════════════════════════════════════════════════════════════════════════
# ENGINE 2 — D9 NAVAMSHA (4 RULES)
# ════════════════════════════════════════════════════════════════════════

# Sign index -> sign lord (0=Aries..11=Pisces)
_SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
               "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]


def _d9_planet_sign(d9: dict, planet: str) -> Optional[str]:
    info = (d9 or {}).get(planet)
    if isinstance(info, dict):
        return info.get("sign")
    return None


def _d9_same_sign(d9: dict, p1: str, p2: str) -> bool:
    s1 = _d9_planet_sign(d9, p1)
    s2 = _d9_planet_sign(d9, p2)
    return bool(s1) and s1 == s2


def _engine_d9_navamsha(kundli: dict, intel: dict) -> dict:
    """Score 4 D9 navamsa rules.

    LOVE rules (3):
      D1. D9 Venus + Rahu in same sign       (D9 love confirmation)
      D2. D9 5L-7L in same sign              (D9 Pancham-Saptam)
      D3. D9 7L conjunct Rahu                (D9 unconventional spouse)

    ARRANGED rule (1):
      D4. D9 7L exalted/own sign             (D9 traditional strength)
    """
    love = 0
    arr = 0
    rsl: list = []
    rsa: list = []

    # Compute D9 lazily (only if planets data available)
    d9 = {}
    try:
        from divisional_charts import compute_d9   # type: ignore
        planets_list = kundli.get("planets") or []
        lagna_lon = kundli.get("lagna_lon")
        d9 = compute_d9(planets_list, lagna_lon) or {}
    except Exception:
        d9 = {}

    if not d9:
        return {
            "name": "D9 Navamsha", "love_score": 0, "arr_score": 0,
            "verdict": "UNKNOWN", "reasons_love": [], "reasons_arr": [],
            "available": False,
        }

    seventh_lord = _house_lord(intel, 7)
    fifth_lord   = _house_lord(intel, 5)

    # D1: D9 Venus + Rahu same sign
    if _d9_same_sign(d9, "Venus", "Rahu"):
        love += 28
        rsl.append("D9: Venus + Rahu in same navamsa sign — love confirmed in marriage chart")

    # D2: D9 5L + 7L same sign
    if fifth_lord and seventh_lord and _d9_same_sign(d9, fifth_lord, seventh_lord):
        love += 28
        rsl.append(f"D9: 5L ({fifth_lord}) + 7L ({seventh_lord}) in same navamsa sign — D9 Pancham-Saptam")

    # D3: D9 7L conjunct Rahu
    if seventh_lord and _d9_same_sign(d9, seventh_lord, "Rahu"):
        love += 22
        rsl.append(f"D9: 7L ({seventh_lord}) conjunct Rahu in navamsa — unconventional spouse")

    # D4: D9 7L exalted/own sign
    #     Exaltation: Sun=Aries, Moon=Taurus, Mars=Capricorn, Mercury=Virgo,
    #                 Jupiter=Cancer, Venus=Pisces, Saturn=Libra
    #     Own: lord matches sign lord.
    if seventh_lord:
        d9_sign = _d9_planet_sign(d9, seventh_lord)
        if d9_sign:
            exaltations = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
                           "Mercury": "Virgo", "Jupiter": "Cancer",
                           "Venus": "Pisces", "Saturn": "Libra"}
            sign_idx_map = {"Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3,
                            "Leo": 4, "Virgo": 5, "Libra": 6, "Scorpio": 7,
                            "Sagittarius": 8, "Capricorn": 9, "Aquarius": 10,
                            "Pisces": 11}
            is_exalted = (exaltations.get(seventh_lord) == d9_sign)
            sign_idx = sign_idx_map.get(d9_sign)
            is_own = (sign_idx is not None and _SIGN_LORDS[sign_idx] == seventh_lord)
            if is_exalted or is_own:
                arr += 22
                rsa.append(f"D9: 7L ({seventh_lord}) exalted/own in {d9_sign} — D9 traditional strength")

    love = min(100, love)
    arr  = min(100, arr)
    return {
        "name": "D9 Navamsha",
        "love_score": love,
        "arr_score": arr,
        "verdict": _engine_verdict(love, arr),
        "reasons_love": rsl,
        "reasons_arr": rsa,
        "available": True,
    }


# ════════════════════════════════════════════════════════════════════════
# ENGINE 3 — KP CUSPAL SUB-LORD (4 LEVELS + 7 ADVANCED RULES)
# ════════════════════════════════════════════════════════════════════════

def _engine_kp_csl(kp: dict) -> dict:
    """Score 4 KP CSL levels + 7 advanced rules.

    CORE 4 LEVELS:
      K1. 7th CSL itself signifies 5H              (primary love signal)
      K2. 7th CSL's STAR LORD signifies 5H         (star-level confirmation)
      K3. 7th CSL's SUB-SUB LORD signifies 5H      (refinement)
      K4. 5th CSL signifies 7H AND 11H             (cross-check)

    ADVANCED (7 rules):
      KA. 7th CSL in star of planet posited in 5H
      KB. Mutual CSL: 5H CSL == 7H CSL                (definite love)
      KC. Rahu = 7th CSL OR star/sub                 (inter-caste love)
      KD. Venus = 7th CSL + signifies 5H             (pure romance)
      KE. 11th CSL signifies 5H + 7H                 (desire fulfilled)
      KN1. 7th CSL signifies 6/8/12 strongly         (NEGATION)
      KN2. 5th CSL signifies 6H                      (NEGATION — breakup)
    """
    love = 0
    arr = 0
    rsl: list = []
    rsa: list = []

    if not kp or not kp.get("cusps"):
        return {
            "name": "KP CSL", "love_score": 0, "arr_score": 0,
            "verdict": "UNKNOWN", "reasons_love": [], "reasons_arr": [],
            "available": False,
        }

    cusp7 = _kp_cusp(kp, 7) or {}
    cusp5 = _kp_cusp(kp, 5) or {}
    cusp11 = _kp_cusp(kp, 11) or {}

    csl7 = cusp7.get("sb")
    csl5 = cusp5.get("sb")
    csl11 = cusp11.get("sb")
    # KP semantics: the X-th CSL is a PLANET. Its star lord / sub-sub lord
    # are derived from THAT PLANET'S record (its own nl/ss), not from the
    # cusp's nl/ss. Fix per architect review (2.8.25 R1).
    chain7 = _csl_chain(kp, csl7)
    star7 = chain7.get("star")
    sub_sub7 = chain7.get("sub_sub")

    sig5 = _kp_significators_of(kp, 5)
    sig7 = _kp_significators_of(kp, 7)
    sig11 = _kp_significators_of(kp, 11)
    sig6 = _kp_significators_of(kp, 6)
    sig8 = _kp_significators_of(kp, 8)
    sig12 = _kp_significators_of(kp, 12)

    # K1: 7th CSL signifies 5H
    if csl7 and csl7 in sig5:
        love += 22
        rsl.append(f"KP L1: 7th CSL ({csl7}) signifies 5H — primary love signal")

    # K2: 7th CSL star lord signifies 5H
    if star7 and star7 in sig5:
        love += 22
        rsl.append(f"KP L2: 7th CSL star lord ({star7}) signifies 5H — strong love")

    # K3: 7th CSL sub-sub lord signifies 5H
    if sub_sub7 and sub_sub7 in sig5:
        love += 12
        rsl.append(f"KP L3: 7th CSL sub-sub ({sub_sub7}) signifies 5H — refinement")

    # K4: 5th CSL signifies 7H + 11H
    if csl5 and csl5 in sig7 and csl5 in sig11:
        love += 22
        rsl.append(f"KP L4: 5th CSL ({csl5}) signifies 7H+11H — romance matures into marriage")

    # KA: 7th CSL in star of planet in 5H
    planets_in_5 = _planets_in_kp_house(kp, 5)
    if star7 and star7 in planets_in_5:
        love += 18
        rsl.append(f"KP RuleA: 7th CSL star ({star7}) is planet posited in 5H — strong love")

    # KB: Mutual CSL
    if csl5 and csl5 == csl7:
        love += 25
        rsl.append(f"KP RuleB: 5H CSL == 7H CSL ({csl7}) — definite love marriage")

    # KC: Rahu involvement in 7th CSL chain
    if csl7 == "Rahu":
        love += 18
        rsl.append("KP RuleC: 7th CSL = Rahu — inter-caste/unconventional love")
    elif star7 == "Rahu":
        love += 14
        rsl.append("KP RuleC: 7th CSL star = Rahu — inter-caste tendency")

    # KD: Venus = 7th CSL + signifies 5H
    if csl7 == "Venus" and "Venus" in sig5:
        love += 14
        rsl.append("KP RuleD: Venus = 7th CSL and signifies 5H — pure romance")

    # KE: 11th CSL signifies 5H + 7H
    if csl11 and csl11 in sig5 and csl11 in sig7:
        love += 16
        rsl.append(f"KP RuleE: 11th CSL ({csl11}) signifies 5H+7H — desire fulfilled via love")

    # KN1: NEGATION — 7th CSL signifies 6/8/12 dominantly
    if csl7:
        bad = sum(1 for s in (sig6, sig8, sig12) if csl7 in s)
        good = sum(1 for s in (sig5, sig7, sig11) if csl7 in s)
        if bad > good and bad >= 2:
            penalty = 25
            love = max(0, love - penalty)
            rsa.append(f"KP NEGATION: 7th CSL ({csl7}) signifies more bad houses (6/8/12) than good — marriage strained")

    # KN2: NEGATION — 5th CSL signifies 6H (breakup before marriage)
    if csl5 and csl5 in sig6:
        love = max(0, love - 12)
        rsa.append(f"KP NEGATION: 5th CSL ({csl5}) signifies 6H — romance breakup risk")

    love = min(100, love)
    arr  = min(100, arr)

    # If no love rules fired AND 7th CSL signifies 7+11 only (not 5),
    # treat as ARRANGED signal.
    if love == 0 and csl7 and csl7 in sig7 and csl7 in sig11 and csl7 not in sig5:
        arr = 60
        rsa.append(f"KP: 7th CSL ({csl7}) signifies 7H+11H without 5H — arranged signature")

    return {
        "name": "KP CSL",
        "love_score": love,
        "arr_score": arr,
        "verdict": _engine_verdict(love, arr),
        "reasons_love": rsl,
        "reasons_arr": rsa,
        "available": True,
    }


# ════════════════════════════════════════════════════════════════════════
# TRUST LAYER 2 — Multi-Engine Consensus
# ════════════════════════════════════════════════════════════════════════

def _engine_verdict(love: int, arr: int) -> str:
    """Single-engine verdict. Returns LOVE / ARRANGED / MIXED / UNKNOWN."""
    if love == 0 and arr == 0:
        return "UNKNOWN"
    if love >= arr + 15:
        return "LOVE"
    if arr >= love + 15:
        return "ARRANGED"
    return "MIXED"


def _consensus_check(engines: list[dict]) -> dict:
    """Trust Layer 2 core. Run consensus voting across 3 engines.

    Returns:
      {
        "consensus":    "STRONG_LOVE" | "LIKELY_LOVE" | "MIXED" |
                        "LIKELY_ARRANGED" | "STRONG_ARRANGED" | "UNCERTAIN",
        "agreement":    "ALL_AGREE" | "MAJORITY" | "SPLIT",
        "boost":        float (multiplier 0.5 .. 1.2),
        "votes_love":   int,
        "votes_arr":    int,
        "votes_mixed":  int,
      }
    """
    votes_love = sum(1 for e in engines if e.get("verdict") == "LOVE")
    votes_arr = sum(1 for e in engines if e.get("verdict") == "ARRANGED")
    votes_mixed = sum(1 for e in engines if e.get("verdict") == "MIXED")
    available = [e for e in engines if e.get("verdict") != "UNKNOWN"]
    n = len(available)

    if n == 0:
        return {"consensus": "UNCERTAIN", "agreement": "SPLIT", "boost": 0.5,
                "votes_love": 0, "votes_arr": 0, "votes_mixed": 0}

    # Strong agreement (all available engines say same thing)
    if votes_love == n:
        return {"consensus": "STRONG_LOVE", "agreement": "ALL_AGREE", "boost": 1.2,
                "votes_love": votes_love, "votes_arr": votes_arr,
                "votes_mixed": votes_mixed}
    if votes_arr == n:
        return {"consensus": "STRONG_ARRANGED", "agreement": "ALL_AGREE", "boost": 1.2,
                "votes_love": votes_love, "votes_arr": votes_arr,
                "votes_mixed": votes_mixed}

    # Majority (2 out of 3)
    if votes_love >= 2 and votes_arr == 0:
        return {"consensus": "LIKELY_LOVE", "agreement": "MAJORITY", "boost": 1.0,
                "votes_love": votes_love, "votes_arr": votes_arr,
                "votes_mixed": votes_mixed}
    if votes_arr >= 2 and votes_love == 0:
        return {"consensus": "LIKELY_ARRANGED", "agreement": "MAJORITY", "boost": 1.0,
                "votes_love": votes_love, "votes_arr": votes_arr,
                "votes_mixed": votes_mixed}

    # Split (love vs arranged disagreement) - honest mixed verdict
    if votes_love > 0 and votes_arr > 0:
        return {"consensus": "MIXED", "agreement": "SPLIT", "boost": 0.7,
                "votes_love": votes_love, "votes_arr": votes_arr,
                "votes_mixed": votes_mixed}

    # Mostly mixed verdicts
    return {"consensus": "MIXED", "agreement": "MAJORITY", "boost": 0.8,
            "votes_love": votes_love, "votes_arr": votes_arr,
            "votes_mixed": votes_mixed}


# ════════════════════════════════════════════════════════════════════════
# TRUST LAYER 3 — 5-Band Confidence Calibration
# ════════════════════════════════════════════════════════════════════════

def _confidence_band(score: int, dominant_side: str) -> dict:
    """Trust Layer 3 core. Translate raw score -> humble verdict band.

    Args:
      score: net dominant-side score (0-100)
      dominant_side: "LOVE" or "ARRANGED" or "MIXED"

    Returns:
      {
        "band":           "STRONG" | "HIGH" | "MODERATE" | "WEAK" | "MIXED",
        "confidence":     0-100,
        "tone_words":     ["definite", "strong tendency", ...],
        "verdict_text":   "Aapki kundli LOVE marriage ka spasht...",
        "verdict_type":   "LOVE" | "ARRANGED" | "MIXED",
      }
    """
    # True MIXED = engines couldn't pick a side
    # Confidence reflects raw score honestly (no floor). Per architect
    # review (2.8.25 R3): floors were inflating certainty under weak data.
    if dominant_side == "MIXED":
        return {
            "band": "MIXED",
            "confidence": min(60, max(0, score)),
            "tone_words": ["dono possible", "situational", "depend karega"],
            "verdict_text": ("Aapki kundli mein LOVE aur ARRANGED dono ke "
                             "elements milte hain — yeh love-cum-arranged "
                             "ka case ho sakta hai. Shayad romance ho, "
                             "lekin family approval bhi mile."),
            "verdict_type": "MIXED",
        }

    side_label = "LOVE" if dominant_side == "LOVE" else "ARRANGED"
    other_label = "arranged" if side_label == "LOVE" else "love"

    if score >= 90:
        return {
            "band": "STRONG", "confidence": min(100, score),
            "tone_words": ["spasht", "clear", "definite"],
            "verdict_text": f"Aapki kundli {side_label} MARRIAGE ka spasht (clear) indication deti hai.",
            "verdict_type": side_label,
        }
    if score >= 75:
        return {
            "band": "HIGH", "confidence": score,
            "tone_words": ["strong tendency", "highly likely", "majority signs"],
            "verdict_text": f"Aapki kundli mein {side_label} marriage ki STRONG TENDENCY hai.",
            "verdict_type": side_label,
        }
    if score >= 60:
        return {
            "band": "MODERATE", "confidence": score,
            "tone_words": ["lean", "tendency", "majority but not all"],
            "verdict_text": (f"Aapki kundli {side_label} side LEAN karti hai, lekin "
                             f"{other_label} ka bhi possibility hai — situation pe depend karega."),
            "verdict_type": side_label,
        }
    # WEAK band — direction is clear but signal is soft.
    # Confidence reflects raw score honestly (no floor). Per architect
    # review (2.8.25 R3).
    return {
        "band": "WEAK", "confidence": max(0, score),
        "tone_words": ["soft lean", "halki tendency", "not strong"],
        "verdict_text": (f"Aapki kundli {side_label} side mild lean dikhati hai, "
                         f"lekin signals strong nahi hain — {other_label} possibility "
                         "ko bhi rule out nahi kar sakte."),
        "verdict_type": side_label,
    }


# ════════════════════════════════════════════════════════════════════════
# PUBLIC API — classify_marriage_type
# ════════════════════════════════════════════════════════════════════════

# Final scoring weights (tuned to favor strongest engine: KP)
_WEIGHTS = {"d1": 0.30, "d9": 0.25, "kp": 0.45}


def classify_marriage_type(kundli: dict, intel: dict, kp: dict,
                           birth: Optional[Any] = None,
                           question: str = "") -> dict:
    """Classify the chart as LOVE vs ARRANGED marriage with calibrated trust.

    Pipeline:
      Trust Layer 1 — parse user question for self-disclosure / tense
      Engines      — run Parashari D1 + D9 Navamsha + KP CSL independently
      Trust Layer 2 — multi-engine consensus check
      Final score  — weighted combine + consensus boost
      Trust Layer 3 — 5-band confidence calibration -> humble verdict

    Returns dict shape:
      {
        "type":         "LOVE" | "ARRANGED" | "MIXED",
        "confidence":   0-100,
        "band":         "STRONG"|"HIGH"|"MODERATE"|"MIXED"|"LOW",
        "verdict_text": "Aapki kundli LOVE...",
        "love_score":   0-100,
        "arr_score":    0-100,
        "engines":      {"d1": {...}, "d9": {...}, "kp": {...}},
        "consensus":    {"consensus": ..., "agreement": ..., "boost": ...},
        "self_disclosure": {"mode": ..., "stated_type": ..., ...},
        "reasons_love": [...],
        "reasons_arr":  [...],
        "mode":         "EXPLAIN"|"VERIFY"|"PREDICT"|"GENERAL",
      }

    Returns {} on missing-data inputs (so __init__ orchestrator falls
    back to LLM-only flow).
    """
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return {}
    if not isinstance(intel, dict):
        intel = {}
    if not isinstance(kp, dict):
        kp = {}

    # ── Trust Layer 1: parse the question ──────────────────────────────
    sd = _detect_self_disclosure(question or "")

    # ── Run 3 engines independently ────────────────────────────────────
    eng_d1 = _engine_parashari_d1(kundli, intel)
    eng_d9 = _engine_d9_navamsha(kundli, intel)
    eng_kp = _engine_kp_csl(kp)

    # ── Trust Layer 2: consensus across 3 engines ──────────────────────
    consensus = _consensus_check([eng_d1, eng_d9, eng_kp])

    # ── Weighted final score (LOVE side and ARR side separately) ──────
    love_combined = (
        eng_d1["love_score"] * _WEIGHTS["d1"]
        + eng_d9["love_score"] * _WEIGHTS["d9"]
        + eng_kp["love_score"] * _WEIGHTS["kp"]
    )
    arr_combined = (
        eng_d1["arr_score"] * _WEIGHTS["d1"]
        + eng_d9["arr_score"] * _WEIGHTS["d9"]
        + eng_kp["arr_score"] * _WEIGHTS["kp"]
    )

    # Apply consensus boost
    boost = consensus.get("boost", 1.0)
    if consensus["consensus"] in ("STRONG_LOVE", "LIKELY_LOVE"):
        love_combined *= boost
    elif consensus["consensus"] in ("STRONG_ARRANGED", "LIKELY_ARRANGED"):
        arr_combined *= boost
    elif consensus["consensus"] == "MIXED":
        # Penalize both sides — honest uncertainty signal
        love_combined *= boost
        arr_combined *= boost

    love_combined = round(min(100, max(0, love_combined)))
    arr_combined  = round(min(100, max(0, arr_combined)))

    # ── Determine dominant side ────────────────────────────────────────
    # Per architect review (2.8.25 R2): when consensus is split (MIXED) or
    # too few engines were available, force MIXED verdict regardless of
    # raw score gap — disagreement MUST surface honestly to devotee, not
    # be hidden behind a weighted-score winner.
    consensus_label = consensus.get("consensus", "UNCERTAIN")
    available_engines = sum(1 for e in (eng_d1, eng_d9, eng_kp)
                            if e.get("verdict") != "UNKNOWN")

    if consensus_label in ("MIXED", "UNCERTAIN") or available_engines < 2:
        dominant = "MIXED"
        dominant_score = max(love_combined, arr_combined)
    elif love_combined >= arr_combined + 12:
        dominant = "LOVE"
        dominant_score = love_combined
    elif arr_combined >= love_combined + 12:
        dominant = "ARRANGED"
        dominant_score = arr_combined
    else:
        dominant = "MIXED"
        dominant_score = max(love_combined, arr_combined)

    # ── Trust Layer 3: confidence band calibration ─────────────────────
    band_info = _confidence_band(dominant_score, dominant)

    # ── Trust Layer 1 application: self-disclosure override ───────────
    # If user already STATED their type, engine MUST honor it.
    if sd["mode"] == "EXPLAIN" and sd["stated_type"]:
        stated = sd["stated_type"]
        # Engine becomes "EXPLAINER" — pulls supporting reasons but never contradicts
        if stated == "LOVE":
            band_info = {
                "band": "EXPLAIN",
                "confidence": max(85, dominant_score if dominant == "LOVE" else 70),
                "tone_words": ["confirm karta hai", "match karta hai"],
                "verdict_text": ("Bilkul, aapki kundli LOVE marriage ke signs deti hai — "
                                 "main bata raha hu KYUN hua."),
                "verdict_type": "LOVE",
            }
            dominant = "LOVE"
        else:
            band_info = {
                "band": "EXPLAIN",
                "confidence": max(85, dominant_score if dominant == "ARRANGED" else 70),
                "tone_words": ["confirm karta hai", "match karta hai"],
                "verdict_text": ("Aapki kundli ARRANGED marriage ke signs deti hai — "
                                 "main bata raha hu KYUN hua."),
                "verdict_type": "ARRANGED",
            }
            dominant = "ARRANGED"

    # ── Aggregate reasons (de-dup) ─────────────────────────────────────
    reasons_love: list = []
    for e in (eng_d1, eng_d9, eng_kp):
        for r in e.get("reasons_love") or []:
            if r not in reasons_love:
                reasons_love.append(r)

    reasons_arr: list = []
    for e in (eng_d1, eng_d9, eng_kp):
        for r in e.get("reasons_arr") or []:
            if r not in reasons_arr:
                reasons_arr.append(r)

    return {
        "type":          dominant,
        "confidence":    band_info["confidence"],
        "band":          band_info["band"],
        "verdict_text":  band_info["verdict_text"],
        "love_score":    love_combined,
        "arr_score":     arr_combined,
        "engines": {
            "d1": eng_d1,
            "d9": eng_d9,
            "kp": eng_kp,
        },
        "consensus":     consensus,
        "self_disclosure": sd,
        "mode":          sd["mode"],
        "reasons_love":  reasons_love,
        "reasons_arr":   reasons_arr,
        "tone_words":    band_info.get("tone_words", []),
    }


__all__ = ["classify_marriage_type"]
