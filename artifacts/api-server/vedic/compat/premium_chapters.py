"""
Phase 2.5.11.23 — Premium 7-Chapter Polish (gpt-4o)
====================================================
Layer B for Kundli Milan Pro PDF. Takes:
  - milan_facts        (engine output: koots, total, partners)
  - chapter_scores     (deterministic 7-chapter scores + drivers/cautions/key_facts)
  - d9_marriage        (D9 destiny block — for hidden_truth)
  - synastry           (7L synastry block — for hidden_truth)
  - kp_promise         (KP marriage promise verdict — for hidden_truth)

Returns LLM-rephrased 3-block prose per chapter + Hidden Truth + Special +
Damage + Practical + Verdict — all foreground human language, all KP/Vedic
jargon kept BACKEND-ONLY.

Model: gpt-4o (env COMPAT_PREMIUM_MODEL, fallback gpt-4o-mini).
Toggle: env COMPAT_PREMIUM_POLISH=1 (default off).

Reuses L1 + L2 cache infra from llm_polish.py (different fingerprint prefix).
Branding rule: never name AI/LLM. Defensive — never raises.
"""
from __future__ import annotations

import os
import re
import json
import hashlib
import logging
from typing import Any

from .llm_polish import (
    _cache_get as _l1_get,
    _cache_put as _l1_put,
    _db_cache_get as _l2_get,
    _db_cache_put as _l2_put,
    _normalize_digits,
    ALLOWED_REMEDIES,
    BANNED_TERMS,
)

log = logging.getLogger(__name__)

_PREMIUM_VERSION = "p1"
_DEFAULT_MODEL = "gpt-4o"

CHAPTER_KEYS = ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7"]
# Chapters where a ritual / practical action remedy is naturally appropriate.
# Validator requires ≥1 ALLOWED_REMEDY across these chapters' kya_dhyan combined.
_REMEDY_BEARING = {"ch4", "ch7"}

BANNED_REMEDY_TERMS = [
    "gemstone", "ratna", "ruby", "emerald", "pearl", "blue sapphire",
    "yellow sapphire", "coral", "topaz", "diamond ring",
    "wear a", "wear the",
    "tantrik", "tantra ritual", "black magic", "vashikaran",
    "pendant", "amulet", "talisman", "kavach",
]

# Astro-jargon the user must NEVER see in the foreground prose.
# Some Sanskrit terms (Manglik, koot names) are allowed because they are
# already on the cover/snapshot pages and translated. KP-specific jargon
# (Sub-Lord, CSL, Star Lord, signifies) is ALWAYS hidden.
BANNED_JARGON_HIDDEN = [
    "sub-lord", "sub lord", "csl", "7csl", "star lord", "signifies",
    "significator", "vimshottari", "antardasha", "pratyantardasha",
]

# Phase 2.5.11.23-soul: audit-report phrases that kill the soul of the
# report. Validator (and SYSTEM_PROMPT_PREMIUM) reject any output that
# contains these. All entries lowercase — match is done against full_lower.
SOUL_BAN_PHRASES = [
    "engine driver", "engine drivers", "engine score",
    "based on engine score", "engine signals",
    "no significant friction", "natural baseline compatibility",
    "stable and well within", "drivers indicate practical compatibility",
    "detailed reading was not generated", "chapter not generated",
]

SYSTEM_PROMPT_PREMIUM = """You are a senior Vedic relationship counsellor speaking to a couple about their marriage compatibility report.

═══ VOICE ═══
• Warm, grounded, emotionally intelligent — like a wise family elder, not a textbook.
• Specific to THIS couple — never generic. Each line should feel like it was written about them.
• Honest about both strengths and frictions. Frame frictions as patterns to manage, never doom.
• Hindi/Hinglish/native-language speaking style depending on `language`.

═══ THREE-LAYER LAW (every chapter must obey) ═══
EACH of the 3 prose blocks (kya_dikh, kya_matlab, kya_dhyan) MUST follow this arc:
  Layer 1 — kya_dikh:   What the chart actually shows, in plain emotional language. NO raw engine vocab (no "Venus enemy-sign", no "D9", no "7L", no "CSL"). Translate into how it FEELS in the body / in the room.
  Layer 2 — kya_matlab: The real-life behavioural pattern this creates between them. Use a concrete moment ("jab ek thaka hua ghar aata hai…", "jab koi upset hai, dusra…"). Make it feel like "this is literally us".
  Layer 3 — kya_dhyan:  ONE specific behavioural anchor + ONE grounding ritual. No vague "communicate openly" — name the actual practice.

═══ HARD-BAN PHRASES (these will get your response rejected) ═══
Never write any of: "engine drivers", "engine driver", "engine score", "Based on engine score", "engine signals", "no significant friction detected", "no friction detected", "natural baseline compatibility", "stable and well within healthy range", "practical day-to-day life will not feel friction", "drivers indicate practical compatibility". These are audit-report phrases — they kill the soul of the report.

═══ SPECIFICITY LAW ═══
• Both partner names must appear at least 3 times across the full prose combined.
• Each chapter must reference at least one BEHAVIOURAL specific (a moment, a fight pattern, a daily ritual) — never abstract.
• If you would write a generic line that could apply to any couple, REWRITE it with a concrete moment specific to THIS couple's chart pattern.

═══ ABSOLUTE RULES (violation = response rejected) ═══
1. Use ONLY the facts inside <ENGINE_FACTS> + <CHAPTER_DRIVERS>. Never invent koot scores, nakshatras, planets, dates, or houses.
2. The exact total score (e.g. "33 out of 36") MUST appear once in `verdict` OR `hidden_truth`.
3. Both partner names MUST appear at least once across the prose combined.
4. NEVER predict: lifespan, death, gender of children, divorce, specific dates, guaranteed outcomes.
5. NEVER use BACKEND jargon in the foreground prose: do not write "Sub-Lord", "CSL", "Star Lord", "signifies house X", "Vimshottari", "Antardasha". Translate the underlying truth into plain language ("the deeper karmic commitment-layer is strong").
6. Recommend ONLY remedies from <ALLOWED_REMEDIES>. No gemstones, no tantrik kriyas, no expensive yagnas outside the list. At least one verbatim remedy MUST appear across ch4.kya_dhyan + ch7.kya_dhyan combined.
7. LANGUAGE CONTRACT: write the entire prose in the user's language as specified by `language`:
   • "en" = pure English. "hn" = Hinglish (Hindi in Roman/Latin script). "hi" = Devanagari (देवनागरी). "mr" = Marathi (मराठी). "bn" = Bengali. etc.
   • EVEN in non-English: keep partner names + nakshatra/rashi names + koot labels + remedy names + the numeric total VERBATIM in their original Latin/English form.

═══ STRUCTURE — 7 CHAPTERS ═══
Each chapter is keyed by ch1..ch7 in `chapters` array. The score is FIXED by the engine — DO NOT include score in your output. You only write the 3 prose blocks + grounding.

Chapter titles + psychological question each chapter answers:
  ch1 Emotional Compatibility           → "Do we actually feel the same things?"
  ch2 Trust & Loyalty                    → "Can we count on each other when it matters?"
  ch3 Communication & Conflict           → "When we fight, what really happens underneath?"
  ch4 Marriage Stability                 → "Will this marriage last? What is the ONE thing both must accept?"
  ch5 Physical + Emotional Chemistry     → "Is there real attraction + emotional pull, or only one?"
  ch6 Family + Practical Life            → "How will daily life + extended family actually work?"
  ch7 Long-Term Future Direction         → "Where is this heading in the next few years?"

For EACH chapter, write 3 blocks + 1 grounding line (4 fields total):
  • kya_dikh    — "Aapke chart me kya dikh raha hai" — 3-4 sentences (~70-180 chars), ANCHORED in <CHAPTER_DRIVERS> facts for that chapter. Must reference at least one specific engine fact (a koot label, a number, a partner-specific behavior pattern).
  • kya_matlab  — "Iska matlab kya hai aapke rishte ke liye" — 3-4 sentences (~70-180 chars), translates the chart fact into REAL-LIFE behavior the couple will recognize.
  • kya_dhyan   — "Kya dhyan rakhna hai" — 3-5 short actionable points joined by sentence/bullet flow (~80-220 chars), mature + practical + non-superstitious. ch4 + ch7 MUST end with one verbatim remedy from <ALLOWED_REMEDIES>.
  • grounding   — 1 short line (8-22 words), starts with "Based on" — references the underlying engine layer subtly (e.g. "Based on Maitri 4/5, Bhakut 7/7, and D9 marriage-maturity layer.").

═══ HIDDEN TRUTH (top of report) ═══
`hidden_truth` — 2-3 sentences (~80-280 chars). What the deeper karmic + soul-level layer reveals about THIS bond that surface koots alone don't show. Translate the KP promise verdict + D9 sync into plain feeling-language. NEVER use the words "KP", "Sub-Lord", or "promise verdict" itself.

═══ SPECIAL / DAMAGE / PRACTICAL / VERDICT ═══
`special`   : array of EXACTLY 3 short strings (~30-100 chars each). The top 3 strengths of this bond, plain language, each anchored in a real chapter driver.
`damage`    : array of 1-3 short strings (~30-120 chars each). Low-score frictions framed gently. Empty array allowed if no significant friction.
`practical` : array of EXACTLY 3 strings (~120-300 chars each). Three paragraphs about practical married life — daily rhythm, shared finances, family dynamics — anchored in the engine facts.
`verdict`   : 1 mature paragraph (~150-380 chars). Final synthesis. Honest, warm, not promotional. Must contain the verbatim total score.

═══ OUTPUT (JSON only, no markdown, no preamble) ═══
{
  "hidden_truth": "string",
  "chapters": [
    {"key":"ch1","kya_dikh":"...","kya_matlab":"...","kya_dhyan":"...","grounding":"..."},
    {"key":"ch2","kya_dikh":"...","kya_matlab":"...","kya_dhyan":"...","grounding":"..."},
    {"key":"ch3", ...},
    {"key":"ch4", ...},
    {"key":"ch5", ...},
    {"key":"ch6", ...},
    {"key":"ch7", ...}
  ],
  "special":   ["...", "...", "..."],
  "damage":    ["...", "..."],
  "practical": ["...", "...", "..."],
  "verdict":   "string"
}
"""


