"""Presenter-only LLM — formats Narrator JSON; never invents astro or psychology."""
from __future__ import annotations

import json
import os
import re
from typing import Any

_ASTRO_JARGON_RX = re.compile(
    r"(?i)\b(venus|mars|jupiter|saturn|moon|sun|mercury|rahu|ketu|uranus|neptune|pluto)\b"
    r"|\b(?:\d{1,2})(?:st|nd|rd|th)\s+house\b"
    r"|\bhouse\s+\d{1,2}\b"
    r"|\b(?:\d{1,2})(?:th|st|nd|rd)\s+lord\b"
    r"|\blord\s+of\b"
    r"|\bdasha\b"
    r"|\bantardasha\b"
    r"|\bmahadasha\b"
    r"|\bnakshatra\b"
    r"|\bkarak\b"
    r"|\blagna\b"
    r"|\bkundli\b"
    r"|\bd[19]\b"
    r"|\brelationship\s+axis\b"
)

_ENGINE_USE_LLM_ENV: dict[str, str] = {
    "commitment": "ASK_COMMITMENT_USE_LLM",
    "patchup": "ASK_PATCHUP_USE_LLM",
    "loyalty_trust": "ASK_LOYALTY_USE_LLM",
    "breakup_risk": "ASK_BREAKUP_USE_LLM",
    "compatibility": "ASK_COMPATIBILITY_USE_LLM",
    "secret_relationship": "ASK_SECRET_USE_LLM",
    "partner_nature": "ASK_PARTNER_NATURE_USE_LLM",
    "communication": "ASK_COMMUNICATION_USE_LLM",
    "emotional_attachment": "ASK_EMOTIONAL_ATTACHMENT_USE_LLM",
    "family_approval": "ASK_FAMILY_APPROVAL_USE_LLM",
    "long_distance": "ASK_LONG_DISTANCE_USE_LLM",
    "toxicity": "ASK_TOXICITY_USE_LLM",
    "chemistry": "ASK_CHEMISTRY_USE_LLM",
    "bed_intimacy": "ASK_BED_INTIMACY_USE_LLM",
    "karmic_marriage": "ASK_KARMIC_MARRIAGE_USE_LLM",
    "relationship_future": "ASK_RELATIONSHIP_FUTURE_USE_LLM",
    "relationship_decisions": "ASK_RELATIONSHIP_DECISIONS_USE_LLM",
    "relationship_verification": "ASK_RELATIONSHIP_VERIFICATION_USE_LLM",
    "relationship_remedies": "ASK_RELATIONSHIP_REMEDIES_USE_LLM",
    "one_sided_love": "ASK_ONE_SIDED_LOVE_USE_LLM",
}


def _truthy(val: str) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes")


def _falsy(val: str) -> bool:
    return (val or "").strip().lower() in ("0", "false", "no")


def human_narrator_enabled() -> bool:
    """Default ON — set ASK_MR_HUMAN_NARRATOR=0 to force locked templates."""
    v = (os.environ.get("ASK_MR_HUMAN_NARRATOR") or "1").strip().lower()
    return v not in ("0", "false", "no")


# Presenter may drop template section labels — keep verdict/confidence checks only.
_PRESENTER_SOFT_ISSUES = frozenset({
    "missing_positive_section",
    "missing_challenges_section",
    "missing_why_section",
    "missing_meaning_section",
    "missing_focus_section",
    "confidence_line",
})

_PRESENTER_HARD_ISSUES = frozenset({
    "empty",
    "cosmo_markdown_banned",
    "banned_phrase",
    "contradiction_high_secrecy",
    "contradiction_low_secrecy",
    "chart_jargon_leak",
    "counseling_fluff",
    "too_long",
})


def presenter_has_only_soft_issues(issues: list[str]) -> bool:
    """True when validation failed only on format/label rules, not fact lock."""
    if not issues:
        return False
    for issue in issues:
        if issue in _PRESENTER_HARD_ISSUES:
            return False
        if issue.startswith("astro_jargon:"):
            return False
    return True


