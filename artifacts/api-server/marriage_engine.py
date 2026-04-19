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
    confidence = min(97, 50 + data_bonus + abs(score - 50) // 4)

    # ── D9 NAVAMSA ───────────────────────────────────────────────────────────
    d9_info = _d9_seventh_lord_info(kundli)
    if d9_info:
        trace.append(f"D9 7th lord = {d9_info.get('d9_7th_lord')} in {d9_info.get('d9_lord_sign')} (D9 house {d9_info.get('d9_lord_house')})")

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


_MONTHS = ["", "January","February","March","April","May","June",
              "July","August","September","October","November","December"]

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
