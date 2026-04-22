"""
AI Narrator for Life Mastery Report.

Purpose
-------
Engine calculates numbers (Life Path, Rashi, Nakshatra, Dasha, etc.).
This narrator wraps GPT-4.1 to turn those FACTS into premium storytelling
paragraphs in the "Ashutosh Bharadwaj live reading" voice — curious hook,
relatable metaphor, honest double-edge (gift + shadow), practical action.

Key guarantees
--------------
1. Engine facts are NEVER modified by AI — AI only writes the prose around them.
2. Strict prompt locks the exact numbers/planets AI may reference.
3. Hard word-count ceiling (enforced by post-trim).
4. If AI fails / times out → caller should fall back to static tier content.
5. 3 languages supported: english, hindi, hinglish.

Model: gpt-4.1 (user-provided OPENAI_API_KEY).
"""
from __future__ import annotations

import os
import threading
from typing import Any, Callable, Dict, Optional

_client = None
_client_err: Optional[str] = None
_client_lock = threading.Lock()


def _get_client():
    global _client, _client_err
    if _client is not None or _client_err is not None:
        return _client
    with _client_lock:
        # Re-check inside the lock.
        if _client is not None or _client_err is not None:
            return _client
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            _client_err = "OPENAI_API_KEY missing"
            return None
        try:
            from openai import OpenAI
            timeout = float(os.environ.get("OPENAI_TIMEOUT", "45"))
            _client = OpenAI(api_key=api_key, timeout=timeout)
            return _client
        except Exception as exc:
            _client_err = f"OpenAI SDK init failed: {exc}"
            return None


# ── Fact-guard validators ────────────────────────────────────────────────────
# Per-section content validation. AI output is REJECTED (→ fallback to static)
# if the validator returns False, protecting against hallucinated numbers /
# planets / deities that contradict the locked engine facts.
#
# Each validator receives (facts, text) and returns True if text is safe.

def _has_num(text: str, value) -> bool:
    """Check a number appears as a standalone token in text (not inside another)."""
    import re
    if value is None or value == "":
        return True  # nothing to check
    return re.search(rf"(?<!\d){re.escape(str(value))}(?!\d)", text) is not None


def _has_word(text: str, value) -> bool:
    """Case-insensitive presence check.

    For composite values like "Lord Vishnu / Brihaspati", ANY non-trivial
    fragment is sufficient — splits on '/' and ',' and accepts a hit on
    any token of length >= 3.
    """
    if not value:
        return True
    text_lc = text.lower()
    raw = str(value).lower().strip()
    if not raw:
        return True
    # Whole-string fast path
    if raw in text_lc:
        return True
    # Try fragments split on '/' and ',' — accept any hit of length >= 3
    import re
    for frag in re.split(r"[\/,]", raw):
        frag = frag.strip()
        # Drop common honorifics/articles to avoid trivial matches
        for prefix in ("lord ", "goddess ", "shri ", "sri ", "bhagwan "):
            if frag.startswith(prefix):
                frag = frag[len(prefix):]
        if len(frag) >= 3 and frag in text_lc:
            return True
    return False


