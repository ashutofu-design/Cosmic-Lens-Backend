"""
Phase 2.5.11.20 — Kundli Milan LLM Prose Polish (HYBRID)
========================================================

Takes deterministic Ashtakoot facts (computed by /api/kundli-milan via
Swiss Ephemeris) and asks an LLM to rewrite the 4 narrative sections
(insight, strengths, challenges, marriage_outlook) in a warm, mature
"experienced Vedic astrologer" voice.

Architecture (matches existing locked_facts pattern):
  Engine = source of truth (numbers, koots, nakshatras, doshas)
  LLM    = language layer ONLY (rephrases facts, never invents)
  Validator = rejects output that drops/changes any fact
  Fallback  = current rule-based templates (zero risk)
  Cache     = in-process LRU keyed on fact-fingerprint

Toggle:    env COMPAT_LLM_POLISH=1   (default off)
Model:     env COMPAT_LLM_MODEL  (default gpt-4o-mini)
Cache cap: env COMPAT_LLM_CACHE_SIZE (default 1024)

Public API:
  polish_compat_analysis(facts, fallback) -> dict   # never raises
"""
from __future__ import annotations

import os
import re
import json
import hashlib
import logging
from collections import OrderedDict
from threading import Lock
from typing import Any

log = logging.getLogger(__name__)

# Bumped whenever the prompt, validator, or remedy whitelist changes.
# Included in cache fingerprint so policy changes auto-invalidate stale prose.
_PROMPT_VERSION = "v11"

# Classical Vedic vocabulary the LLM is allowed to reference. Anything
# outside this set in the prose is treated as a potential hallucination.
_KNOWN_NAKSHATRAS = {
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva phalguni",
    "uttara phalguni", "phalguni", "hasta", "chitra", "swati", "vishakha",
    "anuradha", "jyeshtha", "mula", "purva ashadha", "uttara ashadha",
    "ashadha", "shravana", "dhanishtha", "shatabhisha", "purva bhadrapada",
    "uttara bhadrapada", "bhadrapada", "revati",
}
_KNOWN_RASHIS = {
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
}

# ── Allowed remedies whitelist (single source of truth) ──────────────────────
ALLOWED_REMEDIES = [
    "Maha Mrityunjaya Jaap",
    "Kumbh Vivah",
    "Navagraha Shanti",
    "Mangal Shanti puja",
    "Vivah Yog ritual",
    "joint daily prayers",
    "gratitude practice",
    "Ayurvedic Vata-balancing diet",
    "Ayurvedic Pitta-balancing diet",
    "Ayurvedic Kapha-balancing diet",
    "consult a qualified Jyotishi",
]

# ── Banned phrases (safety mandate) ──────────────────────────────────────────
BANNED_TERMS = [
    "lifespan", "life span", "will die", "guaranteed to",
    "definitely will", "gender of child", "gender of children",
    "boy or girl", "death prediction",
]

# ── Prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an experienced Vedic astrologer who has studied thousands of real relationships. You speak like a wise family pandit: calm, grounded, emotionally intelligent — never theatrical.

═══ STYLE ═══
• First explain the emotional/relationship dynamic in real-life terms.
• Then the practical impact on marriage compatibility.
• Mention both strengths and challenges honestly.
• Frame challenges as manageable patterns — not doom.
• Avoid textbook astrology jargon unless you immediately translate it.
• No generic motivational lines, no fear-based language.

The reader should feel: "Someone genuinely understood this relationship deeply." NOT: "A machine generated astrology text."

═══ ABSOLUTE RULES (violation = response rejected) ═══
1. Use ONLY the facts inside <ENGINE_FACTS>. Do not invent any nakshatra, koot score, dosha, percentage, or planet.
2. Cite numbers VERBATIM. Write "14.5 out of 36", never "around 40%" or "roughly half". The exact total must appear in compatibility_insight.
3. Use exact nakshatra/rashi names from facts. No synonyms, no transliteration variants.
4. NEVER predict: specific dates, lifespan, death, gender of children, guaranteed outcomes.
5. Recommend ONLY remedies from <ALLOWED_REMEDIES>. No gemstones, no tantrik kriyas, no expensive yagnas outside the list.
6. LANGUAGE CONTRACT — write the entire prose in the user's language as specified by `language` in <USER_CONTEXT>:
   • "en" = pure English.
   • "hn" = Hinglish (Hindi written in Roman/English script — "yeh rishta", "samay ke saath", "thoda dhyan rakhna").
   • "hi" = Hindi in Devanagari script (देवनागरी).
   • "bn" = Bengali (বাংলা). "mr" = Marathi (मराठी). "ta" = Tamil (தமிழ்). "te" = Telugu (తెలుగు). "gu" = Gujarati (ગુજરાતી). "kn" = Kannada (ಕನ್ನಡ). "ml" = Malayalam (മലയാളം). "pa" = Punjabi (ਪੰਜਾਬੀ). "or" = Odia (ଓଡ଼ିଆ). "as" = Assamese (অসমীয়া).
   • "zh" = Chinese (中文). "es" = Spanish. "ar" = Arabic (العربية). "fr" = French. "pt" = Portuguese. "de" = German. "ru" = Russian (Русский). "ja" = Japanese (日本語). "id" = Indonesian. "ko" = Korean (한국어). "tr" = Turkish.
   • CRITICAL EXCEPTIONS — even in non-English languages, keep these tokens VERBATIM in their original English form (never translate or transliterate):
     - All nakshatra names (Ashwini, Bharani, Krittika, ... Revati)
     - All rashi names (Aries, Taurus, ... Pisces)
     - All koot labels (Varna, Vasya, Tara, Yoni, Maitri, Gana, Bhakut, Nadi)
     - All remedy names from <ALLOWED_REMEDIES>
     - The numeric total like "14.5 out of 36"
     This is so the validator and downstream UI can match these exact strings.