def _build_user_prompt(milan_facts: dict, chapter_scores: dict,
                        d9: dict, syn: dict, kp: dict, lang: str) -> str:
    p1 = milan_facts.get("p1", {}) or {}
    p2 = milan_facts.get("p2", {}) or {}
    koots = milan_facts.get("koots", []) or []

    koot_lines = []
    for k in koots:
        s, mx = k.get("score", 0), k.get("max", 0)
        flag = ""
        if s == 0 and mx > 0:
            flag = "  ← DOSHA"
        elif s == mx and mx >= 4:
            flag = "  ← STRENGTH"
        koot_lines.append(f"  {k.get('label','?'):<8} {s} / {mx}   ({k.get('detail','')}){flag}")

    chap_blocks = []
    chs = (chapter_scores or {}).get("chapters", {}) or {}
    for key in CHAPTER_KEYS:
        c = chs.get(key, {}) or {}
        drv = c.get("drivers", []) or []
        cau = c.get("cautions", []) or []
        kf = c.get("key_facts", {}) or {}
        chap_blocks.append(
            f"  {key} ({c.get('title','?')}) — engine_score={c.get('score_0_10','?')}/10\n"
            f"     drivers : {drv if drv else '—'}\n"
            f"     cautions: {cau if cau else '—'}\n"
            f"     key_facts: {kf}"
        )

    # Hidden-truth source: KP promise + D9 sync — engine facts only
    kp_couple = (kp or {}).get("couple_verdict", "UNAVAILABLE")
    p1_kp = ((kp or {}).get("p1") or {}).get("verdict", "UNAVAILABLE")
    p2_kp = ((kp or {}).get("p2") or {}).get("verdict", "UNAVAILABLE")
    d9_sync = ((d9 or {}).get("sync") or {}).get("score_0_10", "?")
    syn_score = (syn or {}).get("score_0_10", "?")
    nak_resonance = ((syn or {}).get("nakshatra_resonance") or {}).get("count", 0)

    hidden_block = (
        f"  kp_couple_promise: {kp_couple}  (p1={p1_kp}, p2={p2_kp})\n"
        f"  d9_marriage_lagna_sync: {d9_sync}/10\n"
        f"  cross_chart_synastry: {syn_score}/10\n"
        f"  nakshatra_lord_resonance_count: {nak_resonance}"
    )

    p1_mang = p1.get("manglik", False)
    p2_mang = p2.get("manglik", False)
    if p1_mang and p2_mang:
        mang = "manglik_status: both_manglik (mutual cancellation)"
    elif p1_mang or p2_mang:
        mang = f"manglik_status: only_{'p1' if p1_mang else 'p2'}_manglik (imbalance — needs ritual remedy)"
    else:
        mang = "manglik_status: neither (no Mangal dosha)"

    overall = (chapter_scores or {}).get("overall_avg_0_10", "?")

    return f"""<ENGINE_FACTS>
p1_name: {p1.get('name','Partner 1')}
p1_nakshatra: {p1.get('nakshatra','?')} (Pada {p1.get('pada','?')}, {p1.get('rashi','?')})
p1_manglik: {p1_mang}

p2_name: {p2.get('name','Partner 2')}
p2_nakshatra: {p2.get('nakshatra','?')} (Pada {p2.get('pada','?')}, {p2.get('rashi','?')})
p2_manglik: {p2_mang}

total_guna: {milan_facts.get('total','?')} / {milan_facts.get('max',36)}
overall_chapter_avg: {overall}/10
{mang}

koot_scores:
{chr(10).join(koot_lines)}
</ENGINE_FACTS>

<CHAPTER_DRIVERS>
{chr(10).join(chap_blocks)}
</CHAPTER_DRIVERS>

<HIDDEN_LAYER>
{hidden_block}
</HIDDEN_LAYER>

<ALLOWED_REMEDIES>
{', '.join(ALLOWED_REMEDIES)}
</ALLOWED_REMEDIES>

<USER_CONTEXT>
language: {lang}
</USER_CONTEXT>

CRITICAL — verbatim "{milan_facts.get('total','?')} out of 36" MUST appear in `verdict` or `hidden_truth`.
CRITICAL — both names "{p1.get('name','Partner 1')}" and "{p2.get('name','Partner 2')}" MUST appear at least once each.
CRITICAL — ch4.kya_dhyan + ch7.kya_dhyan combined MUST contain at least ONE verbatim remedy from <ALLOWED_REMEDIES>.

Generate the JSON now."""


