"""
risk_text_ai.py — Cosmic Lens Risk Radar text generation via Cosmic Intelligence.

Generates the 5-field KYA RISK / DHYAN / AVOID / KARNA / UPAY guidance for
each Risk Radar trigger using a friendly Hinglish voice. Brand voice rules:

  - NEVER mention AI / GPT / LLM / model / algorithm / technology
  - NEVER mention raw planet names (Mars, Saturn, Mercury, etc.) or technical
    Sanskrit jargon (dasha, antardasha, tithi, nakshatra, rahukaal) in the
    OUTPUT TEXT — use generic terms like "today's energy", "cosmic vibration",
    "current cycle", "background pressure", "sensitive samay window".
  - EXCEPTION: in the `upay` field, deity names (Hanuman ji, Shani Dev,
    Surya, Maa Lakshmi), mantras ("Om Sham Shanaishcharaya Namah"), and
    traditional remedies (kaale til daan, ghee ka diya, gulab jal) ARE
    allowed and encouraged — these are user-expected Vedic remedies.
  - Hinglish only (Roman script Hindi + English mix), supportive tone, never
    preachy or fearful, no destiny language.

Caching: in-process dict keyed on trigger. 12 triggers max → at most one
generation per trigger per server process. Same trigger = same text
reused across users (acts like a smart template library that fills
itself on demand).

Engineering fallback: if AI call fails or OPENAI_API_KEY is unavailable,
returns None — caller (risk_text_engine._resolve_text) falls back to the
deterministic _TEXT_MAP so the UI never shows a broken card.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

log = logging.getLogger("risk_text_ai")

# ── Severity bands + per-day variants ───────────────────────────────────
# Each trigger is generated in TWO tone bands so the same cosmic signal
# reads differently when it's a mild vs. a strong day:
#   - "mid"  : softer, calmer language for moderate days
#   - "high" : direct, stronger language for genuinely heightened windows
# Within each (trigger, band) we cache N=3 phrasing VARIANTS so consecutive
# days with the same dominant trigger don't show identical text — caller
# rotates by `day_idx % N`. (Low-severity days don't use AI at all — they
# render the engineering neutral bank in risk_text_engine.)
_BANDS = ("mid", "high")
_VARIANTS_PER_BAND = 3

# Module-level cache. Key = (trigger, lang) tuple. Value = {band -> [variant_dict_1..N]}.
# Each (trigger, lang) pair caches its own bundle so the same cosmic signal
# can be served in any of the supported UI languages without re-prompting.
_AI_CACHE: Dict[tuple, Dict[str, List[Dict[str, str]]]] = {}
_CACHE_LOCK = threading.Lock()

# In-flight dedup: per-(trigger, lang) Event so concurrent first-hit + prewarm
# don't duplicate OpenAI calls. Reader takes the lock, checks cache, otherwise
# either becomes the writer (creates Event, releases lock, generates) or
# waits on the existing Event.
_INFLIGHT: Dict[tuple, threading.Event] = {}

# ── Supported UI languages → AI prompt directive ──────────────────────────
# Maps the mobile app's UILang code (matching lib/i18n.ts UILang) to a
# natural-language directive injected into the AI prompt so the model
# writes its 6-field guidance in the user's selected language. "hn"
# (Hinglish) is the original brand-voice default; everything else asks
# the model to translate while preserving voice + structure.
DEFAULT_LANG = "hn"
_LANG_DIRECTIVES: Dict[str, str] = {
    "hn": (
        "HINGLISH ONLY — Roman-script Hindi mixed with English "
        "(conversational Mumbai / Delhi style). NOT pure Hindi devanagari. "
        "NOT pure English.\n"
        "  - Good: \"Aaj reactions slow karein, ek pause-breath-respond rule follow karein.\"\n"
        "  - Bad (pure English): \"Today, slow your reactions and follow a pause-breath-respond rule.\"\n"
        "  - Bad (pure Hindi): \"आज प्रतिक्रिया धीमी करें।\""
    ),
    "en": (
        "ENGLISH ONLY — clear, friendly conversational English (US style). "
        "Warm and supportive, like a wise older sibling. Do NOT mix Hindi / "
        "Hinglish words in the 5 guidance fields. EXCEPTION: in the `upay` "
        "field, traditional remedy names (Hanuman Chalisa, kaale til daan, "
        "ghee diya, jal arghya) MAY remain in their original form because "
        "users expect them — but explain them briefly in English."
    ),
    "hi": (
        "PURE HINDI (DEVANAGARI SCRIPT) ONLY — conversational Hindi, "
        "warm and supportive. Do NOT mix Roman script or English words in "
        "the 5 guidance fields. EXCEPTION: in the `upay` field, mantra text "
        "(\"ॐ शं शनैश्चराय नमः\") and remedy names should appear in Devanagari."
    ),
    "mr": (
        "PURE MARATHI (DEVANAGARI SCRIPT) ONLY — conversational Marathi, "
        "warm and supportive. Do NOT mix Roman script or English words in "
        "the 5 guidance fields. EXCEPTION: traditional mantras and deity "
        "names in the `upay` field stay in Devanagari."
    ),
    "bn": (
        "PURE BENGALI (BENGALI SCRIPT) ONLY — conversational Bengali, "
        "warm and supportive. Do NOT mix Roman script or English words "
        "in the 5 guidance fields."
    ),
    "ta": (
        "PURE TAMIL (TAMIL SCRIPT) ONLY — conversational Tamil, warm "
        "and supportive. Do NOT mix Roman script or English words in "
        "the 5 guidance fields."
    ),
    "te": (
        "PURE TELUGU (TELUGU SCRIPT) ONLY — conversational Telugu, warm "
        "and supportive. Do NOT mix Roman script or English words in "
        "the 5 guidance fields."
    ),
    "gu": (
        "PURE GUJARATI (GUJARATI SCRIPT) ONLY — conversational Gujarati, "
        "warm and supportive."
    ),
    "kn": (
        "PURE KANNADA (KANNADA SCRIPT) ONLY — conversational Kannada, "
        "warm and supportive."
    ),
    "ml": (
        "PURE MALAYALAM (MALAYALAM SCRIPT) ONLY — conversational Malayalam, "
        "warm and supportive."
    ),
    "pa": (
        "PURE PUNJABI (GURMUKHI SCRIPT) ONLY — conversational Punjabi, "
        "warm and supportive."
    ),
    "or": (
        "PURE ODIA (ODIA SCRIPT) ONLY — conversational Odia, warm and "
        "supportive."
    ),
    "as": (
        "PURE ASSAMESE (ASSAMESE SCRIPT) ONLY — conversational Assamese, "
        "warm and supportive."
    ),
    # Global languages
    "zh": "PURE SIMPLIFIED CHINESE (汉字) ONLY — warm, conversational tone.",
    "es": "PURE SPANISH (Latin American conversational style) ONLY — warm, supportive tone.",
    "ar": "PURE ARABIC (MSA, conversational) ONLY — warm, supportive tone.",
    "fr": "PURE FRENCH (conversational, friendly) ONLY — warm, supportive tone.",
    "pt": "PURE PORTUGUESE (Brazilian conversational style) ONLY — warm, supportive tone.",
    "de": "PURE GERMAN (conversational, du-form) ONLY — warm, supportive tone.",
    "ru": "PURE RUSSIAN (conversational) ONLY — warm, supportive tone.",
    "ja": "PURE JAPANESE (conversational, polite ます-form) ONLY — warm, supportive tone.",
    "id": "PURE BAHASA INDONESIA (conversational) ONLY — warm, supportive tone.",
    "ko": "PURE KOREAN (conversational, 해요-style) ONLY — warm, supportive tone.",
    "tr": "PURE TURKISH (conversational) ONLY — warm, supportive tone.",
}


def _normalize_lang(lang: Optional[str]) -> str:
    """Coerce an incoming language code to a supported key, defaulting to Hinglish.

    Accepts None, empty string, unknown codes — all collapse to ``DEFAULT_LANG``
    so callers never have to pre-validate. Case-insensitive.
    """
    if not lang:
        return DEFAULT_LANG
    code = str(lang).strip().lower()
    return code if code in _LANG_DIRECTIVES else DEFAULT_LANG

# Track if a prewarm thread is already running so we don't spawn duplicates.
_PREWARM_STARTED = False
_PREWARM_LOCK = threading.Lock()

# Brand-voice guardrails: words that must NEVER appear in any output field.
_FORBIDDEN_GLOBAL = (
    " ai ", "ai-", "gpt", "chatgpt", "llm", "language model", "openai",
    "machine learning", "algorithm", "trained on", "neural", "artificial intelligence",
)
# Words allowed only in the `upay` field (deity names, mantra references).
# In the other 5 fields these technical / planetary names must NOT leak.
_FORBIDDEN_NON_UPAY = (
    "mars", "saturn", "jupiter", "mercury", "venus", "rahu", "ketu",
    "mangal", "shani", "guru", "brihaspati", "budh", "shukra",
    "dasha", "antardasha", "mahadasha", "pratyantar",
    "nakshatra", "tithi", "rahukaal", "kantaka", "sade sati", "naidhana",
    "vipat", "pratyak", "amavasya", "rikta", "chandrashtama",
)
# Hard length caps per field (characters). AI tends to be terse with our
# prompt, but a runaway response shouldn't blow out card layout.
_MAX_LEN_CATEGORY = 60
_MAX_LEN_FIELD = 280

# Required output fields.
_REQUIRED_KEYS = (
    "category",
    "kya_risk_hai",
    "kya_dhyan_rakhna_hai",
    "kya_avoid_karna_hai",
    "kya_karna_hai",
    "upay",
)

# Internal briefs (engine-side context for the model). These are NOT shown
# to the user — they tell the model what the trigger means so it can write
# appropriate guidance. Triggers + briefs MUST stay in sync with
# risk_text_engine._TEXT_MAP keys.
# Each trigger has (a) an internal brief explaining what cosmic situation it
# represents, and (b) an upay_hint telling the AI which traditional Vedic
# remedy is canonically appropriate for that signal — so the model picks the
# right deity / mantra / daan for the right energy.
_TRIGGER_BRIEFS: Dict[str, Dict[str, str]] = {
    "volatile_day": {
        "brief": (
            "A day with multiple negative cosmic signals stacked. Mixed "
            "energy throughout — moments of ease alternating with heavy "
            "moments. User needs to stay anchored against ups and downs."
        ),
        "upay_hint": (
            "Grounding remedies — deep breathing pranayam, ek glass paani "
            "mein chutki haldi, light meditation. Body-grounding focus."
        ),
    },
    "chandrashtama": {
        "brief": (
            "Moon is transiting the 8th lunar mansion from the user's natal "
            "Moon — a day of heightened emotional sensitivity. Small things "
            "may feel big; emotional clarity is reduced."
        ),
        "upay_hint": (
            "Moon-cooling remedies — gulab jal in water, white chandan "
            "tilak, Chandra mantra 'Om Som Somaya Namah' 11 baar, sheetal "
            "(cooling) practices. Deity: Chandra Dev / Maa."
        ),
    },
    "tara_naidhana": {
        "brief": (
            "The user's daily Tara Bal is at the worst position (Naidhana / "
            "Vadha). A reflective, slow-pace day — energy is in reserve "
            "mode, new ventures will feel stuck."
        ),
        "upay_hint": (
            "Hanuman Chalisa ek baar shaam ko, ghee ka diya. Hanuman ji "
            "softens reflective Tara energy."
        ),
    },
    "saturn_heavy": {
        "brief": (
            "User is in a heavy Saturn phase (Sade Sati Madhya or Ashtam "
            "Shani). Background sense of heavy responsibility, fatigue, "
            "slow progress, and possible friction with authority figures."
        ),
        "upay_hint": (
            "Shani Dev remedies — 'Om Sham Shanaishcharaya Namah' 11 baar, "
            "Saturday ko kaale til ya sarso ka tel daan, kisi needy ko "
            "khaana khilana, peepal ke neeche diya."
        ),
    },
    "mars_active": {
        "brief": (
            "Mars energy is afflicting key life houses or in a conflict "
            "aspect. Day is anger / frustration / impulsiveness prone — "
            "sharp words, road rage, office and family conflicts more "
            "likely."
        ),
        "upay_hint": (
            "Hanuman ji remedies — Hanuman Chalisa subah, Tuesday ko laal "
            "masoor dal kisi needy ko daan, Mangal mantra. Hanuman ji "
            "Mangal energy ko balance karte hain."
        ),
    },
    "tara_mild": {
        "brief": (
            "Tara Bal is at Vipat or Pratyak position — a mild mental-drain "
            "day. Overthinking and tiredness more likely; productivity "
            "below normal."
        ),
        "upay_hint": (
            "Mind-reset remedies — 10 min anulom-vilom pranayam shaam ko, "
            "ek diya ghar mein. Calm-down focus."
        ),
    },
    "pd_weak": {
        "brief": (
            "Pratyantar Dasha lord is weak — effort versus results "
            "imbalance. Effort continues but visible results are delayed; "
            "follow-ups may go silent; small obstacles."
        ),
        "upay_hint": (
            "Patience-building — apne ishtadev ka 5 min dhyan subah, "
            "Ganesh ji ka smaran obstacles ke liye."
        ),
    },
    "amavasya": {
        "brief": (
            "Tithi is Amavasya (new moon) — naturally introspective, "
            "low-energy day. Body is asking for rest; not a day to start "
            "new things."
        ),
        "upay_hint": (
            "Pitr remedies — shaam ko ghee ka diya north-east mein, "
            "pitru-tarpan thoughts, ancestral peace focus."
        ),
    },
    "saturn_mild": {
        "brief": (
            "User is in Sade Sati Phase 1 / Phase 3 or Kantaka Shani — "
            "background pressure that is steady but not heavy. Discipline "
            "and consistency carry the day."
        ),
        "upay_hint": (
            "Shani Dev light remedies — Saturday ko kaale til + sarso ka "
            "tel kisi shani mandir mein, discipline-driven daily action as "
            "main upay."
        ),
    },
    "tithi_rikta": {
        "brief": (
            "Tithi is Rikta (4 / 9 / 14) — a natural energy-drain day. "
            "Heavy commitments will feel like a burden; less is more."
        ),
        "upay_hint": (
            "Body-restore remedies — shaam ko warm haldi-doodh, hydration, "
            "early sleep, light saatvik food."
        ),
    },
    "rahukal_active": {
        "brief": (
            "The day's Rahukaal time window is currently active or "
            "relevant. A sensitive ~1.5 hour window during which "
            "decisions, signatures, and new starts often bring later "
            "complications."
        ),
        "upay_hint": (
            "Protective remedies during Rahukaal — Hanuman Chalisa or Maha "
            "Mrityunjaya 11 baar, Hanuman ji ka smaran. Protective shield."
        ),
    },
    "stable_day": {
        "brief": (
            "No risk signals fire today — energies are in the user's "
            "favor. Smooth flow day; momentum-building is encouraged."
        ),
        "upay_hint": (
            "Surya Dev remedies — subah Surya ko jal arghya, gratitude "
            "practice. Energy boost ke liye."
        ),
    },
}

# ── Tone hints per severity band — injected into the user prompt to shape
# language strength. The brand-voice rules in _SYSTEM_PROMPT still apply
# unchanged on top of this.
_BAND_TONE_HINTS: Dict[str, str] = {
    "mid": (
        "TONE = MILD-TO-MODERATE day. Keep language calm, gentle, "
        "reassuring. AVOID alarming words like 'intense', 'serious', "
        "'badi baatein ho sakti hain', 'sambhal kar', 'risk hai'. USE "
        "softer phrases: 'thodi sensitivity', 'gentle awareness', "
        "'mild cosmic window', 'normal flow', 'ek subtle background "
        "shift', 'koi major baat nahi par dhyan rakhein'. Reassure that "
        "most people won't even notice this if they manage routine well."
    ),
    "high": (
        "TONE = STRONG cosmic alert day. Be direct and clear about the "
        "heightened sensitivity, but stay supportive — never use fear, "
        "destiny, or 'kismat' language. USE phrases like 'aaj specially "
        "dhyan rakhein', 'cosmic energy strong hai is window mein', "
        "'mood aur decisions pe extra alertness rakhein', 'aaj wala din "
        "kaafi heavy hai energy ke level pe'."
    ),
}


# System prompt template — rule #4 (language) is filled in per-call from
# _LANG_DIRECTIVES so the same engine can serve all UI languages without
# duplicating the rest of the brand-voice rulebook.
_SYSTEM_PROMPT_TEMPLATE = """You are Cosmic Lens, a friendly Vedic astrology guide for Indian and global audiences.