═══ STRUCTURE ═══
The user paid to see 6 specific dimensions of this relationship. Each section must answer a different psychological question. Do NOT repeat the same insight across sections — each one stands alone.

The 6 dimensions, mapped to psychological questions the reader is silently asking:
1. Emotional Alignment   → "Do we actually FEEL the same things?"
2. Trust & Loyalty       → "Will this person stay loyal? When does trust face its hardest test?"
3. Conflict Patterns     → "When we fight, what is REALLY happening underneath?"
4. Marriage Stability    → "Will this marriage last? What is the ONE adjustment both must accept?"
5. Commitment Strength   → "Who invests more? Who commits permanently?"
6. Future Direction      → "Where is this heading in the next 2-3 years? What ONE quiet choice decides the outcome?"

Plus a top snapshot — a 1-line soul-summary of the bond + 3 tags.

═══ OUTPUT (JSON only, no markdown, no preamble) ═══
{
  "relationship_snapshot": {
    "summary": "<1 sentence, ~15-30 words. Captures the core energy of the bond. Example: 'A high-emotion, slow-maturity bond — strong attachment exists, but emotional timing between both differs.'>",
    "tags": {
      "emotional_pull":      "<one of: Very Strong | Strong | Medium | Mild>",
      "marriage_potential":  "<one of: High | Medium-High | Medium | Medium-Low | Low>",
      "long_term_stability": "<short phrase, 3-7 words. Example: 'Depends on communication maturity'>"
    }
  },
  "emotional_alignment": {
    "text": "<3-4 sentences, ~70-110 words. Attachment styles, who feels deeper, who withdraws, who needs reassurance. Real behavioral observations, not textbook astrology. Should make the reader think: 'How does it know this about us?'>",
    "grounding": "<1 short line, 8-18 words. Example: 'Based on Moon-sign harmony, Maitri (mental friendship), and Gana koot.'>"
  },
  "trust_loyalty": {
    "text": "<3-4 sentences, ~70-110 words. Insecurity patterns, what erodes vs builds trust, when trust faces its real test. Anchor with a specific emotional phase if possible (not specific dates).>",
    "grounding": "<1 short line, 8-18 words. Example: 'Based on Bhakut, Mangal balance, and 7th-house loyalty indicators.'>"
  },
  "conflict_patterns": {
    "text": "<3-4 sentences, ~70-110 words. HOW fights actually start, HOW they escalate, HOW they heal. NEVER 'Mars causes fights'. Always behavioral pattern. End with ONE practical de-escalation cue, not a remedy.>",
    "grounding": "<1 short line, 8-18 words. Example: 'Based on Yoni, Gana, and Mars-Mercury behavioral indicators.'>"
  },
  "marriage_stability": {
    "text": "<4-5 sentences, ~100-140 words. Marriage probability, family acceptance, the ONE specific adjustment both partners will resist at first but must accept for stability. End with ONE verbatim remedy from <ALLOWED_REMEDIES>.>",
    "grounding": "<1 short line, 8-18 words. Example: 'Based on total Ashtakoot score, Bhakut, and Nadi compatibility.'>"
  },
  "commitment_strength": {
    "text": "<3-4 sentences, ~70-110 words. Who invests faster, who commits more permanently, breakup-reconciliation tendency, long-term effort balance.>",
    "grounding": "<1 short line, 8-18 words. Example: 'Based on Maitri (planetary friendship), Vasya, and 7th-lord placement.'>"
  },
  "future_direction": {
    "text": "<4-5 sentences, ~100-140 words. Next 2-3 year direction, relationship evolution, how the bond matures, the ONE quiet choice the real outcome depends on. End with ONE verbatim remedy from <ALLOWED_REMEDIES>.>",
    "grounding": "<1 short line, 8-18 words. Example: 'Based on overall compatibility score, dasha context, and 7th-house yogas.'>"
  }
}