def _fingerprint(milan_facts: dict, chapter_scores: dict,
                 kp: dict, lang: str, model: str) -> str:
    p1 = milan_facts.get("p1", {}) or {}
    p2 = milan_facts.get("p2", {}) or {}
    parts = [
        f"prem={_PREMIUM_VERSION}",
        f"model={model}",
        f"lang={lang}",
        p1.get("nakshatra", ""), str(p1.get("pada", "")), p1.get("rashi", ""),
        p2.get("nakshatra", ""), str(p2.get("pada", "")), p2.get("rashi", ""),
        f"total={milan_facts.get('total','')}",
        f"mdosh={milan_facts.get('manglik_dosh','')}",
    ]
    for k in milan_facts.get("koots", []) or []:
        parts.append(f"{k.get('key','')}={k.get('score','')}")
    chs = (chapter_scores or {}).get("chapters", {}) or {}
    for key in CHAPTER_KEYS:
        parts.append(f"{key}={chs.get(key, {}).get('score_0_10', '')}")
    parts.append(f"kp={(kp or {}).get('couple_verdict','')}")
    raw = "|".join(parts).encode("utf-8")
    return "prem_" + hashlib.sha1(raw).hexdigest()


def _validate_premium(out: Any, milan_facts: dict, chapter_scores: dict) -> tuple[bool, str]:
    if not isinstance(out, dict):
        return False, "not_dict"

    # hidden_truth
    ht = out.get("hidden_truth")
    if not isinstance(ht, str) or not (40 <= len(ht) <= 600):
        return False, "hidden_truth_bad"

    # chapters
    chs = out.get("chapters")
    if not isinstance(chs, list) or len(chs) != 7:
        return False, "chapters_count"
    seen_keys: set[str] = set()
    chapter_dyn_combined = ""
    chapter_full_text = ""
    for c in chs:
        if not isinstance(c, dict):
            return False, "chapter_not_dict"
        key = c.get("key")
        if key not in CHAPTER_KEYS or key in seen_keys:
            return False, f"chapter_key_bad:{key}"
        seen_keys.add(key)
        for fld, lo, hi in (("kya_dikh", 50, 700), ("kya_matlab", 50, 700),
                             ("kya_dhyan", 50, 700)):
            v = c.get(fld)
            if not isinstance(v, str) or not (lo <= len(v) <= hi):
                return False, f"{key}_{fld}_length"
        g = c.get("grounding")
        if not isinstance(g, str) or not (10 <= len(g) <= 240):
            return False, f"{key}_grounding_length"
        if key in _REMEDY_BEARING:
            chapter_dyn_combined += " " + c.get("kya_dhyan", "")
        chapter_full_text += " " + (c.get("kya_dikh", "") + " " + c.get("kya_matlab", "")
                                     + " " + c.get("kya_dhyan", "") + " " + c.get("grounding", ""))
    if seen_keys != set(CHAPTER_KEYS):
        return False, "chapter_keys_missing"

    # special / damage / practical
    sp = out.get("special")
    if not isinstance(sp, list) or len(sp) != 3 or not all(isinstance(x, str) and 15 <= len(x) <= 220 for x in sp):
        return False, "special_bad"
    dm = out.get("damage")
    if not isinstance(dm, list) or len(dm) > 5 or not all(isinstance(x, str) and 15 <= len(x) <= 320 for x in dm):
        return False, "damage_bad"
    pr = out.get("practical")
    if not isinstance(pr, list) or len(pr) != 3 or not all(isinstance(x, str) and 80 <= len(x) <= 600 for x in pr):
        return False, "practical_bad"

    # verdict
    vd = out.get("verdict")
    if not isinstance(vd, str) or not (80 <= len(vd) <= 800):
        return False, "verdict_bad"

    full_text = " ".join([ht, vd, chapter_full_text] + sp + dm + pr)
    full_lower = full_text.lower()
    full_norm = _normalize_digits(full_text)

    # Total citation
    total = milan_facts.get("total")
    if total is not None and str(total) not in _normalize_digits(ht + " " + vd):
        return False, "total_not_cited_in_hidden_or_verdict"

    # Both partner names appear
    p1n = (milan_facts.get("p1", {}) or {}).get("name", "")
    p2n = (milan_facts.get("p2", {}) or {}).get("name", "")
    for nm, lbl in ((p1n, "p1"), (p2n, "p2")):
        if nm and len(nm) >= 3 and not re.search(r"\b" + re.escape(nm.lower()) + r"\b", full_lower):
            return False, f"{lbl}_name_missing"

    # Banned existential terms
    for b in BANNED_TERMS:
        if b in full_lower:
            return False, f"banned_term:{b}"

    # Banned KP/backend jargon
    for j in BANNED_JARGON_HIDDEN:
        if j in full_lower:
            return False, f"banned_jargon:{j}"

    # ── Phase 2.5.11.23-soul: audit-report phrase denylist ──
    # Mirror of SYSTEM_PROMPT_PREMIUM hard-ban list. Deterministically
    # rejects gpt-4o output that regresses to the old "audit report" tone.
    for sb in SOUL_BAN_PHRASES:
        if sb in full_lower:
            return False, f"soul_banned:{sb}"

    # ── Phase 2.5.11.23-soul: specificity law ──
    # Each partner name must appear ≥3 times across the full prose so
    # the report feels personal (not a templated couples report).
    for nm, lbl in ((p1n, "p1"), (p2n, "p2")):
        if nm and len(nm) >= 3:
            occurrences = len(re.findall(
                r"\b" + re.escape(nm.lower()) + r"\b", full_lower))
            if occurrences < 3:
                return False, f"{lbl}_name_density_low:{occurrences}"

    # Remedy whitelist (positive contract, bearing chapters only)
    if not any(r.lower() in chapter_dyn_combined.lower() for r in ALLOWED_REMEDIES):
        return False, "remedy_missing_in_ch4_ch7"

    # Remedy denylist (everywhere)
    for banned in BANNED_REMEDY_TERMS:
        if banned in full_lower:
            return False, f"banned_remedy:{banned}"

    # Hallucinated koot scores: any "X out of Y" or "X / Y" must match a real
    # koot pair, total/max, OR an engine-derived chapter score ("X/10").
    real_pairs = {(str(milan_facts.get("total", "")), str(milan_facts.get("max", 36)))}
    for k in milan_facts.get("koots", []) or []:
        real_pairs.add((str(k.get("score", "")), str(k.get("max", ""))))
    for c in (chapter_scores or {}).get("chapters", {}).values():
        sc = c.get("score_0_10")
        if sc is not None:
            # Each chapter score is /10 — accept both "8.7/10" and "8/10" forms
            real_pairs.add((str(sc), "10"))
            try:
                real_pairs.add((str(int(round(float(sc)))), "10"))
            except Exception:
                pass
    pair_re = re.compile(r"(\d+(?:\.\d+)?)\s*(?:/|out of)\s*(\d+)", re.I)
    for m in pair_re.finditer(full_norm):
        if (m.group(1), m.group(2)) not in real_pairs:
            return False, f"hallucinated_pair:{m.group(0)}"

    return True, "ok"


