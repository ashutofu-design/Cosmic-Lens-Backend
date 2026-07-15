"""Unified relationship MR narrator — single entry for all engines."""
from __future__ import annotations

import json
from typing import Any

_CONFIDENCE_PCT = {"high": 82, "medium": 62, "low": 42}

RELATIONSHIP_NARRATOR_RULES = """
You are the official Cosmic Lens Relationship Narrator.

Your only job is to explain the verified ENGINE_JSON in a natural, human-like way.

Never calculate astrology yourself.
Never predict on your own.
Never invent planets, houses, yogas, timing, scores, or relationship facts.

Use ONLY:
- ENGINE_JSON
- Fired rules
- Verified evidence
- Final verdict
- Confidence

STRICT RULES

1. Answer the user's exact relationship question first.
2. Stay locked to the detected relationship angle (commitment, loyalty, breakup, patch-up, compatibility, partner nature, marriage, etc.).
3. Explain WHY the verdict came using ONLY fired rules.
4. Mention supportive indicators only if present.
5. Mention challenges only if present.
6. Explain what this means in practical day-to-day relationship life.
7. Give guidance ONLY if it exists in ENGINE_JSON.
8. End with the exact confidence from ENGINE_JSON.

NEVER

- Invent astrology.
- Invent planets or houses.
- Invent diseases, remedies, timing, or predictions.
- Contradict the engine verdict.
- Mix another relationship topic.
- Add emotional counselling.
- Add generic advice.
- Add facts not present in ENGINE_JSON.

Never use words like:
- Shayad
- Ho sakta hai
- Lagta hai
- I think
- Maybe
- Probably

LANGUAGE

Reply in the same language as the user's question.
(Hindi / Hinglish / English)

Style:
- Warm
- Professional
- Natural
- Human astrologer
- Simple language
- Short paragraphs
- No unnecessary jargon.

DEFAULT OUTPUT

1. Direct answer
2. Why this verdict
3. Supportive factors
4. Challenges
5. Practical meaning
6. What the user should pay attention to
7. Confidence

If any section has no evidence in ENGINE_JSON, skip it.

Remember:

You are ONLY the narrator.
The engine is the astrologer.
Never become the astrologer yourself.
""".strip()

_LANG_HINT: dict[str, str] = {
    "hn": "Reply in natural Hinglish (Roman script) matching the user's question language.",
    "hi": "Reply in Hindi (Devanagari) matching the user's question language.",
    "en": "Reply in simple English matching the user's question language.",
}


def is_relationship_mr_engine(archetype: str) -> bool:
    try:
        from ask_intent_llm import MR_ARCHETYPES

        return (archetype or "").strip().lower() in MR_ARCHETYPES
    except Exception:
        return False


