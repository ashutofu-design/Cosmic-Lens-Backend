"""
Canonical narration artifacts — English insights → localized rewrite only.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from . import face_cache as _fc
from .report_version import INSIGHTS_VERSION

log = logging.getLogger(__name__)

CANONICAL_LANG = "en"


def has_canonical_insights(analysis_id: str) -> bool:
    return bool(_fc.get_canonical_insights(analysis_id))


def save_canonical_insights(analysis_id: str, pass_a: Dict[str, Any]) -> None:
    if analysis_id and pass_a:
        _fc.put_canonical_insights(analysis_id, pass_a, INSIGHTS_VERSION)


def load_canonical_insights(analysis_id: str) -> Dict[str, Any]:
    return _fc.get_canonical_insights(analysis_id) or {}


def is_canonical_lang(lang: str) -> bool:
    l = (lang or "").strip().lower()
    return l in ("en", "english", "eng")


def run_localize_pass(
    canonical_pass_a: Dict[str, Any],
    target_lang: str,
    *,
    analysis_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Mini-model: rewrite English Pass A insights into target language only.
    No new facts — structure preserved.
    """
    from .face_ai_orchestrator import _get_client, pass_a_model
    from .token_analytics import record_from_response

    cached = None
    if analysis_id:
        cached = _fc.get_insights_lang(analysis_id, target_lang)
    if cached:
        log.info("[narration_artifact] localize cache HIT %s", target_lang)
        return cached

    client = _get_client()
    if not client:
        return canonical_pass_a

    from numerology.core.report_voice import LANG_INSTRUCT

    lang_map = {"hi": "hindi", "hinglish": "hinglish", "en": "english"}
    lang_rule = LANG_INSTRUCT.get(
        lang_map.get(target_lang.strip().lower(), target_lang),
        LANG_INSTRUCT["hinglish"],
    )

    sys_prompt = (
        "Localize face-reading insights into the target language.\n"
        f"TARGET LANGUAGE: {lang_rule}\n"
        "INPUT: JSON object of block insights in English.\n"
        "OUTPUT: Same JSON keys, same structure (one_liner, bullets, observation, "
        "implication, anchor_phrase). Translate only — do not add facts.\n"
        "Return json_object."
    )
    user_prompt = json.dumps(canonical_pass_a, ensure_ascii=False)

    try:
        resp = client.chat.completions.create(
            model=pass_a_model(),
            temperature=0.3,
            max_tokens=2200,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        record_from_response(
            resp,
            pass_a_model(),
            analysis_id=analysis_id,
            user_id=user_id,
            phase="localize",
            lang=target_lang,
        )
        raw = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and parsed:
            if analysis_id:
                _fc.put_insights_lang(
                    analysis_id, target_lang, parsed, INSIGHTS_VERSION
                )
            return parsed
    except Exception as exc:
        log.warning("[narration_artifact] localize failed: %s", exc)

    return canonical_pass_a