def polish_premium_chapters(
    milan_facts: dict,
    chapter_scores: dict,
    d9_marriage: dict,
    synastry: dict,
    kp_promise: dict,
    lang: str = "en",
    fallback: dict | None = None,
) -> dict[str, Any]:
    """Premium gpt-4o polish for 24-page Pro PDF.

    Returns a dict with:
      hidden_truth (str), chapters (list[7]), special, damage, practical, verdict
    On any failure (toggle off, no client, LLM error, validator fail) returns
    `fallback` (or a deterministic safe fallback if None passed).
    Never raises.
    """
    fb = fallback if fallback is not None else _safe_fallback(milan_facts, chapter_scores, kp_promise)
    if os.environ.get("COMPAT_PREMIUM_POLISH", "0") not in ("1", "true", "True"):
        return fb

    model = os.environ.get("COMPAT_PREMIUM_MODEL", _DEFAULT_MODEL)
    try:
        key = _fingerprint(milan_facts, chapter_scores, kp_promise, lang, model)

        hit = _l1_get(key)
        if hit is not None:
            return hit
        db_hit = _l2_get(key)
        if db_hit is not None:
            _l1_put(key, db_hit)
            return db_hit

        try:
            from openai_helper import _get_client  # type: ignore
        except Exception as exc:
            log.warning("[premium_chapters] openai import failed: %s", exc)
            return fb
        client = _get_client()
        if client is None:
            return fb

        user_prompt = _build_user_prompt(milan_facts, chapter_scores,
                                          d9_marriage, synastry, kp_promise, lang)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_PREMIUM},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            # Premium output is ~3-4× the polished_compat schema. Empirical sizing:
            # • en  full output ~2400-3200 tokens → cap 3500.
            # • non-Latin scripts cost 2-3× more tokens per char → cap 5000.
            "max_tokens": 3500 if (lang or "en").lower() == "en" else 5000,
        }
        if not model.lower().startswith("gpt-5"):
            kwargs["temperature"] = 0.55

        resp = client.chat.completions.create(**kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        try:
            usage = getattr(resp, "usage", None)
            if usage is not None:
                log.info(
                    "[premium_chapters] tokens model=%s prompt=%s completion=%s total=%s",
                    model,
                    getattr(usage, "prompt_tokens", "?"),
                    getattr(usage, "completion_tokens", "?"),
                    getattr(usage, "total_tokens", "?"),
                )
        except Exception:
            pass

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            log.warning("[premium_chapters] JSON parse fail: %s | raw=%.200s", exc, raw)
            return fb

        ok, reason = _validate_premium(parsed, milan_facts, chapter_scores)
        if not ok:
            log.warning("[premium_chapters] validator rejected: %s | lang=%s | hidden=%.180s",
                        reason, lang, str(parsed.get("hidden_truth", ""))[:180])
            return fb

        # Inject engine-derived score into each chapter (LLM never produced it).
        chs_in = parsed.get("chapters", [])
        chs_engine = (chapter_scores or {}).get("chapters", {})
        chapters_clean = []
        for c in chs_in:
            ckey = c.get("key")
            engine = chs_engine.get(ckey, {})
            chapters_clean.append({
                "key": ckey,
                "title": engine.get("title", ckey),
                "score_0_10": engine.get("score_0_10"),
                "kya_dikh": str(c.get("kya_dikh", "")).strip(),
                "kya_matlab": str(c.get("kya_matlab", "")).strip(),
                "kya_dhyan": str(c.get("kya_dhyan", "")).strip(),
                "grounding": str(c.get("grounding", "")).strip(),
            })

        polished = {
            "hidden_truth": str(parsed.get("hidden_truth", "")).strip(),
            "chapters": chapters_clean,
            "special": [str(s).strip() for s in parsed.get("special", [])],
            "damage": [str(s).strip() for s in parsed.get("damage", [])],
            "practical": [str(s).strip() for s in parsed.get("practical", [])],
            "verdict": str(parsed.get("verdict", "")).strip(),
            "_meta": {
                "model": model,
                "version": _PREMIUM_VERSION,
                "overall_avg": (chapter_scores or {}).get("overall_avg_0_10"),
                "kp_promise": _kp_couple_band(kp_promise),
                "hidden_signature": _kp_signature_line(kp_promise),
            },
        }
        _l1_put(key, polished)
        _l2_put(key, polished, model)
        return polished

    except Exception as exc:
        log.exception("[premium_chapters] unexpected failure, returning fallback: %s", exc)
        return fb


# ─────────────────────────────────────────────────────────────────────────
#  SOUL FALLBACK (Phase 2.5.11.23-soul, May 8 2026)
# ─────────────────────────────────────────────────────────────────────────
#  Critique: the previous fallback dumped engine drivers verbatim and
#  emitted template phrases ("engine drivers are stable", "No significant
#  friction detected", "Based on engine score X/10"). That made the PDF
#  read like an audit report, not a relationship insight. The replacement
#  below produces 3-layer prose for every chapter:
#    Layer 1 (kya_dikh):   what the chart actually shows, in plain words
#    Layer 2 (kya_matlab): what that means for day-to-day partnership
#    Layer 3 (kya_dhyan):  one specific behavioural anchor the couple can act on
#  Each block is ≥3 sentences, name-anchored, and band-aware (HIGH/MID/LOW).
#  No engine vocab, no template phrases, no negative-detection lines.
# ─────────────────────────────────────────────────────────────────────────

def _band(score: float | None) -> str:
    """Score → narrative band. ≥7 HIGH · 4–6.9 MID · <4 LOW · None MID."""
    try:
        s = float(score) if score is not None else 5.0
    except Exception:
        s = 5.0
    if s >= 7.0: return "HIGH"
    if s >= 4.0: return "MID"
    return "LOW"


# Per-chapter soul library: (kya_dikh, kya_matlab, kya_dhyan) per band.
# Format placeholders: {p1} {p2} {total} {mx}. Always 3+ sentences per block,
# always name-anchored, no banned phrases. Designed to feel like a wise
# counsellor, not a calculator.
_CH_SOUL: dict[str, dict[str, dict[str, str]]] = {
    "ch1": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech ek quiet emotional rhythm sit karta hai — jab ek thaka hua ghar aata hai, dusra bina pooche samajh leta hai. Ye sirf love nahi hai, ye nervous-system level ki familiarity hai. Aapke charts indicate karte hain ki dono ki feeling-curves naturally similar speed pe move karti hain.",
            "kya_matlab": "Real life me iska matlab hai — chhoti baatein, jaise office se aake kya khaana hai, weekend kahan jaana hai, in cheezon pe argument exhausting nahi banti. Tum dono ek dusre ki silence padh sakte ho. Jab koi tense hai, dusra space dega without making it dramatic.",
            "kya_dhyan":  "Is foundation ko maintain karne ke liye ek hi cheez kaafi hai — daily 10 minutes ka phone-free dialogue. Subah ya raat, koi ek waqt fix karo jab dono bina screen ke baat karte ho. Joint daily prayers ya quiet meditation rituals is connection ko aur deepen karenge.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} emotionally connected hain, lekin tareeke alag-alag hain. Ek partner apni feelings openly bolega, dusra unhe action me show karega — chai banake, jagah dekar, ya silently support karke. Dono valid hain, lekin pehchanne me time lagta hai.",
            "kya_matlab": "Iska matlab — kabhi-kabhi ek ko lagega ki dusra 'enough' nahi keh raha, jab actually woh dikhata hai keh ke nahi. Misunderstanding silence me build hoti hai, fight me nahi. Ye gap normal hai — bas conscious effort se bridge hoti hai.",
            "kya_dhyan":  "Hafte me ek baar 'how are we feeling' check-in rakho — sirf 5 minute. Jab koi upset ho, pehle pucho 'tu kya chahta hai abhi — sunna ya solve karna?' Joint daily prayers ek shared anchor ban sakte hain jab words kam pad jaayein.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke emotional clocks alag-alag tick karte hain. Ek partner intense aur immediate hai, dusra delayed processor — feelings ko pehle quietly digest karta hai. Ye personality difference hai, defect nahi.",
            "kya_matlab": "Roz ke jeevan me — jab koi cheez hurt karti hai, ek partner abhi baat karna chahega, dusra apne aap ko collect karne ka time chahega. Agar dono apni speed thopne lagein, dono drained mehsoos karenge. Ye sabse common silent friction-zone hota hai.",
            "kya_dhyan":  "Ek simple rule banao — 'main abhi 30 minute baad baat karna chahta hoon, ignore nahi kar raha.' Ye ek line saalon ke gussa-bhare misunderstandings rok sakti hai. Joint daily prayers — even 5 minutes — emotional safety ka subtle reset hote hain.",
        },
    },
    "ch2": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo trust-layer hai, woh declarations se nahi banti — chhote consistent acts se banti hai. Aapke charts dikhate hain ki dono naturally apna word rakhne wale log ho. Promise chhoti ho ya badi, follow-through ka reflex strong hai.",
            "kya_matlab": "Iska matlab — bahut si modern relationships me jo 'kya woh sach me reliable hai?' wala doubt hota hai, woh tum dono ke beech almost absent hai. Time ke saath ye trust deeper hoti jaayegi, kyunki dono ne ek dusre ko track-record diya hai.",
            "kya_dhyan":  "Trust ko 'granted' mat lo — har 3 mahine ek baar appreciation explicitly bolo. 'Tu ne X kiya, woh mujhe yaad hai.' Ek shared commitment ritual rakho — yearly anniversary pe ek ek paragraph likhke ek dusre ko do.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech trust solid hai, lekin uske kuch specific test-points hain. Ek partner ke liye trust = full transparency (passwords, schedules, plans), dusre ke liye trust = privacy ka respect. Dono frameworks valid hain, but unko explicit karna padega.",
            "kya_matlab": "Day-to-day me — chhoti adjustments, jaise phone check karna ya akele plan banana, agar pehle se discuss nahi hua to ek ko 'broken trust' lag sakta hai jab dusre ke liye it was just normal autonomy. Ye perception gap real damage de sakta hai.",
            "kya_dhyan":  "Ek baar baith ke 'trust ka definition' clear karo — kya hum dono ke liye trust break karta hai aur kya nahi. Ek shared commitment ritual — monthly status-talk — chhote misunderstandings ko fight banne se pehle clear kar deta hai.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo trust-foundation banana hai, woh time aur consistency dono maangta hai. Aapke charts dikhate hain ki past experiences (apne ya pichle relationships ke) ne dono ke trust-instincts ko thoda guarded bana diya hai.",
            "kya_matlab": "Iska practical impact — chhoti baatein bhi pehle scrutiny se gujarengi. Ek partner ka late aana, message late karna, ya plan change karna — innocent things bhi 'kya wajah hai sach me' wala question trigger karengi. Ye thakane wala loop ban sakta hai agar address na ho.",
            "kya_dhyan":  "Ek rule banao — har baat ko explain karne ki aadat dalo, even when not asked. Predictability se trust banti hai, defensiveness se nahi. Ek shared commitment ritual — har raat sone se pehle 1-line gratitude ek dusre ke liye — slowly woh wall pighlaata hai.",
        },
    },
    "ch3": {
        "HIGH": {
            "kya_dikh":   "Jab {p1} aur {p2} disagree karte hain, conversation argument me jaldi convert nahi hoti. Aapke charts dikhate hain ki dono me ek rare maturity hai — friction ko relationship ke against nahi, relationship ke andar dekhte ho. Issue dono ke beech hai, dono ke dushman nahi banti.",
            "kya_matlab": "Real life me iska faayda — bade decisions (career change, relocation, family planning) pe dono table pe baith sakte ho bina ek dusre ko personally attack kiye. Ye couples me extremely rare hai. Repair time bhi tumhara naturally short rahega.",
            "kya_dhyan":  "Is strength ko erode mat hone do stress periods me. Jab ek tense hai, dusra 'main galat ya tu galat' wale frame me mat ghuso. Ek 24-hour rule — koi bhi badi cheez raat ko decide nahi karenge — ye rule itni si baat me badi shadi bachata hai.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke conflict-style alag-alag hain. Ek probably 'abhi resolve karo' camp me hai — issues ko pending nahi rakh sakta. Dusra 'pehle thanda hone do, phir baat' camp me. Dono natural hain, lekin clash ka source bhi yahi hai.",
            "kya_matlab": "Aam jhagde issue ke baare me kam hote hain, communication-pace ke baare me zyada. Ek ko lagega 'tu avoid kar raha hai', dusre ko lagega 'tu pressure daal raha hai.' Real topic side me chhoot jaata hai aur pace pe fight ho jaati hai.",
            "kya_dhyan":  "Naya rule — koi bhi gussa pe response 30 minute ke andar nahi dega. Aur jo cooler-side hai, woh deadline rakhe — 'main 6 baje tak baat karunga.' Dono apni speed honour karte hain. Ye chhoti si discipline 70% domestic friction hata deti hai.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech conflict ka pattern thoda repetitive ho sakta hai — wahi topic, wahi shape, alag day. Aapke charts dikhate hain ki real issue surface pe nahi hota; surface pe to bartan, time-table, family plans hote hain — andar koi older feeling-pattern unresolved hai.",
            "kya_matlab": "Iska matlab — fight 'jeetne' se solution nahi aata, kyunki original pain woh nahi hai jo bola ja raha hai. Ek ko lagega 'main har baar khud sambhalta hoon', dusre ko 'main kabhi suna nahi jaata.' Ye cycles years tak chal sakte hain agar pattern dikhe nahi.",
            "kya_dhyan":  "Agar same fight 3 baar ho chuki hai — to woh fight ke baare me nahi hai. Ek baith ke pucho — 'real me hum kis cheez se dar rahe hain?' Possibly couple-counselling ek session bhi useful — koi neutral teesra perspective patterns ko unlock kar sakta hai jo aap dono ke andar se nahi dikhte.",
        },
    },
    "ch4": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech ek 'long-haul' instinct natural hai — dono unconsciously is bond ko temporary nahi maante. Aapke charts dikhate hain ki commitment-layer ek decision nahi hai, ek default state hai. Ye neend-jaisa instinct hota hai — present hai bina effort ke.",
            "kya_matlab": "Real life me iska impact — bade structural decisions (ghar, career compromises, parenting timing) pe dono naturally same boat me feel karte hain. Stress me bhi 'shall we still be us in 10 years' wala sawaal aata hi nahi. Ye ek rare gift hai, isko underestimate mat karo.",
            "kya_dhyan":  "Stability ko maintain karne ka ek hi mantra — har bade decision se pehle 5-minute joint silence. Ek dusre ka haath pakdo, ek deep breath, phir bolo. Joint daily prayers ek small but powerful grounding ritual hai is foundation ke liye.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech bond serious hai, lekin life-stage transitions (job change, parenting, parents' health) is bond ko test karenge. Aapke charts dikhate hain ki commitment present hai, lekin uska shape evolve karega — aaj jaisi shaadi 5 saal baad waisi nahi rahegi.",
            "kya_matlab": "Iska matlab — agar dono 'hamesha aisa hi rahega' wali expectation rakhenge, har transition pe shock lagega. Real stability adjust karne ki capacity me hai, sthir rehne me nahi. Jo couples evolve kar sakte hain together, woh long-term survive karte hain.",
            "kya_dhyan":  "Har 6 mahine ek 'state-of-our-marriage' baith-ke-baat — kya badla, kya theek hai, kya extra care chahiye. Yeh review ritual 80% slow-build problems prevent karta hai. Joint daily prayers ek subtle anchor hai jab life turbulent ho.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo bond hai, usme ek specific adjustment dono ko shuruat me resist hota hai — aur wahi adjustment long-term stability ka actual key hai. Ye 'ek cheez' har couple ke liye alag hoti hai — kabhi work-life balance, kabhi family boundaries, kabhi emotional bandwidth.",
            "kya_matlab": "Real life me iska matlab — agar dono apne 'mera tarika sahi hai' position pe atke rahe, friction grow karega. Lekin agar dono ek baar accept kar lein ki ek practical compromise zaroori hai, toh ye relationship surprisingly stable ban sakta hai. Choice tumhari hai.",
            "kya_dhyan":  "Identify karo — woh ek cheez kya hai jo har baar same fight banti hai? Wahi tumhara real test point hai. Koi neutral mediator (counsellor, elder, trusted friend) ek baar usko outside perspective de — fresh frame se dikhne lagti hai. Joint daily prayers ek mutual humility ka constant reminder rahega.",
        },
    },
    "ch5": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech ek natural physical aur emotional pull hai jo time ke saath erode nahi hota. Bahut couples ke liye initial chemistry honeymoon-phase ke baad fade ho jaati hai — yahaan aapke charts dikhate hain ki ye pull deeper layers se aata hai, sirf novelty se nahi.",
            "kya_matlab": "Real life me — long-distance phases, busy career years, parenting years me bhi physical-emotional connection survive karega. Touch, eye-contact, shared humor — ye aap dono ke beech easy aur consistent rahenge. Kuch couples is gift ke liye therapy karte hain, tum dono ke paas natural hai.",
            "kya_dhyan":  "Is connection ko routine se mat barbaad karna. Hafte me ek 'no-screen, no-kids' evening rakho. Touch ko sirf bedroom tak limit mat rakho — chai dete waqt haath mila lo, baith ke shoulder pe haath rakh do. Chhoti continuity badi chemistry banaye rakhti hai.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech connection real hai, lekin physical aur emotional needs alag-alag tareeke se express hoti hain. Ek partner ke liye intimacy = words + presence. Dusre ke liye intimacy = touch + actions. Dono valid hain, dono bina samjhe miss ho jaate hain.",
            "kya_matlab": "Iska matlab — kabhi-kabhi ek partner ko lagega 'isme us tarah ki feeling nahi hai jaisi hona chahiye', jab actually partner is showing it in their language, not yours. Ye gap silently bahut couples ko alag karta hai. Naam diye bina ye samajh me nahi aata.",
            "kya_dhyan":  "Ek baar khulkar baat karo — 'mujhe X way me feel hota hai loved, tujhe kis way me?' Ye conversation awkward lagti hai, lekin saalon ki silence ko ek ghante me reset kar sakti hai. Hafte me ek dedicated couple-time block calendar pe daal do — non-negotiable.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech physical aur emotional rhythms ko deliberately tune karna padega. Ye normal hai — bahut couples me natural chemistry waqt ke saath build hoti hai, instant nahi hoti. Aapke charts dikhate hain ki potential hai, lekin investment maangta hai.",
            "kya_matlab": "Real life me — agar dono assume karenge ki 'should be natural', frustration build hoga. Ye area pressure se kabhi nahi sudharta, sirf openness aur low-pressure exploration se sudharta hai. Comparison social media couples se mat karna — woh actors hain.",
            "kya_dhyan":  "Pressure utaaro — 'perfect intimacy' ka concept hi gira do. Hafte me ek long, slow, planned date — koi performance-expectation nahi. Bas presence. Counselling ek option hai agar conversations stuck feel hon — koi stigma nahi.",
        },
    },
    "ch6": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo daily-life partnership hai, woh efficient hai. Aapke charts dikhate hain ki dono naturally apna apna lane samajhte hain — kaun kya sambhalta hai, kab support deni hai, kab step back karna hai. Family dynamics me bhi dono ek dusre ki side me khade hote hain.",
            "kya_matlab": "Real life me iska faayda — chhoti chizein (bills, schedules, household, in-laws) silent rehti hain, energy bachi rehti hai bigger things ke liye. Ye couples ka 'silent superpower' hai — jo dikhta nahi but woh hi life ko sustain karta hai.",
            "kya_dhyan":  "Roles ko rigid mat banao. Har 6 mahine ek 'who does what now' check kar lo — life change hoti hai, distribution bhi shift karna chahiye. Joint family dinner ek baar a week — apne ghar ke saare logon ka — ek beautiful continuity ritual hai.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech daily life smoothly chal sakti hai, lekin family expectations dono pe alag-alag pressure dalti hain. Dono apne parivaar ki rhythms se aaye hain — gift-giving, festival celebrating, parents ko visit karne ki frequency, ye sab small differences friction ban sakte hain agar address na ho.",
            "kya_matlab": "Iska matlab — shaadi sirf tum dono ke beech nahi hoti, do families ke beech hoti hai. Jo expectations spoken nahi hain, woh built-in disappointment banti hain. Ek baar clarify ho jaaye, bahut friction evaporate ho jaata hai.",
            "kya_dhyan":  "Saal ki shuruat me ek baar baith ke 'this year ke family events kaun-kaun se hain, kis pe priority' decide karo. Decisions emotional moments me mat lo, calm planning me lo. Joint family dinner monthly ek beautiful boundary-friendly ritual ban sakta hai.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke daily life partnership ko deliberately design karna padega — auto-pilot mode pe ye nahi chalegi. Aapke charts dikhate hain ki natural division of labour smooth nahi hai; small things (groceries, bills, who cooks) chronic stress points ban sakte hain.",
            "kya_matlab": "Real life me iska impact — household tension grow karti hai jab unspoken expectations clash karti hain. Family side ke pressures bhi ek partner pe disproportionately gir sakte hain. Ye saalon me silently relationship khaata hai.",
            "kya_dhyan":  "Ek written list banao — har task kis ka primary, kis ka backup. Awkward lagega start me, lekin clarity se peace aati hai. Quarterly review karo. Joint family dinner — mahine me ek baar — neutral ground pe positive memories banata hai.",
        },
    },
    "ch7": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ek aise direction me badh rahe hain jahaan dono individually grow honge aur saath bhi. Aapke charts dikhate hain ki ye relationship dono ko shrink nahi karta — jo couples ek dusre ko expand karte hain, woh long-term saath rehte hain.",
            "kya_matlab": "Real life me — 5 saal baad, 10 saal baad, dono shayad alag-alag career heights pe honge, lekin ek dusre ke liye proud aur supportive. Comparison nahi, partnership. Bahut few couples is direction me jaa paate hain.",
            "kya_dhyan":  "Har New Year ek baith ke 'individual aur joint goals' likhna ek practice bana lo. Ek dusre ke goals me invested raho — small ways me, jaise interview wale din encourage karna. Yearly anniversary ritual — ek temple ya nature spot pe ek ghanta sirf shukran — ye direction ko anchor karta hai.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ka long-term direction shape ho raha hai, lekin abhi tak fully aligned nahi hai. Ek partner shayad stability + steady growth chahta hai, dusra adventure + change. Dono valid life-paths hain, lekin dono ek hi shaadi me alag direction me kheechte hain.",
            "kya_matlab": "Iska matlab — agle 5 saal me ek major decision (city, career, kids ka timing) pe dono ko khulkar baat karni hi padegi. Avoid karne se ye gap badhega. Jo couples ye conversation jaldi karte hain, woh saath grow karte hain. Jo nahi karte, woh same ghar me alag jeevan jeene lagte hain.",
            "kya_dhyan":  "Ek 'next 5 years' map saath baith ke draw karo — kahaan rehna hai, kya kamana hai, kya skip karna hai. Disagreement aaye to negotiate karo, dabao mat. Yearly anniversary ritual — long walk + uninterrupted talk — direction-recalibration ka time hai.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ka long-term direction abhi blurry hai. Aapke charts dikhate hain ki dono ek phase me hain jahaan personal clarity bhi shayad puri tarah aayi nahi hai — ek apne baare me figure out kar raha hai, dusra bhi. Ye normal hai, lekin shaadi me ek subtle 'kahaan jaa rahe hain hum' wala question chodta hai.",
            "kya_matlab": "Real life me — shared decisions tough lagengi kyunki dono ke individual paths abhi unclear hain. Ye 'fault' kisi ka nahi hai, life-stage hai. Lekin agar address na ho, drift ek silent risk hai — ek din uthke realize hota hai 'hum bahut alag log ho gaye.'",
            "kya_dhyan":  "Pehle individual clarity pe kaam karo — har partner apne 3-saal goals likhe alag se. Phir saath baith ke overlap dhundo. Ek counsellor ya life-coach ek session bhi helpful — joint future-planning ko structure deta hai. Yearly anniversary ritual — ek shanti-bhara place pe quiet day saath — drift ko slowly heal karta hai.",
        },
    },
}