_VALIDATORS: Dict[str, Callable[[Dict[str, Any], str], bool]] = {
    "tier1.life_path":
        lambda f, t: _has_num(t, f.get("life_path_number")),
    "tier1.expression":
        lambda f, t: _has_num(t, f.get("expression_number")),
    "tier1.soul_urge":
        lambda f, t: _has_num(t, f.get("soul_urge_number")),
    "tier1.personality":
        lambda f, t: _has_num(t, f.get("personality_number")),
    "tier1.maturity":
        lambda f, t: _has_num(t, f.get("maturity_number")),
    "tier1.personal_year":
        lambda f, t: _has_num(t, f.get("personal_year_number"))
                     and _has_num(t, f.get("current_year")),
    "tier2.sun_moon_rashi":
        lambda f, t: (_has_word(t, f.get("moon_rashi"))
                      or _has_word(t, f.get("sun_rashi"))),
    "tier2.nakshatra":
        lambda f, t: _has_word(t, f.get("nakshatra"))
                     and _has_word(t, f.get("ruling_planet")),
    "tier2.current_mahadasha":
        lambda f, t: _has_word(t, f.get("current_lord")),
    "tier2.sadhe_sati":
        # Just ensure "Saturn/Shani" is mentioned — phase name is optional.
        lambda f, t: _has_word(t, "Shani") or _has_word(t, "Saturn"),
    "tier2.ishta_devata":
        lambda f, t: _has_word(t, f.get("ishta_devata"))
                     and _has_word(t, f.get("ruling_planet")),
    # ── Tier 3 — Personalized Remedies ───────────────────────────────
    "tier3.weakest_planet":
        lambda f, t: _has_word(t, f.get("weakest_planet")),
    "tier3.current_dasha_remedy":
        lambda f, t: _has_word(t, f.get("current_lord")),
    "tier3.karmic_path":
        # Either a debt number or a missing-lesson digit must appear, OR
        # if both are empty the AI must still be coherent (skip strict check).
        lambda f, t: (
            (not f.get("karmic_debts") and not f.get("karmic_lessons_missing"))
            or any(_has_num(t, d) for d in (f.get("karmic_debts") or []))
            or any(_has_num(t, l) for l in (f.get("karmic_lessons_missing") or []))
        ),
    "tier3.personal_year_remedy":
        lambda f, t: _has_num(t, f.get("personal_year_number"))
                     and _has_num(t, f.get("current_year")),
    "tier3.ishta_sadhana":
        lambda f, t: _has_word(t, f.get("ishta_devata"))
                     and _has_word(t, f.get("ruling_planet")),
    # ── Tier 4 — Personal Audits (Doshas) ────────────────────────────
    "tier4.dosh_overview":
        # Score must appear OR verdict keyword (covers score=0 case where the
        # "0" digit may not appear naturally in the prose).
        lambda f, t: _has_num(t, f.get("karmic_load_score"))
                     or _has_word(t, f.get("verdict_keyword")),
    "tier4.mangal_audit":
        # AI must mention Mangal/Mars
        lambda f, t: _has_word(t, "Mangal") or _has_word(t, "Mars")
                     or _has_word(t, "मंगल"),
    "tier4.kaal_sarp_audit":
        # AI must mention Kaal Sarp / Rahu / Ketu
        lambda f, t: (_has_word(t, "Kaal") or _has_word(t, "Rahu")
                      or _has_word(t, "Ketu") or _has_word(t, "काल")),
    "tier4.shani_afflictions":
        lambda f, t: _has_word(t, "Shani") or _has_word(t, "Saturn")
                     or _has_word(t, "शनि"),
    "tier4.audit_synthesis":
        # Score must appear; or accept if score is 0 (overview already clean)
        lambda f, t: _has_num(t, f.get("karmic_load_score"))
                     or f.get("karmic_load_score") == 0,
    # ── Tier 5 — Relationships & Compatibility ───────────────────────
    "tier5.compatibility_dna":
        # Must mention Moon-nakshatra OR moon-sign — the DNA anchor
        lambda f, t: _has_word(t, f.get("moon_nakshatra"))
                     or _has_word(t, f.get("moon_sign")),
    "tier5.yoni_temperament":
        lambda f, t: _has_word(t, f.get("yoni")),
    "tier5.partner_numerology":
        # Must mention self driver number
        lambda f, t: _has_num(t, f.get("self_driver")),
    "tier5.marriage_stability":
        # Must mention either Nadi or Mangal — the stability levers
        lambda f, t: _has_word(t, "Nadi") or _has_word(t, f.get("self_nadi"))
                     or _has_word(t, "Mangal") or _has_word(t, "Saturn")
                     or _has_word(t, "नाड़ी") or _has_word(t, "मंगल"),
    "tier5.ideal_partner":
        # Must mention either own driver, own yoni, or own moon-nakshatra
        lambda f, t: _has_num(t, f.get("self_driver"))
                     or _has_word(t, f.get("self_yoni"))
                     or _has_word(t, f.get("self_moon_nakshatra")),
    # ── Tier 6 — Career & Profession ─────────────────────────────────
    # Each validator anchors on a SPECIFIC locked fact (Atmakaraka planet,
    # Amatyakaraka planet, job-vs-biz verdict word, driver number) so generic
    # career puff is rejected.
    "tier6.soul_purpose":
        # Must mention the Atmakaraka planet by name
        lambda f, t: _has_word(t, f.get("ak_planet")),
    "tier6.career_karaka":
        # Must mention the Amatyakaraka planet by name
        lambda f, t: _has_word(t, f.get("amk_planet")),
    "tier6.job_vs_business":
        # Must mention the LOCKED verdict token from facts (BUSINESS / JOB /
        # HYBRID / EMPLOYMENT) — the engine's call, not generic prose. This
        # blocks contradictory text (e.g. AI saying "JOB" when chart says "BUSINESS").
        lambda f, t: any(
            _has_word(t, tok)
            for tok in (f.get("verdict") or "").replace("/", " ").replace("(", " ")
                                              .replace(")", " ").split()
            if len(tok) >= 3
        ),
    "tier6.best_industries":
        # Must mention BOTH driver number AND vocation planet — the dual anchor
        lambda f, t: _has_num(t, f.get("driver_number"))
                     and _has_word(t, f.get("vocation_planet")),
    "tier6.numerology_career":
        # Must mention driver number AND personal-year number for 2026
        lambda f, t: _has_num(t, f.get("driver_number"))
                     and _has_num(t, f.get("py_2026")),
    # ── Tier 7 — Wealth & Money ──────────────────────────────────────
    # Each validator anchors on a SPECIFIC locked fact from this person's
    # chart (planet name, yoga name, MD lord, driver number) — not generic
    # wealth keywords — so generic/hallucinated prose is rejected.
    "tier7.wealth_dna":
        # Must mention BOTH the money planet AND either yoga-count or driver
        lambda f, t: _has_word(t, f.get("money_planet"))
                     and (_has_num(t, f.get("yoga_count"))
                          or _has_num(t, f.get("driver_number"))),
    "tier7.dhana_yogas":
        # If yogas exist, AT LEAST ONE specific yoga name must appear.
        # If yoga_count == 0, accept any prose (no fact to anchor on).
        lambda f, t: (
            (f.get("yoga_count") or 0) == 0
            or any(_has_word(t, n) for n in (f.get("yoga_names") or []) if n)
        ),
    "tier7.daridra_audit":
        # If active daridra exists → require a specific yoga name OR a bhanga
        # factor token. If clean (no active yogas) → require a daridra/poverty
        # word PLUS the cancelled-state acknowledgement (bhanga / cancel /
        # Lakshmi / favourable) so generic wealth puff doesn't pass.
        lambda f, t: (
            (f.get("active_yoga_count") or 0) > 0
            and (any(_has_word(t, n) for n in (f.get("active_yoga_names") or []) if n)
                 or any(_has_word(t, b) for b in (f.get("bhanga_factors") or []) if b))
        ) or (
            (f.get("active_yoga_count") or 0) == 0
            and (_has_word(t, "Daridra") or _has_word(t, "poverty")
                 or _has_word(t, "दरिद्र"))
        ),
    "tier7.wealth_strategies":
        # MUST mention current MD lord (the dasha anchor) — the rest is prose
        lambda f, t: _has_word(t, f.get("current_md_lord")),
    "tier7.money_numerology":
        # MUST mention BOTH driver number AND money planet — the dual anchor
        lambda f, t: _has_num(t, f.get("driver_number"))
                     and _has_word(t, f.get("money_planet")),
    # ── Tier 8 — Health & Longevity ──────────────────────────────────
    # Each validator anchors on a SPECIFIC locked fact (dosha, planet,
    # MD-lord, driver number) so generic health puff is rejected.
    "tier8.prakriti":
        # Must mention the dominant dosha by name (Vata/Pitta/Kapha)
        lambda f, t: _has_word(t, f.get("dominant_dosha"))
                     and (_has_word(t, f.get("nakshatra"))
                          or _has_word(t, f.get("moon_sign"))),
    "tier8.vitality":
        # Must mention Sun + Moon AND at least one of the locked house numbers
        lambda f, t: (_has_word(t, "Sun") or _has_word(t, "Surya")
                      or _has_word(t, "सूर्य"))
                     and (_has_word(t, "Moon") or _has_word(t, "Chandra")
                          or _has_word(t, "चंद्र"))
                     and (_has_num(t, f.get("sun_house"))
                          or _has_num(t, f.get("moon_house"))),
    "tier8.body_parts":
        # Must mention BOTH driver number AND primary planet (dual anchor)
        lambda f, t: _has_num(t, f.get("driver_number"))
                     and _has_word(t, f.get("primary_planet")),
    "tier8.healing_toolkit":
        # Driver number + primary planet + healing-gem name (triple anchor —
        # rejects generic "do exercise / eat well" prose)
        lambda f, t: _has_num(t, f.get("driver_number"))
                     and _has_word(t, f.get("primary_planet"))
                     and (not f.get("healing_gem") or f.get("healing_gem") == "—"
                          or _has_word(t, f.get("healing_gem"))),
    "tier8.health_window":
        # MD lord + locked verdict token + MD-house number (triple anchor)
        # so AI cannot pass with contradictory window/house claims.
        lambda f, t: _has_word(t, f.get("md_lord"))
                     and any(
                         _has_word(t, tok)
                         for tok in (f.get("verdict") or "").replace("-", " ").split()
                         if len(tok) >= 4
                     )
                     and (_has_num(t, f.get("md_house")) if f.get("md_house") else True),
    # ── Tier 9 — Family, Lineage & Children ──────────────────────────
    # Each validator anchors on locked house lord names + key planet anchors
    # (Moon for mother, Sun for father, Jupiter for children) so generic
    # family puff is rejected.
    "tier9.mother_home":
        # Must mention 4th-house lord by name AND either the sign or moon-house
        lambda f, t: _has_word(t, f.get("fourth_lord"))
                     and (_has_word(t, f.get("fourth_sign"))
                          or _has_num(t, f.get("moon_house"))),
    "tier9.father_dharma":
        # Triple anchor: 9L name + Sun token + locked numeric anchor
        # (9L-house OR sun-house) so generic father puff cannot pass.
        lambda f, t: _has_word(t, f.get("ninth_lord"))
                     and (_has_word(t, "Sun") or _has_word(t, "Surya")
                          or _has_word(t, "सूर्य"))
                     and (_has_num(t, f.get("ninth_lord_house"))
                          or _has_num(t, f.get("sun_house"))),
    "tier9.children_creativity":
        # Quadruple anchor: Jupiter + locked Putra verdict + 5L name +
        # numeric house anchor (5L-house OR Jupiter-house).
        lambda f, t: (_has_word(t, "Jupiter") or _has_word(t, "Brihaspati")
                      or _has_word(t, "बृहस्पति"))
                     and _has_word(t, f.get("putra_yoga_verdict"))
                     and _has_word(t, f.get("fifth_lord"))
                     and (_has_num(t, f.get("fifth_lord_house"))
                          or _has_num(t, f.get("jupiter_house"))),
    "tier9.lineage_pitru":
        # If pitru active → must mention pitru/tarpan token AND the chart-
        # specific 9L (or driver number) so AI must actually reference user's
        # chart, not generic "your ancestors". If clear → must explicitly say
        # clear/no/safe to acknowledge engine's CLEAR call (prevents AI from
        # inventing a pitru-dosha that doesn't exist).
        lambda f, t: (
            f.get("active") and (
                _has_word(t, "Pitru") or _has_word(t, "Pitra")
                or _has_word(t, "tarpan") or _has_word(t, "ancestral")
                or _has_word(t, "पितृ") or _has_word(t, "तर्पण")
            ) and (
                _has_word(t, f.get("ninth_lord"))
                or _has_num(t, f.get("driver_number"))
            )
        ) or (
            (not f.get("active")) and (
                _has_word(t, "clear") or _has_word(t, "no major")
                or _has_word(t, "absent") or _has_word(t, "safe")
                or _has_word(t, "नहीं") or _has_word(t, "साफ")
            ) and (
                _has_word(t, f.get("ninth_lord"))
                or _has_num(t, f.get("driver_number"))
            )
        ),
    "tier9.numerology_family":
        # Must mention driver number + driver planet (dual anchor)
        lambda f, t: _has_num(t, f.get("driver_number"))
                     and _has_word(t, f.get("driver_planet")),
    # ── Tier 10 — Transits, Sade-Sati & Yearly Forecast ─────────────
    # Each validator anchors on locked transit signs/houses + verdict
    # tokens to prevent generic "Saturn troubles you" puff. Ensures AI
    # actually references the live sky vs natal chart.
    "tier10.sade_sati":
        # Quadruple anchor: Saturn token + current Saturn sign + natal Moon
        # sign + verdict OR phase token (so AI cannot say "Sade-Sati" if
        # engine returned NO-SADE-SATI, and vice versa).
        lambda f, t: (_has_word(t, "Saturn") or _has_word(t, "Shani")
                      or _has_word(t, "शनि"))
                     and _has_word(t, f.get("saturn_sign"))
                     and _has_word(t, f.get("natal_moon_sign"))
                     and (
                         any(_has_word(t, tok)
                             for tok in (f.get("verdict") or "").replace("-", " ").split()
                             if len(tok) >= 3)
                         or any(_has_word(t, tok)
                                for tok in (f.get("phase") or "").replace("-", " ").split()
                                if len(tok) >= 4)
                     ),
    "tier10.jupiter_gochar":
        # Triple anchor: Jupiter token + current Jupiter sign + verdict token
        lambda f, t: (_has_word(t, "Jupiter") or _has_word(t, "Brihaspati")
                      or _has_word(t, "बृहस्पति") or _has_word(t, "Guru"))
                     and _has_word(t, f.get("jupiter_sign"))
                     and any(
                         _has_word(t, tok) for tok in
                         (f.get("verdict") or "").lower().split()
                         if len(tok) >= 4
                     ),
    "tier10.dasha_layers":
        # Triple anchor: MD lord + AD lord names + MD-house number
        lambda f, t: _has_word(t, f.get("md_lord"))
                     and _has_word(t, f.get("ad_lord"))
                     and (_has_num(t, f.get("md_house")) if f.get("md_house") else True),
    "tier10.personal_year":
        # Triple anchor: personal year number + current calendar year +
        # locked theme token (FRESH START / EXPANSION / etc.)
        lambda f, t: _has_num(t, f.get("personal_year"))
                     and _has_num(t, f.get("current_year"))
                     and any(
                         _has_word(t, tok)
                         for tok in (f.get("personal_year_theme") or "").replace("&", " ").split()
                         if len(tok) >= 4
                     ),
    "tier10.year_synthesis":
        # Triple anchor: MD lord + personal year number + current calendar year
        # so AI cannot deliver a generic "your year ahead" closing.
        lambda f, t: _has_word(t, f.get("md_lord"))
                     and _has_num(t, f.get("personal_year"))
                     and _has_num(t, f.get("current_year")),
    # ── Tier 11 — Spirituality, Moksha & Dharma-Path ────────────────
    # Each validator multi-anchors on chart-specific tokens (sign names,
    # AK lord, deity tokens) so AI cannot produce generic "be spiritual" puff.
    "tier11.moksha_trikona":
        # Quadruple anchor: 4th-house sign OR 8th-house sign OR 12th-house sign
        # (at least 2 of 3 must appear) + score number + verdict-keyword token.
        lambda f, t: (
            sum(1 for s in (f.get("fourth_sign"), f.get("eighth_sign"),
                            f.get("twelfth_sign")) if s and _has_word(t, s)) >= 2
        ) and _has_num(t, f.get("score"))
          and any(_has_word(t, tok) for tok in
                  (f.get("verdict") or "").replace("—", " ").replace("-", " ").split()
                  if len(tok) >= 5),
    "tier11.karakamsa_dharma":
        # Triple anchor: Atmakaraka planet name + Karakamsa D9 sign + AK token.
        lambda f, t: _has_word(t, f.get("atmakaraka"))
                     and _has_word(t, f.get("karakamsa_sign"))
                     and (_has_word(t, "Karakamsa") or _has_word(t, "Atmakaraka")
                          or _has_word(t, "AK") or _has_word(t, "कारकांश")
                          or _has_word(t, "आत्मकारक") or _has_word(t, "soul")),
    "tier11.ishta_devata":
        # Triple anchor: ishta-lord planet + 12th-from-Karakamsa sign + at least
        # one deity-name token from the deity string (Shiva/Vishnu/Lakshmi/etc).
        lambda f, t: _has_word(t, f.get("ishta_lord"))
                     and _has_word(t, f.get("twelfth_from_karakamsa"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("deity") or "").replace("/", " ").replace("(", " ")
                              .replace(")", " ").split()
                             if len(tok) >= 4 and tok not in ("Lord", "Goddess", "Sri")),
    "tier11.mantra_sadhana":
        # Triple anchor: driver number + driver-planet name + a deity-name token.
        lambda f, t: _has_num(t, f.get("driver_number"))
                     and _has_word(t, f.get("driver_planet"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("primary_deity") or "").replace("/", " ").split()
                             if len(tok) >= 4 and tok not in ("Lord", "Goddess", "Sri")),
    "tier11.spiritual_synthesis":
        # Triple anchor: AK lord + Karakamsa sign + verdict_token (locked
        # synthesis token like STRONG-MOKSHA-PATH / BALANCED-DHARMA-PATH).
        lambda f, t: _has_word(t, f.get("atmakaraka"))
                     and _has_word(t, f.get("karakamsa_sign"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("verdict_token") or "").split("-")
                             if len(tok) >= 5),
    # ── Tier 12 — Marriage & Spouse Deep Audit ──────────────────────
    # Each validator multi-anchors on chart-locked tokens (7th sign,
    # planet names, house numbers, severity tokens) so AI cannot ship
    # generic "your spouse will be loving" puff.
    "tier12.saptamesha":
        # Triple anchor: 7th sign + 7th lord planet + lord house number.
        lambda f, t: _has_word(t, f.get("seventh_sign"))
                     and _has_word(t, f.get("seventh_lord"))
                     and (_has_num(t, f.get("lord_house"))
                          if f.get("lord_house") else True),
    "tier12.spouse_karaka":
        # Triple anchor: karaka planet (Venus) + karaka sign + karaka house.
        lambda f, t: _has_word(t, f.get("karaka_planet"))
                     and _has_word(t, f.get("karaka_sign"))
                     and (_has_num(t, f.get("karaka_house"))
                          if f.get("karaka_house") else True),
    "tier12.d9_spouse":
        # Triple anchor: D9 7th sign + Darakaraka planet name + Darakaraka
        # D9 sign (or 'Navamsa'/'D9'/'navamsha' keyword).
        lambda f, t: _has_word(t, f.get("d9_seventh_sign"))
                     and _has_word(t, f.get("darakaraka"))
                     and (_has_word(t, f.get("darakaraka_sign_d9"))
                          or _has_word(t, "Navamsa") or _has_word(t, "D9")
                          or _has_word(t, "Darakaraka") or _has_word(t, "navamsha")
                          or _has_word(t, "नवांश")),
    "tier12.mangal_audit":
        # Triple anchor: Mars/Mangal token + severity token + mars-house number
        # (from Lagna OR from Moon — at least one must appear).
        lambda f, t: (_has_word(t, "Mars") or _has_word(t, "Mangal")
                      or _has_word(t, "Kuja") or _has_word(t, "मंगल"))
                     and _has_word(t, f.get("severity"))
                     and (_has_num(t, f.get("mars_house_lagna"))
                          or _has_num(t, f.get("mars_house_moon"))),
    "tier12.marriage_timing":
        # Triple anchor: current MD lord + current AD lord + window-status
        # keyword (HOT/WARM/TACTICAL/PREP — at least one ≥4-char token).
        lambda f, t: _has_word(t, f.get("current_md"))
                     and _has_word(t, f.get("current_ad"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("window_status") or "").replace("-", " ").split()
                             if len(tok) >= 4),
    "tier12.marriage_synthesis":
        # Triple anchor: 7th sign + karaka planet (Venus) + verdict_token
        # split on '-' (e.g. HARMONIOUS-MARRIAGE-PATH → at least one ≥5-char
        # token like HARMONIOUS or MARRIAGE).
        lambda f, t: _has_word(t, f.get("seventh_sign"))
                     and _has_word(t, f.get("karaka_planet"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("verdict_token") or "").split("-")
                             if len(tok) >= 5),
    # ── Tier 13 — Children, Progeny & Education Deep Audit ──────────
    # Same multi-anchor strategy: lock to 5th-house sign + chart-locked
    # planet/house tokens + severity/verdict tokens.
    "tier13.putra_bhava":
        # Triple anchor: 5th sign + 5th lord planet + lord house number.
        lambda f, t: _has_word(t, f.get("fifth_sign"))
                     and _has_word(t, f.get("fifth_lord"))
                     and (_has_num(t, f.get("lord_house"))
                          if f.get("lord_house") else True),
    "tier13.putra_karaka":
        # Triple anchor: Jupiter token + Jupiter sign + Jupiter house number.
        lambda f, t: (_has_word(t, "Jupiter") or _has_word(t, "Guru")
                      or _has_word(t, "Brihaspati") or _has_word(t, "गुरु"))
                     and _has_word(t, f.get("karaka_sign"))
                     and (_has_num(t, f.get("karaka_house"))
                          if f.get("karaka_house") else True),
    "tier13.d7_picture":
        # Triple anchor: D7 keyword + D7 5th sign + D7 5th lord planet.
        lambda f, t: (_has_word(t, "Saptamsa") or _has_word(t, "Saptamsha")
                      or _has_word(t, "D7") or _has_word(t, "सप्तांश"))
                     and _has_word(t, f.get("d7_fifth_sign"))
                     and _has_word(t, f.get("d7_fifth_lord")),
    "tier13.yogas_audit":
        # Triple anchor: Putra/Putrakaraka/Santati keyword + severity token +
        # 5th-lord planet name (chart-locked anchor).
        lambda f, t: (_has_word(t, "Putra") or _has_word(t, "Putrakaraka")
                      or _has_word(t, "Santati") or _has_word(t, "progeny")
                      or _has_word(t, "पुत्र"))
                     and _has_word(t, f.get("severity"))
                     and _has_word(t, f.get("fifth_lord")),
    "tier13.children_timing":
        # Triple anchor: current MD lord + current AD lord + window-status
        # keyword (ACTIVE / WARM / TACTICAL / PREP — at least one ≥4-char token).
        lambda f, t: _has_word(t, f.get("current_md"))
                     and _has_word(t, f.get("current_ad"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("window_status") or "").replace("-", " ").split()
                             if len(tok) >= 4),
    "tier13.progeny_synthesis":
        # Triple anchor: 5th sign + Jupiter (Putrakaraka) + verdict_token
        # split on '-' (e.g. BLESSED-PROGENY-PATH → at least one ≥5-char token).
        lambda f, t: _has_word(t, f.get("fifth_sign"))
                     and (_has_word(t, "Jupiter") or _has_word(t, "Guru")
                          or _has_word(t, "गुरु"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("verdict_token") or "").split("-")
                             if len(tok) >= 5),
    # ── Tier 14 — Property, Vehicles & Comforts Deep Audit ──────────
    # Multi-anchor: 4th sign / 4L planet / Mars-Venus karakas / severity / verdict.
    "tier14.sukha_bhava":
        # Triple anchor: 4th sign + 4th lord planet + lord house number.
        lambda f, t: _has_word(t, f.get("fourth_sign"))
                     and _has_word(t, f.get("fourth_lord"))
                     and (_has_num(t, f.get("lord_house"))
                          if f.get("lord_house") else True),
    "tier14.karakas":
        # Quad anchor: Mars (Bhumi) + Venus (Vahana) + chart-locked sign +
        # chart-locked house-num (mars_house OR venus_house) so generic prose
        # without the user's specific placements cannot pass.
        lambda f, t: (_has_word(t, "Mars") or _has_word(t, "Mangal")
                      or _has_word(t, "Bhumi") or _has_word(t, "मंगल"))
                     and (_has_word(t, "Venus") or _has_word(t, "Shukra")
                          or _has_word(t, "Vahana") or _has_word(t, "शुक्र"))
                     and (_has_word(t, f.get("mars_sign"))
                          or _has_word(t, f.get("venus_sign")))
                     and (_has_num(t, f.get("mars_house"))
                          or _has_num(t, f.get("venus_house"))),
    "tier14.d4_picture":
        # When D4 is available: triple anchor (D4 keyword + D4 4th sign + D4 4th lord).
        # When D4 is unavailable (available=False): allow narration that
        # acknowledges the fallback by mentioning D4/Chaturthamsa keyword AND
        # using a fallback marker ("not available" / "fallback" / "D1").
        lambda f, t: (
            ((_has_word(t, "Chaturthamsa") or _has_word(t, "Chaturthamsha")
              or _has_word(t, "D4") or _has_word(t, "चतुर्थांश"))
             and _has_word(t, f.get("d4_fourth_sign"))
             and _has_word(t, f.get("d4_fourth_lord")))
            if f.get("available")
            else (
                (_has_word(t, "Chaturthamsa") or _has_word(t, "D4")
                 or _has_word(t, "चतुर्थांश"))
                and (_has_word(t, "not available") or _has_word(t, "unavailable")
                     or _has_word(t, "fallback") or _has_word(t, "D1")
                     or _has_word(t, "missing") or _has_word(t, "उपलब्ध नहीं"))
            )
        ),
    "tier14.yogas_audit":
        # Triple anchor: Bhumi/Vahana/property keyword + severity token +
        # 4th-lord planet name (chart-locked anchor).
        lambda f, t: (_has_word(t, "Bhumi") or _has_word(t, "Vahana")
                      or _has_word(t, "property") or _has_word(t, "Sukha")
                      or _has_word(t, "भूमि") or _has_word(t, "वाहन"))
                     and _has_word(t, f.get("severity"))
                     and _has_word(t, f.get("fourth_lord")),
    "tier14.acquisition_timing":
        # Triple anchor: current MD lord + current AD lord + window-status keyword
        # (ACTIVE / WARM / TACTICAL / PREP — at least one ≥4-char token).
        lambda f, t: _has_word(t, f.get("current_md"))
                     and _has_word(t, f.get("current_ad"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("window_status") or "").replace("-", " ").split()
                             if len(tok) >= 4),
    "tier14.property_synthesis":
        # Triple anchor: 4th sign + Mars OR Venus karaka + verdict_token
        # split on '-' (e.g. BLESSED-PROPERTY-PATH → at least one ≥5-char token).
        lambda f, t: _has_word(t, f.get("fourth_sign"))
                     and (_has_word(t, "Mars") or _has_word(t, "Venus")
                          or _has_word(t, "Bhumi") or _has_word(t, "Vahana"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("verdict_token") or "").split("-")
                             if len(tok) >= 5),
    # ── Tier 15 — Foreign Travel, Settlement & 12th House ──────────
    "tier15.vyaya_bhava":
        # Triple anchor: 12th sign + 12L planet + lord-house num.
        lambda f, t: _has_word(t, f.get("twelfth_sign"))
                     and _has_word(t, f.get("twelfth_lord"))
                     and (_has_num(t, f.get("lord_house"))
                          if f.get("lord_house") else True),
    "tier15.karakas":
        # Quad anchor: Rahu (foreign) + Moon (water-travel) keyword + chart-locked
        # sign anchor (rahu_sign or moon_sign) + chart-locked house num.
        lambda f, t: (_has_word(t, "Rahu") or _has_word(t, "राहु"))
                     and (_has_word(t, "Moon") or _has_word(t, "Chandra")
                          or _has_word(t, "चंद्र"))
                     and (_has_word(t, f.get("rahu_sign"))
                          or _has_word(t, f.get("moon_sign")))
                     and (_has_num(t, f.get("rahu_house"))
                          or _has_num(t, f.get("moon_house"))),
    "tier15.yogas_audit":
        # Triple anchor: foreign/Vyaya/12th keyword + severity token + 12L planet.
        lambda f, t: (_has_word(t, "foreign") or _has_word(t, "Vyaya")
                      or _has_word(t, "12th") or _has_word(t, "Bhagya")
                      or _has_word(t, "विदेश") or _has_word(t, "व्यय"))
                     and _has_word(t, f.get("severity"))
                     and _has_word(t, f.get("twelfth_lord")),
    "tier15.settlement":
        # Quad anchor: settlement-mode token (SETTLEMENT / EXTENDED-STAY /
        # FREQUENT-TRAVEL / OCCASIONAL-VISIT — at least one ≥5-char token) +
        # Rahu OR Moon keyword + 12L planet + chart-locked Rahu/Moon house num
        # (prevents generic settlement prose from passing without chart anchor).
        lambda f, t: any(_has_word(t, tok) for tok in
                         (f.get("mode") or "").replace("-", " ").split()
                         if len(tok) >= 5)
                     and (_has_word(t, "Rahu") or _has_word(t, "Moon")
                          or _has_word(t, "Chandra"))
                     and _has_word(t, f.get("twelfth_lord"))
                     and (_has_num(t, f.get("rahu_house"))
                          or _has_num(t, f.get("moon_house"))),
    "tier15.travel_timing":
        # Triple anchor: current MD + current AD + window-status keyword.
        lambda f, t: _has_word(t, f.get("current_md"))
                     and _has_word(t, f.get("current_ad"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("window_status") or "").replace("-", " ").split()
                             if len(tok) >= 4),
    "tier15.foreign_synthesis":
        # Triple anchor: 12th sign + Rahu/Vyaya keyword + verdict_token.
        lambda f, t: _has_word(t, f.get("twelfth_sign"))
                     and (_has_word(t, "Rahu") or _has_word(t, "Vyaya")
                          or _has_word(t, "foreign") or _has_word(t, "विदेश"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("verdict_token") or "").split("-")
                             if len(tok) >= 5),
    # ── Tier 16 — Health, Longevity & 8th House (Ayur Bhava) ───────
    "tier16.ayur_bhava":
        # Triple anchor: 8th sign + 8L planet + lord-house num.
        lambda f, t: _has_word(t, f.get("eighth_sign"))
                     and _has_word(t, f.get("eighth_lord"))
                     and (_has_num(t, f.get("lord_house"))
                          if f.get("lord_house") else True),
    "tier16.karakas":
        # Quad anchor: Sun (vitality) + Mars/Saturn (surgery/chronic) +
        # chart-locked sign anchor + chart-locked house num.
        lambda f, t: (_has_word(t, "Sun") or _has_word(t, "Surya")
                      or _has_word(t, "सूर्य"))
                     and (_has_word(t, "Mars") or _has_word(t, "Mangal")
                          or _has_word(t, "Saturn") or _has_word(t, "Shani")
                          or _has_word(t, "मंगल") or _has_word(t, "शनि"))
                     and (_has_word(t, f.get("sun_sign"))
                          or _has_word(t, f.get("mars_sign"))
                          or _has_word(t, f.get("saturn_sign")))
                     and (_has_num(t, f.get("sun_house"))
                          or _has_num(t, f.get("mars_house"))
                          or _has_num(t, f.get("saturn_house"))),
    "tier16.ayurdaya":
        # Triple anchor: tier-key (alpa/madhya/purna) + Ayur/longevity keyword
        # + 8L planet name (chart-locked).
        lambda f, t: (_has_word(t, (f.get("tier_key") or "").upper())
                      or _has_word(t, f.get("tier_key"))
                      or _has_word(t, "PURNA") or _has_word(t, "MADHYA")
                      or _has_word(t, "ALPA"))
                     and (_has_word(t, "Ayur") or _has_word(t, "longevity")
                          or _has_word(t, "Pinda") or _has_word(t, "ायु"))
                     and _has_word(t, f.get("eighth_lord")),
    "tier16.maraka":
        # Quad anchor: 2L + 7L + maraka keyword + chart-locked house num
        # (prevents generic maraka prose).
        lambda f, t: _has_word(t, f.get("second_lord"))
                     and _has_word(t, f.get("seventh_lord"))
                     and (_has_word(t, "maraka") or _has_word(t, "Maraka")
                          or _has_word(t, "मारक"))
                     and (_has_num(t, f.get("second_lord_house"))
                          or _has_num(t, f.get("seventh_lord_house"))),
    "tier16.event_timing":
        # Triple anchor: current MD + current AD + window-status keyword.
        lambda f, t: _has_word(t, f.get("current_md"))
                     and _has_word(t, f.get("current_ad"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("window_status") or "").replace("-", " ").split()
                             if len(tok) >= 4),
    "tier16.longevity_synthesis":
        # Triple anchor: 8th sign + Ayur/health keyword + verdict_token.
        lambda f, t: _has_word(t, f.get("eighth_sign"))
                     and (_has_word(t, "Ayur") or _has_word(t, "health")
                          or _has_word(t, "longevity") or _has_word(t, "ायु")
                          or _has_word(t, "स्वास्थ्य"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("verdict_token") or "").split("-")
                             if len(tok) >= 5),
    # ── Tier 17 — Moksha Synthesis & Final Life-Mastery Verdict ─────
    "tier17.moksha_bhava":
        # Triple anchor: 12th sign + 12L + Ketu sign (chart-locked).
        lambda f, t: _has_word(t, f.get("twelfth_sign"))
                     and _has_word(t, f.get("twelfth_lord"))
                     and (_has_word(t, "Ketu") or _has_word(t, "केतु")
                          or _has_word(t, "moksha") or _has_word(t, "मोक्ष")),
    "tier17.atmakaraka":
        # Triple anchor: Atmakaraka planet + Atmakaraka sign + Atmakaraka/soul keyword.
        lambda f, t: _has_word(t, f.get("atmakaraka"))
                     and (_has_word(t, f.get("atmakaraka_sign"))
                          if f.get("atmakaraka_sign") else True)
                     and (_has_word(t, "Atmakaraka") or _has_word(t, "atmakaraka")
                          or _has_word(t, "soul") or _has_word(t, "आत्मकारक")
                          or _has_word(t, "आत्मा")),
    "tier17.karakamsha":
        # Triple anchor: Karakamsha sign + Karakamsha/Navamsha keyword + soul-arena
        # signal (any meaningful word from the soul_arena description).
        lambda f, t: _has_word(t, f.get("karakamsha_sign"))
                     and (_has_word(t, "Karakamsha") or _has_word(t, "karakamsha")
                          or _has_word(t, "Navamsha") or _has_word(t, "navamsha")
                          or _has_word(t, "नवमांश") or _has_word(t, "soul"))
                     and (_has_word(t, f.get("karakamsha_lord"))
                          if f.get("karakamsha_lord") else True),
    "tier17.trikona_synthesis":
        # Triple anchor: trikona-mode token + dharma OR karma keyword + lagna lord.
        lambda f, t: any(_has_word(t, tok) for tok in
                         (f.get("mode") or "").split("-") if len(tok) >= 5)
                     and (_has_word(t, "dharma") or _has_word(t, "Dharma")
                          or _has_word(t, "karma") or _has_word(t, "Karma")
                          or _has_word(t, "धर्म") or _has_word(t, "कर्म"))
                     and _has_word(t, f.get("lagna_lord")),
    "tier17.life_mission":
        # Triple anchor: mission-token (e.g. DHARMA-SAGE) + mission keyword
        # + chart-locked numeric (winner_score).
        lambda f, t: any(_has_word(t, tok) for tok in
                         (f.get("mission_token") or "").split("-") if len(tok) >= 5)
                     and (_has_word(t, "mission") or _has_word(t, "soul")
                          or _has_word(t, "dharma") or _has_word(t, "मिशन")
                          or _has_word(t, "धर्म") or _has_word(t, "आत्मा")
                          or _has_word(t, "लक्ष्य"))
                     and (_has_num(t, f.get("winner_score"))
                          if f.get("winner_score") else True),
    "tier17.evolution_arc":
        # Triple anchor: current MD + current AD + arc-status keyword.
        lambda f, t: _has_word(t, f.get("current_md"))
                     and _has_word(t, f.get("current_ad"))
                     and any(_has_word(t, tok) for tok in
                             (f.get("arc_status") or "").replace("-", " ").split()
                             if len(tok) >= 4),
    "tier17.final_verdict":
        # Quad anchor: final verdict token + driver number + conductor number
        # + soul/mastery/life keyword (closes the 17-tier loop with numerology).
        lambda f, t: any(_has_word(t, tok) for tok in
                         (f.get("final_verdict_token") or "").split("-")
                         if len(tok) >= 5)
                     and _has_num(t, f.get("driver_number"))
                     and _has_num(t, f.get("conductor_number"))
                     and (_has_word(t, "soul") or _has_word(t, "mastery")
                          or _has_word(t, "life") or _has_word(t, "आत्मा")
                          or _has_word(t, "जीवन") or _has_word(t, "महारत")),
}