def engine_result_to_relationship_json(
    engine_result: Any,
    *,
    question: str = "",
    llm_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generic narrator JSON from any MR EngineResult — no per-engine converters."""
    arch = str(getattr(engine_result, "archetype", "") or "").strip().lower()
    checks = dict(getattr(engine_result, "checks", None) or {})
    verdict = str(getattr(engine_result, "verdict", "") or "").strip()
    conf_label = str(getattr(engine_result, "confidence", "medium") or "medium").strip().lower()
    conf_pct = _CONFIDENCE_PCT.get(conf_label, 55)
    try:
        if checks.get("confidence_pct") is not None:
            conf_pct = int(checks["confidence_pct"])
    except (TypeError, ValueError):
        pass

    pos = list(getattr(engine_result, "evidence_positive", None) or [])
    neg = list(getattr(engine_result, "evidence_negative", None) or [])
    if not pos and not neg:
        try:
            pos, neg, _ = engine_result._finalize_evidence_split()
        except Exception:
            ev = list(getattr(engine_result, "evidence", None) or [])
            pos = ev[:3]
            neg = ev[3:6]

    direct = str(
        checks.get("direct_answer")
        or checks.get("user_direct_answer")
        or verdict
    ).strip()
    q = (question or "").strip()
    intent = ""
    if isinstance(llm_intent, dict):
        intent = str(llm_intent.get("user_intent") or llm_intent.get("intent") or "").strip()

    payload: dict[str, Any] = {
        "engine": arch,
        "archetype": arch,
        "original_question": q,
        "user_intent": intent,
        "verdict": verdict,
        "confidence": conf_pct,
        "direct_answer": direct,
        "strongest": pos[:4],
        "weakest": neg[:4],
        "strongest_effects": pos[:4],
        "weakest_effects": neg[:4],
        "summary": list(getattr(engine_result, "summary", None) or [])[:4],
    }
    for key in (
        "love_score", "arrange_score", "love_pct", "arrange_pct",
        "secret_level", "secrecy_level", "answer_focus", "secret_angle",
        "timing", "question_intent", "fired_rules",
    ):
        if checks.get(key) is not None:
            payload[key] = checks[key]
    return payload


def relationship_narrator_payload(
    engine_result: Any,
    *,
    question: str = "",
    wants_explain: bool = False,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    """Compact ENGINE_JSON block for LLM narrator (all relationship engines)."""
    _ = wants_explain
    if hasattr(engine_result, "to_narrator_payload"):
        base = engine_result.to_narrator_payload()
    else:
        base = str(engine_result)
    if llm_intent or question:
        try:
            blob = engine_result_to_relationship_json(
                engine_result,
                question=question,
                llm_intent=llm_intent,
            )
            return base + "\n\nNARRATOR_JSON:\n" + json.dumps(blob, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return base


def _lang_block(reply_lang: str) -> str:
    rl = (reply_lang or "hn").strip().lower()
    return _LANG_HINT.get(rl, _LANG_HINT["hn"])


def build_relationship_narrator_system_prompt(
    *,
    engine_result: Any | None = None,
    chart_text: str = "",
    question: str = "",
    reply_lang: str = "hn",
    wants_explain: bool = False,
    llm_intent: dict[str, Any] | None = None,
    word_budget: int = 55,
    concise: bool = False,
) -> str:
    """Master relationship narrator prompt — RELATIONSHIP_NARRATOR_RULES + ENGINE_JSON."""
    _ = word_budget
    arch = ""
    if engine_result is not None:
        arch = str(getattr(engine_result, "archetype", "") or "").strip().lower()
    if not chart_text:
        if engine_result is None:
            chart_text = "(no ENGINE_JSON)"
        else:
            chart_text = relationship_narrator_payload(
                engine_result,
                question=question,
                wants_explain=wants_explain,
                llm_intent=llm_intent,
            )

    intent = ""
    if isinstance(llm_intent, dict):
        intent = str(llm_intent.get("user_intent") or llm_intent.get("intent") or "").strip()
    intent_block = ""
    if intent:
        intent_block = f"\nUSER INTENT (answer this first):\n{intent}\n"

    angle = arch.replace("_", " ") if arch else "relationship"
    length_hint = (
        "Keep the reply concise — one short paragraph."
        if concise
        else (
            "Explain fully but stay within 180–260 words in short paragraphs."
            if wants_explain
            else "Keep the reply clear and complete in 120–200 words using short paragraphs."
        )
    )

    q_line = (question or "").strip()
    return f"""{RELATIONSHIP_NARRATOR_RULES}

RELATIONSHIP ANGLE: {angle}

{_lang_block(reply_lang)}
{length_hint}
{intent_block}
ORIGINAL QUESTION: {q_line}

ENGINE_JSON:
{chart_text}
""".strip()


def attach_narrator_json_to_result(
    engine_result: Any,
    *,
    question: str = "",
    llm_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build JSON + store on engine_result.checks for presenter validation."""
    narrator_json = engine_result_to_relationship_json(
        engine_result,
        question=question,
        llm_intent=llm_intent,
    )
    checks = dict(getattr(engine_result, "checks", None) or {})
    checks["narrator_input"] = narrator_json
    checks["question"] = question or ""
    engine_result.checks = checks
    return narrator_json
