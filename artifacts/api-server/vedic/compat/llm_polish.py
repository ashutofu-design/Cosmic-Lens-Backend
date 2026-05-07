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
_PROMPT_VERSION = "v7"

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
6. If user_lang="hi", mix natural Hinglish ("yeh rishta", "samay ke saath"). If "en", pure English.

═══ OUTPUT (JSON only, no markdown, no preamble) ═══
{
  "compatibility_insight": "<3-4 sentences, ~80-110 words. Open with the emotional dynamic, anchor with the exact total score, end with grounded hope.>",
  "strengths": ["<2-4 bullets, each 2-3 sentences. Explain what each strong koot FEELS like in daily life.>"],
  "challenges": ["<2-4 bullets, each 2-3 sentences. Describe the real friction pattern, end with ONE specific remedy from the allowed list. Never doom-frame.>"],
  "marriage_outlook": "<4-5 sentences, ~120-150 words. Practical, non-fatalistic. Acknowledge any cancellation factors. Mention 2-3 specific allowed remedies.>"
}

═══ OUTPUT CHECKLIST (verify before responding — non-negotiable) ═══
Before you submit, confirm:
☐ The exact total score (e.g. "14.5 out of 36") appears literally inside compatibility_insight.
☐ BOTH partner nakshatra OR rashi names from <ENGINE_FACTS> appear at least once across the full output (each partner needs at least one chart-anchor).
☐ Any "X / Y" or "X out of Y" numeric pair you write MUST exactly match a real koot score from <ENGINE_FACTS> (or the total/max). Do not invent or round koot numbers.
☐ Do NOT name any nakshatra or rashi other than the ones in <ENGINE_FACTS>. Generic words like "stars", "signs", "Moon" are fine.
☐ Every entry in "challenges" ends with ONE remedy phrase copied verbatim from <ALLOWED_REMEDIES> (e.g. "Maha Mrityunjaya Jaap", "consult a qualified Jyotishi"). Do not invent gemstones, stones, or rituals outside the list.
☐ No banned terms: lifespan, death, gender of children, "guaranteed to", "definitely will".
☐ Output is valid JSON, no markdown fences, no commentary outside the JSON object."""


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
def _validate(out: Any, facts: dict[str, Any]) -> tuple[bool, str]:
    """Return (ok, reason). ok=False means caller must use fallback."""
    if not isinstance(out, dict):
        return False, "not_dict"
    required = ["compatibility_insight", "strengths", "challenges", "marriage_outlook"]
    for k in required:
        if k not in out:
            return False, f"missing_key:{k}"
    if not isinstance(out["strengths"], list) or not isinstance(out["challenges"], list):
        return False, "lists_expected"
    if not (1 <= len(out["strengths"]) <= 5):
        return False, "strengths_count"
    if not (1 <= len(out["challenges"]) <= 5):
        return False, "challenges_count"

    insight = str(out["compatibility_insight"])
    outlook = str(out["marriage_outlook"])
    full_text = " ".join(
        [insight, outlook] + [str(x) for x in out["strengths"]]
        + [str(x) for x in out["challenges"]]
    )
    full_lower = full_text.lower()

    # Verbatim total score must appear
    total = facts.get("total")
    if total is not None and str(total) not in insight:
        return False, "total_not_cited"

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
        nak = (p.get("nakshatra") or "").split()[0]
        rashi = (p.get("rashi") or "").strip()
        name = (p.get("name") or "").strip()
        if _word_in(nak):
            return True, ""
        if _word_in(rashi):
            return True, ""
        # Names shorter than 3 chars are too collision-prone even with
        # word boundaries (e.g. "An" still matches the standalone word
        # "an"). Fall back to nakshatra/rashi only in that case.
        if name and len(name) >= 3 and _word_in(name):
            return True, ""
        return False, f"{label}_anchor_missing"

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
    # (case-insensitive) somewhere across the challenges block or the
    # marriage_outlook. Keyword-only matching previously allowed
    # paraphrases like "spiritual healer" to slip through; we now
    # require the exact whitelisted phrase. The user is guaranteed to
    # see at least one approved remedy.
    challenges_text = " ".join(str(c) for c in out["challenges"]).lower()
    outlook_lower = outlook.lower()
    remedy_zone = challenges_text + " " + outlook_lower
    allowed_lower = [r.lower() for r in ALLOWED_REMEDIES]
    if not any(r in remedy_zone for r in allowed_lower):
        return False, "challenge_missing_remedy"
    # Negative contract: no banned remedy term anywhere in the
    # remedy-bearing sections (per-bullet to localise the failure
    # reason). This is a denylist safety net — the positive contract
    # above is the actual whitelist guarantee.
    BANNED_REMEDY_TERMS = [
        "gemstone", "ratna", "ruby", "emerald", "pearl", "blue sapphire",
        "yellow sapphire", "coral", "topaz", "diamond ring",
        "wear a", "wear the",            # "wear a ruby", "wear the pearl"
        "tantrik", "tantra ritual", "black magic", "vashikaran",
        "pendant", "amulet", "talisman", "kavach",
    ]
    for ch in out["challenges"]:
        ch_l = str(ch).lower()
        for banned in BANNED_REMEDY_TERMS:
            if banned in ch_l:
                return False, f"banned_remedy:{banned}"
    for banned in BANNED_REMEDY_TERMS:
        if banned in outlook_lower:
            return False, f"banned_remedy_in_outlook:{banned}"

    # Fact-lock: any "X / Y" or "X out of Y" numeric pair the LLM uses
    # MUST correspond to a real koot score (or the total) from facts.
    # This catches hallucinated koot scores even when overall narrative
    # passes other checks.
    real_pairs = {(str(facts.get("total", "")), str(facts.get("max", 36)))}
    for k in facts.get("koots", []):
        real_pairs.add((str(k.get("score", "")), str(k.get("max", ""))))
    pair_re = re.compile(r"(\d+(?:\.\d+)?)\s*(?:/|out of)\s*(\d+)", re.I)
    for m in pair_re.finditer(full_text):
        if (m.group(1), m.group(2)) not in real_pairs:
            return False, f"hallucinated_score:{m.group(0)}"

    # Vocabulary-lock: any nakshatra or rashi name appearing in the
    # prose must match either p1 or p2's actual chart. Catches LLMs
    # that name-drop unrelated nakshatras/rashis (e.g. invents "Krittika"
    # when neither partner has it).
    p1 = facts.get("p1", {}) or {}
    p2 = facts.get("p2", {}) or {}
    allowed_naks = {
        (p1.get("nakshatra") or "").split()[0].lower() if p1.get("nakshatra") else "",
        (p2.get("nakshatra") or "").split()[0].lower() if p2.get("nakshatra") else "",
    } - {""}
    allowed_rashis = {
        (p1.get("rashi") or "").lower(), (p2.get("rashi") or "").lower(),
    } - {""}
    # Whole-word, case-insensitive scan. Previously we only matched
    # capitalized tokens which let lowercase hallucinations slip
    # through ("yeh shravana wali energy ...") in Hinglish output.
    for word_match in re.finditer(r"\b([A-Za-z][A-Za-z]+)\b", full_text):
        token = word_match.group(1).lower()
        if token in _KNOWN_NAKSHATRAS and token not in allowed_naks:
            return False, f"unknown_nakshatra:{word_match.group(1)}"
        if token in _KNOWN_RASHIS and token not in allowed_rashis:
            return False, f"unknown_rashi:{word_match.group(1)}"

    # Length sanity — reject blatantly long/short
    if not (50 <= len(insight) <= 1200):
        return False, "insight_length"
    if not (80 <= len(outlook) <= 1500):
        return False, "outlook_length"

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
            # Phase 2.5.11.20-A: trimmed 900 → 600 (real outputs ~480 tokens;
            # 600 leaves headroom while cutting worst-case cost ~33%).
            "max_tokens": 600,
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

        ok, reason = _validate(parsed, facts)
        if not ok:
            log.warning("[compat_llm] validator rejected: %s", reason)
            return fallback

        # Coerce to plain dict in fallback shape
        polished = {
            "compatibility_insight": str(parsed["compatibility_insight"]).strip(),
            "strengths": [str(x).strip() for x in parsed["strengths"]],
            "challenges": [str(x).strip() for x in parsed["challenges"]],
            "marriage_outlook": str(parsed["marriage_outlook"]).strip(),
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