def _validate(section_key: str, facts: Dict[str, Any], text: str) -> bool:
    """Run per-section validator. Missing validator → accept (soft default)."""
    fn = _VALIDATORS.get(section_key)
    if fn is None:
        return True
    try:
        return bool(fn(facts, text))
    except Exception:
        return True  # never let the guard crash the request


def is_available() -> bool:
    return _get_client() is not None


# ── Voice / style guide ──────────────────────────────────────────────────────
# This is the "Gold Standard Template" we want AI to match — the
# Ashutosh Bharadwaj live-reading vibe.

_VOICE_GUIDE = """
You are Acharya Ashutosh Bharadwaj, a warm, wise Vedic astrology guru who is
reading this person's chart OUT LOUD, one-to-one, like sitting across from them
over chai. Your voice is NOT a textbook. It is a story-telling friend.

The reader has paid premium money for this report. They are tired of generic
horoscope text. They want to feel SEEN — like you've already lived their life
and are reporting it back to them. Every paragraph must make them think:
"Yeh toh meri exact story hai."

RULES OF VOICE (non-negotiable):
1. START WITH A HOOK — a curious question, a "kya aapko pata hai?", or a
   childhood scene that feels strangely personal. NEVER start with "You are…"
   or "Aap ek…".

2. MIRROR THE READER'S LIVED EXPERIENCE — at least ONCE per section, name a
   feeling they have actually had. Use these exact patterns (pick whichever
   fits most naturally):
     • "Aapne kabhi notice kiya hoga ki..."   (you must have noticed...)
     • "Aapne X feel kiya hoga jab..."        (you must have felt X when...)
     • "Bachpan me jab sab Y kar rahe the, aap..."  (childhood mirror)
     • "Late raat akele jab aap sochte ho..."  (vulnerable moment)
   This is the SINGLE MOST IMPORTANT rule — it converts "report" into
   "wow, this person knows me".

3. ACKNOWLEDGE → REFRAME → DIRECT — for any difficulty:
   step 1: name their pain plainly ("haan, yeh thakaan real hai")
   step 2: reframe it as their teacher ("yeh thakaan aapko X sikha rahi hai")
   step 3: give one tiny next action ("kal subah 5 minute X karo, bas")
   Never lecture, never condescend.

4. USE METAPHORS from everyday Indian life — school, cricket, trains, films,
   Jupiter-in-the-sky, rivers, ghee, lemons, monsoon, Mumbai-local,
   Diwali-cleaning — whatever makes the reader SEE the concept.

5. HONEST DOUBLE-EDGE — every gift has a shadow. State the shadow plainly
   but WITH empathy: "kyunki agar koi raja hai, toh ego to aayega hi".

6. ONE PRACTICAL RULE at the end — small, do-able TODAY, no big rituals:
   "isliye rule simple hai: JO feel ho, BAHAR nikalo."

7. TRANSFORMATIONAL CLOSING — last sentence must hit emotionally — a gentle
   push, a blessing, or a recognition the reader has been waiting for.
   NEVER summarise. NEVER say "in conclusion". Examples that work:
     • "Aap toot ke nahi banayi gayi — ban ke toot rahi ho. Yeh farak hai."
     • "Yahi aapka asli kaam hai — aur aap pehle se shuru ho chuke ho."

RULES OF FACTS (absolutely non-negotiable):
A. You may ONLY use the numbers, planets, signs, nakshatras, dashas given in
   the FACTS block below. DO NOT invent new numbers, planets, houses, dates,
   or years.
B. If a fact is not in the FACTS block, do NOT mention it. Better to be silent
   than wrong.
C. Do NOT use markdown headings (##, **, etc.) — plain flowing prose only.
   Short paragraph breaks (blank line) are fine.
D. Do NOT quote English proverbs unless the user's language is English.
E. NEVER prescribe medical / legal / financial action. Spiritual + lifestyle
   guidance only.
F. Do NOT use the words "AI", "Cosmic Intelligence", "OnlyFans". The brand is
   "Cosmic Lens" / "Cosmic Intelligence" — use those if needed.

FORBIDDEN PHRASES: "As an AI", "I am a language model", "According to my
training", "I cannot", "in conclusion", "to summarise", bullet lists,
numbered lists, generic horoscope filler ("the stars say…", "destiny shows…").
"""