def _engine_presenter_env_key(engine: str) -> str:
    return f"ASK_{engine.strip().upper()}_PRESENTER"


def use_engine_presenter_mode(engine: str) -> bool:
    """Presenter ON when engine USE_LLM is on, unless globally/per-engine disabled."""
    eng = (engine or "").strip().lower()
    if _falsy(os.environ.get("ASK_ENGINE_PRESENTER", "1")):
        return False
    per = os.environ.get(_engine_presenter_env_key(eng), "").strip()
    if _falsy(per):
        return False
    if _truthy(per):
        return True
    return engine_llm_enabled(eng)


def engine_llm_enabled(engine: str) -> bool:
    """True when per-engine USE_LLM or global ASK_MR_HUMAN_NARRATOR is on."""
    eng = (engine or "").strip().lower()
    if human_narrator_enabled():
        return eng in _ENGINE_USE_LLM_ENV
    use_llm_key = _ENGINE_USE_LLM_ENV.get(eng)
    if not use_llm_key:
        return False
    return _truthy(os.environ.get(use_llm_key, ""))


def _commitment_presenter_fields(data: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "engine": "commitment",
        "original_question": data.get("original_question", ""),
        "answer_focus": data.get("answer_focus", ""),
        "commitment_angle": data.get("commitment_angle", ""),
        "final_verdict": data.get("final_verdict", ""),
        "direct_answer": data.get("direct_answer", ""),
        "reason_summary": data.get("reason_summary", ""),
        "strongest_effects": list(data.get("strongest_effects") or []),
        "weakest_effects": list(data.get("weakest_effects") or []),
        "meaning_note": data.get("meaning_note", ""),
        "scorecard_user_note": data.get("scorecard_user_note", ""),
        "practical_guidance": data.get("practical_guidance", ""),
        "confidence": data.get("confidence"),
        "confidence_label": data.get("confidence_label", ""),
        "confidence_explanation": data.get("confidence_explanation", ""),
        "forbidden_phrases": list(data.get("forbidden_phrases") or []),
    }
    locked = data.get("locked_template")
    if isinstance(locked, str) and locked.strip():
        fields["locked_template"] = locked.strip()
    timing = data.get("timing")
    if isinstance(timing, dict) and str(timing.get("window") or "").strip():
        fields["timing"] = timing
    return fields


def _generic_presenter_fields(engine: str, data: dict[str, Any]) -> dict[str, Any]:
    from ask_mr.secret_templates import effects_from_evidence

    strongest_raw = list(data.get("strongest_effects") or data.get("strongest") or [])
    weakest_raw = list(data.get("weakest_effects") or data.get("weakest") or [])
    if (engine or "").strip().lower() == "secret_relationship":
        strongest_fx = effects_from_evidence(strongest_raw, limit=3)
        weakest_fx = effects_from_evidence(weakest_raw, limit=3)
    else:
        strongest_fx = strongest_raw
        weakest_fx = weakest_raw

    fields: dict[str, Any] = {
        "engine": engine,
        "original_question": data.get("original_question", ""),
        "answer_focus": data.get("answer_focus", ""),
        "final_verdict": data.get("final_verdict") or data.get("verdict", ""),
        "direct_answer": data.get("direct_answer", ""),
        "reason_summary": data.get("reason_summary", ""),
        "strongest_effects": strongest_fx,
        "weakest_effects": weakest_fx,
        "meaning_note": data.get("meaning_note", ""),
        "practical_guidance": data.get("practical_guidance", ""),
        "confidence": data.get("confidence"),
        "confidence_label": data.get("confidence_label", ""),
        "confidence_explanation": data.get("confidence_explanation", ""),
        "forbidden_phrases": list(data.get("forbidden_phrases") or []),
    }
    locked = data.get("locked_template")
    if isinstance(locked, str) and locked.strip():
        fields["locked_template"] = locked.strip()
    for key in (
        "transparency_outlook",
        "nature_outlook",
        "rem_outlook",
        "rver_outlook",
        "rdec_outlook",
        "rfut_outlook",
        "conditions_line",
    ):
        if data.get(key):
            fields[key] = data.get(key)
    timing = data.get("timing")
    if isinstance(timing, dict) and str(timing.get("window") or timing.get("summary") or "").strip():
        fields["timing"] = timing
    return fields