Your voice is "Powered by Advanced Cosmic Intelligence" — warm, supportive, like a wise older sibling. Practical and grounding, never preachy or fearful.

ABSOLUTE RULES (violation = bad output):

1. NEVER mention AI, GPT, ChatGPT, LLM, machine learning, technology, algorithm, model, "trained on", or anything that reveals you are a language model. You ARE Cosmic Lens — speak as the system itself.

2. NEVER mention raw planet names (Mars, Saturn, Mercury, Jupiter, Venus, Rahu, Ketu, Sun, Moon) or technical Sanskrit jargon (dasha, antardasha, mahadasha, pratyantar, nakshatra, tithi, rahukaal, kantaka, sade sati, naidhana) in the output text. Use generic conversational terms instead, translated into the OUTPUT LANGUAGE specified in rule 4:
   - "today's energy", "aaj ki energy"
   - "current cosmic vibration"
   - "a sensitive time window", "ek sensitive samay window"
   - "steady background pressure"
   - "today's cycle", "aaj ka cycle"
   - "mind-energy", "physical energy", "emotional weather"

3. EXCEPTION — only in the `upay` (remedy) field, the following ARE allowed and encouraged because users expect them, in their original devotional form:
   - Deity names: Hanuman ji, Shani Dev, Surya Dev, Maa Lakshmi, Ganesha, Maa Durga
   - Specific mantras with text: "Om Sham Shanaishcharaya Namah", "Hanuman Chalisa", "Maha Mrityunjaya"
   - Traditional remedies: kaale til daan, ghee ka diya, gulab jal, haldi-doodh, jal arghya, masoor dal daan, sarso ka tel
   You MAY add a short clarifying gloss in the OUTPUT LANGUAGE around these names so non-Hindi speakers understand them.