═══ OUTPUT CHECKLIST (verify before responding — non-negotiable) ═══
Before you submit, confirm:
☐ The exact total score (e.g. "14.5 out of 36") appears literally inside relationship_snapshot.summary OR marriage_stability.text (at least one).
☐ BOTH partner nakshatra OR rashi names from <ENGINE_FACTS> appear at least once across the 6 section texts (each partner needs at least one chart-anchor).
☐ Any "X / Y" or "X out of Y" numeric pair you write MUST exactly match a real koot score from <ENGINE_FACTS> (or the total/max). Do not invent or round koot numbers.
☐ Do NOT name any nakshatra or rashi other than the ones in <ENGINE_FACTS>. Generic words like "stars", "signs", "Moon" are fine.
☐ At least ONE remedy phrase from <ALLOWED_REMEDIES> appears verbatim across marriage_stability.text + future_direction.text combined. No gemstones, no tantrik kriyas, no expensive yagnas outside the list.
☐ Each grounding line is short (8-18 words), references 2-3 real Vedic concepts subtly, and starts with "Based on" or "Derived from".
☐ Each of the 6 section texts answers a DIFFERENT psychological question — no repetition, no overlap.
☐ No banned terms: lifespan, death, gender of children, "guaranteed to", "definitely will".
☐ Output is valid JSON, no markdown fences, no commentary outside the JSON object."""


_SCRIPT_BY_LANG = {
    "hi": ("Devanagari (देवनागरी)", "देवनागरी"),
    "mr": ("Devanagari (मराठी)", "देवनागरी"),
    "bn": ("Bengali (বাংলা)", "বাংলা"),
    "ta": ("Tamil (தமிழ்)", "தமிழ்"),
    "te": ("Telugu (తెలుగు)", "తెలుగు"),
    "gu": ("Gujarati (ગુજરાતી)", "ગુજરાતી"),
    "kn": ("Kannada (ಕನ್ನಡ)", "ಕನ್ನಡ"),
    "ml": ("Malayalam (മലയാളം)", "മലയാളം"),
    "pa": ("Gurmukhi (ਪੰਜਾਬੀ)", "ਪੰਜਾਬੀ"),
    "or": ("Odia (ଓଡ଼ିଆ)", "ଓଡ଼ିଆ"),
    "as": ("Assamese (অসমীয়া)", "অসমীয়া"),
    "zh": ("Chinese (中文)", "中文"),
    "ar": ("Arabic (العربية)", "العربية"),
    "ru": ("Russian (Кириллица)", "Кириллица"),
    "ja": ("Japanese (日本語)", "日本語"),
    "ko": ("Korean (한국어)", "한국어"),
}


def _script_enforcement_line(lang: str) -> str:
    """Loud per-language script enforcement appended at end of user prompt.
    Empirically, gpt-4o-mini ignores SYSTEM-prompt language rules for non-Latin
    scripts (e.g. returns Hinglish/Latin for `hi`). Repeating the rule LAST in
    the user message dramatically improves compliance (recency effect)."""
    code = (lang or "en").lower()
    if code in _SCRIPT_BY_LANG:
        full, native = _SCRIPT_BY_LANG[code]
        return (
            f"SCRIPT MANDATE — Write EVERY word of all 4 fields in {full} script ONLY. "
            f"Do NOT use Latin/Roman/English letters anywhere except for these verbatim-keep tokens "
            f"(which MUST stay in original Latin spelling, never transliterated): "
            f"PARTNER NAMES (p1_name, p2_name) + nakshatra/rashi/koot/remedy names + the numeric total. "
            f"Example for hi: 'Ashu और Animesh के बीच Bhakut Koot 7/7 है — Maha Mrityunjaya Jaap उपयुक्त रहेगा।' "
            f"If any sentence is in a different script (other than the verbatim-keep words), output is discarded. "
            f"Confirm: each name appears in Latin letters; surrounding prose is in {native}."
        )
    if code == "hn":
        return (
            "SCRIPT MANDATE — Write EVERY word in HINGLISH (Hindi spelled in Roman/Latin letters, "
            "e.g. 'yeh rishta', 'samay ke saath'). Do NOT use Devanagari (देवनागरी) anywhere."
        )
    return ""  # en and others: no extra constraint


def _build_user_prompt(facts: dict[str, Any], lang: str = "en") -> str:
    koots = facts.get("koots", [])
    koot_lines = []
    for k in koots:
        marker = ""
        s, mx = k.get("score", 0), k.get("max", 0)
        if s == 0 and mx > 0:
            marker = "  ← DOSHA"
        elif s == mx and mx >= 4:
            marker = "  ← STRENGTH"
        koot_lines.append(
            f"  {k.get('label','?'):<8} {s} / {mx}   ({k.get('detail','')}){marker}"
        )

    p1, p2 = facts.get("p1", {}), facts.get("p2", {})
    p1_mang = p1.get("manglik", False)
    p2_mang = p2.get("manglik", False)
    if p1_mang and p2_mang:
        mang_line = "manglik_status: both_manglik (mutual cancellation applies)"
    elif p1_mang or p2_mang:
        mang_line = f"manglik_status: only_{'p1' if p1_mang else 'p2'}_manglik (imbalance — remedy advised)"
    else:
        mang_line = "manglik_status: neither (no Mangal dosha)"

    return f"""<ENGINE_FACTS>
