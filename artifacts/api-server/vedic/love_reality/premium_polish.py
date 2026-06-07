"""
Love Reality Pro PDF — GPT polish + chapter depth regen (Milan-style pipeline).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any

from vedic.love_reality.pdf_text_safe import (
    polish_content_lang,
    sanitize_love_reality_pro_premium,
)
from vedic.compat.llm_polish import (
    _cache_get as _l1_get,
    _cache_put as _l1_put,
    _db_cache_get as _l2_get,
    _db_cache_put as _l2_put,
)
from vedic.compat.premium_chapters import (
    CHAPTER_BODY_KEY,
    normalize_pro_pdf_lang,
    _openai_regen_chapters_depth,
    _parsed_chapter_row_for_key,
)
from vedic.compat.premium_chapters import _PREMIUM_DEPTH_REGEN_MAX_ROUNDS

log = logging.getLogger(__name__)

_LOVE_VERSION = "lr1"
_DEFAULT_MODEL = os.environ.get("LOVE_REALITY_PREMIUM_MODEL") or os.environ.get(
    "COMPAT_PREMIUM_MODEL", "gpt-4o"
)
LOVE_CHAPTER_KEYS = ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6"]
LOVE_SEMANTIC_KEYS = [
    "love_connection",
    "breakup",
    "loyalty",
    "will_return",
    "future_outcome",
    "red_flags",
]
KEY_BY_CH = {
    "ch1": "love_connection",
    "ch2": "breakup",
    "ch3": "loyalty",
    "ch4": "will_return",
    "ch5": "future_outcome",
    "ch6": "red_flags",
}
_LOVE_MIN_CHAPTER_WORDS = int(os.environ.get("LOVE_REALITY_MIN_CHAPTER_WORDS", "220"))
_LOVE_MIN_CHAPTER_CHARS = int(os.environ.get("LOVE_REALITY_MIN_CHAPTER_CHARS", "1200"))
_LOVE_MIN_PARAGRAPHS = int(os.environ.get("LOVE_REALITY_MIN_PARAGRAPHS", "3"))
_LOVE_MIN_PARA_WORDS = int(os.environ.get("LOVE_REALITY_MIN_PARA_WORDS", "25"))
_BULLET_LINE_RE = re.compile(r"^\s*[-•*]\s+", re.M)
_CHART_SIGNAL_RE = re.compile(
    r"\b(?:Lagna|Moon|Mercury|Venus|Jupiter|Mars|Saturn|Rahu|Ketu|7th|12th|Upapada|UL|dasha|house)\b",
    re.I,
)


def _env_flag(name: str, default: str = "0") -> bool:
    return (os.environ.get(name) or default).strip().lower() in ("1", "true", "yes", "on")


def _polish_enabled() -> bool:
    env = (os.environ.get("LOVE_REALITY_PREMIUM_POLISH") or "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return _env_flag("COMPAT_PREMIUM_POLISH", "1")


def _depth_regen_enabled() -> bool:
    if not _env_flag("LOVE_REALITY_DEPTH_REGEN", ""):
        return _env_flag("COMPAT_PREMIUM_DEPTH_REGEN", "1")
    return _env_flag("LOVE_REALITY_DEPTH_REGEN", "1")


def _cache_disabled() -> bool:
    return _env_flag("LOVE_REALITY_CACHE_DISABLE") or _env_flag(
        "COMPAT_PREMIUM_CACHE_DISABLE"
    )


def _love_polish_fingerprint(bundle: dict, lang: str, model: str) -> str:
    """Stable key from engine scores + lang + model (Milan-style L1/L2 reuse)."""
    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    parts = [
        f"love={_LOVE_VERSION}",
        f"model={model}",
        f"lang={lang}",
        p1.get("nakshatra", ""),
        p1.get("moonSign", "") or p1.get("rashi", ""),
        p2.get("nakshatra", ""),
        p2.get("moonSign", "") or p2.get("rashi", ""),
        f"lc={lc.get('score', '')}",
        f"bu={bu.get('breakup_score', bu.get('score', ''))}",
        f"ly={ly.get('loyalty_score', ly.get('score', ''))}",
        f"wr={wr.get('return_probability', wr.get('score', ''))}",
        f"fo={fo.get('future_score', fo.get('score', ''))}",
        f"aff={((bundle.get('couple_signals') or {}).get('combined_affliction', ''))}",
    ]
    raw = "|".join(str(x) for x in parts).encode("utf-8")
    return "love_" + hashlib.sha1(raw).hexdigest()


def _love_polish_cache_depth_ok(hit: dict) -> bool:
    """Reject shallow cached polish (treat as miss)."""
    chapters = hit.get("chapters") or []
    if len(chapters) < 6:
        return False
    ok_bodies = 0
    for ch in chapters:
        body = (ch.get(CHAPTER_BODY_KEY) or ch.get("chapter_body") or "").strip()
        if _love_chapter_depth_failure_reason(body) is None:
            ok_bodies += 1
    return ok_bodies >= 6


def _empty_shell(model: str, reason: str) -> dict[str, Any]:
    return {
        "hidden_truth": "",
        "chapters": [],
        "special": [],
        "damage": [],
        "practical": [],
        "verdict": "",
        "_meta": {"model": model, "version": _LOVE_VERSION, "reason": reason},
    }


def _facts_summary(bundle: dict) -> str:
    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}

    def _lines(label: str, d: dict) -> list[str]:
        field_labels = {
            "score": "Score",
            "breakup_score": "Breakup score",
            "loyalty_score": "Loyalty score",
            "return_probability": "Return probability",
            "future_score": "Future score",
            "risk_level": "Risk level",
            "loyalty_level": "Loyalty level",
            "return_chance": "Return chance",
            "outcome": "Outcome",
            "current_phase": "Current phase",
            "emotional_summary": "Summary",
        }
        out = [f"=== {label} ==="]
        for k in ("score", "breakup_score", "loyalty_score", "return_probability", "future_score"):
            if k in d and d[k] is not None:
                out.append(f"{field_labels[k]}: {d[k]}")
        for k in ("risk_level", "loyalty_level", "return_chance", "outcome", "current_phase"):
            if d.get(k):
                out.append(f"{field_labels[k]}: {d[k]}")
        if d.get("emotional_summary"):
            out.append(f"{field_labels['emotional_summary']}: {d['emotional_summary']}")
        reasons = d.get("reasons") or []
        if reasons:
            out.append("reasons:")
            for r in reasons[:12]:
                out.append(f"  - {r}")
        return out

    rc = bundle.get("reader_context") or {}

    parts = [
        f"p1_name: {p1.get('name', 'You')}",
        f"p1_moon: {p1.get('moonSign') or p1.get('rashi', '?')}",
        f"p1_nakshatra: {p1.get('nakshatra', '?')}",
        f"p2_name: {p2.get('name', 'Partner')}",
        f"p2_moon: {p2.get('moonSign') or p2.get('rashi', '?')}",
        f"p2_nakshatra: {p2.get('nakshatra', '?')}",
    ]
    if rc.get("primary_gender_inferred"):
        parts.append(
            f"READER_PRIMARY_GENDER (p1 profile, tone only): {rc.get('primary_gender_inferred')} "
            f"(raw: {rc.get('primary_gender_raw') or 'n/a'})"
        )
    if rc.get("will_return_note"):
        parts.append(
            "WILL_RETURN_REALITY_PRIOR: ~90% of estranged situations do not see X return in a real way; "
            "match prose to return_probability — only strong reunion yogas justify optimistic reunion language."
        )
    ledger = lc.get("score_ledger") or []
    if ledger:
        parts.append("=== LOVE_SCORE_LEDGER (cite when explaining cover score) ===")
        for row in ledger[:16]:
            if isinstance(row, dict):
                if row.get("base") is not None:
                    parts.append(f"  {row.get('label')}: base {row.get('base')} — {row.get('note', '')}")
                elif row.get("delta") is not None:
                    parts.append(f"  {row.get('label')}: {row.get('delta'):+} — {row.get('note', '')}")
                else:
                    parts.append(f"  {row.get('label')}: {row.get('note', '')}")
    bridge = bundle.get("narrative_bridge")
    if bridge:
        parts.append(f"NARRATIVE_BRIDGE (use in verdict if scores conflict): {bridge}")
    parts.extend(
        [
            *_lines("LOVE_COMPATIBILITY", lc),
            *_lines("BREAKUP_CHANCES", bu),
            *_lines("LOYALTY_CHECK", ly),
            *_lines("WILL_RETURN", wr),
            *_lines("FUTURE_OUTCOME", fo),
        ],
    )
    ly_locks = ly.get("narrative_locks") or []
    if ly_locks:
        parts.append("=== LOYALTY_NARRATIVE_LOCKS (MANDATORY) ===")
        for line in ly_locks:
            parts.append(f"  - {line}")
    if ly.get("loyalty_score") is not None and int(ly.get("loyalty_score") or 0) < 52:
        parts.append(
            "LOYALTY_CHAPTER_RULE: loyalty_score is LOW — do NOT write that any partner is "
            "'naturally loyal', 'devoted by nature', or 'faithful because Venus is strong'. "
            "Venus in own sign (e.g. Taurus) = attachment STYLE only, NOT proof of real-world loyalty."
        )
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    try:
        parts.append(
            "<STRUCTURED_CHART_DATA>\n"
            + json.dumps({"p1_planets": k1.get("planets"), "p2_planets": k2.get("planets")}, ensure_ascii=False)[:12000]
            + "\n</STRUCTURED_CHART_DATA>"
        )
    except Exception:
        pass
    return "\n".join(parts)


def _love_word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def _love_meaningful_paragraph_count(body: str) -> int:
    parts = [p.strip() for p in re.split(r"\n\s*\n", (body or "").strip()) if p.strip()]
    return sum(1 for p in parts if _love_word_count(p) >= _LOVE_MIN_PARA_WORDS)


def _love_is_bullet_heavy(body: str) -> bool:
    t = (body or "").strip()
    if not t:
        return False
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    if not lines:
        return False
    bullet_lines = sum(1 for ln in lines if _BULLET_LINE_RE.match(ln))
    if bullet_lines >= 3 and bullet_lines >= len(lines) * 0.55:
        return True
    return t.count("•") >= 4 and _love_word_count(t) < _LOVE_MIN_CHAPTER_WORDS


def _love_chapter_depth_failure_reason(body: str) -> str | None:
    t = (body or "").strip()
    if not t:
        return "empty"
    wc = _love_word_count(t)
    if wc < _LOVE_MIN_CHAPTER_WORDS:
        return f"words:{wc}<{_LOVE_MIN_CHAPTER_WORDS}"
    if len(t) < _LOVE_MIN_CHAPTER_CHARS:
        return f"chars:{len(t)}<{_LOVE_MIN_CHAPTER_CHARS}"
    mpc = _love_meaningful_paragraph_count(t)
    if mpc < _LOVE_MIN_PARAGRAPHS:
        return f"paras:{mpc}<{_LOVE_MIN_PARAGRAPHS}"
    if _love_is_bullet_heavy(t):
        return "bullet_heavy"
    if len(_CHART_SIGNAL_RE.findall(t)) < 2:
        return "chart_signals<2"
    return None


def _normalize_chapter_body_from_llm(body: str) -> str:
    if not body:
        return ""
    if isinstance(body, list):
        body = "\n\n".join(str(x).strip() for x in body if str(x).strip())
    text = str(body).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if _love_is_bullet_heavy(text):
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        prose_bits = [
            re.sub(r"^[-•*]\s+", "", ln).strip()
            for ln in lines
            if _BULLET_LINE_RE.match(ln)
        ]
        if prose_bits:
            grouped: list[str] = []
            for i in range(0, len(prose_bits), 2):
                grouped.append(" ".join(prose_bits[i : i + 2]))
            text = "\n\n".join(grouped)
    return text


def _parse_love_premium_response(parsed: dict) -> dict:
    chapters = parsed.get("chapters")
    if isinstance(chapters, list):
        for ch in chapters:
            if not isinstance(ch, dict):
                continue
            raw = ch.get(CHAPTER_BODY_KEY) or ch.get("full_read") or ch.get("body") or ""
            normalized = _normalize_chapter_body_from_llm(raw)
            ch[CHAPTER_BODY_KEY] = normalized
            if ch.get("full_read"):
                ch["full_read"] = normalized
    practical = parsed.get("practical")
    if isinstance(practical, str) and practical.strip():
        parsed["practical"] = [practical.strip()]
    elif isinstance(practical, list):
        parsed["practical"] = [str(x).strip() for x in practical if str(x).strip()]
    return parsed


def _build_love_regen_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "English", "hn": "Roman Hindi (Hinglish)"}[lang]
    return f"""You are re-expanding Love Reality Pro PDF chapters that failed depth QA.

