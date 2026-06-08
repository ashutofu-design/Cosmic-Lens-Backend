"""
Love Reality Pro — per-section LLM calls (S02–S03, blueprint, chapters, harmony, dasha, roadmap).
Shared astrologer voice; no mega-prompt.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from vedic.compat.openai_pdf_telemetry import PdfGenOpenAITelemetry, stub_meta
from vedic.love_reality.pdf_text_safe import polish_content_lang, sanitize_love_reality_pro_premium
from vedic.compat.premium_chapters import CHAPTER_BODY_KEY, normalize_pro_pdf_lang

log = logging.getLogger(__name__)

_ASSEMBLY_VER = "lr_sections_v4"
_CHAPTER_MIN_WORDS = int(os.environ.get("LOVE_REALITY_SECTION_CHAPTER_MIN_WORDS", "120"))
_HARMONY_MIN_WORDS = int(os.environ.get("LOVE_REALITY_SECTION_HARMONY_MIN_WORDS", "180"))

_CHAPTER_KEYS = ("breakup", "loyalty")
_BLUEPRINT_REALITY_KEY = "love_connection"
_RED_FLAGS_KEY = "red_flags"


def _env_flag(name: str, default: str = "0") -> bool:
    return (os.environ.get(name) or default).strip().lower() in ("1", "true", "yes", "on")


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def _love_llm_shared_voice(lang: str) -> str:
    from vedic.love_reality.premium_polish import (
        _verdict_page_banned_block,
        _verdict_page_direct_voice,
        _verdict_page_primary_reader,
    )

    if lang == "hn":
        persona = (
            "Aap ek senior relationship astrologer hain — seedha, simple Roman Hinglish, "
            "jaise samne baith kar samjha rahe ho. Textbook ya coach tone nahi."
        )
    else:
        persona = (
            "You are a senior relationship astrologer — simple everyday English, "
            "like explaining face-to-face. No textbook or coach tone."
        )
    return (
        f"{persona}\n\n"
        f"{_verdict_page_primary_reader(lang)}\n\n"
        f"{_verdict_page_direct_voice(lang)}\n\n"
        f"{_verdict_page_banned_block(lang)}"
    )


def _section_model(env_key: str) -> str:
    from vedic.love_reality.premium_polish import _VERDICT_PAGE_QUALITY_MODEL, _verdict_page_model

    explicit = (os.environ.get(env_key) or "").strip()
    if explicit:
        return explicit
    quality_flag = env_key.replace("_MODEL", "_QUALITY")
    if _env_flag(quality_flag):
        return _VERDICT_PAGE_QUALITY_MODEL
    return _verdict_page_model()


def _openai_kwargs(model: str, max_tokens: int, *, temp_env: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "timeout": float(os.environ.get("LOVE_REALITY_OPENAI_TIMEOUT", "120")),
    }
    if not model.lower().startswith("gpt-5"):
        kwargs["temperature"] = float(os.environ.get(temp_env, "0.78"))
        kwargs["presence_penalty"] = float(os.environ.get("LOVE_REALITY_SECTION_PRESENCE_PENALTY", "0.5"))
        kwargs["frequency_penalty"] = float(os.environ.get("LOVE_REALITY_SECTION_FREQUENCY_PENALTY", "0.3"))
    return kwargs


def _cache_dir() -> str:
    base = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "love_polish")
    )
    os.makedirs(base, exist_ok=True)
    return base


def _few_shot_name_rule(lang: str) -> str:
    if lang == "hn":
        return "CRITICAL: Example mein jo naam hain wo sirf style hain — user message ke ACTUAL p1/p2 naam use karo. Aarav/Riya mat likho."
    return "CRITICAL: Example names are style only — use ACTUAL p1/p2 names from the user message. Never write Aarav or Riya."


def _chapter_few_shot(chapter_key: str, lang: str) -> str:
    name_rule = _few_shot_name_rule(lang)
    if chapter_key == "love_connection":
        if lang == "hn":
            return f"""{name_rule}
MAT AISE MAT LIKHO: "Chart signals for this theme are active..."
AISE LIKHO (p1 ideal vs partner reality — real names):
"[p1_name], tumhari 7th house aur Upapada stability chahte hain. Par [p2_name] ki chart alag rhythm laati hai. Tumhe lagta hai sunai nahi deti; unhe lagta hai tum push karte ho."
"""
        return f"""{name_rule}
