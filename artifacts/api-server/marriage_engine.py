"""
marriage_engine.py — Deterministic marriage verdict engine.

Replaces AI-decided marriage logic with a pure-Python rule engine that
consumes the already-computed kundli + chart_intelligence + KP outputs
and produces a structured verdict BEFORE the AI is invoked. The AI then
acts purely as a narrator that converts this verdict into Hinglish/Hindi
prose — it MUST NOT change verdict, score, timing, or remedy.

Inputs:
    kundli  : dict from kundli_engine.calculate_kundli (has planets,
              dashas, currentDasha, ascendant, moonSign, divisionalCharts)
    intel   : dict from chart_intelligence.analyze_chart (has dignities,
              house_lords, yogas, mangal_dosh, sade_sati)
    kp      : dict from kp_engine.calculate_kp (has cusps, planets,
              significations)
    birth   : optional dict with at least "gender" so karaka is correct
              ("Venus" for men, "Jupiter" for women).

Output: see assess_marriage().__doc__

Logic priority (matches user-supplied 6-step spec):
    1. KP denial check (7th cusp Sub-Lord vs houses 2/7/11 vs 1/6/10/12)
    2. 7th-lord + Karaka promise
    3. Delay factors (Saturn / Mangal / Sade-Sati / combust)
    4. Next favourable Dasha-Antardasha (DA where MD or AD signifies 2/7/11)
    5. Score (0-100) drives final verdict
    6. D9 7th-lord exposed (true marriage promise per BPHS)

NOTE: Live transit (Jupiter trigger) is not fetched here to keep this
function pure. Caller can attach `transit_trigger` later if available.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS = {
    "Aries": "Mars",      "Taurus": "Venus",     "Gemini": "Mercury",
    "Cancer": "Moon",     "Leo": "Sun",          "Virgo": "Mercury",
    "Libra": "Venus",     "Scorpio": "Mars",     "Sagittarius": "Jupiter",
    "Capricorn": "Saturn","Aquarius": "Saturn",  "Pisces": "Jupiter",
}
DIGNITY_RANK = {
    "debilitated": 0, "enemy-sign": 1, "neutral-sign": 2,
    "friend-sign": 3, "own-sign": 4, "moolatrikona": 5, "exalted": 6,
}
PROMISE_HOUSES = {2, 7, 11}
DENIAL_HOUSES  = {1, 6, 10, 12}

# Day-name → Hindi vaar (for the narration string)
_DAY_HI = {
    "Sunday":    "Ravivar",  "Monday":   "Somvar",   "Tuesday":  "Mangalvar",
    "Wednesday": "Budhvar",  "Thursday": "Guruvar",  "Friday":   "Shukravar",
    "Saturday":  "Shanivar",
}

# One-line emergency fallback (used only if remedies.py is unavailable
# at runtime). The single source of truth is remedies._REMEDY_TABLE.
_FALLBACK_REMEDY = (
    'Hanuman Chalisa daily paath karein — sab grahon ki ashanti shaant karta hai'
)


def _remedy_for_planet(planet: str) -> str:
    """
    Return a one-line marriage-narration remedy string for `planet`, sourced
    VERBATIM from the canonical `remedies._REMEDY_TABLE` (Sprint 5). Single
    source of truth — eliminates the old hard-coded duplicate that diverged
    (e.g. wrong 'Om Shum Shukraya Namah' vs proper BPHS
    'Om Draam Dreem Draum Sah Shukraya Namah').
    """
    try:
        from remedies import _REMEDY_TABLE  # type: ignore
    except Exception:
        return _FALLBACK_REMEDY
    entry = _REMEDY_TABLE.get(planet)
    if not isinstance(entry, dict):
        return _FALLBACK_REMEDY
    mantra   = entry.get("mantra")  or {}
    charity  = entry.get("charity") or []
    trans    = mantra.get("transliteration") or ""
    count    = mantra.get("count") or 108
    day_en   = (mantra.get("day") or "").split(" ")[0]   # "Saturday (or Wednesday)" → "Saturday"
    day_hi   = _DAY_HI.get(day_en, day_en or "is din")
    daan     = (charity[0].lower() if charity else "appropriate items")
    if not trans:
        return _FALLBACK_REMEDY
    return (
        f'{day_hi} ({day_en}) ko {count} baar "{trans}" jaap karein, '
        f'{daan} ka daan'
    )


# Backwards-compatible accessor — anything that used to read REMEDY_BY_PLANET[X]
# now goes through the dynamic lookup so the canonical remedies.py stays the
# single source of truth.
class _RemedyView:
    def get(self, planet, default=None):
        out = _remedy_for_planet(planet) if planet else None
        return out if out else (default if default is not None else _FALLBACK_REMEDY)
    def __getitem__(self, planet):
        return _remedy_for_planet(planet)
    def __contains__(self, planet):
        try:
            from remedies import _REMEDY_TABLE  # type: ignore
            return planet in _REMEDY_TABLE
        except Exception:
            return False

REMEDY_BY_PLANET = _RemedyView()


def _sign_idx(sign_name: Any) -> Optional[int]:
    if not isinstance(sign_name, str):
        return None
    try:
        return SIGNS.index(sign_name.strip().capitalize())
    except ValueError:
        return None


def _maybe_shadbala(kundli: dict, lagna_sign_idx: Optional[int]) -> dict:
    """Lazily compute Shadbala for the 7 classical grahas. Returns {} on any failure."""
    if lagna_sign_idx is None:
        return {}
    try:
        from shadbala import compute_shadbala
        raw = (kundli or {}).get("planets") or []
        # shadbala.py expects each planet dict to have "lon" (float).
        # kundli_engine returns "longitude" — translate without mutating originals.
        planets = []
        for p in raw:
            if not isinstance(p, dict): continue
            lon = p.get("lon", p.get("longitude"))
            if not isinstance(lon, (int, float)): continue
            planets.append({**p, "lon": float(lon)})
        moon = next((p for p in planets if p.get("name") == "Moon"), None)
        sun  = next((p for p in planets if p.get("name") == "Sun"),  None)
        moon_sun_angle = None
        if moon and sun:
            moon_sun_angle = (moon["lon"] - sun["lon"]) % 360.0
        return compute_shadbala(planets, lagna_sign_idx, moon_sun_angle) or {}
    except Exception as e:
        return {"_error": str(e)}


def _shadbala_band(pct: Optional[float]) -> str:
    """Bucket strength_pct into qualitative bands for narration & scoring."""
    if pct is None:
        return "unknown"
    if pct >= 110: return "very-strong"
    if pct >= 90:  return "strong"
    if pct >= 70:  return "moderate"
    if pct >= 50:  return "weak"
    return "very-weak"


def _maybe_jupiter_trigger(kundli: dict,
                           lagna_sign_idx: Optional[int],
                           moon_sign_idx:  Optional[int],
                           dasha_window:   Optional[dict]) -> dict:
    """
    Compute Jupiter transit windows over the next 3 years and (if possible)
    intersect them with the next favourable Maha-Antardasha window to produce
    a tighter "marriage trigger" timing block. Safe-failing — returns {} on error.
    """
    if lagna_sign_idx is None:
        return {}
    try:
        from transit_engine import (
            jupiter_marriage_trigger_windows,
            intersect_window_with_jupiter,
        )
        today = datetime.utcnow()
        jup_windows = jupiter_marriage_trigger_windows(
            lagna_sign_idx, moon_sign_idx, start=today, years_ahead=3)
        # Is Jupiter currently in a trigger sign?
        active = next(
            (w for w in jup_windows
             if datetime.fromisoformat(w["start"]) <= today
             <= datetime.fromisoformat(w["end"])),
            None,
        )
        refined = None
        if dasha_window:
            refined = intersect_window_with_jupiter(dasha_window, jup_windows)
        return {
            "jupiter_active_now": bool(active),
            "active_window":      active,
            "all_windows":        jup_windows,
            "refined_window":     refined,
        }
    except Exception as e:
        return {"_error": str(e)}


def _safe_iso_date(s: str) -> Optional[datetime]:
    if not isinstance(s, str) or not s:
        return None
    try:
        return datetime.fromisoformat(s.split("T")[0])
    except Exception:
        return None


def _significators_of(houses_set: set, sigs: dict) -> set:
    """Set of planet names whose KP significations cover any house in houses_set.
    We use the union of pl + sb_houses + ss_houses (all KP signification levels)."""
    out = set()
    for pname, sig in (sigs or {}).items():
        bag = set(sig.get("pl") or []) | set(sig.get("sb_houses") or []) \
            | set(sig.get("ss_houses") or []) | set(sig.get("sl") or [])
        if bag & houses_set:
            out.add(pname)
    return out


def _next_dasha_window(dashas: list, significators: set, today: datetime) -> Optional[dict]:
    """First (Maha,Antar) pair in the future where MD or AD planet signifies 2/7/11."""
    for md in (dashas or []):
        for ad in (md.get("subDashas") or []):
            ad_end = _safe_iso_date(ad.get("endDate") or "")
            if not ad_end or ad_end < today:
                continue
            mp = md.get("planet"); ap = ad.get("planet")
            if mp in significators or ap in significators:
                start = (ad.get("startDate") or "")[:7]
                end   = (ad.get("endDate") or "")[:7]
                if mp in significators and ap in significators:
                    why = f"both {mp} (Mahadasha) and {ap} (Antardasha) signify houses 2/7/11"
                elif mp in significators:
                    why = f"{mp} (Mahadasha) signifies houses 2/7/11"
                else:
                    why = f"{ap} (Antardasha) signifies houses 2/7/11"
                return {"dasha": f"{mp}-{ap}", "start": start, "end": end, "reason": why}
    return None


def _d9_seventh_lord_info(kundli: dict) -> dict:
    """Return D9 7th-lord placement (Navamsa) — primary classical marriage check."""
    d9 = ((kundli or {}).get("divisionalCharts") or {}).get("D9") or {}
    asc_idx = d9.get("ascendantSignIndex")
    if asc_idx is None:
        return {}
    d9_7_idx  = (int(asc_idx) + 6) % 12
    d9_7_sign = SIGNS[d9_7_idx]
    d9_7_lord = SIGN_LORDS.get(d9_7_sign)
    pl_map = {p.get("name"): p for p in (d9.get("planets") or []) if p.get("name")}
    lord_pos = pl_map.get(d9_7_lord) or {}
    return {
        "d9_7th_sign":  d9_7_sign,
        "d9_7th_lord":  d9_7_lord,
        "d9_lord_sign": lord_pos.get("sign"),
        "d9_lord_house":lord_pos.get("house"),
    }


# ── Phase 2.8.18 — Marriage Focus Block layers ──────────────────────────────
# Six new helpers fill gaps in the per-user A-H spec:
#   A. Per-planet KP YES/NO weighted scan (was: only 7th CSL)
#   D. SAV(H7/H2/H11) bhava strength
#   D. Vargottam check for Venus/Jupiter/Mars/7L
#   D. Argala on H7 verdict
#   F. Saturn current transit aspecting H7 (was: only natal Saturn)
#   H. Spouse description synthesis

# Sign nature lookup (for spouse description)
_SIGN_NATURE = {
    "Aries":       ("movable", "fire",  "masculine"),
    "Taurus":      ("fixed",   "earth", "feminine"),
    "Gemini":      ("dual",    "air",   "masculine"),
    "Cancer":      ("movable", "water", "feminine"),
    "Leo":         ("fixed",   "fire",  "masculine"),
    "Virgo":       ("dual",    "earth", "feminine"),
    "Libra":       ("movable", "air",   "masculine"),
    "Scorpio":     ("fixed",   "water", "feminine"),
    "Sagittarius": ("dual",    "fire",  "masculine"),
    "Capricorn":   ("movable", "earth", "feminine"),
    "Aquarius":    ("fixed",   "air",   "masculine"),
    "Pisces":      ("dual",    "water", "feminine"),
}


def _maybe_sav_marriage(kundli: dict, lagna_sign_idx: Optional[int]) -> dict:
    """Extract SAV bindus for H7 (kalatra), H2 (kutumb), H11 (gains/desires),
    plus H8 (samanya marriage karaka) and H12 (bed pleasures).
    Returns {} or {"_error": str} on failure."""
    if lagna_sign_idx is None:
        return {}
    try:
        from ashtakavarga import compute_ashtakavarga
        av = compute_ashtakavarga(kundli.get("planets") or [], lagna_sign_idx)
        if not av or "sav" not in av:
            return {}
        sav = av["sav"]
        verdicts = av.get("verdicts", {})
        return {
            "h7":  {"value": sav[6],  "band": verdicts.get(7,  "")},
            "h2":  {"value": sav[1],  "band": verdicts.get(2,  "")},
            "h11": {"value": sav[10], "band": verdicts.get(11, "")},
            "h8":  {"value": sav[7],  "band": verdicts.get(8,  "")},
            "h12": {"value": sav[11], "band": verdicts.get(12, "")},
        }
    except Exception as e:
        return {"_error": str(e)}


def _maybe_vargottam_marriage(kundli: dict, seventh_lord: str) -> dict:
    """Vargottam check for marriage-relevant planets: Venus, Jupiter, Mars, 7L.
    A planet is vargottam if its D1 sign equals D9 sign — power doubled.
    Tier from compute_vargottama_matrix:
      truly-powerful = vargottam in 5+ vargas (BPHS — extraordinarily strong)
      vargottam      = D1==D9 specifically (classical marriage definition)
      supported      = >=2 vargas (D1 + 1 other)
      weak           = <2 (treated as no vargottam)
    Returns {} or {"_error": str} on failure."""
    try:
        from divisional_charts import compute_vargottama_matrix
        planets = kundli.get("planets") or []
        if not planets:
            return {}
        matrix = compute_vargottama_matrix(planets, lagna_lon=None) or {}
        if not matrix:
            return {}
        relevant = ["Venus", "Jupiter", "Mars"]
        if seventh_lord and seventh_lord not in relevant:
            relevant.append(seventh_lord)
        out = {}
        for p in relevant:
            info = matrix.get(p) or {}
            vargas = info.get("vargas") or []
            d1_d9  = "D9" in vargas
            count  = len(vargas)
            if count >= 5:
                tier = "truly-powerful"
            elif d1_d9:
                tier = "vargottam"
            elif count >= 2:
                tier = "supported"
            else:
                tier = "weak"
            out[p] = {
                "d1_d9_vargottam": d1_d9,
                "vargas_count":    count,
                "vargas":          vargas,
                "tier":            tier,
            }
        return out
    except Exception as e:
        return {"_error": str(e)}


def _maybe_argala_marriage(kundli: dict, lagna_sign_name: Any) -> dict:
    """Compute Argala / Virodhargala verdict on H7 (kalatra bhava).
    Returns {} or {"_error": str} on failure."""
    try:
        from argala import compute_argala
        argala = compute_argala(kundli.get("planets") or [], lagna_sign_name)
        if not argala:
            return {}
        h7 = argala.get(7) or {}
        return {
            "h7_overall":       h7.get("overall", "NEUTRAL"),
            "h7_benefic_score": h7.get("benefic_score", 0),
            "h7_malefic_score": h7.get("malefic_score", 0),
            "h7_paap_argala":   (h7.get("paap_argala") or {}).get("verdict", ""),
        }
    except Exception as e:
        return {"_error": str(e)}


def _maybe_saturn_transit_h7(lagna_sign_idx: Optional[int]) -> dict:
    """Check whether current Saturn (sidereal) sits in or aspects natal H7.
    Saturn aspects 3rd, 7th, and 10th houses from itself (graha-drishti).
    Returns {} or {"_error": str} on failure."""
    if lagna_sign_idx is None:
        return {}
    try:
        import swisseph as swe  # type: ignore
        from datetime import timezone
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        now = datetime.now(timezone.utc)
        ut  = now.hour + now.minute / 60.0 + now.second / 3600.0
        jd  = swe.julday(now.year, now.month, now.day, ut)
        res, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
        sat_sign_idx = int((res[0] % 360) / 30)
        h7_sign_idx  = (int(lagna_sign_idx) + 6) % 12
        sat_aspect_signs = [
            (sat_sign_idx + 2) % 12,  # 3rd aspect
            (sat_sign_idx + 6) % 12,  # 7th aspect
            (sat_sign_idx + 9) % 12,  # 10th aspect
        ]
        sat_in_h7      = (sat_sign_idx == h7_sign_idx)
        sat_aspects_h7 = (h7_sign_idx in sat_aspect_signs and not sat_in_h7)
        return {
            "saturn_sign_idx":   sat_sign_idx,
            "saturn_sign":       SIGNS[sat_sign_idx],
            "h7_sign":           SIGNS[h7_sign_idx],
            "saturn_in_h7":      sat_in_h7,
            "saturn_aspects_h7": sat_aspects_h7,
            "blocking":          (sat_in_h7 or sat_aspects_h7),
        }
    except Exception as e:
        return {"_error": str(e)}


def _per_planet_kp_scan(sigs: dict, seventh_lord: str) -> dict:
    """Per-planet KP YES/NO classification with weighted scoring.

    Classification (union of NL.pl + sub_lord.sb_houses + ss_houses + sign_lord.sl):
      YES     = signifies houses 2/7/11 only
      NO      = signifies houses 6/8/12 only
      MIXED   = signifies BOTH groups (counted half each in weight)
      NEUTRAL = signifies neither

    Weights (BPHS-aligned for marriage):
      7L              -> 2.0  (highest)
      Venus, Jupiter  -> 1.5  (primary karakas)
      Others          -> 1.0

    Final verdict:
      STRONG-YES   = yes_weighted >= 2x no_weighted AND yes_weighted >= 3
      STRONG-NO    = no_weighted  >= 2x yes_weighted AND no_weighted  >= 3
      TILTED-YES   = yes_weighted > no_weighted
      TILTED-NO    = no_weighted  > yes_weighted
      BALANCED     = otherwise

    Returns {} on empty input or {"_error": str} on internal failure."""
    if not sigs:
        return {}
    try:
        yes_houses = {2, 7, 11}
        no_houses  = {6, 8, 12}

        yes_planets:     list = []
        no_planets:      list = []
        mixed_planets:   list = []
        neutral_planets: list = []
        yes_weighted = 0.0
        no_weighted  = 0.0
        per_planet:  dict = {}

        for pname, sig in (sigs or {}).items():
            if not isinstance(sig, dict):
                continue
            bag = (set(sig.get("pl") or []) | set(sig.get("sb_houses") or [])
                   | set(sig.get("ss_houses") or []) | set(sig.get("sl") or []))
            if not bag:
                continue
            hits_yes = bag & yes_houses
            hits_no  = bag & no_houses

            if pname == seventh_lord:
                w = 2.0
            elif pname in ("Venus", "Jupiter"):
                w = 1.5
            else:
                w = 1.0

            if hits_yes and not hits_no:
                classification = "YES"
                yes_planets.append(pname)
                yes_weighted += w
            elif hits_no and not hits_yes:
                classification = "NO"
                no_planets.append(pname)
                no_weighted  += w
            elif hits_yes and hits_no:
                classification = "MIXED"
                mixed_planets.append(pname)
                yes_weighted += w * 0.5
                no_weighted  += w * 0.5
            else:
                classification = "NEUTRAL"
                neutral_planets.append(pname)

            per_planet[pname] = {
                "classification": classification,
                "weight":         w,
                "hits_yes":       sorted(hits_yes),
                "hits_no":        sorted(hits_no),
            }

        if yes_weighted >= no_weighted * 2 and yes_weighted >= 3:
            verdict = "STRONG-YES"
        elif no_weighted >= yes_weighted * 2 and no_weighted >= 3:
            verdict = "STRONG-NO"
        elif yes_weighted > no_weighted:
            verdict = "TILTED-YES"
        elif no_weighted > yes_weighted:
            verdict = "TILTED-NO"
        else:
            verdict = "BALANCED"

        return {
            "yes_planets":     yes_planets,
            "no_planets":      no_planets,
            "mixed_planets":   mixed_planets,
            "neutral_planets": neutral_planets,
            "yes_weighted":    round(yes_weighted, 2),
            "no_weighted":     round(no_weighted,  2),
            "verdict":         verdict,
            "per_planet":      per_planet,
        }
    except Exception as e:
        return {"_error": str(e)}


def _spouse_description(kundli: dict, intel: dict, d9_info: dict) -> dict:
    """Synthesise structured spouse traits from:
      - 7H sign nature (movable/fixed/dual + element + polarity)
      - 7L placement house (life-area where spouse arrives from)
      - Planets occupying H7
      - A7 (Darapada) sign + lord (perception layer)
      - Venus / Jupiter sign nature (karaka qualities)
      - D9 7H sign + lord (true-marriage chart)

    Returns dict — LLM narrates from these traits. Empty dict on any failure."""
    try:
        out: dict = {}
        house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
        pmap        = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

        seventh = house_lords.get(7) or {}
        seventh_sign = seventh.get("sign") or ""
        if seventh_sign in _SIGN_NATURE:
            nature = _SIGN_NATURE[seventh_sign]
            out["h7_sign"]     = seventh_sign
            out["h7_quality"]  = nature[0]
            out["h7_element"]  = nature[1]
            out["h7_polarity"] = nature[2]

        seventh_lord = seventh.get("lord") or ""
        if seventh_lord:
            sl_pos = pmap.get(seventh_lord) or {}
            out["sl_house"] = sl_pos.get("house")
            out["sl_sign"]  = sl_pos.get("sign")

        occupants = [p.get("name") for p in (kundli.get("planets") or [])
                     if p.get("name") and p.get("house") == 7]
        out["h7_occupants"] = occupants

        # A7 (Darapada) — Jaimini perception layer
        try:
            from jaimini import compute_arudha_padas
            ascendant = kundli.get("ascendant")
            if isinstance(ascendant, dict):
                ascendant = ascendant.get("sign") or ascendant.get("name")
            ar = compute_arudha_padas(kundli.get("planets") or [], ascendant)
            if isinstance(ar, dict):
                a7 = (ar.get("padas") or {}).get("A7") or {}
                if a7:
                    out["a7_sign"] = a7.get("sign")
                    out["a7_lord"] = a7.get("lord")
        except Exception:
            pass

        venus = pmap.get("Venus")   or {}
        jup   = pmap.get("Jupiter") or {}
        if venus.get("sign"):
            out["venus_sign"] = venus["sign"]
            v_nat = _SIGN_NATURE.get(venus["sign"])
            if v_nat: out["venus_nature"] = " ".join(v_nat)
        if jup.get("sign"):
            out["jupiter_sign"] = jup["sign"]
            j_nat = _SIGN_NATURE.get(jup["sign"])
            if j_nat: out["jupiter_nature"] = " ".join(j_nat)

        if d9_info:
            out["d9_7h_sign"] = d9_info.get("d9_7th_sign")
            out["d9_7l"]      = d9_info.get("d9_7th_lord")
            out["d9_7l_sign"] = d9_info.get("d9_lord_sign")

        return out
    except Exception as e:
        return {"_error": str(e)}


def assess_marriage(kundli: dict, intel: dict, kp: dict,
                    birth: Optional[dict] = None) -> dict:
    """
    Returns deterministic marriage verdict:
      {
        "verdict":              str,            # final 1-line verdict
        "marriage_promised":    bool,
        "marriage_denied":      bool,
        "delay":                bool,
        "score":                int 0-100,
        "confidence":           int 0-100,
        "kp_verdict":           "promised"|"denied"|"ambiguous"|"unknown",
        "kp_reason":            str,
        "seventh_lord":         str,
        "seventh_lord_dignity": str,
        "karaka":               "Venus"|"Jupiter",
        "karaka_dignity":       str,
        "reasons_strong":       [str...],
        "reasons_weak":         [str...],
        "delay_reasons":        [str...],
        "current_dasha_supports": bool,
        "current_dasha":        "MD-AD" or "",
        "next_window":          {"dasha", "start", "end", "reason"} or None,
        "d9":                   {"d9_7th_sign","d9_7th_lord","d9_lord_sign","d9_lord_house"} or {},
        "remedy":               str,
        "remedy_for_planet":    str,
        "logic_trace":          [str...],
      }
    """
    intel = intel or {}
    kp    = kp    or {}
    kundli= kundli or {}
    birth = birth or {}
    trace: list[str] = []

    sex_raw   = (birth.get("gender") or "").strip().lower()
    is_female = sex_raw.startswith("f") or sex_raw in ("स्त्री", "महिला")
    karaka    = "Jupiter" if is_female else "Venus"

    dignities    = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    house_lords  = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    pmap         = {p.get("name"): p for p in (kundli.get("planets") or []) if p.get("name")}

    # ── Pre-compute Shadbala (used to weight scoring) ────────────────────────
    asc_name      = (kundli.get("ascendant") or "").strip().capitalize()
    moon_name     = (kundli.get("moonSign") or "").strip().capitalize()
    lagna_idx     = _sign_idx(asc_name)
    moon_idx      = _sign_idx(moon_name)
    shad          = _maybe_shadbala(kundli, lagna_idx)
    if shad and "_error" not in shad:
        trace.append(
            "Shadbala computed: " + ", ".join(
                f"{p}={shad[p]['strength_pct']}%" for p in shad if isinstance(shad.get(p), dict)
            )
        )
    elif shad.get("_error"):
        trace.append(f"Shadbala unavailable: {shad['_error']}")

    def _sb(planet: str) -> Optional[float]:
        d = shad.get(planet) if isinstance(shad, dict) else None
        if not isinstance(d, dict):
            return None
        v = d.get("strength_pct")
        return float(v) if isinstance(v, (int, float)) else None

    # ── 7th lord placement & strength ────────────────────────────────────────
    seventh         = house_lords.get(7) or {}
    seventh_lord    = seventh.get("lord") or ""
    sl_dig_entry    = dignities.get(seventh_lord) or {}
    sl_dig          = sl_dig_entry.get("dignity") or "neutral-sign"
    sl_combust      = bool(sl_dig_entry.get("combust"))
    sl_house        = (pmap.get(seventh_lord) or {}).get("house")
    trace.append(f"7th lord = {seventh_lord} ({sl_dig}, house {sl_house}, combust={sl_combust})")

    # ── Karaka strength ──────────────────────────────────────────────────────
    kar_entry = dignities.get(karaka) or {}
    kar_dig   = kar_entry.get("dignity") or "neutral-sign"
    kar_combust = bool(kar_entry.get("combust"))
    trace.append(f"Karaka {karaka} = {kar_dig}, combust={kar_combust}")

    # ── STEP 1: KP DENIAL CHECK ──────────────────────────────────────────────
    kp_verdict = "unknown"
    kp_reason  = ""
    sb_lord    = ""
    sigs       = (kp.get("significations") or {})
    cusp7      = next((c for c in (kp.get("cusps") or []) if c.get("house") == 7), None)
    if cusp7 and isinstance(cusp7, dict):
        sb_lord = cusp7.get("sb") or ""
        sl_sigs = sigs.get(sb_lord) or {}
        # Use the strongest signification source: sub-lord's own signified houses
        sl_houses = set(sl_sigs.get("sb_houses") or sl_sigs.get("pl") or [])
        promise_hit = sl_houses & PROMISE_HOUSES
        denial_hit  = sl_houses & DENIAL_HOUSES
        if promise_hit:
            kp_verdict = "promised"
            kp_reason  = (f"7th cusp Sub-Lord {sb_lord} signifies houses "
                          f"{sorted(promise_hit)} (out of 2/7/11) — marriage PROMISED in KP")
        elif denial_hit and not promise_hit:
            kp_verdict = "denied"
            kp_reason  = (f"7th cusp Sub-Lord {sb_lord} signifies only houses "
                          f"{sorted(denial_hit)} (1/6/10/12) — marriage faces DENIAL or long delay")
        else:
            kp_verdict = "ambiguous"
            kp_reason  = (f"7th cusp Sub-Lord {sb_lord} signifies "
                          f"{sorted(sl_houses) or 'no clear set of'} houses — KP verdict ambiguous")
    trace.append(f"KP verdict = {kp_verdict} | {kp_reason}")

    # ── STEP 3: DELAY FACTORS ────────────────────────────────────────────────
    delay_reasons: list[str] = []
    mangal_str = intel.get("mangal_dosh") or ""
    if "present" in mangal_str.lower():
        delay_reasons.append(f"Mangal-dosh active ({mangal_str})")
    sade = intel.get("sade_sati") or ""
    if sade:
        delay_reasons.append(f"Sade-Sati phase running ({sade})")
    sat_entry   = dignities.get("Saturn") or {}
    sat_aspects = sat_entry.get("aspects_houses") or []
    sat_house   = (pmap.get("Saturn") or {}).get("house")
    if sat_house == 7 or 7 in sat_aspects:
        delay_reasons.append(f"Saturn aspects/occupies 7th house (sat_house={sat_house}, aspects={sat_aspects})")
    if sl_combust:
        delay_reasons.append(f"7th lord {seventh_lord} combust by Sun")
    if kar_dig in ("debilitated", "enemy-sign") and not kar_combust:
        delay_reasons.append(f"{karaka} (kalatra-karaka) weak ({kar_dig})")
    elif kar_combust:
        delay_reasons.append(f"{karaka} (kalatra-karaka) combust")
    delay = bool(delay_reasons)
    trace.append(f"Delay factors ({len(delay_reasons)}): {delay_reasons}")

    # ── STEP 4: NEXT FAVOURABLE DASHA WINDOW ─────────────────────────────────
    significators_271 = _significators_of(PROMISE_HOUSES, sigs)
    trace.append(f"Planets signifying 2/7/11 (KP): {sorted(significators_271)}")

    cur_dasha = (kundli.get("currentDasha") or {})
    cur_md    = cur_dasha.get("maha") or ""
    cur_ad    = cur_dasha.get("antar") or ""
    current_supports = bool((cur_md and cur_md in significators_271)
                            or (cur_ad and cur_ad in significators_271))
    today = datetime.utcnow()
    next_window = _next_dasha_window(kundli.get("dashas") or [],
                                     significators_271, today)
    trace.append(f"Current Dasha {cur_md}-{cur_ad} supports = {current_supports}")
    trace.append(f"Next favourable window: {next_window}")

    # ── JUPITER TRANSIT TRIGGER ──────────────────────────────────────────────
    # Compute Jupiter's transit windows over 1/5/7 from Lagna and from Moon.
    # Intersect with the next favourable Dasha-Antardasha window. The
    # intersection is the *tight* marriage trigger band — strongest classical
    # timing combination (dasha + transit synchronisation, BPHS principle).
    jup_trig = _maybe_jupiter_trigger(kundli, lagna_idx, moon_idx, next_window)
    if jup_trig and "_error" not in jup_trig:
        trace.append(f"Jupiter active now: {jup_trig.get('jupiter_active_now')} "
                     f"({jup_trig.get('active_window')})")
        if jup_trig.get("refined_window"):
            rw_block = jup_trig["refined_window"]
            trace.append(f"Refined trigger window (dasha ∩ Jupiter transit): "
                         f"{rw_block['start']} → {rw_block['end']} "
                         f"via {rw_block.get('jupiter_hits')}")
            # Promote refined window into next_window for narration
            if next_window is not None:
                next_window = dict(next_window)
                next_window["refined_start"]  = rw_block["start"][:7]
                next_window["refined_end"]    = rw_block["end"][:7]
                next_window["jupiter_hits"]   = rw_block.get("jupiter_hits")
                next_window["jupiter_sign"]   = rw_block.get("jupiter_sign")
                next_window["reason"] = (
                    next_window.get("reason", "") +
                    f" + Jupiter transits {rw_block.get('jupiter_sign')} "
                    f"(hits {rw_block.get('jupiter_hits')}) during this period"
                )
        elif next_window:
            trace.append("No Jupiter ∩ Dasha intersection — dasha window stays as-is")
    elif jup_trig.get("_error"):
        trace.append(f"Jupiter transit unavailable: {jup_trig['_error']}")

    # ── NEXT-AFTER WINDOW (constraint-aware follow-up) ───────────────────────
    # If the devotee rejects the primary window ("yeh time nahi chahiye / next
    # year batao"), we must hand back a SECOND deterministic window — never
    # let the AI guess. We re-scan dashas starting AFTER next_window.end and
    # apply the same Jupiter-trigger refinement.
    next_alt_window = None
    if next_window and next_window.get("end"):
        try:
            end_ym = next_window["end"]                     # "YYYY-MM"
            after_dt = datetime.strptime(end_ym + "-28", "%Y-%m-%d") + timedelta(days=5)
            cand = _next_dasha_window(kundli.get("dashas") or [],
                                      significators_271, after_dt)
            if cand:
                jt2 = _maybe_jupiter_trigger(kundli, lagna_idx, moon_idx, cand)
                if jt2 and "_error" not in jt2 and jt2.get("refined_window"):
                    rw2 = jt2["refined_window"]
                    cand = dict(cand)
                    cand["refined_start"] = rw2["start"][:7]
                    cand["refined_end"]   = rw2["end"][:7]
                    cand["jupiter_hits"]  = rw2.get("jupiter_hits")
                    cand["jupiter_sign"]  = rw2.get("jupiter_sign")
                    cand["reason"] = (
                        cand.get("reason", "") +
                        f" + Jupiter transits {rw2.get('jupiter_sign')} "
                        f"(hits {rw2.get('jupiter_hits')}) during this period"
                    )
                next_alt_window = cand
                trace.append(f"Next-after-primary window: {next_alt_window}")
        except Exception as exc:
            trace.append(f"next_alt_window scan failed: {exc}")

    # ── PHASE 2.8.18 helper invocations (focus block layers) ────────────────
    # Compute the 6 new layers BEFORE scoring so their findings can adjust
    # the score, but after KP / dasha / Jupiter trigger so the per-planet
    # KP scan and saturn-transit checks see all dependencies.
    sav_marr      = _maybe_sav_marriage(kundli, lagna_idx)
    vargottam_m   = _maybe_vargottam_marriage(kundli, seventh_lord)
    argala_h7     = _maybe_argala_marriage(kundli, asc_name)
    saturn_trans  = _maybe_saturn_transit_h7(lagna_idx)
    kp_per_planet = _per_planet_kp_scan(sigs, seventh_lord)
    if sav_marr and "_error" not in sav_marr:
        trace.append(f"SAV: H7={sav_marr.get('h7',{}).get('value')}({sav_marr.get('h7',{}).get('band')}), "
                     f"H2={sav_marr.get('h2',{}).get('value')}, H11={sav_marr.get('h11',{}).get('value')}")
    elif sav_marr.get("_error"):
        trace.append(f"SAV unavailable: {sav_marr['_error']}")
    if vargottam_m and "_error" not in vargottam_m:
        vg_hits = [p for p, info in vargottam_m.items() if isinstance(info, dict) and info.get("d1_d9_vargottam")]
        if vg_hits:
            trace.append(f"Vargottam (D1=D9): {vg_hits}")
    if argala_h7 and "_error" not in argala_h7:
        trace.append(f"Argala on H7: {argala_h7.get('h7_overall')} (B={argala_h7.get('h7_benefic_score')}, M={argala_h7.get('h7_malefic_score')})")
    if saturn_trans and "_error" not in saturn_trans and saturn_trans.get("blocking"):
        why = "in" if saturn_trans.get("saturn_in_h7") else "aspecting"
        trace.append(f"Saturn currently {why} natal H7 — commitment-check transit ACTIVE")
    if kp_per_planet:
        trace.append(f"KP per-planet: {kp_per_planet.get('verdict')} "
                     f"(YES={kp_per_planet.get('yes_planets')}, NO={kp_per_planet.get('no_planets')}, "
                     f"weighted yes={kp_per_planet.get('yes_weighted')} vs no={kp_per_planet.get('no_weighted')})")

    # ── STEP 5: SCORING ──────────────────────────────────────────────────────
    score = 50
    rs: list[str] = []
    rw: list[str] = []

    # 7th lord
    if sl_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 20
        rs.append(f"7th lord {seventh_lord} {sl_dig} — strong kalatra-bhava")
    elif sl_dig in ("debilitated", "enemy-sign") and not sl_combust:
        score -= 10
        rw.append(f"7th lord {seventh_lord} {sl_dig} — kalatra-bhava weak")
    if sl_combust:
        score -= 8
        rw.append(f"7th lord {seventh_lord} combust by Sun")

    # Karaka
    if kar_dig in ("exalted", "moolatrikona", "own-sign"):
        score += 15
        rs.append(f"{karaka} (kalatra-karaka) {kar_dig}")
    elif kar_dig in ("debilitated", "enemy-sign") and not kar_combust:
        score -= 10
        rw.append(f"{karaka} (kalatra-karaka) {kar_dig}")
    if kar_combust:
        score -= 8
        rw.append(f"{karaka} combust")

    # KP verdict
    if kp_verdict == "promised":
        score += 15; rs.append(kp_reason)
    elif kp_verdict == "denied":
        score -= 20; rw.append(kp_reason)

    # ── SHADBALA-WEIGHTED REFINEMENT ─────────────────────────────────────────
    # Classical Parashari Shadbala: a planet that meets/exceeds its required
    # virupa minimum is a *karyakarta* (capable of producing the result of
    # the houses it owns/aspects). For marriage, the three planets that
    # MUST be capable of producing the result are: 7th lord, kalatra-karaka
    # (Venus or Jupiter by gender), and Jupiter (kalyana karaka — universal
    # benefic for shubh-karya). We amplify each planet's existing score
    # contribution by its strength_pct band.
    sb_7l   = _sb(seventh_lord)
    sb_kar  = _sb(karaka)
    sb_jup  = _sb("Jupiter")
    sb_breakdown = {
        seventh_lord: {"pct": sb_7l,  "band": _shadbala_band(sb_7l)},
        karaka:       {"pct": sb_kar, "band": _shadbala_band(sb_kar)},
        "Jupiter":    {"pct": sb_jup, "band": _shadbala_band(sb_jup)},
    }

    def _apply_sb(label: str, pct: Optional[float]):
        nonlocal score
        if pct is None:
            return
        if pct >= 110:
            score += 6
            rs.append(f"{label} Shadbala very-strong ({pct:.0f}% of required) — full karyakarta")
        elif pct >= 90:
            score += 3
            rs.append(f"{label} Shadbala strong ({pct:.0f}%) — capable of producing marriage result")
        elif pct < 70 and pct >= 50:
            score -= 3
            rw.append(f"{label} Shadbala weak ({pct:.0f}% of required minimum)")
        elif pct < 50:
            score -= 6
            rw.append(f"{label} Shadbala very-weak ({pct:.0f}%) — struggles to deliver marriage karya")

    _apply_sb(f"7th lord {seventh_lord}", sb_7l)
    _apply_sb(f"Karaka {karaka}",         sb_kar)
    # Jupiter (kalyana karaka) gets a smaller weight — only the boost half
    if sb_jup is not None:
        if sb_jup >= 110:
            score += 4
            rs.append(f"Jupiter (kalyana karaka) Shadbala very-strong ({sb_jup:.0f}%) — universal benefic at full power")
        elif sb_jup >= 90:
            score += 2
            rs.append(f"Jupiter (kalyana karaka) Shadbala strong ({sb_jup:.0f}%)")
        elif sb_jup < 50:
            score -= 3
            rw.append(f"Jupiter very-weak ({sb_jup:.0f}%) — shubh-karya support reduced")

    # Marriage-supportive yogas
    yogas = intel.get("yogas") or []
    marr_yogas = [y for y in yogas if isinstance(y, str) and any(
        t in y.lower() for t in ("raja", "gajakesari", "budhaditya",
                                 "mahapurusha", "neech-bhanga", "malavya"))]
    if marr_yogas:
        score += min(10, 4 * len(marr_yogas))
        rs.extend(marr_yogas)

    # Delay penalty
    if delay_reasons:
        penalty = min(20, 6 * len(delay_reasons))
        score -= penalty
        rw.extend(delay_reasons)

    # Current dasha supports → small boost
    if current_supports:
        score += 5
        rs.append(f"Current Dasha {cur_md}-{cur_ad} signifies 2/7/11 (window OPEN)")

    # ── PHASE 2.8.18: Score adjustments from focus-block layers ─────────────
    # SAV(H7) — declared spec: H7 value >=28 → +5, <=18 → -8
    if sav_marr and isinstance(sav_marr.get("h7"), dict):
        h7_val_raw = sav_marr["h7"].get("value")
        try:
            h7_val = int(h7_val_raw)
        except (TypeError, ValueError):
            h7_val = None
        if h7_val is not None:
            if h7_val >= 28:
                score += 5; rs.append(f"SAV(H7)={h7_val} — STRONG kalatra bhava (>=28)")
            elif h7_val <= 18:
                score -= 8; rw.append(f"SAV(H7)={h7_val} — WEAK kalatra bhava (<=18)")
    # Vargottam (D1=D9) for marriage planets — cap +6 total; weak D1!=D9 with 0 hits → -2 each
    if vargottam_m and "_error" not in vargottam_m:
        vg_bonus = 0
        for p, info in vargottam_m.items():
            if not isinstance(info, dict):
                continue
            if info.get("d1_d9_vargottam"):
                vg_bonus += 3
                rs.append(f"{p} vargottam (D1=D9) — power doubled in marriage")
            elif info.get("tier") == "weak":
                score -= 2
                rw.append(f"{p} weak in vargas (no vargottam, <2 vargas) — kalatra-karyakarta dispersed")
        score += min(vg_bonus, 6)
    # Argala on H7 — declared: STRONG-BENEFIC +4, MILD-BENEFIC +2, MIXED -3, MILD-MALEFIC -3, STRONG-MALEFIC -5
    if argala_h7 and isinstance(argala_h7, dict):
        ov = argala_h7.get("h7_overall")
        if ov == "STRONG-BENEFIC":
            score += 4; rs.append("Argala on H7: STRONG-BENEFIC — kalatra-bhava well-supported")
        elif ov == "MILD-BENEFIC":
            score += 2; rs.append("Argala on H7: MILD-BENEFIC — mild benefic support")
        elif ov == "MIXED":
            score -= 3; rw.append("Argala on H7: MIXED — divided support")
        elif ov == "MILD-MALEFIC":
            score -= 3; rw.append("Argala on H7: MILD-MALEFIC — minor obstruction on kalatra-bhava")
        elif ov == "STRONG-MALEFIC":
            score -= 5; rw.append("Argala on H7: STRONG-MALEFIC — kalatra-bhava under malefic pressure")
    # Saturn current transit on H7 (separate from natal — the second of the
    # double-transit pair; Jupiter handled by _maybe_jupiter_trigger above)
    if saturn_trans and saturn_trans.get("blocking"):
        score -= 4
        why = "currently in" if saturn_trans.get("saturn_in_h7") else "currently aspecting"
        delay_reasons.append(f"Saturn {why} natal H7 ({saturn_trans.get('saturn_sign')}) — commitment-check transit active")
    # KP per-planet weighted scan
    if kp_per_planet and kp_per_planet.get("verdict"):
        v = kp_per_planet["verdict"]
        if v == "STRONG-YES":
            score += 6
            rs.append(f"KP per-planet scan STRONG-YES (weighted yes={kp_per_planet['yes_weighted']} vs no={kp_per_planet['no_weighted']})")
        elif v == "TILTED-YES":
            score += 2
            rs.append(f"KP per-planet scan TILTED-YES (yes={kp_per_planet['yes_weighted']} vs no={kp_per_planet['no_weighted']})")
        elif v == "STRONG-NO":
            score -= 8
            rw.append(f"KP per-planet scan STRONG-NO (weighted no={kp_per_planet['no_weighted']} vs yes={kp_per_planet['yes_weighted']})")
        elif v == "TILTED-NO":
            score -= 3
            rw.append(f"KP per-planet scan TILTED-NO (no={kp_per_planet['no_weighted']} vs yes={kp_per_planet['yes_weighted']})")

    score = max(0, min(100, score))

    # ── VERDICT ──────────────────────────────────────────────────────────────
    if kp_verdict == "denied" and score < 45:
        verdict = "Vivah mein gehre rukawat / denial — extensive remedies zaroori"
        promised, denied = False, True
    elif score >= 75:
        verdict = ("Vivah strongly promised" + (" — thodi der ho sakti hai" if delay else ""))
        promised, denied = True, False
    elif score >= 55:
        verdict = ("Vivah promised — delay ke saath" if delay else "Vivah promised")
        promised, denied = True, False
    elif score >= 40:
        verdict = "Vivah sambhav hai par challenges hain — upay ke saath"
        promised, denied = True, False
    else:
        verdict = "Vivah mein significant rukawat — gambhir upay aur dharma-paalan zaroori"
        promised, denied = (kp_verdict != "denied"), (kp_verdict == "denied")

    # Confidence: based on data completeness + score conviction.
    # Shadbala + Jupiter trigger materially raise the conviction since they
    # add two independent classical confirmations (strength + transit).
    data_bonus = 0
    if kp_verdict in ("promised", "denied"): data_bonus += 15
    if next_window:                          data_bonus += 10
    if seventh_lord and sl_dig:              data_bonus += 5
    if (intel.get("dignities") or []):       data_bonus += 5
    if shad and "_error" not in shad and len(shad) >= 5:
        data_bonus += 5                       # Shadbala available
    if jup_trig and (jup_trig.get("refined_window")
                     or jup_trig.get("jupiter_active_now")):
        data_bonus += 5                       # Jupiter trigger present
    # PHASE 2.8.18: single +5 confidence bonus iff ALL 4 focus-block helpers ran clean.
    # (kp_per_planet is treated as bonus data, not gated — it depends on KP availability.)
    focus_helpers_clean = (
        bool(sav_marr)     and "_error" not in sav_marr     and bool(sav_marr.get("h7"))
        and bool(vargottam_m) and "_error" not in vargottam_m and len(vargottam_m) > 0
        and bool(argala_h7)   and "_error" not in argala_h7   and bool(argala_h7.get("h7_overall"))
        and bool(saturn_trans) and "_error" not in saturn_trans
    )
    if focus_helpers_clean:
        data_bonus += 5
    confidence = min(97, 50 + data_bonus + abs(score - 50) // 4)

    # ── D9 NAVAMSA ───────────────────────────────────────────────────────────
    d9_info = _d9_seventh_lord_info(kundli)
    if d9_info:
        trace.append(f"D9 7th lord = {d9_info.get('d9_7th_lord')} in {d9_info.get('d9_lord_sign')} (D9 house {d9_info.get('d9_lord_house')})")

    # ── PHASE 2.8.18: SPOUSE DESCRIPTION SYNTHESIS ──────────────────────────
    spouse_desc = _spouse_description(kundli, intel, d9_info)
    if spouse_desc:
        trace.append(f"Spouse-desc synthesised: 7H={spouse_desc.get('h7_sign')}/"
                     f"{spouse_desc.get('h7_quality')}/{spouse_desc.get('h7_element')}, "
                     f"7L in H{spouse_desc.get('sl_house')}, "
                     f"A7={spouse_desc.get('a7_sign')}, D9-7H={spouse_desc.get('d9_7h_sign')}")

    # ── REMEDY: pick weakest among (7L, karaka) ──────────────────────────────
    candidates = []
    if seventh_lord:
        candidates.append((seventh_lord, sl_dig, sl_combust))
    candidates.append((karaka, kar_dig, kar_combust))
    # Choose weakest by dignity-rank, combust pushes down
    def weak_score(c):
        name, dig, comb = c
        return DIGNITY_RANK.get(dig, 2) - (3 if comb else 0)
    weakest_planet = min(candidates, key=weak_score)[0]
    remedy = REMEDY_BY_PLANET.get(weakest_planet) or REMEDY_BY_PLANET["Venus"]

    return {
        "verdict":              verdict,
        "marriage_promised":    promised,
        "marriage_denied":      denied,
        "delay":                delay,
        "score":                int(score),
        "confidence":           int(confidence),
        "kp_verdict":           kp_verdict,
        "kp_reason":            kp_reason,
        "seventh_lord":         seventh_lord,
        "seventh_lord_dignity": sl_dig,
        "karaka":               karaka,
        "karaka_dignity":       kar_dig,
        "reasons_strong":       rs,
        "reasons_weak":         rw,
        "delay_reasons":        delay_reasons,
        "current_dasha_supports": current_supports,
        "current_dasha":        f"{cur_md}-{cur_ad}".strip("-"),
        "next_window":          next_window,
        "next_alt_window":      next_alt_window,
        "d9":                   d9_info,
        "remedy":               remedy,
        "remedy_for_planet":    weakest_planet,
        "shadbala":             sb_breakdown,
        "jupiter_trigger":      jup_trig,
        # ── Phase 2.8.18 focus-block layers ─────────────────────────────────
        "sav_marriage":         sav_marr,
        "vargottam_marriage":   vargottam_m,
        "argala_h7":            argala_h7,
        "saturn_transit_h7":    saturn_trans,
        "kp_per_planet":        kp_per_planet,
        "spouse_description":   spouse_desc,
        "logic_trace":          trace,
    }


def _shad_line(v: dict) -> str:
    sb = v.get("shadbala") or {}
    if not sb:
        return ""
    parts = []
    for planet, info in sb.items():
        if not isinstance(info, dict): continue
        pct  = info.get("pct")
        band = info.get("band")
        if pct is None: continue
        parts.append(f"{planet}={pct:.0f}% ({band})")
    if not parts:
        return ""
    return "  Shadbala (planet karyakarta strength): " + ", ".join(parts) + "\n"


def _jup_line(v: dict) -> str:
    jt = v.get("jupiter_trigger") or {}
    if not jt or jt.get("_error"):
        return ""
    out = ""
    if jt.get("jupiter_active_now") and jt.get("active_window"):
        aw = jt["active_window"]
        out += (f"  Jupiter currently transiting {aw.get('sign')} "
                f"(hits {aw.get('hits')}) until {aw.get('end')}\n")
    rw = jt.get("refined_window")
    if rw:
        out += (f"  Refined trigger band (Dasha ∩ Jupiter): "
                f"{rw.get('start')} → {rw.get('end')} "
                f"via Jupiter in {rw.get('jupiter_sign')} {rw.get('jupiter_hits')}\n")
    return out


def _focus_block_lines(v: dict) -> str:
    """Phase 2.8.18 — render the 6 new focus-block layers as a compact section
    inside the AUTHORITATIVE MARRIAGE VERDICT block. All values come straight
    from assess_marriage(); LLM treats them as locked facts (Rule O applies)."""
    if not v:
        return ""
    lines: list[str] = []

    # ── Layer A: Per-planet KP YES/NO scan ──────────────────────────────────
    kpp = v.get("kp_per_planet") or {}
    if kpp and kpp.get("verdict"):
        yes_p = kpp.get("yes_planets") or []
        no_p  = kpp.get("no_planets")  or []
        mix_p = kpp.get("mixed_planets") or []
        lines.append(
            "  KP per-planet scan: {0} (weighted YES={1} vs NO={2})".format(
                kpp.get("verdict"), kpp.get("yes_weighted"), kpp.get("no_weighted")
            )
        )
        lines.append("    YES (signifies 2/7/11): " + (str(yes_p) if yes_p else "none"))
        lines.append("    NO  (signifies 6/8/12): " + (str(no_p) if no_p else "none"))
        if mix_p:
            lines.append("    MIXED (both groups): " + str(mix_p))

    # ── Layer D: SAV (H7/H2/H11) ────────────────────────────────────────────
    sav = v.get("sav_marriage") or {}
    if sav and "_error" not in sav:
        h7  = sav.get("h7")  or {}
        h2  = sav.get("h2")  or {}
        h11 = sav.get("h11") or {}
        h8  = sav.get("h8")  or {}
        h12 = sav.get("h12") or {}
        lines.append(
            "  Sarvashtakavarga (marriage houses): "
            "H7={0}({1}), H2={2}({3}), H11={4}({5}), H8={6}, H12={7}".format(
                h7.get("value"), h7.get("band"),
                h2.get("value"), h2.get("band"),
                h11.get("value"), h11.get("band"),
                h8.get("value"), h12.get("value"),
            )
        )

    # ── Layer D: Vargottam check ────────────────────────────────────────────
    vg = v.get("vargottam_marriage") or {}
    if vg and "_error" not in vg:
        parts: list[str] = []
        for p, info in vg.items():
            if not isinstance(info, dict):
                continue
            tier  = info.get("tier", "weak")
            d1d9  = "vargottam" if info.get("d1_d9_vargottam") else "no"
            count = info.get("vargas_count", 0)
            parts.append("{0}={1}({2}v, D1-D9:{3})".format(p, tier, count, d1d9))
        if parts:
            lines.append("  Vargottam (marriage planets): " + ", ".join(parts))

    # ── Layer D: Argala on H7 ───────────────────────────────────────────────
    arg = v.get("argala_h7") or {}
    if arg and "_error" not in arg and arg.get("h7_overall"):
        paap = arg.get("h7_paap_argala") or ""
        suffix = (" — " + paap) if paap else ""
        lines.append(
            "  Argala on H7 (kalatra-bhava): {0} (benefic={1}, malefic={2}){3}".format(
                arg.get("h7_overall"),
                arg.get("h7_benefic_score"),
                arg.get("h7_malefic_score"),
                suffix,
            )
        )

    # ── Layer F: Saturn current transit on H7 ───────────────────────────────
    st = v.get("saturn_transit_h7") or {}
    if st and "_error" not in st:
        if st.get("blocking"):
            why = "in" if st.get("saturn_in_h7") else "aspecting"
            lines.append(
                "  Saturn TRANSIT: currently {0} natal H7 ({1}) "
                "— commitment-check phase ACTIVE".format(
                    why, st.get("saturn_sign")
                )
            )
        else:
            lines.append(
                "  Saturn TRANSIT: currently in {0} "
                "— no direct pressure on natal H7 ({1})".format(
                    st.get("saturn_sign"), st.get("h7_sign")
                )
            )

    # ── Layer H: Spouse description traits ─────────────────────────────────
    sd = v.get("spouse_description") or {}
    if sd and (sd.get("h7_sign") or sd.get("d9_7h_sign")):
        bits: list[str] = []
        if sd.get("h7_sign"):
            bits.append(
                "7H {0} ({1}/{2}/{3})".format(
                    sd.get("h7_sign"), sd.get("h7_quality"),
                    sd.get("h7_element"), sd.get("h7_polarity")
                )
            )
        if sd.get("sl_house"):
            bits.append("7L in H{0}/{1}".format(sd.get("sl_house"), sd.get("sl_sign")))
        if sd.get("h7_occupants"):
            bits.append("H7 occupants=" + str(sd.get("h7_occupants")))
        if sd.get("a7_sign"):
            bits.append("A7={0} (lord {1})".format(sd.get("a7_sign"), sd.get("a7_lord")))
        if sd.get("venus_sign"):
            bits.append("Venus in " + str(sd.get("venus_sign")))
        if sd.get("jupiter_sign"):
            bits.append("Jupiter in " + str(sd.get("jupiter_sign")))
        if sd.get("d9_7h_sign"):
            bits.append(
                "D9-7H={0} (lord {1} in {2})".format(
                    sd.get("d9_7h_sign"), sd.get("d9_7l"), sd.get("d9_7l_sign")
                )
            )
        if bits:
            lines.append("  Spouse traits (synthesise narration from these): " + "; ".join(bits))

    if not lines:
        return ""
    header = "  ── PHASE 2.8.18 FOCUS-BLOCK LAYERS (locked, do not paraphrase numbers) ──"
    return header + "\n" + "\n".join(lines) + "\n"


_MONTHS = ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]


def _ym_to_human(ym: str) -> str:
    """\"2025-12\" → \"December 2025\". Returns input unchanged if malformed."""
    try:
        y, m = (ym or "").split("-")[:2]
        return f"{_MONTHS[int(m)]} {y}"
    except Exception:
        return ym or "?"


