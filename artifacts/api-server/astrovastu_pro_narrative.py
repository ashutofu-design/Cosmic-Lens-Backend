"""
AstroVastu PRO — Part B personal narrative (explain-only).

Engine report is LOCKED. OpenAI may only explain facts already computed.
Never invent rooms, directions, scores, or change verdicts.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_NARRATIVE_VERSION = "avp_narr_v1"
_DEFAULT_MODEL = os.environ.get("ASTROVASTU_NARRATIVE_MODEL", "gpt-4o-mini")
_CACHE_CAP = 400
_cache: OrderedDict[str, dict] = OrderedDict()
_cache_lock = threading.Lock()

_LANG_NAME = {
    "en": "English",
    "hinglish": "Hinglish (Roman Hindi)",
    "hi": "Hindi in Roman script (Hinglish style)",
    "bilingual": "English plus Hinglish paragraphs",
}


def _narrative_enabled() -> bool:
    return os.environ.get("ASTROVASTU_PRO_NARRATIVE", "1").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _cache_disabled() -> bool:
    return os.environ.get("ASTROVASTU_NARRATIVE_CACHE_DISABLE", "").strip() in (
        "1", "true", "yes",
    )


def _cache_get(key: str) -> Optional[dict]:
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return dict(_cache[key])
    return None


def _cache_put(key: str, value: dict) -> None:
    with _cache_lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > _CACHE_CAP:
            _cache.popitem(last=False)


def _fingerprint(report: dict, lang: str, model: str) -> str:
    overall = report.get("overall") or {}
    ks = report.get("kundli_summary") or {}
    parts = [
        _NARRATIVE_VERSION,
        model,
        lang,
        str(overall.get("score", "")),
        str(overall.get("grade", "")),
        ks.get("lagna", ""),
        ks.get("mahadasha", ""),
        str(ks.get("sade_sati", "")),
    ]
    for pa in (report.get("priority_actions") or [])[:5]:
        if isinstance(pa, dict):
            parts.append(
                f"{pa.get('room_type')}|{pa.get('direction')}|{pa.get('verdict')}|"
                f"{pa.get('ideal_directions_short')}|{pa.get('action_label_en')}"
            )
    raw = "|".join(parts).encode("utf-8")
    return "avp_narr_" + hashlib.sha1(raw).hexdigest()


def _compact_facts(report: dict) -> str:
    """Minimal engine facts for the narrator — no full PDF dump."""
    overall = report.get("overall") or {}
    counts = overall.get("counts") or {}
    ks = report.get("kundli_summary") or {}
    md = report.get("mahadasha_alert") or {}

    lines = [
        f"overall_score: {overall.get('score')}/100 grade: {overall.get('grade')}",
        f"ideal_rooms: {counts.get('ideal')} acceptable: {counts.get('acceptable')} "
        f"adjust: {counts.get('adjustment_needed')} avoid: {counts.get('avoid')}",
        f"lagna: {ks.get('lagna')} mahadasha: {ks.get('mahadasha')} "
        f"sade_sati_active: {ks.get('sade_sati')}",
    ]
    if md:
        lines.append(
            f"mahadasha_alert: lord={md.get('active_lord')} direction={md.get('lord_direction')} "
            f"summary={md.get('summary_en', '')}"
        )

    lines.append("priority_rooms:")
    for i, pa in enumerate(report.get("priority_actions") or [])[:5], 1):
        if not isinstance(pa, dict):
            continue
        lines.append(
            f"  {i}. {pa.get('room_type')} NOW={pa.get('direction')} "
            f"SHOULD_BE={pa.get('ideal_directions_short')} "
            f"verdict={pa.get('verdict')} action={pa.get('action_label_en')} "
            f"note={pa.get('why', '')[:200]}"
        )

    lines.append("all_rooms:")
    for r in (report.get("rooms") or [])[:12]:
        if not isinstance(r, dict):
            continue
        lines.append(
            f"  - {r.get('room_type')} now={r.get('direction')} "
            f"ideal={r.get('ideal_directions_short')} verdict={r.get('verdict')} "
            f"action={r.get('action_label_en')}"
        )

    fixes = report.get("executive_fixes") or []
    if fixes:
        lines.append("top_fixes:")
        for fx in fixes[:3]:
            if isinstance(fx, dict):
                lines.append(f"  - {fx.get('en', '')}")

    return "\n".join(lines)


def _empty_shell(reason: str, model: str) -> dict:
    return {
        "personal_reading": {"en": "", "hi": ""},
        "do_first": {"en": [], "hi": []},
        "do_avoid": {"en": [], "hi": []},
        "closing": {"en": "", "hi": ""},
        "_meta": {"ok": False, "reason": reason, "model": model, "version": _NARRATIVE_VERSION},
    }


def _normalize_lang(lang: str) -> str:
    low = (lang or "en").strip().lower()
    if low in ("hn", "hinglish", "hi-latin"):
        return "hinglish"
    if low in ("hi", "hindi"):
        return "hinglish"
    if low == "bilingual":
        return "bilingual"
    return "en"


def _build_prompts(facts: str, lang: str, *, light: bool = False) -> tuple[str, str]:
    lang_name = _LANG_NAME.get(lang, "English")
    system = (
        "You are the personal Vastu guide for Cosmic Lens AstroVastu PRO.\n"
        "You receive LOCKED FACTS from a deterministic engine (birth chart D1 + floor plan).\n\n"
        "ABSOLUTE RULES:\n"
        "1. Output ONLY valid JSON matching the schema requested.\n"
        "2. NEVER change scores, grades, verdicts, room names, or directions.\n"
        "3. NEVER invent rooms not listed in the facts.\n"
        "4. NEVER mention AI, GPT, OpenAI, or language model.\n"
        "5. Explain WHY the engine flagged issues using the facts — warm, authoritative, premium tone.\n"
        "6. If relocation is recommended, say so clearly; if remedies are the path, say shift is not possible.\n"
        "7. Do not give medical, legal, or engineering certification advice.\n"
    )
    if light:
        user = (
            f"Write a SHORT personal reading in: {lang_name}.\n\n"
            "LOCKED ENGINE FACTS (source of truth):\n"
            f"{facts}\n\n"
            "Return JSON:\n"
            "{\n"
            '  "personal_reading": {"en": "1 short paragraph (80-120 words max)", "hi": "optional Hinglish"},\n'
            '  "do_first": {"en": ["action1","action2"], "hi": []},\n'
            '  "do_avoid": {"en": ["avoid1"], "hi": []},\n'
            '  "closing": {"en": "one encouraging closing line", "hi": ""}\n'
            "}\n"
            "Keep total output concise — this is a single-room scan PDF.\n"
            "For english-only: leave hi fields empty strings or empty arrays.\n"
            "For hinglish: fill hi with natural Roman Hindi; en can be shorter summary.\n"
            "For bilingual: fill both en and hi.\n"
        )
    else:
        user = (
            f"Write Part B personal reading in: {lang_name}.\n\n"
            "LOCKED ENGINE FACTS (source of truth):\n"
            f"{facts}\n\n"
            "Return JSON:\n"
            "{\n"
            '  "personal_reading": {"en": "2-3 short paragraphs", "hi": "optional Hinglish"},\n'
            '  "do_first": {"en": ["action1","action2","action3"], "hi": []},\n'
            '  "do_avoid": {"en": ["avoid1","avoid2"], "hi": []},\n'
            '  "closing": {"en": "one encouraging closing line", "hi": ""}\n'
            "}\n"
            "For english-only: leave hi fields empty strings or empty arrays.\n"
            "For hinglish: fill hi with natural Roman Hindi; en can be shorter summary.\n"
            "For bilingual: fill both en and hi.\n"
        )
    return system, user


def _depth_ok(block: dict, *, light: bool = False) -> bool:
    pr = block.get("personal_reading") or {}
    en = (pr.get("en") or "").strip()
    hi = (pr.get("hi") or "").strip()
    if light:
        if len(en) < 120 and len(hi) < 80:
            return False
        if len(block.get("do_first", {}).get("en") or []) < 1:
            return False
        return True
    if len(en) < 280 and len(hi) < 200:
        return False
    if len(block.get("do_first", {}).get("en") or []) < 2:
        return False
    return True


def generate_pro_narrative(report: dict, lang: str = "en", *, light: bool = False) -> dict:
    """
    Part B explain-only narrative. Never raises; returns shell on failure.
    `light=True` for single-room scans — shorter copy for 6–10 page PDFs.
    """
    model = _DEFAULT_MODEL
    if not _narrative_enabled():
        return _empty_shell("narrative_off", model)

    if not isinstance(report, dict) or not report.get("rooms"):
        return _empty_shell("no_rooms", model)

    norm_lang = _normalize_lang(lang)
    key = _fingerprint(report, norm_lang, model) + ("|light" if light else "")

    if not _cache_disabled():
        hit = _cache_get(key)
        if hit is not None and _depth_ok(hit, light=light):
            out = dict(hit)
            meta = dict(out.get("_meta") or {})
            meta["cache"] = "L1"
            out["_meta"] = meta
            return out

    facts = _compact_facts(report)
    system, user = _build_prompts(facts, norm_lang, light=light)

    try:
        from openai_helper import _get_client
    except Exception:
        return _empty_shell("openai_import", model)

    client = _get_client()
    if client is None:
        return _empty_shell("openai_unconfigured", model)

    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": int(
            os.environ.get(
                "ASTROVASTU_NARRATIVE_MAX_TOKENS_LIGHT" if light else "ASTROVASTU_NARRATIVE_MAX_TOKENS",
                "700" if light else "1400",
            )
        ),
    }
    if not model.lower().startswith("gpt-5"):
        kwargs["temperature"] = 0.45
    kwargs["timeout"] = float(os.environ.get("ASTROVASTU_NARRATIVE_TIMEOUT", "90"))

    try:
        resp = client.chat.completions.create(**kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            return _empty_shell("empty_response", model)
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return _empty_shell("bad_json", model)
    except Exception as exc:
        log.warning("[avp_narrative] openai failed: %s", exc)
        return _empty_shell("openai_fail", model)

    out = {
        "personal_reading": parsed.get("personal_reading") or {"en": "", "hi": ""},
        "do_first": parsed.get("do_first") or {"en": [], "hi": []},
        "do_avoid": parsed.get("do_avoid") or {"en": [], "hi": []},
        "closing": parsed.get("closing") or {"en": "", "hi": ""},
        "_meta": {
            "ok": _depth_ok(parsed, light=light),
            "reason": "generated",
            "model": model,
            "version": _NARRATIVE_VERSION,
            "lang": norm_lang,
            "light": light,
        },
    }

    if out["_meta"]["ok"] and not _cache_disabled():
        _cache_put(key, out)

    return out
