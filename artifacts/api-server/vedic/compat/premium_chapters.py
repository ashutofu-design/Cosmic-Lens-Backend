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

SYSTEM_PROMPT_PREMIUM = """You are a senior Vedic relationship counsellor speaking to a couple about their marriage compatibility report.

═══ VOICE ═══
• Warm, grounded, emotionally intelligent — like a wise family elder, not a textbook.
• Specific to THIS couple — never generic. Each line should feel like it was written about them.
• Honest about both strengths and frictions. Frame frictions as patterns to manage, never doom.
• Hindi/Hinglish/native-language speaking style depending on `language`.

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


def _safe_fallback(milan_facts: dict, chapter_scores: dict,
                   kp_promise: dict | None = None) -> dict[str, Any]:
    """Deterministic safe fallback when LLM toggle off / client unavailable.
    Uses engine drivers/cautions verbatim — guarantees a valid PDF can render."""
    p1n = (milan_facts.get("p1", {}) or {}).get("name", "Partner 1")
    p2n = (milan_facts.get("p2", {}) or {}).get("name", "Partner 2")
    total = milan_facts.get("total", 0)
    mx = milan_facts.get("max", 36)
    chs_engine = (chapter_scores or {}).get("chapters", {}) or {}
    chapters_out = []
    for k in CHAPTER_KEYS:
        ch = chs_engine.get(k, {}) or {}
        drv = ch.get("drivers", []) or []
        cau = ch.get("cautions", []) or []
        kd = "; ".join(drv) if drv else "The engine signals for this chapter are balanced — neither strongly positive nor a major friction zone."
        km = "; ".join(cau) if cau else "No significant friction is detected for this chapter; both partners can rely on natural baseline compatibility here."
        chapters_out.append({
            "key": k,
            "title": ch.get("title", k),
            "score_0_10": ch.get("score_0_10"),
            "kya_dikh": kd[:600] if len(kd) >= 50 else (kd + " — engine drivers are stable and well within healthy range.")[:600],
            "kya_matlab": km[:600] if len(km) >= 50 else (km + " — practical day-to-day life will not feel friction at this level.")[:600],
            "kya_dhyan": "Honest dialogue, mutual respect, and consistent care matter most. Consider joint daily prayers as a small grounding ritual.",
            "grounding": f"Based on engine score {ch.get('score_0_10','?')}/10 and engine drivers.",
        })
    return {
        "hidden_truth": f"This bond between {p1n} and {p2n} carries genuine compatibility "
                        f"({total} out of {mx}) with both natural strengths and growth zones.",
        "chapters": chapters_out,
        "special": [
            "Strong overall match score with engine support across multiple chapters.",
            "Both partners' core temperaments show meaningful alignment.",
            "Several engine drivers indicate practical compatibility.",
        ],
        "damage": [],
        "practical": [
            "Daily life will benefit from clear roles and gentle communication. "
            "Build small consistent rituals together — morning check-ins, weekend planning.",
            "Family dynamics deserve patient navigation. Each side has its own rhythm; "
            "respect that and find your own household culture.",
            "Long-term direction depends on both staying intentional. Yearly conversations "
            "about goals, growth, and what matters most keep you aligned.",
        ],
        "verdict": f"This relationship between {p1n} and {p2n} totals {total} out of {mx} on classical "
                   f"compatibility — a meaningful foundation. Stay honest, stay kind, stay curious about "
                   f"each other.",
        "_meta": {
            "model": "fallback", "version": _PREMIUM_VERSION,
            "kp_promise": _kp_couple_band(kp_promise),
            "hidden_signature": _kp_signature_line(kp_promise),
        },
    }


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