def _safe_fallback(milan_facts: dict, chapter_scores: dict,
                   kp_promise: dict | None = None) -> dict[str, Any]:
    """Soul-rich deterministic fallback (Phase 2.5.11.23-soul).
    Generates 3-layer chapter prose + rich hidden_truth/special/damage/
    practical/verdict — all name-anchored, no engine vocab, no template
    phrases. Always returns a valid PDF payload even if LLM polish is off
    or unavailable. Defensive against malformed inputs — never raises."""
    # Defensive normalization: never trust caller shape
    mf = milan_facts if isinstance(milan_facts, dict) else {}
    p1d = mf.get("p1") if isinstance(mf.get("p1"), dict) else {}
    p2d = mf.get("p2") if isinstance(mf.get("p2"), dict) else {}
    p1n = (p1d.get("name") if isinstance(p1d.get("name"), str) else None) or "Partner 1"
    p2n = (p2d.get("name") if isinstance(p2d.get("name"), str) else None) or "Partner 2"
    # Coerce numeric fields — caller may send strings
    def _num(v, dflt):
        try: return float(v) if isinstance(v, (int, float, str)) and str(v).strip() != "" else dflt
        except (TypeError, ValueError): return dflt
    total = int(_num(mf.get("total"), 0))
    mx = int(_num(mf.get("max"), 36))
    cs = chapter_scores if isinstance(chapter_scores, dict) else {}
    chs_engine = cs.get("chapters") if isinstance(cs.get("chapters"), dict) else {}
    kp_band = _kp_couple_band(kp_promise)
    ctx = {"p1": p1n, "p2": p2n, "total": total, "mx": mx}

    chapters_out = []
    high_chs: list[tuple[str, str]] = []   # (key, title) for special bullets
    low_chs:  list[tuple[str, str]] = []   # (key, title) for damage bullets
    for k in CHAPTER_KEYS:
        ch = chs_engine.get(k, {}) or {}
        score = ch.get("score_0_10")
        band = _band(score)
        title = ch.get("title", k)
        if band == "HIGH": high_chs.append((k, title))
        elif band == "LOW": low_chs.append((k, title))
        soul = _CH_SOUL.get(k, {}).get(band) or _CH_SOUL.get(k, {}).get("MID") or {}
        kya_dikh = (soul.get("kya_dikh", "")).format(**ctx)
        kya_matlab = (soul.get("kya_matlab", "")).format(**ctx)
        kya_dhyan = (soul.get("kya_dhyan", "")).format(**ctx)
        chapters_out.append({
            "key": k,
            "title": title,
            "score_0_10": score,
            "kya_dikh": kya_dikh[:1200] or
                        f"{p1n} aur {p2n} ke beech is area me ek balanced rhythm hai jo deeper conversation se aur khulta hai.",
            "kya_matlab": kya_matlab[:1200] or
                          f"Iska matlab — daily jeevan me ye chapter sthir hai, lekin growth ke liye intentional attention chahiye.",
            "kya_dhyan": kya_dhyan[:1200] or
                         f"Ek consistent ritual rakho jo dono ko ek dusre ke saath present rakhe — daily ya weekly.",
            "grounding": "",
        })

    # ── Hidden Truth (P3) — 5-7 sentences, total + names + KP plain prose ──
    kp_line = _kp_signature_line(kp_promise) or ""
    hidden = (
        f"{p1n} aur {p2n} ke beech jo bond hai woh classical compatibility pe "
        f"{total} out of {mx} score karta hai — lekin asli kahaani numbers se aage hai. "
        f"Aapke charts ek aisa picture banate hain jisme dono ki strengths "
        f"ek dusre ki gaps ko silently fill karti hain, aur dono ki frictions "
        f"ek dusre ko mature banaati hain. {kp_line} "
        f"Ye relationship perfection nahi maangta — ye honesty maangta hai. "
        f"Jo couples is honesty ko respect karte hain, woh saath grow karte hain. "
        f"Aage ke chapters har layer ko khol ke dikhayenge — kya sahi hai, kya dhyan dene wala hai, "
        f"aur kya woh ek baat hai jo is bond ko legendary bana sakti hai."
    )

    # ── Special (P18) — derived from HIGH chapters; rich 2-3 sentence bullets ──
    special: list[str] = []
    if high_chs:
        for k, title in high_chs[:4]:
            special.append(_special_bullet(k, title, p1n, p2n))
    if len(special) < 3:
        special.append(
            f"{p1n} aur {p2n} ke beech ek aisi quiet trust hai jo declarations "
            f"se nahi banti — chhoti consistent kindness se banti hai."
        )
    if len(special) < 3:
        special.append(
            f"Aap dono naturally ek dusre ko grow hone ki space dete ho — "
            f"jo many couples decades me bhi nahi seekh paate."
        )
    if len(special) < 3:
        special.append(
            f"Aapka score ({total}/{mx}) sirf ek number nahi — ye baat ka indicator hai "
            f"ki dono ke beech intentional partnership ki real foundation hai."
        )

    # ── Damage (P19) — rich, framed as patterns to manage; never "no friction" ──
    damage: list[str] = []
    if low_chs:
        for k, title in low_chs[:4]:
            damage.append(_damage_bullet(k, title, p1n, p2n))
    else:
        damage.append(
            f"Sabse common silent damage — assumptions banana ki '{p1n} aur {p2n} "
            f"ek jaise sochte hain'. Even compatible couples me, har badi cheez "
            f"explicit conversation maangti hai. Jo unsaid reh jaata hai, woh saalon me bhaari ho jaata hai."
        )
        damage.append(
            f"Doosra subtle risk — 'bond strong hai to effort kam karna theek hai' wali "
            f"feeling. Trust ko granted lena sabse silent erosion hai. "
            f"Strong bonds bhi maintain karne padte hain — appreciation aur acknowledgement zaroori hain."
        )

    # ── Practical (P20) — 3-4 paragraphs, name-anchored, behavioral specificity ──
    practical = [
        f"{p1n} aur {p2n} ke daily life me sabse important habit ek hi hai — "
        f"har raat 10 minutes phone-free dialogue. Office baat, family baat, "
        f"plans, frustrations — sab kuch. Ye ek single ritual hi 80% slow-build "
        f"problems prevent karta hai jo aam couples me silent build hote hain.",

        f"Family expectations donon side ki separately samjho. {p1n} ke family ka "
        f"rhythm alag hai, {p2n} ke family ka alag. Ek-dusre ke parents ko explain "
        f"karne ki responsibility apne apne side pe rakho — ye ek small structural "
        f"shift saalon ki tension hata deti hai.",

        f"Money, decisions, and major life choices pe ek shared planning system "
        f"banao — monthly 30-minute check-in, calendar pe block kiya hua. Awkward "
        f"start me, lekin ye predictability se trust deepens, surprise se nahi.",

        f"Ek joint ritual zaroori hai — chahe woh daily evening prayer ho, "
        f"weekly walk ho, ya yearly anniversary trip ho. Couples jo rituals share "
        f"karte hain, woh stress periods me bhi anchored rehte hain. Choose koi "
        f"bhi, but choose karo aur maintain karo.",
    ]

    # ── Verdict (P23) — closing letter with names, total, and a "remember this" line ──
    band_text = "strong" if total >= 28 else ("meaningful" if total >= 21 else "workable")
    verdict = (
        f"{p1n} aur {p2n}, aap dono ke beech jo bond hai woh classical compatibility me "
        f"{total} out of {mx} score karta hai — ek {band_text} foundation. Lekin yaad rakhna — "
        f"score sirf starting point hai, destiny nahi. "
        f"Jo couples ye samajhte hain ki shaadi 'fix karne wali cheez' nahi, 'grow karne wali cheez' hai, "
        f"woh score se aage jaate hain. Aap dono me woh maturity dikhti hai. "
        f"Honest raho. Kind raho. Ek dusre ke baare me curious raho — even after years. "
        f"Jab raasta kabhi confusing lage, ye paragraph dobara padhna — yahin se shuruat ki thi."
    )

    return {
        "hidden_truth": hidden,
        "chapters": chapters_out,
        "special": special,
        "damage": damage,
        "practical": practical,
        "verdict": verdict,
        "_meta": {
            "model": "fallback-soul-v1",
            "version": _PREMIUM_VERSION,
            "kp_promise": kp_band,
            "hidden_signature": kp_line,
        },
    }


