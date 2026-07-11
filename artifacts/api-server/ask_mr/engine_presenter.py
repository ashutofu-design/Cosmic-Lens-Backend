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


def _secret_section_skeleton() -> str:
    return """
STRUCTURE (secrecy / third-person interest — natural Hinglish, NO labels):
P1 — User ke exact sawal ka seedha jawab: direct_answer se shuru karo; tone final_verdict se locked.
P2 — Kyun: reason_summary + strongest_effects[] ko 1–2 flowing sentences me weave karo.
P3 — Risk: weakest_effects[] + meaning_note + transparency_outlook — real-life language, no chart jargon.
P4 — practical_guidance ek caring next step ke taur par.
Final sentence: confidence_explanation from JSON — copy score + reason exactly.

Write like a trusted friend explaining chart truth — NOT a stitched template.
No "— lekin", no bullets, no D1/D9/house/planet/lord names. Same facts, warmer flow.
""".strip()


def _generic_section_skeleton(engine: str) -> str:
    return f"""
STRUCTURE (human conversation for {engine} — plain paragraphs, NO robotic labels):
P1 — Seedha jawab: answer ORIGINAL_QUESTION using direct_answer; tone locked to final_verdict.
P2 — Kyun: weave reason_summary naturally (no "Asli wajah seedhi hai" label).
P3 — Support + challenges: strongest_effects / weakest_effects as everyday meaning.
P4 — Matlab + transparency + practical_guidance as caring advice (no section headers).
Final line: confidence_explanation from JSON — copy exactly.
Use PRESENTER_JSON facts only. Sound human, not a form.
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
    if engine == "commitment":
        return "LENGTH: 90–140 words — natural Hinglish paragraphs, not form fields."
    return f"LENGTH: {lo}–{max(hi, 130)} words — natural flowing paragraphs."


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

    skeleton = (
        _COMMITMENT_SECTION_SKELETON
        if eng == "commitment"
        else _secret_section_skeleton()
        if eng == "secret_relationship"
        else _generic_section_skeleton(eng)
    )

    intent_block = ""
    if (user_intent or "").strip():
        intent_block = (
            "\nUSER ACTUALLY ASKED (open with THIS concern first):\n"
            f"{user_intent.strip()}\n"
        )

    q_line = (question or fields.get("original_question") or "").strip()
    return f"""You are "Cosmo Ask" — a warm, honest Hinglish guide.
You are a PRESENTER, not an astrologer. The {eng} engine already decided the verdict.
Your job: explain PRESENTER_JSON facts so the user feels understood — human, clear, not template-y.

FACT LOCK (hard):
• Use ONLY PRESENTER_JSON fields. Skip missing fields.
• Do NOT invent planets, houses, lords, dasha, dates, scores, or new psychology.
• Do NOT contradict final_verdict or weaken/strengthen it beyond JSON.
• Prefer strongest_effects / weakest_effects / meaning_note / practical_guidance over raw evidence jargon.

HUMAN STYLE (soft freedom):
• Write flowing paragraphs — NEVER robotic labels like "Kyun ye verdict aaya:" or "Mukhya sanket:".
• Speak to the user's exact question in the first 1–2 sentences.
• You MAY rephrase, connect ideas, and add warmth — same facts, clearer feeling.
• Keep Roman Hinglish unless Lang says Devanagari.
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