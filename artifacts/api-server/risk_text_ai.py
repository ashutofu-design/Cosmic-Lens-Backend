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

# Module-level cache. Key = trigger string. Value = dict with 6 fields.
_AI_CACHE: Dict[str, Dict[str, str]] = {}
_CACHE_LOCK = threading.Lock()

# In-flight dedup: per-trigger Event so concurrent first-hit + prewarm don't
# duplicate OpenAI calls. Reader takes the lock, checks cache, otherwise
# either becomes the writer (creates Event, releases lock, generates) or
# waits on the existing Event.
_INFLIGHT: Dict[str, threading.Event] = {}

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

_SYSTEM_PROMPT = """You are Cosmic Lens, a friendly Vedic astrology guide for Indian audiences.

Your voice is "Powered by Advanced Cosmic Intelligence" — warm, supportive, like a wise older sibling. Practical and grounding, never preachy or fearful.

ABSOLUTE RULES (violation = bad output):

1. NEVER mention AI, GPT, ChatGPT, LLM, machine learning, technology, algorithm, model, "trained on", or anything that reveals you are a language model. You ARE Cosmic Lens — speak as the system itself.

2. NEVER mention raw planet names (Mars, Saturn, Mercury, Jupiter, Venus, Rahu, Ketu, Sun, Moon) or technical Sanskrit jargon (dasha, antardasha, mahadasha, pratyantar, nakshatra, tithi, rahukaal, kantaka, sade sati, naidhana) in the output text. Use generic conversational terms instead:
   - "aaj ki energy"
   - "current cosmic vibration"
   - "ek sensitive samay window"
   - "background mein steady pressure"
   - "aaj ka cycle"
   - "mann ki energy", "physical energy", "emotional weather"

3. EXCEPTION — only in the `upay` (remedy) field, the following ARE allowed and encouraged because users expect them:
   - Deity names: Hanuman ji, Shani Dev, Surya Dev, Maa Lakshmi, Ganesha, Maa Durga
   - Specific mantras with text: "Om Sham Shanaishcharaya Namah", "Hanuman Chalisa", "Maha Mrityunjaya"
   - Traditional remedies: kaale til daan, ghee ka diya, gulab jal, haldi-doodh, jal arghya, masoor dal daan, sarso ka tel

4. Language: HINGLISH ONLY — Roman-script Hindi mixed with English (conversational Mumbai / Delhi style). NOT pure Hindi devanagari. NOT pure English.
   - Good: "Aaj reactions slow karein, ek pause-breath-respond rule follow karein."
   - Bad (pure English): "Today, slow your reactions and follow a pause-breath-respond rule."
   - Bad (pure Hindi): "आज प्रतिक्रिया धीमी करें।"

5. Length per field: 1 to 3 short sentences (~20-40 words). Concise, practical, action-oriented.

6. Tone: supportive, friendly, never destiny / fate / fear language. NEVER use phrases like "kismat kharab hai", "graho ka prakop", "buri shakti", "dosh hai".

7. Output must be valid JSON with EXACTLY these 6 keys:
   - "category": short 2-3 word title (e.g. "Conflict / Anger", "Pressure / Patience")
   - "kya_risk_hai": what the day's challenge is
   - "kya_dhyan_rakhna_hai": what to be mindful of
   - "kya_avoid_karna_hai": specific things to avoid
   - "kya_karna_hai": positive actions for today
   - "upay": ONE traditional remedy (mantra / daan / diya — deity names OK here)
"""


_CLIENT_CACHE: Dict[str, Any] = {"client": None, "tried": False}


def _client():
    """Build (and cache) an OpenAI SDK client.

    Prefers the Replit AI Integrations proxy (no separate billing) when the
    ``AI_INTEGRATIONS_OPENAI_BASE_URL`` + ``AI_INTEGRATIONS_OPENAI_API_KEY``
    env vars are present, otherwise falls back to the project's existing
    ``openai_helper._get_client()`` (which uses ``OPENAI_API_KEY``).
    Returns None if neither path is available.
    """
    if _CLIENT_CACHE["tried"]:
        return _CLIENT_CACHE["client"]
    _CLIENT_CACHE["tried"] = True

    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "").strip()
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "").strip()
    if base_url and api_key:
        try:
            from openai import OpenAI  # type: ignore

            timeout = float(os.environ.get("COSMIC_RISK_TEXT_TIMEOUT", "20"))
            cli = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
            _CLIENT_CACHE["client"] = cli
            log.info("risk_text_ai: using Replit AI Integrations proxy")
            return cli
        except Exception as exc:
            log.warning("risk_text_ai: Replit proxy init failed: %s", exc)

    try:
        from openai_helper import _get_client  # type: ignore

        cli = _get_client()
        if cli is not None:
            log.info("risk_text_ai: using direct OPENAI_API_KEY")
        _CLIENT_CACHE["client"] = cli
        return cli
    except Exception as exc:
        log.warning("risk_text_ai: cannot import openai_helper client: %s", exc)
        return None