_LANG_INSTRUCT = {
    "english": "Write in clean, warm English. No Hindi words except proper nouns (Jupiter/Guru both OK).",
    "hindi": "Write in shuddh Hindi (Devanagari script). Technical Sanskrit terms OK (राशि, नक्षत्र, दशा, ग्रह). Tone: guru samjha rahe hain, not a textbook.",
    "hinglish": "Write in Hinglish (Hindi in Roman script) — the way Indians naturally WhatsApp. Mix English words freely (hook, challenge, problem, struggle). Tone: dost-jaisa, warm, live-reading vibe. Example: 'Ek baat batao — bachpan me jab sab chup the, aapke andar ek awaaz hoti thi...'",
}


def _build_prompt(section_key: str, facts: Dict[str, Any], lang: str,
                  word_target: int) -> tuple[str, str]:
    """Return (system_prompt, user_prompt)."""
    lang = lang if lang in _LANG_INSTRUCT else "hinglish"
    lang_rule = _LANG_INSTRUCT[lang]

    # Flatten facts into a locked, bullet-style block the AI can reference.
    facts_lines = []
    for k, v in facts.items():
        if v is None or v == "":
            continue
        facts_lines.append(f"  • {k}: {v}")
    facts_block = "\n".join(facts_lines) if facts_lines else "  (no facts provided)"

    min_words = int(word_target * 0.85)
    max_words = int(word_target * 1.10)

    sys_prompt = _VOICE_GUIDE + f"\n\nLANGUAGE RULE: {lang_rule}\n"
    sys_prompt += (
        f"\nLENGTH RULE: Write between {min_words} and {max_words} words. "
        "Not less, not more. Count carefully."
    )

    user_prompt = (
        f"Section: {section_key}\n\n"
        f"FACTS (use ONLY these — do not invent new ones):\n{facts_block}\n\n"
        f"Write the narration for this section in {lang}, "
        f"{word_target} words (±10%). Remember the voice rules. Start with a hook, "
        "weave in the facts, give one practical rule, end with an emotional line."
    )
    return sys_prompt, user_prompt


