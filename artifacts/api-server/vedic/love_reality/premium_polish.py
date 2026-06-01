"""
Love Reality Pro PDF — GPT polish + chapter depth regen (Milan-style pipeline).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
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
    build_premium_regen_chapter_system_prompt,
    _chapter_body_depth_failure_reason,
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
KEY_BY_CH = {
    "ch1": "love_connection",
    "ch2": "breakup",
    "ch3": "loyalty",
    "ch4": "will_return",
    "ch5": "future_outcome",
    "ch6": "red_flags",
}


def _env_flag(name: str, default: str = "0") -> bool:
    return (os.environ.get(name) or default).strip().lower() in ("1", "true", "yes", "on")


def _polish_enabled() -> bool:
    if _env_flag("LOVE_REALITY_PREMIUM_POLISH"):
        return True
    return _env_flag("COMPAT_PREMIUM_POLISH", "0")


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
    if len(chapters) < 4:
        return False
    ok_bodies = 0
    for ch in chapters:
        if len((ch.get(CHAPTER_BODY_KEY) or ch.get("chapter_body") or "").strip()) >= 120:
            ok_bodies += 1
    return ok_bodies >= 4


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
        out = [f"=== {label} ==="]
        for k in ("score", "breakup_score", "loyalty_score", "return_probability", "future_score"):
            if k in d and d[k] is not None:
                out.append(f"{k}: {d[k]}")
        for k in ("risk_level", "loyalty_level", "return_chance", "outcome", "current_phase"):
            if d.get(k):
                out.append(f"{k}: {d[k]}")
        if d.get("emotional_summary"):
            out.append(f"emotional_summary: {d['emotional_summary']}")
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


def _build_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "English", "hn": "Roman Hindi (Hinglish)"}[lang]
    return f"""You are a premium relationship astrologer writing a Love Reality Pro PDF for a couple in a current romantic bond (not a marriage report).

LANGUAGE: Write entirely in {script}. Address the couple as "you both" (Hinglish: tum dono / aap dono).
- CRITICAL: Use Latin letters ONLY. NEVER output Devanagari Unicode (no हिन्दी script — PDF cannot render it).