def extract_window_str(v: dict) -> str:
    """
    Single source of truth for the human-readable timing window string.
    Returns the EXACT phrase the AI is required to echo verbatim, e.g.
    "April 2026 to June 2026". Empty string if no window.
    The AI validator uses this to detect violations and force a retry.
    """
    if not v:
        return ""
    nw = v.get("next_window") or {}
    if not nw:
        return ""
    ref_s, ref_e = nw.get("refined_start"), nw.get("refined_end")
    if ref_s and ref_e and ref_s != nw.get("start") and ref_e != nw.get("end"):
        return f"{_ym_to_human(ref_s)} to {_ym_to_human(ref_e)}"
    return f"{_ym_to_human(nw.get('start',''))} to {_ym_to_human(nw.get('end',''))}"


def extract_alt_window_str(v: dict) -> str:
    """Same as extract_window_str, but for next_alt_window (constraint-aware)."""
    if not v:
        return ""
    nw = v.get("next_alt_window") or {}
    if not nw:
        return ""
    ref_s, ref_e = nw.get("refined_start"), nw.get("refined_end")
    if ref_s and ref_e and ref_s != nw.get("start") and ref_e != nw.get("end"):
        return f"{_ym_to_human(ref_s)} to {_ym_to_human(ref_e)}"
    return f"{_ym_to_human(nw.get('start',''))} to {_ym_to_human(nw.get('end',''))}"