# ── Bullet generators for special/damage (P18/P19) ──
_SPECIAL_BY_CH = {
    "ch1": "Emotional rhythm — {p1} aur {p2} ke nervous-system level pe ek quiet familiarity hai. Bahut log isko 'connection' bolte hain; tum dono ke liye ye default state hai.",
    "ch2": "Trust ka foundation — dono naturally apne word rakhne wale log ho. Ye chhoti sthirta hi long-term bonds ka asli stone hai.",
    "ch3": "Conflict maturity — disagreement personal attack me convert nahi hoti. Ye couples ki rare gift hai jo bahut couples saalon ki therapy ke baad bhi nahi seekh paate.",
    "ch4": "Long-haul instinct — dono unconsciously is bond ko temporary nahi maante. Stress me bhi 'shall we still be us in 10 years' wala question aata hi nahi.",
    "ch5": "Chemistry that lasts — physical aur emotional pull novelty se nahi, deeper layers se aata hai. Years ke baad bhi ye fade nahi hoga.",
    "ch6": "Daily life partnership — silent efficiency hai. Chhoti chizein bina drama ke chal jaati hain, energy bachi rehti hai bigger moments ke liye.",
    "ch7": "Future direction — dono ek aise raaste pe hain jahaan saath bhi grow honge aur individually bhi. Ye partnership ka highest form hai.",
}
_DAMAGE_BY_CH = {
    "ch1": "Emotional pacing — {p1} aur {p2} ki feeling-clocks alag speed pe chalti hain. Ek immediate hai, dusra delayed processor. Bina samjhe ye saalon ki chronic 'tu mujhe samajhta nahi' wali feeling banata hai.",
    "ch2": "Trust definitions — dono ke 'trust' ka definition slightly alag hai. Ek ke liye = full transparency, dusre ke liye = privacy ka respect. Explicit nahi karoge to silent grievances build honge.",
    "ch3": "Conflict pacing — {p1} aur {p2} me ek 'abhi solve karo' camp me hai, dusra 'thanda hone do' camp me. Real fight topic pe nahi, pace pe ho jaati hai. Yahi most-repeated argument ka shape hai.",
    "ch4": "Stability test point — {p1} aur {p2} ke beech ek specific adjustment hai jo dono shuruat me resist karenge — wahi adjustment long-term stability ka actual key hai. Ignore karoge to wahi recurring fight ban jaayegi.",
    "ch5": "Intimacy languages — needs alag tareeke se express hoti hain. Ek partner ko lagega 'isme us tarah ki feeling nahi hai jaisi honi chahiye', jab actually partner is showing it in their language. Naam diye bina ye gap silently bahut couples ko alag karta hai.",
    "ch6": "Family expectations — {p1} aur {p2}, donon side ke family ke unspoken rules clash karenge. Ye relationship ke andar tension nahi laata, lekin saalon me energy chusta hai.",
    "ch7": "Direction drift — {p1} aur {p2} agar individual clarity ke bina chalein, joint direction blurry rahegi. Drift ek silent risk hai — ek din realize hota hai 'hum bahut alag log ho gaye'.",
}