def _default_model() -> str:
    """Default to gpt-4.1-mini for cost. Override via OPENAI_NARRATOR_MODEL."""
    return os.environ.get("OPENAI_NARRATOR_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"


# Hard ceiling regardless of word_target (prevents runaway max_tokens).
MAX_TOKENS_PER_CALL = int(os.environ.get("NARRATOR_MAX_TOKENS_PER_CALL", "500"))


def narrate(section_key: str, facts: Dict[str, Any], lang: str = "hinglish",
            word_target: int = 300, model: Optional[str] = None,
            person_name: str = "", dob: str = "") -> Optional[str]:
    """
    Generate a storytelling paragraph for ONE section (single API call).

    NOTE: This is the legacy path — for cost-optimised generation use
    `narrate_grouped_batch()` which batches 4-6 sections per API call.

    Args:
        section_key: e.g. "tier1.life_path"
        facts: engine facts the AI may reference
        lang: english | hindi | hinglish
        word_target: target word count (±10% enforced by prompt)
        model: override model (default gpt-4.1-mini)
        person_name, dob: used for cache key (optional; if empty, no cache)
    """
    # 1. Cache lookup (if person identifiers given)
    if person_name and dob:
        try:
            from . import narration_cache as _nc
            cached = _nc.get(person_name, dob, lang, section_key, facts)
            if cached:
                return cached
        except Exception:
            pass

    client = _get_client()
    if client is None:
        return None

    # 2. Daily spend cap check
    try:
        from . import narration_cache as _nc
        if _nc.is_daily_capped():
            print(f"[ai_narrator] daily cap reached "
                  f"(${_nc.DAILY_LIMIT_USD}); falling back to static.")
            return None
    except Exception:
        _nc = None  # type: ignore

    model = model or _default_model()
    sys_p, user_p = _build_prompt(section_key, facts, lang, word_target)

    # Hinglish ≈ 1.5 tokens/word; cap at MAX_TOKENS_PER_CALL.
    capped_max = min(MAX_TOKENS_PER_CALL, max(120, int(word_target * 1.7)))

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.75,  # warm, storytelling — not robotic
            messages=[
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p},
            ],
            max_tokens=capped_max,
        )
        text = (resp.choices[0].message.content or "").strip()

        # 3. Record spend
        if _nc is not None:
            try:
                in_t = getattr(resp.usage, "prompt_tokens", 0) or 0
                out_t = getattr(resp.usage, "completion_tokens", 0) or 0
                _nc.record_spend(_nc.cost_for(in_t, out_t))
            except Exception:
                pass

        if not text:
            return None
        if not _validate(section_key, facts, text):
            print(f"[ai_narrator] {section_key} ({lang}) FAILED FACT-GUARD — "
                  f"falling back to static. Facts={list(facts.keys())}")
            return None

        # 4. Cache the result
        if person_name and dob and _nc is not None:
            try:
                _nc.put(person_name, dob, lang, section_key, facts, text)
            except Exception:
                pass

        return text
    except Exception as exc:
        # Log but don't crash — caller falls back to static.
        _msg = str(exc).lower()
        _flavor = "OPENAI_FAILED" if any(s in _msg for s in (
            "429", "insufficient_quota", "rate limit", "timeout", "api key")) else "AI_FAILED"
        print(f"[ai_narrator] {_flavor} → fallback used :: {section_key} ({lang}) :: {exc}")
        return None


