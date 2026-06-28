"""Global hard guards for Ask — death/lifespan refusal + engine-only policy."""

from __future__ import annotations

import os
import re
from typing import Any, Optional

_ENGINE_SLICES = frozenset({
    "mr_engine_v1",
    "career_engine_v1",
    "career_timing_v1",
    "education_engine_v1",
    "children_engine_v1",
    "property_engine_v1",
    "travel_engine_v1",
    "litigation_engine_v1",
    "finance_engine_v1",
    "health_engine_v1",
    "travel_timing_v1",
    "finance_timing_v1",
    "health_timing_v1",
    "children_timing_v1",
    "love_timing_v1",
    "education_timing_v1",
    "property_timing_v1",
    "litigation_timing_v1",
    "spiritual_timing_v1",
    "fame_timing_v1",
    "network_timing_v1",
    "universal_timing_v1",
})

_MARRIAGE_TIMING_RX = re.compile(
    r"(?ix)"
    r"\b(shaadi|shadi|vivah|marriage|wedding|rishta|biwi|pati|patni)\b.{0,40}\b("
    r"kab|kab\s+hoga|kab\s+hogi|kab\s+honge|when|kis\s+saal|kis\s+year|muhurat"
    r")\b"
    r"|"
    r"\b(kab|when)\b.{0,40}\b(shaadi|shadi|vivah|marriage|wedding|rishta)\b"
)

_NO_ENGINE_REFUSAL = (
    "Yeh sawaal abhi hamare chart engine se process nahi ho sakta — "
    "sirf raw chart par jawab nahi dete. "
    "Kripya shaadi, career, health, paisa, property, travel, bachche ya "
    "court-case se juda specific sawaal puchiye; tab engine facts ke saath jawab milega."
)

# Spec-only TIMING SPEC blocks are NOT engine output — must not unlock LLM passthrough.
_TIMING_SPEC_ONLY_RX = re.compile(
    r"(?ix)^\s*===\s*TIMING\s+SPEC\s*\(",
)
_TIMING_ENGINE_LOCKED_RX = re.compile(
    r"(?ix)TIMING\s+(?:ENGINE|FALLBACK)\s*\(LOCKED\)",
)


def is_real_timing_engine_block(block: str) -> bool:
    """True when block is deterministic engine output, not a spec checklist."""
    text = (block or "").strip()
    if not text:
        return False
    if _TIMING_SPEC_ONLY_RX.search(text):
        return False
    if _TIMING_ENGINE_LOCKED_RX.search(text):
        return True
    if re.search(r"(?im)^Verdict:\s*.+", text) and "TIMING ENGINE" in text.upper():
        return True
    if re.search(r"(?im)^Current window:\s*.+\u2192", text):
        return True
    return False


_GENERAL_LIFE_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"life\s+me\s+struggle|struggle\s+kab|mushkil\s+kab|pareshani\s+kab|"
    r"life\s+me\s+peace|sab\s+theek\s+kab|set\s+ho\s+jaunga|"
    r"problem\s+kab\s+khatam|dukh\s+kab|tension\s+kab\s+kam|"
    r"jaayega|jaayegi|khatam\s+hoga"
    r")\b",
)


def is_death_lifespan_question(question: str) -> bool:
    """True when the user asks for death timing, lifespan, or mrityu prediction."""
    try:
        from health_focus_routing import detect_hard_guard

        return detect_hard_guard(question or "") == "REFUSE_DEATH"
    except Exception:
        return False


def build_death_refusal_text(question: str, kundli: Any = None) -> str:
    try:
        from ask_health.engines.hard_guard import run_hard_guard

        result = run_hard_guard(
            kundli if isinstance(kundli, dict) else {},
            question or "",
            archetype="refuse_death",
        )
        text = (result.template_text or "").strip()
        if text:
            return text
    except Exception:
        pass
    return (
        "Death / mrityu / 'kab marunga' ka jawab dena shastriya etiquette ke khilaf hai. "
        "Main exact end-date ya lifespan predict nahi kar sakta."
    )


def death_refusal_result(question: str, *, kundli: Any = None, qtype: str = "STATIC") -> dict:
    """Response dict for death/lifespan questions — no LLM."""
    return {
        "text": build_death_refusal_text(question, kundli),
        "topic": "health",
        "question_type": qtype,
        "confidence": 1.0,
        "source": "refuse_death",
        "engine_tag": "ans-engine",
        "follow_ups": [],
    }


def direct_llm_allowed() -> bool:
    """Default OFF — set RAW_PASSTHROUGH_DIRECT_LLM=1 to allow legacy chart-only LLM."""
    return (os.environ.get("RAW_PASSTHROUGH_DIRECT_LLM") or "0").strip().lower() in (
        "1",
        "on",
        "true",
        "yes",
    )