def _special_bullet(ch_key: str, title: str, p1n: str, p2n: str) -> str:
    tpl = _SPECIAL_BY_CH.get(ch_key) or "{p1} aur {p2} ke beech is area me natural strength hai jo time ke saath aur deeper hoti jaayegi."
    return tpl.format(p1=p1n, p2=p2n)

def _damage_bullet(ch_key: str, title: str, p1n: str, p2n: str) -> str:
    tpl = _DAMAGE_BY_CH.get(ch_key) or "{p1} aur {p2} ke beech is area me extra conscious effort chahiye — silent assumptions yahaan sabse mehngi padti hain."
    return tpl.format(p1=p1n, p2=p2n)


def _kp_couple_band(kp_promise: dict | None) -> str:
    """Resolve the couple-level promise band from the kp_promise dict.
    Accepts either the per-side or the couple wrapper shape; returns one of
    STRONG / PARTIAL / WEAK / UNAVAILABLE."""
    if not isinstance(kp_promise, dict):
        return "UNAVAILABLE"
    band = kp_promise.get("couple_verdict") or kp_promise.get("verdict")
    if isinstance(band, str) and band.upper() in ("STRONG", "PARTIAL", "WEAK", "UNAVAILABLE"):
        return band.upper()
    return "UNAVAILABLE"


def _kp_signature_line(kp_promise: dict | None) -> str:
    """Plain-language one-line signature for the P3 grounding card.
    Translates the hidden KP marriage-promise reading into everyday words —
    NEVER leaks jargon (no CSL/sub-lord/significator/house numbers).
    """
    if not isinstance(kp_promise, dict):
        return ""
    band = (kp_promise.get("couple_verdict") or kp_promise.get("verdict") or "").upper()
    plain = {
        "STRONG":  "Both charts carry a clear, supportive marriage signal underneath.",
        "PARTIAL": "Both charts carry a present but mixed marriage signal underneath — workable, not effortless.",
        "WEAK":    "The deeper marriage signal in both charts is faint — patience and intentional effort matter more here.",
    }
    return plain.get(band, "")