Return STRICT JSON with ONE top-level key `chapters` (array).
Each element: {{"key": "<semantic_key>", "chapter_body": "<long prose>"}}.

Valid keys ONLY: {", ".join(LOVE_SEMANTIC_KEYS)}.

DEPTH CONTRACT (non-negotiable for every chapter_body):
- Minimum {_LOVE_MIN_PARAGRAPHS} paragraphs separated by \\n\\n.
- Minimum {_LOVE_MIN_CHAPTER_WORDS} words total (~250–350 words per chapter).
- Continuous consultation prose — weave chart facts (Lagna, Moon, 7th lord, 12th house, Mercury, Venus, dasha) into a human story.
- FORBIDDEN: bullet lists, one-sentence summaries, repeating engine reason strings verbatim, parameter dumps.
- Compare both partners' charts inside the narrative (destiny blueprint vs lived reality).

Write entirely in {script}. Latin letters ONLY — no Devanagari."""


def _build_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "English", "hn": "Roman Hindi (Hinglish)"}[lang]
    self_change_hdr = (
        "Aapko Apne Me Kya Badlav Chahiye"
        if lang == "hn"
        else "What You Need to Change in Yourself"
    )
    partner_change_hdr = (
        "Partner Ko Kya Change Karna Hoga"
        if lang == "hn"
        else "What Your Partner Needs to Change"
    )
    return f"""You are a premium relationship astrologer writing a Love Reality Pro PDF for a couple in a current romantic bond (not a marriage report).