DO NOT: "Chart signals for this theme are active between both partners..."
WRITE (p1 — ideal blueprint vs partner reality, use real names):
"[p1_name], your 7th house and Upapada point to warmth and steadiness. [p2_name]'s chart runs on a different rhythm — processes inside first. You feel unheard when they go quiet; they feel pushed when you chase answers."
"""
    if chapter_key == "breakup":
        if lang == "hn":
            return f"""{name_rule}
AISE LIKHO: "[p1_name], jab baat atakti hai tum turant solve karna chahte ho. [p2_name] chup ho jati hai, tum push karte ho. Repair 48 ghante delay ho to separation feel hoti hai."
"""
        return f"""{name_rule}
WRITE: "[p1_name], when talk stalls you move to fix it fast. [p2_name] goes quiet and you push harder. Separation feels close when repair waits more than 48 hours."
"""
    if chapter_key == "loyalty":
        if lang == "hn":
            return f"""{name_rule}
AISE LIKHO: "[p1_name], trust consistency se measure karte ho — jab [p2_name] silent hoti hai mind worst-case bharta hai."
"""
        return f"""{name_rule}
WRITE: "[p1_name], you measure trust through consistency — when [p2_name] is silent your mind fills worst-case stories."
"""
    if chapter_key == "red_flags":
        if lang == "hn":
            return f"""{name_rule}
AISE LIKHO (sharp, 3+ paragraphs): "[p1_name], do pattern bar-bar — peak gusse par ultimatum, silence ko ignore samajhna."
"""
        return f"""{name_rule}
WRITE (sharp, minimum 3 paragraphs, use real names):
"[p1_name], two patterns keep showing — ultimatums at peak anger, and reading silence as intentional ignore. Name both clearly with chart backing."
"""
    return ""


def _harmony_few_shot(lang: str) -> str:
    if lang == "hn":
        return """AISE LIKHO (honest, real p1/p2 names):
"[p1_name], agar alag hue to chart genuine return ko kam probability deta hai — false reunion promise mat do. Repair habit ke bina 6-8 mahine ka loop wapas aata hai."
"""
    return """WRITE (honest, real p1/p2 names):
"[p1_name], if apart the chart gives low genuine-return probability — do not promise reunion. Without repair habits the same six-to-eight month loop returns."
"""


def _red_flags_engine_facts(bundle: dict) -> str:
    rf = bundle.get("hidden_red_flags") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    lines = [
        f"Breakup pressure score: {bu.get('breakup_score') or bu.get('score') or '?'}/100",
        f"Loyalty score: {ly.get('loyalty_score') or ly.get('score') or '?'}/100",
    ]
    for r in (rf.get("reasons") or [])[:6]:
        lines.append(f"Red-flag signal: {r}")
    for r in (bu.get("reasons") or [])[:3]:
        lines.append(f"Friction signal: {r}")
    return "ENGINE RED-FLAG FACTS (name these patterns in prose):\n" + "\n".join(lines)


def _dasha_engine_facts(bundle: dict) -> str:
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    fo = bundle.get("future_outcome") or {}
    lines = ["VIMSHOTTARI DASHA FACTS (explain in plain guide for p1):"]
    for nm, kraw in ((p1.get("name") or "p1", k1), (p2.get("name") or "p2", k2)):
        cd = kraw.get("currentDasha") or {}
        maha, antar = cd.get("maha"), cd.get("antar")
        start, end = cd.get("startDate"), cd.get("endDate")
        if maha:
            bit = f"{nm}: Mahadasha {maha}"
            if antar:
                bit += f", Antardasha {antar}"
            if start and end:
                bit += f" (window {start} → {end})"
            lines.append(bit)
    if fo.get("next_shift"):
        lines.append(f"Couple dasha outlook: {fo.get('next_shift')}")
    sig = bundle.get("couple_signals") or {}
    for n in (sig.get("synastry_notes") or [])[:3]:
        lines.append(f"Synastry note: {n}")
    return "\n".join(lines)


def _roadmap_engine_facts(bundle: dict) -> str:
    fo = bundle.get("future_outcome") or {}
    wr = bundle.get("will_return") or {}
    bu = bundle.get("breakup_chances") or {}
    lc = bundle.get("love_compatibility") or {}
    timeline = fo.get("timeline_flow") or []
    t3 = timeline[1] if len(timeline) > 1 else {}
    lines = [
        "ROADMAP ENGINE SCORES (guide p1 — do NOT invent new numbers):",
        f"Love score: {lc.get('score') or '?'}/100",
        f"Future outlook score: {fo.get('future_score') or fo.get('score') or '?'}/100",
        f"Return probability: {wr.get('return_probability') or wr.get('score') or '?'}/100",
        f"Breakup pressure: {bu.get('breakup_score') or bu.get('score') or '?'}/100",
        f"Next 3 months trend: {t3.get('trend') or 'mixed'} — {t3.get('reason') or fo.get('emotional_summary') or ''}",
        f"Next 12 months outlook: {fo.get('outcome') or 'mixed'} — {fo.get('current_phase') or ''}",
        f"Next 36 months / return band: {wr.get('return_chance') or 'mixed'} — {wr.get('time_window') or fo.get('outcome') or ''}",
    ]
    if fo.get("next_shift"):
        lines.append(f"Phase shift note: {fo.get('next_shift')}")
    return "\n".join(lines)


def _chapter_section_brief(chapter_key: str, lang: str) -> str:
    briefs = {
        "love_connection": (
            "PDF Section 05 — Partner Blueprint vs Reality. "
            "p1 ideal signature (7th, Upapada, Venus) vs p2 actual nature. No generic placeholder."
        ),
        "breakup": (
            "PDF Section 08 — Core Root Cause. Why friction escalates toward separation — chart-backed story."
        ),
        "loyalty": (
            "PDF Section 09 — Loyalty & Trust under pressure. Do NOT say 'naturally loyal' if score is low."
        ),
        "red_flags": (
            "PDF Section 10 — Red Flags lead-in. Top friction patterns — sharp, specific, no bullet list."
        ),
    }
    return briefs.get(chapter_key, "")


def _build_chapter_system_prompt(chapter_key: str, lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "plain conversational English", "hn": "natural Roman Hinglish"}[lang]
    return f"""Write ONLY one Love Reality chapter — key `{chapter_key}`.