4. OUTPUT LANGUAGE — STRICT:
{lang_directive}

5. Length per field: 1 to 3 short sentences (~20-40 words). Concise, practical, action-oriented.

6. Tone: supportive, friendly, never destiny / fate / fear language. NEVER use phrases like "kismat kharab hai", "graho ka prakop", "buri shakti", "dosh hai", "bad luck", "cursed", "doomed".

7. Output must be valid JSON with EXACTLY these 6 keys:
   - "category": short 2-3 word title (e.g. "Conflict / Anger", "Pressure / Patience")
   - "kya_risk_hai": what the day's challenge is
   - "kya_dhyan_rakhna_hai": what to be mindful of
   - "kya_avoid_karna_hai": specific things to avoid
   - "kya_karna_hai": positive actions for today
   - "upay": ONE traditional remedy (mantra / daan / diya — deity names OK here)
   The KEY NAMES stay in English (kya_risk_hai etc.) — only the VALUES are in the output language.
"""


def _system_prompt_for(lang: str) -> str:
    """Render the system prompt with the language directive baked in."""
    directive = _LANG_DIRECTIVES.get(lang, _LANG_DIRECTIVES[DEFAULT_LANG])
    return _SYSTEM_PROMPT_TEMPLATE.format(lang_directive=directive)


_CLIENT_CACHE: Dict[str, Any] = {"client": None, "tried": False}


def _try_replit_proxy():
    """Build an OpenAI SDK client wired to the Replit AI Integrations proxy.

    Returns the client on success, None if the proxy env vars are missing or
    SDK init fails.
    """
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "").strip()
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "").strip()
    if not (base_url and api_key):
        return None
    try:
        from openai import OpenAI  # type: ignore

        timeout = float(os.environ.get("COSMIC_RISK_TEXT_TIMEOUT", "20"))
        cli = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        log.info("risk_text_ai: using Replit AI Integrations proxy")
        return cli
    except Exception as exc:
        log.warning("risk_text_ai: Replit proxy init failed: %s", exc)
        return None


def _try_direct_openai():
    """Build an OpenAI SDK client using the user's own OPENAI_API_KEY.

    Reuses ``openai_helper._get_client()`` so the same key path the rest of
    the app uses is honored. Returns None if the key is missing or import
    fails.
    """
    try:
        from openai_helper import _get_client  # type: ignore

        cli = _get_client()
        if cli is not None:
            log.info("risk_text_ai: using direct OPENAI_API_KEY")
        return cli
    except Exception as exc:
        log.warning("risk_text_ai: cannot import openai_helper client: %s", exc)
        return None


def _client():
    """Build (and cache) an OpenAI SDK client.

    Provider selection is controlled by the ``COSMIC_AI_PROVIDER`` env var:

      - ``auto`` (default): try Replit AI Integrations proxy first (no extra
        billing on Replit), then fall back to the user's OPENAI_API_KEY.
        This means in production on Replit the proxy is used, and in
        VS Code / local where the proxy env vars are absent the OpenAI
        key is used — no code change needed.
      - ``replit``: only use the Replit proxy. Useful when you want a hard
        guarantee that no charges hit your OpenAI account.
      - ``openai``: only use the user's OPENAI_API_KEY, even on Replit.
        Useful in future when you have a paid OpenAI plan and want
        predictable per-token billing through your own OpenAI account.

    Returns None if the selected provider(s) are unavailable. Result is
    cached so this is a one-time decision per process.
    """
    if _CLIENT_CACHE["tried"]:
        return _CLIENT_CACHE["client"]
    _CLIENT_CACHE["tried"] = True

    provider = os.environ.get("COSMIC_AI_PROVIDER", "auto").strip().lower()
    if provider not in ("auto", "replit", "openai"):
        log.warning(
            "risk_text_ai: unknown COSMIC_AI_PROVIDER=%r, falling back to 'auto'",
            provider,
        )
        provider = "auto"

    cli = None
    if provider == "replit":
        cli = _try_replit_proxy()
        if cli is None:
            log.warning(
                "risk_text_ai: COSMIC_AI_PROVIDER=replit but proxy env vars "
                "missing — no client will be built"
            )
    elif provider == "openai":
        cli = _try_direct_openai()
        if cli is None:
            log.warning(
                "risk_text_ai: COSMIC_AI_PROVIDER=openai but OPENAI_API_KEY "
                "missing — no client will be built"
            )
    else:  # auto
        cli = _try_replit_proxy() or _try_direct_openai()

    _CLIENT_CACHE["client"] = cli
    _CLIENT_CACHE["provider"] = provider
    return cli


def _scan_forbidden(text: str, field: str, lang: str = DEFAULT_LANG) -> Optional[str]:
    """Return the first forbidden token found, or None if clean.

    Field-aware: deity / planet names + Sanskrit jargon are allowed in the
    `upay` field (user-expected for traditional remedies), but forbidden
    elsewhere. AI / GPT / model leaks are forbidden everywhere.

    Language-aware: the non-upay planet/Sanskrit token list is Roman / Hinglish
    transliteration. For non-`hn` output languages the model writes in a
    different script (Devanagari, Tamil, Chinese, English, …) so the
    Hinglish-token scan would either be a no-op (different script) or
    produce false positives (legitimate English "Mars/Saturn" usage). We
    keep the GLOBAL anti-leak scan (AI / GPT / etc. are forbidden in every
    language) and skip the non-upay planet scan for non-Hinglish output.
    """
    lower = " " + text.lower() + " "
    for tok in _FORBIDDEN_GLOBAL:
        if tok in lower:
            return f"global:{tok.strip()}"
    if field != "upay" and lang == DEFAULT_LANG:
        for tok in _FORBIDDEN_NON_UPAY:
            # Word-boundary-ish match — surround with spaces so "shukravar"
            # (Friday) doesn't trigger "shukra" inside.
            if f" {tok} " in lower or lower.startswith(f"{tok} ") or lower.endswith(f" {tok}"):
                return f"non_upay:{tok}"
    return None


def _validate(payload: Any, lang: str = DEFAULT_LANG) -> Optional[Dict[str, str]]:
    """Verify payload has all 6 required string fields, enforce length caps,
    and run the brand-voice forbidden-token scan field-aware. Returns the
    cleaned dict on success, None on any violation.
    """
    if not isinstance(payload, dict):
        return None
    out: Dict[str, str] = {}
    for k in _REQUIRED_KEYS:
        v = payload.get(k)
        if not isinstance(v, str):
            return None
        v = v.strip()
        if not v:
            return None
        cap = _MAX_LEN_CATEGORY if k == "category" else _MAX_LEN_FIELD
        if len(v) > cap:
            log.warning(
                "risk_text_ai: field %s exceeds %d chars (got %d) — rejecting",
                k, cap, len(v),
            )
            return None
        violation = _scan_forbidden(v, k, lang)
        if violation:
            log.warning(
                "risk_text_ai: brand-voice violation in %s (%s, lang=%s) — rejecting",
                k, violation, lang,
            )
            return None
        out[k] = v
    return out


def _generate_bundle(
    trigger: str,
    lang: str = DEFAULT_LANG,
) -> Optional[Dict[str, List[Dict[str, str]]]]:
    """Single AI call → all variants for a trigger.

    Asks the model to produce, in one structured response, ``N`` distinct
    phrasing variants for EACH severity band (currently {"mid", "high"}).
    Returned shape::

        {
          "mid":  [variant1, variant2, variant3],
          "high": [variant1, variant2, variant3],
        }

    Each variant is the same 6-field dict the legacy single-shot generator
    returned. Every variant is run through ``_validate`` (length caps +
    brand-voice forbidden-token scan) — if ANY variant fails validation
    the entire bundle is rejected and ``None`` is returned, so the
    engineering ``_TEXT_MAP`` fallback in ``risk_text_engine`` kicks in.
    NEVER returns a partially-valid bundle (no fakes).
    """
    cli = _client()
    if cli is None:
        return None
    spec = _TRIGGER_BRIEFS.get(trigger)
    if not spec:
        log.warning("risk_text_ai: unknown trigger %r", trigger)
        return None
    lang = _normalize_lang(lang)

    n = _VARIANTS_PER_BAND
    band_specs_block = "\n\n".join(
        f"=== BAND \"{band}\" ===\n{_BAND_TONE_HINTS[band]}\n"
        f"Generate exactly {n} DIFFERENT phrasing variants for this band."
        for band in _BANDS
    )

    # Final language reminder in the user message — belt-and-braces with the
    # system-prompt rule #4. The model occasionally drifts back to Hinglish
    # mid-response on long prompts; restating "OUTPUT LANGUAGE: <lang>" right
    # before the JSON spec keeps the response on-language.
    lang_reminder = _LANG_DIRECTIVES.get(lang, _LANG_DIRECTIVES[DEFAULT_LANG])

    user_msg = (
        "Generate the Cosmic Lens daily guidance for this trigger, in TWO "
        "tone bands and multiple phrasing variants per band.\n\n"
        f"Trigger key: {trigger}\n"
        f"Internal meaning (do NOT mention this directly in output): "
        f"{spec['brief']}\n\n"
        f"Canonical upay direction (use one of these — do NOT invent a "
        f"different deity / mantra / daan): {spec['upay_hint']}\n\n"
        f"{band_specs_block}\n\n"
        "Each variant within a band MUST:\n"
        "  - cover the same underlying signal (same category direction)\n"
        "  - use DIFFERENT word choices, sentence structures, and angles "
        "from the other variants in the same band (so consecutive days "
        "with the same trigger don't read identically)\n"
        "  - stay short and within the brand voice rules\n"
        "  - keep the upay aligned to the canonical direction above\n\n"
        f"OUTPUT LANGUAGE REMINDER (lang code = {lang}):\n{lang_reminder}\n\n"
        "Return strict JSON in EXACTLY this shape:\n"
        "{\n"
        f"  \"mid\":  [ v1, v2, v3 ],\n"
        f"  \"high\": [ v1, v2, v3 ]\n"
        "}\n"
        "Each vN must have keys: category, kya_risk_hai, "
        "kya_dhyan_rakhna_hai, kya_avoid_karna_hai, kya_karna_hai, upay. "
        "All VALUES must be in the output language above. Keys themselves "
        "stay in English."
    )

    model = os.environ.get("COSMIC_RISK_TEXT_MODEL", "gpt-4o-mini")
    timeout = float(os.environ.get("COSMIC_RISK_TEXT_TIMEOUT", "30"))

    try:
        resp = cli.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _system_prompt_for(lang)},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.85,
            max_tokens=2400,
            timeout=timeout,
        )
        content = (resp.choices[0].message.content or "").strip()
        if not content:
            log.warning("risk_text_ai: empty response for %s/%s", trigger, lang)
            return None
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            log.warning("risk_text_ai: bad JSON for %s/%s: %s", trigger, lang, exc)
            return None
        if not isinstance(payload, dict):
            log.warning("risk_text_ai: top-level not a dict for %s/%s", trigger, lang)
            return None

        bundle: Dict[str, List[Dict[str, str]]] = {}
        for band in _BANDS:
            arr = payload.get(band)
            if not isinstance(arr, list) or len(arr) < n:
                log.warning(
                    "risk_text_ai: missing/short '%s' band for %s/%s (got %r)",
                    band, trigger, lang, type(arr).__name__,
                )
                return None
            band_variants: List[Dict[str, str]] = []
            for idx, raw in enumerate(arr[:n]):
                validated = _validate(raw, lang=lang)
                if validated is None:
                    log.warning(
                        "risk_text_ai: variant %d of band %s failed validation for %s/%s",
                        idx, band, trigger, lang,
                    )
                    return None
                band_variants.append(validated)
            bundle[band] = band_variants
        return bundle
    except Exception as exc:
        log.warning("risk_text_ai: generation failed for %s/%s: %s", trigger, lang, exc)
        return None


def get_text(
    trigger: str,
    band: str = "mid",
    variant_idx: int = 0,
    lang: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Returns one AI-generated text variant for the (trigger, lang) × band, or None.

    Caching model:
      - One AI call per (trigger, lang) (process-wide) generates the FULL
        bundle of all band × variant combinations IN THAT LANGUAGE.
      - Subsequent calls are O(1): pick ``bundle[band][variant_idx % N]``.
      - Same trigger across consecutive days rotates through N=3 variants
        (caller passes ``variant_idx=day_idx``) so the per-day card text
        actually CHANGES day-to-day even when the dominant cosmic signal
        is unchanged.

    Lang resolution:
      - ``lang`` defaults to ``DEFAULT_LANG`` ("hn" — Hinglish, original
        brand voice).
      - Unknown / blank codes are coerced to ``DEFAULT_LANG`` so callers
        can pass user-supplied strings without pre-validation.

    In-flight dedup: keyed on ``(trigger, lang)`` — two callers asking for
    the same language at the same time share one AI call; callers asking
    for different languages don't block each other.

    Falls back gracefully:
      - Unknown band → coerced to "mid".
      - Trigger not in cache and AI unavailable → ``None`` (caller uses
        engineering ``_TEXT_MAP`` as a last resort).
    """
    if band not in _BANDS:
        band = "mid"
    lang = _normalize_lang(lang)
    cache_key = (trigger, lang)

    # Fast path: cached bundle present.
    with _CACHE_LOCK:
        bundle = _AI_CACHE.get(cache_key)
    if bundle is not None:
        variants = bundle.get(band) or bundle.get("mid")
        if variants:
            return variants[variant_idx % len(variants)]
        return None

    # Decide: are we the writer (no in-flight gen yet) or a waiter
    # (someone else is already generating)?
    own_event: Optional[threading.Event] = None
    wait_event: Optional[threading.Event] = None
    with _CACHE_LOCK:
        bundle = _AI_CACHE.get(cache_key)
        if bundle is not None:
            variants = bundle.get(band) or bundle.get("mid")
            if variants:
                return variants[variant_idx % len(variants)]
            return None
        existing = _INFLIGHT.get(cache_key)
        if existing is not None:
            wait_event = existing
        else:
            own_event = threading.Event()
            _INFLIGHT[cache_key] = own_event

    # Waiter path: block until the writer signals, then read from cache.
    if wait_event is not None:
        timeout = float(os.environ.get("COSMIC_RISK_TEXT_TIMEOUT", "30"))
        wait_event.wait(timeout=timeout + 5.0)
        with _CACHE_LOCK:
            bundle = _AI_CACHE.get(cache_key)
        if bundle is None:
            return None
        variants = bundle.get(band) or bundle.get("mid")
        if not variants:
            return None
        return variants[variant_idx % len(variants)]

    # Writer path: generate the full bundle, store, signal waiters.
    try:
        result = _generate_bundle(trigger, lang=lang)
        if result is not None:
            with _CACHE_LOCK:
                _AI_CACHE[cache_key] = result
            variants = result.get(band) or result.get("mid")
            if variants:
                return variants[variant_idx % len(variants)]
        return None
    finally:
        with _CACHE_LOCK:
            _INFLIGHT.pop(cache_key, None)
        assert own_event is not None
        own_event.set()


