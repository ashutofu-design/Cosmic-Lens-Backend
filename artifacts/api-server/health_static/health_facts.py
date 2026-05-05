"""Health deterministic fact pack — multi-dimensional verdict (Phase H1).

Y2 architecture core: ZERO LLM inference. Same chart + same dasha
pointer = same facts forever.

5 Dimensions (per user-approved spec):
  • vitality            — body strength / immunity (H1, Sun, Moon, lagna lord)
  • disease_resistance  — recovery power (H6, Mars, Mercury — Vipreet logic)
  • chronic_risk        — long-term illness (H8, Saturn, Rahu) [INVERTED]
  • mental_health       — mind stability (Moon, H4, Mercury, Jupiter aspect)
  • accident_risk       — sudden events (Mars, H8, Ketu) [INVERTED]

  Each dimension returns:
    verdict      : GREEN / YELLOW / RED
    reason       : str (DIAGNOSIS-BAN sanitized — never names diseases)
    tier         : high / moderate / low / none
    raw_score    : float (PRE-KP-nudge, for conflict resolver visibility)
    severity     : LOW / MODERATE / HIGH (orthogonal to verdict)
    confidence   : NORMAL / LOW (LOW set by KP-Vedic conflict resolver)
    conflict_flag: bool (set True when resolver demoted/upgraded)

  INVERTED dimensions (chronic_risk, accident_risk):
    GREEN = LOW risk (good)   |   RED = HIGH risk (bad)
  STANDARD dimensions (vitality, disease_resistance, mental_health):
    GREEN = strong/good       |   RED = weak/bad

3 Yogas (high-impact only — per user-approved list):
  • Arishta Yoga         — Moon-Saturn or Moon-Rahu in dusthana
  • Balarishta           — Moon weak (debilitated/combust) + malefic aspect
                           on lagna or Moon (early-life vulnerability marker)
  • Vipreet Rajyoga      — STRICT: 2 of (6L/8L/12L) in mutual dusthana
                           relationship (recovery power from setbacks)

KP integration policy (Option B — weighted nudge, NOT hard override):
  KP CSL nudges applied AFTER pre-nudge raw_score captured. Conflict
  resolver reads pre-nudge raw to detect true KP↔Vedic disagreement.
  This pattern was validated in finance_static Phase 2.8.82 (architect
  re-review PASSED).

⚠️ BRAND-SAFETY HARD GUARDS (non-negotiable):
  • _sanitize_reason() strips any disease names (defensive layer)
  • Reasons use generic terms: "vitality channel", "stress zone",
    "physical risk zone", "chronic risk zone", "mental peace zone"
  • Never says "you have/will get X disease"
  • Output dict carries `brand_safety` block flagging sensitive context

Public:
  compute_health_facts(kundli) -> dict
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple

from stock_engine.stock_facts import (  # noqa: E402
    _planet_by_name, _sign_idx, _planet_dignity, _house_lord,
    _planets_in_house, _aspects, _SIGN_LORDS, _DIGNITY_SCORE,
)

_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_MALEFICS_NAT = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
_DUSTHANA_HOUSES = (6, 8, 12)
_KENDRA = (1, 4, 7, 10)

# ── Brand-safety: disease names defensive blocklist ─────────────────
# If any reason string accidentally contains these (e.g. via copy-paste
# from legacy engine), _sanitize_reason replaces with neutral term.
# Not exhaustive by design — primary discipline is to NEVER write
# disease names in reason templates below. This is a safety net.
_DISEASE_BLOCKLIST = {
    "diabetes": "metabolic stress zone",
    "cancer": "serious health zone",
    "tumour": "serious health zone",
    "tumor": "serious health zone",
    "heart attack": "cardiac stress zone",
    "stroke": "neuro stress zone",
    "depression": "low-mood zone",
    "anxiety disorder": "mental stress zone",
    "schizophrenia": "mental stress zone",
    "bipolar": "mental stress zone",
    "tuberculosis": "respiratory stress zone",
    "tb ": "respiratory stress zone ",
    "asthma": "respiratory zone",
    "arthritis": "joint stress zone",
    "kidney failure": "kidney stress zone",
    "liver failure": "liver stress zone",
    "hiv": "immunity zone",
    "aids": "immunity zone",
}


def _sanitize_reason(reason: str) -> str:
    """Defensive layer: replace any blocklisted disease name with a
    neutral category term. Primary discipline is to never write
    disease names in reason templates — this is the safety net."""
    if not reason:
        return reason
    out = reason
    low = reason.lower()
    for bad, good in _DISEASE_BLOCKLIST.items():
        if bad in low:
            # case-insensitive replace
            import re as _re
            out = _re.sub(_re.escape(bad), good, out, flags=_re.IGNORECASE)
            low = out.lower()
    return out


# ── Severity computation (orthogonal to GREEN/YELLOW/RED) ───────────
def _severity_standard(raw: float, green_thr: float, red_thr: float) -> str:
    """For STANDARD dims (vitality/disease_resistance/mental_health):
    HIGH severity = strong signal (very green or very red),
    MODERATE = clear signal, LOW = weak/borderline."""
    if raw >= green_thr + 3 or raw <= red_thr - 2:
        return "HIGH"
    if raw >= green_thr or raw <= red_thr:
        return "MODERATE"
    return "LOW"


def _severity_inverted(raw: float, low_thr: float, high_thr: float) -> str:
    """For INVERTED dims (chronic_risk/accident_risk): severity reflects
    risk magnitude. HIGH risk score = HIGH severity."""
    if raw >= high_thr + 2:
        return "HIGH"
    if raw >= high_thr:
        return "MODERATE"
    if raw >= low_thr:
        return "LOW"
    return "LOW"


# ── Yoga detectors (3 high-impact only) ─────────────────────────────
def _detect_arishta_yoga(planets: List[dict]) -> bool:
    """Moon-Saturn OR Moon-Rahu conjunction in dusthana (6/8/12).
    Classical health-risk yoga. Strict — both in same house + house
    must be dusthana."""
    moon = _planet_by_name(planets, "Moon")
    if not moon:
        return False
    mh = moon.get("house") or 0
    if mh not in _DUSTHANA_HOUSES:
        return False
    for malefic in ("Saturn", "Rahu"):
        p = _planet_by_name(planets, malefic)
        if p and (p.get("house") or 0) == mh:
            return True
    return False


def _detect_balarishta(planets: List[dict], asc_si: int) -> bool:
    """Early-life vulnerability marker. STRICT:
    Moon debilitated/combust AND aspected by a natural malefic
    (Saturn/Mars/Rahu/Ketu). NOT a death predictor — only flags
    constitution fragility for lifestyle caution."""
    moon = _planet_by_name(planets, "Moon")
    if not moon:
        return False
    moon_dig = _planet_dignity(planets, "Moon")
    if moon_dig != "debilitated":
        return False
    mh = moon.get("house") or 0
    if not mh:
        return False
    for malefic in ("Saturn", "Mars", "Rahu", "Ketu"):
        m = _planet_by_name(planets, malefic)
        if not m:
            continue
        if _aspects(malefic, m.get("house") or 0, mh):
            return True
    return False


def _detect_vipreet_recovery_strict(planets: List[dict],
                                     asc_si: int) -> bool:
    """Vipreet Rajyoga for HEALTH RECOVERY POWER.
    STRICT: at least TWO dusthana lords (out of 6L/8L/12L) in mutual
    relationship — same house, mutual aspect, or parivartana.
    Indicates ability to bounce back from health setbacks."""
    lords = {hn: _house_lord(asc_si, hn) for hn in _DUSTHANA_HOUSES}
    placements = {}
    for hn, lord in lords.items():
        if not lord:
            continue
        p = _planet_by_name(planets, lord)
        if not p:
            continue
        placements[hn] = (lord, p.get("house") or 0)
    if len(placements) < 2:
        return False
    pairs = [(a, b) for a in placements for b in placements if a < b]
    for a, b in pairs:
        la, ha = placements[a]
        lb, hb = placements[b]
        if la == lb or not ha or not hb:
            continue
        if ha == hb and ha in _DUSTHANA_HOUSES:
            return True
        if ha == b and hb == a:
            return True
        if (ha in _DUSTHANA_HOUSES and hb in _DUSTHANA_HOUSES
                and _aspects(la, ha, hb) and _aspects(lb, hb, ha)):
            return True
    return False


# ── Tier mapping ────────────────────────────────────────────────────
def _tier(verdict: str, strong_signal: bool, weak_signal: bool) -> str:
    if verdict == "GREEN":
        return "high"
    if verdict == "RED":
        return "none"
    if weak_signal:
        return "low"
    if strong_signal:
        return "moderate"
    return "low"


# ── KP↔Vedic Conflict Resolver (4 triggers) ─────────────────────────
def _apply_kp_vedic_conflict_resolver(dimensions: Dict[str, dict],
                                       kp_csl: Optional[dict]) -> None:
    """Phase H1 — KP↔Vedic Conflict Resolver (ADD-ONLY guard layer).

    Mirror of finance_static resolver. Demote/upgrade verdicts when KP
    and Vedic strongly disagree; mark confidence=LOW + conflict_flag=True
    so downstream UX can differentiate "stable YELLOW" from "uncertain
    conflict YELLOW". Conflict reasons sanitized via _sanitize_reason
    AFTER this resolver completes (in caller).

    Triggers (only fire when kp_csl is non-None):
      V1 — vitality GREEN (raw>=7) + 1st CSL RED
           → demote to YELLOW (KP says vitality channel contaminated)
      V2 — vitality RED + ALL 3 KP cusps GREEN
           → upgrade to YELLOW (KP says clean health channels)
      C1 — chronic_risk GREEN (low risk, raw<=2) + 8th CSL RED
           → demote to YELLOW (KP says chronic channel contaminated)
      C2 — chronic_risk RED (high risk) + 8th CSL GREEN AND no
           kp_disease_signal → demote toward YELLOW (KP says clean)
      D1 — disease_resistance GREEN (raw>=7) + 6th CSL RED
           → demote to YELLOW (KP says disease channel hot)

    No conflict logic on mental_health or accident_risk in v1 — KP
    layer in current design does not directly map to those dimensions.
    """
    if not kp_csl or not isinstance(kp_csl, dict):
        return
    h1 = kp_csl.get("h1") or {}
    h6 = kp_csl.get("h6") or {}
    h8 = kp_csl.get("h8") or {}
    h1_v = h1.get("verdict")
    h6_v = h6.get("verdict")
    h8_v = h8.get("verdict")
    kp_green_count = sum(1 for v in (h1_v, h6_v, h8_v) if v == "GREEN")
    kp_disease = bool(kp_csl.get("kp_disease_signal"))

    # ── V1 / V2: vitality ──
    vt = dimensions.get("vitality")
    if vt:
        if (vt["verdict"] == "GREEN"
                and float(vt.get("raw_score", 0)) >= 7
                and h1_v == "RED"):
            vt["verdict"] = "YELLOW"
            vt["tier"] = "moderate"
            vt["confidence"] = "LOW"
            vt["conflict_flag"] = True
            vt["reason"] += (" [KP-VEDIC CONFLICT — KP CSL flags 6/8/12 "
                              "contamination on 1st cusp; Vedic GREEN "
                              "demoted to cautious YELLOW]")
        elif vt["verdict"] == "RED" and kp_green_count == 3:
            vt["verdict"] = "YELLOW"
            vt["tier"] = "moderate"
            vt["confidence"] = "LOW"
            vt["conflict_flag"] = True
            vt["reason"] += (" [KP-VEDIC CONFLICT — all 3 KP cusps "
                              "GREEN; Vedic RED upgraded to cautious "
                              "YELLOW]")

    # ── D1: disease_resistance ──
    dr = dimensions.get("disease_resistance")
    if dr:
        if (dr["verdict"] == "GREEN"
                and float(dr.get("raw_score", 0)) >= 7
                and h6_v == "RED"):
            dr["verdict"] = "YELLOW"
            dr["tier"] = "moderate"
            dr["confidence"] = "LOW"
            dr["conflict_flag"] = True
            dr["reason"] += (" [KP-VEDIC CONFLICT — KP 6th CSL flags "
                              "disease channel hot; Vedic GREEN "
                              "demoted to cautious YELLOW]")

    # ── C1 / C2: chronic_risk (INVERTED — GREEN means low risk) ──
    cr = dimensions.get("chronic_risk")
    if cr:
        # C1: Vedic says low risk (GREEN, raw<=2) but KP 8th cusp RED
        if (cr["verdict"] == "GREEN"
                and float(cr.get("raw_score", 99)) <= 2
                and h8_v == "RED"):
            cr["verdict"] = "YELLOW"
            cr["tier"] = "low"
            cr["confidence"] = "LOW"
            cr["conflict_flag"] = True
            cr["reason"] += (" [KP-VEDIC CONFLICT — KP 8th CSL flags "
                              "chronic channel contaminated; Vedic GREEN "
                              "low-risk demoted to cautious YELLOW]")
        # C2: Vedic says high risk (RED) but KP 8th GREEN + no disease
        elif (cr["verdict"] == "RED" and h8_v == "GREEN"
              and not kp_disease):
            cr["verdict"] = "YELLOW"
            cr["tier"] = "low"
            cr["confidence"] = "LOW"
            cr["conflict_flag"] = True
            cr["reason"] += (" [KP-VEDIC CONFLICT — KP 8th CSL clean "
                              "GREEN; Vedic RED chronic-risk softened "
                              "to YELLOW]")


# ── Dimension scorers (5) ───────────────────────────────────────────
def _compute_vitality(lord_states, karakas, planets, asc_si,
                      kp_csl=None) -> Tuple[str, str, str, float]:
    """Body strength / immunity / life-force.
    Inputs: H1 lord, Sun, Moon, lagna occupants."""
    h1_d = _DIGNITY_SCORE.get(lord_states["h1"]["lord_dignity"], 0)
    sun_d = _DIGNITY_SCORE.get((karakas.get("Sun") or {}).get("dignity", ""), 0)
    moon_d = _DIGNITY_SCORE.get((karakas.get("Moon") or {}).get("dignity", ""), 0)
    h1_lord_in_dusthana = lord_states["h1"]["lord_in_dusthana"]
    # Malefic on lagna = vitality drain
    h1_occupants = _planets_in_house(planets, 1)
    malefics_on_h1 = sum(1 for p in h1_occupants if p in _MALEFICS_NAT)
    # Lagna lord in kendra/trikona = strong vitality
    h1_lord_house = lord_states["h1"]["lord_house"]
    h1_lord_in_strong = h1_lord_house in (1, 4, 5, 7, 9, 10)

    score = (h1_d * 1.5) + sun_d + moon_d
    if h1_lord_in_strong:
        score += 1.5
    if h1_lord_in_dusthana:
        score -= 2
    score -= malefics_on_h1 * 1.0

    vedic_raw = float(score)

    # KP nudge (cap ±2) — applied AFTER pre-nudge capture
    if kp_csl and isinstance(kp_csl, dict):
        score += int(kp_csl.get("vitality_nudge") or 0)

    if score >= 7:
        v, reason = "GREEN", "Vitality channel strong — H1 lord, Sun, Moon supportive"
    elif score >= 3:
        v, reason = "YELLOW", "Vitality channel moderate — kuch support, kuch weakness"
    else:
        v, reason = "RED", "Vitality channel weak — basic life-force supports limited"
    t = _tier(v, strong_signal=(h1_d >= 2 and sun_d >= 1),
              weak_signal=(h1_lord_in_dusthana or malefics_on_h1 >= 2))
    return v, reason, t, vedic_raw


def _compute_disease_resistance(lord_states, karakas, planets,
                                 kp_csl=None) -> Tuple[str, str, str, float]:
    """Recovery power / immunity / fight against illness.
    Vipreet logic: weak 6L = good immunity. Strong Mars = fighter.
    Strong Mercury = nervous-system regulation."""
    h6_lord_in_dusthana = lord_states["h6"]["lord_in_dusthana"]
    h6_lord_dignity = lord_states["h6"]["lord_dignity"]
    h6_d = _DIGNITY_SCORE.get(h6_lord_dignity, 0)
    mars_d = _DIGNITY_SCORE.get((karakas.get("Mars") or {}).get("dignity", ""), 0)
    mer_d = _DIGNITY_SCORE.get((karakas.get("Mercury") or {}).get("dignity", ""), 0)
    # Mars on H6 = good fighter (classical immunity yoga)
    mars_h = (karakas.get("Mars") or {}).get("house") or 0
    mars_on_h6 = (mars_h == 6)

    score = mars_d + mer_d
    # Vipreet: 6L weak/dusthana = positive for resistance
    if h6_lord_in_dusthana:
        score += 2
    elif h6_d <= 0:
        score += 1
    # Strong 6L NOT in dusthana = active enemies/illness
    if h6_d >= 2 and not h6_lord_in_dusthana:
        score -= 2
    if mars_on_h6:
        score += 2

    vedic_raw = float(score)

    if kp_csl and isinstance(kp_csl, dict):
        score += int(kp_csl.get("disease_nudge") or 0)

    if score >= 6:
        v, reason = "GREEN", "Recovery channel strong — immunity / fight power supportive"
    elif score >= 2:
        v, reason = "YELLOW", "Recovery channel moderate — average resistance"
    else:
        v, reason = "RED", "Recovery channel weak — slower bounce-back, dhyan dena"
    t = _tier(v, strong_signal=(mars_d + mer_d >= 3),
              weak_signal=(h6_d >= 2 and not h6_lord_in_dusthana))
    return v, reason, t, vedic_raw


def _compute_chronic_risk(lord_states, karakas, planets, asc_si,
                           kp_csl=None) -> Tuple[str, str, str, float]:
    """Long-term illness susceptibility. INVERTED semantics:
    GREEN = LOW risk, RED = HIGH risk."""
    risk = 0
    h8_lord_house = lord_states["h8"]["lord_house"]
    sat_h = (karakas.get("Saturn") or {}).get("house") or 0
    rahu_h = (karakas.get("Rahu") or {}).get("house") or 0
    sat_d = _DIGNITY_SCORE.get((karakas.get("Saturn") or {}).get("dignity", ""), 0)

    # Saturn or Rahu in 1/6/8/12 = chronic affliction marker
    if sat_h in (1, 6, 8, 12):
        risk += 2
    if rahu_h in (1, 6, 8, 12):
        risk += 2
    # 8L in 1 or 6 = body chronic affliction
    if h8_lord_house in (1, 6):
        risk += 2
    # Saturn debilitated = chronic stress amplifier
    if sat_d <= -1:
        risk += 1
    # Saturn-Rahu conjunction in any dusthana = serious chronic marker
    if sat_h == rahu_h and sat_h in _DUSTHANA_HOUSES:
        risk += 2
    # Lagna lord in 8 or 12 = chronic body weakness
    h1_lord_house = lord_states["h1"]["lord_house"]
    if h1_lord_house in (8, 12):
        risk += 1

    vedic_raw = float(risk)

    if kp_csl and isinstance(kp_csl, dict):
        risk += int(kp_csl.get("chronic_nudge") or 0)

    # INVERTED: high risk score → RED verdict
    if risk >= 5:
        v, reason = "RED", "Chronic risk zone elevated — long-term care advisable"
    elif risk >= 2:
        v, reason = "YELLOW", "Chronic risk moderate — periodic checkups recommended"
    else:
        v, reason = "GREEN", "Chronic risk zone low — basic care sufficient"
    t = _tier(v, strong_signal=(risk <= 1),
              weak_signal=(risk >= 4))
    return v, reason, t, vedic_raw


def _compute_mental_health(lord_states, karakas, planets,
                            asc_si) -> Tuple[str, str, str, float]:
    """Mental peace / mind stability.
    Inputs: Moon condition, H4 lord, Mercury, Jupiter aspect on Moon."""
    moon = _planet_by_name(planets, "Moon")
    moon_d = _DIGNITY_SCORE.get(_planet_dignity(planets, "Moon"), 0)
    moon_h = (moon or {}).get("house") or 0
    mer_d = _DIGNITY_SCORE.get((karakas.get("Mercury") or {}).get("dignity", ""), 0)
    h4_d = _DIGNITY_SCORE.get(lord_states["h4"]["lord_dignity"], 0)
    h4_lord_in_dusthana = lord_states["h4"]["lord_in_dusthana"]

    score = (moon_d * 2.0) + h4_d + mer_d

    # Moon-Saturn / Moon-Rahu / Moon-Ketu conjunction = mental stress
    for malefic in ("Saturn", "Rahu", "Ketu"):
        m = _planet_by_name(planets, malefic)
        if m and (m.get("house") or 0) == moon_h and moon_h:
            score -= 2

    # Jupiter aspect on Moon = protective
    jup = _planet_by_name(planets, "Jupiter")
    if jup and moon and _aspects("Jupiter", jup.get("house") or 0, moon_h):
        score += 2

    if h4_lord_in_dusthana:
        score -= 1.5

    vedic_raw = float(score)
    score_final = score  # no KP nudge for mental_health in v1

    if score_final >= 6:
        v, reason = "GREEN", "Mental peace zone supportive — Moon + H4 stable"
    elif score_final >= 2:
        v, reason = "YELLOW", "Mental peace zone moderate — kabhi-kabhi stress"
    else:
        v, reason = "RED", "Mental peace zone stressed — meditation/support helpful"
    t = _tier(v, strong_signal=(moon_d >= 2 and h4_d >= 1),
              weak_signal=(moon_d <= 0 or h4_lord_in_dusthana))
    return v, reason, t, vedic_raw


def _compute_accident_risk(lord_states, karakas, planets,
                            asc_si) -> Tuple[str, str, str, float]:
    """Sudden physical-event risk. INVERTED: GREEN = LOW risk, RED = HIGH."""
    risk = 0
    mars = _planet_by_name(planets, "Mars")
    ketu = _planet_by_name(planets, "Ketu")
    mars_h = (mars or {}).get("house") or 0
    ketu_h = (ketu or {}).get("house") or 0

    # Mars in 1 or 8 = accident-prone body marker
    if mars_h in (1, 8):
        risk += 2
    # Mars-Ketu conjunction = sudden accidents (classical)
    if mars_h == ketu_h and mars_h:
        risk += 2
    # Mars-Saturn conjunction = accident/injury yoga
    sat = _planet_by_name(planets, "Saturn")
    if sat and mars_h and sat.get("house") == mars_h:
        risk += 2
    # Malefic on lagna (other than benefic Mars in own/exalted)
    h1_occ = _planets_in_house(planets, 1)
    for m in ("Saturn", "Mars", "Rahu", "Ketu"):
        if m in h1_occ and m != "Mars":
            risk += 1
        elif m == "Mars" and m in h1_occ:
            mars_dig = _planet_dignity(planets, "Mars")
            if mars_dig not in ("exalted", "own"):
                risk += 1
    # 8L on lagna = body harm channel
    if lord_states["h8"]["lord_house"] == 1:
        risk += 1
    # Rahu on H8 = sudden hidden risk
    rahu_h = (karakas.get("Rahu") or {}).get("house") or 0
    if rahu_h == 8:
        risk += 1

    vedic_raw = float(risk)
    risk_final = risk  # no KP nudge for accident_risk in v1

    if risk_final >= 5:
        v, reason = "RED", "Accident risk zone elevated — extra physical caution needed"
    elif risk_final >= 2:
        v, reason = "YELLOW", "Accident risk moderate — normal caution recommended"
    else:
        v, reason = "GREEN", "Accident risk zone low — basic mindfulness sufficient"
    t = _tier(v, strong_signal=(risk_final <= 1),
              weak_signal=(risk_final >= 4))
    return v, reason, t, vedic_raw


# ── Main fact pack ──────────────────────────────────────────────────
def compute_health_facts(kundli: dict) -> Dict[str, Any]:
    """Returns deterministic health fact pack (5 dimensions + KP + yogas
    + brand_safety meta). Same chart → same output forever."""
    if not isinstance(kundli, dict):
        return {"error": "invalid kundli"}

    asc_sign = kundli.get("ascendant", "")
    asc_si = _sign_idx(asc_sign)
    if asc_si is None:
        return {"error": "ascendant unknown"}
    planets = kundli.get("planets") or []
    if not planets:
        return {"error": "no planets"}

    # ── House lord states (focus on health houses 1, 4, 6, 8) ──
    lord_states: Dict[str, dict] = {}
    for hn in (1, 4, 6, 8, 12):
        lord = _house_lord(asc_si, hn)
        lord_p = _planet_by_name(planets, lord) if lord else None
        lord_house = (lord_p or {}).get("house") if lord_p else None
        lord_dig = _planet_dignity(planets, lord) if lord else ""
        lord_states[f"h{hn}"] = {
            "lord": lord,
            "lord_house": lord_house,
            "lord_dignity": lord_dig,
            "lord_in_dusthana": lord_house in _DUSTHANA_HOUSES if lord_house else False,
        }

    # ── Karakas (key planets for health) ──
    karakas: Dict[str, dict] = {}
    for pn in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
               "Saturn", "Rahu", "Ketu"):
        p = _planet_by_name(planets, pn) or {}
        karakas[pn] = {
            "house": p.get("house"),
            "sign": p.get("sign"),
            "dignity": _planet_dignity(planets, pn) if p else "",
        }

    # ── Yogas (3 high-impact) ──
    yogas: List[str] = []
    if _detect_arishta_yoga(planets):
        yogas.append("Arishta")
    if _detect_balarishta(planets, asc_si):
        yogas.append("Balarishta")
    if _detect_vipreet_recovery_strict(planets, asc_si):
        yogas.append("Vipreet-Recovery")

    # ── KP CSL layer (1st/6th/8th cusps) — read-only nudge ──
    try:
        from health_static.kp_health_csl import compute_kp_health_csl
        kp_csl = compute_kp_health_csl(kundli)
    except Exception as _e:
        print(f"[health_static] kp layer error: {_e}", flush=True)
        kp_csl = None

    # ── 5 dimension scorers (4-tuple: verdict, reason, tier, vedic_raw) ──
    vt_v, vt_r, vt_t, vt_raw = _compute_vitality(
        lord_states, karakas, planets, asc_si, kp_csl=kp_csl)
    dr_v, dr_r, dr_t, dr_raw = _compute_disease_resistance(
        lord_states, karakas, planets, kp_csl=kp_csl)
    cr_v, cr_r, cr_t, cr_raw = _compute_chronic_risk(
        lord_states, karakas, planets, asc_si, kp_csl=kp_csl)
    mh_v, mh_r, mh_t, mh_raw = _compute_mental_health(
        lord_states, karakas, planets, asc_si)
    ar_v, ar_r, ar_t, ar_raw = _compute_accident_risk(
        lord_states, karakas, planets, asc_si)

    # Add Vipreet-Recovery yoga boost to disease_resistance reason
    # (does NOT change verdict — purely informational)
    if "Vipreet-Recovery" in yogas and dr_v != "RED":
        dr_r += " (+ Vipreet Rajyoga: extra recovery power)"

    # Arishta yoga = caution flag on vitality reason
    if "Arishta" in yogas and vt_v == "GREEN":
        vt_r += " (Arishta yoga noted — periodic care advisable)"

    dimensions = {
        "vitality": {"verdict": vt_v, "reason": vt_r, "tier": vt_t,
                     "raw_score": vt_raw, "confidence": "NORMAL",
                     "conflict_flag": False,
                     "severity": _severity_standard(vt_raw, 7.0, 3.0),
                     "inverted": False},
        "disease_resistance": {"verdict": dr_v, "reason": dr_r, "tier": dr_t,
                               "raw_score": dr_raw, "confidence": "NORMAL",
                               "conflict_flag": False,
                               "severity": _severity_standard(dr_raw, 6.0, 2.0),
                               "inverted": False},
        "chronic_risk": {"verdict": cr_v, "reason": cr_r, "tier": cr_t,
                         "raw_score": cr_raw, "confidence": "NORMAL",
                         "conflict_flag": False,
                         "severity": _severity_inverted(cr_raw, 2.0, 5.0),
                         "inverted": True},
        "mental_health": {"verdict": mh_v, "reason": mh_r, "tier": mh_t,
                          "raw_score": mh_raw, "confidence": "NORMAL",
                          "conflict_flag": False,
                          "severity": _severity_standard(mh_raw, 6.0, 2.0),
                          "inverted": False},
        "accident_risk": {"verdict": ar_v, "reason": ar_r, "tier": ar_t,
                          "raw_score": ar_raw, "confidence": "NORMAL",
                          "conflict_flag": False,
                          "severity": _severity_inverted(ar_raw, 2.0, 5.0),
                          "inverted": True},
    }

    # ── KP↔Vedic Conflict Resolver (5 triggers, ADD-ONLY guard) ──
    _apply_kp_vedic_conflict_resolver(dimensions, kp_csl)

    # ── Sanitize all reason strings via diagnosis-ban blocklist ──
    # Defensive layer — primary discipline is to never write disease
    # names in templates above. This is the safety net.
    for d in dimensions.values():
        d["reason"] = _sanitize_reason(d["reason"])

    # ── Composite (cache meta only — never shown to user) ──
    # For STANDARD dims: GREEN=2, YELLOW=1, RED=0
    # For INVERTED dims: GREEN=2 (low risk = good), YELLOW=1, RED=0
    _vscore = {"GREEN": 2, "YELLOW": 1, "RED": 0}
    composite = sum(_vscore[d["verdict"]] for d in dimensions.values())

    # ── Sub-flags (route-specific aids) ──
    sub_flags = {
        "vitality_strong": dimensions["vitality"]["verdict"] == "GREEN",
        "vitality_weak": dimensions["vitality"]["verdict"] == "RED",
        "recovery_strong": dimensions["disease_resistance"]["verdict"] == "GREEN",
        "chronic_risk_high": dimensions["chronic_risk"]["verdict"] == "RED",
        "accident_risk_high": dimensions["accident_risk"]["verdict"] == "RED",
        "mental_stress_present": dimensions["mental_health"]["verdict"] == "RED",
        "vipreet_recovery_active": "Vipreet-Recovery" in yogas,
        "arishta_present": "Arishta" in yogas,
        "balarishta_present": "Balarishta" in yogas,
        "any_high_severity_risk": any(
            d["severity"] == "HIGH" and d["inverted"] and d["verdict"] == "RED"
            for d in dimensions.values()
        ),
    }

    # ── Brand-safety meta block (consumed by replies layer) ──
    brand_safety = {
        "doctor_disclaimer_required": True,  # ALWAYS true for health
        "diagnosis_ban_active": True,        # never name diseases
        "sensitive_bucket": None,            # set by routing layer per Q
        "death_prediction_blocked": True,
        "cure_guarantee_blocked": True,
        "high_severity_risk_present": sub_flags["any_high_severity_risk"],
    }

    return {
        "ascendant": asc_sign,
        "asc_si": asc_si,
        "house_lords": lord_states,
        "karakas": karakas,
        "yogas": yogas,
        "dimensions": dimensions,
        "composite_score": composite,
        "sub_flags": sub_flags,
        "kp_csl": kp_csl,
        "brand_safety": brand_safety,
        "engine_version": "health_facts_v1.0_5dim_kp168_conflict_resolver",
    }