OUTPUT: JSON only with this schema:
{{
  "hidden_truth": "string — one deep pattern neither partner fully sees",
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

RULES:
- Use ONLY facts from the user message. Do not invent scores.
- score_0_10 MUST match engine score/100 (e.g. score 78 → 7.8, loyalty 35 → 3.5). Never inflate.
- TONE: Brutally honest, emotionally intelligent, psychologically sharp. 90% of readers come after breakup, betrayal, ghosting, or loyalty doubt — do NOT sugarcoat.
- If charts are weak: say clearly (instability, separation patterns, low return probability, loyalty risk). Never force happy endings.
- BANNED generic filler: "communication is important", "open communication", "mutual understanding", "Yeh zaroori hai ki tum dono", "with effort things improve" — unless tied to a named placement from STRUCTURED_CHART_DATA.
- STRUCTURE: Each chapter MUST open differently (placement cite, dasha date, one observed behavior, or a direct question). Never reuse the same opening sentence pattern across chapters.
- EXPLANATION: For every claim, cite chart fact first (planet, house, degree or dasha), then emotional meaning. Include `grounding` per chapter: 2–4 factual lines bridging score to placements (under 400 chars).
- CONSISTENCY: If breakup_score is high (55+) AND future_score is also high (55+), explain timing split (near-term friction vs later repair) — do not contradict without bridge.
- Will X Return: NEVER write "X will return". Use probability language only (unlikely / possible / attachment remains but reunion weak).
- Loyalty chapter: If loyalty_score < 52 OR narrative_locks present — NEVER say "naturally loyal", "devoted romantic nature", or "faithful by nature" for any partner. Venus-Mars conjunction = passion risk, NOT loyalty proof. Moon in 8th / debilitated D9 Moon = secrecy and wavering commitment — lead with that.
- BANNED loyalty phrases when score low: "naturally loyal", "woh naturally loyal hain", "devoted romantic nature", "clear communication se overcome".
- Each chapter_body: continuous consultation prose, \\n\\n between paragraphs. Target 900–1800 characters (Latin) — vary length by chapter; do NOT pad to identical word count.
- Focus on CURRENT PARTNER bond — NOT marriage koot/36 gun.
- special: 3 strengths (only if chart supports — otherwise name fragile strengths honestly).
- damage: 2 sharp risks — name the quiet pattern that could damage the bond.
- practical: 2 daily-life paragraphs — observational, not therapy homework.
- No bullet-only chapters. Human, specific, premium voice."""


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


def _milan_facts_from_bundle(bundle: dict) -> dict:
    """Minimal facts dict for shared depth-regen helpers."""
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    lc = bundle.get("love_compatibility") or {}
    return {
        "p1": p1,
        "p2": p2,
        "total": lc.get("score", 0),
        "max": 100,
    }


def _love_failing_chapter_keys(parsed: dict, milan_facts: dict, lang: str) -> list[str]:
    out: list[str] = []
    for ck in LOVE_CHAPTER_KEYS:
        row = _parsed_chapter_row_for_key(parsed, ck)
        body = str((row or {}).get(CHAPTER_BODY_KEY) or "").strip()
        if _chapter_body_depth_failure_reason(body, milan_facts, lang):
            out.append(ck)
    return out


def _love_apply_depth_regen(
    *,
    client: Any,
    model: str,
    lang: str,
    milan_facts: dict,
    regen_system: str,
    regen_user: str,
    parsed: dict,
    oa_timeout: float,
) -> None:
    """Re-call OpenAI for any chapter that failed the depth gate (Milan-style)."""
    max_rounds = int(_PREMIUM_DEPTH_REGEN_MAX_ROUNDS)
    for _ in range(max_rounds):
        failing = _love_failing_chapter_keys(parsed, milan_facts, lang)
        if not failing:
            return
        from vedic.compat.premium_chapters import _depth_regen_dynamic_max_tokens

        mt = _depth_regen_dynamic_max_tokens(len(failing))
        got = _openai_regen_chapters_depth(
            client, None, model, lang, regen_system, regen_user, failing, parsed, oa_timeout, max_tokens=mt
        )
        if not got:
            return
        for ck, body in got.items():
            row = _parsed_chapter_row_for_key(parsed, ck)
            if row is not None and body:
                row[CHAPTER_BODY_KEY] = body


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
            int(os.environ.get("LOVE_REALITY_PREMIUM_MAX_TOKENS", "12000")),
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
    except Exception as exc:
        log.warning("[love_reality_premium] openai fail: %s", exc)
        return _empty_shell(model, "openai_fail")

    _normalize_parsed(parsed)
    _scrub_loyalty_contradictions(parsed, bundle)

    if _depth_regen_enabled():
        milan_facts = _milan_facts_from_bundle(bundle)
        regen_parsed = {"chapters": []}
        for i, c in enumerate(parsed.get("chapters") or [], start=1):
            rc = dict(c)
            rc["key"] = f"ch{i}"
            regen_parsed["chapters"].append(rc)
        try:
            _love_apply_depth_regen(
                client=client,
                model=model,
                lang=lang,
                milan_facts=milan_facts,
                regen_system=build_premium_regen_chapter_system_prompt(lang),
                regen_user=_build_user_prompt(bundle, lang),
                parsed=regen_parsed,
                oa_timeout=kwargs["timeout"],
            )
            for i, c in enumerate(regen_parsed.get("chapters") or [], start=1):
                if i <= len(parsed.get("chapters") or []):
                    body = c.get(CHAPTER_BODY_KEY) or ""
                    if body:
                        parsed["chapters"][i - 1][CHAPTER_BODY_KEY] = body
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