def _scan_forbidden(text: str, field: str) -> Optional[str]:
    """Return the first forbidden token found, or None if clean.

    Field-aware: deity / planet names + Sanskrit jargon are allowed in the
    `upay` field (user-expected for traditional remedies), but forbidden
    elsewhere. AI / GPT / model leaks are forbidden everywhere.
    """
    lower = " " + text.lower() + " "
    for tok in _FORBIDDEN_GLOBAL:
        if tok in lower:
            return f"global:{tok.strip()}"
    if field != "upay":
        for tok in _FORBIDDEN_NON_UPAY:
            # Word-boundary-ish match — surround with spaces so "shukravar"
            # (Friday) doesn't trigger "shukra" inside.
            if f" {tok} " in lower or lower.startswith(f"{tok} ") or lower.endswith(f" {tok}"):
                return f"non_upay:{tok}"
    return None


def _validate(payload: Any) -> Optional[Dict[str, str]]:
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
        violation = _scan_forbidden(v, k)
        if violation:
            log.warning(
                "risk_text_ai: brand-voice violation in %s (%s) — rejecting",
                k, violation,
            )
            return None
        out[k] = v
    return out


def _generate_one(trigger: str) -> Optional[Dict[str, str]]:
    """Single OpenAI call for one trigger. Returns validated dict or None."""
    cli = _client()
    if cli is None:
        return None
    spec = _TRIGGER_BRIEFS.get(trigger)
    if not spec:
        log.warning("risk_text_ai: unknown trigger %r", trigger)
        return None

    user_msg = (
        "Generate the Cosmic Lens daily guidance for this trigger.\n\n"
        f"Trigger key: {trigger}\n"
        f"Internal meaning (do NOT mention this directly in output): "
        f"{spec['brief']}\n\n"
        f"Canonical upay direction (use one of these — do NOT invent a "
        f"different deity / mantra / daan): {spec['upay_hint']}\n\n"
        "Return strict JSON with EXACTLY these 6 keys: "
        "category, kya_risk_hai, kya_dhyan_rakhna_hai, kya_avoid_karna_hai, "
        "kya_karna_hai, upay. Follow all brand voice rules. Hinglish only."
    )

    model = os.environ.get("COSMIC_RISK_TEXT_MODEL", "gpt-4o-mini")
    timeout = float(os.environ.get("COSMIC_RISK_TEXT_TIMEOUT", "20"))

    try:
        resp = cli.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=600,
            timeout=timeout,
        )
        content = (resp.choices[0].message.content or "").strip()
        if not content:
            log.warning("risk_text_ai: empty response for %s", trigger)
            return None
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            log.warning("risk_text_ai: bad JSON for %s: %s", trigger, exc)
            return None
        validated = _validate(payload)
        if validated is None:
            log.warning("risk_text_ai: validation failed for %s", trigger)
            return None
        return validated
    except Exception as exc:
        log.warning("risk_text_ai: generation failed for %s: %s", trigger, exc)
        return None


def get_text(trigger: str) -> Optional[Dict[str, str]]:
    """Returns AI-generated text dict for the trigger, or None on failure.

    Cached per-trigger (process-wide). Same trigger reuses the same text
    forever, so first hit per trigger is ~1-3s, subsequent hits are O(1).

    In-flight dedup: when two callers request the same trigger concurrently
    (e.g. first user request + background prewarm worker), only one OpenAI
    call is made. The second caller waits on a per-trigger Event and reads
    the result from cache once the first caller finishes.
    """
    # Fast path: cached.
    with _CACHE_LOCK:
        if trigger in _AI_CACHE:
            return _AI_CACHE[trigger]

    # Decide: are we the writer (no in-flight gen yet) or a waiter
    # (someone else is already generating)?
    own_event: Optional[threading.Event] = None
    wait_event: Optional[threading.Event] = None
    with _CACHE_LOCK:
        if trigger in _AI_CACHE:
            return _AI_CACHE[trigger]
        existing = _INFLIGHT.get(trigger)
        if existing is not None:
            wait_event = existing
        else:
            own_event = threading.Event()
            _INFLIGHT[trigger] = own_event

    # Waiter path: block until the writer signals, then read from cache.
    if wait_event is not None:
        timeout = float(os.environ.get("COSMIC_RISK_TEXT_TIMEOUT", "20"))
        # Add a small buffer over the OpenAI timeout so the waiter doesn't
        # bail before a slow-but-successful writer finishes.
        wait_event.wait(timeout=timeout + 5.0)
        with _CACHE_LOCK:
            return _AI_CACHE.get(trigger)

    # Writer path: generate, store, signal waiters, clean up the in-flight
    # entry. Errors are swallowed by _generate_one (returns None) but the
    # try/finally guarantees waiters are released even on unexpected
    # exceptions.
    try:
        result = _generate_one(trigger)
        if result is not None:
            with _CACHE_LOCK:
                _AI_CACHE[trigger] = result
        return result
    finally:
        with _CACHE_LOCK:
            _INFLIGHT.pop(trigger, None)
        assert own_event is not None
        own_event.set()


def cache_status() -> Dict[str, Any]:
    """Diagnostic: which triggers are currently cached."""
    with _CACHE_LOCK:
        return {
            "cached_triggers": sorted(_AI_CACHE.keys()),
            "cache_size": len(_AI_CACHE),
            "total_known": len(_TRIGGER_BRIEFS),
        }


def _prewarm_worker(triggers: List[str]) -> None:
    """Background worker: generate text for all triggers serially."""
    for trig in triggers:
        try:
            get_text(trig)
        except Exception as exc:
            log.warning("risk_text_ai: prewarm failed for %s: %s", trig, exc)
    log.info(
        "risk_text_ai: prewarm done, cached %d/%d triggers",
        len(_AI_CACHE),
        len(_TRIGGER_BRIEFS),
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
