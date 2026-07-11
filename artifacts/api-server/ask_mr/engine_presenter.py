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

_COMMITMENT_SECTION_SKELETON = """
STRUCTURE (mandatory order — plain paragraphs, NO Cosmo section headers):
P1 — Direct Answer: use direct_answer only; keep verdict-locked tone.
P2 — Kyun ye verdict aaya: use reason_summary only.
P3 — Mukhya sanket: expand strongest_effects[] only (real-life effects, no planet jargon).
P4 — Dhyan dene layak challenges: expand weakest_effects[] only.
P5 — Iska practical matlab: meaning_note + scorecard_user_note if present (no raw score numbers).
P6 — Timing: ONLY if timing.window exists in PRESENTER_JSON.
P7 — Aapko kis baat par dhyan dena chahiye: practical_guidance only.
Final line: confidence_explanation — exact score + kyunki reason from JSON.
""".strip()


def _truthy(val: str) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes")


def _falsy(val: str) -> bool:
    return (val or "").strip().lower() in ("0", "false", "no")


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


def extract_presenter_fields(engine: str, narrator_json: dict[str, Any]) -> dict[str, Any]:
    """Map narrator JSON to presenter-safe field subset."""
    eng = (engine or "").strip().lower()
    data = dict(narrator_json or {})
    if eng == "commitment":
        return _commitment_presenter_fields(data)
    return {
        "engine": eng,
        "locked_template": str(data.get("locked_template") or "").strip(),
        "final_verdict": data.get("final_verdict", ""),
        "confidence_explanation": data.get("confidence_explanation", ""),
    }


def _presenter_lang_block(lang: str) -> str:
    rl = (lang or "hn").strip().lower()
    if rl in ("hi", "hn", "hinglish"):
        return (
            'LANGUAGE: Warm Roman Hinglish (default). Use Devanagari only if user question is Devanagari.'
        )
    if rl == "en":
        return "LANGUAGE: Plain English — warm, direct, no jargon."
    return f"LANGUAGE: Match user lang={rl}."


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
        return f"LENGTH: {lo}–{hi} words — expand each skeleton step to 1–2 sentences."
    if engine == "commitment":
        return "LENGTH: 85–120 words — same facts as LOCKED_TEMPLATE, light Hinglish polish only."
    return f"LENGTH: {lo}–{hi} words total."


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
    """Strict presenter prompt — LLM may only rephrase PRESENTER_JSON fields."""
    eng = (engine or "").strip().lower()
    fields = extract_presenter_fields(eng, narrator_json)
    presenter_blob = json.dumps(fields, indent=2, ensure_ascii=False)
    forbidden = fields.get("forbidden_phrases") or []
    forbidden_line = ", ".join(str(x) for x in forbidden[:12] if x)

    skeleton = _COMMITMENT_SECTION_SKELETON if eng == "commitment" else (
        "STRUCTURE: Follow locked_template paragraph order if present; otherwise "
        "direct_answer → reasons → strongest → weakest → meaning → guidance → confidence."
    )

    intent_block = ""
    if (user_intent or "").strip():
        intent_block = (
            "\nUSER ACTUALLY ASKED (anchor opening to this — do not drift):\n"
            f"{user_intent.strip()}\n"
        )

    q_line = (question or fields.get("original_question") or "").strip()
    return f"""You are "Cosmo Ask" — a PRESENTER only, not an astrologer or counsellor.
The {eng} engine already decided the verdict. You receive PRESENTER_JSON with final facts.

ROLE LOCK:
• Use ONLY fields in PRESENTER_JSON. Skip any missing field or section.
• Do NOT invent planets, houses, lords, dasha, dates, scores, or psychology beyond JSON.
• Do NOT recalculate or contradict final_verdict.
• Rephrase lightly in natural Hinglish — same facts, same order, same verdict strength.
• NEVER use hedging: shayad, ho sakta hai, kehna mushkil, lagta hai, maybe, perhaps, might.
• NEVER use planet/house/lord jargon in user-facing text — use strongest_effects/weakest_effects only.
• NEVER say "Engine ke hisaab" or expose raw scorecard numbers.
• BANNED phrases: {forbidden_line or "clarity, patience, boundaries, open communication"}.

{_presenter_lang_block(lang)}
{intent_block}
ORIGINAL_QUESTION: {q_line}

PRESENTER_JSON:
{presenter_blob}

{skeleton}

REFERENCE (mandatory structure — do not add/remove facts):
{fields.get("locked_template") or "(use PRESENTER_JSON fields in skeleton order)"}

{_presenter_length_block(eng, wants_explain=wants_explain, concise=concise)}

OUTPUT: Plain paragraphs only. No Markdown headers (**, ---). No bullets unless concise mode.
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

    eng = (engine or "").strip().lower()
    if eng == "commitment":
        from ask_mr.commitment_narrator import validate_commitment_narrator_output

        ok, sub = validate_commitment_narrator_output(t, narrator_json)
        if not ok:
            issues.extend(sub)

    return len(issues) == 0, issues