def extract_presenter_fields(engine: str, narrator_json: dict[str, Any]) -> dict[str, Any]:
    """Map narrator JSON to presenter-safe field subset."""
    eng = (engine or "").strip().lower()
    data = dict(narrator_json or {})
    if eng == "commitment":
        return _commitment_presenter_fields(data)
    return _generic_presenter_fields(eng, data)


def _presenter_lang_block(lang: str) -> str:
    rl = (lang or "hn").strip().lower()
    if rl in ("hi", "hn", "hinglish"):
        return (
            "LANGUAGE: Warm Roman Hinglish (default). Use Devanagari only if user question is Devanagari."
        )
    if rl == "en":
        return "LANGUAGE: Plain English — warm, direct, no jargon."
    return f"LANGUAGE: Match user lang={rl}."


_COMMITMENT_SECTION_SKELETON = """
STRUCTURE (human conversation — plain paragraphs, NO robotic section headers):
Write like a warm, honest friend explaining chart truth in Hinglish.

P1 — Seedha jawab: answer the ORIGINAL QUESTION directly using direct_answer. Lead with haan/nahi/mixed tone locked to final_verdict.
P2 — Kyun: weave reason_summary into 1–2 natural sentences (do NOT write "Kyun ye verdict aaya:" as a label).
P3 — Support: expand strongest_effects[] as everyday life meaning (no planet jargon).
P4 — Caution: expand weakest_effects[] as real challenges (no planet jargon).
P5 — Matlab: meaning_note + scorecard_user_note if present — practical, human.
P6 — Timing: ONLY if timing.window exists.
P7 — Focus: practical_guidance as caring next step.
Final line: copy confidence_explanation from PRESENTER_JSON exactly (score + kyunki reason).

FREEDOM (allowed):
• Light rephrase, connectors, and emotional warmth so it does not sound copy-paste.
• Short bridging phrases ("iska matlab yeh hai", "seedhi baat").
• Merge short related points into smooth paragraphs.

NOT allowed:
• New planets/houses/dasha/dates/scores/psychology not in PRESENTER_JSON.
• Softening or flipping final_verdict.
• Hedging (shayad / ho sakta hai / maybe).
• Generic counselling (clarity, patience, boundaries, open communication).
""".strip()


def _universal_story_skeleton(engine: str) -> str:
    return f"""
STRUCTURE (young astrologer voice for {engine} — explain like a real astrologer reading THEIR kundli):
5–6 flowing paragraphs, 150–220 words. Roman Hinglish, warm, direct — like a young astrologer friend.

P1 — Open with user's exact question + seedha jawab (direct_answer + final_verdict).
P2 — Full paragraph on POSITIVE kundli signals from strongest_effects[] — explain what each means in real life.
P3 — Full paragraph on CHALLENGING kundli signals from weakest_effects[] — explain clearly, no one-liners.
P4 — Full paragraph connecting both sides → final_verdict; user must feel "meri kundli se yeh aaya".
P5 — Full advice paragraph from practical_guidance / meaning_note.
P6 — confidence_explanation from JSON — copy score + reason exactly.

Must help user TRUST the answer: they should feel "meri kundli me yeh hai isliye yeh jawab aaya".
NO section labels, NO counseling lecture, NO planet/house/dasha jargon, NO "Asli wajah".
""".strip()