def cache_status() -> Dict[str, Any]:
    """Diagnostic: which (trigger, lang) pairs are currently cached, plus per-band variant counts."""
    with _CACHE_LOCK:
        per_key = {
            f"{trig}/{lang}": {band: len(variants) for band, variants in bundle.items()}
            for (trig, lang), bundle in _AI_CACHE.items()
        }
        cached_keys = sorted(f"{trig}/{lang}" for (trig, lang) in _AI_CACHE.keys())
        return {
            "cached_keys": cached_keys,
            "cache_size": len(_AI_CACHE),
            "total_known_triggers": len(_TRIGGER_BRIEFS),
            "bands": list(_BANDS),
            "variants_per_band": _VARIANTS_PER_BAND,
            "supported_langs": sorted(_LANG_DIRECTIVES.keys()),
            "default_lang": DEFAULT_LANG,
            "per_key_variants": per_key,
        }


def _prewarm_worker(triggers: List[str]) -> None:
    """Background worker: generate full bundle for all triggers in DEFAULT_LANG.

    One AI call per trigger generates all bands × variants in the default
    Hinglish brand voice. ``get_text`` does the actual cache write, so calling
    it once with default args is enough to populate the bundle for every
    (band, variant_idx) combination.

    NOTE: Other languages are NOT prewarmed — there are 13 triggers × 25
    languages = 325 potential bundles, which would cost ~$0.50-1 per server
    boot in OpenAI calls just to cover languages no one may use. Non-default
    languages are generated lazily on first request, then cached for the
    process lifetime so subsequent users on the same language are O(1).
    """
    for trig in triggers:
        try:
            get_text(trig, lang=DEFAULT_LANG)
        except Exception as exc:
            log.warning("risk_text_ai: prewarm failed for %s: %s", trig, exc)
    log.info(
        "risk_text_ai: prewarm done, cached %d/%d triggers in %s "
        "(bands=%s, variants=%d, other langs are lazy)",
        sum(1 for k in _AI_CACHE if k[1] == DEFAULT_LANG),
        len(_TRIGGER_BRIEFS),
        DEFAULT_LANG,
        list(_BANDS),
        _VARIANTS_PER_BAND,
    )


def prewarm_async() -> bool:
    """Spawn a background daemon thread to pre-generate all trigger texts.

    Idempotent — only spawns once per process. Returns True if a thread was
    spawned, False if it was already running or OPENAI is unavailable.
    """
    global _PREWARM_STARTED
    if os.environ.get("COSMIC_RISK_TEXT_PREWARM", "1") not in ("1", "true", "yes"):
        return False
    if _client() is None:
        log.info("risk_text_ai: prewarm skipped (no OpenAI client)")
        return False
    with _PREWARM_LOCK:
        if _PREWARM_STARTED:
            return False
        _PREWARM_STARTED = True
    triggers = list(_TRIGGER_BRIEFS.keys())
    log.info("risk_text_ai: starting background prewarm for %d triggers", len(triggers))
    t = threading.Thread(
        target=_prewarm_worker, args=(triggers,), name="risk_text_ai-prewarm", daemon=True
    )
    t.start()
    return True


# Auto-start prewarm on module import (non-blocking).
prewarm_async()
