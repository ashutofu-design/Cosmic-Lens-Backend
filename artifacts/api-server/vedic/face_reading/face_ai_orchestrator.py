"""
Two-pass Face Reading AI orchestration.

PASS A (mini): one JSON call → 12 compact insights from FaceSignalBundle
PASS B (4o):   one JSON call → premium prose for high-impact blocks only

Fallback: Pass A bullets → template; failed Pass B → legacy block template.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Set

from .face_report_blocks import (
    BLOCK_WORD_TARGETS,
    PASS_A_KEYS,
    PASS_B_BLOCKS,
    PASS_A_BLOCK_HINTS,
    narrative_from_pass_a_insight,
    legacy_template_narrative,
)
from .report_voice import (
    FACE_VOICE_ADDENDUM,
    passes_face_voice_combined,
    post_process_prose,
)
from .consistency_layer import clean_internal_labels

from .report_version import INSIGHTS_VERSION, NARRATION_VERSION

FACE_CACHE_VERSION = NARRATION_VERSION

PASS_A_SCHEMA_KEYS = PASS_A_KEYS + [
    "faceread.hook_identity",
    "faceread.hook_shock",
    "faceread.tldr",
]


def ai_enabled() -> bool:
    from .ai_narrator import ai_enabled as _ae
    return _ae()


def _get_client():
    from .ai_narrator import _get_client as _gc
    return _gc()


def pass_a_model() -> str:
    return (
        os.environ.get("FACE_READING_PASS_A_MODEL")
        or os.environ.get("OPENAI_NARRATOR_MODEL")
        or "gpt-4.1-mini"
    ).strip()


def pass_b_model() -> str:
    return (os.environ.get("FACE_READING_AI_MODEL") or "gpt-4o").strip()


def use_two_pass() -> bool:
    return (os.environ.get("FACE_AI_TWO_PASS") or "1").strip().lower() not in (
        "0", "false", "off",
    )


def _lang_norm(lang: str) -> str:
    from numerology.core.report_voice import LANG_INSTRUCT

    _map = {
        "en": "english", "english": "english",
        "hi": "hindi", "hindi": "hindi",
        "hinglish": "hinglish", "hg": "hinglish", "hn": "hinglish",
    }
    l = _map.get((lang or "").strip().lower(), "hinglish")
    return l if l in LANG_INSTRUCT else "hinglish"


def run_pass_a(
    bundle: Any,
    lang: str = "hinglish",
    *,
    analysis_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Single mini-model call: FaceSignalBundle → insights JSON for all blocks.
    Returns {block_key: {one_liner, bullets, observation, implication, anchor_phrase}}.
    """
    client = _get_client()
    if not client:
        return {}

    lang = _lang_norm(lang)
    from numerology.core.report_voice import LANG_INSTRUCT
    lang_rule = LANG_INSTRUCT[lang]

    sys_prompt = (
        "You compress face-reading signals into dense behavioral insights.\n"
        f"LANGUAGE: {lang_rule}\n"
        "INPUT: FaceSignalBundle JSON only — do not invent facts.\n"
        "OUTPUT: One JSON object. Keys EXACTLY:\n"
        + json.dumps(PASS_A_SCHEMA_KEYS)
        + "\nEach value = object with keys: one_liner (string), bullets (array of 2-4 strings), "
        "observation (string), implication (string), anchor_phrase (string from bundle).\n"
        "STYLE: hedged (tends to, pattern suggests). No astrology, medical, hiring, destiny.\n"
        "DENSITY: high — no filler. Each block must differ — no repeated adjectives.\n"
        + FACE_VOICE_ADDENDUM[:1200]
    )

    user_prompt = (
        "Produce insights for all blocks from this bundle:\n"
        + bundle.to_prompt_json()
    )

    try:
        resp = client.chat.completions.create(
            model=pass_a_model(),
            temperature=0.35,
            max_tokens=2200,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        _record_spend(
            resp,
            pass_a_model(),
            phase="pass_a",
            analysis_id=analysis_id,
            user_id=user_id,
            lang=lang,
        )
        raw = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return {}
        out: Dict[str, Any] = {}
        for k in PASS_A_SCHEMA_KEYS:
            v = parsed.get(k)
            if isinstance(v, dict):
                out[k] = v
            elif isinstance(v, str) and v.strip():
                out[k] = {"one_liner": v.strip(), "bullets": []}
        print(f"[face_ai] Pass A OK model={pass_a_model()} keys={len(out)}")
        return out
    except Exception as exc:
        print(f"[face_ai] Pass A failed: {exc}")
        return {}


def run_pass_b(
    bundle: Any,
    pass_a: Dict[str, Any],
    lang: str,
    block_keys: List[str],
    *,
    hook: Optional[Dict[str, Any]] = None,
    analysis_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Dict[str, str]:
    """Single gpt-4o call for premium prose on PASS_B_BLOCKS only."""
    client = _get_client()
    if not client:
        return {}

    keys = [k for k in block_keys if k in PASS_B_BLOCKS]
    if not keys:
        return {}

    lang = _lang_norm(lang)
    from numerology.core.report_voice import LANG_INSTRUCT, VOICE_GUIDE
    lang_rule = LANG_INSTRUCT[lang]

    blocks_spec = []
    for k in keys:
        hint = PASS_A_BLOCK_HINTS.get(k, "insight")
        if k.startswith("faceread."):
            hint = "short cover line"
        insight = pass_a.get(k) or {}
        blocks_spec.append(
            f"[{k}] goal: {hint}\n"
            f"PASS_A_SEED: {json.dumps(insight, ensure_ascii=False)}\n"
            f"~{BLOCK_WORD_TARGETS.get(k, 120)} words"
        )

    sys_prompt = (
        VOICE_GUIDE
        + FACE_VOICE_ADDENDUM
        + f"\nLANGUAGE: {lang_rule}\n"
        + "PASS B: Expand PASS_A seeds into premium prose. Use FaceSignalBundle for facts only.\n"
        + "Return JSON {key: prose}. Keys EXACTLY: "
        + json.dumps(keys)
        + "\nNo repetition across keys. No new facts beyond bundle.\n"
    )

    user_prompt = (
        "FACE_SIGNAL_BUNDLE:\n"
        + bundle.to_prompt_json()
        + "\n\nEXPAND THESE BLOCKS:\n"
        + "\n\n".join(blocks_spec)
    )

    max_tok = min(4000, sum(BLOCK_WORD_TARGETS.get(k, 120) for k in keys) * 2 + 400)

    try:
        resp = client.chat.completions.create(
            model=pass_b_model(),
            temperature=0.46,
            max_tokens=max_tok,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        _record_spend(
            resp,
            pass_b_model(),
            phase="pass_b",
            analysis_id=analysis_id,
            user_id=user_id,
            lang=lang,
        )
        raw = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return {}
        out: Dict[str, str] = {}
        for k in keys:
            txt = clean_internal_labels(
                post_process_prose((parsed.get(k) or "").strip())
            )
            if not txt:
                continue
            if not _validate_prose(txt, bundle, k):
                print(f"[face_ai] Pass B {k} failed validation")
                continue
            out[k] = txt
        print(
            f"[face_ai] Pass B OK model={pass_b_model()} "
            f"{len(out)}/{len(keys)} blocks"
        )
        return out
    except Exception as exc:
        print(f"[face_ai] Pass B failed: {exc}")
        return {}


def _validate_prose(text: str, bundle: Any, block_key: str) -> bool:
    from .face_signal_bundle import validate_prose_against_bundle

    if not validate_prose_against_bundle(text, bundle):
        return False
    if not passes_face_voice_combined(text, f"faceread.{block_key}"):
        return False
    banned = ("kundli", "nakshatra", "diagnosis", "soulmate", "guaranteed")
    low = text.lower()
    if any(b in low for b in banned):
        return False
    return True


def _record_spend(
    resp: Any,
    model: str,
    *,
    phase: str = "openai",
    analysis_id: Optional[str] = None,
    user_id: Optional[int] = None,
    lang: str = "",
    section: str = "",
    retry: int = 0,
) -> None:
    try:
        from .token_analytics import record_from_response

        record_from_response(
            resp,
            model,
            analysis_id=analysis_id,
            user_id=user_id,
            phase=phase,
            lang=lang,
            section=section,
            retry=retry,
        )
    except Exception:
        pass


def _cache_load_insights(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    try:
        from . import redis_manager as _rm
        from . import redis_codec as _codec

        key = f"{os.environ.get('FACE_REDIS_PREFIX', 'face')}:insights:{analysis_id}:{lang}"
        raw = _rm.get_raw(key)
        if raw:
            return _codec.loads(raw)
    except Exception:
        pass
    return None


def _cache_save_insights(analysis_id: str, lang: str, data: Dict[str, Any]) -> None:
    try:
        from . import redis_manager as _rm
        from . import redis_codec as _codec
        from .face_cache import TTL_NARRATION

        key = f"{os.environ.get('FACE_REDIS_PREFIX', 'face')}:insights:{analysis_id}:{lang}"
        _rm.set_raw(key, _codec.dumps(data), TTL_NARRATION)
    except Exception:
        pass


def _resolve_pass_a(
    bundle: Any,
    lang_n: str,
    analysis_id: Optional[str],
    user_id: Optional[int],
    ai_mode: Any,
) -> tuple[Dict[str, Any], bool, bool]:
    """Returns (pass_a, from_cache, ran_api)."""
    from .narration_artifact import (
        is_canonical_lang,
        load_canonical_insights,
        run_localize_pass,
        save_canonical_insights,
    )
    from .token_budget import AIMode

    if ai_mode == AIMode.TEMPLATE_ONLY:
        return {}, False, False

    pass_a: Dict[str, Any] = {}
    from_cache = False
    ran_api = False

    if analysis_id:
        cached = _fc_get_insights_lang(analysis_id, lang_n)
        if cached:
            return cached, True, False

    canonical = load_canonical_insights(analysis_id) if analysis_id else {}

    if canonical and not is_canonical_lang(lang_n):
        if ai_mode in (AIMode.LOCALIZE_ONLY, AIMode.MINI_ONLY, AIMode.FULL):
            pass_a = run_localize_pass(
                canonical,
                lang_n,
                analysis_id=analysis_id,
                user_id=user_id,
            )
            return pass_a, bool(analysis_id), True

    if canonical and is_canonical_lang(lang_n):
        return canonical, True, False

    # Canonical English Pass A (one-time per analysis)
    pass_a = run_pass_a(
        bundle,
        "english",
        analysis_id=analysis_id,
        user_id=user_id,
    )
    ran_api = bool(pass_a)
    if analysis_id and pass_a:
        save_canonical_insights(analysis_id, pass_a)
        _cache_save_insights(
            analysis_id,
            "en",
            {"pass_a": pass_a, "version": INSIGHTS_VERSION},
        )
        if not is_canonical_lang(lang_n):
            pass_a = run_localize_pass(
                pass_a,
                lang_n,
                analysis_id=analysis_id,
                user_id=user_id,
            )
        else:
            _fc_put_insights_lang(analysis_id, lang_n, pass_a)

    return pass_a, from_cache, ran_api


def _fc_get_insights_lang(analysis_id: str, lang: str) -> Dict[str, Any]:
    from .face_cache import get_insights_lang
    return get_insights_lang(analysis_id, lang) or {}


def _fc_put_insights_lang(analysis_id: str, lang: str, pass_a: Dict[str, Any]) -> None:
    from .face_cache import put_insights_lang
    put_insights_lang(analysis_id, lang, pass_a, INSIGHTS_VERSION)


def enrich_12_blocks(
    ordered_blocks: List[Dict[str, Any]],
    *,
    engines: Dict[str, Any],
    legacy_sections: Dict[str, Any],
    person: Dict[str, Any],
    hook: Optional[Dict[str, Any]] = None,
    tldr: Optional[Dict[str, Any]] = None,
    lang: str = "hinglish",
    session_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    user_id: Optional[int] = None,
    ai_mode: Optional[Any] = None,
) -> bool:
    """
    Bundle → Pass A (canonical EN + localize) → Pass B (budgeted 4o).
    """
    from .token_budget import AIMode, allow_pass_b, resolve_ai_mode

    if not ai_enabled():
        return False

    snap = resolve_ai_mode(user_id, analysis_id=analysis_id, lang=lang)
    if ai_mode is not None:
        from dataclasses import replace
        snap = replace(snap, mode=ai_mode)
    else:
        ai_mode = snap.mode

    if ai_mode == AIMode.TEMPLATE_ONLY:
        for block in ordered_blocks:
            k = block.get("key") or ""
            if not k or block.get("appendix"):
                continue
            txt = legacy_template_narrative(k, legacy_sections, engines, person)
            if txt:
                block["narrative"] = txt
                block["_source"] = "template"
        return False

    from .face_signal_bundle import load_bundle_for_analysis

    hook = hook or {}
    tldr = tldr or {}
    snapshot = None
    if analysis_id:
        try:
            from .face_cache import get_analysis
            snapshot = get_analysis(analysis_id)
        except Exception:
            pass

    bundle = load_bundle_for_analysis(
        engines,
        legacy_sections,
        person=person,
        snapshot=snapshot,
        hook=hook,
        tldr=tldr,
    )

    lang_n = _lang_norm(lang)
    pass_a, pass_a_cached, pass_a_ran = _resolve_pass_a(
        bundle, lang_n, analysis_id, user_id, ai_mode
    )

    applied = False
    used_pass_b: Set[str] = set()

    for block in ordered_blocks:
        k = block.get("key") or ""
        if not k or block.get("appendix"):
            continue
        insight = pass_a.get(k) or {}
        txt = narrative_from_pass_a_insight(k, insight)
        if not txt:
            txt = legacy_template_narrative(k, legacy_sections, engines, person)
        if txt:
            block["narrative"] = txt
            block["_source"] = "pass_a" if insight else "template"

    pass_b_keys = sorted(PASS_B_BLOCKS)
    pass_b_texts: Dict[str, str] = {}
    if pass_b_keys and ai_mode == AIMode.FULL and allow_pass_b(snap):
        pass_b_texts = run_pass_b(
            bundle,
            pass_a,
            lang_n,
            pass_b_keys,
            hook=hook,
            analysis_id=analysis_id,
            user_id=user_id,
        )

    for block in ordered_blocks:
        k = block.get("key") or ""
        if k in pass_b_texts:
            block["narrative"] = pass_b_texts[k]
            block["_source"] = "pass_b"
            applied = True
            used_pass_b.add(k)

    if pass_b_texts.get("faceread.hook_identity"):
        hook["identity_line"] = pass_b_texts["faceread.hook_identity"]
        applied = True
    if pass_b_texts.get("faceread.hook_shock"):
        hook["shock_line"] = pass_b_texts["faceread.hook_shock"]
        applied = True
    if pass_b_texts.get("faceread.tldr") and tldr is not None:
        tldr["summary_paragraph"] = pass_b_texts["faceread.tldr"]
        applied = True

    calls = int(pass_a_ran) + (1 if pass_b_texts else 0)
    budget = estimate_token_budget(bundle)
    print(
        f"[face_ai] 12-block mode={ai_mode} calls={calls} "
        f"pass_a_cached={pass_a_cached} pass_b={len(used_pass_b)} "
        f"budget={snap.reason} fp={bundle.fingerprint()[:8]}"
    )
    return applied or bool(pass_a)


def estimate_token_budget(bundle: Any, n_pass_b: int = 8) -> Dict[str, int]:
    """Rough byte estimates for logging."""
    b = len(bundle.to_prompt_json())
    return {
        "bundle_bytes": b,
        "pass_a_input_est": b + 900,
        "pass_b_input_est": b + 1200 + n_pass_b * 200,
        "legacy_21_est": b + 12 * 450,
    }