Return STRICT JSON:
{{
  "chapter_body": "long prose",
  "grounding": "2-3 chart fact lines in plain words"
}}

Write entirely in {script}.

{_chapter_section_brief(chapter_key, lang)}

RULES:
- Minimum {_CHAPTER_MIN_WORDS}+ words, {_CHAPTER_MIN_WORDS // 3}+ paragraphs (\\n\\n).
- Simple words — no high-end English, no corporate psychology.
- Talk TO p1 (first kundli). Partner as context.
- Cite real chart facts from user message — Moon, houses, graha.
- Do not repeat the same insight twice. No safe counseling wrap ending.

{_love_llm_shared_voice(lang)}

{_chapter_few_shot(chapter_key, lang)}

Use ONLY facts from the user message."""


def _build_harmony_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "plain conversational English", "hn": "natural Roman Hinglish"}[lang]
    return f"""Write ONLY PDF Section 11 — Harmony Formula (long-term + reconnection context combined).

Return STRICT JSON:
{{
  "harmony": "long prose"
}}

Write entirely in {script}.

RULES:
- Minimum {_HARMONY_MIN_WORDS}+ words. Honest about return_probability — no false reunion promises.
- Long-term direction + what shifts the bond — p1 lens, simple English.
- Element clash (Fire/Earth/Air/Water) from Moon signs if in facts.

{_love_llm_shared_voice(lang)}

{_harmony_few_shot(lang)}

Use ONLY facts from the user message."""


def _blueprint_chart_facts(bundle: dict) -> str:
    """Deterministic 7th/UL/Venus lines — anchor LLM for Partner Blueprint vs Reality."""
    from vedic.love_reality.pdf_data_v2 import _partner_blueprint

    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    lc = bundle.get("love_compatibility") or {}
    p1_bp = _partner_blueprint(k1, p1.get("name") or "You")
    p2_bp = _partner_blueprint(k2, p2.get("name") or "Partner")
    love = int(lc.get("score") or 0)
    return (
        "CHART BLUEPRINT FACTS (cite these in prose — ideal vs actual):\n\n"
        f"YOUR IDEAL PARTNER SIGNATURE ({p1.get('name') or 'p1'}):\n"
        + "\n".join(p1_bp["lines"])
        + f"\n\nPARTNER ACTUAL SIGNATURE ({p2.get('name') or 'p2'}):\n"
        + "\n".join(p2_bp["lines"])
        + f"\n\nElement mix: You {p1_bp['element']} · Partner {p2_bp['element']}\n"
        f"Love compatibility score: {love}/100 — explain gap between ideal blueprint and partner reality."
    )


def _build_blueprint_reality_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "plain conversational English", "hn": "natural Roman Hinglish"}[lang]
    return f"""Write ONLY PDF Section — Partner Blueprint vs Reality (love_connection).

Return STRICT JSON:
{{
  "blueprint_reality": "long prose comparing p1 ideal partner signature vs p2 actual nature",
  "chapter_body": "same text as blueprint_reality",
  "grounding": "2-3 chart fact lines"
}}

Write entirely in {script}.

TASK:
- Page title: Partner Blueprint vs Reality
- p1 chart shows IDEAL partner (7th lord, Venus, Jupiter, Upapada)
- p2 chart shows ACTUAL partner nature
- Explain the GAP in simple words — not generic love advice
- Minimum 100 words, 3 paragraphs separated by \\n\\n
- Use REAL names from user message for p1 and p2

{_love_llm_shared_voice(lang)}

{_few_shot_name_rule(lang)}
DO NOT copy engine one-liner summaries verbatim.
DO NOT write only one sentence.

Example shape (use real names, not placeholders):
"[p1_name], your 7th house points to a partner who brings steadiness. [p2_name]'s chart shows a different rhythm — Earth vs your Air. The love score shows how far ideal and reality sit apart."

Use ONLY facts from the user message."""


def polish_love_reality_blueprint_reality_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Page 5 — Partner Blueprint vs Reality."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_BLUEPRINT_REALITY_MODEL")
    system = _build_blueprint_reality_system_prompt(lang)
    user = (
        _build_section_user_prompt(
            bundle,
            lang,
            section_note="Write Partner Blueprint vs Reality for p1 — ideal chart vs partner actual.",
        )
        + "\n\n"
        + _blueprint_chart_facts(bundle)
        + "\n\nEmit JSON with blueprint_reality and chapter_body (same text)."
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_BLUEPRINT_REALITY_MAX_TOKENS", "2400")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(
            parsed.get("blueprint_reality")
            or parsed.get("chapter_body")
            or parsed.get(CHAPTER_BODY_KEY)
            or ""
        ).strip()
        if _word_count(body) < 50:
            return {}
        grounding = str(parsed.get("grounding") or "").strip()
        return {
            "chapter_key": _BLUEPRINT_REALITY_KEY,
            "chapter_body": body,
            "blueprint_reality": body,
            "grounding": grounding,
        }

    return _run_section_llm(
        scope="blueprint_reality",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_BLUEPRINT_REALITY_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_red_flags_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "plain conversational English", "hn": "natural Roman Hinglish"}[lang]
    return f"""Write ONLY PDF Section — Red Flags Matrix (lead-in prose before bullet list).

Return STRICT JSON:
{{
  "red_flags_narrative": "long sharp prose",
  "chapter_body": "same as red_flags_narrative",
  "grounding": "2 chart fact lines"
}}

Write entirely in {script}.

TASK:
- Name the top 2–4 friction patterns for THIS couple — chart-backed
- Talk TO p1 (first kundli). Sharp, specific, no lecture, no bullet list in prose
- Minimum 80 words, 3 short paragraphs (\\n\\n)
- Match breakup/loyalty scores — if high breakup pressure, say so plainly

{_love_llm_shared_voice(lang)}
{_few_shot_name_rule(lang)}

DO NOT write generic "be careful" advice.
Use ONLY engine facts from user message."""


def polish_love_reality_red_flags_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Red Flags body (Page 12)."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_RED_FLAGS_MODEL")
    system = _build_red_flags_system_prompt(lang)
    user = (
        _build_section_user_prompt(bundle, lang, section_note="Write Red Flags lead-in for p1.")
        + "\n\n"
        + _red_flags_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_RED_FLAGS_MAX_TOKENS", "2000")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(
            parsed.get("red_flags_narrative")
            or parsed.get("chapter_body")
            or parsed.get(CHAPTER_BODY_KEY)
            or ""
        ).strip()
        if _word_count(body) < 45:
            return {}
        return {
            "chapter_key": _RED_FLAGS_KEY,
            "chapter_body": body,
            "red_flags_narrative": body,
            "grounding": str(parsed.get("grounding") or "").strip(),
        }

    return _run_section_llm(
        scope="red_flags",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_RED_FLAGS_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_dasha_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "plain conversational English", "hn": "natural Roman Hinglish"}[lang]
    return f"""Write ONLY PDF Section — Vimshottari Dasha Synchronization (guide for p1).

Return STRICT JSON:
{{
  "dasha_narrative": "long prose explaining both partners' dasha cycles and what p1 should watch"
}}

Write entirely in {script}.

TASK:
- Explain p1 and p2 current MD/AD in simple words — not textbook Sanskrit
- Say how cycles align OR clash for this couple right now
- Guide p1: what to do / avoid in this antardasha window (repair, patience, no ultimatums)
- Minimum 90 words, 3 paragraphs (\\n\\n)
- Use exact dasha names and date windows from facts only

{_love_llm_shared_voice(lang)}
{_few_shot_name_rule(lang)}

Example shape:
"[p1_name], you're running Jupiter MD with Rahu AD until [date] — this stretches patience. [p2_name]'s Saturn AD slows emotional replies. When both cycles stress communication, name friction within 24 hours."

Use ONLY facts from user message."""


def polish_love_reality_dasha_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Dasha page — prose guide + engine bullets at render."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_DASHA_MODEL")
    system = _build_dasha_system_prompt(lang)
    user = (
        _build_section_user_prompt(bundle, lang, section_note="Write Dasha sync guide for p1.")
        + "\n\n"
        + _dasha_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_DASHA_MAX_TOKENS", "2200")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("dasha_narrative") or "").strip()
        if _word_count(body) < 60:
            return {}
        return {"dasha_narrative": body}

    return _run_section_llm(
        scope="dasha",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_DASHA_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_roadmap_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {"en": "plain conversational English", "hn": "natural Roman Hinglish"}[lang]
    return f"""Write ONLY PDF Section — 1–3 Year Chronological Roadmap (p1 action guide).

Return STRICT JSON:
{{
  "roadmap_narrative": "long prose guiding p1 through next 3, 12, and 36 months based on engine scores"
}}

Write entirely in {script}.

TASK:
- Use engine trends for Next 3 months, Next 12 months, Next 36 months from facts
- Guide p1 what to expect and what TO DO each phase — repair habits, patience, clarity
- If trend is down/strained/unlikely — say honestly, no false hope
- If return probability is low — do not promise reunion
- Minimum 100 words, 3 paragraphs mapped to 3/12/36 month windows (\\n\\n)
- Simple English — astrologer advising face-to-face

{_love_llm_shared_voice(lang)}
{_few_shot_name_rule(lang)}

DO NOT invent scores or dates not in facts.
Use ONLY facts from user message."""


def polish_love_reality_roadmap_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Roadmap page — score-based guide for p1."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_ROADMAP_MODEL")
    system = _build_roadmap_system_prompt(lang)
    user = (
        _build_section_user_prompt(bundle, lang, section_note="Write 3/12/36 month roadmap guide for p1.")
        + "\n\n"
        + _roadmap_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_ROADMAP_MAX_TOKENS", "2400")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("roadmap_narrative") or "").strip()
        if _word_count(body) < 70:
            return {}
        return {"roadmap_narrative": body}

    return _run_section_llm(
        scope="roadmap",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_ROADMAP_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_section_user_prompt(bundle: dict, lang: str, *, section_note: str) -> str:
    from vedic.love_reality.premium_polish import _verdict_page_facts_summary

    p1 = bundle.get("p1") or {}
    p1_name = str(p1.get("name") or "Partner A").strip()
    lang_voice = polish_content_lang(normalize_pro_pdf_lang(lang))
    voice = (
        f"Aap = {p1_name} (p1/pehli kundli)."
        if lang_voice == "hn"
        else f"You = {p1_name} (p1/first kundli)."
    )
    return (
        f"{section_note}\n\n"
        + _verdict_page_facts_summary(bundle)
        + f"\n\nlanguage: {lang}\n"
        + f"narration_style: {voice}\n"
        + "Emit JSON only."
    )


def _fingerprint(blob: str) -> str:
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


def _section_cache_key(bundle: dict, lang: str, model: str, scope: str, prompt_fp: str) -> str:
    from vedic.love_reality.premium_polish import _love_polish_fingerprint

    raw = "|".join([_love_polish_fingerprint(bundle, lang, model), scope, prompt_fp, _ASSEMBLY_VER])
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _run_section_llm(
    *,
    scope: str,
    bundle: dict,
    lang: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temp_env: str,
    force_llm: bool,
    parse_fn: Callable[[dict], dict[str, Any]],
    tel: PdfGenOpenAITelemetry | None,
) -> dict[str, Any]:
    empty: dict[str, Any] = {"_meta": {"scope": scope, "openai_skipped": True}}
    from vedic.love_reality.premium_polish import _polish_enabled

    if not _polish_enabled():
        empty["_meta"]["reason"] = "polish_off"
        return empty

    prompt_fp = _fingerprint(system)
    cache_key = _section_cache_key(bundle, lang, model, scope, prompt_fp)
    cache_path = os.path.join(_cache_dir(), f"{scope}_{cache_key}.json")
    force = force_llm or _env_flag(f"LOVE_REALITY_{scope.upper()}_FORCE")

    if not force and os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                hit = json.load(fh)
            if isinstance(hit, dict) and parse_fn(hit):
                hit.setdefault("_meta", {})["cache"] = f"{scope}_file"
                hit["_meta"]["openai_skipped"] = True
                return hit
        except Exception as exc:
            log.warning("[%s] cache read failed: %s", scope, exc)

    try:
        from openai_helper import _get_client  # type: ignore
    except Exception:
        empty["_meta"]["reason"] = "openai_import_fail"
        return empty

    client = _get_client()
    if client is None:
        empty["_meta"]["reason"] = "openai_client_none"
        return empty

    kwargs = _openai_kwargs(model, max_tokens, temp_env=temp_env)
    kwargs["messages"] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        resp = client.chat.completions.create(**kwargs)
        if tel is not None:
            tel.record(resp, scope)
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            empty["_meta"]["reason"] = "empty_openai_body"
            return empty
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            empty["_meta"]["reason"] = "json_not_object"
            return empty
        out = parse_fn(parsed)
        if not out:
            retry_user = user + "\n\nRETRY: prior response too short. Write LONGER — minimum 3 paragraphs."
            kwargs["messages"] = [
                {"role": "system", "content": system},
                {"role": "user", "content": retry_user},
            ]
            try:
                resp2 = client.chat.completions.create(**kwargs)
                if tel is not None:
                    tel.record(resp2, f"{scope}_retry")
                raw2 = (resp2.choices[0].message.content or "").strip()
                if raw2:
                    parsed2 = json.loads(raw2)
                    if isinstance(parsed2, dict):
                        out = parse_fn(parsed2)
            except Exception as exc2:
                log.warning("[%s] retry fail: %s", scope, exc2)
        if not out:
            empty["_meta"]["reason"] = "parse_empty"
            return empty
    except Exception as exc:
        log.warning("[%s] openai fail: %s", scope, exc)
        empty["_meta"]["reason"] = "openai_fail"
        return empty

    out.setdefault("_meta", {})
    out["_meta"].update({
        "scope": scope,
        "model": model,
        "lang": lang,
        "prompt_fingerprint": prompt_fp,
        "cache_key": cache_key[:12],
        "openai_skipped": False,
    })
    try:
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        log.warning("[%s] cache write failed: %s", scope, exc)
    return out


def polish_love_reality_chapter_only(
    bundle: dict,
    chapter_key: str,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    if chapter_key not in _CHAPTER_KEYS:
        return {"_meta": {"scope": f"chapter_{chapter_key}", "reason": "invalid_key"}}
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    scope = f"chapter_{chapter_key}"
    model = _section_model(f"LOVE_REALITY_CHAPTER_{chapter_key.upper()}_MODEL")
    system = _build_chapter_system_prompt(chapter_key, lang)
    user = _build_section_user_prompt(
        bundle,
        lang,
        section_note=f"Write chapter `{chapter_key}` for {bundle.get('p1', {}).get('name', 'p1')}.",
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_CHAPTER_MAX_TOKENS", "2800")), 4096)

    min_words = 70 if chapter_key == "red_flags" else max(90, _CHAPTER_MIN_WORDS - 30)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("chapter_body") or parsed.get(CHAPTER_BODY_KEY) or "").strip()
        if _word_count(body) < min_words:
            return {}
        grounding = str(parsed.get("grounding") or "").strip()
        return {"chapter_key": chapter_key, "chapter_body": body, "grounding": grounding}

    return _run_section_llm(
        scope=scope,
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_CHAPTER_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def polish_love_reality_harmony_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_HARMONY_MODEL")
    system = _build_harmony_system_prompt(lang)
    user = _build_section_user_prompt(
        bundle,
        lang,
        section_note="Write Section 11 Harmony Formula — long-term + reconnection for p1.",
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_HARMONY_MAX_TOKENS", "2400")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("harmony") or "").strip()
        if _word_count(body) < max(80, _HARMONY_MIN_WORDS - 40):
            return {}
        return {"harmony": body}

    return _run_section_llm(
        scope="harmony",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_HARMONY_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _upsert_chapter(pro: dict, key: str, body: str, grounding: str = "") -> None:
    chapters = pro.setdefault("chapters", [])
    if not isinstance(chapters, list):
        chapters = []
        pro["chapters"] = chapters
    row = {"key": key, CHAPTER_BODY_KEY: body, "chapter_body": body}
    if grounding:
        row["grounding"] = grounding
    for i, ch in enumerate(chapters):
        if isinstance(ch, dict) and str(ch.get("key") or "").lower() == key:
            chapters[i] = {**ch, **row}
            return
    chapters.append(row)


def _assembly_depth_ok(pro: dict) -> bool:
    if not str(pro.get("verdict") or "").strip():
        return False
    da = pro.get("deep_analysis")
    if not isinstance(da, list) or len(da) < 4:
        return False
    by_key = {}
    for ch in pro.get("chapters") or []:
        if isinstance(ch, dict):
            k = str(ch.get("key") or "").lower()
            body = str(ch.get(CHAPTER_BODY_KEY) or ch.get("chapter_body") or "")
            if k and _word_count(body) >= 70:
                by_key[k] = body
    if not str(pro.get("blueprint_reality") or "").strip() and _BLUEPRINT_REALITY_KEY not in by_key:
        return False
    for k in _CHAPTER_KEYS:
        if k not in by_key:
            return False
    rf = str(pro.get("red_flags_narrative") or "").strip() or by_key.get(_RED_FLAGS_KEY, "")
    if _word_count(rf) < 45:
        return False
    if not str(pro.get("harmony") or "").strip() and "will_return" not in by_key:
        return False
    if _word_count(str(pro.get("dasha_narrative") or "")) < 60:
        return False
    if _word_count(str(pro.get("roadmap_narrative") or "")) < 70:
        return False
    return True


def _section_body_from_hit(hit: dict, *keys: str) -> str:
    for k in keys:
        v = str(hit.get(k) or "").strip()
        if v:
            return v
    return ""


def _invoke_section_fn(
    fn: Callable[..., dict[str, Any]],
    bundle: dict,
    lang: str,
    force_llm: bool,
    *,
    chapter_key: str | None = None,
) -> dict[str, Any]:
    if chapter_key:
        return polish_love_reality_chapter_only(
            bundle, chapter_key, lang=lang, force_llm=force_llm, tel=None
        )
    return fn(bundle, lang=lang, force_llm=force_llm, tel=None)


def _run_section_job(
    label: str,
    fn: Callable[..., dict[str, Any]],
    bundle: dict,
    lang: str,
    force_llm: bool,
    *,
    body_keys: tuple[str, ...],
    pro_key: str | None = None,
    ch_key: str | None = None,
    chapter_key: str | None = None,
) -> tuple[str, dict[str, Any], str, str | None, str | None]:
    """Run one section LLM call with retry; never raises."""
    try:
        hit = _invoke_section_fn(
            fn, bundle, lang, force_llm, chapter_key=chapter_key
        )
        body = _section_body_from_hit(hit, *body_keys)
        if not body:
            log.warning(
                "[assembly] %s miss (%s) — retry forced",
                label,
                (hit.get("_meta") or {}).get("reason"),
            )
            hit = _invoke_section_fn(
                fn, bundle, lang, True, chapter_key=chapter_key
            )
            body = _section_body_from_hit(hit, *body_keys)
        if not body:
            log.warning("[assembly] %s still empty after retry", label)
        return label, hit, body, pro_key, ch_key
    except Exception as exc:
        log.exception("[assembly] %s failed: %s", label, exc)
        return label, {"_meta": {"reason": "section_exception", "error": str(exc)}}, "", pro_key, ch_key


def assemble_love_reality_pro_premium(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    model: str = "",
) -> dict[str, Any]:
    """Orchestrate all section LLM calls into one pro_premium dict. Never raises."""
    from vedic.love_reality.premium_polish import (
        _DEFAULT_MODEL,
        _scrub_loyalty_contradictions,
        polish_love_reality_deep_analysis_only,
        polish_love_reality_verdict_page_only,
    )
    from vedic.love_reality.premium_validate import apply_love_premium_validation

    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = model or _DEFAULT_MODEL
    tel = PdfGenOpenAITelemetry(model)
    pro: dict[str, Any] = {
        "hidden_truth": "",
        "chapters": [],
        "special": [],
        "damage": [],
        "practical": [],
        "verdict": "",
        "_meta": {"assembly": _ASSEMBLY_VER, "version": _ASSEMBLY_VER},
    }
    section_meta: dict[str, Any] = {}

    try:
        s02 = polish_love_reality_verdict_page_only(bundle, lang=lang, force_llm=force_llm)
        if s02.get("verdict"):
            pro["verdict"] = s02["verdict"]
        if s02.get("practical"):
            pro["practical"] = s02["practical"]
        section_meta["verdict_page"] = s02.get("_meta") or {}

        s03 = polish_love_reality_deep_analysis_only(bundle, lang=lang, force_llm=force_llm)
        if s03.get("deep_analysis"):
            pro["deep_analysis"] = s03["deep_analysis"]
        section_meta["deep_analysis"] = s03.get("_meta") or {}

        parallel_jobs: list[tuple] = [
            (
                "blueprint_reality",
                polish_love_reality_blueprint_reality_only,
                ("chapter_body", "blueprint_reality"),
                "blueprint_reality",
                _BLUEPRINT_REALITY_KEY,
                None,
            ),
            (
                "breakup",
                polish_love_reality_chapter_only,
                ("chapter_body",),
                None,
                "breakup",
                "breakup",
            ),
            (
                "loyalty",
                polish_love_reality_chapter_only,
                ("chapter_body",),
                None,
                "loyalty",
                "loyalty",
            ),
            (
                "harmony",
                polish_love_reality_harmony_only,
                ("harmony",),
                "harmony",
                None,
                None,
            ),
            (
                "red_flags",
                polish_love_reality_red_flags_only,
                ("red_flags_narrative", "chapter_body"),
                "red_flags_narrative",
                _RED_FLAGS_KEY,
                None,
            ),
            (
                "dasha",
                polish_love_reality_dasha_only,
                ("dasha_narrative",),
                "dasha_narrative",
                None,
                None,
            ),
            (
                "roadmap",
                polish_love_reality_roadmap_only,
                ("roadmap_narrative",),
                "roadmap_narrative",
                None,
                None,
            ),
        ]

        workers = min(7, int(os.environ.get("LOVE_REALITY_SECTION_WORKERS", "5")))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    _run_section_job,
                    label,
                    fn,
                    bundle,
                    lang,
                    force_llm,
                    body_keys=body_keys,
                    pro_key=pro_key,
                    ch_key=ch_key,
                    chapter_key=chapter_key,
                )
                for label, fn, body_keys, pro_key, ch_key, chapter_key in parallel_jobs
            ]
            for fut in as_completed(futures):
                label, hit, body, pro_key, ch_key = fut.result()
                section_meta[label] = hit.get("_meta") or {}
                if not body:
                    continue
                if pro_key:
                    pro[pro_key] = body
                if ch_key:
                    _upsert_chapter(pro, ch_key, body, hit.get("grounding") or "")
                if label == "harmony":
                    _upsert_chapter(pro, "will_return", body)
                    _upsert_chapter(pro, "future_outcome", body)
                elif label in _CHAPTER_KEYS:
                    _upsert_chapter(pro, label, body, hit.get("grounding") or "")

        _scrub_loyalty_contradictions(pro, bundle)
        pro = sanitize_love_reality_pro_premium(pro, bundle)
        apply_love_premium_validation(pro, bundle, lang)
    except Exception as exc:
        log.exception("[assembly] fatal: %s", exc)
        pro.setdefault("_meta", {})["assembly_error"] = str(exc)

    pro.setdefault("_meta", {})
    pro["_meta"].update({
        "model": model,
        "lang": lang,
        "requested_lang": requested_lang,
        "assembly": _ASSEMBLY_VER,
        "sections": section_meta,
    })
    pg = tel.build_meta(
        fallback_used=not _assembly_depth_ok(pro),
        final_status="OK" if _assembly_depth_ok(pro) else "partial",
        validator_attempts=0,
        cache_hit=False,
        openai_skipped=False,
    )
    from vedic.love_reality.premium_polish import _attach_polish_telemetry

    _attach_polish_telemetry(pro["_meta"], pg)
    return pro