# ── Pre-baked, fact-locked answer templates ──────────────────────────────────
# These are filled in by Python BEFORE the AI is called. The AI's job collapses
# from "decide + compose" to "polish wording" — single OpenAI call, no retry.
_LANG_GREETING = {
    "hn": "Seedhi baat —", "hi": "सीधी बात —", "en": "Straight answer —",
}
_LANG_REASON_LABEL = {
    "hn": "Vajah",      "hi": "वजह",       "en": "Reason",
}
_LANG_TIMING_LABEL = {
    "hn": "Samay",      "hi": "समय",       "en": "Timing",
}
_LANG_REMEDY_LABEL = {
    "hn": "Upay",       "hi": "उपाय",      "en": "Remedy",
}
_LANG_AFTER_LABEL = {
    "hn": "Aap is window ko avoid karna chahte hain — agla sashakt yog",
    "hi": "यदि आप यह समय छोड़ना चाहते हैं — अगला सशक्त योग",
    "en": "If you wish to skip that window — the next strong yog",
}
_LANG_NO_WINDOW = {
    "hn": "Agle 12 saal mein koi spasht prabal vivah-yog nahi mil raha — dheeraj rakhein.",
    "hi": "अगले १२ वर्षों में कोई स्पष्ट प्रबल विवाह-योग नहीं मिल रहा — धैर्य रखें।",
    "en": "No strong marriage yog appears in the next 12 years — patience is advised.",
}