Your JSON fields map directly into a fixed 14-page deterministic PDF renderer. Write each field as flowing narrative prose — scores, tables, and bullet matrices are rendered separately from engine data. Your job is the long human story layer.

LANGUAGE: Write entirely in {script}. Address the couple as "you both" (Hinglish: tum dono / aap dono).
- CRITICAL: Use Latin letters ONLY. NEVER output Devanagari Unicode (no हिन्दी script — PDF cannot render it).

OUTPUT: JSON only with this schema:
{{
  "hidden_truth": "string — one deep pattern neither partner fully sees (3–4 sentences minimum)",
  "chapters": [
    {{"key": "love_connection", "chapter_body": "long prose", "score_0_10": number|null, "grounding": "short chart bridge"}},
    {{"key": "breakup", ...}},
    {{"key": "loyalty", ...}},
    {{"key": "will_return", ...}},
    {{"key": "future_outcome", ...}},
    {{"key": "red_flags", ...}}
  ],
  "special": ["string", "string", "string"],
  "damage": ["string", "string"],
  "practical": ["string", "string"],
  "verdict": "string"
}}

GLOBAL DEPTH CONTRACT (applies to EVERY chapter_body and both practical strings):
- FORBIDDEN: single-sentence outputs, brief bullet points, engine reason-string copy-paste, or parameter lists without narrative.
- REQUIRED: minimum {_LOVE_MIN_PARAGRAPHS} separate, deeply elaborated paragraphs per chapter, separated by \\n\\n.
- REQUIRED: minimum {_LOVE_MIN_CHAPTER_WORDS} words (~250–300+ words) per chapter_body — continuous human story, not a summary.
- Weave chart data seamlessly (e.g. "7th lord Mercury in 12th house Scorpio" or "partner's five planets stacked in the 12th house") into emotional meaning — cite placement first, then lived behaviour.

