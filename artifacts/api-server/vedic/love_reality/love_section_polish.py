"""
Love Reality Pro — per-section LLM calls (S02, S03, chapters 05/08/09/10/11).
Shared astrologer voice; no mega-prompt.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any, Callable

from vedic.compat.openai_pdf_telemetry import PdfGenOpenAITelemetry, stub_meta
from vedic.love_reality.pdf_text_safe import polish_content_lang, sanitize_love_reality_pro_premium
from vedic.compat.premium_chapters import CHAPTER_BODY_KEY, normalize_pro_pdf_lang

log = logging.getLogger(__name__)

_ASSEMBLY_VER = "lr_sections_v1"
_CHAPTER_MIN_WORDS = int(os.environ.get("LOVE_REALITY_SECTION_CHAPTER_MIN_WORDS", "180"))
_HARMONY_MIN_WORDS = int(os.environ.get("LOVE_REALITY_SECTION_HARMONY_MIN_WORDS", "180"))

_CHAPTER_KEYS = ("love_connection", "breakup", "loyalty", "red_flags")


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


def _chapter_few_shot(chapter_key: str, lang: str) -> str:
    if chapter_key == "love_connection":
        if lang == "hn":
            return """MAT AISE MAT LIKHO: "Chart signals for this theme are active between both partners..."
AISE LIKHO (p1 = pehli kundli, ideal vs partner reality):
"Aarav, tumhari kundli ke 7th house aur Upapada jo partner dikhate hain — wo tumhe stability aur warmth chahte hain. Par Riya ki chart alag rhythm laati hai — wo andar process karti hai. Tumhe lagta hai tum sunte nahi ho; unhe lagta hai tum push karte ho. Yeh mismatch destiny fail nahi karta — bas samajhna padta hai."""
        return """DO NOT: "Chart signals for this theme are active between both partners..."
WRITE (p1 first kundli — ideal blueprint vs partner reality):
"Aarav, your chart's 7th house and Upapada point to a partner who brings warmth and steadiness. Riya's chart runs on a different rhythm — she processes inside first. You feel unheard when she goes quiet; she feels pushed when you chase answers. That gap is not failed destiny — it needs to be named early."
"""
    if chapter_key == "breakup":
        if lang == "hn":
            return """AISE LIKHO (root cause — p1 lens, simple Hinglish):
"Aarav, jab baat atakti hai to tum turant solve karna chahte ho — gussa jaldi aa jata hai. Riya chup ho jati hai, tum aur push karte ho. Chart yeh friction repeat hone ka pattern dikhata hai — separation tab feel hoti hai jab repair 48 ghante se delay ho."
"""
        return """WRITE (root cause — p1 lens):
"Aarav, when talk stalls you move to fix it fast — anger spikes before you cool down. Riya goes quiet and you push harder. The chart shows this loop repeating — separation feels close when repair waits more than 48 hours after a fight."
"""
    if chapter_key == "loyalty":
        if lang == "hn":
            return """AISE LIKHO:
"Aarav, tum trust ko consistency se measure karte ho — jab Riya silent hoti hai, mind worst-case bharta hai. Chart keh raha hai loyalty score kam hai kyunki pause ko rejection samajh liya jata hai, pyaar kam hone par nahi."
"""
        return """WRITE:
"Aarav, you measure trust through consistency — when Riya is silent your mind fills the gap with worst-case stories. The chart shows a weaker loyalty score because pause gets read as rejection, not because care is gone."
"""
    if chapter_key == "red_flags":
        if lang == "hn":
            return """AISE LIKHO (sharp, no lecture):
"Aarav, do pattern bar-bar dikhte hain — gusse ke peak par ultimatum, aur silence ko ignore samajhna. Chart in dono ko high-risk friction maanta hai jab dasha communication ko stress deti hai."
"""
        return """WRITE (sharp, no lecture):
"Aarav, two patterns keep showing up — ultimatums at peak anger, and reading silence as intentional ignore. The chart flags both as high-risk friction when dasha periods stress communication."
"""
    return ""


def _harmony_few_shot(lang: str) -> str:
    if lang == "hn":
        return """AISE LIKHO (long-term + reconnection — honest, p1 to):
"Aarav, agar alag hue to chart genuine return ko kam probability deta hai — yeh mat padhna ki Riya zaroor wapas aayegi. Jo bond bacha hai usme warmth hai par repair habit ke bina 6-8 mahine ka loop wapas aata hai. Tumhe gusse ke peak par baat band karna seekhna hoga."
"""
    return """WRITE (long-term + reconnection — honest, to p1):
"Aarav, if you were apart the chart gives a low probability of a genuine return — do not read this as 'she will definitely come back.' What remains in the bond has warmth, but without repair habits the same six-to-eight month loop returns. You need to stop trying to settle every fight at peak anger."
"""


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

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("chapter_body") or parsed.get(CHAPTER_BODY_KEY) or "").strip()
        if _word_count(body) < max(80, _CHAPTER_MIN_WORDS - 40):
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
            if k and _word_count(body) >= 80:
                by_key[k] = body
    for k in _CHAPTER_KEYS:
        if k not in by_key:
            return False
    if not str(pro.get("harmony") or "").strip() and "will_return" not in by_key:
        return False
    return True


def assemble_love_reality_pro_premium(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    model: str = "",
) -> dict[str, Any]:
    """Orchestrate all section LLM calls into one pro_premium dict."""
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

    for ck in _CHAPTER_KEYS:
        hit = polish_love_reality_chapter_only(bundle, ck, lang=lang, force_llm=force_llm, tel=tel)
        section_meta[ck] = hit.get("_meta") or {}
        if hit.get("chapter_body"):
            _upsert_chapter(pro, ck, hit["chapter_body"], hit.get("grounding") or "")

    harm = polish_love_reality_harmony_only(bundle, lang=lang, force_llm=force_llm, tel=tel)
    section_meta["harmony"] = harm.get("_meta") or {}
    if harm.get("harmony"):
        pro["harmony"] = harm["harmony"]
        _upsert_chapter(pro, "will_return", harm["harmony"])
        _upsert_chapter(pro, "future_outcome", harm["harmony"])

    _scrub_loyalty_contradictions(pro, bundle)
    pro = sanitize_love_reality_pro_premium(pro, bundle)
    apply_love_premium_validation(pro, bundle, lang)

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