def format_final_answer(v: dict, lang_code: str = "hn", use_alt: bool = False) -> str:
    """
    Build a fully-baked, fact-locked answer the AI only has to polish for tone.
    Single source of truth for verdict / dasha / dates / remedy.

    Args:
      v          : verdict dict from assess_marriage()
      lang_code  : "hn" (Hinglish, default), "hi" (Devanagari), "en" (English)
      use_alt    : if True, narrate next_alt_window instead of next_window
                   (used when the devotee rejects the primary window).
    """
    if not v:
        return ""
    code = lang_code if lang_code in _LANG_GREETING else "hn"
    g    = _LANG_GREETING[code]
    L_R  = _LANG_REASON_LABEL[code]
    L_T  = _LANG_TIMING_LABEL[code]
    L_X  = _LANG_REMEDY_LABEL[code]
    L_A  = _LANG_AFTER_LABEL[code]

    # Verdict line — uses the engine's already-localised Hinglish phrase.
    verdict = v.get("verdict") or ""

    # Pick reasons (top 2 strong, top 1 weak) — no AI invention.
    rs = (v.get("reasons_strong") or [])[:2]
    rw = (v.get("reasons_weak")   or [])[:1]
    reason_bits = []
    if rs:
        reason_bits.append("; ".join(rs))
    if rw:
        reason_bits.append(f"weakening: {rw[0]}")
    reason_line = ". ".join(reason_bits) if reason_bits else "—"

    # Timing — primary OR alt (constraint mode).
    primary = extract_window_str(v)
    alt     = extract_alt_window_str(v)
    if use_alt and alt:
        timing_line = alt
    elif primary:
        timing_line = primary
    else:
        return f"{g} {_LANG_NO_WINDOW[code]}"

    # Optional after-line so even non-constraint replies hint that an alt exists.
    after_line = ""
    if (not use_alt) and alt:
        after_line = f"\n{L_A}: {alt}."

    cur_dasha = v.get("current_dasha") or ""
    sl_name   = v.get("seventh_lord") or ""
    karaka    = v.get("karaka") or ""
    remedy    = v.get("remedy") or ""

    return (
        f"{g} {verdict}.\n\n"
        f"{L_R}: 7th lord {sl_name}, kalatra-karaka {karaka}, "
        f"current dasha {cur_dasha}. {reason_line}.\n\n"
        f"{L_T}: {timing_line}.{after_line}\n\n"
        f"{L_X}: {remedy}."
    )