PDF PAGE-AWARE FIELD CONTRACT:

1) love_connection → Pages 2–3 (Blueprint Story)
   Write exactly {_LOVE_MIN_PARAGRAPHS}+ paragraphs contrasting "Destiny vs Reality":
   - Paragraph 1: Your ideal partner blueprint from 7th lord, Upapada Lagna (UL), Venus, Jupiter (from STRUCTURED_CHART_DATA).
   - Paragraph 2: Partner's actual chart signature — what they bring in real life (Lagna, Moon, 12th-house stack, Mercury placement).
   - Paragraph 3+: Why the gap between your Sagittarius/Gemini (or actual signs) archetype and partner reality creates the love score tension — name specific houses and lords.
   - score_0_10 from LOVE_COMPATIBILITY score; grounding cites UL / 7th / Venus–Jupiter facts.

2) breakup → Page 6 (Root Cause — separation half)
   Brutal, honest {_LOVE_MIN_PARAGRAPHS}+ paragraph analysis of BREAKUP_CHANCES score (e.g. 100/100 breakup risk):
   - Name ego friction, 12th-house secrecy, Mercury clash, Saturn/Mars on 7th axis, dusthana 7th lord — as a story, not a bullet list.
   - Explain what is silently breaking the bond apart and why denial costs more than clarity.