def _presenter_length_block(
    engine: str,
    *,
    wants_explain: bool,
    concise: bool,
) -> str:
    try:
        from ask_cosmo_narrator import cosmo_ask_word_target

        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain, concise=concise)
    except TypeError:
        from ask_cosmo_narrator import cosmo_ask_word_target

        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain)
    except Exception:
        lo, hi = (85, 120)
    if concise:
        return f"LENGTH: {min(lo, 70)}–{min(hi, 90)} words — one short paragraph, no headers."
    if wants_explain:
        return f"LENGTH: {lo}–{hi} words — explain naturally, 1–2 sentences per idea."
    return "LENGTH: 180–260 words — 5–6 full paragraphs (avg length each), young astrologer explain style."


def build_engine_presenter_system_prompt(
    *,
    engine: str,
    narrator_json: dict[str, Any],
    lang: str = "hn",
    wants_explain: bool = False,
    concise: bool = False,
    question: str = "",
    user_intent: str = "",
) -> str:
    """Presenter prompt — fact-locked, human Hinglish with light phrasing freedom."""
    eng = (engine or "").strip().lower()
    fields = extract_presenter_fields(eng, narrator_json)
    presenter_blob = json.dumps(fields, indent=2, ensure_ascii=False)
    forbidden = fields.get("forbidden_phrases") or []
    forbidden_line = ", ".join(str(x) for x in forbidden[:12] if x)

    skeleton = _universal_story_skeleton(eng)

    intent_block = ""
    if (user_intent or "").strip():
        intent_block = (
            "\nUSER ACTUALLY ASKED (open with THIS concern first):\n"
            f"{user_intent.strip()}\n"
        )

    q_line = (question or fields.get("original_question") or "").strip()
    return f"""You are a young, warm Indian astrologer (late 20s) explaining THIS user's kundli in Roman Hinglish.
You are a PRESENTER — the {eng} engine already computed verdict from their chart. Your job: make them feel
"meri kundli me yeh signal hai, isliye yeh jawab aaya" — trust through clear positive/negative pinpoints.

FACT LOCK (hard):
• Use ONLY PRESENTER_JSON fields. Skip missing fields.
• Do NOT invent planets, houses, lords, dasha, dates, scores, or new psychology.
• Do NOT contradict final_verdict or weaken/strengthen it beyond JSON.
• Name strongest_effects[] as supportive kundli signals; weakest_effects[] as challenging kundli signals.

HUMAN STYLE (young astrologer):
• Sound like you're sitting with them explaining their chart — natural, not template, not therapist.
• Start by acknowledging their exact question, then answer directly.
• Separate positive signals and negative signals clearly so user knows WHY.
• NEVER robotic labels ("Asli wajah", "Mukhya sanket", "The Big Picture").
• NEVER hedge: shayad, ho sakta hai, kehna mushkil, lagta hai, maybe, perhaps, might.
• NEVER say "Engine ke hisaab" or print raw scorecard numbers.
• BANNED: {forbidden_line or "clarity, patience, boundaries, open communication"}.

{_presenter_lang_block(lang)}
{intent_block}
ORIGINAL_QUESTION: {q_line}

PRESENTER_JSON:
{presenter_blob}

{skeleton}

REFERENCE FACTS (same truth — rewrite as natural speech, do not invent):
{fields.get("locked_template") or "(use PRESENTER_JSON fields)"}

{_presenter_length_block(eng, wants_explain=wants_explain, concise=concise)}

OUTPUT: Plain paragraphs only. No Markdown headers. No bullet list unless concise mode.
""".strip()


def detect_astro_jargon(text: str) -> list[str]:
    """Return astro jargon tokens found in user-facing text."""
    return list({m.group(0).lower() for m in _ASTRO_JARGON_RX.finditer(text or "")})