def _engine_json_envelope(v: dict) -> str:
    """
    JSON envelope at the very top of the prompt block. The AI is told to
    treat every value here as IMMUTABLE — copy verbatim, do not paraphrase.
    """
    import json as _json
    window_str = extract_window_str(v)
    alt_str    = extract_alt_window_str(v)
    nw  = v.get("next_window") or {}
    nw2 = v.get("next_alt_window") or {}
    payload = {
        "final_verdict":   v.get("verdict"),
        "score":           v.get("score"),
        "confidence_pct":  v.get("confidence"),
        "marriage_promised": v.get("marriage_promised"),
        "marriage_denied":   v.get("marriage_denied"),
        "delay":             v.get("delay"),
        "kp_verdict":        v.get("kp_verdict"),
        "current_dasha":     v.get("current_dasha"),
        "next_dasha_window": (f"{nw.get('start')} → {nw.get('end')}" if nw else None),
        "timeline_start":    nw.get("refined_start") or nw.get("start") or None,
        "timeline_end":      nw.get("refined_end")   or nw.get("end")   or None,
        "must_use_window_str": window_str or None,
        "next_alt_window_str": alt_str or None,
        "next_alt_dasha":      (f"{nw2.get('dasha')}" if nw2 else None),
        "remedy_planet":   v.get("remedy_for_planet"),
        "remedy":          v.get("remedy"),
    }
    return (
        "═══ ENGINE JSON (IMMUTABLE — COPY VALUES VERBATIM) ═══\n"
        + _json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n═════════════════════════════════════════════════════\n"
    )