def passthrough_has_domain_engine_facts(
    *,
    checks: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
    marriage_block: str = "",
    career_block: str = "",
    domain_timing_block: str = "",
) -> bool:
    """True only when a domain engine produced facts — never chart-only / compact D1."""
    checks = checks or {}
    slice_meta = slice_meta or {}

    if checks.get("skip_llm"):
        return True

    if (marriage_block or "").strip():
        return True
    if (career_block or "").strip():
        return True
    if is_real_timing_engine_block(domain_timing_block):
        return True

    sl = str(slice_meta.get("slice") or "")
    has_verdict = bool(slice_meta.get("verdict"))
    has_evidence = bool(slice_meta.get("evidence"))
    has_checks = bool(slice_meta.get("checks"))

    if sl in _ENGINE_SLICES and (has_verdict or has_evidence or has_checks):
        return True
    if sl == "marriage_relationship" and slice_meta.get("buckets"):
        return True

    return False


def marriage_timing_engine_required(question: str) -> bool:
    q = (question or "").strip()
    return bool(q and _MARRIAGE_TIMING_RX.search(q))


def general_timing_engine_required(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    """Timing Q with no mapped domain engine (life struggle, vague kab)."""
    q = (question or "").strip()
    if not q:
        return False
    if _GENERAL_LIFE_TIMING_RX.search(q):
        return True
    try:
        from event_timing.timing_router import resolve_timing_domain

        dom, _bucket, is_timing = resolve_timing_domain(q, llm_intent)
        return bool(is_timing and dom in ("general", "universal"))
    except Exception:
        return False


def passthrough_missing_required_engine(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    marriage_block: str = "",
    career_block: str = "",
    domain_timing_block: str = "",
    has_domain_engine: bool,
) -> Optional[str]:
    """When a domain timing Q must have engine output but does not, return reason code."""
    if has_domain_engine:
        return None
    q = question or ""
    if career_timing_engine_required(q, llm_intent) and not (career_block or "").strip():
        return "career_timing"
    if marriage_timing_engine_required(q) and not (marriage_block or "").strip():
        return "marriage_timing"
    if general_timing_engine_required(q, llm_intent) and not is_real_timing_engine_block(
        domain_timing_block,
    ):
        return "general_timing"
    try:
        from event_timing.timing_router import resolve_timing_domain

        dom, _bucket, is_timing = resolve_timing_domain(q, llm_intent)
        if is_timing and dom not in ("general", "career", "marriage", "universal"):
            if not (domain_timing_block or "").strip():
                return f"{dom}_timing"
        if is_timing and dom == "universal" and not (domain_timing_block or "").strip():
            return "universal_timing"
    except Exception:
        pass
    return "no_domain_engine"


def enforce_engine_only_or_refuse(
    *,
    question: str,
    qtype: str,
    llm_intent: dict[str, Any] | None = None,
    checks: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
    marriage_block: str = "",
    career_block: str = "",
    domain_timing_block: str = "",
) -> Optional[dict]:
    """Return refusal payload when LLM must not run chart-only; None = OK to proceed."""
    if direct_llm_allowed():
        return None

    # Never show engine_required wall for basic health outlook (Health kaisi rahegi?).
    try:
        from ask_health.timing_registry import health_static_overrides_llm_timing

        if health_static_overrides_llm_timing(question or "", llm_intent):
            return None
    except Exception:
        import re

        if re.search(
            r"(?ix)\b(health|sehat|swasth|swasthya|tabiyat)\s+(kaisi|kaisa)\s*"
            r"(rahegi|rahega|hogi|hoga)?",
            question or "",
        ) and not re.search(
            r"(?ix)\b(kab|when|kis\s+(?:saal|year|date|mahine|month)|20\d{2})\b",
            question or "",
        ):
            return None

    checks = checks or {}
    slice_meta = slice_meta or {}
    # Health static was selected but engine facts missing — answer via LLM, not refusal wall.
    if checks.get("is_health_static"):
        try:
            from ask_health.classifier import is_health_static_question

            if is_health_static_question(question or ""):
                return None
        except Exception:
            pass
        dom = str((llm_intent or {}).get("domain") or "").strip().lower()
        if dom == "health":
            return None

    has_domain = passthrough_has_domain_engine_facts(
        checks=checks,
        slice_meta=slice_meta,
        marriage_block=marriage_block,
        career_block=career_block,
        domain_timing_block=domain_timing_block,
    )
    missing = passthrough_missing_required_engine(
        question,
        llm_intent,
        marriage_block=marriage_block,
        career_block=career_block,
        domain_timing_block=domain_timing_block,
        has_domain_engine=has_domain,
    )
    if missing and missing != "no_domain_engine":
        if missing == "general_timing":
            try:
                from ask_timing_clarify import (
                    build_timing_domain_clarifier_result,
                    needs_timing_domain_clarifier,
                )

                if needs_timing_domain_clarifier(question, llm_intent):
                    return build_timing_domain_clarifier_result(question, qtype=qtype)
            except Exception:
                pass
        return no_engine_refusal_result(question, qtype=qtype)
    if not has_domain:
        try:
            from ask_timing_clarify import (
                build_timing_domain_clarifier_result,
                needs_timing_domain_clarifier,
            )

            if needs_timing_domain_clarifier(question, llm_intent):
                return build_timing_domain_clarifier_result(question, qtype=qtype)
        except Exception:
            pass
        return no_engine_refusal_result(question, qtype=qtype)
    return None


def career_timing_engine_required(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    try:
        from ask_career.timing_registry import is_career_timing_question

        return is_career_timing_question(question or "", llm_intent)
    except Exception:
        return False


def build_career_timing_slice_meta(verdict: dict[str, Any]) -> dict[str, Any]:
    """Admin slice_meta for career timing (assess_career → LLM narrator)."""
    try:
        from event_timing.career.career_timing import build_career_timing_engine_trace
    except Exception:
        build_career_timing_engine_trace = None  # type: ignore

    strategy = str(verdict.get("strategy") or "").strip()
    timing_evidence = _career_timing_evidence(verdict)
    dasha_trace = _career_dasha_trace(verdict)
    meta = {
        "slice": "career_timing_v1",
        "topic": "career",
        "archetype": verdict.get("bucket"),
        "verdict": verdict.get("verdict"),
        "summary": [strategy[:300]] if strategy else [],
        "evidence": timing_evidence,
        "timing_evidence": timing_evidence,
        "dasha_trace": dasha_trace,
        "ignore": list(verdict.get("brand_safety_warnings") or [])[:8],
        "checks": {
            "bucket": verdict.get("bucket"),
            "score": verdict.get("score"),
            "confidence": verdict.get("confidence"),
            "tense": verdict.get("tense"),
            "trigger_score": (verdict.get("score_breakdown") or {}).get("trigger_score"),
        },
        "narrator_mode": "engine_facts_only",
    }
    if isinstance(verdict.get("step_audit"), dict):
        meta["step_audit"] = verdict["step_audit"]
    if isinstance(verdict.get("timing_audit"), dict):
        meta["timing_audit"] = verdict["timing_audit"]
    return meta


def build_career_timing_engine_trace(verdict: dict[str, Any]) -> dict[str, Any]:
    """Delegate to career_timing module (full step_audit + timing_audit)."""
    try:
        from event_timing.career.career_timing import (
            build_career_timing_engine_trace as _trace,
        )

        return _trace(verdict)
    except Exception:
        return {}


def _career_timing_evidence(verdict: dict[str, Any]) -> list[str]:
    """Dasha / transit / trigger reasons first — not full natal layer dump."""
    out: list[str] = []
    triggers = verdict.get("triggers") or {}
    for key in (
        "T1_vimshottari",
        "T2_saturn_transit",
        "T3_jupiter_yogini",
    ):
        block = triggers.get(key) if isinstance(triggers, dict) else None
        if not isinstance(block, dict):
            continue
        for w in block.get("why") or []:
            if w and w not in out:
                out.append(str(w))
    if len(out) < 4:
        for r in verdict.get("reasons") or []:
            rs = str(r)
            if any(tok in rs for tok in ("MD", "AD", "PD", "dasha", "transit", "window", "Career")):
                if rs not in out:
                    out.append(rs)
            if len(out) >= 8:
                break
    return out[:8]


def _career_dasha_trace(verdict: dict[str, Any]) -> dict[str, Any]:
    tw = verdict.get("timing_window") if isinstance(verdict.get("timing_window"), dict) else {}
    cur = tw.get("current") if isinstance(tw.get("current"), dict) else {}
    nxt = tw.get("next_career") if isinstance(tw.get("next_career"), dict) else {}
    return {
        "current_lords": cur.get("lords"),
        "current_start": cur.get("start"),
        "current_end": cur.get("end"),
        "next_career_ad": nxt.get("ad"),
        "next_career_md": nxt.get("md"),
        "next_career_start": nxt.get("start"),
        "next_career_end": nxt.get("end"),
        "next_career_reason": nxt.get("reason"),
        "saturn_transit": tw.get("saturn_transit"),
        "jupiter_active": tw.get("jupiter_active"),
    }


def no_engine_refusal_result(question: str, *, qtype: str = "STATIC") -> dict:
    return {
        "text": _NO_ENGINE_REFUSAL,
        "topic": "scope",
        "question_type": qtype,
        "confidence": 1.0,
        "source": "engine_required",
        "engine_tag": "ans-engine",
        "follow_ups": [],
    }