def validate_presenter_output(
    text: str,
    narrator_json: dict[str, Any],
    engine: str,
) -> tuple[bool, list[str]]:
    """Reject presenter output that invents astro jargon or breaks engine validation."""
    issues: list[str] = []
    t = (text or "").strip()
    if not t:
        return False, ["empty"]

    jargon = detect_astro_jargon(t)
    if jargon:
        issues.append(f"astro_jargon:{','.join(sorted(jargon)[:5])}")

    if re.search(
        r"(?i)\b(the\s+big\s+picture|deep\s+breakdown|ab\s+kya\s+karein|relationship\s+counseling)\b",
        t,
    ):
        issues.append("cosmo_markdown_banned")

    from ask_mr.story_answer import STORY_ANSWER_MAX_WORDS, looks_like_bad_story_llm_output

    if looks_like_bad_story_llm_output(t):
        issues.append("counseling_fluff")
    elif len(t.split()) > STORY_ANSWER_MAX_WORDS:
        issues.append("too_long")

    eng = (engine or "").strip().lower()
    engine_validators: dict[str, Any] = {}
    if eng == "commitment":
        from ask_mr.commitment_narrator import validate_commitment_narrator_output

        engine_validators[eng] = validate_commitment_narrator_output
    elif eng == "patchup":
        from ask_mr.patchup_narrator import validate_patchup_narrator_output

        engine_validators[eng] = validate_patchup_narrator_output
    elif eng == "secret_relationship":
        from ask_mr.secret_narrator import validate_secret_presenter_output

        engine_validators[eng] = validate_secret_presenter_output

    validator = engine_validators.get(eng)
    if validator:
        _ok, sub = validator(t, narrator_json)
        sub = [s for s in sub if s not in _PRESENTER_SOFT_ISSUES]
        if sub:
            issues.extend(sub)

    return len(issues) == 0, issues


def present_story_answer_llm(
    narrator_json: dict[str, Any],
    *,
    engine: str,
    question: str,
    lang: str = "hn",
    llm_intent: dict[str, Any] | None = None,
) -> str | None:
    """Thin presenter call — story format for any MR engine."""
    from openai_helper import _get_client

    eng = (engine or "").strip().lower()
    client = _get_client()
    if not client or not isinstance(narrator_json, dict) or not eng:
        return None

    intent = ""
    if isinstance(llm_intent, dict):
        intent = str(llm_intent.get("user_intent") or llm_intent.get("intent") or "").strip()

    system_prompt = build_engine_presenter_system_prompt(
        engine=eng,
        narrator_json=narrator_json,
        lang=lang,
        wants_explain=False,
        concise=False,
        question=question or "",
        user_intent=intent,
    )
    user_payload = (question or str(narrator_json.get("original_question") or "")).strip()
    model = os.environ.get(
        "RAW_PASSTHROUGH_MODEL",
        os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
            max_tokens=620,
        )
        text = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[engine_presenter] story direct presenter failed ({eng}): {exc}", flush=True)
        return None
    if not text:
        return None

    from ask_mr.narrator import polish_mr_confident_tone

    polished = polish_mr_confident_tone(text)
    ok, issues = validate_presenter_output(polished, narrator_json, eng)
    if ok or presenter_has_only_soft_issues(issues):
        return polished
    hard = [
        i for i in issues
        if i in _PRESENTER_HARD_ISSUES or i.startswith("astro_jargon:")
    ]
    if polished and not hard:
        print(
            f"[engine_presenter] story direct presenter accepted with issues {issues}",
            flush=True,
        )
        return polished
    print(
        f"[engine_presenter] story direct presenter rejected ({eng}) {issues}",
        flush=True,
    )
    return None


def present_secret_answer_llm(
    narrator_json: dict[str, Any],
    *,
    question: str,
    lang: str = "hn",
    llm_intent: dict[str, Any] | None = None,
) -> str | None:
    """Backward-compatible secret presenter wrapper."""
    return present_story_answer_llm(
        narrator_json,
        engine="secret_relationship",
        question=question,
        lang=lang,
        llm_intent=llm_intent,
    )