3) loyalty → Pages 6–7 (Root Cause + Loyalty chapter)
   Separate from breakup — {_LOVE_MIN_PARAGRAPHS}+ paragraphs on LOYALTY_CHECK score (e.g. 0/100 loyalty):
   - Trust psychology, secrecy impulse, external pull, dual-nature Moon — do NOT repeat breakup chapter verbatim.
   - If loyalty_score < 52: NEVER say "naturally loyal" or "devoted by nature".

4) will_return + future_outcome → Page 9 (Harmony Formula)
   - will_return: probability language only (never "X will return"); {_LOVE_MIN_PARAGRAPHS} paragraphs on reconnection context.
   - future_outcome: {_LOVE_MIN_PARAGRAPHS}+ paragraphs including explicit blocks:
     • "{self_change_hdr}" — concrete inner shifts the primary reader must own.
     • "{partner_change_hdr}" — concrete shifts the partner must own.
   - Open with elemental clash/healing (Fire/Water/Air/Earth from Moon/sign context).

5) red_flags → Page 8 lead-in narrative
   {_LOVE_MIN_PARAGRAPHS}+ sharp paragraphs naming top operational friction patterns — sets up the deterministic red-flags matrix below; do not duplicate bullet list format.

6) practical → Pages 12–13 (EXACTLY 2 long paragraph strings)
   - Paragraph 1 (Planetary Remedies): deep descriptive prose on countermeasures for the heaviest afflicted planet (Venus, Moon, Saturn-on-7th, Mars-on-7th) — ritual, day-of-week, action tied to chart affliction. Minimum 180 words.
   - Paragraph 2 (Human Action Plan): deep advisory prose translating astro patterns into real-world behavioural safeguards — what to do, say, and avoid in conflict. Minimum 180 words.

7) verdict → Page 14 (Closing Guidance)
   Multi-paragraph close weaving NARRATIVE_BRIDGE naturally; empowering, realistic; prepares reader for 36-month roadmap.

MANDATORY LOCKS (from user message — non-negotiable):
- LOVE_SCORE_LEDGER: cite when explaining love_connection score / cover alignment.
- NARRATIVE_BRIDGE: must inform verdict and any breakup-vs-future tension resolution.
- LOYALTY_NARRATIVE_LOCKS + LOYALTY_CHAPTER_RULE: obey exactly when loyalty_score < 52.