p1_name: {p1.get('name','Partner 1')}
p1_nakshatra: {p1.get('nakshatra','?')} (Pada {p1.get('pada','?')}, {p1.get('rashi','?')})
p1_manglik: {p1_mang}

p2_name: {p2.get('name','Partner 2')}
p2_nakshatra: {p2.get('nakshatra','?')} (Pada {p2.get('pada','?')}, {p2.get('rashi','?')})
p2_manglik: {p2_mang}

total_guna: {facts.get('total','?')} / {facts.get('max',36)} ({facts.get('percent','?')}%)
grade: {facts.get('grade',{}).get('label','?')}

koot_scores:
{chr(10).join(koot_lines)}

{mang_line}
</ENGINE_FACTS>

<ALLOWED_REMEDIES>
{', '.join(ALLOWED_REMEDIES)}
</ALLOWED_REMEDIES>

<USER_CONTEXT>
language: {lang}
</USER_CONTEXT>

CRITICAL — both partner names MUST appear at least once each across the
4 fields combined: "{p1.get('name','Partner 1')}" and "{p2.get('name','Partner 2')}".
Output that omits either name will be rejected.

{_script_enforcement_line(lang)}

Generate the JSON now."""


# ── Fingerprint + cache ──────────────────────────────────────────────────────
def _fingerprint(facts: dict[str, Any], lang: str) -> str:
    """Deterministic cache key from the facts that drive the prose.

    Includes _PROMPT_VERSION so prompt/validator/whitelist changes
    automatically invalidate stale cache entries.
    """
    p1 = facts.get("p1", {})
    p2 = facts.get("p2", {})
    grade = facts.get("grade", {}) or {}
    parts = [
        f"v={_PROMPT_VERSION}",
        f"lang={lang}",
        p1.get("nakshatra", ""), str(p1.get("pada", "")), p1.get("rashi", ""),
        p2.get("nakshatra", ""), str(p2.get("pada", "")), p2.get("rashi", ""),
        f"total={facts.get('total','')}",
        f"max={facts.get('max','')}",
        f"pct={facts.get('percent','')}",
        f"grade={grade.get('label','')}",
        f"m1={p1.get('manglik','')}", f"m2={p2.get('manglik','')}",
        f"mdosh={facts.get('manglik_dosh','')}",
    ]
    for k in facts.get("koots", []):
        parts.append(f"{k.get('key','')}={k.get('score','')}/{k.get('max','')}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


_CACHE_CAP = int(os.environ.get("COMPAT_LLM_CACHE_SIZE", "1024"))
_cache: "OrderedDict[str, dict]" = OrderedDict()
_cache_lock = Lock()


def _cache_get(key: str) -> dict | None:
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    return None


def _cache_put(key: str, value: dict) -> None:
    with _cache_lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > _CACHE_CAP:
            _cache.popitem(last=False)


# ── Phase 2.5.11.20-A: Persistent DB cache (cross-process, cross-restart) ────
# In-memory cache above is L1 (per-process, fast). DB cache is L2 (shared,
# survives restarts/deploys). Both are best-effort: any DB error → fall
# through to LLM call, never raise.
def _db_cache_get(fingerprint: str) -> dict | None:
    try:
        from models import KundliMilanCache  # type: ignore
        from database import db as _db  # type: ignore
        from datetime import datetime as _dt
        row = _db.session.get(KundliMilanCache, fingerprint)
        if row is None:
            return None
        # Defense-in-depth: even though _PROMPT_VERSION is in the fingerprint,
        # also reject any row whose stored version mismatches the current one
        # (e.g. legacy rows written before we added the version-in-fingerprint).
        if (row.prompt_version or "") != _PROMPT_VERSION:
            return None
        # Best-effort hit-counter bump (don't fail the read if this fails)
        try:
            row.hits = (row.hits or 0) + 1
            row.last_hit_at = _dt.utcnow()
            _db.session.commit()
        except Exception:
            try:
                _db.session.rollback()
            except Exception:
                pass
        return dict(row.polished_json) if row.polished_json else None
    except Exception as exc:
        log.warning("[compat_llm] db cache read failed: %s", exc)
        # Architect 2.5.11.20-A: rollback on outer failure so a poisoned
        # session doesn't break unrelated DB work later in the same request.
        try:
            from database import db as _db  # type: ignore
            _db.session.rollback()
        except Exception:
            pass
        return None


def _db_cache_put(fingerprint: str, polished: dict, model: str) -> None:
    """Race-safe upsert. On Postgres uses ON CONFLICT DO UPDATE so concurrent
    misses for the same fingerprint don't produce noisy IntegrityError logs.
    Falls back to read-then-write for SQLite (dev) or any unexpected dialect."""
    try:
        from models import KundliMilanCache  # type: ignore
        from database import db as _db  # type: ignore
        from datetime import datetime as _dt

        now = _dt.utcnow()
        dialect = _db.session.bind.dialect.name if _db.session.bind else ""

        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(KundliMilanCache).values(
                fingerprint=fingerprint,
                polished_json=polished,
                model=model,
                prompt_version=_PROMPT_VERSION,
                created_at=now,
                last_hit_at=now,
                hits=0,
            ).on_conflict_do_update(
                index_elements=["fingerprint"],
                set_={
                    "polished_json": polished,
                    "model": model,
                    "prompt_version": _PROMPT_VERSION,
                    "last_hit_at": now,
                },
            )
            _db.session.execute(stmt)
        else:
            # SQLite dev path (or anything non-PG): read-modify-write.
            existing = _db.session.get(KundliMilanCache, fingerprint)
            if existing is not None:
                existing.polished_json = polished
                existing.model = model
                existing.prompt_version = _PROMPT_VERSION
                existing.last_hit_at = now
            else:
                _db.session.add(KundliMilanCache(
                    fingerprint=fingerprint, polished_json=polished,
                    model=model, prompt_version=_PROMPT_VERSION, hits=0,
                ))
        _db.session.commit()
    except Exception as exc:
        log.warning("[compat_llm] db cache write failed: %s", exc)
        try:
            from database import db as _db  # type: ignore
            _db.session.rollback()
        except Exception:
            pass


# ── Validator ────────────────────────────────────────────────────────────────
_TEXT_SECTIONS = (
    "emotional_alignment",
    "trust_loyalty",
    "conflict_patterns",
    "marriage_stability",
    "commitment_strength",
    "future_direction",
)
_REMEDY_BEARING_SECTIONS = ("marriage_stability", "future_direction")


_LATIN_LANGS = {"en", "hn", "es", "fr", "de", "pt", "id", "tr"}


# Map of common non-Latin digit codepoints → ASCII '0'-'9'. Covers
# Devanagari, Bengali, Gurmukhi, Gujarati, Tamil, Telugu, Kannada,
# Malayalam, Oriya, Arabic-Indic and Eastern-Arabic-Indic. Used to
# normalize LLM output before searching for verbatim numeric tokens
# like the koot total ("14.5", "24") which the model often re-renders
# in the target script's native digits.
_DIGIT_TRANSLATE = {}
for _base in (
    0x0966,  # Devanagari ०-९
    0x09E6,  # Bengali
    0x0A66,  # Gurmukhi
    0x0AE6,  # Gujarati
    0x0BE6,  # Tamil
    0x0C66,  # Telugu
    0x0CE6,  # Kannada
    0x0D66,  # Malayalam
    0x0B66,  # Oriya
    0x0660,  # Arabic-Indic ٠-٩
    0x06F0,  # Eastern Arabic-Indic ۰-۹
):
    for _i in range(10):
        _DIGIT_TRANSLATE[_base + _i] = ord('0') + _i


def _normalize_digits(s: str) -> str:
    """Map Indic/Arabic digits to ASCII '0'-'9' so str(total) checks
    succeed against LLM output that re-rendered numerals in the target
    script (e.g. Devanagari "२४" → "24")."""
    if not s:
        return s
    return s.translate(_DIGIT_TRANSLATE)


def _validate(out: Any, facts: dict[str, Any], lang: str = "en") -> tuple[bool, str]:
    """Return (ok, reason). ok=False means caller must use fallback.

    Phase 2.5.11.21 — schema upgraded from 4 flat keys to:
      relationship_snapshot: { summary, tags: {emotional_pull, marriage_potential, long_term_stability} }
      <6 text sections>:    { text, grounding }
    matching the 6 paywall promises 1:1 + a top snapshot.

    Anchor + vocab checks use Latin word-boundary regex; for non-Latin
    scripts (Devanagari/CJK/Arabic/Indic) the LLM commonly transliterates
    every name into the target script, making Latin anchor matching
    impossible. For those languages we skip the anchor + vocab checks
    and rely on (a) total citation + (b) verbatim koot-pair fact-lock
    + (c) banned-term + (d) banned-remedy + (e) remedy-whitelist as
    sufficient grounding signals.
    """
    if not isinstance(out, dict):
        return False, "not_dict"

    # ── relationship_snapshot shape ───────────────────────────────────────
    snap = out.get("relationship_snapshot")
    if not isinstance(snap, dict):
        return False, "missing_or_bad:relationship_snapshot"
    snap_summary = snap.get("summary")
    if not isinstance(snap_summary, str) or not (15 <= len(snap_summary) <= 400):
        return False, "snapshot_summary_bad"
    snap_tags = snap.get("tags")
    if not isinstance(snap_tags, dict):
        return False, "snapshot_tags_bad"
    for tk in ("emotional_pull", "marriage_potential", "long_term_stability"):
        v = snap_tags.get(tk)
        if not isinstance(v, str) or not (2 <= len(v) <= 80):
            return False, f"snapshot_tag_bad:{tk}"

    # ── per-section text + grounding shape + length ───────────────────────
    section_texts: dict[str, str] = {}
    for sec in _TEXT_SECTIONS:
        s = out.get(sec)
        if not isinstance(s, dict):
            return False, f"missing_or_bad:{sec}"
        text = s.get("text")
        grounding = s.get("grounding")
        if not isinstance(text, str):
            return False, f"{sec}_text_bad"
        if not isinstance(grounding, str):
            return False, f"{sec}_grounding_bad"
        # Length sanity per section
        long_secs = {"marriage_stability", "future_direction"}
        lo, hi = (80, 1200) if sec in long_secs else (50, 1000)
        if not (lo <= len(text) <= hi):
            return False, f"{sec}_text_length"
        if not (10 <= len(grounding) <= 240):
            return False, f"{sec}_grounding_length"
        section_texts[sec] = text

    full_text = " ".join([snap_summary] + list(section_texts.values()))
    full_lower = full_text.lower()

    # Verbatim total score must appear SOMEWHERE in the deep schema
    # (snapshot.summary or any of the 6 section texts). Normalize Indic
    # digits to ASCII first — Devanagari/Tamil/etc LLM output frequently
    # re-renders "24" as "२४"/"௨௪" which would otherwise false-fail.
    total = facts.get("total")
    if total is not None:
        if str(total) not in _normalize_digits(full_text):
            return False, "total_not_cited"

    # Per-language Latin-anchor toggle.
    is_latin_lang = (lang or "en").lower() in _LATIN_LANGS
    # Alias kept for downstream checks below (was used to gate insight-length etc.)
    insight = snap_summary
    outlook = section_texts["future_direction"]

    # Each partner must be anchored to their own chart — accept any of:
    # nakshatra, rashi, OR partner name appearing in the prose. Name is
    # a valid anchor because it proves the LLM is grounded in this
    # specific request (cannot be hallucinated; comes from <ENGINE_FACTS>).
    # All checks are case-insensitive AND word-boundary anchored to
    # avoid substring collisions (e.g. "Mula" ⊂ "formula", "Leo" ⊂
    # "chameleon", short name "an" ⊂ "and").
    def _word_in(term: str) -> bool:
        if not term:
            return False
        return re.search(r"\b" + re.escape(term.lower()) + r"\b", full_lower) is not None

    def _has_anchor(p_key: str, label: str) -> tuple[bool, str]:
        p = facts.get(p_key, {})
        # Phase 2.5.11.20-B: accept ANY token of a multi-word nakshatra
        # (e.g. "Bhadrapada" alone counts as anchor for "Purva Bhadrapada"),
        # mirroring the vocab-allowlist logic below for symmetry.
        nak_full = (p.get("nakshatra") or "").strip()
        nak_tokens = [t for t in nak_full.split() if t] if nak_full else []
        rashi = (p.get("rashi") or "").strip()
        name = (p.get("name") or "").strip()
        if any(_word_in(t) for t in nak_tokens) or (nak_full and _word_in(nak_full)):
            return True, ""
        if _word_in(rashi):
            return True, ""
        # Names shorter than 3 chars are too collision-prone even with
        # word boundaries (e.g. "An" still matches the standalone word
        # "an"). Fall back to nakshatra/rashi only in that case.
        if name and len(name) >= 3 and _word_in(name):
            return True, ""
        return False, f"{label}_anchor_missing"

    if is_latin_lang:
        ok1, reason1 = _has_anchor("p1", "p1")
        if not ok1:
            return False, reason1
        ok2, reason2 = _has_anchor("p2", "p2")
        if not ok2:
            return False, reason2

    # No banned terms
    for b in BANNED_TERMS:
        if b in full_lower:
            return False, f"banned_term:{b}"

    # Whitelist enforcement (positive contract):
    # At least ONE entry from ALLOWED_REMEDIES must appear verbatim
    # across marriage_stability.text + future_direction.text combined.
    remedy_zone_raw = " ".join(section_texts[s] for s in _REMEDY_BEARING_SECTIONS)
    remedy_zone = remedy_zone_raw.lower()
    outlook_lower = outlook.lower()
    allowed_lower = [r.lower() for r in ALLOWED_REMEDIES]
    if not any(r in remedy_zone for r in allowed_lower):
        return False, "remedy_missing"
    # Negative contract: no banned remedy term anywhere in any of the 6
    # section texts. Denylist safety net — the positive contract above
    # is the actual whitelist guarantee.
    BANNED_REMEDY_TERMS = [
        "gemstone", "ratna", "ruby", "emerald", "pearl", "blue sapphire",
        "yellow sapphire", "coral", "topaz", "diamond ring",
        "wear a", "wear the",            # "wear a ruby", "wear the pearl"
        "tantrik", "tantra ritual", "black magic", "vashikaran",
        "pendant", "amulet", "talisman", "kavach",
    ]
    for sec_name, sec_text in section_texts.items():
        sec_lower = sec_text.lower()
        for banned in BANNED_REMEDY_TERMS:
            if banned in sec_lower:
                return False, f"banned_remedy_in_{sec_name}:{banned}"

    # Fact-lock: any "X / Y" or "X out of Y" numeric pair the LLM uses
    # MUST correspond to a real koot score (or the total) from facts.
    # This catches hallucinated koot scores even when overall narrative
    # passes other checks.
    real_pairs = {(str(facts.get("total", "")), str(facts.get("max", 36)))}
    for k in facts.get("koots", []):
        real_pairs.add((str(k.get("score", "")), str(k.get("max", ""))))
    # Normalize Indic digits before regex scan so Devanagari/Tamil/etc
    # outputs like "१४.५ out of ३६" are validated against ASCII koots.
    pair_re = re.compile(r"(\d+(?:\.\d+)?)\s*(?:/|out of)\s*(\d+)", re.I)
    for m in pair_re.finditer(_normalize_digits(full_text)):
        if (m.group(1), m.group(2)) not in real_pairs:
            return False, f"hallucinated_score:{m.group(0)}"

    # Vocabulary-lock: any nakshatra or rashi name appearing in the
    # prose must match either p1 or p2's actual chart. Catches LLMs
    # that name-drop unrelated nakshatras/rashis (e.g. invents "Krittika"
    # when neither partner has it).
    p1 = facts.get("p1", {}) or {}
    p2 = facts.get("p2", {}) or {}
    # Include EVERY word of each multi-word nakshatra so e.g. "Purva Bhadrapada"
    # allows both "Purva" and "Bhadrapada" tokens (LLM commonly shortens to
    # the second word). Previously we kept only the first word, which made
    # the validator reject the LLM's natural shortening with `unknown_nakshatra:Bhadrapada`.
    allowed_naks: set[str] = set()
    for _p in (p1, p2):
        _nak = (_p.get("nakshatra") or "").strip().lower()
        if _nak:
            for _tok in _nak.split():
                allowed_naks.add(_tok)
            allowed_naks.add(_nak)  # also the full multi-word form
    allowed_rashis = {
        (p1.get("rashi") or "").lower(), (p2.get("rashi") or "").lower(),
    } - {""}
    # Whole-word, case-insensitive scan. Previously we only matched
    # capitalized tokens which let lowercase hallucinations slip
    # through ("yeh shravana wali energy ...") in Hinglish output.
    # The vocab-lock is Latin-word-boundary based so it has nothing to
    # check on transliterated non-Latin output — but if LLM mixes in
    # Latin nakshatra/rashi tokens (which it sometimes does even in
    # Devanagari output), we still want to catch hallucinations.
    for word_match in re.finditer(r"\b([A-Za-z][A-Za-z]+)\b", full_text):
        token = word_match.group(1).lower()
        if token in _KNOWN_NAKSHATRAS and token not in allowed_naks:
            return False, f"unknown_nakshatra:{word_match.group(1)}"
        if token in _KNOWN_RASHIS and token not in allowed_rashis:
            return False, f"unknown_rashi:{word_match.group(1)}"

    # Per-section length sanity already enforced above during shape check.
    return True, "ok"


# ── Public entrypoint ────────────────────────────────────────────────────────
def polish_compat_analysis(
    facts: dict[str, Any],
    fallback: dict[str, Any],
    lang: str = "en",
) -> dict[str, Any]:
    """
    Main entrypoint. Returns a polished analysis dict shaped like `fallback`:
      { compatibility_insight, strengths, challenges, marriage_outlook }

    Behaviour:
      • Toggle off → returns fallback as-is.
      • Cache hit → returns cached prose (no LLM call).
      • LLM call success + validator pass → cache + return.
      • Any failure → returns fallback (never raises).
    """
    if os.environ.get("COMPAT_LLM_POLISH", "0") not in ("1", "true", "True"):
        return fallback

    try:
        key = _fingerprint(facts, lang)

        # L1: in-process LRU (fast, per-worker, lost on restart)
        hit = _cache_get(key)
        if hit is not None:
            return hit

        # L2: persistent DB (shared across workers, survives restarts/deploys)
        db_hit = _db_cache_get(key)
        if db_hit is not None:
            _cache_put(key, db_hit)  # warm L1 from L2
            return db_hit

        # Lazy import — avoid loading openai_helper at module-import time
        try:
            from openai_helper import _get_client  # type: ignore
        except Exception as exc:
            log.warning("[compat_llm] openai_helper import failed: %s", exc)
            return fallback

        client = _get_client()
        if client is None:
            return fallback

        model = os.environ.get("COMPAT_LLM_MODEL", "gpt-4o-mini")
        user_prompt = _build_user_prompt(facts, lang=lang)

        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            # Phase 2.5.11.21: 7-section schema is ~3x larger than the old 4-key
            # output (snapshot + 6 sections × text+grounding). Empirical sizing:
            # • en full output ~1400-1700 tokens → cap 2000.
            # • Hinglish/non-Latin 2-3× more tokens per char → cap 2800.
            "max_tokens": 2000 if (lang or "en").lower() == "en" else 2800,
        }
        # gpt-5.x rejects temperature; only set for non-gpt-5 models
        if not model.lower().startswith("gpt-5"):
            kwargs["temperature"] = 0.6

        resp = client.chat.completions.create(**kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        try:
            usage = getattr(resp, "usage", None)
            if usage is not None:
                pt = getattr(usage, "prompt_tokens", "?")
                ct = getattr(usage, "completion_tokens", "?")
                tt = getattr(usage, "total_tokens", "?")
                log.info(
                    "[compat_llm] tokens model=%s prompt=%s completion=%s total=%s",
                    model, pt, ct, tt,
                )
        except Exception:
            pass
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            log.warning("[compat_llm] JSON parse fail: %s | raw=%.200s", exc, raw)
            return fallback

        ok, reason = _validate(parsed, facts, lang=lang)
        if not ok:
            # Surface the offending fragment to make non-Latin failures
            # diagnosable without re-running with debug instrumentation.
            try:
                log.warning(
                    "[compat_llm] validator rejected: %s | lang=%s | snap_summary=%.180s",
                    reason, lang, str((parsed or {}).get("relationship_snapshot", {}).get("summary", "")),
                )
            except Exception:
                log.warning("[compat_llm] validator rejected: %s", reason)
            return fallback

        # Coerce to plain dict — emit BOTH the new 7-section deep schema
        # AND the legacy 4-key flat schema (derived) for backward-compat
        # with mobile clients that haven't been updated yet.
        # Defensive: _validate already guarantees these keys exist, but use
        # .get() throughout so a malformed-but-validator-passed payload
        # (or any future validator regression) cannot crash the request —
        # outer try/except would catch but would log noisy stack traces
        # and return fallback; explicit .get() returns a usable shape.
        snap = parsed.get("relationship_snapshot", {}) or {}
        snap_tags = snap.get("tags", {}) or {}
        snap_clean = {
            "summary": str(snap.get("summary", "")).strip(),
            "tags": {
                "emotional_pull":      str(snap_tags.get("emotional_pull", "")).strip(),
                "marriage_potential":  str(snap_tags.get("marriage_potential", "")).strip(),
                "long_term_stability": str(snap_tags.get("long_term_stability", "")).strip(),
            },
        }
        sections_clean: dict[str, dict[str, str]] = {}
        for sec in _TEXT_SECTIONS:
            sec_obj = parsed.get(sec, {}) or {}
            sections_clean[sec] = {
                "text":      str(sec_obj.get("text", "")).strip(),
                "grounding": str(sec_obj.get("grounding", "")).strip(),
            }

        polished = {
            # ── New 7-section deep schema (primary) ──
            "relationship_snapshot": snap_clean,
            **sections_clean,
            # ── Legacy 4-key flat schema (derived for backward-compat) ──
            "compatibility_insight": snap_clean["summary"],
            "strengths": [
                sections_clean["emotional_alignment"]["text"],
                sections_clean["commitment_strength"]["text"],
            ],
            "challenges": [
                sections_clean["trust_loyalty"]["text"],
                sections_clean["conflict_patterns"]["text"],
            ],
            "marriage_outlook": sections_clean["future_direction"]["text"],
        }
        _cache_put(key, polished)
        _db_cache_put(key, polished, model)  # persist for cross-restart reuse
        return polished

    except Exception as exc:
        log.exception("[compat_llm] unexpected failure, returning fallback: %s", exc)
        return fallback


def cache_stats() -> dict[str, int]:
    """Diagnostic helper for tests / health endpoint."""
    with _cache_lock:
        return {"size": len(_cache), "cap": _CACHE_CAP}