def format_verdict_for_prompt(v: dict) -> str:
    """Render verdict as a tightly-structured authoritative block for the AI prompt.

    Layout:
      1. JSON envelope (machine-precise, top of block — what the AI MUST copy)
      2. Human-readable detail block (context for the narrator)
    """
    if not v:
        return ""
    nw = v.get("next_window") or {}
    if nw:
        # Prefer the refined (dasha ∩ Jupiter transit) sub-window if available.
        ref_s = nw.get("refined_start")
        ref_e = nw.get("refined_end")
        if ref_s and ref_e and ref_s != nw.get("start") and ref_e != nw.get("end"):
            primary_hr = f"{_ym_to_human(ref_s)} to {_ym_to_human(ref_e)}"
            nw_line = (
                f"  Next favourable Dasha window: {nw.get('dasha')} "
                f"({nw.get('start')} → {nw.get('end')}) — {nw.get('reason')}\n"
                f"  REFINED window (Dasha ∩ Jupiter transit through "
                f"{nw.get('jupiter_sign')}, hits {nw.get('jupiter_hits')}): "
                f"{ref_s} → {ref_e}\n"
                f"  >>> NARRATE THIS WINDOW EXACTLY AS: \"{primary_hr}\" "
                f"(Dasha {nw.get('dasha')} + Jupiter transit through "
                f"{nw.get('jupiter_sign')} — both classical triggers active). "
                f"DO NOT widen, shift, or change these dates. <<<"
            )
        else:
            nw_hr = f"{_ym_to_human(nw.get('start',''))} to {_ym_to_human(nw.get('end',''))}"
            nw_line = (
                f"  Next favourable Dasha window: {nw.get('dasha')} "
                f"({nw.get('start')} → {nw.get('end')}) — {nw.get('reason')}\n"
                f"  >>> NARRATE THIS WINDOW EXACTLY AS: \"{nw_hr}\" "
                f"(Maha-Antardasha: {nw.get('dasha')}). DO NOT widen, shift, or change these dates. <<<"
            )
    else:
        nw_line = ("  Next favourable Dasha window: NOT FOUND in next 12 years\n"
                   "  >>> NARRATE THIS AS: \"agle 12 saal mein koi spasht prabal vivah-yog "
                   "ka window nahi mil raha\" — DO NOT invent dates. <<<")
    d9 = v.get("d9") or {}
    d9_line = (f"  D9 (Navamsa) 7th lord: {d9.get('d9_7th_lord')} in {d9.get('d9_lord_sign')} "
               f"(D9 house {d9.get('d9_lord_house')})" if d9 else "  D9 7th lord: unavailable")
    rs = "\n".join(f"    + {r}" for r in (v.get("reasons_strong") or [])) or "    (none)"
    rw = "\n".join(f"    - {r}" for r in (v.get("reasons_weak") or [])) or "    (none)"

    return (
        _engine_json_envelope(v) + "\n"
        "════════════════════════════════════════════════════════════════════\n"
        "AUTHORITATIVE MARRIAGE VERDICT (deterministically computed by engine)\n"
        "════════════════════════════════════════════════════════════════════\n"
        f"  VERDICT:          {v.get('verdict')}\n"
        f"  Score:            {v.get('score')}/100   (confidence {v.get('confidence')}%)\n"
        f"  marriage_promised:{v.get('marriage_promised')}  marriage_denied:{v.get('marriage_denied')}  delay:{v.get('delay')}\n"
        f"  KP verdict:       {v.get('kp_verdict')} — {v.get('kp_reason')}\n"
        f"  7th lord:         {v.get('seventh_lord')} ({v.get('seventh_lord_dignity')})\n"
        f"  Karaka:           {v.get('karaka')} ({v.get('karaka_dignity')})\n"
        f"  Current Dasha:    {v.get('current_dasha')} (supports 2/7/11 = {v.get('current_dasha_supports')})\n"
        f"{_shad_line(v)}"
        f"{_jup_line(v)}"
        f"{_focus_block_lines(v)}"
        f"{nw_line}\n"
        f"{d9_line}\n"
        "  Strong supporting factors:\n"
        f"{rs}\n"
        "  Weakening / delay factors:\n"
        f"{rw}\n"
        f"  Recommended remedy planet: {v.get('remedy_for_planet')}\n"
        f"  Recommended remedy:        {v.get('remedy')}\n"
        "════════════════════════════════════════════════════════════════════\n"
    )