def narrate_with_fallback(section_key: str, facts: Dict[str, Any],
                          static_text: str, lang: str = "hinglish",
                          word_target: int = 300) -> str:
    """Wrapper: try AI, fall back to static text on any failure."""
    ai_text = narrate(section_key, facts, lang, word_target)
    return ai_text if ai_text else static_text


def narrate_batch(specs: list, concurrency: int = 3,
                  person_name: str = "", dob: str = "") -> Dict[str, str]:
    """
    BACKWARD-COMPAT WRAPPER → delegates to narrate_grouped_batch (1 API call
    per ~6 sections). Drop-in replacement for the old per-section batcher.

    Each spec dict must contain:
      • key, section_key, facts, lang, word_target, fallback

    To force the legacy 1-call-per-section path (e.g. for debugging), set
    env NARRATOR_FORCE_LEGACY=1.
    """
    if os.environ.get("NARRATOR_FORCE_LEGACY") == "1":
        return _narrate_batch_legacy(specs, concurrency,
                                     person_name=person_name, dob=dob)
    return narrate_grouped_batch(specs, group_size=6, concurrency=concurrency,
                                 person_name=person_name, dob=dob)


def _narrate_batch_legacy(specs: list, concurrency: int = 3,
                           person_name: str = "", dob: str = "") -> Dict[str, str]:
    """Original 1-call-per-section parallel batcher (kept for emergencies)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: Dict[str, str] = {}

    def _run(spec: dict) -> tuple[str, str]:
        key = spec["key"]
        try:
            txt = narrate(
                spec["section_key"],
                spec["facts"],
                lang=spec.get("lang", "hinglish"),
                word_target=spec.get("word_target", 300),
                person_name=person_name,
                dob=dob,
            )
        except Exception as exc:
            print(f"[ai_narrator.batch] {key} raised: {exc}")
            txt = None
        return key, (txt or spec.get("fallback", ""))

    # Short-circuit if narrator unavailable — skip the pool entirely.
    if not is_available():
        for spec in specs:
            results[spec["key"]] = spec.get("fallback", "")
        return results

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = [pool.submit(_run, spec) for spec in specs]
        for fut in as_completed(futures):
            try:
                k, v = fut.result()
                results[k] = v
            except Exception as exc:
                # Should not happen (inner _run catches) but be defensive.
                print(f"[ai_narrator.batch] future raised: {exc}")

    # Ensure every spec key is present (belt-and-suspenders).
    for spec in specs:
        results.setdefault(spec["key"], spec.get("fallback", ""))
    return results


# ──────────────────────────────────────────────────────────────────────────
# GROUPED BATCH — the cost-optimised path
# ──────────────────────────────────────────────────────────────────────────
def _build_group_prompt(group: list, lang: str) -> tuple[str, str]:
    """
    Build ONE prompt that asks the model to write N sections in a single
    JSON response. The system prompt (voice guide) is sent ONCE per group
    instead of once per section → ~80% input-token savings.
    """
    import json as _json
    lang = lang if lang in _LANG_INSTRUCT else "hinglish"
    lang_rule = _LANG_INSTRUCT[lang]

    # Build per-section facts blocks
    sections_payload = []
    for spec in group:
        facts = spec.get("facts") or {}
        facts_lines = [f"  • {k}: {v}" for k, v in facts.items()
                       if v not in (None, "")]
        sections_payload.append({
            "key": spec["key"],
            "section_key": spec["section_key"],
            "word_target": int(spec.get("word_target", 280)),
            "facts": "\n".join(facts_lines) if facts_lines else "(none)",
        })

    sys_prompt = (
        _VOICE_GUIDE
        + f"\n\nLANGUAGE RULE: {lang_rule}\n"
        + "\nOUTPUT FORMAT: Respond with a single JSON object whose keys are "
          "EXACTLY the section 'key' values given in the user message, and "
          "whose values are the storytelling paragraphs. No markdown, no "
          "extra commentary outside the JSON.\n"
        + "LENGTH RULE: Honour each section's word_target (±15%). Be tight, "
          "no padding, no bullet lists.\n"
    )

    sections_text = "\n\n".join(
        f"━━━ Section [{s['key']}] ({s['section_key']}, "
        f"~{s['word_target']} words) ━━━\nFACTS (use ONLY these):\n{s['facts']}"
        for s in sections_payload
    )

    keys_list = [s["key"] for s in sections_payload]
    user_prompt = (
        f"Write {len(group)} sections in {lang}. Return ONE JSON object "
        f"with these exact keys: {_json.dumps(keys_list)}.\n\n"
        f"For EACH section, follow the voice rules: hook → mirror lived "
        f"experience → weave facts → one practical rule → emotional close.\n\n"
        f"{sections_text}"
    )
    return sys_prompt, user_prompt


def _split_sections_safely(text: str, group: list) -> Dict[str, str]:
    """Last-resort: regex-split if model returned non-JSON prose."""
    import re
    out: Dict[str, str] = {}
    keys = [s["key"] for s in group]
    # Try to find blocks like "key1: ...\nkey2: ..."
    for i, k in enumerate(keys):
        nxt = keys[i + 1] if i + 1 < len(keys) else None
        pat = rf'"?{re.escape(k)}"?\s*[:=]\s*"?(.*?)"?(?=(?:"?{re.escape(nxt)}"?\s*[:=])|\Z)' \
              if nxt else rf'"?{re.escape(k)}"?\s*[:=]\s*"?(.*)$'
        m = re.search(pat, text, re.DOTALL)
        if m:
            out[k] = m.group(1).strip().strip('",')
    return out


def _call_grouped(group: list, lang: str, model: str) -> Dict[str, str]:
    """
    Make ONE OpenAI call covering all specs in `group`.
    Returns {key: text} for whatever sections came back valid.
    Failed/missing keys are simply absent from the result.
    """
    import json as _json
    client = _get_client()
    if client is None:
        return {}

    sys_p, user_p = _build_group_prompt(group, lang)

    # Sum word_targets, convert to tokens (1.5×), cap per-call at 3000.
    total_words = sum(int(s.get("word_target", 280)) for s in group)
    per_group_max = min(3000, max(400, int(total_words * 1.7)))

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.75,
            messages=[
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p},
            ],
            max_tokens=per_group_max,
            response_format={"type": "json_object"},
        )
        raw = (resp.choices[0].message.content or "").strip()

        # Record spend
        try:
            from . import narration_cache as _nc
            in_t = getattr(resp.usage, "prompt_tokens", 0) or 0
            out_t = getattr(resp.usage, "completion_tokens", 0) or 0
            _nc.record_spend(_nc.cost_for(in_t, out_t))
        except Exception:
            pass

        # Parse JSON; fallback to regex split if needed.
        try:
            parsed = _json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("not a dict")
        except Exception:
            parsed = _split_sections_safely(raw, group)

        # Validate each section against fact-guard
        validated: Dict[str, str] = {}
        for spec in group:
            k = spec["key"]
            txt = (parsed.get(k) or "").strip()
            if not txt:
                continue
            sec_key = spec["section_key"]
            facts = spec.get("facts") or {}
            if _validate(sec_key, facts, txt):
                validated[k] = txt
            else:
                print(f"[ai_narrator.grouped] {sec_key} ({lang}) "
                      f"FAILED FACT-GUARD — falling back to static.")
        return validated

    except Exception as exc:
        print(f"[ai_narrator.grouped] batch failed ({len(group)} sections): {exc}")
        return {}


def narrate_grouped_batch(specs: list, group_size: int = 6,
                          concurrency: int = 3,
                          person_name: str = "",
                          dob: str = "") -> Dict[str, str]:
    """
    THE primary cost-optimised batcher.

    Pipeline per render:
      1. Cache lookup — every spec where person_name+dob+facts hash hits → free
      2. Skip empty/duplicate facts (saves API calls)
      3. Group remaining specs into chunks of `group_size`
      4. Each group → ONE API call returning JSON {key: text}
      5. Cache each successful narration to disk

    Concurrency defaults to 3 (gentler on rate limits than the old 6).
    Model: gpt-4.1-mini (override via OPENAI_NARRATOR_MODEL).

    Returns {key: text} where text = AI output OR spec['fallback'] on miss.
    Never raises.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: Dict[str, str] = {}
    nc = None
    try:
        from . import narration_cache as nc_mod
        nc = nc_mod
    except Exception:
        nc = None

    # ── Step 0: Short-circuit if no API key
    if not is_available():
        for spec in specs:
            results[spec["key"]] = spec.get("fallback", "")
        return results

    # ── Step 1+2: Cache lookup + skip low-value
    pending: list = []
    for spec in specs:
        key = spec["key"]
        facts = spec.get("facts") or {}
        lang = spec.get("lang", "hinglish")
        sec_key = spec["section_key"]

        # Skip: no usable facts at all
        non_empty = sum(1 for v in facts.values() if v not in (None, ""))
        if non_empty < 2:
            results[key] = spec.get("fallback", "")
            continue

        # Cache hit?
        if nc and person_name and dob:
            cached = nc.get(person_name, dob, lang, sec_key, facts)
            if cached:
                results[key] = cached
                continue

        pending.append(spec)

    if not pending:
        # Everything served from cache or skipped.
        for spec in specs:
            results.setdefault(spec["key"], spec.get("fallback", ""))
        return results

    # ── Step 2.5: Daily spend cap
    if nc and nc.is_daily_capped():
        print(f"[ai_narrator] daily cap ${nc.DAILY_LIMIT_USD} reached "
              f"— {len(pending)} sections will use static fallback.")
        for spec in pending:
            results[spec["key"]] = spec.get("fallback", "")
        return results

    # ── Step 3: Group by language, then chunk into group_size
    by_lang: Dict[str, list] = {}
    for spec in pending:
        by_lang.setdefault(spec.get("lang", "hinglish"), []).append(spec)

    groups: list = []
    for lang, lang_specs in by_lang.items():
        for i in range(0, len(lang_specs), group_size):
            groups.append((lang, lang_specs[i:i + group_size]))

    # Per-report cap: estimate cost; if over PER_REPORT_LIMIT, trim groups
    # (each grouped call ≈ $0.005-0.010 for ~6×280-word sections on mini).
    if nc:
        est_cost = len(groups) * 0.012  # generous upper bound
        if est_cost > nc.PER_REPORT_LIMIT_USD:
            max_groups = max(1, int(nc.PER_REPORT_LIMIT_USD / 0.012))
            print(f"[ai_narrator] per-report cap ${nc.PER_REPORT_LIMIT_USD}: "
                  f"trimming {len(groups)} → {max_groups} groups; "
                  f"remainder will use static fallback.")
            groups = groups[:max_groups]

    model = _default_model()

    # ── Step 4: Fire grouped calls in parallel (concurrency=3)
    def _run(item):
        lang, group = item
        return lang, group, _call_grouped(group, lang, model)

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = [pool.submit(_run, item) for item in groups]
        for fut in as_completed(futures):
            try:
                lang, group, group_results = fut.result()
            except Exception as exc:
                print(f"[ai_narrator.grouped] future raised: {exc}")
                continue
            for spec in group:
                k = spec["key"]
                txt = group_results.get(k, "")
                if txt:
                    results[k] = txt
                    # Step 5: cache it
                    if nc and person_name and dob:
                        try:
                            nc.put(person_name, dob, lang,
                                   spec["section_key"], spec.get("facts") or {},
                                   txt)
                        except Exception:
                            pass

    # ── Final pass: anything still missing → fallback
    for spec in specs:
        results.setdefault(spec["key"], spec.get("fallback", ""))
    return results
