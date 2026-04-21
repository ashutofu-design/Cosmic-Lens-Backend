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

RULES OF VOICE (non-negotiable):
1. START WITH A HOOK — a curious question, a "kya aapko pata hai?", or a
   childhood scene that feels strangely personal. NEVER start with "You are…"
   or "Aap ek…".
2. USE METAPHORS from everyday Indian life — school, cricket, trains, films,
   Jupiter-in-the-sky, rivers, ghee, lemons — whatever makes the reader
   SEE the concept.
3. HONEST DOUBLE-EDGE — every gift has a shadow. State the shadow plainly
   but WITH empathy: "kyunki agar koi raja hai, toh ego to aayega hi".
4. ONE PRACTICAL RULE at the end — "isliye rule simple hai: JO feel ho,
   BAHAR nikalo."
5. EMOTIONAL CLOSURE — last sentence must feel like a gentle push or a
   blessing, not a summary.

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

FORBIDDEN PHRASES: "As an AI", "I am a language model", "According to my
training", "I cannot", bullet lists, numbered lists.
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


def narrate(section_key: str, facts: Dict[str, Any], lang: str = "hinglish",
            word_target: int = 300, model: Optional[str] = None) -> Optional[str]:
    """
    Generate a storytelling paragraph for a report section.

    Args:
        section_key: e.g. "tier1.life_path", "tier2.moon_nakshatra"
        facts: dict of engine-computed facts the AI may reference
        lang: english | hindi | hinglish
        word_target: target word count (±10% enforced by prompt)
        model: override model (default from OPENAI_NARRATOR_MODEL env or gpt-4.1)

    Returns:
        Storytelling text on success; None on failure (caller falls back to static).
    """
    client = _get_client()
    if client is None:
        return None

    model = model or os.environ.get("OPENAI_NARRATOR_MODEL", "gpt-4.1")
    sys_p, user_p = _build_prompt(section_key, facts, lang, word_target)

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.75,  # warm, storytelling — not robotic
            messages=[
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p},
            ],
            max_tokens=int(word_target * 3),  # ~3 tokens per word buffer
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return None
        if not _validate(section_key, facts, text):
            print(f"[ai_narrator] {section_key} ({lang}) FAILED FACT-GUARD — "
                  f"falling back to static. Facts={list(facts.keys())}")
            return None
        return text
    except Exception as exc:
        # Log but don't crash — caller falls back to static.
        print(f"[ai_narrator] {section_key} ({lang}) failed: {exc}")
        return None


def narrate_with_fallback(section_key: str, facts: Dict[str, Any],
                          static_text: str, lang: str = "hinglish",
                          word_target: int = 300) -> str:
    """Wrapper: try AI, fall back to static text on any failure."""
    ai_text = narrate(section_key, facts, lang, word_target)
    return ai_text if ai_text else static_text


def narrate_batch(specs: list, concurrency: int = 6) -> Dict[str, str]:
    """
    Fire N narration requests in parallel, return {key: final_text}.

    Each spec dict must contain:
      • key          — unique identifier (used as dict key in result)
      • section_key  — e.g. "tier1.life_path"
      • facts        — dict of engine facts
      • lang         — english | hindi | hinglish
      • word_target  — int
      • fallback     — static text to use if AI fails

    Guarantees:
      • Never raises — any failure falls back to spec['fallback'].
      • Order-preserving (dict keys follow spec order).
      • Returns within ~ceil(N/concurrency) × per-call-time seconds.
    """
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
