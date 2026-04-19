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

from datetime import datetime
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

REMEDY_BY_PLANET = {
    "Venus":   'Shukravar (Friday) ko 108 baar "Om Shum Shukraya Namah" jaap karein, safed mishri ka daan',
    "Jupiter": 'Guruvar (Thursday) ko 108 baar "Om Gum Gurave Namah" jaap karein, peeli daal ka daan',
    "Mars":    'Mangalvar (Tuesday) ko Hanuman Chalisa 11 baar paath, gud ka daan',
    "Saturn":  'Shanivar (Saturday) ko 108 baar "Om Sham Shanaischaraya Namah" jaap, til-tel ka daan',
    "Mercury": 'Budhvar (Wednesday) ko 108 baar "Om Bum Budhaya Namah" jaap, hari sabzi ka daan',
    "Sun":     'Ravivar (Sunday) ko Surya ko tambe ke lote se jal arpan + 108 baar "Om Suryaya Namah"',
    "Moon":    'Somvar (Monday) ko 108 baar "Om Som Somaya Namah" jaap, doodh-chawal ka daan',
    "Rahu":    'Shanivar ko Durga Saptashati ka paath, kambal daan',
    "Ketu":    'Mangalvar ko Ganesh Atharvashirsha paath, til daan',
}


def _sign_idx(sign_name: Any) -> Optional[int]:
    if not isinstance(sign_name, str):
        return None
    try:
        return SIGNS.index(sign_name.strip().capitalize())
    except ValueError:
        return None


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

    # Confidence: based on data completeness + score conviction
    data_bonus = 0
    if kp_verdict in ("promised", "denied"): data_bonus += 15
    if next_window:                          data_bonus += 10
    if seventh_lord and sl_dig:              data_bonus += 5
    if (intel.get("dignities") or []):       data_bonus += 5
    confidence = min(95, 50 + data_bonus + abs(score - 50) // 4)

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
        "d9":                   d9_info,
        "remedy":               remedy,
        "remedy_for_planet":    weakest_planet,
        "logic_trace":          trace,
    }


def format_verdict_for_prompt(v: dict) -> str:
    """Render verdict as a tightly-structured authoritative block for the AI prompt."""
    if not v:
        return ""
    nw = v.get("next_window") or {}
    nw_line = (f"  Next favourable Dasha window: {nw.get('dasha')} "
               f"({nw.get('start')} → {nw.get('end')}) — {nw.get('reason')}"
               if nw else "  Next favourable Dasha window: not found within computed dasha range")
    d9 = v.get("d9") or {}
    d9_line = (f"  D9 (Navamsa) 7th lord: {d9.get('d9_7th_lord')} in {d9.get('d9_lord_sign')} "
               f"(D9 house {d9.get('d9_lord_house')})" if d9 else "  D9 7th lord: unavailable")
    rs = "\n".join(f"    + {r}" for r in (v.get("reasons_strong") or [])) or "    (none)"
    rw = "\n".join(f"    - {r}" for r in (v.get("reasons_weak") or [])) or "    (none)"

    return (
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