RULES:
- Use ONLY facts from the user message. Do not invent scores.
- score_0_10 MUST match engine score/100 (e.g. score 78 → 7.8, loyalty 35 → 3.5). Never inflate.
- TONE: Brutally honest, emotionally intelligent, psychologically sharp. 90% of readers come after breakup, betrayal, ghosting, or loyalty doubt — do NOT sugarcoat.
- If charts are weak: say clearly (instability, separation patterns, low return probability, loyalty risk). Never force happy endings.
- BANNED: bullet-only chapters, generic filler ("communication is important", "open communication", "mutual understanding", "Yeh zaroori hai ki tum dono", "with effort things improve") unless tied to a named placement.
- STRUCTURE: Each chapter MUST open differently (placement cite, dasha date, observed behaviour, or direct question).
- EXPLANATION: For every claim, cite chart fact first, then emotional meaning. Include `grounding` per chapter: 2–4 factual lines (under 400 chars).
- Will X Return: NEVER write "X will return". Use probability language only.
- special: 3 strengths (only if chart supports — otherwise name fragile strengths honestly).
- damage: 2 sharp risks.
- Focus on CURRENT PARTNER bond — NOT marriage koot/36 gun."""


def _build_user_prompt(bundle: dict, lang: str) -> str:
    return (
        _facts_summary(bundle)
        + f"\n\nlanguage: {normalize_pro_pdf_lang(lang)}\nEmit JSON only."
    )


_LOYALTY_BANNED_RE = re.compile(
    r"naturally\s+loyal|naturally\s+faithful|devoted\s+romantic\s+nature|"
    r"faithful\s+by\s+nature|woh\s+naturally\s+loyal|naturally\s+loyal\s+hain",
    re.I,
)


def _scrub_loyalty_contradictions(parsed: dict, bundle: dict) -> None:
    """Remove 'naturally loyal' etc. when engine says loyalty is low."""
    ly = bundle.get("loyalty_check") or {}
    score = int(ly.get("loyalty_score") or ly.get("score") or 100)
    if score >= 52:
        return
    for ch in parsed.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if str(ch.get("key") or "").strip().lower() != "loyalty":
            continue
        for field in (CHAPTER_BODY_KEY, "full_read", "grounding"):
            text = str(ch.get(field) or "")
            if not text:
                continue
            text = _LOYALTY_BANNED_RE.sub(
                "loyalty is unstable on this chart — surface Venus strength does not prove faithfulness",
                text,
            )
            text = re.sub(
                r"clear communication aur mutual support se aap in challenges ko overcome kar sakte hain[.]?",
                "Chart shows impulse and hidden layers — do not equate chemistry with loyalty.",
                text,
                flags=re.I,
            )
            ch[field] = text
        break


def _normalize_parsed(parsed: dict) -> None:
    """Ensure chapters list has ch1..ch6 aliases for depth regen."""
    chs = parsed.get("chapters")
    if not isinstance(chs, list):
        parsed["chapters"] = []
        return
    by_key = {}
    for c in chs:
        if isinstance(c, dict):
            by_key[str(c.get("key") or "").strip().lower()] = c
    out = []
    for i, ck in enumerate(LOVE_CHAPTER_KEYS, start=1):
        ik = KEY_BY_CH[ck]
        row = dict(by_key.get(ik) or by_key.get(ck) or {})
        row["key"] = ik
        if CHAPTER_BODY_KEY not in row and row.get("full_read"):
            row[CHAPTER_BODY_KEY] = row["full_read"]
        out.append(row)
    parsed["chapters"] = out
    # Milan depth regen expects ch1..ch7 keys on rows — duplicate index keys
    for i, row in enumerate(out, start=1):
        row["ch_index"] = f"ch{i}"

def _love_failing_chapter_keys(parsed: dict) -> list[str]:
    out: list[str] = []
    for ik in LOVE_SEMANTIC_KEYS:
        row = _parsed_chapter_row_for_key(parsed, ik)
        body = str((row or {}).get(CHAPTER_BODY_KEY) or "").strip()
        if _love_chapter_depth_failure_reason(body):
            out.append(ik)
    return out


def _love_apply_depth_regen(
    *,
    client: Any,
    model: str,
    lang: str,
    regen_user: str,
    parsed: dict,
    oa_timeout: float,
) -> None:
    """Re-call OpenAI for any chapter that failed the Love Reality depth gate."""
    max_rounds = int(_PREMIUM_DEPTH_REGEN_MAX_ROUNDS)
    regen_system = _build_love_regen_system_prompt(lang)
    for _ in range(max_rounds):
        failing = _love_failing_chapter_keys(parsed)
        if not failing:
            return
        from vedic.compat.premium_chapters import _depth_regen_dynamic_max_tokens

        mt = max(4000, _depth_regen_dynamic_max_tokens(len(failing)))
        got = _openai_regen_chapters_depth(
            client,
            None,
            model,
            lang,
            regen_system,
            regen_user,
            failing,
            parsed,
            oa_timeout,
            max_tokens=mt,
        )
        if not got:
            return
        for ck, body in got.items():
            row = _parsed_chapter_row_for_key(parsed, ck)
            if row is not None and body:
                normalized = _normalize_chapter_body_from_llm(body)
                row[CHAPTER_BODY_KEY] = normalized
                if row.get("full_read"):
                    row["full_read"] = normalized


def polish_love_reality_premium(bundle: dict, lang: str = "en") -> dict[str, Any]:
    """Returns pro_premium block for PDF renderer. Never raises."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _DEFAULT_MODEL
    if not _polish_enabled():
        return _empty_shell(model, "polish_off")

    cache_key = _love_polish_fingerprint(bundle, lang, model)
    if not _cache_disabled():
        hit = _l1_get(cache_key)
        if hit is not None and _love_polish_cache_depth_ok(hit):
            log.info("[love_reality_premium] L1 cache hit key=%s", cache_key[:16])
            out = dict(hit)
            meta = dict(out.get("_meta") or {})
            meta.setdefault("cache", "L1")
            out["_meta"] = meta
            return out
        db_hit = _l2_get(cache_key)
        if db_hit is not None and _love_polish_cache_depth_ok(db_hit):
            log.info("[love_reality_premium] L2 cache hit key=%s", cache_key[:16])
            _l1_put(cache_key, db_hit)
            out = dict(db_hit)
            meta = dict(out.get("_meta") or {})
            meta.setdefault("cache", "L2")
            out["_meta"] = meta
            return out

    try:
        from openai_helper import _get_client  # type: ignore
    except Exception:
        return _empty_shell(model, "openai_import_fail")

    client = _get_client()
    if client is None:
        return _empty_shell(model, "openai_client_none")

    system = _build_system_prompt(lang)
    user = _build_user_prompt(bundle, lang)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": min(
            int(os.environ.get("LOVE_REALITY_PREMIUM_MAX_TOKENS", "8000")),
            16384,
        ),
    }
    if not model.lower().startswith("gpt-5"):
        kwargs["temperature"] = 0.55
    kwargs["timeout"] = float(os.environ.get("LOVE_REALITY_OPENAI_TIMEOUT", "180"))

    try:
        resp = client.chat.completions.create(**kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            return _empty_shell(model, "empty_openai_body")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return _empty_shell(model, "json_not_object")
        parsed = _parse_love_premium_response(parsed)
    except Exception as exc:
        log.warning("[love_reality_premium] openai fail: %s", exc)
        return _empty_shell(model, "openai_fail")

    _normalize_parsed(parsed)
    _scrub_loyalty_contradictions(parsed, bundle)

    if _depth_regen_enabled():
        try:
            _love_apply_depth_regen(
                client=client,
                model=model,
                lang=lang,
                regen_user=_build_user_prompt(bundle, lang),
                parsed=parsed,
                oa_timeout=kwargs["timeout"],
            )
        except Exception as exc:
            log.warning("[love_reality_premium] depth regen skipped: %s", exc)

    parsed = sanitize_love_reality_pro_premium(parsed, bundle)

    from vedic.love_reality.premium_validate import apply_love_premium_validation

    apply_love_premium_validation(parsed, bundle, lang)

    parsed.setdefault("_meta", {})
    parsed["_meta"].update({
        "model": model,
        "version": _LOVE_VERSION,
        "lang": lang,
        "requested_lang": requested_lang,
    })
    if not _cache_disabled() and _love_polish_cache_depth_ok(parsed):
        try:
            _l1_put(cache_key, parsed)
            _l2_put(cache_key, parsed, model)
        except Exception as exc:
            log.warning("[love_reality_premium] cache write failed: %s", exc)
    return parsed
